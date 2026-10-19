"""패턴 호출의 시간 제한 시험이 부하에서 왜 빨개지는지 가른다(대기열 306, ADR 0035).

대상은 `tests/tools/test_open_session.py` 의
`test_패턴_호출은_제한_시간에_돌아오고_멈춘_호출을_센다` 다. `tools/open_session.ps1` 의
`Invoke-PatternTimed` 가 가짜 요소의 패턴 호출을 스레드 잡(`Start-ThreadJob`)으로 띄우고
`Wait-Job -Timeout` 으로 기다린다. 고치기 전 시험은 지연 0 의 호출(`[0-ok-0]`)이 1초 제한 안에 `ok`
를 돌려주는지, 3초 자는 호출(`[3000-expand-hung-1]`)이 제한에서 `expand-hung` 으로 돌아오는지 본다.
pre-commit 의 pytest 에서 `[0-ok-0]` 이 두 번 빨갰다(`expand-hung`. 일지 2026-10-16-50,
2026-10-17-04). 고친 판은 제한을 사례마다 준다. 지연 0 의 호출은 제한 30초(`[0-30-ok-0-30000]`)이고,
멈춘 호출은 제한 1초에 20초 동안 풀어 주기를 기다리며 6초 안에 돌아와야 한다
(`[20000-1-expand-hung-1-6000]`).

고친 길을 지났다는 표지는 `Wait-Job` 이 기다린 시간으로 센다. 고치기 전 판의 1초 제한은 그
기다림에만 걸린다. 기다린 시간은 사례 본문 앞에 같은 이름의 함수로 `Wait-Job` 을 감싸 잰다. 서버가
함수와 본문을 한 스크립트로 이어 돌려, `Invoke-PatternTimed` 안의 `Wait-Job` 이 cmdlet 보다 그
함수를 먼저 찾는다. 사례가 걸린 시간(`elapsed_ms`)은 표지가 못 된다. 스레드 잡을 띄우는 몫까지 들어,
고치기 전 판이 1초 넘게 걸리고도 통과한 회차가 있었다(셀프 리뷰가 짚었다, 일지 2026-10-19-10).

기다림이 1초 이상인 것만으로도 표지가 못 된다. 부하에서는 1초 제한이 늦게 걸린다. 2026-10-19 의 32개
측정에서 고치기 전 판의 지연 0 사례는 빨간 회차가 1182~1328ms 를 기다린 뒤 돌아왔고, 1080~1272ms 를
기다리고 통과한 회차도 넷 있었다. 제한이 실제로 걸린 시각은 멈춘 사례가 본다. 그 사례는 두 판 모두
제한 1초에 잡이 끝나지 않으므로, 기다린 시간이 곧 그 회차에 제한이 걸린 시각이다. 그래서 표지는 고친
판의 지연 0 사례가 통과하면서, 같은 측정의 멈춘 사례가 기다린 가장 긴 시간(두 판 가운데 긴 것)보다
오래 기다린 회차다. 그 측정에서 1초 제한은 그때까지 모두 걸렸으니, 그 회차는 고치기 전 판이라면
`expand-hung` 이었다고 본다. 요약은 판과 사례마다 통과하면서 1초 넘게 기다린 값
(`passed_waited_over_1000ms`)과 빨간 사례가 기다린 값(`red_waited`)과 기다린 시간의
분포(`waited_ms`)를 내고, 두 판과 두 사례를 맞대 세는 것은 읽는 쪽이 한다. 양성 대조는 둘이다.
고치기 전 판의 빨간 지연 0 사례가 모두 1초 넘게 기다렸고(`red_waited_below_1000ms` 가 0), 멈춘
사례가 모두 1초 넘게 기다렸다(`waited_ms` 의 `at_least_1000ms` 가 측정 회차와 같다). 둘 가운데
하나라도 어긋나면 감싼 함수가 재는 것이 그 제한이 견주는 것과 다르다.

그 시험 모듈에서 스레드 잡을 띄우는 시험은 이것 하나라, 첫 사례는 대개 그 pwsh 서버(모듈의
`_SERVER`, xdist 일꾼마다 하나)의 첫 스레드 잡이다. 그래서 회차마다 서버를 새로 띄우고 둘을 잰다.

- `cold`: 새 서버에서 처음 띄운 스레드 잡. `Invoke-PatternTimed` 의 두 줄(`Start-ThreadJob`,
  `Wait-Job`)을 같은 스크립트 블록으로 펼쳐 제한 30초로 부르고, 띄우기까지와 `Wait-Job` 이 기다린
  시간을 따로 잰다. 제한이 견주는 것은 뒤의 것이다.
- 사례: 서버를 다시 새로 띄운 뒤 시험 함수를 `parametrize` 의 값마다 그대로 부르고, 시험 모듈의
  `_call` 을 감싸 pwsh 가 돌려준 출력(`결과|걸린 ms|센 멈춘 호출`)을 남긴다. 첫 사례가 그 서버의 첫
  스레드 잡이다. 본문 끝에 감싼 `Wait-Job` 이 기다린 ms 를 한 줄 더 내게 하고, 감싼 `_call` 이 그
  줄을 떼어 남긴 뒤 나머지를 시험에 돌려준다.
- `warm`: 같은 서버에서 `cold` 와 같은 호출을 한 번 더 부른다(앞 사례가 스레드 잡을 띄운 뒤다).

서버는 띄운 직전에 `$PID` 를 한 번 불러, 서버를 띄우는 시간이 잰 값에 들지 않게 한다. 시험 모듈을
경로로 불러 함수만 부르므로 pytest 의 수집과 어설션 고쳐 쓰기는 빠진다. 시험 모듈이 제 파일의
자리에서 센 스크립트 경로(`SCRIPT`)는 불러온 뒤 저장소의 `tools/open_session.ps1` 로 바꾼다. 그래서
어설션의 빨강에는 메시지가 없고, 출력으로 무엇을 봤는지 안다. `--test-file` 을 여러 번 주면 그
파일들을 회차마다 번갈아 부른다. 파일마다 pwsh 서버가 하나다.

해석의 갈래. 지연 0 사례의 빨강이

- A. 첫 스레드 잡이 늦게 뜬다: 같은 회차의 `cold` 가 1초 넘게 기다렸다. 부하에서 새 런스페이스를
  여는 비용이 제한을 넘긴 것이다. 갈래를 받치는 대조는 `warm` 이 같은 부하에서 1초를 넘는 일이
  드문지다.
- B. 그 밖: 같은 회차의 `cold` 가 1초 안에 끝났다.

같은 회차의 `cold` 와 사례는 다른 서버의 첫 잡이라, 갈래는 회차 단위의 대리 지표다. 그래서 갈래와
함께 `cold`·`warm` 이 1초를 넘긴 회차 수를 낸다. 2026-10-18 의 측정에서는 `cold` 가 1초를 넘긴
회차에도 같은 회차의 사례가 통과해, `cold` 가 사례와 같은 분포가 아니었고 이 갈래를 대리 지표로 쓰지
못했다(일지 2026-10-19-10. 그때는 사례의 빨강도 재현되지 않았다). 2026-10-19 에 고치기 전 판만 잰
측정에서는 사례의 빨강이 재현됐고(32개 40회차에 4번, pytest 세 벌 38회차에 1번), 다섯 모두 B 였다.
두 판을 번갈아 잰 측정의 갈래는 README 행에 있다.

표지(회차가 측정인지): 부하 프로세스가 회차가 끝날 때까지 살아 있었다, 서버를 새로 띄울 때마다
`$PID` 가 숫자였다, 사례마다 pwsh 가 세 칸의 출력을 돌려줬다(시험이 패턴 호출까지 갔다), 사례마다
감싼 `Wait-Job` 이 기다린 ms 를 냈다(패턴 호출이 그 함수를 거쳤다), `cold`·`warm` 이 모두 `ok` 를
돌려줬다. 표지가 없는 회차는 따로 세고, 하나라도 있으면 종료 코드가 1 이다.

부하는 같은 폴더의 `mutate_ctrl_c.py` 의 `burners` 를 그대로 쓴다(`--burners K`,
`--pytest-loads P`). `--out` 을 주면 pytest 부하 i 의 출력을 `<out 의 이름>_pytest<i>.txt` 에
남기고, 그 부하도 대상 시험을 한 번 돌므로 실패 줄을 요약의 `pytest_load_failed` 에 싣는다.

돌리는 법: 저장소 루트에서 `PYTHONUTF8=1 uv run python <이 파일> N [--burners K]
[--pytest-loads P] [--test-file <경로>]… --out <JSON>`. 이 파일은
`.scratch/harness/probes/precommit_xdist/open_session_pattern_timed.py` 다. 표준 출력에는 회차별
행을 뺀 요약 한 줄을 낸다. `--resummarize <JSON>…` 은 측정하지 않고 저장한 회차 행으로 요약만 다시
내어 그 파일에 쓴다.

못 보는 것: pytest 와 xdist 가 얹는 것, 실제 pre-commit 에서 그 사례 앞에 같은 서버를 쓴 사례들의
상태, 실제 pre-commit 부하의 모양, 다른 기계. `cold` 는 `Invoke-PatternTimed` 를 펼친 사본이라
그 함수가 바뀌면 함께 고친다. 감싼 `Wait-Job` 은 함수 호출 한 겹을 더해, 사례가 걸린 시간에 그 몫이
든다(재지 않았다). `waited` 칸은 2026-10-19 의 셀프 리뷰 뒤에 더했다.
`open_session_pattern_timed_all.sh` 의 앞 넷(고치기 전 판만 잰 재현)은 그 전 판으로 돌려 결과에 그
칸이 없다.
"""

