"""최종 사용자 경로. 사이트가 서명한 토큰으로 자기 실행을 시작하고 결정하고 구독한다(ADR 0023).

주 이음매는 채널 라우터 테스트와 같다 — `create_app()` 에 가짜 포트를 주입하고 httpx `ASGITransport`
로 밀며, 앱의 수명은 테스트 본문의 `async with` 로 연다(`.claude/rules/tests.md`). 토큰은 테스트가
`cryptography` 로 만든 키로 직접 서명한다(`tests/signing.py`). 둘째 구동자(같은 앱을 ASGI 로 직접
부르는 것)는 스트림의 수명에만 쓴다 — 도는 실행에 구독이 붙는 것과, 토큰이 만료돼도 열린 스트림이
끊기지 않는 것(`.claude/rules/http.md` 의 예외).

바깥 행동만 본다. 상태 코드와 봉투, 프레임의 `data` 와 `id`, 트레이스에 남은 이벤트, 서버 기록의 한
줄이다. 등록부의 자료 구조는 보지 않는다. 판정 순서는 core 테스트(`tests/core/test_run.py` 의
"결정의 주체" 절)가 고정하고 여기서는 면의 번역과 조립을 잰다.
"""

import asyncio
import io
import json
from collections.abc import AsyncGenerator, AsyncIterator, Callable, Mapping, Sequence
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from datetime import UTC, datetime, timedelta

import anyio
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient, Response
from langchain_core.callbacks import AsyncCallbackManagerForLLMRun
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatResult
from starlette.types import Message, Scope
from tests.signing import AUDIENCE, SigningKey, bearer, claims, new_key, sign

from agent_os.channel.http.end_user import END_USER_PREFIX
from agent_os.channel.http.items import FAILED_MESSAGE
from agent_os.core.ports import (
    ChatModel,
    Clock,
    Cursor,
    ManifestRow,
    PluginError,
    PluginKey,
    PluginSource,
    RunRow,
    RunStatus,
    ToolConnection,
    ToolResult,
    ToolSource,
    ToolSpec,
    Trace,
    TraceStore,
    UnknownEvent,
    WriteOutcome,
)
from agent_os.http.errors import INTERNAL_MESSAGE, NOT_FOUND_MESSAGE, UNAVAILABLE_MESSAGE
from agent_os.http.sites import Site, Sites
from agent_os.sdk import (
    AgentContext,
    AgentName,
    BaseAgent,
    ConversationSummarized,
    Event,
    Json,
    LlmCalled,
    McpServer,
    PluginKind,
    PluginManifest,
    PluginName,
    Principal,
    RunFinished,
    RunId,
    RunPaused,
    RunStarted,
    parse_manifest,
)
from agent_os.server import create_app

ADMIN_TOKEN = "adm1n-t0ken-that-only-tests-know"
CHANNEL_TOKEN = "channel-t0ken-that-only-tests-know"
CHANNEL = {"Authorization": f"Bearer {CHANNEL_TOKEN}"}
# 운영자 채널의 주체(`serve` 의 OS 사용자). `|` 가 없다.
OPERATOR = Principal("operator")
T0 = datetime(2026, 10, 5, 12, 0, tzinfo=UTC)

ISSUER = "https://shop.example"
OTHER_ISSUER = "https://other.example"
# 사이트마다 위젯을 넣은 페이지의 출처. CORS 의 허용 출처다.
ORIGIN = "https://www.shop.example"
OTHER_ORIGIN = "https://www.other.example"
KEY = new_key("k1")
OTHER_KEY = new_key()
ALICE = Principal(f"{ISSUER}|alice")
BOB = Principal(f"{ISSUER}|bob")

START = f"{END_USER_PREFIX}/runs"
DECISIONS = f"{END_USER_PREFIX}/runs/{{run_id}}/approval"
SUBSCRIPTION = f"{END_USER_PREFIX}/runs/{{run_id}}/subscription"

# 이 사이트가 여는 에이전트. `secret` 은 등록돼 있지만 목록 밖이고, `nope` 은 목록 안이지만 없다.
OPEN_AGENTS = frozenset(
    AgentName(name)
    for name in ("echo", "asking", "gated", "working", "silent", "unloadable", "nope")
)


def _site(agents: frozenset[AgentName] = OPEN_AGENTS) -> Sites:
    """사이트 둘. 이 파일의 최종 사용자는 대부분 첫째 사이트의 사람이다."""
    return Sites(
        (
            Site(
                issuer=ISSUER,
                audience=AUDIENCE,
                keys=(KEY.site_key(),),
                allowed_origins=(ORIGIN,),
                agents=agents,
            ),
            Site(
                issuer=OTHER_ISSUER,
                audience=AUDIENCE,
                keys=(OTHER_KEY.site_key(),),
                allowed_origins=(OTHER_ORIGIN,),
                agents=frozenset({AgentName("echo")}),
            ),
        )
    )


def _manifest(name: str, mcp: Sequence[str] = (), approval: Sequence[str] = ()) -> PluginManifest:
    def listed(names: Sequence[str]) -> str:
        return "[" + ", ".join(f'"{n}"' for n in names) + "]"

    return parse_manifest(
        f'schema_version = "1"\nkind = "agent"\nname = "{name}"\nversion = "0.1.0"\n'
        f'entrypoint = "agent:Agent"\nmcp = {listed(mcp)}\nrequires_approval = {listed(approval)}\n'
    )


CALC_SERVER = parse_manifest(
    'schema_version = "1"\nkind = "mcp"\nname = "calc-server"\nversion = "0.1.0"\n'
    '[server]\ncommand = "fake-server"\n'
)
# 도구가 돌려주는 글. 진행 항목에 실리면 안 된다.
TOOL_RESULT = "도구-결과-원문"
# 모델에 가는 프롬프트. 어떤 항목에도 실리면 안 된다.
PROMPT = "모델에-가는-프롬프트"


class EchoAgent:
    """모델도 도구도 쓰지 않는다. 요청을 되울리고 끝낸다."""

    async def run(self, request: str, ctx: AgentContext) -> AsyncIterator[Event]:
        yield RunFinished(run_id=ctx.run_id, ts=ctx.now(), output=f"echo:{request}")


