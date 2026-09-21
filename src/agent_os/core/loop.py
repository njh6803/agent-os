"""루프. 모델을 부르고, 모델이 도구를 부르면 실행해 되돌리고, 모델이 멈출 때까지 반복한다.

런타임이 소유한다. 에이전트는 ctx.llm() 한 번으로 이 전체를 돌린다.
LangGraph 대신 langchain-core 위에 직접 쓴다. 근거는 ADR 0001의 2026-09-21 후퇴 기록.
"""

from __future__ import annotations

from collections.abc import Callable

from langchain_core.messages import BaseMessage, HumanMessage

from agent_os.core.model import ModelReply, reply_from
from agent_os.core.ports import ChatModel

MAX_TURNS = 10


class LoopLimitExceeded(Exception):
    """모델이 상한 안에 멈추지 않았다. 비용이 무한정 늘지 않게 한다."""


async def run_loop(
    model: ChatModel,
    prompt: str,
    *,
    on_model_call: Callable[[ModelReply], None],
) -> str:
    """마지막 텍스트를 돌려준다. 모델 호출마다 on_model_call 이 불려 실패해도 앞선 호출이 남는다."""
    messages: list[BaseMessage] = [HumanMessage(prompt)]
    for _ in range(MAX_TURNS):
        message = await model.ainvoke(messages)
        on_model_call(reply_from(message))
        if not message.tool_calls:
            return message.text
        # TODO(first-slice/07): 도구를 실행해 ToolMessage 로 되돌린다. 지금은 도구가 없다
        messages.append(message)
    raise LoopLimitExceeded(f"루프가 {MAX_TURNS}턴 안에 멈추지 않았다")
