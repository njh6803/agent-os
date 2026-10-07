"""SessionStart 훅(startup|resume). 클라우드 세션이면 git 훅과 web 의존성을 깐다.

클라우드 세션의 VM 에는 `web/node_modules` 가 없어, web verify 와 러너(tools/run_checks.py)를
돌리기 전에 `pnpm -C web install --frozen-lockfile` 을 손으로 쳐야 했다(일지 2026-10-07-05, 대기열
138). 새 클론이라 pre-commit 의 git 훅도 없어, 손으로 `uv run pre-commit install` 을 치기 전의
커밋은 인용 대조·변이 표 원문 확인·커밋 메시지 검사(셋 다 CI 에 없다)를 조용히 건너뛴다(일지
2026-10-07-10 의 회고). 공식 문서(code.claude.com 의 cloud-environments, "Setup scripts vs.
SessionStart hooks", 2026-10-07 읽음)는 설정 스크립트를 VM 을 갖추는 자리로, 프로젝트 설치를
SessionStart 훅의 자리로 가른다. 설정 스크립트는 환경 캐시가 있으면 건너뛰고, 훅은 시작과
이어짐마다 돈다. 클라우드 세션에서만 깔려면 `CLAUDE_CODE_REMOTE` 가 `true` 인지 보는 예를 같은
문서가 든다.

판정은 넷이다. 환경 변수 `CLAUDE_CODE_REMOTE` 가 `true` 이고, 페이로드의 `source` 가 startup·resume
일 때만 깐다. 그 위에서 프로젝트 루트에 `.pre-commit-config.yaml` 이 있으면
`uv run --directory <루트> pre-commit install` 을, 루트 아래 `web/pnpm-lock.yaml` 이 있으면 pnpm 을
띄운다(`plan`). git 훅이 먼저다. 앞의 것이 빠진 커밋은 조용하고 뒤의 것이 빠진 검사는 시끄럽게
빨갛다. `uv run` 은 빈 `.venv` 를 먼저 맞춘다(등록의 `--no-sync` 가 만든 빈 `.venv`, 일지
2026-10-07-10). 두 설치는 훅 안의 시간 제한 하나를 나눠 쓴다(`run_steps`). 루트는
`CLAUDE_PROJECT_DIR` 이 먼저다. 페이로드의 `cwd` 는 Claude 가 `cd` 하면 따라 움직이고
`CLAUDE_PROJECT_DIR` 은 세션이 시작된 루트에 머문다(공식 hooks 문서). 이미 맞게 깔려 있으면 둘 다
곧 끝난다(시간은 `.claude/rules/tools.md`). 성공하면 아무것도 내지 않는다. 실패하거나 명령을 찾지
못하거나 시간 안에 끝나지 않으면, 모델에게 `additionalContext` 로, 사용자에게 `systemMessage` 로
절대 경로를 든 명령과 함께 알리고 0 으로 끝난다. SessionStart 는 종료 코드로 세션을 막지 못한다(공식
hooks 문서). 명령은 `shutil.which` 로 찾는다.

못 보는 것: 로컬 세션에서는 아무것도 하지 않는다. 로컬은 주 체크아웃에서 한 번 치는 pre-commit
install 과 체크아웃마다 손으로 까는 pnpm 의 규약이 `docs/constitution/operations.md` 가드레일에
있다. 루트가 워크트리이면 pre-commit install 이 공유 git 훅의 인터프리터를 그 워크트리의 것으로
덮는다(같은 가드레일의 경고. 클라우드 세션은 새 클론이라 워크트리에 서지 않는다). 여러 저장소를 연
클라우드 세션은 저장소의 `.claude/settings.json` 훅을 싣지 않는다(공식 문서). Claude 의 첫 응답은
SessionStart 훅이 끝날 때까지 기다리므로(공식 hooks 문서), 시간 제한까지 가면 첫 응답이 그만큼
늦는다. git 훅을 까는 길이 실제 클라우드 세션에서 도는지는 이 변경을 병합한 뒤의 새 세션에서 처음
본다.
"""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import NamedTuple, TypedDict

