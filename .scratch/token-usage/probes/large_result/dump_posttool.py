"""탐침 PostToolUse 훅. 받은 입력을 `run.py` 가 넘긴 파일에 그대로 한 줄씩 덧붙인다.

결과는 `run.py` 가 저장소 밖에 지은 픽스처와 그것을 읽거나 찍은 명령의 출력이라 비밀이 없어 거르지
않는다. 출력은 내지 않아 세션에 아무것도 더하지 않는다.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    out = Path(sys.argv[1])
    payload = json.loads(sys.stdin.buffer.read())
    with out.open("a", encoding="utf-8") as log:
        log.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
