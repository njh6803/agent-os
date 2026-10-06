"""윈도에서 무시된 깊은 경로가 든 워크트리를 `git worktree remove` 가 지우는지 잰다.

`tidy-checkouts` 스킬 3의 판정 4가 근거로 든다. `node_modules` 를 흉내 낸 무시된 경로(전체
470자 남짓)를 워크트리 둘에 만들고, 하나는 그냥 `git worktree remove`, 다른 하나는
`git -c core.longpaths=true worktree remove` 로 지운다. 각각 종료 코드, 폴더가 남았는지,
`git worktree list` 에 등록이 남았는지를 찍는다.

임시 디렉터리에 저장소를 만들고 끝에 지운다. 이 저장소는 건드리지 않는다. 돌리는 법:
`PYTHONUTF8=1 uv run python .scratch/harness/probes/worktree_longpath.py`
"""

import shutil
import subprocess
import tempfile
from pathlib import Path


def git(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True, check=False)


def long_path(path: Path) -> Path:
    """MAX_PATH 를 넘는 경로를 파이썬이 다루도록 `\\\\?\\` 접두사를 붙인다."""
    return Path("\\\\?\\" + str(path))


def make_worktree(repo: Path, name: str) -> Path:
    worktree = repo.parent / name
    added = git("worktree", "add", "-b", name, str(worktree), cwd=repo)
    print(f"{name}: add exit={added.returncode}")
    deep = worktree / "node_modules" / ".pnpm"
    for index in range(12):
        deep = deep / f"segment-{index:02d}-padding-padding"
    long_path(deep).mkdir(parents=True)
    (long_path(deep) / "file.txt").write_text("x", encoding="utf-8")
    print(f"{name}: 깊은 경로 길이={len(str(deep / 'file.txt'))}")
    return worktree


def remove(repo: Path, worktree: Path, *config: str) -> None:
    result = git(*config, "worktree", "remove", str(worktree), cwd=repo)
    registered = str(worktree).replace("\\", "/") in git("worktree", "list", cwd=repo).stdout
    print(
        f"{worktree.name}: remove exit={result.returncode}"
        f" 폴더 남음={long_path(worktree).exists()} 등록 남음={registered}"
        f" stderr={result.stderr.strip()[:160]}"
    )


def main() -> None:
    base = Path(tempfile.mkdtemp(prefix="wt-longpath-"))
    repo = base / "repo"
    repo.mkdir()
    try:
        git("init", "-b", "main", cwd=repo)
        (repo / ".gitignore").write_text("node_modules/\n", encoding="utf-8")
        git("add", ".", cwd=repo)
        identity = ("-c", "user.name=probe", "-c", "user.email=probe@example.com")
        git(*identity, "commit", "-m", "init", cwd=repo)
        longpaths = git("config", "core.longpaths", cwd=repo).stdout.strip()
        print(git("--version", cwd=repo).stdout.strip(), f"core.longpaths={longpaths}")
        remove(repo, make_worktree(repo, "wt-plain"))
        remove(repo, make_worktree(repo, "wt-longpaths"), "-c", "core.longpaths=true")
    finally:
        shutil.rmtree(long_path(base), ignore_errors=True)


if __name__ == "__main__":
    main()
