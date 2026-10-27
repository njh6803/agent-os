"""midturn 훅의 "파일이 없으면 기다리지 않는다" 시험이 부하에서 왜 빨개지는지 가른다(대기열 306,
ADR 0035).

대상은 `tests/tools/test_hook_midturn_korean.py` 의
`test_트랜스크립트_파일이_없으면_기다리지_않는다` 다. 고치기 전 판(`5e7fa88d`)은
훅(`tools/hook_midturn_korean.py`)을 자식으로 띄우고(`_run_hook`), 시험이 시작한 때부터 자식이
돌아올 때까지가 `WAIT_SECONDS`(2초)보다 짧은지 본다. 훅의 `main` 은 트랜스크립트 파일이 없으면
기다리지 않고 곧바로 돌아온다. 그 단언이 pre-commit 과 부하 pytest 에서 2.1~4.17초로 여러 번
빨갰다(대기열 306 행).

걸린 시간을 넷으로 나눈다. 시험 모듈의 `subprocess` 를 감싼 것으로 바꿔, `_run_hook` 이 부르는
`subprocess.run` 이 같은 명령을 `-c` 머리말(`PRELUDE`) 뒤에 돌리게 한다. 머리말은 자기가 시작한 때를
남기고 `runpy` 로 훅을 `__main__` 으로 돌린 뒤, 훅이 돌아온 때와 `time.sleep` 을 부른 횟수를 기록
파일에 남긴다. 시계는 모두 `perf_counter_ns` 다(윈도에서 QueryPerformanceCounter 라 프로세스 사이에
견줄 수 있다).

- 띄우기(`spawn_ms`): 감싼 `run` 이 불린 때부터 머리말이 시작한 때까지. venv 의 `python.exe` 는 기본
  설치의 인터프리터를 다시 띄우는 실행기라(`sys._base_executable` 이 다르다) 프로세스가 둘 뜬다. 두
  프로세스의 생성 시각(`GetProcessTimes`)을 `GetSystemTimePreciseAsFileTime` 과 맞대 같은 시계로
  옮겨, 실행기가 생기기까지(`before_launcher_ms`), 실행기가 인터프리터를 띄우기까지(`launcher_ms`),
  인터프리터가 머리말에 닿기까지(`interpreter_ms`)도 낸다.
- 본문(`body_ms`): 머리말이 시작한 때부터 훅이 돌아온 때까지. 훅 모듈을 불러오는 것이 든다.
- 닫기(`exit_ms`): 훅이 돌아온 때부터 감싼 `run` 의 `communicate` 가 돌아온 때까지. 머리말이 기록을
  쓰는 것, 인터프리터의 마무리와 실행기의 끝, 부모가 파이프의 끝을 읽는 것이 든다.
- 부모(`parent_ms`): 시험이 불린 때부터 감싼 `run` 이 불린 때까지와, `communicate` 가 돌아온 때부터
  시험이 끝날 때까지의 합.

갈래. 빨간 회차마다 넷 가운데 가장 긴 몫으로 가른다. A 띄우기, A' 닫기(둘 다 자식 프로세스를 띄우고
닫는 비용이고 훅은 기다리지 않았다), B 본문(훅이 기다렸거나 훅 모듈을 불러오는 것이 늦었다. 앞의
것은 `sleeps` 가 0 이 아니다), C 부모(시험 프로세스 쪽이 늦었다). 양성 대조는 넷이다(`--control`).
`waits` 는 파일이 없을 때 돌아오는 두 줄(`GUARD`)을 지운 훅 사본을 띄워 B 를, `slow-start` 는
머리말이 시작을 남기기 전에 자서 A 를, `slow-exit` 은 훅이 돌아온 뒤 자서 A' 를, `slow-parent` 는
감싼 `run` 이 `communicate` 뒤 자서 C 를 낸다. 대조의 회차가 모두 빨갛고 기대한 갈래여야 셈이
맞다(요약의 `control_ok`).

고친 판(저장소의 시험)은 훅의 `main` 을 이 프로세스에서 불러 `time.sleep` 을 부르지 않는지 본다.
자식을 띄우지 않아 감싼 `run` 이 불리지 않는다. 그 시험이 받는 `capsys` 는 표준 출력을 모으는
대역(`Capsys`)으로 준다. `--test-file` 을 여러 번 주면 한 회차에 그 파일들을
차례로 불러 같은 부하를 받게 한다. 고친 길을 지났다는 표지는 같은 회차의 고치기 전 판이 빨갛고 고친
판이 통과한 회차다(`pair_red_then_passed`). 고친 판은 기다리지 않으므로 그 회차가 고치기 전 판이
빨개진 부하를 고친 판이 지난 회차다.

표지(회차가 측정인지): 부하가 회차 끝까지 살아 있었다. 고치기 전 판이면 감싼 `run` 이 한 번 불렸고,
머리말이 기록 파일을 썼으며(훅까지 돌았다), 훅의 종료 코드가 0 이고 출력이 비었고, 시험의 결과가 잰
시간과 맞는다(빨강이 시간 단언에서 났다. 시험의 `time.monotonic` 은 윈도 3.12 에서 약 16ms 해상도라
상한 앞뒤 50ms 는 따지지 않는다). 고친 판이면 감싼 `run` 이 불리지 않았다. 표지가 없는 회차는 따로
세고 하나라도 있으면 종료 코드가 1 이다.

부하는 같은 폴더의 `mutate_ctrl_c.py` 의 `burners` 를 그대로 쓴다(`--burners K`,
`--pytest-loads P`). `--out` 을 주면 pytest 부하 i 의 출력을 `<out 의 이름>_pytest<i>.txt` 에
남기고, 그 부하도 대상 시험을 한 번 돌므로 실패 줄을 요약의 `pytest_load_failed` 에 싣는다.

돌리는 법: 저장소 루트에서 `PYTHONUTF8=1 uv run python <이 파일> N [--burners K] [--pytest-loads P]
[--test-file <경로>]… [--control <이름>] --out <JSON>`. 이 파일은
`.scratch/harness/probes/precommit_xdist/midturn_missing_transcript.py` 다. 표준 출력에는 회차별
행을 뺀 요약 한 줄을 낸다. 측정 전부는 `midturn_missing_transcript_all.sh` 가 돌린다.

못 보는 것: pytest 와 xdist 가 얹는 것(수집, 어설션 고쳐 쓰기, 픽스처), 실제 pre-commit 부하의 모양,
다른 기계. 머리말은 `-c` 와 `runpy` 를 더해 띄우기와 본문에 그 몫이 들고, 기록을 쓰는 몫(ctypes 를
불러온다)이 닫기에 든다(재지 않았다). 훅이 `python <경로>` 로 뜰 때와 `sys.path[0]` 이 다르다(훅은
표준 라이브러리만 부른다). 프로세스 생성 시각의 해상도는 재지 않았다.
"""

