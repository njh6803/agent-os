"""조합: psycopg 3 비동기 모드. 연결은 psycopg_pool 의 비동기 풀에서 빌린다."""

from __future__ import annotations

from datetime import datetime

import psycopg
from model import Account, as_int
from psycopg.rows import TupleRow, class_row
from psycopg_pool import AsyncConnectionPool

type Conn = psycopg.AsyncConnection[TupleRow]
type Pool = AsyncConnectionPool[Conn]


async def connect(dsn: str) -> Conn:
    return await psycopg.AsyncConnection.connect(dsn, autocommit=True)


def make_pool(dsn: str, *, size: int = 2, timeout: float = 10.0) -> Pool:
    """닫힌 풀을 만든다. 여는 것은 `await pool.open(wait=True)` 다. timeout 은 연결을 빌릴 때와
    처음 채울 때 기다리는 초다."""
    return AsyncConnectionPool(
        dsn,
        min_size=size,
        max_size=size,
        open=False,
        timeout=timeout,
        kwargs={"autocommit": True},
    )


def server_version(conn: Conn) -> str:
    return conn.info.parameter_status("server_version") or ""


async def add_account(conn: Conn, name: str, password_hash: str) -> int:
    cursor = await conn.execute(
        "INSERT INTO accounts (name, password_hash) VALUES (%s, %s) RETURNING id",
        (name, password_hash),
    )
    row = await cursor.fetchone()
    if row is None:
        raise LookupError(name)
    return as_int(row[0])


async def find_account(conn: Conn, name: str) -> Account | None:
    async with conn.cursor(row_factory=class_row(Account)) as cursor:
        await cursor.execute(
            "SELECT id, name, password_hash, failed_attempts, locked_until"
            " FROM accounts WHERE name = %s",
            (name,),
        )
        return await cursor.fetchone()


async def bump_failures(conn: Conn, name: str) -> int:
    async with conn.transaction():
        cursor = await conn.execute(
            "SELECT failed_attempts FROM accounts WHERE name = %s FOR UPDATE", (name,)
        )
        row = await cursor.fetchone()
        if row is None:
            raise LookupError(name)
        count = as_int(row[0]) + 1
        await conn.execute(
            "UPDATE accounts SET failed_attempts = %s WHERE name = %s", (count, name)
        )
    return count


async def add_refresh_token(
    conn: Conn, token_hash: bytes, account_id: int, expires_at: datetime
) -> None:
    await conn.execute(
        "INSERT INTO refresh_tokens (token_hash, account_id, expires_at) VALUES (%s, %s, %s)",
        (token_hash, account_id, expires_at),
    )


async def delete_refresh_token(conn: Conn, token_hash: bytes) -> bool:
    deleted = await conn.execute("DELETE FROM refresh_tokens WHERE token_hash = %s", (token_hash,))
    return deleted.rowcount == 1
