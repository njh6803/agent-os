"""Anthropic 모델 어댑터. 어댑터는 langchain-anthropic 패키지 자체이고 여기는 조립 재료만 둔다.

API 키는 ChatAnthropic이 환경에서 스스로 읽는다. 이 모듈은 키 값을 만지지 않는다(원칙 V).
"""

from __future__ import annotations

from collections.abc import Mapping

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel

DEFAULT_MODEL = "claude-opus-5"
MODEL_ENV = "AGENT_OS_MODEL"
MAX_TOKENS = 16000


def resolve_model_name(env: Mapping[str, str], flag: str | None = None) -> str:
    """플래그, 환경변수, 기본값 순. 폴백은 없다. 빈 값은 '지정 안 함'이 아니라 잘못된 지정이다."""
    if flag is not None:
        return _non_empty(flag)
    if MODEL_ENV not in env:
        return DEFAULT_MODEL
    return _non_empty(env[MODEL_ENV])


def _non_empty(name: str) -> str:
    if not name:
        raise ValueError("모델 이름이 비어 있다. 이름을 적거나 지정을 지운다")
    return name


def anthropic_chat_model(name: str) -> BaseChatModel:
    # pyright strict는 pydantic 별칭 필드를 별칭 이름으로만 받고, Field(None, alias=...)의
    # 위치 기본값을 기본값으로 보지 않는다. 그래서 별칭으로 부르고 timeout·stop을 명시한다.
    return ChatAnthropic(model_name=name, max_tokens_to_sample=MAX_TOKENS, timeout=None, stop=None)
