"""tools/hook_env_read.py 의 순수 함수. stdin 을 읽는 main 은 실제 실행으로 확인한다.

대기열 43 — 감사 중 grep 한 번에 `.env` 의 키가 도구 출력에 실렸다. 발동해야 할 것과 발동하지
말아야 할 것을 반씩 둔다. 뒤의 것이 거짓 양성의 경계다. 첫 구현의 구멍 열둘과 오탐 아홉은
2026-09-28 적대 검증 워크플로가 찾았고 그 입력들이 여기 있다.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from tools.hook_env_read import (
    deny_reason_for_command,
    deny_reason_for_grep_tool,
    env_file_name,
    reason_for,
)


@pytest.mark.parametrize(
    "명령",
    [
        "cat .env",
        "cat '.env'",
        'head -n 1 "C:/project/agent/.env"',
        "grep ANTHROPIC .env",
        "grep -e ANTHROPIC .env",
        "sed -n 1p ../.env",
        "awk '{print $1}' .env",
        "less .env.local",
        "source .env",
        ". .env",
        "sudo cat .env",
        "\\cat .env",
        "/usr/bin/cat .env",
        "timeout 5 cat .env",
        "timeout -k 3 5 cat .env",
        "cat .ENV",
        "cat .e*",
        "head -n 1 .env*",
        "sed -n 1p '.e?v'",
        "nice -n 10 cat .env",
        "env cat .env",
        "PYTHONUTF8=1 cat .env | head -n 1",
        "ls && (cat .env)",
        "echo start; tail -n 2 .env",
        "if [ -f .env ]; then cat .env; fi",
        "while true; do head -n 1 .env; done",
        "cat \\\n  .env",
        "diff .env .env.example",
        "paste .env x.txt",
        "git diff --no-index .env .env.example",
        "find . -name '.env*' -exec cat {} +",
        'bash -c "cat .env"',
        "sh -lc 'grep KEY .env'",
        'eval "cat .env"',
        'echo "$(cat .env)"',
        "echo `cat .env`",
        "diff <(cat .env) <(cat .env.example)",
    ],
)
def test_env_를_읽는_명령을_막는다(명령: str) -> None:
    reason = deny_reason_for_command(명령)

    assert reason is not None
    assert ".env.example" in reason


def test_입력_리다이렉션도_읽기다() -> None:
    assert deny_reason_for_command("while read l; do echo $l; done < .env") is not None
    assert deny_reason_for_command('echo "$(< .env)"') is not None
    assert deny_reason_for_command('done < "$PWD/.env"') is not None
    assert deny_reason_for_command("cat < .env.example") is None


@pytest.mark.parametrize(
    "명령",
    [
        "grep -rn ANTHROPIC .",
        "grep -r ANTHROPIC",
        "grep -Rin -A 3 KEY",
        "grep -rC3 KEY",
        "grep --recursive KEY ./",
        "grep -rn KEY ..",
        "grep -rn KEY 2>/dev/null",
        "grep -rn KEY 2>&1 | head -n 20",
        "grep -rn KEY > hits.txt",
        'grep -rn KEY "$PWD"',
        'grep -rn KEY "$CLAUDE_PROJECT_DIR"',
        "grep -rn --include=* KEY .",
        "rg --hidden --no-ignore KEY",
        "rg --hidden -u KEY",
        "rg -uu KEY .",
        "rg -nuu KEY",
        "rg -uu KEY 2>/dev/null",
        "rg -uu -g '.env*' KEY",
    ],
)
def test_env_를_빼지_않은_저장소_전체_grep_을_막는다(명령: str) -> None:
    """감사에서 실제로 키가 실린 모양이다. grep 은 숨김 파일을 건너뛰지 않는다."""
    reason = deny_reason_for_command(명령)

    assert reason is not None
    assert "저장소 전체" in reason


def test_루트를_절대_경로나_상위_체인으로_줘도_훑기다(tmp_path: Path) -> None:
    """서브에이전트는 절대 경로를 쓴다. 판정은 cwd 기준으로 푼 경로에 `.env` 가 있는지다."""
    (tmp_path / ".env").write_text("K=v\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "deep").mkdir()
    root = tmp_path.as_posix()

    assert deny_reason_for_command(f"grep -rn KEY {root}", cwd=str(tmp_path / "src")) is not None
    assert (
        deny_reason_for_command("grep -rn KEY ../..", cwd=str(tmp_path / "src" / "deep"))
        is not None
    )
    assert deny_reason_for_command(f"rg -uu KEY {root}", cwd=str(tmp_path)) is not None
    assert deny_reason_for_command(f"grep -rn KEY {root}/src", cwd=str(tmp_path)) is None
    assert deny_reason_for_command("grep -rn KEY src/deep", cwd=str(tmp_path)) is None


@pytest.mark.parametrize(
    "명령",
    [
        "cat .env.example",
        "grep ANTHROPIC .env.example",
        "uv run --env-file .env pytest -m llm",
        "ls -la .env",
        "stat .env",
        "grep -rn KEY src/ tests/",
        "grep -rn --exclude=.env* KEY .",
        "grep -rn --exclude .env KEY .",
        "grep -rn --include=*.py KEY .",
        "grep -n KEY pyproject.toml",
        "grep -n .env .gitignore",
        "grep -rn '\\.env\\.example' docs/",
        "git ls-files | grep .env",
        "git status --short | grep -c '.env'",
        "grep -rnE 'ANTHROPIC|OPENAI' src/",
        "grep -rn KEY \\\n  src/",
        "grep -rn KEY *",
        "rg KEY",
        "rg --hidden KEY .",
        "rg --no-ignore KEY",
        "rg --no-ignore-messages KEY",
        "rg -uu -g '!.env*' KEY",
        "rg -uu --glob=!.env* KEY .",
        "rg -uu -t py KEY",
        "rg -uu -g '*.py' KEY",
        "echo '.env is secret'",
        "cat <<'EOF' > note.md\ncat .env\nEOF",
        "cat > .env <<'EOF'\nK=v\nEOF",
        "cat .env.example > .env",
        'gh pr create --body "the hook denies < .env reads and cat .env"',
        "cat .envrc",
        "cat *",
        "cat *.py",
        "cat .env.ex*",
        "cat config.env",
        "cat docs/env.md",
        "printf 'ANTHROPIC_API_KEY=\\n' > .env",
        "[ -f .env ] && echo exists",
    ],
)
def test_읽지_않는_명령은_막지_않는다(명령: str) -> None:
    assert deny_reason_for_command(명령) is None


def test_env_파일_이름을_알아보고_example_은_뺀다() -> None:
    assert env_file_name(".env") == ".env"
    assert env_file_name(".ENV") == ".ENV"
    assert env_file_name("../.env.local") == ".env.local"
    assert env_file_name("$PWD/.env") == ".env"
    assert env_file_name("--file=.env") == ".env"
    assert env_file_name(".env.example") is None
    assert env_file_name(".Env.Example") is None
    assert env_file_name(".envrc") is None
    assert env_file_name("config.env") is None


def test_Grep_도구는_경로와_glob_을_본다() -> None:
    """Grep 도구는 glob 없이 훑을 때만 숨김 파일을 건너뛴다. 경로나 glob 이 닿으면 읽는다(실측)."""
    assert deny_reason_for_grep_tool(".env", None) is not None
    assert deny_reason_for_grep_tool("C:\\project\\agent\\.env", None) is not None
    assert deny_reason_for_grep_tool("C:/project/agent", ".env*") is not None
    assert deny_reason_for_grep_tool("C:/project/agent", ".env.*") is not None
    assert deny_reason_for_grep_tool("C:/project/agent", "*") is not None
    assert deny_reason_for_grep_tool("C:/project/agent", ".*") is not None
    assert deny_reason_for_grep_tool("C:/project/agent", "**/.env") is not None
    assert deny_reason_for_grep_tool(".env.example", None) is None
    assert deny_reason_for_grep_tool("C:/project/agent", ".env.example") is None
    assert deny_reason_for_grep_tool("src", "*.py") is None
    assert deny_reason_for_grep_tool(None, None) is None


def test_도구가_Grep_이면_경로를_Bash_면_명령을_판정한다() -> None:
    assert reason_for("Grep", {"path": ".env"}) is not None
    assert reason_for("Bash", {"command": "cat .env"}) is not None
    assert reason_for("Bash", {"command": "cat .env.example"}) is None
    assert reason_for("Bash", {}) is None


@pytest.mark.parametrize(
    "명령",
    [
        'for f in .env*; do cat "$f"; done',
        "ls -a | xargs cat",
        "python -c \"print(open('.env').read())\"",
        "cp .env copy.txt",
        "grep -rn KEY sub/",
        "cat C:\\Users\\me\\.env",
    ],
)
def test_독스트링이_못_본다고_적은_것은_정말_못_본다(명령: str) -> None:
    """못 본다는 주장도 잰다(.claude/rules/tools.md). 잡게 되면 독스트링을 고친다."""
    assert deny_reason_for_command(명령, cwd=None) is None
