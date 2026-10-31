"""모델 이름 결정(플래그, 환경변수, 기본값 순이고 폴백은 없다)과 모델 소스 어댑터."""

import pytest
from langchain_anthropic import ChatAnthropic

from agent_os.adapters.anthropic import (
    DEFAULT_MODEL,
    MAX_TOKENS,
    MODEL_ENV,
    AnthropicModels,
    resolve_model_name,
)
from agent_os.core.ports import ModelSource, PluginError
from agent_os.sdk import PluginManifest, parse_manifest


def test_환경변수가_없으면_기본_모델이다() -> None:
    assert resolve_model_name({}) == DEFAULT_MODEL


def test_환경변수가_있으면_그_모델이다() -> None:
    assert resolve_model_name({MODEL_ENV: "claude-haiku-4-5"}) == "claude-haiku-4-5"


def test_플래그가_환경변수보다_앞선다() -> None:
    assert resolve_model_name({MODEL_ENV: "from-env"}, flag="from-flag") == "from-flag"


def test_빈_지정은_기본값으로_넘어가지_않고_거부한다() -> None:
    """빈 문자열은 '지정 안 함'이 아니라 잘못된 지정이다. 몰래 기본값으로 넘어가지 않는다."""
    with pytest.raises(ValueError, match="모델 이름"):
        resolve_model_name({MODEL_ENV: ""})
    with pytest.raises(ValueError, match="모델 이름"):
        resolve_model_name({}, flag="")


def _model_manifest(extra: str = "", model_id: str = "claude-haiku-4-5") -> PluginManifest:
    """플러그인 이름(`haiku`)과 `model_id` 가 다른 모델 매니페스트."""
    return parse_manifest(
        'schema_version = "1"\nkind = "model"\nname = "haiku"\nversion = "0.1.0"\n'
        f'provider = "anthropic"\nmodel_id = "{model_id}"\n' + extra
    )


def _build(manifest: PluginManifest) -> ChatAnthropic:
    models: ModelSource = AnthropicModels()
    model = models.build(manifest)
    assert isinstance(model, ChatAnthropic)
    return model


def test_모델_id_가_플러그인_이름과_달라도_model_id_가_모델에_닿는다() -> None:
    model = _build(_model_manifest())

    assert model.model == "claude-haiku-4-5"


def test_max_tokens_를_적지_않으면_어댑터의_기본값이_닿는다() -> None:
    assert _build(_model_manifest()).max_tokens == MAX_TOKENS


def test_max_tokens_를_적으면_그_값이_닿는다() -> None:
    assert _build(_model_manifest("max_tokens = 2048\n")).max_tokens == 2048


def test_temperature_를_적지_않으면_제공사의_기본값에_맡긴다() -> None:
    assert _build(_model_manifest()).temperature is None


def test_temperature_를_적으면_그_값이_닿는다() -> None:
    assert _build(_model_manifest("temperature = 0.25\n")).temperature == 0.25


def test_부를_때마다_새_모델을_만든다() -> None:
    models: ModelSource = AnthropicModels()
    manifest = _model_manifest()

    assert models.build(manifest) is not models.build(manifest)


def test_만들기는_키가_없어도_실패하지_않는다() -> None:
    """키가 없는 것은 만들 때가 아니라 첫 호출에서 드러난다(프로브 build_without_key.py)."""
    models: ModelSource = AnthropicModels()

    assert isinstance(models.build(_model_manifest()), ChatAnthropic)


def test_모델이_아닌_매니페스트는_구성_오류다() -> None:
    agent = parse_manifest(
        'schema_version = "1"\nkind = "agent"\nname = "calc"\nversion = "0.1.0"\n'
        'entrypoint = "agent:Agent"\n'
    )
    models: ModelSource = AnthropicModels()

    with pytest.raises(PluginError, match="calc 은 provider 와 model_id 가 없어 모델이 아니다"):
        models.build(agent)


# 값은 TOML 문자열 안에 그대로 들어간다. 개행은 실제 줄바꿈이 아니라 TOML 이스케이프로 준다.
@pytest.mark.parametrize("model_id", [" ", "\t", r" \n "], ids=["공백", "탭", "공백과 개행"])
def test_공백만_있는_model_id_는_실행_전_구성_오류다(model_id: str) -> None:
    models: ModelSource = AnthropicModels()

    with pytest.raises(PluginError, match="model 플러그인 haiku 의 model_id 가 공백뿐이다"):
        models.build(_model_manifest(model_id=model_id))
