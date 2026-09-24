"""tools/hook_prompt_directive.py 의 순수 함수. stdin 을 읽는 main 은 실제 실행으로 확인한다."""

from __future__ import annotations

from pathlib import Path

from tools.hook_prompt_directive import (
    block_reason_for,
    context_for,
    has_assistant_turn,
    is_first_turn,
)

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


# open_session.ps1 의 Convert-StartLine 이 옮긴 첫 줄. 스킬 파일을 상대 경로로 가리키고, 연
# 저장소를 표지로 든다. 상대 경로라 저장소가 아닌 폴더에서는 파일을 못 찾아 멈추고, 표지로 훅이
# 폴더를 가른다.
ROOT = "C:\\project\\agent"
OPEN_SESSION = Path(__file__).parents[2] / "tools" / "open_session.ps1"


def _opened(root: str = ROOT, skill: str = "implement") -> str:
    """Convert-StartLine 이 만드는 모양의 첫 줄로 DIRECTIVE 를 연다. 모양의 원천은 ps1 이다(아래
    대조)."""
    first = (
        f".claude/skills/{skill}/SKILL.md 를 읽어 그대로 따른다. "
        f"이 세션을 연 저장소는 `{root}`이고 "
        "작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 "
        "끝까지다. 인자: .scratch/admin-api/issues/05-traces-list.md"
    )
    return DIRECTIVE.replace(DIRECTIVE.splitlines()[0], first, 1)


def test_연_저장소와_작업_폴더가_같으면_막지_않고_이름을_붙인다() -> None:
    assert block_reason_for(_opened(), ROOT) is None
    context = context_for(_opened())
    assert context is not None
    assert "`feature/05-traces-list`" in context


def test_작업_폴더가_연_저장소와_다르면_프롬프트를_막는다() -> None:
    """딥링크는 폴더를 싣지 않고 앱이 마지막 폴더를 쓴다. 그것이 워크트리면 거기에도 같은 스킬
    파일이 있어, 사람이 보내기 전에 폴더를 보던 눈 없이 엉뚱한 곳에서 시작한다(PR #65 의
    CodeRabbit). 모델에게 권하는 것이 아니라 프롬프트를 막는다 — 첫 줄은 "그대로 따른다"라고
    말하므로 권고는 그것과 다툰다."""
    worktree = f"{ROOT}\\.claude\\worktrees\\silly-carson-627e95"

    reason = block_reason_for(_opened(), worktree)

    assert reason is not None
    assert f"`{worktree}`" in reason
    assert f"`{ROOT}`" in reason


def test_작업_폴더를_모르면_막는다() -> None:
    """비교할 수 없으면 막는 쪽이다. 빈 문자열도 모르는 것이다."""
    for cwd in (None, ""):
        reason = block_reason_for(_opened(), cwd)

        assert reason is not None, cwd
        assert "(알 수 없음)" in reason, cwd


def test_폴더_비교는_구분자와_대소문자와_끝의_구분자를_가리지_않는다() -> None:
    """윈도 경로라 대소문자를 가리지 않는다. 운영체제의 정규화에 맡기지 않아 CI 에서도 같은
    답이다."""
    for cwd in ("c:/project/agent", "C:\\project\\agent\\", "C:/Project/Agent/"):
        assert block_reason_for(_opened(), cwd) is None, cwd


def test_연_저장소가_워크트리이거나_공백이_든_경로여도_같은_폴더면_막지_않는다() -> None:
    for root in (f"{ROOT}\\.claude\\worktrees\\wt", "C:\\My Docs\\agent"):
        assert block_reason_for(_opened(root=root), root) is None, root
        assert block_reason_for(_opened(root=root), ROOT + "\\other") is not None, root


def test_옮기지_않은_첫_줄이나_지시문이_아니면_막지_않는다() -> None:
    """슬래시 명령과 전각은 앱이 연 폴더에서 스킬을 찾는다. 가리키는 저장소가 따로 없다. 지시문이
    아닌 프롬프트는 이 훅의 일이 아니다."""
    not_directive = "\n".join(
        line for line in _opened().splitlines() if not line.startswith("브랜치:")
    )
    for prompt in (DIRECTIVE, DIRECTIVE.replace("／", "/", 1), not_directive):
        assert block_reason_for(prompt, "D:\\elsewhere") is None


