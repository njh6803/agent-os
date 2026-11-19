"""`tools/database_for_tests.py`: 주소 고르기, 이름 짓기, 서버 확인, 데이터베이스 만들기와 지우기.

순수한 함수는 값으로, 데이터베이스에 닿는 함수는 테스트 컨테이너로 본다. 명령줄은 스레드에서 한
번씩 부르고(`main` 이 스스로 이벤트 루프를 연다), 실제 프로세스로도 한 번 부른다.
"""

from __future__ import annotations

import asyncio
import os
import re
import subprocess
import sys
import uuid
from collections.abc import Mapping
from pathlib import Path

import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool
from tests.postgres_support import closed_port, plain, tables
from tools.database_for_tests import (
    DEFAULT_URL,
    UP_COMMAND,
    URL_ENV,
    DatabaseAddress,
    DatabaseProblem,
    ScopedDatabase,
    build_template,
    create_database,
    drop_database,
    is_scoped_name,
    main,
    make_name,
    prefix_problem,
    reason_of,
    resolve_address,
    server_problem,
    unreachable_text,
)

SECRET = "leak_probe_pw"
ROOT = Path(__file__).resolve().parents[2]
NAME_SHAPE = re.compile(r"[a-z0-9_]+_(?:template|test|e2e)_[0-9a-f]{32}")


def _prefix() -> str:
    """겹치지 않는 시험용 접두. 21자 이하다."""
    return f"tdb{uuid.uuid4().hex[:8]}"


def _address(url: str) -> DatabaseAddress:
    return resolve_address({URL_ENV: url})


def _dead(address: DatabaseAddress) -> str:
    """아무것도 듣지 않는 포트를 가리키는 주소. 비밀번호는 알아볼 수 있는 값이다."""
    url = address.url.set(port=closed_port(), password=SECRET)
    return url.render_as_string(hide_password=False)


async def _count(address: DatabaseAddress, pattern: str) -> int:
    """이름이 패턴(LIKE)에 맞는 데이터베이스의 수. 관리 데이터베이스에서 센다."""
    admin = ScopedDatabase(address=address, name=address.url.database or "")
    async with plain(admin) as connection:
        result = await connection.execute(
            text("SELECT count(*) FROM pg_database WHERE datname LIKE :pattern"),
            {"pattern": pattern},
        )
        return int(result.scalar_one())


# --- 주소 고르기 --------------------------------------------------------------------------------


def test_환경_변수가_없으면_테스트_컨테이너의_기본_주소다() -> None:
    address = resolve_address({})
    assert address.from_env is False
    assert address.place == "127.0.0.1:25432/agent_os"
    assert address.url == make_url(DEFAULT_URL)


@pytest.mark.parametrize("value", ["", "   "])
def test_환경_변수가_공백뿐이면_없는_것으로_본다(value: str) -> None:
    address = resolve_address({URL_ENV: value})
    assert (address.from_env, address.place) == (False, "127.0.0.1:25432/agent_os")


def test_환경_변수가_있으면_그_값이고_글에_비밀번호가_없다() -> None:
    address = _address(f"postgresql://runner:{SECRET}@db.internal:6543/probe")
    assert address.from_env is True
    assert address.place == "db.internal:6543/probe"
    assert SECRET not in repr(address)
    assert SECRET not in str(address)
    scoped = ScopedDatabase(address=address, name="probe_test_x")
    assert scoped.place == "db.internal:6543/probe_test_x"
    assert SECRET not in repr(scoped)
    assert SECRET in scoped.text()
    assert SECRET in address.text_for("other")


def test_포트가_없는_주소는_5432로_읽는다() -> None:
    assert _address("postgresql://u:p@db.internal/probe").place == "db.internal:5432/probe"


@pytest.mark.parametrize(
    "value",
    [
        f"postgresql://u:{SECRET}@db.internal:5432/probe?options=-cx",
        f"postgresql://u:{SECRET}@db.internal:5432/probe?",
    ],
    ids=["질의_문자열", "빈_질의"],
)
def test_질의_문자열이_든_값은_받지_않고_글에_값을_싣지_않는다(value: str) -> None:
    with pytest.raises(DatabaseProblem) as caught:
        resolve_address({URL_ENV: value})
    assert str(caught.value) == (
        f"{URL_ENV} 에 질의 문자열(? 뒤)이 들어 있어 받지 않습니다. "
        "질의가 시험마다의 데이터베이스 이름을 덮을 수 있습니다."
    )
    assert SECRET not in str(caught.value)


