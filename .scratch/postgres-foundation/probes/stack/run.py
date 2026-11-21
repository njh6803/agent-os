"""postgres-foundation 명세의 시제품 프로브. ADR 0066 이 명세에 넘긴 어림을 시제품으로 잰다.

재는 것(섹션 이름).
- `types`: asyncpg-stubs 없는 환경에서 시제품(`proto/`)이 pyright strict 를 지나는지, 포트를 import
  하지 않는 어댑터가 조립 자리에서 포트와 맞대지는지(어긋난 어댑터 둘이 양성 대조), 타입 우회가
  없는지.
- `migrate`: 표를 만들지 않고 `downgrade` 도 없는 첫 마이그레이션으로 판 기록 표에 줄이 남는지.
- `versions`: 표의 판 견줌 세 갈래(같다, 뒤처졌다, 모르는 더 새 판)와, alembic 이 모르는 번호를
  만났을 때 스스로 내는 것. 마이그레이션 폴더가 비었을 때 확인과 올리기가 무엇을 하는지, 일부러
  실패하는 마이그레이션이 판 기록 표의 줄과 만들다 만 표를 어떻게 남기는지.
- `errors`: 접속 실패가 어떤 예외로 오는지(거부, 이름 풀이, 틀린 비밀번호, 없는 데이터베이스,
  로그인을 막은 계정, 접속 규칙에 맞는 줄이 없는 접속), 시제품이 다시 시도할 것과 바로 멈출 것을
  가르는지, 늦게 뜬 서버에 다시 시도로 붙는지, 접속은 받되 답하지 않는 서버에서 다시 시도하는
  시간이 지켜지는지(시도마다의 제한 시간이 있고 없고).
- `url`: 비밀번호에 주소에서 뜻이 있는 글자가 들 때, 글자를 그대로 이어 붙인 주소를 SQLAlchemy 가
  어떻게 읽는지. compose 가 짓는 꼴의 주소에서 자리(호스트·포트·데이터베이스)를 다르게 읽는 것을
  시제품의 `parse_url` 이 모두, 그리고 그것만 거부하는지.
- `uvicorn`: 데이터베이스에 문제가 있을 때 uvicorn 이 무엇을 찍고 어떤 종료 코드로 끝나는지를 확인
  자리 둘(순수 ASGI 미들웨어, FastAPI 의 수명 함수)로 견준다. 글은 명세의 표처럼 두 줄이다. 꺼질 때
  연결 묶음을 닫는지도 본다.
- `preping`: PostgreSQL 이 다시 뜬 뒤 쉬던 연결을 쓸 때 `pool_pre_ping` 이 있고 없고의 차이.
- `window`: 강제로 죽인 PostgreSQL 이 복구하는 동안 접속이 어떤 오류 번호로 거절되는지(57P03).

못 보는 것. 실제 `agent_os` 패키지가 아니라 같은 모양의 시제품이다. 윈도 호스트에서 돌리고
PostgreSQL 만 컨테이너다. 리눅스에서 도는 `serve` 는 재지 않는다. 다시 돌리는 방법은 README.
"""

from __future__ import annotations

import argparse
import ast
import asyncio
import contextlib
import json
import os
import secrets
import socket
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from importlib import metadata
from pathlib import Path
from urllib.parse import quote

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))

import uvicorn  # noqa: E402
from proto.apps import gate_app  # noqa: E402
from proto.database import (  # noqa: E402
    AHEAD,
    BEHIND,
    DRIVER,
    VERSIONS,
    WAITING,
    Failure,
    PostgresDatabase,
    failure_kind,
    parse_url,
    sqlstate_of,
)
from sqlalchemy import text  # noqa: E402
from sqlalchemy.engine import URL, make_url  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine  # noqa: E402
from sqlalchemy.pool import NullPool  # noqa: E402
from tools.check_type_escapes import escapes_in  # noqa: E402
from tools.probe_kit import LineReader, Rounds, Slot  # noqa: E402

IMAGE = "postgres@sha256:b9f6b8ff03b62f3cfd9d9ba3fe56226a9991c79d3fb46fd46536263bf02be553"
ACCOUNT = "agent_os"
PASSWORD = "stack-probe-password"
VERSIONS_NEXT = HERE / "proto" / "versions_next"
VERSIONS_FAILING = HERE / "proto" / "versions_failing"
# `versions_failing/0002_broken.py` 가 던지는 예외의 글. 이 글이 오면 표를 만드는 문장까지 돌았다
BROKEN = "probe: 일부러 실패하는 마이그레이션"
TABLES_SQL = "select tablename from pg_tables where schemaname = 'public' order by 1"
VERSION_SQL = "select version_num from alembic_version"
SECTIONS = ("types", "migrate", "versions", "errors", "url", "uvicorn", "preping", "window")


def docker(*args: str, timeout: float = 120.0) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["docker", *args],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        check=False,
    )


def free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