from __future__ import annotations

import argparse
import contextlib
import ctypes
import inspect
import io
import json
import os
import statistics
import subprocess
import sys
import tempfile
import time
import types
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType

import pytest
from mutate_ctrl_c import ROOT, burners, failed_in, load_test_module

TEST_FILE = ROOT / "tests" / "tools" / "test_hook_midturn_korean.py"
HOOK = ROOT / "tools" / "hook_midturn_korean.py"
TEST_NAME = "test_트랜스크립트_파일이_없으면_기다리지_않는다"
BOUND_MS = 2000  # 고치기 전 시험의 상한(`WAIT_SECONDS`)
EDGE_MS = 50  # 시험의 시계와 이 프로브의 시계가 갈릴 수 있는 폭
SLOW_SECONDS = 2.5  # 양성 대조가 한 몫에 더하는 시간
OUT_ENV = "PROBE_MIDTURN_OUT"
CONTROL_ENV = "PROBE_MIDTURN_CONTROL"
EXPECTED = {"waits": "B", "slow-start": "A", "slow-exit": "A'", "slow-parent": "C"}
# 파일이 없을 때 돌아오는 두 줄. `waits` 대조가 지운다
GUARD = "    if not transcript.is_file():\n        return 0\n"

# 자식의 머리말. 기록 파일에 머리말이 시작한 때, 훅이 돌아온 때, sleep 횟수, 종료 코드, 이
# 인터프리터의 생성 시각을 남긴다. 표준 출력에는 아무것도 내지 않는다(시험이 출력을 본다)
PRELUDE = f"""
import os, sys, time
_control = os.environ.get("{CONTROL_ENV}", "")
if _control == "slow-start":
    time.sleep({SLOW_SECONDS})
_ready = time.perf_counter_ns()
_real_sleep = time.sleep
_sleeps = []
def _counted(seconds):
    _sleeps.append(seconds)
    _real_sleep(seconds)
time.sleep = _counted
import runpy
_code = 0
try:
    runpy.run_path(sys.argv[1], run_name="__main__")
except SystemExit as _exit:
    _code = _exit.code if isinstance(_exit.code, int) else (0 if _exit.code is None else 1)
_returned = time.perf_counter_ns()
time.sleep = _real_sleep
if _control == "slow-exit":
    time.sleep({SLOW_SECONDS})
import ctypes, json
_ft = ctypes.c_ulonglong
_kernel = ctypes.WinDLL("kernel32")
_kernel.GetCurrentProcess.restype = ctypes.c_void_p
_kernel.GetProcessTimes.argtypes = [ctypes.c_void_p] + [ctypes.POINTER(_ft)] * 4
_created, _exited, _kt, _ut, _now = _ft(), _ft(), _ft(), _ft(), _ft()
_ok = _kernel.GetProcessTimes(
    _kernel.GetCurrentProcess(),
    ctypes.byref(_created), ctypes.byref(_exited), ctypes.byref(_kt), ctypes.byref(_ut),
)
_before = time.perf_counter_ns()
_kernel.GetSystemTimePreciseAsFileTime(ctypes.byref(_now))
_after = time.perf_counter_ns()
_pair = [_now.value, (_before + _after) // 2]
with open(os.environ["{OUT_ENV}"], "w", encoding="utf-8") as _out:
    json.dump(
        {{
            "ready": _ready,
            "returned": _returned,
            "sleeps": len(_sleeps),
            "code": _code,
            "created_filetime": _created.value if _ok else None,
            "pair": _pair,
        }},
        _out,
    )
sys.exit(_code)
"""

