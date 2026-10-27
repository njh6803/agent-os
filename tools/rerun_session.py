"""다시 풀기 회차의 세션 하나. 클론에서 실제 지시문 모양의 첫 메시지로 `claude -p`를 띄우고,
스트림과 세션 기록 파일을 읽어 회차 기록의 칸을 짓는다.

명세는 `.scratch/model-rerun/spec.md`의 "러너가 기대는 `claude -p`의 동작"·"명령과 막는 규칙"·
"지시문과 첫 메시지"·"이어 가기와 끝"의 결과 커밋·"회차 기록"이고 티켓은
`.scratch/model-rerun/issues/06-round-drive-record.md`다. 같은 일을 프로브 크기로 한 것은
`.scratch/model-rerun/probes/headless_flags/headless_flags.py`의 `drive`·`summarize`·
`transcript_effort`·`record`다. 옮기며 셋으로 나눴다.

- 요약(스트림 줄 → 값): `summarize_call`, `result_text`, `session_cost`, `count_lines`. 줄을
  JSON으로 풀어 `type`으로 알아보고, 풀지 못한 줄은 예외로 던지지 않고 이벤트가 아닌 줄로 센다.
- 판정(값 → 값): `start_line`·`ticket_title`·`directive`·`first_message`(첫 메시지),
  `session_command`(명령), `pick_result_commit`(결과 커밋의 세 규칙), `call_record`·
  `session_record`·`round_record`(회차 기록의 칸). 하위 프로세스를 부르지 않는다.
- 구동(하위 프로세스): `drive`(세션 호출 하나), `launch`(세션 id를 적고 띄운다), `claude_version`,
  `local_branches`(클론의 로컬 브랜치). 호출마다 시간 제한이 있다.

끄기(명세 "상한과 끄기"). 마감을 넘긴 호출, 출력을 닫고도 끝나지 않은 호출, 줄 판정(`drive`의
`watch`, 09의 설정 확인)이 끄라고 한 호출은 끄기 직전에 그 pid 의 명령
줄(`tools/proc_command_line.py`, 주입받는다)에 그 호출의 세션 id 가 있을 때만(`_ours`) 프로세스
나무째 끈다(`_kill`). 없거나 읽지 못하면 끄지 않고 남긴다. 호출이 멈춘 꼴은 `Stop`이다.
나무째 끄는 것은 윈도 venv 의 `python.exe`처럼 진짜 프로그램을 자식으로 띄우는 런처가 있어서다. 그
하나만 끄면 진짜가 남는다. 출력이 닫힌 뒤 끝나기를 기다리는 것(`REAP_TIMEOUT`)도 호출의 마감을
넘지 않고, 마감이 먼저 오면 시간을 넘긴 호출이다. 마감 뒤에 더 쓰는 시간은 끄기(윈도 `taskkill`
한 번, `KILL_TIMEOUT`), 끈 프로세스를 거두는 기다림(`REAP_TIMEOUT`), 남은 줄의
배출(`DRAIN_TIMEOUT`)이다.

첫 메시지. 첫 줄은 `tools/open_session.ps1`의 `Convert-StartLine`이 `/implement <티켓 경로>`를 옮긴
꼴이고(시험이 그 함수를 pwsh로 불러 같은지 본다), 빈 줄, 지시문이 뒤따른다. 첫 줄의 연 저장소는
`launch`가 세션의 작업 폴더로 넘긴 글 그대로다. 클론의 첫 턴 훅(`tools/hook_prompt_directive.py`)이
그 값을 세션의 작업 폴더와 견주고, 그 견줌은 구분자와 대소문자만 접는다. 지시문은 명세 "지시문의
틀"이고 갈래 사이에 `모델:` 줄만 다르다.

세션의 비용과 `modelUsage`는 그 세션 id의 마지막 결과 이벤트의 값이다. `--resume`의 결과 이벤트가
세션 누적을 싣기 때문이다(`probes/README.md` 2026-10-22). 결과 글은 글이 빈 것(공백만 든 것 포함)을
뺀 마지막 결과 이벤트의 `result`다(`서브-2.jsonl`). 노력과 모델은 세션 기록 파일에서 센다. 파일은
작업 폴더 이름을 셈하지 않고 `<설정 폴더>/projects/*/<세션 id>.jsonl`, 서브에이전트는
`<세션 id>/subagents/*.jsonl`로 찾는다. 모델이 `<synthetic>`이고 노력이 없는 줄은 뺀다. 불일치를
판정하는 것은 09다.

결과 커밋(명세 "결과 커밋"). 지시문의 `브랜치:` 이름의 로컬 브랜치가 있으면 그 끝이다. 없으면 main이
아닌 로컬 브랜치 가운데 B 뒤에 커밋이 있는 것이 하나뿐일 때 그 끝이고, 둘 이상이거나 없으면 결과
커밋이 없다. 고른 규칙과 B 뒤 커밋 수를 낸다. 지시문의 브랜치는 B 뒤 커밋이 0이어도 그 끝을 고른다.
끝남인지(B 뒤에 커밋이 있는지)를 가르는 것은 08이다.

커밋하는 기록에는 모델이 쓴 글과 도구 입력이 없다. 원본 stream-json은 받는 대로 회차 폴더의
`stream/`에 쓰고, 세션 기록 파일은 설정 폴더에 남는다. 기록의 글 칸은 그 값이 나오는 자리에서만
옮긴다. init의 도구 목록은 init 이벤트의 `tools`, 판은 `claude --version`의 첫 줄, 계정 이름과 환경
변수의 이름은 러너가 받은 값이다.

이 모듈 밖의 칸. 이어 가기(호출의 종류, 인계·개입 수, 물으며 끝남, 호출의 지시문 담음·물음표 끝,
끝의 종류)는 `tools/rerun_continue.py`가 짓고 `Continued`로 넘긴다. 공식 단가·토큰 합·대신 넣은
값은 07, 거부 수·사용률·오염·모델 불일치는 09가 짓는다. `round_record`는 그 칸을 인자로
받는다(`Elsewhere`).

못 보는 것.
- 세션 기록 파일의 줄에서 `message.model`이 모델의 꼴(`tools/rerun_files.py`의
  `MODEL_FORM`)이 아니면 그 줄을 세지 않는다. 노력이 영소문자
  식별자가 아니면 노력 없음으로 센다. 결과 이벤트의 `subtype`이 영소문자 식별자가 아니면
  `unknown`으로, `terminal_reason`이 그렇지 않으면 빈 값으로 적는다. 기록의
  꼴(`tools/rerun_files.py`)이 거부해 기록을 잃지 않으려는 것이고, 그 줄과 이벤트의 원본은 회차
  폴더와 설정 폴더에 남는다.
- 표준 입력은 따로 스레드가 쓴다. 자식이 읽지 않고 끝나면 그 스레드는 파이프 오류로 끝난다.
- 결과 커밋은 클론의 로컬 브랜치(`refs/heads/`)만 본다. 세션이 분리 HEAD에 커밋했거나 태그만
  남겼으면 결과 커밋이 없다.
"""

