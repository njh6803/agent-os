"""바꾼 규칙·스킬·서브에이전트가 새 `claude -p` 세션에 실리는지 카나리아 질문으로 잰다.

절차의 원천은 `docs/constitution/operations.md` 환경 규약 상세의 카나리아 항목이다. 세션마다
스크래치에 카나리아 스크립트를 새로 짓다가 커밋되지 않아 리뷰가 다시 잴 수 없었고(대기열 129),
규칙 명령에 둔 `.claude/` 읽기 거부가 `paths` 규칙의 로드까지 막아 실험군과 대조군이 모두
"없음"인 채로 확인이 조용히 비었다(대기열 127, 일지 2026-10-06-15). 워크트리 세션에서는 회차를
반복문으로 묶은 명령을 앱의 가드가 거부했다(대기열 120). 그래서 명세 파일 하나를 받아 모든 회차를
이 도구 안에서 돌리고, 셸에는 단순 명령 하나만 남긴다. 서브에이전트 갈래가 없어 확인 스크립트를
세 번 손으로 지었고, 뒤의 두 번은 판정이 거짓 통과 자리를 다시 열거나 새로 냈다(대기열 153, 일지
2026-10-11-01·2026-10-12-02).

사용: uv run python tools/canary.py <명세.toml> <출력 디렉터리>

명세는 TOML 이다. 체크아웃은 이 도구를 부른 폴더 기준이다.

    kind = "rule"                    # rule 이면 --tools Read, skill 이면 --tools Skill,
                                     # agent 면 --tools Agent 와 agent_tools
    model = "sonnet"                 # 선택. 기본 sonnet
    question = '''
    Read 도구로 `{target}` 하나만 통째로 읽어라. ...없으면 "없음"이라고만 답하라.
    '''                              # stdin 으로 간다. rule 이면 {target} 이 갈래의 대상으로 바뀐다
    expect = ["식별자는 영문"]        # 카나리아. 바뀐 본문에만 있는 글. 질문에 있으면 안 된다
    source = ".claude/rules/tools.md"  # 바뀐 규칙·스킬·서브에이전트 파일. 체크아웃 기준
    # skill = "tidy-checkouts"       skill 이면 선택. 실험군 회차마다 이 스킬을 Skill 로 불러야 한다
    # agent = "spec-reviewer"        agent 면 반드시. 정의의 name
    # agent_tools = ["Read", "Grep", "Glob", "Bash"]   agent 면 반드시. 정의의 tools 줄

    [[arm]]
    name = "실험군"                  # 출력 파일 이름의 머리
    role = "experiment"              # experiment, control
    checkout = "."                   # 선택. 기본 "."
    target = "tools/hook_env_read.py"   # rule 이면 반드시, skill·agent 면 쓰지 않는다
    # runs = 3                       선택. 기본은 실험군 3, 대조군 1

    [[arm]]
    name = "대조군"
    role = "control"
    target = "README.md"             # 규칙의 paths 밖 파일

agent 명세의 질문은 본 세션에게 그 서브에이전트를 Agent 로 한 번 부르게 하고, 서브에이전트에게는
도구를 쓰지 말고 지시문의 자리를 옮기게 하며, 그 답을 그대로 전하게 한다. 본 세션의 도구는
`Agent` 에 정의의 도구를 더한 것이다. 까닭과 그 근거의 한계는 `tools_for` 에 있다.

판정. 회차마다 아래가 모두 맞아야 통과다.
- init 의 `tools` 가 그 도구(agent 면 `Agent` 와 `agent_tools`, 순서는 따지지 않는다)이고
  `mcp_servers` 가 비었다. init 은 `Agent` 를 옛 이름 `Task` 로 찍어 같은 것으로 읽는다.
- 읽는 이벤트(system, assistant, user, result)의 모양이 예상과 같다. 어긋난 줄은 사실로 쓰지 않고
  실패로 본다. 건너뛰면 대상 밖 Read 를 놓쳐 거짓 통과가 날 수 있다(PR #157 리뷰).
- `result` 가 성공이고 `claude` 가 0 으로 끝났다. 회차마다 제한 시간(600초)을 넘기면 종료
  코드 124 다.
- rule: Read 를 한 번 이상 불렀고 모두 `<체크아웃>/<target>` 이다. 다른 파일(특히 규칙 파일)을
  읽었으면 답이 실린 규칙이 아니라 그 파일에서 왔을 수 있다.
- skill: 실린 스킬 본문의 자리(`Base directory for this skill:` 줄)는 모두 `<체크아웃>/.claude/
  skills/` 바로 아래다. 워크트리는 주 체크아웃 안에 있어 접두사가 아니라 자리 전체로 견준다.
  `skill` 을 주었으면 실험군은 그 스킬을 Skill 로 불렀고 그 이름의 자리 줄이 있다. 줄이 없으면
  자리 판정이 비므로 실패다. 대조군에는 요구하지 않는다. 새 스킬은 옛 사본에 없다.
- agent: 본 세션은 그 에이전트를 부르는 Agent 밖의 도구를 쓰지 않았다. 본 세션과 다른
  서브에이전트(Explore 등)도 정의의 도구를 가지므로, 정의를 직접 읽거나 다른 서브에이전트에게 읽혀
  옮긴 답을 이것이 막는다. 서브에이전트(`parent_tool_use_id` 가 붙은 assistant 이벤트, 앞쪽 실행이면
  결과의 `totalToolUseCount`)는 도구를 부르지 않았다. 실험군과 사본에 그 정의(`source`)가 있는
  대조군은 init 의 `agents` 에 그 에이전트가 있다. 그 둘과 init 에 그 에이전트가 실린 대조군은 그
  에이전트를 한 번 불렀고 서브에이전트가 돈 근거가 있다. 근거는 띄운 방식마다 다르다
  (`_agent_reasons`). 근거가 없으면 도구 판정이 비어 통과하므로 실패다. 넘긴 프롬프트는 거부된
  회차에도 `parent_tool_use_id` 를 단 user 이벤트로 찍혀 근거로 세지 않는다. 사본에 정의가 없는
  대조군(새 에이전트)은 부르지 않아도 된다.
- 실험군: 답이 "없음"이 아니고 카나리아를 모두 담았다. "없음"은 바뀐 본문이 실리지 않았다는 뜻이고,
  대조군과 같은 답이면 확인이 빈 것이지 통과가 아니다. 결과 이벤트가 둘이면(백그라운드로 띄운
  서브에이전트가 끝난 뒤 본 세션이 다시 답한다) 답은 마지막 것이다.
- 대조군: 답에 카나리아가 하나도 없다. "없음"이든 옛 줄이든 된다. 카나리아가 있으면 질문이 답을
  흘렸거나 대조군이 새 사본이다.
카나리아 대조는 백틱과 `*` 를 걷고 공백을 하나로 모은 뒤의 부분 문자열이다. 돌리기 전에 아래를 보고
어긋나면 돌리지 않는다. 질문과 rule 갈래의 대상 파일에 카나리아가 없다. 갈래의 체크아웃이 있다.
실험군 사본의 원천(`source`)에 카나리아가 모두 있고, 실험군과 체크아웃이 다른 대조군 사본에는 하나도
없다(대기열 133). 원천에 없는 것을 물으면 맞는 답 "없음"을 실패로 잘못 읽는다. agent 명세면 실험군
사본의 정의가 `name` 과 `tools` 줄로 명세와 맞는다(`agent_problems`). 갈래 세션에 함께 실리는
상위 폴더의 `CLAUDE.md` 에 카나리아가 없다(`ancestor_problems`, 대기열 171).

모델이 부르지 못하는 스킬(`disable-model-invocation: true`)은 질문 머리에 슬래시 명령으로 넣고
`skill` 을 주지 않는다. 그 본문은 프롬프트에 펼쳐져 Skill 호출도 자리 줄도 남기지 않는다
(claude 2.1.291 에서 `/grill-me` 로 손으로 봤다, 일지 2026-10-07-02).

못 보는 것.
- 규칙이 실렸다는 흔적은 stream-json 에 없다(claude 2.1.291 에서 손으로 봤다, 일지
  2026-10-07-02). 규칙은 답의 카나리아와 Read 호출로만 본다.
- 슬래시 명령으로 넣은 스킬이 어느 체크아웃의 사본인지. 세션을 시작한 체크아웃의 사본이 실린다는
  `operations.md` 항목에 기댄다.
- skill 의 답이 스킬 본문이 아니라 목록의 설명에서 왔는지는 `skill` 로 호출을 요구할 때만 가른다.
  설명에도 있는 낱말을 카나리아로 고르면 가르지 못한다.
- 질문이 카나리아를 바꿔 말해 드러냈는지. 글자 그대로 든 것만 명세 오류로 잡고, 나머지는 대조군이
  잡는다(대조군 답에 카나리아가 있으면 실패).
- Read 의 결과가 오류였는지. 돌리기 전에 대상 파일이 있는지만 본다.
- 카나리아가 원천의 어느 자리에 있는지. 원천 확인은 파일 전체의 부분 문자열이라, 질문이 묻는
  자리(절, 칸)에는 없고 다른 절에만 있어도 실험군 확인을 지난다. 대조군 사본은 다른 절에 같은
  낱말만 있어도 막힌다. 카나리아는 바뀐 본문에만 있는 글로 고른다.
- 서브에이전트 정의가 어느 체크아웃의 사본인지. init 의 `agents` 는 이름만 싣는다. 세션을 시작한
  체크아웃의 사본이 실린다고 보고, 대조군의 옛 답으로 가른다.
- 본 세션이 서브에이전트의 답을 고치지 않고 전했는지. 앞쪽 실행이면 서브에이전트의 마지막 답이
  stream-json 에 없어 본 세션의 답만 본다.
- agent 의 답이 정의 본문이 아니라 본 세션의 Agent 도구 설명에 실린 `description` 에서 왔는지.
  `description` 에도 있는 낱말을 카나리아로 고르면 가르지 못한다.
- 상위 폴더 P 의 `P/CLAUDE.local.md` 와 `P/.claude/CLAUDE.md`. 실리는지 재지 않아 보지 않는다. 다만
  체크아웃이 `P/.claude/` 안에 있으면(이 저장소의 워크트리) `P/.claude/` 도 상위 폴더라 그
  `CLAUDE.md` 는 본다.

종료 코드: 0 모두 통과, 1 실패한 회차가 있다, 2 명세나 인자가 틀렸다(아무것도 돌리지 않았다),
3 `claude` 를 띄우지 못했거나 출력 디렉터리를 만들지 못했거나 원본을 쓰지 못했다.
"""

