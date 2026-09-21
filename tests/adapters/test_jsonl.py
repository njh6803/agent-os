"""JSONL TraceSink. 한 줄에 JSON 하나, 첫 줄은 헤더, 모르는 종류는 원문 보존."""

import json
from datetime import UTC, datetime
from pathlib import Path

from agent_os.adapters.jsonl import TRACE_SCHEMA_VERSION, JsonlTrace, UnknownEvent, read_trace
from agent_os.core.ports import TraceSink
from agent_os.sdk import AgentName, Event, Principal, RunFinished, RunId, RunStarted

TS = datetime(2026, 9, 21, 12, 0, tzinfo=UTC)


def _events(run_id: str) -> list[Event]:
    return [
        RunStarted(
            run_id=RunId(run_id),
            ts=TS,
            agent=AgentName("calc"),
            request="2+2?",
            principal=Principal("alice"),
        ),
        RunFinished(run_id=RunId(run_id), ts=TS, output="4"),
    ]


def test_실행마다_실행_식별자_이름의_파일_하나가_생긴다(tmp_path: Path) -> None:
    sink: TraceSink = JsonlTrace(tmp_path / "traces")

    for event in _events("run-1") + _events("run-2"):
        sink.write(event)

    assert sorted(p.name for p in (tmp_path / "traces").iterdir()) == [
        "run-1.jsonl",
        "run-2.jsonl",
    ]


def test_첫_줄은_형식_버전과_실행_식별자를_담은_헤더이고_다음_줄부터_이벤트다(
    tmp_path: Path,
) -> None:
    sink: TraceSink = JsonlTrace(tmp_path)
    events = _events("run-1")

    for event in events:
        sink.write(event)

    lines = (tmp_path / "run-1.jsonl").read_text(encoding="utf-8").splitlines()
    assert json.loads(lines[0]) == {"schema_version": TRACE_SCHEMA_VERSION, "run_id": "run-1"}
    assert lines[1:] == [event.model_dump_json() for event in events]


def test_쓴_것을_다시_읽으면_넣은_이벤트와_같다(tmp_path: Path) -> None:
    sink: TraceSink = JsonlTrace(tmp_path)
    events = _events("run-1")
    for event in events:
        sink.write(event)

    trace = read_trace(tmp_path / "run-1.jsonl")

    assert trace.header.run_id == "run-1"
    assert list(trace.events) == events


def test_모르는_종류의_이벤트가_섞여_있어도_원문이_보존된다(tmp_path: Path) -> None:
    sink: TraceSink = JsonlTrace(tmp_path)
    started, finished = _events("run-1")
    sink.write(started)
    future = '{"type":"run_paused","run_id":"run-1","ts":"2026-09-21T12:00:00Z","reason":"x"}'
    with (tmp_path / "run-1.jsonl").open("a", encoding="utf-8") as f:
        f.write(future + "\n")
    sink.write(finished)

    trace = read_trace(tmp_path / "run-1.jsonl")

    assert list(trace.events) == [started, UnknownEvent(raw=future), finished]
