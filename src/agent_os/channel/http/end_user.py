"""최종 사용자 면. 사이트가 서명한 토큰으로 자기 실행을 시작하고 결정하고 구독한다(ADR 0023).

경로는 접두사 `/end-user` 아래 셋이다. 시작(`POST /end-user/runs`, 본문은 `StartRun`), 결정
(`POST /end-user/runs/{run_id}/approval`, 본문은 `Decision`), 구독
(`GET /end-user/runs/{run_id}/subscription`, 선택 헤더 `Last-Event-ID`). 접두사를 `/runs` 와 가른
이유는 nginx 가 바깥에 넘기는 경로를 그 접두사 하나로 만들기 위해서다(ADR 0024) — 운영자의 채널
토큰과 원문 스트림이 원격에 닿지 않는다. 인증 미들웨어가 이 접두사 아래를 서명 토큰으로만 열고,
지난 요청의 신원(주체 `발급자|sub` 와 사이트 항목)을 요청에 심는다. 주체도 승인자도 본문에서 받지
않는다(ADR 0015).

**판정은 core 가 한다.** 라우트는 core 에 그 사이트의 열 에이전트 목록을 넘길 뿐 에이전트가 목록
안인지, 실행이 누구의 것인지, 상태가 어떤지 먼저 보지 않는다(`.claude/rules/channel.md`). 결정과
구독에서 실행의 에이전트와 주체는 트레이스 안에 있어, 채널이 먼저 보면 트레이스를 먼저 읽어 판정
순서가 core 밖으로 샌다. 상태 코드는 표가 이 면의 것으로 옮긴다 — 남의 실행, 손상된 실행, 없는
실행, 열 에이전트 밖의 실행은 모두 같은 404 고정 문구다(`agent_os.http.errors`).

**프레임은 `data:` 한 줄과 `id:` 한 줄이다.** `data` 는 최종 사용자 항목 하나(`items`)이고 `id` 는
그 항목의 근거인 트레이스 인덱스의 십진 글자다. 결정 본문의 `pause_index` 는 일시정지 항목의 `id`
이고, 끊긴 쪽은 마지막으로 받은 `id` 를 `Last-Event-ID` 로 보내 그다음부터 받는다. `event:` 와
`retry:` 는 싣지 않는다. FastAPI 는 `ServerSentEvent(data=항목, id=…)` 를 yield 하면 두 줄을 쓰고,
반환 주해에 항목 유니온과 `SkipJsonSchema[ServerSentEvent]` 를 함께 두면 계약의 항목 스키마가 그
유니온을 바로 가리킨다(`.scratch/end-user-channel/probes/sse_id_frames.py` 모양 E, 타입 우회 없이
`check_types.py` 가 쟀다). 그 대가로 FastAPI 의 정의 수집이 `ServerSentEvent` 를 어디서도 가리키지
않는 컴포넌트로 계약에 남긴다. 후처리로 지우지 않는다(ADR 0014 의 2026-09-24 이력이 같은 종류의
후처리를 거부했다).

**시작과 결정의 응답은 등록부의 받는 쪽 하나다.** 처음부터(결정은 결정 항목부터) 받는 구독과 같은
프레임이고, 응답은 첫 이벤트를 받은 뒤에 시작한다(`router` 모듈 독스트링).

**구독의 첫 걸음은 한 걸음이다.** core 의 자기 실행 읽기(`read_own_run`) → `Last-Event-ID` 의 범위 →
등록부 보기(도는 실행이면 실황에 붙는다) 사이에 await 가 없다. 그 사이에 실행이 이벤트를 내 빠지거나
두 번 나가지 않는다. 그 뒤 트레이스에서 `Last-Event-ID` 다음 인덱스부터 투영해 보내고 네 갈래로
간다. 마지막 이벤트가 끝남·실패면 닫는다. 일시정지면 그 항목까지 보내고 닫는다. 등록부에 있으면
실황에서 오는 것을 결말까지 보낸다. 등록부에 없고 결말도 없으면(서버가 다시 떠 사라진 실행) 끝내지
못함 항목으로 닫고 그 `id` 는 마지막 이벤트의 인덱스 + 1 이다. **트레이스의 결말이 등록부 보기보다
우선한다** — 마지막 이벤트를 쓴 실행이 도구 연결을 닫는 동안 등록부에 남는 창이 있다. 결정의 자리가
오래됐는지는 보지 않는다. 구독은 읽기다.
"""

