"""tools/model_sweep_judge.py 검증. 표지 모집단, 배정, 판정하지 않는 조건, 주된 판정과 되풀이,
입력의 조건, 그리고 고정값이 두 사전 등록 절과 맞는지.

행은 `collect.py`가 쓰는 `branches.json`의 행을 본뜬 합성 행이다(`_행`). 기본값은 표지 모집단에 들고
기한 안에 병합된 브랜치이고, 테스트마다 한 칸만 바꾼다. 갈래가 정해진 이름은 도구의 `arm`으로
고른다(`arm`은 `test_model_sweep.py`가 손으로 셈한 첫 바이트로 고정한다).
"""

from __future__ import annotations

import re
from datetime import date, timedelta
from pathlib import Path

import pytest
from tools.model_sweep import BASE, COMPARISON, SWEPT, arm, prereg_kinds, prereg_section
from tools.model_sweep_judge import (
    ARM_RECORD,
    EARLY_PR,
    END_AT,
    JUDGE_AT,
    KEEP,
    LOWER,
    MODEL_OFF,
    N_K,
    NO_JUDGMENT,
    OTHER_DROP,
    RENAMED,
    RESAMPLES,
    ROUNDED_OVER,
    SEED,
    SWEEP_MARK,
    SWEEP_START,
    SWEEP_START_AT,
    TOP_SHARE_MIN,
    UNMERGED,
    Json,
    Row,
    blocking_reasons,
    boot_geomean_ratio,
    failed_names,
    input_problems,
    interventions,
    judge_kind,
    kind_problems,
    lower_verdict,
    split_arms,
    total_cost,
    verdicts,
)

_ROOT = Path(__file__).resolve().parents[2]
_PROBES = _ROOT / ".scratch" / "harness" / "probes"
_SWEEP_README = _PROBES / "model_sweep" / "README.md"
_COST_README = _PROBES / "session_cost" / "README.md"
_REGISTERED = {"구현": ("feature/",), "하네스": ("chore/", "claude/")}
_IN_WINDOW = "2026-10-20T00:00:00+00:00"


def _이름들(prefix: str, want: str, count: int) -> list[str]:
    names: list[str] = []
    i = 0
    while len(names) < count:
        name = f"{prefix}{i:03d}-합성"
        if arm(name) == want:
            names.append(name)
        i += 1
    return names


def _지시문(branch_line: str | None, model_line: str | None) -> dict[str, Json]:
    feats: dict[str, Json] = {"directive": True}
    if branch_line is not None:
        feats["branch_line"] = branch_line
    if model_line is not None:
        feats["model_line"] = model_line
    return feats


def _행(branch: str, **over: Json) -> Row:
    """표지 모집단에 들고 기한 안에 병합된 구현 브랜치. 모델 줄과 기록은 배정된 갈래의 것이다."""
    assigned = arm(branch)
    row: Row = {
        "branch": branch,
        "kind": "구현",
        "state": "MERGED",
        "created": _IN_WINDOW,
        "merged": "2026-10-21T00:00:00+00:00",
        "base_ref": "main",
        "msgs_main": 10,
        "msgs_sub": 2,
        "cost": 40.0,
        "cost_main": 32.0,
        "rework": 1,
        "interventions": 1,
        "queued_human": 0,
        "first_human_at": _IN_WINDOW,
        "top_model_effort": ARM_RECORD[assigned],
        "directive_features": _지시문(branch, f"{assigned}. {SWEEP_MARK}의 갈래"),
    }
    row.update(over)
    return row


def _갈래(want: str, count: int, **over: Json) -> list[Row]:
    prefix = "chore/" if over.get("kind") == "하네스" else "feature/"
    return [_행(name, **over) for name in _이름들(prefix, want, count)]


def _비용행(costs: list[float], **over: Json) -> list[Row]:
    return [_행(f"feature/{i:03d}-비용", cost=c, cost_main=c, **over) for i, c in enumerate(costs)]


# --- 표지 모집단과 배정 --------------------------------------------------------------------------


def test_표지_지시문의_병합된_브랜치는_배정된_갈래의_모집단에_든다() -> None:
    rows = _갈래(BASE, 2) + _갈래(COMPARISON, 3)
    s = split_arms(rows, "구현")
    assert [len(s.arms[BASE]), len(s.arms[COMPARISON])] == [2, 3]
    assert s.no_branch == 0
    assert all(sum(c.values()) == 0 for c in s.marks.values())


