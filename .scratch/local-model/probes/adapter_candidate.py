"""후보 어댑터. `ChatOpenAI`를 상속해 호출 둘(`_generate`, `_agenerate`)을 감싼다(측정이 아니다).

`openai_compat.py`의 `guard_candidate_*` 사례가 이 모듈을 루프와 같은 길(`bind_tools` 뒤
`ainvoke`)로 부르고, `check_adapter_types.py`가 저장소의 pyright strict 설정과 타입 우회 판정자로
검사한다. 구현 티켓의 어댑터는 이 파일을 옮기는 것이 아니라 여기서 본 모양을 근거로 새로 짓는다.

core 는 어댑터가 만든 모델 객체에 `bind_tools`와 `ainvoke`를 바로 부르고 예외는 그 객체에서 core 로
올라온다(`core/loop.py`의 `model_caller`). 그래서 어댑터가 설 수 있는 자리는 모델 객체 안이다.

- 키 변수가 없으면 요청을 만들기 전에 변수 이름만 든 내장 예외로 끝난다(`KeySource.__call__`).
- 인증 헤더에 실을 수 없는 키 값(개행, 비ASCII)도 같은 자리에서 값 없이 끝난다. 라이브러리에 넘기면
  예외의 글이나 원인에 값이 실린다(`openai_compat.py`의 `bad_key_*` 사례).
- 호출에서 올라온 예외는 종류를 가리지 않고 받아, 글에서 키 값을 가린 내장 예외로 바꾼다. 가리는
  값은 호출을 시작하며 읽어 둔 값과 예외를 바꾸는 때의 환경 값 둘이다(`KeySource.masked`. 호출
  도중에 환경의 값이 바뀐 갈래는 이 프로브가 재지 않았다). `openai.OpenAIError`만 받으면 200 응답의
  `error` 칸이 내는 `ValueError`가 그대로 지나간다(같은 프로브의 `ok_status_error_body` 사례).
- pydantic 의 검증 예외(도구 호출의 인자가 JSON 이지만 객체가 아니거나, 글이 아닌 객체로 왔다)는
  글을 싣지 않고 틀린 자리만 싣는다. 그 글이 받은 인자를 되울린다(같은 프로브의
  `guard_candidate_args_*` 사례).
- 바꾼 예외는 `except` 밖에서 던진다. 안에서 `from None`으로 던지면 `__context__`에 원래 예외가
  남는다(같은 프로브의 `guard_first_plan_401` 사례).
- 바꾼 예외의 글에는 모델 파일에 적은 주소를 글자 그대로 싣고 제어 문자만 이스케이프한다
  (`_address`. ADR 0057 결정 "주소는 비밀이 아닌 것으로 본다"와 MCP 어댑터의 `_where`가 같은
  방식이다). 사용자 정보와 쿼리를 떼지 않으므로 그 둘이 든 주소가 여기까지 오면 글에 그대로
  실린다. 사용자 정보가 있으면 키 대신 Basic 인증이 가고, 서버가 그것을 되울린 글도 가리지
  못한다(같은 프로브의 `guard_candidate_userinfo_401` 사례). 가리는 것은 키 값뿐이다. 그래서
  사용자 정보와 쿼리가 든 주소는 모델 파일을 읽는 단계가 거절해야 한다.
- 취소(`CancelledError`)는 `Exception`이 아니라 받지 않는다. 실행 타임아웃이 그대로 듣는다(같은
  프로브의 `guard_candidate_cancelled` 사례).

모델마다 제 비동기 HTTP 클라이언트를 주고, 그 클라이언트는 쉬는 연결을 두지 않는다(`_own_client`).
라이브러리가 주소별로 캐시해 나눠 쓰는 클라이언트는 한 프로세스의 둘째 이벤트 루프에서 같은 주소를
부르면 실패한다(같은 프로브의 `two_loops_same_url`·`two_loops_own_client` 사례). 모델마다 준
클라이언트를 닫는 자리는 없다. 기본값 클라이언트(쉬는 연결을 남긴다)를 주면 한 루프에서 놓인 모델의
연결이 닫히지 않고 쌓인다(같은 프로브의 `runs_in_one_loop` 사례). 그래서 응답을 다 읽은 연결을
그 자리에서 닫게 한다. 대가로 호출마다 연결을 새로 맺는다.

`disable_streaming=True`로 만들어 `astream`도 `_agenerate`를 지나게 한다(같은 프로브의 `guard_paths`
사례). 끄지 않으면 `astream`은 `_astream`으로 가서 이 두 메서드를 비켜 간다(같은 프로브의
`guard_stream_bypass_control` 사례). 스트리밍 콜백이 붙은 `ainvoke`도 같은 길이라는 것은
langchain-core 1.6.3 의 `_agenerate_with_cache`를 읽은 것이고 재지 않았다.
"""

