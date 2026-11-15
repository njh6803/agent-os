"""조합: SQLAlchemy 2 Core 동기 엔진. 드라이버는 URL 이 고른다(`postgresql+psycopg://`)."""

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
from sqlalchemy import Engine, create_engine, delete, insert, select, text, update


def make_engine(url: str, *, size: int = 2) -> Engine:
    return create_engine(url, pool_size=size, max_overflow=0)


def server_version(engine: Engine) -> str:
    with engine.connect() as conn:
        return as_str(conn.execute(text("SHOW server_version")).scalar_one())


def add_account(engine: Engine, name: str, password_hash: str) -> int:
    with engine.begin() as conn:
        created = conn.execute(
            insert(accounts)
            .values(name=name, password_hash=password_hash, failed_attempts=0)
            .returning(ACCOUNT_ID)
        )
        return created.scalar_one()


def find_account(engine: Engine, name: str) -> Account | None:
    query = select(
        ACCOUNT_ID,
        ACCOUNT_NAME,
        ACCOUNT_PASSWORD_HASH,
        ACCOUNT_FAILED_ATTEMPTS,
        ACCOUNT_LOCKED_UNTIL,
    ).where(ACCOUNT_NAME == name)
    with engine.connect() as conn:
        row = conn.execute(query).one_or_none()
    if row is None:
        return None
    # SQLAlchemy 2.1 의 `Row` 는 바로 풀린다. `Row.tuple()` 은 2.0.19 부터, `Row._tuple()` 은 2.1.0
    # 부터 폐기 경고다(이 프로브의 첫 판이 `tuple()` 을 써서 pytest 가 그 경고를 냈다).
    account_id, account_name, password_hash, failed_attempts, locked_until = row
    return Account(
        id=account_id,
        name=account_name,
        password_hash=password_hash,
        failed_attempts=failed_attempts,
        locked_until=as_datetime_or_none(locked_until),
    )


def bump_failures(engine: Engine, name: str) -> int:
    with engine.begin() as conn:
        current = conn.execute(
            select(ACCOUNT_FAILED_ATTEMPTS).where(ACCOUNT_NAME == name).with_for_update()
        ).scalar_one()
        count = current + 1
        conn.execute(update(accounts).where(ACCOUNT_NAME == name).values(failed_attempts=count))
    return count


def add_refresh_token(
    engine: Engine, token_hash: bytes, account_id: int, expires_at: datetime
) -> None:
    with engine.begin() as conn:
        conn.execute(
            insert(refresh_tokens).values(
                token_hash=token_hash, account_id=account_id, expires_at=expires_at
            )
        )


def delete_refresh_token(engine: Engine, token_hash: bytes) -> bool:
    with engine.begin() as conn:
        deleted = conn.execute(delete(refresh_tokens).where(TOKEN_HASH == token_hash))
        return deleted.rowcount == 1
