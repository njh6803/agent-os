"""패키지 A 의 Alembic 환경. 부르는 쪽이 `config.attributes["connection"]` 에 넣은 연결을 쓴다.

엔진을 만들지 않고 `asyncio.run` 도 부르지 않는다. 그래서 비동기 연결의 `run_sync` 안에서, 곧 이미
도는 이벤트 루프 안에서 불려도 된다. 연결이 없으면 엔진을 스스로 만드는 대신 멈춘다.
"""

from __future__ import annotations

from alembic import context
from sqlalchemy import Connection

connection = context.config.attributes.get("connection")
if not isinstance(connection, Connection):
    raise RuntimeError("config.attributes['connection'] 에 동기 연결이 없다")

context.configure(connection=connection, target_metadata=None)
with context.begin_transaction():
    context.run_migrations()
