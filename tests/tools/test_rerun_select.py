"""`tools/rerun_select.py`: 다시 풀기의 과제 고르기.

티켓은 `.scratch/model-rerun/issues/05-task-selection.md`다. 값만 받는 함수는 지은 입력으로, 병합
기록 읽기는 squash 병합 꼴의 임시 저장소로, 숨은 시험 가르기와 이어지는 자리는 02의
`sort_candidate`를 작은 pytest 시험으로 돌려 본다(명세 Testing Decisions "과제 고르기와 숨은 시험
가르기").
"""

from __future__ import annotations

import ast
import json
import os
import random
import subprocess
import sys
from collections.abc import Callable
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from tools.check_md_tables import parse, problems_in
from tools.rerun_files import (
    LIST_MAIN,
    LIST_PILOT,
    TIER_LARGE,
    TIER_MEDIUM,
    TIER_PILOT,
    TIER_SMALL,
    read_task_list,
    write_task_list,
)
from tools.rerun_hidden import Dropped, Failure, Hidden, sort_candidate
from tools.run_hooks import REPO_LOCATION_VARS

from tools import rerun_select as sel

_KST = timezone(timedelta(hours=9))
_IN = datetime(2026, 10, 20, 12, tzinfo=_KST)  # 날짜 바닥 뒤
_BEFORE = datetime(2026, 10, 1, 12, tzinfo=_KST)  # 날짜 바닥 앞
_ROOT = Path(__file__).resolve().parents[2]


def _sha(n: int, salt: int) -> str:
    return f"{salt:02x}{n:038x}"


def _후보(
    n: int,
    *,
    size: int = 0,
    base_at: datetime = _IN,
    text: str | None = "",
    ticket: str | None = None,
    setup: tuple[str, ...] = sel.SETUP_FILES,
) -> sel.Candidate:
    """`n`번 후보. PR 은 100 + n 이고, 크기 지표가 `size`가 되도록 백틱 경로를 티켓 글에 붙인다."""
    body = None if text is None else text + "".join(f" `f{i}.py`" for i in range(size))
    return sel.Candidate(
        merge=_sha(n, 1),
        base=_sha(n, 2),
        merged_at=base_at + timedelta(hours=1),
        base_at=base_at,
        pr=100 + n,
        ticket=ticket or f".scratch/feat/issues/{n:02d}-t.md",
        ticket_text=body,
        setup_present=setup,
    )


def _행(
    n: int, *, cost: float = 10.0, post: float = 0.0, branch: str | None = None
) -> sel.BranchRow:
    return sel.BranchRow(
        branch=branch or f"feature/{n:02d}-t",
        prs=(100 + n,),
        cost=cost,
        cost_post_pr=post,
        top_model_effort="claude-opus-5-5/xhigh",
    )


# `n`번 후보마다 PR 100 + n 의 행이 하나씩 든 브랜치 표
_ROWS = tuple(_행(n) for n in range(1, 40))


def _검사(*candidates: sel.Candidate) -> list[sel.Checked]:
    return [sel.checked_of(c, _ROWS) for c in candidates]


def _숨은(n: int) -> Hidden:
    return Hidden(
        hidden_tests=tuple(f"tests/test_a.py::test_{i}" for i in range(n)),
        support_files=("tests/conftest.py",),
        dropped=(),
    )


class _가르기:
    """가짜 숨은 시험 가르기. 부른 M 을 적고, M 마다 정해 둔 결과(없으면 숨은 시험 셋)를 낸다."""

    def __init__(self, results: dict[str, Hidden | Failure] | None = None) -> None:
        self.calls: list[str] = []
        self.results = results or {}

    def __call__(self, base: str, merge: str) -> Hidden | Failure:
        self.calls.append(merge)
        return self.results.get(merge, _숨은(3))


# --- 푼 티켓 ---


def test_푼_티켓은_B_에서_done_이_아니고_M_에서_done_인_파일이고_여럿_가운데_그것만_고른다() -> (
    None
):
    changes = [
        sel.TicketChange(".scratch/a/issues/01-x.md", "in-progress", "done"),
        sel.TicketChange(".scratch/a/issues/02-y.md", "done", "done"),
        sel.TicketChange(".scratch/a/issues/03-z.md", "ready-for-agent", "in-progress"),
        sel.TicketChange(".scratch/a/issues/04-w.md", "done", None),
    ]

    assert sel.solved_tickets(changes) == (".scratch/a/issues/01-x.md",)


def test_B_에_없던_티켓_파일도_M_에서_done_이면_푼_티켓이고_done_으로_시작하는_값도_done_이다() -> (
    None
):
    changes = [
        sel.TicketChange(".scratch/a/issues/05-new.md", None, "done"),
        sel.TicketChange(".scratch/a/issues/06-v.md", "wontfix", "done(사람이"),
    ]

    assert sel.solved_tickets(changes) == (
        ".scratch/a/issues/05-new.md",
        ".scratch/a/issues/06-v.md",
    )


def test_과제_id_는_티켓_경로의_slug_와_두_자리_번호다() -> None:
    assert (
        sel.task_id_of(".scratch/end-user-channel/issues/04-llm-stream.md") == "end-user-channel-04"
    )
    with pytest.raises(sel.SelectError, match="티켓 경로가 아니다"):
        sel.task_id_of(".scratch/harness/issues/004-x.md")


# --- 싼 조건 ---


def test_B_에_티켓_파일이_없으면_빠진다() -> None:
    (got,) = _검사(_후보(1, text=None))

    assert got.reasons == ("B 에 티켓 파일이 없다",)


@pytest.mark.parametrize(
    ("rows", "reason"),
    [
        ([], "브랜치 표에 PR #101 의 행이 없다"),
        ([_행(1), _행(1, branch="feature/01-other")], "브랜치 표에 PR #101 의 행이 2개다"),
        ([_행(1, branch="chore/01-t")], "원래 브랜치 chore/01-t 가 feature/ 로 시작하지 않는다"),
    ],
)
def test_원래_브랜치의_행이_하나가_아니거나_feature_가_아니면_빠진다(
    rows: list[sel.BranchRow], reason: str
) -> None:
    got = sel.checked_of(_후보(1), rows)

    assert got.reasons == (reason,)
    assert got.origin is None
    assert got.cost is None


