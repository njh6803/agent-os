"""PostgreSQL 어댑터와 `migrate` 명령의 시험이 함께 쓰는 도우미.

시험용 마이그레이션 폴더(`tests/adapters/postgres_versions/`의 9001, 9002)를 복사하고, 시험이
어댑터와 따로 데이터베이스를 들여다보는 연결과 질문을 모았다. 제품 폴더 밖이라 휠에 들지 않는다.
"""

from __future__ import annotations

import shutil
import socket
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine
from sqlalchemy.pool import NullPool
from tools.database_for_tests import ScopedDatabase

# `serve` 와 `migrate` 가 주소를 못 읽을 때 찍는 두 글(명세 postgres-foundation "멈출 때의 글").
# 두 명령의 시험이 글자까지 같은 글을 단언한다.
NO_URL = (
    "AGENT_OS_DATABASE_URL 이 비어 있습니다. serve 와 migrate 는 PostgreSQL 데이터베이스가 있어야"
    " 돕니다(ADR 0066).\n"
    "  단독 배포에서는 compose 가 .env 의 AGENT_OS_DATABASE_PASSWORD 로 이 값을 짓습니다."
    " 개발 PC 의 값은 README 에 있습니다.\n"
)
UNREADABLE_URL = (
    "AGENT_OS_DATABASE_URL 을 읽지 못했습니다."
    " postgresql://계정:비밀번호@호스트:포트/데이터베이스 꼴이어야 합니다.\n"
    "  값에는 비밀번호가 들어 있어 여기 찍지 않습니다. 비밀번호에 @ 가 들면 주소를 읽지 못하므로,"
    " 비밀번호는 영문자와 숫자만 씁니다.\n"
)

VERSIONS = Path(__file__).parent / "adapters" / "postgres_versions"
FIRST = "9001_first_probe.py"
SECOND = "9002_second_probe.py"

# 표 하나를 만든 뒤, 표지 글자를 바인드 값으로 넘기는 문장이 데이터베이스에서 실패하는 셋째
# 마이그레이션. 서버는 0으로 나누기의 글에 값을 싣지 않는다. 표지는 호출 줄이 아니라 상수 줄에만
# 있어 역추적에 찍히는 코드 줄에 실리지 않는다.
BROKEN = """\
from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision: str = "9003"
down_revision: str | None = "9002"
MARKER = "{marker}"


def upgrade() -> None:
    op.create_table("probe_three", sa.Column("id", sa.Integer(), nullable=False))
    statement = sa.text("SELECT CAST(:marker AS text), 1 / :zero")
    op.execute(statement.bindparams(marker=MARKER, zero=0))
"""


def copy_versions(destination: Path, *names: str) -> Path:
    """시험용 마이그레이션 파일 몇 개를 새 폴더에 복사한다."""
    destination.mkdir()
    for name in names:
        shutil.copy(VERSIONS / name, destination / name)
    return destination


def broken_versions(destination: Path, marker: str) -> Path:
    """9001, 9002에 실패하는 9003을 더한 폴더."""
    copy_versions(destination, FIRST, SECOND)
    source = BROKEN.format(marker=marker)
    (destination / "9003_broken_probe.py").write_text(source, encoding="utf-8")
    return destination


def closed_port() -> int:
    """지금 아무것도 듣지 않는 포트."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


@asynccontextmanager
async def plain(
    database: ScopedDatabase, *, autocommit: bool = False, name: str | None = None
) -> AsyncGenerator[AsyncConnection]:
    """시험이 직접 쓰는 연결. 어댑터와 따로 연다."""
    engine = create_async_engine(
        database.address.with_database(name or database.name),
        poolclass=NullPool,
        isolation_level="AUTOCOMMIT" if autocommit else "READ COMMITTED",
    )
    try:
        async with engine.connect() as connection:
            yield connection
    finally:
        await engine.dispose()


async def strings(database: ScopedDatabase, sql: str) -> list[str]:
    async with plain(database) as connection:
        result = await connection.execute(text(sql))
        return [str(value) for value in result.scalars().all()]


async def tables(database: ScopedDatabase) -> set[str]:
    sql = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"
    return set(await strings(database, sql))


async def revisions(database: ScopedDatabase) -> list[str]:
    """판 기록 표의 줄. 표가 없으면 빈 목록이다."""
    if "alembic_version" not in await tables(database):
        return []
    return await strings(database, "SELECT version_num FROM alembic_version")


async def other_connections(database: ScopedDatabase) -> int:
    """이 데이터베이스에 시험의 확인 연결 말고 남은 연결의 수."""
    async with plain(database) as connection:
        result = await connection.execute(
            text(
                "SELECT count(*) FROM pg_stat_activity "
                "WHERE datname = :name AND pid <> pg_backend_pid()"
            ),
            {"name": database.name},
        )
        return int(result.scalar_one())
