"""xdist 작업자들이 PostgreSQL 컨테이너 하나를 나눠 쓸 때 템플릿 복제가 시험 하나에 드는 시간과,
`tests/` 의 도우미 하나를 두 패키지의 시험이 함께 쓸 수 있는지를 잰다(ADR 0066 결정 "테스트
데이터베이스"와 "위젯 관리 서버"가 명세에 넘긴 둘).

하는 일. PostgreSQL 컨테이너 하나를 테스트 compose 와 같은 설정(tmpfs, fsync 끔)으로 띄우고, 장난감
시험 묶음 `toy/`(패키지 둘, 공용 도우미 하나, 시험 320 개)을 pytest 하위 프로세스로 갈래마다 돌린
뒤, 시험이 작업자별 JSONL 에 남긴 기록을 모아 셈하고, 자기가 띄운 컨테이너를 지운다. 인자 없이 돈다.

    uv run --project <tree> --no-sync python .scratch/postgres-foundation/probes/clone_xdist/run.py

갈래(회차).
- 정적: 도우미가 두 패키지를 import 하지 않는다(`ast` 와 새 인터프리터의 `sys.modules`).
- 컨테이너: 떠서 답하고, tmpfs 와 fsync 끔이 실제로 걸렸다.
- 서버 없음: 닫힌 포트를 주면 skip 이 아니라 도우미의 한 줄로 실패한다.
- `-n 8` 세 번(주 측정), `-n 1` 한 번(경합 없는 기준).
- 대조: 템플릿 없이 시험마다 빈 데이터베이스에 마이그레이션을 올린다(`-n 8`).
- 동시: pytest 실행 둘(`-n 4` 씩)이 같은 컨테이너를 함께 쓴다.
- `STRATEGY = FILE_COPY` 로 복제한다(`-n 8`).
- 세션 루프: 세션 범위 픽스처를 `loop_scope="session"` 비동기 픽스처로 바꾼다(`-n 8`).

회차의 표지. pytest 를 돈 회차는 아래가 모두 있어야 측정이다(`judge`). 하나라도 없으면 그 까닭을
적고 측정 아님으로 센다(`tools/probe_kit.py` 의 `Rounds`).
- pytest 머리의 `rootdir` 가 `toy/` 이고 `configfile: pyproject.toml`, `asyncio: mode=Mode.AUTO`,
  `<n> workers [<시험 수> items]` 다. 장난감의 설정과 xdist 가 실제로 걸렸다는 표지다.
- 요약 줄이 `<시험 수> passed` 이고 실패·오류·skip 이 없다.
- 시험 기록의 줄 수가 시험 수와 같고, 줄마다 잰 값이 다 있다.
- 서로 다른 작업자 id 가 `-n` 의 수와 같다.
- 템플릿 기록이 (작업자, 패키지)마다 하나이고, 시험 기록의 템플릿 이름이 그 작업자와 패키지의
  템플릿이다. 대조 갈래는 반대로 템플릿 기록이 없고 시험마다 마이그레이션 시간이 있다.
- 템플릿 기록에 적힌 세션 픽스처의 꼴(`style`)이 그 갈래가 고른 꼴이다.
- 패키지 A 의 데이터베이스에서 본 표가 A 의 표와 `alembic_version` 뿐이고 B 도 그렇다. 표의 판은
  `0001` 하나다(템플릿에 올린 마이그레이션이 커밋돼 복제본에 실렸다는 표지다. 시험은 마이그레이션을
  올리지 않는다).
- 실행이 끝난 뒤 `toy_` 로 시작하는 데이터베이스가 서버에 남지 않았다.
- FILE_COPY 갈래는 시험 하나에 쓰인 WAL 이 기본 전략(`-n 8` 주 측정)의 절반보다 적다. 기본 전략
  (WAL_LOG)은 복제한 블록을 WAL 에 적고 FILE_COPY 는 적지 않으므로, 전략이 실제로 바뀌었다는 표지다.

못 보는 것.
- 연결 수의 최댓값은 0.05초마다 뜬 표본의 최댓값이다. 표본 사이의 짧은 봉우리는 놓친다. 표본을 뜨는
  연결 하나가 그 수에 든다.
- 체크포인트 수(`pg_stat_checkpointer`)는 통계가 늦게 실려 실행 경계에서 어긋날 수 있다. 표지로 쓰지
  않고 적기만 한다.
- `ast` 는 글자로 적힌 import 만 본다. 그래서 새 인터프리터에서 도우미를 불러 `sys.modules` 도 본다.
- 시간은 이 PC 의 부하를 탄다. 실행마다 호스트 CPU 부하를 한 번 찍지만 회차로 세지 않는다.
- 벽시계 시간은 pytest 를 띄워 끝날 때까지다. 인터프리터 시작, xdist 작업자 띄우기, 수집이 든다.
  pytest 에 `--basetemp` 를 주므로, 저장소의 러너처럼 주지 않을 때 세션 끝에 드는 옛 임시 폴더
  지우기는 들지 않는다(`launch` 의 주석).
"""

from __future__ import annotations

