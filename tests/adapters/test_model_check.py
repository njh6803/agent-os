"""모델 서버의 접속 확인(`ModelSource.check`, `adapters/model_check.py`)의 시험. 가짜 모델 서버에
붙는다.

모델 소스(`ManifestModels`)를 지나 매니페스트로 확인한다. 두 제공사마다 같은 갈래를 본다. 붙는 서버,
닫힌 포트, 401, 없는 모델, 오류 상태, 늦는 서버, 서버가 오류 본문에 되울린 키, 재시도 없음이다.
환경 변수는 `monkeypatch`로 심고, 어댑터는 부를 때마다 읽는다. 기한을 짧게 줘서 늦는 서버를 재고,
시간 단언은 상한을 넉넉히 둔다(`.claude/rules/tests.md`).
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from collections.abc import Callable
from dataclasses import replace

import anthropic
import httpx2
import openai
import pytest
from langchain_anthropic import ChatAnthropic
from pydantic import SecretStr
from tests.adapters.fake_model_server import (
    FakeModelServer,
    Reply,
    anthropic_error_reply,
    anthropic_model_reply,
    error_reply,
    models_list_reply,
)

from agent_os.adapters.model_check import anthropic_check_client, display_address, reason_tail
from agent_os.adapters.models import ManifestModels
from agent_os.core.ports import CheckOutcome, ModelSource, PluginError, Reached, Unreached
from agent_os.sdk import PluginManifest, parse_manifest

KEY = "sk-ant-test-key-91c4"
ECHO = "probe-echo-7f3a"
KEY_VARIABLE = "LOCAL_MODEL_CHECK_KEY"
SHORT = 0.3
# 홀로 돌면 1초 안쪽이다. 다른 시험과 겹쳐도 닿는 넉넉한 상한이다.
GENEROUS = 15.0
# 본문을 흘리는 총 시간. 기한(`SHORT`)보다 훨씬 길고, 기한이 막지 않으면 이 시간 뒤에야 붙은 것으로
# 돌아온다. 기한으로 끝난 시험은 이 시간보다 일찍 돌아온다.
DRIP = 2.0
AMBIENT = (
    "ANTHROPIC_API_URL",
    "ANTHROPIC_BASE_URL",
    "ANTHROPIC_PROXY",
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "OPENAI_API_KEY",
    "OPENAI_BASE_URL",
    "OPENAI_PROXY",
    "OPENAI_ORG_ID",
    "OPENAI_ORGANIZATION",
    "OPENAI_PROJECT_ID",
    "OPENAI_CUSTOM_HEADERS",
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "NO_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
    "no_proxy",
    KEY_VARIABLE,
)


@pytest.fixture(autouse=True)
def _clean_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """이 PC의 환경이 요청의 길을 바꾸지 않게 주소·키·프록시 변수를 비운다."""
    for name in AMBIENT:
        monkeypatch.delenv(name, raising=False)


def _anthropic_manifest(model_id: str = "claude-haiku-4-5") -> PluginManifest:
    return parse_manifest(
        'schema_version = "1"\nkind = "model"\nname = "haiku"\nversion = "0.1.0"\n'
        f'provider = "anthropic"\nmodel_id = {json.dumps(model_id)}\n'
    )


def _compatible_manifest(
    base_url: str, *, model_id: str = "served-model-name", api_key_env: str | None = None
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
    return parse_manifest("\n".join(lines) + "\n")


def _use_anthropic(monkeypatch: pytest.MonkeyPatch, root_url: str, key: str = KEY) -> None:
    """환경으로 주소와 키를 심는다. 모델 객체가 이 변수들에서 읽는다."""
    monkeypatch.setenv("ANTHROPIC_API_URL", root_url)
    monkeypatch.setenv("ANTHROPIC_API_KEY", key)


async def _check(manifest: PluginManifest, deadline: float = 10.0) -> CheckOutcome:
    models: ModelSource = ManifestModels(check_deadline_seconds=deadline)
    return await models.check(manifest)


def _reason(outcome: CheckOutcome, because: str = "") -> str:
    """붙지 못함의 까닭 글. 붙지 못함이 아니면 `because` 를 앞에 단 글로 실패한다. 어느 결정이
    어긋나 붙음이 나왔는지가 실패 출력에 그 시험만의 글로 남는다."""
    assert isinstance(outcome, Unreached), f"{because}{outcome}"
    assert type(outcome.reason) is str
    assert outcome.reason
    return outcome.reason


def _closed_roots() -> tuple[str, str]:
    """떴다가 꺼진 서버의 (뿌리 주소, 모델 파일의 `base_url`). 그 포트는 닫혀 있다."""
    with FakeModelServer() as server:
        return server.root_url, server.base_url


def _head(name: str, address: str) -> str:
    return f"모델 {name}({address})에 붙지 못했다: "


async def _wait_for_request(server: FakeModelServer) -> None:
    deadline = time.monotonic() + GENEROUS
    while not server.requests:
        assert time.monotonic() < deadline, "서버가 요청을 받지 못했다"
        await asyncio.sleep(0.02)


# --- anthropic -------------------------------------------------------------------------------


async def test_anthropic_은_그_모델_하나를_묻는_요청_한_건을_보내고_200이면_붙은_것이다(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with FakeModelServer(anthropic_model_reply("claude-haiku-4-5")) as server:
        _use_anthropic(monkeypatch, server.root_url)

        outcome = await _check(_anthropic_manifest())

        assert outcome == Reached(), f"모델 객체의 주소로 묻지 않았다: {outcome}"
        (request,) = server.requests
        assert request.method == "GET"
        assert request.path == "/v1/models/claude-haiku-4-5"
        assert request.header("x-api-key") == [KEY]


async def test_anthropic_은_돌아온_id가_물은_id와_달라도_200이면_붙은_것이다(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """날짜를 뗀 이름을 물으면 제공사가 날짜 붙은 id를 돌려준다(이야기 7)."""
    with FakeModelServer(anthropic_model_reply("claude-opus-4-5-20251101")) as server:
        _use_anthropic(monkeypatch, server.root_url)

        outcome = await _check(_anthropic_manifest("claude-opus-4-5"))

        assert outcome == Reached()
        assert [request.path for request in server.requests] == ["/v1/models/claude-opus-4-5"]


async def test_anthropic_닫힌_포트는_서버에_닿지_못했다이다(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root, _ = _closed_roots()
    _use_anthropic(monkeypatch, root)

    outcome = await _check(_anthropic_manifest())

    assert _reason(outcome) == _head("haiku", root) + "서버에 닿지 못했다"


@pytest.mark.parametrize("status", [401, 403])
async def test_anthropic_키_거절은_상태_번호를_싣는다(
    monkeypatch: pytest.MonkeyPatch, status: int
) -> None:
    with FakeModelServer(anthropic_error_reply(status, "invalid x-api-key")) as server:
        _use_anthropic(monkeypatch, server.root_url)

        outcome = await _check(_anthropic_manifest())

        assert _reason(outcome) == (
            _head("haiku", server.root_url) + f"키를 받아들이지 않았다(HTTP {status})"
        )


async def test_anthropic_없는_모델은_그_이름의_모델이_없다고_답했다이다(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with FakeModelServer(
        anthropic_error_reply(404, "model: nope", kind="not_found_error")
    ) as server:
        _use_anthropic(monkeypatch, server.root_url)

        outcome = await _check(_anthropic_manifest("nope"))

        assert _reason(outcome) == (
            _head("haiku", server.root_url) + "그 이름의 모델이 없다고 답했다(HTTP 404)"
        )


@pytest.mark.parametrize("status", [429, 500, 529])
async def test_anthropic_오류_상태는_요청_한_건에_서버가_오류로_답했다이다(
    monkeypatch: pytest.MonkeyPatch, status: int
) -> None:
    """라이브러리의 재시도를 끈다. 500에 요청이 세 건 가던 기본 설정이 아니다."""
    with FakeModelServer(
        anthropic_error_reply(status, "overloaded"), anthropic_model_reply("claude-haiku-4-5")
    ) as server:
        _use_anthropic(monkeypatch, server.root_url)

        outcome = await _check(_anthropic_manifest())

        assert _reason(outcome, because="다시 시도해 둘째 요청에 답을 받았다: ") == (
            _head("haiku", server.root_url) + f"서버가 오류로 답했다(HTTP {status})"
        )
        assert len(server.requests) == 1


async def test_anthropic_답이_늦는_서버는_기한_뒤_시간_초과다(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with FakeModelServer(anthropic_model_reply("claude-haiku-4-5", delay_seconds=4.0)) as server:
        _use_anthropic(monkeypatch, server.root_url)
        started = time.monotonic()

        outcome = await _check(_anthropic_manifest(), SHORT)

        assert _reason(outcome) == _head("haiku", server.root_url) + "0.3초 안에 답이 없었다"
        assert time.monotonic() - started < GENEROUS
        assert len(server.requests) == 1


async def test_anthropic_본문을_조금씩_흘리는_서버는_총_기한_뒤_시간_초과다(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """라이브러리의 시간 제한은 읽기 한 번마다라서, 간격이 짧게 흘리는 서버는 그 제한에 걸리지
    않는다. 총 시간을 막는 것은 `move_on_after` 뿐이다."""
    slow = replace(anthropic_model_reply("claude-haiku-4-5"), drip_seconds=DRIP)
    with FakeModelServer(slow) as server:
        _use_anthropic(monkeypatch, server.root_url)
        started = time.monotonic()

        outcome = await _check(_anthropic_manifest(), SHORT)

        reason = _reason(outcome, because="기한이 총 시간을 막지 못했다: ")
        assert reason == _head("haiku", server.root_url) + "0.3초 안에 답이 없었다"
        assert time.monotonic() - started < DRIP


@pytest.mark.parametrize("status", [401, 404, 500])
async def test_anthropic_서버가_오류_본문에_되울린_키와_글은_이유에_없다(
    monkeypatch: pytest.MonkeyPatch, status: int
) -> None:
    """키 글자만 가리는 구현(예외의 글을 옮기고 키만 지움)은 표지 문구가 남아 여기서 빨갛다."""
    with FakeModelServer(anthropic_error_reply(status, f"{ECHO} 받은 키 {KEY}")) as server:
        _use_anthropic(monkeypatch, server.root_url)

        reason = _reason(await _check(_anthropic_manifest()))

        assert KEY not in reason
        assert ECHO not in reason
        assert reason.startswith(_head("haiku", server.root_url))


async def test_anthropic_주소의_사용자_정보와_쿼리는_이유에_없다(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with FakeModelServer(anthropic_error_reply(500, "boom")) as server:
        decorated = server.root_url.replace("http://", "http://alice:s3cretpw@") + "/?k=v"
        _use_anthropic(monkeypatch, decorated)

        reason = _reason(await _check(_anthropic_manifest()))

        for leaked in ("alice", "s3cretpw", "k=v", "?"):
            assert leaked not in reason
        assert reason.startswith(_head("haiku", server.root_url))


async def test_anthropic_키가_없으면_요청을_보내지_않고_키_없음이다(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with FakeModelServer(anthropic_model_reply("claude-haiku-4-5")) as server:
        monkeypatch.setenv("ANTHROPIC_API_URL", server.root_url)

        outcome = await _check(_anthropic_manifest())

        assert _reason(outcome) == (
            _head("haiku", server.root_url) + "키가 없다(환경 변수 ANTHROPIC_API_KEY)"
        )
        assert server.requests == []


def test_anthropic_모델_객체는_키가_없으면_키_칸이_빈_글이다(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """확인이 '키가 없다'를 가르는 근거를 고정한다. 이 값이 바뀌면 확인이 빈 키로 요청을 보낸다."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)

    model = ChatAnthropic(
        model_name="claude-haiku-4-5", max_tokens_to_sample=16, timeout=None, stop=None
    )

    assert model.anthropic_api_key.get_secret_value() == ""


