"""`openai_compat.py`의 사례 모듈들이 나눠 쓰는 것(측정이 아니다).

- 루프와 같은 길로 모델을 부른다. `core/loop.py`의 `model_caller`에 `ToolSpec`을 넘겨 `bind_tools`
  뒤 `ainvoke`를 지나게 하고, 돌아온 메시지를 `core/model.py`의 `reply_from`으로도 읽는다.
- 예외를 편다. 종류(모듈 경로까지), 글, `__cause__`와 `__context__`를 따라 닿는 예외 전부, 그리고
  찾는 글자(키, 주소)가 어느 자리에 실렸는지.
- 환경 변수를 잠깐 바꾸고, 루트 로거의 DEBUG 레코드를 모은다.
"""

from __future__ import annotations

import base64
import dataclasses
import json
import logging
import os
import sys
import threading
import time
import traceback
from collections.abc import Awaitable, Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import httpx2
from adapter_candidate import build_chat_model
from fake_server import FakeServer, Received, Reply, Responder
from fake_server import error as error_reply
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from pydantic import ValidationError

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / "src"))
from agent_os.core.loop import model_caller  # noqa: E402
from agent_os.core.model import reply_from  # noqa: E402
from agent_os.core.ports import ChatModel, ToolSpec  # noqa: E402
from agent_os.sdk import HttpServer, PluginName  # noqa: E402

