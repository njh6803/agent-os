"""모델 서버 모델. 모델 매니페스트가 `openai-compatible` 이면 그 `base_url` 의 Chat Completions 에
붙는다.

`chat_openai_compatible` 이 모델 매니페스트의 칸으로 `ChatOpenAI` 의 하위 클래스 하나를 만든다.
제공사로 가르는 것은 모델 소스(`adapters/models.py`)의 몫이고, 만들기는 키도 네트워크도 요구하지
않는다(ADR 0040). 결정과 근거는 ADR 0057 이고, 측정은 `.scratch/local-model/probes/openai_compat.py`
(사례 108)와 `check_adapter_types.py`, 리눅스 수명 사례 `linux_lifetime.sh` 다. 이 모듈은 그
프로브의 `adapter_candidate.py` 를 옮긴 것이 아니라 거기서 본 모양으로 새로 지었다.

**요청.** 생성자에 모두 이름으로 넘긴다. 고정하는 인자 넷은 환경이 요청의 길과 행선지를 바꾸지
못하게 막는다. `use_responses_api=False` 는 모델 이름(`gpt-5-pro-local`)이나 환경의
`LC_OUTPUT_VERSION` 이 요청을 `/v1/responses` 로 보내는 것을, `openai_proxy=None` 은 환경의
`OPENAI_PROXY` 가 요청을 키와 함께 그 프록시로 보내는 것을, `output_version=None` 은 환경의
`LC_OUTPUT_VERSION` 이 그 칸을 채우는 것을 막는다. `disable_streaming=True` 는 `astream` 도
`_agenerate` 를 지나게 해 아래 감싸기를 비켜 가지 않게 한다. 토큰 단위 스트리밍은 범위 밖이라(ADR
0014) 잃는 것이 없다. 상한(`max_tokens`)과 온도(`temperature`)는 매니페스트에 있을 때만 요청에
실린다. 키는 언제나 이름으로 넘기므로 환경의 `OPENAI_API_KEY` 는 요청 어디에도 없다. 타임아웃과
재시도는 라이브러리의 기본값 그대로다(429·500·연결 실패는 세 번, 400·401·404는 한 번 보낸다).

**키.** `api_key` 에는 키를 읽는 함수(`_KeySource`)를 넘긴다. 환경을 읽기만 하고 호출 직전에
읽으므로 환경의 값을 바꾸면 다음 요청의 헤더가 바뀐다. `api_key_env` 가 없으면 자리 채움 글자
`no-key` 를 보낸다. 변수가 없거나 비었거나, 값에 인증 헤더로 보낼 수 없는 글자가 있으면 변수의
이름만 든 `RuntimeError` 다. 라이브러리에 그대로 넘기면 그 값이 예외의 글이나 원인 사슬에 실린다.
앞뒤 공백은 떼지 않는다. 보내는 값이 환경의 값과 달라지면 서버가 되울린 값을 아래 가리기가 찾지
못한다.

**실패.** 호출을 감싸(`_generate`, `_agenerate`) 라이브러리를 부르기 전에 키 함수를 한 번 먼저
부르고, 호출에서 올라온 `Exception` 전부를 내장 예외(`RuntimeError`, `ConnectionError`)로 바꾼다.
문구의 갈래는 아래 넷이다. `CancelledError` 는 받지 않아
실행 기한이 그대로 듣는다. 바꾼 예외는 `except` 블록 밖에서 던져 `__cause__` 도 `__context__` 도
없다. 안에서 `from None` 으로 던지면 맨 위 글만 가려지고 `__context__` 에 원래 예외가 남아 그 글과
요청 헤더에 키가 있다(MCP 어댑터가 되울린 헤더 값을 가린 문구에 원인을 남기지 않는 것과 같은
까닭이다).

- 상태 오류: `RuntimeError("모델 서버 <주소> 가 요청을 거절했다 (HTTP <코드>): <글>")`
- 연결 오류(시간 초과 포함): `ConnectionError("모델 서버 <주소> 에 닿지 못했다: <글>")`. 원인 사슬의
  글은 싣지 않는다.
- 검증 예외: `RuntimeError("모델 서버 <주소> 의 응답을 읽지 못했다: <자리> 의 꼴이 틀렸다")`. 원래
  글은 틀린 값을 되울려 도구 호출의 인자가 실리므로 자리만 싣는다.
- 그 밖: `RuntimeError("모델 서버 <주소> 호출이 실패했다 (<원래 예외의 종류 이름>): <글>")`

`<주소>` 는 모델 파일의 `base_url` 을 글자 그대로 실은 것이고 찍히지 않는 글자만 이스케이프한다(ADR
0057 "주소는 비밀이 아닌 것으로 본다"). 사용자 정보와 쿼리가 든 주소는 읽는 단계가 거부해 여기까지
오지 않는다. `<글>` 은 원래 예외의 `str` 에서 키 값을 글자 그대로 찾아 `***` 로 바꾼 것이다. 찾는
값은 호출을 시작하며 읽어 둔 값과 예외를 바꾸는 때의 환경 값 둘이다.

모델을 만드는 자리에서 난 예외는 종류를 가리지 않고 `PluginError` 로 바꾼다. 개행이나 숫자가 아닌
포트가 든 주소가 읽는 단계를 지나 만드는 순간 `httpx2.InvalidURL` 로 거부되고, 그 글은 주소의 조각을
되울린다. 읽는 단계가 적은 값을 되울리지 않는 것과 맞춰 예외 종류의 이름만 싣는다.

**HTTP 클라이언트.** 모델을 만들 때마다 그 모델만 쓰는 비동기 클라이언트를 새로 만들어 넘기고 쉬는
연결을 두지 않는다. 손대지 않은 모델은 라이브러리가 주소별로 캐시한 클라이언트를 나눠 쓰는데, 같은
프로세스에서 이벤트 루프를 닫고 새로 연 뒤 같은 주소를 부르면 `Event loop is closed` 로 실패한다.
모델마다 준 클라이언트를 닫는 자리는 없다(core 는 모델을 만들고 놓을 뿐이고 포트에 닫기가 없다).
그래서 쉬는 연결의 수를 0 으로 두어 놓인 모델이 연결을 남기지 않게 한다. 치르는 값은 호출마다 연결을
새로 맺는 것이다.

**알려진 한계 넷.** 막는 길을 찾지 못했거나 막으면 정당한 쓰임을 잃어 두었다.

1. 모델 이름의 머리가 요청을 바꾼다. `use_responses_api=False` 로도 라이브러리가 이름을 보고 요청을
   바꾼다. 이름이 `o1-local` 처럼 `^o\\d` 에 맞으면 시스템 메시지가 `developer` 역할로 가고,
   `gpt-5-local` 처럼 `gpt-5` 로 시작하고 `chat` 이 없으면 매니페스트의 온도(1이 아닌 값)가 빠진다.
   OpenAI 모델을 중계하는 게이트웨이 뒤에서 모델 파일의 온도가 듣지 않거나 그 역할을 모르는 서버가
   요청을 거절할 수 있다.
2. 환경의 `OPENAI_ORG_ID`, `OPENAI_ORGANIZATION`, `OPENAI_PROJECT_ID`, `OPENAI_CUSTOM_HEADERS` 가
   키와 주소를 명시해도 모델 서버로 간다(두 라이브러리가 값이 없으면 환경에서 채운다). `serve` 의
   환경을 정하는 운영자의 변수이고 모델 서버의 키가 아니라 막지 않는다.
3. 서버가 키를 잘라 내거나 인코딩해 되울리면 가리지 못한다. 한 호출 안에서 환경의 값이 두 번 이상
   바뀌면 가운데 값을 놓칠 수 있다.
4. 라이브러리가 `httpcore2` 의 DEBUG 로그에 응답 헤더의 값을 찍는다. 헤더에 비밀을 싣는 서버나
   게이트웨이면 루트 로거를 DEBUG 로 켠 때 그 값이 로그에 남는다. 요청 헤더의 값과 키와 프롬프트는
   찍히지 않고(`tests/adapters/test_openai_compatible.py` 가 본다) 로그 필터는 두지 않는다.
"""