def test_M_제목에_PR_번호가_없으면_빠진다() -> None:
    (got,) = _검사(replace(_후보(1), pr=None))

    assert got.reasons == ("M 제목 끝에 PR 번호가 없다",)


@pytest.mark.parametrize("term", sel.EXTERNAL_TERMS)
def test_바깥_검증_낱말이_티켓_글에_있으면_빠지고_맞은_낱말을_든다(term: str) -> None:
    (got,) = _검사(_후보(1, text=f"수용 기준: {term} 를 돌린다"))

    assert got.terms == (term,)
    assert got.reasons == (f"바깥 검증 낱말에 걸렸다({term})",)


def test_바깥_검증_낱말은_대소문자를_가리지_않고_부정문에도_걸린다() -> None:
    (got,) = _검사(_후보(1, text="Playwright 는 쓰지 않고 `-M LLM`도 돌리지 않는다"))

    assert got.terms == ("-m llm", "playwright")


def test_파일_이름에_human_verification_이_들면_낱말이_아닌_까닭으로_빠진다() -> None:
    (got,) = _검사(_후보(1, ticket=".scratch/feat/issues/01-human-verification.md"))

    assert got.terms == ()
    assert got.reasons == ("파일 이름에 human-verification 가 든다",)


def test_낱말_목록_밖의_말로_적은_바깥_검증은_걸리지_않는다() -> None:
    """못 보는 것: "브라우저로 본다" 같은 말은 낱말 목록에 없어 남는다."""
    (got,) = _검사(_후보(1, text="수용 기준: 화면을 브라우저로 본다"))

    assert (got.terms, got.reasons) == ((), ())


@pytest.mark.parametrize(
    ("cost", "post", "kept"),
    [(80.0, 10.0, True), (70.0, 0.0, True), (90.0, 19.99, False), (70.01, 0.0, False)],
)
def test_PR_앞_비용은_cost_에서_cost_post_pr_를_뺀_값이고_70_달러를_넘으면_빠진다(
    cost: float, post: float, *, kept: bool
) -> None:
    got = sel.checked_of(_후보(1), [_행(1, cost=cost, post=post)])

    assert got.cost == round(cost - post, 4)
    assert (got.reasons == ()) is kept
    if not kept:
        assert got.reasons == (f"PR 앞 비용 ${cost - post:.2f} 가 $70 를 넘는다",)


def test_크기_지표는_B_의_티켓_글에서_백틱으로_싼_서로_다른_파일_경로의_수다() -> None:
    text = "`tools/a.py`와 `tools/a.py`, `docs/b.md`, `명령 줄`, `uv run`, `x.toolong7`"

    assert sel.size_of(text) == 2
    assert sel.size_of(None) == 0


def _정규식_인자(source: str, name: str) -> list[str]:
    """`<name> = re.compile("<글>")` 꼴의 대입에서 글을 모은다."""
    found: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Call):
            continue
        if not any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            continue
        first = node.value.args[0] if node.value.args else None
        if isinstance(first, ast.Constant) and isinstance(first.value, str):
            found.append(first.value)
    return found


def test_크기_지표의_정규식은_소급_측정의_BACKTICK_PATH_와_같다() -> None:
    source = (_ROOT / ".scratch/harness/probes/session_cost/collect.py").read_text(encoding="utf-8")

    assert _정규식_인자(source, "BACKTICK_PATH") == [sel.BACKTICK_PATH.pattern]


# --- 되살리기 ---


def test_낱말로만_빠진_후보를_되살리면_남고_표에_되살렸다고_까닭과_함께_적는다() -> None:
    checked = _검사(_후보(1, text="`-m llm`은 돌리지 않는다"))

    got = sel.revive(checked, {"feat-01": "부정문에 걸렸다"})

    assert got[0].reasons == ()
    rows = sel.build_rows(got, _가르기())
    assert rows[0].kept
    table = sel.render_table(rows, [], [])
    assert "| 날짜 안 | 남음 | — | -m llm(되살림: 부정문에 걸렸다) |" in table


@pytest.mark.parametrize(
    ("candidate", "rows", "wanted", "message"),
    [
        (
            _후보(1, text="`-m llm`"),
            [_행(1, cost=80.0)],
            "feat-01",
            "feat-01: 다른 조건으로도 빠졌다(PR 앞 비용 $80.00 가 $70 를 넘는다)",
        ),
        (
            _후보(1, text="`-m llm`", ticket=".scratch/feat/issues/01-human-verification.md"),
            [_행(1)],
            "feat-01",
            "feat-01: 다른 조건으로도 빠졌다(파일 이름에 human-verification 가 든다)",
        ),
        (_후보(1), [_행(1)], "feat-01", "feat-01: 바깥 검증 낱말에 걸리지 않았다"),
        (_후보(1), [_행(1)], "feat-09", "feat-09: 후보 0개에 맞는다(하나여야 한다)"),
    ],
)
def test_다른_조건으로_빠졌거나_낱말에_걸리지_않은_후보를_되살리려_하면_오류다(
    candidate: sel.Candidate, rows: list[sel.BranchRow], wanted: str, message: str
) -> None:
    checked = [sel.checked_of(candidate, rows)]

    with pytest.raises(sel.SelectError, match="되살릴 목록을 들이지 못했다") as caught:
        sel.revive(checked, {wanted: "까닭"})

    assert message in str(caught.value)


def test_되살릴_목록은_과제_id_에서_까닭으로_가는_객체이고_까닭이_비면_오류다() -> None:
    assert sel.parse_revive('{"feat-01": "까닭"}') == {"feat-01": "까닭"}
    with pytest.raises(sel.SelectError, match="feat-01 에 까닭이 없다"):
        sel.parse_revive('{"feat-01": " "}')
    with pytest.raises(sel.SelectError, match="객체다"):
        sel.parse_revive('["feat-01"]')


