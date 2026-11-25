"""칸의 차례를 틀린 읽기, `text()` 판(port_shape_async 대조군). 임시 사본의 대조군 나무에만 둔다.

`accounts_order_table.py` 와 같은 틀림을 SQL 글(`text()`)로 짓는다. 행의 칸이 `Any` 라면 타입 검사가
틀림을 보지 못한다. `reveal_type` 은 이 파일을 분석했다는 표지이자 행의 타입이다.
"""

from __future__ import annotations

from typing import reveal_type

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine

from agent_os.adapters.postgres.accounts import Row, as_tier

_FIND = text(
    "SELECT failures, name, tier, password_hash, locked_until FROM accounts WHERE name = :name"
)


async def find_swapped_text(engine: AsyncEngine, name: str) -> Row | None:
    async with engine.connect() as connection:
        found = (await connection.execute(_FIND, {"name": name})).one_or_none()
    reveal_type(found)
    if found is None:
        return None
    row_name, failures, tier, password_hash, locked_until = found
    return Row(row_name, as_tier(tier), password_hash, failures, locked_until)