@dataclass(frozen=True)
class Server:
    """이 프로브가 띄운 PostgreSQL 컨테이너 하나. 이름의 무작위 접미사가 이 실행의 표지다."""

    name: str
    port: int

    def url(self, database: str = ACCOUNT, password: str = PASSWORD) -> str:
        return f"postgresql://{ACCOUNT}:{password}@127.0.0.1:{self.port}/{database}"

    def psql(self, sql: str, database: str = ACCOUNT) -> subprocess.CompletedProcess[str]:
        """컨테이너 안의 로컬 소켓으로 붙는다. 호스트 쪽 접속과 다른 연결이라 커밋된 것만 보인다."""
        head = ("exec", self.name, "psql", "-U", ACCOUNT, "-d", database)
        return docker(*head, "-v", "ON_ERROR_STOP=1", "-Atc", sql)

    def rows(self, sql: str, database: str = ACCOUNT) -> list[str]:
        return self.psql(sql, database).stdout.split()

    def ready(self, seconds: float = 120.0) -> bool:
        """컨테이너 안의 TCP 와 호스트에 발행한 포트가 모두 답할 때까지 기다린다."""
        deadline = time.monotonic() + seconds
        check = ("exec", self.name, "pg_isready", "-h", "127.0.0.1", "-U", ACCOUNT, "-d", ACCOUNT)
        while time.monotonic() < deadline:
            if docker(*check, timeout=20).returncode == 0 and self._port_open():
                return True
            time.sleep(0.3)
        return False

    def _port_open(self) -> bool:
        try:
            with socket.create_connection(("127.0.0.1", self.port), timeout=1):
                return True
        except OSError:
            return False

    def new_database(self, label: str) -> str:
        name = f"probe_{label}_{secrets.token_hex(3)}"
        done = self.psql(f"create database {name}")
        if done.returncode != 0:
            raise RuntimeError(f"데이터베이스를 만들지 못했다: {done.stderr.strip()}")
        return name


def start_server(*server_args: str) -> Server:
    name = f"pgf-stack-{secrets.token_hex(4)}"
    port = free_port()
    environment = (
        ("-e", f"POSTGRES_USER={ACCOUNT}")
        + ("-e", f"POSTGRES_PASSWORD={PASSWORD}")
        + ("-e", f"POSTGRES_DB={ACCOUNT}")
    )
    publish = ("-p", f"127.0.0.1:{port}:5432")
    done = docker("run", "-d", "--name", name, *publish, *environment, IMAGE, *server_args)
    if done.returncode != 0:
        raise RuntimeError(f"컨테이너를 띄우지 못했다: {done.stderr.strip()}")
    server = Server(name, port)
    if not server.ready():
        remove_server(server)
        raise RuntimeError("PostgreSQL 이 제한 시간 안에 준비되지 않았다")
    return server


def remove_server(server: Server) -> None:
    """이 실행이 띄운 컨테이너만 지운다. 이름은 `start_server` 가 무작위로 지은 것이다."""
    docker("rm", "-f", "-v", server.name)


def settle(slot: Slot, *, seen: bool, result: str) -> None:
    """기대한 표지를 봤으면 측정으로, 못 봤으면 본 것을 까닭으로 적어 측정 아님으로 센다."""
    slot.mark(measured=seen, result=result if seen else f"표지 없음: {result}")


def behind(problem: str | None) -> bool:
    """표가 뒤처졌다는 두 줄 글인가. 둘째 줄은 판 번호를 든다."""
    return problem is not None and problem.startswith(f"{BEHIND}\n  표의 판은 ")


def ahead(problem: str | None) -> bool:
    """표가 더 새롭다는 두 줄 글인가."""
    return problem is not None and problem.startswith(f"{AHEAD}\n  표의 판은 ")


def database_for(url_text: str, **options: float | Path) -> PostgresDatabase:
    url = parse_url(url_text)
    if url is None:
        raise RuntimeError("프로브가 지은 주소를 시제품이 읽지 못했다")
    retry = options.get("retry_seconds", 5.0)
    versions = options.get("versions", VERSIONS)
    if not isinstance(retry, float) or not isinstance(versions, Path):
        raise TypeError("retry_seconds 는 실수, versions 는 경로다")
    return PostgresDatabase(url, versions=versions, retry_seconds=retry, retry_interval=0.5)


# ---------------------------------------------------------------- types


def pyright_diagnostics() -> tuple[int, list[tuple[str, str, str]]]:
    """(분석한 파일 수, [(파일의 상대 경로, 규칙, 문구)]) 를 낸다. 심각도가 error 인 것만 센다."""
    argv = [sys.executable, "-m", "pyright", "--outputjson", "-p", str(HERE)]
    done = subprocess.run(
        [*argv, "--pythonpath", sys.executable],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=600,
        check=False,
    )
    report = json.loads(done.stdout)
    found: list[tuple[str, str, str]] = []
    for item in report["generalDiagnostics"]:
        if item["severity"] != "error":
            continue
        relative = Path(str(item["file"])).resolve().relative_to(HERE).as_posix()
        found.append((relative, str(item.get("rule", "")), str(item["message"])))
    return int(report["summary"]["filesAnalyzed"]), found


def section_types(rounds: Rounds, notes: list[str]) -> None:
    with rounds.round("types: asyncpg-stubs 가 없는 환경") as slot:
        try:
            stubs = metadata.version("asyncpg-stubs")
        except metadata.PackageNotFoundError:
            stubs = "없음"
        versions = {name: metadata.version(name) for name in ("sqlalchemy", "asyncpg", "alembic")}
        notes.append(
            f"판: {versions}, asyncpg-stubs {stubs}, pyright {metadata.version('pyright')}"
        )
        settle(slot, seen=stubs == "없음", result=f"asyncpg-stubs {stubs}")
    analyzed, diagnostics = pyright_diagnostics()
    sources = sorted((HERE / "proto").rglob("*.py"))
    with rounds.round("types: 시제품의 pyright strict") as slot:
        errors = [item for item in diagnostics if item[0].startswith("proto/")]
        notes.extend(f"시제품의 오류: {item}" for item in errors)
        seen = analyzed >= len(sources) and not errors
        settle(slot, seen=seen, result=f"파일 {analyzed}개 분석, proto 오류 {len(errors)}")
    with rounds.round("types: 어긋난 어댑터 둘(양성 대조)") as slot:
        control = [item for item in diagnostics if item[0].startswith("control/")]
        notes.extend(f"대조의 오류: {item[1]}: {item[2].splitlines()[0]}" for item in control)
        rules = sorted(item[1] for item in control)
        seen = rules == ["reportArgumentType", "reportArgumentType"]
        settle(slot, seen=seen, result=f"control 오류 {rules}")
    with rounds.round("types: 타입 우회") as slot:
        escapes = [line for path in sources for line in escapes_in(path.read_text("utf-8"))]
        caught = escapes_in("from typing import Any\nvalue: Any = 1\n")
        settle(slot, seen=not escapes and bool(caught), result=f"우회 {len(escapes)}건")


