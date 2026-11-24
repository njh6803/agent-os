"""계정 포트의 PostgreSQL 구현. 프로브(`port_shape_async`)가 임시 사본의 어댑터 층에만 둔다.

제품 코드가 아니다. `agent_os.http` 를 가져오지 않는다. 줄(`Row`)과 받는 값(`Incoming`)을 이
모듈이 스스로 적는다. 쿼리는 SQLAlchemy Core 의 `Table` 이고, 칸을 이름에 묶어 `select` 에 넣으면
행의 칸이 타입을 지닌다. NULL 을 받는 칸은 `Column[... | None]` 으로 적어 `None` 을 타입에 싣는다.

엔진을 받는 모양은 둘이다. (가) `PostgresDatabase` 가 아래 함수들을 자기 엔진으로 부른다(임시 사본의
`database.py` 끝에 붙인다). (나) 같은 엔진을 받는 `PostgresAccounts` 를 조립이 만든다.

'이름이 이미 있음'의 갈래 넷은 `agent_os.http.accounts` 의 독스트링이 적는다. 유일 제약 위반은
예외의 클래스가 아니라 PostgreSQL 의 오류 번호(23505)로 알아본다. 포트에 내는 예외는 `except` 밖에서
던져 원인(`__cause__`)과 문맥(`__context__`)을 잇지 않는다. 드라이버(asyncpg)가 낸 원래 예외의
글에는 서버가 낸 DETAIL 이 들어 넣으려던 값이 실리고, 그것을 감싼 SQLAlchemy 예외의 글에는 없다
(`drive.py` 의 DETAIL 사례).
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol

from agent_os.core.conflicts import NameTaken as CoreNameTaken
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    MetaData,
    Select,
    Table,
    Text,
    insert,
    select,
    update,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine

type Tier = Literal["system_admin", "admin"]

UNIQUE_VIOLATION = "23505"
LOCK_AFTER = 2

metadata = MetaData()
NAME = Column("name", Text, nullable=False, unique=True)
TIER = Column("tier", Text, nullable=False)
PASSWORD_HASH: Column[str | None] = Column("password_hash", Text, nullable=True)
FAILURES = Column("failures", Integer, nullable=False)
LOCKED_UNTIL: Column[datetime | None] = Column(
    "locked_until", DateTime(timezone=True), nullable=True
)
accounts = Table("accounts", metadata, NAME, TIER, PASSWORD_HASH, FAILURES, LOCKED_UNTIL)


@dataclass(frozen=True, slots=True)
class Row:
    name: str
    tier: Tier
    password_hash: str | None
    failures: int
    locked_until: datetime | None


class Incoming(Protocol):
    @property
    def name(self) -> str: ...

    @property
    def tier(self) -> Tier: ...


class AdapterNameTaken(Exception):
    """알아보기 갈래에서 어댑터가 던지는 자기 예외."""


def as_tier(value: str) -> Tier:
    if value == "system_admin":
        return "system_admin"
    if value == "admin":
        return "admin"
    raise ValueError("모르는 단계다")


def _is_unique_violation(error: BaseException) -> bool:
    current: BaseException | None = error
    seen: list[BaseException] = []
    while current is not None and all(current is not item for item in seen):
        if getattr(current, "sqlstate", None) == UNIQUE_VIOLATION:
            return True
        seen.append(current)
        current = current.__cause__ or current.__context__
    return False


def _query() -> Select[str, str, str | None, int, datetime | None]:
    return select(NAME, TIER, PASSWORD_HASH, FAILURES, LOCKED_UNTIL)


async def find_row(engine: AsyncEngine, name: str) -> Row | None:
    async with engine.connect() as connection:
        found = (await connection.execute(_query().where(NAME == name))).one_or_none()
    if found is None:
        return None
    row_name, tier, password_hash, failures, locked_until = found
    return Row(row_name, as_tier(tier), password_hash, failures, locked_until)


async def list_rows(engine: AsyncEngine) -> list[Row]:
    async with engine.connect() as connection:
        found = (await connection.execute(_query().order_by(NAME))).all()
    rows: list[Row] = []
    for row_name, tier, password_hash, failures, locked_until in found:
        rows.append(Row(row_name, as_tier(tier), password_hash, failures, locked_until))
    return rows


async def bump_failure(engine: AsyncEngine, name: str, *, at: datetime) -> None:
    async with engine.begin() as connection:
        await connection.execute(update(accounts).where(NAME == name).values(failures=FAILURES + 1))
        await connection.execute(
            update(accounts).where(NAME == name, FAILURES >= LOCK_AFTER).values(locked_until=at)
        )


async def insert_row(engine: AsyncEngine, account: Incoming) -> Row | None:
    """넣은 줄. 이름이 이미 있으면 `None`. 다른 실패는 그대로 올린다."""
    statement = (
        insert(accounts)
        .values(name=account.name, tier=account.tier, failures=0)
        .returning(NAME, TIER, PASSWORD_HASH, FAILURES, LOCKED_UNTIL)
    )
    try:
        async with engine.begin() as connection:
            created = (await connection.execute(statement)).one()
    except IntegrityError as error:
        if not _is_unique_violation(error):
            raise
        return None
    row_name, tier, password_hash, failures, locked_until = created
    return Row(row_name, as_tier(tier), password_hash, failures, locked_until)


class _Reads:
    """찾기, 목록, 실패 적기. 갈래마다의 클래스가 함께 쓴다."""

    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    async def find(self, name: str) -> Row | None:
        return await find_row(self._engine, name)

    async def list_all(self) -> Sequence[Row]:
        return await list_rows(self._engine)

    async def record_failure(self, name: str, *, at: datetime) -> None:
        await bump_failure(self._engine, name, at=at)


class PostgresAccounts(_Reads):
    """(나) 같은 엔진을 받는 별도 어댑터이자 core 갈래. 이름이 이미 있으면
    `agent_os.core.conflicts.NameTaken` 을 던진다."""

    async def add(self, account: Incoming) -> Row:
        row = await insert_row(self._engine, account)
        if row is None:
            raise CoreNameTaken(account.name)
        return row


class InjectedTakenAccounts(_Reads):
    """주입 갈래. 조립이 넘긴 만드는 법으로 예외를 짓는다."""

    def __init__(self, engine: AsyncEngine, *, taken: Callable[[str], Exception]) -> None:
        super().__init__(engine)
        self._taken = taken

    async def add(self, account: Incoming) -> Row:
        row = await insert_row(self._engine, account)
        if row is None:
            raise self._taken(account.name)
        return row


class RecognizedTakenAccounts(_Reads):
    """알아보기 갈래. 자기 예외를 던지고 포트의 물음에 답한다."""

    async def add(self, account: Incoming) -> Row:
        row = await insert_row(self._engine, account)
        if row is None:
            raise AdapterNameTaken()
        return row

    def is_name_taken(self, error: Exception) -> bool:
        return isinstance(error, AdapterNameTaken)


class ResultTakenAccounts(_Reads):
    """값 갈래. 이름이 이미 있으면 `"taken"` 을 돌려준다."""

    async def add(self, account: Incoming) -> Row | Literal["taken"]:
        row = await insert_row(self._engine, account)
        return "taken" if row is None else row


class UntranslatedAccounts(_Reads):
    """대조군. 유일 제약 위반을 옮기지 않고 SQLAlchemy 의 예외를 그대로 올린다.

    포트의 시그니처는 모두 맞으므로 타입 검사는 이 어긋남을 보지 못한다(프로브가 본다).
    """

    async def add(self, account: Incoming) -> Row:
        statement = (
            insert(accounts)
            .values(name=account.name, tier=account.tier, failures=0)
            .returning(NAME, TIER, PASSWORD_HASH, FAILURES, LOCKED_UNTIL)
        )
        async with self._engine.begin() as connection:
            created = (await connection.execute(statement)).one()
        row_name, tier, password_hash, failures, locked_until = created
        return Row(row_name, as_tier(tier), password_hash, failures, locked_until)

    def is_name_taken(self, error: Exception) -> bool:
        return isinstance(error, AdapterNameTaken)