from __future__ import annotations

import contextlib
import json
import math
import os
import re
import signal
import subprocess
import sys
import threading
import time
import uuid
from collections import Counter
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from decimal import ROUND_FLOOR, Decimal
from enum import Enum
from pathlib import Path
from typing import IO

from tools.probe_kit import LineReader
from tools.proc_command_line import CommandLineReader, command_line
from tools.rerun_files import (
    IDENT_FORM,
    MODEL_FORM,
    RULE_BRANCH,
    RULE_NONE,
    RULE_ONLY,
    VERSION_FORM,
    Arm,
    Call,
    End,
    Hit,
    Json,
    LineCount,
    ModelUsage,
    Outcome,
    Record,
    ResultEvent,
    Session,
    Spend,
    Substitute,
    Task,
    Tokens,
    Window,
    parse_round_dir_name,
)
from tools.rerun_round import RoundDir
from tools.run_hooks import REPO_LOCATION_VARS

GIT_TIMEOUT = 60
VERSION_TIMEOUT = 60
# 끝난 자식을 거두는 기다림과 남은 줄의 배출. 손자가 출력을 쥐고 남으면 EOF 가 오지 않는다.
REAP_TIMEOUT = 60
DRAIN_TIMEOUT = 10
KILL_TIMEOUT = 60  # 윈도의 `taskkill` 한 번
_READ_SLICE = 5.0  # 줄 하나를 기다리는 한 번. 마감은 호출의 시간 제한이다

# --- 첫 메시지와 지시문(명세 "지시문과 첫 메시지") ---

START_SKILL = "implement"
_START_SKILL_FILE = f".claude/skills/{START_SKILL}/SKILL.md"
# `tools/open_session.ps1`의 `Convert-StartLine`이 짓는 문장. 두 곳이 갈리면 실제 세션과 다른 길로
# 스킬이 실린다. 시험이 그 함수를 pwsh 로 불러 견준다.
_START_LINE = (
    "{skill} 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `{root}`이고 작업 폴더가 그곳이 아니면"
    " 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: {rest}"
)
_TITLE_HEAD = re.compile(r"#\s+(?:[0-9]+:\s*)?")


def start_line(root: str, ticket: str) -> str:
    """첫 줄. `/implement <티켓 경로>`를 `Convert-StartLine`이 옮긴 꼴이다."""
    return _START_LINE.format(skill=_START_SKILL_FILE, root=root, rest=ticket).rstrip()


def ticket_title(text: str) -> str:
    """티켓 파일의 첫 제목 줄에서 `# NN:`·`# ` 머리를 뗀 글. 제목 줄이 없으면 `ValueError`다."""
    for line in text.splitlines():
        if head := _TITLE_HEAD.match(line):
            return line[head.end() :].strip()
    raise ValueError("티켓 파일에 `# ` 제목 줄이 없다")


def directive(task: Task, arm: Arm, title: str) -> str:
    """회차의 지시문(명세 "지시문의 틀"). 갈래 사이에 `모델:` 줄만 다르다. 워크트리 문장은 없다."""
    return "\n".join(
        (
            f"다음 작업: {task.ticket}. {title}",
            "다음 단계: 구현",
            "어디서: 새 세션",
            f"시작 프롬프트: /{START_SKILL} {task.ticket}",
            f"브랜치: {task.branch}",
            f"모델: {arm.label}",
            "읽을 것: 없음",
            "이어받을 상태: 없음",
            "확인할 선행 조건: 없음",
            "이번 요청 범위: 구현·리뷰·커밋까지",
        )
    )