class AskingAgent:
    """모델에게 한 번 묻고 그 답으로 끝낸다. 프롬프트는 요청이 아니라 고정 글이다."""

    async def run(self, request: str, ctx: AgentContext) -> AsyncIterator[Event]:
        yield RunFinished(run_id=ctx.run_id, ts=ctx.now(), output=await ctx.llm(PROMPT))


class ToolAgent:
    """add 를 직접 부르고 그 다음 끝낸다. 매니페스트가 add 를 승인 대상으로 두면 멈춘다."""

    async def run(self, request: str, ctx: AgentContext) -> AsyncIterator[Event]:
        await ctx.tool("add", a=2, b=3)
        yield RunFinished(run_id=ctx.run_id, ts=ctx.now(), output="다 했다")


class SilentAgent:
    """run_finished 없이 끝나 런타임이 run_failed 로 끝낸다. 그 실패의 원문은 밖으로 나가지
    않는다."""

    async def run(self, request: str, ctx: AgentContext) -> AsyncIterator[Event]:
        return
        yield RunFinished(run_id=ctx.run_id, ts=ctx.now(), output="닿지 않는다")


AGENTS: Mapping[str, BaseAgent] = {
    "echo": EchoAgent(),
    "asking": AskingAgent(),
    "gated": ToolAgent(),
    "working": ToolAgent(),
    "silent": SilentAgent(),
    "secret": EchoAgent(),
}
MANIFESTS = {
    "echo": _manifest("echo"),
    "asking": _manifest("asking"),
    "gated": _manifest("gated", mcp=["calc-server"], approval=["add"]),
    "working": _manifest("working", mcp=["calc-server"]),
    "silent": _manifest("silent"),
    "secret": _manifest("secret"),
    "unloadable": _manifest("unloadable"),
}
UNLOADABLE_REASON = "진입점을 불러올 수 없다: plugins/agents/unloadable/agent.py"


class FakePlugins:
    """이름별 매니페스트와 에이전트와 꺼진 집합. 부른 횟수를 세어 판정이 포트보다 먼저인지 본다."""

    def __init__(self) -> None:
        self.disabled: frozenset[PluginKey] = frozenset()
        self.calls = 0

    def read_manifest(self, kind: PluginKind, name: PluginName) -> PluginManifest | None:
        self.calls += 1
        if kind is PluginKind.MCP:
            return CALC_SERVER if name == "calc-server" else None
        return MANIFESTS.get(name)

    def list_manifests(self, kind: PluginKind) -> Sequence[ManifestRow]:
        raise NotImplementedError("최종 사용자 경로는 목록을 읽지 않는다")

    def load_agent(self, manifest: PluginManifest) -> BaseAgent:
        self.calls += 1
        if manifest.name == "unloadable":
            raise PluginError(UNLOADABLE_REASON)
        return AGENTS[manifest.name]

    def read_disabled(self) -> frozenset[PluginKey]:
        self.calls += 1
        return self.disabled

    def write_enabled(self, kind: PluginKind, name: PluginName, enabled: bool) -> WriteOutcome:
        raise NotImplementedError("최종 사용자 경로는 켜고 끄지 않는다")


class FakeTrace:
    """쓴 이벤트를 실행마다 들고 읽어 준다. `damaged` 의 실행은 마지막 줄 앞에 모르는 종류가
    낀다. 읽은 실행을 `reads` 에 쌓고, `on_read` 가 있으면 읽은 내용을 정한 뒤 그것을 부른다 —
    읽기와 그다음 걸음 사이에 실행이 움직이게 하는 지렛대다."""

    def __init__(self) -> None:
        self.events: list[Event] = []
        self.damaged: set[RunId] = set()
        self.reads: list[RunId] = []
        self.on_read: Callable[[], object] | None = None

    def write(self, event: Event) -> None:
        self.events.append(event)

    def read(self, run_id: RunId) -> Trace | None:
        self.reads.append(run_id)
        found = self._stored(run_id)
        if self.on_read is not None:
            self.on_read()
        return found

    def _stored(self, run_id: RunId) -> Trace | None:
        events = self.of(run_id)
        if not events:
            return None
        stored: tuple[Event | UnknownEvent, ...] = events
        if run_id in self.damaged:
            stored = (*events[:-1], UnknownEvent(raw='{"type": "from_the_future"}'), events[-1])
        return Trace(run_id=run_id, schema_version="3", events=stored)

    def list(
        self,
        *,
        status: RunStatus | None = None,
        limit: int | None = None,
        after: Cursor | None = None,
    ) -> Sequence[RunRow]:
        raise NotImplementedError("최종 사용자 경로는 목록을 읽지 않는다")

    def of(self, run_id: RunId) -> tuple[Event, ...]:
        return tuple(event for event in self.events if event.run_id == run_id)


class StepClock:
    """테스트가 옮기는 시계. 토큰의 시간 클레임도 실행의 시각도 이것으로 센다."""

    def __init__(self) -> None:
        self.at = T0
        self._issued = 0

    def now(self) -> datetime:
        return self.at

    def new_run_id(self) -> RunId:
        self._issued += 1
        return RunId(f"run-{self._issued}")


class FakeConnection:
    def __init__(self, servers: Mapping[PluginName, McpServer]) -> None:
        self._servers = servers

    def tools(self) -> Sequence[ToolSpec]:
        if not self._servers:
            return []
        schema: Mapping[str, Json] = {"type": "object", "properties": {"a": {}, "b": {}}}
        return [ToolSpec(name="add", description="더한다", input_schema=schema)]

    async def call(self, name: str, args: Mapping[str, Json]) -> ToolResult:
        return ToolResult(ok=True, content=TOOL_RESULT)


class ScopedTools:
    """MCP 어댑터처럼 연결을 anyio 취소 범위 안에서 연다."""

    @asynccontextmanager
    async def connect(
        self, servers: Mapping[PluginName, McpServer]
    ) -> AsyncGenerator[ToolConnection]:
        with anyio.CancelScope():
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


def _gated_model(answer: str = "답") -> GatedModel:
    return GatedModel(messages=iter([AIMessage(content=answer)]), gate=asyncio.Event())


