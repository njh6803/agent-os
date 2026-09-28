import json
from collections.abc import AsyncIterator

from fastapi import FastAPI
from fastapi.sse import EventSourceResponse

from agent_os.sdk import Event

app = FastAPI()


@app.post("/runs", response_class=EventSourceResponse, operation_id="start_run")
async def start_run() -> AsyncIterator[Event]:
    if False:
        yield


spec = app.openapi()
print(json.dumps(spec["paths"]["/runs"], ensure_ascii=False, indent=1)[:2500])
print(sorted(spec.get("components", {}).get("schemas", {})))
