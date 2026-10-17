"""다른 프로세스가 교체하는 동안의 읽기 시험이 부하에서 왜 빨개지는지 가른다(ADR 0035).

대상은 `tests/adapters/test_filesystem.py` 의
`test_다른_프로세스가_교체하는_동안의_읽기가_재시도_안에서_성공한다` 다. 2026-10-17 pre-commit 의
pytest (xdist 8개)에서 두 세션에 한 번씩 빨갰다(일지 2026-10-17-02, 2026-10-17-03). 모양이 남은 것은
03 의 한 번이고, 읽기가 재시도 창(`_RETRY_DELAYS`, 합 31ms)을 다 쓰고도 `PermissionError` 를 받아
`PluginError` 로 끝났다. 02 에는 시험 이름과 수만 남았다.

모드 둘이다.

- `test`: 시험 함수를 그대로 N 번 부른다(재현 빈도). 시험 모듈을 경로로 불러 함수만 부르므로 pytest
  의 수집과 픽스처는 빠지고, 루트는 회차마다 새 임시 폴더다. `--test-file` 을 여러 번 주면 그
  파일들을 회차마다 번갈아 불러 같은 부하를 받게 한다. 고치기 전 판은
  `git show aa93cf7b:tests/adapters/test_filesystem.py` 를 저장소 밖의 `.py` 파일로 옮겨 준다.
  시험의 `_plugins` 를 감싸 `read_disabled` 의 `PluginError` 마다 걸린 시간과 까닭의 종류를 남긴다.
  상한(31ms) 을 다 쓰고 까닭이 `PermissionError` 인 것(잠김)이 고친 판이 넘기는 것이라, 고친 판의
  통과 가운데 그것이 있었던 회차가 넘김이 실제로 쓰였다는 표지다. 고치기 전 판에서는 그것이 곧
  빨강이다.
- `trace`: 같은 장면을 계측해 N 번 돌린다. 다른 프로세스가 실제 어댑터로 calc 를 켜고 끄는 동안
  이쪽이 실제 어댑터로 쉬지 않고 읽는다. 읽는 쪽은 `Path.read_text` 를 감싸 운영자 파일을 연
  시도마다 시작·끝과 결과를, 쓰는 쪽은 `os.replace` 를 감싸 교체 시도마다 시작·끝과 결과를
  `time.perf_counter_ns()` 로 남긴다. 이 PC(파이썬 3.12, 윈도)에서 `perf_counter` 는
  QueryPerformanceCounter 이고 `time.time` 과 `monotonic` 은 15.6ms 해상도라 쓰지
  않는다(`time.get_clock_info` 를 손으로 봤다). 두 프로세스의 값이 한 축인지는 회차마다 대 본다(아래
  표지).

`trace` 의 `--priority above|high` 는 쓰는 쪽 프로세스를 그 우선순위 등급으로 띄운다. 교체가 길어진
까닭이 쓰는 쪽이 CPU 를 기다린 것이면 등급을 올렸을 때 교체가 짧아지고, 쓰는 쪽 밖(백신 검사 등)에서
기다린 것이면 그대로다. 다만 등급마다 따로 띄운 실행을 차례로 견주므로, 그사이 이 프로브 밖의
부하(다른 세션)가 바뀌면 이 비교는 그 둘을 가르지 못한다.

부하는 둘이다. `--burners K` 는 쉬지 않고 도는 파이썬 프로세스 K 개를 먼저 띄우고 끝에 죽인다. 이
PC 는 논리 CPU 16개다. `--pytest-loads P`(`test` 모드만)는 이 저장소의 전체 pytest 를 xdist 8개로
나눠 도는 것 P 벌을 띄우고, 그것이 하나라도 끝나면 회차를 멈춘다. 세션 둘이 같은 시각에 커밋하는
부하(ADR 0035 의 두 벌 동시)에 가깝지만 web verify 등 다른 검사의 몫은 빠진다.

해석의 갈래. 읽기 한 번(`read_disabled` 한 번)이 `PermissionError` 를 연달아 받은 구간을 막힘이라
한다.

- A. 쥔 쪽이 늘어났다: 막힘과 겹치는 교체 시도가 하나다. 그 교체 하나가 막힘 내내 파일을 쥐었다.
- B. 교체가 잦았다: 막힘과 겹치는 교체 시도가 둘 이상이다. 시도마다 다른 교체에 걸렸다.
- C. 제3자: 막힘과 겹치는 교체 시도가 없다. 이 두 프로세스 밖의 무엇(백신 검사 등)이 쥐었다.

양성 대조는 부하가 없는 회차다. 그때의 짧은 막힘이 교체 하나와 겹치면(A) 막힘이 교체 호출 안에서
난다는 계측의 전제가 선다. 교체가 막힘을 연다는 해석은 어림이고(교체의 이름 바꾸기가 끝나고 핸들을
닫기 전까지 그 핸들이 삭제 권한을 쥐어, 삭제 공유 없이 여는 읽기가 공유 위반을 받는다는 윈도의 일반
동작), 이 프로브가 재는 것은 겹침뿐이다.

표지(회차가 측정인지): 부하 프로세스가 회차가 끝날 때까지 살아 있었다, 자식의 `started` 시각이
부모가 띄운 시각과 그 줄을 받은 시각 사이에 있다(한 축), `trace` 는 막힘이 하나 이상 있었고(재시도가
실제로 돌았다) 쓰는 쪽이 제때 끝나며 기록 파일을 남겼다(`toggler_ok`). 쓰는 쪽이 첫 줄을
`FIRST_LINE_SECONDS` 안에 내지 않거나 교체를 마친 뒤 `TOGGLE_GRACE_SECONDS` 안에 끝나지 않으면 그
회차를 끊는다. 자식이 멈추거나 기록 없이 죽어도 프로브가 끝없이 기다리거나 앞서 모은 회차를 잃지
않게 하려는 것이다(PR #288 의 CodeRabbit 지적. 그 전의 판으로 돈 아래 결과에서는 이 갈래가 나지
않았다). 표지가 없는 회차는 따로 세고, 하나라도 있으면 종료 코드가 1 이다. `--pytest-loads` 는
pytest 가 끝나는 회차가 늘 하나 있어 1 로 끝난다. `test` 의 실패는 예외의 종류와 마지막 줄을 남긴다.
재려는 실패의 모양은 `PluginError` 이고 마지막 줄이 `disabled.toml` 의 `[Errno 13]` 이다. 어설션의
빨강은 메시지가 없어, 빨개진 줄의 코드와 읽기가 본 상태(`seen`, 꺼진 이름의 목록들)를 남긴다. 시험
파일마다 위 잠김이 있었던 회차 수와, 그 가운데 통과한 회차 수를 따로 센다.

돌리는 법: 저장소 루트에서 `uv run python <이 파일> <test|trace> N [--burners K]`. 이 파일은
`.scratch/harness/probes/precommit_xdist/filesystem_read_retry.py` 다. 전체 결과 JSON 은 `--out` 에
쓰고, 표준 출력에는 회차별 행을 뺀 요약 한 줄을 낸다. 요약의 `seconds` 는 부하를 띄운 뒤 회차를 다
돌기까지 걸린 초다.

못 보는 것: pytest 와 xdist 가 얹는 것, 실제 pre-commit 부하의 모양, 다른 기계.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib.util
import json
import os
import queue
import statistics
import subprocess
import sys
import tempfile
import threading
import time
import traceback
from collections.abc import Callable, Iterator
from pathlib import Path
from types import ModuleType

import pytest

from agent_os.adapters.filesystem import FilesystemPlugins
from agent_os.core.ports import PluginError, PluginKey

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TEST_FILE = ROOT / "tests" / "adapters" / "test_filesystem.py"
TEST_NAME = "test_다른_프로세스가_교체하는_동안의_읽기가_재시도_안에서_성공한다"
DISABLED = "disabled.toml"
# 재시도의 설계 상한(1·2·4·8·16ms 의 합). 시험의 `RETRY_CAP_SECONDS` 와 같은 값이다.
RETRY_WINDOW_NS = 31_000_000
CAP_SECONDS = RETRY_WINDOW_NS / 1_000_000_000
TOGGLE_SECONDS = 0.3
# `trace` 가 쓰는 쪽을 기다리는 상한. 첫 줄까지, 그리고 교체 시간(TOGGLE_SECONDS) 뒤 끝나기까지다.
FIRST_LINE_SECONDS = 30.0
TOGGLE_GRACE_SECONDS = 30.0

BURNER = "while True:\n    pass\n"
# 쓰는 쪽 프로세스의 우선순위 등급(윈도). 다른 OS 에는 이 상수가 없어 모두 0 이다.
PRIORITY = {
    "normal": 0,
    "above": getattr(subprocess, "ABOVE_NORMAL_PRIORITY_CLASS", 0),
    "high": getattr(subprocess, "HIGH_PRIORITY_CLASS", 0),
}

# 시험의 TOGGLER 와 같은 일을 하되 교체 시도마다 시작·끝·결과를 남긴다. 첫 줄은 started 와 그
# 시각이다.
TRACED_TOGGLER = """
import json, os, sys, time
from pathlib import Path
from agent_os.adapters.filesystem import FilesystemPlugins
from agent_os.core.ports import PluginError
from agent_os.sdk import PluginKind, PluginName
records = []
original = os.replace
def traced(src, dst):
    t0 = time.perf_counter_ns()
    try:
        original(src, dst)
    except OSError as error:
        records.append((t0, time.perf_counter_ns(), type(error).__name__))
        raise
    records.append((t0, time.perf_counter_ns(), "ok"))
