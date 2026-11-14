"""Anthropic 모델. 어댑터는 langchain-anthropic 패키지 자체이고 여기는 조립 재료만 둔다.

`chat_anthropic` 이 모델 매니페스트의 칸(`model_id`, `max_tokens`, `temperature`)으로
`ChatAnthropic` 하나를 만든다. 제공사로 가르는 것은 모델 소스(`adapters/models.py`)의 몫이고,
만들기는 키도 네트워크도 요구하지 않는다(ADR 0040).

API 키는 ChatAnthropic이 환경에서 스스로 읽는다. 이 모듈은 키 값을 만지지 않는다(원칙 V). 키가 없는
것은 만들 때가 아니라 첫 호출에서 드러난다.
"""

from __future__ import annotations

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models import BaseChatModel

MAX_TOKENS = 16000


def chat_anthropic(
    model_id: str, max_tokens: int | None, temperature: float | None
) -> BaseChatModel:
    """`max_tokens` 가 없으면 `MAX_TOKENS` 를, `temperature` 가 없으면 제공사 기본값을 쓴다."""
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
