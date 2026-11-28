"""계정을 다루는 경로 다섯과 링크로 비밀번호 정하기와 내 비밀번호 바꾸기를 앱에 넣어 바깥 행동만
본다(admin-login 06).

계정 저장소는 가짜가 아니라 시험마다 복제한 진짜 데이터베이스다. 링크를 잠가 한 번만 쓰는 일과
견주는 사이에 바뀐 계정은 행 잠금과 트랜잭션이 정하므로 가짜로는 증명되지 않는다. 시계는 시험이
움직이는 가짜 시계 하나이고, 기준 주소는 `https://admin.test` 다.

비밀번호와 링크 토큰이 기록과 서버 기록과 응답에 실리지 않는지는 카나리아(일부러 심은 글)로 찾는다.
"""

from __future__ import annotations

import asyncio
import hashlib
import io
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient, Response
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from sqlalchemy import text
from tests.fake_database import FakeDatabase
from tests.fake_models import DEFAULT_MODEL, FakeModels
from tests.postgres_support import plain
from tests.test_server import FakePlugins, FakeTrace, IdleTools
from tools.database_for_tests import ScopedDatabase

from agent_os.adapters.postgres.database import PostgresDatabase, parse_database_url
from agent_os.core.ports import Clock
from agent_os.http import logins as logins_module
from agent_os.http.accounts import AccountStore, Tier
from agent_os.http.login_tokens import ACCESS_COOKIE, REFRESH_COOKIE, LoginDurations
from agent_os.http.passwords import PASSWORD_RULE_TEXT, hash_password
from agent_os.http.permissions import FORBIDDEN_FOR_ACCOUNT_MESSAGE
from agent_os.http.sites import Sites
from agent_os.sdk import Principal, RunId
from agent_os.server import create_app

START = datetime(2026, 11, 27, 9, 0, tzinfo=UTC)
PASSWORD = "Correct-horse-9!"
WRONG = "Wrong-horse-9!"
NEW = "Brand-new-pass-5!"
LINKED = "Linked-pass-1!"
CANARY = "Canary-pass-77!"
WEAK = "weakpassword"
# 걷힌 공유 토큰을 흉내 낸 머리. 운영자 경로는 `Authorization` 머리를 읽지 않으므로 401이다.
OLD_SHARED = {"Authorization": "Bearer adm1n-t0ken-that-only-tests-know"}
DEAD_LINK = "이 링크는 더 쓸 수 없다"
LOCKED = "계정이 잠겼다. 잠시 뒤에 다시 한다"
WRONG_CURRENT = "지금 비밀번호가 맞지 않는다"
NAME_TAKEN = "같은 이름의 계정이 이미 있다"
STRANGER = "x" * 43


class MovingClock:
    """시험이 움직이는 시계. 앱과 서비스와 데이터베이스에 적는 시각이 모두 이것을 따른다."""

    def __init__(self) -> None:
        self.at = START

    def now(self) -> datetime:
        return self.at

    def new_run_id(self) -> RunId:
        raise NotImplementedError("계정을 다루는 일은 실행을 일으키지 않는다")

    def advance(self, **delta: float) -> None:
        self.at += timedelta(**delta)


@dataclass(frozen=True)
class SeedAccount:
    name: str
    tier: Tier
    password_hash: str | None
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


@pytest.fixture
def clock() -> MovingClock:
    return MovingClock()


@pytest.fixture
def stderr() -> io.StringIO:
    return io.StringIO()


def _app(accounts: AccountStore, clock: Clock, stderr: io.StringIO) -> FastAPI:
    return create_app(
        plugins=FakePlugins(),
        trace=FakeTrace(),
        models=FakeModels(GenericFakeChatModel(messages=iter(()))),
        default_model=DEFAULT_MODEL,
        tools=IdleTools(),
        clock=clock,
        principal=Principal("alice"),
        sites=Sites(),
        run_timeout_seconds=None,
        end_user_concurrent_runs=None,
        stderr=stderr,
        database=FakeDatabase(),
        accounts=accounts,
        login_durations=LoginDurations(),
    )


@pytest_asyncio.fixture
async def client(
    accounts: AccountStore, clock: MovingClock, stderr: io.StringIO
) -> AsyncIterator[AsyncClient]:
    transport = ASGITransport(app=_app(accounts, clock, stderr))
    async with AsyncClient(transport=transport, base_url="https://admin.test") as opened:
        yield opened


async def _seed(
    accounts: AccountStore,
    name: str,
    *,
    tier: Tier = "admin",
    password: str | None = PASSWORD,
) -> None:
    stored = None if password is None else hash_password(password)
    async with accounts.transaction() as work:
        await work.add(SeedAccount(name=name, tier=tier, password_hash=stored, created_at=START))


async def _rows(database: ScopedDatabase, sql: str, **params: object) -> list[tuple[object, ...]]:
    async with plain(database) as connection:
        result = await connection.execute(text(sql), params)
        return [tuple(row) for row in result.all()]


async def _execute(database: ScopedDatabase, sql: str, **params: object) -> None:
    async with plain(database, autocommit=True) as connection:
        await connection.execute(text(sql), params)


