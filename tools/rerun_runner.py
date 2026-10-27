"""다시 풀기의 러너 명령. 과제 목록 하나를 받아 과제를 실행 차례대로 돌고, 과제마다 갈래 계획의
회차를 동시에 둘까지 돌린 뒤 다음 과제로 간다.

명세는 `.scratch/model-rerun/spec.md`의 "차례, 동시성, 예산"·"한도"·"오염 검사"·"이어 가기와 끝"·
"클론과 설정 폴더"·"상한과 끄기"·"파일럿과 사전 등록"과 그 주석들이고 티켓은
`.scratch/model-rerun/issues/10-schedule-and-budget.md`다. 부르는 꼴은
`python -m tools.rerun_runner <과제 목록> --root ... --config-dir ... --account ... --claude ...
--cap ...`이다.

회차 하나는 04의 자리(`tools/rerun_round.py`), 09의 열기 전 확인과 판정(`tools/rerun_checks.py`),
08의 이어 가기(`tools/rerun_continue.py`), 07의 게이트(`tools/rerun_gates.py`)와 공식 단가
(`tools/rerun_cost.py`)를 차례로 잇고 01의 꼴(`tools/rerun_files.py`)로 `records/`에 쓴다. 회차를
열기 전의 확인과 회차 번호 잡기, 폴더 만들기는 주 스레드 한 곳에서 차례로 하고, 준비부터 기록
쓰기까지는 일꾼 스레드가 회차마다 따로 한다. 그래서 함께 도는 두 회차가 같은 번호를 받지 않는다.

시작 전 점검의 차례.
1. 본 측정 목록이면 사전 등록 절의 해시를 판정 도구(03)의 상수와 대 본다. 파일럿 목록은 보지 않는다.
2. 뿌리 아래 기록 없는 회차 폴더(죽은 러너가 남긴 것)를 찾는다. 그 세션 id가 명령 줄에 든 `claude`
   프로세스가 돌거나, 이름이 같은 프로세스의 명령 줄을 읽지 못하면 멈춘다. 아니면 측정
   아님(중단)으로 적는다.
3. 지금 판의 본 측정 기록에 인계가 있는데 그 판의 확인 인자가 없으면 멈춘다(본 측정 목록일 때).
4. 가장 늦은 한도 기록의 풀리는 시각이 아직 오지 않았으면 그때까지 잔다.

과제마다 다시 띄우기의 판정(`plan_task`)으로 돌 갈래를 고르고, 시작하기 전에 쓴 것과 그 갈래의
어림(`estimate_usd`)의 합이 상한을 넘으면 멈춘다. 회차가 끝나면 끝마다 다룬다. 한도는 그 갈래를 다시
줄 앞에 넣고 함께 돌던 회차가 끝난 뒤 풀리는 시각까지 잔다(시각을 모르면 멈춘다). 오염은 같은
과제·갈래·판의 둘째이면 그 과제를 빼고, 첫째면 다시 돈다. 설정·준비·호출·모델·계정은 멈춘다. 본
측정에서 인계가 난 회차가 끝나면 그 판의 확인이 없을 때 멈춘다. 멈출 때 함께 돌던 회차는 끝까지 두고
새 회차는 열지 않는다.

구현에서 정한 것.
- 끈 호출이나 결과 이벤트 없이 끝난 호출이 든 세션(호출의 `results`가 빈 세션)은 비용 칸에 그 세션의
  공식 단가 셈을 대신 넣고 `cost_substituted`를 세운다(08의 메모). 본 세션 기록 파일이 없으면 그
  세션의 마지막 `modelUsage`만으로 셈한다(대개 0이다).
- 회차 세션의 기록 파일이 든 프로젝트 폴더에 남은 다른 세션(과제의 시험이 띄운 하위 `claude -p`)의
  공식 단가 셈은 `other_usd`에 넣고, 예산의 쓴 것과 판정의 두 비용에 더한다(`other_transcripts`,
  사람이 정했다, 일지 2026-10-28-10).
- 끝남인 회차에서 게이트 작업 트리를 짓지 못하거나(`GateError`) 로그를 쓰지 못하면(`OSError`) 그
  회차를 측정 아님(준비)으로 적고 멈춘다. 세션이 쓴 결과와 별개로 사람이 볼 일일 수 있다(07의 메모).
- 기록의 게이트와 준비 명령은 갈아 끼운 명령이 아니라 그 자리의 정해진 이름(`GATE_COMMANDS`나
  `OLD_GATE_COMMANDS`, `SETUP_COMMANDS`)으로 적는다. 시험이 갈아 끼운 명령도 기록의 꼴을 지나게
  하려는 것이다.
- 게이트 묶음은 과제의 B 에 게이트 러너(`GATE_FILE`)가 있는지로 고른다(`tools/rerun_gates.py`의
  `has_gate_file`). 없으면 옛 묶음(`old_gates`)을 돈다. 가르지 못하면 게이트 작업 트리를 짓지 못한
  것과 같이 측정 아님(준비)으로 적고 멈춘다.
- 끄지 못하고 남긴 호출(`LEFT_RUNNING`)이 든 회차가 끝나면 그 프로세스가 돌 수 있어 멈춘다.
- 공식 단가에 단가가 없는 모델(`PriceError`)이 나면 그 회차를 적지 못하고 멈춘다. 기록 없는 폴더가
  남고, 다시 띄우면 그 폴더를 측정 아님(중단)으로 적으려고 같은 세션을 다시 셈하다 같은 까닭으로
  멈춘다. 단가표(`tools/rerun_cost.py`)에 그 모델을 더한 뒤 다시 띄우면 중단으로 적힌다.

못 보는 것. 강제로 죽은 러너가 `records/`에 남긴 임시 파일(`.….tmp`)은 지우지 않는다. 기록 파일
이름으로 풀리지 않아 번호 셈과 예산과 판정이 보지 않는다(01의 `write_record` 독스트링). 기록 없는
회차 폴더의 프로세스는 이름이 띄운 `claude` 실행 파일의 끝 이름과 같은 것만 훑어, 다른 이름으로 띄운
세션(래퍼, 셸 스크립트)은 보지 못한다. 명령 줄 입구는 `--claude`가 파일이면 그 절대 경로를, 아니면
`shutil.which`로 푼 실제 경로를 써서 그 끝 이름을 쓴다. 같은 뿌리와 `records/`에 러너 둘을 함께
띄우는 것은 막지 않는다. 뒤에 뜬 러너는 앞 러너가 준비 중인(세션 id를 아직 적지 않은) 회차를 죽은
회차로 적고, 앞 러너는 그 회차의 기록을 쓰다 `FileExistsError`로 멈춘다. 하위 세션의 비용은 회차
세션과 같은 프로젝트 폴더(같은 작업 폴더와 설정 폴더)에 남은 기록만 센다. 다른 폴더에서 띄웠거나
다른 설정 폴더를 쓴 하위 세션, 기록을 남기지 않는 하위 세션은 빠진다. 하위 세션의 `modelUsage`는
러너가 받지 못해 기록 파일의 응답으로만 셈하므로(`tools/rerun_cost.py`의 채우기를 하지 못한다)
실제보다 낮을 수 있다. 파일럿 회차 기록의 응답 셈(서브에이전트 기록 포함)은 그 회차 `costUSD`의
0.72~1.00배였다(`.scratch/model-rerun/probes/official_cost/`).
"""

