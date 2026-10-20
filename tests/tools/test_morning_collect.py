"""tools/morning_collect.py 의 순수 함수 검증. 장부 호출과 기록 줄은 시험마다 작게 지어 넣는다.

gh·git·tasklist 를 부르는 길은 시험이 없고 `collect` 를 실제로 돌려
확인했다(`.claude/rules/tests.md`, 일지 2026-10-20-22 의 검사).
"""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta, timezone

import pytest
from tools.hook_report import BLOCK, NOTICE, Firing
from tools.model_sweep_judge import END_AT, JUDGE_AT, SWEEP_START_AT
from tools.morning_collect import (
    Collected,
    GhPr,
    HookRow,
    TicketRow,
    Timing,
    active_minutes,
    ago_text,
    bucket_of,
    ci_state,
    day_rows,
    duty_of,
    handoff_tickets,
    hook_legend,
    hook_rows,
    journal_next,
    kept,
    label_of,
    merged_got,
    merged_unknown,
    open_state,
    over_cap,
    queue_part,
    queue_whats,
    review_rounds,
    size_groups,
    sweep_kind,
    tasklist_load,
    ticket_start,
    timing,
    tool_timings,
    top_combo,
    without_merged,
    work_of,
    worktree_entries,
    worktree_pr,
)
from tools.morning_report import UNCOLLECTED, Metric, Section, Table, Value, pr_kind
from tools.token_report import Call, Json

KST = timezone(timedelta(hours=9))


def 호출(
    at: str,
    session: str = "s1",
    *,
    agent: str | None = None,
    branch: str | None = "chore/x",
    model: str = "claude-opus-5-5",
    effort: str | None = "xhigh",
    output: int = 1_000,
) -> Call:
    return Call(
        f"{session}-{at}",
        at,
        session,
        agent,
        None,
        "C--project-agent",
        branch,
        model,
        effort,
        0,
        0,
        0,
        0,
        output,
        0,
        None,
    )


def test_세션의_호출_사이가_5분_이하이면_그_사이의_분을_모두_돈_분으로_센다() -> None:
    active = active_minutes({"a": [0, 3, 20], "b": [2]})
    assert sorted(active) == [0, 1, 2, 3, 20]
    assert active[2] == {"a", "b"}
    assert active[20] == {"a"}


def test_동시_세션_구간은_정해_둔_다섯_무리다() -> None:
    assert [bucket_of(n) for n in (1, 3, 4, 9, 14, 15, 40)] == [
        "1~3",
        "1~3",
        "4~6",
        "7~9",
        "10~14",
        "15+",
        "15+",
    ]


def test_날마다_비용과_병합_PR과_평균_동시_세션을_센다() -> None:
    calls = [호출("2026-10-19T01:00:00Z"), 호출("2026-10-19T01:02:00Z", "s2")]
    merged = [datetime(2026, 10, 19, 2, tzinfo=UTC)]
    rows = day_rows(calls, merged, [date(2026, 10, 18), date(2026, 10, 19)], KST)
    assert rows[0].cost is None
    assert rows[0].prs == 0
    one = rows[1]
    cost = calls[0].cost()
    assert cost is not None
    assert one.prs == 1
    assert one.cost == cost * 2
    assert one.hours == 2 / 60
    assert one.avg == 1.0


def test_명령의_이름표는_알아볼_수_있는_꼴만_남긴다() -> None:
    assert label_of("git -C C:/a commit -F msg.txt") == "git commit"
    assert label_of("gh pr view 301 --json title") == "gh pr view"
    assert label_of("uv run python tools/run_checks.py") == "uv run_checks.py"
    assert label_of("uv run pytest -q") == "uv pytest"
    assert label_of("TOKEN=abc curl https://x") == "curl"


def test_이름표는_따옴표_낱말과_heredoc_본문을_남기지_않는다() -> None:
    assert label_of("git 'sk-비밀' x") == "git"
    assert label_of("uv run python - <<'EOF'\nimport secret_token.py\nEOF") == "uv"
    assert label_of("X=$(cat .env) curl y") == "(알 수 없음)"


def test_PR_제목의_앞머리가_작업_종류다() -> None:
    assert pr_kind("fix(test): Ctrl-C 판정") == "fix"
    assert pr_kind("chore!: 큰 변경") == "chore"
    assert pr_kind("제목만") == "(없음)"


