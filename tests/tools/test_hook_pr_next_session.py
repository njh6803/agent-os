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
