"""JSONL TraceStore. 한 줄에 JSON 하나, 첫 줄은 헤더, 모르는 종류는 원문 보존, 한 실행을 읽는다.

목록은 디렉터리의 실행들을 요약으로 돌려주고 읽히지 않는 파일은 표지로 남긴다.
"""

import json
from collections.abc import Sequence
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from agent_os.adapters.jsonl import JsonlTrace
from agent_os.core.ports import (
    DEFAULT_LIMIT,
    MAX_LIMIT,
    Cursor,
    PluginError,
    RunRow,
    RunSummary,
    TraceStore,
    UnknownEvent,
    UnreadableTrace,
    cursor_of,
)
from agent_os.sdk import (
    AgentName,
    ApprovalGranted,
    Event,
    LlmCalled,
    Principal,
    RunFailed,
    RunFinished,
    RunId,
    RunPaused,
    RunResumed,
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
    store: TraceStore = JsonlTrace(tmp_path / "traces")

    for event in _events("run-1") + _events("run-2"):
        store.write(event)

    assert sorted(p.name for p in (tmp_path / "traces").iterdir()) == [
        "run-1.jsonl",
        "run-2.jsonl",
    ]


def test_첫_줄은_형식_버전과_실행_식별자를_담은_헤더이고_다음_줄부터_이벤트다(
    tmp_path: Path,
) -> None:
    store: TraceStore = JsonlTrace(tmp_path)
    events = _events("run-1")

    for event in events:
        store.write(event)

    lines = (tmp_path / "run-1.jsonl").read_text(encoding="utf-8").splitlines()
    assert json.loads(lines[0]) == {"schema_version": "2", "run_id": "run-1"}
    assert lines[1:] == [event.model_dump_json() for event in events]


def test_쓴_것을_다시_읽으면_넣은_이벤트와_같다(tmp_path: Path) -> None:
    store: TraceStore = JsonlTrace(tmp_path)
    events = _events("run-1")
    for event in events:
        store.write(event)

    trace = store.read(RunId("run-1"))

    assert trace is not None
    assert trace.run_id == "run-1"
    assert trace.schema_version == "2"
    assert list(trace.events) == events


def test_여러_실행이_섞여_쓰여도_한_실행의_이벤트만_쓴_순서대로_돌려준다(tmp_path: Path) -> None:
    store: TraceStore = JsonlTrace(tmp_path)
    first, second = _events("run-1"), _events("run-2")
    for event in (first[0], second[0], first[1], second[1]):
        store.write(event)

    trace = store.read(RunId("run-1"))

    assert trace is not None
    assert list(trace.events) == first


def test_쓴_적_없는_실행을_읽으면_None_이다(tmp_path: Path) -> None:
    store: TraceStore = JsonlTrace(tmp_path)

    assert store.read(RunId("ghost")) is None


def test_모르는_종류의_이벤트가_섞여_있어도_원문이_보존된다(tmp_path: Path) -> None:
    store: TraceStore = JsonlTrace(tmp_path)
    started, finished = _events("run-1")
    store.write(started)
    future = '{"type":"run_rewound","run_id":"run-1","ts":"2026-09-21T12:00:00Z","to":"x"}'
    with (tmp_path / "run-1.jsonl").open("a", encoding="utf-8") as f:
        f.write(future + "\n")
    store.write(finished)

    trace = store.read(RunId("run-1"))

    assert trace is not None
    assert list(trace.events) == [started, UnknownEvent(raw=future), finished]


# 형식 1 로 쓰인 트레이스. 재개의 입력이 되는 필드가 아직 없다.
_V1_TRACE = (
    '{"schema_version":"1","run_id":"old"}\n'
    '{"type":"llm_called","run_id":"old","ts":"2026-09-21T12:00:00Z",'
    '"model":"m","input_tokens":7,"output_tokens":3}\n'
)


def test_형식_1_트레이스도_읽히고_읽은_결과가_버전_1임을_말한다(tmp_path: Path) -> None:
    (tmp_path / "old.jsonl").write_text(_V1_TRACE, encoding="utf-8")
    store: TraceStore = JsonlTrace(tmp_path)

    trace = store.read(RunId("old"))

    assert trace is not None
    assert trace.schema_version == "1"
    event = trace.events[0]
    assert isinstance(event, LlmCalled)
    assert event.text == ""
    assert event.tool_calls == ()


def test_두꺼워진_이벤트가_파일에_그대로_남고_다시_읽힌다(tmp_path: Path) -> None:
    store: TraceStore = JsonlTrace(tmp_path)
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
        store.write(event)

    trace = store.read(RunId("run-1"))

    assert trace is not None
    assert list(trace.events) == events


def _started(run_id: str, at: datetime) -> RunStarted:
    return RunStarted(
        run_id=RunId(run_id),
        ts=at,
        agent=AgentName("calc"),
        request="2+2?",
        principal=Principal("alice"),
    )


def _write_trace(
    store: TraceStore, run_id: str, *, at: datetime = TS, ending: Event | None = None
) -> None:
    """실행 하나를 쓴다. ending 이 없으면 시작 이벤트만 있는 결말 없는 실행이다."""
    store.write(_started(run_id, at))
    if ending is not None:
        store.write(ending)


def _ids(rows: Sequence[RunRow]) -> list[str]:
    return [row.run_id for row in rows]


def _summaries(rows: Sequence[RunRow]) -> list[RunSummary]:
    """행 전부가 요약임을 확인하며 좁힌다. 표지가 섞이면 그 자리에서 실패한다."""
    summaries = [row for row in rows if isinstance(row, RunSummary)]
    assert len(summaries) == len(rows)
    return summaries


def test_실행들을_시작_시각_역순으로_돌려준다(tmp_path: Path) -> None:
    store: TraceStore = JsonlTrace(tmp_path)
    _write_trace(store, "older", at=TS)
    _write_trace(store, "newer", at=TS + timedelta(minutes=5))
    _write_trace(store, "newest", at=TS + timedelta(minutes=9))

    assert _ids(store.list()) == ["newest", "newer", "older"]


def test_시작_시각이_같으면_실행_식별자로_갈린다(tmp_path: Path) -> None:
    store: TraceStore = JsonlTrace(tmp_path)
    for run_id in ("run-a", "run-c", "run-b"):
        _write_trace(store, run_id, at=TS)

    assert _ids(store.list()) == ["run-c", "run-b", "run-a"]


def test_마지막_이벤트가_일시정지_끝남_실패이면_상태도_각각_그것이다(tmp_path: Path) -> None:
    store: TraceStore = JsonlTrace(tmp_path)
    _write_trace(
        store, "paused", at=TS, ending=RunPaused(run_id=RunId("paused"), ts=TS, tool="x", args={})
    )
    _write_trace(
        store,
        "finished",
        at=TS + timedelta(minutes=1),
        ending=RunFinished(run_id=RunId("finished"), ts=TS, output="4"),
    )
    _write_trace(
        store,
        "failed",
        at=TS + timedelta(minutes=2),
        ending=RunFailed(run_id=RunId("failed"), ts=TS, error="터졌다"),
    )

    rows = _summaries(store.list())

    assert [(row.run_id, row.status) for row in rows] == [
        ("failed", "failed"),
        ("finished", "finished"),
        ("paused", "paused"),
    ]


def test_끝_이벤트가_없는_실행은_결말_없음이다(tmp_path: Path) -> None:
    """진행 중이라 부르지 않는다. 돌고 있는 실행과 죽어 사라진 실행이 파일에서 같다."""
    store: TraceStore = JsonlTrace(tmp_path)
    _write_trace(store, "run-1")

    rows = _summaries(store.list())

    assert [row.status for row in rows] == ["unfinished"]


def test_마지막_이벤트가_모르는_종류여도_결말_없음이다(tmp_path: Path) -> None:
    """그 줄은 읽히므로 표지가 아니라 요약이다. 다섯째 상태 값을 만들지 않는다(ADR 0012 이력)."""
    store: TraceStore = JsonlTrace(tmp_path)
    _write_trace(store, "run-1")
    with (tmp_path / "run-1.jsonl").open("a", encoding="utf-8") as file:
        file.write('{"type":"run_rewound","run_id":"run-1","ts":"2026-09-21T12:00:00Z","to":"x"}\n')

    rows = _summaries(store.list())

    assert [(row.run_id, row.status) for row in rows] == [("run-1", "unfinished")]


def test_status가_그_상태의_실행만_남긴다(tmp_path: Path) -> None:
    """승인자가 멈춘 실행을 찾는 길이 이 질의 하나다. 별도 경로가 아니다."""
    store: TraceStore = JsonlTrace(tmp_path)
    _write_trace(
        store, "paused", at=TS, ending=RunPaused(run_id=RunId("paused"), ts=TS, tool="x", args={})
    )
    _write_trace(
        store,
        "finished",
        at=TS + timedelta(minutes=1),
        ending=RunFinished(run_id=RunId("finished"), ts=TS, output="4"),
    )

    assert _ids(store.list(status="paused")) == ["paused"]


def test_limit이_개수를_자른다(tmp_path: Path) -> None:
    store: TraceStore = JsonlTrace(tmp_path)
    for index in range(4):
        _write_trace(store, f"run-{index}", at=TS + timedelta(minutes=index))

    assert _ids(store.list(limit=2)) == ["run-3", "run-2"]


def test_after로_다음_쪽을_받으면_겹치지도_빠지지도_않는다(tmp_path: Path) -> None:
    store: TraceStore = JsonlTrace(tmp_path)
    for index in range(5):
        _write_trace(store, f"run-{index}", at=TS + timedelta(minutes=index))
    everything = _ids(store.list())

    pages: list[str] = []
    cursor: Cursor | None = None
    while True:
        page = store.list(limit=2, after=cursor)
        if not page:
            break
        pages.extend(_ids(page))
        cursor = cursor_of(page[-1])

    assert pages == everything


def test_쪽_사이에_새_실행이_생겨도_있던_실행이_두_번_오거나_빠지지_않는다(tmp_path: Path) -> None:
    """오프셋과 커서를 가르는 성질이다. 새 실행은 머리에 서므로 다음 첫 쪽에서 보인다."""
    store: TraceStore = JsonlTrace(tmp_path)
    for index in range(5):
        _write_trace(store, f"run-{index}", at=TS + timedelta(minutes=index))
    everything = _ids(store.list())

    first = store.list(limit=2)
    _write_trace(store, "run-new", at=TS + timedelta(hours=1))
    rest = store.list(after=cursor_of(first[-1]))

    assert _ids(first) + _ids(rest) == everything
    assert _ids(store.list(limit=1)) == ["run-new"]


# 알려진 한계 둘(ADR 0012 의 2026-09-23 이력). 정렬 키가 쓰기 순서가 아니라 시작 시각이라, 한 순회가
# 이미 지나간 키 범위에 나중에 들어온 실행은 그 순회에서 보이지 않는다. 받아들인 한계라 테스트가
# 지금의 동작을 고정한다 — 고치는 날 빨개지고 그때 이력을 함께 고친다. 셋째 길(순회 도중 키가 바뀐
# 행)은 개행을 커밋 표지로 보며 닫혔고 아래의 뒤집힌 테스트가 그것을 지킨다.


def test_알려진_한계_지나간_범위에_늦게_나타난_파일은_그_순회에서_빠진다(tmp_path: Path) -> None:
    """`run()` 이 시각을 읽은 직후 같은 호출에서 파일을 만들므로 실행 프로세스가 하나면 생기지
    않는다. 벽시계가 뒤로 가거나 동시에 도는 실행 둘이 그 사이에서 엇갈릴 때의 모양이다."""
    store: TraceStore = JsonlTrace(tmp_path)
    for name, minutes in (("run-a", 0), ("run-b", 2), ("run-c", 4)):
        _write_trace(store, name, at=TS + timedelta(minutes=minutes))

    first = store.list(limit=2)
    _write_trace(store, "run-late", at=TS + timedelta(minutes=3))
    rest = store.list(after=cursor_of(first[-1]))

    assert _ids(first) + _ids(rest) == ["run-c", "run-b", "run-a"]
    assert "run-late" in _ids(store.list())


def test_알려진_한계_재개된_옛_실행이_다시_멈추면_멈춘_실행_순회에서_빠진다(tmp_path: Path) -> None:
    """실행 프로세스가 하나여도 생긴다. 한 턴에 승인 대상이 둘이면 재개한 뒤 둘째에서 다시 멈추는데,
    그 사이 결말 없음이던 실행이 오래된 시작 시각 그대로 필터에 돌아온다."""
    store: TraceStore = JsonlTrace(tmp_path)
    for name, minutes in (("run-a", 0), ("run-b", 2), ("run-c", 4)):
        _write_trace(
            store,
            name,
            at=TS + timedelta(minutes=minutes),
            ending=RunPaused(run_id=RunId(name), ts=TS, tool="add", args={}),
        )
    store.write(ApprovalGranted(run_id=RunId("run-b"), ts=TS, approver=Principal("bob")))
    store.write(RunResumed(run_id=RunId("run-b"), ts=TS))

    first = store.list(status="paused", limit=1)
    second = store.list(status="paused", limit=1, after=cursor_of(first[-1]))
    store.write(RunPaused(run_id=RunId("run-b"), ts=TS, tool="add", args={}))
    rest = store.list(status="paused", after=cursor_of(second[-1]))

    assert _ids(first) + _ids(second) + _ids(rest) == ["run-c", "run-a"]
    assert _ids(store.list(status="paused")) == ["run-c", "run-b", "run-a"]


def test_쓰는_중인_마지막_줄이_있어도_순회가_같은_실행을_두_번_세지_않는다(tmp_path: Path) -> None:
    """알려진 한계였던 셋째 길을 뒤집은 것이다. 반만 쓰인 마지막 줄은 아직 쓰이지 않은 것이라 그 앞
    줄로 요약하므로 행이 표지가 되어 꼬리로 가지 않는다. 한 번에 쓴 줄도 리눅스에서는 읽는 쪽에
    반쪽으로 보여 실행 프로세스가 하나여도 생기던 길이다(ADR 0012 의 2026-09-23 이력 둘째)."""
    store: TraceStore = JsonlTrace(tmp_path)
    for name, minutes in (("run-a", 0), ("run-b", 2), ("run-c", 4)):
        _write_trace(store, name, at=TS + timedelta(minutes=minutes))

    first = store.list(limit=1)
    finished = RunFinished(run_id=RunId("run-c"), ts=TS, output="4").model_dump_json()
    with (tmp_path / "run-c.jsonl").open("a", encoding="utf-8") as file:
        file.write(finished[: len(finished) // 2])
    rest = store.list(after=cursor_of(first[-1]))

    assert _ids(first) + _ids(rest) == ["run-c", "run-b", "run-a"]
    assert [row.status for row in _summaries(store.list())] == ["unfinished"] * 3


def test_limit을_주지_않으면_기본값까지만_돌려준다(tmp_path: Path) -> None:
    store: TraceStore = JsonlTrace(tmp_path)
    for index in range(DEFAULT_LIMIT + 1):
        _write_trace(store, f"run-{index:03d}", at=TS)

    assert len(store.list()) == DEFAULT_LIMIT


def test_상한을_넘거나_영_이하인_limit은_거부한다(tmp_path: Path) -> None:
    """상한이 없으면 요청 하나가 "실행이 쌓여도 응답이 그만큼 커지지 않는다"를 무력화한다."""
    store: TraceStore = JsonlTrace(tmp_path)

    with pytest.raises(ValueError, match=str(MAX_LIMIT)):
        store.list(limit=MAX_LIMIT + 1)
    with pytest.raises(ValueError, match="1"):
        store.list(limit=0)


def test_형식_1_트레이스도_목록에_나오고_요약이_형식_버전_1을_싣는다(tmp_path: Path) -> None:
    """읽기는 되고 재개만 안 된다. 화면이 "이 실행은 재개할 수 없다"를 말할 수 있어야 한다."""
    (tmp_path / "old.jsonl").write_text(
        '{"schema_version":"1","run_id":"old"}\n' + _started("old", TS).model_dump_json() + "\n",
        encoding="utf-8",
    )
    store: TraceStore = JsonlTrace(tmp_path)

    rows = _summaries(store.list())

    assert [(row.run_id, row.schema_version) for row in rows] == [("old", "1")]


def test_요약의_시각_둘은_시작_이벤트와_마지막_이벤트에서_온다(tmp_path: Path) -> None:
    """마지막 시각이 방치를 알아보는 유일한 길이다. 일시정지에 만료가 없기 때문이다."""
    store: TraceStore = JsonlTrace(tmp_path)
    last_at = TS + timedelta(hours=3)
    _write_trace(
        store, "run-1", at=TS, ending=RunFinished(run_id=RunId("run-1"), ts=last_at, output="4")
    )

    row = store.list()[0]

    assert isinstance(row, RunSummary)
    assert (row.started_at, row.last_at) == (TS, last_at)


def test_요약은_에이전트_이름과_주체를_싣고_필드가_일곱이다(tmp_path: Path) -> None:
    """프롬프트와 토큰 수와 출력과 이벤트는 요약에 없다. 목록은 개요를 보는 자리다."""
    store: TraceStore = JsonlTrace(tmp_path)
    _write_trace(store, "run-1")

    row = store.list()[0]

    assert isinstance(row, RunSummary)
    assert (row.agent, row.principal) == ("calc", "alice")
    assert set(vars(row)) == {
        "run_id",
        "status",
        "schema_version",
        "started_at",
        "last_at",
        "agent",
        "principal",
    }


def test_빈_디렉터리와_없는_디렉터리가_빈_목록이다(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()

    assert JsonlTrace(empty).list() == ()
    assert JsonlTrace(tmp_path / "없다").list() == ()


# 읽히지 않는 모양 다섯. 사람이 손을 대거나, 새 줄이 조각에 붙거나, 새 실행의 첫 쓰기가 닿기 전에
# 프로세스가 죽으면 생길 수 있는 것들이다. 끝나지 않은 마지막 줄은 손상이 아니라 아직 쓰이지 않은
# 것이므로(ADR 0012 의 2026-09-23 이력 둘째) 커밋된 줄이 깨지거나 커밋된 헤더가 없어야 손상이다.
_BROKEN: dict[str, bytes] = {
    "bad-header": b'{"schema_version":"9","run_id":"bad-header"}\n',
    "broken-line": b'{"schema_version":"2","run_id":"broken-line"}\n{"type":"run_star\n',
    "empty-file": b"",
    "header-fragment": b'{"schema_version":"2","run_id":"head',
    "not-utf8": b'{"schema_version":"2","run_id":"not-utf8"}\n\xff\xfe\x00\n',
}


def _write_broken(directory: Path) -> None:
    for run_id, content in _BROKEN.items():
        (directory / f"{run_id}.jsonl").write_bytes(content)


def test_읽을_수_없는_트레이스가_표지로_남고_나머지_목록은_돌아온다(tmp_path: Path) -> None:
    """깨진 파일 하나가 /traces 전체를 죽이지 않는다. 표지는 요약 뒤에 모인다."""
    store: TraceStore = JsonlTrace(tmp_path)
    _write_trace(store, "fine")
    _write_broken(tmp_path)

    rows = store.list()

    assert _ids(rows[:1]) == ["fine"]
    assert isinstance(rows[0], RunSummary)
    assert sorted(_ids(rows[1:])) == sorted(_BROKEN)
    assert all(isinstance(row, UnreadableTrace) and row.reason for row in rows[1:])


def test_표지는_status_질의에서_함께_빠진다(tmp_path: Path) -> None:
    """표지는 상태가 없다. 승인자의 멈춘 실행 목록에 섞여 들어오지 않는다."""
    store: TraceStore = JsonlTrace(tmp_path)
    _write_trace(
        store, "paused", at=TS, ending=RunPaused(run_id=RunId("paused"), ts=TS, tool="x", args={})
    )
    _write_broken(tmp_path)

    assert _ids(store.list(status="paused")) == ["paused"]


def test_같은_손상_파일을_단건으로_읽으면_PluginError다(tmp_path: Path) -> None:
    """목록과 단건의 비대칭이 의도다. 단건은 그 파일 하나를 달라는 요청이라 실패가 곧 답이다.

    포장하지 않으면 pydantic 검증 오류와 IndexError 와 UnicodeDecodeError 가 그대로 올라와
    채널의 `except PluginError` 를 지나친다(ADR 0012 이력).
    """
    _write_broken(tmp_path)
    store: TraceStore = JsonlTrace(tmp_path)

    for run_id in _BROKEN:
        with pytest.raises(PluginError, match=run_id):
            store.read(RunId(run_id))


def test_읽을_수_없는_이유가_트레이스_줄의_내용을_되울리지_않는다(tmp_path: Path) -> None:
    """목록은 내용을 읽는 자리가 아니다(스토리 15). pydantic 의 검증 문구는 받은 값의 앞뒤를 싣는데,
    커밋된 줄이 깨졌으면 그 내용이 곧 도구 결과다. 경로와 오류 종류는 운영자가 파일을 찾고 원인을
    짐작하는 값이라 남긴다(PR #56 의 CodeRabbit 지적). 조각이 개행으로 끝나는 이유는 끝나지 않은
    줄이 손상이 아니라 아직 쓰이지 않은 것이기 때문이다(ADR 0012 의 2026-09-23 이력 둘째)."""
    store: TraceStore = JsonlTrace(tmp_path)
    _write_trace(store, "run-1")
    leaked = "tool-output-that-must-not-leak"
    called = ToolCalled(
        run_id=RunId("run-1"), ts=TS, tool="fetch", ok=True, args={}, content=leaked
    ).model_dump_json()
    with (tmp_path / "run-1.jsonl").open("a", encoding="utf-8") as file:
        file.write(called[: called.index(leaked) + len(leaked)] + "\n")

    row = store.list()[0]
    with pytest.raises(PluginError) as single:
        store.read(RunId("run-1"))

    assert isinstance(row, UnreadableTrace)
    for reason in (row.reason, str(single.value)):
        assert "must-not-leak" not in reason
        assert "run-1.jsonl" in reason
        assert "json_invalid" in reason


def test_파일_이름과_내용의_실행_식별자가_어긋나면_표지이고_단건은_PluginError다(
    tmp_path: Path,
) -> None:
    """파일 이름이 실행 식별자의 유일한 원천이다. 어긋난 파일이 남의 실행 정보를 이 식별자로
    내보내지 않는다. 재개 진입점이 같은 검사를 하지만 그쪽은 재개 경로 전용이다."""
    store: TraceStore = JsonlTrace(tmp_path)
    header_lies = '{"schema_version":"2","run_id":"other"}\n' + _started("a", TS).model_dump_json()
    (tmp_path / "header-lies.jsonl").write_text(header_lies + "\n", encoding="utf-8")
    event_lies = (
        '{"schema_version":"2","run_id":"event-lies"}\n' + _started("other", TS).model_dump_json()
    )
    (tmp_path / "event-lies.jsonl").write_text(event_lies + "\n", encoding="utf-8")

    rows = store.list()

    assert sorted(_ids(rows)) == ["event-lies", "header-lies"]
    assert all(isinstance(row, UnreadableTrace) for row in rows)
    for run_id in ("header-lies", "event-lies"):
        with pytest.raises(PluginError, match="실행 식별자"):
            store.read(RunId(run_id))


def test_모르는_종류의_이벤트도_파일_이름과_같은_실행을_말해야_한다(tmp_path: Path) -> None:
    """원문이 유효한 JSON 이라 식별자를 읽을 수 있다. 판별자만 모르는 줄이기 때문이다.

    이 검사가 없으면 남의 실행 이벤트가 이 식별자의 트레이스에 실리고, 그 줄이 마지막이면 그
    시각이 이 실행의 마지막 시각이 된다.
    """
    store: TraceStore = JsonlTrace(tmp_path)
    _write_trace(store, "run-a")
    intruder = '{"type":"run_rewound","run_id":"run-b","ts":"2026-09-21T13:00:00Z","to":"x"}'
    with (tmp_path / "run-a.jsonl").open("a", encoding="utf-8") as file:
        file.write(intruder + "\n")

    rows = store.list()

    assert [(row.run_id, isinstance(row, UnreadableTrace)) for row in rows] == [("run-a", True)]
    with pytest.raises(PluginError, match="run-b"):
        store.read(RunId("run-a"))


def test_실행_식별자가_없는_모르는_종류는_그대로_통과한다(tmp_path: Path) -> None:
    """식별자가 없는 줄은 남의 실행을 주장하지 않는다. 모르는 것을 지우지 않고 들고 있게 한다."""
    store: TraceStore = JsonlTrace(tmp_path)
    _write_trace(store, "run-a")
    nameless = '{"type":"run_rewound","ts":"2026-09-21T13:00:00Z","to":"x"}'
    with (tmp_path / "run-a.jsonl").open("a", encoding="utf-8") as file:
        file.write(nameless + "\n")

    row = store.list()[0]

    assert isinstance(row, RunSummary)
    assert (row.run_id, row.status) == ("run-a", "unfinished")
    trace = store.read(RunId("run-a"))
    assert trace is not None
    assert trace.events[-1] == UnknownEvent(raw=nameless)


def test_실행_식별자_패턴을_어기는_이름의_파일은_목록에서_빠진다(tmp_path: Path) -> None:
    """런타임이 만들 수 없는 이름이라 잃어버린 실행이 아니다. 되물을 수 없는 것을 싣지 않는다."""
    store: TraceStore = JsonlTrace(tmp_path)
    _write_trace(store, "fine")
    for name in ("두 낱말", "..", "-앞이하이픈", "a" * 65):
        (tmp_path / f"{name}.jsonl").write_bytes(_BROKEN["empty-file"])

    assert _ids(store.list()) == ["fine"]


def test_목록은_헤더와_첫_줄과_마지막_줄만_본다(tmp_path: Path) -> None:
    """단건 읽기를 재사용하면 파일마다 전부 파싱하고 limit 은 그 뒤에 자르므로 도움이 되지 않는다.

    가운데 줄이 깨진 파일의 요약이 그대로 나오는 것이 그 계약의 관찰 가능한 모양이다. 같은 파일을
    단건으로 읽으면 PluginError 이므로 손상이 조용히 사라지지도 않는다.
    """
    store: TraceStore = JsonlTrace(tmp_path)
    _write_trace(store, "run-1")
    path = tmp_path / "run-1.jsonl"
    path.write_text(path.read_text(encoding="utf-8") + '{"type":"쓰레기\n', encoding="utf-8")
    store.write(RunFinished(run_id=RunId("run-1"), ts=TS, output="4"))

    assert [(row.run_id, row.status) for row in _summaries(store.list())] == [("run-1", "finished")]
    with pytest.raises(PluginError):
        store.read(RunId("run-1"))


def test_목록은_가운데_줄을_디코딩하지도_않는다(tmp_path: Path) -> None:
    """가운데 줄이 UTF-8 이 아니어도 요약이다. 파싱하지 않는 줄을 디코딩할 이유가 없고, 손상은
    단건이 PluginError 로 말한다. 파일 전체를 텍스트로 읽던 때는 표지였다."""
    store: TraceStore = JsonlTrace(tmp_path)
    _write_trace(store, "run-1")
    with (tmp_path / "run-1.jsonl").open("ab") as file:
        file.write(b"\xff\xfe\x00\n")
    store.write(RunFinished(run_id=RunId("run-1"), ts=TS, output="4"))

    assert [(row.run_id, row.status) for row in _summaries(store.list())] == [("run-1", "finished")]
    with pytest.raises(PluginError):
        store.read(RunId("run-1"))


# 끝나지 않은 마지막 줄(ADR 0012 의 2026-09-23 이력 둘째). 개행이 한 줄의 커밋 표지라 개행으로
# 끝나지 않은 마지막 줄은 아직 쓰이지 않은 것이고, 목록과 단건 둘 다 그 앞 줄까지 읽는다. 쓰기는 그
# 뒤에 이어 쓰지 않는다. 쓰는 도중의 파일과 쓰다 죽은 파일이 같은 모양이다.


def _append_unterminated(path: Path, event: Event, cut: int) -> None:
    """이벤트 줄의 앞 cut 바이트만 쓴다. 개행은 쓰지 않는다."""
    with path.open("ab") as file:
        file.write(event.model_dump_json().encode()[:cut])


def test_끝나지_않은_마지막_줄은_목록이_그_앞_줄로_요약한다(tmp_path: Path) -> None:
    """표지가 아니다. 상태와 마지막 시각이 커밋된 마지막 줄에서 온다."""
    store: TraceStore = JsonlTrace(tmp_path)
    paused_at = TS + timedelta(minutes=1)
    paused = RunPaused(run_id=RunId("run-a"), ts=paused_at, tool="add", args={})
    _write_trace(store, "run-a", ending=paused)
    granted = ApprovalGranted(
        run_id=RunId("run-a"), ts=TS + timedelta(minutes=2), approver=Principal("bob")
    )
    _append_unterminated(tmp_path / "run-a.jsonl", granted, cut=20)

    [row] = _summaries(store.list())

    assert (row.status, row.last_at) == ("paused", paused_at)


def test_끝나지_않은_마지막_줄은_단건이_그_앞_줄까지_돌려준다(tmp_path: Path) -> None:
    """실행 중인 트레이스를 들여다보는 순간이 500 이 아니다. 티켓 06 은 500 을 파일이 깨졌다는
    신호로 정했으므로 쓰는 중인 파일에서 나면 그 신호가 거짓이 된다."""
    store: TraceStore = JsonlTrace(tmp_path)
    started = _started("run-a", TS)
    paused = RunPaused(run_id=RunId("run-a"), ts=TS, tool="add", args={})
    store.write(started)
    store.write(paused)
    granted = ApprovalGranted(run_id=RunId("run-a"), ts=TS, approver=Principal("bob"))
    _append_unterminated(tmp_path / "run-a.jsonl", granted, cut=20)

    trace = store.read(RunId("run-a"))

    assert trace is not None
    assert list(trace.events) == [started, paused]


def test_한글_한_글자의_가운데서_잘린_꼬리도_아직_쓰이지_않은_것이다(tmp_path: Path) -> None:
    """판정은 디코딩 전에 바이트로 한다. 텍스트로 먼저 읽으면 꼬리 하나 때문에 파일 전체가
    UnicodeDecodeError 가 된다."""
    store: TraceStore = JsonlTrace(tmp_path)
    started = _started("run-a", TS)
    store.write(started)
    finished = RunFinished(run_id=RunId("run-a"), ts=TS, output="결과는 넷")
    cut = finished.model_dump_json().encode().index("넷".encode()) + 1
    _append_unterminated(tmp_path / "run-a.jsonl", finished, cut=cut)

    [row] = _summaries(store.list())
    trace = store.read(RunId("run-a"))

    assert row.status == "unfinished"
    assert trace is not None
    assert list(trace.events) == [started]


def test_헤더_뒤_첫_줄이_끝나지_않은_파일은_목록에서_표지이고_단건은_이벤트가_없다(
    tmp_path: Path,
) -> None:
    """새 파일의 헤더와 큰 첫 이벤트가 두 번에 쓰이는 사이의 모양이다. 시작 이벤트가 아직 없어
    요약을 만들 수 없으므로 표지이고 단건은 헤더만 있는 트레이스다. 표지에서 요약으로 한 방향으로만
    바뀌고 요약은 머리에 서므로 한 순회에서 두 번 오지 않는다."""
    path = tmp_path / "run-a.jsonl"
    path.write_bytes(b'{"schema_version":"2","run_id":"run-a"}\n')
    _append_unterminated(path, _started("run-a", TS), cut=20)
    store: TraceStore = JsonlTrace(tmp_path)

    rows = store.list()
    trace = store.read(RunId("run-a"))

    assert [(row.run_id, isinstance(row, UnreadableTrace)) for row in rows] == [("run-a", True)]
    assert trace is not None
    assert trace.events == ()


def test_끝나지_않은_줄_뒤에는_이어_쓰지_않는다(tmp_path: Path) -> None:
    """새 줄이 조각에 붙으면 커밋된 손상 줄이 되어, 그 실행은 단건이 영구히 500 이고 다시 멈추면
    재개할 수 없다. 재개의 첫 쓰기를 쓰다 죽은 뒤 다시 재개하는 길이다. 파일은 한 바이트도 바뀌지
    않는다."""
    store: TraceStore = JsonlTrace(tmp_path)
    _write_trace(
        store, "run-a", ending=RunPaused(run_id=RunId("run-a"), ts=TS, tool="add", args={})
    )
    granted = ApprovalGranted(run_id=RunId("run-a"), ts=TS, approver=Principal("bob"))
    path = tmp_path / "run-a.jsonl"
    _append_unterminated(path, granted, cut=20)
    before = path.read_bytes()

    with pytest.raises(PluginError, match="run-a"):
        store.write(granted)

    assert path.read_bytes() == before


def test_비어_있는_파일은_새_파일처럼_헤더부터_쓴다(tmp_path: Path) -> None:
    """파일을 연 뒤 첫 쓰기가 디스크에 닿기 전에 프로세스가 죽으면 빈 파일이 남는다. 쓰인 것이
    없으므로 새 파일과 같고, 이어 붙일 조각도 없으므로 거부할 이유가 없다."""
    (tmp_path / "run-1.jsonl").write_bytes(b"")
    store: TraceStore = JsonlTrace(tmp_path)
    started, finished = _events("run-1")

    store.write(started)
    store.write(finished)

    trace = store.read(RunId("run-1"))
    assert trace is not None
    assert list(trace.events) == [started, finished]


def test_줄의_경계는_개행_하나라_문자열_안의_줄_구분_문자가_줄을_가르지_않는다(
    tmp_path: Path,
) -> None:
    """JSON 은 U+2028, U+2029, U+0085 를 문자열 안에 날것으로 허용하고 pydantic 도 그렇게 쓴다.
    `str.splitlines` 는 그 셋에서도 가르므로 멀쩡한 트레이스가 단건과 재개에서 손상이었다."""
    store: TraceStore = JsonlTrace(tmp_path)
    started = _started("run-1", TS)
    finished = RunFinished(run_id=RunId("run-1"), ts=TS, output="가\u2028나\u2029다\x85라")
    store.write(started)
    store.write(finished)

    trace = store.read(RunId("run-1"))

    assert trace is not None
    assert list(trace.events) == [started, finished]


def test_CRLF로_끝나는_줄도_같은_이벤트로_읽히고_원문에_CR이_남지_않는다(tmp_path: Path) -> None:
    """윈도우의 텍스트 모드 쓰기는 줄 끝을 CRLF 로 쓴다. 리눅스에서 도는 CI 도 그 파일을 같은
    이벤트로 읽어야 하고, 모르는 종류의 원문에 CR 이 붙으면 원문 보존이 아니다."""
    started, finished = _events("run-1")
    future = '{"type":"run_rewound","run_id":"run-1","ts":"2026-09-21T12:00:00Z","to":"x"}'
    lines = [
        '{"schema_version":"2","run_id":"run-1"}',
        started.model_dump_json(),
        future,
        finished.model_dump_json(),
    ]
    (tmp_path / "run-1.jsonl").write_bytes("".join(line + "\r\n" for line in lines).encode())
    store: TraceStore = JsonlTrace(tmp_path)

    trace = store.read(RunId("run-1"))
    [row] = _summaries(store.list())

    assert trace is not None
    assert list(trace.events) == [started, UnknownEvent(raw=future), finished]
    assert row.status == "finished"
