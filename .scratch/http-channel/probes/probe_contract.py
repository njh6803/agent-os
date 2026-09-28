"""스펙 검토 프로브: 설치된 fastapi 0.141.1 이 채널 라우트 둘을 계약에 어떻게 싣는가."""

from __future__ import annotations

import json
import sys
from collections.abc import AsyncIterator
from typing import Annotated, Literal

from fastapi import APIRouter, Body, Path
from fastapi.responses import StreamingResponse
from fastapi.sse import EventSourceResponse, ServerSentEvent
from pydantic import BaseModel, ConfigDict, Field

from agent_os.sdk import RUN_ID_PATTERN
from agent_os.sdk import Event as SdkEvent
from agent_os.server import create_app

VARIANT = sys.argv[1]

type Event = SdkEvent


class StartRun(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    agent: str
    request: str


if VARIANT == "collide":

    class ApprovalGranted(BaseModel):
        model_config = ConfigDict(extra="forbid", frozen=True)
        decision: Literal["approve"]

    class ApprovalDenied(BaseModel):
        model_config = ConfigDict(extra="forbid", frozen=True)
        decision: Literal["deny"]
        reason: str

    type Decision = Annotated[ApprovalGranted | ApprovalDenied, Field(discriminator="decision")]
else:

    class Approve(BaseModel):
        model_config = ConfigDict(
            extra="forbid", frozen=True, json_schema_serialization_defaults_required=True
        )
        if VARIANT == "default_discriminator":
            decision: Literal["approve"] = "approve"
        else:
            decision: Literal["approve"]

    class Deny(BaseModel):
        model_config = ConfigDict(extra="forbid", frozen=True)
        decision: Literal["deny"]
        reason: str

    type Decision = Annotated[Approve | Deny, Field(discriminator="decision")]

router = APIRouter()

if VARIANT == "sse_items":

    @router.post("/runs", operation_id="start_run", response_class=EventSourceResponse)
    async def start_run(body: StartRun) -> AsyncIterator[ServerSentEvent]:
        yield ServerSentEvent(data={})
elif VARIANT == "plain_response":

    @router.post("/runs", operation_id="start_run", response_class=EventSourceResponse)
    async def start_run(body: StartRun) -> StreamingResponse:
        return EventSourceResponse(iter([b""]))
else:

    @router.post("/runs", operation_id="start_run", response_class=EventSourceResponse)
    async def start_run(body: StartRun) -> AsyncIterator[Event]:
        if False:
            yield


@router.post(
    "/runs/{run_id:verbatim}/approval",
    operation_id="submit_approval",
    response_class=EventSourceResponse,
)
async def submit_approval(
    run_id: Annotated[str, Path(pattern=RUN_ID_PATTERN)],
    body: Annotated[Decision, Body()],
) -> AsyncIterator[Event]:
    if False:
        yield


app = create_app(plugins=object(), trace=object(), token="t", stderr=sys.stderr)
app.include_router(router)
spec = app.openapi()
schemas = spec["components"]["schemas"]
print("openapi:", spec["openapi"])
print("components:", sorted(schemas))
runs = spec["paths"]["/runs"]["post"]
print("/runs 200:", json.dumps(runs["responses"]["200"], ensure_ascii=False))
print("/runs requestBody:", json.dumps(runs.get("requestBody"), ensure_ascii=False))
appr = spec["paths"]["/runs/{run_id}/approval"]["post"]
print("approval requestBody:", json.dumps(appr.get("requestBody"), ensure_ascii=False))
print("approval responses keys:", sorted(appr["responses"]))
for name in (
    "Event",
    "Decision",
    "Approve",
    "Deny",
    "ApprovalGranted",
    "ApprovalDenied",
    "TraceEvent",
):
    if name in schemas:
        print(name, "=", json.dumps(schemas[name], ensure_ascii=False)[:700])
