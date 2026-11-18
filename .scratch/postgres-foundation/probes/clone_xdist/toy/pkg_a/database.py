"""패키지 A 의 데이터베이스 코드. 표의 정의, 엔진, 마이그레이션을 적용하는 함수다.

마이그레이션은 `alembic.ini` 없이 설정을 코드로 짓고, 받은 연결을 `config.attributes` 에 넣어
`migrations/env.py` 가 그 연결을 그대로 쓰게 한다. 이 함수는 동기 함수이고 연결도 동기 연결이다.
비동기 엔진을 쓰는 쪽은 `await connection.run_sync(upgrade)` 로 부른다. `env.py` 가 `asyncio.run` 을
부르지 않으므로 이미 도는 이벤트 루프 안에서도 부를 수 있다.
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
    Integer,
    LargeBinary,
    MetaData,
    Table,
    Text,
)
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

MIGRATIONS = Path(__file__).resolve().parent / "migrations"
HEAD = "0001"
TABLES = frozenset({"accounts", "refresh_tokens", "login_attempts"})

metadata = MetaData()

accounts = Table(
    "accounts",
    metadata,
    Column("id", BigInteger, Identity(always=True), primary_key=True),
    Column("name", Text, nullable=False, unique=True),
    Column("password_hash", Text, nullable=False),
    Column("failed_attempts", Integer, nullable=False, server_default="0"),
    Column("locked_until", DateTime(timezone=True), nullable=True),
)

refresh_tokens = Table(
    "refresh_tokens",
    metadata,
    Column("token_hash", LargeBinary, primary_key=True),
    Column("account_id", BigInteger, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False),
    Column("expires_at", DateTime(timezone=True), nullable=False),
)


def create_engine(url: str) -> AsyncEngine:
    return create_async_engine(url)


def upgrade(connection: Connection) -> None:
    """받은 연결로 `upgrade head` 를 돈다. 커밋은 연결을 연 쪽의 몫이다."""
    config = Config()
    config.set_main_option("script_location", str(MIGRATIONS).replace("%", "%%"))
    config.attributes["connection"] = connection
    command.upgrade(config, "head")
