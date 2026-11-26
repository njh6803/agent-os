"""권한 표와 그 검사(`agent_os.http.permissions`). 표의 내용과 전수 검사는 실제 계약을 보고, 검사의
동작은 표를 직접 넘긴 작은 앱으로 본다.

실제 앱의 경로는 두 단계가 모두 가진 권한 넷만 요구해서 모자란 권한의 403 이 나지 않는다. 그래서
검사 자체는 `manage_accounts` 를 요구하는 줄을 넣은 표로 따로 잰다.
"""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator, Mapping
from pathlib import Path

import pytest
import pytest_asyncio
from fastapi import APIRouter, Depends, FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel, ConfigDict

from agent_os.channel.http.end_user import END_USER_PREFIX
from agent_os.http.accounts import Tier
from agent_os.http.auth import LoginVerifier, RequireToken, SharedToken
from agent_os.http.errors import (
    CatchUnexpected,
    EndUserPaths,
    ErrorCode,
    install_error_handlers,
)
from agent_os.http.login_tokens import ACCESS_COOKIE, LoginClaims
from agent_os.http.paths import is_under
from agent_os.http.permissions import (
    FORBIDDEN_FOR_ACCOUNT_MESSAGE,
    PERMISSION_TABLE,
    SHARED_TOKEN_PERMISSIONS,
    TIER_PERMISSIONS,
    LoginOnly,
    Open,
    Permission,
    Requirement,
    permission_check,
)

ROOT = Path(__file__).resolve().parent.parent


def _operations() -> dict[str, tuple[str, str]]:
    """계약의 오퍼레이션 전부. `operationId` 에서 (메서드, 경로) 로."""
    contract = json.loads((ROOT / "openapi.json").read_text(encoding="utf-8"))
    found: dict[str, tuple[str, str]] = {}
    for path, item in contract["paths"].items():
        for method, operation in item.items():
            operation_id = operation["operationId"]
            assert operation_id not in found, f"계약에 같은 operationId 가 둘이다: {operation_id}"
            found[operation_id] = (method.upper(), path)
    return found


def test_권한_이름은_다섯이고_단계마다_가진_권한이_명세와_같다() -> None:
    assert {permission.value for permission in Permission} == {
        "view",
        "toggle_plugins",
        "start_runs",
        "decide",
        "manage_accounts",
    }
    assert TIER_PERMISSIONS["system_admin"] == frozenset(Permission)
    admin = TIER_PERMISSIONS["admin"]
    assert admin == frozenset(Permission) - {Permission.MANAGE_ACCOUNTS}, (
        f"관리자의 권한: {sorted(permission.value for permission in admin)}"
    )


def test_공유_토큰은_계정을_다루는_권한만_뺀_넷을_가진다() -> None:
    assert SHARED_TOKEN_PERMISSIONS == frozenset(Permission) - {Permission.MANAGE_ACCOUNTS}, (
        f"공유 토큰의 권한: {sorted(permission.value for permission in SHARED_TOKEN_PERMISSIONS)}"
    )


def test_권한_표는_계약의_운영자_오퍼레이션을_빠짐없이_꼭_한_번씩_든다() -> None:
    """표에 없는 오퍼레이션을 더하면 이 시험이 빨개진다. 반대로 계약에 없는 줄이 표에 남아도
    빨개진다 — 지운 경로의 줄이 남으면 표가 거짓말을 한다."""
    operator = {
        operation_id
        for operation_id, (_method, path) in _operations().items()
        if path != "/health" and not is_under(path, END_USER_PREFIX)
    }
    assert operator, "운영자 오퍼레이션이 없으면 이 전수 검사는 아무것도 재지 않는다"
    assert set(PERMISSION_TABLE) == operator


def test_표의_값은_로그인_없이_연다와_로그인만_요구한다와_권한_하나_셋_가운데_하나다() -> None:
    for requirement in PERMISSION_TABLE.values():
        assert isinstance(requirement, Open | LoginOnly | Permission)


@pytest.mark.parametrize(
    ("operation_id", "expected"),
    [
        ("log_in", Open()),
        ("get_setup", Open()),
        ("log_out", LoginOnly()),
        ("get_me", LoginOnly()),
        ("list_plugins", Permission.VIEW),
        ("read_plugin", Permission.VIEW),
        ("list_traces", Permission.VIEW),
        ("read_trace", Permission.VIEW),
        ("list_conversations", Permission.VIEW),
        # 스스로 하는 접속 확인은 보기이고, 눌러서 하는 것은 서버에서 stdio 프로세스를 띄우므로 더
        # 무거운 쪽이다
        ("check_connection", Permission.VIEW),
        ("check_connection_by_launching", Permission.TOGGLE_PLUGINS),
        ("set_plugin_enabled", Permission.TOGGLE_PLUGINS),
        ("start_run", Permission.START_RUNS),
        ("continue_run", Permission.START_RUNS),
        ("decide_approval", Permission.DECIDE),
    ],
)
def test_명세의_권한_표_줄이_그대로_적혀_있다(operation_id: str, expected: Requirement) -> None:
    found = PERMISSION_TABLE[operation_id]
    assert found == expected, f"{operation_id} 의 줄은 {found!r} 이다"


# 검사의 동작. 표를 직접 넘긴 작은 앱이고, 로그인 쪽은 쿠키 값 하나가 계정 하나인 가짜가 정한다.

