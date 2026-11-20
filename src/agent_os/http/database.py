"""데이터베이스 포트와, 앱의 수명을 여닫을 때 그것을 확인하고 닫는 순수 ASGI 미들웨어.

`serve` 는 표의 판이 맞는 데이터베이스에 닿아야 뜬다(ADR 0066). 확인은 수명이 열리는 첫 메시지에서
앱의 시작 단계보다 먼저 한다. 확인을 앱의 시작 단계 안에 두면 MCP 서버 같은 시작 일이 먼저 돌고
그 뒤에야 데이터베이스를 알게 된다. 문제가 있으면 앱의 시작 단계를 부르지 않은 채
`lifespan.startup.failed` 에 멈출 때의 글을 싣는다. uvicorn 은 그 글을 역추적 없이 찍고 3 으로
끝난다.

**포트는 메서드 넷이다.** 비동기 `startup_problem` 과 `close`, 그리고 예외를 글로 바꾸는 동기
`unexpected_problem` 과 `close_problem` 이다. 뒤의 둘은 어댑터만 아는 것(자리 표시, 오류 번호를
고르는 법)이 글에 들어서 여기서 만들 수 없다. 미들웨어는 예외의 글과 역추적을 싣지 않고 이 둘이
돌려준 글만 싣는다(원칙 V). 포트는 SQLAlchemy 의 타입을 주고받지 않는다.

**종료 완료는 닫은 뒤에 보낸다.** uvicorn 은 `lifespan.shutdown.complete` 를 받으면 더 기다리지
않는다. 먼저 넘기면 연결 묶음을 닫는 도중에 프로세스가 끝난다. 그래서 앱이 보내는 완료를 붙잡아
두었다가 닫은 뒤에 넘기고, 닫다 실패하면 완료 대신 `lifespan.shutdown.failed` 를 보낸다. 앱이 스스로
시작이나 종료를 실패시켜도, 앱이 아무 말 없이 끝나거나 취소되어도 닫기는 한 번 불린다.
"""

from __future__ import annotations

from typing import Protocol

from starlette.types import ASGIApp, Message, Receive, Scope, Send


class Database(Protocol):
    """서버가 뜨기 전 확인하고 멈출 때 닫는 데이터베이스. 어댑터는 시그니처로 만족한다."""

    async def startup_problem(self) -> str | None:
        """닿아서 표의 판을 견준다. 문제가 없으면 `None`, 있으면 멈출 때의 글."""
        ...

    async def close(self) -> None:
        """연결 묶음을 닫는다."""
        ...

    def unexpected_problem(self, error: BaseException) -> str:
        """확인이 글 대신 예외를 던졌을 때의 글. 예외의 글과 역추적은 싣지 않는다."""
        ...

    def close_problem(self, error: BaseException) -> str:
        """닫기가 예외를 던졌을 때의 글. 예외의 글과 역추적은 싣지 않는다."""
        ...


class CheckDatabase:
    """수명 범위의 앞뒤를 맡는다. HTTP 와 그 밖의 범위는 건드리지 않고 안쪽으로 넘긴다."""

    def __init__(self, app: ASGIApp, *, database: Database) -> None:
        self._app = app
        self._database = database
        self._closed = False

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "lifespan":
            await self._app(scope, receive, send)
            return
        try:
            await self._guard(scope, receive, send)
        finally:
            # 앱이 말없이 끝났거나 취소됐을 때도 연결 묶음이 남지 않게 한다. 이미 닫았으면 아무것도
            # 안 한다.
            await self._close()

    async def _guard(self, scope: Scope, receive: Receive, send: Send) -> None:
        first = await receive()
        if first["type"] != "lifespan.startup":
            await self._app(scope, _replaying(first, receive), self._holding(send))
            return
        problem = await self._startup_problem()
        if problem is not None:
            await self._close()
            await send({"type": "lifespan.startup.failed", "message": problem})
            return
        await self._app(scope, _replaying(first, receive), self._holding(send))

    async def _startup_problem(self) -> str | None:
        try:
            return await self._database.startup_problem()
        except Exception as error:  # 어떤 예외든 까닭만 싣는 글로 바꾼다
            return self._database.unexpected_problem(error)

    async def _close(self) -> str | None:
        """연결 묶음을 한 번만 닫는다. 실패하면 그 글을, 아니면 `None` 을 돌려준다."""
        if self._closed:
            return None
        self._closed = True
        try:
            await self._database.close()
        except Exception as error:  # 어떤 예외든 까닭만 싣는 글로 바꾼다
            return self._database.close_problem(error)
        return None

    def _holding(self, send: Send) -> Send:
        """앱이 보내는 수명 메시지 가운데 끝나는 것은 닫은 뒤에 넘긴다."""

        async def held(message: Message) -> None:
            kind = message["type"]
            if kind == "lifespan.shutdown.complete":
                problem = await self._close()
                if problem is not None:
                    message = {"type": "lifespan.shutdown.failed", "message": problem}
            elif kind in ("lifespan.startup.failed", "lifespan.shutdown.failed"):
                await self._close()
            await send(message)

        return held


def _replaying(first: Message, receive: Receive) -> Receive:
    """이미 읽은 첫 메시지를 안쪽 앱에게 다시 들려주고 그다음부터는 그대로 받는다."""
    pending: list[Message] = [first]

    async def replay() -> Message:
        if pending:
            return pending.pop()
        return await receive()

    return replay