@pytest.mark.parametrize(
    "value",
    [
        f"postgresql://u:{SECRET}@x@db.internal:5432/probe",
        f"postgresql+asyncpg://u:{SECRET}@db.internal:5432/probe",
        f"mysql://u:{SECRET}@db.internal:3306/probe",
        f"postgresql://u:{SECRET}@/probe",
        f"postgresql://u:{SECRET}@db.internal:5432",
        f"postgresql://u:{SECRET}@db.internal:notaport/probe",
    ],
    ids=[
        "골뱅이가_둘",
        "드라이버_붙음",
        "다른_종류",
        "호스트_없음",
        "데이터베이스_없음",
        "포트_글자",
    ],
)
def test_읽지_못하는_값은_받지_않고_글에_값을_싣지_않는다(value: str) -> None:
    with pytest.raises(DatabaseProblem) as caught:
        resolve_address({URL_ENV: value})
    assert str(caught.value) == (
        f"{URL_ENV} 을 읽지 못했습니다. 값에는 비밀번호가 들어 있어 여기 찍지 않습니다. "
        "비밀번호에 @ 가 들면 주소를 읽지 못하므로, 비밀번호는 영문자와 숫자만 씁니다."
    )
    assert SECRET not in str(caught.value)


# --- 이름 ---------------------------------------------------------------------------------------


@pytest.mark.parametrize("prefix", ["agent_os", "a", "x1_y2", "a" * 21])
def test_소문자_숫자_밑줄_스물한_자까지의_접두는_받는다(prefix: str) -> None:
    assert prefix_problem(prefix) is None


@pytest.mark.parametrize(
    ("prefix", "expected"),
    [
        ("", "데이터베이스 이름의 접두 '' 은 소문자, 숫자, 밑줄만 쓴다"),
        ("Agent", "데이터베이스 이름의 접두 'Agent' 은 소문자, 숫자, 밑줄만 쓴다"),
        ("a-b", "데이터베이스 이름의 접두 'a-b' 은 소문자, 숫자, 밑줄만 쓴다"),
        ('a"b', "데이터베이스 이름의 접두 'a\"b' 은 소문자, 숫자, 밑줄만 쓴다"),
        ("a" * 22, f"데이터베이스 이름의 접두 '{'a' * 22}' 은 21자까지다(이름이 63바이트까지라서)"),
    ],
)
def test_받지_않는_접두는_이유를_돌려준다(prefix: str, expected: str) -> None:
    assert prefix_problem(prefix) == expected


@pytest.mark.parametrize("kind", ["template", "test", "e2e"])
def test_이름은_접두_종류_서른두_자_16진수이고_63바이트_안이다(kind: str) -> None:
    name = make_name("a" * 21, kind)
    assert NAME_SHAPE.fullmatch(name) is not None
    assert name.startswith(f"{'a' * 21}_{kind}_")
    assert len(name.encode()) <= 63
    assert is_scoped_name(name)


def test_이름은_부를_때마다_다르다() -> None:
    assert make_name("agent_os", "test") != make_name("agent_os", "test")


def test_접두나_종류가_틀리면_이름을_짓지_않는다() -> None:
    with pytest.raises(ValueError, match="접두"):
        make_name("Bad", "test")
    with pytest.raises(ValueError, match="종류는 template, test, e2e 가운데 하나다"):
        make_name("agent_os", "prod")


def test_지울_수_있는_이름은_시험이_짓는_꼴뿐이다() -> None:
    good = make_name("agent_os", "e2e")
    assert is_scoped_name(good)
    bad = [
        "agent_os",
        "postgres",
        "agent_os_test_",
        "agent_os_test_" + "a" * 31,
        "agent_os_test_" + "a" * 33,
        "agent_os_test_" + "A" * 32,
        "agent_os_prod_" + "a" * 32,
        f'{good}"; DROP DATABASE agent_os; --',
        f"{good} ",
        f"{good}\n",
    ]
    assert [name for name in bad if is_scoped_name(name)] == []


# --- 까닭과 글 ----------------------------------------------------------------------------------


class _StateError(Exception):
    def __init__(self, sqlstate: str) -> None:
        super().__init__(f"드라이버가 낸 글 {SECRET}")
        self.sqlstate = sqlstate


