"""tools/rerun_runner.py: 과제 목록을 실행 차례대로 돌며 동시에 둘, 예산 상한, 한도 기다림, 다시
돌기, 멈춤을 지킨다.

회차는 가짜 `claude`(`tests/tools/fake_claude.py`)와 임시 원본 저장소(B와 M)로 끝까지 돈다. 가짜의
각본은 회차 폴더(`<과제 id>-<갈래>-<회차 번호>`)마다 줘서 함께 도는 회차의 차례에 기대지 않는다.
게이트·준비·pytest 자리는 작은 파이썬 명령이고, 시계와 잠은 가짜다. 다시 띄우기의
판정(`plan_task`)과 어림(`estimate_usd`)은 지은 기록으로 본다.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field, replace
from pathlib import Path

import pytest
from tests.tools import fake_claude as fake
from tools.proc_command_line import command_line
from tools.rerun_files import (
    END_CAPPED,
    END_DONE,
    END_NOT_MEASURED,
    GATE_COMMANDS,
    GATE_FILE,
    LIST_MAIN,
    LIST_PILOT,
    OLD_GATE_COMMANDS,
    TIER_PILOT,
    TIER_SMALL,
    End,
    Json,
    Outcome,
    Record,
    Session,
    Spend,
    Task,
    TaskList,
    Tokens,
    judge_view,
    read_record,
    write_record,
    write_task_list,
)
from tools.rerun_gates import GateError, Limits
from tools.rerun_judge import PREREG_END, PREREG_START
from tools.rerun_round import ROOT, create_round_dir, main_checkout, rule_path
from tools.rerun_runner import (
    ARM_RATIOS,
    CONDITION_VERSION,
    EXIT_DONE,
    EXIT_USAGE,
    MAX_PARALLEL,
    Halt,
    Plan,
    Settings,
    World,
    estimate_usd,
    main,
    plan_task,
    run,
)

from tools import rerun_cost, rerun_runner

GIT_TIMEOUT = 60
TICKET = ".scratch/rerun-x/issues/03-thing.md"
OPUS = "claude-opus-5-5"
SONNET = "claude-sonnet-5-5"
NOW = 1_000_000.0  # 가짜 시계의 처음(유닉스 초)


def _git(cwd: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@invalid", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=GIT_TIMEOUT,
    )
    assert done.returncode == 0, f"git {args}: {done.stderr}"
    return done.stdout.strip()


def _커밋(repo: Path, files: dict[str, str], message: str) -> str:
    for rel, text in files.items():
        path = repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", message)
    return _git(repo, "rev-parse", "HEAD")


def _원본_짓기(repo: Path, *, gate_file: bool) -> tuple[Path, str, str]:
    """B 와 M 의 원본. `gate_file`이면 B 에 게이트 러너(`GATE_FILE`)를 둔다."""
    _git(repo, "init", "-q", "-b", "main")
    files = {
        TICKET: "# 03: 그것을 짓는다\n\n**Status:** ready-for-agent\n",
        "pytest.ini": "[pytest]\n",
        "tests/test_old.py": "def test_old():\n    assert True\n",
    }
    if gate_file:
        files[GATE_FILE] = ""
    base = _커밋(repo, files, "B")
    merge = _커밋(repo, {"tests/test_new.py": "def test_new():\n    assert True\n"}, "M")
    return repo, base, merge


@pytest.fixture(scope="module")
def 원본(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, str, str]:
    return _원본_짓기(tmp_path_factory.mktemp("원본"), gate_file=True)


@pytest.fixture(scope="module")
def 옛_원본(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, str, str]:
    """B 에 게이트 러너가 없던 때(2026-10-07 #160 앞)의 과제."""
    return _원본_짓기(tmp_path_factory.mktemp("옛_원본"), gate_file=False)


def _과제(
    n: int,
    src: tuple[Path, str, str],
    *,
    arms: Sequence[str] = ("A",),
    pilot: bool = False,
    order: int | None = None,
    pr_cost: float = 10.0,
) -> Task:
    _, base, merge = src
    return Task(
        task_id=f"rerun-x-{n:02d}",
        ticket=TICKET,
        base=base,
        merge=merge,
        branch=f"feature/{n:02d}-thing",
        tier=TIER_PILOT if pilot else TIER_SMALL,
        size=4,
        order=n if order is None else order,
        pilot=pilot,
        pr_cost_usd=pr_cost,
        round_cap_usd=40.0,
        hidden_tests=("tests/test_new.py::test_new",),
        support_files=(),
        original_model_effort=None,
        arm_plan=tuple(arms),
    )


def _key(task: Task, arm: str, round_no: int) -> str:
    return f"{task.task_id}-{arm}-{round_no}"


# --- 각본 ---


def _응답줄(model: str = OPUS, effort: str | None = "xhigh") -> dict[str, Json]:
    """공식 단가로 셈할 수 있는 세션 기록 파일의 assistant 줄."""
    line = fake.transcript_line(model, effort, "msg_usage")
    line["message"] = {
        "model": model,
        "id": "msg_usage",
        "role": "assistant",
        "content": [],
        "usage": {"input_tokens": 1000, "output_tokens": 2000},
    }
    return line


def _끝남(task: Task, cost: float = 1.0, *, hang: float = 0.0, text: str = "다 했다") -> Json:
    """결과 커밋을 남기고 끝나는 호출."""
    return fake.call(
        [fake.init_event(), fake.result_event(cost, text)],
        git=[["switch", "-c", task.branch], ["commit", "--allow-empty", "-m", "풀었다"]],
        hang=hang,
    )


def _인계_글(task: Task) -> str:
    return "\n".join(
        (
            "셀프 리뷰 앞에서 끊는다.",
            f"다음 작업: {task.ticket}. 나머지를 짓는다",
            "다음 단계: 구현",
            "어디서: 새 세션",
            f"시작 프롬프트: /implement {task.ticket}",
            f"브랜치: {task.branch}",
            "모델: Opus 5.5 / xhigh",
            "읽을 것: 없음",
            "이어받을 상태: 인계: 셀프 리뷰 앞",
            "확인할 선행 조건: 없음",
            "이번 요청 범위: 구현·리뷰·커밋까지",
        )
    )


def _인계(task: Task) -> Json:
    return fake.call([fake.init_event(), fake.result_event(1.0, _인계_글(task))])


def _오염() -> Json:
    return fake.call(
        [
            fake.init_event(),
            fake.tool_use_event("Bash", {"command": "gh pr list"}),
            fake.result_event(0.5, "멈췄다"),
        ]
    )


def _한도(resets_at: int | None) -> Json:
    if resets_at is None:
        return fake.call([fake.init_event(), fake.limit_result()])
    return fake.call(
        [
            fake.init_event(),
            fake.rate_limit_event("rejected", resets_at=resets_at),
            fake.result_event(0.25, "한도"),
        ]
    )


# --- 러너 ---


@dataclass
class 시계:
    t: float = NOW
    잠: list[float] = field(default_factory=list[float])  # 잠에서 깬 때
    잠든_때_부름: list[int] = field(default_factory=list[int])  # 잠들 때까지의 세션 부름 수
    config: Path | None = None

    def now(self) -> float:
        return self.t

    def sleep(self, seconds: float) -> None:
        if self.config is not None:
            self.잠든_때_부름.append(len(fake.read_calls(self.config)))
        self.t += max(seconds, 0.0)
        self.잠.append(self.t)


def _명령(code: str) -> tuple[str, ...]:
    return (sys.executable, "-c", code)


PASS = _명령("pass")
FAIL = _명령("raise SystemExit(1)")


@dataclass
class 판:
    tmp: Path
    source: Path
    tasks: list[Task]
    kind: str = LIST_PILOT
    cap: float = 1000.0
    confirmed: int | None = None
    rerun: frozenset[str] = frozenset()
    condition: int = CONDITION_VERSION
    readme_text: str = f"머리\n{PREREG_START}\n정의\n{PREREG_END}\n"
    expected: str | None = None  # 빈 값이면 README 절의 해시
    gates: Sequence[Sequence[str]] = (FAIL, PASS, PASS)  # 숨은 시험을 건너뛰어 빠르다
    old_gates: Sequence[Sequence[str]] = (FAIL, PASS, PASS, PASS, PASS, PASS)
    setup: Sequence[Sequence[str]] = (PASS, PASS, PASS)
    clock: 시계 = field(default_factory=시계)
    lines: list[str] = field(default_factory=list[str])
    processes: Callable[[str], list[int] | None] = lambda _name: []
    read_command_line: Callable[[int], tuple[str, ...] | None] = command_line

    @property
    def root(self) -> Path:
        return self.tmp / "뿌리"

    @property
    def config(self) -> Path:
        return self.tmp / "설정"

    @property
    def records(self) -> Path:
        return self.tmp / "records"

    def script(self, rounds: dict[str, Sequence[Json]], *, email: str = fake.EMAIL) -> None:
        fake.write_script(self.config, rounds=rounds, email=email)

    def run(self) -> int:
        readme = self.tmp / "README.md"
        readme.write_text(self.readme_text, encoding="utf-8", newline="\n")
        section = self.readme_text.split(PREREG_START, 1)[1].split(PREREG_END, 1)[0]
        expected = self.expected or hashlib.sha256(section.encode("utf-8")).hexdigest()
        self.clock.config = self.config
        settings = Settings(
            task_list=TaskList(kind=self.kind, tasks=tuple(self.tasks)),
            root=self.root,
            config_dir=str(self.config),
            account="njh6803",
            claude=tuple(fake.claude()),
            cap_usd=self.cap,
            records=self.records,
            readme=readme,
            expected_sha256=expected,
            source=self.source,
            main_checkout=self.tmp / "주",
            confirmed=self.confirmed,
            rerun=self.rerun,
            condition_version=self.condition,
        )
        world = World(
            out=self.lines.append,
            now=self.clock.now,
            sleep=self.clock.sleep,
            processes=self.processes,
            read_command_line=self.read_command_line,
            setup=tuple(tuple(c) for c in self.setup),
            gates=tuple(tuple(c) for c in self.gates),
            old_gates=tuple(tuple(c) for c in self.old_gates),
            pytest=(sys.executable, "-m", "pytest"),
            limits=Limits(setup=120, gates=120, hidden=120, git=120),
            home=self.tmp / "집",
        )
        return run(settings, world)

    def saved(self) -> list[Record]:
        if not self.records.exists():
            return []
        return sorted(
            (read_record(p) for p in self.records.glob("*.json")),
            key=lambda r: (r.task_id, r.arm, r.round_no),
        )

    def calls(self) -> list[dict[str, Json]]:
        return fake.read_calls(self.config)


@pytest.fixture
def 판짜기(tmp_path: Path, 원본: tuple[Path, str, str]) -> Callable[..., 판]:
    def make(tasks: list[Task], **kw: object) -> 판:
        board = 판(tmp_path, 원본[0], tasks)
        for k, v in kw.items():
            setattr(board, k, v)
        return board

    return make


def _ends(records: Sequence[Record]) -> list[tuple[str, int, str, str | None]]:
    return [(r.arm, r.round_no, r.end.kind, r.end.reason) for r in records]


# --- 지은 기록(다시 띄우기의 판정과 예산) ---


ZERO = Tokens(input=None, output=None, cache_read=None, cache_write=None, thinking=None)


def _기록(
    task: Task,
    arm: str,
    round_no: int,
    *,
    end: End = End(END_DONE, None, None),  # noqa: B008  # 얼린 데이터클래스다
    version: int = CONDITION_VERSION,
    cost: float = 1.0,
    handoffs: int = 0,
) -> Record:
    done = end.kind == END_DONE
    return Record(
        task_id=task.task_id,
        arm=arm,
        round_no=round_no,
        condition_version=version,
        pilot=task.pilot,
        round_dir_name=f"{task.task_id}-{arm}-{round_no}-zz{round_no}",
        claude_version=None,
        account="njh6803",
        env_names=(),
        init_tools=(),
        sessions=(),
        handoffs=handoffs,
        interventions=0,
        asked_at_end=False,
        end=end,
        outcome=Outcome(
            commit="c" * 40 if done else None,
            rule="지시문 브랜치" if done else None,
            commits_after_base=1 if done else None,
            setup_failure=None,
            gates=None,
            hidden=None,
        ),
        spend=Spend(
            claude_code_usd=cost,
            official_usd=cost,
            other_usd=0.0,
            tokens=ZERO,
            substitutes=(),
            wall_seconds=1.0,
            denied_calls=0,
            utilization_start=(),
            utilization_end=(),
            contamination=(),
            model_mismatch=(),
        ),
    )


def _측정_아님(reason: str, resets_at: int | None = None) -> End:
    return End(END_NOT_MEASURED, reason, resets_at)


# --- 상수와 어림 ---


def test_비율_표는_설계의_위_끝이고_동시에_둘이다() -> None:
    assert ARM_RATIOS == {"A": 1.0, "B": 0.8, "C": 0.7, "D": 0.9, "E": 0.7}
    assert MAX_PARALLEL == 2
    assert CONDITION_VERSION >= 1


def test_어림은_PR_앞_비용에_갈래_계획의_비율_합을_곱한다(원본: tuple[Path, str, str]) -> None:
    five = _과제(1, 원본, arms=("A", "B", "C", "D", "E"), pr_cost=10.0)
    assert estimate_usd(five, five.arm_plan) == pytest.approx(41.0)
    pilot = _과제(2, 원본, arms=("A", "A"), pilot=True, pr_cost=10.0)
    assert estimate_usd(pilot, pilot.arm_plan) == pytest.approx(20.0)
    assert estimate_usd(pilot, ("E",)) == pytest.approx(7.0)


# --- 다시 띄우기의 판정 ---


def test_기록이_없는_과제는_갈래_계획을_다_돈다(원본: tuple[Path, str, str]) -> None:
    task = _과제(1, 원본, arms=("A", "B"))
    assert plan_task(task, [], condition=1, rerun=False) == Plan(("A", "B"))


def test_같은_판에서_끝난_회차는_건너뛰고_측정_아님은_다시_돈다(
    원본: tuple[Path, str, str],
) -> None:
    task = _과제(1, 원본, arms=("A", "B", "C"))
    records = [
        _기록(task, "A", 1, version=1),
        _기록(task, "B", 1, end=_측정_아님("설정"), version=1),
        _기록(task, "C", 1, end=End(END_CAPPED, "시간", None), version=1),  # 상한도 끝난 회차다
    ]
    assert plan_task(task, records, condition=1, rerun=False) == Plan(("B",))


def test_같은_갈래가_두_번_든_파일럿은_기록_수로_남은_회차를_센다(
    원본: tuple[Path, str, str],
) -> None:
    task = _과제(1, 원본, arms=("A", "A"), pilot=True)
    assert plan_task(task, [_기록(task, "A", 1, version=1)], condition=1, rerun=False) == Plan(
        ("A",)
    )
    both = [_기록(task, "A", 1, version=1), _기록(task, "A", 2, version=1)]
    assert plan_task(task, both, condition=1, rerun=False) == Plan(())


def test_러너의_판보다_큰_판의_기록이_있으면_id_를_줬어도_멈춘다(
    원본: tuple[Path, str, str],
) -> None:
    task = _과제(1, 원본, arms=("A", "B"))
    records = [_기록(task, "A", 1, version=3)]
    for rerun in (False, True):
        got = plan_task(task, records, condition=2, rerun=rerun)
        assert isinstance(got, Halt) and "큰 판 3" in got.why, rerun


def test_낮은_판에서_다_마친_과제는_id_가_없으면_다시_돌지_않는다(
    원본: tuple[Path, str, str],
) -> None:
    task = _과제(1, 원본, arms=("A",))
    assert plan_task(task, [_기록(task, "A", 1, version=1)], condition=2, rerun=False) == Plan(())


def test_id_를_준_과제는_낮은_판에서_다_마쳤어도_올린_판에서_돈다(
    원본: tuple[Path, str, str],
) -> None:
    task = _과제(1, 원본, arms=("A", "B"))
    old = [_기록(task, "A", 1, version=1), _기록(task, "B", 1, version=1)]
    assert plan_task(task, old, condition=2, rerun=True) == Plan(("A", "B"))
    # 같은 명령을 다시 치면 올린 판에서 끝난 회차는 건너뛴다
    again = [*old, _기록(task, "A", 2, version=2)]
    assert plan_task(task, again, condition=2, rerun=True) == Plan(("B",))


def test_판을_올리지_않고_준_id_는_회차를_늘리지_않는다(원본: tuple[Path, str, str]) -> None:
    task = _과제(1, 원본, arms=("A",))
    assert plan_task(task, [_기록(task, "A", 1, version=1)], condition=1, rerun=True) == Plan(())


def test_낮은_판에서_다_마치지_못한_과제를_id_없이_판을_올리면_멈추고_id_를_낸다(
    원본: tuple[Path, str, str],
) -> None:
    task = _과제(1, 원본, arms=("A", "B"))
    got = plan_task(task, [_기록(task, "A", 1, version=1)], condition=2, rerun=False)
    assert isinstance(got, Halt)
    assert task.task_id in got.why


def test_오염의_둘째는_같은_조건_판의_기록에서만_센다(원본: tuple[Path, str, str]) -> None:
    task = _과제(1, 원본, arms=("A", "B"))
    dirty = _측정_아님("오염")
    twice = [_기록(task, "A", 1, end=dirty, version=1), _기록(task, "A", 2, end=dirty, version=1)]
    assert plan_task(task, twice, condition=1, rerun=False) == Plan(())  # 그 판에서 뺐다
    mixed = [_기록(task, "A", 1, end=dirty, version=1), _기록(task, "A", 2, end=dirty, version=2)]
    assert plan_task(task, mixed, condition=2, rerun=True) == Plan(("A", "B"))
    # 뺀 과제도 id 를 주면 그 판에서 돈다(id 가 앞선다)
    assert plan_task(task, twice, condition=1, rerun=True) == Plan(("A", "B"))


# --- 회차를 끝까지 ---


def test_끝남인_회차는_게이트와_숨은_시험을_돌고_기록에_정해진_이름으로_적는다(
    판짜기: Callable[..., 판], 원본: tuple[Path, str, str]
) -> None:
    task = _과제(1, 원본, arms=("A",))
    board = 판짜기([task], gates=(PASS, PASS, PASS))
    board.script({_key(task, "A", 1): [_끝남(task, 2.5)]})
    assert board.run() == 0
    (rec,) = board.saved()
    assert (rec.end.kind, rec.round_no, rec.condition_version) == (END_DONE, 1, CONDITION_VERSION)
    assert rec.outcome.gates is not None
    assert [g.command for g in rec.outcome.gates] == list(GATE_COMMANDS)
    assert [g.exit_code for g in rec.outcome.gates] == [0, 0, 0]
    assert rec.outcome.hidden is not None and rec.outcome.hidden.passed == 1
    assert rec.spend.claude_code_usd == pytest.approx(2.5)
    assert rec.account == "njh6803" and rec.claude_version == "2.1.302 (Claude Code)"


def test_회차의_막는_규칙은_뿌리_바로_아래의_편집과_쓰기를_막는다(
    판짜기: Callable[..., 판], 원본: tuple[Path, str, str]
) -> None:
    """파일럿 판 2의 한 회차가 뿌리에 임시 파일을 써 오염으로 버려졌다(일지 2026-10-28-10)."""
    task = _과제(1, 원본, arms=("A",))
    board = 판짜기([task], gates=(PASS, PASS, PASS))
    board.script({_key(task, "A", 1): [_끝남(task, 2.5)]})
    assert board.run() == 0
    (rec,) = board.saved()
    settings = board.root / rec.round_dir_name / "deny-settings.json"
    deny = json.loads(settings.read_text("utf-8"))["permissions"]["deny"]
    where = rule_path(Path(os.path.abspath(board.root)))
    assert f"Write({where}/*.*)" in deny and f"Edit({where}/*.*)" in deny


def test_B에_게이트_러너가_없는_과제는_옛_게이트_묶음을_돌고_그_이름으로_적는다(
    tmp_path: Path, 옛_원본: tuple[Path, str, str]
) -> None:
    task = _과제(1, 옛_원본, arms=("A",))
    board = 판(tmp_path, 옛_원본[0], [task], old_gates=(PASS,) * 6)
    board.script({_key(task, "A", 1): [_끝남(task, 2.5)]})
    assert board.run() == 0, board.lines
    (rec,) = board.saved()
    assert rec.end.kind == END_DONE
    assert rec.outcome.gates is not None
    assert [g.command for g in rec.outcome.gates] == list(OLD_GATE_COMMANDS)
    assert [g.exit_code for g in rec.outcome.gates] == [0] * 6
    assert rec.outcome.hidden is not None and rec.outcome.hidden.passed == 1


def test_옛_게이트_묶음이_실패하면_숨은_시험을_돌지_않는다(
    tmp_path: Path, 옛_원본: tuple[Path, str, str]
) -> None:
    task = _과제(1, 옛_원본, arms=("A",))
    # 새 묶음은 모두 통과라, 새 묶음을 돌면 숨은 시험이 돈다
    board = 판(tmp_path, 옛_원본[0], [task], gates=(PASS, PASS, PASS))
    board.script({_key(task, "A", 1): [_끝남(task, 2.5)]})
    assert board.run() == 0
    (rec,) = board.saved()
    assert rec.outcome.gates is not None
    assert [g.exit_code for g in rec.outcome.gates] == [1, 0, 0, 0, 0, 0]
    assert rec.outcome.hidden is None


def test_옛_게이트_명령의_수가_정해진_수와_다르면_거부한다() -> None:
    with pytest.raises(ValueError, match="게이트"):
        World(old_gates=(PASS, PASS, PASS))
    assert len(World().old_gates) == len(OLD_GATE_COMMANDS)


def test_끝남이_아닌_회차는_게이트를_돌지_않고_공식_단가는_모든_회차에서_셈한다(
    판짜기: Callable[..., 판], 원본: tuple[Path, str, str]
) -> None:
    task = _과제(1, 원본, arms=("A",))
    board = 판짜기([task])
    capped = fake.call([fake.init_event(), fake.budget_result(39.5)], main=[_응답줄()])
    board.script({_key(task, "A", 1): [capped]})
    assert board.run() == 0
    (rec,) = board.saved()
    assert (rec.end.kind, rec.end.reason) == (END_CAPPED, "예산")
    assert rec.outcome.gates is None and rec.outcome.hidden is None
    assert rec.spend.official_usd > 0


def test_같은_프로젝트_폴더에_남은_다른_세션의_공식_단가를_회차_비용에_더한다(
    판짜기: Callable[..., 판], 원본: tuple[Path, str, str]
) -> None:
    """과제의 시험이 띄운 하위 `claude -p` 세션(파일럿 end-user-continuation-02)의 몫이다. 사람이
    회차 비용에 더하기로 했다(일지 2026-10-28-10 "설계 8절 확인과 사람 결정")."""
    task = _과제(1, 원본, arms=("A",))
    board = 판짜기([task])
    done = fake.call(
        [fake.init_event(), fake.result_event(1.0, "다 했다")],
        main=[_응답줄()],
        others={"child-1": [_응답줄(SONNET, None)], "child-2": [_응답줄(SONNET, None)]},
        git=[["switch", "-c", task.branch], ["commit", "--allow-empty", "-m", "풀었다"]],
    )
    board.script({_key(task, "A", 1): [done]})
    assert board.run() == 0
    (rec,) = board.saved()
    child = (1000 * 2.0 + 2000 * 10.0) / 1e6  # Sonnet 5.5 입력 1000, 출력 2000
    assert math.isclose(rec.spend.other_usd, 2 * child, rel_tol=1e-12)
    # 회차의 세션 비용 칸과 공식 단가 셈에는 들지 않고, 판정이 읽는 두 비용에 더해진다
    assert rec.spend.claude_code_usd == 1.0
    view = judge_view(rec)
    assert math.isclose(view.cost_claude_code_usd, 1.0 + 2 * child, rel_tol=1e-12)
    assert math.isclose(view.cost_official_usd, rec.spend.official_usd + 2 * child, rel_tol=1e-12)


def test_동시에_둘까지_돌고_셋째는_자리가_빌_때_연다(
    판짜기: Callable[..., 판], 원본: tuple[Path, str, str]
) -> None:
    task = _과제(1, 원본, arms=("A", "B", "C", "D"))
    board = 판짜기([task])
    board.script({_key(task, a, 1): [_끝남(task, hang=1.5)] for a in "ABCD"})
    assert board.run() == 0
    running = [c["running"] for c in board.calls()]
    assert max(int(str(n)) for n in running) == 2
    assert _ends(board.saved()) == [(a, 1, END_DONE, None) for a in "ABCD"]


def test_같은_갈래가_두_번_든_파일럿의_두_회차가_함께_돌아도_번호가_다르다(
    판짜기: Callable[..., 판], 원본: tuple[Path, str, str]
) -> None:
    task = _과제(1, 원본, arms=("A", "A"), pilot=True)
    board = 판짜기([task])
    board.script({_key(task, "A", n): [_끝남(task, hang=1.0)] for n in (1, 2)})
    assert board.run() == 0
    assert _ends(board.saved()) == [("A", 1, END_DONE, None), ("A", 2, END_DONE, None)]
    assert max(int(str(c["running"])) for c in board.calls()) == 2


def test_과제는_실행_차례대로_돌고_한_과제를_마친_뒤_다음_과제로_간다(
    판짜기: Callable[..., 판], 원본: tuple[Path, str, str]
) -> None:
    late = _과제(1, 원본, arms=("A", "B"), order=1)
    early = _과제(2, 원본, arms=("A", "B"), order=0)
    board = 판짜기([late, early])
    board.script(
        {
            **{_key(early, a, 1): [_끝남(early, hang=0.5)] for a in "AB"},
            **{_key(late, a, 1): [_끝남(late)] for a in "AB"},
        }
    )
    assert board.run() == 0
    order = [str(c["round"]).rsplit("-", 2)[0] for c in board.calls()]
    assert order == [early.task_id] * 2 + [late.task_id] * 2


# --- 한도 ---


def test_한도에_막힌_회차는_풀리는_시각까지_기다린_뒤_새_클론과_새_번호로_다시_돈다(
    판짜기: Callable[..., 판], 원본: tuple[Path, str, str]
) -> None:
    task = _과제(1, 원본, arms=("A",))
    board = 판짜기([task])
    resets = int(NOW) + 3600
    board.script({_key(task, "A", 1): [_한도(resets)], _key(task, "A", 2): [_끝남(task)]})
    assert board.run() == 0
    assert _ends(board.saved()) == [
        ("A", 1, END_NOT_MEASURED, "한도"),
        ("A", 2, END_DONE, None),
    ]
    assert board.saved()[0].end.resets_at == resets
    assert board.clock.잠 and board.clock.잠[-1] >= resets  # 넘긴 잠의 목표가 풀리는 시각 이상
    assert board.clock.잠든_때_부름 == [1]  # 잠들 때까지 다시 돈 회차를 열지 않았다
    clones = {str(c["cwd"]) for c in board.calls()}
    assert len(clones) == 2


def test_풀리는_시각을_모르는_한도면_멈추고_다시_띄우면_그_회차를_다시_돈다(
    판짜기: Callable[..., 판], 원본: tuple[Path, str, str]
) -> None:
    task = _과제(1, 원본, arms=("A", "B"))
    board = 판짜기([task])
    board.script(
        {
            _key(task, "A", 1): [_한도(None)],
            _key(task, "B", 1): [_끝남(task, hang=1.0)],  # 함께 돌던 회차는 끝까지 둔다
            _key(task, "A", 2): [_끝남(task)],
        }
    )
    assert board.run() == 1
    assert _ends(board.saved()) == [
        ("A", 1, END_NOT_MEASURED, "한도"),
        ("B", 1, END_DONE, None),
    ]
    assert board.saved()[0].end.resets_at is None
    assert any("풀리는 시각" in line for line in board.lines)
    assert board.run() == 0
    assert _ends(board.saved())[-1] == ("B", 1, END_DONE, None)
    assert ("A", 2, END_DONE, None) in _ends(board.saved())
    assert board.clock.잠 == []


def test_다시_뜬_때_풀리는_시각이_오지_않은_한도_기록이_있으면_기다린다(
    판짜기: Callable[..., 판], 원본: tuple[Path, str, str]
) -> None:
    task = _과제(1, 원본, arms=("A",))
    board = 판짜기([task])
    resets = int(NOW) + 600
    board.records.mkdir()
    write_record(board.records, _기록(task, "A", 1, end=_측정_아님("한도", resets), cost=0.5))
    board.script({_key(task, "A", 2): [_끝남(task)]})
    assert board.run() == 0
    assert board.clock.잠 and board.clock.잠[-1] >= resets
    assert board.clock.잠든_때_부름 == [0]
    assert _ends(board.saved())[-1] == ("A", 2, END_DONE, None)


# --- 오염 ---


def test_오염이_한_번이면_다시_돌고_두_번이면_그_과제를_모든_갈래에서_뺀다(
    판짜기: Callable[..., 판], 원본: tuple[Path, str, str]
) -> None:
    task = _과제(1, 원본, arms=("A", "B", "C"))
    after = _과제(2, 원본, arms=("A",))
    board = 판짜기([task, after])
    board.script(
        {
            _key(task, "A", 1): [_오염()],
            _key(task, "B", 1): [_끝남(task, hang=3.0)],
            _key(task, "A", 2): [_오염()],
            _key(after, "A", 1): [_끝남(after)],
        }
    )
    assert board.run() == 0
    assert _ends([r for r in board.saved() if r.task_id == task.task_id]) == [
        ("A", 1, END_NOT_MEASURED, "오염"),
        ("A", 2, END_NOT_MEASURED, "오염"),
        ("B", 1, END_DONE, None),
    ]
    assert any(task.task_id in line and "뺀다" in line for line in board.lines)
    assert [r.task_id for r in board.saved()].count(after.task_id) == 1  # 다음 과제로 갔다


# --- 멈춤 ---


def test_설정_멈춤에서_함께_돌던_회차는_끝까지_돌고_새_회차는_열지_않는다(
    판짜기: Callable[..., 판], 원본: tuple[Path, str, str]
) -> None:
    task = _과제(1, 원본, arms=("A", "B", "C"))
    board = 판짜기([task])
    outside: Json = {"name": "바깥", "path": "/x", "source": "바깥@market"}
    # init 을 낸 뒤 매달려, 러너가 그 줄에서 끌 때 결과 이벤트가 아직 없다
    settings = fake.call([fake.init_event(extra_plugins=[outside])], main=[_응답줄()], hang=30.0)
    board.script({_key(task, "A", 1): [settings], _key(task, "B", 1): [_끝남(task, hang=3.0)]})
    assert board.run() == 1
    assert _ends(board.saved()) == [
        ("A", 1, END_NOT_MEASURED, "설정"),
        ("B", 1, END_DONE, None),
    ]
    assert {str(c["round"]) for c in board.calls()} == {_key(task, a, 1) for a in "AB"}
    # init 에서 끈 호출은 결과 이벤트가 없어 그 세션의 비용을 공식 단가 셈으로 대신 넣는다
    a1 = board.saved()[0]
    (session,) = a1.sessions
    assert session.runner_killed and session.cost_substituted
    assert session.cost_usd == pytest.approx(a1.spend.official_usd)
    assert (
        a1.spend.claude_code_usd == pytest.approx(a1.spend.official_usd)
        and a1.spend.official_usd > 0
    )


def test_계정이_맞지_않으면_회차를_열지_않고_멈춘다(
    판짜기: Callable[..., 판], 원본: tuple[Path, str, str]
) -> None:
    task = _과제(1, 원본, arms=("A",))
    board = 판짜기([task])
    board.script({_key(task, "A", 1): [_끝남(task)]}, email="other@example.com")
    assert board.run() == 1
    assert board.saved() == [] and board.calls() == []
    assert not board.root.exists() or list(board.root.iterdir()) == []
    assert "@" not in "\n".join(board.lines)


def test_준비가_실패하면_측정_아님_준비로_적고_멈춘다(
    판짜기: Callable[..., 판], 원본: tuple[Path, str, str]
) -> None:
    task = _과제(1, 원본, arms=("A", "B"))
    board = 판짜기([task], setup=(FAIL, PASS, PASS))
    board.script({})
    assert board.run() == 1
    assert _ends(board.saved()) in (
        [("A", 1, END_NOT_MEASURED, "준비")],
        [("A", 1, END_NOT_MEASURED, "준비"), ("B", 1, END_NOT_MEASURED, "준비")],
    )
    assert board.calls() == []


@pytest.mark.parametrize(
    ("call", "reason"),
    [
        (fake.call([fake.init_event()]), "호출"),  # 결과 이벤트 없이 끝났다
        (
            fake.call(
                [fake.init_event(), fake.result_event(1.0, "끝")],
                main=[fake.transcript_line("claude-sonnet-5-5", "xhigh")],
            ),
            "모델",
        ),
    ],
)
def test_측정_아님_호출과_모델_뒤에_멈춘다(
    판짜기: Callable[..., 판], 원본: tuple[Path, str, str], call: Json, reason: str
) -> None:
    task = _과제(1, 원본, arms=("A",))
    after = _과제(2, 원본, arms=("A",))
    board = 판짜기([task, after])
    board.script({_key(task, "A", 1): [call], _key(after, "A", 1): [_끝남(after)]})
    assert board.run() == 1
    assert _ends(board.saved()) == [("A", 1, END_NOT_MEASURED, reason)]
    assert any(reason in line for line in board.lines)


# --- 인계 ---


def test_본_측정에서_첫_인계_뒤_멈추고_확인_인자를_주면_잇는다(
    판짜기: Callable[..., 판], 원본: tuple[Path, str, str]
) -> None:
    task = _과제(1, 원본, arms=("A", "B"))
    board = 판짜기([task], kind=LIST_MAIN)
    board.script(
        {
            _key(task, "A", 1): [_인계(task), _끝남(task)],
            _key(task, "B", 1): [_끝남(task)],
        }
    )
    assert board.run() == 1
    first = board.saved()
    assert ("A", 1, END_DONE, None) in _ends(first)
    assert any(r.handoffs == 1 for r in first)
    assert any("인계" in line for line in board.lines)
    calls = len(board.calls())
    # 확인 없이 다시 띄우면 회차를 열기 전에 멈춘다
    assert board.run() == 1
    assert len(board.calls()) == calls
    # 다른 판의 확인은 확인이 아니다
    board.confirmed = CONDITION_VERSION + 1
    assert board.run() == 1
    assert len(board.calls()) == calls
    board.confirmed = CONDITION_VERSION
    assert board.run() == 0
    assert {(r.arm, r.end.kind) for r in board.saved()} == {("A", END_DONE), ("B", END_DONE)}


def test_첫_인계가_나면_새_회차를_열지_않는다(
    판짜기: Callable[..., 판], 원본: tuple[Path, str, str]
) -> None:
    task = _과제(1, 원본, arms=("A", "B", "C"))
    board = 판짜기([task], kind=LIST_MAIN)
    board.script(
        {
            _key(task, "A", 1): [_인계(task), _끝남(task)],
            _key(task, "B", 1): [_끝남(task, hang=5.0)],  # A 가 먼저 끝난다
        }
    )
    assert board.run() == 1
    assert {str(c["round"]) for c in board.calls()} == {_key(task, a, 1) for a in "AB"}


def test_다른_판의_확인을_쥐고_돌던_동안에도_첫_인계에서_멈춘다(
    판짜기: Callable[..., 판], 원본: tuple[Path, str, str]
) -> None:
    task = _과제(1, 원본, arms=("A", "B", "C"))
    board = 판짜기(
        [task], kind=LIST_MAIN, condition=CONDITION_VERSION + 1, confirmed=CONDITION_VERSION
    )
    board.script(
        {
            _key(task, "A", 1): [_인계(task), _끝남(task)],
            _key(task, "B", 1): [_끝남(task, hang=5.0)],  # A 가 먼저 끝난다
        }
    )
    assert board.run() == 1
    assert any(f"--confirm-handoff {CONDITION_VERSION + 1}" in line for line in board.lines)
    assert {str(c["round"]) for c in board.calls()} == {_key(task, a, 1) for a in "AB"}


def test_파일럿에서는_인계로_멈추지_않는다(
    판짜기: Callable[..., 판], 원본: tuple[Path, str, str]
) -> None:
    task = _과제(1, 원본, arms=("A", "B"), pilot=True)
    board = 판짜기([task])
    board.script(
        {_key(task, "A", 1): [_인계(task), _끝남(task)], _key(task, "B", 1): [_끝남(task)]}
    )
    assert board.run() == 0
    assert len(board.saved()) == 2


def test_해시가_맞지_않는_본_측정_목록은_회차를_열지_않는다(
    판짜기: Callable[..., 판], 원본: tuple[Path, str, str]
) -> None:
    task = _과제(1, 원본, arms=("A",))
    board = 판짜기([task], kind=LIST_MAIN, expected="0" * 64)
    board.script({_key(task, "A", 1): [_끝남(task)]})
    assert board.run() == 1
    assert board.calls() == [] and board.saved() == []
    assert any("사전 등록" in line for line in board.lines)


def test_파일럿_목록은_해시를_대_보지_않는다(
    판짜기: Callable[..., 판], 원본: tuple[Path, str, str]
) -> None:
    task = _과제(1, 원본, arms=("A",), pilot=True)
    board = 판짜기([task], expected="0" * 64)
    board.script({_key(task, "A", 1): [_끝남(task)]})
    assert board.run() == 0


# --- 예산 ---


def test_쓴_것과_다음_과제의_어림이_상한을_넘으면_멈추고_한_줄로_낸다(
    판짜기: Callable[..., 판], 원본: tuple[Path, str, str]
) -> None:
    done = _과제(1, 원본, arms=("A", "A"), pilot=True)
    task = _과제(2, 원본, arms=("A", "A"), pilot=True, pr_cost=10.0)
    board = 판짜기([done, task], cap=25.0)
    board.records.mkdir()
    write_record(board.records, _기록(done, "A", 1, cost=3.0))
    # 측정 아님의 비용도 쓴 것에 든다
    write_record(board.records, _기록(done, "A", 2, cost=2.5, end=_측정_아님("설정")))
    board.script({_key(done, "A", 3): [_끝남(done)]})
    # done 의 남은 회차(측정 아님을 다시 돈다)의 어림 10 + 쓴 것 5.5 는 상한 안이다
    # task 의 어림 2.0 × 10 = 20 과 그때 쓴 것 6.5 의 합이 25 를 넘는다
    assert board.run() == 1
    assert [r.task_id for r in board.saved()].count(task.task_id) == 0
    (line,) = [x for x in board.lines if "상한" in x]
    assert "$6.50" in line and "$25.00" in line and task.task_id in line and "$20.00" in line


def test_이어_도는_과제의_어림은_남은_회차의_배수다(
    판짜기: Callable[..., 판], 원본: tuple[Path, str, str]
) -> None:
    task = _과제(1, 원본, arms=("A", "B"), pr_cost=10.0)
    board = 판짜기([task], cap=12.0)
    board.records.mkdir()
    write_record(board.records, _기록(task, "A", 1, cost=5.0))
    board.script({_key(task, "B", 1): [_끝남(task)]})
    assert board.run() == 1  # 5 + 0.8 × 10 = 13 > 12
    (line,) = [x for x in board.lines if "상한" in x]
    assert "$8.00" in line
    board.cap = 13.5
    assert board.run() == 0
    assert _ends(board.saved()) == [("A", 1, END_DONE, None), ("B", 1, END_DONE, None)]


# --- 죽은 러너가 남긴 회차 ---


S1 = "00000000-0000-4000-8000-000000000001"
S2 = "00000000-0000-4000-8000-000000000002"


def _죽은_회차(board: 판, task: Task) -> Path:
    place = create_round_dir(board.root, task.task_id, "A", 1, token="dead")
    place.append_session_id(S1)
    place.append_session_id(S2)
    lines = [
        json.dumps({**fake.init_event(), "session_id": S1}),
        json.dumps({**fake.result_event(3.0, "글"), "session_id": S1}),
    ]
    (place.stream / f"01-{S1}.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (place.stream / f"02-{S2}.jsonl").write_text(
        json.dumps({**fake.init_event(), "session_id": S2}) + "\n", encoding="utf-8"
    )
    transcript = board.config / "projects" / "x" / f"{S2}.jsonl"
    transcript.parent.mkdir(parents=True)
    transcript.write_text(json.dumps(_응답줄()) + "\n", encoding="utf-8")
    return place.path


def test_기록_없는_회차_폴더를_측정_아님_중단으로_쓰고_그_비용이_쓴_것에_든다(
    판짜기: Callable[..., 판], 원본: tuple[Path, str, str]
) -> None:
    task = _과제(1, 원본, arms=("A",))
    board = 판짜기([task])
    board.script({_key(task, "A", 2): [_끝남(task)]})
    _죽은_회차(board, task)
    assert board.run() == 0
    dead, again = board.saved()
    assert (dead.round_no, dead.end.kind, dead.end.reason) == (1, END_NOT_MEASURED, "중단")
    assert dead.round_dir_name == f"{task.task_id}-A-1-dead"
    by_id: dict[str, Session] = {s.session_id: s for s in dead.sessions}
    assert by_id[S1].cost_usd == pytest.approx(3.0) and not by_id[S1].cost_substituted
    substituted = by_id[S2].cost_usd
    assert by_id[S2].cost_substituted and substituted is not None and substituted > 0
    assert dead.spend.claude_code_usd == pytest.approx(3.0 + substituted)
    assert (again.round_no, again.end.kind) == (2, END_DONE)


@pytest.mark.parametrize("seen", [("claude", "--resume", S2), None])
def test_그_세션이_돌거나_같은_이름_프로세스의_명령_줄을_읽지_못하면_멈춘다(
    판짜기: Callable[..., 판], 원본: tuple[Path, str, str], seen: tuple[str, ...] | None
) -> None:
    task = _과제(1, 원본, arms=("A",))
    board = 판짜기([task])
    asked: list[str] = []

    def processes(name: str) -> list[int]:
        asked.append(name)
        return [4242]

    board.processes = processes
    board.read_command_line = lambda _pid: seen
    board.script({_key(task, "A", 2): [_끝남(task)]})
    _죽은_회차(board, task)
    assert board.run() == 1
    assert board.saved() == [] and board.calls() == []
    assert asked == [Path(fake.claude()[0]).name]


def test_다른_세션의_같은_이름_프로세스는_지나간다(
    판짜기: Callable[..., 판], 원본: tuple[Path, str, str]
) -> None:
    task = _과제(1, 원본, arms=("A",))
    board = 판짜기([task])
    board.processes = lambda _name: [4242]
    board.read_command_line = lambda _pid: ("claude", "--resume", "다른-세션")
    board.script({_key(task, "A", 2): [_끝남(task)]})
    _죽은_회차(board, task)
    assert board.run() == 0
    assert [r.end.reason for r in board.saved()] == ["중단", None]


def test_다른_이름으로_띄운_세션은_훑지_못해_지나간다(
    판짜기: Callable[..., 판], 원본: tuple[Path, str, str]
) -> None:
    """모듈 독스트링의 못 보는 것: 띄운 `claude`의 끝 이름과 다른 이름의 프로세스(래퍼)는 훑지
    않는다. 그 세션이 그 프로세스에서 돌아도 지나간다(거짓 음성)."""
    task = _과제(1, 원본, arms=("A",))
    board = 판짜기([task])
    board.processes = lambda name: [4242] if name == "node" else []
    board.read_command_line = lambda _pid: ("node", "cli.js", "--resume", S2)
    board.script({_key(task, "A", 2): [_끝남(task)]})
    _죽은_회차(board, task)
    assert board.run() == 0
    assert [r.end.reason for r in board.saved()] == ["중단", None]


def test_죽은_러너가_남긴_임시_파일은_지우지_않고_번호와_판정이_보지_않는다(
    판짜기: Callable[..., 판], 원본: tuple[Path, str, str]
) -> None:
    task = _과제(1, 원본, arms=("A",))
    board = 판짜기([task])
    board.records.mkdir()
    tmp = board.records / f".{task.task_id}-A-1.json.dead.tmp"
    tmp.write_text("{반쯤", encoding="utf-8")
    board.script({_key(task, "A", 1): [_끝남(task)]})
    assert board.run() == 0
    assert _ends(board.saved()) == [("A", 1, END_DONE, None)]
    assert tmp.read_text(encoding="utf-8") == "{반쯤"


def test_같은_뿌리의_뒤_러너는_준비_중인_회차를_죽은_회차로_적고_앞_러너의_기록은_겹친다(
    판짜기: Callable[..., 판], 원본: tuple[Path, str, str]
) -> None:
    """모듈 독스트링의 못 보는 것: 러너 둘을 막지 않는다. 앞 러너가 세션 id를 적기 전의 회차를 뒤
    러너가 중단으로 적으면, 앞 러너가 그 회차의 기록을 쓸 때 `FileExistsError`가 난다."""
    task = _과제(1, 원본, arms=("A",))
    board = 판짜기([task])
    live = create_round_dir(board.root, task.task_id, "A", 1, token="live")
    board.script({_key(task, "A", 2): [_끝남(task)]})
    assert board.run() == 0
    dead = board.saved()[0]
    assert (dead.round_dir_name, dead.end.reason) == (live.path.name, "중단")
    with pytest.raises(FileExistsError):
        write_record(board.records, replace(dead, end=End(END_NOT_MEASURED, "설정", None)))


# --- 끝마다 멈춤(게이트, 끄지 못한 호출, 공식 단가) ---


def test_게이트를_돌지_못하면_측정_아님_준비로_적고_멈춘다(
    판짜기: Callable[..., 판], 원본: tuple[Path, str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    task = _과제(1, 원본, arms=("A",))
    after = _과제(2, 원본, arms=("A",))
    board = 판짜기([task, after])

    def broken(*_args: object, **_kw: object) -> object:
        raise GateError("작업 트리를 짓지 못했다")

    monkeypatch.setattr(rerun_runner, "check_result", broken)
    board.script({_key(task, "A", 1): [_끝남(task)], _key(after, "A", 1): [_끝남(after)]})
    assert board.run() == 1
    assert _ends(board.saved()) == [("A", 1, END_NOT_MEASURED, "준비")]
    assert any("게이트를 돌지 못했다" in line for line in board.lines)


def test_B의_게이트_묶음을_가르지_못하면_측정_아님_준비로_적고_멈춘다(
    판짜기: Callable[..., 판], 원본: tuple[Path, str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    task = _과제(1, 원본, arms=("A",))
    after = _과제(2, 원본, arms=("A",))
    board = 판짜기([task, after])

    def broken(*_args: object, **_kw: object) -> object:
        raise GateError("B 를 읽지 못했다")

    monkeypatch.setattr(rerun_runner, "has_gate_file", broken)
    board.script({_key(task, "A", 1): [_끝남(task)], _key(after, "A", 1): [_끝남(after)]})
    assert board.run() == 1
    assert _ends(board.saved()) == [("A", 1, END_NOT_MEASURED, "준비")]
    assert any("게이트를 돌지 못했다" in line for line in board.lines)


def test_결과_커밋이_게이트_러너를_지워도_B로_고른_묶음을_돈다(
    판짜기: Callable[..., 판], 원본: tuple[Path, str, str]
) -> None:
    task = _과제(1, 원본, arms=("A",))
    board = 판짜기([task])
    removing = fake.call(
        [fake.init_event(), fake.result_event(1.0, "다 했다")],
        git=[["switch", "-c", task.branch], ["rm", "-q", GATE_FILE], ["commit", "-m", "지웠다"]],
    )
    board.script({_key(task, "A", 1): [removing]})
    assert board.run() == 0, board.lines
    (rec,) = board.saved()
    assert rec.outcome.gates is not None
    assert [g.command for g in rec.outcome.gates] == list(GATE_COMMANDS)


def test_끄지_못하고_남긴_호출이_든_회차_뒤에_멈춘다(
    판짜기: Callable[..., 판], 원본: tuple[Path, str, str]
) -> None:
    task = _과제(1, 원본, arms=("A",))
    after = _과제(2, 원본, arms=("A",))
    board = 판짜기([task, after])
    board.read_command_line = lambda _pid: None  # 끄기 전에 명령 줄을 읽지 못해 남긴다
    outside: Json = {"name": "바깥", "path": "/x", "source": "바깥@market"}
    settings = fake.call([fake.init_event(extra_plugins=[outside])], main=[_응답줄()], hang=3.0)
    board.script({_key(task, "A", 1): [settings], _key(after, "A", 1): [_끝남(after)]})
    assert board.run() == 1
    assert any("끄지 못하고 남긴 호출" in line for line in board.lines)
    assert [r.task_id for r in board.saved()] == [task.task_id]


def test_공식_단가가_없는_모델이면_적지_못하고_멈추고_다시_띄워도_같은_자리에서_멈춘다(
    판짜기: Callable[..., 판], 원본: tuple[Path, str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    task = _과제(1, 원본, arms=("A",))
    board = 판짜기([task])
    unpriced = fake.call(
        [fake.init_event(), fake.result_event(1.0, "끝")],
        main=[_응답줄("claude-made-up-1")],
    )
    board.script({_key(task, "A", 1): [unpriced]})
    assert board.run() == 1
    assert any("기록 없이 실패했다" in line and "공식 단가" in line for line in board.lines)
    assert board.saved() == []
    board.lines.clear()
    assert board.run() == 1
    assert any("공식 단가를 셈하지 못했다" in line for line in board.lines)
    assert board.saved() == [] and len(board.calls()) == 1
    # 단가표에 그 모델을 더한 뒤 다시 띄우면 남은 폴더가 중단으로 적힌다(모듈 독스트링).
    # 그 뒤 같은 갈래의 2회차는 각본이 없어 무엇으로 끝나든 보지 않는다.
    monkeypatch.setitem(rerun_cost.PRICES, "claude-made-up-1", rerun_cost.Price(1.0, 1.0, 0.1))
    board.run()
    assert _ends(board.saved())[0] == ("A", 1, END_NOT_MEASURED, "중단")


def test_조건_판은_러너의_판으로_적는다(
    판짜기: Callable[..., 판], 원본: tuple[Path, str, str]
) -> None:
    task = _과제(1, 원본, arms=("A",))
    board = 판짜기([task], condition=CONDITION_VERSION + 4)
    board.script({_key(task, "A", 1): [_끝남(task)]})
    assert board.run() == 0
    assert [r.condition_version for r in board.saved()] == [CONDITION_VERSION + 4]


def test_러너는_records_에_회차마다_기록_파일_하나만_남긴다(
    판짜기: Callable[..., 판], 원본: tuple[Path, str, str]
) -> None:
    task = _과제(1, 원본, arms=("A",))
    board = 판짜기([task])
    board.script({_key(task, "A", 1): [_끝남(task)]})
    assert board.run() == 0
    assert os.listdir(board.records) == [f"{task.task_id}-A-1.json"]


# --- 명령 줄 ---


def _인자(tmp: Path, tasks: Path, *more: str) -> list[str]:
    return [
        str(tasks),
        "--root",
        str(tmp / "뿌리"),
        "--config-dir",
        str(tmp / "설정"),
        "--account",
        "njh6803",
        "--claude",
        "claude",
        *more,
    ]


@pytest.mark.parametrize("cap", ["nan", "inf", "0", "-1"])
def test_예산_상한이_유한한_양수가_아니면_아무것도_하지_않고_2다(
    tmp_path: Path, cap: str, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(_인자(tmp_path, tmp_path / "없는.json", "--cap", cap)) == EXIT_USAGE
    assert "예산 상한" in capsys.readouterr().err
    assert not (tmp_path / "뿌리").exists()


def test_목록에_없는_과제_id_를_다시_돌라고_하면_2다(
    tmp_path: Path, 원본: tuple[Path, str, str], capsys: pytest.CaptureFixture[str]
) -> None:
    tasks = tmp_path / "tasks.json"
    write_task_list(tasks, TaskList(kind=LIST_PILOT, tasks=(_과제(1, 원본, pilot=True),)))
    argv = _인자(tmp_path, tasks, "--cap", "10", "--rerun", "rerun-x-09")
    assert main(argv) == EXIT_USAGE
    assert "rerun-x-09" in capsys.readouterr().err
    assert not (tmp_path / "뿌리").exists()


def test_찾지_못하는_claude_는_받지_않는다(
    tmp_path: Path, 원본: tuple[Path, str, str], capsys: pytest.CaptureFixture[str]
) -> None:
    tasks = tmp_path / "tasks.json"
    write_task_list(tasks, TaskList(kind=LIST_PILOT, tasks=(_과제(1, 원본, pilot=True),)))
    argv = _인자(tmp_path, tasks, "--cap", "10")
    argv[argv.index("--claude") + 1] = str(tmp_path / "없는-claude")
    assert main(argv) == EXIT_USAGE
    assert "claude 실행 파일" in capsys.readouterr().err
    assert not (tmp_path / "뿌리").exists()


def test_맨_이름으로_준_claude_는_실제_경로로_풀어_넘긴다(
    tmp_path: Path, 원본: tuple[Path, str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    tasks = tmp_path / "tasks.json"
    write_task_list(tasks, TaskList(kind=LIST_PILOT, tasks=(_과제(1, 원본, pilot=True),)))
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    exe = bin_dir / ("claude.exe" if sys.platform == "win32" else "claude")
    exe.write_bytes(b"")
    exe.chmod(0o755)
    monkeypatch.setenv("PATH", str(bin_dir) + os.pathsep + os.environ.get("PATH", ""))
    seen: list[Settings] = []

    def capture(settings: Settings, _world: World) -> int:
        seen.append(settings)
        return EXIT_DONE

    monkeypatch.setattr(rerun_runner, "run", capture)
    assert main(_인자(tmp_path, tasks, "--cap", "10")) == EXIT_DONE
    (settings,) = seen
    (claude,) = settings.claude
    assert Path(claude).parent == bin_dir and Path(claude).name.lower() == exe.name


def test_확장자_없는_판_이름의_경로로_준_claude_도_그_경로로_넘긴다(
    tmp_path: Path, 원본: tuple[Path, str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    # 측정 기간의 판을 고정하려고 `versions/<판>`의 복사본을 준다(티켓 11). 윈도의 `shutil.which`는
    # PATHEXT 의 확장자가 없는 파일을 실행 파일로 보지 않는다
    tasks = tmp_path / "tasks.json"
    write_task_list(tasks, TaskList(kind=LIST_PILOT, tasks=(_과제(1, 원본, pilot=True),)))
    exe = tmp_path / "판" / "2.1.302"
    exe.parent.mkdir()
    exe.write_bytes(b"")
    exe.chmod(0o755)
    seen: list[Settings] = []

    def capture(settings: Settings, _world: World) -> int:
        seen.append(settings)
        return EXIT_DONE

    monkeypatch.setattr(rerun_runner, "run", capture)
    argv = _인자(tmp_path, tasks, "--cap", "10")
    argv[argv.index("--claude") + 1] = str(exe)
    assert main(argv) == EXIT_DONE
    (settings,) = seen
    assert settings.claude == (str(exe),)


def test_주_체크아웃_아래의_뿌리는_받지_않는다(
    tmp_path: Path, 원본: tuple[Path, str, str], capsys: pytest.CaptureFixture[str]
) -> None:
    tasks = tmp_path / "tasks.json"
    write_task_list(tasks, TaskList(kind=LIST_PILOT, tasks=(_과제(1, 원본, pilot=True),)))
    argv = _인자(tmp_path, tasks, "--cap", "10")
    argv[argv.index("--root") + 1] = str(main_checkout(ROOT) / "회차")
    assert main(argv) == EXIT_USAGE
    assert "주 체크아웃" in capsys.readouterr().err
