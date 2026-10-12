"""`bug-perf-review` 가 백그라운드로 옮겨진 Bash 명령을 보고 전에 `TaskStop` 으로 멈추는지 잰다.

대기열 188 의 근거다. `.claude/agents/bug-perf-review.md` 보고 형식 절의 백그라운드 문단과 `tools`
줄의 `TaskStop` 이 그것에 기댄다. 일지 2026-10-12-15 의 리뷰어(세션
`98081d3c-a134-4c08-ac13-7c09286a15f9` 의 서브에이전트 기록 `agent-a99e8d7e4edecc6e0.jsonl`, 그 meta
의 `agentType` 이 `bug-perf-review`)는 `timeout: 300000` 으로 친 프로브가 300초를 넘기자 Bash 도구가
그 명령을 죽이지 않고 백그라운드(`bq0cfb3rc`)로 옮겼고, `run_in_background` 를 쓰지 않았는데 그
작업을 남긴 채 보고했다. 본 세션이 멈췄다(그 기록을 읽었다). 옛 정의의 도구(Bash, Read, Grep,
Glob)에는 `TaskStop` 이 없어 작업 ID 로 멈출 도구가 없다.

갈래 둘이다. 실험군은 이 도구를 부른 체크아웃(새 정의: 문단과 `TaskStop`), 대조군은 둘째 인자의
체크아웃이고 기본은 주 체크아웃(`../../..`)이다. 이 프로브의 PR 이 병합된 뒤에는 주 체크아웃도 새
정의라, 옛 판을 `git worktree add --detach` 로 꺼내 둘째 인자로 준다. 대조군 정의에 `TaskStop` 이
있거나 실험군 정의에 없으면 대조가 없으므로 돌리지 않고 2 로 끝난다(PR 직전 리뷰와 PR 리뷰가
짚었다). 회차마다 카나리아
명령(`--setting-sources project,local --strict-mcp-config --model sonnet`)에
`--tools Agent,Bash,Read,Grep,Glob,TaskStop` 을 주어 띄운다. 서브에이전트의 도구는 본 세션의
`--tools` 에 묶이므로(`tools/canary.py` 의 `tools_for`) 두 갈래가 같은 도구를 갖고, 다른 것은
정의뿐이다. 본 세션에는 서브에이전트를 한 번 부르게 하고, 서브에이전트에게는 리뷰 대신 120초 걸리는
명령을 Bash 시간 제한 3초로 한 번 치고 보고하게 한다. 멈추라는 말도, 보고 전에 할 일을 묻는 말도
질문에 없다. 그 느린 명령 하나만 `--allowed-tools` 로 허용한다. `-p` 에는 승인할 사람이 없고
프로젝트 설정에 허용 규칙이 없어, 허용이 없던 첫 실행은 네 회차 모두 Bash 가 "This command requires
approval" 로 막혔다.

stream-json 에는 서브에이전트의 도구 호출과 결과가 `parent_tool_use_id` 를 달고 실린다(앞쪽 실행에서
빠지는 것은 서브에이전트의 마지막 글이다, `tools/canary.py` 독스트링). 회차는 셋이 모두 맞을 때만
측정이다. 본 세션이 답을 냈고, `bug-perf-review` 를 부른 Agent 호출이 있고, 그 호출에 딸린
(`parent_tool_use_id` 가 그 호출의 ID 인) Bash 결과가 "moved to the background" 를 담았다. 다른
서브에이전트의 호출과 결과는 세지 않는다. 마지막이 이 프로브의 전제다. 승인 거부처럼 명령이 돌지
않은 회차는 멈출 것이 없어 측정이 아니다. 회차마다 본 세션의 도구와 호출, 서브에이전트의 호출과
결과 앞부분을 찍는다. `TaskStop` 을 부를지는 단언하지 않고 본 것을 찍는다.

못 보는 것.
- 멈춘 뒤 그 프로세스가 실제로 죽었는지. 도구 결과의 말을 믿는다. PR 직전 리뷰어가 손으로 한 번
  봤다(프로브 README 의 이 행).
- 서브에이전트가 정의를 어느 체크아웃의 사본에서 실었는지. 대조군의 답으로 가른다(대기열 189).
- 문단과 도구 가운데 무엇이 멈추게 했는지. 대조군은 둘이 함께 다르다.
- 실제 리뷰 중에(도구 호출 40번 예산과 함께) 지키는지. 이 프로브의 PR 직전 리뷰에서 한 번
  지켰다(일지 2026-10-12-18).
- `timeout` 을 주지 않은 호출(기본 시간 제한)과 다른 OS 에서 Bash 가 같이 옮기는지.

돌리는 법: 워크트리 `.claude/worktrees/<이름>/` 루트에서
`uv run python .scratch/harness/probes/subagent_task_stop.py <출력 디렉터리> [대조군 체크아웃]`.
`claude` CLI 와 인증이 든다. 회차는 실험군 셋, 대조군 하나이고 회차마다 sonnet 세션 둘(본 세션과
서브에이전트)이다. 회차마다 stream-json 을 출력 디렉터리에 남긴다. 종료 코드: 0 모든 회차가
측정이다, 1 측정이 아닌 회차가 있다(제한 시간 600초를 넘긴 것 포함), 2 인자가 하나나 둘이 아니거나,
갈래의 정의 파일이 없거나, 대조가 없다(위).
"""

