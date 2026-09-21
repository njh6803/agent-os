"""core가 프로세스 밖과 닿는 포트. 닫힌 목록 다섯이고 늘리려면 ADR이 필요하다.

표는 `.claude/rules/core.md`. 어댑터는 이것을 상속하지 않고 시그니처로 만족한다.
ChatModel만 예외로 langchain-core의 추상 클래스 자체가 포트다. 루프가 그 위에서 돌기 때문이다.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol

from langchain_core.language_models import BaseChatModel

from agent_os.sdk import (
    BaseAgent,
    Event,
    Json,
    McpServer,
    PluginKind,
    PluginManifest,
    PluginName,
    RunId,
)

# 모델 호출. 첫 어댑터는 langchain-anthropic의 ChatAnthropic이고 main.py가 만든다.
type ChatModel = BaseChatModel


class PluginError(Exception):
    """실행 전 구성 오류. 없는 플러그인, 매니페스트 파싱 실패, 진입점 import 실패.

    실행 식별자를 만들기 전에 나므로 트레이스가 없다. 채널은 이것을 받아 진단만 적고 끝낸다.
    """


@dataclass(frozen=True)
class UnknownEvent:
    """이 런타임이 모르는 종류. 원문을 그대로 들고 있어 옛 도구가 새 트레이스를 지우지 않는다."""

    raw: str


# 트레이스 형식 버전의 집합. 2 부터 이벤트가 재개의 입력이 될 만큼 두껍다(ADR 0008, 0009).
# 버전이 뜻하는 것은 이벤트의 내용이라 어댑터가 아니라 여기가 소유한다. 어댑터는 이것을 헤더에 쓴다.
type TraceSchemaVersion = Literal["1", "2"]


@dataclass(frozen=True)
class Trace:
    """한 실행의 트레이스. 이벤트는 쓴 순서 그대로다.

    schema_version 은 저장소가 그 실행을 쓸 때의 형식 버전이다. 버전 1 은 재개의 입력이 되는
    필드가 비어 있어 읽을 수는 있지만 재개할 수 없다(ADR 0009). 그 판정은 재개 진입점이 한다.
    """

    run_id: RunId
    schema_version: TraceSchemaVersion
    events: tuple[Event | UnknownEvent, ...]


class TraceStore(Protocol):
    """이벤트를 쓰고 한 실행의 트레이스를 읽는다. 첫 어댑터는 JSONL 파일.

    쓰는 곳과 읽는 곳이 항상 같다는 사실을 이 타입 하나가 강제한다(ADR 0009). 부재는 None.
    """

    def write(self, event: Event) -> None: ...

    def read(self, run_id: RunId) -> Trace | None: ...


class PluginSource(Protocol):
    """매니페스트를 읽고 에이전트를 로드한다. 첫 어댑터는 파일시스템(ADR 0003).

    부재는 None, 실패(파싱, import)는 PluginError.
    """

    def read_manifest(self, kind: PluginKind, name: PluginName) -> PluginManifest | None: ...

    def load_agent(self, manifest: PluginManifest) -> BaseAgent: ...


class Clock(Protocol):
    """현재 시각(UTC)과 실행 식별자. 첫 어댑터는 시스템 시계와 uuid4."""

    def now(self) -> datetime: ...

    def new_run_id(self) -> RunId: ...


@dataclass(frozen=True)
class ToolSpec:
    """모델에게 붙일 도구 하나. input_schema 는 JSON Schema."""

    name: str
    description: str
    input_schema: Mapping[str, Json]


@dataclass(frozen=True)
class ToolResult:
    """도구가 돌려준 것. ok 가 거짓이면 content 는 에러 내용이다."""

    ok: bool
    content: str


class ToolConnection(Protocol):
    """ToolSource 가 연 연결. 도구 목록을 주고 도구를 부른다."""

    def tools(self) -> Sequence[ToolSpec]: ...

    async def call(self, name: str, args: Mapping[str, Json]) -> ToolResult: ...


class ToolSource(Protocol):
    """서버 명세를 받아 도구를 연결한다. 시작과 종료의 수명이 있다. 첫 어댑터는 MCP stdio.

    connect 가 실패하면(서버 기동 실패) 실행은 run_failed 로 끝난다. 비어 있으면 도구 없이 연다.
    """

    def connect(
        self, servers: Mapping[PluginName, McpServer]
    ) -> AbstractAsyncContextManager[ToolConnection]: ...
