"""HTTP 채널의 라우터와 본문. 경로는 둘이고 둘 다 실행 하나의 이벤트 스트림을 돌려준다.

`POST /runs` 는 실행 하나를 일으키고, `POST /runs/{run_id}/approval` 은 멈춘 실행에 결정 하나를 내
재개한다. 재개 스트림의 첫 이벤트는 그 결정이고 재생된 사실은 다시 나가지 않는다(ADR 0009, 0014).

**응답은 첫 이벤트를 받은 뒤에 시작한다**(ADR 0014). 스트리밍 응답은 첫 바이트 전에 상태
코드를 확정하므로, 실행 전 실패(`PluginError` 계열)는 첫 이벤트 전에 갈라야 상태 코드와 봉투로
답할 수 있다. FastAPI 는 의존성을 전부 푼 뒤에 SSE 제너레이터를 부르고 응답을 시작한다. 그래서
의존성이 실행을 일으키고 첫 이벤트를 기다리며, 그 전의 예외는 의존성에서 던져져 기존 예외
핸들러를 지나 봉투가 된다. 제너레이터 안에서 첫 yield 전에 던지면 이미 200 이 나간 뒤이고, 그
예외는 태스크 그룹의 예외 그룹으로 감싸져 표의 마지막 갈래(고정 문구의 500)로 간다. 응답을 직접
만들어 돌려주는 길로 가면 FastAPI 가 제너레이터 라우트에만 붙이는 keepalive 를 잃는다. 두 경로가
같다 — `run()` 에서는 `run_started` 앞이, `resume()` 에서는 결정 이벤트 앞이 실행 전이다.

**프레임은 `data:` 하나다.** 종류는 JSON 의 `type` 한 곳에 있고 `event:` 와 `id:` 를 싣지 않는다
(ADR 0014). 계약의 항목 스키마는 FastAPI 의 정형이라 `event`·`id`·`retry` 를 선택 필드로 광고하지만
그대로 둔다(ADR 0014 의 2026-09-24 이력). 이벤트를 제너레이터가 그대로 내면 FastAPI 가 `data:` 만
싣는다.

실행의 주체와 결정의 승인자는 조립이 넘긴 주체 하나이고 본문에서 받지 않는다(ADR 0015). 모델도 시작
때 조립이 정한 것이다.

같은 실행에 동시에 온 둘째 결정이 409 인 것은 이 모듈이 아니라 core `resume()` 이 지킨다. 이유는
그 독스트링에 있다.
"""

# `from __future__ import annotations` 를 두지 않는다. 라우트가 라우터 안에서 만든 의존성을 주해의
# `Depends(...)` 로 가리키는데, FastAPI 는 문자열 주해를 모듈 전역에서만 풀어 지역의 클로저를 찾지
# 못하고 앱의 스키마를 만들다 실패한다.

from collections.abc import AsyncIterator
from typing import Annotated, Literal, TextIO

from fastapi import APIRouter, Body, Depends, Path, Request
from fastapi.sse import EventSourceResponse
from pydantic import AfterValidator, BaseModel, ConfigDict, Field

from agent_os import sdk
from agent_os.channel.http.runs import Runs, RunStream
from agent_os.core.ports import ChatModel, Clock, PluginSource, ToolSource, TraceStore
from agent_os.core.run import Approve as CoreApprove
from agent_os.core.run import Deny as CoreDeny
from agent_os.core.run import resume, run
from agent_os.http.errors import request_id_of
from agent_os.http.routes import documented_stream_errors
from agent_os.sdk import PLUGIN_NAME_PATTERN, RUN_ID_PATTERN, AgentName, Principal, RunId

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


