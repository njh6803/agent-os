"""다시 풀기 회차의 이어 가기와 상한. 세션 호출이 멈출 때마다 결과 글과 클론을 보고 인계·끝남·개입
가운데 하나로 잇고, 개입·세션·예산·시간의 상한에서 회차를 끊는다.

명세는 `.scratch/model-rerun/spec.md`의 "이어 가기와 끝"·"상한과 끄기"이고 티켓은
`.scratch/model-rerun/issues/08-continue-and-caps.md`다. 설계 5절의 이어 가기가 원천이다.

갈래 셋. 1. 결과 글에 회차 지시문과 같은 브랜치의 인계 지시문이 있으면(첫 턴 훅의
`directive_branch`로 알아본다) 그 지시문으로 새 세션을 연다. 인계로 세고 개입으로 세지 않는다. 2.
1이 아니고 결과 커밋이 B 뒤에 있으면 끝남이다. 3. 그 밖이면 `--resume`으로 같은 세션에
`INTERVENTION_MESSAGE` 한 줄을 넣고 개입 하나로 센다. 결과 글은 글이 빈 것을 뺀 마지막 결과 이벤트의
`result`이고(`result_text`), 끝남의 마지막 결과 글이 물음표로 끝나면 물으며
끝남이다(`ends_with_question`).

호출 앞뒤의 끝. 호출 앞에서는 셋째 개입·다섯째 세션·$1 미만의 남은 예산·4시간을 넘긴 벽시계면 그
호출을 하지 않고 상한으로 끊는다(`before_call`). 호출 뒤에서는 먼저 주입받은 `screen`(09의 한도·설정
판정이 들어갈 자리)이 낸 끝을 따르고, 그다음 시간을 넘긴 호출, `error_max_budget_usd`, 끄지 않고
남긴 호출과 init 이나 결과 이벤트가 없는 호출(측정 아님(호출))의 차례로 본다(`call_end`). 결과
이벤트 없이 끝난 호출을 갈래 3으로 보내면 Claude Code가 죽은 것이 개입으로 셈해진다. 끄지 않고 남긴
호출 뒤에 이어 가면 살아 있는 프로세스 곁에서 같은 세션을 이어 부르거나 같은 클론에 새 세션을 연다.

예산. 호출마다 넘기는 값은 회차 상한에서 그 호출 전까지 회차가 쓴 것을 뺀 값이다. 쓴 것은 세션마다
마지막 비용(`session_cost`)의 합이고, `--resume`으로 이어 부를 세션이 이미 쓴 몫도 든다. 예산
플래그는 그 호출의 몫만 세기 때문이다.

끄기는 `tools/rerun_session.py`의 `drive`가 한다. 이 모듈은 벽시계의 남은 시간을 호출의 시간
제한으로 넘기고, 시계와 명령 줄 읽기를 주입받아 그대로 넘긴다.

못 보는 것.
- 결과 커밋은 호출이 끝난 뒤의 클론만 본다. 세션이 B 뒤에 커밋하고 그 브랜치를 지웠으면 끝남이
  아니다.
- 인계 지시문은 결과 글의 덩이(`다음 작업:` 줄부터 그 뒤 첫 `이번 요청 범위:` 줄까지) 가운데 그
  브랜치의 지시문인 마지막 덩이를 줄마다 다듬어 옮긴다(`handoff_directive`). 그런 덩이가 없으면 글
  전체다. 덩이 안의 다른 글(설명 문장)은 거르지 않는다.
- 마감에 닿아 끈 호출이 든 세션의 비용은 모른다. 그 몫은 예산의 쓴 것에 들지 않지만, 시간의 끄기는
  회차를 끝내므로 뒤의 호출이 없다. 그 몫을 공식 단가로 대신 넣는 것은 10이다. 출력을 닫고 멈춰 끈
  호출은 결과 이벤트가 있으면 그 비용이 있고 회차가 이어진다.
"""

from __future__ import annotations

import time
from collections.abc import Callable, Mapping, Sequence

from tools.hook_prompt_directive import directive_branch
from tools.proc_command_line import CommandLineReader, command_line
from tools.rerun_files import (
    CALL_FIRST,
    CALL_HANDOFF,
    CALL_INTERVENTION,
    END_CAPPED,
    END_DONE,
    END_NOT_MEASURED,
    Arm,
    End,
    Task,
)
from tools.rerun_round import RoundDir
from tools.rerun_session import (
    TIMED_OUT,
    CallRun,
    Continued,
    Launched,
    Opening,
    Picked,
    Stop,
    first_message,
    launch,
    local_branches,
    new_session_id,
    pick_result_commit,
    result_text,
    session_cost,
)