async def _login(client: AsyncClient, name: str, password: str = PASSWORD) -> Response:
    response = await client.post("/auth/login", json={"name": name, "password": password})
    # httpx 는 `Secure` 쿠키를 보관통에 넣고 다음 요청에 스스로 싣는다. 이 시험은 쿠키를 머리로
    # 직접 싣고 어느 요청에 무엇이 실렸는지를 단언하므로 보관통을 늘 비워 둔다
    client.cookies.clear()
    return response


def _cookies(response: Response) -> dict[str, str]:
    found: dict[str, str] = {}
    for line in response.headers.get_list("set-cookie"):
        name, _, rest = line.partition("=")
        found[name] = rest.partition(";")[0]
    return found


def _both(response: Response) -> dict[str, str]:
    """갱신까지 부를 수 있게 쿠키 둘을 함께 싣는 머리."""
    cookies = _cookies(response)
    access = f"{ACCESS_COOKIE}={cookies[ACCESS_COOKIE]}"
    refresh = f"{REFRESH_COOKIE}={cookies[REFRESH_COOKIE]}"
    return {"Cookie": f"{access}; {refresh}"}


async def _session(
    client: AsyncClient, accounts: AccountStore, name: str, *, tier: Tier = "admin"
) -> dict[str, str]:
    """계정을 심고 로그인해 쿠키 머리를 돌려준다."""
    await _seed(accounts, name, tier=tier)
    response = await _login(client, name)
    assert response.status_code == 204
    return _both(response)


async def _boss(client: AsyncClient, accounts: AccountStore) -> dict[str, str]:
    return await _session(client, accounts, "root.one", tier="system_admin")


async def _create(client: AsyncClient, boss: dict[str, str], name: str) -> str:
    """계정을 만들고 첫 링크 토큰을 돌려준다."""
    response = await client.post("/accounts", json={"name": name}, headers=boss)
    assert response.status_code == 201
    return str(response.json()["link_token"])


async def _link(client: AsyncClient, boss: dict[str, str], name: str) -> str:
    response = await client.post(f"/accounts/{name}/link", headers=boss)
    assert response.status_code == 201
    return str(response.json()["link_token"])


async def _set(client: AsyncClient, token: str, password: str = NEW) -> Response:
    return await client.post("/auth/set-password", json={"token": token, "password": password})


async def _kinds(database: ScopedDatabase) -> list[tuple[str, str | None, str | None]]:
    """로그인 성공 줄을 뺀 기록의 (종류, 대상, 한 사람)."""
    rows = await _rows(
        database,
        "SELECT kind, account, actor FROM operator_login_records"
        " WHERE kind <> 'login_succeeded' ORDER BY seq",
    )
    return [(str(kind), _optional(account), _optional(actor)) for kind, account, actor in rows]


def _optional(value: object) -> str | None:
    return None if value is None else str(value)


async def _row(database: ScopedDatabase, name: str) -> tuple[object, ...]:
    (row,) = await _rows(
        database,
        "SELECT tier, password_hash, disabled_at, failures, locked_until"
        " FROM operator_accounts WHERE name = :name",
        name=name,
    )
    return row


def _field(response: Response) -> str:
    violations = response.json()["violations"]
    assert len(violations) == 1
    return str(violations[0]["field"])


# --- 계정 만들기 ---------------------------------------------------------------------------------


async def test_계정을_만들면_201과_링크_토큰과_스물네_시간_뒤_기한을_받고_비밀번호는_비어_있다(
    client: AsyncClient, accounts: AccountStore, database: ScopedDatabase
) -> None:
    boss = await _boss(client, accounts)

    response = await client.post("/accounts", json={"name": "new.user"}, headers=boss)

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"name", "link_token", "link_expires_at"}
    assert body["name"] == "new.user"
    assert datetime.fromisoformat(body["link_expires_at"]) == START + timedelta(hours=24)
    row = await _row(database, "new.user")
    assert (row[0], row[1], row[2], row[3], row[4]) == ("admin", None, None, 0, None)
    stored = await _rows(
        database, "SELECT token_hash, account, used_at FROM operator_password_links"
    )
    digest = hashlib.sha256(body["link_token"].encode("ascii")).hexdigest()
    assert stored == [(digest, "new.user", None)]
    assert body["link_token"] not in repr(stored)
    assert await _kinds(database) == [
        ("account_created", "new.user", "root.one"),
        ("link_created", "new.user", "root.one"),
    ]


async def test_이름의_영문_대문자는_소문자로_접어_만든다(
    client: AsyncClient, accounts: AccountStore
) -> None:
    boss = await _boss(client, accounts)

    response = await client.post("/accounts", json={"name": "New.User"}, headers=boss)

    assert response.status_code == 201
    assert response.json()["name"] == "new.user"


@pytest.mark.parametrize("name", ["ab", "bad name", "-lead", "한글이름", "a" * 33, "new\nuser"])
async def test_규칙에_맞지_않는_이름은_422이고_계정을_만들지_않는다(
    name: str, client: AsyncClient, accounts: AccountStore, database: ScopedDatabase
) -> None:
    boss = await _boss(client, accounts)

    response = await client.post("/accounts", json={"name": name}, headers=boss)

    assert response.status_code == 422
    assert _field(response) == "body.name"
    assert await _rows(database, "SELECT name FROM operator_accounts") == [("root.one",)]


