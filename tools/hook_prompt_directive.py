"""UserPromptSubmit 훅. 첫 메시지가 next-session 지시문이면 새 세션이 스스로 이름을 붙이게 한다.

이름은 여는 쪽(open-session 4단계)이 붙였는데, 첫 줄이 슬래시 명령이면 앱이 딥링크의 `/` 를 전각
`／`(U+FF0F)로 바꿔 넣어 여는 쪽이 `held=` 에서 멈추고, 사람은 새 세션에서 고쳐 보낸 뒤 옛 세션으로
돌아오지 않았다. 티켓 03·05 세션이 앱이 지은 제목으로 남았다. 그래서 받는 쪽이 붙인다. 훅은 MCP
도구를 부를 수 없으니 계기만 넣는다(CLAUDE.md 교정 루프). 형식의 원천은 next-session 스킬이다.

사람이 `／` 를 고치지 않고 보내면 스킬이 로드되지 않는다(티켓 05 세션 실측). 그때는 스킬 파일을
읽어 따르라는 줄을 붙인다. 앱의 전각 치환은 출처 모를 링크가 명령을 일으키지 못하게 하는 장치인데,
여기까지 온 것은 사람이 보내기를 누른 뒤라 그 확인은 이미 있었다.

못 보는 것: 지시문 모양은 누구나 쓸 수 있다. 막는 것은 사람이 보냈다는 것과, 이름이 kebab 한
토막이라 `.claude/skills/` 밖을 가리키지 못한다는 것뿐이다. 이미 사람이 이름을 지은 세션에 지시문을
붙여 넣으면 이 훅이 이름을 바꾸라고 하고, 그때 앱이 사람에게 승인을 묻는다.
"""

from __future__ import annotations

import json
import re
import sys
from typing import TypedDict

FULLWIDTH_SLASH = "／"
_BRANCH_LINE = "브랜치:"
_NEW_SESSION = re.compile(r"어디서:\s*새 세션")
_SKILL_NAME = re.compile(r"([a-z0-9][a-z0-9-]*)(?:\s|$)")


class HookPayload(TypedDict, total=False):
    """Claude Code 가 stdin 으로 주는 훅 입력 중 이 훅이 읽는 부분."""

    prompt: str


def context_for(prompt: str) -> str | None:
    """새 세션 지시문이면 계기 문장, 아니면 None.

    지시문은 줄 머리에 `브랜치:` 줄(값이 있다)과 `어디서: 새 세션` 줄이 있는 프롬프트다. 문장 속에서
    형식을 인용한 것은 세지 않는다.
    """
    lines = [line.strip() for line in prompt.splitlines()]
    if not any(_NEW_SESSION.match(line) for line in lines):
        return None
    branch = _branch_of(lines)
    if branch is None:
        return None
    context = (
        "next-session 지시문으로 연 새 세션이다. 여는 쪽은 이름을 붙이지 않는다. 다른 일보다 먼저 "
        "이 세션의 제목을 지시문의 브랜치 이름으로 바꾼다 — `set_session_title` 에 "
        f"`self` 와 `{branch}`. 앱이 지은 제목이면 묻지 않고 바뀐다."
    )
    skill = _fullwidth_skill(prompt)
    if skill is not None:
        context += (
            f" 첫 줄의 슬래시 명령이 전각 `{FULLWIDTH_SLASH}`(U+FF0F)라 스킬이 로드되지 않았다. "
            f"`.claude/skills/{skill}/SKILL.md` 를 읽어 그대로 따른다. "
            "스킬의 인자는 첫 줄의 이름 뒤부터 메시지 끝까지다."
        )
    return context


def _branch_of(lines: list[str]) -> str | None:
    """`브랜치:` 줄의 값. 감싼 백틱은 벗긴다. 줄이 없거나 값이 비었으면 None."""
    for line in lines:
        if line.startswith(_BRANCH_LINE):
            value = line.removeprefix(_BRANCH_LINE).strip().strip("`").strip()
            return value or None
    return None


def _fullwidth_skill(prompt: str) -> str | None:
    """첫 글자가 전각 `／` 이고 바로 뒤가 kebab 이름 하나면 그 이름.

    이름이 곧 경로라 좁게 받는다.
    """
    head = prompt.lstrip()
    if not head.startswith(FULLWIDTH_SLASH):
        return None
    match = _SKILL_NAME.match(head, len(FULLWIDTH_SLASH))
    return match.group(1) if match is not None else None


def main() -> int:
    # 훅 환경에는 PYTHONUTF8 이 없어 텍스트 stdin 이 cp949 로 읽힌다. 그러면 한글이 깨져
    # `브랜치:` 가 매치되지 않고, 예외 없이 exit 0 에 출력 0바이트로 계기가 사라진다(실측).
    # 바이트로 받아 JSON 이 UTF-8 로 풀게 한다.
    payload: HookPayload = json.load(sys.stdin.buffer)
    context = context_for(payload.get("prompt", ""))
    if context is None:
        return 0
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": context,
                }
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
