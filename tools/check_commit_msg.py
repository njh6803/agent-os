"""커밋 메시지 검사. 컨벤셔널 커밋 형식을 기계가 판정한다.

- 제목은 `<타입>: <제목>` 또는 `<타입>(<범위>): <제목>`. 타입은 git-commit 스킬의 표와 같다.
- 제목은 72자 이하, 끝에 마침표 없음.
- Merge, Revert, fixup!, squash! 로 시작하는 메시지는 통과시킨다.

pre-commit의 commit-msg 스테이지가 돌린다. 산문 규칙(`docs/constitution/operations.md`)은
"왜와 남긴 위험을 본문에"이고 그것은 리뷰가 본다. 여기는 형식만.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

TYPES = ("feat", "fix", "docs", "style", "refactor", "test", "chore", "perf")
PATTERN = re.compile(r"^(" + "|".join(TYPES) + r")(\([\w\-./ ]+\))?!?: \S.*$")
PASS_PREFIXES = ("Merge ", "Revert ", "fixup! ", "squash! ")
MAX_SUBJECT = 72


def subject_of(text: str) -> str:
    for line in text.splitlines():
        if line.strip() and not line.startswith("#"):
            return line.rstrip()
    return ""


def problems_for(subject: str) -> list[str]:
    if subject.startswith(PASS_PREFIXES):
        return []
    problems: list[str] = []
    if PATTERN.match(subject) is None:
        problems.append(
            f"제목이 '<타입>: <제목>' 형식이 아니다: {subject!r}. 타입은 {', '.join(TYPES)}"
        )
    if len(subject) > MAX_SUBJECT:
        problems.append(f"제목 {len(subject)}자 > {MAX_SUBJECT}자")
    if subject.endswith("."):
        problems.append("제목 끝에 마침표를 쓰지 않는다")
    return problems


def main(path: str) -> int:
    subject = subject_of(Path(path).read_text(encoding="utf-8"))
    problems = problems_for(subject)
    for problem in problems:
        print(problem)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
