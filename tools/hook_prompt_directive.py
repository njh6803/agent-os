"""UserPromptSubmit 훅. 첫 메시지가 next-session 지시문이면 새 세션이 스스로 이름을 붙이게 한다.

이름은 여는 쪽(open-session 4단계)이 붙였는데, 첫 줄이 슬래시 명령이면 앱이 딥링크의 `/` 를 전각
`／`(U+FF0F)로 바꿔 넣어 여는 쪽이 `held=` 에서 멈추고, 사람은 새 세션에서 고쳐 보낸 뒤 옛 세션으로
돌아오지 않았다. 티켓 03·05 세션이 앱이 지은 제목으로 남았다. 그래서 받는 쪽이 붙인다. 훅은 MCP
도구를 부를 수 없으니 계기만 넣는다(CLAUDE.md 교정 루프). 형식의 원천은 next-session 스킬이다.

사람이 `／` 를 고치지 않고 보내면 스킬이 로드되지 않는다(티켓 05 세션 실측). 그때는 스킬 파일을
읽어 따르라는 줄을 붙인다. 앱의 전각 치환은 출처 모를 링크가 명령을 일으키지 못하게 하는 장치인데,
여기까지 온 것은 사람이 보내기를 누른 뒤라 그 확인은 이미 있었다.

첫 턴에만 낸다. 내용만으로는 "지시문으로 연 세션"과 "지시문을 붙여 넣고 이야기하는 세션"이 같다.
이 훅을 만든 세션에 사람이 지시문을 붙여 질문하자 훅이 그 세션 이름을 바꾸라고 했고, 제목이 앱이
지은 것이라 따랐으면 묻지 않고 바뀌었다(실측). 같은 제목이 둘이 되면 open-session 1단계가 "그
세션이 하고 있다"며 열지 않는다. 지시문으로 연 세션은 지시문이 언제나 첫 메시지이므로,
트랜스크립트에 assistant 기록이 아직 없을 때만 낸다. 훅이 도는 시점에 지금 프롬프트가 기록됐는지와
무관하다.

못 보는 것: 지시문 모양은 누구나 쓸 수 있다. 막는 것은 사람이 보냈다는 것, 첫 턴이라는 것, 이름이
kebab 한 토막이라 `.claude/skills/` 밖을 가리키지 못한다는 것뿐이다. 사람이 손으로 연 새 세션에
지시문을 첫 메시지로 붙여 넣은 것도 발동하는데, 그것은 open-session 이 하는 일과 같아 의도한 쪽이다.
`/clear` 뒤의 첫 메시지도 같다. 트랜스크립트가 새 파일로 시작해 assistant 기록이 없으므로 발동하고,
같은 앱 세션이 그 지시문의 일로 새로 시작하는 것이라 이름을 바꾸는 것이 맞다고 본다.
"""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Iterable
from pathlib import Path
from typing import TypedDict

FULLWIDTH_SLASH = "／"
_BRANCH_LINE = "브랜치:"
_NEW_SESSION = re.compile(r"어디서:\s*새 세션")
_SKILL_NAME = re.compile(r"([a-z0-9][a-z0-9-]*)(?:\s|$)")


class HookPayload(TypedDict, total=False):
    """Claude Code 가 stdin 으로 주는 훅 입력 중 이 훅이 읽는 부분."""

    prompt: str
    transcript_path: str


class TranscriptRecord(TypedDict, total=False):
    """트랜스크립트 JSONL 한 줄 중 이 훅이 읽는 부분."""

    type: str


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


def is_first_turn(transcript_path: str | None) -> bool:
    """이 세션에서 모델이 아직 한 번도 답하지 않았는가.

    두 부재를 반대로 판정한다. 파일이 아직 없으면 첫 턴이다 — 새 세션의 첫 프롬프트에서는
    트랜스크립트가 만들어지기 전일 수 있다. 경로 키가 없으면 첫 턴을 증명할 수 없으니 아니라고
    본다. 잘못 발동하면 엉뚱한 세션의 이름이 조용히 바뀌고, 발동하지 않으면 앱이 지은 제목이 남아
    open-session 4단계의 확인이 알린다. 빈 경로도 모르는 것이다(`Path("")` 는 작업 디렉터리다).
    """
    if not transcript_path:
        return False
    path = Path(transcript_path)
    if not path.exists():
        return True
    with path.open(encoding="utf-8", errors="replace") as transcript:
        return not has_assistant_turn(transcript)


def has_assistant_turn(lines: Iterable[str]) -> bool:
    """트랜스크립트 JSONL 에 assistant 기록이 하나라도 있으면 True. 첫 것에서 멈춘다."""
    return any(_record_type(line) == "assistant" for line in lines)


def _record_type(line: str) -> str | None:
    """JSONL 한 줄의 최상위 `type`. JSON 객체가 아니면 None.

    `{` 로 시작하는 올바른 JSON 은 객체뿐이라 주해가 참이다. 본문 문자열 속의 같은 글자는
    세지 않는다.
    """
    if not line.lstrip().startswith("{"):
        return None
    try:
        record: TranscriptRecord = json.loads(line)
    except ValueError:
        return None
    return record.get("type")


def main() -> int:
    # 훅 환경에는 PYTHONUTF8 이 없어 텍스트 stdin 이 cp949 로 읽힌다. 그러면 한글이 깨져
    # `브랜치:` 가 매치되지 않고, 예외 없이 exit 0 에 출력 0바이트로 계기가 사라진다(실측).
    # 바이트로 받아 JSON 이 UTF-8 로 풀게 한다.
    payload: HookPayload = json.load(sys.stdin.buffer)
    context = context_for(payload.get("prompt", ""))
    # 지시문일 때만 트랜스크립트를 연다. 평범한 프롬프트마다 긴 파일을 읽지 않는다.
    if context is None or not is_first_turn(payload.get("transcript_path")):
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
