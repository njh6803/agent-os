"""다시 풀기의 판정(`.scratch/model-rerun/spec.md` "판정", 설계 6절).

본 측정의 과제 목록, `records/`의 회차 기록, 프로브 README의 사전 등록 절을 읽어 갈래마다의 표와
결론 한 줄(새 칸, 칸을 둠, 결론 없음)을 낸다. 정의는 사전 등록 절이 원천이고 이 파일은 그것을
옮긴다. 사전 등록 절은 아직 README에 없고 `PREREG_SHA256`은 어떤 절과도 맞지 않는 자리 표시 값이라,
명령 줄의 판정은 늘 결론 없음이다. 그래서 판정 함수 `judge_files`는 기대 해시를 인자로 받고 명령 줄
입구만 상수를 넘긴다. `prereg_section`·`prereg_problem`·`PREREG_SHA256`은 다른 모듈이 import하도록
공개 이름이다. 결론은 ADR 0029 이력 초안의 재료이고, 초안과 승인은 이 기능 밖이다. 꼴은
`tools/rerun_files.py`의 과제 목록과 판정 몫(`JudgeView`)만 읽고 회차 도구의 모듈은 import하지
않는다.

쓰는 회차(`select_rounds`): 파일럿 표시가 있는 회차는 읽되 셈에 넣지 않는다. 과제마다 측정 아님까지
센 본 측정 회차에서 가장 큰 조건 판 V를 잡고, V에서 갈래마다 측정인 회차 가운데 회차 번호가 가장
작은 것을 쓴다. V에 측정인 회차가 없는 갈래가 있거나, 쓰는 회차 사이에 `claude --version`이 다르면
그 과제를 T에서 빼고 까닭을 출력에 적는다.

명세와 설계가 정하지 않아 여기서 정한 것:
- 쓰는 회차에 판을 모르는(빈 값) 회차가 있으면 같은지 알 수 없어 과제를 빼고 그 갈래를 적는다.
- 과제 목록에 있는데 본 측정의 회차가 하나도 없는 과제도 뺀 과제로 적는다.
- 사전 등록 절은 README 전체에서 시작 표지와 끝 표지가 하나씩이고 시작이 앞일 때만 받는다. 선례
  `tools/model_sweep.py`처럼 첫 시작 표지와 그 뒤의 첫 끝 표지 사이를 읽으면, 절보다 앞의 글이 시작
  표지를 적었을 때 절이 아닌 글을 절로 읽는다. 하나씩일 때만 받으면 표지를 적은 글이 절의 앞에 있든
  뒤에 있든 결론 없음으로 멈춰 드러난다. 그래서 표지는 절의 두 자리에만 쓴다.
- 부트스트랩 표본에서 C_A가 0인 것도 S_k·S_A가 0인 것처럼 세지 않는다. 나눌 수 없다.
- 후보 가운데 U_k가 같으면 갈래 차례(A~E)의 앞을 고른다.
- 되풀이는 고른 갈래만 본 판정과 견준다. 결론 없음 조건은 본 판정의 것만 보고, 결론 없음이면
  "갈린다"를 붙이지 않는다. 결론 없음이면 세 표의 머리에 "탐색(판정이 아니다)"을 붙인다.
- 탐색의 "실패하면 올리기"에서 싸고 비싼 것은 본 판정의 C로 가른다. C가 작은 갈래를 먼저 여는 짝을
  들고(C가 같으면 짝이 없다), 설계가 이름 든 D에서 C로 올리는 짝은 C와 상관없이 든다.
- 파일럿 과제 목록은 판정하지 않고 꼴 오류로 거부한다.

못 보는 것:
- 사전 등록 절의 내용이 이 파일의 정의와 같은지는 보지 않는다. 해시만 대 본다. 절이 정의를 바꾸면
  이 파일과 상수를 함께 고친다.
- 표지가 줄 안에 섞여 있어도 하나씩이면 절로 받는다. 그래서 절이 없는 README의 한 문장이 두 표지를
  적으면 그 사이를 절로 읽는다. 이 저장소의 README는 표지를 홀로 한 줄에 두는지를 시험이 지킨다.
- `records/`에서 기록 파일 이름(`tools/rerun_files.py`의 `parse_record_file_name`)으로 풀리지 않는
  파일은 말없이 넘긴다. 과제 목록에 없는 과제의 기록도 세지 않는다.
- 회차 기록의 비용과 끝이 맞게 적혔는지는 보지 않는다. 회차 도구(티켓 04·06~10)가 쓴 대로 센다.

쓰는 법: `uv run python -m tools.rerun_judge --tasks <본 측정 과제 목록> [--records <폴더>]
[--readme <README>]`. 다른 도구를 불러 써서 모듈로 띄운다. 경로로 띄우면 `tools`를 import하지
못한다. 기록 폴더와 README의 기본값은 `.scratch/model-rerun/probes/` 아래다. 판정을 내면(결론 없음
포함) 0, 기록 폴더가 없거나 입력을 읽지 못했거나(UTF-8이 아닌 파일 포함) 인자가 틀리면 2로 끝난다.
"""