def test_열린_PR의_CI_상태는_실패가_먼저고_다음이_도는_중이다() -> None:
    failed: list[Json] = [{"conclusion": "SUCCESS"}, {"conclusion": "FAILURE"}]
    running: list[Json] = [{"conclusion": "SUCCESS"}, {"status": "IN_PROGRESS", "conclusion": ""}]
    passed: list[Json] = [{"conclusion": "SUCCESS"}, {"conclusion": "SKIPPED"}]
    assert ci_state(failed) == "CI 실패"
    assert ci_state(running) == "CI 도는 중"
    assert ci_state(passed) == "CI 통과"
    assert ci_state([]) == "CI 없음"


def test_열린_PR의_상태는_초안과_리뷰_결정과_CI를_잇는다() -> None:
    passed: list[Json] = [{"conclusion": "SUCCESS"}]
    draft: Json = {"isDraft": True, "reviewDecision": None, "statusCheckRollup": passed}
    changes: Json = {
        "isDraft": False,
        "reviewDecision": "CHANGES_REQUESTED",
        "statusCheckRollup": passed,
    }
    approved: Json = {"isDraft": False, "reviewDecision": "APPROVED", "statusCheckRollup": []}
    waiting: Json = {
        "isDraft": False,
        "reviewDecision": "REVIEW_REQUIRED",
        "statusCheckRollup": passed,
    }
    assert open_state(draft) == "초안 · CI 통과"
    assert open_state(changes) == "리뷰 변경 요청 · CI 통과"
    assert open_state(approved) == "리뷰 승인 · CI 없음"
    assert open_state(waiting) == "리뷰 대기 · CI 통과"


def test_리뷰_왕복은_PR을_연_뒤_올린_커밋_수이고_main을_합친_커밋은_세지_않는다() -> None:
    # #301 의 11 가운데 7 이 `Merge remote-tracking branch 'origin/main'` 이었다
    opened = datetime(2026, 10, 19, 5, tzinfo=UTC)
    commits = [
        (opened - timedelta(hours=1), "feat: 처음"),
        (opened + timedelta(minutes=5), "fix: 리뷰 반영"),
        (opened + timedelta(hours=1), "Merge remote-tracking branch 'origin/main' into chore/x"),
        (opened + timedelta(hours=2), "docs: 일지"),
    ]
    assert review_rounds(opened, commits) == 2


def test_tasklist_의_CSV_에서_프로세스_수와_메모리_합을_MB로_읽는다() -> None:
    text = (
        '"claude.exe","10","Console","1","102,400 K"\n"claude.exe","11","Console","1","2,048 K"\n'
    )
    assert tasklist_load(text) == (2, 102)
    assert tasklist_load("정보: 지정된 조건에 일치하는 작업이 없습니다.\n") == (0, 0)


def test_대기열_행의_무엇_칸을_번호로_꺼낸다() -> None:
    text = (
        "| # | 무엇 | 어디로 | 승인 |\n|---|---|---|---|\n"
        "| 238 | 남은 워크트리 \\| 여섯 | 사람 몫: 정리 | 2026-10-19 11회차 |\n"
    )
    assert queue_whats(text) == {238: "남은 워크트리 | 여섯"}


def test_훅_표는_최근_14일과_앞_14일을_견주고_조용한_훅을_가른다() -> None:
    last = date(2026, 10, 19)
    firings = [
        Firing("hook_a.py", NOTICE, last, ""),
        Firing("hook_a.py", NOTICE, last - timedelta(days=20), ""),
        Firing("hook_a.py", NOTICE, last - timedelta(days=21), ""),
        Firing("hook_b.py", BLOCK, last - timedelta(days=1), "이유"),
    ]
    hooks = ["hook_a.py", "hook_b.py", "hook_old.py", "hook_new.py"]
    introduced = {"hook_old.py": date(2026, 9, 1), "hook_new.py": date(2026, 10, 10)}
    rows = hook_rows(firings, hooks, introduced, last, earliest=date(2026, 9, 1))
    assert HookRow("알림", "hook_a.py", 1, 2, "유지") in rows
    assert HookRow("막음", "hook_b.py", 1, 0, "유지") in rows
    assert HookRow("조용함", "hook_old.py", 0, 0, "검토") in rows
    assert HookRow("조용함", "hook_new.py", 0, 0, "판단 이름") in rows


