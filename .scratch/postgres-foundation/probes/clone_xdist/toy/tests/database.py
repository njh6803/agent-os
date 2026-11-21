"""두 패키지의 시험이 함께 쓰는 테스트 데이터베이스 도우미(장난감).

어느 패키지도 import 하지 않는다. 패키지마다 다른 것 둘, 곧 마이그레이션을 적용하는 함수와
데이터베이스 이름의 접두는 인자로 받는다. 맡는 일은 셋이다.

1. `database_problem`: 환경 변수의 연결 문자열로 서버가 답하는지 보고, 문제가 있으면 한 줄 문구를
   돌려준다. `database_url` 픽스처가 그 문구로 실패한다(skip 이 아니다).
2. `template_database` 픽스처(세션 범위, 곧 xdist 작업자마다 한 번): 템플릿 데이터베이스를 만들고
   마이그레이션을 한 번 올린다. 세션이 끝나면 지운다.
3. `database` 픽스처(시험마다): 템플릿을 복제하고 시험이 끝나면 지운다(`DROP DATABASE … WITH
   (FORCE)`).

이름은 `<접두>_template_<uuid4 hex>` 와 `<접두>_test_<uuid4 hex>` 다. 테스트 서버 하나를 워크트리와
세션이 함께 쓰므로 무작위 토막으로 겹치지 않게 한다.

동기 드라이버가 없어(asyncpg 뿐이다) 세션 범위 픽스처를 짓는 길이 둘이다. `SESSION_STYLE` 이 고른다.
- `sync_run`: 동기 픽스처가 `asyncio.run` 으로 코루틴을 돈다.
- `session_loop`: `loop_scope="session"` 인 비동기 픽스처가 pytest-asyncio 의 세션 루프에서 돈다.
시험마다의 픽스처는 어느 쪽이든 그 시험의 루프에서 도는 비동기 픽스처다.

측정용으로만 있는 것이 셋이다. 실제 도우미에는 없을 것이다.
- `SESSION_STYLE`, `VARIANT` 를 환경 변수로 바꾸는 것. `VARIANT` 는 `template`(기본), `file_copy`
  (복제 전략만 다르다), `migrate_each`(템플릿 없이 시험마다 빈 데이터베이스에 마이그레이션)다.
- `write_record`: 걸린 시간과 본 것을 작업자별 JSONL 파일에 남긴다.
- `Database.record`: 시험이 자기가 잰 것을 얹는 자리다.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import time
from collections.abc import AsyncGenerator, AsyncIterator, Callable, Iterator, Mapping
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import Connection, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine
from sqlalchemy.pool import NullPool

URL_ENV = "TOY_TEST_DATABASE_URL"
RECORDS_ENV = "CLONE_PROBE_RECORDS"
VARIANT_ENV = "CLONE_PROBE_VARIANT"
STYLE_ENV = "CLONE_PROBE_SESSION_STYLE"
START_HINT = "띄우는 명령: docker compose -f compose.test.yml up -d --wait"
CONNECT_TIMEOUT_SECONDS = 5

VARIANT = os.environ.get(VARIANT_ENV, "template")
SESSION_STYLE = os.environ.get(STYLE_ENV, "sync_run")
VARIANTS = ("template", "file_copy", "migrate_each")
SESSION_STYLES = ("sync_run", "session_loop")

type Migrate = Callable[[Connection], None]

_NAME = re.compile(r"[a-z][a-z0-9_]*")


@dataclass
class Database:
    """시험 하나가 받는 데이터베이스. `record` 는 측정용이다."""

    url: str
    name: str
    record: dict[str, object] = field(default_factory=dict[str, object])


def write_record(record: Mapping[str, object]) -> None:
    """측정용. `RECORDS_ENV` 폴더의 작업자별 파일에 한 줄을 덧붙인다. 폴더가 없으면 하지 않는다."""
    folder = os.environ.get(RECORDS_ENV)
    if not folder:
        return
    worker = os.environ.get("PYTEST_XDIST_WORKER", "main")
    line = json.dumps({"worker": worker, "pid": os.getpid(), **record}, ensure_ascii=False)
    with (Path(folder) / f"{worker}.jsonl").open("a", encoding="utf-8") as out:
        out.write(line + "\n")


def _checked(name: str) -> str:
    """식별자로 끼워 넣을 이름. 소문자, 숫자, 밑줄만 받는다."""
    if _NAME.fullmatch(name) is None:
        raise ValueError(f"데이터베이스 이름으로 쓸 수 없다: {name!r}")
    return name


def url_for(url: str, database: str) -> str:
    """같은 서버의 다른 데이터베이스를 가리키는 연결 문자열."""
    return make_url(url).set(database=database).render_as_string(hide_password=False)


@asynccontextmanager
async def admin_connection(url: str) -> AsyncGenerator[AsyncConnection]:
    """`CREATE DATABASE` 와 `DROP DATABASE` 를 칠 연결. 트랜잭션 밖에서 쳐야 해서 자동 커밋이다.
    연결을 묶어 두지 않는다(`NullPool`). 묶인 연결은 만든 루프에 매이고 시험마다 루프가 다르다."""
    engine = create_async_engine(
        url,
        poolclass=NullPool,
        isolation_level="AUTOCOMMIT",
        connect_args={"timeout": CONNECT_TIMEOUT_SECONDS},
    )
    try:
        async with engine.connect() as connection:
            yield connection
    finally:
        await engine.dispose()


async def database_problem(environ: Mapping[str, str]) -> str | None:
    """테스트 서버를 쓸 수 없는 까닭 한 줄. 쓸 수 있으면 None 이다."""
    url = environ.get(URL_ENV, "")
    if not url:
        return f"{URL_ENV} 가 비어 있다. {START_HINT}"
    try:
        async with admin_connection(url) as connection:
            await connection.execute(text("SELECT 1"))
    except (OSError, SQLAlchemyError, TimeoutError) as error:
        reason = " ".join(str(error).split())[:200]
        return f"테스트 PostgreSQL 이 답하지 않는다({type(error).__name__}: {reason}). {START_HINT}"
    return None


async def create_database(
    url: str, name: str, *, template: str | None = None, strategy: str | None = None
) -> float:
    """데이터베이스를 만들고 `CREATE DATABASE` 문 하나에 든 초를 낸다."""
    statement = f'CREATE DATABASE "{_checked(name)}"'
    if template is not None:
        statement += f' TEMPLATE "{_checked(template)}"'
    if strategy is not None:
        statement += f" STRATEGY = {strategy}"
    async with admin_connection(url) as connection:
        started = time.perf_counter()
        await connection.execute(text(statement))
        return time.perf_counter() - started


async def drop_database(url: str, name: str) -> float:
    """데이터베이스를 지우고 `DROP DATABASE` 문 하나에 든 초를 낸다. 남은 연결은 끊는다."""
    statement = f'DROP DATABASE IF EXISTS "{_checked(name)}" WITH (FORCE)'
    async with admin_connection(url) as connection:
        started = time.perf_counter()
        await connection.execute(text(statement))
        return time.perf_counter() - started


async def apply_migrations(url: str, migrate: Migrate) -> None:
    """패키지가 준 함수로 마이그레이션을 올린다. 트랜잭션은 여기서 열고 닫는다(커밋)."""
    engine = create_async_engine(url, poolclass=NullPool)
    try:
        async with engine.begin() as connection:
            await connection.run_sync(migrate)
    finally:
        await engine.dispose()


async def describe(url: str) -> dict[str, object]:
    """측정용. 새 연결로 본 표 이름, 표의 판, 데이터베이스 크기."""
    engine = create_async_engine(url, poolclass=NullPool)
    try:
        async with engine.connect() as connection:
            tables = await connection.execute(
                text("SELECT tablename FROM pg_tables WHERE schemaname = 'public' ORDER BY 1")
            )
            names = [str(row[0]) for row in tables]
            version = None
            if "alembic_version" in names:
                found = await connection.execute(text("SELECT version_num FROM alembic_version"))
                version = ",".join(str(row[0]) for row in found)
            size = await connection.execute(text("SELECT pg_database_size(current_database())"))
            return {"tables": names, "version": version, "size_bytes": size.scalar_one()}
    finally:
        await engine.dispose()


async def build_template(url: str, prefix: str, migrate: Migrate) -> str:
    """템플릿 데이터베이스를 만들고 마이그레이션을 올린 뒤 그 이름을 낸다."""
    name = f"{_checked(prefix)}_template_{uuid4().hex}"
    started = time.perf_counter()
    create_sql = await create_database(url, name)
    try:
        migrate_started = time.perf_counter()
        await apply_migrations(url_for(url, name), migrate)
        migrate_seconds = time.perf_counter() - migrate_started
        build_seconds = time.perf_counter() - started
        seen = await describe(url_for(url, name))
    except BaseException:
        await drop_database(url, name)
        raise
    write_record(
        {
            "kind": "template",
            "package": prefix,
            "name": name,
            "style": SESSION_STYLE,
            "build_s": build_seconds,
            "create_sql_s": create_sql,
            "migrate_s": migrate_seconds,
            **seen,
        }
    )
    return name


async def drop_template(url: str, prefix: str, name: str) -> None:
    drop_sql = await drop_database(url, name)
    write_record({"kind": "template_drop", "package": prefix, "name": name, "drop_sql_s": drop_sql})


@asynccontextmanager
async def temporary_database(
    url: str, prefix: str, *, template: str | None, migrate: Migrate | None
) -> AsyncGenerator[Database]:
    """시험 하나의 데이터베이스. 템플릿이 있으면 복제하고, 없으면 비운 채 만들어 마이그레이션을
    올린다(대조 갈래). 끝나면 지우고 걸린 시간을 남긴다."""
    name = f"{_checked(prefix)}_test_{uuid4().hex}"
    strategy = "FILE_COPY" if VARIANT == "file_copy" and template is not None else None
    record: dict[str, object] = {
        "kind": "test",
        "package": prefix,
        "name": name,
        "template": template,
        "variant": VARIANT,
        "strategy": strategy,
    }
    started = time.perf_counter()
    record["create_sql_s"] = await create_database(url, name, template=template, strategy=strategy)
    try:
        if migrate is not None:
            migrate_started = time.perf_counter()
            await apply_migrations(url_for(url, name), migrate)
            record["migrate_s"] = time.perf_counter() - migrate_started
        record["prepare_s"] = time.perf_counter() - started
        yield Database(url=url_for(url, name), name=name, record=record)
    finally:
        drop_started = time.perf_counter()
        record["drop_sql_s"] = await drop_database(url, name)
        record["drop_s"] = time.perf_counter() - drop_started
        write_record(record)


def _url_or_fail(problem: str | None) -> str:
    if problem is not None:
        pytest.fail(problem, pytrace=False)
    return os.environ[URL_ENV]


def _check_switches() -> None:
    if VARIANT not in VARIANTS:
        raise pytest.UsageError(f"{VARIANT_ENV} 는 {VARIANTS} 가운데 하나다: {VARIANT!r}")
    if SESSION_STYLE not in SESSION_STYLES:
        raise pytest.UsageError(f"{STYLE_ENV} 는 {SESSION_STYLES} 가운데 하나다: {SESSION_STYLE!r}")


def database_url_fixture() -> object:
    """`database_url` 픽스처(세션 범위)를 지어 낸다. 뿌리 conftest 가 받는다. 서버를 쓸 수 없으면
    그 픽스처를 받는 시험이 모두 같은 한 줄로 실패한다."""
    _check_switches()
    if SESSION_STYLE == "session_loop":

        @pytest_asyncio.fixture(scope="session", loop_scope="session", name="database_url")
        async def looped() -> str:
            return _url_or_fail(await database_problem(os.environ))

        return looped

    @pytest.fixture(scope="session", name="database_url")
    def synced() -> str:
        return _url_or_fail(asyncio.run(database_problem(os.environ)))

    return synced


def template_fixture(prefix: str, migrate: Migrate) -> object:
    """`template_database` 픽스처(세션 범위)를 지어 낸다. 패키지의 conftest 가 받는다."""
    _check_switches()
    if SESSION_STYLE == "session_loop":

        @pytest_asyncio.fixture(scope="session", loop_scope="session", name="template_database")
        async def looped(database_url: str) -> AsyncIterator[str]:
            name = await build_template(database_url, prefix, migrate)
            try:
                yield name
            finally:
                await drop_template(database_url, prefix, name)

        return looped

    @pytest.fixture(scope="session", name="template_database")
    def synced(database_url: str) -> Iterator[str]:
        name = asyncio.run(build_template(database_url, prefix, migrate))
        try:
            yield name
        finally:
            asyncio.run(drop_template(database_url, prefix, name))

    return synced


def database_fixture(prefix: str, migrate: Migrate) -> object:
    """`database` 픽스처(시험마다)를 지어 낸다. 패키지의 conftest 가 받는다."""
    _check_switches()
    if VARIANT == "migrate_each":

        @pytest.fixture(name="database")
        async def migrated(database_url: str) -> AsyncIterator[Database]:
            async with temporary_database(
                database_url, prefix, template=None, migrate=migrate
            ) as database:
                yield database

        return migrated

    @pytest.fixture(name="database")
    async def cloned(database_url: str, template_database: str) -> AsyncIterator[Database]:
        async with temporary_database(
            database_url, prefix, template=template_database, migrate=None
        ) as database:
            yield database

    return cloned
