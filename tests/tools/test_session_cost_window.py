"""tools/session_cost_window.py 검증. `collect.py --since`의 창이 무엇을 창과 관계없이 보고 무엇을
창 안에서만 세는지.

턴은 `collect.py`가 넘기는 턴 머리(`TurnHead`)를 본뜬 합성 값이다(`_턴`). 창은 `_SINCE`이고,
테스트마다 창 앞·창 경계·창 안의 시각을 하나씩 쓴다.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

from tools.session_cost_window import (
    DIRECTIVE_MARK,
    TurnHead,
    cost_state_sessions,
    first_directive,
    first_humans,
    human_nondirective,
    in_window,
    parse_since,
)

_SINCE = datetime(2026, 10, 13, 4, 11, 21, tzinfo=UTC)
_BEFORE = "2026-10-13T04:11:20.999Z"
_AT = "2026-10-13T04:11:21.000Z"
_IN = "2026-10-14T00:00:00.000Z"
_LATER = "2026-10-15T00:00:00.000Z"
_DIRECTIVE = f"{DIRECTIVE_MARK} 하네스\n모델: Opus 5.5 / medium. 레벨 스윕의 갈래"


def _턴(
    start: str, trigger: str = "human", text: str = "고쳐 줘", branch: str = "chore/a"
) -> TurnHead:
    return TurnHead(start=start, branch=branch, trigger=trigger, text=text)


# --- parse_since, in_window ----------------------------------------------------------------------


def test_창이_없으면_None이다() -> None:
    assert parse_since(None) is None
    assert parse_since("") is None


def test_시각대_없는_창은_UTC로_본다() -> None:
    assert parse_since("2026-10-13T04:11:21") == _SINCE


def test_Z로_끝나는_창을_읽는다() -> None:
    assert parse_since("2026-10-13T04:11:21Z") == _SINCE


def test_시각대가_있는_창은_그대로_둔다() -> None:
    kst = timezone(timedelta(hours=9))
    assert parse_since("2026-10-13T13:11:21+09:00") == datetime(
        2026, 10, 13, 13, 11, 21, tzinfo=kst
    )


def test_창이_없으면_모든_시각이_창_안이다() -> None:
    assert in_window(_BEFORE, None)


def test_창의_시작_시각은_창_안이다() -> None:
    assert in_window(_AT, _SINCE)


def test_창_앞의_시각은_창_밖이다() -> None:
    assert not in_window(_BEFORE, _SINCE)


# --- first_humans --------------------------------------------------------------------------------


def test_첫_사람_트리거는_창_앞의_것까지_본다() -> None:
    turns = [_턴(_IN, text="둘째"), _턴(_BEFORE, text="첫째")]
    assert first_humans(turns) == {"chore/a": (_BEFORE, "첫째")}


def test_첫_사람_트리거는_사람의_턴만_본다() -> None:
    turns = [_턴(_BEFORE, trigger="auto"), _턴(_AT, trigger="interrupt"), _턴(_IN, text="사람")]
    assert first_humans(turns) == {"chore/a": (_IN, "사람")}


def test_첫_사람_트리거는_브랜치마다_정한다() -> None:
    turns = [_턴(_IN, branch="chore/a"), _턴(_LATER, branch="chore/b")]
    assert first_humans(turns) == {"chore/a": (_IN, "고쳐 줘"), "chore/b": (_LATER, "고쳐 줘")}


def test_귀속되지_않은_턴은_첫_사람_트리거가_되지_않는다() -> None:
    assert first_humans([_턴(_BEFORE, branch=""), _턴(_IN)]) == {"chore/a": (_IN, "고쳐 줘")}


def test_시작이_같으면_앞에_온_턴이_첫_트리거다() -> None:
    turns = [_턴(_IN, text="앞"), _턴(_IN, text="뒤")]
    assert first_humans(turns) == {"chore/a": (_IN, "앞")}


# --- first_directive -----------------------------------------------------------------------------


def test_첫_지시문은_창_안의_것만_본다() -> None:
    turns = [_턴(_BEFORE, text=_DIRECTIVE), _턴(_LATER, text=_DIRECTIVE), _턴(_IN, text=_DIRECTIVE)]
    assert first_directive(turns, _SINCE) == _IN


def test_첫_지시문은_귀속되지_않은_턴도_본다() -> None:
    assert first_directive([_턴(_IN, text=_DIRECTIVE, branch="")], _SINCE) == _IN


def test_사람이_아닌_턴의_지시문_표지는_첫_지시문이_아니다() -> None:
    assert first_directive([_턴(_IN, trigger="auto", text=_DIRECTIVE)], _SINCE) == ""


def test_다음_작업_표지가_없으면_모델_줄이_있어도_지시문이_아니다() -> None:
    text = "다음 작업 하네스\n모델: Opus 5.5 / medium. 레벨 스윕의 갈래\n브랜치: chore/a"
    assert first_directive([_턴(_IN, text=text)], _SINCE) == ""


def test_창_안에_지시문이_없으면_빈_문자열이다() -> None:
    assert first_directive([_턴(_BEFORE, text=_DIRECTIVE), _턴(_IN)], _SINCE) == ""


# --- human_nondirective --------------------------------------------------------------------------


def test_사람_개입은_창_안의_지시문_아닌_사람_턴이다() -> None:
    turns = [
        _턴(_BEFORE, text=_DIRECTIVE),
        _턴(_BEFORE),
        _턴(_AT),
        _턴(_IN, text=_DIRECTIVE),
        _턴(_IN, trigger="auto"),
        _턴(_IN, trigger="interrupt"),
        _턴(_LATER),
    ]
    first = first_humans(turns)["chore/a"]
    assert human_nondirective(turns, first, _SINCE) == 2


def test_창_안의_첫_트리거가_지시문이_아니면_과제_진술이라_뺀다() -> None:
    turns = [_턴(_IN, text="과제"), _턴(_LATER)]
    first = first_humans(turns)["chore/a"]
    assert human_nondirective(turns, first, _SINCE) == 1


def test_창_앞의_첫_트리거는_세지_않았으니_빼지_않는다() -> None:
    turns = [_턴(_BEFORE, text="과제"), _턴(_IN), _턴(_LATER)]
    first = first_humans(turns)["chore/a"]
    assert human_nondirective(turns, first, _SINCE) == 2


def test_첫_트리거가_지시문이면_빼지_않는다() -> None:
    turns = [_턴(_IN, text=_DIRECTIVE), _턴(_LATER)]
    first = first_humans(turns)["chore/a"]
    assert human_nondirective(turns, first, _SINCE) == 1


def test_창이_없으면_첫_트리거를_빼고_모두_센다() -> None:
    turns = [_턴(_BEFORE, text="과제"), _턴(_IN), _턴(_LATER)]
    first = first_humans(turns)["chore/a"]
    assert human_nondirective(turns, first, None) == 2


def test_사람_개입은_0_밑으로_내려가지_않는다() -> None:
    assert human_nondirective([], (_IN, "과제"), _SINCE) == 0


def test_첫_트리거가_없으면_빼지_않는다() -> None:
    assert human_nondirective([_턴(_IN, trigger="auto"), _턴(_LATER)], None, _SINCE) == 1


# --- cost_state_sessions -------------------------------------------------------------------------


def test_창이_없으면_cost_state를_모두_남긴다() -> None:
    assert cost_state_sessions(["s1", "s2"], {}, None) == {"s1", "s2"}


def test_창_안에_기록이_있는_세션의_cost_state만_남긴다() -> None:
    stamps = {"s1": [_BEFORE, _AT], "s2": [_BEFORE], "s4": [_IN]}
    assert cost_state_sessions(["s1", "s2", "s3"], stamps, _SINCE) == {"s1"}