from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

from mutate_ctrl_c import ROOT, burners, failed_in, load_test_module

TEST_FILE = ROOT / "tests" / "tools" / "test_open_session.py"
SCRIPT = ROOT / "tools" / "open_session.ps1"
TEST_NAME = "test_패턴_호출은_제한_시간에_돌아오고_멈춘_호출을_센다"
CUT_MS = 1000  # 고치기 전 시험의 지연 0 사례가 준 제한
CALL_LINE = "$got = Invoke-PatternTimed $element 'expand'"
# `Invoke-PatternTimed` 의 두 줄을 펼친 것. 띄우기까지와 `Wait-Job` 이 기다린 시간을 따로 낸다
SPLIT = r"""
$job = Start-ThreadJob -ArgumentList $element, 'expand' -ScriptBlock {
    param($e, $a)
    $e.GetCurrentPattern([System.Windows.Automation.ExpandCollapsePattern]::Pattern).Expand()
    'ok'
}
$started = $watch.ElapsedMilliseconds
$done = Wait-Job $job -Timeout 30
$waited = $watch.ElapsedMilliseconds - $started
$got = if ($done) { Receive-Job $job; Remove-Job $job -Force } else { 'expand-hung' }
"$got|$started|$waited"
"""
# 사례 본문 앞에 둔다. `Invoke-PatternTimed` 안의 `Wait-Job` 이 이 함수를 거쳐 기다린 시간을 남긴다
WAIT_PROXY = r"""
$script:ProbeWaitedMs = -1
function Wait-Job {
    param($Job, $Timeout)
    $probeWatch = [System.Diagnostics.Stopwatch]::StartNew()
    $probeDone = Microsoft.PowerShell.Core\Wait-Job @PSBoundParameters
    $script:ProbeWaitedMs = $probeWatch.ElapsedMilliseconds
    $probeDone
}
"""
WAITED_PREFIX = "probe-waited|"
# 사례 본문 끝에 둔다. 감싼 `_call` 이 이 줄을 떼어 낸다
WAIT_TAIL = f'\n"{WAITED_PREFIX}$script:ProbeWaitedMs"\n'

