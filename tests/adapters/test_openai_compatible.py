"""모델 서버 어댑터(`adapters/openai_compatible.py`)의 시험. 가짜 모델 서버(04)에 붙는다.

모델은 모델 소스(`ManifestModels`)를 지나 매니페스트로 만든다. 루프와 같은 길(`bind_tools` 뒤
`ainvoke`)로 부르고, 돌려받은 메시지를 core의 `reply_from`으로 읽어 응답의 해석까지 본다. 꺼진
서버와 500은 라이브러리가 재시도해 몇 초가 걸리므로(닫힌 포트 7.3~7.5초를 쟀다) 사례 수를
줄였다.

시간 단언은 모두 기한까지 거듭 견준다(`.claude/rules/tests.md`). 환경 변수는 `monkeypatch`로 심고,
어댑터는 부를 때마다 `os.environ`을 읽는다.
"""

from __future__ import annotations

import asyncio
import gc
import json
import logging
import os
from typing import TypeGuard

import anyio
import pytest
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI
from tests.adapters.fake_model_server import (
    CHAT_PATH,
    FakeModelServer,
    Received,
    Reply,
    completion,
    error_reply,
    tool_call,
)

from agent_os.adapters.models import ManifestModels
from agent_os.core.model import reply_from
from agent_os.core.ports import PluginError
from agent_os.sdk import PluginManifest, parse_manifest

# 연결이 닫히기를 기다리는 기한(초). 홀로 돌면 0.1초 안쪽이다.
PATIENCE_SECONDS = 20.0
KEY_VARIABLE = "LOCAL_MODEL_TEST_KEY"
KEY = "sk-local-test-key-4f2a"

ADD_TOOL: dict[str, object] = {
    "type": "function",
    "function": {
        "name": "add",
        "description": "두 수를 더한다",
        "parameters": {
            "type": "object",
            "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
            "required": ["a", "b"],
        },
    },
}


def _manifest(
    base_url: str,
    *,
    model_id: str = "served-model-name",
    api_key_env: str | None = None,
    max_tokens: int | None = None,
    temperature: float | None = None,
) -> PluginManifest:
    lines = [
        'schema_version = "1"',
        'kind = "model"',
        'name = "local-model"',
        'version = "0.1.0"',
        'provider = "openai-compatible"',
        f"model_id = {json.dumps(model_id)}",
        f"base_url = {json.dumps(base_url)}",
    ]
    if api_key_env is not None:
        lines.append(f"api_key_env = {json.dumps(api_key_env)}")
    if max_tokens is not None:
        lines.append(f"max_tokens = {max_tokens}")
    if temperature is not None:
        lines.append(f"temperature = {temperature}")
    return parse_manifest("\n".join(lines) + "\n")


def _model(base_url: str, **fields: object) -> BaseChatModel:
    manifest = _manifest(
        base_url,
        model_id=str(fields.get("model_id", "served-model-name")),
        api_key_env=str(fields["api_key_env"]) if "api_key_env" in fields else None,
        max_tokens=int(str(fields["max_tokens"])) if "max_tokens" in fields else None,
        temperature=float(str(fields["temperature"])) if "temperature" in fields else None,
    )
    return ManifestModels().build(manifest)


async def _ask(model: BaseChatModel, *, tools: bool = True) -> AIMessage:
    """루프가 모델을 부르는 길(`bind_tools` 뒤 `ainvoke`)."""
    if tools:
        return await model.bind_tools([ADD_TOOL]).ainvoke("2 더하기 3은?")
    return await model.ainvoke("2 더하기 3은?")


async def _failure_of(model: BaseChatModel) -> Exception:
    try:
        await _ask(model)
    except Exception as error:
        failure = error
    else:
        raise AssertionError("호출이 실패해야 한다")
    return failure


def _plain(error: Exception, kind: type[Exception]) -> None:
    """모든 실패가 같은 모양이다. 내장 타입이고 원인도 문맥도 잇지 않는다."""
    assert type(error) is kind, f"{type(error)!r}: {error}"
    assert type(error).__module__ == "builtins"
    assert error.__cause__ is None
    assert error.__context__ is None