# `from __future__ import annotations` 를 두지 않는다. 이유는 `router` 모듈의 같은 주석이다.

from collections.abc import AsyncIterable, AsyncIterator
from dataclasses import dataclass
from typing import Annotated

from anyio.streams.memory import MemoryObjectReceiveStream
from fastapi import APIRouter, Body, Depends, Header, HTTPException, Path, Request
from fastapi.sse import EventSourceResponse, ServerSentEvent
from pydantic.json_schema import SkipJsonSchema

from agent_os.channel.http.bodies import Decision, StartRun
from agent_os.channel.http.items import EndUserItem, UnfinishedItem, project
from agent_os.channel.http.runs import Indexed, Runs, RunStream
from agent_os.core.ports import (
    ChatModel,
    Clock,
    PluginSource,
    ToolSource,
    TraceStore,
    run_status,
)
from agent_os.core.run import read_own_run, resume, run
from agent_os.http.auth import end_user_of
from agent_os.http.errors import request_id_of
from agent_os.http.routes import documented_stream_errors
from agent_os.http.sites import EndUser
from agent_os.sdk import RUN_ID_PATTERN, Event, RunId

# 서명 토큰이 여는 접두사이자 이 면의 라우트의 접두사(ADR 0023). 한 값이라 이 면의 라우트가 서명
# 토큰의 면 밖에 설 길이 없다. `/runs` 를 품지도 그것에 품기지도 않는다. 인증 표와 예외 표의 면을
# 넘기는 조립 층이 이것을 읽는다.
END_USER_PREFIX = "/end-user"
_RUNS = "/runs"
# 시작 경로. 예외 표가 이것으로 시작 경로의 면(깨진 기록이 500)과 실행을 가리키는 경로의 면(깨진
# 기록이 404)을 가른다.
END_USER_START_PATH = f"{END_USER_PREFIX}{_RUNS}"

# `Last-Event-ID` 의 형식. 십진 정수의 글자이고 12자리면 어느 트레이스의 인덱스보다 크다. 어기면
# 422 이고 `violations` 의 `field` 는 `header.last-event-id` 다. 헤더인 이유는 표준(HTML SSE)이 그
# 자리이고, 위젯이 fetch 로 스트림을 읽으므로(`EventSource` 는 `Authorization` 을 못 싣는다) 어차피
# 위젯이 직접 보내기 때문이다. 질의 파라미터는 두지 않는다 — 두 자리에 두면 둘이 다를 때의 규칙이
# 든다.
LAST_EVENT_ID_PATTERN = r"^[0-9]{1,12}$"

# 시작 경로의 422 설명. 요청 글자 수의 상한은 사이트마다 다른 값이라(사이트 파일의 상한 표는
# end-user-channel 티켓 02 가 들인다) 계약에는 단위와 기본값만 글자로 적는다 — 본문이 `StartRun`
# 그대로라 `maxLength` 를 둘 자리가 없다(명세의 2026-10-05 to-tickets 주석). 이 설명은 계약의
# 약속이고, 서버가 글자 수를 재어 422 로 답하는 것도 티켓 02 가 들인다.
_START_INVALID = (
    "요청의 형식이 올바르지 않거나 request 가 그 사이트의 글자 수 상한을 넘었다. 글자는 코드 "
    "포인트(파이썬 len)로 세고 상한의 기본값은 20,000자다"
)


