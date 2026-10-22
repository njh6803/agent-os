"""probe.py 의 E 갈래가 AskUserQuestion 에 등록하는 탐침 훅(대기열 394).

같은 질문(질문 문장들)의 첫 호출은 거부하고 이유에 표지(`DENY_MARK`)와 지시를 싣는다. 두 번째
호출은 지나가게 하고 `log_hook.MARK` 를 additionalContext 로 낸다. 본 질문은 `PROBE_STATE` 파일에
적는다. 받은 입력과 판정을 `PROBE_LOG` 에 받은 시각(`at`)과 함께, 출력을 비운 뒤 끝 시각(`end`)을
덧붙인다. 표준 라이브러리만 쓴다.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

from log_hook import MARK, append

DENY_MARK = "선택화면거부탐침-K4"
REASON = (
    f"{DENY_MARK}: 이 선택 화면은 한 번 막았다. 이 이유를 읽었으면 다음 글의 첫 줄에 이 표지를"
    " 그대로 옮기고, 같은 입력으로 AskUserQuestion 을 다시 부른다. 다시 부르면 막지 않는다."
)


def key_of(tool_input: object) -> str:
    questions = tool_input.get("questions") if isinstance(tool_input, dict) else None
    texts = [q.get("question") for q in questions if isinstance(q, dict)] if questions else []
    return json.dumps(texts, ensure_ascii=False)


def main() -> int:
    payload = json.loads(sys.stdin.buffer.read())
    log = os.environ.get("PROBE_LOG")
    state = Path(os.environ["PROBE_STATE"])
    seen = json.loads(state.read_text(encoding="utf-8")) if state.exists() else []
    key = key_of(payload.get("tool_input"))
    first = key not in seen
    append(log, {"at": time.time(), "payload": payload, "decision": "deny" if first else "pass"})
    if first:
        state.write_text(json.dumps([*seen, key], ensure_ascii=False), encoding="utf-8")
        specific: dict[str, object] = {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": REASON,
        }
    else:
        context = f"{MARK}: 선택 화면 훅이 돌았다."
        specific = {"hookEventName": "PreToolUse", "additionalContext": context}
    print(json.dumps({"hookSpecificOutput": specific}), flush=True)
    append(log, {"end": time.time()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
