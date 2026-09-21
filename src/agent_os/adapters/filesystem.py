"""파일시스템 PluginSource. 진실의 원천은 디렉터리와 매니페스트다(ADR 0003).

`<root>/<kind 디렉터리>/<name>/plugin.toml`. 부재는 None, 파싱·import 실패는 PluginError.
진입점은 플러그인 디렉터리 기준 파일이며 고유 모듈명 `agent_os_plugins.<name>.<module>`로 로드한다.
sys.path 를 건드리지 않는다.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from pydantic import ValidationError

from agent_os.core.ports import PluginError
from agent_os.sdk import BaseAgent, PluginKind, PluginManifest, PluginName, parse_manifest

_DIRECTORY = {
    PluginKind.AGENT: "agents",
    PluginKind.MCP: "mcp",
    PluginKind.SKILL: "skills",
    PluginKind.MODEL: "models",
}
_MANIFEST = "plugin.toml"


class FilesystemPlugins:
    def __init__(self, root: Path) -> None:
        self._root = root

    def read_manifest(self, kind: PluginKind, name: PluginName) -> PluginManifest | None:
        path = self._root / _DIRECTORY[kind] / name / _MANIFEST
        if not path.is_file():
            return None
        manifest = _parse(path)
        if manifest.kind is not kind:
            raise PluginError(
                f"디렉터리와 kind가 어긋난다: {path} 는 {kind} 자리인데 {manifest.kind}"
            )
        if manifest.name != name:
            raise PluginError(
                f"디렉터리와 name이 어긋난다: {path} 는 {name} 자리인데 {manifest.name}"
            )
        return manifest

    def load_agent(self, manifest: PluginManifest) -> BaseAgent:
        if manifest.entrypoint is None:
            raise PluginError(f"{manifest.name} 은 entrypoint 가 없어 에이전트가 아니다")
        module_path, attr = manifest.entrypoint.split(":")
        directory = self._root / _DIRECTORY[PluginKind.AGENT] / manifest.name
        module = _import(directory, manifest.name, module_path)
        agent = getattr(module, attr, None)
        if agent is None:
            raise PluginError(f"진입점 {manifest.entrypoint} 에 {attr} 이 없다 ({directory})")
        instance = agent()
        if not callable(getattr(instance, "run", None)):
            raise PluginError(f"{manifest.entrypoint} 은 run() 이 없어 에이전트가 아니다")
        return instance


def _parse(path: Path) -> PluginManifest:
    try:
        return parse_manifest(path.read_text(encoding="utf-8"))
    except (ValidationError, ValueError) as error:
        raise PluginError(f"매니페스트를 읽을 수 없다: {path}\n{error}") from error


def _import(directory: Path, name: PluginName, module_path: str) -> object:
    file = directory.joinpath(*module_path.split(".")).with_suffix(".py")
    module_name = f"agent_os_plugins.{name}.{module_path}"
    spec = importlib.util.spec_from_file_location(module_name, file)
    if spec is None or spec.loader is None:
        raise PluginError(f"진입점 파일이 없다: {file}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception as error:
        del sys.modules[module_name]
        raise PluginError(f"진입점을 import할 수 없다: {file}\n{error}") from error
    return module
