"""계정을 다루는 라우터: 목록, 만들기, 링크 만들기, 활성과 비활성, 잠금 풀기(ADR 0062, 명세
admin-login "계정을 다루는 경로").

모두 계정을 다룰 권한(`manage_accounts`)이 있는 계정만 부른다. 권한은 라우터에 건 의존성이 형식
검사보다 먼저 가린다. 짧은 JWT 의 단계가 관리자여도 403 이다.
판정은 `agent_os.http.account_admin` 이 하고 이 모듈은 요청을 풀어 넘기고 답을 모양으로 옮긴다.

응답 모델의 독스트링은 한 줄이고 논증은 `#` 주석에 둔다. 라우트는 `operation_id` 를 손으로 주고
자기가 내는 에러를 문서에 적는다. 경로의 `{name}` 은 바꾸지 않고 이름 규칙에 댄다. 슬래시와 개행이
든 값도 422 가 되도록 `verbatim` 변환기로 받는다.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from fastapi import APIRouter, HTTPException, Path, Request, Response
from pydantic import BaseModel, ConfigDict, Field, StrictBool

from agent_os.admin.auth import NOT_LOGGED_IN_MESSAGE, invalid_field
from agent_os.http.account_admin import AccountAdmin, IssuedLink
from agent_os.http.accounts import (
    ACCOUNT_NAME_PATTERN,
    ACCOUNT_NAME_RULE_TEXT,
    AccountRow,
    fold_account_name,
    is_account_name,
)
from agent_os.http.auth import operator_of
from agent_os.http.login_tokens import forwarded_address
from agent_os.http.permissions import REQUIRE_PERMISSION
from agent_os.http.routes import documented_errors

NAME_TAKEN_MESSAGE = "같은 이름의 계정이 이미 있다"
SYSTEM_ADMIN_MESSAGE = "시스템 관리자 계정에는 할 수 없다"
DISABLED_ACCOUNT_MESSAGE = "비활성인 계정에는 링크를 만들 수 없다"
ACCOUNT_ABSENT_MESSAGE = "그런 계정이 없다"


# 상태는 해시와 비활성으로 바꾼 시각 둘에서 나온다(명세 "상태는 둘로 적는다"). 잠김은 상태가 아니라
# `locked_until` 이다
class AccountSummary(BaseModel):
    """계정 목록의 줄. 이름과 단계와 상태와 잠겨 풀리는 시각과 만든 시각."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    tier: Literal["system_admin", "admin"]
    state: Literal["active", "disabled", "password_unset"]
    locked_until: datetime | None
    created_at: datetime


class AccountList(BaseModel):
    """계정 목록. 시스템 관리자가 먼저이고 나머지는 이름순이다."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    accounts: list[AccountSummary]


class CreateAccountRequest(BaseModel):
    """계정 만들기 요청. 새 계정의 이름을 받는다."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1, max_length=32)


class SetActiveRequest(BaseModel):
    """활성과 비활성을 바꾸는 요청. 엄격한 불린 하나를 받는다."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    active: StrictBool


# 링크의 토큰은 이 응답에서 한 번만 보인다. 서버에는 해시만 남는다
class PasswordLink(BaseModel):
    """새 비밀번호 링크. 토큰과 그 기한이다."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    link_token: str = Field(repr=False)
    link_expires_at: datetime


