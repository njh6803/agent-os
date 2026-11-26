"""로그인, 로그아웃, 지금 누구인지, 첫 계정 확인(`/auth/*`)을 앱에 넣어 바깥 행동만 본다.

계정 저장소는 가짜가 아니라 시험마다 복제한 진짜 데이터베이스다. 잠금의 횟수 세기와 줄 잠금,
로그인 한 건과 갱신용 번호 해시의 기록, 서명 키의 줄이 모두 데이터베이스에서 일어나기 때문이다.
시계는 시험이 움직이는 가짜 시계 하나이고 앱과 서비스와 데이터베이스에 적는 시각이 모두 이것을
따른다. 기준 주소는 `https://admin.test` 다. httpx 는 `http` 에서 `Secure` 쿠키를 싣지 않는다.

비밀번호와 갱신용 번호와 해시가 기록과 서버 기록과 응답에 실리지 않는지는 카나리아(일부러 심은
글)로 찾는다.
"""

from __future__ import annotations

import asyncio
import hashlib
import io
import logging
import re
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient, Response
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from sqlalchemy import text
from tests.fake_accounts import UnusedAccounts
from tests.fake_database import FakeDatabase
from tests.fake_models import DEFAULT_MODEL, FakeModels
from tests.postgres_support import plain
from tests.test_server import ORIGIN_CASES, FakePlugins, FakeTrace, IdleTools
from tools.database_for_tests import ScopedDatabase

from agent_os.adapters.postgres.database import PostgresDatabase, parse_database_url
from agent_os.channel.http.end_user import END_USER_PREFIX
from agent_os.channel.http.router import CHANNEL_PREFIX
from agent_os.core.ports import Clock
from agent_os.http import logins as logins_module
from agent_os.http.accounts import AccountStore, Tier
from agent_os.http.auth import PUBLIC_PATHS
from agent_os.http.errors import UNAUTHORIZED_MESSAGE
from agent_os.http.login_tokens import ACCESS_COOKIE, REFRESH_COOKIE, LoginDurations
from agent_os.http.logins import LoginService, SigningKeys
from agent_os.http.passwords import hash_password
from agent_os.http.sites import Sites
from agent_os.sdk import Principal, RunId
from agent_os.server import create_app

START = datetime(2026, 11, 26, 9, 0, tzinfo=UTC)
PASSWORD = "Correct-horse-9!"
WRONG = "Wrong-horse-9!"
CANARY = "Canary-pass-77!"
ADMIN_TOKEN = "adm1n-t0ken-that-only-tests-know"
CHANNEL_TOKEN = "channel-t0ken-that-only-tests-know"
SHARED = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
REFUSED = "로그인하지 못했다"


class MovingClock:
    """시험이 움직이는 시계. 앱과 서비스와 데이터베이스에 적는 시각이 모두 이것을 따른다."""

    def __init__(self) -> None:
        self.at = START

    def now(self) -> datetime:
        return self.at

    def new_run_id(self) -> RunId:
        raise NotImplementedError("로그인은 실행을 일으키지 않는다")

    def advance(self, **delta: float) -> None:
        self.at += timedelta(**delta)


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
        admin_token=ADMIN_TOKEN,
        channel_token=CHANNEL_TOKEN,
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
    app = _app(accounts, clock, stderr)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="https://admin.test") as opened:
        yield opened


async def _seed(
    accounts: AccountStore,
    name: str,
    *,
    tier: Tier = "admin",
    password: str = PASSWORD,
    password_hash: str | None = None,
) -> None:
    stored = password_hash if password_hash is not None else hash_password(password)
    async with accounts.transaction() as work:
        await work.add(NewAccount(name=name, tier=tier, password_hash=stored, created_at=START))


async def _rows(database: ScopedDatabase, sql: str, **params: object) -> list[tuple[object, ...]]:
    async with plain(database) as connection:
        result = await connection.execute(text(sql), params)
        return [tuple(row) for row in result.all()]


async def _execute(database: ScopedDatabase, sql: str, **params: object) -> None:
    async with plain(database, autocommit=True) as connection:
        await connection.execute(text(sql), params)


async def _records(database: ScopedDatabase) -> list[tuple[str, str | None, str | None]]:
    rows = await _rows(
        database, "SELECT kind, account, address FROM operator_login_records ORDER BY seq"
    )
    return [(str(kind), _optional(account), _optional(address)) for kind, account, address in rows]


def _optional(value: object) -> str | None:
    return None if value is None else str(value)