def test_배정은_실제로_돈_모델이_아니라_브랜치_줄의_이름으로_한다() -> None:
    (name,) = _이름들("feature/", BASE, 1)
    row = _행(name, top_model_effort=ARM_RECORD[COMPARISON])
    s = split_arms([row], "구현")
    assert s.arms[BASE] == [row]
    assert s.arms[COMPARISON] == []
    assert s.marks[BASE][MODEL_OFF] == 0


def test_모델_줄이_배정과_다르면_배정된_갈래에_두고_표지를_센다() -> None:
    (name,) = _이름들("feature/", BASE, 1)
    row = _행(name, directive_features=_지시문(name, f"{COMPARISON}. {SWEEP_MARK}의 갈래"))
    s = split_arms([row], "구현")
    assert s.arms[BASE] == [row]
    assert s.marks[BASE][MODEL_OFF] == 1


def test_브랜치_줄이_PR_머리와_다르면_줄의_이름으로_배정하고_표지를_센다() -> None:
    (line,) = _이름들("feature/", COMPARISON, 1)
    (head,) = _이름들("feature/", BASE, 1)
    row = _행(head, directive_features=_지시문(line, f"{COMPARISON}. {SWEEP_MARK}의 갈래"))
    s = split_arms([row], "구현")
    assert s.arms[COMPARISON] == [row]
    assert s.marks[COMPARISON][RENAMED] == 1


def test_브랜치_줄이_없는_지시문은_배정하지_않고_수만_센다() -> None:
    (name,) = _이름들("feature/", BASE, 1)
    row = _행(name, directive_features=_지시문(None, f"{BASE}. {SWEEP_MARK}의 갈래"))
    s = split_arms([row], "구현")
    assert s.no_branch == 1
    assert s.arms == {BASE: [], COMPARISON: []}


_END_MINUS = (END_AT - timedelta(seconds=1)).isoformat()


@pytest.mark.parametrize(
    "over",
    [
        {"kind": "하네스"},
        {
            "directive_features": {
                "directive": False,
                "branch_line": "feature/000-합성",
                "model_line": f"{BASE}. {SWEEP_MARK}의 갈래",
            }
        },
        {"directive_features": _지시문("feature/000-합성", f"{BASE}. 결정표 칸")},
        {"directive_features": _지시문("feature/000-합성", None)},
        {"first_human_at": END_AT.isoformat()},
        {"first_human_at": None},
    ],
    ids=["다른_종류", "지시문이_아님", "표지가_없음", "모델_줄이_없음", "끝에_시작", "트리거_없음"],
)
def test_표지_모집단_밖의_브랜치는_어디에도_세지_않는다(over: dict[str, Json]) -> None:
    row = _행("feature/000-합성")
    row.update(over)
    s = split_arms([row], "구현")
    assert s.arms == {BASE: [], COMPARISON: []}
    assert s.no_branch == 0
    assert all(sum(c.values()) == 0 for c in s.marks.values())


def test_끝_직전에_시작한_브랜치는_모집단에_든다() -> None:
    row = _행("feature/000-합성", first_human_at=_END_MINUS)
    assert split_arms([row], "구현").arms[arm("feature/000-합성")] == [row]


@pytest.mark.parametrize("state", ["OPEN", "CLOSED"])
def test_닫혔거나_열린_PR은_병합만_빠짐으로_센다(state: str) -> None:
    row = _행("feature/000-합성", state=state, merged=None)
    s = split_arms([row], "구현")
    assigned = arm("feature/000-합성")
    assert s.arms[assigned] == []
    assert s.marks[assigned][UNMERGED] == 1
    assert s.marks[assigned][OTHER_DROP] == 0


@pytest.mark.parametrize(
    "over",
    [
        {"merged": JUDGE_AT.isoformat()},
        {"base_ref": "develop"},
        {"msgs_main": 0, "msgs_sub": 0},
        {"cost": 0.0},
    ],
    ids=["기한에_병합", "main_밖", "귀속_응답_없음", "비용_없음"],
)
def test_병합됐지만_모집단_조건에_못_미치면_그_밖에_빠짐으로_센다(over: dict[str, Json]) -> None:
    row = _행("feature/000-합성")
    row.update(over)
    s = split_arms([row], "구현")
    assigned = arm("feature/000-합성")
    assert s.arms[assigned] == []
    assert s.marks[assigned][OTHER_DROP] == 1
    assert s.marks[assigned][UNMERGED] == 0


