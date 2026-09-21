"""core가 프로세스 밖과 닿는 포트. 닫힌 목록 다섯이고 늘리려면 ADR이 필요하다.

표는 `.claude/rules/core.md`. 어댑터는 이것을 상속하지 않고 시그니처로 만족한다.
ChatModel만 예외로 langchain-core의 추상 클래스 자체가 포트다. 루프가 그 위에서 돌기 때문이다.
ToolSource는 07이 더한다.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from langchain_core.language_models import BaseChatModel

from agent_os.sdk import BaseAgent, Event, PluginKind, PluginManifest, PluginName, RunId

# 모델 호출. 첫 어댑터는 langchain-anthropic의 ChatAnthropic이고 main.py가 만든다.
type ChatModel = BaseChatModel


class PluginError(Exception):
    """실행 전 구성 오류. 없는 플러그인, 매니페스트 파싱 실패, 진입점 import 실패.

    실행 식별자를 만들기 전에 나므로 트레이스가 없다. 채널은 이것을 받아 진단만 적고 끝낸다.
    """


class TraceSink(Protocol):
    """이벤트를 쓴다. 첫 어댑터는 JSONL 파일."""

    def write(self, event: Event) -> None: ...


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
