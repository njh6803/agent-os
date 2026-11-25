"""제품 마이그레이션 `0002`(운영자 계정의 표 여섯)를 실제 테스트 데이터베이스에 올려 본다.

명세 admin-login "표와 마이그레이션"이 정한 것을 본다. 표 여섯과 시스템 관리자에만 거는 유일 색인이
서고, 시각 칸에 기본값이 없고, `0002`가 보낸 문장이 표와 색인을 만드는 것뿐이다. 서명 키의 표를 먼저
만들어 올리기를 일부러 멈추면 `0002`의 다른 표가 하나도 남지 않는다(올리기가 한 트랜잭션이다).

`0002`가 줄을 넣거나 바꾸지 않으므로 값을 싣는 실패를 일으킬 길이 없다. 그래서 값이 기록에 실리지
않는지를 재는 대신, 보낸 문장의 종류가 규칙을 지키는지를 시험이 가른다.
"""

from __future__ import annotations

import re
import shutil
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import event, text
from sqlalchemy.engine import Connection
from sqlalchemy.engine.interfaces import DBAPICursor
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool
from tests.postgres_support import plain, revisions, tables
from tools.database_for_tests import ScopedDatabase

from agent_os.adapters.postgres.database import (
    MIGRATIONS,
    PRODUCT_VERSIONS,
    PostgresDatabase,
    parse_database_url,
)

OPERATOR_TABLES = {
    "operator_accounts",
    "operator_logins",
    "operator_refresh_tokens",
    "operator_password_links",
    "operator_signing_key",
    "operator_login_records",
}
NOW = datetime(2026, 11, 26, 9, 0, tzinfo=UTC)
# 표와 색인을 만드는 문장의 머리. 아래 시험이 `operator_` 표를 건드린 문장이 이 머리로 시작하는지
# 본다.
CREATING = re.compile(r"\s*CREATE\s+(TABLE|UNIQUE\s+INDEX|INDEX)\b", re.IGNORECASE)


def _config(versions: Path) -> Config:
    """어댑터가 쓰는 alembic 설정과 같은 모양. 어댑터의 비공개 메서드를 부르지 않으려고 다시
    짓는다."""
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS).replace("%", "%%"))
    config.set_main_option("version_locations", str(versions).replace("%", "%%"))
    config.set_main_option("path_separator", "newline")
    return config


async def _sent_statements(database: ScopedDatabase) -> list[str]:
    """빈 데이터베이스에 제품의 마이그레이션을 올리며 데이터베이스에 보낸 문장들."""
    sent: list[str] = []
    engine = create_async_engine(
        database.address.with_database(database.name),
        poolclass=NullPool,
        hide_parameters=True,
    )

    def collect(
        _connection: Connection, _cursor: DBAPICursor, statement: str, *_rest: object
    ) -> None:
        sent.append(statement)

    event.listen(engine.sync_engine, "before_cursor_execute", collect)

    def upgrade(connection: Connection) -> None:
        config = _config(PRODUCT_VERSIONS)
        config.attributes["connection"] = connection
        command.upgrade(config, "head")

    try:
        async with engine.begin() as connection:
            await connection.run_sync(upgrade)
    finally:
        await engine.dispose()
    return sent


async def _rows(database: ScopedDatabase, sql: str) -> Sequence[tuple[str, ...]]:
    async with plain(database) as connection:
        result = await connection.execute(text(sql))
        return [tuple(str(value) for value in row) for row in result.all()]


# --- 표와 색인 -----------------------------------------------------------------------------------


async def test_0002가_표_여섯을_만들고_판이_0002가_된다(database: ScopedDatabase) -> None:
    assert OPERATOR_TABLES <= await tables(database)
    assert await revisions(database) == ["0002"]


async def test_시각을_담는_칸에_기본값이_없다(database: ScopedDatabase) -> None:
    names = ", ".join(f"'{name}'" for name in sorted(OPERATOR_TABLES))
    defaults = await _rows(
        database,
        "SELECT table_name, column_name, column_default FROM information_schema.columns "
        f"WHERE table_schema = 'public' AND table_name IN ({names}) "
        "AND column_default IS NOT NULL",
    )
    assert defaults == []


async def test_시각을_담는_칸은_모두_시간대가_붙은_타입이다(database: ScopedDatabase) -> None:
    names = ", ".join(f"'{name}'" for name in sorted(OPERATOR_TABLES))
    wrong = await _rows(
        database,
        "SELECT table_name, column_name, data_type FROM information_schema.columns "
        f"WHERE table_schema = 'public' AND table_name IN ({names}) "
        "AND (column_name LIKE '%\\_at' OR column_name IN ('locked_until', 'expires_at')) "
        "AND data_type <> 'timestamp with time zone'",
    )
    assert wrong == []