from __future__ import annotations

import argparse
import io
import math
import os
import shutil
import sys
import time
from collections import Counter, deque
from collections.abc import Callable, Sequence
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import dataclass, field, replace
from pathlib import Path

from tools.proc_command_line import CommandLineReader, command_line, pids_named
from tools.rerun_checks import REASON_CONTAMINATION, before_round, screen_for
from tools.rerun_continue import run_sessions
from tools.rerun_cost import Cost, PriceError, cost_of, round_cost, transcript_lines
from tools.rerun_files import (
    ARM_BY_NAME,
    END_DONE,
    END_NOT_MEASURED,
    GATE_COMMANDS,
    LIST_MAIN,
    OLD_GATE_COMMANDS,
    REASON_LIMIT,
    SETUP_COMMANDS,
    End,
    Gate,
    Json,
    ModelUsage,
    Outcome,
    Record,
    Session,
    SetupFailure,
    ShapeError,
    Spend,
    Task,
    TaskList,
    next_round_no,
    parse_record_file_name,
    parse_round_dir_name,
    read_record,
    read_task_list,
    write_record,
)
from tools.rerun_gates import (
    GATE_ARGV,
    OLD_GATE_ARGV,
    PYTEST_ARGV,
    GateError,
    Limits,
    check_result,
    has_gate_file,
)
from tools.rerun_judge import PREREG_README, PREREG_SHA256, prereg_problem
from tools.rerun_round import (
    RECORDS,
    ROOT,
    SETUP_ARGV,
    CloneError,
    PlaceError,
    RoundDir,
    checked_place,
    checked_root,
    create_round_dir,
    deny_heads,
    deny_rules,
    main_checkout,
    prepare_round,
    root_heads,
    session_env,
    unrecorded_round_dirs,
)
from tools.rerun_session import (
    LEFT_RUNNING,
    Continued,
    Elsewhere,
    claude_version,
    directive,
    local_branches,
    outcome_of,
    pick_result_commit,
    round_record,
    session_cost,
    summarize_call,
    ticket_title,
    transcript_counts,
    transcript_files,
)

# 조건 판. 회차 조건(하네스, 단가, 판정 규칙)을 고치면 올린다. 회차 기록에 적는다
CONDITION_VERSION = 4
MAX_PARALLEL = 2
# 갈래마다 원래 PR 앞 비용에 곱하는 비율의 위 끝(설계 7절)
ARM_RATIOS: dict[str, float] = {"A": 1.0, "B": 0.8, "C": 0.7, "D": 0.9, "E": 0.7}
REASON_SETUP = "준비"
REASON_INTERRUPTED = "중단"

