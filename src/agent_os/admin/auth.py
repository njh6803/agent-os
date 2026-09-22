"""관리 API 의 fail-closed 인증. 공유 토큰 하나를 요구하고 allowlist 만 지나간다(ADR 0011).

미들웨어가 기본으로 막고 라우트가 보호를 opt-in 하지 않는다. opt-in 이면 라우트를 더하며 잊은
것이 곧 공개가 되고, 잊었다는 사실을 아는 길이 전수 검사 테스트 하나뿐이 된다. fail-closed 면 그
테스트는 벨트이지 안전장치 전부가 아니다.

미들웨어가 라우팅보다 바깥이라 문서에 없는 경로도 401 이다. 인증 없는 요청이 어떤 경로가
실재하는지 알아낼 수 없다는 뜻이기도 하다.

`http-channel` 은 이 결정을 물려받지 않는다 — 실행을 일으키는 면은 인증의 성격이 달라 그 기능이
자기 ADR 을 쓴다. 그때 이 미들웨어가 앱 전체에 걸려 있다는 사실을 같이 본다. 그때까지 기본값은
막는 쪽이다.
"""

from __future__ import annotations

import hmac

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from agent_os.admin.http import UNAUTHORIZED_MESSAGE, error_envelope, remember_failure

# 인증 없이 지나가는 경로. 원소는 하나이고 자라면 ADR 0011 의 이력에 쌓는다 — 목록이 문서 없이
# 자라는 것이 fail-open 으로 돌아가는 길이다. 비교가 정확히 같은지만 보는 이유는 `/health/` 나
# `/health/../traces` 같은 변형이 그대로 걸리게 하기 위해서다.
PUBLIC_PATHS = frozenset({"/health"})

_SCHEME = "bearer"
# 헤더는 ASGI 경계에서 latin-1 로 디코딩되므로 같은 코덱으로 되돌리면 실린 바이트 그대로다.
_HEADER_CODEC = "latin-1"


class RequireToken(BaseHTTPMiddleware):
    """토큰이 맞는 요청만 지나간다. 그 밖은 전부 401 이고 라우팅에 닿지 않는다."""

    def __init__(self, app: ASGIApp, *, token: str) -> None:
        super().__init__(app)
        # 비교를 바이트로 하는 이유는 `hmac.compare_digest` 가 str 을 받으면 non-ASCII 에서
        # TypeError 를 내기 때문이다. 원격 입력 하나가 401 이어야 할 자리를 500 으로 바꾼다.
        self._token = token.encode("utf-8")

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path in PUBLIC_PATHS:
            return await call_next(request)
        if not self._matches(request.headers.get("authorization")):
            remember_failure(request, UNAUTHORIZED_MESSAGE)
            return error_envelope(request, status=401, message=UNAUTHORIZED_MESSAGE)
        return await call_next(request)

    def _matches(self, header: str | None) -> bool:
        """헤더 하나를 판정한다. 없는 것과 빈 것이 같은 답을 받되 둘 다 통과가 아니다.

        빈 값을 먼저 거르는 이유는 헤더 부재를 빈 문자열로 다루는 구현과 겹치면 그 자체가
        fail-open 이기 때문이다. 비교는 값에 따라 시간이 달라지지 않는다 — 비교 시간이 곧 토큰을
        한 글자씩 알려 주는 경로다(스토리 40).
        """
        if header is None:
            return False
        scheme, _, value = header.partition(" ")
        if scheme.lower() != _SCHEME or not value:
            return False
        return hmac.compare_digest(value.encode(_HEADER_CODEC, errors="replace"), self._token)
