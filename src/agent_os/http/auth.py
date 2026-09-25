"""HTTP 표면의 fail-closed 인증. 경로마다 공유 토큰 하나를 요구하고 allowlist 만 지나간다(ADR 0011).

미들웨어가 기본으로 막고 라우트가 보호를 opt-in 하지 않는다. opt-in 이면 라우트를 더하며 잊은
것이 곧 공개가 되고, 잊었다는 사실을 아는 길이 전수 검사 테스트 하나뿐이 된다. fail-closed 면 그
테스트는 벨트이지 안전장치 전부가 아니다.

미들웨어가 라우팅보다 바깥이라 문서에 없는 경로도 401 이다. 인증 없는 요청이 어떤 경로가
실재하는지 알아낼 수 없다는 뜻이기도 하다.

어느 토큰을 요구하나는 접두사→토큰 표가 정하고 표는 조립 층이 넘긴다. 채널은 `/runs` 아래에서
자기 토큰을 쓴다(ADR 0015, ADR 0011 의 2026-09-24 이력). 토큰을 가르는 이유는 권한의 성격이
달라서다 — 관리 토큰은 트레이스를 읽고 채널 토큰은 비용과 부작용이 있는 실행을 일으킨다. 표에
없는 경로의 기본값은 관리 토큰이라, 새 채널 경로를 접두사 밖에 두는 실수는 틀린 토큰으로 막힐
뿐 열리지 않는다.
"""

from __future__ import annotations

import hmac
from collections.abc import Mapping

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from agent_os.http.errors import UNAUTHORIZED_MESSAGE, error_envelope, remember_failure

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


class RequireToken(BaseHTTPMiddleware):
    """경로가 요구하는 토큰이 맞는 요청만 지나간다. 그 밖은 전부 401 이고 라우팅에 닿지 않는다."""

    def __init__(self, app: ASGIApp, *, default: str, prefixes: Mapping[str, str]) -> None:
        super().__init__(app)
        # 비교를 바이트로 하는 이유는 `hmac.compare_digest` 가 str 을 받으면 non-ASCII 에서
        # TypeError 를 내기 때문이다. 원격 입력 하나가 401 이어야 할 자리를 500 으로 바꾼다.
        self._default = default.encode("utf-8")
        self._prefixes = {prefix: token.encode("utf-8") for prefix, token in prefixes.items()}

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path
        if path in PUBLIC_PATHS:
            return await call_next(request)
        if not _matches(request.headers.get("authorization"), self._expected(path)):
            remember_failure(request, UNAUTHORIZED_MESSAGE)
            return error_envelope(
                request,
                status=401,
                message=UNAUTHORIZED_MESSAGE,
                headers=_CHALLENGE,
            )
        return await call_next(request)

    def _expected(self, path: str) -> bytes:
        """경로가 요구하는 토큰. 표에 걸리지 않으면 기본값이다.

        접두사는 경로 조각 단위로 본다. `/runs` 는 `/runs` 와 `/runs/…` 에 걸리고 `/runsx` 에는
        걸리지 않는다 — 문자열 접두사면 이름이 우연히 겹친 경로가 다른 토큰의 면으로 넘어간다.
        미들웨어와 라우팅이 같은 경로 문자열을 보므로 이 분류와 라우트가 엇갈릴 길은 없다. 표의
        접두사는 서로를 품지 않는다고 본다. 품는 표가 생기면 어느 쪽이 이기는지를 그 표를 넘기는
        쪽이 테스트와 함께 정한다 — 원소가 하나인 지금은 그 규칙을 잴 길이 없다.
        """
        for prefix, token in self._prefixes.items():
            if path == prefix or path.startswith(f"{prefix}/"):
                return token
        return self._default


def _matches(header: str | None, expected: bytes) -> bool:
    """헤더 하나를 판정한다. 없는 것과 빈 것이 같은 답을 받되 둘 다 통과가 아니다.

    빈 값을 먼저 거르는 이유는 헤더 부재를 빈 문자열로 다루는 구현과 겹치면 그 자체가
    fail-open 이기 때문이다. 비교는 값에 따라 시간이 달라지지 않는다 — 비교 시간이 곧 토큰을
    한 글자씩 알려 주는 경로다(스토리 40). 어느 토큰이든 이 한 곳을 지난다.
    """
    if header is None:
        return False
    scheme, _, value = header.partition(" ")
    if scheme.lower() != _SCHEME or not value:
        return False
    return hmac.compare_digest(value.encode(_HEADER_CODEC, errors="replace"), expected)
