"""칸의 차례를 틀린 읽기, `Table` 판(port_shape_async 대조군). 임시 사본의 대조군 나무에만 둔다.

`select` 의 차례(`failures`, `name`, …)와 행을 푸는 차례(`name`, `failures`, …)가 다르다. 칸을
이름에 묶은 `Table` 이라 푼 값이 타입을 지녀, 줄을 짓는 자리에서 타입 검사가 잡는지를 본다.
`reveal_type` 은 행의 타입을 드러낸다(NULL 을 받는 칸을 `Column[... | None]` 으로 적은 것이
실리는지).
"""

from __future__ import annotations

from typing import reveal_type

from agent_os.adapters.postgres.accounts import (
    FAILURES,
    LOCKED_UNTIL,
    NAME,
    PASSWORD_HASH,
    TIER,
    Row,
    as_tier,
)
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine


async def find_swapped(engine: AsyncEngine, name: str) -> Row | None:
    query = select(FAILURES, NAME, TIER, PASSWORD_HASH, LOCKED_UNTIL).where(NAME == name)
    async with engine.connect() as connection:
        found = (await connection.execute(query)).one_or_none()
    reveal_type(found)
    if found is None:
        return None
    row_name, failures, tier, password_hash, locked_until = found
    return Row(row_name, as_tier(tier), password_hash, failures, locked_until)