async def test_같은_이름의_계정_만들기는_409이고_응답과_서버_기록에_이름이_실리지_않는다(
    client: AsyncClient, accounts: AccountStore, stderr: io.StringIO, database: ScopedDatabase
) -> None:
    boss = await _boss(client, accounts)
    await _create(client, boss, "canary.acct9")

    again = await client.post("/accounts", json={"name": "canary.acct9"}, headers=boss)
    folded = await client.post("/accounts", json={"name": "Canary.Acct9"}, headers=boss)

    for response in (again, folded):
        assert response.status_code == 409
        assert response.json()["code"] == "conflict"
        assert response.json()["message"] == NAME_TAKEN
        assert "canary" not in response.text.lower(), f"응답: {response.text}"
    assert "canary" not in stderr.getvalue().lower()
    assert await _rows(database, "SELECT count(*) FROM operator_password_links") == [(1,)]


# --- 링크로 비밀번호 정하기 ----------------------------------------------------------------------


async def test_링크로_비밀번호를_정하면_204이고_로그인시키지_않으며_그_계정이_로그인할_수_있다(
    client: AsyncClient, accounts: AccountStore, database: ScopedDatabase
) -> None:
    boss = await _boss(client, accounts)
    token = await _create(client, boss, "new.user")
    assert (await _login(client, "new.user", NEW)).status_code == 401

    response = await _set(client, token)

    assert response.status_code == 204, f"링크 정하기가 {response.status_code} 를 냈다"
    assert response.content == b""
    assert "set-cookie" not in response.headers
    assert await _rows(database, "SELECT id FROM operator_logins WHERE account = 'new.user'") == []
    assert (await _login(client, "new.user", NEW)).status_code == 204
    assert ("password_set_by_link", "new.user", None) in await _kinds(database)


async def test_같은_링크는_두_번_쓰이지_않고_두_번째는_404이며_첫_비밀번호가_남는다(
    client: AsyncClient, accounts: AccountStore
) -> None:
    boss = await _boss(client, accounts)
    token = await _create(client, boss, "new.user")
    assert (await _set(client, token, NEW)).status_code == 204

    again = await _set(client, token, LINKED)

    assert again.status_code == 404
    assert again.json()["code"] == "not_found"
    assert again.json()["message"] == DEAD_LINK
    assert (await _login(client, "new.user", NEW)).status_code == 204
    assert (await _login(client, "new.user", LINKED)).status_code == 401


@pytest.mark.parametrize(
    ("delay", "status"),
    [(timedelta(hours=23, minutes=59, seconds=59), 204), (timedelta(hours=24), 404)],
)
async def test_링크는_만든_때부터_스물네_시간까지만_쓸_수_있다(
    delay: timedelta, status: int, client: AsyncClient, accounts: AccountStore, clock: MovingClock
) -> None:
    boss = await _boss(client, accounts)
    token = await _create(client, boss, "new.user")
    clock.advance(seconds=delay.total_seconds())

    response = await _set(client, token)

    assert response.status_code == status, f"{delay} 뒤 링크가 {response.status_code} 를 냈다"


async def test_없는_링크와_못_쓰게_된_링크와_비활성_계정의_링크가_같은_404이다(
    client: AsyncClient, accounts: AccountStore
) -> None:
    boss = await _boss(client, accounts)
    old = await _create(client, boss, "new.user")
    await _link(client, boss, "new.user")
    other = await _create(client, boss, "off.user")
    await client.put("/accounts/off.user/active", json={"active": False}, headers=boss)

    answers = [await _set(client, token) for token in (STRANGER, old, other)]

    assert [each.status_code for each in answers] == [404, 404, 404]
    assert {each.json()["message"] for each in answers} == {DEAD_LINK}


async def test_링크가_살아_있어도_계정이_비활성이면_404이고_비밀번호가_정해지지_않는다(
    client: AsyncClient, accounts: AccountStore, database: ScopedDatabase
) -> None:
    boss = await _boss(client, accounts)
    token = await _create(client, boss, "new.user")
    # 활성 바꾸기 경로는 링크도 함께 못 쓰게 하므로, 링크는 그대로 두고 계정 줄만 직접 끈다
    await _execute(
        database, "UPDATE operator_accounts SET disabled_at = :at WHERE name = 'new.user'", at=START
    )

    response = await _set(client, token)

    assert response.status_code == 404
    assert response.json()["message"] == DEAD_LINK
    assert (await _row(database, "new.user"))[1] is None


async def test_링크가_죽었으면_비밀번호_규칙보다_먼저_404이고_살아_있으면_규칙_위반이_422이다(
    client: AsyncClient, accounts: AccountStore
) -> None:
    boss = await _boss(client, accounts)
    token = await _create(client, boss, "new.user")

    dead = await _set(client, STRANGER, WEAK)
    weak = await _set(client, token, WEAK)

    assert dead.status_code == 404
    assert weak.status_code == 422
    assert _field(weak) == "body.password"
    assert weak.json()["violations"][0]["message"] == PASSWORD_RULE_TEXT
    # 규칙을 어긴 시도는 링크를 쓰지 않는다
    assert (await _set(client, token)).status_code == 204


