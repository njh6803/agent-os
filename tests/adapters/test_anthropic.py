"""모델 이름 결정. 플래그, 환경변수, 기본값 순이고 폴백은 없다."""

import pytest

from agent_os.adapters.anthropic import DEFAULT_MODEL, MODEL_ENV, resolve_model_name


def test_환경변수가_없으면_기본_모델이다() -> None:
    assert resolve_model_name({}) == DEFAULT_MODEL


def test_환경변수가_있으면_그_모델이다() -> None:
    assert resolve_model_name({MODEL_ENV: "claude-haiku-4-5"}) == "claude-haiku-4-5"


def test_플래그가_환경변수보다_앞선다() -> None:
    assert resolve_model_name({MODEL_ENV: "from-env"}, flag="from-flag") == "from-flag"


def test_빈_지정은_기본값으로_넘어가지_않고_거부한다() -> None:
    """빈 문자열은 '지정 안 함'이 아니라 잘못된 지정이다. 몰래 기본값으로 넘어가지 않는다."""
    with pytest.raises(ValueError, match=MODEL_ENV):
        resolve_model_name({MODEL_ENV: ""})
    with pytest.raises(ValueError, match="--model"):
        resolve_model_name({}, flag="")
