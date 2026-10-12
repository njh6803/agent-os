"""워크트리 폴더의 모듈을 올린 프로세스를 도구의 `scan_modules` 가 대는지 잰다(대기열 201).

`tools/tidy_checkouts.py remove` 가 `spec-pipeline-and-pytest-ids` 의 `.venv` 안 `.pyd` 하나를
지우다 `WinError 5` 로 다섯 번 멈췄다. uv 는 `.venv` 를 캐시에서 하드링크로 채워, 어느 체크아웃의
파이썬이 확장 모듈을 올려도 같은 파일에 걸린 다른 워크트리의 이름까지 지울 수
없다(`worktree_occupancy.py` 의 E·F). 그래서 도구는 프로세스마다 적재한 모듈의 경로와 그 파일의 다른
하드링크 이름을 펼쳐 폴더 아래에 든 것을 찾는다.

갈래(임시 폴더만 만진다):
- A 아무도 올리지 않는다. 폴더 안 `.pyd` 의 지우기가 지나야 측정이다.
- G 자식이 폴더 안 `.pyd` 를 그 이름으로 올린다. 지우기가 `WinError 5` 로 막혀야 측정이다.
- E 자식이 폴더 밖 이름으로 같은 파일(하드링크)을 올린다. 지우기가 `WinError 5` 로 막혀야 측정이다.
갈래마다 지우기의 결과, `scan_modules` 가 댄 pid 에 자식의 pid 가 드는지, Restart Manager 가
그 파일에 댄 pid 를 찍는다. 측정이 아닌 갈래가 하나라도 있으면 종료 코드가 1이다.

`--folder <경로>` 는 실제 폴더를 읽기만 한다(이름을 바꾸거나 지우지 않는다). 그 아래 모듈 파일
(`.pyd`·`.dll`·`.exe`·`.node`) 전부를 Restart Manager 에 한 번에 등록하고, 그 앞뒤로 `scan_modules`
를 한 번씩 불러 두 쪽이 댄 pid 의 집합을 견준다. 짧게 도는 파이썬(pre-commit, pytest)이 그 사이에
끝나므로 파일마다 차례로 등록하면 답이 어긋난다(첫 판에서 파일 123개에 23초였다). 이어 뒤의 훑기로
모듈 파일마다 하드링크 수와 댄 pid 를 찍고, `scan_modules` 한 번의 시간과 항목 수를 찍는다.

윈도 전용이다. 돌리는 법(저장소 루트에서), 인자는 없거나 `--folder <경로>`:
`PYTHONUTF8=1 uv run python .scratch/harness/probes/module_holder.py [인자]`
"""

import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lock_holder import ERROR_MORE_DATA, a_dll, rm_holders  # noqa: E402
from tools.tidy_checkouts import holders_in, same_path, scan_modules  # noqa: E402

MODULE_EXTS = {".pyd", ".dll", ".exe", ".node"}


def load(target: Path, cwd: Path) -> tuple[subprocess.Popen[str], int]:
    """`target` 을 올린 자식을 띄운다. uv 의 venv 파이썬은 실행기라 실제 파이썬의 pid 를 받는다."""
    script = (
        f"import ctypes, os, sys\nlib = ctypes.WinDLL({str(target)!r})\n"
        "print(os.getpid(), flush=True)\nsys.stdin.read()\n"
    )
    child = subprocess.Popen(
        [sys.executable, "-c", script],
        cwd=cwd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    )
    assert child.stdout is not None
    line = child.stdout.readline().strip()
    if not line.isdigit():
        raise SystemExit(f"자식이 준비되지 않았다: {line!r}")
    return child, int(line)


def release(child: subprocess.Popen[str] | None) -> None:
    if child is None:
        return
    assert child.stdin is not None
    child.stdin.close()
    child.wait(timeout=10)


def try_unlink(path: Path) -> str:
    try:
        os.unlink(path)
    except OSError as error:
        return f"막힘({error.winerror})"
    return "지남"


