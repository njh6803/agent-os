"""실행 타임아웃을 core 의 몸통(`_drive`) 안에 두면 걸린 모델 호출이 `run_failed` 로 끝나는지.

사용자가 걸린 실행이 동시 실행 칸을 붙잡는 열린 문제의 답으로 실행 타임아웃을 골랐다(ADR 0014
는 취소와 타임아웃을 범위 밖에 두었다). 들이려면 둘을 알아야 한다. (1) 타임아웃의 취소가
`run_failed` 로 바뀌려면 취소 범위가 core 의 `except Exception` 안에 있어야 한다 — anyio 의
`fail_after` 는 범위를 나갈 때 `TimeoutError`(Exception)를 내므로 그 자리면 된다. (2) 그 범위는
core 의 async generator 안에서 yield 를 건너고, 그 안에 MCP 어댑터의 연결(anyio 취소 범위를
쓴다)이 열려 있다. 채널의 `runs.py` 는 그 사이의 await 에서 받은 취소가 범위를 깨뜨린다고 적었다.
타임아웃의 취소가 같은 길을 깨뜨리지 않는지 실제 `McpTools` 와 픽스처 서버로 잰다.

모양은 둘이다.
- 안쪽: core `_drive` 를 흉내 낸 제너레이터가 `with anyio.fail_after(timeout)` 안에서 안쪽
  제너레이터(MCP 연결을 열고 모델 호출 대신 오래 잔다)를 돌리고, `TimeoutError` 를 받아
  `run_failed` 를 yield 한다. 소비자는 채널 `Runs._drive` 처럼 태스크 그룹의 다른 태스크에서
  await 없이 흐름에 넣는다.
- 바깥(대조군): 제너레이터에는 타임아웃이 없고 소비자가 `move_on_after` 로 자른다. ADR 0014 가
  거부한 "끊기면 취소" 와 같은 모양이라 `run_failed` 가 나지 않아야 한다.

둘 다 항목의 도착 시각, 마지막 항목, 걸린 시간, 태스크 그룹이 예외 없이 닫혔는지를 찍는다. 재는 것은
모델 호출 자리(`anyio.sleep`)의 취소다 — 도구 호출 중의 취소와 서버 프로세스의 소멸은 재지 않는다.

    PYTHONUTF8=1 uv run python .scratch/end-user-channel/probes/run_timeout.py
"""

from __future__ import annotations

import asyncio
import sys
import time
from collections.abc import AsyncGenerator, AsyncIterator, Mapping
from contextlib import aclosing
from pathlib import Path

import anyio
from anyio.streams.memory import MemoryObjectSendStream

from agent_os.adapters.mcp import McpTools
from agent_os.sdk import McpServer, PluginName

ROOT = Path(__file__).resolve().parents[3]
FIXTURE = ROOT / "tests" / "adapters" / "mcp_fixture_server.py"
SERVERS: Mapping[PluginName, McpServer] = {
    PluginName("fixture"): McpServer(command=sys.executable, args=(str(FIXTURE),))
}

type Item = dict[str, str]


async def execute(hang: float) -> AsyncGenerator[Item]:
    """core `execute()` 의 모양. MCP 연결 안에서 이벤트를 내고 모델 호출 자리에서 오래 잔다."""
    async with McpTools().connect(SERVERS) as connection:
        yield {"type": "tools", "count": str(len(connection.tools()))}
        yield {"type": "llm_called"}
        await anyio.sleep(hang)
        yield {"type": "run_finished"}


async def drive_inside(hang: float, timeout: float) -> AsyncIterator[Item]:
    """core `_drive` 의 모양에 타임아웃을 더한 것. 취소가 Exception 으로 바뀌어 결말이 붙는다."""
    try:
        with anyio.fail_after(timeout):
            async with aclosing(execute(hang)) as executed:
                async for item in executed:
                    yield item
    except Exception as error:
        yield {"type": "run_failed", "error": f"{type(error).__name__}: {error}"}


async def drive_plain(hang: float) -> AsyncIterator[Item]:
    """타임아웃 없는 몸통(지금의 core)."""
    try:
        async with aclosing(execute(hang)) as executed:
            async for item in executed:
                yield item
    except Exception as error:
        yield {"type": "run_failed", "error": f"{type(error).__name__}: {error}"}


async def pump(events: AsyncIterator[Item], send: MemoryObjectSendStream[Item]) -> None:
    """채널 `Runs._drive` 의 모양. 이벤트 사이에 await 하지 않는다."""
    with send:
        async for item in events:
            send.send_nowait(item)


async def pump_cut(events: AsyncIterator[Item], send: MemoryObjectSendStream[Item]) -> None:
    """대조군. 소비자가 바깥에서 자른다 — ADR 0014 가 거부한 모양."""
    with send:
        with anyio.move_on_after(TIMEOUT):
            async for item in events:
                send.send_nowait(item)
        async with aclosing(events):
            pass


# 타임아웃은 MCP 서버가 뜨는 시간(이 기계에서 1초 남짓)보다 길어야 한다. 짧으면 연결 도중에 끊겨
# yield 를 건넌 뒤의 취소가 아니라 연결 중의 취소를 재게 된다(처음 돌린 1초가 그랬다).
TIMEOUT = 6.0


async def run_case(title: str, *, inside: bool) -> None:
    started = time.perf_counter()
    received: list[tuple[float, Item]] = []
    failure: BaseException | None = None
    try:
        async with anyio.create_task_group() as group:
            send, receive = anyio.create_memory_object_stream[Item](100)
            if inside:
                group.start_soon(pump, drive_inside(100.0, TIMEOUT), send)
            else:
                group.start_soon(pump_cut, drive_plain(100.0), send)
            async with receive:
                async for item in receive:
                    received.append((time.perf_counter() - started, item))
    except BaseException as error:  # noqa: BLE001 — 무엇이 새는지 보려는 자리다
        failure = error
    elapsed = time.perf_counter() - started
    print(f"--- {title}")
    print(f"  항목(도착 초): {[(round(at, 2), item['type']) for at, item in received]}")
    last = received[-1][1] if received else None
    print(f"  마지막: {last}")
    print(f"  걸린 시간: {elapsed:.2f}s, 태스크 그룹 예외: {failure!r}")


async def main() -> None:
    await run_case("안쪽(core 몸통의 fail_after)", inside=True)
    await run_case("바깥(소비자의 move_on_after, 대조군)", inside=False)


if __name__ == "__main__":
    asyncio.run(main())
