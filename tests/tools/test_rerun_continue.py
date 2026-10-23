"""tools/rerun_continue.py: 회차의 세션이 멈출 때마다 인계·끝남·개입으로 잇고, 상한에서 끊는다.

값만 받는 판정(물음표 끝, 인계 지시문, 다음 호출의 종류, 호출 앞뒤의 끝)은 지은 값으로, 고리는 가짜
`claude`(`tests/tools/fake_claude.py`)와 B 하나뿐인 임시 클론으로 돈다. 가짜가 받은 인자와 표준
입력은 설정 폴더의 파일로 본다. 끄기는 실제 명령 줄 읽기(`tools/proc_command_line.py`)를 감싼 함수를
주입해 그 함수가 세션 id 를 본 뒤에 끄는지, 끈 프로세스와 그 자식이 남지 않는지 본다.
"""

from __future__ import annotations

import os
import signal
import subprocess
import time
from collections.abc import Callable, Iterator
from dataclasses import replace
from pathlib import Path

import pytest
from tests.tools import fake_claude as fake
from tools.proc_command_line import CommandLineReader, command_line
from tools.rerun_continue import (
    BUDGET_SUBTYPE,
    INTERVENTION_MESSAGE,
    REASON_BUDGET,
    REASON_CALL,
    REASON_INTERVENTIONS,
    REASON_SESSIONS,
    REASON_TIME,
    before_call,
    call_end,
    ends_with_question,
    handoff_directive,
    next_kind,
    run_sessions,
)
from tools.rerun_files import (
    ARMS,
    CALL_FIRST,
    CALL_HANDOFF,
    CALL_INTERVENTION,
    CAP_REASONS,
    END_CAPPED,
    END_DONE,
    END_NOT_MEASURED,
    NOT_MEASURED_REASONS,
    RULE_BRANCH,
    RULE_NONE,
    RULE_ONLY,
    End,
    Json,
    Task,
    Tokens,
    read_record,
    write_record,
)
from tools.rerun_round import RoundDir, create_round_dir, session_env
from tools.rerun_session import (
    CallRun,
    CallSummary,
    Continued,
    Drove,
    Elsewhere,
    Init,
    Launched,
    Picked,
    SeenResult,
    Stop,
    directive,
    first_message,
    local_branches,
    outcome_of,
    pick_result_commit,
    round_record,
    session_record,
)
from tools.run_hooks import REPO_LOCATION_VARS

BRANCH = "feature/03-thing"
TICKET = ".scratch/rerun-x/issues/03-thing.md"
TASK = Task(
    task_id="rerun-x-03",
    ticket=TICKET,
    base="b" * 40,  # 시험마다 클론의 B 로 바꾼다
    merge="c" * 40,
    branch=BRANCH,
    tier="작은",
    size=4,
    order=0,
    pilot=False,
    pr_cost_usd=10.0,
    round_cap_usd=40.0,
    hidden_tests=("tests/test_x.py::test_a",),
    support_files=(),
    original_model_effort=None,
    arm_plan=("A",),
)
ARM = ARMS[0]
NOTHING = Elsewhere(
    official_usd=0.0,
    tokens=Tokens(input=None, output=None, cache_read=None, cache_write=None, thinking=None),
    substitutes=(),
    denied_calls=0,
    utilization_start=(),
    utilization_end=(),
    contamination=(),
    model_mismatch=(),
)
COMMIT: list[list[str]] = [["switch", "-c", BRANCH], ["commit", "--allow-empty", "-m", "x"]]


def _sid(n: int) -> str:
    return f"00000000-0000-4000-8000-{n:012d}"


S1, S2, S3, S4, S5 = (_sid(n) for n in range(1, 6))


def _handoff_out(branch: str = BRANCH) -> str:
    """`next-session`이 앱 밖에서 내는 결과 글의 꼴. 지시문은 울타리 안에 있고 앞뒤에 글이 있다."""
    return "\n".join(
        (
            "셀프 리뷰 앞에서 끊는다. 아래 지시문을 사람이 새 세션에 붙여 넣는다.",
            "",
            "```",
            f"다음 작업: {TICKET}. 나머지를 짓는다",
            "다음 단계: 구현",
            "어디서: 새 세션",
            f"시작 프롬프트: /implement {TICKET}",
            f"브랜치: {branch}",
            "모델: Opus 5.5 / xhigh",
            "읽을 것: 없음",
            "이어받을 상태: 인계: 셀프 리뷰 앞",
            "확인할 선행 조건: 없음",
            "이번 요청 범위: 구현·리뷰·커밋까지",
            "```",
            "",
            "사람이 새 세션에 붙여 넣는다.",
        )
    )