# --- 날짜, 숨은 시험, 거슬러 채우기 ---


def test_숨은_시험이_셋보다_적거나_가르지_못하면_빠지고_싼_조건에서_빠진_후보는_가르지_않는다() -> (
    None
):
    checked = _검사(_후보(1), _후보(2), _후보(3), _후보(4, text="playwright"))
    가르기 = _가르기({_sha(2, 1): _숨은(2), _sha(3, 1): Failure("pytest 가 시간 제한을 넘겼다")})

    rows = {r.checked.candidate.task_id: r for r in sel.build_rows(checked, 가르기, need=1)}

    assert rows["feat-01"].kept
    assert rows["feat-02"].reasons == ("숨은 시험이 2개라 3개보다 적다",)
    assert rows["feat-03"].reasons == ("숨은 시험을 가르지 못했다: pytest 가 시간 제한을 넘겼다",)
    assert rows["feat-04"].hidden is None
    assert _sha(4, 1) not in 가르기.calls


def test_날짜_안이_모자라면_앞의_후보를_M_이_늦은_것부터_하나씩_더하고_나머지는_닿지_않는다() -> (
    None
):
    checked = _검사(
        _후보(
            10, base_at=_BEFORE + timedelta(days=4), text="playwright"
        ),  # 가장 늦고 낱말로 빠진다
        _후보(11, base_at=_BEFORE + timedelta(days=3)),
        _후보(12, base_at=_BEFORE + timedelta(days=2)),
        _후보(13, base_at=_BEFORE + timedelta(days=1)),
        _후보(1),
        _후보(2),
    )
    가르기 = _가르기({_sha(11, 1): _숨은(1)})

    rows = sel.build_rows(checked, 가르기, need=3)

    places = {r.checked.candidate.task_id: (r.place, r.kept) for r in rows}
    assert places == {
        "feat-01": (sel.Place.IN_WINDOW, True),
        "feat-02": (sel.Place.IN_WINDOW, True),
        "feat-10": (sel.Place.BACKFILL, False),
        "feat-11": (sel.Place.BACKFILL, False),
        "feat-12": (sel.Place.BACKFILL, True),
        "feat-13": (sel.Place.UNREACHED, False),
    }
    assert 가르기.calls == [_sha(2, 1), _sha(1, 1), _sha(11, 1), _sha(12, 1)]
    unreached = next(r for r in rows if r.place is sel.Place.UNREACHED)
    assert unreached.reasons == ("B 가 2026-10-12 앞이고 거슬러 채우기가 닿지 않았다",)
    order = [r.checked.candidate.task_id for r in rows]
    assert order == ["feat-02", "feat-01", "feat-10", "feat-11", "feat-12", "feat-13"]


def test_날짜_안의_후보가_문턱을_채우면_그_앞의_후보는_가르지_않는다() -> None:
    checked = _검사(_후보(1), _후보(2, base_at=_BEFORE))
    가르기 = _가르기()

    rows = sel.build_rows(checked, 가르기, need=1)

    assert [r.place for r in rows] == [sel.Place.IN_WINDOW, sel.Place.UNREACHED]
    assert 가르기.calls == [_sha(1, 1)]


def test_닿지_않은_행에는_날짜의_까닭_뒤에_싼_조건의_까닭도_적는다() -> None:
    checked = _검사(_후보(1), _후보(2, base_at=_BEFORE, text="playwright"))

    rows = sel.build_rows(checked, _가르기(), need=1)

    assert rows[1].reasons == (
        "B 가 2026-10-12 앞이고 거슬러 채우기가 닿지 않았다",
        "바깥 검증 낱말에 걸렸다(playwright)",
    )


def test_날짜_바닥은_KST_2026_10_12_0시이고_B_의_커밋_시각으로_본다() -> None:
    checked = _검사(
        _후보(1, base_at=sel.DATE_FLOOR),
        _후보(2, base_at=sel.DATE_FLOOR - timedelta(seconds=1)),
    )

    rows = sel.build_rows(checked, _가르기(), need=1)

    assert sel.DATE_FLOOR == datetime(2026, 10, 12, tzinfo=_KST)
    assert [r.place for r in rows] == [sel.Place.IN_WINDOW, sel.Place.UNREACHED]


# --- 후보 표 ---


def test_빠진_노드는_조건과_까닭으로_묶어_세고_묶음이_많으면_앞의_여섯과_남은_수다() -> None:
    dropped = [
        Dropped("a::t1", 2, "AttributeError"),
        Dropped("a::t2", 2, "AttributeError"),
        Dropped("a::t3", 1, "M 첫째 실행: 실패"),
        Dropped("a::t4", 3, "이름 'new_name'"),
    ]

    assert sel.dropped_summary(dropped) == (
        "조건 1 M 첫째 실행: 실패 ×1; 조건 2 AttributeError ×2; 조건 3 이름 'new_name' ×1"
    )
    many = [Dropped(f"a::t{i}", 3, f"이름 'n{i}'") for i in range(8)]
    assert sel.dropped_summary(many).endswith("; 외 2가지")
    assert sel.dropped_summary(many).count("×1") == 6