def test_기한_직전에_병합된_브랜치는_모집단에_든다() -> None:
    row = _행("feature/000-합성", merged=(JUDGE_AT - timedelta(seconds=1)).isoformat())
    assert split_arms([row], "구현").arms[arm("feature/000-합성")] == [row]


def test_스윕_시작_전에_열린_PR을_탐색_표지로_센다() -> None:
    early = _행("feature/000-합성", created=(SWEEP_START_AT - timedelta(seconds=1)).isoformat())
    at_start = _행("feature/001-합성", created=SWEEP_START_AT.isoformat())
    s = split_arms([early, at_start], "구현")
    assert s.marks[arm("feature/000-합성")][EARLY_PR] == 1
    assert sum(c[EARLY_PR] for c in s.marks.values()) == 1
    assert sum(len(v) for v in s.arms.values()) == 2


# --- 판정하지 않는 조건 ---------------------------------------------------------------------------


def _가름(per_arm: int, **over: Json) -> list[Row]:
    return _갈래(BASE, per_arm, **over) + _갈래(COMPARISON, per_arm, **over)


def test_갈래의_모집단이_n_k보다_적으면_판정하지_않는다() -> None:
    short = split_arms(_가름(N_K["구현"] - 1), "구현")
    enough = split_arms(_가름(N_K["구현"]), "구현")
    reasons = blocking_reasons("구현", short, [], SWEPT)
    assert len(reasons) == 2
    assert all(f"n_k {N_K['구현']}" in why for why in reasons)
    assert blocking_reasons("구현", enough, [], SWEPT) == []


def test_배정된_모델_레벨이_최대인_몫이_80퍼센트에_못_미치면_판정하지_않는다() -> None:
    n = 10
    at_least = round(n * TOP_SHARE_MIN)
    rows = _가름(n)
    off = ARM_RECORD[COMPARISON]
    base_rows = [r for r in rows if arm(str(r["branch"])) == BASE]
    for r in base_rows[at_least:]:
        r["top_model_effort"] = off
    exact = blocking_reasons("구현", split_arms(rows, "구현"), [], SWEPT)
    base_rows[at_least - 1]["top_model_effort"] = off
    below = blocking_reasons("구현", split_arms(rows, "구현"), [], SWEPT)
    assert not any("0.8" in why for why in exact)
    assert [why for why in below if "0.8" in why] == [
        f"{BASE} 에서 배정된 모델·레벨이 최대인 몫 0.70 이 0.8 보다 적다"
    ]


def test_도구의_SWEPT에서_빠진_종류는_사람이_멈춘_것으로_판정하지_않는다() -> None:
    s = split_arms(_가름(N_K["구현"]), "구현")
    assert blocking_reasons("구현", s, [], {"하네스": SWEPT["하네스"]}) == [
        "사람이 스윕을 멈췄다(도구의 SWEPT 에서 빠졌다)"
    ]


def test_소급_측정의_표지가_문턱을_넘으면_그_표지를_들어_판정하지_않는다() -> None:
    s = split_arms(_가름(N_K["구현"]), "구현")
    assert blocking_reasons("구현", s, ["usage 없는 응답의 몫"], SWEPT) == [
        "소급 측정의 판정하지 않는 조건에 걸렸다: usage 없는 응답의 몫"
    ]


def _표지(name: str, value: str, limit: str) -> list[str]:
    """`analyze.markers`의 표 한 행(이름, 소수 셋째 자리 값, 문턱, 넘는가)."""
    return [name, value, limit, "넘는다" if float(value) > float(limit) else "안"]


def test_값이_문턱을_넘은_표지의_이름만_고른다() -> None:
    rows = [
        _표지("usage 없는 응답의 몫", "0.020", "0.01"),
        _표지("귀속되지 않은 비용의 몫", "0.100", "0.2"),
        _표지("귀속된 응답이 없는 병합 PR의 몫", "0.300", "0.2"),
    ]
    assert failed_names(rows) == ["usage 없는 응답의 몫", "귀속된 응답이 없는 병합 PR의 몫"]


def test_값이_문턱과_같은_표지는_통과다() -> None:
    rows = [
        _표지("귀속되지 않은 비용의 몫", "0.200", "0.2"),
        _표지("usage 없는 응답의 몫", "0.011", "0.01"),
    ]
    assert failed_names(rows) == ["usage 없는 응답의 몫"]


