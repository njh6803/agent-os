"""계정 어댑터가 읽고 쓰는 표의 SQLAlchemy 정의.

SQL 을 글로 적지 않고 표 정의로 지으면 칸마다 타입이 붙어, 칸의 차례를 틀린 행 풀기를 pyright 가
잡는다. 비어 있을 수 있는 칸은 타입 인자에 `None` 을 함께 적는다. 비어도 된다는
표시(`nullable=True`)만 적으면 읽은 값의 타입에서 `None` 이 빠진다. 쓰기의 값 넣기(`values(...)`)는
칸 이름과 값을 타입 검사가 보지 않으므로, 표 정의와 실제 표(마이그레이션)가 맞는지와 쓰기의 칸
이름은 진짜 데이터베이스에 대고 도는 시험이 본다(`tests/adapters/test_postgres_accounts.py`).

마이그레이션(`0002`)이 표의 원천이다. 이 정의는 표 셋(계정, 로그인, 로그인 기록)만 들고 칸은 표마다
모두 적는다. 칸 이름과 타입을 실제 표와 견주는 시험이 표 전체를 보기 때문이다. 서명 키, 갱신용 번호,
비밀번호 링크의 표는 그 표를 읽고 쓰는 티켓이 이 모듈에 더한다. 시각 칸에는 기본값을 두지 않는다.
시각은 부르는 쪽이 시계에서 읽어 넘긴다.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Identity,
    Integer,
    MetaData,
    Table,
    Text,
    Uuid,
)

metadata = MetaData()

ACCOUNT_NAME = Column("name", Text, nullable=False)
ACCOUNT_TIER = Column("tier", Text, nullable=False)
ACCOUNT_PASSWORD_HASH: Column[str | None] = Column("password_hash", Text, nullable=True)
ACCOUNT_DISABLED_AT: Column[datetime | None] = Column(
    "disabled_at", DateTime(timezone=True), nullable=True
)
ACCOUNT_FAILURES = Column("failures", Integer, nullable=False)
ACCOUNT_LOCKED_UNTIL: Column[datetime | None] = Column(
    "locked_until", DateTime(timezone=True), nullable=True
)
ACCOUNT_CREATED_AT = Column("created_at", DateTime(timezone=True), nullable=False)
ACCOUNTS = Table(
    "operator_accounts",
    metadata,
    ACCOUNT_NAME,
    ACCOUNT_TIER,
    ACCOUNT_PASSWORD_HASH,
    ACCOUNT_DISABLED_AT,
    ACCOUNT_FAILURES,
    ACCOUNT_LOCKED_UNTIL,
    ACCOUNT_CREATED_AT,
)

LOGIN_ID = Column("id", Uuid, nullable=False)
LOGIN_ACCOUNT = Column("account", Text, nullable=False)
LOGIN_LOGGED_IN_AT = Column("logged_in_at", DateTime(timezone=True), nullable=False)
LOGIN_REFRESHED_AT = Column("refreshed_at", DateTime(timezone=True), nullable=False)
LOGIN_ENDED_AT: Column[datetime | None] = Column("ended_at", DateTime(timezone=True), nullable=True)
LOGINS = Table(
    "operator_logins",
    metadata,
    LOGIN_ID,
    LOGIN_ACCOUNT,
    LOGIN_LOGGED_IN_AT,
    LOGIN_REFRESHED_AT,
    LOGIN_ENDED_AT,
)

RECORD_SEQ = Column("seq", BigInteger, Identity(), nullable=False)
RECORD_OCCURRED_AT = Column("occurred_at", DateTime(timezone=True), nullable=False)
RECORD_KIND = Column("kind", Text, nullable=False)
RECORD_ACCOUNT: Column[str | None] = Column("account", Text, nullable=True)
RECORD_ACTOR: Column[str | None] = Column("actor", Text, nullable=True)
RECORD_ADDRESS: Column[str | None] = Column("address", Text, nullable=True)
LOGIN_RECORDS = Table(
    "operator_login_records",
    metadata,
    RECORD_SEQ,
    RECORD_OCCURRED_AT,
    RECORD_KIND,
    RECORD_ACCOUNT,
    RECORD_ACTOR,
    RECORD_ADDRESS,
)
