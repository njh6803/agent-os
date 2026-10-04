"""이벤트는 디스크에 남는 형식이다. JSON 왕복과 판별을 확인한다."""

from datetime import UTC, datetime

import pytest
from pydantic import TypeAdapter, ValidationError

from agent_os.sdk import (
    AgentName,
    ApprovalDenied,
    ApprovalGranted,
    ConversationSummarized,
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


def _as_event(**fields: Json) -> Event:
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


def test_모델_호출_이벤트는_그_호출을_일으킨_프롬프트를_담는다() -> None:
    """재개의 대조가 쓰는 유일한 입력이다(ADR 0009 의 2026-09-22 이력)."""
    event = LlmCalled(
        run_id=RunId("r1"),
        ts=TS,
        model="fake-model",
        input_tokens=7,
        output_tokens=3,
        prompt="2 더하기 2는?",
    )

    assert _round_trip(event) == event


def test_프롬프트가_없는_모델_호출_이벤트도_읽힌다() -> None:
    """루프의 둘째 턴부터와 이 결정 이전에 쓰인 트레이스가 그렇다."""
    event = _as_event(type="llm_called", run_id="r1", model="m", input_tokens=1, output_tokens=1)

    assert isinstance(event, LlmCalled)
    assert event.prompt == ""


# --- 대화(ADR 0022, 형식 3) ----------------------------------------------------


def test_시작_이벤트의_앞_실행은_선택이고_기본이_없음이라_옛_줄이_그대로_읽힌다() -> None:
    """형식 1·2 의 줄에는 이 키가 없다. 기본값이 있어야 그 줄이 손상이 아니다(ADR 0022)."""
    old = _as_event(
        type="run_started",
        run_id="r1",
        ts="2026-09-21T12:00:00Z",
        agent="echo",
        request="hi",
        principal="alice",
    )
    continued = _as_event(
        type="run_started",
        run_id="r2",
        ts="2026-09-21T12:00:00Z",
        agent="echo",
        request="그럼?",
        principal="alice",
        previous_run="r1",
    )

    assert isinstance(old, RunStarted)
    assert old.previous_run is None
    assert isinstance(continued, RunStarted)
    assert continued.previous_run == "r1"
    assert _round_trip(continued) == continued


def test_앞_실행과_덮는_끝에는_sdk_의_패턴을_걸지_않는다() -> None:
    """패턴 위반은 거슬러 읽기가 기록의 손상으로 판정한다. 모델에 걸면 그 판정이 단건 읽기의
    손상으로 옮고 손편집 사례를 타입 있는 가짜로 만들 수 없다(명세 검토)."""
    started = _as_event(
        type="run_started",
        run_id="r2",
        ts="2026-09-21T12:00:00Z",
        agent="echo",
        request="그럼?",
        principal="alice",
        previous_run="../etc",
    )
    summarized = _as_event(
        type="conversation_summarized",
        run_id="r2",
        ts="2026-09-21T12:00:00Z",
        summary="요약",
        last_covered_run="a/b",
        model="m",
        input_tokens=1,
        output_tokens=1,
    )

    assert isinstance(started, RunStarted)
    assert started.previous_run == "../etc"
    assert isinstance(summarized, ConversationSummarized)
    assert summarized.last_covered_run == "a/b"


def test_대화_요약_이벤트는_글과_덮는_끝과_모델과_토큰_수를_담고_왕복한다() -> None:
    event = ConversationSummarized(
        run_id=RunId("r2"),
        ts=TS,
        summary="요청한 쪽이 2+2 를 물었고 에이전트가 4 라고 답했다",
        last_covered_run=RunId("r1"),
        model="fake-model",
        input_tokens=70,
        output_tokens=30,
    )

    assert _round_trip(event) == event
    assert event.type == "conversation_summarized"


@pytest.mark.parametrize(
    "missing", ["summary", "last_covered_run", "model", "input_tokens", "output_tokens"]
)
def test_대화_요약_이벤트의_필드는_전부_필수다(missing: str) -> None:
    complete: dict[str, Json] = {
        "type": "conversation_summarized",
        "run_id": "r2",
        "ts": "2026-09-21T12:00:00Z",
        "summary": "요약",
        "last_covered_run": "r1",
        "model": "m",
        "input_tokens": 1,
        "output_tokens": 1,
    }

    with pytest.raises(ValidationError):
        TypeAdapter[Event](Event).validate_python(
            {key: value for key, value in complete.items() if key != missing}
        )


def test_직렬화_스키마에서_새_필드와_새_이벤트의_필드가_required_다() -> None:
    """서버는 필드를 언제나 전부 싣는다. 기본값 있는 `previous_run` 이 required 에서 빠지면 생성
    클라이언트가 그것을 선택 필드로 받는다(ADR 0022)."""
    # 직렬화 쪽 JSON 스키마. 관리 API 와 openapi.json 이 보는 그것이다.
    defs = TypeAdapter[Event](Event).json_schema(mode="serialization")["$defs"]

    for name in ("RunStarted", "ConversationSummarized"):
        assert set(defs[name]["required"]) == set(defs[name]["properties"]), name
    previous = defs["RunStarted"]["properties"]["previous_run"]
    assert previous["anyOf"] == [{"type": "string"}, {"type": "null"}]
    assert previous["default"] is None