async def _login(
    client: AsyncClient, name: str = "kim.min", password: str = PASSWORD, **headers: str
) -> Response:
    response = await client.post(
        "/auth/login", json={"name": name, "password": password}, headers=headers
    )
    # httpx 는 `Secure` 쿠키를 보관통에 넣고 다음 요청에 스스로 싣는다. 이 시험은 쿠키를 머리로
    # 직접 싣고 어느 요청에 무엇이 실렸는지를 단언하므로 보관통을 늘 비워 둔다.
    client.cookies.clear()
    return response


def _cookies(response: Response) -> dict[str, str]:
    """`Set-Cookie` 줄에서 이름과 값을 뽑는다."""
    found: dict[str, str] = {}
    for line in response.headers.get_list("set-cookie"):
        name, _, rest = line.partition("=")
        found[name] = rest.partition(";")[0]
    return found


def _as_cookie(response: Response) -> dict[str, str]:
    cookies = _cookies(response)
    return {"Cookie": f"{ACCESS_COOKIE}={cookies[ACCESS_COOKIE]}"}


def _without_request_id(response: Response) -> tuple[int, object, dict[str, str]]:
    body: dict[str, object] = response.json()
    body.pop("request_id", None)
    headers = {key: value for key, value in response.headers.items() if key != "x-request-id"}
    return response.status_code, body, headers


# --- 로그인 성공 ---------------------------------------------------------------------------------


async def test_맞는_비밀번호면_204와_쿠키_둘을_심고_로그인_한_건을_남긴다(
    client: AsyncClient, accounts: AccountStore, database: ScopedDatabase
) -> None:
    await _seed(accounts, "kim.min")

    response = await _login(client)

    assert response.status_code == 204
    assert response.content == b""
    lines = response.headers.get_list("set-cookie")
    assert len(lines) == 2
    access = next(line for line in lines if line.startswith(f"{ACCESS_COOKIE}="))
    refresh = next(line for line in lines if line.startswith(f"{REFRESH_COOKIE}="))
    for line in lines:
        assert "HttpOnly" in line
        assert "Secure" in line
        assert "SameSite=Strict" in line
        assert "Path=/" in line
        assert "Domain" not in line
    assert "Max-Age" not in access
    assert "Max-Age=1800" in refresh
    logins = await _rows(database, "SELECT account, logged_in_at, ended_at FROM operator_logins")
    assert logins == [("kim.min", START, None)]
    assert await _records(database) == [("login_succeeded", "kim.min", None)]


async def test_갱신용_번호는_해시만_저장하고_쿠키에는_원문이_간다(
    client: AsyncClient, accounts: AccountStore, database: ScopedDatabase
) -> None:
    await _seed(accounts, "kim.min")

    response = await _login(client)

    refresh = _cookies(response)[REFRESH_COOKIE]
    stored = await _rows(database, "SELECT token_hash, used_at FROM operator_refresh_tokens")
    assert stored == [(hashlib.sha256(refresh.encode("ascii")).hexdigest(), None)]
    assert refresh not in repr(stored)


async def test_대문자로_적은_이름도_같은_계정으로_로그인하고_이름은_소문자로_답한다(
    client: AsyncClient, accounts: AccountStore
) -> None:
    await _seed(accounts, "kim.dev")

    response = await _login(client, name="Kim.Dev")
    me = await client.get("/auth/me", headers=_as_cookie(response))

    assert response.status_code == 204
    assert me.json()["name"] == "kim.dev"


async def test_맞은_로그인은_틀린_횟수를_지운다(
    client: AsyncClient, accounts: AccountStore, database: ScopedDatabase
) -> None:
    await _seed(accounts, "kim.min")
    for _ in range(3):
        await _login(client, password=WRONG)

    await _login(client)

    assert await _rows(database, "SELECT failures, locked_until FROM operator_accounts") == [
        (0, None)
    ]


async def test_저장된_해시의_매개변수가_옛것이면_맞은_로그인에서_새로_해시한다(
    client: AsyncClient, accounts: AccountStore, database: ScopedDatabase
) -> None:
    from argon2 import PasswordHasher

    from agent_os.http.passwords import normalize_password

    weak = PasswordHasher(time_cost=1, memory_cost=8, parallelism=1).hash(
        normalize_password(PASSWORD)
    )
    await _seed(accounts, "kim.min", password_hash=weak)

    response = await _login(client)

    assert response.status_code == 204
    (stored,) = await _rows(database, "SELECT password_hash FROM operator_accounts")
    assert stored != (weak,)
    assert str(stored[0]).startswith("$argon2id$v=19$m=19456,t=2,p=1$")
    assert (await _login(client)).status_code == 204


