"""쿠키로 로그인한 운영자가 `/runs` 를 부르면 그 트레이스에 계정 이름이 남는다(명세 admin-login
"이벤트의 두 칸"). 공유 토큰으로 부르면 두 칸이 빈다.

계정 저장소는 시험마다 복제한 진짜 데이터베이스이고, 계정을 서버 명령 대신 포트로 넣고 로그인
경로를 실제로 불러 쿠키를 받는다. 기준 주소는 `https://admin.test` 다(httpx 는 `http` 에서
`Secure` 쿠키를 싣지 않는다). 쿠키는 보관통에 맡기지 않고 `Cookie` 머리로 직접 싣는다. 요청마다
어느 자격이 실렸는지가 단언의 대상이기 때문이다.

실행은 `tests/channel/http/test_router.py` 의 가짜 플러그인과 가짜 트레이스를 쓴다. 트레이스에서
이벤트를 직접 읽어 칸을 본다.
"""

from __future__ import annotations

import io
from collections.abc import AsyncGenerator, AsyncIterator, Mapping
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient, Response
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from tests.channel.http.test_router import FakePlugins, FakeTrace, ScopedTools
from tests.fake_database import FakeDatabase
from tests.fake_models import DEFAULT_MODEL, FakeModels
from tools.database_for_tests import ScopedDatabase

from agent_os.adapters.postgres.database import PostgresDatabase, parse_database_url
from agent_os.http import permissions as permissions_module
from agent_os.http.accounts import AccountStore, Tier
from agent_os.http.login_tokens import ACCESS_COOKIE, LoginDurations
from agent_os.http.passwords import hash_password
from agent_os.http.permissions import PERMISSION_TABLE, Permission
from agent_os.http.sites import Sites
from agent_os.sdk import (
    ApprovalDenied,
    ApprovalGranted,
    Json,
    Principal,
    RunId,
    RunStarted,
)
from agent_os.server import create_app

NOW = datetime(2026, 11, 26, 9, 0, tzinfo=UTC)
PASSWORD = "Correct-horse-9!"
ADMIN_TOKEN = "adm1n-t0ken-that-only-tests-know"
CHANNEL_TOKEN = "channel-t0ken-that-only-tests-know"
SHARED = {"Authorization": f"Bearer {CHANNEL_TOKEN}"}
APPROVE: Mapping[str, Json] = {"decision": "approve", "pause_index": 1}
DENY: Mapping[str, Json] = {"decision": "deny", "reason": "너무 크다", "pause_index": 1}


class _Clock:
    """시각은 멈춰 있고 실행 식별자만 차례로 낸다. 짧은 JWT 의 수명이 시험 도중 끝나지 않는다."""

    def __init__(self) -> None:
        self._issued = 0

    def now(self) -> datetime:
        return NOW

    def new_run_id(self) -> RunId:
        self._issued += 1
        return RunId(f"run-{self._issued}")


@dataclass(frozen=True)
class _NewAccount:
    name: str
    tier: Tier
    password_hash: str
    created_at: datetime


def _ignore(_message: str) -> None:
    """기다린다는 알림을 찍지 않는다."""


@pytest_asyncio.fixture
async def accounts(database: ScopedDatabase) -> AsyncIterator[AccountStore]:
    url = parse_database_url(database.address.text_for(database.name))
    assert url is not None
    adapter = PostgresDatabase(url, notice=_ignore)
    store: AccountStore = adapter.accounts()
    try:
        yield store
    finally:
        await adapter.close()


