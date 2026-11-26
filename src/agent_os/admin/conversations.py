"""대화 목록의 HTTP 모양. 라우트는 `http.py` 의 `admin_router()` 에 있다.

모델은 core 의 대화 줄(`ports.ConversationLine`)을 옮긴 것이다. 따로 두는 이유는 실행 목록과 같다 —
core 의 독스트링은 논증이라 그대로 계약의 description 이 되면 주석을 다듬는 것이 계약 변경으로
보인다(`admin/traces.py`). 필드 목록이 두 곳이 되는 대가는 대조 테스트가 치른다. 읽히지 않는
트레이스의 표지와 커서와 쪽의 모양은 실행 목록의 것을 그대로 쓴다. 대화 줄의 커서가 끝 실행의
(시작 시각, 식별자)라 실행 목록의 커서와 같은 키이기 때문이다.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Annotated

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field

from agent_os.admin.traces import CURSOR_PATTERN, UnreadableTrace, encode_cursor
from agent_os.core import ports
from agent_os.core.conversations import FIRST_REQUEST_LENGTH
from agent_os.core.ports import RunStatus
from agent_os.sdk import RUN_ID_PATTERN

# 응답의 실행 식별자. 패턴을 거는 이유는 이 값이 그대로 화면의 `/chat/<last_run>` 주소가 되기
# 때문이다. `type` 별칭으로 쓰지 않는 이유는 그러면 pydantic 이 이것을 이름 있는 스키마로 떼어 내기
# 때문이다.
_WireRunId = Annotated[str, Field(pattern=RUN_ID_PATTERN)]

_MODEL_CONFIG = ConfigDict(extra="forbid", frozen=True)


# core 의 `ports.ConversationLine` 을 옮긴 것이다. 끝 실행의 칸 다섯(`last_run`·`status`·`agent`·
# `last_started_at`·`last_at`)과 첫 실행의 칸 셋(`first_request`·`requesting_account`·`principal`),
# 그 사이의 `run_count` 와 `complete` 다. 칸에 기본값을 두지 않아 모두 계약의 required 다. 첫 요청의
# 길이는 core 가 자르는 값을 계약에도 박아 둔다(파이썬의 글자 수, pydantic 의 `max_length` 와 같은
# 셈).
class Conversation(BaseModel):
    """이어 가기로 이어진 실행들의 한 줄. 갈라진 끝 하나를 대표한다."""

    model_config = _MODEL_CONFIG

    last_run: _WireRunId
    status: RunStatus
    agent: str
    first_request: Annotated[str, Field(max_length=FIRST_REQUEST_LENGTH)]
    requesting_account: str | None
    principal: str
    run_count: Annotated[int, Field(ge=1)]
    last_started_at: AwareDatetime
    last_at: AwareDatetime
    complete: bool


# 목록의 행. 판별자가 없고 required 필드로 갈린다 — 표지만 `reason` 을, 대화 줄만 `last_run` 과
# 나머지를 든다(실행 목록의 `RunRow` 와 같은 모양). 별칭에 이름을 주는 이유는 생성 클라이언트가 익명
# 유니온 대신 이 이름을 받게 하기 위해서다.
type ConversationRow = Conversation | UnreadableTrace


# 봉투가 아니라 이 자원의 모양이다. `next_cursor` 에 기본값을 두지 않는 이유는 그것이 곧 스키마의
# required 에서 빠지는 것이기 때문이다.
class ConversationPage(BaseModel):
    """대화 목록의 한 쪽. 끝 실행이 최근인 대화가 먼저다. next_cursor 가 null 이면 더 없다."""

    model_config = _MODEL_CONFIG

    conversations: tuple[ConversationRow, ...]
    next_cursor: Annotated[str, Field(pattern=CURSOR_PATTERN)] | None


def conversation_page(rows: Sequence[ports.ConversationRow], *, limit: int) -> ConversationPage:
    """포트가 준 한 쪽을 응답의 한 쪽으로(질의).

    다음 커서는 받은 행이 limit 개일 때만 준다. 실행 목록과 같은 규칙이고 대가도 같다 — 딱 떨어지면
    다음 요청이 빈 쪽과 null 을 받는다.
    """
    next_cursor = encode_cursor(ports.cursor_of(rows[-1])) if len(rows) >= limit else None
    return ConversationPage(
        conversations=tuple(_conversation_row(row) for row in rows), next_cursor=next_cursor
    )


def _conversation_row(row: ports.ConversationRow) -> ConversationRow:
    """포트의 행을 응답의 행으로(질의). 필드를 하나씩 옮겨 pyright 가 이름을 보게 한다."""
    if isinstance(row, ports.UnreadableTrace):
        return UnreadableTrace(run_id=row.run_id, reason=row.reason)
    return Conversation(
        last_run=row.last_run,
        status=row.status,
        agent=row.agent,
        first_request=row.first_request,
        requesting_account=row.requesting_account,
        principal=row.principal,
        run_count=row.run_count,
        last_started_at=row.last_started_at,
        last_at=row.last_at,
        complete=row.complete,
    )