def end_user_router(
    runs: Runs,
    *,
    plugins: PluginSource,
    model: ChatModel,
    tools: ToolSource,
    trace: TraceStore,
    clock: Clock,
) -> APIRouter:
    """최종 사용자 면의 라우터. 운영자 채널과 같은 `Runs` 를 받아 등록부 하나를 나눠 쓴다."""
    router = APIRouter(prefix=END_USER_PREFIX, responses=documented_stream_errors(500))

    async def start_stream(body: StartRun, request: Request) -> RunStream:
        """서명한 주체로 실행을 일으키고 첫 이벤트를 받는다. 응답은 이것이 돌아온 뒤에 시작한다.

        에이전트가 그 사이트의 열 에이전트 목록 안인지 먼저 보지 않는다. 목록 밖이면 core 가 없는
        에이전트와 같은 `Absent` 를 던지고 매니페스트를 읽지 않는다.
        """
        user = _signed_in(request)
        events = run(
            body.agent,
            body.request,
            user.principal,
            visible_agents=user.site.agents,
            plugins=plugins,
            model=model,
            tools=tools,
            trace=trace,
            clock=clock,
        )
        return await runs.start(events, request_id=request_id_of(request), first_index=0)

    # 404 는 목록 밖이거나 없는 에이전트이고 메시지가 같다. 409 는 운영자가 꺼 둔 것을 부른 것이고
    # 종류와 이름 없는 고정 문구다. 429 는 요청하는 쪽의 상한이다. 500 은 그 밖의 구성 오류이고 고정
    # 문구다 — 원문은 서버 기록에만 있다.
    @router.post(
        _RUNS,
        operation_id="start_end_user_run",
        summary="서명한 최종 사용자로 실행 하나를 일으켜 그 항목을 생기는 대로 흘린다",
        response_class=EventSourceResponse,
        responses=documented_stream_errors(
            401, 404, 409, 422, 429, descriptions={422: _START_INVALID}
        ),
    )
    async def start_end_user_run(
        stream: Annotated[RunStream, Depends(start_stream)],
    ) -> AsyncIterator[EndUserItem | SkipJsonSchema[ServerSentEvent]]:
        async for frame in _framed(stream.items()):
            yield frame

    async def decide_stream(
        run_id: Annotated[str, Path(pattern=RUN_ID_PATTERN)],
        decision: Annotated[Decision, Body()],
        request: Request,
    ) -> RunStream:
        """서명한 주체의 결정을 내고 결정 항목부터 받는다. 응답은 이것이 돌아온 뒤에 선다.

        실행의 주체도 에이전트도 상태도 결정의 자리도 먼저 보지 않는다. 판정 순서는 core 의
        `resume()` 이다(자기 실행 읽기 → 형식 1 → 일시정지 아님 → 자리 → 고리 → 준비).
        """
        user = _signed_in(request)
        events = resume(
            RunId(run_id),
            decision.pause_index,
            decision.to_core(),
            user.principal,
            visible_agents=user.site.agents,
            plugins=plugins,
            model=model,
            tools=tools,
            trace=trace,
            clock=clock,
        )
        return await runs.start(
            events, request_id=request_id_of(request), first_index=decision.pause_index + 1
        )

    # 404 는 남의 실행, 없는 실행, 열 에이전트 밖의 실행, 그리고 하위 타입이 아닌 `PluginError` 전부
    # (손상된 트레이스, 깨진 고리, 기록이 가리키는 에이전트의 부재, mcp 와 진입점의 구성 오류)이고
    # 메시지가 모두 같은 고정 문구다 — 구성 오류까지 404 가 되는 것은 ADR 0023 의 2026-10-05 이력이
    # 받아들인 대가이고 원인은 서버 기록에 있다. 409 는 자기 실행이 결정을 받을 수 없는 상태(형식 1,
    # 일시정지 아님, 지나간 자리)이고 메시지가 가르며, 꺼짐은 고정 문구다. 받지 않은 결정은 쓰이지
    # 않는다.
    @router.post(
        f"{_RUNS}/{{run_id:verbatim}}/approval",
        operation_id="decide_end_user_approval",
        summary="서명한 최종 사용자의 멈춘 실행에 결정 하나를 내고 결정 항목부터 흘린다",
        response_class=EventSourceResponse,
        responses=documented_stream_errors(401, 404, 409, 422, 429),
    )
    async def decide_end_user_approval(
        stream: Annotated[RunStream, Depends(decide_stream)],
    ) -> AsyncIterator[EndUserItem | SkipJsonSchema[ServerSentEvent]]:
        async for frame in _framed(stream.items()):
            yield frame

    async def subscription(
        run_id: Annotated[str, Path(pattern=RUN_ID_PATTERN)],
        request: Request,
        last_event_id: Annotated[str | None, Header(pattern=LAST_EVENT_ID_PATTERN)] = None,
    ) -> _Subscription:
        """구독의 첫 걸음. 자기 실행 읽기와 범위 확인과 등록부 보기가 await 없이 한 걸음이다.

        동기 함수로 두지 않는다 — FastAPI 가 동기 의존성을 워커 스레드에서 돌려 이 걸음이 이벤트
        루프 밖으로 나가고, 그 사이에 실행이 이벤트를 내면 빠지거나 두 번 나간다.
        """
        user = _signed_in(request)
        own = read_own_run(trace, RunId(run_id), user.principal, user.site.agents)
        events = own.link.events
        start = 0 if last_event_id is None else int(last_event_id) + 1
        last = len(events) - 1
        if start > last + 1:
            raise HTTPException(
                status_code=409,
                detail=f"Last-Event-ID {start - 1} 이 이 실행의 마지막 자리 {last} 보다 크다",
            )
        live = None if run_status(events[-1]) != "unfinished" else runs.join(RunId(run_id))
        return _Subscription(events=events, start=start, live=live)

    # 404 는 결정과 같다. 409 는 `Last-Event-ID` 가 트레이스의 마지막 인덱스보다 큰 것이다 —
    # 클라이언트가 서버의 기록보다 앞선 것을 봤다는 주장이라 상태가 맞지 않는다(끝내지 못함 항목의
    # `id` 를 되돌려 보낸 것이 여기 든다). 그 판정은 자기 실행 읽기의 네 판정 뒤라 남의 실행의
    # 길이가 드러나지 않는다.
    @router.get(
        f"{_RUNS}/{{run_id:verbatim}}/subscription",
        operation_id="subscribe_end_user_run",
        summary="서명한 최종 사용자의 실행에 다시 붙어 놓친 항목부터 결말까지 흘린다",
        response_class=EventSourceResponse,
        responses=documented_stream_errors(401, 404, 409, 422, 429),
    )
    async def subscribe_end_user_run(
        subscribed: Annotated[_Subscription, Depends(subscription)],
    ) -> AsyncIterator[EndUserItem | SkipJsonSchema[ServerSentEvent]]:
        async for frame in subscribed.frames():
            yield frame

    return router