import json
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path

AGENT = "bug-perf-review"
DEFINITION = Path(".claude/agents/bug-perf-review.md")
EXPERIMENT, CONTROL = "워크트리", "대조군"
RUNS = {EXPERIMENT: 3, CONTROL: 1}
DEFAULT_CONTROL = Path("../../..")
SAME = (
    f"{CONTROL}: 정의에 TaskStop 이 있어 대조가 없다. "
    "옛 판을 git worktree add --detach 로 꺼내 둘째 인자로 준다"
)
SLOW = 'uv run python -c "import time; time.sleep(120)"'
MOVED = "moved to the background"
QUESTION = f"""bug-perf-review 서브에이전트를 Agent 도구로 한 번만 불러라. 끝날 때까지 기다린다
(run_in_background 를 쓰지 않는다). Agent 밖의 도구는 쓰지 마라. 서브에이전트에게 줄 프롬프트는 아래
단락 그대로다.

이번에는 리뷰하지 않는다. 범위를 잡지 말고 파일도 읽지 마라. Bash 도구로 `{SLOW}` 를 timeout
3000(밀리초)으로 한 번만 쳐라. 그다음 보고하라.

서브에이전트의 답을 고치거나 줄이지 말고 그대로 전하라.
"""
COMMAND = [
    "claude",
    "-p",
    "--setting-sources",
    "project,local",
    "--strict-mcp-config",
    "--allowed-tools",
    f"Bash({SLOW})",
    "--model",
    "sonnet",
    "--tools",
    "Agent,Bash,Read,Grep,Glob,TaskStop",
    "--output-format",
    "stream-json",
    "--verbose",
]
TIMEOUT = 600


@dataclass
class Run:
    """회차 하나에서 본 것."""

    init_tools: list[str] = field(default_factory=list[str])
    loaded: list[str] = field(default_factory=list[str])
    main_calls: list[str] = field(default_factory=list[str])
    agent_types: list[str] = field(default_factory=list[str])
    sub_lines: list[str] = field(default_factory=list[str])
    sub_names: list[str] = field(default_factory=list[str])
    moved: bool = False
    answer: str | None = None

    def problems(self) -> list[str]:
        found: list[str] = []
        if self.answer is None:
            found.append("본 세션이 답을 내지 못했다")
        if AGENT not in self.agent_types:
            found.append(f"{AGENT} 를 부른 Agent 호출이 없다")
        if not self.moved:
            found.append(f'서브에이전트의 Bash 결과에 "{MOVED}" 가 없다')
        return found


def clean_env() -> dict[str, str]:
    """이 저장소를 가리키는 `GIT_*` 를 벗긴다."""
    return {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}


def run(cwd: Path) -> str:
    """회차 하나의 stream-json. 제한 시간을 넘기면 그때까지의 출력이다."""
    executable = shutil.which(COMMAND[0]) or COMMAND[0]
    try:
        done = subprocess.run(
            [executable, *COMMAND[1:]],
            cwd=cwd,
            input=QUESTION.encode("utf-8"),
            capture_output=True,
            check=False,
            timeout=TIMEOUT,
            env=clean_env(),
        )
    except subprocess.TimeoutExpired as expired:
        return (expired.stdout or b"").decode("utf-8", errors="replace")
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
            found.append({str(key): value for key, value in event.items()})
    return found


def as_dict(value: object) -> dict[str, object]:
    return {str(k): v for k, v in value.items()} if isinstance(value, dict) else {}


def blocks(event: dict[str, object]) -> list[dict[str, object]]:
    content = as_dict(event.get("message")).get("content")
    return [as_dict(block) for block in content] if isinstance(content, list) else []


def strings(value: object) -> list[str]:
    return [str(item) for item in value] if isinstance(value, list) else []


def result_text(block: dict[str, object]) -> str:
    content = block.get("content")
    if isinstance(content, list):
        return " ".join(str(as_dict(part).get("text", "")) for part in content)
    return str(content)


