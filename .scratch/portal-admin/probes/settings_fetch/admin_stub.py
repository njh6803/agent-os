"""위젯 관리 서버 대역과 "지금 누구인지" 대역. FastAPI 앱 하나의 두 경로다.

`run.py` 가 띄운다. 손으로 띄울 때는 `PROBE_DSN` 환경 변수에 연결 글을 넣고
`uv run --with "psycopg[binary,pool]" python admin_stub.py --port <포트> --run-token <표지>` 다.
`--port` 를 여러 번 주면 같은 앱이 그 포트 모두에서 듣는다. 페이지 대역의 fetch 는 주소(출처)마다
연결 묶음을 따로 두므로, `Connection: close` 를 보내는 갈래가 이어 쓰는 갈래의 연결을 닫지 않게
하려고 둘째 포트를 쓴다.

- `GET /sites`: PostgreSQL 에서 사이트 열 줄과 회차 표지(nonce)를 `SELECT` 해 JSON 으로 답한다.
  `delay_ms` 를 주면 조회 앞에 데이터베이스에서 그만큼 잔다(`pg_sleep`). 느린 대역의 갈래가 쓴다.
- `GET /whoami`: 요청의 쿠키 값을 해시해 계정 하나를 찾아 짧은 JSON 으로 답한다. Agent OS 서버의
  "지금 누구인지" 경로를 흉내 낸 가벼운 조회다.
- `GET /__stats`: 경로마다 받은 요청과 끝낸 조회의 수. 데이터베이스를 부르지 않는다.

답의 `probe` 칸이 표지다. `seq`(이 프로세스가 그 경로로 받은 요청의 일련번호), `rows`, `nonce`
(데이터베이스에서 읽은 값), `client_port` 와 `connection`(이 서버가 본 상대 포트와 `Connection`
헤더), `query_ms`(연결을 빌려 조회를 끝내기까지)다.

전제와 고른 것.
- 드라이버는 psycopg 3 의 동기 연결 묶음(`psycopg_pool.ConnectionPool`)이고 경로 함수는 `def` 다.
  FastAPI 가 스레드 풀에서 돌린다. 윈도의 기본 이벤트 루프(Proactor)에서 psycopg 의 비동기 모드가
  거부되는 것은 `.scratch/admin-login/probes/pg_stack/` 이 쟀다. 이 저장소의 데이터베이스 도구는
  아직 정해지지 않았다.
- 연결은 psycopg 의 기본값(autocommit 끔)이라 요청 하나가 `BEGIN`, `SELECT`, `COMMIT` 을 보낸다.
- 비밀번호가 든 연결 글은 환경 변수로만 받고 명령줄에 싣지 않는다. `--run-token` 은 이 회차의
  표지라 명령줄에 싣는다. `run.py` 가 끄기 전에 명령줄에서 이 표지를 본다.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import os
import socket
import threading
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from psycopg_pool import ConnectionPool

SITES_SQL = """
SELECT s.name, s.issuer, s.assurance_mode, s.report_link, s.public_origin, s.login_entry,
       n.nonce, pg_backend_pid()
FROM probe_sites AS s CROSS JOIN probe_nonce AS n
ORDER BY s.name
"""

WHOAMI_SQL = """
SELECT a.username, a.role, n.nonce, pg_backend_pid()
FROM probe_accounts AS a CROSS JOIN probe_nonce AS n
WHERE a.session_hash = %s
"""

SESSION_COOKIE = "probe_session"


class Counters:
    """경로마다 받은 요청(`started`)과 조회를 끝낸 요청(`finished`)의 수. 경로 함수가 스레드 풀에서
    돌아 잠금으로 센다."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.started: dict[str, int] = {"sites": 0, "sites_delayed": 0, "whoami": 0}
        self.finished: dict[str, int] = {"sites": 0, "sites_delayed": 0, "whoami": 0}

    def start(self, name: str) -> int:
        with self._lock:
            self.started[name] += 1
            return self.started[name]

    def finish(self, name: str) -> None:
        with self._lock:
            self.finished[name] += 1

    def snapshot(self) -> dict[str, dict[str, int]]:
        with self._lock:
            return {"started": dict(self.started), "finished": dict(self.finished)}


