"""Anthropic 모듈이 `ChatAnthropic` 을 만드는 것. 제공사로 가르는 것은 `test_models.py` 가 본다."""

from langchain_anthropic import ChatAnthropic

from agent_os.adapters.anthropic import MAX_TOKENS, chat_anthropic


def _build(max_tokens: int | None = None, temperature: float | None = None) -> ChatAnthropic:
    model = chat_anthropic("claude-haiku-4-5", max_tokens, temperature)
    assert isinstance(model, ChatAnthropic)
    return model


def test_모델_id_가_모델에_닿는다() -> None:
    assert _build().model == "claude-haiku-4-5"


def test_max_tokens_를_적지_않으면_어댑터의_기본값이_닿는다() -> None:
    assert _build().max_tokens == MAX_TOKENS


def test_max_tokens_를_적으면_그_값이_닿는다() -> None:
    assert _build(max_tokens=2048).max_tokens == 2048


def test_temperature_를_적지_않으면_제공사의_기본값에_맡긴다() -> None:
    assert _build().temperature is None


def test_temperature_를_적으면_그_값이_닿는다() -> None:
    assert _build(temperature=0.25).temperature == 0.25
