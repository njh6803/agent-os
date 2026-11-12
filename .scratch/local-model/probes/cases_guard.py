"""어댑터가 모델 객체 안에 설 수 있는지(질문 7)의 사례.

core 는 어댑터가 만든 모델에 `bind_tools`와 `ainvoke`를 바로 부른다(`core/loop.py`). 그래서 사례는
그 길(`support.call`)로 부르고 세 가지를 본다. (가) 키 변수가 없으면 변수 이름만 든 예외로
끝나는가, (나) 서버가 되울린 키가 예외에서 가려지는가, (다) `openai`의 예외 형식이 올라오지 않는가.

모델 셋을 견준다.
- 손대지 않은 `ChatOpenAI`(대조군). 고치지 않으면 키가 든 `openai` 계열 예외가 올라온다.
- `FirstPlan`. 첫째 안을 글자 그대로 옮겼다. `_agenerate`에서 `openai.OpenAIError`만 받아 `except`
  안에서 `from None`으로 내장 예외를 던진다.
- 후보(`adapter_candidate.py`). 모든 예외를 받아 `except` 밖에서 던지고, 키를 호출 전에 본다.

표지: 재정의한 메서드를 지났다는 것은 그 메서드가 남긴 기록(`PASSES`)으로, 키가 되울려졌다는 것은
서버가 그 키가 든 요청을 받았다는 것으로 본다. 후보에는 기록이 없어, 지나는 길은 후보를 상속해
기록만 더한 `Counted`로 따로 본다.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import AsyncIterator
from functools import partial
from typing import override

import anyio
import openai
from adapter_candidate import GuardedChatOpenAI, KeySource, build_chat_model
from cases_key import BAD_KEYS
from fake_server import (
    FakeServer,
    Received,
    Reply,
    Responder,
    closed_port,
    completion,
    tool_call,
)
from langchain_core.callbacks import AsyncCallbackManagerForLLMRun, CallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.outputs import ChatGenerationChunk, ChatResult
from langchain_openai import ChatOpenAI
from support import (
    KEY,
    KEY_VARIABLE,
    MODEL_ID,
    PROMPT,
    SPECS,
    USER_BASIC,
    USER_PASSWORD,
    Case,
    CountingKey,
    Outcome,
    Report,
    attempt,
    authorizations,
    bodies,
    call,
    candidate,
    chat,
    describe,
    echo,
    leaked,
    links,
    message_view,
    ok_error_body,
    ok_not_json,
    ok_null_choices,
    passes_read_stage,
    qualified,
    said,
    with_userinfo,
)

PASSES: list[str] = []
TOOLS = [
    {"name": spec.name, "description": spec.description, "input_schema": dict(spec.input_schema)}
    for spec in SPECS
]
SENT = f"Bearer {KEY}"
# 이상한 주소에 심는 글자. 예외 글에 이것이 있으면 주소의 그 부분이 글에 실린 것이다.
ODD_MARK = "odd-part-3c7e"
# 유니코드 줄 구분 문자. 찍히지 않는 글자인데 ASCII 제어 문자가 아니라 라이브러리가 주소로 받는다.
LINE_SEPARATOR = chr(0x2028)
# 꼴이 이상한 주소들. 포트 8000 에는 아무도 붙지 않는다(만들기는 네트워크에 닿지 않는다).
ODD_ADDRESSES: dict[str, str] = {
    "plain": "http://127.0.0.1:8000/v1",
    "newline": f"http://127.0.0.1:8000/v1\n{ODD_MARK}",
    "tab": f"http://127.0.0.1:8000/v1\t{ODD_MARK}",
    "space_in_path": f"http://127.0.0.1:8000/v1/{ODD_MARK} x",
    "port_too_big": "http://127.0.0.1:99999/v1",
    "port_not_number": f"http://127.0.0.1:{ODD_MARK}/v1",
    "unicode_host": "http://모델서버.test/v1",
    "empty_label_host": "http://a..b/v1",
    "long_path": "http://127.0.0.1:8000/v1/" + "a" * 70000,
    "userinfo": "http://probe-user:probe-pass@127.0.0.1:8000/v1",
    "unclosed_bracket": "http://[::1/v1",
}


class FirstPlan(ChatOpenAI):
    """첫째 안 그대로. `openai.OpenAIError`만 받아 `except` 안에서 `from None`으로 던진다."""

    @override
    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: AsyncCallbackManagerForLLMRun | None = None,
        **kwargs: object,
    ) -> ChatResult:
        PASSES.append("_agenerate")
        try:
            return await super()._agenerate(messages, stop, run_manager, **kwargs)
        except openai.OpenAIError as error:
            raise RuntimeError(str(error).replace(KEY, "***")) from None


class Counted(GuardedChatOpenAI):
    """후보에 지나간 메서드의 기록만 더했다."""

    @override
    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: object,
    ) -> ChatResult:
        PASSES.append("_generate")
        return super()._generate(messages, stop, run_manager, **kwargs)

    @override
    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: AsyncCallbackManagerForLLMRun | None = None,
        **kwargs: object,
    ) -> ChatResult:
        PASSES.append("_agenerate")
        return await super()._agenerate(messages, stop, run_manager, **kwargs)

    @override
    async def _astream(self, *args: object, **kwargs: object) -> AsyncIterator[ChatGenerationChunk]:
        PASSES.append("_astream")
        async for chunk in super()._astream(*args, **kwargs):
            yield chunk


def _counted(base_url: str, *, streaming_off: bool) -> Counted:
    return Counted(
        model=MODEL_ID,
        base_url=base_url,
        api_key=KeySource(KEY_VARIABLE, {KEY_VARIABLE: KEY}),
        use_responses_api=False,
        disable_streaming=streaming_off,
    )


def _label(outcome: Outcome) -> str:
    error = outcome.error
    if error is None:
        return "예외 없음"
    chained = "원인 사슬 있음" if len(links(error)) > 1 else "원인 사슬 없음"
    return f"{qualified(type(error))} 키 {leaked(error, KEY)} {chained}"


def _view(server: FakeServer | None, outcome: Outcome) -> dict[str, object]:
    error = outcome.error
    foreign = [] if error is None else [qualified(type(found)) for _, found in links(error)]
    return {
        "error": describe(error, key=KEY),
        "non_builtin_types": sorted({name for name in foreign if not name.startswith("builtins.")}),
        "requests": 0 if server is None else len(server.requests),
        "authorization": [] if server is None else authorizations(server),
        "passes": list(PASSES),
        "seconds": outcome.seconds,
    }


def _report(server: FakeServer, outcome: Outcome, *, marked: bool = True) -> Report:
    """키가 든 요청이 서버에 닿았고 예외가 올라왔으면 측정이다. `marked`는 사례가 더 보는 표지다."""
    echoed = SENT in authorizations(server) and outcome.error is not None
    return Report(measured=echoed and marked, result=_label(outcome), data=_view(server, outcome))


async def guard_control_plain() -> Report:
    PASSES.clear()
    with FakeServer(echo(401)) as server:
        outcome = await call(chat(server.base_url, api_key=CountingKey(value=KEY)))
    return _report(server, outcome)


async def _first_plan(responder: Responder) -> Report:
    PASSES.clear()
    with FakeServer(responder) as server:
        model = FirstPlan(
            model=MODEL_ID, base_url=server.base_url, api_key=KEY, use_responses_api=False
        )
        outcome = await call(model)
    return _report(server, outcome, marked="_agenerate" in PASSES)


async def _candidate(responder: Responder) -> Report:
    PASSES.clear()
    with FakeServer(responder) as server:
        outcome = await call(candidate(server.base_url))
    return _report(server, outcome)


async def guard_candidate_closed_port() -> Report:
    PASSES.clear()
    outcome = await call(candidate(f"http://127.0.0.1:{closed_port()}/v1"))
    text = "" if outcome.error is None else str(outcome.error)
    return Report(
        measured="Connection error" in text,
        result=_label(outcome),
        data=_view(None, outcome),
    )


async def guard_candidate_userinfo_401() -> Report:
    """주소에 사용자 정보가 있을 때 후보의 예외 글에 암호가 실리는지.

    암호 글자 그대로와, 서버가 되울린 Basic 인증 값(`user:암호`의 base64)을 따로 찾는다. 후보가
    가리는 것은 환경의 키 값뿐이라 뒤의 것은 가리지 못한다.
    """
    PASSES.clear()
    with FakeServer(echo(401)) as server:
        outcome = await call(candidate(with_userinfo(server.base_url)))
    error = outcome.error
    kind = "예외 없음" if error is None else qualified(type(error))
    return Report(
        measured=len(server.requests) >= 1 and error is not None,
        result=f"{kind} 암호 {leaked(error, USER_PASSWORD)}, base64 꼴 {leaked(error, USER_BASIC)}",
        data={
            **_view(server, outcome),
            "error": describe(error, key=KEY, password=USER_PASSWORD, basic=USER_BASIC),
        },
    )


def _build_error(address: str) -> Exception | None:
    """후보로 모델을 만들다 난 예외. 만들어지면 없음이다. 네트워크에 닿지 않는다."""
    try:
        candidate(address)
    except Exception as error:  # 만들다 난 예외가 사례의 결과다
        return error
    return None


async def build_rejects_address() -> Report:
    """읽는 단계의 주소 검사를 지난 주소 가운데 모델을 만들다 실패하는 것이 있는지.

    명세는 "모델 만들기는 키도 네트워크도 요구하지 않고, 실패하는 것은 모델 소스가 거부하는 모양의
    매니페스트뿐"이라는 포트의 전제에 기댄다. 그런데 주소는 sdk 의 검사(`urlsplit` 기반의 규칙
    넷)만 지나면 라이브러리로 간다. 꼴이 이상한 주소 여럿을 그 검사와 후보의 만들기에 차례로 넣는다.

    표지는 셋이다. 보통 주소(`plain`)가 검사를 지나고 만들어진다(만들기가 도는 양성 대조), 사용자
    정보가 든 주소가 검사에서 거부된다(검사가 실제로 돈 음성 대조), 닫지 않은 대괄호 주소도 검사에서
    거부된다. 결과는 검사를 지났는데 만들다 실패한 주소의 이름과 예외의 종류다.
    """
    PASSES.clear()
    rows: dict[str, dict[str, object]] = {}
    slipped: list[str] = []
    for name, address in ODD_ADDRESSES.items():
        accepted = passes_read_stage(address)
        error = _build_error(address) if accepted else None
        rows[name] = {
            "read_stage": accepted,
            "build": describe(error),
            "text_has_address_part": error is not None and ODD_MARK in str(error),
        }
        if error is not None:
            slipped.append(f"{name}({qualified(type(error))})")
    measured = (
        rows["plain"]["read_stage"] is True
        and rows["plain"]["build"] is None
        and rows["userinfo"]["read_stage"] is False
        and rows["unclosed_bracket"]["read_stage"] is False
    )
    result = "검사를 지나고 만들다 실패: " + (", ".join(slipped) or "없음")
    return Report(measured=measured, result=result, data={"addresses": rows})


async def guard_candidate_odd_url_401() -> Report:
    """검사도 만들기도 지나는 이상한 주소로 401 을 받았을 때 후보의 예외 글에 주소가 실리는 꼴.

    후보는 주소를 글자 그대로 싣되 찍히지 않는 글자를 이스케이프한다(`adapter_candidate.py`의
    `_address`). 주소는 경로에 공백, 한글, 유니코드 줄 구분 문자(U+2028)가 든 것이다. ASCII 제어
    문자는 넣지 못한다. 그런 주소는 모델을 만들다 거부된다(`build_rejects_address`). 표지는 서버가
    요청을 받았고 예외 글에 그 경로의 표지 글자가 있는 것이다(주소가 글에 실렸다). 결과는 그 글에
    줄 구분 문자가 날것으로 있는지, 이스케이프한 꼴로 있는지와 서버가 받은 요청 줄이다.
    """
    PASSES.clear()
    with FakeServer(echo(401)) as server:
        outcome = await call(candidate(f"{server.base_url}/{ODD_MARK} 한{LINE_SEPARATOR}글"))
        targets = [request.target for request in server.requests]
    text = "" if outcome.error is None else str(outcome.error)
    kind = "예외 없음" if outcome.error is None else qualified(type(outcome.error))
    raw = "날것 있음" if LINE_SEPARATOR in text else "날것 없음"
    escaped = "이스케이프 있음" if "\\u2028" in text else "이스케이프 없음"
    return Report(
        measured=bool(targets) and ODD_MARK in text,
        result=f"{kind} 줄 구분 문자 {raw}, {escaped} 요청 줄 {' | '.join(targets)}",
        data={"text": text, "targets": targets, "error": describe(outcome.error, key=KEY)},
    )


async def guard_candidate_missing_key() -> Report:
    """(가) 환경에 키 변수가 없다. 모델은 만들어지고, 부를 때 변수 이름만 든 예외로 끝난다."""
    PASSES.clear()
    with FakeServer() as server:
        outcome = await call(candidate(server.base_url, key=None))
    text = "" if outcome.error is None else str(outcome.error)
    return Report(
        measured=f"{KEY_VARIABLE} 가 없다" in text,
        result=f"{_label(outcome)} 요청 {len(server.requests)}건",
        data=_view(server, outcome),
    )


async def _candidate_bad_key(kind: str) -> Report:
    """헤더에 실을 수 없는 키 값이 환경에 있다. 후보는 호출 전에 값 없이 끝낸다.

    표지는 예외의 글이 그 변수의 이름과 "보낼 수 없는 글자"를 함께 든다는 것이다. 변수 이름만 보면
    값이 환경에 닿지 않아 "변수가 없다"로 끝난 회차도 같은 표지가 된다.
    """
    PASSES.clear()
    value, needle = BAD_KEYS[kind]
    with FakeServer() as server:
        outcome = await call(candidate(server.base_url, key=value))
    text = "" if outcome.error is None else str(outcome.error)
    kind_of = "예외 없음" if outcome.error is None else qualified(type(outcome.error))
    return Report(
        measured=KEY_VARIABLE in text and "보낼 수 없는 글자" in text,
        result=f"{kind_of} 키 {leaked(outcome.error, needle)} 요청 {len(server.requests)}건",
        data={
            "key": repr(value),
            **_view(server, outcome),
            "error": describe(outcome.error, key=needle),
        },
    )


async def guard_candidate_key_rotation() -> Report:
    """모델을 만든 뒤 환경의 키를 바꾸고, 그다음 지운다. 호출 때 읽는지를 본다."""
    PASSES.clear()
    env = {KEY_VARIABLE: "probe-key-before-1111"}
    with FakeServer() as server:
        model = build_chat_model(
            model_id=MODEL_ID,
            base_url=server.base_url,
            api_key_env=KEY_VARIABLE,
            max_tokens=None,
            temperature=None,
            env=env,
        )
        await call(model, tools=False)
        env[KEY_VARIABLE] = "probe-key-after-2222"
        await call(model, tools=False)
        del env[KEY_VARIABLE]
        removed = await call(model, tools=False)
    sent = authorizations(server)
    fresh = sent[:2] == ["Bearer probe-key-before-1111", "Bearer probe-key-after-2222"]
    return Report(
        measured=len(sent) >= 2,
        result=("호출 때 읽었다" if fresh else "호출 때 읽지 않았다") + f", 요청 {len(sent)}건",
        data={"authorization": sent, "after_removed": describe(removed.error)},
    )


async def guard_candidate_no_key_variable() -> Report:
    """키 변수를 적지 않은 모델 파일. 자리 채움 글자가 인증 헤더로 간다."""
    PASSES.clear()
    with FakeServer() as server:
        outcome = await call(candidate(server.base_url, variable=None), tools=False)
    sent = authorizations(server)
    return Report(
        measured=said(outcome) == "pong" and len(sent) == 1,
        result=" | ".join(sent),
        data={"authorization": sent},
    )


async def guard_candidate_success() -> Report:
    """후보로 도구를 붙여 성공하는 호출 둘. 선택 칸을 주지 않을 때와 줄 때의 본문을 본다."""
    PASSES.clear()
    reply = completion(content=None, tool_calls=[tool_call("add", '{"a": 2, "b": 3}')])
    with FakeServer(lambda _request: reply) as server:
        bare = await call(candidate(server.base_url))
        await call(candidate(server.base_url, max_tokens=256, temperature=0.2))
    seen = bodies(server)
    first = seen[0] if seen else {}
    second = seen[1] if len(seen) > 1 else {}
    optional = ("max_tokens", "max_completion_tokens", "temperature")
    calls = [] if bare.message is None else bare.message.tool_calls
    return Report(
        measured=len(seen) == 2 and len(calls) == 1 and "tools" in first,
        result=(
            f"주지 않으면 {[name for name in optional if name in first] or '없음'}, "
            f"주면 {[name for name in optional if name in second]}"
        ),
        data={"bodies": seen, "message": message_view(bare.message)},
    )


async def _drain(model: BaseChatModel) -> AIMessage:
    """`bind_tools` 뒤 `astream`으로 끝까지 읽는다. 루프가 쓰지 않는 길이다."""
    last: AIMessage = AIMessage("")
    async for chunk in model.bind_tools(TOOLS).astream([HumanMessage(PROMPT)]):
        last = chunk
    return last


async def _sync(model: BaseChatModel) -> AIMessage:
    """`bind_tools` 뒤 동기 `invoke`를 스레드에서 부른다. 루프가 쓰지 않는 길이다."""
    return await asyncio.to_thread(model.bind_tools(TOOLS).invoke, [HumanMessage(PROMPT)])


async def guard_paths() -> Report:
    """호출 길마다 후보의 어느 메서드를 지나는지(`Counted`의 기록)."""
    passes: dict[str, list[str]] = {}
    with FakeServer() as server:
        model = _counted(server.base_url, streaming_off=True)
        PASSES.clear()
        await call(model)
        passes["bind_tools.ainvoke"] = list(PASSES)
        PASSES.clear()
        await attempt(lambda: _drain(model))
        passes["bind_tools.astream"] = list(PASSES)
        PASSES.clear()
        await attempt(lambda: _sync(model))
        passes["bind_tools.invoke"] = list(PASSES)
    return Report(
        measured=len(server.requests) == 3,
        result=" ".join(f"{name}→{'+'.join(found) or '없음'}" for name, found in passes.items()),
        data={"passes": passes, "stream_flags": [body.get("stream") for body in bodies(server)]},
    )


async def guard_stream_bypass_control() -> Report:
    """대조군. 스트리밍을 끄지 않으면 `astream`은 `_astream`으로 가서 감싼 메서드를 비켜 간다."""
    PASSES.clear()
    with FakeServer(echo(401)) as server:
        model = _counted(server.base_url, streaming_off=False)
        outcome = await attempt(lambda: _drain(model))
    return _report(server, outcome, marked=PASSES == ["_astream"])


async def _candidate_other_path(path: str) -> Report:
    PASSES.clear()
    with FakeServer(echo(401)) as server:
        model = candidate(server.base_url)
        invoke = _drain if path == "astream" else _sync
        outcome = await attempt(lambda: invoke(model))
    return _report(server, outcome)


ARGS_MARK = "args-secret-6e1f"
# JSON 이지만 객체가 아닌 인자, 그리고 글이 아니라 객체로 온 인자. 둘 다 라이브러리가 pydantic 의
# 검증 예외로 끝내고, 그 글의 `input_value`에 인자가 실린다(`cases_response.py`의
# `tool_args_not_object`, `tool_args_object_value`).
_ARGS_SHAPES: dict[str, object] = {
    "not_object": f'["{ARGS_MARK}", 2]',
    "object_value": {"a": ARGS_MARK, "b": 2},
}


async def _args_shape(shape: str) -> Report:
    """인자의 꼴이 틀린 도구 호출을 손대지 않은 모델과 후보에 같이 보낸다.

    표지는 두 서버가 요청을 받았고, 대조(손대지 않은 모델)의 예외 글에 인자의 글자가 실린 것이다.
    찾을 것이 있으면 찾는다는 양성 대조다. 결과는 후보의 예외에서 그 글자가 어디에 있는지다.
    """
    PASSES.clear()
    function = {"name": "add", "arguments": _ARGS_SHAPES[shape]}
    calls = [{"id": "call_1", "type": "function", "function": function}]
    reply = completion(content=None, tool_calls=calls, finish_reason="tool_calls")
    with FakeServer(lambda _request: reply) as plain_server:
        plain = await call(chat(plain_server.base_url))
    with FakeServer(lambda _request: reply) as server:
        guarded = await call(candidate(server.base_url))
    control = leaked(plain.error, ARGS_MARK)
    kind = "예외 없음" if guarded.error is None else qualified(type(guarded.error))
    return Report(
        measured=bool(plain_server.requests) and bool(server.requests) and control == "글에 있음",
        result=f"{kind} 인자 {leaked(guarded.error, ARGS_MARK)}",
        data={
            "control": describe(plain.error, args=ARGS_MARK),
            "error": describe(guarded.error, args=ARGS_MARK),
        },
    )


def _slow(_request: Received) -> Reply:
    time.sleep(1.5)
    return completion()


async def guard_candidate_cancelled() -> Report:
    """실행 타임아웃처럼 `move_on_after`로 감싼다. 후보가 취소를 삼키지 않는지 본다.

    표지는 요청이 서버에 닿았고 기한이 실제로 호출을 끊으려 했다(`cancel_called`)는 것이다. 기한
    전에 다른 까닭으로 끝난 호출은 취소를 재지 않은 회차다.
    """
    PASSES.clear()
    outcome: Outcome | None = None
    with FakeServer(_slow) as server:
        model = candidate(server.base_url)
        with anyio.move_on_after(0.5) as scope:
            outcome = await call(model, tools=False)
        reached = len(server.requests)
    passed = scope.cancelled_caught and outcome is None
    return Report(
        measured=reached >= 1 and scope.cancel_called,
        result="취소가 그대로 올라왔다" if passed else "취소가 그대로 올라오지 않았다",
        data={
            "cancelled_caught": scope.cancelled_caught,
            "returned": outcome is not None,
            "error": None if outcome is None else describe(outcome.error),
        },
    )


CASES: dict[str, Case] = {
    "guard_control_plain": guard_control_plain,
    "guard_first_plan_401": partial(_first_plan, echo(401)),
    "guard_first_plan_ok_error_body": partial(_first_plan, ok_error_body),
    "guard_candidate_401": partial(_candidate, echo(401)),
    "guard_candidate_500": partial(_candidate, echo(500)),
    "guard_candidate_ok_error_body": partial(_candidate, ok_error_body),
    "guard_candidate_not_json": partial(_candidate, ok_not_json),
    "guard_candidate_null_choices": partial(_candidate, ok_null_choices),
    "guard_candidate_args_not_object": partial(_args_shape, "not_object"),
    "guard_candidate_args_object_value": partial(_args_shape, "object_value"),
    "guard_candidate_closed_port": guard_candidate_closed_port,
    "guard_candidate_userinfo_401": guard_candidate_userinfo_401,
    "build_rejects_address": build_rejects_address,
    "guard_candidate_odd_url_401": guard_candidate_odd_url_401,
    "guard_candidate_missing_key": guard_candidate_missing_key,
    "guard_candidate_bad_key_newline": partial(_candidate_bad_key, "newline"),
    "guard_candidate_bad_key_unicode": partial(_candidate_bad_key, "unicode"),
    "guard_candidate_bad_key_trailing_space": partial(_candidate_bad_key, "trailing_space"),
    "guard_candidate_key_rotation": guard_candidate_key_rotation,
    "guard_candidate_no_key_variable": guard_candidate_no_key_variable,
    "guard_candidate_success": guard_candidate_success,
    "guard_paths": guard_paths,
    "guard_stream_bypass_control": guard_stream_bypass_control,
    "guard_candidate_astream_401": partial(_candidate_other_path, "astream"),
    "guard_candidate_invoke_401": partial(_candidate_other_path, "invoke"),
    "guard_candidate_cancelled": guard_candidate_cancelled,
}
