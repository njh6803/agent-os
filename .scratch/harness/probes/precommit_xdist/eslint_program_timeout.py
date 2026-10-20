"""`web/eslint.config.test.ts` 에서 TypeScript 프로그램을 처음 세우는 시험이 부하에서 60초 제한을
넘기는지, 넘기면 멈춘 것인지 늦게 끝난 것인지 가른다(대기열 306, ADR 0035).

대상은 그 파일에서 기록에 빨갛게 남은 시험 셋이다.

- `next-react`: "실제 관리 화면 자리"의 "app/ 이 next 와 react 를 import 하는 것은 아무것도 보고되지
  않는다". 공유 판정자의 `lintText` 가 관리 화면 앱의 실제 파일 자리를 처음 린트해, 그 앱의 tsconfig
  로 프로그램을 세운다. 2026-10-17 에 144초로 빨갰다(일지 2026-10-17-04).
- `cli-two`, `cli-lone`: "끄기 주석"의 두 시험. verify 의 린트 명령을 `spawnSync` 로 새로 띄워 그
  프로세스가 프로그램을 다시 세운다. 2026-10-19 에 67초와 110초로 빨갰다(일지 2026-10-19-24).

`spawnSync` 와 프로그램을 세우는 동기 작업은 이벤트 루프를 막는다. 그동안 vitest 의 제한 타이머는
돌지 못하고, 막힘이 풀린 뒤에 늦게 불린다. 그래서 기록의 67·110·144초는 끊긴 시간이 아니라 실제로
끝난 시간으로 본다(어림. 이 프로브의 `observe` 판이 잰다).

판은 둘이다(`--mode`).

- `before`: 저장소의 설정 그대로(제한 60초) 돌린다. 빨강이 나는지와 그 시간을 본다.
- `observe`: `--testTimeout` 으로 제한을 600초로 늘려 돌린다. 제한이 끊지 않을 때 그 시험이 실제로
  얼마 만에 끝나는지, 그리고 단언이 초록인지 본다. 60초를 넘기고도 초록이면 "늦게 끝났다"이고, 600초
  안에 끝나지 않으면 "멈췄다"다.

고친 판(저장소의 시험에 넉넉한 제한을 준 판)은 `before` 판으로 잰다. 고친 길을 지났다는 표지는 대상
시험이 60초 넘게 걸리고도 초록인 회차다(`passed_over_60s`). 옛 제한이었다면 그 회차는 넘김으로
빨갰다.

회차마다 `pnpm -C web exec vitest run eslint.config.test.ts --project node --reporter=json
--outputFile=<임시>` 를 띄우고, 리포터의 JSON 에서 대상 시험의 `status`, `duration`,
`failureMessages` 를 읽는다. 표지(회차가 측정인지): 부하가 회차 끝까지 살아 있었다. JSON 이 쓰였고
그 파일의 시험 수가 기대와 같다(`EXPECTED_TESTS`, 파일이 시험을 더하면 고친다). 대상 셋이 모두
이름으로 실렸다. 대상 시험이 빨가면 그 실패가 제한 넘김(`Test timed out in`)이다. 표지가 없는 회차는
따로 세고 하나라도 있으면 종료 코드가 1 이다. 대상이 아닌 시험이 빨간 회차는 측정으로 세되 그 이름을
요약의 `other_failed` 에 싣는다. 회차를 통틀어 가장 오래 걸린 시험 여덟(`slowest_ms`)과, 파일
전체의 시간(`file_ms`)에서 시험들의 시간을 뺀 몫(`outside_tests_ms`. `beforeAll` 과 수집이 든다)도
낸다.

양성 대조(`--control slow`): 대상 시험이 늦게 끝나는 것을 이 셈이 빨강과 그 시간으로 잡는지 본다.
이 프로브가 그 회차 동안 `web/probe-slow-<pid>.setup.ts` 와, 저장소의 `web/vitest.config.ts` 를
`mergeConfig` 로 감싸 `test.setupFiles` 에 그 파일만 더한 `web/probe-slow-<pid>.vitest.config.ts` 를
써서 `--config` 로 붙이고 끝에 지운다. `--setupFiles` 로 붙이던 첫 대조 회차가 0.7초에 측정 없이
끝났고, 손으로 띄워 보니 vitest 5.0.2 의 명령줄이 그 옵션을 받지 않았다(`Unknown option`). setup
파일은 환경 변수 `ESLINT_PROGRAM_PROBE_SLOW_MS` 만큼, 대상 셋의 각 시험이 몸통에서 처음 부르는
`ESLint.prototype.lintText`(`next-react`)나 `spawnSync`(`cli-two`, `cli-lone`) 안에서 이벤트 루프를
막는다(`Atomics.wait`). vitest 의 제한은 시험 함수와 훅에 따로 걸려(`withTimeout`), 시험 앞의
`beforeEach` 에서 막으면 훅의 제한에 들어 시험이 빨개지지 않는다. 그 판이 첫 판이었고 돌리기 전에
vitest 5.0.2 의 원본을 읽고 고쳤다. 저장소의 vitest 설정은 건드리지 않는다. `before` 판에서 65초를
막으면 셋 모두 제한 넘김으로 빨개야 셈이 맞다(요약의 `control_ok`). 고친 판에는 같은 막힘을 거는
`--control slow-pass` 를 쓴다. 셋 모두 65초 넘게 걸리고도 초록이어야 고친 제한이 그 시험들에 실제로
걸린 것이다.

부하는 같은 폴더의 `mutate_ctrl_c.py` 의 `burners` 를 그대로 쓴다(`--burners K`,
`--pytest-loads P`). `--out` 을 주면 pytest 부하 i 의 출력을 `<out 의 이름>_pytest<i>.txt` 에 남기고
실패 줄을 요약의 `pytest_load_failed` 에 싣는다.

돌리는 법: 저장소 루트에서 `PYTHONUTF8=1 uv run python <이 파일> N [--mode before|observe]
[--burners K] [--pytest-loads P] [--control slow|slow-pass] --out <JSON>`. 이 파일은
`.scratch/harness/probes/precommit_xdist/eslint_program_timeout.py` 다. `pnpm` 이 PATH 에 있어야
한다.

못 보는 것: pre-commit 이 web-verify 의 다른 단계(타입체크, 다른 vitest 프로젝트)와 함께 돌릴 때의
모양, vitest 일꾼이 뜨지 못한 사건(일지 2026-10-19-24), 다른 기계.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

from mutate_ctrl_c import ROOT, burners, failed_in, kill_tree

TARGETS = {
    "next-react": "app/ 이 next 와 react 를 import 하는 것은 아무것도 보고되지 않는다",
    "cli-two": "끄기 주석이 끄려던 위반은 verify 의 린트 명령에서 그대로 보고되고 빨갛다",
    "cli-lone": "가릴 위반이 없는 끄기 주석 하나만으로도 verify 의 린트 명령은 빨갛다",
}
# 2026-10-19 의 `web/eslint.config.test.ts` 가 든 시험의 수. 파일이 시험을 더하거나 빼면 고친다
EXPECTED_TESTS = 61
TIMEOUT_MARK = "Test timed out in"
OBSERVE_TIMEOUT_MS = 600_000
SLOW_MS = 65_000
SLOW_ENV = "ESLINT_PROGRAM_PROBE_SLOW_MS"
# vitest 의 제한은 시험 함수와 훅에 따로 걸려, `beforeEach` 에서 막으면 시험이 아니라 훅의
# 제한(120초)에 든다. 그래서 대상 시험이 몸통에서 처음 부르는 `lintText`·`spawnSync` 를 감싸 그
# 안에서 막는다. 시험 파일의 `spawnSync` 는 내장 모듈의 이름 있는 export 라 `syncBuiltinESMExports`
# 로 바꾼 값을 옮긴다
SETUP = """
import childProcess from "node:child_process";
import { syncBuiltinESMExports } from "node:module";
import { ESLint } from "eslint";
import { afterEach, beforeEach } from "vitest";

