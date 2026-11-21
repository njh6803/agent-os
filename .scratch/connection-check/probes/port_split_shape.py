"""접속 확인을 더한 두 포트와, 관리 쪽이 그 가운데 일부만 받는 모양(후보).

`check_port_split.py`가 이 파일을 저장소 밖 폴더에 복사해 pyright strict로 본다. 여기의 줄은 모두
깨끗해야 하고, 걸려야 하는 줄은 그 러너의 `CONTROL_TAIL`이 이 글 뒤에 붙인다. 구현이 아니라
모양이다. 이름과 시그니처는 `.scratch/connection-check/spec.md`의 "포트와 층"이 정한 것을 옮겼다.

재는 것은 ADR 0067 결정 "포트와 층"이 재지 않은 구상으로 남긴 둘이다. 관리 쪽에 포트 전체가 아니라
접속 확인 메서드만 넘길 수 있는가(`connect`는 넘기지 않는다). 그리고 화면이 스스로 하는 확인의 길이
원격 MCP 서버와 모델만 받게 하면 stdio MCP 서버를 넘기는 코드가 타입 검사에 걸리는가.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from typing import Protocol

from agent_os.core.ports import ChatModel, PluginSource, ToolConnection
from agent_os.sdk import (
    HttpServer,
    McpServer,
    PluginKind,
    PluginManifest,
    PluginName,
    StdioServer,
)


@dataclass(frozen=True)
class Reached:
    """붙었다."""


@dataclass(frozen=True)
class Unreached:
    """붙지 못했다. 까닭의 글을 든다."""

    reason: str


type CheckOutcome = Reached | Unreached


class ToolSource(Protocol):
    """지금의 도구 포트에 접속 확인 둘을 더한 모양."""

    def connect(
        self, servers: Mapping[PluginName, McpServer]
    ) -> AbstractAsyncContextManager[ToolConnection]: ...

    async def check_remote(self, name: PluginName, server: HttpServer) -> CheckOutcome: ...

    async def check_stdio(self, name: PluginName, server: StdioServer) -> CheckOutcome: ...


class ModelSource(Protocol):
    """지금의 모델 포트에 접속 확인 하나를 더한 모양."""

    def build(self, manifest: PluginManifest) -> ChatModel: ...

    async def check(self, manifest: PluginManifest) -> CheckOutcome: ...


type RemoteCheck = Callable[[PluginName, HttpServer], Awaitable[CheckOutcome]]
type StdioCheck = Callable[[PluginName, StdioServer], Awaitable[CheckOutcome]]
type ModelCheck = Callable[[PluginManifest], Awaitable[CheckOutcome]]


@dataclass(frozen=True)
class AutomaticChecks:
    """화면이 스스로 하는 확인의 길이 받는 것 전부. 프로세스를 띄우는 확인이 없다."""

    plugins: PluginSource
    remote: RemoteCheck
    model: ModelCheck


@dataclass(frozen=True)
class LaunchingChecks:
    """운영자가 누르는 확인의 길이 받는 것 전부."""

    plugins: PluginSource
    stdio: StdioCheck


async def check_automatically(
    checks: AutomaticChecks, kind: PluginKind, name: PluginName
) -> CheckOutcome | None:
    """붙어 본 결과. 없는 플러그인이거나 이 길의 대상이 아니면 없음."""
    manifest = checks.plugins.read_manifest(kind, name)
    if manifest is None:
        return None
    if manifest.kind is PluginKind.MODEL:
        return await checks.model(manifest)
    server = manifest.server
    if isinstance(server, HttpServer):
        return await checks.remote(name, server)
    return None


async def check_by_launching(checks: LaunchingChecks, name: PluginName) -> CheckOutcome | None:
    """프로세스를 한 번 띄워 본 결과. 없는 플러그인이거나 stdio가 아니면 없음."""
    manifest = checks.plugins.read_manifest(PluginKind.MCP, name)
    if manifest is None:
        return None
    server = manifest.server
    if isinstance(server, StdioServer):
        return await checks.stdio(name, server)
    return None


def assemble(
    plugins: PluginSource, tools: ToolSource, models: ModelSource
) -> tuple[AutomaticChecks, LaunchingChecks]:
    """조립 층이 포트의 묶인 메서드만 골라 넘긴다. 관리 쪽은 `connect`를 받지 않는다."""
    automatic = AutomaticChecks(plugins=plugins, remote=tools.check_remote, model=models.check)
    return automatic, LaunchingChecks(plugins=plugins, stdio=tools.check_stdio)


class FakeTools:
    """포트를 상속하지 않고 시그니처로 만족하는 가짜."""

    def connect(
        self, servers: Mapping[PluginName, McpServer]
    ) -> AbstractAsyncContextManager[ToolConnection]:
        raise NotImplementedError

    async def check_remote(self, name: PluginName, server: HttpServer) -> CheckOutcome:
        return Reached()

    async def check_stdio(self, name: PluginName, server: StdioServer) -> CheckOutcome:
        return Unreached(reason=f"MCP 서버 {name}({server.command})에 붙지 못했다")


class WideTools:
    """포트보다 넓게 받는 구현. 포트를 만족해도 부르는 쪽은 좁은 타입으로만 넘길 수 있다."""

    def connect(
        self, servers: Mapping[PluginName, McpServer]
    ) -> AbstractAsyncContextManager[ToolConnection]:
        raise NotImplementedError

    async def check_remote(self, name: PluginName, server: McpServer) -> CheckOutcome:
        return Reached()

    async def check_stdio(self, name: PluginName, server: McpServer) -> CheckOutcome:
        return Reached()


class FakeModels:
    """모델 포트를 시그니처로 만족하는 가짜."""

    def build(self, manifest: PluginManifest) -> ChatModel:
        raise NotImplementedError

    async def check(self, manifest: PluginManifest) -> CheckOutcome:
        return Reached()


def fakes_satisfy_ports(
    plugins: PluginSource,
) -> tuple[tuple[AutomaticChecks, LaunchingChecks], tuple[AutomaticChecks, LaunchingChecks]]:
    """가짜 셋을 포트 타입으로 주해해 넘긴다. 시그니처가 어긋나면 이 줄들이 걸린다."""
    tools: ToolSource = FakeTools()
    wide: ToolSource = WideTools()
    models: ModelSource = FakeModels()
    return assemble(plugins, tools, models), assemble(plugins, wide, models)
