"""PostToolUse 훅(Write|Edit). 일지를 단계를 닫는 모양으로 갱신하면 retro 계기를 컨텍스트에 넣는다.

계기는 retro 스킬 설명("일지의 '다음' 절을 갱신하며 단계를 닫을 때")에 지침으로 있었는데
2026-09-21 세션에서 에이전트가 일지를 쓰고도 돌리지 않았다. 지침이 어겨졌으니 훅이다(CLAUDE.md
교정 루프). stdin 으로 훅 JSON 을 받고, 경로가 docs/journal/*.md 이면 additionalContext 를 낸다.

발동 조건은 하나다. 쓴 본문 — Write 의 `content` 나 Edit 의 `new_string` — 이 `## 다음` 을 담을 때.
대기열 28(사용자 승인 2026-09-24)은 Write 를 무조건 계기로 두었는데, 세션 첫머리에 일지를 새로 쓰는
Write 는 단계를 닫는 것이 아니라 좁혔다(PR #91 리뷰). 경로만 보던 동안 인용 하나를 고친 Edit 마다
계기가 울렸다(대기열 28 의 5회차와 일지 2026-09-27-01·02 의 둘). 세션이 그것을 무시하는 법을
배우고, 무시하는 습관은 진짜 계기도 무시하게 만든다.
못 보는 것: `## 다음` 제목 아래 불릿만 고친 Edit(제목이 new_string 에 없다). 그것은 절을 새로 쓴
것이 아니라 손본 것이라 계기가 아니다.
"""

from __future__ import annotations

import json
import sys
from pathlib import PurePath
from typing import TypedDict

JOURNAL_PARTS = ("docs", "journal")
CLOSING_HEADING = "## 다음"


class ToolInput(TypedDict, total=False):
    file_path: str
    content: str
    new_string: str


class HookPayload(TypedDict, total=False):
    """Claude Code 가 stdin 으로 주는 훅 입력 중 이 훅이 읽는 부분."""

    tool_name: str
    tool_input: ToolInput


CONTEXT = (
    "docs/journal/ 의 일지를 단계를 닫는 모양으로 갱신했다('다음' 절을 새로 썼다). "
    "retro 스킬의 계기다. 사용자에게 묻지 말고 Skill 도구로 retro 를 지금 돌린다."
)


def is_journal(file_path: str) -> bool:
    """docs/journal/<name>.md 인가."""
    path = PurePath(file_path.replace("\\", "/"))
    parts = path.parts
    if path.suffix != ".md" or len(parts) < 3:
        return False
    return tuple(parts[-3:-1]) == JOURNAL_PARTS


def context_for(tool_name: str, file_path: str, text: str | None) -> str | None:
    """단계를 닫는 일지 갱신이면 컨텍스트 문장, 아니면 None. `text` 는 Write 의 content 나 Edit 의
    new_string 이다."""
    if not is_journal(file_path) or tool_name not in ("Write", "Edit"):
        return None
    if text is not None and CLOSING_HEADING in text:
        return CONTEXT
    return None


def main() -> int:
    payload: HookPayload = json.load(sys.stdin.buffer)
    tool_input = payload.get("tool_input", {})
    file_path = tool_input.get("file_path")
    if file_path is None:
        return 0
    tool_name = payload.get("tool_name", "")
    text = tool_input.get("content") if tool_name == "Write" else tool_input.get("new_string")
    context = context_for(tool_name, file_path, text)
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
