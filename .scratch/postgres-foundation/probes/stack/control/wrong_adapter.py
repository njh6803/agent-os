"""양성 대조. 포트와 어긋난 어댑터 둘을 같은 조립 자리에 넘긴다.

pyright strict 가 이 파일의 두 호출을 오류로 내야, `proto/assembly.py` 의 오류 0 이 "맞대지
않아서"가 아니라 "맞아서"라는 뜻이 된다. 하나는 반환 타입이 다르고 하나는 메서드가 빠졌다.
"""

from __future__ import annotations

from fastapi import FastAPI
from proto.apps import gate_app


class WrongReturn:
    async def startup_problem(self) -> int:
        return 0

    async def close(self) -> None:
        return None


class MissingClose:
    async def startup_problem(self) -> str | None:
        return None


def wrong_return() -> FastAPI:
    return gate_app(WrongReturn())


def missing_close() -> FastAPI:
    return gate_app(MissingClose())
