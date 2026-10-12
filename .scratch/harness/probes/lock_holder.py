"""워크트리를 쥔 프로세스를 무엇이 대는지 잰다. Restart Manager 와 작업 디렉터리 훑기를 견준다.

대기열 177 은 "Restart Manager 로 쥔 프로세스의 이름과 pid 를 남긴 이유에 붙인다"였다. 들이기
전에 쟀고, 그 결과로 `tools/tidy_checkouts.py` 의 `cwd_holders`(작업 디렉터리 훑기)를 골랐다.
그 독스트링의 판정 4가 근거로 든다.

갈래 A~E 는 `worktree_occupancy.py` 와 같고, F(앞지우기)는 빼고 G·H 를 더했다. 임시 폴더
`wt-<갈래>/zz/deep/` 에 파일을 둔다.
- A 아무도 쥐지 않는다.
- B 자식 프로세스가 `zz/deep/` 을 작업 디렉터리로 쥔다.
- C 자식 프로세스가 폴더 안의 파일을 연다.
- D 자식 프로세스가 폴더 밖의 하드링크 이름으로 같은 파일을 연다.
- E 자식 프로세스가 폴더 밖의 하드링크 이름으로 같은 DLL 을 적재한다.
- G 자식 프로세스가 폴더 안의 `.pyd` 를 그 이름 그대로 적재한다(`.venv` 의 확장 모듈).
- H 자식 프로세스가 폴더 자신을 작업 디렉터리로 쥔다(2026-10-12 에 남은 워크트리의 모양).

갈래마다 찍는 것: 이름 바꾸기 탐침, 폴더를 DELETE 권한으로 열기(공유 위반이면 32), Restart
Manager 에 폴더 경로 하나·폴더 아래 파일 전부를 등록한 결과, 도구의 `cwd_holders` 가 댄 pid.
자식 pid 는 uv 의 venv 파이썬이면 실행기이고, 실제 파이썬은 그 자식이다. 끝에 파일 1000개와
20000개를 Restart Manager 에 한 번에 등록하는 시간을 잰다. 이 저장소는 건드리지 않는다.

`--folder <경로> ...` 는 실제 폴더들을 읽기만 한다(이름을 바꾸지 않는다). 먼저 프로세스 수와 그중
작업 디렉터리를 읽은 수를, 이어 폴더마다 DELETE 권한으로 열기와 `cwd_holders` 를 찍는다. `--rm
<경로>` 는 그 아래 파일 전부를 5000개씩 덩이로 Restart Manager 에 등록한다(역시 읽기만 한다).

윈도 전용이다. 돌리는 법(저장소 루트에서), 인자는 없거나 `--folder <경로> ...` 나 `--rm <경로>`:
`PYTHONUTF8=1 uv run python .scratch/harness/probes/lock_holder.py [인자]`
"""

import ctypes
import glob
import os
import shutil
import subprocess
import sys
import sysconfig
import tempfile
import time
from ctypes import wintypes
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from tools.tidy_checkouts import (  # noqa: E402
    _process_cwds,
    _windows_api,
    _windows_pids,
    cwd_holders,
)

CCH_RM_SESSION_KEY = 32
CCH_RM_MAX_APP_NAME = 255
CCH_RM_MAX_SVC_NAME = 63
ERROR_MORE_DATA = 234
CHUNK = 5000
DELETE = 0x00010000
SHARE_ALL = 0x7
OPEN_EXISTING = 3
BACKUP_SEMANTICS = 0x02000000


class RmUniqueProcess(ctypes.Structure):
    _fields_ = [("dwProcessId", wintypes.DWORD), ("ProcessStartTime", wintypes.FILETIME)]


class RmProcessInfo(ctypes.Structure):
    _fields_ = [
        ("Process", RmUniqueProcess),
        ("strAppName", wintypes.WCHAR * (CCH_RM_MAX_APP_NAME + 1)),
        ("strServiceShortName", wintypes.WCHAR * (CCH_RM_MAX_SVC_NAME + 1)),
        ("ApplicationType", ctypes.c_int),
        ("AppStatus", wintypes.ULONG),
        ("TSSessionId", wintypes.DWORD),
        ("bRestartable", wintypes.BOOL),
    ]


