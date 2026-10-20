"""tools/morning_report.py 검증. 수집 JSON(`Data`)과 메모 JSON(`Notes`)은 시험마다 작게 지어 넣는다.

수치는 2026-10-19 아침 보고에서 옮겨 줄였다(환산 비용 856.36, 7일 중앙값 485.69).
"""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import date
from pathlib import Path

import pytest
from tools.morning_report import (
    LOOKUP_FAILED,
    NO_CONTENT,
    NO_NAME,
    UNCOLLECTED,
    Data,
    Metric,
    Named,
    Notes,
    Pr,
    Proposal,
    QueueRow,
    Section,
    Seen,
    Table,
    Todo,
    Value,
    check_text,
    latest_checks,
    main,
    metric_row,
    proposal_state,
    read_state,
    render,
    sparkline,
    state_json,
    table_lines,
    verdict,
)

DAY = date(2026, 10, 19)
COST = (1356.51, 1297.73, 132.08, 485.69, 1545.33, 431.90, 50.85, 856.36)


def 지표(
    key: str = "cost", series: tuple[float | None, ...] = COST, alarm: str | None = None
) -> Metric:
    return Metric(key, "환산 비용", "money", series, alarm)


def 자료(**kw: object) -> Data:
    base = Data(
        day=DAY,
        made="2026-10-20T09:10:00+09:00",
        metrics=(지표(alarm="1.76배"),),
        values={"cmd:git commit:median_s": Value("git commit 중앙값", 385.2, "초")},
        sections=(),
        prs={301: Pr(301, "test: 부하에서 흔들린 Ctrl-C 판정", "본문", "chore/mutate-ctrl-c")},
        queue={238: QueueRow(238, 11, human=True, what="남은 워크트리 여섯")},
        branches={},
        journal="",
        alarms=1,
    )
    return replace(base, **kw)


def 메모(**kw: object) -> Notes:
    base = Notes(
        prs={
            301: Named(
                "Ctrl-C 판정 안정화", "부하에서 흔들린 판정과 시간 제한을 고쳤다", "부하 시험"
            )
        },
        queue={238: Named("남은 워크트리 정리", "정리 도구가 지우지 못한 워크트리 여섯")},
        branches={},
        todos=(),
        proposals=(),
        remarks={},
        next=(),
    )
    return replace(base, **kw)


def 제안(**kw: object) -> Proposal:
    base = Proposal(
        id="commit-wait",
        title="커밋 대기 줄이기",
        basis="상세 4의 git commit",
        effect="커밋마다 기다리는 시간이 준다",
        difficulty="어려움",
        decision="ADR 0035 개정",
        check="cmd:git commit:median_s",
        better="down",
        change=("검사를 나눈다",),
    )
    return replace(base, **kw)


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


def test_어제_값이_없으면_판정하지_않는다() -> None:
    assert verdict((1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, None), None) == "-"


def test_지표_행은_어제_전날_7일_추이_앞_7일_중앙값_판정이다() -> None:
    # 2026-10-19 보고의 행 그대로다
    row = metric_row(지표(alarm="1.76배"))
    assert row == ["환산 비용", "$856.36", "$50.85", "▇▁▃█▃▁▅", "$485.69", "⚠ 경보 (1.76배)"]


def test_지표를_모으지_못했으면_어제_칸에_수집_안_됨을_적는다() -> None:
    m = Metric("prs", "병합 PR 수", "int", (), None)
    assert metric_row(m) == ["병합 PR 수", UNCOLLECTED, "-", "", "-", "-"]


def test_앞_7일_중앙값은_값이_없는_날을_빼고_센다() -> None:
    m = Metric("prs", "PR당 비용", "money", (None, None, 2.0, None, 4.0, None, 6.0, 1.0), None)
    assert metric_row(m)[4] == "$4.00"


def test_표의_칸에_든_세로줄과_줄바꿈은_표를_깨지_않게_바꾼다() -> None:
    lines = table_lines(Table(("이름", "값"), "lr", (("a|b", "1\n2"),)))
    assert lines == ["| 이름 | 값 |", "|---|--:|", "| a\\|b | 1 2 |"]


