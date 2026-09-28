"""명세 축의 셋째 길을 다시 잰다. 쓰는 중인 마지막 줄을 목록이 어떻게 보나."""

from __future__ import annotations

import tempfile
from datetime import UTC, datetime, timedelta
from pathlib import Path

from agent_os.adapters.jsonl import JsonlTrace
from agent_os.core.ports import cursor_of
from agent_os.sdk import AgentName, Principal, RunFinished, RunId, RunStarted

T0 = datetime(2026, 9, 23, 12, 0, tzinfo=UTC)

with tempfile.TemporaryDirectory() as raw:
    root = Path(raw)
    store = JsonlTrace(root)
    for name, minutes in (("run-a", 0), ("run-b", 2), ("run-c", 4)):
        store.write(
            RunStarted(
                run_id=RunId(name),
                ts=T0 + timedelta(minutes=minutes),
                agent=AgentName("calc"),
                request="?",
                principal=Principal("alice"),
            )
        )
    first = store.list(limit=1)
    print("page1", [(type(r).__name__, r.run_id) for r in first])
    whole = RunFinished(run_id=RunId("run-c"), ts=T0, output="x" * 20000).model_dump_json() + "\n"
    with (root / "run-c.jsonl").open("a", encoding="utf-8") as file:
        file.write(whole[:9000])  # 쓰는 중: 줄의 앞부분만 디스크에 닿았다
    rest = store.list(after=cursor_of(first[-1]))
    print("rest ", [(type(r).__name__, r.run_id) for r in rest])
