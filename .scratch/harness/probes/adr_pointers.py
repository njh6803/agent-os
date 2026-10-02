"""ADR 본문의 `(바뀜: ...)` 포인터가 실제 이력 제목과 글자 그대로 맞는지 본다(대기열 88).

포인터 모양은 `.claude/rules/adr.md`가 정한다. 제목은 가리키는 ADR(앞에 `ADR NNNN`이 없으면
자기 ADR)의 `###` 줄에서 날짜 뒤와 같아야 하고, 포인터는 `## 이력` 위(본문)에 있어야 한다.
0006의 `## 개정 이력`은 그 뒤에 Consequences가 오는 본문의 절이라 이력으로 보지 않는다.
`(바뀜:`으로 시작하지만 모양이 맞지 않는 것(따옴표 빠짐, `ADR 14`)과 없는 ADR을 가리키는 것도
어긋남으로 센다.

못 보는 것: 포인터가 달려야 하는데 없는 본문 문장. 그것은 뜻의 판단이라 사람과 리뷰가 본다.
제목이 맞아도 그 이력이 정말 그 문장을 바꿨는지도 보지 못한다.

돌리는 법: 저장소 루트에서 `uv run python .scratch/harness/probes/adr_pointers.py`. 어긋나면 1이다.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
ADR_DIR = ROOT / "docs" / "adr"
MARK = "(바뀜:"
POINTER = re.compile(r'\(바뀜: (?:ADR (\d{4}) ?)?(?:이력 (\d{4}-\d{2}-\d{2}) "([^"]+)")?\)')


def adr_file(number: str) -> Path | None:
    matches = list(ADR_DIR.glob(f"{number}-*.md"))
    return matches[0] if len(matches) == 1 else None


def history_titles(path: Path) -> set[str]:
    lines = path.read_text(encoding="utf-8").splitlines()
    return {line[4:].strip() for line in lines if line.startswith("### ")}


def problems_of(path: Path) -> tuple[int, list[str]]:
    lines = path.read_text(encoding="utf-8").splitlines()
    history_at = next((i for i, line in enumerate(lines) if line.strip() == "## 이력"), len(lines))
    titles: dict[Path, set[str]] = {}
    total = 0
    found: list[str] = []
    for index, line in enumerate(lines):
        where = f"{path.name}:{index + 1}"
        matches = list(POINTER.finditer(line))
        total += line.count(MARK)
        if line.count(MARK) != len(matches):
            found.append(f"{where}: 모양이 맞지 않는 `{MARK}`가 있다")
        for match in matches:
            cited_adr, date, title = match.groups()
            target = adr_file(cited_adr) if cited_adr else path
            reasons: list[str] = []
            if index >= history_at:
                reasons.append("이력 절 안에 있다")
            if cited_adr is None and date is None:
                reasons.append("가리키는 것이 없다")
            if target is None:
                reasons.append(f"ADR {cited_adr}이 없다")
            elif date is not None:
                if target not in titles:
                    titles[target] = history_titles(target)
                if f"{date} {title}" not in titles[target]:
                    reasons.append(f"{target.name}에 그 제목이 없다")
            if reasons:
                found.append(f"{where}: {match.group(0)} — {', '.join(reasons)}")
    return total, found


def main() -> int:
    total = 0
    found: list[str] = []
    for path in sorted(ADR_DIR.glob("0*.md")):
        count, problems = problems_of(path)
        total += count
        found.extend(problems)
    for line in found:
        print(line)
    print(f"포인터 {total}개, 어긋남 {len(found)}개")
    return 1 if found else 0


if __name__ == "__main__":
    sys.exit(main())
