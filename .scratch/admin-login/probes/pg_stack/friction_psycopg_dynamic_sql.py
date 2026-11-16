"""기대한 오류의 대조군. psycopg 의 `execute` 는 실행 때 만든 `str` 을 질의로 받지 않는다.

`run.py` 는 이 파일의 오류가 `read_text` 줄 하나에만 나는 것을 표지로 본다. 같은 내용을 바이트로
읽어 넘기는 둘째 호출에는 오류가 없어야 한다(`migrate_sql.py` 가 쓰는 길).
"""

from __future__ import annotations

from pathlib import Path

import psycopg
from psycopg.rows import TupleRow


def run_file(conn: psycopg.Connection[TupleRow], path: Path) -> None:
    conn.execute(path.read_text(encoding="utf-8"))
    conn.execute(path.read_bytes())