@dataclass(frozen=True)
class _Subscription:
    """구독 하나가 보낼 것. 읽은 트레이스의 이벤트, 보낼 첫 인덱스, 도는 실행이면 붙은 실황."""

    events: tuple[Event, ...]
    start: int
    live: MemoryObjectReceiveStream[Indexed] | None

    async def frames(self) -> AsyncIterator[ServerSentEvent]:
        """네 갈래(모듈 독스트링). 받는 쪽이 떠나 이 제너레이터가 닫히면 붙은 실황도 닫는다."""
        try:
            for index in range(self.start, len(self.events)):
                frame = _frame(index, self.events[index])
                if frame is not None:
                    yield frame
            if run_status(self.events[-1]) != "unfinished":
                return
            if self.live is None:
                yield ServerSentEvent(data=UnfinishedItem(), id=str(len(self.events)))
                return
            async for frame in _framed(self.live):
                yield frame
        finally:
            if self.live is not None:
                self.live.close()


def _signed_in(request: Request) -> EndUser:
    """서명 토큰을 지난 요청의 신원. 미들웨어가 이 접두사 아래를 언제나 검증하므로 없음은 조립의
    결함이고, 예기치 않은 실패의 500 고정 문구로 끝난다."""
    found = end_user_of(request)
    if found is None:
        raise RuntimeError("서명 토큰을 지나지 않은 요청이 최종 사용자 경로에 닿았다")
    return found


def _frame(index: int, event: Event) -> ServerSentEvent | None:
    """이벤트 하나의 프레임. 항목이 없는 종류는 프레임이 없고 인덱스만 지난다."""
    item = project(event)
    return None if item is None else ServerSentEvent(data=item, id=str(index))


async def _framed(items: AsyncIterable[Indexed]) -> AsyncIterator[ServerSentEvent]:
    """등록부의 받는 쪽이 받은 이벤트를 투영한 프레임들. 시작·결정 응답과 구독의 실황이 쓴다."""
    async for item in items:
        frame = _frame(item.index, item.event)
        if frame is not None:
            yield frame