import argparse
import ast
import asyncio
import json
import math
import os
import re
import secrets
import socket
import statistics
import subprocess
import sys
import tempfile
import threading
import time
from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import IO, TypeGuard

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))

from tools.probe_kit import Rounds, Slot  # noqa: E402

IMAGE = "postgres@sha256:b9f6b8ff03b62f3cfd9d9ba3fe56226a9991c79d3fb46fd46536263bf02be553"
ACCOUNT = "agent_os_test"
CONTAINER_PREFIX = "clone-xdist-probe"
SERVER_OPTIONS = ("fsync=off", "synchronous_commit=off", "full_page_writes=off")
TMPFS = "/var/lib/postgresql"
TOY = HERE / "toy"
HELPER = TOY / "tests" / "database.py"
URL_ENV = "TOY_TEST_DATABASE_URL"
RECORDS_ENV = "CLONE_PROBE_RECORDS"
VARIANT_ENV = "CLONE_PROBE_VARIANT"
STYLE_ENV = "CLONE_PROBE_SESSION_STYLE"
DUMP_ENV = "CLONE_PROBE_DUMP_AFTER"
PACKAGES = ("pkg_a", "pkg_b")
CASES = {"toy_a": 240, "toy_b": 80}
TABLES = {
    "toy_a": {"accounts", "refresh_tokens", "login_attempts", "alembic_version"},
    "toy_b": {"widgets", "widget_origins", "alembic_version"},
}
HEAD = "0001"
FAIL_MARK = "테스트 PostgreSQL 이 답하지 않는다("
BRANCHES = ("absent", "n8", "n1", "migrate-each", "pair", "file-copy", "session-loop")
START_HINT = "띄우는 명령: docker compose -f compose.test.yml up -d --wait"
PYTEST_TIMEOUT = 600
READY_TIMEOUT = 120
SAMPLE_EVERY = 0.05
TIMED = ("create_sql_s", "prepare_s", "first_query_s", "drop_sql_s", "drop_s")

type Record = dict[str, object]

_raw: list[Path] = []


def raw(title: str, body: str) -> None:
    """원본 출력을 실행 폴더의 `raw.log` 에 덧붙인다."""
    if _raw:
        with _raw[0].open("a", encoding="utf-8") as out:
            out.write(f"\n===== {time.strftime('%H:%M:%S')} {title}\n{body}\n")


def say(line: str) -> None:
    print(line, flush=True)
    raw("출력", line)


@dataclass(frozen=True)
class Done:
    code: int
    out: str
    err: str


def run(argv: Sequence[str], *, cwd: Path | None = None, timeout: float = 60) -> Done:
    """명령 하나. 시간을 넘기면 종료 코드 -1 이다."""
    try:
        completed = subprocess.run(
            list(argv),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
            cwd=cwd,
        )
    except subprocess.TimeoutExpired:
        done = Done(-1, "", f"{timeout:.0f}초 안에 끝나지 않았다")
    else:
        done = Done(completed.returncode, completed.stdout, completed.stderr)
    raw(" ".join(argv), f"exit={done.code}\n--- stdout\n{done.out}\n--- stderr\n{done.err}")
    return done


def docker(*args: str, timeout: float = 60) -> Done:
    return run(["docker", *args], timeout=timeout)


def host_load() -> str:
    """호스트 CPU 부하(윈도만). 시간을 읽을 때의 사정을 적으려는 것이고 회차로 세지 않는다."""
    if sys.platform != "win32":
        return "(윈도가 아니라 재지 않았다)"
    command = "(Get-CimInstance Win32_Processor).LoadPercentage"
    done = run(["powershell", "-NoProfile", "-Command", command], timeout=60)
    return f"{done.out.strip()}%" if done.code == 0 else "(읽지 못했다)"


# ---------------------------------------------------------------- 서버에 묻기


async def _fetch(url: str, statement: str) -> list[tuple[object, ...]]:
    engine = create_async_engine(
        url, poolclass=NullPool, isolation_level="AUTOCOMMIT", connect_args={"timeout": 10}
    )
    try:
        async with engine.connect() as connection:
            result = await connection.execute(text(statement))
            return [tuple(row) for row in result]
    finally:
        await engine.dispose()


def fetch(url: str, statement: str) -> list[tuple[object, ...]]:
    return asyncio.run(asyncio.wait_for(_fetch(url, statement), timeout=30))


def as_int(value: object) -> int:
    return int(value) if isinstance(value, (int, float)) else int(str(value))


def as_float(value: object) -> float | None:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def leftovers(url: str) -> list[str]:
    """이 프로브의 접두로 시작하는 데이터베이스 이름."""
    rows = fetch(url, "SELECT datname FROM pg_database WHERE starts_with(datname, 'toy_')")
    return sorted(str(row[0]) for row in rows)


@dataclass(frozen=True)
class Snapshot:
    """실행 앞뒤에서 뜨는 서버의 누적 값. WAL 은 바이트다."""

    wal: int
    requested: int
    timed: int


def snapshot(url: str) -> Snapshot:
    statement = (
        "SELECT pg_wal_lsn_diff(pg_current_wal_lsn(), '0/0'), num_requested, num_timed"
        " FROM pg_stat_checkpointer"
    )
    row = fetch(url, statement)[0]
    return Snapshot(as_int(row[0]), as_int(row[1]), as_int(row[2]))


