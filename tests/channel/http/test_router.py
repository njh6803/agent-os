"""HTTP 채널. `create_app()` 이 만든 앱에 실행을 일으켜 그 이벤트 스트림과 트레이스를 본다.

주 이음매는 관리 API 와 같다 — 가짜 포트를 주입하고 httpx `ASGITransport` 로 민다. 다른 점은 둘이다.
채널의 실행은 앱의 수명이 소유하므로 **테스트가 앱의 수명을 연다**(`ASGITransport` 는 lifespan 을
보내지 않는다). 그 수명은 anyio 태스크 그룹이라 픽스처가 아니라 테스트 본문의 `async with` 로
연다 — 픽스처의 setup 과 teardown 은 다른 태스크다(`.claude/rules/tests.md`).

둘째 구동자는 같은 앱을 `app(scope, receive, send)` 로 직접 부른다. 스트림의 수명 넷(조각별 전달,
끊겨도 끝까지, 느린 수신자, 서버가 멈추면 결말 없음)에만 쓴다(`.claude/rules/http.md`). 가짜 모델이
테스트가 풀어 줄 때까지 기다려서 실행의 진행을 테스트가 쥔다.

가짜 포트는 상속하지 않고 시그니처로 만족하며 `_app` 의 인자 타입이 포트 적합성을 검증한다.
네트워크도 디스크도 타지 않는다. 가짜 트레이스는 JSONL 어댑터와 같은 직렬화로 줄을 들고 있고
어댑터가 실제로 그렇게 쓴다는 것은 `tests/adapters/test_jsonl.py` 가 잰다.
"""

import asyncio
import io
import json
import time
from collections.abc import AsyncGenerator, AsyncIterator, Callable, Iterator, Mapping, Sequence
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from datetime import UTC, datetime, timedelta

import anyio
import fastapi.routing
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient, Response
from langchain_core.callbacks import AsyncCallbackManagerForLLMRun
from langchain_core.language_models import LanguageModelInput
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.messages.tool import ToolCall as LangchainToolCall
from langchain_core.outputs import ChatResult
from langchain_core.runnables import Runnable
from starlette.types import Message, Scope

from agent_os.core.ports import (
    ChatModel,
    Clock,
    Cursor,
    ManifestRow,
    PluginError,
    PluginSource,
    RunRow,
    RunStatus,
    RunSummary,
    ToolConnection,
    ToolResult,
    ToolSource,
    ToolSpec,
    Trace,
    TraceSchemaVersion,
    TraceStore,
    UnknownEvent,
    run_status,
)
from agent_os.core.run import run
from agent_os.http.errors import INTERNAL_MESSAGE
from agent_os.sdk import (
    RUN_ID_PATTERN,
    AgentContext,
    AgentName,
    BaseAgent,
    Event,
    Json,
    McpServer,
    PluginKind,
    PluginManifest,
    PluginName,
    Principal,
    RunFailed,
    RunFinished,
    RunId,
    RunPaused,
    RunStarted,
    ToolCalled,
    parse_manifest,
)
from agent_os.server import create_app

ADMIN_TOKEN = "adm1n-t0ken-that-only-tests-know"
CHANNEL_TOKEN = "channel-t0ken-that-only-tests-know"
ADMIN = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
CHANNEL = {"Authorization": f"Bearer {CHANNEL_TOKEN}"}
PRINCIPAL = Principal("alice")
T0 = datetime(2026, 9, 26, 12, 0, tzinfo=UTC)

# 실행 한 번이 트레이스에 남기는 결말. 스트림이 이것 가운데 하나를 보낸 뒤 닫힌다.
TERMINAL = frozenset({"run_finished", "run_failed", "run_paused"})

# 받는 쪽을 막아 둔 사이에 실행이 내는 이벤트 수. FastAPI 와 미들웨어 사이의 버퍼보다 훨씬 커서,
# 크기가 제한된 큐에 기다리며 넣는 구현이면 실행이 그 큐 앞에서 멈춘다.
BURST = 100


def _toml_list(names: Sequence[str]) -> str:
    return "[" + ", ".join(f'"{name}"' for name in names) + "]"


def _agent(
    name: str, mcp: Sequence[str] = (), requires_approval: Sequence[str] = ()
) -> PluginManifest:
    return parse_manifest(
        f'schema_version = "1"\nkind = "agent"\nname = "{name}"\nversion = "0.1.0"\n'
        f'entrypoint = "agent:Agent"\nmcp = {_toml_list(mcp)}\n'
        f"requires_approval = {_toml_list(requires_approval)}\n"
    )


def _mcp(name: str, secret_args: Mapping[str, Sequence[str]] | None = None) -> PluginManifest:
    table = "".join(f"{tool} = {_toml_list(args)}\n" for tool, args in (secret_args or {}).items())
    return parse_manifest(
        f'schema_version = "1"\nkind = "mcp"\nname = "{name}"\nversion = "0.1.0"\n'
        '[server]\ncommand = "fake-server"\n'
        + (f"\n[server.secret_args]\n{table}" if table else "")
    )


class EchoAgent:
    """모델도 도구도 쓰지 않는다. 요청을 되울리고 끝낸다."""

    async def run(self, request: str, ctx: AgentContext) -> AsyncIterator[Event]:
        yield RunFinished(run_id=ctx.run_id, ts=ctx.now(), output=f"echo:{request}")


class AskingAgent:
    """모델에게 한 번 묻고 그 답으로 끝낸다. 모델이 조용한 동안이 곧 실행이 조용한 동안이다."""

    async def run(self, request: str, ctx: AgentContext) -> AsyncIterator[Event]:
        yield RunFinished(run_id=ctx.run_id, ts=ctx.now(), output=await ctx.llm(request))


class ChattyAgent:
    """모델의 답을 받은 뒤 이벤트를 한꺼번에 많이 낸다. 느린 수신자 앞에서 쌓일 것을 만든다."""

    async def run(self, request: str, ctx: AgentContext) -> AsyncIterator[Event]:
        answer = await ctx.llm(request)
        for index in range(BURST):
            yield ToolCalled(run_id=ctx.run_id, ts=ctx.now(), tool=f"note-{index}", ok=True)
        yield RunFinished(run_id=ctx.run_id, ts=ctx.now(), output=answer)


class ToolAgent:
    """모델을 거치지 않고 add 를 직접 부른다. 매니페스트가 그것을 승인 대상으로 두면 멈춘다."""

    async def run(self, request: str, ctx: AgentContext) -> AsyncIterator[Event]:
        total = await ctx.tool("add", a=2, b=3)
        yield RunFinished(run_id=ctx.run_id, ts=ctx.now(), output=total)


# 등록된 것 전부. 이름이 곧 테스트가 부르는 에이전트다. 모델이 도구를 고르는 둘은 AskingAgent 다 —
# `gated-asking` 은 add 에서, `careful` 은 login 에서 멈춘다.
ECHO = _agent("echo")
ASKING = _agent("asking")
CHATTY = _agent("chatty")
ADDING = _agent("adding", mcp=["calc-server"])
GATED = _agent("gated", mcp=["calc-server"], requires_approval=["add"])
GATED_ASKING = _agent("gated-asking", mcp=["calc-server"], requires_approval=["add"])
CAREFUL = _agent("careful", mcp=["calc-server"], requires_approval=["login"])
GHOSTLY = _agent("ghostly", mcp=["ghost"])
LEAKY = _agent("leaky", mcp=["secret-server"], requires_approval=["login"])
UNLOADABLE = _agent("unloadable")
CALC_SERVER = _mcp("calc-server")
SECRET_SERVER = _mcp("secret-server", {"login": ["password"]})
AGENTS: Mapping[str, BaseAgent] = {
    "echo": EchoAgent(),
    "asking": AskingAgent(),
    "chatty": ChattyAgent(),
    "adding": ToolAgent(),
    "gated": ToolAgent(),
    "gated-asking": AskingAgent(),
    "careful": AskingAgent(),
    "ghostly": EchoAgent(),
    "leaky": EchoAgent(),
}
# 매니페스트로 읽히지 않는 에이전트와 진입점을 불러올 수 없는 에이전트. 문구가 곧 봉투의 message 다.
UNREADABLE_REASON = "매니페스트를 읽을 수 없다: plugins/agents/broken/plugin.toml"
UNLOADABLE_REASON = (
    "진입점을 불러올 수 없다: plugins/agents/unloadable/agent.py: No module named 'nope'"
)


