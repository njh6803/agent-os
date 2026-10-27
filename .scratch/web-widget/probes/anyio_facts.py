"""ADR 0039 가 anyio 에 기대는 사실 둘을 잰다.

하나. 몸통(태스크 그룹을 연 태스크)이 그룹 안에서 던진 취소 아닌 예외가 그룹 밖으로 나올 때
감싸이는지. 시제품은 그것을 보고 몸통의 예외를 그룹 안에서 붙잡아 그룹 밖에서 다시 던졌다(명세의
실시간 중계 절).

둘. 크기 0 의 메모리 흐름에서, 기다리던 받는 쪽에 항목이 넘어간 뒤 받는 쪽이 깨어나기 전에 취소되면
그 항목이 사라지는지. ADR 0039 의 거부한 안 넷째(이벤트 자체를 메모리 흐름으로 보낸다)의 근거다. 앞
세션은 `anyio/streams/memory.py` 를 읽은 어림으로 적었고, 셀프 리뷰가 취소의 종류에 따라 갈린다고
짚었다. 그래서 취소를 두 갈래로 가른다. asyncio 의 날 취소(`Task.cancel()`)와 anyio 취소 범위의
취소(`CancelScope.cancel()`)다.

회차는 다섯이다.
- 감쌈: 몸통이 자식 하나가 잠든 그룹 안에서 `ValueError` 를 던진다. 나온 예외의 타입을 본다.
- 감쌈 대조: 같은 `ValueError` 를 그룹 없이 던진다. 붙잡는 쪽이 타입을 가른다는 양성 대조다.
- 흐름 대조: 받는 쪽이 기다리는 중에 `send_nowait` 하고 취소하지 않는다. 항목이 닿는다는 양성
  대조다.
- 흐름 날 취소: `send_nowait` 바로 뒤에 받는 쪽 태스크의 `cancel()` 을 부른다.
- 흐름 범위 취소: `send_nowait` 바로 뒤에 받는 쪽을 감싼 `CancelScope` 의 `cancel()` 을 부른다.

흐름 회차의 표지는 받는 쪽 태스크가 끝나며 적은 결말(받은 항목, 또는 취소)과 그 뒤 흐름에 남은
항목의 수다. 둘 다 적힌 회차만 측정이다. 받는 쪽이 취소로 끝났고 흐름이 비었으면 그 항목은 사라진
것이다.

못 보는 것.
- trio 백엔드. 이 저장소는 asyncio 에서만 돈다.
- 받는 쪽이 `receive()` 가 아니라 `async for` 로 기다리는 것. `async for` 는 `receive()` 를 부른다
  (`MemoryObjectReceiveStream.__anext__`, 코드를 읽었다).

돌리기: 저장소 루트에서 `uv run python .scratch/web-widget/probes/anyio_facts.py`.
"""

from __future__ import annotations

import asyncio
import sys
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from importlib.metadata import version
from pathlib import Path

import anyio

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from tools.probe_kit import Rounds  # noqa: E402


async def _raise_in_group() -> None:
    async with anyio.create_task_group() as group:
        group.start_soon(anyio.sleep, 10)
        raise ValueError("몸통의 예외")


async def _raise_alone() -> None:
    raise ValueError("몸통의 예외")


async def _caught(body: Callable[[], Awaitable[None]]) -> str:
    try:
        await body()
    except BaseException as error:  # noqa: BLE001 — 무엇이 나오는지가 재는 것이다
        inner = ""
        if isinstance(error, BaseExceptionGroup):
            inner = " 안: " + ", ".join(type(item).__name__ for item in error.exceptions)
        return type(error).__name__ + inner
    return "<예외 없음>"


@dataclass
class _Receiver:
    outcome: str = ""


async def _stream_round(cancel: str) -> tuple[str, int]:
    """받는 쪽이 기다리게 한 뒤 항목 하나를 넘기고 `cancel` 대로 취소한다. 받는 쪽의 결말과 흐름에
    남은 항목의 수를 낸다. 받는 쪽은 anyio 태스크 그룹이 아니라 asyncio 태스크로 띄워, 날 취소가
    그룹의 처리에 섞이지 않게 한다."""
    send, receive = anyio.create_memory_object_stream[str]()
    receiver = _Receiver()
    scope = anyio.CancelScope()

    async def wait_for_item() -> None:
        try:
            with scope:
                receiver.outcome = f"받음: {await receive.receive()}"
                return
        except asyncio.CancelledError:
            receiver.outcome = "취소됨(CancelledError)"
            raise
        receiver.outcome = "취소됨(범위가 삼킴)"

    task = asyncio.create_task(wait_for_item())
    # 받는 쪽이 `receive()` 안에서 기다릴 때까지 돈다.
    while receive.statistics().tasks_waiting_receive == 0:
        await asyncio.sleep(0)
    send.send_nowait("항목")
    if cancel == "날":
        task.cancel()
    elif cancel == "범위":
        scope.cancel()
    await asyncio.wait({task}, timeout=5)
    left = receive.statistics().current_buffer_used
    await send.aclose()
    await receive.aclose()
    return receiver.outcome, left


async def main() -> int:
    rounds = Rounds()
    print(f"python: {sys.version.split()[0]}  anyio: {version('anyio')}  백엔드: asyncio")

    with rounds.round("감쌈") as current:
        caught = await _caught(_raise_in_group)
        print(f"[감쌈] {caught}")
        if "ValueError" in caught:
            current.mark(measured=True, result=caught)

    with rounds.round("감쌈 대조") as current:
        caught = await _caught(_raise_alone)
        print(f"[감쌈 대조] {caught}")
        if "ValueError" in caught:
            current.mark(measured=True, result=caught)

    for label, cancel in (("흐름 대조", ""), ("흐름 날 취소", "날"), ("흐름 범위 취소", "범위")):
        with rounds.round(label) as current:
            outcome, left = await _stream_round(cancel)
            print(f"[{label}] 받는 쪽: {outcome!r}, 흐름에 남은 항목: {left}")
            if outcome:
                lost = outcome.startswith("취소됨") and left == 0
                current.mark(measured=True, result=("사라짐" if lost else outcome))

    print(rounds.summary())
    return rounds.exit_code()


if __name__ == "__main__":
    raise SystemExit(anyio.run(main))
