"""포트 타입을 적는 시험 픽스처의 자리(port_shape_async). 프로브가 타입 검사만 하고 돌리지 않는다.

`.claude/rules/tests.md` 의 `trace: TraceStore = FakeTrace()` 꼴을 계정 포트에 적는다. (나)의 별도
어댑터와 (가)의 한 객체를 둘 다 포트 자리에 적는다.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest_asyncio
from agent_os.adapters.postgres.accounts import PostgresAccounts
from agent_os.http.accounts import AccountStore
from tools.database_for_tests import ScopedDatabase

from agent_os.adapters.postgres.database import PostgresDatabase, parse_database_url


def _owner(database: ScopedDatabase) -> PostgresDatabase:
    url = parse_database_url(database.text())
    if url is None:
        raise AssertionError("주소를 읽지 못했다")
    return PostgresDatabase(url, notice=print)


@pytest_asyncio.fixture
async def accounts(database: ScopedDatabase) -> AsyncIterator[AccountStore]:
    owner = _owner(database)
    store: AccountStore = PostgresAccounts(owner.engine)
    try:
        yield store
    finally:
        await owner.close()


@pytest_asyncio.fixture
async def accounts_on_database(database: ScopedDatabase) -> AsyncIterator[AccountStore]:
    owner = _owner(database)
    store: AccountStore = owner
    try:
        yield store
    finally:
        await owner.close()


@pytest_asyncio.fixture
async def accounts_from_factory(database: ScopedDatabase) -> AsyncIterator[AccountStore]:
    owner = _owner(database)
    store: AccountStore = owner.accounts()
    try:
        yield store
    finally:
        await owner.close()