class FakePlugins:
    """이름별 매니페스트와 에이전트. 부른 횟수를 세어 검증이 포트보다 먼저 끝나는지 본다.

    읽을 수 없는 매니페스트와 불러올 수 없는 진입점은 어댑터처럼 PluginError 로 답한다.
    """

    def __init__(self) -> None:
        manifests = (
            *(ECHO, ASKING, CHATTY, ADDING, GATED, GATED_ASKING, CAREFUL),
            *(GHOSTLY, LEAKY, UNLOADABLE),
        )
        self._manifests = {(m.kind, m.name): m for m in (*manifests, CALC_SERVER, SECRET_SERVER)}
        self.calls = 0

    def read_manifest(self, kind: PluginKind, name: PluginName) -> PluginManifest | None:
        self.calls += 1
        if kind is PluginKind.AGENT and name == "broken":
            raise PluginError(UNREADABLE_REASON)
        return self._manifests.get((kind, name))

    def list_manifests(self, kind: PluginKind) -> Sequence[ManifestRow]:
        self.calls += 1
        return tuple(m for (k, _), m in self._manifests.items() if k is kind)

    def load_agent(self, manifest: PluginManifest) -> BaseAgent:
        self.calls += 1
        if manifest.name == "unloadable":
            raise PluginError(UNLOADABLE_REASON)
        return AGENTS[manifest.name]


class FakeTrace:
    """쓴 이벤트를 JSONL 어댑터와 같은 직렬화의 줄로 들고 읽기와 목록에 답한다.

    관리 API 가 같은 포트를 읽으므로 목록은 어댑터의 규칙대로 실행마다 요약 하나를 만든다. 상태는
    core 의 `run_status()` 로 파생한다. `broken_after` 번째 쓰기부터 실패하는 것은 디스크가 가득
    찬 것과 같다. `legacy` 의 실행은 형식 1 로 읽히고, `damaged` 의 실행은 마지막 줄 앞에 모르는
    종류의 줄이 낀 채로 읽힌다 — 마지막 이벤트는 그대로라 상태만 보면 멀쩡하다. 읽기를 세어 검증이
    포트보다 먼저 끝나는지 본다.

    `disk_seconds` 는 디스크에 한 번 닿는 데 드는 시간이다. 읽은 내용은 읽기를 시작한 순간의 것이고
    쓴 내용은 그 시간이 지난 뒤에 보인다. 읽기나 쓰기가 루프 밖(스레드)으로 나가면 그동안 다른
    요청이 같은 실행을 읽기 시작해 같은 옛 내용을 볼 수 있다. 0 이면 그 창이 스레드의 타이밍에 달려
    경합이 드러나다 말다 한다.
    """

    def __init__(
        self,
        *,
        broken_after: int | None = None,
        legacy: frozenset[RunId] = frozenset(),
        damaged: frozenset[RunId] = frozenset(),
        disk_seconds: float = 0.0,
    ) -> None:
        self.lines: list[str] = []
        self.reads: list[RunId] = []
        self._events: list[Event] = []
        self._broken_after = broken_after
        self._legacy = legacy
        self._damaged = damaged
        self._disk_seconds = disk_seconds

    def write(self, event: Event) -> None:
        if self._broken_after is not None and len(self._events) >= self._broken_after:
            raise OSError("트레이스를 쓸 수 없다: 디스크가 가득 찼다")
        time.sleep(self._disk_seconds)
        self._events.append(event)
        self.lines.append(event.model_dump_json())

    def read(self, run_id: RunId) -> Trace | None:
        self.reads.append(run_id)
        events = self.events_of(run_id)
        time.sleep(self._disk_seconds)
        if not events:
            return None
        stored: tuple[Event | UnknownEvent, ...] = events
        if run_id in self._damaged:
            stored = (*events[:-1], UnknownEvent(raw='{"type": "from_the_future"}'), events[-1])
        version: TraceSchemaVersion = "1" if run_id in self._legacy else "2"
        return Trace(run_id=run_id, schema_version=version, events=stored)

    def list(
        self,
        *,
        status: RunStatus | None = None,
        limit: int | None = None,
        after: Cursor | None = None,
    ) -> Sequence[RunRow]:
        rows: list[RunRow] = []
        for run_id in dict.fromkeys(event.run_id for event in self._events):
            events = self.events_of(run_id)
            started = events[0]
            assert isinstance(started, RunStarted)
            summary = RunSummary(
                run_id=run_id,
                status=run_status(events[-1]),
                schema_version="2",
                started_at=started.ts,
                last_at=events[-1].ts,
                agent=started.agent,
                principal=started.principal,
            )
            if status is None or summary.status == status:
                rows.append(summary)
        return rows

    def events_of(self, run_id: RunId) -> tuple[Event, ...]:
        return tuple(event for event in self._events if event.run_id == run_id)

    def status(self, run_id: RunId) -> RunStatus | None:
        events = self.events_of(run_id)
        return run_status(events[-1]) if events else None


class FakeClock:
    def __init__(self) -> None:
        self._issued = 0
        self._ticks = 0

    def now(self) -> datetime:
        self._ticks += 1
        return T0 + timedelta(seconds=self._ticks)

    def new_run_id(self) -> RunId:
        self._issued += 1
        return RunId(f"run-{self._issued}")


class FakeConnection:
    """붙은 서버가 있으면 add 와 login 을 준다. 실제 어댑터처럼 서버가 없으면 도구도 없다."""

    def __init__(self, servers: Mapping[PluginName, McpServer]) -> None:
        self._servers = servers
        self.calls: list[tuple[str, Mapping[str, Json]]] = []

    def tools(self) -> Sequence[ToolSpec]:
        if not self._servers:
            return []
        schema: Mapping[str, Json] = {"type": "object", "properties": {"a": {}, "b": {}}}
        login: Mapping[str, Json] = {"type": "object", "properties": {"password": {}}}
        return [
            ToolSpec(name="add", description="더한다", input_schema=schema),
            ToolSpec(name="login", description="로그인", input_schema=login),
        ]

    async def call(self, name: str, args: Mapping[str, Json]) -> ToolResult:
        self.calls.append((name, args))
        return ToolResult(ok=True, content="5")


class ScopedTools:
    """MCP 어댑터처럼 연결을 anyio 취소 범위 안에서 연다.

    취소 범위는 들어간 태스크와 다른 태스크에서 닫으면 RuntimeError 를 낸다. 그러면 실행은
    run_finished 가 아니라 run_failed 로 끝난다.
    """

    def __init__(self) -> None:
        self.connections: list[FakeConnection] = []
        self.closed = False

    @property
    def calls(self) -> list[tuple[str, Mapping[str, Json]]]:
        """연 연결들에서 불린 도구 전부."""
        return [call for connection in self.connections for call in connection.calls]

    @asynccontextmanager
    async def connect(
        self, servers: Mapping[PluginName, McpServer]
    ) -> AsyncGenerator[ToolConnection]:
        connection = FakeConnection(servers)
        self.connections.append(connection)
        with anyio.CancelScope():
            yield connection
        self.closed = True


class BrokenTools:
    """MCP 서버 기동 실패."""

    @asynccontextmanager
    async def connect(
        self, servers: Mapping[PluginName, McpServer]
    ) -> AsyncGenerator[ToolConnection]:
        raise ConnectionError("server did not start")
        yield FakeConnection(servers)


class GatedModel(GenericFakeChatModel):
    """테스트가 문을 열 때까지 답하지 않는다. 실행의 진행을 테스트가 쥔다."""

    gate: asyncio.Event

    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: AsyncCallbackManagerForLLMRun | None = None,
        **kwargs: object,
    ) -> ChatResult:
        await self.gate.wait()
        return self._generate(messages, stop, None, **kwargs)


def _gated_model(answer: str = "4") -> GatedModel:
    return GatedModel(messages=iter([AIMessage(content=answer)]), gate=asyncio.Event())


class ToolAwareModel(GenericFakeChatModel):
    """도구를 묶어도 자기 자신이다. core 는 연결이 도구를 주면 `bind_tools` 를 부른다."""

    def bind_tools(
        self,
        tools: Sequence[object],
        *,
        tool_choice: str | None = None,
        **kwargs: object,
    ) -> Runnable[LanguageModelInput, AIMessage]:
        return self


def _tool_request(*calls: tuple[str, Mapping[str, Json]]) -> AIMessage:
    """모델이 한 턴에 낸 도구 호출들."""
    requested = [
        LangchainToolCall(name=name, args=dict(args), id=f"c{index}")
        for index, (name, args) in enumerate(calls, start=1)
    ]
    return AIMessage(content="", tool_calls=requested)


def _tool_calling_model(*replies: AIMessage) -> ToolAwareModel:
    return ToolAwareModel(messages=iter(replies))


