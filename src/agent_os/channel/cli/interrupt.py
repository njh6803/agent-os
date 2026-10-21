"""CLI 의 Ctrl+C. 첫 번째는 실행을 취소해 MCP 서버를 닫은 뒤 끝내고, 두 번째는 닫기를 기다리지 않고
곧바로 끝낸다(ADR 0034 의 2026-10-17·2026-10-21 이력).

조합 층의 run 과 resume 이 `asyncio.run` 대신 `run_interruptibly` 를 부른다. 그 앞에 SIGINT 처리기를
달아 asyncio 의 러너가 제 처리기를 달지 않게 하고(러너는 SIGINT 처리기가 기본값일 때만 단다. Python
3.12 `asyncio/runners.py`), 끝나면 이전 처리기를 되돌린다. 처리기가 기본값이 아니면 러너와 같이
달지 않고 `asyncio.run` 그대로 돈다. 셸이 작업 제어 없이 띄운 백그라운드 작업은 SIGINT 를 무시한 채
시작하고, 그 무시가 같은 터미널의 Ctrl+C 에서 그 실행을 지킨다. 처리기는 주 스레드에서만 달 수 있다
(`signal.signal` 이 다른 스레드에서 ValueError 를 낸다). CLI 진입점과 `tests/test_main.py` 의
in-process 호출이 모두 주 스레드다. serve 는 이것을 쓰지 않는다. uvicorn 이 제 처리기를 단다.

**첫 번째는 주 코루틴을 감싼 anyio 취소 범위의 취소다.** 주 태스크의 네이티브 취소(러너의 첫
번째)로 전하면, 서버를 닫는 도중에 온 첫째 뒤 mcp 2.3.0 에서 CLI 가 10초 안에 끝나지 않았다(ADR 0034
의 2026-10-21 이력. 상류의 무엇이 끝나지 않는지는 가르지 않았다). 범위의 취소는 보호된 닫기가 끝난
뒤에 전해지므로, 도구 호출 도중이든 답이 보인 뒤 서버를 닫는 도중이든 한 번이면 서버를 닫고 끝난다.
신호 처리기는 루프가 기다리는 도중에도 주 스레드에서 돌지만 POSIX 의 루프는 그것으로 깨어나지
않는다. asyncio 는 `add_signal_handler` 를 쓸 때만 신호의 깨움 서술자를 달고, 윈도우의 Proactor
루프만 처음부터 단다(Python 3.12 `asyncio/unix_events.py`·`proactor_events.py`). 그래서 취소를
`loop.call_soon_threadsafe` 로 루프에 맡겨 두 OS 에서 깨운다. 범위를 잡기 전에 눌렸으면 범위를 잡는
자리가 곧바로 취소하고, 루프가 닫힌 뒤에 눌렸으면 닫을 것이 없어 그 자리에서 끝낸다. 범위의 취소는
범위를 나갈 때까지 기다림마다 다시 들어와, 취소된 실행이 범위 안에서 보호 없이 기다리는
정리(에이전트의 `finally` 안의 await)는 곧바로 끊긴다.

**두 번째는 표준 에러에 다른 한 줄을 쓰고 정리 없이 곧바로 끝난다.** mcp 2.3.0 의 닫기가 닫는 도중의
둘째 네이티브 취소에서 끝나지 않아서다(`.scratch/mcp-shutdown/spec.md` 의 "CLI의 Ctrl+C"). 곧바로
끝낸 뒤 남은 MCP 서버는 윈도우에서는 이 프로세스가 끝나며 닫힌 Job Object 가 함께 거두고, POSIX
에서는 남을 수 있다. 트레이스는 결말 없이 남고 쓰던 줄이 반쪽으로 남을 수 있다. JSONL 어댑터는
끝나지 않은 마지막 줄을 커밋되지 않은 것으로 읽는다(`agent_os.adapters.jsonl` 의 모듈 독스트링).

**끝나는 꼴은 처리하지 않은 KeyboardInterrupt 로 끝나는 파이썬과 같다.** POSIX 는 SIGINT 로 죽고
(셸에서 130), 윈도우는 STATUS_CONTROL_C_EXIT(3221225786)다. 그 꼴을 보고 Ctrl+C 를 알아보는 부모
프로세스가 지금과 같이 반응한다. 추적 대신 한 줄을 남긴다. 그 한 줄은 트레이스의 상태를 말하지
않는다. 결말을 쓴 뒤 서버를 닫는 동안 눌렀을 수 있고, 처리기는 결말을 보지 않는다. 눌린 뒤 주
코루틴이 취소가 아닌 예외로 끝나도(취소를 받은 정리가 터졌다) 그 추적 대신 같은 한 줄로 끝난다. 누른
사람이 바란 것은 중단이다. 표준 출력이나 에러를 읽는 쪽이 먼저 떠나 쓰기가 실패해도 그 꼴로 끝난다.
"""

from __future__ import annotations

import asyncio
import contextlib
import io
import os
import signal
import sys
from collections.abc import Callable, Coroutine
from types import FrameType
from typing import NoReturn

import anyio

STATUS_CONTROL_C_EXIT = 0xC000013A
# `os._exit` 는 C int 를 받아 0xC000013A 를 그대로 주면 OverflowError 다(명세의 프로브가 잡았다).
# 같은 32비트를 부호 있는 값으로 준다.
_EXIT_CODE_CONTROL_C = STATUS_CONTROL_C_EXIT - 2**32
INTERRUPTED = "실행을 중단했다."
FORCED = "실행을 중단했다. MCP 서버가 닫히기를 기다리지 않고 끝낸다."


