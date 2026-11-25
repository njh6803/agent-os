"""트랜잭션 하나를 여는 계정 포트의 PostgreSQL 구현. 프로브(`port_shape_async`)가 임시 사본의 어댑터
층에만 둔다.

제품 코드가 아니다. `agent_os.http` 를 가져오지 않고 시그니처로 `AccountTransactions` 를 만족한다.
작업 객체(`PgWork`)는 연결 하나를 쥐고 줄을 잠가 읽고(`SELECT ... FOR UPDATE`) 적는다. 판정은 하지
않는다. 트랜잭션을 여는 모양은 둘이다.

- `ContextTransactions`: `contextlib.asynccontextmanager` 로 지은 메서드가 `engine.begin()` 안에서
  작업 객체를 내준다. 블록이 예외로 끝나면 `engine.begin()` 이 되돌린다.
- `ClassTransactions`: `__aenter__` 와 `__aexit__` 를 가진 클래스(`ClassTransaction`)를 돌려준다.
  `__aexit__` 가 예외가 없으면 적고(commit) 있으면 되돌리며(rollback) 연결을 닫는다.

대조군 `UnlockedTransactions` 는 `ContextTransactions` 와 같되 읽기가 줄을 잠그지 않는다(`FOR
UPDATE` 없음). 겹친 두 시도가 같은 값을 읽어 한 번의 적기를 잃는지 보는 데 쓴다.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime
from types import TracebackType

from agent_os.adapters.postgres.accounts import (
    FAILURES,
    LOCKED_UNTIL,
    NAME,
    PASSWORD_HASH,
    TIER,
    Row,
    accounts,
    as_tier,
)
from sqlalchemy import Select, select, update
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine, AsyncTransaction


def _row_query() -> Select[str, str, str | None, int, datetime | None]:
    return select(NAME, TIER, PASSWORD_HASH, FAILURES, LOCKED_UNTIL)


class PgWork:
    """트랜잭션 하나 안의 읽기와 쓰기. 연결은 트랜잭션을 연 쪽이 쥐고 닫는다."""

    def __init__(self, connection: AsyncConnection, *, for_update: bool) -> None:
        self._connection = connection
        self._for_update = for_update

    async def lock(self, name: str) -> Row | None:
        query = _row_query().where(NAME == name)
        if self._for_update:
            query = query.with_for_update()
        found = (await self._connection.execute(query)).one_or_none()
        if found is None:
            return None
        row_name, tier, password_hash, failures, locked_until = found
        return Row(row_name, as_tier(tier), password_hash, failures, locked_until)

    async def write_failures(
        self, name: str, *, failures: int, locked_until: datetime | None
    ) -> None:
        await self._connection.execute(
            update(accounts)
            .where(NAME == name)
            .values(failures=failures, locked_until=locked_until)
        )


class ContextTransactions:
    """`asynccontextmanager` 로 짓는 모양."""

    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[PgWork]:
        async with self._engine.begin() as connection:
            yield PgWork(connection, for_update=True)


class ClassTransaction:
    """클래스로 짓는 비동기 문맥 관리자 하나. 한 번 들어가고 한 번 나온다."""

    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine
        self._connection: AsyncConnection | None = None
        self._transaction: AsyncTransaction | None = None

    async def __aenter__(self) -> PgWork:
        connection = self._engine.connect()
        await connection.start()
        self._connection = connection
        transaction = connection.begin()
        await transaction.start()
        self._transaction = transaction
        return PgWork(connection, for_update=True)

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        connection, transaction = self._connection, self._transaction
        self._connection, self._transaction = None, None
        try:
            if transaction is not None:
                if exc is None:
                    await transaction.commit()
                else:
                    await transaction.rollback()
        finally:
            if connection is not None:
                await connection.close()


class ClassTransactions:
    """클래스로 짓는 모양."""

    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    def transaction(self) -> ClassTransaction:
        return ClassTransaction(self._engine)


class UnlockedTransactions:
    """대조군. `ContextTransactions` 와 같되 읽기가 줄을 잠그지 않는다."""

    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[PgWork]:
        async with self._engine.begin() as connection:
            yield PgWork(connection, for_update=False)
