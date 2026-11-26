"""계정 어댑터(`agent_os.adapters.postgres.accounts`)를 실제 테스트 데이터베이스에 대고 본다.

포트 타입(`AccountStore`)을 적은 픽스처로 넣기, 읽기, 쓰기, 이름 충돌을 본다. 어댑터는 포트를
상속하지 않고 시그니처로 만족하므로, 픽스처의 주해가 포트 적합성을 검증하는 유일한 자리다.

이름 충돌과 데이터베이스의 실패에 카나리아(기록에서 찾아낼 수 있게 일부러 심은 이름)를 넣어, 돌려준
값과 예외의 글과 역추적과 서버 기록에 그 이름이 실리지 않는지 본다. 값을 싣는 실패는 표에 항상
어기는 검사 제약(`CHECK`)을 더해 일으킨다. 서버가 낸 DETAIL 이 그 줄 전체(이름과 해시)를 싣는
실패다.
"""

from __future__ import annotations

import asyncio
import logging
import traceback
from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.dialects import postgresql
from tests.postgres_support import plain
from tools.database_for_tests import ScopedDatabase

from agent_os.adapters.postgres.account_tables import (
    ACCOUNTS,
    LOGIN_RECORDS,
    LOGINS,
    REFRESH_TOKENS,
    SIGNING_KEY,
)
from agent_os.adapters.postgres.accounts import AccountStoreError
from agent_os.adapters.postgres.database import (
    PostgresDatabase,
    parse_database_url,
    reason_of,
)
from agent_os.http.accounts import AccountStore, AccountWork, Tier

NOW = datetime(2026, 11, 26, 9, 0, tzinfo=UTC)
LATER = NOW + timedelta(hours=1)
CANARY = "canary.name.77"
HASH = "$argon2id$v=19$m=19456,t=2,p=1$c2FsdA$aGFzaA"


@dataclass(frozen=True)
class NewAccount:
    name: str
    tier: Tier
    password_hash: str
    created_at: datetime


def _ignore(_message: str) -> None:
    """기다린다는 알림을 찍지 않는다."""


@pytest_asyncio.fixture
async def accounts(database: ScopedDatabase) -> AsyncIterator[AccountStore]:
    url = parse_database_url(database.address.text_for(database.name))
    assert url is not None
    adapter = PostgresDatabase(url, notice=_ignore)
    store: AccountStore = adapter.accounts()
    try:
        yield store
    finally:
        await adapter.close()


@asynccontextmanager
async def _work(store: AccountStore) -> AsyncGenerator[AccountWork]:
    """트랜잭션 하나. 작업 객체를 포트 타입에 한 번 적는다(어긋남이 메서드 이름까지 드러난다)."""
    async with store.transaction() as opened:
        work: AccountWork = opened
        yield work


def _new(name: str, tier: Tier = "admin", *, at: datetime = NOW) -> NewAccount:
    return NewAccount(name=name, tier=tier, password_hash=HASH, created_at=at)


# --- 넣기와 읽기 ---------------------------------------------------------------------------------


async def test_계정을_넣고_잠가_읽으면_넣은_값이_그대로_돌아온다(accounts: AccountStore) -> None:
    async with _work(accounts) as work:
        created = await work.add(_new("kim.min", "admin"))
        assert created != "taken"
        assert (created.name, created.tier, created.password_hash) == ("kim.min", "admin", HASH)
        assert (created.failures, created.locked_until, created.disabled_at) == (0, None, None)
        assert created.created_at == NOW
    async with _work(accounts) as work:
        found = await work.lock("kim.min")
    assert found is not None
    assert found == created


async def test_없는_이름은_없음이다(accounts: AccountStore) -> None:
    async with _work(accounts) as work:
        assert await work.lock("nobody") is None
        assert await work.lock_system_admin() is None


async def test_시스템_관리자를_단계로_찾는다(accounts: AccountStore) -> None:
    async with _work(accounts) as work:
        await work.add(_new("kim.min", "admin"))
        await work.add(_new("root-user", "system_admin"))
    async with _work(accounts) as work:
        found = await work.lock_system_admin()
    assert found is not None
    assert (found.name, found.tier) == ("root-user", "system_admin")


# --- 이름 충돌은 값으로 가른다 -------------------------------------------------------------------


async def test_같은_이름을_다시_넣으면_taken을_돌려주고_첫_줄은_그대로다(
    accounts: AccountStore,
) -> None:
    async with _work(accounts) as work:
        await work.add(_new("kim.min", "admin"))
    async with _work(accounts) as work:
        second = await work.add(_new("kim.min", "admin", at=LATER))
        assert second == "taken"
        # 위반이 트랜잭션을 망가뜨리지 않아 같은 트랜잭션에서 다시 읽을 수 있다
        kept = await work.lock("kim.min")
    assert kept is not None
    assert kept.created_at == NOW