@pytest.mark.parametrize(
    "body",
    [
        {"token": "has space", "password": NEW},
        {"token": "t" * 129, "password": NEW},
        {"token": "", "password": NEW},
        {"password": NEW},
        {"token": STRANGER},
        {"token": STRANGER, "password": NEW, "extra": 1},
        {"token": STRANGER, "password": "p" * 1025},
    ],
)
async def test_본문의_형식이_틀리면_422이고_값을_되울리지_않는다(
    body: dict[str, object], client: AsyncClient
) -> None:
    response = await client.post("/auth/set-password", json=body)

    assert response.status_code == 422
    assert response.json()["code"] == "invalid_request"
    for value in body.values():
        if isinstance(value, str) and len(value) >= 5:
            assert value not in response.text


async def test_같은_링크로_동시에_온_비밀번호_정하기_둘_가운데_하나만_204이다(
    client: AsyncClient, accounts: AccountStore
) -> None:
    boss = await _boss(client, accounts)
    token = await _create(client, boss, "new.user")

    first, second = await asyncio.gather(_set(client, token, NEW), _set(client, token, LINKED))

    assert sorted([first.status_code, second.status_code]) == [204, 404]
    winner = NEW if first.status_code == 204 else LINKED
    loser = LINKED if winner == NEW else NEW
    assert (await _login(client, "new.user", winner)).status_code == 204
    assert (await _login(client, "new.user", loser)).status_code == 401


async def test_링크로_정하면_그_계정의_다른_로그인이_끊기고_틀린_횟수와_잠금이_풀린다(
    client: AsyncClient, accounts: AccountStore, database: ScopedDatabase
) -> None:
    boss = await _boss(client, accounts)
    await _seed(accounts, "kim.min")
    kim = _both(await _login(client, "kim.min"))
    for _ in range(5):
        await _login(client, "kim.min", WRONG)
    assert (await _row(database, "kim.min"))[3] == 5
    token = await _link(client, boss, "kim.min")

    response = await _set(client, token)

    assert response.status_code == 204
    # 짧은 JWT 는 만료까지 통과하지만 끊긴 로그인은 갱신이 받지 않는다
    refreshed = await client.post("/auth/refresh", headers=kim)
    assert refreshed.status_code == 401, f"정한 뒤 옛 로그인의 갱신이 {refreshed.status_code}"
    assert await _rows(
        database, "SELECT ended_at FROM operator_logins WHERE account = 'kim.min'"
    ) == [(START,)]
    row = await _row(database, "kim.min")
    assert (row[3], row[4]) == (0, None)
    assert (await _login(client, "kim.min", NEW)).status_code == 204


# --- 계정 목록 -----------------------------------------------------------------------------------


async def test_목록은_시스템_관리자가_먼저이고_나머지는_이름순이며_상태와_잠김을_싣는다(
    client: AsyncClient, accounts: AccountStore, clock: MovingClock
) -> None:
    boss = await _boss(client, accounts)
    await _seed(accounts, "bee.two")
    await _seed(accounts, "amy.one")
    await _seed(accounts, "lock.one")
    await _seed(accounts, "off.one")
    await _create(client, boss, "pending.one")
    await client.put("/accounts/off.one/active", json={"active": False}, headers=boss)
    for _ in range(5):
        await _login(client, "lock.one", WRONG)

    response = await client.get("/accounts", headers=boss)

    assert response.status_code == 200
    rows = response.json()["accounts"]
    assert [row["name"] for row in rows] == [
        "root.one",
        "amy.one",
        "bee.two",
        "lock.one",
        "off.one",
        "pending.one",
    ]
    assert all(set(row) == {"name", "tier", "state", "locked_until", "created_at"} for row in rows)
    by_name = {row["name"]: row for row in rows}
    assert by_name["root.one"]["tier"] == "system_admin"
    assert by_name["amy.one"]["tier"] == "admin"
    assert {name: by_name[name]["state"] for name in by_name} == {
        "root.one": "active",
        "amy.one": "active",
        "bee.two": "active",
        "lock.one": "active",
        "off.one": "disabled",
        "pending.one": "password_unset",
    }
    assert datetime.fromisoformat(by_name["lock.one"]["locked_until"]) == START + timedelta(
        minutes=1
    )
    assert by_name["amy.one"]["locked_until"] is None
    # 풀리는 시각이 지났으면 잠긴 것으로 세지 않는다
    clock.advance(minutes=1)
    later = (await client.get("/accounts", headers=boss)).json()["accounts"]
    assert {row["name"]: row["locked_until"] for row in later}["lock.one"] is None


# --- 링크 만들기 ---------------------------------------------------------------------------------


async def test_링크를_새로_만들면_쓰지_않은_앞_링크가_못_쓰게_되고_새_링크가_통한다(
    client: AsyncClient, accounts: AccountStore, database: ScopedDatabase
) -> None:
    boss = await _boss(client, accounts)
    first = await _create(client, boss, "new.user")

    response = await client.post("/accounts/new.user/link", headers=boss)

    assert response.status_code == 201
    body = response.json()
    assert set(body) == {"link_token", "link_expires_at"}
    assert datetime.fromisoformat(body["link_expires_at"]) == START + timedelta(hours=24)
    voided = await _set(client, first)
    assert voided.status_code == 404, f"새로 만든 뒤 앞 링크가 {voided.status_code} 를 냈다"
    assert (await _set(client, body["link_token"])).status_code == 204
    assert await _kinds(database) == [
        ("account_created", "new.user", "root.one"),
        ("link_created", "new.user", "root.one"),
        ("link_created", "new.user", "root.one"),
        ("password_set_by_link", "new.user", None),
    ]


