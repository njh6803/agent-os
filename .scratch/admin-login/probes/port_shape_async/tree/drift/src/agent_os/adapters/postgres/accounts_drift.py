"""포트에서 어긋난 어댑터들(port_shape_async 대조군). 임시 사본의 대조군 나무에만 둔다.

`agent_os.http` 를 가져오지 않는다는 조건은 `accounts.py` 와 같다. 클래스마다 어긋남 하나다.

- `SyncFindAccounts`: `find` 가 비동기가 아니다.
- `ShortRowAccounts`: 돌려주는 줄에 `locked_until` 이 없다.
- `BytesNameAccounts`: `find` 가 이름을 `bytes` 로 받는다.
- `ResultDriftAccounts`: 값 갈래의 `add` 가 `"taken"` 대신 `"exists"` 를 돌려준다.
- `ListRowAccounts`: 어긋남이 아니다. `list_all` 이 `list[Row]` 를 돌려준다. 포트가 `Sequence` 로
  적으면 맞고 `list` 로 적으면 맞지 않는지를 보는 데 쓴다.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from agent_os.adapters.postgres.accounts import (
    Incoming,
    Row,
    Tier,
    bump_failure,
    find_row,
    insert_row,
    list_rows,
)
from agent_os.core.conflicts import NameTaken
from sqlalchemy.ext.asyncio import AsyncEngine


@dataclass(frozen=True, slots=True)
class ShortRow:
    name: str
    tier: Tier
    password_hash: str | None
    failures: int


def _short(row: Row) -> ShortRow:
    return ShortRow(row.name, row.tier, row.password_hash, row.failures)


async def _added(engine: AsyncEngine, account: Incoming) -> Row:
    row = await insert_row(engine, account)
    if row is None:
        raise NameTaken(account.name)
    return row


class SyncFindAccounts:
    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    def find(self, name: str) -> Row | None:
        return None if name else None

    async def list_all(self) -> Sequence[Row]:
        return await list_rows(self._engine)

    async def record_failure(self, name: str, *, at: datetime) -> None:
        await bump_failure(self._engine, name, at=at)

    async def add(self, account: Incoming) -> Row:
        return await _added(self._engine, account)


class ShortRowAccounts:
    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    async def find(self, name: str) -> ShortRow | None:
        row = await find_row(self._engine, name)
        return None if row is None else _short(row)

    async def list_all(self) -> Sequence[ShortRow]:
        return [_short(row) for row in await list_rows(self._engine)]

    async def record_failure(self, name: str, *, at: datetime) -> None:
        await bump_failure(self._engine, name, at=at)

    async def add(self, account: Incoming) -> ShortRow:
        return _short(await _added(self._engine, account))


class BytesNameAccounts:
    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    async def find(self, name: bytes) -> Row | None:
        return await find_row(self._engine, name.decode())

    async def list_all(self) -> Sequence[Row]:
        return await list_rows(self._engine)

    async def record_failure(self, name: str, *, at: datetime) -> None:
        await bump_failure(self._engine, name, at=at)

    async def add(self, account: Incoming) -> Row:
        return await _added(self._engine, account)


class ResultDriftAccounts:
    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    async def add(self, account: Incoming) -> Row | Literal["exists"]:
        row = await insert_row(self._engine, account)
        return "exists" if row is None else row


class ListRowAccounts:
    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    async def find(self, name: str) -> Row | None:
        return await find_row(self._engine, name)

    async def list_all(self) -> list[Row]:
        return await list_rows(self._engine)

    async def record_failure(self, name: str, *, at: datetime) -> None:
        await bump_failure(self._engine, name, at=at)

    async def add(self, account: Incoming) -> Row:
        return await _added(self._engine, account)
