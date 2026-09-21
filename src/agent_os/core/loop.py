"""루프. 모델을 부르고, 모델이 도구를 부르면 실행해 되돌리고, 모델이 멈출 때까지 반복한다.

런타임이 소유한다. 에이전트는 ctx.llm() 한 번으로 이 전체를 돌린다.
LangGraph 대신 langchain-core 위에 직접 쓴다. 근거는 ADR 0001의 2026-09-21 후퇴 기록.

모델도 도구도 연결이 아니라 호출 함수 하나씩으로 받는다. 승인 게이트, 마스킹, 기록, 재생이 그
함수들 안에 있어 루프와 컨텍스트의 직접 호출이 같은 길을 지난다(ADR 0009: 정책은 도구에 붙지
경로에 붙지 않는다). 재생이 실제 포트 대신 기록을 돌려주는 자리도 거기라 루프는 재개를 모른다.

실패 정책(`.claude/rules/core.md`): 도구 에러는 호출 함수가 ok=false 로 돌려주고 루프는 그 내용을
모델에 되돌려 계속한다. 상한 10턴을 넘으면 LoopLimitExceeded. 모델 API 에러는 SDK 재시도 뒤 그대로
올린다.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping, Sequence

from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.messages.tool import ToolCall
from langchain_core.runnables import Runnable

from agent_os.core.ports import ChatModel, ToolResult, ToolSpec
from agent_os.sdk import Json

MAX_TURNS = 10

# 도구 하나를 부른다. 예외를 내지 않고 실패를 ok=false 로 돌려준다.
type ToolCaller = Callable[[str, Mapping[str, Json]], Awaitable[ToolResult]]

# 모델 한 턴을 부른다. 기록에 남기는 것도 재생으로 대신하는 것도 이 안이다.
type ModelCaller = Callable[[Sequence[BaseMessage]], Awaitable[AIMessage]]


class LoopLimitExceeded(Exception):
    """모델이 상한 안에 멈추지 않았다. 비용이 무한정 늘지 않게 한다."""


async def run_loop(ask: ModelCaller, prompt: str, *, call: ToolCaller) -> str:
    """마지막 텍스트를 돌려준다.

    상한은 실행 전체 기준이고 재생된 턴도 센다. 재생이 ask 안쪽에 있어 재개해도 이 for 가 처음부터
    돌기 때문에 저절로 그렇다. 상한이 재개로 리셋되면 멈추고-재개를 반복해 무한히 돌 수 있다.
    """
    messages: list[BaseMessage] = [HumanMessage(prompt)]
    for _ in range(MAX_TURNS):
        message = await ask(messages)
        if not message.tool_calls:
            return message.text
        messages.append(message)
        for tool_call in message.tool_calls:
            messages.append(await _execute(call, tool_call))
    raise LoopLimitExceeded(f"루프가 {MAX_TURNS}턴 안에 멈추지 않았다")


def model_caller(model: ChatModel, specs: Sequence[ToolSpec]) -> ModelCaller:
    """도구를 붙인 모델을 부르는 함수 하나. bind 와 Runnable 이 여기서 끝난다.

    컨텍스트는 이것을 받아 재생이나 기록으로 감싼다. 그래서 langchain 의 Runnable 이 게이트와
    재생이 있는 자리까지 새지 않는다(CODING_STANDARDS "서드파티는 경계에서 감싼다").
    """
    bound = _bind(model, specs)

    async def invoke(messages: Sequence[BaseMessage]) -> AIMessage:
        return await bound.ainvoke(messages)

    return invoke


def _bind(model: ChatModel, specs: Sequence[ToolSpec]) -> Runnable[LanguageModelInput, AIMessage]:
    if not specs:
        return model
    return model.bind_tools([_anthropic_style(spec) for spec in specs])


def _anthropic_style(spec: ToolSpec) -> dict[str, object]:
    """langchain 이 받는 도구 dict 형식 중 하나. input_schema 키가 JSON Schema 다."""
    return {
        "name": spec.name,
        "description": spec.description,
        "input_schema": dict(spec.input_schema),
    }


async def _execute(call: ToolCaller, tool_call: ToolCall) -> ToolMessage:
    result = await call(tool_call["name"], tool_call["args"])
    return ToolMessage(
        content=result.content,
        tool_call_id=tool_call["id"] or "",
        status="success" if result.ok else "error",
    )
