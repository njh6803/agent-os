"""조립의 시제품 둘. 데이터베이스를 확인하는 자리가 다르다.

`gate_app` 은 순수 ASGI 미들웨어(`gate.DatabaseGate`)가, `lifespan_app` 은 FastAPI 의 수명 함수가
확인한다. 뒤의 것은 문제가 있으면 예외를 던진다. uvicorn 이 둘을 어떻게 찍는지 견주려는 것이다.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from proto.gate import DatabaseGate
from proto.port import Database


class DatabaseNotReady(RuntimeError):
    """`lifespan_app` 이 던지는 예외."""


def gate_app(database: Database) -> FastAPI:
    app = FastAPI()
    app.add_middleware(DatabaseGate, database=database)
    return app


def lifespan_app(database: Database) -> FastAPI:
    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
        problem = await database.startup_problem()
        if problem is not None:
            await database.close()
            raise DatabaseNotReady(problem)
        try:
            yield
        finally:
            await database.close()

    return FastAPI(lifespan=lifespan)
