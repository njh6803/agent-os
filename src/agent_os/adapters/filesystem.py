"""파일시스템 PluginSource. 진실의 원천은 디렉터리와 매니페스트다(ADR 0003).

`<root>/<kind 디렉터리>/<name>/plugin.toml`. 부재는 None, 파싱·import 실패는 PluginError.
진입점은 플러그인 디렉터리 기준 파일이며 고유 모듈명 `agent_os_plugins.<name>.<module>`로 로드한다.
sys.path 를 건드리지 않는다.

단건과 목록이 읽히지 않는 파일을 다르게 말한다. 단건은 PluginError, 목록은 표지다. 이 비대칭은
의도이고 논증은 ADR 0012 의 2026-09-22 이력에 있다. 테스트가 고정한다.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from pydantic import ValidationError

from agent_os.core.ports import ManifestRow, PluginError, UnreadableManifest
from agent_os.sdk import (
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


class FilesystemPlugins:
    def __init__(self, root: Path) -> None:
        self._root = root

    def read_manifest(self, kind: PluginKind, name: PluginName) -> PluginManifest | None:
        path = self._root / _DIRECTORY[kind] / name / _MANIFEST
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