def first_message(root: str, ticket: str, directive_text: str) -> str:
    """첫 메시지. 첫 줄, 빈 줄, 지시문이다."""
    return f"{start_line(root, ticket)}\n\n{directive_text}"


# --- 명령(설계 5절과 명세 "명령과 막는 규칙") ---

SESSION_FLAGS = (
    "-p",
    "--permission-mode",
    "auto",
    "--setting-sources",
    "user,project,local",
    "--strict-mcp-config",
    "--output-format",
    "stream-json",
    "--verbose",
)


def budget_text(usd: float) -> str:
    """`--max-budget-usd`에 넘길 글. 센트 아래를 버려 남은 값을 넘지 않는다. 음수는 0이다.
    버림은 `repr`의 십진 글에서 한다. `math.floor(0.29 * 100)`은 28이라 정확히 센트로 떨어지는
    값도 한 센트를 잃는다. 그래서 돌려준 글을 `float`로 다시 넣어도 같은 글이 나온다. `nan`과
    무한대는 `ValueError`다. 넘긴 글이 `nan`이면 Claude Code 가 그것을 어떻게 읽는지 모른다."""
    if not math.isfinite(usd):
        raise ValueError(f"예산은 유한한 값이어야 한다: {usd!r}")
    cents = Decimal(repr(usd)).quantize(Decimal("0.01"), rounding=ROUND_FLOOR)
    return f"{max(Decimal(0), cents):.2f}"  # 같으면 앞의 것이라 `-0.0`도 "0.00"이다


class Opening(Enum):
    """세션 호출이 세션을 여는 꼴. 값이 그 명령의 플래그다."""

    NEW = "--session-id"  # 러너가 지은 id 로 새 세션을 연다
    RESUME = "--resume"  # 그 세션을 이어 부른다


def session_command(
    claude: Sequence[str],
    arm: Arm,
    session_id: str,
    budget_usd: float,
    *,
    settings: Path,
    opening: Opening = Opening.NEW,
) -> list[str]:
    """세션 호출의 명령. 세션은 `opening`의 플래그로 연다. 이어 부를 때도 모델·노력·예산을 다시
    준다. 모델은 전체 이름이고 `claude`는 명령 줄로 받은 실행 파일(과 그 인자)이다. `settings`는
    막는 규칙 파일이고 `--settings`로 넘긴다(`tools/rerun_round.py`의 `write_deny_rules`)."""
    return [
        *claude,
        SESSION_FLAGS[0],
        "--model",
        arm.model,
        "--effort",
        arm.effort,
        *SESSION_FLAGS[1:],
        "--settings",
        str(settings),
        opening.value,
        session_id,
        "--max-budget-usd",
        budget_text(budget_usd),
    ]


# --- 요약(스트림 줄 → 값) ---

SYNTHETIC = "<synthetic>"
UNKNOWN_SUBTYPE = "unknown"


@dataclass(frozen=True)
class Init:
    """init 이벤트에서 옮기는 것. 09가 `mcp_servers`·`plugins`를 허용 모임과 견준다."""

    tools: tuple[str, ...]
    plugins: tuple[str, ...]
    mcp_servers: tuple[str, ...]
    version: str | None


@dataclass(frozen=True)
class SeenResult:
    """결과 이벤트 하나. 글(`text`)은 커밋하는 기록에 옮기지 않는다."""

    subtype: str | None
    terminal_reason: str | None
    num_turns: int | None
    cost_usd: float | None  # `total_cost_usd`. 세션 누적이다
    text: str | None  # `result`
    session_id: str | None
    usage: tuple[ModelUsage, ...]  # `modelUsage`


@dataclass(frozen=True)
class CallSummary:
    init: Init | None  # 그 호출의 첫 init
    results: tuple[SeenResult, ...]
    events: int  # `type`이 있는 JSON 객체 줄의 수
    non_events: int  # 비지 않았는데 이벤트가 아닌 줄의 수


def _parse_json(text: str) -> Json:
    # `json.loads`의 반환형은 Any라 `Json`으로 받아 뒤의 좁히기가 타입 검사를 지나게 한다.
    return json.loads(text)


def _obj(v: Json) -> dict[str, Json]:
    return v if isinstance(v, dict) else {}


def _list(v: Json) -> list[Json]:
    return v if isinstance(v, list) else []


def _str(v: Json) -> str | None:
    return v if isinstance(v, str) else None


def _int(v: Json) -> int | None:
    return v if isinstance(v, int) and not isinstance(v, bool) else None


def _num(v: Json) -> float | None:
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
        return None
    return float(v)


def _names(v: Json) -> tuple[str, ...]:
    """글의 목록이거나 `name`을 가진 객체의 목록에서 이름을 꺼낸다."""
    out: list[str] = []
    for item in _list(v):
        name = item if isinstance(item, str) else _str(_obj(item).get("name"))
        if name is not None:
            out.append(name)
    return tuple(out)


def parse_event(line: str) -> dict[str, Json] | None:
    """stream-json 줄 하나를 이벤트로 푼다. JSON 객체이고 `type`이 글일 때만 이벤트다."""
    if not line.lstrip().startswith("{"):
        return None
    try:
        value = _parse_json(line)
    except ValueError:  # 시간 제한에 끊기면 마지막 줄이 잘린다
        return None
    except RecursionError:  # 깊게 중첩된 줄. 풀지 못한 줄과 같이 이벤트가 아니다
        return None
    if isinstance(value, dict) and isinstance(value.get("type"), str):
        return value
    return None