from __future__ import annotations

import argparse
import hashlib
import io
import math
import random
import statistics
import sys
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from tools.model_sweep_judge import percentile_ci
from tools.rerun_files import (
    ARMS,
    END_CAPPED,
    END_DONE,
    END_NOT_MEASURED,
    LIST_MAIN,
    JudgeView,
    ShapeError,
    Task,
    TaskList,
    arm_label,
    parse_record_file_name,
    read_judge_view,
    read_task_list,
)

PREREG_START, PREREG_END = "<!-- 사전 등록 시작 -->", "<!-- 사전 등록 끝 -->"
# 사전 등록 절 내용의 SHA-256. 절이 아직 없어 어떤 절과도 맞지 않는 자리 표시 값이다.
PREREG_SHA256 = "사전 등록 전(절의 SHA-256을 아직 넣지 않았다)"

CHECKOUT = Path(__file__).resolve().parent.parent
PROBES = CHECKOUT / ".scratch" / "model-rerun" / "probes"
PREREG_README = PROBES / "README.md"
RECORDS_DIR = PROBES / "records"

# --- 판정의 문턱(설계 6절, 명세 "판정") ---

BASE_ARM = "A"
KEEP_CELL = arm_label(BASE_ARM)  # 후보가 없을 때 두는 칸
MIN_TASKS = 6  # T가 이보다 적으면 결론 없음
SOLVED_SLACK = 1  # 후보 조건 1: S_k ≥ S_A − 1
MORE_INTERVENTIONS_MAX = 2  # 후보 조건 2: 개입 수가 A보다 많은 과제가 둘 이하
RATIO_UPPER_MAX = 1.0  # 후보 조건 3: R_k의 구간 위 끝이 1보다 작다
SEED, RESAMPLES = 0, 2000
UNCOUNTABLE_SHARE = 0.05  # 세지 않은 표본이 이 몫을 넘으면 셀 수 없음

EXPLORATORY = "탐색(판정이 아니다) "
ORIGINAL_EFFORT = "xhigh"  # 원래 세션과 A를 견주는 과제의 원래 레벨
PASTED_ARMS = ("D", "E")  # 붙여 넣은 글의 주장과 견주는 갈래
PASTED_CLAIM = "Opus 비용의 55~60%"
PASTED_ESCALATION = ("D", "C")  # 붙여 넣은 글의 규칙: Sonnet high로 안 되면 Opus medium으로 넘긴다

type Cost = Callable[[JudgeView], float]
type Solved = Callable[[JudgeView], bool]


def prereg_section(text: str) -> str | None:
    """README에서 두 표지 사이의 글. 시작 표지와 끝 표지가 하나씩이고 시작이 앞일 때만 절이고, 그
    밖은 빈 값이다. 선례 `tools/model_sweep.py`의 같은 이름 함수는 첫 시작 표지와 그 뒤의 첫 끝 표지
    사이를 읽어, 절보다 앞의 글이 시작 표지를 적으면 절이 아닌 글을 읽는다."""
    if text.count(PREREG_START) != 1 or text.count(PREREG_END) != 1:
        return None
    _, _, rest = text.partition(PREREG_START)
    body, end, _ = rest.partition(PREREG_END)
    return body if end else None


# --- 쓰는 회차 ---


@dataclass(frozen=True)
class Excluded:
    task_id: str
    reason: str


@dataclass(frozen=True)
class Selection:
    tasks: tuple[str, ...]  # T. 과제 목록 파일에 적힌 차례다
    rounds: Mapping[tuple[str, str], JudgeView]  # (과제 id, 갈래) → 쓰는 회차. T의 과제만 든다
    excluded: tuple[Excluded, ...]  # 과제 목록에 있는데 T에서 뺀 과제


