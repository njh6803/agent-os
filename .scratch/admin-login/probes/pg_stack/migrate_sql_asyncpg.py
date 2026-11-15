"""표 관리 후보: 같은 번호 붙인 SQL 파일을 asyncpg 로 적용하는 러너. `migrate_sql.py` 의 짝이다."""

from __future__ import annotations

from pathlib import Path

import asyncpg
from model import as_str

LOCK_KEY = 4_211_009_001


async def apply(dsn: str, folder: Path) -> list[str]:
    applied: list[str] = []
    conn = await asyncpg.connect(dsn)
    try:
        await conn.execute("SELECT pg_advisory_lock($1)", LOCK_KEY)
        await conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations ("
            "version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now())"
        )
        rows = await conn.fetch("SELECT version FROM schema_migrations")
        done = {as_str(row["version"]) for row in rows}
        for path in sorted(folder.glob("*.sql")):
            if path.stem in done:
                continue
            async with conn.transaction():
                await conn.execute(path.read_text(encoding="utf-8"))
                await conn.execute("INSERT INTO schema_migrations (version) VALUES ($1)", path.stem)
            applied.append(path.stem)
        await conn.execute("SELECT pg_advisory_unlock($1)", LOCK_KEY)
    finally:
        await conn.close()
    return applied
