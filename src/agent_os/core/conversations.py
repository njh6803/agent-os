"""대화 목록을 묶는 순수 함수 하나. 이어 가기로 이어진 실행들을 갈라진 끝마다 한 줄로 묶는다.

어댑터는 실행마다 `RunRecord`(요약과 시작 이벤트의 앞 실행·요청·요청한 계정)를 만들어 이 함수에
넘기고, 묶는 규칙(끝 고르기, 거슬러 오르기, 멈추기, 칸 채우기, 정렬과 커서)은 여기 한 곳에만 있다.
색인을 붙이는 다음 어댑터도 같은 함수를 부른다. 파일이나 시계에 닿지 않는다.

- **끝.** 어느 실행도 이어 가지 않은 실행이다. 같은 실행을 둘이 이어 가 갈라지면 끝마다 한 줄이다.
  자기 자신을 앞 실행으로 가리키는 기록은 스스로를 이어 간 것으로 세지 않는다. 그 실행이 끝이어야
  손상된 기록도 목록에 한 줄로 보인다. 둘 이상이 서로를 가리키는 순환에는 끝이 없어 그 실행들은
  어느 줄에도 들지 않는다(끝에서 거슬러 오르다 만나는 순환은 아래 멈춤이 다룬다).
- **멈춤.** 끝에서 앞 실행을 차례로 거슬러 오르다 앞 실행이 없거나(지운 트레이스) 읽히지 않거나 이미
  지난 실행으로 돌아오면(순환) 거기서 멈추고 `complete` 를 거짓으로 둔다. 그 줄의 첫 실행은 멈추기
  전에 읽힌 가장 오래된 실행이다. 이어 가기의 판정(주체가 같은지, 앞 실행이 끝났는지)은 목록이
  표시하는 자리라 다시 하지 않는다. 그 판정은 대화를 이어 갈 때 `continuation.py` 가 한다.
- **차례.** 끝 실행의 (시작 시각, 식별자) 역순이고 표지는 시각이 없어 맨 뒤에서 식별자로 갈린다.
  실행 목록과 같은 키(`order_key`)라 커서도 같다(ADR 0012).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from agent_os.core.ports import (
    ConversationLine,
    ConversationRow,
    Cursor,
    RunRecord,
    RunStatus,
    UnreadableTrace,
    cursor_of,
    order_key,
    page_size,
)
from agent_os.sdk import RunId

# 줄이 싣는 첫 요청의 길이. 파이썬의 글자 수(코드 포인트)다. 목록 응답 하나가 모든 대화의 내용을
# 나르지 않게 하려는 것이고, 화면은 열 폭에 맞춰 다시 줄인다.
FIRST_REQUEST_LENGTH = 120


def list_conversations(
    runs: Iterable[RunRecord | UnreadableTrace],
    *,
    status: RunStatus | None = None,
    limit: int | None = None,
    after: Cursor | None = None,
) -> tuple[ConversationRow, ...]:
    """실행 기록들을 대화 줄로 묶어 한 쪽을 돌려준다(질의).

    `status` 는 끝 실행의 상태이고 표지는 상태가 없어 함께 빠진다. `limit` 의 범위(1 과
    `MAX_LIMIT` 사이)를 어기면 `ValueError` 다. 어댑터가 실행을 읽어 넘기는 순서는 결과에 영향을
    주지 않는다.
    """
    size = page_size(limit)
    given = list(runs)
    records = [run for run in given if isinstance(run, RunRecord)]
    unreadable = [run for run in given if isinstance(run, UnreadableTrace)]
    by_id = {record.summary.run_id: record for record in records}
    continued = {
        record.previous_run
        for record in records
        if record.previous_run is not None and record.previous_run != record.summary.run_id
    }
    ends = [end for end in records if end.summary.run_id not in continued]
    if status is not None:
        ends = [end for end in ends if end.summary.status == status]
        unreadable = []
    # 정렬 키와 상태는 끝 실행 하나에서 나온다. 그래서 거르고 자른 뒤 고른 끝에만 거슬러 오른다.
    candidates: list[RunRecord | UnreadableTrace] = [*ends, *unreadable]
    keyed = [
        (order_key(cursor_of(item.summary if isinstance(item, RunRecord) else item)), item)
        for item in candidates
    ]
    keyed.sort(key=lambda pair: pair[0], reverse=True)
    if after is not None:
        edge = order_key(after)
        keyed = [pair for pair in keyed if pair[0] < edge]
    return tuple(
        _line(item, by_id) if isinstance(item, RunRecord) else item for _, item in keyed[:size]
    )


def _line(end: RunRecord, by_id: Mapping[RunId, RunRecord]) -> ConversationLine:
    """끝 실행에서 앞 실행을 거슬러 올라 줄 하나를 만든다(질의)."""
    first = end
    count = 1
    seen = {end.summary.run_id}
    complete = True
    while first.previous_run is not None:
        previous = by_id.get(first.previous_run)
        if previous is None or previous.summary.run_id in seen:
            complete = False
            break
        first = previous
        seen.add(first.summary.run_id)
        count += 1
    return ConversationLine(
        last_run=end.summary.run_id,
        status=end.summary.status,
        agent=end.summary.agent,
        first_request=first.request[:FIRST_REQUEST_LENGTH],
        requesting_account=first.requesting_account,
        principal=first.summary.principal,
        run_count=count,
        last_started_at=end.summary.started_at,
        last_at=end.summary.last_at,
        complete=complete,
    )
