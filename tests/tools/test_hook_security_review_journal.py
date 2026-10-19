"""tools/hook_security_review_journal.py 의 순수 함수. stdin 을 읽는 main 은 실제 실행으로 확인한다.

입력 모양은 트랜스크립트의 Skill 호출(`{"skill": "security-review"}`)을 옮겼다.
"""

from __future__ import annotations

import json

from tools.hook_security_review_journal import LEAD, SKILL, TOOL, HookPayload, context_for
from tools.run_hooks import registered_matchers


def _호출(skill: object, tool: str = TOOL) -> HookPayload:
    return json.loads(json.dumps({"tool_name": tool, "tool_input": {"skill": skill}}))


def test_security_review_호출이면_보고를_다_쓴_턴에_일지로_옮기라고_알린다() -> None:
    context = context_for(_호출(SKILL))

    assert context is not None
    assert context.startswith(LEAD)
    assert "code-review 6단계 끝" in context


def test_args가_붙어도_같은_문장을_낸다() -> None:
    with_args = json.loads(
        json.dumps({"tool_name": TOOL, "tool_input": {"skill": SKILL, "args": "범위는 abc..HEAD"}})
    )

    assert context_for(with_args) == context_for(_호출(SKILL))


def test_앞의_슬래시는_벗겨_비교한다() -> None:
    assert context_for(_호출("/security-review")) is not None


def test_다른_스킬은_침묵한다() -> None:
    for skill in ("code-review", "next-session", "security-review-extra", "security", ""):
        assert context_for(_호출(skill)) is None, skill


def test_접두가_붙은_이름은_지나간다() -> None:
    """못 보는 것. 내장 명령은 접두 없이 불렸고, 접두가 붙은 이름은 다른 스킬일 수 있다."""
    assert context_for(_호출("some-plugin:security-review")) is None
    assert context_for(_호출(".claude/worktrees/x:security-review")) is None


def test_Skill이_아닌_도구는_보지_않는다() -> None:
    assert context_for(_호출(SKILL, tool="Read")) is None


def test_입력_모양이_다르면_침묵한다() -> None:
    payloads: list[HookPayload] = [
        {"tool_name": TOOL},
        json.loads('{"tool_name": "Skill", "tool_input": "security-review"}'),
        json.loads('{"tool_name": "Skill", "tool_input": {"skill": 1}}'),
        json.loads('{"tool_name": "Skill", "tool_input": {"args": "x"}}'),
    ]
    for payload in payloads:
        assert context_for(payload) is None, payload


def test_서브에이전트의_호출에도_같은_문장을_낸다() -> None:
    """못 보는 것. 입력의 `agent_id` 로 가르지 않는다. 일지를 쓰는 세션인지도 가르지 않아 문장이
    조건으로 말한다."""
    sub = json.loads(
        json.dumps(
            {
                "tool_name": TOOL,
                "agent_id": "a1",
                "agent_type": "general-purpose",
                "tool_input": {"skill": SKILL},
            }
        )
    )

    assert context_for(sub) == context_for(_호출(SKILL))
    assert LEAD.startswith("일지를 쓰는 세션이면")


def test_settings의_매처는_훅이_아는_도구_하나다() -> None:
    """매처를 넓히면 훅이 이름으로 걸러 조용히 지나가고, 이름을 바꾸면 등록이 훅을 걸지 않는다."""
    assert registered_matchers("hook_security_review_journal.py", "PreToolUse") == [TOOL]