def _app(
    *,
    plugins: PluginSource | None = None,
    trace: TraceStore | None = None,
    model: ChatModel | None = None,
    clock: Clock | None = None,
    stderr: io.StringIO | None = None,
    sites: Sites | None = None,
) -> FastAPI:
    """최종 사용자 경로가 선 앱 하나. 인자 타입이 가짜의 포트 적합성을 검증하는 자리다."""
    tools: ToolSource = ScopedTools()
    return create_app(
        plugins=plugins or FakePlugins(),
        trace=trace or FakeTrace(),
        model=model or GenericFakeChatModel(messages=iter([AIMessage(content="답")])),
        tools=tools,
        clock=clock or StepClock(),
        principal=OPERATOR,
        admin_token=ADMIN_TOKEN,
        channel_token=CHANNEL_TOKEN,
        sites=sites or _site(),
        stderr=stderr or io.StringIO(),
    )


def _lifespan(app: FastAPI) -> AbstractAsyncContextManager[object]:
    return app.router.lifespan_context(app)


@asynccontextmanager
async def _serving(app: FastAPI) -> AsyncGenerator[AsyncClient]:
    """앱의 수명을 연 채로 민다. 테스트 본문에서 `async with` 로 쓴다."""
    transport = ASGITransport(app=app)
    async with (
        _lifespan(app),
        AsyncClient(transport=transport, base_url="http://site.test") as client,
    ):
        yield client


def _token(subject: str = "alice", *, key: SigningKey = KEY, issuer: str = ISSUER) -> str:
    return sign(key, claims(issuer, subject, T0))


def _as(subject: str = "alice") -> dict[str, str]:
    return bearer(_token(subject))


def _frames(text: str) -> list[tuple[int, dict[str, object]]]:
    """프레임마다 `id` 와 `data`. 프레임은 `data:` 한 줄과 `id:` 한 줄뿐이다 — 다른 줄이 끼면
    실패한다.

    keepalive 주석은 프레임이 아니라 건너뛴다. `id` 와 `data` 의 순서는 FastAPI 가 정한다.
    """
    frames: list[tuple[int, dict[str, object]]] = []
    for block in text.split("\n\n"):
        if not block or block.startswith(":"):
            continue
        fields = dict(line.split(": ", 1) for line in block.split("\n"))
        assert set(fields) == {"data", "id"}, block
        payload: Json = json.loads(fields["data"])
        assert isinstance(payload, dict)
        frames.append((int(fields["id"]), dict(payload)))
    return frames


def _types(frames: Sequence[tuple[int, Mapping[str, object]]]) -> list[tuple[int, object]]:
    return [(index, item["type"]) for index, item in frames]


def _start(agent: str, request: str = "2+3?") -> dict[str, str]:
    return {"agent": agent, "request": request}


async def _until(condition: Callable[[], bool], *, within: float = 5.0) -> None:
    async with asyncio.timeout(within):
        while not condition():
            await asyncio.sleep(0.001)


def _write(trace: FakeTrace, run_id: str, *events: Event) -> None:
    for event in events:
        trace.write(event)


def _started(
    run_id: str, principal: Principal = ALICE, agent: str = "echo", previous: str | None = None
) -> RunStarted:
    return RunStarted(
        run_id=RunId(run_id),
        ts=T0,
        agent=AgentName(agent),
        request="2+3?",
        principal=principal,
        previous_run=None if previous is None else RunId(previous),
    )


def _llm(run_id: str) -> LlmCalled:
    return LlmCalled(
        run_id=RunId(run_id), ts=T0, model="m", input_tokens=1, output_tokens=1, prompt=PROMPT
    )


def _finished(run_id: str) -> RunFinished:
    return RunFinished(run_id=RunId(run_id), ts=T0, output="끝")


def _paused(run_id: str) -> RunPaused:
    return RunPaused(run_id=RunId(run_id), ts=T0, tool="add", args={"a": 2, "b": 3})


# 시작 — 서명한 주체로 실행을 일으켜 그 항목을 받는다


async def test_시작은_서명한_주체로_실행을_일으키고_프레임마다_data_와_id_두_줄이다() -> None:
    """주체는 `발급자|sub` 이고 시작 이벤트에 그대로 남는다(ADR 0023). 본문에서 받지 않는다.
    프레임의 `id` 는 그 항목의 근거인 트레이스 인덱스라 빈자리가 있다 — 모델 호출은 항목이 없다."""
    trace = FakeTrace()
    app = _app(trace=trace)

    async with _serving(app) as client:
        response = await client.post(START, json=_start("asking"), headers=_as())

    assert response.status_code == 200
    assert _types(_frames(response.text)) == [(0, "started"), (2, "finished")]
    started = trace.events[0]
    assert isinstance(started, RunStarted)
    assert started.principal == ALICE
    assert _frames(response.text)[0][1] == {"type": "started", "run_id": "run-1"}
    assert _frames(response.text)[1][1] == {"type": "finished", "output": "답"}


async def test_항목은_프롬프트도_도구_결과도_주체도_싣지_않는다() -> None:
    """그 바이트가 최종 사용자의 브라우저로 갈 이유가 없다(ADR 0023 의 신뢰 경계). 진행 항목은 도구
    이름과 성패만, 일시정지 항목은 도구와 인자 원문(무엇을 승인하는지)을 든다."""
    async with _serving(_app()) as client:
        working = await client.post(START, json=_start("working"), headers=_as())
        asking = await client.post(START, json=_start("asking"), headers=_as())
        gated = await client.post(START, json=_start("gated"), headers=_as())

    progress = _frames(working.text)[1][1]
    paused = _frames(gated.text)[-1][1]
    assert progress == {"type": "progress", "tool": "add", "ok": True}
    assert paused == {"type": "paused", "tool": "add", "args": {"a": 2, "b": 3}}
    for response in (working, asking, gated):
        assert TOOL_RESULT not in response.text
        assert PROMPT not in response.text
        assert "|alice" not in response.text


async def test_실패한_실행은_고정_문구와_실행_식별자의_실패_항목이고_원문을_싣지_않는다() -> None:
    """사용자에게 보여 줄 말과 운영자에게 알릴 식별자다. 원문은 트레이스에 있다."""
    trace = FakeTrace()

    async with _serving(_app(trace=trace)) as client:
        response = await client.post(START, json=_start("silent"), headers=_as())

    assert _frames(response.text)[-1] == (
        1,
        {"type": "failed", "message": FAILED_MESSAGE, "run_id": "run-1"},
    )
    assert "run_finished" not in response.text
    assert "run_finished" in trace.events[-1].model_dump_json()


