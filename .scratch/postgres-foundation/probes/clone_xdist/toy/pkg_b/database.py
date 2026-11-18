"""패키지 B 의 데이터베이스 코드. 표의 정의, 엔진, 마이그레이션을 적용하는 함수다.

패키지 A 의 `database.py` 와 같은 꼴이지만 코드를 나눠 쓰지 않는다(두 패키지는 서로를 import 하지
못한다). 표 이름은 A 와 겹치지 않는다.
"""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import (
    BigInteger,
    Column,
    Connection,
    DateTime,
    ForeignKey,
    Identity,
    MetaData,
    Table,
    Text,
)
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

MIGRATIONS = Path(__file__).resolve().parent / "migrations"
HEAD = "0001"
TABLES = frozenset({"widgets", "widget_origins"})

metadata = MetaData()

widgets = Table(
    "widgets",
    metadata,
    Column("id", BigInteger, Identity(always=True), primary_key=True),
    Column("slug", Text, nullable=False, unique=True),
    Column("title", Text, nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=True),
)

widget_origins = Table(
    "widget_origins",
    metadata,
    Column("id", BigInteger, Identity(always=True), primary_key=True),
    Column("widget_id", BigInteger, ForeignKey("widgets.id", ondelete="CASCADE"), nullable=False),
    Column("origin", Text, nullable=False),
)


def create_engine(url: str) -> AsyncEngine:
    return create_async_engine(url)


def upgrade(connection: Connection) -> None:
    """받은 연결로 `upgrade head` 를 돈다. 커밋은 연결을 연 쪽의 몫이다."""
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS).replace("%", "%%"))
    config.attributes["connection"] = connection
    command.upgrade(config, "head")