KEY = "probe-key-0123456789"
KEY_VARIABLE = "PROBE_MODEL_KEY"
MODEL_ID = "requested-model-id"
PROMPT_MARK = "probe-prompt-5521"
PROMPT = f"{PROMPT_MARK} 2 와 3 을 더해 줘"
QUERY_SECRET = "query-secret-4b9d"
USER_PASSWORD = "probe-pass-77c3"
# 주소의 사용자 정보가 Basic 인증 헤더로 갈 때의 꼴(`user:암호`의 base64).
USER_BASIC = base64.b64encode(f"probe-user:{USER_PASSWORD}".encode()).decode()
CLIP = 700
SPECS = (
    ToolSpec(
        name="add",
        server=PluginName("calc"),
        description="두 정수를 더한다",
        input_schema={
            "type": "object",
            "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
            "required": ["a", "b"],
        },
    ),
)
# 프로브가 도는 동안 환경에서 지우는 변수. 라이브러리가 읽어 요청의 자리나 내용을 바꾸는 것들이다.
SCRUBBED_PREFIXES = ("OPENAI_", "LANGSMITH_", "LANGCHAIN_", "LC_OUTPUT_")
SCRUBBED_NAMES = ("HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "NO_PROXY")


@dataclass(frozen=True)
class Report:
    """사례 하나의 결과. `measured`는 재려는 상황이 났다는 표지, `result`는 결과의 갈래다."""

    measured: bool
    result: str
    data: Mapping[str, object]


type Case = Callable[[], Awaitable[Report]]


@dataclass(frozen=True)
class Outcome:
    message: AIMessage | None
    error: Exception | None
    seconds: float


def scrub_environment() -> list[str]:
    """요청을 바꿀 수 있는 환경 변수를 지우고 그 이름만 돌려준다. 값은 찍지 않는다."""
    names = sorted(
        name
        for name in os.environ
        if name.upper().startswith(SCRUBBED_PREFIXES) or name.upper() in SCRUBBED_NAMES
    )
    for name in names:
        del os.environ[name]
    return names


@contextmanager
def environment(**values: str | None) -> Iterator[None]:
    """환경 변수를 잠깐 바꾼다. 없음은 그 변수를 지운다."""
    before = {name: os.environ.get(name) for name in values}
    try:
        _apply(values)
        yield
    finally:
        _apply(before)


def _apply(values: Mapping[str, str | None]) -> None:
    for name, value in values.items():
        if value is None:
            os.environ.pop(name, None)
        else:
            os.environ[name] = value


def chat(base_url: str | None, **options: object) -> ChatOpenAI:
    """손대지 않은 `ChatOpenAI`. 사례가 준 인자만 넘긴다. `api_key`가 없음이면 넘기지 않는다."""
    settings: dict[str, object] = {"model": MODEL_ID, "api_key": KEY, **options}
    if base_url is not None:
        settings["base_url"] = base_url
    if settings["api_key"] is None:
        del settings["api_key"]
    return ChatOpenAI(**settings)


async def call(
    model: ChatModel, *, tools: bool = True, messages: Sequence[BaseMessage] | None = None
) -> Outcome:
    """루프와 같은 길로 한 번 부른다. 예외는 삼켜 `Outcome`에 싣는다."""
    invoke = model_caller(model, SPECS if tools else ())
    return await attempt(lambda: invoke(messages or [HumanMessage(PROMPT)]))


async def attempt(invoke: Callable[[], Awaitable[AIMessage]]) -> Outcome:
    started = time.monotonic()
    try:
        message = await invoke()
    except Exception as error:  # 예외가 사례의 결과다
        return Outcome(None, error, round(time.monotonic() - started, 3))
    return Outcome(message, None, round(time.monotonic() - started, 3))


def with_userinfo(base_url: str) -> str:
    """주소에 사용자 정보를 끼운다. `http://probe-user:<암호>@127.0.0.1:<포트>/v1` 꼴이다."""
    return base_url.replace("http://", f"http://probe-user:{USER_PASSWORD}@", 1)


def passes_read_stage(address: str) -> bool:
    """sdk 가 원격 MCP 서버의 `url`에 거는 검사(`HttpServer`의 규칙 넷)를 그 주소가 지나는지.

    명세는 모델 파일의 `base_url`에 같은 규칙 넷을 쓴다. 쿼리의 거부는 명세가 더하는 규칙이라 여기
    없다.
    """
    try:
        HttpServer(transport="http", url=address)
    except ValidationError:
        return False
    return True


def said(outcome: Outcome) -> str | None:
    return None if outcome.message is None else outcome.message.text


def candidate(
    base_url: str,
    *,
    key: str | None = KEY,
    variable: str | None = KEY_VARIABLE,
    max_tokens: int | None = None,
    temperature: float | None = None,
    http_async_client: httpx2.AsyncClient | None = None,
) -> BaseChatModel:
    """후보 어댑터가 만든 모델. `key`가 없음이면 환경에 그 변수가 없다."""
    return build_chat_model(
        model_id=MODEL_ID,
        base_url=base_url,
        api_key_env=variable,
        max_tokens=max_tokens,
        temperature=temperature,
        env={} if key is None else {KEY_VARIABLE: key},
        http_async_client=http_async_client,
    )


class CountingKey:
    """부른 횟수와 부른 스레드를 세는 키 함수. 값을 주지 않으면 부를 때마다 다른 값을 낸다."""

    def __init__(self, *, value: str | None = None, error: Exception | None = None) -> None:
        self.calls = 0
        self.threads: list[str] = []
        self._value = value
        self._error = error

    def __call__(self) -> str:
        self.calls += 1
        self.threads.append(threading.current_thread().name)
        if self._error is not None:
            raise self._error
        return self._value if self._value is not None else f"probe-key-call-{self.calls:04d}"


def _sent_key(request: Received) -> str:
    return " ".join(request.header("Authorization")).removeprefix("Bearer ")


def echo(status: int) -> Responder:
    """받은 키를 오류 글에 되울리는 응답. 상태 코드만 사례가 고른다."""

    def respond(request: Received) -> Reply:
        text = f"Incorrect API key provided: {_sent_key(request)}. 키를 확인하라."
        return error_reply(status, text)

    return respond


def ok_error_body(request: Received) -> Reply:
    """상태는 200 인데 본문이 `error` 칸뿐인 응답. 받은 키를 되울린다."""
    detail = {"message": f"upstream rejected key {_sent_key(request)}", "code": "invalid_api_key"}
    return Reply(200, json.dumps({"error": detail}).encode())


def ok_not_json(request: Received) -> Reply:
    """상태는 200 인데 본문이 JSON 이 아닌 응답. 받은 키를 되울린다."""
    body = f"upstream auth failed for {_sent_key(request)}".encode()
    return Reply(200, body, content_type="text/plain")


def ok_null_choices(request: Received) -> Reply:
    """상태는 200 인데 `choices`가 null 인 응답. 받은 키를 다른 칸에 되울린다."""
    payload = {"id": "chatcmpl-probe", "choices": None, "note": f"key {_sent_key(request)}"}
    return Reply(200, json.dumps(payload).encode())


def qualified(kind: type) -> str:
    return f"{kind.__module__}.{kind.__qualname__}"


def clip(text: str, limit: int = CLIP) -> str:
    return text if len(text) <= limit else f"{text[:limit]}…(+{len(text) - limit}자)"


def links(error: BaseException) -> list[tuple[str, BaseException]]:
    """예외에서 `__cause__`와 `__context__`와 묶음의 멤버를 따라 닿는 예외 전부. 처음이 자신이다."""
    found: list[tuple[str, BaseException]] = []
    seen: set[int] = set()
    pending: list[tuple[str, BaseException]] = [("self", error)]
    while pending:
        path, current = pending.pop(0)
        if id(current) in seen:
            continue
        seen.add(id(current))
        found.append((path, current))
        if current.__cause__ is not None:
            pending.append((f"{path}.cause", current.__cause__))
        if current.__context__ is not None:
            pending.append((f"{path}.context", current.__context__))
        if isinstance(current, BaseExceptionGroup):
            pending.extend((f"{path}[{i}]", member) for i, member in enumerate(current.exceptions))
    return found


def leaks(error: BaseException, needle: str) -> list[str]:
    """찾는 글자가 실린 자리. 글, repr, 예외가 쥔 요청 헤더와 응답 본문, 그리고 트레이스백 글."""
    places: list[str] = []
    for path, current in links(error):
        if needle in str(current):
            places.append(f"{path}.str")
        if needle in repr(current):
            places.append(f"{path}.repr")
        places.extend(f"{path}.{name}" for name in _held(current, needle))
    if needle in "".join(traceback.format_exception(error)):
        places.append("traceback")
    return places


def _held(error: BaseException, needle: str) -> list[str]:
    """openai 의 예외가 쥔 요청과 응답에 그 글자가 있는지. 없는 속성은 지나친다."""
    names: list[str] = []
    headers = getattr(getattr(error, "request", None), "headers", None)
    if headers is not None and any(needle in str(value) for value in headers.values()):
        names.append("request.headers")
    if needle in str(getattr(error, "body", "")):
        names.append("body")
    return names


def describe(error: BaseException | None, **needles: str) -> dict[str, object] | None:
    """예외 하나를 JSON 으로 찍을 모양으로. `needles`는 찾을 글자에 붙인 이름이다."""
    if error is None:
        return None
    chain = [
        {
            "at": path,
            "type": qualified(type(current)),
            "text": clip(str(current)),
            "suppress_context": current.__suppress_context__,
        }
        for path, current in links(error)
    ]
    skipped = (object, BaseException, Exception)
    return {
        "type": qualified(type(error)),
        "bases": [qualified(base) for base in type(error).__mro__[1:] if base not in skipped],
        "text": clip(str(error)),
        "status_code": getattr(error, "status_code", None),
        "chain": chain[1:],
        "leaks": {name: leaks(error, needle) for name, needle in needles.items()},
    }


def leaked(error: BaseException | None, needle: str) -> str:
    """결과 갈래의 낱말. 글(글, repr, 트레이스백)에 실린 것과 예외가 쥔 객체에만 있는 것을 가른다.

    쥔 객체는 openai 예외의 `request.headers`(인증 헤더와 Host)와 `body`(서버의 오류 본문)다.
    """
    if error is None:
        return "예외 없음"
    places = leaks(error, needle)
    if not places:
        return "없음"
    written = [place for place in places if not place.endswith(("request.headers", ".body"))]
    return "글에 있음" if written else "예외가 쥔 요청·응답에만 있음"


def message_view(message: AIMessage | None) -> dict[str, object] | None:
    """돌아온 메시지에서 core 가 읽는 것과 그 둘레. `reply`는 `reply_from`이 본 모양이다."""
    if message is None:
        return None
    return {
        "text": message.text,
        "content": message.content,
        "tool_calls": message.tool_calls,
        "invalid_tool_calls": message.invalid_tool_calls,
        "additional_kwargs": message.additional_kwargs,
        "response_metadata": message.response_metadata,
        "usage_metadata": message.usage_metadata,
        "reply": _reply(message),
    }


def _reply(message: AIMessage) -> dict[str, object]:
    try:
        return dataclasses.asdict(reply_from(message))
    except Exception as error:  # `reply_from`이 못 읽는 메시지도 결과다
        return {"error": qualified(type(error)), "text": clip(str(error))}


def authorizations(server: FakeServer) -> list[str]:
    """서버가 받은 요청마다의 Authorization 값. 없으면 빈 글자."""
    return [" ".join(request.header("Authorization")) for request in server.requests]


def bodies(server: FakeServer) -> list[dict[str, object]]:
    return [request.json() or {} for request in server.requests]


def targets(server: FakeServer) -> list[str]:
    return [f"{request.method} {request.target}" for request in server.requests]


class Collector(logging.Handler):
    def __init__(self) -> None:
        super().__init__(level=logging.DEBUG)
        self.records: list[logging.LogRecord] = []

    def emit(self, record: logging.LogRecord) -> None:
        self.records.append(record)


@contextmanager
def debug_logs() -> Iterator[Collector]:
    """루트 로거를 DEBUG 로 두고 모든 레코드를 모은다. 끝나면 되돌린다."""
    root = logging.getLogger()
    before = root.level
    collector = Collector()
    root.addHandler(collector)
    root.setLevel(logging.DEBUG)
    try:
        yield collector
    finally:
        root.removeHandler(collector)
        root.setLevel(before)


def rendered(record: logging.LogRecord) -> str:
    """레코드 하나가 로그에 찍히는 글. 예외 정보(`exc_info`)의 트레이스백까지 든다."""
    return logging.Formatter("%(name)s %(levelname)s %(message)s").format(record)
