"""`Database` 포트(`agent_os.http.database`)의 가짜와, 앱의 수명을 직접 구동하는 도우미.

가짜는 포트를 상속하지 않고 시그니처로 만족한다. 시험은 `database: Database = FakeDatabase()`
처럼 포트 타입으로 annotate해 적합성을 검증한다(`.claude/rules/tests.md`). 가짜가 돌려주는 글은
어댑터의 글이 아니라 시험이 알아볼 수 있는 표지이고, 어댑터의 글은 어댑터 시험이 글자까지 본다.

구동자는 같은 앱을 `app(scope, receive, send)` 로 직접 불러 lifespan 메시지를 주고받는다.
`ASGITransport` 는 lifespan 을 보내지 않고 `app.router.lifespan_context` 는 확인 미들웨어를 지나지
않기 때문이다(`.claude/rules/http.md` 의 테스트 항목, 예외의 "시작과 끝의 수명 주기").
"""

from __future__ import annotations

import asyncio
from collections.abc import MutableMapping

from starlette.types import ASGIApp, Message
from tests.fake_accounts import UnusedAccounts

STARTUP_PROBLEM = "표지: 가짜 데이터베이스의 멈출 때의 글"
UNEXPECTED_PREFIX = "표지: 확인하다 멈췄다"
CLOSE_PREFIX = "표지: 닫다 실패했다"


class FakeDatabase:
    """확인과 닫기의 결과를 시험이 정하는 데이터베이스. 불린 차례를 `events` 에 쌓는다."""

    def __init__(
        self,
        *,
        problem: str | None = None,
        check_error: BaseException | None = None,
        close_error: BaseException | None = None,
        hold_close: asyncio.Event | None = None,
    ) -> None:
        self._problem = problem
        self._check_error = check_error
        self._close_error = close_error
        self._hold_close = hold_close
        self.events: list[str] = []

    async def startup_problem(self) -> str | None:
        self.events.append("startup_problem")
        if self._check_error is not None:
            raise self._check_error
        return self._problem

    async def close(self) -> None:
        self.events.append("close_started")
        if self._hold_close is not None:
            await self._hold_close.wait()
        if self._close_error is not None:
            raise self._close_error
        self.events.append("close_finished")

    def accounts(self) -> UnusedAccounts:
        """`serve` 가 앱에 넘기는 계정 저장소. 서명 키만 메모리에 두는 대역이다."""
        return UnusedAccounts()

    def unexpected_problem(self, error: BaseException) -> str:
        return f"{UNEXPECTED_PREFIX}({type(error).__name__})"

    def close_problem(self, error: BaseException) -> str:
        return f"{CLOSE_PREFIX}({type(error).__name__})"


class LifespanDriver:
    """앱 하나의 lifespan 범위를 구동한다. 앱이 보낸 메시지는 순서대로 `sent` 에 쌓인다."""

    def __init__(self, app: ASGIApp) -> None:
        self._app = app
        self._to_app: asyncio.Queue[Message] = asyncio.Queue()
        self._from_app: asyncio.Queue[Message] = asyncio.Queue()
        self._task: asyncio.Task[None] | None = None
        self.sent: list[Message] = []

    async def _next(self) -> Message:
        message = await asyncio.wait_for(self._from_app.get(), timeout=10)
        self.sent.append(message)
        return message

    async def startup(self) -> Message:
        """시작 메시지를 보내고 앱의 첫 답(`startup.complete` 나 `startup.failed`)을 돌려준다."""
        scope: MutableMapping[str, object] = {
            "type": "lifespan",
            "asgi": {"version": "3.0", "spec_version": "2.0"},
            "state": {},
        }

        async def run() -> None:
            await self._app(scope, self._to_app.get, self._from_app.put)

        self._task = asyncio.create_task(run())
        await self._to_app.put({"type": "lifespan.startup"})
        return await self._next()

    async def request_shutdown(self) -> None:
        await self._to_app.put({"type": "lifespan.shutdown"})

    async def shutdown(self) -> Message:
        """끝내라는 메시지를 보내고 앱의 첫 답을 돌려준다."""
        await self.request_shutdown()
        return await self._next()

    async def silence(self, seconds: float) -> bool:
        """앱이 `seconds` 동안 아무 메시지도 보내지 않았으면 참."""
        await asyncio.sleep(seconds)
        return self._from_app.empty()

    async def next_message(self) -> Message:
        return await self._next()

    async def finish(self) -> None:
        """앱이 끝나기를 기다린다. 앱이 예외로 끝났으면 그 예외를 올린다."""
        if self._task is not None:
            await asyncio.wait_for(self._task, timeout=10)
