"""이벤트 타입. 원칙 V: 실행은 이벤트 스트림이다.

플러그인이 import하는 공개 표면이자 JSONL 트레이스로 디스크에 남는 형식이고, 관리 API의 트레이스
상세로 `openapi.json`에도 그대로 박힌다. 종류를 더하거나 필드를 바꾸면 ADR을 남긴다(헌법 "플러그인
모델", ADR 0008). 그 계약 파일도 같은 PR에서 바뀐다.

결정(2026-09-19): 종류별 클래스 + Literal type 필드의 판별 유니온.
타입 검사가 지켜 주는 쪽을 골랐다. 종류 추가는 클래스 하나와 유니온 한 줄이다.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Annotated, Literal

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from agent_os.sdk.ids import AgentName, Principal, RunId
from agent_os.sdk.json import Json


# 이벤트는 관리 API 의 트레이스 상세에 그대로 실린다(ADR 0010 의 2026-09-24 이력). 그래서 이벤트
# 모델의 독스트링은 한 줄이고 논증은 `#` 주석에 둔다 — 독스트링이 곧 openapi.json 의 설명이다.
# 직렬화하면 필드가 언제나 전부 실리는데 pydantic 은 기본값 있는 필드를 JSON 스키마의 required 에서
# 빼므로, 그대로 두면 생성 클라이언트가 판별자 `type` 까지 선택 필드로 받는다. 이 설정이 바꾸는 것은
# 직렬화 쪽 JSON 스키마뿐이고 디스크 형식도 검증도 그대로다. 매니페스트가 같은 이유로 켰다.
class BaseEvent(BaseModel):
    """모든 이벤트의 공통 필드. run_id는 필수(원칙 V). ts는 timezone-aware만 받는다."""

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        json_schema_serialization_defaults_required=True,
    )

    run_id: RunId
    ts: AwareDatetime


# previous_run 은 이 실행이 이어 간 앞 실행이고 대화의 고리는 이 필드 하나로 파생된다(ADR 0022).
# 기본값이 None 인 것은 형식 1·2 트레이스의 줄에 이 키가 없기 때문이다 — 기본값이 있어야 그 줄이
# 손상이 아니다. 직렬화 스키마에서는 BaseEvent 의 설정대로 required 이고 null 을 허락한다. sdk 의
# 식별자 패턴을 걸지 않는 것은 이벤트의 run_id 와 같은 규칙이다. 패턴 위반은 거슬러 읽기가 기록의
# 손상으로 판정한다. 모델에 걸면 그 판정이 단건 읽기의 손상으로 옮고, 손편집 사례를 타입 있는 가짜로
# 만들 수 없다.
#
# shortcuts 는 바로가기다. 에이전트 이름에서 그 대화에서 그 에이전트가 가장 최근에 처리한 실행으로
# 가는 지도이고, 없음(None)은 바로가기가 없는 실행이다(ADR 0022 의 둘째 2026-10-15 이력). 기본값이
# None 인 것은 형식 1·2·3 의 옛 줄에 이 키가 없기 때문이고 형식은 3 그대로다. 직렬화 스키마의 모양은
# previous_run 과 같다. 키와 값에 sdk 의 패턴을 걸지 않는 것도 이벤트의 다른 식별자 필드와 같은
# 규칙이다 — 걸면 패턴 위반이 단건 읽기의 손상이 된다. 필드 이름이 용어집의 말이 아닌 것은 이것이
# 시작 이벤트의 필드일 뿐 도메인의 개념이 아니어서다.
class RunStarted(BaseEvent):
    """실행이 시작됐다. 에이전트·요청·주체와 앞 실행·바로가기(없으면 null)를 든다. 런타임이 낸다."""

    type: Literal["run_started"] = "run_started"
    agent: AgentName
    request: str
    principal: Principal
    previous_run: RunId | None = None
    shortcuts: Mapping[AgentName, RunId] | None = None


class ToolCall(BaseModel):
    """모델이 요청한 도구 호출 하나. 실행되기 전이다. 실행된 기록은 ToolCalled 다."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    name: str
    args: Mapping[str, Json]


# 관찰용이면서 재개의 입력이다. 재생이 text 와 tool_calls 로 모델 응답을 되살린다.
#
# prompt 는 이 호출을 일으킨 ctx.llm() 의 프롬프트이고 재생의 대조가 쓰는 유일한 입력이다.
# 루프의 첫 턴에만 담긴다. 둘째 턴부터의 입력은 기록에서 파생되므로 같은 값을 턴마다 되풀이해
# 적지 않는다. 비어 있지 않은 prompt 가 곧 ctx.llm() 하나가 시작하는 자리다(ADR 0009 이력).
#
# 재개가 쓰는 필드들에 기본값이 있는 것은 형식 1 트레이스의 줄도 읽혀야 하기 때문이다
# (ADR 0009). 읽을 수 있을 뿐 재개는 못 한다는 판정은 파일 첫 줄의 형식 버전이 한다.
class LlmCalled(BaseEvent):
    """모델 호출 하나. 관찰용이면서 재개의 입력이다. prompt 는 루프의 첫 턴에만 담긴다."""

    type: Literal["llm_called"] = "llm_called"
    model: str
    input_tokens: int
    output_tokens: int
    prompt: str = ""
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
    """실행이 출력을 내고 끝났다. 에이전트가 마지막에 하나 낸다."""

    type: Literal["run_finished"] = "run_finished"
    output: str


