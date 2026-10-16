"""skip 을 세션 실패로 만드는 판정(원칙 II)이 xdist 로 나눠 돌 때도 서는지 본다(ADR 0035).

`tests/conftest.py` 의 `pytest_sessionfinish` 가 skip 이 하나라도 있으면 종료 코드를 1 로 바꾼다.
같은 사례(`skip_case.py`: skip 하나, 통과 둘)를 세 번 돌린다. 한 프로세스(xdist 를 끈다), xdist 2개,
xdist 자동이다. 셋 다 `uv run --with pytest-xdist` 의 같은 일회용 환경에서 돌아 시간 차이에 환경을
만드는 비용이 섞이지 않는다. 사례가 저장소 밖(`tests/` 밖)이라 conftest 가 자동으로 걸리지 않아
`-p tests.conftest` 로 불러온다. 자동 회차는 `-q` 가 없어 xdist 가 만든 프로세스 수(`created: N/N
workers`)를 낸다. 그 수와 `os.cpu_count()` 를 함께 적는다.

표지: 세 회차 모두 skip 줄(`skip 1건. …(원칙 II)`), 요약 `2 passed, 1 skipped`, 종료 코드 1 이
있어야 하고, xdist 회차에는 `bringing up nodes` 나 `created` 줄도 있어야 한다. 하나라도 없으면 그
회차는 측정이 아니므로 종료 코드를 1 로 낸다.

돌리는 법: 저장소 루트에서
`uv run python .scratch/harness/probes/precommit_xdist/skip_under_xdist.py`.
출력은 `results/skip_under_xdist.txt`.

못 보는 것: `-m llm` 의 토큰 합계(`tests/conftest.py` 의 stash 가 프로세스별인지). 사례가 작아 경주
조건이 필요한 판정은 보지 못한다.
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
CASE = Path(__file__).with_name("skip_case.py")
SKIP_LINE = "skip 1건. skip된 테스트는 초록이 아니다(원칙 II)"
CREATED = re.compile(r"created: (\d+)/(\d+) workers")
BASE = ("uv", "run", "--with", "pytest-xdist", "pytest", "-c", "pyproject.toml")
CASE_ARGS = ("-p", "tests.conftest", str(CASE), "-p", "no:cacheprovider", "-rs")
RUNS = (
    ("serial", (*BASE, *CASE_ARGS, "-q", "-p", "no:xdist"), ()),
    ("xdist2", (*BASE, *CASE_ARGS, "-q", "-n", "2"), ("bringing up nodes",)),
    ("xdist_auto", (*BASE, *CASE_ARGS, "-n", "auto"), ("created:",)),
)


def main() -> int:
    env = {**os.environ, "PYTHONUTF8": "1"}
    bad = False
    for name, command, extra in RUNS:
        start = time.monotonic()
        process = subprocess.run(
            command,
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
        seconds = time.monotonic() - start
        output = process.stdout + process.stderr
        wanted = (SKIP_LINE, "2 passed, 1 skipped", *extra)
        missing = [mark for mark in wanted if mark not in output]
        if process.returncode != 1:
            missing.append(f"종료 코드 1 (실제 {process.returncode})")
        created = CREATED.search(output)
        row = {
            "run": name,
            "seconds": round(seconds, 2),
            "workers": None if created is None else int(created[1]),
            "cpu_count": os.cpu_count(),
            "missing": missing,
        }
        bad = bad or bool(missing)
        print(json.dumps(row, ensure_ascii=False), flush=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
