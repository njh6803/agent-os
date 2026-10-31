"""저장소의 기본 모델 플러그인 `claude-opus-5`. 실물 플러그인 루트(`plugins/`)를 실제 파일시스템
어댑터로 읽어, 이 파일의 값을 고정한다. 코드에는 기본 모델의 이름이 없으므로(05 가 걷었다) 코드의
상수와 맞대지 않고, 이 파일이 운영자가 `--model` 로 고르는 값이 서는 자리다.

선례는 저장소의 calc 를 실제 어댑터로 읽는 `tests/test_calc_plugin.py` 다. 격리된 루트의 시험과 두
e2e 스택이 같은 이름의 모델 매니페스트를 두고 `--model claude-opus-5` 를 명시해 넘기므로, 이 파일의
내용이 그 시험들이 기대는 기준이다(`.scratch/model-plugin/spec.md` 의 "저장소의 기본 모델 플러그인과
격리 루트").
"""

from pathlib import Path

from agent_os.adapters.filesystem import FilesystemPlugins
from agent_os.core.ports import PluginSource, UnreadableManifest
from agent_os.sdk import ModelProvider, PluginKind, PluginManifest, PluginName

REPO_ROOT = Path(__file__).resolve().parents[1]
NAME = PluginName("claude-opus-5")


def _plugins() -> PluginSource:
    return FilesystemPlugins(REPO_ROOT / "plugins")


def test_저장소의_기본_모델_플러그인은_모델_매니페스트로_읽힌다() -> None:
    manifest = _plugins().read_manifest(PluginKind.MODEL, NAME)

    assert manifest is not None
    assert manifest.kind is PluginKind.MODEL
    assert manifest.name == NAME
    assert manifest.version == "0.1.0"
    assert manifest.provider is ModelProvider.ANTHROPIC
    assert manifest.model_id == "claude-opus-5"
    assert manifest.max_tokens == 16000


def test_저장소의_기본_모델_플러그인은_온도를_적지_않는다() -> None:
    """`temperature` 가 없으면 제공사 기본값이다. 지금의 동작 그대로다."""
    manifest = _plugins().read_manifest(PluginKind.MODEL, NAME)

    assert manifest is not None
    assert manifest.temperature is None
    assert "temperature" not in manifest.model_fields_set


def test_관리_목록의_모델_행으로_표지가_아니라_읽힌_매니페스트가_선다() -> None:
    rows = _plugins().list_manifests(PluginKind.MODEL)

    assert not any(isinstance(row, UnreadableManifest) for row in rows)
    named = [row for row in rows if isinstance(row, PluginManifest) and row.name == NAME]
    assert len(named) == 1
