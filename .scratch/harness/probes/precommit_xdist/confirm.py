"""ADR 0035 의 완료 조건을 잰다. 구현된 러너의 한 바퀴를 연속으로, 그리고 두 벌 동시로 돌린다.

완료 조건은 검사 여덟을 함께 돌린 한 바퀴를 연속 5번, 같은 한 바퀴를 두 벌 동시에 세 번(여섯
회차) 통과하는 것이다. 한 회차를 통과로 세는 기준은 pytest 의 종료 코드 0 이고 skip 과 error 가 없는
것이다(ADR 0035 의 Consequences). `rounds.py` 는 출력 경로가 라벨 하나라 둘을 동시에 띄우면 서로의
출력을 덮고, pytest 를 구현 전의 껍질(`uv run --with pytest-xdist`)로 갈아 끼운다. 이 프로브는
러너의 `CHECKS` 를 그대로 돌리고, 출력을 부를 때마다 새 폴더에 남긴다.

하위 명령. 저장소 루트에서
`PYTHONUTF8=1 uv run python .scratch/harness/probes/precommit_xdist/confirm.py <하위 명령>`.
- `series <횟수>`: 한 바퀴를 차례로 횟수만큼 돈다.
- `pair <횟수>`: 한 바퀴 둘을 한꺼번에 띄우는 것을 차례로 횟수만큼 한다.
- `round <출력 폴더> <이름>`, `capture <출력 이름> -- <명령...>`: 위 둘이 부르는 안쪽 명령이다.

한 바퀴(`round`)는 `tools/run_checks.py` 의 `run` 을 부르고, 검사 목록에서 pytest 한 항목만 같은
명령을 `capture` 로 감싼다. 러너가 통과한 검사의 출력을 버려서, 그 껍질이 pytest 의 원본 출력과
요약(종료 코드, 집계, 시작과 끝의 벽시계 시각)을 남긴다. 출력은 `results/confirm_<시각>/`(같은 초에
부른 다른 호출이 그 이름을 먼저 잡았으면 `confirm_<시각>-<n>/`)에 회차마다 `<이름>.txt`(러너의 줄과
요약 한 줄), `<이름>.json`, `<이름>_pytest.txt`, `<이름>_pytest.json` 이다.

표지: 러너가 검사 목록의 모든 id 에 결과 줄을 찍었고, 러너의 pytest 명령에 `-n` 이 있고, pytest
출력에 집계 줄(`N passed`, `N error` 처럼 끝에 걸린 시간이 붙은 줄)과 xdist 가 뜬 줄(`bringing up
nodes`)이 있어야 그 회차가 측정이다. 두 벌 동시는 두 벌의 pytest 가 실제로 겹쳤는지(두 시작이 모두
두 끝보다 앞서는지)도 본다. 하나라도 빠지면 측정이 아니라 종료 코드를 1 로 낸다. 사례가 실패하거나
skip·error 가 있는 것은 측정의 결과라 종료 코드에 넣지 않고 마지막 줄의 통과 수에서 뺀다. 다른
검사가 빨간 것도 종료 코드에 넣지 않고 회차 줄의 `other_failed` 에만 적는다(통과 기준은 pytest 의
것이다). 2026-10-16 의 두 실행(`confirm_20261016-185135`, `confirm_20261016-191232`)은 표지가 "통과
집계 줄"이던 앞 판으로 돌았다. 모든 회차에 `passed` 가 있어 판정은 지금 판과 같다.

못 보는 것: 두 벌 동시는 같은 체크아웃에서 돈다. 실제로는 세션마다 워크트리가 달라서, 같은 자리를
쓰는 검사가 같은 체크아웃에서만 부딪힐 수 있다. 그 실패는 회차 줄의 `other_failed` 에 따로 적는다.
pre-commit 이 커밋 때 내보내는 git 환경과 러너 앞뒤의 가벼운 훅은 없다. 같은 PC 에서 다른 세션이
CPU 를 쓰는 정도와 회차 사이의 흔들림.
"""

from __future__ import annotations

import io
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))

from tools import run_checks  # noqa: E402