def _failing_replies() -> Iterator[AIMessage | str]:
    raise RuntimeError("API down")
    yield AIMessage(content="unreachable")


def _app(
    *,
    plugins: PluginSource | None = None,
    trace: TraceStore | None = None,
    model: ChatModel | None = None,
    tools: ToolSource | None = None,
    clock: Clock | None = None,
    stderr: io.StringIO | None = None,
) -> FastAPI:
    """채널이 붙은 앱 하나. 인자 타입이 가짜의 포트 적합성을 검증하는 자리다."""
    return create_app(
        plugins=plugins or FakePlugins(),
        trace=trace or FakeTrace(),
        model=model or GenericFakeChatModel(messages=iter(())),
        tools=tools or ScopedTools(),
        clock=clock or FakeClock(),
        principal=PRINCIPAL,
        admin_token=ADMIN_TOKEN,
        channel_token=CHANNEL_TOKEN,
        stderr=stderr or io.StringIO(),
    )


def _lifespan(app: FastAPI) -> AbstractAsyncContextManager[object]:
    """앱의 수명. 서버가 뜰 때 열고 멈출 때 닫는 그것이다."""
    return app.router.lifespan_context(app)


@asynccontextmanager
async def _serving(app: FastAPI) -> AsyncGenerator[AsyncClient]:
    """앱의 수명을 연 채로 민다. 테스트 본문에서 `async with` 로 쓴다."""
    transport = ASGITransport(app=app)
    async with (
        _lifespan(app),
        AsyncClient(transport=transport, base_url="http://channel.test") as c,
    ):
        yield c


def _blocks(text: str) -> list[str]:
    """스트림을 빈 줄로 가른 덩어리들. 주석(keepalive)도 한 덩어리다."""
    return [block for block in text.split("\n\n") if block]


def _frames(text: str) -> list[str]:
    """프레임마다의 data 값. 주석은 뺀다. 모양은 `test_프레임은_data_한_줄뿐이다` 가 잰다."""
    return [block.removeprefix("data: ") for block in _blocks(text) if not block.startswith(":")]


def _types(frames: Sequence[str]) -> list[str]:
    return [str(json.loads(frame)["type"]) for frame in frames]


def _start(agent: str, request: str = "2+3?") -> dict[str, str]:
    return {"agent": agent, "request": request}


async def _until(condition: Callable[[], bool], *, within: float = 5.0) -> None:
    """조건이 설 때까지 이벤트 루프를 돌린다. 서지 않으면 시간 초과로 실패한다."""
    async with asyncio.timeout(within):
        while not condition():
            await asyncio.sleep(0.001)


# 스트림 — 실행을 일으켜 그 이벤트를 생기는 대로 받는다


async def test_실행을_일으키면_스트림이_트레이스와_같은_줄을_같은_순서로_싣는다() -> None:
    """프레임 하나가 트레이스 한 줄과 **문자열로** 같다(스토리 4·16). 파싱한 뒤 비교하면 두 직렬화
    (트레이스는 이벤트 하나, 스트림은 유니온)가 어긋나는 날을 놓친다."""
    trace = FakeTrace()
    app = _app(trace=trace)

    async with _serving(app) as client:
        response = await client.post("/runs", json=_start("echo"), headers=CHANNEL)

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    frames = _frames(response.text)
    assert frames == trace.lines
    assert _types(frames) == ["run_started", "run_finished"]
    assert json.loads(frames[-1])["output"] == "echo:2+3?"


async def test_프레임은_data_한_줄뿐이고_event_도_id_도_없다() -> None:
    """종류는 JSON 의 `type` 한 곳에서 읽는다(스토리 5). 계약은 `event`·`id`·`retry` 를 선택으로
    광고하지만 서버는 `data` 만 보낸다(ADR 0014 의 2026-09-24 이력)."""
    async with _serving(_app()) as client:
        response = await client.post("/runs", json=_start("echo"), headers=CHANNEL)

    blocks = [block for block in _blocks(response.text) if not block.startswith(":")]
    assert blocks
    for block in blocks:
        lines = block.split("\n")
        assert len(lines) == 1, block
        assert lines[0].startswith("data: "), block


async def test_실행의_주체는_앱이_받은_것이고_스트림의_첫_이벤트가_실행_식별자를_든다() -> None:
    """주체는 본문에서 받지 않는다(ADR 0015). 첫 이벤트에서 얻은 식별자가 승인과 관리 API 의
    열쇠다(스토리 7)."""
    async with _serving(_app()) as client:
        response = await client.post("/runs", json=_start("echo"), headers=CHANNEL)

    first = json.loads(_frames(response.text)[0])
    assert first["type"] == "run_started"
    assert first["principal"] == PRINCIPAL
    assert first["agent"] == "echo"
    assert first["run_id"] == "run-1"


async def test_승인_대상에서_멈춘_실행의_스트림은_run_paused_로_끝나고_도구와_인자를_든다() -> None:
    """시작한 쪽은 무엇을 승인해 달라는지 스트림의 마지막 이벤트에서 본다(스토리 25)."""
    tools = ScopedTools()
    trace = FakeTrace()
    app = _app(trace=trace, tools=tools)

    async with _serving(app) as client:
        response = await client.post("/runs", json=_start("gated"), headers=CHANNEL)

    frames = _frames(response.text)
    assert frames == trace.lines
    paused = json.loads(frames[-1])
    assert paused["type"] == "run_paused"
    assert paused["tool"] == "add"
    assert paused["args"] == {"a": 2, "b": 3}
    assert tools.calls == []


async def test_응답에_추적_식별자와_버퍼링을_막는_헤더가_있다() -> None:
    """스트림이 이상했던 요청을 서버 기록과 잇고(스토리 14), 중간 장치가 모았다 보내지 않는다
    (스토리 20)."""
    async with _serving(_app()) as client:
        response = await client.post("/runs", json=_start("echo"), headers=CHANNEL)

    assert response.headers["X-Request-Id"]
    assert response.headers["Cache-Control"] == "no-cache"
    assert response.headers["X-Accel-Buffering"] == "no"


async def test_모델이_조용한_동안_keepalive_주석이_나간다(monkeypatch: pytest.MonkeyPatch) -> None:
    """중간 프록시가 유휴 연결을 자른다(스토리 19). 첫 이벤트를 기다리는 방식이 FastAPI 의 SSE
    경로를 벗어나면 keepalive 를 잃는데, 이 테스트가 그 자리를 닫는다. 간격을 줄여 잰다."""
    monkeypatch.setattr(fastapi.routing, "_PING_INTERVAL", 0.01)
    model = _gated_model()
    asyncio.get_running_loop().call_later(0.2, model.gate.set)

    async with _serving(_app(model=model)) as client:
        response = await client.post("/runs", json=_start("asking"), headers=CHANNEL)

    blocks = _blocks(response.text)
    assert ": ping" in blocks
    assert _types(_frames(response.text)) == ["run_started", "llm_called", "run_finished"]


@pytest.mark.parametrize(
    ("agent", "model", "tools", "cause"),
    [
        ("adding", GenericFakeChatModel(messages=iter(())), BrokenTools(), "server did not start"),
        ("asking", GenericFakeChatModel(messages=_failing_replies()), ScopedTools(), "API down"),
    ],
    ids=["도구 연결 실패", "모델 실패"],
)
async def test_실행_안의_실패는_200_스트림_속_run_failed_다(
    agent: str, model: ChatModel, tools: ToolSource, cause: str
) -> None:
    """트레이스가 남는 실패와 남지 않는 실패가 CLI 와 같은 경계로 갈린다(스토리 9). 경계는 첫
    이벤트다."""
    trace = FakeTrace()
    app = _app(trace=trace, model=model, tools=tools)

    async with _serving(app) as client:
        response = await client.post("/runs", json=_start(agent), headers=CHANNEL)

    assert response.status_code == 200
    frames = _frames(response.text)
    assert _types(frames) == ["run_started", "run_failed"]
    assert cause in json.loads(frames[-1])["error"]
    assert frames == trace.lines


async def test_채널에서_일으킨_실행이_같은_앱의_관리_API_목록과_상세에_바로_보인다() -> None:
    """두 면이 트레이스 포트 하나를 함께 쓴다(스토리 49). 떠난 쪽이 나머지를 보는 자리가 이것이다
    (스토리 17)."""
    async with _serving(_app()) as client:
        streamed = await client.post("/runs", json=_start("echo"), headers=CHANNEL)
        run_id = json.loads(_frames(streamed.text)[0])["run_id"]
        listed = await client.get("/traces", headers=ADMIN)
        detail = await client.get(f"/traces/{run_id}", headers=ADMIN)

    assert [(row["run_id"], row["status"]) for row in listed.json()["runs"]] == [
        (run_id, "finished")
    ]
    assert detail.json()["events"] == [json.loads(frame) for frame in _frames(streamed.text)]


