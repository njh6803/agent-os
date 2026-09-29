"""tools/check_instructions.py 의 검사들. 변이로 본 빨강은 일회성이라 회귀는 여기서 막는다.

`npx skills update -p` 가 덧댄 사본을 되돌리면 리뷰 범위와 반영 절차가 조용히 사라진다. 경로 참조가
아무것도 가리키지 않게 되면 훅은 요란하게, rules 는 조용히 실패한다(PR #52). 문장 속 `@경로` 는 줄
머리의 것과 같은 임포트인데 2026-09-28 까지 검사가 줄 머리만 봤다.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from collections.abc import Container
from pathlib import Path

from tools.check_instructions import (
    PATCHED_SKILLS,
    ROOT,
    SENTINEL,
    claude_md_imports,
    claude_md_problems,
    hooks_reading_text_stdin,
    hooks_with_relative_paths,
    imported_files_with_dead_paths,
    nested_instruction_files,
    patched_skills_without_sentinel,
    rules_with_dead_paths,
    rules_without_paths,
    skills_with_sentinel_not_listed,
    text_stdin_lines,
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


# 역방향. 목록은 손으로 유지되는데, 사본을 새로 덧대며 주석은 붙이고 목록은 잊으면 그 사본은 앞 검사
# 밖이라 되돌려져도 초록이다. 주석을 붙이는 커밋에서 걸리게 한다(2026-09-28 하네스 감사).


def test_센티널이_있는데_목록에_없는_사본을_잡는다(tmp_path: Path) -> None:
    _사본을_만든다(tmp_path, 센티널을_넣을_스킬=set(PATCHED_SKILLS))
    path = tmp_path / ".claude" / "skills" / "tdd" / "SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_text(f"<!-- {SENTINEL}. 시임 어휘 포인터 -->\n본문\n", encoding="utf-8")

    problems = skills_with_sentinel_not_listed(tmp_path)

    assert len(problems) == 1
    assert "tdd" in problems[0]
    assert "PATCHED_SKILLS" in problems[0]


def test_목록_밖_사본에_센티널이_없으면_문제가_없다(tmp_path: Path) -> None:
    _사본을_만든다(tmp_path, 센티널을_넣을_스킬=set(PATCHED_SKILLS))
    path = tmp_path / ".claude" / "skills" / "tdd" / "SKILL.md"
    path.parent.mkdir(parents=True)
    path.write_text("원본 그대로\n", encoding="utf-8")

    assert skills_with_sentinel_not_listed(tmp_path) == []


def test_이_저장소의_센티널_사본은_전부_목록에_있다() -> None:
    assert skills_with_sentinel_not_listed() == []


# 경로 참조가 아무것도 가리키지 않게 되는 것. 훅은 요란하게(PreToolUse 에서 스크립트를 못 찾은
# 파이썬이 종료 코드 2 로 끝나 모든 Bash 호출을 막는다), rules 는 조용히(그 규칙이 영영 안 실린다)
# 실패한다. 2026-09-23 티켓 03 세션이 앞의 것을 실제로 겪었다(PR #52).


def _설정을_쓴다(root: Path, *명령: str) -> None:
    hooks = [{"type": "command", "command": c} for c in 명령]
    settings = {"hooks": {"PreToolUse": [{"matcher": "Bash", "hooks": hooks}]}}
    path = root / ".claude" / "settings.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(settings), encoding="utf-8")


def _파일을_둔다(root: Path, 상대_경로: str, 내용: str = "") -> None:
    path = root / 상대_경로
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(내용, encoding="utf-8")


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


def test_프론트매터가_없는_rules_파일도_잡는다(tmp_path: Path) -> None:
    path = tmp_path / ".claude" / "rules" / "bare.md"
    path.parent.mkdir(parents=True)
    path.write_text("# 규칙\n\n- 아무 것\n", encoding="utf-8")

    assert [p.name for p in rules_without_paths(tmp_path)] == ["bare.md"]


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


# CLAUDE.md 의 줄 수와 `@` 임포트. 2026-09-28 까지 이 둘에는 회귀 테스트가 없었고 함수가 ROOT 를
# 직접 읽어 시험할 수도 없었다.


def _클로드_파일을_쓴다(root: Path, 본문: str) -> None:
    (root / "CLAUDE.md").write_text(본문, encoding="utf-8")


def test_줄_머리_임포트_하나뿐이면_문제가_없다(tmp_path: Path) -> None:
    _클로드_파일을_쓴다(tmp_path, "# 프로젝트\n\n@docs/constitution/principles.md\n\n본문\n")

    assert claude_md_problems(tmp_path) == []


def test_문장_속_임포트도_임포트다(tmp_path: Path) -> None:
    """공식 문서: `@` 구문은 어디서든 임포트다. 줄 머리만 보면 이 구절이 파일을 통째로 싣는다."""
    _클로드_파일을_쓴다(
        tmp_path,
        "@docs/constitution/principles.md\n\n범위가 헷갈리면 @docs/PRD.md 를 본다.\n",
    )

    problems = claude_md_problems(tmp_path)

    assert len(problems) == 1
    assert "@docs/PRD.md" in problems[0]


def test_백틱과_펜스_안의_at_은_임포트가_아니다() -> None:
    본문 = (
        "@docs/constitution/principles.md\n\n"
        '`@`를 쓰지 않는다. 훅은 `"${CLAUDE_PROJECT_DIR}"` 로.\n'
        "```\n@docs/PRD.md\n```\n"
        "~~~\n@docs/constitution/tech.md\n~~~\n"
        "- 목록 안:\n  ```bash\n  cat @docs/adr/README.md\n  ```\n"
        "문의는 noreply@anthropic.com 으로.\n"
    )

    assert claude_md_imports(본문) == ["@docs/constitution/principles.md"]


def test_임포트가_늘어나면_잡는다(tmp_path: Path) -> None:
    _클로드_파일을_쓴다(tmp_path, "@docs/constitution/principles.md\n@docs/constitution/tech.md\n")

    problems = claude_md_problems(tmp_path)

    assert len(problems) == 1
    assert "tech.md" in problems[0]


def test_이백_한_줄이면_잡는다(tmp_path: Path) -> None:
    _클로드_파일을_쓴다(tmp_path, "@docs/constitution/principles.md\n" + "줄\n" * 200)

    problems = claude_md_problems(tmp_path)

    assert len(problems) == 1
    assert "201줄" in problems[0]


def test_이_저장소의_CLAUDE_md_는_지금_문제가_없다() -> None:
    assert claude_md_problems() == []


# 임포트된 파일 안의 상대 경로. 임포트된 파일은 루트에서 읽혀 형제 파일을 이름만으로 가리키면 깨진다
# (대기열 32, PR #43 이 헌법 버전을 못 찾았다).


def _헌법을_쓴다(root: Path, 본문: str) -> None:
    _파일을_둔다(root, "docs/constitution/principles.md", 본문)


def test_임포트된_파일의_형제_상대_경로를_잡는다(tmp_path: Path) -> None:
    _파일을_둔다(tmp_path, "docs/constitution/tech.md")
    _헌법을_쓴다(tmp_path, "스택은 `tech.md`, 색인은 `docs/constitution/README.md`.\n")
    _파일을_둔다(tmp_path, "docs/constitution/README.md")

    problems = imported_files_with_dead_paths(tmp_path)

    assert len(problems) == 1
    assert "`tech.md`" in problems[0]


def test_전체_경로와_glob_과_디렉터리는_통과한다(tmp_path: Path) -> None:
    _파일을_둔다(tmp_path, ".claude/rules/core.md")
    _파일을_둔다(tmp_path, "docs/adr/0001-x.md")
    _헌법을_쓴다(
        tmp_path, "세부는 `.claude/rules/*.md`, 결정은 `docs/adr/`, 판정은 `tools/x.py`.\n"
    )
    _파일을_둔다(tmp_path, "tools/x.py")

    assert imported_files_with_dead_paths(tmp_path) == []


def test_경로가_아닌_백틱은_보지_않는다(tmp_path: Path) -> None:
    _헌법을_쓴다(
        tmp_path, "`Any`, `cast`, `type: ignore`, `agent_os.core`, `main → sdk`, `run_id`.\n"
    )

    assert imported_files_with_dead_paths(tmp_path) == []


def test_임포트_대상_파일이_없으면_그것부터_잡는다(tmp_path: Path) -> None:
    problems = imported_files_with_dead_paths(tmp_path)

    assert len(problems) == 1
    assert "principles.md" in problems[0]


def test_이_저장소의_임포트된_파일_경로는_지금_다_살아_있다() -> None:
    assert imported_files_with_dead_paths() == []


# 루트 밖의 지침 파일. `next dev` 는 에이전트를 감지하면 앱 폴더에 AGENTS.md 와
# `@AGENTS.md` 한 줄짜리 CLAUDE.md 를 만든다(ADR 0021). 지침을 `.claude/rules/*.md` + `paths`
# 에 둔다는 결정(ADR 0004)이 조용히 우회된다. 원인과 무관하게 결과를 본다.


def test_루트_밖의_CLAUDE_md_와_AGENTS_md_를_잡는다(tmp_path: Path) -> None:
    _클로드_파일을_쓴다(tmp_path, "# 루트\n")
    _파일을_둔다(tmp_path, "web/apps/admin/AGENTS.md", "# Next 가 만든 것\n")
    _파일을_둔다(tmp_path, "web/apps/admin/CLAUDE.md", "@AGENTS.md\n")
    _파일을_둔다(tmp_path, "docs/CLAUDE.md", "# 지역 지침\n")

    problems = nested_instruction_files(tmp_path)

    assert [p.split(":", 1)[0] for p in problems] == [
        "docs/CLAUDE.md",
        "web/apps/admin/AGENTS.md",
        "web/apps/admin/CLAUDE.md",
    ]
    assert ".claude/rules" in problems[0]


def test_node_modules_와_워크트리_아래의_지침_파일은_보지_않는다(tmp_path: Path) -> None:
    """패키지가 싣고 온 AGENTS.md 와 다른 체크아웃의 루트 CLAUDE.md 는 이 저장소의 지침이 아니다."""
    _파일을_둔다(tmp_path, "web/node_modules/next/AGENTS.md")
    _파일을_둔다(tmp_path, "web/node_modules/.pnpm/pkg/node_modules/pkg/CLAUDE.md")
    _파일을_둔다(tmp_path, ".claude/worktrees/02-x/CLAUDE.md")
    _파일을_둔다(tmp_path, ".venv/Lib/site-packages/pkg/AGENTS.md")

    assert nested_instruction_files(tmp_path) == []


def test_이_저장소의_루트_밖에는_지침_파일이_없다() -> None:
    assert nested_instruction_files() == []


def _CLI_로_검사한다(root: Path) -> subprocess.CompletedProcess[str]:
    """다른 검사는 통과하는 최소 트리를 깔고 CLI 진입점을 부른다. 루트는 첫 인자다."""
    _클로드_파일을_쓴다(root, "@docs/constitution/principles.md\n")
    _헌법을_쓴다(root, "# 원칙\n")
    _사본을_만든다(root, 센티널을_넣을_스킬=set(PATCHED_SKILLS))
    return subprocess.run(
        [sys.executable, str(ROOT / "tools" / "check_instructions.py"), str(root)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=ROOT,
        env={**os.environ, "PYTHONUTF8": "1"},
        check=False,
    )


def test_CLI_진입점이_임시_트리의_중첩_지침_파일을_출력한다(tmp_path: Path) -> None:
    _파일을_둔다(tmp_path, "web/apps/admin/AGENTS.md")

    process = _CLI_로_검사한다(tmp_path)

    assert process.returncode == 1
    assert "web/apps/admin/AGENTS.md:" in process.stdout


# 훅의 stdin. 훅 환경은 cp949 라 텍스트 stdin 은 한글을 깨뜨리고 조용히 exit 0 이 된다(대기열 25).


def test_텍스트_stdin_을_읽는_줄을_잡는다() -> None:
    source = "import json\nimport sys\n\npayload = json.load(sys.stdin)\nraw = sys.stdin.read()\n"

    assert text_stdin_lines(source) == [4, 5]


def test_from_import_한_stdin_도_잡는다() -> None:
    source = "from sys import stdin\n\nraw = stdin.read()\n"

    assert text_stdin_lines(source) == [1]


def test_바이트_stdin_은_통과한다() -> None:
    source = "import json\nimport sys\n\npayload = json.load(sys.stdin.buffer)\n"

    assert text_stdin_lines(source) == []


def test_독스트링의_stdin_낱말은_세지_않는다() -> None:
    source = (
        '"""stdin 으로 받는다. sys.stdin 이 텍스트면 깨진다."""\nimport sys\nx = sys.stdin.buffer\n'
    )

    assert text_stdin_lines(source) == []


def test_텍스트_stdin_훅을_파일과_줄로_보고한다(tmp_path: Path) -> None:
    _파일을_둔다(tmp_path, "tools/hook_x.py", "import sys\nraw = sys.stdin.read()\n")
    _파일을_둔다(tmp_path, "tools/hook_y.py", "import sys\nraw = sys.stdin.buffer.read()\n")

    problems = hooks_reading_text_stdin(tmp_path)

    assert len(problems) == 1
    assert problems[0].startswith("tools/hook_x.py:2:")


def test_이_저장소의_훅은_지금_전부_바이트로_읽는다() -> None:
    assert hooks_reading_text_stdin() == []


def test_CLI_진입점이_임시_트리의_빨강을_출력한다(tmp_path: Path) -> None:
    """검사 아홉을 모으는 main 의 배관을 한 번은 실제로 부른다(tests.md). 루트는 첫 인자."""
    _파일을_둔다(tmp_path, ".claude/rules/nopaths.md", "# paths 없는 규칙\n")

    process = _CLI_로_검사한다(tmp_path)

    assert process.returncode == 1
    assert "paths 프론트매터 없음" in process.stdout
