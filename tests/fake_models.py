"""모델 소스 포트의 가짜와 모델 매니페스트 도우미. 시험 파일들이 나눠 쓴다.

가짜는 포트를 상속하지 않고 시그니처로 만족한다. 시험 쪽은 `models: ModelSource = FakeModels(…)`
처럼 포트 타입으로 annotate해서 적합성을 검증한다(`.claude/rules/tests.md`).
"""

from __future__ import annotations

from collections.abc import Mapping

from agent_os.core.ports import ChatModel, PluginError
from agent_os.sdk import PluginManifest, PluginName, parse_manifest

# 시험 도우미가 `default_model` 로 넘기는 이름. 가짜 플러그인 포트가 이 이름의 모델 매니페스트를
# 들고 있다.
DEFAULT_MODEL = PluginName("default-model")


def model_manifest(name: str, max_tokens: int | None = None) -> PluginManifest:
    """모델 매니페스트. `model_id` 는 `<이름>-id` 라 어느 매니페스트로 만들었는지 갈린다."""
    tokens = "" if max_tokens is None else f"max_tokens = {max_tokens}\n"
    return parse_manifest(
        f'schema_version = "1"\nkind = "model"\nname = "{name}"\nversion = "0.1.0"\n'
        f'provider = "anthropic"\nmodel_id = "{name}-id"\n' + tokens
    )


class FakeModels:
    """모델 매니페스트로 모델을 만드는 가짜. 만든 매니페스트를 `built` 에 쌓는다.

    매니페스트의 이름이 `by_name` 에 있으면 그 모델을, 없으면 `default` 를 돌려준다. 매니페스트마다
    다른 모델을 돌려줘서 에이전트가 고른 모델 쪽이 쓰였는지 본다. `failure` 가 있으면 어댑터가
    만들지 못한 모양으로 PluginError 다.
    """

    def __init__(
        self,
        default: ChatModel,
        by_name: Mapping[str, ChatModel] | None = None,
        failure: str | None = None,
    ) -> None:
        self._default = default
        self._by_name = dict(by_name or {})
        self.failure = failure
        self.built: list[PluginManifest] = []

    def build(self, manifest: PluginManifest) -> ChatModel:
        self.built.append(manifest)
        if self.failure is not None:
            raise PluginError(self.failure)
        return self._by_name.get(manifest.name, self._default)
