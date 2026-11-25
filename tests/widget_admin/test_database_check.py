"""위젯 관리 서버의 데이터베이스 객체(`widget_admin.database`)를 실제 테스트 데이터베이스에 붙여
본다.

운영자와 개발자에게 보이는 것을 본다. 찍히는 글, 판 기록 표의 줄, 닿는지 아닌지다. 글은 글자까지
단언한다(명세 widget-admin-server "멈출 때의 글"). 판의 갈래는 템플릿을 거치지 않은 빈
데이터베이스에 시험용 마이그레이션 폴더(`tests/adapters/postgres_versions/`의 9001, 9002)를 대서
만든다. 제품 폴더(`0001_sites`)는 조립을 거치는 사례 하나만 쓴다. 선례는
`tests/adapters/test_postgres_database.py`다.

테스트 컨테이너가 없으면 `database_address` 픽스처가 시험 쪽 글로 setup 오류를 낸다(skip이 아니다).
"""

from __future__ import annotations

import asyncio
import socket
import time
import uuid
from pathlib import Path

import pytest
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
from tests.widget_admin.support import (
    GENEROUS,
    SECRET,
    SHORT_RETRY,
    Notices,
    adapter,
    address_of,
    database_url,
    patient,
)
from tools.database_for_tests import ScopedDatabase

from widget_admin.database import (
    DEFAULT_ATTEMPT_SECONDS,
    DEFAULT_RETRY_INTERVAL,
    DEFAULT_RETRY_SECONDS,
    PRODUCT_VERSIONS,
    Failure,
    failure_kind,
    parse_database_url,
    reason_of,
)


class _SqlstateError(Exception):
    """드라이버가 오류 번호를 실은 예외의 모양. 클래스 이름은 갈래와 상관없다."""

    def __init__(self, sqlstate: str) -> None:
        super().__init__("드라이버가 낸 글")
        self.sqlstate = sqlstate


# --- 기본값과 갈래: 예외의 클래스가 아니라 오류 번호와 OSError 여부로 가른다 -----


def test_기본값은_다시_시도_30초와_시도_사이_1초와_시도_하나_5초다() -> None:
    assert (DEFAULT_RETRY_SECONDS, DEFAULT_RETRY_INTERVAL, DEFAULT_ATTEMPT_SECONDS) == (
        30.0,
        1.0,
        5.0,
    )


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        ("28P01", Failure.PASSWORD),
        ("28000", Failure.NOT_ALLOWED),
        ("3D000", Failure.NO_DATABASE),
        ("57P03", Failure.TRANSIENT),
        ("08006", Failure.TRANSIENT),
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
        assert reason_of(wrapped) == "gaierror"


def test_까닭은_오류_번호_가장_안쪽_OSError_바깥_예외의_이름_순이다() -> None:
    assert reason_of(_SqlstateError("3D000")) == "오류 번호 3D000"
    assert reason_of(ConnectionRefusedError("드라이버의 글")) == "ConnectionRefusedError"
    assert reason_of(RuntimeError("비밀번호가 든 글")) == "RuntimeError"


# --- 주소: 비밀번호를 되울리지 않는다 ----------------------------------------------------------


@pytest.mark.parametrize(
    "value",
    [
        "postgresql://widget_admin:pw@widget-admin-postgres:5432/widget_admin",
        "postgresql://widget_admin:pw@127.0.0.1/widget_admin",
        "postgresql://widget_admin@widget-admin-postgres/widget_admin",
    ],
)
def test_알려진_꼴의_주소를_읽는다(value: str) -> None:
    assert parse_database_url(value) is not None


