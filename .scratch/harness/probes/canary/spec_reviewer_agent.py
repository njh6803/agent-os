"""spec-reviewer 정의에 더한 세 문장(대기열 106·121·125)이 새 세션의 서브에이전트에
실리는지.

`tools/canary.py` 에 에이전트 갈래가 없어(대기열 153) 같은 판정을 손으로 옮겼다.
명령의 모양은 그 도구와 같고(`--setting-sources project,local --strict-mcp-config
--model sonnet`), 도구는 `Agent` 하나로 좁힌다. 실험군은 이 스크립트가 있는
체크아웃에서 셋, 대조군은 인자로 받은 체크아웃(바뀌기 전 사본)에서 하나다. 병합 뒤에는
주 체크아웃이 새 사본이므로 `git worktree add --detach <경로> 58969f7` 로 옛 판을
꺼내 대조군으로 준다.

돌리기 전에 실험군 사본에는 카나리아가 모두 있고 대조군 사본에는 하나도 없는지 보고,
어긋나면 아무것도 돌리지 않고 종료 2다. 회차마다 아래가 모두 맞아야 통과다.
- 모든 줄이 JSON 이다. 어긋난 줄은 사실로 쓰지 않고 실패로 본다.
- init 의 `tools` 가 `Agent` 하나이고 `mcp_servers` 가 비었고, `agents` 에 spec-reviewer
  가 있다. 본 세션이 다른 도구를 가졌으면 정의를 읽어 옮긴 답이 통과할 수 있다.
- 본 세션의 도구 호출은 Agent 뿐이고 그중 `subagent_type: spec-reviewer` 가 있다.
- 서브에이전트의 이벤트(`parent_tool_use_id` 가 붙은 것)가 하나 이상 있고, 그 가운데
  도구 호출이 없다. 서브에이전트 이벤트가 없으면 도구 판정이 비어 통과하므로 실패다.
- `claude` 가 0 으로 끝났고 결과가 오류가 아니다. 제한 시간(600초)을 넘기면 실패다.
- 실험군은 답에 카나리아 셋이 모두 있고, 대조군은 하나도 없다.

사용:
    uv run python .scratch/harness/probes/canary/spec_reviewer_agent.py \\
        <대조군 체크아웃> <출력 디렉터리>
회차마다 stream-json 원본(`.jsonl`)과 stderr(`.err`)를 남긴다.
종료 코드: 0 모두 통과, 1 실패한 회차가 있다, 2 사본이 카나리아와 맞지 않는다.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

CHECKOUT = Path(__file__).resolve().parents[4]
DEFINITION = Path(".claude") / "agents" / "spec-reviewer.md"
TIMEOUT = 600
CANARIES = [
    "지금 이음매(주입되는 포트, 시계)로 잴 수 있는지 코드로 본다",
    "그 문구가 서는 조건",
    "넘긴 것마다 지금 잴 수 없는 이유를 명세에서 찾는다",
]
INNER = (
    "도구를 하나도 쓰지 마라. 파일을 읽지 말고, 지금 네 지시문(시스템 프롬프트)에 "
    "적힌 것만 보고 답한다. 체크리스트 6번 항목의 마지막 세 문장, 체크리스트 7번 "
    "항목의 마지막 문장, 질문 1의 마지막 세 문장을 각각 글자 그대로 옮겨라. "
    "지시문에 그런 문장이 없으면 그 자리에 '없음'이라고만 적어라."
)
QUESTION = (
    "spec-reviewer 서브에이전트를 Agent 도구로 한 번만 불러라. 서브에이전트에게 줄 "
    f"프롬프트는 아래 단락 그대로다.\n\n{INNER}\n\n"
    "서브에이전트의 답을 고치거나 줄이지 말고 그대로 전하라.\n"
)
COMMAND = [
    "claude",
    "-p",
    "--setting-sources",
    "project,local",
    "--strict-mcp-config",
    "--model",
    "sonnet",
    "--tools",
    "Agent",
    "--output-format",
    "stream-json",
    "--verbose",
]


def norm(text: str) -> str:
    return " ".join(text.replace("`", "").replace("*", "").split())


def preflight(control: Path) -> list[str]:
    problems: list[str] = []
    for name, checkout, want in (("실험군", CHECKOUT, True), ("대조군", control, False)):
        path = checkout / DEFINITION
        if not path.is_file():
            problems.append(f"{name}: {path} 이 없다")
            continue
        body = norm(path.read_text(encoding="utf-8"))
        found = [c for c in CANARIES if norm(c) in body]
        if want and len(found) != len(CANARIES):
            problems.append(f"{name}: 사본에 카나리아 {len(found)}/{len(CANARIES)}")
        if not want and found:
            problems.append(f"{name}: 사본에 이미 카나리아가 있다(새 사본이다): {found}")
    return problems


def judge(raw: str, experiment: bool) -> list[str]:
    reasons: list[str] = []
    init: dict[str, object] | None = None
    main_tools: list[str] = []
    called = False
    sub_events = 0
    sub_tools: list[str] = []
    answer = ""
    for number, line in enumerate(raw.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            reasons.append(f"{number}번째 줄이 JSON 이 아니다")
            continue
        if event.get("type") == "system" and event.get("subtype") == "init":
            init = event
        if event.get("parent_tool_use_id"):
            sub_events += 1
        if event.get("type") == "assistant":
            for block in event["message"].get("content", []):
                if block.get("type") != "tool_use":
                    continue
                name = str(block.get("name", "?"))
                if event.get("parent_tool_use_id"):
                    sub_tools.append(name)
                    continue
                main_tools.append(name)
                if block.get("input", {}).get("subagent_type") == "spec-reviewer":
                    called = True
        if event.get("type") == "result":
            answer = str(event.get("result", ""))
            if event.get("is_error"):
                reasons.append(f"결과가 오류다: {answer[:120]}")
    if init is None:
        reasons.append("init 이벤트가 없다")
    else:
        if init.get("tools") != ["Agent"]:
            reasons.append(f"init 의 tools 가 Agent 하나가 아니다: {init.get('tools')}")
        if init.get("mcp_servers"):
            reasons.append(f"init 의 mcp_servers 가 비지 않았다: {init.get('mcp_servers')}")
        agents = init.get("agents")
        if not isinstance(agents, list) or "spec-reviewer" not in agents:
            reasons.append(f"init 의 agents 에 spec-reviewer 가 없다: {agents}")
    if any(name != "Agent" for name in main_tools):
        reasons.append(f"본 세션이 Agent 밖의 도구를 불렀다: {main_tools}")
    if not called:
        reasons.append("Agent 로 spec-reviewer 를 부르지 않았다")
    if sub_events == 0:
        reasons.append("서브에이전트 이벤트가 없어 도구 판정이 빈다")
    if sub_tools:
        reasons.append(f"서브에이전트가 도구를 불렀다: {sub_tools}")
    found = [c for c in CANARIES if norm(c) in norm(answer)]
    if experiment and len(found) != len(CANARIES):
        reasons.append(f"카나리아 {len(found)}/{len(CANARIES)}")
    if not experiment and found:
        reasons.append(f"대조군 답에 카나리아: {found}")
    return reasons


def run(cwd: Path) -> tuple[int | None, str, str]:
    executable = shutil.which(COMMAND[0]) or COMMAND[0]
    try:
        done = subprocess.run(
            [executable, *COMMAND[1:]],
            cwd=cwd,
            input=QUESTION.encode("utf-8"),
            capture_output=True,
            check=False,
            timeout=TIMEOUT,
        )
    except subprocess.TimeoutExpired as expired:
        out = (expired.stdout or b"").decode("utf-8", errors="replace")
        err = (expired.stderr or b"").decode("utf-8", errors="replace")
        return None, out, err + f"\n제한 시간 {TIMEOUT}초를 넘겨 끝냈다"
    out = done.stdout.decode("utf-8", errors="replace")
    return done.returncode, out, done.stderr.decode("utf-8", errors="replace")


def main(control: Path, out: Path) -> int:
    problems = preflight(control)
    if problems:
        print("사본 오류(아무것도 돌리지 않았다):", *problems, sep="\n  ")
        return 2
    out.mkdir(parents=True, exist_ok=True)
    arms = [("실험군", CHECKOUT, True)] * 3 + [("대조군", control, False)]
    failed = 0
    for index, (name, cwd, experiment) in enumerate(arms, start=1):
        code, raw, err = run(cwd)
        (out / f"{index}-{name}.jsonl").write_text(raw, encoding="utf-8", newline="\n")
        (out / f"{index}-{name}.err").write_text(err, encoding="utf-8", newline="\n")
        reasons = judge(raw, experiment)
        if code is None:
            reasons.append(f"제한 시간 {TIMEOUT}초를 넘겼다")
        elif code != 0:
            reasons.append(f"claude 종료 코드 {code}")
        failed += bool(reasons)
        print(f"[{'실패' if reasons else '통과'}] {index}-{name}", *reasons, sep="\n  - ")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]), Path(sys.argv[2])))
