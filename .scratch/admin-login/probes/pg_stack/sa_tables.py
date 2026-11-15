"""SQLAlchemy 2 Core 의 표 정의. 동기·비동기 조합 모듈이 함께 쓴다.

열을 표 밖의 이름으로 먼저 만든다. `accounts.c.id` 로 꺼낸 열은 타입이 `Column[Any]` 이지만, 이름에
묶은 열은 `Column[int]` 처럼 값의 타입을 지닌다(README 의 타입 드러내기 절).
"""

from __future__ import annotations

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    MetaData,
    Table,
    Text,
)

metadata = MetaData()

ACCOUNT_ID = Column("id", BigInteger, primary_key=True)
ACCOUNT_NAME = Column("name", Text, nullable=False, unique=True)
ACCOUNT_PASSWORD_HASH = Column("password_hash", Text, nullable=False)
ACCOUNT_FAILED_ATTEMPTS = Column("failed_attempts", Integer, nullable=False)
ACCOUNT_LOCKED_UNTIL = Column("locked_until", DateTime(timezone=True), nullable=True)

accounts = Table(
    "accounts",
    metadata,
    ACCOUNT_ID,
    ACCOUNT_NAME,
    ACCOUNT_PASSWORD_HASH,
    ACCOUNT_FAILED_ATTEMPTS,
    ACCOUNT_LOCKED_UNTIL,
)

TOKEN_HASH = Column("token_hash", LargeBinary, primary_key=True)
TOKEN_ACCOUNT_ID = Column("account_id", BigInteger, ForeignKey("accounts.id"), nullable=False)
TOKEN_EXPIRES_AT = Column("expires_at", DateTime(timezone=True), nullable=False)

refresh_tokens = Table("refresh_tokens", metadata, TOKEN_HASH, TOKEN_ACCOUNT_ID, TOKEN_EXPIRES_AT)
