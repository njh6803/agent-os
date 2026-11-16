"""조립하는 자리(`server` 와 `main`)를 흉내 낸다. 두 쪽을 함께 가져오는 것은 이 모듈뿐이다.

재는 대상이다(`run.py`). 타입 검사가 여기서 어댑터의 모양을 포트에 맞대고, 실행하면 포트를 쓰는
쪽이 어댑터를 실제로 지난다. 결과는 `RESULT <json>` 한 줄이다.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime

from adapter_side import MemoryAccounts
from http_side import tier_after_adding


def main() -> int:
    tier, failures = tier_after_adding(
        MemoryAccounts(), "kim", at=datetime(2026, 11, 15, tzinfo=UTC)
    )
    print("RESULT " + json.dumps({"tier": tier, "failures": failures}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
