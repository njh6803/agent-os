"""Starlette 의 CORS 미들웨어를 접두사 하나에만 걸고, 그 안쪽의 fail-closed 인증이 낸 401 에도
CORS 헤더가 붙는지.

ADR 0023 은 CORS 를 새 접두사에만 걸고(허용 출처는 사이트 파일), preflight 만이 아니라
미들웨어와 라우트가 낸 에러 응답(401, 404, 409, 429, 500)에도 헤더를 붙이고, `Retry-After` 를
노출 헤더로 내보내라고 했다. Starlette 의 `CORSMiddleware` 는 앱 전체에 걸리는 ASGI
미들웨어라 그대로 쓰면 관리 경로의 preflight 도 지난다(ADR 0011 의 2026-09-28 이력은 그것을
401 로 둔다). 그래서 경로 접두사로 가르는 작은 ASGI 분기 하나를 두고, 접두사 아래만
`CORSMiddleware(인증(앱))` 로, 그 밖은 `인증(앱)` 으로 보내는 조합을 잰다.

재는 것은 일곱이다. (1) 접두사 아래 preflight 가 토큰 없이 CORS 응답을 받는다. (2) 접두사
밖 preflight 는 401 이다. (3) 접두사 아래 토큰 없는 요청의 401 에
`Access-Control-Allow-Origin` 과 `Vary: Origin` 이 있다. (4) 접두사 아래 라우트가 낸
429 의 `Retry-After` 가 `Access-Control-Expose-Headers` 에 든다. (5) 허용 목록 밖 출처의
요청은 CORS 헤더 없이 지나간다(브라우저가 막는다). (6) 접두사 밖은 출처가 있어도 CORS
헤더가 없다. (7) 라우트의 예기치 않은 예외가 500 봉투가 될 때, 변환이 CORS 안쪽에 있으면
헤더가 붙고 바깥의 `AssignRequestId` 에만 있으면(지금의 조립, 대조군) 붙지 않는다 — PR #135
의 CodeRabbit 이 짚었다. 인증은 저장소의 `RequireToken` 을 그대로 쓴다 — 서명 토큰 검증이
들어서도 "401 을 미들웨어가 낸다"는 모양은 같다.

    PYTHONUTF8=1 uv run python .scratch/end-user-channel/probes/cors_scoped.py
"""

from __future__ import annotations

import asyncio
import io

import httpx
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

from agent_os.http.auth import RequireToken
from agent_os.http.errors import INTERNAL_MESSAGE, AssignRequestId, error_envelope

PREFIX = "/chat"
ORIGIN = "https://site.example"


