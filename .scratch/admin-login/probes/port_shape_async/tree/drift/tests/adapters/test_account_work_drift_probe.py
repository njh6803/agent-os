"""트랜잭션 포트의 타입을 적는 시험 픽스처에 어긋난 어댑터를 적는다(port_shape_async 대조군).
돌리지 않는다.

픽스처마다 어긋남 하나이고, run.py 가 오류의 줄을 픽스처 함수의 줄 범위로 가른다. 뒤의 `*_work`
셋은 픽스처가 아니라 작업 객체를 작업 객체의 포트 타입(`AccountWork`)에 바로 적는 자리다. 트랜잭션
포트 자리의 글이 어느 메서드가 어긋났는지 말하지 않을 때 이 자리의 글이 말하는지 본다.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest_asyncio
from agent_os.adapters.postgres.account_work_drift import (
    LockOnlyTransactions,
    LockOnlyWork,
    NoDecoratorTransactions,
    SelfEnterTransactions,
    SyncLockWork,
    TextFailuresWork,
)
from agent_os.http.account_work import AccountTransactions, AccountWork
from sqlalchemy.ext.asyncio import AsyncConnection
from tools.database_for_tests import ScopedDatabase

from agent_os.adapters.postgres.database import PostgresDatabase, parse_database_url


def _owner(database: ScopedDatabase) -> PostgresDatabase:
    url = parse_database_url(database.text())
    if url is None:
        raise AssertionError("주소를 읽지 못했다")
    return PostgresDatabase(url, notice=print)


@pytest_asyncio.fixture
async def no_decorator_store(database: ScopedDatabase) -> AsyncIterator[AccountTransactions]:
    owner = _owner(database)
    store: AccountTransactions = NoDecoratorTransactions(owner.engine)
    try:
        yield store
    finally:
        await owner.close()


@pytest_asyncio.fixture
async def lock_only_store(database: ScopedDatabase) -> AsyncIterator[AccountTransactions]:
    owner = _owner(database)
    store: AccountTransactions = LockOnlyTransactions(owner.engine)
    try:
        yield store
    finally:
        await owner.close()


@pytest_asyncio.fixture
async def self_enter_store(database: ScopedDatabase) -> AsyncIterator[AccountTransactions]:
    owner = _owner(database)
    store: AccountTransactions = SelfEnterTransactions(owner.engine)
    try:
        yield store
    finally:
        await owner.close()


def sync_lock_work(connection: AsyncConnection) -> AccountWork:
    work: AccountWork = SyncLockWork(connection)
    return work


def lock_only_work(connection: AsyncConnection) -> AccountWork:
    work: AccountWork = LockOnlyWork(connection)
    return work


def text_failures_work(connection: AsyncConnection) -> AccountWork:
    work: AccountWork = TextFailuresWork(connection)
    return work
