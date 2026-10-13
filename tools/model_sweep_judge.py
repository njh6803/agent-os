"""레벨 스윕의 판정(ADR 0029 이력 2026-10-13). 스윕 프로브의 `sweep.py judge`가 부른다.

판정의 정의는 두 사전 등록 절이 원천이다. 스윕 프로브 README(`tools/model_sweep.py`의 `PREREG`)의
사전 등록과, 소급 측정 README(`.scratch/harness/probes/session_cost/README.md`) 사전 등록의 "스윕의
판정 기준"이다. 이 파일은 그 정의를 옮긴 순수 함수만 든다. 파일을 읽고, 두 절의 해시를 대 보고, 소급
측정의 표지 넷을 셈하고, 표를 찍는 것은 `sweep.py`가 한다. 판정은 2026-12-15 뒤에 한 번 돌아 그 전에
회귀를 잡을 자리가 없었다. 그래서 프로브에서 옮겨 `tests/tools/test_model_sweep_judge.py`로
고정했다(PR #220 claude-review).

1. 입력의 조건(`input_problems`, `kind_problems`). 하나라도 있으면 갈래를 견주지 않는다. 입력의
   `since`가 `SWEEP_START`가 아니다, `--today`로 준 날짜와 meta의 `synthetic`이 짝을 이루지 않는다,
   판정 시점(`JUDGE_AT`, 도구의 `END` 7일 뒤 0시 UTC) 전이다, 사전 등록 절에서 스윕하는 종류를 읽지
   못했다, 도구의 `SWEPT`가 사전 등록의 종류와 빠진 것 밖으로 어긋난다, `collect.py`가 매긴 종류가
   사전 등록의 접두사와 다른 브랜치가 있다.
2. 표지 모집단(`marked`, `merged_in_time`). 그 종류이고, 첫 사람 트리거가 지시문이고, 그 `모델:`
   줄에 `레벨 스윕`이 들고, 그 트리거가 끝 전이고, 끝에서 7일 안에 main에 병합되었고, 귀속된 응답이
   있고 비용이 0보다 큰 브랜치.
3. 갈래(`split_arms`)는 첫 지시문의 `브랜치:` 줄 값에 도구의 `arm`을 씌운 배정이다. 실제로 돈 모델과
   레벨이 아니다. 갈래마다 표지 셋(병합만 빠진 것, 곧 PR이 닫혔거나 열린 채인 것, `브랜치:` 줄과 PR
   머리가 다른 것, `모델:` 줄이 배정과 다른 것)을 센다. 병합됐지만 기한 뒤이거나 main이 아니거나
   귀속된 응답·비용이 없어 빠진 것은 "그 밖에 빠짐"으로, PR이 스윕 시작 전에 열린 것은 탐색 표지로
   따로 센다(그 브랜치는 비용·턴이 창 안 몫만 든다, `collect.py --since`).
4. 판정하지 않는 조건(`blocking_reasons`). 한 갈래라도 모집단이 n_k 미만이다, 배정된 모델·레벨이 본
   세션 비용의 최대인 브랜치가 80% 미만이다, 도구의 `SWEPT`에서 빠졌다(사람이 멈췄다), 소급 측정의
   표지 넷 가운데 문턱을 넘은 것이 있다.
5. 주된 판정(`lower_verdict`, `verdicts`)은 비용(본 세션과 서브에이전트의 합)의 기하평균 비, 재작업
   점수, 사람 개입으로 "레벨을 내린다"인지 본다. 되풀이 둘(본 세션 비용만, 사람 개입에
   `queued_human`을 더한 것)이 주된 판정과 다르면 "<무엇>에 따라 갈린다"를 붙인다. 4에 걸린 종류는
   세 줄을 "탐색"으로 적고 판정은 "결론 없음"이다(`judge_kind`).

부트스트랩의 시드와 횟수(`SEED`, `RESAMPLES`), 90% 구간(`percentile_ci`, 정렬한 값의 5번째와 95번째
백분위), 3사분위(`third_quartile`, `statistics`의 inclusive), 숫자 칸 읽기(`num`), "결론 없음"은
소급 측정 `analyze.py`의 것과 같은 식이다. 기하평균 비의 부트스트랩(`boot_geomean_ratio`)은 그
파일에 없고 옮기기 전 `sweep.py`의 것이다. `tools/`는 `.scratch/`의 모듈을 들이지 않으므로(pyright가
그 import를 풀지 못한다) 옮겨 적었다. 시드와 횟수는 테스트가 소급 측정 사전 등록 절과 대 본다.

못 보는 것: `SWEPT`에서 종류를 뺀 때가 끝 전인지 뒤인지 보지 않는다(입력에 그 시각이 없다).
`브랜치:` 줄이 없는 지시문은 배정할 수 없어 모집단에서 빼고 그 수만 센다. 실제로 돈 모델과 레벨은
배정에 쓰지 않고 몫(`top_share`)으로만 본다. 표지 "모델 줄이 배정과 다름"은 지시문이 적은 값을 볼 뿐
실제로 돈 모델을 보지 않는다.
"""