def _usage(v: Json) -> tuple[ModelUsage, ...]:
    out: list[ModelUsage] = []
    for model, raw in sorted(_obj(v).items()):
        u = _obj(raw)
        counts = [
            _int(u.get(k))
            for k in (
                "inputTokens",
                "outputTokens",
                "cacheReadInputTokens",
                "cacheCreationInputTokens",
            )
        ]
        cost = _num(u.get("costUSD"))
        if not MODEL_FORM.fullmatch(model) or cost is None or cost < 0:
            continue
        if any(c is None or c < 0 for c in counts):
            continue
        thinking = _int(u.get("thinkingTokens"))
        out.append(
            ModelUsage(
                model=model,
                input_tokens=counts[0] or 0,
                output_tokens=counts[1] or 0,
                cache_read_tokens=counts[2] or 0,
                cache_write_tokens=counts[3] or 0,
                thinking_tokens=thinking if thinking is None or thinking >= 0 else None,
                cost_usd=cost,
            )
        )
    return tuple(out)


def _result(event: dict[str, Json]) -> SeenResult:
    turns = _int(event.get("num_turns"))
    return SeenResult(
        subtype=_str(event.get("subtype")),
        terminal_reason=_str(event.get("terminal_reason")),
        num_turns=turns if turns is None or turns >= 0 else None,
        cost_usd=_num(event.get("total_cost_usd")),
        text=_str(event.get("result")),
        session_id=_str(event.get("session_id")),
        usage=_usage(event.get("modelUsage")),
    )


def summarize_call(lines: Iterable[str]) -> CallSummary:
    """호출 하나의 stream-json 줄을 요약한다."""
    init: Init | None = None
    results: list[SeenResult] = []
    events = non_events = 0
    for line in lines:
        event = parse_event(line)
        if event is None:
            non_events += bool(line.strip())
            continue
        events += 1
        kind = event.get("type")
        if kind == "system" and event.get("subtype") == "init" and init is None:
            init = Init(
                tools=_names(event.get("tools")),
                plugins=_names(event.get("plugins")),
                mcp_servers=_names(event.get("mcp_servers")),
                version=_str(event.get("claude_code_version")),
            )
        elif kind == "result":
            results.append(_result(event))
    return CallSummary(init=init, results=tuple(results), events=events, non_events=non_events)


def result_text(results: Sequence[SeenResult]) -> str | None:
    """결과 글. 글이 빈 것(공백만 든 것 포함)을 뺀 마지막 결과 이벤트의 `result`다."""
    for r in reversed(results):
        if r.text is not None and r.text.strip():
            return r.text
    return None


def session_cost(
    results: Iterable[SeenResult], session_id: str
) -> tuple[float | None, tuple[ModelUsage, ...]]:
    """세션의 비용과 `modelUsage`. 그 세션 id의 결과 이벤트 가운데 비용이 있는 마지막 것의 값이다.
    결과 이벤트의 합이 아니다. 그런 이벤트가 없으면 빈 값이다."""
    last: SeenResult | None = None
    for r in results:
        if r.session_id == session_id and r.cost_usd is not None:
            last = r
    if last is None:
        return None, ()
    return last.cost_usd, last.usage


# --- 세션 기록 파일 ---


def transcript_files(config_dir: Path, session_id: str) -> tuple[list[Path], list[Path]]:
    """본 세션의 기록 파일과 서브에이전트의 기록 파일. 작업 폴더 이름을 셈하지 않는다."""
    projects = config_dir / "projects"
    main = sorted(p for p in projects.glob(f"*/{session_id}.jsonl") if p.is_file())
    side = sorted(
        p
        for d in projects.glob(f"*/{session_id}")
        if d.is_dir()
        for p in (d / "subagents").glob("*.jsonl")
        if p.is_file()
    )
    return main, side


def count_lines(lines: Iterable[str]) -> tuple[LineCount, ...]:
    """기록 파일의 assistant 줄을 모델과 노력으로 센다. `<synthetic>`이고 노력이 없는 줄은 뺀다."""
    counts: Counter[tuple[str, str | None]] = Counter()
    for line in lines:
        record = parse_event(line)
        if record is None or record.get("type") != "assistant":
            continue
        model = _str(_obj(record.get("message")).get("model"))
        if model is None or not MODEL_FORM.fullmatch(model):
            continue
        effort = _str(record.get("effort"))
        if effort is not None and not IDENT_FORM.fullmatch(effort):
            effort = None
        if model == SYNTHETIC and effort is None:
            continue
        counts[(model, effort)] += 1
    return tuple(
        LineCount(model=m, effort=e, lines=n)
        for (m, e), n in sorted(counts.items(), key=lambda kv: (kv[0][0], kv[0][1] or ""))
    )


def _read_lines(paths: Iterable[Path]) -> list[str]:
    """`\\n`으로만 가른다. `splitlines`는 Node가 이스케이프하지 않은 글 안의 U+2028에서도 가른다."""
    out: list[str] = []
    for p in paths:
        out.extend(p.read_text(encoding="utf-8", errors="replace").split("\n"))
    return out


