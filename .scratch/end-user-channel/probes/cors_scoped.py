"""Starlette 의 CORS 미들웨어를 접두사 하나에만 걸고, 그 안쪽의 fail-closed 인증이 낸 401 에도
CORS 헤더가 붙는지.

ADR 0023 은 CORS 를 새 접두사에만 걸고(허용 출처는 사이트 파일), preflight 만이 아니라
미들웨어와 라우트가 낸 에러 응답(401, 404, 409, 429, 500)에도 헤더를 붙이고, `Retry-After` 를
노출 헤더로 내보내라고 했다. Starlette 의 `CORSMiddleware` 는 앱 전체에 걸리는 ASGI
미들웨어라 그대로 쓰면 관리 경로의 preflight 도 지난다(ADR 0011 의 2026-09-28 이력은 그것을
401 로 둔다). 그래서 경로 접두사로 가르는 작은 ASGI 분기 하나를 두고, 접두사 아래만
`CORSMiddleware(인증(앱))` 로, 그 밖은 `인증(앱)` 으로 보내는 조합을 잰다.

재는 것은 여섯이다. (1) 접두사 아래 preflight 가 토큰 없이 CORS 응답을 받는다. (2) 접두사
밖 preflight 는 401 이다. (3) 접두사 아래 토큰 없는 요청의 401 에
`Access-Control-Allow-Origin` 과 `Vary: Origin` 이 있다. (4) 접두사 아래 라우트가 낸
429 의 `Retry-After` 가 `Access-Control-Expose-Headers` 에 든다. (5) 허용 목록 밖 출처의
요청은 CORS 헤더 없이 지나간다(브라우저가 막는다). (6) 접두사 밖은 출처가 있어도 CORS
헤더가 없다. 인증은 저장소의 `RequireToken` 을 그대로 쓴다 — 서명 토큰 검증이 들어서도
"401 을 미들웨어가 낸다"는 모양은 같다.

    PYTHONUTF8=1 uv run python .scratch/end-user-channel/probes/cors_scoped.py
"""

from __future__ import annotations

import asyncio
import io

import httpx
from fastapi import FastAPI, Response
from starlette.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

from agent_os.http.auth import RequireToken
from agent_os.http.errors import AssignRequestId

PREFIX = "/chat"
ORIGIN = "https://site.example"


class SplitByPrefix:
    """접두사 아래는 CORS 를 두른 사슬로, 그 밖은 맨 사슬로 보낸다. 경로 조각 단위로 비교한다."""

    def __init__(self, *, inside: ASGIApp, outside: ASGIApp) -> None:
        self._inside = inside
        self._outside = outside

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        path = scope.get("path", "")
        chain = self._inside if path == PREFIX or path.startswith(f"{PREFIX}/") else self._outside
        await chain(scope, receive, send)


def build() -> ASGIApp:
    app = FastAPI()

    @app.post(f"{PREFIX}/runs")
    async def start() -> dict[str, str]:
        return {"ok": "yes"}

    @app.post(f"{PREFIX}/limited")
    async def limited() -> Response:
        return Response(status_code=429, headers={"Retry-After": "7"})

    @app.get("/plugins")
    async def plugins() -> list[str]:
        return []

    authed = RequireToken(app, default="admin-token", prefixes={PREFIX: "chat-token"})
    cors = CORSMiddleware(
        authed,
        allow_origins=[ORIGIN],
        allow_methods=["GET", "POST"],
        allow_headers=["Authorization", "Content-Type", "Last-Event-ID"],
        expose_headers=["Retry-After", "X-Request-Id"],
    )
    split = SplitByPrefix(inside=cors, outside=authed)
    return AssignRequestId(split, stderr=io.StringIO())


def show(title: str, response: httpx.Response, *names: str) -> None:
    picked = {name: response.headers.get(name) for name in names}
    print(f"{title}: {response.status_code} {picked}")


async def main() -> None:
    transport = httpx.ASGITransport(app=build())
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


if __name__ == "__main__":
    asyncio.run(main())
