"""tools/morning_report.py 검증. 수집 JSON(`Data`)과 메모 JSON(`Notes`)은 시험마다 작게 지어 넣는다.

수치는 2026-10-19 아침 보고에서 옮겨 줄였다(환산 비용 856.36, 7일 중앙값 485.69).
"""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta, timezone
from pathlib import Path

import pytest
from tools.morning_report import (
    LOOKUP_FAILED,
    NO_CONTENT,
    NO_NAME,
    UNCOLLECTED,
    Block,
    Data,
    Decision,
    Head,
    Limit,
    Metric,
    Named,
    Notes,
    Pr,
    QueueRow,
    Section,
    Seen,
    Table,
    Todo,
    Value,
    amount,
    check_state,
    check_text,
    json_int,
    json_list,
    json_obj,
    json_str,
    json_time,
    latest_checks,
    main,
    metric_row,
    read_state,
    render,
    sparkline,
    state_json,
    table_lines,
    unusual,
    verdict,
)

DAY = date(2026, 10, 19)
COST = (1356.51, 1297.73, 132.08, 485.69, 1545.33, 431.90, 50.85, 856.36)
CHECK = "cmd:git commit:median_s"
CONTENT = "부하에서 흔들린 판정과 시간 제한을 고쳤다"
REPORTS = ("summary", "cost", "work", "environment", "experiment")


def 지표(
    key: str = "cost", series: tuple[float | None, ...] = COST, alarm: str | None = None
) -> Metric:
    return Metric(key, "환산 비용", "money", series, alarm)


def 한도(**kw: object) -> Limit:
    base = Limit(
        percent=37,
        at="2026-10-20T09:00:00+09:00",
        resets="2026-10-26T06:00:00+09:00",
        account="njh4803@gmail.com",
        rate=27.0,
        spent=999.0,
        day_points=31.7,
        speed=1.3,
        full_at="2026-10-22T09:00:00+09:00",
        basis_at="2026-10-19T09:00:00+09:00",
        basis_percent=37,
    )
    return replace(base, **kw)


def 자료(**kw: object) -> Data:
    base = Data(
        day=DAY,
        made="2026-10-20T09:10:00+09:00",
        metrics=(지표(alarm="1.76배"),),
        values={CHECK: Value("git commit 중앙값", 385.2, "초")},
        sections=(),
        prs={301: Pr(301, "test: 부하에서 흔들린 Ctrl-C 판정", "본문", "chore/mutate-ctrl-c")},
        queue={238: QueueRow(238, 11, human=True, what="남은 워크트리 여섯")},
        branches={},
        journal="",
        limit=한도(),
    )
    return replace(base, **kw)


def 메모(**kw: object) -> Notes:
    base = Notes(
        prs={301: Named("Ctrl-C 판정 안정화", CONTENT, "부하 시험")},
        queue={238: Named("남은 워크트리 정리", "정리 도구가 지우지 못한 워크트리 여섯")},
        branches={},
        todos=(),
        decisions=(),
        heads={r: Head("결론입니다.", ()) for r in REPORTS},
        blocks={k: Block("결론 문장", "그래서 문장", "없음") for k in ("work.a", "work.b")},
        causes={"cost": "세션이 많았다"},
    )
    return replace(base, **kw)


def 결정(**kw: object) -> Decision:
    base = Decision(
        id="commit-wait",
        question="커밋할 때 도는 검사를 줄일까요?",
        recommend="오래 걸리는 것을 CI에만 둘지 살펴봅니다",
        basis="지난 7일 커밋 225번, 중앙값 6분 25초(작업 보고)",
        check=CHECK,
        better="down",
    )
    return replace(base, **kw)


def 표(*rows: tuple[str, ...], key: str = "work.a", report: str = "work") -> Table:
    return Table(
        key=key,
        report=report,
        question="가장 비싼 작업은?",
        period="10-13 ~ 10-19(7일)",
        unit="달러",
        head=("PR", "작업 이름", "작업 내용"),
        align="lll",
        rows=rows,
    )


def 절(*tables: Table, report: str = "work", lines: tuple[str, ...] = ()) -> Section:
    return Section(4, "비싼 작업", report, tables, lines, "task 통계")


ROW = ("#301", "{{name:301}}", "{{content:301}}")


# 핵심 지표와 표


def test_스파크라인은_가장_낮은_값을_가장_낮은_막대로_높은_값을_높은_막대로_그린다() -> None:
    assert sparkline([1.0, 8.0, 4.0]) == "▁█▄"


def test_스파크라인은_값이_없는_날을_점으로_그리고_값이_모두_같으면_가운데_막대다() -> None:
    assert sparkline([None, 2.0, 2.0]) == "·▄▄"
    assert sparkline([None, None]) == "··"


def test_경보면_판정_칸에_경보와_그_까닭을_적는다() -> None:
    assert verdict(COST, "1.76배") == "⚠ 경보 (1.76배)"
    assert verdict(COST, "") == "⚠ 경보"