def test_지난_보고에_없던_제안은_신규다() -> None:
    assert proposal_state(None, 385.2, "down") == "신규"


def test_지난_값보다_바라는_쪽으로_움직였으면_효과_확인됨이고_아니면_수집_안_됨이다() -> None:
    # 상태는 신규·진행 중·보류·효과 확인됨 넷이고, 진행 중과 보류를 가를 기록이 없다
    prev = Seen(date(2026, 10, 18), 400.0)
    assert proposal_state(prev, 385.2, "down") == "효과 확인됨"
    assert proposal_state(prev, 385.2, "up") == "(진행 중·보류는 수집 안 됨)"


def test_지난_값이나_오늘_값이_없으면_효과를_판정하지_않는다() -> None:
    prev = Seen(date(2026, 10, 17), None)
    assert proposal_state(prev, 385.2, "down") == "(진행 중·보류는 수집 안 됨)"


def test_확인할_수치는_지난_값과_오늘_값을_나란히_적는다() -> None:
    values = {"k": Value("git commit 중앙값", 385.2, "초")}
    assert (
        check_text(제안(check="k"), values, Seen(DAY, 400.0))
        == "git commit 중앙값 400.0초 → 385.2초"
    )
    assert check_text(제안(check="k"), values, None) == "git commit 중앙값 385.2초"


def test_모으지_않은_값을_고른_제안은_수집_안_됨이다() -> None:
    assert check_text(제안(check="없는 키"), {}, None) == f"없는 키 {UNCOLLECTED}"


def 상세(*rows: tuple[str, ...], number: int = 4, lines: tuple[str, ...] = ()) -> Section:
    table = Table(("PR", "작업 이름", "작업 내용"), "lll", rows)
    return Section(number, "비싼 작업과 오래 걸린 명령", (table,), lines, "task 통계")


def test_작업은_처음_나온_표에만_내용을_적고_뒤에서는_그_절을_가리킨다() -> None:
    row = ("#301", "{{name:301}}", "{{content:301}}")
    sections = (상세(row), 상세(row, number=6))
    text, _, warnings = render(자료(sections=sections), 메모(), {})
    assert "| #301 | Ctrl-C 판정 안정화 | 부하에서 흔들린 판정과 시간 제한을 고쳤다 |" in text
    assert "| #301 | Ctrl-C 판정 안정화 | → 상세 4 |" in text
    assert warnings == []


def test_이름을_적지_않은_작업은_이름_없음으로_그리고_경고한다() -> None:
    row = ("#301", "{{name:301}}", "{{content:301}}")
    text, _, warnings = render(자료(sections=(상세(row),)), 메모(prs={}), {})
    assert f"| #301 | {NO_NAME} | {NO_CONTENT} |" in text
    assert any("301" in w for w in warnings)


def test_제목을_가져오지_못한_작업은_제목_조회_실패로_적는다() -> None:
    row = ("#302", "{{name:302}}", "{{content:302}}")
    data = 자료(sections=(상세(row),), prs={302: Pr(302, None, "", "")})
    text, _, _ = render(data, 메모(), {})
    assert f"| #302 | {LOOKUP_FAILED} | {LOOKUP_FAILED} |" in text


CONTENT = "부하에서 흔들린 판정과 시간 제한을 고쳤다"


def test_모델이_쓴_글의_작업_번호는_처음에만_이름과_내용을_붙이고_뒤에서는_이름만_붙인다() -> None:
    todos = (Todo("PR 정리", "#301 뒤에 남은 브랜치를 지운다"), Todo("다시", "#301 을 본다"))
    text, _, _ = render(자료(), 메모(todos=todos), {})
    assert (
        f"- [ ] **PR 정리**: #301 Ctrl-C 판정 안정화({CONTENT}) 뒤에 남은 브랜치를 지운다" in text
    )
    assert "- [ ] **다시**: #301 Ctrl-C 판정 안정화 을 본다" in text


