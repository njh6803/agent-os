"""검사 여덟을 함께 띄워 pre-commit 러너의 한 바퀴를 잰다(ADR 0035).

`tools/run_checks.py` 의 `run` 을 그대로 부르고, 검사 목록에서 pytest 한 항목만 `pytest_run.py` 를
거치게 갈아 끼운다. 러너는 통과한 검사의 출력을 버려서, 그 껍질이 pytest 의 원본 출력과 표지를
파일에 남긴다. `--split` 이면 `web-verify` 도 여섯 단계(`time_web_steps.STEPS`)를 각자 검사로 쪼개
겹쳐 돌린다. 저장소 파일은 바꾸지 않는다.

표지: pytest 껍질의 표지(통과 집계 줄, xdist 가 뜬 줄)가 빠지면 껍질이 1 로 끝나 한 바퀴의 종료
코드도 1 이다. 사례가 실패한 것은 측정의 결과라 종료 코드에 넣지 않고 마지막 줄의 `실패` 에 센다.
다른 검사가 빨가면 종료 코드 1 이다.

돌리는 법: 저장소 루트에서
`uv run python .scratch/harness/probes/precommit_xdist/rounds.py <프로세스 수 또는 auto> [--split]`.
표준 출력이 러너의 줄과 마지막 줄이라 `results/round_xdist<수>.txt` 로 받는다.

못 보는 것: 한 바퀴 앞뒤에 도는 가벼운 훅(ruff 둘, 마크다운 검사 등)의 시간. 같은 PC 에서 다른
세션이 CPU 를 쓰는 정도. 한 번의 값이라 회차 사이의 흔들림.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

from time_web_steps import STEPS  # noqa: E402

from tools import run_checks  # noqa: E402

RESULTS = HERE / "results"


def build_checks(mode: str, pytest_out: Path, *, split: bool) -> tuple[run_checks.Check, ...]:
    pytest_run = ("uv", "run", "python", str(HERE / "pytest_run.py"), mode, str(pytest_out))
    checks: list[run_checks.Check] = []
    for check in run_checks.CHECKS:
        if check.id == "pytest":
            checks.append(run_checks.Check("pytest", pytest_run))
        elif check.id == "web-verify" and split:
            checks.extend(
                run_checks.Check(f"web-{s}", ("pnpm", "-C", "web", "run", s)) for s in STEPS
            )
        else:
            checks.append(check)
    return tuple(checks)


def main() -> int:
    mode = sys.argv[1]
    split = "--split" in sys.argv[2:]
    label = f"round_{'split' if split else 'xdist'}{mode}"
    pytest_out = RESULTS / f"{label}_pytest.txt"
    row_path = Path(f"{pytest_out}.json")
    row_path.unlink(missing_ok=True)
    start = time.monotonic()
    code = run_checks.run(
        build_checks(mode, pytest_out, split=split), os.environ, ROOT, sys.stdout.buffer
    )
    elapsed = time.monotonic() - start
    if not row_path.exists():
        print(f"한 바퀴 {elapsed:.1f}초 ({label}), pytest 껍질이 요약을 남기지 않았다", flush=True)
        return 1
    row = json.loads(row_path.read_text(encoding="utf-8"))
    tail = f"pytest 통과 {row['passed']} 실패 {row['failed']}, 종료 코드 {code}"
    print(f"한 바퀴 {elapsed:.1f}초 ({label}), {tail}", flush=True)
    return code


if __name__ == "__main__":
    sys.exit(main())