def test_후보_표는_후보마다_한_행이고_끝에_세_수를_적으며_GFM_표로_깨지지_않는다() -> None:
    hidden = Hidden(
        hidden_tests=("tests/test_a.py::test_1",) * 3,
        support_files=(),
        dropped=(Dropped("tests/test_a.py::test_x", 3, "문자열 'a|b'"),),
    )
    checked = _검사(
        _후보(1),
        _후보(2, base_at=_BEFORE, text="사람이 확인"),
        _후보(3, base_at=_BEFORE - timedelta(days=1), setup=("web/package.json",)),
        _후보(4, base_at=_BEFORE - timedelta(days=2)),
    )
    rows = sel.build_rows(checked, _가르기({_sha(1, 1): hidden}), need=2)

    table = sel.render_table(rows, ["머리 줄"], ["#7"])

    assert problems_in(table) == []
    tables, _ = parse(table)
    assert len(tables) == 1
    lines = table.splitlines()
    head = next(line for line in lines if line.startswith("| 과제 id"))
    for column in (
        "PR",
        "B 시각",
        "원래 브랜치",
        "자리",
        "빠진 까닭",
        "바깥 검증 낱말",
        "PR 앞 비용",
    ):
        assert f"| {column} |" in head
    assert head.endswith("| B 의 `web/package.json` | B 의 `tools/run_checks.py` |")
    body = {
        line.split(" | ")[0].removeprefix("| "): line
        for line in lines
        if line.startswith("| feat-")
    }
    assert list(body) == ["feat-01", "feat-02", "feat-03", "feat-04"]
    assert "| #101 | " in body["feat-01"]
    assert "| 날짜 안 | 남음 | — |" in body["feat-01"]
    assert "| 3 | 조건 3 문자열 'a\\|b' ×1 | 있음 | 있음 |" in body["feat-01"]
    assert (
        "| 거슬러 채움 | 빠짐 | 바깥 검증 낱말에 걸렸다(사람이 확인) | 사람이 확인 |"
        in body["feat-02"]
    )
    assert "| 거슬러 채움 | 남음 | — |" in body["feat-03"]
    assert body["feat-03"].endswith("| 있음 | 없음 |")
    assert "| 닿지 않음 | 빠짐 |" in body["feat-04"]
    assert lines[-4:] == [
        "- B 가 2026-10-12 이후인 남은 후보: 1개(문턱 12개)",
        "- 거슬러 채워 남은 후보: 1개",
        "- 거슬러 채워 남은 후보 가운데 B 에 준비·게이트 파일(`web/package.json`, "
        "`tools/run_checks.py`) 가운데 하나라도 없는 것: 1개",
        "- 푼 티켓 파일이 둘 이상이라 후보가 아닌 병합 커밋: #7",
    ]


def test_칸의_줄바꿈과_줄_구분_문자는_빈칸이_되고_파이프는_감싼다() -> None:
    branch = "feature/a\nb\r\nc" + chr(0x2028) + "d|e"
    checked = [sel.checked_of(_후보(1), [_행(1, branch=branch)])]

    table = sel.render_table(sel.build_rows(checked, _가르기()), [], [])

    assert "| feature/a b c d\\|e | 날짜 안 |" in table
    assert problems_in(table) == []


# --- 고르기 ---


def _남은(sizes: list[int]) -> tuple[sel.Pick, ...]:
    """크기 지표가 `sizes`인 남은 후보. id 는 차례대로 feat-01, feat-02, …"""
    checked = _검사(*(_후보(i + 1, size=s) for i, s in enumerate(sizes)))
    return sel.picks_of(sel.build_rows(checked, _가르기(), need=1))


def _섞은[T](items: list[T], seed: int) -> list[T]:
    out = list(items)
    random.Random(seed).shuffle(out)
    return out


def _ids(picks: tuple[sel.Pick, ...] | list[sel.Pick]) -> list[str]:
    return [p.checked.candidate.task_id for p in picks]


def test_남은_후보는_크기_지표_순이고_동률은_M_의_해시_순이다() -> None:
    assert _ids(_남은([5, 1, 3, 1])) == ["feat-02", "feat-04", "feat-03", "feat-01"]


def test_파일럿은_아래_삼분의_일을_씨앗_1로_섞어_앞에서_셋이고_갈래_계획이_정해져_있다() -> None:
    picks = _남은(list(range(12)))

    got = sel.pick_pilot(picks)

    assert got.kind == LIST_PILOT
    assert [t.task_id for t in got.tasks] == _섞은(_ids(picks[:4]), 1)[:3]
    assert [t.arm_plan for t in got.tasks] == [("A", "A"), ("A", "A"), ("E",)]
    assert [(t.order, t.tier, t.pilot) for t in got.tasks] == [
        (i, TIER_PILOT, True) for i in range(3)
    ]
    assert sel.pick_pilot(picks) == got


def test_아래_삼분의_일이_셋보다_적으면_파일럿을_고르지_못한다() -> None:
    with pytest.raises(sel.SelectError, match="아래 삼분의 일이 2개라 파일럿 3개를 고르지 못한다"):
        sel.pick_pilot(_남은(list(range(8))))


def test_본_측정은_파일럿을_뺀_후보를_층_셋으로_잘라_씨앗으로_고르고_엇갈린_차례로_둔다() -> None:
    picks = _남은(list(range(21)))  # 파일럿을 빼면 층마다 여섯이라, 씨앗이 고를 것을 가른다
    pilot = sel.pick_pilot(picks)
    used = {t.task_id for t in pilot.tasks}
    rest = [i for i in _ids(picks) if i not in used]

    got = sel.pick_main(picks, pilot)

    small = _섞은(rest[0:6], 2)
    medium = _섞은(rest[6:12], 3)
    large = _섞은(rest[12:18], 4)
    assert got.kind == LIST_MAIN
    assert [(t.task_id, t.tier) for t in got.tasks] == [
        (small[0], TIER_SMALL),
        (medium[0], TIER_MEDIUM),
        (large[0], TIER_LARGE),
        (small[1], TIER_SMALL),
        (medium[1], TIER_MEDIUM),
        (large[1], TIER_LARGE),
        (small[2], TIER_SMALL),
        (medium[2], TIER_MEDIUM),
    ]
    assert [t.order for t in got.tasks] == list(range(8))
    assert not any(t.pilot for t in got.tasks)
    assert sel.pick_main(picks, pilot) == got