def _task_rounds(task_id: str, views: Sequence[JudgeView]) -> dict[str, JudgeView] | str:
    """한 과제의 갈래마다 쓰는 회차, 또는 그 과제를 뺀 까닭.

    가장 큰 조건 판 V의 회차만 보고, 갈래마다 측정인 회차 가운데 회차 번호가 가장 작은 것을 쓴다.
    V는 측정 아님까지 센 그 과제의 본 측정 회차에서 잡는다(명세 "판정").
    """
    top = max(v.condition_version for v in views)
    measured = [v for v in views if v.condition_version == top and v.end.kind != END_NOT_MEASURED]
    chosen: dict[str, JudgeView] = {}
    for v in sorted(measured, key=lambda v: v.round_no):
        chosen.setdefault(v.arm, v)
    missing = [a.name for a in ARMS if a.name not in chosen]
    if missing:
        return f"조건 판 {top}에 측정인 회차가 없는 갈래: {', '.join(missing)}"
    unknown = [a.name for a in ARMS if chosen[a.name].claude_version is None]
    if unknown:
        return f"claude 판을 모르는 갈래: {', '.join(unknown)}"
    versions = sorted({v.claude_version or "" for v in chosen.values()})
    if len(versions) != 1:
        return f"claude 판이 갈래 사이에 다르다: {', '.join(versions)}"
    return chosen


def select_rounds(task_ids: Sequence[str], views: Sequence[JudgeView]) -> Selection:
    """본 측정의 회차만 쓴다(파일럿 표시가 있는 회차는 읽되 셈에 넣지 않는다)."""
    by_task: dict[str, list[JudgeView]] = {}
    for v in views:
        if not v.pilot:
            by_task.setdefault(v.task_id, []).append(v)
    tasks: list[str] = []
    rounds: dict[tuple[str, str], JudgeView] = {}
    excluded: list[Excluded] = []
    for t in task_ids:
        if t not in by_task:
            excluded.append(Excluded(task_id=t, reason="본 측정의 회차가 없다"))
            continue
        got = _task_rounds(t, by_task[t])
        if isinstance(got, str):
            excluded.append(Excluded(task_id=t, reason=got))
            continue
        tasks.append(t)
        rounds.update({(t, arm): v for arm, v in got.items()})
    return Selection(tasks=tuple(tasks), rounds=rounds, excluded=tuple(excluded))


# --- 수 ---


def solved(v: JudgeView) -> bool:
    """설계 6절 "회차마다": 끝남이고, 게이트 셋이 모두 종료 0이고, 숨은 시험이 모두 통과했다."""
    return v.end.kind == END_DONE and v.gates_green is True and v.hidden_passed is True


def solved_without_hidden(v: JudgeView) -> bool:
    """되풀이: 숨은 시험 없이 끝남과 게이트만으로 센 "풀었다"."""
    return v.end.kind == END_DONE and v.gates_green is True


def claude_code_cost(v: JudgeView) -> float:
    return v.cost_claude_code_usd


def official_cost(v: JudgeView) -> float:
    """되풀이: 모든 모델을 공식 단가로 다시 셈한 비용(명세 "판정"의 되풀이 둘)."""
    return v.cost_official_usd


def _views(selection: Selection, arm: str) -> list[JudgeView]:
    return [selection.rounds[(t, arm)] for t in selection.tasks]


def _unit(cost: float, n_solved: int) -> float | None:
    return cost / n_solved if n_solved else None


def ratio_interval(
    selection: Selection, arm: str, cost: Cost, is_solved: Solved
) -> tuple[float, float] | None:
    """R_k의 90% 구간. 셀 수 없으면 빈 값이다.

    회마다 T의 과제를 한 번 다시 뽑아 갈래 k와 A에 함께 쓴다. `random.Random(SEED)`를 부를 때마다
    새로 만들어 모든 갈래가 같은 다시 뽑기 위에서 셈하고, 갈래를 도는 차례가 수를 바꾸지 않는다.
    다시 뽑은 표본에서 S_k나 S_A가 0이면 R_k가 정의되지 않아 세지 않는다. C_A가 0인 표본도 나눌 수
    없어 같이 센다. 그런 표본이 `UNCOUNTABLE_SHARE`를 넘으면 셀 수 없음이다(명세 "판정"의 주석).
    """
    pairs = [
        (cost(k), is_solved(k), cost(a), is_solved(a))
        for k, a in zip(_views(selection, arm), _views(selection, BASE_ARM), strict=True)
    ]
    if not pairs:
        return None
    rng = random.Random(SEED)
    ratios: list[float] = []
    skipped = 0
    for _ in range(RESAMPLES):
        sample = [pairs[rng.randrange(len(pairs))] for _ in pairs]
        c_k = sum(p[0] for p in sample)
        s_k = sum(p[1] for p in sample)
        c_a = sum(p[2] for p in sample)
        s_a = sum(p[3] for p in sample)
        if s_k == 0 or s_a == 0 or c_a == 0:
            skipped += 1
            continue
        ratios.append((c_k / s_k) / (c_a / s_a))
    if skipped > UNCOUNTABLE_SHARE * RESAMPLES:
        return None
    return percentile_ci(ratios)


