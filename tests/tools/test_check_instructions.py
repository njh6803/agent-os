"""tools/check_instructions.py 의 사본 센티널 검사와 경로 참조 검사.

`npx skills update -p` 가 덧댄 사본을 되돌리면 리뷰 범위와 반영 절차가 조용히 사라진다.
변이로 빨강을 한 번 본 것은 일회성이라, 회귀는 이 테스트가 막는다.
"""

from __future__ import annotations

import json
from collections.abc import Container
from pathlib import Path

from tools.check_instructions import (
    PATCHED_SKILLS,
    SENTINEL,
    hooks_with_relative_paths,
    patched_skills_without_sentinel,
    rules_with_dead_paths,
    rules_without_paths,
)


def _사본을_만든다(root: Path, *, 센티널을_넣을_스킬: Container[str]) -> None:
    for name in PATCHED_SKILLS:
        path = root / ".claude" / "skills" / name / "SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        주석 = f"<!-- {SENTINEL}. 원본에 무엇을 더했는지 -->\n"
        머리말 = 주석 if name in 센티널을_넣을_스킬 else ""
        path.write_text(f"{머리말}본문\n", encoding="utf-8")


def test_사본마다_센티널이_있으면_문제가_없다(tmp_path: Path) -> None:
    _사본을_만든다(tmp_path, 센티널을_넣을_스킬=set(PATCHED_SKILLS))

    assert patched_skills_without_sentinel(tmp_path) == []


def test_센티널이_사라진_사본을_잡는다(tmp_path: Path) -> None:
    _사본을_만든다(tmp_path, 센티널을_넣을_스킬=set(PATCHED_SKILLS) - {"code-review"})

    problems = patched_skills_without_sentinel(tmp_path)

    assert len(problems) == 1
    assert "code-review" in problems[0]


def test_사본_파일이_통째로_사라진_것도_잡는다(tmp_path: Path) -> None:
    _사본을_만든다(tmp_path, 센티널을_넣을_스킬=set(PATCHED_SKILLS))
    (tmp_path / ".claude" / "skills" / "retro" / "SKILL.md").unlink()

    problems = patched_skills_without_sentinel(tmp_path)

    assert len(problems) == 1
    assert "retro" in problems[0]


def test_이_저장소의_사본들은_지금_온전하다() -> None:
    assert patched_skills_without_sentinel() == []


# 경로 참조가 아무것도 가리키지 않게 되는 것. 훅은 요란하게(PreToolUse 에서 스크립트를 못 찾은
# 파이썬이 종료 코드 2 로 끝나 모든 Bash 호출을 막는다), rules 는 조용히(그 규칙이 영영 안 실린다)
# 실패한다. 2026-09-23 티켓 03 세션이 앞의 것을 실제로 겪었다(PR #52).


def _설정을_쓴다(root: Path, *명령: str) -> None:
    hooks = [{"type": "command", "command": c} for c in 명령]
    settings = {"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": hooks}]}}
    path = root / ".claude" / "settings.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings), encoding="utf-8")


def _파일을_둔다(root: Path, 상대_경로: str) -> None:
    path = root / 상대_경로
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("", encoding="utf-8")


def test_저장소_파일을_상대_경로로_부르는_훅을_잡는다(tmp_path: Path) -> None:
    """#52 이전의 명령 그대로다. 세션이 저장소 루트를 벗어나면 스크립트를 못 찾는다."""
    _파일을_둔다(tmp_path, "tools/hook_bash_heredoc.py")
    _설정을_쓴다(tmp_path, "uv run --no-sync python tools/hook_bash_heredoc.py")

    problems = hooks_with_relative_paths(tmp_path)

    assert len(problems) == 1
    assert "tools/hook_bash_heredoc.py" in problems[0]
    assert "CLAUDE_PROJECT_DIR" in problems[0]


def test_CLAUDE_PROJECT_DIR_로_부르는_훅은_통과한다(tmp_path: Path) -> None:
    _파일을_둔다(tmp_path, "tools/hook_bash_heredoc.py")
    _설정을_쓴다(
        tmp_path,
        'uv run --project "${CLAUDE_PROJECT_DIR}" --no-sync'
        ' python "${CLAUDE_PROJECT_DIR}/tools/hook_bash_heredoc.py"',
    )

    assert hooks_with_relative_paths(tmp_path) == []