async def test_목록_밖과_없는_에이전트는_메시지까지_같은_404이고_목록_밖은_포트에_닿지_않는다() -> (
    None
):
    """목록 밖과 없는 것이 같은 404 다(ADR 0017 이력). 둘이 갈리면 목록 밖의 에이전트가 있다는 것이
    드러난다. 실행 식별자를 만들기 전이라 트레이스가 없다."""
    plugins = FakePlugins()
    trace = FakeTrace()

    async with _serving(_app(plugins=plugins, trace=trace)) as client:
        outside = await client.post(START, json=_start("secret"), headers=_as())
        calls = plugins.calls
        missing = await client.post(START, json=_start("nope"), headers=_as())

    assert outside.status_code == missing.status_code == 404
    assert outside.json()["message"] == missing.json()["message"] == NOT_FOUND_MESSAGE
    assert calls == 0
    assert trace.events == []


async def test_꺼진_에이전트는_종류도_이름도_없는_고정_문구의_409다() -> None:
    """일시적인 것(409)과 영구적인 것(404)을 가른다. 꺼진 것이 무엇인지는 말하지 않는다(ADR 0017
    이력). 운영자 면은 같은 경우에 종류와 이름을 든다."""
    plugins = FakePlugins()
    plugins.disabled = frozenset({PluginKey(kind=PluginKind.AGENT, name=PluginName("echo"))})

    async with _serving(_app(plugins=plugins)) as client:
        end_user = await client.post(START, json=_start("echo"), headers=_as())
        operator = await client.post("/runs", json=_start("echo"), headers=CHANNEL)

    assert end_user.status_code == 409
    assert end_user.json()["code"] == "conflict"
    assert end_user.json()["message"] == UNAVAILABLE_MESSAGE
    assert "echo" not in end_user.text
    assert operator.status_code == 409
    assert "agent echo" in operator.json()["message"]


async def test_시작_경로의_구성_오류는_고정_문구의_500이고_원인은_서버_기록에만_있다() -> None:
    """실행을 가리키지 않는 경로라 숨길 존재가 없어 500 그대로다. `PluginError` 원문은 서버 기록에만
    남는다(ADR 0023)."""
    stderr = io.StringIO()

    async with _serving(_app(stderr=stderr)) as client:
        response = await client.post(START, json=_start("unloadable"), headers=_as())

    assert response.status_code == 500
    assert response.json()["message"] == INTERNAL_MESSAGE
    assert UNLOADABLE_REASON not in response.text
    assert UNLOADABLE_REASON in stderr.getvalue()
    assert response.headers["X-Request-Id"] in stderr.getvalue()


@pytest.mark.parametrize("extra", ["principal", "approver", "model"])
async def test_주체나_승인자나_모델을_본문에_실으면_422다(extra: str) -> None:
    """주체는 서명이 정한다. 보낸 쪽이 자기 값이 쓰였다고 믿게 두지 않는다(ADR 0015)."""
    async with _serving(_app()) as client:
        response = await client.post(
            START, json={**_start("echo"), extra: "https://shop.example|bob"}, headers=_as()
        )

    assert response.status_code == 422
    assert [v["field"] for v in response.json()["violations"]] == [f"body.{extra}"]


# 결정 — 서명한 주체가 자기 멈춘 실행에 결정을 낸다


async def _paused_run(client: AsyncClient, subject: str = "alice") -> str:
    """서명한 사람의 실행 하나를 승인 대상에서 멈춘다. 시작(0) 뒤 일시정지(1)다."""
    response = await client.post(START, json=_start("gated"), headers=_as(subject))
    frames = _frames(response.text)
    assert _types(frames) == [(0, "started"), (1, "paused")]
    run_id = frames[0][1]["run_id"]
    assert isinstance(run_id, str)
    return run_id


def _decide_path(run_id: str) -> str:
    return DECISIONS.format(run_id=run_id)


APPROVE = {"decision": "approve", "pause_index": 1}


async def test_결정의_응답은_결정_항목부터이고_id_가_pause_index_다음부터다() -> None:
    """결정 본문의 `pause_index` 는 일시정지 항목의 `id` 다(ADR 0023). 재개의 경계는 항목이 없다."""
    async with _serving(_app()) as client:
        run_id = await _paused_run(client)
        response = await client.post(_decide_path(run_id), json=APPROVE, headers=_as())

    assert response.status_code == 200
    assert _types(_frames(response.text)) == [(2, "decided"), (4, "progress"), (5, "finished")]
    assert _frames(response.text)[0][1] == {
        "type": "decided",
        "decision": "approve",
        "reason": None,
    }


async def test_거부의_결정_항목은_사유를_들고_승인자를_싣지_않는다() -> None:
    async with _serving(_app()) as client:
        run_id = await _paused_run(client)
        deny = {"decision": "deny", "reason": "  보내지 마  ", "pause_index": 1}
        response = await client.post(_decide_path(run_id), json=deny, headers=_as())

    assert _frames(response.text)[0][1] == {
        "type": "decided",
        "decision": "deny",
        "reason": "보내지 마",
    }
    assert "approver" not in response.text


async def test_남의_실행에_낸_결정은_없는_실행과_같은_404이고_운영자_채널은_409다() -> None:
    """남의 실행이 있다는 것조차 드러나지 않는다(스토리 10). 같은 실행에 운영자 채널은 409 이고
    메시지가 가른다 — 운영자도 최종 사용자의 실행에 결정하지 못한다(ADR 0023). 어느 쪽이든 아무것도
    쓰지 않는다."""
    trace = FakeTrace()

    async with _serving(_app(trace=trace)) as client:
        run_id = await _paused_run(client)
        before = list(trace.events)
        bob = await client.post(_decide_path(run_id), json=APPROVE, headers=_as("bob"))
        missing = await client.post(_decide_path("no-such-run"), json=APPROVE, headers=_as("bob"))
        operator = await client.post(f"/runs/{run_id}/approval", json=APPROVE, headers=CHANNEL)

    assert bob.status_code == missing.status_code == 404
    assert bob.json() | {"request_id": ""} == missing.json() | {"request_id": ""}
    assert bob.json()["message"] == NOT_FOUND_MESSAGE
    assert operator.status_code == 409
    assert trace.events == before