async def test_링크_만들기의_거절은_없는_계정_404와_시스템_관리자와_비활성_계정_409이다(
    client: AsyncClient, accounts: AccountStore, database: ScopedDatabase
) -> None:
    boss = await _boss(client, accounts)
    await _create(client, boss, "off.user")
    await client.put("/accounts/off.user/active", json={"active": False}, headers=boss)

    absent = await client.post("/accounts/ghost.one/link", headers=boss)
    system = await client.post("/accounts/root.one/link", headers=boss)
    disabled = await client.post("/accounts/off.user/link", headers=boss)

    assert absent.status_code == 404
    assert system.status_code == 409
    assert disabled.status_code == 409
    assert system.json()["code"] == "conflict"
    # 거절된 요청은 링크도 기록도 남기지 않는다
    assert await _rows(database, "SELECT count(*) FROM operator_password_links") == [(1,)]


@pytest.mark.parametrize("name", ["Kim.Min", "a%20b", "kim.min%0A", "ab", "a" * 33])
async def test_경로의_이름이_규칙에_맞지_않으면_다섯_경로가_모두_422이다(
    name: str, client: AsyncClient, accounts: AccountStore
) -> None:
    boss = await _boss(client, accounts)

    responses = [
        await client.post(f"/accounts/{name}/link", headers=boss),
        await client.put(f"/accounts/{name}/active", json={"active": True}, headers=boss),
        await client.post(f"/accounts/{name}/unlock", headers=boss),
    ]

    for response in responses:
        assert response.status_code == 422
        assert _field(response) == "path.name"


# --- 활성과 비활성 -------------------------------------------------------------------------------


async def test_비활성으로_바꾸면_로그인과_갱신이_401이고_쓰지_않은_링크가_404이며_기록이_남는다(
    client: AsyncClient, accounts: AccountStore, database: ScopedDatabase
) -> None:
    boss = await _boss(client, accounts)
    await _seed(accounts, "kim.min")
    kim = _both(await _login(client, "kim.min"))
    # 비활성인 동안 갱신을 부르면 갱신이 스스로 그 로그인을 끊는다. 끊은 것이 비활성으로 바꾼 일의
    # 몫인지 보려고, 되돌린 뒤에 갱신을 부를 로그인을 하나 더 둔다
    later = _both(await _login(client, "kim.min"))
    token = await _link(client, boss, "kim.min")

    response = await client.put("/accounts/kim.min/active", json={"active": False}, headers=boss)

    assert response.status_code == 204
    assert response.content == b""
    refreshed = await client.post("/auth/refresh", headers=kim)
    assert refreshed.status_code == 401, f"끊긴 로그인의 갱신이 {refreshed.status_code} 를 냈다"
    assert (await _login(client, "kim.min")).status_code == 401
    dead = await _set(client, token)
    assert dead.status_code == 404, f"못 쓰게 한 링크가 {dead.status_code} 를 냈다"
    assert await _kinds(database) == [
        ("link_created", "kim.min", "root.one"),
        ("account_disabled", "kim.min", "root.one"),
        ("login_failed", "kim.min", None),
    ]
    # 비활성인 계정은 어차피 갱신도 링크도 받지 않는다. 끊고 못 쓰게 한 것은 되돌린 뒤에 드러난다
    await client.put("/accounts/kim.min/active", json={"active": True}, headers=boss)
    revived = await client.post("/auth/refresh", headers=later)
    assert revived.status_code == 401, (
        f"되돌린 뒤 끊긴 로그인의 갱신이 {revived.status_code} 를 냈다"
    )
    again = await _set(client, token)
    assert again.status_code == 404, f"되돌린 뒤 못 쓰게 한 링크가 {again.status_code} 를 냈다"


async def test_되돌리면_비밀번호가_있던_계정은_로그인하고_없던_계정은_비밀번호_미설정으로_돌아간다(
    client: AsyncClient, accounts: AccountStore
) -> None:
    boss = await _boss(client, accounts)
    await _seed(accounts, "kim.min")
    await _create(client, boss, "new.user")
    for name in ("kim.min", "new.user"):
        await client.put(f"/accounts/{name}/active", json={"active": False}, headers=boss)

    for name in ("kim.min", "new.user"):
        back = await client.put(f"/accounts/{name}/active", json={"active": True}, headers=boss)
        assert back.status_code == 204

    states = {
        row["name"]: row["state"]
        for row in (await client.get("/accounts", headers=boss)).json()["accounts"]
    }
    assert states["kim.min"] == "active"
    assert states["new.user"] == "password_unset"
    assert (await _login(client, "kim.min")).status_code == 204
    assert (await _login(client, "new.user", NEW)).status_code == 401


async def test_이미_그_상태면_아무것도_바꾸지_않고_204이며_기록도_남기지_않는다(
    client: AsyncClient, accounts: AccountStore, database: ScopedDatabase
) -> None:
    boss = await _boss(client, accounts)
    await _seed(accounts, "kim.min")

    already_on = await client.put("/accounts/kim.min/active", json={"active": True}, headers=boss)
    await client.put("/accounts/kim.min/active", json={"active": False}, headers=boss)
    already_off = await client.put("/accounts/kim.min/active", json={"active": False}, headers=boss)

    assert already_on.status_code == 204
    assert already_off.status_code == 204
    assert await _kinds(database) == [("account_disabled", "kim.min", "root.one")]


