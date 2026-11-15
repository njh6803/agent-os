"""작업자마다 테스트가 돌아가도록 짧게 자는 테스트 서른둘. 저마다 픽스처의 DB 에 질의 하나를
한다."""

from __future__ import annotations

import time

import psycopg
import pytest


@pytest.mark.parametrize("index", range(32))
def test_query(index: int, pg_url: str) -> None:
    with psycopg.connect(pg_url) as conn:
        row = conn.execute("SELECT %s::int + 1", (index,)).fetchone()
    assert row == (index + 1,)
    time.sleep(0.3)