def _ended(cost: float, text: str | None = "멈췄다") -> list[Json]:
    return [fake.init_event(), fake.result_event(cost, text)]


def _git(cwd: Path, *args: str) -> str:
    env = {k: v for k, v in os.environ.items() if k not in REPO_LOCATION_VARS}
    return subprocess.run(
        ["git", "-c", "user.name=t", "-c", "user.email=t@example.com", *args],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=True,
        timeout=60,
    ).stdout


def _setup(tmp_path: Path) -> tuple[RoundDir, Path, Task]:
    place = create_round_dir(tmp_path / "뿌리", TASK.task_id, ARM.name, 1, token="t1")
    place.clone.mkdir()
    _git(place.clone, "init", "-q", "-b", "main")
    _git(place.clone, "commit", "-q", "--allow-empty", "-m", "B")
    return (
        place,
        tmp_path / "설정",
        replace(TASK, base=_git(place.clone, "rev-parse", "HEAD").strip()),
    )


def _nothing(_launched: Launched) -> End | None:
    return None


def _ids(*ids: str) -> Callable[[], str]:
    it: Iterator[str] = iter(ids)
    return lambda: next(it)


def _run(
    place: RoundDir,
    config: Path,
    task: Task,
    *,
    ids: Callable[[], str],
    screen: Callable[[Launched], End | None] = _nothing,
    clock: Callable[[], float] = time.monotonic,
    read_command_line: CommandLineReader = command_line,
) -> Continued:
    return run_sessions(
        place,
        task,
        claude=fake.claude(),
        arm=ARM,
        env=session_env(os.environ, config_dir=str(config), round_dir=place),
        directive_text=directive(task, ARM, "그것을 짓는다"),
        wall_clock_from=clock(),
        screen=screen,
        clock=clock,
        read_command_line=read_command_line,
        make_session_id=ids,
    )


def _flag(argv: Json, name: str) -> str | None:
    words = [str(a) for a in argv] if isinstance(argv, list) else []
    for i, word in enumerate(words[:-1]):
        if word == name:
            return words[i + 1]
    return None


def _kinds(got: Continued) -> list[str]:
    return [run.kind for run in got.runs]


# --- 값만 받는 판정 ---


@pytest.mark.parametrize(
    ("text", "asked"),
    [
        ("다 했다. 커밋할까요?", True),
        ("다 했다. 커밋할까요?\n\n   \n", True),  # 끝의 빈 줄과 공백만 든 줄은 뺀다
        ("확인할까요?  \t", True),  # 끝 공백을 뗀 뒤에 본다
        ("다 했다. 커밋할까요？", True),  # 전각
        ("왜 이렇게 했나? 그래서 끝냈다.", False),  # 물음표가 가운데에만 있다
        ("할까요?\n커밋했다.", False),
        ("", False),
        (None, False),
    ],
)
def test_물음표_끝은_공백만_든_줄을_뺀_마지막_줄의_끝_공백을_뗀_뒤에_본다(
    *, text: str | None, asked: bool
) -> None:
    assert ends_with_question(text) is asked


def test_인계_지시문은_다음_작업_줄부터_이번_요청_범위_줄까지다() -> None:
    got = handoff_directive(_handoff_out(), BRANCH)

    lines = got.splitlines()
    assert lines[0] == f"다음 작업: {TICKET}. 나머지를 짓는다"
    assert lines[-1] == "이번 요청 범위: 구현·리뷰·커밋까지"
    assert len(lines) == 10 and "```" not in got and "붙여 넣는다" not in got


def test_앞쪽_설명에_머리_줄과_끝_줄이_있어도_그_브랜치의_지시문_덩이를_옮긴다() -> None:
    text = "\n".join(
        (
            "지시문은 `다음 작업:` 줄로 시작한다.",
            "다음 작업: 아래 지시문을 붙여 넣는다",
            "이번 요청 범위: 설명뿐이다",
            "",
            _handoff_out(),
        )
    )

    got = handoff_directive(text, BRANCH)

    assert got == handoff_directive(_handoff_out(), BRANCH), "설명의 덩이를 지시문으로 옮겼다"


