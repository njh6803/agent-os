"""pre-commit 의 always_run 검사 일곱을 띄우는 모양별로 각자의 시간과 벽시계 시간을 잰다.

저장소 루트에서 `uv run python .scratch/harness/probes/precommit_parallel.py <serial|groups|all>`.
  serial — 일곱을 차례로 돈다(pre-commit 이 훅을 도는 모양)
  groups — 파이썬 묶음(그 안은 차례로)과 web verify 를 나란히 띄운다
  all    — 일곱을 한꺼번에 띄운다
명령은 잴 때(`cbb6a6c`)의 `.pre-commit-config.yaml` entry 를 손으로 옮긴 것이고, 지금은
`tools/run_checks.py` 의 `CHECKS` 와 같다. ruff 둘은 파일을 고쳐서 넣지 않았다. `uv sync` 와
`pnpm -C web install --frozen-lockfile` 이 된 체크아웃이어야 한다.
"""

import subprocess
import sys
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]

COMMANDS: dict[str, list[str]] = {
    "pyright": ["uv", "run", "pyright"],
    "lint-imports": ["uv", "run", "lint-imports"],
    "pytest": ["uv", "run", "pytest", "-q"],
    "check-instructions": ["uv", "run", "python", "tools/check_instructions.py"],
    "check-type-escapes": ["uv", "run", "python", "tools/check_type_escapes.py"],
    "run-hooks": ["uv", "run", "python", "tools/run_hooks.py"],
    "web-verify": ["pnpm", "-C", "web", "verify"],
}

Results = dict[str, tuple[int, float]]


def run(name: str, results: Results) -> None:
    start = time.monotonic()
    proc = subprocess.run(COMMANDS[name], cwd=ROOT, capture_output=True, check=False)
    results[name] = (proc.returncode, time.monotonic() - start)


def run_serial(names: list[str], results: Results) -> None:
    for name in names:
        run(name, results)


def threads_for(mode: str, results: Results) -> list[threading.Thread]:
    names = list(COMMANDS)
    if mode == "serial":
        return [threading.Thread(target=run_serial, args=(names, results))]
    if mode == "groups":
        python = [n for n in names if n != "web-verify"]
        return [
            threading.Thread(target=run_serial, args=(python, results)),
            threading.Thread(target=run, args=("web-verify", results)),
        ]
    if mode == "all":
        return [threading.Thread(target=run, args=(n, results)) for n in names]
    raise SystemExit(f"모드는 serial, groups, all 중 하나다: {mode!r}")


def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    results: Results = {}
    threads = threads_for(mode, results)
    start = time.monotonic()
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    wall = time.monotonic() - start
    for name, (rc, sec) in results.items():
        print(f"{name:20} rc={rc} {sec:6.1f}s")
    print(f"{'wall':20}      {wall:6.1f}s")


if __name__ == "__main__":
    main()
