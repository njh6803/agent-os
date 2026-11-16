"""settings_fetch 측정 전체. 위젯 테스트 페이지의 서버가 요청 때마다 위젯 관리 서버에 사이트
목록을 물으면 응답이 얼마나 느려지는지를 대역 셋으로 잰다.

띄우는 것. PostgreSQL 컨테이너(`postgres:18-alpine`, 이름 `portal-admin-settings-fetch-<표지>`),
위젯 관리 서버 대역(`admin_stub.py`), 위젯 테스트 페이지 서버 대역(`portal_stub.mjs`), 요청을
보내는 쪽(`loadgen.mjs`). 모두 `127.0.0.1` 에서만 듣는다. 끝에 모두 내린다.

쓰임(저장소 루트에서):
    uv run --with "psycopg[binary,pool]" python .scratch/portal-admin/probes/settings_fetch/run.py

회차와 표지. 회차는 (되풀이 번호, 단계, 갈래) 하나다. 갈래마다 재려는 상황이 그 회차에 났다는
표지를 본 뒤에만 측정으로 센다(`tools/probe_kit.py` 의 `Rounds`). 표지는 아래다.
- 요청마다 물었다: 답마다 대역이 돌려준 일련번호(`seq`)가 서로 다르고 그 수가 보낸 요청의 수와
  같다. 되풀이마다 대역이 센 요청 수의 차가 페이지 대역이 적은 호출 수의 합과 같다(`accounting`).
- 데이터베이스를 실제로 조회했다: 답에 든 줄 수가 10 이고, 답에 든 회차 표지(nonce)가 그 되풀이
  직전에 데이터베이스에 써 둔 값과 같다. 끝에 PostgreSQL 통계의 표 훑기 수가 대역이 끝낸 조회의
  수와 같다(`db-scans`).
- 다른 서버를 부르지 않았다(기준): 페이지 대역이 적은 호출이 0 이다(위 `accounting` 이 맞댄다).
- 연결을 이어 썼다: 대역이 본 상대 포트의 가짓수가 요청 수보다 훨씬 적다. 새 연결: 대역이 요청마다
  `Connection: close` 를 봤다(`node:http` 는 `reusedSocket` 이 모두 거짓). 유휴 뒤 새 연결: 대역이
  본 상대 포트가 요청마다 다르다.
- 둘을 차례로 불렀다/함께 불렀다: "지금 누구인지" 호출의 시작이 사이트 목록 호출의 끝보다
  뒤다/앞이다.
- 기억이 맞았다/빗나갔다: 맞은 요청은 대역을 부르지 않았고 그 값의 일련번호가 앞서 빗나간 요청의
  것이다. 빗나간 요청은 새 일련번호를 받았다.
- 대역이 내려가 있었다: 그 포트에서 대역이 답한 것을 본 뒤(`down-prime`) 명령줄의 표지를 보고
  껐고, 그 뒤의 모든 요청의 오류 코드가 `ECONNREFUSED` 다.
- 대역이 느렸다: 대역이 적은 조회 시간이 지연 이상이다. 제한 시간이 걸렸다: 오류 이름이
  `TimeoutError` 다.
- 대역이 답하지 않았다(`--hang`): 받기만 하고 답하지 않는 소켓이 그 요청 줄을 받았다.

못 보는 것. 로컬 PC 의 루프백에서만 잰다. 컨테이너 사이의 네트워크, TLS, 실제 위젯 관리 서버의
코드(아직 없다), 다른 드라이버, 리눅스 호스트는 재지 않는다.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import platform
import secrets
import shutil
import socket
import statistics
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import BinaryIO

import psycopg

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))

from admin_stub import SITES_SQL  # noqa: E402
from tools.probe_kit import Rounds  # noqa: E402

PG_IMAGE = "postgres:18-alpine"
CONTAINER_PREFIX = "portal-admin-settings-fetch-"
SITE_ROWS = 10
SLOW_DELAY_MS = 3000
CALL_TIMEOUT_MS = 1000
CACHE_TTL_MS = 2000
IDLE_GAP_MS = 6000
HANG_CLIENT_TIMEOUT_MS = 330_000

SCHEMA = """
CREATE TABLE probe_nonce (id integer PRIMARY KEY, nonce text NOT NULL);
CREATE TABLE probe_sites (
    name text PRIMARY KEY,
    issuer text NOT NULL UNIQUE,
    assurance_mode text NOT NULL,
    report_link text NOT NULL,
    public_origin text NOT NULL,
    login_entry text NOT NULL
);
CREATE TABLE probe_accounts (
    id integer PRIMARY KEY,
    username text NOT NULL,
    role text NOT NULL,
    session_hash text NOT NULL UNIQUE
);
"""

SCANS_SQL = """
SELECT relname, coalesce(seq_scan, 0) + coalesce(idx_scan, 0)
FROM pg_stat_user_tables WHERE relname IN ('probe_sites', 'probe_accounts')
"""


@dataclass(frozen=True)
class Branch:
    """갈래 하나. `calls` 는 요청 하나가 대역을 부르는 차례, `parallel` 은 둘을 부를 때
    겹치는지다."""

    name: str
    query: str
    calls: tuple[str, ...] = ()
    via: str = "fetch"
    close: bool = False
    parallel: bool | None = None

    def step_entry(self) -> dict[str, str]:
        return {"name": self.name, "query": self.query}


NONE = Branch("none", "calls=none")
MAIN = [
    NONE,
    Branch("sites-fetch", "calls=sites&via=fetch", ("sites",)),
    Branch("sites-http", "calls=sites&via=http", ("sites",), via="http"),
    Branch("both-seq-fetch", "calls=seq&via=fetch", ("sites", "whoami"), parallel=False),
    Branch("both-par-fetch", "calls=par&via=fetch", ("sites", "whoami"), parallel=True),
    # fetch 는 주소마다 연결 묶음을 따로 둔다. 닫는 갈래가 같은 주소를 부르면 이어 쓰는 갈래의
    # 연결까지 닫히므로 대역의 둘째 포트(alt)를 부른다.
    Branch(
        "sites-newconn-fetch", "calls=sites&via=fetch&conn=close&up=alt", ("sites",), close=True
    ),
    Branch(
        "sites-newconn-http",
        "calls=sites&via=http&conn=close",
        ("sites",),
        via="http",
        close=True,
    ),
]
CACHE = Branch("cache2s-fetch", f"calls=sites&via=fetch&ttl={CACHE_TTL_MS}", ("sites",))
IDLE_NONE = Branch("none-idle6s", "calls=none")
IDLE = [
    Branch("sites-idle6s-fetch", "calls=sites&via=fetch", ("sites",)),
    Branch("sites-idle6s-http", "calls=sites&via=http", ("sites",), via="http"),
]
PRELUDE = Branch("prelude", "calls=none")
SLOW = [
    Branch(f"slow3s-notimeout-{via}", f"calls=sites&via={via}&delay_ms={SLOW_DELAY_MS}", via=via)
    for via in ("fetch", "http")
]
SLOW_TIMEOUT = [
    Branch(
        f"slow3s-timeout1s-{via}",
        f"calls=sites&via={via}&delay_ms={SLOW_DELAY_MS}&timeout_ms={CALL_TIMEOUT_MS}",
        via=via,
    )
    for via in ("fetch", "http")
]
DOWN_PRIME = [
    Branch(f"downtarget-alive-{via}", f"calls=sites&via={via}&up=down", ("sites",), via=via)
    for via in ("fetch", "http")
]
DOWN = [
    Branch(f"down-notimeout-{via}", f"calls=sites&via={via}&up=down", via=via)
    for via in ("fetch", "http")
]
DOWN_TIMEOUT = Branch(
    "down-timeout1s-fetch", f"calls=sites&via=fetch&up=down&timeout_ms={CALL_TIMEOUT_MS}"
)
HANG = [
    Branch(f"hang-notimeout-{via}", f"calls=sites&via={via}&up=hang", via=via)
    for via in ("fetch", "http")
]


@dataclass
class Child:
    """띄운 프로세스 하나. `marker` 는 끄기 전에 그 pid 의 명령줄에서 찾는 이 회차의 표지다."""

    name: str
    process: subprocess.Popen[bytes]
    marker: str
    log: BinaryIO


@dataclass
class Row:
    """회차 하나의 판정과 통계."""

    passno: int
    step: str
    branch: str
    measured: bool
    problems: list[str]
    details: dict[str, object]
    client: dict[str, float] | None = None
    upstream: dict[str, float] | None = None
    database: dict[str, float] | None = None
    hop: dict[str, float] | None = None


@dataclass
class Context:
    args: argparse.Namespace
    token: str
    work: Path
    node: str
    container: str
    dsn: str
    admin: str
    portal: str
    down_port: int
    rounds: Rounds = field(default_factory=Rounds)
    rows: list[Row] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)
    children: list[Child] = field(default_factory=list)
    nonce: str = ""
    other_site_scans: int = 0


def log(message: str) -> None:
    stamp = datetime.now(UTC).astimezone().strftime("%H:%M:%S")
    print(f"[{stamp}] {message}", flush=True)


# ---------------------------------------------------------------------------------------------
# 프로세스와 컨테이너


def run(
    argv: list[str], *, timeout: float, env: dict[str, str] | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        env=env,
        check=False,
    )


def command_line(pid: int) -> str:
    """그 pid 의 명령줄. 읽지 못하면 빈 글이다."""
    if os.name == "nt":
        script = f"(Get-CimInstance Win32_Process -Filter 'ProcessId={pid}').CommandLine"
        completed = run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", script], timeout=60
        )
        return completed.stdout.strip()
    try:
        raw = Path(f"/proc/{pid}/cmdline").read_bytes()
    except OSError:
        return ""
    return raw.replace(b"\0", b" ").decode("utf-8", errors="replace")


def stop(child: Child) -> str:
    """끄기 직전에 그 pid 의 명령줄을 읽어 이 회차의 표지가 있을 때만 끈다(`.claude/rules/probes.md`
    의 끄기 항목). 무엇을 했는지 돌려준다."""
    outcome = "이미 끝나 있었다"
    if child.process.poll() is None:
        line = command_line(child.process.pid)
        if child.marker not in line:
            outcome = "명령줄에 이 회차의 표지가 없어 끄지 않았다"
        elif os.name == "nt":
            run(["taskkill", "/PID", str(child.process.pid), "/T", "/F"], timeout=60)
            outcome = "껐다"
        else:
            child.process.kill()
            outcome = "껐다"
    if outcome == "껐다":
        try:
            child.process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            outcome = "껐지만 20초 안에 끝나지 않았다"
    child.log.close()
    return outcome


def launch(ctx: Context, name: str, argv: list[str], *, env: dict[str, str] | None = None) -> Child:
    handle = (ctx.work / f"{name}.log").open("wb")
    process = subprocess.Popen(
        argv, stdout=handle, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, env=env
    )
    child = Child(name, process, ctx.token, handle)
    ctx.children.append(child)
    return child


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def http_json(url: str, *, timeout: float = 5.0) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read())


def wait_for(what: str, check: Callable[[], bool], *, timeout: float) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if check():
            return
        time.sleep(0.25)
    raise RuntimeError(f"{what}: {timeout:.0f}초 안에 준비되지 않았다")


def answers_with(url: str, token: str) -> Callable[[], bool]:
    """그 주소가 이 회차의 표지로 답하는지. 같은 포트의 다른 프로세스를 우리 것으로 읽지 않는다."""

    def check() -> bool:
        try:
            return http_json(url, timeout=2).get("run_token") == token
        except (OSError, ValueError):
            return False

    return check


def refusal(port: int) -> tuple[bool, float, str]:
    """파이썬 소켓으로 그 포트에 붙어 본다. (거절됐는가, 걸린 초, 본 것)."""
    began = time.perf_counter()
    try:
        socket.create_connection(("127.0.0.1", port), timeout=15).close()
    except ConnectionRefusedError as error:
        return True, time.perf_counter() - began, f"ConnectionRefusedError errno={error.errno}"
    except OSError as error:
        return False, time.perf_counter() - began, type(error).__name__
    return False, time.perf_counter() - began, "연결됐다"


def host_load() -> str:
    """호스트 CPU 부하(%). 회차로 세지 않는 참고 값이다. 읽지 못하면 빈 글이다."""
    if os.name != "nt":
        return f"loadavg {os.getloadavg()[0]:.2f}"
    script = (
        "(Get-CimInstance Win32_Processor | Measure-Object -Property LoadPercentage -Average)"
        ".Average"
    )
    try:
        completed = run(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", script], timeout=60
        )
    except subprocess.TimeoutExpired:
        return ""
    return completed.stdout.strip()


def start_postgres(name: str, password: str) -> int:
    """컨테이너를 띄우고 호스트 쪽 포트를 돌려준다. 비밀번호는 명령줄이 아니라 환경으로 넘긴다."""
    image = run(["docker", "image", "inspect", "--format", "{{.Id}}", PG_IMAGE], timeout=60)
    if image.returncode != 0:
        raise RuntimeError(f"이미지 {PG_IMAGE} 가 없다. 먼저 `docker pull {PG_IMAGE}` 를 친다")
    started = run(
        [
            "docker",
            "run",
            "-d",
            "--name",
            name,
            "-e",
            "POSTGRES_PASSWORD",
            "-p",
            "127.0.0.1::5432",
            PG_IMAGE,
        ],
        timeout=180,
        env={**os.environ, "POSTGRES_PASSWORD": password},
    )
    if started.returncode != 0:
        raise RuntimeError(f"docker run 실패: {started.stderr.strip()[:300]}")
    mapped = run(["docker", "port", name, "5432/tcp"], timeout=60).stdout.strip().splitlines()
    if not mapped:
        raise RuntimeError("docker port 가 포트를 내지 않았다")
    return int(mapped[0].rsplit(":", 1)[1])


def remove_postgres(name: str) -> str:
    """이 회차가 띄운 그 이름의 컨테이너만 익명 볼륨과 함께 지운다."""
    run(["docker", "rm", "-f", "-v", name], timeout=120)
    left = run(
        ["docker", "ps", "-a", "--filter", f"name=^/{name}$", "--format", "{{.Names}}"], timeout=60
    )
    return "지웠다" if not left.stdout.strip() else f"남았다: {left.stdout.strip()}"


def postgres_ready(dsn: str) -> Callable[[], bool]:
    def check() -> bool:
        try:
            with psycopg.connect(dsn, connect_timeout=3) as connection:
                connection.execute("SELECT 1")
        except psycopg.Error:
            return False
        return True

    return check


def seed(dsn: str, token: str) -> dict[str, int]:
    """표 셋을 만들고 채운 뒤, 그때까지의 표 훑기 수(기준선)를 돌려준다."""
    session_hash = hashlib.sha256(f"probe-session-{token}".encode()).hexdigest()
    with psycopg.connect(dsn, autocommit=True) as connection:
        connection.execute(SCHEMA)
        connection.execute("INSERT INTO probe_nonce VALUES (1, 'seed')")
        for index in range(1, SITE_ROWS + 1):
            connection.execute(
                "INSERT INTO probe_sites VALUES (%s, %s, %s, %s, %s, %s)",
                (
                    f"site-{index:02d}",
                    f"https://issuer-{index:02d}.example.test",
                    "anonymous" if index % 2 else "login",
                    f"https://reports.example.test/site-{index:02d}",
                    f"https://site-{index:02d}.example.test",
                    "main" if index % 2 else "",
                ),
            )
        for index in range(1, 21):
            connection.execute(
                "INSERT INTO probe_accounts VALUES (%s, %s, %s, %s)",
                (
                    index,
                    f"operator-{index:02d}",
                    "admin",
                    session_hash if index == 7 else hashlib.sha256(str(index).encode()).hexdigest(),
                ),
            )
        connection.execute("SELECT pg_stat_force_next_flush()")
        return dict(connection.execute(SCANS_SQL).fetchall())


def set_nonce(dsn: str, nonce: str) -> None:
    with psycopg.connect(dsn, autocommit=True) as connection:
        connection.execute("UPDATE probe_nonce SET nonce = %s WHERE id = 1", (nonce,))


def scans(dsn: str) -> dict[str, int]:
    with psycopg.connect(dsn, autocommit=True) as connection:
        return dict(connection.execute(SCANS_SQL).fetchall())


def server_version(dsn: str) -> str:
    with psycopg.connect(dsn, autocommit=True) as connection:
        row = connection.execute("SHOW server_version").fetchone()
    return "" if row is None else str(row[0])


class Blackhole:
    """연결을 받고 요청 줄만 읽은 뒤 답하지 않는 소켓. 답하지 않는 대역의 자리다."""

    def __init__(self) -> None:
        self._listener = socket.create_server(("127.0.0.1", 0))
        self.port = int(self._listener.getsockname()[1])
        self.request_lines: list[str] = []
        self._held: list[socket.socket] = []
        threading.Thread(target=self._accept, daemon=True).start()

    def _accept(self) -> None:
        while True:
            try:
                connection, _ = self._listener.accept()
            except OSError:
                return
            connection.settimeout(5)
            try:
                first = connection.recv(200)
            except OSError:
                first = b""
            self.request_lines.append(first.split(b"\r\n", 1)[0].decode("ascii", "replace"))
            self._held.append(connection)

    def close(self) -> None:
        self._listener.close()
        for connection in self._held:
            connection.close()


# ---------------------------------------------------------------------------------------------
# 요청 보내기와 기록 읽기


def loadgen_argv(ctx: Context, name: str, steps: list[dict]) -> tuple[list[str], Path]:
    plan = ctx.work / f"plan-{name}.json"
    out = ctx.work / f"records-{name}.jsonl"
    plan.write_text(
        json.dumps({"target": ctx.portal, "out": str(out), "steps": steps}), encoding="utf-8"
    )
    return [ctx.node, str(HERE / "loadgen.mjs"), str(plan)], out


def read_records(out: Path) -> list[dict]:
    return [json.loads(line) for line in out.read_text(encoding="utf-8").splitlines() if line]


def run_loadgen(ctx: Context, name: str, steps: list[dict], *, timeout: float) -> list[dict]:
    argv, out = loadgen_argv(ctx, name, steps)
    completed = run(argv, timeout=timeout)
    if completed.returncode != 0:
        raise RuntimeError(
            f"loadgen {name} 종료 코드 {completed.returncode}: {completed.stderr[:200]}"
        )
    return read_records(out)


def calls_of(record: dict) -> list[dict]:
    probe = record.get("probe") or {}
    return list(probe.get("calls") or [])


def measured_of(records: list[dict], step: str, branch: str) -> list[dict]:
    return [
        record
        for record in records
        if record["step"] == step and record["branch"] == branch and not record["warmup"]
    ]


def percentile(ordered: list[float], percent: float) -> float:
    """가까운 순위법. 정렬한 n 개 가운데 ceil(percent/100 * n) 번째 값이다."""
    return ordered[max(1, math.ceil(percent / 100 * len(ordered))) - 1]


def stats_of(values: list[float]) -> dict[str, float]:
    ordered = sorted(values)
    return {
        "n": len(ordered),
        "min": ordered[0],
        "median": statistics.median(ordered),
        "p95": percentile(ordered, 95),
        "p99": percentile(ordered, 99),
        "max": ordered[-1],
        "mean": statistics.fmean(ordered),
    }


# ---------------------------------------------------------------------------------------------
# 표지


def base_problems(records: list[dict], expected: int) -> list[str]:
    problems: list[str] = []
    if len(records) != expected:
        problems.append(f"기록이 {len(records)}개다(기대 {expected})")
    if any(record.get("client_error") for record in records):
        problems.append("보내는 쪽에서 실패한 요청이 있다")
    if any(record.get("probe") is None for record in records):
        problems.append("표지 헤더가 없는 답이 있다")
    return problems


def check_served(
    records: list[dict],
    branch: Branch,
    *,
    expected: int,
    nonce: str,
    concurrency: int,
    fresh_each: bool = False,
) -> tuple[list[str], dict[str, object]]:
    """대역을 부르고 답을 받은 갈래(기준 갈래 포함)의 표지."""
    problems = base_problems(records, expected)
    calls = [call for record in records for call in calls_of(record)]
    if any(record.get("status") != 200 for record in records):
        problems.append("200 이 아닌 답이 있다")
    shapes = {tuple(call["what"] for call in calls_of(record)) for record in records}
    if shapes != {branch.calls}:
        problems.append(f"호출의 모양이 기대와 다르다: {sorted(shapes)}")
    if any(not call.get("ok") for call in calls):
        problems.append("실패한 호출이 있다")
    for what, rows in (("sites", SITE_ROWS), ("whoami", 1)):
        mine = [call for call in calls if call["what"] == what]
        if what not in branch.calls:
            continue
        if len({call.get("seq") for call in mine}) != expected:
            problems.append(f"{what} 의 일련번호 가짓수가 요청 수와 다르다")
        if any(call.get("rows") != rows for call in mine):
            problems.append(f"{what} 의 줄 수가 {rows} 이 아닌 답이 있다")
        if any(call.get("nonce") != nonce for call in mine):
            problems.append(f"{what} 의 회차 표지가 이 되풀이의 것이 아닌 답이 있다")
    ports = {call.get("port") for call in calls}
    closes = sum(1 for call in calls if call.get("connection") == "close")
    not_reused = sum(1 for call in calls if call.get("reused") is False)
    if branch.close:
        if closes != len(calls):
            problems.append("대역이 Connection: close 를 보지 못한 호출이 있다")
        if branch.via == "http" and not_reused != len(calls):
            problems.append("node:http 가 소켓을 다시 쓴 호출이 있다")
    elif calls:
        if closes:
            problems.append("이어 쓰는 갈래인데 대역이 Connection: close 를 봤다")
        if fresh_each and len(ports) != len(calls):
            problems.append(f"유휴 뒤인데 상대 포트가 {len(ports)}가지다(호출 {len(calls)})")
        allowed = max(concurrency * len(branch.calls), len(calls) // 10)
        if not fresh_each and len(ports) > allowed:
            problems.append(f"이어 쓰는 갈래인데 상대 포트가 {len(ports)}가지다(허용 {allowed})")
    if branch.parallel is not None:
        overlaps = [
            who["start"] < site["end"]
            for site, who in (calls_of(record) for record in records if len(calls_of(record)) == 2)
        ]
        if branch.parallel and not all(overlaps):
            problems.append("함께 부르는 갈래인데 겹치지 않은 요청이 있다")
        if not branch.parallel and any(overlaps):
            problems.append("차례로 부르는 갈래인데 겹친 요청이 있다")
    details: dict[str, object] = {
        "calls": len(calls),
        "distinct_ports": len(ports) if calls else 0,
        "connection_close_seen": closes,
        "http_not_reused": not_reused,
    }
    return problems, details


def error_label(call: dict) -> str:
    """오류의 이름, 코드, 까닭의 이름, 까닭의 코드를 `/` 로 이은 글."""
    error = call.get("error") or {}
    parts = (error.get(key) for key in ("name", "code", "cause_name", "cause_code"))
    return "/".join(str(part) for part in parts if part is not None)


def is_refused(call: dict) -> bool:
    error = call.get("error") or {}
    return "ECONNREFUSED" in (error.get("code"), error.get("cause_code"))


def is_timeout(call: dict) -> bool:
    error = call.get("error") or {}
    return "TimeoutError" in (error.get("name"), error.get("cause_name"))


def check_failed(
    records: list[dict], *, expected: int, accept: Callable[[dict], bool], what: str
) -> tuple[list[str], dict[str, object]]:
    """대역 호출이 실패하기를 기대하는 갈래. 실패의 까닭까지 본다."""
    problems = base_problems(records, expected)
    calls = [call for record in records for call in calls_of(record)]
    if len(calls) != len(records):
        problems.append("호출이 요청마다 하나가 아니다")
    if any(record.get("status") != 502 for record in records):
        problems.append("502 가 아닌 답이 있다")
    if any(call.get("ok") for call in calls):
        problems.append("성공한 호출이 있다")
    labels = Counter(error_label(call) for call in calls if not call.get("ok"))
    if not all(accept(call) for call in calls):
        problems.append(f"{what} 이 아닌 실패가 있다: {dict(labels)}")
    return problems, {"errors": dict(labels)}


def check_slow_ok(records: list[dict], *, expected: int, nonce: str) -> tuple[list[str], dict]:
    problems = base_problems(records, expected)
    calls = [call for record in records for call in calls_of(record)]
    if any(record.get("status") != 200 for record in records) or len(calls) != len(records):
        problems.append("200 이 아니거나 호출이 하나가 아닌 답이 있다")
    if any(call.get("delay_ms") != SLOW_DELAY_MS for call in calls):
        problems.append("대역이 지연을 받지 못한 호출이 있다")
    if any((call.get("query_ms") or 0) < SLOW_DELAY_MS for call in calls):
        problems.append("대역의 조회 시간이 지연보다 짧은 호출이 있다")
    if any(call.get("rows") != SITE_ROWS or call.get("nonce") != nonce for call in calls):
        problems.append("줄 수나 회차 표지가 다른 답이 있다")
    return problems, {"query_ms_min": min((call.get("query_ms") or 0) for call in calls or [{}])}


def check_cache(
    records: list[dict], *, expected: int, nonce: str
) -> tuple[list[str], dict[str, object], list[dict], list[dict]]:
    problems = base_problems(records, expected)
    hits = [record for record in records if (record.get("probe") or {}).get("cache") == "hit"]
    misses = [record for record in records if (record.get("probe") or {}).get("cache") == "miss"]
    miss_calls = [call for record in misses for call in calls_of(record)]
    miss_seqs = {call.get("seq") for call in miss_calls}
    if len(hits) + len(misses) != len(records):
        problems.append("맞음도 빗나감도 아닌 답이 있다")
    if len(misses) < 2 or not hits:
        problems.append(f"빗나간 요청 {len(misses)}, 맞은 요청 {len(hits)}: 견줄 만큼 나지 않았다")
    if len(miss_calls) != len(misses) or len(miss_seqs) != len(misses):
        problems.append("빗나간 요청이 저마다 새 일련번호를 받지 않았다")
    if any(not call.get("ok") or call.get("rows") != SITE_ROWS for call in miss_calls):
        problems.append("빗나간 요청 가운데 실패했거나 줄 수가 다른 것이 있다")
    if any(call.get("nonce") != nonce for call in miss_calls):
        problems.append("빗나간 요청의 회차 표지가 이 되풀이의 것이 아니다")
    if any(calls_of(record) for record in hits):
        problems.append("맞은 요청이 대역을 불렀다")
    if any(record["probe"].get("cached_seq") not in miss_seqs for record in hits):
        problems.append("맞은 요청의 값이 이 단계에서 빗나간 요청이 받아 온 것이 아니다")
    stale = sum(1 for record in hits if record["probe"].get("cached_nonce") != nonce)
    return problems, {"hits": len(hits), "misses": len(misses), "stale_hits": stale}, hits, misses


def database_and_hop(
    records: list[dict],
) -> tuple[dict[str, float] | None, dict[str, float] | None]:
    """대역이 적은 조회 시간(연결을 빌려 조회를 끝내기까지)의 통계와, 호출이 하나인 요청에서 대역을
    기다린 시간에서 그 조회 시간을 뺀 나머지(HTTP 왕복)의 통계. 성공한 호출이 없으면 None 이다."""
    database: list[float] = []
    hop: list[float] = []
    for record in records:
        calls = [call for call in calls_of(record) if call.get("ok")]
        if not calls:
            continue
        spent = sum(call["query_ms"] for call in calls)
        database.append(spent)
        if len(calls) == 1 and len(calls_of(record)) == 1:
            hop.append(record["probe"]["upstream_ms"] - spent)
    return (stats_of(database) if database else None, stats_of(hop) if hop else None)


def add_row(
    ctx: Context,
    passno: int,
    step: str,
    branch: str,
    records: list[dict],
    verdict: tuple[list[str], dict[str, object]],
) -> None:
    """회차 하나를 적는다. 표지가 모두 맞을 때만 측정이고 통계는 측정인 회차에만 낸다."""
    problems, details = verdict
    label = f"p{passno}/{step}/{branch}"
    row = Row(passno, step, branch, not problems, problems, details)
    with ctx.rounds.round(label) as current:
        if not problems:
            row.client = stats_of([record["ms"] for record in records])
            upstream = [record["probe"]["upstream_ms"] for record in records]
            row.upstream = stats_of(upstream)
            row.database, row.hop = database_and_hop(records)
        current.mark(
            measured=not problems, result="표지 맞음" if not problems else "; ".join(problems)
        )
    ctx.rows.append(row)


def phase(ctx: Context, label: str, body: Callable[[], None]) -> None:
    """되풀이의 한 토막. 토막이 예외로 끝나면 측정이 아닌 회차 하나로 적고 다음 토막으로 간다."""
    try:
        body()
    except Exception as error:  # 토막 하나의 실패가 앞서 모은 회차를 잃게 하지 않는다
        ctx.rounds.record(label, measured=False, result=f"예외: {error!r}")
        log(f"{label}: 예외 {error!r}")


# ---------------------------------------------------------------------------------------------
# 되풀이 하나


def admin_counts(ctx: Context) -> dict[str, dict[str, int]]:
    stats = http_json(f"{ctx.admin}/__stats")
    return {"started": stats["started"], "finished": stats["finished"]}


def delta(after: dict[str, int], before: dict[str, int]) -> dict[str, int]:
    return {name: after[name] - before[name] for name in after}


def main_phase(ctx: Context, passno: int) -> None:
    args = ctx.args
    entries = [branch.step_entry() for branch in MAIN]
    steps: list[dict] = [
        {
            "kind": "rr",
            "label": "seq",
            "count": args.count,
            "warmup": args.warmup,
            "branches": entries,
        },
        {
            "kind": "chunks",
            "label": "conc10",
            "count": args.count,
            "chunk": args.chunk,
            "concurrency": args.concurrency,
            "warmup": args.warmup,
            "branches": entries,
        },
        {
            "kind": "paced",
            "label": "cache",
            "count": args.cache_count,
            "gap_ms": args.cache_gap_ms,
            "lead_ms": 0,
            "branches": [CACHE.step_entry()],
        },
        {
            "kind": "paced",
            "label": "idle",
            "count": args.idle_count,
            "gap_ms": IDLE_GAP_MS,
            "lead_ms": IDLE_GAP_MS,
            "prelude": PRELUDE.step_entry(),
            "branches": [branch.step_entry() for branch in (IDLE_NONE, *IDLE)],
        },
    ]
    before = admin_counts(ctx)
    records = run_loadgen(ctx, f"p{passno}-main", steps, timeout=1200)
    after = admin_counts(ctx)
    for step, concurrency in (("seq", 1), ("conc10", args.concurrency)):
        for branch in MAIN:
            mine = measured_of(records, step, branch.name)
            verdict = check_served(
                mine, branch, expected=args.count, nonce=ctx.nonce, concurrency=concurrency
            )
            add_row(ctx, passno, step, branch.name, mine, verdict)
    mine = measured_of(records, "cache", CACHE.name)
    problems, details, hits, misses = check_cache(mine, expected=args.cache_count, nonce=ctx.nonce)
    add_row(ctx, passno, "cache", "cache2s-hit-fetch", hits, (problems, details))
    add_row(ctx, passno, "cache", "cache2s-miss-fetch", misses, (problems, details))
    for branch in (IDLE_NONE, *IDLE):
        mine = measured_of(records, "idle", branch.name)
        verdict = check_served(
            mine, branch, expected=args.idle_count, nonce=ctx.nonce, concurrency=1, fresh_each=True
        )
        add_row(ctx, passno, "idle", branch.name, mine, verdict)
    reported = Counter(call["what"] for record in records for call in calls_of(record))
    seen = delta(after["started"], before["started"])
    matches = seen["sites"] == reported["sites"] and seen["whoami"] == reported["whoami"]
    quiet = {NONE.name, IDLE_NONE.name, PRELUDE.name}
    none_calls = sum(len(calls_of(record)) for record in records if record["branch"] in quiet)
    text = (
        f"대역이 센 요청 {seen}, 페이지 대역이 적은 호출 {dict(reported)},"
        f" 기준 갈래의 호출 {none_calls}"
    )
    matches = matches and none_calls == 0 and seen["sites_delayed"] == 0
    ctx.rounds.record(
        f"p{passno}/main/accounting", measured=matches, result="표지 맞음" if matches else text
    )
    ctx.notes.append(f"p{passno} main: {text}")


def slow_phase(ctx: Context, passno: int) -> None:
    count = ctx.args.slow_count
    branches = [*SLOW, *SLOW_TIMEOUT]
    steps: list[dict] = [
        {
            "kind": "rr",
            "label": "slow",
            "count": count,
            "warmup": 0,
            "timeout_ms": 60000,
            "branches": [branch.step_entry() for branch in branches],
        }
    ]
    before = admin_counts(ctx)
    records = run_loadgen(ctx, f"p{passno}-slow", steps, timeout=600)
    for branch in SLOW:
        mine = measured_of(records, "slow", branch.name)
        add_row(
            ctx,
            passno,
            "slow",
            branch.name,
            mine,
            check_slow_ok(mine, expected=count, nonce=ctx.nonce),
        )
    for branch in SLOW_TIMEOUT:
        mine = measured_of(records, "slow", branch.name)
        verdict = check_failed(mine, expected=count, accept=is_timeout, what="제한 시간")
        add_row(ctx, passno, "slow", branch.name, mine, verdict)
    # 제한 시간으로 끊긴 요청도 대역의 스레드는 지연을 끝까지 돈다. 다 끝난 뒤에 센다.
    expected = count * len(branches)
    deadline = time.monotonic() + SLOW_DELAY_MS / 1000 + 10
    while time.monotonic() < deadline:
        after = admin_counts(ctx)
        if delta(after["finished"], before["finished"])["sites_delayed"] == expected:
            break
        time.sleep(0.25)
    started = delta(after["started"], before["started"])
    finished = delta(after["finished"], before["finished"])
    matches = started["sites_delayed"] == expected and finished["sites_delayed"] == expected
    text = (
        f"대역이 받은 지연 요청 {started['sites_delayed']},"
        f" 끝낸 것 {finished['sites_delayed']}, 기대 {expected}"
    )
    ctx.rounds.record(
        f"p{passno}/slow/accounting", measured=matches, result="표지 맞음" if matches else text
    )
    ctx.notes.append(f"p{passno} slow: {text}")


def down_phase(ctx: Context, passno: int) -> None:
    args = ctx.args
    down = f"http://127.0.0.1:{ctx.down_port}"
    sacrificial = launch(
        ctx,
        f"admin-down-p{passno}",
        [
            sys.executable,
            str(HERE / "admin_stub.py"),
            "--port",
            str(ctx.down_port),
            "--run-token",
            f"{ctx.token}-down",
        ],
        env={**os.environ, "PROBE_DSN": ctx.dsn},
    )
    wait_for("내릴 대역", answers_with(f"{down}/__stats", f"{ctx.token}-down"), timeout=90)
    prime_steps: list[dict] = [
        {
            "kind": "rr",
            "label": "down-prime",
            "count": 1,
            "warmup": 0,
            "branches": [branch.step_entry() for branch in DOWN_PRIME],
        }
    ]
    primes = run_loadgen(ctx, f"p{passno}-down-prime", prime_steps, timeout=120)
    prime_ok = True
    for branch in DOWN_PRIME:
        mine = measured_of(primes, "down-prime", branch.name)
        problems, _ = check_served(mine, branch, expected=1, nonce=ctx.nonce, concurrency=1)
        prime_ok = prime_ok and not problems
    ctx.other_site_scans += http_json(f"{down}/__stats")["finished"]["sites"]
    outcome = stop(sacrificial)
    refused_before, seconds_before, saw_before = refusal(ctx.down_port)
    main_before = admin_counts(ctx)
    seq_branches = [*DOWN, DOWN_TIMEOUT]
    steps: list[dict] = [
        {
            "kind": "rr",
            "label": "down-seq",
            "count": args.down_count,
            "warmup": 0,
            "timeout_ms": 60000,
            "branches": [branch.step_entry() for branch in seq_branches],
        },
        {
            "kind": "chunks",
            "label": "down-conc10",
            "count": args.concurrency,
            "chunk": args.concurrency,
            "concurrency": args.concurrency,
            "warmup": 0,
            "timeout_ms": 60000,
            "branches": [branch.step_entry() for branch in DOWN],
        },
    ]
    records = run_loadgen(ctx, f"p{passno}-down", steps, timeout=900)
    refused_after, seconds_after, saw_after = refusal(ctx.down_port)
    main_after = admin_counts(ctx)
    untouched = not any(delta(main_after["started"], main_before["started"]).values())
    setup = prime_ok and outcome == "껐다" and refused_before and refused_after and untouched
    setup_text = (
        f"내리기 전 답함 {prime_ok}, 끄기 '{outcome}', 끈 뒤 파이썬 소켓 {saw_before}"
        f"({seconds_before:.3f}초), 잰 뒤 {saw_after}({seconds_after:.3f}초),"
        f" 살아 있는 대역에 닿은 요청 없음 {untouched}"
    )
    ctx.rounds.record(
        f"p{passno}/down/setup", measured=setup, result="표지 맞음" if setup else setup_text
    )
    ctx.notes.append(f"p{passno} down: {setup_text}")
    for step, expected, branches in (
        ("down-seq", args.down_count, seq_branches),
        ("down-conc10", args.concurrency, DOWN),
    ):
        for branch in branches:
            mine = measured_of(records, step, branch.name)
            if branch is DOWN_TIMEOUT:
                verdict = check_failed(
                    mine,
                    expected=expected,
                    accept=lambda call: is_refused(call) or is_timeout(call),
                    what="연결 거절이나 제한 시간",
                )
            else:
                verdict = check_failed(mine, expected=expected, accept=is_refused, what="연결 거절")
            if not setup:
                verdict = ([*verdict[0], "대역이 내려가 있었다는 표지가 없다"], verdict[1])
            add_row(ctx, passno, step, branch.name, mine, verdict)


def pgbench_phase(ctx: Context, passno: int) -> None:
    """대역이 보내는 것과 같은 세 문장(BEGIN, 사이트 목록 SELECT, COMMIT)을 컨테이너 안에서
    pgbench 로 돌려 거래마다의 시간을 잰다. 호스트의 대역이 잰 조회 시간과 견줄 값이다. 호스트에서
    컨테이너로 가는 길(Docker Desktop 의 포트 전달)을 지나지 않는다."""
    count = ctx.args.count
    prefix = f"/tmp/pgbench-p{passno}"
    script = "BEGIN;\n" + " ".join(SITES_SQL.split()) + ";\nCOMMIT;\n"
    written = subprocess.run(
        ["docker", "exec", "-i", ctx.container, "sh", "-c", "cat > /tmp/probe_sites.sql"],
        input=script,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    bench = run(
        [
            "docker",
            "exec",
            ctx.container,
            "pgbench",
            "-n",
            "-h",
            "127.0.0.1",
            "-U",
            "postgres",
            "-f",
            "/tmp/probe_sites.sql",
            "-c",
            "1",
            "-t",
            str(count),
            "-l",
            f"--log-prefix={prefix}",
            "postgres",
        ],
        timeout=600,
    )
    logged = run(["docker", "exec", ctx.container, "sh", "-c", f"cat {prefix}.*"], timeout=60)
    latencies = [int(line.split()[2]) / 1000 for line in logged.stdout.splitlines() if line.strip()]
    problems: list[str] = []
    if written.returncode != 0 or bench.returncode != 0:
        problems.append(f"pgbench 종료 코드 {bench.returncode}: {bench.stderr.strip()[:200]}")
    if f"number of transactions actually processed: {count}/{count}" not in bench.stdout:
        problems.append("pgbench 가 거래를 다 처리했다는 줄이 없다")
    if "number of failed transactions: 0 " not in bench.stdout:
        problems.append("pgbench 의 실패한 거래가 0 이라는 줄이 없다")
    if len(latencies) != count:
        problems.append(f"거래 기록이 {len(latencies)}줄이다(기대 {count})")
    ctx.other_site_scans += len(latencies)
    row = Row(
        passno, "db", "pgbench-in-container", not problems, problems, {"logged": len(latencies)}
    )
    with ctx.rounds.round(f"p{passno}/db/pgbench-in-container") as current:
        if not problems:
            row.client = stats_of(latencies)
        current.mark(
            measured=not problems, result="표지 맞음" if not problems else "; ".join(problems)
        )
    ctx.rows.append(row)


def run_pass(ctx: Context, passno: int) -> None:
    ctx.nonce = secrets.token_hex(8)
    set_nonce(ctx.dsn, ctx.nonce)
    load = host_load()
    log(f"되풀이 {passno} 시작(호스트 CPU 부하 {load}%)")
    ctx.notes.append(f"p{passno} 시작 때 호스트 CPU 부하 {load}%")
    phase(ctx, f"p{passno}/main/phase", lambda: main_phase(ctx, passno))
    load = host_load()
    ctx.notes.append(f"p{passno} 요청 단계 뒤 호스트 CPU 부하 {load}%")
    log(f"되풀이 {passno}: 컨테이너 안의 pgbench(호스트 CPU 부하 {load}%)")
    phase(ctx, f"p{passno}/db/phase", lambda: pgbench_phase(ctx, passno))
    log(f"되풀이 {passno}: 느린 대역")
    phase(ctx, f"p{passno}/slow/phase", lambda: slow_phase(ctx, passno))
    log(f"되풀이 {passno}: 내려간 대역")
    phase(ctx, f"p{passno}/down/phase", lambda: down_phase(ctx, passno))
    load = host_load()
    log(f"되풀이 {passno} 끝(호스트 CPU 부하 {load}%)")
    ctx.notes.append(f"p{passno} 끝 때 호스트 CPU 부하 {load}%")


# ---------------------------------------------------------------------------------------------
# 답하지 않는 대역(--hang)


def start_hang(ctx: Context) -> list[tuple[Branch, subprocess.Popen[bytes], Path]]:
    """갈래마다 요청 하나를 뒤에서 띄운다. fetch 의 기본 제한 시간이 5분이라 끝에서 거둔다."""
    started: list[tuple[Branch, subprocess.Popen[bytes], Path]] = []
    for branch in HANG:
        steps: list[dict] = [
            {
                "kind": "rr",
                "label": "hang",
                "count": 1,
                "warmup": 0,
                "timeout_ms": HANG_CLIENT_TIMEOUT_MS,
                "branches": [branch.step_entry()],
            }
        ]
        argv, out = loadgen_argv(ctx, branch.name, steps)
        process = subprocess.Popen(
            argv, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, stdin=subprocess.DEVNULL
        )
        started.append((branch, process, out))
    return started


def collect_hang(
    ctx: Context, started: list[tuple[Branch, subprocess.Popen[bytes], Path]], hole: Blackhole
) -> None:
    for branch, process, out in started:
        label = f"p0/hang/{branch.name}"
        with ctx.rounds.round(label) as current:
            process.wait(timeout=HANG_CLIENT_TIMEOUT_MS / 1000 + 60)
            records = measured_of(read_records(out), "hang", branch.name)
            held = sum(1 for line in hole.request_lines if line.startswith("GET /sites"))
            record = records[0]
            calls = calls_of(record)
            if record.get("client_error"):
                seen = f"보내는 쪽 {record['client_error'].get('code')}"
            else:
                seen = error_label(calls[0]) if calls else "호출 없음"
            row = Row(0, "hang", branch.name, held == len(HANG), [], {"seen": seen, "held": held})
            row.client = stats_of([record["ms"]])
            ctx.rows.append(row)
            current.mark(
                measured=held == len(HANG),
                result=f"{seen}, {record['ms'] / 1000:.1f}초"
                if held == len(HANG)
                else f"답하지 않는 소켓이 받은 요청 줄이 {held}개다",
            )


# ---------------------------------------------------------------------------------------------
# 결과


def fmt(value: float) -> str:
    return f"{value:.2f}"


def print_tables(ctx: Context) -> dict[str, object]:
    passes = sorted({row.passno for row in ctx.rows if row.passno > 0})
    keys: list[tuple[str, str]] = []
    for row in ctx.rows:
        if (row.step, row.branch) not in keys:
            keys.append((row.step, row.branch))
    quiet = {NONE.name, IDLE_NONE.name}
    baseline = {
        (row.passno, row.step): row.client
        for row in ctx.rows
        if row.branch in quiet and row.client is not None
    }
    print("\n## 되풀이마다(ms)\n")
    print(
        "앞의 다섯 칸은 요청을 보낸 쪽에서 잰 시간, `+중앙값`·`+p95` 는 같은 되풀이 같은 단계의"
        " 기준 갈래와의 차, `대역 대기` 는 페이지 대역이 대역을 기다린 시간, `조회` 는 대역이 적은"
        " 조회 시간, `왕복` 은 호출이 하나인 요청에서 대기에서 조회를 뺀 나머지다"
        "(뒤의 셋은 중앙값 / p95).\n"
    )
    print(
        "| 단계 | 갈래 | 되풀이 | n | 중앙값 | p95 | p99 | 최댓값 | +중앙값 | +p95"
        " | 대역 대기 | 조회 | 왕복 |"
    )
    print("|---|---|---|---|---|---|---|---|---|---|---|---|---|")

    def pair(stats: dict[str, float] | None) -> str:
        return "" if stats is None else f"{fmt(stats['median'])} / {fmt(stats['p95'])}"

    for row in ctx.rows:
        if row.client is None:
            continue
        base = baseline.get((row.passno, row.step))
        skip = base is None or row.branch in quiet
        added = "" if skip or base is None else fmt(row.client["median"] - base["median"])
        added95 = "" if skip or base is None else fmt(row.client["p95"] - base["p95"])
        print(
            f"| {row.step} | {row.branch} | {row.passno} | {int(row.client['n'])} |"
            f" {fmt(row.client['median'])} | {fmt(row.client['p95'])} | {fmt(row.client['p99'])} |"
            f" {fmt(row.client['max'])} | {added} | {added95} | {pair(row.upstream)} |"
            f" {pair(row.database)} | {pair(row.hop)} |"
        )
    print("\n## 되풀이 사이의 차이(ms)\n")
    print(
        "| 단계 | 갈래 | 되풀이마다의 중앙값 | 중앙값의 범위 | 되풀이마다의 p95"
        " | p95 의 범위 | 되풀이마다의 최댓값 |"
    )
    print("|---|---|---|---|---|---|---|")
    spread: dict[str, object] = {}
    for step, branch in keys:
        mine = [
            row
            for row in ctx.rows
            if (row.step, row.branch) == (step, branch) and row.client and row.passno in passes
        ]
        if not mine:
            continue
        medians = [row.client["median"] for row in mine if row.client]
        p95s = [row.client["p95"] for row in mine if row.client]
        maxes = [row.client["max"] for row in mine if row.client]
        spread[f"{step}/{branch}"] = {"medians": medians, "p95s": p95s, "maxes": maxes}
        print(
            f"| {step} | {branch} | {' / '.join(fmt(value) for value in medians)} |"
            f" {fmt(max(medians) - min(medians))} | {' / '.join(fmt(value) for value in p95s)} |"
            f" {fmt(max(p95s) - min(p95s))} | {' / '.join(fmt(value) for value in maxes)} |"
        )
    print("\n## 표지의 관찰\n")
    for row in ctx.rows:
        print(f"- p{row.passno}/{row.step}/{row.branch}: 측정 {row.measured}, {row.details}")
    print("\n## 참고\n")
    for note in ctx.notes:
        print(f"- {note}")
    return spread


def versions(ctx: Context) -> dict[str, object]:
    ready = http_json(f"{ctx.portal}/__ready")
    stats = http_json(f"{ctx.admin}/__stats")
    image = run(["docker", "image", "inspect", "--format", "{{.Id}}", PG_IMAGE], timeout=60)
    return {
        "date": datetime.now(UTC).astimezone().isoformat(timespec="seconds"),
        "platform": platform.platform(),
        "cpu_count": os.cpu_count(),
        "python": platform.python_version(),
        "psycopg": psycopg.__version__,
        "libpq": psycopg.pq.version(),
        "psycopg_impl": psycopg.pq.__impl__,
        "node": ready.get("node"),
        "undici": ready.get("undici"),
        "admin_http_parser": stats.get("http_parser"),
        "admin_pool": stats.get("pool"),
        "postgres": server_version(ctx.dsn),
        "postgres_image": image.stdout.strip(),
        **{
            name: package_version(name)
            for name in ("fastapi", "uvicorn", "psycopg-pool", "starlette")
        },
    }


def package_version(name: str) -> str:
    from importlib.metadata import PackageNotFoundError, version

    try:
        return version(name)
    except PackageNotFoundError:
        return ""


def check_db_scans(ctx: Context, baseline: dict[str, int], finished: dict[str, int]) -> None:
    """대역을 내린 뒤 PostgreSQL 통계의 표 훑기 수를 대역이 끝낸 조회의 수와 맞댄다. 사이트 표는
    내려간 대역의 자리에 잠깐 띄운 대역과 컨테이너 안의 pgbench 도 훑으므로 그 수를 더한다. 통계는
    백엔드가 끝나거나 쉴 때 실리므로 20초까지 기다린다."""
    expected = {
        "probe_sites": finished["sites"] + ctx.other_site_scans,
        "probe_accounts": finished["whoami"],
    }
    seen: dict[str, int] = {}
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        now = scans(ctx.dsn)
        seen = {name: now.get(name, 0) - baseline.get(name, 0) for name in expected}
        if seen == expected:
            break
        time.sleep(0.5)
    ctx.rounds.record(
        "run/db-scans",
        measured=seen == expected,
        result="표지 맞음" if seen == expected else f"통계 {seen}, 대역이 끝낸 조회 {expected}",
    )
    ctx.notes.append(f"PostgreSQL 통계의 표 훑기 수 {seen}, 대역이 끝낸 조회 {expected}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="settings_fetch 측정")
    parser.add_argument("--passes", type=int, default=3, help="되풀이 수")
    parser.add_argument("--gap-seconds", type=float, default=60, help="되풀이 사이에 쉬는 시간")
    parser.add_argument("--count", type=int, default=500, help="갈래마다 보내는 요청 수")
    parser.add_argument("--concurrency", type=int, default=10)
    parser.add_argument("--chunk", type=int, default=50, help="동시 단계에서 갈래를 바꾸는 묶음")
    parser.add_argument("--warmup", type=int, default=30, help="재기 전에 갈래마다 보내는 요청 수")
    parser.add_argument("--cache-count", type=int, default=300)
    parser.add_argument("--cache-gap-ms", type=int, default=50)
    parser.add_argument("--idle-count", type=int, default=5)
    parser.add_argument("--slow-count", type=int, default=3)
    parser.add_argument("--down-count", type=int, default=10)
    parser.add_argument(
        "--hang", action="store_true", help="답하지 않는 대역도 잰다(5분 넘게 걸린다)"
    )
    parser.add_argument("--work", type=Path, default=None, help="원본 기록을 둘 폴더")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    node = shutil.which("node")
    if node is None or shutil.which("docker") is None:
        print("node 와 docker 가 PATH 에 있어야 한다", file=sys.stderr)
        return 2
    token = secrets.token_hex(3)
    work = args.work or Path(tempfile.mkdtemp(prefix=f"settings-fetch-{token}-"))
    work.mkdir(parents=True, exist_ok=True)
    container = f"{CONTAINER_PREFIX}{token}"
    password = secrets.token_urlsafe(18)
    began = time.monotonic()
    log(f"실행 표지 {token}, 원본 기록 {work}")
    leftovers = run(
        ["docker", "ps", "-a", "--filter", f"name={CONTAINER_PREFIX}", "--format", "{{.Names}}"],
        timeout=60,
    ).stdout.split()
    if leftovers:
        log(f"앞선 실행이 남긴 컨테이너가 있다(이 실행은 지우지 않는다): {leftovers}")
    ctx: Context | None = None
    hole = Blackhole()
    exit_code = 1
    try:
        pg_port = start_postgres(container, password)
        dsn = f"host=127.0.0.1 port={pg_port} dbname=postgres user=postgres password={password}"
        wait_for("PostgreSQL", postgres_ready(dsn), timeout=120)
        baseline = seed(dsn, token)
        admin_port, alt_port, portal_port, down_port = (free_port() for _ in range(4))
        ctx = Context(
            args=args,
            token=token,
            work=work,
            node=node,
            container=container,
            dsn=dsn,
            admin=f"http://127.0.0.1:{admin_port}",
            portal=f"http://127.0.0.1:{portal_port}",
            down_port=down_port,
        )
        admin = launch(
            ctx,
            "admin",
            [
                sys.executable,
                str(HERE / "admin_stub.py"),
                "--port",
                str(admin_port),
                "--port",
                str(alt_port),
                "--run-token",
                token,
            ],
            env={**os.environ, "PROBE_DSN": dsn},
        )
        portal = launch(
            ctx,
            "portal",
            [
                node,
                str(HERE / "portal_stub.mjs"),
                "--port",
                str(portal_port),
                "--admin",
                ctx.admin,
                "--alt",
                f"http://127.0.0.1:{alt_port}",
                "--down",
                f"http://127.0.0.1:{down_port}",
                "--hang",
                f"http://127.0.0.1:{hole.port}",
                "--run-token",
                token,
            ],
        )
        wait_for("위젯 관리 서버 대역", answers_with(f"{ctx.admin}/__stats", token), timeout=90)
        wait_for(
            "위젯 테스트 페이지 서버 대역", answers_with(f"{ctx.portal}/__ready", token), timeout=30
        )
        environment = versions(ctx)
        log(f"환경 {json.dumps(environment, ensure_ascii=False)}")
        hanging = start_hang(ctx) if args.hang else []
        for passno in range(1, args.passes + 1):
            if passno > 1:
                log(f"{args.gap_seconds:.0f}초 쉰다")
                time.sleep(args.gap_seconds)
            run_pass(ctx, passno)
        if hanging:
            log("답하지 않는 대역의 요청이 끝나기를 기다린다")
            collect_hang(ctx, hanging, hole)
        finished = admin_counts(ctx)["finished"]
        log(f"위젯 테스트 페이지 서버 대역: {stop(portal)}")
        log(f"위젯 관리 서버 대역: {stop(admin)}")
        check_db_scans(ctx, baseline, finished)
        spread = print_tables(ctx)
        summary = {
            "token": token,
            "environment": environment,
            "args": {name: str(value) for name, value in vars(args).items()},
            "rows": [vars(row) for row in ctx.rows],
            "spread": spread,
            "notes": ctx.notes,
            "rounds": [vars(entry) for entry in ctx.rounds.entries],
        }
        (work / "summary.json").write_text(
            json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8"
        )
        print()
        print(ctx.rounds.summary())
        exit_code = ctx.rounds.exit_code()
    finally:
        hole.close()
        # 자식 하나를 끄다 실패해도(명령줄 읽기나 taskkill 의 제한 시간) 나머지 자식과 컨테이너는
        # 정리한다.
        try:
            if ctx is not None:
                for child in ctx.children:
                    try:
                        outcome = stop(child)
                    except (OSError, subprocess.SubprocessError) as error:
                        log(f"정리: {child.name} 끄다가 실패했다({error})")
                        continue
                    if outcome != "이미 끝나 있었다":
                        log(f"정리: {child.name} {outcome}")
        finally:
            log(f"정리: 컨테이너 {container} {remove_postgres(container)}")
        log(f"걸린 시간 {time.monotonic() - began:.0f}초, 원본 기록 {work}")
    print(f"종료 코드 {exit_code}")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
