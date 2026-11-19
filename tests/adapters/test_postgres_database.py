"""PostgreSQL 어댑터(`agent_os.adapters.postgres.database`)를 실제 테스트 데이터베이스에 붙여 본다.

운영자와 개발자에게 보이는 것을 본다. 찍히는 글, 판 기록 표의 줄, 닿는지 아닌지다. 글은 글자까지
단언한다(명세 postgres-foundation "멈출 때의 글"). 판의 갈래는 템플릿을 거치지 않은 빈
데이터베이스에 시험용 마이그레이션 폴더(`postgres_versions/`의 9001, 9002)를 대서 만든다.

테스트 컨테이너가 없으면 `database_address` 픽스처가 시험 쪽 글로 setup 오류를 낸다(skip이 아니다).
"""

from __future__ import annotations

import asyncio
import socket
import time
import uuid
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import text
from tests.postgres_support import (
    FIRST,
    SECOND,
    closed_port,
    copy_versions,
    other_connections,
    plain,
    revisions,
    tables,
)
from tools.database_for_tests import ScopedDatabase

from agent_os.adapters.postgres.database import (
    DatabaseUrl,
    Failure,
    PostgresDatabase,
    failure_kind,
    parse_database_url,
    reason_of,
)

# 시험이 짧게 주는 다시 시도 시간과 시도 하나의 제한 시간. 기본값(30초, 5초)을 쓰면 시험이 느리다.
SHORT_RETRY = 0.6
SHORT_INTERVAL = 0.1
SHORT_ATTEMPT = 0.4
# 시간 단언의 상한은 홀로 돈 시간의 넉넉한 배수다(`.claude/rules/tests.md`).
GENEROUS = 20.0
# 비밀번호가 글에 실리는지 보려고 계정 이름과 다른, 알아볼 수 있는 값을 쓴다.
SECRET = "leak_probe_pw"


def _url(value: str) -> DatabaseUrl:
    url = parse_database_url(value)
    if url is None:
        raise AssertionError("어댑터가 읽지 못한 주소다")
    return url


class Notices:
    """어댑터가 알린 글을 모은다."""

    def __init__(self) -> None:
        self.lines: list[str] = []

    def __call__(self, message: str) -> None:
        self.lines.append(message)


def _adapter(
    address: str,
    versions: Path,
    notices: Notices,
    *,
    retry_seconds: float = SHORT_RETRY,
    attempt_seconds: float = SHORT_ATTEMPT,
) -> PostgresDatabase:
    return PostgresDatabase(
        _url(address),
        notice=notices,
        versions=versions,
        retry_seconds=retry_seconds,
        retry_interval=SHORT_INTERVAL,
        attempt_seconds=attempt_seconds,
    )


def _address(
    database: ScopedDatabase,
    *,
    username: str | None = None,
    password: str | None = None,
    port: int | None = None,
    name: str | None = None,
) -> str:
    """접속 문자열. 계정, 비밀번호, 포트, 데이터베이스 이름 가운데 바꿀 것만 바꾼다."""
    url = database.address.url.set(database=name or database.name)
    if username is not None:
        url = url.set(username=username)
    if password is not None:
        url = url.set(password=password)
    if port is not None:
        url = url.set(port=port)
    return url.render_as_string(hide_password=False)


@pytest_asyncio.fixture
async def silent_port() -> AsyncIterator[int]:
    """접속은 받되 아무 말도 하지 않는 빈 TCP 서버의 포트."""
    writers: list[asyncio.StreamWriter] = []

    async def hold(reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        writers.append(writer)
        await reader.read()

    server = await asyncio.start_server(hold, "127.0.0.1", 0)
    port = int(server.sockets[0].getsockname()[1])
    try:
        yield port
    finally:
        server.close()
        for writer in writers:
            writer.close()
        await server.wait_closed()


class _SqlstateError(Exception):
    """드라이버가 오류 번호를 실은 예외의 모양. 클래스 이름은 갈래와 상관없다."""

    def __init__(self, sqlstate: str) -> None:
        super().__init__("드라이버가 낸 글")
        self.sqlstate = sqlstate


# --- 갈래와 까닭: 예외의 클래스가 아니라 오류 번호와 OSError 여부로 가른다 ------------------------


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        ("28P01", Failure.PASSWORD),
        ("28000", Failure.NOT_ALLOWED),
        ("3D000", Failure.NO_DATABASE),
        ("57P03", Failure.TRANSIENT),
        ("08006", Failure.TRANSIENT),
        ("08001", Failure.TRANSIENT),
        ("42P01", Failure.OTHER),
        ("53300", Failure.OTHER),
    ],
)
def test_갈래는_오류_번호로_가른다(state: str, expected: Failure) -> None:
    assert failure_kind(_SqlstateError(state)) is expected


