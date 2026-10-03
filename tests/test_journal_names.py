"""일지 파일 이름의 판정자. 같은 날의 순번은 겹치지 않는다(대기열 99).

`docs/constitution/operations.md`가 일지를 `<날짜>-<NN>-<슬러그>.md`로 정하고
"같은 날 세션 둘이 쓰면 순번이 갈라 주고"라고 적는다. 긴 세션 동안 다른 PR이 같은 순번으로
먼저 병합되면 슬러그가 달라 git 충돌이 나지 않고 조용히 둘이 된다(`2026-09-28-06` 한 쌍).
커밋 전 대조(`CLAUDE.md`, 대기열 48)는 번호를 매긴 커밋이 상대 PR의 병합보다 앞서면 그
커밋에서 보지 못하고, main을 들인 뒤에는 목록이 빈다. CI는 PR의 병합 커밋에서 돌고 main
보호가 strict라, 나중에 병합되는 PR은 main을 들인 뒤의 CI에서 이 테스트에 걸린다.

막지 못하는 것: 관리자 우회 병합과 main 직접 푸시. 그 뒤로는 main의 push CI와 뒤따르는 PR이
모두 이 테스트에서 빨갛다.
못 보는 것: `docs/journal/` 바로 아래의 `.md`만 본다(하위 디렉터리, 다른 확장자). 순번의 빠짐과
차례, 날짜가 실제로 있는 날인지, 순번이 아닌 내용의 겹침.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JOURNAL = ROOT / "docs" / "journal"
_NUMBERED_NAME = re.compile(r"(?P<number>\d{4}-\d{2}-\d{2}-\d{2})-.+\.md")

# 순번 규약 전의 이름. 새 일지는 순번을 단다.
BEFORE_NUMBERING = frozenset(
    {
        "2026-09-19-kickoff.md",
        "2026-09-21-first-slice.md",
        "2026-09-21-interrupts-design.md",
        "2026-09-21-open-session.md",
        "2026-09-21-review-feedback.md",
        "2026-09-21-session-boundary.md",
    }
)
# 순번이 겹친 채 병합된 것. 계획·명세·대기열이 이 번호나 파일 이름으로 가리켜 옮기지 않는다.
SHARED_NUMBERS = {
    "2026-09-28-06": frozenset(
        {"2026-09-28-06-hook-runner.md", "2026-09-28-06-web-admin-design.md"}
    ),
}


def journal_name_problems(names: Iterable[str]) -> list[str]:
    """이름이 순번 모양이 아닌 것과, 같은 날의 순번이 겹친 것."""
    problems: list[str] = []
    by_number: dict[str, list[str]] = {}
    for name in sorted(names):
        match = _NUMBERED_NAME.fullmatch(name)
        if match is None:
            if name not in BEFORE_NUMBERING:
                problems.append(f"{name}: 이름이 <날짜>-<NN>-<슬러그>.md 모양이 아니다")
            continue
        by_number.setdefault(match["number"], []).append(name)
    for number, group in by_number.items():
        if len(group) > 1 and frozenset(group) != SHARED_NUMBERS.get(number):
            problems.append(f"{number}: 순번이 겹친다 — {', '.join(group)}")
    return problems


def _journal_names() -> list[str]:
    return sorted(path.name for path in JOURNAL.glob("*.md"))


def test_일지_파일을_하나는_읽는다() -> None:
    """읽은 것이 없는데 겹침 0 으로 초록이 되는 것을 막는다(tests.md, 대기열 98)."""
    assert _journal_names()


def test_이_저장소의_일지는_같은_날의_순번이_겹치지_않는다() -> None:
    assert journal_name_problems(_journal_names()) == []


def test_같은_날의_순번이_겹친_일지를_잡는다() -> None:
    names = ["2026-10-03-01-a.md", "2026-10-03-01-b.md", "2026-10-03-02-c.md"]

    assert journal_name_problems(names) == [
        "2026-10-03-01: 순번이 겹친다 — 2026-10-03-01-a.md, 2026-10-03-01-b.md"
    ]


def test_다른_날의_같은_순번은_겹침이_아니다() -> None:
    assert journal_name_problems(["2026-10-02-01-a.md", "2026-10-03-01-a.md"]) == []


def test_순번이_없는_새_일지를_잡는다() -> None:
    """순번이 없으면 겹침 대조를 빠져나간다. 규약 전의 옛 이름만 예외다."""
    assert journal_name_problems(["2026-10-03-a.md", "2026-09-21-first-slice.md"]) == [
        "2026-10-03-a.md: 이름이 <날짜>-<NN>-<슬러그>.md 모양이 아니다"
    ]


def test_이미_병합된_한_쌍은_정확히_그_둘이면_지나간다() -> None:
    """저장소 상태 테스트에만 기대면, 두 파일이 옮겨져 예외가 죽어도 초록이다(PR #127 리뷰)."""
    names = ["2026-09-28-06-hook-runner.md", "2026-09-28-06-web-admin-design.md"]

    assert journal_name_problems(names) == []


def test_이미_병합된_한_쌍에_셋째가_붙으면_잡는다() -> None:
    names = [
        "2026-09-28-06-hook-runner.md",
        "2026-09-28-06-web-admin-design.md",
        "2026-09-28-06-third.md",
    ]

    assert journal_name_problems(names) == [
        "2026-09-28-06: 순번이 겹친다 — 2026-09-28-06-hook-runner.md, 2026-09-28-06-third.md,"
        " 2026-09-28-06-web-admin-design.md"
    ]
