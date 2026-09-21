"""루프. 모델을 부르고, 모델이 도구를 부르면 실행해 되돌리고, 모델이 멈출 때까지 반복한다.

런타임이 소유한다. 에이전트는 ctx.llm() 한 번으로 이 전체를 돌린다.
LangGraph 대신 langchain-core 위에 직접 쓴다. 근거는 ADR 0001의 2026-09-21 후퇴 기록.

실패 정책(`.claude/rules/core.md`): 도구 에러는 ok=false 로 기록하고 에러 내용을 모델에
되돌려 계속한다. 상한 10턴을 넘으면 LoopLimitExceeded. 모델 API 에러는 SDK 재시도 뒤 그대로 올린다.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence

from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.messages.tool import ToolCall
from langchain_core.runnables import Runnable

from agent_os.core.model import ModelReply, reply_from
from agent_os.core.ports import ChatModel, ToolConnection, ToolResult, ToolSpec
from agent_os.sdk import Json

MAX_TURNS = 10


class LoopLimitExceeded(Exception):
    """모델이 상한 안에 멈추지 않았다. 비용이 무한정 늘지 않게 한다."""


async def run_loop(
    model: ChatModel,
    prompt: str,
    *,
    tools: ToolConnection,
    on_model_call: Callable[[ModelReply], None],
    on_tool_call: Callable[[str, Mapping[str, Json], ToolResult], None],
) -> str:
    """마지막 텍스트를 돌려준다. 호출마다 콜백이 불려 중간에 실패해도 앞선 호출이 남는다."""
    bound = _bind(model, tools.tools())
    messages: list[BaseMessage] = [HumanMessage(prompt)]
    for _ in range(MAX_TURNS):
        message = await bound.ainvoke(messages)
        on_model_call(reply_from(message))
        if not message.tool_calls:
            return message.text
        messages.append(message)
        for call in message.tool_calls:
            messages.append(await _execute(tools, call, on_tool_call))
    raise LoopLimitExceeded(f"루프가 {MAX_TURNS}턴 안에 멈추지 않았다")


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


async def _execute(
    tools: ToolConnection,
    call: ToolCall,
    on_tool_call: Callable[[str, Mapping[str, Json], ToolResult], None],
) -> ToolMessage:
    result = await _call_safely(tools, call)
    on_tool_call(call["name"], call["args"], result)
    return ToolMessage(
        content=result.content,
        tool_call_id=call["id"] or "",
        status="success" if result.ok else "error",
    )


async def _call_safely(tools: ToolConnection, call: ToolCall) -> ToolResult:
    """도구가 예외를 내도 실행은 죽지 않는다. 에러 내용을 결과로 바꿔 모델이 알게 한다."""
    try:
        return await tools.call(call["name"], call["args"])
    except Exception as error:
        return ToolResult(ok=False, content=f"{type(error).__name__}: {error}")
