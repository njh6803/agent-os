"""파일시스템 PluginSource. 디렉터리에 놓는 것만으로 등록이 끝나는지, 운영자 파일이 켜짐을 드는지.

앞부분은 매니페스트와 진입점, 뒷부분(`# 운영자 파일` 아래)은 플러그인 루트의 `disabled.toml` 이다
(ADR 0017). 진짜 디렉터리에 진짜 파일을 쓴다.
"""

import dataclasses
import os
import re
import subprocess
import sys
import threading
import time
import tomllib
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

import pytest

from agent_os.adapters.filesystem import FilesystemPlugins
from agent_os.core.ports import (
    ManifestRow,
    PluginError,
    PluginKey,
    PluginSource,
    UnreadableManifest,
)
from agent_os.sdk import (
    AgentContext,
    BaseAgent,
    Conversation,
    Event,
    PluginKind,
    PluginManifest,
    PluginName,
    RunFinished,
    RunId,
)

AGENT_SRC = """
from collections.abc import AsyncIterator

from agent_os.sdk import AgentContext, Event, RunFinished


class Agent:
    async def run(self, request: str, ctx: AgentContext) -> AsyncIterator[Event]:
        yield RunFinished(run_id=ctx.run_id, ts=ctx.now(), output="{tag}")
"""


def _manifest(kind: str, name: str, extra: str = "") -> str:
    return f'schema_version = "1"\nkind = "{kind}"\nname = "{name}"\nversion = "0.1.0"\n{extra}'


def _write_agent(root: Path, name: str, source: str = AGENT_SRC) -> Path:
    directory = root / "agents" / name
    directory.mkdir(parents=True)
    (directory / "plugin.toml").write_text(
        _manifest("agent", name, 'entrypoint = "agent:Agent"\n'), encoding="utf-8"
    )
    (directory / "agent.py").write_text(source.replace("{tag}", name), encoding="utf-8")
    return directory


def _write_mcp(root: Path, name: str) -> None:
    directory = root / "mcp" / name
    directory.mkdir(parents=True)
    (directory / "plugin.toml").write_text(
        _manifest("mcp", name, '[server]\ncommand = "npx"\nargs = ["-y", "server"]\n'),
        encoding="utf-8",
    )


class FakeContext:
    run_id = RunId("r1")
    conversation = Conversation(summary=None, exchanges=())

    def now(self) -> datetime:
        return datetime(2026, 9, 21, tzinfo=UTC)

    async def llm(self, prompt: str) -> str:
        return "unused"

    async def tool(self, name: str, **args: object) -> str:
        return "unused"


async def _output_of(agent: BaseAgent) -> str:
    ctx: AgentContext = FakeContext()
    events: list[Event] = [event async for event in agent.run("hi", ctx)]
    assert isinstance(events[-1], RunFinished)
    return events[-1].output


@pytest.fixture
def root(tmp_path: Path) -> Path:
    return tmp_path


def test_에이전트_매니페스트를_디렉터리에서_읽는다(root: Path) -> None:
    _write_agent(root, "calc")
    plugins: PluginSource = FilesystemPlugins(root)

    manifest = plugins.read_manifest(PluginKind.AGENT, PluginName("calc"))

    assert manifest is not None
    assert manifest.name == "calc"
    assert manifest.entrypoint == "agent:Agent"


def test_없는_플러그인은_None이다(root: Path) -> None:
    plugins: PluginSource = FilesystemPlugins(root)

    assert plugins.read_manifest(PluginKind.AGENT, PluginName("nope")) is None


def test_디렉터리와_kind가_어긋나면_에러다(root: Path) -> None:
    directory = root / "agents" / "odd"
    directory.mkdir(parents=True)
    (directory / "plugin.toml").write_text(
        _manifest("mcp", "odd", '[server]\ncommand = "x"\n'), encoding="utf-8"
    )
    plugins: PluginSource = FilesystemPlugins(root)

    with pytest.raises(PluginError, match="kind"):
        plugins.read_manifest(PluginKind.AGENT, PluginName("odd"))


def test_매니페스트_파싱_실패는_무엇이_잘못됐는지_담은_에러다(root: Path) -> None:
    directory = root / "agents" / "bad"
    directory.mkdir(parents=True)
    (directory / "plugin.toml").write_text(
        _manifest("agent", "bad", 'entrypoint = "agent:Agent"\n').replace(
            'schema_version = "1"', 'schema_version = "9"'
        ),
        encoding="utf-8",
    )
    plugins: PluginSource = FilesystemPlugins(root)

    with pytest.raises(PluginError, match="schema_version"):
        plugins.read_manifest(PluginKind.AGENT, PluginName("bad"))


async def test_진입점을_로드하면_에이전트가_돈다(root: Path) -> None:
    _write_agent(root, "calc")
    plugins: PluginSource = FilesystemPlugins(root)
    manifest = plugins.read_manifest(PluginKind.AGENT, PluginName("calc"))
    assert manifest is not None

    agent = plugins.load_agent(manifest)

    assert await _output_of(agent) == "calc"