# 사전 등록 절과 대 보는 값(`tools/rerun_files.py`의 `prereg_line`).
PREREG_VALUES: dict[str, Json] = {
    "CONDITION_VERSION": CONDITION_VERSION,
    "MAX_PARALLEL": MAX_PARALLEL,
    "ARM_RATIOS": {**ARM_RATIOS},
}

EXIT_DONE = 0  # 목록을 다 돌았다
EXIT_HALTED = 1  # 멈춰 사람에게 넘겼다
EXIT_USAGE = 2  # 명령 줄이 잘못돼 아무것도 하지 않았다


@dataclass(frozen=True)
class Settings:
    """명령 줄에서 온 값. 시험은 임시 경로와 지은 해시를 넘긴다."""

    task_list: TaskList
    root: Path  # 회차 폴더의 뿌리(`checked_root`가 본 것)
    config_dir: str  # 전용 설정 폴더. 정규화하지 않은 글 그대로다(09의 메모)
    account: str
    claude: tuple[str, ...]
    cap_usd: float
    records: Path
    readme: Path  # 사전 등록 절이 든 README
    expected_sha256: str
    source: Path  # B와 M을 담은 원본 저장소
    main_checkout: Path
    confirmed: int | None  # 인계를 확인한 조건 판
    rerun: frozenset[str]  # 명령 줄로 준 과제 id
    condition_version: int = CONDITION_VERSION


@dataclass(frozen=True)
class World:
    """러너가 바깥과 만나는 자리. 시험은 시계·잠·프로세스 훑기와 게이트 명령을 갈아 끼운다."""

    out: Callable[[str], None] = print
    now: Callable[[], float] = time.time  # 유닉스 초. 한도의 풀리는 시각과 견준다
    sleep: Callable[[float], None] = time.sleep
    processes: Callable[[str], list[int] | None] = pids_named
    read_command_line: CommandLineReader = command_line
    setup: tuple[tuple[str, ...], ...] = SETUP_ARGV
    gates: tuple[tuple[str, ...], ...] = GATE_ARGV
    old_gates: tuple[tuple[str, ...], ...] = OLD_GATE_ARGV
    pytest: tuple[str, ...] = PYTEST_ARGV
    limits: Limits = Limits()
    home: Path = field(default_factory=Path.home)

    def __post_init__(self) -> None:
        if (
            len(self.setup) != len(SETUP_COMMANDS)
            or len(self.gates) != len(GATE_COMMANDS)
            or len(self.old_gates) != len(OLD_GATE_COMMANDS)
        ):
            raise ValueError("준비와 게이트 명령의 수는 정해진 명령의 수와 같아야 한다")


@dataclass(frozen=True)
class Plan:
    """그 과제에서 돌 갈래. 갈래 계획의 차례이고 비었으면 건너뛴다."""

    arms: tuple[str, ...]


@dataclass(frozen=True)
class Halt:
    """회차를 열지 않고 멈출 까닭."""

    why: str


def estimate_usd(task: Task, arms: Sequence[str]) -> float:
    """원래 PR 앞 비용에 `arms`의 비율 합을 곱한 어림."""
    return task.pr_cost_usd * sum(ARM_RATIOS[a] for a in arms)


def _remaining(task: Task, records: Sequence[Record], version: int) -> tuple[str, ...]:
    """판 `version`에서 갈래 계획 가운데 아직 끝나지 않은 회차. 측정 아님은 끝난 회차가 아니다.
    같은 갈래가 두 번 든 계획은 그 갈래의 끝난 기록 수만큼 앞에서 지운다."""
    done = Counter(
        r.arm
        for r in records
        if r.task_id == task.task_id
        and r.condition_version == version
        and r.end.kind != END_NOT_MEASURED
    )
    left: list[str] = []
    for arm in task.arm_plan:
        if done[arm] > 0:
            done[arm] -= 1
        else:
            left.append(arm)
    return tuple(left)


def _contaminated(task: Task, records: Sequence[Record], version: int, arm: str) -> int:
    """판 `version`의 그 갈래에서 측정 아님(오염)인 기록 수."""
    return sum(
        1
        for r in records
        if (r.task_id, r.arm, r.condition_version) == (task.task_id, arm, version)
        and r.end.kind == END_NOT_MEASURED
        and r.end.reason == REASON_CONTAMINATION
    )


def _excluded(task: Task, records: Sequence[Record], version: int) -> bool:
    return any(_contaminated(task, records, version, a) >= 2 for a in set(task.arm_plan))