async def test_손상된_실행과_열_에이전트_밖의_실행도_같은_404이고_서버_기록은_원인을_든다() -> None:
    """손상된 남의 트레이스가 있다는 것도 숨긴다(ADR 0023 의 2026-10-05 이력). 원인은 서버 기록에
    원래 상태 코드와 함께 남아 운영자가 되살린다(스토리 52). 목록에서 뺀 에이전트의 멈춘 실행은 계속
    재개하지 못한다."""
    trace = FakeTrace()
    _write(trace, "damaged", _started("damaged", BOB, "gated"), _paused("damaged"))
    trace.damaged.add(RunId("damaged"))
    _write(trace, "hidden", _started("hidden", ALICE, "secret"), _paused("hidden"))
    stderr = io.StringIO()

    async with _serving(_app(trace=trace, stderr=stderr)) as client:
        damaged = await client.post(_decide_path("damaged"), json=APPROVE, headers=_as())
        hidden = await client.post(_decide_path("hidden"), json=APPROVE, headers=_as())

    for response in (damaged, hidden):
        assert response.status_code == 404
        assert response.json()["message"] == NOT_FOUND_MESSAGE
    assert "원래 상태 500 PluginError" in stderr.getvalue()
    assert "모르는 종류의 이벤트" in stderr.getvalue()
    assert len(trace.events) == 4


async def test_손상된_남의_실행에_운영자_채널은_500_원문이고_최종_사용자_면은_404_고정이다() -> (
    None
):
    """표가 면을 인자로 받는다(`failure_for`). 운영자 면은 바뀌지 않는다. 서버 기록은 둘 다 원인을
    든다."""
    trace = FakeTrace()
    _write(trace, "damaged", _started("damaged", BOB, "gated"), _paused("damaged"))
    trace.damaged.add(RunId("damaged"))
    stderr = io.StringIO()

    async with _serving(_app(trace=trace, stderr=stderr)) as client:
        operator = await client.post("/runs/damaged/approval", json=APPROVE, headers=CHANNEL)
        end_user = await client.post(_decide_path("damaged"), json=APPROVE, headers=_as())

    assert operator.status_code == 500
    assert "모르는 종류의 이벤트" in operator.json()["message"]
    assert end_user.status_code == 404
    assert end_user.json()["message"] == NOT_FOUND_MESSAGE
    lines = stderr.getvalue().splitlines()
    assert len(lines) == 2
    assert all("모르는 종류의 이벤트" in line for line in lines)


async def test_자기_실행의_상태는_409이고_메시지가_가른다() -> None:
    """자기 실행이라 숨길 것이 없다. 일시정지 아님과 지나간 자리는 메시지 그대로다."""
    async with _serving(_app()) as client:
        run_id = await _paused_run(client)
        stale = await client.post(
            _decide_path(run_id), json={"decision": "approve", "pause_index": 0}, headers=_as()
        )
        await client.post(_decide_path(run_id), json=APPROVE, headers=_as())
        done = await client.post(_decide_path(run_id), json=APPROVE, headers=_as())

    assert stale.status_code == 409
    assert "자리 0" in stale.json()["message"]
    assert done.status_code == 409
    assert "일시정지 상태가 아니" in done.json()["message"]


async def test_멈춘_실행의_에이전트가_꺼지면_결정은_고정_문구의_409다() -> None:
    plugins = FakePlugins()

    async with _serving(_app(plugins=plugins)) as client:
        run_id = await _paused_run(client)
        plugins.disabled = frozenset({PluginKey(kind=PluginKind.AGENT, name=PluginName("gated"))})
        response = await client.post(_decide_path(run_id), json=APPROVE, headers=_as())

    assert response.status_code == 409
    assert response.json()["message"] == UNAVAILABLE_MESSAGE


async def test_패턴을_어기는_실행_식별자는_422이고_트레이스를_읽지_않는다() -> None:
    trace = FakeTrace()

    async with _serving(_app(trace=trace)) as client:
        response = await client.post(_decide_path("..%2Fescape"), json=APPROVE, headers=_as())

    assert response.status_code == 422
    assert [v["field"] for v in response.json()["violations"]] == ["path.run_id"]
    assert trace.reads == []


# 구독 — 자기 실행에 다시 붙어 놓친 항목부터 받는다


def _subscribe_path(run_id: str) -> str:
    return SUBSCRIPTION.format(run_id=run_id)


async def _subscribe(client: AsyncClient, run_id: str, last: str | None = None) -> Response:
    headers = _as() | ({} if last is None else {"Last-Event-ID": last})
    return await client.get(_subscribe_path(run_id), headers=headers)


def _finished_trace() -> FakeTrace:
    """끝난 실행 하나. 시작(0), 모델 호출(1), 끝남(2)."""
    trace = FakeTrace()
    _write(trace, "done", _started("done"), _llm("done"), _finished("done"))
    return trace


@pytest.mark.parametrize(
    ("last", "expected"),
    [
        (None, [(0, "started"), (2, "finished")]),
        ("0", [(2, "finished")]),
        ("1", [(2, "finished")]),
        ("2", []),
    ],
    ids=["처음부터", "시작 다음부터", "빈자리 다음부터", "마지막 뒤 — 아무것도 없이 닫힘"],
)
async def test_끝난_실행의_구독은_Last_Event_ID_다음부터_보내고_닫는다(
    last: str | None, expected: list[tuple[int, str]]
) -> None:
    """이미 본 항목이 두 번 오지 않는다(스토리 6). 빈자리를 가리킨 값도 그다음부터다."""
    async with _serving(_app(trace=_finished_trace())) as client:
        response = await _subscribe(client, "done", last)

    assert response.status_code == 200
    assert _types(_frames(response.text)) == expected


async def test_시작_응답과_처음부터의_구독은_같은_프레임이다() -> None:
    """한 파서로 둘을 읽는다(스토리 31)."""
    async with _serving(_app()) as client:
        started = await client.post(START, json=_start("asking"), headers=_as())
        subscribed = await _subscribe(client, "run-1")

    assert _frames(subscribed.text) == _frames(started.text)