def test_본_측정의_큰_층은_삼분의_일로_나누고_남은_후보를_모두_받는다() -> None:
    picks = _남은(list(range(14)))  # 파일럿을 빼면 열하나라 작은·중간 층이 셋씩, 큰 층이 다섯이다
    pilot = sel.pick_pilot(picks)
    used = {t.task_id for t in pilot.tasks}
    rest = [i for i in _ids(picks) if i not in used]

    got = sel.pick_main(picks, pilot)

    assert len(rest) == 11
    assert [t.task_id for t in got.tasks if t.tier == TIER_LARGE] == _섞은(rest[6:11], 4)[:2]


def test_본_측정의_갈래_계획은_실행_차례마다_씨앗_100_더하기_i_로_다섯_갈래를_섞은_것이다() -> None:
    picks = _남은(list(range(12)))

    got = sel.pick_main(picks, sel.pick_pilot(picks))

    for i, task in enumerate(got.tasks):
        assert task.arm_plan == tuple(_섞은(["A", "B", "C", "D", "E"], 100 + i))
    assert len({t.arm_plan for t in got.tasks}) > 1


def test_후보가_늘어도_본_측정은_받은_파일럿_과제를_빼고_파일럿을_다시_고르지_않는다() -> None:
    pilot = sel.pick_pilot(_남은(list(range(12))))
    더한 = _남은([*range(12), 0, 0, 1])  # 작은 후보가 늘어 아래 삼분의 일이 바뀐다

    got = sel.pick_main(더한, pilot)

    used = {t.task_id for t in pilot.tasks}
    assert sel.pick_pilot(더한) != pilot
    assert not used & {t.task_id for t in got.tasks}
    rest = [i for i in _ids(더한) if i not in used]
    assert len(rest) == 12
    assert [t.task_id for t in got.tasks if t.tier == TIER_SMALL] == _섞은(rest[:4], 2)[:3]


def test_파일럿을_뺀_층이_모자라면_본_측정을_고르지_못한다() -> None:
    picks = _남은(list(range(10)))

    with pytest.raises(sel.SelectError, match="작은 층이 2개라 3개를 고르지 못한다"):
        sel.pick_main(picks, sel.pick_pilot(picks))


def test_본_측정에_파일럿이_아닌_목록을_주면_오류다() -> None:
    picks = _남은(list(range(12)))
    not_pilot = replace(sel.pick_pilot(picks), kind=LIST_MAIN)

    with pytest.raises(sel.SelectError, match="파일럿 목록이 아니다"):
        sel.pick_main(picks, not_pilot)


def test_남은_후보의_과제_id_가_겹치면_고르지_않는다() -> None:
    a = _후보(1)
    checked = _검사(a, replace(_후보(2), ticket=a.ticket))
    rows = sel.build_rows(checked, _가르기(), need=1)

    with pytest.raises(sel.SelectError, match="과제 id 가 겹친다: feat-01"):
        sel.picks_of(rows)


@pytest.mark.parametrize(("cost", "cap"), [(10.0, 40.0), (13.34, 40.02), (20.0, 60.0)])
def test_회차_상한은_PR_앞_비용의_세_배와_40_달러_가운데_큰_값이다(cost: float, cap: float) -> None:
    assert sel.round_cap(cost) == cap


def test_고른_목록은_과제_목록의_꼴로_쓰고_다시_읽으면_같다(tmp_path: Path) -> None:
    pilot = sel.pick_pilot(_남은(list(range(12))))
    path = tmp_path / "pilot.json"

    write_task_list(path, pilot)

    assert read_task_list(path) == pilot
    task = pilot.tasks[0]
    number = task.task_id.removeprefix("feat-")
    assert task.ticket == f".scratch/feat/issues/{number}-t.md"
    assert task.branch == f"feature/{number}-t"
    assert (task.pr_cost_usd, task.round_cap_usd) == (10.0, 40.0)
    assert task.hidden_tests == _숨은(3).hidden_tests
    assert task.support_files == ("tests/conftest.py",)
    assert task.original_model_effort == "claude-opus-5-5/xhigh"


def test_고르기의_조건과_씨앗은_명세의_값이다() -> None:
    assert (sel.MIN_CANDIDATES, sel.MIN_HIDDEN, sel.COST_LIMIT_USD) == (12, 3, 70.0)
    assert sel.EXTERNAL_TERMS == (
        "-m llm",
        "playwright",
        "pnpm -C web visual",
        "사진 비교",
        "Claude Design",
        "사람이 확인",
    )
    assert sel.EXTERNAL_NAME == "human-verification"
    assert (sel.SEED_PILOT, sel.SEED_SMALL, sel.SEED_MEDIUM, sel.SEED_LARGE) == (1, 2, 3, 4)
    assert sel.ARM_SEED_BASE == 100
    assert sel.MAIN_COUNTS == (3, 3, 2)
    assert (sel.CAP_MULTIPLIER, sel.CAP_FLOOR_USD) == (3.0, 40.0)
    assert sel.SETUP_FILES == ("web/package.json", "tools/run_checks.py")


# --- 브랜치 표 ---


def test_브랜치_표의_행에서_가지와_PR_과_비용과_모델_레벨을_읽는다() -> None:
    row = {
        "branch": "feature/01-t",
        "prs": [101, 99],
        "cost": 12.5,
        "cost_post_pr": 2,
        "top_model_effort": None,
        "kind": "구현",
    }

    got = sel.parse_branches(json.dumps({"meta": {}, "branches": [row]}))

    assert got == (sel.BranchRow("feature/01-t", (101, 99), 12.5, 2.0, None),)


@pytest.mark.parametrize(
    ("row", "message"),
    [
        ({"branch": "b", "prs": ["1"], "cost": 1, "cost_post_pr": 0}, "prs 가 정수 목록이 아니다"),
        ({"branch": "b", "prs": [1], "cost": True, "cost_post_pr": 0}, "수가 아니다"),
        ({"branch": "", "prs": [1], "cost": 1, "cost_post_pr": 0}, "branch 가 글이 아니다"),
        (
            {"branch": "b", "prs": [1], "cost": 1, "cost_post_pr": 0, "top_model_effort": 3},
            "top_model_effort 가 글이나 null 이 아니다",
        ),
    ],
)
def test_브랜치_표의_꼴이_다르면_오류다(row: dict[str, object], message: str) -> None:
    with pytest.raises(sel.SelectError, match=message):
        sel.parse_branches(json.dumps({"branches": [row]}))


