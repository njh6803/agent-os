"""윈도에서 조회 권한으로는 열리고 읽기 권한으로는 열리지 않는 프로세스를 `command_line`이
기다리지 않고 None 으로 내는지 잰다(harness 티켓 013, `tools/proc_command_line.py`의
`_windows_alive`).

Toolhelp 스냅숏의 프로세스마다 `PROCESS_QUERY_LIMITED_INFORMATION`만으로 열어 보고, 그 모듈의 읽기와
같은 권한(`| PROCESS_VM_READ`)으로도 열어 본다. 앞의 것만 열린 프로세스가 재려는 상황이고, 그런
프로세스마다 `command_line`을 부른 걸린 시간을 잰다. 회차마다 부르기 직전과 직후에 같은 두 열기를
다시 해 그 상황이 그대로인 회차만 측정으로 센다(그새 끝나거나 권한이 바뀐 것은 측정 아님). 결과는
None 이고 1초 안이면 `즉시 None`, None 이고 그보다 오래면 `기다린 뒤 None`, 명령 줄이 나오면
`읽음`이다. 프로세스를 끄지 않는다.

쓰임: `uv run python .scratch/harness/probes/proc_cmdline_alive_gap.py`. 윈도에서만 돈다. 종료
코드는 `tools/probe_kit.py`의 `Rounds.exit_code`이고, 재려는 상황의 프로세스가 하나도 없으면 2다.
"""

from __future__ import annotations

import ctypes
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from tools.probe_kit import Rounds  # noqa: E402

from tools import proc_command_line as pcl  # noqa: E402


def _opens(kernel: ctypes.WinDLL, access: int, pid: int) -> bool:
    handle = kernel.OpenProcess(access, pcl._INHERIT_HANDLE, pid)
    if handle:
        kernel.CloseHandle(handle)
        return True
    return False


def _gap(kernel: ctypes.WinDLL, pid: int) -> bool:
    limited = _opens(kernel, pcl._QUERY_LIMITED, pid)
    return limited and not _opens(kernel, pcl._QUERY_LIMITED | pcl._VM_READ, pid)


def _snapshot() -> list[tuple[int, str]]:
    kernel, _, _ = pcl._windows_api()
    snapshot = kernel.CreateToolhelp32Snapshot(pcl._SNAPSHOT_PROCESSES, 0)
    found: list[tuple[int, str]] = []
    try:
        entry = pcl._ProcessEntry()
        entry.size = ctypes.sizeof(entry)
        more = kernel.Process32FirstW(snapshot, ctypes.byref(entry))
        while more:
            found.append((int(entry.pid), str(entry.exe)))
            more = kernel.Process32NextW(snapshot, ctypes.byref(entry))
    finally:
        kernel.CloseHandle(snapshot)
    return found


def main() -> int:
    if sys.platform != "win32":
        print("윈도에서만 돈다")
        return 2
    kernel, _, _ = pcl._windows_api()
    processes = _snapshot()
    targets = [(pid, exe) for pid, exe in processes if _gap(kernel, pid)]
    print(f"프로세스 {len(processes)}, 재려는 상황 {len(targets)}")
    if not targets:
        return 2
    rounds = Rounds()
    for pid, exe in targets:
        with rounds.round(f"{exe}:{pid}") as current:
            before = _gap(kernel, pid)
            start = time.monotonic()
            argv = pcl.command_line(pid)
            elapsed = time.monotonic() - start
            if before and _gap(kernel, pid):
                if argv is not None:
                    result = "읽음"
                else:
                    result = "즉시 None" if elapsed < 1.0 else "기다린 뒤 None"
                print(f"{exe} {pid}: {result} {elapsed:.2f}초")
                current.mark(measured=True, result=result)
    print(rounds.summary())
    return rounds.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
