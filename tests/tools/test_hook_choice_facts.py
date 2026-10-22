"""tools/hook_choice_facts.py 의 순수 함수와, 표지를 임시 폴더에 쓰는 main 의 실제 실행.

입력 모양은 SDK 제어 모드 탐침(`.scratch/harness/probes/choice_facts/probe.py`)의 훅이 받은
AskUserQuestion 입력(`{"questions": [{"question", "header", "options": [{"label", "description"}],
"multiSelect"}]}`)을 옮겼다.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path

from tools.hook_choice_facts import (
    ANSWERED_LEAD,
    LEAD,
    QUOTE_LIMIT,
    QUOTE_WIDTH,
    QUOTES_LEAD,
    TOOL,
    HookPayload,
    Json,
    Seen,
    claim_first,
    marker_name,
    output_for,
    reason_for,
    screen_key,
)
from tools.run_hooks import registered_matchers

ROOT = Path(__file__).resolve().parents[2]


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
    """처음 보는 화면을 막는 이유. 옮기는 문장의 시험은 이 글로 본다."""
    reason = reason_for(payload)
    assert reason is not None
    return reason


def _훅_출력(payload: HookPayload, *, seen: Seen) -> dict[str, Json]:
    output = output_for(payload, seen=seen)
    assert isinstance(output, dict)
    specific = output.get("hookSpecificOutput")
    assert isinstance(specific, dict)
    assert specific.get("hookEventName") == "PreToolUse"
    return specific


# 막는 이유가 시키는 지시 요소와 그 요소를 드러내는 구절. 문구를 다듬어도 요소가 남으면 지나고,
# 요소를 빼면 그 요소의 이름으로 실패한다.
_막는_이유_요소 = {
    "화면이 아직 뜨지 않았다": "아직 사용자에게 뜨지 않았다",
    "지금 대 본다": "지금 대 본다",
    "다르면 설명을 고친다": "설명을 고치",
    "못 대 본 것은 어림이라고 적는다": "어림",
    "그 뒤 다시 부른다": "다시 부른다",
    "설명만 고치면 다시 막지 않는다": "다시 막지 않는다",
    "근거 지침(grilling 의 올리기 전)": "올리기 전",
}
# 같은 화면을 다시 불러 지나갈 때의 계기(대기열 395).
_답_뒤_요소 = {
    "받은 답과 요약을 이 턴에 일지에 옮긴다": "이 턴에 일지에 옮긴다",
    "설명까지 글자 그대로": "글자 그대로",
    "일지가 없으면 번호를 받아 먼저 만든다": "다음 빈 번호",
    "근거 지침(grilling 의 옮길 때)": "옮길 때",
}
# 표지를 쓰지 못해 막지 못한 화면의 알림(옛 알림과 같은 요소에 답 뒤 요소를 더한다).
_물러선_알림_요소 = {
    "막지 못했다": "막지 못했다",
    "읽히는 때(사람이 답한 뒤)": "사용자가 답한 뒤",
    "답을 쓰기 전에 대 본다": "답을 쓰기 전",
    "옮기는 자리에 고른 대로 실행하기도 든다": "실행하기 전",
    "다르면 다시 묻는다": "다시 묻",
    "못 대 본 것은 어림이라고 적는다": "어림",
    "받은 답과 요약을 일지에 옮긴다": "이 턴에 일지에 옮긴다",
}


def test_처음_보는_선택_화면은_막고_사실을_대_보라는_이유를_낸다() -> None:
    specific = _훅_출력(_호출(*_탐침_선택지), seen=Seen.FIRST)

    assert specific.get("permissionDecision") == "deny"
    assert "additionalContext" not in specific
    reason = specific.get("permissionDecisionReason")
    assert isinstance(reason, str)
    assert reason.startswith(LEAD)
    for 요소, 구절 in _막는_이유_요소.items():
        assert 구절 in reason, 요소


def test_같은_화면을_다시_부르면_지나가고_답을_일지에_옮기라고_알린다() -> None:
    specific = _훅_출력(_호출(*_탐침_선택지), seen=Seen.AGAIN)

    assert "permissionDecision" not in specific
    context = specific.get("additionalContext")
    assert isinstance(context, str)
    assert context.startswith(ANSWERED_LEAD)
    for 요소, 구절 in _답_뒤_요소.items():
        assert 구절 in context, 요소
    assert QUOTES_LEAD not in context


def test_표지를_쓰지_못하면_막지_않고_답_뒤에_읽힐_알림을_낸다() -> None:
    """같은 화면을 가를 수 없으면 막지 않는다. 막으면 다시 불러도 또 막혀 끝나지 않는다."""
    specific = _훅_출력(_호출(*_탐침_선택지), seen=Seen.UNKNOWN)

    assert "permissionDecision" not in specific
    context = specific.get("additionalContext")
    assert isinstance(context, str)
    assert context.startswith(LEAD)
    for 요소, 구절 in _물러선_알림_요소.items():
        assert 구절 in context, 요소
    assert f"{QUOTES_LEAD}: 빨강: 서버 하나에 약 4.5초가 든다." in context


def test_설명에서_수가_든_문장을_라벨과_함께_옮긴다() -> None:
    reason = _알림(_호출(*_탐침_선택지))

    assert f"{QUOTES_LEAD}: 빨강: 서버 하나에 약 4.5초가 든다." in reason
    assert "지금 코드는 그대로 둔다" not in reason


def test_한_설명의_여러_문장_가운데_수가_든_것만_옮긴다() -> None:
    """사건(일지 2026-10-16-36)의 설명 꼴이다. 수가 든 문장 하나만 옮긴다."""
    설명 = "닫기는 차례로 한다. 서버 하나에 최악 약 4.5초(코드를 읽어 셈)가 든다. 코드가 단순하다."
    reason = _알림(_호출(_선택지("차례로", 설명), _선택지("한꺼번에", "고친다.")))

    assert "차례로: 서버 하나에 최악 약 4.5초(코드를 읽어 셈)가 든다." in reason
    assert "닫기는 차례로 한다" not in reason
    assert "코드가 단순하다" not in reason


def test_소수점과_판_번호는_문장을_가르지_않는다() -> None:
    reason = _알림(_호출(_선택지("A", "v2.3.0 의 상수로 약 6.5초다. 끝."), _선택지("B", "x")))

    assert "A: v2.3.0 의 상수로 약 6.5초다." in reason


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
    reason = _알림(_호출(_선택지("A", "1. 첫째 항목 2. 둘째는 5초다."), _선택지("B", "x")))

    assert "A: 1. / A: 첫째 항목 2. / A: 둘째는 5초다." in reason


def test_줄바꿈도_문장을_가른다() -> None:
    reason = _알림(_호출(_선택지("A", "첫 줄이다\n둘째 줄은 2초다"), _선택지("B", "x")))

    assert "A: 둘째 줄은 2초다" in reason
    assert "첫 줄이다" not in reason


def test_질문_문장의_수도_옮긴다() -> None:
    reason = _알림(_호출(_선택지("A", "고른다."), question="서버가 3개면 어떻게 할까요?"))

    assert "질문: 서버가 3개면 어떻게 할까요?" in reason


def test_머리와_라벨의_수도_옮긴다() -> None:
    질문: dict[str, object] = {
        "question": "어느 쪽으로 할까요?",
        "header": "30초",
        "options": [_선택지("3초 안에", "고른다."), _선택지("B", "x")],
        "multiSelect": False,
    }
    reason = _알림(_입력(질문))

    assert f"{QUOTES_LEAD}: 머리: 30초 / 라벨: 3초 안에" in reason


def test_옮기는_문장은_정한_수까지이고_나머지는_수만_적는다() -> None:
    """질문은 넷, 선택지는 질문마다 넷까지라(AskUserQuestion 스키마) 한도를 넘기려면 질문 둘을 쓴다.
    질문 차례, 그 안의 선택지 차례로 옮긴다. 라벨에는 숫자를 넣지 않아 설명만 센다."""
    첫째 = _질문("하나", *(_선택지(라벨, f"{i}초가 든다.") for i, 라벨 in enumerate("가나다라")))
    둘째 = _질문("둘", *(_선택지(라벨, f"{i}초가 든다.") for i, 라벨 in enumerate("마바사아", 4)))
    reason = _알림(_입력(첫째, 둘째))

    assert QUOTE_LIMIT == 5
    assert "마: 4초가 든다." in reason
    assert "바: " not in reason
    assert "외 3개" in reason
    assert reason.index("가: ") < reason.index("마: ")


def test_긴_문장은_앞에서_잘라_옮긴다() -> None:
    """못 보는 것. 숫자가 자른 자리 뒤에 있으면 옮긴 조각에 숫자가 없다."""
    reason = _알림(
        _호출(_선택지("A", "가" * (QUOTE_WIDTH + 20) + " 1초가 든다."), _선택지("B", "x"))
    )

    assert "A: " + "가" * QUOTE_WIDTH + "…" in reason
    assert "가" * (QUOTE_WIDTH + 1) not in reason
    assert "1초" not in reason


def test_전각_숫자도_수로_센다() -> None:
    reason = _알림(_호출(_선택지("A", "３초가 든다."), _선택지("B", "x")))

    assert "A: ３초가 든다." in reason


def test_수가_든_문장이_없어도_막는다() -> None:
    """못 보는 것. 수가 없는 사실(지금 코드의 동작, 바뀌는지 그대로인지)은 옮기지 않고 이유만 같다.
    사건의 "실패 기록 글이 ExceptionGroup 모양이 된다"가 그 꼴이다."""
    reason = _알림(
        _호출(
            _선택지("그대로", "실패 기록 글이 ExceptionGroup 모양이 된다."),
            _선택지("바꾼다", "어댑터를 고친다."),
        )
    )

    assert reason.startswith(LEAD)
    assert QUOTES_LEAD not in reason
    assert "ExceptionGroup" not in reason


def test_한글_수사는_수로_세지_않는다() -> None:
    """못 보는 것(거짓 음성). 숫자가 없는 "두 배", "세 번" 은 옮기지 않는다."""
    reason = _알림(_호출(_선택지("A", "두 배 느려진다."), _선택지("B", "세 번 다시 묻는다.")))

    assert QUOTES_LEAD not in reason


def test_미리보기의_수는_옮기지_않는다() -> None:
    """못 보는 것. preview 는 코드·화면 조각이라 옮기지 않는다."""
    선택지: dict[str, object] = {"label": "A", "description": "고른다.", "preview": "timeout = 30"}
    reason = _알림(_호출(선택지, _선택지("B", "고른다.")))

    assert QUOTES_LEAD not in reason


def test_어림이라고_적은_사실도_옮긴다() -> None:
    """못 보는 것. 사실을 실제로 대 보았는지는 대화에 있어 훅이 가르지 못한다. 어림이라고 적은
    문장도, 대 본 뒤의 화면도 처음이면 같은 이유로 막힌다."""
    reason = _알림(_호출(_선택지("A", "약 6.5초다(어림)."), _선택지("B", "x")))

    assert "A: 약 6.5초다(어림)." in reason


def test_다른_도구는_침묵한다() -> None:
    skill = json.loads('{"tool_name": "Skill", "tool_input": {"skill": "grill-with-docs"}}')
    for payload in (_입력(_질문("q", *_탐침_선택지), tool="Skill"), skill):
        for seen in Seen:
            assert output_for(payload, seen=seen) is None
        assert reason_for(payload) is None


def test_입력_모양이_달라도_선택_화면이면_옮길_문장_없이_막는다() -> None:
    """선택 화면은 입력 모양과 상관없이 뜬다. 가를 수 없는 조각은 건너뛰고 이유는 낸다."""
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
        reason = reason_for(payload)
        assert reason is not None and reason.startswith(LEAD), payload
        assert QUOTES_LEAD not in reason, payload
        assert isinstance(screen_key(payload.get("tool_input")), str), payload


def test_라벨이_글자가_아니면_선택지라고_적는다() -> None:
    payload = json.loads(
        '{"tool_name": "AskUserQuestion", "tool_input": {"questions": [{"question": "q",'
        ' "options": [{"label": 7, "description": "3초다."}]}]}}'
    )

    assert "선택지: 3초다." in _알림(payload)


def _화면(payload: HookPayload) -> str:
    return screen_key(payload.get("tool_input"))


def test_질문_문장과_라벨이_같으면_같은_화면이다() -> None:
    """못 보는 것(거짓 음성). 설명·머리·미리보기·multiSelect 만 다른 뒤 화면은 앞 화면과 같다고
    보아 막지 않는다. 대 본 뒤 설명만 고쳐 다시 부른 화면을 또 막지 않기 위해서다."""
    앞 = _화면(_호출(*_탐침_선택지))
    설명만 = _화면(_호출(_선택지("빨강", "약 6.5초가 든다(어림)."), _선택지("파랑", "x")))
    다른_머리: dict[str, object] = {**_질문("어느 쪽으로 할까요?", *_탐침_선택지), "header": "새"}
    미리보기: dict[str, object] = {**_탐침_선택지[0], "preview": "a = 1"}

    assert 설명만 == 앞
    assert _화면(_입력(다른_머리)) == 앞
    assert _화면(_호출(미리보기, _탐침_선택지[1])) == 앞


def test_질문_문장이나_라벨이나_차례가_다르면_다른_화면이다() -> None:
    앞 = _화면(_호출(*_탐침_선택지))
    둘째 = _질문("둘째 질문", *_탐침_선택지)

    assert _화면(_호출(*_탐침_선택지, question="다른 질문")) != 앞
    assert _화면(_호출(_선택지("초록", "x"), _탐침_선택지[1])) != 앞
    assert _화면(_호출(*reversed(_탐침_선택지))) != 앞
    assert _화면(_입력(_질문("어느 쪽으로 할까요?", *_탐침_선택지), 둘째)) != 앞


def test_표지_이름은_세션과_에이전트와_화면마다_다르다() -> None:
    names = {
        marker_name("s", "", "k"),
        marker_name("s2", "", "k"),
        marker_name("s", "a", "k"),
        marker_name("s", "", "k2"),
    }

    assert len(names) == 4
    assert marker_name("s", "", "k") == marker_name("s", "", "k")


def test_표지는_처음_만든_호출만_처음이라고_본다(tmp_path: Path) -> None:
    assert claim_first("x", tmp_path / "state") is Seen.FIRST
    assert claim_first("x", tmp_path / "state") is Seen.AGAIN
    assert claim_first("y", tmp_path / "state") is Seen.FIRST


def test_표지를_쓰지_못하면_모른다고_돌려준다(tmp_path: Path) -> None:
    """폴더 자리에 파일이 있으면 표지를 만들 수 없다. 처음이라고 보면 같은 화면을 거듭 막는다."""
    blocker = tmp_path / "state"
    blocker.write_text("", encoding="utf-8")

    assert claim_first("x", blocker) is Seen.UNKNOWN


def _main(payload: Mapping[str, object], temp: Path) -> dict[str, Json]:
    """훅을 자식 프로세스로 돌린다. 임시 폴더는 `tempfile.gettempdir()` 가 읽는 변수 셋으로 준다."""
    env = {**os.environ, "TEMP": str(temp), "TMP": str(temp), "TMPDIR": str(temp)}
    completed = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "hook_choice_facts.py")],
        input=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        capture_output=True,
        env=env,
        timeout=60,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr.decode("utf-8", "replace")
    if not completed.stdout.strip():
        return {}
    output: Json = json.loads(completed.stdout)
    assert isinstance(output, dict)
    specific = output.get("hookSpecificOutput")
    assert isinstance(specific, dict)
    return specific


def _세션_호출(session: str, *options: dict[str, object], agent: str = "") -> dict[str, object]:
    payload: dict[str, object] = {**_호출(*options), "session_id": session}
    if agent:
        payload["agent_id"] = agent
    return payload


def test_세션마다_같은_화면은_처음만_막고_다시_부르면_지나간다(tmp_path: Path) -> None:
    """대기열 394 의 고리. 대 보지 않고 같은 화면을 다시 불러도 지나간다(일부러 하는 우회는 못
    본다)."""
    첫 = _main(_세션_호출("s1", *_탐침_선택지), tmp_path)
    둘째 = _main(_세션_호출("s1", *_탐침_선택지), tmp_path)
    다른_세션 = _main(_세션_호출("s2", *_탐침_선택지), tmp_path)
    서브에이전트 = _main(_세션_호출("s1", *_탐침_선택지, agent="a1"), tmp_path)

    assert 첫.get("permissionDecision") == "deny"
    assert "permissionDecision" not in 둘째
    assert str(둘째.get("additionalContext")).startswith(ANSWERED_LEAD)
    assert 다른_세션.get("permissionDecision") == "deny"
    assert 서브에이전트.get("permissionDecision") == "deny"


def test_설명만_고쳐_다시_부른_화면은_막지_않는다(tmp_path: Path) -> None:
    _main(_세션_호출("s1", *_탐침_선택지), tmp_path)
    고친 = _main(_세션_호출("s1", _선택지("빨강", "약 6.5초다(어림)."), _탐침_선택지[1]), tmp_path)
    다른_화면 = _main(_세션_호출("s1", _선택지("초록", "x"), _탐침_선택지[1]), tmp_path)

    assert "permissionDecision" not in 고친
    assert 다른_화면.get("permissionDecision") == "deny"


def test_세션을_모르면_막지_않고_알린다(tmp_path: Path) -> None:
    for payload in (dict(_호출(*_탐침_선택지)), _세션_호출("", *_탐침_선택지)):
        specific = _main(payload, tmp_path)

        assert "permissionDecision" not in specific
        assert str(specific.get("additionalContext")).startswith(LEAD)


def test_다른_도구는_표지를_쓰지_않고_침묵한다(tmp_path: Path) -> None:
    payload = {"tool_name": "Skill", "tool_input": {"skill": "x"}, "session_id": "s1"}

    assert _main(payload, tmp_path) == {}
    assert not (tmp_path / "agent-os-choice-facts").exists()


def test_settings의_매처는_훅이_아는_도구_하나다() -> None:
    """매처를 넓히면 훅이 이름으로 걸러 조용히 지나가고, 이름을 바꾸면 등록이 훅을 걸지 않는다."""
    assert registered_matchers("hook_choice_facts.py", "PreToolUse") == [TOOL]