def transcript_counts(
    config_dir: Path, session_id: str
) -> tuple[tuple[LineCount, ...], tuple[LineCount, ...]]:
    """본 세션과 서브에이전트의 모델·노력 수."""
    main, side = transcript_files(config_dir, session_id)
    return count_lines(_read_lines(main)), count_lines(_read_lines(side))


# --- 결과 커밋(명세 "결과 커밋") ---

MAIN_BRANCH = "main"


@dataclass(frozen=True)
class Picked:
    commit: str | None
    rule: str  # `tools/rerun_files.py`의 RULES
    commits_after_base: int | None  # 고른 브랜치의 B 뒤 커밋 수. 고르지 못했으면 빈 값


def pick_result_commit(branches: Mapping[str, tuple[str, int]], directive_branch: str) -> Picked:
    """결과 커밋의 세 규칙. `branches`는 main이 아닌 로컬 브랜치마다 (끝 커밋, B 뒤 커밋 수)다."""
    if directive_branch in branches:
        tip, after = branches[directive_branch]
        return Picked(commit=tip, rule=RULE_BRANCH, commits_after_base=after)
    ahead = [(tip, after) for tip, after in branches.values() if after > 0]
    if len(ahead) == 1:
        tip, after = ahead[0]
        return Picked(commit=tip, rule=RULE_ONLY, commits_after_base=after)
    return Picked(commit=None, rule=RULE_NONE, commits_after_base=None)


def outcome_of(picked: Picked) -> Outcome:
    """결과 커밋만 든 결과 칸. 결과 작업 트리의 준비·게이트·숨은 시험은 07이 채운다."""
    return Outcome(
        commit=picked.commit,
        rule=picked.rule,
        commits_after_base=picked.commits_after_base,
        setup_failure=None,
        gates=None,
        hidden=None,
    )


def _git_env() -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if k not in REPO_LOCATION_VARS}
    env["GIT_TERMINAL_PROMPT"] = "0"
    return env


def _git(cwd: Path, *args: str) -> str:
    done = subprocess.run(
        ["git", *args],
        cwd=cwd,
        env=_git_env(),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=GIT_TIMEOUT,
        check=False,
    )
    if done.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} 이 {done.returncode} 로 끝났다: {done.stderr}")
    return done.stdout


def local_branches(clone: Path, base: str) -> dict[str, tuple[str, int]]:
    """클론의 main이 아닌 로컬 브랜치마다 (끝 커밋, B 뒤 커밋 수)."""
    out: dict[str, tuple[str, int]] = {}
    listed = _git(clone, "for-each-ref", "--format=%(objectname) %(refname)", "refs/heads/")
    for line in listed.splitlines():
        tip, _, ref = line.partition(" ")
        name = ref.removeprefix("refs/heads/")
        if not ref.startswith("refs/heads/") or name == MAIN_BRANCH:
            continue
        after = int(_git(clone, "rev-list", "--count", f"{base}..{tip}").strip())
        out[name] = (tip, after)
    return out


# --- 구동 ---


class Stop(Enum):
    """세션 호출 하나가 멈춘 꼴(모듈 독스트링의 끄기). 러너가 끄려 하는 것은 살아 있는 채 마감에
    닿은 호출(`DEADLINE_*`), 출력을 닫고도 거두는 기다림 안에 끝나지 않은 호출(`HUNG_*`), 줄
    판정(`drive`의 `watch`)이 끄라고 한 호출(`HALTED_*`)이고, 명령 줄에 그 세션 id 가 없거나 읽지
    못하면 끄지 않고 남긴다(`*_LEFT`)."""

    EXITED = "exited"  # 스스로 끝났다. 종료 코드가 있다
    DEADLINE_KILLED = "deadline_killed"  # 마감에 닿아 나무째 껐다
    DEADLINE_LEFT = "deadline_left"  # 마감에 닿았지만 끄지 않았다
    HUNG_KILLED = "hung_killed"  # 출력을 닫고 멈춰 나무째 껐다
    HUNG_LEFT = "hung_left"  # 출력을 닫고 멈췄지만 끄지 않았다
    HALTED_KILLED = "halted_killed"  # 줄 판정이 끄라고 해 나무째 껐다
    HALTED_LEFT = "halted_left"  # 줄 판정이 끄라고 했지만 끄지 않았다


TIMED_OUT = frozenset({Stop.DEADLINE_KILLED, Stop.DEADLINE_LEFT})  # 시간을 넘긴 호출
# 끄지 않고 남긴 호출
LEFT_RUNNING = frozenset({Stop.DEADLINE_LEFT, Stop.HUNG_LEFT, Stop.HALTED_LEFT})
# 러너가 출력 도중에 끈 호출. 끄기가 결과 이벤트를 자를 수 있다(`session_record`의 `runner_killed`)
CUT_SHORT = frozenset({Stop.DEADLINE_KILLED, Stop.HALTED_KILLED})
# 끄려 한 호출의 꼴. 열쇠는 (시간을 넘겼는가, 껐는가)
_STOPS = {
    (True, True): Stop.DEADLINE_KILLED,
    (True, False): Stop.DEADLINE_LEFT,
    (False, True): Stop.HUNG_KILLED,
    (False, False): Stop.HUNG_LEFT,
}


