"""`tools/hook_choice_facts.py`(대기열 308) 한 번의 시간을 등록 모양으로
잰다(`.claude/rules/tools.md` 의 훅 시간 문단). 선택 화면은 훅이 끝난 뒤에 뜬다(같은 디렉터리의
`probe.py` A 갈래와 표지 훅이 1.5초를 기다리게 한 D 갈래에서 허락 요청이 훅의 끝 기록 뒤에 왔다).

`tools/run_hooks.py` 의 `launch_argv`(등록 모양, 래퍼를 거친다)로 자식을 띄우고 stdin 에 페이로드를
넣어 끝날 때까지의 시간을 갈래마다 다섯 번씩 잰다. 갈래는 둘이다. 수가 든 설명(`probe.py` 의 훅이
받은 입력, 문장을 옮기는 길)과 수가 없는 설명(일반 문장만 내는 길)이다. 회차마다 판정이 `context`
이고 훅이 낸 문장에 그 길의 표지(앞 갈래는 옮긴 문장 `빨강: 서버`, 뒤 갈래는 알림의 첫 문장이면서
옮긴 문장의 머리가 없는 것)가 있어야 측정이다. 어긋난 회차가 하나라도 있으면 1로 끝난다.

쓰임: 저장소 루트에서 `uv run python .scratch/harness/probes/choice_facts/time_hook.py`
"""

from __future__ import annotations

import io
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from tools.hook_choice_facts import LEAD, QUOTES_LEAD  # noqa: E402
from tools.run_hooks import hook_environment, launch_argv, message_of, outcome_of  # noqa: E402

RUNS = 5
HOOK = "hook_choice_facts.py"


def _screen(first: str, second: str) -> dict[str, object]:
    options = [{"label": "빨강", "description": first}, {"label": "파랑", "description": second}]
    question = {"question": "어느 쪽으로 할까요?", "header": "탐침", "options": options}
    return {"tool_name": "AskUserQuestion", "tool_input": {"questions": [{**question}]}}


CASES = [
    (
        "수가 든 설명",
        _screen("서버 하나에 약 4.5초가 든다.", "지금 코드는 그대로 둔다."),
        "빨강: 서버",
    ),
    ("수가 없는 설명", _screen("차례로 닫는다.", "지금 코드는 그대로 둔다."), ""),
]


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
    return (
        elapsed,
        outcome_of(completed.returncode, stdout, "PreToolUse"),
        message_of(completed.returncode, stdout, stderr),
    )


def marked(message: str, marker: str) -> bool:
    if not message.startswith(LEAD):
        return False
    return marker in message if marker else QUOTES_LEAD not in message


def main() -> int:
    stream = sys.stdout
    if isinstance(stream, io.TextIOWrapper):
        stream.reconfigure(encoding="utf-8")
    bad = 0
    for name, payload, marker in CASES:
        times: list[float] = []
        for _ in range(RUNS):
            elapsed, outcome, message = run_once(payload)
            times.append(elapsed)
            if outcome != "context" or not marked(message, marker):
                print(f"  어긋남 {name}: 실제 {outcome}, 문장 {message[:80]!r}")
                bad += 1
        print(f"{name}: {min(times):.0f}~{max(times):.0f}ms ({RUNS}번)")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