def test_값이_NaN인_표지는_견줄_수_없어_든다() -> None:
    rows = [
        _표지("귀속되지 않은 비용의 몫", "0.100", "0.2"),
        ["단가 대조에서 두 끝 밖인 쌍의 몫", "nan", "0.05", "안"],
    ]
    assert failed_names(rows) == ["단가 대조에서 두 끝 밖인 쌍의 몫"]


def test_반올림으로_이름을_못_고르면_그_뜻을_넘긴다() -> None:
    # 문턱 0.01 바로 위의 0.0104는 표에 0.010으로 찍혀 값 칸으로는 넘지 않는다
    rows = [_표지("usage 없는 응답의 몫", "0.010", "0.01")]
    assert failed_names(rows) == [ROUNDED_OVER]


# --- 주된 판정과 되풀이 ---------------------------------------------------------------------------


def test_비용_비_구간의_위_끝이_1보다_작고_품질이_버티면_레벨을_내린다() -> None:
    ok, detail = lower_verdict(
        _비용행([20, 22, 24, 26, 28]), _비용행([40, 44, 48, 52, 56]), total_cost, interventions
    )
    assert ok
    assert detail.startswith("비용 비 0.50 [")


def test_비용_비가_1보다_작아도_구간의_위_끝이_1_이상이면_내리지_않는다() -> None:
    ok, detail = lower_verdict(
        _비용행([30, 40, 50]), _비용행([35, 45, 55]), total_cost, interventions
    )
    assert not ok
    ratio, hi = re.findall(r"비용 비 ([\d.]+) \[[\d.]+, ([\d.]+)\]", detail)[0]
    assert float(ratio) < 1 <= float(hi)
    assert detail.count(": True") == 2


@pytest.mark.parametrize(("comp_rework", "ok"), [(3, True), (4, False)])
def test_재작업_중앙값이_기준_3사분위를_넘으면_내리지_않는다(comp_rework: int, ok: bool) -> None:
    base = [_행(f"feature/{i}-기준", cost=40.0 + i, rework=i) for i in range(5)]  # 3사분위 3
    comp = _비용행([20, 21, 22, 23, 24], rework=comp_rework)
    got, detail = lower_verdict(comp, base, total_cost, interventions)
    assert got is ok
    assert f"재작업 중앙값 {comp_rework:.1f} ≤ 기준 3사분위 3.0: {ok}" in detail


@pytest.mark.parametrize(("comp_int", "ok"), [(2, True), (3, False)])
def test_사람_개입_중앙값이_기준_더하기_1을_넘으면_내리지_않는다(comp_int: int, ok: bool) -> None:
    base = _비용행([40, 41, 42, 43, 44], interventions=1)
    comp = _비용행([20, 21, 22, 23, 24], interventions=comp_int)
    got, detail = lower_verdict(comp, base, total_cost, interventions)
    assert got is ok
    assert f"개입 중앙값 {comp_int:.1f} ≤ 기준 1.0 + 1: {ok}" in detail


def test_기준_갈래가_하나면_그_재작업이_3사분위다() -> None:
    base = [_행("feature/0-기준", cost=40.0, rework=2)]
    ok, detail = lower_verdict(_비용행([20], rework=2), base, total_cost, interventions)
    assert ok
    assert "재작업 중앙값 2.0 ≤ 기준 3사분위 2.0: True" in detail


def test_비용이_0인_브랜치는_비용_비에서_빠진다() -> None:
    comp = _비용행([20, 22, 24, 0])
    _, detail = lower_verdict(comp, _비용행([40, 44, 48]), total_cost, interventions)
    assert "(n 3/3)" in detail


def test_한_갈래에_비용이_있는_브랜치가_없으면_내리지_않는다() -> None:
    assert lower_verdict(_비용행([0, 0]), _비용행([40]), total_cost, interventions) == (
        False,
        "비용이 있는 브랜치가 한 갈래에 없다",
    )


