"""취소 범위 안에서 yield 하는 제너레이터를 소비하는 태스크가
이벤트 사이에 await 하면 무엇이 되나."""

import math
import traceback

import anyio


async def producer():
    with anyio.CancelScope():
        yield 1
        yield 2


async def consume(send, label: str) -> None:
    try:
        async for item in producer():
            try:
                await send.send(item)
            except anyio.BrokenResourceError:
                pass
        print(label, "끝까지 갔다")
    except Exception:
        print(label, "예외:")
        traceback.print_exc()


async def main() -> None:
    # 받는 쪽이 이미 닫힌 흐름에 기다리며 넣는다.
    send, receive = anyio.create_memory_object_stream[int](4)
    receive.close()
    async with anyio.create_task_group() as group:
        group.start_soon(consume, send, "await send")

    send2, receive2 = anyio.create_memory_object_stream[int](math.inf)
    receive2.close()

    async def consume_nowait() -> None:
        async for item in producer():
            try:
                send2.send_nowait(item)
            except anyio.BrokenResourceError:
                pass
        print("send_nowait 끝까지 갔다")

    async with anyio.create_task_group() as group:
        group.start_soon(consume_nowait)


anyio.run(main)
