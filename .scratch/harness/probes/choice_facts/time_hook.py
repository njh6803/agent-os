"""`tools/hook_choice_facts.py`(대기열 308, 막는 꼴은 394·395) 한 번의 시간을 등록 모양으로
잰다(`.claude/rules/tools.md` 의 훅 시간 문단). 선택 화면은 훅이 끝난 뒤에 뜬다(같은 디렉터리의
`probe.py` A 갈래와 표지 훅이 1.5초를 기다리게 한 D 갈래에서 허락 요청이 훅의 끝 기록 뒤에 왔다).

`tools/run_hooks.py` 의 `launch_argv`(등록 모양, 래퍼를 거친다)로 자식을 띄우고 stdin 에 페이로드를
넣어 끝날 때까지의 시간을 갈래마다 다섯 번씩 잰다. 표지 폴더는 이 실행만 쓰는 빈 임시 폴더를
`TEMP`·`TMP`·`TMPDIR` 로 준다. 갈래는 셋이다.
- 처음 화면: 회차마다 새 세션 ID 라 표지를 만들고 막는다. 판정이 `deny` 이고 이유가 `LEAD` 로
  시작하며 옮긴 문장 `빨강: 서버` 가 있어야 측정이다.
- 다시 부른 화면: 재기 전에 한 번 돌려 표지를 만든 세션 ID 로 돈다. 판정이 `context` 이고 문장이
  `ANSWERED_LEAD` 로 시작해야 측정이다.
- 세션 없음: 세션 ID 를 빼 표지를 쓰지 않고 알린다. 판정이 `context` 이고 문장이 `LEAD` 로 시작하며
  `막지 못했다` 가 있어야 측정이다.
어긋난 회차가 하나라도 있으면 1로 끝난다.

쓰임: 저장소 루트에서 `uv run python .scratch/harness/probes/choice_facts/time_hook.py`
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from tools.hook_choice_facts import ANSWERED_LEAD, LEAD  # noqa: E402
from tools.run_hooks import hook_environment, launch_argv, message_of, outcome_of  # noqa: E402

RUNS = 5
HOOK = "hook_choice_facts.py"
SCREEN = {
    "questions": [
        {
            "question": "어느 쪽으로 할까요?",
            "header": "탐침",
            "options": [
                {"label": "빨강", "description": "서버 하나에 약 4.5초가 든다."},
                {"label": "파랑", "description": "지금 코드는 그대로 둔다."},
            ],
        }
    ]
}


def payload_for(session: str | None) -> dict[str, object]:
    payload: dict[str, object] = {"tool_name": "AskUserQuestion", "tool_input": SCREEN}
    if session is not None:
        payload["session_id"] = session
    return payload


def run_once(payload: dict[str, object], temp: Path) -> tuple[float, str, str]:
    """(밀리초, 판정, 훅이 낸 문장)."""
    env = {**hook_environment(), "TEMP": str(temp), "TMP": str(temp), "TMPDIR": str(temp)}
    started = time.perf_counter()
    completed = subprocess.run(
        launch_argv(HOOK),
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
    return (
        elapsed,
        outcome_of(completed.returncode, stdout, "PreToolUse"),
        message_of(completed.returncode, stdout, stderr),
    )


def first_marked(outcome: str, message: str) -> bool:
    return outcome == "deny" and message.startswith(LEAD) and "빨강: 서버" in message


def again_marked(outcome: str, message: str) -> bool:
    return outcome == "context" and message.startswith(ANSWERED_LEAD)


def fallback_marked(outcome: str, message: str) -> bool:
    return outcome == "context" and message.startswith(LEAD) and "막지 못했다" in message


def main() -> int:
    stream = sys.stdout
    if isinstance(stream, io.TextIOWrapper):
        stream.reconfigure(encoding="utf-8")
    bad = 0
    with tempfile.TemporaryDirectory() as scratch:
        temp = Path(scratch)
        again = f"time-again-{uuid.uuid4()}"
        run_once(payload_for(again), temp)  # 표지를 만든다. 재지 않는다.
        cases = [
            ("처음 화면", lambda: payload_for(f"time-first-{uuid.uuid4()}"), first_marked),
            ("다시 부른 화면", lambda: payload_for(again), again_marked),
            ("세션 없음", lambda: payload_for(None), fallback_marked),
        ]
        for name, make, marked in cases:
            times: list[float] = []
            for _ in range(RUNS):
                elapsed, outcome, message = run_once(make(), temp)
                times.append(elapsed)
                if not marked(outcome, message):
                    print(f"  어긋남 {name}: 실제 {outcome}, 문장 {message[:80]!r}")
                    bad += 1
            print(f"{name}: {min(times):.0f}~{max(times):.0f}ms ({RUNS}번)")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
