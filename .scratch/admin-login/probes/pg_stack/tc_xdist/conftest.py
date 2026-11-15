"""세션 범위 픽스처 하나가 testcontainers 로 PostgreSQL 을 띄운다.

pytest-xdist 로 나눠 돌 때 이 픽스처가 프로세스마다 따로 도는지를 보려는 것이다. 픽스처가 뜰 때마다
작업자 이름과 컨테이너 ID 와 걸린 시간을 `PG_PROBE_OUT` 파일에 한 줄씩 덧붙인다. 컨테이너 이름은
`PG_PROBE_PREFIX`(`admin-login-pg-probe-<토큰>`)에 작업자 이름을 붙인다.
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Generator
from pathlib import Path

import pytest
from testcontainers.community.postgres import PostgresContainer

IMAGE_ENV = "PG_PROBE_IMAGE"
OUT_ENV = "PG_PROBE_OUT"
PREFIX_ENV = "PG_PROBE_PREFIX"


@pytest.fixture(scope="session")
def pg_url(worker_id: str) -> Generator[str]:
    begin = time.monotonic()
    name = f"{os.environ[PREFIX_ENV]}-{worker_id}"
    with PostgresContainer(os.environ[IMAGE_ENV], driver=None).with_name(name) as container:
        record = {
            "worker": worker_id,
            "pid": os.getpid(),
            "container": name,
            "start_seconds": round(time.monotonic() - begin, 2),
        }
        with Path(os.environ[OUT_ENV]).open("a", encoding="utf-8") as out:
            out.write(json.dumps(record) + "\n")
        yield container.get_connection_url()