_FILETIME = ctypes.c_ulonglong


def _kernel() -> ctypes.WinDLL:
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.GetProcessTimes.argtypes = [ctypes.c_void_p] + [ctypes.POINTER(_FILETIME)] * 4
    kernel.GetSystemTimePreciseAsFileTime.argtypes = [ctypes.POINTER(_FILETIME)]
    return kernel


KERNEL = _kernel()


def clock_pair() -> tuple[int, int]:
    """같은 순간의 (FILETIME 100ns 단위, perf_counter_ns). 앞뒤 perf 의 가운데를 쓴다."""
    now = _FILETIME()
    before = time.perf_counter_ns()
    KERNEL.GetSystemTimePreciseAsFileTime(ctypes.byref(now))
    after = time.perf_counter_ns()
    return now.value, (before + after) // 2


def to_perf(filetime: int, pair: tuple[int, int] | list[int]) -> int:
    return pair[1] - (pair[0] - filetime) * 100


def created_and_exited(handle: int) -> tuple[int, int] | None:
    """프로세스의 생성 시각과 끝난 시각(FILETIME). 읽지 못하면 `None`."""
    created, exited, kernel_time, user_time = _FILETIME(), _FILETIME(), _FILETIME(), _FILETIME()
    ok = KERNEL.GetProcessTimes(
        ctypes.c_void_p(handle),
        ctypes.byref(created),
        ctypes.byref(exited),
        ctypes.byref(kernel_time),
        ctypes.byref(user_time),
    )
    return (created.value, exited.value) if ok else None


@dataclass
class Call:
    """감싼 `run` 한 번. 시각은 모두 perf_counter_ns 다."""

    called: int
    returned: int | None = None
    finished: int | None = None
    launcher_created: int | None = None
    launcher_exited: int | None = None
    child: dict[str, object] | None = None
    stdout: bytes = b""
    returncode: int | None = None


@dataclass
class Result:
    file: int
    outcome: str
    elapsed_ms: float
    calls: list[Call] = field(default_factory=list[Call])
    began: int = 0
    done: int = 0
    reason: str | None = None