def test_경보가_아니면_7일_안에서_최고와_최저와_정상을_가른다() -> None:
    assert verdict((0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 9.0), None) == "7일 중 최고"
    assert verdict((0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 0.5), None) == "7일 중 최저"
    assert verdict((0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 3.5), None) == "정상"


def test_어제가_다른_날과_같은_값으로_최고나_최저면_평소와_다르지_않다() -> None:
    # 확인 실행에서 어제의 전날 하루만 5이고 어제를 포함한 여섯 날이 0인 지표가
    # `| 읽지 못한 기록 줄 | 0 | 0 | +0 | 원인 모름 |`으로 평소와 다른 것에 올랐다(일지
    # 2026-10-21-04)
    unread = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 5.0, 0.0)
    assert verdict(unread, None) == "정상"
    assert not unusual(Metric("unreadable", "읽지 못한 기록 줄", "int", unread, None))
    assert verdict((1.0, 9.0, 2.0, 3.0, 4.0, 5.0, 6.0, 9.0), None) == "정상"
    assert verdict((4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0, 4.0), None) == "정상"
    # 세션 비용을 다른 순서로 더한 날은 같은 금액이 한 ulp 갈린다(0.1 + 0.2는 0.30000000000000004)
    assert verdict((0.1, 0.2, 0.3, 0.1, 0.2, 0.1, 0.2, 0.1 + 0.2), None) == "정상"
    assert verdict((0.3, 0.2, 0.1, 0.3, 0.2, 0.3, 0.2, 0.3 - 0.2), None) == "정상"


def test_어제가_평소와_같으면_홀로_최고여도_평소와_다르지_않다() -> None:
    # 창의 다른 날에 값이 하루뿐이면 창 밖의 첫날과의 중앙값이 어제와 같을 수 있다(차이 칸이 +0%)
    assert verdict((8.0, None, None, None, None, None, 2.0, 5.0), None) == "정상"
    # 0.1과 0.2의 중앙값은 0.15000000000000002라 같음을 ==로 견주면 홀로 최저로 뽑힌다
    assert verdict((0.1, None, None, None, None, None, 0.2, 0.15), None) == "정상"


def test_7일_안의_최고와_최저는_어제를_뺀_여섯_날과_견준다() -> None:
    # 창 밖의 첫날은 견주는 날에 들지 않는다. 평소의 중앙값에만 들어, 어제가 평소와 같은지를 가르는
    # 자리에서만 판정에 닿는다(위 시험)
    assert verdict((9.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0), None) == "7일 중 최고"
    assert verdict((None, None, None, None, None, None, 2.0, 1.0), None) == "7일 중 최저"
    assert verdict((None, None, None, None, None, None, None, 1.0), None) == "정상"


def test_어제_값이_없으면_판정하지_않는다() -> None:
    assert verdict((1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, None), None) == "-"


def test_평소와_다른_지표의_행은_어제_평소_차이다() -> None:
    # 달러는 소수점 없이, 차이는 평소 대비 백분율이다(Few)
    assert metric_row(지표()) == ["환산 비용", "$856", "$486", "+76%"]


def test_평소가_0이면_차이를_수로_적는다() -> None:
    m = Metric("unreadable", "읽지 못한 기록 줄", "int", (0, 0, 0, 0, 0, 0, 0, 5), None)
    assert metric_row(m) == ["읽지 못한 기록 줄", "5", "0", "+5"]


def test_지표를_모으지_못했으면_어제_칸에_수집_안_됨을_적는다() -> None:
    m = Metric("prs", "병합 PR 수", "int", (), None)
    assert metric_row(m) == ["병합 PR 수", UNCOLLECTED, "-", "-"]


def test_표의_칸에_든_세로줄과_줄바꿈은_표를_깨지_않게_바꾼다() -> None:
    lines = table_lines(("이름", "값"), "lr", (("a|b", "1\n2"),))
    assert lines == ["| 이름 | 값 |", "|---|--:|", "| a\\|b | 1 2 |"]


def test_표는_질문_기간_단위가_없으면_읽지_않는다() -> None:
    # 기간이 적히지 않은 7일치 표가 하루치 표와 같은 모양으로 섞였다(설계의 문제 5)
    j = 표(ROW).to_json()
    assert isinstance(j, dict)
    j["period"] = ""
    with pytest.raises(ValueError, match="period"):
        Table.of(j)


def test_표의_보고가_다섯_밖이면_읽지_않는다() -> None:
    j = 표(ROW).to_json()
    assert isinstance(j, dict)
    j["report"] = "daily"
    with pytest.raises(ValueError, match="report"):
        Table.of(j)