def test_부트스트랩_구간은_옮기기_전_판정_코드가_낸_값과_같다() -> None:
    # 기대값은 옮기기 전 판(72656b2)의 sweep.py boot_geomean_ratio 본문을 그 판의 analyze.py 의
    # SEED·RESAMPLES·percentile_ci 와 함께 스크래치 스크립트로 같은 입력에 돌려 손으로
    # 옮겼다(2026-10-13, `uv run python <스크립트> <워크트리>`). 시드, 횟수, 다시 뽑는 방식,
    # 백분위의 자리 가운데 하나라도 바뀌면 다르다. 값이 넷인 표본으로는 시드 없이 뽑아도 같은 구간이
    # 난 회차가 있어(변이 실행) 값이 열둘인 표본을 쓴다. 로그와 지수의 끝자리가 플랫폼마다 다를 수
    # 있다고 보고(재지 않았다) 상대 오차 1e-12 로 견준다.
    comp = [20.0, 23.0, 27.0, 31.0, 35.0, 38.0, 42.0, 47.0, 52.0, 58.0, 61.0, 66.0]
    base = [30.0, 33.0, 38.0, 41.0, 47.0, 50.0, 55.0, 61.0, 64.0, 70.0, 76.0, 83.0]
    expected = (0.6001729707145008, 0.9490535425498993)
    assert boot_geomean_ratio(comp, base) == pytest.approx(expected, rel=1e-12)


def _판정용(**comp_over: Json) -> list[Row]:
    """기준 갈래 비용 40, 비교 갈래 20인 다섯씩. 판정은 하지만 n_k에는 못 미친다."""
    comp: dict[str, Json] = {"cost": 20.0, "cost_main": 16.0}
    comp.update(comp_over)
    return _갈래(BASE, 5) + _갈래(COMPARISON, 5, **comp)


def test_되풀이가_주된_판정과_같으면_판정만_적는다() -> None:
    lines, verdict = verdicts(split_arms(_판정용(), "구현"))
    assert verdict == LOWER
    assert len(lines) == 3
    assert all(f": {LOWER}. " in line for line in lines)


@pytest.mark.parametrize(
    ("over", "what"),
    [
        ({"cost_main": 40.0}, "본 세션 비용만으로 셈한 판정"),
        ({"queued_human": 3}, "턴 도중의 사람 메시지"),
    ],
)
def test_되풀이가_주된_판정과_다르면_무엇에_따라_갈리는지_붙인다(
    over: dict[str, Json], what: str
) -> None:
    _, verdict = verdicts(split_arms(_판정용(**over), "구현"))
    assert verdict == f"{LOWER} ({what}에 따라 갈린다)"


def test_주된_판정이_서지_않으면_칸을_그대로_둔다() -> None:
    lines, verdict = verdicts(split_arms(_판정용(cost=40.0, cost_main=32.0), "구현"))
    assert verdict == KEEP
    # 비용이 같아 구간의 위 끝이 1이다. 품질 두 조건은 선다
    assert f": {KEEP}. 비용 비 1.00 [1.00, 1.00](n 5/5), " in lines[0]
    assert lines[0].count(": True") == 2


def test_판정하지_않는_조건이_있으면_결론_없음이고_세_줄은_탐색이다() -> None:
    got = judge_kind("구현", _판정용(), [], SWEPT)
    assert got.verdict == NO_JUDGMENT
    assert got.reasons == [
        f"{a} 의 모집단 5 이 n_k {N_K['구현']} 보다 적다" for a in (BASE, COMPARISON)
    ]
    assert all(line.startswith("탐색(판정이 아니다) ") for line in got.runs)


def test_판정하지_않는_조건이_없으면_세_줄을_판정으로_적는다() -> None:
    n = N_K["구현"]
    rows = _갈래(BASE, n) + _갈래(COMPARISON, n, cost=20.0, cost_main=16.0)
    got = judge_kind("구현", rows, [], SWEPT)
    assert got.reasons == []
    assert got.verdict == LOWER
    assert [line.split(":", 1)[0] for line in got.runs] == [
        "주된 판정(비용은 본 세션과 서브에이전트의 합)",
        "되풀이",
        "되풀이",
    ]


# --- 입력의 조건 ----------------------------------------------------------------------------------

_JUDGE_DAY = JUDGE_AT.date()
_REAL: dict[str, Json] = {"since": SWEEP_START}
_SYNTHETIC: dict[str, Json] = {"since": SWEEP_START, "synthetic": True}
_PAIRING = "--today 는 meta 의 synthetic 이 참인 합성 입력에만, 합성 입력은 --today 로만 받는다"
_EARLY = f"판정 시점({JUDGE_AT.isoformat()}) 전이다"