class Sampler:
    """도는 동안 `pg_stat_activity` 를 되풀이해 읽어 최댓값을 잡는다. 표본이라 봉우리를 놓칠 수
    있다. `clients` 는 `backend_type = 'client backend'` 인 줄이고 표본을 뜨는 연결 하나가 든다."""

    def __init__(self, url: str) -> None:
        self._url = url
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._work, daemon=True)
        self.rows = 0
        self.clients = 0
        self.samples = 0
        self.error = ""

    def __enter__(self) -> Sampler:
        self._thread.start()
        return self

    def __exit__(self, *_: object) -> None:
        self._stop.set()
        self._thread.join(timeout=30)

    def _work(self) -> None:
        try:
            asyncio.run(self._sample())
        except (OSError, SQLAlchemyError, TimeoutError) as error:
            self.error = repr(error)

    async def _sample(self) -> None:
        statement = text(
            "SELECT count(*), count(*) FILTER (WHERE backend_type = 'client backend')"
            " FROM pg_stat_activity"
        )
        engine = create_async_engine(
            self._url,
            poolclass=NullPool,
            isolation_level="AUTOCOMMIT",
            connect_args={"timeout": 10},
        )
        try:
            async with engine.connect() as connection:
                while not self._stop.is_set():
                    row = (await connection.execute(statement)).one()
                    self.rows = max(self.rows, as_int(row[0]))
                    self.clients = max(self.clients, as_int(row[1]))
                    self.samples += 1
                    await asyncio.sleep(SAMPLE_EVERY)
        finally:
            await engine.dispose()


# ---------------------------------------------------------------- 컨테이너


@dataclass(frozen=True)
class Server:
    name: str
    port: int

    @property
    def url(self) -> str:
        return f"postgresql+asyncpg://{ACCOUNT}:{ACCOUNT}@127.0.0.1:{self.port}/{ACCOUNT}"


def start_server(name: str) -> Server:
    """테스트 compose 와 같은 설정으로 띄우고 `pg_isready` 가 답할 때까지 기다린다. 이미지는 받지
    않는다(`--pull never`). `-h` 가 없으면 초기화 중의 임시 서버가 유닉스 소켓으로 먼저 답한다."""
    options = [part for option in SERVER_OPTIONS for part in ("-c", option)]
    env = [
        part for key in ("USER", "PASSWORD", "DB") for part in ("-e", f"POSTGRES_{key}={ACCOUNT}")
    ]
    started = docker(
        "run", "-d", "--pull", "never", "--name", name, "--tmpfs", TMPFS, *env,
        "-p", "127.0.0.1::5432", IMAGE, "postgres", *options, timeout=120,
    )  # fmt: skip
    if started.code != 0:
        raise RuntimeError(f"docker run 실패: {started.err.strip()[:300]}")
    mapped = docker("port", name, "5432").out.strip().splitlines()
    if not mapped or not mapped[0].rpartition(":")[2].isdigit():
        raise RuntimeError(f"docker port 가 포트를 내지 않았다: {mapped}")
    server = Server(name, int(mapped[0].rpartition(":")[2]))
    ready = ("exec", name, "pg_isready", "-h", "127.0.0.1", "-U", ACCOUNT, "-d", ACCOUNT)
    deadline = time.monotonic() + READY_TIMEOUT
    while time.monotonic() < deadline:
        if docker(*ready, timeout=15).code == 0:
            return server
        time.sleep(0.3)
    raise RuntimeError(f"{READY_TIMEOUT}초 안에 pg_isready 가 답하지 않았다")


def remove_server(name: str) -> None:
    """이 실행이 띄운 컨테이너 하나만 지운다. 이름에 이 실행의 무작위 토막이 든다."""
    done = docker("rm", "-f", "-v", name, timeout=120)
    say(f"정리: docker rm {name} => 종료 코드 {done.code}")


def server_facts(server: Server) -> tuple[list[str], dict[str, str]]:
    """컨테이너가 재려는 설정으로 떴는지. 빠진 표지와 본 값을 낸다."""
    names = ("server_version", "fsync", "synchronous_commit", "full_page_writes", "max_connections")
    shown = ", ".join(f"current_setting('{name}')" for name in names)
    row = fetch(server.url, f"SELECT {shown}, pg_database_size('template1')")[0]
    facts = {name: str(value) for name, value in zip(names, row, strict=False)}
    facts["template1_bytes"] = str(row[len(names)])
    facts["tmpfs"] = docker("inspect", "-f", "{{json .HostConfig.Tmpfs}}", server.name).out.strip()
    facts["image"] = docker("inspect", "-f", "{{.Config.Image}}", server.name).out.strip()
    facts["engine"] = docker("version", "-f", "{{.Server.Version}}").out.strip()
    problems = [f"{name} 이 off 가 아니다" for name in names[1:4] if facts[name] != "off"]
    if not facts["server_version"].startswith("18"):
        problems.append(f"서버 판이 18 이 아니다: {facts['server_version']}")
    if TMPFS not in facts["tmpfs"]:
        problems.append(f"tmpfs 가 걸리지 않았다: {facts['tmpfs']}")
    return problems, facts