async def test_시스템_관리자가_이미_있으면_다른_이름의_시스템_관리자는_taken이다(
    accounts: AccountStore,
) -> None:
    async with _work(accounts) as work:
        await work.add(_new("root-one", "system_admin"))
    async with _work(accounts) as work:
        assert await work.add(_new("root-two", "system_admin")) == "taken"
        assert await work.add(_new("kim.min", "admin")) != "taken"
        owner = await work.lock_system_admin()
    assert owner is not None
    assert owner.name == "root-one"


async def test_taken_뒤_같은_트랜잭션의_쓰기가_적힌다(accounts: AccountStore) -> None:
    async with _work(accounts) as work:
        await work.add(_new("kim.min", "admin"))
    async with _work(accounts) as work:
        assert await work.add(_new("kim.min", "admin")) == "taken"
        assert await work.add(_new("lee.min", "admin")) != "taken"
    async with _work(accounts) as work:
        assert await work.lock("lee.min") is not None


async def test_같은_이름을_동시에_넣으면_하나만_들어가고_하나는_taken이다(
    accounts: AccountStore,
) -> None:
    async def attempt(created_at: datetime) -> bool:
        async with _work(accounts) as work:
            outcome = await work.add(_new("race.name", "admin", at=created_at))
            await asyncio.sleep(0.2)
            return outcome != "taken"

    results = await asyncio.gather(attempt(NOW), attempt(LATER))
    assert sorted(results) == [False, True]


# --- 쓰기 ----------------------------------------------------------------------------------------


async def test_비밀번호를_다시_정하면_해시를_바꾸고_틀린_횟수와_잠금을_지운다(
    database: ScopedDatabase, accounts: AccountStore
) -> None:
    async with _work(accounts) as work:
        await work.add(_new("root-one", "system_admin"))
    async with plain(database, autocommit=True) as connection:
        await connection.execute(
            text(
                "UPDATE operator_accounts SET failures = 6, locked_until = :until "
                "WHERE name = 'root-one'"
            ),
            {"until": LATER},
        )
    async with _work(accounts) as work:
        before = await work.lock("root-one")
        assert before is not None
        assert (before.failures, before.locked_until) == (6, LATER)
        await work.reset_password("root-one", password_hash="$argon2id$new")
    async with _work(accounts) as work:
        after = await work.lock("root-one")
    assert after is not None
    assert (after.password_hash, after.failures, after.locked_until) == ("$argon2id$new", 0, None)


async def test_로그인을_끊으면_끊기지_않은_줄만_그_시각으로_끊긴다(
    database: ScopedDatabase, accounts: AccountStore
) -> None:
    async with _work(accounts) as work:
        await work.add(_new("root-one", "system_admin"))
        await work.add(_new("kim.min", "admin"))
    insert = text(
        "INSERT INTO operator_logins (id, account, logged_in_at, refreshed_at, ended_at) "
        "VALUES (gen_random_uuid(), :account, :at, :at, :ended)"
    )
    async with plain(database, autocommit=True) as connection:
        await connection.execute(insert, {"account": "root-one", "at": NOW, "ended": None})
        await connection.execute(insert, {"account": "root-one", "at": NOW, "ended": None})
        await connection.execute(insert, {"account": "root-one", "at": NOW, "ended": NOW})
        await connection.execute(insert, {"account": "kim.min", "at": NOW, "ended": None})
    async with _work(accounts) as work:
        await work.end_logins("root-one", at=LATER)
    async with plain(database) as connection:
        result = await connection.execute(
            text("SELECT account, ended_at FROM operator_logins ORDER BY account, ended_at")
        )
        rows = [(row[0], row[1]) for row in result.all()]
    assert rows == [
        ("kim.min", None),
        ("root-one", NOW),
        ("root-one", LATER),
        ("root-one", LATER),
    ]


async def test_기록은_한_줄을_더하고_비밀번호와_해시를_싣지_않는다(
    database: ScopedDatabase, accounts: AccountStore
) -> None:
    async with _work(accounts) as work:
        await work.add(_new("root-one", "system_admin"))
        await work.record("system_admin_set", at=NOW, account="root-one")
    async with plain(database) as connection:
        result = await connection.execute(
            text("SELECT occurred_at, kind, account, actor, address FROM operator_login_records")
        )
        rows = [tuple(row) for row in result.all()]
    assert rows == [(NOW, "system_admin_set", "root-one", None, None)]
    dumped = repr(rows)
    assert HASH not in dumped


async def test_블록이_예외로_끝나면_쓴_것을_되돌린다(accounts: AccountStore) -> None:
    class Stop(Exception):
        pass

    with pytest.raises(Stop):
        async with _work(accounts) as work:
            await work.add(_new("kim.min", "admin"))
            raise Stop
    async with _work(accounts) as work:
        assert await work.lock("kim.min") is None


