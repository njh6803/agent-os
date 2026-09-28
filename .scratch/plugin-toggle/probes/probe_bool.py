"""PUT 본문의 enabled: 기본 bool 과 엄격한 bool, 계약 스키마, verbatim 경로, 스레드."""

import asyncio
import json
import threading
from typing import Annotated

import httpx
from fastapi import FastAPI, Path, Response
from pydantic import BaseModel, ConfigDict, Field, StrictBool

import agent_os.http.routes  # noqa: F401  verbatim 변환기 등록이 부수 효과다
from agent_os.sdk import PLUGIN_NAME_PATTERN


class Loose(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    enabled: bool


class StrictField(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    enabled: Annotated[bool, Field(strict=True)]


class StrictType(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    enabled: StrictBool


seen = {}
app = FastAPI()


@app.put("/loose/{kind}/{name:verbatim}/enabled", status_code=204)
async def loose(
    kind: str, name: Annotated[str, Path(pattern=PLUGIN_NAME_PATTERN)], body: Loose
) -> Response:
    seen["loose"] = (name, body.enabled)
    return Response(status_code=204)


@app.put("/strictf/x", status_code=204)
async def strictf(body: StrictField) -> Response:
    return Response(status_code=204)


@app.put("/strictt/x", status_code=204)
async def strictt(body: StrictType) -> Response:
    return Response(status_code=204)


@app.get("/loose/{kind}/{name:verbatim}")
def get_one(kind: str, name: Annotated[str, Path(pattern=PLUGIN_NAME_PATTERN)]) -> dict[str, str]:
    return {"name": name, "thread": threading.current_thread().name}


@app.get("/async-thread")
async def async_thread() -> dict[str, str]:
    return {"thread": threading.current_thread().name}


async def main() -> None:
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t") as c:
        for value in [True, False, "false", "true", 0, 1, "no", "off", "0", 0.0, "f", None]:
            r1 = await c.put("/loose/agent/calc/enabled", json={"enabled": value})
            r2 = await c.put("/strictf/x", json={"enabled": value})
            r3 = await c.put("/strictt/x", json={"enabled": value})
            loc = r2.json()["detail"][0]["loc"] if r2.status_code == 422 else None
            print(
                f"{value!r:>8}: loose={r1.status_code} parsed={seen.pop('loose', None)}"
                f" strictField={r2.status_code} strictType={r3.status_code} loc={loc}"
            )
        print("--- routing")
        for method, path in [
            ("PUT", "/loose/agent/calc/enabled%0A"),
            ("PUT", "/loose/agent/calc/enabled"),
            ("PUT", "/loose/agent/a/enabled/enabled"),
            ("GET", "/loose/agent/calc/enabled"),
            ("PUT", "/loose/agent/calc"),
        ]:
            r = await c.request(method, path, json={"enabled": False})
            print(method, path, r.status_code, seen.pop("loose", None), r.text[:100])
        print("--- threads")
        print(
            (await c.get("/loose/agent/calc")).json(),
            (await c.get("/async-thread")).json(),
            threading.current_thread().name,
        )
    schema = app.openapi()["components"]["schemas"]
    print("--- schema")
    for n in ("Loose", "StrictField", "StrictType"):
        print(n, json.dumps(schema[n]["properties"]["enabled"]), schema[n].get("required"))


asyncio.run(main())