def test_까닭은_오류_번호_가장_안쪽_OSError_바깥_예외_순이고_드라이버_글을_싣지_않는다() -> None:
    wrapped = RuntimeError(f"감싼 글 {SECRET}")
    wrapped.__cause__ = _StateError("28P01")
    assert reason_of(wrapped) == "오류 번호 28P01"

    outer = RuntimeError("바깥")
    outer.__cause__ = OSError("가운데")
    outer.__cause__.__cause__ = ConnectionRefusedError("안쪽")
    assert reason_of(outer) == "ConnectionRefusedError"

    assert reason_of(RuntimeError(SECRET)) == "RuntimeError"


def test_닿지_못한_글은_기본_주소면_띄우는_명령을_환경_변수면_변수_이름을_든다() -> None:
    default = resolve_address({})
    assert unreachable_text(default, ConnectionRefusedError()) == (
        "테스트 데이터베이스(127.0.0.1:25432/agent_os)에 닿지 못했습니다(ConnectionRefusedError). "
        f"이 명령으로 띄우십시오: {UP_COMMAND}"
    )
    given = _address(f"postgresql://u:{SECRET}@db.internal:6543/probe")
    assert unreachable_text(given, ConnectionRefusedError()) == (
        f"{URL_ENV} 이 가리키는 테스트 데이터베이스(db.internal:6543/probe)에 "
        "닿지 못했습니다(ConnectionRefusedError)."
    )


# --- 테스트 컨테이너에 닿는 함수 -----------------------------------------------------------------


async def test_답하는_서버는_문제가_없다(database_address: DatabaseAddress) -> None:
    assert await server_problem(database_address) is None


async def test_닫힌_포트는_닿지_못했다는_글이고_비밀번호가_없다(
    database_address: DatabaseAddress,
) -> None:
    dead = _address(_dead(database_address))
    problem = await server_problem(dead, seconds=5.0)
    assert problem is not None
    assert problem.startswith(
        f"{URL_ENV} 이 가리키는 테스트 데이터베이스({dead.place})에 닿지 못했습니다("
    )
    assert SECRET not in problem


async def test_데이터베이스를_만들고_지운다_없는_이름을_지워도_오류가_아니다(
    database_address: DatabaseAddress,
) -> None:
    name = make_name(_prefix(), "test")
    assert await _count(database_address, name) == 0
    await create_database(database_address, name)
    try:
        assert await _count(database_address, name) == 1
    finally:
        await drop_database(database_address, name)
    assert await _count(database_address, name) == 0
    await drop_database(database_address, name)


async def test_쓰는_연결이_있어도_지운다(database_address: DatabaseAddress) -> None:
    name = make_name(_prefix(), "test")
    await create_database(database_address, name)
    scoped = ScopedDatabase(address=database_address, name=name)
    try:
        async with plain(scoped, autocommit=True) as holder:
            await holder.execute(text("SELECT 1"))
            await drop_database(database_address, name)
            assert await _count(database_address, name) == 0
            with pytest.raises(DBAPIError):
                await holder.execute(text("SELECT 1"))
    finally:
        await drop_database(database_address, name)


async def test_템플릿을_복제한_데이터베이스에는_템플릿의_표가_있다(
    database_address: DatabaseAddress,
) -> None:
    prefix = _prefix()
    seen: list[str] = []

    async def migrate(url: str) -> None:
        seen.append(url)
        engine = create_async_engine(
            make_url(url).set(drivername="postgresql+asyncpg"), poolclass=NullPool
        )
        try:
            async with engine.begin() as connection:
                await connection.execute(text("CREATE TABLE copied_probe (id integer)"))
        finally:
            await engine.dispose()

    template = await build_template(database_address, prefix, migrate)
    clone = make_name(prefix, "test")
    try:
        assert template.startswith(f"{prefix}_template_")
        assert seen == [database_address.text_for(template)]
        await create_database(database_address, clone, template=template)
        assert "copied_probe" in await tables(ScopedDatabase(database_address, clone))
    finally:
        await drop_database(database_address, clone)
        await drop_database(database_address, template)


async def test_템플릿에_올리다_실패하면_템플릿을_지우고_그_예외를_다시_던진다(
    database_address: DatabaseAddress,
) -> None:
    prefix = _prefix()

    async def migrate(url: str) -> None:
        raise RuntimeError("올리기 실패")

    with pytest.raises(RuntimeError, match="올리기 실패"):
        await build_template(database_address, prefix, migrate)
    remaining = await _count(database_address, f"{prefix}\\_template\\_%")
    assert remaining == 0, f"남은 템플릿 {remaining}개"


# --- 명령줄 -------------------------------------------------------------------------------------


async def _run(argv: list[str], environ: Mapping[str, str]) -> int:
    return await asyncio.to_thread(main, argv, environ)


