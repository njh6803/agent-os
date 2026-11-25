"""대화 목록을 묶는 순수 함수. 어댑터는 실행마다 기록을 만들어 넘기고 묶는 규칙은 여기 한 곳이다.

한 줄은 갈라진 끝 하나다. 끝에서 앞 실행을 거슬러 올라 첫 실행을 고르고, 끊긴 고리에서는 멈춰
`complete` 를 거짓으로 둔다. 이어 가기의 판정(주체, 끝남)은 다시 하지 않는다.
"""

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime, timedelta

import pytest

from agent_os.core import conversations
from agent_os.core.conversations import FIRST_REQUEST_LENGTH, list_conversations
from agent_os.core.ports import (
    DEFAULT_LIMIT,
    MAX_LIMIT,
    ConversationLine,
    ConversationRow,
    Cursor,
    RunRecord,
    RunStatus,
    RunSummary,
    UnreadableTrace,
    cursor_of,
)
from agent_os.sdk import AgentName, Principal, RunId

T0 = datetime(2026, 11, 26, 9, 0, tzinfo=UTC)


def _run(
    run_id: str,
    *,
    previous: str | None = None,
    at: datetime = T0,
    last_at: datetime | None = None,
    status: RunStatus = "finished",
    agent: str = "calc",
    request: str = "2+2?",
    account: str | None = None,
    principal: str = "alice",
) -> RunRecord:
    return RunRecord(
        summary=RunSummary(
            run_id=RunId(run_id),
            status=status,
            schema_version="3",
            started_at=at,
            last_at=at if last_at is None else last_at,
            agent=AgentName(agent),
            principal=Principal(principal),
        ),
        previous_run=None if previous is None else RunId(previous),
        request=request,
        requesting_account=account,
    )


def _lines(rows: Sequence[ConversationRow]) -> list[ConversationLine]:
    """행 전부가 대화 줄임을 확인하며 좁힌다. 표지가 섞이면 그 자리에서 실패한다."""
    lines = [row for row in rows if isinstance(row, ConversationLine)]
    assert len(lines) == len(rows)
    return lines


def _ends(rows: Sequence[ConversationRow]) -> list[str]:
    return [row.run_id if isinstance(row, UnreadableTrace) else row.last_run for row in rows]


def test_이어_가지_않은_실행_하나는_실행_수_1인_대화_한_줄이다() -> None:
    rows = list_conversations(
        [_run("solo", account="kim", request="안녕", last_at=T0 + timedelta(minutes=3))]
    )

    (line,) = _lines(rows)
    assert line == ConversationLine(
        last_run=RunId("solo"),
        status="finished",
        agent=AgentName("calc"),
        first_request="안녕",
        requesting_account="kim",
        principal=Principal("alice"),
        run_count=1,
        last_started_at=T0,
        last_at=T0 + timedelta(minutes=3),
        complete=True,
    )


def test_이어_간_실행들은_끝_실행_하나의_줄로_묶이고_첫_실행의_요청과_계정을_싣는다() -> None:
    rows = list_conversations(
        [
            _run("a", at=T0, request="처음 질문", account="kim", principal="p-first"),
            _run(
                "b",
                previous="a",
                at=T0 + timedelta(minutes=1),
                request="둘째",
                account="park",
                principal="p-second",
            ),
            _run(
                "c",
                previous="b",
                at=T0 + timedelta(minutes=2),
                request="셋째",
                account="lee",
                agent="writer",
                status="failed",
                principal="p-third",
                last_at=T0 + timedelta(minutes=9),
            ),
        ]
    )

    (line,) = _lines(rows)
    assert line.last_run == "c"
    assert line.run_count == 3
    assert line.complete is True
    # 끝 실행에서 오는 칸
    assert (line.status, line.agent) == ("failed", "writer")
    assert line.last_started_at == T0 + timedelta(minutes=2)
    assert line.last_at == T0 + timedelta(minutes=9)
    # 첫 실행에서 오는 칸
    assert line.first_request == "처음 질문"
    assert line.requesting_account == "kim"
    assert line.principal == "p-first"