def test_모든_행이_수집_안_됨인_칸은_그리지_않는다() -> None:
    table = replace(
        표(("#301", UNCOLLECTED, "a"), ("#302", UNCOLLECTED, "b")), head=("PR", "고친 몫", "이름")
    )
    text, _, _ = render(자료(sections=(절(table),)), 메모(), {}, "work")
    assert "| PR | 이름 |" in text
    assert "고친 몫" not in text


def test_행이_없는_표는_블록과_경고_없이_건너뛰고_그_밖의_수에_해당_없음으로_적는다() -> None:
    # 어제 병합이 0건인 날의 `work.merged`가 머리만 있는 표와 `(결론 없음)` 블록으로 그려졌다
    text, _, warnings = render(자료(sections=(절(표()),)), 메모(blocks={}), {}, "work")
    assert "###" not in text
    assert "| PR |" not in text
    assert "- 가장 비싼 작업은?: 해당 없음(10-13 ~ 10-19(7일))" in text
    assert warnings == []


# 분야별 보고


def test_분야별_보고는_결론과_정할_것_뒤에_표마다_결론_질문_그래서_할_일로_감싼다() -> None:
    notes = 메모(heads={"work": Head("어제 PR 넷을 끝냈습니다.", ("열린 PR 둘을 이을까요?",))})
    text, _, warnings = render(자료(sections=(절(표(ROW)),)), notes, {}, "work")
    lines = text.splitlines()
    assert lines[0] == "# 작업 보고 · 2026-10-19(월)"
    assert "**결론:** 어제 PR 넷을 끝냈습니다." in lines
    assert "**이 보고에서 정할 것:** 열린 PR 둘을 이을까요?" in lines
    block = text.split("### 결론 문장", 1)[1]
    assert block.splitlines()[2] == "가장 비싼 작업은? · 10-13 ~ 10-19(7일) · 달러"
    assert "**그래서:** 그래서 문장" in block
    assert "**할 일:** 없음" in block
    assert warnings == []


def test_분야별_보고에는_그_보고의_표와_줄만_싣는다() -> None:
    sections = (
        절(표(ROW), lines=("- 작업 줄",)),
        절(표(("x", "y", "z"), key="cost.a", report="cost"), report="cost", lines=("- 비용 줄",)),
    )
    text, _, _ = render(자료(sections=sections), 메모(), {}, "work")
    assert "- 작업 줄" in text
    assert "비용 줄" not in text
    assert "| x |" not in text


def test_블록의_결론_그래서_할_일이_비면_경고한다() -> None:
    notes = 메모(blocks={"work.a": Block("결론", "", "")})
    _, _, warnings = render(자료(sections=(절(표(ROW)),)), notes, {}, "work")
    assert warnings == ["표 work.a(가장 비싼 작업은?)의 메모에 그래서·할 일이 없다"]


def test_보고의_결론이_비면_경고한다() -> None:
    _, _, warnings = render(자료(), 메모(heads={}), {}, "cost")
    assert warnings == ["메모의 heads에 cost 보고의 결론이 없다"]


def test_작업은_처음_나온_표에만_내용을_적고_뒤에서는_그_표를_가리킨다() -> None:
    second = replace(표(ROW, key="work.b"), question="어제 무엇을 끝냈나?")
    text, _, warnings = render(자료(sections=(절(표(ROW), second),)), 메모(), {}, "work")
    assert f"| #301 | Ctrl-C 판정 안정화 | {CONTENT} |" in text
    assert "| #301 | Ctrl-C 판정 안정화 | → 「가장 비싼 작업은?」 표 |" in text
    assert warnings == []


def test_작업_자리는_PR의_이름과_브랜치를_적고_PR이_없으면_메모의_이름이다() -> None:
    rows = (("{{work:chore/mutate-ctrl-c}}",), ("{{work:feature/02-x}}",), ("{{work:main}}",))
    table = replace(표(*rows), head=("작업(브랜치)",), align="l")
    notes = 메모(branches={"feature/02-x": "실패 원인 기록"})
    text, _, _ = render(자료(sections=(절(table),)), notes, {}, "work")
    assert "| Ctrl-C 판정 안정화 (`chore/mutate-ctrl-c`) |" in text
    assert "| 실패 원인 기록 (`feature/02-x`) |" in text
    assert "| `main` |" in text


def test_이름을_적지_않은_작업은_이름_없음으로_그리고_경고한다() -> None:
    text, _, warnings = render(자료(sections=(절(표(ROW)),)), 메모(prs={}), {}, "work")
    assert f"| #301 | {NO_NAME} | {NO_CONTENT} |" in text
    assert any("301" in w for w in warnings)


def test_제목을_가져오지_못한_작업은_제목_조회_실패로_적는다() -> None:
    row = ("#302", "{{name:302}}", "{{content:302}}")
    data = 자료(sections=(절(표(row)),), prs={302: Pr(302, None, "", "")})
    text, _, _ = render(data, 메모(), {}, "work")
    assert f"| #302 | {LOOKUP_FAILED} | {LOOKUP_FAILED} |" in text


