"""`agent-os operator system-admin` 명령(`agent_os.main.main`)을 실제 테스트 데이터베이스에 붙여
본다.

운영자가 보는 것을 본다. 종료 코드, 표준 출력과 표준 오류의 글, 데이터베이스에 남은 줄이다.
비밀번호는 파이프로 넣고(표준 입력이 터미널이 아니다), 어느 출력에도 로그인 기록에도 비밀번호가
실리지 않는지 본다. 터미널 갈래는 표준 입력이 터미널인 척하는 입력과 가짜 `getpass` 로 본다.

비동기 시험에서는 `main` 을 스레드로 부른다(`main` 이 스스로 이벤트 루프를 연다). 스레드에서는
SIGINT 처리기를 걸 수 없어, 처리기를 거는 `run_interruptibly` 만 `asyncio.run` 으로 바꾼다.
"""

from __future__ import annotations

import asyncio
import io
import sys
import warnings
from collections.abc import AsyncGenerator, Callable, Coroutine, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from getpass import GetPassWarning
from uuid import UUID

import pytest
from argon2 import PasswordHasher
from sqlalchemy import text
from tests.postgres_support import NO_URL, plain
from tools.database_for_tests import ScopedDatabase

from agent_os import main as main_module
from agent_os.adapters.postgres.accounts import PostgresAccounts
from agent_os.adapters.postgres.database import DatabaseUrl, PostgresDatabase
from agent_os.channel.cli.operator import (
    CANNOT_HIDE_TEXT,
    CONFIRM_PROMPT,
    NO_PASSWORD_TEXT,
    NOT_UTF8_TEXT,
    PASSWORD_MISMATCH_TEXT,
    PASSWORD_PROMPT,
    Refused,
    check_name,
    password_hash_of,
    system_admin_command,
)
from agent_os.http.accounts import (
    ACCOUNT_NAME_RULE_TEXT,
    AccountRow,
    AccountStore,
    AccountWork,
    LinkRow,
    NewAccount,
    RecordKind,
    RefreshRow,
    Taken,
    Tier,
)
from agent_os.http.passwords import PASSWORD_RULE_TEXT
from agent_os.main import DATABASE_URL_ENV, main
from agent_os.sdk import RunId

PASSWORD = "Pw-canary-9!"
OTHER_PASSWORD = "Another-canary-7?"
NOW = datetime(2026, 11, 26, 9, 0, tzinfo=UTC)
COMMAND = ["operator", "system-admin"]


class _Stdin(io.StringIO):
    """표준 입력의 대역. `tty` 가 참이면 터미널인 척한다."""

    def __init__(self, text: str, *, tty: bool = False) -> None:
        super().__init__(text)
        self._tty = tty

    def isatty(self) -> bool:
        return self._tty


def _run_plainly[T](work: Callable[[], Coroutine[object, object, T]]) -> T:
    return asyncio.run(work())


def _stderr_notice(message: str) -> None:
    sys.stderr.write(f"{message}\n")


def _prepare(
    monkeypatch: pytest.MonkeyPatch,
    database: ScopedDatabase | None,
    stdin: str | _Stdin,
    *,
    give_up_quickly: bool = False,
) -> None:
    """환경 변수와 표준 입력을 정하고, 스레드에서도 도는 실행기와 짧은 기다림의 어댑터를 끼운다."""
    if database is None:
        monkeypatch.delenv(DATABASE_URL_ENV, raising=False)
    else:
        monkeypatch.setenv(DATABASE_URL_ENV, database.address.text_for(database.name))
    monkeypatch.setattr(sys, "stdin", _Stdin(stdin) if isinstance(stdin, str) else stdin)
    monkeypatch.setattr(main_module, "run_interruptibly", _run_plainly)
    retry_seconds, attempt_seconds = (0.6, 0.4) if give_up_quickly else (8.0, 8.0)

    def build(url: DatabaseUrl) -> PostgresDatabase:
        return PostgresDatabase(
            url,
            notice=_stderr_notice,
            retry_seconds=retry_seconds,
            retry_interval=0.1,
            attempt_seconds=attempt_seconds,
        )

    monkeypatch.setattr(main_module, "_build_database", build)


async def _run(name: str) -> int:
    return await asyncio.to_thread(main, [*COMMAND, name])