def test_저장소_파일을_부르지_않는_훅은_건드리지_않는다(tmp_path: Path) -> None:
    """모든 훅에 CLAUDE_PROJECT_DIR 을 요구하면 이런 훅이 거짓 양성으로 커밋을 막는다."""
    _설정을_쓴다(tmp_path, "echo hi", "jq -r '.tool_input.command' >> ~/.claude/log.txt")

    assert hooks_with_relative_paths(tmp_path) == []


def test_훅_설정이_없으면_문제가_없다(tmp_path: Path) -> None:
    assert hooks_with_relative_paths(tmp_path) == []


def test_이_저장소의_훅은_지금_작업_디렉터리에_묶이지_않는다() -> None:
    assert hooks_with_relative_paths() == []


def _규칙을_쓴다(root: Path, 이름: str, *경로: str) -> None:
    목록 = "".join(f'  - "{p}"\n' for p in 경로)
    path = root / ".claude" / "rules" / f"{이름}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\npaths:\n{목록}---\n\n# 규칙\n", encoding="utf-8")


def test_아무_파일도_가리키지_않는_paths_를_잡는다(tmp_path: Path) -> None:
    """파일을 옮기거나 나누면 그 이름을 적은 규칙이 조용히 안 실린다. 아무도 모른다."""
    _파일을_둔다(tmp_path, "tests/test_server.py")
    _규칙을_쓴다(tmp_path, "admin", "tests/test_server.py", "tests/test_gone.py")

    problems = rules_with_dead_paths(tmp_path)

    assert len(problems) == 1
    assert "tests/test_gone.py" in problems[0]
    assert "admin.md" in problems[0]


def test_디렉터리_glob_과_파일_경로가_살아_있으면_통과한다(tmp_path: Path) -> None:
    _파일을_둔다(tmp_path, "src/pkg/admin/http.py")
    _파일을_둔다(tmp_path, "openapi.json")
    _규칙을_쓴다(tmp_path, "admin", "src/pkg/admin/**", "openapi.json")

    assert rules_with_dead_paths(tmp_path) == []


def test_이_저장소의_rules_paths_는_지금_다_살아_있다() -> None:
    assert rules_with_dead_paths() == []


def test_저장소에_없는_경로_모양은_잡지_않는다(tmp_path: Path) -> None:
    """실재하는 파일만 잡는다는 조건을 고정한다. 빠지면 경로처럼 생긴 모든 글자가 걸린다."""
    _설정을_쓴다(tmp_path, "echo a/b", "grep -q not/a/file")

    assert hooks_with_relative_paths(tmp_path) == []


def test_따옴표나_점_슬래시로_불러도_상대_경로면_잡는다(tmp_path: Path) -> None:
    _파일을_둔다(tmp_path, "tools/hook_x.py")
    _설정을_쓴다(tmp_path, 'python "tools/hook_x.py"', "python ./tools/hook_x.py")

    assert len(hooks_with_relative_paths(tmp_path)) == 2


def test_항목_없는_paths_는_없는_것으로_잡는다(tmp_path: Path) -> None:
    """키만 있고 항목이 없으면 두 검사를 모두 빠져나가던 자리다."""
    path = tmp_path / ".claude" / "rules" / "empty.md"
    path.parent.mkdir(parents=True)
    path.write_text("---\npaths:\n---\n\n# 규칙\n", encoding="utf-8")

    assert [p.name for p in rules_without_paths(tmp_path)] == ["empty.md"]


def test_paths_의_뒷주석은_패턴이_아니다(tmp_path: Path) -> None:
    _파일을_둔다(tmp_path, "src/pkg/a.py")
    path = tmp_path / ".claude" / "rules" / "src.md"
    path.parent.mkdir(parents=True)
    path.write_text('---\npaths:\n  - "src/**"  # 설명\n---\n', encoding="utf-8")

    assert rules_with_dead_paths(tmp_path) == []


def test_glob_으로_읽을_수_없는_패턴은_트레이스백이_아니라_이유를_낸다(tmp_path: Path) -> None:
    _규칙을_쓴다(tmp_path, "abs", "/abs/**")

    problems = rules_with_dead_paths(tmp_path)

    assert len(problems) == 1
    assert "읽을 수 없다" in problems[0]
