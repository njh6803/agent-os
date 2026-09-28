"""첫 이벤트를 의존성에서 기다리면 실행 전 실패가 봉투가 되는가,
제너레이터 안에서 던지면 어떻게 되는가."""

from __future__ import annotations

import asyncio
import inspect
import sys
from collections.abc import AsyncIterator
from typing import Annotated, Literal

import httpx
from fastapi import APIRouter, Depends, FastAPI
from fastapi.sse import EventSourceResponse
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter

from agent_os.core.ports import PluginError
from agent_os.server import create_app


async def first_or_raise() -> str:
    raise PluginError("에이전트 플러그인이 없다: nope")


router = APIRouter()


@router.post("/runs/dep", response_class=EventSourceResponse)
async def via_dep(first: Annotated[str, Depends(first_or_raise)]) -> AsyncIterator[dict[str, str]]:
    yield {"first": first}


@router.post("/runs/gen", response_class=EventSourceResponse)
async def via_gen() -> AsyncIterator[dict[str, str]]:
    raise PluginError("에이전트 플러그인이 없다: nope")
    yield {}


async def main() -> None:
    app = create_app(plugins=object(), trace=object(), token="t", stderr=sys.stderr)
    app.include_router(router)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://x") as client:
        headers = {"authorization": "Bearer t"}
        r = await client.post("/runs/dep", headers=headers)
        print("dep:", r.status_code, r.headers.get("content-type"), r.text[:200])
        try:
            r = await client.post("/runs/gen", headers=headers)
            print("gen:", r.status_code, r.headers.get("content-type"), repr(r.text[:200]))
        except BaseException as error:
            print("gen: 예외로 올라옴", type(error).__name__, str(error)[:120])


class Approve(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision: Literal["approve"] = "approve"


class Deny(BaseModel):
    model_config = ConfigDict(extra="forbid")
    decision: Literal["deny"]
    reason: str


asyncio.run(main())
try:
    TypeAdapter(Annotated[Approve | Deny, Field(discriminator="decision")]).validate_python({})
    print("tag 없는 {} 통과")
except Exception as error:
    print("tag 없는 {}:", str(error).splitlines()[1:3])
print(
    "FastAPI openapi_version 인자:",
    "openapi_version" in inspect.signature(FastAPI.__init__).parameters,
)
