"""Anthropic 모델 어댑터. 어댑터는 langchain-anthropic 패키지 자체이고 여기는 조립 재료만 둔다.

`AnthropicModels` 가 core 의 `ModelSource` 포트를 시그니처로 만족한다(ADR 0040). 모델 매니페스트
(`provider`, `model_id`, `max_tokens`, `temperature`)로 `ChatAnthropic` 하나를 만들고, 실행마다 새로
만든다. 만들기는 키도 네트워크도 요구하지 않는다.

API 키는 ChatAnthropic이 환경에서 스스로 읽는다. 이 모듈은 키 값을 만지지 않는다(원칙 V). 키가 없는
것은 만들 때가 아니라 첫 호출에서 드러난다.
"""

from __future__ import annotations

from collections.abc import Mapping

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel

from agent_os.core.ports import PluginError
from agent_os.sdk import ModelProvider, PluginManifest

MODEL_ENV = "AGENT_OS_MODEL"
MAX_TOKENS = 16000


def resolve_model_name(env: Mapping[str, str], flag: str | None = None) -> str:
    """기본 모델의 이름. 플래그, 환경변수 순이고 코드의 기본값도 폴백도 없다.

    둘 다 없으면 구성 오류(`ValueError`)다. 운영자가 고르지 않은 모델로 몰래 도는 서버를 만들지
    않기 위해서다(ADR 0040). 빈 값은 '지정 안 함'이 아니라 잘못된 지정이다.
    """
    if flag is not None:
        return _non_empty(flag)
    if MODEL_ENV not in env:
        raise ValueError(
            "기본 모델의 이름이 없다. 코드에 기본값은 없고 운영자가 고른다.\n"
            f"  --model 이나 환경변수 {MODEL_ENV} 로 plugins/models/<이름>/plugin.toml 의 이름을"
            " 넘긴다."
        )
    return _non_empty(env[MODEL_ENV])


def _non_empty(name: str) -> str:
    if not name:
        raise ValueError("모델 이름이 비어 있다. 이름을 적거나 지정을 지운다")
    return name


class AnthropicModels:
    """모델 매니페스트로 `ChatAnthropic` 을 만든다. 상태가 없고 부를 때마다 새 객체를 돌려준다."""

    def build(self, manifest: PluginManifest) -> BaseChatModel:
        provider = manifest.provider
        model_id = manifest.model_id
        # 모델이 아닌 종류의 매니페스트는 두 칸이 없다. 칸의 타입이 선택이라 pyright strict 가 이
        # 좁힘을 요구한다. 선례는 `entrypoint` 없는 매니페스트를 거부하는 `load_agent` 다. 이
        # 아래에서 다시 좁히지 않는다 — sdk 의 검증자가 모델 종류에서 둘이 함께 있음을 보장한다.
        if provider is None or model_id is None:
            raise PluginError(f"{manifest.name} 은 provider 와 model_id 가 없어 모델이 아니다")
        # 공백만 있는 id 는 sdk 가 받는다(비지 않은 문자열만 요구한다). 제공사가 거부하게 두면 그
        # 모델을 쓰는 모든 실행이 첫 호출에서 `model_call` 실패로 드러나므로 실행 전 구성 오류로
        # 막는다.
        if not model_id.strip():
            raise PluginError(f"model 플러그인 {manifest.name} 의 model_id 가 공백뿐이다")
        match provider:
            case ModelProvider.ANTHROPIC:
                return _chat_anthropic(model_id, manifest.max_tokens, manifest.temperature)


def _chat_anthropic(
    model_id: str, max_tokens: int | None, temperature: float | None
) -> BaseChatModel:
    # pyright strict는 pydantic 별칭 필드를 별칭 이름으로만 받고, Field(None, alias=...)의
    # 위치 기본값을 기본값으로 보지 않는다. 그래서 별칭으로 부르고 timeout·stop을 명시한다.
    tokens = MAX_TOKENS if max_tokens is None else max_tokens
    if temperature is None:
        return ChatAnthropic(
            model_name=model_id, max_tokens_to_sample=tokens, timeout=None, stop=None
        )
    return ChatAnthropic(
        model_name=model_id,
        max_tokens_to_sample=tokens,
        temperature=temperature,
        timeout=None,
        stop=None,
    )
