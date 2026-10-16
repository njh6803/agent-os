"""`pytest --durations=40` 출력에서 느린 테스트가 어느 파일에 몰렸는지 센다(ADR 0035).

`results/pytest_serial.txt` 는 한 프로세스로 pytest 전체를 돌린 출력이다. 그 안의
`slowest 40 durations` 아래 줄들을 파일마다 합한다. 줄의 모양은 `<초>s call <파일>::<이름>` 이다.
상위 40개의 합이 전체 시간(맨 끝의 요약 줄)에서 차지하는 몫과 나머지 테스트의 평균도 찍는다.

표지: 요약 줄(`N passed … in S s`)이 있고 `call` 줄이 40개여야 한다. 아니면 측정이 아니므로 종료
코드를 1 로 낸다.

돌리는 법: `uv run python .scratch/harness/probes/precommit_xdist/slowest_by_file.py [출력 파일]`.

못 보는 것: 40번째 아래의 분포(`--durations=0` 로 돌리지 않았다). setup·teardown 시간은 상위 40개에
들지 않아 합에 없다.
"""

from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

DEFAULT = Path(__file__).with_name("results") / "pytest_serial.txt"
DURATION = re.compile(r"^(?P<sec>[\d.]+)s call\s+(?P<file>[^:\s]+)::")
SUMMARY = re.compile(r"^(?P<passed>\d+) passed.* in (?P<sec>[\d.]+)s")


def main() -> int:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
    per_file: dict[str, float] = defaultdict(float)
    counts: dict[str, int] = defaultdict(int)
    total_seconds = 0.0
    tests = 0
    calls = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if (match := DURATION.match(line)) is not None:
            per_file[match["file"]] += float(match["sec"])
            counts[match["file"]] += 1
            calls += 1
        elif (match := SUMMARY.match(line)) is not None:
            tests = int(match["passed"])
            total_seconds = float(match["sec"])
    if calls != 40 or tests == 0:
        print(f"표지 없음: call 줄 {calls}개, 통과 {tests}개")
        return 1
    top = sum(per_file.values())
    print(f"전체 {total_seconds:.2f}초, 통과 {tests}개")
    print(f"상위 {calls}개 합 {top:.1f}초 ({top / total_seconds:.0%})")
    rest = (total_seconds - top) / (tests - calls)
    print(f"나머지 {tests - calls}개는 {total_seconds - top:.1f}초, 평균 {rest:.2f}초")
    for name, seconds in sorted(per_file.items(), key=lambda item: -item[1]):
        print(f"{seconds:7.1f}초 {counts[name]:2d}개 {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
