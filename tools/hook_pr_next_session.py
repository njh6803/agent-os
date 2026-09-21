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

_GH_PR = re.compile(r"\bgh\s+pr\s+(create|merge)\b")


class ToolInput(TypedDict, total=False):
    command: str


class HookPayload(TypedDict, total=False):
    """Claude Code 가 stdin 으로 주는 훅 입력 중 이 훅이 읽는 부분."""

    tool_name: str
    tool_input: ToolInput


def action_for(tool_name: str, command: str | None) -> Action | None:
    """PR을 여는 호출이면 "create", 병합하는 호출이면 "merge", 둘 다 아니면 None.

    셸 도구는 명령 문자열에서 `gh pr create|merge` 를 찾고, GitHub MCP 도구는 이름으로 안다.
    `gh pr view|checks|comment` 와 `git push` 는 세션을 닫는 일이 아니다.
    """
    if tool_name in MCP_TOOLS:
        return MCP_TOOLS[tool_name]
    if tool_name not in SHELL_TOOLS or command is None:
        return None
    match = _GH_PR.search(command)
    if match is None:
        return None
    return "create" if match.group(1) == "create" else "merge"


def context_for(action: Action) -> str:
    """에이전트에게 넣을 계기 문장. 성공 여부는 방금 본 도구 결과로 에이전트가 판단한다."""
    verb = "여는" if action == "create" else "병합하는"
    return (
        f"PR을 {verb} 명령이 실행됐다. 성공했으면 next-session 스킬의 계기다. "
        "사용자에게 묻지 말고 Skill 도구로 next-session 을 지금 돌린다."
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
