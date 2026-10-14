"""탐침 PostToolUse 훅. 받은 입력을 `run.py` 가 넘긴 파일에 한 줄씩 덧붙인다.

Grep 의 결과는 `run.py` 가 저장소 밖에 지은 픽스처의 줄이라 비밀이 없어 그대로 적는다. 덧붙여
`tool_response` 의 키마다 타입과, 문자열 값에 생략 표지가 몇 번 들었는지를 적는다. 출력은 내지 않아
세션에 아무것도 더하지 않는다.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

MARKER = "[Omitted long matching line]"


def main() -> int:
    out = Path(sys.argv[1])
    payload = json.loads(sys.stdin.buffer.read())
    response = payload.get("tool_response")
    fields = response if isinstance(response, dict) else {}
    entry = {
        "payload_keys": sorted(payload),
        "hook_event_name": payload.get("hook_event_name"),
        "tool_name": payload.get("tool_name"),
        "tool_input": payload.get("tool_input"),
        "response_type": type(response).__name__,
        "response_types": {str(key): type(value).__name__ for key, value in fields.items()},
        "marker_counts": {
            str(key): value.count(MARKER) for key, value in fields.items() if isinstance(value, str)
        },
        "tool_response": response,
    }
    with out.open("a", encoding="utf-8") as log:
        log.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
