"""ChatModel 포트가 돌려준 것을 우리 타입으로 바꾸는 경계.

langchain의 AIMessage는 루프 밖으로 나가지 않는다(CODING_STANDARDS "서드파티는 경계에서 감싼다").
"""

from __future__ import annotations

from dataclasses import dataclass

from langchain_core.messages import AIMessage


@dataclass(frozen=True)
class ModelReply:
    model: str
    text: str
    input_tokens: int
    output_tokens: int


def reply_from(message: AIMessage) -> ModelReply:
    usage = message.usage_metadata
    return ModelReply(
        model=_model_name(message),
        text=message.text,
        input_tokens=usage["input_tokens"] if usage is not None else 0,
        output_tokens=usage["output_tokens"] if usage is not None else 0,
    )


def _model_name(message: AIMessage) -> str:
    """langchain 프로바이더들이 response_metadata["model_name"]에 실제 모델 이름을 넣는다."""
    name = message.response_metadata.get("model_name")
    return name if isinstance(name, str) else "unknown"
