"""`agent-os operator rotate-key` 명령(`agent_os.main.main`)을 실제 테스트 데이터베이스에 붙여 본다.

운영자가 보는 것을 본다. 종료 코드, 표준 출력과 표준 오류의 글, 데이터베이스에 남은 서명 키와
기록이다. 이 명령은 비밀번호를 받지 않으므로 표준 입력을 읽지 않는다. 도는 `serve` 가 새 키를
쓰는지는 `tests/test_login_http.py` 가 앱과 함께 본다.

비동기 시험에서는 `main` 을 스레드로 부른다(`main` 이 스스로 이벤트 루프를 연다). 스레드에서는
SIGINT 처리기를 걸 수 없어, 처리기를 거는 `run_interruptibly` 만 `asyncio.run` 으로 바꾼다.
"""

from __future__ import annotations

import asyncio
import io
import sys
from collections.abc import Callable, Coroutine, Sequence
from datetime import UTC, datetime

import pytest
from sqlalchemy import text
from tests.postgres_support import NO_URL, plain
from tools.database_for_tests import ScopedDatabase

from agent_os import main as main_module
from agent_os.adapters.postgres.database import DatabaseUrl, PostgresDatabase
from agent_os.channel.cli.operator import ROTATED_TEXT, rotate_key_command
from agent_os.main import DATABASE_URL_ENV, main
from agent_os.sdk import RunId

NOW = datetime(2026, 11, 26, 9, 0, tzinfo=UTC)
COMMAND = ["operator", "rotate-key"]
OLD_KEY = b"\x01" * 32


def _run_plainly[T](work: Callable[[], Coroutine[object, object, T]]) -> T:
    return asyncio.run(work())


def _stderr_notice(message: str) -> None:
    sys.stderr.write(f"{message}\n")


def _prepare(
    monkeypatch: pytest.MonkeyPatch,
    database: ScopedDatabase | None,
    *,
    give_up_quickly: bool = False,
) -> None:
    """환경 변수를 정하고, 스레드에서도 도는 실행기와 짧은 기다림의 어댑터를 끼운다."""
    if database is None:
        monkeypatch.delenv(DATABASE_URL_ENV, raising=False)
    else:
        monkeypatch.setenv(DATABASE_URL_ENV, database.address.text_for(database.name))
    # 이 명령은 표준 입력을 읽지 않는다. 읽으면 이 빈 입력이 막는다
    monkeypatch.setattr(sys, "stdin", io.StringIO(""))
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


async def _run() -> int:
    return await asyncio.to_thread(main, COMMAND)


async def _keys(database: ScopedDatabase) -> Sequence[tuple[bytes, datetime]]:
    async with plain(database) as connection:
        result = await connection.execute(text("SELECT key, created_at FROM operator_signing_key"))
        return [(bytes(row[0]), row[1]) for row in result.all()]


async def _put_key(database: ScopedDatabase, key: bytes) -> None:
    async with plain(database, autocommit=True) as connection:
        await connection.execute(
            text("INSERT INTO operator_signing_key (id, key, created_at) VALUES (1, :key, :at)"),
            {"key": key, "at": NOW},
        )


async def _records(database: ScopedDatabase) -> Sequence[tuple[str, str | None, str | None]]:
    async with plain(database) as connection:
        result = await connection.execute(
            text("SELECT kind, account, address FROM operator_login_records ORDER BY seq")
        )
        return [(row[0], row[1], row[2]) for row in result.all()]


# --- 바꾸기 --------------------------------------------------------------------------------------


async def test_서명_키를_새_난수로_바꾸고_문구를_찍고_0으로_끝난다(
    database: ScopedDatabase, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    await _put_key(database, OLD_KEY)
    _prepare(monkeypatch, database)

    assert await _run() == 0

    captured = capsys.readouterr()
    assert (captured.out, captured.err) == (f"{ROTATED_TEXT}\n", "")
    assert "도는 `serve`는 10초 안에 새 키를 씁니다" in ROTATED_TEXT
    rows = await _keys(database)
    assert len(rows) == 1
    key, _created = rows[0]
    assert len(key) == 32
    assert key != OLD_KEY
    assert await _records(database) == [("signing_key_rotated", None, None)]


async def test_옛_키는_남기지_않고_줄은_하나로_남는다(
    database: ScopedDatabase, monkeypatch: pytest.MonkeyPatch
) -> None:
    await _put_key(database, OLD_KEY)
    _prepare(monkeypatch, database)

    assert await _run() == 0
    assert await _run() == 0

    rows = await _keys(database)
    assert len(rows) == 1
    assert rows[0][0] != OLD_KEY
    assert [kind for kind, _account, _address in await _records(database)] == [
        "signing_key_rotated",
        "signing_key_rotated",
    ]


async def test_줄이_아직_없으면_새로_만든다(
    database: ScopedDatabase, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`serve` 가 한 번도 뜨지 않은 데이터베이스에서 쳐도 키가 하나 생긴다."""
    _prepare(monkeypatch, database)

    assert await _run() == 0

    assert len(await _keys(database)) == 1


async def test_키_값은_출력과_기록에_실리지_않는다(
    database: ScopedDatabase, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _prepare(monkeypatch, database)

    assert await _run() == 0

    ((key, _created),) = await _keys(database)
    captured = capsys.readouterr()
    async with plain(database) as connection:
        result = await connection.execute(text("SELECT * FROM operator_login_records"))
        dump = repr(result.all())
    for surface in (captured.out, captured.err, dump):
        assert key.hex() not in surface
        assert repr(key) not in surface


# --- 데이터베이스 --------------------------------------------------------------------------------


async def test_주소가_없으면_serve와_같은_글로_1로_멈춘다(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _prepare(monkeypatch, None)

    assert await _run() == 1

    captured = capsys.readouterr()
    assert (captured.out, captured.err) == ("", NO_URL)


async def test_표가_아직_안_올라간_데이터베이스에는_migrate를_안내하고_1로_멈춘다(
    empty_database: ScopedDatabase,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _prepare(monkeypatch, empty_database)

    assert await _run() == 1

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "agent-os migrate" in captured.err


async def test_닿지_못하면_까닭만_싣고_1로_멈춘다(
    database: ScopedDatabase, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    _prepare(monkeypatch, database, give_up_quickly=True)
    monkeypatch.setenv(DATABASE_URL_ENV, database.address.text_for("no_such_database_00000000"))

    assert await _run() == 1

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "데이터베이스(" in captured.err
    assert "no_such_database_00000000:x" not in captured.err


# --- 함수 단위: 시계 -----------------------------------------------------------------------------


class _FixedClock:
    def now(self) -> datetime:
        return NOW

    def new_run_id(self) -> RunId:
        raise AssertionError("쓰지 않는다")


async def test_적는_시각은_주입된_시계의_값이다(database: ScopedDatabase) -> None:
    url = main_module.parse_database_url(database.address.text_for(database.name))
    assert url is not None
    adapter = PostgresDatabase(url, notice=lambda _message: None)
    out = io.StringIO()
    try:
        code = await rotate_key_command(
            accounts=adapter.accounts(), clock=_FixedClock(), stdout=out
        )
    finally:
        await adapter.close()

    assert code == 0
    assert out.getvalue() == f"{ROTATED_TEXT}\n"
    ((_, created),) = await _keys(database)
    async with plain(database) as connection:
        occurred = (
            await connection.execute(text("SELECT occurred_at FROM operator_login_records"))
        ).scalar_one()
    assert (created, occurred) == (NOW, NOW)