# 사례는 pwsh 의 결과, 걸린 ms, 센 멈춘 호출이고, 잰 호출(`cold`·`warm`)은 결과, 띄운 ms, 기다린 ms
# 다
Got = tuple[str, int, int]


@dataclass
class Case:
    params: dict[str, object]
    outcome: str
    got: Got | None
    waited: int | None


@dataclass
class Row:
    run: int
    file: int
    cases: list[Case]
    cold: Got | None
    warm: Got | None
    pids_ok: bool
    reason: str | None = None


def params(test: Callable[..., None]) -> list[dict[str, object]]:
    """시험의 `parametrize` 표지에서 사례마다의 인자를 꺼낸다."""
    marks: list[object] = list(getattr(test, "pytestmark", []))
    for mark in marks:
        if getattr(mark, "name", "") != "parametrize":
            continue
        names, rows = getattr(mark, "args", ((), ()))
        keys = [name.strip() for name in names] if isinstance(names, tuple) else []
        return [dict(zip(keys, row, strict=True)) for row in rows]
    raise SystemExit(f"{TEST_NAME} 에 parametrize 가 없다")


def split_waited(stdout: str) -> tuple[str, int | None]:
    """출력에서 `WAIT_TAIL` 의 줄을 떼어 나머지와 기다린 ms 를 낸다. 그 줄이 없거나 -1 이면
    `None`."""
    kept: list[str] = []
    waited: int | None = None
    for line in stdout.splitlines(keepends=True):
        if line.startswith(WAITED_PREFIX):
            value = line[len(WAITED_PREFIX) :].strip()
            waited = int(value) if value.isdigit() else None
        else:
            kept.append(line)
    return "".join(kept), waited


