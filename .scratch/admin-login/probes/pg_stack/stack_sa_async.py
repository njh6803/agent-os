"""조합: SQLAlchemy 2 Core 비동기 엔진. 드라이버는 URL 이 고른다
(`postgresql+psycopg://` 또는 `postgresql+asyncpg://`)."""

from __future__ import annotations

from datetime import datetime

from model import Account, as_datetime_or_none, as_str
from sa_tables import (
    ACCOUNT_FAILED_ATTEMPTS,
    ACCOUNT_ID,
    ACCOUNT_LOCKED_UNTIL,
    ACCOUNT_NAME,
    ACCOUNT_PASSWORD_HASH,
    TOKEN_HASH,
    accounts,
    refresh_tokens,
)
from sqlalchemy import delete, insert, select, text, update
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


def make_engine(url: str, *, size: int = 2) -> AsyncEngine:
    return create_async_engine(url, pool_size=size, max_overflow=0)


async def server_version(engine: AsyncEngine) -> str:
    async with engine.connect() as conn:
        return as_str((await conn.execute(text("SHOW server_version"))).scalar_one())


async def add_account(engine: AsyncEngine, name: str, password_hash: str) -> int:
    async with engine.begin() as conn:
        created = await conn.execute(
            insert(accounts)
            .values(name=name, password_hash=password_hash, failed_attempts=0)
            .returning(ACCOUNT_ID)
        )
        return created.scalar_one()


async def find_account(engine: AsyncEngine, name: str) -> Account | None:
    query = select(
        ACCOUNT_ID,
        ACCOUNT_NAME,
        ACCOUNT_PASSWORD_HASH,
        ACCOUNT_FAILED_ATTEMPTS,
        ACCOUNT_LOCKED_UNTIL,
    ).where(ACCOUNT_NAME == name)
    async with engine.connect() as conn:
        row = (await conn.execute(query)).one_or_none()
    if row is None:
        return None
    account_id, account_name, password_hash, failed_attempts, locked_until = row
    return Account(
        id=account_id,
        name=account_name,
        password_hash=password_hash,
        failed_attempts=failed_attempts,
        locked_until=as_datetime_or_none(locked_until),
    )


async def bump_failures(engine: AsyncEngine, name: str) -> int:
    async with engine.begin() as conn:
        current = (
            await conn.execute(
                select(ACCOUNT_FAILED_ATTEMPTS).where(ACCOUNT_NAME == name).with_for_update()
            )
        ).scalar_one()
        count = current + 1
        await conn.execute(
            update(accounts).where(ACCOUNT_NAME == name).values(failed_attempts=count)
        )
    return count


async def add_refresh_token(
    engine: AsyncEngine, token_hash: bytes, account_id: int, expires_at: datetime
) -> None:
    async with engine.begin() as conn:
        await conn.execute(
            insert(refresh_tokens).values(
                token_hash=token_hash, account_id=account_id, expires_at=expires_at
            )
        )


async def delete_refresh_token(engine: AsyncEngine, token_hash: bytes) -> bool:
    async with engine.begin() as conn:
        deleted = await conn.execute(delete(refresh_tokens).where(TOKEN_HASH == token_hash))
        return deleted.rowcount == 1