INTERVENTION_MESSAGE = "지시문의 이번 요청 범위를 끝까지 마친다"
BUDGET_SUBTYPE = "error_max_budget_usd"

# 끝의 하위 이유. `tools/rerun_files.py`의 CAP_REASONS·NOT_MEASURED_REASONS 에 든다(시험이 본다)
REASON_INTERVENTIONS = "개입"
REASON_SESSIONS = "세션"
REASON_BUDGET = "예산"
REASON_TIME = "시간"
REASON_CALL = "호출"

MAX_INTERVENTIONS = 2  # 셋째 개입을 하지 않는다
MAX_SESSIONS = 4  # 다섯째 세션을 열지 않는다
MIN_BUDGET_USD = 1.0
WALL_CLOCK_SECONDS = 4 * 60 * 60

# 호출의 종류마다 세션을 여는 꼴. 개입만 같은 세션을 이어 부른다
_OPENINGS = {
    CALL_FIRST: Opening.NEW,
    CALL_HANDOFF: Opening.NEW,
    CALL_INTERVENTION: Opening.RESUME,
}
_DIRECTIVE_HEAD = "다음 작업:"
_DIRECTIVE_TAIL = "이번 요청 범위:"
_QUESTION_MARKS = ("?", "？")


def ends_with_question(text: str | None) -> bool:
    """결과 글에서 공백만 든 줄을 뺀 마지막 줄이 끝 공백을 뗀 뒤 `?`나 `？`로 끝나는가."""
    lines = [line.rstrip() for line in (text or "").splitlines() if line.strip()]
    return bool(lines) and lines[-1].endswith(_QUESTION_MARKS)


def handoff_directive(text: str, branch: str) -> str:
    """결과 글에서 `branch`의 인계 지시문을 옮긴다. `다음 작업:` 줄부터 그 뒤 첫 `이번 요청 범위:`
    줄까지(끝 줄이 없으면 글의 끝까지)를 한 덩이로 보고, 뒤의 덩이부터 그 덩이만으로
    `directive_branch`가 `branch`인 첫 덩이를 옮긴다. 앞쪽 설명에 머리 줄과 끝 줄이 든 글에서 설명을
    옮기지 않으려는 것이다. 그런 덩이가 없으면 글 전체를 옮긴다. 갈래 1은 글 전체가 `branch`의
    지시문일 때만 나므로, 받는 쪽 훅도 같은 판정으로 알아본다. 줄마다 다듬고 앞뒤의 빈 줄은 뗀다."""
    lines = [line.strip() for line in text.splitlines()]
    heads = [i for i, line in enumerate(lines) if line.startswith(_DIRECTIVE_HEAD)]
    for head in reversed(heads):
        tail = next(
            (i for i in range(head, len(lines)) if lines[i].startswith(_DIRECTIVE_TAIL)),
            len(lines) - 1,
        )
        block = "\n".join(lines[head : tail + 1]).strip()
        if directive_branch(block) == branch:
            return block
    return "\n".join(lines).strip()


def next_kind(text: str | None, branch: str, picked: Picked) -> str | None:
    """호출이 결과를 낸 뒤 다음 호출의 종류. 끝남이면 None 이다.

    1. 결과 글에 `branch`와 같은 브랜치의 인계 지시문이 있으면 인계다(결과 커밋이 있어도).
    2. 1이 아니고 결과 커밋이 B 뒤에 있으면 끝남이다.
    3. 그 밖은 개입이다."""
    if text is not None and directive_branch(text) == branch:
        return CALL_HANDOFF
    if picked.commit is not None and (picked.commits_after_base or 0) > 0:
        return None
    return CALL_INTERVENTION


def before_call(
    kind: str, *, handoffs: int, interventions: int, left_usd: float, left_seconds: float
) -> End | None:
    """그 호출을 하기 전의 끝. 세는 수는 그 호출 전까지의 것이다. 세션·개입의 상한, 예산, 시간의
    차례로 본다."""
    if kind == CALL_HANDOFF and handoffs >= MAX_SESSIONS - 1:
        return End(END_CAPPED, REASON_SESSIONS, None)
    if kind == CALL_INTERVENTION and interventions >= MAX_INTERVENTIONS:
        return End(END_CAPPED, REASON_INTERVENTIONS, None)
    if left_usd < MIN_BUDGET_USD:
        return End(END_CAPPED, REASON_BUDGET, None)
    if left_seconds <= 0:
        return End(END_CAPPED, REASON_TIME, None)
    return None


