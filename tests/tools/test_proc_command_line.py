"""tools/proc_command_line.py: pid 하나의 명령 줄을 낱말로 읽는다.

살아 있는 하위 프로세스를 띄워 실제로 읽는다. 리눅스 CI 에서는 `/proc`, 이 PC 에서는 PEB 를 읽는다.
"""

from __future__ import annotations

import subprocess
import sys
import time
import uuid

from tools.proc_command_line import argv_from_cmdline, command_line


def test_살아_있는_프로세스의_명령_줄을_낱말로_읽는다() -> None:
    marker = f"표지 {uuid.uuid4()}"  # 공백이 든 낱말도 한 낱말로 돌아온다
    process = subprocess.Popen(
        [sys.executable, "-c", "import time; time.sleep(120)", marker, ""],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        argv = command_line(process.pid)
    finally:
        process.kill()
        process.wait(timeout=60)

    assert argv is not None
    assert marker in argv
    assert argv[-2:] == (marker, "")


def test_끝났지만_거두지_않은_자식은_빈_값이다() -> None:
    process = subprocess.Popen(
        [sys.executable, "-c", "pass"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        # 거두면 pid 가 다른 프로세스에 갈 수 있어 poll 도 부르지 않고 끝나기를 기다린다
        deadline = time.monotonic() + 60
        argv = command_line(process.pid)
        while argv is not None and time.monotonic() < deadline:
            time.sleep(0.1)
            argv = command_line(process.pid)
    finally:
        process.wait(timeout=60)

    assert argv is None


def test_없는_pid_와_0_이하의_pid_는_빈_값이다() -> None:
    assert command_line(0) is None
    assert command_line(-5) is None
    assert command_line(2**31 - 1) is None  # 리눅스의 pid 상한과 윈도의 pid 보다 크다


def test_proc_의_명령_줄은_끝의_NUL_하나만_떼고_빈_낱말을_지킨다() -> None:
    assert argv_from_cmdline(b"claude\0-p\0\0--resume\0s-1\0") == (
        "claude",
        "-p",
        "",
        "--resume",
        "s-1",
    )
    assert argv_from_cmdline(b"") == ()  # 거두지 않은 좀비의 cmdline 은 비었다
