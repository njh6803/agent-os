"""harness 티켓 번호의 판정자. 같은 번호의 티켓은 둘이 아니다(ticket-for-every-pr 01).

harness 티켓은 `.scratch/harness/issues/NNN-<slug>.md` 이고 번호는 `tools/sibling_overlap.py` 의
다음 빈 번호로 받는다(ADR 0037 "번호"). 그 대조는 그 순간의 main 과 형제만 보고, 브랜치가 main 을
merge 커밋으로 들인 뒤에는 main 에 병합된 같은 번호의 티켓이 merge-base 에 들어 "새로" 매긴 번호가
아니라 겹침으로 보지 않는다(셀프 리뷰 명세 축이 임시 저장소로 봤다). 슬러그가 달라 git 충돌도 나지
않는다. CI 는 PR 의 병합 커밋에서 돌고 main 보호가 strict 라, 나중에 병합되는 PR 은 이 테스트에
걸린다. 일지의 같은 자리는 `tests/test_journal_names.py` 가 본다.

막지 못하는 것: 관리자 우회 병합과 main 직접 푸시. 그 뒤로는 main 의 push CI 와 뒤따르는 PR 이 모두
이 테스트에서 빨갛다.
못 보는 것: 이름이 세 자리 번호로 시작하지 않는 파일(번호 도구도 티켓으로 읽지 않는다), 하위
디렉터리, 번호의 빠짐과 차례, 기능 폴더(`.scratch/<slug>/issues/`)의 두 자리 번호.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ISSUES = ROOT / ".scratch" / "harness" / "issues"
_TICKET_NAME = re.compile(r"(?P<number>\d{3})-.+\.md")


def ticket_number_problems(names: Iterable[str]) -> list[str]:
    """같은 번호를 든 티켓 파일이 둘 이상인 것."""
    by_number: dict[str, list[str]] = {}
    for name in sorted(names):
        if (match := _TICKET_NAME.fullmatch(name)) is not None:
            by_number.setdefault(match["number"], []).append(name)
    return [
        f"{number}: 번호가 겹친다 — {', '.join(group)}"
        for number, group in by_number.items()
        if len(group) > 1
    ]


def _ticket_names() -> list[str]:
    return sorted(path.name for path in ISSUES.glob("*.md"))


def test_harness_티켓_파일을_하나는_읽는다() -> None:
    """읽은 것이 없는데 겹침 0 으로 초록이 되는 것을 막는다(tests.md, 대기열 98).

    파일이 있어도 번호 꼴에 맞는 이름이 없으면 겹침 판정이 본 것이 없으므로 그 꼴로 센다(PR #345
    CodeRabbit).
    """
    names = _ticket_names()
    assert any(_TICKET_NAME.fullmatch(name) for name in names), f"번호 꼴의 티켓 없음: {names}"


def test_이_저장소의_harness_티켓은_번호가_겹치지_않는다() -> None:
    assert ticket_number_problems(_ticket_names()) == []


def test_같은_번호의_harness_티켓을_잡는다() -> None:
    names = ["001-alpha.md", "001-zulu.md", "002-other.md", "01-feature.md", "README.md"]

    assert ticket_number_problems(names) == ["001: 번호가 겹친다 — 001-alpha.md, 001-zulu.md"]
