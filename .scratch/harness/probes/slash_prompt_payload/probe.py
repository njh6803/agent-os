"""슬래시 명령으로 시작한 프롬프트를 `UserPromptSubmit` 훅이 어떤 글로 받는지 잰다(대기열 72).

대기열 72 는 첫 줄이 반각 `/<스킬>` 인 지시문이면 사람이 붙여 넣은 것으로 보고 계기를 넣는다. 반각
`/` 는 진짜 명령이 되어 스킬이 실리므로, 훅의 `prompt` 가 사람이 친 원문인지(첫 줄 `/<스킬> …` 과 그
뒤의 지시문) 스킬 본문으로 바뀐 글인지를 먼저 본다.

저장소 밖 임시 폴더에 프로젝트 하나를 짓는다. 사람만 부르는 스킬(`disable-model-invocation: true`,
`/implement` 와 같은 꼴) 하나와, 받은 입력을 그대로 한 줄 JSON 으로 남기는 `UserPromptSubmit` 훅
하나를 둔다. 갈래는 셋이다.
- A 반각 `/probe-slash 인자` 첫 줄 뒤에 빈 줄과 지시문 두 줄.
- B 같은 글의 첫 글자를 전각 `／`(U+FF0F)로. 명령이 되지 않는 대조군이다.
- C 슬래시 없는 보통 첫 줄. 대조군이다.
`claude -p` 에 프롬프트를 stdin 으로 주고, 사용자 설정(전역 훅)을 빼려고 `--setting-sources
project,local` 을 준다. 스킬이 실렸는지는 스킬 본문의 표지 문장을 모델이 옮겼는지로 본다(A 만 기대).

표지. 갈래마다 훅 기록이 하나 남고 stream-json 에 `result` 이벤트가 있을 때만 측정으로 센다.
하나라도 측정이 아니면 종료 코드를 1 로 둔다.

`claude` CLI 와 인증이 든다. 갈래마다 haiku 세션 하나다. 돌리는 법(저장소 루트에서):
`PYTHONUTF8=1 uv run python .scratch/harness/probes/slash_prompt_payload/probe.py`
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL_MARK = "SLASH-PROBE-LOADED"
DIRECTIVE = "다음 작업: 탐침\n어디서: 새 세션\n브랜치: chore/probe"
CASES = {
    "A_halfwidth": "/probe-slash 인자 하나\n\n" + DIRECTIVE,
    "B_fullwidth": "／probe-slash 인자 하나\n\n" + DIRECTIVE,
    "C_plain": "평범한 첫 줄이다. 도구를 쓰지 않고 '확인' 이라고만 답한다.\n\n" + DIRECTIVE,
}
SKILL = f"""---
name: probe-slash
description: 탐침용 스킬. 사람만 부른다.
disable-model-invocation: true
---

도구를 쓰지 않고 `{SKILL_MARK}` 한 낱말만 답한다.
"""
DUMP_HOOK = """import json, os, sys
payload = json.load(sys.stdin.buffer)
with open(os.environ["SLASH_PROBE_LOG"], "a", encoding="utf-8") as log:
    log.write(json.dumps(payload, ensure_ascii=False) + "\\n")
"""


def result_text(stream: Path) -> str | None:
    """stream-json 의 `result` 이벤트 글. 없으면 None. 풀지 못한 줄은 건너뛴다."""
    for line in stream.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict) and event.get("type") == "result":
            text = event.get("result")
            return text if isinstance(text, str) else ""
    return None


def main() -> int:
    claude = shutil.which("claude")
    if claude is None:
        print("claude CLI 가 없다")
        return 1
    with tempfile.TemporaryDirectory(prefix="slash-probe-") as temp:
        project = Path(temp) / "project"
        skill_dir = project / ".claude" / "skills" / "probe-slash"
        skill_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text(SKILL, encoding="utf-8")
        hook = Path(temp) / "dump_hook.py"
        hook.write_text(DUMP_HOOK, encoding="utf-8")
        command = f'"{Path(sys.executable).as_posix()}" "{hook.as_posix()}"'
        settings = {
            "hooks": {"UserPromptSubmit": [{"hooks": [{"type": "command", "command": command}]}]}
        }
        (project / ".claude" / "settings.json").write_text(json.dumps(settings), encoding="utf-8")
        measured = 0
        for name, prompt in CASES.items():
            log = Path(temp) / f"{name}.log"
            stream = Path(temp) / f"{name}.jsonl"
            env = dict(os.environ, SLASH_PROBE_LOG=str(log))
            args = [claude, "-p", "--setting-sources", "project,local", "--strict-mcp-config"]
            args += ["--model", "haiku", "--output-format", "stream-json", "--verbose"]
            args += ["--max-turns", "2"]
            with stream.open("wb") as out:
                try:
                    subprocess.run(
                        args,
                        cwd=project,
                        env=env,
                        input=prompt.encode("utf-8"),
                        stdout=out,
                        stderr=subprocess.DEVNULL,
                        check=False,
                        timeout=180,
                    )
                except subprocess.TimeoutExpired:
                    pass
            records = (
                [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
                if log.exists()
                else []
            )
            answer = result_text(stream)
            if len(records) != 1 or answer is None:
                print(f"{name}: 측정 아님(훅 기록 {len(records)}, result {answer is not None})")
                continue
            measured += 1
            received = str(records[0].get("prompt"))
            first = json.dumps(received.splitlines()[:1], ensure_ascii=False)
            got, sent = len(received.splitlines()), len(prompt.splitlines())
            print(f"{name}: 원문과 같다={received == prompt} 스킬 실림={SKILL_MARK in answer}")
            print(f"  받은 prompt 첫 줄: {first}")
            print(f"  받은 prompt 줄 수: {got}, 원문 줄 수: {sent}")
            print(f"  키: {sorted(records[0])}")
        print(f"측정 {measured}/{len(CASES)}")
        return 0 if measured == len(CASES) else 1


if __name__ == "__main__":
    raise SystemExit(main())