def _is_object(value: object) -> TypeGuard[dict[str, object]]:
    return isinstance(value, dict)


def _is_list(value: object) -> TypeGuard[list[object]]:
    return isinstance(value, list)


def _echo_key(request: Received) -> Reply:
    """받은 키를 되울리는 서버. 키를 잘못 적었다는 401과 그 키를 함께 돌려준다."""
    key = request.header("authorization")[0].removeprefix("Bearer ")
    return error_reply(401, f"Incorrect API key provided: {key}. 키를 확인하라.")


@pytest.fixture(autouse=True)
def _clean_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """바깥 환경의 변수가 이 시험의 요청을 바꾸지 않게 한다."""
    for name in (
        "OPENAI_API_KEY",
        "OPENAI_BASE_URL",
        "OPENAI_PROXY",
        "OPENAI_ORG_ID",
        "OPENAI_ORGANIZATION",
        "OPENAI_PROJECT_ID",
        "OPENAI_CUSTOM_HEADERS",
        "LC_OUTPUT_VERSION",
        KEY_VARIABLE,
    ):
        monkeypatch.delenv(name, raising=False)


# 만들기 -------------------------------------------------------------------------------------


def test_모델_서버_모델은_ChatOpenAI_이고_model_id_와_주소가_모델에_닿는다() -> None:
    model = _model("http://model-server:8000/v1", model_id="skt/A.X-4.0-Light")

    assert isinstance(model, ChatOpenAI)
    assert model.model_name == "skt/A.X-4.0-Light"
    assert model.openai_api_base == "http://model-server:8000/v1"


def test_부를_때마다_새_모델과_새_클라이언트를_만든다() -> None:
    manifest = _manifest("http://model-server:8000/v1")
    models = ManifestModels()

    first, second = models.build(manifest), models.build(manifest)

    assert isinstance(first, ChatOpenAI)
    assert isinstance(second, ChatOpenAI)
    assert first is not second
    assert first.http_async_client is not second.http_async_client


async def test_만들기는_키_변수가_없어도_서버가_꺼져_있어도_실패하지_않는다() -> None:
    """키도 네트워크도 요구하지 않는다(ADR 0040). 키 변수가 환경에 없는데 만들어진다."""
    with FakeModelServer() as server:
        dead = server.base_url
    model = _model(dead, api_key_env=KEY_VARIABLE)

    assert isinstance(model, ChatOpenAI)


@pytest.mark.parametrize("address", ["http://h:8000/v1\\nGET /x", "http://h:abc/v1"])
def test_모델을_만들다_라이브러리가_거부한_주소는_플러그인_이름과_예외_종류의_PluginError다(
    address: str,
) -> None:
    """개행이 든 주소와 숫자가 아닌 포트는 읽는 단계(sdk)를 지나 만드는 순간 `httpx2.InvalidURL`로
    거부된다. 라이브러리의 글은 주소의 조각을 되울려 싣지 않는다."""
    manifest = parse_manifest(
        'schema_version = "1"\nkind = "model"\nname = "ax-4-light"\nversion = "0.1.0"\n'
        'provider = "openai-compatible"\nmodel_id = "m"\n'
        f'base_url = "{address}"\n'
    )

    with pytest.raises(PluginError) as error:
        ManifestModels().build(manifest)

    message = str(error.value)
    assert message.startswith("model 플러그인 ax-4-light 의 base_url 로 모델을 만들 수 없다 (")
    assert message.endswith(")")
    assert "InvalidURL" in message
    assert "GET /x" not in message
    assert "abc" not in message


# 요청 ---------------------------------------------------------------------------------------


async def test_요청은_chat_completions_로_가고_본문의_키는_넷이다() -> None:
    with FakeModelServer(completion()) as server:
        await _ask(_model(server.base_url))

    (request,) = server.requests
    assert request.method == "POST"
    assert request.path == CHAT_PATH
    body = request.json()
    assert body is not None
    assert set(body) == {"messages", "model", "stream", "tools"}
    assert body["model"] == "served-model-name"
    assert body["stream"] is False


