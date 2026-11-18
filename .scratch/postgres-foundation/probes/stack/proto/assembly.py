"""조립 자리의 시제품. 어댑터(`PostgresDatabase`)를 포트(`port.Database`)를 받는 자리에 넘긴다.

pyright strict 가 이 파일에서 오류를 내지 않으면, 포트를 import 하지 않는 어댑터가 실제 SQLAlchemy
타입과 비동기 메서드로 그 포트를 시그니처만으로 만족한다는 뜻이다. 맞대는 것은 이 자리의 호출이다.
"""

from __future__ import annotations

from fastapi import FastAPI

from proto.apps import gate_app
from proto.database import PostgresDatabase, parse_url


def assemble(text: str) -> FastAPI | None:
    url = parse_url(text)
    if url is None:
        return None
    return gate_app(PostgresDatabase(url))
