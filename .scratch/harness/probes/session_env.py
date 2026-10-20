"""세션 프로세스(`claude.exe`)마다 작업 디렉터리와 환경의 세션 id 를 찍는다.

ADR 0032 이력 2026-10-20 의 근거다. 데스크톱 앱이 세션의 `claude.exe` 환경에
`CLAUDE_CODE_HOST_SESSION_ID=local_<uuid>` 를 넣는다는 것을, 이 출력의 세션 id 를 `list_sessions` 의
`sessionId` 와 손으로 대 보아 확인한다. 읽는 길은 `tools/tidy_checkouts.py` 의 `scan_processes` 와
`process_session` 그대로다. 아무것도 끄거나 고치지 않는다.

측정의 표지: `claude.exe` 가 하나 이상 있고 그 가운데 세션 id 를 읽은 것이 하나 이상이다. 둘 가운데
하나라도 없으면 측정이 아니라고 찍고 1로 끝난다. 프로세스를 볼 수 없는 OS 면 2로 끝난다.

사용: uv run python .scratch/harness/probes/session_env.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from tools.tidy_checkouts import process_session, scan_processes  # noqa: E402

SESSION_IMAGES = frozenset({"claude.exe", "claude"})


def main() -> int:
    processes = scan_processes()
    if processes is None:
        print("이 OS 에서 프로세스를 볼 수 없다")
        return 2
    sessions = sorted(
        (pid, cwd) for pid, image, cwd in processes if image.lower() in SESSION_IMAGES
    )
    read = 0
    for pid, cwd in sessions:
        session = process_session(pid)
        read += session is not None
        print(f"pid {pid}\t{session or '(세션 id 없음)'}\t{cwd}")
    print(f"claude 프로세스 {len(sessions)}, 세션 id 를 읽은 것 {read}")
    if not sessions or not read:
        print("측정 아님: claude 프로세스가 없거나 세션 id 를 하나도 읽지 못했다")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
