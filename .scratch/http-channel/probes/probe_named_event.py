"""스트림 항목을 이름 있는 컴포넌트로 실을 수 있나.
sdk 를 건드리지 않는 별칭과 TraceEvent 의 모양."""

import json
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.sse import EventSourceResponse

from agent_os.admin.traces import Trace
from agent_os.sdk import Event as SdkEvent

type Event = SdkEvent

app = FastAPI()


@app.post("/runs", response_class=EventSourceResponse, operation_id="start_run")
async def start_run() -> AsyncIterator[Event]:
    if False:
        yield


@app.get("/traces/x", operation_id="read_trace")
def read_trace() -> Trace:
    raise NotImplementedError


spec = app.openapi()
item = spec["paths"]["/runs"]["post"]["responses"]["200"]["content"]["text/event-stream"]
print(
    "stream data schema:", json.dumps(item["itemSchema"]["properties"]["data"], ensure_ascii=False)
)
schemas = spec["components"]["schemas"]
print("components:", sorted(schemas))
print("Event component:", json.dumps(schemas.get("Event"), ensure_ascii=False)[:300])
print("TraceEvent oneOf count:", len(schemas["TraceEvent"].get("oneOf", [])))
print("TraceEvent first refs:", [o.get("$ref") for o in schemas["TraceEvent"]["oneOf"]][:3])