@asynccontextmanager
async def _serving(accounts: AccountStore, trace: FakeTrace) -> AsyncGenerator[AsyncClient]:
    """앱의 수명을 연 채로 민다. 실행이 앱의 수명에서 도므로 테스트 본문에서 연다."""
    app: FastAPI = create_app(
        plugins=FakePlugins(),
        trace=trace,
        models=FakeModels(GenericFakeChatModel(messages=iter(()))),
        default_model=DEFAULT_MODEL,
        tools=ScopedTools(),
        clock=_Clock(),
        principal=Principal("alice"),
        admin_token=ADMIN_TOKEN,
        channel_token=CHANNEL_TOKEN,
        sites=Sites(),
        run_timeout_seconds=None,
        end_user_concurrent_runs=None,
        stderr=io.StringIO(),
        database=FakeDatabase(),
        accounts=accounts,
        login_durations=LoginDurations(),
    )
    transport = ASGITransport(app=app)
    async with (
        app.router.lifespan_context(app),
        AsyncClient(transport=transport, base_url="https://admin.test") as client,
    ):
        yield client


async def _seed(accounts: AccountStore, name: str, tier: Tier) -> None:
    async with accounts.transaction() as work:
        await work.add(
            _NewAccount(name=name, tier=tier, password_hash=hash_password(PASSWORD), created_at=NOW)
        )


async def _logged_in(client: AsyncClient, name: str) -> dict[str, str]:
    """로그인 경로를 실제로 불러 받은 짧은 JWT 를 `Cookie` 머리로 만든다."""
    response = await client.post("/auth/login", json={"name": name, "password": PASSWORD})
    assert response.status_code == 204
    value = ""
    for line in response.headers.get_list("set-cookie"):
        pair = line.partition(";")[0]
        if pair.startswith(f"{ACCESS_COOKIE}="):
            value = pair.partition("=")[2]
    client.cookies.clear()
    assert value
    return {"Cookie": f"{ACCESS_COOKIE}={value}"}


def _started(trace: FakeTrace, run_id: str) -> RunStarted:
    first = trace.events_of(RunId(run_id))[0]
    assert isinstance(first, RunStarted)
    return first


def _decision(trace: FakeTrace, run_id: str) -> ApprovalGranted | ApprovalDenied:
    for event in trace.events_of(RunId(run_id)):
        if isinstance(event, ApprovalGranted | ApprovalDenied):
            return event
    raise AssertionError("결정 이벤트가 없다")


def _start(agent: str) -> dict[str, str]:
    return {"agent": agent, "request": "2+3?"}


async def _decide(
    client: AsyncClient, run_id: str, decision: Mapping[str, Json], **headers: str
) -> Response:
    return await client.post(f"/runs/{run_id}/approval", json=decision, headers=headers)


async def test_쿠키로_시작한_실행의_시작_이벤트에_요청한_계정이_남고_주체는_그대로다(
    accounts: AccountStore,
) -> None:
    await _seed(accounts, "kim.min", "admin")
    trace = FakeTrace()

    async with _serving(accounts, trace) as client:
        cookie = await _logged_in(client, "kim.min")
        response = await client.post("/runs", json=_start("echo"), headers=cookie)

    assert response.status_code == 200
    started = _started(trace, "run-1")
    assert started.requesting_account == "kim.min", (
        f"요청한 계정은 {started.requesting_account!r} 이다"
    )
    # 실행의 주체는 계정이 아니라 `serve` 가 받은 주체다. 두 칸은 서로 다른 것이다
    assert started.principal == "alice"


async def test_시스템_관리자도_관리자도_시작할_수_있고_각자의_이름이_남는다(
    accounts: AccountStore,
) -> None:
    await _seed(accounts, "root.kim", "system_admin")
    await _seed(accounts, "kim.min", "admin")
    trace = FakeTrace()

    async with _serving(accounts, trace) as client:
        root = await _logged_in(client, "root.kim")
        admin = await _logged_in(client, "kim.min")
        first = await client.post("/runs", json=_start("echo"), headers=root)
        second = await client.post("/runs", json=_start("echo"), headers=admin)

    assert (first.status_code, second.status_code) == (200, 200)
    assert _started(trace, "run-1").requesting_account == "root.kim"
    assert _started(trace, "run-2").requesting_account == "kim.min"


