"""접속 확인의 응답 모델과 관리가 받는 묶음 둘. 라우트는 `admin/http.py` 에 있다.

접속 확인은 켜 둔 플러그인이 가리키는 바깥 서버에 `serve` 가 실제로 붙어 보는 것이다(`CONTEXT.md`).
오퍼레이션은 둘이다. 스스로 하는 확인(`GET`)은 원격 MCP 서버와 모델을, 눌러서 하는 확인(`POST`)은
stdio MCP 서버를 확인한다(ADR 0067).

응답 모델의 독스트링은 한 줄이고 논증은 `#` 주석에 둔다(`.claude/rules/http.md`).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from agent_os.core.ports import CheckOutcome, PluginSource
from agent_os.sdk import HttpServer, PluginManifest, PluginName, StdioServer


# 경로의 `kind` 는 접속 확인이 있는 종류만 받는다. 열거로 닫아 두는 이유는 에이전트와 스킬에는 접속
# 확인이 없다는 것(ADR 0067 결정 "자리")이 생성 클라이언트의 타입에서도 드러나게 하려는 것이다.
# 어기는 값은 형식 오류(422)이고 `violations` 의 `field` 는 `path.kind` 다.
class CheckableKind(StrEnum):
    """접속 확인이 있는 플러그인의 종류. 값은 둘이다."""

    MCP = "mcp"
    MODEL = "model"


# 응답은 칸 `status` 의 값으로 가르는 닫힌 넷이다. 판별자를 두는 이유는 생성 클라이언트에서
# `reason` 이 붙지 못했을 때만 있는 값으로 좁혀지게 하려는 것이다 — 좁히지 않고 읽으면 컴파일에서
# 걸린다. `reason` 이 비지 않은 문자열인 것은 계약에 `minLength: 1` 로 실린다.
class ConnectionReached(BaseModel):
    """접속 확인이 붙었다."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["reached"]


class ConnectionUnreached(BaseModel):
    """접속 확인이 붙어 보았지만 붙지 못했다. 까닭의 글을 든다."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["unreached"]
    reason: str = Field(min_length=1)


class ConnectionDisabled(BaseModel):
    """꺼 둔 플러그인이라 접속 확인을 하지 않았다."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["disabled"]


class ConnectionNotApplicable(BaseModel):
    """이 오퍼레이션이 확인하는 플러그인이 아니라 접속 확인을 하지 않았다."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    status: Literal["not_applicable"]


# 별칭에 이름을 주는 이유는 생성 클라이언트가 익명 유니온 대신 이 이름을 받게 하기 위해서다.
type ConnectionCheck = Annotated[
    ConnectionReached | ConnectionUnreached | ConnectionDisabled | ConnectionNotApplicable,
    Field(discriminator="status"),
]


# 관리 라우터가 받는 확인 함수의 묶음 둘. 포트도 sdk 의 계약도 아니고 관리가 받는 인자의 모양이다.
# 조립하는 자리(`server`)가 포트에서 확인 메서드만 꺼내 채우므로 관리는 도구 연결을 여는 길
# (`ToolSource.connect`)을 부를 수 없다. 두 묶음이 갈린 이유는 스스로 하는 확인의 길이 stdio 서버를
# 확인하는 함수를 아예 받지 못하게 타입으로 가르려는 것이다. 포트와 달리 core 와 adapters 는 이 둘을
# 모른다.
@dataclass(frozen=True)
class AutomaticChecks:
    """스스로 하는 확인의 길이 받는 것 전부. 프로세스를 띄우는 확인은 없다."""

    plugins: PluginSource
    remote: Callable[[PluginName, HttpServer], Awaitable[CheckOutcome]]
    model: Callable[[PluginManifest], Awaitable[CheckOutcome]]


@dataclass(frozen=True)
class LaunchingChecks:
    """눌러서 하는 확인의 길이 받는 것 전부."""

    plugins: PluginSource
    stdio: Callable[[PluginName, StdioServer], Awaitable[CheckOutcome]]