# ---------------------------------------------------------------- migrate, versions


async def section_migrate(rounds: Rounds, server: Server) -> None:
    name = server.new_database("empty")
    database = database_for(server.url(name))
    with rounds.round("migrate: 빈 데이터베이스는 뒤처진 것으로 본다") as slot:
        problem = await database.startup_problem()
        seen = behind(problem) and server.rows(TABLES_SQL, name) == []
        settle(slot, seen=seen, result=f"문구 {problem!r}")
    with rounds.round("migrate: 표 없는 첫 마이그레이션이 판 기록 표에 줄을 남긴다") as slot:
        tree = ast.parse((VERSIONS / "0001_baseline.py").read_text("utf-8"))
        functions = [node.name for node in tree.body if isinstance(node, ast.FunctionDef)]
        outcome = await database.migrate()
        tables, rows = server.rows(TABLES_SQL, name), server.rows(VERSION_SQL, name)
        seen = functions == ["upgrade"] and outcome is None
        seen = seen and tables == ["alembic_version"] and rows == ["0001"]
        settle(slot, seen=seen, result=f"함수 {functions}, 표 {tables}, 줄 {rows}")
    with rounds.round("migrate: 올린 뒤에는 문제가 없다") as slot:
        problem = await database.startup_problem()
        settle(slot, seen=problem is None, result=f"문구 {problem!r}")
    with rounds.round("migrate: 다시 적용해도 그대로다") as slot:
        outcome = await database.migrate()
        rows = server.rows(VERSION_SQL, name)
        settle(slot, seen=outcome is None and rows == ["0001"], result=f"줄 {rows}")
    await database.close()


async def alembic_alone(database: PostgresDatabase) -> str:
    """시제품의 판정 없이 alembic 의 upgrade 만 부른다. 낸 예외의 이름과 문구를 돌려준다."""
    try:
        async with database.engine.begin() as connection:
            await connection.run_sync(database.raw_upgrade)
    except Exception as error:  # alembic 이 무엇을 내는지가 재는 것이다
        return f"{type(error).__module__}.{type(error).__qualname__}: {error}"
    return "예외 없음"


async def section_versions(rounds: Rounds, server: Server, notes: list[str]) -> None:
    name = server.new_database("versions")
    old = database_for(server.url(name))
    new = database_for(server.url(name), versions=VERSIONS_NEXT)
    await old.migrate()
    with rounds.round("versions: 아는 옛 번호는 뒤처진 것으로 본다") as slot:
        problem = await new.startup_problem()
        seen = behind(problem) and server.rows(VERSION_SQL, name) == ["0001"]
        settle(slot, seen=seen, result=f"문구 {problem!r}")
    with rounds.round("versions: 뒤처진 표를 올린다") as slot:
        outcome = await new.migrate()
        tables, rows = server.rows(TABLES_SQL, name), server.rows(VERSION_SQL, name)
        seen = outcome is None and rows == ["0002"] and "probe_marker" in tables
        settle(slot, seen=seen, result=f"표 {tables}, 줄 {rows}")
    with rounds.round("versions: 옛 판은 더 새 표를 만나면 멈춘다") as slot:
        problem = await old.startup_problem()
        settle(slot, seen=ahead(problem), result=f"문구 {problem!r}")
    with rounds.round("versions: 옛 판의 migrate 는 표를 건드리지 않는다") as slot:
        outcome = await old.migrate()
        tables, rows = server.rows(TABLES_SQL, name), server.rows(VERSION_SQL, name)
        seen = ahead(outcome) and rows == ["0002"] and "probe_marker" in tables
        settle(slot, seen=seen, result=f"문구 {outcome!r}, 줄 {rows}")
    with rounds.round("versions: alembic 이 모르는 번호에 스스로 내는 것") as slot:
        raised = await alembic_alone(old)
        notes.append(f"alembic 이 낸 것: {raised}")
        seen = "Can't locate revision" in raised and server.rows(VERSION_SQL, name) == ["0002"]
        settle(slot, seen=seen, result=raised.split(":")[0])
    await old.close()
    await new.close()
    await empty_folder_rounds(rounds, server, notes)
    await failing_migration_round(rounds, server)


async def empty_folder_rounds(rounds: Rounds, server: Server, notes: list[str]) -> None:
    """마이그레이션 파일이 하나도 없는 폴더. 제품의 첫 티켓이 빈 폴더로 들어오는 경우다.

    표지는 상황이 갖춰졌다는 것(폴더가 비었고 데이터베이스에 표가 없다)이고, 판정과 올리기의
    결과는 result 에 적어 읽는다. 같은 빈 데이터베이스를 파일 있는 폴더로 확인하면 뒤처졌다고
    나오는 것은 `migrate` 섹션의 첫 회차가 본다(양성 대조).
    """
    name = server.new_database("emptyfolder")
    with tempfile.TemporaryDirectory(prefix="pgf-empty-versions-") as folder:
        empty_folder = not any(Path(folder).iterdir())
        database = database_for(server.url(name), versions=Path(folder))
        with rounds.round("versions: 빈 마이그레이션 폴더로 빈 데이터베이스를 확인한다") as slot:
            bare = server.rows(TABLES_SQL, name) == []
            problem = await database.startup_problem()
            settle(slot, seen=empty_folder and bare, result=f"문구 {problem!r}")
        with rounds.round("versions: 빈 마이그레이션 폴더로 올린다") as slot:
            try:
                outcome = repr(await database.migrate())
            except Exception as error:  # 빈 폴더에서 alembic 이 무엇을 내는지가 재는 것이다
                outcome = f"예외 {type(error).__name__}: {error}"
            tables = server.rows(TABLES_SQL, name)
            rows = server.rows(VERSION_SQL, name) if "alembic_version" in tables else []
            notes.append(f"빈 폴더로 올린 결과: {outcome}, 표 {tables}, 줄 {rows}")
            settle(slot, seen=empty_folder, result=f"결과 {outcome}, 표 {tables}, 줄 {rows}")
        with rounds.round("versions: 빈 폴더로 올린 뒤 다시 확인한다") as slot:
            problem = await database.startup_problem()
            settle(slot, seen=empty_folder, result=f"문구 {problem!r}")
        await database.close()