# 실행 전 실패 — 응답은 첫 이벤트를 받은 뒤에 시작한다


async def test_없는_에이전트는_404_봉투이고_트레이스가_생기지_않는다() -> None:
    """내 오타와 서버 고장이 갈린다(스토리 10). 200 으로 시작한 뒤 끊긴 스트림이 아니다."""
    trace = FakeTrace()

    async with _serving(_app(trace=trace)) as client:
        response = await client.post("/runs", json=_start("nobody"), headers=CHANNEL)

    assert response.status_code == 404
    body = response.json()
    assert body["code"] == "not_found"
    assert "nobody" in body["message"]
    assert body["request_id"] == response.headers["X-Request-Id"]
    assert trace.lines == []


async def _pre_run_error(agent: str) -> PluginError:
    """core 가 그 에이전트에 대해 실행 전에 던지는 것. 봉투의 문구를 대조할 기준이다."""
    events = run(
        AgentName(agent),
        "2+3?",
        PRINCIPAL,
        plugins=FakePlugins(),
        model=GenericFakeChatModel(messages=iter(())),
        tools=ScopedTools(),
        trace=FakeTrace(),
        clock=FakeClock(),
    )
    with pytest.raises(PluginError) as caught:
        await anext(events)
    return caught.value


@pytest.mark.parametrize(
    "agent",
    ["broken", "ghostly", "leaky", "unloadable"],
    ids=["깨진 매니페스트", "없는 mcp", "마스킹과 승인이 겹침", "진입점 import 실패"],
)
async def test_실행_전_구성_오류는_500_봉투이고_message_가_그_PluginError_의_문구다(
    agent: str,
) -> None:
    """상태 코드만 보면 제너레이터 안에서 첫 yield 전에 던지는 구현도 초록이다. 그 예외는 예외
    그룹으로 감싸져 표의 마지막 갈래(고정 문구)로 간다(명세 검토의 프로브). 4xx 면 운영자에게
    알리지 않는다(스토리 11)."""
    expected = await _pre_run_error(agent)
    trace = FakeTrace()

    async with _serving(_app(trace=trace)) as client:
        response = await client.post("/runs", json=_start(agent), headers=CHANNEL)

    assert response.status_code == 500
    body = response.json()
    assert body["code"] == "internal_error"
    assert body["message"] == str(expected)
    assert body["message"] != INTERNAL_MESSAGE
    assert trace.lines == []


# 본문 — 원격 입력이 파일 경로로 조립되기 전에 끝난다


# 플러그인 루트를 벗어나려는 이름과 패턴을 어기는 이름. `plugins/agents/{agent}/plugin.toml` 로
# 조립되므로 하나라도 포트에 닿으면 루트 밖을 읽는다. 본문이라 퍼센트 인코딩 없이 그대로 싣는다.
ESCAPING_AGENTS = (
    "..",
    "../../etc",
    "..\\..\\secret",
    "/etc/passwd",
    "C:\\Windows",
    "C:/Windows",
    "calc\n",
    "\ncalc",
    "Calc",
    "",
)


async def test_패턴을_어기는_에이전트_이름은_422이고_플러그인_포트가_불리지_않는다() -> None:
    """관리의 `{name}` 과 같은 규칙이고 같은 이유다(스토리 56). 404 와 500 이 갈리는 것 자체가 임의
    경로의 파일 존재를 알려 주는 오라클이다."""
    plugins = FakePlugins()

    async with _serving(_app(plugins=plugins)) as client:
        for agent in ESCAPING_AGENTS:
            response = await client.post("/runs", json=_start(agent), headers=CHANNEL)

            assert response.status_code == 422, agent
            fields = [violation["field"] for violation in response.json()["violations"]]
            assert fields == ["body.agent"], agent
    assert plugins.calls == 0


@pytest.mark.parametrize(
    ("body", "field"),
    [
        ({"request": "2+3?"}, "body.agent"),
        ({"agent": "echo"}, "body.request"),
        ({"agent": "echo", "request": 42}, "body.request"),
    ],
    ids=["에이전트 없음", "요청 없음", "요청이 문자열이 아님"],
)
async def test_필드가_빠지거나_모양이_틀리면_422이고_violations_가_그_필드를_가리킨다(
    body: Mapping[str, Json], field: str
) -> None:
    """어느 필드가 왜 틀렸는지 받는다(스토리 12)."""
    plugins = FakePlugins()

    async with _serving(_app(plugins=plugins)) as client:
        response = await client.post("/runs", json=body, headers=CHANNEL)

    assert response.status_code == 422
    assert response.json()["code"] == "invalid_request"
    assert [violation["field"] for violation in response.json()["violations"]] == [field]
    assert plugins.calls == 0


@pytest.mark.parametrize("extra", ["principal", "approver", "model"])
async def test_주체_승인자_모델을_본문에_실으면_무시하지_않고_422다(extra: str) -> None:
    """보낸 쪽이 자기 값이 쓰였다고 믿게 두지 않는다(ADR 0015, 스토리 23·45)."""
    plugins = FakePlugins()

    async with _serving(_app(plugins=plugins)) as client:
        response = await client.post(
            "/runs", json={**_start("echo"), extra: "mallory"}, headers=CHANNEL
        )

    assert response.status_code == 422
    assert [violation["field"] for violation in response.json()["violations"]] == [f"body.{extra}"]
    assert plugins.calls == 0


async def test_요청은_문자열이면_되고_그대로_실행에_실린다() -> None:
    """CLI 가 받는 것과 같다. 여러 줄도 빈 문자열도 요청이다."""
    async with _serving(_app()) as client:
        for request in ("여러\n줄의 요청", ""):
            response = await client.post("/runs", json=_start("echo", request), headers=CHANNEL)

            first = json.loads(_frames(response.text)[0])
            assert first["request"] == request, request


async def test_422의_서버_기록은_위치와_문구만_싣고_입력값을_싣지_않는다() -> None:
    """채널의 본문은 사람이 쓴 요청 문자열이다(원칙 V). 공용 층의 규칙이라 관리 API 에도 함께
    걸린다."""
    stderr = io.StringIO()

    async with _serving(_app(stderr=stderr)) as client:
        await client.post(
            "/runs",
            json={"agent": "../XYZZY-agent", "request": "PLUGH-request", "principal": "FROB-who"},
            headers=CHANNEL,
        )

    logged = stderr.getvalue()
    assert "body.agent" in logged
    assert "body.principal" in logged
    for value in ("XYZZY", "PLUGH", "FROB"):
        assert value not in logged, value


# 승인 — 멈춘 실행에 결정을 내고 재개된 실행의 스트림을 받는다

APPROVE: Mapping[str, Json] = {"decision": "approve"}
DENY: Mapping[str, Json] = {"decision": "deny", "reason": "너무 크다"}

# 채널을 지나지 않고 트레이스에 직접 둔 실행. 식별자가 `FakeClock` 이 내는 것과 겹치지 않는다.
STORED = RunId("stored-1")
NO_RUNS: frozenset[RunId] = frozenset()
ADD_2_3: Mapping[str, Json] = {"a": 2, "b": 3}


def _stored_start(agent: str = "gated") -> RunStarted:
    return RunStarted(
        run_id=STORED, ts=T0, agent=AgentName(agent), request="2+3?", principal=PRINCIPAL
    )


def _stored_pause(args: Mapping[str, Json] = ADD_2_3) -> RunPaused:
    return RunPaused(run_id=STORED, ts=T0, tool="add", args=args)


def _stored(*events: Event, into: FakeTrace | None = None) -> FakeTrace:
    """그 이벤트들이 이미 쓰인 트레이스. 앱을 세우기 전에 채운다."""
    trace = into or FakeTrace()
    for event in events:
        trace.write(event)
    return trace


async def _decide(client: AsyncClient, run_id: str, decision: Mapping[str, Json]) -> Response:
    return await client.post(f"/runs/{run_id}/approval", json=decision, headers=CHANNEL)


