"""조합: asyncpg. 타입은 asyncpg-stubs 가 준다(없을 때의 결과는 README 가 적는다)."""

from __future__ import annotations

from datetime import datetime

import asyncpg
from asyncpg.pool import PoolConnectionProxy
from model import Account, as_datetime_or_none, as_int, as_str

# 풀에서 빌린 연결은 `Connection` 이 아니라 `PoolConnectionProxy` 다. `Connection` 만 받게 적으면
# 풀에서 빌린 연결을 넘기는 자리가 pyright 오류다(`friction_asyncpg_pool.py` 가 그 오류를 다시
# 낸다).
type Conn = asyncpg.Connection[asyncpg.Record] | PoolConnectionProxy[asyncpg.Record]
type Pool = asyncpg.Pool[asyncpg.Record]


async def make_pool(dsn: str, *, size: int = 2) -> Pool:
    return await asyncpg.create_pool(dsn, min_size=size, max_size=size)


def server_version(conn: Conn) -> str:
    # PostgreSQL 10 부터 판은 두 자리(18.7)인데 asyncpg 는 major=18, minor=0, micro=7 로 준다.
    version = conn.get_server_version()
    return f"{version.major}.{version.micro}"


async def add_account(conn: Conn, name: str, password_hash: str) -> int:
    value: object = await conn.fetchval(
        "INSERT INTO accounts (name, password_hash) VALUES ($1, $2) RETURNING id",
        name,
        password_hash,
    )
    return as_int(value)


async def find_account(conn: Conn, name: str) -> Account | None:
    row = await conn.fetchrow(
        "SELECT id, name, password_hash, failed_attempts, locked_until"
        " FROM accounts WHERE name = $1",
        name,
    )
    if row is None:
        return None
    return Account(
        id=as_int(row["id"]),
        name=as_str(row["name"]),
        password_hash=as_str(row["password_hash"]),
        failed_attempts=as_int(row["failed_attempts"]),
        locked_until=as_datetime_or_none(row["locked_until"]),
    )


async def bump_failures(conn: Conn, name: str) -> int:
    async with conn.transaction():
        value: object = await conn.fetchval(
            "SELECT failed_attempts FROM accounts WHERE name = $1 FOR UPDATE", name
        )
        if value is None:
            raise LookupError(name)
        count = as_int(value) + 1
        await conn.execute("UPDATE accounts SET failed_attempts = $1 WHERE name = $2", count, name)
    return count


async def add_refresh_token(
    conn: Conn, token_hash: bytes, account_id: int, expires_at: datetime
) -> None:
    await conn.execute(
        "INSERT INTO refresh_tokens (token_hash, account_id, expires_at) VALUES ($1, $2, $3)",
        token_hash,
        account_id,
        expires_at,
    )


async def delete_refresh_token(conn: Conn, token_hash: bytes) -> bool:
    status = await conn.execute("DELETE FROM refresh_tokens WHERE token_hash = $1", token_hash)
    return status == "DELETE 1"
