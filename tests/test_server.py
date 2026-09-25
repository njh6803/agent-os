"""주 이음매. create_app() 이 만든 앱에 ASGI 로 요청을 넣고 바깥 행동만 단언한다.

바탕으로 재는 것은 셋이다 — 모든 라우트가 보호를 켜지 않아도 기본으로 막힌다는 것, 에러가 언제나
같은 봉투로 나간다는 것, 인증 없이 경계 밖으로 나가는 응답이 /health 하나뿐이라는 것. 그 위에
데이터 라우트가 하나씩 붙는다. 플러그인 둘과 트레이스 목록과 상세가 파일 끝에 있다.

가짜 포트는 상속하지 않고 시그니처로 만족하며 픽스처가 포트 타입으로 annotate 한다. 그 한 줄이
포트 적합성이 검증되는 자리다. 네트워크도 디스크도 타지 않는다.
"""

import base64
import dataclasses
import inspect
import io
import json
from collections.abc import AsyncIterator, Mapping, Sequence
from datetime import UTC, datetime, timedelta, timezone
from typing import get_type_hints

import httpx
import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import TypeAdapter

from agent_os import server as server_module
from agent_os.admin import http as admin_http
from agent_os.admin import traces as admin_traces
from agent_os.admin.http import Health
from agent_os.admin.traces import CURSOR_PATTERN
from agent_os.core.ports import (
    DEFAULT_LIMIT,
    MAX_LIMIT,
    Absent,
    Cursor,
    ManifestRow,
    NotResumable,
    PluginError,
    PluginSource,
    RunRow,
    RunStatus,
    RunSummary,
    ToolSource,
    Trace,
    TraceSchemaVersion,
    TraceStore,
    UnknownEvent,
    UnreadableManifest,
    UnreadableTrace,
    cursor_of,
    order_key,
)
from agent_os.http.auth import PUBLIC_PATHS
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
# 채널 쪽의 같은 대조. 03·04 가 붙일 `/runs` 와 `/runs/{run_id}/approval` 을 쓰지 않는 이유는
# 라우트가 붙는 순간 404 가 바뀌어 그 티켓이 이 테스트에 막히기 때문이다. 이 경로는 그 둘 어느
# 것에도 맞지 않는다. 실행 식별자 하나로 끝나는 라우트(`/runs/{run_id}`)를 더하는 티켓은 이 경로가
# 그 라우트에 닿는지 다시 본다 — `verbatim` 변환기는 슬래시까지 잡는다.
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
    """디렉터리 대신 행 목록을 든다. 부른 횟수를 세어 검증이 포트보다 먼저 끝나는지 본다.

    읽히지 않는 행에는 어댑터와 같은 비대칭으로 답한다 — 목록에서는 표지, 단건에서는 PluginError.
    어댑터가 실제로 그렇게 답한다는 것은 `tests/adapters/test_filesystem.py` 가 잰다.
    """

    def __init__(self, rows: Sequence[ManifestRow] = ()) -> None:
        self._rows = tuple(rows)
        self.calls = 0

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


@pytest.fixture
def stderr() -> io.StringIO:
    """서버 표준 에러. 실패 하나가 남기는 한 줄을 테스트가 읽는 자리다."""
    return io.StringIO()


@pytest.fixture
def plugins() -> FakePlugins:
    """종류 넷에 하나 이상씩과 읽을 수 없는 것 하나. 행 순서는 어댑터처럼 종류 안에서 이름순이다."""
    return FakePlugins(rows=(BROKEN, CALC, EVERYTHING, SUMMARIZE, SONNET))


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
    source: PluginSource = plugins
    trace: TraceStore = traces
    return create_app(
        plugins=source,
        trace=trace,
        admin_token=TOKEN,
        channel_token=CHANNEL_TOKEN,
        stderr=stderr,
    )


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


async def test_허용되지_않는_메서드도_봉투이고_어휘가_다섯_안에_있다(client: AsyncClient) -> None:
    """405 는 프레임워크가 내는 것이라 표에 없다. 어휘를 다섯으로 지키려고 계열로 접는다."""
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
    plugins: PluginSource = FakePlugins()
    trace: TraceStore = FakeTrace()

    with pytest.raises(ValueError):
        create_app(
            plugins=plugins,
            trace=trace,
            admin_token=admin_token,
            channel_token=channel_token,
            stderr=stderr,
        )


# 채널 토큰 — `/runs` 아래는 채널 토큰만, 그 밖은 관리 토큰만 연다(티켓 02, ADR 0015)


def _under_channel(path: str) -> bool:
    """전수 검사가 관리 경로를 고르는 기준이고 경로 조각 단위다. 미들웨어의 규칙을 여기서 다시
    적은 것이라, 둘이 같은 규칙이라는 것은 `/runsx` 대조가 잰다."""
    return path == "/runs" or path.startswith("/runs/")


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


async def test_관리_경로_전부가_채널_토큰으로_401이다(app: FastAPI, client: AsyncClient) -> None:
    """위젯에 준 토큰으로 모든 실행의 트레이스를 읽지 못한다(스토리 52). 채널 쪽 전수 열거는 채널
    라우트가 생기는 03 이 같은 가드와 함께 더한다."""
    documented = _documented_paths(app)
    admin_paths = [
        path for path in documented if path not in PUBLIC_PATHS and not _under_channel(path)
    ]
    assert admin_paths, "관리 경로가 없으면 이 전수 검사는 401 을 한 번도 재지 않는다"

    for path in admin_paths:
        response = await client.get(path, headers=CHANNEL_BEARER)
        assert response.status_code == 401, path


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