def test_오류_번호가_없으면_사슬에_OSError가_있는지로_가른다() -> None:
    assert failure_kind(ConnectionRefusedError()) is Failure.TRANSIENT
    assert failure_kind(TimeoutError()) is Failure.TRANSIENT
    assert failure_kind(RuntimeError("뜻밖")) is Failure.OTHER
    try:
        try:
            raise socket.gaierror("이름 풀이 실패")
        except OSError as inner:
            raise RuntimeError("감싼 예외") from inner
    except RuntimeError as wrapped:
        assert failure_kind(wrapped) is Failure.TRANSIENT


def test_바깥_예외가_감싸도_안쪽의_오류_번호로_가른다() -> None:
    try:
        try:
            raise _SqlstateError("28P01")
        except _SqlstateError as inner:
            raise RuntimeError("DBAPIError 처럼 감싼 예외") from inner
    except RuntimeError as wrapped:
        assert failure_kind(wrapped) is Failure.PASSWORD
        assert reason_of(wrapped) == "오류 번호 28P01"


def test_오류_번호가_OSError보다_먼저다() -> None:
    error = _SqlstateError("28P01")
    error.__cause__ = ConnectionResetError()
    assert failure_kind(error) is Failure.PASSWORD


def test_까닭은_오류_번호_가장_안쪽_OSError_바깥_예외의_이름_순이다() -> None:
    assert reason_of(_SqlstateError("3D000")) == "오류 번호 3D000"
    assert reason_of(ConnectionRefusedError("드라이버의 글")) == "ConnectionRefusedError"
    assert reason_of(RuntimeError("비밀번호가 든 글")) == "RuntimeError"
    try:
        try:
            raise socket.gaierror("이름 풀이 실패")
        except OSError as inner:
            raise RuntimeError("감싼 예외") from inner
    except RuntimeError as wrapped:
        assert reason_of(wrapped) == "gaierror"


# --- 주소: 비밀번호를 되울리지 않는다 ----------------------------------------------------------


@pytest.mark.parametrize(
    "value",
    [
        "postgresql://agent_os:agent_os@postgres:5432/agent_os",
        "postgresql://agent_os:agent_os@127.0.0.1/agent_os",
        "postgresql://agent_os@postgres/agent_os",
    ],
)
def test_알려진_꼴의_주소를_읽는다(value: str) -> None:
    assert parse_database_url(value) is not None


@pytest.mark.parametrize(
    "value",
    [
        "",
        "agent_os",
        "mysql://agent_os:agent_os@postgres:5432/agent_os",
        "postgresql+asyncpg://agent_os:agent_os@postgres:5432/agent_os",
        "postgres://agent_os:agent_os@postgres:5432/agent_os",
        "postgresql://agent_os:agent_os@postgres:5432/agent_os?database=other",
        "postgresql://agent_os:secret@leak@postgres:5432/agent_os",
        "postgresql://agent_os:agent_os@/agent_os",
        "postgresql://agent_os:agent_os@postgres:5432/",
        "postgresql://agent_os:agent_os@postgres:쉰/agent_os",
    ],
)
def test_받지_않는_주소는_읽지_못한다(value: str) -> None:
    assert parse_database_url(value) is None


def test_주소를_담는_값의_repr과_문자열에_비밀번호가_없다() -> None:
    url = _url(f"postgresql://agent_os:{SECRET}@postgres:5432/agent_os")
    assert SECRET not in repr(url)
    assert SECRET not in str(url)
    assert url.place == "postgres:5432/agent_os"


def test_포트를_적지_않으면_5432다() -> None:
    assert (
        _url("postgresql://agent_os:agent_os@postgres/agent_os").place == "postgres:5432/agent_os"
    )


# --- 표의 판 견줌과 올리기(템플릿을 거치지 않은 빈 데이터베이스) ---------------------------------


async def test_파일이_없는_폴더에서_빈_데이터베이스는_맞고_alembic을_부르지_않는다(
    empty_database: ScopedDatabase, tmp_path: Path
) -> None:
    folders = [tmp_path / "없는_폴더", tmp_path / "빈_폴더"]
    folders[1].mkdir()
    for folder in folders:
        adapter = _adapter(empty_database.text(), folder, Notices())
        try:
            assert await adapter.startup_problem() is None
            result = await adapter.migrate()
        finally:
            await adapter.close()
        assert (result.ok, result.message) == (True, "표가 이미 마지막 판(없음)입니다.")
    assert "alembic_version" not in await tables(empty_database)


