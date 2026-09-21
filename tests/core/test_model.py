"""ChatModel 포트를 통한 호출 한 번. 프로바이더 타입이 경계에서 우리 타입으로 감싸이는지."""

import os

import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage

from agent_os.adapters.anthropic import anthropic_chat_model, resolve_model_name
from agent_os.core.model import ModelReply, call_model
from agent_os.core.ports import ChatModel


async def test_모델_호출은_텍스트와_토큰_수를_우리_타입으로_돌려준다() -> None:
    reply = AIMessage(
        content="4",
        usage_metadata={"input_tokens": 7, "output_tokens": 1, "total_tokens": 8},
    )
    model: ChatModel = GenericFakeChatModel(messages=iter([reply]))

    got = await call_model(model, "2+2?")

    assert got == ModelReply(text="4", input_tokens=7, output_tokens=1)


async def test_토큰_정보가_없는_모델_응답은_0으로_센다() -> None:
    model: ChatModel = GenericFakeChatModel(messages=iter([AIMessage(content="ok")]))

    got = await call_model(model, "hi")

    assert got == ModelReply(text="ok", input_tokens=0, output_tokens=0)


@pytest.mark.llm
async def test_Anthropic_모델이_실제로_답한다() -> None:
    """원칙 I의 판정. 키가 없으면 skip이 아니라 실패한다."""
    assert "ANTHROPIC_API_KEY" in os.environ, "ANTHROPIC_API_KEY 가 없다. .env 를 확인한다"
    model = anthropic_chat_model(resolve_model_name(os.environ))

    got = await call_model(model, "숫자 하나만 답한다. 2 더하기 2는?")

    assert "4" in got.text
    assert got.input_tokens > 0
    assert got.output_tokens > 0