def watch_calls(module: ModuleType, box: list[tuple[str, int | None]]) -> None:
    original: Callable[..., subprocess.CompletedProcess[str]] = module._call

    def wrapped(*args: object, **kw: object) -> subprocess.CompletedProcess[str]:
        completed = original(*args, **kw)
        kept, waited = split_waited(completed.stdout)
        box.append((kept.strip(), waited))
        return subprocess.CompletedProcess(
            completed.args, completed.returncode, stdout=kept, stderr=completed.stderr
        )

    module._call = wrapped


def parsed(stdout: str) -> Got | None:
    fields = stdout.split("|")
    if len(fields) != 3 or not fields[1].isdigit() or not fields[2].isdigit():
        return None
    return fields[0], int(fields[1]), int(fields[2])


def split_body(body: str) -> str | None:
    """시험 본문에서 패턴 호출 줄부터 끝까지를 `SPLIT` 으로 바꾼다. 그 줄이 없으면 `None`."""
    at = body.find(CALL_LINE)
    return None if at < 0 else body[:at] + SPLIT.lstrip("\n")


def timed(module: ModuleType, body: str | None) -> Got | None:
    if body is None:
        return None
    completed = module._call("Invoke-PatternTimed", body, {"delay_ms": 0})
    return parsed(completed.stdout.strip())


def fresh_server(module: ModuleType) -> bool:
    """서버를 닫고 새로 띄운다. 새 서버의 `$PID` 가 숫자면 참이다."""
    module._SERVER.close()
    completed = module._call("", "$PID", {})
    return completed.stdout.strip().isdigit()


def run_once(
    module: ModuleType, box: list[tuple[str, int | None]], split: str | None, index: int, which: int
) -> Row:
    test: Callable[..., None] = getattr(module, TEST_NAME)
    first = fresh_server(module)
    cold = timed(module, split)
    second = fresh_server(module)
    cases: list[Case] = []
    for given in params(test):
        box.clear()
        outcome = "passed"
        try:
            test(**given)
        except Exception as error:  # 실패의 모양을 센다
            outcome = type(error).__name__
        stdout, waited = box[-1] if box else ("", None)
        cases.append(Case(given, outcome, parsed(stdout) if box else None, waited))
    return Row(index, which, cases, cold, timed(module, split), first and second)


def reason_for(row: Row, *, alive: bool) -> str | None:
    if not alive:
        return "부하가 회차 중에 끝났다"
    if not row.pids_ok:
        return "새로 띄운 서버의 $PID 가 숫자가 아니다"
    if any(case.got is None for case in row.cases):
        return "pwsh 가 세 칸의 출력을 돌려주지 않았다"
    if any(case.waited is None for case in row.cases):
        return "감싼 Wait-Job 이 기다린 시간을 내지 않았다"
    for name, got in (("cold", row.cold), ("warm", row.warm)):
        if got is None or got[0] != "ok":
            return f"{name} 이 ok 가 아니다: {got}"
    return None


