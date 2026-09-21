"""이벤트는 디스크에 남는 형식이다. JSON 왕복과 판별을 확인한다."""

from datetime import UTC, datetime

import pytest
from pydantic import TypeAdapter, ValidationError

from agent_os.sdk import AgentName, Event, Principal, RunId, RunStarted


def _started() -> RunStarted:
    return RunStarted(
        run_id=RunId("r1"),
        ts=datetime.now(UTC),
        agent=AgentName("echo"),
        request="hi",
        principal=Principal("alice"),
    )


def test_event_round_trips_through_json() -> None:
    event = _started()
    adapter = TypeAdapter[Event](Event)
    restored = adapter.validate_json(adapter.dump_json(event))
    assert restored == event


def test_unknown_type_is_rejected() -> None:
    with pytest.raises(ValidationError):
        TypeAdapter[Event](Event).validate_python(
            {"type": "nope", "run_id": "r1", "ts": "2026-09-19T00:00:00Z"}
        )


def test_naive_timestamp_is_rejected() -> None:
    with pytest.raises(ValidationError):
        RunStarted(
            run_id=RunId("r1"),
            ts=datetime(2026, 9, 19),  # noqa: DTZ001
            agent=AgentName("echo"),
            request="hi",
            principal=Principal("alice"),
        )


def test_주체_없는_시작_이벤트는_거부한다() -> None:
    with pytest.raises(ValidationError):
        TypeAdapter[Event](Event).validate_python(
            {
                "type": "run_started",
                "run_id": "r1",
                "ts": "2026-09-19T00:00:00Z",
                "agent": "echo",
                "request": "hi",
            }
        )


def test_식별자는_JSON에서_문자열_그대로다() -> None:
    dumped = _started().model_dump(mode="json")
    assert dumped["run_id"] == "r1"
    assert dumped["agent"] == "echo"
    assert dumped["principal"] == "alice"
