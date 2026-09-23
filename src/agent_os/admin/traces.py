"""실행 목록의 HTTP 모양과 다음 커서. 라우트는 `http.py` 의 `admin_router()` 에 있다.

모델은 core 의 요약과 표지(`ports.RunSummary`, `ports.UnreadableTrace`)를 옮긴 것이다. 따로 두는
이유는 매니페스트 표지와 같다 — core 의 독스트링은 논증이라 그대로 계약의 description 이 되면 주석을
다듬는 것이 계약 변경으로 보인다. 필드 목록이 두 곳이 되는 대가는 대조 테스트가 치른다.

**커서는 불투명하다.** 정렬 키(`ports.Cursor`)를 JSON 으로 적어 패딩 없는 base64url 로 감싼 것이고,
계약이 약속하는 것은 문자 집합과 길이(`CURSOR_PATTERN`)뿐이다. 클라이언트는 받은 `next_cursor` 를
`after` 로 되돌려 줄 뿐이라, 정렬 키를 바꾸는 날(ADR 0012 의 2026-09-23 이력이 적은 한계를 고치는
날)에도 계약은 그대로다. 사람이 읽고 지을 수 있는 키였다면 "X 이전 실행"을 뜻하는 문서 없는 시각
필터로 쓰이다 그 쓰임이 계약으로 굳었을 것이다.
"""

from __future__ import annotations

import base64
import binascii
import re
from collections.abc import Sequence
from typing import Annotated

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, ValidationError

from agent_os.core import ports
from agent_os.core.ports import RunStatus, TraceSchemaVersion
from agent_os.sdk import RUN_ID_PATTERN, RunId

# 커서의 문자 집합과 길이. 패딩 없는 base64url 이다. 가장 긴 키(오프셋 있는 마이크로초 시각과 64 자
# 식별자)가 170 자 남짓이라 상한은 넉넉히 잡은 것이고, 요청 하나가 임의 크기의 해독을 시키지 못하게
# 하는 자리다. 판정자와 FastAPI 의 질의 검증이 같은 문자열을 쓴다.
CURSOR_PATTERN = r"^[A-Za-z0-9_-]{1,256}$"
_CURSOR = re.compile(CURSOR_PATTERN)

# 응답의 실행 식별자. 패턴을 거는 이유는 이 값이 그대로 `/traces/{run_id}` 와 `agent-os resume` 의
# 입력이 되기 때문이다. 어기는 값이 새면 계약을 어긴 응답이 나가는 대신 모델이 만들어지지 않는다.
# `type` 별칭으로 쓰지 않는 이유는 그러면 pydantic 이 이것을 이름 있는 스키마로 떼어 내기 때문이다.
_WireRunId = Annotated[str, Field(pattern=RUN_ID_PATTERN)]

_MODEL_CONFIG = ConfigDict(extra="forbid", frozen=True)


# core 의 `ports.RunSummary` 를 옮긴 것이다. 필드 일곱이 전부 트레이스에서 파생되고 프롬프트·
# 토큰 수·출력·이벤트는 없다(ADR 0012 이력). 시각이 AwareDatetime 인 이유는 오프셋 없는 시각이
# 나가면 클라이언트가 그것을 제 지역 시각으로 읽기 때문이다.
class RunSummary(BaseModel):
    """목록에서 보이는 한 실행의 개요. 프롬프트와 토큰 수는 싣지 않는다."""

    model_config = _MODEL_CONFIG

    run_id: _WireRunId
    status: RunStatus
    schema_version: TraceSchemaVersion
    started_at: AwareDatetime
    last_at: AwareDatetime
    agent: str
    principal: str


class UnreadableTrace(BaseModel):
    """트레이스로 읽히지 않는 것의 표지. 실행 식별자와 이유를 든다. 실행 요약이 아니다."""

    model_config = _MODEL_CONFIG

    run_id: _WireRunId
    reason: str


# 목록의 행. 판별자가 없고 required 필드로 갈린다 — 표지만 reason 을, 요약만 status 와 나머지 다섯을
# 든다(매니페스트 쪽 `PluginRow` 와 같은 모양, ADR 0010 의 2026-09-23 이력). 별칭에 이름을 주는
# 이유는 생성 클라이언트가 익명 유니온 대신 이 이름을 받게 하기 위해서다.
type RunRow = RunSummary | UnreadableTrace


