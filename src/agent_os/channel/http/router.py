"""HTTP 채널의 라우터. 운영자 채널(`/runs`)과 최종 사용자 면(다른 접두사)이 한 수명을 나눠 쓴다.

운영자 채널에는 실행 하나의 이벤트 스트림을 돌려주는 라우트가 셋 있다. `POST /runs` 는 실행 하나를
일으키고, `POST /runs/{run_id}/approval` 은 멈춘 실행에 결정 하나를 내 재개한다. 재개 스트림의 첫
이벤트는 그 결정이고 재생된 사실은 다시 나가지 않는다(ADR 0009, 0014).
`POST /runs/{run_id}/continuation` 은 끝난 실행을 이어 가는 새 실행을 일으킨다. 본문은 `POST /runs`
와 같고 스트림도 같다(ADR 0022). 앞 실행은 경로에만 있다 — 본문에 두면 기본값을 둘 수 없어 지금의
모든 호출이 `null` 을 보내야 하고, 본문 둘의 유니온은 형식 오류의 경로가 두 멤버의 이름으로 함께
실린다. 접미사가 있는 이유는 `verbatim` 이 슬래시까지 잡기 때문이다. 접미사 없는
`/{run_id:verbatim}` 을 결정 경로 앞에 두면 `{id}/approval` 을 통째로 잡는다. 최종 사용자 면의
경로와 그 항목 스트림은 `end_user` 모듈이다.

**응답은 첫 이벤트를 받은 뒤에 시작한다**(ADR 0014). 스트리밍 응답은 첫 바이트 전에 상태
코드를 확정하므로, 실행 전 실패(`PluginError` 계열)는 첫 이벤트 전에 갈라야 상태 코드와 봉투로
답할 수 있다. FastAPI 는 의존성을 전부 푼 뒤에 SSE 제너레이터를 부르고 응답을 시작한다. 그래서
의존성이 실행을 일으키고 첫 이벤트를 기다리며, 그 전의 예외는 의존성에서 던져져 기존 예외 핸들러를
지나 봉투가 된다. 제너레이터 안에서 첫 yield 전에 던지면 이미 200 이 나간 뒤이고, 그 예외는 태스크
그룹의 예외 그룹으로 감싸져 표의 마지막 갈래(고정 문구의 500)로 간다. 응답을 직접 만들어 돌려주는
길로 가면 FastAPI 가 제너레이터 라우트에만 붙이는 keepalive 를 잃는다. 모든 경로가 같다 —
`run()`(이어 가기도)에서는 `run_started` 앞이, `resume()` 에서는 결정 이벤트 앞이 실행 전이다.

**운영자 채널의 프레임은 `data:` 하나다.** 종류는 JSON 의 `type` 한 곳에 있고 `event:` 와 `id:` 를
싣지 않는다(ADR 0014). 계약의 항목 스키마는 FastAPI 의 정형이라 `event`·`id`·`retry` 를 선택
필드로 광고하지만 그대로 둔다(ADR 0014 의 2026-09-24 이력). 이벤트를 제너레이터가 그대로 내면
FastAPI 가 `data:` 만 싣는다. 최종 사용자 면의 프레임은 `id:` 를 싣는다(`end_user`).

운영자 채널의 주체와 결정의 승인자는 조립이 넘긴 주체 하나이고 본문에서 받지 않는다(ADR 0015).
모델도 시작 때 조립이 정한 것이다. 같은 실행에 동시에 온 둘째 결정이 409 인 것은 이 모듈이 아니라
core `resume()` 이 지킨다. 이유는 그 독스트링에 있다.
"""

# `from __future__ import annotations` 를 두지 않는다. 라우트가 라우터 안에서 만든 의존성을 주해의
# `Depends(...)` 로 가리키는데, FastAPI 는 문자열 주해를 모듈 전역에서만 풀어 지역의 클로저를 찾지
# 못하고 앱의 스키마를 만들다 실패한다.

from collections.abc import AsyncIterator
from typing import Annotated, TextIO

from fastapi import APIRouter, Body, Depends, Path, Request
from fastapi.sse import EventSourceResponse

from agent_os import sdk
from agent_os.channel.http.bodies import Decision, StartRun
from agent_os.channel.http.end_user import end_user_router
from agent_os.channel.http.runs import Runs, RunStream
from agent_os.core.ports import ChatModel, Clock, PluginSource, ToolSource, TraceStore
from agent_os.core.run import resume, run
from agent_os.http.errors import request_id_of
from agent_os.http.routes import documented_stream_errors
from agent_os.sdk import RUN_ID_PATTERN, Principal, RunId

# 채널 토큰이 여는 접두사이자 운영자 채널 라우트의 접두사(ADR 0015). 한 값이라 운영자 채널의
# 라우트가 채널 토큰의 면 밖에 설 길이 없다. 인증 표를 넘기는 조립 층이 이것을 읽는다.
CHANNEL_PREFIX = "/runs"