def test_기록이_창의_첫날보다_늦으면_조용한_훅을_검토로_내지_않는다() -> None:
    last = date(2026, 10, 19)
    rows = hook_rows(
        [], ["hook_old.py"], {"hook_old.py": date(2026, 9, 1)}, last, date(2026, 10, 1)
    )
    assert rows == [HookRow("조용함", "hook_old.py", 0, 0, "판단 이름")]


def test_판단_이름_판정이_있는_날에만_그_뜻을_한_줄로_푼다() -> None:
    # "판단 이름"은 "판단하기 이르다"인데 처음 보는 사람은 "이름(name)"으로 읽는다
    early = [HookRow("조용함", "hook_new.py", 0, 0, "판단 이름")]
    kept_rows = [HookRow("알림", "hook_a.py", 1, 2, "유지")]
    [line] = hook_legend(early)
    assert line.startswith("- 판정 `판단 이름`은 판단하기 이르다는 뜻이다")
    assert hook_legend(kept_rows) == []


def 티켓(n: int, criteria: int, handoffs: int = 0) -> TicketRow:
    return TicketRow(
        n,
        f"0{n}-t",
        found=True,
        criteria=criteria,
        cost=float(n),
        active_h=1.0,
        sessions=1,
        handoffs=handoffs,
    )


def test_티켓은_수락_조건_수로_세_무리로_나눈다() -> None:
    rows = [티켓(n, c) for n, c in enumerate([3, 9, 5, 12, 7, 20], start=1)]
    groups = size_groups(rows)
    assert [(name, [r.criteria for r in g]) for name, g in groups] == [
        ("작음", [3, 5]),
        ("중간", [7, 9]),
        ("큼", [12, 20]),
    ]


def test_티켓_파일을_찾지_못한_PR은_무리에_넣지_않는다() -> None:
    rows = [
        티켓(1, 3),
        TicketRow(
            2,
            "02-x",
            found=False,
            criteria=0,
            cost=0.0,
            active_h=0.0,
            sessions=0,
            handoffs=0,
        ),
    ]
    assert [len(g) for _, g in size_groups(rows)] == [1]


def test_티켓_창은_인계_훅이_들어온_날부터이고_28일을_넘지_않는다() -> None:
    # 인계가 일어날 수 없던 날의 티켓이 분모에 들면 인계 몫이 낮게 보인다
    day = date(2026, 10, 19)
    assert ticket_start(day, date(2026, 10, 16)) == date(2026, 10, 16)
    assert ticket_start(day, date(2026, 9, 1)) == date(2026, 9, 22)
    assert ticket_start(day, None) == date(2026, 9, 22)


def test_인계가_난_티켓을_인계가_많은_차례로_꺼낸다() -> None:
    rows = [티켓(1, 3), 티켓(2, 9, handoffs=1), 티켓(3, 12, handoffs=2), 티켓(4, 5, handoffs=1)]
    assert [r.number for r in handoff_tickets(rows)] == [3, 2, 4]


def test_브랜치가_돈_모델과_노력은_메인_세션_비용이_가장_큰_것이다() -> None:
    # 판정 도구가 읽는 `top_model_effort`처럼 호출 수가 아니라 비용으로 고르고, 노력이 없으면 `-`다
    mains = [
        호출("2026-10-19T01:00:00Z", effort="medium"),
        호출("2026-10-19T01:01:00Z", effort="medium"),
        호출("2026-10-19T01:02:00Z", effort="xhigh", output=3_000),
    ]
    assert top_combo(mains) == "claude-opus-5-5/xhigh"
    assert top_combo([호출("2026-10-19T01:00:00Z", effort=None)]) == "claude-opus-5-5/-"
    assert top_combo([]) is None


def PR(branch: str, created: datetime, merged: datetime) -> GhPr:
    return GhPr(1, "제목", branch, created, merged)


def test_스윕의_모집단은_기간_안에_병합된_스윕_종류의_PR이고_앞서_연_PR도_남긴다() -> None:
    # 판정 도구의 `split_arms`는 스윕 시작 전에 연 PR에 표지만 달고 모집단에 남긴다
    start, judge, end = SWEEP_START_AT, JUDGE_AT, END_AT
    day = timedelta(days=1)
    assert sweep_kind(PR("feature/01-a", start - day, start + day)) == "구현"
    assert sweep_kind(PR("chore/a", start + day, start + 2 * day)) == "하네스"
    assert sweep_kind(PR("chore/a", start - 2 * day, start - day)) is None
    assert sweep_kind(PR("chore/a", start, judge)) is None
    assert sweep_kind(PR("fix/a", start, start + day)) is None
    assert sweep_kind(PR("chore/a", end, end + day)) is None