from __future__ import annotations

import io
import json
import os
import re
import shutil
import subprocess
import sys
import tomllib
from collections.abc import Callable, Iterable, Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, TypedDict

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError, model_validator

type Kind = Literal["rule", "skill", "agent"]
type Role = Literal["experiment", "control"]

_TOOLS: dict[Kind, str] = {"rule": "Read", "skill": "Skill", "agent": "Agent"}
_DEFAULT_RUNS: dict[Role, int] = {"experiment": 3, "control": 1}
_ROLE_NAMES: dict[Role, str] = {"experiment": "실험군", "control": "대조군"}
_SKILL_DIR = re.compile(r"^Base directory for this skill:\s*(.+?)\s*$", re.MULTILINE)
_NONE_NOISE = re.compile(r"[\s`*_\"'“”‘’.。!]")
_ANSWER_WIDTH = 160
_TIMEOUT_SECONDS = 600.0  # 회차 하나의 제한 시간
_TIMED_OUT = 124  # GNU timeout 의 관례


class SpecError(Exception):
    """명세를 읽지 못했거나 틀렸다. 아무 회차도 돌리기 전에 난다."""


class _Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class Arm(_Model):
    name: str = Field(pattern=r"^[^/\\:]+$")
    role: Role
    checkout: str = "."
    target: str | None = None
    runs: int | None = Field(default=None, ge=1)

    @property
    def times(self) -> int:
        return self.runs if self.runs is not None else _DEFAULT_RUNS[self.role]


