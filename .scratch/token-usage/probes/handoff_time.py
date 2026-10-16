"""인계 훅 둘의 한 번 시간을 등록 모양으로 잰다(`.claude/rules/tools.md` 의 훅 시간 문단, 티켓 05).

`tools/run_hooks.py` 의 `launch_argv`(등록 모양, 래퍼를 거친다)로 자식을 띄우고 stdin 에 페이로드를
넣어 끝날 때까지의 시간을 갈래마다 다섯 번씩 잰다(선례
`.scratch/harness/probes/guard_hooks_time.py`). 트랜스크립트는 이 저장소의 가장 큰
트랜스크립트(31MB, `hook_midturn_korean` 독스트링)에 맞춰 약 32MB 의 채움 기록 뒤에 모델 응답 하나를
둔 파일이다. 훅은 끝 2MiB 만 읽는다. 갈래는 넷이다.

- `hook_handoff`: 경계가 아닌 Bash(`git status`, 트랜스크립트를 열지 않는 길, 침묵)와 문턱 위의 커밋
  (트랜스크립트 끝을 읽는 길, 인계 문장).
- `hook_handoff_notice`: 문턱 위의 Stop(끝을 읽고 표지를 만드는 길, 알림. 회차마다 빈 임시 폴더를
  준다)과 문턱 아래의 Stop(끝을 읽고 침묵).

회차마다 판정(`outcome_of`)이 그 갈래의 기대와 같고, 발동 갈래는 훅이 낸 문장에 표지("인계의 계기",
"한 번만 낸다")가 있어야 측정이다. 어긋난 회차가 하나라도 있으면 1로 끝난다.

쓰임: 저장소 루트에서 `uv run python .scratch/token-usage/probes/handoff_time.py`
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

from tools.run_hooks import hook_environment, launch_argv, message_of, outcome_of  # noqa: E402

RUNS = 5
FILLER_BYTES = 32 * 1024 * 1024


def _transcript(scratch: Path, name: str, tokens: int) -> Path:
    """채움 기록 뒤에 세 입력 토큰 합이 `tokens` 인 응답 하나를 둔 트랜스크립트."""
    path = scratch / f"{name}.jsonl"
    filler = json.dumps({"type": "user", "message": {"role": "user", "content": "x" * 4000}}) + "\n"
    usage = {
        "input_tokens": 2,
        "cache_creation_input_tokens": 1000,
        "cache_read_input_tokens": tokens - 1002,
    }
    last = {"type": "assistant", "message": {"model": "claude-opus-5-5", "usage": usage}}
    with path.open("w", encoding="utf-8", newline="\n") as out:
        out.write(filler * (FILLER_BYTES // len(filler)))
        out.write(json.dumps(last) + "\n")
    return path


def run_once(
    hook: str, payload: dict[str, object], event: str, temp: Path
) -> tuple[float, str, str]:
    """(밀리초, 판정, 훅이 낸 문장)."""
    env = hook_environment()
    env.update({name: str(temp) for name in ("TEMP", "TMP", "TMPDIR")})
    started = time.perf_counter()
    completed = subprocess.run(
        launch_argv(hook),
        input=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        capture_output=True,
        env=env,
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
    with tempfile.TemporaryDirectory() as raw:
        scratch = Path(raw)
        over = _transcript(scratch, "over", 250_000).as_posix()
        under = _transcript(scratch, "under", 120_000).as_posix()

        def post(command: str) -> dict[str, object]:
            return {
                "session_id": "s",
                "hook_event_name": "PostToolUse",
                "transcript_path": over,
                "tool_name": "Bash",
                "tool_input": {"command": command},
            }

        def stop(transcript: str) -> dict[str, object]:
            return {"session_id": "s", "hook_event_name": "Stop", "transcript_path": transcript}

        cases = [
            (
                "인계: 경계 아닌 Bash",
                "hook_handoff.py",
                "PostToolUse",
                "silent",
                "",
                post("git status"),
            ),
            (
                "인계: 문턱 위 커밋",
                "hook_handoff.py",
                "PostToolUse",
                "context",
                "인계의 계기",
                post("git commit -F m.txt"),
            ),
            (
                "알림: 문턱 위 Stop",
                "hook_handoff_notice.py",
                "Stop",
                "notice",
                "한 번만 낸다",
                stop(over),
            ),
            ("알림: 문턱 아래 Stop", "hook_handoff_notice.py", "Stop", "silent", "", stop(under)),
        ]
        for index, (name, hook, event, expect, marker, payload) in enumerate(cases):
            times: list[float] = []
            for run in range(RUNS):
                temp = scratch / f"temp-{index}-{run}"
                temp.mkdir()
                elapsed, outcome, message = run_once(hook, payload, event, temp)
                times.append(elapsed)
                if outcome != expect or marker not in message:
                    print(f"  어긋남 {name}: 기대 {expect}·{marker!r}, 실제 {outcome}")
                    bad += 1
            print(f"{name}: {min(times):.0f}~{max(times):.0f}ms ({RUNS}번, 기대 {expect})")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