async def test_같은_파일명을_가진_플러그인_둘이_서로_덮어쓰지_않는다(root: Path) -> None:
    _write_agent(root, "alpha")
    _write_agent(root, "beta")
    plugins: PluginSource = FilesystemPlugins(root)
    alpha = plugins.read_manifest(PluginKind.AGENT, PluginName("alpha"))
    beta = plugins.read_manifest(PluginKind.AGENT, PluginName("beta"))
    assert alpha is not None and beta is not None

    outputs = [await _output_of(plugins.load_agent(m)) for m in (alpha, beta, alpha)]

    assert outputs == ["alpha", "beta", "alpha"]


def test_진입점_속성이_없으면_에러다(root: Path) -> None:
    _write_agent(root, "noattr", source="x = 1\n")
    plugins: PluginSource = FilesystemPlugins(root)
    manifest = plugins.read_manifest(PluginKind.AGENT, PluginName("noattr"))
    assert manifest is not None

    with pytest.raises(PluginError, match="Agent"):
        plugins.load_agent(manifest)


def test_진입점_import가_실패하면_에러다(root: Path) -> None:
    _write_agent(root, "broken", source="def (\n")
    plugins: PluginSource = FilesystemPlugins(root)
    manifest = plugins.read_manifest(PluginKind.AGENT, PluginName("broken"))
    assert manifest is not None

    with pytest.raises(PluginError, match="broken"):
        plugins.load_agent(manifest)


def test_mcp_매니페스트는_서버_실행_정보를_돌려준다(root: Path) -> None:
    _write_mcp(root, "everything")
    plugins: PluginSource = FilesystemPlugins(root)

    manifest = plugins.read_manifest(PluginKind.MCP, PluginName("everything"))

    assert manifest is not None
    assert manifest.server is not None
    assert manifest.server.command == "npx"
    assert plugins.read_manifest(PluginKind.MCP, PluginName("missing")) is None


def test_디렉터리와_name이_어긋나면_에러다(root: Path) -> None:
    directory = root / "agents" / "outer"
    directory.mkdir(parents=True)
    (directory / "plugin.toml").write_text(
        _manifest("agent", "inner", 'entrypoint = "agent:Agent"\n'), encoding="utf-8"
    )
    plugins: PluginSource = FilesystemPlugins(root)

    with pytest.raises(PluginError, match="name"):
        plugins.read_manifest(PluginKind.AGENT, PluginName("outer"))


def _names(rows: Sequence[ManifestRow]) -> list[str]:
    return [row.name for row in rows]


def test_종류_하나의_매니페스트를_전부_돌려준다(root: Path) -> None:
    _write_agent(root, "alpha")
    _write_agent(root, "beta")
    _write_mcp(root, "everything")
    plugins: PluginSource = FilesystemPlugins(root)

    rows = plugins.list_manifests(PluginKind.AGENT)

    assert _names(rows) == ["alpha", "beta"]
    assert all(isinstance(row, PluginManifest) for row in rows)


def test_빈_디렉터리와_없는_디렉터리가_빈_목록이다(root: Path) -> None:
    (root / "models").mkdir()
    plugins: PluginSource = FilesystemPlugins(root)

    assert plugins.list_manifests(PluginKind.MODEL) == ()
    assert plugins.list_manifests(PluginKind.SKILL) == ()


def _write_broken(root: Path) -> None:
    """읽히지 않는 모양 셋. 매니페스트는 사람이 손으로 쓰는 파일이라 깨지는 것이 예상된 경로다."""
    for name, text in (
        ("badversion", _manifest("agent", "badversion").replace('"1"', '"9"')),
        ("nokind", 'schema_version = "1"\nname = "nokind"\nversion = "0.1.0"\n'),
        ("wrongkind", _manifest("mcp", "wrongkind", '[server]\ncommand = "x"\n')),
    ):
        directory = root / "agents" / name
        directory.mkdir(parents=True)
        (directory / "plugin.toml").write_text(text, encoding="utf-8")


def test_깨진_매니페스트가_섞여도_읽히는_것은_전부_돌아오고_깨진_것은_표지다(root: Path) -> None:
    """깨진 하나가 전부를 가리면 무엇이 살아 있는지조차 알 수 없다. 표지가 이름과 이유를 든다."""
    _write_agent(root, "alpha")
    _write_broken(root)
    plugins: PluginSource = FilesystemPlugins(root)

    rows = plugins.list_manifests(PluginKind.AGENT)

    assert _names(rows) == ["alpha", "badversion", "nokind", "wrongkind"]
    assert isinstance(rows[0], PluginManifest)
    broken = rows[1:]
    assert all(isinstance(row, UnreadableManifest) for row in broken)
    assert all(
        isinstance(row, UnreadableManifest)
        and row.kind is PluginKind.AGENT
        and row.name in row.reason
        for row in broken
    )


