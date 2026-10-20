"""CLI 의 Ctrl+C. 첫 번째는 실행을 취소해 닫기를 마치고, 두 번째는 닫기를 기다리지 않고 끝낸다.

(시제품. `.scratch/mcp-shutdown/probes/full_stack.py`가 저장소 사본에 얹어 잰다. 조합 층의 run 과
resume 이 `asyncio.run` 대신 부르는 자리다.)

`asyncio.run` 의 러너는 SIGINT 처리기가 기본값일 때만 자기 처리기를 단다(Python 3.12
`asyncio/runners.py`). 여기서 먼저 달면 러너는 달지 않는다. 러너의 처리기는 둘째 SIGINT 에
KeyboardInterrupt 를 올리고 남은 태스크를 다시 취소해 끝나기를 기다리는데, mcp 2.3.0 의 닫기가 그
기다림에서 끝나지 않는다(명세 "CLI의 Ctrl+C"). 첫 번째는 그 러너처럼 주 태스크를 한 번 취소한다.

중단으로 끝나는 꼴은 처리하지 않은 KeyboardInterrupt 로 끝나는 파이썬과 같다. POSIX 는 SIGINT 로
죽고(셸에서 130), 윈도우는 STATUS_CONTROL_C_EXIT 다. 두 번째는 정리 없이 끝나 남은 MCP 서버를
윈도우에서는 Job Object 가, POSIX 에서는 런처의 부모 감시가 거둔다.
"""

from __future__ import annotations

import asyncio
import os
import signal
import sys
from collections.abc import Callable, Coroutine
from types import FrameType
from typing import NoReturn

STATUS_CONTROL_C_EXIT = 0xC000013A
# `os._exit`는 C int 를 받아 0xC000013A 를 그대로 주면 OverflowError 다(프로브의 첫 회차가 그것으로
# 끝나지 않았다). 같은 32비트를 부호 있는 값으로 준다.
_EXIT_CODE_CONTROL_C = STATUS_CONTROL_C_EXIT - 2**32
INTERRUPTED = "실행을 중단했다. 트레이스에는 결말 없이 남는다."
FORCED = "닫기를 기다리지 않고 끝낸다. 트레이스에는 결말 없이 남는다."


def run_interruptibly[T](main: Callable[[], Coroutine[object, object, T]]) -> T:
    """`asyncio.run(main())`과 같되 Ctrl+C 를 직접 받는다."""
    presses = _Presses()

    async def held() -> T:
        presses.hold(asyncio.current_task())
        return await main()

    previous = signal.signal(signal.SIGINT, presses.on_sigint)
    try:
        return asyncio.run(held())
    except asyncio.CancelledError:
        if not presses.pressed:
            raise
        _end_interrupted()
    finally:
        signal.signal(signal.SIGINT, previous)


class _Presses:
    """SIGINT 처리기. 첫 번째는 주 태스크를 한 번 취소하고, 두 번째는 곧바로 끝낸다."""

    def __init__(self) -> None:
        self.pressed = False
        self._task: asyncio.Task[object] | None = None

    def hold(self, task: asyncio.Task[object] | None) -> None:
        self._task = task

    def on_sigint(self, signum: int, frame: FrameType | None) -> None:
        task = self._task
        if not self.pressed and task is not None and not task.done():
            self.pressed = True
            task.cancel()
            task.get_loop().call_soon_threadsafe(lambda: None)
            return
        # 신호 처리기는 표준 에러에 쓰는 도중에도 돌 수 있어 버퍼를 거치지 않고 쓴다.
        os.write(2, f"{FORCED}\n".encode())
        _die_interrupted()


def _end_interrupted() -> NoReturn:
    """첫 번째로 취소된 실행이 닫기를 마친 뒤의 끝. 한 줄을 남기고 중단의 꼴로 끝난다."""
    sys.stdout.flush()
    sys.stderr.write(f"{INTERRUPTED}\n")
    sys.stderr.flush()
    _die_interrupted()


def _die_interrupted() -> NoReturn:
    """처리하지 않은 KeyboardInterrupt 로 끝나는 파이썬과 같은 꼴로 곧바로 끝난다."""
    if sys.platform == "win32":
        os._exit(_EXIT_CODE_CONTROL_C)
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    os.kill(os.getpid(), signal.SIGINT)
    os._exit(128 + signal.SIGINT)
