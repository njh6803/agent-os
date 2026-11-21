"""패키지 B 의 Alembic 환경. 부르는 쪽이 `config.attributes["connection"]` 에 넣은 연결을 쓴다.

패키지 A 의 `env.py` 와 글자가 같지만 따로 둔다. 표의 판을 패키지마다 따로 세기 때문이다.
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
