"""alembic 환경. 객체가 `config.attributes["connection"]` 으로 넘긴 연결 위에서만 돈다.

주소도 엔진도 여기서 만들지 않는다. 그래서 스스로 이벤트 루프를 열지 않고(이미 도는 루프 안에서도
적용된다) `alembic.ini` 도 없다. Agent OS 의 같은 이름 파일의 사본이다(ADR 0064).
"""

from __future__ import annotations

from alembic import context
from sqlalchemy import Connection


def run() -> None:
    connection = context.config.attributes.get("connection")
    if not isinstance(connection, Connection):
        raise RuntimeError("마이그레이션은 객체가 넘긴 연결로만 돈다")
    context.configure(connection=connection, target_metadata=None)
    with context.begin_transaction():
        context.run_migrations()


run()
