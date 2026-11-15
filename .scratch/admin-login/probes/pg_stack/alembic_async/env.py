"""Alembic 환경(비동기 엔진). URL 의 드라이버가 비동기뿐일 때 쓴다(`postgresql+asyncpg://`).

Alembic 의 async 템플릿과 같은 꼴이다. 비동기 연결 위에서 동기 마이그레이션 함수를 `run_sync` 로
돈다. `asyncio.run` 을 부르므로 이미 도는 이벤트 루프 안에서는 부르지 못한다.
"""

from __future__ import annotations

import asyncio

from alembic import context
from sqlalchemy import Connection, pool
from sqlalchemy.ext.asyncio import async_engine_from_config

config = context.config


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=None)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


asyncio.run(run_async_migrations())