from __future__ import annotations

import os
import re
from collections.abc import Mapping
from typing import override

import httpx2
import openai
from langchain_core.callbacks import AsyncCallbackManagerForLLMRun, CallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatResult
from langchain_openai import ChatOpenAI
from pydantic import ValidationError

from agent_os.core.ports import PluginError

# 키 없이 붙는 서버에 인증 헤더로 가는 자리 채움 글자. 비밀이 아니다.
PLACEHOLDER_KEY = "no-key"
MASK = "***"
# 인증 헤더 값으로 갈 수 있는 글자. 보이는 ASCII 이고 가운데의 공백만 받는다.
_HEADER_SAFE = re.compile(r"[\x21-\x7e](?:[\x20-\x7e]*[\x21-\x7e])?")


class _KeySource:
    """모델 호출 때마다 환경에서 키를 읽는 함수 객체. `ChatOpenAI` 의 `api_key` 로 넘긴다."""

    def __init__(self, variable: str | None, env: Mapping[str, str]) -> None:
        self._variable = variable
        self._env = env

    def __call__(self) -> str:
        if self._variable is None:
            return PLACEHOLDER_KEY
        value = self._env.get(self._variable)
        if not value:
            raise RuntimeError(f"모델 서버의 키를 읽을 환경 변수 {self._variable} 가 없다")
        if _HEADER_SAFE.fullmatch(value) is None:
            raise RuntimeError(
                f"환경 변수 {self._variable} 의 값에 인증 헤더로 보낼 수 없는 글자가 있다"
            )
        return value

    def masked(self, text: str, started_with: str) -> str:
        """글에서 키 값을 글자 그대로 찾아 가린다. 값을 바꿔 되울린 것은 놓친다.

        찾는 값은 둘이다. 호출을 시작하며 읽어 둔 값(`started_with`)과 지금 환경의 값이다. 지금의
        값만 찾으면 요청이 나간 뒤 환경의 값이 바뀐 호출에서 서버가 되울린 옛 값이 글에 남는다. 호출
        도중에 값이 한 번 바뀌면 보낸 값은 그 둘 가운데 하나다. 두 번 이상 바뀌면 가운데 값을 놓칠
        수 있다.
        """
        if self._variable is None:
            return text
        for value in (started_with, self._env.get(self._variable)):
            if value:
                text = text.replace(value, MASK)
        return text


