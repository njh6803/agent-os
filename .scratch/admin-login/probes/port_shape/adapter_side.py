"""`agent_os.adapters` 의 자리를 흉내 낸 모듈. `http_side` 를 가져오지 않고 그 포트를 만족한다.

재는 대상이다(`run.py`). 제품 코드가 아니다. 줄의 모양(`Row`)과 받는 값의 모양(`Incoming`)을 이
모듈이 스스로 적는다. 같은 모양을 두 모듈에 적는 것이 이 길의 값이다. 저장은 사전이다. 재는 것은
타입의 모양이지 PostgreSQL 이 아니다.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol

type Tier = Literal["system_admin", "admin"]


@dataclass(frozen=True, slots=True)
class Row:
    name: str
    tier: Tier
    password_hash: str | None
    locked_until: datetime | None


class Incoming(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def tier(self) -> Tier: ...


class MemoryAccounts:
    def __init__(self) -> None:
        self._rows: dict[str, Row] = {}
        self._failures: dict[str, list[datetime]] = {}

    def find(self, name: str) -> Row | None:
        return self._rows.get(name)

    def add(self, account: Incoming) -> Row:
        row = Row(name=account.name, tier=account.tier, password_hash=None, locked_until=None)
        self._rows[row.name] = row
        return row

    def record_failure(self, name: str, *, at: datetime) -> int:
        seen = self._failures.setdefault(name, [])
        seen.append(at)
        return len(seen)
