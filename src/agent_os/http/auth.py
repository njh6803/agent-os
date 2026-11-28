"""HTTP 표면의 fail-closed 인증. 경로마다 요구하는 자격 하나가 있고 allowlist 만 지나간다(ADR 0011).

미들웨어가 기본으로 막고 라우트가 보호를 opt-in 하지 않는다. opt-in 이면 라우트를 더하며 잊은
것이 곧 공개가 되고, 잊었다는 사실을 아는 길이 전수 검사 테스트 하나뿐이 된다. fail-closed 면 그
테스트는 벨트이지 안전장치 전부가 아니다.

미들웨어가 라우팅보다 바깥이라 문서에 없는 경로도 401 이다. 인증 없는 요청이 어떤 경로가
실재하는지 알아낼 수 없다는 뜻이기도 하다.

어느 자격을 요구하나는 접두사→자격 표가 정하고 표는 조립 층이 넘긴다. 자격은 둘이다. 최종 사용자
면은 자기 접두사 아래에서 사이트가 서명한 토큰을 쓰고(ADR 0023), 그 밖의 모든 경로(운영자 채널
`/runs` 를 포함한다)는 운영자 로그인, 곧 로그인 쿠키의 짧은 JWT 를 쓴다(ADR 0062). 표에 없는
경로의 기본값이 운영자 로그인이라, 새 경로를 접두사 밖에 두는 실수는 로그인 없이 막힐 뿐 열리지
않는다. 그래서 운영자 로그인은 최종 사용자 접두사에서 통하지 않고 서명 토큰은 그 밖에서 통하지
않는다. `Authorization` 머리는 운영자 경로에서 읽지 않으므로 공유 토큰을 싣고 오던 요청은 401 이다.

서명 토큰을 지난 요청은 그 신원(주체와 사이트 항목)을 요청에 심는다. 라우트의 의존성이 그것을 읽어
core 에 주체를, 열 에이전트 판정에 사이트를 넘긴다 — 본문에서 받지 않는다(ADR 0015).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from agent_os.core.ports import Clock
from agent_os.http.errors import UNAUTHORIZED_MESSAGE, error_envelope, remember_failure
from agent_os.http.login_tokens import ACCESS_COOKIE, LoginClaims
from agent_os.http.paths import is_under
from agent_os.http.sites import EndUser, Refusal, Sites, verify_signed

# 인증 없이 지나가는 경로. 원소는 `/health` 와 로그인, 갱신, 첫 계정 확인, 링크로 비밀번호 정하기
# 다섯이고 자라면 ADR 0011 의 이력에 쌓는다 — 목록이 문서 없이 자라는 것이 fail-open 으로 돌아가는
# 길이다. 갱신은 짧은 JWT 가 만료된 뒤에 오는 요청이라 미들웨어가 짧은 JWT 를 보지 않고, 서비스가
# 갱신용 번호 쿠키를 판정한다. 링크로 비밀번호 정하기는 링크 토큰이 자격이라 로그인 없이 연다(명세
# admin-login "로그인 없이 열리는 경로"). 비교가 정확히 같은지만 보는 이유는 `/health/` 나
# `/health/../traces` 같은 변형이 그대로 걸리게 하기 위해서다.
PUBLIC_PATHS = frozenset(
    {"/health", "/auth/login", "/auth/refresh", "/auth/setup", "/auth/set-password"}
)

_SCHEME = "bearer"
# 최종 사용자 경로의 401 이 요구하는 챌린지(RFC 9110). 어떤 방식으로 인증하는지 알리는 것은 노출이
# 아니다 — 401 자체가 이미 인증이 필요하다고 말한다. realm 을 붙이지 않는 이유는 그것이 내부
# 구성이어서다. 운영자 경로의 401 에는 싣지 않는다. 그 경로는 `Authorization` 머리를 읽지 않고
# 쿠키를 읽는다.
_CHALLENGE = {"WWW-Authenticate": "Bearer"}
# 서명 토큰을 지난 요청의 신원을 담는 ASGI scope 의 키. 라우트의 의존성이 이것으로 읽는다. 남의 키와
# 부딪히지 않게 패키지 이름을 앞에 둔다.
_END_USER_KEY = "agent_os.end_user"
# 짧은 JWT 를 지난 요청의 로그인을 담는 scope 의 키. 같은 이유로 패키지 이름을 앞에 둔다.
_OPERATOR_KEY = "agent_os.operator"


@dataclass(frozen=True)
class SiteSigned:
    """경로가 사이트가 서명한 토큰으로 열린다. 최종 사용자 면이다(ADR 0023).

    시계는 토큰의 시간 클레임을 세는 core 의 `Clock` 포트이고, 조립이 앱에 넘긴 것과 같은 것이다.
    그래서 만료를 가짜 시계로 잴 수 있다. 공용 층이 core 의 포트를 받는 것은 http → core 방향이라
    원칙 IV 안이다.
    """

    sites: Sites
    clock: Clock


class LoginVerifier(Protocol):
    """짧은 JWT 를 검증하는 쪽. 토큰이 없으면 데이터베이스를 읽지 않고 없음이어야 한다."""

    async def verify(self, token: str | None) -> LoginClaims | None: ...


class RequireToken(BaseHTTPMiddleware):
    """경로가 요구하는 자격이 맞는 요청만 지나간다. 그 밖은 전부 401 이고 라우팅에 닿지 않는다.

    표(`prefixes`)에 걸리는 경로는 사이트가 서명한 토큰으로만 열린다. 표에 걸리지 않는 모든 경로는
    로그인 쿠키의 짧은 JWT 로만 열린다. 공유 토큰은 없다(ADR 0062). 운영자 경로의 401 에는
    `WWW-Authenticate` 를 싣지 않고 최종 사용자 경로의 401 에는 싣는다.
    """

    def __init__(
        self,
        app: ASGIApp,
        *,
        prefixes: Mapping[str, SiteSigned],
        login: LoginVerifier,
    ) -> None:
        super().__init__(app)
        self._prefixes = dict(prefixes)
        self._login = login

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path
        if path in PUBLIC_PATHS:
            return await call_next(request)
        match self._required(path):
            case SiteSigned(sites=sites, clock=clock):
                header = request.headers.get("authorization")
                verified = verify_signed(_bearer(header), sites, clock)
                if isinstance(verified, Refusal):
                    reason = verified.reason
                    return _refused(
                        request,
                        f"{UNAUTHORIZED_MESSAGE}: 서명 토큰 — {reason}",
                        headers=_CHALLENGE,
                    )
                request.scope[_END_USER_KEY] = verified
            case None:
                claims = await self._login.verify(request.cookies.get(ACCESS_COOKIE))
                if claims is None:
                    return _refused(request, UNAUTHORIZED_MESSAGE)
                request.scope[_OPERATOR_KEY] = claims
        return await call_next(request)

    def _required(self, path: str) -> SiteSigned | None:
        """경로가 요구하는 서명 토큰. 표에 걸리지 않으면 없음이고 운영자 로그인이다. 비교는
        `is_under` 다."""
        for prefix, credential in self._prefixes.items():
            if is_under(path, prefix):
                return credential
        return None


def end_user_of(request: Request) -> EndUser | None:
    """서명 토큰을 지난 요청의 신원(질의). 최종 사용자 면의 라우트만 부른다.

    미들웨어가 그 접두사 아래의 요청을 언제나 검증하므로 그 라우트에서 없음은 조립의 결함이다.
    갈래가 있는 것은 scope 에서 읽은 값의 타입을 정적 타입이 모르기 때문이다.
    """
    found = request.scope.get(_END_USER_KEY)
    return found if isinstance(found, EndUser) else None


def operator_of(request: Request) -> LoginClaims | None:
    """짧은 JWT 를 지난 요청의 로그인(질의). 없으면 None.

    로그인 없이 지나가는 경로(`PUBLIC_PATHS`)에서는 없음이 정상이다. 그 밖의 운영자 경로에서 없음은
    조립의 결함이다. 갈래가 있는 것은 scope 에서 읽은 값의 타입을 정적 타입이 모르기 때문이다.
    """
    found = request.scope.get(_OPERATOR_KEY)
    return found if isinstance(found, LoginClaims) else None


def _refused(
    request: Request, detail: str, *, headers: Mapping[str, str] | None = None
) -> Response:
    """401 봉투 하나. 밖으로는 고정 문구이고 원인은 서버 기록에 남길 문구로만 적는다. 챌린지 머리는
    `Authorization` 머리로 인증하는 최종 사용자 경로의 것에만 싣는다."""
    remember_failure(request, detail)
    return error_envelope(
        request,
        status=401,
        message=UNAUTHORIZED_MESSAGE,
        headers=headers,
    )


def _bearer(header: str | None) -> str | None:
    """`Bearer` 헤더의 값. 없거나 방식이 다르거나 값이 비었으면 없음이다.

    빈 값을 먼저 거르는 이유는 헤더 부재를 빈 문자열로 다루는 구현과 겹치면 그 자체가 fail-open
    이기 때문이다.
    """
    if header is None:
        return None
    scheme, _, value = header.partition(" ")
    if scheme.lower() != _SCHEME or not value:
        return None
    return value
