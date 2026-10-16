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
    context_for,
    edited_file,
    git_subcommand,
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


def test_고친_파일의_체크아웃에서_도는_커밋이면_알린다(tmp_path: Path) -> None:
    main, _ = _checkouts(tmp_path)
    checkout = checkout_of(str(main))
    assert checkout is not None
    file = main / "tools" / "x.py"
    file.write_text("x = 1\n", encoding="utf-8")

    context = context_for(str(file), [RunningCommit(4321, checkout)])

    assert context is not None
    assert "git commit" in context
    assert "4321" in context
    assert "대기열 293" in context
    assert "이미 적용" in context
    assert "다시 읽" in context


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

    assert context_for(str(file), [RunningCommit(1, checkout)]) is None


def test_도는_커밋이_없거나_체크아웃_밖의_파일이면_알리지_않는다(tmp_path: Path) -> None:
    main, _ = _checkouts(tmp_path)
    checkout = checkout_of(str(main))
    assert checkout is not None
    inside = main / "tools" / "x.py"
    inside.write_text("x = 1\n", encoding="utf-8")
    outside = tmp_path / "scratch.md"
    outside.write_text("메모\n", encoding="utf-8")

    assert context_for(str(inside), []) is None
    assert context_for(str(outside), [RunningCommit(1, checkout)]) is None


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
    assert context_for(str(file), [RunningCommit(1, str(work))]) is None


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
    tmp_path: Path, where: str, prefix: tuple[str, ...], launcher: bool
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


def test_훅은_도는_커밋의_워크트리_편집에만_계기를_낸다(tmp_path: Path) -> None:
    """stdin 의 바이트 페이로드부터 출력까지. 주 체크아웃의 편집은 그 폴더 아래 워크트리에서 커밋이
    돌아도 침묵한다."""
    with committing_repository(tmp_path) as root:
        side_file = root / ".claude" / "worktrees" / "side" / "tracked.txt"
        main_file = root / "notes.md"
        main_file.write_text("메모\n", encoding="utf-8")

        firing = _run_hook(
            {
                "hook_event_name": "PostToolUse",
                "tool_name": "Edit",
                "tool_input": {"file_path": str(side_file), "old_string": "x", "new_string": "y"},
            }
        )
        quiet = _run_hook(
            {
                "hook_event_name": "PostToolUse",
                "tool_name": "Write",
                "tool_input": {"file_path": str(main_file), "content": "메모\n"},
            }
        )

    output = json.loads(firing)["hookSpecificOutput"]
    assert output["hookEventName"] == "PostToolUse"
    assert "git commit" in output["additionalContext"]
    assert quiet == ""


def test_settings의_매처는_편집_도구_셋이다() -> None:
    """알림은 편집이 끝난 뒤에 온다(PostToolUse). 그 편집 하나는 이미 겹쳤다."""
    assert registered_matchers("hook_edit_during_commit.py", "PostToolUse") == [
        "Write|Edit|NotebookEdit"
    ]