async def failing_migration_round(rounds: Rounds, server: Server) -> None:
    """`0001` 까지 올린 데이터베이스에 표를 만들고 예외를 던지는 `0002` 를 올린다.

    표지는 그 마이그레이션이 던진 글(`BROKEN`)이다. 그 글이 오면 표를 만드는 문장이 돈 뒤다.
    판 기록 표의 줄과 만들다 만 표가 남았는지는 result 에 적어 읽는다.
    """
    name = server.new_database("failing")
    base = database_for(server.url(name))
    await base.migrate()
    await base.close()
    broken = database_for(server.url(name), versions=VERSIONS_FAILING)
    with rounds.round("versions: 실패한 마이그레이션 뒤의 판과 표") as slot:
        raised = ""
        try:
            await broken.migrate()
        except RuntimeError as error:
            raised = str(error)
        tables, rows = server.rows(TABLES_SQL, name), server.rows(VERSION_SQL, name)
        settle(slot, seen=raised == BROKEN, result=f"예외 {raised!r}, 표 {tables}, 줄 {rows}")
    await broken.close()


# ---------------------------------------------------------------- errors


async def raw_failure(url: URL) -> BaseException | None:
    """SQLAlchemy 로 붙어 질의 하나를 한다. 실패하면 그 예외를 돌려준다."""
    engine = create_async_engine(url, poolclass=NullPool)
    try:
        async with engine.connect() as connection:
            await connection.execute(text("select 1"))
    except Exception as error:  # 어떤 예외가 오는지가 재는 것이다
        return error
    finally:
        await engine.dispose()
    return None


def shape_of(error: BaseException | None) -> str:
    if error is None:
        return "성공"
    chain: list[str] = []
    current: BaseException | None = error
    while current is not None and len(chain) < 6:
        chain.append(f"{type(current).__module__}.{type(current).__qualname__}")
        current = current.__cause__ or current.__context__
    os_error = isinstance(error, OSError)
    return f"{' <- '.join(chain)} | OSError {os_error} | 오류 번호 {sqlstate_of(error)}"


def driver_url(url_text: str) -> URL:
    return make_url(url_text).set(drivername=DRIVER)


async def timed_problem(database: PostgresDatabase) -> tuple[str | None, float]:
    started = time.monotonic()
    problem = await database.startup_problem()
    return problem, time.monotonic() - started


async def section_errors(rounds: Rounds, server: Server, notes: list[str]) -> None:
    dead = f"postgresql://{ACCOUNT}:{PASSWORD}@127.0.0.1:{free_port()}/{ACCOUNT}"
    nowhere = f"postgresql://{ACCOUNT}:{PASSWORD}@pgf-no-such-host.invalid:5432/{ACCOUNT}"
    wrong = "wrong-password-marker"
    cases = (
        ("거부(듣는 포트 없음)", dead, Failure.TRANSIENT, None),
        ("이름 풀이 실패", nowhere, Failure.TRANSIENT, None),
        ("틀린 비밀번호", server.url(password=wrong), Failure.PASSWORD, "28P01"),
        ("없는 데이터베이스", server.url("no_such_database"), Failure.NO_DATABASE, "3D000"),
    )
    for label, url_text, kind, state in cases:
        with rounds.round(f"errors: {label}") as slot:
            error = await raw_failure(driver_url(url_text))
            notes.append(f"{label}: {shape_of(error)} | 문구 {str(error)[:120]!r}")
            seen = error is not None and failure_kind(error) is kind
            seen = seen and (state is None or sqlstate_of(error) == state)
            leaked = error is not None and (wrong in str(error) or PASSWORD in str(error))
            found = failure_kind(error).value if error is not None else "성공"
            settle(slot, seen=seen and not leaked, result=f"갈래 {found}, 비밀번호 노출 {leaked}")
    await nologin_round(rounds, server, notes)
    await no_hba_entry_rounds(rounds, notes)
    await retry_rounds(rounds, server, dead, wrong)
    await quiet_server_rounds(rounds)


def refusal(error: BaseException | None) -> str:
    if error is None:
        return "성공"
    return f"오류 번호 {sqlstate_of(error)}, 갈래 {failure_kind(error).value}"


async def nologin_round(rounds: Rounds, server: Server, notes: list[str]) -> None:
    """로그인을 막은 계정(`NOLOGIN`)으로 접속한다.

    명세 Testing Decisions 의 어댑터 사례가 28000 을 내는 길로 든 것이다.
    """
    role = f"probe_nologin_{secrets.token_hex(3)}"
    made = server.psql(f"create role {role} nologin password '{PASSWORD}'").returncode == 0
    url = f"postgresql://{role}:{PASSWORD}@127.0.0.1:{server.port}/{ACCOUNT}"
    with rounds.round("errors: 로그인을 막은 계정") as slot:
        error = await raw_failure(driver_url(url))
        notes.append(f"로그인을 막은 계정: {shape_of(error)} | 문구 {str(error)[:160]!r}")
        # 표지: 서버가 그 계정의 로그인을 막았다는 문구다. 비밀번호나 접속 규칙의 실패와 가른다
        seen = made and error is not None and "is not permitted to log in" in str(error)
        settle(slot, seen=seen, result=refusal(error))
    server.psql(f"drop role {role}")