# --- 바깥 층: 임시 저장소 ---

_IDENTITY = ("-c", "user.name=t", "-c", "user.email=t@example.com")
_TIMEOUT = 60
_T = datetime(2026, 10, 20, 9, tzinfo=_KST)


def _env(stamp: datetime | None) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in REPO_LOCATION_VARS}
    if stamp is not None:
        env["GIT_AUTHOR_DATE"] = env["GIT_COMMITTER_DATE"] = stamp.isoformat()
    return env


def _git(repo: Path, *args: str, when: datetime | None = None) -> str:
    done = subprocess.run(
        ["git", "-C", str(repo), *_IDENTITY, *args],
        capture_output=True,
        check=True,
        env=_env(when),
        timeout=_TIMEOUT,
    )
    return done.stdout.decode("utf-8").strip()


def _커밋(repo: Path, files: dict[str, str], message: str, when: datetime) -> str:
    for rel, text in files.items():
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", message, when=when)
    return _git(repo, "rev-parse", "HEAD")


def _티켓(status: str, body: str = "") -> str:
    return f"# 티켓\n\n**Status:** {status}\n\n- [ ] `Status:` 줄을 done 으로 바꾼다\n{body}"


def _저장소(path: Path) -> Path:
    path.mkdir()
    _git(path, "init", "-q", "-b", "main")
    return path


def _브랜치_표(path: Path, rows: list[dict[str, object]]) -> Path:
    path.write_text(json.dumps({"branches": rows}), encoding="utf-8")
    return path


def test_병합_기록에서_푼_티켓이_하나인_squash_커밋을_후보로_찾는다(tmp_path: Path) -> None:
    repo = _저장소(tmp_path / "repo")
    a, b, c, d, e = (f".scratch/a/issues/0{i}-t.md" for i in range(1, 6))
    harness = ".scratch/harness/issues/001-h.md"
    bom = ".scratch/a/issues/08-t.md"  # BOM 뒤 첫 줄이 Status 다
    준비 = _티켓("ready-for-agent")
    c0 = _커밋(
        repo,
        {
            a: _티켓("ready-for-agent", "`x.py`"),
            b: 준비,
            c: _티켓("done"),
            d: 준비,
            harness: 준비,
            bom: chr(0xFEFF) + "**Status:** ready-for-agent\n",
        },
        "docs: 티켓 (#1)",
        _T,
    )
    c1 = _커밋(
        repo,
        {a: _티켓("done", "`x.py`"), b: _티켓("in-progress")},
        "feat: (#77) 를 잇는다 (zzz 09) (#2)",  # 못 보는 것: 꼬리의 (<slug> <NN>)는 보지 않는다
        _T + timedelta(hours=1),
    )
    _커밋(
        repo,
        {c: _티켓("done", "고침"), "web/package.json": "{}\n"},
        "fix: done 에서 done (#3)",
        _T + timedelta(hours=2),
    )
    c3 = _커밋(repo, {e: _티켓("done")}, "feat: 새 티켓 (#4)", _T + timedelta(hours=3))
    _커밋(repo, {b: _티켓("done"), d: _티켓("done")}, "feat: 둘 (#5)", _T + timedelta(hours=4))
    _커밋(repo, {harness: _티켓("done")}, "chore: 하네스 (#6)", _T + timedelta(hours=5))
    _커밋(
        repo,
        {".scratch/a/issues/06-t.md": _티켓("done")},
        "feat: 번호 없는 제목",
        _T + timedelta(hours=6),
    )
    # 못 보는 것: 티켓 파일 밖에서 끝난 일(티켓 없는 PR)은 후보가 아니다
    _커밋(repo, {"README.md": "고침\n"}, "chore: 티켓 없는 PR (#7)", _T + timedelta(hours=7))
    _커밋(
        repo, {bom: chr(0xFEFF) + "**Status:** done\n"}, "feat: BOM (#8)", _T + timedelta(hours=8)
    )
    # 첫 부모 줄 밖의 곁가지 커밋이 푼 티켓은 후보가 아니다
    _git(repo, "checkout", "-q", "-b", "side")
    _커밋(
        repo, {".scratch/a/issues/07-t.md": _티켓("done")}, "feat: 곁가지", _T + timedelta(hours=9)
    )
    _git(repo, "checkout", "-q", "main")
    _git(repo, "merge", "-q", "--no-ff", "-m", "곁가지 (#9)", "side", when=_T + timedelta(hours=10))

    got = sel.list_candidates(repo, "HEAD")

    assert got.ambiguous == ("#5",)
    by_id = {x.task_id: x for x in got.candidates}
    assert set(by_id) == {"a-01", "a-05", "a-06", "a-08"}
    one = by_id["a-01"]
    assert (one.merge, one.base, one.pr, one.ticket) == (c1, c0, 2, a)
    assert one.ticket_text is not None
    assert sel.size_of(one.ticket_text) == 1
    assert (one.base_at, one.merged_at) == (_T, _T + timedelta(hours=1))
    assert one.setup_present == ()
    new = by_id["a-05"]
    assert (new.merge, new.ticket_text) == (c3, None)
    assert new.setup_present == ("web/package.json",)
    assert by_id["a-06"].pr is None


def _한_후보_저장소(path: Path) -> Path:
    repo = _저장소(path)
    _커밋(repo, {".scratch/a/issues/01-t.md": _티켓("ready-for-agent")}, "docs: 티켓 (#1)", _T)
    _커밋(
        repo,
        {".scratch/a/issues/01-t.md": _티켓("done")},
        "feat: 푼다 (#2)",
        _T + timedelta(hours=1),
    )
    return repo


