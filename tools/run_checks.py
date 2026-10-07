"""pre-commit 의 always_run 검사를 함께 띄우고 결과를 모은다(ADR 0005 이력 2026-10-07).

pre-commit 은 훅을 하나씩 돈다(4.6.2 `commands/run.py` 의 `_run_hooks`). 커밋마다 도는 검사 일곱을
차례로 돌면 145.5초, 한꺼번에 띄우면 가장 긴 pytest 만큼인 73.7초였다
(`.scratch/harness/probes/precommit_parallel.py`, Linux 컨테이너 CPU 4, 일지 2026-10-07-02). 그래서
`.pre-commit-config.yaml` 은 이 일곱을 훅 하나로 두고 이 러너가 함께 띄운다. 파일을 고치는 ruff 둘은
이 훅 앞에 따로 있어, 러너는 고친 뒤의 파일을 본다. 검사 목록의 원천은 여기 하나다. CI 는 잡마다
명령을 직접 돈다(`.github/workflows/ci.yml`).

통과한 검사는 한 줄을, 실패한 검사는 그 줄 뒤에 모은 출력(stdout 과 stderr)을 끝난 차례로 찍는다.
하나라도 실패하면 1로 끝난다. pre-commit 의 `SKIP` 을 같은 id 로 읽어, `SKIP=pytest git commit` 이
검사마다 훅이 따로 있던 때처럼 통한다. 명령은 `shutil.which` 로 찾는다. Windows 에서 `pnpm` 은
`pnpm.cmd` 라 경로 없이는 띄우지 못한다.

함께 돌 때 서로 보는 파일은 Vitest 판정자 테스트가 `web/judge-*` 에 쓰는 임시 트리 하나다. 지침
검사의 중첩 지침 파일 훑기가 그 트리를 지나도 찾는 이름이 없고, 도중에 사라진 디렉터리는
건너뛴다(코드를 읽었다, 일지 2026-10-07-02).

못 보는 것: 검사 하나가 멈추면 러너도 멈춘다(시간 제한이 없다. pre-commit 도 두지 않는다). CPU 가
적은 기계에서 함께 띄운 것이 차례로 돈 것보다 느린지는 재지 않았다. Windows 에서 `.cmd` 를 경로로
띄우는 길은 테스트가 도는 Linux 에서 재지 않았다.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from collections.abc import Mapping, Sequence
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

ROOT = Path(__file__).resolve().parents[1]
_NAME_WIDTH = 40


@dataclass(frozen=True)
class Check:
    """검사 하나. id 는 예전 훅 id 와 같아 `SKIP` 이 그대로 통한다."""

    id: str
    command: tuple[str, ...]


@dataclass(frozen=True)
class Outcome:
    check: Check
    passed: bool
    output: bytes
    seconds: float


CHECKS: tuple[Check, ...] = (
    Check("pyright", ("uv", "run", "pyright")),
    Check("lint-imports", ("uv", "run", "lint-imports")),
    Check("pytest", ("uv", "run", "pytest", "-q")),
    Check("check-instructions", ("uv", "run", "python", "tools/check_instructions.py")),
    Check("check-type-escapes", ("uv", "run", "python", "tools/check_type_escapes.py")),
    Check("run-hooks", ("uv", "run", "python", "tools/run_hooks.py")),
    Check("web-verify", ("pnpm", "-C", "web", "verify")),
)


def skipped_ids(environ: Mapping[str, str]) -> frozenset[str]:
    """pre-commit 의 `_get_skips` 와 같은 모양으로 읽는다. 쉼표로 나누고 공백을 걷는다."""
    return frozenset(part.strip() for part in environ.get("SKIP", "").split(",") if part.strip())


def run_one(check: Check, cwd: Path) -> Outcome:
    """검사 하나를 띄워 끝날 때까지 기다린다. 명령을 찾지 못하면 예외 대신 실패로 돌려준다."""
    start = time.monotonic()
    executable = shutil.which(check.command[0])
    if executable is None:
        message = f"명령을 찾지 못했다: {check.command[0]}\n".encode()
        return Outcome(check, False, message, time.monotonic() - start)
    process = subprocess.run(
        [executable, *check.command[1:]],
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    return Outcome(check, process.returncode == 0, process.stdout, time.monotonic() - start)


def status_line(check_id: str, status: str) -> bytes:
    return f"{check_id:.<{_NAME_WIDTH}}{status}\n".encode()


def run(checks: Sequence[Check], environ: Mapping[str, str], cwd: Path, out: BinaryIO) -> int:
    """SKIP 밖의 검사를 한꺼번에 띄우고 끝난 차례로 찍는다. 하나라도 실패하면 1."""
    skips = skipped_ids(environ)
    to_run = [check for check in checks if check.id not in skips]
    for check in checks:
        if check.id in skips:
            out.write(status_line(check.id, "Skipped"))
    failed = False
    if to_run:
        with ThreadPoolExecutor(max_workers=len(to_run)) as pool:
            futures = [pool.submit(run_one, check, cwd) for check in to_run]
            for future in as_completed(futures):
                outcome = future.result()
                status = "Passed" if outcome.passed else "Failed"
                out.write(status_line(outcome.check.id, f"{status} ({outcome.seconds:.1f}s)"))
                if not outcome.passed:
                    failed = True
                    out.write(outcome.output)
                    if not outcome.output.endswith(b"\n"):
                        out.write(b"\n")
                out.flush()
    out.flush()
    return 1 if failed else 0


def main() -> int:
    return run(CHECKS, os.environ, ROOT, sys.stdout.buffer)


if __name__ == "__main__":
    sys.exit(main())
