"""tools/hook_bash_commit_msg.py 를 등록 모양(래퍼)으로 띄워 걸린 시간을 잰다(대기열 222).

갈래 넷: `commit` 이라는 글자가 없는 명령(정규식 전에 끝난다), `commit` 이 들었지만 `-F` 가 없는
커밋(shlex 로 나눠 보고 끝난다), `-F` 의 파일이 맞는 제목(자식 판정이 뜨고 지나간다), 긴 제목(자식
판정이 뜨고 막는다). 커밋은 commit-msg 판정을 부르는 임시 저장소에서 친다. 갈래마다 기대한 출력
(긴 제목은 deny, 나머지는 침묵)이 아니면 수를 찍지 않고 1로 끝난다 — 래퍼가 훅을 못 찾고 지나간
호출을 측정으로 세지 않는다. 저장소 루트에서
`uv run python .scratch/harness/probes/commit_msg_hook/time_hook.py` 로 돌린다.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
ROUNDS = 5


def launch(command: str, cwd: Path) -> tuple[float, str]:
    payload = {"tool_name": "Bash", "tool_input": {"command": command}, "cwd": cwd.as_posix()}
    argv = [
        "uv",
        "run",
        "--project",
        str(ROOT),
        "--no-sync",
        "python",
        str(ROOT / "tools" / "launch_hook.py"),
        "hook_bash_commit_msg.py",
    ]
    start = time.perf_counter()
    result = subprocess.run(
        argv, input=json.dumps(payload).encode(), capture_output=True, check=True
    )
    elapsed = (time.perf_counter() - start) * 1000
    output = result.stdout.decode("utf-8")
    return elapsed, "deny" if '"permissionDecision": "deny"' in output else output or "silent"


def main() -> int:
    with tempfile.TemporaryDirectory() as scratch:
        repo = Path(scratch)
        (repo / ".git").mkdir()
        (repo / "tools").mkdir()
        shutil.copy(ROOT / "tools" / "check_commit_msg.py", repo / "tools")
        (repo / ".pre-commit-config.yaml").write_text(
            "entry: uv run python tools/check_commit_msg.py\n", encoding="utf-8"
        )
        (repo / "good.txt").write_text("chore: 맞는 제목\n", encoding="utf-8")
        (repo / "long.txt").write_text("chore: " + "가" * 69 + "\n", encoding="utf-8")
        for label, command, expected in (
            ("커밋 글자 없음", "uv run pytest -q", "silent"),
            ("-F 없는 커밋", "git commit --amend --no-edit", "silent"),
            ("맞는 제목", "git commit -F good.txt", "silent"),
            ("긴 제목", "git commit -F long.txt", "deny"),
        ):
            runs = [launch(command, repo) for _ in range(ROUNDS)]
            outcomes = {outcome for _, outcome in runs}
            if outcomes != {expected}:
                print(f"{label}: 기대 {expected}, 실제 {sorted(outcomes)}")
                return 1
            times = sorted(elapsed for elapsed, _ in runs)
            print(f"{label}({expected}): {', '.join(f'{t:.0f}' for t in times)} ms")
    return 0


if __name__ == "__main__":
    sys.exit(main())