async def test_도구는_함수_꼴이고_strict_가_없다() -> None:
    with FakeModelServer(completion()) as server:
        await _ask(_model(server.base_url))

    body = server.requests[0].json()
    assert body is not None
    tools = body["tools"]
    assert _is_list(tools)
    (tool,) = tools
    assert _is_object(tool)
    assert tool["type"] == "function"
    function = tool["function"]
    assert _is_object(function)
    assert function["name"] == "add"
    assert "strict" not in function


async def test_도구가_없으면_tools_도_없다() -> None:
    with FakeModelServer(completion()) as server:
        await _ask(_model(server.base_url), tools=False)

    body = server.requests[0].json()
    assert body is not None
    assert "tools" not in body


async def test_상한과_온도를_적지_않으면_요청에_실리지_않아_서버의_기본값이_쓰인다() -> None:
    with FakeModelServer(completion()) as server:
        await _ask(_model(server.base_url))

    body = server.requests[0].json()
    assert body is not None
    for name in ("max_tokens", "max_completion_tokens", "temperature", "tool_choice", "n"):
        assert name not in body


async def test_상한과_온도를_적으면_그_값이_요청에_실린다() -> None:
    with FakeModelServer(completion()) as server:
        await _ask(_model(server.base_url, max_tokens=77, temperature=0.25))

    body = server.requests[0].json()
    assert body is not None
    assert body["max_completion_tokens"] == 77
    assert body["temperature"] == 0.25


async def test_키_변수를_적지_않으면_자리_채움_글자가_인증_헤더로_간다() -> None:
    with FakeModelServer(completion()) as server:
        await _ask(_model(server.base_url))

    assert server.requests[0].header("authorization") == ["Bearer no-key"]


