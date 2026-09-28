"""커서가 잡지 못하는 경우를 진짜 JSONL 어댑터로 잰다. 저장소에 남기지 않는다."""

from __future__ import annotations

import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

from agent_os.adapters.jsonl import JsonlTrace
from agent_os.core.ports import RunRow, cursor_of
from agent_os.sdk import (
    AgentName,
    ApprovalGranted,
    Principal,
    RunId,
    RunPaused,
    RunResumed,
    RunStarted,
)

T0 = datetime(2026, 9, 23, 12, 0, tzinfo=UTC)


def start(store: JsonlTrace, run_id: str, minutes: int) -> None:
    store.write(
        RunStarted(
            run_id=RunId(run_id),
            ts=T0 + timedelta(minutes=minutes),
            agent=AgentName("calc"),
            request="2+2?",
            principal=Principal("alice"),
        )
    )


def pause(store: JsonlTrace, run_id: str, minutes: int) -> None:
    store.write(
        RunPaused(run_id=RunId(run_id), ts=T0 + timedelta(minutes=minutes), tool="add", args={})
    )


def ids(rows: tuple[RunRow, ...]) -> list[str]:
    return [row.run_id for row in rows]


with tempfile.TemporaryDirectory() as raw:
    # 1) 지나간 범위에 늦게 나타난 파일
    store = JsonlTrace(Path(raw) / "a")
    for name, minute in (("a", 0), ("b", 2), ("c", 4)):
        start(store, name, minute)
    page1 = store.list(limit=2)
    print("1) page1", ids(page1))
    start(store, "late", 3)  # 시작 시각이 b 와 c 사이. 파일은 page1 뒤에 생긴다
    start(store, "head", 9)  # 머리에 새로 생긴 실행
    page2 = store.list(limit=2, after=cursor_of(page1[-1]))
    print("1) page2", ids(page2), "| 전체", ids(store.list()))

    # 2) 한 프로세스씩만 도는 전제에서: 재개된 옛 실행이 둘째 게이트에서 다시 멈춘다
    store = JsonlTrace(Path(raw) / "b")
    for name, minute in (("p1", 0), ("p2", 2), ("p3", 4)):
        start(store, name, minute)
        pause(store, name, minute + 1)
    # 승인자가 멈춘 실행 목록을 쪽으로 넘기는 동안 p2 가 재개 중이다(마지막 이벤트가 run_resumed)
    store.write(
        ApprovalGranted(
            run_id=RunId("p2"), ts=T0 + timedelta(minutes=10), approver=Principal("bob")
        )
    )
    store.write(RunResumed(run_id=RunId("p2"), ts=T0 + timedelta(minutes=10)))
    page1 = store.list(status="paused", limit=1)
    print("2) page1", ids(page1))
    page2 = store.list(status="paused", limit=1, after=cursor_of(page1[-1]))
    print("2) page2", ids(page2))
    pause(store, "p2", 11)  # 둘째 게이트에서 다시 멈춘다
    page3 = store.list(status="paused", limit=1, after=cursor_of(page2[-1]))
    print("2) page3", ids(page3), "| 지금 멈춘 것 전체", ids(store.list(status="paused")))