def test_이미_이름이_붙은_작업_번호에는_이름을_다시_붙이지_않고_처음이면_내용만_붙인다() -> None:
    todo = Todo("PR 정리", "#301 Ctrl-C 판정 안정화 뒤에 남은 브랜치")
    text, _, _ = render(자료(), 메모(todos=(todo,)), {})
    assert f"#301 Ctrl-C 판정 안정화({CONTENT}) 뒤에 남은 브랜치" in text
    assert "Ctrl-C 판정 안정화 Ctrl-C" not in text


def test_표에서_내용을_적은_작업은_뒤의_글에서_이름만_붙인다() -> None:
    row = ("#301", "{{name:301}}", "{{content:301}}")
    data = 자료(sections=(상세(row, lines=("- 인계: {{ref:301}} 두 번",)),))
    text, _, _ = render(data, 메모(remarks={4: ("#301 은 길었다",)}), {})
    assert "- 인계: #301 Ctrl-C 판정 안정화 두 번" in text
    assert "- #301 Ctrl-C 판정 안정화 은 길었다" in text


def test_수집_도구가_쓴_줄의_작업도_처음에는_이름과_내용을_적는다() -> None:
    data = 자료(sections=(상세(lines=("- 인계가 난 티켓: {{ref:301}} 인계 2번",)),))
    text, _, _ = render(data, 메모(), {})
    assert f"- 인계가 난 티켓: #301 Ctrl-C 판정 안정화({CONTENT}) 인계 2번" in text


def test_글_속_대기열_번호에도_이름과_내용을_붙인다() -> None:
    notes = 메모(remarks={5: ("대기열 238 은 사람 몫이다",)})
    text, _, _ = render(자료(sections=(상세(number=5),)), notes, {})
    assert (
        "- 대기열 238 남은 워크트리 정리(정리 도구가 지우지 못한 워크트리 여섯) 은 사람 몫이다"
        in text
    )


def test_대기열_뒤의_수에_세는_말이_붙으면_행_번호로_보지_않는다() -> None:
    notes = 메모(remarks={5: ("대기열 3회 이상 행이 12개이고 대기열 4개가 사람 몫이다",)})
    text, _, warnings = render(자료(sections=(상세(number=5),)), notes, {})
    assert "- 대기열 3회 이상 행이 12개이고 대기열 4개가 사람 몫이다" in text
    assert warnings == []


def test_이름을_모르는_작업_번호는_이름_없음을_붙이고_경고한다() -> None:
    # "모든 PR 번호 옆에 이름"을 지키려면 모델 글의 번호도 빠짐없이 대야 한다
    notes = 메모(
        prs={318: Named("바로가기로 실행 읽기", "단축 아이콘의 실행 경로를 읽는다")},
        todos=(Todo("이어 가기", "#318 뒤에 #999 를 본다"),),
    )
    text, _, warnings = render(자료(), notes, {})
    expected = f"#318 바로가기로 실행 읽기(단축 아이콘의 실행 경로를 읽는다) 뒤에 #999 {NO_NAME} 를"
    assert expected in text
    assert any("#999" in w for w in warnings)
    assert not any("#318" in w for w in warnings)


def test_메모에_내용이_없는_작업은_경고한다() -> None:
    notes = 메모(prs={318: Named("바로가기로 실행 읽기", "")}, todos=(Todo("이어 가기", "#318"),))
    _, _, warnings = render(자료(), notes, {})
    assert any("#318" in w for w in warnings)


def test_작업_번호_바로_뒤에_조사가_붙으면_경고한다() -> None:
    # 이름을 끼우면 "#297 리뷰 보고 옮기기은"처럼 받침과 조사가 어긋난다
    todo = Todo("PR 정리", "#301은 끝났고 (#301) 뒤의 일도 끝났다")
    _, _, warnings = render(자료(), 메모(todos=(todo,)), {})
    assert [w for w in warnings if "조사" in w] == [
        "작업 번호 바로 뒤에 조사가 붙었다(이름을 끼우면 받침이 어긋난다): #301"
    ]