def test_에러_봉투의_code_어휘가_상태_코드와_1대1인_다섯이다(app: FastAPI) -> None:
    """어휘가 openapi.json 에 박힌다. 슬라이스 3 이 에러 처리를 한 곳에서 받는 근거다. 다섯째인
    conflict 는 채널이 재개할 수 없는 실행에 내는 409 다(ADR 0010 의 2026-09-24 이력)."""
    schemas = app.openapi().get("components", {}).get("schemas", {})

    assert set(schemas["ErrorCode"]["enum"]) == {
        "unauthorized",
        "invalid_request",
        "not_found",
        "conflict",
        "internal_error",
    }


def test_create_app_이_도구_포트를_받지_않는다() -> None:
    """조회가 MCP 서버를 띄우는 것이 구조적으로 불가능하다(스토리 7)."""
    parameters = inspect.signature(create_app).parameters

    assert "tools" not in parameters
    assert ToolSource not in get_type_hints(create_app).values()


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


async def test_목록의_항목이_매니페스트_그대로라_승인_대상_도구가_보인다(
    client: AsyncClient,
) -> None:
    """가드레일의 범위를 코드를 읽지 않고 안다(스토리 3). interrupts 가 필드로 닫은 것을 읽는
    면이다."""
    rows = (await client.get("/plugins", headers=BEARER)).json()

    calc = next(row for row in rows if row["name"] == "calc")
    assert calc == CALC.model_dump(mode="json")
    assert calc["requires_approval"] == ["add"]


async def test_mcp_매니페스트의_command_와_args_도_가리지_않고_내보낸다(
    client: AsyncClient,
) -> None:
    """가리지 않는 것이 결정이고 경계는 인증이다(ADR 0009 의 2026-09-22 이력, 네 번째 열린 문제).

    MCP 구성을 디버깅하는 사람이 정확히 이 둘을 봐야 한다. 가리는 날에는 이 테스트가 먼저 바뀐다.
    """
    rows = (await client.get("/plugins", headers=BEARER)).json()

    everything = next(row for row in rows if row["name"] == "everything")
    assert everything["server"]["command"] == "npx"
    assert everything["server"]["args"] == ["-y", "@modelcontextprotocol/server-everything"]


async def test_읽을_수_없는_매니페스트가_있어도_나머지가_오고_그것은_종류_이름_이유를_든_표지다(
    client: AsyncClient,
) -> None:
    """조용히 빠지면 등록했다고 믿는 것과 실제가 어긋나고, 전체가 실패하면 무엇이 살아 있는지조차
    모른다(스토리 5·6)."""
    response = await client.get("/plugins", headers=BEARER)

    assert response.status_code == 200
    rows = response.json()
    assert {
        "kind": "agent",
        "name": "broken",
        "reason": "매니페스트를 읽을 수 없다: plugins/agents/broken/plugin.toml",
    } in rows
    assert {row["name"] for row in rows} == {"broken", "calc", "everything", "summarize", "sonnet"}


async def test_플러그인_하나를_물으면_매니페스트를_통째로_돌려준다(client: AsyncClient) -> None:
    """목록이 말해 주지 않는 세부를 확인하는 자리다(스토리 4)."""
    response = await client.get("/plugins/agent/calc", headers=BEARER)

    assert response.status_code == 200
    assert response.json() == CALC.model_dump(mode="json")


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
    assert "404" in document["paths"]["/traces/{run_id}"]["get"]["responses"]
    assert "HTTPValidationError" not in document["components"]["schemas"]


def test_표지의_HTTP_모양이_core_의_표지와_같은_필드를_든다() -> None:
    """관리 쪽 모델이 core 의 표지를 옮긴 것이라 필드 목록이 두 곳이다. core 에 필드가 늘면 여기가
    빨개져 관리 쪽이 조용히 뒤처지지 않는다. 매니페스트에 별도 타입을 두지 않은 이유가 이것이다
    (ADR 0010 의 2026-09-23 이력)."""
    assert set(admin_http.UnreadableManifest.model_fields) == {
        field.name for field in dataclasses.fields(UnreadableManifest)
    }


def test_늘_실리는_매니페스트_필드는_계약에서도_required_다(app: FastAPI) -> None:
    """서버는 필드를 언제나 전부 싣는다. 기본값 있는 필드가 required 에서 빠지면 생성 클라이언트가
    `requires_approval` 을 선택 필드로 받는다 — 이 티켓이 보이려는 바로 그 필드다."""
    schemas = app.openapi()["components"]["schemas"]

    assert set(schemas["PluginManifest"]["required"]) == set(PluginManifest.model_fields)
    assert set(schemas["McpServer"]["required"]) == set(McpServer.model_fields)
    assert set(schemas["UnreadableManifest"]["required"]) == {"kind", "name", "reason"}


def test_플러그인_목록의_행_타입이_이름_있는_스키마다(app: FastAPI) -> None:
    """생성 클라이언트가 익명 유니온 대신 이름 있는 타입을 받는다(스토리 28)."""
    document = app.openapi()
    schemas = document["components"]["schemas"]
    ok = document["paths"]["/plugins"]["get"]["responses"]["200"]
    items = ok["content"]["application/json"]["schema"]["items"]

    assert items == {"$ref": "#/components/schemas/PluginRow"}
    assert schemas["PluginRow"] == {
        "anyOf": [
            {"$ref": "#/components/schemas/PluginManifest"},
            {"$ref": "#/components/schemas/UnreadableManifest"},
        ]
    }


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