def plan_task(task: Task, records: Sequence[Record], *, condition: int, rerun: bool) -> Plan | Halt:
    """다시 띄우기의 판정(명세 "차례, 동시성, 예산"의 다시 띄우기 주석). `records`는 모든 기록이고
    `rerun`은 명령 줄로 그 과제 id를 줬는지다.

    그 과제의 가장 큰 판 V가 C보다 크면 id를 줬어도 멈춘다(판을 내린 러너). id를 준 과제는 판
    `condition`(C)에서 남은 회차를 돈다(오염으로 뺀 것보다 앞선다). 그 밖은 기록이 없으면 갈래
    계획을 다 돈다. V에서 다 마쳤거나 오염으로 뺐으면 건너뛴다. V = C이면 남은 회차를 돌고, V <
    C이면 멈춰 그 id를 낸다."""
    versions = [r.condition_version for r in records if r.task_id == task.task_id]
    top = max(versions, default=condition)
    if top > condition:
        return Halt(f"{task.task_id} 의 기록에 러너의 판 {condition} 보다 큰 판 {top} 이 있다")
    if rerun:
        return Plan(_remaining(task, records, condition))
    if not versions:
        return Plan(task.arm_plan)
    if not _remaining(task, records, top) or _excluded(task, records, top):
        return Plan(())
    if top == condition:
        return Plan(_remaining(task, records, condition))
    return Halt(
        f"{task.task_id} 를 판 {top} 에서 다 마치지 못했는데 러너의 판은 {condition} 이다. "
        f"올린 판에서 다시 돌려면 --rerun {task.task_id} 를 준다"
    )


@dataclass(frozen=True)
class _Done:
    """일꾼이 회차 하나를 마친 꼴. `halt`가 있으면 그 회차 뒤 멈춘다."""

    record: Record
    halt: str | None = None


_ZERO = round_cost(())


def _elsewhere_zero() -> Elsewhere:
    return Elsewhere(
        official_usd=0.0,
        tokens=_ZERO.tokens,
        substitutes=(),
        denied_calls=0,
        utilization_start=(),
        utilization_end=(),
        contamination=(),
        model_mismatch=(),
    )


def _official(config_dir: Path, session_id: str, usage: Sequence[ModelUsage]) -> Cost:
    """세션 하나의 공식 단가 셈. 본 세션 기록 파일이 없으면 `modelUsage`만으로 셈한다."""
    main, _ = transcript_files(config_dir, session_id)
    return cost_of([line for p in main for line in transcript_lines(p)], usage)


def other_transcripts(config_dir: Path, session_ids: Sequence[str]) -> list[Path]:
    """회차 세션의 기록 파일이 든 프로젝트 폴더에서 회차 세션이 아닌 세션의 기록 파일(이름 차례).
    회차마다 클론이 달라 프로젝트 폴더도 다르므로, 거기 남은 다른 세션은 그 회차 안에서 띄운 하위
    `claude -p`(과제의 시험이 띄운 것)다."""
    own = set(session_ids)
    folders = {p.parent for sid in session_ids for p in transcript_files(config_dir, sid)[0]}
    return sorted(
        p for d in folders for p in d.glob("*.jsonl") if p.is_file() and p.stem not in own
    )


def _other_usd(config_dir: Path, session_ids: Sequence[str]) -> float:
    """`other_transcripts`의 공식 단가 셈의 합. 그 세션의 `modelUsage`는 러너가 받지 못해 기록
    파일의 응답으로만 셈한다."""
    others = other_transcripts(config_dir, session_ids)
    return sum(cost_of(transcript_lines(p), ()).official_usd for p in others)


def _with_costs(record: Record, config_dir: Path) -> Record:
    """공식 단가를 셈하고, 결과 이벤트가 없는 호출이 든 세션의 비용 칸에 그 셈을 대신 넣는다. 같은
    프로젝트 폴더에 남은 다른 세션의 공식 단가 셈은 `other_usd`에 넣는다(사람이 정했다, 일지
    2026-10-28-10)."""
    costs: list[Cost] = []
    sessions: list[Session] = []
    for s in record.sessions:
        cost = _official(config_dir, s.session_id, s.model_usage)
        costs.append(cost)
        if any(not c.results for c in s.calls):
            s = replace(s, cost_usd=cost.official_usd, cost_substituted=True)
        sessions.append(s)
    other_usd = _other_usd(config_dir, [s.session_id for s in record.sessions])
    return replace(
        record, sessions=tuple(sessions), spend=_spend(record, sessions, costs, other_usd)
    )


def _spend(
    record: Record, sessions: Sequence[Session], costs: Sequence[Cost], other_usd: float
) -> Spend:
    """세션의 비용 칸 합, 공식 단가 셈의 합, 다른 세션의 공식 단가 셈을 기록의 비용에 넣는다."""
    total = round_cost(costs)
    return replace(
        record.spend,
        claude_code_usd=sum(s.cost_usd for s in sessions if s.cost_usd is not None),
        official_usd=total.official_usd,
        other_usd=other_usd,
        tokens=total.tokens,
        substitutes=total.substitutes,
    )