async def no_hba_entry_rounds(rounds: Rounds, notes: list[str]) -> None:
    """접속 규칙(`pg_hba.conf`)에서 TCP 줄을 모두 지운 서버에 호스트에서 접속한다.

    처음 띄우기가 끊긴 볼륨에서 PostgreSQL 이 다른 컨테이너의 접속을 거절한 문구(`no pg_hba.conf
    entry`, restart_recover README 항목 4)와 같은 문구를 이 길이 낸다. 유닉스 소켓의 줄은 남겨
    컨테이너 안의 psql 로 설정을 다시 읽힌다. 다른 회차와 나누려고 서버를 따로 띄운다.
    """
    hba = await asyncio.to_thread(start_server)
    notices: list[str] = []
    try:
        cut = docker("exec", hba.name, "sh", "-c", 'sed -i "/^host/d" "$PGDATA/pg_hba.conf"')
        reloaded = hba.psql("select pg_reload_conf()").returncode == 0
        with rounds.round("errors: 접속 규칙에 맞는 줄이 없는 접속") as slot:
            error = await raw_failure(driver_url(hba.url()))
            notes.append(f"접속 규칙에 맞는 줄 없음: {shape_of(error)} | 문구 {str(error)[:160]!r}")
            # 표지: 거절의 까닭이 접속 규칙이라는 서버의 문구다
            seen = cut.returncode == 0 and reloaded and error is not None
            seen = seen and "no pg_hba.conf entry" in str(error)
            settle(slot, seen=seen, result=refusal(error))
        denied = PostgresDatabase(driver_url(hba.url()), retry_seconds=30.0, notice=notices.append)
        with rounds.round("errors: 접속을 허락하지 않으면 다시 시도하지 않고 바로 멈춘다") as slot:
            problem, elapsed = await timed_problem(denied)
            seen = problem is not None and "이 접속을 허락하지 않았습니다(" in problem
            seen = seen and elapsed < 5.0 and not notices and PASSWORD not in problem
            result = f"{elapsed:.1f}초, 알림 {len(notices)}줄, 문구 {problem!r}"
            settle(slot, seen=seen, result=result)
        await denied.close()
    finally:
        remove_server(hba)


