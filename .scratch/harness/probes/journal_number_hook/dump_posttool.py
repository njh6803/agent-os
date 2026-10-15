"""탐침 PostToolUse 훅. 받은 입력의 모양을 `run.py` 가 넘긴 파일에 한 줄씩 덧붙인다.

글의 본문은 적지 않는다. 입력은 `file_path` 와 키만, 결과(`tool_response`)는 키와 값의 타입,
`type` 의 값, `originalFile` 이 null 인지만 적는다. 출력은 내지 않아 세션에 아무것도 더하지
않는다.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def shape(response: object) -> dict[str, object]:
    """`tool_response` 의 모양. 딕셔너리가 아니면 그 타입 이름만."""
    if not isinstance(response, dict):
        return {"kind": type(response).__name__}
    fields: dict[str, object] = {str(key): value for key, value in response.items()}
    return {
        "kind": "dict",
        "types": {key: type(value).__name__ for key, value in fields.items()},
        "type": fields.get("type"),
        "original_is_null": fields.get("originalFile") is None,
    }


def main() -> int:
    out = Path(sys.argv[1])
    payload = json.loads(sys.stdin.buffer.read())
    tool_input = payload.get("tool_input") or {}
    entry = {
        "payload_keys": sorted(payload),
        "hook_event_name": payload.get("hook_event_name"),
        "tool_name": payload.get("tool_name"),
        "file_path": tool_input.get("file_path"),
        "input_keys": sorted(tool_input),
        "tool_response": shape(payload.get("tool_response")),
    }
    with out.open("a", encoding="utf-8") as log:
        log.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
