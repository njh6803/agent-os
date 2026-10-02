"""tool_use 가 둘 이상인 메시지 중 결과가 형제 tool_use 사이에 끼어 쓰인 것을 센다.

`run.sh` 의 `claude -p` 세션에서는 병렬 호출의 기록이 메시지 끝에 함께 쓰여 결과가 끼지 않았다.
데스크톱 세션에서는 첫 호출의 결과를 쓸 때 그때까지의 블록이 함께 쓰여 tool_use 와 결과가 번갈아
기록된 메시지가 있었다. 그 수를 센다. 사이드체인은 뺀다. 원문은 찍지 않고 수만 찍는다.
쓰는 법: `uv run python .scratch/harness/probes/pretool_text/interleave.py <트랜스크립트 경로>`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    events: list[tuple[str, str]] = []
    for line in Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            record = json.loads(line)
        except ValueError:
            continue
        message = record.get("message")
        if not isinstance(message, dict) or record.get("isSidechain"):
            continue
        content = message.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if record.get("type") == "assistant" and block.get("type") == "tool_use":
                events.append(("use", str(message.get("id"))))
            elif record.get("type") == "user" and block.get("type") == "tool_result":
                events.append(("result", ""))
    positions: dict[str, list[int]] = {}
    for index, (kind, message_id) in enumerate(events):
        if kind == "use":
            positions.setdefault(message_id, []).append(index)
    parallel = {mid: found for mid, found in positions.items() if len(found) >= 2}
    interleaved = [
        mid
        for mid, found in parallel.items()
        if any(events[i][0] == "result" for i in range(found[0], found[-1]))
    ]
    print(f"tool_use 가 둘 이상인 메시지 {len(parallel)}개, 결과가 낀 것 {len(interleaved)}개")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
