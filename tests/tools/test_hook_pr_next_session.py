"""tools/hook_pr_next_session.py 의 순수 함수. stdin 을 읽는 main 은 실제 실행으로 확인한다."""

from __future__ import annotations

from tools.hook_pr_next_session import action_for, context_for


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


def test_셸이_아닌_도구의_명령은_보지_않는다() -> None:
    assert action_for("Write", "gh pr create") is None
    assert action_for("Bash", None) is None


def test_계기_문장은_next_session_을_가리키고_동사가_다르다() -> None:
    create = context_for("create")
    merge = context_for("merge")

    assert "next-session" in create and "next-session" in merge
    assert "여는" in create
    assert "병합하는" in merge
