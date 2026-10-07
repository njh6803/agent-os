"""윈도에서 남이 쥔 워크트리를 무엇이 미리 알아보는지와 `git worktree remove` 의 끝을 잰다.

대기열 132 의 "지우기 전에 이름 바꾸기로 점유를 보는 탐침을 둔다"를 들이기 전에 쟀다.
`tools/tidy_checkouts.py` 독스트링의 판정 4가 근거로 든다. 갈래마다 임시 저장소에 워크트리를
하나씩 만들고, 무시된 폴더 `zz/deep/` 에 파일을 둔다.

- A 아무도 쥐지 않는다.
- B 자식 프로세스가 `zz/deep/` 을 작업 디렉터리로 쥔다.
- C 자식 프로세스가 워크트리 안의 파일을 연다(파이썬 `open`).
- D 자식 프로세스가 워크트리 밖의 하드링크 이름으로 같은 파일을 연다. uv 의 `.venv` 와 pnpm 의
  `node_modules` 는 캐시에서 하드링크로 채워진다.
- E 자식 프로세스가 워크트리 밖의 하드링크 이름으로 같은 DLL(이 파이썬의 `.pyd` 하나를 복사한
  것)을 적재한다.
- F 점유는 E 와 같고, `git worktree remove` 전에 무시된 폴더를 `shutil.rmtree` 로 먼저 지운다.
  지우지 못하면 git 을 부르지 않는다.

갈래마다 워크트리 폴더를 옆 이름으로 바꿨다가 되돌린 결과, 그 뒤 `git -c core.longpaths=true
worktree remove` 의 종료 코드와 stderr, 폴더·`.git` 파일·등록이 남았는지를 찍는다. F 는 rmtree 가
막혔는지와 그때 `.git` 파일과 등록이 남았는지를 찍는다. 끝에 자식 프로세스를 끝내고 임시 디렉터리를
지운다. 이 저장소는 건드리지 않는다.

윈도 전용이다. 돌리는 법: `PYTHONUTF8=1 uv run python .scratch/harness/probes/worktree_occupancy.py`
"""

import glob
import os
import shutil
import subprocess
import sys
import sysconfig
import tempfile
import time
from pathlib import Path

GIT = ("git", "-c", "core.longpaths=true")
IDENTITY = ("-c", "user.name=probe", "-c", "user.email=probe@example.com")


