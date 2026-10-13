"""tests/tools/test_open_session.py 의 시간을 다른 판의 같은 파일과 번갈아 잰다(ADR 0030 이력).

ADR 0030 은 이 파일의 시간이 사례 36개에 약 30초의 두 배를 넘으면 사례를 묶을지 정한다고 했다.
다른 세션이 도는 PC 에서는 유휴 상태의 절대값을 잴 수 없어, 같은 부하에서 견줄 판의 파일과
번갈아 돌려 비를 낸다. 견줄 판의 파일은 `tests/tools/` 에 잠깐 복사해 같은 스크립트(지금의
`tools/open_session.ps1`)를 부르게 하고 끝나면 지운다. 사례 하나의 값은 두 판이 같다고 본다.
복사본의 이름은 `test_` 로 시작하지 않아 전체 pytest 가 줍지 않고(명령 줄에 직접 준 파일은 이름과
무관하게 모은다), `.gitignore` 에 있어 커밋되지 않는다. 프로브가 강제로 끊겨 `finally` 가 돌지
못하고 남은 복사본은 다음 실행이 알리고 덮어쓴다(PR 직전 버그·성능 리뷰).

회차마다 pytest 의 마지막 줄이 `<N> passed in <초>s` 이고 실패가 없을 때만 측정으로 센다. 측정이
아닌 회차가 있으면 1로 끝난다. 시간은 pytest 가 내는 그 줄의 초다.

돌리는 법: 저장소 루트에서
`PYTHONUTF8=1 uv run python .scratch/harness/probes/open_session_test_time.py`.
`--base <커밋>`(기본 origin/main)과 `--rounds <N>`(기본 2)을 받는다. pwsh 가 PATH 에 있어야 한다.
회차마다 차례를 바꿔(견줄 판 먼저, 지금 판 먼저) 부하의 흐름이 한쪽에 쏠리지 않게 한다.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
TARGET = Path("tests") / "tools" / "test_open_session.py"
COPY = Path("tests") / "tools" / "open_session_base_copy.py"
SUMMARY = re.compile(r"^(\d+) passed in ([\d.]+)s")


class NotMeasured(Exception):
    """pytest 의 마지막 줄이 실패 없는 통과가 아니라 그 회차가 측정이 아니다."""


def _run(test_file: Path) -> tuple[int, float]:
    done = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", str(test_file)],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    lines = done.stdout.strip().splitlines()
    last = lines[-1] if lines else ""
    match = SUMMARY.match(last)
    if done.returncode != 0 or match is None:
        raise NotMeasured(f"{test_file}: {last!r}")
    return int(match.group(1)), float(match.group(2))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="origin/main")
    parser.add_argument("--rounds", type=int, default=2)
    args = parser.parse_args()

    shown = subprocess.run(
        ["git", "-c", "core.longpaths=true", "show", f"{args.base}:{TARGET.as_posix()}"],
        cwd=ROOT,
        capture_output=True,
        check=False,
    )
    if shown.returncode != 0:
        print(f"{args.base} 의 {TARGET} 를 읽지 못했다", file=sys.stderr)
        return 1
    copy = ROOT / COPY
    if copy.exists():
        print(f"앞 실행이 남긴 {COPY} 를 덮어쓴다", file=sys.stderr)
    copy.write_bytes(shown.stdout)
    misses: list[str] = []
    try:
        for round_no in range(1, args.rounds + 1):
            order = [COPY, TARGET] if round_no % 2 else [TARGET, COPY]
            results: dict[Path, tuple[int, float]] = {}
            for test_file in order:
                try:
                    results[test_file] = _run(test_file)
                except NotMeasured as miss:
                    misses.append(str(miss))
            if len(results) != 2:
                continue
            base_cases, base_seconds = results[COPY]
            cases, seconds = results[TARGET]
            print(
                f"round={round_no} first={'base' if order[0] == COPY else 'now'} "
                f"base={base_cases}개 {base_seconds:.2f}s now={cases}개 {seconds:.2f}s "
                f"ratio={seconds / base_seconds:.2f}"
            )
    finally:
        copy.unlink(missing_ok=True)
    for miss in misses:
        print(f"측정 아님: {miss}", file=sys.stderr)
    return 1 if misses else 0


if __name__ == "__main__":
    raise SystemExit(main())