_TABLE: Mapping[str, Requirement] = {
    "open_door": Open(),
    "login_only": LoginOnly(),
    "viewing": Permission.VIEW,
    "managing": Permission.MANAGE_ACCOUNTS,
    "managing_with_body": Permission.MANAGE_ACCOUNTS,
}
_SHARED = "shared-t0ken"
_ACCOUNTS: Mapping[str, Tier] = {"sys": "system_admin", "adm": "admin"}


class _Body(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str


class _Cookies:
    """쿠키 값이 계정 이름이면 그 계정의 로그인을 돌려주는 검증기."""

    async def verify(self, token: str | None) -> LoginClaims | None:
        if token is None or token not in _ACCOUNTS:
            return None
        return LoginClaims(
            name=token, login_id=uuid.UUID(int=1), tier=_ACCOUNTS[token], expires_at=2_000_000_000
        )


def _app(table: Mapping[str, Requirement]) -> FastAPI:
    router = APIRouter(dependencies=[Depends(permission_check(table))])

    @router.get("/open", operation_id="open_door")
    def open_door() -> dict[str, bool]:
        return {"ok": True}

    @router.get("/login-only", operation_id="login_only")
    def login_only() -> dict[str, bool]:
        return {"ok": True}

    @router.get("/viewing", operation_id="viewing")
    def viewing() -> dict[str, bool]:
        return {"ok": True}

    @router.get("/managing", operation_id="managing")
    def managing() -> dict[str, bool]:
        return {"ok": True}

    @router.post("/managing", operation_id="managing_with_body")
    def managing_with_body(body: _Body) -> dict[str, bool]:
        return {"ok": True}

    @router.get("/unlisted", operation_id="unlisted")
    def unlisted() -> dict[str, bool]:
        return {"ok": True}

    app = FastAPI()
    app.include_router(router)
    end_user = EndUserPaths(prefix=END_USER_PREFIX)
    install_error_handlers(app, end_user=end_user)
    login: LoginVerifier = _Cookies()
    app.add_middleware(RequireToken, default=SharedToken(_SHARED), prefixes={}, login=login)
    app.add_middleware(CatchUnexpected, end_user=end_user)
    return app


@pytest_asyncio.fixture
async def client() -> AsyncIterator[AsyncClient]:
    app = _app(_TABLE)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="https://admin.test") as c:
        yield c


def _cookie(name: str) -> dict[str, str]:
    return {"Cookie": f"{ACCESS_COOKIE}={name}"}


SHARED_HEADER = {"Authorization": f"Bearer {_SHARED}"}


async def test_권한이_모자란_계정은_403_고정_문구이고_코드는_forbidden이다(
    client: AsyncClient,
) -> None:
    response = await client.get("/managing", headers=_cookie("adm"))

    assert response.status_code == 403
    body = response.json()
    assert body["code"] == ErrorCode.FORBIDDEN
    assert body["message"] == FORBIDDEN_FOR_ACCOUNT_MESSAGE == "이 계정으로는 할 수 없다"
    assert body["violations"] == []


async def test_권한을_가진_계정은_지난다(client: AsyncClient) -> None:
    assert (await client.get("/managing", headers=_cookie("sys"))).status_code == 200
    assert (await client.get("/viewing", headers=_cookie("adm"))).status_code == 200


async def test_공유_토큰은_계정을_다루는_일을_못_하고_나머지_넷은_한다(client: AsyncClient) -> None:
    refused = await client.get("/managing", headers=SHARED_HEADER)
    allowed = await client.get("/viewing", headers=SHARED_HEADER)

    assert refused.status_code == 403
    assert refused.json()["message"] == FORBIDDEN_FOR_ACCOUNT_MESSAGE
    assert allowed.status_code == 200


async def test_열린_줄은_누구에게나_열리고_로그인만_요구하는_줄은_권한을_보지_않는다(
    client: AsyncClient,
) -> None:
    assert (await client.get("/open", headers=SHARED_HEADER)).status_code == 200
    assert (await client.get("/login-only", headers=_cookie("adm"))).status_code == 200


async def test_표에_없는_오퍼레이션은_조용히_지나지_않고_500이다(client: AsyncClient) -> None:
    """표에 없는 줄을 열린 것으로 읽으면 새 경로가 권한 없이 열린다. 전수 검사가 먼저 잡지만 그것이
    놓친 날에도 닫혀 있어야 한다."""
    response = await client.get("/unlisted", headers=_cookie("sys"))

    assert response.status_code == 500, f"표에 없는 줄이 {response.status_code} 을 냈다"


async def test_권한은_형식보다_먼저다_칸이_틀리거나_빠진_JSON_본문도_403이다(
    client: AsyncClient,
) -> None:
    wrong_field = await client.post("/managing", json={"nope": 1}, headers=_cookie("adm"))
    missing_field = await client.post("/managing", json={}, headers=_cookie("adm"))

    assert wrong_field.status_code == 403
    assert missing_field.status_code == 403


async def test_JSON으로_읽히지_않는_본문은_권한보다_먼저_422다(client: AsyncClient) -> None:
    """FastAPI 는 본문을 JSON 으로 풀다 실패하면 의존성을 풀기 전에 검증 오류를 낸다. 이 순서의
    예외는 받아들인 것이다(명세 "요청을 판정하는 차례")."""
    response = await client.post(
        "/managing",
        content=b"{not json",
        headers={**_cookie("adm"), "Content-Type": "application/json"},
    )

    assert response.status_code == 422
    assert response.json()["violations"][0]["field"].startswith("body")


async def test_권한이_있는_계정이_칸이_틀린_JSON을_보내면_422다(client: AsyncClient) -> None:
    response = await client.post("/managing", json={"nope": 1}, headers=_cookie("sys"))

    assert response.status_code == 422
