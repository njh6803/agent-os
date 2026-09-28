"""파일시스템 PluginSource. 진실의 원천은 디렉터리와 매니페스트와 운영자 파일이다(ADR 0003, 0017).

`<root>/<kind 디렉터리>/<name>/plugin.toml`. 부재는 None, 파싱·import 실패는 PluginError.
진입점은 플러그인 디렉터리 기준 파일이며 고유 모듈명 `agent_os_plugins.<name>.<module>`로 로드한다.
sys.path 를 건드리지 않는다.

단건과 목록이 읽히지 않는 파일을 다르게 말한다. 단건은 PluginError, 목록은 표지다. 이 비대칭은
의도이고 논증은 ADR 0012 의 2026-09-22 이력에 있다. 테스트가 고정한다.

**켜짐은 `<root>/disabled.toml` 이 든다(ADR 0017).** 형식은 이 어댑터가 소유한다 — 플러그인이 읽는
파일이 아니라 sdk 에 두지 않는다. `schema_version = "1"` 과 종류 키 넷(`PluginKind` 의 값)의 이름
배열이고, 없으면 꺼진 것이 없다. 손상은 파일을 여는 것부터 검증까지 전부 PluginError 이고 메시지가
경로와 이유를 든다. 쓰기는 정규형(종류 넷 전부, 이름순, 중복 없음)을 같은 디렉터리의 임시 파일에
쓴 뒤 이름을 바꿔 통째로 교체하고, 바뀌는 것이 없으면 파일을 건드리지 않으며, 깨진 파일은 덮어쓰지
않는다. 열거나 교체하다 받는 `PermissionError` 만 짧게 동기로 다시 시도한다(ADR 0017 의 2026-09-27
첫 이력). 윈도우에서 다른 핸들이 연 파일은 교체가, 교체되는 순간의 읽기가 그 오류이기 때문이다.
"""

from __future__ import annotations

import contextlib
import importlib.util
import os
import sys
import tempfile
import time
import tomllib
from collections.abc import Callable
from pathlib import Path
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from agent_os.core.ports import (
    ManifestRow,
    PluginError,
    PluginKey,
    UnreadableManifest,
    WriteOutcome,
)
from agent_os.sdk import (
    PLUGIN_NAME_PATTERN,
    BaseAgent,
    PluginKind,
    PluginManifest,
    PluginName,
    is_plugin_name,
    parse_manifest,
)

_DIRECTORY = {
    PluginKind.AGENT: "agents",
    PluginKind.MCP: "mcp",
    PluginKind.SKILL: "skills",
    PluginKind.MODEL: "models",
}
_MANIFEST = "plugin.toml"
_DISABLED = "disabled.toml"
_OPERATOR_FILE_SCHEMA_VERSION = "1"

# `PermissionError` 를 다시 시도하는 간격. 합이 곧 상한이다. 부딪힌 순간에만 루프가 이만큼 멈춘다.
# 숫자는 ADR 0017 의 2026-09-27 첫 이력이 실측으로 정했고, 티켓 01 이 실제 어댑터로 다시 쟀다.
_RETRY_DELAYS = (0.001, 0.002, 0.004, 0.008, 0.016)

# 운영자 파일의 이름 하나. sdk 의 패턴을 지나야 파일이 손상이 아니다 — 패턴을 어긴 이름은 플러그인
# 루트 밖을 가리킬 수 있고, 어차피 그런 디렉터리는 로드되지 않는다.
type _ValidName = Annotated[PluginName, Field(pattern=PLUGIN_NAME_PATTERN)]


# 운영자 파일의 모양. TOML 을 읽은 느슨한 값을 좁히는 자리가 이 모델이라 손으로 좁히지 않는다(원칙
# III). 모르는 키는 손상이고(fail-closed, ADR 0017), 빠진 키는 빈 목록이며 형식 버전은 필수라 빈
# 파일이 손상이다. 필드 이름은 `PluginKind` 의 값이고 `disabled()` 가 그 대응을 한 곳에서 든다.
class _OperatorFile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1"]
    agent: tuple[_ValidName, ...] = ()
    mcp: tuple[_ValidName, ...] = ()
    skill: tuple[_ValidName, ...] = ()
    model: tuple[_ValidName, ...] = ()

    def disabled(self) -> frozenset[PluginKey]:
        """꺼진 (종류, 이름)의 집합. 한 배열 안의 중복은 집합이 합친다."""
        by_kind = {
            PluginKind.AGENT: self.agent,
            PluginKind.MCP: self.mcp,
            PluginKind.SKILL: self.skill,
            PluginKind.MODEL: self.model,
        }
        return frozenset(
            PluginKey(kind=kind, name=name) for kind, names in by_kind.items() for name in names
        )


