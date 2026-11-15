"""pyright 오류를 기대하는 대조군. 돌려주는 줄에 칸이 하나 없는 어댑터를 포트 자리에 넘긴다.

`run.py` 가 이 파일에서 `reportArgumentType` 을 본다. 실행하지 않는다.
"""

from __future__ import annotations

from datetime import UTC, datetime

from adapter_drift import ShortRowAccounts
from http_side import tier_after_adding

tier_after_adding(ShortRowAccounts(), "kim", at=datetime(2026, 11, 15, tzinfo=UTC))
