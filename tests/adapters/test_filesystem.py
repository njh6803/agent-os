"""파일시스템 PluginSource. 디렉터리에 놓는 것만으로 등록이 끝나는지."""

from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

import pytest

from agent_os.adapters.filesystem import FilesystemPlugins
from agent_os.core.ports import ManifestRow, PluginError, PluginSource, UnreadableManifest
from agent_os.sdk import (
    AgentContext,
    BaseAgent,
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
