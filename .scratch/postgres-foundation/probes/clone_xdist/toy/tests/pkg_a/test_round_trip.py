"""패키지 A 의 시험 240 개. 받은 데이터베이스에 붙어 줄 하나를 넣고 읽는다.

시험마다 잰 것(붙어서 첫 질의가 끝나기까지의 초)과 본 것(표 이름, 표의 판)을 `database.record` 에
얹는다. 읽은 줄이 자기가 넣은 하나뿐이라는 단언이 데이터베이스가 시험마다 새것임을 본다.
"""

from __future__ import annotations

import time

import pytest
from pkg_a.database import HEAD, TABLES, accounts, create_engine
from sqlalchemy import insert, select, text
from tests.database import Database

CASES = 240


@pytest.mark.parametrize("case", range(CASES))
async def test_account_round_trip(database: Database, case: int) -> None:
    started = time.perf_counter()
    engine = create_engine(database.url)
    try:
        async with engine.begin() as connection:
            await connection.execute(
                insert(accounts).values(name=f"user-{case}", password_hash="x")
            )
            first_query = time.perf_counter() - started
            names = list((await connection.execute(select(accounts.c.name))).scalars())
            found = await connection.execute(
                text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
            )
            tables = sorted(str(row[0]) for row in found)
            version = await connection.execute(text("SELECT version_num FROM alembic_version"))
            versions = [str(row[0]) for row in version]
    finally:
        await engine.dispose()
    database.record.update(
        first_query_s=first_query, tables=tables, versions=versions, rows=len(names)
    )
    assert names == [f"user-{case}"]
    assert set(tables) == TABLES | {"alembic_version"}
    assert versions == [HEAD]
