"""tools/hook_prompt_directive.py 의 순수 함수. stdin 을 읽는 main 은 실제 실행으로 확인한다."""

from __future__ import annotations

from pathlib import Path

from tools.hook_prompt_directive import context_for

NEXT_SESSION = Path(__file__).parents[2] / ".claude" / "skills" / "next-session" / "SKILL.md"

# 티켓 05 세션이 실제로 받은 첫 메시지(2026-09-23). 앱이 딥링크의 첫 `/` 를 U+FF0F 로 바꿔 넣었고
# 사람이 고치지 않고 보냈다. 시작 프롬프트 줄의 `/` 는 ASCII 그대로다.
DIRECTIVE = """／implement .scratch/admin-api/issues/05-traces-list.md

다음 작업: .scratch/admin-api/issues/05-traces-list.md. GET /traces — 실행 요약 목록과 다음 커서
다음 단계: 구현
어디서: 새 세션
시작 프롬프트: /implement .scratch/admin-api/issues/05-traces-list.md
브랜치: feature/05-traces-list
읽을 것: docs/journal/2026-09-23-03-plugins.md 의 "다음"
이어받을 상태: 없음
확인할 선행 조건: 없음
이번 요청 범위: 구현·리뷰·커밋까지. PR과 병합은 사용자가 말할 때"""


def test_next_session_스킬의_지시문_형식을_채우면_알아본다() -> None:
    """형식의 원천은 next-session 스킬이다.

    거기서 라벨이 바뀌면 훅은 예외 없이 침묵하므로 여기서 잡는다.
    """
    text = NEXT_SESSION.read_text(encoding="utf-8")
    block = text.split("## 지시문 형식", 1)[1].split("```", 2)[1]
    filled: list[str] = []
    for line in block.strip().splitlines():
        label, _, placeholder = line.partition(":")
        if label == "어디서":
            assert "새 세션" in placeholder
            filled.append("어디서: 새 세션")
        elif label == "브랜치":
            filled.append("브랜치: chore/x")
        else:
            filled.append(line)

    context = context_for("/implement x\n\n" + "\n".join(filled))

    assert context is not None
    assert "`chore/x`" in context


def test_새_세션_지시문이면_브랜치_이름으로_제목을_바꾸는_계기다() -> None:
    context = context_for(DIRECTIVE.replace("／", "/", 1))

    assert context is not None
    assert "set_session_title" in context
    assert "`self`" in context
    assert "`feature/05-traces-list`" in context
    assert "SKILL.md" not in context


def test_첫_글자가_전각이면_스킬_파일을_읽어_따르라는_계기가_붙는다() -> None:
    context = context_for(DIRECTIVE)

    assert context is not None
    assert "`feature/05-traces-list`" in context
    assert "`.claude/skills/implement/SKILL.md`" in context


def test_어디서가_새_세션이_아니면_계기가_아니다() -> None:
    """이유 칸에서 결정표를 인용해도 줄 머리가 `이 세션`이면 이 세션이다(next-session 결정표)."""
    this_session = DIRECTIVE.replace("어디서: 새 세션", "어디서: 이 세션")
    quoting = DIRECTIVE.replace(
        "어디서: 새 세션",
        "어디서: 이 세션. 결정표의 `어디서: 새 세션`과 다른 것은 컨텍스트가 자산이라서다",
    )

    assert context_for(this_session) is None
    assert context_for(quoting) is None


def test_어디서_줄의_이유는_새_세션_판정을_바꾸지_않는다() -> None:
    with_reason = DIRECTIVE.replace(
        "어디서: 새 세션", "어디서: 새 세션. 티켓 하나가 컨텍스트 하나다"
    )

    assert context_for(with_reason) is not None


def test_브랜치_줄이_없거나_비었으면_계기가_아니다() -> None:
    without = "\n".join(line for line in DIRECTIVE.splitlines() if not line.startswith("브랜치:"))
    empty = DIRECTIVE.replace("브랜치: feature/05-traces-list", "브랜치: ")

    assert context_for(without) is None
    assert context_for(empty) is None


def test_평범한_프롬프트와_형식을_설명하는_문장은_계기가_아니다() -> None:
    """줄 머리의 `브랜치:`·`어디서:` 만 본다. 문장 속에서 형식을 인용한 것은 지시문이 아니다."""
    for prompt in (
        "테스트를 돌려 줘",
        "／implement .scratch/x.md",
        "지시문이면(`브랜치:` 줄과 `어디서: 새 세션` 줄이 있다) 계기를 넣는다",
    ):
        assert context_for(prompt) is None, prompt


def test_브랜치_값을_감싼_백틱과_CRLF는_벗긴다() -> None:
    wrapped = DIRECTIVE.replace(
        "브랜치: feature/05-traces-list", "브랜치: `feature/05-traces-list`"
    )
    context = context_for(wrapped.replace("\n", "\r\n"))

    assert context is not None
    assert "`feature/05-traces-list`" in context
    assert "``" not in context
    assert "\r" not in context


def test_스킬_이름이_케밥_하나가_아니면_읽을_경로를_만들지_않는다() -> None:
    """이름이 경로가 되므로 `..`·구분자·플러그인 접두어는 받지 않는다."""
    for first_line in ("／../../secrets x", "／plugin:skill x", "／ implement x", "／"):
        context = context_for(DIRECTIVE.replace(DIRECTIVE.splitlines()[0], first_line, 1))

        assert context is not None, first_line
        assert "SKILL.md" not in context, first_line