def wrapped_run(
    calls: list[Call], control: str, record: Path
) -> Callable[..., subprocess.CompletedProcess[bytes]]:
    def run(
        args: list[str],
        *,
        input: bytes | None = None,
        capture_output: bool = False,
        env: Mapping[str, str] | None = None,
        check: bool = False,
        timeout: float | None = None,
    ) -> subprocess.CompletedProcess[bytes]:
        call = Call(time.perf_counter_ns())
        calls.append(call)
        record.unlink(missing_ok=True)
        child_env = {**(env if env is not None else os.environ), OUT_ENV: str(record)}
        child_env[CONTROL_ENV] = control
        pipe = subprocess.PIPE if capture_output else None
        proc = subprocess.Popen(
            [args[0], "-c", PRELUDE, *args[1:]],
            stdin=subprocess.PIPE,
            stdout=pipe,
            stderr=pipe,
            env=child_env,
        )
        try:
            out, err = proc.communicate(input, timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.communicate()
            raise
        call.returned = time.perf_counter_ns()
        pair = clock_pair()
        # 윈도 Popen 의 프로세스 핸들. 끝난 뒤에도 Popen 이 닫기 전까지 쓸 수 있다
        times = created_and_exited(int(proc._handle))
        if times:
            call.launcher_created = to_perf(times[0], pair)
            call.launcher_exited = to_perf(times[1], pair)
        with_record(call, record)
        call.stdout = out or b""
        call.returncode = proc.returncode
        if control == "slow-parent":
            time.sleep(SLOW_SECONDS)
        call.finished = time.perf_counter_ns()
        if check and proc.returncode:
            raise subprocess.CalledProcessError(proc.returncode, args, out, err)
        return subprocess.CompletedProcess(args, proc.returncode, out, err)

    return run


def with_record(call: Call, record: Path) -> None:
    try:
        loaded: object = json.loads(record.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return
    if isinstance(loaded, dict):
        call.child = {str(key): value for key, value in loaded.items()}


def guardless_hook(directory: Path) -> Path:
    """`GUARD` 를 지운 훅 사본. 지울 줄이 하나가 아니면 멈춘다."""
    source = HOOK.read_text(encoding="utf-8")
    if source.count(GUARD) != 1:
        raise SystemExit(f"훅에서 지울 두 줄을 하나로 찾지 못했다: {source.count(GUARD)}")
    copy = directory / "hook_midturn_korean_guardless.py"
    copy.write_text(source.replace(GUARD, ""), encoding="utf-8")
    return copy


def prepare(module: ModuleType, calls: list[Call], control: str, record: Path, hook: Path) -> None:
    """시험 모듈이 띄울 훅과 `subprocess.run` 을 바꾼다. 저장소 밖의 사본은 훅 경로를 제 자리에서
    세어 없는 경로를 가리킨다."""
    module.HOOK = hook
    proxy = types.ModuleType("subprocess_probe")
    proxy.__dict__.update(vars(subprocess))
    proxy.run = wrapped_run(calls, control, record)
    module.subprocess = proxy


class Capsys:
    """pytest 밖에서 고친 판의 시험이 받는 `capsys` 대역. 그 시험이 부르는 `readouterr().out` 만
    둔다."""

    def __init__(self, sink: io.StringIO) -> None:
        self.sink = sink

    def readouterr(self) -> types.SimpleNamespace:
        out = self.sink.getvalue()
        self.sink.seek(0)
        self.sink.truncate()
        return types.SimpleNamespace(out=out, err="")


def call_test(module: ModuleType, which: int, calls: list[Call]) -> Result:
    test: Callable[..., None] = getattr(module, TEST_NAME)
    names = inspect.signature(test).parameters
    calls.clear()
    sink = io.StringIO()
    with (
        tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory,
        pytest.MonkeyPatch.context() as patch,
        contextlib.redirect_stdout(sink),
    ):
        given: dict[str, object] = {}
        if "tmp_path" in names:
            given["tmp_path"] = Path(directory)
        if "monkeypatch" in names:
            given["monkeypatch"] = patch
        if "capsys" in names:
            given["capsys"] = Capsys(sink)
        began = time.perf_counter_ns()
        outcome = "passed"
        try:
            test(**given)
        except Exception as error:  # 실패의 모양을 센다
            outcome = type(error).__name__
        done = time.perf_counter_ns()
    return Result(which, outcome, (done - began) / 1e6, list(calls), began, done)


def spans(result: Result) -> dict[str, float] | None:
    """고치기 전 판 회차의 몫(ms). 기록이 모자라면 `None`."""
    if len(result.calls) != 1:
        return None
    call = result.calls[0]
    child = call.child
    if child is None or call.returned is None:
        return None
    ready, returned = child.get("ready"), child.get("returned")
    if not isinstance(ready, int) or not isinstance(returned, int):
        return None
    out = {
        "spawn_ms": (ready - call.called) / 1e6,
        "body_ms": (returned - ready) / 1e6,
        "exit_ms": (call.returned - returned) / 1e6,
        "parent_ms": ((call.called - result.began) + (result.done - call.returned)) / 1e6,
    }
    created, pair = child.get("created_filetime"), child.get("pair")
    if call.launcher_created is not None and isinstance(created, int) and isinstance(pair, list):
        interpreter_created = to_perf(created, [int(value) for value in pair])
        out["before_launcher_ms"] = (call.launcher_created - call.called) / 1e6
        out["launcher_ms"] = (interpreter_created - call.launcher_created) / 1e6
        out["interpreter_ms"] = (ready - interpreter_created) / 1e6
    if call.launcher_exited is not None:
        out["after_launcher_exit_ms"] = (call.returned - call.launcher_exited) / 1e6
    return out


BRANCH_OF = {"spawn_ms": "A", "exit_ms": "A'", "body_ms": "B", "parent_ms": "C"}


def branch(parts: Mapping[str, float]) -> str:
    return BRANCH_OF[max(BRANCH_OF, key=lambda name: parts[name])]


def reason_for(result: Result, *, fixed: bool, alive: bool) -> str | None:
    if not alive:
        return "부하가 회차 중에 끝났다"
    if fixed:
        return "고친 판이 자식을 띄웠다" if result.calls else None
    if len(result.calls) != 1:
        return f"감싼 run 이 {len(result.calls)}번 불렸다"
    call = result.calls[0]
    if call.child is None:
        return "머리말이 기록을 쓰지 않았다"
    if call.returncode != 0 or call.child.get("code") != 0:
        return f"훅의 종료 코드가 0 이 아니다: {call.returncode}"
    if call.stdout.strip():
        return "훅의 출력이 비지 않았다"
    if spans(result) is None:
        return "몫을 셀 기록이 모자란다"
    if result.outcome not in ("passed", "AssertionError"):
        return f"시간 단언 밖의 실패: {result.outcome}"
    red = result.outcome != "passed"
    if red and result.elapsed_ms < BOUND_MS - EDGE_MS:
        return "상한 안인데 빨갰다"
    if not red and result.elapsed_ms >= BOUND_MS + EDGE_MS:
        return "상한을 넘었는데 통과했다"
    return None


def tail(values: list[float]) -> dict[str, float]:
    if not values:
        return {}
    ordered = sorted(values)
    return {
        "n": len(ordered),
        "median": round(statistics.median(ordered), 1),
        "p95": round(ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))], 1),
        "max": round(ordered[-1], 1),
    }