def run_interruptibly[T](main: Callable[[], Coroutine[object, object, T]]) -> T:
    """`asyncio.run(main())` 과 같되 Ctrl+C 를 직접 받는다. 눌렸으면 돌아오지 않고 중단의 꼴로
    끝난다. 주 코루틴이 값을 돌려주든 예외로 끝나든 같다. SIGINT 처리기가 기본값이 아니면(무시,
    다른 처리기) 받지 않고 `asyncio.run(main())` 그대로다."""
    if signal.getsignal(signal.SIGINT) is not signal.default_int_handler:
        return asyncio.run(main())
    presses = _Presses()
    previous = signal.signal(signal.SIGINT, presses.on_sigint)
    try:
        outcome = _run_guarded(presses, main)
        # 처리기를 단 채 견준다. 되돌린 뒤라면 그 사이의 둘째가 KeyboardInterrupt 의 추적을 찍는다.
        if isinstance(outcome, _Cancelled) or presses.pressed:
            _end_interrupted()
    finally:
        signal.signal(signal.SIGINT, previous)
    return outcome


def _run_guarded[T](
    presses: _Presses, main: Callable[[], Coroutine[object, object, T]]
) -> T | _Cancelled:
    """주 코루틴을 범위 아래에서 돌린다. 눌린 뒤에 난 예외는 추적 대신 중단의 꼴로 끝낸다."""
    try:
        return asyncio.run(presses.guarded(main))
    except BaseException:
        if presses.pressed:
            _end_interrupted()
        raise


class _Cancelled:
    """첫 번째로 취소되어 범위가 그 취소를 삼켰다는 표지. 주 코루틴의 반환값과 가르려고 둔다."""


class _Presses:
    """SIGINT 처리기와 그것이 취소하는 범위."""

    def __init__(self) -> None:
        self.pressed = False
        self._scope: anyio.CancelScope | None = None
        self._loop: asyncio.AbstractEventLoop | None = None

    async def guarded[T](self, main: Callable[[], Coroutine[object, object, T]]) -> T | _Cancelled:
        with anyio.CancelScope() as scope:
            self._scope = scope
            self._loop = asyncio.get_running_loop()
            if self.pressed:  # 범위를 잡기 전에 눌렸다
                scope.cancel()
            return await main()
        return _Cancelled()

    def on_sigint(self, signum: int, frame: FrameType | None) -> None:
        if self.pressed:
            _write_unbuffered(FORCED)
            _die_interrupted()
        self.pressed = True
        scope, loop = self._scope, self._loop
        if scope is None or loop is None:
            return  # 범위를 잡기 전이다. `guarded` 가 범위를 잡으며 취소한다
        try:
            loop.call_soon_threadsafe(scope.cancel)
        except RuntimeError:  # 루프가 닫혔다. 닫을 것이 없다
            _end_interrupted()


def _end_interrupted() -> NoReturn:
    """첫 번째의 끝. 한 줄을 남기고 중단의 꼴로 끝난다.

    표준 출력이나 에러를 읽는 쪽이 먼저 떠났으면(`| head`) 쓰기가 OSError(BrokenPipeError 따위)를
    낸다. 한 줄을 남기지 못해도 끝나는 꼴은 지킨다. 시작 때부터 표준 출력이 없거나(`sys.stdout` 이
    None) 파일 객체가 닫힌 것은 CLI 가 만들지 않는 상태라 받지 않는다.
    """
    with contextlib.suppress(OSError):
        sys.stdout.flush()
    with contextlib.suppress(OSError):
        sys.stderr.write(f"{INTERRUPTED}\n")
        sys.stderr.flush()
    _die_interrupted()


def _write_unbuffered(line: str) -> None:
    """신호 처리기에서 표준 에러에 한 줄을 쓴다. 주 스레드가 표준 에러에 쓰는 도중에도 돌 수 있어
    버퍼(그 잠금)를 거치지 않고 그 아래의 원시 파일에 쓴다.

    `os.write(2, …)` 로 쓰지 않는 까닭은 윈도우 콘솔이다. 콘솔의 원시 파일(`_WindowsConsoleIO`)은
    UTF-8 을 받아 콘솔에 그리고, 파일 서술자 2 에 바로 쓴 바이트는 콘솔의 코드 페이지(cp949)로 읽혀
    한글이 깨진다(어림, 콘솔에서 재지 않았다). 층의 모양이 그렇지 않으면 서술자에 쓴다.
    """
    data = f"{line}\n".encode()
    raw = _raw_stderr()
    with contextlib.suppress(OSError):
        if raw is None:
            os.write(2, data)
        else:
            raw.write(data)


def _raw_stderr() -> io.RawIOBase | None:
    """표준 에러의 텍스트 층 아래 버퍼 층 아래의 원시 파일. 층의 모양이 다르면 없다.

    typeshed 의 `TextIOWrapper` 와 `BufferedWriter` 는 제네릭이라 `isinstance` 로 좁히면 형식 인자가
    알 수 없음으로 남는다. 그래서 층을 이름으로 꺼내고 끝의 원시 파일만 형식으로 좁힌다.
    """
    buffer = getattr(sys.stderr, "buffer", None)
    raw = getattr(buffer, "raw", None)
    return raw if isinstance(raw, io.RawIOBase) else None


def _die_interrupted() -> NoReturn:
    """처리하지 않은 KeyboardInterrupt 로 끝나는 파이썬과 같은 꼴로 곧바로 끝난다."""
    if sys.platform == "win32":
        os._exit(_EXIT_CODE_CONTROL_C)
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    os.kill(os.getpid(), signal.SIGINT)
    os._exit(128 + signal.SIGINT)
