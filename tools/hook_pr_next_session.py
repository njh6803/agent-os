"""PostToolUse 훅(Bash|PowerShell|GitHub MCP). PR을 열거나 병합하면 next-session 계기를 넣는다.

단계를 닫는 순간의 지침은 어겨진다(retro 계기가 그랬고 hook_journal_retro 가 됐다). 같은 자리라
처음부터 훅이고, 계기만 넣고 막지는 않는다. 게이트를 두지 않는 이유는 일지 2026-09-21 세션 경계.
"""

from __future__ import annotations

import json
import re
import sys
from typing import Literal, TypedDict

Action = Literal["create", "merge"]

SHELL_TOOLS = frozenset({"Bash", "PowerShell"})
MCP_TOOLS: dict[str, Action] = {
    "mcp__plugin_github_github__create_pull_request": "create",
    "mcp__plugin_github_github__merge_pull_request": "merge",
}

# 명령 위치의 `gh pr create|merge` 만 계기다. echo·printf·커밋 메시지·heredoc 본문에 문구가
# 데이터로 들어가면 오탐이었다(CodeRabbit, PR #28). 셸 파서 없이 넷만 본다. heredoc 본문과
# 인용 구간을 버리고, 제어 연산자와 명령 치환(`$(`, 백틱)으로 나누고, 조각 앞의 공백·괄호·
# 환경변수 대입을 벗긴다. 대신 `bash -c "gh pr merge"` 같은 래퍼 뒤의 실행과
# `"$(gh pr create)"` 처럼 큰따옴표 안의 치환은 못 본다. 래퍼 스크립트 사각과 같은 종류다
# (일지 2026-09-21 세션 경계).
_GH_PR = re.compile(r"gh\s+pr\s+(create|merge)\b")
# hook_bash_heredoc 의 _OPENER 와 같다. 훅은 단독 실행 스크립트라 서로 import 하지 않는다.
_HEREDOC_OPENER = re.compile(r"<<(-?)\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\2")
_QUOTED = re.compile(r"'[^']*'|\"(?:[^\"\\]|\\.)*\"")
# `2>&1` 의 & 는 리다이렉션이라 분리자가 아니다.
_SEPARATOR = re.compile(r"\|\||&&|\$\(|`|(?<![<>])[&|]|[;\n]")
_PREFIX = re.compile(r"^(?:\s+|[({]|[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*")


class ToolInput(TypedDict, total=False):
    command: str


class HookPayload(TypedDict, total=False):
    """Claude Code 가 stdin 으로 주는 훅 입력 중 이 훅이 읽는 부분."""

    tool_name: str
    tool_input: ToolInput


def action_for(tool_name: str, command: str | None) -> Action | None:
    """PR을 여는 호출이면 "create", 병합하는 호출이면 "merge", 둘 다 아니면 None.

    셸 도구는 명령 위치에 있는 `gh pr create|merge` 를 찾고, GitHub MCP 도구는 이름으로 안다.
    `gh pr view|checks|comment` 와 `git push` 는 세션을 닫는 일이 아니고, 문구를 데이터로 품은
    echo·printf·커밋 메시지·heredoc 본문도 아니다.
    """
    if tool_name in MCP_TOOLS:
        return MCP_TOOLS[tool_name]
    if tool_name not in SHELL_TOOLS or command is None:
        return None
    for segment in _executed_segments(command):
        match = _GH_PR.match(segment)
        if match is not None:
            return "create" if match.group(1) == "create" else "merge"
    return None


def _executed_segments(command: str) -> list[str]:
    """명령 위치부터 시작하는 조각들. heredoc 본문과 인용 구간을 버리고 나눈 뒤 앞을 벗긴다."""
    joined = _QUOTED.sub("", "\n".join(_without_heredoc_bodies(command)))
    return [_PREFIX.sub("", piece, count=1) for piece in _SEPARATOR.split(joined)]


def _without_heredoc_bodies(command: str) -> list[str]:
    """heredoc 여는 줄은 남기고 본문과 종료 줄을 버린다. 종료 판정은 hook_bash_heredoc 와 같다."""
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


def context_for(action: Action) -> str:
    """에이전트에게 넣을 계기 문장. 성공 여부는 방금 본 도구 결과로 에이전트가 판단한다."""
    verb = "여는" if action == "create" else "병합하는"
    return (
        f"PR을 {verb} 명령이 실행됐다. 성공했으면 next-session 스킬의 계기다. "
        "사용자에게 묻지 말고 Skill 도구로 next-session 을 지금 돌린다. "
        "PR을 열었으면 그 스킬의 1단계가 반영과 병합을 먼저 마친다. 세션은 그것으로 끝나지 않는다."
    )


def main() -> int:
    payload: HookPayload = json.load(sys.stdin)
    tool_name = payload.get("tool_name")
    if tool_name is None:
        return 0
    command = payload.get("tool_input", {}).get("command")
    action = action_for(tool_name, command)
    if action is None:
        return 0
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PostToolUse",
                    "additionalContext": context_for(action),
                }
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