# ---------------------------------------------------------------- 정적 확인


def imports_of(path: Path) -> set[str]:
    """파일에 글자로 적힌 import 의 모듈 이름."""
    found: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            found.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            found.add("." * node.level + (node.module or ""))
    return found


def tops(modules: set[str]) -> set[str]:
    return {module.split(".")[0] for module in modules}


def loaded_packages(module: str) -> str:
    """새 인터프리터에서 모듈 하나를 불러 `sys.modules` 에 든 장난감 패키지를 찍게 한다."""
    code = (
        f"import sys, {module}; "
        f"print(sorted(n for n in sys.modules if n.split('.')[0] in {PACKAGES!r}))"
    )
    return run([sys.executable, "-c", code], cwd=TOY, timeout=120).out.strip()


def static_problems() -> tuple[list[str], str]:
    """도우미가 두 패키지를 import 하지 않고 두 패키지가 서로와 `tests` 를 import 하지 않는다.
    양성 대조는 패키지의 conftest 다. 거기서는 같은 읽기가 그 패키지의 import 를 본다."""
    problems: list[str] = []
    helper = imports_of(HELPER)
    if "sqlalchemy" not in tops(helper):
        problems.append(f"도우미의 import 를 읽지 못했다: {sorted(helper)}")
    if tops(helper) & set(PACKAGES):
        problems.append(f"도우미가 패키지를 import 한다: {sorted(helper)}")
    for package in PACKAGES:
        conftest = imports_of(TOY / "tests" / package / "conftest.py")
        if package not in tops(conftest) or "tests.database" not in conftest:
            problems.append(f"양성 대조가 서지 않았다. {package} 의 conftest: {sorted(conftest)}")
        files = sorted((TOY / package).rglob("*.py"))
        used: set[str] = set()
        for path in files:
            used |= tops(imports_of(path))
        other = set(PACKAGES) - {package} | {"tests"}
        if len(files) < 4 or used & other:
            problems.append(f"{package}: 파일 {len(files)}개, 금지된 import {sorted(used & other)}")
    alone = loaded_packages("tests.database")
    control = loaded_packages("tests.pkg_a.conftest")
    if alone != "[]" or "'pkg_a.database'" not in control or "pkg_b" in control:
        problems.append(f"sys.modules: 도우미만 {alone!r}, A 의 conftest {control!r}")
    seen = f"도우미의 import {sorted(tops(helper))}, sys.modules 도우미만 {alone}, 대조 {control}"
    return problems, seen


# ---------------------------------------------------------------- pytest 실행


@dataclass(frozen=True)
class Plan:
    label: str
    slug: str
    workers: int
    variant: str = "template"
    style: str = "sync_run"
    paths: tuple[str, ...] = ()


@dataclass
class Running:
    plan: Plan
    folder: Path
    output: Path
    handle: IO[bytes]
    process: subprocess.Popen[bytes]
    started: float


@dataclass
class Outcome:
    plan: Plan
    code: int | None
    seconds: float
    text: str
    records: list[Record]
    facts: dict[str, object] = field(default_factory=dict[str, object])


def launch(plan: Plan, url: str, work: Path) -> Running:
    folder = work / plan.slug
    folder.mkdir()
    env = {
        **os.environ,
        URL_ENV: url,
        RECORDS_ENV: str(folder),
        VARIANT_ENV: plan.variant,
        STYLE_ENV: plan.style,
        DUMP_ENV: str(PYTEST_TIMEOUT - 30),
        "PYTHONUTF8": "1",
    }
    for name in ("PYTEST_ADDOPTS", "PYTEST_PLUGINS", "PYTEST_XDIST_WORKER"):
        env.pop(name, None)
    config = str(TOY / "pyproject.toml")
    argv = [sys.executable, "-m", "pytest", "-n", str(plan.workers), "-p", "no:cacheprovider"]
    # basetemp 를 이 실행 폴더 안의 새 자리로 준다. 주지 않으면 pytest 9.1.1 은 세션 끝
    # (`pytest_sessionfinish`)에 같은 사용자의 `pytest-of-<사용자>` 아래 옛 `pytest-<번호>` 를 셋만
    # 남기고 지우는데(`_pytest/tmpdir.py` 315~340 줄을 읽었다), 그 폴더는 이 PC 의 다른 세션들이
    # 함께 쓴다. 그러면 벽시계 시간에 남의 폴더를 지우는 시간이 섞이고 남의 폴더를 건드린다.
    argv += ["--basetemp", str(work / f"{plan.slug}-basetemp")]
    argv += ["-c", config, "--rootdir", str(TOY), *plan.paths]
    output = work / f"{plan.slug}.out"
    handle = output.open("wb")
    raw(f"pytest 시작: {plan.label}", " ".join(argv))
    process = subprocess.Popen(
        argv, cwd=TOY, env=env, stdin=subprocess.DEVNULL, stdout=handle, stderr=subprocess.STDOUT
    )
    return Running(plan, folder, output, handle, process, time.monotonic())