def call_end(launched: Launched) -> End | None:
    """호출 하나가 끝난 뒤의 끝. 시간을 넘긴 호출, 예산을 다 쓴 호출, 끄지 않고 남긴 호출과 init
    이나 결과 이벤트가 없는 호출의 차례로 본다. 시간을 넘긴 호출은 러너가 끊으려 한 것이라 결과
    이벤트가 없어도 측정 아님(호출)이 아니다(명세 "이어 가기와 끝"의 "러너가 끈 것"). 출력을 닫고
    멈춰 끈 호출은 끄기가 결과 이벤트를 자르지 않았으므로 결과 이벤트가 없으면 측정 아님(호출)이고,
    끄지 못한 호출은 프로세스가 살아 있어 결과 이벤트가 있어도 측정 아님(호출)이다."""
    stop = launched.drove.stop
    if stop in TIMED_OUT:
        return End(END_CAPPED, REASON_TIME, None)
    summary = launched.summary
    if any(r.subtype == BUDGET_SUBTYPE for r in summary.results):
        return End(END_CAPPED, REASON_BUDGET, None)
    if stop is Stop.HUNG_LEFT or summary.init is None or not summary.results:
        return End(END_NOT_MEASURED, REASON_CALL, None)
    return None


def run_sessions(
    place: RoundDir,
    task: Task,
    *,
    claude: Sequence[str],
    arm: Arm,
    env: Mapping[str, str],
    directive_text: str,
    wall_clock_from: float,
    screen: Callable[[Launched], End | None],
    clock: Callable[[], float] = time.monotonic,
    read_command_line: CommandLineReader = command_line,
    make_session_id: Callable[[], str] = new_session_id,
) -> Continued:
    """회차의 세션을 끝까지 잇는다. 첫 호출은 `directive_text`로 새 세션을 연다.

    `wall_clock_from`은 `clock`의 눈금으로 잰 준비가 끝난 때다(04의 `Setup.wall_clock_from`).
    `screen`은 호출마다 가장 먼저 그 호출의 끝(한도, 설정 등)을 낸다. 끝이 없으면 None 이다."""
    root = str(place.clone)
    deadline = wall_clock_from + WALL_CLOCK_SECONDS
    runs: list[CallRun] = []
    spent: dict[str, float] = {}  # 세션 id 마다 마지막 비용
    handoffs = interventions = 0
    kind = CALL_FIRST
    session_id = make_session_id()
    message = first_message(root, task.ticket, directive_text)
    while True:
        left_usd = task.round_cap_usd - sum(spent.values())
        left_seconds = deadline - clock()
        end = before_call(
            kind,
            handoffs=handoffs,
            interventions=interventions,
            left_usd=left_usd,
            left_seconds=left_seconds,
        )
        if end is not None:
            break
        launched = launch(
            place,
            claude=claude,
            arm=arm,
            env=env,
            session_id=session_id,
            opening=_OPENINGS[kind],
            message=message,
            budget_usd=left_usd,
            timeout=left_seconds,
            clock=clock,
            read_command_line=read_command_line,
        )
        if kind == CALL_HANDOFF:
            handoffs += 1
        elif kind == CALL_INTERVENTION:
            interventions += 1
        cost, _ = session_cost(launched.summary.results, session_id)
        if cost is not None:
            spent[session_id] = cost
        text = result_text(launched.summary.results)
        runs.append(
            CallRun(
                kind=kind,
                launched=launched,
                has_directive=text is not None and directive_branch(text) is not None,
                ends_with_question=ends_with_question(text),
            )
        )
        end = screen(launched) or call_end(launched)
        if end is not None:
            break
        picked = pick_result_commit(local_branches(place.clone, task.base), task.branch)
        following = next_kind(text, task.branch, picked)
        if following is None:
            end = End(END_DONE, None, None)
            break
        if following == CALL_INTERVENTION:
            message = INTERVENTION_MESSAGE
        else:  # 인계는 결과 글에 지시문이 있을 때만 난다
            session_id = make_session_id()
            message = first_message(root, task.ticket, handoff_directive(text or "", task.branch))
        kind = following
    asked = end.kind == END_DONE and runs[-1].ends_with_question
    return Continued(
        runs=tuple(runs),
        handoffs=handoffs,
        interventions=interventions,
        asked_at_end=asked,
        end=end,
    )
