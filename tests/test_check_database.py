"""`CheckDatabase`(`agent_os.http.database`) 가 안쪽 앱이 스스로 수명을 실패시키거나 말없이 끝나도
연결 묶음을 한 번만 닫는지 잰다.

`serve` 의 조립을 거치는 사례는 `tests/test_main.py` 가 한다. 여기서는 안쪽 앱을 손으로 짠 작은
ASGI 앱으로 갈아 끼워, 진짜 앱이 만들기 어려운 갈래(앱이 먼저 시작을 실패시킨다, 종료를 실패시킨다,
아무 말 없이 끝난다)를 민다.
"""

from __future__ import annotations

from starlette.types import Message, Receive, Scope, Send
from tests.fake_database import FakeDatabase, LifespanDriver

from agent_os.http.database import CheckDatabase


async def _fails_startup(scope: Scope, receive: Receive, send: Send) -> None:
    await receive()
    await send({"type": "lifespan.startup.failed", "message": "앱이 스스로 실패했다"})


async def _fails_shutdown(scope: Scope, receive: Receive, send: Send) -> None:
    await receive()
    await send({"type": "lifespan.startup.complete"})
    await receive()
    await send({"type": "lifespan.shutdown.failed", "message": "앱이 스스로 실패했다"})


async def _ends_silently(scope: Scope, receive: Receive, send: Send) -> None:
    await receive()


async def test_앱이_스스로_시작을_실패시켜도_닫기는_한_번_불리고_그_글이_그대로_나간다() -> None:
    fake = FakeDatabase()
    driver = LifespanDriver(CheckDatabase(_fails_startup, database=fake))

    reply = await driver.startup()
    await driver.finish()

    assert reply == {"type": "lifespan.startup.failed", "message": "앱이 스스로 실패했다"}
    assert fake.events == ["startup_problem", "close_started", "close_finished"]


async def test_앱이_스스로_종료를_실패시켜도_닫기는_한_번_불리고_그_글이_그대로_나간다() -> None:
    fake = FakeDatabase()
    driver = LifespanDriver(CheckDatabase(_fails_shutdown, database=fake))
    await driver.startup()

    reply = await driver.shutdown()
    await driver.finish()

    assert reply == {"type": "lifespan.shutdown.failed", "message": "앱이 스스로 실패했다"}
    assert fake.events == ["startup_problem", "close_started", "close_finished"]


async def test_앱이_아무_말_없이_끝나도_닫기는_한_번_불린다() -> None:
    fake = FakeDatabase()
    sent: list[Message] = []

    async def receive() -> Message:
        return {"type": "lifespan.startup"}

    async def send(message: Message) -> None:
        sent.append(message)

    # 앱이 답을 보내지 않고 끝나므로 구동자(답을 기다린다)가 아니라 앱을 직접 부른다.
    await CheckDatabase(_ends_silently, database=fake)({"type": "lifespan"}, receive, send)

    assert sent == []
    assert fake.events == ["startup_problem", "close_started", "close_finished"]