def collect(running: Running) -> Outcome:
    """끝나기를 기다려 출력과 기록을 모은다. 시간을 넘기면 끄고 종료 코드를 None 으로 둔다."""
    code: int | None
    try:
        code = running.process.wait(timeout=PYTEST_TIMEOUT)
    except subprocess.TimeoutExpired:
        running.process.kill()
        running.process.wait(timeout=60)
        code = None
    seconds = time.monotonic() - running.started
    running.handle.close()
    records: list[Record] = []
    for path in sorted(running.folder.glob("*.jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            parsed: object = json.loads(line)
            if is_mapping(parsed):
                records.append({str(key): value for key, value in parsed.items()})
    body = running.output.read_text(encoding="utf-8", errors="replace")
    return Outcome(running.plan, code, seconds, body, records)


def summary_of(body: str) -> tuple[dict[str, int], float | None]:
    """pytest 의 마지막 요약 줄에서 갈래별 수와 pytest 가 적은 초."""
    counts: dict[str, int] = {}
    seconds: float | None = None
    for line in body.splitlines():
        found = re.fullmatch(r"=+ (.+) in ([\d.]+)s(?: \(.*\))? =+", line.strip())
        if found is not None:
            pairs = re.findall(r"(\d+) ([a-z]+)", found.group(1))
            counts = {name: int(count) for count, name in pairs}
            seconds = float(found.group(2))
    return counts, seconds


def header_problems(plan: Plan, body: str, items: int) -> list[str]:
    """장난감의 설정과 xdist 가 실제로 걸렸다는 표지."""
    lines = [line.strip() for line in body.splitlines()]
    roots = [line.removeprefix("rootdir: ") for line in lines if line.startswith("rootdir: ")]
    problems: list[str] = []
    if not roots or Path(roots[0]).resolve() != TOY.resolve():
        problems.append(f"rootdir 가 toy 가 아니다: {roots}")
    for mark in ("configfile: pyproject.toml", "asyncio: mode=Mode.AUTO"):
        if not any(mark in line for line in lines):
            problems.append(f"머리에 {mark!r} 가 없다")
    spawned = re.search(r"(\d+) workers? \[(\d+) items\]", body)
    if spawned is None or (int(spawned.group(1)), int(spawned.group(2))) != (plan.workers, items):
        problems.append(f"xdist 줄이 {plan.workers} workers [{items} items] 가 아니다")
    return problems


def spread(values: Sequence[float]) -> dict[str, float]:
    """밀리초로 낸 최소, 중앙값, 95번째 백분위(가까운 순위), 최대."""
    ordered = sorted(value * 1000 for value in values)
    p95 = ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)]
    picked = {
        "min": ordered[0],
        "median": statistics.median(ordered),
        "p95": p95,
        "max": ordered[-1],
    }
    return {name: round(value, 1) for name, value in picked.items()}


def timing_facts(tests: Sequence[Record]) -> tuple[list[str], dict[str, object]]:
    """시험 기록의 잰 값. 값이 빠진 줄이 있으면 그 수를 문제로 낸다."""
    columns: dict[str, list[float]] = {name: [] for name in (*TIMED, "migrate_s", "both_s")}
    missing = 0
    for record in tests:
        values = {name: as_float(record.get(name)) for name in (*TIMED, "migrate_s")}
        if any(values[name] is None for name in TIMED):
            missing += 1
            continue
        for name, value in values.items():
            if value is not None:
                columns[name].append(value)
        columns["both_s"].append((values["prepare_s"] or 0) + (values["drop_s"] or 0))
    facts: dict[str, object] = {name: spread(found) for name, found in columns.items() if found}
    return ([f"잰 값이 빠진 시험 기록 {missing}줄"] if missing else []), facts


def template_problems(plan: Plan, records: Sequence[Record]) -> tuple[list[str], int]:
    """템플릿이 (작업자, 패키지)마다 하나이고 시험이 그 템플릿에서 복제됐는가."""
    tests = [record for record in records if record.get("kind") == "test"]
    built = [record for record in records if record.get("kind") == "template"]
    used = {(record.get("worker"), record.get("package")) for record in tests}
    problems: list[str] = []
    if plan.variant == "migrate_each":
        if built or any(record.get("template") is not None for record in tests):
            problems.append(f"대조 갈래인데 템플릿 기록 {len(built)}줄이 있다")
        if any(as_float(record.get("migrate_s")) is None for record in tests):
            problems.append("대조 갈래인데 마이그레이션 시간이 없는 시험이 있다")
        return problems, len(built)
    owned = {(record.get("worker"), record.get("package")): record.get("name") for record in built}
    if len(built) != len(owned) or set(owned) != used:
        problems.append(f"템플릿 기록 {len(built)}줄, (작업자, 패키지) {len(used)}쌍")
    strays = [
        record
        for record in tests
        if record.get("template") != owned.get((record.get("worker"), record.get("package")))
    ]
    if strays:
        problems.append(f"자기 작업자의 템플릿이 아닌 데서 복제된 시험 {len(strays)}줄")
    wrong = [
        r for r in built if set(as_names(r.get("tables"))) != TABLES.get(str(r.get("package")))
    ]
    if wrong or any(record.get("version") != HEAD for record in built):
        problems.append(f"템플릿을 새 연결로 봤을 때 표나 판이 다르다: {len(wrong)}줄")
    dropped = sum(1 for record in records if record.get("kind") == "template_drop")
    if dropped != len(built):
        problems.append(f"템플릿을 지운 기록 {dropped}줄이 만든 기록 {len(built)}줄과 다르다")
    expected = "FILE_COPY" if plan.variant == "file_copy" else None
    if any(record.get("strategy") != expected for record in tests):
        problems.append(f"복제 문의 전략이 {expected} 가 아닌 시험이 있다")
    # 도우미는 같은 환경 변수로 세션 픽스처의 꼴(동기 + asyncio.run, 또는 세션 루프 비동기)을
    # 고르고 그 값을 템플릿 기록에 적는다. 계획한 꼴의 픽스처가 실제로 템플릿을 지었다는 표지다.
    if any(record.get("style") != plan.style for record in built):
        problems.append(f"세션 픽스처의 꼴이 {plan.style} 가 아닌 템플릿 기록이 있다")
    return problems, len(built)


