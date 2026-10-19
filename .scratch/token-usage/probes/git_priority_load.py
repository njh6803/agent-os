"""CPU가 꽉 찼을 때 `main_checkout()`의 git 한 번이 프로세스 우선순위에 따라 얼마나 걸리는지 잰다.

작업 스케줄러 작업 `agent-os token_report daily`는 등록 때 우선순위를 주지 않아 기본값 `Priority`
7(BELOW_NORMAL_PRIORITY_CLASS)로 돈다. 2026-10-19 08:00 실행은 `main_checkout()`의 git이 10초를 넘겨
끝났고, 그때 다른 세션의 pre-commit(병렬 검사, 07:57~08:08)이 이 PC의 CPU를 쓰고 있었다.

갈래는 다섯이다.
- `inherit`: BELOW_NORMAL로 띄운 파이썬이 플래그 없이 띄운 손자의 우선순위 클래스. 작업 아래의
  cmd·uv·python·git이 그 우선순위를 물려받는다는 전제의 표지다. 16384(BELOW_NORMAL)가 아니면 종료
  코드 1이다.
- `idle`: 부하 없이 보통 우선순위의 git.
- `load_normal`: 보통 우선순위의 CPU 소모 프로세스를 논리 CPU 수의 두 배 띄운 채 보통 우선순위의
  git.
- `load_below`: 같은 부하에서 BELOW_NORMAL(작업 스케줄러 `Priority` 7과 같은 클래스)의 git.
- `tool`: 같은 부하에서 이 체크아웃의 `<모듈>.main_checkout()` 한 번. 자식 파이썬은 보통 우선순위로
  떠서 import까지 마친 뒤 스스로 BELOW_NORMAL로 내려가 그 함수만 잰다(BELOW_NORMAL로 띄우면 파이썬의
  시작만으로 300초를 넘겨, 함수에 닿지 못했다. 2026-10-19 첫 실행). 표지는 둘이다. 내려간 뒤의
  클래스를 stderr에 `PRIO 16384`로 찍어야 하고(없으면 측정이 아니다. 핸들 형을 주지 않은 판은
  바꾸기가 조용히 실패해 고치기 전 판도 1초 안에 지났다), 성공이면 stdout의 `OK`와 함수의 ms, 그
  함수가 띄운 git의 시간 제한에 걸리면 stderr의 `TimeoutExpired`다. 둘 다 없는 회차는 측정이 아니다.
  고치기 전 판(`git show a60e2ddd:tools/token_report.py > tools/_old_token_report.py`로 꺼내고,
  잰 뒤 지운다)과 고친 판을 같은 부하에서 견주는 갈래다.
load 갈래는 번갈아 잰다(시간에 따라 부하가 달라지는 것을 갈래에 고르게 나눈다).

표지: 부하 갈래의 회차는 그 회차가 끝난 직후 부하 프로세스가 모두 살아 있을 때만 측정으로 센다.
측정이 아닌 회차가 하나라도 있으면 종료 코드 1이다.

결과는 JSON 한 줄이다. git 갈래마다 n, 최소·중앙값·최대(ms), 10초를 넘은 회차 수. `tool` 갈래는
성공·시간 초과 수와 자식 안에서 잰 함수의 ms(시간 초과는 자식 전체의 ms). git 한 번의 제한은
60초이고, 넘으면 60000으로 센다. `tool` 자식 하나의 제한은 300초다.

쓰는 법(저장소 루트에서): `uv run --no-project python
.scratch/token-usage/probes/git_priority_load.py [회차] [모듈]` 기본 회차는 갈래마다 5, 기본 모듈은
`tools.token_report`다. 윈도에서만 돈다.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
GIT = ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"]
LIMIT = 60.0
TOOL_LIMIT = 300.0
GIT_TIMEOUT_MS = 10_000
BURN = "while True: pass"
# 핸들 형을 주지 않으면 ctypes가 64비트 의사 핸들을 32비트 정수로 잘라, 우선순위를 읽고 바꾸는
# 호출이 조용히 0(실패)을 낸다(첫 판에서 inherit가 "0"이었다).
KERNEL = (
    "import ctypes; k = ctypes.windll.kernel32; "
    "k.GetCurrentProcess.restype = ctypes.c_void_p; "
    "k.GetPriorityClass.argtypes = [ctypes.c_void_p]; "
    "k.SetPriorityClass.argtypes = [ctypes.c_void_p, ctypes.c_uint32]; "
    "h = k.GetCurrentProcess(); "
)
GRANDCHILD = KERNEL + "print(k.GetPriorityClass(h))"
BELOW = 0x4000
CHILD = (
    "import subprocess, sys; "
    f"print(subprocess.run([sys.executable, '-c', {GRANDCHILD!r}], "
    "capture_output=True, text=True).stdout.strip())"
)
TOOL = (
    "import importlib, sys, time; m = importlib.import_module(sys.argv[1]); "
    + KERNEL
    + f"k.SetPriorityClass(h, {BELOW}); "
    "print('PRIO', k.GetPriorityClass(h), file=sys.stderr, flush=True); "
    "t = time.perf_counter(); m.main_checkout(); "
    "print('OK', round((time.perf_counter() - t) * 1000))"
)


def time_git(creationflags: int) -> float:
    start = time.perf_counter()
    try:
        subprocess.run(
            GIT,
            cwd=ROOT / "tools",
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=LIMIT,
            check=True,
            creationflags=creationflags,
        )
    except subprocess.TimeoutExpired:
        return LIMIT * 1000
    return (time.perf_counter() - start) * 1000


def run_tool(module: str) -> tuple[str, float]:
    """`<module>.main_checkout()`을 따로 띄운 파이썬에서 부른다. ("ok"|"timeout"|"unknown", ms)."""
    start = time.perf_counter()
    try:
        done = subprocess.run(
            [sys.executable, "-c", TOOL, module],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=TOOL_LIMIT,
        )
    except subprocess.TimeoutExpired:
        return "unknown", TOOL_LIMIT * 1000
    if f"PRIO {BELOW}" not in done.stderr:
        return "unknown", 0.0
    if done.returncode == 0 and done.stdout.startswith("OK"):
        return "ok", float(done.stdout.split()[1])
    if "TimeoutExpired" in done.stderr:
        return "timeout", (time.perf_counter() - start) * 1000
    return "unknown", 0.0


def summary(times: list[float]) -> dict[str, float | int]:
    s = sorted(times)
    if not s:
        return {"n": 0}
    return {
        "n": len(s),
        "min_ms": round(s[0]),
        "med_ms": round(s[len(s) // 2]),
        "max_ms": round(s[-1]),
        "over_10s": sum(t > GIT_TIMEOUT_MS for t in s),
    }


def main() -> int:
    if sys.platform != "win32":
        print("윈도에서만 돈다", file=sys.stderr)
        return 2
    rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    module = sys.argv[2] if len(sys.argv) > 2 else "tools.token_report"
    normal = subprocess.NORMAL_PRIORITY_CLASS
    below = subprocess.BELOW_NORMAL_PRIORITY_CLASS

    inherit = subprocess.run(
        [sys.executable, "-c", CHILD], capture_output=True, text=True, creationflags=below
    ).stdout.strip()
    idle = [time_git(normal) for _ in range(rounds)]

    cpus = os.cpu_count() or 1
    burners = [
        subprocess.Popen([sys.executable, "-c", BURN], creationflags=normal)
        for _ in range(cpus * 2)
    ]
    load_normal: list[float] = []
    load_below: list[float] = []
    tool: list[tuple[str, float]] = []
    uncounted = 0
    try:
        time.sleep(2)
        for _ in range(rounds):
            for flags, bucket in ((normal, load_normal), (below, load_below)):
                t = time_git(flags)
                if all(b.poll() is None for b in burners):
                    bucket.append(t)
                else:
                    uncounted += 1
            outcome, ms = run_tool(module)
            if outcome != "unknown" and all(b.poll() is None for b in burners):
                tool.append((outcome, ms))
            else:
                uncounted += 1
    finally:
        for b in burners:
            b.kill()
        for b in burners:
            b.wait()

    result = {
        "cpus": cpus,
        "burners": len(burners),
        "inherit": inherit,
        "idle": summary(idle),
        "load_normal": summary(load_normal),
        "load_below": summary(load_below),
        "module": module,
        "tool": {
            "ok": sum(o == "ok" for o, _ in tool),
            "timeout": sum(o == "timeout" for o, _ in tool),
            "ms": [round(ms) for _, ms in tool],
        },
        "uncounted": uncounted,
    }
    print(json.dumps(result, ensure_ascii=False))
    expected_inherit = str(below)
    return 1 if uncounted or inherit != expected_inherit else 0


if __name__ == "__main__":
    sys.exit(main())
