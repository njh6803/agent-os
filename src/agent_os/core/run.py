"""주 이음매. 에이전트를 돌려 이벤트를 내는 async generator 둘, run() 과 resume().

로더, 루프, 도구 연결, 승인 게이트, 재생, 트레이스 기록, 실패 정책이 전부 이 아래에 있어서 기본
스위트가 이 지점 하나를 민다. run_started, run_paused, approval_granted, approval_denied,
run_resumed, run_failed 는 런타임이 내고, 에이전트는 run_finished 하나를 마지막에 낸다.
conversation_summarized 는 런타임만 낼 수 있다(내는 계기와 실패는 conversation 티켓 02). 에이전트가
낸 다른 이벤트는 그대로 통과하되 conversation_summarized 만은 예외다 — 그것은 다음 실행의 거슬러
읽기가 트레이스에서 읽는 입력이라 에이전트가 내면 그 실행은 run_failed 다(ADR 0022). 거부는 실행을
끝내지 않는다. 거부된 도구 호출은 불리지 않고 tool_called(ok=false) 로 사유가 모델에게 돌아가며,
에이전트가 정상적으로 끝맺는다(ADR 0009).

이어 가기는 run() 의 키워드 인자 previous_run 이다(ADR 0022). 재개와 달리 입력이 run() 의 것에 앞
실행 하나가 더해진 것이라 함수를 따로 두지 않는다. 없음(None)은 새 대화라는 뜻 하나뿐이고 고리를
짐작하는 기본값이 없다. 이어 간 실행은 새 실행 식별자와 새 트레이스 파일을 갖고 run_started 에 앞
실행을 적는다. 에이전트는 고리에서 자기가 처리한 교환과 자기 대화 요약만 컨텍스트 멤버로 받는다.

resume() 이 run() 의 인자가 아닌 이유는 입력이 실제로 다르기 때문이다. 재개는 에이전트 이름,
요청, 주체를 받지 않고 트레이스의 run_started 에서 읽는다. 하나로 합치면 "재개일 때는 이 인자
셋이 무시된다"는, 타입으로 막을 수 없는 규칙을 문서로 적어야 한다(ADR 0009). 내부는 _drive 가
공유하고 갈리는 것은 이벤트를 어디서 얻나(재생이냐 실제 호출이냐)와 무엇을 트레이스에 쓰나뿐이다.

재생 구간에서 생긴 사실은 트레이스에 다시 쓰지 않는다. 이미 거기 있기 때문이고, 에이전트가 낸
것도 마찬가지다. 기준은 "재생 구간인가"가 아니라 "이미 트레이스에 있는가"라서, 재생 구간에서
처음 생긴 사실인 대조 불일치의 run_failed 는 쓴다. 사실이 한 번씩만 남는다.

실행 전과 실행 중의 경계: 없는 플러그인, 매니페스트 오류, 진입점 import 실패, 없는 mcp 이름,
마스킹과 승인이 겹치는 도구, 운영자 파일의 손상, 운영자가 끈 에이전트나 mcp, 이어 갈 수 없는 앞
실행(없음, 손상, 다른 주체, 끝나지 않음)과 깨진 고리는 실행 식별자를 만들기 전에 PluginError 로 끝나
트레이스가 없다. 재개할 수 없는 트레이스(없음, 형식 1, 손상, 일시정지 아님)와 지금의 일시정지를
가리키지 않는 결정(자리 어긋남)도 같은 자리의 PluginError 다. 재개에서는 위의 것이 전부(꺼짐과
운영자 파일의 손상, 깨진 고리도) 결정 이벤트를 쓰기 전에 나 트레이스가 그대로다. 저장소가 결정
이벤트를 이어 쓰지 못해도 PluginError 이고 도구를 부르지 않는다(ADR 0012 이력). 하위 타입을 가르는
기준은 "깨졌나"다 — 대상이 없거나 대상의 상태나 주체가 요청을 허락하지 않는 것이 하위 타입이고 남는
것이 서버의 구성이나 기록이 깨진 것이다(ADR 0014 의 2026-09-26 이력). 요청이 댄 에이전트나 실행이나
이어 갈 앞 실행이 없으면 Absent, 실행이 형식 1 이거나 일시정지가 아니거나 결정이 가리킨 자리가
지금의 일시정지가 아니면 NotResumable(ADR 0014 와 그 2026-09-28 이력), 요청이 부른 에이전트나 그것이
쓰는 mcp 를 운영자가 꺼 두었으면 Disabled(ADR 0017), 앞 실행이 다른 주체의 것이면
DifferentPrincipal, 앞 실행이 run_finished 로 끝나지 않았으면 NotContinuable 이다(ADR 0022·0023).
재개할 실행의 트레이스가 가리키는 에이전트가 없는 것과 고리에서 만나는 실행이 없거나 깨진 것은
요청이 아니라 서버의 기록이 댄 것이라 기록과 구성이 어긋난 것, 곧 PluginError 그대로다.
판정 순서는 부재 → 깨짐 → 꺼짐 → 진입점 import 다. 그 이유는 `_prepare`. 이어 가기는 그 앞에 앞
실행(없음 → 손상 → 다른 주체 → 끝나지 않음)과 고리의 판정이 선다. 그 이유는 `_continued` 와 `_walk`.
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
    DifferentPrincipal,
    Disabled,
    NotContinuable,
    NotResumable,
    PluginError,
    PluginKey,
    PluginSource,
    ToolConnection,
    ToolResult,
    ToolSource,
    ToolSpec,
    Trace,
    TraceSchemaVersion,
    TraceStore,
    UnknownEvent,
    run_status,
)
from agent_os.core.replay import Mismatch, Record, Replay
from agent_os.sdk import (
    AgentName,
    ApprovalDenied,
    ApprovalGranted,
    BaseAgent,
    Conversation,
    ConversationSummarized,
    Event,
    Exchange,
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
    is_run_id,
    secret_args_by_tool,
)

MASKED = "***"

# 재개할 수 있는 트레이스 형식. 1 은 재개의 입력이 되는 필드가 비어 있어 읽기만 된다(ADR 0009).
# 어댑터가 쓸 때 붙이는 버전과 뜻이 달라 따로 둔다. 형식이 늘면 여기에 받아들일 것을 더한다. 2 와 3
# 의 차이는 시작 이벤트의 앞 실행과 대화 요약 이벤트뿐이라 둘 다 재개한다(ADR 0022). 이어 가기는
# 형식을 가리지 않는다 — 앞 실행을 재개하는 것이 아니라 읽는 것이고 필요한 것은 형식 1 에도 있다.
RESUMABLE: tuple[TraceSchemaVersion, ...] = ("2", "3")

# 이어 가지 않은 실행의 컨텍스트 멤버. 요약이 없고 교환이 비어 있다.
_NEW_CONVERSATION = Conversation(summary=None, exchanges=())

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

    그 일시정지는 결정이 자리로 가리킨 것이고, 첫 걸음이 그것이 지금의 일시정지인지 이미 확인했다.
    자리가 없으면 결정은 트레이스 끝의 일시정지에 묶여, 사람이 본 화면이 그것보다 오래될 때 본 적
    없는 호출을 판정한다(ADR 0014 의 2026-09-28 이력).

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
        conversation: Conversation,
    ) -> None:
        self.run_id = started.run_id
        self.conversation = conversation
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
    previous_run: RunId | None = None,
    plugins: PluginSource,
    model: ChatModel,
    tools: ToolSource,
    trace: TraceStore,
    clock: Clock,
) -> AsyncIterator[Event]:
    """새 실행 하나. `previous_run` 을 주면 그 끝난 실행을 이어 간다(ADR 0022).

    이어 가기의 판정은 준비보다 앞이다 — 앞 실행(없음 → 손상 → 다른 주체 → 끝나지 않음), 고리,
    그다음 준비(부재 → 깨짐 → 꺼짐 → import). 재개가 트레이스 판정을 준비보다 앞에 두는 것과 같은
    모양이고, 꺼진 에이전트로 이어 가려는 요청도 고리를 다 읽은 뒤에 거절되는 비용이 있다. 전부 실행
    식별자를 만들기 전이라 거절된 이어 가기는 트레이스를 남기지 않는다. 거슬러 읽기는 동기이고
    이벤트 루프 위에서 돈다. 긴 고리가 루프를 막는 것은 알려진 한계다(명세 "고리를 거슬러 읽기").
    """
    conversation = (
        _NEW_CONVERSATION
        if previous_run is None
        else _continued(trace, previous_run, agent, principal)
    )
    prepared = _prepare(plugins, _requested_manifest(plugins, agent))
    run_id = clock.new_run_id()
    started = RunStarted(
        run_id=run_id,
        ts=clock.now(),
        agent=agent,
        request=request,
        principal=principal,
        previous_run=previous_run,
    )
    trace.write(started)
    yield started
    async for event in _drive(
        prepared,
        started,
        replay=Replay.nothing(),
        verdict=None,
        conversation=conversation,
        model=model,
        tools=tools,
        trace=trace,
        clock=clock,
    ):
        yield event


async def resume(
    run_id: RunId,
    pause_index: int,
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

    `pause_index` 는 결정이 답하는 `run_paused` 가 트레이스에서 서는 0부터 센 자리다(ADR 0014 의
    2026-09-28 이력). 결정 값(`Approve`·`Deny`)이 아니라 따로 받는 이유는 그것이 결정의 내용이
    아니라 결정이 답하는 일시정지를 가리키는 주소라서다. 실행 식별자와 함께 "어느 실행의 어느
    일시정지"를 이루고, 게이트는 그것을 쓰지 않는다. 기본값이 없다 — 있으면 그 값이 곧 지금의
    일시정지라 오래된 결정이 승인자가 본 적 없는 호출을 실행한다(fail-open, ADR 0011 의 논증).

    첫 걸음(트레이스 읽기, 일시정지와 자리 확인, 결정 쓰기)에 await 가 없다. 같은 실행에 동시에 온
    둘째 결정이 마지막 이벤트를 결정으로 읽어 재개 불가가 되는 것이 이것 하나에 기댄다(ADR 0014).
    읽기나 쓰기를 비동기로 바꾸거나 스레드로 보내면 승인된 도구가 두 번 실행된다. HTTP 채널의 동시
    재개 테스트가 그것을 고정한다. 둘 사이의 준비(꺼진 집합 읽기를 포함한다)도 첫 걸음 안이라 포트의
    그 읽기가 동기다(ADR 0017). 준비에서 막히면 결정을 쓰기 전이라 실행은 일시정지 그대로다.

    이어 간 실행의 재개는 시작 이벤트의 앞 실행에서 다시 거슬러 읽어 처음과 같은 멤버를 준다(ADR
    0022). 그것도 첫 걸음 안이고 트레이스 판정 뒤, 준비 앞이다. 고리가 깨졌으면 결정 이벤트를 쓰기
    전에 PluginError 라 실행은 일시정지 그대로다 — 멈춘 사이 거슬러 읽는 범위의 트레이스를 지우면
    그렇고, 그보다 오래된 트레이스를 지우면 재개가 그대로 선다. 주체의 비교 대상은 멈춘 실행의
    `run_started` 주체다.
    """
    started, paused, records = _read_paused(trace, run_id, pause_index)
    conversation = _resumed_conversation(trace, started)
    prepared = _prepare(plugins, _recorded_manifest(plugins, started))
    decided = _decision_event(run_id, decision, approver, clock)
    trace.write(decided)
    yield decided
    async for event in _drive(
        prepared,
        started,
        replay=Replay.of(records),
        verdict=_Verdict(decision, paused),
        conversation=conversation,
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
    conversation: Conversation,
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
            ctx = _Context(
                started, clock, model, connection, prepared.policy, replay, verdict, conversation
            )
            try:
                async for event in prepared.instance.run(started.request, ctx):
                    for pending in ctx.take_events():
                        yield pending
                    if ctx.paused:
                        break
                    if isinstance(event, ConversationSummarized):
                        # 런타임만 내는 종류다. 다음 실행의 거슬러 읽기가 트레이스에서 읽는 입력이라
                        # 에이전트가 지어낸 것이 통과하면 런타임의 것과 가를 수 없고, 그 실행을
                        # 지나는 모든 이어 가기가 영구히 깨진다(ADR 0022). 재생 구간에서도 같다.
                        raise RuntimeError(f"에이전트는 대화 요약 이벤트를 낼 수 없다: {run_id}")
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

    순서가 의도다. 깨짐(mcp 들, 마스킹과 승인의 충돌)을 다 본 뒤에 꺼짐을 보고, 진입점 import 는
    꺼짐보다 뒤다. 깨진 것이 먼저 보여야 운영자가 다시 켜기 전에 고칠 것을 알고, import 실패를
    판정하려면 플러그인 코드를 실행해야 하는데 꺼진 에이전트는 그 코드를 돌리지 않는다(ADR 0017,
    plugin-toggle 명세의 "core — 준비 단계의 판정").
    """
    servers = _resolve_servers(plugins, manifest)
    _reject_masked_approvals(manifest, servers)
    _reject_disabled(plugins.read_disabled(), manifest)
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
    trace: TraceStore, run_id: RunId, pause_index: int
) -> tuple[RunStarted, RunPaused, tuple[Record, ...]]:
    """재개의 입력을 읽고 재개할 수 없는 것을 거부한다. 트레이스를 신뢰하는 유일한 자리다.

    시작 이벤트(에이전트와 요청), 결정이 가리킨 일시정지(결정이 묶이는 호출), 재생 기록을 돌려준다.
    판정 순서는 없음 → 형식 1 → 손상 → 일시정지 아님 → 자리 어긋남이다. 일시정지 아님이 자리보다
    먼저라, 같은 자리를 든 결정 둘이 동시에 오면 둘째는 "지나간 자리"가 아니라 "일시정지 아님"을
    듣는다.

    자리로 이벤트를 꺼내지 않고 마지막 이벤트의 자리와 같은지만 본다. 꺼내면 파이썬의 음수 인덱스
    `-1` 이 마지막 이벤트에 맞는다. 같은지만 보면 음수는 언제나 어긋남이다. 채널이 음수를 형식
    오류로 막아도 여기서 그것을 믿지 않는다. 모르는 종류의 이벤트는 손상에서 이미 거부되므로 여기서
    세는 자리는 트레이스 상세 `events` 의 인덱스와 같다.
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
    current = len(events) - 1
    if pause_index != current:
        raise NotResumable(
            f"결정이 가리킨 자리 {pause_index} 는 지금의 일시정지(자리 {current})가 아니라 "
            f"재개할 수 없다: {run_id}"
        )
    return started, paused, tuple(e for e in events if not isinstance(e, _BOUNDARY))


def _sound_events(stored: Trace, run_id: RunId) -> tuple[Event, ...]:
    """손상된 트레이스를 거른다. 정상 쓰기 경로에서는 어긋날 수 없는 것들이다(티켓 02 리뷰).

    재개와 이어 가기의 거슬러 읽기가 같이 쓴다. 문구가 재개를 말하지 않는 이유다.
    """
    known = tuple(e for e in stored.events if not isinstance(e, UnknownEvent))
    if len(known) != len(stored.events):
        raise PluginError(f"모르는 종류의 이벤트가 섞인 트레이스다: {run_id}")
    if not known:
        raise PluginError(f"비어 있는 트레이스다: {run_id}")
    if stored.run_id != run_id or any(event.run_id != run_id for event in known):
        raise PluginError(f"실행 식별자가 어긋난 트레이스다: {run_id}")
    return known


# --- 이어 가기 — 앞 실행의 판정과 고리를 거슬러 읽기(ADR 0022) ------------------------------


@dataclass(frozen=True)
class _Link:
    """고리의 실행 하나에서 거슬러 읽기가 보는 것. 시작 이벤트, 마지막 이벤트, 이벤트 전부, 그리고
    시작 바로 뒤에 선 대화 요약 이벤트(없으면 None). 요약의 자리와 개수는 `_require_link` 가
    본다."""

    started: RunStarted
    last: Event
    events: tuple[Event, ...]
    summary: ConversationSummarized | None

    @property
    def run_id(self) -> RunId:
        return self.started.run_id


def _continued(
    trace: TraceStore, previous: RunId, agent: AgentName, principal: Principal
) -> Conversation:
    """run() 의 이어 가기 판정. 앞 실행을 하위 타입으로 가른 뒤 고리를 거슬러 읽는다.

    순서는 없음(`Absent`) → 손상(`PluginError`) → 다른 주체(`DifferentPrincipal`) → 끝나지 않음
    (`NotContinuable`)이다. 손상이 주체보다 앞인 이유는 손상된 트레이스의 주체를 믿을 수 없어서이고,
    주체가 끝나지 않음보다 앞인 이유는 최종 사용자 경로가 남의 실행을 없는 실행처럼 숨기려면 남의
    실행의 상태가 먼저 드러나면 안 되기 때문이다(ADR 0023). 앞 실행 자신의 앞 실행 필드 패턴과 요약
    자리 위반은 고리의 판정(`_walk`)에 들어 주체와 끝남 뒤다 — 손상이 주체보다 앞이라는 논거와
    갈리지만 동작은 이것이고, 최종 사용자 경로에서는 오히려 존재를 덜 드러낸다(명세 검토).

    요청이 댄 식별자는 포트에 닿기 전에 sdk 의 판정자를 지난다. 런타임은 그런 이름의 트레이스를 만들
    수 없으므로 패턴 위반은 없음이다. 재개는 거르지 않는다(명세 "이어 가기 진입점").
    """
    if not is_run_id(previous):
        raise Absent(f"이어 갈 앞 실행이 없다: {previous}")
    link = _read_link(trace, previous)
    if link is None:
        raise Absent(f"이어 갈 앞 실행이 없다: {previous}")
    if link.started.principal != principal:
        raise DifferentPrincipal(
            f"앞 실행 {previous} 은 요청한 주체의 실행이 아니라 이어 갈 수 없다"
        )
    if not isinstance(link.last, RunFinished):
        raise NotContinuable(
            f"앞 실행 {previous} 은 끝나지 않아 이어 갈 수 없다: 상태 {run_status(link.last)}"
        )
    return _walk(trace, link, agent, principal)


def _resumed_conversation(trace: TraceStore, started: RunStarted) -> Conversation:
    """재개하는 실행의 멤버. 시작 이벤트의 앞 실행에서 다시 거슬러 읽어 처음과 같은 값을 만든다.

    앞 실행이 없으면(이어 가지 않은 실행, 형식 2로 쓰인 트레이스) 거슬러 읽을 것이 없다. 있는데 그
    실행이 없거나 깨졌으면 요청이 아니라 서버의 기록이 가리킨 것이라 `PluginError` 그대로다. 주체의
    비교 대상은 멈춘 실행의 `run_started` 주체다. 이 티켓에서 런타임은 재개하는 실행 자신의
    트레이스에 든 요약 이벤트를 읽지 않는다(티켓 02).
    """
    previous = started.previous_run
    if previous is None:
        return _NEW_CONVERSATION
    if not is_run_id(previous):
        raise PluginError(f"실행 {started.run_id} 의 앞 실행 필드가 패턴을 어긴다: {previous!r}")
    link = _read_link(trace, previous)
    if link is None:
        raise PluginError(f"실행 {started.run_id} 이 이어 간 앞 실행이 없다: {previous}")
    return _walk(trace, link, started.agent, started.principal)


def _read_link(trace: TraceStore, run_id: RunId) -> _Link | None:
    """고리의 실행 하나. 없으면 None, 손상(단건 읽기의 것과 재개가 보는 것)은 PluginError 다."""
    stored = trace.read(run_id)
    if stored is None:
        return None
    events = _sound_events(stored, run_id)
    started = events[0]
    if not isinstance(started, RunStarted):
        raise PluginError(f"시작 이벤트로 열리지 않는 트레이스다: {run_id}")
    last = events[-1]
    second = events[1] if len(events) > 1 else None
    summary = second if isinstance(second, ConversationSummarized) else None
    return _Link(started=started, last=last, events=events, summary=summary)


def _walk(trace: TraceStore, first: _Link, agent: AgentName, principal: Principal) -> Conversation:
    """앞 실행에서 시작 이벤트의 앞 실행 필드를 따라 거슬러 가며 지금 에이전트의 것만 모은다.

    지금 에이전트와 같은 실행은 교환 하나(시작 이벤트의 요청과 run_finished 의 출력)를 내고, 그
    트레이스에 대화 요약 이벤트가 있고 아직 요약을 만나지 않았으면 그것이 가장 가까운 요약이다. 다른
    에이전트의 실행은 교환도 요약도 내지 않고 지나간다. 가장 가까운 요약을 만나면 그 요약이 덮는
    끝의 실행까지 거슬러 가되 그 실행은 읽지 않고 멈춘다. 요약이 없으면 고리의 처음(앞 실행 필드가
    없는 실행)까지 간다. 더 오래된 요약은 쓰지 않는다 — 새 요약은 언제나 앞 요약을 접어 만들어진다.

    실행마다 검증한다(`_require_link`). 어느 것이든 서버의 기록이 가리킨 것이 깨진 것이라
    PluginError 이고 메시지가 그 실행과 이유를 든다. 다음 실행을 읽을지 멈출지는 `_next_link` 가
    가른다. 포트에 가벼운 읽기를 더하지 않고 트레이스 전체를 읽는다 — 비용은 지나는 실행의 수에
    비례하고 측정은 명세의 프로브다.
    """
    summary: ConversationSummarized | None = None
    newest_first: list[Exchange] = []
    visited: set[RunId] = set()
    link: _Link | None = first
    while link is not None:
        visited.add(link.run_id)
        finished = _require_link(link, principal)
        if link.started.agent == agent:
            newest_first.append(Exchange(request=link.started.request, output=finished.output))
            if summary is None and link.summary is not None:
                summary = link.summary
        link = _next_link(trace, link, summary, visited)
    return Conversation(
        summary=None if summary is None else summary.summary,
        exchanges=tuple(reversed(newest_first)),
    )


def _next_link(
    trace: TraceStore,
    link: _Link,
    summary: ConversationSummarized | None,
    visited: set[RunId],
) -> _Link | None:
    """거슬러 읽기의 다음 실행. None 이면 멈춘다 — 고리의 처음이거나 가장 가까운 요약이 덮는 끝이다.

    덮는 끝의 실행은 읽지 않는다. 순환은 지나온 실행 식별자로 보고 멈춤 조건보다 먼저다 — 정상
    고리에서 덮는 끝은 요약보다 오래돼 지나온 실행일 수 없으므로, 되돌아가는 간선의 목적지가 덮는
    끝과 같은 손편집 트레이스만 여기서 갈린다. 요약을 만났는데 덮는 끝 없이 고리의 처음에 닿는 것과
    다음 실행이 없는 것은 기록이 깨진 것이다.
    """
    older = link.started.previous_run
    if older is None:
        if summary is not None:
            raise PluginError(
                f"요약이 덮는 끝 {summary.last_covered_run} 을 만나지 못한 채 고리의 처음 "
                f"{link.run_id} 에 닿았다"
            )
        return None
    if older in visited:
        raise PluginError(f"고리가 순환한다: 실행 {link.run_id} 의 앞 실행 {older} 을 이미 지났다")
    if summary is not None and older == summary.last_covered_run:
        return None
    next_link = _read_link(trace, older)
    if next_link is None:
        raise PluginError(f"고리의 실행이 없다: {older} (실행 {link.run_id} 의 앞 실행)")
    return next_link


def _require_link(link: _Link, principal: Principal) -> RunFinished:
    """고리의 실행 하나가 성한지. 주체, 끝남, 앞 실행 필드의 패턴, 요약의 자리·개수·덮는 끝의 패턴.
    끝남을 본 그 `run_finished` 를 돌려줘 부르는 쪽이 다시 좁히지 않는다.

    요청이 댄 앞 실행에서는 주체와 끝남이 하위 타입으로 먼저 걸러져 여기서는 지나가고, 고리의 중간
    실행에서는 전부 기록이 깨진 것이다(ADR 0022).
    """
    run_id = link.run_id
    if link.started.principal != principal:
        raise PluginError(f"고리의 실행 {run_id} 은 다른 주체의 실행이다")
    if not isinstance(link.last, RunFinished):
        raise PluginError(f"고리의 실행 {run_id} 은 끝나지 않았다: 상태 {run_status(link.last)}")
    older = link.started.previous_run
    if older is not None and not is_run_id(older):
        raise PluginError(f"고리의 실행 {run_id} 의 앞 실행 필드가 패턴을 어긴다: {older!r}")
    at = [
        index
        for index, event in enumerate(link.events)
        if isinstance(event, ConversationSummarized)
    ]
    if len(at) > 1:
        raise PluginError(f"고리의 실행 {run_id} 에 대화 요약 이벤트가 둘 이상이다")
    if at and at[0] != 1:
        raise PluginError(
            f"고리의 실행 {run_id} 의 대화 요약 이벤트가 시작 바로 뒤의 자리가 아니다"
        )
    found = link.summary
    if found is not None and not is_run_id(found.last_covered_run):
        raise PluginError(
            f"고리의 실행 {run_id} 의 요약이 덮는 끝이 패턴을 어긴다: {found.last_covered_run!r}"
        )
    return link.last


def _requested_manifest(plugins: PluginSource, agent: AgentName) -> PluginManifest:
    """요청이 이름을 댄 에이전트. 없으면 부재다."""
    manifest = plugins.read_manifest(PluginKind.AGENT, PluginName(agent))
    if manifest is None:
        raise Absent(f"에이전트 플러그인이 없다: {agent}")
    return manifest


def _recorded_manifest(plugins: PluginSource, started: RunStarted) -> PluginManifest:
    """재개할 실행의 트레이스가 가리키는 에이전트. 없으면 부재가 아니라 구성 오류다.

    이름을 댄 것이 요청이 아니라 서버가 가진 기록이고, 요청이 가리킨 실행은 있다. 기록과 구성이
    어긋난 것, 곧 깨진 것이라 부재로 말하면 식별자를 잘못 적었다고 믿게 된다(ADR 0014 의
    2026-09-24·2026-09-26 이력). 에이전트가 가리키는 mcp 플러그인이 없을 때와 같은 모양이다.
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


def _reject_disabled(disabled: frozenset[PluginKey], manifest: PluginManifest) -> None:
    """운영자가 끈 것을 부른 실행을 거부한다. 에이전트가 먼저이고 mcp 는 매니페스트에 적힌 순서다.

    꺼진 집합은 부르는 쪽이 한 번 읽어 넘긴다. 에이전트와 mcp 들을 같은 순간의 상태로 판정하기
    위해서다(ADR 0012 의 2026-09-26 이력). 메시지는 꺼진 것의 종류와 이름이다 — 켜진 에이전트가 꺼진
    mcp 때문에 거부되면 운영자에게 켜 달라고 할 것이 그 mcp 이기 때문이다.
    """
    agent = PluginKey(kind=PluginKind.AGENT, name=manifest.name)
    if agent in disabled:
        raise Disabled(f"꺼진 플러그인이다: {agent.kind} {agent.name}")
    for name in manifest.mcp:
        mcp = PluginKey(kind=PluginKind.MCP, name=name)
        if mcp in disabled:
            raise Disabled(
                f"꺼진 플러그인이다: {mcp.kind} {mcp.name} (에이전트 {manifest.name} 이 쓴다)"
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
