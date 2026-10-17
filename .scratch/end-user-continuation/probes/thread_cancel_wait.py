"""anyio.to_thread.run_sync 의 기본값에서 취소가 스레드 끝을 기다리는지 잰다.

명세 "거슬러 읽기의 상한과 자리"의 "취소(앱이 멈춤)가 오면 그 읽기가 끝나기를 기다린다"의 근거다.
기본값은 `abandon_on_cancel=False` 다. 스레드 함수는 0.5초 잠들고, 0.05초 뒤 바깥 취소 범위를
취소한다 — 스레드가 도는 동안 취소가 온다.

표지는 셋이다. 취소를 거는 순간 스레드 함수가 아직 끝나지 않았다(재려는 상황 — 스레드가 도는
동안 취소가 왔다). 기본값에서는 취소가 범위를 나온 시점에 스레드 함수가 끝났다는 표시(done)가 이미
서 있다(기다렸다). 대조인 `abandon_on_cancel=True` 에서는 범위를 곧바로 나오고 그때 done 이 서지
않았다(양성 대조). 모두 서야 측정이고, 아니면 종료 코드가 1이다.
"""

import asyncio
import threading
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass

import anyio
import anyio.to_thread

type Placement = Callable[[Callable[[], None]], Awaitable[None]]


async def _waiting(work: Callable[[], None]) -> None:
    """이어 가기가 쓸 모양 그대로 — 인자 없이 보내 기본값(취소되면 스레드를 기다린다)을 쓴다."""
    await anyio.to_thread.run_sync(work)


async def _abandoning(work: Callable[[], None]) -> None:
    """양성 대조. 취소되면 스레드를 버린다."""
    await anyio.to_thread.run_sync(work, abandon_on_cancel=True)


@dataclass(frozen=True)
class Outcome:
    """한 자리의 결과. 범위를 나오기까지의 초, 취소를 건 순간 스레드가 돌고 있었는지, 범위를 나온
    순간 스레드가 끝났는지."""

    seconds: float
    running_at_cancel: bool
    done_at_exit: bool


async def _cancel_while_running(place: Placement) -> Outcome:
    """스레드가 도는 동안 취소하고 그 결과를 돌려준다."""
    done = threading.Event()
    running_at_cancel = False

    def work() -> None:
        time.sleep(0.5)
        done.set()

    began = time.perf_counter()
    with anyio.CancelScope() as scope:

        async def cancel_soon() -> None:
            nonlocal running_at_cancel
            await anyio.sleep(0.05)
            running_at_cancel = not done.is_set()
            scope.cancel()

        async with anyio.create_task_group() as group:
            group.start_soon(cancel_soon)
            await place(work)
    return Outcome(time.perf_counter() - began, running_at_cancel, done.is_set())


async def main() -> int:
    waited = await _cancel_while_running(_waiting)
    abandoned = await _cancel_while_running(_abandoning)
    for name, outcome in (("기본값", waited), ("대조(버림)", abandoned)):
        print(
            f"{name}: 범위를 나오기까지 {outcome.seconds:.3f}초, "
            f"취소할 때 스레드가 돌고 있었다={outcome.running_at_cancel}, "
            f"나올 때 스레드 끝남={outcome.done_at_exit}"
        )
    measured = (
        waited.running_at_cancel
        and abandoned.running_at_cancel
        and waited.done_at_exit
        and waited.seconds >= 0.45
        and not abandoned.done_at_exit
        and abandoned.seconds < 0.3
    )
    print(f"측정의 표지: {measured}")
    return 0 if measured else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