async def test_승인의_스트림은_결정에서_시작해_결말로_끝나고_승인자는_앱의_주체다() -> None:
    """재개 스트림의 첫 이벤트가 내 결정이다(스토리 29·30). 프레임은 트레이스의 새 줄과 문자열로
    같다. 승인자는 본문이 아니라 `create_app` 에 넘긴 주체다(ADR 0015)."""
    tools = ScopedTools()
    trace = FakeTrace()
    app = _app(trace=trace, tools=tools)

    async with _serving(app) as client:
        started = await client.post("/runs", json=_start("gated"), headers=CHANNEL)
        before = len(trace.lines)
        response = await _decide(client, "run-1", APPROVE)

    assert _types(_frames(started.text))[-1] == "run_paused"
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/event-stream")
    frames = _frames(response.text)
    assert frames == trace.lines[before:]
    assert _types(frames) == ["approval_granted", "run_resumed", "tool_called", "run_finished"]
    assert json.loads(frames[0])["approver"] == PRINCIPAL
    assert tools.calls == [("add", ADD_2_3)]


async def test_거부하면_approval_denied_가_다듬은_사유를_싣고_거부된_도구는_불리지_않는다() -> None:
    """CLI 의 결정 해석은 다듬은 사유를 넘긴다. 두 채널에서 같은 결정이 같게 기록된다(스토리 27).
    다듬는 규칙도 CLI 의 것(파이썬 `str.strip`)이다 — pydantic 의 다듬기는 U+001C~U+001F 를
    공백으로 보지 않는다. 거부는 실행을 끝내지 않는다 — 사유가 모델에 돌아가고 실행이 이어서
    끝난다(ADR 0009)."""
    tools = ScopedTools()
    trace = FakeTrace()
    model = _tool_calling_model(_tool_request(("add", ADD_2_3)), AIMessage(content="못 더했다"))
    app = _app(trace=trace, tools=tools, model=model)

    async with _serving(app) as client:
        await client.post("/runs", json=_start("gated-asking"), headers=CHANNEL)
        before = len(trace.lines)
        response = await _decide(
            client, "run-1", {"decision": "deny", "reason": " \x1c 너무 크다 \x1f\n"}
        )

    frames = _frames(response.text)
    assert frames == trace.lines[before:]
    assert _types(frames) == [
        "approval_denied",
        "run_resumed",
        "tool_called",
        "llm_called",
        "run_finished",
    ]
    denied = json.loads(frames[0])
    assert denied["reason"] == "너무 크다"
    assert denied["approver"] == PRINCIPAL
    refused = json.loads(frames[2])
    assert refused["ok"] is False
    assert "너무 크다" in refused["content"]
    assert tools.calls == []


async def test_재개_스트림은_멈추기_전에_이미_본_사실을_되풀이하지_않는다() -> None:
    """재생된 사실은 새 사실이 아니다(스토리 31, ADR 0009). 멈추기 전에 시작과 모델 호출과 도구
    호출이 하나씩 있었고, 재개 스트림에는 멈춘 그 호출부터의 새 사실만 있다. core 가 지키는 것이
    채널을 지나도 그대로임을 한 번 본다."""
    tools = ScopedTools()
    trace = FakeTrace()
    login: Mapping[str, Json] = {"password": "letmein"}
    model = _tool_calling_model(
        _tool_request(("add", ADD_2_3), ("login", login)), AIMessage(content="들어갔다")
    )
    app = _app(trace=trace, tools=tools, model=model)

    async with _serving(app) as client:
        started = await client.post("/runs", json=_start("careful"), headers=CHANNEL)
        response = await _decide(client, "run-1", APPROVE)

    assert _types(_frames(started.text)) == [
        "run_started",
        "llm_called",
        "tool_called",
        "run_paused",
    ]
    frames = _frames(response.text)
    assert _types(frames) == [
        "approval_granted",
        "run_resumed",
        "tool_called",
        "llm_called",
        "run_finished",
    ]
    assert json.loads(frames[2])["tool"] == "login"
    assert json.loads(frames[3])["prompt"] == ""
    assert tools.calls == [("add", ADD_2_3), ("login", login)]


async def test_재개_뒤_첫_호출이_멈춘_호출이_아니면_run_resumed_없이_run_failed_로_끝난다() -> None:
    """결정은 어긋난 호출에 적용되지 않는다(스토리 38). 멈춘 것은 add(9, 9) 인데 에이전트는
    add(2, 3) 을 부른다. core 가 지키는 것이 채널을 지나도 그대로다."""
    tools = ScopedTools()
    trace = _stored(_stored_start(), _stored_pause({"a": 9, "b": 9}))
    before = len(trace.lines)
    app = _app(trace=trace, tools=tools)

    async with _serving(app) as client:
        response = await _decide(client, STORED, APPROVE)

    frames = _frames(response.text)
    assert frames == trace.lines[before:]
    assert _types(frames) == ["approval_granted", "run_failed"]
    assert "멈춘 자리와 다르다" in json.loads(frames[-1])["error"]
    assert tools.calls == []


async def test_재개가_다시_멈추면_같은_경로로_둘째_결정을_내_끝까지_간다() -> None:
    """한 턴에 승인 대상이 둘이면 두 번 멈춘다(스토리 36). 결정 하나는 도구 하나만 판정한다."""
    tools = ScopedTools()
    trace = FakeTrace()
    add_4_5: Mapping[str, Json] = {"a": 4, "b": 5}
    model = _tool_calling_model(
        _tool_request(("add", ADD_2_3), ("add", add_4_5)), AIMessage(content="5 와 9")
    )
    app = _app(trace=trace, tools=tools, model=model)

    async with _serving(app) as client:
        started = await client.post("/runs", json=_start("gated-asking"), headers=CHANNEL)
        first = await _decide(client, "run-1", APPROVE)
        second = await _decide(client, "run-1", APPROVE)

    assert json.loads(_frames(started.text)[-1])["args"] == ADD_2_3
    assert _types(_frames(first.text)) == [
        "approval_granted",
        "run_resumed",
        "tool_called",
        "run_paused",
    ]
    assert json.loads(_frames(first.text)[-1])["args"] == add_4_5
    assert _types(_frames(second.text)) == [
        "approval_granted",
        "run_resumed",
        "tool_called",
        "llm_called",
        "run_finished",
    ]
    assert json.loads(_frames(second.text)[-1])["output"] == "5 와 9"
    assert tools.calls == [("add", ADD_2_3), ("add", add_4_5)]


async def test_채널_밖에서_멈춘_실행을_채널이_재개하고_승인자는_채널의_주체다() -> None:
    """CLI 에서 시작한 실행을 HTTP 로 승인하는 것과 같은 모양이다(스토리 37). 트레이스가 같으면
    같은 실행이다. 시작한 주체와 승인자가 다른 것이 곧 결정의 승인자가 채널의 주체라는 뜻이다."""
    plugins = FakePlugins()
    tools = ScopedTools()
    trace = FakeTrace()
    clock = FakeClock()
    outside = [
        event
        async for event in run(
            AgentName("gated"),
            "2+3?",
            Principal("bob"),
            plugins=plugins,
            model=GenericFakeChatModel(messages=iter(())),
            tools=tools,
            trace=trace,
            clock=clock,
        )
    ]
    paused = outside[-1]
    assert isinstance(paused, RunPaused)
    app = _app(plugins=plugins, trace=trace, tools=tools, clock=clock)

    async with _serving(app) as client:
        response = await _decide(client, paused.run_id, APPROVE)

    frames = _frames(response.text)
    assert _types(frames) == ["approval_granted", "run_resumed", "tool_called", "run_finished"]
    assert json.loads(frames[0])["approver"] == PRINCIPAL
    assert tools.calls == [("add", ADD_2_3)]