async def test_시험용_폴더로_빈_데이터베이스는_뒤처졌고_올린_뒤에는_맞다(
    empty_database: ScopedDatabase, tmp_path: Path
) -> None:
    versions = copy_versions(tmp_path / "versions", FIRST, SECOND)
    adapter = _adapter(empty_database.text(), versions, Notices())
    try:
        assert await adapter.startup_problem() == (
            "데이터베이스의 표가 이 판보다 뒤처져 있습니다. agent-os migrate 를 먼저 돌리십시오.\n"
            "  표의 판은 없음이고 이 판의 마지막 판은 9002입니다."
        )
        result = await adapter.migrate()
        assert (result.ok, result.message) == (True, "표를 없음에서 9002으로 올렸습니다.")
        assert await adapter.startup_problem() is None
        again = await adapter.migrate()
        assert (again.ok, again.message) == (True, "표가 이미 마지막 판(9002)입니다.")
    finally:
        await adapter.close()
    assert await revisions(empty_database) == ["9002"]
    assert {"probe_one", "probe_two"} <= await tables(empty_database)


async def test_아는_옛_번호는_뒤처졌다(empty_database: ScopedDatabase, tmp_path: Path) -> None:
    older = copy_versions(tmp_path / "older", FIRST)
    newer = copy_versions(tmp_path / "newer", FIRST, SECOND)
    first = _adapter(empty_database.text(), older, Notices())
    second = _adapter(empty_database.text(), newer, Notices())
    try:
        assert (await first.migrate()).ok
        assert await second.startup_problem() == (
            "데이터베이스의 표가 이 판보다 뒤처져 있습니다. agent-os migrate 를 먼저 돌리십시오.\n"
            "  표의 판은 9001이고 이 판의 마지막 판은 9002입니다."
        )
        result = await second.migrate()
        assert (result.ok, result.message) == (True, "표를 9001에서 9002으로 올렸습니다.")
    finally:
        await first.close()
        await second.close()
    assert await revisions(empty_database) == ["9002"]


async def test_모르는_번호는_더_새롭고_올리기는_표를_건드리지_않는다(
    empty_database: ScopedDatabase, tmp_path: Path
) -> None:
    older = copy_versions(tmp_path / "older", FIRST)
    newer = copy_versions(tmp_path / "newer", FIRST, SECOND)
    newer_adapter = _adapter(empty_database.text(), newer, Notices())
    older_adapter = _adapter(empty_database.text(), older, Notices())
    expected = (
        "데이터베이스가 이 판보다 새롭습니다. 되돌리려면 올리기 전의 백업을 복원하십시오.\n"
        "  표의 판은 9002이고 이 판이 아는 마지막 판은 9001입니다."
    )
    try:
        assert (await newer_adapter.migrate()).ok
        assert await older_adapter.startup_problem() == expected
        result = await older_adapter.migrate()
        assert (result.ok, result.message) == (False, expected)
    finally:
        await newer_adapter.close()
        await older_adapter.close()
    assert await revisions(empty_database) == ["9002"]


async def test_폴더가_비어_있으면_표에_번호가_있는_데이터베이스는_더_새롭다(
    empty_database: ScopedDatabase, tmp_path: Path
) -> None:
    versions = copy_versions(tmp_path / "versions", FIRST)
    filled = _adapter(empty_database.text(), versions, Notices())
    empty = _adapter(empty_database.text(), tmp_path / "없는_폴더", Notices())
    try:
        assert (await filled.migrate()).ok
        assert await empty.startup_problem() == (
            "데이터베이스가 이 판보다 새롭습니다. 되돌리려면 올리기 전의 백업을 복원하십시오.\n"
            "  표의 판은 9001이고 이 판이 아는 마지막 판은 없음입니다."
        )
    finally:
        await filled.close()
        await empty.close()


async def test_올리기를_마치고_닫으면_연결이_남지_않는다(
    empty_database: ScopedDatabase, tmp_path: Path
) -> None:
    versions = copy_versions(tmp_path / "versions", FIRST, SECOND)
    adapter = _adapter(empty_database.text(), versions, Notices())
    assert (await adapter.migrate()).ok
    await adapter.close()
    assert await other_connections(empty_database) == 0


# --- 닿지 못하는 갈래 --------------------------------------------------------------------------


