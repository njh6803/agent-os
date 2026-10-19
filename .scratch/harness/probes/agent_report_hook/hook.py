"""탐침 훅(PostToolUse, 매처 `Agent|Task`). 서브에이전트가 보고를 돌려준 순간의 입력을 적고 표지
문장을 낸다.

`run.py` 가 `--settings` 로만 붙인다. 입력은 키 이름, 도구 이름, `tool_input.subagent_type`, 응답의
모양(종류와 키 이름)만 `PROBE_LOG` 에 한 줄로 덧붙이고 내용은 적지 않는다(원칙 V). 낸
문장(`additionalContext`)에는 질문에 없는 표지 `REPORT_HOOK_7731` 이 든다. 막지 않는다.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

TOKEN = "REPORT_HOOK_7731"


def main() -> int:
    payload = json.loads(sys.stdin.buffer.read())
    tool_input = payload.get("tool_input")
    response = payload.get("tool_response")
    entry = {
        "event": payload.get("hook_event_name"),
        "tool_name": payload.get("tool_name"),
        "payload_keys": sorted(payload),
        "subagent_type": tool_input.get("subagent_type") if isinstance(tool_input, dict) else None,
        "response_type": type(response).__name__,
        "response_keys": sorted(response) if isinstance(response, dict) else None,
        # 서브에이전트를 백그라운드로 띄운 호출이면 결과가 보고가 아니라 띄웠다는 응답이다.
        "is_async": response.get("isAsync") if isinstance(response, dict) else None,
        "status": response.get("status") if isinstance(response, dict) else None,
    }
    with Path(os.environ["PROBE_LOG"]).open("a", encoding="utf-8") as log:
        log.write(json.dumps(entry, ensure_ascii=False) + "\n")
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": f"{TOKEN}: 이 보고를 받은 턴에 일지로 옮긴다.",
        }
    }
    sys.stdout.write(json.dumps(output, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
