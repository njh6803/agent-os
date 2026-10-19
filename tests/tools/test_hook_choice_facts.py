"""tools/hook_choice_facts.py 의 순수 함수. stdin 을 읽는 main 은 실제 실행으로 확인한다.

입력 모양은 SDK 제어 모드 탐침(`.scratch/harness/probes/choice_facts/probe.py`)의 훅이 받은
AskUserQuestion 입력(`{"questions": [{"question", "header", "options": [{"label", "description"}],
"multiSelect"}]}`)을 옮겼다.
"""

from __future__ import annotations

import json

from tools.hook_choice_facts import (
    LEAD,
    QUOTE_LIMIT,
    QUOTE_WIDTH,
    QUOTES_LEAD,
    TOOL,
    HookPayload,
    context_for,
)
from tools.run_hooks import registered_matchers


def _선택지(label: str, description: str) -> dict[str, object]:
    return {"label": label, "description": description}


def _질문(question: str, *options: dict[str, object]) -> dict[str, object]:
    return {"question": question, "header": "탐침", "options": list(options), "multiSelect": False}


def _입력(*questions: dict[str, object], tool: str = TOOL) -> HookPayload:
    return json.loads(json.dumps({"tool_name": tool, "tool_input": {"questions": list(questions)}}))


def _호출(*options: dict[str, object], question: str = "어느 쪽으로 할까요?") -> HookPayload:
    return _입력(_질문(question, *options))


_탐침_선택지 = (
    _선택지("빨강", "서버 하나에 약 4.5초가 든다."),
    _선택지("파랑", "지금 코드는 그대로 둔다."),
)


def _알림(payload: HookPayload) -> str:
    context = context_for(payload)
    assert context is not None
    return context


# 알림이 시키는 지시 요소와 그 요소를 드러내는 구절. 문구를 다듬어도 요소가 남으면 지나고, 요소를
# 빼면 그 요소의 이름으로 실패한다.
_지시_요소 = {
    "읽히는 때(사람이 답한 뒤)": "사용자가 답한 뒤",
    "첫째 일(답을 쓰기 전에 대 본다)": "답을 쓰기 전",
    "옮기는 자리에 고른 대로 실행하기도 든다": "실행하기 전",
    "다르면 다시 묻는다": "다시 묻",
    "못 대 본 것은 어림이라고 적는다": "어림",
    "둘째 일(다음 화면의 설명 전에 대 본다)": "다음 선택 화면",
    "근거 지침(grilling 의 올리기 전)": "올리기 전",
}


def test_선택_화면이면_사실을_대_보았는지_확인하라고_알린다() -> None:
    context = _알림(_호출(*_탐침_선택지))

    assert context.startswith(LEAD)
    for 요소, 구절 in _지시_요소.items():
        assert 구절 in context, 요소


def test_설명에서_수가_든_문장을_라벨과_함께_옮긴다() -> None:
    context = _알림(_호출(*_탐침_선택지))

    assert f"{QUOTES_LEAD}: 빨강: 서버 하나에 약 4.5초가 든다." in context
    assert "지금 코드는 그대로 둔다" not in context


def test_한_설명의_여러_문장_가운데_수가_든_것만_옮긴다() -> None:
    """사건(일지 2026-10-16-36)의 설명 꼴이다. 수가 든 문장 하나만 옮긴다."""
    설명 = "닫기는 차례로 한다. 서버 하나에 최악 약 4.5초(코드를 읽어 셈)가 든다. 코드가 단순하다."
    context = _알림(_호출(_선택지("차례로", 설명), _선택지("한꺼번에", "고친다.")))

    assert "차례로: 서버 하나에 최악 약 4.5초(코드를 읽어 셈)가 든다." in context
    assert "닫기는 차례로 한다" not in context
    assert "코드가 단순하다" not in context


def test_소수점과_판_번호는_문장을_가르지_않는다() -> None:
    context = _알림(_호출(_선택지("A", "v2.3.0 의 상수로 약 6.5초다. 끝."), _선택지("B", "x")))

    assert "A: v2.3.0 의 상수로 약 6.5초다." in context


def test_닫는_따옴표나_괄호_뒤에서도_문장을_가른다() -> None:
    따옴표 = _알림(
        _호출(_선택지("A", '지금 판은 "그대로 둔다." 바꾸면 3초가 든다.'), _선택지("B", "x"))
    )
    괄호 = _알림(_호출(_선택지("A", "바꾸지 않는다(지금 판.) 바꾸면 2초다."), _선택지("B", "x")))

    assert "A: 바꾸면 3초가 든다." in 따옴표
    assert "그대로 둔다" not in 따옴표
    assert "A: 바꾸면 2초다." in 괄호
    assert "지금 판" not in 괄호


def test_번호_목록은_번호의_점에서_갈라_옮긴다() -> None:
    """못 보는 것(거짓 양성). 번호의 점 뒤에서 갈라 숫자가 사실이 아닌 조각도 옮기고 한도를
    먹는다."""
    context = _알림(_호출(_선택지("A", "1. 첫째 항목 2. 둘째는 5초다."), _선택지("B", "x")))

    assert "A: 1. / A: 첫째 항목 2. / A: 둘째는 5초다." in context


def test_줄바꿈도_문장을_가른다() -> None:
    context = _알림(_호출(_선택지("A", "첫 줄이다\n둘째 줄은 2초다"), _선택지("B", "x")))

    assert "A: 둘째 줄은 2초다" in context
    assert "첫 줄이다" not in context


def test_질문_문장의_수도_옮긴다() -> None:
    context = _알림(_호출(_선택지("A", "고른다."), question="서버가 3개면 어떻게 할까요?"))

    assert "질문: 서버가 3개면 어떻게 할까요?" in context


