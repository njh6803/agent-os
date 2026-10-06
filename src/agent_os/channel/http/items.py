"""최종 사용자 항목과 투영. 이벤트 하나가 항목 하나 또는 없음이 된다(ADR 0023).

최종 사용자 면의 스트림은 트레이스 이벤트가 아니라 그 사람이 볼 것만 옮긴 항목이다. 프롬프트, 도구
결과, 주체, 예외 원문, 대화 요약은 싣지 않는다 — 그 바이트가 최종 사용자의 브라우저로 갈 이유가
없고, 사이트의 페이지 안 스크립트가 읽을 수 있다(ADR 0023 의 신뢰 경계). 같은 이벤트 타입에서 필드를
비우는 안은 빈 값이 원래 빈 것인지 숨긴 것인지 타입으로 가를 수 없어 거부됐다. 운영자
채널(`/runs`)은 그대로 원문 이벤트를 싣는다.

**투영은 종류로만 가른다.** 에이전트가 낸 같은 종류의 이벤트도 같은 항목이다 — 이벤트에는 누가
냈는지 표시가 없다(ADR 0009 의 2026-10-03 이력). 항목이 없는 종류(모델 호출, 재개의 경계, 대화
요약)는 프레임을 내지 않고 트레이스 인덱스만 지난다. 그래서 프레임의 `id` 는 단조 증가하되 빈자리가
있다. 모르는 종류는 여기 닿지 않는다 — 자기 실행 읽기의 손상 판정이 그런 트레이스를 먼저 거절한다.

**계약에 박히는 모델이라 독스트링은 한 줄이고 논증은 `#` 주석에 둔다**(`.claude/rules/http.md`).
컴포넌트 이름은 기존 것(특히 본문 `Decision`·`Approve`·`Deny` 와 이벤트 `RunStarted` 같은 것)과
겹치지 않게 `…Item` 으로 짓는다. 겹치면 FastAPI 가 모듈 경로로 이름을 짓는다. 판별자 `type` 의 값은
이벤트의 것(`run_started` 따위)과 다른 낱말이라 소비자가 둘을 섞지 않는다.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Annotated, Literal, assert_never

from pydantic import BaseModel, ConfigDict, Field

from agent_os.sdk import (
    ApprovalDenied,
    ApprovalGranted,
    ConversationSummarized,
    Event,
    Json,
    LlmCalled,
    RunFailed,
    RunFinished,
    RunId,
    RunPaused,
    RunResumed,
    RunStarted,
    ToolCalled,
)

# 실패 항목의 문구. 요약 실패도 도구 서버 기동 실패도 같은 문구 하나다 — 예외 원문은 서버 기록과
# 트레이스에만 있다. 가르는 것은 web-widget 이 정한다(conversation 이 넘긴 것).
FAILED_MESSAGE = "실행이 실패로 끝났다"

# 항목은 응답에만 실리므로 직렬화 스키마 하나만 계약에 선다. 직렬화하면 필드가 언제나 전부 실리는데
# pydantic 은 기본값 있는 필드를 required 에서 빼므로, 이벤트와 같은 설정으로 판별자까지 required 로
# 둔다(`sdk/events.py`).
_ITEM_CONFIG = ConfigDict(
    extra="forbid", frozen=True, json_schema_serialization_defaults_required=True
)


class StartedItem(BaseModel):
    """실행이 시작됐다. 구독과 결정에 쓸 실행 식별자를 든다."""

    model_config = _ITEM_CONFIG

    type: Literal["started"] = "started"
    run_id: RunId


# 도구 하나가 불렸다. 인자와 결과는 싣지 않는다 — 결과는 도구 서버의 원문이고 인자는 모델이 지은
# 것이다. 진행은 도구 단위다. 모델 호출은 항목이 없다.
class ProgressItem(BaseModel):
    """도구 하나가 불렸다. 도구 이름과 성패만 든다."""

    model_config = _ITEM_CONFIG

    type: Literal["progress"] = "progress"
    tool: str
    ok: bool


# 인자는 원문이다. 승인 대상 도구는 `secret_args` 를 가질 수 없어 가려질 것이 없고(ADR 0009), 그것을
# 보이는 것이 최종 사용자가 무엇을 승인하는지 보는 것이다(ADR 0023). 이 항목의 `id` 가 결정 본문의
# `pause_index` 다.
class PausedItem(BaseModel):
    """승인을 기다리며 멈췄다. 멈춘 도구와 그 인자를 든다. 이 항목의 id 가 결정의 pause_index 다."""

    model_config = _ITEM_CONFIG

    type: Literal["paused"] = "paused"
    tool: str
    args: Mapping[str, Json]


# 승인자는 싣지 않는다 — 그 실행의 주체만 결정하므로 언제나 그 사람 자신이다. 허가에는 사유가 없어
# `reason` 이 null 이다. 결정 응답의 첫 항목이 이것이다(ADR 0014).
class DecidedItem(BaseModel):
    """결정이 기록됐다. 허가인지 거부인지와 거부의 사유를 든다."""

    model_config = _ITEM_CONFIG

    type: Literal["decided"] = "decided"
    decision: Literal["approve", "deny"]
    reason: str | None


class FinishedItem(BaseModel):
    """실행이 출력을 내고 끝났다."""

    model_config = _ITEM_CONFIG

    type: Literal["finished"] = "finished"
    output: str


# 최종 사용자에게 보여 줄 말과 운영자에게 알릴 식별자다. 예외 원문은 싣지 않는다(ADR 0023).
class FailedItem(BaseModel):
    """실행이 실패로 끝났다. 고정 문구와 실행 식별자를 든다."""

    model_config = _ITEM_CONFIG

    type: Literal["failed"] = "failed"
    message: str
    run_id: RunId


# 트레이스에 근거가 없는 유일한 항목이다. 구독이 등록부에 없고 결말도 없는 실행(서버가 다시 떠
# 사라진 실행)을 닫을 때만 낸다. 그 실행은 끝나지 않았고 끝나지 않을 것이다.
class UnfinishedItem(BaseModel):
    """실행이 끝내지 못하고 사라졌다. 구독이 닫을 때만 낸다."""

    model_config = _ITEM_CONFIG

    type: Literal["unfinished"] = "unfinished"


# 판별자 `type` 의 유니온. 별칭 이름이 계약의 컴포넌트 이름이 되고 스트림 항목 스키마의
# `contentSchema` 가 그것을 바로 가리킨다(`.scratch/end-user-channel/probes/sse_id_frames.py`
# 모양 E). 항목 컴포넌트의 타입은 생성되지만 SSE 응답 본문은 생성 타입이 `unknown` 이라, 소비자가
# 판별자 술어로 이 유니온에 좁힌다(ADR 0021·0023).
type EndUserItem = Annotated[
    StartedItem
    | ProgressItem
    | PausedItem
    | DecidedItem
    | FinishedItem
    | FailedItem
    | UnfinishedItem,
    Field(discriminator="type"),
]


def project(event: Event) -> EndUserItem | None:
    """이벤트 하나를 항목 하나 또는 없음으로(질의). 종류로만 가른다."""
    match event:
        case RunStarted(run_id=run_id):
            return StartedItem(run_id=run_id)
        case ToolCalled(tool=tool, ok=ok):
            return ProgressItem(tool=tool, ok=ok)
        case RunPaused(tool=tool, args=args):
            return PausedItem(tool=tool, args=args)
        case ApprovalGranted():
            return DecidedItem(decision="approve", reason=None)
        case ApprovalDenied(reason=reason):
            return DecidedItem(decision="deny", reason=reason)
        case RunFinished(output=output):
            return FinishedItem(output=output)
        case RunFailed(run_id=run_id):
            return FailedItem(message=FAILED_MESSAGE, run_id=run_id)
        case LlmCalled() | RunResumed() | ConversationSummarized():
            return None
        case _:
            assert_never(event)