async def test_틀린_비밀번호는_다시_시도하지_않고_바로_비밀번호_글이다(
    empty_database: ScopedDatabase, tmp_path: Path
) -> None:
    notices = Notices()
    adapter = _adapter(_address(empty_database, password=SECRET), tmp_path / "versions", notices)
    started = time.monotonic()
    try:
        problem = await adapter.startup_problem()
    finally:
        await adapter.close()
    assert time.monotonic() - started < SHORT_RETRY + GENEROUS
    assert problem == (
        f"데이터베이스({empty_database.place})가 계정이나 비밀번호를 받아들이지 않았습니다"
        "(오류 번호 28P01).\n"
        "  .env 의 비밀번호만 바꿨다면 데이터베이스 안의 비밀번호도 바꿔야 합니다."
        ' 배포 안내의 "데이터베이스 비밀번호 바꾸기"를 보십시오.'
    )
    assert notices.lines == []
    assert problem is not None
    assert SECRET not in problem


async def test_로그인을_막은_계정은_다시_시도하지_않고_바로_접속을_허락하지_않았다는_글이다(
    empty_database: ScopedDatabase, tmp_path: Path
) -> None:
    role = f"agent_os_nologin_{uuid.uuid4().hex}"
    notices = Notices()
    async with plain(
        empty_database, autocommit=True, name=empty_database.address.url.database
    ) as admin:
        await admin.execute(text(f"CREATE ROLE \"{role}\" NOLOGIN PASSWORD '{SECRET}'"))
        try:
            adapter = _adapter(
                _address(empty_database, username=role, password=SECRET),
                tmp_path / "versions",
                notices,
            )
            try:
                problem = await adapter.startup_problem()
            finally:
                await adapter.close()
        finally:
            await admin.execute(text(f'DROP ROLE "{role}"'))
    assert problem == (
        f"데이터베이스({empty_database.place})가 이 접속을 허락하지 않았습니다(오류 번호 28000).\n"
        "  처음 띄우기가 끝나기 전에 서버가 꺼졌다면 데이터베이스가 반쯤 만들어진 채 남았을 수"
        ' 있습니다. 배포 안내의 "띄우기가 끊겼을 때"를 보십시오.'
    )
    assert notices.lines == []
    assert problem is not None
    assert SECRET not in problem


async def test_없는_데이터베이스_이름은_바로_데이터베이스_없음_글이다(
    empty_database: ScopedDatabase, tmp_path: Path
) -> None:
    missing = f"agent_os_missing_{uuid.uuid4().hex}"
    place = f"{empty_database.address.url.host}:{empty_database.address.url.port}/{missing}"
    notices = Notices()
    adapter = _adapter(_address(empty_database, name=missing), tmp_path / "versions", notices)
    try:
        problem = await adapter.startup_problem()
    finally:
        await adapter.close()
    assert problem == (
        f"데이터베이스({place})가 없습니다(오류 번호 3D000)."
        " 주소의 데이터베이스 이름을 확인하십시오.\n"
        "  처음 띄우기가 끝나기 전에 서버가 꺼졌다면 데이터베이스가 반쯤 만들어진 채 남았을 수"
        ' 있습니다. 배포 안내의 "띄우기가 끊겼을 때"를 보십시오.'
    )
    assert notices.lines == []


async def test_접속_권한이_없는_계정은_다시_시도하지_않고_그_밖_글이다(
    empty_database: ScopedDatabase, tmp_path: Path
) -> None:
    """오류 번호 42501(권한 없음)은 표의 다섯 갈래에 없는 번호라 `그 밖` 글로 나온다."""
    role = f"agent_os_noconnect_{uuid.uuid4().hex}"
    notices = Notices()
    async with plain(
        empty_database, autocommit=True, name=empty_database.address.url.database
    ) as admin:
        await admin.execute(text(f"CREATE ROLE \"{role}\" LOGIN PASSWORD '{SECRET}'"))
        # 접속 권한은 이 시험의 데이터베이스에서만 거둔다. 공용 기본 데이터베이스는 건드리지 않는다.
        await admin.execute(text(f'REVOKE CONNECT ON DATABASE "{empty_database.name}" FROM PUBLIC'))
        try:
            adapter = _adapter(
                _address(empty_database, username=role, password=SECRET),
                tmp_path / "versions",
                notices,
            )
            try:
                problem = await adapter.startup_problem()
            finally:
                await adapter.close()
        finally:
            await admin.execute(text(f'DROP ROLE "{role}"'))
    assert (
        problem == f"데이터베이스({empty_database.place})에 접속하지 못했습니다(오류 번호 42501)."
    )
    assert notices.lines == []


