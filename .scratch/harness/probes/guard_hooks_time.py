"""대기열 232·262·272 의 훅 한 번의 시간을 등록 모양으로 잰다(`.claude/rules/tools.md` 의 훅 시간
문단).

`tools/run_hooks.py` 의 `launch_argv`(등록 모양, 래퍼를 거친다)로 자식을 띄우고 stdin 에 페이로드를
넣어 끝날 때까지의 시간을 갈래마다 다섯 번씩 잰다. 픽스처는 그 러너의 `create_fixtures` 다. 갈래는
여섯이다.

- `hook_user_settings_read`: 대상이 아닌 Bash 명령(침묵), 프로젝트 설정의 Read(침묵), 사용자 설정의
  Read(막음). 파일을 열지 않고 경로만 푼다.
- `hook_push_delete_open_pr`: 지우지 않는 Bash 명령(git 을 부르지 않는 길, 침묵)과, origin 이 로컬
  bare 저장소인 열린 PR 의 머리 지우기(`git remote get-url` 과 `ls-remote` 의 길, 막음). gh 와
  네트워크는 재지 않는다.
- `hook_journal_retro`: 새 일지 파일의 Write(`tools/sibling_overlap.py` 를 자식으로 돌리는 길,
  알림). origin 이 로컬 bare 저장소이고 형제 워크트리가 없는 임시 저장소라 이 저장소에서 그 도구가
  쓰는 9~11초는 재지 않는다.

회차마다 판정(`outcome_of`)이 그 갈래의 기대와 같고, 발동 갈래는 훅이 낸 문장(`message_of`)에 그
동작의 표지(설정 훅의 "키 이름만", 푸시 훅의 "#7", 일지 훅의 `NUMBER_LEAD` 조각)가 있어야 측정이다.
일지 훅의 대조 실패 안내도 같은 `context` 라 판정만으로는 재려는 길을 지났는지 가를 수 없다(셀프
리뷰 표준 축). 어긋난 회차가 하나라도 있으면 1로 끝난다. 끝 줄에 갈래마다 최소·최대 밀리초를 찍는다.

쓰임: 저장소 루트에서 `uv run python .scratch/harness/probes/guard_hooks_time.py`
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from tools.run_hooks import (  # noqa: E402
    create_fixtures,
    hook_environment,
    launch_argv,
    message_of,
    outcome_of,
)

RUNS = 5


def cases(fixtures: dict[str, str]) -> list[tuple[str, str, str, str, dict[str, object]]]:
    """(이름, 훅, 기대, 문장의 표지, 페이로드). 침묵 갈래의 표지는 빈 글자다."""
    today, numbered = fixtures["TODAY"], fixtures["NUMBERED_REPO"]
    journal = f"{numbered}/docs/journal/{today}-01-x.md"
    settings, project = "hook_user_settings_read.py", f"{ROOT.as_posix()}/.claude/settings.json"
    push, repo = "hook_push_delete_open_pr.py", fixtures["OPEN_PR_REPO"]
    delete = "git push origin --delete chore/x"
    user = _read(f"{fixtures['USER_HOME']}/.claude.json")
    return [
        ("설정: 대상 아닌 Bash", settings, "silent", "", _bash("git status")),
        ("설정: 프로젝트 Read", settings, "silent", "", _read(project)),
        ("설정: 사용자 Read", settings, "deny", "키 이름만", user),
        ("푸시: 지우지 않는 Bash", push, "silent", "", {**_bash("git status"), "cwd": repo}),
        ("푸시: 열린 PR 지우기", push, "deny", "#7", {**_bash(delete), "cwd": repo}),
        (
            "일지: 새 파일 Write",
            "hook_journal_retro.py",
            "context",
            "다음 빈 번호와 다르다",
            {
                "tool_name": "Write",
                "tool_input": {"file_path": journal, "content": "x"},
                "tool_response": {"type": "create"},
            },
        ),
    ]


def _bash(command: str) -> dict[str, object]:
    return {"tool_name": "Bash", "tool_input": {"command": command}}


def _read(path: str) -> dict[str, object]:
    return {"tool_name": "Read", "tool_input": {"file_path": path}}


def run_once(hook: str, payload: dict[str, object], event: str) -> tuple[float, str, str]:
    """(밀리초, 판정, 훅이 낸 문장)."""
    started = time.perf_counter()
    completed = subprocess.run(
        launch_argv(hook),
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
    outcome = outcome_of(completed.returncode, stdout, event)
    return elapsed, outcome, message_of(completed.returncode, stdout, stderr)


def main() -> int:
    stream = sys.stdout
    if isinstance(stream, io.TextIOWrapper):
        stream.reconfigure(encoding="utf-8")
    bad = 0
    with tempfile.TemporaryDirectory() as scratch:
        fixtures = create_fixtures(Path(scratch))
        for name, hook, expect, marker, payload in cases(fixtures):
            event = "PostToolUse" if hook == "hook_journal_retro.py" else "PreToolUse"
            times: list[float] = []
            for _ in range(RUNS):
                elapsed, outcome, message = run_once(hook, payload, event)
                times.append(elapsed)
                if outcome != expect or marker not in message:
                    print(f"  어긋남 {name}: 기대 {expect}·{marker!r}, 실제 {outcome}")
                    bad += 1
            print(f"{name}: {min(times):.0f}~{max(times):.0f}ms ({RUNS}번, 기대 {expect})")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
