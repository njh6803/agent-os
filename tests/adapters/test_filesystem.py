"""파일시스템 PluginSource. 디렉터리에 놓는 것만으로 등록이 끝나는지."""

from datetime import UTC, datetime
from pathlib import Path

import pytest

from agent_os.adapters.filesystem import FilesystemPlugins
from agent_os.core.ports import PluginError, PluginSource
from agent_os.sdk import AgentContext, BaseAgent, Event, PluginKind, PluginName, RunFinished, RunId

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