# 스트림의 항목. sdk 의 판별 유니온에 이름을 준 별칭이라 계약에 `Event` 라는 이름 있는 타입이
# 생기고, 트레이스 상세의 `TraceEvent` 와 같은 멤버 컴포넌트를 가리킨다. 트레이스 상세가 아닌
# 이유는 스트림이 이 런타임이 방금 낸 이벤트라 모르는 종류의 표지가 들 자리가 없기 때문이다(ADR
# 0010 의 2026-09-24 이력). 별칭이 없으면 항목이 `Streamitem …` 이라는 제목의 익명 유니온으로
# 계약에 인라인된다. sdk 는 바뀌지 않는다.
type Event = sdk.Event


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

    라우터 하나에 접두사 둘이다 — 운영자 채널과 최종 사용자 면이 같은 `Runs`(앱의 수명과 등록부)를
    나눠 쓴다. 등록부가 하나라야 어느 면에서 일으킨 실행이든 도는 동안 이름표가 하나이고, 수명이
    닫힐 때 남은 실행이 모두 취소된다. 접두사마다 무엇이 여는지는 조립 층이 인증 표로 정한다.

    포트는 조립 층이 만들어 넘기고 라우터는 받은 것만 쓴다(ADR 0010). 트레이스 포트는 관리 라우터와
    같은 것이라 채널에서 일으킨 실행이 같은 앱의 관리 API 에 바로 보인다. 운영자 채널의 주체는
    조립이 넘긴 것이고, 최종 사용자 면의 주체는 요청마다 서명 토큰이 정한다.
    """
    runs = Runs(stderr=stderr)
    router = APIRouter(lifespan=runs.lifespan)
    router.include_router(
        _operator_router(
            runs,
            plugins=plugins,
            model=model,
            tools=tools,
            trace=trace,
            clock=clock,
            principal=principal,
        )
    )
    router.include_router(
        end_user_router(runs, plugins=plugins, model=model, tools=tools, trace=trace, clock=clock)
    )
    return router


def _operator_router(
    runs: Runs,
    *,
    plugins: PluginSource,
    model: ChatModel,
    tools: ToolSource,
    trace: TraceStore,
    clock: Clock,
    principal: Principal,
) -> APIRouter:
    """운영자 채널의 라우터. 채널 토큰이 열고 원문 이벤트와 원문 에러를 싣는다(ADR 0023)."""
    router = APIRouter(prefix=CHANNEL_PREFIX, responses=documented_stream_errors(500))

    async def started(body: StartRun, request: Request, previous_run: RunId | None) -> RunStream:
        """새 실행을 일으키고 첫 이벤트를 받는다. 시작과 이어 가기가 앞 실행 하나만 다르게 준다."""
        events = run(
            body.agent,
            body.request,
            principal,
            previous_run=previous_run,
            plugins=plugins,
            model=model,
            tools=tools,
            trace=trace,
            clock=clock,
        )
        return await runs.start(events, request_id=request_id_of(request), first_index=0)

    async def run_stream(body: StartRun, request: Request) -> RunStream:
        """실행을 일으키고 첫 이벤트를 받는다. 응답은 이것이 돌아온 뒤에 시작한다.

        `started` 를 바로 의존성으로 걸지 않는 이유는 FastAPI 가 그 시그니처의 `previous_run` 을
        질의 파라미터로 읽기 때문이다. 경로마다 앞 실행을 고정한 래퍼 하나가 의존성이다.
        """
        return await started(body, request, None)

    # 404 는 없는 에이전트, 409 는 꺼진 것을 부르면 core 가 던지는 `Disabled` 를 표가 옮긴 것(ADR
    # 0017, 요청한 에이전트이거나 그것이 쓰는 mcp 다), 500 은 그 밖의 구성 오류다. 재개할 수 없는
    # 상태를 만나는 것은 재개 라우트뿐이고, 이어 갈 수 없는 앞 실행을 만나는 것은 이어 가기
    # 라우트뿐이다.
    @router.post(
        "",
        operation_id="start_run",
        summary="실행 하나를 일으켜 그 이벤트를 생기는 대로 흘린다",
        response_class=EventSourceResponse,
        responses=documented_stream_errors(401, 404, 409, 422),
    )
    async def start_run(stream: Annotated[RunStream, Depends(run_stream)]) -> AsyncIterator[Event]:
        async for item in stream.items():
            yield item.event

    async def resume_stream(
        run_id: Annotated[str, Path(pattern=RUN_ID_PATTERN)],
        decision: Annotated[Decision, Body()],
        request: Request,
    ) -> RunStream:
        """결정을 내고 재개된 실행의 첫 이벤트(그 결정)를 받는다. 응답은 이것이 돌아온 뒤에 선다.

        실행의 상태도 주체도 결정의 자리도 플러그인의 켜짐도 먼저 확인하지 않는다. 부재와 다른
        주체와 재개 불가와 꺼짐은 core 의 `resume()` 이 던진 타입을 표가 옮긴다. 채널이 포트나
        `run_status()` 로 먼저 보면 판정 순서(자기 실행 읽기 → 형식 1 → 일시정지 아님 → 자리 →
        고리 → 준비)가 core 밖으로 샌다(ADR 0014 와 그 2026-09-28·2026-10-05 이력, ADR 0017).
        """
        events = resume(
            RunId(run_id),
            decision.pause_index,
            decision.to_core(),
            principal,
            plugins=plugins,
            model=model,
            tools=tools,
            trace=trace,
            clock=clock,
        )
        return await runs.start(
            events, request_id=request_id_of(request), first_index=decision.pause_index + 1
        )

    # 404 는 없는 실행, 409 는 결정을 받을 수 없는 실행이다. 뜻이 다섯이고 메시지가 가른다 — 그
    # 실행이 다른 주체의 것(ADR 0009 의 2026-10-03 이력), 형식 1 트레이스(ADR 0014), 일시정지가 아닌
    # 실행, 지금의 일시정지가 아닌 자리를 든 결정(ADR 0014 의 2026-09-28 이력), 그 실행의 에이전트나
    # 그것이 쓰는 mcp 가 꺼짐(ADR 0017). 받지 않은 결정은 쓰이지 않는다. 꺼짐이면 다시 켠 뒤 같은
    # 결정을 보낼 수 있다. 자리 어긋남은 그 결정이 본 일시정지가 이미 지나간 것이라 같은 결정은 다시
    # 보내도 받아들여지지 않는다. 트레이스가 가리키는 에이전트가 사라진 실행은 요청이 아니라 서버의
    # 기록이 댄 이름이라 404 가 아니라 500 이다(ADR 0014 의 2026-09-24 이력). `{run_id}` 는
    # `traces/{run_id}.jsonl` 로 조립되는 원격 입력이라 관리의 `/traces/{run_id}` 와 같이 `verbatim`
    # 과 sdk 의 패턴을 지난다. 계약의 경로는 변환기 없이 적힌다.
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
        async for item in stream.items():
            yield item.event

    async def continue_stream(
        run_id: Annotated[str, Path(pattern=RUN_ID_PATTERN)], body: StartRun, request: Request
    ) -> RunStream:
        """앞 실행을 가리켜 새 실행을 일으키고 첫 이벤트를 받는다. 응답은 이것이 돌아온 뒤에 선다.

        앞 실행의 존재도 상태도 주체도 먼저 확인하지 않는다. 부재, 다른 주체, 이어 갈 수 없음, 꺼짐,
        깨진 고리는 core 의 `run()` 이 던진 타입을 표가 옮긴다. 채널이 포트나 `run_status()` 로 먼저
        보면 판정 순서(앞 실행 → 고리 → 준비)가 core 밖으로 샌다(`.claude/rules/channel.md`).
        """
        return await started(body, request, RunId(run_id))

    # 404 는 없는 앞 실행이거나 없는 에이전트이고 메시지가 가른다. 409 는 뜻이 셋이고 메시지가
    # 가른다 — 앞 실행이 다른 주체의 것(`DifferentPrincipal`), 앞 실행이 `run_finished` 로 끝나지
    # 않음 (`NotContinuable`, 메시지가 실패·일시정지·결말 없음을 든다), 요청한 에이전트나 그것이
    # 쓰는 mcp 가 꺼짐(`Disabled`). 500 은 거슬러 읽는 고리가 깨진 것(없거나 손상이거나 주체가
    # 다르거나 끝나지 않았거나 순환하는 실행)과 그 밖의 구성 오류이고, 봉투의 `message` 가 그
    # `PluginError` 의 문구라 운영자가 어느 실행을 되살려야 하는지 안다. 전부 실행 식별자를 만들기
    # 전이라 트레이스가 생기지 않는다(ADR 0022). `{run_id}` 는 결정 경로와 같이 `verbatim` 과 sdk 의
    # 패턴을 지난다.
    @router.post(
        "/{run_id:verbatim}/continuation",
        operation_id="continue_run",
        summary="끝난 실행을 이어 가는 새 실행을 일으켜 그 이벤트를 생기는 대로 흘린다",
        response_class=EventSourceResponse,
        responses=documented_stream_errors(401, 404, 409, 422),
    )
    async def continue_run(
        stream: Annotated[RunStream, Depends(continue_stream)],
    ) -> AsyncIterator[Event]:
        async for item in stream.items():
            yield item.event

    return router