@dataclass(frozen=True)
class ArmRow:
    arm: str
    solved: int  # S_k
    cost: float  # C_k
    unit: float | None  # U_k = C_k / S_k. S_k가 0이면 빈 값
    ratio: float | None  # R_k = U_k / U_A. 둘 가운데 하나가 비면 빈 값
    interval: tuple[float, float] | None  # R_k의 90% 구간. 셀 수 없으면 빈 값
    more_interventions: int  # 개입 수가 A보다 많은 과제 수
    asked: int  # 물으며 끝남
    capped: int  # 상한으로 끊김
    candidate: bool  # 후보 조건 셋을 모두 맞는다. A는 후보가 아니다


@dataclass(frozen=True)
class ArmTable:
    """갈래마다의 줄과 고른 갈래. 본 판정과 되풀이 둘이 저마다 하나다."""

    rows: tuple[ArmRow, ...]
    pick: str | None  # 후보 가운데 U_k가 가장 작은 갈래. 후보가 없으면 빈 값


def _is_candidate(
    arm: str, n_solved: int, more: int, interval: tuple[float, float] | None, base_solved: int
) -> bool:
    """설계 6절의 후보 조건 셋. 셀 수 없는 구간은 위 끝을 몰라 셋째를 맞지 못한다."""
    return (
        arm != BASE_ARM
        and n_solved >= base_solved - SOLVED_SLACK
        and more <= MORE_INTERVENTIONS_MAX
        and interval is not None
        and interval[1] < RATIO_UPPER_MAX
    )


def score(selection: Selection, cost: Cost, is_solved: Solved) -> ArmTable:
    base = _views(selection, BASE_ARM)
    base_solved = sum(is_solved(v) for v in base)
    base_unit = _unit(sum(cost(v) for v in base), base_solved)
    rows: list[ArmRow] = []
    for a in ARMS:
        vs = _views(selection, a.name)
        c = sum(cost(v) for v in vs)
        s = sum(is_solved(v) for v in vs)
        unit = _unit(c, s)
        interval = ratio_interval(selection, a.name, cost, is_solved)
        more = sum(v.interventions > b.interventions for v, b in zip(vs, base, strict=True))
        rows.append(
            ArmRow(
                arm=a.name,
                solved=s,
                cost=c,
                unit=unit,
                ratio=unit / base_unit if unit is not None and base_unit else None,
                interval=interval,
                more_interventions=more,
                asked=sum(v.asked_at_end for v in vs),
                capped=sum(v.end.kind == END_CAPPED for v in vs),
                candidate=_is_candidate(a.name, s, more, interval, base_solved),
            )
        )
    candidates = [r for r in rows if r.candidate]
    # 같은 U_k면 갈래 차례(A~E)의 앞이다. 후보는 S_k가 0이 아니라 U_k가 있다.
    pick = min(candidates, key=lambda r: math.inf if r.unit is None else r.unit, default=None)
    return ArmTable(rows=tuple(rows), pick=None if pick is None else pick.arm)


# --- 결론 ---


def prereg_problem(readme_text: str, expected_sha256: str) -> str | None:
    """사전 등록 절이 고정한 판이 아니면 그 까닭, 맞으면 빈 값. 해시는 절 내용의 UTF-8
    SHA-256이다."""
    section = prereg_section(readme_text)
    if section is None:
        counts = f"시작 {readme_text.count(PREREG_START)}개, 끝 {readme_text.count(PREREG_END)}개"
        return f"사전 등록 절의 표지가 시작과 끝 하나씩 차례대로 있지 않다({counts})"
    digest = hashlib.sha256(section.encode("utf-8")).hexdigest()
    if digest != expected_sha256:
        return f"사전 등록 절의 SHA-256 {digest}이 판정 도구의 상수 {expected_sha256}와 다르다"
    return None


def blockers(
    selection: Selection, main_table: ArmTable, prereg_issue: str | None
) -> tuple[str, ...]:
    """설계 6절 "판정하지 않는 조건". `prereg_issue`는 `prereg_problem`이 돌려준 까닭이다."""
    n = len(selection.tasks)
    base_solved = next(r.solved for r in main_table.rows if r.arm == BASE_ARM)
    found: list[str] = []
    if n < MIN_TASKS:
        found.append(f"T가 {MIN_TASKS}보다 적다({n})")
    if base_solved * 2 < n:
        found.append(f"S_A가 T의 절반보다 적다(S_A {base_solved}, T {n})")
    if prereg_issue is not None:
        found.append(prereg_issue)
    return tuple(found)