def git(*args: str, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run([*GIT, *args], cwd=cwd, capture_output=True, text=True, check=False)


def registered(repo: Path, worktree: Path) -> bool:
    listed = git("worktree", "list", "--porcelain", cwd=repo).stdout.splitlines()
    paths = {
        line.removeprefix("worktree ").casefold() for line in listed if line.startswith("worktree ")
    }
    return worktree.as_posix().casefold() in paths


def hold(code: str, cwd: Path) -> subprocess.Popen[str]:
    """`code` 를 돌린 뒤 stdin 이 닫힐 때까지 기다리는 자식 파이썬. 준비되면 `ready` 를 찍는다."""
    script = f"{code}\nimport sys\nprint('ready', flush=True)\nsys.stdin.read()\n"
    child = subprocess.Popen(
        [sys.executable, "-c", script],
        cwd=cwd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    )
    assert child.stdout is not None
    line = child.stdout.readline().strip()
    if line != "ready":
        raise SystemExit(f"자식이 준비되지 않았다: {line!r}")
    return child


def release(child: subprocess.Popen[str] | None) -> None:
    if child is None:
        return
    assert child.stdin is not None
    child.stdin.close()
    child.wait(timeout=10)


def rename_probe(worktree: Path) -> str:
    aside = worktree.with_name(worktree.name + ".probe")
    try:
        os.rename(worktree, aside)
    except OSError as error:
        return f"막힘({error.winerror} {error.strerror})"
    os.rename(aside, worktree)
    return "지남"


def a_dll() -> Path:
    """이 파이썬의 `.pyd` 하나. DLL 이라 `ctypes.WinDLL` 로 적재된다."""
    found = sorted(glob.glob(os.path.join(sysconfig.get_paths()["platlib"], "*.pyd")))
    found += sorted(glob.glob(os.path.join(sys.base_prefix, "DLLs", "*.pyd")))
    if not found:
        raise SystemExit("적재할 .pyd 를 찾지 못했다")
    return Path(found[0])


def occupy(name: str, sub: Path, outside: Path) -> subprocess.Popen[str] | None:
    inner = sub / "data.txt"
    if name in ("A", "B", "C"):
        inner.write_text("x", encoding="utf-8")
    if name == "B":
        return hold("pass", cwd=sub)
    if name == "C":
        return hold(f"f = open({str(inner)!r}, encoding='utf-8')", cwd=outside)
    if name == "D":
        source = outside / "linked.txt"
        source.write_text("x", encoding="utf-8")
        os.link(source, inner)
        return hold(f"f = open({str(source)!r}, encoding='utf-8')", cwd=outside)
    if name in ("E", "F"):
        source = outside / f"linked-{name}.pyd"
        shutil.copyfile(a_dll(), source)
        os.link(source, sub / "linked.pyd")
        return hold(f"import ctypes\nlib = ctypes.WinDLL({str(source)!r})", cwd=outside)
    return None


def case(repo: Path, outside: Path, name: str) -> None:
    worktree = repo.parent / f"wt-{name}"
    added = git("worktree", "add", "-b", f"wt-{name}", str(worktree), cwd=repo)
    if added.returncode != 0:
        raise SystemExit(f"{name}: worktree add 실패 {added.stderr.strip()}")
    sub = worktree / "zz" / "deep"
    sub.mkdir(parents=True)
    child = occupy(name, sub, outside)
    try:
        before = registered(repo, worktree)
        probe = rename_probe(worktree)
        if name == "F":
            try:
                shutil.rmtree(worktree / "zz")
            except OSError as error:
                print(
                    f"{name}: 이름 바꾸기={probe} rmtree 막힘({error.winerror} {error.strerror})"
                    f" .git 남음={(worktree / '.git').exists()}"
                    f" 등록 남음={registered(repo, worktree)}"
                )
                return
        removed = git("worktree", "remove", str(worktree), cwd=repo)
        print(
            f"{name}: 이름 바꾸기={probe} remove exit={removed.returncode} 지우기 전 등록={before}"
            f" 폴더 남음={worktree.exists()} .git 남음={(worktree / '.git').exists()}"
            f" 등록 남음={registered(repo, worktree)} stderr={removed.stderr.strip()[:160]}"
        )
    finally:
        release(child)


def main() -> None:
    if sys.platform != "win32":
        raise SystemExit("윈도 전용 프로브다. 열린 파일이 지우기를 막는 것은 윈도다")
    base = Path(tempfile.mkdtemp(prefix="wt-occupancy-"))
    repo = base / "repo"
    outside = base / "outside"
    repo.mkdir()
    outside.mkdir()
    try:
        git("init", "-b", "main", cwd=repo)
        (repo / "README.md").write_text("probe\n", encoding="utf-8")
        # 실제 워크트리의 `.venv`·`node_modules` 처럼 무시된 폴더여야 remove 가 거부하지 않는다
        (repo / ".gitignore").write_text("zz/\n", encoding="utf-8")
        git("add", ".", cwd=repo)
        git(*IDENTITY, "commit", "-m", "init", cwd=repo)
        print(git("--version", cwd=repo).stdout.strip(), f"python={sys.version.split()[0]}")
        for name in ("A", "B", "C", "D", "E", "F"):
            case(repo, outside, name)
    finally:
        time.sleep(0.5)
        shutil.rmtree(base, ignore_errors=True)


if __name__ == "__main__":
    main()