def test_대기열_할_일은_제목에_행_번호와_회차와_이름을_넣고_처음이면_내용을_붙인다() -> None:
    todo = Todo("", "주 체크아웃에서 직접 보고 지운다", queue=238)
    notes = 메모(todos=(todo,), remarks={5: ("대기열 238 은 사람 몫이다",)})
    text, _, _ = render(자료(sections=(상세(number=5),)), notes, {})
    assert (
        "- [ ] **대기열 238 (11회차) 남은 워크트리 정리**(정리 도구가 지우지 못한 워크트리 여섯):"
        " 주 체크아웃에서 직접 보고 지운다" in text
    )
    assert "- 대기열 238 남은 워크트리 정리 은 사람 몫이다" in text


def test_머리_줄은_경보와_할_일과_제안의_수를_센다() -> None:
    notes = 메모(todos=(Todo("a", "b"), Todo("c", "d")), proposals=(제안(),))
    text, _, _ = render(자료(), notes, {})
    assert text.splitlines()[:2] == [
        "# 일일 보고 · 2026-10-19",
        "**경보 1건 · 직접 하실 일 2건 · 개선 제안 1건**",
    ]


def test_할_일의_까닭이_두_문장_이상이면_경고한다() -> None:
    long = Todo("정리", "남은 워크트리를 지운다. 그다음 브랜치도 지운다.")
    short = Todo("정리", "남은 워크트리를 지워 디스크를 비운다.")
    _, _, warned = render(자료(), 메모(todos=(long,)), {})
    _, _, quiet = render(자료(), 메모(todos=(short,)), {})
    assert any("할 일" in w and "정리" in w for w in warned)
    assert quiet == []


def test_제안의_난이도가_쉬움_보통_어려움_밖이면_경고한다() -> None:
    _, _, warned = render(자료(), 메모(proposals=(제안(difficulty="낮음"),)), {})
    _, _, quiet = render(자료(), 메모(proposals=(제안(difficulty="어려움"),)), {})
    assert any("난이도" in w and "낮음" in w for w in warned)
    assert quiet == []


def test_상세_머리에_수집_JSON과_수집_시각과_순간_값의_뜻을_적는다() -> None:
    text, _, _ = render(자료(), 메모(), {})
    after = text.split("## 상세", 1)[1].strip().splitlines()[0]
    assert "`2026-10-19.data.json`" in after
    assert "2026-10-20T09:10:00+09:00" in after
    assert "그 시각의 값" in after


def test_머리_줄의_경보_수는_지표_표의_경보_줄이_아니라_수집_도구가_센_수다() -> None:
    # `alarms_of`는 단가표에 없는 모델과 읽지 못한 줄을 한 경보로 센다
    text, _, _ = render(자료(alarms=2), 메모(), {})
    assert text.splitlines()[1].startswith("**경보 2건 ·")


def test_다른_형식의_수집_JSON은_읽지_않는다() -> None:
    j = 자료().to_json()
    assert isinstance(j, dict)
    j["format"] = 1
    with pytest.raises(ValueError, match="형식"):
        Data.of(j)


def test_병합_PR의_분류는_메모의_묶음이고_없으면_제목_앞머리다() -> None:
    row = ("{{group:301}}", "#301", "{{name:301}}")
    data = 자료(sections=(상세(row, number=6),))
    grouped, _, _ = render(data, 메모(), {})
    assert "| 부하 시험 | #301 | Ctrl-C 판정 안정화 |" in grouped
    plain, _, _ = render(data, 메모(prs={301: Named("Ctrl-C 판정 안정화", "내용")}), {})
    assert "| test | #301 | Ctrl-C 판정 안정화 |" in plain