def test_같은_실행을_둘이_이어_가면_끝마다_한_줄이고_첫_요청이_같다() -> None:
    rows = list_conversations(
        [
            _run("root", request="공통 질문"),
            _run("left", previous="root", at=T0 + timedelta(minutes=1)),
            _run("right", previous="root", at=T0 + timedelta(minutes=2)),
        ]
    )

    lines = _lines(rows)
    assert [line.last_run for line in lines] == ["right", "left"]
    assert [line.run_count for line in lines] == [2, 2]
    assert [line.first_request for line in lines] == ["공통 질문", "공통 질문"]


def test_앞_실행이_없는_고리는_거기서_멈추고_완전하지_않다() -> None:
    """지운 트레이스다. 첫 실행은 멈추기 전에 읽힌 가장 오래된 실행이다."""
    rows = list_conversations(
        [
            _run("b", previous="gone", request="읽힌 가장 오래된 요청", account="kim"),
            _run("c", previous="b", at=T0 + timedelta(minutes=1)),
        ]
    )

    (line,) = _lines(rows)
    assert (line.last_run, line.run_count, line.complete) == ("c", 2, False)
    assert line.first_request == "읽힌 가장 오래된 요청"
    assert line.requesting_account == "kim"


def test_읽히지_않는_앞_실행에서도_멈추고_그_표지는_맨_뒤에_따로_선다() -> None:
    rows = list_conversations(
        [
            _run("b", previous="broken"),
            UnreadableTrace(run_id=RunId("broken"), reason="깨졌다"),
        ]
    )

    assert _ends(rows) == ["b", "broken"]
    line = rows[0]
    assert isinstance(line, ConversationLine)
    assert (line.run_count, line.complete) == (1, False)
    assert rows[1] == UnreadableTrace(run_id=RunId("broken"), reason="깨졌다")


def test_손상된_기록의_순환은_이미_지난_실행에서_멈춘다() -> None:
    """끝 c 가 b 를 가리키고 b 와 a 가 서로를 가리킨다. a 에서 b 로 돌아오는 자리에서 멈춘다."""
    rows = list_conversations(
        [
            _run("a", previous="b"),
            _run("b", previous="a"),
            _run("c", previous="b", at=T0 + timedelta(minutes=1)),
        ]
    )

    (line,) = _lines(rows)
    assert line.last_run == "c"
    assert (line.run_count, line.complete) == (3, False)


def test_자기_자신을_앞_실행으로_가리키는_실행도_끝으로_한_줄이_선다() -> None:
    rows = list_conversations([_run("loop", previous="loop")])

    (line,) = _lines(rows)
    assert (line.last_run, line.run_count, line.complete) == ("loop", 1, False)


def test_줄은_끝_실행의_시작_시각이_늦은_차례이고_같으면_식별자가_큰_쪽이_먼저다() -> None:
    rows = list_conversations(
        [
            _run("m", at=T0),
            _run("x", at=T0),
            _run("late", at=T0 + timedelta(hours=1)),
            _run("early", at=T0 - timedelta(hours=1)),
        ]
    )

    assert _ends(rows) == ["late", "x", "m", "early"]


def test_이어_가기가_생겨_끝이_바뀐_대화는_새_끝의_시작_시각으로_맨_위에_선다() -> None:
    old = [_run("old", at=T0), _run("other", at=T0 + timedelta(minutes=1))]
    assert _ends(list_conversations(old)) == ["other", "old"]

    continued = [*old, _run("old-2", previous="old", at=T0 + timedelta(minutes=5))]
    assert _ends(list_conversations(continued)) == ["old-2", "other"]


def test_status_는_끝_실행의_상태로_거르고_표지도_함께_뺀다() -> None:
    records = [
        _run("a", status="paused"),
        _run("b", previous="a", status="finished", at=T0 + timedelta(minutes=1)),
        _run("c", status="paused", at=T0 + timedelta(minutes=2)),
        UnreadableTrace(run_id=RunId("broken"), reason="깨졌다"),
    ]

    assert _ends(list_conversations(records, status="paused")) == ["c"]
    assert _ends(list_conversations(records, status="finished")) == ["b"]
    assert _ends(list_conversations(records)) == ["c", "b", "broken"]