def session_value(cookie_header: str | None) -> str:
    """`Cookie` 헤더에서 프로브 쿠키의 값을 꺼낸다. 없으면 빈 글이다."""
    for part in (cookie_header or "").split(";"):
        name, _, value = part.strip().partition("=")
        if name == SESSION_COOKIE:
            return value
    return ""


def create_app(dsn: str, run_token: str, pool_min: int, pool_max: int) -> FastAPI:
    pool = ConnectionPool(dsn, min_size=pool_min, max_size=pool_max, open=False)
    counters = Counters()

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
        pool.open()
        pool.wait(timeout=30)
        yield
        pool.close()

    app = FastAPI(lifespan=lifespan)

    def probe_fields(request: Request, seq: int, began: float) -> dict[str, object]:
        client = request.client
        return {
            "seq": seq,
            "client_port": client.port if client is not None else None,
            "connection": request.headers.get("connection"),
            "query_ms": round((time.perf_counter() - began) * 1000, 3),
        }

    @app.get("/sites")
    def sites(request: Request, delay_ms: int = 0) -> dict[str, object]:
        seq = counters.start("sites")
        if delay_ms > 0:
            counters.start("sites_delayed")
        began = time.perf_counter()
        with pool.connection() as connection:
            if delay_ms > 0:
                connection.execute("SELECT pg_sleep(%s)", (delay_ms / 1000,))
            rows = connection.execute(SITES_SQL).fetchall()
        probe = probe_fields(request, seq, began)
        counters.finish("sites")
        if delay_ms > 0:
            counters.finish("sites_delayed")
        probe.update(
            rows=len(rows),
            nonce=rows[0][6] if rows else None,
            backend_pid=rows[0][7] if rows else None,
            delay_ms=delay_ms,
        )
        return {
            "sites": [
                {
                    "name": row[0],
                    "issuer": row[1],
                    "assurance_mode": row[2],
                    "report_link": row[3],
                    "public_origin": row[4],
                    "login_entry": row[5],
                }
                for row in rows
            ],
            "probe": probe,
        }

    @app.get("/whoami")
    def whoami(request: Request) -> dict[str, object]:
        seq = counters.start("whoami")
        digest = hashlib.sha256(session_value(request.headers.get("cookie")).encode()).hexdigest()
        began = time.perf_counter()
        with pool.connection() as connection:
            row = connection.execute(WHOAMI_SQL, (digest,)).fetchone()
        probe = probe_fields(request, seq, began)
        counters.finish("whoami")
        probe.update(
            rows=0 if row is None else 1,
            nonce=None if row is None else row[2],
            backend_pid=None if row is None else row[3],
        )
        return {
            "username": None if row is None else row[0],
            "role": None if row is None else row[1],
            "probe": probe,
        }

    @app.get("/__stats")
    def stats() -> dict[str, object]:
        return {
            "run_token": run_token,
            "pid": os.getpid(),
            "http_parser": "httptools" if importlib.util.find_spec("httptools") else "h11",
            "pool": {"min": pool_min, "max": pool_max},
            **counters.snapshot(),
        }

    return app


def bind(port: int) -> socket.socket:
    listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listener.bind(("127.0.0.1", port))
    return listener


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, action="append", required=True)
    parser.add_argument("--run-token", required=True)
    parser.add_argument("--pool-min", type=int, default=4)
    parser.add_argument("--pool-max", type=int, default=10)
    args = parser.parse_args()
    dsn = os.environ.get("PROBE_DSN", "")
    if not dsn:
        raise SystemExit("PROBE_DSN 환경 변수에 연결 글이 없다")
    config = uvicorn.Config(
        create_app(dsn, args.run_token, args.pool_min, args.pool_max),
        log_level="warning",
        access_log=False,
    )
    uvicorn.Server(config).run(sockets=[bind(port) for port in args.port])


if __name__ == "__main__":
    main()
