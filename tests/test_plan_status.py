"""`.scratch/plan.md` 기능 행의 상태가 티켓의 `Status:`와 어긋나지 않는지의 판정자(harness 044).

`docs/agents/issue-tracker.md` 전체 계획 절은 기능 행의 `in-progress`를 "첫 티켓이 병합될 때",
`done`을 "마지막 티켓이 병합될 때" 사람이 바꾼다고 적는다. 이 규약이 문서에만 있어 세 번 어겨졌다.
첫 티켓(design-card-build 03)이 병합됐는데 행이 `todo`였고, 첫 티켓 둘(skill-plugin 01·02)이
병합됐는데 셋째 티켓의 PR에서야 행이 `in-progress`가 됐고, 마지막 티켓(skill-plugin 04)이
병합됐는데 행이 `in-progress`였다(대기열 546). 티켓은 PR을 열기 전에 `done`으로 바꾸므로 행을 같은
PR이 바꾸면 이 시험이 병합 커밋에서 초록이다.

보는 것은 둘이다. 하나라도 `done`인 티켓이 있으면 행이 `todo`가 아니다. 티켓이 모두 닫혔고
(`done` 또는 `wontfix`) `done`이 하나 이상이면 행이 `done`이다. 티켓의 `Status:` 값이나 줄이 읽히지
않는 것과 행의 칸이 표 머리와 맞지 않는 것도 읽지 못한 채 초록이 되지 않도록 문제로 센다.

막지 못하는 것: 관리자 우회 병합과 main 직접 푸시(그 뒤로는 main의 push CI와 뒤따르는 PR이 모두
빨갛다).
못 보는 것: 행이 티켓보다 앞선 경우. `done` 행에 열린 티켓이 있는 것은 정상이다. 기능 밖에서
제품 코드를 고치는 일은 그 기능 폴더의 새 티켓으로 더하고 행은 `done` 그대로 두기 때문이다
(`docs/agents/issue-tracker.md`). `in-progress` 행에 `done` 티켓이 없는 것도 보지 않는다. 세 사건이
모두 행이 티켓보다 뒤처진 쪽이었고, 행을 티켓보다 먼저 올리는 순서까지 막지는 않기 위해서다.
`plan.md`에 행이 없는 기능 폴더(하네스 기능은 티켓의 `Status:`가 상태다, ADR 0037)와 티켓 폴더가
없는 행도 보지 않는다. 행의 `Blocked by`와 슬라이스 번호도 보지 않는다.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRATCH = ROOT / ".scratch"
PLAN = SCRATCH / "plan.md"

# 표 칸의 구분자. 칸 안의 `\|`는 구분자가 아니다.
_CELL_SPLIT = re.compile(r"(?<!\\)\|")
# 값 뒤에 괄호 설명이 붙은 티켓이 있어(`done (2026-10-14 …)`) 줄 끝까지 맞추지 않고 첫 낱말을
# 읽는다.
_TICKET_STATUS = re.compile(r"^\*\*Status:\*\* (?P<value>\S+)", re.MULTILINE)

_ROW_STATUSES = frozenset({"todo", "in-progress", "done"})
_TICKET_STATUSES = frozenset({"ready-for-agent", "in-progress", "done", "wontfix"})
_CLOSED = frozenset({"done", "wontfix"})

_SLUG_HEADER = "기능(slug)"
_STATUS_HEADER = "Status"

# 기능 slug -> {티켓 파일 이름 -> `Status:` 값(줄이 없으면 None)}.
TicketStatuses = Mapping[str, Mapping[str, str | None]]
PlanTable = tuple[list[str] | None, list[tuple[int, list[str]]], list[str]]


def read_ticket_statuses(scratch: Path) -> dict[str, dict[str, str | None]]:
    """`.scratch/<slug>/issues/*.md` 의 첫 `**Status:**` 줄 값을 slug 별로 읽는다."""
    statuses: dict[str, dict[str, str | None]] = {}
    for issues in sorted(scratch.glob("*/issues")):
        tickets: dict[str, str | None] = {}
        for ticket in sorted(issues.glob("*.md")):
            match = _TICKET_STATUS.search(ticket.read_text(encoding="utf-8"))
            tickets[ticket.name] = match["value"] if match is not None else None
        statuses[issues.parent.name] = tickets
    return statuses


def _plan_table(plan_text: str) -> PlanTable:
    """표 머리, 그 아래 행(줄 번호, 칸들), 칸 수가 머리와 다른 행의 문제를 읽는다."""
    header: list[str] | None = None
    rows: list[tuple[int, list[str]]] = []
    problems: list[str] = []
    for number, line in enumerate(plan_text.splitlines(), start=1):
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in _CELL_SPLIT.split(line)[1:-1]]
        if header is None:
            if _SLUG_HEADER in cells and _STATUS_HEADER in cells:
                header = cells
            continue
        if all(cell and set(cell) <= {"-", ":"} for cell in cells):
            continue
        if len(cells) != len(header):
            problems.append(
                f"plan.md {number}번 줄: 칸이 {len(cells)}개인데 표 머리는 {len(header)}개다"
            )
            continue
        rows.append((number, cells))
    return header, rows, problems


def plan_status_problems(plan_text: str, tickets: TicketStatuses) -> list[str]:
    """행 상태와 티켓 `Status:` 가 어긋나거나 읽히지 않는 것."""
    header, rows, problems = _plan_table(plan_text)
    if header is None:
        return [f"plan.md: 표 머리({_SLUG_HEADER}, {_STATUS_HEADER})를 찾지 못했다"]
    slug_at = header.index(_SLUG_HEADER)
    status_at = header.index(_STATUS_HEADER)
    for number, cells in rows:
        slug, row_status = cells[slug_at], cells[status_at]
        where = f"{slug}(plan.md {number}번 줄)"
        if row_status not in _ROW_STATUSES:
            problems.append(f"{where}: 행 상태 `{row_status}`를 모른다")
            continue
        ticket_statuses = tickets.get(slug, {})
        for name, value in ticket_statuses.items():
            if value is None:
                problems.append(f"{where}: 티켓 {name}에 `**Status:**` 줄이 없다")
            elif value not in _TICKET_STATUSES:
                problems.append(f"{where}: 티켓 {name}의 상태 `{value}`를 모른다")
        values = [value for value in ticket_statuses.values() if value in _TICKET_STATUSES]
        done = values.count("done")
        if done and row_status == "todo":
            problems.append(f"{where}: 티켓 {done}/{len(values)}개가 done인데 행이 todo다")
        elif done and all(value in _CLOSED for value in values) and row_status != "done":
            problems.append(f"{where}: 티켓이 모두 닫혔는데 행이 {row_status}다")
    return problems


def _plan_slugs(plan_text: str) -> list[str]:
    header, rows, _ = _plan_table(plan_text)
    slug_at = header.index(_SLUG_HEADER) if header is not None else 0
    return [cells[slug_at] for _, cells in rows]


def _plan(*rows: tuple[str, str]) -> str:
    """슬라이스·slug·내용·막힘·상태 다섯 칸의 표. 내용 칸에 이스케이프한 `\\|`를 든다."""
    lines = [
        "| 슬라이스 | 기능(slug) | 내용 | Blocked by | Status |",
        "|---|---|---|---|---|",
    ]
    lines += [f"| 1 | {slug} | 발급자\\|sub 를 묶는다 | 없음 | {status} |" for slug, status in rows]
    return "\n".join(lines) + "\n"


def test_plan_md_행과_티켓을_하나는_읽는다() -> None:
    """읽은 것이 없는데 어긋남 0 으로 초록이 되는 것을 막는다(tests.md, 대기열 98)."""
    slugs = _plan_slugs(PLAN.read_text(encoding="utf-8"))
    tickets = read_ticket_statuses(SCRATCH)

    assert slugs, "plan.md 에서 읽은 행 없음"
    assert any(tickets.get(slug) for slug in slugs), f"티켓을 읽은 기능 없음: {sorted(tickets)}"
    assert any("done" in tickets.get(slug, {}).values() for slug in slugs), "done 티켓 없음"


def test_이_저장소의_plan_md_상태는_티켓과_어긋나지_않는다() -> None:
    plan_text = PLAN.read_text(encoding="utf-8")

    assert plan_status_problems(plan_text, read_ticket_statuses(SCRATCH)) == []


def test_첫_티켓_병합_뒤_todo로_남은_행을_잡는다() -> None:
    tickets = {"feat": {"01-a.md": "done", "02-b.md": "ready-for-agent"}}

    problems = plan_status_problems(_plan(("feat", "todo")), tickets)

    assert problems == ["feat(plan.md 3번 줄): 티켓 1/2개가 done인데 행이 todo다"]


def test_마지막_티켓_병합_뒤_in_progress로_남은_행을_잡는다() -> None:
    tickets = {"feat": {"01-a.md": "done", "02-b.md": "done"}}

    problems = plan_status_problems(_plan(("feat", "in-progress")), tickets)

    assert problems == ["feat(plan.md 3번 줄): 티켓이 모두 닫혔는데 행이 in-progress다"]


def test_wontfix_는_닫힌_것으로_세고_done_이_하나는_있어야_행을_요구한다() -> None:
    closed = {"feat": {"01-a.md": "done", "02-b.md": "wontfix"}}
    none_done = {"feat": {"01-a.md": "wontfix"}}

    assert plan_status_problems(_plan(("feat", "in-progress")), closed) == [
        "feat(plan.md 3번 줄): 티켓이 모두 닫혔는데 행이 in-progress다"
    ]
    assert plan_status_problems(_plan(("feat", "todo")), none_done) == []


def test_티켓의_Status_줄이_없거나_모르는_값을_잡는다() -> None:
    tickets = {"feat": {"01-a.md": None, "02-b.md": "finished", "03-c.md": "done"}}

    problems = plan_status_problems(_plan(("feat", "done")), tickets)

    assert problems == [
        "feat(plan.md 3번 줄): 티켓 01-a.md에 `**Status:**` 줄이 없다",
        "feat(plan.md 3번 줄): 티켓 02-b.md의 상태 `finished`를 모른다",
    ]


def test_행_상태를_모르거나_칸_수가_표_머리와_다른_행을_잡는다() -> None:
    text = _plan(("feat", "blocked")) + "| 2 | short | 칸이 모자라다 | todo |\n"

    problems = plan_status_problems(text, {})

    assert problems == [
        "plan.md 4번 줄: 칸이 4개인데 표 머리는 5개다",
        "feat(plan.md 3번 줄): 행 상태 `blocked`를 모른다",
    ]


def test_표_머리가_없는_plan_md를_잡는다() -> None:
    assert plan_status_problems("표 없는 글\n", {}) == [
        "plan.md: 표 머리(기능(slug), Status)를 찾지 못했다"
    ]


def test_칸이_모두_빈_행을_구분선으로_넘기지_않고_잡는다() -> None:
    text = _plan(("feat", "done")) + "| | | | | |\n"

    assert plan_status_problems(text, {}) == ["(plan.md 4번 줄): 행 상태 ``를 모른다"]


def test_어긋나지_않는_꼴은_지나간다() -> None:
    """done 행의 열린 티켓(issue-tracker.md: 기능 밖 제품 코드 티켓), 티켓 없는 todo 행,
    행이 티켓보다 앞선 in-progress 행 등."""
    tickets = {
        "later-ticket": {"01-a.md": "done", "02-b.md": "in-progress"},
        "started": {"01-a.md": "done", "02-b.md": "ready-for-agent"},
        "finished": {"01-a.md": "done"},
        "fresh": {"01-a.md": "ready-for-agent"},
        "ahead": {"01-a.md": "ready-for-agent"},
    }
    plan = _plan(
        ("later-ticket", "done"),
        ("started", "in-progress"),
        ("finished", "done"),
        ("fresh", "todo"),
        ("ahead", "in-progress"),
        ("no-folder", "todo"),
    )

    assert plan_status_problems(plan, tickets) == []


def test_이스케이프한_파이프가_든_행의_칸을_맞게_읽는다() -> None:
    """내용 칸의 `\\|` 때문에 칸이 밀리면 slug 와 상태를 엉뚱한 칸에서 읽는다."""
    assert _plan_slugs(_plan(("feat", "done"))) == ["feat"]
    tickets = {"feat": {"01-a.md": "done"}}

    assert plan_status_problems(_plan(("feat", "todo")), tickets) == [
        "feat(plan.md 3번 줄): 티켓 1/1개가 done인데 행이 todo다"
    ]


def test_티켓의_첫_Status_줄만_읽는다(tmp_path: Path) -> None:
    issues = tmp_path / "feat" / "issues"
    issues.mkdir(parents=True)
    first = "# 01\n\n**Status:** in-progress\n\n본문 **Status:** done\n\n**Status:** done\n"
    (issues / "01-a.md").write_text(first, encoding="utf-8")
    quoted = "# 02\n\n`**Status:** done` 를 인용한 글\n"
    annotated = "# 03\n\n**Status:** done (2026-10-14 설명)\n"
    (issues / "02-b.md").write_text(quoted, encoding="utf-8")
    (issues / "03-c.md").write_text(annotated, encoding="utf-8")

    assert read_ticket_statuses(tmp_path) == {
        "feat": {"01-a.md": "in-progress", "02-b.md": None, "03-c.md": "done"}
    }