async def test_이어_간_실행의_시작_이벤트에는_이어_가기를_보낸_계정이_남는다(
    accounts: AccountStore,
) -> None:
    await _seed(accounts, "kim.min", "admin")
    await _seed(accounts, "lee.sun", "admin")
    trace = FakeTrace()

    async with _serving(accounts, trace) as client:
        kim = await _logged_in(client, "kim.min")
        lee = await _logged_in(client, "lee.sun")
        await client.post("/runs", json=_start("echo"), headers=kim)
        response = await client.post("/runs/run-1/continuation", json=_start("echo"), headers=lee)

    assert response.status_code == 200
    assert _started(trace, "run-1").requesting_account == "kim.min"
    second = _started(trace, "run-2")
    assert second.previous_run == RunId("run-1")
    assert second.requesting_account == "lee.sun"


@pytest.mark.parametrize(("decision", "kind"), [(APPROVE, ApprovalGranted), (DENY, ApprovalDenied)])
async def test_승인이나_거부의_결정_이벤트에_결정한_계정이_남는다(
    accounts: AccountStore, decision: Mapping[str, Json], kind: type
) -> None:
    await _seed(accounts, "kim.min", "admin")
    await _seed(accounts, "lee.sun", "admin")
    trace = FakeTrace()

    async with _serving(accounts, trace) as client:
        kim = await _logged_in(client, "kim.min")
        lee = await _logged_in(client, "lee.sun")
        await client.post("/runs", json=_start("gated"), headers=kim)
        response = await _decide(client, "run-1", decision, **lee)

    assert response.status_code == 200
    event = _decision(trace, "run-1")
    assert isinstance(event, kind)
    # 시작한 계정과 결정한 계정은 다를 수 있고 각각 자기 칸에 남는다
    assert event.deciding_account == "lee.sun", f"결정한 계정은 {event.deciding_account!r} 이다"
    assert _started(trace, "run-1").requesting_account == "kim.min"


async def test_공유_토큰으로_보낸_시작과_이어_가기와_결정은_두_칸이_빈다(
    accounts: AccountStore,
) -> None:
    trace = FakeTrace()

    async with _serving(accounts, trace) as client:
        await client.post("/runs", json=_start("echo"), headers=SHARED)
        await client.post("/runs/run-1/continuation", json=_start("echo"), headers=SHARED)
        await client.post("/runs", json=_start("gated"), headers=SHARED)
        await _decide(client, "run-3", APPROVE, **SHARED)

    for run_id in ("run-1", "run-2", "run-3"):
        account = _started(trace, run_id).requesting_account
        assert account is None, f"공유 토큰의 요청한 계정은 {account!r} 이다"
    assert _decision(trace, "run-3").deciding_account is None


async def test_쿠키와_공유_토큰이_함께_와도_공유_토큰으로_본다(accounts: AccountStore) -> None:
    """공유 토큰이 맞으면 인증이 쿠키를 보지 않는다(키를 읽다 데이터베이스가 죽는 일을 막는
    순서). 그래서 그 요청에는 계정이 없다. 공유 토큰을 걷으면 이 갈래도 사라진다."""
    await _seed(accounts, "kim.min", "admin")
    trace = FakeTrace()

    async with _serving(accounts, trace) as client:
        cookie = await _logged_in(client, "kim.min")
        response = await client.post("/runs", json=_start("echo"), headers={**cookie, **SHARED})

    assert response.status_code == 200
    assert _started(trace, "run-1").requesting_account is None


async def test_쿠키로_온_요청도_거절된_시작은_트레이스를_남기지_않는다(
    accounts: AccountStore,
) -> None:
    await _seed(accounts, "kim.min", "admin")
    trace = FakeTrace()

    async with _serving(accounts, trace) as client:
        cookie = await _logged_in(client, "kim.min")
        response: Response = await client.post("/runs", json=_start("nobody"), headers=cookie)

    assert response.status_code == 404
    assert trace.lines == []


