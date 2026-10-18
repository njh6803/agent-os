"""probe.py 의 A 갈래가 AskUserQuestion 에 등록하는 탐침 훅(대기열 308).

받은 입력을 `PROBE_LOG` 에 받은 시각(`at`)과 함께 한 줄로 덧붙이고, 모델에게 표지 문장을
additionalContext 로 낸다. 그 출력을 비운 뒤 끝 시각(`end`)을 한 줄 더 덧붙이고 바로 끝난다. 끝 기록
뒤의 파이썬 종료와 그것을 띄운 `uv run` 의 종료에 드는 시간은 재지 않는다. 표지(`MARK`)는 이 훅만
내는 문구라, 모델이 답에 옮기면 그 문장이 닿은 것이다. 표준 라이브러리만 쓴다.
"""

from __future__ import annotations

import json
import os
import sys
import time

MARK = "선택화면탐침-ZQ7"


def append(log: str | None, record: dict[str, object]) -> None:
    if log:
        with open(log, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def main() -> int:
    raw = sys.stdin.buffer.read()
    log = os.environ.get("PROBE_LOG")
    append(log, {"at": time.time(), "payload": json.loads(raw)})
    context = f"{MARK}: 선택 화면 훅이 돌았다."
    output = {"hookSpecificOutput": {"hookEventName": "PreToolUse", "additionalContext": context}}
    print(json.dumps(output), flush=True)
    append(log, {"end": time.time()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