# 실패 원인의 값 아홉(ADR 0031). 실패한 실행이 왜 실패했는지를 실패가 생긴 자리로 가른 종류이고
# 실패의 내용(`RunFailed.error`)이 아니다. 닫힌 목록이고 값을 늘리는 것은 계약의 가산 변경이다.
# 값마다의 뜻은 ADR 0031 의 이력에 있다. 이벤트와 최종 사용자 실패 항목이 이 값 집합 하나를 나눠
# 쓴다 — 두 곳에 같은 열거를 따로 두면 언젠가 어긋난다. 별칭 이름이 계약의 컴포넌트 이름이 된다.
type FailureCause = Literal[
    "conversation_summary",
    "timeout",
    "tool_connection",
    "model_call",
    "tool_failure",
    "loop_limit",
    "resume_mismatch",
    "agent_code",
    "other",
]


# cause 는 실패 원인이고 없음(None)은 원인이 기록되지 않은 실패다. 기본값이 None 인 것은 형식 1·2·3
# 의 옛 줄에 이 키가 없기 때문이고 형식은 3 그대로다(ADR 0031). 직렬화 스키마에서는 BaseEvent 의
# 설정대로 required 이고 null 을 허락한다. 이름이 `reason` 이 아닌 이유는 관리 화면의 필드 이름 표가
# 필드 이름을 키로 써서, 거부 사유(`ApprovalDenied.reason`)와 같은 이름이면 "실패 원인"을 붙일 칸이
# 없기 때문이다. 원인이 든 실패는 런타임만 낸다 — 에이전트가 이 종류를 yield 하면 원인이 있든 없든
# 그 실행은 런타임의 run_failed 로 끝난다(ADR 0031).
class RunFailed(BaseEvent):
    """실행이 실패로 끝났다. error 는 내용, cause 는 실패 원인(없으면 null)이다. 런타임이 낸다."""

    type: Literal["run_failed"] = "run_failed"
    error: str
    cause: FailureCause | None = None


# 이어 간 실행의 트레이스에서 run_started 바로 뒤에 서고 실행 하나에 많아야 하나다(ADR 0022).
# 런타임이 그 에이전트의 앞 요약과 오래된 교환을 그 실행의 모델로 접은 글이고, 다음 이어 가기의
# 거슬러 읽기가 트레이스에서 읽는 입력이다. 그래서 런타임만 낸다 — 에이전트가 이 종류를 yield 하면
# 그 실행은 run_failed 다. 에이전트가 지어낸 요약이 통과하면 런타임의 것과 가를 수 없다. summary 가
# `text` 가 아닌 이유는 관리 화면의 필드 이름 표가 `text` 에 "응답 텍스트"를 붙이기 때문이다.
# last_covered_run 은 이 요약이 덮는 범위의 끝, 곧 덮인 교환 가운데 가장 최근 실행이다. 시작은 적지
# 않는다 — 새 요약은 거슬러 읽기가 만난 가장 가까운 요약을 접어 만들어지므로 시작은 그 에이전트의
# 첫 교환이다. 거슬러 읽기가 읽기 상한(core)에 닿아 멈춘 적이 있는 대화는 그 상한 너머가 빠진다.
# 거슬러 읽기는 가장 가까운 요약을 만나면 덮는 끝의 실행까지만 가고 그 실행은 읽지 않는다. 식별자에
# 패턴을 걸지 않는 이유는 RunStarted.previous_run 과 같다. 토큰 수는 요약에 든 비용이 보이게 한다.
class ConversationSummarized(BaseEvent):
    """런타임이 앞 요약과 오래된 교환을 새 대화 요약으로 접었다. 에이전트가 내면 실행이 실패한다."""

    type: Literal["conversation_summarized"] = "conversation_summarized"
    summary: str
    last_covered_run: RunId
    model: str
    input_tokens: int
    output_tokens: int


Event = Annotated[
    RunStarted
    | LlmCalled
    | ToolCalled
    | RunPaused
    | ApprovalGranted
    | ApprovalDenied
    | RunResumed
    | RunFinished
    | RunFailed
    | ConversationSummarized,
    Field(discriminator="type"),
]
