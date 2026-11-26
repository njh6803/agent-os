"""위젯 관리 서버의 수명 확인 미들웨어(`widget_admin.lifespan.CheckDatabase`)를 앱 전체로 본다.

서버를 띄우지 않고 앱을 `app(scope, receive, send)` 로 직접 불러 뜨기·내리기 신호를 주고받는 수명
구동자(`tests/fake_database.py` 의 `LifespanDriver`)로 돌린다. `ASGITransport` 는 lifespan 을 돌리지
않아 이 사례를 볼 수 없다(`.claude/rules/http.md` 테스트 항목의 예외와 같은 자리). 요청은 같은 앱을
`ASGITransport` 로 부른다. 닫기와 확인이 예외를 던지는 갈래는 진짜 데이터베이스로 일으킬 수 없어
데이터베이스 객체의 확인이나 닫기만 바꾼 객체를 앱을 짓는 함수에 넘겨 일으킨다(명세 검토 S4).
"""

from __future__ import annotations

import asyncio
import io
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from starlette.types import Message, Receive, Scope, Send
from tests.fake_database import LifespanDriver
from tests.postgres_support import FIRST, SECOND, copy_versions, other_connections
from tests.widget_admin.support import Notices, client_of, database_url, patient
from tools.database_for_tests import ScopedDatabase

from widget_admin.database import PRODUCT_VERSIONS, WidgetAdminDatabase
from widget_admin.lifespan import CheckDatabase
from widget_admin.server import create_app

# 접속하지 않는 주소. 확인과 닫기를 바꾼 객체가 엔진을 짓기만 하고 연결은 열지 않는다.
_PLACEHOLDER = "postgresql://widget_admin:placeholder@127.0.0.1:1/probe"


class _Scripted(WidgetAdminDatabase):
    """확인과 닫기의 결과를 시험이 정하는 객체. 불린 차례를 `events` 에 쌓는다."""

    def __init__(
        self,
        *,
        problem: str | None = None,
        check_error: BaseException | None = None,
        close_error: BaseException | None = None,
        hold_close: asyncio.Event | None = None,
    ) -> None:
        super().__init__(database_url(_PLACEHOLDER), notice=Notices())
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
        await super().close()
        self.events.append("close_finished")


def _app_recording_its_own_lifespan(database: WidgetAdminDatabase, events: list[str]) -> FastAPI:
    """앱 자신의 시작 단계와 끝 단계가 불린 것도 `events` 에 쌓는 앱."""
    app = create_app(database=database, stderr=io.StringIO())

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
        events.append("app_startup")
        yield
        events.append("app_shutdown")

    app.router.lifespan_context = lifespan
    return app


async def test_표가_뒤처진_데이터베이스는_앱의_시작_단계_전에_시작_실패_글로_멈춘다(
    empty_database: ScopedDatabase, tmp_path: Path
) -> None:
    versions = copy_versions(tmp_path / "versions", FIRST, SECOND)
    database = patient(empty_database.text(), versions, Notices())
    events: list[str] = []
    driver = LifespanDriver(_app_recording_its_own_lifespan(database, events))

    reply = await driver.startup()
    await driver.finish()

    assert reply == {
        "type": "lifespan.startup.failed",
        "message": (
            "데이터베이스의 표가 이 판보다 뒤처져 있습니다. widget-admin migrate 를 먼저"
            " 돌리십시오.\n"
            "  표의 판은 없음이고 이 판의 마지막 판은 9002입니다."
        ),
    }
    assert events == []
    assert await other_connections(empty_database) == 0


async def test_확인이_통과하면_뜨고_health가_200이며_내릴_때_연결이_남지_않는다(
    empty_database: ScopedDatabase,
) -> None:
    database = patient(empty_database.text(), PRODUCT_VERSIONS, Notices())
    assert (await database.migrate()).ok
    events: list[str] = []
    app = _app_recording_its_own_lifespan(database, events)
    driver = LifespanDriver(app)

    started = await driver.startup()
    async with client_of(app) as client:
        health = await client.get("/health")
    stopped = await driver.shutdown()
    await driver.finish()

    assert started == {"type": "lifespan.startup.complete"}
    assert (health.status_code, health.json()) == (200, {"status": "ok"})
    assert stopped == {"type": "lifespan.shutdown.complete"}
    assert events == ["app_startup", "app_shutdown"]
    assert await other_connections(empty_database) == 0


