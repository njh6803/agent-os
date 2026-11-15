"""표 관리 후보: 번호 붙인 SQL 파일을 작은 러너로 차례로 적용한다(psycopg 동기).

파일 이름의 stem 이 판이고 이름 순서대로 적용한다. 적용한 판은 `schema_migrations` 표에 남긴다.
세션 수준의 권고 잠금으로 러너 둘이 함께 떠도 한쪽이 기다렸다가 남은 것만 적용한다. 파일 하나와
그 판을 적는 일은 한 트랜잭션이다. 파일에는 문장이 여럿이라 매개변수 없이 한 번에 보낸다.

psycopg 의 `execute` 는 질의를 `LiteralString`·`bytes`·`sql.SQL` 로만 받는다. 파일에서 읽은 `str` 은
pyright 오류라 바이트로 읽어 넘긴다.
"""

from __future__ import annotations

from pathlib import Path

import psycopg
from model import as_str

LOCK_KEY = 4_211_009_001


def apply(dsn: str, folder: Path) -> list[str]:
    """적용한 판의 목록을 돌려준다."""
    applied: list[str] = []
    with psycopg.connect(dsn, autocommit=True) as conn:
        conn.execute("SELECT pg_advisory_lock(%s)", (LOCK_KEY,))
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            "version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
        )
        done = {as_str(row[0]) for row in conn.execute("SELECT version FROM schema_migrations")}
        for path in sorted(folder.glob("*.sql")):
            if path.stem in done:
                continue
            with conn.transaction():
                conn.execute(path.read_bytes())
                conn.execute("INSERT INTO schema_migrations (version) VALUES (%s)", (path.stem,))
            applied.append(path.stem)
        conn.execute("SELECT pg_advisory_unlock(%s)", (LOCK_KEY,))
    return applied