@dataclass(frozen=True)
class Drove:
    lines: tuple[str, ...]
    exit_code: int | None  # `Stop.EXITED`일 때만 값이 있다
    stop: Stop


def _feed(stdin: IO[bytes], data: bytes) -> None:
    try:
        stdin.write(data)
        stdin.close()
    except OSError:  # 메시지를 다 받기 전에 끝난 자식은 파이프를 닫는다
        pass


def never(_line: str) -> bool:
    """줄 판정의 기본값. 어느 줄에서도 끄라고 하지 않는다."""
    return False


def drive(
    command: Sequence[str],
    *,
    cwd: str,
    env: Mapping[str, str],
    message: str,
    stream_file: Path,
    timeout: float,
    session_id: str,
    clock: Callable[[], float] = time.monotonic,
    read_command_line: CommandLineReader = command_line,
    watch: Callable[[str], bool] = never,
) -> Drove:
    """세션 호출 하나. 메시지를 표준 입력으로 넣고 줄을 받는 대로 `stream_file`에 쓴다.

    출력은 `tools/probe_kit.py`의 `LineReader`로 읽고(줄 하나마다 제한 시간, 끝에 남은 줄은
    `drain`), 읽지 않는 stderr는 버린다. `timeout`을 넘기면 명령 줄에 `session_id`가 있는지 본 뒤
    프로세스 나무째 끈다(모듈 독스트링의 끄기). 받은 줄을 쓴 뒤 `watch`가 참이면 그 줄에서 읽기를
    멈추고 같은 규칙으로 끈다(09의 설정 확인이 허용 밖의 init 에서 끈다). 그때 이미 끝났으면 스스로
    끝난 호출이다. 멈춘 꼴은 `Drove.stop`이다. 자식이 스스로 끝났으면 손자가 출력을 쥐어 EOF가 오지
    않아도 기다리지 않고, 시간을 넘긴 호출로 적지 않는다. POSIX 에서는
    자식이 새 세션(프로세스 그룹)을 이끌게 띄워 그 그룹을 끈다. 그래서 러너의 터미널에서 친 Ctrl+C
    가 자식에 닿지 않고, 러너가 끊길 때(`KeyboardInterrupt`도) 이 함수가 같은 규칙으로 끈다.
    """
    process = subprocess.Popen(
        list(command),
        cwd=cwd,
        env=dict(env),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        start_new_session=True,  # 윈도에서는 쓰지 않는 인자다
    )

    def ours() -> bool:
        return _ours(process, session_id, read_command_line)

    stdin, stdout = process.stdin, process.stdout
    if stdin is None or stdout is None:  # PIPE 를 주었으므로 나지 않는다
        if ours():
            _kill(process)
        raise RuntimeError("자식의 표준 입출력을 열지 못했다")
    try:
        return _read_process(
            process, stdin, stdout, message, stream_file, timeout, clock, ours, watch
        )
    except BaseException:
        # 기록 파일을 열거나 쓰다 예외가 났거나 러너가 끊겼으면 자식을 남기지 않는다
        if process.poll() is None and ours():
            _kill(process)
        raise


def _ours(
    process: subprocess.Popen[bytes], session_id: str, read_command_line: CommandLineReader
) -> bool:
    """끄기 직전에 볼 것. 그 pid 의 명령 줄에 그 호출의 세션 id 가 있는가. 읽지 못하면 거짓이다.
    모르는 프로세스를 끄지 않는 쪽이 안전하다(명세 "상한과 끄기"). 거두기 전이라 그 pid 는 다른
    프로세스에 가지 않았다(`tools/proc_command_line.py`)."""
    argv = read_command_line(process.pid)
    return argv is not None and session_id in argv


def _kill(process: subprocess.Popen[bytes]) -> None:
    """프로세스 나무째 끄고 거둔다."""
    _kill_tree(process)
    process.wait(timeout=REAP_TIMEOUT)


def _kill_tree(process: subprocess.Popen[bytes]) -> None:
    """그 프로세스와 그 아래 프로세스를 끈다. 윈도는 `taskkill /T`가 부모를 따라 찾고, POSIX 는 그
    프로세스가 이끄는 그룹을 끈다(`drive`의 `start_new_session`). `taskkill`을 띄우지 못했거나
    시간을 넘겼어도, 그룹을 끄지 못했어도 그 프로세스는 `Popen`의 핸들로 끈다. 선례는
    `tools/mutate.py`의 `_kill_tree`다."""
    if sys.platform == "win32":
        with contextlib.suppress(OSError, subprocess.TimeoutExpired):
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,  # 출력을 붙잡으면 남은 손자가 파이프를 쥘 때 멈춘다
                stderr=subprocess.DEVNULL,
                check=False,
                timeout=KILL_TIMEOUT,
            )
    else:
        with contextlib.suppress(ProcessLookupError, PermissionError):
            os.killpg(process.pid, signal.SIGKILL)
    process.kill()


