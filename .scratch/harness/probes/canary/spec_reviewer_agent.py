"""spec-reviewer 정의에 더한 세 문장(대기열 106·121·125)이 새 세션의 서브에이전트에
실리는지.

`tools/canary.py` 에 에이전트 갈래가 없어(대기열 153) 같은 판정을 손으로 옮겼다.
명령의 모양은 그 도구와 같고(`--setting-sources project,local --strict-mcp-config
--model sonnet`), 도구는 `Agent` 하나로 좁힌다. 실험군은 이 스크립트가 있는
체크아웃에서 셋, 대조군은 인자로 받은 체크아웃(바뀌기 전 사본)에서 하나다.

회차마다 아래가 모두 맞아야 통과다.
- init 의 `agents` 에 spec-reviewer 가 있다.
- 본 세션이 Agent 도구로 `subagent_type: spec-reviewer` 를 불렀다.
- 서브에이전트가 도구를 하나도 부르지 않았다. 파일을 읽어 옮긴 답이면 정의가
  실렸다는 증거가 못 된다.
- 실험군은 답에 카나리아 셋이 모두 있고, 대조군은 하나도 없다.

사용:
    uv run python .scratch/harness/probes/canary/spec_reviewer_agent.py \\
        <대조군 체크아웃> <출력 디렉터리>
종료 코드: 0 모두 통과, 1 실패한 회차가 있다.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path

CHECKOUT = Path(__file__).resolve().parents[4]
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


def judge(raw: str, experiment: bool) -> list[str]:
    reasons: list[str] = []
    agents: list[str] = []
    called = False
    sub_tools: list[str] = []
    answer = ""
    for line in raw.splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        if event.get("type") == "system" and event.get("subtype") == "init":
            agents = [str(name) for name in event.get("agents") or []]
        if event.get("type") == "assistant":
            for block in event["message"].get("content", []):
                if block.get("type") != "tool_use":
                    continue
                if event.get("parent_tool_use_id"):
                    sub_tools.append(str(block.get("name", "?")))
                elif block.get("input", {}).get("subagent_type") == "spec-reviewer":
                    called = True
        if event.get("type") == "result":
            answer = str(event.get("result", ""))
            if event.get("is_error"):
                reasons.append(f"결과가 오류다: {answer[:120]}")
    if "spec-reviewer" not in agents:
        reasons.append(f"init 의 agents 에 spec-reviewer 가 없다: {agents}")
    if not called:
        reasons.append("Agent 로 spec-reviewer 를 부르지 않았다")
    if sub_tools:
        reasons.append(f"서브에이전트가 도구를 불렀다: {sub_tools}")
    found = [c for c in CANARIES if norm(c) in norm(answer)]
    if experiment and len(found) != len(CANARIES):
        reasons.append(f"카나리아 {len(found)}/{len(CANARIES)}")
    if not experiment and found:
        reasons.append(f"대조군 답에 카나리아: {found}")
    return reasons


def main(control: Path, out: Path) -> int:
    out.mkdir(parents=True, exist_ok=True)
    executable = shutil.which(COMMAND[0]) or COMMAND[0]
    arms = [("실험군", CHECKOUT, True)] * 3 + [("대조군", control, False)]
    failed = 0
    for index, (name, cwd, experiment) in enumerate(arms, start=1):
        done = subprocess.run(
            [executable, *COMMAND[1:]],
            cwd=cwd,
            input=QUESTION.encode("utf-8"),
            capture_output=True,
            check=False,
            timeout=600,
        )
        raw = done.stdout.decode("utf-8", errors="replace")
        (out / f"{index}-{name}.jsonl").write_text(raw, encoding="utf-8", newline="\n")
        reasons = judge(raw, experiment)
        if done.returncode != 0:
            reasons.append(f"claude 종료 코드 {done.returncode}")
        failed += bool(reasons)
        print(f"[{'실패' if reasons else '통과'}] {index}-{name}", *reasons, sep="\n  - ")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(Path(sys.argv[1]), Path(sys.argv[2])))