from __future__ import annotations

import math
import random
import statistics
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta

from tools import model_sweep as tool

type Json = dict[str, Json] | list[Json] | str | int | float | bool | None
type Row = dict[str, Json]
type Measure = Callable[[Row], float]


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


SWEEP_START = "2026-10-13T04:11:21Z"  # 스윕을 연 PR #217 의 병합 시각(`gh pr view 217`)
SWEEP_START_AT = parse_ts(SWEEP_START)
END_AT = datetime.combine(tool.END, time(), UTC)
JUDGE_AT = END_AT + timedelta(days=7)
N_K = {"구현": 27, "하네스": 25}  # 사전 등록 "σ_k와 표본 수". 판정 때 다시 셈하지 않는다
ARM_RECORD = {tool.BASE: "claude-opus-5-5/xhigh", tool.COMPARISON: "claude-opus-5-5/medium"}
SWEEP_MARK = "레벨 스윕"
TOP_SHARE_MIN = 0.8
SEED, RESAMPLES = 0, 2000

UNMERGED = "병합만 빠짐"  # 사전 등록의 표지: 닫혔거나 열린 채인 PR
OTHER_DROP = "그 밖에 빠짐"  # 병합됐지만 기한 뒤, main 밖, 귀속 응답·비용 없음
RENAMED = "브랜치 줄과 PR 머리가 다름"
MODEL_OFF = "모델 줄이 배정과 다름"
EARLY_PR = "PR이 스윕 시작 전에 열림"  # 탐색 표지
MARKS = [UNMERGED, OTHER_DROP, RENAMED, MODEL_OFF, EARLY_PR]

LOWER, KEEP, NO_JUDGMENT = "레벨을 내린다", "칸을 그대로 둔다", "결론 없음"
EXPLORATORY = "탐색(판정이 아니다) "


# --- 행 ------------------------------------------------------------------------------------------


def num(row: Row, key: str) -> float:
    value = row.get(key)
    return float(value) if isinstance(value, int | float) and not isinstance(value, bool) else 0.0


def line_of(row: Row, key: str) -> str | None:
    """첫 지시문의 줄 값(`model_line`, `branch_line`). 없거나 비면 None."""
    feats = row.get("directive_features")
    value = feats.get(key) if isinstance(feats, dict) else None
    return value if isinstance(value, str) and value else None


def stamp(row: Row, key: str) -> datetime | None:
    value = row.get(key)
    return parse_ts(value) if isinstance(value, str) and value else None


def directive(row: Row) -> bool:
    """첫 사람 트리거가 지시문인가(`collect.py`의 `directive_features`)."""
    feats = row.get("directive_features")
    return isinstance(feats, dict) and bool(feats.get("directive"))


# --- 표지 모집단과 배정 ---------------------------------------------------------------------------


def marked(row: Row, kind: str) -> bool:
    """표지 모집단의 조건 가운데 병합에 관한 것을 뺀 것(그 종류, 지시문, 표지, 끝 전의 트리거)."""
    model = line_of(row, "model_line")
    first = stamp(row, "first_human_at")
    return (
        row.get("kind") == kind
        and directive(row)
        and model is not None
        and SWEEP_MARK in model
        and first is not None
        and first < END_AT
    )


def merged_in_time(row: Row) -> bool:
    merged = stamp(row, "merged")
    return (
        merged is not None
        and merged < JUDGE_AT
        and row.get("base_ref") == "main"
        and num(row, "msgs_main") + num(row, "msgs_sub") > 0
        and num(row, "cost") > 0
    )


@dataclass(frozen=True)
class Split:
    """한 종류의 표지 지시문을 배정대로 가른 것. `arms`가 갈래마다의 모집단이다."""

    arms: dict[str, list[Row]]
    marks: dict[str, Counter[str]]
    no_branch: int


