"""PostToolUse 훅(Write|Edit). 일지를 갱신하면 retro 계기를 컨텍스트에 넣는다.

계기는 retro 스킬 설명("일지의 '다음' 절을 갱신하며 단계를 닫을 때")에 지침으로 있었는데
2026-09-21 세션에서 에이전트가 일지를 쓰고도 돌리지 않았다. 지침이 어겨졌으니 훅이다(CLAUDE.md
교정 루프). stdin 으로 훅 JSON 을 받고, 경로가 docs/journal/*.md 면 additionalContext 를 낸다.
"""

from __future__ import annotations

import json
import sys
from pathlib import PurePath
from typing import TypedDict

JOURNAL_PARTS = ("docs", "journal")


class ToolInput(TypedDict, total=False):
    file_path: str


class HookPayload(TypedDict, total=False):
    """Claude Code 가 stdin 으로 주는 훅 입력 중 이 훅이 읽는 부분."""

    tool_input: ToolInput


CONTEXT = (
    "docs/journal/ 의 일지를 갱신했다. 이것이 단계를 닫는 갱신('다음' 절을 새로 썼다)이면 "
    "retro 스킬의 계기다. 사용자에게 묻지 말고 Skill 도구로 retro 를 지금 돌린다."
)


def context_for(file_path: str) -> str | None:
    """docs/journal/<name>.md 를 쓴 것이면 컨텍스트 문장, 아니면 None."""
    path = PurePath(file_path.replace("\\", "/"))
    parts = path.parts
    if path.suffix != ".md" or len(parts) < 3:
        return None
    if tuple(parts[-3:-1]) != JOURNAL_PARTS:
        return None
    return CONTEXT


def main() -> int:
    payload: HookPayload = json.load(sys.stdin)
    file_path = payload.get("tool_input", {}).get("file_path")
    context = context_for(file_path) if file_path is not None else None
    if context is None:
        return 0
    print(
        json.dumps(
            {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": context}}
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