async def _accounts(database: ScopedDatabase) -> Sequence[tuple[str, str, str | None, int]]:
    async with plain(database) as connection:
        result = await connection.execute(
            text("SELECT name, tier, password_hash, failures FROM operator_accounts ORDER BY name")
        )
        return [(row[0], row[1], row[2], row[3]) for row in result.all()]


async def _records(database: ScopedDatabase) -> Sequence[tuple[str, str | None]]:
    async with plain(database) as connection:
        result = await connection.execute(
            text("SELECT kind, account FROM operator_login_records ORDER BY seq")
        )
        return [(row[0], row[1]) for row in result.all()]


async def _insert_account(
    database: ScopedDatabase, name: str, tier: str, *, password_hash: str | None = "stored"
) -> None:
    async with plain(database, autocommit=True) as connection:
        await connection.execute(
            text(
                "INSERT INTO operator_accounts (name, tier, password_hash, failures, created_at) "
                "VALUES (:name, :tier, :hash, 0, :at)"
            ),
            {"name": name, "tier": tier, "hash": password_hash, "at": NOW},
        )


def _verifies(stored: str | None, password: str) -> bool:
    assert stored is not None
    return PasswordHasher().verify(stored, password)


def _assert_no_secret(capsys: pytest.CaptureFixture[str], *secrets: str) -> tuple[str, str]:
    captured = capsys.readouterr()
    for secret in secrets:
        assert secret not in captured.out
        assert secret not in captured.err
    return captured.out, captured.err


# --- 만들기 --------------------------------------------------------------------------------------


