"""앱의 수명이 열릴 때 데이터베이스를 확인하는 문의 시제품. 순수 ASGI 미들웨어다.

수명 범위(`lifespan`)의 첫 메시지를 받아 데이터베이스를 확인하고, 문제가 있으면 안쪽 앱을 부르지
않고 `lifespan.startup.failed` 에 그 한 줄을 실어 보낸다. 문제가 없으면 받은 첫 메시지를 안쪽 앱에
다시 건네고, 안쪽 앱의 수명이 끝나면 연결 묶음을 닫는다.
"""

from __future__ import annotations

from starlette.types import ASGIApp, Message, Receive, Scope, Send

from proto.port import Database


class DatabaseGate:
    def __init__(self, app: ASGIApp, *, database: Database) -> None:
        self._app = app
        self._database = database

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "lifespan":
            await self._app(scope, receive, send)
            return
        first = await receive()
        problem = await self._database.startup_problem()
        if problem is not None:
            await self._database.close()
            await send({"type": "lifespan.startup.failed", "message": problem})
            return
        pending: list[Message] = [first]

        async def replay() -> Message:
            if pending:
                return pending.pop()
            return await receive()

        try:
            await self._app(scope, replay, send)
        finally:
            await self._database.close()