class CreatedAccount(BaseModel):
    """만든 계정의 이름과 그 계정의 첫 비밀번호 링크."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    link_token: str = Field(repr=False)
    link_expires_at: datetime


def accounts_router(*, admin: AccountAdmin) -> APIRouter:
    """계정을 다루는 라우터. 다섯 라우트 모두 계정을 다룰 권한이 있는 계정만 지난다."""
    router = APIRouter(responses=documented_errors(500), dependencies=[REQUIRE_PERMISSION])

    @router.get(
        "/accounts",
        operation_id="list_accounts",
        summary="계정 전부를 시스템 관리자부터 이름순으로 읽는다",
        responses=documented_errors(401, 403),
    )
    async def list_accounts() -> AccountList:
        now = admin.now()
        rows = await admin.list_accounts()
        return AccountList(accounts=[_summary(row, now) for row in rows])

    @router.post(
        "/accounts",
        operation_id="create_account",
        summary="관리자 계정을 비밀번호 없이 만들고 첫 비밀번호 링크를 받는다",
        status_code=201,
        responses=documented_errors(
            401, 403, 409, 422, descriptions={409: "같은 이름의 계정이 이미 있다"}
        ),
    )
    async def create_account(body: CreateAccountRequest, request: Request) -> CreatedAccount:
        actor = _actor(request)
        name = fold_account_name(body.name)
        if not is_account_name(name):
            raise invalid_field("body", "name", message=ACCOUNT_NAME_RULE_TEXT)
        created = await admin.create(name, actor=actor, address=_address(request))
        if created == "taken":
            raise HTTPException(status_code=409, detail=NAME_TAKEN_MESSAGE)
        return CreatedAccount(
            name=created.name,
            link_token=created.link.token,
            link_expires_at=created.link.expires_at,
        )

    @router.post(
        "/accounts/{name:verbatim}/link",
        operation_id="create_password_link",
        summary="그 계정의 앞 링크를 못 쓰게 하고 새 비밀번호 링크를 만든다",
        status_code=201,
        responses=documented_errors(401, 403, 404, 409, 422),
    )
    async def create_password_link(
        name: Annotated[str, Path(pattern=ACCOUNT_NAME_PATTERN)], request: Request
    ) -> PasswordLink:
        issued = await admin.create_link(name, actor=_actor(request), address=_address(request))
        if isinstance(issued, IssuedLink):
            return PasswordLink(link_token=issued.token, link_expires_at=issued.expires_at)
        if issued == "absent":
            raise HTTPException(status_code=404, detail=ACCOUNT_ABSENT_MESSAGE)
        if issued == "system_admin":
            raise HTTPException(status_code=409, detail=SYSTEM_ADMIN_MESSAGE)
        raise HTTPException(status_code=409, detail=DISABLED_ACCOUNT_MESSAGE)

    @router.put(
        "/accounts/{name:verbatim}/active",
        operation_id="set_account_active",
        summary="계정을 활성이나 비활성으로 바꾼다. 이미 그 상태면 아무것도 바꾸지 않는다",
        status_code=204,
        response_class=Response,
        responses=documented_errors(401, 403, 404, 409, 422),
    )
    async def set_account_active(
        name: Annotated[str, Path(pattern=ACCOUNT_NAME_PATTERN)],
        body: SetActiveRequest,
        request: Request,
    ) -> Response:
        change = admin.enable if body.active else admin.disable
        refused = await change(name, actor=_actor(request), address=_address(request))
        if refused == "absent":
            raise HTTPException(status_code=404, detail=ACCOUNT_ABSENT_MESSAGE)
        if refused == "system_admin":
            raise HTTPException(status_code=409, detail=SYSTEM_ADMIN_MESSAGE)
        return Response(status_code=204)

    @router.post(
        "/accounts/{name:verbatim}/unlock",
        operation_id="unlock_account",
        summary="계정의 잠금과 틀린 횟수를 지운다",
        status_code=204,
        response_class=Response,
        responses=documented_errors(401, 403, 404, 422),
    )
    async def unlock_account(
        name: Annotated[str, Path(pattern=ACCOUNT_NAME_PATTERN)], request: Request
    ) -> Response:
        refused = await admin.unlock(name, actor=_actor(request), address=_address(request))
        if refused == "absent":
            raise HTTPException(status_code=404, detail=ACCOUNT_ABSENT_MESSAGE)
        return Response(status_code=204)

    return router


def _summary(row: AccountRow, now: datetime) -> AccountSummary:
    if row.disabled_at is not None:
        state: Literal["active", "disabled", "password_unset"] = "disabled"
    elif row.password_hash is None:
        state = "password_unset"
    else:
        state = "active"
    # 풀리는 시각이 이미 지났으면 잠긴 것이 아니다
    locked = row.locked_until if row.locked_until is not None and row.locked_until > now else None
    return AccountSummary(
        name=row.name,
        tier=row.tier,
        state=state,
        locked_until=locked,
        created_at=row.created_at,
    )


def _actor(request: Request) -> str:
    """요청한 계정의 이름. 이 라우트는 계정을 다룰 권한이 있어야 닿으므로 계정이 없으면 조립의
    결함이다."""
    claims = operator_of(request)
    if claims is None:
        raise HTTPException(status_code=401, detail=NOT_LOGGED_IN_MESSAGE)
    return claims.name


def _address(request: Request) -> str | None:
    return forwarded_address(request.headers.getlist("x-forwarded-for"))