async def test_다시_로그인하면_끝났거나_쉬었거나_너무_오래된_로그인과_그_번호를_치운다(
    client: AsyncClient, accounts: AccountStore, clock: MovingClock, database: ScopedDatabase
) -> None:
    await _seed(accounts, "kim.min")

    def digest(response: Response) -> str:
        return hashlib.sha256(_cookies(response)[REFRESH_COOKIE].encode("ascii")).hexdigest()

    # 첫째는 로그아웃으로 끝내고, 둘째는 살려 둔다. 셋째 로그인이 치우는 것은 끝난 첫째뿐이다
    first = await _login(client)
    second = await _login(client)
    await client.post("/auth/logout", headers=_as_cookie(first))
    (ended,) = await _rows(database, "SELECT id FROM operator_logins WHERE ended_at IS NOT NULL")
    (alive,) = await _rows(database, "SELECT id FROM operator_logins WHERE ended_at IS NULL")

    clock.advance(minutes=1)
    third = await _login(client)

    ids = {row[0] for row in await _rows(database, "SELECT id FROM operator_logins")}
    assert len(ids) == 2
    assert ended[0] not in ids
    assert alive[0] in ids
    stored = {
        row[0] for row in await _rows(database, "SELECT token_hash FROM operator_refresh_tokens")
    }
    assert stored == {digest(second), digest(third)}
    assert digest(first) not in stored


# --- 로그인 실패 ---------------------------------------------------------------------------------


async def test_실패의_답은_네_갈래가_같다(
    client: AsyncClient, accounts: AccountStore, database: ScopedDatabase
) -> None:
    await _seed(accounts, "kim.min")
    await _seed(accounts, "off.one")
    await _seed(accounts, "blank.pw")
    await _execute(
        database, "UPDATE operator_accounts SET password_hash = NULL WHERE name = 'blank.pw'"
    )
    await _execute(
        database, "UPDATE operator_accounts SET disabled_at = :at WHERE name = 'off.one'", at=START
    )

    wrong = await _login(client, password=WRONG)
    unknown = await _login(client, name="nobody")
    disabled = await _login(client, name="off.one")
    blank = await _login(client, name="blank.pw")

    answers = [_without_request_id(each) for each in (wrong, unknown, disabled, blank)]
    assert answers[0][0] == 401
    assert answers[0][1] == {"code": "unauthorized", "message": REFUSED, "violations": []}
    assert answers[1:] == [answers[0]] * 3
    for each in (wrong, unknown, disabled, blank):
        assert "set-cookie" not in each.headers
    # 로그인 실패는 `Authorization` 머리를 받는 자리가 아니라 Bearer 챌린지를 싣지 않는다.
    # 미들웨어의 401(자격이 없는 요청)만 싣는다(`/auth/me` 시험)
    assert "www-authenticate" not in wrong.headers


async def test_실패의_기록은_계정이_있을_때만_이름을_적고_없는_이름은_남기지_않는다(
    client: AsyncClient, accounts: AccountStore, database: ScopedDatabase
) -> None:
    await _seed(accounts, "kim.min")

    await _login(client, password=WRONG)
    await _login(client, name="canary.name")

    assert await _records(database) == [
        ("login_failed", "kim.min", None),
        ("login_failed", None, None),
    ]


async def test_이름이_규칙에_맞지_않는_이름은_데이터베이스를_읽지_않고_401이다(
    client: AsyncClient,
) -> None:
    response = await _login(client, name="a b")

    assert response.status_code == 401
    assert response.json()["message"] == REFUSED


async def test_본문이_틀리면_422이고_비밀번호_값을_되울리지_않는다(client: AsyncClient) -> None:
    extra = await client.post("/auth/login", json={"name": "a", "password": CANARY, "x": 1})
    empty = await client.post("/auth/login", json={"name": "", "password": CANARY})
    missing = await client.post("/auth/login", json={"name": "kim.min"})

    for response in (extra, empty, missing):
        assert response.status_code == 422
        assert response.json()["code"] == "invalid_request"
        assert CANARY not in response.text


# --- 잠금 ----------------------------------------------------------------------------------------


async def test_다섯_번째_틀림이_1분_잠그고_잠긴_동안은_맞아도_거절되며_횟수는_늘지_않는다(
    client: AsyncClient, accounts: AccountStore, clock: MovingClock, database: ScopedDatabase
) -> None:
    await _seed(accounts, "kim.min")
    for _ in range(5):
        assert (await _login(client, password=WRONG)).status_code == 401
    locked_until = START + timedelta(minutes=1)
    assert await _rows(database, "SELECT failures, locked_until FROM operator_accounts") == [
        (5, locked_until)
    ]

    for _ in range(3):
        assert (await _login(client)).status_code == 401

    assert await _rows(database, "SELECT failures, locked_until FROM operator_accounts") == [
        (5, locked_until)
    ]
    clock.advance(seconds=59)
    assert (await _login(client)).status_code == 401
    clock.advance(seconds=1)
    assert (await _login(client)).status_code == 204
    assert await _rows(database, "SELECT failures, locked_until FROM operator_accounts") == [
        (0, None)
    ]


