"""ChatModel 포트를 통한 호출. 프로바이더 타입이 여기서 우리 타입으로 바뀐다.

langchain의 AIMessage는 이 모듈 밖으로 나가지 않는다(CODING_STANDARDS "서드파티는 경계에서 감싼다").
"""

from __future__ import annotations

from dataclasses import dataclass

from langchain_core.messages import AIMessage, HumanMessage

from agent_os.core.ports import ChatModel


@dataclass(frozen=True)
class ModelReply:
    text: str
    input_tokens: int
    output_tokens: int


async def call_model(model: ChatModel, prompt: str) -> ModelReply:
    message = await model.ainvoke([HumanMessage(prompt)])
    return _wrap(message)


def _wrap(message: AIMessage) -> ModelReply:
    usage = message.usage_metadata
    if usage is None:
        return ModelReply(text=message.text, input_tokens=0, output_tokens=0)
    return ModelReply(
        text=message.text,
        input_tokens=usage["input_tokens"],
        output_tokens=usage["output_tokens"],
    )