# 권한 검사가 실제 라우트에서 도는지. 지금의 두 단계는 권한 넷을 모두 가져 403 이 날 길이 없으므로,
# 관리자의 권한을 비운 표를 끼워 실제 앱의 실제 라우트가 모두 막는지 본다.
_GATED: list[tuple[str, str, str, Mapping[str, Json] | None]] = [
    ("list_plugins", "GET", "/plugins", None),
    ("read_plugin", "GET", "/plugins/agent/echo", None),
    ("list_traces", "GET", "/traces", None),
    ("read_trace", "GET", "/traces/run-1", None),
    ("list_conversations", "GET", "/conversations", None),
    ("check_connection", "GET", "/plugins/mcp/calc-server/connection-check", None),
    ("check_connection_by_launching", "POST", "/plugins/mcp/calc-server/connection-check", None),
    ("set_plugin_enabled", "PUT", "/plugins/agent/echo/enabled", {"enabled": False}),
    ("start_run", "POST", "/runs", {"agent": "echo", "request": "2+3?"}),
    ("continue_run", "POST", "/runs/run-1/continuation", {"agent": "echo", "request": "2+3?"}),
    ("decide_approval", "POST", "/runs/run-1/approval", {"decision": "approve", "pause_index": 1}),
    ("list_accounts", "GET", "/accounts", None),
    ("create_account", "POST", "/accounts", {"name": "new.user"}),
    ("create_password_link", "POST", "/accounts/kim.min/link", None),
    ("set_account_active", "PUT", "/accounts/kim.min/active", {"active": False}),
    ("unlock_account", "POST", "/accounts/kim.min/unlock", None),
]
_NOTHING: Mapping[Tier, frozenset[Permission]] = {
    "system_admin": frozenset(Permission),
    "admin": frozenset[Permission](),
}


def test_권한_표의_권한_줄은_모두_실제_라우트로_밟는다() -> None:
    gated = {operation_id for operation_id, _method, _path, _body in _GATED}
    assert gated == {
        operation_id
        for operation_id, requirement in PERMISSION_TABLE.items()
        if isinstance(requirement, Permission)
    }


@pytest.mark.parametrize(
    ("operation_id", "method", "path", "body"), _GATED, ids=[row[0] for row in _GATED]
)
async def test_권한이_모자란_계정은_실제_라우트마다_403이고_아무_일도_일어나지_않는다(
    accounts: AccountStore,
    monkeypatch: pytest.MonkeyPatch,
    operation_id: str,
    method: str,
    path: str,
    body: Mapping[str, Json] | None,
) -> None:
    await _seed(accounts, "kim.min", "admin")
    trace = FakeTrace()
    monkeypatch.setattr(permissions_module, "TIER_PERMISSIONS", _NOTHING)

    async with _serving(accounts, trace) as client:
        cookie = await _logged_in(client, "kim.min")
        response = await client.request(method, path, json=body, headers=cookie)

    assert response.status_code == 403, f"{operation_id} 가 {response.status_code} 을 냈다"
    assert response.json()["message"] == "이 계정으로는 할 수 없다"
    assert trace.lines == []


async def test_권한이_모자란_계정도_로그인만_요구하는_경로는_지난다(
    accounts: AccountStore, monkeypatch: pytest.MonkeyPatch
) -> None:
    await _seed(accounts, "kim.min", "admin")
    monkeypatch.setattr(permissions_module, "TIER_PERMISSIONS", _NOTHING)

    async with _serving(accounts, FakeTrace()) as client:
        cookie = await _logged_in(client, "kim.min")
        me = await client.get("/auth/me", headers=cookie)
        out = await client.post("/auth/logout", headers=cookie)

    assert (me.status_code, out.status_code) == (200, 204)