def test_표에서_내용을_적은_작업은_뒤의_글에서_이름만_붙인다() -> None:
    notes = 메모(blocks={"work.a": Block("결론", "#301 은 길었다", "없음")})
    data = 자료(sections=(절(표(ROW), lines=("- 인계: {{ref:301}} 두 번",)),))
    text, _, _ = render(data, notes, {}, "work")
    assert "**그래서:** #301 Ctrl-C 판정 안정화 은 길었다" in text
    assert "- 인계: #301 Ctrl-C 판정 안정화 두 번" in text


def test_수집_도구가_쓴_줄의_작업도_처음에는_이름과_내용을_적는다() -> None:
    data = 자료(sections=(절(lines=("- 인계가 난 티켓: {{ref:301}} 인계 2번",)),))
    text, _, _ = render(data, 메모(), {}, "work")
    assert f"- 인계가 난 티켓: #301 Ctrl-C 판정 안정화({CONTENT}) 인계 2번" in text


def test_병합_PR의_분류는_메모의_묶음이고_없으면_제목_앞머리다() -> None:
    table = 표(("{{group:301}}", "#301", "{{name:301}}"))
    data = 자료(sections=(절(table),))
    grouped, _, _ = render(data, 메모(), {}, "work")
    assert "| 부하 시험 | #301 | Ctrl-C 판정 안정화 |" in grouped
    plain, _, _ = render(data, 메모(prs={301: Named("Ctrl-C 판정 안정화", "내용")}), {}, "work")
    assert "| test | #301 | Ctrl-C 판정 안정화 |" in plain


def test_분야별_보고의_끝에_원본을_한_줄로_적는다() -> None:
    text, _, _ = render(자료(sections=(절(표(ROW)),)), 메모(), {}, "work")
    assert text.rstrip().splitlines()[-1] == "원본: task 통계"


def test_비용_보고는_주간_한도_칸의_환산_비율을_머리에_적는다() -> None:
    text, _, _ = render(자료(), 메모(), {}, "cost")
    assert "주간 한도 1% ≈ API 환산 $27" in text
    work, _, _ = render(자료(), 메모(), {}, "experiment")
    assert "주간 한도 1%" not in work


def test_보고에는_앱이_그리지_못하는_HTML_태그가_없다() -> None:
    for report in REPORTS:
        text, _, _ = render(자료(sections=(절(표(ROW)),)), 메모(), {}, report)
        assert "<details" not in text
        assert "<summary" not in text


# 종합 보고


def test_종합_보고의_첫_줄은_정할_것의_수와_결론이다() -> None:
    notes = 메모(decisions=(결정(),), heads={"summary": Head("어제는 1.8배 썼습니다.", ())})
    text, _, _ = render(자료(), notes, {}, "summary")
    assert text.splitlines()[:3] == [
        "# 종합 보고 · 2026-10-19(월)",
        "",
        "**오늘 정할 것 1개.** 어제는 1.8배 썼습니다.",
    ]


def test_종합_보고의_절_차례는_한도_정할_것_다른_것_할_일_분야별이다() -> None:
    text, _, _ = render(자료(), 메모(), {}, "summary")
    heads = ("## 주간 한도", "## 오늘 정할 것", "## 평소와 다른 것", "## 직접 하실 일")
    order = [text.index(h) for h in (*heads, "## 오늘 나오는 분야별 보고")]
    assert order == sorted(order)


def test_주간_한도는_지금_몫과_어제_몫과_차는_시각을_적는다() -> None:
    text, _, _ = render(자료(), 메모(), {}, "summary")
    block = text.split("## 주간 한도", 1)[1].split("## 오늘 정할 것", 1)[0]
    assert "지금 **37%** 썼습니다(주간 · 모든 모델, 10-20 09:00 기준)" in block
    assert "초기화(10-26(월) 06:00)까지 5일 21시간 남았습니다" in block
    assert (
        "어제 약 **32%p**를 썼습니다. 하루 예산 14%p(100%를 7일로 나눈 값)의 2.2배입니다" in block
    )
    assert "최근 24시간 속도(시간당 약 1.3%p)면 **10-22(목) 09시께** 찹니다" in block
    assert "1% ≈ API 환산 $27(10-19 09:00에 찍은 37%와 그때까지 이번 창의" in block


def test_장부를_채우기_전에_찍은_한도가_없으면_어림하지_않았다고_적는다() -> None:
    limit = 한도(rate=None, day_points=None, speed=None, full_at=None, basis_at=None)
    text, _, _ = render(자료(limit=limit), 메모(), {}, "summary")
    assert "지금 **37%** 썼습니다" in text
    assert "어제 쓴 몫과 속도는 어림하지 않았습니다" in text
    # 몫이나 비용이 0이어도 비율이 없는데, 그 원인은 내일도 그대로일 수 있다(PR 직전 리뷰)
    assert "내일부터 나옵니다" not in text
    assert "몫이나 그때까지의 비용이 0이라" in text