class Spec(_Model):
    kind: Kind
    model: str = "sonnet"
    question: str = Field(min_length=1)
    expect: list[str] = Field(min_length=1)
    source: str = Field(min_length=1)
    skill: str | None = None
    agent: str | None = None
    agent_tools: list[str] | None = None
    arm: list[Arm] = Field(min_length=1)

    @model_validator(mode="after")
    def _consistent(self) -> Spec:
        problems: list[str] = []
        if any(not canary.strip() for canary in self.expect):
            problems.append("expect 에 빈 카나리아가 있다")
        shown = [c for c in self.expect if c.strip() and _flat(c) in _flat(self.question)]
        if shown:
            problems.append(f"question 이 카나리아를 드러낸다: {', '.join(shown)}")
        roles = {arm.role for arm in self.arm}
        if roles != {"experiment", "control"}:
            problems.append("실험군과 대조군이 하나 이상씩 있어야 한다")
        names = [arm.name for arm in self.arm]
        repeated = sorted({name for name in names if names.count(name) > 1})
        if repeated:
            problems.append(f"갈래 이름이 겹친다: {', '.join(repeated)}")
        if self.kind == "rule":
            if "{target}" not in self.question:
                problems.append("rule 의 question 에 {target} 자리가 없다. 읽을 파일을 알려야 한다")
            missing = [arm.name for arm in self.arm if arm.target is None]
            if missing:
                problems.append(f"rule 갈래에 target 이 없다: {', '.join(missing)}")
        else:
            extra = [arm.name for arm in self.arm if arm.target is not None]
            if extra:
                problems.append(f"{self.kind} 갈래는 target 을 쓰지 않는다: {', '.join(extra)}")
        if self.kind != "skill" and self.skill is not None:
            problems.append("skill 은 kind 가 skill 일 때만 쓴다")
        problems += self._agent_field_problems()
        if problems:
            raise ValueError("; ".join(problems))
        return self

    def _agent_field_problems(self) -> list[str]:
        if self.kind != "agent":
            if self.agent is not None or self.agent_tools is not None:
                return ["agent 와 agent_tools 는 kind 가 agent 일 때만 쓴다"]
            return []
        if not self.agent or not self.agent_tools:
            return ["agent 명세에는 agent 와 agent_tools 가 모두 있어야 한다"]
        if any(not name.strip() for name in self.agent_tools):
            return ["agent_tools 에 빈 이름이 있다"]
        if {"Agent", "Task"} & set(self.agent_tools):
            return ["agent_tools 는 정의의 도구다. 본 세션의 Agent 는 러너가 더한다"]
        return []


@dataclass(frozen=True)
class AgentOutcome:
    """본 세션이 부른 Agent 의 결과. `status` 는 결과가 글이면 `오류: <글>` 이다.

    `tool_uses` 는 결과의 `totalToolUseCount` 이고 없으면 None 이다.
    """

    agent: str
    status: str
    tool_uses: int | None


@dataclass(frozen=True)
class Facts:
    """회차 하나의 stream-json 에서 뽑은 것. init 이 없으면 `tools` 가 None 이다.

    `malformed` 는 읽는 이벤트 가운데 모양이 어긋나 사실로 쓰지 않은 줄이다. `reads`, `skills`,
    `calls` 는 본 세션의 호출이고, 서브에이전트의 것(`parent_tool_use_id` 가 붙은 이벤트)은
    `sub_turns`(assistant 이벤트 수)와 `sub_calls` 에 따로 센다. `calls` 의 Agent 는
    `Agent(<subagent_type>)` 로 적는다.
    """

    tools: tuple[str, ...] | None
    servers: tuple[str, ...]
    reads: tuple[str, ...]
    skills: tuple[str, ...]
    skill_dirs: tuple[str, ...]
    answer: str | None
    error: str | None
    malformed: tuple[str, ...] = ()
    agents: tuple[str, ...] = ()
    calls: tuple[str, ...] = ()
    sub_turns: int = 0
    sub_calls: tuple[str, ...] = ()
    outcomes: tuple[AgentOutcome, ...] = ()


@dataclass(frozen=True)
class RunResult:
    exit_code: int
    stdout: str
    stderr: str


type Runner = Callable[[Sequence[str], Path, str], RunResult]


class _Block(TypedDict, total=False):
    type: str
    id: str
    name: str
    input: dict[str, object]
    text: str
    tool_use_id: str


class _Message(TypedDict, total=False):
    content: list[_Block] | str


class _Head(TypedDict, total=False):
    type: str


class _System(TypedDict, total=False):
    subtype: str
    tools: list[str]
    mcp_servers: list[dict[str, object] | str]
    agents: list[str]


class _Turn(TypedDict, total=False):
    message: _Message
    parent_tool_use_id: str | None
    tool_use_result: object


class _AgentResult(TypedDict, total=False):
    status: str
    totalToolUseCount: int


class _Result(TypedDict, total=False):
    subtype: str
    result: str
    is_error: bool