async def test_확인이_글을_돌려주면_그_글이_시작_실패에_실리고_닫기가_한_번_불린다() -> None:
    database = _Scripted(problem="표지: 확인이 돌려준 글")
    driver = LifespanDriver(create_app(database=database, stderr=io.StringIO()))

    reply = await driver.startup()
    await driver.finish()

    assert reply == {"type": "lifespan.startup.failed", "message": "표지: 확인이 돌려준 글"}
    assert database.events == ["startup_problem", "close_started", "close_finished"]


async def test_확인이_예외를_던져도_확인하다_멈췄다는_글로_시작_실패에_실린다() -> None:
    database = _Scripted(check_error=RuntimeError("비밀번호가 섞인 글"))
    driver = LifespanDriver(create_app(database=database, stderr=io.StringIO()))

    reply = await driver.startup()
    await driver.finish()

    assert reply == {
        "type": "lifespan.startup.failed",
        "message": (
            "데이터베이스(127.0.0.1:1/probe)를 확인하다 뜻밖의 오류로 멈췄습니다(RuntimeError).\n"
            "  이 판의 결함일 수 있습니다."
            " 예외의 글과 역추적은 비밀번호가 섞일 수 있어 찍지 않습니다."
        ),
    }
    assert database.events == ["startup_problem", "close_started", "close_finished"]


async def test_확인이_예외를_던지고_닫기마저_예외를_던져도_시작_실패가_나간다() -> None:
    database = _Scripted(
        check_error=RuntimeError("확인 실패"), close_error=RuntimeError("닫기 실패")
    )
    driver = LifespanDriver(create_app(database=database, stderr=io.StringIO()))

    reply = await driver.startup()
    await driver.finish()

    assert reply["type"] == "lifespan.startup.failed"
    assert "확인하다 뜻밖의 오류로 멈췄습니다" in str(reply["message"])
    assert database.events == ["startup_problem", "close_started"]


async def test_내릴_때_닫기가_한_번_불린다() -> None:
    database = _Scripted()
    driver = LifespanDriver(create_app(database=database, stderr=io.StringIO()))
    await driver.startup()

    stopped = await driver.shutdown()
    await driver.finish()

    assert stopped == {"type": "lifespan.shutdown.complete"}
    assert database.events == ["startup_problem", "close_started", "close_finished"]


async def test_내릴_때_수명의_완료는_닫기가_끝난_뒤에_나간다() -> None:
    hold = asyncio.Event()
    database = _Scripted(hold_close=hold)
    driver = LifespanDriver(create_app(database=database, stderr=io.StringIO()))
    await driver.startup()

    await driver.request_shutdown()
    held = await driver.silence(0.3)
    hold.set()
    stopped = await driver.next_message()
    await driver.finish()

    assert held
    assert database.events == ["startup_problem", "close_started", "close_finished"]
    assert stopped == {"type": "lifespan.shutdown.complete"}


async def test_내릴_때_닫기가_실패하면_닫다_실패했다는_글이_종료_실패로_나간다() -> None:
    database = _Scripted(close_error=RuntimeError("닫기 실패"))
    driver = LifespanDriver(create_app(database=database, stderr=io.StringIO()))
    await driver.startup()

    stopped = await driver.shutdown()
    await driver.finish()

    assert stopped == {
        "type": "lifespan.shutdown.failed",
        "message": "데이터베이스(127.0.0.1:1/probe)의 연결을 닫다 오류가 났습니다(RuntimeError).",
    }


async def test_앱이_스스로_시작을_실패시켜도_닫기는_한_번_불린다() -> None:
    async def failing_app(scope: Scope, receive: Receive, send: Send) -> None:
        await receive()
        await send({"type": "lifespan.startup.failed", "message": "앱이 낸 실패"})

    database = _Scripted()
    driver = LifespanDriver(CheckDatabase(failing_app, database=database))

    reply = await driver.startup()
    await driver.finish()

    assert reply == {"type": "lifespan.startup.failed", "message": "앱이 낸 실패"}
    assert database.events == ["startup_problem", "close_started", "close_finished"]


async def test_앱이_아무_말_없이_끝나도_닫기는_한_번_불린다() -> None:
    async def silent_app(scope: Scope, receive: Receive, send: Send) -> None:
        await receive()

    database = _Scripted()
    sent: list[Message] = []

    async def receive() -> Message:
        return {"type": "lifespan.startup"}

    async def send(message: Message) -> None:
        sent.append(message)

    await CheckDatabase(silent_app, database=database)({"type": "lifespan"}, receive, send)

    assert sent == []
    assert database.events == ["startup_problem", "close_started", "close_finished"]