async def quiet_server_rounds(rounds: Rounds) -> None:
    """접속은 받되 아무 답도 하지 않는 서버. 시도마다의 제한 시간이 있고 없고를 견준다."""
    release = asyncio.Event()

    async def hold(_: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        await release.wait()
        writer.close()

    listener = await asyncio.start_server(hold, "127.0.0.1", 0)
    port = int(listener.sockets[0].getsockname()[1])
    url = driver_url(f"postgresql://{ACCOUNT}:{PASSWORD}@127.0.0.1:{port}/{ACCOUNT}")
    notices: list[str] = []
    bounded = PostgresDatabase(
        url, retry_seconds=3.0, retry_interval=0.5, connect_timeout=1.0, notice=notices.append
    )
    with rounds.round("errors: 답하지 않는 서버에는 시도마다의 제한 시간으로 돌아온다") as slot:
        problem, elapsed = await timed_problem(bounded)
        seen = problem is not None and "닿지 못했습니다" in problem and 3.0 <= elapsed < 8.0
        settle(slot, seen=seen and len(notices) == 1, result=f"{elapsed:.1f}초, 문구 {problem!r}")
    await bounded.close()
    unbounded = PostgresDatabase(url, retry_seconds=3.0, connect_timeout=None, notice=print)
    with rounds.round("errors: 제한 시간이 없으면 정한 시간을 넘겨 기다린다(대조)") as slot:
        waiting = asyncio.create_task(timed_problem(unbounded))
        done, _ = await asyncio.wait({waiting}, timeout=10.0)
        waiting.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await waiting
        settle(slot, seen=not done, result="정한 3초를 넘겨 10초 뒤에도 기다리고 있었다")
    await unbounded.close()
    release.set()
    listener.close()
    await listener.wait_closed()


async def retry_rounds(rounds: Rounds, server: Server, dead: str, wrong: str) -> None:
    notices: list[str] = []
    refused = PostgresDatabase(
        driver_url(dead), retry_seconds=3.0, retry_interval=0.5, notice=notices.append
    )
    with rounds.round("errors: 거부는 정한 시간만큼 다시 시도한 뒤 멈춘다") as slot:
        problem, elapsed = await timed_problem(refused)
        seen = problem is not None and "닿지 못했습니다" in problem and 3.0 <= elapsed < 8.0
        seen = seen and len(notices) == 1 and WAITING in notices[0]
        settle(slot, seen=seen, result=f"{elapsed:.1f}초, 알림 {len(notices)}줄, 문구 {problem!r}")
    await refused.close()
    notices.clear()
    denied = PostgresDatabase(
        driver_url(server.url(password=wrong)), retry_seconds=30.0, notice=notices.append
    )
    with rounds.round("errors: 틀린 비밀번호는 다시 시도하지 않고 바로 멈춘다") as slot:
        problem, elapsed = await timed_problem(denied)
        seen = problem is not None and "받아들이지 않았습니다" in problem and elapsed < 5.0
        seen = seen and not notices and wrong not in problem
        settle(slot, seen=seen, result=f"{elapsed:.1f}초, 알림 {len(notices)}줄, 문구 {problem!r}")
    await denied.close()
    await late_server_round(rounds, server)


async def late_server_round(rounds: Rounds, server: Server) -> None:
    """서버를 멈춰 둔 채 확인을 시작하고 4초 뒤에 서버를 띄운다. 다시 시도가 붙는지 본다."""
    notices: list[str] = []
    late = PostgresDatabase(
        driver_url(server.url()), retry_seconds=90.0, retry_interval=0.5, notice=notices.append
    )
    with rounds.round("errors: 늦게 뜬 서버에 다시 시도로 붙는다") as slot:
        stopped = docker("stop", server.name).returncode == 0
        waiting = asyncio.create_task(timed_problem(late))
        await asyncio.sleep(4.0)
        still_waiting = not waiting.done()
        await asyncio.to_thread(docker, "start", server.name)
        problem, elapsed = await asyncio.wait_for(waiting, timeout=120)
        seen = stopped and still_waiting and behind(problem) and len(notices) == 1
        settle(slot, seen=seen, result=f"{elapsed:.1f}초 뒤 붙음, 문구 {problem!r}")
    await late.close()
    if not await asyncio.to_thread(server.ready):
        raise RuntimeError("다시 띄운 서버가 준비되지 않았다")


# ---------------------------------------------------------------- url

SAMPLES = (
    ("16진수 64자", "0f" * 32),
    ("골뱅이", "p@ss"),
    ("쌍점", "p:ss"),
    ("빗금", "p/ss"),
    ("셋 섞임", "p@s:s/w"),
    ("퍼센트와 16진수", "p%41ss"),
    ("퍼센트만", "p%ss"),
    ("물음표", "p?ss"),
    ("샵", "p#ss"),
    ("빈칸", "p ss"),
    ("더하기", "p+ss"),
    ("앰퍼샌드", "p&ss"),
    ("한글", "비밀번호"),
)


async def login(url: URL | None) -> str:
    if url is None:
        return "읽지 못함"
    error = await raw_failure(url)
    return "접속" if error is None else f"실패({failure_kind(error).value})"


def read_naive(naive: str, password: str) -> tuple[URL | None, str]:
    """글자를 그대로 이어 붙인 주소를 읽는다. (읽은 주소, 어떻게 읽혔는지) 를 낸다."""
    try:
        url = make_url(naive)
    except Exception as error:  # 어떤 예외로 거부하는지가 재는 것이다
        leaked = password in str(error) or naive in str(error)
        return None, f"거부 {type(error).__name__}, 문구에 값 노출 {leaked}"
    same = url.password == password and url.host == "127.0.0.1" and url.database == ACCOUNT
    return url.set(drivername=DRIVER), "같게 읽음" if same else f"다르게 읽음(host={url.host!r})"


# compose 가 `.env` 의 비밀번호로 짓는 주소의 꼴(명세 "연결 문자열과 비밀번호의 변수")
COMPOSE_FORM = "postgresql://agent_os:{password}@postgres:5432/agent_os"
# `@` 뒤의 글이 호스트가 아닌 자리로 흘러가는 비밀번호. 호스트만 보는 판정이 놓친다
PARSE_EXTRA = (
    ("골뱅이 뒤 빗금", "x@h/db"),
    ("골뱅이 뒤 물음표", "x@h?q=1"),
    ("골뱅이 뒤 쌍점과 빗금", "x@h:1/db"),
)


def misread(naive: str, password: str) -> tuple[str, str]:
    """compose 꼴의 주소를 SQLAlchemy 가 어떻게 읽는지. (갈래, 읽은 호스트) 를 낸다.

    갈래는 `자리`(호스트·포트·데이터베이스 가운데 하나가 다르다, 읽다 거부한 것도 든다),
    `비밀번호만`(자리는 같고 비밀번호만 다르다), `같다` 셋이다.
    """
    try:
        url = make_url(naive)
    except Exception:  # 읽다 거부하는 것도 자리를 잃은 갈래다
        return "자리", ""
    host = url.host or ""
    if (host, url.port, url.database) != ("postgres", 5432, ACCOUNT):
        return "자리", host
    return ("같다" if url.password == password else "비밀번호만"), host


def parse_rounds(rounds: Rounds, notes: list[str]) -> None:
    """주소를 읽지 못한 것으로 보는 판정(`parse_url`)이 자리를 다르게 읽는 주소를 모두, 그리고
    그것만 거부하는지. 서버 없이 읽기만 한다. 호스트에 `@` 가 드는지만 보던 판정이 놓치는 주소가
    있는지가 대조다."""
    old_missed: list[str] = []
    for label, password in (*SAMPLES, *PARSE_EXTRA):
        naive = COMPOSE_FORM.format(password=password)
        kind, host = misread(naive, password)
        refused = parse_url(naive) is None
        read = f"읽기 {kind}, 호스트 {host!r}, 거부 {refused}"
        notes.append(f"주소 판정 {label} {password!r}: {read}")
        with rounds.round(f"url 판정: {label}") as slot:
            # 표지: 자리를 다르게 읽은 주소이면 거부했고, 아니면 거부하지 않았다
            settle(slot, seen=refused == (kind == "자리"), result=f"읽기 {kind}, 거부 {refused}")
        if kind == "자리" and host and "@" not in host:
            old_missed.append(label)
    with rounds.round("url 판정: 호스트만 보는 판정이 놓치는 주소가 있다(대조)") as slot:
        settle(slot, seen=bool(old_missed), result=f"놓친 것 {old_missed}")


async def section_url(rounds: Rounds, server: Server, notes: list[str]) -> None:
    parse_rounds(rounds, notes)
    for label, password in SAMPLES:
        with rounds.round(f"url: {label}") as slot:
            escaped = password.replace("'", "''")
            changed = server.psql(f"alter role {ACCOUNT} password '{escaped}'").returncode == 0
            host, port = "127.0.0.1", server.port
            built = URL.create(DRIVER, ACCOUNT, password, host, port, ACCOUNT)
            control = await login(built)
            naive_url, reading = read_naive(server.url(password=password), password)
            naive = await login(naive_url)
            encoded = await login(driver_url(server.url(password=quote(password, safe=""))))
            notes.append(f"{label} {password!r}: {reading} / 그대로 {naive} / 인코딩 {encoded}")
            seen = changed and control == "접속" and encoded == "접속"
            settle(slot, seen=seen, result=f"그대로 이어 붙이면 {naive}")
    restored = server.psql(f"alter role {ACCOUNT} password '{PASSWORD}'")
    if restored.returncode != 0:
        raise RuntimeError("비밀번호를 되돌리지 못했다")


# ---------------------------------------------------------------- uvicorn


@dataclass
class StubRun:
    code: int | None
    lines: list[str] = field(default_factory=list[str])

    def has(self, fragment: str) -> bool:
        return any(fragment in line for line in self.lines)


def run_stub(url_text: str, variant: str, *, retry: float, expect_up: bool) -> StubRun:
    """`serve_stub.py` 를 띄운다. 뜨기를 기대하면 뜬 줄을 본 뒤 끄고, 아니면 끝나기를 기다린다."""
    env = {**os.environ, "PGF_URL": url_text, "PGF_VARIANT": variant, "PGF_RETRY": str(retry)}
    env["PYTHONUTF8"] = "1"
    process = subprocess.Popen(
        [sys.executable, str(HERE / "serve_stub.py")],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        env=env,
    )
    if process.stderr is None:
        raise RuntimeError("표준 오류를 붙잡지 못했다")
    reader = LineReader(process.stderr)
    lines: list[str] = []
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline and not reader.ended:
        line = reader.readline(deadline - time.monotonic())
        if line is None:
            continue
        lines.append(line.rstrip())
        if expect_up and "Uvicorn running on" in line:
            break
    if process.poll() is None:
        process.kill()
    code = process.wait(timeout=30)
    lines.extend(line.rstrip() for line in reader.drain(5))
    return StubRun(None if expect_up else code, lines)


class Recording:
    """부른 횟수를 세는 포장. 포트를 시그니처로 만족한다."""

    def __init__(self, inner: PostgresDatabase) -> None:
        self._inner = inner
        self.checked = 0
        self.closed = 0

    async def startup_problem(self) -> str | None:
        self.checked += 1
        return await self._inner.startup_problem()

    async def close(self) -> None:
        self.closed += 1
        await self._inner.close()


async def serve_and_stop(recording: Recording) -> bool:
    """같은 프로세스에서 uvicorn 을 띄워 뜬 것을 본 뒤 정상 종료시킨다. 떴으면 True 다."""
    config = uvicorn.Config(gate_app(recording), host="127.0.0.1", port=0, log_level="warning")
    server = uvicorn.Server(config)
    serving = asyncio.create_task(server.serve())
    deadline = time.monotonic() + 30
    while not server.started and not serving.done() and time.monotonic() < deadline:
        await asyncio.sleep(0.05)
    started = server.started
    server.should_exit = True
    await asyncio.wait_for(serving, timeout=30)
    return started


async def section_uvicorn(rounds: Rounds, server: Server, notes: list[str]) -> None:
    empty = server.url(server.new_database("uvicorn_empty"))
    ready_name = server.new_database("uvicorn_ready")
    ready = server.url(ready_name)
    preparing = database_for(ready)
    await preparing.migrate()
    await preparing.close()
    failed = "Application startup failed"
    second = "  표의 판은 없음이고 이 판의 마지막 판은 0001입니다."
    with rounds.round("uvicorn: 미들웨어가 확인하면 두 줄 글과 종료 코드 3") as slot:
        run = await asyncio.to_thread(run_stub, empty, "gate", retry=0.0, expect_up=False)
        notes.append(f"미들웨어 확인의 출력 {len(run.lines)}줄: {run.lines}")
        seen = run.has(BEHIND) and run.has(failed) and not run.has("Traceback") and run.code == 3
        alone = second in run.lines
        result = f"종료 코드 {run.code}, {len(run.lines)}줄, 둘째 줄이 그대로 한 줄 {alone}"
        settle(slot, seen=seen, result=result)
    with rounds.round("uvicorn: 수명 함수가 예외를 던지면 역추적이 함께 찍힌다") as slot:
        run = await asyncio.to_thread(run_stub, empty, "lifespan", retry=0.0, expect_up=False)
        notes.append(f"수명 함수 확인의 출력 {len(run.lines)}줄, 끝 세 줄: {run.lines[-3:]}")
        seen = run.has(BEHIND) and run.has(failed) and run.has("Traceback") and run.code == 3
        settle(slot, seen=seen, result=f"종료 코드 {run.code}, {len(run.lines)}줄, 역추적 있음")
    with rounds.round("uvicorn: 닿지 못하면 알림 한 줄 뒤에 멈춘다") as slot:
        dead = f"postgresql://{ACCOUNT}:{PASSWORD}@127.0.0.1:{free_port()}/{ACCOUNT}"
        # 윈도에서는 거부된 접속 한 번이 약 2초 걸린다. 알림은 첫 실패 뒤에도 시간이 남아야 찍힌다
        run = await asyncio.to_thread(run_stub, dead, "gate", retry=7.0, expect_up=False)
        notes.append(f"닿지 못할 때의 출력: {run.lines}")
        seen = run.has(WAITING) and run.has("닿지 못했습니다") and run.has(failed)
        settle(slot, seen=seen and run.code == 3, result=f"종료 코드 {run.code}")
    with rounds.round("uvicorn: 올린 데이터베이스면 뜬다(양성 대조)") as slot:
        run = await asyncio.to_thread(run_stub, ready, "gate", retry=0.0, expect_up=True)
        seen = run.has("Application startup complete") and run.has("Uvicorn running on")
        settle(slot, seen=seen, result="떴다")
    with rounds.round("uvicorn: 꺼질 때 연결 묶음을 한 번 닫는다") as slot:
        recording = Recording(database_for(ready))
        started = await serve_and_stop(recording)
        seen = started and recording.checked == 1 and recording.closed == 1
        settle(slot, seen=seen, result=f"확인 {recording.checked}번, 닫기 {recording.closed}번")


# ---------------------------------------------------------------- preping, window


async def select_one(database: PostgresDatabase) -> str:
    try:
        async with database.engine.connect() as connection:
            await connection.execute(text("select 1"))
    except Exception as error:  # 어떤 예외가 오는지가 재는 것이다
        return f"실패 {type(error).__name__}"
    return "성공"


async def section_preping(rounds: Rounds, server: Server) -> None:
    url = driver_url(server.url())
    checking = PostgresDatabase(url, retry_seconds=0.0, pre_ping=True)
    trusting = PostgresDatabase(url, retry_seconds=0.0, pre_ping=False)
    before = [await select_one(checking), await select_one(trusting)]
    restarted = (await asyncio.to_thread(docker, "restart", server.name)).returncode == 0
    if not await asyncio.to_thread(server.ready):
        raise RuntimeError("다시 띄운 서버가 준비되지 않았다")
    with rounds.round("preping: 쓰기 전에 확인하면 다시 뜬 서버에 바로 붙는다") as slot:
        after = await select_one(checking)
        seen = restarted and before == ["성공", "성공"] and after == "성공"
        settle(slot, seen=seen, result=f"다시 뜬 뒤 첫 질의 {after}")
    with rounds.round("preping: 확인하지 않으면 첫 질의가 죽은 연결로 실패한다(대조)") as slot:
        first, second = await select_one(trusting), await select_one(trusting)
        seen = restarted and first.startswith("실패") and second == "성공"
        settle(slot, seen=seen, result=f"첫 질의 {first}, 둘째 {second}")
    await checking.close()
    await trusting.close()


async def section_window(rounds: Rounds, notes: list[str]) -> None:
    """체크포인트를 미룬 서버에 줄을 많이 넣고 강제로 죽인 뒤, 복구하는 동안 접속을 되풀이한다."""
    server = await asyncio.to_thread(
        start_server, "-c", "checkpoint_timeout=1h", "-c", "max_wal_size=16GB"
    )
    try:
        with rounds.round("window: 복구 중의 접속은 57P03 으로 거절된다") as slot:
            fill = (
                "create table filler as select g, md5(g::text) from generate_series(1, 4000000) g"
            )
            filled = server.psql(fill).returncode == 0
            killed = docker("kill", "-s", "KILL", server.name).returncode == 0
            await asyncio.to_thread(docker, "start", server.name)
            shapes: dict[str, int] = {}
            url, deadline = driver_url(server.url()), time.monotonic() + 120
            while time.monotonic() < deadline:
                error = await raw_failure(url)
                if error is None:
                    break
                key = f"{failure_kind(error).value}/{sqlstate_of(error)}/{type(error).__name__}"
                shapes[key] = shapes.get(key, 0) + 1
            notes.append(f"복구 중에 본 실패: {shapes}")
            log = docker("logs", server.name).stderr
            recovered = "database system was interrupted" in log or "redo starts" in log
            starting = any(key.startswith("transient/57P03/") for key in shapes)
            others = [key for key in shapes if not key.startswith("transient/")]
            seen = filled and killed and recovered and starting and not others
            settle(slot, seen=seen, result=f"갈래 {sorted(shapes)}")
    finally:
        remove_server(server)


# ---------------------------------------------------------------- main


async def run_sections(chosen: list[str], rounds: Rounds, notes: list[str]) -> None:
    if "types" in chosen:
        section_types(rounds, notes)
    needs_server = {"migrate", "versions", "errors", "url", "uvicorn", "preping"}
    if needs_server & set(chosen):
        server = await asyncio.to_thread(start_server)
        try:
            await run_with_server(chosen, rounds, server, notes)
        finally:
            remove_server(server)
    if "window" in chosen:
        await section_window(rounds, notes)


async def run_with_server(
    chosen: list[str], rounds: Rounds, server: Server, notes: list[str]
) -> None:
    if "migrate" in chosen:
        await section_migrate(rounds, server)
    if "versions" in chosen:
        await section_versions(rounds, server, notes)
    if "errors" in chosen:
        await section_errors(rounds, server, notes)
    if "url" in chosen:
        await section_url(rounds, server, notes)
    if "uvicorn" in chosen:
        await section_uvicorn(rounds, server, notes)
    if "preping" in chosen:
        await section_preping(rounds, server)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sections", default=",".join(SECTIONS))
    chosen = [name for name in str(parser.parse_args().sections).split(",") if name]
    unknown = sorted(set(chosen) - set(SECTIONS))
    if unknown:
        parser.error(f"모르는 섹션: {unknown}")
    rounds, notes = Rounds(), list[str]()
    asyncio.run(run_sections(chosen, rounds, notes))
    for entry in rounds.entries:
        print(f"[{'측정' if entry.measured else '측정 아님'}] {entry.label} -> {entry.result}")
    print("--- 관찰")
    for note in notes:
        print(note)
    print("--- 셈")
    print(rounds.summary())
    return rounds.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