RESULTS = HERE / "results"
SELF = Path(__file__).resolve()
# `-q` 의 집계 줄은 감싸지 않고, 실패 요약이 있으면 `=====` 로 감싸일 수 있다.
SUMMARY = re.compile(r"^(?:=+ )?(?P<counts>\d+ \w+(?:, \d+ \w+)*) in [\d.]+s", re.MULTILINE)
COUNT = re.compile(r"(\d+) (\w+)")
BANNER = "bringing up nodes"
BAD = ("failed", "skipped", "error", "errors")


def summary_counts(output: str) -> dict[str, int]:
    """마지막 집계 줄의 낱말별 수. 집계 줄이 없으면 빈 사전."""
    found = list(SUMMARY.finditer(output))
    if not found:
        return {}
    return {word: int(n) for n, word in COUNT.findall(found[-1]["counts"])}


def capture(name: Path, command: list[str]) -> int:
    """명령을 돌려 원본 출력과 요약을 남기고 그 명령의 종료 코드로 끝난다."""
    executable = shutil.which(command[0]) or command[0]
    start = time.time()
    process = subprocess.run(
        [executable, *command[1:]],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    end = time.time()
    # 윈도의 pytest 는 `\r\n` 으로 찍는다. 그대로 텍스트 모드로 쓰면 `\r\r\n` 이 되어 홀로 선 CR 이
    # 남는다(첫 커밋의 줄 구분 문자 검사가 잡았다).
    output = process.stdout.decode("utf-8", errors="replace").replace("\r\n", "\n")
    Path(f"{name}.txt").write_text(output, encoding="utf-8")
    row = {
        "command": command,
        "returncode": process.returncode,
        "start": start,
        "end": end,
        "seconds": round(end - start, 2),
        "counts": summary_counts(output),
        "banner": BANNER in output,
    }
    Path(f"{name}.json").write_text(json.dumps(row, ensure_ascii=False) + "\n", encoding="utf-8")
    return process.returncode


def judge_round(runner_text: str, pytest_row: dict[str, object] | None) -> dict[str, object]:
    """러너의 줄과 pytest 요약에서 표지와 통과를 가린다."""
    lines = runner_text.splitlines()
    missing: list[str] = []
    other_failed: list[str] = []
    for check in run_checks.CHECKS:
        mine = [line for line in lines if line.startswith(f"{check.id}.")]
        if not any("Passed" in line or "Failed" in line for line in mine):
            missing.append(f"{check.id} 결과 줄")
        elif check.id != "pytest" and any("Failed" in line for line in mine):
            other_failed.append(check.id)
    if pytest_row is None:
        return {"missing": [*missing, "pytest 요약"], "passed": False, "other_failed": other_failed}
    command = pytest_row["command"]
    counts = pytest_row["counts"]
    assert isinstance(command, list) and isinstance(counts, dict)
    if "-n" not in command:
        missing.append("러너의 -n")
    if not pytest_row["banner"]:
        missing.append("xdist 가 뜬 줄")
    if not counts:
        missing.append("집계 줄")
    clean = pytest_row["returncode"] == 0 and not any(counts.get(word) for word in BAD)
    workers = command[command.index("-n") + 1] if "-n" in command else None
    return {
        "missing": missing,
        "passed": clean and not missing,
        "other_failed": other_failed,
        "workers": workers,
        "counts": counts,
        "pytest_returncode": pytest_row["returncode"],
        "pytest_seconds": pytest_row["seconds"],
        "pytest_start": pytest_row["start"],
        "pytest_end": pytest_row["end"],
    }


def read_json(path: Path) -> dict[str, object] | None:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else None


def run_round(folder: Path, name: str) -> int:
    pytest_name = folder / f"{name}_pytest"
    checks: list[run_checks.Check] = []
    for check in run_checks.CHECKS:
        if check.id == "pytest":
            wrapped = ("uv", "run", "python", str(SELF), "capture", str(pytest_name), "--")
            checks.append(run_checks.Check("pytest", wrapped + check.command))
        else:
            checks.append(check)
    buffer = io.BytesIO()
    start = time.monotonic()
    code = run_checks.run(tuple(checks), os.environ, ROOT, buffer)
    seconds = round(time.monotonic() - start, 1)
    # 러너는 실패한 검사의 출력 바이트를 그대로 옮긴다. `capture` 와 같은 까닭으로 `\r\n` 을 접는다.
    text = buffer.getvalue().decode("utf-8", errors="replace").replace("\r\n", "\n")
    row = {
        "name": name,
        "seconds": seconds,
        "runner_code": code,
        **judge_round(text, read_json(Path(f"{pytest_name}.json"))),
    }
    line = json.dumps(row, ensure_ascii=False)
    (folder / f"{name}.txt").write_text(text + line + "\n", encoding="utf-8")
    (folder / f"{name}.json").write_text(line + "\n", encoding="utf-8")
    print(line, flush=True)
    return 1 if row["missing"] else 0


def new_folder() -> Path:
    """부를 때마다 새 폴더. 같은 초에 부른 다른 호출이 이름을 먼저 잡았으면 뒤에 번호를 붙인다."""
    stamp = time.strftime("%Y%m%d-%H%M%S")
    RESULTS.mkdir(parents=True, exist_ok=True)
    n = 1
    while True:
        folder = RESULTS / (f"confirm_{stamp}" if n == 1 else f"confirm_{stamp}-{n}")
        try:
            folder.mkdir()
        except FileExistsError:
            n += 1
            continue
        return folder


def round_command(folder: Path, name: str) -> list[str]:
    uv = shutil.which("uv") or "uv"
    return [uv, "run", "python", str(SELF), "round", str(folder), name]


def series(times: int) -> int:
    folder = new_folder()
    print(json.dumps({"folder": str(folder), "cpu_count": os.cpu_count()}), flush=True)
    rows = []
    for i in range(1, times + 1):
        name = f"series{i}"
        subprocess.run(
            round_command(folder, name), cwd=ROOT, stdout=subprocess.DEVNULL, check=False
        )
        row = read_json(folder / f"{name}.json") or {"name": name, "missing": ["회차 요약"]}
        print(json.dumps(row, ensure_ascii=False), flush=True)
        rows.append(row)
    return finish(rows, f"연속 {times}번")


def pair(times: int) -> int:
    folder = new_folder()
    print(json.dumps({"folder": str(folder), "cpu_count": os.cpu_count()}), flush=True)
    rows = []
    for i in range(1, times + 1):
        names = (f"pair{i}a", f"pair{i}b")
        procs = [
            subprocess.Popen(round_command(folder, name), cwd=ROOT, stdout=subprocess.DEVNULL)
            for name in names
        ]
        for proc in procs:
            proc.wait()
        both = [read_json(folder / f"{name}.json") or {"missing": ["회차 요약"]} for name in names]
        starts = [row.get("pytest_start") for row in both]
        ends = [row.get("pytest_end") for row in both]
        numbers = [v for v in (*starts, *ends) if isinstance(v, float)]
        overlapped = len(numbers) == 4 and max(numbers[:2]) < min(numbers[2:])
        for name, row in zip(names, both, strict=True):
            missing = list(row.get("missing") or [])
            if not overlapped:
                missing.append("두 벌이 겹쳤다")
            row = {**row, "name": name, "missing": missing, "overlapped": overlapped}
            print(json.dumps(row, ensure_ascii=False), flush=True)
            rows.append(row)
    return finish(rows, f"두 벌 동시 {times}번")


def finish(rows: list[dict[str, object]], label: str) -> int:
    measured = [row for row in rows if not row.get("missing")]
    passed = [row for row in measured if row.get("passed")]
    print(
        f"{label}: 회차 {len(rows)}, 측정 {len(measured)}, 통과 {len(passed)}, "
        f"측정 아님 {len(rows) - len(measured)}",
        flush=True,
    )
    return 0 if len(measured) == len(rows) else 1


def main() -> int:
    command = sys.argv[1]
    if command == "capture":
        return capture(Path(sys.argv[2]), sys.argv[sys.argv.index("--") + 1 :])
    if command == "round":
        return run_round(Path(sys.argv[2]), sys.argv[3])
    if command == "series":
        return series(int(sys.argv[2]))
    if command == "pair":
        return pair(int(sys.argv[2]))
    print(f"모르는 하위 명령: {command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
