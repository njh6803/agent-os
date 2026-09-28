"""tools/hook_git_main_commit.py 의 순수 함수와 브랜치 읽기. main 은 실제 실행으로 확인한다."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from tools.hook_git_main_commit import commits_in, current_branch, deny_reason, reason_for


def test_명령_위치의_git_commit_을_잡는다() -> None:
    assert commits_in("git add -A && git commit -m 'feat: x'")
    assert commits_in("git commit -F .git/MSG")
    assert commits_in("cd sub; git -C . commit --amend --no-edit")
    assert commits_in('[ "$(git branch --show-current)" = main ] && git commit -m x')


def test_커밋이_아닌_git_명령은_잡지_않는다() -> None:
    assert not commits_in("git log --oneline -5")
    assert not commits_in("git status --short && git diff")
    assert not commits_in("gh pr merge 12 --squash")


def test_데이터로_든_문구는_잡지_않는다() -> None:
    """echo·heredoc·커밋 메시지 안의 `git commit` 은 실행이 아니다(hook_pr_next_session 과 같다)."""
    assert not commits_in("echo 'git commit 은 나중에'")
    assert not commits_in("cat <<'EOF' > note.md\ngit commit -m x\nEOF")
    assert not commits_in('git commit-tree HEAD^{tree} -m "x"')


def test_인용된_옵션_값_뒤의_commit_도_잡는다() -> None:
    """PR #91 리뷰: 인용을 지우면 commit 이 -c 의 값 자리로 밀린다."""
    assert commits_in('git -c "user.name=작성자" commit -m x')


def test_보호_브랜치_위의_커밋만_막는다() -> None:
    reason = reason_for("git commit -m x", "main")

    assert reason is not None
    assert "main" in reason
    assert reason_for("git commit -m x", "feature/01-x") is None
    assert reason_for("git commit -m x", None) is None
    assert reason_for("git log", "main") is None
    assert deny_reason("chore/x") is None


def _저장소를_만든다(path: Path, 브랜치: str) -> None:
    subprocess.run(["git", "init", "-q", "-b", 브랜치, str(path)], check=True)


def test_현재_브랜치를_읽는다(tmp_path: Path) -> None:
    _저장소를_만든다(tmp_path / "on-main", "main")
    _저장소를_만든다(tmp_path / "on-topic", "chore/x")

    assert current_branch(str(tmp_path / "on-main")) == "main"
    assert current_branch(str(tmp_path / "on-topic")) == "chore/x"


def test_환경의_GIT_DIR_을_무시한다(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """pre-commit 이 워크트리에서 훅을 돌릴 때 git 이 내보내는 값이다. 읽을 것은 cwd 의 저장소다."""
    _저장소를_만든다(tmp_path / "on-main", "main")
    _저장소를_만든다(tmp_path / "on-topic", "chore/x")
    monkeypatch.setenv("GIT_DIR", str(tmp_path / "on-main" / ".git"))

    assert current_branch(str(tmp_path / "on-topic")) == "chore/x"


def test_저장소가_아니면_None이다(tmp_path: Path) -> None:
    """게이트가 아니라 안전장치다. 저장소 밖에서는 막지 않는다."""
    (tmp_path / "plain").mkdir()

    assert current_branch(str(tmp_path / "plain")) is None
