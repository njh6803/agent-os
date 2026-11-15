"""admin-login pg_stack 프로브. PostgreSQL 을 쓰는 도구 조합을 고르는 데 쓸 사실을 잰다.

결정하지 않고 본 것만 낸다. 회차마다 재려는 상황이 그 회차에 났다는 표지를 보고
`tools/probe_kit.py` 의 `Rounds` 로 센다. 표지 없는 회차가 하나라도 있으면 종료 코드가 1 이다.
후보 패키지를 깐 환경의 파이썬으로 띄운다(README 의 다시 돌리기). 자식 프로세스는 모두 이 스크립트를
띄운 인터프리터(`sys.executable`)로 돈다.

항목(`--items types,windows` 로 고른다). 결과의 뜻은 README 의 결과 절이 적는다.
  types   이 폴더의 파이썬 파일을 pyright strict(저장소 잠금의 판)로 본다. 분석했다는 표지는
          `filesAnalyzed` 가 파일 수와 같은 것과 양성 대조 `control_checks.py` 의
          `reportMissingParameterType` 이다. 파일마다 오류 수를 내고, 기대한 오류의 대조군 둘
          (`friction_*.py`)은 그 규칙이 그 파일에 났는지를 표지로 본다. 같은 검사를
          `--pythonplatform Linux` 로 한 번 더 한다. 타입 우회 검사는 `tools/check_type_escapes.py`
          의 `escapes_in` 을 파일마다 부른다. 표지는 양성 대조에서 금지된 이름 둘과 억제 주석이
          나오는 것이다. `--nostubs-python` 을 주면 asyncpg-stubs 가 없는 환경으로 asyncpg 모듈을
          다시 본다. 표지는 그 환경에 없는 psycopg 의 가져오기가 풀리지 않았다는 오류다.
  migrate 표 관리 후보마다 새 데이터베이스에 적용한다. 표지는 표 둘과 색인 둘이 생긴 것이다.
          한 번 더 적용해 아무것도 하지 않는지 보고, SQL 러너는 둘을 함께 띄워 판이 한 번씩만
          적용되는지 본다.
  windows 이 PC 에서 조합을 돈다. `exercise.py` 를 기본 루프와 Selector 루프로, `loop_app.py` 를
          서버와 같은 `uvicorn.run` 호출과 Selector 루프로, `test_async_loop.py` 를 저장소 루트의
          pytest 설정으로. 조합 하나의 표지는 성공이면 서버 판과 실패 횟수 10, 실패면 오류 문구다.
          pytest 갈래의 표지는 머리의 `rootdir`·`configfile`·`asyncio: mode=Mode.AUTO` 다.
          가르는 갈래가 둘 더 있다. `loop_app.py` 의 `/mcp` 는 그 루프에서 stdio MCP 서버를 열고
          (표지는 도구 이름 `ping`), `pytest_selector/` 는 같은 시험을 루프 공장 훅으로 Selector
          루프에서 돈다.
  linux   `Dockerfile` 로 이미지를 짓고 그 컨테이너 안에서 같은 셋을 돈다. 표지는 위와 같고 플랫폼이
          `linux` 인 것을 더 본다.
  tc      testcontainers. `tc_start.py` 를 프로세스마다 한 번씩 띄워 시간을 재고(Ryuk 켬·끔),
          `tc_xdist/` 를 저장소의 pytest 설정으로 `-n` 없이 한 번, `-n <논리 CPU 의 절반>` 으로 한
          번 돈다. 표지는 테스트 서른둘이 통과한 것과 픽스처 기록이 있는 것이다.
  image   공식 이미지의 태그마다 크기(엔진이 보고하는 풀린 크기)와 `postgres --version` 을 본다.

자원. 만드는 컨테이너와 네트워크의 이름은 `admin-login-pg-probe-<토큰>-` 으로 시작하고 끝에서(예외가
나도) 그 접두로 찾아 지운다. 컨테이너는 익명 볼륨과 함께 지운다. testcontainers 가 띄우는 Ryuk
컨테이너만 이름이 `testcontainers-ryuk-<세션>` 이고 스스로 지워진다. 이미지는 남긴다. PostgreSQL 은
호스트의 `127.0.0.1` 임의 포트에만 연다. 비밀번호는 실행마다 무작위이고 명령줄과 원본 기록에 싣지
않는다(`-e 이름` 과 자식의 환경 변수로 넘긴다).

못 보는 것.
- GitHub Actions 의 service container. 이 PC 에서 띄울 수 없다.
- 리눅스 호스트의 testcontainers. 컨테이너 안에서는 Docker 소켓이 없어 돌리지 않았다.
- 다른 측정 세션이 같은 Docker 데몬을 쓴다. 시간은 범위로 읽는다.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import secrets
import subprocess
import sys
import tempfile
import time
from collections.abc import Generator, Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import psycopg
from psycopg import sql

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))

import migrate_alembic  # noqa: E402
import migrate_sql  # noqa: E402
import migrate_sql_asyncpg  # noqa: E402
import migrate_yoyo  # noqa: E402
from model import as_str  # noqa: E402
from tools.check_type_escapes import escapes_in  # noqa: E402
from tools.probe_kit import Rounds, Slot  # noqa: E402

PREFIX = "admin-login-pg-probe"
LINUX_IMAGE = f"{PREFIX}-linux"
PROBE_IN_IMAGE = "/app/.scratch/admin-login/probes/pg_stack"
PYTHON_IN_IMAGE = "/app/.venv/bin/python"
DSN_ENV = "PG_PROBE_DSN"
MIGRATIONS = HERE / "migrations"
TABLES = {"accounts", "refresh_tokens"}
INDEXES = {"accounts_locked_until", "refresh_tokens_account"}
SYNC_LABELS = ("psycopg-sync", "sqlalchemy-core-sync+psycopg")
ASYNC_LABELS = (
    "psycopg-async",
    "psycopg-async+pool",
    "asyncpg",
    "sqlalchemy-core-async+psycopg",
    "sqlalchemy-core-async+asyncpg",
)
CONTROL = "control_checks.py"
FRICTIONS = {
    "friction_asyncpg_pool.py": "reportArgumentType",
    "friction_psycopg_dynamic_sql.py": "reportArgumentType",
}
SELECTOR = "asyncio:SelectorEventLoop"

type Json = dict[str, Json] | list[Json] | str | int | float | bool | None

_raw: list[Path] = []


def raw(title: str, text: str) -> None:
    if _raw:
        with _raw[0].open("a", encoding="utf-8") as out:
            out.write(f"\n===== {time.strftime('%H:%M:%S')} {title}\n{text}\n")


def parse(text: str) -> Json:
    try:
        parsed: Json = json.loads(text)
    except ValueError:
        return None
    return parsed


def as_list(value: Json) -> list[Json]:
    return value if isinstance(value, list) else []


def as_text(value: Json) -> str:
    return value if isinstance(value, str) else ""


def dig(value: Json, *keys: str) -> Json:
    for key in keys:
        value = value.get(key) if isinstance(value, dict) else None
    return value


def results_in(text: str) -> list[Json]:
    """출력에서 `RESULT <json>` 줄을 모은다."""
    lines = [line.removeprefix("RESULT ") for line in text.splitlines() if "RESULT {" in line]
    return [parse(line) for line in lines]


@dataclass(frozen=True)
class Done:
    code: int
    out: str
    err: str
    seconds: float

    @property
    def text(self) -> str:
        return f"{self.out}\n{self.err}"


def run(
    argv: Sequence[str],
    *,
    env: Mapping[str, str] | None = None,
    cwd: Path | None = None,
    timeout: float = 300,
) -> Done:
    """명령 하나. 표준 입력은 닫힌 파이프다. 시간을 넘기면 종료 코드 -1 이다."""
    started = time.monotonic()
    try:
        completed = subprocess.run(
            list(argv),
            input="",
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
            env=None if env is None else dict(env),
            cwd=cwd,
        )
    except subprocess.TimeoutExpired:
        done = Done(
            -1, "", f"{timeout:.0f}초 안에 끝나지 않았다", round(time.monotonic() - started, 2)
        )
    else:
        seconds = round(time.monotonic() - started, 2)
        done = Done(completed.returncode, completed.stdout, completed.stderr, seconds)
    head = f"exit={done.code} seconds={done.seconds}"
    raw(" ".join(argv), f"{head}\n--- stdout\n{done.out}\n--- stderr\n{done.err}")
    return done


def docker(*args: str, env: Mapping[str, str] | None = None, timeout: float = 300) -> Done:
    return run(["docker", *args], env=env, timeout=timeout)


@dataclass
class Context:
    token: str
    rounds: Rounds
    pg_image: str
    major: str
    serial: int = 0

    def name(self, label: str) -> str:
        self.serial += 1
        return f"{PREFIX}-{self.token}-{label}-{self.serial}"


@contextmanager
def case(ctx: Context, label: str) -> Generator[Slot]:
    """회차 하나를 세고 끝나면 한 줄로 낸다."""
    with ctx.rounds.round(label) as slot:
        yield slot
    entry = ctx.rounds.entries[-1]
    verdict = "측정" if entry.measured else "측정 아님"
    print(f"- [{verdict}] {entry.label} => {entry.result}", flush=True)


# ---------------------------------------------------------------- PostgreSQL 컨테이너


@dataclass(frozen=True)
class Pg:
    """띄운 PostgreSQL 하나. 비밀번호는 원본 기록에 싣지 않는다."""

    name: str
    port: int
    password: str
    run_seconds: float = 0.0
    ready_seconds: float = 0.0

    def dsn(self, database: str = "probe", *, inside: bool = False) -> str:
        where = "pg:5432" if inside else f"127.0.0.1:{self.port}"
        return f"postgresql://probe:{self.password}@{where}/{database}"


def answers(dsn: str) -> bool:
    try:
        with psycopg.connect(dsn, connect_timeout=3) as conn:
            return conn.execute("SELECT 1").fetchone() == (1,)
    except psycopg.Error:
        return False


def start_pg(ctx: Context, network: str, label: str = "pg") -> Pg | None:
    """`docker run` 으로 띄워 첫 질의가 답할 때까지 기다린다. 네트워크가 빈 글이면 기본 다리망이다.

    `run_seconds` 는 `docker run -d` 가 돌아오기까지, `ready_seconds` 는 그 명령을 치기 전부터 첫
    질의가 답하기까지다.
    """
    name = ctx.name(label)
    password = secrets.token_hex(16)
    env = {**os.environ, "POSTGRES_PASSWORD": password}
    options = ("-e", "POSTGRES_PASSWORD", "-e", "POSTGRES_USER=probe", "-e", "POSTGRES_DB=probe")
    net = ("--network", network, "--network-alias", "pg") if network else ()
    begin = time.monotonic()
    started = docker(
        "run", "-d", "--name", name, *options, *net, "-p", "127.0.0.1::5432", ctx.pg_image, env=env
    )
    if started.code != 0:
        return None
    mapped = docker("port", name, "5432").out.strip().splitlines()
    if not mapped or not mapped[0].rpartition(":")[2].isdigit():
        return None
    port = int(mapped[0].rpartition(":")[2])
    pg = Pg(name, port, password)
    while time.monotonic() - begin < 180:
        if answers(pg.dsn()):
            ready = round(time.monotonic() - begin, 2)
            print(f"PostgreSQL 준비: {name}, {ready}초", flush=True)
            return Pg(name, port, password, started.seconds, ready)
        time.sleep(0.2)
    return None


def create_database(pg: Pg, database: str) -> str:
    with psycopg.connect(pg.dsn(), autocommit=True) as conn:
        conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(database)))
    return pg.dsn(database)


def names_in(dsn: str, query: sql.SQL) -> set[str]:
    with psycopg.connect(dsn) as conn:
        return {as_str(row[0]) for row in conn.execute(query)}


def schema_of(dsn: str) -> tuple[set[str], set[str]]:
    tables = names_in(dsn, sql.SQL("SELECT tablename FROM pg_tables WHERE schemaname = 'public'"))
    indexes = names_in(dsn, sql.SQL("SELECT indexname FROM pg_indexes WHERE schemaname = 'public'"))
    return tables, indexes


def sqlalchemy_url(dsn: str, driver: str) -> str:
    return dsn.replace("postgresql://", f"postgresql+{driver}://", 1)


def cleanup(token: str) -> None:
    """이 실행이 만든 컨테이너와 네트워크만 지운다. 이름 접두가 `<PREFIX>-<토큰>-` 인 것이다."""
    prefix = f"{PREFIX}-{token}-"
    listed = docker("ps", "-a", "--filter", f"name={prefix}", "--format", "{{.Names}}").out.split()
    containers = [name for name in listed if name.startswith(prefix)]
    if containers:
        docker("rm", "-f", "-v", *containers)
    listed = docker("network", "ls", "--filter", f"name={prefix}", "--format", "{{.Name}}")
    networks = [name for name in listed.out.split() if name.startswith(prefix)]
    if networks:
        docker("network", "rm", *networks)
    print(f"정리: 컨테이너 {len(containers)}, 네트워크 {len(networks)}", flush=True)


# ---------------------------------------------------------------- types


def typecheck(*extra: str) -> Json:
    done = run([sys.executable, str(HERE / "typecheck.py"), *extra], timeout=900)
    return parse(done.out)


def errors_by_file(report: Json) -> dict[str, list[str]]:
    """파일(이 폴더 기준 경로)마다 오류의 규칙 이름."""
    found: dict[str, list[str]] = {}
    for item in as_list(dig(report, "generalDiagnostics")):
        if dig(item, "severity") != "error":
            continue
        path = Path(as_text(dig(item, "file")))
        key = path.relative_to(HERE).as_posix() if path.is_relative_to(HERE) else path.name
        found.setdefault(key, []).append(as_text(dig(item, "rule")) or "(규칙 없음)")
    return found


def revealed(report: Json) -> list[str]:
    lines: list[str] = []
    for item in as_list(dig(report, "generalDiagnostics")):
        message = as_text(dig(item, "message"))
        if dig(item, "severity") == "information" and message.startswith("Type of"):
            lines.append(message.replace("\n", " "))
    return lines


def probe_files() -> list[str]:
    paths = [path for path in HERE.rglob("*.py") if "__pycache__" not in path.parts]
    return sorted(path.relative_to(HERE).as_posix() for path in paths)


def types_item(ctx: Context, nostubs_python: str) -> None:
    print("\n## types", flush=True)
    files = probe_files()
    reports = {
        "호스트 플랫폼": typecheck(),
        "pythonPlatform Linux": typecheck("--pythonplatform", "Linux"),
    }
    for label, report in reports.items():
        errors = errors_by_file(report)
        analyzed = dig(report, "summary", "filesAnalyzed")
        strict = "reportMissingParameterType" in errors.get(CONTROL, [])
        seen = analyzed == len(files) and strict
        with case(ctx, f"types pyright 분석 범위({label})") as slot:
            slot.mark(
                measured=seen,
                result=(
                    f"pyright {dig(report, 'version')}, filesAnalyzed {analyzed}/{len(files)}, "
                    f"양성 대조의 오류 {sorted(set(errors.get(CONTROL, [])))}"
                ),
            )
        for name in files:
            if name == CONTROL:
                continue
            rules = errors.get(name, [])
            expected = FRICTIONS.get(name)
            with case(ctx, f"types pyright {name}({label})") as slot:
                measured = seen and (expected is None or expected in rules)
                slot.mark(measured=measured, result=f"오류 {len(rules)} {sorted(set(rules))}")
    print("타입 드러내기(reveal.py, 호스트 플랫폼):", flush=True)
    for line in revealed(reports["호스트 플랫폼"]):
        print(f"  {line}", flush=True)
    control = escapes_in((HERE / CONTROL).read_text(encoding="utf-8"))
    listening = all(any(word in line for line in control) for word in ("`Any`", "`cast`", "억제"))
    with case(ctx, "types 타입 우회 검사의 양성 대조") as slot:
        slot.mark(measured=listening, result=f"{control}")
    for name in files:
        if name == CONTROL:
            continue
        found = escapes_in((HERE / name).read_text(encoding="utf-8"))
        with case(ctx, f"types 타입 우회 {name}") as slot:
            slot.mark(measured=listening, result=f"우회 {len(found)} {found}")
    if nostubs_python:
        report = typecheck("--interpreter", nostubs_python)
        errors = errors_by_file(report)
        other = "reportMissingImports" in errors.get("stack_psycopg_sync.py", [])
        for name in ("stack_asyncpg.py", "migrate_sql_asyncpg.py"):
            rules = errors.get(name, [])
            with case(ctx, f"types asyncpg-stubs 없이 {name}") as slot:
                slot.mark(
                    measured=other and "reportMissingImports" not in rules,
                    result=f"오류 {len(rules)} {sorted(set(rules))}",
                )


# ---------------------------------------------------------------- migrate


def state_text(dsn: str) -> tuple[bool, str]:
    tables, indexes = schema_of(dsn)
    return TABLES <= tables and INDEXES <= indexes, f"표 {sorted(tables)}, 색인 {sorted(indexes)}"


def migrate_item(ctx: Context, pg: Pg) -> None:
    print("\n## migrate", flush=True)
    dsn = create_database(pg, "mig_sql")
    with case(ctx, "migrate 번호 붙인 SQL + 러너(psycopg), 러너 둘을 함께") as slot:
        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(migrate_sql.apply, dsn, MIGRATIONS) for _ in range(2)]
            applied = [future.result() for future in futures]
        again = migrate_sql.apply(dsn, MIGRATIONS)
        made, text = state_text(dsn)
        once = sorted(applied[0] + applied[1]) == sorted(
            path.stem for path in MIGRATIONS.glob("*.sql")
        )
        slot.mark(
            measured=made,
            result=f"두 러너가 적용한 판 {applied}(한 번씩만 {once}), 다시 적용 {again}, {text}",
        )
    dsn = create_database(pg, "mig_sql_asyncpg")
    with case(ctx, "migrate 번호 붙인 SQL + 러너(asyncpg)") as slot:
        first = asyncio.run(migrate_sql_asyncpg.apply(dsn, MIGRATIONS))
        again = asyncio.run(migrate_sql_asyncpg.apply(dsn, MIGRATIONS))
        made, text = state_text(dsn)
        slot.mark(measured=made, result=f"적용한 판 {first}, 다시 적용 {again}, {text}")
    for database, env, driver in (
        ("mig_alembic_sync", "alembic_sync", "psycopg"),
        ("mig_alembic_async", "alembic_async", "asyncpg"),
    ):
        dsn = create_database(pg, database)
        with case(ctx, f"migrate Alembic {env}, 드라이버 {driver}") as slot:
            migrate_alembic.upgrade(sqlalchemy_url(dsn, driver), env)
            migrate_alembic.upgrade(sqlalchemy_url(dsn, driver), env)
            made, text = state_text(dsn)
            slot.mark(measured=made, result=f"upgrade head 두 번, {text}")
    dsn = create_database(pg, "mig_yoyo")
    with case(ctx, "migrate yoyo-migrations(같은 SQL 파일)") as slot:
        first_count = migrate_yoyo.apply(sqlalchemy_url(dsn, "psycopg"), MIGRATIONS)
        again_count = migrate_yoyo.apply(sqlalchemy_url(dsn, "psycopg"), MIGRATIONS)
        made, text = state_text(dsn)
        slot.mark(measured=made, result=f"적용 {first_count}개, 다시 적용 {again_count}개, {text}")


# ---------------------------------------------------------------- 조합을 돈 결과 읽기


def outcome_text(ctx: Context, item: Json) -> tuple[bool, str]:
    """조합 하나의 결과 줄. 성공의 표지는 서버 판과 실패 횟수 10, 실패의 표지는 오류 문구다."""
    loop = as_text(dig(item, "loop"))
    if dig(item, "ok") is True:
        version = as_text(dig(item, "server_version"))
        count = dig(item, "failed_attempts")
        seen = version.startswith(ctx.major) and count == 10
        return seen, f"성공, 루프 {loop}, 서버 {version}, 실패 횟수 {count}"
    error = as_text(dig(item, "error"))
    return bool(error), f"실패, 루프 {loop}, `{error}`"


def exercise_rounds(ctx: Context, where: str, labels: Sequence[str], items: Sequence[Json]) -> None:
    for label in labels:
        key = "label" if any(dig(item, "label") == label for item in items) else "stack"
        item = next((item for item in items if dig(item, key) == label), None)
        with case(ctx, f"{where} {label}") as slot:
            measured, result = outcome_text(ctx, item)
            slot.mark(measured=measured, result=result if item is not None else "결과 줄 없음")


def loop_rounds(ctx: Context, where: str, platform: str, items: Sequence[Json]) -> None:
    """`loop_client.py` 의 결과 줄을 회차로 옮긴다."""
    by_kind = {
        as_text(dig(item, "kind")): item for item in items if dig(item, "kind") != "exercise"
    }
    loop = as_text(dig(by_kind.get("loop"), "loop"))
    with case(ctx, f"{where} 서버의 이벤트 루프") as slot:
        seen = bool(loop) and dig(by_kind.get("loop"), "platform") == platform
        slot.mark(measured=seen, result=f"{loop}, 플랫폼 {dig(by_kind.get('loop'), 'platform')}")
    exercises = [item for item in items if dig(item, "kind") == "exercise"]
    exercise_rounds(ctx, where, (*SYNC_LABELS, *ASYNC_LABELS), exercises)
    child = by_kind.get("subprocess")
    with case(ctx, f"{where} 자식 프로세스 띄우기(anyio.run_process)") as slot:
        ok = dig(child, "ok")
        seen = (ok is True and dig(child, "stdout") == "child-ok") or (
            ok is False and "NotImplementedError" in as_text(dig(child, "error"))
        )
        shown = dig(child, "stdout") if ok is True else dig(child, "error")
        slot.mark(measured=seen, result=f"ok {ok}, 루프 {dig(child, 'loop')}, `{shown}`")
    opened = by_kind.get("mcp")
    with case(ctx, f"{where} stdio MCP 서버 열기(stdio_client)") as slot:
        ok = dig(opened, "ok")
        seen = (ok is True and dig(opened, "tools") == "ping") or (
            ok is False and bool(as_text(dig(opened, "error")))
        )
        shown = dig(opened, "tools") if ok is True else dig(opened, "error")
        slot.mark(measured=seen, result=f"ok {ok}, 루프 {dig(opened, 'loop')}, `{shown}`")
    with case(ctx, f"{where} 서버 끝내기(/shutdown)") as slot:
        code = dig(by_kind.get("shutdown"), "exit_code")
        slot.mark(measured="shutdown" in by_kind, result=f"종료 코드 {code}")


def pytest_rounds(ctx: Context, where: str, text: str, root: str, outcomes: Sequence[Json]) -> None:
    """pytest 한 번. 표지는 머리의 rootdir·configfile·asyncio 모드다."""
    head = [f"rootdir: {root}", "configfile: pyproject.toml", "asyncio: mode=Mode.AUTO"]
    configured = all(any(want in line for line in text.splitlines()) for want in head)
    summary = next(
        (line for line in reversed(text.splitlines()) if " in " in line and "=" in line), ""
    )
    with case(ctx, f"{where} pytest 설정과 집계") as slot:
        slot.mark(
            measured=configured, result=f"머리 표지 {configured}, 집계 `{summary.strip('= ')}`"
        )
    if configured:
        exercise_rounds(ctx, where, ASYNC_LABELS, outcomes)


# ---------------------------------------------------------------- windows


def child_env(dsn: str, **more: str) -> dict[str, str]:
    return {**os.environ, DSN_ENV: dsn, "PYTHONPATH": str(HERE), "PYTHONUTF8": "1", **more}


def windows_item(ctx: Context, dsn: str, work: Path) -> None:
    print("\n## windows", flush=True)
    env = child_env(dsn)
    done = run([sys.executable, str(HERE / "exercise.py")], env=env)
    exercise_rounds(
        ctx, "windows asyncio.run 기본 루프", (*SYNC_LABELS, *ASYNC_LABELS), results_in(done.out)
    )
    done = run([sys.executable, str(HERE / "exercise.py"), "--loop", "selector"], env=env)
    exercise_rounds(ctx, "windows asyncio.run Selector 루프", ASYNC_LABELS, results_in(done.out))
    done = run([sys.executable, str(HERE / "loop_client.py")], env=env)
    loop_rounds(ctx, "windows uvicorn.run(서버와 같은 호출)", sys.platform, results_in(done.out))
    done = run([sys.executable, str(HERE / "loop_client.py"), "--loop", SELECTOR], env=env)
    loop_rounds(ctx, f"windows uvicorn.run(loop={SELECTOR})", sys.platform, results_in(done.out))
    out = work / f"pytest-{ctx.token}.jsonl"
    argv = [sys.executable, "-m", "pytest", str(HERE / "test_async_loop.py"), "-rA"]
    done = run(
        [*argv, "-p", "no:cacheprovider"], env=child_env(dsn, PG_PROBE_OUT=str(out)), cwd=ROOT
    )
    lines = out.read_text(encoding="utf-8").splitlines() if out.exists() else []
    pytest_rounds(
        ctx, "windows pytest(저장소 설정)", done.text, str(ROOT), [parse(line) for line in lines]
    )
    out = work / f"pytest-selector-{ctx.token}.jsonl"
    argv = [sys.executable, "-m", "pytest", str(HERE / "pytest_selector"), "-rA"]
    done = run(
        [*argv, "-p", "no:cacheprovider"], env=child_env(dsn, PG_PROBE_OUT=str(out)), cwd=ROOT
    )
    lines = out.read_text(encoding="utf-8").splitlines() if out.exists() else []
    pytest_rounds(
        ctx,
        "windows pytest(저장소 설정 + 루프 공장 훅으로 Selector)",
        done.text,
        str(ROOT),
        [parse(line) for line in lines],
    )


# ---------------------------------------------------------------- linux


def linux_item(ctx: Context, pg: Pg, network: str, tree: Path) -> None:
    print("\n## linux", flush=True)
    context = ("--build-context", f"tree={tree}")
    built = docker(
        "build", "--progress", "plain", "-f", str(HERE / "Dockerfile"), *context,
        "-t", LINUX_IMAGE, str(HERE), timeout=1500,
    )  # fmt: skip
    with case(ctx, "linux 이미지 빌드") as slot:
        named = f"naming to docker.io/library/{LINUX_IMAGE}" in built.text
        slot.mark(measured=built.code == 0 and named, result=f"{built.seconds:.0f}초")
    if built.code != 0:
        return
    env = {**os.environ, DSN_ENV: pg.dsn("main", inside=True)}

    def inside(label: str, *command: str, timeout: float = 300) -> Done:
        head = ("run", "--rm", "--name", ctx.name(label), "--network", network, "-e", DSN_ENV)
        return docker(*head, "-w", "/app", LINUX_IMAGE, *command, env=env, timeout=timeout)

    done = inside("versions", PYTHON_IN_IMAGE, f"{PROBE_IN_IMAGE}/versions.py")
    print("리눅스 이미지의 패키지:", flush=True)
    for item in results_in(done.out):
        print(f"  {json.dumps(item, ensure_ascii=False)}", flush=True)
    done = inside("exercise", PYTHON_IN_IMAGE, f"{PROBE_IN_IMAGE}/exercise.py")
    exercise_rounds(
        ctx, "linux asyncio.run 기본 루프", (*SYNC_LABELS, *ASYNC_LABELS), results_in(done.out)
    )
    done = inside("loop", PYTHON_IN_IMAGE, f"{PROBE_IN_IMAGE}/loop_client.py")
    loop_rounds(ctx, "linux uvicorn.run(서버와 같은 호출)", "linux", results_in(done.out))
    script = (
        f"PG_PROBE_OUT=/tmp/out.jsonl {PYTHON_IN_IMAGE} -m pytest "
        f"{PROBE_IN_IMAGE}/test_async_loop.py -rA -p no:cacheprovider; "
        "echo PYTEST_EXIT=$?; cat /tmp/out.jsonl"
    )
    done = inside("pytest", "sh", "-c", script)
    outcomes = [parse(line) for line in done.out.splitlines() if line.startswith('{"stack"')]
    pytest_rounds(ctx, "linux pytest(저장소 설정의 사본)", done.text, "/app", outcomes)


# ---------------------------------------------------------------- tc


def host_load() -> str:
    """호스트 CPU 부하(윈도만). 시간을 읽을 때의 사정을 적으려는 것이고 회차로 세지 않는다."""
    if sys.platform != "win32":
        return "(윈도가 아니라 재지 않았다)"
    command = "(Get-CimInstance Win32_Processor).LoadPercentage"
    done = run(["powershell", "-NoProfile", "-Command", command], timeout=60)
    return f"{done.out.strip()}%" if done.code == 0 else "(읽지 못했다)"


def tc_item(ctx: Context, work: Path, rounds: int) -> None:
    print("\n## tc", flush=True)
    print(f"호스트 CPU 부하(시작): {host_load()}", flush=True)
    for index in range(rounds):
        # 대조: testcontainers 없이 같은 이미지를 `docker run` 으로 띄운다. 호스트 부하가 출렁여
        # 갈래를 번갈아 돈다.
        plain = start_pg(ctx, "", "plain")
        with case(ctx, f"tc 대조: docker run 으로 하나 띄우기 {index + 1}") as slot:
            if plain is not None:
                slot.mark(
                    measured=True,
                    result=(
                        f"docker run {plain.run_seconds}초, 첫 질의가 답하기까지 합계 "
                        f"{plain.ready_seconds}초"
                    ),
                )
        if plain is not None:
            docker("rm", "-f", "-v", plain.name)
        for label, disabled in (("Ryuk 켬(기본)", ""), ("Ryuk 끔", "true")):
            env = {**os.environ, "PYTHONPATH": str(HERE)}
            if disabled:
                env["TESTCONTAINERS_RYUK_DISABLED"] = disabled
            argv = [sys.executable, str(HERE / "tc_start.py"), ctx.pg_image, ctx.name("tc")]
            done = run(argv, env=env, timeout=300)
            found = results_in(done.out)
            item = found[0] if found else None
            with case(ctx, f"tc 컨테이너 하나 띄우기, {label} {index + 1}") as slot:
                version = as_text(dig(item, "server_version"))
                seen = version.startswith(ctx.major) and dig(item, "ryuk_disabled") is bool(
                    disabled
                )
                slot.mark(
                    measured=seen,
                    result=(
                        f"가져오기 {dig(item, 'import_seconds')}초, "
                        f"start() {dig(item, 'start_seconds')}초, "
                        f"첫 질의 {dig(item, 'first_query_seconds')}초, "
                        f"stop() {dig(item, 'stop_seconds')}초, 프로세스 전체 {done.seconds}초, "
                        f"Ryuk 컨테이너 {dig(item, 'ryuk_containers')}({dig(item, 'ryuk_image')})"
                    ),
                )
    workers = max(1, (os.cpu_count() or 1) // 2)
    for label, extra in (("-n 없음", ()), (f"-n {workers}", ("-n", str(workers)))):
        out = work / f"xdist-{ctx.token}-{len(extra)}.jsonl"
        env = {
            **os.environ,
            "PG_PROBE_IMAGE": ctx.pg_image,
            "PG_PROBE_OUT": str(out),
            "PG_PROBE_PREFIX": f"{PREFIX}-{ctx.token}-x{len(extra)}",
        }
        argv = [sys.executable, "-m", "pytest", str(HERE / "tc_xdist"), "-p", "no:cacheprovider"]
        done = run([*argv, *extra], env=env, cwd=ROOT, timeout=900)
        lines = out.read_text(encoding="utf-8").splitlines() if out.exists() else []
        records = [parse(line) for line in lines]
        with case(ctx, f"tc 세션 픽스처와 pytest {label}") as slot:
            containers = {as_text(dig(record, "container")) for record in records}
            pids = {str(dig(record, "pid")) for record in records}
            seconds = sorted(str(dig(record, "start_seconds")) for record in records)
            slot.mark(
                measured="32 passed" in done.out and bool(records),
                result=(
                    f"띄운 컨테이너 {len(containers)}개(프로세스 {len(pids)}개), 픽스처가 뜨는 데 "
                    f"{seconds}초, pytest 전체 {done.seconds}초"
                ),
            )
    print(f"호스트 CPU 부하(끝): {host_load()}", flush=True)


# ---------------------------------------------------------------- image


def image_item(ctx: Context, tags: Sequence[str]) -> None:
    print("\n## image", flush=True)
    for tag in tags:
        if docker("image", "inspect", "-f", "{{.Id}}", tag).code != 0:
            docker("pull", tag, timeout=900)
        size = docker("image", "inspect", "-f", "{{.Size}}", tag).out.strip()
        argv = ("run", "--rm", "--name", ctx.name("ver"), "--network", "none", tag)
        version = docker(*argv, "postgres", "--version").out.strip()
        with case(ctx, f"image {tag}") as slot:
            megabytes = round(int(size) / 1_000_000) if size.isdigit() else None
            slot.mark(
                measured=megabytes is not None and version.startswith("postgres (PostgreSQL)"),
                result=f"{megabytes}MB, `{version}`",
            )


# ---------------------------------------------------------------- 진입


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--items", default="types,migrate,windows,linux,tc,image")
    parser.add_argument("--tree", default="", help="후보를 더한 pyproject.toml 과 uv.lock 의 폴더")
    parser.add_argument("--nostubs-python", default="", help="asyncpg-stubs 가 없는 환경의 파이썬")
    parser.add_argument("--pg-image", default="postgres:18-alpine")
    parser.add_argument("--image-tags", default="postgres:18-alpine,postgres:18")
    parser.add_argument("--tc-rounds", type=int, default=3)
    parser.add_argument("--work", default="")
    args = parser.parse_args()
    items = {item for item in str(args.items).split(",") if item}
    pg_image: str = args.pg_image
    tc_rounds: int = args.tc_rounds
    work = Path(str(args.work) or tempfile.mkdtemp(prefix="pg-stack-"))
    work.mkdir(parents=True, exist_ok=True)
    token = secrets.token_hex(3)
    _raw.append(work / f"raw-{token}.log")
    major = pg_image.partition(":")[2].split("-")[0].split(".")[0]
    ctx = Context(token, Rounds(), pg_image, major)
    version = docker("version", "--format", "엔진 {{.Server.Version}} {{.Server.Os}}")
    print(f"실행 토큰 {token}, 원본 기록 {_raw[0]}", flush=True)
    print(
        f"{version.out.strip()}, 파이썬 {sys.version.split()[0]}, 호스트 {sys.platform}", flush=True
    )
    network = f"{PREFIX}-{token}-net"
    try:
        if "types" in items:
            types_item(ctx, str(args.nostubs_python))
        if items & {"migrate", "windows", "linux"}:
            docker("network", "create", network)
            pg = start_pg(ctx, network)
            if pg is None:
                ctx.rounds.record("PostgreSQL 준비", measured=False, result="띄우지 못했다")
            else:
                if "migrate" in items:
                    migrate_item(ctx, pg)
                main_dsn = create_database(pg, "main")
                migrate_sql.apply(main_dsn, MIGRATIONS)
                if "windows" in items:
                    windows_item(ctx, main_dsn, work)
                if "linux" in items:
                    linux_item(ctx, pg, network, Path(str(args.tree)))
        if "tc" in items:
            tc_item(ctx, work, tc_rounds)
        if "image" in items:
            image_item(ctx, [tag for tag in str(args.image_tags).split(",") if tag])
    finally:
        cleanup(token)
    print(f"\n{ctx.rounds.summary()}", flush=True)
    return ctx.rounds.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