# 읽는 종류만 그 모양을 검증한다. 다른 종류(rate_limit_event 등)는 모양이 무엇이든 건너뛴다.
# 도구 결과의 `tool_use_result` 는 본 세션이 부른 Agent 의 것만 검증한다. 다른 도구의 결과는
# 판정에 쓰지 않으므로, 모양을 재지 않은 채 검증해 규칙·스킬 회차를 어긋난 줄로 떨어뜨리지 않는다.
_HEAD = TypeAdapter(_Head)
_SYSTEM = TypeAdapter(_System)
_TURN = TypeAdapter(_Turn)
_AGENT_RESULT: TypeAdapter[_AgentResult | str] = TypeAdapter(_AgentResult | str)
_RESULT = TypeAdapter(_Result)


def load_spec(text: str) -> Spec:
    try:
        return Spec.model_validate(tomllib.loads(text))
    except (tomllib.TOMLDecodeError, ValidationError) as error:
        raise SpecError(str(error)) from error


def read_spec(path: Path) -> Spec:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise SpecError(f"{path} 를 읽지 못했다: {error}") from error
    return load_spec(text)


def tools_for(spec: Spec) -> tuple[str, ...]:
    """회차 세션의 도구. agent 는 본 세션의 Agent 에 서브에이전트 정의의 도구를 더한다.

    서브에이전트의 도구가 본 세션의 `--tools` 에 묶이기 때문이다. `--tools Agent` 하나로 좁힌 본
    세션에서는 서브에이전트가 도구 0개로 거부됐고, 정의의 도구 넷을 더하자 돌았다(claude 2.1.292
    에서 손으로 본 두 구성, 일지 2026-10-12-02). 부분집합은 재지 않았다.
    """
    return (_TOOLS[spec.kind], *(spec.agent_tools or []))


def command(spec: Spec) -> list[str]:
    """질문은 넣지 않는다. `--tools` 는 가변 인자라 뒤에 둔 질문까지 도구 이름으로 삼킨다."""
    return [
        "claude",
        "-p",
        "--setting-sources",
        "project,local",
        "--strict-mcp-config",
        "--model",
        spec.model,
        "--tools",
        ",".join(tools_for(spec)),
        "--output-format",
        "stream-json",
        "--verbose",
    ]


def prompt_for(spec: Spec, arm: Arm) -> str:
    if spec.kind == "rule" and arm.target is not None:
        return spec.question.replace("{target}", arm.target)
    return spec.question


def _json_object(line: str) -> object | None:
    """JSON 객체 줄이면 그 값. 빈 줄, 경고, 잘린 줄이면 None 이다."""
    if not line.lstrip().startswith("{"):
        return None
    try:
        value: object = json.loads(line)
    except ValueError:  # claude 가 중간에 끝나면 마지막 줄이 잘린다
        return None
    return value


def _server_name(server: dict[str, object] | str) -> str:
    if isinstance(server, str):
        return server
    name = server.get("name")
    return name if isinstance(name, str) else repr(server)


def _blocks(turn: _Turn) -> list[_Block]:
    content = turn.get("message", {}).get("content", [])
    return [] if isinstance(content, str) else content


def _where(error: ValidationError) -> str:
    first = error.errors()[0]
    return f"{'.'.join(str(part) for part in first['loc'])}: {first['msg']}"


def _canonical(name: str) -> str:
    """init 은 Agent 를 옛 이름 Task 로 찍었다(claude 2.1.292 의 원본에서 손으로 봤다, 일지
    2026-10-12-02·03). 호출 블록은 Agent 였지만 같은 것으로 읽는다."""
    return "Agent" if name == "Task" else name


def _agent_call(agent: str) -> str:
    """본 세션의 호출 목록(`Facts.calls`)에 그 에이전트를 부른 Agent 를 적는 꼴."""
    return f"Agent({agent})"


def _outcome(agent: str, value: object) -> AgentOutcome:
    """Agent 결과의 `tool_use_result`. 모양이 어긋나면 ValidationError 가 올라간다."""
    result = _AGENT_RESULT.validate_python(value)
    if isinstance(result, str):
        return AgentOutcome(agent, f"오류: {result}", None)
    return AgentOutcome(agent, result.get("status", "상태 없음"), result.get("totalToolUseCount"))