async def test_일시정지한_실행의_구독은_일시정지_항목까지_보내고_닫는다() -> None:
    trace = FakeTrace()
    _write(trace, "held", _started("held", agent="gated"), _paused("held"))

    async with _serving(_app(trace=trace)) as client:
        response = await _subscribe(client, "held")

    assert _types(_frames(response.text)) == [(0, "started"), (1, "paused")]


async def test_등록부에_없고_결말도_없으면_끝내지_못함_항목으로_닫히고_그_id_를_보내면_409다() -> (
    None
):
    """서버가 다시 떠 사라진 실행이다. 끝없이 기다리지 않는다(스토리 7). 끝내지 못함 항목의 `id` 는
    트레이스에 없는 자리라, 그것을 되돌려 보내면 서버의 기록보다 앞선 것을 봤다는 주장이다."""
    trace = FakeTrace()
    _write(trace, "lost", _started("lost", agent="asking"), _llm("lost"))

    async with _serving(_app(trace=trace)) as client:
        response = await _subscribe(client, "lost")
        again = await _subscribe(client, "lost", "2")

    assert _frames(response.text) == [
        (0, {"type": "started", "run_id": "lost"}),
        (2, {"type": "unfinished"}),
    ]
    assert again.status_code == 409
    assert again.json()["code"] == "conflict"


async def test_요약_이벤트는_항목이_없고_인덱스만_지난다() -> None:
    """요약은 런타임의 비용과 맥락 관리라 최종 사용자가 할 일이 없다. 위젯은 교환을 sessionStorage
    에 든다(ADR 0024). 요약 이벤트는 손으로 쓴다."""
    trace = FakeTrace()
    summary = ConversationSummarized(
        run_id=RunId("woven"),
        ts=T0,
        summary="앞 대화의 요약",
        last_covered_run=RunId("older"),
        model="m",
        input_tokens=1,
        output_tokens=1,
    )
    _write(trace, "woven", _started("woven", previous="older"), summary, _finished("woven"))

    async with _serving(_app(trace=trace)) as client:
        response = await _subscribe(client, "woven")

    assert _types(_frames(response.text)) == [(0, "started"), (2, "finished")]
    assert "앞 대화의 요약" not in response.text


@pytest.mark.parametrize(
    "value",
    ["abc", "-1", "1e3", " 1", "1234567890123"],
    ids=["글자", "음수", "지수", "공백", "13자리"],
)
async def test_형식에_맞지_않는_Last_Event_ID_는_422이고_그_헤더를_가리킨다(value: str) -> None:
    async with _serving(_app(trace=_finished_trace())) as client:
        response = await _subscribe(client, "done", value)

    assert response.status_code == 422
    assert [v["field"] for v in response.json()["violations"]] == ["header.last-event-id"]


async def test_범위_밖_Last_Event_ID_는_409이고_남의_실행에서는_404가_먼저다() -> None:
    """범위 판정은 자기 실행 읽기의 네 판정 뒤다. 그래야 남의 실행의 길이가 드러나지 않는다."""
    trace = _finished_trace()
    _write(trace, "bobs", _started("bobs", BOB), _finished("bobs"))

    async with _serving(_app(trace=trace)) as client:
        beyond = await _subscribe(client, "done", "4")
        foreign = await _subscribe(client, "bobs", "99")

    assert beyond.status_code == 409
    assert foreign.status_code == 404


async def test_남의_실행_손상된_실행_열_에이전트_밖의_실행은_모두_같은_404다() -> None:
    """모르는 종류가 섞인 트레이스도 손상이라 404 다. 넷의 메시지가 같다."""
    trace = FakeTrace()
    _write(trace, "bobs", _started("bobs", BOB), _finished("bobs"))
    _write(trace, "damaged", _started("damaged"), _finished("damaged"))
    trace.damaged.add(RunId("damaged"))
    _write(trace, "hidden", _started("hidden", agent="secret"), _finished("hidden"))

    async with _serving(_app(trace=trace)) as client:
        responses = [
            await _subscribe(client, run_id) for run_id in ("bobs", "damaged", "hidden", "nothing")
        ]

    for response in responses:
        assert response.status_code == 404
        assert response.json()["message"] == NOT_FOUND_MESSAGE


async def test_다른_사이트의_같은_sub_는_다른_주체라_구독하지_못한다() -> None:
    """주체는 발급자와 `sub` 를 묶은 이름이다. 고정 접두사나 `sub` 그대로면 겹친다(ADR 0023)."""
    trace = _finished_trace()

    async with _serving(_app(trace=trace)) as client:
        other = await client.get(
            _subscribe_path("done"),
            headers=bearer(_token(key=OTHER_KEY, issuer=OTHER_ISSUER)),
        )

    assert other.status_code == 404


# 둘째 구동자 — 도는 실행에 붙는 구독과 열린 스트림의 수명


class _Wire:
    """같은 앱을 ASGI 로 직접 부르는 쪽. 받은 메시지를 순서대로 적는다.

    receive 는 본문을 한 번 주고 그 뒤로는 테스트가 떠날 때까지 기다린다.
    """

    def __init__(self, body: Mapping[str, Json] | None = None) -> None:
        self.sent: list[Message] = []
        self._body = b"" if body is None else json.dumps(body).encode()
        self._requested = False
        self._gone = asyncio.Event()

    async def receive(self) -> Message:
        if not self._requested:
            self._requested = True
            return {"type": "http.request", "body": self._body, "more_body": False}
        await self._gone.wait()
        return {"type": "http.disconnect"}

    async def send(self, message: Message) -> None:
        self.sent.append(message)

    def leave(self) -> None:
        self._gone.set()

    def status(self) -> int | None:
        for message in self.sent:
            if message["type"] == "http.response.start":
                status = message["status"]
                return status if isinstance(status, int) else None
        return None

    def frames(self) -> list[tuple[int, dict[str, object]]]:
        chunks = [
            bytes(message["body"])
            for message in self.sent
            if message["type"] == "http.response.body"
        ]
        return _frames(b"".join(chunks).decode())


