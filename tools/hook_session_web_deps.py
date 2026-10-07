"""SessionStart 훅(startup|resume). 클라우드 세션이면 web 의존성을 깐다(대기열 135).

클라우드 세션의 VM 에는 `web/node_modules` 가 없어, web verify 와 러너(tools/run_checks.py)를
돌리기 전에 `pnpm -C web install --frozen-lockfile` 을 손으로 쳐야 했다(일지 2026-10-07-03).
공식 문서(code.claude.com 의 cloud-environments, "Setup scripts vs. SessionStart hooks", 2026-10-07
읽음)는 설정 스크립트를 VM 을 갖추는 자리로, 프로젝트 설치를 SessionStart 훅의 자리로 가른다.
설정 스크립트는 환경 캐시가 있으면 건너뛰고, 훅은 시작과 이어짐마다 돈다. 클라우드 세션에서만
깔려면 `CLAUDE_CODE_REMOTE` 가 `true` 인지 보는 예를 같은 문서가 든다.

판정은 셋이다. 환경 변수 `CLAUDE_CODE_REMOTE` 가 `true` 이고, 페이로드의 `source` 가 startup·resume
이고, 프로젝트 루트 아래 `web/pnpm-lock.yaml` 이 있을 때만 pnpm 을 띄운다. 루트는
`CLAUDE_PROJECT_DIR` 이 먼저다. 페이로드의 `cwd` 는 Claude 가 `cd` 하면 따라 움직이고
`CLAUDE_PROJECT_DIR` 은 세션이 시작된 루트에 머문다(공식 hooks 문서). 이미 맞게 깔려 있으면 pnpm 이
곧 끝난다(시간은 `.claude/rules/tools.md`). 성공하면 아무것도 내지 않는다. 실패하거나 pnpm 을 찾지
못하거나 시간 안에 끝나지 않으면, 모델에게 `additionalContext` 로, 사용자에게 `systemMessage` 로
web 의 절대 경로를 든 명령과 함께 알리고 0 으로 끝난다. SessionStart 는 종료 코드로 세션을 막지
못한다(공식 hooks 문서). 명령은 `shutil.which` 로 찾는다.

못 보는 것: 로컬 세션에서는 아무것도 하지 않는다. 로컬은 체크아웃마다 손으로 까는 규약이
`docs/constitution/operations.md` 가드레일에 있다. 여러 저장소를 연 클라우드 세션은 저장소의
`.claude/settings.json` 훅을 싣지 않는다(공식 문서). 클라우드 세션이 실제로 이 훅을 부르는지는
이 훅을 병합한 뒤의 새 세션에서 처음 본다. Claude 의 첫 응답은 SessionStart 훅이 끝날 때까지
기다리므로(공식 hooks 문서), 시간 제한까지 가면 첫 응답이 그만큼 늦는다. `uv sync` 는 하지 않는다
(`README.md` 의 클론 뒤 설치).
"""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import TypedDict

INSTALL_SOURCES = frozenset({"startup", "resume"})
# 등록의 timeout(300초)보다 짧게 두어, 넘기면 훅이 스스로 알리고 끝난다. 테스트가 대조한다.
TIMEOUT_SECONDS = 240.0
INSTALL_ARGS = ("install", "--frozen-lockfile")
PNPM_MISSING = "pnpm 을 PATH 에서 찾지 못했다. 위 명령은 pnpm 을 갖춘 뒤에 친다"
_TAIL_LINES = 20


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


def web_dir(root: str) -> Path | None:
    """`root` 아래 `web/pnpm-lock.yaml` 이 있으면 그 `web/`. 없으면 None 이다."""
    web = Path(root) / "web"
    return web if (web / "pnpm-lock.yaml").is_file() else None


def manual_command(web: Path) -> str:
    """사람이나 모델이 어디서 쳐도 같은 `web/` 에 까는 명령."""
    return shlex.join(["pnpm", "-C", str(web), *INSTALL_ARGS])


def install(command: list[str], web: Path, timeout: float) -> str | None:
    """`command` 에 `-C <web> install --frozen-lockfile` 을 붙여 띄운다. 성공하면 None, 아니면
    까닭이다."""
    argv = [*command, "-C", str(web), *INSTALL_ARGS]
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
        return f"{command[0]} 를 띄우지 못했다: {error}"
    if process.returncode == 0:
        return None
    lines = process.stdout.decode("utf-8", "replace").splitlines()
    tail = "\n".join(lines[-_TAIL_LINES:])
    return f"종료 코드 {process.returncode}\n{tail}"


def failure_output(reason: str, web: Path) -> HookOutput:
    """설치하지 못했을 때 세션에 낼 JSON. 모델에게는 까닭과 손으로 칠 명령을, 사용자에게는 한
    줄을 준다."""
    command = manual_command(web)
    context = (
        f"클라우드 세션의 web 의존성 설치가 되지 않았다. web verify 와 `tools/run_checks.py` 를"
        f" 돌리기 전에 `{command}` 를 직접 친다. 까닭:\n{reason}"
    )
    return {
        "hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": context},
        "systemMessage": f"web 의존성을 깔지 못했다. `{command}` 를 직접 친다.",
    }


def main() -> int:
    payload: HookPayload = json.load(sys.stdin.buffer)
    if not should_install(os.environ.get("CLAUDE_CODE_REMOTE"), payload.get("source")):
        return 0
    web = web_dir(project_root(os.environ.get("CLAUDE_PROJECT_DIR"), payload.get("cwd")))
    if web is None:
        return 0
    pnpm = shutil.which("pnpm")
    reason = PNPM_MISSING if pnpm is None else install([pnpm], web, TIMEOUT_SECONDS)
    if reason is not None:
        print(json.dumps(failure_output(reason, web)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