async def test_시스템_관리자는_둘이_될_수_없고_관리자는_여럿이다(database: ScopedDatabase) -> None:
    insert = text(
        "INSERT INTO operator_accounts (name, tier, failures, created_at) "
        "VALUES (:name, :tier, 0, :at)"
    )
    async with plain(database, autocommit=True) as connection:
        await connection.execute(insert, {"name": "root-one", "tier": "system_admin", "at": NOW})
        await connection.execute(insert, {"name": "kim", "tier": "admin", "at": NOW})
        await connection.execute(insert, {"name": "lee", "tier": "admin", "at": NOW})
        with pytest.raises(DBAPIError) as raised:
            await connection.execute(
                insert, {"name": "root-two", "tier": "system_admin", "at": NOW}
            )
    assert getattr(raised.value.orig, "sqlstate", None) == "23505"


async def test_알지_못하는_단계는_데이터베이스가_막는다(database: ScopedDatabase) -> None:
    async with plain(database, autocommit=True) as connection:
        with pytest.raises(DBAPIError) as raised:
            await connection.execute(
                text(
                    "INSERT INTO operator_accounts (name, tier, failures, created_at) "
                    "VALUES ('x-y-z', 'owner', 0, :at)"
                ),
                {"at": NOW},
            )
    assert getattr(raised.value.orig, "sqlstate", None) == "23514"


async def test_서명_키의_표는_한_줄만_받고_키는_32바이트다(database: ScopedDatabase) -> None:
    insert = text("INSERT INTO operator_signing_key (id, key, created_at) VALUES (:id, :key, :at)")
    async with plain(database, autocommit=True) as connection:
        for values in (
            {"id": 2, "key": b"k" * 32, "at": NOW},
            {"id": 1, "key": b"k" * 31, "at": NOW},
        ):
            with pytest.raises(DBAPIError) as raised:
                await connection.execute(insert, values)
            assert getattr(raised.value.orig, "sqlstate", None) == "23514"
        await connection.execute(insert, {"id": 1, "key": b"k" * 32, "at": NOW})
        with pytest.raises(DBAPIError) as again:
            await connection.execute(insert, {"id": 1, "key": b"j" * 32, "at": NOW})
    assert getattr(again.value.orig, "sqlstate", None) == "23505"


# --- 보낸 문장의 종류 ----------------------------------------------------------------------------


async def test_0002가_보낸_문장은_표와_색인을_만드는_것뿐이다(
    empty_database: ScopedDatabase,
) -> None:
    sent = await _sent_statements(empty_database)
    touching = [statement for statement in sent if "operator_" in statement]
    # 일곱째 이후의 문장이 섞이지 않았는지 보려고 개수도 센다: 표 여섯, 색인 여섯(유일 하나 포함)
    # 중 표를 만드는 문장은 여섯이다
    creating_tables = [s for s in touching if re.match(r"\s*CREATE\s+TABLE\b", s, re.IGNORECASE)]
    assert len(creating_tables) == len(OPERATOR_TABLES)
    assert any("UNIQUE INDEX" in s.upper() for s in touching)
    others = [s for s in touching if CREATING.match(s) is None]
    assert others == [], "표와 색인을 만드는 것 말고 `operator_` 표를 건드린 문장이 있다"


async def test_표를_만드는_문장은_줄을_넣지_않는다(empty_database: ScopedDatabase) -> None:
    sent = await _sent_statements(empty_database)
    writing = [
        statement
        for statement in sent
        if re.match(r"\s*(INSERT|UPDATE|DELETE|ALTER|TRUNCATE|COPY)\b", statement, re.IGNORECASE)
        and "alembic_version" not in statement
    ]
    assert writing == []


# --- 올리기가 한 트랜잭션이다 --------------------------------------------------------------------


async def test_표가_이미_있어_멈춘_올리기는_다른_표를_하나도_남기지_않는다(
    empty_database: ScopedDatabase, tmp_path: Path
) -> None:
    only_first = tmp_path / "only_first"
    only_first.mkdir()
    shutil.copy(PRODUCT_VERSIONS / "0001_first.py", only_first / "0001_first.py")
    first_url = parse_database_url(empty_database.address.text_for(empty_database.name))
    assert first_url is not None
    first = PostgresDatabase(first_url, notice=_ignore, versions=only_first)
    try:
        upgraded = await first.migrate()
    finally:
        await first.close()
    assert upgraded.ok, upgraded.message
    assert await revisions(empty_database) == ["0001"]
    async with plain(empty_database, autocommit=True) as connection:
        await connection.execute(text("CREATE TABLE operator_signing_key (id integer)"))

    url = parse_database_url(empty_database.address.text_for(empty_database.name))
    assert url is not None
    adapter = PostgresDatabase(url, notice=_ignore)
    try:
        result = await adapter.migrate()
    finally:
        await adapter.close()

    assert not result.ok
    assert "already exists" in result.message
    assert await revisions(empty_database) == ["0001"]
    assert (await tables(empty_database)) & OPERATOR_TABLES == {"operator_signing_key"}


def _ignore(_message: str) -> None:
    """기다린다는 알림을 찍지 않는다."""