INSTALL_SOURCES = frozenset({"startup", "resume"})
# 등록의 timeout(300초)보다 짧게 두어, 넘기면 훅이 스스로 알리고 끝난다. 두 설치가 나눠 쓴다.
# 테스트가 대조한다.
TIMEOUT_SECONDS = 240.0
MIN_STEP_SECONDS = 1.0
INSTALL_ARGS = ("install", "--frozen-lockfile")
PRE_COMMIT_CONFIG = ".pre-commit-config.yaml"
GIT_HOOKS_LABEL = "git 훅(pre-commit) 설치"
WEB_DEPS_LABEL = "web 의존성 설치"
PNPM_MISSING = "pnpm 을 PATH 에서 찾지 못했다. 위 명령은 pnpm 을 갖춘 뒤에 친다"
UV_MISSING = "uv 를 PATH 에서 찾지 못했다. 위 명령은 uv 를 갖춘 뒤에 친다"
_TAIL_LINES = 20


class Failure(NamedTuple):
    what: str
    reason: str
    command: str  # 손으로 칠 명령


@dataclass(frozen=True)
class Step:
    """설치 하나. 띄울 프로그램을 찾아 `run(프로그램 경로, 시간 제한)` 으로 깐다. 실패하면 까닭."""

    what: str
    program: str
    missing: str
    run: Callable[[str, float], str | None]
    command: str


class HookPayload(TypedDict, total=False):
    """Claude Code 가 stdin 으로 주는 SessionStart 입력 중 이 훅이 읽는 부분."""

    source: str
    cwd: str


class _Specific(TypedDict):
    hookEventName: str
    additionalContext: str


class HookOutput(TypedDict):
    hookSpecificOutput: _Specific
    systemMessage: str


def should_install(remote: str | None, source: str | None) -> bool:
    """클라우드 세션이 시작되거나 이어질 때만 참이다."""
    return remote == "true" and source in INSTALL_SOURCES


def project_root(project_dir: str | None, cwd: str | None) -> str:
    """설치할 프로젝트의 루트. `CLAUDE_PROJECT_DIR`, 페이로드의 `cwd`, 현재 디렉터리 차례다."""
    return project_dir or cwd or os.getcwd()


def pre_commit_root(root: str) -> Path | None:
    """`root` 에 pre-commit 설정이 있으면 그 루트. 없으면 None 이다."""
    path = Path(root)
    return path if (path / PRE_COMMIT_CONFIG).is_file() else None


def web_dir(root: str) -> Path | None:
    """`root` 아래 `web/pnpm-lock.yaml` 이 있으면 그 `web/`. 없으면 None 이다."""
    web = Path(root) / "web"
    return web if (web / "pnpm-lock.yaml").is_file() else None


def pre_commit_args(root: Path) -> list[str]:
    """`uv` 뒤에 붙여 `root` 의 저장소에 git 훅을 까는 인자. pre-commit 은 지금 디렉터리의 저장소에
    까므로 uv 가 `--directory` 로 그리 옮겨 띄운다."""
    return ["run", "--directory", str(root), "pre-commit", "install"]


def manual_command(web: Path) -> str:
    """사람이나 모델이 어디서 쳐도 같은 `web/` 에 까는 명령."""
    return shlex.join(["pnpm", "-C", str(web), *INSTALL_ARGS])


def pre_commit_command(root: Path) -> str:
    """사람이나 모델이 어디서 쳐도 같은 저장소에 git 훅을 까는 명령."""
    return shlex.join(["uv", *pre_commit_args(root)])


def step_timeout(deadline: float, now: float) -> float:
    """두 설치가 나눠 쓰는 시간 제한에서 이번 설치가 받는 몫. 다 썼어도 1초는 받는다."""
    return max(deadline - now, MIN_STEP_SECONDS)