def conclusion(
    main_table: ArmTable, found: Sequence[str], official: ArmTable, no_hidden: ArmTable
) -> str:
    """결론 한 줄. 되풀이로 고른 갈래가 본 판정과 다르면 "<단가 / 숨은 시험>에 따라 갈린다"를
    붙인다. 되풀이는 고른 갈래만 견주고, 결론 없음 조건은 본 판정의 것만 본다."""
    if found:
        return f"결론 없음: {'; '.join(found)}. 칸은 {KEEP_CELL} 그대로다"
    if main_table.pick is None:
        line = f"칸을 둔다: {KEEP_CELL} (후보 없음)"
    else:
        line = f"새 칸: {arm_label(main_table.pick)} (갈래 {main_table.pick})"
    split_by = [
        what
        for table, what in ((official, "단가"), (no_hidden, "숨은 시험"))
        if table.pick != main_table.pick
    ]
    if split_by:
        line += " (" + ", ".join(f"{w}에 따라 갈린다" for w in split_by) + ")"
    return line


@dataclass(frozen=True)
class Mixed:
    """갈래마다 T의 회차 가운데 셈에 다른 몫이 섞인 회차 수(명세 "회차 기록"·"상한과 끄기"·"게이트와
    숨은 시험"의 주석)."""

    arm: str
    cost_substituted: int  # 끈 호출의 비용을 공식 단가 셈으로 대신 넣었다. C_k에 두 셈이 섞인 몫
    setup_failed: int  # 결과 작업 트리의 준비가 실패해 풀지 못했다. 일시 실패일 수 있는 몫
    official_substituted: int  # 공식 단가 셈에 `modelUsage`로 대신 셈한 몫이 들었다


def mixed_counts(selection: Selection) -> tuple[Mixed, ...]:
    out: list[Mixed] = []
    for a in ARMS:
        vs = _views(selection, a.name)
        out.append(
            Mixed(
                arm=a.name,
                cost_substituted=sum(v.cost_substituted for v in vs),
                setup_failed=sum(v.setup_failed for v in vs),
                official_substituted=sum(v.official_substituted for v in vs),
            )
        )
    return tuple(out)


# --- 탐색(판정이 아니다, 설계 6절) ---


@dataclass(frozen=True)
class TierRow:
    tier: str
    arm: str
    tasks: int  # 그 층의 T 과제 수
    solved: int
    ratio: float | None  # 그 층 안의 U_k / U_A


@dataclass(frozen=True)
class Escalation:
    """싼 갈래 `first`로 먼저 열고 못 풀면 비싼 갈래 `then`으로 다시 연다고 할 때의 어림. 싸고
    비싼 것은 본 판정의 C(T의 Claude Code 셈의 합)로 가른다. C가 같은 두 갈래는 짝을 짓지 않는다.
    붙여 넣은 글의 규칙인 `PASTED_ESCALATION`은 C와 상관없이 짝이다."""

    first: str
    then: str
    solved: int
    cost: float  # 과제마다 first가 풀었으면 C_first, 아니면 C_first + C_then
    unit: float | None


@dataclass(frozen=True)
class Effort:
    """갈래마다 T의 회차에서 낸 시간과 토큰. 토큰 합은 그 칸이 빈 회차가 하나라도 있으면 빈
    값이다."""

    arm: str
    wall_median: float | None  # 회차의 벽시계 초의 중앙값
    input: int | None
    output: int | None
    cache_read: int | None
    cache_write: int | None
    thinking: int | None
    thinking_share: float | None  # 생각 토큰 / 출력 토큰
    asked: int  # 물으며 끝남의 수(명세가 "`AskUserQuestion`을 부른 수"를 바꿨다)
    capped: int
    denied: int  # 막는 규칙이 거부한 호출 수


@dataclass(frozen=True)
class OriginalRatio:
    """A의 비용과 원래 세션의 PR 앞 비용의 비. 원래 세션의 레벨이 xhigh인 T의 과제로만 낸다."""

    tasks: int
    a_cost: float
    pr_cost: float
    ratio: float | None


@dataclass(frozen=True)
class UtilizationRow:
    arm: str
    window: str
    rounds: int  # 첫과 끝 사용률에 모두 그 창이 있는 회차 수
    median_change: float  # 끝 사용률 − 첫 사용률의 중앙값


