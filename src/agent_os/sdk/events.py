"""이벤트 타입. 원칙 V: 실행은 이벤트 스트림이다.

플러그인이 import하는 공개 표면이자 JSONL 트레이스로 디스크에 남는 형식이다.
종류를 더하거나 필드를 바꾸면 ADR을 남긴다(헌법 "플러그인 모델", ADR 0008).

결정(2026-09-19): 종류별 클래스 + Literal type 필드의 판별 유니온.
타입 검사가 지켜 주는 쪽을 골랐다. 종류 추가는 클래스 하나와 유니온 한 줄이다.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from agent_os.sdk.ids import AgentName, Principal, RunId
from agent_os.sdk.json import Json


class BaseEvent(BaseModel):
    """모든 이벤트의 공통 필드. run_id는 필수(원칙 V). ts는 timezone-aware만 받는다."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    run_id: RunId
    ts: AwareDatetime


class RunStarted(BaseEvent):
    type: Literal["run_started"] = "run_started"
    agent: AgentName
    request: str
    principal: Principal


class ToolCall(BaseModel):
    """모델이 요청한 도구 호출 하나. 실행되기 전이다. 실행된 기록은 ToolCalled 다."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    name: str
    args: Mapping[str, Json]


class LlmCalled(BaseEvent):
    """관찰용이면서 재개의 입력이다. 재생이 text 와 tool_calls 로 모델 응답을 되살린다.

    재개가 쓰는 필드들에 기본값이 있는 것은 형식 1 트레이스의 줄도 읽혀야 하기 때문이다
    (ADR 0009). 읽을 수 있을 뿐 재개는 못 한다는 판정은 파일 첫 줄의 형식 버전이 한다.
    """

    type: Literal["llm_called"] = "llm_called"
    model: str
    input_tokens: int
    output_tokens: int
    text: str = ""
    tool_calls: tuple[ToolCall, ...] = ()


class ToolCalled(BaseEvent):
    """실행된 도구 호출 하나. ok 가 거짓이면 content 는 에러 내용이다(용어집 "도구 결과")."""

    type: Literal["tool_called"] = "tool_called"
    tool: str
    ok: bool
    args: Mapping[str, Json] = {}
    content: str = ""


class RunPaused(BaseEvent):
    """승인을 기다리며 멈췄다. 실패도 끝난 것도 아니다. 도구 하나만 담아 승인과 실행이 1:1이다."""

    type: Literal["run_paused"] = "run_paused"
    tool: str
    args: Mapping[str, Json]


class ApprovalGranted(BaseEvent):
    """사람이 일시정지한 도구 호출을 허가했다. 승인자는 필수다(ADR 0009)."""

    type: Literal["approval_granted"] = "approval_granted"
    approver: Principal


class ApprovalDenied(BaseEvent):
    """사람이 거부했다. 사유는 거부에만 있다. 거부는 실행을 끝내지 않는다."""

    type: Literal["approval_denied"] = "approval_denied"
    approver: Principal
    reason: str


class RunResumed(BaseEvent):
    """재생이 끝나고 실제 실행이 다시 시작된다. 재생 구간과 실제 구간의 경계다."""

    type: Literal["run_resumed"] = "run_resumed"


class RunFinished(BaseEvent):
    type: Literal["run_finished"] = "run_finished"
    output: str


class RunFailed(BaseEvent):
    type: Literal["run_failed"] = "run_failed"
    error: str


Event = Annotated[
    RunStarted
    | LlmCalled
    | ToolCalled
    | RunPaused
    | ApprovalGranted
    | ApprovalDenied
    | RunResumed
    | RunFinished
    | RunFailed,
    Field(discriminator="type"),
]