class _Runner:
    def __init__(self, settings: Settings, world: World) -> None:
        self.settings = settings
        self.world = world
        self.config = Path(settings.config_dir)
        self.rules = deny_rules(
            deny_heads(settings.main_checkout, home=world.home), roots=root_heads(settings.root)
        )
        self.main_list = settings.task_list.kind == LIST_MAIN

    # --- 주 스레드 ---

    def run(self) -> int:
        s = self.settings
        tasks = sorted(s.task_list.tasks, key=lambda t: t.order)
        s.records.mkdir(parents=True, exist_ok=True)
        if self.main_list:
            problem = prereg_problem(s.readme.read_text(encoding="utf-8"), s.expected_sha256)
            if problem is not None:
                return self._halt(f"사전 등록 절이 맞지 않아 아무 회차도 열지 않는다: {problem}")
        why = self._close_dead_rounds(tasks)
        if why is not None:
            return self._halt(why)
        records = self._records()
        if self._unconfirmed(records):
            return self._halt(
                f"판 {s.condition_version} 의 본 측정 기록에 인계가 있는데 확인이 없다. "
                f"기록을 본 뒤 --confirm-handoff {s.condition_version} 로 다시 띄운다"
            )
        resets = [
            r.end.resets_at
            for r in records
            if r.end.kind == END_NOT_MEASURED
            and r.end.reason == REASON_LIMIT
            and r.end.resets_at is not None
        ]
        if resets:
            self._sleep_until(max(resets))
        for task in tasks:
            records = self._records()
            plan = plan_task(
                task, records, condition=s.condition_version, rerun=task.task_id in s.rerun
            )
            if isinstance(plan, Halt):
                return self._halt(plan.why)
            if not plan.arms:
                continue
            spent = sum(r.spend.claude_code_usd + r.spend.other_usd for r in records)
            estimate = estimate_usd(task, plan.arms)
            if spent + estimate > s.cap_usd:
                return self._halt(
                    f"예산 상한에 닿는다. 쓴 것 ${spent:.2f}, 상한 ${s.cap_usd:.2f}, "
                    f"다음 과제 {task.task_id} 의 어림 ${estimate:.2f}"
                )
            why = self._run_task(task, plan.arms)
            if why is not None:
                return self._halt(why)
        self.world.out("과제 목록을 다 돌았다")
        return EXIT_DONE

    def _halt(self, why: str) -> int:
        self.world.out(f"멈춘다: {why}")
        return EXIT_HALTED

    def _records(self) -> list[Record]:
        try:
            names = sorted(os.listdir(self.settings.records))
        except FileNotFoundError:
            return []
        return [
            read_record(self.settings.records / n)
            for n in names
            if parse_record_file_name(n) is not None
        ]

    def _unconfirmed(self, records: Sequence[Record]) -> bool:
        if not self.main_list or self.settings.confirmed == self.settings.condition_version:
            return False
        return any(
            r.condition_version == self.settings.condition_version
            and not r.pilot
            and r.handoffs > 0
            for r in records
        )

    def _sleep_until(self, until: float) -> None:
        left = until - self.world.now()
        if left > 0:
            self.world.out(
                f"한도가 풀리는 시각(유닉스 초 {until:.0f})까지 새 회차를 열지 않고 잔다"
            )
            self.world.sleep(left)

    def _close_dead_rounds(self, tasks: Sequence[Task]) -> str | None:
        """기록 없는 회차 폴더를 측정 아님(중단)으로 적는다. 멈출 까닭이 있으면 그 글이다."""
        s = self.settings
        dead = unrecorded_round_dirs(s.root, s.records)
        if not dead:
            return None
        names = ", ".join(p.name for p in dead)
        ids = {i for p in dead for i in _session_ids(p)}
        if ids:
            name = Path(s.claude[0]).name
            pids = self.world.processes(name)
            if pids is None:
                return f"{name} 프로세스를 훑지 못해 기록 없는 회차({names})가 도는지 모른다"
            for pid in pids:
                argv = self.world.read_command_line(pid)
                if argv is None:
                    return (
                        f"{name} 프로세스 {pid} 의 명령 줄을 읽지 못해 "
                        f"기록 없는 회차({names})가 도는지 모른다"
                    )
                if ids & set(argv):
                    return f"기록 없는 회차({names})의 세션이 프로세스 {pid} 에서 돈다"
        by_id = {t.task_id: t for t in tasks}
        for place in dead:
            named = parse_round_dir_name(place.name)
            task = by_id.get(named.task_id) if named is not None else None
            if task is None:
                return f"기록 없는 회차 폴더 {place.name} 의 과제가 이 목록에 없다"
            try:
                record = self._interrupted(place, task)
            except PriceError as e:
                return f"기록 없는 회차 {place.name} 의 공식 단가를 셈하지 못했다: {e}"
            write_record(s.records, record)
            self.world.out(f"죽은 러너가 남긴 회차 {place.name} 를 측정 아님(중단)으로 적었다")
        return None

    def _bare(self, place: RoundDir, task: Task, end: End, env: dict[str, str]) -> Record:
        """세션이 없는 회차의 기록."""
        return round_record(
            place,
            task,
            condition_version=self.settings.condition_version,
            claude_version=None,
            account=self.settings.account,
            env=env,
            continued=Continued(runs=(), handoffs=0, interventions=0, asked_at_end=False, end=end),
            config_dir=self.config,
            outcome=Outcome(None, None, None, None, None, None),
            wall_clock_from=0.0,
            now=0.0,
            elsewhere=_elsewhere_zero(),
        )

    def _interrupted(self, place: RoundDir, task: Task) -> Record:
        """죽은 러너가 남긴 회차의 측정 아님(중단) 기록. 비용은 세션마다 원본 줄의 마지막
        `total_cost_usd`이고, 그것이 없는 세션은 공식 단가 셈을 대신 넣는다."""
        end = End(END_NOT_MEASURED, REASON_INTERRUPTED, None)
        record = self._bare(place, task, end, {})
        sessions: list[Session] = []
        costs: list[Cost] = []
        tools: tuple[str, ...] = ()
        for sid in _session_ids(place):
            lines = [
                line
                for p in sorted(place.stream.glob(f"*-{sid}.jsonl"))
                for line in p.read_text(encoding="utf-8", errors="replace").splitlines()
            ]
            summary = summarize_call(lines)
            if summary.init is not None and not tools:
                tools = summary.init.tools
            cost, usage = session_cost(summary.results, sid)
            official = _official(self.config, sid, usage)
            costs.append(official)
            main, side = transcript_counts(self.config, sid)
            sessions.append(
                Session(
                    session_id=sid,
                    calls=(),
                    cost_usd=official.official_usd if cost is None else cost,
                    cost_substituted=cost is None,
                    runner_killed=False,
                    model_usage=usage,
                    main_lines=main,
                    subagent_lines=side,
                )
            )
        other_usd = _other_usd(self.config, [s.session_id for s in sessions])
        spend = _spend(record, sessions, costs, other_usd)
        return replace(record, sessions=tuple(sessions), init_tools=tools, spend=spend)

    def _create(self, task: Task, arm: str) -> RoundDir:
        """회차 번호를 잡고 곧바로 그 폴더를 만든다. 주 스레드에서만 부른다."""
        s = self.settings
        records = os.listdir(s.records) if s.records.exists() else []
        dirs = os.listdir(s.root) if s.root.exists() else []
        number = next_round_no(task.task_id, arm, records, dirs)
        return create_round_dir(s.root, task.task_id, arm, number)

    def _open(self, task: Task, arm: str) -> RoundDir | str:
        """회차를 열기 전의 확인을 지나면 그 회차 폴더, 걸리면 멈출 까닭이다."""
        s = self.settings
        s.root.mkdir(parents=True, exist_ok=True)
        env = session_env(os.environ, config_dir=s.config_dir, round_dir=RoundDir(s.root))
        refusal = before_round(s.claude, env=env, cwd=s.root, account=s.account)
        if refusal is None:
            return self._create(task, arm)
        if refusal.end is None:
            return f"{task.task_id} {arm} 회차를 열기 전의 확인에 걸렸다: {refusal.why}"
        place = self._create(task, arm)
        write_record(s.records, self._bare(place, task, refusal.end, env))
        return f"{place.name} 를 측정 아님({refusal.end.reason})으로 적었다: {refusal.why}"

    def _run_task(self, task: Task, arms: Sequence[str]) -> str | None:
        """과제 하나의 회차를 동시에 둘까지 돈다. 멈출 까닭이 있으면 그 글이다."""
        s = self.settings
        queue = deque(arms)
        running: dict[Future[_Done], str] = {}
        halt: str | None = None
        excluded = False
        limit_until: float | None = None
        with ThreadPoolExecutor(MAX_PARALLEL) as pool:
            while True:
                while (
                    halt is None
                    and not excluded
                    and limit_until is None
                    and queue
                    and len(running) < MAX_PARALLEL
                ):
                    arm = queue.popleft()
                    opened = self._open(task, arm)
                    if isinstance(opened, str):
                        halt = opened
                    else:
                        running[pool.submit(self._round, task, arm, opened)] = arm
                if not running:
                    if halt is None and not excluded and limit_until is not None:
                        self._sleep_until(limit_until)
                        limit_until = None
                        continue
                    return halt
                finished, _ = wait(running, return_when=FIRST_COMPLETED)
                for future in finished:
                    arm = running.pop(future)
                    try:
                        done = future.result()
                    except Exception as e:  # 일꾼의 어느 실패든 기록 없이 멈춘다
                        halt = halt or f"{task.task_id} {arm} 회차가 기록 없이 실패했다: {e!r}"
                        continue
                    record = done.record
                    end = record.end
                    halt = halt or done.halt
                    name = record.round_dir_name
                    if end.kind == END_NOT_MEASURED and end.reason == REASON_LIMIT:
                        queue.appendleft(arm)
                        if end.resets_at is None:
                            halt = halt or (
                                f"{name} 이 풀리는 시각을 모르는 한도에 막혔다. "
                                "한도가 풀린 뒤 같은 명령으로 다시 띄운다"
                            )
                        else:
                            limit_until = max(limit_until or 0.0, float(end.resets_at))
                    elif end.kind == END_NOT_MEASURED and end.reason == REASON_CONTAMINATION:
                        count = _contaminated(task, self._records(), s.condition_version, arm)
                        if count < 2:
                            queue.appendleft(arm)
                        elif not excluded:
                            excluded = True
                            self.world.out(
                                f"{task.task_id} 를 갈래 {arm} 의 오염 두 번으로 모든 갈래에서 뺀다"
                            )
                    elif end.kind == END_NOT_MEASURED:
                        halt = halt or f"{name} 이 측정 아님({end.reason})으로 끝났다"
                    if (
                        self.main_list
                        and record.handoffs > 0
                        and s.confirmed != s.condition_version
                    ):
                        halt = halt or (
                            f"본 측정에서 인계가 난 회차 {name} 가 끝났다. 기록을 본 뒤 "
                            f"--confirm-handoff {s.condition_version} 로 다시 띄운다"
                        )

    # --- 일꾼 스레드 ---

    def _round(self, task: Task, arm_name: str, place: RoundDir) -> _Done:
        """회차 하나를 준비부터 기록 쓰기까지 돈다."""
        s, w = self.settings, self.world
        arm = ARM_BY_NAME[arm_name]
        env = session_env(os.environ, config_dir=s.config_dir, round_dir=place)
        try:
            setup = prepare_round(
                place,
                source=s.source,
                base=task.base,
                merge=task.merge,
                rules=self.rules,
                setup=w.setup,
                env=env,
                timeout=w.limits.setup,
            )
        except CloneError as e:
            return self._setup_failed(place, task, env, f"클론을 짓지 못했다: {e}")
        if setup.failed is not None:
            failed = setup.failed
            command = SETUP_COMMANDS[failed.index]
            why = f"준비 명령 {command} 가 실패했다({failed.end.value}, {failed.exit_code})"
            return self._setup_failed(place, task, env, why)
        screen = screen_for(
            place, arm, config_dir=self.config, main_checkout=s.main_checkout, home=w.home
        )
        version = claude_version(s.claude, env=env, cwd=place.clone)
        title = ticket_title((place.clone / task.ticket).read_text(encoding="utf-8"))
        continued = run_sessions(
            place,
            task,
            claude=s.claude,
            arm=arm,
            env=env,
            directive_text=directive(task, arm, title),
            wall_clock_from=setup.wall_clock_from,
            screen=screen,
            watch=screen.watch,
            read_command_line=w.read_command_line,
        )
        picked = pick_result_commit(local_branches(place.clone, task.base), task.branch)
        outcome = outcome_of(picked)
        note: str | None = None
        if continued.end.kind == END_DONE and picked.commit is not None:
            try:
                if has_gate_file(s.source, task.base, env, timeout=w.limits.git):
                    gates, gate_names = w.gates, GATE_COMMANDS
                else:
                    gates, gate_names = w.old_gates, OLD_GATE_COMMANDS
                checked = check_result(
                    place,
                    source=s.source,
                    commit=picked.commit,
                    task=task,
                    env=env,
                    out=w.out,
                    setup=w.setup,
                    gates=gates,
                    pytest=w.pytest,
                    limits=w.limits,
                )
            except (GateError, OSError) as e:
                end = End(END_NOT_MEASURED, REASON_SETUP, None)
                continued = replace(continued, end=end, asked_at_end=False)
                note = f"{place.name} 의 게이트를 돌지 못했다: {e}"
            else:
                outcome = replace(
                    outcome,
                    setup_failure=self._named_setup(checked.setup_failure),
                    gates=_named_gates(checked.gates, gate_names),
                    hidden=checked.hidden,
                )
        findings = screen.findings()
        record = round_record(
            place,
            task,
            condition_version=s.condition_version,
            claude_version=version,
            account=s.account,
            env=env,
            continued=continued,
            config_dir=self.config,
            outcome=outcome,
            wall_clock_from=setup.wall_clock_from,
            now=time.monotonic(),
            elsewhere=replace(
                _elsewhere_zero(),
                denied_calls=findings.denied_calls,
                utilization_start=findings.utilization_start,
                utilization_end=findings.utilization_end,
                contamination=findings.contamination,
                model_mismatch=findings.model_mismatch,
            ),
        )
        record = _with_costs(record, self.config)
        write_record(s.records, record)
        if any(r.launched.drove.stop in LEFT_RUNNING for r in continued.runs):
            note = note or f"{place.name} 에 끄지 못하고 남긴 호출이 있어 그 프로세스가 돌 수 있다"
        return _Done(record, note)

    def _setup_failed(self, place: RoundDir, task: Task, env: dict[str, str], why: str) -> _Done:
        end = End(END_NOT_MEASURED, REASON_SETUP, None)
        record = self._bare(place, task, end, env)
        write_record(self.settings.records, record)
        return _Done(record, f"{place.name}: {why}")

    def _named_setup(self, failure: SetupFailure | None) -> SetupFailure | None:
        """게이트 작업 트리의 준비 실패를 정해진 준비 명령의 이름으로. 같은 명령이 여럿이면 첫
        자리로 읽는다(정해진 명령은 서로 다르다)."""
        if failure is None:
            return None
        commands = [" ".join(argv) for argv in self.world.setup]
        index = commands.index(failure.command) if failure.command in commands else None
        if index is None:
            return failure
        return replace(failure, command=SETUP_COMMANDS[index])


