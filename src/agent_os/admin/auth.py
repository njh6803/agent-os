"""운영자 로그인의 라우터: 로그인, 로그아웃, 지금 누구인지, 첫 계정 확인(ADR 0062, 명세
admin-login).

판정은 `agent_os.http.logins` 가 하고 이 모듈은 요청을 풀어 넘기고 쿠키 줄을 응답에 싣는다. 자격은
미들웨어가 라우팅 전에 본다. 로그인과 첫 계정 확인은 로그인 없이 열리는 경로이고(`PUBLIC_PATHS`),
로그아웃과 지금 누구인지는 짧은 JWT 로만 열린다(`LOGIN_ONLY_PATHS`). 요청 출처 검사는 넷 모두에
걸린다.

응답 모델의 독스트링은 한 줄이고 논증은 `#` 주석에 둔다. 라우트는 `operation_id` 를 손으로 주고
자기가 내는 에러를 문서에 적는다. 쿠키를 심거나 지우는 응답은 `Set-Cookie` 머리를 응답 문서에
적는다.
"""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field

from agent_os.http.auth import operator_of
from agent_os.http.login_tokens import forwarded_address
from agent_os.http.logins import LoginService
from agent_os.http.permissions import REQUIRE_PERMISSION
from agent_os.http.routes import documented_errors

# 로그인 실패의 문구 하나. 없는 계정과 틀린 비밀번호와 잠긴 계정과 비활성 계정을 가르지 않는다
# (ADR 0062 결정 "잠금과 실패 문구").
LOGIN_REFUSED_MESSAGE = "로그인하지 못했다"
# 로그인 한 건이 있어야 뜻이 있는 경로에 로그인 없이 닿았을 때의 문구
NOT_LOGGED_IN_MESSAGE = "로그인하지 않았다"

_SET_COOKIE_HEADER: dict[str, object] = {
    "description": "쿠키 둘(`__Host-aos_at`, `__Host-aos_rt`)을 심거나 지우는 줄이다. 줄이 둘 온다",
    "schema": {"type": "string"},
}


# 계약에 박히는 요청 본문이다. 비밀번호가 든 본문이라 `repr` 에서 뺀다. 오류 응답은 값을 싣지 않는다
# (`violations` 는 칸의 자리와 pydantic 의 문구만 든다). 길이는 정규화하기 전에 센 글자 수이고,
# 비밀번호의 상한을 넉넉히 두는 까닭은 정규화가 글자 수를 줄이기도 해서다(명세 "계정 이름과
# 비밀번호"의 "몸통의 상한").
class LoginRequest(BaseModel):
    """로그인 요청. 계정 이름과 비밀번호를 받는다."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1, max_length=32)
    password: str = Field(min_length=1, max_length=1024, repr=False)


# 단계는 두 값의 닫힌 열거다. 화면이 메뉴를 가르는 데 쓴다.
class Me(BaseModel):
    """지금 로그인한 계정. 이름과 단계와 짧은 로그인의 수명(분)과 서버의 실행 제한 시간(초)."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    tier: Literal["system_admin", "admin"]
    token_minutes: int
    run_timeout_seconds: float


class Setup(BaseModel):
    """첫 계정이 필요한지. 운영자 계정이 하나도 없을 때만 참이다."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    needs_first_account: bool


def auth_router(
    *, login: LoginService, token_minutes: int, run_timeout_seconds: float
) -> APIRouter:
    """로그인 라우터. 수명은 서버가 뜰 때 해시 전용 스레드와 서명 키를 만들고 멈출 때 닫는다.

    `run_timeout_seconds` 는 `create_app` 이 받은 실행 제한 시간이고, 주지 않았으면 core 의 기본값을
    조립이 읽어 넘긴다. 이 모듈에 600 을 따로 적지 않는다. 두 자리가 따로 적으면 core 의 기본값이
    바뀔 때 화면이 멈추는 때만 옛 값으로 남는다.
    """
    router = APIRouter(
        lifespan=lambda _app: login.lifespan(),
        responses=documented_errors(500),
        dependencies=[REQUIRE_PERMISSION],
    )

    @router.post(
        "/auth/login",
        operation_id="log_in",
        summary="계정 이름과 비밀번호로 로그인하고 쿠키 둘을 받는다",
        status_code=204,
        response_class=Response,
        responses={
            204: {"headers": {"Set-Cookie": _SET_COOKIE_HEADER}},
            **documented_errors(401, 403, 422),
        },
    )
    async def log_in(body: LoginRequest, request: Request) -> Response:
        address = forwarded_address(request.headers.getlist("x-forwarded-for"))
        cookies = await login.log_in(body.name, body.password, address=address)
        if cookies is None:
            raise HTTPException(status_code=401, detail=LOGIN_REFUSED_MESSAGE)
        return _with_cookies(cookies)

    @router.post(
        "/auth/logout",
        operation_id="log_out",
        summary="이 로그인을 끊고 쿠키를 지운다",
        status_code=204,
        response_class=Response,
        responses={
            204: {"headers": {"Set-Cookie": _SET_COOKIE_HEADER}},
            **documented_errors(401, 403),
        },
    )
    async def log_out(request: Request) -> Response:
        claims = operator_of(request)
        if claims is None:
            # 미들웨어가 이 경로를 로그인 없이는 지나보내지 않는다. 여기 닿으면 조립의 결함이다
            raise HTTPException(status_code=401, detail=NOT_LOGGED_IN_MESSAGE)
        address = forwarded_address(request.headers.getlist("x-forwarded-for"))
        return _with_cookies(await login.log_out(claims, address=address))

    @router.get(
        "/auth/me",
        operation_id="get_me",
        summary="지금 로그인한 계정을 짧은 JWT 만 보고 답한다",
        responses=documented_errors(401, 403),
    )
    async def get_me(request: Request) -> Me:
        claims = operator_of(request)
        if claims is None:
            raise HTTPException(status_code=401, detail=NOT_LOGGED_IN_MESSAGE)
        return Me(
            name=claims.name,
            tier=claims.tier,
            token_minutes=token_minutes,
            run_timeout_seconds=run_timeout_seconds,
        )

    @router.get(
        "/auth/setup",
        operation_id="get_setup",
        summary="첫 계정이 필요한지 로그인 없이 묻는다",
        responses=documented_errors(403),
    )
    async def get_setup() -> Setup:
        return Setup(needs_first_account=await login.needs_first_account())

    return router


def _with_cookies(lines: list[str]) -> Response:
    """본문 없는 204 에 `Set-Cookie` 줄을 하나씩 싣는다. 줄이 둘이라 머리를 두 번 더한다."""
    response = Response(status_code=204)
    for line in lines:
        response.headers.append("set-cookie", line)
    return response
