"""카드 막기 탐침의 PreToolUse 훅. 받은 입력을 기록하고, 스스로 내는 카드만 막는다.

`card_block_app.py` 의 절차가 이 파일을 앱 세션의 PreToolUse 에 등록한다. 첫 인자가 기록
파일(JSON 줄)이다. 입력마다 받은 시각, 도구 이름, `tool_use_id`, `tool_input` 을 한 줄로
남긴다. 도구 이름이 `__start_session` 으로 끝나고 `tool_input.initiation` 이 `own_initiative`
이면 `permissionDecision: deny` 를 내고 이유에 `MARK` 를 싣는다. 그 밖의 입력은 아무것도 내지
않고 0 으로 끝나 도구를 그대로 지나게 한다. 판정은 이 기록과 세션 기록을 맞대는
`card_block_app.py` 가 한다.

표준 라이브러리만 쓰고 stdin 은 바이트로 읽는다(`.claude/rules/tools.md`).
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

MARK = "CARD-BLOCK-PROBE-7f3a"
REASON = (
    f"{MARK} 탐침이 스스로 내는 세션 카드(own_initiative)를 막았다. "
    "후속 일은 일지의 '다음'이나 대기열 행으로 적는다."
)


def decide(payload: dict[str, object]) -> dict[str, object] | None:
    """막을 입력이면 훅 출력을, 지나갈 입력이면 None 을 낸다."""
    name = payload.get("tool_name")
    tool_input = payload.get("tool_input")
    if not isinstance(name, str) or not name.endswith("__start_session"):
        return None
    if not isinstance(tool_input, dict):
        return None
    if tool_input.get("initiation") != "own_initiative":
        return None
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": REASON,
        }
    }


def main() -> int:
    log = Path(sys.argv[1])
    raw = sys.stdin.buffer.read()
    try:
        payload = json.loads(raw)
    except ValueError:
        payload = {"unparsed": raw.decode("utf-8", "replace")}
    if not isinstance(payload, dict):
        payload = {"unparsed": repr(payload)}
    out = decide(payload)
    record = {
        "at": time.time(),
        "tool_name": payload.get("tool_name"),
        "tool_use_id": payload.get("tool_use_id"),
        "tool_input": payload.get("tool_input"),
        "denied": out is not None,
    }
    with log.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    if out is not None:
        sys.stdout.write(json.dumps(out, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