def split_arms(rows: Sequence[Row], kind: str) -> Split:
    """갈래는 첫 지시문의 `브랜치:` 줄 값(그대로)에 도구의 `arm`을 씌운 배정이다."""
    arms: dict[str, list[Row]] = {a: [] for a in tool.ARMS}
    marks: dict[str, Counter[str]] = {a: Counter() for a in tool.ARMS}
    no_branch = 0
    for r in rows:
        if not marked(r, kind):
            continue
        branch_line = line_of(r, "branch_line")
        if branch_line is None:
            no_branch += 1
            continue
        assigned = tool.arm(branch_line)
        counts = marks[assigned]
        if branch_line != r.get("branch"):
            counts[RENAMED] += 1
        if not (line_of(r, "model_line") or "").startswith(assigned):
            counts[MODEL_OFF] += 1
        created = stamp(r, "created")
        if created is not None and created < SWEEP_START_AT:
            counts[EARLY_PR] += 1
        if merged_in_time(r):
            arms[assigned].append(r)
        elif r.get("state") != "MERGED":
            counts[UNMERGED] += 1
        else:
            counts[OTHER_DROP] += 1
    return Split(arms, marks, no_branch)


# --- 판정하지 않는 조건 ---------------------------------------------------------------------------


def top_share(pop: Sequence[Row], assigned: str) -> float:
    """본 세션 비용이 가장 큰 모델·레벨이 배정된 갈래의 것인 브랜치의 몫."""
    top = sum(1 for r in pop if r.get("top_model_effort") == ARM_RECORD[assigned])
    return top / len(pop) if pop else 0.0


def blocking_reasons(
    kind: str,
    split: Split,
    failed_markers: Sequence[str],
    swept: dict[str, tuple[str, ...]],
) -> list[str]:
    """`failed_markers`는 소급 측정의 표지 넷 가운데 문턱을 넘은 것의 이름이고, `swept`는 도구의
    `SWEPT`다. 거기서 빠진 종류는 사람이 멈춘 것이다."""
    reasons: list[str] = []
    for a in tool.ARMS:
        n = len(split.arms[a])
        if n < N_K[kind]:
            reasons.append(f"{a} 의 모집단 {n} 이 n_k {N_K[kind]} 보다 적다")
        share = top_share(split.arms[a], a)
        if share < TOP_SHARE_MIN:
            reasons.append(
                f"{a} 에서 배정된 모델·레벨이 최대인 몫 {share:.2f} 이 {TOP_SHARE_MIN} 보다 적다"
            )
    if kind not in swept:
        reasons.append("사람이 스윕을 멈췄다(도구의 SWEPT 에서 빠졌다)")
    reasons.extend(f"소급 측정의 판정하지 않는 조건에 걸렸다: {name}" for name in failed_markers)
    return reasons


# --- 주된 판정과 되풀이 ---------------------------------------------------------------------------


def geomean(values: Sequence[float]) -> float:
    return math.exp(statistics.fmean(math.log(v) for v in values))


def percentile_ci(values: Sequence[float]) -> tuple[float, float]:
    """정렬한 값의 5번째와 95번째 백분위(가까운 순위)."""
    s = sorted(values)
    return s[int(0.05 * (len(s) - 1))], s[int(0.95 * (len(s) - 1))]


def third_quartile(values: Sequence[float]) -> float:
    """둘보다 적으면 그 값이고, 없으면 nan이다."""
    if len(values) < 2:
        return values[0] if values else math.nan
    return statistics.quantiles(values, n=4, method="inclusive")[2]


def boot_geomean_ratio(comp: Sequence[float], base: Sequence[float]) -> tuple[float, float]:
    """두 갈래를 따로 다시 뽑은 기하평균 비(비교/기준)의 90% 구간."""
    rng = random.Random(SEED)
    got: list[float] = []
    for _ in range(RESAMPLES):
        gc = geomean([rng.choice(comp) for _ in comp])
        gb = geomean([rng.choice(base) for _ in base])
        got.append(gc / gb)
    return percentile_ci(got)


def lower_verdict(
    comp: Sequence[Row], base: Sequence[Row], cost: Measure, intervention: Measure
) -> tuple[bool, str]:
    """사전 등록 "레벨을 내린다"의 세 조건. 비용이 0인 브랜치는 로그를 셀 수 없어 비용 비에서
    뺀다."""
    cc = [cost(r) for r in comp if cost(r) > 0]
    cb = [cost(r) for r in base if cost(r) > 0]
    if not cc or not cb:
        return False, "비용이 있는 브랜치가 한 갈래에 없다"
    ratio = geomean(cc) / geomean(cb)
    lo, hi = boot_geomean_ratio(cc, cb)
    rework_c = statistics.median(num(r, "rework") for r in comp)
    rework_q3 = third_quartile([num(r, "rework") for r in base])
    int_c = statistics.median(intervention(r) for r in comp)
    int_b = statistics.median(intervention(r) for r in base)
    ok = hi < 1 and rework_c <= rework_q3 and int_c <= int_b + 1
    detail = (
        f"비용 비 {ratio:.2f} [{lo:.2f}, {hi:.2f}](n {len(cc)}/{len(cb)}), "
        f"재작업 중앙값 {rework_c:.1f} ≤ 기준 3사분위 {rework_q3:.1f}: {rework_c <= rework_q3}, "
        f"개입 중앙값 {int_c:.1f} ≤ 기준 {int_b:.1f} + 1: {int_c <= int_b + 1}"
    )
    return ok, detail


