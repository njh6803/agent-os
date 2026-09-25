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
from collections.abc import AsyncGenerator, AsyncIterator, Callable, Iterator, Mapping, Sequence
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from datetime import UTC, datetime, timedelta

import anyio
import fastapi.routing
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from langchain_core.callbacks import AsyncCallbackManagerForLLMRun
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatResult
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
    TraceStore,
    run_status,
)
from agent_os.core.run import run
from agent_os.http.errors import INTERNAL_MESSAGE
from agent_os.sdk import (
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
    RunFinished,
    RunId,
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


# 등록된 것 전부. 이름이 곧 테스트가 부르는 에이전트다.
ECHO = _agent("echo")
ASKING = _agent("asking")
CHATTY = _agent("chatty")
ADDING = _agent("adding", mcp=["calc-server"])
GATED = _agent("gated", mcp=["calc-server"], requires_approval=["add"])
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
        manifests = (ECHO, ASKING, CHATTY, ADDING, GATED, GHOSTLY, LEAKY, UNLOADABLE)
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
    찬 것과 같다.
    """

    def __init__(self, *, broken_after: int | None = None) -> None:
        self.lines: list[str] = []
        self._events: list[Event] = []
        self._broken_after = broken_after

    def write(self, event: Event) -> None:
        if self._broken_after is not None and len(self._events) >= self._broken_after:
            raise OSError("트레이스를 쓸 수 없다: 디스크가 가득 찼다")
        self._events.append(event)
        self.lines.append(event.model_dump_json())

    def read(self, run_id: RunId) -> Trace | None:
        events = self.events_of(run_id)
        if not events:
            return None
        return Trace(run_id=run_id, schema_version="2", events=events)

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


# 채널 라우트가 붙기 전 계약의 컴포넌트 이름 전부. 이 티켓은 이름을 더하기만 하고 기존 이름을 바꾸지
# 않는다. 바뀌면 생성 클라이언트의 타입 이름이 바뀐다.
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


def test_스트림_항목이_이름_있는_Event_이고_TraceEvent_와_같은_멤버를_가리킨다() -> None:
    """생성 클라이언트가 `Streamitem Start Run` 같은 익명 유니온을 받지 않고(스토리 21), 같은
    이벤트를 두 타입으로 다루지 않는다(스토리 22). 기존 이름은 그대로이고 새 이름만 늘며 입력과
    출력으로 갈라진 이름이 없다."""
    document = _app().openapi()
    schemas = document["components"]["schemas"]
    ok = document["paths"]["/runs"]["post"]["responses"]["200"]
    item = ok["content"]["text/event-stream"]["itemSchema"]

    assert item["properties"]["data"]["contentSchema"] == {"$ref": "#/components/schemas/Event"}
    assert EXISTING_COMPONENTS <= set(schemas)
    assert set(schemas) - EXISTING_COMPONENTS == {"Event", "StartRun"}
    assert not any(name.endswith(("-Input", "-Output")) for name in schemas)
    assert not any("Streamitem" in name for name in schemas)
    trace_members = _members(schemas["TraceEvent"])
    assert _members(schemas["Event"]) == [
        member for member in trace_members if member != "#/components/schemas/UnknownEvent"
    ]


def test_스트림_항목_스키마는_FastAPI_의_정형_그대로_data_만_필수다() -> None:
    """광고를 그대로 둔다. 서버는 data 만 보내고 그것은 프레임 테스트가 고정한다(ADR 0014 의
    2026-09-24 이력)."""
    ok = _app().openapi()["paths"]["/runs"]["post"]["responses"]["200"]
    item = ok["content"]["text/event-stream"]["itemSchema"]

    assert item["required"] == ["data"]
    assert set(item["properties"]) == {"data", "event", "id", "retry"}


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


def test_계약의_제목과_설명이_관리와_채널을_함께_말한다() -> None:
    """옛 머리의 "읽기 전용이고 실행을 일으키지 않는다"는 채널이 붙는 순간 거짓이다(스토리 63)."""
    info = _app().openapi()["info"]

    assert "관리" in info["description"]
    assert "채널" in info["description"]
    assert "읽기 전용" not in info["title"] + info["description"]
    assert info["title"] != "Agent OS 관리 API"
