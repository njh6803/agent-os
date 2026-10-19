"""PostToolUse 훅(Write|Edit). 근거로 읽히는 문서(`docs/adr/`, `.scratch/**/probes/README.md`,
`.scratch/retro-queue.md`)에 더한 줄이 측정 낱말(`쟀다`·`재니`·`실측`)을 들면서 같은 줄에 `probes/`
경로도 `손으로`도 없으면, `docs/agents/issue-tracker.md` 의 "프로브와 근거" 절을 컨텍스트에 넣는다.

왜. 그 절은 "쟀다"·"실측"을 커밋한 프로브가 다시 내는 것에만 쓰고 그 파일을 가리키며, 손으로 돌려 본
것은 손으로 봤다고 적으라고 한다(대기열 45). 그 절이 지침이 된 뒤에도 ADR 이력에 손으로 돌린 시간
비교를 "재니"로 적었고, 셀프 리뷰 두 축이 잡은 뒤 프로브로 다시 재느라 측정을 세 번 돌았다(대기열
227, 일지 2026-10-13-26 외 둘). 쓰는 순간에 알리는 계기 훅이고 막지 않는다 — 낱말이 근거 문장인지,
낱말을 이름으로 든 것인지는 모델이 가른다(`.claude/rules/tools.md` 의 계기·막는 훅 가름).

왜 따로 등록하는가. Write·Edit 의 다른 PostToolUse 훅은 저마다 다른 일을 판정한다(일지 회고 계기,
ruff, 줄 구분 문자, 스크래치 스크립트, 도는 커밋. `tools/hook_scratch_probe_rule.py` 의 같은 문단).
여기에 얹으면 독스트링의 왜·못 보는 것과 페이로드 표의 사례가 두 판정으로 섞인다. 등록은 첫
`Write|Edit` 묶음에 더한다. 값은 Write·Edit 마다 래퍼를 거친 파이썬 한 번이다(약 0.2초, 이 훅은 재지
않았고 `.claude/rules/tools.md` 시간 항목의 어림이다).

판정. 도구가 Write·Edit 이고 `tool_input.file_path` 가 문자열이며 `is_evidence_doc` 이 참이면, 더한
줄(`added_lines`)마다 `MEASURE_WORDS` 가운데 하나가 들고 `EXEMPT_MARKS` 는 하나도 없는 줄을 고른다.
더한 줄은 쓰기 전 파일에 없던 쓴 뒤 파일의 줄이다. 쓰기 전 파일은 결과의 `originalFile` 이다(덮어쓴
Write 와 Edit 에서 문자열이고, 새 파일을 만든 Write 에서는 null 이다. 프로브 README 의
`journal_number_hook/` 행의 2026-10-16 결과). 쓴 뒤 파일은 Write 면 `content`, Edit 면
`originalFile` 에서 `old_string` 을 `new_string` 으로 바꾼 글이다(`replace_all` 이 참이면 모두,
아니면 처음 하나). Edit 의 조각은 줄의 일부일 수 있어, 조각만 보면 같은 줄의 나머지에 든 `probes/`
를 보지 못한다(셀프 리뷰가 잡았다, 일지 2026-10-19-06). `originalFile` 이 문자열이 아니거나
`old_string` 이 그 안에 없는 Edit 은 조각 둘을 쓰기 전·뒤 글로 본다. 줄 집합의 차라 순서와 횟수는
보지 않는다. 걸린 줄은 앞의 `SHOWN_LINES` 개를 `LINE_WIDTH` 글자로 잘라 문장에 싣는다.

한 번이 아니다. 형제 훅(`hook_scratch_probe_rule`)과 달리 표지를 두지 않고 걸릴 때마다 알린다.
알림이 걸린 줄을 보여 주므로, 앞의 알림을 "인용일 뿐"으로 넘긴 세션도 뒤의 근거 문장에서 다시 본다.

못 보는 것:
- 다른 꼴의 측정 낱말(`잰`, `재 보니`, `측정했다`). 대기열 227 이 고른 셋만 본다.
- 낱말을 이름으로만 든 줄(대기열 행이 "`쟀다`·`실측`을 든 줄"이라고 적은 것). 근거 문장과 가르지
  않고 알린다.
- 옛 줄을 고쳐 쓴 것. 줄의 다른 자리만 고쳐도(대기열 행에 취소선을 긋는 것) 쓴 뒤 파일에서는 그 줄
  전체가 새 줄이라 옛 낱말이 다시 걸린다. 알림이 이 경우는 무시하라고 적는다. `originalFile` 이 없는
  Edit 은 조각만 보므로 거꾸로 낱말이 조각 밖에 있으면 지나간다.
- 근거가 같은 줄 밖에 있는 문장. 줄을 바꿔 `probes/` 를 적은 감긴 문단도, 프로브를 첫 칸에 파일
  이름으로만 드는 프로브 README 의 행도 알린다. 알림이 이 경우도 무시하라고 적는다.
- `probes/` 를 들기만 하고 그 파일이 낱말의 근거인지, `손으로` 가 부정문인지("손으로 보지 않고
  실측했다"). 같은 줄에 그 문자열이 있으면 지나간다.
- 정규화하지 않은 경로(`docs/./adr/`, `..`). 토막을 그대로 견준다. 거꾸로 `docs/adr` 토막은 어느
  깊이에 있든, 확장자가 무엇이든 받는다.
- Bash heredoc·`>>`·`sed -i` 로 쓴 문서. 이 훅은 편집 도구에만 붙는다.
- 세 자리 밖의 근거 글(명세, 코드 주석, `.claude/rules/`). 대기열 227 의 "어디로" 칸이 고른 자리만
  본다.
- 알림이 실제 세션의 모델에게 닿는지. 아직 재지 않았다(`.claude/rules/tools.md` 의 새 훅 항목이
  말하는 모델이 옮기게 하는 확인).
"""

