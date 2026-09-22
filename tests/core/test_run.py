"""주 이음매. 포트 다섯을 가짜로 주입하고 이벤트의 열만 단언한다. 네트워크가 없다.

가짜는 포트를 상속하지 않고 시그니처로 만족한다. _run 의 인자 타입이 포트 적합성이 검증되는 자리다.
"""

import itertools
from collections.abc import AsyncGenerator, AsyncIterator, Iterator, Mapping, Sequence
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta

import pytest
from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models import LanguageModelInput
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.messages.tool import ToolCall as LangchainToolCall
from langchain_core.outputs import ChatResult
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
    Trace,
    TraceSchemaVersion,
    TraceStore,
    UnknownEvent,
)
from agent_os.core.run import Approve, resume, run
from agent_os.sdk import (
    AgentContext,
    AgentName,
    ApprovalGranted,
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
    RunPaused,
    RunResumed,
    RunStarted,
    ToolCall,
    ToolCalled,
    ToolError,
    parse_manifest,
)

FIXED_NOW = datetime(2026, 9, 21, 12, 0, tzinfo=UTC)
PRINCIPAL = Principal("alice")
SERVER = McpServer(command="fake-server")


def _toml_list(names: Sequence[str]) -> str:
    return "[" + ", ".join(f'"{name}"' for name in names) + "]"


def _agent_manifest(
    name: str, mcp: Sequence[str] = (), requires_approval: Sequence[str] = ()
) -> PluginManifest:
    return parse_manifest(
        f'schema_version = "1"\nkind = "agent"\nname = "{name}"\n'
        f'version = "0.1.0"\nentrypoint = "agent:Agent"\n'
        f"mcp = {_toml_list(mcp)}\nrequires_approval = {_toml_list(requires_approval)}\n"
    )


def _mcp_manifest(
    name: str, secret_args: Mapping[str, Sequence[str]] | None = None
) -> PluginManifest:
    table = "".join(f"{tool} = {_toml_list(args)}\n" for tool, args in (secret_args or {}).items())
    return parse_manifest(
        f'schema_version = "1"\nkind = "mcp"\nname = "{name}"\nversion = "0.1.0"\n'
        f'[server]\ncommand = "{SERVER.command}"\n'
        + (f"\n[server.secret_args]\n{table}" if table else "")
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
    """쓴 것을 그대로 읽어 준다. schema_version 은 옛 형식을 재개하려는 경우를 만들 때만 준다."""

    def __init__(self, schema_version: TraceSchemaVersion = "2") -> None:
        self.events: list[Event] = []
        self._schema_version: TraceSchemaVersion = schema_version

    def write(self, event: Event) -> None:
        self.events.append(event)

    def read(self, run_id: RunId) -> Trace | None:
        events = tuple(e for e in self.events if e.run_id == run_id)
        if not events:
            return None
        return Trace(run_id=run_id, schema_version=self._schema_version, events=events)


class CorruptTrace(FakeTrace):
    """헤더의 실행 식별자와 이벤트의 것이 어긋난 파일. 손으로 고쳤거나 손상된 트레이스다."""

    def read(self, run_id: RunId) -> Trace | None:
        found = super().read(run_id)
        if found is None:
            return None
        intruder = RunPaused(run_id=RunId("다른-실행"), ts=FIXED_NOW, tool="x", args={})
        return Trace(
            run_id=found.run_id,
            schema_version=found.schema_version,
            events=(*found.events, intruder),
        )


class AdvancingClock:
    """부를 때마다 1초씩 간다. 재생 구간의 시각이 흔들리면 프롬프트 대조가 깨지는 것을 보이려고."""

    def __init__(self) -> None:
        self.ids_issued = 0
        self._ticks = 0

    def now(self) -> datetime:
        self._ticks += 1
        return FIXED_NOW + timedelta(seconds=self._ticks)

    def new_run_id(self) -> RunId:
        self.ids_issued += 1
        return RunId(f"run-{self.ids_issued}")


class FakePlugins:
    def __init__(
        self,
        agents: dict[str, BaseAgent],
        mcp: Sequence[str] = (),
        servers: Sequence[str] = (),
        requires_approval: Sequence[str] = (),
        secret_args: Mapping[str, Sequence[str]] | None = None,
    ) -> None:
        self._agents = agents
        self._mcp = tuple(mcp)
        self._servers = tuple(servers)
        self._requires_approval = tuple(requires_approval)
        self._secret_args = secret_args

    def read_manifest(self, kind: PluginKind, name: PluginName) -> PluginManifest | None:
        if kind is PluginKind.AGENT and name in self._agents:
            return _agent_manifest(name, self._mcp, self._requires_approval)
        if kind is PluginKind.MCP and name in self._servers:
            return _mcp_manifest(name, self._secret_args)
        return None

    def load_agent(self, manifest: PluginManifest) -> BaseAgent:
        return self._agents[manifest.name]


class FakeConnection:
    def __init__(
        self, results: Mapping[str, str | Exception], params: Mapping[str, Sequence[str]]
    ) -> None:
        self._results = results
        self._params = params
        self.calls: list[tuple[str, Mapping[str, Json]]] = []

    def tools(self) -> Sequence[ToolSpec]:
        return [
            ToolSpec(name=n, description=n, input_schema=_schema(self._params.get(n, ())))
            for n in self._results
        ]

    async def call(self, name: str, args: Mapping[str, Json]) -> ToolResult:
        self.calls.append((name, args))
        result = self._results[name]
        if isinstance(result, Exception):
            raise result
        return ToolResult(ok=True, content=result)


def _schema(params: Sequence[str]) -> Mapping[str, Json]:
    """MCP 서버가 주는 모양의 입력 스키마. 인자 이름은 properties 의 키다."""
    return {"type": "object", "properties": {name: {} for name in params}}


class FakeTools:
    """이름별로 결과나 에러를 정해 둔다. 어떤 서버를 받았고 닫혔는지 기록한다.

    params 는 도구별 인자 이름. 비밀 인자의 실재 검사가 보는 것이라 선언한 도구에만 준다.
    """

    def __init__(
        self,
        results: Mapping[str, str | Exception] | None = None,
        params: Mapping[str, Sequence[str]] | None = None,
    ) -> None:
        self.connection = FakeConnection(results or {}, params or {})
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
        yield FakeConnection({}, {})


class ToolAwareFakeModel(GenericFakeChatModel):
    """bind_tools 를 받아들이기만 하는 가짜. 응답은 정해진 대로이고 불린 횟수를 센다.

    횟수는 재생이 모델 포트에 닿지 않는다는 것을 세는 데 쓴다. 응답 iterator 가 소진되는 것으로는
    "모자라면 터진다"만 알 수 있지 "더 부르지 않았다"를 알 수 없다.
    """

    calls: int = 0

    def bind_tools(
        self,
        tools: Sequence[object],
        *,
        tool_choice: str | None = None,
        **kwargs: object,
    ) -> Runnable[LanguageModelInput, AIMessage]:
        return self

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: object,
    ) -> ChatResult:
        self.calls += 1
        return super()._generate(messages, stop, run_manager, **kwargs)


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