def is_mapping(value: object) -> TypeGuard[dict[object, object]]:
    """JSON 에서 푼 값이 객체인가. 칸의 값은 쓰는 자리에서 다시 좁힌다."""
    return isinstance(value, dict)


def is_sequence(value: object) -> TypeGuard[list[object]]:
    """JSON 에서 푼 값이 배열인가."""
    return isinstance(value, list)


def as_names(value: object) -> list[str]:
    return [str(item) for item in value] if is_sequence(value) else []


def judge(outcome: Outcome, left: Sequence[str]) -> list[str]:
    """회차의 표지를 보고 빠진 것을 낸다. 비면 측정이다. 본 값은 `outcome.facts` 에 적는다."""
    plan, records = outcome.plan, outcome.records
    expected = sum(CASES.values())
    counts, pytest_seconds = summary_of(outcome.text)
    tests = [record for record in records if record.get("kind") == "test"]
    workers = {str(record.get("worker")) for record in tests}
    problems = header_problems(plan, outcome.text, expected)
    if outcome.code != 0:
        problems.append(f"pytest 종료 코드 {outcome.code}")
    if counts.get("passed") != expected or set(counts) - {"passed", "warnings", "warning"}:
        problems.append(f"요약 줄이 {expected} passed 가 아니다: {counts}")
    per_package = Counter(str(record.get("package")) for record in tests)
    if dict(per_package) != CASES:
        problems.append(f"시험 기록이 {CASES} 가 아니다: {dict(per_package)}")
    if len(workers) != plan.workers:
        problems.append(f"작업자 id 가 {plan.workers} 가 아니라 {len(workers)}: {sorted(workers)}")
    more, templates = template_problems(plan, records)
    problems += more
    for record in tests:
        package = str(record.get("package"))
        if set(as_names(record.get("tables"))) != TABLES.get(package):
            problems.append(f"{package} 의 데이터베이스에서 본 표가 다르다: {record.get('tables')}")
            break
        if record.get("versions") != [HEAD] or record.get("rows") != 1:
            problems.append(f"표의 판이나 줄 수가 다르다: {record.get('versions')}")
            break
    if left:
        problems.append(f"남은 데이터베이스 {len(left)}개: {list(left)[:3]}")
    more, facts = timing_facts(tests)
    problems += more
    built = [record for record in records if record.get("kind") == "template"]
    for name in ("build_s", "migrate_s"):
        found = [value for record in built if (value := as_float(record.get(name))) is not None]
        if found:
            facts[f"template_{name}"] = spread(found)
    sizes = sorted({as_int(record.get("size_bytes")) for record in built})
    outcome.facts.update(
        facts,
        passed=counts.get("passed"),
        warnings=counts.get("warnings", counts.get("warning", 0)),
        wall_s=round(outcome.seconds, 2),
        pytest_s=pytest_seconds,
        workers=len(workers),
        templates=templates,
        template_bytes=sizes,
        names=len({str(record.get("name")) for record in tests}),
    )
    return problems


def describe(outcome: Outcome) -> str:
    facts = outcome.facts
    shown = {
        "통과": "passed",
        "벽시계 초": "wall_s",
        "pytest 초": "pytest_s",
        "작업자": "workers",
        "템플릿": "templates",
        "경고": "warnings",
        "연결 최대": "max_clients",
        "pg_stat_activity 줄 최대": "max_rows",
        "표본": "samples",
        "시험당 WAL KB": "wal_per_test_kb",
        "요청 체크포인트": "checkpoints",
        "호스트 부하": "host_load",
    }
    head = ", ".join(f"{title} {facts.get(key)}" for title, key in shown.items())
    names = {
        "prepare_s": "준비(관리 연결 포함)",
        "create_sql_s": "CREATE DATABASE 문",
        "migrate_s": "시험마다 마이그레이션",
        "first_query_s": "붙어서 첫 질의",
        "drop_s": "지우기(관리 연결 포함)",
        "drop_sql_s": "DROP DATABASE 문",
        "both_s": "준비+지우기",
        "template_build_s": "템플릿 만들기",
        "template_migrate_s": "템플릿 마이그레이션",
    }
    lines = [head]
    for key, title in names.items():
        found = facts.get(key)
        if isinstance(found, dict):
            lines.append(f"    {title} ms: {json.dumps(found, ensure_ascii=False)}")
    return "\n".join(lines)


