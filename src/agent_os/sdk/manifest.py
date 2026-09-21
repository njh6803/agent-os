"""플러그인 매니페스트. plugin.toml 하나에 schema_version과 kind가 있다.

디스크에 남는 형식이라 바꾸면 ADR을 남긴다(헌법 "플러그인 모델", ADR 0008).
schema_version을 올리면 ADR 0008의 이력에 쌓는다.
"""

from __future__ import annotations

import tomllib
from collections.abc import Mapping
from enum import StrEnum
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from agent_os.sdk.ids import PluginName


class PluginKind(StrEnum):
    """넷. skill과 model은 첫 슬라이스에서 디렉터리와 값만 예약한다."""

    AGENT = "agent"
    MCP = "mcp"
    SKILL = "skill"
    MODEL = "model"


_ENTRYPOINT = r"^[A-Za-z_][\w.]*:[A-Za-z_]\w*$"
_NAME = r"^[a-z][a-z0-9-]{1,62}$"


class McpServer(BaseModel):
    """mcp 플러그인이 가리키는 stdio 서버의 실행 정보."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    command: str
    args: tuple[str, ...] = ()
    # 도구 이름 -> 트레이스에 마스킹해 쓸 인자 이름들(ADR 0009). 도구별인 이유는 금지 규칙을
    # 매니페스트만으로 판정하려면 도구 단위여야 하기 때문이다. 어느 도구가 어느 서버의
    # 것인지는 MCP 에 붙어야 알 수 있어서, 평면 목록으로는 정적 판정이 성립하지 않는다.
    secret_args: Mapping[str, tuple[str, ...]] = {}


class PluginManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1"]
    kind: PluginKind
    name: PluginName = Field(pattern=_NAME)
    version: str
    entrypoint: str | None = Field(default=None, pattern=_ENTRYPOINT)
    # 에이전트만. 쓸 mcp 플러그인 이름. 비어 있으면 도구가 없다(ADR 0002)
    mcp: tuple[PluginName, ...] = ()
    # 에이전트만. 승인 없이는 부를 수 없는 도구 이름. 비어 있으면 지금까지와 같다(ADR 0009).
    # 같은 일을 할 수 있는 도구는 전부 여기 들어가야 한다. 모델이 다른 도구로 우회하는 것은
    # 거부가 아니라 이 목록이 막는다.
    requires_approval: tuple[str, ...] = ()
    # mcp만
    server: McpServer | None = None

    @model_validator(mode="after")
    def _fields_belong_to_their_kind(self) -> Self:
        if self.kind is PluginKind.AGENT:
            if self.entrypoint is None:
                raise ValueError("agent 플러그인은 entrypoint가 필요하다 (모듈:속성)")
        elif self.entrypoint is not None:
            raise ValueError(f"{self.kind} 플러그인은 entrypoint를 갖지 않는다")
        if self.kind is not PluginKind.AGENT and "mcp" in self.model_fields_set:
            raise ValueError(f"{self.kind} 플러그인은 mcp 목록을 갖지 않는다")
        if self.kind is not PluginKind.AGENT and "requires_approval" in self.model_fields_set:
            raise ValueError(f"{self.kind} 플러그인은 requires_approval 목록을 갖지 않는다")
        if self.kind is PluginKind.MCP:
            if self.server is None:
                raise ValueError("mcp 플러그인은 [server] 표가 필요하다 (command, args)")
        elif self.server is not None:
            raise ValueError(f"{self.kind} 플러그인은 [server] 표를 갖지 않는다")
        return self


def parse_manifest(text: str) -> PluginManifest:
    return PluginManifest.model_validate(tomllib.loads(text))


def secret_args_by_tool(servers: Mapping[PluginName, McpServer]) -> Mapping[str, tuple[str, ...]]:
    """도구 이름 -> 마스킹할 인자 이름들. 서버를 가로질러 평평하다.

    빈 선언은 마스킹이 아니므로 뺀다. 가릴 인자가 없는 도구는 금지 규칙에도 걸리지 않고
    마스킹 조회에서도 원문을 돌려주므로, 두 쓰임이 같은 규칙을 본다.
    """
    return {
        tool: names
        for server in servers.values()
        for tool, names in server.secret_args.items()
        if names
    }


def approval_conflicts(
    agent: PluginManifest, servers: Mapping[PluginName, McpServer]
) -> tuple[str, ...]:
    """마스킹과 승인이 함께 걸린 도구 이름들. 비어 있으면 정책이 성립한다(ADR 0009).

    마스킹된 인자는 복원할 수 없어, 승인받아 실제로 실행되는 그 호출이 마스킹된 값을 보내게
    된다. 둘 다 매니페스트에 적히므로 실행 식별자가 생기기 전에 정적으로 판정된다. 거부는
    이 질의를 부르는 쪽이 한다. sdk 는 core 의 구성 오류 타입을 모르기 때문이다.
    """
    masked = {
        tool for server in servers.values() for tool, args in server.secret_args.items() if args
    }
    return tuple(tool for tool in agent.requires_approval if tool in masked)
