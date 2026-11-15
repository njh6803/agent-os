"""조합마다 같은 일을 실제 PostgreSQL 에서 해 보고 조합마다 `RESULT <json>` 한 줄을 낸다.

한 조합의 일: 계정 하나 넣기, 이름으로 읽기, 연결 둘이 함께 실패 횟수를 다섯 번씩 올리기(읽고 하나
올려 쓰는 두 문장이 한 트랜잭션이다. 줄 잠금이 듣지 않으면 10 에 못 미친다), 다시 읽기, 갱신용 번호
넣기, 지우기, 또 지우기, 없는 이름 읽기. `ok` 는 그 값이 모두 기대와 같을 때만 참이다.

DSN 은 환경 변수 `PG_PROBE_DSN`(`postgresql://사용자:비밀번호@호스트:포트/DB`)에서 읽고 출력에 싣지
않는다. `--loop` 는 비동기 조합을 돌릴 이벤트 루프다. `default` 는 `asyncio.run` 의 기본(윈도는
Proactor), `selector` 는 `asyncio.SelectorEventLoop` 다. 이 파일은 도우미이고 회차의 셈은 `run.py`
가 한다. `loop_app.py` 와 `test_async_loop.py` 가 같은 함수를 uvicorn 과 pytest 안에서 부른다.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import secrets
import sys
from collections.abc import AsyncGenerator, Awaitable, Callable, Generator
from concurrent.futures import ThreadPoolExecutor
from contextlib import (
    AbstractAsyncContextManager,
    AbstractContextManager,
    asynccontextmanager,
    contextmanager,
)
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta

import stack_asyncpg
import stack_psycopg_async
import stack_psycopg_sync
import stack_sa_async
import stack_sa_sync
from model import Account
from sqlalchemy import Engine
from sqlalchemy.ext.asyncio import AsyncEngine

DSN_ENV = "PG_PROBE_DSN"
WORKERS = 2
BUMPS = 5


@dataclass(frozen=True)
class Outcome:
    stack: str
    ok: bool
    loop: str = "-"
    server_version: str = ""
    failed_attempts: int = -1
    deleted: tuple[bool, bool] = (False, False)
    missing_is_none: bool = False
    error: str = ""


def failure(stack: str, loop: str, error: Exception) -> Outcome:
    text = str(error).strip().splitlines()
    return Outcome(stack, ok=False, loop=loop, error=f"{type(error).__name__}: {text[0][:300]}")


@dataclass(frozen=True)
class Seen:
    """한 조합이 낸 값. `judge` 가 기대와 견준다."""

    version: str
    account_id: int
    first: Account | None
    after: Account | None
    deleted: tuple[bool, bool]
    missing: Account | None


def judge(stack: str, loop: str, seen: Seen) -> Outcome:
    first, after = seen.first, seen.after
    ok = (
        first is not None
        and first.id == seen.account_id
        and first.failed_attempts == 0
        and first.locked_until is None
        and after is not None
        and after.failed_attempts == WORKERS * BUMPS
        and seen.deleted == (True, False)
        and seen.missing is None
    )
    return Outcome(
        stack,
        ok=ok,
        loop=loop,
        server_version=seen.version,
        failed_attempts=after.failed_attempts if after is not None else -1,
        deleted=seen.deleted,
        missing_is_none=seen.missing is None,
    )


def sqlalchemy_url(dsn: str, driver: str) -> str:
    return dsn.replace("postgresql://", f"postgresql+{driver}://", 1)


# ---------------------------------------------------------------- 동기 조합


@dataclass(frozen=True)
class SyncStack[H]:
    label: str
    open: Callable[[str], AbstractContextManager[H]]
    version: Callable[[H], str]
    add_account: Callable[[H, str, str], int]
    find_account: Callable[[H, str], Account | None]
    bump_failures: Callable[[H, str], int]
    add_refresh_token: Callable[[H, bytes, int, datetime], None]
    delete_refresh_token: Callable[[H, bytes], bool]


@contextmanager
def open_sa_sync(dsn: str) -> Generator[Engine]:
    engine = stack_sa_sync.make_engine(sqlalchemy_url(dsn, "psycopg"))
    try:
        yield engine
    finally:
        engine.dispose()


PSYCOPG_SYNC = SyncStack(
    "psycopg-sync",
    stack_psycopg_sync.connect,
    stack_psycopg_sync.server_version,
    stack_psycopg_sync.add_account,
    stack_psycopg_sync.find_account,
    stack_psycopg_sync.bump_failures,
    stack_psycopg_sync.add_refresh_token,
    stack_psycopg_sync.delete_refresh_token,
)
SA_SYNC = SyncStack(
    "sqlalchemy-core-sync+psycopg",
    open_sa_sync,
    stack_sa_sync.server_version,
    stack_sa_sync.add_account,
    stack_sa_sync.find_account,
    stack_sa_sync.bump_failures,
    stack_sa_sync.add_refresh_token,
    stack_sa_sync.delete_refresh_token,
)


def exercise_sync[H](stack: SyncStack[H], dsn: str, loop: str = "-") -> Outcome:
    name = f"probe-{secrets.token_hex(6)}"
    token = secrets.token_bytes(32)

    def worker() -> None:
        with stack.open(dsn) as other:
            for _ in range(BUMPS):
                stack.bump_failures(other, name)

    def steps() -> Seen:
        with stack.open(dsn) as handle:
            version = stack.version(handle)
            account_id = stack.add_account(handle, name, "not-a-real-hash")
            first = stack.find_account(handle, name)
            with ThreadPoolExecutor(max_workers=WORKERS) as pool:
                for future in [pool.submit(worker) for _ in range(WORKERS)]:
                    future.result()
            after = stack.find_account(handle, name)
            expires_at = datetime.now(UTC) + timedelta(days=7)
            stack.add_refresh_token(handle, token, account_id, expires_at)
            deleted = (
                stack.delete_refresh_token(handle, token),
                stack.delete_refresh_token(handle, token),
            )
            missing = stack.find_account(handle, f"{name}-missing")
        return Seen(version, account_id, first, after, deleted, missing)

    try:
        seen = steps()
    except Exception as error:  # 조합 하나의 실패를 결과 한 줄로 남긴다
        return failure(stack.label, loop, error)
    return judge(stack.label, loop, seen)


# ---------------------------------------------------------------- 비동기 조합


@dataclass(frozen=True)
class AsyncStack[H]:
    label: str
    open: Callable[[str], AbstractAsyncContextManager[H]]
    version: Callable[[H], Awaitable[str]]
    add_account: Callable[[H, str, str], Awaitable[int]]
    find_account: Callable[[H, str], Awaitable[Account | None]]
    bump_failures: Callable[[H, str], Awaitable[int]]
    add_refresh_token: Callable[[H, bytes, int, datetime], Awaitable[None]]
    delete_refresh_token: Callable[[H, bytes], Awaitable[bool]]


@asynccontextmanager
async def open_psycopg_async(dsn: str) -> AsyncGenerator[stack_psycopg_async.Conn]:
    async with await stack_psycopg_async.connect(dsn) as conn:
        yield conn


@asynccontextmanager
async def open_psycopg_pool(dsn: str) -> AsyncGenerator[stack_psycopg_async.Conn]:
    pool = stack_psycopg_async.make_pool(dsn, size=1, timeout=8.0)
    try:
        await pool.open(wait=True, timeout=8.0)
        async with pool.connection() as conn:
            yield conn
    finally:
        await pool.close()


async def psycopg_version(conn: stack_psycopg_async.Conn) -> str:
    return stack_psycopg_async.server_version(conn)


@asynccontextmanager
async def open_asyncpg(dsn: str) -> AsyncGenerator[stack_asyncpg.Conn]:
    pool = await stack_asyncpg.make_pool(dsn, size=1)
    try:
        async with pool.acquire() as conn:
            yield conn
    finally:
        await pool.close()


async def asyncpg_version(conn: stack_asyncpg.Conn) -> str:
    return stack_asyncpg.server_version(conn)


def open_sa_async(driver: str) -> Callable[[str], AbstractAsyncContextManager[AsyncEngine]]:
    @asynccontextmanager
    async def opened(dsn: str) -> AsyncGenerator[AsyncEngine]:
        engine = stack_sa_async.make_engine(sqlalchemy_url(dsn, driver))
        try:
            yield engine
        finally:
            await engine.dispose()

    return opened


def sa_async(driver: str) -> AsyncStack[AsyncEngine]:
    return AsyncStack(
        f"sqlalchemy-core-async+{driver}",
        open_sa_async(driver),
        stack_sa_async.server_version,
        stack_sa_async.add_account,
        stack_sa_async.find_account,
        stack_sa_async.bump_failures,
        stack_sa_async.add_refresh_token,
        stack_sa_async.delete_refresh_token,
    )


def psycopg_async(
    label: str, opener: Callable[[str], AbstractAsyncContextManager[stack_psycopg_async.Conn]]
) -> AsyncStack[stack_psycopg_async.Conn]:
    return AsyncStack(
        label,
        opener,
        psycopg_version,
        stack_psycopg_async.add_account,
        stack_psycopg_async.find_account,
        stack_psycopg_async.bump_failures,
        stack_psycopg_async.add_refresh_token,
        stack_psycopg_async.delete_refresh_token,
    )


PSYCOPG_ASYNC = psycopg_async("psycopg-async", open_psycopg_async)
PSYCOPG_POOL = psycopg_async("psycopg-async+pool", open_psycopg_pool)
ASYNCPG = AsyncStack(
    "asyncpg",
    open_asyncpg,
    asyncpg_version,
    stack_asyncpg.add_account,
    stack_asyncpg.find_account,
    stack_asyncpg.bump_failures,
    stack_asyncpg.add_refresh_token,
    stack_asyncpg.delete_refresh_token,
)
SA_ASYNC_PSYCOPG = sa_async("psycopg")
SA_ASYNC_ASYNCPG = sa_async("asyncpg")


async def exercise_async[H](stack: AsyncStack[H], dsn: str) -> Outcome:
    loop = type(asyncio.get_running_loop()).__name__
    name = f"probe-{secrets.token_hex(6)}"
    token = secrets.token_bytes(32)

    async def worker() -> None:
        async with stack.open(dsn) as other:
            for _ in range(BUMPS):
                await stack.bump_failures(other, name)

    async def steps() -> Seen:
        async with stack.open(dsn) as handle:
            version = await stack.version(handle)
            account_id = await stack.add_account(handle, name, "not-a-real-hash")
            first = await stack.find_account(handle, name)
            await asyncio.gather(*(worker() for _ in range(WORKERS)))
            after = await stack.find_account(handle, name)
            expires_at = datetime.now(UTC) + timedelta(days=7)
            await stack.add_refresh_token(handle, token, account_id, expires_at)
            deleted = (
                await stack.delete_refresh_token(handle, token),
                await stack.delete_refresh_token(handle, token),
            )
            missing = await stack.find_account(handle, f"{name}-missing")
        return Seen(version, account_id, first, after, deleted, missing)

    try:
        seen = await steps()
    except Exception as error:  # 조합 하나의 실패를 결과 한 줄로 남긴다
        return failure(stack.label, loop, error)
    return judge(stack.label, loop, seen)


SYNC_LABELS = (PSYCOPG_SYNC.label, SA_SYNC.label)
ASYNC_LABELS = (
    PSYCOPG_ASYNC.label,
    PSYCOPG_POOL.label,
    ASYNCPG.label,
    SA_ASYNC_PSYCOPG.label,
    SA_ASYNC_ASYNCPG.label,
)


def run_sync_stack(label: str, dsn: str, loop: str = "-") -> Outcome:
    if label == PSYCOPG_SYNC.label:
        return exercise_sync(PSYCOPG_SYNC, dsn, loop)
    if label == SA_SYNC.label:
        return exercise_sync(SA_SYNC, dsn, loop)
    raise KeyError(label)


async def run_async_stack(label: str, dsn: str) -> Outcome:
    if label == PSYCOPG_ASYNC.label:
        return await exercise_async(PSYCOPG_ASYNC, dsn)
    if label == PSYCOPG_POOL.label:
        return await exercise_async(PSYCOPG_POOL, dsn)
    if label == ASYNCPG.label:
        return await exercise_async(ASYNCPG, dsn)
    if label == SA_ASYNC_PSYCOPG.label:
        return await exercise_async(SA_ASYNC_PSYCOPG, dsn)
    if label == SA_ASYNC_ASYNCPG.label:
        return await exercise_async(SA_ASYNC_ASYNCPG, dsn)
    raise KeyError(label)


def emit(outcome: Outcome) -> None:
    print(f"RESULT {json.dumps(asdict(outcome), ensure_ascii=False)}", flush=True)


async def run_all_async(dsn: str) -> None:
    for label in ASYNC_LABELS:
        emit(await run_async_stack(label, dsn))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--loop", choices=("default", "selector"), default="default")
    args = parser.parse_args()
    dsn = os.environ.get(DSN_ENV, "")
    if not dsn:
        sys.stderr.write(f"{DSN_ENV} 가 없다\n")
        return 2
    loop: str = args.loop
    if loop == "default":
        for label in SYNC_LABELS:
            emit(run_sync_stack(label, dsn))
        asyncio.run(run_all_async(dsn))
    else:
        asyncio.run(run_all_async(dsn), loop_factory=asyncio.SelectorEventLoop)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