@pytest.mark.parametrize(
    "value",
    [
        "",
        "widget_admin",
        "mysql://widget_admin:pw@postgres:5432/widget_admin",
        "postgresql+asyncpg://widget_admin:pw@postgres:5432/widget_admin",
        "postgres://widget_admin:pw@postgres:5432/widget_admin",
        # `sslmode` 같은 질의 문자열은 받지 않는다. asyncpg 는 `sslmode` 를 몰라 첫 질의에서 죽는다.
        "postgresql://widget_admin:pw@postgres:5432/widget_admin?sslmode=require",
        "postgresql://widget_admin:pw@postgres:5432/widget_admin?database=other",
        "postgresql://widget_admin:secret@leak@postgres:5432/widget_admin",
        # 계정 자리에 `/` 가 들면 SQLAlchemy 가 계정 묶음을 버리고 비밀번호를 데이터베이스 이름으로
        # 읽는다.
        "postgresql://widget/admin:secret@postgres:5432/widget_admin",
        "postgresql://widget_admin:pw@/widget_admin",
        "postgresql://widget_admin:pw@postgres:5432/",
        "postgresql://widget_admin:pw@postgres:쉰/widget_admin",
    ],
)
def test_받지_않는_주소는_읽지_못한다(value: str) -> None:
    assert parse_database_url(value) is None


def test_주소를_담는_값의_repr과_문자열에_비밀번호가_없다() -> None:
    place = "widget-admin-postgres:5432/widget_admin"
    url = database_url(f"postgresql://widget_admin:{SECRET}@{place}")
    assert SECRET not in repr(url)
    assert SECRET not in str(url)
    assert url.place == "widget-admin-postgres:5432/widget_admin"


def test_포트를_적지_않으면_5432다() -> None:
    url = database_url("postgresql://widget_admin:pw@widget-admin-postgres/widget_admin")
    assert url.place == "widget-admin-postgres:5432/widget_admin"


# --- 표의 판 견줌과 올리기(템플릿을 거치지 않은 빈 데이터베이스) ---------------------------------


async def test_제품_폴더로_빈_데이터베이스는_뒤처졌고_올린_뒤에는_맞다(
    empty_database: ScopedDatabase,
) -> None:
    notices = Notices()
    database = patient(empty_database.text(), PRODUCT_VERSIONS, notices)
    try:
        assert await database.startup_problem() == (
            "데이터베이스의 표가 이 판보다 뒤처져 있습니다. widget-admin migrate 를 먼저"
            " 돌리십시오.\n"
            "  표의 판은 없음이고 이 판의 마지막 판은 0001입니다."
        )
        result = await database.migrate()
        assert (result.ok, result.message) == (True, "표를 없음에서 0001으로 올렸습니다.")
        assert await database.startup_problem() is None
    finally:
        await database.close()
    assert await revisions(empty_database) == ["0001"]
    assert "sites" in await tables(empty_database)
    assert notices.lines == []


async def test_시험용_폴더로_빈_데이터베이스는_뒤처졌고_올린_뒤에는_맞다_다시_올려도_그대로다(
    empty_database: ScopedDatabase, tmp_path: Path
) -> None:
    versions = copy_versions(tmp_path / "versions", FIRST, SECOND)
    database = patient(empty_database.text(), versions, Notices())
    try:
        assert await database.startup_problem() == (
            "데이터베이스의 표가 이 판보다 뒤처져 있습니다. widget-admin migrate 를 먼저"
            " 돌리십시오.\n"
            "  표의 판은 없음이고 이 판의 마지막 판은 9002입니다."
        )
        result = await database.migrate()
        assert (result.ok, result.message) == (True, "표를 없음에서 9002으로 올렸습니다.")
        assert await database.startup_problem() is None
        again = await database.migrate()
        assert (again.ok, again.message) == (True, "표가 이미 마지막 판(9002)입니다.")
    finally:
        await database.close()
    assert await revisions(empty_database) == ["9002"]
    assert {"probe_one", "probe_two"} <= await tables(empty_database)