def test_판정_시점의_실제_입력은_입력의_문제가_없다() -> None:
    assert input_problems(_REAL, None, _JUDGE_DAY) == []


def test_합성_입력은_today로_판정_시점을_지난다() -> None:
    assert input_problems(_SYNTHETIC, _JUDGE_DAY, date(2026, 10, 13)) == []


def test_입력의_since가_스윕_시작이_아니면_판정하지_않는다() -> None:
    meta: dict[str, Json] = {"since": "2026-10-01T00:00:00Z"}
    assert input_problems(meta, None, _JUDGE_DAY) == [
        f"입력의 since(2026-10-01T00:00:00Z)가 스윕 시작 {SWEEP_START} 이 아니다"
    ]


@pytest.mark.parametrize(
    ("meta", "today"),
    [(_REAL, _JUDGE_DAY), (_SYNTHETIC, None)],
    ids=["실제_입력에_today", "합성_입력에_today_없음"],
)
def test_today와_합성_입력이_짝을_이루지_않으면_판정하지_않는다(
    meta: dict[str, Json], today: date | None
) -> None:
    assert _PAIRING in input_problems(meta, today, _JUDGE_DAY)


def test_판정_시점_전에는_갈래를_견주지_않는다() -> None:
    assert input_problems(_REAL, None, _JUDGE_DAY - timedelta(days=1)) == [_EARLY]
    assert input_problems(_SYNTHETIC, _JUDGE_DAY - timedelta(days=1), _JUDGE_DAY) == [_EARLY]


def test_collect의_종류가_사전_등록의_접두사와_어긋나면_판정하지_않는다() -> None:
    rows = [
        _행("feature/001-a", kind="하네스"),
        _행("docs/002-b", kind="구현"),
        _행("docs/003-c", kind="문서"),
        _행("chore/004-d", kind="하네스"),
    ]
    assert kind_problems(rows, _REGISTERED, SWEPT) == [
        "feature/001-a: collect.py 의 종류 하네스 와 사전 등록의 접두사가 어긋난다",
        "docs/002-b: collect.py 의 종류 구현 와 사전 등록의 접두사가 어긋난다",
    ]


def test_도구의_SWEPT가_사전_등록과_빠진_것_밖으로_어긋나면_판정하지_않는다() -> None:
    problems = kind_problems([], _REGISTERED, {"구현": ("feat/",)})
    assert len(problems) == 1
    assert problems[0].startswith("도구의 SWEPT 의 구현")


def test_사전_등록에서_종류를_읽지_못하면_판정하지_않는다() -> None:
    assert kind_problems([], {}, SWEPT) == ["README 사전 등록 절에서 스윕하는 종류를 읽지 못했다"]


# --- 고정값과 두 사전 등록 절 ---------------------------------------------------------------------


def _스윕_절() -> str:
    section = prereg_section(_SWEEP_README.read_text(encoding="utf-8"))
    assert section, f"{_SWEEP_README} 에 사전 등록 절이 없다"
    return re.sub(r"\s+", " ", section)


def test_사전_등록의_종류마다_n_k가_있다() -> None:
    # 종류가 하나 더해졌는데 N_K 에 없으면 판정 시점에 KeyError 로 죽는다(PR #220 claude-review).
    registered = prereg_kinds(prereg_section(_SWEEP_README.read_text(encoding="utf-8")))
    assert registered
    assert set(registered) <= set(N_K)


def test_사전_등록이_판정의_고정값을_든다() -> None:
    section = _스윕_절()
    for kind, n in N_K.items():
        assert f"{kind} {n}" in section, f"n_k {kind} {n}"
    assert f"{_JUDGE_DAY.isoformat()} 0시 UTC" in section
    assert f"{TOP_SHARE_MIN:.0%}" in section
    assert f"`{SWEEP_MARK}`" in section
    for record in ARM_RECORD.values():
        model, effort = record.split("/")
        assert f"`{model}`·`{effort}`" in section.replace("· ", "·"), record


def test_소급_측정_사전_등록이_부트스트랩의_횟수와_시드를_든다() -> None:
    section = prereg_section(_COST_README.read_text(encoding="utf-8"))
    criteria = section.split("### 스윕의 판정 기준", 1)[1]
    assert f"{RESAMPLES:,}회" in criteria
    assert f"`random.Random({SEED})`" in criteria