async def test_한_루프에서_동시에_온_결정_둘은_하나만_받아들여져_도구가_한_번_불린다() -> None:
    """두 번 누른 버튼 하나가 승인된 도구를 두 번 실행하지 않는다(스토리 34·35·73, ADR 0014).

    이것을 지키는 것은 설계가 아니라 `resume()` 의 첫 걸음(트레이스 읽기, 일시정지 확인, 결정
    쓰기)에 await 가 없다는 사실 하나다. 트레이스 쓰기를 비동기로 바꾸거나 스레드로 보내는 변경은
    성능 개선처럼 보이지만 둘째 결정이 마지막 이벤트를 아직 일시정지로 읽게 만든다. 그 순간 여기가
    깨진다. 범위는 이벤트 루프 하나(워커 하나)다. 프로세스 사이의 경합 — CLI `resume` 과 HTTP 승인이
    같은 순간 같은 실행에 오는 것 — 은 알려진 한계이고 이 테스트가 재지 않는다.

    디스크에 닿는 데 시간이 들게 두는 이유는 읽기나 쓰기를 스레드로 보내는 변경이 스레드 타이밍과
    무관하게 여기서 깨지게 하기 위해서다. 즉시 끝나면 둘째 요청이 첫째의 결정보다 먼저 읽을지가
    타이밍에 달려, `asyncio.to_thread` 로 쓰기를 보내는 변경이 초록으로 지나갔다(셀프 리뷰)."""
    tools = ScopedTools()
    trace = FakeTrace(disk_seconds=0.05)
    app = _app(trace=trace, tools=tools)

    async with _serving(app) as client:
        await client.post("/runs", json=_start("gated"), headers=CHANNEL)
        responses = await asyncio.gather(
            _decide(client, "run-1", APPROVE), _decide(client, "run-1", APPROVE)
        )

    assert sorted(response.status_code for response in responses) == [200, 409]
    accepted = next(response for response in responses if response.status_code == 200)
    rejected = next(response for response in responses if response.status_code == 409)
    assert _types(_frames(accepted.text)) == [
        "approval_granted",
        "run_resumed",
        "tool_called",
        "run_finished",
    ]
    assert rejected.json()["code"] == "conflict"
    decisions = [kind for kind in _types(trace.lines) if kind.startswith("approval_")]
    assert decisions == ["approval_granted"]
    assert tools.calls == [("add", ADD_2_3)]


# 결정이 받아들여지지 않는 실행 — 상태 코드가 가르고 트레이스에 결정이 쓰이지 않는다


async def test_없는_실행에_결정을_내면_404_봉투이고_아무것도_쓰이지_않는다() -> None:
    """식별자를 잘못 적은 것이다(스토리 32). 200 으로 시작한 뒤 끊긴 스트림이 아니다."""
    trace = FakeTrace()

    async with _serving(_app(trace=trace)) as client:
        response = await _decide(client, "nobody-1", APPROVE)

    assert response.status_code == 404
    body = response.json()
    assert body["code"] == "not_found"
    assert "nobody-1" in body["message"]
    assert body["request_id"] == response.headers["X-Request-Id"]
    assert trace.lines == []


@pytest.mark.parametrize(
    ("events", "legacy"),
    [
        ((_stored_start(), RunFinished(run_id=STORED, ts=T0, output="5")), NO_RUNS),
        ((_stored_start(), RunFailed(run_id=STORED, ts=T0, error="API down")), NO_RUNS),
        ((_stored_start(),), NO_RUNS),
        ((_stored_start(), _stored_pause()), frozenset({STORED})),
    ],
    ids=["끝난 실행", "실패한 실행", "결말 없는 실행", "형식 1 트레이스"],
)
async def test_재개할_수_없는_실행은_409_봉투이고_결정이_쓰이지_않는다(
    events: tuple[Event, ...], legacy: frozenset[RunId]
) -> None:
    """이미 누군가 결정한 것과 식별자를 잘못 적은 것은 다른 일이다(스토리 32·33). 형식 1 은 멈춘
    실행이어도 읽을 수만 있고 재개할 수 없다."""
    tools = ScopedTools()
    trace = _stored(*events, into=FakeTrace(legacy=legacy))
    before = list(trace.lines)

    async with _serving(_app(trace=trace, tools=tools)) as client:
        response = await _decide(client, STORED, APPROVE)

    assert response.status_code == 409
    body = response.json()
    assert body["code"] == "conflict"
    assert STORED in body["message"]
    assert trace.lines == before
    assert tools.calls == []


@pytest.mark.parametrize(
    ("agent", "damaged", "cause"),
    [("gated", frozenset({STORED}), "모르는 종류"), ("vanished", NO_RUNS, "vanished")],
    ids=["손상된 트레이스", "트레이스가 가리키는 에이전트가 사라진 실행"],
)
async def test_기록이_깨진_실행은_404_가_아니라_500_봉투이고_결정이_쓰이지_않는다(
    agent: str, damaged: frozenset[RunId], cause: str
) -> None:
    """요청이 가리킨 실행은 있다. 깨진 것은 요청이 아니라 서버의 기록이나 플러그인 루트라, 404 로
    말하면 식별자를 잘못 적었다고 믿게 된다(ADR 0014 의 2026-09-24 이력). 문구가 core 의 것이라는
    단언은 예외 그룹에 감싸져 고정 문구로 가는 구현이 엉뚱한 이유로 초록이 되지 않게 한다."""
    trace = _stored(_stored_start(agent), _stored_pause(), into=FakeTrace(damaged=damaged))
    before = list(trace.lines)

    async with _serving(_app(trace=trace)) as client:
        response = await _decide(client, STORED, APPROVE)

    assert response.status_code == 500
    body = response.json()
    assert body["code"] == "internal_error"
    assert cause in body["message"]
    assert body["message"] != INTERNAL_MESSAGE
    assert trace.lines == before


# 결정 본문과 경로 — 형식이 틀리면 트레이스에 닿기 전에 끝난다


@pytest.mark.parametrize(
    ("decision", "field"),
    [
        ({"decision": "approve", "reason": "좋다"}, "body.approve.reason"),
        ({"decision": "approve", "reason": ""}, "body.approve.reason"),
        ({"decision": "deny"}, "body.deny.reason"),
        ({"decision": "deny", "reason": ""}, "body.deny.reason"),
        ({"decision": "deny", "reason": " \t\n "}, "body.deny.reason"),
        ({"decision": "deny", "reason": "\x1c\x1f"}, "body.deny.reason"),
        ({}, "body"),
        ({"reason": "좋다"}, "body"),
        ({"decision": "maybe"}, "body"),
    ],
    ids=[
        "승인에 사유",
        "승인에 빈 사유",
        "거부에 사유 없음",
        "거부에 빈 사유",
        "거부에 공백뿐인 사유",
        "거부에 파이썬만 공백으로 보는 사유",
        "판별자 없음",
        "판별자 없이 사유만",
        "모르는 결정",
    ],
)
async def test_결정의_모양이_틀리면_422이고_violations_가_그_필드를_가리키며_결정이_쓰이지_않는다(
    decision: Mapping[str, Json], field: str
) -> None:
    """사유 없는 거부가 기본값으로 굳지 않고(스토리 26·27), 승인에 적은 말이 조용히 버려지지 않는다
    (스토리 28). 멤버 안의 필드는 판별자 값을 경로에 든다 — pydantic 이 판별 유니온의 오류 위치에
    태그를 넣는다. 트레이스를 읽지도 않는다."""
    trace = _stored(_stored_start(), _stored_pause())
    before = list(trace.lines)

    async with _serving(_app(trace=trace)) as client:
        response = await _decide(client, STORED, decision)

    assert response.status_code == 422
    assert response.json()["code"] == "invalid_request"
    assert [violation["field"] for violation in response.json()["violations"]] == [field]
    assert trace.reads == []
    assert trace.lines == before


@pytest.mark.parametrize("extra", ["approver", "principal"])
@pytest.mark.parametrize("decision", [APPROVE, DENY], ids=["승인", "거부"])
async def test_결정에_승인자나_주체를_실으면_무시하지_않고_422다(
    decision: Mapping[str, Json], extra: str
) -> None:
    """결정 이벤트의 승인자는 `create_app` 에 넘긴 주체다(ADR 0015, 스토리 45). 보낸 쪽이 자기
    값이 쓰였다고 믿게 두지 않는다."""
    trace = _stored(_stored_start(), _stored_pause())

    async with _serving(_app(trace=trace)) as client:
        response = await _decide(client, STORED, {**decision, extra: "mallory"})

    assert response.status_code == 422
    fields = [violation["field"] for violation in response.json()["violations"]]
    assert fields == [f"body.{decision['decision']}.{extra}"]
    assert trace.reads == []


# 루트를 벗어나려는 식별자와 패턴을 어기는 식별자. `traces/{run_id}.jsonl` 로 조립되므로 하나라도
# 포트에 닿으면 루트 밖을 읽는다. 퍼센트 인코딩으로 적는 이유는 httpx 가 맨 `..` 조각을 보내기 전에
# 지워 요청이 다른 경로로 가기 때문이다. 개행이 꼬리에 붙은 것은 떼어지면 멈춘 실행 `stored-1` 로
# 읽히는 값이다.
ESCAPING_RUN_IDS = (
    "%2E%2E",
    "..%2F..%2Fetc",
    "..%5C..%5Csecret",
    "%2Fetc%2Fpasswd",
    "C:%5CWindows",
    "C:%2FWindows",
    "stored-1%0A",
    "%0Astored-1",
    "stored%0A-1",
    "a" * 65,
)


