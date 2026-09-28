"""PreToolUse 훅(Bash|PowerShell). 보호 브랜치 위의 `git commit` 을 막는다.

main 은 보호 브랜치라 이 저장소에서 main 위의 커밋은 언제나 실수다. 같은 체크아웃을 세션 둘이 쓰다
커밋이 엉뚱한 브랜치에 들어간 것이 두 번이다(대기열 15) — PR #46(2026-09-23)에서는 다른 세션의
커밋이 내 피처 브랜치에 얹혔고, 2026-09-27 에는 다른 세션이 체크아웃을 main 으로 옮긴 32초 뒤 내
커밋이 main 에 들어갔다. 이 훅은 뒤의 모양을 막는다. 다른 세션의 존재는 훅이 알 수 없지만 지금
브랜치는 알 수 있고, main 위의 커밋을 막는 데는 그것으로 충분하다.

명령 위치의 `git commit` 만 본다(hook_pr_next_session 과 같은 방식 — heredoc 본문과 인용 구간을
버리고 제어 연산자로 나눈 뒤 조각 앞을 벗긴다). 브랜치는 페이로드의 `cwd` 에서
`git branch --show-current` 로 읽는다. 환경의 `GIT_DIR`·`GIT_WORK_TREE`·`GIT_COMMON_DIR` 은 벗기고
읽는다 — git 이 훅 자식에 내보낸 값이 남아 있으면 cwd 가 아닌 저장소의 브랜치가 나온다(pre-commit
아래 실측, 2026-09-28). 훅은 단독 실행 스크립트라 서로 import 하지 않는다.
못 보는 것: `git -C <다른 저장소> commit` 과 `cd <다른 저장소> && git commit`(둘 다 cwd 의 브랜치로
판정한다 — 앞은 못 막고 뒤는 오탐이다), 래퍼 스크립트 안의 커밋, detached HEAD(브랜치 이름이 비어
막지 않는다), git 이 없거나 저장소 밖(막지 않는다 — 게이트가 아니라 안전장치라 fail-open 이다),
앞 모양(다른 세션의 커밋이 내 브랜치에 얹히는 것).
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from typing import TypedDict

PROTECTED = frozenset({"main"})
_REPO_LOCATION_VARS = ("GIT_DIR", "GIT_WORK_TREE", "GIT_COMMON_DIR")

# `commit-tree`·`commit-graph` 는 커밋이 아니라 배관이다. `\b` 는 `-` 앞에서도 경계라 따로 막는다.
_GIT_COMMIT = re.compile(r"git\s+(?:(?:-C|-c)\s+\S+\s+|--no-pager\s+)*commit(?![\w-])")
_HEREDOC_OPENER = re.compile(r"<<(-?)\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\2")
_QUOTED = re.compile(r"'[^']*'|\"(?:[^\"\\]|\\.)*\"")
_SEPARATOR = re.compile(r"\|\||&&|\$\(|`|(?<![<>])[&|]|[;\n]")
_PREFIX = re.compile(r"^(?:\s+|[({]|[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*")


class ToolInput(TypedDict, total=False):
    command: str


class HookPayload(TypedDict, total=False):
    """Claude Code 가 stdin 으로 주는 훅 입력 중 이 훅이 읽는 부분."""

    tool_input: ToolInput
    cwd: str


def commits_in(command: str) -> bool:
    """명령 위치에 `git commit` 이 있는가. echo·heredoc·커밋 메시지 안의 문구는 아니다."""
    return any(_GIT_COMMIT.match(segment) for segment in _executed_segments(command))


def _executed_segments(command: str) -> list[str]:
    joined = _QUOTED.sub("", "\n".join(_without_heredoc_bodies(command)))
    return [_PREFIX.sub("", piece, count=1) for piece in _SEPARATOR.split(joined)]


def _without_heredoc_bodies(command: str) -> list[str]:
    lines = command.splitlines()
    kept: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        kept.append(line)
        index += 1
        opener = _HEREDOC_OPENER.search(line)
        if opener is None:
            continue
        strips_tabs = opener.group(1) == "-"
        terminator = opener.group(3)
        while index < len(lines):
            candidate = lines[index].lstrip("\t") if strips_tabs else lines[index]
            index += 1
            if candidate == terminator:
                break
    return kept


def current_branch(cwd: str | None) -> str | None:
    """`cwd` 의 현재 브랜치 이름. 저장소가 아니거나 detached 면 None."""
    env = {key: value for key, value in os.environ.items() if key not in _REPO_LOCATION_VARS}
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=cwd,
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None


def deny_reason(branch: str | None) -> str | None:
    """보호 브랜치면 막는 이유, 아니면 None. 커밋 명령인지는 부르는 쪽이 먼저 본다."""
    if branch not in PROTECTED:
        return None
    return (
        f"지금 브랜치가 `{branch}` 이다. 보호 브랜치 위의 커밋은 이 저장소에서 언제나 실수다"
        "(대기열 15 — 2026-09-27 에 다른 세션이 체크아웃을 옮긴 32초 뒤의 커밋이 main 에 "
        "들어갔다). `git branch --show-current` 로 브랜치를 보고, 작업 브랜치로 옮기거나 만든 뒤 "
        "커밋한다."
    )


def reason_for(command: str, branch: str | None) -> str | None:
    return deny_reason(branch) if commits_in(command) else None


def main() -> int:
    # stdin 은 바이트로. 이유는 .claude/rules/tools.md(대기열 25).
    payload: HookPayload = json.load(sys.stdin.buffer)
    command = payload.get("tool_input", {}).get("command")
    if command is None or not commits_in(command):
        return 0
    reason = deny_reason(current_branch(payload.get("cwd")))
    if reason is None:
        return 0
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
