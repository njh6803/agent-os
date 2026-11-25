"""hash_load 프로브의 스크립트가 나눠 쓰는 것. 정해진 해시 설정, 비밀번호, 메모리 읽기, CPU 고정,
셈.

해시 설정은 ADR 0062 결정 "비밀번호 저장"의 것이다(Argon2id, m=19456, t=2, p=1). 비밀번호는 같은
ADR 의 "비밀번호 규칙"(8~128자, 영문 대문자·숫자·특수문자 각 1자 이상)을 지키는 것으로 골랐다.

메모리는 리눅스에서 `/proc/self/status` 의 `VmRSS`(지금 상주)와 `VmHWM`(최고 상주), 윈도에서
`GetProcessMemoryInfo` 의 `WorkingSetSize`·`PeakWorkingSetSize` 다(선례
`../password_hash/peak_memory.py`). 잡았다가 쓰지 않은 쪽은 들지 않는다.

CPU 고정은 리눅스에서만 한다(`os.sched_setaffinity`). 프로세스에 건 고정은 뒤에 만드는 스레드가
물려받는다. 윈도에서는 고정하지 않고 빈 목록을 돌려준다.
"""

from __future__ import annotations

import math
import os
import random
import statistics
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from argon2 import PasswordHasher

MIB = 1024 * 1024
TIME_COST = 2
MEMORY_COST = 19456
PARALLELISM = 1
PASSWORD = "Probe-Pass1!"
WRONG_SAME_LENGTH = "Probe-Pass2!"
WRONG_LONG = "Wrong-Pass9!" + "w" * 116
USER = "admin"


def hasher() -> PasswordHasher:
    """정해진 설정의 해시 도구. argon2-cffi 는 여기서 가져온다. `run.py docker` 가 argon2-cffi 없는
    저장소 환경에서 이 모듈의 셈만 쓰기 때문이다."""
    from argon2 import PasswordHasher

    return PasswordHasher(time_cost=TIME_COST, memory_cost=MEMORY_COST, parallelism=PARALLELISM)


def tiny_hasher() -> PasswordHasher:
    """가져오기와 라이브러리가 처음 쓰는 몫을 바닥에 넣는 아주 작은 설정."""
    from argon2 import PasswordHasher

    return PasswordHasher(time_cost=1, memory_cost=8, parallelism=1)


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
        if not psapi.GetProcessMemoryInfo(
            kernel32.GetCurrentProcess(), ctypes.byref(counters), size
        ):
            raise OSError("GetProcessMemoryInfo 가 실패했다")
        return int(counters.WorkingSetSize), int(counters.PeakWorkingSetSize)

    def pin(cpus: Sequence[int]) -> list[int]:
        """윈도에서는 고정하지 않는다."""
        del cpus
        return []

else:

    def memory() -> tuple[int, int]:
        """(지금 상주 바이트, 최고 상주 바이트)."""
        found: dict[str, int] = {}
        for line in Path("/proc/self/status").read_text(encoding="ascii").splitlines():
            name, _, rest = line.partition(":")
            if name in ("VmRSS", "VmHWM"):
                found[name] = int(rest.split()[0]) * 1024
        return found["VmRSS"], found["VmHWM"]

    def pin(cpus: Sequence[int]) -> list[int]:
        """이 프로세스를 주어진 CPU 에 고정하고, 고정한 뒤 읽은 목록을 돌려준다."""
        if cpus:
            os.sched_setaffinity(0, set(cpus))
        return sorted(os.sched_getaffinity(0))


def parse_cpus(text: str) -> list[int]:
    """`0,1` 이나 `0-3` 꼴."""
    found: list[int] = []
    for part in text.split(","):
        if not part:
            continue
        low, _, high = part.partition("-")
        found.extend(range(int(low), int(high or low) + 1))
    return found


def quantile(values: Sequence[float], q: float) -> float:
    """선형 보간 분위수."""
    ordered = sorted(values)
    if not ordered:
        return math.nan
    position = (len(ordered) - 1) * q
    low = math.floor(position)
    high = math.ceil(position)
    return ordered[low] + (ordered[high] - ordered[low]) * (position - low)