def rm_holders(paths: list[str]) -> tuple[int, list[tuple[int, str]]]:
    """(오류 코드, [(pid, 앱 이름)]). 오류 코드 0 이 성공이다."""
    rm = ctypes.WinDLL("rstrtmgr")
    session = wintypes.DWORD()
    key = ctypes.create_unicode_buffer(CCH_RM_SESSION_KEY + 1)
    code = rm.RmStartSession(ctypes.byref(session), 0, key)
    if code:
        return code, []
    try:
        array = (wintypes.LPCWSTR * len(paths))(*paths)
        code = rm.RmRegisterResources(session, len(paths), array, 0, None, 0, None)
        if code:
            return code, []
        needed = wintypes.UINT()
        count = wintypes.UINT(0)
        reasons = wintypes.DWORD()
        code = rm.RmGetList(
            session, ctypes.byref(needed), ctypes.byref(count), None, ctypes.byref(reasons)
        )
        if code == 0:
            return 0, []
        if code != ERROR_MORE_DATA:
            return code, []
        infos = (RmProcessInfo * needed.value)()
        count = wintypes.UINT(needed.value)
        code = rm.RmGetList(
            session, ctypes.byref(needed), ctypes.byref(count), infos, ctypes.byref(reasons)
        )
        if code:
            return code, []
        return 0, [(infos[i].Process.dwProcessId, infos[i].strAppName) for i in range(count.value)]
    finally:
        rm.RmEndSession(session)


def open_for_delete(folder: Path) -> str:
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.CreateFileW.restype = wintypes.HANDLE
    kernel.CreateFileW.argtypes = [
        wintypes.LPCWSTR,
        wintypes.DWORD,
        wintypes.DWORD,
        ctypes.c_void_p,
        wintypes.DWORD,
        wintypes.DWORD,
        wintypes.HANDLE,
    ]
    handle = kernel.CreateFileW(
        str(folder), DELETE, SHARE_ALL, None, OPEN_EXISTING, BACKUP_SEMANTICS, None
    )
    if handle in (None, ctypes.c_void_p(-1).value):
        return f"막힘({ctypes.get_last_error()})"
    kernel.CloseHandle(handle)
    return "열림"


def hold(code: str, cwd: Path) -> subprocess.Popen[str]:
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


def a_dll() -> Path:
    found = sorted(glob.glob(os.path.join(sysconfig.get_paths()["platlib"], "*.pyd")))
    found += sorted(glob.glob(os.path.join(sys.base_prefix, "DLLs", "*.pyd")))
    if not found:
        raise SystemExit("적재할 .pyd 를 찾지 못했다")
    return Path(found[0])


def rename_probe(folder: Path) -> str:
    aside = folder.with_name(folder.name + ".probe")
    try:
        os.rename(folder, aside)
    except OSError as error:
        return f"막힘({error.winerror})"
    os.rename(aside, folder)
    return "지남"


def occupy(name: str, folder: Path, sub: Path, outside: Path) -> subprocess.Popen[str] | None:
    inner = sub / "data.txt"
    inner.write_text("x", encoding="utf-8")
    if name == "B":
        return hold("pass", cwd=sub)
    if name == "H":
        return hold("pass", cwd=folder)
    if name == "C":
        return hold(f"f = open({str(inner)!r}, encoding='utf-8')", cwd=outside)
    if name == "D":
        source = outside / "linked.txt"
        source.write_text("x", encoding="utf-8")
        os.link(source, sub / "linked.txt")
        return hold(f"f = open({str(source)!r}, encoding='utf-8')", cwd=outside)
    if name == "E":
        source = outside / "linked-E.pyd"
        shutil.copyfile(a_dll(), source)
        os.link(source, sub / "linked.pyd")
        return hold(f"import ctypes\nlib = ctypes.WinDLL({str(source)!r})", cwd=outside)
    if name == "G":
        target = sub / "own.pyd"
        shutil.copyfile(a_dll(), target)
        return hold(f"import ctypes\nlib = ctypes.WinDLL({str(target)!r})", cwd=outside)
    return None


def files_under(folder: Path) -> list[str]:
    return [str(Path(top) / name) for top, _, names in os.walk(folder) for name in names]


