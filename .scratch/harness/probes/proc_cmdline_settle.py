"""막 띄운 자식의 명령 줄을 한 번 읽기가 빈 값으로 읽는 틈과, 그 틈을
`tools/proc_command_line.py`의 `command_line`이 메우는지 잰다(harness 티켓 013, 대기열 456).

회차 하나: 표지(회차마다 새 uuid)를 인자로 든 잠자는 파이썬 자식을 `Popen`으로 띄우고, 돌아온
직후 `command_line`과 같은 부름(`settled`에 `_read_once`와 `_alive`)을 한 번 하되, 읽기를
세는 함수로 감싼다. 그 안의 첫 읽기가 첫 읽기의 갈래이고, 기다리지 않는 한 번 읽기라 고치기
전의 `command_line`과 같은 길이다. 첫 읽기가 None 이면 그 자리에서 진단을 읽고, 도구가 다시
읽어 그 틈을 메웠는지를 센다. 그 뒤 10초까지 한 번 읽기를 거듭해
표지가 든 명령 줄이 나오면 그 회차를 측정으로 센다(그 pid 가 그 명령 줄을 가진 우리 자식이라는
양성 대조). 끝내 나오지 않으면 측정 아님이다. 자식은 pid 가 아니라 `Popen`의 핸들로 끄고
거둔다. 거두기 전의 핸들은 그 자식만 가리켜, 끝난 자식의 pid 를 받은 남의 프로세스를 끄는 일이
없다(`.claude/rules/probes.md`의 끄기 항목이 막는 길).

첫 읽기가 None 이면 그 까닭을 가르려고 같은 순간 가까이에서 날 값을 더 읽는다.
- 리눅스: `/proc/<pid>/cmdline`의 바이트 수와 `/proc/<pid>/stat`의 상태 글자.
- 윈도: 그 모듈의 PEB 읽기를 단계마다 다시 밟아 어디서 끊겼는지(OpenProcess, PEB 의 매개변수
  주소, CommandLine 의 UNICODE_STRING)와, 매개변수 블록의 Flags 의 정규화 비트(0x1,
  RTL_USER_PROC_PARAMS_NORMALIZED)와 CommandLine.Buffer 값. 그 둘은 첫 읽기보다 조금 늦게 읽어
  첫 읽기의 순간과 같지 않을 수 있다.

쓰임: `uv run python .scratch/harness/probes/proc_cmdline_settle.py [회차 수]`(기본 500). 리눅스는
컨테이너(`python:3.12.10-slim-bookworm`. CI 의 ubuntu-latest 와 그 파이썬과는 판이 다르다)에서
저장소를 읽기 전용으로 붙여 표준 라이브러리 파이썬으로 돈다(README 행). 종료 코드는
`tools/probe_kit.py`의 `Rounds.exit_code`다.
"""

from __future__ import annotations

import ctypes
import subprocess
import sys
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from tools.probe_kit import Rounds  # noqa: E402

from tools import proc_command_line as pcl  # noqa: E402

SETTLE = 10.0
NORMALIZED = 0x1
FLAGS_OFFSET = 0x08


def _linux_detail(pid: int) -> str:
    try:
        raw = Path(f"/proc/{pid}/cmdline").read_bytes()
    except OSError as error:
        return f"cmdline 못 읽음 {type(error).__name__}"
    try:
        stat = Path(f"/proc/{pid}/stat").read_text()
        state = stat.rsplit(")", 1)[1].split()[0]
    except (OSError, IndexError):
        state = "?"
    return f"cmdline {len(raw)}바이트, 상태 {state}"


def _windows_detail(pid: int) -> str:
    kernel, ntdll, _ = pcl._windows_api()
    handle = kernel.OpenProcess(pcl._QUERY_LIMITED | pcl._VM_READ, pcl._INHERIT_HANDLE, pid)
    if not handle:
        return f"OpenProcess 실패 {ctypes.get_last_error()}"
    try:
        parameters = pcl._parameters(kernel, ntdll, handle)
        if parameters is None:
            return "매개변수 주소 없음"
        if parameters == 0:
            return "매개변수 주소 0"
        flags_raw = pcl._read_memory(kernel, handle, parameters + FLAGS_OFFSET, 4)
        raw = pcl._read_memory(kernel, handle, parameters + pcl._PARAMS_COMMAND_LINE, 16)
    finally:
        kernel.CloseHandle(handle)
    if flags_raw is None or raw is None:
        return "매개변수 블록 못 읽음"
    flags = int.from_bytes(flags_raw, "little")
    length = int.from_bytes(raw[0:2], "little")
    buffer = int.from_bytes(raw[8:16], "little")
    normalized = "정규화" if flags & NORMALIZED else "비정규화"
    kind = "오프셋 꼴" if buffer < 0x10000 else "주소 꼴"
    return f"{normalized}, 길이 {length}, Buffer {kind}"


def _detail(pid: int) -> str:
    try:
        if sys.platform == "linux":
            return _linux_detail(pid)
        if sys.platform == "win32":
            return _windows_detail(pid)
    except (OSError, AttributeError, ValueError, ctypes.ArgumentError) as error:
        return f"진단 실패 {error!r}"
    return "다른 OS"


def _one(rounds: Rounds, index: int) -> None:
    marker = f"settle-{uuid.uuid4()}"
    with rounds.round(f"{index}") as current:
        process = subprocess.Popen(
            [sys.executable, "-c", "import time; time.sleep(60)", marker],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            reads: list[tuple[str, ...] | None] = []
            details: list[str] = []

            def read(pid: int) -> tuple[str, ...] | None:
                argv = pcl._read_once(pid)
                reads.append(argv)
                if argv is None and len(reads) == 1:
                    details.append(_detail(pid))
                return argv

            # `command_line`과 같은 부름이고 읽기만 센다
            tool = pcl.settled(
                read,
                pcl._alive,
                process.pid,
                settle=pcl.SETTLE_SECONDS,
                clock=time.monotonic,
                sleep=time.sleep,
            )
            first = reads[0]
            argv = tool
            deadline = time.monotonic() + SETTLE
            while (argv is None or marker not in argv) and time.monotonic() < deadline:
                time.sleep(0.01)
                argv = pcl._read_once(process.pid)
            if argv is not None and marker in argv:
                if first is not None:
                    result = "첫 읽기 명령 줄" if marker in first else "첫 읽기 다른 명령 줄"
                elif tool is not None and marker in tool:
                    result = f"첫 읽기 None({details[0]}), 도구가 메움"
                else:
                    result = f"첫 읽기 None({details[0]}), 도구도 못 읽음"
                current.mark(measured=True, result=result)
        finally:
            process.kill()  # Popen 의 핸들이라 우리 자식만 끈다
            process.wait(timeout=60)


def main() -> int:
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    rounds = Rounds()
    for index in range(count):
        _one(rounds, index)
    print(f"{sys.platform} {sys.version.split()[0]}, 회차 {count}")
    print(rounds.summary())
    return rounds.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
