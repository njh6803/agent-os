"""일지 파일 이름의 판정자. 전환일 뒤의 일지는 시각 꼴이고, 같은 분의 일지는 겹치지 않는다.

`docs/constitution/operations.md`가 일지를 `<날짜>-<HHMM>-<슬러그>.md`로 정한다(ADR 0045 결정 7).
앞부분은 그 세션이 일지를 만든 로컬 시분이라 번호를 받지 않고, 먼저 만들고 늦게 병합해도 이름을
옮기지 않는다. 순번 꼴(`<날짜>-<NN>-<슬러그>.md`)은 전환일까지 만든 옛 일지의 이름이다.

두 가지를 막는다. 전환일(`TRANSITION_DAY`) 뒤 날짜의 순번 꼴 일지와, `<날짜>-<HHMM>` 앞부분이
겹치는 새 꼴 일지 둘이다. 같은 분에 다른 슬러그로 만든 일지 둘은 파일 이름이 달라 git이 알리지
않지만, 인용 `일지 <날짜>-<HHMM>`이 둘로 풀린다. CI는 PR의 병합 커밋에서 돌고 main 보호가 strict라,
늦게 병합되는 PR이 main을 들인 뒤의 CI에서 이 시험에 막힌다. 그 PR의 세션이 분을 바꿔 이름을
옮기고 이 브랜치가 들인 인용을 고친다. 옛 꼴의 같은 날 순번 겹침도 계속 본다(대기열 99).

`TRANSITION_DAY`는 이 PR이 마지막으로 origin/main을 합친 날(로컬 날짜)이다. 전환일은 일지 이름
티켓이 병합된 날인데 커밋할 때는 알 수 없고, 병합하는 세션이 병합 직전에 main을 합치므로 대개
같은 날이다. 다르면 상수가 그만큼 앞서 그 사이에 순번 꼴로 만든 일지도 빨개진다. 세션이 main을
다시 합칠 때마다 이 상수를 그날로 옮긴다. 날짜가 그대로면 빨개지는 시험이 없어 알리지 못한다.

막지 못하는 것: 관리자 우회 병합과 main 직접 푸시. 그 뒤로는 main의 push CI와 뒤따르는 PR이
모두 이 테스트에서 빨갛다. 그때는 처음 본 세션이 상수를 옮기거나 그 파일 이름을 바꾸는 PR을 낸다.
못 보는 것: `docs/journal/` 바로 아래의 `.md`만 본다(하위 디렉터리, 다른 확장자). 시각이 실제로
그 세션이 만든 때인지, 날짜가 실제로 있는 날인지, 순번이 아닌 내용의 겹침.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
JOURNAL = ROOT / "docs" / "journal"
_STAMPED_NAME = re.compile(r"(?P<stamp>\d{4}-\d{2}-\d{2}-\d{4})-.+\.md")
_NUMBERED_NAME = re.compile(r"(?P<number>\d{4}-\d{2}-\d{2}-\d{2})-.+\.md")

# 이 PR이 마지막으로 origin/main을 합친 날(로컬 날짜). 이 날짜 뒤의 순번 꼴 일지는 빨갛다.
TRANSITION_DAY = "2026-11-07"

# 순번 규약 전의 이름. 새 일지는 시각을 단다.
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

_HOW_TO_NAME = (
    "일지 이름은 `<날짜>-<HHMM>-<슬러그>.md`이고 앞부분은 Bash의 `date +%Y-%m-%d-%H%M`이나"
    " PowerShell의 `Get-Date -Format yyyy-MM-dd-HHmm`으로 짓는다"
    "(`docs/constitution/operations.md` 일지 규칙)."
)
_HOW_TO_FIX = "`git mv`로 이름을 바꾸고, 이 브랜치가 들인 그 일지의 인용도 고친다."


def journal_name_problems(names: Iterable[str]) -> list[str]:
    """새 꼴이 아닌 이름, 전환일 뒤의 순번 꼴, 같은 분의 겹침, 같은 날 순번의 겹침."""
    problems: list[str] = []
    by_stamp: dict[str, list[str]] = {}
    by_number: dict[str, list[str]] = {}
    for name in sorted(names):
        if (stamped := _STAMPED_NAME.fullmatch(name)) is not None:
            by_stamp.setdefault(stamped["stamp"], []).append(name)
        elif (numbered := _NUMBERED_NAME.fullmatch(name)) is not None:
            if name[:10] > TRANSITION_DAY:
                problems.append(
                    f"{name}: 전환일({TRANSITION_DAY}) 뒤의 일지인데 순번 꼴"
                    f"(`<날짜>-<NN>-`)이다. {_HOW_TO_NAME} {_HOW_TO_FIX}"
                )
            else:
                by_number.setdefault(numbered["number"], []).append(name)
        elif name not in BEFORE_NUMBERING:
            problems.append(
                f"{name}: 이름이 `<날짜>-<HHMM>-<슬러그>.md` 꼴이 아니다. {_HOW_TO_NAME}"
                f" {_HOW_TO_FIX}"
            )
    for stamp, group in by_stamp.items():
        if len(group) > 1:
            problems.append(
                f"{stamp}: `<날짜>-<HHMM>` 앞부분이 겹친다 — {', '.join(group)}. 같은 분에 만든"
                f" 일지 둘은 인용 `일지 {stamp}`이 둘로 풀린다. 늦게 병합되는 쪽이 분을 바꾼다."
                f" {_HOW_TO_NAME} {_HOW_TO_FIX}"
            )
    for number, group in by_number.items():
        if len(group) > 1 and frozenset(group) != SHARED_NUMBERS.get(number):
            problems.append(f"{number}: 순번이 겹친다 — {', '.join(group)}")
    return problems


def _journal_names() -> list[str]:
    return sorted(path.name for path in JOURNAL.glob("*.md"))


def test_일지_파일을_하나는_읽는다() -> None:
    """읽은 것이 없는데 겹침 0 으로 초록이 되는 것을 막는다(tests.md, 대기열 98)."""
    assert _journal_names()


def test_이_저장소의_일지_이름은_규칙을_지킨다() -> None:
    assert journal_name_problems(_journal_names()) == []


def test_새_꼴_이름을_받는다() -> None:
    names = ["2026-11-06-1432-a.md", "2026-11-06-1433-b.md", "2026-11-07-0930-c.md"]

    assert journal_name_problems(names) == []


def test_전환일_뒤_날짜의_순번_꼴을_잡는다() -> None:
    problems = journal_name_problems(["2026-11-08-01-late.md", f"{TRANSITION_DAY}-05-same-day.md"])

    assert len(problems) == 1
    assert problems[0].startswith("2026-11-08-01-late.md:")
    assert f"전환일({TRANSITION_DAY}) 뒤" in problems[0]
    assert "순번 꼴" in problems[0]


def test_전환일_뒤_순번_꼴의_실패_문장은_새_꼴과_짓는_명령과_원천과_할_일을_든다() -> None:
    (problem,) = journal_name_problems(["2026-11-08-01-late.md"])

    assert "<날짜>-<HHMM>-<슬러그>.md" in problem
    assert "date +%Y-%m-%d-%H%M" in problem
    assert "Get-Date -Format yyyy-MM-dd-HHmm" in problem
    assert "docs/constitution/operations.md" in problem
    assert "git mv" in problem
    assert "인용" in problem


def test_같은_분에_만든_일지_둘을_잡는다() -> None:
    names = ["2026-11-06-1432-a.md", "2026-11-06-1432-b.md", "2026-11-06-1433-c.md"]
    stamp = "2026-11-06-1432"

    (problem,) = journal_name_problems(names)

    assert problem.startswith("2026-11-06-1432:")
    assert "2026-11-06-1432-a.md, 2026-11-06-1432-b.md" in problem
    assert f"일지 {stamp}" in problem
    assert "git mv" in problem
    assert "date +%Y-%m-%d-%H%M" in problem


def test_다른_날의_같은_시각은_겹침이_아니다() -> None:
    assert journal_name_problems(["2026-11-06-1432-a.md", "2026-11-07-1432-a.md"]) == []


def test_옛_꼴의_같은_날_순번_겹침을_계속_잡는다() -> None:
    names = ["2026-10-03-01-a.md", "2026-10-03-01-b.md", "2026-10-03-02-c.md"]

    assert journal_name_problems(names) == [
        "2026-10-03-01: 순번이 겹친다 — 2026-10-03-01-a.md, 2026-10-03-01-b.md"
    ]


def test_옛_꼴의_다른_날_같은_순번은_겹침이_아니다() -> None:
    assert journal_name_problems(["2026-10-02-01-a.md", "2026-10-03-01-a.md"]) == []


def test_옛_꼴과_새_꼴의_앞부분은_서로_겹치지_않는다() -> None:
    """`2026-11-06-14-a.md`와 `2026-11-06-1432-b.md`는 인용 접두가 달라 따로 풀린다."""
    assert journal_name_problems(["2026-11-06-14-a.md", "2026-11-06-1432-b.md"]) == []


def test_이름이_새_꼴도_옛_꼴도_아닌_일지를_잡고_규약_전의_옛_이름만_지나간다() -> None:
    problems = journal_name_problems(["2026-10-03-a.md", "2026-09-21-first-slice.md"])

    assert len(problems) == 1
    assert problems[0].startswith("2026-10-03-a.md: 이름이 `<날짜>-<HHMM>-<슬러그>.md` 꼴이 아니다")


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