def case(base: Path, outside: Path, name: str) -> bool:
    """갈래 하나. 측정이면(지우기의 결과가 갈래의 기대와 같으면) True."""
    folder = base / f"wt-{name}"
    folder.mkdir()
    target = folder / "mod.pyd"
    child: subprocess.Popen[str] | None = None
    pid: int | None = None
    if name == "E":
        source = outside / "linked-E.pyd"
        shutil.copyfile(a_dll(), source)
        os.link(source, target)
        child, pid = load(source, outside)
    else:
        shutil.copyfile(a_dll(), target)
        if name == "G":
            child, pid = load(target, outside)
    try:
        started = time.perf_counter()
        modules = scan_modules()
        took = time.perf_counter() - started
        found = holders_in(modules, str(folder), "module")
        pids = None if found is None else sorted({holder.pid for holder in found})
        rm = rm_holders([str(target)])
        unlinked = try_unlink(target)
    finally:
        release(child)
    expected = "지남" if name == "A" else "막힘(5)"
    measured = unlinked == expected
    caught = "볼 수 없음" if pids is None else ("자식을 댔다" if pid in pids else "자식이 없다")
    if name == "A":
        caught = "볼 수 없음" if pids is None else ("빈 목록" if not pids else f"댔다 {pids}")
    print(
        f"{name}: 자식 pid={pid} 지우기={unlinked} 측정={'예' if measured else '아니오'}"
        f" scan_modules={pids} ({caught}, {took:.2f}s) RM={rm}"
    )
    return measured


def module_files(folder: Path) -> list[Path]:
    return [
        Path(top) / name
        for top, _, names in os.walk(folder)
        for name in names
        if os.path.splitext(name)[1].lower() in MODULE_EXTS
    ]


def scanned_pids(folder: Path) -> tuple[set[int], list[tuple[int, str, str]], float]:
    started = time.perf_counter()
    modules = scan_modules()
    took = time.perf_counter() - started
    if modules is None:
        raise SystemExit("scan_modules 가 볼 수 없다고 돌려주었다")
    found = holders_in(modules, str(folder), "module")
    return {holder.pid for holder in found or []}, modules, took


def read_folder(folder: Path) -> None:
    """실제 폴더를 읽기만 한다."""
    files = module_files(folder)
    before, _, _ = scanned_pids(folder)
    started = time.perf_counter()
    # 234(ERROR_MORE_DATA)는 두 번의 RmGetList 사이에 프로세스가 늘었다는 뜻이라 다시 부른다
    for _ in range(3):
        code, by_rm = rm_holders([str(path) for path in files])
        if code != ERROR_MORE_DATA:
            break
    rm_took = time.perf_counter() - started
    after, modules, took = scanned_pids(folder)
    rm_pids = {pid for pid, _ in by_rm}
    count = len({pid for pid, _, _ in modules})
    print(f"scan_modules: {took:.2f}s, 프로세스 {count}개, 항목 {len(modules)}개")
    print(f"모듈 파일 {len(files)}개, RM 등록 {rm_took:.2f}s 오류={code} RM={sorted(by_rm)}")
    print(f"scan 앞={sorted(before)} 뒤={sorted(after)}")
    print(
        f"RM 에만={sorted(rm_pids - before - after)} scan 에만={sorted((before & after) - rm_pids)}"
    )
    images = {pid: image for pid, image, _ in modules}
    for path in files:
        held = sorted({pid for pid, _, name in modules if same_path(name, str(path))})
        if held:
            names = [images.get(pid, "") for pid in held]
            print(f"  {path.relative_to(folder)} nlink={os.stat(path).st_nlink} {held} {names}")


def main() -> int:
    if sys.platform != "win32":
        raise SystemExit("윈도 전용 프로브다")
    if len(sys.argv) == 3 and sys.argv[1] == "--folder":
        read_folder(Path(sys.argv[2]))
        return 0
    base = Path(tempfile.mkdtemp(prefix="module-holder-"))
    outside = base / "outside"
    outside.mkdir()
    try:
        print(f"python={sys.version.split()[0]} 이 프로세스 pid={os.getpid()}")
        measured = [case(base, outside, name) for name in ("A", "G", "E")]
    finally:
        time.sleep(0.5)
        shutil.rmtree(base, ignore_errors=True)
    if not all(measured):
        print("측정이 아닌 갈래가 있다")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