def test_open_session_스크립트가_만드는_첫_줄을_훅이_알아본다() -> None:
    """문구의 원천은 ps1 이고 훅은 그것을 글자로 파싱한다. 한쪽만 바뀌면 폴더 가드가 조용히
    꺼지므로(표지를 못 찾으면 막을 이유가 없다) 여기서 잡는다."""
    source = OPEN_SESSION.read_text(encoding="utf-8")
    marker = next(line for line in source.splitlines() if "이 세션을 연 저장소는" in line)
    template = marker.split('return "', 1)[1].split('".TrimEnd()', 1)[0]
    first = (
        template.replace("``", "`")
        .replace("$skill", ".claude/skills/implement/SKILL.md")
        .replace("$root", ROOT)
        .replace("$rest", "x")
    )
    assert "$" not in first
    prompt = DIRECTIVE.replace(DIRECTIVE.splitlines()[0], first, 1)

    assert block_reason_for(prompt, ROOT) is None
    assert block_reason_for(prompt, "D:\\elsewhere") is not None


def test_모델이_아직_답하지_않은_트랜스크립트는_첫_턴이다() -> None:
    """지시문으로 연 세션은 지시문이 첫 메시지다. 훅이 도는 시점엔 assistant 기록이 없다."""
    first_turn = [
        '{"type":"queue-operation","operation":"enqueue"}',
        '{"type":"attachment","attachment":{"type":"hook_additional_context"}}',
        '{"type":"user","message":{"role":"user","content":"／implement x"}}',
    ]

    assert has_assistant_turn(first_turn) is False
    assert has_assistant_turn([]) is False


def test_모델이_한_번이라도_답했으면_첫_턴이_아니다() -> None:
    """진행 중인 대화에 지시문을 붙여 넣은 것은 새 세션이 아니다(이 훅을 만든 세션에서 실측)."""
    ongoing = [
        '{"type":"user","message":{"role":"user","content":"훅을 만든다"}}',
        '{"type":"assistant","message":{"role":"assistant","content":[]}}',
        '{"type":"user","message":{"role":"user","content":"```\\n브랜치: x\\n```"}}',
    ]

    assert has_assistant_turn(ongoing) is True


def test_기록의_종류는_최상위_type만_보고_깨진_줄은_건너뛴다() -> None:
    """본문 속의 `"type":"assistant"` 는 기록의 종류가 아니다. 최상위 `type` 만 본다.

    잘린 줄은 훅이 읽는 동안 앱이 마지막 줄을 쓰고 있을 때 생긴다.
    """
    lines = [
        "not json",
        "[]",
        '{"type":"user","message":{"content":"잘린',
        '{"type":"user","message":{"content":"{\\"type\\":\\"assistant\\"}"}}',
        '{"type":"attachment","attachment":{"type":"assistant"}}',
    ]

    assert has_assistant_turn(lines) is False
    assert has_assistant_turn([*lines, '{"type":"assistant"}']) is True


def test_트랜스크립트_파일이_아직_없으면_첫_턴이다(tmp_path: Path) -> None:
    """새 세션의 첫 프롬프트에서는 트랜스크립트가 만들어지기 전일 수 있다."""
    assert is_first_turn(str(tmp_path / "없음.jsonl")) is True


def test_트랜스크립트에_assistant_기록이_생기면_첫_턴이_끝난다(tmp_path: Path) -> None:
    transcript = tmp_path / "t.jsonl"
    transcript.write_text('{"type":"user"}\n', encoding="utf-8")
    assert is_first_turn(str(transcript)) is True

    transcript.write_text('{"type":"user"}\n{"type":"assistant"}\n', encoding="utf-8")
    assert is_first_turn(str(transcript)) is False


def test_트랜스크립트_경로를_모르면_첫_턴이라고_하지_않는다() -> None:
    """잘못 발동하면 엉뚱한 세션의 이름이 조용히 바뀐다. 모를 때는 발동하지 않아야 드러난다."""
    assert is_first_turn(None) is False
    assert is_first_turn("") is False
