"""계정 저장소의 PostgreSQL 구현(포트는 `agent_os.http.accounts`의 `AccountStore`).

이 모듈은 포트를 가져오지도 상속하지도 않는다. 시그니처(메서드의 이름과 인자와 돌려주는 타입)로
만족한다(원칙 IV. 어댑터는 `agent_os.http`를 가져오지 못한다). 줄은 이 모듈이 자기 타입
(`AccountRecord`)으로 낸다. 어긋나면 포트 타입을 적은 시험 픽스처와 조립하는 `main`의 타입 검사가
잡는다.

**이름 충돌은 돌려주는 값으로 가른다.** 넣는 메서드(`add`)는 이름이 이미 있거나 시스템 관리자가 이미
있어 유일 제약(오류 번호 23505)에 걸리면 글자 값 `"taken"`을 돌려준다. 넣기는 SAVEPOINT 안에서 해서,
그 위반이 트랜잭션을 망가뜨리지 않고 부르는 쪽이 같은 트랜잭션에서 다시 읽을 수 있다. 같은 이름을
동시에 넣는 두 명령은 하나가 `"taken"`을 받고 다시 읽어 이긴 쪽의 줄을 본다.

**원래 예외를 원인으로 잇지 않는다.** 서버가 낸 유일 제약 위반의 DETAIL 에는 넣으려던 값이 실려
(`Key (name)=(값) already exists.`), 그 예외를 원인(`__cause__`)이나 문맥(`__context__`)으로 이은
역추적에 계정 이름이 실린다(프로브 `port_shape_async`가 쟀다). 그래서 데이터베이스가 낸 그 밖의
예외도 포트 밖으로 낼 때 `AccountStoreError` 하나로 바꾸고, 그 예외는 `except` 블록 밖에서 던져
원인과 문맥이 모두 빈다. 오류 번호만 `sqlstate` 속성에 싣는다(`reason_of`가 그 번호로 까닭을
말한다).

**시각은 받아서 적는다.** 이 모듈은 SQL의 `now()`도 칸의 기본값도 쓰지 않는다. 시각은 모두 부르는
쪽이 시계에서 읽어 넘긴 값이다. 그래야 시험의 가짜 시계가 그 칸을 움직인다.

**줄을 잠그고 읽는다(`SELECT ... FOR UPDATE`).** 판정의 규칙은 `http`가 갖고 이 모듈은 줄을 잠그고
읽고 적는 일만 한다. 시스템 관리자가 아직 없을 때는 잠글 줄이 없어, 둘이 동시에 만들면 둘 다 없다고
읽는다. 그때는 시스템 관리자에만 거는 유일 색인이 하나를 `"taken"`으로 막는다.

알려진 한계: 요청이 취소될 때(`CancelledError`)의 되돌림은 프로브도 시험도 보지 않았다. 같은 이름을
동시에 넣는 경합도 프로브는 재지 못했고(명세 Further Notes의 "재지 못한 것"),
`tests/adapters/test_postgres_accounts.py`의 시험이 본다.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol
from uuid import UUID

from sqlalchemy import Select, delete, insert, or_, select, update
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncEngine

from agent_os.adapters.postgres.account_tables import (
    ACCOUNT_CREATED_AT,
    ACCOUNT_DISABLED_AT,
    ACCOUNT_FAILURES,
    ACCOUNT_LOCKED_UNTIL,
    ACCOUNT_NAME,
    ACCOUNT_PASSWORD_HASH,
    ACCOUNT_TIER,
    ACCOUNTS,
    LOGIN_ACCOUNT,
    LOGIN_ENDED_AT,
    LOGIN_ID,
    LOGIN_LOGGED_IN_AT,
    LOGIN_RECORDS,
    LOGIN_REFRESHED_AT,
    LOGINS,
    RECORD_ACCOUNT,
    RECORD_ADDRESS,
    RECORD_KIND,
    RECORD_OCCURRED_AT,
    REFRESH_CREATED_AT,
    REFRESH_LOGIN_ID,
    REFRESH_TOKEN_HASH,
    REFRESH_TOKENS,
    REFRESH_USED_AT,
    SIGNING_KEY,
    SIGNING_KEY_CREATED_AT,
    SIGNING_KEY_ID,
    SIGNING_KEY_VALUE,
)
from agent_os.adapters.postgres.errors import sqlstate_of

type Tier = Literal["system_admin", "admin"]
type Taken = Literal["taken"]
type RecordKind = Literal[
    "system_admin_set",
    "login_succeeded",
    "login_failed",
    "locked",
    "logged_out",
    "refresh_reused",
    "signing_key_rotated",
]

UNIQUE_VIOLATION = "23505"
# 서명 키의 표는 한 줄만 든다. 줄의 번호가 늘 1이고 표의 검사 제약이 다른 번호를 막는다
SIGNING_KEY_ROW = 1

# 줄에서 읽는 칸의 차례. `AccountRecord` 와 `_record_of` 가 같은 차례로 푼다.
type _Row = Select[str, str, str | None, datetime | None, int, datetime | None, datetime]


class AccountStoreError(RuntimeError):
    """데이터베이스가 낸 예외를 포트 밖으로 낼 때 바꾼 예외. 원인과 문맥이 비어 있다.

    문구는 원래 예외의 클래스 이름만 싣고 값을 싣지 않는다. 오류 번호는 `sqlstate` 속성에 있고
    `reason_of` 가 그것을 읽는다.
    """

    def __init__(self, kind: str, *, sqlstate: str | None) -> None:
        super().__init__(f"계정 저장소가 실패했습니다({kind})")
        self.sqlstate = sqlstate


@dataclass(frozen=True, slots=True)
class AccountRecord:
    """계정의 줄 하나. 포트의 읽기 전용 줄(`AccountRow`)을 시그니처로 만족한다."""

    name: str
    tier: Tier
    password_hash: str | None
    disabled_at: datetime | None
    failures: int
    locked_until: datetime | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class RefreshRecord:
    """갱신용 번호 한 줄과 그 번호가 속한 로그인 한 건. 포트의 `RefreshRow` 를 시그니처로
    만족한다."""

    login_id: UUID
    account: str
    logged_in_at: datetime
    refreshed_at: datetime
    ended_at: datetime | None
    used_at: datetime | None


class _NewAccount(Protocol):
    """넣을 계정. 포트의 `NewAccount` 와 같은 모양이고, 이 모듈은 포트를 가져오지 않는다."""

    @property
    def name(self) -> str: ...

    @property
    def tier(self) -> Tier: ...

    @property
    def password_hash(self) -> str: ...

    @property
    def created_at(self) -> datetime: ...


def _as_tier(value: str) -> Tier:
    if value == "system_admin":
        return "system_admin"
    if value == "admin":
        return "admin"
    raise ValueError("계정의 단계를 알 수 없다")


def _select_accounts() -> _Row:
    return select(
        ACCOUNT_NAME,
        ACCOUNT_TIER,
        ACCOUNT_PASSWORD_HASH,
        ACCOUNT_DISABLED_AT,
        ACCOUNT_FAILURES,
        ACCOUNT_LOCKED_UNTIL,
        ACCOUNT_CREATED_AT,
    )


def _record_of(
    name: str,
    tier: str,
    password_hash: str | None,
    disabled_at: datetime | None,
    failures: int,
    locked_until: datetime | None,
    created_at: datetime,
) -> AccountRecord:
    return AccountRecord(
        name, _as_tier(tier), password_hash, disabled_at, failures, locked_until, created_at
    )


def _store_error(error: BaseException) -> AccountStoreError:
    """예외를 포트 밖으로 낼 예외로 바꾼다. 원인을 잇지 않으므로 부르는 쪽이 `except` 밖에서
    던진다."""
    return AccountStoreError(type(error).__name__, sqlstate=sqlstate_of(error))


class PostgresAccountWork:
    """트랜잭션 하나 안의 읽기와 쓰기. 연결은 트랜잭션을 연 쪽이 쥐고 닫는다."""

    def __init__(self, connection: AsyncConnection) -> None:
        self._connection = connection

    async def lock_system_admin(self) -> AccountRecord | None:
        query = _select_accounts().where(ACCOUNT_TIER == "system_admin").with_for_update()
        return await self._one(query)

    async def lock(self, name: str) -> AccountRecord | None:
        query = _select_accounts().where(ACCOUNT_NAME == name).with_for_update()
        return await self._one(query)

    async def add(self, account: _NewAccount) -> AccountRecord | Taken:
        return await self._guard(lambda: self._insert(account))

    async def reset_password(self, name: str, *, password_hash: str) -> None:
        statement = (
            update(ACCOUNTS)
            .where(ACCOUNT_NAME == name)
            .values(password_hash=password_hash, failures=0, locked_until=None)
        )
        await self._guard(lambda: self._connection.execute(statement))

    async def end_logins(self, name: str, *, at: datetime) -> None:
        statement = (
            update(LOGINS)
            .where(LOGIN_ACCOUNT == name, LOGIN_ENDED_AT.is_(None))
            .values(ended_at=at)
        )
        await self._guard(lambda: self._connection.execute(statement))

    async def record(
        self,
        kind: RecordKind,
        *,
        at: datetime,
        account: str | None,
        address: str | None = None,
    ) -> None:
        statement = insert(LOGIN_RECORDS).values(
            {
                RECORD_OCCURRED_AT.name: at,
                RECORD_KIND.name: kind,
                RECORD_ACCOUNT.name: account,
                RECORD_ADDRESS.name: address,
            }
        )
        await self._guard(lambda: self._connection.execute(statement))

    async def any_account(self) -> bool:
        query = select(ACCOUNT_NAME).limit(1)
        return await self._guard(lambda: self._exists(query))

    async def set_failures(
        self, name: str, *, failures: int, locked_until: datetime | None
    ) -> None:
        statement = (
            update(ACCOUNTS)
            .where(ACCOUNT_NAME == name)
            .values(failures=failures, locked_until=locked_until)
        )
        await self._guard(lambda: self._connection.execute(statement))

    async def clear_failures(self, name: str) -> None:
        statement = (
            update(ACCOUNTS).where(ACCOUNT_NAME == name).values(failures=0, locked_until=None)
        )
        await self._guard(lambda: self._connection.execute(statement))

    async def delete_ended_logins(
        self, name: str, *, idle_before: datetime, total_before: datetime
    ) -> None:
        # 갱신용 번호는 로그인 한 건을 가리키는 외래 키의 `ON DELETE CASCADE` 로 함께 지워진다
        statement = delete(LOGINS).where(
            LOGIN_ACCOUNT == name,
            or_(
                LOGIN_ENDED_AT.is_not(None),
                LOGIN_REFRESHED_AT <= idle_before,
                LOGIN_LOGGED_IN_AT <= total_before,
            ),
        )
        await self._guard(lambda: self._connection.execute(statement))

    async def open_login(self, login_id: UUID, name: str, *, at: datetime) -> None:
        statement = insert(LOGINS).values(
            {
                LOGIN_ID.name: login_id,
                LOGIN_ACCOUNT.name: name,
                LOGIN_LOGGED_IN_AT.name: at,
                LOGIN_REFRESHED_AT.name: at,
            }
        )
        await self._guard(lambda: self._connection.execute(statement))

    async def add_refresh_token(self, token_hash: str, login_id: UUID, *, at: datetime) -> None:
        statement = insert(REFRESH_TOKENS).values(
            {
                REFRESH_TOKEN_HASH.name: token_hash,
                REFRESH_LOGIN_ID.name: login_id,
                REFRESH_CREATED_AT.name: at,
            }
        )
        await self._guard(lambda: self._connection.execute(statement))

    async def end_login(self, login_id: UUID, *, at: datetime) -> None:
        statement = (
            update(LOGINS).where(LOGIN_ID == login_id, LOGIN_ENDED_AT.is_(None)).values(ended_at=at)
        )
        await self._guard(lambda: self._connection.execute(statement))

    async def ensure_signing_key(self, key: bytes, *, at: datetime) -> None:
        # 없으면 넣는다 한 문장이라 `serve` 둘이 함께 떠도 줄이 하나로 모인다
        statement = (
            postgresql.insert(SIGNING_KEY)
            .values(
                {
                    SIGNING_KEY_ID.name: SIGNING_KEY_ROW,
                    SIGNING_KEY_VALUE.name: key,
                    SIGNING_KEY_CREATED_AT.name: at,
                }
            )
            .on_conflict_do_nothing()
        )
        await self._guard(lambda: self._connection.execute(statement))

    async def read_signing_key(self) -> bytes | None:
        query = select(SIGNING_KEY_VALUE).where(SIGNING_KEY_ID == SIGNING_KEY_ROW)
        return await self._guard(lambda: self._scalar_bytes(query))

    async def replace_signing_key(self, key: bytes, *, at: datetime) -> None:
        # 한 문장으로 바꿔 넣는다. 줄이 없으면 넣고, 있으면 키와 만든 시각만 바꾼다
        insertion = postgresql.insert(SIGNING_KEY).values(
            {
                SIGNING_KEY_ID.name: SIGNING_KEY_ROW,
                SIGNING_KEY_VALUE.name: key,
                SIGNING_KEY_CREATED_AT.name: at,
            }
        )
        statement = insertion.on_conflict_do_update(
            index_elements=[SIGNING_KEY_ID],
            set_={SIGNING_KEY_VALUE.name: key, SIGNING_KEY_CREATED_AT.name: at},
        )
        await self._guard(lambda: self._connection.execute(statement))

    async def lock_refresh(self, token_hash: str) -> RefreshRecord | None:
        # 로그인 줄을 먼저, 번호 줄을 그다음에 잠근다. 로그인 줄을 지우는
        # 쪽(`delete_ended_logins`)이 로그인 줄을 잡은 뒤 외래 키 CASCADE 로 번호 줄을 잡는 순서와
        # 같다. 계정의 줄은 잠그지 않는다(로그인을 여는 쪽이 계정을 잠근 채 로그인 줄을 지워, 둘이
        # 서로 기다리게 된다)
        return await self._guard(lambda: self._refresh_row(token_hash))

    async def read_account(self, name: str) -> AccountRecord | None:
        return await self._one(_select_accounts().where(ACCOUNT_NAME == name))

    async def use_refresh_token(self, token_hash: str, *, at: datetime) -> None:
        statement = (
            update(REFRESH_TOKENS)
            .where(REFRESH_TOKEN_HASH == token_hash, REFRESH_USED_AT.is_(None))
            .values(used_at=at)
        )
        await self._guard(lambda: self._connection.execute(statement))

    async def touch_login(self, login_id: UUID, *, at: datetime) -> None:
        statement = update(LOGINS).where(LOGIN_ID == login_id).values(refreshed_at=at)
        await self._guard(lambda: self._connection.execute(statement))

    async def _refresh_row(self, token_hash: str) -> RefreshRecord | None:
        owner = select(REFRESH_LOGIN_ID).where(REFRESH_TOKEN_HASH == token_hash)
        owner_row = (await self._connection.execute(owner)).one_or_none()
        if owner_row is None:
            return None
        login = (
            select(LOGIN_ID, LOGIN_ACCOUNT, LOGIN_LOGGED_IN_AT, LOGIN_REFRESHED_AT, LOGIN_ENDED_AT)
            .where(LOGIN_ID == owner_row[0])
            .with_for_update()
        )
        login_row = (await self._connection.execute(login)).one_or_none()
        if login_row is None:
            return None
        # 번호 줄은 로그인 줄을 잡은 뒤 새 문장으로 읽는다. 앞서 온 갱신이 커밋한 쓴 시각이 보인다
        used = select(REFRESH_USED_AT).where(REFRESH_TOKEN_HASH == token_hash).with_for_update()
        used_row = (await self._connection.execute(used)).one_or_none()
        if used_row is None:
            return None
        login_id, account, logged_in_at, refreshed_at, ended_at = login_row
        if not isinstance(login_id, UUID):
            raise TypeError("로그인 번호가 UUID가 아니다")
        return RefreshRecord(login_id, account, logged_in_at, refreshed_at, ended_at, used_row[0])

    async def _one(self, query: _Row) -> AccountRecord | None:
        return await self._guard(lambda: self._first(query))

    async def _exists(self, query: Select[str]) -> bool:
        return (await self._connection.execute(query)).first() is not None

    async def _scalar_bytes(self, query: Select[bytes]) -> bytes | None:
        row = (await self._connection.execute(query)).one_or_none()
        return None if row is None else bytes(row[0])

    async def _first(self, query: _Row) -> AccountRecord | None:
        row = (await self._connection.execute(query)).one_or_none()
        if row is None:
            return None
        name, tier, password_hash, disabled_at, failures, locked_until, created_at = row
        return _record_of(
            name, tier, password_hash, disabled_at, failures, locked_until, created_at
        )

    async def _insert(self, account: _NewAccount) -> AccountRecord | Taken:
        statement = (
            insert(ACCOUNTS)
            .values(
                {
                    ACCOUNT_NAME.name: account.name,
                    ACCOUNT_TIER.name: account.tier,
                    ACCOUNT_PASSWORD_HASH.name: account.password_hash,
                    ACCOUNT_FAILURES.name: 0,
                    ACCOUNT_CREATED_AT.name: account.created_at,
                }
            )
            .returning(
                ACCOUNT_NAME,
                ACCOUNT_TIER,
                ACCOUNT_PASSWORD_HASH,
                ACCOUNT_DISABLED_AT,
                ACCOUNT_FAILURES,
                ACCOUNT_LOCKED_UNTIL,
                ACCOUNT_CREATED_AT,
            )
        )
        try:
            # SAVEPOINT 안에서 넣어, 유일 제약 위반이 바깥 트랜잭션을 망가뜨리지 않게 한다
            async with self._connection.begin_nested():
                created = (await self._connection.execute(statement)).one()
        except IntegrityError as error:
            if sqlstate_of(error) != UNIQUE_VIOLATION:
                raise
            return "taken"
        return _record_of(*created)

    async def _guard[T](self, work: Callable[[], Awaitable[T]]) -> T:
        """데이터베이스가 낸 예외를 `AccountStoreError` 로 바꿔 올린다. 원인을 잇지 않는다."""
        try:
            return await work()
        except (SQLAlchemyError, OSError) as error:
            failure = _store_error(error)
        # 바꾼 예외는 `except` 밖에서 던진다. 안에서 던지면 원래 예외가 문맥으로 이어진다
        raise failure


class PostgresAccounts:
    """계정 저장소. 엔진은 `PostgresDatabase` 가 쥐고 닫는다."""

    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[PostgresAccountWork]:
        """트랜잭션 하나를 연다. 블록을 정상으로 나오면 적고 예외로 나오면 되돌린다."""
        connection = await self._start()
        try:
            async with connection.begin():
                yield PostgresAccountWork(connection)
        except (SQLAlchemyError, OSError) as error:
            # 적거나 되돌리다 난 실패다. 작업 객체의 실패는 이미 `AccountStoreError` 라 여기 닿지
            # 않는다
            failure = _store_error(error)
        else:
            return
        finally:
            await connection.close()
        raise failure

    async def _start(self) -> AsyncConnection:
        connection = self._engine.connect()
        try:
            await connection.start()
        except (SQLAlchemyError, OSError) as error:
            failure = _store_error(error)
        else:
            return connection
        raise failure
