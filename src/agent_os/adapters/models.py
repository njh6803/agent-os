"""모델 소스. 모델 매니페스트의 `provider` 로 갈라 제공사의 모듈에게 모델을 만들게 한다.

`ManifestModels` 가 core 의 `ModelSource` 포트를 시그니처로 만족한다(ADR 0040). 이 모듈은 제공사를
모른다. 모델이 아닌 종류의 매니페스트와 공백뿐인 `model_id` 의 거부는 가르기 전에 있어 두 제공사에
같고, 만들기는 어느 제공사도 키도 네트워크도 요구하지 않는다. 기본 모델의 이름을 정하는
`resolve_model_name` 과 `MODEL_ENV` 도 제공사와 무관해 여기 산다.

`openai-compatible` 은 모델 서버 모듈(`adapters/openai_compatible.py`)이 만든다(ADR 0057). 주소를
라이브러리가 받지 않아 모델을 만들지 못하면 실행 전 구성 오류(`PluginError`)이고, 실행은
`run_started` 전에 끝나 트레이스가 남지 않는다.

`check` 는 접속 확인이다(ADR 0067). 제공사로 갈라 `adapters/model_check.py` 의 함수에 넘기고, 요청의
종류와 갈래와 기한은 그 모듈이 적는다. 기한은 이 소스를 만들 때 받는다.
"""

from __future__ import annotations

from collections.abc import Mapping

from langchain_core.language_models import BaseChatModel

from agent_os.adapters.anthropic import chat_anthropic
from agent_os.adapters.model_check import (
    CHECK_DEADLINE_SECONDS,
    check_anthropic,
    check_openai_compatible,
)
from agent_os.adapters.openai_compatible import chat_openai_compatible
from agent_os.core.ports import CheckOutcome, PluginError
from agent_os.sdk import ModelProvider, PluginManifest

MODEL_ENV = "AGENT_OS_MODEL"


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


def _provider_and_id(manifest: PluginManifest) -> tuple[ModelProvider, str]:
    """모델 매니페스트의 `provider` 와 `model_id`. 모델 종류가 아니거나 `model_id` 가 공백뿐이면
    구성 오류다. 만들기와 접속 확인이 같은 거름을 지난다."""
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
    return provider, model_id


def _base_url(manifest: PluginManifest) -> str:
    # 모델 종류에서 `base_url` 이 있음을 sdk 의 검증자가 보장한다. 위 두 칸과 같은 까닭으로
    # pyright strict 가 이 좁힘을 요구한다.
    if manifest.base_url is None:
        raise PluginError(f"{manifest.name} 은 base_url 이 없어 모델 서버에 붙을 수 없다")
    return manifest.base_url


class ManifestModels:
    """모델 매니페스트로 모델을 만들고 서버에 붙는지 확인한다. 부를 때마다 새 객체를 돌려준다.

    접속 확인의 기한(초)은 만들 때 주는 값이고 기본이 10초다(ADR 0067). 시험은 짧은 기한을 준다.
    """

    def __init__(self, check_deadline_seconds: float = CHECK_DEADLINE_SECONDS) -> None:
        self._check_deadline_seconds = check_deadline_seconds

    def build(self, manifest: PluginManifest) -> BaseChatModel:
        provider, model_id = _provider_and_id(manifest)
        match provider:
            case ModelProvider.ANTHROPIC:
                return chat_anthropic(model_id, manifest.max_tokens, manifest.temperature)
            case ModelProvider.OPENAI_COMPATIBLE:
                return chat_openai_compatible(
                    plugin_name=manifest.name,
                    model_id=model_id,
                    base_url=_base_url(manifest),
                    api_key_env=manifest.api_key_env,
                    max_tokens=manifest.max_tokens,
                    temperature=manifest.temperature,
                )

    async def check(self, manifest: PluginManifest) -> CheckOutcome:
        """모델 서버의 접속 확인(ADR 0067). 제공사마다 다른 요청 한 건으로 붙어 본다.

        구성 오류(모델이 아닌 종류, 공백뿐인 `model_id`)는 만들 때와 같은 `PluginError` 로 올린다.
        붙지 못한 것은 예외가 아니라 `Unreached` 다. 요청과 갈래는 `adapters/model_check.py`.
        """
        provider, model_id = _provider_and_id(manifest)
        match provider:
            case ModelProvider.ANTHROPIC:
                return await check_anthropic(manifest, model_id, self._check_deadline_seconds)
            case ModelProvider.OPENAI_COMPATIBLE:
                return await check_openai_compatible(
                    manifest, model_id, _base_url(manifest), self._check_deadline_seconds
                )