def tail(values: list[int]) -> dict[str, float]:
    if not values:
        return {}
    ordered = sorted(values)
    return {
        "n": len(ordered),
        "median": statistics.median(ordered),
        "p95": ordered[min(len(ordered) - 1, int(len(ordered) * 0.95))],
        "max": ordered[-1],
        f"at_least_{CUT_MS}ms": sum(1 for value in ordered if value >= CUT_MS),
    }


def waited(got: Got | None) -> int:
    return got[2] if got else 0


def summarize(rows: list[Row], files: list[Path]) -> list[dict[str, object]]:
    by_file: list[dict[str, object]] = []
    for which, path in enumerate(files):
        measured = [row for row in rows if row.file == which and row.reason is None]
        per_case: list[dict[str, object]] = []
        for position in range(len(measured[0].cases) if measured else 0):
            seen = [(row, row.cases[position]) for row in measured]
            red = [(row, case) for row, case in seen if case.outcome != "passed"]
            waits = [
                (case.outcome == "passed", case.waited)
                for _, case in seen
                if case.waited is not None
            ]
            per_case.append(
                {
                    "case": seen[0][1].params,
                    "passed": len(seen) - len(red),
                    "red": len(red),
                    "red_branches": {
                        "A": sum(1 for row, _ in red if waited(row.cold) >= CUT_MS),
                        "B": sum(1 for row, _ in red if waited(row.cold) < CUT_MS),
                    },
                    "elapsed_ms": tail([case.got[1] for _, case in seen if case.got]),
                    "waited_ms": tail([waited for _, waited in waits]),
                    # 통과하면서 1초 넘게 기다린 값. 고친 판 지연 0 사례의 이 값을 멈춘 사례의
                    # `waited_ms` 의 `max` 와 맞대 표지를 센다(독스트링)
                    f"passed_waited_over_{CUT_MS}ms": sorted(
                        waited for passed, waited in waits if passed and waited >= CUT_MS
                    ),
                    # 고치기 전 판에서 0 이어야 하는 대조
                    f"red_waited_below_{CUT_MS}ms": sum(
                        1 for passed, waited in waits if not passed and waited < CUT_MS
                    ),
                    "red_got": [case.got for _, case in red][:10],
                    "red_waited": sorted(waited for passed, waited in waits if not passed),
                    "red_cold": [row.cold for row, _ in red][:10],
                }
            )
        by_file.append(
            {
                "test_file": str(path),
                "measured": len(measured),
                "cases": per_case,
                "cold_started_ms": tail([row.cold[1] for row in measured if row.cold]),
                "cold_waited_ms": tail([waited(row.cold) for row in measured]),
                "warm_waited_ms": tail([waited(row.warm) for row in measured]),
            }
        )
    return by_file


def run(
    runs: int, burner_count: int, pytest_loads: int, files: list[Path], logs: list[Path]
) -> dict[str, object]:
    modules = [load_test_module(path, index) for index, path in enumerate(files)]
    boxes: list[list[tuple[str, int | None]]] = [[] for _ in modules]
    splits: list[str | None] = []
    for module, box in zip(modules, boxes, strict=True):
        # 시험 모듈은 스크립트 경로를 제 파일의 자리에서 센다. 저장소 밖의 사본이면 없는 경로가 되어
        # 서버가 스크립트를 부르지 못한다(첫 실행의 44회차가 모두 측정 아님이었다)
        module.SCRIPT = SCRIPT
        body = str(module._PATTERN_TIMED)
        splits.append(split_body(body))
        # 시험 함수는 본문을 모듈의 이름으로 찾으므로 바꿔 둔 본문이 사례에 쓰인다
        module._PATTERN_TIMED = WAIT_PROXY + body + WAIT_TAIL
        watch_calls(module, box)
    rows: list[Row] = []
    seconds = 0.0
    try:
        with burners(burner_count, pytest_loads, logs) as procs:
            began = time.monotonic()
            for index in range(runs):
                which = index % len(modules)
                row = run_once(modules[which], boxes[which], splits[which], index, which)
                alive = all(proc.poll() is None for proc in procs)
                row.reason = reason_for(row, alive=alive)
                rows.append(row)
                if pytest_loads and not alive:
                    break
            seconds = round(time.monotonic() - began, 1)
    finally:
        for module in modules:
            module._SERVER.close()
    reasons = [row.reason for row in rows if row.reason is not None]
    return {
        "runs": runs,
        "burners": burner_count,
        "pytest_loads": pytest_loads,
        "unmeasured": len(reasons),
        "unmeasured_reasons": sorted(set(reasons)),
        "seconds": seconds,
        "by_file": summarize(rows, files),
        "pytest_load_failed": {path.name: failed_in(path) for path in logs[:pytest_loads]},
        "rows": [
            {
                "run": row.run,
                "file": row.file,
                "reason": row.reason,
                "cold": row.cold,
                "warm": row.warm,
                "cases": [[case.params, case.outcome, case.got, case.waited] for case in row.cases],
            }
            for row in rows
        ],
    }


