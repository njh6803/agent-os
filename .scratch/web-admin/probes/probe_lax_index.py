"""결정 본문에 `Annotated[int, Field(ge=0)]` 필드를 채널 모델 모양대로 더하면
FastAPI 가 무엇을 받는가.

web-admin 명세 검토가 쟀다. 채널의 본문 모델과 같은 설정(`extra="forbid"`,
`frozen=True`)에 자리 필드를 lax 와 `strict=True` 로 둔 두 모델을 세우고,
정수·문자열·실수·불린·소수·음수 본문을 보낸다.
`uv run python .scratch/web-admin/probes/probe_lax_index.py`. 네트워크를 타지 않는다.
"""

import asyncio
from typing import Annotated, Literal

from fastapi import Body, FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel, ConfigDict, Field


class Lax(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    decision: Literal["approve"]
    at: Annotated[int, Field(ge=0)]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    decision: Literal["approve"]
    at: Annotated[int, Field(ge=0, strict=True)]


app = FastAPI()


@app.post("/lax")
async def lax(body: Annotated[Lax, Body()]) -> int:
    return body.at


@app.post("/strict")
async def strict(body: Annotated[Strict, Body()]) -> int:
    return body.at


CASES = [
    '{"decision":"approve","at":2}',
    '{"decision":"approve","at":"2"}',
    '{"decision":"approve","at":2.0}',
    '{"decision":"approve","at":true}',
    '{"decision":"approve","at":2.5}',
    '{"decision":"approve","at":-1}',
]


async def main() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        for path in ("/lax", "/strict"):
            for body in CASES:
                r = await c.post(path, content=body, headers={"content-type": "application/json"})
                print(path, body, r.status_code, r.text[:60])
    schema = app.openapi()["components"]["schemas"]
    print("lax schema", schema["Lax"]["properties"]["at"])
    print("strict schema", schema["Strict"]["properties"]["at"])


asyncio.run(main())