async def test_패턴을_어기는_실행_식별자는_422이고_트레이스_포트가_불리지_않는다() -> None:
    """관리의 `/traces/{run_id}` 와 같은 규칙이고 같은 이유다(스토리 56). 404 와 500 이 갈리는 것
    자체가 임의 경로의 파일 존재를 알려 주는 오라클이다."""
    trace = _stored(_stored_start(), _stored_pause())
    before = list(trace.lines)

    async with _serving(_app(trace=trace)) as client:
        for run_id in ESCAPING_RUN_IDS:
            response = await _decide(client, run_id, APPROVE)

            assert response.status_code == 422, run_id
            fields = [violation["field"] for violation in response.json()["violations"]]
            assert fields == ["path.run_id"], run_id
    assert trace.reads == []
    assert trace.lines == before


# 실행은 앱이 소유한다 — 둘째 구동자(스트림의 수명 넷)


class _Wire:
    """같은 앱을 ASGI 로 직접 부르는 쪽. 받은 메시지를 순서대로 적고 끊김과 막힘을 테스트가 낸다.

    receive 는 본문을 한 번 주고 그 뒤로는 테스트가 떠날 때까지 기다린다. send 는 막아 두면 그
    자리에서 기다린다 — 느린 수신자다.
    """

    def __init__(self, body: Mapping[str, Json]) -> None:
        self.sent: list[Message] = []
        self._body = json.dumps(body).encode()
        self._requested = False
        self._gone = asyncio.Event()
        self._flowing = asyncio.Event()
        self._flowing.set()

    async def receive(self) -> Message:
        if not self._requested:
            self._requested = True
            return {"type": "http.request", "body": self._body, "more_body": False}
        await self._gone.wait()
        return {"type": "http.disconnect"}

    async def send(self, message: Message) -> None:
        await self._flowing.wait()
        self.sent.append(message)

    def leave(self) -> None:
        self._gone.set()

    def hold(self) -> None:
        self._flowing.clear()

    def release(self) -> None:
        self._flowing.set()

    def frames(self) -> list[str]:
        chunks = [
            bytes(message["body"])
            for message in self.sent
            if message["type"] == "http.response.body"
        ]
        return _frames(b"".join(chunks).decode())


def _scope() -> Scope:
    """`POST /runs` 하나. 채널 토큰을 든다."""
    return {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "POST",
        "scheme": "http",
        "path": "/runs",
        "raw_path": b"/runs",
        "root_path": "",
        "query_string": b"",
        "headers": [
            (b"authorization", f"Bearer {CHANNEL_TOKEN}".encode()),
            (b"content-type", b"application/json"),
        ],
        "client": ("127.0.0.1", 50000),
        "server": ("channel.test", 80),
    }


async def test_미들웨어_둘_뒤에서도_모델을_풀기_전에_run_started_프레임이_도착한다() -> None:
    """스트림이 모이지 않는다(스토리 75). 실행이 모델 앞에 서 있는 동안 첫 프레임이 `send` 에
    닿으려면 응답이 이미 시작해 있어야 하므로, "첫 이벤트가 나오면 응답이 바로 시작한다"도 함께
    잰다(명세의 이음매)."""
    model = _gated_model()
    app = _app(model=model)
    wire = _Wire(_start("asking"))

    async with _lifespan(app):
        call = asyncio.create_task(app(_scope(), wire.receive, wire.send))
        await _until(lambda: wire.frames() != [])

        assert _types(wire.frames()) == ["run_started"]
        assert not model.gate.is_set()
        model.gate.set()
        await call

    assert _types(wire.frames()) == ["run_started", "llm_called", "run_finished"]


async def test_끊겨도_실행은_끝까지_가서_트레이스가_결말로_끝난다() -> None:
    """연결이 끊기는 것은 전송의 사건이지 사람의 결정이 아니다(스토리 15·74, ADR 0014). 앱
    호출은 실행을 기다리지 않고 돌아온다."""
    model = _gated_model()
    trace = FakeTrace()
    app = _app(model=model, trace=trace)
    wire = _Wire(_start("asking"))

    async with _lifespan(app):
        call = asyncio.create_task(app(_scope(), wire.receive, wire.send))
        await _until(lambda: wire.frames() != [])
        wire.leave()
        async with asyncio.timeout(5):
            await call
        model.gate.set()
        await _until(lambda: trace.status(RunId("run-1")) != "unfinished")

    assert trace.status(RunId("run-1")) == "finished"
    assert _types(wire.frames()) == ["run_started"]


async def test_받는_쪽이_느려도_실행은_기다리지_않고_끝까지_간다() -> None:
    """받는 쪽이 느리면 그 실행의 이벤트가 쌓이고 실행은 트레이스에 계속 쓴다(명세). 크기가 제한된
    큐에 기다리며 넣는 구현은 이것만 어기고 나머지를 모두 통과한다(명세 검토)."""
    model = _gated_model()
    trace = FakeTrace()
    app = _app(model=model, trace=trace)
    wire = _Wire(_start("chatty"))

    async with _lifespan(app):
        call = asyncio.create_task(app(_scope(), wire.receive, wire.send))
        await _until(lambda: wire.frames() != [])
        wire.hold()
        model.gate.set()
        await _until(lambda: trace.status(RunId("run-1")) == "finished")
        wire.release()
        await call

    assert wire.frames() == trace.lines
    assert len(trace.lines) == BURST + 3


async def test_서버가_멈추면_떠난_실행은_기다리지_않고_취소되어_결말_없음이다() -> None:
    """멈추라는 명령이 실행 하나가 끝나기를 기다리지 않는다(스토리 47). 끝내지 못한 실행을
    실패라고 적지 않는다(스토리 48). 모델의 문은 끝내 열리지 않는다."""
    model = _gated_model()
    trace = FakeTrace()
    app = _app(model=model, trace=trace)
    wire = _Wire(_start("asking"))
    lifespan = _lifespan(app)

    await lifespan.__aenter__()
    call = asyncio.create_task(app(_scope(), wire.receive, wire.send))
    await _until(lambda: wire.frames() != [])
    wire.leave()
    await call
    async with asyncio.timeout(5):
        await lifespan.__aexit__(None, None, None)

    assert not model.gate.is_set()
    assert trace.status(RunId("run-1")) == "unfinished"
    assert _types(trace.lines) == ["run_started"]


async def test_도구를_쓰는_실행이_끝까지_가고_도구_연결이_닫힌다() -> None:
    """가짜 도구 포트는 MCP 어댑터처럼 anyio 취소 범위 안에서 연결을 연다. 이것은 기본 경로다.
    연결이 연 태스크가 아닌 곳에서 닫히는 길은 트레이스를 쓰지 못한 실행과 서버가 멈출 때 생기고,
    그 둘을 아래 테스트와 수명을 닫는 테스트가 가른다."""
    tools = ScopedTools()
    app = _app(tools=tools)

    async with _serving(app) as client:
        response = await client.post("/runs", json=_start("adding"), headers=CHANNEL)

    assert _types(_frames(response.text)) == ["run_started", "tool_called", "run_finished"]
    assert tools.closed


async def test_트레이스를_쓰지_못해_멈춘_실행은_스트림을_결말_없이_닫고_앱은_계속_선다() -> None:
    """결말 없이 닫힌 스트림은 서버가 그 실행을 끝내지 못했다는 뜻이다(스토리 18). 실행 하나의
    실패가 앱의 수명이 소유한 다른 실행들을 함께 끝내지 않는다. 원인은 서버 기록에 남는다."""
    stderr = io.StringIO()
    trace = FakeTrace(broken_after=1)
    app = _app(trace=trace, stderr=stderr)

    async with _serving(app) as client:
        broken = await client.post("/runs", json=_start("echo"), headers=CHANNEL)
        health = await client.get("/health")

    assert broken.status_code == 200
    assert _types(_frames(broken.text)) == ["run_started"]
    assert "run-1" in stderr.getvalue()
    assert broken.headers["X-Request-Id"] in stderr.getvalue()
    assert "디스크가 가득 찼다" in stderr.getvalue()
    assert health.status_code == 200


# 계약 — 스트림 항목과 본문이 이름 있는 타입으로 실린다