class CatchUnexpected(BaseHTTPMiddleware):
    """예기치 않은 예외를 고정 문구의 500 봉투로 바꾼다. 지금은 `AssignRequestId` 가 함께 하는 일을
    떼어 낸 것이다 — CORS 안쪽에 두려면 식별자 심기(모든 응답)와 가라야 한다(PR #135 CodeRabbit)."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            return await call_next(request)
        except Exception:
            return error_envelope(request, status=500, message=INTERNAL_MESSAGE)


class SplitByPrefix:
    """접두사 아래는 CORS 를 두른 사슬로, 그 밖은 맨 사슬로 보낸다. 경로 조각 단위로 비교한다.

    `app.add_middleware` 로 걸리는 모양이라 받은 `app` 위에 두 사슬을 스스로 짓는다. 그래야
    Starlette 가 앱 스택의 맨 바깥에 두는 `ServerErrorMiddleware` 가 이 분기의 바깥에 선다 — FastAPI
    앱을 밖에서 감싸면 그 미들웨어가 안쪽에 들어가 예외를 500 평문으로 먼저 보낸 뒤 다시 던지므로,
    바깥의 어떤 변환도 봉투를 만들 수 없다(처음 판의 프로브가 그랬다. 실제 조립 `create_app` 은
    `add_middleware` 다).
    """

    def __init__(self, app: ASGIApp, *, catch_inside: bool) -> None:
        authed = RequireToken(app, default="admin-token", prefixes={PREFIX: "chat-token"})
        inner: ASGIApp = CatchUnexpected(authed) if catch_inside else authed
        self._inside: ASGIApp = CORSMiddleware(
            inner,
            allow_origins=[ORIGIN],
            allow_methods=["GET", "POST"],
            allow_headers=["Authorization", "Content-Type", "Last-Event-ID"],
            expose_headers=["Retry-After", "X-Request-Id"],
        )
        self._outside: ASGIApp = authed

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        path = scope.get("path", "")
        chain = self._inside if path == PREFIX or path.startswith(f"{PREFIX}/") else self._outside
        await chain(scope, receive, send)


def build(*, catch_inside: bool) -> ASGIApp:
    """`catch_inside` 가 참이면 예외→봉투 변환을 CORS 안쪽에 두고, 거짓이면 지금처럼 바깥의
    `AssignRequestId` 에만 맡긴다(대조군). 미들웨어는 실제 조립과 같이 `add_middleware` 로 건다."""
    app = FastAPI()

    @app.post(f"{PREFIX}/runs")
    async def start() -> dict[str, str]:
        return {"ok": "yes"}

    @app.post(f"{PREFIX}/limited")
    async def limited() -> Response:
        return Response(status_code=429, headers={"Retry-After": "7"})

    @app.post(f"{PREFIX}/boom")
    async def boom() -> dict[str, str]:
        raise RuntimeError("예기치 않은 실패")

    @app.get("/plugins")
    async def plugins() -> list[str]:
        return []

    app.add_middleware(SplitByPrefix, catch_inside=catch_inside)
    app.add_middleware(AssignRequestId, stderr=io.StringIO())
    return app


def show(title: str, response: httpx.Response, *names: str) -> None:
    picked = {name: response.headers.get(name) for name in names}
    print(f"{title}: {response.status_code} {picked}")


async def main() -> None:
    transport = httpx.ASGITransport(app=build(catch_inside=True))
    preflight = {
        "Origin": ORIGIN,
        "Access-Control-Request-Method": "POST",
        "Access-Control-Request-Headers": "authorization, last-event-id",
    }
    cors_names = ("access-control-allow-origin", "vary", "access-control-expose-headers")
    async with httpx.AsyncClient(transport=transport, base_url="http://probe") as client:
        show(
            "(1) 접두사 아래 preflight, 토큰 없음",
            await client.options(f"{PREFIX}/runs", headers=preflight),
            "access-control-allow-origin",
            "access-control-allow-methods",
            "access-control-allow-headers",
        )
        show(
            "(2) 접두사 밖 preflight, 토큰 없음",
            await client.options("/plugins", headers=preflight),
            *cors_names,
        )
        show(
            "(3) 접두사 아래 토큰 없는 POST",
            await client.post(f"{PREFIX}/runs", headers={"Origin": ORIGIN}),
            *cors_names,
            "www-authenticate",
        )
        show(
            "(4) 접두사 아래 429",
            await client.post(
                f"{PREFIX}/limited",
                headers={"Origin": ORIGIN, "Authorization": "Bearer chat-token"},
            ),
            *cors_names,
            "retry-after",
        )
        show(
            "(5) 허용 밖 출처",
            await client.post(
                f"{PREFIX}/runs",
                headers={"Origin": "https://evil.example", "Authorization": "Bearer chat-token"},
            ),
            *cors_names,
        )
        show(
            "(6) 접두사 밖, 출처 있는 GET 에 관리 토큰",
            await client.get(
                "/plugins", headers={"Origin": ORIGIN, "Authorization": "Bearer admin-token"}
            ),
            *cors_names,
        )
        boom_headers = {"Origin": ORIGIN, "Authorization": "Bearer chat-token"}
        show(
            "(7) 접두사 아래 예기치 않은 예외의 500, 변환이 CORS 안쪽",
            await client.post(f"{PREFIX}/boom", headers=boom_headers),
            *cors_names,
            "x-request-id",
        )
    control = httpx.ASGITransport(app=build(catch_inside=False))
    async with httpx.AsyncClient(transport=control, base_url="http://probe") as client:
        show(
            "(7') 같은 500, 변환이 바깥(지금의 AssignRequestId)뿐인 대조군",
            await client.post(f"{PREFIX}/boom", headers=boom_headers),
            *cors_names,
            "x-request-id",
        )


if __name__ == "__main__":
    asyncio.run(main())