@dataclass(frozen=True)
class Exploration:
    tiers: tuple[TierRow, ...]
    escalations: tuple[Escalation, ...]
    effort: tuple[Effort, ...]
    original: OriginalRatio
    utilization: tuple[UtilizationRow, ...]


def _tier_rows(selection: Selection, tasks: Sequence[Task]) -> list[TierRow]:
    tier_of = {t.task_id: t.tier for t in tasks}
    rows: list[TierRow] = []
    for tier in dict.fromkeys(tier_of[t] for t in selection.tasks):
        ids = [t for t in selection.tasks if tier_of[t] == tier]
        units: dict[str, float | None] = {}
        counts: dict[str, int] = {}
        for a in ARMS:
            vs = [selection.rounds[(t, a.name)] for t in ids]
            counts[a.name] = sum(solved(v) for v in vs)
            units[a.name] = _unit(sum(claude_code_cost(v) for v in vs), counts[a.name])
        base = units[BASE_ARM]
        for a in ARMS:
            unit = units[a.name]
            ratio = unit / base if unit is not None and base else None
            rows.append(TierRow(tier, a.name, len(ids), counts[a.name], ratio))
    return rows


def _escalations(selection: Selection) -> list[Escalation]:
    totals = {a.name: sum(claude_code_cost(v) for v in _views(selection, a.name)) for a in ARMS}
    out: list[Escalation] = []
    for first in ARMS:
        for then in ARMS:
            pasted = (first.name, then.name) == PASTED_ESCALATION
            if totals[first.name] >= totals[then.name] and not pasted:
                continue
            pairs = zip(_views(selection, first.name), _views(selection, then.name), strict=True)
            n_solved, cost = 0, 0.0
            for x, y in pairs:
                cost += claude_code_cost(x) + (0.0 if solved(x) else claude_code_cost(y))
                n_solved += solved(x) or solved(y)
            out.append(Escalation(first.name, then.name, n_solved, cost, _unit(cost, n_solved)))
    return out


def _token_sum(values: Sequence[int | None]) -> int | None:
    known = [v for v in values if v is not None]
    return sum(known) if len(known) == len(values) else None


def _effort(selection: Selection) -> list[Effort]:
    out: list[Effort] = []
    for a in ARMS:
        vs = _views(selection, a.name)
        output = _token_sum([v.tokens.output for v in vs])
        thinking = _token_sum([v.tokens.thinking for v in vs])
        out.append(
            Effort(
                arm=a.name,
                wall_median=statistics.median(v.wall_seconds for v in vs) if vs else None,
                input=_token_sum([v.tokens.input for v in vs]),
                output=output,
                cache_read=_token_sum([v.tokens.cache_read for v in vs]),
                cache_write=_token_sum([v.tokens.cache_write for v in vs]),
                thinking=thinking,
                thinking_share=thinking / output if thinking is not None and output else None,
                asked=sum(v.asked_at_end for v in vs),
                capped=sum(v.end.kind == END_CAPPED for v in vs),
                denied=sum(v.denied_calls for v in vs),
            )
        )
    return out


def _original(selection: Selection, tasks: Sequence[Task]) -> OriginalRatio:
    by_id = {t.task_id: t for t in tasks}
    ids = [
        t
        for t in selection.tasks
        if (by_id[t].original_model_effort or "").rsplit("/", 1)[-1] == ORIGINAL_EFFORT
    ]
    a_cost = sum(claude_code_cost(selection.rounds[(t, BASE_ARM)]) for t in ids)
    pr_cost = sum(by_id[t].pr_cost_usd for t in ids)
    return OriginalRatio(len(ids), a_cost, pr_cost, a_cost / pr_cost if pr_cost else None)


def _utilization(selection: Selection) -> list[UtilizationRow]:
    out: list[UtilizationRow] = []
    for a in ARMS:
        changes: dict[str, list[float]] = {}
        for v in _views(selection, a.name):
            start = {w.window: w.utilization for w in v.utilization_start}
            for w in v.utilization_end:
                if w.window in start:
                    changes.setdefault(w.window, []).append(w.utilization - start[w.window])
        out.extend(
            UtilizationRow(a.name, window, len(cs), statistics.median(cs))
            for window, cs in changes.items()
        )
    return out


def explore(selection: Selection, task_list: TaskList) -> Exploration:
    return Exploration(
        tiers=tuple(_tier_rows(selection, task_list.tasks)),
        escalations=tuple(_escalations(selection)),
        effort=tuple(_effort(selection)),
        original=_original(selection, task_list.tasks),
        utilization=tuple(_utilization(selection)),
    )


# --- 판정 ---