def _tool_request(*names: str) -> AIMessage:
    """모델이 한 턴에 낸 도구 호출들. 이름을 안 주면 add 하나다."""
    calls = [
        LangchainToolCall(name=name, args={"a": 2, "b": 2}, id=f"c{i}")
        for i, name in enumerate(names or ("add",), start=1)
    ]
    return AIMessage(content="", tool_calls=calls)


def _failing_replies() -> Iterator[AIMessage | str]:
    raise RuntimeError("API down")
    yield AIMessage(content="unreachable")


async def _run(
    agent: BaseAgent,
    model: ChatModel,
    trace: TraceStore,
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
        run_id=RunId("run-1"),
        ts=FIXED_NOW,
        model="fake-model",
        input_tokens=7,
        output_tokens=3,
        prompt="2+2?",
        text="4",
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


async def test_마스킹된_인자를_가진_도구를_승인_대상으로_적으면_실행_전에_끝난다(
    trace: FakeTrace, clock: FakeClock
) -> None:
    model = GenericFakeChatModel(messages=iter([_reply("4")]))
    plugins = FakePlugins(
        {"calc": OneShotAgent()},
        mcp=["mailer"],
        servers=["mailer"],
        requires_approval=["send_email"],
        secret_args={"send_email": ["api_key"]},
    )

    with pytest.raises(PluginError, match="send_email"):
        await _run(OneShotAgent(), model, trace, clock, plugins=plugins)

    assert clock.ids_issued == 0
    assert trace.events == []


async def test_마스킹이_걸리지_않은_도구는_승인_대상으로_적어도_실행된다(
    trace: FakeTrace, clock: FakeClock
) -> None:
    model = ToolAwareFakeModel(messages=iter([_reply("4")]))
    tools = FakeTools(
        {"read_inbox": "empty", "send_email": "sent"}, params={"send_email": ["api_key"]}
    )
    plugins = FakePlugins(
        {"calc": OneShotAgent()},
        mcp=["mailer"],
        servers=["mailer"],
        requires_approval=["read_inbox"],
        secret_args={"send_email": ["api_key"]},
    )

    events = await _run(OneShotAgent(), model, trace, clock, tools=tools, plugins=plugins)

    assert [e.type for e in events] == ["run_started", "llm_called", "run_finished"]


async def test_모델_호출_이벤트가_모델이_낸_텍스트와_도구_호출을_담는다(
    trace: FakeTrace, clock: FakeClock
) -> None:
    model = ToolAwareFakeModel(messages=iter([_tool_request(), _reply("4")]))
    tools = FakeTools({"add": "4"})

    events = await _run(OneShotAgent(), model, trace, clock, tools=tools)

    assert isinstance(events[1], LlmCalled)
    assert events[1].tool_calls == (ToolCall(id="c1", name="add", args={"a": 2, "b": 2}),)
    assert isinstance(events[3], LlmCalled)
    assert events[3].text == "4"
    assert events[3].tool_calls == ()


async def test_도구_호출_이벤트가_인자와_결과_내용을_담는다(
    trace: FakeTrace, clock: FakeClock
) -> None:
    model = ToolAwareFakeModel(messages=iter([_tool_request(), _reply("4")]))
    tools = FakeTools({"add": "4"})

    events = await _run(OneShotAgent(), model, trace, clock, tools=tools)

    assert events[2] == ToolCalled(
        run_id=RunId("run-1"),
        ts=FIXED_NOW,
        tool="add",
        ok=True,
        args={"a": 2, "b": 2},
        content="4",
    )


async def test_직접_부른_도구도_인자와_결과_내용을_담는다(
    trace: FakeTrace, clock: FakeClock
) -> None:
    model = GenericFakeChatModel(messages=iter([]))
    tools = FakeTools({"add": "4"})

    events = await _run(DirectToolAgent(), model, trace, clock, tools=tools)

    assert events[1] == ToolCalled(
        run_id=RunId("run-1"),
        ts=FIXED_NOW,
        tool="add",
        ok=True,
        args={"a": 2, "b": 2},
        content="4",
    )


async def test_실패한_도구_호출은_결과_내용에_에러를_담는다(
    trace: FakeTrace, clock: FakeClock
) -> None:
    model = GenericFakeChatModel(messages=iter([]))
    tools = FakeTools({"add": RuntimeError("boom")})

    events = await _run(DirectToolAgent(), model, trace, clock, tools=tools)

    assert isinstance(events[1], ToolCalled)
    assert events[1].ok is False
    assert "boom" in events[1].content


async def test_비밀로_선언된_인자는_마스킹돼_이벤트에_담긴다(
    trace: FakeTrace, clock: FakeClock
) -> None:
    model = ToolAwareFakeModel(messages=iter([_tool_request(), _reply("4")]))
    tools = FakeTools({"add": "4"}, params={"add": ["a", "b"]})
    plugins = FakePlugins(
        {"calc": OneShotAgent()}, mcp=["srv"], servers=["srv"], secret_args={"add": ["a"]}
    )

    events = await _run(OneShotAgent(), model, trace, clock, tools=tools, plugins=plugins)

    assert isinstance(events[1], LlmCalled)
    assert events[1].tool_calls[0].args == {"a": "***", "b": 2}
    assert isinstance(events[2], ToolCalled)
    assert events[2].args == {"a": "***", "b": 2}


async def test_마스킹은_이벤트에만_걸리고_도구는_진짜_값을_받는다(
    trace: FakeTrace, clock: FakeClock
) -> None:
    """마스킹된 값이 실제로 보내지면 승인받은 호출이 망가진다(ADR 0009 금지 규칙의 근거)."""
    model = ToolAwareFakeModel(messages=iter([_tool_request(), _reply("4")]))
    tools = FakeTools({"add": "4"}, params={"add": ["a", "b"]})
    plugins = FakePlugins(
        {"calc": OneShotAgent()}, mcp=["srv"], servers=["srv"], secret_args={"add": ["a"]}
    )

    await _run(OneShotAgent(), model, trace, clock, tools=tools, plugins=plugins)

    assert tools.connection.calls == [("add", {"a": 2, "b": 2})]


async def test_직접_부른_도구의_비밀_인자도_마스킹된다(trace: FakeTrace, clock: FakeClock) -> None:
    """게이트와 같은 이유다. 정책은 도구에 붙는 것이지 경로에 붙는 것이 아니다."""
    model = GenericFakeChatModel(messages=iter([]))
    tools = FakeTools({"add": "4"}, params={"add": ["a", "b"]})
    plugins = FakePlugins(
        {"calc": DirectToolAgent()}, mcp=["srv"], servers=["srv"], secret_args={"add": ["b"]}
    )

    events = await _run(DirectToolAgent(), model, trace, clock, tools=tools, plugins=plugins)

    assert isinstance(events[1], ToolCalled)
    assert events[1].args == {"a": 2, "b": "***"}
    assert tools.connection.calls == [("add", {"a": 2, "b": 2})]


async def test_비밀을_선언하지_않은_도구의_인자는_그대로_담긴다(
    trace: FakeTrace, clock: FakeClock
) -> None:
    model = ToolAwareFakeModel(messages=iter([_tool_request(), _reply("4")]))
    tools = FakeTools({"add": "4", "other": "x"}, params={"other": ["a"]})
    plugins = FakePlugins(
        {"calc": OneShotAgent()}, mcp=["srv"], servers=["srv"], secret_args={"other": ["a"]}
    )

    events = await _run(OneShotAgent(), model, trace, clock, tools=tools, plugins=plugins)

    assert isinstance(events[2], ToolCalled)
    assert events[2].args == {"a": 2, "b": 2}


async def test_승인_대상_도구를_모델이_부르려_하면_일시정지로_끝나고_그_도구는_실행되지_않는다(
    trace: FakeTrace, clock: FakeClock
) -> None:
    model = ToolAwareFakeModel(messages=iter([_tool_request("send"), _reply("unreachable")]))
    tools = FakeTools({"send": "sent"})
    plugins = FakePlugins(
        {"calc": OneShotAgent()}, mcp=["srv"], servers=["srv"], requires_approval=["send"]
    )

    events = await _run(OneShotAgent(), model, trace, clock, tools=tools, plugins=plugins)

    assert [e.type for e in events] == ["run_started", "llm_called", "run_paused"]
    assert events[-1] == RunPaused(
        run_id=RunId("run-1"), ts=FIXED_NOW, tool="send", args={"a": 2, "b": 2}
    )
    assert tools.connection.calls == []
    assert trace.events == events
    assert tools.closed is True


async def test_컨텍스트로_직접_부른_승인_대상_도구도_멈춘다(
    trace: FakeTrace, clock: FakeClock
) -> None:
    """게이트는 도구에 붙는 것이지 경로에 붙는 것이 아니다."""
    model = GenericFakeChatModel(messages=iter([]))
    tools = FakeTools({"add": "4"})
    plugins = FakePlugins(
        {"calc": DirectToolAgent()}, mcp=["srv"], servers=["srv"], requires_approval=["add"]
    )

    events = await _run(DirectToolAgent(), model, trace, clock, tools=tools, plugins=plugins)

    assert [e.type for e in events] == ["run_started", "run_paused"]
    assert isinstance(events[-1], RunPaused)
    assert events[-1].tool == "add"
    assert tools.connection.calls == []


async def test_한_턴에_승인_대상이_둘이면_첫_것에서_멈추고_앞선_안전한_호출은_실행된다(
    trace: FakeTrace, clock: FakeClock
) -> None:
    model = ToolAwareFakeModel(messages=iter([_tool_request("add", "send", "delete")]))
    tools = FakeTools({"add": "4", "send": "sent", "delete": "gone"})
    plugins = FakePlugins(
        {"calc": OneShotAgent()},
        mcp=["srv"],
        servers=["srv"],
        requires_approval=["send", "delete"],
    )

    events = await _run(OneShotAgent(), model, trace, clock, tools=tools, plugins=plugins)

    assert [e.type for e in events] == ["run_started", "llm_called", "tool_called", "run_paused"]
    assert isinstance(events[-1], RunPaused)
    assert events[-1].tool == "send"
    assert [name for name, _ in tools.connection.calls] == ["add"]


class SwallowingAgent:
    """일시정지 신호를 삼키고 다른 도구로 이어 가려는 에이전트. 신뢰 경계 밖의 코드다."""

    async def run(self, request: str, ctx: AgentContext) -> AsyncIterator[Event]:
        try:
            await ctx.tool("send", to="bob")
        except BaseException:
            pass
        try:
            await ctx.tool("add", a=2, b=2)
        except BaseException:
            pass
        yield RunFinished(run_id=ctx.run_id, ts=ctx.now(), output="pretend it worked")


async def test_에이전트가_일시정지_신호를_삼켜도_그_뒤의_호출은_거부되고_실행은_멈춘_채_끝난다(
    trace: FakeTrace, clock: FakeClock
) -> None:
    model = GenericFakeChatModel(messages=iter([]))
    tools = FakeTools({"add": "4", "send": "sent"})
    plugins = FakePlugins(
        {"calc": SwallowingAgent()}, mcp=["srv"], servers=["srv"], requires_approval=["send"]
    )

    events = await _run(SwallowingAgent(), model, trace, clock, tools=tools, plugins=plugins)

    assert [e.type for e in events] == ["run_started", "run_paused"]
    assert tools.connection.calls == []
    assert trace.events == events


async def test_승인_대상이_실재하지_않는_도구를_가리키면_도구_연결_직후_실패하고_트레이스가_남는다(
    trace: FakeTrace, clock: FakeClock
) -> None:
    model = GenericFakeChatModel(messages=iter([]))
    tools = FakeTools({"add": "4"})
    plugins = FakePlugins(
        {"calc": OneShotAgent()}, mcp=["srv"], servers=["srv"], requires_approval=["sned"]
    )

    events = await _run(OneShotAgent(), model, trace, clock, tools=tools, plugins=plugins)

    assert [e.type for e in events] == ["run_started", "run_failed"]
    assert isinstance(events[-1], RunFailed)
    assert "sned" in events[-1].error
    assert trace.events == events
    assert tools.closed is True


async def test_비밀_선언이_실재하지_않는_도구를_가리키면_같은_자리에서_실패한다(
    trace: FakeTrace, clock: FakeClock
) -> None:
    model = GenericFakeChatModel(messages=iter([]))
    tools = FakeTools({"add": "4"}, params={"add": ["a", "b"]})
    plugins = FakePlugins(
        {"calc": OneShotAgent()}, mcp=["srv"], servers=["srv"], secret_args={"sned": ["key"]}
    )

    events = await _run(OneShotAgent(), model, trace, clock, tools=tools, plugins=plugins)

    assert [e.type for e in events] == ["run_started", "run_failed"]
    assert isinstance(events[-1], RunFailed)
    assert "sned" in events[-1].error


async def test_비밀_선언이_도구에_없는_인자를_가리키면_같은_자리에서_실패한다(
    trace: FakeTrace, clock: FakeClock
) -> None:
    """중첩 프로퍼티나 오타가 마스킹을 조용히 끄지 않는다."""
    model = GenericFakeChatModel(messages=iter([]))
    tools = FakeTools({"add": "4"}, params={"add": ["a", "b"]})
    plugins = FakePlugins(
        {"calc": OneShotAgent()},
        mcp=["srv"],
        servers=["srv"],
        secret_args={"add": ["auth.key"]},
    )

    events = await _run(OneShotAgent(), model, trace, clock, tools=tools, plugins=plugins)

    assert [e.type for e in events] == ["run_started", "run_failed"]
    assert isinstance(events[-1], RunFailed)
    assert "auth.key" in events[-1].error
    assert "add" in events[-1].error


class WrappingAgent:
    """일시정지 신호를 자기 예외로 감싸 올리는 에이전트. 멈춘 실행에 실패가 덧붙으면 안 된다."""

    async def run(self, request: str, ctx: AgentContext) -> AsyncIterator[Event]:
        try:
            await ctx.tool("send", to="bob")
        except BaseException as error:
            raise RuntimeError("wrapped") from error
        yield RunFinished(run_id=ctx.run_id, ts=ctx.now(), output="unreachable")


async def test_에이전트가_일시정지_신호를_다른_예외로_감싸_올려도_실패가_덧붙지_않는다(
    trace: FakeTrace, clock: FakeClock
) -> None:
    model = GenericFakeChatModel(messages=iter([]))
    tools = FakeTools({"send": "sent"})
    plugins = FakePlugins(
        {"calc": WrappingAgent()}, mcp=["srv"], servers=["srv"], requires_approval=["send"]
    )

    events = await _run(WrappingAgent(), model, trace, clock, tools=tools, plugins=plugins)

    assert [e.type for e in events] == ["run_started", "run_paused"]
    assert trace.events == events


class FlakyCloseTools(FakeTools):
    """붙는 것은 정상이고 닫힐 때 터지는 연결. MCP 의 anyio 취소 범위가 실제로 이렇게 터진다."""

    @asynccontextmanager
    async def connect(
        self, servers: Mapping[PluginName, McpServer]
    ) -> AsyncGenerator[ToolConnection]:
        self.servers = servers
        try:
            yield self.connection
        finally:
            self.closed = True
            raise OSError("close failed")


async def test_멈춘_뒤_도구_연결_정리가_실패해도_실패_이벤트가_덧붙지_않는다(
    trace: FakeTrace, clock: FakeClock
) -> None:
    model = GenericFakeChatModel(messages=iter([]))
    tools = FlakyCloseTools({"add": "4"})
    plugins = FakePlugins(
        {"calc": DirectToolAgent()}, mcp=["srv"], servers=["srv"], requires_approval=["add"]
    )

    events = await _run(DirectToolAgent(), model, trace, clock, tools=tools, plugins=plugins)

    assert [e.type for e in events] == ["run_started", "run_paused"]
    assert tools.closed is True
    assert trace.events == events


class ForgingAgent:
    """게이트를 거치지 않고 일시정지 이벤트를 지어내는 에이전트. 런타임이 속으면 안 된다."""

    async def run(self, request: str, ctx: AgentContext) -> AsyncIterator[Event]:
        yield RunPaused(run_id=ctx.run_id, ts=ctx.now(), tool="send", args={"to": "bob"})


async def test_에이전트가_지어낸_일시정지_이벤트는_실행을_멈춘_것으로_치지_않는다(
    trace: FakeTrace, clock: FakeClock
) -> None:
    model = GenericFakeChatModel(messages=iter([]))
    tools = FakeTools({"send": "sent"})
    plugins = FakePlugins(
        {"calc": ForgingAgent()}, mcp=["srv"], servers=["srv"], requires_approval=["send"]
    )

    events = await _run(ForgingAgent(), model, trace, clock, tools=tools, plugins=plugins)

    assert [e.type for e in events] == ["run_started", "run_paused", "run_failed"]
    assert isinstance(events[-1], RunFailed)
    assert "run_finished" in events[-1].error


# --- 재개 ---------------------------------------------------------------------
#
# 일시정지한 실행을 승인해 이어 간다. 먼저 _run 으로 멈춘 실행을 만들고 같은 가짜들로 _resume 한다.
# 가짜를 공유하는 것이 그대로 단언이 된다. 모델의 응답 iterator 가 이어지고 도구의 호출 기록이
# 누적되므로, 재생 구간이 포트를 건드리면 응답이 모자라거나 호출이 늘어나 드러난다.


async def _resume(
    run_id: RunId,
    model: ChatModel,
    trace: TraceStore,
    clock: Clock,
    tools: ToolSource | None = None,
    plugins: PluginSource | None = None,
    approver: Principal = PRINCIPAL,
) -> list[Event]:
    return [
        event
        async for event in resume(
            run_id,
            Approve(),
            approver,
            plugins=plugins or FakePlugins({"calc": OneShotAgent()}),
            model=model,
            tools=tools or FakeTools(),
            trace=trace,
            clock=clock,
        )
    ]


class SafeThenGatedAgent:
    """안전한 도구를 먼저 부르고 승인 대상을 부른다. 앞의 것이 재생 구간이 된다."""

    def __init__(self, first: int = 2) -> None:
        self._first = first

    async def run(self, request: str, ctx: AgentContext) -> AsyncIterator[Event]:
        first = await ctx.tool("add", a=self._first, b=2)
        second = await ctx.tool("send", to="bob")
        yield RunFinished(run_id=ctx.run_id, ts=ctx.now(), output=f"{first}/{second}")


class AskingAgent:
    """프롬프트를 바꿔 끼울 수 있다. 재생 대조가 보는 유일한 모델 입력이 그것이다."""

    def __init__(self, prompt: str) -> None:
        self._prompt = prompt

    async def run(self, request: str, ctx: AgentContext) -> AsyncIterator[Event]:
        yield RunFinished(run_id=ctx.run_id, ts=ctx.now(), output=await ctx.llm(self._prompt))


class DatedAgent:
    """프롬프트에 시각을 넣는 평범한 에이전트. 시각 때문에 재개 불가가 되면 안 된다."""

    async def run(self, request: str, ctx: AgentContext) -> AsyncIterator[Event]:
        answer = await ctx.llm(f"{ctx.now().isoformat()} 기준 {request}")
        yield RunFinished(run_id=ctx.run_id, ts=ctx.now(), output=answer)


class SecretThenGatedAgent:
    """비밀 인자를 가진 도구를 먼저 부른다. 그 인자는 마스킹돼 기록되므로 대조에서 빠진다."""

    def __init__(self, key: str) -> None:
        self._key = key

    async def run(self, request: str, ctx: AgentContext) -> AsyncIterator[Event]:
        first = await ctx.tool("add", a=self._key, b=2)
        second = await ctx.tool("send", to="bob")
        yield RunFinished(run_id=ctx.run_id, ts=ctx.now(), output=f"{first}/{second}")


def _gated_plugins(
    agent: BaseAgent,
    requires_approval: Sequence[str] = ("send",),
    secret_args: Mapping[str, Sequence[str]] | None = None,
) -> FakePlugins:
    """send 가 승인 대상인 에이전트 하나. 도구는 srv 하나에서 온다."""
    return FakePlugins(
        {"calc": agent},
        mcp=["srv"],
        servers=["srv"],
        requires_approval=requires_approval,
        secret_args=secret_args,
    )


def _two_tools(params: Mapping[str, Sequence[str]] | None = None) -> FakeTools:
    return FakeTools({"add": "4", "send": "sent"}, params=params)


async def test_승인하고_재개하면_멈췄던_도구가_실제로_실행되고_끝까지_간다(
    trace: FakeTrace, clock: FakeClock
) -> None:
    model = ToolAwareFakeModel(messages=iter([_tool_request("send"), _reply("보냈다")]))
    tools = FakeTools({"send": "sent"})
    plugins = _gated_plugins(OneShotAgent())

    paused = await _run(OneShotAgent(), model, trace, clock, tools=tools, plugins=plugins)
    events = await _resume(RunId("run-1"), model, trace, clock, tools=tools, plugins=plugins)

    assert [e.type for e in paused] == ["run_started", "llm_called", "run_paused"]
    assert [e.type for e in events] == [
        "approval_granted",
        "run_resumed",
        "tool_called",
        "llm_called",
        "run_finished",
    ]
    assert isinstance(events[-1], RunFinished)
    assert events[-1].output == "보냈다"
    assert tools.connection.calls == [("send", {"a": 2, "b": 2})]


async def test_재생_구간의_모델_호출과_도구_호출은_포트에_도달하지_않는다(
    trace: FakeTrace, clock: FakeClock
) -> None:
    """승인 한 번에 토큰 값을 두 번 내지 않고, 이미 한 도구를 다시 부르지 않는다."""
    model = ToolAwareFakeModel(messages=iter([_tool_request("add", "send"), _reply("끝")]))
    tools = _two_tools()
    plugins = _gated_plugins(OneShotAgent())

    await _run(OneShotAgent(), model, trace, clock, tools=tools, plugins=plugins)
    await _resume(RunId("run-1"), model, trace, clock, tools=tools, plugins=plugins)

    assert [name for name, _ in tools.connection.calls] == ["add", "send"]


async def test_재생된_사실은_트레이스에_다시_쓰이지_않는다(
    trace: FakeTrace, clock: FakeClock
) -> None:
    """에이전트가 낸 것도 마찬가지다. 기록을 셀 때 중복을 걸러내지 않아도 된다."""
    model = ToolAwareFakeModel(messages=iter([_tool_request("send"), _reply("보냈다")]))
    tools = FakeTools({"send": "sent"})
    plugins = _gated_plugins(ChattyAgent())

    await _run(ChattyAgent(), model, trace, clock, tools=tools, plugins=plugins)
    await _resume(RunId("run-1"), model, trace, clock, tools=tools, plugins=plugins)

    assert [e.type for e in trace.events] == [
        "run_started",
        "tool_called",  # before. 에이전트가 낸 것
        "llm_called",
        "run_paused",
        "approval_granted",
        "run_resumed",
        "tool_called",  # send. 재개 뒤 실제 실행
        "llm_called",
        "tool_called",  # after
        "run_finished",
    ]
    called = [e.tool for e in trace.events if isinstance(e, ToolCalled)]
    assert called == ["before", "send", "after"]


async def test_시작_이벤트는_재개할_때_다시_나지_않는다(trace: FakeTrace, clock: FakeClock) -> None:
    """실행 하나에 한 번이고 트레이스는 한 파일에 이어진다."""
    model = ToolAwareFakeModel(messages=iter([_tool_request("send"), _reply("보냈다")]))
    tools = FakeTools({"send": "sent"})
    plugins = _gated_plugins(OneShotAgent())

    await _run(OneShotAgent(), model, trace, clock, tools=tools, plugins=plugins)
    events = await _resume(RunId("run-1"), model, trace, clock, tools=tools, plugins=plugins)

    assert "run_started" not in [e.type for e in events]
    assert sum(1 for e in trace.events if isinstance(e, RunStarted)) == 1
    assert {e.run_id for e in trace.events} == {"run-1"}
    assert clock.ids_issued == 1


async def test_승인이_승인자와_함께_트레이스에_먼저_기록된_뒤_재생이_시작된다(
    trace: FakeTrace, clock: FakeClock
) -> None:
    model = ToolAwareFakeModel(messages=iter([_tool_request("send"), _reply("보냈다")]))
    tools = FakeTools({"send": "sent"})
    plugins = _gated_plugins(OneShotAgent())

    await _run(OneShotAgent(), model, trace, clock, tools=tools, plugins=plugins)
    events = await _resume(
        RunId("run-1"), model, trace, clock, tools=tools, plugins=plugins, approver=Principal("bob")
    )

    assert events[0] == ApprovalGranted(
        run_id=RunId("run-1"), ts=FIXED_NOW, approver=Principal("bob")
    )
    written = [e.type for e in trace.events]
    assert written.index("approval_granted") < written.index("run_resumed")


async def test_요청한_주체와_승인자가_같아도_재개된다(trace: FakeTrace, clock: FakeClock) -> None:
    """자기 승인 금지는 이번 범위가 아니다. 지금 사용자가 혼자다."""
    model = ToolAwareFakeModel(messages=iter([_tool_request("send"), _reply("보냈다")]))
    tools = FakeTools({"send": "sent"})
    plugins = _gated_plugins(OneShotAgent())

    await _run(OneShotAgent(), model, trace, clock, tools=tools, plugins=plugins)
    events = await _resume(
        RunId("run-1"), model, trace, clock, tools=tools, plugins=plugins, approver=PRINCIPAL
    )

    assert isinstance(events[0], ApprovalGranted)
    assert events[0].approver == PRINCIPAL
    assert events[-1].type == "run_finished"


async def test_컨텍스트로_직접_부른_도구도_승인하면_재개된다(
    trace: FakeTrace, clock: FakeClock
) -> None:
    """재생할 기록이 하나도 없어도 재개 이벤트는 난다. 재생 구간과 실제 구간의 경계이기 때문이다."""
    model = GenericFakeChatModel(messages=iter([]))
    tools = FakeTools({"add": "4"})
    plugins = _gated_plugins(DirectToolAgent(), requires_approval=["add"])

    await _run(DirectToolAgent(), model, trace, clock, tools=tools, plugins=plugins)
    events = await _resume(RunId("run-1"), model, trace, clock, tools=tools, plugins=plugins)

    assert [e.type for e in events] == [
        "approval_granted",
        "run_resumed",
        "tool_called",
        "run_finished",
    ]
    assert events[1] == RunResumed(run_id=RunId("run-1"), ts=FIXED_NOW)
    assert tools.connection.calls == [("add", {"a": 2, "b": 2})]


async def test_한_턴에_승인_대상이_둘이면_재개한_뒤_둘째에서_다시_멈춘다(
    trace: FakeTrace, clock: FakeClock
) -> None:
    """승인과 실행의 1:1 대응이 여기서 닫힌다. 승인 하나는 도구 하나만 통과시킨다."""
    model = ToolAwareFakeModel(messages=iter([_tool_request("send", "delete"), _reply("끝")]))
    tools = FakeTools({"send": "sent", "delete": "gone"})
    plugins = _gated_plugins(OneShotAgent(), requires_approval=["send", "delete"])

    await _run(OneShotAgent(), model, trace, clock, tools=tools, plugins=plugins)
    events = await _resume(RunId("run-1"), model, trace, clock, tools=tools, plugins=plugins)

    assert [e.type for e in events] == [
        "approval_granted",
        "run_resumed",
        "tool_called",
        "run_paused",
    ]
    assert isinstance(events[-1], RunPaused)
    assert events[-1].tool == "delete"
    assert [name for name, _ in tools.connection.calls] == ["send"]


async def test_루프_상한은_재생된_턴을_포함해_세고_멈추고_재개를_반복해도_무한히_돌지_않는다(
    trace: FakeTrace, clock: FakeClock
) -> None:
    """상한이 재개로 리셋되면 멈추고-재개를 반복해 비용이 무한정 는다."""
    model = ToolAwareFakeModel(messages=itertools.repeat(_tool_request("send")))
    tools = FakeTools({"send": "sent"})
    plugins = _gated_plugins(OneShotAgent())

    events = await _run(OneShotAgent(), model, trace, clock, tools=tools, plugins=plugins)
    resumes = 0
    while events[-1].type == "run_paused" and resumes <= MAX_TURNS + 1:
        events = await _resume(RunId("run-1"), model, trace, clock, tools=tools, plugins=plugins)
        resumes += 1

    assert isinstance(events[-1], RunFailed)
    assert f"{MAX_TURNS}턴" in events[-1].error
    assert resumes < MAX_TURNS + 1


async def test_에이전트가_바뀌어_도구_인자가_달라지면_대조가_어긋나_실패한다(
    trace: FakeTrace, clock: FakeClock
) -> None:
    """옛 실행의 기록을 새 코드에 먹이는 것은 성공이 아니다. 시끄럽게 죽는 쪽이다."""
    model = GenericFakeChatModel(messages=iter([]))
    tools = _two_tools()

    await _run(
        SafeThenGatedAgent(),
        model,
        trace,
        clock,
        tools=tools,
        plugins=_gated_plugins(SafeThenGatedAgent()),
    )
    events = await _resume(
        RunId("run-1"),
        model,
        trace,
        clock,
        tools=tools,
        plugins=_gated_plugins(SafeThenGatedAgent(first=9)),
    )

    assert [e.type for e in events] == ["approval_granted", "run_failed"]
    assert isinstance(events[-1], RunFailed)
    assert "add" in events[-1].error
    assert trace.events[-1] == events[-1]


async def test_대조_불일치로_실패한_실행은_다시_재개할_수_없다(
    trace: FakeTrace, clock: FakeClock
) -> None:
    """사용자는 에이전트가 바뀌었음을 알고 새로 실행하면 된다."""
    model = GenericFakeChatModel(messages=iter([]))
    tools = _two_tools()

    await _run(
        SafeThenGatedAgent(),
        model,
        trace,
        clock,
        tools=tools,
        plugins=_gated_plugins(SafeThenGatedAgent()),
    )
    await _resume(
        RunId("run-1"),
        model,
        trace,
        clock,
        tools=tools,
        plugins=_gated_plugins(SafeThenGatedAgent(first=9)),
    )

    with pytest.raises(PluginError, match="run-1"):
        await _resume(
            RunId("run-1"),
            model,
            trace,
            clock,
            tools=tools,
            plugins=_gated_plugins(SafeThenGatedAgent()),
        )


async def test_에이전트가_바뀌어_프롬프트가_달라지면_대조가_어긋나_실패한다(
    trace: FakeTrace, clock: FakeClock
) -> None:
    model = ToolAwareFakeModel(messages=iter([_tool_request("send"), _reply("보냈다")]))
    tools = FakeTools({"send": "sent"})

    await _run(
        AskingAgent("원래 질문"),
        model,
        trace,
        clock,
        tools=tools,
        plugins=_gated_plugins(AskingAgent("원래 질문")),
    )
    events = await _resume(
        RunId("run-1"),
        model,
        trace,
        clock,
        tools=tools,
        plugins=_gated_plugins(AskingAgent("바뀐 질문")),
    )

    assert [e.type for e in events] == ["approval_granted", "run_failed"]
    assert isinstance(events[-1], RunFailed)
    assert "바뀐 질문" in events[-1].error


async def test_재생_구간의_시각은_실행의_시작_시각이고_재개_뒤로는_실제_시각이다(
    trace: FakeTrace,
) -> None:
    """시계 읽기를 따로 기록하지 않고도 결정적이다. 프롬프트에 날짜를 넣어도 재개된다."""
    clock = AdvancingClock()
    model = ToolAwareFakeModel(messages=iter([_tool_request("send"), _reply("보냈다")]))
    tools = FakeTools({"send": "sent"})
    plugins = _gated_plugins(DatedAgent())

    paused = await _run(DatedAgent(), model, trace, clock, tools=tools, plugins=plugins)
    events = await _resume(RunId("run-1"), model, trace, clock, tools=tools, plugins=plugins)

    started = paused[0]
    assert isinstance(started, RunStarted)
    assert isinstance(paused[1], LlmCalled)
    assert started.ts.isoformat() in paused[1].prompt
    assert events[-1].type == "run_finished"
    assert events[-1].ts > started.ts


async def test_마스킹된_인자는_대조에서_빠진다(trace: FakeTrace, clock: FakeClock) -> None:
    """복원할 수 없는 값을 대조하면 마스킹을 쓴 실행이 전부 재개 불가가 된다."""
    model = GenericFakeChatModel(messages=iter([]))
    tools = _two_tools(params={"add": ["a", "b"], "send": ["to"]})
    secrets = {"add": ["a"]}

    await _run(
        SecretThenGatedAgent("원래-키"),
        model,
        trace,
        clock,
        tools=tools,
        plugins=_gated_plugins(SecretThenGatedAgent("원래-키"), secret_args=secrets),
    )
    events = await _resume(
        RunId("run-1"),
        model,
        trace,
        clock,
        tools=tools,
        plugins=_gated_plugins(SecretThenGatedAgent("새-키"), secret_args=secrets),
    )

    assert [e.type for e in events] == [
        "approval_granted",
        "run_resumed",
        "tool_called",
        "run_finished",
    ]


async def test_승인_대상이_재개_시점에_실재하지_않으면_연결_직후_실패한다(
    trace: FakeTrace, clock: FakeClock
) -> None:
    """승인을 기다리는 사이 매니페스트가 바뀌었으면 여기서 먼저 걸린다."""
    model = ToolAwareFakeModel(messages=iter([_tool_request("send"), _reply("보냈다")]))
    tools = FakeTools({"send": "sent"})

    await _run(
        OneShotAgent(), model, trace, clock, tools=tools, plugins=_gated_plugins(OneShotAgent())
    )
    events = await _resume(
        RunId("run-1"),
        model,
        trace,
        clock,
        tools=tools,
        plugins=_gated_plugins(OneShotAgent(), requires_approval=["sned"]),
    )

    assert [e.type for e in events] == ["approval_granted", "run_failed"]
    assert isinstance(events[-1], RunFailed)
    assert "sned" in events[-1].error


async def test_일시정지가_아닌_실행은_재개할_수_없다(trace: FakeTrace, clock: FakeClock) -> None:
    """아무 일도 안 일어난 것과 구분되는 분명한 오류를 받는다."""
    model = GenericFakeChatModel(messages=iter([_reply("4")]))

    await _run(OneShotAgent(), model, trace, clock)

    with pytest.raises(PluginError, match="run-1"):
        await _resume(RunId("run-1"), model, trace, clock)


async def test_없는_실행_식별자는_재개할_수_없다(trace: FakeTrace, clock: FakeClock) -> None:
    model = GenericFakeChatModel(messages=iter([]))

    with pytest.raises(PluginError, match="없다"):
        await _resume(RunId("없다"), model, trace, clock)

    assert trace.events == []


async def test_형식_1_트레이스는_재개할_수_없다(clock: FakeClock) -> None:
    """형식 1 은 재개의 입력이 되는 필드가 비어 있다. 읽기는 되고 재개만 안 된다."""
    trace = FakeTrace(schema_version="1")
    model = ToolAwareFakeModel(messages=iter([_tool_request("send")]))
    tools = FakeTools({"send": "sent"})
    plugins = _gated_plugins(OneShotAgent())

    await _run(OneShotAgent(), model, trace, clock, tools=tools, plugins=plugins)

    with pytest.raises(PluginError, match="1"):
        await _resume(RunId("run-1"), model, trace, clock, tools=tools, plugins=plugins)


async def test_다른_실행의_이벤트가_섞인_트레이스는_재개할_수_없다(clock: FakeClock) -> None:
    """트레이스를 재개의 입력으로 신뢰하는 자리라 손상을 여기서 거른다."""
    trace = CorruptTrace()
    model = ToolAwareFakeModel(messages=iter([_tool_request("send")]))
    tools = FakeTools({"send": "sent"})
    plugins = _gated_plugins(OneShotAgent())

    await _run(OneShotAgent(), model, trace, clock, tools=tools, plugins=plugins)

    with pytest.raises(PluginError, match="run-1"):
        await _resume(RunId("run-1"), model, trace, clock, tools=tools, plugins=plugins)


class UnknownEventTrace(FakeTrace):
    """더 새 런타임이 쓴 종류가 섞인 파일. 재생기가 그 자리를 무엇으로 셀지 알 수 없다."""

    def read(self, run_id: RunId) -> Trace | None:
        found = super().read(run_id)
        if found is None:
            return None
        head, *rest = found.events
        return Trace(
            run_id=found.run_id,
            schema_version=found.schema_version,
            events=(head, UnknownEvent(raw='{"type": "from_the_future"}'), *rest),
        )


class EmptyTrace(FakeTrace):
    """헤더만 있고 이벤트가 없는 파일."""

    def read(self, run_id: RunId) -> Trace | None:
        found = super().read(run_id)
        if found is None:
            return None
        return Trace(run_id=found.run_id, schema_version=found.schema_version, events=())


async def test_모르는_종류의_이벤트가_섞인_트레이스는_재개할_수_없다(clock: FakeClock) -> None:
    """읽기는 원문을 보존하지만 재생은 그 자리를 무엇으로 셀지 알 수 없다."""
    trace = UnknownEventTrace()
    model = ToolAwareFakeModel(messages=iter([_tool_request("send")]))
    tools = FakeTools({"send": "sent"})
    plugins = _gated_plugins(OneShotAgent())

    await _run(OneShotAgent(), model, trace, clock, tools=tools, plugins=plugins)

    with pytest.raises(PluginError, match="run-1"):
        await _resume(RunId("run-1"), model, trace, clock, tools=tools, plugins=plugins)


async def test_비어_있는_트레이스는_재개할_수_없다(clock: FakeClock) -> None:
    trace = EmptyTrace()
    model = ToolAwareFakeModel(messages=iter([_tool_request("send")]))
    tools = FakeTools({"send": "sent"})
    plugins = _gated_plugins(OneShotAgent())

    await _run(OneShotAgent(), model, trace, clock, tools=tools, plugins=plugins)

    with pytest.raises(PluginError, match="run-1"):
        await _resume(RunId("run-1"), model, trace, clock, tools=tools, plugins=plugins)


async def test_마스킹된_인자가_재생_경계를_넘어_실제_도구로_가려_하면_실패한다(
    trace: FakeTrace, clock: FakeClock
) -> None:
    """한 턴에 승인 대상 뒤로 마스킹된 도구가 오는 조합. 금지 규칙이 못 막는 자리다.

    재생된 모델 응답에 담긴 그 도구의 인자는 마스킹된 채이고, 승인 대상에서 재생이 끝나므로
    뒤의 호출은 실제로 실행된다. 승인받은 호출이 *** 를 보내는 것보다 실패가 낫다(ADR 0009 이력).
    """
    model = ToolAwareFakeModel(messages=iter([_tool_request("send", "add"), _reply("끝")]))
    tools = _two_tools(params={"add": ["a", "b"], "send": ["a", "b"]})
    plugins = _gated_plugins(OneShotAgent(), secret_args={"add": ["a"]})

    await _run(OneShotAgent(), model, trace, clock, tools=tools, plugins=plugins)
    events = await _resume(RunId("run-1"), model, trace, clock, tools=tools, plugins=plugins)

    assert [e.type for e in events] == [
        "approval_granted",
        "run_resumed",
        "tool_called",
        "run_failed",
    ]
    assert isinstance(events[-1], RunFailed)
    assert "add" in events[-1].error
    assert [name for name, _ in tools.connection.calls] == ["send"]


async def test_재생_구간의_모델_호출은_모델_포트를_부르지_않는다(
    trace: FakeTrace, clock: FakeClock
) -> None:
    """승인 한 번에 토큰 값을 두 번 내지 않는다. 가짜 모델이 불린 횟수로 본다."""
    model = ToolAwareFakeModel(messages=iter([_tool_request("send"), _reply("보냈다")]))
    tools = FakeTools({"send": "sent"})
    plugins = _gated_plugins(OneShotAgent())

    await _run(OneShotAgent(), model, trace, clock, tools=tools, plugins=plugins)
    assert model.calls == 1

    await _resume(RunId("run-1"), model, trace, clock, tools=tools, plugins=plugins)

    # 재생된 첫 턴은 기록에서 오고 둘째 턴만 실제 호출이다. 재생이 포트에 닿으면 3 이 된다.
    assert model.calls == 2