def _named_gates(gates: tuple[Gate, ...] | None, names: tuple[str, ...]) -> tuple[Gate, ...] | None:
    """돈 게이트를 고른 묶음의 정해진 이름 `names`로. 수가 다르면 `ValueError`다."""
    if gates is None:
        return None
    if len(gates) != len(names):
        raise ValueError(f"돈 게이트 {len(gates)}개가 묶음의 이름 {len(names)}개와 다르다")
    return tuple(replace(g, command=name) for g, name in zip(gates, names, strict=True))


def _session_ids(place: RoundDir) -> list[str]:
    """회차 폴더에 적힌 세션 id. 처음 나온 차례이고 겹친 것은 한 번이다."""
    try:
        text = place.session_ids.read_text(encoding="utf-8")
    except FileNotFoundError:
        return []
    return list(dict.fromkeys(line.strip() for line in text.splitlines() if line.strip()))


def run(settings: Settings, world: World) -> int:
    """러너 본체. 종료 코드는 `EXIT_DONE`이나 `EXIT_HALTED`다."""
    try:
        return _Runner(settings, world).run()
    except (ShapeError, OSError) as e:
        world.out(f"멈춘다: 기록이나 파일을 읽고 쓰지 못했다: {e}")
        return EXIT_HALTED


# --- 명령 줄 ---


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m tools.rerun_runner", description="다시 풀기의 과제 목록을 돈다."
    )
    parser.add_argument("tasks", help="과제 목록 JSON")
    parser.add_argument("--root", required=True, help="회차 폴더의 뿌리(절대 경로)")
    parser.add_argument("--config-dir", required=True, help="전용 설정 폴더(절대 경로)")
    parser.add_argument("--account", required=True, help="로그인한 이메일의 @ 앞")
    parser.add_argument("--claude", required=True, help="띄울 claude 실행 파일")
    parser.add_argument("--cap", required=True, type=float, help="예산 상한(USD)")
    parser.add_argument(
        "--confirm-handoff", type=int, default=None, help="인계를 확인한 조건 판의 수"
    )
    parser.add_argument(
        "--rerun", action="append", default=[], help="지금 판에서 다시 돌 과제 id(여럿)"
    )
    parser.add_argument("--records", default=str(RECORDS), help="회차 기록 폴더")
    parser.add_argument("--readme", default=str(PREREG_README), help="사전 등록 절이 든 README")
    return parser


