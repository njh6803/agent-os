"""서브에이전트가 보고를 돌려준 순간에 본 세션의 PostToolUse 계기 훅이 걸리는지 잰다(대기열 250).

물음은 둘이다. 그 순간 훅 입력이 어느 서브에이전트의 보고인지(`tool_input.subagent_type`) 알려
주는지, 그 훅이 낸 `additionalContext` 가 보고를 받은 본 세션의 모델에게 닿는지다. 본 세션이 Agent
도구로 general-purpose 서브에이전트를 한 번 부르고, 돌아온 결과 옆에 서브에이전트의 답 말고 덧붙은
글이 있으면 옮기게 한다.
- `훅`(실험군, 두 회차): `--settings` 로 PostToolUse 매처 `Agent|Task` 에 탐침 훅(`hook.py`)을
  붙인다. 훅은 입력의 모양을 적고 질문에 없는 표지 `REPORT_HOOK_7731` 이 든 문장을 낸다.
- `훅없음`(대조군, 한 회차): 같은 질문을 훅 없이 던진다. 모델이 표지를 지어내지 않는다는 대조다.

재려는 상황이 났다는 표지는 넷이다. 회차의 stream-json 에 본 세션의 Agent(또는 Task) 도구 호출이
있고, 그 호출의 도구 결과가 오류가 아니며, 성공한 결과 이벤트가 있다. 실험군은 훅 기록에
PostToolUse 의 Agent(또는 Task) 줄이 있다. 도구 결과를 보지 않던 첫 판은 대조군에서 호출이
거부돼도 `NONE` 을 측정으로 셌다(셀프 리뷰 표준 축, 일지 2026-10-19-05). 하나라도 빠진 회차는
측정이 아니라 따로 찍고 1 로 끝난다. 결론은 측정인 회차만으로 낸다. 기대를 단언하지 않고 본
것(표지가 답에 들었는지, 훅이 본 `subagent_type`)을 찍는다.

서브에이전트를 백그라운드로 띄울지는 모델과 하네스가 정하고 탐침은 고르지 않는다. 훅 줄의
`is_async` 가 참이면 그 호출의 결과는 보고가 아니라 띄웠다는 응답이고, 그 회차의 훅은 보고를 받을
때가 아니라 띄울 때 돈 것이다. 보고는 그 뒤에 따로 온다. 회차마다 그 값과 `status` 를 찍는다.

세션은 이 저장소 밖 임시 디렉터리에서 카나리아와 같은 명령(`--setting-sources
project,local --strict-mcp-config`)으로 띄워 이 저장소와 사용자의 훅이 실리지 않는다. 모델은
sonnet, 도구는 Agent 와 Read 다(`--tools Agent` 하나면 서브에이전트가 도구 0개로 거부됐다,
`docs/constitution/operations.md` 카나리아 항목). 회차마다 stream-json 원본(`<갈래>-<n>.jsonl`)과 훅
기록(`<갈래>-<n>.hook.jsonl`)을 출력 디렉터리에 남기고 임시 디렉터리는 끝에 지운다.

못 보는 것: 서브에이전트가 이 저장소의 정의(`bug-perf-review`)일 때. 훅 입력의 `subagent_type` 이 그
이름을 그대로 싣는지는 general-purpose 로만 본다. 내장 `/security-review` 는 Skill 로 실린
프롬프트를 본 세션이 따라 보고를 스스로 쓰므로 보고를 받는 도구 호출이 없다. 이 탐침은 그 길을 재지
않는다.

돌리는 법: `uv run python .scratch/harness/probes/agent_report_hook/run.py <출력 디렉터리>`.
`claude` CLI 와 인증이 든다. 회차마다 sonnet 세션 하나와 그 서브에이전트 하나다. 종료 코드: 0 모든
회차가 측정이 됐다, 1 측정이 아닌 회차가 있다(제한 시간 600초를 넘긴 것 포함).
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TOKEN = "REPORT_HOOK_7731"
AGENT_TOOLS = frozenset({"Agent", "Task"})
QUESTION = (
    "Call the Agent tool exactly once with subagent_type general-purpose and this prompt: "
    "'Reply with the single word DONE. Do not use any tools.' Do not call any other tool. "
    "After it returns, check whether any extra text was attached next to that tool result "
    "apart from the subagent's own reply (for example a system reminder added by a hook). "
    "If there is, copy that extra text verbatim on one line that starts with SEEN:. "
    "If there is none, write exactly NONE."
)
COMMAND = [
    "claude",
    "-p",
    "--setting-sources",
    "project,local",
    "--strict-mcp-config",
    "--model",
    "sonnet",
    "--output-format",
    "stream-json",
    "--verbose",
    "--max-turns",
    "6",
    "--allowed-tools",
    "Agent",
    "Read",
    "--tools",
    "Agent,Read",
]
RUNS = (("훅", 1), ("훅", 2), ("훅없음", 1))
TIMEOUT = 600


@dataclass
class Facts:
    agent_calls: int
    agent_ok: bool
    answer: str | None


def clean_env(log: Path) -> dict[str, str]:
    """이 저장소를 가리키는 `GIT_*` 를 벗기고 훅 기록 자리를 준다."""
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env["PROBE_LOG"] = str(log)
    return env


def settings(work: Path) -> Path:
    command = (
        f'uv run --project "{ROOT.as_posix()}" --no-sync python "{(HERE / "hook.py").as_posix()}"'
    )
    hook = {"type": "command", "command": command, "timeout": 30}
    body = {"hooks": {"PostToolUse": [{"matcher": "Agent|Task", "hooks": [hook]}]}}
    path = work / "settings.json"
    path.write_text(json.dumps(body, ensure_ascii=False), encoding="utf-8")
    return path


def run(work: Path, arm: str, log: Path) -> str:
    """회차 하나의 stream-json. 제한 시간을 넘기면 그때까지의 출력이라 결과가 없어 무효로 찍힌다."""
    executable = shutil.which(COMMAND[0]) or COMMAND[0]
    extra = ["--settings", str(settings(work))] if arm == "훅" else []
    try:
        done = subprocess.run(
            [executable, *COMMAND[1:], *extra],
            cwd=work,
            input=QUESTION.encode("utf-8"),
            capture_output=True,
            check=False,
            timeout=TIMEOUT,
            env=clean_env(log),
        )
    except subprocess.TimeoutExpired as expired:
        return (expired.stdout or b"").decode("utf-8", errors="replace")
    return done.stdout.decode("utf-8", errors="replace")


def facts(raw: str) -> Facts:
    """본 세션의 Agent(또는 Task) 도구 호출 수, 그 도구 결과가 오류 없이 왔는지, 성공한 결과의 답.
    결과가 없거나 오류면 답은 None 이다. 호출이 거부되면 도구 결과가 오류라 측정에서 빠진다."""
    call_ids: set[str] = set()
    agent_ok = False
    answer: str | None = None
    for line in raw.splitlines():
        try:
            event = json.loads(line)
        except ValueError:  # 제한 시간에 끊기면 마지막 줄이 잘린다
            continue
        if not isinstance(event, dict) or event.get("parent_tool_use_id"):
            continue
        content = event.get("message", {}).get("content", [])
        for block in content if isinstance(content, list) else []:
            if block.get("type") == "tool_use" and block.get("name") in AGENT_TOOLS:
                call_ids.add(str(block.get("id")))
            if block.get("type") == "tool_result" and block.get("tool_use_id") in call_ids:
                agent_ok = agent_ok or not block.get("is_error")
        if event.get("type") == "result":
            ok = event.get("subtype") == "success" and not event.get("is_error")
            answer = event.get("result") if ok else None
    return Facts(agent_calls=len(call_ids), agent_ok=agent_ok, answer=answer)


def hook_entries(log: Path) -> list[dict[str, object]]:
    if not log.is_file():
        return []
    entries: list[dict[str, object]] = []
    for line in log.read_text(encoding="utf-8").splitlines():
        entry = json.loads(line)
        if entry.get("event") == "PostToolUse" and entry.get("tool_name") in AGENT_TOOLS:
            entries.append(entry)
    return entries


def main(out: Path) -> int:
    out.mkdir(parents=True, exist_ok=True)
    invalid = 0
    for arm, index in RUNS:
        name = f"{arm}-{index}"
        log = out / f"{name}.hook.jsonl"
        log.unlink(missing_ok=True)
        work = Path(tempfile.mkdtemp(prefix="agent-report-hook-"))
        try:
            raw = run(work, arm, log)
        finally:
            shutil.rmtree(work, ignore_errors=True)
        (out / f"{name}.jsonl").write_text(raw, encoding="utf-8", newline="\n")
        found = facts(raw)
        entries = hook_entries(log)
        measured = found.agent_calls > 0 and found.agent_ok and found.answer is not None
        if arm == "훅":
            measured = measured and bool(entries)
        if not measured:
            invalid += 1
            print(
                f"{name}: 측정 아님 — Agent 호출 {found.agent_calls},"
                f" 도구 결과 성공 {found.agent_ok}, 결과 {found.answer is not None},"
                f" 훅 줄 {len(entries)}"
            )
            continue
        answer = found.answer or ""
        seen = [
            f"subagent_type={e.get('subagent_type')} is_async={e.get('is_async')}"
            f" status={e.get('status')} 응답={e.get('response_type')}"
            f" 키={e.get('response_keys')} 입력 키={e.get('payload_keys')}"
            for e in entries
        ]
        has_token = "있다" if TOKEN in answer else "없다"
        print(
            f"{name}: Agent 호출 {found.agent_calls}, 표지가 답에 {has_token},"
            f" 답 앞머리 {' '.join(answer.split())[:120]!r}"
        )
        for line in seen:
            print(f"  훅: {line}")
    print(f"회차 {len(RUNS)}, 측정 아님 {invalid}")
    return 1 if invalid else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("돌리는 법: run.py <출력 디렉터리>")
    sys.exit(main(Path(sys.argv[1])))
