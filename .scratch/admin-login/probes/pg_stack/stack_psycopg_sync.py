"""조합: psycopg 3 동기 모드. 계정 넣기, 이름으로 읽기, 실패 횟수 올리기(트랜잭션), 갱신용 번호."""

from __future__ import annotations

from datetime import datetime

import psycopg
from model import Account, as_int
from psycopg.rows import TupleRow, class_row

type Conn = psycopg.Connection[TupleRow]


def connect(dsn: str) -> Conn:
    return psycopg.connect(dsn, autocommit=True)


def server_version(conn: Conn) -> str:
    return conn.info.parameter_status("server_version") or ""


def add_account(conn: Conn, name: str, password_hash: str) -> int:
    row = conn.execute(
        "INSERT INTO accounts (name, password_hash) VALUES (%s, %s) RETURNING id",
        (name, password_hash),
    ).fetchone()
    if row is None:
        raise LookupError(name)
    return as_int(row[0])


def find_account(conn: Conn, name: str) -> Account | None:
    with conn.cursor(row_factory=class_row(Account)) as cursor:
        cursor.execute(
            "SELECT id, name, password_hash, failed_attempts, locked_until"
            " FROM accounts WHERE name = %s",
            (name,),
        )
        return cursor.fetchone()


def bump_failures(conn: Conn, name: str) -> int:
    """읽고 하나 올려 쓴다. 두 문장이 한 트랜잭션이고 줄을 잠근다."""
    with conn.transaction():
        row = conn.execute(
            "SELECT failed_attempts FROM accounts WHERE name = %s FOR UPDATE", (name,)
        ).fetchone()
        if row is None:
            raise LookupError(name)
        count = as_int(row[0]) + 1
        conn.execute("UPDATE accounts SET failed_attempts = %s WHERE name = %s", (count, name))
    return count


def add_refresh_token(conn: Conn, token_hash: bytes, account_id: int, expires_at: datetime) -> None:
    conn.execute(
        "INSERT INTO refresh_tokens (token_hash, account_id, expires_at) VALUES (%s, %s, %s)",
        (token_hash, account_id, expires_at),
    )


def delete_refresh_token(conn: Conn, token_hash: bytes) -> bool:
    deleted = conn.execute("DELETE FROM refresh_tokens WHERE token_hash = %s", (token_hash,))
    return deleted.rowcount == 1