# 채널 라우트가 붙기 전 계약의 컴포넌트 이름 전부. 채널은 이름을 더하기만 하고 기존 이름을 바꾸지
# 않는다. 바뀌면 생성 클라이언트의 타입 이름이 바뀐다. 결정의 멤버를 `ApprovalGranted` 처럼 이벤트와
# 같은 이름으로 지으면 여기 있는 이벤트 컴포넌트가 입력과 출력으로 갈라진다(명세 검토의 프로브).
EXISTING_COMPONENTS = frozenset(
    {
        "ApprovalDenied",
        "ApprovalGranted",
        "ErrorCode",
        "ErrorEnvelope",
        "Health",
        "Json",
        "LlmCalled",
        "McpServer",
        "PluginKind",
        "PluginManifest",
        "PluginRow",
        "RunFailed",
        "RunFinished",
        "RunPaused",
        "RunResumed",
        "RunRow",
        "RunStarted",
        "RunStatus",
        "RunSummary",
        "ToolCall",
        "ToolCalled",
        "Trace",
        "TraceEvent",
        "TracePage",
        "TraceSchemaVersion",
        "UnknownEvent",
        "UnreadableManifest",
        "UnreadableTrace",
        "Violation",
    }
)


def _members(schema: Mapping[str, Json]) -> list[str]:
    one_of = schema["oneOf"]
    assert isinstance(one_of, list)
    references: list[str] = []
    for member in one_of:
        assert isinstance(member, dict)
        references.append(str(member["$ref"]))
    return references


CHANNEL_OPERATIONS = (("/runs", "post"), ("/runs/{run_id}/approval", "post"))


def test_스트림_항목이_이름_있는_Event_이고_TraceEvent_와_같은_멤버를_가리킨다() -> None:
    """생성 클라이언트가 `Streamitem Start Run` 같은 익명 유니온을 받지 않고(스토리 21), 같은
    이벤트를 두 타입으로 다루지 않는다(스토리 22). 기존 이름은 그대로이고 새 이름만 늘며 입력과
    출력으로 갈라진 이름이 없다. 두 채널 라우트의 스트림이 같은 항목이다."""
    document = _app().openapi()
    schemas = document["components"]["schemas"]

    for path, method in CHANNEL_OPERATIONS:
        ok = document["paths"][path][method]["responses"]["200"]
        item = ok["content"]["text/event-stream"]["itemSchema"]
        assert item["properties"]["data"]["contentSchema"] == {
            "$ref": "#/components/schemas/Event"
        }, path
    assert EXISTING_COMPONENTS <= set(schemas)
    assert set(schemas) - EXISTING_COMPONENTS == {
        "Event",
        "StartRun",
        "Decision",
        "Approve",
        "Deny",
    }
    assert not any(name.endswith(("-Input", "-Output")) for name in schemas)
    assert not any("Streamitem" in name for name in schemas)
    trace_members = _members(schemas["TraceEvent"])
    assert _members(schemas["Event"]) == [
        member for member in trace_members if member != "#/components/schemas/UnknownEvent"
    ]


def test_스트림_항목_스키마는_FastAPI_의_정형_그대로_data_만_필수다() -> None:
    """광고를 그대로 둔다. 서버는 data 만 보내고 그것은 프레임 테스트가 고정한다(ADR 0014 의
    2026-09-24 이력)."""
    paths = _app().openapi()["paths"]

    for path, method in CHANNEL_OPERATIONS:
        item = paths[path][method]["responses"]["200"]["content"]["text/event-stream"]["itemSchema"]
        assert item["required"] == ["data"], path
        assert set(item["properties"]) == {"data", "event", "id", "retry"}, path


def test_POST_runs_가_사람이_지은_operation_id_와_봉투_에러_문서를_든다() -> None:
    """생성 클라이언트의 함수 이름이 `operationId` 다(스토리 64). 409 는 재개 라우트의 것이다."""
    operation = _app().openapi()["paths"]["/runs"]["post"]
    envelope = {"$ref": "#/components/schemas/ErrorEnvelope"}

    assert operation["operationId"] == "start_run"
    errors = {status for status in operation["responses"] if not status.startswith("2")}
    assert errors == {"401", "404", "422", "500"}
    for status in errors:
        content = operation["responses"][status]["content"]
        assert set(content) == {"application/json"}, status
        assert content["application/json"]["schema"] == envelope, status
    body = operation["requestBody"]["content"]["application/json"]["schema"]
    assert body == {"$ref": "#/components/schemas/StartRun"}


def test_본문_타입은_필드가_전부_필수이고_한_줄_설명을_든다() -> None:
    """요청 본문은 검증 스키마라 기본값이 있으면 계약이 "선택"이라 말하고 서버는 필수로 받는다
    (명세 검토의 프로브). 그래서 본문 모델에는 기본값 있는 필드를 두지 않는다."""
    schema = _app().openapi()["components"]["schemas"]["StartRun"]

    assert set(schema["required"]) == set(schema["properties"]) == {"agent", "request"}
    assert schema["additionalProperties"] is False
    assert "\n" not in schema["description"]


def test_승인_라우트가_지은_operation_id_와_봉투_에러_문서와_식별자_패턴을_든다() -> None:
    """생성 클라이언트의 함수 이름이 `operationId` 다(스토리 64). 에러는 전부 스트림이 시작되기 전의
    JSON 봉투다. 경로의 패턴은 관리의 `/traces/{run_id}` 와 같은 sdk 의 것이라, 목록에서 얻은
    식별자를 그대로 넘길 수 있다."""
    operation = _app().openapi()["paths"]["/runs/{run_id}/approval"]["post"]
    envelope = {"$ref": "#/components/schemas/ErrorEnvelope"}

    assert operation["operationId"] == "decide_approval"
    errors = {status for status in operation["responses"] if not status.startswith("2")}
    assert errors == {"401", "404", "409", "422", "500"}
    for status in errors:
        content = operation["responses"][status]["content"]
        assert set(content) == {"application/json"}, status
        assert content["application/json"]["schema"] == envelope, status
    run_id = next(p for p in operation["parameters"] if p["name"] == "run_id")
    assert run_id["in"] == "path"
    assert run_id["schema"]["pattern"] == RUN_ID_PATTERN
    body = operation["requestBody"]["content"]["application/json"]["schema"]
    assert body == {"$ref": "#/components/schemas/Decision"}


def test_409_는_승인_라우트에만_있다() -> None:
    """재개할 수 없는 상태를 만나는 것은 재개 라우트뿐이다. 관리는 실행을 일으키지 않는다."""
    paths = _app().openapi()["paths"]

    conflicting = [
        (path, method)
        for path, operations in paths.items()
        for method, operation in operations.items()
        if "409" in operation["responses"]
    ]

    assert conflicting == [("/runs/{run_id}/approval", "post")]


def test_결정_본문이_판별자_decision_의_이름_있는_유니온이고_허가와_거부가_섞이지_않는다() -> None:
    """생성 타입이 "사유 있는 허가"를 허용하지 않는다(스토리 65). 판별자에도 기본값이 없어
    `decision` 이 required 다 — 있으면 계약은 선택이라 말하고 서버는 판별자 없는 본문을 거부한다
    (명세 검토의 프로브). 멤버의 설명은 한 줄이다."""
    schemas = _app().openapi()["components"]["schemas"]
    decision = schemas["Decision"]

    assert _members(decision) == ["#/components/schemas/Approve", "#/components/schemas/Deny"]
    assert decision["discriminator"] == {
        "propertyName": "decision",
        "mapping": {
            "approve": "#/components/schemas/Approve",
            "deny": "#/components/schemas/Deny",
        },
    }
    approve, deny = schemas["Approve"], schemas["Deny"]
    assert set(approve["required"]) == set(approve["properties"]) == {"decision"}
    assert set(deny["required"]) == set(deny["properties"]) == {"decision", "reason"}
    assert approve["properties"]["decision"]["const"] == "approve"
    assert deny["properties"]["decision"]["const"] == "deny"
    for member in (approve, deny):
        assert member["additionalProperties"] is False
        assert "\n" not in member["description"]


def test_채널에는_승인_요청을_읽는_경로가_없다() -> None:
    """관찰은 관리의 일이다(ADR 0014). 시작한 쪽은 스트림 마지막의 `run_paused` 에서, 운영자는 관리
    API 의 트레이스 상세에서 무엇을 승인하는지 본다(스토리 25)."""
    paths = _app().openapi()["paths"]

    channel = {
        path: set(operations) for path, operations in paths.items() if path.startswith("/runs")
    }

    assert channel == {"/runs": {"post"}, "/runs/{run_id}/approval": {"post"}}


def test_계약의_제목과_설명이_관리와_채널을_함께_말한다() -> None:
    """옛 머리의 "읽기 전용이고 실행을 일으키지 않는다"는 채널이 붙는 순간 거짓이다(스토리 63)."""
    info = _app().openapi()["info"]

    assert "관리" in info["description"]
    assert "채널" in info["description"]
    assert "읽기 전용" not in info["title"] + info["description"]
    assert info["title"] != "Agent OS 관리 API"