def cwd_pids(folder: Path) -> str:
    found = cwd_holders(folder)
    if found is None:
        return "볼 수 없음"
    return str(sorted(holder.pid for holder in found))


def case(base: Path, outside: Path, name: str) -> None:
    folder = base / f"wt-{name}"
    sub = folder / "zz" / "deep"
    sub.mkdir(parents=True)
    child = occupy(name, folder, sub, outside)
    pid = child.pid if child else None
    try:
        probe = rename_probe(folder)
        opened = open_for_delete(folder)
        by_dir = rm_holders([str(folder)])
        by_files = rm_holders(files_under(folder))
        print(
            f"{name}: 자식 pid={pid} 이름 바꾸기={probe} DELETE 열기={opened}"
            f" RM 폴더={by_dir} RM 파일 전부={by_files} cwd_holders={cwd_pids(folder)}"
        )
    finally:
        release(child)


def timing(base: Path, count: int) -> None:
    folder = base / f"many-{count}"
    for index in range(count):
        part = folder / f"d{index // 500}"
        part.mkdir(parents=True, exist_ok=True)
        (part / f"f{index}.js").write_text("x", encoding="utf-8")
    started = time.perf_counter()
    paths = files_under(folder)
    walked = time.perf_counter()
    result = rm_holders(paths)
    done = time.perf_counter()
    print(
        f"RM 파일 {count}개: 훑기 {walked - started:.3f}s,"
        f" 등록과 목록 {done - walked:.3f}s, 결과={result}"
    )


def read_folders(folders: list[Path]) -> None:
    """실제 폴더들을 읽기만 한다. 이름을 바꾸거나 지우지 않는다."""
    started = time.perf_counter()
    processes = _process_cwds()
    listed = len(_windows_pids(_windows_api()[0]))
    readable = "볼 수 없음" if processes is None else str(len(processes))
    print(
        f"프로세스 {listed}개 중 작업 디렉터리를 읽은 것 {readable}개"
        f" ({time.perf_counter() - started:.3f}s)"
    )
    for folder in folders:
        started = time.perf_counter()
        found = cwd_holders(folder)
        print(
            f"{folder}: DELETE 열기={open_for_delete(folder)}"
            f" cwd_holders={found} ({time.perf_counter() - started:.3f}s)"
        )


def register_folder_files(folder: Path) -> None:
    """실제 폴더 아래 파일 전부를 Restart Manager 에 덩이로 등록한다. 읽기만 한다."""
    started = time.perf_counter()
    paths = files_under(folder)
    walked = time.perf_counter()
    codes: list[int] = []
    holders: dict[int, str] = {}
    # 한 세션에 4만여 개를 등록하면 오류 29(레지스트리 쓰기)였다. 덩이로 나눠 세션마다 등록한다
    for start in range(0, len(paths), CHUNK):
        code, chunk = rm_holders(paths[start : start + CHUNK])
        codes.append(code)
        holders.update(dict(chunk))
    done = time.perf_counter()
    print(
        f"  RM: 파일 {len(paths)}개, 훑기 {walked - started:.3f}s,"
        f" 등록과 목록 {done - walked:.3f}s, 덩이 {len(codes)}개, 오류={sorted(set(codes))},"
        f" 댄 것={holders}"
    )


def main() -> None:
    if sys.platform != "win32":
        raise SystemExit("윈도 전용 프로브다")
    if len(sys.argv) >= 3 and sys.argv[1] == "--folder":
        read_folders([Path(arg) for arg in sys.argv[2:]])
        return
    if len(sys.argv) == 3 and sys.argv[1] == "--rm":
        register_folder_files(Path(sys.argv[2]))
        return
    base = Path(tempfile.mkdtemp(prefix="lock-holder-"))
    outside = base / "outside"
    outside.mkdir()
    try:
        print(f"python={sys.version.split()[0]} 이 프로세스 pid={os.getpid()}")
        for name in ("A", "B", "C", "D", "E", "G", "H"):
            case(base, outside, name)
        for count in (1000, 20000):
            timing(base, count)
    finally:
        time.sleep(0.5)
        shutil.rmtree(base, ignore_errors=True)


if __name__ == "__main__":
    main()
