"""주 이음매. create_app() 이 만든 앱에 ASGI 로 요청을 넣고 바깥 행동만 단언한다.

바탕으로 재는 것은 셋이다 — 모든 라우트가 보호를 켜지 않아도 기본으로 막힌다는 것, 에러가 언제나
같은 봉투로 나간다는 것, 인증 없이 경계 밖으로 나가는 응답이 /health 하나뿐이라는 것. 그 위에
데이터 라우트가 하나씩 붙는다. 플러그인 둘과 트레이스 목록과 상세가 파일 끝에 있다.

가짜 포트는 상속하지 않고 시그니처로 만족하며 픽스처가 포트 타입으로 annotate 한다. 그 한 줄이
포트 적합성이 검증되는 자리다. 네트워크도 디스크도 타지 않는다.
"""

import asyncio
import base64
import contextlib
import dataclasses
import inspect
import io
import json
import time
from collections.abc import AsyncIterator, Iterable, Mapping, Sequence
from datetime import UTC, datetime, timedelta, timezone
from typing import Literal, get_type_hints

import httpx
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from pydantic import TypeAdapter
from starlette.exceptions import HTTPException as StarletteHTTPException
from tests.signing import (
    AUDIENCE,
    SigningKey,
    bearer,
    claims,
    hs256_with,
    new_key,
    sign,
    unsigned,
)

from agent_os import server as server_module
from agent_os.admin import http as admin_http
from agent_os.admin import traces as admin_traces
from agent_os.admin.http import Health
from agent_os.admin.traces import CURSOR_PATTERN
from agent_os.channel.http.end_user import END_USER_PREFIX
from agent_os.channel.http.router import CHANNEL_PREFIX
from agent_os.core.ports import (
    DEFAULT_LIMIT,
    MAX_LIMIT,
    Absent,
    Clock,
    Cursor,
    Disabled,
    ManifestRow,
    NotResumable,
    PluginError,
    PluginKey,
    PluginSource,
    RunRow,
    RunStatus,
    RunSummary,
    ToolConnection,
    ToolSource,
    Trace,
    TraceSchemaVersion,
    TraceStore,
    UnknownEvent,
    UnreadableManifest,
    UnreadableTrace,
    WriteOutcome,
    cursor_of,
    order_key,
)
from agent_os.http.auth import PUBLIC_PATHS
from agent_os.http.errors import INTERNAL_MESSAGE, REQUEST_ID_HEADER, UNAUTHORIZED_MESSAGE
from agent_os.http.sites import Site, Sites
from agent_os.sdk import (
    PLUGIN_NAME_PATTERN,
    RUN_ID_PATTERN,
    AgentName,
    BaseAgent,
    Event,
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
    ToolCall,
    is_run_id,
    parse_manifest,
)
from agent_os.server import create_app

# 관리 토큰. 이 파일의 대부분이 관리 라우트를 밀어서 이름을 짧게 둔다.
TOKEN = "t0ken-that-only-tests-know"
BEARER = {"Authorization": f"Bearer {TOKEN}"}
CHANNEL_TOKEN = "channel-t0ken-that-only-tests-know"
CHANNEL_BEARER = {"Authorization": f"Bearer {CHANNEL_TOKEN}"}
# allowlist 밖이면서 라우트가 없는 경로. 토큰이 없으면 401 이고 있으면 404 라는 것이 곧 미들웨어가
# 라우팅보다 먼저라는 사실이다. 데이터 라우트가 붙어도 이 경로는 문서에 없어 그 대조가 유지된다.
GUARDED = "/unrouted"
# 채널 쪽의 같은 대조. `/runs` 와 `/runs/{run_id}/approval` 을 쓰지 않는 이유는 라우트가 있어 채널
# 토큰의 답이 404 가 아니기 때문이다. 이 경로는 그 둘 어느 것에도 맞지 않는다 — 승인 라우트는
# `verbatim` 이 슬래시까지 잡아도 `/approval` 로 끝나야 맞는다. 실행 식별자 하나로 끝나는
# 라우트(`/runs/{run_id}`)를 더하는 티켓은 이 경로가 그 라우트에 닿는지 다시 본다.
CHANNEL_GUARDED = "/runs/unrouted"


CALC = parse_manifest(
    """
schema_version = "1"
kind = "agent"
name = "calc"
version = "0.1.0"
entrypoint = "agent:Calc"
mcp = ["everything"]
requires_approval = ["add"]
"""
)
EVERYTHING = parse_manifest(
    """
schema_version = "1"
kind = "mcp"
name = "everything"
version = "0.1.0"

[server]
command = "npx"
args = ["-y", "@modelcontextprotocol/server-everything"]
"""
)
SUMMARIZE = parse_manifest(
    """
schema_version = "1"
kind = "skill"
name = "summarize"
version = "0.1.0"
"""
)
SONNET = parse_manifest(
    """
schema_version = "1"
kind = "model"
name = "sonnet"
version = "0.1.0"
"""
)
BROKEN = UnreadableManifest(
    kind=PluginKind.AGENT,
    name="broken",
    reason="매니페스트를 읽을 수 없다: plugins/agents/broken/plugin.toml",
)


class FakePlugins:
    """디렉터리 대신 행 목록과 꺼진 집합을 든다. 부른 횟수를 세어 검증이 포트보다 먼저 끝나는지
    본다.

    읽히지 않는 행에는 어댑터와 같은 비대칭으로 답한다 — 목록에서는 표지, 단건에서는 PluginError.
    켜짐도 어댑터의 규칙으로 답한다 — 쓰기는 부재 판정이 먼저이고, 운영자 파일의 손상(`corrupt`)이
    그다음이며, 바뀌는 것이 없어도 성공이다. 쓰기는 읽고, 디스크 시간(`disk_seconds`)을 들인 뒤
    쓴다. 즉시 끝나면 스레드풀에서 도는 동기 라우트도 스레드 타이밍에 따라 초록으로 지나간다
    (채널 테스트의 선례). 어댑터가 실제로 이렇게 답한다는 것은 `tests/adapters/test_filesystem.py`
    가 잰다.
    """

    def __init__(
        self,
        rows: Sequence[ManifestRow] = (),
        *,
        disabled: Iterable[PluginKey] = (),
        corrupt: str | None = None,
        unwritable: str | None = None,
        disk_seconds: float = 0.0,
    ) -> None:
        self._rows = tuple(rows)
        self.disabled = frozenset(disabled)
        self._corrupt = corrupt
        self._unwritable = unwritable
        self._disk_seconds = disk_seconds
        self.calls = 0
        self.disabled_reads = 0
        self.writes: list[tuple[PluginKey, bool]] = []

    def read_manifest(self, kind: PluginKind, name: PluginName) -> PluginManifest | None:
        self.calls += 1
        for row in self._rows:
            if row.kind is not kind or row.name != name:
                continue
            if isinstance(row, UnreadableManifest):
                raise PluginError(row.reason)
            return row
        return None

    def list_manifests(self, kind: PluginKind) -> Sequence[ManifestRow]:
        self.calls += 1
        return tuple(row for row in self._rows if row.kind is kind)

    def load_agent(self, manifest: PluginManifest) -> BaseAgent:
        raise NotImplementedError("관리는 실행을 일으키지 않는다")

    def read_disabled(self) -> frozenset[PluginKey]:
        self.calls += 1
        self.disabled_reads += 1
        if self._corrupt is not None:
            raise PluginError(self._corrupt)
        return self.disabled

    def write_enabled(self, kind: PluginKind, name: PluginName, enabled: bool) -> WriteOutcome:
        self.calls += 1
        if not any(row.kind is kind and row.name == name for row in self._rows):
            return "absent"
        if self._corrupt is not None:
            raise PluginError(self._corrupt)
        if self._unwritable is not None:
            raise PluginError(self._unwritable)
        current = self.disabled
        time.sleep(self._disk_seconds)
        key = PluginKey(kind=kind, name=name)
        self.writes.append((key, enabled))
        self.disabled = current - {key} if enabled else current | {key}
        return "applied"


T0 = datetime(2026, 9, 23, 12, 0, tzinfo=UTC)


def _summary(
    run_id: str,
    status: RunStatus,
    *,
    started: timedelta,
    last: timedelta,
    schema_version: TraceSchemaVersion = "2",
) -> RunSummary:
    return RunSummary(
        run_id=RunId(run_id),
        status=status,
        schema_version=schema_version,
        started_at=T0 + started,
        last_at=T0 + last,
        agent=AgentName("calc"),
        principal=Principal("alice"),
    )


# 상태 넷과 형식 1 과 표지 하나. 시작 시각은 전부 다르고 가장 오래된 것이 형식 1 이다. 멈춘 실행의
# 마지막 시각은 뒤에 시작한 실행들보다 오래됐다 — 방치를 알아보는 길이 그 시각뿐이다(스토리 12).
PAUSED = _summary("7c1e2d9a", "paused", started=timedelta(minutes=0), last=timedelta(minutes=1))
FINISHED = _summary("a41f0b33", "finished", started=timedelta(minutes=2), last=timedelta(minutes=3))
FAILED = _summary("5d0c8e71", "failed", started=timedelta(minutes=4), last=timedelta(minutes=4))
UNFINISHED = _summary(
    "e93b6f02", "unfinished", started=timedelta(minutes=6), last=timedelta(minutes=7)
)
LEGACY = _summary(
    "0b7d4c18", "finished", started=-timedelta(days=1), last=-timedelta(days=1), schema_version="1"
)
UNREADABLE = UnreadableTrace(
    run_id=RunId("c2f85a90"), reason="traces/c2f85a90.jsonl: 헤더를 읽을 수 없다"
)
NEWEST_FIRST = (UNFINISHED, FAILED, FINISHED, PAUSED, LEGACY, UNREADABLE)

SUMMARY_FIELDS = {
    "run_id",
    "status",
    "schema_version",
    "started_at",
    "last_at",
    "agent",
    "principal",
}

# 멈춘 실행 하나의 트레이스. 가운데에 이 런타임이 모르는 종류가 한 줄 끼어 있다 — 재개는 그런 줄이
# 하나라도 있으면 거부되므로 화면이 그 줄을 보지 못하면 재개 불가의 원인을 못 찾는다. 그 줄의 원문도
# `type` 을 들고 있어, 원문을 펼쳐 판별자를 얹으면 덮어쓰게 된다는 것을 이 데이터가 드러낸다.
FUTURE_LINE = '{"type":"run_rewound","run_id":"7c1e2d9a","ts":"2026-09-23T12:00:30Z","to":"llm-1"}'
PAUSED_EVENTS: tuple[Event | UnknownEvent, ...] = (
    RunStarted(
        run_id=PAUSED.run_id,
        ts=T0,
        agent=AgentName("calc"),
        request="2+3?",
        principal=Principal("alice"),
    ),
    LlmCalled(
        run_id=PAUSED.run_id,
        ts=T0 + timedelta(seconds=10),
        model="claude",
        input_tokens=12,
        output_tokens=5,
        prompt="2+3?",
        tool_calls=(ToolCall(id="call-1", name="add", args={"a": 2, "b": 3}),),
    ),
    UnknownEvent(raw=FUTURE_LINE),
    RunPaused(
        run_id=PAUSED.run_id, ts=T0 + timedelta(minutes=1), tool="add", args={"a": 2, "b": 3}
    ),
)
PAUSED_TRACE = Trace(run_id=PAUSED.run_id, schema_version="2", events=PAUSED_EVENTS)
LEGACY_TRACE = Trace(
    run_id=LEGACY.run_id,
    schema_version="1",
    events=(
        RunStarted(
            run_id=LEGACY.run_id,
            ts=LEGACY.started_at,
            agent=AgentName("calc"),
            request="2+2?",
            principal=Principal("alice"),
        ),
        RunFinished(run_id=LEGACY.run_id, ts=LEGACY.last_at, output="4"),
    ),
)


@dataclasses.dataclass(frozen=True)
class ListCall:
    status: RunStatus | None
    limit: int | None
    after: Cursor | None


class FakeTrace:
    """디렉터리 대신 행 목록과 트레이스들을 들고 어댑터의 규칙으로 답한다. 받은 인자를 적어 둔다.

    목록의 규칙은 상태로 거르고 정렬 키 역순으로 세운 뒤 커서 다음부터 limit 만큼 자르는 것이고,
    키는 core 의 `cursor_of`·`order_key` 로 만든다. 가짜가 정렬을 따로 지으면 HTTP 가 되돌려 준
    커서가 어댑터와 같은 키를 가리키는지 재지 못한다. 단건은 읽히지 않는 행에 어댑터와 같은
    비대칭으로 답한다 — 목록에서는 표지, 단건에서는 PluginError. 어댑터가 실제로 이렇게 답한다는
    것은 `tests/adapters/test_jsonl.py` 가 잰다. 쓰기는 불리면 그 자체가 결함이라 터뜨린다.
    """

    def __init__(self, rows: Sequence[RunRow] = (), traces: Sequence[Trace] = ()) -> None:
        self.rows: Sequence[RunRow] = tuple(rows)
        self.traces: Mapping[RunId, Trace] = {trace.run_id: trace for trace in traces}
        self.calls: list[ListCall] = []
        self.reads: list[RunId] = []

    def write(self, event: Event) -> None:
        raise NotImplementedError("관리는 읽기 전용이다")

    def read(self, run_id: RunId) -> Trace | None:
        self.reads.append(run_id)
        for row in self.rows:
            if isinstance(row, UnreadableTrace) and row.run_id == run_id:
                raise PluginError(row.reason)
        return self.traces.get(run_id)

    def list(
        self,
        *,
        status: RunStatus | None = None,
        limit: int | None = None,
        after: Cursor | None = None,
    ) -> Sequence[RunRow]:
        self.calls.append(ListCall(status=status, limit=limit, after=after))
        rows = [
            row
            for row in self.rows
            if status is None or (isinstance(row, RunSummary) and row.status == status)
        ]
        rows.sort(key=lambda row: order_key(cursor_of(row)), reverse=True)
        if after is not None:
            rows = [row for row in rows if order_key(cursor_of(row)) < order_key(after)]
        return tuple(rows[: DEFAULT_LIMIT if limit is None else limit])


class IdleTools:
    """이 파일은 관리를 민다. 관리는 실행을 일으키지 않으므로 불리면 그 자체가 결함이다.
    채널이 이 포트를 쓰는 것은 `tests/channel/http/test_router.py` 가 잰다."""

    def connect(
        self, servers: Mapping[PluginName, McpServer]
    ) -> contextlib.AbstractAsyncContextManager[ToolConnection]:
        raise NotImplementedError("관리는 실행을 일으키지 않는다")


class IdleClock:
    """불리면 그 자체가 결함이다. 이유는 `IdleTools` 와 같다."""

    def now(self) -> datetime:
        raise NotImplementedError("관리는 실행을 일으키지 않는다")

    def new_run_id(self) -> RunId:
        raise NotImplementedError("관리는 실행을 일으키지 않는다")


def _admin_app(
    *,
    plugins: PluginSource,
    trace: TraceStore,
    stderr: io.StringIO,
    admin_token: str = TOKEN,
    channel_token: str = CHANNEL_TOKEN,
    sites: Sites | None = None,
    clock: Clock | None = None,
) -> FastAPI:
    """관리를 미는 앱. 채널의 포트 셋은 불리지 않는 자리표시자다. 인자 타입이 포트 적합성을
    검증하는 자리다. 서명 토큰을 재는 테스트만 사이트 목록과 토큰의 시간을 셀 시계를 준다."""
    tools: ToolSource = IdleTools()
    idle: Clock = IdleClock()
    return create_app(
        plugins=plugins,
        trace=trace,
        model=GenericFakeChatModel(messages=iter(())),
        tools=tools,
        clock=clock or idle,
        principal=Principal("alice"),
        admin_token=admin_token,
        channel_token=channel_token,
        sites=sites or Sites(),
        stderr=stderr,
    )


