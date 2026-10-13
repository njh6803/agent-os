"""`hook_push_behind_main` 한 번의 시간을 등록 모양으로 잰다(`.claude/rules/tools.md` 의 훅 시간
문단).

`.claude/settings.json` 이 띄우는 모양(`tools/run_hooks.py` 의 `REGISTRATION`)으로 자식을 띄우고
stdin 에 페이로드를 넣어 끝날 때까지의 시간을 다섯 번씩 잰다. 갈래는 둘이다. 푸시가 아닌 명령(git 을
부르지 않는 길, Bash·PowerShell 호출 대부분)과, 로컬 bare 저장소를 origin 으로 두고 한 커밋 뒤처진
작업 브랜치의 푸시(브랜치 읽기, fetch, rev-list 의 길)다. origin 이 로컬 경로라 네트워크 fetch 의
시간은 재지 않는다.

회차마다 표지를 본다. 푸시 아닌 갈래는 종료 0에 출력이 비어야 하고, 푸시 갈래는 `permissionDecision`
이 `deny` 이고 이유에 훅의 문구 `origin/main 보다` 가 있어야 한다. 표지가 어긋난 회차가 있으면 1로
끝난다 (재려는 길을 지나지 않은 회차다). 끝 줄에 갈래마다 최소·최대 밀리초를 찍는다.

쓰임: 저장소 루트에서 `uv run python .scratch/harness/probes/push_behind_hook_time.py`
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path.cwd()
IDENTITY = ("-c", "user.name=probe", "-c", "user.email=probe@localhost")
RUNS = 5


def git(*args: str) -> None:
    subprocess.run(["git", *args], check=True, capture_output=True, timeout=30)


def behind_repository(scratch: Path) -> Path:
    origin = scratch / "origin.git"
    repo = scratch / "work"
    git("init", "-q", "--bare", "-b", "main", str(origin))
    git("init", "-q", "-b", "main", str(repo))
    git("-C", str(repo), *IDENTITY, "commit", "-q", "--allow-empty", "-m", "first")
    git("-C", str(repo), "remote", "add", "origin", str(origin))
    git("-C", str(repo), "switch", "-q", "-c", "chore/x")
    git("-C", str(repo), "switch", "-q", "main")
    git("-C", str(repo), *IDENTITY, "commit", "-q", "--allow-empty", "-m", "ahead")
    git("-C", str(repo), "push", "-q", "origin", "main")
    git("-C", str(repo), "switch", "-q", "chore/x")
    return repo


def run_once(payload: dict[str, object]) -> tuple[float, int, str]:
    command = [
        "uv",
        "run",
        "--project",
        str(ROOT),
        "--no-sync",
        "python",
        str(ROOT / "tools" / "launch_hook.py"),
        "hook_push_behind_main.py",
    ]
    environment = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    started = time.perf_counter()
    completed = subprocess.run(
        command,
        input=json.dumps(payload).encode("utf-8"),
        capture_output=True,
        env=environment,
        timeout=60,
        check=False,
    )
    elapsed = (time.perf_counter() - started) * 1000
    return elapsed, completed.returncode, completed.stdout.decode("utf-8", errors="replace")


def denied(output: str) -> bool:
    try:
        parsed = json.loads(output)
    except json.JSONDecodeError:
        return False
    specific = parsed.get("hookSpecificOutput", {}) if isinstance(parsed, dict) else {}
    return specific.get("permissionDecision") == "deny" and "origin/main 보다" in specific.get(
        "permissionDecisionReason", ""
    )


def main() -> int:
    with tempfile.TemporaryDirectory() as scratch:
        repo = behind_repository(Path(scratch))
        arms: dict[str, dict[str, object]] = {
            "푸시 아님": {"tool_input": {"command": "git status"}, "cwd": str(repo)},
            "뒤처진 푸시": {
                "tool_input": {"command": "git push -u origin chore/x"},
                "cwd": str(repo),
            },
        }
        summary: list[str] = []
        off_marker = 0
        for name, payload in arms.items():
            times: list[float] = []
            for index in range(RUNS):
                elapsed, code, output = run_once(payload)
                marked = (
                    denied(output) if name == "뒤처진 푸시" else code == 0 and not output.strip()
                )
                print(f"{name} {index + 1}: {elapsed:.0f}ms 표지 {'맞음' if marked else '어긋남'}")
                times.append(elapsed)
                if not marked:
                    off_marker += 1
            summary.append(f"{name} {min(times):.0f}~{max(times):.0f}ms")
        print("요약: " + ", ".join(summary))
    return 1 if off_marker else 0


if __name__ == "__main__":
    sys.exit(main())
