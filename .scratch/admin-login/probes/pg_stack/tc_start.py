"""testcontainers 가 PostgreSQL 컨테이너 하나를 띄워 첫 질의가 답하기까지의 시간을 `RESULT <json>`
로 낸다.

프로세스 하나가 컨테이너 하나를 띄운다. 테스트 프로세스가 치르는 값을 보려는 것이라 가져오기 시간도
함께 적는다. `start()` 는 컨테이너 만들기와 준비 기다림(psql 로 질의가 될 때까지)을 품고, Ryuk 을
끄지 않았으면 그 프로세스의 첫 `start()` 가 Ryuk 컨테이너도 띄운다. 컨테이너 이름은 인자로 받는다
(`admin-login-pg-probe-` 접두). 측정의 셈은 `run.py` 가 한다.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time

BEGIN = time.monotonic()

import psycopg  # noqa: E402
from model import as_str  # noqa: E402
from testcontainers.community.postgres import PostgresContainer  # noqa: E402
from testcontainers.core.config import testcontainers_config  # noqa: E402
from testcontainers.core.labels import SESSION_ID  # noqa: E402


def main() -> int:
    image, name = sys.argv[1], sys.argv[2]
    imported = time.monotonic()
    container = PostgresContainer(image, driver=None).with_name(name)
    container.start()
    started = time.monotonic()
    try:
        with psycopg.connect(container.get_connection_url()) as conn:
            row = conn.execute("SHOW server_version").fetchone()
            version = as_str(row[0]) if row is not None else ""
        answered = time.monotonic()
        listed = subprocess.run(
            ["docker", "ps", "--filter", f"name=testcontainers-ryuk-{SESSION_ID}", "-q"],
            capture_output=True,
            encoding="utf-8",
            timeout=30,
            check=False,
        )
        ryuk_containers = len(listed.stdout.split())
        answered_after_listing = time.monotonic()
    finally:
        container.stop()
    stopped = time.monotonic()
    result = {
        "name": name,
        "server_version": version,
        "ryuk_disabled": testcontainers_config.ryuk_disabled,
        "ryuk_containers": ryuk_containers,
        "ryuk_image": testcontainers_config.ryuk_image,
        "import_seconds": round(imported - BEGIN, 2),
        "start_seconds": round(started - imported, 2),
        "first_query_seconds": round(answered - started, 2),
        "stop_seconds": round(stopped - answered_after_listing, 2),
    }
    print(f"RESULT {json.dumps(result)}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