def _read_process(
    process: subprocess.Popen[bytes],
    stdin: IO[bytes],
    stdout: IO[bytes],
    message: str,
    stream_file: Path,
    timeout: float,
    clock: Callable[[], float],
    ours: Callable[[], bool],
    watch: Callable[[str], bool],
) -> Drove:
    reader = LineReader(stdout)
    threading.Thread(target=_feed, args=(stdin, message.encode("utf-8")), daemon=True).start()
    lines: list[str] = []
    timed_out = halted = False
    deadline = clock() + timeout
    with stream_file.open("w", encoding="utf-8", newline="") as raw:

        def keep(line: str) -> None:
            lines.append(line)
            raw.write(line)
            raw.flush()

        while not reader.ended:
            left = deadline - clock()
            if left <= 0:
                timed_out = process.poll() is None  # 마감 전에 스스로 끝났으면 넘긴 호출이 아니다
                break
            line = reader.readline(min(left, _READ_SLICE))
            if line is not None:
                keep(line)
                if watch(line):
                    halted = True
                    break
            elif process.poll() is not None:
                # 자식은 끝났는데 손자가 출력을 쥐어 EOF 가 오지 않는다. 남은 줄은 drain 이 받는다
                break
        code: int | None = None
        if halted:
            code = process.poll()  # 이미 끝났으면 스스로 끝난 호출이다
        elif not timed_out:
            reap = min(REAP_TIMEOUT, deadline - clock())  # 거두는 기다림도 마감을 넘지 않는다
            try:
                code = process.wait(timeout=max(reap, 0.0))
            except subprocess.TimeoutExpired:  # 출력을 닫고도 끝나지 않았다
                timed_out = reap < REAP_TIMEOUT  # 거둠의 제한보다 마감이 먼저 왔다
        stop = Stop.EXITED
        if code is None:
            killing = ours()
            if killing:
                _kill(process)
            halt = Stop.HALTED_KILLED if killing else Stop.HALTED_LEFT
            stop = halt if halted else _STOPS[timed_out, killing]
        for line in reader.drain(DRAIN_TIMEOUT):
            keep(line)
    return Drove(lines=tuple(lines), exit_code=code, stop=stop)