@dataclass(frozen=True)
class Judgment:
    tasks: tuple[str, ...]  # T
    listed: int  # 과제 목록의 과제 수
    excluded: tuple[Excluded, ...]
    main: ArmTable
    official: ArmTable  # 되풀이: 공식 단가
    no_hidden: ArmTable  # 되풀이: 숨은 시험 없이 센 풀었다
    mixed: tuple[Mixed, ...]
    explore: Exploration
    blockers: tuple[str, ...]  # 결론 없음의 까닭. 있으면 표는 탐색이다
    conclusion: str

    @property
    def text(self) -> str:
        return render(self)


def read_views(records_dir: Path) -> list[JudgeView]:
    paths = sorted(p for p in records_dir.iterdir() if parse_record_file_name(p.name) is not None)
    return [read_judge_view(p) for p in paths]


def judge_files(
    tasks_path: Path, records_dir: Path, readme_path: Path, expected_sha256: str
) -> Judgment:
    """판정. 기대 해시는 인자로 받고, 사전 등록 절의 해시 상수는 명령 줄 입구만 넘긴다."""
    task_list = read_task_list(tasks_path)
    if task_list.kind != LIST_MAIN:
        raise ShapeError(f"{tasks_path}: 본 측정의 과제 목록이 아니다({task_list.kind})")
    selection = select_rounds([t.task_id for t in task_list.tasks], read_views(records_dir))
    main = score(selection, claude_code_cost, solved)
    official = score(selection, official_cost, solved)
    no_hidden = score(selection, claude_code_cost, solved_without_hidden)
    try:
        readme_text = readme_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        raise ShapeError(f"{readme_path}: README: UTF-8이 아니다({e})") from e
    prereg = prereg_problem(readme_text, expected_sha256)
    found = blockers(selection, main, prereg)
    return Judgment(
        tasks=selection.tasks,
        listed=len(task_list.tasks),
        excluded=selection.excluded,
        main=main,
        official=official,
        no_hidden=no_hidden,
        mixed=mixed_counts(selection),
        explore=explore(selection, task_list),
        blockers=found,
        conclusion=conclusion(main, found, official, no_hidden),
    )


# --- 출력 ---


def _money(v: float | None) -> str:
    return "-" if v is None else f"${v:.2f}"


def _ratio(v: float | None) -> str:
    return "-" if v is None else f"{v:.2f}"


def _interval(v: tuple[float, float] | None) -> str:
    return "셀 수 없음" if v is None else f"[{v[0]:.2f}, {v[1]:.2f}]"