def test_다른_브랜치의_덩이를_건너_그_브랜치의_덩이를_옮긴다() -> None:
    other = _handoff_out("feature/04-other").replace("나머지를", "다른 것을")
    text = f"{_handoff_out()}\n\n{other}"

    got = handoff_directive(text, BRANCH)

    assert f"브랜치: {BRANCH}" in got.splitlines() and "다른 것을" not in got


def test_같은_브랜치의_덩이가_둘이면_마지막_덩이를_옮긴다() -> None:
    quoted = _handoff_out().replace("나머지를", "앞선 것을")  # 결과 글이 앞선 지시문을 인용했다
    text = f"{quoted}\n\n{_handoff_out()}"

    got = handoff_directive(text, BRANCH)

    assert "나머지를" in got and "앞선 것을" not in got, "앞선 덩이를 옮겼다"


def test_머리_줄과_끝_줄이_없는_지시문은_글_전체를_줄마다_다듬어_넘긴다() -> None:
    text = "  어디서: 새 세션\n브랜치: feature/03-thing  \n\n"

    assert handoff_directive(text, BRANCH) == "어디서: 새 세션\n브랜치: feature/03-thing"


def _picked(commit: str | None, rule: str, after: int | None) -> Picked:
    return Picked(commit=commit, rule=rule, commits_after_base=after)


def test_다음_호출의_종류는_같은_브랜치_지시문_결과_커밋_그_밖의_차례로_가른다() -> None:
    ahead = _picked("1" * 40, RULE_BRANCH, 2)
    none = _picked(None, RULE_NONE, None)

    # 1. 같은 브랜치의 지시문은 결과 커밋이 있어도 인계다
    assert next_kind(_handoff_out(), BRANCH, ahead) == CALL_HANDOFF
    # 2. 다른 브랜치의 지시문은 인계가 아니고, 결과 커밋이 B 뒤에 있으면 끝남이다
    assert next_kind(_handoff_out("feature/04-other"), BRANCH, ahead) is None
    assert next_kind("다 했다", BRANCH, _picked("2" * 40, RULE_ONLY, 1)) is None
    # 3. 그 밖은 개입이다. 지시문의 브랜치가 B 뒤 커밋 없이 있어도, 고르지 못했어도 그렇다
    assert next_kind("다 했다", BRANCH, _picked("1" * 40, RULE_BRANCH, 0)) == CALL_INTERVENTION
    assert next_kind("다 했다", BRANCH, none) == CALL_INTERVENTION
    assert next_kind(_handoff_out("feature/04-other"), BRANCH, none) == CALL_INTERVENTION
    assert next_kind(None, BRANCH, none) == CALL_INTERVENTION


def test_호출_전의_끝은_세션_개입의_상한_예산_시간의_차례다() -> None:
    def before(kind: str, h: int = 0, i: int = 0, usd: float = 40.0, s: float = 60.0) -> End | None:
        return before_call(kind, handoffs=h, interventions=i, left_usd=usd, left_seconds=s)

    capped = END_CAPPED
    assert before(CALL_FIRST) is None
    assert before(CALL_HANDOFF, h=2) is None  # 넷째 세션
    assert before(CALL_HANDOFF, h=3) == End(capped, REASON_SESSIONS, None)  # 다섯째 세션
    assert before(CALL_INTERVENTION, i=1) is None  # 둘째 개입
    assert before(CALL_INTERVENTION, i=2) == End(capped, REASON_INTERVENTIONS, None)  # 셋째
    assert before(CALL_INTERVENTION, h=3) is None  # 개입은 세션을 늘리지 않는다
    assert before(CALL_FIRST, usd=1.0) is None
    assert before(CALL_FIRST, usd=0.999) == End(capped, REASON_BUDGET, None)
    assert before(CALL_FIRST, s=0.0) == End(capped, REASON_TIME, None)
    assert before(CALL_HANDOFF, h=3, usd=0.0, s=0.0) == End(capped, REASON_SESSIONS, None)
    assert before(CALL_FIRST, usd=0.0, s=0.0) == End(capped, REASON_BUDGET, None)


def _launched(
    *,
    init: bool = True,
    results: tuple[SeenResult, ...] = (),
    stop: Stop = Stop.EXITED,
) -> Launched:
    return Launched(
        session_id=S1,
        budget_usd=40.0,
        stream_file=Path("01.jsonl"),
        drove=Drove(lines=(), exit_code=0 if stop is Stop.EXITED else None, stop=stop),
        summary=CallSummary(
            init=Init(tools=(), plugins=(), mcp_servers=(), version=None) if init else None,
            results=results,
            events=1,
            non_events=0,
        ),
    )


