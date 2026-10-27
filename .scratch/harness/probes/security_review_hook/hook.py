"""`run.py` 실험군의 `--settings` 가 부르는 래퍼. 훅이 돌았다는 표지로 인자로 받은 기록 파일에 한
줄을 덧붙이고, 같은 stdin 바이트를 저장소의 훅(`tools/hook_security_review_journal.py`)에 넘겨 그
stdout 과 종료 코드를 그대로 돌려준다.

스트림에는 additionalContext 가 실리지 않아(`.claude/rules/tools.md` 새 훅 항목), 이 줄이 없으면
실험군의 음성 결과를 훅이 돌지 못한 회차(PATH, 시간 초과의 fail-open)와 가를 수 없다(PR 직전
`bug-perf-review`, 일지 2026-10-28-08). 기록에는 도구 이름과 `skill` 값만 적는다.
"""

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
HOOK = ROOT / "tools" / "hook_security_review_journal.py"


def summary(data: bytes) -> str:
    """기록 한 줄. 페이로드를 풀지 못해도 훅이 돌았다는 사실은 남긴다."""
    try:
        payload = json.loads(data)
    except ValueError:
        return "ran unparsed"
    tool_input = payload.get("tool_input") if isinstance(payload, dict) else None
    skill = tool_input.get("skill") if isinstance(tool_input, dict) else None
    tool = payload.get("tool_name") if isinstance(payload, dict) else None
    return f"ran tool={tool} skill={skill}"


def main(log: Path) -> int:
    data = sys.stdin.buffer.read()
    with log.open("a", encoding="utf-8") as handle:
        handle.write(summary(data) + "\n")
    done = subprocess.run(
        [sys.executable, str(HOOK)], input=data, capture_output=True, check=False, timeout=20
    )
    sys.stdout.buffer.write(done.stdout)
    return done.returncode


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1])))