def measure(plans: Sequence[Plan], server: Server, work: Path) -> list[Outcome]:
    """실행 하나(동시 갈래는 둘)를 돌리고 서버의 앞뒤 값과 연결 수의 표본을 붙인다."""
    load = host_load()
    before = snapshot(server.url)
    with Sampler(server.url) as sampler:
        running = [launch(plan, server.url, work) for plan in plans]
        outcomes = [collect(item) for item in running]
    after = snapshot(server.url)
    tests = sum(1 for outcome in outcomes for r in outcome.records if r.get("kind") == "test")
    for outcome in outcomes:
        outcome.facts.update(
            host_load=load,
            max_clients=sampler.clients,
            max_rows=sampler.rows,
            samples=sampler.samples,
            sampler_error=sampler.error,
            wal_per_test_kb=round((after.wal - before.wal) / 1024 / max(tests, 1), 1),
            checkpoints=after.requested - before.requested,
            timed_checkpoints=after.timed - before.timed,
        )
    return outcomes


def mark(slot: Slot, problems: Sequence[str], good: str = "표지 모두 있음") -> None:
    """빠진 표지가 없을 때만 측정으로 적는다."""
    slot.mark(measured=not problems, result=good if not problems else "; ".join(problems))


def report(rounds: Rounds, detail: str) -> None:
    """방금 센 회차를 한 줄로 내고 본 값을 덧붙인다."""
    entry = rounds.entries[-1]
    verdict = "측정" if entry.measured else "측정 아님"
    say(f"- [{verdict}] {entry.label} => {entry.result}")
    if detail:
        say(f"    {detail}")


def pytest_round(rounds: Rounds, plan: Plan, server: Server, work: Path) -> Outcome:
    """pytest 실행 하나를 회차로 센다."""
    outcome = Outcome(plan, None, 0.0, "", [])
    with rounds.round(plan.label) as slot:
        outcome = measure([plan], server, work)[0]
        mark(slot, judge(outcome, leftovers(server.url)))
    report(rounds, describe(outcome))
    return outcome