def read_facts(lines: Iterable[str]) -> Facts:
    tools: tuple[str, ...] | None = None
    servers: tuple[str, ...] = ()
    agents: tuple[str, ...] = ()
    reads: list[str] = []
    skills: list[str] = []
    skill_dirs: list[str] = []
    calls: list[str] = []
    sub_turns = 0
    sub_calls: list[str] = []
    agent_calls: dict[str, str] = {}  # 본 세션의 Agent 호출 id 에서 subagent_type 으로
    outcomes: list[AgentOutcome] = []
    answer: str | None = None
    error: str | None = None
    malformed: list[str] = []
    for number, line in enumerate(lines, 1):
        raw = _json_object(line)
        if raw is None:
            continue
        kind: str | None = None
        try:
            kind = _HEAD.validate_python(raw).get("type")
            if kind == "system":
                system = _SYSTEM.validate_python(raw)
                if system.get("subtype") == "init":
                    tools = tuple(_canonical(name) for name in system.get("tools", []))
                    servers = tuple(_server_name(s) for s in system.get("mcp_servers", []))
                    agents = tuple(system.get("agents", []))
            elif kind == "assistant":
                turn = _TURN.validate_python(raw)
                if turn.get("parent_tool_use_id"):
                    sub_turns += 1
                    sub_calls += [
                        _canonical(block.get("name", "?"))
                        for block in _blocks(turn)
                        if block.get("type") == "tool_use"
                    ]
                    continue
                for block in _blocks(turn):
                    if block.get("type") != "tool_use":
                        continue
                    name = _canonical(block.get("name", "?"))
                    arguments = block.get("input", {})
                    if name == "Agent":
                        wanted = arguments.get("subagent_type")
                        agent = wanted if isinstance(wanted, str) else repr(arguments)
                        agent_calls[block.get("id", "")] = agent
                        calls.append(_agent_call(agent))
                        continue
                    calls.append(name)
                    if name == "Read":
                        path = arguments.get("file_path")
                        reads.append(path if isinstance(path, str) else repr(arguments))
                    elif name == "Skill":
                        skill = arguments.get("skill")
                        skills.append(skill if isinstance(skill, str) else repr(arguments))
            elif kind == "user":
                turn = _TURN.validate_python(raw)
                if turn.get("parent_tool_use_id"):
                    continue
                for block in _blocks(turn):
                    if block.get("type") == "text":
                        skill_dirs.extend(_SKILL_DIR.findall(block.get("text", "")))
                    called = block.get("tool_use_id")
                    if block.get("type") == "tool_result" and called in agent_calls:
                        value = turn.get("tool_use_result")
                        outcomes.append(_outcome(agent_calls[called], value))
            elif kind == "result":
                result = _RESULT.validate_python(raw)
                subtype = result.get("subtype", "")
                text = result.get("result", "")
                if subtype == "success" and not result.get("is_error", False):
                    answer, error = text, None
                else:
                    answer, error = None, f"{subtype or '결과 없음'}: {text}"
        except ValidationError as invalid:
            malformed.append(f"{number}번째 줄({kind or '종류 없음'}) {_where(invalid)}")
    return Facts(
        tools,
        servers,
        tuple(reads),
        tuple(skills),
        tuple(skill_dirs),
        answer,
        error,
        tuple(malformed),
        agents=agents,
        calls=tuple(calls),
        sub_turns=sub_turns,
        sub_calls=tuple(sub_calls),
        outcomes=tuple(outcomes),
    )


def _flat(text: str) -> str:
    return " ".join(text.replace("`", "").replace("*", "").split())


def _says_none(answer: str) -> bool:
    return _NONE_NOISE.sub("", answer) == "없음"


def _same_place(path: str, expected: Path, checkout: Path) -> bool:
    seen = Path(path) if Path(path).is_absolute() else checkout / path
    return _place_key(seen) == _place_key(expected)


def _agent_reasons(spec: Spec, arm: Arm, facts: Facts, checkout: Path) -> list[str]:
    """에이전트 갈래의 판정. 답이 실린 정의가 아니라 파일을 읽은 데서 오는 길을 막는다.

    실험군과 사본에 그 정의가 있는 대조군은 init 의 `agents` 에 그 에이전트가 있어야 한다. 그 둘과
    init 에 그 에이전트가 실린 대조군은 본 세션이 그 에이전트를 한 번 부르고 서브에이전트가 돌아야
    한다. 새 에이전트라 옛 사본에 정의가 없는 대조군은 부르지 않아도 된다. 돈 근거는 띄운 방식마다
    다르다. 앞쪽 실행은 서브에이전트의 마지막 텍스트 답이 stream-json 에 찍히지 않아 결과의
    `status: completed` 가, 백그라운드 실행은 결과가 `async_launched` 라 서브에이전트의 assistant
    이벤트가 근거다(claude 2.1.292 에서 손으로 봤다, 일지 2026-10-12-02·03).
    """
    reasons: list[str] = []
    call = _agent_call(str(spec.agent))
    other = [name for name in facts.calls if name != call]
    if other:
        reasons.append(f"본 세션이 {spec.agent} 를 부르는 것 밖의 도구를 썼다: {', '.join(other)}")
    defined = arm.role == "experiment" or (checkout / spec.source).is_file()
    loaded = spec.agent in facts.agents
    if defined and not loaded:
        listed = ", ".join(facts.agents) or "없음"
        reasons.append(f"init 의 agents 에 {spec.agent} 가 없다: {listed}")
    if defined or loaded:
        times = facts.calls.count(call)
        if times != 1:
            reasons.append(f"본 세션이 {spec.agent} 를 한 번 부르지 않았다: {times}번")
        mine = [outcome for outcome in facts.outcomes if outcome.agent == spec.agent]
        if not any(outcome.status == "completed" for outcome in mine) and facts.sub_turns == 0:
            seen = ", ".join(outcome.status for outcome in mine) or "결과 없음"
            reasons.append(
                "서브에이전트가 돈 근거가 없다(완료한 결과도 서브에이전트의 assistant 이벤트도 "
                f"없다): {seen}"
            )
    used = [*facts.sub_calls]
    for outcome in facts.outcomes:
        if outcome.status == "completed" and outcome.tool_uses != 0:
            count = "횟수 없음" if outcome.tool_uses is None else f"{outcome.tool_uses}회"
            used.append(f"앞쪽 실행의 도구 {count}")
    if used:
        reasons.append(f"서브에이전트가 도구를 불렀다: {', '.join(used)}")
    return reasons


