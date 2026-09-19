"""플러그인 매니페스트. plugin.toml 하나에 kind가 있다.

디스크에 남는 형식이라 바꾸면 ADR을 남긴다(헌법 "플러그인 모델").
mcp 종류의 서버 실행 필드는 첫 슬라이스 명세에서 정한다.
"""

from __future__ import annotations

import tomllib
from typing import Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

PluginKind = Literal["agent", "mcp", "skill"]

_ENTRYPOINT = r"^[A-Za-z_][\w.]*:[A-Za-z_]\w*$"


class PluginManifest(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: PluginKind
    name: str = Field(pattern=r"^[a-z][a-z0-9-]{1,62}$")
    version: str
    entrypoint: str | None = Field(default=None, pattern=_ENTRYPOINT)

    @model_validator(mode="after")
    def _entrypoint_only_for_agent(self) -> Self:
        if self.kind == "agent" and self.entrypoint is None:
            raise ValueError("agent 플러그인은 entrypoint가 필요하다 (모듈:속성)")
        if self.kind != "agent" and self.entrypoint is not None:
            raise ValueError(f"{self.kind} 플러그인은 entrypoint를 갖지 않는다")
        return self


def parse_manifest(text: str) -> PluginManifest:
    return PluginManifest.model_validate(tomllib.loads(text))
