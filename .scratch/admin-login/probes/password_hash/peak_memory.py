"""프로세스가 해시 한 번에 상주 메모리를 얼마나 더 쓰는지 재서 `RESULT <json>` 한 줄로 낸다.

프로세스 하나에 줄 하나다(`--key "<후보> <줄>"`). 가져오기와 아주 작은 매개변수의 해시 한 번을
먼저 끝내 라이브러리가 처음 쓰는 몫을 바닥에 넣는다. 그 뒤 바닥(지금 상주 `rss_before`, 최고 상주
`peak_before`)을 읽고, 그 줄의 매개변수로 해시 한 번과 견줌 두 번(맞는 비밀번호, 틀린 비밀번호)을
차례로 한 뒤 최고 상주(`peak_after`)를 다시 읽는다. 셋은 겹치지 않으므로 최고 상주는 한 번의 몫이다.
더 쓴 양은 `peak_after - peak_before`(아래 끝)와 `peak_after - rss_before`(위 끝) 사이다. 바닥을
읽기 전에 최고 상주가 지금 상주보다 높았으면 그 차이만큼 아래 끝이 낮게 나온다.

`--key control` 은 양성 대조다. 64 MiB 바이트열을 잡아 쪽(4096 바이트)마다 한 바이트를 쓴다. 이
읽기가 쓴 메모리를 본다면 두 끝이 64 MiB 를 사이에 둔다. 잡기만 하고 쓰지 않은 쪽은 상주에 들지
않으므로 쓰는 것까지가 대조다.

읽는 값. 리눅스는 `/proc/self/status` 의 `VmRSS`·`VmHWM`, 윈도는 `GetProcessMemoryInfo` 의
`WorkingSetSize`·`PeakWorkingSetSize` 다. 다른 프로세스와 나눠 쓰는 쪽도 여기 든다. 해시가 잡았다가
쓰지 않은 쪽이 있으면 여기 들지 않는다.
"""

from __future__ import annotations

import argparse
import gc
import json
import sys
from pathlib import Path

import store_argon2
import store_scrypt
from argon2 import PasswordHasher
from rows import MIB, PASSWORD, bind, find
from store_scrypt import ScryptParams

CONTROL_BYTES = 64 * MIB
PAGE = 4096

if sys.platform == "win32":
    import ctypes
    from ctypes import wintypes

    class _Counters(ctypes.Structure):
        _fields_ = (
            ("cb", wintypes.DWORD),
            ("PageFaultCount", wintypes.DWORD),
            ("PeakWorkingSetSize", ctypes.c_size_t),
            ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
            ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t),
            ("PeakPagefileUsage", ctypes.c_size_t),
        )

    def memory() -> tuple[int, int]:
        """(지금 상주 바이트, 최고 상주 바이트)."""
        kernel32 = ctypes.WinDLL("kernel32")
        psapi = ctypes.WinDLL("psapi")
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        psapi.GetProcessMemoryInfo.argtypes = (
            wintypes.HANDLE,
            ctypes.POINTER(_Counters),
            wintypes.DWORD,
        )
        counters = _Counters()
        size = ctypes.sizeof(_Counters)
        handle = kernel32.GetCurrentProcess()
        if not psapi.GetProcessMemoryInfo(handle, ctypes.byref(counters), size):
            raise OSError("GetProcessMemoryInfo 가 실패했다")
        return int(counters.WorkingSetSize), int(counters.PeakWorkingSetSize)

else:

    def memory() -> tuple[int, int]:
        """(지금 상주 바이트, 최고 상주 바이트)."""
        found: dict[str, int] = {}
        for line in Path("/proc/self/status").read_text(encoding="ascii").splitlines():
            name, _, rest = line.partition(":")
            if name in ("VmRSS", "VmHWM"):
                found[name] = int(rest.split()[0]) * 1024
        return found["VmRSS"], found["VmHWM"]


def warm_up() -> None:
    store_scrypt.hash_password(PASSWORD, ScryptParams(log_n=1, r=8, p=1))
    store_argon2.hash_password(PASSWORD, PasswordHasher(time_cost=1, memory_cost=8, parallelism=1))
    gc.collect()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--key", required=True)
    args = parser.parse_args()
    key: str = args.key
    warm_up()
    result: dict[str, object] = {"kind": "memory", "key": key, "platform": sys.platform}
    if key == "control":
        rss_before, peak_before = memory()
        buffer = bytearray(CONTROL_BYTES)
        for offset in range(0, CONTROL_BYTES, PAGE):
            buffer[offset] = 1
        _, peak_after = memory()
        result["genuine"] = sum(buffer[::PAGE]) == CONTROL_BYTES // PAGE
        result["nominal_bytes"] = CONTROL_BYTES
    else:
        bound = bind(find(key))
        rss_before, peak_before = memory()
        _, genuine = bound.round_trip()
        _, peak_after = memory()
        result["genuine"] = genuine
        result["nominal_bytes"] = bound.row.nominal_bytes
    result.update(rss_before=rss_before, peak_before=peak_before, peak_after=peak_after)
    print(f"RESULT {json.dumps(result, ensure_ascii=False)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