def judge(spec: Spec, arm: Arm, facts: Facts, checkout: Path) -> list[str]:
    """통과면 빈 목록, 아니면 실패의 이유들."""
    reasons: list[str] = []
    tools = tools_for(spec)
    if facts.tools is None:
        reasons.append("init 이벤트가 없다. 세션이 시작되지 않았다")
    elif sorted(facts.tools) != sorted(tools):
        reasons.append(f"도구가 {', '.join(tools)} 가 아니다: {', '.join(facts.tools) or '없음'}")
    if facts.servers:
        reasons.append(f"MCP 서버가 실렸다: {', '.join(facts.servers)}")
    if facts.malformed:
        reasons.append(
            "stream-json 모양이 어긋난 줄이 있어 뽑은 사실이 빠졌을 수 있다(판이 바뀌었는지 본다): "
            + "; ".join(facts.malformed[:3])
        )
    if spec.kind == "rule" and arm.target is not None:
        target = checkout / arm.target
        if not facts.reads:
            reasons.append("Read 를 부르지 않았다. 규칙이 실릴 계기가 없다")
        outside = [path for path in facts.reads if not _same_place(path, target, checkout)]
        if outside:
            reasons.append(f"{arm.target} 밖을 읽었다: {', '.join(outside)}")
    if spec.kind == "skill":
        home = checkout / ".claude" / "skills"
        foreign = [
            folder
            for folder in facts.skill_dirs
            if not _same_place(str(Path(folder).parent), home, checkout)
        ]
        if foreign:
            reasons.append(f"{checkout} 가 아닌 사본이 실렸다: {', '.join(foreign)}")
        if spec.skill is not None and arm.role == "experiment":
            if spec.skill not in facts.skills:
                reasons.append(f"스킬 {spec.skill} 을 부르지 않았다")
            if not any(Path(folder).name == spec.skill for folder in facts.skill_dirs):
                reasons.append(f"스킬 {spec.skill} 이 실린 자리 줄이 없다. 자리 판정이 빈다")
    if spec.kind == "agent":
        reasons += _agent_reasons(spec, arm, facts, checkout)
    if facts.answer is None:
        reasons.append(f"세션이 답을 내지 못했다: {facts.error or '결과 이벤트가 없다'}")
        return reasons
    answer = _flat(facts.answer)
    canaries = [_flat(canary) for canary in spec.expect]
    if arm.role == "experiment":
        if _says_none(facts.answer):
            reasons.append('실험군이 "없음"이라 답했다. 바뀐 본문이 실리지 않았다')
        else:
            missing = [canary for canary in canaries if canary not in answer]
            if missing:
                reasons.append(f"실험군 답에 카나리아가 없다: {', '.join(missing)}")
    else:
        present = [canary for canary in canaries if canary in answer]
        if present:
            reasons.append(
                f"대조군 답에 카나리아가 있다(질문이 흘렸거나 새 사본이다): {', '.join(present)}"
            )
    return reasons


def target_problems(spec: Spec, arm: Arm, checkout: Path) -> list[str]:
    """rule 갈래의 대상 파일이 없거나 카나리아를 담았으면 그 문제들. 답이 파일에서 올 수 있다."""
    if arm.target is None:
        return []
    target = checkout / arm.target
    try:
        text = _flat(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError) as error:
        return [f"{arm.name}: 대상 {target} 이 없다: {error}"]
    found = [canary for canary in spec.expect if _flat(canary) in text]
    if found:
        return [f"{arm.name}: 대상 {arm.target} 에 카나리아가 있다: {', '.join(found)}"]
    return []


def _text(data: bytes | str | None) -> str:
    if data is None:
        return ""
    return data if isinstance(data, str) else data.decode("utf-8", "replace")