def test_확인할_수치의_달러는_10_이상이면_소수점_없이_적는다() -> None:
    assert amount(856.36, "$") == "$856"
    assert amount(0.05, "$") == "$0.05"
    assert amount(1234.5, "자") == "1,234자"


def test_초기화_시각은_찍은_시각의_시간대로_분까지_반올림해_적는다() -> None:
    # get_usage는 초기화 시각을 UTC로, 초 아래 꼬리를 붙여 준다(2026-10-25T20:59:59.733Z)
    limit = 한도(resets="2026-10-25T20:59:59.733000+00:00")
    text, _, _ = render(자료(limit=limit), 메모(), {}, "summary")
    assert "초기화(10-26(월) 06:00)까지 5일 21시간 남았습니다" in text


def test_초기화_전에_차지_않으면_그렇게_적는다() -> None:
    text, _, _ = render(자료(limit=한도(full_at=None, speed=0.2)), 메모(), {}, "summary")
    assert "이 속도면 초기화 전에 차지 않습니다" in text


def test_주간_한도를_찍지_않았으면_까닭을_적는다() -> None:
    text, _, _ = render(자료(limit="한도 기록이 없다"), 메모(), {}, "summary")
    assert f"- 주간 한도 {UNCOLLECTED}: 한도 기록이 없다" in text


def test_평소와_다른_것은_경보와_7일_최고_최저만_싣고_나머지는_이름만_적는다() -> None:
    calm = Metric("prs", "병합 PR 수", "int", (1, 2, 3, 4, 5, 6, 7, 4), None)
    text, _, _ = render(자료(metrics=(지표(alarm="1.76배"), calm)), 메모(), {}, "summary")
    assert "| 환산 비용 | $856 | $486 | +76% | 세션이 많았다 |" in text
    assert "**평소대로:** 병합 PR 수" in text


def test_다른_날과_같은_값으로_최저인_지표는_평소와_다른_것에_싣지_않고_평소대로에_적는다() -> None:
    tied = Metric("unreadable", "읽지 못한 기록 줄", "int", (0, 0, 0, 0, 0, 0, 5, 0), None)
    text, _, warnings = render(자료(metrics=(지표(alarm="1.76배"), tied)), 메모(), {}, "summary")
    assert "| 읽지 못한 기록 줄 |" not in text
    assert "**평소대로:** 읽지 못한 기록 줄" in text
    assert not [w for w in warnings if "unreadable" in w]


def test_평소와_다른_지표에_원인이_없으면_원인_모름으로_적고_경고한다() -> None:
    text, _, warnings = render(자료(), 메모(causes={}), {}, "summary")
    assert "| 환산 비용 | $856 | $486 | +76% | 원인 모름 |" in text
    assert warnings == ["평소와 다른 지표 cost(환산 비용)에 메모의 causes가 없다(모르면 원인 모름)"]


def test_오늘_정할_것은_질문_추천_근거_확인할_수치다() -> None:
    state = {"commit-wait": Seen(date(2026, 10, 18), 400.0, CHECK)}
    text, new_state, _ = render(자료(), 메모(decisions=(결정(),)), state, "summary")
    block = text.split("## 오늘 정할 것", 1)[1].split("## 평소와 다른 것", 1)[0]
    assert "**1. 커밋할 때 도는 검사를 줄일까요?**" in block
    assert "- 추천: 오래 걸리는 것을 CI에만 둘지 살펴봅니다" in block
    assert "- 근거: 지난 7일 커밋 225번, 중앙값 6분 25초(작업 보고)" in block
    assert "- 확인할 수치: git commit 중앙값 400.0초 → 385.2초(효과 확인됨)" in block
    assert new_state == {"commit-wait": Seen(date(2026, 10, 18), 385.2, CHECK)}


def test_정할_것이_셋을_넘으면_경고한다() -> None:
    decisions = tuple(결정(id=str(i)) for i in range(4))
    _, _, warnings = render(자료(), 메모(decisions=decisions), {}, "summary")
    assert warnings == ["오늘 정할 것이 4개로 3개를 넘는다(오늘 손써야 하는 것만 남긴다)"]


def test_분야별_보고는_제안_상태를_내지_않는다() -> None:
    _, new_state, _ = render(자료(), 메모(decisions=(결정(),)), {}, "cost")
    assert new_state is None


def test_오늘_나오는_분야별_보고는_월요일에만_주간_보고를_더한다() -> None:
    sunday, _, _ = render(자료(day=date(2026, 10, 18)), 메모(), {}, "summary")
    assert "작업 환경 보고(10:00), 실험 보고(10:15)" in sunday
    monday, _, _ = render(자료(), 메모(), {}, "summary")
    assert "작업 환경 보고와 실험 보고는 월요일에 나옵니다" in monday


# 작업 표기