async def test_활성_바꾸기의_거절은_없는_계정_404와_시스템_관리자_409와_엄격한_불린_422이다(
    client: AsyncClient, accounts: AccountStore, database: ScopedDatabase
) -> None:
    boss = await _boss(client, accounts)
    await _seed(accounts, "kim.min")

    absent = await client.put("/accounts/ghost.one/active", json={"active": False}, headers=boss)
    system = await client.put("/accounts/root.one/active", json={"active": False}, headers=boss)
    forms = [
        await client.put("/accounts/kim.min/active", json=body, headers=boss)
        for body in ({"active": "false"}, {"active": 0}, {}, {"active": False, "x": 1})
    ]

    assert absent.status_code == 404
    assert system.status_code == 409
    assert [each.status_code for each in forms] == [422] * 4
    assert _field(forms[0]) == "body.active"
    assert (await _row(database, "kim.min"))[2] is None
    assert (await _row(database, "root.one"))[2] is None


# --- 잠금 풀기 -----------------------------------------------------------------------------------


async def test_잠금_풀기는_잠금과_틀린_횟수를_지우고_풀_것이_있었을_때만_기록한다(
    client: AsyncClient, accounts: AccountStore, database: ScopedDatabase
) -> None:
    boss = await _boss(client, accounts)
    await _seed(accounts, "kim.min")
    for _ in range(5):
        await _login(client, "kim.min", WRONG)
    assert (await _login(client, "kim.min")).status_code == 401

    unlocked = await client.post("/accounts/kim.min/unlock", headers=boss)
    nothing = await client.post("/accounts/kim.min/unlock", headers=boss)
    absent = await client.post("/accounts/ghost.one/unlock", headers=boss)

    assert unlocked.status_code == 204
    assert nothing.status_code == 204
    assert absent.status_code == 404
    row = await _row(database, "kim.min")
    assert (row[3], row[4]) == (0, None)
    assert (await _login(client, "kim.min")).status_code == 204
    kinds = [kind for kind, _, _ in await _kinds(database)]
    assert kinds.count("unlocked") == 1, f"풀림 기록이 {kinds.count('unlocked')} 줄이다"
    assert ("unlocked", "kim.min", "root.one") in await _kinds(database)


async def test_틀린_횟수만_쌓이고_잠기지_않은_계정도_풀_것이_있어_기록한다(
    client: AsyncClient, accounts: AccountStore, database: ScopedDatabase
) -> None:
    boss = await _boss(client, accounts)
    await _seed(accounts, "kim.min")
    await _login(client, "kim.min", WRONG)

    await client.post("/accounts/kim.min/unlock", headers=boss)

    assert (await _row(database, "kim.min"))[3] == 0
    assert ("unlocked", "kim.min", "root.one") in await _kinds(database)


# --- 권한 ----------------------------------------------------------------------------------------

_FIVE = [
    ("GET", "/accounts", None),
    ("POST", "/accounts", {"name": "new.user"}),
    ("POST", "/accounts/kim.min/link", None),
    ("PUT", "/accounts/kim.min/active", {"active": False}),
    ("POST", "/accounts/kim.min/unlock", None),
]


@pytest.mark.parametrize(("method", "path", "body"), _FIVE)
async def test_관리자_단계는_계정을_다루는_경로_다섯_모두에서_403이다(
    method: str,
    path: str,
    body: dict[str, object] | None,
    client: AsyncClient,
    accounts: AccountStore,
) -> None:
    await _seed(accounts, "kim.min")
    admin = await _session(client, accounts, "lee.jin")

    response = await client.request(method, path, json=body, headers=admin)

    assert response.status_code == 403, f"{method} {path} 가 {response.status_code} 를 냈다"
    assert response.json()["code"] == "forbidden"
    assert response.json()["message"] == FORBIDDEN_FOR_ACCOUNT_MESSAGE


@pytest.mark.parametrize(("method", "path", "body"), _FIVE)
async def test_자격이_없으면_계정을_다루는_경로_다섯_모두에서_401이다(
    method: str, path: str, body: dict[str, object] | None, client: AsyncClient
) -> None:
    response = await client.request(method, path, json=body)

    assert response.status_code == 401


@pytest.mark.parametrize(("method", "path", "body"), _FIVE)
async def test_옛_공유_토큰은_계정을_다루는_경로_다섯_모두에서_401이다(
    method: str,
    path: str,
    body: dict[str, object] | None,
    client: AsyncClient,
    accounts: AccountStore,
) -> None:
    await _seed(accounts, "kim.min")

    response = await client.request(method, path, json=body, headers=OLD_SHARED)

    assert response.status_code == 401
    assert "www-authenticate" not in response.headers


async def test_권한이_없으면_칸이_틀린_JSON_본문도_403이고_JSON이_아닌_본문은_422이다(
    client: AsyncClient, accounts: AccountStore
) -> None:
    admin = await _session(client, accounts, "lee.jin")
    wrong_fields = await client.post("/accounts", json={"nope": 1}, headers=admin)
    wrong_active = await client.put(
        "/accounts/kim.min/active", json={"active": "maybe"}, headers=admin
    )
    not_json = await client.post(
        "/accounts",
        content=b"this is not json",
        headers={**admin, "Content-Type": "application/json"},
    )

    assert wrong_fields.status_code == 403
    assert wrong_active.status_code == 403
    assert not_json.status_code == 422


