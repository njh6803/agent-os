"""다시 풀기의 두 계약 파일(과제 목록과 회차 기록)의 꼴.

과제 고르기, 회차, 판정의 세 도구가 주고받는 파일 둘의 키 이름, 형, 맨 위 모양, 꼴 판, 읽고 쓰는
함수, `records/`의 파일 이름, 회차 폴더의 이름, 다음 회차 번호를 이 모듈이 정한다. 세 도구는 각자
픽스처 꼴을 짓지 않고 이 모듈의 함수로 파일을 짓고 읽는다(`.scratch/model-rerun/spec.md` "자리와
모듈"의 2026-10-22 주석). 이 모듈은 하위 프로세스를 부르지 않고 표준 라이브러리의 정해진 모듈만
import한다. 판정이 이 모듈만 import해도 회차 도구의 바깥 몫을 끌어오지 않게 하려는
것이다(`tests/tools/test_rerun_files.py`가 본다).

꼴.
- 두 파일 모두 JSON이고 맨 위는 객체다. 첫 키는 꼴 판 `shape_version`(정수)이다. 판을 올리면 옛 판의
  파일은 읽기가 거부한다.
- 읽기는 모르는 판, 빠진 키, 형이 다른 값, 모르는 키를 `ShapeError`로 거부한다. 값이 비는 칸도 키는
  들고 값이 `null`이다. 빈 값과 0을 가른다(게이트가 돌지 않은 것과 종료 0은 다르다).
- 쓰기는 지은 값을 글로 바꾼 뒤 이 모듈의 읽기로 다시 풀어 보고, 거부되면 쓰지 않는다. 그래서 쓰는
  함수는 읽는 함수가 받는 꼴만 낸다. 수는 유한한 값만 받는다(`NaN`과 무한대는 표준 JSON이 아니다).
- 회차 기록에는 모델이 쓴 글과 도구 입력을 담을 칸이 없다. 수, 식별자, 참거짓, 정해진 이름만 담고,
  글 칸은 칸마다 그 값이 나오는 꼴만 받는다(`.claude/rules/tools.md`의 허용 목록 항목). 모델 이름은
  `claude-`로 시작하는 이름과 `<synthetic>`, 창·subtype·끝난 까닭·노력은 영소문자 식별자, 도구
  이름은 영문 식별자, 계정 이름은 이메일의 `@` 앞 꼴, 오염 꼴의 이름은 러너 상수의 꼴이다. 게이트와
  준비의 명령은 명세가 정한 세 명령의 상수(`GATE_COMMANDS`, `SETUP_COMMANDS`)와 같아야 한다. 회차
  폴더 경로는 마지막 조각이 그 기록의 과제 id·갈래·회차 번호로 지은 회차 폴더 이름이고,
  줄바꿈·따옴표·`=`가 없다. 실패한 숨은 시험의 노드 ID는 겹치지 않고 줄바꿈이 없다.

못 보는 것. 키와 형, 칸 사이의 맞음(끝의 종류와 하위 이유, 끝남이 아닌 회차의 게이트, 결과 커밋과
고른 규칙)만 본다. 값이 실제와 맞는지(비용의 합이 세션 비용의 합인지, 노드 ID가 과제 목록의
것인지)는 그 값을 짓는 도구가 지킨다. 꼴로 좁힌 글 칸도 그 꼴 안의 글은 받는다. 도구 이름, 오염
꼴의 이름, 계정 이름 칸은 식별자 꼴이라 `sk-ant-…` 같은 토큰 꼴의 글도 받는다. 그 칸은 init 이벤트의
도구 목록, 러너 상수, 명령 줄로 받은 계정 이름에서만 옮긴다(회차 도구가 지킨다). 실패한 노드 ID도
매개변수 부분에 공백과 따옴표가 들 수 있어 꼴로 좁히지 않고, 과제 목록의 숨은 시험 ID에서만 옮긴다.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from pathlib import Path

type Json = dict[str, Json] | list[Json] | str | int | float | bool | None

SHAPE_VERSION = 1

# --- 갈래(설계 4절) ---

OPUS = "claude-opus-5-5"
SONNET = "claude-sonnet-5-5"
MODEL_LABELS = {OPUS: "Opus 5.5", SONNET: "Sonnet 5.5"}


@dataclass(frozen=True)
class Arm:
    name: str
    model: str
    effort: str

    @property
    def label(self) -> str:
        """지시문의 `모델:` 줄에 쓰는 사람의 이름(`Opus 5.5 / xhigh` 꼴)."""
        return f"{MODEL_LABELS[self.model]} / {self.effort}"


ARMS = (
    Arm("A", OPUS, "xhigh"),
    Arm("B", OPUS, "high"),
    Arm("C", OPUS, "medium"),
    Arm("D", SONNET, "high"),
    Arm("E", SONNET, "medium"),
)
ARM_BY_NAME = {a.name: a for a in ARMS}


def arm_label(name: str) -> str:
    return ARM_BY_NAME[name].label


# --- 과제 목록의 값 ---

LIST_PILOT = "파일럿"
LIST_MAIN = "본 측정"
LIST_KINDS = (LIST_PILOT, LIST_MAIN)

TIER_SMALL = "작은"
TIER_MEDIUM = "중간"
TIER_LARGE = "큰"
TIER_PILOT = "파일럿"
TIERS = (TIER_SMALL, TIER_MEDIUM, TIER_LARGE, TIER_PILOT)

# --- 회차 기록의 값 ---

CALL_FIRST = "첫"
CALL_HANDOFF = "인계"
CALL_INTERVENTION = "개입"
CALL_KINDS = (CALL_FIRST, CALL_HANDOFF, CALL_INTERVENTION)

END_DONE = "끝남"
END_CAPPED = "상한으로 끊김"
END_NOT_MEASURED = "측정 아님"
CAP_REASONS = ("개입", "세션", "예산", "시간")
NOT_MEASURED_REASONS = ("한도", "오염", "모델", "설정", "준비", "호출", "중단")
END_REASONS: dict[str, tuple[str, ...]] = {
    END_DONE: (),
    END_CAPPED: CAP_REASONS,
    END_NOT_MEASURED: NOT_MEASURED_REASONS,
}
REASON_LIMIT = "한도"

# 결과 커밋을 고른 규칙(명세 "결과 커밋"). 지시문의 `브랜치:` 이름의 로컬 브랜치, B 뒤에 커밋이 있는
# 하나뿐인 다른 로컬 브랜치, 둘 이상이거나 없어 결과 커밋이 없음.
RULE_BRANCH = "지시문 브랜치"
RULE_ONLY = "하나뿐인 브랜치"
RULE_NONE = "없음"
RULES = (RULE_BRANCH, RULE_ONLY, RULE_NONE)

# 결과 작업 트리에서 도는 게이트 셋, 이 차례다(명세 "게이트와 숨은 시험").
GATE_COMMANDS = (
    "uv run ruff check .",
    "uv run ruff format --check .",
    "uv run python tools/run_checks.py",
)
# 준비 명령 셋(명세 "준비"). 결과 작업 트리의 준비도 같다.
SETUP_COMMANDS = (
    "uv sync",
    "pnpm -C web install --frozen-lockfile",
    "uv run pre-commit install",
)

# --- 글자의 꼴 ---

_TASK_ID = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*-[0-9]{2,}")
_COMMIT = re.compile(r"[0-9a-f]{40}")
_UUID = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
_MODEL = re.compile(r"claude-[a-z0-9.-]+(?:\[1m\])?|<synthetic>")
_IDENT = re.compile(r"[a-z][a-z0-9_]*")  # 창, subtype, 끝난 까닭, 노력
_TOOL = re.compile(r"[A-Za-z][A-Za-z0-9_-]*")
_ACCOUNT = re.compile(r"[a-z0-9][a-z0-9._-]*")
_PATTERN_NAME = re.compile(r"[가-힣a-z0-9][가-힣a-z0-9_-]*")  # 오염 꼴의 이름(러너 상수)
_ENV_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_()]*")
_VERSION = re.compile(r"[0-9][0-9A-Za-z .()+-]*")
_TOKEN = re.compile(r"[0-9a-z]+")
_ROUND_DIR = re.compile(r"[^\x00-\x1f\x7f\"'=]+")
_NODE = re.compile(r"[^\x00-\x1f\x7f]+")


class ShapeError(ValueError):
    """두 계약 파일의 꼴에 맞지 않는 값."""


# --- 과제 목록 ---


@dataclass(frozen=True)
class Task:
    """과제 하나(명세 "과제 목록의 칸"과 그 주석)."""

    task_id: str  # `<slug>-<NN>`
    ticket: str  # 티켓 경로
    base: str  # B, 40자 커밋 해시
    merge: str  # M, 40자 커밋 해시
    branch: str  # 원래 PR의 머리 브랜치
    tier: str  # TIERS
    size: int  # 크기 지표
    order: int  # 실행 차례(0부터)
    pilot: bool
    pr_cost_usd: float  # 원래 세션의 PR 앞 비용
    round_cap_usd: float  # 회차 상한
    hidden_tests: tuple[str, ...]  # 숨은 시험의 pytest 노드 ID
    support_files: tuple[str, ...]  # M이 바꾼 시험 지원 파일
    original_model_effort: str | None  # 브랜치 표의 `top_model_effort`
    arm_plan: tuple[str, ...]  # 돌 갈래의 차례. 같은 갈래가 두 번 들 수 있다


@dataclass(frozen=True)
class TaskList:
    kind: str  # LIST_KINDS
    tasks: tuple[Task, ...]


def hidden_test_file(node_id: str) -> str:
    """노드 ID의 첫 `::` 앞, 곧 숨은 시험 파일. 매개변수의 `::`는 첫 `::` 뒤라 건드리지 않는다."""
    file, sep, rest = node_id.partition("::")
    if not sep or not file or not rest:
        raise ShapeError(f"노드 ID가 아니다: {node_id!r}")
    return file


def hidden_test_files(task: Task) -> tuple[str, ...]:
    """과제의 숨은 시험 파일. 겹치지 않고 처음 나온 차례다. 게이트(07)와 고르기(05)가 쓴다."""
    return tuple(dict.fromkeys(hidden_test_file(n) for n in task.hidden_tests))


_TASK_KEYS = (
    "task_id",
    "ticket",
    "base",
    "merge",
    "branch",
    "tier",
    "size",
    "order",
    "pilot",
    "pr_cost_usd",
    "round_cap_usd",
    "hidden_tests",
    "support_files",
    "original_model_effort",
    "arm_plan",
)


def _task_json(t: Task) -> dict[str, Json]:
    return {
        "task_id": t.task_id,
        "ticket": t.ticket,
        "base": t.base,
        "merge": t.merge,
        "branch": t.branch,
        "tier": t.tier,
        "size": t.size,
        "order": t.order,
        "pilot": t.pilot,
        "pr_cost_usd": t.pr_cost_usd,
        "round_cap_usd": t.round_cap_usd,
        "hidden_tests": list(t.hidden_tests),
        "support_files": list(t.support_files),
        "original_model_effort": t.original_model_effort,
        "arm_plan": list(t.arm_plan),
    }


def _task(o: _Obj) -> Task:
    pilot = o.flag("pilot")
    tier = o.choice("tier", TIERS)
    if pilot != (tier == TIER_PILOT):
        raise ShapeError(f"{o.where}: 파일럿 과제의 층은 '{TIER_PILOT}'이고 그 밖의 과제는 아니다")
    hidden = o.strs("hidden_tests")
    for n in hidden:
        hidden_test_file(n)
    plan = o.strs("arm_plan")
    if not plan or any(a not in ARM_BY_NAME for a in plan):
        raise ShapeError(f"{o.where}.arm_plan: 갈래 이름(A~E)이 하나 이상 들어야 한다: {plan!r}")
    return Task(
        task_id=o.text("task_id", _TASK_ID),
        ticket=o.text("ticket"),
        base=o.text("base", _COMMIT),
        merge=o.text("merge", _COMMIT),
        branch=o.text("branch"),
        tier=tier,
        size=o.count("size"),
        order=o.count("order"),
        pilot=pilot,
        pr_cost_usd=o.money("pr_cost_usd"),
        round_cap_usd=o.money("round_cap_usd"),
        hidden_tests=hidden,
        support_files=o.strs("support_files"),
        original_model_effort=o.opt_text("original_model_effort"),
        arm_plan=plan,
    )


def dumps_task_list(task_list: TaskList) -> str:
    """과제 목록의 글. 읽기로 다시 풀어 보고 거부되면 `ShapeError`다."""
    text = _dumps(
        {
            "shape_version": SHAPE_VERSION,
            "kind": task_list.kind,
            "tasks": [_task_json(t) for t in task_list.tasks],
        }
    )
    parse_task_list(text)
    return text


def parse_task_list(text: str) -> TaskList:
    o = _top(text, "과제 목록", ("kind", "tasks"))
    kind = o.choice("kind", LIST_KINDS)
    tasks = tuple(_task(item) for item in o.objs("tasks", _TASK_KEYS))
    for t in tasks:
        if t.pilot != (kind == LIST_PILOT):
            raise ShapeError(
                f"과제 목록: {kind} 목록에 파일럿인지가 {t.pilot}인 과제 {t.task_id}가 들었다"
            )
    _no_duplicates("과제 id", [t.task_id for t in tasks])
    _no_duplicates("실행 차례", [t.order for t in tasks])
    return TaskList(kind=kind, tasks=tasks)


def read_task_list(path: Path) -> TaskList:
    return parse_task_list(_read_text(path, "과제 목록"))


def write_task_list(path: Path, task_list: TaskList) -> None:
    path.write_text(dumps_task_list(task_list), encoding="utf-8", newline="\n")


# --- 회차 기록 ---


@dataclass(frozen=True)
class ResultEvent:
    """결과 이벤트 하나에서 옮기는 칸."""

    index: int  # 그 호출 안의 결과 이벤트 순번(0부터)
    subtype: str
    terminal_reason: str | None
    num_turns: int | None


@dataclass(frozen=True)
class Call:
    kind: str  # CALL_KINDS
    budget_usd: float  # 넘긴 `--max-budget-usd`
    exit_code: int | None  # 끈 호출 등 종료 코드를 모르면 빈 값
    results: tuple[ResultEvent, ...]
    has_directive: bool  # 결과 글이 지시문을 담았는지
    ends_with_question: bool  # 결과 글의 끝 줄이 물음표로 끝났는지
    kill_skipped: bool  # 끄지 않고 기록한 호출(명령 줄에 세션 id가 없었다, 08)


@dataclass(frozen=True)
class ModelUsage:
    """세션의 마지막 결과 이벤트의 `modelUsage` 한 모델."""

    model: str
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int
    thinking_tokens: int | None
    cost_usd: float


@dataclass(frozen=True)
class LineCount:
    """기록 파일의 assistant 줄을 모델과 노력으로 센 수. 노력을 보지 않거나 없으면 빈 값."""

    model: str
    effort: str | None
    lines: int


@dataclass(frozen=True)
class Session:
    session_id: str  # 러너가 지은 uuid
    calls: tuple[Call, ...]
    cost_usd: float | None  # 마지막 `total_cost_usd`. 대신 넣었으면 공식 단가의 값
    cost_substituted: bool  # 비용을 공식 단가 셈으로 대신 넣었다(10)
    runner_killed: bool  # 러너가 끈 호출이 있었다(08)
    model_usage: tuple[ModelUsage, ...]
    main_lines: tuple[LineCount, ...]  # 본 세션 기록 파일
    subagent_lines: tuple[LineCount, ...]  # `subagents/`의 기록 파일


@dataclass(frozen=True)
class End:
    kind: str  # END_REASONS의 키
    reason: str | None  # 끝남이면 빈 값
    resets_at: int | None  # 한도의 풀리는 시각(유닉스 초). 모르면 빈 값


@dataclass(frozen=True)
class Gate:
    command: str
    exit_code: int | None  # 시간을 넘겼으면 빈 값
    timed_out: bool


@dataclass(frozen=True)
class SetupFailure:
    """결과 작업 트리의 준비가 실패한 명령(07)."""

    command: str
    exit_code: int | None  # 시간을 넘겼으면 빈 값


@dataclass(frozen=True)
class Hidden:
    passed: int
    total: int
    failed: tuple[str, ...]  # 통과하지 못한 노드 ID


@dataclass(frozen=True)
class Outcome:
    commit: str | None  # 결과 커밋
    rule: str | None  # RULES. 고르지 않았으면 빈 값
    commits_after_base: int | None
    setup_failure: SetupFailure | None
    gates: tuple[Gate, ...] | None  # 돌지 않았으면 빈 값
    hidden: Hidden | None  # 돌지 않았으면 빈 값


@dataclass(frozen=True)
class Tokens:
    """토큰 합. 원본에 그 칸이 없으면 빈 값."""

    input: int | None
    output: int | None
    cache_read: int | None
    cache_write: int | None
    thinking: int | None


@dataclass(frozen=True)
class Substitute:
    """공식 단가 셈에서 기록 파일에 응답이 없어 `modelUsage`로 대신 셈한 모델과 그 토큰."""

    model: str
    tokens: Tokens


@dataclass(frozen=True)
class Window:
    window: str  # 한도 창의 이름(`five_hour` 등)
    utilization: float


@dataclass(frozen=True)
class Hit:
    """오염 검사에 걸린 꼴의 이름과 도구 이름. 입력은 옮기지 않는다."""

    pattern: str
    tool: str


@dataclass(frozen=True)
class Spend:
    claude_code_usd: float  # 세션마다 비용의 합
    official_usd: float  # 공식 단가의 셈
    tokens: Tokens
    substitutes: tuple[Substitute, ...]
    wall_seconds: float
    denied_calls: int  # 막는 규칙이 거부한 호출 수
    utilization_start: tuple[Window, ...]
    utilization_end: tuple[Window, ...]
    contamination: tuple[Hit, ...]
    model_mismatch: tuple[LineCount, ...]  # 허용 밖 모델(과 노력)의 줄 수


@dataclass(frozen=True)
class Record:
    """회차 하나(명세 "회차 기록"의 칸과 그 주석)."""

    # 식별
    task_id: str
    arm: str
    round_no: int  # 같은 과제·갈래의 몇째(1부터). 조건 판을 넘어 이어 센다
    condition_version: int
    pilot: bool
    round_dir: str
    # 환경
    claude_version: str | None
    account: str
    env_names: tuple[str, ...]
    init_tools: tuple[str, ...]
    # 세션
    sessions: tuple[Session, ...]
    # 이어 가기
    handoffs: int
    interventions: int
    asked_at_end: bool
    # 끝, 결과, 비용과 탐색
    end: End
    outcome: Outcome
    spend: Spend


_RESULT_KEYS = ("index", "subtype", "terminal_reason", "num_turns")
_CALL_KEYS = (
    "kind",
    "budget_usd",
    "exit_code",
    "results",
    "has_directive",
    "ends_with_question",
    "kill_skipped",
)
_USAGE_KEYS = (
    "model",
    "input_tokens",
    "output_tokens",
    "cache_read_tokens",
    "cache_write_tokens",
    "thinking_tokens",
    "cost_usd",
)
_LINES_KEYS = ("model", "effort", "lines")
_SESSION_KEYS = (
    "session_id",
    "calls",
    "cost_usd",
    "cost_substituted",
    "runner_killed",
    "model_usage",
    "main_lines",
    "subagent_lines",
)
_END_KEYS = ("kind", "reason", "resets_at")
_GATE_KEYS = ("command", "exit_code", "timed_out")
_SETUP_KEYS = ("command", "exit_code")
_HIDDEN_KEYS = ("passed", "total", "failed")
_OUTCOME_KEYS = ("commit", "rule", "commits_after_base", "setup_failure", "gates", "hidden")
_TOKENS_KEYS = ("input", "output", "cache_read", "cache_write", "thinking")
_SUBSTITUTE_KEYS = ("model", "tokens")
_WINDOW_KEYS = ("window", "utilization")
_HIT_KEYS = ("pattern", "tool")
_SPEND_KEYS = (
    "claude_code_usd",
    "official_usd",
    "tokens",
    "substitutes",
    "wall_seconds",
    "denied_calls",
    "utilization_start",
    "utilization_end",
    "contamination",
    "model_mismatch",
)
_RECORD_KEYS = (
    "task_id",
    "arm",
    "round_no",
    "condition_version",
    "pilot",
    "round_dir",
    "claude_version",
    "account",
    "env_names",
    "init_tools",
    "sessions",
    "handoffs",
    "interventions",
    "asked_at_end",
    "end",
    "outcome",
    "spend",
)


def _lines_json(c: LineCount) -> dict[str, Json]:
    return {"model": c.model, "effort": c.effort, "lines": c.lines}


def _tokens_json(t: Tokens) -> dict[str, Json]:
    return {
        "input": t.input,
        "output": t.output,
        "cache_read": t.cache_read,
        "cache_write": t.cache_write,
        "thinking": t.thinking,
    }


def _windows_json(ws: tuple[Window, ...]) -> list[Json]:
    return [{"window": w.window, "utilization": w.utilization} for w in ws]


def _session_json(s: Session) -> dict[str, Json]:
    return {
        "session_id": s.session_id,
        "calls": [
            {
                "kind": c.kind,
                "budget_usd": c.budget_usd,
                "exit_code": c.exit_code,
                "results": [
                    {
                        "index": r.index,
                        "subtype": r.subtype,
                        "terminal_reason": r.terminal_reason,
                        "num_turns": r.num_turns,
                    }
                    for r in c.results
                ],
                "has_directive": c.has_directive,
                "ends_with_question": c.ends_with_question,
                "kill_skipped": c.kill_skipped,
            }
            for c in s.calls
        ],
        "cost_usd": s.cost_usd,
        "cost_substituted": s.cost_substituted,
        "runner_killed": s.runner_killed,
        "model_usage": [
            {
                "model": u.model,
                "input_tokens": u.input_tokens,
                "output_tokens": u.output_tokens,
                "cache_read_tokens": u.cache_read_tokens,
                "cache_write_tokens": u.cache_write_tokens,
                "thinking_tokens": u.thinking_tokens,
                "cost_usd": u.cost_usd,
            }
            for u in s.model_usage
        ],
        "main_lines": [_lines_json(c) for c in s.main_lines],
        "subagent_lines": [_lines_json(c) for c in s.subagent_lines],
    }


def _outcome_json(o: Outcome) -> dict[str, Json]:
    setup: Json = None
    if o.setup_failure is not None:
        setup = {"command": o.setup_failure.command, "exit_code": o.setup_failure.exit_code}
    gates: Json = None
    if o.gates is not None:
        gates = [
            {"command": g.command, "exit_code": g.exit_code, "timed_out": g.timed_out}
            for g in o.gates
        ]
    hidden: Json = None
    if o.hidden is not None:
        hidden = {
            "passed": o.hidden.passed,
            "total": o.hidden.total,
            "failed": list(o.hidden.failed),
        }
    return {
        "commit": o.commit,
        "rule": o.rule,
        "commits_after_base": o.commits_after_base,
        "setup_failure": setup,
        "gates": gates,
        "hidden": hidden,
    }


def _spend_json(s: Spend) -> dict[str, Json]:
    return {
        "claude_code_usd": s.claude_code_usd,
        "official_usd": s.official_usd,
        "tokens": _tokens_json(s.tokens),
        "substitutes": [
            {"model": x.model, "tokens": _tokens_json(x.tokens)} for x in s.substitutes
        ],
        "wall_seconds": s.wall_seconds,
        "denied_calls": s.denied_calls,
        "utilization_start": _windows_json(s.utilization_start),
        "utilization_end": _windows_json(s.utilization_end),
        "contamination": [{"pattern": h.pattern, "tool": h.tool} for h in s.contamination],
        "model_mismatch": [_lines_json(c) for c in s.model_mismatch],
    }


def _record_json(r: Record) -> dict[str, Json]:
    return {
        "shape_version": SHAPE_VERSION,
        "task_id": r.task_id,
        "arm": r.arm,
        "round_no": r.round_no,
        "condition_version": r.condition_version,
        "pilot": r.pilot,
        "round_dir": r.round_dir,
        "claude_version": r.claude_version,
        "account": r.account,
        "env_names": list(r.env_names),
        "init_tools": list(r.init_tools),
        "sessions": [_session_json(s) for s in r.sessions],
        "handoffs": r.handoffs,
        "interventions": r.interventions,
        "asked_at_end": r.asked_at_end,
        "end": {"kind": r.end.kind, "reason": r.end.reason, "resets_at": r.end.resets_at},
        "outcome": _outcome_json(r.outcome),
        "spend": _spend_json(r.spend),
    }


def _lines(o: _Obj) -> LineCount:
    return LineCount(
        model=o.text("model", _MODEL), effort=o.opt_text("effort", _IDENT), lines=o.count("lines")
    )


def _tokens(o: _Obj) -> Tokens:
    return Tokens(
        input=o.opt_count("input"),
        output=o.opt_count("output"),
        cache_read=o.opt_count("cache_read"),
        cache_write=o.opt_count("cache_write"),
        thinking=o.opt_count("thinking"),
    )


def _windows(o: _Obj, key: str) -> tuple[Window, ...]:
    return tuple(
        Window(window=w.text("window", _IDENT), utilization=w.money("utilization"))
        for w in o.objs(key, _WINDOW_KEYS)
    )


def _call(o: _Obj) -> Call:
    return Call(
        kind=o.choice("kind", CALL_KINDS),
        budget_usd=o.money("budget_usd"),
        exit_code=o.opt_integer("exit_code"),
        results=tuple(
            ResultEvent(
                index=r.count("index"),
                subtype=r.text("subtype", _IDENT),
                terminal_reason=r.opt_text("terminal_reason", _IDENT),
                num_turns=r.opt_count("num_turns"),
            )
            for r in o.objs("results", _RESULT_KEYS)
        ),
        has_directive=o.flag("has_directive"),
        ends_with_question=o.flag("ends_with_question"),
        kill_skipped=o.flag("kill_skipped"),
    )


def _session(o: _Obj) -> Session:
    return Session(
        session_id=o.text("session_id", _UUID),
        calls=tuple(_call(c) for c in o.objs("calls", _CALL_KEYS)),
        cost_usd=o.opt_money("cost_usd"),
        cost_substituted=o.flag("cost_substituted"),
        runner_killed=o.flag("runner_killed"),
        model_usage=tuple(
            ModelUsage(
                model=u.text("model", _MODEL),
                input_tokens=u.count("input_tokens"),
                output_tokens=u.count("output_tokens"),
                cache_read_tokens=u.count("cache_read_tokens"),
                cache_write_tokens=u.count("cache_write_tokens"),
                thinking_tokens=u.opt_count("thinking_tokens"),
                cost_usd=u.money("cost_usd"),
            )
            for u in o.objs("model_usage", _USAGE_KEYS)
        ),
        main_lines=tuple(_lines(c) for c in o.objs("main_lines", _LINES_KEYS)),
        subagent_lines=tuple(_lines(c) for c in o.objs("subagent_lines", _LINES_KEYS)),
    )


def _end(o: _Obj) -> End:
    kind = o.choice("kind", tuple(END_REASONS))
    reasons = END_REASONS[kind]
    reason = o.opt_text("reason")
    if (reason is None) != (not reasons) or (reason is not None and reason not in reasons):
        raise ShapeError(
            f"{o.where}: 끝 '{kind}'의 하위 이유는 {reasons or '빈 값'}이다: {reason!r}"
        )
    resets_at = o.opt_count("resets_at")
    if resets_at is not None and reason != REASON_LIMIT:
        raise ShapeError(f"{o.where}.resets_at: 한도가 아닌 끝에는 빈 값이다")
    return End(kind=kind, reason=reason, resets_at=resets_at)


def _outcome(o: _Obj) -> Outcome:
    commit = o.opt_text("commit", _COMMIT)
    rule = o.opt_choice("rule", RULES)
    setup_obj = o.opt_obj("setup_failure", _SETUP_KEYS)
    setup = None
    if setup_obj is not None:
        setup = SetupFailure(
            command=setup_obj.choice("command", SETUP_COMMANDS),
            exit_code=setup_obj.opt_integer("exit_code"),
        )
    gates: tuple[Gate, ...] | None = None
    if not o.is_null("gates"):
        gates = tuple(
            Gate(
                command=g.choice("command", GATE_COMMANDS),
                exit_code=g.opt_integer("exit_code"),
                timed_out=g.flag("timed_out"),
            )
            for g in o.objs("gates", _GATE_KEYS)
        )
        if tuple(g.command for g in gates) != GATE_COMMANDS:
            raise ShapeError(f"{o.where}.gates: 게이트는 {GATE_COMMANDS} 셋이 이 차례로 든다")
    hidden_obj = o.opt_obj("hidden", _HIDDEN_KEYS)
    hidden = None
    if hidden_obj is not None:
        hidden = Hidden(
            passed=hidden_obj.count("passed"),
            total=hidden_obj.count("total"),
            failed=hidden_obj.strs("failed", _NODE),
        )
        for n in hidden.failed:
            hidden_test_file(n)
        if len(set(hidden.failed)) != len(hidden.failed):
            raise ShapeError(f"{o.where}.hidden.failed: 실패 노드가 겹친다")
        if hidden.passed + len(hidden.failed) != hidden.total:
            raise ShapeError(f"{o.where}.hidden: 통과 수와 실패 노드 수의 합이 전체 수가 아니다")
    if (commit is None) != (rule in (None, RULE_NONE)):
        raise ShapeError(f"{o.where}: 결과 커밋 {commit!r}과 고른 규칙 {rule!r}이 맞지 않는다")
    ran = setup is not None or gates is not None or hidden is not None
    if commit is None and ran:
        raise ShapeError(f"{o.where}: 결과 커밋이 없는 회차에는 준비·게이트·숨은 시험이 없다")
    if setup is not None and (gates is not None or hidden is not None):
        raise ShapeError(f"{o.where}: 준비가 실패한 회차에는 게이트와 숨은 시험이 없다")
    return Outcome(
        commit=commit,
        rule=rule,
        commits_after_base=o.opt_count("commits_after_base"),
        setup_failure=setup,
        gates=gates,
        hidden=hidden,
    )


def _spend(o: _Obj) -> Spend:
    return Spend(
        claude_code_usd=o.money("claude_code_usd"),
        official_usd=o.money("official_usd"),
        tokens=_tokens(o.obj("tokens", _TOKENS_KEYS)),
        substitutes=tuple(
            Substitute(model=x.text("model", _MODEL), tokens=_tokens(x.obj("tokens", _TOKENS_KEYS)))
            for x in o.objs("substitutes", _SUBSTITUTE_KEYS)
        ),
        wall_seconds=o.money("wall_seconds"),
        denied_calls=o.count("denied_calls"),
        utilization_start=_windows(o, "utilization_start"),
        utilization_end=_windows(o, "utilization_end"),
        contamination=tuple(
            Hit(pattern=h.text("pattern", _PATTERN_NAME), tool=h.text("tool", _TOOL))
            for h in o.objs("contamination", _HIT_KEYS)
        ),
        model_mismatch=tuple(_lines(c) for c in o.objs("model_mismatch", _LINES_KEYS)),
    )


def dumps_record(record: Record) -> str:
    """회차 기록의 글. 읽기로 다시 풀어 보고 거부되면 `ShapeError`다."""
    text = _dumps(_record_json(record))
    parse_record(text)
    return text


def parse_record(text: str) -> Record:
    o = _top(text, "회차 기록", _RECORD_KEYS)
    end = _end(o.obj("end", _END_KEYS))
    outcome = _outcome(o.obj("outcome", _OUTCOME_KEYS))
    if end.kind != END_DONE and (
        outcome.setup_failure is not None or outcome.gates is not None or outcome.hidden is not None
    ):
        raise ShapeError(f"회차 기록: 준비·게이트·숨은 시험은 '{END_DONE}'인 회차에서만 돈다")
    if end.kind == END_DONE and outcome.commit is None:
        # 명세 "이어 가기와 끝"의 갈래 2: 결과 커밋이 B 뒤에 있어야 끝남이다.
        raise ShapeError(f"회차 기록: '{END_DONE}'인 회차에는 결과 커밋이 있다")
    task_id = o.text("task_id", _TASK_ID)
    arm = o.choice("arm", tuple(ARM_BY_NAME))
    round_no = o.count("round_no")
    if round_no < 1:
        raise ShapeError("회차 기록.round_no: 1부터 센다")
    round_dir = o.text("round_dir", _ROUND_DIR)
    named = parse_round_dir_name(re.split(r"[\\/]", round_dir)[-1])
    if named is None or (named.task_id, named.arm, named.round_no) != (task_id, arm, round_no):
        raise ShapeError(
            f"회차 기록.round_dir: 마지막 조각이 이 회차의 폴더 이름이 아니다: {round_dir!r}"
        )
    return Record(
        task_id=task_id,
        arm=arm,
        round_no=round_no,
        condition_version=o.count("condition_version"),
        pilot=o.flag("pilot"),
        round_dir=round_dir,
        claude_version=o.opt_text("claude_version", _VERSION),
        account=o.text("account", _ACCOUNT),
        env_names=o.strs("env_names", _ENV_NAME),
        init_tools=o.strs("init_tools", _TOOL),
        sessions=tuple(_session(s) for s in o.objs("sessions", _SESSION_KEYS)),
        handoffs=o.count("handoffs"),
        interventions=o.count("interventions"),
        asked_at_end=o.flag("asked_at_end"),
        end=end,
        outcome=outcome,
        spend=_spend(o.obj("spend", _SPEND_KEYS)),
    )


def read_record(path: Path) -> Record:
    return parse_record(_read_text(path, "회차 기록"))


def write_record(records_dir: Path, record: Record) -> Path:
    """`records_dir`에 기록을 쓰고 그 경로를 낸다. 이미 있는 파일은 덮지 않고
    `FileExistsError`다."""
    text = dumps_record(record)
    path = records_dir / record_file_name(record.task_id, record.arm, record.round_no)
    with path.open("x", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return path


# --- 판정이 읽는 칸 ---


@dataclass(frozen=True)
class JudgeView:
    """판정(03)이 읽는 칸(명세 "회차 기록"의 판정이 읽는 칸과 그 주석의 식별·탐색 칸)."""

    task_id: str
    arm: str
    round_no: int
    pilot: bool
    condition_version: int
    claude_version: str | None
    end: End
    gates_green: bool | None  # 게이트 셋이 모두 종료 0. 돌지 않았으면 빈 값
    hidden_passed: bool | None  # 숨은 시험이 모두 통과. 돌지 않았으면 빈 값
    cost_claude_code_usd: float
    cost_official_usd: float
    interventions: int
    asked_at_end: bool
    tokens: Tokens
    wall_seconds: float
    denied_calls: int
    utilization_start: tuple[Window, ...]
    utilization_end: tuple[Window, ...]
    cost_substituted: bool  # 세션 비용을 공식 단가 셈으로 대신 넣은 세션이 있다
    official_substituted: bool  # 공식 단가 셈에 `modelUsage`로 대신 셈한 모델이 있다
    setup_failed: bool  # 결과 작업 트리의 준비가 실패했다


def judge_view(record: Record) -> JudgeView:
    o = record.outcome
    gates_green = None
    if o.gates is not None:
        gates_green = all(g.exit_code == 0 and not g.timed_out for g in o.gates)
    hidden_passed = None
    if o.hidden is not None:
        hidden_passed = o.hidden.total > 0 and o.hidden.passed == o.hidden.total
    s = record.spend
    return JudgeView(
        task_id=record.task_id,
        arm=record.arm,
        round_no=record.round_no,
        pilot=record.pilot,
        condition_version=record.condition_version,
        claude_version=record.claude_version,
        end=record.end,
        gates_green=gates_green,
        hidden_passed=hidden_passed,
        cost_claude_code_usd=s.claude_code_usd,
        cost_official_usd=s.official_usd,
        interventions=record.interventions,
        asked_at_end=record.asked_at_end,
        tokens=s.tokens,
        wall_seconds=s.wall_seconds,
        denied_calls=s.denied_calls,
        utilization_start=s.utilization_start,
        utilization_end=s.utilization_end,
        cost_substituted=any(x.cost_substituted for x in record.sessions),
        official_substituted=bool(s.substitutes),
        setup_failed=o.setup_failure is not None,
    )


def read_judge_view(path: Path) -> JudgeView:
    return judge_view(read_record(path))


# --- `records/`의 파일 이름, 회차 폴더, 다음 회차 번호 ---


@dataclass(frozen=True)
class RoundName:
    task_id: str
    arm: str
    round_no: int
    token: str | None  # 회차 폴더의 짧은 난수. 기록 파일 이름에는 없다


def _check_round(task_id: str, arm: str, round_no: int) -> None:
    if not _TASK_ID.fullmatch(task_id):
        raise ShapeError(f"과제 id가 아니다: {task_id!r}")
    if arm not in ARM_BY_NAME:
        raise ShapeError(f"갈래 이름이 아니다: {arm!r}")
    if round_no < 1:
        raise ShapeError(f"회차 번호는 1부터다: {round_no}")


def record_file_name(task_id: str, arm: str, round_no: int) -> str:
    """`records/`의 파일 이름 `<과제 id>-<갈래>-<회차 번호>.json`."""
    _check_round(task_id, arm, round_no)
    return f"{task_id}-{arm}-{round_no}.json"


def round_dir_name(task_id: str, arm: str, round_no: int, token: str) -> str:
    """회차 폴더의 이름 `<과제 id>-<갈래>-<회차 번호>-<짧은 난수>`."""
    _check_round(task_id, arm, round_no)
    if not _TOKEN.fullmatch(token):
        raise ShapeError(f"짧은 난수는 영소문자와 숫자다: {token!r}")
    return f"{task_id}-{arm}-{round_no}-{token}"


def _parse_name(parts: list[str], token: str | None) -> RoundName | None:
    task_id, arm, number = parts
    if not (_TASK_ID.fullmatch(task_id) and arm in ARM_BY_NAME and number.isascii()):
        return None
    if not number.isdigit() or int(number) < 1 or str(int(number)) != number:
        return None
    return RoundName(task_id=task_id, arm=arm, round_no=int(number), token=token)


def parse_round_dir_name(name: str) -> RoundName | None:
    """회차 폴더 이름을 푼다. 과제 id에 `-`가 들어 오른쪽에서 자른다. 회차 폴더가 아니면 빈 값."""
    parts = name.rsplit("-", 3)
    if len(parts) != 4 or not _TOKEN.fullmatch(parts[3]):
        return None
    return _parse_name(parts[:3], parts[3])


def parse_record_file_name(name: str) -> RoundName | None:
    """기록 파일 이름을 푼다. 기록 파일이 아니면 빈 값."""
    stem, dot, ext = name.rpartition(".")
    if not dot or ext != "json":
        return None
    parts = stem.rsplit("-", 2)
    if len(parts) != 3:
        return None
    return _parse_name(parts, None)


def next_round_no(
    task_id: str, arm: str, record_names: Iterable[str], round_dir_names: Iterable[str]
) -> int:
    """그 과제·갈래의 다음 회차 번호. `records/`의 파일 이름과 뿌리 아래 폴더 이름을 함께 본다.

    기록은 회차가 끝날 때 쓰므로 `records/`만 보면 동시에 도는 두 회차와 죽은 러너가 남긴 회차가
    같은 번호를 받는다(명세 "차례, 동시성, 예산"의 주석). 번호를 잡고 폴더를 만드는 차례는 부르는
    쪽(10)이 지킨다. 파일 이름에 조건 판이 없어 번호는 판을 넘어 이어진다.
    """
    found = [parse_record_file_name(n) for n in record_names]
    found += [parse_round_dir_name(n) for n in round_dir_names]
    numbers = [f.round_no for f in found if f is not None and (f.task_id, f.arm) == (task_id, arm)]
    return max(numbers, default=0) + 1


# --- 읽기 도우미 ---


def _dumps(value: dict[str, Json]) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"


def _read_text(path: Path, what: str) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        raise ShapeError(f"{what}: UTF-8이 아니다({e})") from e


def _top(text: str, what: str, keys: tuple[str, ...]) -> _Obj:
    try:
        value: Json = json.loads(text)
    except (json.JSONDecodeError, RecursionError) as e:
        raise ShapeError(f"{what}: JSON이 아니다({e})") from e
    if not isinstance(value, dict):
        raise ShapeError(f"{what}: 맨 위가 객체가 아니다")
    version = value.get("shape_version")
    if not _is_int(version) or version != SHAPE_VERSION:
        raise ShapeError(f"{what}: 모르는 꼴 판 {version!r}(이 모듈은 {SHAPE_VERSION})")
    return _Obj(value, what, ("shape_version", *keys))


def _no_duplicates(what: str, values: list[str] | list[int]) -> None:
    seen: set[str | int] = set()
    for v in values:
        if v in seen:
            raise ShapeError(f"과제 목록: {what} {v!r}가 겹친다")
        seen.add(v)


def _is_int(v: Json) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


class _Obj:
    """키가 정해진 JSON 객체 하나. 빠진 키와 모르는 키를 거부하고, 값마다 형을 확인해 꺼낸다."""

    def __init__(self, value: Json, where: str, keys: tuple[str, ...]) -> None:
        if not isinstance(value, dict):
            raise ShapeError(f"{where}: 객체가 아니다")
        missing = [k for k in keys if k not in value]
        if missing:
            raise ShapeError(f"{where}: 빠진 키 {missing}")
        unknown = [k for k in value if k not in keys]
        if unknown:
            raise ShapeError(f"{where}: 모르는 키 {unknown}")
        self._value = value
        self.where = where

    def _get[T](self, key: str, kind: str, ok: Callable[[Json], T | None]) -> T:
        v = self._value[key]
        got = ok(v)
        if got is None:
            raise ShapeError(f"{self.where}.{key}: {kind}가 아니다: {v!r}")
        return got

    def is_null(self, key: str) -> bool:
        return self._value[key] is None

    def text(self, key: str, pattern: re.Pattern[str] | None = None) -> str:
        def ok(v: Json) -> str | None:
            if not isinstance(v, str) or not v:
                return None
            return v if pattern is None or pattern.fullmatch(v) else None

        return self._get(key, "정해진 꼴의 문자열", ok)

    def opt_text(self, key: str, pattern: re.Pattern[str] | None = None) -> str | None:
        return None if self.is_null(key) else self.text(key, pattern)

    def choice(self, key: str, values: tuple[str, ...]) -> str:
        return self._get(key, f"{values} 가운데 하나", lambda v: v if v in values else None)

    def opt_choice(self, key: str, values: tuple[str, ...]) -> str | None:
        return None if self.is_null(key) else self.choice(key, values)

    def flag(self, key: str) -> bool:
        v = self._value[key]
        if not isinstance(v, bool):
            raise ShapeError(f"{self.where}.{key}: 참거짓이 아니다: {v!r}")
        return v

    def integer(self, key: str) -> int:
        return self._get(key, "정수", lambda v: v if isinstance(v, int) and _is_int(v) else None)

    def opt_integer(self, key: str) -> int | None:
        return None if self.is_null(key) else self.integer(key)

    def count(self, key: str) -> int:
        """0 이상의 정수."""

        def ok(v: Json) -> int | None:
            return v if isinstance(v, int) and _is_int(v) and v >= 0 else None

        return self._get(key, "0 이상의 정수", ok)

    def opt_count(self, key: str) -> int | None:
        return None if self.is_null(key) else self.count(key)

    def money(self, key: str) -> float:
        """0 이상의 유한한 수(정수도 받는다)."""

        def ok(v: Json) -> float | None:
            if isinstance(v, bool) or not isinstance(v, int | float):
                return None
            if not math.isfinite(v) or v < 0:
                return None
            return float(v)

        return self._get(key, "0 이상의 수", ok)

    def opt_money(self, key: str) -> float | None:
        return None if self.is_null(key) else self.money(key)

    def _list(self, key: str) -> list[Json]:
        v = self._value[key]
        if not isinstance(v, list):
            raise ShapeError(f"{self.where}.{key}: 목록이 아니다: {v!r}")
        return v

    def strs(self, key: str, pattern: re.Pattern[str] | None = None) -> tuple[str, ...]:
        out: list[str] = []
        for i, v in enumerate(self._list(key)):
            if not isinstance(v, str) or not v or (pattern and not pattern.fullmatch(v)):
                raise ShapeError(f"{self.where}.{key}[{i}]: 정해진 꼴의 문자열이 아니다: {v!r}")
            out.append(v)
        return tuple(out)

    def obj(self, key: str, keys: tuple[str, ...]) -> _Obj:
        return _Obj(self._value[key], f"{self.where}.{key}", keys)

    def opt_obj(self, key: str, keys: tuple[str, ...]) -> _Obj | None:
        return None if self.is_null(key) else self.obj(key, keys)

    def objs(self, key: str, keys: tuple[str, ...]) -> list[_Obj]:
        return [_Obj(v, f"{self.where}.{key}[{i}]", keys) for i, v in enumerate(self._list(key))]
