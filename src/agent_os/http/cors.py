"""최종 사용자 면의 CORS. 접두사 하나에만 Starlette 의 `CORSMiddleware` 를 건다(ADR 0023).

브라우저는 허용 출처의 페이지에서 보낸 요청만 응답을 읽게 둔다. 서버는 막지 않고 허용 밖 출처에
`Access-Control-Allow-Origin` 을 내지 않을 뿐이다. 위젯이 에러 봉투도 읽어야 하므로 성공 응답만이
아니라 인증과 표가 낸 에러 응답에도 헤더가 붙는다 — CORS 가 인증과 라우터를 감싸는 순서가 그것을
만든다. 조립의 순서는 `server.py` 다.

**앱 전체가 아니라 접두사 하나다.** `CORSMiddleware` 는 `Origin` 이 있는 preflight 에 경로와
무관하게 직접 답하므로, 앱 전체에 걸면 관리 경로와 운영자 채널의 preflight 도 인증 앞에서
지나간다. 그 경로들의 preflight 는 401 이다(ADR 0011 의 2026-09-28 이력). 그래서 경로로 가르는
작은 분기 하나가 접두사 아래만 CORS 를 두른 사슬로 보낸다. 비교는 인증 표와 예외 표가 쓰는
`is_under` 이고 경로도 그 둘이 보는 것(`request.url.path`)이다 — ASGI 의 `path` 를 그대로 보면
퍼센트 인코딩된 `?` 가 든 경로에서 인증은 최종 사용자 면으로 보는데 CORS 는 아니게 된다. CORS
판정 자체는 직접 쓰지 않는다. 같은 일을 하는 검증된 코드가 이미 의존성에 있다(end-user-channel
명세 "CORS", `cors_scoped.py`).

**preflight 의 갈래는 셋이고 라이브러리가 정한다.** 허용 출처는 토큰 없이 200 이다. 허용 밖
출처(사이트 파일이 없어 허용 출처가 빈 것도)를 비롯해 라이브러리의 preflight 검사(출처, 메서드,
헤더, private network)에 걸린 것은 라이브러리의 400 평문이고 봉투가 아니다 — 봉투 규칙의 유일한
예외다. 브라우저는 preflight 의 실패를 페이지 스크립트에
드러내지 않아 봉투가 있어도 읽히지 않는다. `Origin` 이 없으면 CORS 요청이 아니라서 안쪽으로 넘기고
인증이 401 로 막는다. preflight 는 라우팅에 닿지 않으므로 그 200 은 경로가 실재하는지 말하지 않는다.
"""

from __future__ import annotations

from collections.abc import Sequence

from starlette.datastructures import URL
from starlette.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

from agent_os.http.errors import REQUEST_ID_HEADER
from agent_os.http.paths import is_under

# 값은 명세가 정했다. 메서드는 최종 사용자 면의 경로 셋이 쓰는 둘과 preflight 의 `OPTIONS` 이고,
# 헤더는 서명 토큰과 JSON 본문과 구독의 재개 지점이다. 라이브러리가 CORS 안전 목록 헤더
# (`Accept`·`Accept-Language`·`Content-Language`)를 늘 더하므로 preflight 가 허용하는 헤더는 이
# 셋보다 넓다. 노출 헤더는 429 의 기다릴 초와, 위젯이 운영자에게 건넬 추적 식별자다. 쿠키를 쓰지
# 않으므로 자격 증명은 허용하지 않고, `max_age` 는 라이브러리 기본값이다.
ALLOW_METHODS = ("GET", "POST", "OPTIONS")
ALLOW_HEADERS = ("Authorization", "Content-Type", "Last-Event-ID")
EXPOSE_HEADERS = ("Retry-After", REQUEST_ID_HEADER)


class CorsUnderPrefix:
    """접두사 아래 요청은 CORS 를 두른 사슬로, 그 밖은 맨 사슬로 보낸다.

    `app.add_middleware` 로 건다. 받은 안쪽 앱 위에 두 사슬을 스스로 짓는 모양이라, Starlette 가 앱
    스택의 맨 바깥에 두는 `ServerErrorMiddleware` 가 이 분기보다 바깥에 선다. FastAPI 앱을 밖에서
    감싸면 그 미들웨어가 안쪽에 들어가 예외를 500 평문으로 먼저 보낸 뒤 다시 던지므로, 바깥의 어떤
    변환도 봉투를 만들 수 없다(`cors_scoped.py` 의 처음 판, 일지 2026-10-05-03).

    HTTP 가 아닌 scope(lifespan, 지금은 라우트가 없는 websocket)는 맨 사슬로 간다. CORS 는 HTTP
    요청의 것이다.
    """

    def __init__(self, app: ASGIApp, *, prefix: str, origins: Sequence[str]) -> None:
        self._prefix = prefix
        self._bare = app
        self._cors = CORSMiddleware(
            app,
            allow_origins=tuple(origins),
            allow_methods=ALLOW_METHODS,
            allow_headers=ALLOW_HEADERS,
            expose_headers=EXPOSE_HEADERS,
        )

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http" and is_under(URL(scope=scope).path, self._prefix):
            await self._cors(scope, receive, send)
            return
        await self._bare(scope, receive, send)