from __future__ import annotations

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

# 키 없이 붙는 서버에 인증 헤더로 가는 자리 채움 글자. 비밀이 아니다.
PLACEHOLDER_KEY = "no-key"
MASK = "***"
# 인증 헤더 값으로 갈 수 있는 글자. 보이는 ASCII 이고 가운데의 공백만 받는다.
_HEADER_SAFE = re.compile(r"[\x21-\x7e](?:[\x20-\x7e]*[\x21-\x7e])?")


class KeySource:
    """모델 호출 때마다 환경에서 키를 읽는 함수 객체. `ChatOpenAI`의 `api_key`로 넘긴다."""

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
        값만 찾으면, 요청이 나간 뒤 환경의 값이 바뀐 호출에서 서버가 되울린 옛 값이 글에 남는다.
        호출 도중에 값이 한 번 바뀌면 보낸 값은 그 둘 가운데 하나다. 두 번 이상 바뀌면 가운데 값을
        놓칠 수 있다.
        """
        if self._variable is None:
            return text
        for value in (started_with, self._env.get(self._variable)):
            if value:
                text = text.replace(value, MASK)
        return text


class GuardedChatOpenAI(ChatOpenAI):
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

    def _key_source(self) -> KeySource:
        key = self.openai_api_key
        if not isinstance(key, KeySource):
            raise TypeError("GuardedChatOpenAI 의 api_key 는 KeySource 여야 한다")
        return key


def _failure(
    error: Exception, key: KeySource, started_with: str, base_url: str | None
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
    """예외 글에 실을 주소. 모델 파일에 적은 글자 그대로이고 제어 문자만 이스케이프한다.

    개행이 든 주소를 그대로 실으면 글이 줄을 바꾼다. 사용자 정보와 쿼리는 떼지 않는다. 그 둘이 든
    주소는 모델 파일을 읽는 단계가 거절해야 한다(모듈 독스트링).
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


def build_chat_model(
    *,
    model_id: str,
    base_url: str,
    api_key_env: str | None,
    max_tokens: int | None,
    temperature: float | None,
    env: Mapping[str, str],
    http_async_client: httpx2.AsyncClient | None = None,
) -> BaseChatModel:
    """모델 파일의 칸으로 모델 하나를 만든다. 키도 네트워크도 요구하지 않는다.

    주소가 라이브러리가 받지 않는 꼴(제어 문자, 숫자가 아닌 포트, 너무 긴 주소)이면 만드는 순간
    `httpx2.InvalidURL`이 올라온다(같은 프로브의 `build_rejects_address` 사례). 이 후보는 그 예외를
    바꾸지 않는다. 무엇으로 바꿀지는 명세가 어댑터 모듈의 몫으로 정한다.

    `max_completion_tokens`와 `temperature`는 없음을 그대로 넘긴다. 없음이면 요청 본문에 그 키가
    실리지 않는다. `openai_proxy`와 `output_version`을 없음으로 못박는 것은 환경의 `OPENAI_PROXY`와
    `LC_OUTPUT_VERSION`이 그 기본값을 채우지 못하게 하려는 것이다. `http_async_client`는 모델마다
    새로 만든다(모듈 독스트링). 그 인자는 견줄 갈래를 재는 사례(`cases_lifetime.py`)만 준다.
    """
    return GuardedChatOpenAI(
        model=model_id,
        base_url=base_url,
        api_key=KeySource(api_key_env, env),
        http_async_client=http_async_client or _own_client(),
        max_completion_tokens=max_tokens,
        temperature=temperature,
        use_responses_api=False,
        disable_streaming=True,
        openai_proxy=None,
        output_version=None,
    )