async def test_옛_공유_토큰은_내_비밀번호_바꾸기에서_401이다(client: AsyncClient) -> None:
    response = await client.post(
        "/auth/password",
        json={"current_password": PASSWORD, "new_password": NEW},
        headers=OLD_SHARED,
    )

    assert response.status_code == 401
    # 운영자 경로의 401 은 챌린지를 싣지 않는다(`Authorization` 머리를 읽지 않는다)
    challenge = response.headers.get("www-authenticate")
    assert challenge is None, f"챌린지 {challenge}"


async def test_요청_출처가_다르면_새_경로_둘도_403이다(
    client: AsyncClient, accounts: AccountStore
) -> None:
    boss = await _boss(client, accounts)
    cross = {"Sec-Fetch-Site": "cross-site"}

    unlinked = await client.post(
        "/auth/set-password", json={"token": STRANGER, "password": NEW}, headers=cross
    )
    accounts_list = await client.get("/accounts", headers={**boss, **cross})

    assert unlinked.status_code == 403
    assert accounts_list.status_code == 403


# --- 내 비밀번호 바꾸기 --------------------------------------------------------------------------


async def _change(client: AsyncClient, headers: dict[str, str], current: str, new: str) -> Response:
    return await client.post(
        "/auth/password", json={"current_password": current, "new_password": new}, headers=headers
    )


async def test_내_비밀번호를_바꾸면_204이고_바꾼_로그인만_남고_다른_로그인은_끊긴다(
    client: AsyncClient, accounts: AccountStore, database: ScopedDatabase
) -> None:
    await _seed(accounts, "kim.min")
    here = _both(await _login(client, "kim.min"))
    elsewhere = _both(await _login(client, "kim.min"))

    response = await _change(client, here, PASSWORD, NEW)

    assert response.status_code == 204
    assert response.content == b""
    assert (await client.get("/auth/me", headers=here)).status_code == 200
    kept = await client.post("/auth/refresh", headers=here)
    assert kept.status_code == 204, f"바꾼 로그인의 갱신이 {kept.status_code} 를 냈다"
    assert (await client.post("/auth/refresh", headers=elsewhere)).status_code == 401
    assert (await _login(client, "kim.min", PASSWORD)).status_code == 401
    assert (await _login(client, "kim.min", NEW)).status_code == 204
    assert ("password_changed", "kim.min", None) in await _kinds(database)


async def test_틀린_지금_비밀번호는_422이고_다섯째_틀림부터_잠가_맞아도_409이다(
    client: AsyncClient, accounts: AccountStore, clock: MovingClock, database: ScopedDatabase
) -> None:
    await _seed(accounts, "kim.min")
    here = _both(await _login(client, "kim.min"))

    for count in range(1, 5):
        wrong = await _change(client, here, WRONG, NEW)
        assert wrong.status_code == 422
        assert _field(wrong) == "body.current_password"
        assert wrong.json()["violations"][0]["message"] == WRONG_CURRENT
        failures = (await _row(database, "kim.min"))[3]
        assert failures == count, f"{count} 번째 뒤 틀린 횟수가 {failures} 이다"
    assert "locked" not in [kind for kind, _, _ in await _kinds(database)]

    fifth = await _change(client, here, WRONG, NEW)
    locked = await _change(client, here, PASSWORD, NEW)

    assert fifth.status_code == 422
    assert locked.status_code == 409
    assert locked.json()["code"] == "conflict"
    assert locked.json()["message"] == LOCKED
    assert (await _row(database, "kim.min"))[3:] == (5, START + timedelta(minutes=1))
    assert [kind for kind, _, _ in await _kinds(database)].count("locked") == 1
    # 잠긴 동안은 횟수가 늘지 않고, 풀린 뒤에는 맞는 비밀번호로 바뀐다
    clock.advance(minutes=1)
    assert (await _change(client, here, PASSWORD, NEW)).status_code == 204


async def test_네_번_틀린_뒤_맞는_지금_비밀번호는_바꾸고_틀린_횟수를_지운다(
    client: AsyncClient, accounts: AccountStore, database: ScopedDatabase
) -> None:
    await _seed(accounts, "kim.min")
    here = _both(await _login(client, "kim.min"))
    for _ in range(4):
        await _change(client, here, WRONG, NEW)

    response = await _change(client, here, PASSWORD, NEW)

    assert response.status_code == 204
    row = await _row(database, "kim.min")
    assert (row[3], row[4]) == (0, None)
    assert "locked" not in [kind for kind, _, _ in await _kinds(database)]


async def test_새_비밀번호가_규칙을_어기면_422이고_틀린_횟수에_들지_않는다(
    client: AsyncClient, accounts: AccountStore, database: ScopedDatabase
) -> None:
    await _seed(accounts, "kim.min")
    here = _both(await _login(client, "kim.min"))

    for current in (PASSWORD, WRONG):
        for _ in range(6):
            response = await _change(client, here, current, WEAK)
            assert response.status_code == 422, f"약한 새 비밀번호가 {response.status_code} 를 냈다"
            assert _field(response) == "body.new_password"
            assert response.json()["violations"][0]["message"] == PASSWORD_RULE_TEXT

    assert (await _row(database, "kim.min"))[3:] == (0, None)
    assert (await _login(client, "kim.min", PASSWORD)).status_code == 204