async def test_경로에_세미콜론이_든_마이그레이션_폴더도_판을_찾아_올린다(
    empty_database: ScopedDatabase, tmp_path: Path
) -> None:
    """`path_separator` 가 `os` 면 `;`(POSIX 는 `:`)에서 경로가 갈려 폴더를 못 찾고, 판이 있는
    폴더가 빈 폴더처럼 맞다고 읽힌다."""
    versions = copy_versions(tmp_path / "버전;폴더", FIRST, SECOND)
    adapter = _adapter(empty_database.text(), versions, Notices())
    try:
        result = await adapter.migrate()
    finally:
        await adapter.close()
    assert result.message == "표를 없음에서 9002으로 올렸습니다."
    assert result.ok
    assert await revisions(empty_database) == ["9002"]


async def test_닫힌_포트는_다시_시도한_뒤_닿지_못했다는_글이고_알림이_한_번_찍힌다(
    empty_database: ScopedDatabase, tmp_path: Path
) -> None:
    port = closed_port()
    place = f"{empty_database.address.url.host}:{port}/{empty_database.name}"
    notices = Notices()
    adapter = _adapter(_address(empty_database, port=port), tmp_path / "versions", notices)
    started = time.monotonic()
    try:
        problem = await adapter.startup_problem()
    finally:
        await adapter.close()
    elapsed = time.monotonic() - started
    assert SHORT_RETRY <= elapsed < GENEROUS
    assert problem is not None
    assert problem.startswith(
        f"데이터베이스({place})에 닿지 못했습니다. 0.6초 동안 다시 시도했습니다("
    )
    assert problem.endswith("Error).")
    assert notices.lines == [
        f"데이터베이스({place})에 아직 닿지 못해 최대 0.6초 동안 다시 시도합니다."
    ]


async def test_접속은_받되_답하지_않는_서버는_시간_안에_돌아온다(
    empty_database: ScopedDatabase, tmp_path: Path, silent_port: int
) -> None:
    place = f"{empty_database.address.url.host}:{silent_port}/{empty_database.name}"
    notices = Notices()
    adapter = _adapter(_address(empty_database, port=silent_port), tmp_path / "versions", notices)
    started = time.monotonic()
    try:
        async with asyncio.timeout(GENEROUS):
            problem = await adapter.startup_problem()
    finally:
        await adapter.close()
    assert time.monotonic() - started < GENEROUS
    assert problem == (
        f"데이터베이스({place})에 닿지 못했습니다. 0.6초 동안 다시 시도했습니다(TimeoutError)."
    )
    assert len(notices.lines) == 1


async def test_판_기록_표가_잠겨_있으면_연결은_열려도_시간_안에_돌아온다(
    empty_database: ScopedDatabase, tmp_path: Path
) -> None:
    """시도 하나를 드라이버의 접속 인자로만 걸면 이 사례는 잠금이 풀릴 때까지 돌아오지 않는다."""
    versions = copy_versions(tmp_path / "versions", FIRST)
    setup = _adapter(empty_database.text(), versions, Notices())
    try:
        assert (await setup.migrate()).ok
    finally:
        await setup.close()
    adapter = _adapter(empty_database.text(), versions, Notices())
    started = time.monotonic()
    try:
        async with plain(empty_database) as holder:
            await holder.execute(text("LOCK TABLE alembic_version IN ACCESS EXCLUSIVE MODE"))
            async with asyncio.timeout(GENEROUS):
                problem = await adapter.startup_problem()
            elapsed = time.monotonic() - started
            await holder.rollback()
        async with asyncio.timeout(GENEROUS):
            await adapter.close()
    finally:
        await adapter.close()
    assert elapsed < GENEROUS
    assert problem == (
        f"데이터베이스({empty_database.place})에 닿지 못했습니다. 0.6초 동안 다시 시도했습니다"
        "(TimeoutError)."
    )
    assert await other_connections(empty_database) == 0


async def test_뜻밖의_예외의_글은_예외의_글을_싣지_않고_까닭만_싣는다(
    empty_database: ScopedDatabase, tmp_path: Path
) -> None:
    adapter = _adapter(empty_database.text(), tmp_path / "versions", Notices())
    try:
        message = adapter.unexpected_problem(RuntimeError(f"비밀번호 {SECRET} 가 섞인 글"))
    finally:
        await adapter.close()
    assert message == (
        f"데이터베이스({empty_database.place})를 확인하다 뜻밖의 오류로 멈췄습니다(RuntimeError).\n"
        "  이 판의 결함일 수 있습니다. 예외의 글과 역추적은 비밀번호가 섞일 수 있어 찍지 않습니다."
    )
    assert SECRET not in message
