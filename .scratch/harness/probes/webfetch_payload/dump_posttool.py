"""탐침 PostToolUse 훅. 받은 입력의 모양을 `run.sh` 가 넘긴 파일에 한 줄씩 덧붙인다.

페이지 본문은 적지 않는다. 결과(`tool_response.result`)는 길이 둘(글자, UTF-8 바이트)과 앞 80자만
적는다. 입력의 프롬프트도 길이만 적는다. 출력은 내지 않아 세션에 아무것도 더하지 않는다.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def shape(response: object) -> dict[str, object]:
    """`tool_response` 의 모양. 딕셔너리가 아니면 그 타입 이름만."""
    if not isinstance(response, dict):
        return {"type": type(response).__name__}
    fields: dict[str, object] = {str(key): value for key, value in response.items()}
    result = fields.get("result")
    entry: dict[str, object] = {
        "type": "dict",
        "types": {key: type(value).__name__ for key, value in fields.items()},
        "code": fields.get("code"),
        "bytes": fields.get("bytes"),
    }
    if isinstance(result, str):
        encoded = len(result.encode("utf-8"))
        entry["result_chars"] = len(result)
        entry["result_utf8"] = encoded
        entry["utf8_equals_bytes"] = encoded == fields.get("bytes")
        entry["result_head"] = result[:80]
    return entry


def main() -> int:
    out = Path(sys.argv[1])
    payload = json.loads(sys.stdin.buffer.read())
    tool_input = payload.get("tool_input") or {}
    entry = {
        "payload_keys": sorted(payload),
        "hook_event_name": payload.get("hook_event_name"),
        "tool_name": payload.get("tool_name"),
        "url": tool_input.get("url"),
        "prompt_chars": len(str(tool_input.get("prompt", ""))),
        "agent_id": payload.get("agent_id"),
        "tool_response": shape(payload.get("tool_response")),
    }
    with out.open("a", encoding="utf-8") as log:
        log.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
