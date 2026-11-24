"""포트 타입을 적는 시험 픽스처에 어긋난 어댑터를 적는다(port_shape_async 대조군). 돌리지 않는다.

픽스처마다 어긋남 하나이고, run.py 가 오류의 줄을 픽스처 함수의 줄 범위로 가른다.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest_asyncio
from agent_os.adapters.postgres.accounts_drift import (
    BytesNameAccounts,
    ShortRowAccounts,
    SyncFindAccounts,
)
from agent_os.http.accounts import AccountStore
from tools.database_for_tests import ScopedDatabase

from agent_os.adapters.postgres.database import PostgresDatabase, parse_database_url


def _owner(database: ScopedDatabase) -> PostgresDatabase:
    url = parse_database_url(database.text())
    if url is None:
        raise AssertionError("주소를 읽지 못했다")
    return PostgresDatabase(url, notice=print)


@pytest_asyncio.fixture
async def sync_find_store(database: ScopedDatabase) -> AsyncIterator[AccountStore]:
    owner = _owner(database)
    store: AccountStore = SyncFindAccounts(owner.engine)
    try:
        yield store
    finally:
        await owner.close()


@pytest_asyncio.fixture
async def short_row_store(database: ScopedDatabase) -> AsyncIterator[AccountStore]:
    owner = _owner(database)
    store: AccountStore = ShortRowAccounts(owner.engine)
    try:
        yield store
    finally:
        await owner.close()


@pytest_asyncio.fixture
async def bytes_name_store(database: ScopedDatabase) -> AsyncIterator[AccountStore]:
    owner = _owner(database)
    store: AccountStore = BytesNameAccounts(owner.engine)
    try:
        yield store
    finally:
        await owner.close()
