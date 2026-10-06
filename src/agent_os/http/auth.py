"""HTTP 표면의 fail-closed 인증. 경로마다 요구하는 자격 하나가 있고 allowlist 만 지나간다(ADR 0011).

미들웨어가 기본으로 막고 라우트가 보호를 opt-in 하지 않는다. opt-in 이면 라우트를 더하며 잊은
것이 곧 공개가 되고, 잊었다는 사실을 아는 길이 전수 검사 테스트 하나뿐이 된다. fail-closed 면 그
테스트는 벨트이지 안전장치 전부가 아니다.

미들웨어가 라우팅보다 바깥이라 문서에 없는 경로도 401 이다. 인증 없는 요청이 어떤 경로가
실재하는지 알아낼 수 없다는 뜻이기도 하다.

어느 자격을 요구하나는 접두사→자격 표가 정하고 표는 조립 층이 넘긴다. 자격은 셋이다. 운영자
채널은 `/runs` 아래에서 자기 공유 토큰을 쓰고(ADR 0015, ADR 0011 의 2026-09-24 이력), 최종 사용자
면은 자기 접두사 아래에서 사이트가 서명한 토큰을 쓰며(ADR 0023), 그 밖은 관리 토큰이다. 자격을
가르는 이유는 권한의 성격이 달라서다 — 관리 토큰은 트레이스를 읽고, 채널 토큰은 비용과 부작용이 있는
실행을 일으키며, 서명 토큰은 원격의 최종 사용자가 자기 실행만 다룬다. 표에 없는 경로의 기본값은 관리
토큰이라, 새 경로를 접두사 밖에 두는 실수는 틀린 토큰으로 막힐 뿐 열리지 않는다. 그래서 채널 토큰과
관리 토큰은 최종 사용자 접두사에서 통하지 않고 서명 토큰은 그 밖에서 통하지 않는다.

서명 토큰을 지난 요청은 그 신원(주체와 사이트 항목)을 요청에 심는다. 라우트의 의존성이 그것을 읽어
core 에 주체를, 열 에이전트 판정에 사이트를 넘긴다 — 본문에서 받지 않는다(ADR 0015).
"""

from __future__ import annotations

import hmac
from collections.abc import Mapping
from dataclasses import dataclass

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from agent_os.core.ports import Clock
from agent_os.http.errors import UNAUTHORIZED_MESSAGE, error_envelope, remember_failure
from agent_os.http.paths import is_under
from agent_os.http.sites import EndUser, Refusal, Sites, verify_signed

# 인증 없이 지나가는 경로. 원소는 하나이고 자라면 ADR 0011 의 이력에 쌓는다 — 목록이 문서 없이
# 자라는 것이 fail-open 으로 돌아가는 길이다. 비교가 정확히 같은지만 보는 이유는 `/health/` 나
# `/health/../traces` 같은 변형이 그대로 걸리게 하기 위해서다.
PUBLIC_PATHS = frozenset({"/health"})

_SCHEME = "bearer"
# 401 이 요구하는 챌린지(RFC 9110). 어떤 방식으로 인증하는지 알리는 것은 노출이 아니다 — 401
# 자체가 이미 인증이 필요하다고 말한다. realm 을 붙이지 않는 이유는 그것이 내부 구성이어서다.
_CHALLENGE = {"WWW-Authenticate": "Bearer"}
# 헤더는 ASGI 경계에서 latin-1 로 디코딩되므로 같은 코덱으로 되돌리면 실린 바이트 그대로다.
_HEADER_CODEC = "latin-1"
# 서명 토큰을 지난 요청의 신원을 담는 ASGI scope 의 키. 라우트의 의존성이 이것으로 읽는다. 남의 키와
# 부딪히지 않게 패키지 이름을 앞에 둔다.
_END_USER_KEY = "agent_os.end_user"


@dataclass(frozen=True)
class SharedToken:
    """경로가 공유 토큰 하나로 열린다. 관리와 운영자 채널이다."""

    value: str


@dataclass(frozen=True)
class SiteSigned:
    """경로가 사이트가 서명한 토큰으로 열린다. 최종 사용자 면이다(ADR 0023).

    시계는 토큰의 시간 클레임을 세는 core 의 `Clock` 포트이고, 조립이 앱에 넘긴 것과 같은 것이다.
    그래서 만료를 가짜 시계로 잴 수 있다. 공용 층이 core 의 포트를 받는 것은 http → core 방향이라
    원칙 IV 안이다.
    """

    sites: Sites
    clock: Clock


