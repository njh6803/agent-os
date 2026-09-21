"""ChatModel 포트가 돌려준 것이 경계에서 우리 타입으로 감싸이는지. 그리고 실제 호출 하나."""

import os
from collections.abc import Mapping, Sequence

import pytest
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from langchain_core.messages.tool import ToolCall as LangchainToolCall

from agent_os.adapters.anthropic import anthropic_chat_model, resolve_model_name
from agent_os.core.loop import run_loop
from agent_os.core.model import ModelReply, reply_from
from agent_os.core.ports import ChatModel, ToolConnection, ToolResult, ToolSpec
from agent_os.sdk import Json, ToolCall


class NoTools:
    def tools(self) -> Sequence[ToolSpec]:
        return []

    async def call(self, name: str, args: Mapping[str, Json]) -> ToolResult:
        raise LookupError(name)


def _ignore_tool_call(name: str, args: Mapping[str, Json], result: ToolResult) -> None:
    return None


def test_모델_응답은_이름_텍스트_토큰_수를_우리_타입으로_바꾼다() -> None:
    message = AIMessage(
        content="4",
        response_metadata={"model_name": "m"},
        usage_metadata={"input_tokens": 7, "output_tokens": 1, "total_tokens": 8},
    )

    assert reply_from(message) == ModelReply(
        model="m", text="4", input_tokens=7, output_tokens=1, tool_calls=()
    )


def test_토큰과_이름_정보가_없는_응답은_0과_unknown으로_센다() -> None:
    assert reply_from(AIMessage(content="ok")) == ModelReply(
        model="unknown", text="ok", input_tokens=0, output_tokens=0, tool_calls=()
    )


def test_모델이_요청한_도구_호출도_우리_타입으로_바뀐다() -> None:
    message = AIMessage(
        content="",
        tool_calls=[LangchainToolCall(name="add", args={"a": 2, "b": 2}, id="c1")],
    )

    assert reply_from(message).tool_calls == (ToolCall(id="c1", name="add", args={"a": 2, "b": 2}),)


async def test_도구_없는_루프는_한_바퀴로_끝나고_마지막_텍스트를_돌려준다() -> None:
    model: ChatModel = GenericFakeChatModel(messages=iter([AIMessage(content="4")]))
    tools: ToolConnection = NoTools()
    calls: list[ModelReply] = []

    text = await run_loop(
        model, "2+2?", tools=tools, on_model_call=calls.append, on_tool_call=_ignore_tool_call
    )

    assert text == "4"
    assert len(calls) == 1


@pytest.mark.llm
async def test_Anthropic_모델이_실제로_답한다() -> None:
    """원칙 I의 판정. 키가 없으면 skip이 아니라 실패한다."""
    assert "ANTHROPIC_API_KEY" in os.environ, "ANTHROPIC_API_KEY 가 없다. .env 를 확인한다"
    name = resolve_model_name(os.environ)
    model = anthropic_chat_model(name)
    tools: ToolConnection = NoTools()
    calls: list[ModelReply] = []

    text = await run_loop(
        model,
        "숫자 하나만 답한다. 2 더하기 2는?",
        tools=tools,
        on_model_call=calls.append,
        on_tool_call=_ignore_tool_call,
    )

    assert "4" in text
    assert calls[0].model == name
    assert calls[0].input_tokens > 0
    assert calls[0].output_tokens > 0