def test_열_수_없는_매니페스트가_있어도_목록이_살아남는다(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """권한 오류와 경쟁 삭제는 OSError 이고 ValueError 가 아니다. 포장하지 않으면 매니페스트
    하나가 목록 전체를 가리는데 그것이 ADR 0012 이력이 막으려 한 모양이다.

    실제 권한 오류를 이식성 있게 만들 수 없어 읽기만 주입한다. 보는 것은 바깥 행동 그대로다 —
    목록이 살아남고 그 자리에 표지가 서는 것.
    """
    _write_agent(root, "alpha")
    _write_agent(root, "locked")
    original = Path.read_text

    def refuse(self: Path, encoding: str | None = None, errors: str | None = None) -> str:
        if self.parent.name == "locked":
            raise PermissionError(13, "권한이 없다")
        return original(self, encoding, errors)

    monkeypatch.setattr(Path, "read_text", refuse)
    plugins: PluginSource = FilesystemPlugins(root)

    rows = plugins.list_manifests(PluginKind.AGENT)

    assert _names(rows) == ["alpha", "locked"]
    assert isinstance(rows[0], PluginManifest)
    assert isinstance(rows[1], UnreadableManifest)
    assert "권한" in rows[1].reason


def test_같은_깨진_파일을_단건으로_읽으면_PluginError다(root: Path) -> None:
    """목록과 단건의 비대칭이 의도다. 문서에만 두면 다음 사람이 일관성 결함으로 보고 고친다."""
    _write_broken(root)
    plugins: PluginSource = FilesystemPlugins(root)

    for name in ("badversion", "nokind", "wrongkind"):
        with pytest.raises(PluginError, match=name):
            plugins.read_manifest(PluginKind.AGENT, PluginName(name))


def test_플러그인_이름_패턴을_어기는_디렉터리도_표지로_남는다(root: Path) -> None:
    """조용히 빼면 등록했다고 믿는 것과 실제가 어긋난다. 대소문자 오해가 가장 흔한 모양이다.

    런타임은 이 디렉터리를 로드할 수 없지만 표지가 종류와 이름과 이유를 들어, 단건 조회가 줄 것을
    이미 전부 담는다. 트레이스 쪽과 갈리는 것이 의도다 — 그 표지는 실행 식별자 하나만 든다.
    """
    _write_agent(root, "alpha")
    odd = ("MyAgent", "두 낱말", "a", "-앞이하이픈")
    for name in odd:
        directory = root / "agents" / name
        directory.mkdir(parents=True)
        (directory / "plugin.toml").write_text(_manifest("agent", "alpha"), encoding="utf-8")
    plugins: PluginSource = FilesystemPlugins(root)

    rows = plugins.list_manifests(PluginKind.AGENT)

    assert sorted(_names(rows)) == sorted(["alpha", *odd])
    readable = [row for row in rows if isinstance(row, PluginManifest)]
    assert _names(readable) == ["alpha"]
    assert all(
        isinstance(row, UnreadableManifest) and "패턴" in row.reason
        for row in rows
        if row.name in odd
    )


# 운영자 파일 — 켜짐은 플러그인 루트의 disabled.toml 이 든다(ADR 0017, plugin-toggle 티켓 01)

DISABLED = "disabled.toml"
# API 가 쓰는 정규형. 종류 넷이 모두, 이름순으로, 중복 없이. 아무것도 꺼지지 않은 파일이 이것이다.
CANONICAL_EMPTY = 'schema_version = "1"\nagent = []\nmcp = []\nskill = []\nmodel = []\n'
_KIND_DIRECTORY = {
    PluginKind.AGENT: "agents",
    PluginKind.MCP: "mcp",
    PluginKind.SKILL: "skills",
    PluginKind.MODEL: "models",
}
_KIND_EXTRA = {
    PluginKind.AGENT: 'entrypoint = "agent:Agent"\n',
    PluginKind.MCP: '[server]\ncommand = "npx"\n',
    PluginKind.SKILL: "",
    PluginKind.MODEL: "",
}


def _key(kind: PluginKind, name: str) -> PluginKey:
    return PluginKey(kind=kind, name=PluginName(name))


def _write_plugin(root: Path, kind: PluginKind, name: str) -> None:
    """종류를 가리지 않고 매니페스트 하나. 켜고 끄는 키는 매니페스트의 내용이 아니라 그 파일의
    존재다."""
    directory = root / _KIND_DIRECTORY[kind] / name
    directory.mkdir(parents=True)
    (directory / "plugin.toml").write_text(
        _manifest(kind.value, name, _KIND_EXTRA[kind]), encoding="utf-8"
    )


def _operator_file(root: Path, text: str) -> Path:
    path = root / DISABLED
    path.write_text(text, encoding="utf-8")
    return path


def _loaded(root: Path) -> dict[str, object]:
    """쓴 파일을 표준 라이브러리로 읽은 값. 쓰기 코드가 맞게 쓰는지는 이것이 판정한다(ADR 0017)."""
    return tomllib.loads((root / DISABLED).read_text(encoding="utf-8"))


def _root_entries(root: Path) -> set[str]:
    """플러그인 루트에 있는 것. 임시 파일이 남았는지 보는 자리다."""
    return {child.name for child in root.iterdir()}


def _plugins(root: Path) -> PluginSource:
    return FilesystemPlugins(root)


def test_운영자_파일이_없으면_꺼진_것이_없다(root: Path) -> None:
    """기본은 켜짐이고 파일에는 끈 것만 적는다(ADR 0017). 새 에이전트를 넣을 때 켜는 단계가 없다
    (스토리 19)."""
    _write_agent(root, "calc")

    assert _plugins(root).read_disabled() == frozenset()


def test_운영자_파일의_이름_배열이_꺼진_집합이고_빠진_키는_빈_목록이며_중복은_하나로_합친다(
    root: Path,
) -> None:
    """손으로 적은 파일에서 키가 빠지거나 이름이 겹쳐도 뜻이 하나로만 읽힌다(스토리 24)."""
    _operator_file(root, 'schema_version = "1"\nagent = ["calc", "calc"]\nmcp = ["everything"]\n')

    assert _plugins(root).read_disabled() == {
        _key(PluginKind.AGENT, "calc"),
        _key(PluginKind.MCP, "everything"),
    }


def test_운영자_파일의_종류_키가_플러그인_종류의_값_넷이다(root: Path) -> None:
    """키 이름은 `PluginKind` 의 값과 같다(ADR 0017). 종류마다 하나씩 끄면 넷이 전부 읽힌다."""
    _operator_file(
        root,
        'schema_version = "1"\nagent = ["a1"]\nmcp = ["m1"]\nskill = ["s1"]\nmodel = ["d1"]\n',
    )

    assert _plugins(root).read_disabled() == {
        _key(PluginKind.AGENT, "a1"),
        _key(PluginKind.MCP, "m1"),
        _key(PluginKind.SKILL, "s1"),
        _key(PluginKind.MODEL, "d1"),
    }


# 손상의 모양. 매니페스트에서 여는 것부터 검증까지를 PluginError 로 바꾸는 선례와 같다.
CORRUPT = (
    pytest.param('schema_version = "1"\nagent = [', id="문법 오류"),
    pytest.param("", id="빈 파일"),
    pytest.param('agent = ["calc"]\n', id="형식 버전이 없음"),
    pytest.param('schema_version = "2"\nagent = ["calc"]\n', id="모르는 형식 버전"),
    pytest.param('schema_version = "1"\nagents = ["calc"]\n', id="모르는 키"),
    pytest.param('schema_version = "1"\nagent = ["MyAgent"]\n', id="패턴을 어긴 이름"),
    pytest.param('schema_version = "1"\nagent = "calc"\n', id="배열이 아닌 값"),
    pytest.param('schema_version = "1"\nagent = [1]\n', id="문자열이 아닌 원소"),
)


@pytest.mark.parametrize("text", CORRUPT)
def test_운영자_파일의_손상은_PluginError이고_메시지에_파일_경로가_있다(
    root: Path, text: str
) -> None:
    """무엇이 꺼져 있는지 모르는 채 돌리면 끈 것이 돈다(스토리 20·21). 빈 파일도 손상이다 — 형식
    버전이 없는 파일을 "아무것도 꺼지지 않았다"로 읽으면 잘린 파일이 끈 것을 전부 켠다(스토리
    23)."""
    path = _operator_file(root, text)

    with pytest.raises(PluginError, match=re.escape(str(path))):
        _plugins(root).read_disabled()


def test_UTF_8로_읽지_못하는_운영자_파일도_손상이다(root: Path) -> None:
    path = root / DISABLED
    path.write_bytes(b'schema_version = "1"\nagent = ["\xff"]\n')

    with pytest.raises(PluginError, match=re.escape(str(path))):
        _plugins(root).read_disabled()


def test_디렉터리가_없는_이름은_손상이_아니라_꺼진_집합에_든다(root: Path) -> None:
    """지운 플러그인의 이름이 남아도 에러가 아니다. 같은 이름이 다시 들어오면 꺼진 채로 오는 것이
    안전한 쪽이다(스토리 15)."""
    _operator_file(root, 'schema_version = "1"\nagent = ["ghost"]\n')

    assert _plugins(root).read_disabled() == {_key(PluginKind.AGENT, "ghost")}


def test_끄면_파일이_생기고_켜면_그_이름이_빠지며_마지막_것을_켜도_파일은_남고_네_배열이_빈다(
    root: Path,
) -> None:
    """끈 것은 지운 것이 아니라 같은 길로 되돌린다(스토리 1·2). 파일을 지우면 쓰기 말고 삭제라는
    둘째 경로가 생기므로 남긴다. 성공 뒤에 임시 파일이 남지 않는다."""
    _write_agent(root, "calc")
    plugins = _plugins(root)

    disabled = plugins.write_enabled(PluginKind.AGENT, PluginName("calc"), enabled=False)
    written = _loaded(root)
    enabled = plugins.write_enabled(PluginKind.AGENT, PluginName("calc"), enabled=True)

    assert disabled == "applied"
    assert written == {
        "schema_version": "1",
        "agent": ["calc"],
        "mcp": [],
        "skill": [],
        "model": [],
    }
    assert enabled == "applied"
    assert _loaded(root) == {
        "schema_version": "1",
        "agent": [],
        "mcp": [],
        "skill": [],
        "model": [],
    }
    assert plugins.read_disabled() == frozenset()
    assert _root_entries(root) == {"agents", DISABLED}


def test_쓴_파일은_정규형이라_종류_넷이_모두_있고_이름순이며_중복이_없고_주석이_사라진다(
    root: Path,
) -> None:
    """git 의 변경이 켜고 끈 것만 보여야 한다(스토리 25). 주석을 남기려면 손으로 고친다(스토리
    26)."""
    for name in ("alpha", "beta", "gamma"):
        _write_agent(root, name)
    _write_mcp(root, "everything")
    _operator_file(
        root,
        "# 손으로 적었다\n"
        'mcp = ["everything"]\n'
        'schema_version = "1"\n'
        'agent = ["gamma", "alpha", "gamma"]\n',
    )

    _plugins(root).write_enabled(PluginKind.AGENT, PluginName("beta"), enabled=False)

    assert (root / DISABLED).read_text(encoding="utf-8") == (
        'schema_version = "1"\n'
        'agent = ["alpha", "beta", "gamma"]\n'
        'mcp = ["everything"]\n'
        "skill = []\n"
        "model = []\n"
    )


# 왕복의 집합들. 빈 것, 종류마다 하나, 패턴의 경계 문자를 쓴 이름.
LONGEST = "a" + "z" * 62
ROUND_TRIPS = (
    pytest.param((), id="빈 집합"),
    pytest.param(
        (
            (PluginKind.AGENT, "calc"),
            (PluginKind.MCP, "everything"),
            (PluginKind.SKILL, "summarize"),
            (PluginKind.MODEL, "sonnet"),
        ),
        id="종류마다 하나",
    ),
    pytest.param(
        ((PluginKind.AGENT, "ab"), (PluginKind.AGENT, "a0-9-z"), (PluginKind.AGENT, LONGEST)),
        id="패턴의 경계 문자",
    ),
)


@pytest.mark.parametrize("keys", ROUND_TRIPS)
def test_쓴_파일을_tomllib으로_읽으면_쓴_집합_그대로다(
    root: Path, keys: Sequence[tuple[PluginKind, str]]
) -> None:
    """쓰기 코드는 직접 짜고 맞게 쓰는지는 표준 라이브러리가 판정한다(ADR 0017). 쓰기 의존성을
    들이지 않는다."""
    _write_agent(root, "seed")
    for kind, name in keys:
        _write_plugin(root, kind, name)
    plugins = _plugins(root)
    for kind, name in keys:
        plugins.write_enabled(kind, PluginName(name), enabled=False)
    # 빈 집합에도 파일이 서게 하려고 하나를 껐다 켠다. 켜도 파일은 남는다.
    plugins.write_enabled(PluginKind.AGENT, PluginName("seed"), enabled=False)
    plugins.write_enabled(PluginKind.AGENT, PluginName("seed"), enabled=True)

    loaded = _loaded(root)

    assert loaded == {
        "schema_version": "1",
        **{kind.value: sorted(name for k, name in keys if k is kind) for kind in PluginKind},
    }
    assert plugins.read_disabled() == {_key(kind, name) for kind, name in keys}


def test_쓰기가_고아_항목을_지우지_않는다(root: Path) -> None:
    """디렉터리가 없는 이름은 손편집으로만 지운다(스토리 16). 그 이름의 PUT 은 부재라 켤 수 없다."""
    _write_agent(root, "calc")
    _operator_file(root, 'schema_version = "1"\nagent = ["ghost"]\n')

    _plugins(root).write_enabled(PluginKind.AGENT, PluginName("calc"), enabled=False)

    assert _loaded(root)["agent"] == ["calc", "ghost"]


def test_없는_이름에_쓰면_부재를_값으로_돌려주고_파일은_바이트_그대로다(root: Path) -> None:
    """오타로 지은 이름이 파일에 쌓이면 안 된다(스토리 5). 없었으면 여전히 없다."""
    _write_agent(root, "calc")
    plugins = _plugins(root)

    before_file = plugins.write_enabled(PluginKind.AGENT, PluginName("nope"), enabled=False)
    assert before_file == "absent"
    assert not (root / DISABLED).exists()

    path = _operator_file(root, "# 주석\nschema_version = \"1\"\nagent = ['calc']\n")
    original = path.read_bytes()
    other_kind = plugins.write_enabled(PluginKind.MCP, PluginName("calc"), enabled=False)

    assert other_kind == "absent"
    assert path.read_bytes() == original


def test_운영자_파일이_깨졌어도_없는_이름은_부재다(root: Path) -> None:
    """부재 판정이 먼저다(ADR 0017 의 2026-09-27 둘째 이력). 없는 이름을 두고 파일이 깨졌다고
    답하면 운영자는 이름이 맞다고 믿은 채 파일을 고치러 간다."""
    _write_agent(root, "calc")
    path = _operator_file(root, "not toml at all ][")
    original = path.read_bytes()

    outcome = _plugins(root).write_enabled(PluginKind.AGENT, PluginName("nope"), enabled=False)

    assert outcome == "absent"
    assert path.read_bytes() == original


def test_매니페스트가_깨진_플러그인에도_쓸_수_있다(root: Path) -> None:
    """고칠 때까지 런타임이 부르지 않게 하려는 것이 끄는 이유일 수 있다(스토리 6). 판정 대상은
    파일이 있느냐이지 읽히느냐가 아니다."""
    _write_broken(root)

    outcome = _plugins(root).write_enabled(
        PluginKind.AGENT, PluginName("badversion"), enabled=False
    )

    assert outcome == "applied"
    assert _loaded(root)["agent"] == ["badversion"]


def test_깨진_파일에_쓰면_PluginError이고_파일이_바이트_그대로다_바뀌는_것이_없는_쓰기도_같다(
    root: Path,
) -> None:
    """덮어쓰면 끈 것이 조용히 켜질 수 있다(스토리 22). 손상 판정이 "바뀌는 것이 없다"는 판단보다
    먼저라 켜진 것을 켜는 요청도 거부한다."""
    _write_agent(root, "calc")
    path = _operator_file(root, 'schema_version = "1"\nagent = "calc"\n')
    original = path.read_bytes()
    plugins = _plugins(root)

    with pytest.raises(PluginError, match=re.escape(str(path))):
        plugins.write_enabled(PluginKind.AGENT, PluginName("calc"), enabled=False)
    with pytest.raises(PluginError, match=re.escape(str(path))):
        plugins.write_enabled(PluginKind.AGENT, PluginName("calc"), enabled=True)

    assert path.read_bytes() == original
    assert _root_entries(root) == {"agents", DISABLED}


def test_바뀌는_것이_없는_쓰기는_파일을_건드리지_않는다(root: Path) -> None:
    """주석이 이유 없이 사라지거나 없던 파일이 생기면 안 된다(스토리 27). 이미 꺼진 것을 끄고 켜진
    것을 켜는 것이 그렇다."""
    _write_agent(root, "calc")
    _write_agent(root, "echo")
    plugins = _plugins(root)

    assert plugins.write_enabled(PluginKind.AGENT, PluginName("echo"), enabled=True) == "applied"
    assert not (root / DISABLED).exists()

    path = _operator_file(root, '# 주석\nschema_version = "1"\nagent = ["calc"]\n')
    original = path.read_bytes()
    assert plugins.write_enabled(PluginKind.AGENT, PluginName("calc"), enabled=False) == "applied"
    assert plugins.write_enabled(PluginKind.AGENT, PluginName("echo"), enabled=True) == "applied"

    assert path.read_bytes() == original


@dataclasses.dataclass
class Injected:
    """주입한 실패의 기록. 몇 번 거절했는지가 곧 재시도가 실제로 돌았다는 증거다."""

    refusals: int = 0


def _refuse_reads(
    monkeypatch: pytest.MonkeyPatch, *, error: OSError, times: int | None
) -> Injected:
    """운영자 파일 읽기를 times 번(None 이면 끝까지) 거절한다. 매니페스트 읽기는 건드리지 않는다."""
    injected = Injected()
    original = Path.read_text

    def refuse(self: Path, encoding: str | None = None, errors: str | None = None) -> str:
        if self.name == DISABLED and (times is None or injected.refusals < times):
            injected.refusals += 1
            raise error
        return original(self, encoding, errors)

    monkeypatch.setattr(Path, "read_text", refuse)
    return injected


def _refuse_replaces(
    monkeypatch: pytest.MonkeyPatch, *, error: OSError, times: int | None
) -> Injected:
    """임시 파일을 운영자 파일로 바꾸는 교체를 times 번(None 이면 끝까지) 거절한다."""
    injected = Injected()
    original = os.replace

    def refuse(src: str | os.PathLike[str], dst: str | os.PathLike[str]) -> None:
        if times is None or injected.refusals < times:
            injected.refusals += 1
            raise error
        original(src, dst)

    monkeypatch.setattr(os, "replace", refuse)
    return injected


def test_읽기가_PermissionError를_몇_번_받다_성공하면_집합을_돌려준다(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """윈도우에서 교체되는 순간 여는 읽기가 그렇다. 상한 안에서 풀리면 500 이 아니다(ADR 0017 의
    2026-09-27 첫 이력)."""
    _operator_file(root, 'schema_version = "1"\nagent = ["calc"]\n')
    injected = _refuse_reads(
        monkeypatch, error=PermissionError(13, "다른 핸들이 쥐고 있다"), times=3
    )

    assert _plugins(root).read_disabled() == {_key(PluginKind.AGENT, "calc")}
    assert injected.refusals == 3


def test_읽기가_끝까지_PermissionError면_PluginError이고_메시지에_경로가_있다(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """오래 쥔 핸들 앞에서는 상한을 넘긴 뒤 규칙 그대로다. 다시 시도하긴 했다는 것을 거절 횟수가
    말한다."""
    path = _operator_file(root, 'schema_version = "1"\nagent = ["calc"]\n')
    injected = _refuse_reads(
        monkeypatch, error=PermissionError(13, "다른 핸들이 쥐고 있다"), times=None
    )

    with pytest.raises(PluginError, match=re.escape(str(path))):
        _plugins(root).read_disabled()
    assert injected.refusals >= 2


def test_PermissionError가_아닌_열기_실패는_다시_시도하지_않고_바로_PluginError다(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """다시 시도하는 것은 PermissionError 하나다. 끊긴 드라이브는 다시 읽어도 같다."""
    path = _operator_file(root, 'schema_version = "1"\nagent = ["calc"]\n')
    injected = _refuse_reads(monkeypatch, error=OSError(5, "입출력 오류"), times=None)

    with pytest.raises(PluginError, match=re.escape(str(path))):
        _plugins(root).read_disabled()
    assert injected.refusals == 1


def test_교체가_PermissionError를_몇_번_받다_성공하면_파일이_바뀌고_임시_파일이_없다(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """윈도우에서 다른 핸들이 연 파일을 교체할 때가 그렇다. 관리의 GET 이 스레드풀에서 읽는 사이
    PUT 이 쓰면 `serve` 하나 안에서도 부딪힌다(ADR 0017 의 2026-09-27 첫 이력)."""
    _write_agent(root, "calc")
    _operator_file(root, CANONICAL_EMPTY)
    injected = _refuse_replaces(
        monkeypatch, error=PermissionError(13, "다른 핸들이 쥐고 있다"), times=3
    )

    outcome = _plugins(root).write_enabled(PluginKind.AGENT, PluginName("calc"), enabled=False)

    assert outcome == "applied"
    assert injected.refusals == 3
    assert _loaded(root)["agent"] == ["calc"]
    assert _root_entries(root) == {"agents", DISABLED}


def test_교체가_끝까지_PermissionError면_PluginError이고_옛_파일이_그대로이며_임시_파일이_없다(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """실패한 쓰기가 켜짐을 바꾸면 안 된다(스토리 29). 옛 파일은 바이트 그대로이고, 임시 파일이
    남으면 다음 사람이 무엇인지 모른다."""
    _write_agent(root, "calc")
    path = _operator_file(root, CANONICAL_EMPTY)
    original = path.read_bytes()
    injected = _refuse_replaces(
        monkeypatch, error=PermissionError(13, "다른 핸들이 쥐고 있다"), times=None
    )

    with pytest.raises(PluginError, match=re.escape(str(path))):
        _plugins(root).write_enabled(PluginKind.AGENT, PluginName("calc"), enabled=False)

    assert injected.refusals >= 2
    assert path.read_bytes() == original
    assert _root_entries(root) == {"agents", DISABLED}


def test_PermissionError가_아닌_쓰기_실패는_다시_시도하지_않고_PluginError이며_옛_파일이_그대로다(
    root: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """가득 찬 디스크는 다시 써도 같다. 옛 파일은 그대로이고 임시 파일도 남지 않는다."""
    _write_agent(root, "calc")
    path = _operator_file(root, CANONICAL_EMPTY)
    original = path.read_bytes()
    injected = _refuse_replaces(monkeypatch, error=OSError(28, "디스크가 가득 찼다"), times=None)

    with pytest.raises(PluginError, match=re.escape(str(path))):
        _plugins(root).write_enabled(PluginKind.AGENT, PluginName("calc"), enabled=False)

    assert injected.refusals == 1
    assert path.read_bytes() == original
    assert _root_entries(root) == {"agents", DISABLED}


# 실제 핸들로 재는 넷. 윈도우에서는 다른 핸들이 연 파일의 교체와, 교체되는 순간 여는 읽기가
# PermissionError 라서(ADR 0017 의 2026-09-27 첫 이력) 이 넷이 재시도를 실제로 지난다. 윈도우가 아닌
# 러너에서는 교체가 원자적이라 그 오류가 없고, 같은 단언이 "열린 채 읽는 쪽이 있어도 교체가 막히지
# 않는다"와 "교체되는 도중에도 읽기는 언제나 완전한 집합 하나를 본다"를 잰다. skip 하지 않는다.
# 교체하는 쪽도 실제 어댑터다. ADR 의 실측이 그 조건이고, 쉬지 않고 `os.replace` 만 도는 쓰기는 읽기
# 여섯 시도가 전부 교체 창에 걸릴 만큼 잦아 실제 쓰기의 모양이 아니다(그렇게 쟀을 때 한 번
# 빨개졌다).
HOLD_SECONDS = 0.004
TOGGLE_SECONDS = 0.3
CALC_DISABLED = 'schema_version = "1"\nagent = ["calc"]\n'
# 다른 프로세스가 파일을 연 채 잠깐 쥔다. 열었다는 신호를 표준 출력으로 보낸다.
HOLDER = """
import sys, time
with open(sys.argv[1], "rb"):
    print("opened", flush=True)
    time.sleep(float(sys.argv[2]))
"""
# 다른 프로세스가 실제 어댑터로 calc 를 켜고 끈다. 자기 쓰기가 상한을 넘겨 PluginError 면 세고
# 계속한다 — ADR 0017 이 받아들인 것이고, 재는 것은 그쪽이 아니라 이쪽의 읽기다. 센 수는 마지막 줄로
# 나가고 종료 코드 0 이 예기치 않은 예외 없이 끝났다는 뜻이다.
TOGGLER = """
import sys, time
from pathlib import Path
from agent_os.adapters.filesystem import FilesystemPlugins
from agent_os.core.ports import PluginError
from agent_os.sdk import PluginKind, PluginName
plugins = FilesystemPlugins(Path(sys.argv[1]))
deadline = time.monotonic() + float(sys.argv[2])
print("started", flush=True)
enabled = True
capped = 0
while time.monotonic() < deadline:
    try:
        plugins.write_enabled(PluginKind.AGENT, PluginName("calc"), enabled=enabled)
    except PluginError:
        capped += 1
    enabled = not enabled
print(capped, flush=True)
"""


def _toggle(root: Path, seconds: float) -> int:
    """같은 프로세스의 다른 스레드가 실제 어댑터로 calc 를 켜고 끈다. 위 TOGGLER 와 같은 일이다.

    돌려주는 것은 상한을 넘긴 쓰기의 수다. 단언하지 않고 세기만 한다 — 재는 것은 이쪽의 읽기다.
    """
    plugins = _plugins(root)
    deadline = time.monotonic() + seconds
    enabled = True
    capped = 0
    while time.monotonic() < deadline:
        try:
            plugins.write_enabled(PluginKind.AGENT, PluginName("calc"), enabled=enabled)
        except PluginError:
            capped += 1
        enabled = not enabled
    return capped


# 켜고 끄는 동안 읽기가 볼 수 있는 상태 둘. 파일은 늘 있고 마지막 것을 켜도 남는다.
TOGGLED_STATES: set[frozenset[PluginKey]] = {
    frozenset(),
    frozenset({_key(PluginKind.AGENT, "calc")}),
}


def _assert_replaced_under_hold(root: Path, outcome: str) -> None:
    assert outcome == "applied"
    assert _loaded(root)["agent"] == ["calc"]
    assert _root_entries(root) == {"agents", DISABLED}


def test_다른_스레드가_운영자_파일을_연_채여도_교체가_재시도_안에서_성공한다(root: Path) -> None:
    """관리의 GET 은 스레드풀에서 읽고 PUT 은 이벤트 루프에서 쓴다. 그 핸들이 상한 안에 닫히면
    쓰기가 성공해야 한다."""
    _write_agent(root, "calc")
    path = _operator_file(root, CANONICAL_EMPTY)
    opened = threading.Event()

    def hold() -> None:
        with path.open("rb"):
            opened.set()
            time.sleep(HOLD_SECONDS)

    holder = threading.Thread(target=hold)
    holder.start()
    opened.wait()
    outcome = _plugins(root).write_enabled(PluginKind.AGENT, PluginName("calc"), enabled=False)
    holder.join()

    _assert_replaced_under_hold(root, outcome)


def test_다른_프로세스가_운영자_파일을_연_채여도_교체가_재시도_안에서_성공한다(root: Path) -> None:
    """손편집기나 다른 `serve` 가 잠깐 연 것이다."""
    _write_agent(root, "calc")
    path = _operator_file(root, CANONICAL_EMPTY)
    holder = subprocess.Popen(
        [sys.executable, "-c", HOLDER, str(path), str(HOLD_SECONDS)],
        stdout=subprocess.PIPE,
        text=True,
    )
    assert holder.stdout is not None
    assert holder.stdout.readline().strip() == "opened"
    outcome = _plugins(root).write_enabled(PluginKind.AGENT, PluginName("calc"), enabled=False)
    holder.wait(timeout=10)

    _assert_replaced_under_hold(root, outcome)


def _read_while(plugins: PluginSource, running: Callable[[], bool]) -> set[frozenset[PluginKey]]:
    """교체가 도는 동안 쉬지 않고 읽는다. 한 번이라도 PluginError 면 이 함수가 그대로 던진다."""
    seen: set[frozenset[PluginKey]] = set()
    while True:
        seen.add(plugins.read_disabled())
        if not running():
            return seen


def test_다른_스레드가_교체하는_동안의_읽기가_재시도_안에서_성공한다(root: Path) -> None:
    """읽기는 언제나 두 상태 가운데 하나를 본다. 반쪽 파일도, 500 도 없다. 관리의 GET 이
    스레드풀에서 읽는 사이 PUT 이 루프에서 쓰는 모양이다."""
    _write_agent(root, "calc")
    _operator_file(root, CALC_DISABLED)

    with ThreadPoolExecutor(max_workers=1) as pool:
        toggling = pool.submit(_toggle, root, TOGGLE_SECONDS)
        seen = _read_while(_plugins(root), lambda: not toggling.done())
    toggling.result()

    assert seen == TOGGLED_STATES


def test_다른_프로세스가_교체하는_동안의_읽기가_재시도_안에서_성공한다(root: Path) -> None:
    """다른 `serve` 나 스크립트가 같은 파일을 쓰는 것이다. 나중에 쓴 쪽이 이기지만(스토리 44) 읽기는
    어느 쪽이든 완전한 파일을 본다."""
    _write_agent(root, "calc")
    _operator_file(root, CALC_DISABLED)
    toggler = subprocess.Popen(
        [sys.executable, "-c", TOGGLER, str(root), str(TOGGLE_SECONDS)],
        stdout=subprocess.PIPE,
        text=True,
    )
    assert toggler.stdout is not None
    assert toggler.stdout.readline().strip() == "started"

    seen = _read_while(_plugins(root), lambda: toggler.poll() is None)

    assert toggler.wait(timeout=10) == 0
    assert seen == TOGGLED_STATES