def summary(values: Sequence[float]) -> dict[str, float | int]:
    """최소, 10 분위, 중앙, 90 분위, 최대와 수."""
    if not values:
        return {"n": 0}
    return {
        "n": len(values),
        "min": min(values),
        "p10": quantile(values, 0.10),
        "median": statistics.median(values),
        "p90": quantile(values, 0.90),
        "max": max(values),
    }


def ks_statistic(left: Sequence[float], right: Sequence[float]) -> float:
    """두 표본의 콜모고로프-스미르노프 D(누적 분포의 가장 큰 차)."""
    a, b = sorted(left), sorted(right)
    n, m = len(a), len(b)
    i = j = 0
    biggest = 0.0
    while i < n and j < m:
        point = min(a[i], b[j])
        while i < n and a[i] <= point:
            i += 1
        while j < m and b[j] <= point:
            j += 1
        biggest = max(biggest, abs(i / n - j / m))
    return biggest


def ks_p_value(statistic: float, n: int, m: int) -> float:
    """점근 근사의 p 값(Stephens 의 보정). 표본이 수십 개 이상일 때의 어림 식이다."""
    effective = math.sqrt(n * m / (n + m))
    lam = (effective + 0.12 + 0.11 / effective) * statistic
    if lam < 0.2:
        return 1.0
    total = 0.0
    for j in range(1, 101):
        total += 2 * (-1) ** (j - 1) * math.exp(-2 * j * j * lam * lam)
    return min(max(total, 0.0), 1.0)


def median_difference_interval(
    left: Sequence[float], right: Sequence[float], *, seed: int, resamples: int = 2000
) -> tuple[float, float, float]:
    """중앙값의 차(오른쪽 - 왼쪽)와 붓스트랩 95% 구간."""
    chooser = random.Random(seed)
    observed = statistics.median(right) - statistics.median(left)
    found: list[float] = []
    for _ in range(resamples):
        a = [chooser.choice(left) for _ in left]
        b = [chooser.choice(right) for _ in right]
        found.append(statistics.median(b) - statistics.median(a))
    return observed, quantile(found, 0.025), quantile(found, 0.975)


def median_interval(
    values: Sequence[float], *, seed: int, resamples: int = 2000
) -> tuple[float, float, float]:
    """한 표본의 중앙값과 붓스트랩 95% 구간. 짝지은 차의 중앙값에 쓴다."""
    chooser = random.Random(seed)
    observed = statistics.median(values)
    found = [statistics.median([chooser.choice(values) for _ in values]) for _ in range(resamples)]
    return observed, quantile(found, 0.025), quantile(found, 0.975)


def signed_rank(differences: Sequence[float]) -> tuple[float, float]:
    """윌콕슨 부호 순위 검정의 (z, 양쪽 p). 짝지은 차가 0 을 가운데로 고르게 퍼졌다는 가설을
    본다.

    0 인 차는 빼고, 크기가 같은 차는 평균 순위를 주며, 분산에서 같은 크기의 몫을 덜어 낸 정규
    근사다. 짝이 수십 개 이상일 때의 어림 식이다."""
    nonzero = [value for value in differences if value != 0]
    n = len(nonzero)
    if n == 0:
        return 0.0, 1.0
    order = sorted(range(n), key=lambda index: abs(nonzero[index]))
    ranks = [0.0] * n
    ties = 0.0
    start = 0
    while start < n:
        end = start
        while end + 1 < n and abs(nonzero[order[end + 1]]) == abs(nonzero[order[start]]):
            end += 1
        for position in range(start, end + 1):
            ranks[order[position]] = (start + end) / 2 + 1
        size = end - start + 1
        ties += size**3 - size
        start = end + 1
    plus = sum(rank for rank, value in zip(ranks, nonzero, strict=True) if value > 0)
    mean = n * (n + 1) / 4
    variance = n * (n + 1) * (2 * n + 1) / 24 - ties / 48
    if variance <= 0:
        return 0.0, 1.0
    z = (plus - mean) / math.sqrt(variance)
    return z, math.erfc(abs(z) / math.sqrt(2))