def test_앞_날의_메모가_고른_확인할_수치의_열쇠를_읽는다(tmp_path: Path) -> None:
    # 수집 도구가 이 열쇠의 값을 순위와 상관없이 남겨야 제안이 효과 확인됨에 닿는다
    def 메모_파일(day: str, *checks: str) -> None:
        proposals = [{"id": c, "check": c} for c in checks]
        text = json.dumps({"proposals": proposals}, ensure_ascii=False)
        (tmp_path / f"{day}.notes.json").write_text(text, encoding="utf-8")

    메모_파일("2026-10-17", "cmd:옛것:median_s")
    메모_파일("2026-10-18", "cmd:Bash: gh:median_s", "read:CLAUDE.md:chars")
    메모_파일("2026-10-19", "cmd:오늘:median_s")
    assert latest_checks(tmp_path, DAY) == {"cmd:Bash: gh:median_s", "read:CLAUDE.md:chars"}
    assert latest_checks(tmp_path, date(2026, 10, 17)) == frozenset()


def test_절의_차례는_핵심_지표_할_일_제안_그리고_접힌_상세다() -> None:
    text, _, _ = render(자료(sections=(상세(number=1),)), 메모(), {})
    order = [text.index(h) for h in ("## 핵심 지표", "## 직접 하실 일", "## 개선 제안", "## 상세")]
    assert order == sorted(order)
    assert "<details><summary>1. 비싼 작업과 오래 걸린 명령</summary>" in text
    assert text.index("## 상세") < text.index("<details><summary>1.")


def test_상세_절의_끝에_원본을_한_줄로_적는다() -> None:
    text, _, _ = render(자료(sections=(상세(),)), 메모(), {})
    body = text.split("<summary>4. 비싼 작업과 오래 걸린 명령</summary>", 1)[1]
    assert body.split("</details>", 1)[0].rstrip().splitlines()[-1] == "원본: task 통계"


def test_상세_절의_목록이_다섯_줄을_넘으면_경고한다() -> None:
    lines = tuple(f"- 줄 {i}" for i in range(4))
    notes = 메모(remarks={4: ("해석 하나", "해석 둘")})
    _, _, warnings = render(자료(sections=(상세(lines=lines),)), notes, {})
    assert any("상세 4" in w for w in warnings)


def test_제안의_상태와_확인할_수치는_지난_상태에서_잇고_오늘_상태를_낸다() -> None:
    notes = 메모(proposals=(제안(),))
    state = {"commit-wait": Seen(date(2026, 10, 18), 400.0, CHECK)}
    text, new_state, _ = render(자료(), notes, state)
    assert "| 1 | 커밋 대기 줄이기 |" in text
    assert "git commit 중앙값 400.0초 → 385.2초 | 효과 확인됨 |" in text
    assert new_state == {"commit-wait": Seen(date(2026, 10, 18), 385.2, CHECK)}


def test_처음_낸_제안의_시작일은_보고하는_날이다() -> None:
    _, new_state, _ = render(자료(), 메모(proposals=(제안(),)), {})
    assert new_state == {"commit-wait": Seen(DAY, 385.2, CHECK)}


CHECK = "cmd:git commit:median_s"


def test_확인할_수치의_열쇠가_바뀐_제안은_지난_값과_견주지_않는다() -> None:
    # 같은 제안을 다른 지표로 다시 내면 다른 지표끼리 견주게 된다
    state = {"commit-wait": Seen(date(2026, 10, 18), 400.0, "cmd:다른 것:median_s")}
    text, new_state, _ = render(자료(), 메모(proposals=(제안(),)), state)
    assert "| git commit 중앙값 385.2초 | (진행 중·보류는 수집 안 됨) |" in text
    assert new_state == {"commit-wait": Seen(date(2026, 10, 18), 385.2, CHECK)}


def test_제안_상태는_확인할_수치의_열쇠와_함께_쓰고_다시_읽는다() -> None:
    state = {"commit-wait": Seen(DAY, 385.2, CHECK)}
    assert read_state(state_json(state)) == state


def test_제안의_바꿀_것은_표_아래_접힌_곳에_적는다() -> None:
    text, _, _ = render(자료(), 메모(proposals=(제안(),)), {})
    details = text.split("<details><summary>제안별 바꿀 것</summary>", 1)[1].split("</details>")[0]
    assert "**1. 커밋 대기 줄이기**" in details
    assert "- 검사를 나눈다" in details


