"""plugin-toggle 명세의 주장 둘을 잰다.

1. FastAPI 요청 본문의 `bool` 필드는 느슨하게 "false"·0 을 받는가. `StrictBool` 이면 422 인가.
2. 동기 `def` 라우트는 스레드풀에서 돌고 `async def` 는 이벤트 루프 스레드에서 도는가.
3. 경로가 같은 GET `{name:path}` 라우트가 있을 때 PUT `.../{name}/enabled` 가 PUT 라우트에 닿는가.
"""

from __future__ import annotations

import asyncio
import threading

from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel, ConfigDict, StrictBool

app = FastAPI()
seen: dict[str, str] = {}


class Lax(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: bool


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")
    enabled: StrictBool


@app.put("/lax")
async def lax(body: Lax) -> dict[str, bool]:
    return {"enabled": body.enabled}


@app.put("/strict")
async def strict(body: Strict) -> dict[str, bool]:
    return {"enabled": body.enabled}


@app.get("/sync")
def sync_route() -> dict[str, str]:
    seen["sync"] = threading.current_thread().name
    return {}


@app.get("/async")
async def async_route() -> dict[str, str]:
    seen["async"] = threading.current_thread().name
    return {}


@app.get("/plugins/{kind}/{name:path}")
def read_plugin(kind: str, name: str) -> dict[str, str]:
    return {"route": "get", "name": name}


@app.put("/plugins/{kind}/{name:path}/enabled", status_code=204)
async def put_enabled(kind: str, name: str) -> None:
    seen["put_name"] = name


async def main() -> None:
    loop_thread = threading.current_thread().name
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
        for value in ["false", 0, "no", True]:
            lax_r = await c.put("/lax", json={"enabled": value})
            strict_r = await c.put("/strict", json={"enabled": value})
            print(
                f"value={value!r}: lax={lax_r.status_code} {lax_r.text}"
                f" strict={strict_r.status_code}"
            )
        await c.get("/sync")
        await c.get("/async")
        print(f"loop thread={loop_thread} sync={seen['sync']} async={seen['async']}")
        put_r = await c.put("/plugins/agent/calc/enabled")
        get_r = await c.get("/plugins/agent/calc/enabled")
        miss_r = await c.put("/plugins/agent/calc")
        print(f"PUT .../calc/enabled -> {put_r.status_code} name={seen.get('put_name')}")
        print(f"GET .../calc/enabled -> {get_r.status_code} {get_r.text}")
        print(f"PUT .../calc -> {miss_r.status_code}")


asyncio.run(main())
