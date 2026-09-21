"""주 이음매. 포트 다섯을 가짜로 주입하고 이벤트의 열만 단언한다. 네트워크가 없다.

가짜는 포트를 상속하지 않고 시그니처로 만족한다. _run 의 인자 타입이 포트 적합성이 검증되는 자리다.
"""

import itertools
from collections.abc import AsyncGenerator, AsyncIterator, Iterator, Mapping, Sequence
from contextlib import asynccontextmanager
from datetime import UTC, datetime

import pytest
from langchain_core.language_models import LanguageModelInput
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from langchain_core.messages.tool import ToolCall
from langchain_core.runnables import Runnable

from agent_os.core.loop import MAX_TURNS
from agent_os.core.ports import (
    ChatModel,
    Clock,
    PluginError,
    PluginSource,
    ToolConnection,
    ToolResult,
    ToolSource,
    ToolSpec,
    TraceSink,
)
from agent_os.core.run import run
from agent_os.sdk import (
    AgentContext,
    AgentName,
    BaseAgent,
    Event,
    Json,
    LlmCalled,
    McpServer,
    PluginKind,
    PluginManifest,
    PluginName,
    Principal,
    RunFailed,
    RunFinished,
    RunId,
    RunStarted,
    ToolCalled,
    ToolError,
    parse_manifest,
)

FIXED_NOW = datetime(2026, 9, 21, 12, 0, tzinfo=UTC)
PRINCIPAL = Principal("alice")
SERVER = McpServer(command="fake-server")


def _agent_manifest(name: str, mcp: Sequence[str] = ()) -> PluginManifest:
    mcp_line = "mcp = [" + ", ".join(f'"{m}"' for m in mcp) + "]\n"
    return parse_manifest(
        f'schema_version = "1"\nkind = "agent"\nname = "{name}"\n'
        f'version = "0.1.0"\nentrypoint = "agent:Agent"\n{mcp_line}'
    )


def _mcp_manifest(name: str) -> PluginManifest:
    return parse_manifest(
        f'schema_version = "1"\nkind = "mcp"\nname = "{name}"\nversion = "0.1.0"\n'
        f'[server]\ncommand = "{SERVER.command}"\n'
    )


class FakeClock:
    def __init__(self) -> None:
        self.ids_issued = 0

    def now(self) -> datetime:
        return FIXED_NOW

    def new_run_id(self) -> RunId:
        self.ids_issued += 1
        return RunId(f"run-{self.ids_issued}")


class FakeTrace:
    def __init__(self) -> None:
        self.events: list[Event] = []

    def write(self, event: Event) -> None:
        self.events.append(event)


class FakePlugins:
    def __init__(
        self,
        agents: dict[str, BaseAgent],
        mcp: Sequence[str] = (),
        servers: Sequence[str] = (),
    ) -> None:
        self._agents = agents
        self._mcp = tuple(mcp)
        self._servers = tuple(servers)

    def read_manifest(self, kind: PluginKind, name: PluginName) -> PluginManifest | None:
        if kind is PluginKind.AGENT and name in self._agents:
            return _agent_manifest(name, self._mcp)
        if kind is PluginKind.MCP and name in self._servers:
            return _mcp_manifest(name)
        return None

    def load_agent(self, manifest: PluginManifest) -> BaseAgent:
        return self._agents[manifest.name]


class FakeConnection:
    def __init__(self, results: Mapping[str, str | Exception]) -> None:
        self._results = results
        self.calls: list[tuple[str, Mapping[str, Json]]] = []

    def tools(self) -> Sequence[ToolSpec]:
        return [ToolSpec(name=n, description=n, input_schema={}) for n in self._results]

    async def call(self, name: str, args: Mapping[str, Json]) -> ToolResult:
        self.calls.append((name, args))
        result = self._results[name]
        if isinstance(result, Exception):
            raise result
        return ToolResult(ok=True, content=result)


class FakeTools:
    """이름별로 결과나 에러를 정해 둔다. 어떤 서버를 받았고 닫혔는지 기록한다."""

    def __init__(self, results: Mapping[str, str | Exception] | None = None) -> None:
        self.connection = FakeConnection(results or {})
        self.servers: Mapping[PluginName, McpServer] | None = None
        self.closed = False

    @asynccontextmanager
    async def connect(
        self, servers: Mapping[PluginName, McpServer]
    ) -> AsyncGenerator[ToolConnection]:
        self.servers = servers
        try:
            yield self.connection
        finally:
            self.closed = True


