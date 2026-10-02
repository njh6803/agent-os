"""tools/hook_pr_next_session.py 의 순수 함수. stdin 을 읽는 main 은 실제 실행으로 확인한다."""

from __future__ import annotations

import json
from typing import TypedDict

from tools.hook_pr_next_session import MCP_TOOLS, SHELL_TOOLS, action_for, context_for
from tools.run_hooks import SETTINGS, registration_command

HOOK_COMMAND = registration_command("hook_pr_next_session.py")


# 매처를 읽는 모양. 같은 스키마가 tools/check_instructions.py 와 tools/run_hooks.py 에 비공개로
# 있고, run_hooks 의 것은 매처를 읽지 않는다. 테스트 하나를 위해 도구의 표면을 넓히지 않는다.
class _HookEntry(TypedDict, total=False):
    command: str


class _HookGroup(TypedDict, total=False):
    matcher: str
    hooks: list[_HookEntry]


class _Settings(TypedDict, total=False):
    hooks: dict[str, list[_HookGroup]]


def test_gh_pr_create는_PR을_여는_명령이다() -> None:
    command = 'gh pr create --title "feat: x" --body-file body.md'

    assert action_for("Bash", command) == "create"


def test_gh_pr_merge는_PowerShell에서도_PR을_병합하는_명령이다() -> None:
    assert action_for("PowerShell", "gh pr merge 27 --squash --delete-branch") == "merge"
    chained = "gh pr merge --squash --delete-branch && git checkout main"
    assert action_for("Bash", chained) == "merge"


def test_PR을_열거나_병합하지_않는_명령은_None이다() -> None:
    for command in (
        "gh pr view --json number,mergeable",
        "gh pr checks --watch",
        'gh pr comment 27 --body "@coderabbitai review"',
        "gh pr list",
        "git push -u origin feature/02-read-the-trace",
    ):
        assert action_for("Bash", command) is None, command


def test_GitHub_MCP의_PR_도구는_이름으로_안다() -> None:
    assert action_for("mcp__plugin_github_github__create_pull_request", None) == "create"
    assert action_for("mcp__plugin_github_github__merge_pull_request", None) == "merge"


def test_클라우드_세션의_GitHub_MCP_도구도_이름으로_안다() -> None:
    """claude.ai 클라우드 세션의 GitHub 도구는 플러그인 접두가 없다.

    대기열 79, 일지 2026-10-01-05.
    """
    assert action_for("mcp__github__create_pull_request", None) == "create"
    assert action_for("mcp__github__merge_pull_request", None) == "merge"


def test_settings의_매처와_훅이_아는_도구가_같다() -> None:
    """이름을 훅에만 더하면 등록이 그 도구에 훅을 걸지 않고, 매처에만 더하면 훅이 조용히 지나간다.

    tools/run_hooks.py 는 훅을 이름으로 부르므로 매처를 보지 않는다.
    """
    settings: _Settings = json.loads(SETTINGS.read_text(encoding="utf-8"))
    matchers = [
        group.get("matcher", "")
        for group in settings.get("hooks", {}).get("PostToolUse", [])
        if any(entry.get("command") == HOOK_COMMAND for entry in group.get("hooks", []))
    ]

    assert len(matchers) == 1
    assert set(matchers[0].split("|")) == SHELL_TOOLS | set(MCP_TOOLS)


def test_셸이_아닌_도구의_명령은_보지_않는다() -> None:
    assert action_for("Write", "gh pr create") is None
    assert action_for("Bash", None) is None


def test_계기_문장은_next_session_을_가리키고_동사가_다르다() -> None:
    create = context_for("create")
    merge = context_for("merge")

    assert "next-session" in create and "next-session" in merge
    assert "여는" in create
    assert "병합하는" in merge


def test_데이터로_품은_gh_pr은_계기가_아니다() -> None:
    """echo·printf·커밋 메시지·`-c` 문자열 안의 문구는 명령 위치가 아니다(CodeRabbit, PR #28)."""
    for command in (
        "echo 'gh pr create --title x'",
        "printf 'gh pr merge %s' 28",
        'git commit -m "chore: gh pr merge 뒤에 next-session 계기를 넣는다"',
        "uv run python -c \"print({'command': 'gh pr create'})\"",
    ):
        assert action_for("Bash", command) is None, command


def test_heredoc_본문의_gh_pr은_계기가_아니다() -> None:
    quoted = "cat <<'EOF' > run.sh\ngh pr merge 28 --squash\nEOF"
    tabbed = "cat <<-EOF > run.sh\n\tgh pr create --fill\n\tEOF"

    assert action_for("Bash", quoted) is None
    assert action_for("Bash", tabbed) is None


def test_명령_위치의_gh_pr은_접두어_뒤에_있어도_계기다() -> None:
    for command, action in (
        ("PYTHONUTF8=1 gh pr create --fill", "create"),
        ("cd /c/project/agent && gh pr merge 28 --squash --delete-branch", "merge"),
        ("gh pr create --title x --body-file - <<'EOF'\nbody\nEOF", "create"),
        ("  (gh pr merge 28)", "merge"),
        ("git push -u origin HEAD\ngh pr create --fill", "create"),
    ):
        assert action_for("Bash", command) == action, command


def test_따옴표_안의_분리자는_명령_위치를_만들지_않는다() -> None:
    """인용 구간 안의 `;`·`&&`·개행은 데이터다(셀프 리뷰 Spec 축, PR #28)."""
    for command in (
        "echo 'a && gh pr create'",
        "echo 'gh pr create; gh pr merge'",
        'git commit -m "fix: a; gh pr merge 28"',
        'git commit -m "a\ngh pr merge 28 뒤에"',
    ):
        assert action_for("Bash", command) is None, command


def test_치환과_인용된_환경변수_뒤의_gh_pr도_명령_위치다() -> None:
    assert action_for("Bash", "PR_URL=$(gh pr create --fill)") == "create"
    assert action_for("Bash", "FOO='a b' gh pr merge 28") == "merge"