SPAN_NAMES = (
    "spawn_ms",
    "body_ms",
    "exit_ms",
    "parent_ms",
    "before_launcher_ms",
    "launcher_ms",
    "interpreter_ms",
    "after_launcher_exit_ms",
)


def span_tails(results: list[Result]) -> dict[str, dict[str, float]]:
    parts = [part for part in (spans(result) for result in results) if part]
    return {name: tail([part[name] for part in parts if name in part]) for name in SPAN_NAMES}


def summarize(
    rows: list[list[Result]], files: list[Path], fixed: list[bool], control: str
) -> dict[str, object]:
    by_file: list[dict[str, object]] = []
    for which, path in enumerate(files):
        measured = [row[which] for row in rows if row[which].reason is None]
        red = [result for result in measured if result.outcome != "passed"]
        entry: dict[str, object] = {
            "test_file": str(path),
            "fixed": fixed[which],
            "measured": len(measured),
            "red": len(red),
            "elapsed_ms": tail([result.elapsed_ms for result in measured]),
            "red_elapsed_ms": sorted(round(result.elapsed_ms, 1) for result in red),
        }
        if not fixed[which]:
            branches: dict[str, int] = {}
            for result in red:
                parts = spans(result)
                if parts:
                    name = branch(parts)
                    branches[name] = branches.get(name, 0) + 1
            entry["red_branches"] = branches
            entry["sleeps_nonzero"] = sum(
                1
                for result in measured
                if result.calls and (result.calls[0].child or {}).get("sleeps") not in (0, None)
            )
            entry["spans_measured"] = span_tails(measured)
            entry["spans_red"] = span_tails(red)
            # 시간이 상한의 절반을 넘은 회차의 몫. 빨강이 드문 부하에서 같은 쪽으로 기우는지 본다
            entry["spans_over_half"] = span_tails(
                [result for result in measured if result.elapsed_ms >= BOUND_MS / 2]
            )
        by_file.append(entry)
    summary: dict[str, object] = {"by_file": by_file}
    if len(files) > 1 and not fixed[0] and any(fixed[1:]):
        summary["pair_red_then_passed"] = sum(
            1
            for row in rows
            if row[0].reason is None
            and row[0].outcome != "passed"
            and all(result.reason is None and result.outcome == "passed" for result in row[1:])
        )
    if control:
        measured = [row[0] for row in rows if row[0].reason is None]
        got = [branch(parts) for parts in (spans(result) for result in measured) if parts]
        summary["control"] = control
        summary["control_ok"] = (
            bool(measured)
            and all(result.outcome != "passed" for result in measured)
            and got == [EXPECTED[control]] * len(measured)
        )
        summary["control_branches"] = got
    return summary