class BrokenTools:
    """MCP 서버 기동 실패."""

    @asynccontextmanager
    async def connect(
        self, servers: Mapping[PluginName, McpServer]
    ) -> AsyncGenerator[ToolConnection]:
        raise ConnectionError("server did not start")
        yield FakeConnection({})


class ToolAwareFakeModel(GenericFakeChatModel):
    """bind_tools 를 받아들이기만 하는 가짜. 응답은 정해진 대로."""

    def bind_tools(
        self,
        tools: Sequence[object],
        *,
        tool_choice: str | None = None,
        **kwargs: object,
    ) -> Runnable[LanguageModelInput, AIMessage]:
        return self


class OneShotAgent:
    async def run(self, request: str, ctx: AgentContext) -> AsyncIterator[Event]:
        yield RunFinished(run_id=ctx.run_id, ts=ctx.now(), output=await ctx.llm(request))


class ChattyAgent:
    """자기 이벤트를 루프 앞뒤로 낸다. 순서 보장을 검증하기 위한 것."""

    async def run(self, request: str, ctx: AgentContext) -> AsyncIterator[Event]:
        yield ToolCalled(run_id=ctx.run_id, ts=ctx.now(), tool="before", ok=True)
        answer = await ctx.llm(request)
        yield ToolCalled(run_id=ctx.run_id, ts=ctx.now(), tool="after", ok=True)
        yield RunFinished(run_id=ctx.run_id, ts=ctx.now(), output=answer)


class SilentAgent:
    """run_finished 없이 끝나는 잘못된 에이전트."""

    async def run(self, request: str, ctx: AgentContext) -> AsyncIterator[Event]:
        yield ToolCalled(run_id=ctx.run_id, ts=ctx.now(), tool="only", ok=True)


class DirectToolAgent:
    """모델을 거치지 않고 도구를 직접 부른다."""

    async def run(self, request: str, ctx: AgentContext) -> AsyncIterator[Event]:
        try:
            output = await ctx.tool("add", a=2, b=2)
        except ToolError as error:
            output = f"error:{error}"
        yield RunFinished(run_id=ctx.run_id, ts=ctx.now(), output=output)


def _reply(text: str) -> AIMessage:
    return AIMessage(
        content=text,
        response_metadata={"model_name": "fake-model"},
        usage_metadata={"input_tokens": 7, "output_tokens": 3, "total_tokens": 10},
    )


def _tool_request(name: str = "add") -> AIMessage:
    return AIMessage(content="", tool_calls=[ToolCall(name=name, args={"a": 2, "b": 2}, id="c1")])


def _failing_replies() -> Iterator[AIMessage | str]:
    raise RuntimeError("API down")
    yield AIMessage(content="unreachable")


async def _run(
    agent: BaseAgent,
    model: ChatModel,
    trace: TraceSink,
    clock: Clock,
    tools: ToolSource | None = None,
    plugins: PluginSource | None = None,
    name: str = "calc",
) -> list[Event]:
    plugins = plugins or FakePlugins({"calc": agent})
    tools = tools or FakeTools()
    return [
        event
        async for event in run(
            AgentName(name),
            "2+2?",
            PRINCIPAL,
            plugins=plugins,
            model=model,
            tools=tools,
            trace=trace,
            clock=clock,
        )
    ]


@pytest.fixture
def trace() -> FakeTrace:
    return FakeTrace()


@pytest.fixture
def clock() -> FakeClock:
    return FakeClock()


async def test_도구_없는_에이전트는_시작_모델호출_종료로_끝난다(
    trace: FakeTrace, clock: FakeClock
) -> None:
    model = GenericFakeChatModel(messages=iter([_reply("4")]))

    events = await _run(OneShotAgent(), model, trace, clock)

    assert [e.type for e in events] == ["run_started", "llm_called", "run_finished"]
    assert isinstance(events[-1], RunFinished)
    assert events[-1].output == "4"