async def test_잠금_기록은_잠근_시도에만_한_줄_더_적힌다(
    client: AsyncClient, accounts: AccountStore, database: ScopedDatabase
) -> None:
    await _seed(accounts, "kim.min")
    for _ in range(5):
        await _login(client, password=WRONG)
    await _login(client)

    kinds = [kind for kind, _, _ in await _records(database)]
    assert kinds == ["login_failed"] * 5 + ["locked", "login_failed"]


async def test_다섯_번째에_맞는_비밀번호는_로그인이고_잠그지도_잠김을_적지도_않는다(
    client: AsyncClient, accounts: AccountStore, database: ScopedDatabase
) -> None:
    await _seed(accounts, "kim.min")
    for _ in range(4):
        await _login(client, password=WRONG)

    response = await _login(client)

    assert response.status_code == 204
    assert await _rows(database, "SELECT failures, locked_until FROM operator_accounts") == [
        (0, None)
    ]
    kinds = [kind for kind, _, _ in await _records(database)]
    assert "locked" not in kinds


async def test_잠금이_풀린_뒤_또_틀리면_잠금이_두_배로_길어진다(
    client: AsyncClient, accounts: AccountStore, clock: MovingClock, database: ScopedDatabase
) -> None:
    await _seed(accounts, "kim.min")
    for _ in range(5):
        await _login(client, password=WRONG)
    clock.advance(minutes=1)

    await _login(client, password=WRONG)

    assert await _rows(database, "SELECT failures, locked_until FROM operator_accounts") == [
        (6, clock.at + timedelta(minutes=2))
    ]


async def test_동시에_다섯_번_틀리면_뒤따르는_맞는_로그인도_잠겨_401이다(
    client: AsyncClient, accounts: AccountStore, database: ScopedDatabase
) -> None:
    """동시 요청이 몇 번째로 줄을 잡았는지는 정해져 있지 않으므로 횟수의 값이 아니라 결과만 본다.
    다섯 번이 모두 줄을 잠그고 미리 세므로 하나도 잃지 않고 잠금에 닿는다."""
    await _seed(accounts, "kim.min")

    responses = await asyncio.gather(*(_login(client, password=WRONG) for _ in range(5)))

    assert [each.status_code for each in responses] == [401] * 5
    after = await _login(client)
    assert after.status_code == 401
    assert "set-cookie" not in after.headers
    assert await _rows(database, "SELECT id FROM operator_logins") == []
    kinds = [kind for kind, _, _ in await _records(database)]
    assert kinds.count("locked") == 1


async def test_동시에_네_번_틀려도_잠기지_않아_맞는_로그인이_지난다(
    client: AsyncClient, accounts: AccountStore, database: ScopedDatabase
) -> None:
    await _seed(accounts, "kim.min")

    await asyncio.gather(*(_login(client, password=WRONG) for _ in range(4)))

    assert "locked" not in [kind for kind, _, _ in await _records(database)]
    assert (await _login(client)).status_code == 204


async def test_다른_계정의_잠금은_이_계정의_로그인을_막지_않는다(
    client: AsyncClient, accounts: AccountStore
) -> None:
    await _seed(accounts, "kim.min")
    await _seed(accounts, "lee.jin")
    for _ in range(5):
        await _login(client, password=WRONG)

    assert (await _login(client, name="lee.jin")).status_code == 204


# --- 견주는 사이에 바뀐 계정 ---------------------------------------------------------------------


def _race(
    monkeypatch: pytest.MonkeyPatch,
    loop: asyncio.AbstractEventLoop,
    database: ScopedDatabase,
    sql: str,
    **params: object,
) -> list[str]:
    """맞는 견줌이 끝난 직후, 둘째 트랜잭션이 열리기 전에 계정을 바꾼다.

    견줌은 해시 전용 스레드에서 도므로 그 스레드가 시험의 이벤트 루프에 일을 맡기고 기다린다.
    돌려주는 목록에는 계정을 실제로 바꾼 횟수만큼 글자가 쌓인다. 견줌이 맞지 않으면 바꾸지 않아
    시험이 바뀐 계정 없이도 초록이 되므로, 시험은 이 목록이 찼는지 단언한다.
    """
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