def _seen(subtype: str = "success", text: str | None = "글") -> SeenResult:
    return SeenResult(
        subtype=subtype,
        terminal_reason=None,
        num_turns=1,
        cost_usd=1.0,
        text=text,
        session_id=S1,
        usage=(),
    )


def test_호출_뒤의_끝은_끈_호출_예산_결과_없음의_차례다() -> None:
    assert call_end(_launched(results=(_seen(),))) is None
    assert call_end(_launched(results=(_seen(), _seen(BUDGET_SUBTYPE, None)))) == End(
        END_CAPPED, REASON_BUDGET, None
    )
    assert call_end(_launched(results=())) == End(END_NOT_MEASURED, REASON_CALL, None)
    assert call_end(_launched(init=False, results=(_seen(),))) == End(
        END_NOT_MEASURED, REASON_CALL, None
    )
    killed = call_end(_launched(init=False, stop=Stop.DEADLINE_KILLED))
    assert killed == End(END_CAPPED, REASON_TIME, None), "러너가 끈 호출을 측정 아님(호출)으로 봤다"
    left = call_end(_launched(results=(_seen(),), stop=Stop.DEADLINE_LEFT))
    assert left == End(END_CAPPED, REASON_TIME, None)


def test_출력을_닫고_멈춘_호출은_끄기와_상관없이_결과로_가르고_남긴_것은_잇지_않는다() -> None:
    # 출력이 닫힌 뒤에 껐으니 끄기가 결과 이벤트를 자르지 않았다. 결과가 있으면 잇고 없으면 측정
    # 아님(호출)이다. 끄지 못해 살아 있는 프로세스 곁에서는 결과가 있어도 잇지 않는다.
    assert call_end(_launched(results=(_seen(),), stop=Stop.HUNG_KILLED)) is None
    hung_dead = call_end(_launched(init=False, stop=Stop.HUNG_KILLED))
    assert hung_dead == End(END_NOT_MEASURED, REASON_CALL, None), "멈춰 끈 호출을 시간으로 셌다"
    hung_left = call_end(_launched(results=(_seen(),), stop=Stop.HUNG_LEFT))
    assert hung_left == End(END_NOT_MEASURED, REASON_CALL, None), "살아 있는 호출 뒤에 이었다"


def test_끝의_하위_이유는_기록이_받는_이유다() -> None:
    caps = (REASON_INTERVENTIONS, REASON_SESSIONS, REASON_BUDGET, REASON_TIME)
    assert set(caps) == set(CAP_REASONS)
    assert REASON_CALL in NOT_MEASURED_REASONS


# --- 갈래 셋 ---


def test_첫_호출이_결과_커밋을_남기고_물음표로_끝나면_물으며_끝남이다(tmp_path: Path) -> None:
    place, config, task = _setup(tmp_path)
    fake.write_script(config, calls=[fake.call(_ended(0.4, "다 했다. 커밋할까요?\n"), git=COMMIT)])

    got = _run(place, config, task, ids=_ids(S1))

    assert got.end == End(END_DONE, None, None)
    assert got.asked_at_end and (got.handoffs, got.interventions) == (0, 0)
    assert _kinds(got) == [CALL_FIRST]
    assert got.runs[0].ends_with_question and not got.runs[0].has_directive


def test_같은_브랜치_지시문이면_그_지시문으로_새_세션을_열고_인계로_센다(tmp_path: Path) -> None:
    place, config, task = _setup(tmp_path)
    fake.write_script(
        config,
        sessions={
            S1: [fake.call(_ended(0.4, _handoff_out()))],
            S2: [fake.call(_ended(0.3, "다 했다."), git=COMMIT)],
        },
    )

    got = _run(place, config, task, ids=_ids(S1, S2))

    # 세션 id 를 먼저 본다. 같은 id 로 다시 열면 가짜의 그 세션 차례가 바닥나 끝도 갈린다
    first, second = fake.read_calls(config)
    assert _flag(second["argv"], "--session-id") == S2 and _flag(second["argv"], "--resume") is None
    assert got.end == End(END_DONE, None, None)
    assert (got.handoffs, got.interventions) == (1, 0)
    assert _kinds(got) == [CALL_FIRST, CALL_HANDOFF]
    assert got.runs[0].has_directive and not got.runs[1].has_directive
    expected = first_message(
        str(place.clone), task.ticket, handoff_directive(_handoff_out(), BRANCH)
    )
    assert second["stdin"] == expected
    assert first["stdin"] != second["stdin"]
    assert [p.name for p in sorted(place.stream.iterdir())] == [f"01-{S1}.jsonl", f"02-{S2}.jsonl"]


