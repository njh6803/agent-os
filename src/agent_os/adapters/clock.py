"""시스템 Clock. UTC 시각과 uuid4 실행 식별자. 시계와 난수가 core 에 닿는 유일한 자리다."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from agent_os.sdk import RunId


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)

    def new_run_id(self) -> RunId:
        return RunId(str(uuid4()))
