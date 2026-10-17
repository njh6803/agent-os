"""pre-commit 의 always_run 검사를 함께 띄우고 결과를 모은다(ADR 0005 이력 2026-10-07).

pre-commit 은 훅을 하나씩 돈다(4.6.2 `commands/run.py` 의 `_run_hooks`). 커밋마다 도는 검사 일곱을
한꺼번에 띄우면 차례로 돌 때보다 Linux 와 Windows 모두 4할 남짓 줄었다(잰 시간과 프로브는
ADR 0005 의 2026-10-07 이력). 그래서
`.pre-commit-config.yaml` 은 이 검사들을 훅 하나로 두고 이 러너가 함께 띄운다. 잰 뒤에 워크플로
감사(zizmor, ADR 0027)가 더해져 여덟이다. 그 검사는 한 번에 0.3초 남짓이지만, 그 회귀 테스트가
그때 병목이던 pytest 에 1.5~6.7초를 더한다(손으로 봤다). 함께 띄운 벽시계 시간은 다시 재지 않았다.
파일을 고치는 ruff 둘은 이 훅 앞에 따로 있어, 러너는 고친 뒤의 파일을 본다. 검사 목록의 원천은 여기
하나다. CI 는 잡마다 명령을 직접 돈다(`.github/workflows/ci.yml`).

pytest 는 pytest-xdist 로 논리 CPU 수의 절반만큼 프로세스를 나눠 돈다(ADR 0035). 함께 띄운 뒤에도
한 프로세스 pytest 가 가장 긴 막대라, 문서만 바꾼 커밋도 약 11.5분 걸렸다(대기열 309). 나누는
자리는 이 러너뿐이다. 손으로 치는 `uv run pytest`, `tools/mutate.py` 가 띄우는 pytest, LLM
테스트(`-m llm`), CI 는 한 프로세스로 돈다. 그래서 테스트끼리 부딪혀서 나는 실패는 이 러너에서만
나고, CI 의 빨강과 따로 읽는다.

통과한 검사는 한 줄을, 실패한 검사는 그 줄 뒤에 모은 출력(stdout 과 stderr)을 끝난 차례로 찍는다.
하나라도 실패하면 1로 끝난다. pre-commit 의 `SKIP` 을 같은 id 로 읽어, `SKIP=pytest git commit` 이
검사마다 훅이 따로 있던 때처럼 통한다. 명령은 `shutil.which` 로 찾는다. Windows 에서 npm 전역
설치의 `pnpm` 은 `pnpm.cmd` 라 경로 없이는 띄우지 못한다. GitHub Actions 의 windows-latest 에서
`shutil.which` 는 그것을 찾았고 경로 없는 `subprocess` 는 WinError 2 였다(실행 37561588972, 일지
2026-10-07-07).

함께 돌 때 서로 보는 파일은 Vitest 판정자 테스트가 `web/judge-*` 에 쓰는 임시 트리 하나다. 지침
검사의 중첩 지침 파일 훑기가 그 트리를 지나도 찾는 이름이 없고, 도중에 사라진 디렉터리는
건너뛴다(코드를 읽었다, 일지 2026-10-07-05).

못 보는 것: 검사 하나가 멈추면 러너도 멈춘다(시간 제한이 없다. pre-commit 도 두지 않는다). CPU 가
넷보다 적은 기계에서 함께 띄운 것이 차례로 돈 것보다 느린지는 재지 않았다. Windows 의
`pnpm.cmd` 길은 위 실행에서 한 번 봤을 뿐이고, 그 길을 거는 상설 테스트는 없다. CI 는 Linux 에서만
돈다. 세션 둘이 같은 시각에 커밋하면 pytest 프로세스가 두 배로 떠, 시간에 기댄 사례가 빨개질 수
있다. 잠금은 두지 않았다(두 벌 동시의 한 바퀴는 `.scratch/harness/probes/precommit_xdist/` 가 잰다).
절반 규칙은 이 PC(논리 CPU 16, 물리 코어 8)에서만 쟀고, `os.cpu_count()` 가 컨테이너의 CPU 한도를
반영하는지는 재지 않았다.
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
    """검사 하나. id 는 `SKIP` 이 읽는 이름이고, 러너 전부터 있던 검사는 예전 훅 id 와 같다."""

    id: str
    command: tuple[str, ...]


@dataclass(frozen=True)
class Outcome:
    check: Check
    passed: bool
    output: bytes
    seconds: float


def pytest_workers(cpu_count: int | None) -> int:
    """pytest 를 나눠 돌릴 프로세스 수. 논리 CPU 의 절반이고 1 아래로 내려가지 않는다(ADR 0035).

    `os.cpu_count()` 는 하드웨어 스레드 수라 물리 코어의 두 배일 수 있고, 값을 모르면 None 이다.
    """
    return max(1, (cpu_count or 1) // 2)


CHECKS: tuple[Check, ...] = (
    Check("pyright", ("uv", "run", "pyright")),
    Check("lint-imports", ("uv", "run", "lint-imports")),
    Check("pytest", ("uv", "run", "pytest", "-q", "-n", str(pytest_workers(os.cpu_count())))),
    Check("check-instructions", ("uv", "run", "python", "tools/check_instructions.py")),
    Check("check-type-escapes", ("uv", "run", "python", "tools/check_type_escapes.py")),
    Check("run-hooks", ("uv", "run", "python", "tools/run_hooks.py")),
    Check(
        "zizmor",
        ("uv", "run", "zizmor", "--offline", "--strict-collection")
        + ("--config", ".github/zizmor.yml", "."),
    ),
    Check("web-verify", ("pnpm", "-C", "web", "verify")),
)


def skipped_ids(environ: Mapping[str, str]) -> frozenset[str]:
    """pre-commit 의 `_get_skips` 와 같은 모양으로 읽는다. 쉼표로 나누고 공백을 걷는다."""
    return frozenset(part.strip() for part in environ.get("SKIP", "").split(",") if part.strip())


def run_one(check: Check, cwd: Path) -> Outcome:
    """검사 하나를 띄워 끝날 때까지 기다린다. 명령을 찾거나 띄우지 못하면 예외 대신 실패다."""
    start = time.monotonic()
    executable = shutil.which(check.command[0])
    if executable is None:
        message = f"명령을 찾지 못했다: {check.command[0]}\n".encode()
        return Outcome(check, passed=False, output=message, seconds=time.monotonic() - start)
    try:
        process = subprocess.run(
            [executable, *check.command[1:]],
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
    except OSError as error:
        message = f"명령을 띄우지 못했다: {executable}: {error}\n".encode()
        return Outcome(check, passed=False, output=message, seconds=time.monotonic() - start)
    return Outcome(
        check,
        passed=process.returncode == 0,
        output=process.stdout,
        seconds=time.monotonic() - start,
    )


def status_line(check_id: str, status: str) -> bytes:
    return f"{check_id:.<{_NAME_WIDTH}}{status}\n".encode()


def run(checks: Sequence[Check], environ: Mapping[str, str], cwd: Path, out: BinaryIO) -> int:
    """SKIP 밖의 검사를 한꺼번에 띄우고 끝난 차례로 찍는다. 하나라도 실패하면 1.

    environ 은 SKIP 을 읽는 데만 쓴다. 자식은 이 프로세스의 환경을 그대로 물려받는다.
    """
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