def test_모델이_쓴_글의_작업_번호는_처음에만_이름과_내용을_붙이고_뒤에서는_이름만_붙인다() -> None:
    todos = (Todo("PR 정리", "#301 뒤에 남은 브랜치를 지운다"), Todo("다시", "#301 을 본다"))
    text, _, _ = render(자료(), 메모(todos=todos), {}, "summary")
    assert (
        f"- [ ] **PR 정리**: #301 Ctrl-C 판정 안정화({CONTENT}) 뒤에 남은 브랜치를 지운다" in text
    )
    assert "- [ ] **다시**: #301 Ctrl-C 판정 안정화 을 본다" in text


def test_이미_이름이_붙은_작업_번호에는_이름을_다시_붙이지_않고_처음이면_내용만_붙인다() -> None:
    todo = Todo("PR 정리", "#301 Ctrl-C 판정 안정화 뒤에 남은 브랜치")
    text, _, _ = render(자료(), 메모(todos=(todo,)), {}, "summary")
    assert f"#301 Ctrl-C 판정 안정화({CONTENT}) 뒤에 남은 브랜치" in text
    assert "Ctrl-C 판정 안정화 Ctrl-C" not in text


def test_글_속_대기열_번호에도_이름과_내용을_붙인다() -> None:
    todo = Todo("정리", "대기열 238 은 사람 몫이다")
    text, _, _ = render(자료(), 메모(todos=(todo,)), {}, "summary")
    assert (
        "대기열 238 남은 워크트리 정리(정리 도구가 지우지 못한 워크트리 여섯) 은 사람 몫이다"
        in text
    )


def test_대기열_뒤의_수에_세는_말이_붙으면_행_번호로_보지_않는다() -> None:
    todo = Todo("정리", "대기열 3회 이상 행이 12개이고 대기열 4개가 사람 몫이다")
    text, _, warnings = render(자료(), 메모(todos=(todo,)), {}, "summary")
    assert "대기열 3회 이상 행이 12개이고 대기열 4개가 사람 몫이다" in text
    assert warnings == []


def test_이름을_모르는_작업_번호는_이름_없음을_붙이고_경고한다() -> None:
    notes = 메모(
        prs={318: Named("바로가기로 실행 읽기", "단축 아이콘의 실행 경로를 읽는다")},
        todos=(Todo("이어 가기", "#318 뒤에 #999 를 본다"),),
    )
    text, _, warnings = render(자료(), notes, {}, "summary")
    expected = f"#318 바로가기로 실행 읽기(단축 아이콘의 실행 경로를 읽는다) 뒤에 #999 {NO_NAME} 를"
    assert expected in text
    assert any("#999" in w for w in warnings)
    assert not any("#318" in w for w in warnings)


def test_메모에_내용이_없는_작업은_경고한다() -> None:
    notes = 메모(prs={318: Named("바로가기로 실행 읽기", "")}, todos=(Todo("이어 가기", "#318"),))
    _, _, warnings = render(자료(), notes, {}, "summary")
    assert any("#318" in w for w in warnings)


def test_작업_번호_바로_뒤에_조사가_붙으면_경고한다() -> None:
    # 이름을 끼우면 "#297 리뷰 보고 옮기기은"처럼 받침과 조사가 어긋난다
    todo = Todo("PR 정리", "#301은 끝났고 (#301) 뒤의 일도 끝났다")
    _, _, warnings = render(자료(), 메모(todos=(todo,)), {}, "summary")
    assert [w for w in warnings if "조사" in w] == [
        "작업 번호 바로 뒤에 조사가 붙었다(이름을 끼우면 받침이 어긋난다): #301"
    ]


def test_대기열_할_일은_제목에_행_번호와_회차와_이름을_넣고_처음이면_내용을_붙인다() -> None:
    todos = (
        Todo("", "주 체크아웃에서 직접 보고 지운다", queue=238),
        Todo("다시", "대기열 238 본다"),
    )
    text, _, _ = render(자료(), 메모(todos=todos), {}, "summary")
    assert (
        "- [ ] **대기열 238 (11회차) 남은 워크트리 정리**(정리 도구가 지우지 못한 워크트리 여섯):"
        " 주 체크아웃에서 직접 보고 지운다" in text
    )
    assert "- [ ] **다시**: 대기열 238 남은 워크트리 정리 본다" in text


def test_할_일의_까닭이_두_문장_이상이면_경고한다() -> None:
    long = Todo("정리", "남은 워크트리를 지운다. 그다음 브랜치도 지운다.")
    short = Todo("정리", "남은 워크트리를 지워 디스크를 비운다.")
    _, _, warned = render(자료(), 메모(todos=(long,)), {}, "summary")
    _, _, quiet = render(자료(), 메모(todos=(short,)), {}, "summary")
    assert any("할 일" in w and "정리" in w for w in warned)
    assert quiet == []


