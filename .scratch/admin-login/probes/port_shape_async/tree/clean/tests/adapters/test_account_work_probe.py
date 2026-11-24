"""트랜잭션 포트의 타입을 적는 시험 픽스처의 자리(port_shape_async). 프로브가 타입 검사만 하고
돌리지 않는다.

`.claude/rules/tests.md` 의 `trace: TraceStore = FakeTrace()` 꼴을 트랜잭션 포트에 적는다.
트랜잭션을 여는 모양 둘(`asynccontextmanager`, 클래스)을 둘 다 포트 자리에 적는다.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest_asyncio
from agent_os.adapters.postgres.account_work import ClassTransactions, ContextTransactions
from agent_os.http.account_work import AccountTransactions
from tools.database_for_tests import ScopedDatabase

from agent_os.adapters.postgres.database import PostgresDatabase, parse_database_url


def _owner(database: ScopedDatabase) -> PostgresDatabase:
    url = parse_database_url(database.text())
    if url is None:
        raise AssertionError("주소를 읽지 못했다")
    return PostgresDatabase(url, notice=print)


@pytest_asyncio.fixture
async def context_transactions(database: ScopedDatabase) -> AsyncIterator[AccountTransactions]:
    owner = _owner(database)
    store: AccountTransactions = ContextTransactions(owner.engine)
    try:
        yield store
    finally:
        await owner.close()


@pytest_asyncio.fixture
async def class_transactions(database: ScopedDatabase) -> AsyncIterator[AccountTransactions]:
    owner = _owner(database)
    store: AccountTransactions = ClassTransactions(owner.engine)
    try:
        yield store
    finally:
        await owner.close()