def main(argv: list[str] | None = None) -> int:
    """종료 코드: 0 다 돌았다, 1 멈춰 사람에게 넘겼다, 2 명령 줄이 잘못돼 아무 회차도 열지
    않았다."""
    args = _parser().parse_args(argv)
    cap: float = args.cap
    if not math.isfinite(cap) or cap <= 0:
        print(f"끝: 예산 상한은 유한한 양수여야 한다: {cap!r}", file=sys.stderr)
        return EXIT_USAGE
    try:
        task_list = read_task_list(Path(str(args.tasks)))
        checkout = main_checkout(ROOT)
        root = checked_root(str(args.root), main_checkout=checkout, home=Path.home())
        config_text = str(args.config_dir)
        checked_place(
            config_text,
            "설정 폴더",
            main_checkout=checkout,
            user_claude=Path.home() / ".claude",
        )
    except (ShapeError, OSError, PlaceError, CloneError) as e:
        print(f"끝: {e}", file=sys.stderr)
        return EXIT_USAGE
    rerun: list[str] = args.rerun
    unknown = sorted(set(rerun) - {t.task_id for t in task_list.tasks})
    if unknown:
        print(f"끝: 목록에 없는 과제 id: {', '.join(unknown)}", file=sys.stderr)
        return EXIT_USAGE
    # 실제 경로로 푼다. 죽은 회차를 훑을 때 그 끝 이름(윈도의 `claude.exe`)과 프로세스 이름을
    # 견주므로, `claude`처럼 확장자 없이 준 이름 그대로면 아무 프로세스와도 맞지 않아 지나간다.
    # 파일 경로로 주면 그 파일이다. 판을 고정한 `versions/<판>` 복사본은 확장자가 없어 윈도의
    # `shutil.which`가 PATHEXT 밖이라고 받지 않는다. 그 끝 이름(`2.1.302`)이 곧 프로세스 이름이다
    given = Path(args.claude)
    claude = str(given.absolute()) if given.is_file() else shutil.which(str(args.claude))
    if claude is None:
        print(f"끝: claude 실행 파일을 찾지 못했다: {args.claude}", file=sys.stderr)
        return EXIT_USAGE
    confirmed: int | None = args.confirm_handoff
    settings = Settings(
        task_list=task_list,
        root=root,
        config_dir=config_text,
        account=str(args.account),
        claude=(claude,),
        cap_usd=cap,
        records=Path(str(args.records)),
        readme=Path(str(args.readme)),
        expected_sha256=PREREG_SHA256,
        source=checkout,
        main_checkout=checkout,
        confirmed=confirmed,
        rerun=frozenset(rerun),
    )
    return run(settings, World())


if __name__ == "__main__":
    # 윈도의 파이프는 로캘의 인코딩이라 한국어 줄을 찍다 깨진다(선례 `tools/rerun_round.py`의 같은
    # 자리)
    for stream in (sys.stdout, sys.stderr):
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(encoding="utf-8")
    sys.exit(main())