async def test_키_변수를_적으면_호출_직전에_읽은_값이_인증_헤더로_간다(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(KEY_VARIABLE, KEY)
    with FakeModelServer(completion()) as server:
        await _ask(_model(server.base_url, api_key_env=KEY_VARIABLE))

    assert server.requests[0].header("authorization") == [f"Bearer {KEY}"]


@pytest.mark.parametrize(
    ("model_id", "variables"),
    [
        ("served-model-name", {"OPENAI_API_KEY": "sk-ambient-9c1d"}),
        ("served-model-name", {"OPENAI_BASE_URL": "http://127.0.0.1:1/v1"}),
        ("served-model-name", {"OPENAI_PROXY": "http://127.0.0.1:1"}),
        ("served-model-name", {"LC_OUTPUT_VERSION": "responses/v1"}),
        ("gpt-5-pro-local", {}),
        ("my-codex-model", {}),
    ],
    ids=["OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_PROXY", "LC_OUTPUT_VERSION", "pro", "codex"],
)
async def test_환경의_변수와_모델_이름이_요청의_길과_행선지를_바꾸지_않는다(
    monkeypatch: pytest.MonkeyPatch, model_id: str, variables: dict[str, str]
) -> None:
    """응답 API로 가는 길(`/v1/responses`)이 닫혀 있고 환경의 키는 서버에 가지 않는다."""
    for name, value in variables.items():
        monkeypatch.setenv(name, value)
    with FakeModelServer(completion()) as server:
        await _ask(_model(server.base_url, model_id=model_id))

    (request,) = server.requests
    assert request.path == CHAT_PATH
    assert request.header("authorization") == ["Bearer no-key"]


# 응답 ---------------------------------------------------------------------------------------


async def test_응답의_글_토큰_수_모델_이름을_읽는다() -> None:
    usage = {"prompt_tokens": 7, "completion_tokens": 3, "total_tokens": 10}
    with FakeModelServer(completion(content="5입니다", usage=usage, model="served-x")) as server:
        message = await _ask(_model(server.base_url))

    reply = reply_from(message)
    assert reply.text == "5입니다"
    assert (reply.input_tokens, reply.output_tokens) == (7, 3)
    assert reply.model == "served-x"
    assert reply.tool_calls == ()


async def test_서버가_모델_이름과_토큰을_싣지_않으면_unknown_과_0이다() -> None:
    with FakeModelServer(completion(model=None, usage=None)) as server:
        message = await _ask(_model(server.base_url))

    reply = reply_from(message)
    assert reply.model == "unknown"
    assert (reply.input_tokens, reply.output_tokens) == (0, 0)


async def test_도구_호출을_읽는다() -> None:
    call = tool_call("add", '{"a": 2, "b": 3}', call_id="call_9")
    with FakeModelServer(completion(content=None, tool_calls=[call])) as server:
        message = await _ask(_model(server.base_url))

    (read,) = reply_from(message).tool_calls
    assert (read.id, read.name, dict(read.args)) == ("call_9", "add", {"a": 2, "b": 3})


async def test_깨진_인자의_도구_호출은_예외_없이_invalid_tool_calls_에_그_이름으로_든다() -> None:
    with FakeModelServer(completion(content=None, tool_calls=[tool_call("add", "{broken")])) as s:
        message = await _ask(_model(s.base_url))

    assert [call["name"] for call in message.invalid_tool_calls] == ["add"]
    assert message.tool_calls == []
    with pytest.raises(ValueError, match="올바른 JSON 이 아니다: add"):
        reply_from(message)


# 실패 ---------------------------------------------------------------------------------------


async def test_키_변수가_환경에_없으면_변수_이름만_든_실패이고_요청은_나가지_않는다() -> None:
    with FakeModelServer(completion()) as server:
        failure = await _failure_of(_model(server.base_url, api_key_env=KEY_VARIABLE))

    _plain(failure, RuntimeError)
    assert str(failure) == f"모델 서버의 키를 읽을 환경 변수 {KEY_VARIABLE} 가 없다"
    assert server.requests == []


async def test_키_변수의_값이_비었으면_없는_것과_같이_실패한다(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(KEY_VARIABLE, "")
    with FakeModelServer(completion()) as server:
        failure = await _failure_of(_model(server.base_url, api_key_env=KEY_VARIABLE))

    _plain(failure, RuntimeError)
    assert str(failure) == f"모델 서버의 키를 읽을 환경 변수 {KEY_VARIABLE} 가 없다"
    assert server.requests == []


@pytest.mark.parametrize(
    "value",
    ["key\n", "key ", " key", "키-값", "a\tb"],
    ids=["개행", "뒤 공백", "앞 공백", "한글", "탭"],
)
async def test_인증_헤더로_보낼_수_없는_키는_값을_싣지_않고_실패하며_요청은_나가지_않는다(
    monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    monkeypatch.setenv(KEY_VARIABLE, value)
    with FakeModelServer(completion()) as server:
        failure = await _failure_of(_model(server.base_url, api_key_env=KEY_VARIABLE))

    _plain(failure, RuntimeError)
    assert str(failure) == f"환경 변수 {KEY_VARIABLE} 의 값에 인증 헤더로 보낼 수 없는 글자가 있다"
    assert server.requests == []


def test_동기_호출도_같은_키_실패를_같은_문구로_낸다() -> None:
    model = _model("http://127.0.0.1:9/v1", api_key_env=KEY_VARIABLE)

    with pytest.raises(RuntimeError) as error:
        model.invoke("hi")

    assert str(error.value) == f"모델 서버의 키를 읽을 환경 변수 {KEY_VARIABLE} 가 없다"


async def test_거절한_서버의_상태와_글을_싣고_되울린_키는_가린다(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(KEY_VARIABLE, KEY)
    with FakeModelServer(_echo_key) as server:
        url = server.base_url
        failure = await _failure_of(_model(url, api_key_env=KEY_VARIABLE))

    _plain(failure, RuntimeError)
    message = str(failure)
    assert message.startswith(f"모델 서버 {url} 가 요청을 거절했다 (HTTP 401): ")
    assert "Incorrect API key provided: ***." in message
    assert KEY not in message
    assert len(server.requests) == 1


async def test_요청을_받은_뒤_환경의_키가_바뀌어도_옛_키도_새_키도_문구에_없다(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """호출 도중에 값이 한 번 바뀌면 서버가 되울리는 것은 읽어 둔 옛 값이다. 지금의 값만 찾으면 옛
    값이 `run_failed`의 문구로 트레이스에 남는다."""
    new_key = "sk-local-rotated-8e7b"
    monkeypatch.setenv(KEY_VARIABLE, KEY)

    def rotate_then_echo(request: Received) -> Reply:
        reply = _echo_key(request)
        os.environ[KEY_VARIABLE] = new_key
        return reply

    with FakeModelServer(rotate_then_echo) as server:
        failure = await _failure_of(_model(server.base_url, api_key_env=KEY_VARIABLE))

    message = str(failure)
    assert "HTTP 401" in message
    assert KEY not in message
    assert new_key not in message


async def test_문구의_주소는_모델_파일에_적은_글자_그대로_경로까지_실린다(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(KEY_VARIABLE, KEY)
    with FakeModelServer(_echo_key) as server:
        address = f"{server.base_url}/gateway/한글 경로"
        failure = await _failure_of(_model(address, api_key_env=KEY_VARIABLE))

    assert f"모델 서버 {address} 가 요청을 거절했다 (HTTP 401)" in str(failure)


async def test_서버의_500은_재시도_뒤_상태_오류로_끝난다() -> None:
    """429·500·연결 실패는 라이브러리가 세 번 보낸다. 몇 초가 걸리는 사례라 하나만 둔다."""
    replies = [error_reply(500, "서버 사정") for _ in range(3)]
    with FakeModelServer(*replies) as server:
        url = server.base_url
        failure = await _failure_of(_model(url))

    _plain(failure, RuntimeError)
    assert str(failure).startswith(f"모델 서버 {url} 가 요청을 거절했다 (HTTP 500): ")
    assert len(server.requests) == 3


async def test_꺼진_서버는_닿지_못했다는_ConnectionError_이고_원인_글을_싣지_않는다() -> None:
    """닫힌 포트는 재시도로 7초쯤 걸린다. 앞 시험의 서버가 있던 포트를 그대로 쓴다."""
    with FakeModelServer() as server:
        dead = server.base_url
    failure = await _failure_of(_model(dead))

    _plain(failure, ConnectionError)
    assert str(failure) == f"모델 서버 {dead} 에 닿지 못했다: Connection error."


async def test_200_응답의_error_칸은_호출이_실패했다는_문구로_끝난다() -> None:
    with FakeModelServer(Reply.json(200, {"error": {"message": "엔진이 죽었다"}})) as server:
        url = server.base_url
        failure = await _failure_of(_model(url))

    _plain(failure, RuntimeError)
    assert str(failure).startswith(f"모델 서버 {url} 호출이 실패했다 (ValueError): ")


@pytest.mark.parametrize(
    "arguments", ['["args-secret-6e1f", 2]', '"args-secret-6e1f"'], ids=["배열", "글자"]
)
async def test_객체가_아닌_도구_인자는_자리만_싣고_인자의_글자를_싣지_않는다(
    arguments: str,
) -> None:
    call = tool_call("add", arguments)
    with FakeModelServer(completion(content=None, tool_calls=[call])) as server:
        url = server.base_url
        failure = await _failure_of(_model(url))

    _plain(failure, RuntimeError)
    message = str(failure)
    assert message.startswith(f"모델 서버 {url} 의 응답을 읽지 못했다: ")
    assert message.endswith(" 의 꼴이 틀렸다")
    assert "args-secret-6e1f" not in message


# 수명과 취소 ---------------------------------------------------------------------------------


async def test_환경의_키를_바꾸면_다음_요청의_헤더가_바뀐다(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(KEY_VARIABLE, "sk-first-1111")
    with FakeModelServer(completion(), completion()) as server:
        model = _model(server.base_url, api_key_env=KEY_VARIABLE)
        await _ask(model)
        monkeypatch.setenv(KEY_VARIABLE, "sk-second-2222")
        await _ask(model)

    first, second = server.requests
    assert first.header("authorization") == ["Bearer sk-first-1111"]
    assert second.header("authorization") == ["Bearer sk-second-2222"]


async def _settled(server: FakeModelServer) -> bool:
    return await asyncio.to_thread(server.connections_settled, PATIENCE_SECONDS)


async def test_한_루프에서_모델_다섯을_만들어_부르고_놓으면_연결이_모두_닫혀_있다() -> None:
    """쉬는 연결을 두지 않는 클라이언트라 놓인 모델이 연결을 남기지 않는다. 리눅스에서는 기본값
    클라이언트도 놓으면 닫아 이 시험이 윈도에서만 퇴행을 가른다."""
    with FakeModelServer(*[completion() for _ in range(5)]) as server:
        for _ in range(5):
            model = _model(server.base_url)
            await _ask(model)
            del model
        gc.collect()

        assert server.opened_connections == 5
        assert await _settled(server)


async def test_401로_끝난_호출과_기한에_끊긴_호출_뒤에도_연결이_모두_닫혀_있다(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(KEY_VARIABLE, KEY)
    slow = completion(delay_seconds=1.0)
    with FakeModelServer(_echo_key, slow) as server:
        refused = _model(server.base_url, api_key_env=KEY_VARIABLE)
        await _failure_of(refused)
        cut = _model(server.base_url)
        with anyio.move_on_after(0.3) as scope:
            await _ask(cut)
        assert scope.cancelled_caught
        del refused, cut
        gc.collect()

        assert await _settled(server)


async def test_실행_기한이_답을_기다리는_호출을_끊고_취소가_다른_예외로_바뀌지_않는다() -> None:
    with FakeModelServer(completion(delay_seconds=1.0)) as server:
        model = _model(server.base_url)
        with anyio.move_on_after(0.3) as scope:
            await _ask(model)

        assert scope.cancelled_caught


async def test_모델_하나를_쥔_채_여러_번_불러도_놓기_전에_연결이_모두_닫혀_있다() -> None:
    """호출마다 연결을 새로 맺는 값을 치르고 쉬는 연결을 남기지 않는다. 기본값 클라이언트는 쥔 채
    부르면 연결 하나를 쥐고 있어 두 OS 모두에서 이 사례가 가른다."""
    with FakeModelServer(*[completion() for _ in range(4)]) as server:
        model = _model(server.base_url)
        for _ in range(4):
            await _ask(model)

        assert server.opened_connections == 4
        assert await _settled(server)
        assert isinstance(model, ChatOpenAI)


def test_한_프로세스에서_루프를_둘_차례로_돌려도_같은_주소를_부를_수_있다() -> None:
    """이벤트 루프 둘을 차례로 여닫는 것 자체를 재므로 pytest-asyncio의 루프를 쓸 수 없고 동기
    시험 함수에서 `asyncio.run`을 직접 부른다(`.claude/rules/tests.md`의 예외). 라이브러리가
    주소별로 나눠 쓰는 클라이언트는 둘째 루프에서 `Event loop is closed`로 실패한다."""

    async def once(server: FakeModelServer) -> AIMessage:
        return await _ask(_model(server.base_url))

    with FakeModelServer(completion(content="첫째"), completion(content="둘째")) as server:
        first = asyncio.run(once(server))
        second = asyncio.run(once(server))

    assert (first.text, second.text) == ("첫째", "둘째")


# 로그 ---------------------------------------------------------------------------------------


@pytest.mark.parametrize("refused", [False, True], ids=["성공", "401"])
async def test_루트_로거를_DEBUG로_켜도_모든_레코드에_키_값이_없다(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, *, refused: bool
) -> None:
    """로그 필터는 두지 않는다. 라이브러리의 판을 올리면 이 시험이 다시 본다. 서버가 그 키를 받았고
    `httpx2`의 요청 줄이 레코드에 있다는 표지 둘을 함께 단언해, 로그를 실제로 모았음을 보인다."""
    monkeypatch.setenv(KEY_VARIABLE, KEY)
    caplog.set_level(logging.DEBUG)
    with FakeModelServer(_echo_key if refused else completion()) as server:
        model = _model(server.base_url, api_key_env=KEY_VARIABLE)
        if refused:
            await _failure_of(model)
        else:
            await _ask(model)

    assert server.requests[0].header("authorization") == [f"Bearer {KEY}"]
    assert any(record.name.startswith("httpx2") for record in caplog.records)
    for record in caplog.records:
        assert KEY not in record.getMessage()
        assert KEY not in repr(record.args)