def absent_round(rounds: Rounds, work: Path) -> None:
    """닫힌 포트를 주면 패키지 B 의 시험 80 개가 skip 이 아니라 도우미의 한 줄로 실패하는가.
    표지는 요약 줄이 오류 80 뿐이고, 오류 절의 `ERROR at setup of` 머리 80 개와 도우미의 문구로
    시작해 띄우는 명령으로 끝나는 줄 80 개가 있는 것이다. 짧은 요약의 ERROR 줄은 터미널 폭에 잘려
    문구가 다 실리지 않으므로 보지 않는다."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        closed = Server("없음", int(probe.getsockname()[1]))
    plan = Plan("서버 없음 -n 2", "absent", 2, paths=("tests/pkg_b",))
    detail = ""
    with rounds.round(plan.label) as slot:
        outcome = collect(launch(plan, closed.url, work))
        counts, seconds = summary_of(outcome.text)
        lines = [line.strip() for line in outcome.text.splitlines()]
        heads = [line for line in lines if "ERROR at setup of test_widget_round_trip[" in line]
        marked = [
            line for line in lines if line.startswith(FAIL_MARK) and line.endswith(START_HINT)
        ]
        expected = CASES["toy_b"]
        seen = counts == {"errors": expected} and not outcome.records
        seen = seen and len(heads) == expected and len(marked) == expected
        detail = f"요약 {counts}, 오류 머리 {len(heads)}, 도우미의 문구 {len(marked)}줄"
        detail += f", pytest {seconds}초, 벽시계 {outcome.seconds:.2f}초, 종료 코드 {outcome.code}"
        mark(slot, [] if seen else [detail], "도우미의 한 줄로 실패")
        detail += f"\n    첫 줄: {marked[0] if marked else ''}"
    report(rounds, detail)


def pair_round(rounds: Rounds, server: Server, work: Path) -> list[Outcome]:
    """pytest 실행 둘이 같은 컨테이너를 함께 쓴다. 둘 다 표지가 있고 이름이 겹치지 않아야 한다."""
    plans = [Plan(f"동시 {index} -n 4", f"pair-{index}", 4) for index in (1, 2)]
    outcomes: list[Outcome] = []
    with rounds.round("동시 두 실행 -n 4 + -n 4") as slot:
        outcomes = measure(plans, server, work)
        left = leftovers(server.url)
        problems = [f"{o.plan.label}: {p}" for o in outcomes for p in judge(o, left)]
        kinds = ("test", "template")
        names = [str(r.get("name")) for o in outcomes for r in o.records if r.get("kind") in kinds]
        if len(names) != len(set(names)):
            problems.append(f"이름이 겹쳤다: {len(names)}개 가운데 다른 것 {len(set(names))}개")
        mark(slot, problems)
    report(rounds, "\n    ".join(f"{o.plan.label}: {describe(o)}" for o in outcomes))
    return outcomes


def file_copy_round(rounds: Rounds, server: Server, work: Path, base: Sequence[Outcome]) -> Outcome:
    """FILE_COPY 로 복제한다. 전략이 실제로 바뀌었다는 표지는 시험 하나에 쓰인 WAL 이다."""
    plan = Plan("FILE_COPY -n 8", "file-copy", 8, variant="file_copy")
    usual = [as_float(outcome.facts.get("wal_per_test_kb")) for outcome in base]
    floor = min((value for value in usual if value is not None), default=0.0)
    outcome = Outcome(plan, None, 0.0, "", [])
    with rounds.round(plan.label) as slot:
        outcome = measure([plan], server, work)[0]
        problems = judge(outcome, leftovers(server.url))
        used = as_float(outcome.facts.get("wal_per_test_kb"))
        if used is None or floor <= 0 or used >= floor / 2:
            problems.append(f"시험당 WAL {used}KB 가 기본 전략 {floor}KB 의 절반보다 적지 않다")
        mark(slot, problems)
    report(rounds, describe(outcome))
    return outcome


def branches(rounds: Rounds, server: Server, work: Path, only: set[str]) -> list[Outcome]:
    """고른 갈래를 차례로 돈다. FILE_COPY 의 표지는 같은 실행의 `-n 8` 주 측정에 기댄다."""
    outcomes: list[Outcome] = []
    main_runs: list[Outcome] = []
    if "absent" in only:
        absent_round(rounds, work)
    if "n8" in only:
        main_runs = [
            pytest_round(rounds, Plan(f"-n 8 {index}회차", f"n8-{index}", 8), server, work)
            for index in (1, 2, 3)
        ]
        outcomes += main_runs
    if "n1" in only:
        outcomes.append(pytest_round(rounds, Plan("-n 1", "n1", 1), server, work))
    if "migrate-each" in only:
        contrast = Plan("대조: 시험마다 마이그레이션 -n 8", "migrate-each", 8, "migrate_each")
        outcomes.append(pytest_round(rounds, contrast, server, work))
    if "pair" in only:
        outcomes += pair_round(rounds, server, work)
    if "file-copy" in only:
        outcomes.append(file_copy_round(rounds, server, work, main_runs))
    if "session-loop" in only:
        looped = Plan("세션 루프 픽스처 -n 8", "session-loop", 8, style="session_loop")
        outcomes.append(pytest_round(rounds, looped, server, work))
    return outcomes


def main() -> int:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("--work", type=Path, default=Path(tempfile.gettempdir()) / CONTAINER_PREFIX)
    parser.add_argument("--only", default=",".join(BRANCHES), help="돌릴 갈래(쉼표로 잇는다)")
    args = parser.parse_args()
    only = {name for name in str(args.only).split(",") if name}
    if only - set(BRANCHES):
        parser.error(f"모르는 갈래: {sorted(only - set(BRANCHES))}. 고를 수 있는 것: {BRANCHES}")
    token = secrets.token_hex(4)
    work: Path = args.work / f"run-{token}"
    work.mkdir(parents=True)
    _raw.append(work / "raw.log")
    say(f"실행 {token}, 원본 출력 {work}, 시작 {time.strftime('%Y-%m-%d %H:%M:%S')}")
    rounds = Rounds()
    results: dict[str, object] = {"token": token, "started": time.strftime("%Y-%m-%d %H:%M:%S")}

    seen = ""
    with rounds.round("정적: 도우미가 두 패키지를 import 하지 않는다") as slot:
        problems, seen = static_problems()
        mark(slot, problems, "import 없음")
    report(rounds, seen)

    name = f"{CONTAINER_PREFIX}-{token}"
    # 회차는 예외를 삼키므로 서버가 떴는지는 이 목록이 비었는지로 본다.
    started: list[Server] = []
    outcomes: list[Outcome] = []
    try:
        with rounds.round("컨테이너: tmpfs 와 fsync 끔으로 떠서 답한다") as slot:
            begun = time.monotonic()
            started.append(start_server(name))
            problems, facts = server_facts(started[0])
            facts["ready_s"] = str(round(time.monotonic() - begun, 2))
            results["server"] = facts
            mark(slot, problems, "설정대로 떴다")
        report(rounds, json.dumps(results.get("server", {}), ensure_ascii=False))
        if started:
            outcomes = branches(rounds, started[0], work, only)
    finally:
        remove_server(name)
    results["runs"] = [
        {"label": o.plan.label, "variant": o.plan.variant, "style": o.plan.style, **o.facts}
        for o in outcomes
    ]
    results["rounds"] = [
        {"label": e.label, "measured": e.measured, "result": e.result} for e in rounds.entries
    ]
    (work / "results.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    say(f"끝 {time.strftime('%Y-%m-%d %H:%M:%S')}, 결과 {work / 'results.json'}")
    summary = rounds.summary()
    say(summary)
    return rounds.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
