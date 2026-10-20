"""손자 없는 두 러너 시험의 8초 상한이 부하에서 빨개지는지, 빨개지면 어느 몫이 늘었는지
가른다(대기열 306, ADR 0035).

대상은 `tests/tools/test_mutate.py` 의 두 시험이다. 둘 다 20초 자는 자식을 `tools/mutate.py` 의
`run_command` 로 띄우고, 시험이 부른 때부터 돌아올 때까지가 8초보다 짧은지 본다(`assert
time.monotonic() - 시작 < 8`). 8초는 러너가 자식이 끝나기를 기다리는 회귀(20초)를 가르는 상한이다.

- `test_실제_러너는_시간_제한을_실제로_넘긴_명령을_끊는다`(`timeout`): 제한 1초가 실제로 지나면
  `_kill_tree`(`taskkill /F /T`)로 끝내고 `_drain` 으로 남은 출력을 읽는다.
- `test_실제_러너는_프로세스_트리를_끝내지_못해도_자식은_끝낸다`(`no-tree`): 첫 기다림을 곧바로
  끊고, `taskkill` 을 띄우지 못하게 한 채 `_drain` 의 기다림을 1초로 줄인다.

2026-10-19 까지 이 두 단언이 빨개진 기록은 찾지 못했다(ADR 0035 의 2026-10-18 이력 "남은 것", 이
프로브를 지은 세션이 세션 기록을 그 시험 이름과 단언으로 찾았다). 이 프로브는 먼저 재현되는지 본다.

위 모양은 고치기 전 판(`5e7fa88d`)이다. 고친 판은 `timeout` 의 자식이 60초를 자고 상한이 30초다.
상한은 판마다 그 시험의 소스에서 걸린 시간 단언(`time.monotonic() - 시작 < N`)을 읽어 정하고(아래
표지의 상한 앞뒤 견주기에 쓴다), 단언이 하나가 아니면 멈춘다. `--test-file` 을 여러 번 주면 한
회차에 판마다 두 시험을 차례로 불러 같은 부하를 받게 한다. 고친 길의 표지는 둘이다. 판마다의
`passed_over_old_bound` 는 통과했지만 걸린 시간이 8초를 넘어 고치기 전 판이라면 빨갰을 회차의 수다.
두 판을 주면 `pair_red_then_passed` 는 같은 회차에 앞 판(고치기 전)의 시간 제한 시험이 빨갛고 뒤
판(고친 판)이 통과한 회차의 수다. 2026-10-19 의 첫 `after` 측정은 고친 판의 상한을
`--timeout-bound-ms 30000` 으로 받던 판으로 돌았다(소스에서 읽는 값과 같다). 그보다 앞선 `repro`
단계의 결과(`b0`, `b32`, `pytest3`, `control_*`)는 더 앞의 판으로 돌아 요약에 `bound_ms` 가 없다.

걸린 시간을 넷으로 나눈다. `tools.mutate` 의 `_kill_tree` 와 `_drain` 을 시각을 남기는 것으로
감싼다. `run_command` 는 둘을 모듈 전역으로 찾으므로 시험이 부르는 러너가 감싼 것을 거친다.

- 끊기 전(`before_kill_ms`): 시험이 불린 때부터 `_kill_tree` 가 불린 때까지. 자식을 띄우는 것과 첫
  기다림이 든다. `timeout` 은 그 기다림이 제한 1초다.
- 끝내기(`kill_ms`): `_kill_tree` 한 번. `timeout` 은 `taskkill` 과 `process.kill`, `no-tree` 는
  `process.kill` 뿐이다.
- 읽기(`drain_ms`): `_drain` 한 번. 출력 파이프가 닫히기를 기다린다.
- 그 뒤(`after_ms`): `_drain` 이 돌아온 때부터 시험이 끝날 때까지. `process.wait` 와 단언이 든다.

갈래. 빨간 회차마다 넷 가운데 가장 긴 몫으로 가른다(A 끊기 전, B 끝내기, C 읽기, D 그 뒤).
`timeout` 의 끊기 전은 제한 1초를 빼고 견준다. 양성 대조는 넷이다(`--control`).
`slow-before` 는 감싼 `_kill_tree` 가 시각을 남기기 전에, `slow-kill` 은 남긴 뒤 원래 것을 부르기
전에, `slow-drain` 은 감싼 `_drain` 이 원래 것을 부르기 전에, `slow-after` 는 원래 것이 돌아온 뒤
시각을 남기기 전에 8.5초 잔다. 대조의 회차가 모두 빨갛고 기대한 갈래여야 셈이 맞다(요약의
`control_ok`).

표지(회차가 측정인지): 부하가 회차 끝까지 살아 있었다. 감싼 `_kill_tree` 와 `_drain` 이 한 번씩
불렸다(러너가 끊는 길을 지났다). 감싼 `run_command`(시험 모듈의 이름을 바꾼다)가 돌려준
`timed_out_after` 가 그 시험의 기대(1, 60)와 같다(그래서 빨강은 시간 단언에서 난다). 시험의 결과가
잰 시간과 맞는다(시험의 `time.monotonic` 은 윈도 3.12 에서 약 16ms 해상도라 상한 앞뒤 50ms 는 따지지
않는다). 표지가 없는 회차는 따로 세고 하나라도 있으면 종료 코드가 1 이다.

부하는 같은 폴더의 `mutate_ctrl_c.py` 의 `burners` 를 그대로 쓴다(`--burners K`,
`--pytest-loads P`). `--out` 을 주면 pytest 부하 i 의 출력을 `<out 의 이름>_pytest<i>.txt` 에 남기고
실패 줄을 요약의 `pytest_load_failed` 에 싣는다.

돌리는 법: 저장소 루트에서 `PYTHONUTF8=1 uv run python <이 파일> N [--burners K] [--pytest-loads P]
[--test-file <경로>]… [--control <이름>] --out <JSON>`. 이 파일은
`.scratch/harness/probes/precommit_xdist/mutate_no_grandchild_bound.py` 다. 측정 전부는
`mutate_no_grandchild_bound_all.sh` 가 돌린다.

못 보는 것: pytest 와 xdist 가 얹는 것, 실제 pre-commit 부하의 모양, 다른 기계. 두 시험이 자식을
띄우는 venv 의 `python.exe` 는 기본 설치의 인터프리터를 다시 띄우는 실행기라, `no-tree` 에서
`process.kill` 이 실행기만 끝내면 인터프리터가 파이프를 쥐고 남을 수 있다(그러면 읽기가 1초를 쓴다.
재지 않았다).
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import re
import statistics
import sys
import tempfile
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from types import ModuleType

import pytest
from mutate_ctrl_c import ROOT, burners, failed_in, load_test_module

# `mutate_ctrl_c` 가 저장소 루트를 sys.path 에 넣은 뒤라야 찾는다. import 문은 정렬이 앞으로 옮긴다
mutate = importlib.import_module("tools.mutate")

TEST_FILE = ROOT / "tests" / "tools" / "test_mutate.py"
TESTS = {
    "timeout": ("test_실제_러너는_시간_제한을_실제로_넘긴_명령을_끊는다", 1),
    "no-tree": ("test_실제_러너는_프로세스_트리를_끝내지_못해도_자식은_끝낸다", 60),
}
BOUND_MS = 8000
EDGE_MS = 50
SLOW_SECONDS = 8.5
EXPECTED = {"slow-before": "A", "slow-kill": "B", "slow-drain": "C", "slow-after": "D"}
BRANCH_OF = {"before_kill_ms": "A", "kill_ms": "B", "drain_ms": "C", "after_ms": "D"}


@dataclass
class Marks:
    """감싼 함수가 남긴 시각(perf_counter_ns)과 러너의 결과."""

    kill: list[tuple[int, int]] = field(default_factory=list[tuple[int, int]])
    drain: list[tuple[int, int]] = field(default_factory=list[tuple[int, int]])
    timed_out_after: list[int | None] = field(default_factory=list[int | None])


@dataclass
class Version:
    """한 판의 시험 파일. 상한은 그 판의 시험 소스에서 읽는다."""

    path: Path
    module: ModuleType
    box: list[Marks]
    bounds: dict[str, float]


@dataclass
class Result:
    case: str
    outcome: str
    elapsed_ms: float
    began: int
    done: int
    marks: Marks
    version: int = 0
    round: int = 0
    reason: str | None = None


# 시험이 걸린 시간을 견주는 단언. 두 시험 모두 이 모양이 하나씩 있다
TIME_BOUND = re.compile(r"time\.monotonic\(\) - 시작 < (\d+)")


def bounds_of(module: ModuleType) -> dict[str, float]:
    bounds: dict[str, float] = {}
    for case, (name, _) in TESTS.items():
        found = TIME_BOUND.findall(inspect.getsource(getattr(module, name)))
        if len(found) != 1:
            raise SystemExit(f"{name} 의 걸린 시간 단언이 {len(found)}개다(하나여야 한다)")
        bounds[case] = float(found[0]) * 1000
    return bounds


def watch(marks: Marks, control: str) -> None:
    """`tools.mutate` 의 `_kill_tree`·`_drain` 을 감싼다. 원래 것은 처음 감쌀 때 한 번 잡는다."""
    kill_tree: Callable[..., None] = ORIGINAL["kill"]
    drain: Callable[..., str] = ORIGINAL["drain"]

    def watched_kill(process: object) -> None:
        if control == "slow-before":
            time.sleep(SLOW_SECONDS)
        start = time.perf_counter_ns()
        if control == "slow-kill":
            time.sleep(SLOW_SECONDS)
        kill_tree(process)
        marks.kill.append((start, time.perf_counter_ns()))

    def watched_drain(process: object) -> str:
        start = time.perf_counter_ns()
        if control == "slow-drain":
            time.sleep(SLOW_SECONDS)
        output = drain(process)
        if control == "slow-after":
            end = time.perf_counter_ns()
            time.sleep(SLOW_SECONDS)
        else:
            end = time.perf_counter_ns()
        marks.drain.append((start, end))
        return output

    mutate._kill_tree = watched_kill
    mutate._drain = watched_drain


ORIGINAL: dict[str, Callable[..., object]] = {"kill": mutate._kill_tree, "drain": mutate._drain}


def watch_runner(module: ModuleType, box: list[Marks]) -> None:
    """시험 모듈이 부르는 `run_command` 를 감싸 돌려준 `timed_out_after` 를 남긴다."""
    original: Callable[..., mutate.CommandResult] = module.run_command

    def wrapped(*args: object, **kw: object) -> mutate.CommandResult:
        result = original(*args, **kw)
        box[0].timed_out_after.append(result.timed_out_after)
        return result

    module.run_command = wrapped


def call_test(versions: list[Version], index: int, case: str, control: str) -> Result:
    version = versions[index]
    name = TESTS[case][0]
    test: Callable[..., None] = getattr(version.module, name)
    names = inspect.signature(test).parameters
    marks = Marks()
    version.box[0] = marks
    with (
        tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory,
        pytest.MonkeyPatch.context() as patch,
    ):
        watch(marks, control)
        given: dict[str, object] = {"tmp_path": Path(directory)}
        if "monkeypatch" in names:
            given["monkeypatch"] = patch
        began = time.perf_counter_ns()
        outcome = "passed"
        try:
            test(**given)
        except Exception as error:  # 실패의 모양을 센다
            outcome = type(error).__name__
        done = time.perf_counter_ns()
    return Result(case, outcome, (done - began) / 1e6, began, done, marks, version=index)


def spans(result: Result) -> dict[str, float] | None:
    marks = result.marks
    if len(marks.kill) != 1 or len(marks.drain) != 1:
        return None
    (kill_start, kill_end), (drain_start, drain_end) = marks.kill[0], marks.drain[0]
    return {
        "before_kill_ms": (kill_start - result.began) / 1e6,
        "kill_ms": (kill_end - kill_start) / 1e6,
        "drain_ms": (drain_end - drain_start) / 1e6,
        "after_ms": (result.done - drain_end) / 1e6,
        "between_ms": (drain_start - kill_end) / 1e6,
    }


def branch(case: str, parts: dict[str, float]) -> str:
    # `timeout` 의 끊기 전에는 제한 1초가 든다. 그 몫은 부하와 무관하게 늘 있다
    adjusted = dict(parts)
    if case == "timeout":
        adjusted["before_kill_ms"] -= TESTS[case][1] * 1000
    return BRANCH_OF[max(BRANCH_OF, key=lambda name: adjusted[name])]


def reason_for(result: Result, *, alive: bool, bound_ms: float) -> str | None:
    if not alive:
        return "부하가 회차 중에 끝났다"
    marks = result.marks
    if len(marks.kill) != 1 or len(marks.drain) != 1:
        return f"끝내기 {len(marks.kill)}번, 읽기 {len(marks.drain)}번이 불렸다"
    if marks.timed_out_after != [TESTS[result.case][1]]:
        return f"러너의 timed_out_after 가 기대와 다르다: {marks.timed_out_after}"
    if result.outcome not in ("passed", "AssertionError"):
        return f"시간 단언 밖의 실패: {result.outcome}"
    red = result.outcome != "passed"
    if red and result.elapsed_ms < bound_ms - EDGE_MS:
        return "상한 안인데 빨갰다"
    if not red and result.elapsed_ms >= bound_ms + EDGE_MS:
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


def span_tails(results: list[Result]) -> dict[str, dict[str, float]]:
    parts = [part for part in (spans(result) for result in results) if part]
    names = (*BRANCH_OF, "between_ms")
    return {name: tail([part[name] for part in parts]) for name in names}


def case_summary(measured: list[Result], case: str, bound_ms: float) -> dict[str, object]:
    red = [result for result in measured if result.outcome != "passed"]
    # 고친 길의 표지: 상한을 넓힌 판에서 옛 8초 상한이라면 빨갰을 통과 회차
    passed_over_old = [
        result
        for result in measured
        if result.outcome == "passed" and result.elapsed_ms >= BOUND_MS + EDGE_MS
    ]
    branches: dict[str, int] = {}
    for result in red:
        parts = spans(result)
        if parts:
            name = branch(case, parts)
            branches[name] = branches.get(name, 0) + 1
    return {
        "case": case,
        "test": TESTS[case][0],
        "bound_ms": bound_ms,
        "measured": len(measured),
        "red": len(red),
        "red_branches": branches,
        "elapsed_ms": tail([result.elapsed_ms for result in measured]),
        "red_elapsed_ms": sorted(round(result.elapsed_ms, 1) for result in red),
        "spans_measured": span_tails(measured),
        "spans_red": span_tails(red),
        "over_half": sum(1 for result in measured if result.elapsed_ms >= bound_ms / 2),
        "passed_over_old_bound": len(passed_over_old),
        "passed_over_old_bound_ms": sorted(
            round(result.elapsed_ms, 1) for result in passed_over_old
        ),
    }


def summarize(results: list[Result], control: str, versions: list[Version]) -> dict[str, object]:
    by_case: list[dict[str, object]] = []
    for index, version in enumerate(versions):
        for case in TESTS:
            measured = [
                result
                for result in results
                if result.version == index and result.case == case and result.reason is None
            ]
            row = case_summary(measured, case, version.bounds[case])
            by_case.append({"version": index, "test_file": str(version.path), **row})
    summary: dict[str, object] = {"by_case": by_case}
    if len(versions) == 2:
        # 두 판의 표지: 같은 회차에 앞 판(고치기 전)의 시간 제한 시험이 빨갛고 뒤 판(고친 판)이
        # 통과했다
        by_round: dict[int, dict[int, Result]] = {}
        for result in results:
            if result.case == "timeout" and result.reason is None:
                by_round.setdefault(result.round, {})[result.version] = result
        summary["pair_red_then_passed"] = sum(
            1
            for pair in by_round.values()
            if len(pair) == 2 and pair[0].outcome != "passed" and pair[1].outcome == "passed"
        )
    if control:
        measured = [result for result in results if result.reason is None]
        got = [
            branch(result.case, parts)
            for result in measured
            if (parts := spans(result)) is not None
        ]
        summary["control"] = control
        summary["control_ok"] = (
            bool(measured)
            and all(result.outcome != "passed" for result in measured)
            and got == [EXPECTED[control]] * len(measured)
        )
        summary["control_branches"] = got
    return summary


def run(
    runs: int,
    burner_count: int,
    pytest_loads: int,
    test_files: list[Path],
    control: str,
    logs: list[Path],
) -> dict[str, object]:
    versions: list[Version] = []
    for index, path in enumerate(test_files):
        module = load_test_module(path, index)
        box = [Marks()]
        watch_runner(module, box)
        versions.append(Version(path, module, box, bounds_of(module)))
    results: list[Result] = []
    rounds = 0
    seconds = 0.0
    try:
        with burners(burner_count, pytest_loads, logs) as procs:
            began = time.monotonic()
            for number in range(runs):
                row = [
                    call_test(versions, index, case, control)
                    for index in range(len(versions))
                    for case in TESTS
                ]
                alive = all(proc.poll() is None for proc in procs)
                for result in row:
                    result.round = number
                    bound = versions[result.version].bounds[result.case]
                    result.reason = reason_for(result, alive=alive, bound_ms=bound)
                results += row
                rounds += 1
                if pytest_loads and not alive:
                    break
            seconds = round(time.monotonic() - began, 1)
    finally:
        mutate._kill_tree = ORIGINAL["kill"]
        mutate._drain = ORIGINAL["drain"]
    reasons = [result.reason for result in results if result.reason is not None]
    return {
        "runs": runs,
        "rounds": rounds,
        "burners": burner_count,
        "pytest_loads": pytest_loads,
        "test_files": [str(path) for path in test_files],
        "unmeasured": len(reasons),
        "unmeasured_reasons": sorted(set(reasons)),
        "seconds": seconds,
        **summarize(results, control, versions),
        "pytest_load_failed": {path.name: failed_in(path) for path in logs[:pytest_loads]},
        "rows": [
            {
                "round": result.round,
                "version": result.version,
                "case": result.case,
                "outcome": result.outcome,
                "elapsed_ms": round(result.elapsed_ms, 1),
                "reason": result.reason,
                "spans": spans(result),
            }
            for result in results
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("runs", type=int)
    parser.add_argument("--burners", type=int, default=0)
    parser.add_argument("--pytest-loads", type=int, default=0)
    parser.add_argument("--test-file", action="append", default=[])
    parser.add_argument("--control", choices=sorted(EXPECTED), default="")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    test_files = [Path(path) for path in args.test_file] or [TEST_FILE]
    out = Path(args.out) if args.out else None
    logs = (
        [out.with_name(f"{out.stem}_pytest{index}.txt") for index in range(args.pytest_loads)]
        if out
        else []
    )
    summary = run(args.runs, args.burners, args.pytest_loads, test_files, args.control, logs)
    if out:
        out.write_text(json.dumps(summary, ensure_ascii=False) + "\n", encoding="utf-8")
    brief = {key: value for key, value in summary.items() if key != "rows"}
    print(json.dumps(brief, ensure_ascii=False), flush=True)
    if args.control and not summary.get("control_ok"):
        return 1
    return 1 if summary["unmeasured"] else 0


if __name__ == "__main__":
    sys.exit(main())
