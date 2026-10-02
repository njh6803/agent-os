"""탐침 훅(PreToolUse·PostToolUse). 입력과 그 순간의 트랜스크립트 꼬리를 `PROBE_LOG` 에 덧붙인다.

대기열 94의 선행 조건을 잰다. 도구 호출 직전에 그 호출 앞의 assistant 텍스트가 트랜스크립트에 이미
있는지, 이 호출의 `tool_use` 기록 자체가 있는지, 병렬 호출과 서브에이전트의 호출에서는 어떤지다.
자기 `tool_use` 가 없으면 나타날 때까지 기다린 시간도 적는다. 같은 것을 PostToolUse 에서도 본다.
환경 변수는 적지 않고 입력은 키 이름과 `command` 하나만 적는다(원칙 V). 트랜스크립트에서는 마지막
사용자 프롬프트 뒤의 기록을 (종류, 메시지 id 끝 여섯 자, 블록 종류, 텍스트의 앞 60자 또는 도구 id)
로 처음 읽은 때(`tail_at_start`)와 기다린 뒤(`tail`) 두 번 적는다. 글은 `run.sh` 의 고정 프롬프트가
만든 낱말이다(ALPHA 등). 막지 않는다.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

Entry = list[str]


def _is_prompt(record: dict[str, object]) -> bool:
    """도구 결과가 아닌 사용자 기록(턴을 여는 프롬프트)인가."""
    if record.get("type") != "user":
        return False
    message = record.get("message")
    if not isinstance(message, dict):
        return False
    content = message.get("content")
    if isinstance(content, str):
        return True
    if not isinstance(content, list):
        return False
    return not any(isinstance(b, dict) and b.get("type") == "tool_result" for b in content)


def _entries(record: dict[str, object]) -> list[Entry]:
    kind = str(record.get("type"))
    message = record.get("message")
    if not isinstance(message, dict):
        return [[kind]]
    message_id = str(message.get("id", ""))[-6:]
    content = message.get("content")
    if not isinstance(content, list):
        return [[kind, message_id, "str"]]
    entries: list[Entry] = []
    for block in content:
        if not isinstance(block, dict):
            continue
        block_type = str(block.get("type"))
        if block_type == "text":
            entries.append([kind, message_id, "text", str(block.get("text", ""))[:60]])
        elif block_type == "tool_use":
            entries.append([kind, message_id, "tool_use", str(block.get("id", ""))[-8:]])
        elif block_type == "tool_result":
            entries.append(
                [kind, message_id, "tool_result", str(block.get("tool_use_id", ""))[-8:]]
            )
        else:
            entries.append([kind, message_id, block_type])
    return entries


def tail_since_prompt(transcript: Path) -> list[Entry]:
    """마지막 사용자 프롬프트 뒤의 기록들. 사이드체인과 메타 기록은 뺀다."""
    if not transcript.exists():
        return [["transcript-missing"]]
    records: list[dict[str, object]] = []
    for line in transcript.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if isinstance(record, dict) and record.get("type") in ("user", "assistant"):
            records.append(record)
    start = 0
    for index, record in enumerate(records):
        if _is_prompt(record) and not record.get("isSidechain"):
            start = index
    tail: list[Entry] = []
    for record in records[start:]:
        prefix = ["side"] if record.get("isSidechain") else []
        tail.extend(prefix + entry for entry in _entries(record))
    return tail


def has_own(tail: list[Entry], tool_use_id: str) -> bool:
    return any(e[-1] == tool_use_id[-8:] for e in tail if "tool_use" in e)


def main() -> int:
    started = time.time()
    payload = json.loads(sys.stdin.buffer.read())
    transcript = Path(str(payload.get("transcript_path", "")))
    tool_use_id = str(payload.get("tool_use_id", ""))
    tail = tail_since_prompt(transcript)
    tail_at_start = tail
    own_at_start = has_own(tail, tool_use_id)
    # 자기 tool_use 가 아직 없으면 20ms 마다 다시 읽어 나타날 때까지의 시간을 잰다(상한 3초).
    waited_ms = 0
    while not has_own(tail, tool_use_id) and waited_ms < 3000:
        time.sleep(0.02)
        waited_ms += 20
        tail = tail_since_prompt(transcript)
    tool_input = payload.get("tool_input")
    entry = {
        # 훅이 시작한 때(초, 소수 셋째 자리). 병렬 호출의 훅이 겹치는지 본다.
        "started": round(started % 1000, 3),
        "event": payload.get("hook_event_name"),
        "payload_keys": sorted(payload),
        "tool_name": payload.get("tool_name"),
        "tool_use_id": tool_use_id[-8:],
        "command": tool_input.get("command") if isinstance(tool_input, dict) else None,
        "agent_id_present": "agent_id" in payload,
        "agent_type": payload.get("agent_type"),
        "transcript_name": transcript.name,
        "own_tool_use_at_start": own_at_start,
        "waited_ms": waited_ms,
        "own_tool_use_after_wait": has_own(tail, tool_use_id),
        "tail_at_start": tail_at_start,
        "tail": tail,
    }
    with Path(os.environ["PROBE_LOG"]).open("a", encoding="utf-8") as log:
        log.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
