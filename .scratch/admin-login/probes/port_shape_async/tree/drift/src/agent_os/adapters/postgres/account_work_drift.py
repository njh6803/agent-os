"""트랜잭션 포트에서 어긋난 어댑터들(port_shape_async 대조군). 임시 사본의 대조군 나무에만 두고
돌리지 않는다.

`agent_os.http` 를 가져오지 않는다는 조건은 `account_work.py` 와 같다. 클래스마다 어긋남 하나다.

- `NoDecoratorTransactions`: `transaction` 에 `@asynccontextmanager` 를 빠뜨려 비동기 생성기를
  돌려준다.
- `SyncLockTransactions`: 작업 객체의 `lock` 이 비동기가 아니다.
- `LockOnlyTransactions`: 작업 객체에 `write_failures` 가 없다.
- `TextFailuresTransactions`: 작업 객체의 `write_failures` 가 횟수를 `str` 로 받는다.
- `SelfEnterTransactions`: 클래스 모양인데 `__aenter__` 가 작업 객체가 아니라 자기를 돌려준다.
- `IteratorAnnotatedTransactions`: 어긋남이 아니라 적는 법의 갈래다. `@asynccontextmanager` 메서드의
  반환을 `AsyncIterator` 로 적는다(번들 typeshed 가 그 겹침에 `@deprecated` 를 붙였다).
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from types import TracebackType
from typing import Self

from agent_os.adapters.postgres.account_work import PgWork
from agent_os.adapters.postgres.accounts import Row
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine


class NoDecoratorTransactions:
    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    async def transaction(self) -> AsyncGenerator[PgWork]:
        async with self._engine.begin() as connection:
            yield PgWork(connection, for_update=True)


class SyncLockWork:
    def __init__(self, connection: AsyncConnection) -> None:
        self._work = PgWork(connection, for_update=True)

    def lock(self, name: str) -> Row | None:
        return None if name else None

    async def write_failures(
        self, name: str, *, failures: int, locked_until: datetime | None
    ) -> None:
        await self._work.write_failures(name, failures=failures, locked_until=locked_until)


class SyncLockTransactions:
    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[SyncLockWork]:
        async with self._engine.begin() as connection:
            yield SyncLockWork(connection)


class LockOnlyWork:
    def __init__(self, connection: AsyncConnection) -> None:
        self._work = PgWork(connection, for_update=True)

    async def lock(self, name: str) -> Row | None:
        return await self._work.lock(name)


class LockOnlyTransactions:
    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[LockOnlyWork]:
        async with self._engine.begin() as connection:
            yield LockOnlyWork(connection)


class TextFailuresWork:
    def __init__(self, connection: AsyncConnection) -> None:
        self._work = PgWork(connection, for_update=True)

    async def lock(self, name: str) -> Row | None:
        return await self._work.lock(name)

    async def write_failures(
        self, name: str, *, failures: str, locked_until: datetime | None
    ) -> None:
        await self._work.write_failures(name, failures=int(failures), locked_until=locked_until)


class TextFailuresTransactions:
    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[TextFailuresWork]:
        async with self._engine.begin() as connection:
            yield TextFailuresWork(connection)


class SelfEnterTransaction:
    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        return None


class SelfEnterTransactions:
    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    def transaction(self) -> SelfEnterTransaction:
        return SelfEnterTransaction(self._engine)


class IteratorAnnotatedTransactions:
    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    @asynccontextmanager
    async def transaction(self) -> AsyncIterator[PgWork]:
        async with self._engine.begin() as connection:
            yield PgWork(connection, for_update=True)
