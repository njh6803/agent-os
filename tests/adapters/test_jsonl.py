"""JSONL TraceSink. 한 줄에 JSON 하나, 첫 줄은 헤더, 모르는 종류는 원문 보존."""

import json
from datetime import UTC, datetime
from pathlib import Path

from agent_os.adapters.jsonl import JsonlTrace, UnknownEvent, read_trace
from agent_os.core.ports import TraceSink
from agent_os.sdk import (
    AgentName,
    Event,
    LlmCalled,
    Principal,
    RunFinished,
    RunId,
    RunStarted,
    ToolCall,
    ToolCalled,
)

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
    assert json.loads(lines[0]) == {"schema_version": "2", "run_id": "run-1"}
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
    future = '{"type":"run_rewound","run_id":"run-1","ts":"2026-09-21T12:00:00Z","to":"x"}'
    with (tmp_path / "run-1.jsonl").open("a", encoding="utf-8") as f:
        f.write(future + "\n")
    sink.write(finished)

    trace = read_trace(tmp_path / "run-1.jsonl")

    assert list(trace.events) == [started, UnknownEvent(raw=future), finished]


# 형식 1 로 쓰인 트레이스. 재개의 입력이 되는 필드가 아직 없다.
_V1_TRACE = (
    '{"schema_version":"1","run_id":"old"}\n'
    '{"type":"llm_called","run_id":"old","ts":"2026-09-21T12:00:00Z",'
    '"model":"m","input_tokens":7,"output_tokens":3}\n'
)


def test_형식_1_트레이스도_읽히고_재개에_쓰는_필드는_비어_있다(tmp_path: Path) -> None:
    path = tmp_path / "old.jsonl"
    path.write_text(_V1_TRACE, encoding="utf-8")

    trace = read_trace(path)

    assert trace.header.schema_version == "1"
    event = trace.events[0]
    assert isinstance(event, LlmCalled)
    assert event.text == ""
    assert event.tool_calls == ()


def test_두꺼워진_이벤트가_파일에_그대로_남고_다시_읽힌다(tmp_path: Path) -> None:
    sink: TraceSink = JsonlTrace(tmp_path)
    events: list[Event] = [
        LlmCalled(
            run_id=RunId("run-1"),
            ts=TS,
            model="m",
            input_tokens=7,
            output_tokens=3,
            text="보내겠습니다",
            tool_calls=(ToolCall(id="c1", name="send_email", args={"to": "bob"}),),
        ),
        ToolCalled(
            run_id=RunId("run-1"),
            ts=TS,
            tool="send_email",
            ok=True,
            args={"to": "bob"},
            content="sent",
        ),
    ]

    for event in events:
        sink.write(event)

    assert list(read_trace(tmp_path / "run-1.jsonl").events) == events
