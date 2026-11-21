"""패키지 B 의 시험 80 개. 받은 데이터베이스에 붙어 줄 하나를 넣고 읽는다.

파일 이름이 패키지 A 의 시험과 같다. import 모드가 importlib 이라 함께 모인다.
"""

from __future__ import annotations

import time

import pytest
from pkg_b.database import HEAD, TABLES, create_engine, widgets
from sqlalchemy import insert, select, text
from tests.database import Database

CASES = 80


@pytest.mark.parametrize("case", range(CASES))
async def test_widget_round_trip(database: Database, case: int) -> None:
    started = time.perf_counter()
    engine = create_engine(database.url)
    try:
        async with engine.begin() as connection:
            await connection.execute(insert(widgets).values(slug=f"widget-{case}", title="x"))
            first_query = time.perf_counter() - started
            slugs = list((await connection.execute(select(widgets.c.slug))).scalars())
            found = await connection.execute(
                text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
            )
            tables = sorted(str(row[0]) for row in found)
            version = await connection.execute(text("SELECT version_num FROM alembic_version"))
            versions = [str(row[0]) for row in version]
    finally:
        await engine.dispose()
    database.record.update(
        first_query_s=first_query, tables=tables, versions=versions, rows=len(slugs)
    )
    assert slugs == [f"widget-{case}"]
    assert set(tables) == TABLES | {"alembic_version"}
    assert versions == [HEAD]
