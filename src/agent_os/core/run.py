"""주 이음매. 에이전트를 돌려 이벤트를 내는 async generator 둘, run() 과 resume().

로더, 루프, 도구 연결, 승인 게이트, 재생, 트레이스 기록, 실패 정책이 전부 이 아래에 있어서 기본
스위트가 이 지점 하나를 민다. run_started, run_paused, approval_granted, approval_denied,
run_resumed, run_failed 는 런타임이 내고, 에이전트는 run_finished 하나를 마지막에 낸다. 에이전트가
낸 다른 이벤트는 그대로 통과한다. 거부는 실행을 끝내지 않는다. 거부된 도구 호출은 불리지 않고
tool_called(ok=false) 로 사유가 모델에게 돌아가며, 에이전트가 정상적으로 끝맺는다(ADR 0009).

resume() 이 run() 의 인자가 아닌 이유는 입력이 실제로 다르기 때문이다. 재개는 에이전트 이름,
요청, 주체를 받지 않고 트레이스의 run_started 에서 읽는다. 하나로 합치면 "재개일 때는 이 인자
셋이 무시된다"는, 타입으로 막을 수 없는 규칙을 문서로 적어야 한다(ADR 0009). 내부는 _drive 가
공유하고 갈리는 것은 이벤트를 어디서 얻나(재생이냐 실제 호출이냐)와 무엇을 트레이스에 쓰나뿐이다.

재생 구간에서 생긴 사실은 트레이스에 다시 쓰지 않는다. 이미 거기 있기 때문이고, 에이전트가 낸
것도 마찬가지다. 기준은 "재생 구간인가"가 아니라 "이미 트레이스에 있는가"라서, 재생 구간에서
처음 생긴 사실인 대조 불일치의 run_failed 는 쓴다. 사실이 한 번씩만 남는다.

실행 전과 실행 중의 경계: 없는 플러그인, 매니페스트 오류, 진입점 import 실패, 없는 mcp 이름,
마스킹과 승인이 겹치는 도구는 실행 식별자를 만들기 전에 PluginError 로 끝나 트레이스가 없다.
재개할 수 없는 트레이스(없음, 형식 1, 일시정지 아님, 손상)도 같은 자리의 PluginError 다.
저장소가 결정 이벤트를 이어 쓰지 못해도 PluginError 이고 도구를 부르지 않는다(ADR 0012 이력).
그 가운데 요청을 고쳐서 풀리는 것은 하위 타입이다. 요청이 댄 에이전트나 실행이 없으면 Absent,
실행이 일시정지가 아니거나 형식 1 이면 NotResumable 이다(ADR 0014). 재개할 실행의 트레이스가
가리키는 에이전트가 없는 것은 요청이 아니라 서버의 기록이 댄 이름이라 PluginError 그대로다.
MCP 서버 기동 실패부터는 실행 안이라 run_failed 로 끝나고 트레이스가 남는다. 매니페스트가
가리키는 도구와 인자의 실재는 도구 목록이 연결 뒤에야 나오므로 연결 직후에 검사하고, 어긋나면
실행 안의 실패다(ADR 0009). 그 검사는 재개에서도 같은 자리에서 돈다.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator, AsyncIterator, Mapping, Sequence
from contextlib import aclosing
from dataclasses import dataclass
from datetime import datetime
from typing import NoReturn, TypeGuard, assert_never

from langchain_core.messages import AIMessage, BaseMessage

from agent_os.core.loop import ModelCaller, model_caller, run_loop
from agent_os.core.model import ModelReply, message_from, reply_from
from agent_os.core.ports import (
    Absent,
    ChatModel,
    Clock,
    NotResumable,
    PluginError,
    PluginSource,
    ToolConnection,
    ToolResult,
    ToolSource,
    ToolSpec,
    Trace,
    TraceSchemaVersion,
    TraceStore,
    UnknownEvent,
)
from agent_os.core.replay import Mismatch, Record, Replay
from agent_os.sdk import (
    AgentName,
    ApprovalDenied,
    ApprovalGranted,
    BaseAgent,
    Event,
    Json,
    LlmCalled,
    McpServer,
    PluginKind,
    PluginManifest,
    PluginName,
    Principal,
    RunFailed,
    RunFinished,
    RunId,
    RunPaused,
    RunResumed,
    RunStarted,
    ToolCall,
    ToolCalled,
    ToolError,
    approval_conflicts,
    secret_args_by_tool,
)

MASKED = "***"

# 재개할 수 있는 트레이스 형식. 1 은 재개의 입력이 되는 필드가 비어 있어 읽기만 된다(ADR 0009).
# 어댑터가 쓸 때 붙이는 버전과 뜻이 달라 따로 둔다. 형식이 늘면 여기에 받아들일 것을 더한다.
RESUMABLE: tuple[TraceSchemaVersion, ...] = ("2",)

# 실행의 시작과 재개의 경계를 표시하는 이벤트. 재생할 사실이 아니라 재생 기록에서 뺀다. 나머지는
# 런타임의 모델·도구 호출과 에이전트가 낸 것이고, 트레이스만 보고는 둘을 구분할 수 없어 함께 센다.
_BOUNDARY = (RunStarted, RunPaused, ApprovalGranted, ApprovalDenied, RunResumed)


@dataclass(frozen=True)
class Approve:
    """승인. 멈췄던 도구 호출이 실제로 실행된다."""


@dataclass(frozen=True)
class Deny:
    """거부. 도구를 부르지 않고 사유를 실패한 도구 결과로 모델에 되돌린다(ADR 0009).

    사유가 필수인 것은 ApprovalDenied.reason 이 필수 필드이기 때문이다. 선택으로 두면 채널이 빈
    문자열을 지어내 사유 없는 거부가 기본값으로 굳는다. 승인자를 필수로 만든 논증과 같다.
    """

    reason: str

    def __post_init__(self) -> None:
        """빈 사유는 여기서 막는다. 채널마다 검사하면 다음 채널이 올 때 fail-open 이 다시 열린다."""
        if not self.reason.strip():
            raise ValueError("거부에는 사유가 있어야 한다")


# 승인자가 내린 결정. 게이트가 도구 하나를 판정하는 데 한 번 쓰인다. 거부도 한 번만 쓰이므로,
# 거부 뒤 승인 대상을 또 만나면 다시 멈춘다. 한 번의 거부가 뒤의 것까지 막아 주지 않는다.
type Decision = Approve | Deny


@dataclass(frozen=True)
class _Verdict:
    """결정과 그것이 판정하는 호출. 사람이 승인하거나 거부한 것은 일시정지가 보여 준 그 호출이다.

    재개 뒤 첫 실제 호출이 멈춘 것과 다르면 결정을 적용하지 않고 실패로 끝낸다. 재생 대조는
    기록이 있는 구간만 보므로, 기록 끝 이후에 바뀐 에이전트(다른 도구를 부른다)나 매니페스트(그
    도구가 승인 대상에서 빠졌다)는 여기서 잡는다. 정책이 아니라 호출에 묶여야 "사람이 승인한 것과
    실제로 실행되는 것"이 같다(ADR 0009 와 그 2026-09-22 이력, 티켓 05).
    """

    decision: Decision
    paused: RunPaused


@dataclass(frozen=True)
class _Policy:
    """매니페스트가 정한 도구별 가드레일. 마스킹과 승인이 늘 함께 다녀서 한 덩어리다."""

    secrets: Mapping[str, tuple[str, ...]]
    approvals: frozenset[str]


@dataclass(frozen=True)
class _Prepared:
    """실행 식별자가 생기기 전에 확정되는 것. run() 과 resume() 이 같은 준비를 거친다."""

    servers: Mapping[PluginName, McpServer]
    policy: _Policy
    instance: BaseAgent


class _Paused(BaseException):
    """게이트가 실행을 멈추는 신호. 에이전트의 제너레이터를 지나 실행 조립부까지 올라간다.

    Exception 이 아닌 이유는 플러그인이 `except Exception` 으로 삼키면 가드레일이 아니기 때문이다.
    에이전트 코드는 신뢰 경계 밖이다. 그래도 삼키면 컨텍스트가 그 뒤의 어떤 호출도 하지 않는다.
    """


def _mask(
    tool: str, args: Mapping[str, Json], secrets: Mapping[str, tuple[str, ...]]
) -> Mapping[str, Json]:
    """선언된 인자를 가려 이벤트에 담는다. 실제 도구 호출에는 진짜 값이 그대로 간다.

    마스킹하는 자리가 core 이고 트레이스 어댑터가 아닌 이유는, 원칙 V 가 금하는 것이 파일이
    아니라 이벤트이고 secret_args 를 아는 것도 core 이기 때문이다(ADR 0009).
    """
    names = secrets.get(tool, ())
    if not names:
        return args
    return {key: MASKED if key in names else value for key, value in args.items()}


def _reject_masked_args(
    tool: str, args: Mapping[str, Json], secrets: Mapping[str, tuple[str, ...]]
) -> None:
    """마스킹된 값이 실제 도구에 가려는 것을 막는다. 재생이 만드는 유일한 새 노출이다.

    ADR 0009 는 "재생 구간에서 도구 인자는 쓰이지 않고 결과만 필요하다"고 보았지만, 한 모델 턴에
    승인 대상 뒤로 마스킹된 도구가 오면 그 호출은 재개 뒤 실제로 실행되고 인자는 재생된 모델
    응답에서 온 마스킹된 값이다. 조용히 망가진 호출을 보내느니 실패로 끝낸다.
    """
    leaked = [name for name in secrets.get(tool, ()) if args.get(name) == MASKED]
    if leaked:
        raise ValueError(f"마스킹된 인자를 실제 도구에 보낼 수 없다: {tool} 의 {', '.join(leaked)}")


class _Context:
    """AgentContext 를 시그니처로 만족한다. 루프 안에서 생긴 이벤트를 순서대로 쌓아 둔다.

    도구 호출은 루프에서 오든 에이전트가 직접 부르든 _call 하나를 지나고, 모델 호출은 _ask 하나를
    지난다. 게이트, 마스킹, 기록, 재생이 그 두 자리에 있어서 경로를 바꿔 빠져나갈 수 없다(ADR 0009).
    """

    def __init__(
        self,
        started: RunStarted,
        clock: Clock,
        model: ChatModel,
        tools: ToolConnection,
        policy: _Policy,
        replay: Replay,
        verdict: _Verdict | None,
    ) -> None:
        self.run_id = started.run_id
        self._started_at = started.ts
        self._paused = False
        self._resumed = False
        self._clock = clock
        self._model = model
        self._tools = tools
        self._policy = policy
        self._replay = replay
        self._verdict = verdict
        self._pending: list[Event] = []

    @property
    def paused(self) -> bool:
        """조립부가 읽는다. 플러그인이 되돌릴 수 없도록 읽기 전용이다."""
        return self._paused

    @property
    def replaying(self) -> bool:
        """재생 구간인가. 여기서 에이전트가 낸 이벤트는 이미 트레이스에 있어 다시 흘리지 않는다."""
        return self._replay.resuming and not self._resumed

    def now(self) -> datetime:
        """에이전트의 시계. 재개 이벤트 전에는 실행의 시작 시각이다.

        처음 실행 전체가 나중에 재생될 구간이므로 처음부터 고정한다. 그래야 프롬프트에 날짜를
        넣는 평범한 에이전트가 시각 때문에 재개 불가가 되지 않는다(ADR 0009, 사용자 스토리 8).
        시계 읽기를 따로 기록하지 않고도 결정적이다.

        런타임이 자기 이벤트에 찍는 시각은 이것이 아니라 실제 시각이다. 그쪽은 대조 대상이
        아니라 관찰용이고, 얼리면 한 실행의 트레이스가 전부 같은 시각이 되어 쓸모를 잃는다.
        """
        return self._clock.now() if self._resumed else self._started_at

    async def llm(self, prompt: str) -> str:
        """프롬프트와 "첫 턴인가"는 이 호출의 클로저가 들고 있다.

        인스턴스에 두면 에이전트가 llm() 을 겹쳐 부를 때 서로 덮어써 대조가 엉뚱해진다.
        """
        self._stay_paused()
        invoke = model_caller(self._model, self._tools.tools())
        first = True

        async def ask(messages: Sequence[BaseMessage]) -> AIMessage:
            nonlocal first
            turn, first = prompt if first else "", False
            return await self._ask(invoke, messages, turn)

        return await run_loop(ask, prompt, call=self._call)

    async def tool(self, name: str, **args: Json) -> str:
        """도구가 ok=false 를 돌려주든 예외를 던지든 에이전트에게는 같은 ToolError 다."""
        result = await self._call(name, args)
        if not result.ok:
            raise ToolError(result.content)
        return result.content

    def take_events(self) -> list[Event]:
        """쌓인 이벤트를 비우며 돌려준다. 호출 안의 이벤트가 에이전트의 다음 이벤트보다 앞선다."""
        taken, self._pending = self._pending, []
        return taken

    def replay_event(self, event: Event) -> None:
        """재생 구간에서 에이전트가 낸 이벤트를 기록과 맞춰 소비한다. 조립부가 부른다."""
        self._replay.take_agent_event(event)

    async def _ask(
        self, invoke: ModelCaller, messages: Sequence[BaseMessage], prompt: str
    ) -> AIMessage:
        """모델 한 턴. 재생 구간이면 기록을 되살리고 포트를 건드리지 않는다.

        prompt 는 루프의 첫 턴에만 차 있고 둘째 턴부터는 빈 문자열이다. 둘째 턴부터의 입력은
        기록에서 파생되므로 같은 값을 턴마다 되풀이해 적지 않는다(ADR 0009 의 2026-09-22 이력).
        """
        replayed = self._replay.take_model(prompt)
        if replayed is not None:
            return message_from(replayed)
        if self._verdict is not None:
            raise Mismatch(
                f"멈춘 도구 호출 {self._verdict.paused.tool} 대신 모델을 부르려 했다. "
                "에이전트가 바뀌었다"
            )
        self._resume()
        message = await invoke(messages)
        self._record_model_call(reply_from(message), prompt)
        return message

    async def _call(self, name: str, args: Mapping[str, Json]) -> ToolResult:
        """도구 하나. 재생 구간이면 기록된 결과를 돌려주고 게이트도 지나지 않는다.

        재생 구간에서 게이트를 다시 걸지 않는 이유는, 기록된 성공 또는 실패 결과를 돌려주고 도구를
        다시 부르지 않기 때문이다. 거부된 호출도 실패로 기록되어 같은 길로 되살아난다. 재생이 끝난
        뒤 첫 실제 호출은 멈췄던 그 호출이어야 하고, 결정은 그 호출에만 적용된다.

        대조가 소비보다 앞이다. Mismatch 는 Exception 이라 에이전트가 삼키고 다시 부를 수 있는데,
        먼저 소비하면 그때 결정이 사라져 거부한 호출이 정책이 풀린 도구로 실행될 수 있다.
        """
        self._stay_paused()
        masked = _mask(name, args, self._policy.secrets)
        replayed = self._replay.take_tool(name, masked)
        if replayed is not None:
            return ToolResult(ok=replayed.ok, content=replayed.content)
        if self._verdict is not None:
            _require_paused_call(self._verdict.paused, name, masked)
        verdict = self._take_verdict()
        self._resume()
        if verdict is None:
            if name in self._policy.approvals:
                self._pause(name, masked)
        else:
            # 결정의 종류마다 갈래가 있어야 한다. 폴스루로 승인하면 새 결정이 조용히 승인으로 돈다.
            match verdict.decision:
                case Deny(reason=reason):
                    return self._deny(name, masked, reason)
                case Approve():
                    pass
                case _:
                    assert_never(verdict.decision)
        _reject_masked_args(name, args, self._policy.secrets)
        result = await _call_safely(self._tools, name, args)
        self._record_tool_call(name, masked, result)
        return result

    def _take_verdict(self) -> _Verdict | None:
        """결정 하나는 도구 하나만 판정한다. 그래서 둘째 승인 대상에서 다시 멈춘다."""
        verdict, self._verdict = self._verdict, None
        return verdict

    def _deny(self, name: str, masked: Mapping[str, Json], reason: str) -> ToolResult:
        """거부는 실행을 끝내지 않는다. 도구를 부르지 않은 채 실패한 결과로 기록해 돌려준다.

        이미 있는 도구 실패 경로 그대로다. 루프는 사유를 모델에 되돌려 계속하고, 직접 부른
        에이전트는 ToolError 로 받아 이름으로 잡는다(ADR 0009). 기록이 남으므로 다음 재생에서도
        이 호출은 실패로 되살아나고 실제로 불리지 않는다. 뒤의 승인이 앞의 거부를 뒤집지 않는다.
        """
        result = ToolResult(ok=False, content=f"승인자가 거부했다: {reason}")
        self._record_tool_call(name, masked, result)
        return result

    def _resume(self) -> None:
        """재생 구간이 끝나는 자리. 실제 실행은 여기서부터이고 시계도 여기서 움직인다."""
        if self._resumed or not self._replay.resuming:
            return
        self._resumed = True
        self._pending.append(RunResumed(run_id=self.run_id, ts=self._clock.now()))

    def _pause(self, name: str, masked: Mapping[str, Json]) -> NoReturn:
        """도구를 부르지 않은 채 일시정지를 기록하고 실행을 끝낸다."""
        self._pending.append(
            RunPaused(run_id=self.run_id, ts=self._clock.now(), tool=name, args=masked)
        )
        self._paused = True
        raise _Paused()

    def _stay_paused(self) -> None:
        """멈춘 뒤에는 모델도 도구도 부르지 않는다. 신호를 삼킨 에이전트가 이어 가지 못하게."""
        if self._paused:
            raise _Paused()

    def _record_model_call(self, reply: ModelReply, prompt: str) -> None:
        self._pending.append(
            LlmCalled(
                run_id=self.run_id,
                ts=self._clock.now(),
                model=reply.model,
                input_tokens=reply.input_tokens,
                output_tokens=reply.output_tokens,
                prompt=prompt,
                text=reply.text,
                tool_calls=tuple(
                    ToolCall(
                        id=call.id,
                        name=call.name,
                        args=_mask(call.name, call.args, self._policy.secrets),
                    )
                    for call in reply.tool_calls
                ),
            )
        )

    def _record_tool_call(self, name: str, masked: Mapping[str, Json], result: ToolResult) -> None:
        self._pending.append(
            ToolCalled(
                run_id=self.run_id,
                ts=self._clock.now(),
                tool=name,
                ok=result.ok,
                args=masked,
                content=result.content,
            )
        )


async def run(
    agent: AgentName,
    request: str,
    principal: Principal,
    *,
    plugins: PluginSource,
    model: ChatModel,
    tools: ToolSource,
    trace: TraceStore,
    clock: Clock,
) -> AsyncIterator[Event]:
    prepared = _prepare(plugins, _requested_manifest(plugins, agent))
    run_id = clock.new_run_id()
    started = RunStarted(
        run_id=run_id, ts=clock.now(), agent=agent, request=request, principal=principal
    )
    trace.write(started)
    yield started
    async for event in _drive(
        prepared,
        started,
        replay=Replay.nothing(),
        verdict=None,
        model=model,
        tools=tools,
        trace=trace,
        clock=clock,
    ):
        yield event


async def resume(
    run_id: RunId,
    decision: Decision,
    approver: Principal,
    *,
    plugins: PluginSource,
    model: ChatModel,
    tools: ToolSource,
    trace: TraceStore,
    clock: Clock,
) -> AsyncIterator[Event]:
    """같은 실행을 이어 간다. 새 실행이 아니라 run_id 도 트레이스 파일도 하나다.

    에이전트 이름과 요청은 트레이스의 시작 이벤트에서 읽는다. 결정이 트레이스에 먼저 기록된 뒤
    재생이 시작되므로, 재생이 무엇을 하든 누가 허락했는지, 누가 왜 막았는지는 남는다.

    첫 걸음(트레이스 읽기, 일시정지 확인, 결정 쓰기)에 await 가 없다. 같은 실행에 동시에 온 둘째
    결정이 마지막 이벤트를 결정으로 읽어 재개 불가가 되는 것이 이것 하나에 기댄다(ADR 0014). 읽기나
    쓰기를 비동기로 바꾸거나 스레드로 보내면 승인된 도구가 두 번 실행된다. HTTP 채널의 동시 재개
    테스트가 그것을 고정한다.
    """
    started, paused, records = _read_paused(trace, run_id)
    prepared = _prepare(plugins, _recorded_manifest(plugins, started))
    decided = _decision_event(run_id, decision, approver, clock)
    trace.write(decided)
    yield decided
    async for event in _drive(
        prepared,
        started,
        replay=Replay.of(records),
        verdict=_Verdict(decision, paused),
        model=model,
        tools=tools,
        trace=trace,
        clock=clock,
    ):
        yield event


async def _drive(
    prepared: _Prepared,
    started: RunStarted,
    *,
    replay: Replay,
    verdict: _Verdict | None,
    model: ChatModel,
    tools: ToolSource,
    trace: TraceStore,
    clock: Clock,
) -> AsyncIterator[Event]:
    """도구를 연결한 채 에이전트를 돌리고 결말을 붙인다. run() 과 resume() 이 공유하는 몸통."""
    run_id = started.run_id

    # 런타임이 실제로 게이트에서 멈췄는가. 이벤트 종류로 판정하지 않는 이유는 에이전트가
    # run_paused 를 지어내 yield 할 수 있기 때문이다. 에이전트는 신뢰 경계 밖이다.
    paused = False

    def emit(event: Event) -> Event:
        trace.write(event)
        return event

    async def execute() -> AsyncGenerator[Event]:
        """실패해도 그때까지 쌓인 이벤트를 먼저 흘린다.

        일시정지는 실패가 아니다. 신호를 여기서 받아 연결을 정상으로 닫고, 쌓인 이벤트의 끝에
        run_paused 가 있다. 에이전트가 신호를 삼키고 이어 가도 그 뒤의 이벤트는 통과시키지 않고,
        신호를 다른 예외로 감싸 올려도 멈춘 실행에 run_failed 가 덧붙지 않는다.
        """
        nonlocal paused
        async with tools.connect(prepared.servers) as connection:
            _reject_unknown_declarations(prepared.policy, connection.tools())
            ctx = _Context(started, clock, model, connection, prepared.policy, replay, verdict)
            try:
                async for event in prepared.instance.run(started.request, ctx):
                    for pending in ctx.take_events():
                        yield pending
                    if ctx.paused:
                        break
                    if ctx.replaying:
                        ctx.replay_event(event)
                        continue
                    yield event
            except _Paused:
                pass
            except Exception:
                if not ctx.paused:
                    raise
            finally:
                paused = ctx.paused
                for pending in ctx.take_events():
                    yield pending

    # 안쪽 제너레이터를 여기서 닫는다. 트레이스 쓰기가 실패하면 예외가 이 몸통에서 나고, 그때
    # execute() 는 도구 연결 안의 yield 에 멈춰 있다. 가비지 수집에 맡기면 다른 태스크가 그것을 닫아
    # MCP 어댑터의 anyio 취소 범위가 깨진다 — 연결은 연 태스크가 닫아야 한다(http-channel 티켓 03).
    last: Event | None = None
    async with aclosing(execute()) as executed:
        try:
            async for event in executed:
                last = event
                yield emit(event)
        except Exception as error:
            # 멈춘 뒤에 나는 예외는 도구 연결의 정리뿐이다. 일시정지가 트레이스에 이미 있으므로
            # 그 위에 run_failed 를 덧붙이지 않는다. 덧붙이면 재개가 그 실행을 실패로 읽는다.
            if not paused:
                yield emit(RunFailed(run_id=run_id, ts=clock.now(), error=_describe(error)))
            return
    if not paused and not isinstance(last, RunFinished):
        yield emit(
            RunFailed(run_id=run_id, ts=clock.now(), error="에이전트가 run_finished 없이 끝났다")
        )


def _decision_event(
    run_id: RunId, decision: Decision, approver: Principal, clock: Clock
) -> ApprovalGranted | ApprovalDenied:
    """결정을 트레이스에 남는 이벤트로. 승인과 거부가 별도 클래스인 이유는 sdk 의 events.py."""
    match decision:
        case Deny(reason=reason):
            return ApprovalDenied(run_id=run_id, ts=clock.now(), approver=approver, reason=reason)
        case Approve():
            return ApprovalGranted(run_id=run_id, ts=clock.now(), approver=approver)
        case _:
            assert_never(decision)


def _prepare(plugins: PluginSource, manifest: PluginManifest) -> _Prepared:
    """실행 식별자가 생기기 전에 끝나는 검사들. 여기서 나는 오류는 트레이스가 없다.

    에이전트의 매니페스트는 부르는 쪽이 읽어 넘긴다. 없을 때의 뜻이 `run()` 과 `resume()` 에서
    다르기 때문이다(`_requested_manifest`, `_recorded_manifest`).
    """
    servers = _resolve_servers(plugins, manifest)
    _reject_masked_approvals(manifest, servers)
    return _Prepared(
        servers=servers,
        policy=_Policy(
            secrets=secret_args_by_tool(servers),
            approvals=frozenset(manifest.requires_approval),
        ),
        instance=plugins.load_agent(manifest),
    )


def _require_paused_call(paused: RunPaused, name: str, masked: Mapping[str, Json]) -> None:
    """재개 뒤 첫 실제 도구 호출이 멈춘 그 호출인지. 인자는 마스킹된 것끼리 비교한다."""
    if paused.tool != name or dict(paused.args) != dict(masked):
        raise Mismatch(
            f"재개 뒤 첫 호출이 멈춘 자리와 다르다. 멈춘 것은 도구 {paused.tool} "
            f"{dict(paused.args)}, 지금 {name} {dict(masked)}. 결정을 적용하지 않는다"
        )


def _read_paused(
    trace: TraceStore, run_id: RunId
) -> tuple[RunStarted, RunPaused, tuple[Record, ...]]:
    """재개의 입력을 읽고 재개할 수 없는 것을 거부한다. 트레이스를 신뢰하는 유일한 자리다.

    시작 이벤트(에이전트와 요청), 마지막 일시정지(결정이 묶이는 호출), 재생 기록을 돌려준다.
    """
    stored = trace.read(run_id)
    if stored is None:
        raise Absent(f"그런 실행이 없다: {run_id}")
    if stored.schema_version not in RESUMABLE:
        raise NotResumable(
            f"형식 {stored.schema_version} 트레이스는 읽을 수는 있어도 재개할 수 없다: {run_id}"
        )
    events = _sound_events(stored, run_id)
    started = events[0]
    if not isinstance(started, RunStarted):
        raise PluginError(f"시작 이벤트로 열리지 않는 트레이스는 재개할 수 없다: {run_id}")
    paused = events[-1]
    if not isinstance(paused, RunPaused):
        raise NotResumable(f"일시정지 상태가 아니라 재개할 수 없다: {run_id}")
    return started, paused, tuple(e for e in events if not isinstance(e, _BOUNDARY))


def _sound_events(stored: Trace, run_id: RunId) -> tuple[Event, ...]:
    """손상된 트레이스를 거른다. 정상 쓰기 경로에서는 어긋날 수 없는 것들이다(티켓 02 리뷰)."""
    known = tuple(e for e in stored.events if not isinstance(e, UnknownEvent))
    if len(known) != len(stored.events):
        raise PluginError(f"모르는 종류의 이벤트가 있어 재생할 수 없다: {run_id}")
    if not known:
        raise PluginError(f"비어 있는 트레이스는 재개할 수 없다: {run_id}")
    if stored.run_id != run_id or any(event.run_id != run_id for event in known):
        raise PluginError(f"실행 식별자가 어긋난 트레이스는 재개할 수 없다: {run_id}")
    return known


def _requested_manifest(plugins: PluginSource, agent: AgentName) -> PluginManifest:
    """요청이 이름을 댄 에이전트. 없으면 부재다."""
    manifest = plugins.read_manifest(PluginKind.AGENT, PluginName(agent))
    if manifest is None:
        raise Absent(f"에이전트 플러그인이 없다: {agent}")
    return manifest


def _recorded_manifest(plugins: PluginSource, started: RunStarted) -> PluginManifest:
    """재개할 실행의 트레이스가 가리키는 에이전트. 없으면 부재가 아니라 구성 오류다.

    이름을 댄 것이 요청이 아니라 서버가 가진 기록이고, 요청이 가리킨 실행은 있다. 클라이언트가
    고칠 수 없는 일이라 부재로 말하면 식별자를 잘못 적었다고 믿게 된다(ADR 0014 의 2026-09-24
    이력). 에이전트가 가리키는 mcp 플러그인이 없을 때와 같은 모양이다.
    """
    manifest = plugins.read_manifest(PluginKind.AGENT, PluginName(started.agent))
    if manifest is None:
        raise PluginError(f"실행 {started.run_id} 의 에이전트 플러그인이 없다: {started.agent}")
    return manifest


def _resolve_servers(
    plugins: PluginSource, manifest: PluginManifest
) -> dict[PluginName, McpServer]:
    """매니페스트가 지정한 mcp 플러그인만. 비어 있으면 도구가 없다(ADR 0002)."""
    servers: dict[PluginName, McpServer] = {}
    for name in manifest.mcp:
        mcp = plugins.read_manifest(PluginKind.MCP, name)
        if mcp is None or mcp.server is None:
            raise PluginError(f"에이전트 {manifest.name} 이 지정한 mcp 플러그인이 없다: {name}")
        servers[name] = mcp.server
    return servers


def _reject_masked_approvals(
    manifest: PluginManifest, servers: Mapping[PluginName, McpServer]
) -> None:
    """금지 규칙을 실행 식별자가 생기기 전에 거부로 바꾼다. 이유는 sdk 의 approval_conflicts."""
    conflicts = approval_conflicts(manifest, servers)
    if conflicts:
        raise PluginError(
            f"마스킹된 인자를 가진 도구는 승인 대상이 될 수 없다: {', '.join(conflicts)}"
        )


def _reject_unknown_declarations(policy: _Policy, specs: Sequence[ToolSpec]) -> None:
    """매니페스트가 가리키는 도구와 인자가 실재하는지. 도구 목록이 연결 뒤에 나와 여기가 첫 자리다.

    오타나 중첩 프로퍼티가 게이트나 마스킹을 조용히 끄는 fail-open 을 막는다(ADR 0009 와 그
    2026-09-21 이력). 실행 안이라 run_failed 로 끝나고 트레이스가 남는다. 재개에서도 같은
    자리에서 도므로, 승인을 기다리는 사이 매니페스트가 바뀌었으면 여기서 먼저 걸린다.
    """
    params = {spec.name: _param_names(spec) for spec in specs}
    for tool in policy.approvals:
        if tool not in params:
            raise LookupError(f"requires_approval 이 가리키는 도구가 없다: {tool}")
    for tool, names in policy.secrets.items():
        if tool not in params:
            raise LookupError(f"secret_args 가 가리키는 도구가 없다: {tool}")
        for name in names:
            if name not in params[tool]:
                raise LookupError(f"secret_args 가 가리키는 인자가 도구 {tool} 에 없다: {name}")


def _param_names(spec: ToolSpec) -> frozenset[str]:
    """JSON Schema 의 properties 키. 없으면 이름 있는 인자가 없는 도구다."""
    properties = spec.input_schema.get("properties")
    return frozenset(properties) if isinstance(properties, dict) else frozenset()


async def _call_safely(tools: ToolConnection, name: str, args: Mapping[str, Json]) -> ToolResult:
    """도구가 예외를 내도 실행은 죽지 않는다. 에러 내용을 결과로 바꿔 모델이 알게 한다."""
    try:
        return await tools.call(name, args)
    except Exception as error:
        return ToolResult(ok=False, content=_describe(error))


def _describe(error: BaseException) -> str:
    """ExceptionGroup 은 겉만 보면 원인을 알 수 없어서 안의 예외를 펼친다."""
    if _is_group(error):
        inner = "; ".join(_describe(e) for e in error.exceptions)
        return f"{type(error).__name__}[{inner}]"
    return f"{type(error).__name__}: {error}"


def _is_group(error: BaseException) -> TypeGuard[BaseExceptionGroup[BaseException]]:
    """isinstance 로 좁히면 pyright 가 타입 인자를 Unknown 으로 둔다. 여기서 명시한다."""
    return isinstance(error, BaseExceptionGroup)