@pytest.fixture
def stderr() -> io.StringIO:
    """서버 표준 에러. 실패 하나가 남기는 한 줄을 테스트가 읽는 자리다."""
    return io.StringIO()


EVERYTHING_KEY = PluginKey(kind=PluginKind.MCP, name=PluginName("everything"))
BROKEN_KEY = PluginKey(kind=PluginKind.AGENT, name=PluginName("broken"))
CALC_KEY = PluginKey(kind=PluginKind.AGENT, name=PluginName("calc"))


@pytest.fixture
def plugins() -> FakePlugins:
    """종류 넷에 하나 이상씩과 읽을 수 없는 것 하나. 행 순서는 어댑터처럼 종류 안에서 이름순이다.
    mcp 하나가 꺼져 있다."""
    return FakePlugins(
        rows=(BROKEN, CALC, EVERYTHING, SUMMARIZE, SONNET), disabled={EVERYTHING_KEY}
    )


@pytest.fixture
def traces() -> FakeTrace:
    """상태 넷과 형식 1 과 표지 하나. 순서를 섞어 넣어 정렬이 포트의 일임을 드러낸다. 단건으로
    읽히는 것은 멈춘 실행과 형식 1 실행 둘이다."""
    return FakeTrace(
        rows=(UNREADABLE, PAUSED, UNFINISHED, LEGACY, FAILED, FINISHED),
        traces=(PAUSED_TRACE, LEGACY_TRACE),
    )


@pytest.fixture
def app(stderr: io.StringIO, plugins: FakePlugins, traces: FakeTrace) -> FastAPI:
    return _admin_app(plugins=plugins, trace=traces, stderr=stderr)


@pytest.fixture
async def client(app: FastAPI) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://admin.test") as opened:
        yield opened


def _documented_paths(app: FastAPI) -> tuple[str, ...]:
    """앱이 아는 경로 전부. 라우트를 더하면 전수 검사의 대상이 저절로 는다."""
    paths = app.openapi().get("paths", {})
    return tuple(str(path) for path in paths)


def _route_that_raises(app: FastAPI, path: str, error: Exception) -> None:
    """예외를 상태 코드로 옮기는 표를 미는 지렛대.

    표의 갈래 중에는 진짜 라우트로 일으키기 어려운 것이 있다(예기치 않은 예외). 이 라우트는 표가
    실제로 도는지 보기 위한 것이고, 진짜 라우트가 닿는 갈래는 그 라우트로 다시 잰다.
    """

    @app.get(path)
    def _raise() -> Health:
        raise error


