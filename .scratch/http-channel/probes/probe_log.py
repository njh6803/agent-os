"""본문 검증 오류가 서버 기록 한 줄에 무엇을 싣는가."""

from __future__ import annotations

import asyncio
import io
from typing import Annotated

import httpx
from fastapi import APIRouter, Body
from pydantic import BaseModel, ConfigDict

from agent_os.server import create_app


class StartRun(BaseModel):
    model_config = ConfigDict(extra="forbid")
    agent: str
    request: str


router = APIRouter()


@router.post("/runs")
async def start(body: Annotated[StartRun, Body()]) -> dict[str, str]:
    return {}


async def main() -> None:
    err = io.StringIO()
    app = create_app(plugins=object(), trace=object(), token="t", stderr=err)
    app.include_router(router)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://x") as c:
        body = {"agent": "calc", "principal": "mallory", "extra_secret": "sk-ant-XXXX"}
        r = await c.post("/runs", json=body, headers={"authorization": "Bearer t"})
        print(r.status_code, r.json()["violations"])
    print("서버 기록:", err.getvalue())


asyncio.run(main())
