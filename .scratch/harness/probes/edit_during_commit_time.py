"""대기열 293 의 훅(`hook_edit_during_commit`) 한 번의 시간을 등록 모양으로
잰다(`.claude/rules/tools.md` 의 훅 시간 문단).

`tools/run_hooks.py` 의 `launch_argv`(등록 모양, 래퍼를 거친다)로 자식을 띄우고 stdin 에 페이로드를
넣어 끝날 때까지의 시간을 갈래마다 다섯 번씩 잰다. 픽스처는 그 러너의 `create_fixtures` 와
`committing_repository`(그 안의 워크트리에서 pre-commit 훅에 멈춘 `git commit` 이 돈다)다. 갈래는
셋이다.

- 체크아웃 밖 파일의 Write(침묵). 프로세스를 훑지 않는 길이다.
- 커밋이 돌지 않는 체크아웃 파일의 Write(침묵). 프로세스를 훑고 커밋을 찾지 못하는 길이다.
- 커밋이 도는 워크트리 파일의 Edit(알림). 훑고 찾는 길이다.

표지. 침묵 둘은 출력이 같아 어느 길을 지났는지 출력으로 가를 수 없다. 그래서 회차마다 훅 자신의
함수로 그 갈래의 상황이 났는지 먼저 본다. 체크아웃 밖이면 `checkout_of` 가 None 이고(훅의 `main` 이
훑기 전에 돌아온다, 코드를 읽었다), 훑는 두 갈래는 그 체크아웃이 있고
`running_commits(scan_processes())` 에 그 체크아웃의 커밋이 없거나 있다. 상황이 다르거나,
판정(`outcome_of`)이 기대와 다르거나, 알림 갈래의 문장(`message_of`)에 `git commit` 이 없으면 측정이
아니라 세고 1로 끝난다. 끝 줄에 갈래마다 최소·최대 밀리초와, 잴 때 이 PC 에 떠 있던 git 프로세스
수(훑는 길의 몫이 그 수를 따른다)를 찍는다.

쓰임: 저장소 루트에서 `uv run python .scratch/harness/probes/edit_during_commit_time.py`
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from tools.hook_edit_during_commit import (  # noqa: E402
    checkout_of,
    running_commits,
    scan_processes,
)
from tools.run_hooks import (  # noqa: E402
    committing_repository,
    create_fixtures,
    hook_environment,
    launch_argv,
    message_of,
    outcome_of,
)

HOOK = "hook_edit_during_commit.py"
RUNS = 5


def run_once(payload: dict[str, object]) -> tuple[float, str, str]:
    """(밀리초, 판정, 훅이 낸 문장)."""
    started = time.perf_counter()
    completed = subprocess.run(
        launch_argv(HOOK),
        input=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        capture_output=True,
        env=hook_environment(),
        cwd=ROOT,
        timeout=60,
        check=False,
    )
    elapsed = (time.perf_counter() - started) * 1000
    stdout = completed.stdout.decode("utf-8", "replace")
    stderr = completed.stderr.decode("utf-8", "replace")
    outcome = outcome_of(completed.returncode, stdout, "PostToolUse")
    return elapsed, outcome, message_of(completed.returncode, stdout, stderr)


def situation(path: str) -> str:
    """그 파일을 고쳤을 때 훅이 지날 길. 밖, 훑고 못 찾음, 훑고 찾음."""
    checkout = checkout_of(os.path.dirname(path))
    if checkout is None:
        return "밖"
    processes = scan_processes() or []
    found = {os.path.normcase(commit.checkout) for commit in running_commits(processes)}
    return "훑고 찾음" if os.path.normcase(checkout) in found else "훑고 못 찾음"


def _write(path: str) -> dict[str, object]:
    return {"tool_name": "Write", "tool_input": {"file_path": path, "content": "x\n"}}


def main() -> int:
    stream = sys.stdout
    if isinstance(stream, io.TextIOWrapper):
        stream.reconfigure(encoding="utf-8")
    bad = 0
    with (
        tempfile.TemporaryDirectory() as scratch,
        committing_repository(Path(scratch)) as committing,
    ):
        fixtures = create_fixtures(Path(scratch))
        side_file = str(committing / ".claude" / "worktrees" / "side" / "tracked.txt")
        loose = f"{scratch}/loose-note.md"
        no_commit = f"{fixtures['MAIN_REPO']}/x.md"
        edit = {"tool_name": "Edit", "tool_input": {"file_path": side_file, "old_string": "x"}}
        cases = [
            ("체크아웃 밖 Write", loose, "밖", "silent", "", _write(loose)),
            (
                "커밋 없는 체크아웃 Write",
                no_commit,
                "훑고 못 찾음",
                "silent",
                "",
                _write(no_commit),
            ),
            ("커밋이 도는 워크트리 Edit", side_file, "훑고 찾음", "context", "git commit", edit),
        ]
        processes = scan_processes()
        for name, path, path_kind, expect, marker, payload in cases:
            times: list[float] = []
            for _ in range(RUNS):
                seen = situation(path)
                elapsed, outcome, message = run_once(payload)
                times.append(elapsed)
                if seen != path_kind or outcome != expect or marker not in message:
                    print(f"  측정 아님 {name}: 상황 {seen}, 판정 {outcome}")
                    bad += 1
            print(f"{name}: {min(times):.0f}~{max(times):.0f}ms ({RUNS}번, 기대 {expect})")
    print(f"잴 때 떠 있던 git 프로세스: {'모름' if processes is None else len(processes)}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