async def test_블록이_내는_예외는_그대로_나간다(accounts: AccountStore) -> None:
    class Stop(Exception):
        pass

    with pytest.raises(Stop) as raised:
        async with _work(accounts):
            raise Stop("그대로")
    assert str(raised.value) == "그대로"


# --- 로그인 경로가 쓰는 메서드 -------------------------------------------------------------------


async def test_계정이_하나라도_있는지_답한다(accounts: AccountStore) -> None:
    async with _work(accounts) as work:
        assert await work.any_account() is False
        await work.add(_new("kim.min", "admin"))
        assert await work.any_account() is True


async def test_틀린_횟수와_잠금을_적고_지운다(accounts: AccountStore) -> None:
    async with _work(accounts) as work:
        await work.add(_new("kim.min", "admin"))
        await work.set_failures("kim.min", failures=5, locked_until=LATER)
    async with _work(accounts) as work:
        row = await work.lock("kim.min")
        assert row is not None
        assert (row.failures, row.locked_until) == (5, LATER)
        await work.clear_failures("kim.min")
    async with _work(accounts) as work:
        row = await work.lock("kim.min")
        assert row is not None
        assert (row.failures, row.locked_until) == (0, None)


async def test_로그인_한_건과_갱신용_번호_해시를_적고_그_해시만_남는다(
    database: ScopedDatabase, accounts: AccountStore
) -> None:
    login_id = uuid4()
    async with _work(accounts) as work:
        await work.add(_new("kim.min", "admin"))
        await work.open_login(login_id, "kim.min", at=NOW)
        await work.add_refresh_token("a" * 64, login_id, at=NOW)
    async with plain(database) as connection:
        logins = (
            await connection.execute(
                text(
                    "SELECT id, account, logged_in_at, refreshed_at, ended_at FROM operator_logins"
                )
            )
        ).all()
        tokens = (
            await connection.execute(
                text(
                    "SELECT token_hash, login_id, created_at, used_at FROM operator_refresh_tokens"
                )
            )
        ).all()
    assert [tuple(row) for row in logins] == [(login_id, "kim.min", NOW, NOW, None)]
    assert [tuple(row) for row in tokens] == [("a" * 64, login_id, NOW, None)]


async def test_로그인_한_건을_끝내면_끝난_시각이_적히고_다시_끝내도_처음_시각이_남는다(
    database: ScopedDatabase, accounts: AccountStore
) -> None:
    login_id = uuid4()
    async with _work(accounts) as work:
        await work.add(_new("kim.min", "admin"))
        await work.open_login(login_id, "kim.min", at=NOW)
        await work.end_login(login_id, at=LATER)
    async with _work(accounts) as work:
        await work.end_login(login_id, at=LATER + timedelta(hours=1))
    async with plain(database) as connection:
        ended = (
            await connection.execute(text("SELECT ended_at FROM operator_logins"))
        ).scalar_one()
    assert ended == LATER


async def test_끝났거나_쉬었거나_너무_오래된_로그인만_지우고_갱신용_번호도_함께_지운다(
    database: ScopedDatabase, accounts: AccountStore
) -> None:
    ended, idle, old, alive, other = (uuid4() for _ in range(5))
    async with _work(accounts) as work:
        await work.add(_new("kim.min", "admin"))
        await work.add(_new("lee.jin", "admin"))
        for login_id in (ended, idle, old, alive):
            await work.open_login(login_id, "kim.min", at=NOW)
            await work.add_refresh_token(f"{login_id.hex}", login_id, at=NOW)
        await work.open_login(other, "lee.jin", at=NOW)
        await work.end_login(ended, at=NOW)
    # 쉰 로그인은 마지막 갱신이 쉬는 기준 이전이고, 오래된 로그인은 처음 로그인한 때가 총 기준
    # 이전이다
    async with plain(database, autocommit=True) as connection:
        await connection.execute(
            text("UPDATE operator_logins SET refreshed_at = :at WHERE id = :id"),
            {"at": NOW - timedelta(hours=2), "id": idle},
        )
        await connection.execute(
            text("UPDATE operator_logins SET logged_in_at = :at WHERE id = :id"),
            {"at": NOW - timedelta(days=2), "id": old},
        )
    async with _work(accounts) as work:
        await work.delete_ended_logins(
            "kim.min", idle_before=NOW - timedelta(hours=1), total_before=NOW - timedelta(days=1)
        )
    async with plain(database) as connection:
        left = {
            row[0]
            for row in (await connection.execute(text("SELECT id FROM operator_logins"))).all()
        }
        tokens = {
            row[0]
            for row in (
                await connection.execute(text("SELECT token_hash FROM operator_refresh_tokens"))
            ).all()
        }
    assert left == {alive, other}
    assert tokens == {alive.hex}