def test_워크트리의_PR은_열림_병합_없음이고_PR을_읽지_못했으면_모름이다() -> None:
    merged = {"chore/a"}
    opened = {"chore/b": 296}
    assert worktree_pr("chore/b", merged, opened) == ("열림", 296)
    assert worktree_pr("chore/a", merged, opened) == ("병합", None)
    assert worktree_pr("chore/c", merged, opened) == ("없음", None)
    assert worktree_pr("chore/c", None, opened) == ("모름", None)
    assert worktree_pr("chore/c", merged, None) == ("모름", None)
    assert worktree_pr("chore/a", merged, None) == ("병합", None)
    assert worktree_pr(None, None, None) == ("없음", None)


def test_병합_PR을_읽지_못하면_그것에_기대는_지표_셋을_빈_열로_바꾼다() -> None:
    full = (1.0,) * 8
    keys = ("cost", "per_pr", "avg", "per_hour", "prs")
    metrics = tuple(Metric(k, k, "int", full, None) for k in keys)
    assert [m.series for m in without_merged(metrics)] == [full, (), full, (), ()]


def test_값을_남길_이름표는_상위_몫과_지난_제안이_고른_열쇠의_이름표다() -> None:
    # 값이 줄어 순위에서 빠져도 제안의 확인할 수치는 남아야 효과 확인됨에 닿는다
    ranked = ["Bash: git commit", "Bash: uv run pytest", "Read", "Bash: gh"]
    wanted = frozenset({"cmd:Bash: gh:median_s", "read:Read:chars"})
    assert kept(ranked, 2, wanted, "cmd") == ["Bash: git commit", "Bash: uv run pytest", "Bash: gh"]


def test_절마다_모은_것을_하나로_합친다() -> None:
    a = Collected()
    a.value("x", "엑스", 1.0, "회")
    a.value("없음", "값 없음", None, "회")
    a.refs.add(1)
    b = Collected()
    b.branches["chore/x"] = "제목"
    b.refs.add(2)
    got = merged_got([a, b])
    assert got.values == {"x": Value("엑스", 1.0, "회")}
    assert (got.refs, got.branches) == ({1, 2}, {"chore/x": "제목"})


def test_걸린_시간은_10분_30초를_넘은_것을_합계에서_빼고_따로_센다() -> None:
    t = timing([1.0, 2.0, 3.0, 700.0])
    # 상위 10% 경계는 자료 안에서 잇는 분위수(inclusive)라 가장 큰 값을 넘지 않는다
    assert t == Timing(count=3, total_s=6.0, median_s=2.0, p90_s=2.8, over=1)
    assert timing([900.0]) is None


def test_한계를_넘은_호출은_호출이_모두_넘은_이름표까지_센다() -> None:
    # `timing`이 None인 이름표(호출이 모두 한계를 넘었다)도 빠지지 않는다
    assert over_cap([[1.0, 700.0], [900.0, 800.0], []]) == 3


def test_대기열_3회차_이상_행은_목록이_아니라_표로_적는다() -> None:
    # 상세 절은 목록 다섯 줄 이하라(작성 규칙 4), 행 수가 늘어도 목록은 한 줄이다
    text = (
        "| # | 무엇 | 어디로 | 승인 |\n|---|---|---|---|\n"
        "| 238 | 남은 워크트리 | 사람 몫: 정리 | 2026-10-19 11회차 |\n"
        "| 240 | 규칙 넷 | `CLAUDE.md` | 2026-10-19 4회차 |\n"
        "| 241 | 규칙 다섯 | `CLAUDE.md` | 2026-10-19 6회차 |\n"
        "| 242 | 규칙 하나 | `CLAUDE.md` | 2026-10-19 2회차 |\n"
    )
    part = queue_part(date(2026, 10, 19), text, "원본")
    summary = "- 열린 행 4개 · 기한 지난 행 0개 · 사람 몫 1개(직접 하실 일 참고)"
    assert part.section.lines == (summary,)
    assert part.section.tables == (
        Table(
            ("대기열", "회차", "작업 이름", "작업 내용"),
            "lrll",
            (
                ("대기열 241", "6회차", "{{qname:241}}", "{{qcontent:241}}"),
                ("대기열 240", "4회차", "{{qname:240}}", "{{qcontent:240}}"),
            ),
        ),
    )
    assert sorted(part.got.queue) == [238, 240, 241]


