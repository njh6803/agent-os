"""키를 함수로 넘길 때(질문 3)와 헤더에 실을 수 없는 키(질문 4)의 사례.

표지: 함수 사례는 함수가 실제로 불렸다(부른 횟수). 글자 사례는 모델이 쥔 키가 넣은 값 그대로다. 둘
다 라이브러리가 그 키를 받았다는 뜻이고, 그 뒤에 난 예외나 서버에 닿은 값이 결과다.
"""

from __future__ import annotations

import threading
from functools import partial

from fake_server import FakeServer
from pydantic import SecretStr
from support import (
    KEY_VARIABLE,
    Case,
    CountingKey,
    Report,
    authorizations,
    call,
    chat,
    describe,
    leaked,
    qualified,
)

# 종류 → (키 값, 글에서 찾을 글자)
BAD_KEYS = {
    "newline": ("nl-key-4f7a91c2\n", "nl-key-4f7a91c2"),
    "unicode": ("uni-키-8d2e55b0", "8d2e55b0"),
    "trailing_space": ("sp-key-77aa01 ", "sp-key-77aa01"),
}


async def key_function_per_request() -> Report:
    """함수는 만들 때 불리지 않고 요청마다 불린다. 함수는 부를 때마다 다른 값을 낸다."""
    key = CountingKey()
    with FakeServer() as server:
        model = chat(server.base_url, api_key=key)
        counts = [key.calls]
        for _ in range(2):
            await call(model, tools=False)
            counts.append(key.calls)
    sent = authorizations(server)
    return Report(
        measured=len(sent) == 2 and all(v.startswith("Bearer probe-key-call-") for v in sent),
        result=(
            f"만들 때 {counts[0]}회, 첫 호출 {counts[1] - counts[0]}회, "
            f"둘째 호출 {counts[2] - counts[1]}회"
        ),
        data={
            "calls": counts,
            "authorization": sent,
            "key_threads": sorted(set(key.threads)),
            "loop_thread": threading.current_thread().name,
        },
    )


async def key_function_raises() -> Report:
    """함수가 던진 예외가 `ainvoke`를 부른 쪽에 어떤 모양으로 닿는지."""
    raised = RuntimeError(f"변수 {KEY_VARIABLE} 가 없다")
    key = CountingKey(error=raised)
    with FakeServer() as server:
        model = chat(server.base_url, api_key=key)
        built = key.calls
        outcome = await call(model)
    error = outcome.error
    kind = "예외 없음" if error is None else qualified(type(error))
    return Report(
        measured=key.calls >= 1 and error is not None,
        result=f"{kind} 함수 {key.calls}회 요청 {len(server.requests)}건",
        data={
            "error": describe(error),
            "same_object": error is raised,
            "calls_when_built": built,
            "calls": key.calls,
            "requests": len(server.requests),
            "seconds": outcome.seconds,
        },
    )


async def _bad_key(kind: str, *, function: bool) -> Report:
    value, needle = BAD_KEYS[kind]
    key = CountingKey(value=value)
    with FakeServer() as server:
        model = chat(server.base_url, api_key=key if function else value)
        outcome = await call(model, tools=False)
    held = model.openai_api_key
    stored = isinstance(held, SecretStr) and held.get_secret_value() == value
    given = key.calls >= 1 if function else stored
    error = outcome.error
    sent = [repr(header) for header in authorizations(server)]
    return Report(
        measured=given and (error is not None or len(sent) >= 1),
        result=(
            f"예외 {qualified(type(error))} {leaked(error, needle)}"
            if error is not None
            else f"서버에 닿았다 {' '.join(sent)}"
        ),
        data={
            "key": repr(value),
            "error": describe(error, key=needle),
            "requests": len(sent),
            "authorization": sent,
            "calls": key.calls,
            "seconds": outcome.seconds,
        },
    )


CASES: dict[str, Case] = {
    "key_function_per_request": key_function_per_request,
    "key_function_raises": key_function_raises,
    "bad_key_newline_string": partial(_bad_key, "newline", function=False),
    "bad_key_newline_function": partial(_bad_key, "newline", function=True),
    "bad_key_unicode_string": partial(_bad_key, "unicode", function=False),
    "bad_key_unicode_function": partial(_bad_key, "unicode", function=True),
    "bad_key_trailing_space_string": partial(_bad_key, "trailing_space", function=False),
    "bad_key_trailing_space_function": partial(_bad_key, "trailing_space", function=True),
}