os.replace = traced
plugins = FilesystemPlugins(Path(sys.argv[1]))
deadline = time.monotonic() + float(sys.argv[2])
print("started", time.perf_counter_ns(), flush=True)
enabled = True
capped = 0
while time.monotonic() < deadline:
    try:
        plugins.write_enabled(PluginKind.AGENT, PluginName("calc"), enabled=enabled)
    except PluginError:
        capped += 1
    enabled = not enabled
Path(sys.argv[3]).write_text(json.dumps({"capped": capped, "replaces": records}), encoding="utf-8")
print(capped, flush=True)
"""


def kill_tree(proc: subprocess.Popen[bytes] | subprocess.Popen[str]) -> None:
    """프로세스와 그 자식을 끝낸다. `pytest -n` 의 일꾼은 자식이라 `kill` 만으로는 남는다."""
    if proc.poll() is not None:
        return
    if sys.platform == "win32":
        subprocess.run(
            ["taskkill", "/T", "/F", "/PID", str(proc.pid)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    else:
        proc.kill()
    proc.wait(timeout=30)


@contextlib.contextmanager
def burners(count: int, pytest_loads: int = 0) -> Iterator[list[subprocess.Popen[bytes]]]:
    """부하 프로세스를 띄운다. 쉬지 않고 도는 파이썬 count 개와, 이 저장소의 전체 pytest 를 xdist
    8개로 나눠 도는 것 pytest_loads 벌이다. 뒤의 것은 스스로 끝나므로 그 뒤의 회차는 부하가 없다."""
    procs = [
        subprocess.Popen([sys.executable, "-c", BURNER], stdout=subprocess.DEVNULL)
        for _ in range(count)
    ]
    procs += [
        subprocess.Popen(
            [sys.executable, "-m", "pytest", "-q", "-n", "8", "-p", "no:cacheprovider"],
            cwd=ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        for _ in range(pytest_loads)
    ]
    try:
        # pytest 는 수집과 일꾼을 띄우는 데 시간이 든다. 그 전의 회차는 부하가 덜하다(어림).
        time.sleep(20.0 if pytest_loads else 1.0 if count else 0.0)
        yield procs
    finally:
        for proc in procs:
            kill_tree(proc)


def all_alive(procs: list[subprocess.Popen[bytes]]) -> bool:
    return all(proc.poll() is None for proc in procs)


def load_test_module(test_file: Path, index: int = 0) -> ModuleType:
    spec = importlib.util.spec_from_file_location(f"probe_test_filesystem_{index}", test_file)
    if spec is None or spec.loader is None:
        raise SystemExit(f"시험 모듈을 불러오지 못했다: {test_file}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def watch_seen(module: ModuleType, box: list[set[frozenset[object]]]) -> None:
    """시험의 읽기 함수가 돌려준 상태 집합을 box 에 남긴다. 판에 따라 이름이 `_read_while` 이거나
    `_read_while_past_cap` 이다. 메시지 없는 어설션의 빨강이 무엇을 봤는지 보려는 것이다."""
    for name in ("_read_while", "_read_while_past_cap"):
        original: Callable[..., set[frozenset[object]]] | None = getattr(module, name, None)
        if original is None:
            continue

        def wrapped(
            *args: object, _original: Callable[..., set[frozenset[object]]] = original
        ) -> set[frozenset[object]]:
            seen = _original(*args)
            box.append(seen)
            return seen

        setattr(module, name, wrapped)


class CountingPlugins:
    """`read_disabled` 의 PluginError 를 걸린 초와 까닭의 종류로 record 에 남기고 그대로 던진다."""

    def __init__(self, inner: FilesystemPlugins, record: list[tuple[float, str]]) -> None:
        self._inner = inner
        self._record = record

    def read_disabled(self) -> frozenset[PluginKey]:
        started = time.perf_counter()
        try:
            return self._inner.read_disabled()
        except PluginError as error:
            spent = time.perf_counter() - started
            self._record.append((spent, type(error.__cause__).__name__))
            raise


def count_failures(module: ModuleType, record: list[tuple[float, str]]) -> None:
    """시험의 `_plugins` 가 돌려주는 소스를 `CountingPlugins` 로 감싼다. 교체 중 읽기 시험이 그
    소스에서 부르는 것은 `read_disabled` 뿐이다."""
    original: Callable[[Path], FilesystemPlugins] = module._plugins

    def wrapped(root: Path) -> CountingPlugins:
        return CountingPlugins(original(root), record)

    module._plugins = wrapped


def locked_past_cap(record: list[tuple[float, str]]) -> int:
    """상한을 다 쓰고 까닭이 PermissionError 인 PluginError 의 수. 고친 판이 넘기는 것이다."""
    return sum(1 for spent, cause in record if cause == "PermissionError" and spent >= CAP_SECONDS)


def describe_seen(seen: set[frozenset[object]]) -> list[list[str]]:
    """상태 집합을 꺼진 이름의 목록들로 적는다. `[[], ["calc"]]` 가 시험이 기대하는 둘이다."""
    return sorted(sorted(str(getattr(key, "name", key)) for key in state) for state in seen)


def run_test_mode(
    runs: int, burner_count: int, pytest_loads: int, test_files: list[Path]
) -> dict[str, object]:
    """시험 파일 여럿을 번갈아 불러 같은 부하를 받게 한다. 회차 i 는 파일 i % len 이다."""
    box: list[set[frozenset[object]]] = []
    record: list[tuple[float, str]] = []
    modules = [load_test_module(path, index) for index, path in enumerate(test_files)]
    for module in modules:
        watch_seen(module, box)
        count_failures(module, record)
    tests: list[Callable[[Path], None]] = [getattr(module, TEST_NAME) for module in modules]
    outcomes: list[list[str]] = [[] for _ in test_files]
    errors: list[list[str]] = [[] for _ in test_files]
    # 회차마다 (통과했나, 상한을 다 쓴 잠김의 수, 그 밖의 PluginError 수). 측정인 회차만 든다.
    locks: list[list[tuple[bool, int, int]]] = [[] for _ in test_files]
    unmeasured = 0
    with burners(burner_count, pytest_loads) as procs:
        began = time.monotonic()
        for index in range(runs):
            which = index % len(tests)
            box.clear()
            record.clear()
            with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
                try:
                    tests[which](Path(directory))
                    outcome = "passed"
                except Exception as error:  # 실패의 모양을 센다
                    outcome = type(error).__name__
                    lines = str(error).splitlines()
                    detail = lines[-1][:200] if lines else "(메시지 없음)"
                    if isinstance(error, AssertionError):
                        # 시험의 어설션은 둘이다. 빨개진 줄의 코드로 가른다.
                        frame = traceback.extract_tb(error.__traceback__)[-1]
                        detail = f"{detail} at={frame.line!r}"
                        if box:
                            detail = f"{detail} seen={describe_seen(box[-1])}"
                    errors[which].append(detail)
            if not all_alive(procs):
                unmeasured += 1
                outcome = "unmeasured"
            else:
                locked = locked_past_cap(record)
                locks[which].append((outcome == "passed", locked, len(record) - locked))
            outcomes[which].append(outcome)
            if pytest_loads and not all_alive(procs):
                break
        seconds = round(time.monotonic() - began, 1)
    by_file = [
        {
            "test_file": str(path),
            "counts": {name: got.count(name) for name in sorted(set(got))},
            "runs_with_locked_past_cap": sum(1 for _, locked, _ in rows if locked),
            "passed_with_locked_past_cap": sum(
                1 for passed, locked, _ in rows if passed and locked
            ),
            "locked_past_cap": sum(locked for _, locked, _ in rows),
            "other_plugin_errors": sum(other for *_, other in rows),
            "errors": errs[:10],
        }
        for path, got, errs, rows in zip(test_files, outcomes, errors, locks, strict=True)
    ]
    return {
        "mode": "test",
        "runs": runs,
        "burners": burner_count,
        "pytest_loads": pytest_loads,
        "unmeasured": unmeasured,
        "seconds": seconds,
        "by_file": by_file,
    }


def trace_once(module: ModuleType, root: Path, priority: str) -> dict[str, object]:
    """한 회차. 읽기 시도와 교체 시도의 기록을 돌려준다. priority 는 쓰는 쪽 프로세스의 등급이다."""
    module._write_agent(root, "calc")
    module._operator_file(root, module.CALC_DISABLED)
    reads: list[tuple[int, int, int, str]] = []
    call = 0
    original = Path.read_text

    def traced(self: Path, encoding: str | None = None, errors: str | None = None) -> str:
        if self.name != DISABLED:
            return original(self, encoding, errors)
        t0 = time.perf_counter_ns()
        try:
            text = original(self, encoding, errors)
        except OSError as error:
            reads.append((call, t0, time.perf_counter_ns(), type(error).__name__))
            raise
        reads.append((call, t0, time.perf_counter_ns(), "ok"))
        return text

    record_file = root.parent / f"{root.name}.replaces.json"
    before = time.perf_counter_ns()
    toggler = subprocess.Popen(
        [sys.executable, "-c", TRACED_TOGGLER, str(root), str(TOGGLE_SECONDS), str(record_file)],
        stdout=subprocess.PIPE,
        text=True,
        creationflags=PRIORITY[priority],
    )
    line = first_line(toggler, FIRST_LINE_SECONDS)
    after = time.perf_counter_ns()
    first = (line or "").split()
    started = int(first[1]) if len(first) == 2 and first[0] == "started" else -1
    one_axis = before <= started <= after
    in_time = line is not None
    deadline = time.monotonic() + TOGGLE_SECONDS + TOGGLE_GRACE_SECONDS
    plugins = FilesystemPlugins(root)
    failed_calls: list[int] = []
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(Path, "read_text", traced)
        while in_time:
            call += 1
            try:
                plugins.read_disabled()
            except PluginError:
                failed_calls.append(call)
            if toggler.poll() is not None:
                break
            if time.monotonic() > deadline:
                in_time = False
    kill_tree(toggler)
    try:
        toggled = json.loads(record_file.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        toggled = None
    finally:
        record_file.unlink(missing_ok=True)
    return {
        "one_axis": one_axis,
        "toggler_ok": in_time and toggled is not None,
        "calls": call,
        "failed_calls": failed_calls,
        "reads": reads,
        "replaces": toggled["replaces"] if toggled is not None else [],
        "capped": toggled["capped"] if toggled is not None else None,
    }


def first_line(proc: subprocess.Popen[str], seconds: float) -> str | None:
    """proc 의 첫 줄을 seconds 안에 받는다. 넘기면 None 이다. 막히는 `readline` 은 루프의 시간으로
    끊지 못해 읽는 스레드에 맡긴다. 그 스레드는 daemon 이라 proc 를 끝내 파이프가 닫히면 함께
    끝나고, 그러지 못해도 파이썬의 끝을 막지 않는다(`.claude/rules/probes.md`)."""
    stream = proc.stdout
    if stream is None:
        return None
    box: queue.Queue[str] = queue.Queue()
    threading.Thread(target=lambda: box.put(stream.readline()), daemon=True).start()
    try:
        return box.get(timeout=seconds)
    except queue.Empty:
        return None


def streaks(reads: list[tuple[int, int, int, str]]) -> list[tuple[int, int, int, int]]:
    """읽기 한 번 안에서 PermissionError 가 이어진 구간. (call, 시작, 끝, 시도 수)."""
    found: list[tuple[int, int, int, int]] = []
    by_call: dict[int, list[tuple[int, int, str]]] = {}
    for call, t0, t1, outcome in reads:
        by_call.setdefault(call, []).append((t0, t1, outcome))
    for call, attempts in by_call.items():
        refused = [(t0, t1) for t0, t1, outcome in attempts if outcome == "PermissionError"]
        if refused:
            found.append((call, refused[0][0], refused[-1][1], len(refused)))
    return found


def classify(start: int, end: int, replaces: list[list[object]]) -> tuple[str, int, str, bool]:
    """막힘과 겹치는 교체 시도의 수로 갈래를 고른다. 겹친 교체 가운데 가장 긴 것의 ns 와 결과,
    그 교체가 막힘을 처음부터 끝까지 품는지도 돌려준다."""
    overlapping = [
        (int(str(r0)), int(str(r1)), str(outcome))
        for r0, r1, outcome in replaces
        if int(str(r0)) <= end and int(str(r1)) >= start
    ]
    if not overlapping:
        return "C", 0, "", False
    r0, r1, outcome = max(overlapping, key=lambda row: row[1] - row[0])
    branch = "A" if len(overlapping) == 1 else "B"
    return branch, r1 - r0, outcome, r0 <= start and end <= r1


def ms(ns: float) -> float:
    return round(ns / 1_000_000, 3)


def run_trace_mode(runs: int, burner_count: int, priority: str) -> dict[str, object]:
    rows: list[dict[str, object]] = []
    unmeasured = 0
    all_streak_ms: list[float] = []
    all_replace_ms: list[float] = []
    by_branch: dict[str, int] = {"A": 0, "B": 0, "C": 0}
    long_streaks: list[dict[str, object]] = []
    failed_reads = 0
    total_calls = 0
    module = load_test_module(TEST_FILE)
    with burners(burner_count) as procs:
        for index in range(runs):
            with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory:
                root = Path(directory) / "root"
                root.mkdir()
                result = trace_once(module, root, priority)
            reads = result["reads"]
            replaces = result["replaces"]
            assert isinstance(reads, list) and isinstance(replaces, list)
            found = streaks(reads)
            alive = all_alive(procs)
            measured = (
                bool(result["one_axis"]) and bool(result["toggler_ok"]) and alive and bool(found)
            )
            failed = result["failed_calls"]
            assert isinstance(failed, list)
            if not measured:
                unmeasured += 1
                reason = {
                    "one_axis": result["one_axis"],
                    "toggler_ok": result["toggler_ok"],
                    "burners_alive": alive,
                    "replaces_ok": sum(1 for *_, outcome in replaces if outcome == "ok"),
                    "capped": result["capped"],
                }
                rows.append({"run": index, "measured": False, "streaks": len(found), **reason})
                continue
            calls = result["calls"]
            assert isinstance(calls, int)
            total_calls += calls
            failed_reads += len(failed)
            all_replace_ms.extend(
                ms(int(str(r1)) - int(str(r0))) for r0, r1, outcome in replaces if outcome == "ok"
            )
            for call, start, end, attempts in found:
                branch, longest, outcome, contained = classify(start, end, replaces)
                by_branch[branch] += 1
                span = ms(end - start)
                all_streak_ms.append(span)
                if end - start >= RETRY_WINDOW_NS or call in failed:
                    long_streaks.append(
                        {
                            "run": index,
                            "call": call,
                            "failed": call in failed,
                            "attempts": attempts,
                            "streak_ms": span,
                            "branch": branch,
                            "longest_overlapping_replace_ms": ms(longest),
                            "longest_outcome": outcome,
                            "contained": contained,
                        }
                    )
            rows.append(
                {
                    "run": index,
                    "measured": True,
                    "calls": calls,
                    "failed": len(failed),
                    "streaks": len(found),
                    "replaces_ok": sum(1 for *_, outcome in replaces if outcome == "ok"),
                    "capped": result["capped"],
                }
            )

    def tail(values: list[float]) -> dict[str, float]:
        if not values:
            return {}
        ordered = sorted(values)
        return {
            "n": len(ordered),
            "median": round(statistics.median(ordered), 3),
            "p99": ordered[min(len(ordered) - 1, int(len(ordered) * 0.99))],
            "max": ordered[-1],
            "over_31ms": sum(1 for value in ordered if value >= 31),
        }

    return {
        "mode": "trace",
        "runs": runs,
        "burners": burner_count,
        "priority": priority,
        "unmeasured": unmeasured,
        "read_calls": total_calls,
        "failed_reads": failed_reads,
        "streak_ms": tail(all_streak_ms),
        "replace_ok_ms": tail(all_replace_ms),
        "branches": by_branch,
        "long_or_failed_streaks": long_streaks,
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("test", "trace"))
    parser.add_argument("runs", type=int)
    parser.add_argument("--burners", type=int, default=0)
    parser.add_argument("--test-file", action="append", help="test 모드가 번갈아 부를 시험 파일")
    parser.add_argument("--pytest-loads", type=int, default=0)
    parser.add_argument("--priority", choices=tuple(PRIORITY), default="normal")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    if args.mode == "test":
        files = [Path(name) for name in args.test_file or [str(TEST_FILE)]]
        summary = run_test_mode(args.runs, args.burners, args.pytest_loads, files)
    else:
        summary = run_trace_mode(args.runs, args.burners, args.priority)
    text = json.dumps(summary, ensure_ascii=False)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    brief = {key: value for key, value in summary.items() if key != "rows"}
    print(json.dumps(brief, ensure_ascii=False), flush=True)
    return 1 if summary["unmeasured"] else 0


if __name__ == "__main__":
    os.environ.setdefault("PYTHONUTF8", "1")
    sys.exit(main())