class FilesystemPlugins:
    def __init__(self, root: Path) -> None:
        self._root = root

    def read_disabled(self) -> frozenset[PluginKey]:
        """운영자 파일이 없으면 빈 집합. 있으면 그 내용이고, 읽거나 검증하지 못하면 PluginError."""
        path = self._root / _DISABLED
        try:
            text = _retrying(lambda: path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return frozenset()
        except (OSError, ValueError) as error:
            # UnicodeDecodeError 가 ValueError 다. PermissionError 는 재시도가 다한 뒤에 여기 온다.
            raise PluginError(f"운영자 파일을 읽을 수 없다: {path}\n{error}") from error
        return _parse_operator_file(path, text)

    def write_enabled(self, kind: PluginKind, name: PluginName, enabled: bool) -> WriteOutcome:
        """부재 판정 → 손상 판정 → 바뀌는 것이 있을 때만 통째로 교체. 순서가 의도다(포트의
        독스트링)."""
        if not self._manifest_path(kind, name).is_file():
            return "absent"
        disabled = self.read_disabled()
        key = PluginKey(kind=kind, name=name)
        wanted = disabled - {key} if enabled else disabled | {key}
        if wanted != disabled:
            _replace_operator_file(self._root / _DISABLED, _render_operator_file(wanted))
        return "applied"

    def read_manifest(self, kind: PluginKind, name: PluginName) -> PluginManifest | None:
        path = self._manifest_path(kind, name)
        if not path.is_file():
            return None
        manifest = _parse(path)
        if manifest.kind is not kind:
            raise PluginError(
                f"디렉터리와 kind가 어긋난다: {path} 는 {kind} 자리인데 {manifest.kind}"
            )
        if manifest.name != name:
            raise PluginError(
                f"디렉터리와 name이 어긋난다: {path} 는 {name} 자리인데 {manifest.name}"
            )
        return manifest

    def list_manifests(self, kind: PluginKind) -> tuple[ManifestRow, ...]:
        """종류 디렉터리의 매니페스트를 이름 순으로. 없는 디렉터리는 빈 목록이다."""
        directory = self._root / _DIRECTORY[kind]
        if not directory.is_dir():
            return ()
        rows: list[ManifestRow] = []
        for child in sorted(directory.iterdir()):
            if (child / _MANIFEST).is_file():
                rows.append(self._row(kind, child.name))
        return tuple(rows)

    def _row(self, kind: PluginKind, name: str) -> ManifestRow:
        """디렉터리 하나. 이름이 패턴을 어기는 것도 표지로 남고 조용히 빠지지 않는다.

        런타임은 그것을 로드할 수 없지만(매니페스트의 name 이 같은 패턴을 만족해야 한다) 조용히
        빼면 등록했다고 믿는 것과 실제가 어긋난다. 대소문자 오해는 사람이 손으로 쓰는 파일에서
        가장 흔한 모양이고, 매니페스트 표지는 종류와 이름과 이유를 들어 단건 조회가 줄 것을 이미
        전부 담는다. 트레이스 쪽은 반대로 목록에서 빠진다 — 그 표지는 실행 식별자 하나만 들어서
        되물을 수 없는 식별자가 곧 죽은 행이 되고, 그 파일은 런타임이 만들 수도 없다.
        """
        if not is_plugin_name(name):
            return UnreadableManifest(
                kind=kind,
                name=name,
                reason=f"디렉터리 이름이 플러그인 이름의 패턴을 어긴다: {name}",
            )
        try:
            manifest = self.read_manifest(kind, PluginName(name))
        except PluginError as error:
            return UnreadableManifest(kind=kind, name=name, reason=str(error))
        if manifest is None:
            # 매니페스트 파일이 있는 것을 부르는 쪽이 확인했으므로 경쟁 상태로 사라진 경우뿐이다.
            return UnreadableManifest(kind=kind, name=name, reason=f"{name} 의 매니페스트가 없다")
        return manifest

    def _manifest_path(self, kind: PluginKind, name: PluginName) -> Path:
        """단건 읽기와 켜짐 쓰기가 같은 파일을 본다(질의). 부재 판정의 대상이 이 파일이다."""
        return self._root / _DIRECTORY[kind] / name / _MANIFEST

    def load_agent(self, manifest: PluginManifest) -> BaseAgent:
        if manifest.entrypoint is None:
            raise PluginError(f"{manifest.name} 은 entrypoint 가 없어 에이전트가 아니다")
        module_path, attr = manifest.entrypoint.split(":")
        directory = self._root / _DIRECTORY[PluginKind.AGENT] / manifest.name
        module = _import(directory, manifest.name, module_path)
        agent = getattr(module, attr, None)
        if agent is None:
            raise PluginError(f"진입점 {manifest.entrypoint} 에 {attr} 이 없다 ({directory})")
        instance = agent()
        if not callable(getattr(instance, "run", None)):
            raise PluginError(f"{manifest.entrypoint} 은 run() 이 없어 에이전트가 아니다")
        return instance


def _retrying[T](attempt: Callable[[], T]) -> T:
    """`PermissionError` 만 `_RETRY_DELAYS` 만큼 쉬며 다시 시도한다. 마지막 시도의 오류는 그대로
    난다.

    동기인 이유는 이것을 부르는 두 메서드가 동기여야 하기 때문이다 — 재개의 첫 걸음에 `await` 가
    없다는 불변식(ADR 0014)과, 한 프로세스 안의 쓰기 둘을 이벤트 루프가 줄세운다는 전제(ADR 0017)가
    둘 다 그것에 기댄다. 다른 오류는 다시 시도해도 같으므로 바로 난다.
    """
    for delay in _RETRY_DELAYS:
        try:
            return attempt()
        except PermissionError:
            time.sleep(delay)
    return attempt()


def _parse_operator_file(path: Path, text: str) -> frozenset[PluginKey]:
    """문법부터 이름 패턴까지 손상 전부를 PluginError 로 만든다. 경로와 이유를 메시지에 든다."""
    try:
        parsed = _OperatorFile.model_validate(tomllib.loads(text))
    except (ValidationError, ValueError) as error:
        # TOMLDecodeError 가 ValueError 다.
        raise PluginError(f"운영자 파일이 깨졌다: {path}\n{error}") from error
    return parsed.disabled()


def _render_operator_file(disabled: frozenset[PluginKey]) -> str:
    """정규형. 종류 넷을 모두, 이름순으로, 중복 없이. 이름이 패턴 안이라 따옴표를 피할 일이 없다.

    쓰기 코드를 직접 짜는 이유는 모양이 닫혀 있고 이름이 패턴에 묶여 있어서다(ADR 0017). 맞게
    쓰는지는 `tomllib` 과의 왕복 테스트가 판정한다.
    """
    lines = [f'schema_version = "{_OPERATOR_FILE_SCHEMA_VERSION}"']
    for kind in PluginKind:
        names = sorted(key.name for key in disabled if key.kind is kind)
        items = ", ".join(f'"{name}"' for name in names)
        lines.append(f"{kind.value} = [{items}]")
    return "\n".join(lines) + "\n"


def _replace_operator_file(path: Path, text: str) -> None:
    """같은 디렉터리의 임시 파일에 쓴 뒤 이름을 바꿔 통째로 교체한다. 반쪽 파일이 보이지 않는다.

    성공이든 실패든 임시 파일을 남기지 않는다. 교체가 `PermissionError` 면 다시 시도하고, 그래도
    실패하면 옛 파일이 그대로인 채 PluginError 다. 실패의 형태를 하나로 만드는 자리가 여기이고
    정상 흐름은 `_swap_in` 에 있다.
    """
    try:
        _swap_in(path, text)
    except OSError as error:
        raise PluginError(f"운영자 파일을 쓸 수 없다: {path}\n{error}") from error


def _swap_in(path: Path, text: str) -> None:
    """임시 파일을 만들고 쓰고 교체한다. 어느 단계에서 실패하든 임시 파일은 지우고 OSError 다."""
    descriptor, temp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        _retrying(lambda: os.replace(temp, path))
    finally:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(temp)


def _parse(path: Path) -> PluginManifest:
    """읽지 못하는 모든 이유를 PluginError 로 만든다. 파일을 여는 것부터 검증까지 전부다.

    OSError 를 함께 잡는 이유는 그것이 목록의 표지 경로를 지나치기 때문이다. is_file() 로 본
    뒤 실제로 읽는 사이에 파일이 사라지거나, 권한이 없거나, 네트워크 드라이브가 끊기면 OSError 이고
    ValueError 가 아니다. 그러면 매니페스트 하나가 목록 전체를 가리는데 그것이 ADR 0012 의
    2026-09-22 이력이 막으려 한 모양이다(PR 직전 보안·버그 축).
    """
    try:
        return parse_manifest(path.read_text(encoding="utf-8"))
    except (OSError, ValidationError, ValueError) as error:
        # ValidationError 와 UnicodeDecodeError 가 둘 다 ValueError 다.
        raise PluginError(f"매니페스트를 읽을 수 없다: {path}\n{error}") from error


def _import(directory: Path, name: PluginName, module_path: str) -> object:
    file = directory.joinpath(*module_path.split(".")).with_suffix(".py")
    module_name = f"agent_os_plugins.{name}.{module_path}"
    spec = importlib.util.spec_from_file_location(module_name, file)
    if spec is None or spec.loader is None:
        raise PluginError(f"진입점 파일이 없다: {file}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception as error:
        del sys.modules[module_name]
        raise PluginError(f"진입점을 import할 수 없다: {file}\n{error}") from error
    return module