def test_수집_JSON은_쓰고_다시_읽어도_같다() -> None:
    table = Table(("a", "b"), "lr", (("x", "1"),))
    data = 자료(sections=(Section(1, "토큰 사용", (table,), ("- 줄",), "장부"),))
    assert Data.of(data.to_json()) == data


def test_메모_JSON의_빠진_칸은_빈_값으로_읽는다() -> None:
    notes = Notes.of({"prs": {"301": {"name": "이름", "content": "내용"}}})
    assert notes.prs == {301: Named("이름", "내용", "")}
    assert notes.todos == ()
    assert notes.proposals == ()


def test_메모_JSON을_읽지_못하면_경고로_알리고_빈_메모로_그린다(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # 예약 작업은 `경고:` 줄마다 메모를 고친다. 접두가 없으면 문법 오류를 지나친다
    data = json.dumps(자료().to_json(), ensure_ascii=False)
    (tmp_path / "2026-10-19.data.json").write_text(data, encoding="utf-8")
    (tmp_path / "2026-10-19.notes.json").write_text('{"prs": {"301": {"name": "a",}}}', "utf-8")
    assert main(["--reports", str(tmp_path), "--day", "2026-10-19"]) == 0
    first = capsys.readouterr().err.splitlines()[0]
    assert first.startswith("경고: 메모 JSON을 읽지 못해 빈 메모로 그렸다(메모 전체를 다시 쓴다):")


def test_목록_경고는_수집_줄과_메모_줄을_나눠_메모가_쓸_줄_수를_알린다() -> None:
    lines = tuple(f"- 줄 {i}" for i in range(4))
    notes = 메모(remarks={4: ("해석 하나", "해석 둘")})
    _, _, warnings = render(자료(sections=(상세(lines=lines),)), notes, {})
    assert warnings == [
        "상세 4의 목록이 6줄로 5줄을 넘는다(수집 4줄, 메모 2줄)."
        " 메모가 이 절에 쓸 수 있는 줄은 1줄이다"
    ]


def test_제안의_작업_내용은_문서에서_먼저_나오는_표_행에_붙는다() -> None:
    # 표의 행이 모두 바꿀 것보다 앞에 그려지므로, 바꿀 것은 표를 다 채운 뒤에 채운다
    first = 제안(change=("#301 을 나눈다",))
    second = 제안(id="b", title="둘째", basis="#301 의 기다림")
    text, _, _ = render(자료(), 메모(proposals=(first, second)), {})
    assert f"| #301 Ctrl-C 판정 안정화({CONTENT}) 의 기다림 |" in text
    assert "- #301 Ctrl-C 판정 안정화 을 나눈다" in text


def test_못_보는_것_이어_쓴_대기열_번호는_앞_번호에만_이름을_붙인다() -> None:
    notes = 메모(remarks={5: ("대기열 238·243 은 사람 몫이다",)})
    text, _, warnings = render(자료(sections=(상세(number=5),)), notes, {})
    assert (
        "- 대기열 238 남은 워크트리 정리(정리 도구가 지우지 못한 워크트리 여섯)·243 은 사람 몫이다"
        in text
    )
    assert warnings == []


def test_못_보는_것_세는_말이_붙은_대기열_번호는_놓친다() -> None:
    notes = 메모(remarks={5: ("대기열 238건 은 사람 몫이다",)})
    text, _, warnings = render(자료(sections=(상세(number=5),)), notes, {})
    assert "- 대기열 238건 은 사람 몫이다" in text
    assert warnings == []


def test_못_보는_것_다로_끝나지_않는_문장은_세지_않는다() -> None:
    todo = Todo("정리", "워크트리를 지움. 브랜치도 지울까? 디스크를 비운다.")
    _, _, warnings = render(자료(), 메모(todos=(todo,)), {})
    assert warnings == []