def got_from(value: object) -> Got | None:
    if not isinstance(value, list) or len(value) != 3:
        return None
    first, second, third = value
    if isinstance(first, str) and isinstance(second, int) and isinstance(third, int):
        return first, second, third
    return None


def rows_from(saved: list[dict[str, object]]) -> list[Row]:
    """결과 JSON 의 회차 행을 `Row` 로 되돌린다. `waited` 칸이 없는 옛 행은 `None` 이다."""
    rows: list[Row] = []
    for item in saved:
        cases: list[Case] = []
        entries = item["cases"]
        for entry in entries if isinstance(entries, list) else []:
            given, outcome, got = entry[0], entry[1], entry[2]
            waited_ms = entry[3] if len(entry) > 3 else None
            cases.append(
                Case(
                    given if isinstance(given, dict) else {},
                    str(outcome),
                    got_from(got),
                    waited_ms if isinstance(waited_ms, int) else None,
                )
            )
        run_index, which, reason = item["run"], item["file"], item["reason"]
        rows.append(
            Row(
                run_index if isinstance(run_index, int) else -1,
                which if isinstance(which, int) else -1,
                cases,
                got_from(item["cold"]),
                got_from(item["warm"]),
                pids_ok=True,
                reason=reason if isinstance(reason, str) else None,
            )
        )
    return rows


def resummarize(path: Path) -> None:
    """저장한 회차 행으로 요약(`by_file`)만 다시 내어 그 파일에 쓴다. 측정은 다시 하지 않는다."""
    summary = json.loads(path.read_text(encoding="utf-8"))
    files = [Path(part["test_file"]) for part in summary["by_file"]]
    summary["by_file"] = summarize(rows_from(summary["rows"]), files)
    path.write_text(json.dumps(summary, ensure_ascii=False) + "\n", encoding="utf-8")
    brief = {key: value for key, value in summary.items() if key != "rows"}
    print(json.dumps(brief, ensure_ascii=False), flush=True)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("runs", type=int, nargs="?", default=0)
    parser.add_argument("--burners", type=int, default=0)
    parser.add_argument("--pytest-loads", type=int, default=0)
    parser.add_argument("--test-file", action="append", help="번갈아 부를 시험 파일")
    parser.add_argument("--out", default=None)
    parser.add_argument("--resummarize", nargs="+", default=[], help="요약만 다시 낼 결과 JSON")
    args = parser.parse_args()
    if args.resummarize:
        for name in args.resummarize:
            resummarize(Path(name))
        return 0
    files = [Path(name) for name in args.test_file or [str(TEST_FILE)]]
    out = Path(args.out) if args.out else None
    logs = (
        [out.with_name(f"{out.stem}_pytest{index}.txt") for index in range(args.pytest_loads)]
        if out
        else []
    )
    summary = run(args.runs, args.burners, args.pytest_loads, files, logs)
    if out:
        out.write_text(json.dumps(summary, ensure_ascii=False) + "\n", encoding="utf-8")
    brief = {key: value for key, value in summary.items() if key != "rows"}
    print(json.dumps(brief, ensure_ascii=False), flush=True)
    return 1 if summary["unmeasured"] else 0


if __name__ == "__main__":
    sys.exit(main())