def _arm_table_lines(table: ArmTable) -> list[str]:
    lines = [
        "| 갈래 | 모델 / 레벨 | S | C | U | R | R의 90% 구간 | 개입이 A보다 많은 과제 "
        "| 물으며 끝남 | 상한으로 끊김 | 후보 |",
        "|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in table.rows:
        mark = "기준" if r.arm == BASE_ARM else ("후보" if r.candidate else "")
        lines.append(
            f"| {r.arm} | {arm_label(r.arm)} | {r.solved} | {_money(r.cost)} | {_money(r.unit)} "
            f"| {_ratio(r.ratio)} | {_interval(r.interval)} | {r.more_interventions} | {r.asked} "
            f"| {r.capped} | {mark} |"
        )
    return lines


def render(j: Judgment) -> str:
    lines = ["# 다시 풀기 판정", ""]
    lines.append(f"과제 목록 {j.listed}개 가운데 T는 {len(j.tasks)}개다.")
    lines.extend(f"- 뺀 과제 {x.task_id}: {x.reason}" for x in j.excluded)
    lines.append("")
    prefix = EXPLORATORY if j.blockers else ""
    tables = (
        ("본 판정(비용은 Claude Code의 셈, 풀었다는 끝남·게이트·숨은 시험)", j.main),
        ("되풀이: 비용을 공식 단가로 셈한다", j.official),
        ("되풀이: 숨은 시험 없이 끝남과 게이트만으로 센다", j.no_hidden),
    )
    for title, table in tables:
        lines.extend([f"## {prefix}{title}", ""])
        lines.extend(_arm_table_lines(table))
        pick = "후보 없음" if table.pick is None else f"갈래 {table.pick}"
        lines.extend(["", f"후보 가운데 U가 가장 작은 갈래: {pick}", ""])
    lines.extend(["## 셈에 섞인 몫(T의 회차)", ""])
    lines.append("| 갈래 | 끈 호출의 비용을 공식 단가로 대신 넣음 | 결과 작업 트리의 준비 실패 |")
    lines.append("|---|---|---|")
    lines.extend(f"| {m.arm} | {m.cost_substituted} | {m.setup_failed} |" for m in j.mixed)
    total = sum(m.official_substituted for m in j.mixed)
    lines.extend(["", f"공식 단가 셈에 modelUsage로 대신 셈한 몫이 든 회차: {total}", ""])
    lines.extend(_explore_lines(j))
    lines.extend([f"결론: {j.conclusion}", ""])
    return "\n".join(lines)


def _tokens(v: int | None) -> str:
    return "모름" if v is None else str(v)


def _seconds(v: float | None) -> str:
    return "-" if v is None else f"{v:.0f}"


def _explore_lines(j: Judgment) -> list[str]:
    e = j.explore
    lines = [f"## {EXPLORATORY.strip()}", "", "크기 층별 결과(층 안의 비용 비):", ""]
    lines.append("| 층 | 갈래 | 과제 | S | R |")
    lines.append("|---|---|---|---|---|")
    lines.extend(
        f"| {t.tier} | {t.arm} | {t.tasks} | {t.solved} | {_ratio(t.ratio)} |" for t in e.tiers
    )
    lines.extend(["", "실패하면 올리기의 비용 셈(어림):", ""])
    lines.append("| 먼저 | 다시 | 푼 수 | 비용 | 푼 과제 하나의 비용 |")
    lines.append("|---|---|---|---|---|")
    lines.extend(
        f"| {x.first} | {x.then} | {x.solved} | {_money(x.cost)} | {_money(x.unit)} |"
        for x in e.escalations
    )
    first, then = PASTED_ESCALATION
    lines.extend(
        [
            "",
            f"붙여 넣은 글의 규칙은 {first}에서 {then}로 올리는 짝이다"
            "(본 판정의 C와 상관없이 든다).",
            "",
            "시간과 토큰:",
            "",
        ]
    )
    lines.append(
        "| 갈래 | 벽시계 중앙값(초) | 입력 | 출력 | 캐시 읽기 | 캐시 쓰기 | 생각 | 생각의 몫 "
        "| 물으며 끝남 | 상한으로 끊김 | 거부된 호출 |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
    lines.extend(
        f"| {f.arm} | {_seconds(f.wall_median)} | {_tokens(f.input)} | {_tokens(f.output)} "
        f"| {_tokens(f.cache_read)} | {_tokens(f.cache_write)} | {_tokens(f.thinking)} "
        f"| {_ratio(f.thinking_share)} | {f.asked} | {f.capped} | {f.denied} |"
        for f in e.effort
    )
    o = e.original
    lines.extend(
        [
            "",
            f"A의 비용과 원래 세션의 PR 앞 비용의 비(원래 세션이 xhigh인 과제 {o.tasks}개): "
            f"{_money(o.a_cost)} / {_money(o.pr_cost)} = {_ratio(o.ratio)}",
            "",
        ]
    )
    for r in j.main.rows:
        if r.arm in PASTED_ARMS:
            lines.append(
                f"{r.arm}({arm_label(r.arm)}): R {_ratio(r.ratio)} {_interval(r.interval)}, "
                f"붙여 넣은 글은 {PASTED_CLAIM}"
            )
    lines.extend(["", "한도 사용률의 회차마다의 변화(끝 − 첫):", ""])
    if not e.utilization:
        lines.append("사용률이 실린 회차가 없다.")
    lines.extend(
        f"- {u.arm} {u.window}: 회차 {u.rounds}개, 중앙값 {u.median_change:+.3f}"
        for u in e.utilization
    )
    lines.append("")
    return lines


# --- 명령 줄 ---


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="다시 풀기의 판정")
    parser.add_argument("--tasks", type=Path, required=True, help="본 측정의 과제 목록 파일")
    parser.add_argument("--records", type=Path, default=RECORDS_DIR, help="회차 기록 폴더")
    parser.add_argument("--readme", type=Path, default=PREREG_README, help="프로브 README")
    args = parser.parse_args(argv)
    tasks_path: Path = args.tasks
    records_dir: Path = args.records
    readme_path: Path = args.readme
    if not records_dir.is_dir():
        print(f"기록 폴더가 없다: {records_dir}", file=sys.stderr)
        return 2
    try:
        # 상수는 부를 때 모듈에서 읽는다. 시험이 바꿔 넣은 값이 판정 함수에 가는지 본다.
        judgment = judge_files(tasks_path, records_dir, readme_path, PREREG_SHA256)
    except (ShapeError, OSError) as e:
        print(f"읽지 못했다: {e}", file=sys.stderr)
        return 2
    print(judgment.text, end="")
    return 0


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(encoding="utf-8")
    sys.exit(main())