def test_머리와_라벨의_수도_옮긴다() -> None:
    질문: dict[str, object] = {
        "question": "어느 쪽으로 할까요?",
        "header": "30초",
        "options": [_선택지("3초 안에", "고른다."), _선택지("B", "x")],
        "multiSelect": False,
    }
    context = _알림(_입력(질문))

    assert f"{QUOTES_LEAD}: 머리: 30초 / 라벨: 3초 안에" in context


def test_옮기는_문장은_정한_수까지이고_나머지는_수만_적는다() -> None:
    """질문은 넷, 선택지는 질문마다 넷까지라(AskUserQuestion 스키마) 한도를 넘기려면 질문 둘을 쓴다.
    질문 차례, 그 안의 선택지 차례로 옮긴다. 라벨에는 숫자를 넣지 않아 설명만 센다."""
    첫째 = _질문("하나", *(_선택지(라벨, f"{i}초가 든다.") for i, 라벨 in enumerate("가나다라")))
    둘째 = _질문("둘", *(_선택지(라벨, f"{i}초가 든다.") for i, 라벨 in enumerate("마바사아", 4)))
    context = _알림(_입력(첫째, 둘째))

    assert QUOTE_LIMIT == 5
    assert "마: 4초가 든다." in context
    assert "바: " not in context
    assert "외 3개" in context
    assert context.index("가: ") < context.index("마: ")


def test_긴_문장은_앞에서_잘라_옮긴다() -> None:
    """못 보는 것. 숫자가 자른 자리 뒤에 있으면 옮긴 조각에 숫자가 없다."""
    context = _알림(
        _호출(_선택지("A", "가" * (QUOTE_WIDTH + 20) + " 1초가 든다."), _선택지("B", "x"))
    )

    assert "A: " + "가" * QUOTE_WIDTH + "…" in context
    assert "가" * (QUOTE_WIDTH + 1) not in context
    assert "1초" not in context


def test_전각_숫자도_수로_센다() -> None:
    context = _알림(_호출(_선택지("A", "３초가 든다."), _선택지("B", "x")))

    assert "A: ３초가 든다." in context


def test_수가_든_문장이_없어도_알린다() -> None:
    """못 보는 것. 수가 없는 사실(지금 코드의 동작, 바뀌는지 그대로인지)은 옮기지 않고 알림만 같다.
    사건의 "실패 기록 글이 ExceptionGroup 모양이 된다"가 그 꼴이다."""
    context = _알림(
        _호출(
            _선택지("그대로", "실패 기록 글이 ExceptionGroup 모양이 된다."),
            _선택지("바꾼다", "어댑터를 고친다."),
        )
    )

    assert context.startswith(LEAD)
    assert QUOTES_LEAD not in context
    assert "ExceptionGroup" not in context


def test_한글_수사는_수로_세지_않는다() -> None:
    """못 보는 것(거짓 음성). 숫자가 없는 "두 배", "세 번" 은 옮기지 않는다."""
    context = _알림(_호출(_선택지("A", "두 배 느려진다."), _선택지("B", "세 번 다시 묻는다.")))

    assert QUOTES_LEAD not in context


def test_미리보기의_수는_옮기지_않는다() -> None:
    """못 보는 것. preview 는 코드·화면 조각이라 옮기지 않는다."""
    선택지: dict[str, object] = {"label": "A", "description": "고른다.", "preview": "timeout = 30"}
    context = _알림(_호출(선택지, _선택지("B", "고른다.")))

    assert QUOTES_LEAD not in context


def test_어림이라고_적은_사실도_옮긴다() -> None:
    """못 보는 것. 사실을 실제로 대 보았는지는 대화에 있어 훅이 가르지 못한다. 어림이라고 적은
    문장도, 대 본 뒤의 화면도 같은 알림을 받는다."""
    context = _알림(_호출(_선택지("A", "약 6.5초다(어림)."), _선택지("B", "x")))

    assert "A: 약 6.5초다(어림)." in context


def test_다른_도구는_침묵한다() -> None:
    assert context_for(_입력(_질문("q", *_탐침_선택지), tool="Skill")) is None
    skill = json.loads('{"tool_name": "Skill", "tool_input": {"skill": "grill-with-docs"}}')
    assert context_for(skill) is None


def test_입력_모양이_달라도_선택_화면이면_옮길_문장_없이_알린다() -> None:
    """선택 화면은 입력 모양과 상관없이 떴다. 가를 수 없는 조각은 건너뛰고 알림은 낸다."""
    payloads: list[HookPayload] = [
        {"tool_name": TOOL},
        json.loads('{"tool_name": "AskUserQuestion", "tool_input": "x"}'),
        json.loads('{"tool_name": "AskUserQuestion", "tool_input": {"questions": "x"}}'),
        json.loads(
            '{"tool_name": "AskUserQuestion", "tool_input": {"questions": [1, {"options": "x"},'
            ' {"question": 3, "options": [2, {"label": "A", "description": 5}]}]}}'
        ),
    ]
    for payload in payloads:
        context = context_for(payload)
        assert context is not None and context.startswith(LEAD), payload
        assert QUOTES_LEAD not in context, payload


def test_라벨이_글자가_아니면_선택지라고_적는다() -> None:
    payload = json.loads(
        '{"tool_name": "AskUserQuestion", "tool_input": {"questions": [{"question": "q",'
        ' "options": [{"label": 7, "description": "3초다."}]}]}}'
    )

    assert "선택지: 3초다." in _알림(payload)


def test_settings의_매처는_훅이_아는_도구_하나다() -> None:
    """매처를 넓히면 훅이 이름으로 걸러 조용히 지나가고, 이름을 바꾸면 등록이 훅을 걸지 않는다."""
    assert registered_matchers("hook_choice_facts.py", "PreToolUse") == [TOOL]