def _scope(method: str, path: str, token: str, last_event_id: str | None = None) -> Scope:
    headers = [
        (b"authorization", f"Bearer {token}".encode()),
        (b"content-type", b"application/json"),
    ]
    if last_event_id is not None:
        headers.append((b"last-event-id", last_event_id.encode()))
    return {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "root_path": "",
        "query_string": b"",
        "headers": headers,
        "client": ("127.0.0.1", 50000),
        "server": ("site.test", 80),
    }


def _call(app: FastAPI, scope: Scope, wire: _Wire) -> asyncio.Task[None]:
    """앱을 ASGI 로 한 번 부르는 태스크."""
    return asyncio.create_task(app(scope, wire.receive, wire.send))


async def test_도는_실행에_붙은_구독은_그_뒤_항목을_생기는_대로_받는다() -> None:
    """도는 실행이면 트레이스의 나머지를 보낸 뒤 실황에서 오는 것을 결말까지 보낸다(ADR 0023).
    모델이 문 앞에 선 동안 붙고, 문을 연 뒤 결말까지 받는다. `Last-Event-ID` 가 트레이스의
    마지막이면 트레이스에서 보낼 것이 없어 실황만 온다."""
    model = _gated_model()
    app = _app(model=model)
    token = _token()
    starting = _Wire(_start("asking"))
    whole = _Wire()
    tail = _Wire()

    async with _lifespan(app):
        start = _call(app, _scope("POST", START, token), starting)
        await _until(lambda: starting.frames() != [])
        from_start = _call(app, _scope("GET", _subscribe_path("run-1"), token), whole)
        from_last = _call(app, _scope("GET", _subscribe_path("run-1"), token, "0"), tail)
        await _until(lambda: whole.frames() != [] and tail.status() == 200)
        assert _types(whole.frames()) == [(0, "started")]
        assert tail.frames() == []
        model.gate.set()
        async with asyncio.timeout(5):
            await start
            await from_start
            await from_last

    assert _types(whole.frames()) == [(0, "started"), (2, "finished")]
    assert whole.frames() == starting.frames()
    assert _types(tail.frames()) == [(2, "finished")]


async def test_구독이_트레이스를_읽는_바로_그때_실행이_움직여도_빠짐도_중복도_없다() -> None:
    """트레이스 읽기와 등록부 보기 사이에 await 가 없다는 것을 잰다. 트레이스를 읽는 바로 그
    자리에서 모델의 문을 연다 — 둘 사이에 await 가 하나라도 끼면 실행이 그 틈에 결말까지 가 등록부를
    떠나고, 구독은 앞서 읽은 트레이스(시작 하나)와 빈 등록부를 보고 끝내지 못함으로 닫는다. await 가
    없으면 실행은 구독이 실황에 붙은 뒤에야 움직여 그 뒤의 이벤트가 실황으로 온다(ADR 0023)."""
    model = _gated_model()
    trace = FakeTrace()
    app = _app(model=model, trace=trace)
    token = _token()
    starting = _Wire(_start("asking"))
    subscribing = _Wire()

    async with _lifespan(app):
        start = _call(app, _scope("POST", START, token), starting)
        await _until(lambda: starting.frames() != [])
        trace.on_read = model.gate.set
        subscribe = _call(app, _scope("GET", _subscribe_path("run-1"), token), subscribing)
        async with asyncio.timeout(5):
            await start
            await subscribe

    assert _types(subscribing.frames()) == [(0, "started"), (2, "finished")]
    assert subscribing.frames() == starting.frames()


async def test_구독이_떠나도_실행은_끝까지_가고_다른_받는_쪽은_결말까지_받는다() -> None:
    """받는 쪽이 떠나 구독의 제너레이터가 닫히면 붙은 실황도 닫힌다(`_Subscription.frames`). 떠난
    쪽 때문에 실행이 서거나 같은 실행의 다른 받는 쪽이 끊기지 않는다(ADR 0014)."""
    model = _gated_model()
    trace = FakeTrace()
    app = _app(model=model, trace=trace)
    token = _token()
    starting = _Wire(_start("asking"))
    leaving = _Wire()

    async with _lifespan(app):
        start = _call(app, _scope("POST", START, token), starting)
        await _until(lambda: starting.frames() != [])
        subscribe = _call(app, _scope("GET", _subscribe_path("run-1"), token), leaving)
        await _until(lambda: leaving.frames() != [])
        leaving.leave()
        async with asyncio.timeout(5):
            await subscribe
        model.gate.set()
        async with asyncio.timeout(5):
            await start

    assert _types(leaving.frames()) == [(0, "started")]
    assert _types(starting.frames()) == [(0, "started"), (2, "finished")]
    assert trace.events[-1].type == "run_finished"


async def test_토큰이_만료돼도_열린_스트림은_끊기지_않고_같은_토큰의_다음_요청은_401이다() -> None:
    """토큰은 요청 하나를 여는 것이고 연결은 그 요청이다(스토리 15). 시계는 토큰의 시간 클레임을
    세는 그것이다 — 검증 자리가 시계 포트를 받아서 이것을 잴 수 있다(티켓 01의 결정)."""
    model = _gated_model()
    clock = StepClock()
    app = _app(model=model, clock=clock)
    token = _token()
    wire = _Wire(_start("asking"))

    async with _lifespan(app):
        call = asyncio.create_task(app(_scope("POST", START, token), wire.receive, wire.send))
        await _until(lambda: wire.frames() != [])
        clock.at = T0 + timedelta(seconds=300 + 31)
        model.gate.set()
        async with asyncio.timeout(5):
            await call
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://site.test") as c:
            later = await c.get(_subscribe_path("run-1"), headers=bearer(token))

    assert _types(wire.frames()) == [(0, "started"), (2, "finished")]
    assert later.status_code == 401


# CORS — 허용 출처의 페이지가 성공 응답도 에러 봉투도 읽는다(ADR 0023, end-user-channel 티켓 04).
# 미들웨어의 자리와 범위(preflight, 허용 밖 출처, 접두사 밖, 사이트 둘, 예기치 않은 500)는
# `tests/test_server.py` 의 CORS 절이 잰다. 여기서는 진짜 라우트가 낸 상태 코드마다 헤더가 붙는지
# 본다.