def test_다른_브랜치_지시문은_인계가_아니고_결과_커밋이_있으면_끝남이다(tmp_path: Path) -> None:
    place, config, task = _setup(tmp_path)
    other = _handoff_out("feature/04-other")
    fake.write_script(config, calls=[fake.call(_ended(0.4, other), git=COMMIT)])

    got = _run(place, config, task, ids=_ids(S1))

    assert got.end == End(END_DONE, None, None)
    assert (got.handoffs, got.interventions) == (0, 0)
    assert got.runs[0].has_directive and not got.asked_at_end


def test_그_밖이면_resume_으로_한_줄을_넣고_개입_하나로_센다(tmp_path: Path) -> None:
    place, config, task = _setup(tmp_path)
    fake.write_script(
        config,
        sessions={
            S1: [
                fake.call(_ended(0.4, "어디까지 할까요?")),
                fake.call(_ended(0.9, "다 했다."), git=COMMIT),
            ]
        },
    )

    got = _run(place, config, task, ids=_ids(S1))

    assert got.end == End(END_DONE, None, None)
    assert (got.handoffs, got.interventions) == (0, 1)
    assert not got.asked_at_end  # 개입 뒤 마지막 글은 물음표로 끝나지 않았다
    assert _kinds(got) == [CALL_FIRST, CALL_INTERVENTION]
    assert got.runs[0].ends_with_question
    _, second = fake.read_calls(config)
    assert _flag(second["argv"], "--resume") == S1 and _flag(second["argv"], "--session-id") is None
    assert _flag(second["argv"], "--model") == ARM.model
    assert second["stdin"] == INTERVENTION_MESSAGE
    assert place.session_ids.read_text(encoding="utf-8").splitlines() == [S1, S1]
    assert [p.name for p in sorted(place.stream.iterdir())] == [f"01-{S1}.jsonl", f"02-{S1}.jsonl"]


def test_결과_커밋의_규칙으로_끝남을_가른다(tmp_path: Path) -> None:
    place, config, task = _setup(tmp_path)
    two = [
        ["switch", "-c", "a"],
        ["commit", "--allow-empty", "-m", "a"],
        ["switch", "-c", "b"],
        ["commit", "--allow-empty", "-m", "b"],
    ]
    fake.write_script(
        config,
        sessions={
            S1: [
                fake.call(
                    _ended(0.4), git=two
                ),  # B 뒤 커밋이 있는 브랜치가 둘이라 결과 커밋이 없다
                fake.call(_ended(0.5), git=COMMIT),  # 지시문의 브랜치가 생겼다
            ]
        },
    )

    got = _run(place, config, task, ids=_ids(S1))

    assert _kinds(got) == [CALL_FIRST, CALL_INTERVENTION]
    assert got.end == End(END_DONE, None, None)
    picked = pick_result_commit(local_branches(place.clone, task.base), task.branch)
    assert picked.rule == RULE_BRANCH and (picked.commits_after_base or 0) > 0


def test_하나뿐인_다른_브랜치의_결과_커밋도_끝남이다(tmp_path: Path) -> None:
    place, config, task = _setup(tmp_path)
    elsewhere = [["switch", "-c", "fix/y"], ["commit", "--allow-empty", "-m", "y"]]
    fake.write_script(config, calls=[fake.call(_ended(0.4), git=elsewhere)])

    got = _run(place, config, task, ids=_ids(S1))

    assert got.end == End(END_DONE, None, None) and _kinds(got) == [CALL_FIRST]
    assert pick_result_commit(local_branches(place.clone, task.base), task.branch).rule == RULE_ONLY


def test_결과_이벤트_없이_끝난_호출은_개입이_아니라_측정_아님_호출이다(tmp_path: Path) -> None:
    place, config, task = _setup(tmp_path)
    fake.write_script(config, calls=[fake.call([fake.init_event()], exit_code=1)])

    got = _run(place, config, task, ids=_ids(S1))

    assert got.end == End(END_NOT_MEASURED, REASON_CALL, None)
    assert _kinds(got) == [CALL_FIRST] and got.interventions == 0
    assert len(fake.read_calls(config)) == 1