def claude_version(claude: Sequence[str], *, env: Mapping[str, str], cwd: Path) -> str | None:
    """`claude --version`의 첫 줄. 판의 꼴이 아니거나 0이 아니게 끝나거나 시간을 넘기면 빈
    값이다."""
    try:
        done = subprocess.run(
            [*claude, "--version"],
            cwd=cwd,
            env=dict(env),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=VERSION_TIMEOUT,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    first = done.stdout.strip().splitlines()[:1]
    if done.returncode != 0 or not first or not VERSION_FORM.fullmatch(first[0].strip()):
        return None
    return first[0].strip()


@dataclass(frozen=True)
class Launched:
    session_id: str
    budget_usd: float  # 넘긴 `--max-budget-usd`의 값
    stream_file: Path
    drove: Drove
    summary: CallSummary


def new_session_id() -> str:
    return str(uuid.uuid4())


def launch(
    place: RoundDir,
    *,
    claude: Sequence[str],
    arm: Arm,
    env: Mapping[str, str],
    session_id: str,
    opening: Opening,
    message: str,
    budget_usd: float,
    timeout: float,
    clock: Callable[[], float] = time.monotonic,
    read_command_line: CommandLineReader = command_line,
    watch: Callable[[str], bool] = never,
) -> Launched:
    """회차 폴더의 클론에서 세션 호출 하나를 띄운다. 띄우기 전에 세션 id를 회차 폴더의
    `session_ids`에 덧붙이고(`RoundDir.append_session_id`), 원본 줄은 `<호출 차례 두 자리>-<세션
    id>.jsonl`에 받는다. 세션은 `opening`대로 새로 열거나 이어 부른다. 세션의 작업 폴더는
    `str(place.clone)`이라, 새 세션의 메시지(`first_message`)도 그 글을 연 저장소로 지어야 첫 턴
    훅의 폴더 견줌을 지난다. `watch`는 `drive`의 줄 판정이다."""
    place.append_session_id(session_id)
    calls = place.call_count()
    budget = float(budget_text(budget_usd))
    stream_file = place.stream / f"{calls:02d}-{session_id}.jsonl"
    drove = drive(
        session_command(
            claude, arm, session_id, budget, settings=place.deny_settings, opening=opening
        ),
        cwd=str(place.clone),
        env=env,
        message=message,
        stream_file=stream_file,
        timeout=timeout,
        session_id=session_id,
        clock=clock,
        read_command_line=read_command_line,
        watch=watch,
    )
    return Launched(
        session_id=session_id,
        budget_usd=budget,
        stream_file=stream_file,
        drove=drove,
        summary=summarize_call(drove.lines),
    )


# --- 회차 기록의 칸 ---


@dataclass(frozen=True)
class CallRun:
    """호출 하나와 그 호출의 이어 가기 판정(`tools/rerun_continue.py`가 결과 글에서 낸다)."""

    kind: str  # `tools/rerun_files.py`의 CALL_KINDS
    launched: Launched
    has_directive: bool
    ends_with_question: bool


@dataclass(frozen=True)
class Continued:
    """회차의 호출들과 이어 가기의 셈. `tools/rerun_continue.py`의 `run_sessions`가 짓는다."""

    runs: tuple[CallRun, ...]  # 차례대로
    handoffs: int
    interventions: int
    asked_at_end: bool
    end: End


@dataclass(frozen=True)
class Elsewhere:
    """회차 기록 가운데 이 모듈이 짓지 않는 칸. 공식 단가·토큰 합·대신 넣은 값은 07, 나머지는
    09다."""

    official_usd: float
    tokens: Tokens
    substitutes: tuple[Substitute, ...]
    denied_calls: int
    utilization_start: tuple[Window, ...]
    utilization_end: tuple[Window, ...]
    contamination: tuple[Hit, ...]
    model_mismatch: tuple[LineCount, ...]


def call_record(run: CallRun) -> Call:
    results = tuple(
        ResultEvent(
            index=i,
            subtype=r.subtype if r.subtype and IDENT_FORM.fullmatch(r.subtype) else UNKNOWN_SUBTYPE,
            terminal_reason=(
                r.terminal_reason
                if r.terminal_reason is not None and IDENT_FORM.fullmatch(r.terminal_reason)
                else None
            ),
            num_turns=r.num_turns,
        )
        for i, r in enumerate(run.launched.summary.results)
    )
    return Call(
        kind=run.kind,
        budget_usd=run.launched.budget_usd,
        exit_code=run.launched.drove.exit_code,
        results=results,
        has_directive=run.has_directive,
        ends_with_question=run.ends_with_question,
        kill_skipped=run.launched.drove.stop in LEFT_RUNNING,
    )


def session_record(session_id: str, runs: Sequence[CallRun], config_dir: Path) -> Session:
    """세션 하나의 칸. `runs`는 그 세션의 호출들이고 차례대로다. 러너가 출력 도중에 끈
    호출(`CUT_SHORT`. 마감에 닿은 것과 줄 판정이 끄라고 한 것)이 있으면 `runner_killed`를 세운다.
    그 호출은 대개 결과 이벤트가 나기 전에 끊겨 그 세션의 Claude Code 셈을 모른다. 결과 이벤트를
    내고 출력을 닫은 뒤 거두는 기다림 중에 마감이 온 호출은 결과 이벤트가 있어 셈을 안다. 그래서
    셈을 공식 단가로 대신 넣는 것(`cost_substituted`, 10)은 이 표시가 아니라 끈 호출의 결과
    이벤트가 없는지로 가른다. 출력을 닫고 멈춰 끈 호출(`Stop.HUNG_KILLED`)은 세우지 않는다. 출력이
    이미 끝나 끄기가 결과 이벤트를 자르지 않았고, 결과 이벤트가 없으면 그 회차는 측정
    아님(호출)이다(`tools/rerun_continue.py`의 `call_end`)."""
    cost, usage = session_cost(
        (r for run in runs for r in run.launched.summary.results), session_id
    )
    main, side = transcript_counts(config_dir, session_id)
    return Session(
        session_id=session_id,
        calls=tuple(call_record(r) for r in runs),
        cost_usd=cost,
        cost_substituted=False,
        runner_killed=any(r.launched.drove.stop in CUT_SHORT for r in runs),
        model_usage=usage,
        main_lines=main,
        subagent_lines=side,
    )


def round_record(
    place: RoundDir,
    task: Task,
    *,
    condition_version: int,
    claude_version: str | None,
    account: str,
    env: Mapping[str, str],
    continued: Continued,
    config_dir: Path,
    outcome: Outcome,
    wall_clock_from: float,
    now: float,
    elsewhere: Elsewhere,
) -> Record:
    """회차 기록. 식별은 회차 폴더의 이름에서, 환경은 러너가 받은 값과 첫 init에서 옮긴다.

    벽시계는 준비가 끝난 뒤(`wall_clock_from`, 04의 `Setup.wall_clock_from`)부터 `now`까지다.
    Claude Code의 셈은 세션마다 마지막 비용의 합이고, 비용을 모르는 세션은 더하지 않는다(대신 넣는
    것은 10).
    """
    named = parse_round_dir_name(place.name)
    if named is None or named.task_id != task.task_id:
        raise ValueError(f"과제 {task.task_id} 의 회차 폴더가 아니다: {place.name}")
    runs = continued.runs
    runs_by_session: dict[str, list[CallRun]] = {}
    for run in runs:
        runs_by_session.setdefault(run.launched.session_id, []).append(run)
    sessions = tuple(session_record(sid, rs, config_dir) for sid, rs in runs_by_session.items())
    init = next((r.launched.summary.init for r in runs if r.launched.summary.init), None)
    e = elsewhere
    return Record(
        task_id=task.task_id,
        arm=named.arm,
        round_no=named.round_no,
        condition_version=condition_version,
        pilot=task.pilot,
        round_dir_name=place.name,
        claude_version=claude_version,
        account=account,
        env_names=tuple(sorted(env)),
        init_tools=init.tools if init else (),
        sessions=sessions,
        handoffs=continued.handoffs,
        interventions=continued.interventions,
        asked_at_end=continued.asked_at_end,
        end=continued.end,
        outcome=outcome,
        spend=Spend(
            claude_code_usd=sum(s.cost_usd for s in sessions if s.cost_usd is not None),
            official_usd=e.official_usd,
            other_usd=0.0,  # 러너가 회차를 마친 뒤 셈해 넣는다(러너의 `_with_costs`)
            tokens=e.tokens,
            substitutes=e.substitutes,
            wall_seconds=round(max(now - wall_clock_from, 0.0), 2),
            denied_calls=e.denied_calls,
            utilization_start=e.utilization_start,
            utilization_end=e.utilization_end,
            contamination=e.contamination,
            model_mismatch=e.model_mismatch,
        ),
    )