def row_json(result: Result) -> dict[str, object]:
    call = result.calls[0] if result.calls else None
    return {
        "file": result.file,
        "outcome": result.outcome,
        "elapsed_ms": round(result.elapsed_ms, 1),
        "reason": result.reason,
        "spans": spans(result),
        "sleeps": (call.child or {}).get("sleeps") if call else None,
    }


def run(
    runs: int,
    burner_count: int,
    pytest_loads: int,
    files: list[Path],
    control: str,
    logs: list[Path],
) -> dict[str, object]:
    modules = [load_test_module(path, index) for index, path in enumerate(files)]
    calls: list[list[Call]] = [[] for _ in modules]
    # 고친 판은 대상 시험이 `monkeypatch` 를 받는다(훅의 `main` 을 이 프로세스에서 부른다)
    fixed = [
        "monkeypatch" in inspect.signature(getattr(module, TEST_NAME)).parameters
        for module in modules
    ]
    rows: list[list[Result]] = []
    seconds = 0.0
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as scratch:
        hook = guardless_hook(Path(scratch)) if control == "waits" else HOOK
        for index, module in enumerate(modules):
            prepare(module, calls[index], control, Path(scratch) / f"record{index}.json", hook)
        with burners(burner_count, pytest_loads, logs) as procs:
            began = time.monotonic()
            for _ in range(runs):
                row = [
                    call_test(module, which, calls[which]) for which, module in enumerate(modules)
                ]
                alive = all(proc.poll() is None for proc in procs)
                for result in row:
                    result.reason = reason_for(result, fixed=fixed[result.file], alive=alive)
                rows.append(row)
                if pytest_loads and not alive:
                    break
            seconds = round(time.monotonic() - began, 1)
    reasons = [result.reason for row in rows for result in row if result.reason is not None]
    return {
        "runs": runs,
        "rounds": len(rows),
        "burners": burner_count,
        "pytest_loads": pytest_loads,
        "unmeasured": len(reasons),
        "unmeasured_reasons": sorted(set(reasons)),
        "seconds": seconds,
        **summarize(rows, files, fixed, control),
        "pytest_load_failed": {path.name: failed_in(path) for path in logs[:pytest_loads]},
        "rows": [[row_json(result) for result in row] for row in rows],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("runs", type=int)
    parser.add_argument("--burners", type=int, default=0)
    parser.add_argument("--pytest-loads", type=int, default=0)
    parser.add_argument("--test-file", action="append", help="한 회차에 차례로 부를 시험 파일")
    parser.add_argument("--control", choices=sorted(EXPECTED), default="")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    files = [Path(name) for name in args.test_file or [str(TEST_FILE)]]
    if args.control and len(files) != 1:
        raise SystemExit("--control 은 시험 파일 하나와 쓴다")
    out = Path(args.out) if args.out else None
    logs = (
        [out.with_name(f"{out.stem}_pytest{index}.txt") for index in range(args.pytest_loads)]
        if out
        else []
    )
    summary = run(args.runs, args.burners, args.pytest_loads, files, args.control, logs)
    if out:
        out.write_text(json.dumps(summary, ensure_ascii=False) + "\n", encoding="utf-8")
    brief = {key: value for key, value in summary.items() if key != "rows"}
    print(json.dumps(brief, ensure_ascii=False), flush=True)
    if args.control and not summary.get("control_ok"):
        return 1
    return 1 if summary["unmeasured"] else 0


if __name__ == "__main__":
    sys.exit(main())
