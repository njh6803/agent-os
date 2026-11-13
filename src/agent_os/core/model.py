"""ChatModel(모델 소스가 만든 모델)이 돌려준 것을 우리 타입으로 바꾸는 경계.

langchain의 AIMessage는 루프 밖으로 나가지 않는다(CODING_STANDARDS "서드파티는 경계에서 감싼다").
"""

from __future__ import annotations

from dataclasses import dataclass

from langchain_core.messages import AIMessage
from langchain_core.messages.ai import UsageMetadata
from langchain_core.messages.tool import ToolCall as LangchainToolCall

from agent_os.sdk import LlmCalled, ToolCall


@dataclass(frozen=True)
class ModelReply:
    model: str
    text: str
    input_tokens: int
    output_tokens: int
    tool_calls: tuple[ToolCall, ...]


def reply_from(message: AIMessage) -> ModelReply:
    """모델의 응답을 우리 타입으로 바꾼다. 바꾸지 못하는 응답은 여기서 거절한다.

    인자가 올바른 JSON이 아닌 도구 호출은 라이브러리가 비스트리밍 응답에서 예외 없이 `tool_calls`
    에서 빼 `invalid_tool_calls` 에 넣는다. 그대로 읽으면 루프가 그 응답을 빈 최종 답으로 받으므로,
    멀쩡한 호출이 섞여 있어도 응답 전체를 거절한다. 문구는 도구 이름만 든다. 깨진 인자의 글과
    라이브러리의 `error` 글은 서버가 보낸 글을 되울릴 수 있어 싣지 않는다. 도구 이름도 서버가 정한
    값이지만 어느 도구였는지가 실패 내용의 쓸모라 싣는다. 이름에 키를 실어 보내는 서버는 가리지
    않는다(`.scratch/local-model/spec.md`).
    """
    if message.invalid_tool_calls:
        names = ", ".join(call["name"] or "(이름 없음)" for call in message.invalid_tool_calls)
        raise ValueError(f"모델이 낸 도구 호출의 인자가 올바른 JSON 이 아니다: {names}")
    usage = message.usage_metadata
    return ModelReply(
        model=_model_name(message),
        text=message.text,
        input_tokens=usage["input_tokens"] if usage is not None else 0,
        output_tokens=usage["output_tokens"] if usage is not None else 0,
        tool_calls=tuple(
            ToolCall(id=call["id"] or "", name=call["name"], args=call["args"])
            for call in message.tool_calls
        ),
    )


def _model_name(message: AIMessage) -> str:
    """langchain 프로바이더들이 response_metadata["model_name"]에 실제 모델 이름을 넣는다."""
    name = message.response_metadata.get("model_name")
    return name if isinstance(name, str) else "unknown"


def message_from(event: LlmCalled) -> AIMessage:
    """기록된 모델 응답을 루프가 다시 읽을 수 있는 메시지로 되살린다. 재생의 안쪽이다.

    reply_from 의 반대 방향이고 같은 이유로 여기 있다. langchain 의 AIMessage 를 만드는 것은
    경계의 일이지 재생기의 일이 아니다(CODING_STANDARDS "서드파티는 경계에서 감싼다").
    """
    return AIMessage(
        content=event.text,
        tool_calls=[
            LangchainToolCall(name=call.name, args=dict(call.args), id=call.id)
            for call in event.tool_calls
        ],
        response_metadata={"model_name": event.model},
        usage_metadata=UsageMetadata(
            input_tokens=event.input_tokens,
            output_tokens=event.output_tokens,
            total_tokens=event.input_tokens + event.output_tokens,
        ),
    )
