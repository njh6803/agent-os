"""포트에서 어긋난 어댑터 둘. `http_side` 를 가져오지 않는다는 조건은 `adapter_side` 와 같다.

재는 대상이다(`run.py`). 어긋남을 조립하는 자리의 타입 검사가 잡는지를 보려는 대조군이다.
`ShortRowAccounts` 는 돌려주는 줄에 `locked_until` 이 없고, `BytesNameAccounts` 는 `find` 가 이름을
`bytes` 로 받는다.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol

type Tier = Literal["system_admin", "admin"]


@dataclass(frozen=True, slots=True)
class ShortRow:
    name: str
    tier: Tier
    password_hash: str | None


@dataclass(frozen=True, slots=True)
class FullRow:
    name: str
    tier: Tier
    password_hash: str | None
    locked_until: datetime | None


class Incoming(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def tier(self) -> Tier: ...


class ShortRowAccounts:
    def find(self, name: str) -> ShortRow | None:
        return ShortRow(name=name, tier="admin", password_hash=None)

    def add(self, account: Incoming) -> ShortRow:
        return ShortRow(name=account.name, tier=account.tier, password_hash=None)

    def record_failure(self, name: str, *, at: datetime) -> int:
        return len(name) + at.year


class BytesNameAccounts:
    def find(self, name: bytes) -> FullRow | None:
        return FullRow(name=name.decode(), tier="admin", password_hash=None, locked_until=None)

    def add(self, account: Incoming) -> FullRow:
        return FullRow(name=account.name, tier=account.tier, password_hash=None, locked_until=None)

    def record_failure(self, name: str, *, at: datetime) -> int:
        return len(name) + at.year