def test_막는_판정이_낸_끝이_측정_아님_호출보다_앞선다(tmp_path: Path) -> None:
    place, config, task = _setup(tmp_path)
    fake.write_script(config, calls=[fake.call([fake.init_event()], exit_code=1)])
    limit = End(END_NOT_MEASURED, "한도", 1792962000)
    looked: list[str] = []

    def screen(launched: Launched) -> End | None:
        looked.append(launched.session_id)
        return limit

    got = _run(place, config, task, ids=_ids(S1), screen=screen)

    assert got.end == limit and looked == [S1]


# --- 상한 ---


def test_개입이_셋째가_되면_그_호출을_하지_않고_상한으로_끊긴다(tmp_path: Path) -> None:
    place, config, task = _setup(tmp_path)
    asking = [fake.call(_ended(0.1 * n, "어디까지 할까요?")) for n in (1, 2, 3, 4)]
    fake.write_script(config, sessions={S1: asking})

    got = _run(place, config, task, ids=_ids(S1))

    assert got.end == End(END_CAPPED, REASON_INTERVENTIONS, None)
    assert _kinds(got) == [CALL_FIRST, CALL_INTERVENTION, CALL_INTERVENTION]
    assert got.interventions == 2 and len(fake.read_calls(config)) == 3
    assert got.runs[-1].ends_with_question
    assert not got.asked_at_end  # 물으며 끝남은 끝남의 표시다


def test_세션이_다섯째가_되면_그_호출을_하지_않고_상한으로_끊긴다(tmp_path: Path) -> None:
    place, config, task = _setup(tmp_path)
    fake.write_script(
        config, sessions={s: [fake.call(_ended(0.1, _handoff_out()))] for s in (S1, S2, S3, S4, S5)}
    )

    got = _run(place, config, task, ids=_ids(S1, S2, S3, S4, S5))

    assert got.end == End(END_CAPPED, REASON_SESSIONS, None)
    assert _kinds(got) == [CALL_FIRST, CALL_HANDOFF, CALL_HANDOFF, CALL_HANDOFF]
    assert got.handoffs == 3 and [c["session_id"] for c in fake.read_calls(config)] == [
        S1,
        S2,
        S3,
        S4,
    ]


# --- 예산 ---


def test_호출마다_넘긴_예산은_상한에서_이어_부를_세션까지_쓴_것을_뺀_값이다(tmp_path: Path) -> None:
    place, config, task = _setup(tmp_path)
    fake.write_script(
        config,
        sessions={
            # 결과 이벤트의 비용은 그 세션의 누적이다. 둘째 호출 뒤 S1 은 15.25 를 썼다
            S1: [fake.call(_ended(10.5)), fake.call(_ended(15.25, _handoff_out()))],
            S2: [fake.call(_ended(3.0, "다 했다."), git=COMMIT)],
        },
    )

    got = _run(place, config, task, ids=_ids(S1, S2))

    assert got.end == End(END_DONE, None, None)
    budgets = [_flag(c["argv"], "--max-budget-usd") for c in fake.read_calls(config)]
    # 40 - 0, 40 - 10.5(이어 부를 S1 의 몫), 40 - 15.25(S1 의 마지막 누적)
    assert budgets == ["40.00", "29.50", "24.75"]
    assert [r.launched.budget_usd for r in got.runs] == [40.0, 29.5, 24.75]


def test_남은_예산이_1달러_미만이면_세션을_열지_않고_상한으로_끊긴다(tmp_path: Path) -> None:
    place, config, task = _setup(tmp_path)
    fake.write_script(config, sessions={S1: [fake.call(_ended(39.01)), fake.call(_ended(39.5))]})

    got = _run(place, config, task, ids=_ids(S1))

    assert got.end == End(END_CAPPED, REASON_BUDGET, None)
    assert _kinds(got) == [CALL_FIRST] and got.interventions == 0
    assert len(fake.read_calls(config)) == 1


def test_error_max_budget_usd_인_호출은_상한으로_끊긴다(tmp_path: Path) -> None:
    place, config, task = _setup(tmp_path)
    fake.write_script(config, calls=[fake.call([fake.init_event(), fake.budget_result(40.2)])])

    got = _run(place, config, task, ids=_ids(S1))

    assert got.end == End(END_CAPPED, REASON_BUDGET, None)
    assert _kinds(got) == [CALL_FIRST] and len(fake.read_calls(config)) == 1