# 접두사→자격 표의 값. 공유 토큰 하나이거나 사이트 목록이 서명한 토큰이다.
type Credential = SharedToken | SiteSigned


@dataclass(frozen=True)
class _Shared:
    """비교를 위해 미리 바이트로 바꾼 공유 토큰."""

    value: bytes


class RequireToken(BaseHTTPMiddleware):
    """경로가 요구하는 자격이 맞는 요청만 지나간다. 그 밖은 전부 401 이고 라우팅에 닿지 않는다."""

    def __init__(
        self, app: ASGIApp, *, default: SharedToken, prefixes: Mapping[str, Credential]
    ) -> None:
        super().__init__(app)
        self._default = _prepared(default)
        self._prefixes = {prefix: _prepared(credential) for prefix, credential in prefixes.items()}

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path
        if path in PUBLIC_PATHS:
            return await call_next(request)
        header = request.headers.get("authorization")
        match self._required(path):
            case _Shared(value=expected):
                if not _matches(header, expected):
                    return _refused(request, UNAUTHORIZED_MESSAGE)
            case SiteSigned(sites=sites, clock=clock):
                verified = verify_signed(_bearer(header), sites, clock)
                if isinstance(verified, Refusal):
                    reason = verified.reason
                    return _refused(request, f"{UNAUTHORIZED_MESSAGE}: 서명 토큰 — {reason}")
                request.scope[_END_USER_KEY] = verified
        return await call_next(request)

    def _required(self, path: str) -> _Shared | SiteSigned:
        """경로가 요구하는 자격. 표에 걸리지 않으면 기본값이다. 비교는 `is_under` 다."""
        for prefix, credential in self._prefixes.items():
            if is_under(path, prefix):
                return credential
        return self._default


def end_user_of(request: Request) -> EndUser | None:
    """서명 토큰을 지난 요청의 신원(질의). 최종 사용자 면의 라우트만 부른다.

    미들웨어가 그 접두사 아래의 요청을 언제나 검증하므로 그 라우트에서 없음은 조립의 결함이다.
    갈래가 있는 것은 scope 에서 읽은 값의 타입을 정적 타입이 모르기 때문이다.
    """
    found = request.scope.get(_END_USER_KEY)
    return found if isinstance(found, EndUser) else None


def _prepared(credential: Credential) -> _Shared | SiteSigned:
    """표의 값을 비교할 모양으로. 공유 토큰은 바이트로 바꾼다.

    바이트로 비교하는 이유는 `hmac.compare_digest` 가 str 을 받으면 non-ASCII 에서 TypeError 를 내기
    때문이다. 원격 입력 하나가 401 이어야 할 자리를 500 으로 바꾼다.
    """
    match credential:
        case SharedToken(value=value):
            return _Shared(value.encode("utf-8"))
        case SiteSigned():
            return credential


def _refused(request: Request, detail: str) -> Response:
    """401 봉투 하나. 밖으로는 고정 문구이고 원인은 서버 기록에 남길 문구로만 적는다."""
    remember_failure(request, detail)
    return error_envelope(request, status=401, message=UNAUTHORIZED_MESSAGE, headers=_CHALLENGE)


def _bearer(header: str | None) -> str | None:
    """`Bearer` 헤더의 값. 없거나 방식이 다르거나 값이 비었으면 없음이다.

    빈 값을 먼저 거르는 이유는 헤더 부재를 빈 문자열로 다루는 구현과 겹치면 그 자체가 fail-open
    이기 때문이다. 공유 토큰과 서명 토큰이 이 한 곳을 지난다.
    """
    if header is None:
        return None
    scheme, _, value = header.partition(" ")
    if scheme.lower() != _SCHEME or not value:
        return None
    return value


def _matches(header: str | None, expected: bytes) -> bool:
    """공유 토큰 하나를 판정한다. 없는 것과 빈 것이 같은 답을 받되 둘 다 통과가 아니다.

    비교는 값에 따라 시간이 달라지지 않는다 — 비교 시간이 곧 토큰을 한 글자씩 알려 주는 경로다
    (스토리 40). 어느 공유 토큰이든 이 한 곳을 지난다.
    """
    value = _bearer(header)
    if value is None:
        return False
    return hmac.compare_digest(value.encode(_HEADER_CODEC, errors="replace"), expected)
