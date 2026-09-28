"""소비하는 태스크가 이벤트 사이의 await 에서 취소되면
제너레이터가 취소 범위 안에 멈춘 채 남는가."""

import anyio

reached = anyio.Event()


async def producer():
    with anyio.CancelScope():
        yield 1
        yield 2


async def consume_awaiting() -> None:
    async for _ in producer():
        reached.set()
        await anyio.sleep(10)  # 이벤트 사이의 await. 여기서 취소를 받는다


async def consume_sync() -> None:
    async for _ in producer():
        reached.set()
    await anyio.sleep(10)  # 제너레이터를 다 돈 뒤에 기다린다


async def trial(consume) -> None:
    global reached
    reached = anyio.Event()
    try:
        async with anyio.create_task_group() as group:
            group.start_soon(consume)
            await reached.wait()
            group.cancel_scope.cancel()
        print(consume.__name__, "깨끗하게 취소됐다")
    except BaseException as error:  # noqa: BLE001 - 프로브
        print(consume.__name__, "깨졌다:", type(error).__name__, error)


async def main() -> None:
    await trial(consume_sync)
    await trial(consume_awaiting)


anyio.run(main)