async def test_모든_이벤트에_같은_실행_식별자가_붙고_시작_이벤트에_주체가_있다(
    trace: FakeTrace, clock: FakeClock
) -> None:
    model = GenericFakeChatModel(messages=iter([_reply("4")]))

    events = await _run(OneShotAgent(), model, trace, clock)

    assert {e.run_id for e in events} == {"run-1"}
    assert isinstance(events[0], RunStarted)
    assert events[0].principal == "alice"
    assert events[0].agent == "calc"


async def test_모델_호출마다_이벤트_하나에_모델_이름과_토큰_수가_담긴다(
    trace: FakeTrace, clock: FakeClock
) -> None:
    model = GenericFakeChatModel(messages=iter([_reply("4")]))

    events = await _run(OneShotAgent(), model, trace, clock)

    assert events[1] == LlmCalled(
        run_id=RunId("run-1"), ts=FIXED_NOW, model="fake-model", input_tokens=7, output_tokens=3
    )


async def test_컨텍스트_호출_안의_이벤트가_그_호출_뒤_에이전트_이벤트보다_앞선다(
    trace: FakeTrace, clock: FakeClock
) -> None:
    model = GenericFakeChatModel(messages=iter([_reply("4")]))

    events = await _run(ChattyAgent(), model, trace, clock)

    assert [e.type for e in events] == [
        "run_started",
        "tool_called",  # before
        "llm_called",
        "tool_called",  # after
        "run_finished",
    ]


async def test_실행_함수는_내는_모든_이벤트를_트레이스에_쓴다(
    trace: FakeTrace, clock: FakeClock
) -> None:
    model = GenericFakeChatModel(messages=iter([_reply("4")]))

    events = await _run(ChattyAgent(), model, trace, clock)

    assert trace.events == events


async def test_루프가_상한을_넘으면_실패_이벤트로_끝난다(
    trace: FakeTrace, clock: FakeClock
) -> None:
    model = ToolAwareFakeModel(messages=itertools.repeat(_tool_request()))
    tools = FakeTools({"add": "4"})

    events = await _run(OneShotAgent(), model, trace, clock, tools=tools)

    assert sum(1 for e in events if e.type == "llm_called") == MAX_TURNS
    assert isinstance(events[-1], RunFailed)
    assert f"{MAX_TURNS}턴" in events[-1].error


async def test_모델_호출이_실패하면_실패_이벤트로_끝나고_트레이스가_남는다(
    trace: FakeTrace, clock: FakeClock
) -> None:
    model = GenericFakeChatModel(messages=_failing_replies())

    events = await _run(OneShotAgent(), model, trace, clock)

    assert [e.type for e in events] == ["run_started", "run_failed"]
    assert isinstance(events[-1], RunFailed)
    assert "API down" in events[-1].error
    assert trace.events == events


async def test_에이전트가_종료_이벤트_없이_끝나면_실패_이벤트로_끝난다(
    trace: FakeTrace, clock: FakeClock
) -> None:
    model = GenericFakeChatModel(messages=iter([_reply("4")]))

    events = await _run(SilentAgent(), model, trace, clock)

    assert [e.type for e in events] == ["run_started", "tool_called", "run_failed"]


async def test_없는_에이전트는_실행_식별자도_트레이스도_없이_실행_전에_끝난다(
    trace: FakeTrace, clock: FakeClock
) -> None:
    model = GenericFakeChatModel(messages=iter([_reply("4")]))

    with pytest.raises(PluginError, match="nope"):
        await _run(OneShotAgent(), model, trace, clock, name="nope")

    assert clock.ids_issued == 0
    assert trace.events == []


async def test_도구를_쓰는_에이전트는_모델호출과_도구호출이_순서대로_들어간다(
    trace: FakeTrace, clock: FakeClock
) -> None:
    model = ToolAwareFakeModel(messages=iter([_tool_request(), _reply("4")]))
    tools = FakeTools({"add": "4"})
    plugins = FakePlugins({"calc": OneShotAgent()}, mcp=["srv"], servers=["srv"])

    events = await _run(OneShotAgent(), model, trace, clock, tools=tools, plugins=plugins)

    assert [e.type for e in events] == [
        "run_started",
        "llm_called",
        "tool_called",
        "llm_called",
        "run_finished",
    ]
    assert events[2] == ToolCalled(run_id=RunId("run-1"), ts=FIXED_NOW, tool="add", ok=True)
    assert tools.connection.calls == [("add", {"a": 2, "b": 2})]