async def test_헬스체크만_토큰_없이_답한다(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_인증_없이_지나가는_경로의_목록은_헬스체크_하나다() -> None:
    """목록이 문서 없이 자라는 것이 fail-open 으로 돌아가는 길이다(ADR 0011)."""
    assert PUBLIC_PATHS == frozenset({"/health"})


async def test_헬스체크_응답이_내부_구성을_싣지_않는다(client: AsyncClient) -> None:
    """인증 없이 경계 밖으로 나가는 유일한 응답이다(스토리 42)."""
    body = (await client.get("/health")).json()

    assert list(body) == ["status"]


async def test_allowlist_밖의_모든_경로가_토큰_없이_401이다(
    app: FastAPI, client: AsyncClient
) -> None:
    """라우트를 더하고 보호를 잊으면 이 테스트가 깨진다. fail-closed 라 벨트이지 전부가 아니다."""
    documented = _documented_paths(app)
    guarded = [path for path in documented if path not in PUBLIC_PATHS]
    assert guarded, "allowlist 밖 경로가 없으면 이 전수 검사는 401 을 한 번도 재지 않는다"

    for path in documented:
        response = await client.get(path)
        expected = 200 if path in PUBLIC_PATHS else 401
        assert response.status_code == expected, path


async def test_문서에_없는_경로도_토큰_없이는_404가_아니라_401이다(client: AsyncClient) -> None:
    """미들웨어가 라우팅보다 먼저다. 인증 없는 요청이 어떤 경로가 실재하는지 알 수 없다."""
    assert (await client.get(GUARDED)).status_code == 401


async def test_다른_출처의_preflight_는_토큰이_없으면_관리_경로도_채널_경로도_401이다(
    client: AsyncClient,
) -> None:
    """관리 화면의 중계는 `OPTIONS` 를 그대로 상류로 넘긴다(ADR 0019). 관리 경로와 채널 경로에는
    CORS 가 없고 그것이 곧 차단이라는 것은 미들웨어가 메서드를 가르지 않는다는 데 기댄다(ADR 0011
    이력, 스토리 65). 허용 헤더도 없다. CORS 가 preflight 에 답하는 것은 최종 사용자 접두사뿐이고
    (ADR 0023), 그 범위는 아래 CORS 절의 전수 검사가 잰다."""
    preflight = {
        "Origin": "http://evil.example",
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "authorization",
    }

    for path in ("/plugins", CHANNEL_PREFIX):
        response = await client.options(path, headers=preflight)
        assert response.status_code == 401, path
        assert "access-control-allow-origin" not in response.headers, path


async def test_틀린_토큰도_빈_토큰도_401이다(client: AsyncClient) -> None:
    """헤더 부재를 빈 문자열로 다루는 구현과 겹치면 그 자체가 fail-open 이다."""
    headers: tuple[dict[str, str], ...] = (
        {},
        {"Authorization": "Bearer wrong-token"},
        {"Authorization": "Bearer"},
        {"Authorization": "Bearer "},
        {"Authorization": ""},
        {"Authorization": TOKEN},
        {"Authorization": f"Basic {TOKEN}"},
    )

    for header in headers:
        response = await client.get(GUARDED, headers=header)
        assert response.status_code == 401, header


async def test_비ASCII_토큰도_500이_아니라_401이다(client: AsyncClient) -> None:
    """원격 입력이 상태 코드를 바꾸지 못한다. `hmac` 의 str 비교는 non-ASCII 에서 TypeError 다.

    바이트로 미는 이유는 헤더가 원래 바이트이기 때문이다. 클라이언트 라이브러리가 ASCII 만
    보내 주더라도 경계에 실제로 닿는 것은 임의의 바이트다.
    """
    headers = {b"Authorization": "Bearer 토큰이-아닌-값".encode()}

    response = await client.get(GUARDED, headers=headers)

    assert response.status_code == 401


async def test_허용되지_않는_메서드도_봉투이고_어휘_안에_있다(client: AsyncClient) -> None:
    """405 는 프레임워크가 내는 것이라 표에 없다. 어휘를 늘리지 않으려고 계열로 접는다."""
    response = await client.post("/health")

    assert response.status_code == 405
    assert response.json()["code"] == "invalid_request"


async def test_405가_어떤_메서드를_쓸_수_있는지_알려_준다(client: AsyncClient) -> None:
    """RFC 9110 이 405 에 Allow 를 요구한다. 라우터가 붙인 헤더를 봉투가 버리면 안 된다."""
    response = await client.post("/health")

    assert "GET" in response.headers["Allow"]


async def test_401이_어떤_인증을_쓰는지_알려_준다(client: AsyncClient) -> None:
    """RFC 9110 이 401 에 WWW-Authenticate 를 요구한다. 방식을 알리는 것은 노출이 아니다 —
    401 자체가 이미 인증이 필요하다고 말한다."""
    response = await client.get(GUARDED)

    assert response.headers["WWW-Authenticate"] == "Bearer"


async def test_맞는_토큰은_미들웨어를_지나_라우팅까지_간다(client: AsyncClient) -> None:
    """401 이 아니라 404 라는 것이 곧 지나갔다는 뜻이다. 이 경로에는 라우트가 없다."""
    assert (await client.get(GUARDED, headers=BEARER)).status_code == 404


@pytest.mark.parametrize(
    ("admin_token", "channel_token"),
    [("", CHANNEL_TOKEN), (TOKEN, ""), (TOKEN, TOKEN)],
    ids=["빈 관리 토큰", "빈 채널 토큰", "같은 두 토큰"],
)
def test_빈_토큰이나_같은_두_토큰으로는_앱을_세울_수_없다(
    stderr: io.StringIO, admin_token: str, channel_token: str
) -> None:
    """토큰 없이 도는 면을 기본값으로 남기지 않고, 두 토큰이 같으면 분리가 무효다(ADR 0015).
    진단과 종료 코드로 운영자에게 말하는 것은 `serve` 의 몫이다."""
    with pytest.raises(ValueError):
        _admin_app(
            plugins=FakePlugins(),
            trace=FakeTrace(),
            stderr=stderr,
            admin_token=admin_token,
            channel_token=channel_token,
        )


# 채널 토큰 — `/runs` 아래는 채널 토큰만, 그 밖은 관리 토큰만 연다(티켓 02, ADR 0015)


type _Surface = Literal["end_user", "channel", "admin"]


def _surface_of(path: str) -> _Surface:
    """전수 검사가 세 면을 가르는 기준이고 경로 조각 단위다. 미들웨어의 규칙을 여기서 다시 적은
    것이라, 둘이 같은 규칙이라는 것은 `/runsx` 와 `/end-userx` 대조가 잰다. 접두사는 채널이 소유한
    그것이다. 둘로만 가르면 최종 사용자 경로가 관리로 분류되어, 새 접두사에서 관리 토큰이 401 인지가
    재어지지 않은 채 초록이다(end-user-channel 명세 검토가 짚었다)."""
    prefixes: tuple[tuple[str, _Surface], ...] = (
        (END_USER_PREFIX, "end_user"),
        (CHANNEL_PREFIX, "channel"),
    )
    for prefix, surface in prefixes:
        if path == prefix or path.startswith(f"{prefix}/"):
            return surface
    return "admin"


async def test_채널_경로는_채널_토큰만_열고_관리_토큰으로는_401이다(client: AsyncClient) -> None:
    """트레이스를 읽는 권한이 비용과 부작용이 있는 실행을 일으키는 권한이 되지 않는다(스토리 51).
    채널 토큰의 404 가 곧 미들웨어를 지나 라우팅까지 갔다는 뜻이다."""
    nothing = await client.get(CHANNEL_GUARDED)
    admin = await client.get(CHANNEL_GUARDED, headers=BEARER)
    channel = await client.get(CHANNEL_GUARDED, headers=CHANNEL_BEARER)

    assert nothing.status_code == 401
    assert admin.status_code == 401
    assert channel.status_code == 404


async def test_접두사_그_자체도_채널이다(client: AsyncClient) -> None:
    """`/runs` 에는 03 이 라우트를 붙여 채널 토큰의 답이 404 에서 405 로 바뀐다. 그래서 채널
    토큰으로는 미들웨어를 지났다는 것(401 이 아니다)까지만 본다."""
    admin = await client.get("/runs", headers=BEARER)
    channel = await client.get("/runs", headers=CHANNEL_BEARER)

    assert admin.status_code == 401
    assert channel.status_code != 401


async def test_접두사를_문자열로만_공유하는_경로는_채널이_아니다(client: AsyncClient) -> None:
    """접두사 비교는 경로 조각 단위다(스토리 54). 문자열 비교였다면 이 대조가 뒤집힌다."""
    channel = await client.get("/runsx", headers=CHANNEL_BEARER)
    admin = await client.get("/runsx", headers=BEARER)

    assert channel.status_code == 401
    assert admin.status_code == 404


def _documented_operations(app: FastAPI) -> tuple[tuple[str, str], ...]:
    """앱이 아는 (메서드, 경로) 전부. 라우트를 더하면 자격 세 방향의 전수 검사가 저절로 는다."""
    paths = app.openapi().get("paths", {})
    return tuple(
        (str(method).upper(), str(path))
        for path, operations in paths.items()
        for method in operations
    )


async def test_자격은_자기_면만_연다_세_면마다_다른_두_자격은_401이다(stderr: io.StringIO) -> None:
    """트레이스를 읽는 권한이 실행을 일으키는 권한이 되지 않고(스토리 51), 위젯에 준 토큰으로 모든
    실행의 트레이스를 읽지 못한다(스토리 52). 운영자의 두 공유 토큰은 최종 사용자 접두사를 열지
    못하고 사이트가 서명한 토큰은 그 밖을 열지 못한다(ADR 0023, end-user-channel 스토리 69). 서명
    토큰은 최종 사용자 접두사에서는 통하는 토큰이다 — 사이트 목록이 비어 아무것도 열지 못하는
    토큰으로 재면 이 방향은 비어 있어도 초록이다. 방향마다 열거가 비면 그 방향은 아무것도 재지
    않는다."""
    app = _signed_app(stderr)
    signed = bearer(sign(KEY_A1, _good()))
    operations = [
        (method, path) for method, path in _documented_operations(app) if path not in PUBLIC_PATHS
    ]
    end_user = [op for op in operations if _surface_of(op[1]) == "end_user"]
    channel = [op for op in operations if _surface_of(op[1]) == "channel"]
    admin = [op for op in operations if _surface_of(op[1]) == "admin"]
    assert end_user, "최종 사용자 경로가 없으면 공유 토큰 두 방향은 401 을 한 번도 재지 않는다"
    assert channel, "채널 경로가 없으면 관리 토큰과 서명 토큰 쪽 방향은 비어 있다"
    assert admin, "관리 경로가 없으면 채널 토큰과 서명 토큰 쪽 방향은 비어 있다"

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://all.test") as client:
        assert (await client.get(END_USER_GUARDED, headers=signed)).status_code == 404
        for (method, path), wrong in [
            *((op, header) for op in end_user for header in (BEARER, CHANNEL_BEARER)),
            *((op, header) for op in channel for header in (BEARER, signed)),
            *((op, header) for op in admin for header in (CHANNEL_BEARER, signed)),
        ]:
            response = await client.request(method, path, headers=wrong)
            assert response.status_code == 401, (method, path, wrong)


async def test_채널_토큰도_응답에도_서버_기록에도_나타나지_않는다(
    client: AsyncClient, stderr: io.StringIO
) -> None:
    """원칙 V. 틀린 면에 내민 토큰도, 맞는 면에 내민 토큰도 되울리지 않는다."""
    wrong_surface = await client.get(GUARDED, headers=CHANNEL_BEARER)
    admin_on_channel = await client.get(CHANNEL_GUARDED, headers=BEARER)
    accepted = await client.get(CHANNEL_GUARDED, headers=CHANNEL_BEARER)

    for response in (wrong_surface, admin_on_channel, accepted):
        assert CHANNEL_TOKEN not in response.text
        assert TOKEN not in response.text
    assert CHANNEL_TOKEN not in stderr.getvalue()
    assert TOKEN not in stderr.getvalue()


# 서명 토큰 — 최종 사용자 접두사 아래는 사이트가 서명한 토큰만 연다(ADR 0023, end-user-channel
# 티켓 01). 검증을 지났는지는 라우트가 없는 경로의 404(지났다)와 401(막혔다)로 본다. 받아들인 토큰의
# 주체가 실행에 드는 것은 최종 사용자 경로의 테스트(`tests/channel/http/test_end_user.py`)가 잰다.

# 최종 사용자 접두사 아래이면서 라우트가 없는 경로.
END_USER_GUARDED = f"{END_USER_PREFIX}/unrouted"
NOW = datetime(2026, 10, 5, 12, 0, tzinfo=UTC)
ISSUER_A = "https://a.example"
ISSUER_B = "https://b.example"
# 사이트마다 위젯을 넣은 페이지의 출처 하나. CORS 의 허용 출처다.
ORIGIN_A = "https://www.a.example"
ORIGIN_B = "https://www.b.example"
# 사이트 A 는 키를 바꾸는 중이라 kid 둘이고, 사이트 B 는 kid 없는 키 하나다.
KEY_A1 = new_key("k1")
KEY_A2 = new_key("k2")
KEY_B = new_key()
SITES = Sites(
    (
        Site(
            issuer=ISSUER_A,
            audience=AUDIENCE,
            keys=(KEY_A1.site_key(), KEY_A2.site_key()),
            allowed_origins=(ORIGIN_A,),
            agents=frozenset(),
        ),
        Site(
            issuer=ISSUER_B,
            audience=AUDIENCE,
            keys=(KEY_B.site_key(),),
            allowed_origins=(ORIGIN_B,),
            agents=frozenset(),
        ),
    )
)


class StillClock:
    """테스트가 정한 시각에 서 있는 시계. 서명 토큰의 시간 클레임을 이것으로 센다.

    관리는 실행을 일으키지 않으므로 실행 식별자를 달라고 하면 그 자체가 결함이다."""

    def __init__(self, at: datetime) -> None:
        self.at = at

    def now(self) -> datetime:
        return self.at

    def new_run_id(self) -> RunId:
        raise NotImplementedError("관리는 실행을 일으키지 않는다")


def _signed_app(stderr: io.StringIO, clock: Clock | None = None) -> FastAPI:
    """사이트 둘을 받아들이는 앱. 시계는 주지 않으면 `NOW` 에 서 있다."""
    return _admin_app(
        plugins=FakePlugins(),
        trace=FakeTrace(),
        stderr=stderr,
        sites=SITES,
        clock=clock or StillClock(NOW),
    )


def _good(**changed: object) -> dict[str, object]:
    """사이트 A 의 사용자 alice 가 지금 받은 토큰의 클레임. 바꿀 것만 준다. `None` 은 뺀다."""
    payload = claims(ISSUER_A, "alice", NOW) | changed
    return {name: value for name, value in payload.items() if value is not None}


async def _gate(app: FastAPI, token: str) -> httpx.Response:
    """라우트가 없는 최종 사용자 경로에 그 토큰을 내민다. 404 면 지났고 401 이면 막혔다."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://site.test") as c:
        return await c.get(END_USER_GUARDED, headers=bearer(token))


_ISSUED = int(NOW.timestamp())

# 거절 열다섯. 이름, 토큰, 서버 기록이 원인으로 드는 말.
_REFUSED: tuple[tuple[str, str, str], ...] = (
    ("서명 틀림", sign(KEY_B, _good(), kid="k1"), "서명"),
    ("만료", sign(KEY_A1, _good(iat=_ISSUED - 400, exp=_ISSUED - 30)), "만료"),
    ("미래 iat", sign(KEY_A1, _good(iat=_ISSUED + 31, exp=_ISSUED + 331)), "iat"),
    ("수명 601초", sign(KEY_A1, _good(exp=_ISSUED + 601)), "수명"),
    ("iat 없음", sign(KEY_A1, _good(iat=None)), "MissingRequiredClaimError"),
    ("sub 없음", sign(KEY_A1, _good(sub=None)), "MissingRequiredClaimError"),
    ("aud 없음", sign(KEY_A1, _good(aud=None)), "MissingRequiredClaimError"),
    ("exp 없음", sign(KEY_A1, _good(exp=None)), "MissingRequiredClaimError"),
    ("iss 없음", sign(KEY_A1, _good(iss=None)), "발급자"),
    ("다른 대상", sign(KEY_A1, _good(aud="someone-else")), "InvalidAudienceError"),
    ("모르는 발급자", sign(KEY_A1, _good(iss="https://c.example")), "모르는 발급자"),
    ("모르는 kid", sign(KEY_A1, _good(), kid="k9"), "kid"),
    ("alg none", unsigned(_good()), "InvalidAlgorithmError"),
    ("HS256", hs256_with(KEY_A1.public_pem().encode(), _good()), "InvalidAlgorithmError"),
    ("형식 깨짐", "not-a-jwt", "형식"),
)


@pytest.mark.parametrize(
    ("token", "reason"),
    [(token, reason) for _, token, reason in _REFUSED],
    ids=[name for name, _, _ in _REFUSED],
)
async def test_서명_토큰의_거절은_전부_같은_401_고정_문구이고_원인은_서버_기록에만_있다(
    token: str, reason: str, stderr: io.StringIO
) -> None:
    """만료인지 서명인지 밖으로 말하면 토큰을 다듬어 가며 단계를 알아낼 수 있다(스토리 51). 운영자는
    서버 기록에서 원인을 본다. 토큰 값은 응답에도 기록에도 싣지 않는다(원칙 V)."""
    response = await _gate(_signed_app(stderr), token)

    assert response.status_code == 401
    assert response.json()["message"] == UNAUTHORIZED_MESSAGE
    assert response.headers["WWW-Authenticate"] == "Bearer"
    assert reason in stderr.getvalue()
    assert token not in response.text
    assert token not in stderr.getvalue()


def test_거절_사례는_열다섯이고_서로_다른_토큰이다() -> None:
    """사례가 줄거나 둘이 같은 토큰이 되면 그 거절은 재어지지 않는다."""
    assert len(_REFUSED) == 15
    assert len({token for _, token, _ in _REFUSED}) == 15


@pytest.mark.parametrize(
    "token",
    [
        sign(KEY_A1, _good()),
        sign(KEY_A2, _good()),
        sign(SigningKey(KEY_A2.private, None), _good()),
        sign(KEY_B, _good(iss=ISSUER_B)),
        sign(KEY_A1, _good(exp=_ISSUED + 600)),
        sign(KEY_A1, _good(aud=[AUDIENCE, "other"])),
    ],
    ids=[
        "옛 키(k1)",
        "새 키(k2)",
        "kid 없이 키 둘인 사이트 — 차례로 시도",
        "kid 없는 키 하나인 사이트",
        "수명이 꼭 600초",
        "대상 배열에 우리가 든다",
    ],
)
async def test_받아들이는_토큰은_라우팅까지_간다(token: str, stderr: io.StringIO) -> None:
    """키를 바꾸는 동안 옛 키와 새 키가 함께 받아들여진다(스토리 19). 키가 하나인 작은 사이트는
    kid 없이 서명한다(스토리 20). 수명이 꼭 600초인 토큰은 경계 안이다 — 경계는 명세가 정했다."""
    response = await _gate(_signed_app(stderr), token)

    assert response.status_code == 404


@pytest.mark.parametrize(
    "token",
    [
        sign(SigningKey(KEY_A1.private, None), _good(iss=ISSUER_B)),
        sign(KEY_B, _good()),
        sign(KEY_B, _good(), kid="k2"),
    ],
    ids=["A 의 키로 B 를 주장", "B 의 키로 A 를 주장(kid 없음)", "B 의 키로 A 를 주장(A 의 kid)"],
)
async def test_다른_사이트의_키로_서명한_토큰은_401이다(token: str, stderr: io.StringIO) -> None:
    """발급자로 고른 항목의 키로만 검증한다. 한 사이트가 다른 사이트의 발급자를 주장해 그 사용자로
    서명할 수 없다(스토리 21, ADR 0023)."""
    assert (await _gate(_signed_app(stderr), token)).status_code == 401


@pytest.mark.parametrize(
    "token",
    [sign(KEY_A1, _good(sub="")), sign(KEY_A1, _good(sub=7))],
    ids=["빈 sub", "숫자 sub"],
)
async def test_sub_는_비지_않은_문자열이어야_한다(token: str, stderr: io.StringIO) -> None:
    """주체 이름 `발급자|sub` 의 뒤가 빈 것도, 수를 글자로 바꿔 받는 것도 막는다."""
    assert (await _gate(_signed_app(stderr), token)).status_code == 401


async def test_수명은_정수로_자르지_않은_값으로_센다(stderr: io.StringIO) -> None:
    """NumericDate 는 소수일 수 있다. 자른 값으로 세면 600.5초가 600초로 읽혀 경계를 넘은 토큰이
    지나간다. 만료와 미래는 라이브러리처럼 자른 값으로 견준다."""
    token = sign(KEY_A1, _good(exp=_ISSUED + 600.5))

    response = await _gate(_signed_app(stderr), token)

    assert response.status_code == 401
    assert "수명 600.5초" in stderr.getvalue()


@pytest.mark.parametrize(
    ("changed", "expected"),
    [
        ({"iat": _ISSUED - 400, "exp": _ISSUED - 29}, 404),
        ({"iat": _ISSUED - 400, "exp": _ISSUED - 30}, 401),
        ({"iat": _ISSUED + 30, "exp": _ISSUED + 330}, 404),
        ({"iat": _ISSUED + 31, "exp": _ISSUED + 331}, 401),
        ({"nbf": _ISSUED + 30}, 404),
        ({"nbf": _ISSUED + 31}, 401),
    ],
    ids=[
        "만료 29초 지남",
        "만료 30초 지남",
        "iat 가 30초 뒤",
        "iat 가 31초 뒤",
        "nbf 가 30초 뒤",
        "nbf 가 31초 뒤",
    ],
)
async def test_시계_여유_30초가_exp_iat_nbf_에_같이_걸린다(
    changed: dict[str, object], expected: int, stderr: io.StringIO
) -> None:
    """라이브러리의 시간 비교식(PyJWT 2.14.0 `api_jwt.py`, 코드를 읽었다)을 검증 자리가 시계
    포트로 옮긴다. 만료는 `exp <= 지금 - 여유`, 미래는 `> 지금 + 여유` 다."""
    response = await _gate(_signed_app(stderr), sign(KEY_A1, _good(**changed)))

    assert response.status_code == expected


async def test_토큰의_시간은_앱이_받은_시계로_센다(stderr: io.StringIO) -> None:
    """같은 토큰이 시계를 돌리면 만료된다. 라이브러리가 벽시계로 세면 가짜 시계로는 만료를 잴 수
    없고, 열린 스트림이 만료 뒤에도 끊기지 않는 것(스토리 15)도 잴 수 없다(티켓 01의 결정)."""
    clock = StillClock(NOW)
    app = _signed_app(stderr, clock)
    token = sign(KEY_A1, _good())

    before = await _gate(app, token)
    clock.at = NOW + timedelta(seconds=300 + 30)
    after = await _gate(app, token)

    assert before.status_code == 404
    assert after.status_code == 401
    assert "만료" in stderr.getvalue()


async def test_사이트가_없으면_서명_토큰이_전부_401이다(
    client: AsyncClient, stderr: io.StringIO
) -> None:
    """사이트 파일을 주지 않은 배치. 최종 사용자 경로는 서되 받아들일 사이트가 없다(스토리 41).
    모르는 발급자에서 끝나 시계에 닿지 않는다 — 이 앱의 시계는 불리면 터진다."""
    response = await client.get(END_USER_GUARDED, headers=bearer(sign(KEY_A1, _good())))

    assert response.status_code == 401
    assert "모르는 발급자" in stderr.getvalue()


async def test_접두사를_문자열로만_공유하는_경로는_최종_사용자_면이_아니다(
    stderr: io.StringIO,
) -> None:
    """접두사 비교는 경로 조각 단위다. `/end-userx` 는 관리 토큰의 면이다."""
    app = _signed_app(stderr)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://site.test") as c:
        signed = await c.get("/end-userx", headers=bearer(sign(KEY_A1, _good())))
        admin = await c.get("/end-userx", headers=BEARER)

    assert signed.status_code == 401
    assert admin.status_code == 404


# CORS — 최종 사용자 접두사에만 걸고 에러 응답에도 붙는다(ADR 0023, end-user-channel 티켓 04).
# 브라우저가 허용 출처의 페이지에서 보낸 요청만 응답을 읽는다. 서버는 막지 않고 허용 밖 출처에
# `Allow-Origin` 을 내지 않을 뿐이다. 여기서는 미들웨어의 자리와 범위를 잰다. 라우트가 낸 상태
# 코드 전부에 헤더가 붙는 것은 최종 사용자 경로의 테스트(`tests/channel/http/test_end_user.py`)가
# 잰다.

ALLOW_ORIGIN = "access-control-allow-origin"
# 허용 출처의 응답에 붙는 셋. 허용 밖 출처에는 `Allow-Origin` 이 없다.
CORS_HEADERS = (ALLOW_ORIGIN, "vary", "access-control-expose-headers")
EXPOSED = "Retry-After, X-Request-Id"
EVIL_ORIGIN = "https://evil.example"


def _preflight(
    origin: str | None, method: str = "POST", asked: str = "authorization"
) -> dict[str, str]:
    """preflight 의 헤더. 묻는 메서드와 묻는 헤더 목록(`asked`)을 싣고, 출처가 없으면 `Origin` 을
    싣지 않는다."""
    sent = {"Access-Control-Request-Method": method, "Access-Control-Request-Headers": asked}
    return sent if origin is None else sent | {"Origin": origin}


def _cors_of(response: httpx.Response) -> list[str]:
    """응답에 붙은 CORS 헤더의 이름들. 접두사 밖에서는 비어야 한다."""
    return [name for name in CORS_HEADERS if name in response.headers]


async def test_허용_출처의_preflight_는_최종_사용자_접두사에서만_토큰_없이_200이고_그_밖은_401이다(
    stderr: io.StringIO,
) -> None:
    """ADR 0011 의 2026-10-03 이력이 "allowlist가 메서드 하나만큼 자란다"고 한 범위를 판정한다.
    앱이 아는 오퍼레이션 가운데 allowlist 밖의 전부에 허용 출처의 preflight 를 토큰 없이 보낸다.
    CORS 미들웨어가 답하는 것은 최종 사용자 접두사뿐이고, 그 밖은 허용 출처라도 인증이 401 로
    막으며 그 401 에는 CORS 헤더도 없다. `PUBLIC_PATHS` 는 그대로 `/health` 하나다 — preflight 는
    그 목록의 원소가 아니라 CORS 미들웨어의 몫이다(`/health` 의 preflight 는 인증을 지나 라우터의
    405 다). 방향마다 열거가 비면 그 방향은 아무것도 재지 않는다."""
    app = _signed_app(stderr)
    operations = [
        (method, path) for method, path in _documented_operations(app) if path not in PUBLIC_PATHS
    ]
    end_user = [op for op in operations if _surface_of(op[1]) == "end_user"]
    others = [op for op in operations if _surface_of(op[1]) != "end_user"]
    assert end_user, "최종 사용자 경로가 없으면 preflight 가 지나가는 쪽은 아무것도 재지 않는다"
    assert {_surface_of(path) for _, path in others} == {"channel", "admin"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://site.test") as c:
        for method, path in end_user:
            response = await c.options(path, headers=_preflight(ORIGIN_A, method))
            assert response.status_code == 200, (method, path)
            assert response.headers[ALLOW_ORIGIN] == ORIGIN_A, (method, path)
        for method, path in others:
            response = await c.options(path, headers=_preflight(ORIGIN_A, method))
            assert response.status_code == 401, (method, path)
            assert _cors_of(response) == [], (method, path)


async def test_접두사의_preflight_는_허용_출처면_200_허용_밖이면_400_평문_출처가_없으면_401이다(
    stderr: io.StringIO,
) -> None:
    """preflight 는 CORS 미들웨어가 인증 앞에서 답하고 갈래는 셋이다. 허용 밖 출처의 400 은
    라이브러리의 평문이고 봉투가 아니다 — 봉투 규칙의 유일한 예외다(`.claude/rules/http.md`).
    브라우저는 preflight 의 실패를 페이지 스크립트에 드러내지 않아 봉투가 있어도 읽히지 않는다.
    `Origin` 이 없으면 CORS 요청이 아니라서 미들웨어가 안쪽으로 넘기고 인증이 막는다. 셋 다 추적
    식별자를 든다 — 식별자를 심는 미들웨어가 CORS 바깥이다. 라우트가 없는 경로로 재는 이유는
    preflight 가 라우팅에 닿지 않아서다."""
    app = _signed_app(stderr)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://site.test") as c:
        allowed = await c.options(END_USER_GUARDED, headers=_preflight(ORIGIN_A))
        disallowed = await c.options(END_USER_GUARDED, headers=_preflight(EVIL_ORIGIN))
        no_origin = await c.options(END_USER_GUARDED, headers=_preflight(None))

    assert allowed.status_code == 200
    assert allowed.headers[ALLOW_ORIGIN] == ORIGIN_A
    assert allowed.headers["vary"] == "Origin"
    assert (disallowed.status_code, disallowed.text) == (400, "Disallowed CORS origin")
    assert disallowed.headers["content-type"].startswith("text/plain")
    assert ALLOW_ORIGIN not in disallowed.headers
    assert no_origin.status_code == 401
    assert no_origin.json()["code"] == "unauthorized"
    for response in (allowed, disallowed, no_origin):
        assert REQUEST_ID_HEADER in response.headers


async def test_preflight_는_허용_밖의_메서드와_헤더를_400으로_막고_자격_증명은_허용하지_않는다(
    stderr: io.StringIO,
) -> None:
    """허용 메서드는 `GET`·`POST`·`OPTIONS`, 허용 헤더는 `Authorization`·`Content-Type`·
    `Last-Event-ID` 다(end-user-channel 명세 "CORS"). 라이브러리가 CORS 안전 목록 헤더를 늘 더하므로
    허용되는 헤더는 그보다 넓지만, 그 밖의 메서드나 헤더를 묻는 preflight 는 허용 출처라도
    라이브러리의 400 이다. 쿠키를 쓰지 않으므로 자격 증명은 허용하지 않는다."""
    app = _signed_app(stderr)
    asked = "authorization, content-type, last-event-id"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://site.test") as c:
        allowed = await c.options(END_USER_GUARDED, headers=_preflight(ORIGIN_A, "GET", asked))
        method = await c.options(END_USER_GUARDED, headers=_preflight(ORIGIN_A, "DELETE"))
        header = await c.options(
            END_USER_GUARDED, headers=_preflight(ORIGIN_A, "POST", "x-api-key")
        )

    assert allowed.status_code == 200
    assert allowed.headers["access-control-allow-methods"] == "GET, POST, OPTIONS"
    assert "access-control-allow-credentials" not in allowed.headers
    assert (method.status_code, method.text) == (400, "Disallowed CORS method")
    assert (header.status_code, header.text) == (400, "Disallowed CORS headers")


async def test_허용_밖_출처의_요청에는_Allow_Origin_이_없고_요청_자체는_막지_않는다(
    stderr: io.StringIO,
) -> None:
    """읽지 못하게 하는 것은 브라우저다(스토리 23). 그래서 허용 밖 출처의 요청도 인증과 라우팅을
    그대로 지난다 — 토큰이 없으면 401 이고 맞는 토큰이면 라우팅까지 간다."""
    app = _signed_app(stderr)
    evil = {"Origin": EVIL_ORIGIN}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://site.test") as c:
        refused = await c.get(END_USER_GUARDED, headers=evil)
        routed = await c.get(END_USER_GUARDED, headers=evil | bearer(sign(KEY_A1, _good())))

    assert refused.status_code == 401
    assert routed.status_code == 404
    for response in (refused, routed):
        assert ALLOW_ORIGIN not in response.headers
        assert "access-control-allow-credentials" not in response.headers


async def test_접두사_밖에는_허용_출처의_요청에도_CORS_헤더가_없다(stderr: io.StringIO) -> None:
    """관리와 운영자 채널은 브라우저가 다른 출처에서 부르는 면이 아니다(관리 화면의 중계는 같은
    출처다, ADR 0019). 허용 출처는 최종 사용자 접두사에만 걸린다. 접두사를 문자열로만 공유하는
    경로도 밖이다 — 분기의 비교가 경로 조각 단위다."""
    app = _signed_app(stderr)
    origin = {"Origin": ORIGIN_A}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://site.test") as c:
        admin = await c.get("/plugins", headers=origin | BEARER)
        channel = await c.get(CHANNEL_GUARDED, headers=origin | CHANNEL_BEARER)
        refused = await c.get(GUARDED, headers=origin)
        lookalike = await c.get("/end-userx", headers=origin | BEARER)

    assert [r.status_code for r in (admin, channel, refused, lookalike)] == [200, 404, 401, 404]
    for response in (admin, channel, refused, lookalike):
        assert _cors_of(response) == [], response.url


async def test_사이트_둘의_출처가_모두_허용되고_출처와_토큰의_사이트를_묶지_않는다(
    stderr: io.StringIO,
) -> None:
    """허용 출처는 모든 사이트의 것을 합친 하나다(명세가 정했다). preflight 에는 토큰이 없어
    미들웨어가 출처의 사이트를 토큰보다 먼저 가를 수 없기 때문이다. 그래서 사이트 B 의 페이지에서
    사이트 A 의 토큰으로 보낸 요청도 읽힌다 — 둘 다 운영자가 사이트 파일에 올린 사이트라 믿는 범위
    안이다."""
    app = _signed_app(stderr)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://site.test") as c:
        preflights = [
            await c.options(END_USER_GUARDED, headers=_preflight(origin))
            for origin in (ORIGIN_A, ORIGIN_B)
        ]
        crossed = await c.get(
            END_USER_GUARDED, headers={"Origin": ORIGIN_B} | bearer(sign(KEY_A1, _good()))
        )

    assert [(r.status_code, r.headers.get(ALLOW_ORIGIN)) for r in preflights] == [
        (200, ORIGIN_A),
        (200, ORIGIN_B),
    ]
    assert crossed.status_code == 404
    assert crossed.headers[ALLOW_ORIGIN] == ORIGIN_B


async def test_사이트_파일이_없으면_허용_출처가_비어_어느_출처에도_붙지_않고_preflight_는_400이다(
    client: AsyncClient,
) -> None:
    """사이트 파일을 주지 않은 배치(스토리 41). 최종 사용자 경로는 서되 받아들일 사이트도 출처도
    없다."""
    preflight = await client.options(END_USER_GUARDED, headers=_preflight(ORIGIN_A))
    simple = await client.get(END_USER_GUARDED, headers={"Origin": ORIGIN_A})

    assert (preflight.status_code, preflight.text) == (400, "Disallowed CORS origin")
    assert simple.status_code == 401
    assert ALLOW_ORIGIN not in preflight.headers
    assert ALLOW_ORIGIN not in simple.headers


async def test_최종_사용자_면의_예기치_않은_500도_봉투이고_CORS_헤더와_추적_식별자를_든다(
    stderr: io.StringIO,
) -> None:
    """핸들러가 놓친 예외를 봉투로 바꾸는 자리가 CORS 안쪽이라 페이지가 그 500 의 봉투를 읽는다.
    변환이 CORS 바깥에만 있으면 그 500 에는 헤더가 붙지 않는다(`cors_scoped.py` 사례 7 과 대조군).
    원인은 서버 기록에만 간다. 운영자 면의 같은 500 은 "예기치 않은 실패도 봉투" 테스트가 잰다."""
    app = _signed_app(stderr)
    _route_that_raises(app, f"{END_USER_PREFIX}/oops", RuntimeError("내부 사정이 담긴 문구"))
    headers = {"Origin": ORIGIN_A} | bearer(sign(KEY_A1, _good()))
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://site.test") as c:
        response = await c.get(f"{END_USER_PREFIX}/oops", headers=headers)

    assert response.status_code == 500
    assert response.json()["code"] == "internal_error"
    assert response.json()["message"] == INTERNAL_MESSAGE
    assert response.headers[ALLOW_ORIGIN] == ORIGIN_A
    assert response.headers["vary"] == "Origin"
    assert response.headers["access-control-expose-headers"] == EXPOSED
    assert response.headers[REQUEST_ID_HEADER] == response.json()["request_id"]
    assert "내부 사정이 담긴 문구" not in response.text
    assert "내부 사정이 담긴 문구" in stderr.getvalue()


async def test_CORS_분기는_인증과_같은_경로로_면을_가른다(stderr: io.StringIO) -> None:
    """인증 표와 예외 표와 CORS 분기가 같은 비교(`is_under`)에 같은 경로(`request.url.path`)를
    넣는다. 경로에 퍼센트 인코딩된 `?` 가 들면 ASGI 의 `path` 와 다시 파싱한 URL 의 경로가 갈린다.
    인증은 이 경로를 최종 사용자 면으로 보아 관리 토큰을 401 로 막는데, CORS 가 다른 경로를 보면 그
    401 의 봉투를 페이지가 읽지 못한다."""
    app = _signed_app(stderr)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://site.test") as c:
        response = await c.get(f"{END_USER_PREFIX}%3Fx", headers={"Origin": ORIGIN_A} | BEARER)

    assert response.status_code == 401
    assert response.headers[ALLOW_ORIGIN] == ORIGIN_A


async def test_에러_응답이_봉투이고_code_가_상태_코드와_짝이다(client: AsyncClient) -> None:
    response = await client.get(GUARDED)
    body = response.json()

    assert set(body) == {"code", "message", "violations", "request_id"}
    assert body["code"] == "unauthorized"
    assert body["message"]
    assert body["violations"] == []


async def test_성공_응답은_봉투가_아니고_추적_식별자가_헤더로_나간다(client: AsyncClient) -> None:
    response = await client.get("/health")

    assert response.headers["X-Request-Id"]
    assert "request_id" not in response.json()


async def test_에러_봉투의_추적_식별자가_헤더와_같은_값이다(client: AsyncClient) -> None:
    response = await client.get(GUARDED)

    assert response.json()["request_id"] == response.headers["X-Request-Id"]


async def test_요청마다_추적_식별자가_다르다(client: AsyncClient) -> None:
    first = (await client.get("/health")).headers["X-Request-Id"]
    second = (await client.get("/health")).headers["X-Request-Id"]

    assert first != second


async def test_에러_하나가_서버_표준_에러에_같은_추적_식별자로_한_줄_남는다(
    client: AsyncClient, stderr: io.StringIO
) -> None:
    """화면에서 본 오류를 서버 기록과 잇는 상관 키다. 감사 로그가 아니다(스토리 31)."""
    response = await client.get(GUARDED)

    lines = stderr.getvalue().splitlines()
    assert len(lines) == 1
    assert response.headers["X-Request-Id"] in lines[0]


async def test_성공한_요청은_서버_표준_에러에_남지_않는다(
    client: AsyncClient, stderr: io.StringIO
) -> None:
    """누가 무엇을 조회했는지는 남기지 않는다. 감사 로그는 비목표다."""
    await client.get("/health")

    assert stderr.getvalue() == ""


async def test_요청이_들고_온_토큰이_응답에도_서버_기록에도_나타나지_않는다(
    client: AsyncClient, stderr: io.StringIO
) -> None:
    """원칙 V. 맞는 토큰도 틀린 토큰도 되울리지 않는다."""
    wrong = "secret-looking-value-from-the-wire"

    rejected = await client.get(GUARDED, headers={"Authorization": f"Bearer {wrong}"})
    accepted = await client.get(GUARDED, headers=BEARER)

    assert wrong not in rejected.text
    assert wrong not in stderr.getvalue()
    assert TOKEN not in accepted.text
    assert TOKEN not in stderr.getvalue()


async def test_없는_경로는_404이고_code_가_not_found_다(client: AsyncClient) -> None:
    response = await client.get("/nowhere", headers=BEARER)

    assert response.status_code == 404
    assert response.json()["code"] == "not_found"


async def test_core_의_구성_오류는_500이고_code_가_internal_error_다(
    app: FastAPI, client: AsyncClient
) -> None:
    """부재가 이미 404 로 갈리므로 PluginError 에 남는 것은 서버 디스크의 문제뿐이다(ADR 0010)."""
    _route_that_raises(app, "/broken", PluginError("매니페스트를 읽을 수 없다: plugin.toml"))

    response = await client.get("/broken", headers=BEARER)

    assert response.status_code == 500
    assert response.json()["code"] == "internal_error"
    assert "plugin.toml" in response.json()["message"]


async def test_core_의_부재는_404이고_code_가_not_found_다(
    app: FastAPI, client: AsyncClient
) -> None:
    """요청이 이름을 댄 에이전트나 실행이 없다(ADR 0014). 표가 MRO 로 옮기므로 이 갈래가 기반
    타입의 갈래보다 먼저여야 한다 — 순서가 뒤집히면 이것이 500 이 된다."""
    _route_that_raises(app, "/absent", Absent("에이전트 플러그인이 없다: nope"))

    response = await client.get("/absent", headers=BEARER)

    assert response.status_code == 404
    assert response.json()["code"] == "not_found"
    assert "nope" in response.json()["message"]


async def test_core_의_재개_불가는_409이고_code_가_conflict_다(
    app: FastAPI, client: AsyncClient
) -> None:
    """실행은 있는데 지금 상태가 요청과 맞지 않다. 부재도 형식 오류도 아니다(ADR 0010 의
    2026-09-24 이력). 이 갈래도 기반 타입의 갈래보다 먼저여야 한다."""
    _route_that_raises(app, "/done", NotResumable("일시정지 상태가 아니라 재개할 수 없다: run-1"))

    response = await client.get("/done", headers=BEARER)

    assert response.status_code == 409
    assert response.json()["code"] == "conflict"
    assert "run-1" in response.json()["message"]


async def test_core_의_꺼짐은_409이고_code_가_conflict_다(
    app: FastAPI, client: AsyncClient
) -> None:
    """대상은 있는데 운영자가 끈 상태라 요청을 허락하지 않는다. 깨진 것이 아니라 500 이 아니고,
    없는 것이 아니라 404 가 아니다(ADR 0017, ADR 0014 의 2026-09-26 이력). 이 갈래도 기반 타입의
    갈래보다 먼저여야 한다 — 뒤집히면 500 이 된다. 던지는 쪽은 core 의 준비 단계이고 그 순서는
    `tests/core/test_run.py` 가 잰다. 여기서는 표만 잰다."""
    _route_that_raises(app, "/off", Disabled("꺼진 플러그인이다: agent calc"))

    response = await client.get("/off", headers=BEARER)

    assert response.status_code == 409
    assert response.json()["code"] == "conflict"
    assert "calc" in response.json()["message"]


async def test_예기치_않은_실패도_봉투이고_내부_문구를_밖으로_내지_않는다(
    app: FastAPI, client: AsyncClient, stderr: io.StringIO
) -> None:
    """운영자는 서버 기록에서 원인을 찾고 클라이언트는 상관 키만 받는다."""
    _route_that_raises(app, "/oops", RuntimeError("내부 사정이 담긴 문구"))

    response = await client.get("/oops", headers=BEARER)

    assert response.status_code == 500
    assert response.json()["code"] == "internal_error"
    assert "내부 사정이 담긴 문구" not in response.text
    assert "내부 사정이 담긴 문구" in stderr.getvalue()
    assert response.headers["X-Request-Id"] == response.json()["request_id"]


async def test_질의_형식_오류는_422이고_violations_가_점으로_이은_경로를_든다(
    app: FastAPI, client: AsyncClient
) -> None:
    """422 는 FastAPI 가 내고 봉투만 우리 것이다. 진짜 라우트의 질의 검증은 `/traces` 쪽이 잰다."""

    @app.get("/paged")
    def _paged(limit: int = 1) -> Health:  # pragma: no cover - 검증에서 끝나 몸통에 닿지 않는다
        return Health(status="ok")

    response = await client.get("/paged?limit=not-a-number", headers=BEARER)

    assert response.status_code == 422
    body = response.json()
    assert body["code"] == "invalid_request"
    assert [violation["field"] for violation in body["violations"]] == ["query.limit"]
    assert body["violations"][0]["message"]


def test_스키마에_이름_있는_타입이_나온다(app: FastAPI) -> None:
    """생성 클라이언트의 타입 이름이 익명 구조체가 되지 않는다(스토리 28)."""
    components = app.openapi().get("components", {})
    schemas = components.get("schemas", {})

    assert {"Health", "ErrorEnvelope", "Violation"} <= set(schemas)


def test_에러_봉투의_code_어휘가_상태_코드와_1대1인_여섯이다(app: FastAPI) -> None:
    """어휘가 openapi.json 에 박힌다. 슬라이스 3 이 에러 처리를 한 곳에서 받는 근거다. conflict 는
    대상이 있지만 그 상태나 주체가 요청을 허락하지 않는 409 이고, 표가 재개 불가와 꺼짐과 다른
    주체와 이어 갈 수 없음을 거기로 옮긴다(ADR 0010 의 2026-09-24·2026-09-26 이력, ADR 0022). 관리
    라우트는 내지 않는다. 여섯째인 too_many_requests 는 요청하는 쪽의 상한에 걸린 429 다(ADR 0023,
    ADR 0010 의 2026-10-03 이력)."""
    schemas = app.openapi().get("components", {}).get("schemas", {})

    assert set(schemas["ErrorCode"]["enum"]) == {
        "unauthorized",
        "invalid_request",
        "not_found",
        "conflict",
        "too_many_requests",
        "internal_error",
    }


async def test_429_는_계열로_접히지_않고_too_many_requests_다(
    app: FastAPI, client: AsyncClient
) -> None:
    """어휘 테스트는 enum 의 집합만 본다. 상태 코드→어휘 표에 429 가 없으면 4xx 계열로 접혀
    `invalid_request` 가 되고 그 테스트는 초록이다(end-user-channel 명세 검토). 429 를 내는 자리는
    상한 티켓이 들이므로 여기서는 표만 잰다."""
    _route_that_raises(app, "/busy", StarletteHTTPException(status_code=429, detail="바쁘다"))

    response = await client.get("/busy", headers=BEARER)

    assert response.status_code == 429
    assert response.json()["code"] == "too_many_requests"


def test_관리_라우터가_도구_포트를_받지_않는다() -> None:
    """조회가 MCP 서버를 띄우는 것이 구조적으로 불가능하다(스토리 7). 앱은 채널을 위해 도구 포트를
    받지만 그 성질을 지키던 것은 관리 라우터의 시그니처다(ADR 0010 의 2026-09-24 이력)."""
    parameters = inspect.signature(admin_http.admin_router).parameters

    assert "tools" not in parameters
    assert ToolSource not in get_type_hints(admin_http.admin_router).values()


def test_모듈_수준_전역_앱이_없다() -> None:
    """전역 앱은 import 시점에 경로를 고정해 테스트가 진짜 파일시스템을 쓰게 만든다(ADR 0010)."""
    assert "app" not in vars(server_module)


# 플러그인 — 등록된 것을 한 곳에서 본다(티켓 04)


async def test_플러그인_목록이_종류들을_한_평평한_목록으로_주고_항목마다_종류를_든다(
    client: AsyncClient,
) -> None:
    """클라이언트가 종류로 가른다. 종류마다 경로가 갈리면 PRD 의 "한 곳"이 아니다(스토리 2)."""
    response = await client.get("/plugins", headers=BEARER)

    assert response.status_code == 200
    rows = response.json()
    assert [(row["kind"], row["name"]) for row in rows] == [
        ("agent", "broken"),
        ("agent", "calc"),
        ("mcp", "everything"),
        ("skill", "summarize"),
        ("model", "sonnet"),
    ]


async def test_행의_겉은_종류_이름_켜짐이고_읽히는_행은_매니페스트를_표지_행은_이유를_든다(
    client: AsyncClient,
) -> None:
    """읽히든 안 읽히든 모든 행에 스위치를 그릴 수 있다(스토리 56). 켜짐은 매니페스트 안이 아니라
    행의 겉에 있어 `plugin.toml` 에 적으면 된다고 믿게 하지 않는다(스토리 10, ADR 0017)."""
    rows = (await client.get("/plugins", headers=BEARER)).json()

    shapes = {frozenset(row) for row in rows}
    assert shapes == {
        frozenset({"kind", "name", "enabled", "manifest"}),
        frozenset({"kind", "name", "enabled", "reason"}),
    }
    assert all("enabled" not in row["manifest"] for row in rows if "manifest" in row)


async def test_목록의_행이_매니페스트를_통째로_담아_승인_대상_도구가_보인다(
    client: AsyncClient,
) -> None:
    """가드레일의 범위를 코드를 읽지 않고 안다(스토리 3). interrupts 가 필드로 닫은 것을 읽는
    면이다. 매니페스트는 sdk 의 것 그대로다(ADR 0010 의 2026-09-23·2026-09-26 이력)."""
    rows = (await client.get("/plugins", headers=BEARER)).json()

    calc = next(row for row in rows if row["name"] == "calc")
    assert calc["manifest"] == CALC.model_dump(mode="json")
    assert calc["manifest"]["requires_approval"] == ["add"]


async def test_mcp_매니페스트의_command_와_args_도_가리지_않고_내보낸다(
    client: AsyncClient,
) -> None:
    """가리지 않는 것이 결정이고 경계는 인증이다(ADR 0009 의 2026-09-22 이력, 네 번째 열린 문제).

    MCP 구성을 디버깅하는 사람이 정확히 이 둘을 봐야 한다. 가리는 날에는 이 테스트가 먼저 바뀐다.
    """
    rows = (await client.get("/plugins", headers=BEARER)).json()

    everything = next(row for row in rows if row["name"] == "everything")
    assert everything["manifest"]["server"]["command"] == "npx"
    assert everything["manifest"]["server"]["args"] == [
        "-y",
        "@modelcontextprotocol/server-everything",
    ]


async def test_읽을_수_없는_매니페스트가_있어도_나머지가_오고_그것은_켜짐과_이유를_든_표지다(
    client: AsyncClient,
) -> None:
    """조용히 빠지면 등록했다고 믿는 것과 실제가 어긋나고, 전체가 실패하면 무엇이 살아 있는지조차
    모른다(스토리 5·6). 표지에도 켜짐이 있어 깨진 것을 끈 채로 고치고 있는지 안다(스토리 8)."""
    response = await client.get("/plugins", headers=BEARER)

    assert response.status_code == 200
    rows = response.json()
    assert {
        "kind": "agent",
        "name": "broken",
        "enabled": True,
        "reason": "매니페스트를 읽을 수 없다: plugins/agents/broken/plugin.toml",
    } in rows
    assert {row["name"] for row in rows} == {"broken", "calc", "everything", "summarize", "sonnet"}


async def test_꺼진_것은_목록에서_enabled_가_거짓이고_표지_행도_꺼질_수_있다(
    client: AsyncClient, plugins: FakePlugins
) -> None:
    """무엇이 꺼져 있는지 한 곳에서 본다(스토리 7·8). 켜짐은 매니페스트가 아니라 운영자 파일에서
    온다."""
    plugins.disabled = frozenset({EVERYTHING_KEY, BROKEN_KEY})

    rows = (await client.get("/plugins", headers=BEARER)).json()

    assert {row["name"]: row["enabled"] for row in rows} == {
        "broken": False,
        "calc": True,
        "everything": False,
        "summarize": True,
        "sonnet": True,
    }


async def test_이름이_패턴을_어긴_표지_행은_언제나_켜짐이다(
    stderr: io.StringIO,
) -> None:
    """그런 이름은 운영자 파일에 들 수 없다 — 들면 파일이 손상이다. 꺼진 집합에 같은 문자열이 있어도
    유효한 이름의 타입으로 감싸 견주지 않는다."""
    odd = UnreadableManifest(
        kind=PluginKind.AGENT,
        name="MyAgent",
        reason="디렉터리 이름이 플러그인 이름의 패턴을 어긴다",
    )
    plugins = FakePlugins(rows=(odd, CALC), disabled={CALC_KEY})
    transport = ASGITransport(app=_admin_app(plugins=plugins, trace=FakeTrace(), stderr=stderr))

    async with AsyncClient(transport=transport, base_url="http://admin.test") as client:
        rows = (await client.get("/plugins", headers=BEARER)).json()

    assert {row["name"]: row["enabled"] for row in rows} == {"MyAgent": True, "calc": False}


async def test_꺼진_집합은_목록_요청_하나에_한_번_읽는다(
    client: AsyncClient, plugins: FakePlugins
) -> None:
    """행마다 파일을 다시 읽지 않는다(ADR 0012 의 2026-09-26 이력)."""
    await client.get("/plugins", headers=BEARER)

    assert plugins.disabled_reads == 1


async def test_운영자_파일이_깨지면_목록_전체가_500_봉투다(stderr: io.StringIO) -> None:
    """매니페스트 하나가 깨졌을 때 그 행만 표지가 되는 것과 다르다. 행마다 "알 수 없음"을 실으면
    행의 타입이 약해진다(ADR 0017). 메시지가 파일 경로를 든다(스토리 21)."""
    plugins = FakePlugins(rows=(CALC,), corrupt="운영자 파일이 깨졌다: plugins/disabled.toml")
    transport = ASGITransport(app=_admin_app(plugins=plugins, trace=FakeTrace(), stderr=stderr))

    async with AsyncClient(transport=transport, base_url="http://admin.test") as client:
        response = await client.get("/plugins", headers=BEARER)

    assert response.status_code == 500
    assert response.json()["code"] == "internal_error"
    assert "plugins/disabled.toml" in response.json()["message"]


async def test_플러그인_하나를_물으면_켜짐과_매니페스트를_통째로_든_행을_돌려준다(
    client: AsyncClient,
) -> None:
    """목록이 말해 주지 않는 세부를 확인하고(스토리 4), 목록을 다 받지 않고 켜짐 하나를 본다
    (스토리 9)."""
    calc = await client.get("/plugins/agent/calc", headers=BEARER)
    everything = await client.get("/plugins/mcp/everything", headers=BEARER)

    assert calc.status_code == 200
    assert calc.json() == {
        "kind": "agent",
        "name": "calc",
        "enabled": True,
        "manifest": CALC.model_dump(mode="json"),
    }
    assert everything.json()["enabled"] is False


async def test_단건_조회의_판정_순서는_부재_깨진_매니페스트_운영자_파일의_손상이다(
    stderr: io.StringIO,
) -> None:
    """운영자 파일이 깨졌어도 없는 이름은 404 다(ADR 0017 의 2026-09-27 둘째 이력). 깨진
    매니페스트는 운영자 파일보다 먼저 500 이라 메시지가 매니페스트를 가리킨다."""
    operator_file = "운영자 파일이 깨졌다: plugins/disabled.toml"
    plugins = FakePlugins(rows=(BROKEN, CALC), corrupt=operator_file)
    transport = ASGITransport(app=_admin_app(plugins=plugins, trace=FakeTrace(), stderr=stderr))

    async with AsyncClient(transport=transport, base_url="http://admin.test") as client:
        absent = await client.get("/plugins/agent/nothing", headers=BEARER)
        broken = await client.get("/plugins/agent/broken", headers=BEARER)
        present = await client.get("/plugins/agent/calc", headers=BEARER)

    assert absent.status_code == 404
    assert broken.status_code == 500
    assert "plugins/agents/broken/plugin.toml" in broken.json()["message"]
    assert "disabled.toml" not in broken.json()["message"]
    assert present.status_code == 500
    assert "plugins/disabled.toml" in present.json()["message"]


async def test_없는_플러그인은_404이고_code_가_not_found_다(client: AsyncClient) -> None:
    """내 오타와 서버의 문제가 갈린다(스토리 18). 같은 이름이라도 종류가 다르면 없는 것이다."""
    for path in ("/plugins/agent/nothing", "/plugins/mcp/calc"):
        response = await client.get(path, headers=BEARER)

        assert response.status_code == 404, path
        assert response.json()["code"] == "not_found", path


async def test_읽을_수_없는_매니페스트는_목록에서는_표지이고_단건으로는_500이다(
    client: AsyncClient,
) -> None:
    """비대칭이 의도다(ADR 0012 의 2026-09-22 이력). 목록은 "무엇이 있나"라서 하나가 깨져도 나머지가
    답이고, 단건은 그 파일 하나를 달라는 것이라 실패가 곧 답이다. 4xx 면 운영자가 잘못 요청했다고
    믿고 깨진 파일을 못 찾는다(스토리 19)."""
    rows = (await client.get("/plugins", headers=BEARER)).json()
    single = await client.get("/plugins/agent/broken", headers=BEARER)

    assert any(row["name"] == "broken" and "reason" in row for row in rows)
    assert single.status_code == 500
    assert single.json()["code"] == "internal_error"
    assert "plugins/agents/broken/plugin.toml" in single.json()["message"]


async def test_없는_종류는_422이고_포트가_불리지_않는다(
    client: AsyncClient, plugins: FakePlugins
) -> None:
    """없는 종류는 부재가 아니라 형식 오류다. 404 면 그런 종류가 있는데 비었다고 읽힌다."""
    response = await client.get("/plugins/agents/calc", headers=BEARER)

    assert response.status_code == 422
    assert [violation["field"] for violation in response.json()["violations"]] == ["path.kind"]
    assert plugins.calls == 0


# 루트를 벗어나려는 이름들. 경로 조각이 `plugins/{kind}/{name}/plugin.toml` 로 그대로 조립되므로
# 하나라도 포트에 닿으면 루트 밖을 읽는다. 퍼센트 인코딩으로 적는 이유는 httpx 가 맨 `..` 조각을
# 보내기 전에 정규화해 지워 버리기 때문이다 — 그러면 요청이 `/plugins` 로 가서 이 단언이 엉뚱한
# 이유로 통과한다. 서버는 이것들을 디코딩된 채로 받는다(`%2F` 는 `/` 가 된다).
ESCAPING_NAMES = (
    "%2E%2E",  # ..
    "..%2F..%2Fetc",  # ../../etc
    "..%5C..%5Csecret",  # ..\..\secret — 윈도가 주 환경이라 역슬래시도 구분자다
    "%2Fetc%2Fpasswd",  # /etc/passwd — pathlib 의 / 는 오른쪽이 절대 경로면 왼쪽을 버린다
    "C:%5CWindows",  # C:\Windows
    "C:%2FWindows",  # C:/Windows
)


async def test_루트를_벗어나려는_이름은_422이고_포트가_아예_불리지_않는다(
    client: AsyncClient, plugins: FakePlugins
) -> None:
    """검증이 파일시스템에 닿기 전에 끝난다(스토리 43). 404 와 500 이 갈리는 것 자체가 임의 경로의
    파일 존재를 알려 주는 오라클이라, 포트가 한 번이라도 불리면 그 오라클이 열린다."""
    for name in ESCAPING_NAMES:
        response = await client.get(f"/plugins/agent/{name}", headers=BEARER)

        assert response.status_code == 422, name
        fields = [violation["field"] for violation in response.json()["violations"]]
        assert fields == ["path.name"], name
    assert plugins.calls == 0


async def test_개행이_섞인_이름도_422이고_포트가_불리지_않는다(
    client: AsyncClient, plugins: FakePlugins
) -> None:
    """형식 위반은 자리가 어디든 422 다. 라우팅 정규식이 파이썬 `re` 라서 `.` 은 개행을 넘지 못하고
    `$` 는 마지막 개행 앞에서도 맞는다. 그 규칙대로면 가운데 개행은 라우트가 안 맞아 404 가 되고
    꼬리 개행은 떼어져 `calc` 로 읽힌다. 둘 다 내 오타와 서버의 문제를 가르는 표를 어긴다."""
    for name in ("calc%0A", "%0Acalc", "calc%0Ax"):
        response = await client.get(f"/plugins/agent/{name}", headers=BEARER)

        assert response.status_code == 422, name
    assert plugins.calls == 0


def test_경로에_거는_이름_패턴이_sdk_가_매니페스트에_거는_그것이고_계약에_박힌다(
    app: FastAPI,
) -> None:
    """새 규칙이 아니라 있는 계약을 조회 쪽에도 거는 것이다."""
    parameters = app.openapi()["paths"]["/plugins/{kind}/{name}"]["get"]["parameters"]
    name = next(parameter for parameter in parameters if parameter["name"] == "name")

    assert name["schema"]["pattern"] == PLUGIN_NAME_PATTERN


def test_문서화된_에러_응답이_전부_봉투이고_내는_에러를_빠뜨리지_않는다(app: FastAPI) -> None:
    """라우트를 더하며 적는 것을 잊으면 이 테스트가 깨진다. 401 은 미들웨어가 내는 것이라
    프레임워크가 적어 주지 않고, FastAPI 가 파라미터 있는 라우트에 붙이는 제 422 모양은 우리 봉투가
    아니라 그대로 두면 계약이 거짓말을 한다."""
    document = app.openapi()
    envelope = {"$ref": "#/components/schemas/ErrorEnvelope"}

    for path, operations in document["paths"].items():
        for method, operation in operations.items():
            where = f"{method} {path}"
            responses = operation["responses"]
            errors = {status for status in responses if not status.startswith("2")}
            assert "500" in errors, where
            if path not in PUBLIC_PATHS:
                assert "401" in errors, where
            if operation.get("parameters"):
                assert "422" in errors, where
            for status in errors:
                schema = responses[status]["content"]["application/json"]["schema"]
                assert schema == envelope, (where, status)
    assert "404" in document["paths"]["/plugins/{kind}/{name}"]["get"]["responses"]
    assert "404" in document["paths"]["/plugins/{kind}/{name}/enabled"]["put"]["responses"]
    assert "404" in document["paths"]["/traces/{run_id}"]["get"]["responses"]
    assert "HTTPValidationError" not in document["components"]["schemas"]


def test_표지_행의_HTTP_모양이_core_의_표지에_켜짐을_더한_것이다() -> None:
    """관리 쪽 행이 core 의 표지를 옮긴 것이라 필드 목록이 두 곳이다. core 에 필드가 늘면 여기가
    빨개져 관리 쪽이 조용히 뒤처지지 않는다. 더한 하나가 켜짐이고 그것은 표지가 아니라 행의
    것이다(ADR 0010 의 2026-09-26 이력). 읽히는 행은 매니페스트를 통째로 담아 별도 타입이 없다."""
    assert set(admin_http.PluginPlaceholder.model_fields) == {
        field.name for field in dataclasses.fields(UnreadableManifest)
    } | {"enabled"}
    assert set(admin_http.Plugin.model_fields) == {"kind", "name", "enabled", "manifest"}


def test_늘_실리는_매니페스트_필드와_행의_필드는_계약에서도_required_다(app: FastAPI) -> None:
    """서버는 필드를 언제나 전부 싣는다. 기본값 있는 필드가 required 에서 빠지면 생성 클라이언트가
    `requires_approval` 을 선택 필드로 받는다. 행 둘은 기본값이 없어 전부 required 이고, 그래서
    `manifest` 와 `reason` 으로 갈린다(스토리 57)."""
    schemas = app.openapi()["components"]["schemas"]

    assert set(schemas["PluginManifest"]["required"]) == set(PluginManifest.model_fields)
    assert set(schemas["McpServer"]["required"]) == set(McpServer.model_fields)
    assert set(schemas["Plugin"]["required"]) == {"kind", "name", "enabled", "manifest"}
    assert set(schemas["PluginPlaceholder"]["required"]) == {"kind", "name", "enabled", "reason"}
    assert schemas["Plugin"]["additionalProperties"] is False
    assert schemas["PluginPlaceholder"]["additionalProperties"] is False


def test_플러그인_목록의_행_타입이_이름_있는_스키마다(app: FastAPI) -> None:
    """생성 클라이언트가 익명 유니온 대신 이름 있는 타입을 받는다(스토리 28·57). 단건도 같은
    행이다."""
    document = app.openapi()
    schemas = document["components"]["schemas"]
    ok = document["paths"]["/plugins"]["get"]["responses"]["200"]
    items = ok["content"]["application/json"]["schema"]["items"]
    single = document["paths"]["/plugins/{kind}/{name}"]["get"]["responses"]["200"]

    assert items == {"$ref": "#/components/schemas/PluginRow"}
    assert schemas["PluginRow"] == {
        "anyOf": [
            {"$ref": "#/components/schemas/Plugin"},
            {"$ref": "#/components/schemas/PluginPlaceholder"},
        ]
    }
    assert single["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/Plugin"
    }
    assert schemas["Plugin"]["properties"]["manifest"] == {
        "$ref": "#/components/schemas/PluginManifest"
    }


def test_읽히는_행의_이름은_sdk_의_패턴을_계약에_싣고_표지_행의_이름은_싣지_않는다(
    app: FastAPI,
) -> None:
    """목록에서 얻은 이름을 켜고 끄는 경로에 그대로 넘길 수 있다. 표지는 패턴을 어긴 디렉터리
    이름일 수 있어 `str` 그대로다(`.claude/rules/core.md`)."""
    schemas = app.openapi()["components"]["schemas"]

    assert schemas["Plugin"]["properties"]["name"]["pattern"] == PLUGIN_NAME_PATTERN
    assert "pattern" not in schemas["PluginPlaceholder"]["properties"]["name"]


# 켜고 끄기 — 관리의 첫 쓰기 경로(plugin-toggle 티켓 01, ADR 0010 의 2026-09-26 이력)

ENABLED_PATH = "/plugins/agent/calc/enabled"
OFF = {"enabled": False}
ON = {"enabled": True}


async def _enabled_of(client: AsyncClient, name: str) -> bool:
    rows = (await client.get("/plugins", headers=BEARER)).json()
    return bool(next(row for row in rows if row["name"] == name)["enabled"])


async def test_켜고_끄기가_본문_없는_204이고_다음_목록에_반영된다(
    client: AsyncClient, plugins: FakePlugins
) -> None:
    """HTTP 요청 하나로 끄고 같은 길로 켠다(스토리 1·2). 204 인 이유는 깨진 매니페스트를 끈 직후의
    응답이 단건 조회(500)와 모양이 갈리지 않게 하기 위해서다(스토리 4, ADR 0010 의 2026-09-26
    이력)."""
    off = await client.put(ENABLED_PATH, json=OFF, headers=BEARER)
    after_off = await _enabled_of(client, "calc")
    on = await client.put(ENABLED_PATH, json=ON, headers=BEARER)
    after_on = await _enabled_of(client, "calc")

    assert off.status_code == 204
    assert off.content == b""
    assert after_off is False
    assert on.status_code == 204
    assert after_on is True
    assert plugins.writes == [(CALC_KEY, False), (CALC_KEY, True)]


async def test_이미_꺼진_것을_다시_꺼도_204다(client: AsyncClient) -> None:
    """두 번 누른 버튼이나 재시도가 에러가 되면 안 된다(스토리 3)."""
    response = await client.put("/plugins/mcp/everything/enabled", json=OFF, headers=BEARER)

    assert response.status_code == 204
    assert await _enabled_of(client, "everything") is False


async def test_없는_플러그인의_켜고_끄기는_404이고_운영자_파일이_깨졌어도_그렇다(
    client: AsyncClient, stderr: io.StringIO
) -> None:
    """오타로 지은 이름이 파일에 쌓이면 안 된다(스토리 5). 부재 판정이 손상 판정보다 먼저다(ADR
    0017 의 2026-09-27 둘째 이력). 같은 이름이라도 종류가 다르면 없는 것이다."""
    for path in ("/plugins/agent/nothing/enabled", "/plugins/mcp/calc/enabled"):
        response = await client.put(path, json=OFF, headers=BEARER)

        assert response.status_code == 404, path
        assert response.json()["code"] == "not_found", path

    corrupt = FakePlugins(rows=(CALC,), corrupt="운영자 파일이 깨졌다: plugins/disabled.toml")
    transport = ASGITransport(app=_admin_app(plugins=corrupt, trace=FakeTrace(), stderr=stderr))
    async with AsyncClient(transport=transport, base_url="http://admin.test") as other:
        response = await other.put("/plugins/agent/nothing/enabled", json=OFF, headers=BEARER)

    assert response.status_code == 404
    assert corrupt.writes == []


async def test_매니페스트가_깨진_플러그인도_켜고_끌_수_있다(client: AsyncClient) -> None:
    """고칠 때까지 런타임이 부르지 않게 하려는 것이 끄는 이유일 수 있다(스토리 6). 끄는 키는
    매니페스트가 아니라 이름이다."""
    response = await client.put("/plugins/agent/broken/enabled", json=OFF, headers=BEARER)

    assert response.status_code == 204
    assert await _enabled_of(client, "broken") is False


@pytest.mark.parametrize(
    "fake",
    [
        pytest.param(
            FakePlugins(rows=(CALC,), corrupt="운영자 파일이 깨졌다: plugins/disabled.toml"),
            id="운영자 파일의 손상",
        ),
        pytest.param(
            FakePlugins(rows=(CALC,), unwritable="운영자 파일을 쓸 수 없다: plugins/disabled.toml"),
            id="쓰기 실패",
        ),
    ],
)
async def test_있는_이름이라도_운영자_파일이_깨졌거나_쓰지_못하면_500_봉투이고_쓰지_않는다(
    stderr: io.StringIO, fake: FakePlugins
) -> None:
    """깨진 파일을 덮어쓰면 끈 것이 조용히 켜질 수 있다(스토리 22). 실패한 쓰기가 켜짐을 바꾸면 안
    된다(스토리 29)."""
    transport = ASGITransport(app=_admin_app(plugins=fake, trace=FakeTrace(), stderr=stderr))

    async with AsyncClient(transport=transport, base_url="http://admin.test") as client:
        response = await client.put(ENABLED_PATH, json=OFF, headers=BEARER)

    assert response.status_code == 500
    assert response.json()["code"] == "internal_error"
    assert "plugins/disabled.toml" in response.json()["message"]
    assert fake.writes == []


async def test_skill_과_model_의_켜고_끄기도_204이고_기록된다(
    client: AsyncClient, plugins: FakePlugins
) -> None:
    """등록된 것을 한 가지 방법으로 다룬다(스토리 17). 효과가 나는 때는 로더가 생긴 뒤이고 그것은
    `README.md` 가 말한다(스토리 18)."""
    skill = await client.put("/plugins/skill/summarize/enabled", json=OFF, headers=BEARER)
    model = await client.put("/plugins/model/sonnet/enabled", json=OFF, headers=BEARER)

    assert (skill.status_code, model.status_code) == (204, 204)
    assert plugins.writes == [
        (PluginKey(kind=PluginKind.SKILL, name=PluginName("summarize")), False),
        (PluginKey(kind=PluginKind.MODEL, name=PluginName("sonnet")), False),
    ]
    assert await _enabled_of(client, "summarize") is False
    assert await _enabled_of(client, "sonnet") is False


async def test_켜고_끄는_경로의_이름이_루트를_벗어나거나_개행이_섞이면_422이고_포트가_불리지_않는다(
    client: AsyncClient, plugins: FakePlugins
) -> None:
    """단건 조회와 같은 규칙이다(스토리 40). 이름이 파일 경로로 조립되기 전에 sdk 의 패턴을
    지난다."""
    for name in (*ESCAPING_NAMES, "calc%0A", "%0Acalc", "calc%0Ax"):
        response = await client.put(f"/plugins/agent/{name}/enabled", json=OFF, headers=BEARER)

        assert response.status_code == 422, name
        fields = [violation["field"] for violation in response.json()["violations"]]
        assert fields == ["path.name"], name
    assert plugins.calls == 0


async def test_enabled_를_GET_하면_422이고_이름까지만_PUT_하면_405다(client: AsyncClient) -> None:
    """`{name:verbatim}` 이 슬래시까지 잡아 GET 은 이름 `calc/enabled` 로 단건에 맞은 뒤 패턴이
    거른다. PUT 은 단건 경로에 라우트가 없다(ADR 0010 의 2026-09-26 이력)."""
    get = await client.get(ENABLED_PATH, headers=BEARER)
    put = await client.put("/plugins/agent/calc", json=OFF, headers=BEARER)

    assert get.status_code == 422
    assert [violation["field"] for violation in get.json()["violations"]] == ["path.name"]
    assert put.status_code == 405
    assert put.json()["code"] == "invalid_request"


async def test_enabled_뒤에_꼬리_개행이_붙은_경로는_이름_calc_로_맞아_204다(
    client: AsyncClient, plugins: FakePlugins
) -> None:
    """명세 검토의 프로브를 실제 변환기로 다시 잰 결과다. 라우팅 정규식이 파이썬 `re` 라 `$` 가
    리터럴 `/enabled` 뒤의 꼬리 개행 앞에서도 맞는다. 포트에 닿는 이름은 `calc` 그대로라 패턴을
    지나고 경로가 플러그인 루트를 벗어나지 않으므로 그대로 둔다."""
    response = await client.put(f"{ENABLED_PATH}%0A", json=OFF, headers=BEARER)

    assert response.status_code == 204
    assert plugins.writes == [(CALC_KEY, False)]


@pytest.mark.parametrize(
    ("body", "field"),
    [
        pytest.param({}, "body.enabled", id="enabled 없음"),
        pytest.param({"enabled": "false"}, "body.enabled", id="문자열 false"),
        pytest.param({"enabled": 0}, "body.enabled", id="숫자 0"),
        pytest.param({"enabled": False, "reason": "위험"}, "body.reason", id="추가 필드"),
    ],
)
async def test_enabled_가_없거나_불린이_아니거나_추가_필드가_있으면_422이고_포트가_불리지_않는다(
    client: AsyncClient, plugins: FakePlugins, body: dict[str, object], field: str
) -> None:
    """`"false"` 나 `0` 을 조용히 뜻으로 읽으면 계약에 없는 값이 켜짐을 정한다(스토리 41). 모르는
    필드를 받으면 보낸 쪽이 자기 값이 쓰였다고 믿는다(스토리 42)."""
    response = await client.put(ENABLED_PATH, json=body, headers=BEARER)

    assert response.status_code == 422
    assert response.json()["code"] == "invalid_request"
    assert [violation["field"] for violation in response.json()["violations"]] == [field]
    assert plugins.calls == 0


def test_본문_모델은_enabled_하나가_필수인_boolean_이고_추가_필드를_받지_않는다(
    app: FastAPI,
) -> None:
    """엄격한 불린이어도 계약의 스키마는 `boolean` 그대로다. 본문 모델의 이름이 기존 컴포넌트와
    겹치지 않아 컴포넌트가 `-Input`·`-Output` 으로 갈라지지 않는다."""
    schemas = app.openapi()["components"]["schemas"]
    body = schemas["SetEnabled"]

    assert body["properties"] == {"enabled": {"type": "boolean", "title": "Enabled"}}
    assert body["required"] == ["enabled"]
    assert body["additionalProperties"] is False
    assert not {name for name in schemas if name.endswith(("-Input", "-Output"))}


def test_켜고_끄는_라우트가_operation_id_와_봉투_에러_문서를_들고_409는_없다(app: FastAPI) -> None:
    """생성 클라이언트의 함수 이름이 `operationId` 다. 끄는 것은 꺼진 것을 거부하지 않으므로 409 가
    없다. 경로의 패턴은 단건 조회와 같은 sdk 의 것이다."""
    document = app.openapi()
    operation = document["paths"]["/plugins/{kind}/{name}/enabled"]["put"]
    envelope = {"$ref": "#/components/schemas/ErrorEnvelope"}

    assert operation["operationId"] == "set_plugin_enabled"
    errors = {status for status in operation["responses"] if not status.startswith("2")}
    assert errors == {"401", "404", "422", "500"}
    for status in errors:
        schema = operation["responses"][status]["content"]["application/json"]["schema"]
        assert schema == envelope, status
    assert "content" not in operation["responses"]["204"]
    name = next(parameter for parameter in operation["parameters"] if parameter["name"] == "name")
    assert name["schema"]["pattern"] == PLUGIN_NAME_PATTERN
    body = operation["requestBody"]["content"]["application/json"]["schema"]
    assert body == {"$ref": "#/components/schemas/SetEnabled"}


async def test_동시에_온_켜고_끄기_둘이_둘_다_남는다(stderr: io.StringIO) -> None:
    """갱신 하나가 사라지면 끈 줄 아는 것이 돈다(스토리 43). 한 프로세스 안의 쓰기 둘은 이벤트
    루프가 줄세운다는 ADR 0017 의 전제는 쓰기 라우트가 루프 위에서 돌 때만 참이다 — 동기 `def` 면
    FastAPI 가 워커 스레드에서 돌려 읽고 고치고 쓰기 둘이 겹친다. 가짜의 쓰기가 디스크 시간을 들이는
    이유는 즉시 끝나면 그 겹침이 스레드 타이밍에 달려 초록으로 지나가기 때문이다."""
    plugins = FakePlugins(rows=(CALC, EVERYTHING), disk_seconds=0.05)
    transport = ASGITransport(app=_admin_app(plugins=plugins, trace=FakeTrace(), stderr=stderr))

    async with AsyncClient(transport=transport, base_url="http://admin.test") as client:
        responses = await asyncio.gather(
            client.put(ENABLED_PATH, json=OFF, headers=BEARER),
            client.put("/plugins/mcp/everything/enabled", json=OFF, headers=BEARER),
        )
        rows = (await client.get("/plugins", headers=BEARER)).json()

    assert [response.status_code for response in responses] == [204, 204]
    assert {row["name"]: row["enabled"] for row in rows} == {"calc": False, "everything": False}


# 트레이스 목록 — 지나간 실행과 멈춘 실행(티켓 05)


def _run_ids(response: httpx.Response) -> list[str]:
    return [str(row["run_id"]) for row in response.json()["runs"]]


def _opaque(payload: str) -> str:
    """손으로 짠 커서. 형식 오류를 밀 때만 쓴다 — 클라이언트는 받은 것을 되돌려 줄 뿐이다."""
    return base64.urlsafe_b64encode(payload.encode()).rstrip(b"=").decode("ascii")


async def test_트레이스_목록이_실행_요약과_다음_커서를_돌려준다(client: AsyncClient) -> None:
    """무엇이 돌았는지 기억과 스크롤백에 의존하지 않는다(스토리 8·9·12). 행마다 어떤 에이전트의
    것이고 누가 요청했고 언제 시작해 언제 마지막으로 움직였는지가 보인다."""
    response = await client.get("/traces", headers=BEARER)

    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"runs", "next_cursor"}
    paused = next(row for row in body["runs"] if row["run_id"] == PAUSED.run_id)
    assert paused == {
        "run_id": "7c1e2d9a",
        "status": "paused",
        "schema_version": "2",
        "started_at": "2026-09-23T12:00:00Z",
        "last_at": "2026-09-23T12:01:00Z",
        "agent": "calc",
        "principal": "alice",
    }


async def test_요약의_필드는_일곱이고_프롬프트도_토큰_수도_없다(
    app: FastAPI, client: AsyncClient
) -> None:
    """목록은 개요를 보는 자리이지 내용을 읽는 자리가 아니다(스토리 15, ADR 0012 이력)."""
    rows = (await client.get("/traces", headers=BEARER)).json()["runs"]
    schema = app.openapi()["components"]["schemas"]["RunSummary"]

    assert all(set(row) == SUMMARY_FIELDS for row in rows if "reason" not in row)
    assert set(schema["properties"]) == SUMMARY_FIELDS


async def test_최근_실행이_먼저_오고_상태_넷이_갈린다(client: AsyncClient) -> None:
    """스크립트가 셋을 같게 다루면 멈춘 실행을 잃어버린다(스토리 10·13)."""
    rows = (await client.get("/traces", headers=BEARER)).json()["runs"]

    assert [row["run_id"] for row in rows] == [row.run_id for row in NEWEST_FIRST]
    assert [row.get("status") for row in rows[:4]] == ["unfinished", "failed", "finished", "paused"]


def test_끝_이벤트가_없는_실행을_진행_중이라_부르지_않는다(app: FastAPI) -> None:
    """돌고 있는 실행과 죽어 사라진 실행이 파일 위에서 똑같이 보인다(스토리 11). 어휘가 계약에
    박히므로 생성 클라이언트도 "진행 중"이라는 값을 모른다."""
    schemas = app.openapi()["components"]["schemas"]

    assert schemas["RunStatus"]["enum"] == ["paused", "finished", "failed", "unfinished"]


async def test_형식_1_실행도_목록에_나오고_요약이_형식_버전을_싣는다(client: AsyncClient) -> None:
    """화면이 "이 실행은 재개할 수 없다"를 말할 수 있다(스토리 17)."""
    rows = (await client.get("/traces", headers=BEARER)).json()["runs"]

    legacy = next(row for row in rows if row["run_id"] == LEGACY.run_id)
    assert legacy["schema_version"] == "1"


async def test_읽을_수_없는_트레이스가_있어도_나머지가_오고_그것은_표지다(
    client: AsyncClient,
) -> None:
    """트레이스 하나가 /traces 전체를 죽이지 않는다(ADR 0012 의 2026-09-22 이력)."""
    response = await client.get("/traces", headers=BEARER)

    assert response.status_code == 200
    rows = response.json()["runs"]
    assert {"run_id": UNREADABLE.run_id, "reason": UNREADABLE.reason} in rows
    assert len(rows) == len(NEWEST_FIRST)


async def test_질의가_없으면_포트가_상태_없이_기본_개수로_첫_쪽을_받는다(
    client: AsyncClient, traces: FakeTrace
) -> None:
    """셋 다 선택이고 status 가 없으면 전부다. 기본 개수는 계약에 박힌 그 숫자다."""
    await client.get("/traces", headers=BEARER)

    assert traces.calls == [ListCall(status=None, limit=DEFAULT_LIMIT, after=None)]


async def test_status_limit_after_가_포트에_그대로_전달된다(
    client: AsyncClient, traces: FakeTrace
) -> None:
    first = await client.get("/traces", params={"limit": "2"}, headers=BEARER)
    cursor = first.json()["next_cursor"]

    await client.get(
        "/traces", params={"status": "paused", "limit": "3", "after": cursor}, headers=BEARER
    )

    assert traces.calls[-1] == ListCall(status="paused", limit=3, after=cursor_of(FAILED))


async def test_status_paused_가_곧_멈춘_실행_목록이다(client: AsyncClient) -> None:
    """승인자가 멈춘 실행을 찾는 길이 이 질의 하나다(스토리 22). 표지는 상태가 없어 섞이지
    않는다."""
    response = await client.get("/traces", params={"status": "paused"}, headers=BEARER)

    assert response.status_code == 200
    assert _run_ids(response) == [PAUSED.run_id]


async def test_멈춘_실행에_별도_경로가_없다(
    app: FastAPI, client: AsyncClient, traces: FakeTrace
) -> None:
    """상태는 요약의 한 필드이지 다른 자원이 아니다(스토리 23). 경로를 두면 `paused` 라는 실행
    식별자가 생길 수 없게 되고 상태가 늘 때마다 경로가 는다. 그 경로는 상세이고 `paused` 는 그냥
    실행 식별자다."""
    response = await client.get("/traces/paused", headers=BEARER)

    assert "/traces/paused" not in _documented_paths(app)
    assert response.status_code == 404
    assert traces.calls == []
    assert traces.reads == ["paused"]


async def test_잘못된_status_는_422이고_포트가_불리지_않는다(
    client: AsyncClient, traces: FakeTrace
) -> None:
    for status in ("running", "in_progress", "PAUSED", ""):
        response = await client.get("/traces", params={"status": status}, headers=BEARER)

        assert response.status_code == 422, status
        fields = [violation["field"] for violation in response.json()["violations"]]
        assert fields == ["query.status"], status
    assert traces.calls == []


async def test_영_이하이거나_상한을_넘는_limit_은_422이고_포트가_불리지_않는다(
    client: AsyncClient, traces: FakeTrace
) -> None:
    """상한이 없으면 요청 하나가 "실행이 쌓여도 응답이 그만큼 커지지 않는다"를 무력화한다."""
    for limit in ("0", "-1", str(MAX_LIMIT + 1), "many"):
        response = await client.get("/traces", params={"limit": limit}, headers=BEARER)

        assert response.status_code == 422, limit
        fields = [violation["field"] for violation in response.json()["violations"]]
        assert fields == ["query.limit"], limit
    assert traces.calls == []


async def test_limit_의_경계값은_받는다(client: AsyncClient, traces: FakeTrace) -> None:
    for limit in (1, MAX_LIMIT):
        response = await client.get("/traces", params={"limit": str(limit)}, headers=BEARER)

        assert response.status_code == 200, limit
    assert [call.limit for call in traces.calls] == [1, MAX_LIMIT]


def test_limit_의_기본값과_상한이_계약에_박힌다(app: FastAPI) -> None:
    """숫자는 core 가 소유하고 질의 검증과 openapi.json 이 그것을 읽는다
    (`.claude/rules/core.md`)."""
    parameters = app.openapi()["paths"]["/traces"]["get"]["parameters"]
    limit = next(parameter for parameter in parameters if parameter["name"] == "limit")

    assert limit["schema"]["default"] == DEFAULT_LIMIT
    assert limit["schema"]["minimum"] == 1
    assert limit["schema"]["maximum"] == MAX_LIMIT


# 형식에 맞지 않는 커서들. 앞의 넷은 문자 집합과 길이에서, 뒤의 것들은 해독과 검증에서 걸린다. 둘 다
# 포트에 닿기 전에 끝나야 한다 — 없으면 조작된 커서가 처리되지 않은 500 이 된다.
MALFORMED_AFTER = (
    "",
    "!!!!",
    "../../etc",
    "a" * 257,
    "a",  # base64 로 해독되지 않는 길이
    _opaque("not json"),
    _opaque("[]"),
    _opaque('{"started_at":null}'),  # 식별자가 빠졌다
    _opaque('{"started_at":null,"run_id":"../x"}'),  # 식별자 패턴 위반
    _opaque('{"started_at":"2026-09-23T12:00:00","run_id":"r1"}'),  # 시간대가 없다
    _opaque('{"started_at":"not-a-time","run_id":"r1"}'),
    _opaque('{"started_at":null,"run_id":"r1","offset":3}'),  # 모르는 필드
)


async def test_형식에_맞지_않는_after_는_422이고_포트가_불리지_않는다(
    client: AsyncClient, traces: FakeTrace
) -> None:
    """04·06 이 경로 파라미터에 거는 것과 같은 종류의 검증이다. violations 가 after 를 가리켜야
    검증이 실제로 돌았다는 것까지 본다."""
    for after in MALFORMED_AFTER:
        response = await client.get("/traces", params={"after": after}, headers=BEARER)

        assert response.status_code == 422, after
        assert response.json()["code"] == "invalid_request", after
        fields = [violation["field"] for violation in response.json()["violations"]]
        assert fields == ["query.after"], after
    assert traces.calls == []


async def test_받은_행이_limit_개보다_적으면_다음_커서가_null_이다(client: AsyncClient) -> None:
    response = await client.get("/traces", params={"limit": str(MAX_LIMIT)}, headers=BEARER)

    assert response.json()["next_cursor"] is None


async def test_딱_떨어지면_다음_쪽이_비고_그때_커서가_null_이다(client: AsyncClient) -> None:
    """포트에 limit 을 그대로 넘기므로 하나 더 읽어 끝을 미리 볼 수 없다. 대가는 요청 하나다."""
    size = str(len(NEWEST_FIRST))
    full = await client.get("/traces", params={"limit": size}, headers=BEARER)
    after = full.json()["next_cursor"]
    rest = await client.get("/traces", params={"limit": size, "after": after}, headers=BEARER)

    assert after is not None
    assert rest.json() == {"runs": [], "next_cursor": None}


async def test_다음_커서가_마지막_행의_정렬_키를_잃지_않고_포트에_되돌아간다(
    client: AsyncClient, traces: FakeTrace
) -> None:
    """마이크로초와 UTC 가 아닌 오프셋과 시각 없는 표지까지. 하나라도 잃으면 경계의 행이 두 번
    오거나 빠진다."""
    seoul = timezone(timedelta(hours=9))
    precise = dataclasses.replace(
        FAILED, started_at=datetime(2026, 9, 23, 21, 4, 0, 123456, tzinfo=seoul)
    )
    traces.rows = [precise, UNREADABLE]

    first = await client.get("/traces", params={"limit": "1"}, headers=BEARER)
    second = await client.get(
        "/traces", params={"limit": "1", "after": first.json()["next_cursor"]}, headers=BEARER
    )
    await client.get(
        "/traces", params={"limit": "1", "after": second.json()["next_cursor"]}, headers=BEARER
    )

    afters = [call.after for call in traces.calls]
    assert afters == [None, cursor_of(precise), cursor_of(UNREADABLE)]
    returned = afters[1]
    assert returned is not None
    assert returned.started_at is not None
    assert returned.started_at.utcoffset() == timedelta(hours=9)


async def test_포트가_받는_커서의_시각대는_pydantic_의_것이_아니라_표준_라이브러리의_것이다(
    client: AsyncClient, traces: FakeTrace
) -> None:
    """서드파티 타입이 경계를 넘어 core 의 값에 실리지 않는다(`CODING_STANDARDS.md`). pydantic 이
    JSON 에서 만든 시각은 pydantic-core 의 `TzInfo` 를 든다. 그것이 인터프리터 종료까지 살아 있으면
    종료 중 GC 가 그 해제에서 세그폴트를 낸다 — FastAPI 가 라우트 함수를 모듈 전역 캐시에 두어 그
    클로저가 붙잡은 포트(여기서는 이 가짜)가 프로세스 끝까지 살기 때문이다(PR #78 의 CI, 종료 코드
    139)."""
    seoul = timezone(timedelta(hours=9))
    traces.rows = [
        dataclasses.replace(FAILED, started_at=datetime(2026, 9, 23, 21, 4, tzinfo=seoul)),
        UNREADABLE,
    ]

    first = await client.get("/traces", params={"limit": "1"}, headers=BEARER)
    await client.get(
        "/traces", params={"limit": "1", "after": first.json()["next_cursor"]}, headers=BEARER
    )

    returned = traces.calls[-1].after
    assert returned is not None
    assert returned.started_at is not None
    assert type(returned.started_at.tzinfo) is timezone
    assert returned.started_at.utcoffset() == timedelta(hours=9)


async def test_쪽_사이에_새_실행이_생겨도_같은_항목이_두_번_오거나_건너뛰지_않는다(
    client: AsyncClient, traces: FakeTrace
) -> None:
    """오프셋과 커서를 가르는 성질이다(스토리 33). 정적인 목록으로는 재지 못한다 — 오프셋도 목록이
    그대로면 겹치지도 빠지지도 않는다."""
    everything = _run_ids(await client.get("/traces", headers=BEARER))

    first = await client.get("/traces", params={"limit": "2"}, headers=BEARER)
    newest = _summary("f00d4e5b", "unfinished", started=timedelta(hours=1), last=timedelta(hours=1))
    traces.rows = [*traces.rows, newest]
    seen = _run_ids(first)
    cursor = first.json()["next_cursor"]
    while cursor is not None:
        page = await client.get("/traces", params={"limit": "2", "after": cursor}, headers=BEARER)
        seen.extend(_run_ids(page))
        cursor = page.json()["next_cursor"]

    assert seen == everything
    assert _run_ids(await client.get("/traces", headers=BEARER)) == [newest.run_id, *everything]


async def test_응답의_실행_식별자가_패턴을_만족하고_계약에_박힌다(
    app: FastAPI, client: AsyncClient
) -> None:
    """그대로 `agent-os resume` 에도 `/traces/{run_id}` 에도 넘길 수 있다(스토리 24)."""
    rows = (await client.get("/traces", headers=BEARER)).json()["runs"]
    schemas = app.openapi()["components"]["schemas"]

    assert all(is_run_id(row["run_id"]) for row in rows)
    assert schemas["RunSummary"]["properties"]["run_id"]["pattern"] == RUN_ID_PATTERN
    assert schemas["UnreadableTrace"]["properties"]["run_id"]["pattern"] == RUN_ID_PATTERN


async def test_패턴을_어기는_식별자는_응답에_실리지_않는다(
    client: AsyncClient, traces: FakeTrace
) -> None:
    """어댑터는 그런 이름의 파일을 목록에서 뺀다. 그래도 새면 계약을 어긴 응답 대신 500 이다."""
    traces.rows = [dataclasses.replace(PAUSED, run_id=RunId("../escaped"))]

    response = await client.get("/traces", headers=BEARER)

    assert response.status_code == 500
    assert "../escaped" not in response.text


def test_다음_커서의_모양이_계약에_박힌다(app: FastAPI) -> None:
    """불투명 문자열이고 문자 집합과 길이만 약속한다. 클라이언트는 받은 것을 되돌려 줄 뿐이라
    정렬 키를 바꾸는 날에도 이 약속은 그대로다."""
    document = app.openapi()
    parameters = document["paths"]["/traces"]["get"]["parameters"]
    after = next(parameter for parameter in parameters if parameter["name"] == "after")
    next_cursor = document["components"]["schemas"]["TracePage"]["properties"]["next_cursor"]
    opaque = {"type": "string", "pattern": CURSOR_PATTERN}

    assert opaque in after["schema"]["anyOf"]
    assert opaque in next_cursor["anyOf"]


def test_트레이스_목록의_타입이_이름_있는_스키마다(app: FastAPI) -> None:
    """생성 클라이언트가 익명 구조체 대신 이 이름들을 받는다(스토리 28)."""
    document = app.openapi()
    schemas = document["components"]["schemas"]
    ok = document["paths"]["/traces"]["get"]["responses"]["200"]

    assert ok["content"]["application/json"]["schema"] == {"$ref": "#/components/schemas/TracePage"}
    assert schemas["TracePage"]["properties"]["runs"]["items"] == {
        "$ref": "#/components/schemas/RunRow"
    }
    assert schemas["RunRow"] == {
        "anyOf": [
            {"$ref": "#/components/schemas/RunSummary"},
            {"$ref": "#/components/schemas/UnreadableTrace"},
        ]
    }
    assert {"RunStatus", "TraceSchemaVersion"} <= set(schemas)


def test_늘_실리는_트레이스_목록_필드는_계약에서도_required_다(app: FastAPI) -> None:
    """next_cursor 가 null 일 수 있어도 키는 언제나 있다. 선택 필드로 보이면 생성 클라이언트가
    "키가 없음"과 "마지막 쪽"을 가르는 코드를 따로 짠다."""
    schemas = app.openapi()["components"]["schemas"]

    assert set(schemas["TracePage"]["required"]) == {"runs", "next_cursor"}
    assert set(schemas["RunSummary"]["required"]) == SUMMARY_FIELDS
    assert set(schemas["UnreadableTrace"]["required"]) == {"run_id", "reason"}


def test_트레이스_목록의_HTTP_모양이_core_의_요약과_표지와_같은_필드를_든다() -> None:
    """관리 쪽 모델이 core 의 것을 옮긴 것이라 필드 목록이 두 곳이다. core 에 필드가 늘면 여기가
    빨개져 관리 쪽이 조용히 뒤처지지 않는다."""
    assert set(admin_traces.RunSummary.model_fields) == {
        field.name for field in dataclasses.fields(RunSummary)
    }
    assert set(admin_traces.UnreadableTrace.model_fields) == {
        field.name for field in dataclasses.fields(UnreadableTrace)
    }


# 트레이스 상세 — 무엇이 어긋났는지 되짚는 자리(티켓 06)


def _expected_json(event: Event | UnknownEvent) -> dict[str, object]:
    """이벤트 하나가 응답에서 보여야 하는 모양. 아는 종류는 sdk 의 직렬화 그대로이고 모르는 종류는
    판별자와 원문 문자열을 나란히 든 표지다(ADR 0010 의 2026-09-22 이력)."""
    if isinstance(event, UnknownEvent):
        return {"type": "unknown", "raw": event.raw}
    return event.model_dump(mode="json")


async def test_트레이스_상세가_한_실행의_이벤트를_쓴_순서_그대로_돌려준다(
    client: AsyncClient,
) -> None:
    """무엇이 어긋났는지 되짚는 자리다(스토리 16). 승인자는 무엇을 승인해 달라는지를 목록이 아니라
    여기서 본다(스토리 25) — 마지막 이벤트가 멈춘 도구와 그 인자를 든다."""
    response = await client.get(f"/traces/{PAUSED.run_id}", headers=BEARER)

    assert response.status_code == 200
    body = response.json()
    assert body == {
        "run_id": PAUSED.run_id,
        "schema_version": "2",
        "events": [_expected_json(event) for event in PAUSED_EVENTS],
    }
    assert body["events"][-1]["tool"] == "add"
    assert body["events"][-1]["args"] == {"a": 2, "b": 3}


async def test_모르는_종류의_이벤트가_판별자를_달고_원문_문자열_그대로_실린다(
    client: AsyncClient,
) -> None:
    """빼면 화면이 실행에 대해 거짓말을 하고, 그 줄이 곧 재개 불가의 원인이다. 원문을 펼쳐 판별자를
    얹지 않는다 — 원문이 이미 `type` 을 들고 있어 덮어쓰게 된다(ADR 0010 의 2026-09-22 이력)."""
    events = (await client.get(f"/traces/{PAUSED.run_id}", headers=BEARER)).json()["events"]

    unknown = events[2]
    assert unknown == {"type": "unknown", "raw": FUTURE_LINE}
    assert json.loads(unknown["raw"])["type"] == "run_rewound"


async def test_형식_1_트레이스도_상세가_읽히고_형식_버전을_싣는다(client: AsyncClient) -> None:
    """읽기는 되고 재개만 안 된다. 목록을 거치지 않고 상세로 곧장 들어온 화면도 "이 실행은 재개할
    수 없다"를 말할 수 있다(스토리 17)."""
    response = await client.get(f"/traces/{LEGACY.run_id}", headers=BEARER)

    assert response.status_code == 200
    assert response.json()["schema_version"] == "1"
    assert response.json()["events"] == [_expected_json(event) for event in LEGACY_TRACE.events]


async def test_없는_실행은_404이고_code_가_not_found_다(
    client: AsyncClient, traces: FakeTrace
) -> None:
    """내 오타와 서버의 문제가 갈린다(스토리 18). 포트가 불렸는지 보는 이유는 라우트가 없어도 같은
    404 가 나기 때문이다 — 포트가 None 이라고 답한 404 여야 한다."""
    response = await client.get("/traces/0000dead", headers=BEARER)

    assert response.status_code == 404
    assert response.json()["code"] == "not_found"
    assert traces.reads == ["0000dead"]


async def test_읽을_수_없는_트레이스는_목록에서는_표지이고_단건으로는_500이다(
    client: AsyncClient,
) -> None:
    """4xx 면 운영자가 잘못 요청했다고 믿고 깨진 파일을 못 찾는다(스토리 19). 명세의 상태 코드 표는
    PluginError 를 매니페스트로만 적었지만 ADR 0012 의 2026-09-22 이력이 트레이스로 넓혔다.

    쓰는 중인 파일은 여기 오지 않는다. 개행으로 끝나지 않은 마지막 줄은 아직 쓰이지 않은 것이라
    어댑터가 그 앞 줄까지 돌려주고, 그것은 이 라우트에서 200 이다(ADR 0012 의 2026-09-23 이력 둘째,
    `tests/adapters/test_jsonl.py`)."""
    rows = (await client.get("/traces", headers=BEARER)).json()["runs"]
    single = await client.get(f"/traces/{UNREADABLE.run_id}", headers=BEARER)

    assert {"run_id": UNREADABLE.run_id, "reason": UNREADABLE.reason} in rows
    assert single.status_code == 500
    body = single.json()
    assert set(body) == {"code", "message", "violations", "request_id"}
    assert body["code"] == "internal_error"
    assert "traces/c2f85a90.jsonl" in body["message"]


async def test_루트를_벗어나려는_실행_식별자는_422이고_포트가_아예_불리지_않는다(
    client: AsyncClient, traces: FakeTrace
) -> None:
    """`traces/{run_id}.jsonl` 로 그대로 조립되므로 하나라도 포트에 닿으면 루트 밖을 읽는다. 404 와
    500 이 갈리는 것 자체가 임의 경로의 파일 존재 오라클이다. CLI 에서는 argv 라 신뢰 경계 안이던
    값을 HTTP 가 원격 입력으로 바꾼다. 개행과 길이도 같은 판정자가 본다."""
    for run_id in (*ESCAPING_NAMES, "7c1e2d9a%0A", "%0A7c1e2d9a", "7c1e%0A2d9a", "a" * 65):
        response = await client.get(f"/traces/{run_id}", headers=BEARER)

        assert response.status_code == 422, run_id
        fields = [violation["field"] for violation in response.json()["violations"]]
        assert fields == ["path.run_id"], run_id
    assert traces.reads == []


def test_경로에_거는_실행_식별자_패턴이_sdk_의_그것이고_계약에_박힌다(app: FastAPI) -> None:
    """`RunId` 는 제약 없는 NewType 이라 런타임 검증이 0 이다. 패턴은 목록이 내는 식별자에 거는 것과
    같은 것이라, 목록에서 얻은 식별자를 그대로 넘길 수 있다(스토리 24)."""
    parameters = app.openapi()["paths"]["/traces/{run_id}"]["get"]["parameters"]
    run_id = next(parameter for parameter in parameters if parameter["name"] == "run_id")

    assert run_id["schema"]["pattern"] == RUN_ID_PATTERN


def test_트레이스_상세의_타입이_이름_있는_판별_유니온이다(app: FastAPI) -> None:
    """생성 클라이언트가 `type` 하나로 항목을 가른다. 모르는 종류의 표지가 같은 판별자를 달고 한
    유니온에 들어간다(스토리 28, ADR 0010 의 2026-09-22 이력)."""
    document = app.openapi()
    schemas = document["components"]["schemas"]
    ok = document["paths"]["/traces/{run_id}"]["get"]["responses"]["200"]

    assert ok["content"]["application/json"]["schema"] == {"$ref": "#/components/schemas/Trace"}
    assert schemas["Trace"]["properties"]["events"]["items"] == {
        "$ref": "#/components/schemas/TraceEvent"
    }
    discriminator = schemas["TraceEvent"]["discriminator"]
    assert discriminator["propertyName"] == "type"
    assert discriminator["mapping"]["unknown"] == "#/components/schemas/UnknownEvent"


def test_모르는_종류의_판별자가_실제_이벤트_종류와_겹치지_않고_sdk_의_이벤트를_빠뜨리지_않는다(
    app: FastAPI,
) -> None:
    """겹치면 생성 클라이언트가 그 값의 항목을 어느 쪽으로 읽을지 모른다. 상세의 유니온이 sdk 의
    이벤트를 하나라도 빠뜨리면 그 종류가 여기서 읽히지 않는다."""
    sdk_types = set(TypeAdapter[Event](Event).json_schema()["discriminator"]["mapping"])
    mapping = app.openapi()["components"]["schemas"]["TraceEvent"]["discriminator"]["mapping"]

    assert "unknown" not in sdk_types
    assert set(mapping) == sdk_types | {"unknown"}


def test_늘_실리는_이벤트_필드는_계약에서도_required_다(app: FastAPI) -> None:
    """서버는 이벤트의 필드를 언제나 전부 싣는다. 기본값 있는 필드가 required 에서 빠지면 생성
    클라이언트가 판별자 `type` 까지 선택 필드로 받아 그것으로 항목을 가르지 못한다."""
    schemas = app.openapi()["components"]["schemas"]
    mapping = schemas["TraceEvent"]["discriminator"]["mapping"]

    for reference in mapping.values():
        name = str(reference).rsplit("/", 1)[-1]
        assert set(schemas[name]["required"]) == set(schemas[name]["properties"]), name
    assert set(schemas["Trace"]["required"]) == {"run_id", "schema_version", "events"}
    assert set(schemas["UnknownEvent"]["required"]) == {"type", "raw"}


def test_이벤트의_스키마가_전부_한_줄_설명을_싣는다(app: FastAPI) -> None:
    """이벤트가 계약에 박히므로 독스트링이 곧 생성 클라이언트의 문서다. 없으면 그 종류만 문서 없이
    나가고, 여러 줄이면 주석을 다듬는 것이 계약 변경으로 보인다(`.claude/rules/sdk.md`, PR #63 의
    claude-review 가 설명이 빠진 셋을 찾았다)."""
    schemas = app.openapi()["components"]["schemas"]
    mapping = schemas["TraceEvent"]["discriminator"]["mapping"]

    for reference in mapping.values():
        name = str(reference).rsplit("/", 1)[-1]
        description = str(schemas[name].get("description", ""))
        assert description, name
        assert "\n" not in description, name


def test_트레이스_상세의_HTTP_모양이_core_의_트레이스와_같은_필드를_든다() -> None:
    """관리 쪽 모델이 core 의 것을 옮긴 것이라 필드 목록이 두 곳이다. core 에 필드가 늘면 여기가
    빨개져 관리 쪽이 조용히 뒤처지지 않는다. 표지만 판별자 하나를 더 든다."""
    assert set(admin_traces.Trace.model_fields) == {
        field.name for field in dataclasses.fields(Trace)
    }
    assert set(admin_traces.UnknownEvent.model_fields) == {
        field.name for field in dataclasses.fields(UnknownEvent)
    } | {"type"}