# --- 끄기 ---


def _jumps_after_first_line(place: RoundDir, nth: int) -> Callable[[], float]:
    """`nth`째 호출의 원본 줄이 하나라도 오면 4시간을 훌쩍 넘긴 값을 내는 시계."""

    def clock() -> float:
        landed = any(p.stat().st_size > 0 for p in place.stream.glob(f"{nth:02d}-*.jsonl"))
        return time.monotonic() + (10.0**6 if landed else 0.0)

    return clock


def _alive(pid: int, marker: str) -> bool:
    """그 pid 가 아직 명령 줄에 `marker`를 실은 프로세스인가. pid 가 재사용됐으면 거짓이다."""
    argv = command_line(pid)
    return argv is not None and marker in argv


def _gone(pid: int, marker: str) -> bool:
    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        if not _alive(pid, marker):
            return True
        time.sleep(0.2)
    return False


def _pid(entry: dict[str, Json]) -> int:
    pid = entry["pid"]
    assert isinstance(pid, int)
    return pid


def _recording(seen: list[tuple[str, ...] | None]) -> CommandLineReader:
    def read(pid: int) -> tuple[str, ...] | None:
        argv = command_line(pid)
        seen.append(argv)
        return argv

    return read


def test_벽시계를_넘긴_첫_호출은_명령_줄의_세션_id_를_본_뒤_트리째_끈다(tmp_path: Path) -> None:
    place, config, task = _setup(tmp_path)
    fake.write_script(config, calls=[fake.call([fake.init_event()], child=600, hang=600)])
    seen: list[tuple[str, ...] | None] = []

    got = _run(
        place,
        config,
        task,
        ids=_ids(S1),
        clock=_jumps_after_first_line(place, 1),
        read_command_line=_recording(seen),
    )

    assert got.end == End(END_CAPPED, REASON_TIME, None)
    [argv] = seen
    assert argv is not None and _flag(list(argv), "--session-id") == S1
    [call] = fake.read_calls(config)
    [child] = fake.read_children(config)
    assert _gone(_pid(call), S1) and _gone(_pid(child), S1)
    drove = got.runs[0].launched.drove
    assert drove.stop is Stop.DEADLINE_KILLED
    assert drove.exit_code is None
    assert '"init"' in (place.stream / f"01-{S1}.jsonl").read_text(encoding="utf-8")


def test_벽시계를_넘긴_resume_호출도_명령_줄의_세션_id_를_본_뒤_끈다(tmp_path: Path) -> None:
    place, config, task = _setup(tmp_path)
    fake.write_script(
        config,
        sessions={
            S1: [
                fake.call(_ended(0.4)),
                fake.call([fake.init_event()], child=600, hang=600),
            ]
        },
    )
    seen: list[tuple[str, ...] | None] = []

    got = _run(
        place,
        config,
        task,
        ids=_ids(S1),
        clock=_jumps_after_first_line(place, 2),
        read_command_line=_recording(seen),
    )

    assert got.end == End(END_CAPPED, REASON_TIME, None)
    assert _kinds(got) == [CALL_FIRST, CALL_INTERVENTION] and got.interventions == 1
    [argv] = seen
    assert argv is not None and _flag(list(argv), "--resume") == S1
    _, call = fake.read_calls(config)
    [child] = fake.read_children(config)
    assert _gone(_pid(call), S1) and _gone(_pid(child), S1)
    assert got.runs[1].launched.drove.stop is Stop.DEADLINE_KILLED
    assert session_record(S1, got.runs, config).runner_killed, "마감에 끈 세션에 표시가 없다"


@pytest.mark.parametrize(
    ("stop", "marked", "left"),
    [
        (Stop.EXITED, False, False),
        (Stop.DEADLINE_KILLED, True, False),
        (Stop.DEADLINE_LEFT, False, True),
        (Stop.HUNG_KILLED, False, False),  # 출력이 닫힌 뒤라 끄기가 결과를 자르지 않았다
        (Stop.HUNG_LEFT, False, True),
    ],
)
def test_세션의_끈_표시는_마감에_끈_호출에만_서고_남긴_호출은_호출_칸에_든다(
    tmp_path: Path, *, stop: Stop, marked: bool, left: bool
) -> None:
    runs = [
        CallRun(
            CALL_FIRST, _launched(results=(_seen(),)), has_directive=False, ends_with_question=False
        ),
        CallRun(
            CALL_INTERVENTION, _launched(stop=stop), has_directive=False, ends_with_question=False
        ),
    ]

    got = session_record(S1, runs, tmp_path)

    assert got.runner_killed is marked, "세션의 끈 표시가 멈춘 꼴과 다르다"
    assert [c.kill_skipped for c in got.calls] == [False, left], "남긴 호출의 칸이 멈춘 꼴과 다르다"