async def test_매니페스트가_지정한_서버만_붙는다(trace: FakeTrace, clock: FakeClock) -> None:
    model = GenericFakeChatModel(messages=iter([_reply("4")]))
    tools = FakeTools()
    plugins = FakePlugins({"calc": OneShotAgent()}, mcp=["one"], servers=["one", "other"])

    await _run(OneShotAgent(), model, trace, clock, tools=tools, plugins=plugins)

    assert tools.servers == {"one": SERVER}


async def test_지정이_비면_도구_없이_돈다(trace: FakeTrace, clock: FakeClock) -> None:
    model = GenericFakeChatModel(messages=iter([_reply("4")]))
    tools = FakeTools({"add": "4"})
    plugins = FakePlugins({"calc": OneShotAgent()}, mcp=[], servers=["one"])

    events = await _run(OneShotAgent(), model, trace, clock, tools=tools, plugins=plugins)

    assert tools.servers == {}
    assert "tool_called" not in [e.type for e in events]


async def test_지정한_mcp_이름이_실재하지_않으면_실행_전에_끝난다(
    trace: FakeTrace, clock: FakeClock
) -> None:
    model = GenericFakeChatModel(messages=iter([_reply("4")]))
    plugins = FakePlugins({"calc": OneShotAgent()}, mcp=["ghost"], servers=[])

    with pytest.raises(PluginError, match="ghost"):
        await _run(OneShotAgent(), model, trace, clock, plugins=plugins)

    assert clock.ids_issued == 0
    assert trace.events == []


async def test_MCP_서버_기동_실패는_실패_이벤트로_끝나고_트레이스가_남는다(
    trace: FakeTrace, clock: FakeClock
) -> None:
    model = GenericFakeChatModel(messages=iter([_reply("4")]))

    events = await _run(OneShotAgent(), model, trace, clock, tools=BrokenTools())

    assert [e.type for e in events] == ["run_started", "run_failed"]
    assert isinstance(events[-1], RunFailed)
    assert "server did not start" in events[-1].error
    assert trace.events == events


async def test_도구_에러는_실패로_기록되고_루프는_계속된다(
    trace: FakeTrace, clock: FakeClock
) -> None:
    model = ToolAwareFakeModel(messages=iter([_tool_request(), _reply("포기")]))
    tools = FakeTools({"add": ValueError("overflow")})

    events = await _run(OneShotAgent(), model, trace, clock, tools=tools)

    assert [e.type for e in events] == [
        "run_started",
        "llm_called",
        "tool_called",
        "llm_called",
        "run_finished",
    ]
    assert isinstance(events[2], ToolCalled)
    assert events[2].ok is False


async def test_컨텍스트는_모델을_거치지_않고_도구를_직접_부른다(
    trace: FakeTrace, clock: FakeClock
) -> None:
    model = GenericFakeChatModel(messages=iter([]))
    tools = FakeTools({"add": "4"})

    events = await _run(DirectToolAgent(), model, trace, clock, tools=tools)

    assert [e.type for e in events] == ["run_started", "tool_called", "run_finished"]
    assert isinstance(events[-1], RunFinished)
    assert events[-1].output == "4"
    assert tools.connection.calls == [("add", {"a": 2, "b": 2})]


async def test_직접_부른_도구가_실패하면_에이전트가_잡을_수_있는_ToolError다(
    trace: FakeTrace, clock: FakeClock
) -> None:
    model = GenericFakeChatModel(messages=iter([]))
    tools = FakeTools({"add": RuntimeError("boom")})

    events = await _run(DirectToolAgent(), model, trace, clock, tools=tools)

    assert [e.type for e in events] == ["run_started", "tool_called", "run_finished"]
    assert isinstance(events[1], ToolCalled)
    assert events[1].ok is False
    assert isinstance(events[-1], RunFinished)
    assert "boom" in events[-1].output


async def test_도구_연결은_실행이_실패해도_닫힌다(trace: FakeTrace, clock: FakeClock) -> None:
    model = GenericFakeChatModel(messages=_failing_replies())
    tools = FakeTools()

    await _run(OneShotAgent(), model, trace, clock, tools=tools)

    assert tools.closed is True