def test_못_보는_것_이어_쓴_대기열_번호는_앞_번호에만_이름을_붙인다() -> None:
    todo = Todo("정리", "대기열 238·243 은 사람 몫이다")
    text, _, warnings = render(자료(), 메모(todos=(todo,)), {}, "summary")
    assert (
        "대기열 238 남은 워크트리 정리(정리 도구가 지우지 못한 워크트리 여섯)·243 은 사람 몫이다"
        in text
    )
    assert warnings == []


def test_못_보는_것_세는_말이_붙은_대기열_번호는_놓친다() -> None:
    todo = Todo("정리", "대기열 238건 은 사람 몫이다")
    text, _, warnings = render(자료(), 메모(todos=(todo,)), {}, "summary")
    assert "대기열 238건 은 사람 몫이다" in text
    assert warnings == []


def test_못_보는_것_다로_끝나지_않는_문장은_세지_않는다() -> None:
    todo = Todo("정리", "워크트리를 지움. 브랜치도 지울까? 디스크를 비운다.")
    _, _, warnings = render(자료(), 메모(todos=(todo,)), {}, "summary")
    assert warnings == []


# 제안 상태


def test_지난_보고에_없던_제안은_신규다() -> None:
    assert check_state(None, 385.2, "down") == "신규"


def test_지난_값보다_바라는_쪽으로_움직였으면_효과_확인됨이고_아니면_수집_안_됨이다() -> None:
    prev = Seen(date(2026, 10, 18), 400.0)
    assert check_state(prev, 385.2, "down") == "효과 확인됨"
    assert check_state(prev, 385.2, "up") == "진행 중·보류는 수집 안 됨"


def test_지난_값이나_오늘_값이_없으면_효과를_판정하지_않는다() -> None:
    prev = Seen(date(2026, 10, 17), None)
    assert check_state(prev, 385.2, "down") == "진행 중·보류는 수집 안 됨"


def test_확인할_수치는_지난_값과_오늘_값을_나란히_적는다() -> None:
    values = {"k": Value("git commit 중앙값", 385.2, "초")}
    assert (
        check_text(결정(check="k"), values, Seen(DAY, 400.0))
        == "git commit 중앙값 400.0초 → 385.2초"
    )
    assert check_text(결정(check="k"), values, None) == "git commit 중앙값 385.2초"


def test_모으지_않은_값을_고른_제안은_수집_안_됨이다() -> None:
    assert check_text(결정(check="없는 키"), {}, None) == f"없는 키 {UNCOLLECTED}"


def test_처음_낸_제안의_시작일은_보고하는_날이다() -> None:
    _, new_state, _ = render(자료(), 메모(decisions=(결정(),)), {}, "summary")
    assert new_state == {"commit-wait": Seen(DAY, 385.2, CHECK)}


def test_확인할_수치의_열쇠가_바뀐_제안은_지난_값과_견주지_않는다() -> None:
    state = {"commit-wait": Seen(date(2026, 10, 18), 400.0, "cmd:다른 것:median_s")}
    text, new_state, _ = render(자료(), 메모(decisions=(결정(),)), state, "summary")
    assert "- 확인할 수치: git commit 중앙값 385.2초(진행 중·보류는 수집 안 됨)" in text
    assert new_state == {"commit-wait": Seen(date(2026, 10, 18), 385.2, CHECK)}


def test_제안_상태는_확인할_수치의_열쇠와_함께_쓰고_다시_읽는다() -> None:
    state = {"commit-wait": Seen(DAY, 385.2, CHECK)}
    assert read_state(state_json(state)) == state


def test_앞_날의_종합_메모가_고른_확인할_수치의_열쇠를_읽는다(tmp_path: Path) -> None:
    # 수집 도구가 이 열쇠의 값을 순위와 상관없이 남겨야 제안이 효과 확인됨에 닿는다
    def 메모_파일(day: str, *checks: str) -> None:
        decisions = [{"id": c, "check": c} for c in checks]
        text = json.dumps({"decisions": decisions}, ensure_ascii=False)
        (tmp_path / f"{day}.summary.notes.json").write_text(text, encoding="utf-8")

    메모_파일("2026-10-17", "cmd:옛것:median_s")
    메모_파일("2026-10-18", "cmd:Bash: gh:median_s", "read:CLAUDE.md:chars")
    메모_파일("2026-10-19", "cmd:오늘:median_s")
    assert latest_checks(tmp_path, DAY) == {"cmd:Bash: gh:median_s", "read:CLAUDE.md:chars"}
    assert latest_checks(tmp_path, date(2026, 10, 17)) == frozenset()


# JSON과 CLI


def test_다른_형식의_수집_JSON은_읽지_않는다() -> None:
    j = 자료().to_json()
    assert isinstance(j, dict)
    j["format"] = 2
    with pytest.raises(ValueError, match="형식"):
        Data.of(j)


