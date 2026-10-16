"""pytest 전체를 한 번 돌려 걸린 시간과 표지를 JSON 한 줄로 낸다(ADR 0035).

첫 인자는 `serial`(한 프로세스), 프로세스 수(`8`), `auto` 중 하나이고 둘째 인자는 pytest 의 원본
출력을 남길 파일이다. 한 줄 요약은 표준 출력과 `<파일>.json` 에 낸다. xdist 는
`uv run --with pytest-xdist` 의 일회용 환경에만 든다(프로젝트 의존성이 아니다). 처음 한 번은
내려받는다.

표지: 통과 집계 줄(`N passed`)이 있어야 하고, xdist 회차에는 `bringing up nodes` 나
`created: N/N workers` 줄이 있어야 한다. 프로세스 수를 줬으면 `created` 줄의 수가 같아야 한다.
하나라도 없으면 그 회차는 측정이 아니므로 종료 코드를 1 로 낸다. 사례가 실패한 것은 측정의 결과라
종료 코드에 넣지 않고 `failed` 에 센다. `auto` 는 `-q` 를 빼야 xdist 가 `created` 줄을 내서 그
회차만 `-q` 가 없다.

돌리는 법: 저장소 루트에서
`uv run python .scratch/harness/probes/precommit_xdist/pytest_run.py 8 <출력 파일>`.

못 보는 것: 같은 PC 에서 다른 세션이 CPU 를 쓰는 정도. 한 번의 값이라 회차 사이의 흔들림.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
# `-q` 가 없으면 집계 줄이 `=====` 로 감싸인다.
SUMMARY = re.compile(r"^(?:=+ )?(?:(?P<failed>\d+) failed, )?(?P<passed>\d+) passed", re.MULTILINE)
BANNER = re.compile(r"bringing up nodes|created: (?P<made>\d+)/(?P<wanted>\d+) workers")


def command(mode: str) -> list[str]:
    if mode == "serial":
        return ["uv", "run", "pytest", "-q", "-p", "no:cacheprovider"]
    quiet = [] if mode == "auto" else ["-q"]
    with_xdist = ["uv", "run", "--with", "pytest-xdist", "pytest"]
    return [*with_xdist, *quiet, "-p", "no:cacheprovider", "-n", mode]


def missing_marks(mode: str, output: str) -> list[str]:
    missing = []
    if SUMMARY.search(output) is None:
        missing.append("통과 집계 줄")
    if mode == "serial":
        return missing
    banner = BANNER.search(output)
    if banner is None:
        missing.append("xdist 가 뜬 줄")
    elif banner["made"] is not None and mode != "auto" and int(banner["made"]) != int(mode):
        missing.append(f"created 의 수 {mode} (실제 {banner['made']})")
    return missing


def main() -> int:
    mode, out = sys.argv[1], Path(sys.argv[2])
    start = time.monotonic()
    process = subprocess.run(
        command(mode),
        cwd=ROOT,
        env={**os.environ, "PYTHONUTF8": "1"},
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    seconds = time.monotonic() - start
    out.write_text(process.stdout, encoding="utf-8")
    summary = SUMMARY.search(process.stdout)
    banner = BANNER.search(process.stdout)
    made = None if banner is None or banner["made"] is None else int(banner["made"])
    workers = made if made is not None else (int(mode) if mode.isdigit() else None)
    missing = missing_marks(mode, process.stdout)
    row = {
        "mode": mode,
        "seconds": round(seconds, 2),
        "returncode": process.returncode,
        "passed": None if summary is None else int(summary["passed"]),
        "failed": 0 if summary is None or summary["failed"] is None else int(summary["failed"]),
        "workers": workers,
        "missing": missing,
    }
    line = json.dumps(row, ensure_ascii=False)
    Path(f"{out}.json").write_text(line + "\n", encoding="utf-8")
    print(line, flush=True)
    return 1 if missing else 0


if __name__ == "__main__":
    sys.exit(main())
