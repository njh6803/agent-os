"""alembic 환경. 어댑터가 `config.attributes["connection"]` 으로 넘긴 연결 위에서만 돈다.

주소도 엔진도 여기서 만들지 않는다. 그래서 `asyncio.run` 을 부르지 않고 `alembic.ini` 도 없다.
"""

from __future__ import annotations

from alembic import context
from sqlalchemy import Connection


def run() -> None:
    connection = context.config.attributes.get("connection")
    if not isinstance(connection, Connection):
        raise RuntimeError("마이그레이션은 어댑터가 넘긴 연결로만 돈다")
    context.configure(connection=connection, target_metadata=None)
    with context.begin_transaction():
        context.run_migrations()


run()