def test_수집_JSON은_쓰고_다시_읽어도_같다() -> None:
    data = 자료(sections=(절(표(ROW), lines=("- 줄",)),))
    assert Data.of(data.to_json()) == data
    missing = 자료(limit="한도 기록이 없다")
    assert Data.of(missing.to_json()) == missing


def test_메모_JSON의_빠진_칸은_빈_값으로_읽는다() -> None:
    notes = Notes.of({"prs": {"301": {"name": "이름", "content": "내용"}}})
    assert notes.prs == {301: Named("이름", "내용", "")}
    assert (notes.todos, notes.decisions, notes.heads, notes.blocks) == ((), (), {}, {})


def test_메모_JSON의_머리와_블록과_원인을_읽는다() -> None:
    notes = Notes.of(
        {
            "heads": {"cost": {"conclusion": "결론", "decide": ["질문"]}},
            "blocks": {"cost.models": {"conclusion": "a", "so_what": "b", "todo": "c"}},
            "causes": {"cost": "원인"},
        }
    )
    assert notes.heads == {"cost": Head("결론", ("질문",))}
    assert notes.blocks == {"cost.models": Block("a", "b", "c")}
    assert notes.causes == {"cost": "원인"}


def _자료_파일(tmp_path: Path) -> None:
    data = json.dumps(자료(sections=(절(표(ROW)),)).to_json(), ensure_ascii=False)
    (tmp_path / "2026-10-19.data.json").write_text(data, encoding="utf-8")


def test_보고마다_그_보고의_메모를_읽어_그_보고의_파일을_쓰고_종합만_상태를_쓴다(
    tmp_path: Path,
) -> None:
    _자료_파일(tmp_path)
    assert main(["--reports", str(tmp_path), "--day", "2026-10-19", "--report", "work"]) == 0
    assert (tmp_path / "2026-10-19.work.md").read_text("utf-8").startswith("# 작업 보고")
    assert not (tmp_path / "2026-10-19.state.json").exists()
    assert main(["--reports", str(tmp_path), "--day", "2026-10-19", "--report", "summary"]) == 0
    assert (tmp_path / "2026-10-19.summary.md").read_text("utf-8").startswith("# 종합 보고")
    assert (tmp_path / "2026-10-19.state.json").exists()


def test_메모_JSON을_읽지_못하면_경고로_알리고_빈_메모로_그린다(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # 예약 작업은 `경고:` 줄마다 메모를 고친다. 접두가 없으면 문법 오류를 지나친다
    _자료_파일(tmp_path)
    notes = tmp_path / "2026-10-19.work.notes.json"
    notes.write_text('{"prs": {"301": {"name": "a",}}}', "utf-8")
    assert main(["--reports", str(tmp_path), "--day", "2026-10-19", "--report", "work"]) == 0
    first = capsys.readouterr().err.splitlines()[0]
    assert first.startswith("경고: 메모 JSON을 읽지 못해 빈 메모로 그렸다(메모 전체를 다시 쓴다):")


def test_보고나_상태_파일을_쓰지_못하면_트레이스백_없이_종료_2다(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # 예약 작업은 종료 코드와 stderr 한 줄로 실패를 가른다. 같은 이름의 폴더가 쓰기를 막는다
    _자료_파일(tmp_path)
    (tmp_path / "2026-10-19.work.md").mkdir()
    assert main(["--reports", str(tmp_path), "--day", "2026-10-19", "--report", "work"]) == 2
    assert capsys.readouterr().err.startswith("보고 파일을 쓰지 못했다:")
    (tmp_path / "2026-10-19.state.json").mkdir()
    assert main(["--reports", str(tmp_path), "--day", "2026-10-19", "--report", "summary"]) == 2
    assert capsys.readouterr().err.startswith("보고 파일을 쓰지 못했다:")


def test_JSON_풀이는_기대한_꼴이_아니면_빈_것이나_None이다() -> None:
    # 수집 도구와 그리기 도구가 함께 쓴다. 꼴이 틀린 칸은 실패로 끝내지 않고 비운다
    assert (json_obj({"a": 1}), json_obj([1])) == ({"a": 1}, {})
    assert (json_list([1]), json_list({"a": 1})) == ([1], [])
    assert (json_str("가"), json_str(3)) == ("가", "")
    # 참거짓은 파이썬에서 int 의 하위 형이지만 수로 읽지 않는다
    assert (json_int(3), json_int(json.loads("true")), json_int(3.0)) == (3, None, None)


def test_JSON_시각은_시간대가_없으면_UTC로_읽고_읽지_못하면_None이다() -> None:
    assert json_time("2026-10-19T09:00:00") == datetime(2026, 10, 19, 9, tzinfo=UTC)
    kst = timezone(timedelta(hours=9))
    assert json_time("2026-10-19T09:00:00+09:00") == datetime(2026, 10, 19, 9, tzinfo=kst)
    assert (json_time("어제"), json_time(None), json_time(1)) == (None, None, None)