def test_첫_요청은_파이썬의_글자_수로_앞_120자만_싣는다() -> None:
    assert FIRST_REQUEST_LENGTH == 120
    long = "가" * 119 + "나다라"

    (line,) = _lines(list_conversations([_run("a", request=long)]))
    assert line.first_request == "가" * 119 + "나"

    (exact,) = _lines(list_conversations([_run("a", request="가" * 120)]))
    assert exact.first_request == "가" * 120

    # BMP 밖의 글자(이모지)도 한 글자로 센다. UTF-16 단위로 세면 59자에서 잘린다.
    (emoji,) = _lines(list_conversations([_run("a", request="🙂" * 121)]))
    assert emoji.first_request == "🙂" * 120


def test_limit_로_자르고_커서는_끝_실행의_정렬_키_그대로다() -> None:
    records = [_run(f"r{n}", at=T0 + timedelta(minutes=n)) for n in range(5)]

    first = list_conversations(records, limit=2)
    assert _ends(first) == ["r4", "r3"]
    cursor = cursor_of(first[-1])
    assert cursor == Cursor(started_at=T0 + timedelta(minutes=3), run_id=RunId("r3"))

    second = list_conversations(records, limit=2, after=cursor)
    assert _ends(second) == ["r2", "r1"]
    third = list_conversations(records, limit=2, after=cursor_of(second[-1]))
    assert _ends(third) == ["r0"]


def test_거슬러_오르기는_고른_쪽과_상태에_맞는_끝_실행에만_돈다(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    records = [
        _run(f"r{n}", at=T0 + timedelta(minutes=n), status="failed" if n == 1 else "finished")
        for n in range(5)
    ]
    built: list[RunId] = []
    original = getattr(conversations, "_line")  # noqa: B009 비공개 함수에 호출 세는 껍질을 씌운다

    def counting(end: RunRecord, by_id: Mapping[RunId, RunRecord]) -> ConversationLine:
        built.append(end.summary.run_id)
        line: ConversationLine = original(end, by_id)
        return line

    monkeypatch.setattr(conversations, "_line", counting)

    assert _ends(list_conversations(records, limit=2)) == ["r4", "r3"]
    assert built == ["r4", "r3"]

    built.clear()
    assert _ends(list_conversations(records, status="failed")) == ["r1"]
    assert built == ["r1"]


def test_같은_시작_시각에서도_커서가_쪽을_겹치거나_빠뜨리지_않는다() -> None:
    records = [_run(run_id, at=T0) for run_id in ("a", "b", "c", "d", "e")]

    seen: list[str] = []
    after: Cursor | None = None
    while True:
        page = list_conversations(records, limit=2, after=after)
        if not page:
            break
        seen.extend(_ends(page))
        after = cursor_of(page[-1])

    assert seen == ["e", "d", "c", "b", "a"]


def test_표지에서_이어지는_커서는_시각이_없고_표지끼리는_식별자로_갈린다() -> None:
    records: list[RunRecord | UnreadableTrace] = [
        _run("ok"),
        UnreadableTrace(run_id=RunId("bad-1"), reason="x"),
        UnreadableTrace(run_id=RunId("bad-2"), reason="x"),
    ]

    page = list_conversations(records, limit=2)
    assert _ends(page) == ["ok", "bad-2"]
    assert _ends(list_conversations(records, limit=2, after=cursor_of(page[-1]))) == ["bad-1"]


def test_limit_의_기본값은_50이고_범위_밖이면_ValueError다() -> None:
    records = [_run(f"r{n:03}", at=T0 + timedelta(seconds=n)) for n in range(DEFAULT_LIMIT + 5)]

    assert len(list_conversations(records)) == DEFAULT_LIMIT
    for bad in (0, -1, MAX_LIMIT + 1):
        with pytest.raises(ValueError, match="limit"):
            list_conversations(records, limit=bad)


def test_빈_입력은_빈_목록이다() -> None:
    assert list_conversations([]) == ()