async def test_모르는_번호는_더_새롭고_올리기는_표를_건드리지_않는다(
    empty_database: ScopedDatabase, tmp_path: Path
) -> None:
    older = copy_versions(tmp_path / "older", FIRST)
    newer = copy_versions(tmp_path / "newer", FIRST, SECOND)
    newer_database = patient(empty_database.text(), newer, Notices())
    older_database = patient(empty_database.text(), older, Notices())
    expected = (
        "데이터베이스가 이 판보다 새롭습니다. 되돌리려면 올리기 전의 백업을 복원하십시오.\n"
        "  표의 판은 9002이고 이 판이 아는 마지막 판은 9001입니다."
    )
    try:
        assert (await newer_database.migrate()).ok
        assert await older_database.startup_problem() == expected
        result = await older_database.migrate()
        assert (result.ok, result.message) == (False, expected)
    finally:
        await newer_database.close()
        await older_database.close()
    assert await revisions(empty_database) == ["9002"]


async def test_올리기를_마치고_닫으면_연결이_남지_않는다(
    empty_database: ScopedDatabase, tmp_path: Path
) -> None:
    versions = copy_versions(tmp_path / "versions", FIRST, SECOND)
    database = patient(empty_database.text(), versions, Notices())
    assert (await database.migrate()).ok
    await database.close()
    assert await other_connections(empty_database) == 0


# --- 닿지 못하는 갈래 --------------------------------------------------------------------------


def _without_credentials(problem: str | None, scoped: ScopedDatabase) -> None:
    """글에 `계정:비밀번호@` 꼴이 없다. 테스트 컨테이너의 비밀번호는 계정 이름과 같아서 비밀번호
    글자만 찾으면 주소의 다른 조각과 가려지지 않는다."""
    assert problem is not None
    url = scoped.address.url
    assert f"{url.username}:{url.password}@" not in problem


async def test_틀린_비밀번호는_다시_시도하지_않고_바로_비밀번호_글이다(
    empty_database: ScopedDatabase, tmp_path: Path
) -> None:
    notices = Notices()
    database = patient(address_of(empty_database, password=SECRET), tmp_path / "versions", notices)
    started = time.monotonic()
    try:
        problem = await database.startup_problem()
    finally:
        await database.close()
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
    role = f"widget_admin_nologin_{uuid.uuid4().hex}"
    notices = Notices()
    async with plain(
        empty_database, autocommit=True, name=empty_database.address.url.database
    ) as admin:
        await admin.execute(text(f"CREATE ROLE \"{role}\" NOLOGIN PASSWORD '{SECRET}'"))
        try:
            database = patient(
                address_of(empty_database, username=role, password=SECRET),
                tmp_path / "versions",
                notices,
            )
            try:
                problem = await database.startup_problem()
            finally:
                await database.close()
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
    missing = f"widget_admin_missing_{uuid.uuid4().hex}"
    place = f"{empty_database.address.url.host}:{empty_database.address.url.port}/{missing}"
    notices = Notices()
    database = patient(address_of(empty_database, name=missing), tmp_path / "versions", notices)
    try:
        problem = await database.startup_problem()
    finally:
        await database.close()
    assert problem == (
        f"데이터베이스({place})가 없습니다(오류 번호 3D000)."
        " 주소의 데이터베이스 이름을 확인하십시오.\n"
        "  처음 띄우기가 끝나기 전에 서버가 꺼졌다면 데이터베이스가 반쯤 만들어진 채 남았을 수"
        ' 있습니다. 배포 안내의 "띄우기가 끊겼을 때"를 보십시오.'
    )
    assert notices.lines == []
    _without_credentials(problem, empty_database)


async def test_닫힌_포트는_다시_시도한_뒤_닿지_못했다는_글이고_알림이_한_번_찍힌다(
    empty_database: ScopedDatabase, tmp_path: Path
) -> None:
    port = closed_port()
    place = f"{empty_database.address.url.host}:{port}/{empty_database.name}"
    notices = Notices()
    database = adapter(address_of(empty_database, port=port), tmp_path / "versions", notices)
    started = time.monotonic()
    try:
        problem = await database.startup_problem()
    finally:
        await database.close()
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
    _without_credentials(problem, empty_database)
    _without_credentials("\n".join(notices.lines), empty_database)