async def test_허용_출처의_요청은_200과_에러_응답_모두에_CORS_헤더_셋을_받는다() -> None:
    """페이지 안 위젯이 에러 봉투를 읽는다(스토리 24). 401 은 인증이, 404·409·422·500 은 표가 낸다 —
    CORS 가 인증과 라우터를 감싸므로 어느 것에나 붙는다. 노출 헤더가 추적 식별자를 들어 위젯이 그
    값을 운영자에게 건넬 수 있다."""
    origin = {"Origin": ORIGIN}

    async with _serving(_app()) as client:
        ok = await client.post(START, json=_start("echo"), headers=_as() | origin)
        refused = await client.post(START, json=_start("echo"), headers=origin)
        missing = await client.post(START, json=_start("secret"), headers=_as() | origin)
        run_id = await _paused_run(client)
        stale = await client.post(
            _decide_path(run_id),
            json={"decision": "approve", "pause_index": 0},
            headers=_as() | origin,
        )
        invalid = await client.post(
            START, json={**_start("echo"), "model": "x"}, headers=_as() | origin
        )
        broken = await client.post(START, json=_start("unloadable"), headers=_as() | origin)

    responses = {200: ok, 401: refused, 404: missing, 409: stale, 422: invalid, 500: broken}
    for status, response in responses.items():
        assert response.status_code == status
        assert response.headers["access-control-allow-origin"] == ORIGIN, status
        assert response.headers["vary"] == "Origin", status
        assert response.headers["access-control-expose-headers"] == "Retry-After, X-Request-Id"


# 계약 — 새 접두사의 경로 셋과 항목 유니온


END_USER_OPERATIONS = (
    (START, "post", "start_end_user_run"),
    (DECISIONS, "post", "decide_end_user_approval"),
    (SUBSCRIPTION, "get", "subscribe_end_user_run"),
)
ITEMS = {
    "StartedItem": "started",
    "ProgressItem": "progress",
    "PausedItem": "paused",
    "DecidedItem": "decided",
    "FinishedItem": "finished",
    "FailedItem": "failed",
    "UnfinishedItem": "unfinished",
}


def test_경로_셋이_지은_operation_id_와_봉투_에러_문서와_항목_유니온을_든다() -> None:
    """에러는 스트림이 시작되기 전의 JSON 봉투다. 429 는 `Retry-After` 를 문서에 든다(ADR 0023)."""
    paths = _app().openapi()["paths"]
    envelope = {"$ref": "#/components/schemas/ErrorEnvelope"}

    for path, method, operation_id in END_USER_OPERATIONS:
        operation = paths[path][method]
        assert operation["operationId"] == operation_id, path
        errors = {status for status in operation["responses"] if not status.startswith("2")}
        assert errors == {"401", "404", "409", "422", "429", "500"}, path
        for status in errors:
            content = operation["responses"][status]["content"]
            assert content == {"application/json": {"schema": envelope}}, (path, status)
        assert set(operation["responses"]["429"]["headers"]) == {"Retry-After"}, path
        item = operation["responses"]["200"]["content"]["text/event-stream"]["itemSchema"]
        assert item["properties"]["data"]["contentSchema"] == {
            "$ref": "#/components/schemas/EndUserItem"
        }, path


def test_시작의_422_설명은_요청_글자_수의_단위와_기본값을_적는다() -> None:
    """요청 글자 수의 값은 사이트 파일이 원천이고 계약에는 단위와 기본값이 글자로 적힌다(스토리
    13·35). 위젯 개발자가 계약에서 읽는다. 결정과 구독은 공유 설명 그대로다."""
    paths = _app().openapi()["paths"]

    start = paths[START]["post"]["responses"]["422"]["description"]
    decide = paths[DECISIONS]["post"]["responses"]["422"]["description"]

    assert "코드 포인트" in start
    assert "20,000" in start
    assert decide == "요청의 형식이 올바르지 않다"


def test_항목_유니온은_판별자_type_의_이름_있는_컴포넌트이고_멤버가_일곱이다() -> None:
    """생성 타입에서 판별자 술어를 만든다(스토리 28). 멤버 이름은 기존 컴포넌트와 겹치지 않는다."""
    schemas = _app().openapi()["components"]["schemas"]
    union = schemas["EndUserItem"]

    assert union["discriminator"] == {
        "propertyName": "type",
        "mapping": {value: f"#/components/schemas/{name}" for name, value in ITEMS.items()},
    }
    assert {member["$ref"] for member in union["oneOf"]} == {
        f"#/components/schemas/{name}" for name in ITEMS
    }
    for name, value in ITEMS.items():
        member = schemas[name]
        assert member["properties"]["type"]["const"] == value, name
        assert set(member["required"]) == set(member["properties"]), name
        assert member["additionalProperties"] is False, name
        assert "\n" not in member["description"], name


def _references(document: Json) -> set[str]:
    """문서 안의 `$ref` 가 가리키는 컴포넌트 이름 전부."""
    found: set[str] = set()
    if isinstance(document, dict):
        for key, value in document.items():
            if key == "$ref" and isinstance(value, str):
                found.add(value.rsplit("/", 1)[-1])
            found |= _references(value)
    elif isinstance(document, list):
        for value in document:
            found |= _references(value)
    return found


def test_참조되지_않는_컴포넌트는_ServerSentEvent_하나다() -> None:
    """프레임에 `id` 를 싣는 모양(`SkipJsonSchema[ServerSentEvent]`)의 대가로 FastAPI 가 남긴다.
    후처리로 지우지 않는다. 다른 고아가 조용히 늘면 여기서 빨개지고, FastAPI 가 이것을 고치면 그때
    집합을 비운다."""
    document = _app().openapi()
    schemas = document["components"]["schemas"]

    assert set(schemas) - _references(document) == {"ServerSentEvent"}


def test_구독은_Last_Event_ID_헤더를_선택으로_받고_형식을_계약에_싣는다() -> None:
    operation = _app().openapi()["paths"][SUBSCRIPTION]["get"]

    (header,) = [p for p in operation["parameters"] if p["in"] == "header"]
    assert header["name"] == "last-event-id"
    assert header["required"] is False
    assert header["schema"]["anyOf"][0]["pattern"] == r"^[0-9]{1,12}$"