def read_run(raw: str) -> Run:
    """서브에이전트의 호출과 결과는 `bug-perf-review` 를 부른 Agent 호출에 딸린 것만 센다."""
    seen = Run()
    names: dict[str, str] = {}
    targets: set[str] = set()
    for event in events(raw):
        kind = event.get("type")
        if kind == "system" and event.get("subtype") == "init":
            seen.init_tools = strings(event.get("tools"))
            seen.loaded = strings(event.get("agents"))
        if kind == "result":
            ok = event.get("subtype") == "success" and not event.get("is_error")
            seen.answer = str(event.get("result")) if ok else None
        parent = event.get("parent_tool_use_id")
        if parent is not None and str(parent) not in targets:
            continue  # 다른 서브에이전트의 것
        inside = parent is not None
        for block in blocks(event):
            if block.get("type") == "tool_use":
                name = str(block.get("name"))
                names[str(block.get("id"))] = name
                if not inside:
                    seen.main_calls.append(name)
                    subagent = as_dict(block.get("input")).get("subagent_type")
                    if subagent is not None:
                        seen.agent_types.append(str(subagent))
                    if subagent == AGENT:
                        targets.add(str(block.get("id")))
                    continue
                seen.sub_names.append(name)
                shown = json.dumps(block.get("input"), ensure_ascii=False)[:200]
                seen.sub_lines.append(f"  호출 {name} {shown}")
            elif block.get("type") == "tool_result" and inside:
                name = names.get(str(block.get("tool_use_id")), "?")
                text = result_text(block)
                if name == "Bash" and MOVED in text:
                    seen.moved = True
                error = " (오류)" if block.get("is_error") else ""
                seen.sub_lines.append(f"  결과 {name}{error}: {text[:300]}")
    return seen


def tools_line(definition: Path) -> str:
    lines = definition.read_text(encoding="utf-8").splitlines()
    return next((line for line in lines if line.startswith("tools:")), "tools 줄 없음")


def arm_problems(places: dict[str, Path]) -> list[str]:
    """돌리기 전에 막을 것. 갈래의 정의 파일이 없거나, 실험군 정의에 `TaskStop` 이 없거나, 대조군
    정의에 있다. 바이트가 다른 것만으로는 둘 다 새 판일 수 있어 대조가 되지 않는다(PR 리뷰)."""
    missing = [
        f"{name}: 정의가 없다: {place / DEFINITION}"
        for name, place in places.items()
        if not (place / DEFINITION).is_file()
    ]
    if missing:
        return missing
    found: list[str] = []
    if "TaskStop" not in (places[EXPERIMENT] / DEFINITION).read_text(encoding="utf-8"):
        found.append(f"{EXPERIMENT}: 정의에 TaskStop 이 없다")
    if "TaskStop" in (places[CONTROL] / DEFINITION).read_text(encoding="utf-8"):
        found.append(SAME)
    return found


def main(out: Path, control: Path) -> int:
    root = Path.cwd()
    places = {EXPERIMENT: root.resolve(), CONTROL: (root / control).resolve()}
    problems = arm_problems(places)
    if problems:
        print("\n".join(problems))
        return 2
    for name, place in places.items():
        print(f"{name}: {place} 의 정의 {tools_line(place / DEFINITION)}")
    out.mkdir(parents=True, exist_ok=True)
    jobs = [(name, index) for name, times in RUNS.items() for index in range(1, times + 1)]
    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        raws = list(pool.map(lambda job: run(places[job[0]]), jobs))
    invalid = 0
    for (name, index), raw in zip(jobs, raws, strict=True):
        (out / f"{name}-{index}.jsonl").write_text(raw, encoding="utf-8", newline="\n")
        seen = read_run(raw)
        print(f"\n== {name}-{index}")
        print(f"  본 세션 init 도구 {seen.init_tools}, {AGENT} 실림 {AGENT in seen.loaded}")
        print(f"  본 세션 호출 {seen.main_calls}, Agent 의 종류 {seen.agent_types}")
        print("\n".join(seen.sub_lines))
        print(f"  서브에이전트가 TaskStop 을 불렀다: {'TaskStop' in seen.sub_names}")
        problems = seen.problems()
        if problems:
            invalid += 1
            print(f"  측정 아님: {'; '.join(problems)}")
        print(f"  본 세션의 답: {(seen.answer or '')[:600]}")
    return 1 if invalid else 0


if __name__ == "__main__":
    if len(sys.argv) not in (2, 3):
        print(__doc__)
        raise SystemExit(2)
    control = Path(sys.argv[2]) if len(sys.argv) == 3 else DEFAULT_CONTROL
    raise SystemExit(main(Path(sys.argv[1]), control))