async def test_시스템_관리자가_없으면_만들고_0으로_끝난다(
    database: ScopedDatabase, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _prepare(monkeypatch, database, f"{PASSWORD}\n")
    assert await _run("root-one") == 0
    out, err = _assert_no_secret(capsys, PASSWORD)
    assert (out, err) == ("시스템 관리자 root-one 계정을 만들었습니다.\n", "")
    rows = await _accounts(database)
    assert [(name, tier, failures) for name, tier, _hash, failures in rows] == [
        ("root-one", "system_admin", 0)
    ]
    assert _verifies(rows[0][2], PASSWORD)
    assert await _records(database) == [("system_admin_set", "root-one")]


async def test_표준_입력이_cp949로_열려_있어도_한글_비밀번호의_해시는_UTF8_글자의_것이다(
    database: ScopedDatabase, monkeypatch: pytest.MonkeyPatch
) -> None:
    korean = "한글Pw-9!x"
    _prepare(monkeypatch, database, "")
    monkeypatch.setattr(
        sys, "stdin", io.TextIOWrapper(io.BytesIO(f"{korean}\n".encode()), encoding="cp949")
    )
    assert await _run("root-one") == 0
    assert _verifies((await _accounts(database))[0][2], korean)


async def test_들어온_이름의_영문_대문자는_소문자로_바꿔_만든다(
    database: ScopedDatabase, monkeypatch: pytest.MonkeyPatch
) -> None:
    _prepare(monkeypatch, database, f"{PASSWORD}\n")
    assert await _run("Root-One") == 0
    assert [row[0] for row in await _accounts(database)] == ["root-one"]


async def test_윈도_파이프의_줄_끝_캐리지리턴과_개행을_뗀다(
    database: ScopedDatabase, monkeypatch: pytest.MonkeyPatch
) -> None:
    _prepare(monkeypatch, database, f"{PASSWORD}\r\n둘째 줄은 읽지 않는다\n")
    assert await _run("root-one") == 0
    assert _verifies((await _accounts(database))[0][2], PASSWORD)


async def test_줄_끝의_개행_말고는_비밀번호의_글자를_바꾸지_않는다(
    database: ScopedDatabase, monkeypatch: pytest.MonkeyPatch
) -> None:
    padded = f" {PASSWORD} "
    _prepare(monkeypatch, database, f"{padded}\n")
    assert await _run("root-one") == 0
    assert _verifies((await _accounts(database))[0][2], padded)


async def test_한글_비밀번호도_정규화한_글로_해시된다(
    database: ScopedDatabase, monkeypatch: pytest.MonkeyPatch
) -> None:
    korean = "한글Pw1비밀번호"
    _prepare(monkeypatch, database, f"{korean}\n")
    assert await _run("root-one") == 0
    assert _verifies((await _accounts(database))[0][2], korean)


# --- 다시 정하기 ---------------------------------------------------------------------------------


async def test_같은_이름의_시스템_관리자면_비밀번호를_다시_정하고_잠금과_로그인을_지운다(
    database: ScopedDatabase, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _prepare(monkeypatch, database, f"{PASSWORD}\n")
    assert await _run("root-one") == 0
    capsys.readouterr()
    async with plain(database, autocommit=True) as connection:
        await connection.execute(
            text(
                "UPDATE operator_accounts SET failures = 7, locked_until = :until "
                "WHERE name = 'root-one'"
            ),
            {"until": NOW + timedelta(days=1)},
        )
        login = text(
            "INSERT INTO operator_logins (id, account, logged_in_at, refreshed_at) "
            "VALUES (gen_random_uuid(), 'root-one', :at, :at)"
        )
        await connection.execute(login, {"at": NOW})
        await connection.execute(login, {"at": NOW})

    _prepare(monkeypatch, database, f"{OTHER_PASSWORD}\n")
    assert await _run("root-one") == 0

    out, err = _assert_no_secret(capsys, PASSWORD, OTHER_PASSWORD)
    assert err == ""
    assert "비밀번호를 다시 정했습니다" in out
    rows = await _accounts(database)
    assert [(name, tier, failures) for name, tier, _hash, failures in rows] == [
        ("root-one", "system_admin", 0)
    ]
    assert _verifies(rows[0][2], OTHER_PASSWORD)
    async with plain(database) as connection:
        result = await connection.execute(
            text("SELECT locked_until FROM operator_accounts WHERE name = 'root-one'")
        )
        assert result.scalar_one() is None
        result = await connection.execute(
            text("SELECT count(*) FROM operator_logins WHERE ended_at IS NULL")
        )
        assert result.scalar_one() == 0
    assert await _records(database) == [
        ("system_admin_set", "root-one"),
        ("system_admin_set", "root-one"),
    ]


# --- 멈추는 갈래: 아무것도 바꾸지 않는다 ---------------------------------------------------------


async def test_다른_이름의_시스템_관리자가_있으면_그_이름을_적고_1로_멈춘다(
    database: ScopedDatabase, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _prepare(monkeypatch, database, f"{PASSWORD}\n")
    assert await _run("root-one") == 0
    capsys.readouterr()
    before = await _accounts(database)

    _prepare(monkeypatch, database, f"{OTHER_PASSWORD}\n")
    assert await _run("root-two") == 1

    out, err = _assert_no_secret(capsys, PASSWORD, OTHER_PASSWORD)
    assert out == ""
    assert "root-one" in err
    assert await _accounts(database) == before
    assert await _records(database) == [("system_admin_set", "root-one")]


async def test_그_이름의_관리자_단계_계정이_있으면_1로_멈춘다(
    database: ScopedDatabase, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    await _insert_account(database, "kim.min", "admin")
    before = await _accounts(database)
    _prepare(monkeypatch, database, f"{PASSWORD}\n")
    assert await _run("kim.min") == 1

    out, err = _assert_no_secret(capsys, PASSWORD)
    assert out == ""
    assert "관리자 단계" in err
    assert await _accounts(database) == before
    assert await _records(database) == []


async def test_이름_규칙을_어기면_데이터베이스에_닿기_전에_1로_멈춘다(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _prepare(monkeypatch, None, f"{PASSWORD}\n")
    assert await _run("ab") == 1
    out, err = _assert_no_secret(capsys, PASSWORD)
    assert out == ""
    assert ACCOUNT_NAME_RULE_TEXT in err
    # 주소가 없어도 이름 문구가 먼저다: 주소 진단이 아니라 이름 문구다
    assert NO_URL not in err


@pytest.mark.parametrize(
    "stdin",
    ["abcdefgh1!\n", "Abcdefgh!\n", "Abcdefgh1\n", "Ab1!\n", "\n", f"{'A1!' + 'a' * 126}\n"],
    ids=["대문자_없음", "숫자_없음", "특수문자_없음", "짧음", "빈_줄", "백스물아홉"],
)
async def test_비밀번호가_규칙을_어기면_규칙을_적고_1로_멈춘다(
    stdin: str,
    database: ScopedDatabase,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _prepare(monkeypatch, database, stdin)
    assert await _run("root-one") == 1
    out, err = capsys.readouterr()
    assert out == ""
    assert PASSWORD_RULE_TEXT in err
    assert stdin.strip() == "" or stdin.strip() not in err
    assert await _accounts(database) == []


async def test_표준_입력에_줄이_없으면_1로_멈춘다(
    database: ScopedDatabase, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _prepare(monkeypatch, database, "")
    assert await _run("root-one") == 1
    out, err = capsys.readouterr()
    assert (out, err) == ("", f"{NO_PASSWORD_TEXT}\n")
    assert await _accounts(database) == []


def test_표준_입력이_UTF8이_아니면_역추적_없이_받아들이지_않는다() -> None:
    stdin = io.TextIOWrapper(io.BytesIO(b"\xff\xfeAbcdefg1!\n"), encoding="utf-8")
    assert password_hash_of(stdin, input) == Refused(NOT_UTF8_TEXT)


# --- 데이터베이스 -------------------------------------------------------------------------------


async def test_주소가_없으면_serve와_같은_글로_1로_멈춘다(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _prepare(monkeypatch, None, f"{PASSWORD}\n")
    assert await _run("root-one") == 1
    out, err = _assert_no_secret(capsys, PASSWORD)
    assert (out, err) == ("", NO_URL)


async def test_표가_아직_안_올라간_데이터베이스에는_migrate를_안내하고_1로_멈춘다(
    empty_database: ScopedDatabase,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _prepare(monkeypatch, empty_database, f"{PASSWORD}\n")
    assert await _run("root-one") == 1
    out, err = _assert_no_secret(capsys, PASSWORD)
    assert out == ""
    assert "agent-os migrate" in err


async def test_닿지_못하면_까닭만_싣고_1로_멈춘다(
    database: ScopedDatabase, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    unreachable = database.address.text_for("no_such_database_00000000")
    _prepare(monkeypatch, database, f"{PASSWORD}\n", give_up_quickly=True)
    monkeypatch.setenv(DATABASE_URL_ENV, unreachable)
    assert await _run("root-one") == 1
    out, err = _assert_no_secret(capsys, PASSWORD, "no_such_database_00000000:x")
    assert out == ""
    assert "데이터베이스(" in err


# --- 터미널 갈래 ---------------------------------------------------------------------------------


async def test_터미널이면_보이지_않게_두_번_받고_같으면_만든다(
    database: ScopedDatabase, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    prompts: list[str] = []
    answers = iter([PASSWORD, PASSWORD])

    def fake_getpass(prompt: str = "") -> str:
        prompts.append(prompt)
        return next(answers)

    monkeypatch.setattr(main_module.getpass, "getpass", fake_getpass)
    _prepare(monkeypatch, database, _Stdin("읽지 않는다\n", tty=True))
    assert await _run("root-one") == 0
    _assert_no_secret(capsys, PASSWORD)
    assert prompts == [PASSWORD_PROMPT, CONFIRM_PROMPT]
    assert _verifies((await _accounts(database))[0][2], PASSWORD)


async def test_터미널에서_두_번이_다르면_1로_멈춘다(
    database: ScopedDatabase, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    answers = iter([PASSWORD, OTHER_PASSWORD])
    monkeypatch.setattr(main_module.getpass, "getpass", lambda prompt="": next(answers))
    _prepare(monkeypatch, database, _Stdin("", tty=True))
    assert await _run("root-one") == 1
    out, err = _assert_no_secret(capsys, PASSWORD, OTHER_PASSWORD)
    assert (out, err) == ("", f"{PASSWORD_MISMATCH_TEXT}\n")
    assert await _accounts(database) == []


# --- 함수 단위: 시계, 입력
# --------------------------------------------------------------------------


class _FixedClock:
    def now(self) -> datetime:
        return NOW

    def new_run_id(self) -> RunId:
        raise AssertionError("쓰지 않는다")


async def test_적는_시각은_주입된_시계의_값이다(database: ScopedDatabase) -> None:
    url = main_module.parse_database_url(database.address.text_for(database.name))
    assert url is not None
    adapter = PostgresDatabase(url, notice=lambda _message: None)
    accounts: PostgresAccounts = adapter.accounts()
    out, err = io.StringIO(), io.StringIO()
    try:
        code = await system_admin_command(
            "root-one",
            "$argon2id$stored",
            accounts=accounts,
            clock=_FixedClock(),
            stdout=out,
            stderr=err,
        )
    finally:
        await adapter.close()
    assert code == 0
    async with plain(database) as connection:
        created = (
            await connection.execute(text("SELECT created_at FROM operator_accounts"))
        ).scalar_one()
        occurred = (
            await connection.execute(text("SELECT occurred_at FROM operator_login_records"))
        ).scalar_one()
    assert (created, occurred) == (NOW, NOW)


def test_이름_검사는_대문자를_바꾼_뒤_규칙에_댄다() -> None:
    assert check_name("Kim.Min") == "kim.min"
    refused = check_name("김민수")
    assert isinstance(refused, Refused)
    assert ACCOUNT_NAME_RULE_TEXT in refused.text


@dataclass(frozen=True)
class _Row:
    name: str
    tier: Tier = "system_admin"
    password_hash: str | None = "stored"
    disabled_at: datetime | None = None
    failures: int = 0
    locked_until: datetime | None = None
    created_at: datetime = NOW


_NOT_USED = "시스템 관리자 명령은 로그인의 메서드를 쓰지 않는다"


class _RacingWork:
    """처음 읽을 때는 시스템 관리자가 없고 넣기는 늘 `"taken"` 이다. 이긴 쪽이 있으면 다시 읽을 때
    보인다."""

    def __init__(self, winner: str | None, *, existing: AccountRow | None = None) -> None:
        self._winner = winner
        self._existing = existing
        self.reads = 0
        self.adds = 0
        self.written: list[str] = []

    async def lock_system_admin(self) -> AccountRow | None:
        self.reads += 1
        if self.reads == 1 or self._winner is None:
            return None
        return _Row(self._winner)

    async def lock(self, name: str) -> AccountRow | None:
        return self._existing

    async def add(self, account: NewAccount) -> AccountRow | Taken:
        self.adds += 1
        return "taken"

    async def reset_password(self, name: str, *, password_hash: str) -> None:
        self.written.append("reset_password")

    async def end_logins(self, name: str, *, at: datetime) -> None:
        self.written.append("end_logins")

    async def record(
        self,
        kind: RecordKind,
        *,
        at: datetime,
        account: str | None,
        address: str | None = None,
        actor: str | None = None,
    ) -> None:
        self.written.append("record")

    # 아래는 로그인이 쓰는 메서드다. 시스템 관리자 명령은 부르지 않으므로 불리면 터진다.
    async def any_account(self) -> bool:
        raise AssertionError(_NOT_USED)

    async def set_failures(
        self, name: str, *, failures: int, locked_until: datetime | None
    ) -> None:
        raise AssertionError(_NOT_USED)

    async def clear_failures(self, name: str) -> None:
        raise AssertionError(_NOT_USED)

    async def delete_ended_logins(
        self, name: str, *, idle_before: datetime, total_before: datetime
    ) -> None:
        raise AssertionError(_NOT_USED)

    async def open_login(self, login_id: UUID, name: str, *, at: datetime) -> None:
        raise AssertionError(_NOT_USED)

    async def add_refresh_token(self, token_hash: str, login_id: UUID, *, at: datetime) -> None:
        raise AssertionError(_NOT_USED)

    async def end_login(self, login_id: UUID, *, at: datetime) -> None:
        raise AssertionError(_NOT_USED)

    async def ensure_signing_key(self, key: bytes, *, at: datetime) -> None:
        raise AssertionError(_NOT_USED)

    async def read_signing_key(self) -> bytes | None:
        raise AssertionError(_NOT_USED)

    async def replace_signing_key(self, key: bytes, *, at: datetime) -> None:
        raise AssertionError(_NOT_USED)

    async def lock_refresh(self, token_hash: str) -> RefreshRow | None:
        raise AssertionError(_NOT_USED)

    async def read_account(self, name: str) -> AccountRow | None:
        raise AssertionError(_NOT_USED)

    async def use_refresh_token(self, token_hash: str, *, at: datetime) -> None:
        raise AssertionError(_NOT_USED)

    async def touch_login(self, login_id: UUID, *, at: datetime) -> None:
        raise AssertionError(_NOT_USED)

    async def list_accounts(self) -> Sequence[AccountRow]:
        raise AssertionError(_NOT_USED)

    async def set_disabled(self, name: str, *, at: datetime | None) -> None:
        raise AssertionError(_NOT_USED)

    async def end_other_logins(self, name: str, *, keep: UUID, at: datetime) -> None:
        raise AssertionError(_NOT_USED)

    async def add_link(
        self, token_hash: str, account: str, *, at: datetime, expires_at: datetime
    ) -> None:
        raise AssertionError(_NOT_USED)

    async def void_links(self, account: str, *, at: datetime) -> None:
        raise AssertionError(_NOT_USED)

    async def lock_link(self, token_hash: str) -> LinkRow | None:
        raise AssertionError(_NOT_USED)

    async def use_link(self, token_hash: str, *, at: datetime) -> None:
        raise AssertionError(_NOT_USED)


class _RacingStore:
    def __init__(self, work: _RacingWork) -> None:
        self._work = work

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[AccountWork]:
        yield self._work


async def test_넣기가_taken이면_다시_읽어_이긴_쪽이_다른_이름이면_멈춘다() -> None:
    work = _RacingWork(winner="other-root")
    store: AccountStore = _RacingStore(work)
    out, err = io.StringIO(), io.StringIO()
    code = await system_admin_command(
        "root-one", "$argon2id$stored", accounts=store, clock=_FixedClock(), stdout=out, stderr=err
    )
    assert code == 1
    assert "other-root" in err.getvalue()
    assert out.getvalue() == ""
    assert (work.reads, work.adds, work.written) == (2, 1, [])


async def test_두_조회_사이에_시스템_관리자가_생기면_다시_읽어_재설정한다() -> None:
    # 시스템 관리자 조회는 비었는데 이름 조회가 시스템 관리자 줄을 돌려준 경합. 관리자 단계로 읽으면
    # 안 된다
    work = _RacingWork(winner="root-one", existing=_Row("root-one"))
    store: AccountStore = _RacingStore(work)
    out, err = io.StringIO(), io.StringIO()
    code = await system_admin_command(
        "root-one", "$argon2id$stored", accounts=store, clock=_FixedClock(), stdout=out, stderr=err
    )
    assert code == 0
    assert "다시 정했습니다" in out.getvalue()
    assert err.getvalue() == ""
    assert (work.reads, work.adds) == (2, 0)
    assert work.written == ["reset_password", "end_logins", "record"]


async def test_두_번_다_막히면_세_번째를_시도하지_않고_예외로_끝난다() -> None:
    work = _RacingWork(winner=None)
    store: AccountStore = _RacingStore(work)
    with pytest.raises(RuntimeError):
        await system_admin_command(
            "root-one",
            "$argon2id$stored",
            accounts=store,
            clock=_FixedClock(),
            stdout=io.StringIO(),
            stderr=io.StringIO(),
        )
    assert (work.reads, work.adds) == (2, 2)


def test_터미널이_글자를_숨기지_못하면_입력을_받기_전에_멈춘다() -> None:
    asked: list[str] = []

    def ask(prompt: str) -> str:
        asked.append(prompt)
        # 터미널을 다루지 못할 때 getpass 의 대체 길이 내는 것과 같은 경고
        warnings.warn("Can not control echo on the terminal.", GetPassWarning, stacklevel=2)
        return PASSWORD

    refused = password_hash_of(_Stdin("", tty=True), ask)
    assert refused == Refused(CANNOT_HIDE_TEXT)
    assert asked == [PASSWORD_PROMPT]


def test_비밀번호_입력은_터미널이_아니면_첫_줄만_읽는다() -> None:
    def never(_prompt: str) -> str:
        raise AssertionError("터미널이 아니면 묻지 않는다")

    hashed = password_hash_of(_Stdin(f"{PASSWORD}\n둘째\n"), never)
    assert isinstance(hashed, str)
    assert hashed.startswith("$argon2id$")
    assert PASSWORD not in hashed
