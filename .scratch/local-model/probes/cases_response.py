"""도구 호출 인자가 깨진 응답(질문 5)과 응답 해석(질문 9)의 사례.

표지는 둘이다. 가짜 모델 서버가 그 응답을 한 번 내줬고(요청이 정확히 1건이다. 재시도가 든 전송
실패가 아니다), 결과가 그 응답을 읽다 난 것이다(메시지가 돌아왔거나, 예외가 전송·상태 오류가
아니다). 돌아온 `AIMessage`의 칸과, core 가 그것을 읽는 `reply_from`의 결과가 결과다.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from functools import partial

import openai
from fake_server import FakeServer, Reply, completion, tool_call
from support import Case, Outcome, Report, call, chat, describe, message_view, qualified

GOOD = '{"a": 2, "b": 3}'
BROKEN = '{"a": 2, "b":'
THOUGHT = "생각-표지-9931"
USAGE = {"prompt_tokens": 11, "completion_tokens": 7, "total_tokens": 18}
USAGE_DETAILS = {
    **USAGE,
    "prompt_tokens_details": {"cached_tokens": 4},
    "completion_tokens_details": {"reasoning_tokens": 3},
}


def _raw_call(arguments: object, *, with_id: bool = True) -> dict[str, object]:
    """`arguments`가 글자가 아니거나 `id`가 없는 도구 호출. 모델 서버가 낼 수 있는 변형이다."""
    raw: dict[str, object] = {
        "type": "function",
        "function": {"name": "add", "arguments": arguments},
    }
    if with_id:
        raw["id"] = "call_1"
    return raw


def _read_the_reply(outcome: Outcome) -> bool:
    """결과가 그 응답을 읽다 난 것인지. 메시지가 돌아왔거나, 예외가 전송·상태 오류가 아니다.

    전송이나 상태의 실패(`openai.APIConnectionError`, `openai.APIStatusError`)는 서버가 내준 응답을
    읽은 결과가 아니라, 그런 회차는 측정으로 세지 않는다. `openai.OpenAIError` 전체를 빼지 않는다.
    그 계열 가운데 응답 본문을 읽다 나는 예외는 재려는 상황이다. 어떤 예외였는지는 결과 갈래가 종류
    이름으로 적는다.
    """
    transport_or_status = (openai.APIConnectionError, openai.APIStatusError)
    return outcome.message is not None or not isinstance(outcome.error, transport_or_status)


async def _tool_case(calls: Sequence[Mapping[str, object]]) -> Report:
    reply = completion(content=None, tool_calls=calls, finish_reason="tool_calls")
    with FakeServer(lambda _request: reply) as server:
        outcome = await call(chat(server.base_url))
    message = outcome.message
    if message is not None:
        valid, invalid = len(message.tool_calls), len(message.invalid_tool_calls)
        result = f"tool_calls {valid} invalid_tool_calls {invalid}"
    else:
        result = f"예외 {qualified(type(outcome.error))}"
    return Report(
        measured=len(server.requests) == 1 and _read_the_reply(outcome),
        result=result,
        data={
            "served": list(calls),
            "message": message_view(message),
            "error": describe(outcome.error),
            "requests": len(server.requests),
        },
    )


async def _served(reply: Reply) -> tuple[Outcome, int]:
    with FakeServer(lambda _request: reply) as server:
        outcome = await call(chat(server.base_url), tools=False)
    return outcome, len(server.requests)


async def _usage_case(reply: Reply) -> Report:
    """`usage`와 `model`이 메시지의 어느 칸으로 가는지."""
    outcome, requests = await _served(reply)
    view = message_view(outcome.message) or {}
    metadata = view.get("response_metadata")
    name = metadata.get("model_name", "(없음)") if isinstance(metadata, dict) else None
    return Report(
        measured=requests == 1 and outcome.message is not None,
        result=f"model_name={name} usage_metadata={view.get('usage_metadata')}",
        data={"message": view, "error": describe(outcome.error)},
    )


async def response_reasoning_content() -> Report:
    """서버가 사고 글을 `reasoning_content`와 `reasoning`에 따로 줄 때 `text`에 섞이는지."""
    extra = {"reasoning_content": THOUGHT, "reasoning": THOUGHT}
    outcome, requests = await _served(completion(message_extra=extra, usage=USAGE))
    view = message_view(outcome.message) or {}
    found = sorted(
        name
        for name, value in view.items()
        if THOUGHT in json.dumps(value, ensure_ascii=False, default=repr)
    )
    text = view.get("text")
    return Report(
        measured=requests == 1 and isinstance(text, str) and "pong" in text,
        result=f"text={text!r} 사고 글이 든 칸: {' '.join(found) or '없음'}",
        data={"message": view, "thought_in": found, "error": describe(outcome.error)},
    )


CASES: dict[str, Case] = {
    "tool_args_valid": partial(_tool_case, [tool_call("add", GOOD)]),
    "tool_args_broken": partial(_tool_case, [tool_call("add", BROKEN)]),
    "tool_args_mixed": partial(
        _tool_case, [tool_call("add", GOOD, "call_ok"), tool_call("add", BROKEN, "call_bad")]
    ),
    "tool_args_broken_empty_name": partial(_tool_case, [tool_call("", BROKEN)]),
    "tool_args_valid_empty_name": partial(_tool_case, [tool_call("", GOOD)]),
    "tool_args_empty_string": partial(_tool_case, [tool_call("add", "")]),
    "tool_args_not_object": partial(_tool_case, [tool_call("add", "[1, 2]")]),
    "tool_args_object_value": partial(_tool_case, [_raw_call({"a": 2, "b": 3})]),
    "tool_args_null": partial(_tool_case, [_raw_call(None)]),
    "tool_call_missing_id": partial(_tool_case, [_raw_call(GOOD, with_id=False)]),
    "response_usage_and_model": partial(_usage_case, completion(usage=USAGE)),
    "response_without_usage_and_model": partial(_usage_case, completion(model=None)),
    "response_usage_details": partial(_usage_case, completion(usage=USAGE_DETAILS)),
    "response_reasoning_content": response_reasoning_content,
}