# 봉투가 아니라 이 자원의 모양이다. ADR 0010 이 거부한 봉투는 모든 응답에 같은 겉(data,
# request_id)을 씌우는 것이고, 커서는 목록의 일부라 본문에 있어야 생성 클라이언트의 타입에 실린다.
# next_cursor 에 기본값을 두지 않는 이유는 그것이 곧 스키마의 required 에서 빠지는 것이기 때문이다.
class TracePage(BaseModel):
    """실행 목록의 한 쪽. 최근 실행이 먼저다. next_cursor 가 null 이면 더 없다."""

    model_config = _MODEL_CONFIG

    runs: tuple[RunRow, ...]
    next_cursor: Annotated[str, Field(pattern=CURSOR_PATTERN)] | None


class _CursorWire(BaseModel):
    """커서 안의 JSON. 해독의 판정자가 이 모델 하나라 손으로 파싱하는 자리가 없다.

    strict 가 막는 것은 JSON 숫자(유닉스 시각)를 시각으로 읽는 것 하나다. 문자열 쪽은 pydantic 의
    날짜 해석이 받는 모양(소문자 `t`·`z`, 공백 구분자 등)을 그대로 받아 한 키에 모양이 여럿일 수
    있다. 어느 모양이든 가리키는 키는 하나라 순회가 어긋나지 않으므로 서버가 낸 모양으로 좁히지
    않는다.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)

    started_at: AwareDatetime | None
    run_id: _WireRunId


def encode_cursor(cursor: ports.Cursor) -> str:
    """정렬 키를 커서 문자열로(질의). 표지 뒤의 커서는 시각이 null 이다."""
    wire = _CursorWire(started_at=cursor.started_at, run_id=cursor.run_id)
    return _b64url_encode(wire.model_dump_json().encode())


def decode_cursor(text: str) -> ports.Cursor:
    """커서 문자열을 정렬 키로(질의). 형식에 맞지 않으면 ValueError 이고 부르는 쪽이 422 로 옮긴다.

    문자 집합을 여기서도 보는 이유는 이 함수가 혼자서도 판정자여야 하기 때문이다(`_b64url_decode`
    가 `+` 와 `/` 도 받는다). 문구는 고정이다 — pydantic 의 검증 문구는 여러 줄이고 받은 값을
    되울린다.
    """
    if _CURSOR.fullmatch(text) is None:
        raise ValueError("커서의 문자 집합이나 길이가 맞지 않다")
    try:
        wire = _CursorWire.model_validate_json(_b64url_decode(text))
    except (binascii.Error, ValidationError) as error:
        raise ValueError("앞 쪽의 next_cursor 가 아니다") from error
    return ports.Cursor(started_at=wire.started_at, run_id=RunId(wire.run_id))


def _b64url_encode(data: bytes) -> str:
    """패딩 없는 base64url(질의). 패딩의 `=` 는 질의 문자열에서 퍼센트 인코딩되므로 뺀다."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(text: str) -> bytes:
    """패딩 없는 base64url 을 되돌린다(질의). 맞지 않는 길이나 문자는 `binascii.Error` 다.

    `b64decode` 는 altchars 를 표준 문자로 바꾼 뒤 검증하므로 `+` 와 `/` 도 받는다.
    """
    padded = text + "=" * (-len(text) % 4)
    return base64.b64decode(padded, altchars=b"-_", validate=True)


def trace_page(rows: Sequence[ports.RunRow], *, limit: int) -> TracePage:
    """포트가 준 한 쪽을 응답의 한 쪽으로(질의).

    다음 커서는 받은 행이 limit 개일 때만 준다. 포트에 limit 을 그대로 넘기므로 하나 더 읽어 끝을
    미리 볼 수 없고, 딱 떨어지면 다음 요청이 빈 쪽과 null 을 받는다. 대가는 요청 하나다.
    """
    next_cursor = encode_cursor(ports.cursor_of(rows[-1])) if len(rows) >= limit else None
    return TracePage(runs=tuple(_run_row(row) for row in rows), next_cursor=next_cursor)


def _run_row(row: ports.RunRow) -> RunRow:
    """포트의 행을 응답의 행으로(질의).

    필드를 하나씩 옮기는 이유는 pyright 가 이름을 보게 하기 위해서다. 속성에서 읽게 하면 빠진 필드가
    실행 시각에야 드러난다.
    """
    if isinstance(row, ports.UnreadableTrace):
        return UnreadableTrace(run_id=row.run_id, reason=row.reason)
    return RunSummary(
        run_id=row.run_id,
        status=row.status,
        schema_version=row.schema_version,
        started_at=row.started_at,
        last_at=row.last_at,
        agent=row.agent,
        principal=row.principal,
    )