def _run(argv: list[str], timeout: float) -> str | None:
    """`argv` 를 띄운다. 성공하면 None, 아니면 까닭이다."""
    try:
        process = subprocess.run(
            argv,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            timeout=timeout,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return f"{timeout}초 안에 끝나지 않았다"
    except OSError as error:
        return f"{argv[0]} 를 띄우지 못했다: {error}"
    if process.returncode == 0:
        return None
    lines = process.stdout.decode("utf-8", "replace").splitlines()
    tail = "\n".join(lines[-_TAIL_LINES:])
    return f"종료 코드 {process.returncode}\n{tail}"


def install(command: list[str], web: Path, timeout: float) -> str | None:
    """`command` 에 `-C <web> install --frozen-lockfile` 을 붙여 띄운다. 성공하면 None, 아니면
    까닭이다."""
    return _run([*command, "-C", str(web), *INSTALL_ARGS], timeout)


def install_pre_commit(command: list[str], root: Path, timeout: float) -> str | None:
    """`command` 에 `run --directory <root> pre-commit install` 을 붙여 띄운다. 성공하면 None,
    아니면 까닭이다."""
    return _run([*command, *pre_commit_args(root)], timeout)


def plan(root: str) -> list[Step]:
    """`root` 에서 할 설치를 차례대로. git 훅이 먼저다."""
    steps: list[Step] = []
    hooks = pre_commit_root(root)
    if hooks is not None:

        def run_pre_commit(program: str, timeout: float) -> str | None:
            return install_pre_commit([program], hooks, timeout)

        command = pre_commit_command(hooks)
        steps.append(Step(GIT_HOOKS_LABEL, "uv", UV_MISSING, run_pre_commit, command))
    web = web_dir(root)
    if web is not None:

        def run_pnpm(program: str, timeout: float) -> str | None:
            return install([program], web, timeout)

        command = manual_command(web)
        steps.append(Step(WEB_DEPS_LABEL, "pnpm", PNPM_MISSING, run_pnpm, command))
    return steps


def run_steps(
    steps: list[Step],
    which: Callable[[str], str | None],
    clock: Callable[[], float],
) -> list[Failure]:
    """설치를 차례로 띄우고 실패를 모은다. 모두가 `TIMEOUT_SECONDS` 하나를 나눠 쓴다."""
    deadline = clock() + TIMEOUT_SECONDS
    failures: list[Failure] = []
    for step in steps:
        program = which(step.program)
        if program is None:
            reason: str | None = step.missing
        else:
            reason = step.run(program, step_timeout(deadline, clock()))
        if reason is not None:
            failures.append(Failure(step.what, reason, step.command))
    return failures


def failure_output(failures: list[Failure]) -> HookOutput:
    """설치하지 못했을 때 세션에 낼 JSON. 모델에게는 설치마다 까닭과 손으로 칠 명령을, 사용자에게는
    한 줄을 준다."""
    items = [f"- {f.what}: `{f.command}` 를 직접 친다. 까닭:\n{f.reason}" for f in failures]
    head = "클라우드 세션의 준비가 덜 됐다. 커밋과 검증 명령 전에 아래를 친다."
    commands = "; ".join(f"`{f.command}`" for f in failures)
    return {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": "\n".join([head, *items]),
        },
        "systemMessage": f"세션 준비가 덜 됐다. {commands} 를 직접 친다.",
    }


def main() -> int:
    payload: HookPayload = json.load(sys.stdin.buffer)
    if not should_install(os.environ.get("CLAUDE_CODE_REMOTE"), payload.get("source")):
        return 0
    root = project_root(os.environ.get("CLAUDE_PROJECT_DIR"), payload.get("cwd"))
    failures = run_steps(plan(root), shutil.which, time.monotonic)
    if failures:
        print(json.dumps(failure_output(failures)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
