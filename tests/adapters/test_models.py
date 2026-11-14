"""모델 이름 결정(플래그, 환경변수 순, 기본값도 폴백도 없다)과 제공사로 갈라 만드는 모델 소스."""

import pytest
from langchain_anthropic import ChatAnthropic

from agent_os.adapters.models import MODEL_ENV, ManifestModels, resolve_model_name
from agent_os.core.ports import ModelSource, PluginError
from agent_os.sdk import PluginManifest, parse_manifest


def test_플래그도_환경변수도_없으면_이름을_넘기는_두_길을_든_구성_오류다() -> None:
    """코드의 기본 모델은 없다. 운영자가 고르지 않은 것을 몰래 채우지 않는다."""
    with pytest.raises(ValueError) as error:
        resolve_model_name({})

    assert "--model" in str(error.value)
    assert MODEL_ENV in str(error.value)


def test_환경변수가_있으면_그_모델이다() -> None:
    assert resolve_model_name({MODEL_ENV: "claude-haiku-4-5"}) == "claude-haiku-4-5"


def test_플래그가_환경변수보다_앞선다() -> None:
    assert resolve_model_name({MODEL_ENV: "from-env"}, flag="from-flag") == "from-flag"


def test_빈_지정은_없는_것으로_넘어가지_않고_거부한다() -> None:
    """빈 문자열은 '지정 안 함'이 아니라 잘못된 지정이다. 다음 순서로 넘어가지 않는다."""
    with pytest.raises(ValueError, match="모델 이름"):
        resolve_model_name({MODEL_ENV: ""})
    with pytest.raises(ValueError, match="모델 이름"):
        resolve_model_name({}, flag="")


def _anthropic(model_id: str = "claude-haiku-4-5", extra: str = "") -> PluginManifest:
    """플러그인 이름(`haiku`)과 `model_id` 가 다른 anthropic 모델 매니페스트."""
    return parse_manifest(
        'schema_version = "1"\nkind = "model"\nname = "haiku"\nversion = "0.1.0"\n'
        f'provider = "anthropic"\nmodel_id = "{model_id}"\n' + extra
    )


def _openai_compatible(model_id: str = "skt/A.X-4.0-Light") -> PluginManifest:
    return parse_manifest(
        'schema_version = "1"\nkind = "model"\nname = "ax-4-light"\nversion = "0.1.0"\n'
        f'provider = "openai-compatible"\nmodel_id = "{model_id}"\n'
        'base_url = "http://model-server:8000/v1"\n'
    )


def test_anthropic_은_ChatAnthropic_을_만들고_model_id_가_모델에_닿는다() -> None:
    models: ModelSource = ManifestModels()

    model = models.build(_anthropic())

    assert isinstance(model, ChatAnthropic)
    assert model.model == "claude-haiku-4-5"


def test_매니페스트의_max_tokens_와_temperature_가_모델에_닿는다() -> None:
    """두 칸이 `chat_anthropic` 의 제 자리 인자로 넘어가는지 모델 소스를 지나 본다. 값이 서로 달라야
    인자 순서가 바뀐 변이가 잡힌다."""
    models: ModelSource = ManifestModels()

    model = models.build(_anthropic(extra="max_tokens = 2048\ntemperature = 0.25\n"))

    assert isinstance(model, ChatAnthropic)
    assert model.max_tokens == 2048
    assert model.temperature == 0.25


def test_부를_때마다_새_모델을_만든다() -> None:
    models: ModelSource = ManifestModels()
    manifest = _anthropic()

    assert models.build(manifest) is not models.build(manifest)


def test_만들기는_키가_없어도_실패하지_않는다() -> None:
    """키가 없는 것은 만들 때가 아니라 첫 호출에서 드러난다(프로브 build_without_key.py)."""
    models: ModelSource = ManifestModels()

    assert isinstance(models.build(_anthropic()), ChatAnthropic)


def test_모델이_아닌_매니페스트는_구성_오류다() -> None:
    agent = parse_manifest(
        'schema_version = "1"\nkind = "agent"\nname = "calc"\nversion = "0.1.0"\n'
        'entrypoint = "agent:Agent"\n'
    )
    models: ModelSource = ManifestModels()

    with pytest.raises(PluginError, match="calc 은 provider 와 model_id 가 없어 모델이 아니다"):
        models.build(agent)


# 값은 TOML 문자열 안에 그대로 들어간다. 개행은 실제 줄바꿈이 아니라 TOML 이스케이프로 준다.
@pytest.mark.parametrize("model_id", [" ", "\t", r" \n "], ids=["공백", "탭", "공백과 개행"])
@pytest.mark.parametrize("provider", ["anthropic", "openai-compatible"])
def test_공백만_있는_model_id_는_제공사를_가르기_전에_실행_전_구성_오류다(
    provider: str, model_id: str
) -> None:
    models: ModelSource = ManifestModels()
    manifest = _anthropic(model_id) if provider == "anthropic" else _openai_compatible(model_id)

    with pytest.raises(PluginError, match="model 플러그인 .+ 의 model_id 가 공백뿐이다"):
        models.build(manifest)


def test_openai_compatible_은_붙는_어댑터가_아직_없다는_실행_전_구성_오류다() -> None:
    """계약 티켓만 병합된 개발 브랜치의 임시 갈래다. pyright 는 갈래가 있는지만 보고 무엇을
    던지는지는 보지 않아 이 시험이 그 자리를 덮는다. 어댑터 티켓이 이 시험과 문구를 지운다."""
    models: ModelSource = ManifestModels()

    with pytest.raises(PluginError) as error:
        models.build(_openai_compatible())

    assert str(error.value) == (
        "model 플러그인 ax-4-light 의 provider openai-compatible 에 붙는 어댑터가 아직 없다"
    )
