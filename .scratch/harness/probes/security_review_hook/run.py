"""내장 `/security-review` 를 부르는 순간의 계기 훅(`tools/hook_security_review_journal.py`) 문장이
본 세션의 모델에게 닿는지 잰다(대기열 250).

본 세션이 Skill 도구로 `security-review` 를 한 번 부르되 그 지시는 따르지 않게 하고, 그 호출에
덧붙은 글이 있으면 첫 문장을 옮기게 한다.
- `훅`(실험군, 두 회차): `--settings` 로 PreToolUse 매처 `Skill` 에 저장소의 훅을 붙인다.
- `훅없음`(대조군, 한 회차): 같은 질문을 훅 없이 던진다. 모델이 그 문장을 지어내지 않는다는 대조다.

재려는 상황이 났다는 표지는 셋이다. 회차의 stream-json 에 본 세션의 Skill 호출(`skill` 이
`security-review`)이 있고, 그 호출의 도구 결과가 오류가 아니며, 성공한 결과 이벤트가 있다. 하나라도
빠진 회차는 측정이 아니라 따로 찍고 1 로 끝난다. 결론은 측정인 회차만으로 낸다. 기대를 단언하지
않고 본 것(훅의 첫 문장 `LEAD` 가 답에 들었는지)을 찍는다. 스트림에는 additionalContext 가 실리지
않으므로(`.claude/rules/tools.md` 새 훅 항목) 답에 든 것으로만 본다.

세션은 이 저장소 밖 임시 디렉터리에서 카나리아와 같은 명령(`--setting-sources project,local
--strict-mcp-config`)으로 띄워 이 저장소와 사용자의 훅이 실리지 않는다. 모델은 sonnet, 도구는 Skill
하나다. 회차마다 stream-json 원본(`<갈래>-<n>.jsonl`)을 출력 디렉터리에 남기고 임시 디렉터리는 끝에
지운다.

못 보는 것: 사람이 슬래시 명령으로 친 `/security-review`. 세션이 그 명령의 지시를 끝까지 따라 보고를
쓴 뒤에도 문장이 맥락에 남는지(이 탐침은 지시를 따르지 않게 한다).

돌리는 법: `uv run python .scratch/harness/probes/security_review_hook/run.py <출력 디렉터리>`.
`claude` CLI 와 인증이 든다. 회차마다 sonnet 세션 하나다. 종료 코드: 0 모든 회차가 측정이 됐다,
1 측정이 아닌 회차가 있다(제한 시간 600초를 넘긴 것 포함).
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
sys.path.insert(0, str(ROOT))

from tools.hook_security_review_journal import LEAD, SKILL  # noqa: E402

QUESTION = (
    f"Call the Skill tool exactly once with skill {SKILL}. Do not carry out the instructions it"
    " returns and do not call any other tool. Then check whether any extra text was attached to"
    " that tool call apart from the skill's own content (for example a system reminder added by a"
    " hook). If there is, copy its first sentence verbatim on one line that starts with SEEN:."
    " If there is none, write exactly NONE."
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
    "4",
    "--allowed-tools",
    "Skill",
    "--tools",
    "Skill",
]
RUNS = (("훅", 1), ("훅", 2), ("훅없음", 1))
TIMEOUT = 600


@dataclass
class Facts:
    skill_calls: int
    skill_ok: bool
    answer: str | None


def clean_env() -> dict[str, str]:
    """이 저장소를 가리키는 `GIT_*` 를 벗긴다."""
    return {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}


def write_settings(work: Path) -> Path:
    hook_path = (ROOT / "tools" / "hook_security_review_journal.py").as_posix()
    command = f'uv run --project "{ROOT.as_posix()}" --no-sync python "{hook_path}"'
    hook = {"type": "command", "command": command, "timeout": 30}
    body = {"hooks": {"PreToolUse": [{"matcher": "Skill", "hooks": [hook]}]}}
    path = work / "settings.json"
    path.write_text(json.dumps(body, ensure_ascii=False), encoding="utf-8")
    return path


def run(work: Path, arm: str) -> str:
    """회차 하나의 stream-json. 제한 시간을 넘기면 그때까지의 출력이라 결과가 없어 무효로 찍힌다."""
    executable = shutil.which(COMMAND[0]) or COMMAND[0]
    extra = ["--settings", str(write_settings(work))] if arm == "훅" else []
    try:
        done = subprocess.run(
            [executable, *COMMAND[1:], *extra],
            cwd=work,
            input=QUESTION.encode("utf-8"),
            capture_output=True,
            check=False,
            timeout=TIMEOUT,
            env=clean_env(),
        )
    except subprocess.TimeoutExpired as expired:
        return (expired.stdout or b"").decode("utf-8", errors="replace")
    return done.stdout.decode("utf-8", errors="replace")


def blocks(event: dict[str, object]) -> list[dict[str, object]]:
    message = event.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    return [b for b in content if isinstance(b, dict)] if isinstance(content, list) else []


def facts(raw: str) -> Facts:
    """본 세션의 security-review 호출 수, 그 도구 결과가 오류 없이 왔는지, 성공한 결과의 답."""
    call_ids: set[str] = set()
    skill_ok = False
    answer: str | None = None
    for line in raw.splitlines():
        try:
            event = json.loads(line)
        except ValueError:  # 제한 시간에 끊기면 마지막 줄이 잘린다
            continue
        if not isinstance(event, dict) or event.get("parent_tool_use_id"):
            continue
        for block in blocks(event):
            tool_input = block.get("input")
            skill = tool_input.get("skill") if isinstance(tool_input, dict) else None
            is_call = block.get("type") == "tool_use" and block.get("name") == "Skill"
            if is_call and isinstance(skill, str) and skill.lstrip("/") == SKILL:
                call_ids.add(str(block.get("id")))
            if block.get("type") == "tool_result" and block.get("tool_use_id") in call_ids:
                skill_ok = skill_ok or not block.get("is_error")
        if event.get("type") == "result":
            ok = event.get("subtype") == "success" and not event.get("is_error")
            answer = event.get("result") if ok else None
    return Facts(skill_calls=len(call_ids), skill_ok=skill_ok, answer=answer)


def main(out: Path) -> int:
    out.mkdir(parents=True, exist_ok=True)
    invalid = 0
    for arm, index in RUNS:
        name = f"{arm}-{index}"
        work = Path(tempfile.mkdtemp(prefix="security-review-hook-"))
        try:
            raw = run(work, arm)
        finally:
            shutil.rmtree(work, ignore_errors=True)
        (out / f"{name}.jsonl").write_text(raw, encoding="utf-8", newline="\n")
        found = facts(raw)
        if not (found.skill_calls and found.skill_ok and found.answer is not None):
            invalid += 1
            print(
                f"{name}: 측정 아님 — security-review 호출 {found.skill_calls},"
                f" 도구 결과 성공 {found.skill_ok}, 결과 {found.answer is not None}"
            )
            continue
        answer = found.answer or ""
        has_lead = "있다" if LEAD in answer else "없다"
        print(
            f"{name}: security-review 호출 {found.skill_calls}, 훅의 첫 문장이 답에 {has_lead},"
            f" 답 앞머리 {' '.join(answer.split())[:160]!r}"
        )
    print(f"회차 {len(RUNS)}, 측정 아님 {invalid}")
    return 1 if invalid else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("돌리는 법: run.py <출력 디렉터리>")
    sys.exit(main(Path(sys.argv[1])))
