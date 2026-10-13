"""tools/hook_bash_commit_msg.py 의 함수. 판정은 tools/check_commit_msg.py 의 사본을 실제로 띄워
받는다. main 은 실제 실행(tools/run_hooks.py)으로 본다."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from tools.check_commit_msg import problems_for
from tools.hook_bash_commit_msg import (
    MessageFile,
    checker_for,
    deny_reason,
    message_files,
    problems_of,
    resolve,
)

ROOT = Path(__file__).resolve().parents[2]
# 대기열 222 셋째 사건(일지 2026-10-13-30)의 제목 길이 76자를 흉내 낸다.
_긴_제목 = "chore: " + "가" * 69
_맞는_제목 = "chore: 커밋 메시지 제목을 먼저 대 본다"
_HOME = "/home/u"


def _저장소(path: Path, *, commit_msg_hook: bool = True) -> Path:
    """`.git` 이 있는 폴더. commit-msg 판정을 부르는 pre-commit 설정과 그 스크립트의 사본을 둔다."""
    (path / ".git").mkdir(parents=True)
    (path / "tools").mkdir()
    shutil.copy(ROOT / "tools" / "check_commit_msg.py", path / "tools" / "check_commit_msg.py")
    entry = "uv run python tools/check_commit_msg.py" if commit_msg_hook else "uv run ruff check"
    (path / ".pre-commit-config.yaml").write_text(f"entry: {entry}\n", encoding="utf-8")
    return path


@pytest.fixture
def 저장소(tmp_path: Path) -> str:
    """제목이 긴 `long.txt` 와 맞는 `good.txt` 를 루트와 하위 폴더 `sub` 에 둔 저장소."""
    repo = _저장소(tmp_path / "repo")
    for folder in (repo, repo / "sub"):
        folder.mkdir(exist_ok=True)
        (folder / "long.txt").write_text(f"{_긴_제목}\n\n본문\n", encoding="utf-8")
        (folder / "good.txt").write_text(f"{_맞는_제목}\n\n본문\n", encoding="utf-8")
    return repo.as_posix()


def _파일들(command: str) -> list[str]:
    return [message.file for message in message_files(command)]


def test_git_commit_의_F_와_file_인자를_찾는다() -> None:
    assert _파일들("git commit -F msg.txt") == ["msg.txt"]
    assert _파일들("git commit -Fmsg.txt") == ["msg.txt"]
    assert _파일들("git commit --file msg.txt") == ["msg.txt"]
    assert _파일들("git commit --file=msg.txt") == ["msg.txt"]
    assert _파일들("git commit -aF msg.txt") == ["msg.txt"]
    assert _파일들("git commit --amend -F 'a b.txt'") == ["a b.txt"]


def test_줄_끝_역슬래시로_이은_경로도_찾는다() -> None:
    """트랜스크립트에 흔한 모양이다(명세 축 셀프 리뷰가 잡았다)."""
    assert _파일들("git commit -F \\\n  msg.txt") == ["msg.txt"]


def test_SKIP_으로_commit_msg_를_건너뛰면_보지_않는다() -> None:
    assert _파일들("SKIP=commit-msg git commit -F msg.txt") == []
    assert _파일들("SKIP=ruff-check,commit-msg git commit -F msg.txt") == []
    assert _파일들("SKIP=ruff-check git commit -F msg.txt") == ["msg.txt"]


def test_F_가_여럿이면_마지막_것만_본다() -> None:
    """git 은 마지막 `-F` 를 메시지로 쓴다. 앞의 것으로 막으면 거짓 양성이다."""
    assert _파일들("git commit -F bad.txt -F good.txt") == ["good.txt"]


def test_git_의_C_폴더를_함께_준다() -> None:
    assert message_files("git -C sub commit -F msg.txt") == [MessageFile("sub", "msg.txt")]
    assert message_files("git -C a -C b commit -F m") == [MessageFile("a/b", "m")]


def test_체인과_줄바꿈_뒤의_커밋도_찾는다() -> None:
    command = "uv run pytest -q && git commit -F a.txt; echo ok\ngit commit -F b.txt"

    assert _파일들(command) == ["a.txt", "b.txt"]


def test_다른_옵션의_값은_파일로_보지_않는다() -> None:
    assert _파일들("git commit -m F") == []
    assert _파일들("git commit -mFix") == []
    assert _파일들("git commit --author F -m x") == []
    assert _파일들("git -c user.name=F commit -m x") == []
    assert _파일들("git commit -- -F msg.txt") == []


def test_커밋이_아니거나_표준_입력이면_찾지_않는다() -> None:
    """못 보는 것: `-F -`(heredoc 으로 넘긴 메시지)와 `-m` 은 보지 않는다."""
    assert _파일들("git commit -F - <<'EOF'\nchore: x\nEOF") == []
    assert _파일들("git log -F x") == []
    assert _파일들("echo git commit -F x") == []
    assert _파일들('git commit -m "chore: x"') == []


def test_git_을_다른_이름으로_부르면_찾지_않는다() -> None:
    """못 보는 것: `command git`, 전체 경로."""
    assert _파일들("command git commit -F msg.txt") == []
    assert _파일들("/usr/bin/git commit -F msg.txt") == []


@pytest.mark.parametrize(
    "command",
    [
        "git commit --no-verify -F msg.txt",
        "git commit -nF msg.txt",
        "git commit -e -F msg.txt",
        "git commit --edit -F msg.txt",
        "git commit --squash=HEAD -F msg.txt",
        "git commit --fixup HEAD -F msg.txt",
        "git commit --cleanup=verbatim -F msg.txt",
    ],
)
def test_메시지가_파일_그대로가_아니거나_훅을_건너뛰는_커밋은_보지_않는다(command: str) -> None:
    assert message_files(command) == []


def test_같은_명령에서_쓰는_파일은_보지_않는다() -> None:
    """PreToolUse 에서는 아직 없거나 옛 내용이다. 옛 내용으로 막으면 거짓 양성이다."""
    assert _파일들("printf 'chore: x\\n' > msg.txt && git commit -F msg.txt") == []
    assert _파일들("cp a.txt msg.txt; git commit -F msg.txt") == []


def test_앞에_cd_가_있으면_보지_않는다() -> None:
    """못 보는 것: 상대 경로가 어디서 풀릴지 모른다."""
    assert _파일들("cd sub && git commit -F msg.txt") == []
    assert _파일들("git commit -F msg.txt && cd sub") == ["msg.txt"]


def test_heredoc_본문의_작은따옴표는_shlex_가_거절해_찾지_않는다() -> None:
    """못 보는 것: 짝 없는 따옴표와 heredoc 본문의 작은따옴표."""
    assert _파일들("git commit -F 'msg.txt") == []
    assert _파일들("git commit -F msg.txt\ncat <<EOF\ndon't\nEOF") == []


def test_파일을_cwd_에서_푼다(tmp_path: Path) -> None:
    cwd = tmp_path.as_posix()

    assert resolve("msg.txt", cwd, _HOME) == f"{cwd}/msg.txt"
    assert resolve("/c/x/msg.txt", cwd, _HOME) == "C:/x/msg.txt"
    assert resolve("~/msg.txt", cwd, _HOME) == "/home/u/msg.txt"
    assert resolve("$TMP/msg.txt", cwd, _HOME) is None


def test_판정_스크립트는_커밋하는_저장소의_것이다(tmp_path: Path) -> None:
    repo = _저장소(tmp_path / "repo")
    (repo / "sub").mkdir()
    bare = _저장소(tmp_path / "bare", commit_msg_hook=False)

    assert checker_for((repo / "sub").as_posix()) == f"{repo.as_posix()}/tools/check_commit_msg.py"
    assert checker_for(bare.as_posix()) is None
    assert checker_for((tmp_path / "nowhere").as_posix()) is None


def test_판정은_commit_msg_훅과_같다(저장소: str) -> None:
    checker = f"{저장소}/tools/check_commit_msg.py"

    assert problems_of(f"{저장소}/long.txt", checker) == problems_for(_긴_제목)
    assert problems_of(f"{저장소}/good.txt", checker) == []


def test_판정_문장_없이_끝나거나_시간을_넘기면_지나간다(tmp_path: Path) -> None:
    """못 보는 것: 자식이 시간 제한을 넘기거나 판정 문장 없이 끝난다."""
    silent = tmp_path / "silent.py"
    silent.write_text("raise SystemExit(1)\n", encoding="utf-8")
    slow = tmp_path / "slow.py"
    slow.write_text(
        "import time\ntime.sleep(5)\nprint('x')\nraise SystemExit(1)\n", encoding="utf-8"
    )

    assert problems_of("any.txt", silent.as_posix()) == []
    assert problems_of("any.txt", slow.as_posix(), timeout=0.5) == []


def test_제목이_걸리는_커밋을_막는다(저장소: str) -> None:
    reason = deny_reason("git commit -F long.txt", 저장소, _HOME)

    assert reason is not None
    assert "76자 > 72자" in reason
    assert "대기열 222" in reason


def test_절대_경로와_C_로_가리킨_파일도_막는다(저장소: str, tmp_path: Path) -> None:
    outside = tmp_path.as_posix()

    assert deny_reason(f"git -C {저장소} commit -F {저장소}/long.txt", outside, _HOME)
    assert deny_reason(f"git -C {저장소}/sub commit -F long.txt", outside, _HOME)
    assert deny_reason("git -C sub commit -F long.txt", 저장소, _HOME)


def test_제목이_맞으면_지나간다(저장소: str) -> None:
    assert deny_reason("git commit -F good.txt", 저장소, _HOME) is None
    assert deny_reason("git commit -F long.txt -F good.txt", 저장소, _HOME) is None


def test_commit_msg_판정이_없는_저장소는_지나간다(tmp_path: Path) -> None:
    bare = _저장소(tmp_path / "bare", commit_msg_hook=False)
    (bare / "long.txt").write_text(f"{_긴_제목}\n", encoding="utf-8")

    assert deny_reason("git commit -F long.txt", bare.as_posix(), _HOME) is None


def test_파일이_없으면_지나간다(저장소: str) -> None:
    assert deny_reason("git commit -F none.txt", 저장소, _HOME) is None
