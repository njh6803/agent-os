"""하드링크 없는 `.venv`(uv 의 `--link-mode copy`)에서 판정 3의 모듈 막힘이 사라지는지와 그 값을
잰다(대기열 217).

`tools/tidy_checkouts.py judge` 가 병합된 워크트리 대부분을 "모듈을 올린 프로세스" 로 남겼다. 같은
pid 몇이 거의 모든 워크트리를 쥔 것으로 나왔다. uv 가 `.venv` 를 캐시에서 하드링크로 채워, 한
체크아웃의 파이썬이 올린 확장 모듈이 다른 워크트리의 같은 파일(하드링크 이름)로도 보이기
때문이라고 어림했다(일지 2026-10-12-38 의 링크 수 30~38).

갈래(임시 폴더만 만든다. 저장소의 `uv.lock` 대로 `uv sync --frozen` 을 세 번 친다):
- other: 하드링크(`--link-mode hardlink`)로 채운 `.venv`. "다른 체크아웃" 이다. 여기서 띄운 자식이
  확장 모듈을 import 하고 기다린다.
- hard: 하드링크로 채운 `.venv`. 지금의 워크트리다. other 의 자식이 이것을 쥔 것으로 보여야 한다.
- copy: `--link-mode copy` 로 채운 `.venv`. other 의 자식이 쥐지 않아야 한다.
그 뒤 copy 자신에서 자식을 하나 더 띄워, 하드링크가 없어도 자기 `.venv` 에서 올린 모듈은 여전히
잡히는지 본다(copy-self).

찍는 것: 갈래마다 `uv sync` 시간, 파일 수와 바이트, 링크 수가 1보다 큰 파일의 수와 바이트(이
몫은 캐시와 디스크를 나눠 쓴다), 확장 모듈 하나의 링크 수. 이어 `scan_modules` 한 번에서
`holders_in` 이 갈래마다 댄 pid, 확장 모듈을 지운 결과(hard 는 `WinError 5`, copy 는 지나야 측정).
측정이 아닌 것이 하나라도 있으면 종료 코드가 1이다.

윈도 전용이다. 돌리는 법(저장소 루트에서):
`PYTHONUTF8=1 uv run python .scratch/harness/probes/venv_link_mode.py`
"""

import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.tidy_checkouts import holders_in, scan_modules  # noqa: E402

# 자식이 올릴 확장 모듈. pydantic 은 런타임 의존이라 모든 `.venv` 에 있다
CHILD = (
    "import os, sys\nimport pydantic_core._pydantic_core as m\n"
    "print(os.getpid(), m.__file__, flush=True)\nsys.stdin.read()\n"
)


def sync(venv: Path, mode: str, *extra: str) -> float:
    env = {**os.environ, "UV_PROJECT_ENVIRONMENT": str(venv)}
    env.pop("VIRTUAL_ENV", None)
    started = time.perf_counter()
    subprocess.run(
        ["uv", "sync", "--frozen", "--link-mode", mode, "--quiet", *extra],
        cwd=ROOT,
        env=env,
        check=True,
        timeout=600,
    )
    return time.perf_counter() - started


def sizes(venv: Path) -> tuple[int, int, int, int]:
    """(파일 수, 바이트, 링크 수가 1보다 큰 파일 수, 그 바이트)."""
    count = total = linked = linked_bytes = 0
    for top, _, names in os.walk(venv):
        for name in names:
            stat = os.stat(Path(top) / name)
            count += 1
            total += stat.st_size
            if stat.st_nlink > 1:
                linked += 1
                linked_bytes += stat.st_size
    return count, total, linked, linked_bytes


def python_of(venv: Path) -> Path:
    return venv / "Scripts" / "python.exe"


def spawn(venv: Path) -> tuple[subprocess.Popen[str], int, Path]:
    """`venv` 의 파이썬으로 확장 모듈을 올린 자식. venv 파이썬은 실행기라 실제 pid 를 받는다."""
    child = subprocess.Popen(
        [str(python_of(venv)), "-c", CHILD],
        cwd=venv,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
    )
    assert child.stdout is not None
    pid, _, path = child.stdout.readline().strip().partition(" ")
    if not pid.isdigit():
        raise SystemExit(f"자식이 준비되지 않았다: {pid!r}")
    return child, int(pid), Path(path)


def release(child: subprocess.Popen[str]) -> None:
    assert child.stdin is not None
    child.stdin.close()
    child.wait(timeout=10)


def held_by(venv: Path) -> list[int] | None:
    found = holders_in(scan_modules(), str(venv), "module")
    return None if found is None else sorted({holder.pid for holder in found})


def try_unlink(path: Path) -> str:
    try:
        os.unlink(path)
    except OSError as error:
        return f"막힘({error.winerror})"
    return "지남"


def mib(size: int) -> str:
    return f"{size / 2**20:.1f}MiB"


def main() -> int:
    if sys.platform != "win32":
        raise SystemExit("윈도 전용 프로브다")
    base = Path(tempfile.mkdtemp(prefix="venv-link-mode-"))
    venvs = {"other": base / "other", "hard": base / "hard", "copy": base / "copy"}
    modes = {"other": "hardlink", "hard": "hardlink", "copy": "copy"}
    print(f"python={sys.version.split()[0]} 임시={base}")
    measured: list[bool] = []
    try:
        for name, venv in venvs.items():
            took = sync(venv, modes[name])
            count, total, linked, linked_bytes = sizes(venv)
            print(
                f"{name}({modes[name]}): uv sync {took:.1f}s, 파일 {count}개 {mib(total)},"
                f" 링크>1 {linked}개 {mib(linked_bytes)}"
            )
        child, pid, module = spawn(venvs["other"])
        try:
            relative = module.relative_to(venvs["other"])
            for name in ("hard", "copy"):
                print(f"  {relative} nlink {name}={os.stat(venvs[name] / relative).st_nlink}")
            started = time.perf_counter()
            pids = {name: held_by(venv) for name, venv in venvs.items()}
            print(f"other 의 자식 pid={pid}, holders_in 세 번 {time.perf_counter() - started:.2f}s")
            for name, found in pids.items():
                print(f"  {name}: {found}")
            measured.append(pids["other"] is not None and pid in pids["other"])
            measured.append(pids["hard"] is not None and pid in pids["hard"])
            measured.append(pids["copy"] == [])
            hard_rm = try_unlink(venvs["hard"] / relative)
            copy_rm = try_unlink(venvs["copy"] / relative)
            print(f"  지우기 hard={hard_rm} copy={copy_rm}")
            measured += [hard_rm == "막힘(5)", copy_rm == "지남"]
        finally:
            release(child)
        # copy 의 확장 모듈은 위에서 지웠다. uv 는 설치 기록만 보므로 그 패키지를 다시 깐다
        took = sync(venvs["copy"], "copy", "--reinstall-package", "pydantic-core")
        print(f"copy 에 pydantic-core 다시 깔기 {took:.1f}s")
        own, own_pid, _ = spawn(venvs["copy"])
        try:
            found = held_by(venvs["copy"])
            print(f"copy-self: 자식 pid={own_pid} holders_in={found}")
            measured.append(found is not None and own_pid in found)
        finally:
            release(own)
    finally:
        time.sleep(0.5)
        shutil.rmtree(base, ignore_errors=True)
    if not all(measured):
        print(f"측정이 아닌 것이 있다: {measured}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
