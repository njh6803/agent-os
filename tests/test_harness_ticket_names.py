"""harness 티켓 이름의 판정자. 번호는 전환 때까지만 있고, 같은 번호의 티켓은 둘이 아니다.

새 harness 티켓은 번호를 받지 않는다. 파일은 `.scratch/harness/issues/<slug>.md`, 첫 줄은
`# <slug>: <제목>`, 브랜치는 `chore/<slug>`다(`docs/agents/issue-tracker.md`, ADR 0045 결정 6).
옛 티켓 `NNN-<slug>.md`는 번호를 지킨다. 두 가지를 막는다. 전환 때의 마지막 번호
(`LAST_NUMBER`)보다 큰 번호로 시작하는 티켓과, 같은 번호를 든 옛 티켓 둘이다. 숫자 세 자리와
하이픈으로 시작하는 slug는 옛 꼴로 읽혀 이 시험에 걸린다. 일지의 같은 자리는
`tests/test_journal_names.py`가 본다.

`LAST_NUMBER`는 이 PR이 마지막으로 origin/main을 합친 때의 가장 큰 번호다. 병합하는 세션이 병합
직전에 main을 합치므로 대개 병합 때의 최대 번호와 같다. main을 다시 합칠 때 그 값으로 옮긴다.
상수보다 큰 번호가 main에 들어오면 이 시험이 빨개져 옮길 때를 알린다.

막지 못하는 것: 관리자 우회 병합과 main 직접 푸시. 그 뒤로는 main의 push CI와 뒤따르는 PR이
모두 이 테스트에서 빨갛다. 그때는 처음 본 세션이 상수를 옮기거나 그 파일 이름을 바꾸는 PR을 낸다.
못 보는 것: 번호로 시작하지 않는 이름이 slug 규칙(영어 소문자로 시작)을 지키는지, 하위 디렉터리,
번호의 빠짐과 차례, 기능 폴더(`.scratch/<slug>/issues/`)의 두 자리 번호.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ISSUES = ROOT / ".scratch" / "harness" / "issues"
_TICKET_NAME = re.compile(r"(?P<number>\d{3})-.+\.md")

# 이 PR이 마지막으로 origin/main을 합친 때의 가장 큰 티켓 번호. 이보다 큰 번호의 티켓은 빨갛다.
LAST_NUMBER = 45

_HOW_TO_NAME = (
    "새 하네스 티켓은 `<slug>.md`이고 브랜치는 `chore/<slug>`다(`docs/agents/issue-tracker.md`)."
    " 파일과 브랜치 이름에서 번호를 떼고, 세션 제목도 새 브랜치로 바꾼다."
)


def ticket_name_problems(names: Iterable[str]) -> list[str]:
    """전환 때의 마지막 번호보다 큰 번호로 시작하는 티켓, 같은 번호를 든 티켓 둘 이상."""
    problems: list[str] = []
    by_number: dict[str, list[str]] = {}
    for name in sorted(names):
        if (match := _TICKET_NAME.fullmatch(name)) is None:
            continue
        if int(match["number"]) > LAST_NUMBER:
            problems.append(
                f"{name}: 전환 때의 마지막 번호({LAST_NUMBER:03d})보다 큰 번호로 시작한다."
                f" {_HOW_TO_NAME}"
            )
        else:
            by_number.setdefault(match["number"], []).append(name)
    problems += [
        f"{number}: 번호가 겹친다 — {', '.join(group)}"
        for number, group in by_number.items()
        if len(group) > 1
    ]
    return problems


def _ticket_names() -> list[str]:
    return sorted(path.name for path in ISSUES.glob("*.md"))


def test_harness_티켓_파일을_하나는_읽는다() -> None:
    """읽은 것이 없는데 겹침 0 으로 초록이 되는 것을 막는다(tests.md, 대기열 98).

    파일이 있어도 번호 꼴에 맞는 이름이 없으면 판정이 본 것이 없으므로 그 꼴로 센다(PR #345
    CodeRabbit). 옛 티켓 45장은 번호를 지키므로 번호 꼴이 하나는 남는다.
    """
    names = _ticket_names()
    assert any(_TICKET_NAME.fullmatch(name) for name in names), f"번호 꼴의 티켓 없음: {names}"


def test_이_저장소의_harness_티켓_이름은_규칙을_지킨다() -> None:
    assert ticket_name_problems(_ticket_names()) == []


def test_상수는_이_저장소의_옛_티켓_가운데_가장_큰_번호다() -> None:
    """상수가 실제 최대보다 작으면 위 시험이 빨갛고, 크면 새 번호 티켓이 조용히 지난다."""
    numbers = [
        int(match["number"])
        for name in _ticket_names()
        if (match := _TICKET_NAME.fullmatch(name)) is not None
    ]

    assert max(numbers) == LAST_NUMBER


def test_같은_번호의_harness_티켓을_잡는다() -> None:
    names = ["001-alpha.md", "001-zulu.md", "002-other.md", "01-feature.md", "README.md"]

    assert ticket_name_problems(names) == ["001: 번호가 겹친다 — 001-alpha.md, 001-zulu.md"]


def test_마지막_번호보다_큰_번호의_티켓을_잡는다() -> None:
    names = [f"{LAST_NUMBER:03d}-last.md", f"{LAST_NUMBER + 1:03d}-late.md"]

    (problem,) = ticket_name_problems(names)

    assert problem.startswith(f"{LAST_NUMBER + 1:03d}-late.md:")
    assert f"마지막 번호({LAST_NUMBER:03d})" in problem


def test_번호_없는_slug_티켓은_지나간다() -> None:
    names = ["ci-python-runner-pin.md", "queue-split.md", "README.md", "002-other.md"]

    assert ticket_name_problems(names) == []


def test_번호_실패_문장은_새_꼴과_브랜치와_원천과_할_일을_든다() -> None:
    (problem,) = ticket_name_problems([f"{LAST_NUMBER + 1:03d}-late.md"])

    assert "<slug>.md" in problem
    assert "chore/<slug>" in problem
    assert "docs/agents/issue-tracker.md" in problem
    assert "번호를 떼고" in problem
    assert "세션 제목" in problem