@pytest.mark.parametrize(
    "body",
    [
        {"current_password": PASSWORD},
        {"new_password": NEW},
        {"current_password": "", "new_password": NEW},
        {"current_password": PASSWORD, "new_password": NEW, "extra": 1},
        {"current_password": "p" * 1025, "new_password": NEW},
    ],
)
async def test_내_비밀번호_바꾸기의_본문이_틀리면_422이고_값을_되울리지_않는다(
    body: dict[str, object], client: AsyncClient, accounts: AccountStore
) -> None:
    here = await _session(client, accounts, "kim.min")

    response = await client.post("/auth/password", json=body, headers=here)

    assert response.status_code == 422
    assert PASSWORD not in response.text
    assert NEW not in response.text


def _race(
    monkeypatch: pytest.MonkeyPatch,
    loop: asyncio.AbstractEventLoop,
    database: ScopedDatabase,
    sql: str,
    **params: object,
) -> list[str]:
    """맞는 견줌이 끝난 직후, 둘째 트랜잭션이 열리기 전에 계정을 바꾼다(`test_login_http` 와 같은
    길). 돌려주는 목록에는 계정을 실제로 바꾼 횟수만큼 글자가 쌓인다."""
    real = logins_module.password_matches
    changed: list[str] = []

    def racing(stored_hash: str, password: str) -> bool:
        matched = real(stored_hash, password)
        if matched:
            asyncio.run_coroutine_threadsafe(_execute(database, sql, **params), loop).result(10)
            changed.append(sql)
        return matched

    monkeypatch.setattr(logins_module, "password_matches", racing)
    return changed


async def test_견준_뒤_저장하기_전에_링크로_비밀번호가_정해지면_422이고_링크로_정한_해시가_남는다(
    client: AsyncClient,
    accounts: AccountStore,
    database: ScopedDatabase,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _seed(accounts, "kim.min")
    here = _both(await _login(client, "kim.min"))
    by_link = hash_password(LINKED)
    changed = _race(
        monkeypatch,
        asyncio.get_running_loop(),
        database,
        "UPDATE operator_accounts SET password_hash = :hash WHERE name = 'kim.min'",
        hash=by_link,
    )

    response = await _change(client, here, PASSWORD, NEW)

    assert len(changed) == 1, "견주는 사이에 계정이 바뀌지 않았다. 시험이 경합을 만들지 못했다"
    assert response.status_code == 422, f"경합 뒤 바꾸기가 {response.status_code} 를 냈다"
    assert _field(response) == "body.current_password"
    assert response.json()["violations"][0]["message"] == WRONG_CURRENT
    assert (await _row(database, "kim.min"))[1] == by_link
    assert "password_changed" not in [kind for kind, _, _ in await _kinds(database)]


async def test_견주는_사이_계정이_꺼지면_바꾸지_않고_401이다(
    client: AsyncClient,
    accounts: AccountStore,
    database: ScopedDatabase,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _seed(accounts, "kim.min")
    here = _both(await _login(client, "kim.min"))
    before = (await _row(database, "kim.min"))[1]
    changed = _race(
        monkeypatch,
        asyncio.get_running_loop(),
        database,
        "UPDATE operator_accounts SET disabled_at = :at WHERE name = 'kim.min'",
        at=START,
    )

    response = await _change(client, here, PASSWORD, NEW)

    assert len(changed) == 1, "견주는 사이에 계정이 바뀌지 않았다. 시험이 경합을 만들지 못했다"
    # 비활성이 된 계정은 로그인과 같이 더는 로그인할 수 없는 계정이라 401 이다
    assert response.status_code == 401
    assert (await _row(database, "kim.min"))[1] == before


# --- 비밀번호와 링크가 어디에도 실리지 않는다 ---------------------------------------------------


async def test_로그인_기록과_서버_기록과_응답에_비밀번호와_링크_토큰이_실리지_않는다(
    client: AsyncClient, accounts: AccountStore, stderr: io.StringIO, database: ScopedDatabase
) -> None:
    boss = await _boss(client, accounts)
    responses: list[Response] = []
    token = await _create(client, boss, "new.user")
    again = await _link(client, boss, "new.user")
    responses.append(await _set(client, token, CANARY))
    responses.append(await _set(client, again, CANARY))
    responses.append(await _set(client, again, WEAK))
    here = _both(await _login(client, "new.user", CANARY))
    responses.append(await _change(client, here, WRONG, CANARY))
    responses.append(await _change(client, here, CANARY, WEAK))
    responses.append(await _change(client, here, CANARY, LINKED))
    responses.append(await client.get("/accounts", headers=boss))

    records = await _rows(database, "SELECT * FROM operator_login_records")
    links = await _rows(database, "SELECT * FROM operator_password_links")
    everything = repr(records) + stderr.getvalue() + "".join(each.text for each in responses)
    for secret in (CANARY, WRONG, LINKED, WEAK):
        assert secret not in everything
    for hidden in (token, again):
        assert hidden not in repr(records)
        assert hidden not in stderr.getvalue()
        assert hidden not in repr(links)
    assert "$argon2" not in repr(records)
    assert "$argon2" not in stderr.getvalue()
    assert records, "기록이 비었다. 시험이 아무것도 보지 못했다"
