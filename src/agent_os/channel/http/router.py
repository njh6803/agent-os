"""HTTP 채널의 라우터와 본문. `POST /runs` 가 실행 하나를 일으켜 그 이벤트 스트림을 돌려준다.

**응답은 첫 이벤트를 받은 뒤에 시작한다**(ADR 0014). 스트리밍 응답은 첫 바이트 전에 상태
코드를 확정하므로, 실행 전 실패(`PluginError` 계열)는 첫 이벤트 전에 갈라야 상태 코드와 봉투로
답할 수 있다. FastAPI 는 의존성을 전부 푼 뒤에 SSE 제너레이터를 부르고 응답을 시작한다. 그래서
의존성이 실행을 일으키고 첫 이벤트를 기다리며, 그 전의 예외는 의존성에서 던져져 기존 예외
핸들러를 지나 봉투가 된다. 제너레이터 안에서 첫 yield 전에 던지면 이미 200 이 나간 뒤이고, 그
예외는 태스크 그룹의 예외 그룹으로 감싸져 표의 마지막 갈래(고정 문구의 500)로 간다. 응답을 직접
만들어 돌려주는 길로 가면 FastAPI 가 제너레이터 라우트에만 붙이는 keepalive 를 잃는다.

**프레임은 `data:` 하나다.** 종류는 JSON 의 `type` 한 곳에 있고 `event:` 와 `id:` 를 싣지 않는다
(ADR 0014). 계약의 항목 스키마는 FastAPI 의 정형이라 `event`·`id`·`retry` 를 선택 필드로 광고하지만
그대로 둔다(ADR 0014 의 2026-09-24 이력). 이벤트를 제너레이터가 그대로 내면 FastAPI 가 `data:` 만
싣는다.

실행의 주체는 조립이 넘긴 것이고 본문에서 받지 않는다(ADR 0015). 모델도 시작 때 조립이 정한 것이다.
"""

# `from __future__ import annotations` 를 두지 않는다. 라우트가 라우터 안에서 만든 의존성을 주해의
# `Depends(...)` 로 가리키는데, FastAPI 는 문자열 주해를 모듈 전역에서만 풀어 지역의 클로저를 찾지
# 못하고 앱의 스키마를 만들다 실패한다.

from collections.abc import AsyncIterator
from typing import Annotated, TextIO

from fastapi import APIRouter, Depends, Request
from fastapi.sse import EventSourceResponse
from pydantic import BaseModel, ConfigDict, Field

from agent_os import sdk
from agent_os.channel.http.runs import Runs, RunStream
from agent_os.core.ports import ChatModel, Clock, PluginSource, ToolSource, TraceStore
from agent_os.core.run import run
from agent_os.http.errors import request_id_of
from agent_os.http.routes import documented_stream_errors
from agent_os.sdk import PLUGIN_NAME_PATTERN, AgentName, Principal

# 채널 토큰이 여는 접두사이자 채널 라우트의 접두사(ADR 0015). 한 값이라 채널 라우트가 채널 토큰의 면
# 밖에 설 길이 없다. 인증 표를 넘기는 조립 층이 이것을 읽는다.
CHANNEL_PREFIX = "/runs"

# 스트림의 항목. sdk 의 판별 유니온에 이름을 준 별칭이라 계약에 `Event` 라는 이름 있는 타입이
# 생기고, 트레이스 상세의 `TraceEvent` 와 같은 멤버 컴포넌트를 가리킨다. 트레이스 상세가 아닌
# 이유는 스트림이 이 런타임이 방금 낸 이벤트라 모르는 종류의 표지가 들 자리가 없기 때문이다(ADR
# 0010 의 2026-09-24 이력). 별칭이 없으면 항목이 `Streamitem …` 이라는 제목의 익명 유니온으로
# 계약에 인라인된다. sdk 는 바뀌지 않는다.
type Event = sdk.Event


# 계약에 박히는 요청 본문이다. 기본값 있는 필드를 두지 않는다 — 기본값이 있으면 그 필드는 계약에서
# 선택이 된다. 이벤트와 매니페스트가 켜 둔 `json_schema_serialization_defaults_required` 는 직렬화
# 스키마에만 걸리고 요청 본문은 검증 스키마로 실린다(명세 검토의 프로브). 추가 필드는 무시하지
# 않고 422 다. 주체와 승인자와 모델이 그런 필드이고, 보낸 쪽이 자기 값이 쓰였다고 믿게 두지
# 않는다(ADR 0015). `agent` 는 `plugins/agents/{agent}/plugin.toml` 로 조립되는 원격 입력이라 sdk
# 의 패턴을 포트에 닿기 전에 지난다. `request` 는 문자열이면 된다 — CLI 가 받는 것과 같다.
class StartRun(BaseModel):
    """실행 하나를 일으키는 요청. 등록된 에이전트의 이름과 요청 문자열이다."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    agent: Annotated[AgentName, Field(pattern=PLUGIN_NAME_PATTERN)]
    request: str


def channel_router(
    *,
    plugins: PluginSource,
    model: ChatModel,
    tools: ToolSource,
    trace: TraceStore,
    clock: Clock,
    principal: Principal,
    stderr: TextIO,
) -> APIRouter:
    """채널 라우터. 실행을 소유하는 수명을 들고 있어 앱에 붙으면 그 수명이 앱의 수명에 합쳐진다.

    포트는 조립 층이 만들어 넘기고 라우터는 받은 것만 쓴다(ADR 0010). 트레이스 포트는 관리 라우터와
    같은 것이라 채널에서 일으킨 실행이 같은 앱의 관리 API 에 바로 보인다.
    """
    runs = Runs(stderr=stderr)
    router = APIRouter(
        prefix=CHANNEL_PREFIX, lifespan=runs.lifespan, responses=documented_stream_errors(500)
    )

    async def run_stream(body: StartRun, request: Request) -> RunStream:
        """실행을 일으키고 첫 이벤트를 받는다. 응답은 이것이 돌아온 뒤에 시작한다."""
        events = run(
            body.agent,
            body.request,
            principal,
            plugins=plugins,
            model=model,
            tools=tools,
            trace=trace,
            clock=clock,
        )
        return await runs.start(events, request_id=request_id_of(request))

    # 404 는 없는 에이전트, 500 은 그 밖의 구성 오류다. 409 는 없다 — 재개할 수 없는 상태를 만나는
    # 것은 재개 라우트다.
    @router.post(
        "",
        operation_id="start_run",
        summary="실행 하나를 일으켜 그 이벤트를 생기는 대로 흘린다",
        response_class=EventSourceResponse,
        responses=documented_stream_errors(401, 404, 422),
    )
    async def start_run(stream: Annotated[RunStream, Depends(run_stream)]) -> AsyncIterator[Event]:
        async for event in stream.events():
            yield event

    return router
