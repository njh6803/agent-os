"""요청 출처 검사. 운영자 면(관리 API와 운영자 채널)은 같은 출처의 페이지가 보낸 요청과 브라우저가
아닌 프로그램의 요청만 받는다(ADR 0062 의 결정 "요청 출처 검사").

운영자의 브라우저에 로그인 상태가 생기면, 다른 사이트의 페이지나 같은 서버의 다른 페이지가 그
브라우저를 빌려 관리 API 와 운영자 채널을 부를 수 있다. 막는 규칙은 둘이다.

- `Sec-Fetch-Site` 가 있으면 값이 `same-origin` 일 때만 지난다. `same-site`·`cross-site`·`none` 과
  그 밖의 값은 403 이다. 브라우저가 이 머리를 붙이고 페이지의 스크립트는 바꿀 수 없다.
- 없으면 `Origin` 도 없을 때만 지난다. 브라우저가 아닌 프로그램(httpx, Node 의 fetch, Playwright 의
  API 컨텍스트)은 둘 다 보내지 않고, 이 서버의 시험이 그런 프로그램이다. 관리 화면의 중계(Next 의
  rewrites)는 브라우저가 낸 요청을 그대로 넘기므로 그 요청은 브라우저가 붙인 `Sec-Fetch-Site` 를
  달고 온다(ADR 0062 의 쿠키 프로브가 본 것). `Sec-Fetch-Site` 를 모르는 옛 브라우저는 교차 출처
  요청에 `Origin` 을 붙이므로 여기서 걸린다.

그 밖의 머리(`Sec-Fetch-Mode`, `Referer`, `Host` 따위)는 보지 않는다. Node 의 fetch 는
`Sec-Fetch-Mode: cors` 를 보내므로 그 머리를 보면 중계가 막힌다.

**검사는 인증보다 앞에 선다.** 출처가 틀린 요청에는 토큰이 있든 없든 403 이고, 어느 경로가 로그인을
요구하는지 다른 사이트에 알리지 않는다. `Origin` 이 있고 토큰이 없는 요청이 401 이 아니라 403 인
까닭이다. 문서에 없는 경로도 검사에 걸린다(미들웨어가 라우팅보다 바깥이다).

**걸리지 않는 곳은 `/health` 와 최종 사용자 접두사다.** `/health` 는 이름으로 뺀다. 인증 없이 열린
경로의 목록(`PUBLIC_PATHS`)을 따라가지 않는다. 그 목록에 로그인·갱신 같은 경로가 들어와도 그 경로는
다른 사이트가 부르면 안 되는 것이라 이 검사를 받는다(ADR 0011 의 2026-11-15 이력). 최종 사용자 면은
다른 사이트의 페이지가 부르는 것이 본래 용도라 CORS 와 서명 토큰이 그 면의 출처 정책이다(ADR 0023).
두 비교는 인증 표와 CORS 분기가 쓰는 것과 같은 `request.url.path` 와 `is_under` 라서 서명 토큰으로
열린 경로가 곧 이 검사 밖이다.

403 봉투의 문구는 고정이고 머리의 이름이나 값을 싣지 않는다. 서버 기록에도 값을 남기지 않는다.
"""

from __future__ import annotations

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from agent_os.http.errors import FORBIDDEN_MESSAGE, error_envelope, remember_failure
from agent_os.http.paths import is_under

# 이 검사 밖에 두는 상태 확인 경로. 인증 없이 열린 경로의 목록과 값이 같아도 따로 적는다(위
# 독스트링).
_HEALTH_PATH = "/health"
_FETCH_SITE = "sec-fetch-site"
_ORIGIN = "origin"
# 같은 출처의 페이지가 보낸 요청에 브라우저가 붙이는 값. 이것만 지난다.
_SAME_ORIGIN = "same-origin"


class CheckOrigin(BaseHTTPMiddleware):
    """출처가 맞지 않는 요청은 403 이고 인증과 라우팅에 닿지 않는다."""

    def __init__(self, app: ASGIApp, *, exempt_prefix: str) -> None:
        super().__init__(app)
        self._exempt_prefix = exempt_prefix

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path
        if path == _HEALTH_PATH or is_under(path, self._exempt_prefix) or _accepted(request):
            return await call_next(request)
        # 서버 기록의 문구에도 머리의 값을 싣지 않는다. 값은 요청하는 쪽이 정하는 글이다.
        remember_failure(request, "요청 출처 검사에 걸렸다")
        return error_envelope(request, status=403, message=FORBIDDEN_MESSAGE)


def _accepted(request: Request) -> bool:
    """출처 검사를 지나는가(질의). 위 모듈 독스트링의 두 규칙이 전부다."""
    site = request.headers.get(_FETCH_SITE)
    if site is not None:
        return site == _SAME_ORIGIN
    return request.headers.get(_ORIGIN) is None