class _ModelServerChat(ChatOpenAI):
    """호출에서 나는 예외를 키 값을 가린 내장 예외로 바꾸는 `ChatOpenAI`."""

    @override
    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: object,
    ) -> ChatResult:
        key = self._key_source()
        started_with = key()
        failure: Exception
        try:
            return super()._generate(messages, stop, run_manager, **kwargs)
        except Exception as error:
            failure = _failure(error, key, started_with, self.openai_api_base)
        raise failure

    @override
    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: AsyncCallbackManagerForLLMRun | None = None,
        **kwargs: object,
    ) -> ChatResult:
        key = self._key_source()
        started_with = key()
        failure: Exception
        try:
            return await super()._agenerate(messages, stop, run_manager, **kwargs)
        except Exception as error:
            failure = _failure(error, key, started_with, self.openai_api_base)
        raise failure

    def _key_source(self) -> _KeySource:
        key = self.openai_api_key
        if not isinstance(key, _KeySource):
            raise TypeError("모델 서버 모델의 api_key 는 키를 읽는 함수여야 한다")
        return key


def _failure(
    error: Exception, key: _KeySource, started_with: str, base_url: str | None
) -> Exception:
    """라이브러리의 예외를 내장 예외로 바꾼다. 원래 예외를 원인으로 잇지 않는다."""
    address = _address(base_url)
    detail = key.masked(str(error), started_with)
    if isinstance(error, openai.APIStatusError):
        return RuntimeError(
            f"모델 서버 {address} 가 요청을 거절했다 (HTTP {error.status_code}): {detail}"
        )
    if isinstance(error, openai.APIConnectionError):
        return ConnectionError(f"모델 서버 {address} 에 닿지 못했다: {detail}")
    if isinstance(error, ValidationError):
        # 그 글은 틀린 값(`input_value`)을 되울려 도구 호출의 인자가 실린다. 자리만 싣는다.
        places = ", ".join(
            ".".join(str(part) for part in entry["loc"])
            for entry in error.errors(include_url=False, include_context=False, include_input=False)
        )
        return RuntimeError(f"모델 서버 {address} 의 응답을 읽지 못했다: {places} 의 꼴이 틀렸다")
    return RuntimeError(f"모델 서버 {address} 호출이 실패했다 ({type(error).__name__}): {detail}")


def _address(base_url: str | None) -> str:
    """예외 글에 실을 주소. 모델 파일에 적은 글자 그대로이고 찍히지 않는 글자만 이스케이프한다.

    개행이 든 주소를 그대로 실으면 글이 줄을 바꾼다. 사용자 정보와 쿼리는 떼지 않는다. 그 둘이 든
    주소는 모델 파일을 읽는 단계가 거절해 여기까지 오지 않는다(모듈 독스트링).
    """
    if base_url is None:
        return "(주소 없음)"
    return "".join(
        char if char.isprintable() else char.encode("unicode_escape").decode("ascii")
        for char in base_url
    )


def _own_client() -> httpx2.AsyncClient:
    """모델 하나가 쓰는 비동기 클라이언트. 라이브러리 기본값에서 쉬는 연결의 수만 0 으로 바꾼다."""
    limits = httpx2.Limits(max_connections=1000, max_keepalive_connections=0)
    return openai.DefaultAsyncHttpxClient(limits=limits)


def chat_openai_compatible(
    *,
    plugin_name: str,
    model_id: str,
    base_url: str,
    api_key_env: str | None,
    max_tokens: int | None,
    temperature: float | None,
    env: Mapping[str, str] | None = None,
) -> BaseChatModel:
    """모델 파일의 칸으로 모델 하나를 만든다. 키도 네트워크도 요구하지 않는다.

    `max_tokens` 와 `temperature` 는 없음을 그대로 넘긴다. 없음이면 요청 본문에 그 키가 실리지
    않는다. `env` 를 주지 않으면 이 프로세스의 환경을 부를 때마다 읽는다.
    """
    try:
        return _ModelServerChat(
            model=model_id,
            base_url=base_url,
            api_key=_KeySource(api_key_env, os.environ if env is None else env),
            http_async_client=_own_client(),
            max_completion_tokens=max_tokens,
            temperature=temperature,
            use_responses_api=False,
            disable_streaming=True,
            openai_proxy=None,
            output_version=None,
        )
    except Exception as error:
        kind = type(error).__name__
    # 라이브러리의 글은 주소의 조각을 되울려 싣지 않고, 원인으로도 잇지 않는다. `except` 밖에서
    # 던진다.
    raise PluginError(f"model 플러그인 {plugin_name} 의 base_url 로 모델을 만들 수 없다 ({kind})")
