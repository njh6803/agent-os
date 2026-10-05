"""최종 사용자 스트림이 프레임마다 SSE `id` 를 싣고도 계약에 항목 유니온이 이름 있는
컴포넌트로 서는지.

ADR 0023 은 "프레임마다 SSE `id` 가 그 항목의 근거인 트레이스 인덱스다"와 "항목 타입은
생성되지 않으므로 소비자가 판별자 술어로 좁힌다(이름 있는 컴포넌트)"를 함께 정했다. 설치된
FastAPI 는 SSE 프레임에 `id:` 를 실으려면 `fastapi.sse.ServerSentEvent` 를 yield 해야
하고, 그 타입은 스트림 항목 타입에서 빠진다(라우팅 층의 주석 "transport wrapper, not a
data model"). 그래서 `id` 와 이름 있는 항목 스키마를 함께 얻는 길이 있는지 모양 넷을 놓고, 그중
셋(A, C, E)은 여기서 돌리고 B 는 pyright 가 거부하는 모양이라 `check_types.py` 에서만 잰다.

- A: 반환 주해가 `AsyncIterator[ServerSentEvent]`. `id` 는 실리지만 항목 스키마가
  정형(`data: string`)이다.
- B: 반환 주해가 `AsyncIterator[EndUserItem]`(판별 유니온 별칭)인데 런타임은
  `ServerSentEvent` 를 yield. 계약은 맞지만 주해와 실제 yield 타입이 달라 pyright strict 가
  거부한다(`check_types.py`). 타입 우회 없이는 못 쓴다.
- C: 반환 주해가 별칭 `EndUserFrame = EndUserItem | SkipJsonSchema[ServerSentEvent]`.
  pydantic 의 `SkipJsonSchema` 가 스키마에서 그 멤버를 지우고, 타입으로는 유니온 멤버라
  `ServerSentEvent` yield 가 주해와 맞는다. 계약에 `EndUserFrame` 이 `EndUserItem` 을
  가리키는 별칭 컴포넌트로 하나 더 선다.
- E: C 와 같은 유니온을 별칭 없이 주해에 바로 쓴다. 항목 스키마가 `EndUserItem` 을 바로
  가리킨다.

각 모양에서 (1) 응답 바이트에 `id:` 줄이 있는지, (2) `app.openapi()` 의
`itemSchema.properties.data` 가 무엇을 가리키는지, (3) 컴포넌트 목록을 찍는다. C 와 E 에서
pydantic 단독(`TypeAdapter(...).json_schema()`)은 건너뛴 멤버의 정의를 남기지 않지만
FastAPI 의 정의 수집(`get_definitions`)은 `ServerSentEvent` 를 어디서도 가리키지 않는
컴포넌트로 남긴다 — 그것도 찍는다. pyright 판정은 `check_types.py` 가 이 파일의 모양 B 와
C 를 `tests/` 아래로 복사해 잰다.

    PYTHONUTF8=1 uv run python .scratch/end-user-channel/probes/sse_id_frames.py
"""

from __future__ import annotations

import asyncio
import json
import re
from collections.abc import AsyncIterator
from typing import Annotated, Literal

import httpx
from fastapi import FastAPI
from fastapi.sse import EventSourceResponse, ServerSentEvent
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter
from pydantic.json_schema import SkipJsonSchema


class Started(BaseModel):
    """실행이 시작됐다."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    type: Literal["started"] = "started"
    run_id: str


class Finished(BaseModel):
    """실행이 출력을 내고 끝났다."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    type: Literal["finished"] = "finished"
    output: str


type EndUserItem = Annotated[Started | Finished, Field(discriminator="type")]
type EndUserFrame = EndUserItem | SkipJsonSchema[ServerSentEvent]


def build() -> FastAPI:
    app = FastAPI()

    @app.post("/a", response_class=EventSourceResponse, operation_id="a")
    async def shape_a() -> AsyncIterator[ServerSentEvent]:
        yield ServerSentEvent(data=Started(run_id="r1"), id="0")
        yield ServerSentEvent(data=Finished(output="끝"), id="3")

    # 모양 B 는 pyright 가 거부하는 모양이라 여기서는 두지 않는다. 타입 판정은 check_types.py.
    @app.post("/c", response_class=EventSourceResponse, operation_id="c")
    async def shape_c() -> AsyncIterator[EndUserFrame]:
        yield ServerSentEvent(data=Started(run_id="r1"), id="0")
        yield Finished(output="맨 항목")
        yield ServerSentEvent(data=Finished(output="끝"), id="3")

    @app.post("/e", response_class=EventSourceResponse, operation_id="e")
    async def shape_e() -> AsyncIterator[EndUserItem | SkipJsonSchema[ServerSentEvent]]:
        yield ServerSentEvent(data=Started(run_id="r1"), id="0")
        yield ServerSentEvent(data=Finished(output="끝"), id="3")

    return app


def orphans(schema: dict[str, object]) -> list[str]:
    """어디서도 `$ref` 로 가리키지 않는 컴포넌트."""
    text = json.dumps(schema)
    referenced = set(re.findall(r"#/components/schemas/([A-Za-z0-9_]+)", text))
    components = schema.get("components")
    names = set(components["schemas"]) if isinstance(components, dict) else set()
    return sorted(names - referenced)


async def main() -> None:
    app = build()
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://probe") as client:
        for path in ("/a", "/c", "/e"):
            response = await client.post(path)
            print(f"--- {path} 응답 {response.status_code} {response.headers['content-type']}")
            print(response.text)
    schema = app.openapi()
    for op in ("a", "c", "e"):
        content = schema["paths"][f"/{op}"]["post"]["responses"]["200"]["content"]
        data = content["text/event-stream"]["itemSchema"]["properties"]["data"]
        print(f"--- {op} itemSchema.data:", json.dumps(data, ensure_ascii=False))
    print("--- 컴포넌트:", sorted(schema["components"]["schemas"]))
    print("--- 고아 컴포넌트:", orphans(schema))
    adapter_defs = TypeAdapter(EndUserFrame).json_schema(mode="serialization").get("$defs", {})
    print("--- pydantic 단독 $defs:", sorted(adapter_defs))
    print("--- openapi 판:", schema["openapi"])


if __name__ == "__main__":
    asyncio.run(main())