def test_고르기_명령은_후보가_모두_싼_조건에서_빠지면_표를_쓰고_목록_없이_1로_끝난다(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _한_후보_저장소(tmp_path / "repo")
    branches = _브랜치_표(tmp_path / "branches.json", [])
    table, out = tmp_path / "후보.md", tmp_path / "pilot.json"
    가르기 = _가르기()
    argv = ["pilot", "--branches", str(branches), "--table", str(table), "--out", str(out)]

    code = sel.main(
        [*argv, "--repo", str(repo), "--rev", "HEAD"], make_sorter=lambda _r, _o: 가르기
    )

    assert code == 1
    text = table.read_text(encoding="utf-8")
    assert "되살릴 목록은 없다." in text
    assert "| a-01 | #2 |" in text
    assert "브랜치 표에 PR #2 의 행이 없다" in text
    assert not out.exists()
    assert 가르기.calls == []
    assert "목록을 짓지 못했다: 남은 후보 0개의 아래 삼분의 일이 0개" in capsys.readouterr().err


def test_후보_표_머리는_입력_파일을_저장소_기준_경로로_적고_저장소_밖이면_이름만_적는다(
    tmp_path: Path,
) -> None:
    repo = _한_후보_저장소(tmp_path / "repo")
    (repo / "probes").mkdir()
    branches = _브랜치_표(repo / "probes" / "branches.json", [])
    revive = tmp_path / "밖" / "revive.json"
    revive.parent.mkdir()
    revive.write_text("{}", encoding="utf-8")
    table = tmp_path / "후보.md"
    argv = ["table", "--branches", str(branches), "--revive", str(revive), "--table", str(table)]

    code = sel.main(
        [*argv, "--repo", str(repo), "--rev", "HEAD"], make_sorter=lambda _r, _o: _가르기()
    )

    assert code == 0
    text = table.read_text(encoding="utf-8")
    assert "브랜치 표는 `probes/branches.json`(" in text
    assert "되살릴 목록은 `revive.json`다." in text
    assert tmp_path.name not in text


def test_되살릴_목록이_틀리면_표를_쓰지_않고_2로_끝난다(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _한_후보_저장소(tmp_path / "repo")
    branches = _브랜치_표(tmp_path / "branches.json", [])
    revive = tmp_path / "revive.json"
    revive.write_text(json.dumps({"a-01": "까닭"}), encoding="utf-8")
    table = tmp_path / "후보.md"
    argv = ["table", "--branches", str(branches), "--revive", str(revive), "--table", str(table)]

    code = sel.main(
        [*argv, "--repo", str(repo), "--rev", "HEAD"], make_sorter=lambda _r, _o: _가르기()
    )

    assert code == 2
    assert not table.exists()
    assert "a-01: 바깥 검증 낱말에 걸리지 않았다" in capsys.readouterr().err


def test_본_측정_명령에_읽지_못할_파일럿_목록을_주면_2로_끝난다(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _한_후보_저장소(tmp_path / "repo")
    branches = _브랜치_표(tmp_path / "branches.json", [])
    pilot = tmp_path / "pilot.json"
    pilot.write_text("{}", encoding="utf-8")
    table, out = tmp_path / "후보.md", tmp_path / "main.json"
    argv = ["main", "--branches", str(branches), "--table", str(table), "--out", str(out)]

    code = sel.main(
        [*argv, "--pilot", str(pilot), "--repo", str(repo), "--rev", "HEAD"],
        make_sorter=lambda _r, _o: _가르기(),
    )

    assert code == 2
    assert not table.exists()
    assert "파일럿 목록" in capsys.readouterr().err


def test_병합_기록은_저장소를_가리키는_GIT_환경을_벗기고_읽는다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """워크트리에서 커밋하면 pre-commit 아래의 git 이 `GIT_DIR` 을
    내보낸다(`.claude/rules/tools.md`)."""
    repo = _한_후보_저장소(tmp_path / "repo")
    엉뚱한 = _저장소(tmp_path / "엉뚱한")
    for name in REPO_LOCATION_VARS:
        monkeypatch.setenv(name, str(엉뚱한 / ".git" / name))
    monkeypatch.setenv("GIT_DIR", str(엉뚱한 / ".git"))

    got = sel.list_candidates(repo, "HEAD")

    assert [c.task_id for c in got.candidates] == ["a-01"]


def test_git_호출이_시간_제한을_넘기면_고르기의_오류다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _한_후보_저장소(tmp_path / "repo")
    monkeypatch.setattr(sel, "GIT_TIMEOUT", 1e-6)

    with pytest.raises(sel.SelectError, match=r"시간 제한\(1e-06초\)을 넘겼다"):
        sel.list_candidates(repo, "HEAD")


_한_후보_행: dict[str, object] = {
    "branch": "feature/01-t",
    "prs": [2],
    "cost": 5.0,
    "cost_post_pr": 0.0,
    "top_model_effort": None,
}


@pytest.mark.parametrize("command", ["table", "pilot"])
def test_출력_자리의_폴더가_없으면_숨은_시험을_가르기_전에_2로_끝난다(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], command: str
) -> None:
    repo = _한_후보_저장소(tmp_path / "repo")
    branches = _브랜치_표(tmp_path / "branches.json", [_한_후보_행])
    없는 = tmp_path / "없는"
    table = (없는 if command == "table" else tmp_path) / "후보.md"
    argv = [command, "--branches", str(branches), "--table", str(table)]
    if command == "pilot":
        argv += ["--out", str(없는 / "pilot.json")]
    가르기 = _가르기()

    code = sel.main(
        [*argv, "--repo", str(repo), "--rev", "HEAD"], make_sorter=lambda _r, _o: 가르기
    )

    assert code == 2
    assert 가르기.calls == []
    assert "의 폴더가 없다" in capsys.readouterr().err


def test_후보_표를_쓰지_못하면_2로_끝난다(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    repo = _한_후보_저장소(tmp_path / "repo")
    branches = _브랜치_표(tmp_path / "branches.json", [])
    table = tmp_path / "후보.md"
    table.mkdir()  # 폴더라 파일로 쓰지 못한다
    argv = ["table", "--branches", str(branches), "--table", str(table)]

    code = sel.main(
        [*argv, "--repo", str(repo), "--rev", "HEAD"], make_sorter=lambda _r, _o: _가르기()
    )

    assert code == 2
    assert f"후보 표 {table} 를 쓰지 못했다" in capsys.readouterr().err


def _여러_후보_저장소(path: Path, n: int) -> Path:
    """티켓 `n`개를 하나씩 푼 저장소. `i`번 티켓의 크기 지표는 `i`이고 PR 은 100 + i 다."""
    repo = _저장소(path)
    tickets = {
        f".scratch/a/issues/{i:02d}-t.md": _티켓(
            "ready-for-agent", "".join(f" `f{k}.py`" for k in range(i))
        )
        for i in range(1, n + 1)
    }
    _커밋(repo, tickets, "docs: 티켓 (#1)", _T)
    for i in range(1, n + 1):
        _커밋(
            repo,
            {f".scratch/a/issues/{i:02d}-t.md": _티켓("done")},
            f"feat: {i} (#{100 + i})",
            _T + timedelta(hours=i),
        )
    return repo


def test_파일럿_명령과_본_측정_명령은_목록을_쓰고_0으로_끝나며_본_측정은_파일럿_과제를_뺀다(
    tmp_path: Path,
) -> None:
    repo = _여러_후보_저장소(tmp_path / "repo", 12)
    rows: list[dict[str, object]] = [
        {
            "branch": f"feature/{i:02d}-t",
            "prs": [100 + i],
            "cost": 5.0,
            "cost_post_pr": 0.0,
            "top_model_effort": "claude-opus-5-5/xhigh",
        }
        for i in range(1, 13)
    ]
    branches = _브랜치_표(tmp_path / "branches.json", rows)
    pilot, main = tmp_path / "pilot.json", tmp_path / "main.json"
    table = tmp_path / "후보.md"
    common = ["--branches", str(branches), "--table", str(table), "--repo", str(repo)]
    common += ["--rev", "HEAD"]

    first = sel.main(["pilot", *common, "--out", str(pilot)], make_sorter=lambda _r, _o: _가르기())
    second = sel.main(
        ["main", *common, "--out", str(main), "--pilot", str(pilot)],
        make_sorter=lambda _r, _o: _가르기(),
    )

    assert (first, second) == (0, 0)
    got_pilot, got_main = read_task_list(pilot), read_task_list(main)
    assert (got_pilot.kind, len(got_pilot.tasks)) == (LIST_PILOT, 3)
    assert (got_main.kind, len(got_main.tasks)) == (LIST_MAIN, 8)
    pilot_ids = {t.task_id for t in got_pilot.tasks}
    assert pilot_ids <= {f"a-{i:02d}" for i in range(1, 5)}  # 크기 지표의 아래 삼분의 일
    assert not pilot_ids & {t.task_id for t in got_main.tasks}


def _숨은_시험_저장소(path: Path) -> Path:
    """B 에서 단언으로 실패하고 M 에서 통과하는 시험 셋을 M 이 더한 저장소."""
    repo = _저장소(path)
    ticket = ".scratch/calc/issues/01-triple.md"
    body = "`calc.py` 의 `triple` 을 고친다\n"
    files = {
        "pytest.ini": "[pytest]\npythonpath = .\n",
        "calc.py": "def triple(x):\n    return x * 2\n",
        ticket: _티켓("ready-for-agent", body),
    }
    _커밋(repo, files, "docs: 티켓 (#1)", _T)
    tests = "".join(
        f"\n\ndef test_{i}():\n    assert calc.triple({i}) == {3 * i}\n" for i in (1, 2, 3)
    )
    files = {
        "calc.py": "def triple(x):\n    return x * 3\n",
        "tests/test_calc.py": "import calc\n" + tests,
        ticket: _티켓("done", body),
    }
    _커밋(repo, files, "feat: 세 배를 고친다 (calc 01) (#2)", _T + timedelta(hours=1))
    return repo


def test_후보_표_명령은_싼_조건을_지난_후보를_02_의_가르기로_가르고_숨은_시험_수를_적는다(
    tmp_path: Path,
) -> None:
    repo = _숨은_시험_저장소(tmp_path / "repo")
    row: dict[str, object] = {
        "branch": "feature/01-triple",
        "prs": [2],
        "cost": 5.0,
        "cost_post_pr": 1.0,
        "top_model_effort": "claude-opus-5-5/xhigh",
    }
    branches = _브랜치_표(tmp_path / "branches.json", [row])
    table = tmp_path / "후보.md"
    임시 = tmp_path / "임시"
    임시.mkdir()
    notes: list[str] = []

    def make(repo_: Path, _out: Callable[[str], None]) -> sel.Sorter:
        def sort(base: str, merge: str) -> Hidden | Failure:
            pytest_command = (sys.executable, "-m", "pytest")
            return sort_candidate(
                repo_,
                base,
                merge,
                out=notes.append,
                setup=(),
                pytest=pytest_command,
                temp_root=임시,
            )

        return sort

    argv = ["table", "--branches", str(branches), "--table", str(table)]
    code = sel.main([*argv, "--repo", str(repo), "--rev", "HEAD"], make_sorter=make)

    assert code == 0
    text = table.read_text(encoding="utf-8")
    line = next(x for x in text.splitlines() if x.startswith("| calc-01 "))
    cells = [c.strip() for c in line.strip("|").split("|")]
    assert cells[1] == "#2"
    assert cells[5:9] == ["feature/01-triple", "날짜 안", "남음", "—"]
    assert cells[10:14] == ["$4.00", "1", "3", "—"]
    assert cells[14:] == ["없음", "없음"]
    assert "- B 가 2026-10-12 이후인 남은 후보: 1개(문턱 12개)" in text
    assert notes == []
    assert list(임시.iterdir()) == []