const TARGETS = new Set(%s);
const slow = Number(process.env["%s"] ?? "0");
let pending = false;

function block() {
  if (pending) {
    pending = false;
    Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, slow);
  }
}

const lintText = ESLint.prototype.lintText;
ESLint.prototype.lintText = function (...args) {
  block();
  return lintText.apply(this, args);
};
const spawnSync = childProcess.spawnSync;
childProcess.spawnSync = function (...args) {
  block();
  return spawnSync.apply(this, args);
};
syncBuiltinESMExports();

beforeEach((context) => {
  pending = slow > 0 && TARGETS.has(context.task.name);
});
afterEach(() => {
  pending = false;
});
"""
# vitest 5.0.2 의 명령줄은 `--setupFiles` 를 받지 않았다(`Unknown option`. 첫 대조 회차가 0.7초에
# 끝난 뒤 손으로 띄워 봤다). 그래서 저장소의 설정을 감싸 `test.setupFiles` 만 더한 설정 파일을
# `--config` 로 넘긴다. node 프로젝트는 `extends: true` 라 그 값을 물려받는다
CONFIG = """
import { mergeConfig } from "vitest/config";
import base from "./vitest.config.ts";

export default mergeConfig(base, { test: { setupFiles: [%s] } });
"""


def vitest_once(
    pnpm: str, mode: str, config: Path | None, report: Path, env: dict[str, str]
) -> tuple[int, float]:
    command = [
        pnpm,
        "-C",
        "web",
        "exec",
        "vitest",
        "run",
        "eslint.config.test.ts",
        "--project",
        "node",
        "--reporter=json",
        f"--outputFile={report}",
    ]
    if mode == "observe":
        command.append(f"--testTimeout={OBSERVE_TIMEOUT_MS}")
    if config is not None:
        command.append(f"--config={config}")
    start = time.monotonic()
    process = subprocess.Popen(
        command, cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    try:
        returncode = process.wait(timeout=OBSERVE_TIMEOUT_MS / 1000 * 4)
    except subprocess.TimeoutExpired:
        # `pnpm` 은 cmd 로 풀려 그것만 끝내면 vitest 와 일꾼이 남아, 다음 회차가 그 옆에서 돈다.
        # 트리째 끝낸다. 그 회차는 JSON 이 없어 측정이 아니다
        with contextlib.suppress(subprocess.TimeoutExpired):
            kill_tree(process)
        return -1, time.monotonic() - start
    return returncode, time.monotonic() - start


def read_report(report: Path) -> dict[str, object] | None:
    try:
        loaded: object = json.loads(report.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return loaded if isinstance(loaded, dict) else None


def assertions(report: dict[str, object]) -> list[dict[str, object]]:
    found: list[dict[str, object]] = []
    files = report.get("testResults")
    if not isinstance(files, list):
        return found
    for file in files:
        if isinstance(file, dict) and isinstance(file.get("assertionResults"), list):
            found += [row for row in file["assertionResults"] if isinstance(row, dict)]
    return found


def row_of(code: int, seconds: float, report: dict[str, object] | None, *, alive: bool) -> dict:
    row: dict[str, object] = {"exit": code, "seconds": round(seconds, 1), "reason": None}
    if not alive:
        row["reason"] = "부하가 회차 중에 끝났다"
        return row
    if report is None:
        row["reason"] = "리포터의 JSON 이 없다"
        return row
    found = assertions(report)
    if EXPECTED_TESTS and len(found) != EXPECTED_TESTS:
        row["reason"] = f"시험 수가 {len(found)} 이다(기대 {EXPECTED_TESTS})"
        return row
    by_title = {str(item.get("title")): item for item in found}
    targets: dict[str, object] = {}
    for key, title in TARGETS.items():
        item = by_title.get(title)
        if item is None:
            row["reason"] = f"대상 시험이 실리지 않았다: {key}"
            return row
        messages = item.get("failureMessages")
        text = "\n".join(str(message) for message in messages) if isinstance(messages, list) else ""
        status = str(item.get("status"))
        timed_out = TIMEOUT_MARK in text
        if status != "passed" and not timed_out:
            row["reason"] = f"대상 시험이 제한 넘김 밖의 까닭으로 빨갰다: {key}"
        targets[key] = {
            "status": status,
            "duration_ms": item.get("duration"),
            "timed_out": timed_out,
            "message": text[:200],
        }
    row["targets"] = targets
    row["tests"] = len(found)
    durations = {
        str(item.get("title")): float(duration)
        for item in found
        if isinstance(duration := item.get("duration"), int | float)
    }
    row["durations"] = durations
    files = report.get("testResults")
    first = files[0] if isinstance(files, list) and files else None
    if isinstance(first, dict) and isinstance(first.get("startTime"), int | float):
        # 파일의 시작과 끝 사이에서 시험들의 시간을 뺀 몫에 beforeAll 과 수집이 든다(어림)
        row["file_ms"] = float(first["endTime"]) - float(first["startTime"])
        row["outside_tests_ms"] = row["file_ms"] - sum(durations.values())
    row["other_failed"] = [
        str(item.get("title"))
        for item in found
        if item.get("status") != "passed" and str(item.get("title")) not in TARGETS.values()
    ]
    return row


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


def summarize(rows: list[dict], control: str) -> dict[str, object]:
    measured = [row for row in rows if row["reason"] is None]
    by_target: dict[str, object] = {}
    for key in TARGETS:
        items = [row["targets"][key] for row in measured]
        durations = [
            float(item["duration_ms"]) for item in items if item["duration_ms"] is not None
        ]
        by_target[key] = {
            "measured": len(items),
            "red": sum(1 for item in items if item["status"] != "passed"),
            "timed_out": sum(1 for item in items if item["timed_out"]),
            "over_60s": sum(1 for value in durations if value >= 60_000),
            # 고친 길을 지났다는 표지: 60초 넘게 걸리고도 초록이다(옛 제한이면 넘김으로 빨갰다)
            "passed_over_60s": sum(
                1
                for item in items
                if item["status"] == "passed" and float(item["duration_ms"] or 0) >= 60_000
            ),
            "duration_ms": tail(durations),
        }
    longest: dict[str, float] = {}
    for row in measured:
        for title, value in row["durations"].items():
            longest[title] = max(longest.get(title, 0.0), value)
    summary: dict[str, object] = {
        "by_target": by_target,
        "other_failed": sorted({name for row in measured for name in row["other_failed"]}),
        "vitest_seconds": tail([float(row["seconds"]) for row in measured]),
        "file_ms": tail([row["file_ms"] for row in measured if "file_ms" in row]),
        "outside_tests_ms": tail(
            [row["outside_tests_ms"] for row in measured if "outside_tests_ms" in row]
        ),
        # 회차를 통틀어 가장 오래 걸린 시험 여덟(대상 밖의 시험이 60초에 다가가는지 본다)
        "slowest_ms": dict(sorted(longest.items(), key=lambda pair: -pair[1])[:8]),
    }
    if control:
        summary["control"] = control
        if control == "slow":
            ok = all(row["targets"][key]["timed_out"] for row in measured for key in TARGETS)
        else:
            ok = all(
                row["targets"][key]["status"] == "passed"
                and float(row["targets"][key]["duration_ms"] or 0) >= SLOW_MS
                for row in measured
                for key in TARGETS
            )
        summary["control_ok"] = bool(measured) and ok
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("runs", type=int)
    parser.add_argument("--mode", choices=("before", "observe"), default="before")
    parser.add_argument("--burners", type=int, default=0)
    parser.add_argument("--pytest-loads", type=int, default=0)
    parser.add_argument("--control", choices=("slow", "slow-pass"), default="")
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    pnpm = shutil.which("pnpm")
    if pnpm is None:
        print(json.dumps({"error": "pnpm 을 찾지 못했다"}, ensure_ascii=False))
        return 1
    out = Path(args.out) if args.out else None
    logs = (
        [out.with_name(f"{out.stem}_pytest{index}.txt") for index in range(args.pytest_loads)]
        if out
        else []
    )
    env = dict(os.environ)
    rows: list[dict] = []
    # setup 파일과 설정 파일은 `vitest` 와 저장소의 설정을 import 하므로 web/ 안에 둔다(저장소
    # 밖에서는 패키지를 찾지 못한다)
    setup = ROOT / "web" / f"probe-slow-{os.getpid()}.setup.ts" if args.control else None
    config = setup.with_name(f"probe-slow-{os.getpid()}.vitest.config.ts") if setup else None
    # 끝내지 못한 vitest 가 임시 폴더의 파일을 쥐어도 정리가 던져 요약을 잃지 않게 한다
    with (
        tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as directory,
        contextlib.ExitStack() as stack,
    ):
        if setup is not None and config is not None:
            names = json.dumps(list(TARGETS.values()), ensure_ascii=False)
            setup.write_text(SETUP % (names, SLOW_ENV), encoding="utf-8")
            stack.callback(setup.unlink, missing_ok=True)
            config.write_text(CONFIG % json.dumps(f"./{setup.name}"), encoding="utf-8")
            stack.callback(config.unlink, missing_ok=True)
            env[SLOW_ENV] = str(SLOW_MS)
        with burners(args.burners, args.pytest_loads, logs) as procs:
            began = time.monotonic()
            for index in range(args.runs):
                report = Path(directory) / f"report{index}.json"
                code, seconds = vitest_once(pnpm, args.mode, config, report, env)
                alive = all(proc.poll() is None for proc in procs)
                rows.append(row_of(code, seconds, read_report(report), alive=alive))
                if args.pytest_loads and not alive:
                    break
            elapsed = round(time.monotonic() - began, 1)
    reasons = [str(row["reason"]) for row in rows if row["reason"] is not None]
    summary: dict[str, object] = {
        "runs": args.runs,
        "rounds": len(rows),
        "mode": args.mode,
        "burners": args.burners,
        "pytest_loads": args.pytest_loads,
        "unmeasured": len(reasons),
        "unmeasured_reasons": sorted(set(reasons)),
        "seconds": elapsed,
        **summarize(rows, args.control),
        "pytest_load_failed": {path.name: failed_in(path) for path in logs},
        "rows": rows,
    }
    if out:
        out.write_text(json.dumps(summary, ensure_ascii=False) + "\n", encoding="utf-8")
    brief = {key: value for key, value in summary.items() if key != "rows"}
    print(json.dumps(brief, ensure_ascii=False), flush=True)
    if args.control and not summary.get("control_ok"):
        return 1
    return 1 if reasons else 0


if __name__ == "__main__":
    sys.exit(main())
