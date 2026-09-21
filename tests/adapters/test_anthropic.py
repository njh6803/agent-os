"""모델 이름 결정. 환경변수, 기본값 순이고 폴백은 없다."""

from agent_os.adapters.anthropic import DEFAULT_MODEL, MODEL_ENV, resolve_model_name


def test_환경변수가_없으면_기본_모델이다() -> None:
    assert resolve_model_name({}) == DEFAULT_MODEL


def test_환경변수가_있으면_그_모델이다() -> None:
    assert (
        resolve_model_name({MODEL_ENV: "claude-haiku-4-5-20251001"}) == "claude-haiku-4-5-20251001"
    )


def test_환경변수가_비어_있으면_기본값으로_보지_않고_그대로_거부한다() -> None:
    """빈 문자열은 '지정 안 함'이 아니라 잘못된 지정이다. 몰래 기본값으로 넘어가지 않는다."""
    import pytest

    with pytest.raises(ValueError):
        resolve_model_name({MODEL_ENV: ""})