async def test_견주는_사이_비밀번호가_바뀌면_맞았어도_로그인이_아니다(
    client: AsyncClient,
    accounts: AccountStore,
    database: ScopedDatabase,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _seed(accounts, "kim.min")
    changed = _race(
        monkeypatch,
        asyncio.get_running_loop(),
        database,
        "UPDATE operator_accounts SET password_hash = :hash WHERE name = 'kim.min'",
        hash=hash_password("Another-pass-1!"),
    )

    response = await _login(client)

    assert len(changed) == 1, "견주는 사이에 계정이 바뀌지 않았다. 시험이 경합을 만들지 못했다"
    assert response.status_code == 401
    assert "set-cookie" not in response.headers
    assert await _rows(database, "SELECT id FROM operator_logins") == []
    kinds = [kind for kind, _, _ in await _records(database)]
    assert "login_succeeded" not in kinds


async def test_견주는_사이_계정이_꺼지면_맞았어도_로그인이_아니다(
    client: AsyncClient,
    accounts: AccountStore,
    database: ScopedDatabase,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _seed(accounts, "kim.min")
    changed = _race(
        monkeypatch,
        asyncio.get_running_loop(),
        database,
        "UPDATE operator_accounts SET disabled_at = :at WHERE name = 'kim.min'",
        at=START,
    )

    response = await _login(client)

    assert len(changed) == 1, "견주는 사이에 계정이 바뀌지 않았다. 시험이 경합을 만들지 못했다"
    assert response.status_code == 401
    assert await _rows(database, "SELECT id FROM operator_logins") == []


async def test_다섯째_시도의_비밀번호가_맞았으면_둘째_트랜잭션이_거절해도_잠금은_기록하지_않는다(
    client: AsyncClient,
    accounts: AccountStore,
    database: ScopedDatabase,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    await _seed(accounts, "kim.min")
    for _ in range(4):
        await _login(client, password=WRONG)
    changed = _race(
        monkeypatch,
        asyncio.get_running_loop(),
        database,
        "UPDATE operator_accounts SET disabled_at = :at WHERE name = 'kim.min'",
        at=START,
    )

    response = await _login(client)

    assert len(changed) == 1, "견주는 사이에 계정이 바뀌지 않았다. 시험이 경합을 만들지 못했다"
    assert response.status_code == 401
    # 잠금은 틀린 비밀번호가 건다. 맞은 시도를 마무리하다 거절된 것은 실패 한 줄이면 된다
    kinds = [kind for kind, _, _ in await _records(database)]
    assert kinds.count("login_failed") == 5
    assert "locked" not in kinds


# --- 짧은 JWT 와 지금 누구인지 ------------------------------------------------------------------


async def test_지금_누구인지는_쿠키의_짧은_JWT_만_보고_이름과_단계와_두_시간을_답한다(
    client: AsyncClient, accounts: AccountStore
) -> None:
    await _seed(accounts, "root.one", tier="system_admin")

    response = await _login(client, name="root.one")
    me = await client.get("/auth/me", headers=_as_cookie(response))

    assert me.status_code == 200
    assert me.json() == {
        "name": "root.one",
        "tier": "system_admin",
        "token_minutes": 5,
        "run_timeout_seconds": 600.0,
    }


async def test_짧은_JWT_는_수명이_끝나면_통하지_않는다(
    client: AsyncClient, accounts: AccountStore, clock: MovingClock
) -> None:
    await _seed(accounts, "kim.min")
    cookie = _as_cookie(await _login(client))

    clock.advance(minutes=5, seconds=-1)
    assert (await client.get("/auth/me", headers=cookie)).status_code == 200
    clock.advance(seconds=1)
    assert (await client.get("/auth/me", headers=cookie)).status_code == 401
    assert (await client.get("/plugins", headers=cookie)).status_code == 401


async def test_쿠키가_없거나_깨졌으면_지금_누구인지는_401이다(client: AsyncClient) -> None:
    none = await client.get("/auth/me")
    garbage = await client.get("/auth/me", headers={"Cookie": f"{ACCESS_COOKIE}=abc.def.ghi"})

    assert none.status_code == 401
    assert garbage.status_code == 401
    assert none.headers["www-authenticate"] == "Bearer"


async def test_공유_토큰으로는_지금_누구인지와_로그아웃을_열지_못한다(
    client: AsyncClient,
) -> None:
    assert (await client.get("/auth/me", headers=SHARED)).status_code == 401
    assert (await client.post("/auth/logout", headers=SHARED)).status_code == 401


async def test_서명_키는_10초가_지난_뒤_다시_읽고_바뀐_키로_만든_옛_증표는_통하지_않는다(
    client: AsyncClient,
    accounts: AccountStore,
    clock: MovingClock,
    database: ScopedDatabase,
) -> None:
    await _seed(accounts, "kim.min")
    cookie = _as_cookie(await _login(client))
    await _execute(database, "UPDATE operator_signing_key SET key = :key", key=b"\x07" * 32)

    clock.advance(seconds=9)
    assert (await client.get("/auth/me", headers=cookie)).status_code == 200
    clock.advance(seconds=1)
    assert (await client.get("/auth/me", headers=cookie)).status_code == 401


async def test_공유_토큰이_맞으면_로그인_쿠키가_함께_와도_서명_키를_읽지_않는다(
    clock: MovingClock, stderr: io.StringIO
) -> None:
    store = UnusedAccounts()
    store.fail_reads = 1000  # 키를 읽으려 하면 터진다
    accounts: AccountStore = store
    app = _app(accounts, clock, stderr)
    cookie = {"Cookie": f"{ACCESS_COOKIE}=not.a.token"}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="https://admin.test") as client:
        response = await client.get("/plugins", headers={**SHARED, **cookie})

    assert response.status_code == 200
    assert store.reads == 0


async def _let_tasks_run() -> None:
    """만든 작업이 닿을 수 있는 데까지 가게 이벤트 루프를 몇 번 넘겨준다."""
    for _ in range(10):
        await asyncio.sleep(0)


async def test_서명_키가_만료됐을_때_동시에_온_요청은_읽기_하나를_함께_쓴다() -> None:
    clock = MovingClock()
    store = UnusedAccounts()
    store.key = b"\x01" * 32
    keys = SigningKeys(store, clock)
    assert await keys.current() == b"\x01" * 32
    assert store.reads == 1

    clock.advance(seconds=10)
    store.gate = asyncio.Event()
    first = asyncio.create_task(keys.current())
    await _let_tasks_run()
    # 첫 읽기가 값을 읽고 트랜잭션을 연 채인 동안 키가 바뀌고 둘째 요청이 온다
    store.key = b"\x02" * 32
    second = asyncio.create_task(keys.current())
    await _let_tasks_run()
    store.gate.set()

    # 읽기 둘이 겹치면 늦게 끝난 쪽이 옛 키를 캐시에 되돌릴 수 있다. 하나로 모이면 10초에 한 번이다
    assert store.reads == 2, f"읽기가 {store.reads - 1}번 났다. 하나여야 한다"
    assert await first == await second == b"\x01" * 32


async def test_서명_키를_읽다_실패하면_기다리던_요청이_다시_읽는다() -> None:
    clock = MovingClock()
    store = UnusedAccounts()
    store.key = b"\x01" * 32
    keys = SigningKeys(store, clock)
    await keys.current()

    clock.advance(seconds=10)
    store.gate = asyncio.Event()
    store.fail_reads = 1
    first = asyncio.create_task(keys.current())
    await _let_tasks_run()
    second = asyncio.create_task(keys.current())
    await _let_tasks_run()
    store.gate.set()

    with pytest.raises(RuntimeError, match="서명 키를 읽지 못했다"):
        await first
    assert await second == b"\x01" * 32


async def test_서명_키의_줄은_하나이고_로그인을_거듭해도_늘지_않는다(
    client: AsyncClient, accounts: AccountStore, database: ScopedDatabase
) -> None:
    await _seed(accounts, "kim.min")
    await _login(client)
    await _login(client)

    assert len(await _rows(database, "SELECT id FROM operator_signing_key")) == 1


# --- 로그아웃 ------------------------------------------------------------------------------------


async def test_로그아웃은_쿠키_둘을_지우고_로그인_한_건을_끝내며_기록을_남긴다(
    client: AsyncClient, accounts: AccountStore, clock: MovingClock, database: ScopedDatabase
) -> None:
    await _seed(accounts, "kim.min")
    cookie = _as_cookie(await _login(client))
    clock.advance(minutes=1)

    response = await client.post("/auth/logout", headers=cookie)

    assert response.status_code == 204
    lines = response.headers.get_list("set-cookie")
    # 두 쿠키를 한 번씩 지운다. 같은 쿠키를 두 번 지우는 응답은 실패다
    assert sorted(line.partition("=")[0] for line in lines) == sorted(
        [ACCESS_COOKIE, REFRESH_COOKIE]
    )
    for line in lines:
        name = line.partition("=")[0]
        assert line.startswith(f"{name}=;"), line
        assert "Max-Age=0" in line, line
        assert "Secure" in line, line
        assert "Path=/" in line, line
    assert await _rows(database, "SELECT ended_at FROM operator_logins") == [(clock.at,)]
    assert (await _records(database))[-1] == ("logged_out", "kim.min", None)


async def test_로그아웃_뒤에도_이미_받은_짧은_JWT_는_수명이_끝날_때까지_통한다(
    client: AsyncClient, accounts: AccountStore
) -> None:
    await _seed(accounts, "kim.min")
    cookie = _as_cookie(await _login(client))
    await client.post("/auth/logout", headers=cookie)

    assert (await client.get("/auth/me", headers=cookie)).status_code == 200


# --- 첫 계정 확인 --------------------------------------------------------------------------------


async def test_첫_계정_확인은_로그인_없이_열리고_계정이_하나도_없을_때만_참이다(
    client: AsyncClient, accounts: AccountStore
) -> None:
    before = await client.get("/auth/setup")
    await _seed(accounts, "kim.min")
    after = await client.get("/auth/setup")

    assert (before.status_code, before.json()) == (200, {"needs_first_account": True})
    assert (after.status_code, after.json()) == (200, {"needs_first_account": False})


# --- 자격 ----------------------------------------------------------------------------------------


async def test_운영자_경로는_쿠키로도_공유_토큰으로도_열리고_쿠키가_없으면_401이다(
    client: AsyncClient, accounts: AccountStore
) -> None:
    await _seed(accounts, "kim.min")
    cookie = _as_cookie(await _login(client))

    assert (await client.get("/plugins", headers=cookie)).status_code == 200
    assert (await client.get("/plugins", headers=SHARED)).status_code == 200
    assert (await client.get("/plugins")).status_code == 401
    assert (
        await client.get("/plugins", headers={"Cookie": f"{ACCESS_COOKIE}=x"})
    ).status_code == 401


async def test_운영자_채널은_쿠키와_채널_토큰으로_열리고_관리_토큰으로는_열리지_않는다(
    client: AsyncClient, accounts: AccountStore
) -> None:
    await _seed(accounts, "kim.min")
    cookie = _as_cookie(await _login(client))
    channel = {"Authorization": f"Bearer {CHANNEL_TOKEN}"}

    with_cookie = await client.post(CHANNEL_PREFIX, json={}, headers=cookie)
    with_channel = await client.post(CHANNEL_PREFIX, json={}, headers=channel)
    with_admin = await client.post(CHANNEL_PREFIX, json={}, headers=SHARED)

    assert (with_cookie.status_code, with_channel.status_code) == (422, 422)
    assert with_admin.status_code == 401


async def test_최종_사용자_경로는_쿠키로_열리지_않는다(
    client: AsyncClient, accounts: AccountStore
) -> None:
    await _seed(accounts, "kim.min")
    cookie = _as_cookie(await _login(client))

    response = await client.post(f"{END_USER_PREFIX}/runs", json={}, headers=cookie)

    assert response.status_code == 401


async def test_로그인과_첫_계정_확인과_헬스체크만_인증_없이_답한다(
    client: AsyncClient,
) -> None:
    assert (await client.get("/health")).status_code == 200
    assert (await client.get("/auth/setup")).status_code == 200
    assert (
        await client.post("/auth/login", json={"name": "a", "password": "b"})
    ).status_code == 401
    for method, path in (("GET", "/auth/me"), ("POST", "/auth/logout"), ("GET", "/plugins")):
        response = await client.request(method, path)
        assert response.status_code == 401, path


# --- 요청 출처 검사 ------------------------------------------------------------------------------


@pytest.mark.parametrize(("headers", "passes"), ORIGIN_CASES)
async def test_요청_출처_검사의_사례_표가_로그인에도_같다(
    client: AsyncClient,
    accounts: AccountStore,
    database: ScopedDatabase,
    headers: dict[str, str],
    *,
    passes: bool,
) -> None:
    """관리 API와 운영자 채널의 표(`tests/test_server.py`)를 그대로 쓴다. 지나는 요청은 로그인까지
    가고, 막힌 요청은 맞는 비밀번호를 들고도 403 이며 계정도 기록도 건드리지 않는다."""
    await _seed(accounts, "kim.min")

    response = await _login(client, **headers)

    if passes:
        assert response.status_code == 204
        return
    assert response.status_code == 403
    assert response.json()["code"] == "forbidden"
    assert "set-cookie" not in response.headers
    assert await _records(database) == []
    assert await _rows(database, "SELECT failures FROM operator_accounts") == [(0,)]


async def test_다른_출처의_로그아웃과_첫_계정_확인도_403이다(client: AsyncClient) -> None:
    foreign = {"Origin": "https://evil.example"}

    assert (await client.post("/auth/logout", headers=foreign)).status_code == 403
    assert (await client.get("/auth/me", headers=foreign)).status_code == 403
    assert (await client.get("/auth/setup", headers=foreign)).status_code == 403


# --- 접속 주소 -----------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("forwarded", "expected"),
    [
        (["203.0.113.7"], "203.0.113.7"),
        (["2001:db8::1"], "2001:db8::1"),
        (["203.0.113.7", "198.51.100.1"], None),
        (["203.0.113.7, 198.51.100.1"], None),
        (["not-an-ip"], None),
        ([], None),
    ],
    ids=["하나", "IPv6", "머리 둘", "쉼표 둘", "IP 아님", "머리 없음"],
)
async def test_접속_주소는_앞_프록시가_덮어쓴_하나일_때만_기록에_남는다(
    client: AsyncClient,
    accounts: AccountStore,
    database: ScopedDatabase,
    forwarded: list[str],
    expected: str | None,
) -> None:
    await _seed(accounts, "kim.min")

    await client.post(
        "/auth/login",
        json={"name": "kim.min", "password": PASSWORD},
        headers=[("X-Forwarded-For", value) for value in forwarded],
    )

    assert await _records(database) == [("login_succeeded", "kim.min", expected)]


# --- 비밀이 새지 않는다 --------------------------------------------------------------------------


async def test_비밀번호와_갱신용_번호와_해시가_기록과_서버_기록과_응답에_실리지_않는다(
    client: AsyncClient,
    accounts: AccountStore,
    database: ScopedDatabase,
    stderr: io.StringIO,
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.DEBUG)
    await _seed(accounts, "kim.min")
    failed = await _login(client, password=CANARY)
    ok = await _login(client)
    refresh = _cookies(ok)[REFRESH_COOKIE]
    await client.post("/auth/logout", headers=_as_cookie(ok))
    await _login(client, name="no.such", password=CANARY)

    (stored_hash,) = await _rows(database, "SELECT password_hash FROM operator_accounts")
    dump = repr(await _rows(database, "SELECT * FROM operator_login_records"))
    surfaces = [dump, stderr.getvalue(), caplog.text, failed.text, ok.text]
    for surface in surfaces:
        assert CANARY not in surface
        assert PASSWORD not in surface
        assert refresh not in surface
        assert str(stored_hash[0]) not in surface


async def test_로그인하지_않은_요청은_어느_경로에서도_고정_문구의_401_봉투뿐이다(
    accounts: AccountStore, clock: MovingClock, stderr: io.StringIO
) -> None:
    """계정이 있어도 로그인 없이 닿는 응답에는 계정이나 사유가 새지 않는다. 앱이 아는 모든
    오퍼레이션을 훑어 공개 경로를 뺀 나머지가 같은 봉투와 같은 문구인지 본다."""
    await _seed(accounts, "kim.min")
    app = _app(accounts, clock, stderr)
    operations = [
        (method.upper(), re.sub(r"\{[^}]+\}", "x", str(path)))
        for path, item in app.openapi()["paths"].items()
        for method in item
        if path not in PUBLIC_PATHS
    ]
    assert len(operations) > 10, "훑은 오퍼레이션이 비면 이 전수 검사는 401 을 한 번도 재지 않는다"
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="https://admin.test") as anonymous:
        for method, path in operations:
            response = await anonymous.request(method, path)
            assert response.status_code == 401, (method, path)
            body = response.json()
            assert set(body) == {"code", "message", "violations", "request_id"}, (method, path)
            assert body["code"] == "unauthorized", (method, path)
            assert body["message"] == UNAUTHORIZED_MESSAGE, (method, path)
            assert body["violations"] == [], (method, path)
            assert "set-cookie" not in response.headers, (method, path)


# --- 수명 ----------------------------------------------------------------------------------------


async def test_서비스의_수명은_뜰_때_서명_키의_줄을_만들고_닫은_뒤에도_다시_쓸_수_있다(
    accounts: AccountStore, clock: MovingClock, database: ScopedDatabase
) -> None:
    service = LoginService(accounts=accounts, clock=clock, durations=LoginDurations())
    await _seed(accounts, "kim.min")
    assert await _rows(database, "SELECT id FROM operator_signing_key") == []

    async with service.lifespan():
        assert len(await _rows(database, "SELECT id FROM operator_signing_key")) == 1
        assert await service.log_in("kim.min", PASSWORD, address=None) is not None

    assert await service.log_in("kim.min", PASSWORD, address=None) is not None
    await service.close()