def total_cost(r: Row) -> float:
    return num(r, "cost")


def main_cost(r: Row) -> float:
    return num(r, "cost_main")


def interventions(r: Row) -> float:
    return num(r, "interventions")


def with_queued(r: Row) -> float:
    return num(r, "interventions") + num(r, "queued_human")


# (이름, 비용, 사람 개입, 주된 판정과 다를 때 붙이는 "<무엇>에 따라 갈린다"의 <무엇>)
RUNS: list[tuple[str, Measure, Measure, str]] = [
    ("주된 판정(비용은 본 세션과 서브에이전트의 합)", total_cost, interventions, ""),
    ("되풀이: 본 세션 비용만", main_cost, interventions, "본 세션 비용만으로 셈한 판정"),
    (
        "되풀이: 사람 개입에 턴 도중 사람 메시지를 더함",
        total_cost,
        with_queued,
        "턴 도중의 사람 메시지",
    ),
]


def verdicts(split: Split) -> tuple[list[str], str]:
    """주된 판정과 되풀이 둘의 줄, 그리고 판정 문장."""
    comp, base = split.arms[tool.COMPARISON], split.arms[tool.BASE]
    lines: list[str] = []
    results: list[bool] = []
    for name, cost, intervention, _ in RUNS:
        ok, detail = lower_verdict(comp, base, cost, intervention)
        results.append(ok)
        lines.append(f"{name}: {LOWER if ok else KEEP}. {detail}")
    split_by = [
        what for (*_, what), ok in zip(RUNS[1:], results[1:], strict=True) if ok != results[0]
    ]
    verdict = LOWER if results[0] else KEEP
    if split_by:
        verdict += " (" + ", ".join(f"{w}에 따라 갈린다" for w in split_by) + ")"
    return lines, verdict


@dataclass(frozen=True)
class KindJudgment:
    """한 종류의 판정. `reasons`가 있으면 `runs`는 탐색이고 `verdict`는 결론 없음이다."""

    split: Split
    reasons: list[str]
    runs: list[str]
    verdict: str


def judge_kind(
    kind: str,
    rows: Sequence[Row],
    failed_markers: Sequence[str],
    swept: dict[str, tuple[str, ...]],
) -> KindJudgment:
    split = split_arms(rows, kind)
    reasons = blocking_reasons(kind, split, failed_markers, swept)
    runs, verdict = verdicts(split)
    if reasons:
        return KindJudgment(split, reasons, [EXPLORATORY + line for line in runs], NO_JUDGMENT)
    return KindJudgment(split, reasons, runs, verdict)


# --- 입력의 조건 ----------------------------------------------------------------------------------


def input_problems(meta: Mapping[str, Json], today: date | None, now: date) -> list[str]:
    """갈래를 견주기 전에 막는 입력의 조건. `today`는 `--today`로 준 날짜이고(합성 입력에만), 없으면
    `now`(오늘, UTC)로 판정 시점을 본다."""
    problems: list[str] = []
    if meta.get("since") != SWEEP_START:
        problems.append(f"입력의 since({meta.get('since')})가 스윕 시작 {SWEEP_START} 이 아니다")
    if (today is not None) != (meta.get("synthetic") is True):
        problems.append(
            "--today 는 meta 의 synthetic 이 참인 합성 입력에만, 합성 입력은 --today 로만 받는다"
        )
    day = today if today is not None else now
    if datetime.combine(day, time(), UTC) < JUDGE_AT:
        problems.append(f"판정 시점({JUDGE_AT.isoformat()}) 전이다")
    return problems


def kind_problems(
    rows: Sequence[Row],
    registered: dict[str, tuple[str, ...]],
    swept: dict[str, tuple[str, ...]],
) -> list[str]:
    """사전 등록의 종류(`registered`)와 도구의 `SWEPT`(`swept`), `collect.py`의 종류가 서로 맞는지.
    멈춰서 `swept`에서 빠진 종류는 문제가 아니다."""
    if not registered:
        return ["README 사전 등록 절에서 스윕하는 종류를 읽지 못했다"]
    problems = [f"도구의 {p}" for p in tool.sweep_problems(swept, registered)]
    for r in rows:
        branch, collected = str(r.get("branch")), r.get("kind")
        mine = tool.kind(branch, registered)
        listed = isinstance(collected, str) and collected in registered
        if (mine is not None or listed) and mine != collected:
            problems.append(
                f"{branch}: collect.py 의 종류 {collected} 와 사전 등록의 접두사가 어긋난다"
            )
    return problems
