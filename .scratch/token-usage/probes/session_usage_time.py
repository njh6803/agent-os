"""세션 시작 훅(`tools/hook_session_usage.py`, 티켓 04) 한 번의 시간을 등록 모양으로 잰다
(`.claude/rules/tools.md` 의 훅 시간 문단).

`tools/run_hooks.py` 의 `launch_argv`(등록 모양, 래퍼를 거친다)로 자식을 띄우고 stdin 에
SessionStart 페이로드를 넣어 끝날 때까지의 시간을 갈래마다 다섯 번씩 잰다. 프로젝트 폴더는 그 러너의
`${USAGE_REPO}` 이고, 홈은 이 프로브가 만든 임시 폴더다. 가짜 `.claude.json` 은 이 PC 의 그 파일과
크기가 비슷하게(약 180KB, 2026-10-16 `stat` 으로 바이트 수만 봤다) 다른 키를 채운다. 훅은 그 파일
전체를 JSON 으로 풀기 때문이다. 갈래는 넷이다.

- 이어 하기: 계정만 남기는 길(침묵). git 하나와 `.claude.json` 읽기.
- 새 요약 뒤의 시작: 요약 파일을 읽고 표지를 만들어 보이는 길(알림). 회차마다 표지를 지운다.
- 같은 요약의 둘째 시작: 표지가 이미 있어 보이지 않는 길(침묵).
- 읽지 못한 `.claude.json`: 잘린 JSON 이라 0.2초 기다려 다시 읽는 길(침묵, 계정 null).

회차마다 판정(`outcome_of`)이 기대와 같고, 계정 기록이 한 줄 늘었고(그 줄의 계정이 갈래의 기대와
같다), 알림 갈래는 훅이 낸 문장에 `보고서 날짜:` 가 있어야 측정이다. 어긋난 회차가 하나라도 있으면
1로 끝난다. 끝 줄에 갈래마다 최소·최대 밀리초를 찍는다.

쓰임: 저장소 루트에서 `uv run python .scratch/token-usage/probes/session_usage_time.py`
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Literal

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
HOOK = "hook_session_usage.py"
UUID = "00000000-0000-0000-0000-0000000000bb"


def make_home(where: Path, kind: Literal["whole", "broken"]) -> Path:
    """약 180KB 의 가짜 `.claude.json` 을 둔 홈. `broken` 이면 그 글의 앞 절반만 둔다."""
    home = where / f"home-{kind}"
    home.mkdir()
    projects = {f"C:/project/p{i}": {"history": ["x" * 40] * 30} for i in range(130)}
    data = {"oauthAccount": {"accountUuid": UUID, "emailAddress": "t@probe"}, "projects": projects}
    text = json.dumps(data)
    half = text[: len(text) // 2]
    (home / ".claude.json").write_text(half if kind == "broken" else text, encoding="utf-8")
    return home


def run_once(payload: dict[str, object], env: dict[str, str]) -> tuple[float, str, str]:
    """(밀리초, 판정, 훅이 낸 문장)."""
    started = time.perf_counter()
    completed = subprocess.run(
        launch_argv(HOOK),
        input=json.dumps(payload).encode("utf-8"),
        capture_output=True,
        env={**hook_environment(), **env},
        cwd=ROOT,
        timeout=60,
        check=False,
    )
    elapsed = (time.perf_counter() - started) * 1000
    stdout = completed.stdout.decode("utf-8", "replace")
    stderr = completed.stderr.decode("utf-8", "replace")
    return (
        elapsed,
        outcome_of(completed.returncode, stdout, "SessionStart"),
        message_of(completed.returncode, stdout, stderr),
    )


def main() -> int:
    stream = sys.stdout
    if isinstance(stream, io.TextIOWrapper):
        stream.reconfigure(encoding="utf-8")
    bad = 0
    with tempfile.TemporaryDirectory() as scratch:
        fixtures = create_fixtures(Path(scratch))
        repo = Path(fixtures["USAGE_REPO"])
        report = repo / ".scratch" / "token-report"
        ledger = report / "ledger" / "accounts.jsonl"
        shown = report / "shown"
        homes = {kind: make_home(Path(scratch), kind) for kind in ("whole", "broken")}
        start = {"session_id": "s", "hook_event_name": "SessionStart", "source": "startup"}
        resume = {**start, "source": "resume"}
        branches = [
            ("이어 하기", resume, "whole", "silent", "", "clear"),
            ("새 요약 뒤의 시작", start, "whole", "notice", "보고서 날짜:", "clear"),
            ("같은 요약의 둘째 시작", start, "whole", "silent", "", "keep"),
            ("읽지 못한 .claude.json", resume, "broken", "silent", "", "clear"),
        ]
        for name, payload, kind, expect, marker, markers in branches:
            broken = kind == "broken"
            home = homes[kind].as_posix()
            env = {
                "CLAUDE_PROJECT_DIR": repo.as_posix(),
                "USERPROFILE": home,
                "HOME": home,
                "CLAUDE_CODE_SESSION_ATTENDED": "1",
            }
            times: list[float] = []
            for _ in range(RUNS):
                if markers == "clear":
                    for path in shown.glob("*") if shown.is_dir() else []:
                        path.unlink()
                before = ledger.read_text(encoding="utf-8").splitlines() if ledger.is_file() else []
                elapsed, outcome, message = run_once(payload, env)
                times.append(elapsed)
                after = ledger.read_text(encoding="utf-8").splitlines() if ledger.is_file() else []
                account = json.loads(after[-1])["account_uuid"] if after else "없음"
                grew = len(after) == len(before) + 1 and account == (None if broken else UUID)
                # 읽지 못한 갈래는 0.2초를 기다렸어야 그 길을 지난 것이다.
                grew = grew and (not broken or elapsed >= 200)
                if outcome != expect or marker not in message or not grew:
                    print(f"  어긋남 {name}: 기대 {expect}·{marker!r}, 실제 {outcome}, 줄 {grew}")
                    bad += 1
            print(f"{name}: {min(times):.0f}~{max(times):.0f}ms ({RUNS}번, 기대 {expect})")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