async def test_서명_키는_없을_때만_들어가고_둘이_함께_넣어도_하나로_모인다(
    database: ScopedDatabase, accounts: AccountStore
) -> None:
    first, second = b"\x01" * 32, b"\x02" * 32
    async with _work(accounts) as work:
        assert await work.read_signing_key() is None
        await work.ensure_signing_key(first, at=NOW)
        await work.ensure_signing_key(second, at=LATER)
    async with _work(accounts) as work:
        assert await work.read_signing_key() == first
    await asyncio.gather(*(_ensure_key(accounts, bytes([index]) * 32) for index in range(3, 8)))
    async with _work(accounts) as work:
        assert await work.read_signing_key() == first
    async with plain(database) as connection:
        count = (
            await connection.execute(text("SELECT count(*) FROM operator_signing_key"))
        ).scalar_one()
    assert count == 1


async def _ensure_key(accounts: AccountStore, key: bytes) -> None:
    async with _work(accounts) as work:
        await work.ensure_signing_key(key, at=NOW)


async def test_로그인_기록은_접속_주소를_함께_적는다(
    database: ScopedDatabase, accounts: AccountStore
) -> None:
    async with _work(accounts) as work:
        await work.add(_new("kim.min", "admin"))
        await work.record("login_failed", at=NOW, account="kim.min", address="203.0.113.7")
        await work.record("locked", at=LATER, account="kim.min")
    async with plain(database) as connection:
        result = await connection.execute(
            text("SELECT kind, account, address FROM operator_login_records ORDER BY seq")
        )
        rows = [tuple(row) for row in result.all()]
    assert rows == [
        ("login_failed", "kim.min", "203.0.113.7"),
        ("locked", "kim.min", None),
    ]


# --- 표 정의가 실제 표와 맞는다 ------------------------------------------------------------------


async def test_표_정의의_칸이_실제_표의_칸과_이름과_타입과_비어도_됨까지_같다(
    database: ScopedDatabase,
) -> None:
    for table in (ACCOUNTS, LOGINS, LOGIN_RECORDS, REFRESH_TOKENS, SIGNING_KEY):
        async with plain(database) as connection:
            result = await connection.execute(
                text(
                    "SELECT column_name, data_type, is_nullable FROM information_schema.columns "
                    "WHERE table_schema = 'public' AND table_name = :name"
                ),
                {"name": table.name},
            )
            actual = {row[0]: (row[1], row[2] == "YES") for row in result.all()}
        declared = {
            column.name: (
                column.type.compile(dialect=postgresql.dialect()).lower(),
                bool(column.nullable),
            )
            for column in table.columns
        }
        assert declared == actual, table.name


# --- 값을 싣는 실패 ------------------------------------------------------------------------------


async def test_taken의_결과와_서버_기록에_이름이_실리지_않는다(
    accounts: AccountStore, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    async with _work(accounts) as work:
        await work.add(_new(CANARY, "admin"))
    async with _work(accounts) as work:
        outcome = await work.add(_new(CANARY, "admin"))
    assert outcome == "taken"
    assert CANARY not in repr(outcome)
    assert CANARY not in caplog.text


async def test_데이터베이스가_값을_싣고_낸_실패는_원인을_잇지_않고_값이_실리지_않는다(
    database: ScopedDatabase, accounts: AccountStore, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    # 모든 넣기를 어기는 검사 제약. 서버가 낸 DETAIL 은 줄 전체(이름과 해시)를 싣는다
    async with plain(database, autocommit=True) as connection:
        await connection.execute(
            text("ALTER TABLE operator_accounts ADD CONSTRAINT always_fails CHECK (failures > 0)")
        )

    with pytest.raises(AccountStoreError) as raised:
        async with _work(accounts) as work:
            await work.add(_new(CANARY, "admin"))

    error = raised.value
    assert error.__cause__ is None
    assert error.__context__ is None
    assert error.sqlstate == "23514"
    assert reason_of(error) == "오류 번호 23514"
    shown = "".join(traceback.format_exception(error))
    assert CANARY not in shown
    assert HASH not in shown
    assert CANARY not in caplog.text
    assert HASH not in caplog.text


async def test_닿지_못하면_값이_없는_AccountStoreError로_나가고_원인을_잇지_않는다(
    database: ScopedDatabase,
) -> None:
    url = parse_database_url(database.address.text_for("agent_os_no_such_database_00000000"))
    assert url is not None
    adapter = PostgresDatabase(url, notice=_ignore)
    try:
        with pytest.raises(AccountStoreError) as raised:
            async with _work(adapter.accounts()):
                raise AssertionError("닿지 못해 블록에 들어오지 못해야 한다")
    finally:
        await adapter.close()
    assert raised.value.__cause__ is None
    assert raised.value.__context__ is None
    assert raised.value.sqlstate == "3D000"