def 기록(at: str, *content: dict[str, Json]) -> dict[str, Json]:
    items: list[Json] = list(content)
    return {"timestamp": at, "message": {"content": items}}


def test_도구_호출과_그_결과의_시각_차가_걸린_시간이고_백그라운드는_세지_않는다() -> None:
    records = [
        기록(
            "2026-10-19T01:00:00Z",
            {"type": "tool_use", "id": "a", "name": "Bash", "input": {"command": "git status"}},
            {
                "type": "tool_use",
                "id": "b",
                "name": "Bash",
                "input": {"command": "uv run pytest", "run_in_background": True},
            },
        ),
        기록("2026-10-19T01:00:04Z", {"type": "tool_result", "tool_use_id": "a"}),
        기록("2026-10-19T01:00:05Z", {"type": "tool_result", "tool_use_id": "b"}),
        기록("2026-10-19T01:01:00Z", {"type": "tool_use", "id": "c", "name": "Edit", "input": {}}),
        기록("2026-10-19T01:01:09Z", {"type": "tool_result", "tool_use_id": "c"}),
    ]
    found = tool_timings(records, lambda at: True)
    assert found == [("Bash: git status", 4.0), ("Edit", 9.0)]


def test_작업의_비용과_활동과_PR_뒤_몫을_브랜치_호출로_센다() -> None:
    calls = [
        호출("2026-10-19T01:00:00Z", "s1"),
        호출("2026-10-19T01:03:00Z", "s1"),
        호출("2026-10-19T03:00:00Z", "s2"),
    ]
    opened = datetime(2026, 10, 19, 2, tzinfo=UTC)
    merged = datetime(2026, 10, 19, 4, tzinfo=UTC)
    w = work_of(301, "fix: 제목", calls, opened, merged, {"s2": True})
    assert (w.number, w.kind, w.sessions, w.handoffs) == (301, "fix", 2, 1)
    assert w.active_h == 5 / 60
    assert w.lead_h == 3.0
    assert w.after == pytest.approx(1 / 3)


def test_워크트리_목록에서_주_체크아웃을_빼고_경로와_브랜치를_읽는다() -> None:
    text = (
        "worktree C:/project/agent\nHEAD 1\nbranch refs/heads/main\n\n"
        "worktree C:/project/agent/.claude/worktrees/a\nHEAD 2\nbranch refs/heads/chore/a\n\n"
        "worktree C:/project/agent/.claude/worktrees/b\nHEAD 3\ndetached\n\n"
    )
    assert worktree_entries(text) == [
        ("C:/project/agent/.claude/worktrees/a", "chore/a"),
        ("C:/project/agent/.claude/worktrees/b", None),
    ]


def test_훅이_하는_일은_독스트링_첫_문단에서_계기를_뗀_첫_문장이다() -> None:
    src = (
        '"""PreToolUse 훅(Bash). 큰 heredoc 을 막고\nWrite 도구로 안내한다. 둘째 문장.\n\n더."""\n'
    )
    assert duty_of(src) == "큰 heredoc 을 막고 Write 도구로 안내한다."
    assert duty_of('"""SessionStart 훅. 짧다."""\n') == "짧다."
    assert duty_of("x = (\n") == "(수집 안 됨)"


def test_마지막_기록은_한_시간_안이면_분으로_적고_음수는_0으로_적는다() -> None:
    assert ago_text(30 * 60) == "30분 전"
    assert ago_text(-5) == "0분 전"
    assert ago_text(5 * 3600 + 10) == "5시간 전"


def test_일지의_다음_절만_꺼낸다() -> None:
    text = "# 일지\n\n## 한 일\n- a\n\n## 다음\n- 재개를 기다린다\n- tidy\n"
    assert journal_next(text) == "- 재개를 기다린다\n- tidy"
    assert journal_next("# 다음이 없다\n") == ""


def test_병합_PR을_읽지_못하면_그것에_기대는_표와_줄을_걷고_수집_안_됨을_적는다() -> None:
    s = Section(3, "병렬 세션", (Table(("병합 PR",), "r", (("0",),)),), ("- 병합 PR 0개",), "출처")
    got = merged_unknown(s, kept=("- 지금의 부하: 워크트리 3개",))
    lines = (f"- 병합 PR {UNCOLLECTED}(gh 실패)", "- 지금의 부하: 워크트리 3개")
    assert got == Section(3, "병렬 세션", (), lines, "출처")