async def test_anthropic_환경의_프록시를_지나_묻는다(monkeypatch: pytest.MonkeyPatch) -> None:
    """모델 객체가 환경의 `ANTHROPIC_PROXY`에서 프록시 칸을 읽는다. 확인도 그 칸을 따른다."""
    with FakeModelServer(anthropic_model_reply("claude-haiku-4-5")) as proxy:
        _use_anthropic(monkeypatch, "http://model.test")
        monkeypatch.setenv("ANTHROPIC_PROXY", proxy.root_url)

        outcome = await _check(_anthropic_manifest())

        assert outcome == Reached()
        (request,) = proxy.requests
        assert request.target == "http://model.test/v1/models/claude-haiku-4-5"
        assert request.header("x-api-key") == [KEY]


async def test_anthropic_스킴이_없는_프록시는_예외가_아니라_닿지_못함으로_돌아오고_글에_싣지_않는다(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """확인하는 클라이언트를 짓다 난 예외(httpx가 이 프록시 값을 `ValueError`로 거부한다)도
    라이브러리 호출에서 난 예외다. 사용자 정보가 든 프록시 글이 예외의 글에 실려 관리 경로의 500과
    서버 기록으로 가지 않게 갈래의 `Unreached` 로 바꾼다."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", KEY)
    monkeypatch.setenv("ANTHROPIC_PROXY", "user:pw@proxy.corp:3128")

    outcome = await _check(_anthropic_manifest())

    reason = _reason(outcome)
    assert reason == _head("haiku", "https://api.anthropic.com") + "확인하지 못했다(ValueError)"
    assert "user:pw" not in reason
    assert "proxy.corp" not in reason


async def test_anthropic_확인하는_클라이언트는_모델_객체의_덧붙임_헤더를_싣는다() -> None:
    """지금 제품은 그 칸을 채우지 않아 포트로 부르는 시험은 어떤 구현에서도 초록이다. 클라이언트를
    모델 객체에서 짓는 함수에 헤더를 든 모델 객체를 넘겨 헤더가 요청에 실리는지 본다."""
    with FakeModelServer(anthropic_model_reply("claude-haiku-4-5")) as server:
        model = ChatAnthropic(
            model_name="claude-haiku-4-5",
            max_tokens_to_sample=16,
            timeout=None,
            stop=None,
            base_url=server.root_url,
            api_key=SecretStr(KEY),
            default_headers={"X-Relay-Tenant": "tenant-7"},
        )

        async with anthropic_check_client(model, 10.0) as client:
            await client.models.retrieve("claude-haiku-4-5")

        (request,) = server.requests
        assert request.header("x-relay-tenant") == ["tenant-7"]
        assert request.header("x-api-key") == [KEY]


# --- openai-compatible -----------------------------------------------------------------------


async def test_openai_compatible_은_목록을_묻는_요청_한_건을_보내고_이름이_있으면_붙은_것이다(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(KEY_VARIABLE, KEY)
    with FakeModelServer(models_list_reply(["other-model", "served-model-name"])) as server:
        manifest = _compatible_manifest(server.base_url, api_key_env=KEY_VARIABLE)

        outcome = await _check(manifest)

        assert outcome == Reached()
        (request,) = server.requests
        assert request.method == "GET"
        assert request.path == "/v1/models"
        assert request.header("authorization") == [f"Bearer {KEY}"]


async def test_openai_compatible_목록에_없으면_모델이_목록에_없다이고_다음_쪽을_읽지_않는다() -> (
    None
):
    with FakeModelServer(
        models_list_reply(["other-model"], has_more=True), models_list_reply(["served-model-name"])
    ) as server:
        manifest = _compatible_manifest(server.base_url)

        outcome = await _check(manifest)

        assert _reason(outcome) == (
            _head("local-model", server.base_url) + "그 이름의 모델이 목록에 없다"
        )
        assert len(server.requests) == 1


async def test_openai_compatible_은_글자가_다른_id를_같은_것으로_보지_않는다() -> None:
    with FakeModelServer(models_list_reply(["Served-Model-Name", "served-model-name-2"])) as server:
        outcome = await _check(_compatible_manifest(server.base_url))

        reason = _reason(outcome, because="글자가 다른 id 를 같은 것으로 봤다: ")
        assert reason.endswith("그 이름의 모델이 목록에 없다")


async def test_openai_compatible_키_칸이_없으면_자리_채움_글자를_싣고_환경의_API_KEY를_싣지_않는다(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-ambient-must-not-travel")
    with FakeModelServer(models_list_reply(["served-model-name"])) as server:
        outcome = await _check(_compatible_manifest(server.base_url))

        assert outcome == Reached()
        (request,) = server.requests
        assert request.header("authorization") == ["Bearer no-key"]


async def test_openai_compatible_은_모델_파일의_주소로_가고_환경의_주소와_프록시를_따르지_않는다(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with (
        FakeModelServer(models_list_reply(["served-model-name"])) as intended,
        FakeModelServer(models_list_reply(["served-model-name"])) as decoy,
    ):
        monkeypatch.setenv("OPENAI_BASE_URL", decoy.base_url)
        monkeypatch.setenv("OPENAI_PROXY", decoy.root_url)

        outcome = await _check(_compatible_manifest(intended.base_url))

        assert outcome == Reached()
        assert len(intended.requests) == 1
        assert decoy.requests == []


async def test_openai_compatible_닫힌_포트는_서버에_닿지_못했다이다() -> None:
    _, base_url = _closed_roots()

    outcome = await _check(_compatible_manifest(base_url))

    assert _reason(outcome) == _head("local-model", base_url) + "서버에 닿지 못했다"


@pytest.mark.parametrize(
    ("base_url", "environment", "kinds"),
    [
        ("http://127.0.0.1:abc/v1", {}, ("InvalidURL",)),
        # 없는 파일을 윈도의 ssl 은 `OSError` 로, 리눅스는 `FileNotFoundError` 로 낸다.
        (
            "http://127.0.0.1:9/v1",
            {"SSL_CERT_FILE": "/없는/인증서.pem"},
            ("OSError", "FileNotFoundError"),
        ),
    ],
    ids=["숫자가_아닌_포트", "없는_인증서_파일"],
)
async def test_openai_compatible_클라이언트를_짓다_난_예외도_예외가_아니라_닿지_못함으로_돌아온다(
    monkeypatch: pytest.MonkeyPatch,
    base_url: str,
    environment: dict[str, str],
    kinds: tuple[str, ...],
) -> None:
    """매니페스트 검사는 호스트만 보아 `:abc` 같은 포트를 지나치고, 환경의 인증서 파일은 아무
    검사도 지나지 않는다. 그 값에서 클라이언트를 짓다 나는 예외도 라이브러리 호출에서 난 예외이므로
    포트의 약속대로 `Unreached` 로 돌아와야 한다(실행의 `chat_openai_compatible` 도 같은 자리를
    `PluginError` 로 바꾼다)."""
    for variable, value in environment.items():
        monkeypatch.setenv(variable, value)

    outcome = await _check(_compatible_manifest(base_url))

    reason = _reason(outcome, because="클라이언트를 짓다 난 예외가 올라왔다: ")
    assert reason in [_head("local-model", base_url) + f"확인하지 못했다({kind})" for kind in kinds]


@pytest.mark.parametrize("status", [401, 403])
async def test_openai_compatible_키_거절은_상태_번호를_싣는다(status: int) -> None:
    with FakeModelServer(error_reply(status, "bad key")) as server:
        outcome = await _check(_compatible_manifest(server.base_url))

        assert _reason(outcome) == (
            _head("local-model", server.base_url) + f"키를 받아들이지 않았다(HTTP {status})"
        )


@pytest.mark.parametrize("status", [404, 429, 500, 529])
async def test_openai_compatible_그_밖의_오류_상태는_요청_한_건에_서버가_오류로_답했다이다(
    status: int,
) -> None:
    with FakeModelServer(
        error_reply(status, "boom"), models_list_reply(["served-model-name"])
    ) as server:
        outcome = await _check(_compatible_manifest(server.base_url))

        assert _reason(outcome, because="다시 시도해 둘째 요청에 답을 받았다: ") == (
            _head("local-model", server.base_url) + f"서버가 오류로 답했다(HTTP {status})"
        )
        assert len(server.requests) == 1


async def test_openai_compatible_답이_늦는_서버는_기한_뒤_시간_초과다() -> None:
    with FakeModelServer(models_list_reply(["served-model-name"], delay_seconds=4.0)) as server:
        started = time.monotonic()

        outcome = await _check(_compatible_manifest(server.base_url), SHORT)

        assert _reason(outcome) == (
            _head("local-model", server.base_url) + "0.3초 안에 답이 없었다"
        )
        assert time.monotonic() - started < GENEROUS
        assert len(server.requests) == 1


async def test_openai_compatible_본문을_조금씩_흘리는_서버는_총_기한_뒤_시간_초과다() -> None:
    slow = replace(models_list_reply(["served-model-name"]), drip_seconds=DRIP)
    with FakeModelServer(slow) as server:
        started = time.monotonic()

        outcome = await _check(_compatible_manifest(server.base_url), SHORT)

        reason = _reason(outcome, because="기한이 총 시간을 막지 못했다: ")
        assert reason == _head("local-model", server.base_url) + "0.3초 안에 답이 없었다"
        assert time.monotonic() - started < DRIP


@pytest.mark.parametrize("status", [401, 404, 500])
async def test_openai_compatible_서버가_오류_본문에_되울린_키와_글은_이유에_없다(
    monkeypatch: pytest.MonkeyPatch, status: int
) -> None:
    monkeypatch.setenv(KEY_VARIABLE, KEY)
    with FakeModelServer(error_reply(status, f"{ECHO} 받은 키 {KEY}")) as server:
        manifest = _compatible_manifest(server.base_url, api_key_env=KEY_VARIABLE)

        reason = _reason(await _check(manifest))

        assert KEY not in reason
        assert ECHO not in reason
        assert reason.startswith(_head("local-model", server.base_url))


async def test_openai_compatible_변수가_없거나_비면_요청을_보내지_않고_키_없음이다(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with FakeModelServer(models_list_reply(["served-model-name"])) as server:
        manifest = _compatible_manifest(server.base_url, api_key_env=KEY_VARIABLE)
        expected = _head("local-model", server.base_url) + f"키가 없다(환경 변수 {KEY_VARIABLE})"

        assert _reason(await _check(manifest)) == expected
        monkeypatch.setenv(KEY_VARIABLE, "")
        assert _reason(await _check(manifest)) == expected
        assert server.requests == []


async def test_openai_compatible_변수의_값에_헤더로_보낼_수_없는_글자가_있으면_요청을_보내지_않는다(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    unsendable = "키-값-비밀"
    monkeypatch.setenv(KEY_VARIABLE, unsendable)
    with FakeModelServer(models_list_reply(["served-model-name"])) as server:
        manifest = _compatible_manifest(server.base_url, api_key_env=KEY_VARIABLE)

        reason = _reason(await _check(manifest))

        assert reason == (
            _head("local-model", server.base_url)
            + f"키에 인증 헤더로 보낼 수 없는 글자가 있다(환경 변수 {KEY_VARIABLE})"
        )
        assert unsendable not in reason
        assert server.requests == []


async def test_openai_compatible_목록이_아닌_200_응답은_그_밖_갈래로_예외_종류만_싣는다() -> None:
    with FakeModelServer(Reply.text(200, f"<html>{ECHO}</html>")) as server:
        reason = _reason(await _check(_compatible_manifest(server.base_url)))

        assert reason.startswith(_head("local-model", server.base_url) + "확인하지 못했다(")
        assert ECHO not in reason


# --- 두 제공사에 같은 것 ------------------------------------------------------------------------


@pytest.mark.parametrize("provider", ["anthropic", "openai-compatible"])
async def test_확인은_예외도_로그도_남기지_않고_바깥의_취소는_삼키지_않는다(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture, provider: str
) -> None:
    caplog.set_level(logging.WARNING)
    root, base_url = _closed_roots()
    _use_anthropic(monkeypatch, root)
    manifest = _anthropic_manifest() if provider == "anthropic" else _compatible_manifest(base_url)

    outcome = await _check(manifest)

    assert isinstance(outcome, Unreached)
    assert caplog.records == []

    with FakeModelServer(
        anthropic_model_reply("claude-haiku-4-5", delay_seconds=4.0)
        if provider == "anthropic"
        else models_list_reply(["served-model-name"], delay_seconds=4.0)
    ) as slow:
        _use_anthropic(monkeypatch, slow.root_url)
        manifest = (
            _anthropic_manifest()
            if provider == "anthropic"
            else _compatible_manifest(slow.base_url)
        )
        task = asyncio.create_task(_check(manifest))
        await _wait_for_request(slow)

        task.cancel()

        with pytest.raises(asyncio.CancelledError):
            await task


@pytest.mark.parametrize("provider", ["anthropic", "openai-compatible"])
async def test_모델이_아닌_매니페스트와_공백뿐인_model_id는_구성_오류의_예외다(
    provider: str,
) -> None:
    models: ModelSource = ManifestModels()
    agent = parse_manifest(
        'schema_version = "1"\nkind = "agent"\nname = "calc"\nversion = "0.1.0"\n'
        'entrypoint = "agent:Agent"\n'
    )
    blank = (
        _anthropic_manifest(" ")
        if provider == "anthropic"
        else _compatible_manifest("http://model-server:8000/v1", model_id=" ")
    )

    with pytest.raises(PluginError, match="calc 은 provider 와 model_id 가 없어 모델이 아니다"):
        await models.check(agent)
    with pytest.raises(PluginError, match="model_id 가 공백뿐이다"):
        await models.check(blank)


def _request() -> httpx2.Request:
    return httpx2.Request("GET", "http://model.test/v1/models")


@pytest.mark.parametrize(
    ("make", "expected"),
    [
        (lambda: anthropic.APITimeoutError(request=_request()), "10초 안에 답이 없었다"),
        (lambda: openai.APITimeoutError(request=_request()), "10초 안에 답이 없었다"),
        (lambda: anthropic.APIConnectionError(request=_request()), "서버에 닿지 못했다"),
        (lambda: openai.APIConnectionError(request=_request()), "서버에 닿지 못했다"),
        (lambda: ValueError(ECHO), "확인하지 못했다(ValueError)"),
        (lambda: RuntimeError(""), "확인하지 못했다(RuntimeError)"),
    ],
    ids=[
        "anthropic 시간 초과",
        "openai 시간 초과",
        "anthropic 연결 오류",
        "openai 연결 오류",
        "그 밖의 예외",
        "글이 빈 예외",
    ],
)
def test_시간_초과는_연결_오류의_하위_종류라도_닿지_못함보다_먼저_가르고_그_밖은_종류_이름만_싣는다(
    make: Callable[[], Exception], expected: str
) -> None:
    tail = reason_tail(make(), 10.0, not_found_tail=None)

    assert tail == expected


# --- 주소를 보이는 글로 -------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("raw", "shown"),
    [
        ("https://api.anthropic.com/", "https://api.anthropic.com"),
        ("http://user:pass@host:8000/v1?k=v#frag", "http://host:8000/v1"),
        ("http://a:b@c:d@host/v1", "http://host/v1"),
        ("http://model-server:8000/v1", "http://model-server:8000/v1"),
        ("http://[::1]:8000/v1", "http://[::1]:8000/v1"),
        ("http://host/한\n글", "http://host/한\\n글"),
    ],
)
def test_보이는_주소는_사용자_정보와_쿼리를_떼고_찍히지_않는_글자를_이스케이프한다(
    raw: str, shown: str
) -> None:
    assert display_address(raw) == shown
