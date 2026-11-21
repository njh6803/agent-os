"""쉬운 말 규칙이 든 두 자리(사용자 출력 스타일, 프로젝트 `CLAUDE.md`)가 새 `claude -p` 세션과
그 서브에이전트의 컨텍스트에 실리는지 잰다.

harness 티켓 `plain-words-in-written-artifacts` 의 전제다. 쉬운 말 규칙은 두 자리에 있다. 사용자
출력 스타일 `~/.claude/output-styles/fluent-korean-explanatory.md`(사용자 설정의 `outputStyle` 이
고른다. 저장소 밖이다)의 한 줄과, 이 저장소 `CLAUDE.md` 원칙 절의 "사람에게 보이는 글" 항목이다.
두 자리의 글에만 있는 낱말(카나리아)을 정해 두고, 세션에게 도구 없이 컨텍스트에 실린 그 문장을
글자 그대로 옮기게 한다. 물음에는 카나리아가 없다.

갈래. 모두 이 프로브를 부른 폴더(저장소나 워크트리의 루트)에서 띄운다.
- `p-기본`: `claude -p` 를 설정 원천을 좁히지 않고 띄운다(사용자·프로젝트·로컬 설정이 모두 든다).
- `p-프로젝트만`: `--setting-sources project,local`. 사용자 설정이 빠지므로 출력 스타일의
  대조군이다. `tools/canary.py` 가 띄우는 모양이다.
- `sub-<이름>`: `p-기본` 모양의 본 세션이 그 서브에이전트를 Agent 로 한 번 부르고, 서브에이전트가
  같은 물음에 답한다. 판정은 본 세션의 말이 아니라 서브에이전트가 낸 보고로 한다.
  `general-purpose`, `Explore`, 이 저장소가 정의한 `spec-reviewer` 다.

원본에서 본 이벤트의 모양(claude 2.1.325, 첫 실행의 원본을 열어 봤다). init 이벤트의
`output_style` 이 그 세션이 고른 출력 스타일의 이름이다. 서브에이전트는 답을 글로 내지 않고
`SubagentHandback` 도구를 불러 `message` 에 싣고(그 assistant 이벤트에 `parent_tool_use_id` 가
붙는다), 본 세션의 Agent 도구 결과에는 답이 없이 "보고가 메시지로 전해졌다"는 문구만 온다. 같은
이벤트의 `tool_use_result` 가 `status`, `handbackReport.text`(서브에이전트의 답), `toolsUsed` 를
든다.

표지(측정인 회차). 결과 이벤트가 성공이고, 답하는 쪽(p 갈래는 본 세션, sub 갈래는 서브에이전트)이
도구를 부르지 않았다(서브에이전트가 보고를 내는 `SubagentHandback` 은 뺀다). 도구를 불렀으면 답이
파일을 읽은 데서 왔을 수 있다. sub 갈래는 그에 더해 본 세션이 Agent 를 한 번만 불렀고 다른 도구를
쓰지 않았으며, 그 호출의 `subagent_type` 이 갈래의 서브에이전트이고(다른 종류가 불리면 그 갈래의
결과가 아니다), Agent 에 넘긴 프롬프트에 카나리아가 없고(본 세션이 자기 컨텍스트의 문장을 흘리지
않았다), 도구 결과의 `status` 가 `completed` 이고 서브에이전트의 보고가 있다.
양성 대조는 두 카나리아가 서로 맡는다. 한 회차의 답이 한 자리의 문장을 옮기고 다른 자리에는
"없음"이라 하면, 그 세션이 실린 문장을 옮긴다는 것과 물음이 답을 흘리지 않는다는 것이 함께 선다.
두 자리 모두 "없음"인 갈래는 같은 물음에 문장을 옮긴 다른 갈래가 있을 때만 읽는다. 측정인 회차
가운데 문장을 하나라도 옮긴 회차가 없으면 코드가 "양성 대조 없음"을 찍고 1 로 끝난다. 그런 결과는
물음이 문장을 옮기게 하지 못한 것이라 결론을 내지 않는다. 갈래를 골라 돌려도 같으므로, "없음"이
나올 갈래는 문장을 옮길 갈래와 함께 돌린다. 어느 갈래의 "없음"을 어느 갈래의 옮김이 받치는지는
읽는 쪽이 본다.

못 보는 것.
- 데스크톱 앱이 띄운 대화 세션. 이 프로브는 `claude -p` 만 띄운다. 앱 세션 안에서 돌리면 띄운
  세션이 부모의 환경 변수(`CLAUDE_CODE_ENTRYPOINT` 등)를 물려받는다. 그것이 출력 스타일의 로드를
  바꾸는지는 가르지 않는다.
- 실린 규칙이 글에 실제로 반영되는지. 여기서는 컨텍스트에 실렸는지만 본다. 반영은 `scope.py` 가
  잰다.
- 백그라운드로 띄운 서브에이전트. 물음이 앞쪽 실행을 시킨다. 도구 결과의 `status` 가 `completed`
  가 아니면 측정이 아니다.
- 서브에이전트가 받는 것 가운데 출력 스타일의 일부만 실리는 경우. 판정은 카나리아 한 문장과 스타일
  이름으로만 한다.

돌리는 법: 저장소(워크트리) 루트에서
`uv run python .scratch/harness/probes/plain_words_reach/loading.py <출력 디렉터리> [갈래 ...]`.
갈래 이름을 주면 그 갈래만 돈다. `claude` CLI 와 인증이 들고, 사용자 설정이 그 출력 스타일을 골라
둔 PC 여야 한다(아니면 2 로 끝난다). 회차는 일곱이고 본 세션은 모두 sonnet 이다(서브에이전트가 도는
모델은 그 정의가 정하고 여기서 보지 않는다). 회차마다 stream-json 원본을
출력 디렉터리에 남긴다. 종료 코드: 0 모든 회차가 측정이고 문장을 옮긴 회차가 있다, 1 측정이 아닌
회차가 있거나 문장을 옮긴 회차가 없다, 2 카나리아가 원천에 없거나 물음에 있다.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from tools.probe_kit import Rounds  # noqa: E402

STYLE_NAME = "fluent-korean-explanatory"
STYLE_FILE = Path.home() / ".claude" / "output-styles" / f"{STYLE_NAME}.md"
STYLE_CANARY = "흔히 쓰는 용어"
PROJECT_CANARY = "구체적인 장면"
QUESTION = (
    "도구를 하나도 쓰지 마라. 파일을 읽지 말고, 이 세션의 컨텍스트에 이미 실린 것만 보고 답한다.\n"
    "1) 시스템 프롬프트에 출력 스타일(Output Style) 지침이 실려 있으면 그 스타일의 이름과, 그 "
    '지침에서 "낯선"이라는 낱말이 든 문장 하나를 글자 그대로 옮겨라. 실려 있지 않으면 '
    '"1) 없음"이라고만 적는다.\n'
    '2) 실린 프로젝트 지시(CLAUDE.md)의 "원칙" 절에서 "사람에게 보이는 글"로 시작하는 항목을 '
    '글자 그대로 옮겨라. 실려 있지 않으면 "2) 없음"이라고만 적는다.\n'
)
DELEGATE = (
    "Agent 도구로 `{agent}` 서브에이전트를 한 번만 불러라(subagent_type 은 `{agent}`, 백그라운드가 "
    "아니라 앞쪽 실행). 다른 도구는 쓰지 않는다. 서브에이전트에게 넘길 프롬프트는 아래 두 줄 "
    "사이의 글을 글자 그대로 쓰고 한 글자도 더하거나 빼지 않는다.\n"
    "-----\n{question}-----\n"
    "서브에이전트의 답을 받으면 그 답만 글자 그대로 전하라.\n"
)
BASE = ["claude", "-p", "--strict-mcp-config", "--model", "sonnet"]
TAIL = ["--output-format", "stream-json", "--verbose"]
SUB_TOOLS = "Agent,Read,Grep,Glob,Bash"
HANDBACK = "SubagentHandback"
TIMEOUT = 600


@dataclass(frozen=True)
class Arm:
    name: str
    runs: int
    agent: str | None = None
    project_only: bool = False

    def command(self) -> list[str]:
        sources = ["--setting-sources", "project,local"] if self.project_only else []
        tools = SUB_TOOLS if self.agent else "Read"
        return [*BASE, *sources, "--tools", tools, *TAIL]

    def prompt(self) -> str:
        if self.agent is None:
            return QUESTION
        return DELEGATE.format(agent=self.agent, question=QUESTION)


ARMS = [
    Arm("p-기본", 2),
    Arm("p-프로젝트만", 1, project_only=True),
    Arm("sub-general-purpose", 2, agent="general-purpose"),
    Arm("sub-Explore", 1, agent="Explore"),
    Arm("sub-spec-reviewer", 1, agent="spec-reviewer"),
]


def clean_env() -> dict[str, str]:
    """pre-commit 아래에서 불려도 이 저장소를 가리키는 `GIT_*` 가 띄운 세션에 닿지 않게 벗긴다."""
    return {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}


def run(arm: Arm, cwd: Path) -> str:
    """회차 하나의 stream-json. 제한 시간을 넘기면 그때까지의 출력이고, 세션을 띄우지 못하면 그
    까닭 한 줄이다. 둘 다 결과 이벤트가 없어 측정이 아니다. 예외를 밖으로 던지지 않아야 함께 띄운
    다른 회차의 원본이 남는다."""
    executable = shutil.which(BASE[0]) or BASE[0]
    try:
        done = subprocess.run(
            [executable, *arm.command()[1:]],
            cwd=cwd,
            input=arm.prompt().encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=TIMEOUT,
            env=clean_env(),
        )
    except subprocess.TimeoutExpired as expired:
        return (expired.stdout or b"").decode("utf-8", errors="replace")
    except OSError as error:
        return f"세션을 띄우지 못했다: {error}\n"
    return done.stdout.decode("utf-8", errors="replace")


def events(raw: str) -> list[dict[str, object]]:
    found: list[dict[str, object]] = []
    for line in raw.splitlines():
        if not line.lstrip().startswith("{"):
            continue
        try:
            event = json.loads(line)
        except ValueError:  # 제한 시간에 끊기면 마지막 줄이 잘린다
            continue
        if isinstance(event, dict):
            found.append(event)
    return found


def blocks(event: dict[str, object]) -> list[dict[str, object]]:
    message = event.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, list):
        return []
    return [block for block in content if isinstance(block, dict)]


@dataclass
class Outcome:
    """Agent 도구 결과 하나. `report` 는 서브에이전트가 낸 보고의 글이고 없으면 None 이다."""

    status: object
    report: str | None
    tools_used: list[str]


@dataclass
class Facts:
    style: object = None
    answer: str | None = None
    main_calls: list[str] = field(default_factory=list)
    sub_calls: list[str] = field(default_factory=list)
    agent_prompts: list[str] = field(default_factory=list)
    agent_types: list[str] = field(default_factory=list)
    outcomes: list[Outcome] = field(default_factory=list)


def outcome_of(detail: object) -> Outcome:
    if not isinstance(detail, dict):
        return Outcome(None, None, [])
    handback = detail.get("handbackReport")
    text = handback.get("text") if isinstance(handback, dict) else None
    used = detail.get("toolsUsed")
    names = [str(name) for name in used] if isinstance(used, list) else []
    return Outcome(detail.get("status"), text if isinstance(text, str) else None, names)


def facts(raw: str) -> Facts:
    """init 의 출력 스타일, 본 세션과 서브에이전트의 도구 호출, Agent 에 넘긴 프롬프트와 부른
    서브에이전트의 종류, Agent 도구 결과의 상세(서브에이전트의 보고), 성공한 결과의 답."""
    out = Facts()
    agent_ids: set[object] = set()
    for event in events(raw):
        kind = event.get("type")
        parent = event.get("parent_tool_use_id")
        if kind == "system" and event.get("subtype") == "init":
            out.style = event.get("output_style")
        if kind == "assistant":
            for block in blocks(event):
                if block.get("type") != "tool_use":
                    continue
                name = str(block.get("name"))
                if parent is not None:
                    out.sub_calls.append(name)
                    continue
                out.main_calls.append(name)
                if name in ("Agent", "Task"):
                    agent_ids.add(block.get("id"))
                    given = block.get("input")
                    prompt = given.get("prompt") if isinstance(given, dict) else None
                    called = given.get("subagent_type") if isinstance(given, dict) else None
                    out.agent_prompts.append(str(prompt))
                    out.agent_types.append(str(called))
        if kind == "user" and parent is None:
            for block in blocks(event):
                if block.get("type") == "tool_result" and block.get("tool_use_id") in agent_ids:
                    out.outcomes.append(outcome_of(event.get("tool_use_result")))
        if kind == "result":
            ok = event.get("subtype") == "success" and not event.get("is_error")
            result = event.get("result")
            out.answer = result if ok and isinstance(result, str) else None
    return out


def judge(arm: Arm, found: Facts) -> tuple[bool, str, str]:
    """(측정인가, 결과 또는 측정이 아닌 까닭, 판정에 쓴 답)."""
    if found.answer is None:
        return False, "성공한 결과 이벤트가 없다", ""
    if arm.agent is None:
        if found.main_calls:
            return False, f"본 세션이 도구를 불렀다: {found.main_calls}", found.answer
        subject = found.answer
    else:
        if found.main_calls not in (["Agent"], ["Task"]):
            return False, f"본 세션의 도구 호출이 Agent 한 번이 아니다: {found.main_calls}", ""
        if found.agent_types != [arm.agent]:
            return False, f"부른 서브에이전트가 {arm.agent} 가 아니다: {found.agent_types}", ""
        leaked = [c for c in (STYLE_CANARY, PROJECT_CANARY) if c in found.agent_prompts[0]]
        if leaked:
            return False, f"Agent 에 넘긴 프롬프트에 카나리아가 있다: {leaked}", ""
        if len(found.outcomes) != 1:
            return False, f"Agent 도구 결과가 하나가 아니다: {len(found.outcomes)}", ""
        outcome = found.outcomes[0]
        if outcome.status != "completed" or outcome.report is None:
            return False, f"끝난 서브에이전트의 보고가 없다: status={outcome.status}", ""
        subject = outcome.report
        used = [name for name in (*found.sub_calls, *outcome.tools_used) if name != HANDBACK]
        if used:
            return False, f"서브에이전트가 도구를 불렀다: {used}", subject
    style = STYLE_CANARY in subject
    name = STYLE_NAME in subject
    project = PROJECT_CANARY in subject
    result = (
        f"init 의 출력 스타일 {found.style} · 답에 출력 스타일 {'실림' if style else '없음'}"
        f"(이름 {'있음' if name else '없음'}) · 답에 CLAUDE.md {'실림' if project else '없음'}"
    )
    return True, result, subject


def copied(subject: str) -> bool:
    """답이 두 자리 가운데 한 자리의 문장이라도 옮겼는가. 양성 대조가 되는 회차다."""
    return STYLE_CANARY in subject or PROJECT_CANARY in subject


def preflight(cwd: Path) -> list[str]:
    problems: list[str] = []
    for canary in (STYLE_CANARY, PROJECT_CANARY, STYLE_NAME):
        if canary in QUESTION:
            problems.append(f"물음에 카나리아가 있다: {canary}")
    try:
        style = STYLE_FILE.read_text(encoding="utf-8")
    except OSError as error:
        problems.append(f"출력 스타일 파일을 읽지 못했다: {error}")
    else:
        if STYLE_CANARY not in style:  # 빈 파일도 여기서 걸린다
            problems.append(f"출력 스타일 파일에 카나리아가 없다: {STYLE_CANARY}")
    try:
        project = (cwd / "CLAUDE.md").read_text(encoding="utf-8")
    except OSError as error:
        problems.append(f"CLAUDE.md 를 읽지 못했다: {error}")
    else:
        if PROJECT_CANARY not in project:  # 빈 파일도 여기서 걸린다
            problems.append(f"CLAUDE.md 에 카나리아가 없다: {PROJECT_CANARY}")
    return problems


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 2
    out = Path(argv[0])
    wanted = set(argv[1:])
    arms = [arm for arm in ARMS if not wanted or arm.name in wanted]
    cwd = Path.cwd()
    problems = preflight(cwd)
    if problems or not arms:
        print("돌리지 않는다:", *(problems or ["그런 갈래가 없다"]), sep="\n  ")
        return 2
    out.mkdir(parents=True, exist_ok=True)
    jobs = [(arm, index) for arm in arms for index in range(1, arm.runs + 1)]
    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        raws = list(pool.map(lambda job: run(job[0], cwd), jobs))
    rounds = Rounds()
    controls = 0
    for (arm, index), raw in zip(jobs, raws, strict=True):
        label = f"{arm.name}-{index}"
        (out / f"{label}.jsonl").write_text(raw, encoding="utf-8", newline="\n")
        with rounds.round(label) as current:
            measured, result, subject = judge(arm, facts(raw))
            current.mark(measured=measured, result=f"{arm.name}: {result}" if measured else result)
            controls += measured and copied(subject)
            print(f"[{'측정' if measured else '측정 아님'}] {label} · {result}")
            for line in subject.splitlines():
                print(f"    {line}")
    print(rounds.summary())
    if not controls:
        print("양성 대조 없음: 측정인 회차 가운데 문장을 옮긴 회차가 없다. 결론을 내지 않는다.")
        return 1
    return rounds.exit_code()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
