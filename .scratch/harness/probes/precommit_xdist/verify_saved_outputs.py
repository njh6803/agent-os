"""`results/` 에 저장한 원본 출력이 재려던 상황의 표지를 갖췄는지 보고 ADR 이 드는 수를 찍는다(ADR
0035).

프로브(`pytest_run.py`, `rounds.py`, `pair.py`, `time_web_steps.py`, `skip_under_xdist.py`)는 실행
중에 표지를 단언하고 그 결과를 출력에 남긴다. 이 스크립트는 저장한 출력을 다시 읽어 표지가 모두
있는지, 한 바퀴의 `Passed` 줄 수가 맞는지, 두 벌이 겹쳐 돌았는지를 대 본다. 프로브가 다시 낸 pytest
회차는 깨끗한지(종료 코드 0, skip·error 0)도 대 본다. ADR 이 그 회차를 통과로 들기 때문이다. 손으로
돌린 출력(한 프로세스, xdist 8개, 인터뷰 중 앞 판의 실패 둘)과 CI 의 잡 목록은 그 출력의 집계 줄과
시각만 본다. 표지가 하나라도 빠졌거나 깨끗하지 않은 회차가 있으면 종료 코드를 1 로 낸다. 걸린 시간은
대 보지 않고 그대로 찍는다.

돌리는 법: `uv run python .scratch/harness/probes/precommit_xdist/verify_saved_outputs.py`.
통과한 사례 수 3156 은 손으로 돌린 두 출력을 잰 때(`feb64be1`)의 것이다. 그 뒤 main(`c689c9ce`)은
`pytest_collect.txt` 의 3254개로 늘었다. 프로브가 다시 낸 출력의 수는 `c689c9ce` 의 것이다.

못 보는 것: 저장한 출력이 실제로 그 명령에서 나왔는지(손으로 옮긴 파일인지). 출력 안의 숫자가
맞는지.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path

from time_web_steps import STEPS

RESULTS = Path(__file__).resolve().parent / "results"
HAND_SERIAL = ("^3156 passed, 7 deselected", "slowest 40 durations")
HAND_XDIST8 = ("^bringing up nodes", "^3156 passed")
COLLECTED = r"^3254/3261 tests collected \(7 deselected\)"
FILESYSTEM = "tests/adapters/test_filesystem.py::test_다른_스레드가_운영자_파일을_연_채여도_교체가"
MUTATE = "tests/tools/test_mutate.py::test_못_보는_것_뒤의_시험이_걸려도_첫_실패에서_멈춰_빨강이다"
# 인터뷰 중 스크래치 스크립트의 앞 판으로 돌린 출력(3156개, `feb64be1`).
# 실패한 사례의 이름과 단언이 표지다.
HAND_AUTO_ROUND = (
    rf"^FAILED {re.escape(FILESYSTEM)}",
    rf"^FAILED {re.escape(MUTATE)}",
    r"^2 failed, 3154 passed",
    r"^한 바퀴 [\d.]+초 \(pytest -n auto\), 종료 코드 1$",
)
HAND_PAIR_B = (
    rf"^FAILED {re.escape(MUTATE)}",
    r"^1 failed, 3155 passed",
    r"assert \([\d.]+ - [\d.]+\) < 20",
)
# 러너가 검사마다 찍는 `<id>....Passed (<초>s)` 줄의 수. 검사 여덟, web 을 쪼갠 회차는 열셋이다.
ROUNDS = {
    "round_xdist4": 8,
    "round_xdist6": 8,
    "round_xdist8": 8,
    "round_xdist12": 8,
    "round_xdistauto": 8,
    "round_split8": 13,
}


def read(name: str) -> str:
    return (RESULTS / name).read_text(encoding="utf-8")


def json_lines(name: str) -> list[dict[str, object]]:
    return [json.loads(line) for line in read(name).splitlines() if line.strip()]


def check_patterns(name: str, patterns: tuple[str, ...]) -> list[str]:
    text = read(name)
    return [p for p in patterns if re.search(p, text, re.MULTILINE) is None]


def summary_counts(text: str) -> dict[str, int]:
    """pytest 의 마지막 집계 줄에서 failed, skipped, error 의 수를 읽는다(없는 말은 0)."""
    lines = [line for line in text.splitlines() if re.search(r"\d+ passed.* in [\d.]+s", line)]
    counts = {"failed": 0, "skipped": 0, "error": 0}
    if lines:
        for number, word in re.findall(r"(\d+) (failed|skipped|errors?)", lines[-1]):
            counts[word.removesuffix("s")] = int(number)
    return counts


def check_pytest_row(name: str) -> tuple[list[str], str]:
    """한 회차의 껍질 행과 원본 출력을 대 본다. 깨끗함(종료 코드 0, skip·error 0)도 본다."""
    row = json.loads(read(f"{name}.json"))
    counts = summary_counts(read(name))
    missing = list(row["missing"])
    if row["returncode"] != 0 or any(counts.values()):
        missing.append(f"깨끗하지 않다: 종료 코드 {row['returncode']}, {counts}")
    note = (
        f"{row['seconds']}초, 통과 {row['passed']}, 실패 {counts['failed']}, "
        f"skip {counts['skipped']}, error {counts['error']}, 종료 코드 {row['returncode']}, "
        f"프로세스 {row['workers']}"
    )
    return missing, note


def check_round(label: str, passed_lines: int) -> tuple[list[str], str]:
    tail = rf"^한 바퀴 [\d.]+초 \({label}\), pytest 통과 \d+ 실패 \d+, 종료 코드 0$"
    missing = check_patterns(f"{label}.txt", (tail,))
    found = len(re.findall(r"^[\w:-]+\.+Passed \(", read(f"{label}.txt"), re.MULTILINE))
    if found != passed_lines:
        missing.append(f"Passed 줄 {passed_lines}개 (실제 {found})")
    row_missing, row_note = check_pytest_row(f"{label}_pytest.txt")
    last = [line for line in read(f"{label}.txt").splitlines() if line.startswith("한 바퀴")]
    return missing + row_missing, f"{last[-1] if last else '한 바퀴 줄 없음'} / pytest {row_note}"


def check_pair() -> tuple[list[str], str]:
    rows = json_lines("pair.txt")
    runs = [row for row in rows if "run" in row]
    missing = [] if len(runs) == 2 else ["두 벌의 줄"]
    overlap = [row for row in rows if "겹쳐 돌았다" in row]
    if not overlap or overlap[-1]["겹쳐 돌았다"] is not True:
        missing.append("겹쳐 돌았다")
    parts = []
    for run in runs:
        missing += [f"{run['run']}: {m}" for m in run["missing"]]
        text = read(f"pair_{run['run']}_pytest.txt")
        failed = summary_counts(text)["failed"]
        parts.append(f"{run['run']} {run['pytest_start_s']}~{run['end_s']}초 실패 {failed}")
    # 프로브가 낸 판정을 저장한 시각으로 다시 센다. 두 시작이 모두 두 끝보다 앞서야 겹친 것이다.
    if len(runs) == 2 and max(r["pytest_start_s"] for r in runs) >= min(r["end_s"] for r in runs):
        missing.append("저장한 시각으로 다시 세니 겹치지 않았다")
    # ADR 이 두 벌 동시의 실패로 드는 사례다. 두 벌이 모두 통과한 출력으로 바뀌면 ADR 도 고친다.
    mutate = rf"^FAILED {re.escape(MUTATE)}"
    texts = [read(f"pair_{name}_pytest.txt") for name in ("a", "b")]
    if not any(re.search(mutate, text, re.MULTILINE) for text in texts):
        missing.append("ADR 이 드는 test_mutate 의 실패가 두 벌 어디에도 없다")
    return missing, ", ".join(parts)


def check_web_steps() -> tuple[list[str], str]:
    rows = {row["step"]: row for row in json_lines("web_steps.jsonl") if "returncode" in row}
    missing = [f"단계 {s}" for s in STEPS if s not in rows]
    for step, row in rows.items():
        if row["returncode"] != 0 or row["marked"] is not True:
            missing.append(f"{step}: 종료 코드 {row['returncode']}, 표지 {row['marked']}")
    total = sum(float(row["seconds"]) for row in rows.values())
    return missing, f"단계 합 {total:.1f}초"


def check_skip() -> tuple[list[str], str]:
    rows = {row["run"]: row for row in json_lines("skip_under_xdist.txt")}
    missing = [f"회차 {n}" for n in ("serial", "xdist2", "xdist_auto") if n not in rows]
    parts = []
    for name, row in rows.items():
        missing += [f"{name}: {m}" for m in row["missing"]]
        parts.append(f"{name} {row['seconds']}초")
    auto = rows.get("xdist_auto", {})
    parts.append(f"자동 프로세스 {auto.get('workers')} (cpu_count {auto.get('cpu_count')})")
    return missing, ", ".join(parts)


def check_ci() -> tuple[list[str], str]:
    jobs = json.loads(read("ci_run_38856631253_jobs.json"))["jobs"]
    python = [job for job in jobs if job["name"] == "python"]
    if len(python) != 1:
        return ["python 잡 하나"], ""
    # ci.yml 의 이 단계가 `uv run pytest -q` 를 부른다. 단계 이름이 그 첫 줄(ulimit)이다.
    steps = [s for s in python[0]["steps"] if "ulimit -c unlimited" in s["name"]]
    if len(steps) != 1:
        return ["pytest 단계(ulimit 줄) 하나"], ""
    first, last = steps[0]["startedAt"], steps[0]["completedAt"]
    seconds = (datetime.fromisoformat(last) - datetime.fromisoformat(first)).total_seconds()
    return [], f"pytest 단계 {seconds:.0f}초"


def main() -> int:
    results: dict[str, tuple[list[str], str]] = {
        "pytest_serial.txt (손)": (check_patterns("pytest_serial.txt", HAND_SERIAL), ""),
        "pytest_xdist8.txt (손)": (check_patterns("pytest_xdist8.txt", HAND_XDIST8), ""),
        "pytest_collect.txt (손)": (check_patterns("pytest_collect.txt", (COLLECTED,)), ""),
        "hand_auto_round.txt (손)": (check_patterns("hand_auto_round.txt", HAND_AUTO_ROUND), ""),
        "hand_pair_b.txt (손)": (check_patterns("hand_pair_b.txt", HAND_PAIR_B), ""),
        "alone_xdist8": check_pytest_row("alone_xdist8_pytest.txt"),
        "pair": check_pair(),
        "web_steps": check_web_steps(),
        "skip_under_xdist": check_skip(),
        "ci_run_38856631253": check_ci(),
    }
    for label, passed_lines in ROUNDS.items():
        results[label] = check_round(label, passed_lines)
    bad = False
    for name, (missing, note) in results.items():
        bad = bad or bool(missing)
        print(f"{name}: " + (f"표지 없음 {missing}" if missing else f"표지 있음. {note}"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