from __future__ import annotations

import json
import re
import sys
from typing import TypedDict

TOOLS = ("Write", "Edit")
MEASURE_WORDS = ("쟀다", "재니", "실측")
EXEMPT_MARKS = ("probes/", "손으로")
SHOWN_LINES = 3
LINE_WIDTH = 160
# 알림의 첫 문장. 알림이 모델에게 닿는지 잴 때 모델이 옮겼는지 볼 문구다.
LEAD = "근거로 읽히는 문서에 측정 낱말을 든 줄을 더했다"
_BODY = (
    "{lead}. 그 줄에 커밋한 프로브(`probes/` 경로)도 `손으로`도 없다. "
    '`docs/agents/issue-tracker.md` 의 "프로브와 근거" 절이 정한 대로, "쟀다"·"실측"은 커밋한 '
    "프로브가 다시 내는 것에만 쓰고 그 파일을 가리킨다. 손으로 돌려 본 것은 그 명령과 함께 손으로 "
    "봤다고, 코드를 읽은 것은 파일과 판과 함께 읽었다고, 재지 않은 것은 어림이라고 고쳐 적는다. "
    "다음 셋이면 고치지 않고 이 알림은 무시한다. 낱말을 이름으로 든 것뿐이다. 이미 있던 줄의 다른 "
    "자리만 고쳤다(취소선, 닫힘 표지). 근거 프로브가 같은 줄 밖(감긴 문단의 앞뒤 줄, 프로브 README "
    "행의 첫 칸)에 있다. 걸린 줄({count}개):\n{lines}"
)
_SPLIT = re.compile(r"[\\/]+")


class ToolInput(TypedDict, total=False):
    file_path: object
    content: object
    old_string: object
    new_string: object
    replace_all: object


class ToolResponse(TypedDict, total=False):
    type: str
    originalFile: object


class HookPayload(TypedDict, total=False):
    """Claude Code 가 stdin 으로 주는 훅 입력 중 이 훅이 읽는 부분. `tool_input`·`tool_response` 는
    객체가 아닌 값이 와도 `context_for` 가 런타임에 다시 본다."""

    tool_name: str
    tool_input: ToolInput
    tool_response: ToolResponse


def is_evidence_doc(path: str) -> bool:
    """`docs/adr/` 아래 파일, `.scratch/` 아래의 `probes/README.md`, `.scratch/retro-queue.md`
    인가."""
    parts = [part.casefold() for part in _SPLIT.split(path) if part]
    if len(parts) < 2:
        return False
    *folders, name = parts
    if any(folders[index : index + 2] == ["docs", "adr"] for index in range(len(folders) - 1)):
        return True
    if folders[-1] == ".scratch" and name == "retro-queue.md":
        return True
    return name == "readme.md" and folders[-1] == "probes" and ".scratch" in folders[:-1]


def added_lines(old: str, new: str) -> list[str]:
    """`new` 의 비지 않은 줄 가운데 `old` 에 없던 줄."""
    before = set(old.splitlines())
    return [line for line in new.splitlines() if line.strip() and line not in before]


def flagged_lines(lines: list[str]) -> list[str]:
    """측정 낱말을 들고 근거 표지가 없는 줄."""
    return [
        line
        for line in lines
        if any(word in line for word in MEASURE_WORDS)
        and not any(mark in line for mark in EXEMPT_MARKS)
    ]


def _before_after(payload: HookPayload, tool_input: ToolInput) -> tuple[str, str] | None:
    """(쓰기 전 글, 쓴 뒤 글). 꼴이 어긋나면 None."""
    response = payload.get("tool_response")
    original = response.get("originalFile") if isinstance(response, dict) else None
    if payload.get("tool_name") == "Edit":
        old, new = tool_input.get("old_string"), tool_input.get("new_string")
        if not isinstance(old, str) or not isinstance(new, str):
            return None
        if isinstance(original, str) and old and old in original:
            count = -1 if tool_input.get("replace_all") is True else 1
            return original, original.replace(old, new, count)
        return old, new
    content = tool_input.get("content")
    if not isinstance(content, str):
        return None
    return (original if isinstance(original, str) else ""), content


def context_for(payload: HookPayload) -> str | None:
    """근거 문서에 근거 표지 없는 측정 낱말 줄을 더했으면 컨텍스트 문장, 아니면 None."""
    if payload.get("tool_name") not in TOOLS:
        return None
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return None
    path = tool_input.get("file_path")
    if not isinstance(path, str) or not is_evidence_doc(path):
        return None
    texts = _before_after(payload, tool_input)
    if texts is None:
        return None
    flagged = flagged_lines(added_lines(*texts))
    if not flagged:
        return None
    shown = "\n".join(f"- {line.strip()[:LINE_WIDTH]}" for line in flagged[:SHOWN_LINES])
    return _BODY.format(lead=LEAD, count=len(flagged), lines=shown)


def main() -> int:
    payload: HookPayload = json.load(sys.stdin.buffer)
    context = context_for(payload)
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