async def test_접속은_받되_답하지_않는_서버는_시간_안에_돌아온다(
    empty_database: ScopedDatabase, tmp_path: Path, silent_port: int
) -> None:
    place = f"{empty_database.address.url.host}:{silent_port}/{empty_database.name}"
    notices = Notices()
    database = adapter(address_of(empty_database, port=silent_port), tmp_path / "versions", notices)
    started = time.monotonic()
    try:
        async with asyncio.timeout(GENEROUS):
            problem = await database.startup_problem()
    finally:
        await database.close()
    assert time.monotonic() - started < GENEROUS
    assert problem == (
        f"데이터베이스({place})에 닿지 못했습니다. 0.6초 동안 다시 시도했습니다(TimeoutError)."
    )
    assert len(notices.lines) == 1
    _without_credentials(problem, empty_database)


async def test_판_기록_표가_잠겨_있으면_연결은_열려도_시간_안에_돌아온다(
    empty_database: ScopedDatabase, tmp_path: Path
) -> None:
    """시도 하나를 드라이버의 접속 인자로만 걸면 이 사례는 잠금이 풀릴 때까지 돌아오지 않는다."""
    versions = copy_versions(tmp_path / "versions", FIRST)
    setup = patient(empty_database.text(), versions, Notices())
    try:
        assert (await setup.migrate()).ok
    finally:
        await setup.close()
    database = adapter(empty_database.text(), versions, Notices())
    started = time.monotonic()
    try:
        async with plain(empty_database) as holder:
            await holder.execute(text("LOCK TABLE alembic_version IN ACCESS EXCLUSIVE MODE"))
            async with asyncio.timeout(GENEROUS):
                problem = await database.startup_problem()
            elapsed = time.monotonic() - started
            await holder.rollback()
        async with asyncio.timeout(GENEROUS):
            await database.close()
    finally:
        await database.close()
    assert elapsed < GENEROUS
    assert problem == (
        f"데이터베이스({empty_database.place})에 닿지 못했습니다. 0.6초 동안 다시 시도했습니다"
        "(TimeoutError)."
    )
    _without_credentials(problem, empty_database)
    assert await other_connections(empty_database) == 0


# --- 예외를 글로 바꾸는 것: 예외의 글을 싣지 않고 까닭만 싣는다 ----------------------------------


async def test_뜻밖의_예외의_글은_예외의_글을_싣지_않고_까닭만_싣는다(
    empty_database: ScopedDatabase, tmp_path: Path
) -> None:
    database = patient(empty_database.text(), tmp_path / "versions", Notices())
    try:
        message = database.unexpected_problem(RuntimeError(f"비밀번호 {SECRET} 가 섞인 글"))
    finally:
        await database.close()
    assert message == (
        f"데이터베이스({empty_database.place})를 확인하다 뜻밖의 오류로 멈췄습니다(RuntimeError).\n"
        "  이 판의 결함일 수 있습니다. 예외의 글과 역추적은 비밀번호가 섞일 수 있어 찍지 않습니다."
    )
    assert SECRET not in message


async def test_닫기가_실패했을_때의_글은_예외의_글을_싣지_않고_까닭만_싣는다(
    empty_database: ScopedDatabase, tmp_path: Path
) -> None:
    database = patient(empty_database.text(), tmp_path / "versions", Notices())
    try:
        message = database.close_problem(RuntimeError(f"비밀번호 {SECRET} 가 섞인 글"))
    finally:
        await database.close()
    assert message == (
        f"데이터베이스({empty_database.place})의 연결을 닫다 오류가 났습니다(RuntimeError)."
    )
    assert SECRET not in message