def source_problems(spec: Spec, places: dict[str, Path]) -> list[str]:
    """원천(바뀐 규칙·스킬·서브에이전트 파일)의 사본이 갈래와 맞지 않으면 그 문제들.

    실험군 사본에는 카나리아가 모두 있어야 한다. 원천에 없는 것을 물으면 맞는 답 "없음"을 실패로
    읽는다(대기열 133). 대조군 사본에는 하나도 없어야 한다. 있으면 그 대조군이 새 사본이거나,
    카나리아가 바뀐 본문에만 있는 글이 아니다(옛 사본의 다른 절에 같은 낱말이 있다). 대조군 사본에
    파일이 없으면 새 규칙·스킬·서브에이전트라 괜찮다. rule 명세에서 실험군과 같은 체크아웃의
    대조군은 `paths` 밖 파일을 읽는 갈래이고 사본이 같으니 원천을 읽지 않는다. skill·agent 명세에는
    이 면제가 없다.
    """
    fresh = {_place_key(places[arm.name]) for arm in spec.arm if arm.role == "experiment"}
    problems: list[str] = []
    for arm in spec.arm:
        checkout = places[arm.name]
        if not checkout.is_dir():
            continue  # `_preflight` 가 따로 알린다
        if arm.role == "control" and spec.kind == "rule" and _place_key(checkout) in fresh:
            continue
        path = checkout / spec.source
        try:
            text = _flat(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            if arm.role == "experiment":
                problems.append(f"{arm.name}: 원천 {path} 이 없다")
            continue
        except (OSError, UnicodeDecodeError) as error:
            problems.append(f"{arm.name}: 원천 {path} 을 읽지 못했다: {error}")
            continue
        if arm.role == "experiment":
            missing = [canary for canary in spec.expect if _flat(canary) not in text]
            if missing:
                problems.append(
                    f"{arm.name}: 원천 {spec.source} 에 카나리아가 없다: {', '.join(missing)}"
                )
        else:
            present = [canary for canary in spec.expect if _flat(canary) in text]
            if present:
                found = ", ".join(present)
                problems.append(
                    f"{arm.name}: 대조군 사본의 원천 {spec.source} 에 카나리아가 있다: {found}. "
                    "대조군이 새 사본이거나 카나리아가 바뀐 본문에만 있는 글이 아니다"
                )
    return problems


def _frontmatter(text: str) -> dict[str, str] | None:
    """`---` 로 둘러싼 머리말의 `키: 값` 줄. 머리말이 없거나 닫히지 않았으면 None 이다."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    fields: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            return fields
        key, colon, value = line.partition(":")
        if colon and not line[:1].isspace():
            fields[key.strip()] = value.strip()
    return None


def agent_problems(spec: Spec, places: dict[str, Path]) -> list[str]:
    """실험군 사본의 서브에이전트 정의가 명세와 맞지 않으면 그 문제들.

    정의의 `name` 이 `agent` 이고 `tools` 줄(쉼표로 가른 이름)이 `agent_tools` 와 같은 집합이어야
    한다. 어긋나면 init 의 `agents` 에 없거나 서브에이전트의 도구가 본 세션의 `--tools` 와 어긋나
    회차가 헛돈다. `tools` 줄이 없는 정의는 받지 않는다(그때 서브에이전트가 받는 도구는 재지
    않았다). 원천을 읽지 못한 것은 `source_problems` 가 알린다. 대조군 사본은 보지 않는다. 옛
    정의는 없거나 `tools` 가 달라도 되고, 정의가 있는데 실리지 않거나 돌지 않았으면 판정이 잡는다.
    """
    if spec.kind != "agent":
        return []
    wanted = sorted(spec.agent_tools or [])
    problems: list[str] = []
    for arm in spec.arm:
        if arm.role != "experiment":
            continue
        try:
            text = (places[arm.name] / spec.source).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        fields = _frontmatter(text)
        if fields is None:
            problems.append(f"{arm.name}: 원천 {spec.source} 에 `---` 로 둘러싼 머리말이 없다")
            continue
        name = fields.get("name")
        if name != spec.agent:
            problems.append(f"{arm.name}: 정의의 name 이 {spec.agent} 가 아니다: {name}")
        listed = fields.get("tools", "").split(",")
        declared = sorted(tool.strip() for tool in listed if tool.strip())
        if declared != wanted:
            problems.append(
                f"{arm.name}: 정의의 tools {declared} 가 agent_tools {wanted} 와 다르다"
            )
    return problems


def _main_worktree(checkout: Path) -> Path | None:
    """연결된 워크트리면 주 워크트리의 루트, 아니면 None.

    연결된 워크트리의 `.git` 은 `gitdir: <주>/.git/worktrees/<이름>` 한 줄인 파일이다. 모양이
    다르면(주 워크트리, 서브모듈, 별도 git 디렉터리) None 이라 상위 폴더를 모두 본다.
    """
    try:
        text = (checkout / ".git").read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None
    if not text.startswith("gitdir:"):
        return None
    gitdir = Path(text.removeprefix("gitdir:").strip())
    worktrees = Path(os.path.normpath(checkout / gitdir)).parent
    if worktrees.name != "worktrees" or worktrees.parent.name != ".git":
        return None
    return worktrees.parent.parent


def ancestor_problems(spec: Spec, places: dict[str, Path]) -> list[str]:
    """갈래 세션에 함께 실리는 상위 폴더의 `CLAUDE.md` 에 카나리아가 있으면 그 문제들(대기열 171).

    세션에는 체크아웃의 `CLAUDE.md` 와 함께 상위 폴더의 것도 실린다. git 루트에서 멈추지 않는다.
    다만 주 체크아웃 안의 연결된 워크트리에서 띄운 세션에는 워크트리에 자기 `CLAUDE.md` 가 있든
    없든 주 워크트리 루트의 것이 실리지 않았고 그 위 폴더의 것은 실렸다
    (`.scratch/harness/probes/claude_md_parent.py`, 결과는 프로브 README 의 그 행). 그래서 그 루트만
    건너뛴다. 대조군이면 답이 그 파일에서 흘러나오고, 실험군이면 통과가 체크아웃의 사본이 아니라
    그 파일에서 왔을 수 있다. 주 워크트리 루트와 워크트리 사이의 폴더(`.claude/`,
    `.claude/worktrees/`)는 재지 않아 실린다고 보고 본다.
    """
    problems: list[str] = []
    for arm in spec.arm:
        checkout = places[arm.name]
        skipped = _main_worktree(checkout)
        for parent in checkout.parents:
            path = parent / "CLAUDE.md"
            if skipped is not None and _place_key(parent) == _place_key(skipped):
                continue
            if not path.is_file():
                continue
            try:
                text = _flat(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError) as error:
                problems.append(f"{arm.name}: 상위 폴더의 {path} 를 읽지 못했다: {error}")
                continue
            found = [canary for canary in spec.expect if _flat(canary) in text]
            if found:
                problems.append(
                    f"{arm.name}: 상위 폴더의 {path} 에 카나리아가 있다: {', '.join(found)}. "
                    "그 파일도 이 갈래의 세션에 실려 답이 그 파일에서 올 수 있다"
                )
    return problems


def _place_key(path: Path | str) -> str:
    return os.path.normcase(os.path.normpath(path))


def run_claude(
    args: Sequence[str], cwd: Path, stdin: str, timeout: float = _TIMEOUT_SECONDS
) -> RunResult:
    """`claude` 를 한 번 띄운다. 제한 시간을 넘기면 그때까지의 출력과 종료 코드 124 를 돌려준다.

    멈춘 세션 하나가 나머지 회차의 원본까지 붙잡지 않게 하려는 것이다(PR #157 CodeRabbit).
    """
    executable = shutil.which(args[0]) or args[0]
    try:
        completed = subprocess.run(
            [executable, *args[1:]],
            cwd=cwd,
            input=stdin.encode("utf-8"),
            capture_output=True,
            check=False,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as expired:
        note = f"\n제한 시간 {timeout:g}초를 넘겨 끝냈다"
        return RunResult(_TIMED_OUT, _text(expired.stdout), _text(expired.stderr) + note)
    return RunResult(completed.returncode, _text(completed.stdout), _text(completed.stderr))


@dataclass(frozen=True)
class _Job:
    arm: Arm
    index: int
    checkout: Path


def _summary(facts: Facts) -> str:
    answer = " ".join((facts.answer or facts.error or "").split())
    if len(answer) > _ANSWER_WIDTH:
        answer = answer[:_ANSWER_WIDTH] + "…"
    reads = ", ".join(Path(path).name for path in facts.reads) or "-"
    skills = ", ".join(facts.skills) or "-"
    tools = ", ".join(facts.tools) if facts.tools is not None else "init 없음"
    agent = ""
    if facts.outcomes or facts.sub_turns:
        seen = ", ".join(f"{outcome.agent} {outcome.status}" for outcome in facts.outcomes)
        agent = f" · 서브에이전트 {seen or '결과 없음'}, {facts.sub_turns}턴"
    return (
        f"도구 {tools} · 서버 {len(facts.servers)} · 읽음 {reads} · 스킬 {skills}"
        f" · 호출 {', '.join(facts.calls) or '-'}{agent} · 답: {answer}"
    )


def _preflight(spec: Spec, places: dict[str, Path]) -> list[str]:
    """돌리기 전에 막을 문제들. 갈래의 체크아웃이 없거나, rule 갈래의 대상 파일이 어긋났거나,
    원천 사본이 갈래와 맞지 않거나, 실험군의 서브에이전트 정의가 명세와 다르거나, 상위 폴더의
    `CLAUDE.md` 에 카나리아가 있다."""
    problems = [
        f"{arm.name}: 체크아웃 {places[arm.name]} 이 없다"
        for arm in spec.arm
        if not places[arm.name].is_dir()
    ]
    problems += [
        problem for arm in spec.arm for problem in target_problems(spec, arm, places[arm.name])
    ]
    problems += source_problems(spec, places)
    problems += agent_problems(spec, places)
    return problems + ancestor_problems(spec, places)


def _run_all(spec: Spec, jobs: Sequence[_Job], runner: Runner) -> list[RunResult]:
    """회차를 나란히 돌린다. `claude` 를 띄우지 못하면 OSError 가 그대로 올라온다."""
    args = command(spec)

    def run(job: _Job) -> RunResult:
        return runner(args, job.checkout, prompt_for(spec, job.arm))

    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        return list(pool.map(run, jobs))


def _verdict(spec: Spec, job: _Job, result: RunResult) -> tuple[Facts, list[str]]:
    """회차 하나의 사실과 실패 이유. 이유가 비면 통과다."""
    facts = read_facts(result.stdout.splitlines())
    reasons = judge(spec, job.arm, facts, job.checkout)
    if result.exit_code != 0:
        last = (result.stderr.strip().splitlines() or ["stderr 없음"])[-1]
        reasons.append(f"claude 가 종료 코드 {result.exit_code} 로 끝났다: {last}")
    return facts, reasons


def _record(
    job: _Job,
    result: RunResult,
    verdict: tuple[Facts, list[str]],
    output: Path,
    out: Callable[[str], None],
) -> None:
    """회차 하나의 원본을 남기고 판정을 찍는다."""
    facts, reasons = verdict
    stem = f"{job.arm.name}-{job.index}"
    (output / f"{stem}.jsonl").write_text(result.stdout, encoding="utf-8")
    (output / f"{stem}.err").write_text(result.stderr, encoding="utf-8")
    label = f"{job.arm.name}({_ROLE_NAMES[job.arm.role]}) {job.index}/{job.arm.times}"
    out(f"[{'실패' if reasons else '통과'}] {label}")
    for reason in reasons:
        out(f"  - {reason}")
    out(f"  {_summary(facts)}")


def main(
    argv: Sequence[str],
    *,
    cwd: Path | None = None,
    runner: Runner = run_claude,
    out: Callable[[str], None] = print,
) -> int:
    if len(argv) != 2:
        out(__doc__ or "")
        return 2
    base = cwd if cwd is not None else Path.cwd()
    try:
        spec = read_spec(Path(argv[0]))
    except SpecError as error:
        out(f"명세 오류(아무것도 돌리지 않았다): {error}")
        return 2
    output = Path(argv[1])
    places = {arm.name: Path(os.path.abspath(base / arm.checkout)) for arm in spec.arm}
    jobs = [
        _Job(arm, index, places[arm.name]) for arm in spec.arm for index in range(1, arm.times + 1)
    ]
    problems = _preflight(spec, places)
    if problems:
        out("명세 오류(아무것도 돌리지 않았다):")
        for problem in problems:
            out(f"  {problem}")
        return 2
    try:
        output.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        out(f"출력 디렉터리를 만들지 못했다(아무것도 돌리지 않았다): {error}")
        return 3
    try:
        results = _run_all(spec, jobs, runner)
    except OSError as error:
        out(f"claude 를 띄우지 못했다(원본을 남기지 않았다): {error}")
        return 3
    verdicts = [_verdict(spec, job, result) for job, result in zip(jobs, results, strict=True)]
    try:
        for job, result, verdict in zip(jobs, results, verdicts, strict=True):
            _record(job, result, verdict, output, out)
    except OSError as error:
        out(f"원본을 쓰지 못했다(판정을 끝까지 찍지 못했다): {error}")
        return 3
    failed = sum(1 for _, reasons in verdicts if reasons)
    out(f"통과 {len(jobs) - failed} · 실패 {failed}. 원본은 {output}")
    return 1 if failed else 0


if __name__ == "__main__":
    # 윈도우의 파이프는 PYTHONUTF8 이 없으면 cp949 다. 한글 출력이 깨지지 않게 고정한다.
    stream = sys.stdout
    if isinstance(stream, io.TextIOWrapper):
        stream.reconfigure(encoding="utf-8")
    raise SystemExit(main(sys.argv[1:]))