async def test_create는_빈_데이터베이스를_만들고_주소를_한_줄_찍고_drop이_지운다(
    database_address: DatabaseAddress,
    capsys: pytest.CaptureFixture[str],
) -> None:
    prefix = _prefix()
    environ = {URL_ENV: database_address.text_for(database_address.url.database or "")}
    assert await _run(["create", prefix], environ) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    lines = captured.out.splitlines()
    assert len(lines) == 1
    created = make_url(lines[0])
    name = created.database or ""
    assert NAME_SHAPE.fullmatch(name) is not None
    assert name.startswith(f"{prefix}_e2e_")
    assert created.render_as_string(hide_password=False) == database_address.text_for(name)
    try:
        assert await _count(database_address, name) == 1
        assert await tables(ScopedDatabase(database_address, name)) == set()
    finally:
        assert await _run(["drop", name], environ) == 0
    assert await _count(database_address, name) == 0
    assert capsys.readouterr().err == ""


async def test_drop은_시험이_짓는_꼴이_아닌_이름은_지우지_않고_1로_끝난다(
    database_address: DatabaseAddress,
    capsys: pytest.CaptureFixture[str],
) -> None:
    administrative = database_address.url.database or ""
    environ = {URL_ENV: database_address.text_for(administrative)}
    assert await _run(["drop", administrative], environ) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == (
        "지울 수 있는 이름의 꼴이 아닙니다. <접두>_(e2e|test|template)_<16진수 32자> 만 지웁니다.\n"
    )
    assert await _count(database_address, administrative) == 1


async def test_접두가_틀리면_create는_서버에_닿기_전에_1로_끝난다(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert await _run(["create", "Bad-Prefix"], {}) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == "데이터베이스 이름의 접두 'Bad-Prefix' 은 소문자, 숫자, 밑줄만 쓴다\n"


@pytest.mark.parametrize("argv", [[], ["create"], ["drop"], ["create", "a", "b"], ["list"]])
async def test_인자가_틀리면_사용법을_찍고_1로_끝난다(
    argv: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    assert await _run(argv, {}) == 1
    captured = capsys.readouterr()
    assert (captured.out, captured.err) == (
        "",
        "사용법: database_for_tests.py create <접두> | drop <이름>\n",
    )


@pytest.mark.parametrize("command", ["create", "drop"])
async def test_서버가_답하지_않으면_시험_쪽_글을_찍고_1로_끝난다(
    command: str,
    database_address: DatabaseAddress,
    capsys: pytest.CaptureFixture[str],
) -> None:
    dead_text = _dead(database_address)
    argument = _prefix() if command == "create" else make_name(_prefix(), "e2e")
    assert await _run([command, argument], {URL_ENV: dead_text}) == 1
    captured = capsys.readouterr()
    place = _address(dead_text).place
    assert captured.out == ""
    assert captured.err.startswith(
        f"{URL_ENV} 이 가리키는 테스트 데이터베이스({place})에 닿지 못했습니다("
    )
    assert SECRET not in captured.err


async def test_받지_않는_환경_변수면_create는_글을_찍고_1로_끝난다(
    capsys: pytest.CaptureFixture[str],
) -> None:
    assert await _run(["create", "tdbx"], {URL_ENV: f"postgresql://u:{SECRET}@h:1/d?x=1"}) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.startswith(f"{URL_ENV} 에 질의 문자열(? 뒤)이 들어 있어 받지 않습니다.")
    assert SECRET not in captured.err


async def test_실제_프로세스로_create와_drop을_부른다(database_address: DatabaseAddress) -> None:
    """스크립트로 직접 실행되는 길(`__main__`)과 표준 출력의 한 줄을 본다."""
    environment = dict(os.environ)
    environment[URL_ENV] = database_address.text_for(database_address.url.database or "")
    script = str(ROOT / "tools" / "database_for_tests.py")

    def call(*arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-I", script, *arguments],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=environment,
            cwd=ROOT,
            timeout=120,
        )

    created = await asyncio.to_thread(call, "create", _prefix())
    assert (created.returncode, created.stderr) == (0, "")
    lines = created.stdout.splitlines()
    assert len(lines) == 1
    name = make_url(lines[0]).database or ""
    try:
        assert is_scoped_name(name)
        assert await _count(database_address, name) == 1
    finally:
        dropped = await asyncio.to_thread(call, "drop", name)
    assert (dropped.returncode, dropped.stdout, dropped.stderr) == (0, "", "")
    assert await _count(database_address, name) == 0
