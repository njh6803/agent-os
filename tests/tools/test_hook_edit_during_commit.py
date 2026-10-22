"""tools/hook_edit_during_commit.py 의 판정. 도는 커밋은 임시 저장소에서 실제로 멈춰 세운
`git commit` 프로세스로 찾는다(`tools.run_hooks.committing_repository`). 윈도는 PEB, 리눅스는
`/proc` 길이 돈다.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
from tools.hook_edit_during_commit import (
    Process,
    RunningCommit,
    argv_from_cmdline,
    checkout_of,
    commit_directory,
    deny_reason,
    edited_file,
    git_subcommand,
    is_launcher,
    parent_from_stat,
    running_commits,
    scan_processes,
)
from tools.run_hooks import committing_repository, registered_matchers

from tools import hook_edit_during_commit

HOOK = Path(__file__).parents[2] / "tools" / "hook_edit_during_commit.py"


@pytest.mark.parametrize(
    ("argv", "subcommand"),
    [
        pytest.param(["git", "commit", "-F", "msg.txt"], "commit", id="보통_커밋"),
        pytest.param(
            ["C:\\Program Files\\Git\\mingw64\\bin\\git.exe", "commit", "-q"],
            "commit",
            id="윈도_실행_파일",
        ),
        pytest.param(
            ["git", "-C", "x", "-c", "a=b", "--no-pager", "commit"], "commit", id="전역_옵션"
        ),
        pytest.param(["git", "--git-dir", "x/.git", "status"], "status", id="값을_먹는_전역_옵션"),
        pytest.param(["git", "log", "--grep", "commit"], "log", id="인자_속의_commit"),
        pytest.param(["git", "commit-tree", "abc"], "commit-tree", id="다른_하위_명령"),
        pytest.param(["git"], None, id="하위_명령_없음"),
        pytest.param(["git", "-c"], None, id="값이_빠진_전역_옵션"),
        pytest.param([], None, id="빈_명령_줄"),
    ],
)
def test_git_의_하위_명령을_전역_옵션_뒤에서_찾는다(
    argv: list[str], subcommand: str | None
) -> None:
    assert git_subcommand(argv) == subcommand


def test_런처는_세지_않고_그_자식인_실제_git_의_작업_디렉터리로_찾는다(tmp_path: Path) -> None:
    """윈도 git 의 런처(`cmd\\git.exe`)는 띄운 폴더 B 를 작업 디렉터리로 쥔 채 같은 명령 줄로 살고,
    실제 git 을 자식으로 띄운다. 작업 디렉터리만 본 첫 판은 B 에서 친 `git -C <A> commit` 을 B 의
    커밋으로도 읽었다(셀프 리뷰 명세 축). 자식 git 을 띄운 git 을 빼면 남는 것은 A 로 옮겨 간 실제
    git 이다."""
    main, side = _checkouts(tmp_path)
    argv = ("git", "-C", "../../..", "commit", "-m", "x")
    launcher = Process(10, "git.exe", argv, str(side), parent=1)
    real = Process(11, "git.exe", argv, str(main), parent=10)

    found = running_commits([launcher, real])

    assert found == [RunningCommit(11, str(checkout_of(str(main))))]


def test_리눅스의_명령_줄은_빈_낱말을_지킨다() -> None:
    """빈 낱말을 버리면 `-C` 가 `commit` 을 값으로 먹어 하위 명령을 놓친다(PR 직전
    `bug-perf-review`)."""
    argv = argv_from_cmdline(b"git\0-C\0\0commit\0-m\0x\0")

    assert argv == ("git", "-C", "", "commit", "-m", "x")
    assert git_subcommand(argv) == "commit"
    assert argv_from_cmdline(b"") == ()


@pytest.mark.parametrize(
    ("stat", "parent"),
    [
        pytest.param("4242 (git) S 4200 4242 4200 0 -1", 4200, id="보통"),
        pytest.param("4242 (my (odd) git) S 4200 4242", 4200, id="이름에_괄호와_공백"),
        pytest.param("4242 (git)", 0, id="잘린_줄"),
    ],
)
def test_리눅스의_부모_pid_는_이름_칸_뒤에서_센다(stat: str, parent: int) -> None:
    assert parent_from_stat(stat) == parent


def _checkouts(root: Path) -> tuple[Path, Path]:
    """주 체크아웃(`.git` 디렉터리)과 그 안의 연결된 워크트리(`.git` 파일). 이 저장소의
    `.claude/worktrees/<이름>` 과 같은 자리다."""
    main = root / "main"
    (main / ".git").mkdir(parents=True)
    (main / "tools").mkdir()
    side = main / ".claude" / "worktrees" / "side"
    (side / "tools").mkdir(parents=True)
    (side / ".git").write_text("gitdir: ../../../.git/worktrees/side\n", encoding="utf-8")
    return main, side


def test_위로_올라가_처음_git_이_있는_폴더가_체크아웃이다(tmp_path: Path) -> None:
    main, side = _checkouts(tmp_path)

    assert checkout_of(str(main / "tools")) == checkout_of(str(main))
    assert checkout_of(str(side / "tools")) == checkout_of(str(side))
    assert checkout_of(str(side)) != checkout_of(str(main))
    assert checkout_of(str(tmp_path)) is None


def test_고친_파일의_체크아웃에서_도는_커밋이면_막는다(tmp_path: Path) -> None:
    """PostToolUse 의 알림은 편집 뒤에 와서, 알림을 받고도 커밋이 실패했다(대기열 412). 그래서
    편집 전에 막고, 커밋이 끝난 뒤 같은 편집을 다시 하게 한다."""
    main, _ = _checkouts(tmp_path)
    checkout = checkout_of(str(main))
    assert checkout is not None
    file = main / "tools" / "x.py"
    file.write_text("x = 1\n", encoding="utf-8")

    reason = deny_reason(str(file), [RunningCommit(4321, checkout)])

    assert reason is not None
    assert "git commit" in reason
    assert "4321" in reason
    assert "막았다" in reason
    assert "대기열 293·412" in reason
    assert "끝난 뒤" in reason
    assert "이미 적용" not in reason
    # 커밋을 띄우지 않은 세션이 남긴 거짓 양성(못 보는 것)에 막혔을 때 기다릴 커밋이 없다.
    assert "띄운 커밋이 없으면 같은 편집을 한 번 다시 한다" in reason


def _git_layout(root: Path) -> dict[str, str]:
    """Git for Windows 의 배치. 런처 둘(`cmd`, `bin`)과 실제 git(`mingw64/bin`), 그리고 곁에
    `mingw64` 가 없는 `bin/git.exe`(cygwin 처럼 실제 git 이 `bin` 에 있는 꼴)."""
    install = root / "Git"
    paths = {
        "cmd": install / "cmd" / "git.exe",
        "bin": install / "bin" / "git.exe",
        "real": install / "mingw64" / "bin" / "git.exe",
        "cygwin": root / "cygwin64" / "bin" / "git.exe",
    }
    for path in paths.values():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"")
    return {name: str(path) for name, path in paths.items()}


def test_윈도_git_의_런처를_실행_파일_자리로_알아본다(tmp_path: Path) -> None:
    """런처는 곁의 `mingw64`(또는 `mingw32`, `clangarm64`) 아래 실제 git 이 있는 `cmd`·`bin` 의
    `git.exe` 다. 리눅스의 이름(`git`)과 실행 파일 자리를 읽지 못한 이름(`git.exe`)은 런처가
    아니다."""
    layout = _git_layout(tmp_path)

    assert is_launcher(layout["cmd"])
    assert is_launcher(layout["bin"])
    assert not is_launcher(layout["real"])
    assert not is_launcher(layout["cygwin"])
    assert not is_launcher("git.exe")
    assert not is_launcher("git")


def _repo_and_outside(root: Path) -> tuple[Path, Path]:
    """커밋하는 저장소 A(`repo`)와 커밋을 띄운 다른 체크아웃 B(`outside`)의 하위 폴더 `deep`."""
    repo, outside = root / "repo", root / "outside"
    (repo / ".git").mkdir(parents=True)
    (repo / "sub").mkdir()
    (outside / ".git").mkdir(parents=True)
    (outside / "deep").mkdir()
    return repo, outside / "deep"


@pytest.mark.parametrize(
    ("kind", "options", "where"),
    [
        pytest.param("cmd", ("-C", "{repo}"), "outside", id="런처_절대_-C"),
        pytest.param("bin", ("-C", "../../repo"), "outside", id="런처_상대_-C"),
        pytest.param("cmd", ("--work-tree={repo}",), "outside", id="런처_절대_work_tree"),
        pytest.param("cmd", ("--work-tree", "../../repo"), "outside", id="런처_상대_work_tree"),
        pytest.param("cmd", ("-C", "", "-C", "{repo}"), "outside", id="런처_빈_-C_는_건너뛴다"),
        pytest.param("real", ("-C", "{repo}"), "outside", id="실제_git_절대_-C_옮기기_전"),
        pytest.param("real", ("-C", "{repo}"), "repo", id="실제_git_절대_-C_옮긴_뒤"),
        pytest.param("real", ("-C", "{repo}", "-C", "sub"), "outside", id="실제_git_절대_뒤_상대"),
        pytest.param("real", ("-C", "../../repo"), "repo", id="실제_git_상대_-C_옮긴_뒤"),
        pytest.param("real", ("--work-tree={repo}",), "outside", id="실제_git_절대_work_tree"),
        pytest.param("git.exe", ("-C", "{repo}"), "outside", id="자리를_모르는_git_절대_-C"),
    ],
)
def test_커밋이_도는_작업_트리를_띄운_폴더가_아니라_명령_줄로_찾는다(
    tmp_path: Path, kind: str, options: tuple[str, ...], where: str
) -> None:
    """런처는 띄운 폴더를 작업 디렉터리로 쥔 채 살고, 실제 git 도 `-C` 를 풀어 작업 디렉터리를
    옮기기 전에는 띄운 폴더에 있다. 그 순간을 띄운 폴더의 커밋으로 세던 판이 부하 pytest 가 임시
    저장소에 친 커밋을 이 체크아웃의 커밋으로 두 번 알렸다(대기열 368,
    `.scratch/harness/probes/edit_during_commit_launcher.py`). 절대 경로 `-C` 는 옮기기 전과 뒤가
    같은 자리를 가리키고, 런처는 옮기지 않으므로 띄운 폴더에서 푼다. 옮긴 뒤의 실제 git 에 상대 경로
    `-C` 를 다시 얹으면 놓친다(PR 직전 `bug-perf-review`)."""
    layout = _git_layout(tmp_path / "install")
    image = layout.get(kind, kind)
    repo, deep = _repo_and_outside(tmp_path)
    cwd = deep if where == "outside" else repo
    argv = ("git", *(word.format(repo=repo.as_posix()) for word in options), "commit")

    found = running_commits([Process(7, image, argv, str(cwd))])

    assert found == [RunningCommit(7, str(checkout_of(str(repo))))]
    assert checkout_of(commit_directory(Process(7, image, argv, str(cwd)))) == checkout_of(
        str(repo)
    )


def test_못_보는_것_상대_경로의_실제_git_이_옮기기_전이면_띄운_폴더의_커밋으로_센다(
    tmp_path: Path,
) -> None:
    """거짓 양성이다. 상대 경로 `-C`·`--work-tree` 는 실제 git 이 이미 옮겼는지 알 수 없어 작업
    디렉터리를 그대로 믿는다. 옮기기 전의 순간이면 띄운 폴더의 편집을 막는다."""
    layout = _git_layout(tmp_path / "install")
    repo, deep = _repo_and_outside(tmp_path)
    argv = ("git", "-C", "../../repo", "commit")

    found = running_commits([Process(7, layout["real"], argv, str(deep))])

    assert found == [RunningCommit(7, str(checkout_of(str(deep))))]
    assert checkout_of(str(deep)) != checkout_of(str(repo))


@pytest.mark.parametrize("where", ["outside", "repo"])
def test_런처가_띄운_실제_git_의_상대_경로는_런처의_작업_디렉터리에서_푼다(
    tmp_path: Path, where: str
) -> None:
    """런처의 자식은 런처의 작업 디렉터리에서 시작해 같은 명령 줄을 받는다. 그래서 자식이 옮겼든
    옮기기 전이든 상대 경로를 런처의 작업 디렉터리에서 풀면 같은 자리다. 자식의 작업 디렉터리를 믿던
    판은 런처로 친 상대 경로의 네 갈래(갈래마다 60회차)에서 27·59·28·58회차를 거짓으로 셌다. 순간은
    자식 git 이나 자식이 끝난 뒤였다(`.scratch/harness/probes/edit_during_commit_launcher.py`)."""
    layout = _git_layout(tmp_path / "install")
    repo, deep = _repo_and_outside(tmp_path)
    argv = ("git", "-C", "../../repo", "commit")
    launcher = Process(10, layout["cmd"], argv, str(deep), parent=1)
    child = Process(11, layout["real"], argv, str(deep if where == "outside" else repo), parent=10)

    found = running_commits([launcher, child])

    assert found == [RunningCommit(11, str(checkout_of(str(repo))))]


@pytest.mark.parametrize("committing", ["main", "side"])
def test_주_체크아웃과_그_안의_워크트리는_다른_체크아웃이다(
    tmp_path: Path, committing: str
) -> None:
    """워크트리는 주 체크아웃의 폴더 아래에 있다. 경로의 머리만 보면 한쪽의 커밋을 다른 쪽의 편집에
    잇는다."""
    main, side = _checkouts(tmp_path)
    here, there = (main, side) if committing == "main" else (side, main)
    checkout = checkout_of(str(here))
    assert checkout is not None
    file = there / "tools" / "x.py"
    file.write_text("x = 1\n", encoding="utf-8")

    assert deny_reason(str(file), [RunningCommit(1, checkout)]) is None


def test_도는_커밋이_없거나_체크아웃_밖의_파일이면_알리지_않는다(tmp_path: Path) -> None:
    main, _ = _checkouts(tmp_path)
    checkout = checkout_of(str(main))
    assert checkout is not None
    inside = main / "tools" / "x.py"
    inside.write_text("x = 1\n", encoding="utf-8")
    outside = tmp_path / "scratch.md"
    outside.write_text("메모\n", encoding="utf-8")

    assert deny_reason(str(inside), []) is None
    assert deny_reason(str(outside), [RunningCommit(1, checkout)]) is None


def test_편집_도구_셋의_파일_경로를_읽는다() -> None:
    assert edited_file({"file_path": "C:/x/a.py", "old_string": "a"}) == "C:/x/a.py"
    assert edited_file({"notebook_path": "C:/x/b.ipynb", "new_source": "x"}) == "C:/x/b.ipynb"
    assert edited_file({"file_path": ""}) is None


def test_못_보는_것_셸로_고친_파일은_경로가_없어_알리지_않는다() -> None:
    """거짓 음성이다. 이 훅은 편집 도구 셋에만 붙고, Bash 의 `sed -i`·`>` 는 경로 칸이 없다."""
    assert edited_file({"command": "sed -i 's/a/b/' tools/x.py"}) is None


def test_git_프로세스의_커밋만_센다(tmp_path: Path) -> None:
    """git 을 감싸는 실행 파일(`hub commit`)은 세지 않는다. 그 아래에서 도는 git 이 센다."""
    main, _ = _checkouts(tmp_path)
    cwd = str(main)
    processes = [
        Process(1, "git.exe", ("git", "commit", "-m", "x"), cwd),
        Process(2, "git.exe", ("git", "status"), cwd),
        Process(3, "git", ("git", "-C", cwd, "commit"), cwd),
        Process(4, "hub.exe", ("hub", "commit", "-m", "x"), cwd),
    ]

    found = running_commits(processes)

    assert [commit.pid for commit in found] == [1, 3]
    assert {commit.checkout for commit in found} == {checkout_of(cwd)}


def test_못_보는_것_커밋이_아닌_검사가_도는_동안은_세지_않는다(tmp_path: Path) -> None:
    """거짓 음성이다. 같은 검사를 손으로 돌려도(`uv run pre-commit run`, `uv run pytest`) 그동안의
    편집은 알리지 않는다. git 의 `commit` 만 센다."""
    main, _ = _checkouts(tmp_path)
    processes = [
        Process(1, "uv.exe", ("uv", "run", "pre-commit", "run", "--all-files"), str(main)),
        Process(2, "python.exe", ("python", "-m", "pytest", "-q"), str(main)),
    ]

    assert running_commits(processes) == []


def test_못_보는_것_git_이_없는_작업_트리의_커밋은_세지_않는다(tmp_path: Path) -> None:
    """거짓 음성이다. 바깥 저장소를 `--git-dir` 로 쓰는 작업 트리(`.git` 이 없다)는 체크아웃을 찾지
    못해, 그 커밋도 그 안의 편집도 체크아웃이 없다."""
    work = tmp_path / "work"
    work.mkdir()
    argv = ("git", f"--git-dir={tmp_path}/bare.git", f"--work-tree={work}", "commit")
    file = work / "x.py"
    file.write_text("x = 1\n", encoding="utf-8")

    found = running_commits([Process(1, "git", argv, str(work))])

    assert found == []
    assert deny_reason(str(file), [RunningCommit(1, str(work))]) is None


# 윈도 git 의 런처. 이 PC 에서 세션의 PowerShell 도구가 `git` 을 이것으로 먼저 풀었고, 띄운 폴더를
# 작업 디렉터리로 쥔 채 실제 git 을 자식으로 띄운다. 런처가 없는 리눅스에서는 그 갈래가 보통
# `git` 으로 돈다.
LAUNCHER = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Git" / "cmd" / "git.exe"


@pytest.mark.parametrize(
    ("where", "prefix", "launcher"),
    [
        pytest.param("repo/sub", (), False, id="하위_폴더에서"),
        pytest.param("outside", ("-C", "{repo}"), False, id="다른_체크아웃에서_-C"),
        pytest.param("outside/deep", ("-C", "../../repo"), False, id="다른_체크아웃에서_상대_-C"),
        pytest.param(
            "outside",
            ("--git-dir={repo}/.git", "--work-tree={repo}"),
            False,
            id="다른_체크아웃에서_git_dir_와_work_tree",
        ),
        pytest.param("outside", ("-C", "{repo}"), True, id="다른_체크아웃에서_런처로_-C"),
        pytest.param(
            "outside/deep", ("-C", "../../repo"), True, id="다른_체크아웃에서_런처로_상대_-C"
        ),
    ],
)
def test_어디서_친_커밋이든_그_작업_트리의_체크아웃으로_찾는다(
    tmp_path: Path, where: str, prefix: tuple[str, ...], *, launcher: bool
) -> None:
    """실제 git 은 작업 디렉터리를 그 작업 트리 안으로 옮긴다. 런처는 띄운 폴더(여기서는 다른
    체크아웃)에 남으므로 세지 않아야 거짓 알림이 나지 않는다(셀프 리뷰 명세 축). 런처에 `-C` 를 얹던
    판은 실제 git 에도 얹어 상대 경로 `-C` 를 놓쳤다(PR 직전 `bug-perf-review`)."""
    if launcher and sys.platform == "win32":
        assert LAUNCHER.exists(), f"런처가 없다: {LAUNCHER}"
    executable = str(LAUNCHER) if launcher and sys.platform == "win32" else "git"
    repo, outside = tmp_path / "repo", tmp_path / "outside"
    (repo / "sub").mkdir(parents=True)
    git = [executable, "-c", "user.name=t", "-c", "user.email=t@localhost"]
    subprocess.run([*git, "init", "-q", "-b", "main", str(repo)], check=True, timeout=60)
    subprocess.run([*git, "init", "-q", "-b", "main", str(outside)], check=True, timeout=60)
    (outside / "deep").mkdir()
    subprocess.run(
        [*git, "-C", str(repo), "commit", "-q", "--allow-empty", "-m", "a"], check=True, timeout=60
    )
    hooks = repo / ".git" / "hooks"
    started, release = tmp_path / "started", tmp_path / "release"
    (hooks / "pre-commit").write_text(
        f'#!/bin/sh\n: > "{started.as_posix()}"\ni=0\n'
        f'while [ ! -f "{release.as_posix()}" ] && [ "$i" -lt 600 ]; do\n'
        "  sleep 0.1\n  i=$((i + 1))\ndone\n",
        encoding="utf-8",
        newline="\n",
    )
    # 리눅스 git 은 실행 권한이 없는 훅을 건너뛴다(PR 직전 `bug-perf-review`)
    (hooks / "pre-commit").chmod(0o755)
    (repo / "f.txt").write_text("x\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(repo), "add", "f.txt"], check=True, timeout=60)
    options = [word.format(repo=repo.as_posix()) for word in prefix]
    command = [
        *git,
        *options,
        "-c",
        f"core.hooksPath={hooks.as_posix()}",
        "commit",
        "-q",
        "-m",
        "x",
    ]
    process = subprocess.Popen(
        command,
        cwd=tmp_path / where,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        for _ in range(600):
            if started.exists() or process.poll() is not None:
                break
            time.sleep(0.05)
        assert started.exists()
        processes = scan_processes()
        assert processes is not None
        found = {commit.checkout for commit in running_commits(processes)}
        assert checkout_of(str(repo)) in found
        assert checkout_of(str(outside)) not in found
    finally:
        release.write_text("", encoding="utf-8")
        process.wait(timeout=60)


def test_못_보는_것_git_별칭으로_친_커밋은_세지_않는다(tmp_path: Path) -> None:
    """거짓 음성이다. 명령 줄의 하위 명령이 별칭 이름(`ci`)이라 `commit` 이 아니다."""
    main, _ = _checkouts(tmp_path)

    assert running_commits([Process(1, "git.exe", ("git", "ci", "-m", "x"), str(main))]) == []


def test_못_보는_것_윈도와_리눅스_밖에서는_프로세스를_읽지_않는다(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "platform", "darwin")

    assert scan_processes() is None


def test_못_보는_것_32비트_파이썬이면_윈도에서_프로세스를_읽지_않는다(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """PEB 는 x64 의 자리만 안다. 윈도 밖에서는 그 길이 없어, 같은 바꾸기로 리눅스 길이 그대로 도는
    것만 본다."""
    monkeypatch.setattr(hook_edit_during_commit, "_is_64bit", lambda: False)

    processes = scan_processes()

    if sys.platform == "win32":
        assert processes is None
    else:
        assert processes is not None


def test_멈춰_세운_커밋을_실제_프로세스에서_찾고_끝나면_놓는다(tmp_path: Path) -> None:
    """윈도에서는 Toolhelp 와 PEB, 리눅스에서는 `/proc` 길이 이 시험으로 돈다."""
    with committing_repository(tmp_path) as root:
        side = root / ".claude" / "worktrees" / "side"
        processes = scan_processes()
        assert processes is not None
        during = running_commits(processes)
        assert checkout_of(str(side)) in {commit.checkout for commit in during}
        assert checkout_of(str(root)) not in {commit.checkout for commit in during}
        if sys.platform == "win32":
            # 런처를 알아보려면 실행 파일의 전체 경로를 읽어야 한다
            images = {
                process.image for process in processes if process.pid in {c.pid for c in during}
            }
            assert images
            assert all(os.path.isabs(image) for image in images), images

    processes = scan_processes()
    assert processes is not None
    after = running_commits(processes)
    assert checkout_of(str(side)) not in {commit.checkout for commit in after}


def _run_hook(payload: dict[str, object]) -> str:
    result = subprocess.run(
        [sys.executable, str(HOOK)],
        input=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        capture_output=True,
        timeout=60,
        check=True,
    )
    return result.stdout.decode("utf-8")


def test_훅은_도는_커밋의_워크트리_편집만_막는다(tmp_path: Path) -> None:
    """stdin 의 바이트 페이로드부터 출력까지. 주 체크아웃의 편집은 그 폴더 아래 워크트리에서 커밋이
    돌아도 지나간다."""
    with committing_repository(tmp_path) as root:
        side_file = root / ".claude" / "worktrees" / "side" / "tracked.txt"
        main_file = root / "notes.md"
        main_file.write_text("메모\n", encoding="utf-8")

        firing = _run_hook(
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Edit",
                "tool_input": {"file_path": str(side_file), "old_string": "x", "new_string": "y"},
            }
        )
        quiet = _run_hook(
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Write",
                "tool_input": {"file_path": str(main_file), "content": "메모\n"},
            }
        )

    output = json.loads(firing)["hookSpecificOutput"]
    assert output["hookEventName"] == "PreToolUse"
    assert output["permissionDecision"] == "deny"
    assert "git commit" in output["permissionDecisionReason"]
    assert quiet == ""


def test_settings의_매처는_편집_도구_셋이고_편집_전에_돈다() -> None:
    """편집이 끝난 뒤(PostToolUse)에 알리던 판은 알림을 받고도 그 편집이 커밋을 실패시켰다(대기열
    412). 편집 전(PreToolUse)에 막는다."""
    assert registered_matchers("hook_edit_during_commit.py", "PreToolUse") == [
        "Write|Edit|NotebookEdit"
    ]
    assert registered_matchers("hook_edit_during_commit.py", "PostToolUse") == []