# 결정 본문의 멤버 둘과 그 유니온. 이름이 core 의 `Approve`·`Deny`·`Decision` 과 같다. 용어집의
# 결정은 "허가이거나, 사유를 붙인 거부"이고 이것과 core 의 것은 같은 개념의 두 모양(와이어와 core
# 의 값)이라, 관리의 `Trace`·`RunSummary` 가 core 의 것과 이름이 같은 선례를 따른다. core 쪽은 이
# 모듈에서 별칭으로 부른다. 이벤트 컴포넌트(`ApprovalGranted`·`ApprovalDenied`)와 같은 이름을 쓰지
# 않는 이유는 그러면 계약의 이벤트 컴포넌트가 입력과 출력으로 갈라지기 때문이다(명세 검토의 프로브).
#
# 판별자에도 기본값을 두지 않는다. 요청 본문은 검증 스키마로 실려 기본값이 곧 계약의 "선택"이
# 되는데 서버는 판별자 없는 본문을 거부한다(`StartRun` 과 같은 규칙). 추가 필드는 422 다 — 승인에
# 붙은 사유가 조용히 버려지지 않고, 승인자는 본문이 아니라 조립이 넘긴 주체다(ADR 0015).
class Approve(BaseModel):
    """허가. 멈춘 도구 호출이 실제로 실행된다. 사유를 담을 자리가 없다."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    decision: Literal["approve"]

    def to_core(self) -> CoreApprove:
        """core 가 받는 결정(질의)."""
        return CoreApprove()


def _trimmed(reason: str) -> str:
    """거부 사유를 CLI 와 같은 규칙(파이썬 `str.strip`)으로 다듬는다. 다듬어 비면 형식 오류다.

    pydantic 의 `strip_whitespace` 를 쓰지 않는 이유는 그 다듬기(rust)가 U+001C~U+001F 를 공백으로
    보지 않아서다. 그러면 그 문자만 든 사유가 검증을 지나 core 의 `Deny` 에서 막혀 422 가 아니라
    고정 문구의 500 이 되고, 앞뒤에 붙은 것은 CLI 와 다르게 기록된다. 두 경우를 채널 테스트가 잰다.
    """
    trimmed = reason.strip()
    if not trimmed:
        raise ValueError("거부에는 공백이 아닌 사유가 있어야 한다")
    return trimmed


# 사유는 앞뒤 공백을 다듬어 기록한다. CLI 의 결정 해석이 다듬은 사유를 넘기므로 두 채널에서 같은
# 결정이 같게 기록된다(스토리 27). 다듬은 뒤 비면 422 이고 core 의 `Deny` 가 한 번 더 막는다.
# `min_length` 는 계약에 "비어 있지 않다"를 적는 자리이고 판정은 `_trimmed` 가 한다.
class Deny(BaseModel):
    """거부. 도구를 부르지 않고 사유를 모델에 되돌린다. 사유는 비어 있을 수 없다."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    decision: Literal["deny"]
    reason: Annotated[str, Field(min_length=1), AfterValidator(_trimmed)]

    def to_core(self) -> CoreDeny:
        """core 가 받는 결정(질의)."""
        return CoreDeny(reason=self.reason)


# 판별자 `decision` 의 유니온이라 허가와 거부가 같은 모양의 선택 필드로 섞이지 않는다(ADR 0014).
# 계약에 `Decision` 이라는 이름 있는 타입이 서려면 라우트가 이것을 `Body()` 로 받아야 한다 — 별칭을
# 그대로 받으면 FastAPI 가 본문을 `Body` 라는 제목의 익명 유니온으로 인라인한다. 계약 이름 테스트가
# 그것을 잡는다. 422 의 `violations` 경로 모양은 `.claude/rules/http.md`.
type Decision = Annotated[Approve | Deny, Field(discriminator="decision")]


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

    async def resume_stream(
        run_id: Annotated[str, Path(pattern=RUN_ID_PATTERN)],
        decision: Annotated[Decision, Body()],
        request: Request,
    ) -> RunStream:
        """결정을 내고 재개된 실행의 첫 이벤트(그 결정)를 받는다. 응답은 이것이 돌아온 뒤에 선다.

        실행의 상태를 먼저 확인하지 않는다. 부재와 재개 불가는 core 의 `resume()` 이 던진 타입을
        표가 옮긴다. 채널이 포트나 `run_status()` 로 먼저 보면 형식 1 판정이 core 밖으로 샌다(ADR
        0014).
        """
        events = resume(
            RunId(run_id),
            decision.to_core(),
            principal,
            plugins=plugins,
            model=model,
            tools=tools,
            trace=trace,
            clock=clock,
        )
        return await runs.start(events, request_id=request_id_of(request))

    # 404 는 없는 실행, 409 는 재개할 수 없는 실행(일시정지가 아님, 형식 1)이다. 트레이스가
    # 가리키는 에이전트가 사라진 실행은 요청이 아니라 서버의 기록이 댄 이름이라 404 가 아니라 500
    # 이다(ADR 0014 의 2026-09-24 이력). `{run_id}` 는 `traces/{run_id}.jsonl` 로 조립되는 원격
    # 입력이라 관리의 `/traces/{run_id}` 와 같이 `verbatim` 과 sdk 의 패턴을 지난다. 계약의 경로는
    # 변환기 없이 적힌다.
    @router.post(
        "/{run_id:verbatim}/approval",
        operation_id="decide_approval",
        summary="멈춘 실행에 결정 하나를 내고 재개된 실행의 이벤트를 생기는 대로 흘린다",
        response_class=EventSourceResponse,
        responses=documented_stream_errors(401, 404, 409, 422),
    )
    async def decide_approval(
        stream: Annotated[RunStream, Depends(resume_stream)],
    ) -> AsyncIterator[Event]:
        async for event in stream.events():
            yield event

    return router