def _end_left(pid: int, marker: str) -> None:
    """시험이 남긴 가짜를 끈다. 끄기 직전에 명령 줄에 표지가 있는지
    본다(`.claude/rules/probes.md`)."""
    if _alive(pid, marker):
        os.kill(pid, signal.SIGTERM)


@pytest.mark.parametrize(
    "answer",
    [("python", "다른-프로세스"), None],
    ids=["세션_id_없는_명령_줄", "읽지_못함"],
)
def test_명령_줄에_세션_id_가_없거나_읽지_못하면_끄지_않고_기록한다(
    tmp_path: Path, answer: tuple[str, ...] | None
) -> None:
    place, config, task = _setup(tmp_path)
    fake.write_script(config, calls=[fake.call([fake.init_event()], hang=600)])
    seen: list[int] = []

    def read(pid: int) -> tuple[str, ...] | None:
        seen.append(pid)
        return answer

    try:
        got = _run(
            place,
            config,
            task,
            ids=_ids(S1),
            clock=_jumps_after_first_line(place, 1),
            read_command_line=read,
        )

        assert got.end == End(END_CAPPED, REASON_TIME, None)
        drove = got.runs[0].launched.drove
        assert drove.stop is Stop.DEADLINE_LEFT
        assert len(seen) == 1
        [call] = fake.read_calls(config)
        assert _alive(_pid(call), S1)  # 끄지 않았다
        record = round_record(
            place,
            task,
            condition_version=1,
            claude_version=None,
            account="njh6803",
            env={},
            continued=got,
            config_dir=config,
            outcome=outcome_of(pick_result_commit({}, task.branch)),
            wall_clock_from=0.0,
            now=1.0,
            elsewhere=NOTHING,
        )
        records = tmp_path / "records"
        records.mkdir()
        [session] = read_record(write_record(records, record)).sessions
        assert session.calls[0].kill_skipped and not session.runner_killed
    finally:
        for call in fake.read_calls(config):
            _end_left(_pid(call), S1)


# --- 회차 기록 ---


def test_회차_기록에_호출의_종류와_이어_가기_칸과_끈_세션의_표시가_든다(tmp_path: Path) -> None:
    place, config, task = _setup(tmp_path)
    fake.write_script(
        config,
        sessions={
            S1: [fake.call(_ended(10.5)), fake.call(_ended(15.25, _handoff_out()))],
            S2: [fake.call(_ended(3.0, "커밋했다. 다음은?"), git=COMMIT)],
        },
    )
    got = _run(place, config, task, ids=_ids(S1, S2))

    record = round_record(
        place,
        task,
        condition_version=1,
        claude_version=None,
        account="njh6803",
        env={},
        continued=got,
        config_dir=config,
        outcome=outcome_of(pick_result_commit(local_branches(place.clone, task.base), BRANCH)),
        wall_clock_from=0.0,
        now=1.0,
        elsewhere=NOTHING,
    )
    records = tmp_path / "records"
    records.mkdir()
    back = read_record(write_record(records, record))

    assert (back.handoffs, back.interventions, back.asked_at_end) == (1, 1, True)
    assert back.end == End(END_DONE, None, None)
    first, second = back.sessions
    assert first.session_id == S1 and second.session_id == S2
    assert [c.kind for c in first.calls] == [CALL_FIRST, CALL_INTERVENTION]
    assert [c.kind for c in second.calls] == [CALL_HANDOFF]
    assert [c.has_directive for c in first.calls] == [False, True]
    assert [c.ends_with_question for c in second.calls] == [True]
    assert not any(c.kill_skipped for s in back.sessions for c in s.calls)
    assert not first.runner_killed and not second.runner_killed
    assert (first.cost_usd, second.cost_usd) == (15.25, 3.0)
    assert back.spend.claude_code_usd == 18.25
