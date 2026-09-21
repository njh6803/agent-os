"""이벤트는 디스크에 남는 형식이다. JSON 왕복과 판별을 확인한다."""

from datetime import UTC, datetime

import pytest
from pydantic import TypeAdapter, ValidationError

from agent_os.sdk import (
    AgentName,
    ApprovalDenied,
    ApprovalGranted,
    Event,
    Json,
    LlmCalled,
    Principal,
    RunId,
    RunPaused,
    RunResumed,
    RunStarted,
    ToolCall,
    ToolCalled,
)

TS = datetime(2026, 9, 21, 12, 0, tzinfo=UTC)


def _round_trip(event: Event) -> Event:
    adapter = TypeAdapter[Event](Event)
    return adapter.validate_json(adapter.dump_json(event))


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


def test_일시정지_이벤트는_부르려던_도구와_인자를_담는다() -> None:
    event = RunPaused(
        run_id=RunId("r1"),
        ts=TS,
        tool="send_email",
        args={"to": "bob@example.com", "retries": 2},
    )

    assert _round_trip(event) == event


def _as_event(**fields: str) -> Event:
    return TypeAdapter[Event](Event).validate_python({"ts": "2026-09-21T12:00:00Z", **fields})


def test_승인과_거부는_별도_종류이고_둘_다_승인자를_담는다() -> None:
    granted = ApprovalGranted(run_id=RunId("r1"), ts=TS, approver=Principal("alice"))
    denied = ApprovalDenied(
        run_id=RunId("r1"), ts=TS, approver=Principal("alice"), reason="보낼 내용이 아니다"
    )

    assert _round_trip(granted) == granted
    assert _round_trip(denied) == denied
    assert granted.type != denied.type


def test_승인자_없는_승인과_거부는_거부한다() -> None:
    with pytest.raises(ValidationError):
        _as_event(type="approval_granted", run_id="r1")
    with pytest.raises(ValidationError):
        _as_event(type="approval_denied", run_id="r1", reason="안 된다")


def test_사유는_거부에만_있다() -> None:
    with pytest.raises(ValidationError):
        _as_event(type="approval_granted", run_id="r1", approver="alice", reason="자리가 없다")
    with pytest.raises(ValidationError):
        _as_event(type="approval_denied", run_id="r1", approver="alice")


# 새 이벤트 넷의, run_id 와 ts 를 뺀 나머지 필수 필드.
_REST: dict[str, dict[str, Json]] = {
    "run_paused": {"tool": "send_email", "args": {"to": "bob"}},
    "approval_granted": {"approver": "alice"},
    "approval_denied": {"approver": "alice", "reason": "보낼 내용이 아니다"},
    "run_resumed": {},
}


def test_재개_이벤트는_재생_구간의_끝을_표시한다() -> None:
    event = RunResumed(run_id=RunId("r1"), ts=TS)

    assert _round_trip(event) == event


@pytest.mark.parametrize("kind", list(_REST))
def test_새_이벤트_넷에도_실행_식별자와_시각이_필수다(kind: str) -> None:
    complete: dict[str, Json] = {
        "type": kind,
        "run_id": "r1",
        "ts": "2026-09-21T12:00:00Z",
        **_REST[kind],
    }
    assert TypeAdapter[Event](Event).validate_python(complete).type == kind

    for required in ("run_id", "ts"):
        with pytest.raises(ValidationError):
            TypeAdapter[Event](Event).validate_python(
                {key: value for key, value in complete.items() if key != required}
            )


def test_모델_호출_이벤트는_모델이_낸_텍스트와_도구_호출을_담는다() -> None:
    event = LlmCalled(
        run_id=RunId("r1"),
        ts=TS,
        model="fake-model",
        input_tokens=7,
        output_tokens=3,
        text="보내겠습니다",
        tool_calls=(ToolCall(id="c1", name="send_email", args={"to": "bob"}),),
    )

    assert _round_trip(event) == event


def test_도구_호출_이벤트는_인자와_결과_내용을_담는다() -> None:
    event = ToolCalled(
        run_id=RunId("r1"),
        ts=TS,
        tool="send_email",
        ok=False,
        args={"to": "bob"},
        content="SMTP timeout",
    )

    assert _round_trip(event) == event
