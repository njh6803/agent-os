"""플러그인 매니페스트. plugin.toml 하나에 schema_version과 kind가 있다.

디스크에 남는 형식이라 바꾸면 ADR을 남긴다(헌법 "플러그인 모델", ADR 0008).
schema_version을 올리면 ADR 0008의 이력에 쌓는다.
"""

from __future__ import annotations

import tomllib
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


class PluginManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["1"]
    kind: PluginKind
    name: PluginName = Field(pattern=_NAME)
    version: str
    entrypoint: str | None = Field(default=None, pattern=_ENTRYPOINT)
    # 에이전트만. 쓸 mcp 플러그인 이름. 비어 있으면 도구가 없다(ADR 0002)
    mcp: tuple[PluginName, ...] = ()
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
        if self.kind is PluginKind.MCP:
            if self.server is None:
                raise ValueError("mcp 플러그인은 [server] 표가 필요하다 (command, args)")
        elif self.server is not None:
            raise ValueError(f"{self.kind} 플러그인은 [server] 표를 갖지 않는다")
        return self


def parse_manifest(text: str) -> PluginManifest:
    return PluginManifest.model_validate(tomllib.loads(text))
