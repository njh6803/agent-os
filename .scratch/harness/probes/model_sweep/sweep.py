"""레벨 스윕의 모집단을 소급 측정 결과로 재고, 사전 등록 절이 고정된 판 그대로인지 보고, 스윕을
판정한다.

`population`은 소급 측정 프로브의 `branches.json`(`../session_cost/`)만 읽어, 스윕이 다룰 수 있는
브랜치가 작업 종류마다 얼마나 되는지 찍는다. 스윕은 지시문으로 연 세션의 모델 줄만 바꾸므로 그
브랜치만 갈래에 든다. 지시문으로 열렸다는 것은 그 브랜치의 첫 사람 트리거에 `다음 작업:`이 든
것이다(`collect.py`의 `directive_features`). 종류는 소급 측정 사전 등록의 브랜치
종류다(`branches.json`의 `kind`). 세는 것은 `state`가 `MERGED`이고 비용이 0보다 큰 브랜치다.

`prereg`는 README 사전 등록 절의 SHA-256이 `PREREG_SHA256`과 같은지 본다.

`judge`는 `collect.py --since <SWEEP_START>`가 쓴 스윕 기간의 `branches.json`을 읽어 README 사전
등록대로 종류마다 한 번 판정한다. 순서는 이렇다.

1. 아래 가운데 하나라도 맞으면 갈래를 견주지 않고 1로 끝난다. 두 사전 등록 절(이 README와
   `../session_cost/README.md`) 가운데 하나라도 해시가 다르다, 판정 시점(`JUDGE_AT`, 도구의 `END`
   7일 뒤 0시 UTC) 전이다, 입력의 `since`가 `SWEEP_START`가 아니다, `--today`와 합성 입력이 짝을
   이루지 않는다(아래), 2의 어긋남이 있다.
2. 스윕하는 종류와 접두사는 사전 등록 절에서 읽고(`tools/model_sweep.py`의 `prereg_kinds`), 도구의
   `SWEPT`와 대 본다. 도구에서 빠진 종류는 사람이 멈춘 것이라 "결론 없음"이다. 빠진 것 밖의 차이나,
   `collect.py`가 매긴 종류가 사전 등록의 접두사와 다른 브랜치가 있으면 판정하지 않는다.
3. 표지 모집단: 그 종류이고, 첫 사람 트리거가 지시문이고, 그 `모델:` 줄에 `레벨 스윕`이 들고, 그
   트리거가 끝 전이고, 끝에서 7일 안에 main에 병합되었고, 귀속된 응답이 있고 비용이 0보다 큰 브랜치.
4. 갈래는 첫 지시문의 `브랜치:` 줄 값에 도구의 `arm`을 씌운 배정이다. 실제로 돈 모델과 레벨이
   아니다.
5. 갈래마다 표지 셋(병합만 빠진 것, 곧 PR이 닫혔거나 열린 채인 것, `브랜치:` 줄과 PR 머리가 다른 것,
   `모델:` 줄이 배정과 다른 것)을 적는다. 병합됐지만 기한 뒤이거나 main이 아니거나 귀속된
   응답·비용이 없어 빠진 것은 "그 밖에 빠짐"으로 따로 적는다. 그리고 판정하지 않는 조건(갈래의 수가
   n_k 미만, 배정된 모델·레벨이 본 세션 비용의 최대인 브랜치가 80% 미만, 소급 측정의 표지 넷,
   멈춤)을 본다.
6. 주된 판정은 비용(본 세션과 서브에이전트의 합)의 기하평균 비, 재작업 점수, 사람 개입으로 "레벨을
   내린다"인지 본다(소급 측정 사전 등록 "스윕의 판정 기준"). 되풀이 둘(본 세션 비용만, 사람 개입에
   `queued_human`을 더한 것)을 함께 적고, 주된 판정과 다르면 "<무엇>에 따라 갈린다"를 붙인다.
   판정하지 않는 조건에 걸린 종류는 세 줄을 "탐색"으로 찍고 판정은 "결론 없음"이다.

`--today`는 판정 시점 전에 합성한 입력으로 판정 경로를 돌려 볼 때만 쓴다. 스윕 기록으로 판정 시점
전에 갈래를 견주지 않는다(사전 등록 "판정 시점과 되풀이"). 그래서 `--today`는 meta의 `synthetic`이
참인 입력에만 받고, 그런 입력은 실제 판정에 받지 않는다. `collect.py`는 그 칸을 쓰지 않는다.

판은 판정할 때 체크아웃에 있는 파일들(`collect.py`, `costs.py`, `analyze.py`, `sweep.py`,
`tools/model_sweep.py`)의 해시와, 입력을 쓴 `collect.py`가 meta에 남긴 자기 해시(`collect_sha256`)를
함께 찍는다. 둘이 다르면 입력을 쓴 뒤 모으는 코드가 바뀐 것이다.

못 보는 것: `branches.json`은 2026-10-12까지 병합된 브랜치라 그 뒤의 처리량은 보지
않는다(`population`). 주마다의 수는 병합 시각(UTC)의 ISO 주로 셈하고 첫 주와 마지막 주는 일부만
든다. 첫 사람 트리거가 지시문이 아닌 브랜치가 사람이 연 세션인지 지시문 없이 이어 간 세션인지는
가르지 않는다. PR이 없는 브랜치는 `branches.json`에 행이 없어 "병합만 빠진" 표지에 들지
않는다(meta의 `branches_without_pr`에 이름과 기록 수만 남는다). `SWEPT`에서 종류를 뺀 때가 끝 전인지
뒤인지는 보지 않는다. `브랜치:` 줄이 없는 지시문은 배정할 수 없어 모집단에서 빼고 그 수를 적는다.

종료 코드: `population`은 0, 입력이 없으면 2. `prereg`는 같으면 0, 다르거나 절이 없으면 1. `judge`는
판정(결론 없음 포함)을 찍었으면 0, 1의 조건에 걸려 판정하지 않았으면 1, 입력이 없거나
`meta`·`branches`가 없으면 2.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SESSION_COST = HERE.parent / "session_cost"
sys.path.insert(0, str(SESSION_COST))
sys.path.insert(0, str(ROOT))
import analyze  # noqa: E402

from tools import model_sweep as tool  # noqa: E402

README = HERE / "README.md"
BRANCHES = SESSION_COST / "branches.json"
START, END = "<!-- 사전 등록 시작 -->", "<!-- 사전 등록 끝 -->"
PREREG_SHA256 = "8a1c774f9c5ab85d8b4d2400191f91916703f2db469b4bba003bd2c72d3a1649"
BASE = "claude-opus-5-5/xhigh"
KINDS = ["구현", "하네스", "명세", "티켓", "디자인", "문서", "수정"]
Z = 1.645 + 0.842
REDUCTIONS = (0.3, 0.4, 0.5)

# 판정의 고정값. 정의는 README 사전 등록 절이 원천이다.
SWEEP_START = "2026-10-13T04:11:21Z"  # 스윕을 연 PR #217 의 병합 시각(`gh pr view 217`)
END_AT = datetime.combine(tool.END, time(), UTC)
JUDGE_AT = END_AT + timedelta(days=7)
N_K = {"구현": 27, "하네스": 25}  # 사전 등록 "σ_k와 표본 수". 판정 때 다시 셈하지 않는다
ARM_RECORD = {tool.BASE: BASE, tool.COMPARISON: "claude-opus-5-5/medium"}  # 기록의 모델·레벨
SWEEP_MARK = "레벨 스윕"
TOP_SHARE_MIN = 0.8

type Row = dict[str, analyze.Json]


def section(text: str) -> str:
    if START not in text or END not in text:
        return ""
    return text.split(START, 1)[1].split(END, 1)[0]


def preregistration() -> tuple[bool, str]:
    current = section(README.read_text(encoding="utf-8"))
    if not current:
        return False, "README에 사전 등록 절이 없다"
    digest = hashlib.sha256(current.encode("utf-8")).hexdigest()
    if digest != PREREG_SHA256:
        return False, f"사전 등록 절의 SHA-256 {digest} 이 고정한 값 {PREREG_SHA256} 과 다르다"
    return True, f"사전 등록 절은 고정한 판 그대로다(SHA-256 {digest[:12]}…)"


def prereg() -> int:
    intact, why = preregistration()
    print(why)
    return 0 if intact else 1


def n_k(sigma: float, reduction: float) -> int:
    """소급 측정 사전 등록 "스윕의 판정 기준"의 식. 감소율만 바꿔 넣을 수 있게 했다."""
    delta = math.log(1 / (1 - reduction))
    return math.ceil(2 * Z**2 * sigma**2 / delta**2)


def sigma(rows: list[Row]) -> float | None:
    costs = [r["cost"] for r in rows]
    logs = [math.log(c) for c in costs if isinstance(c, int | float) and c > 0]
    return statistics.stdev(logs) if len(logs) >= 3 else None


def directive(row: Row) -> bool:
    feats = row.get("directive_features")
    return isinstance(feats, dict) and bool(feats.get("directive"))


def at_base(row: Row) -> bool:
    share = row.get("top_share")
    return row.get("top_model_effort") == BASE and isinstance(share, int | float) and share >= 0.9


def iso_week(stamp: object) -> str:
    when = datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
    return when.strftime("%G-W%V")


def describe(name: str, rows: list[Row]) -> str:
    s = sigma(rows)
    if s is None:
        return f"{name} {len(rows)}개, σ 셀 수 없음"
    needs = ", ".join(f"{int(r * 100)}% {n_k(s, r)}" for r in REDUCTIONS)
    return f"{name} {len(rows)}개, σ {s:.2f}, n_k({needs})"


def population(path: Path) -> int:
    if not path.exists():
        print(f"{path} 이 없다. 소급 측정 프로브의 collect.py 를 먼저 돌린다", file=sys.stderr)
        return 2
    data = json.loads(path.read_text(encoding="utf-8"))
    merged = [b for b in data["branches"] if b["state"] == "MERGED" and b["cost"] > 0]
    print(f"병합되고 비용이 있는 브랜치 {len(merged)}개(branches.json, {path.name})")
    print()
    print("종류마다 무리의 σ(로그 비용)와 한 갈래의 n_k(감소율별)")
    for kind in KINDS:
        rows = [b for b in merged if b["kind"] == kind]
        if not rows:
            continue
        led = [b for b in rows if directive(b)]
        led_base = [b for b in led if at_base(b)]
        rows_base = [b for b in rows if at_base(b)]
        print(f"- {kind}: 병합 {len(rows)}개, 지시문으로 열림 {len(led)}개")
        print(f"  {describe('지시문으로 열림 · opus-5-5 xhigh 90% 이상', led_base)}")
        print(f"  {describe('opus-5-5 xhigh 90% 이상(소급 측정 결과 절의 무리)', rows_base)}")
        print(f"  {describe('지시문으로 열림 전부', led)}")
        print(f"  {describe('병합 전부', rows)}")
        if led:
            top = Counter(str(b["top_model_effort"]) for b in led)
            same = top[BASE]
            print(f"  지시문으로 열린 것의 본 세션 최대 모델·레벨이 {BASE}: {same}/{len(led)}")
            queued = sum(int(b.get("queued_human") or 0) for b in led)
            print(f"  지시문으로 열린 것의 턴 도중 사람 메시지(queued_human) 합 {queued}")
    print()
    print("주마다 지시문으로 열린 병합 브랜치(병합 시각의 ISO 주, 첫 주와 마지막 주는 일부)")
    weeks: dict[str, Counter[str]] = defaultdict(Counter)
    for b in merged:
        if directive(b):
            weeks[iso_week(b["merged"])][str(b["kind"])] += 1
    for week in sorted(weeks):
        counts = ", ".join(f"{k} {weeks[week][k]}" for k in KINDS if weeks[week][k])
        print(f"- {week}: {counts}")
    print()
    print("주마다 비용 중앙값(지시문으로 열림 · opus-5-5 xhigh 90% 이상, 병합 시각의 ISO 주)")
    for kind in tool.SWEPT:
        costs: dict[str, list[float]] = defaultdict(list)
        for b in merged:
            if b["kind"] == kind and directive(b) and at_base(b):
                costs[iso_week(b["merged"])].append(float(b["cost"]))
        cells = ", ".join(
            f"{week} ${statistics.median(v):.1f}({len(v)}개)" for week, v in sorted(costs.items())
        )
        print(f"- {kind}: {cells}")
    return 0


# --- 판정 -----------------------------------------------------------------------------------------


def line_of(row: Row, key: str) -> str | None:
    feats = row.get("directive_features")
    value = feats.get(key) if isinstance(feats, dict) else None
    return value if isinstance(value, str) and value else None


def stamp(row: Row, key: str) -> datetime | None:
    value = row.get(key)
    return parse_ts(value) if isinstance(value, str) and value else None


def parse_ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def kind_problems(rows: list[Row], registered: dict[str, tuple[str, ...]]) -> list[str]:
    """사전 등록의 종류와 도구의 `SWEPT`, `collect.py`의 종류가 서로 맞는지. 멈춘 종류는 문제가
    아니다."""
    if not registered:
        return ["README 사전 등록 절에서 스윕하는 종류를 읽지 못했다"]
    problems = [f"도구의 {p}" for p in tool.sweep_problems(tool.SWEPT, registered)]
    for r in rows:
        branch, kind = str(r.get("branch")), r.get("kind")
        mine = tool.kind(branch, registered)
        if (mine is not None or kind in registered) and mine != kind:
            problems.append(f"{branch}: collect.py 의 종류 {kind} 와 사전 등록의 접두사가 어긋난다")
    return problems


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
        and analyze.num(row, "msgs_main") + analyze.num(row, "msgs_sub") > 0
        and analyze.num(row, "cost") > 0
    )


UNMERGED = "병합만 빠짐"  # 사전 등록의 표지: 닫혔거나 열린 채인 PR
OTHER_DROP = "그 밖에 빠짐"  # 병합됐지만 기한 뒤, main 밖, 귀속 응답·비용 없음
RENAMED = "브랜치 줄과 PR 머리가 다름"
MODEL_OFF = "모델 줄이 배정과 다름"
# 탐색 표지: 스윕 시작 전에 PR을 연 브랜치는 비용·턴이 창 안 몫만 든다(collect.py --since)
EARLY_PR = "PR이 스윕 시작 전에 열림"
MARKS = [UNMERGED, OTHER_DROP, RENAMED, MODEL_OFF, EARLY_PR]


@dataclass
class Split:
    """한 종류의 표지 지시문을 배정대로 가른 것."""

    arms: dict[str, list[Row]] = field(default_factory=lambda: {a: [] for a in tool.ARMS})
    marks: dict[str, Counter[str]] = field(
        default_factory=lambda: {a: Counter() for a in tool.ARMS}
    )
    no_branch: int = 0


def split_arms(rows: list[Row], kind: str) -> Split:
    """갈래는 첫 지시문의 `브랜치:` 줄 값(그대로)에 도구의 `arm`을 씌운 배정이다."""
    s = Split()
    for r in rows:
        if not marked(r, kind):
            continue
        branch_line = line_of(r, "branch_line")
        if branch_line is None:
            s.no_branch += 1
            continue
        assigned = tool.arm(branch_line)
        marks = s.marks[assigned]
        if branch_line != r.get("branch"):
            marks[RENAMED] += 1
        if not (line_of(r, "model_line") or "").startswith(assigned):
            marks[MODEL_OFF] += 1
        created = stamp(r, "created")
        if created is not None and created < parse_ts(SWEEP_START):
            marks[EARLY_PR] += 1
        if merged_in_time(r):
            s.arms[assigned].append(r)
        elif r.get("state") != "MERGED":
            marks[UNMERGED] += 1
        else:
            marks[OTHER_DROP] += 1
    return s


def top_share(pop: list[Row], assigned: str) -> float:
    """본 세션 비용이 가장 큰 모델·레벨이 배정된 갈래의 것인 브랜치의 몫."""
    top = sum(1 for r in pop if r.get("top_model_effort") == ARM_RECORD[assigned])
    return top / len(pop) if pop else 0.0


def blocking_reasons(kind: str, s: Split, stopped: bool, markers_ok: bool) -> list[str]:
    reasons: list[str] = []
    for a in tool.ARMS:
        n = len(s.arms[a])
        if n < N_K[kind]:
            reasons.append(f"{a} 의 모집단 {n} 이 n_k {N_K[kind]} 보다 적다")
        share = top_share(s.arms[a], a)
        if share < TOP_SHARE_MIN:
            reasons.append(f"{a} 에서 배정된 모델·레벨이 최대인 몫 {share:.2f} 이 0.8 보다 적다")
    if stopped:
        reasons.append("사람이 스윕을 멈췄다(도구의 SWEPT 에서 빠졌다)")
    if not markers_ok:
        reasons.append("소급 측정의 판정하지 않는 조건(표지 넷) 가운데 하나에 걸렸다")
    return reasons


def geomean(values: list[float]) -> float:
    return math.exp(statistics.fmean(math.log(v) for v in values))


def boot_geomean_ratio(comp: list[float], base: list[float]) -> tuple[float, float]:
    """두 갈래를 따로 다시 뽑은 기하평균 비(비교/기준)의 90% 구간."""
    rng = random.Random(analyze.SEED)
    got: list[float] = []
    for _ in range(analyze.RESAMPLES):
        gc = geomean([rng.choice(comp) for _ in comp])
        gb = geomean([rng.choice(base) for _ in base])
        got.append(gc / gb)
    return analyze.percentile_ci(got)


type Measure = Callable[[Row], float]


def lower_verdict(
    comp: list[Row], base: list[Row], cost: Measure, intervention: Measure
) -> tuple[bool, str]:
    """사전 등록 "레벨을 내린다"의 세 조건. 비용이 0인 브랜치는 로그를 셀 수 없어 비용 비에서
    뺀다."""
    cc = [cost(r) for r in comp if cost(r) > 0]
    cb = [cost(r) for r in base if cost(r) > 0]
    if not cc or not cb:
        return False, "비용이 있는 브랜치가 한 갈래에 없다"
    ratio = geomean(cc) / geomean(cb)
    lo, hi = boot_geomean_ratio(cc, cb)
    rework_c = statistics.median(analyze.num(r, "rework") for r in comp)
    rework_q3 = analyze.quartiles([analyze.num(r, "rework") for r in base])[2]
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
    return analyze.num(r, "cost")


def main_cost(r: Row) -> float:
    return analyze.num(r, "cost_main")


def interventions(r: Row) -> float:
    return analyze.num(r, "interventions")


def with_queued(r: Row) -> float:
    return analyze.num(r, "interventions") + analyze.num(r, "queued_human")


LOWER, KEEP, NO_JUDGMENT = "레벨을 내린다", "칸을 그대로 둔다", analyze.NO_JUDGMENT
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


def verdicts(s: Split) -> tuple[list[str], str]:
    """주된 판정과 되풀이 둘의 줄, 그리고 판정 문장."""
    comp, base = s.arms[tool.COMPARISON], s.arms[tool.BASE]
    lines: list[str] = []
    results: list[bool] = []
    for name, cost, intervention, _ in RUNS:
        ok, detail = lower_verdict(comp, base, cost, intervention)
        results.append(ok)
        lines.append(f"{name}: {LOWER if ok else KEEP}. {detail}")
    split = [what for (*_, what), ok in zip(RUNS[1:], results[1:], strict=True) if ok != results[0]]
    verdict = LOWER if results[0] else KEEP
    if split:
        verdict += " (" + ", ".join(f"{w}에 따라 갈린다" for w in split) + ")"
    return lines, verdict


def judge_kind(
    kind: str, rows: list[Row], stopped: bool, markers_ok: bool
) -> tuple[list[str], str]:
    s = split_arms(rows, kind)
    head = ["갈래", "모집단", "n_k", "배정 모델·레벨이 최대인 몫", *MARKS]
    table_rows = [
        [a, str(len(s.arms[a])), str(N_K[kind]), f"{top_share(s.arms[a], a):.2f}"]
        + [str(s.marks[a][m]) for m in MARKS]
        for a in tool.ARMS
    ]
    out = [f"## {kind}", "", analyze.table(head, table_rows), ""]
    out.append(f"- `브랜치:` 줄이 없어 배정하지 못한 표지 지시문: {s.no_branch}")
    reasons = blocking_reasons(kind, s, stopped, markers_ok)
    lines, verdict = verdicts(s)
    label = "탐색(판정이 아니다) " if reasons else ""
    out.extend(f"- {label}{line}" for line in lines)
    if reasons:
        out.append("")
        out.extend(f"- 판정하지 않는 조건: {why}" for why in reasons)
        return out, NO_JUDGMENT
    return out, verdict


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def head_commit() -> str:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True, text=True
        )
    except OSError:
        return "알 수 없음"
    return out.stdout.strip() or "알 수 없음"


VERSIONED = [
    SESSION_COST / "collect.py",
    SESSION_COST / "costs.py",
    SESSION_COST / "analyze.py",
    HERE / "sweep.py",
    ROOT / "tools" / "model_sweep.py",
]


def input_blockers(
    meta: dict[str, analyze.Json],
    rows: list[Row],
    registered: dict[str, tuple[str, ...]],
    today: date | None,
) -> list[str]:
    """갈래를 견주기 전에 막는 조건. `today`는 `--today`로 준 날짜이고, 없으면 오늘(UTC)이다.
    `--today`는 meta의 `synthetic`이 참인 합성 입력과만 짝을 이룬다."""
    blockers = [why for intact, why in (preregistration(), analyze.preregistration()) if not intact]
    if meta.get("since") != SWEEP_START:
        blockers.append(f"입력의 since({meta.get('since')})가 스윕 시작 {SWEEP_START} 이 아니다")
    if (today is not None) != (meta.get("synthetic") is True):
        blockers.append(
            "--today 는 meta 의 synthetic 이 참인 합성 입력에만, 합성 입력은 --today 로만 받는다"
        )
    day = today if today is not None else datetime.now(UTC).date()
    if datetime.combine(day, time(), UTC) < JUDGE_AT:
        blockers.append(f"판정 시점({JUDGE_AT.isoformat()}) 전이다")
    return blockers + kind_problems(rows, registered)


def print_header(path: Path, meta: dict[str, analyze.Json], today: date | None) -> None:
    print("# 레벨 스윕 판정")
    print()
    print(f"- {preregistration()[1]}")
    print(f"- 소급 측정: {analyze.preregistration()[1]}")
    versions = ", ".join(f"{f.name} {file_digest(f)}" for f in VERSIONED)
    print(f"- 판(SHA-256 앞 12자리): HEAD {head_commit()}, {versions}")
    written = str(meta.get("collect_sha256") or "없음")[:12]
    day = f"{today}(--today)" if today is not None else str(datetime.now(UTC).date())
    print(f"- 입력: {path}(since {meta.get('since')}, 쓴 collect.py {written}), 날짜 {day}")


def judge(path: Path, today: date | None) -> int:
    """`today`는 `--today`로 준 날짜다(합성 입력에만)."""
    if not path.exists():
        print(f"{path} 이 없다. collect.py --since {SWEEP_START} 를 먼저 돌린다", file=sys.stderr)
        return 2
    data = json.loads(path.read_text(encoding="utf-8"))
    meta, rows = data.get("meta"), data.get("branches")
    if not isinstance(meta, dict) or not isinstance(rows, list):
        print(f"{path} 에 meta 나 branches 가 없다", file=sys.stderr)
        return 2
    registered = tool.prereg_kinds(section(README.read_text(encoding="utf-8")))
    blockers = input_blockers(meta, rows, registered, today)
    print_header(path, meta, today)
    if blockers:
        print()
        for b in blockers:
            print(f"- 판정하지 않는다: {b}")
        return 1
    marker_rows, markers_ok = analyze.markers(meta)
    print()
    print("## 소급 측정의 표지 넷(스윕 기간)")
    print()
    print(analyze.table(["표지", "값", "문턱", "넘는가"], marker_rows))
    summary: list[str] = []
    for kind in registered:
        lines, verdict = judge_kind(kind, rows, kind not in tool.SWEPT, markers_ok)
        print()
        print("\n".join(lines))
        summary.append(f"- {kind}: **{verdict}**")
    print()
    print("## 판정")
    print()
    print("\n".join(summary))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    pop = sub.add_parser("population", help="스윕이 다룰 수 있는 브랜치를 종류마다 센다")
    pop.add_argument("--branches", type=Path, default=BRANCHES)
    sub.add_parser("prereg", help="사전 등록 절이 고정한 판 그대로인지 본다")
    jud = sub.add_parser("judge", help="스윕 기간의 branches.json 으로 종류마다 판정한다")
    jud.add_argument("--branches", type=Path, required=True)
    jud.add_argument("--today", type=date.fromisoformat, help="합성 입력으로 돌려 볼 때만 쓴다")
    args = parser.parse_args()
    if args.command == "population":
        return population(args.branches)
    if args.command == "judge":
        return judge(args.branches, args.today)
    return prereg()


if __name__ == "__main__":
    sys.exit(main())
