"""타입 드러내기. 조합마다 드라이버가 돌려준 값을 pyright 가 무슨 타입으로 보는지 찍게 한다.

실행하지 않는다. pyright 가 `reveal_type` 마다 내는 정보 줄을 `run.py` 가 모은다. `Any` 로 드러난
자리는 pyright strict 가 통과시키지만 타입이 지켜지지 않는 자리이고, 조합 모듈은 그 값을
`model.py` 의 도우미로 좁힌다.
"""

from __future__ import annotations

from typing import reveal_type

import asyncpg
import psycopg
from model import Account
from psycopg.rows import TupleRow, class_row
from sa_tables import ACCOUNT_ID, ACCOUNT_LOCKED_UNTIL, ACCOUNT_NAME, accounts
from sqlalchemy import Connection, select, text


def psycopg_rows(conn: psycopg.Connection[TupleRow]) -> None:
    reveal_type(conn.execute("SELECT 1").fetchone())
    with conn.cursor(row_factory=class_row(Account)) as cursor:
        reveal_type(cursor.fetchone())


async def asyncpg_rows(conn: asyncpg.Connection[asyncpg.Record]) -> None:
    row = await conn.fetchrow("SELECT 1 AS one")
    reveal_type(row)
    if row is not None:
        reveal_type(row["one"])
    reveal_type(await conn.fetchval("SELECT 1"))


def sqlalchemy_rows(conn: Connection) -> None:
    reveal_type(conn.execute(select(ACCOUNT_ID, ACCOUNT_NAME, ACCOUNT_LOCKED_UNTIL)).one())
    reveal_type(conn.execute(select(ACCOUNT_ID)).scalar_one())
    reveal_type(conn.execute(select(accounts.c.id)).scalar_one())
    reveal_type(conn.execute(text("SELECT 1")).scalar_one())
