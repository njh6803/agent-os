"""기대한 오류의 대조군. asyncpg-stubs 에서 풀이 빌려주는 연결은 `Connection` 의 하위 타입이 아니다.

`run.py` 는 이 파일에 `reportArgumentType` 오류가 정확히 하나 나는 것을 표지로 본다. 조합 모듈
`stack_asyncpg.py` 는 연결 타입을 둘의 합으로 적어 이 오류를 피한다.
"""

from __future__ import annotations

import asyncpg


async def first_value(conn: asyncpg.Connection[asyncpg.Record]) -> object:
    value: object = await conn.fetchval("SELECT 1")
    return value


async def from_pool(pool: asyncpg.Pool[asyncpg.Record]) -> object:
    async with pool.acquire() as conn:
        return await first_value(conn)
