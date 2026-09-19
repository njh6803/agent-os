"""이벤트 타입. 원칙 V: 실행은 이벤트 스트림이다.

플러그인이 import하는 공개 표면이자 JSONL 트레이스로 디스크에 남는 형식이다.
종류를 더하거나 필드를 바꾸면 ADR을 남긴다(헌법 "플러그인 모델").

결정(2026-09-19): 종류별 클래스 + Literal type 필드의 판별 유니온.
타입 검사가 지켜 주는 쪽을 골랐다. 종류 추가는 클래스 하나와 유니온 한 줄이다.
"""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class BaseEvent(BaseModel):
    """모든 이벤트의 공통 필드. run_id는 필수(원칙 V). ts는 timezone-aware만 받는다."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    run_id: str
    ts: AwareDatetime


class RunStarted(BaseEvent):
    type: Literal["run_started"] = "run_started"
    agent: str
    request: str


class LlmCalled(BaseEvent):
    type: Literal["llm_called"] = "llm_called"
    model: str
    input_tokens: int
    output_tokens: int


class ToolCalled(BaseEvent):
    type: Literal["tool_called"] = "tool_called"
    tool: str
    ok: bool


class RunFinished(BaseEvent):
    type: Literal["run_finished"] = "run_finished"
    output: str


class RunFailed(BaseEvent):
    type: Literal["run_failed"] = "run_failed"
    error: str


Event = Annotated[
    RunStarted | LlmCalled | ToolCalled | RunFinished | RunFailed,
    Field(discriminator="type"),
]
