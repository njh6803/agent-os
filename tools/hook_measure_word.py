"""PostToolUse 훅(Write|Edit). 근거로 읽히는 문서(`docs/adr/`, `.scratch/**/probes/README.md`,
`.scratch/retro-queue/`와 `docs/journal/` 바로 아래의 `.md`)에 더한 줄이 측정 낱말(`쟀다`·`재니`·
`실측`)을 들면서 같은 줄에 `probes/` 경로도 `손으로`도 없으면, `docs/agents/issue-tracker.md` 의
"프로브와 근거" 절을 컨텍스트에 넣는다.

왜. 그 절은 "쟀다"·"실측"을 커밋한 프로브가 다시 내는 것에만 쓰고 그 파일을 가리키며, 손으로 돌려 본
것은 손으로 봤다고 적으라고 한다(대기열 45). 그 절이 지침이 된 뒤에도 ADR 이력에 손으로 돌린 시간
비교를 "재니"로 적었고, 셀프 리뷰 두 축이 잡은 뒤 프로브로 다시 재느라 측정을 세 번 돌았다(대기열
227 의 6회차, 일지 2026-10-13-26 외 다섯). 쓰는 순간에 알리는 계기 훅이고 막지 않는다 — 낱말이 근거
문장인지, 낱말을 이름으로 든 것인지는 모델이 가른다(`.claude/rules/tools.md` 의 계기·막는 훅 가름).

일지를 범위에 더한 까닭. 227 이 처음 고른 자리는 ADR·프로브 README·대기열이라 일지에는 닿지 않았다.
그 뒤 일지에 손으로 돌린 스크래치 스크립트(`yaml_probe.py`)로 본 것을 "쟀다"로 적었고 셀프 리뷰
표준 축이 Nit으로 잡았다(대기열 558, 227 의 7회차, 일지 2026-11-03-02). 일지 계기인
`hook_journal_evidence` 는 세션·에이전트마다 한 번이라 문장마다 짚지 못한다.

왜 따로 등록하는가. Write·Edit 의 다른 PostToolUse 훅은 저마다 다른 일을 판정한다(일지 회고 계기,
ruff, 줄 구분 문자, 스크래치 스크립트, 프로브 결론, 일지 근거, 디자인 폴더, 화면 코드, 도는 변이.
`.claude/settings.json` 의 첫 `Write|Edit` 묶음과 `Write|Edit|NotebookEdit` 묶음). 여기에 얹으면
독스트링의 왜·못 보는 것과 페이로드 표의 사례가 두 판정으로 섞인다. 등록은 첫 `Write|Edit` 묶음에
더한다. 값은 Write·Edit 마다 래퍼를 거친 파이썬 한 번이다(약 0.2초, 이 훅은 재지 않았고
`.claude/rules/tools.md` 시간 항목의 어림이다).

프로브 README 와 `hook_probe_conclusion`. 그 훅은 프로브 README 를 고치면 근거의 종류를 같은 절로
짚는다(대기열 421). 그래서 측정 낱말을 든 줄을 `probes/` 바로 아래 README 에 더한 편집에는 두
알림이 함께 날 수 있다. 그 훅은 세션·에이전트마다 한 번 알리므로(세션을 모르거나 표지를 쓰지 못하면
호출마다, 그 독스트링의 한 번 절) 겹침은 많아야 그 한 번이고, 측정 낱말 없는 편집이 그 한 번을 먼저
쓰면 겹침은 없다. 그 뒤의 편집은 이 훅만 알린다. 그 훅의 못 보는 것("한 번 알린 뒤의 결과와
결론")을 이 훅이 낱말이 든 줄만큼 메우므로 프로브 README 를 범위에서 빼지 않는다(대기열 227 행이
반영할 때 보라고 적은 겹침, 2026-10-28). 같은 까닭으로 알림의 무시 조건도 프로브 README 행의 첫 칸에
프로브가 있다는 것만으로는 무시하지 않고, 그 줄의 결과를 그 프로브가 다시 낼 때만 무시하게 적는다.
하위 폴더의 README 는 그 훅만 알린다(못 보는 것).

일지와 `hook_journal_evidence`. 그 훅은 일지를 Write·Edit 하면 결과 문장의 근거 종류를 같은 절로
짚는다(대기열 445). 그래서 측정 낱말을 든 줄을 일지에 더한 편집에는 두 알림이 함께 날 수 있다. 그
훅은 세션·에이전트를 알면 그 한 번만 알리므로, 세션을 아는 호출에서 겹침은 많아야 그 한 번이고,
낱말 없는 편집이 그 한 번을 먼저 쓰면 겹침은 없다. 그 뒤의 편집은 이 훅만 알린다. 세션을 모르는
페이로드(`session_id` 없음)에서는 그 훅이 호출마다 알려 겹침도 호출마다 난다. 두 훅의 경로 판정도
다르다. 이 훅은 대소문자를 가리지 않고(`docs/Journal/x.md`, `x.MD` 도 받는다), 그 훅은 소문자
`docs/journal/<이름>.md` 만 받아서 대문자 경로의 편집은 이 훅만 알린다. 그 훅의 못 보는
것("한 번 알린 뒤의 결과 문장")을 이 훅이 낱말이 든 줄만큼 메운다(대기열 558 이 반영할 때 보라고
적은 겹침). 두 훅은 서로 다른 일을 판정하므로 합치지 않는다. 일지는 `> 사용자:` 인용으로 프롬프트
원문을 싣고 그 줄이 낱말을 들면 걸린다. 알림이 그 인용은 이름으로 든 것으로 읽어 무시하라고
적는다.

판정. 도구가 Write·Edit 이고 `tool_input.file_path` 가 문자열이며 `is_evidence_doc` 이 참이면, 더한
줄(`added_lines`)마다 `MEASURE_WORDS` 가운데 하나가 들고 `EXEMPT_MARKS` 는 하나도 없는 줄을 고른다.
더한 줄은 쓰기 전 파일에 없던 쓴 뒤 파일의 줄이다. 쓰기 전 파일은 결과의 `originalFile` 이다(덮어쓴
Write 와 Edit 에서 문자열이고, 새 파일을 만든 Write 에서는 null 이다. 프로브 README 의
`journal_number_hook/` 행의 2026-10-16 결과). 쓴 뒤 파일은 Write 면 `content`, Edit 면
`originalFile` 에서 `old_string` 을 `new_string` 으로 바꾼 글이다(`replace_all` 이 참이면 모두,
아니면 처음 하나). Edit 의 조각은 줄의 일부일 수 있어, 조각만 보면 같은 줄의 나머지에 든 `probes/`
를 보지 못한다(셀프 리뷰가 잡았다, 일지 2026-10-28-07). `originalFile` 이 문자열이 아니거나
`old_string` 이 그 안에 없는 Edit 은 조각 둘을 쓰기 전·뒤 글로 본다. 줄 집합의 차라 순서와 횟수는
보지 않는다. 걸린 줄은 앞의 `SHOWN_LINES` 개를 `LINE_WIDTH` 글자로 잘라 문장에 싣는다.

한 번이 아니다. 형제 훅(`hook_scratch_probe_rule`)과 달리 표지를 두지 않고 걸릴 때마다 알린다.
알림이 걸린 줄을 보여 주므로, 앞의 알림을 "인용일 뿐"으로 넘긴 세션도 뒤의 근거 문장에서 다시 본다.

못 보는 것:
- 다른 꼴의 측정 낱말(`잰`, `재 보니`, `측정했다`). 대기열 227 이 고른 셋만 본다.
- 낱말을 이름으로만 든 줄(대기열 항목이 "`쟀다`·`실측`을 든 줄"이라고 적은 것). 근거 문장과 가르지
  않고 알린다.
- 옛 줄을 고쳐 쓴 것. 줄의 다른 자리만 고쳐도(대기열 항목의 상태 줄을 `열림`에서 `닫힘 (…)`으로
  고치는 것) 쓴 뒤 파일에서는 그 줄 전체가 새 줄이라, 그 줄이 이미 들고 있던 낱말이 다시 걸린다.
  알림이 이 경우는 무시하라고 적는다. `originalFile` 이 없는 Edit 은 조각만 보므로 거꾸로 낱말이
  조각 밖에 있으면 지나간다.
- 근거가 같은 줄 밖에 있는 문장. 줄을 바꿔 `probes/` 를 적은 감긴 문단도, 프로브를 첫 칸에 파일
  이름으로만 드는 프로브 README 의 행도 알린다. 알림이 그 줄의 결과를 같은 줄 밖의 프로브가 다시
  내면 무시하라고 적는다. 그 결과를 프로브가 냈는지 손으로 봤는지는 모델이 가른다.
- `probes/` 를 들기만 하고 그 파일이 낱말의 근거인지, `손으로` 가 부정문인지("손으로 보지 않고
  실측했다"). 같은 줄에 그 문자열이 있으면 지나간다.
- 정규화하지 않은 경로(`docs/./adr/`, `..`). 토막을 그대로 견준다. 거꾸로 `docs/adr` 토막은 어느
  깊이에 있든, 확장자가 무엇이든 받고, `.scratch` 토막도 어느 깊이에 있든
  받는다(`web/.scratch/retro-queue/0573.md`). 대기열 폴더와 일지 폴더는 바로 아래의 `.md` 만
  본다. 하위 폴더, `.md` 가 아닌 파일, 비슷한 이름의 폴더(`.scratch/retro-queue-x/`,
  `docs/journals/`), 이행 전의 표 파일 `.scratch/retro-queue.md` 는 지나간다. 일지 폴더는 앞
  토막의 깊이를 가리지 않아 `agent/docs/journal/x.md` 도 받는다(`docs/agents/journal/x.md` 는 마지막
  두 폴더가 `agents`·`journal` 이라 지나간다).
- `probes/` 아래 하위 폴더의 README(`.scratch/harness/probes/session_cost/README.md`). 대기열 227 이
  고른 `.scratch/**/probes/README.md` 꼴만 본다. 그 README 는 `hook_probe_conclusion` 만 알린다.
- Bash heredoc·`>>`·`sed -i` 로 쓴 문서. 이 훅은 편집 도구에만 붙는다. Bash 로 쓴 일지는
  `hook_journal_evidence` 의 Bash 묶음이 결과 문장 계기를 낼 뿐, 측정 낱말 줄은 짚지 않는다.
- 네 자리 밖의 근거 글(명세, 코드 주석, `.claude/rules/`). 대기열 227 의 "어디로" 칸이 고른 셋과
  대기열 558 이 더한 일지만 본다.
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
    "다음 셋이면 고치지 않고 이 알림은 무시한다. 낱말을 이름으로 든 것뿐이다"
    "(일지의 `> 사용자:` 인용 포함). 이미 있던 줄의 다른 자리만 고쳤다(상태 줄을 열림에서 "
    "닫힘으로 고친 것). 그 줄의 결과를 같은 줄 밖(감긴 문단의 앞뒤 줄, 프로브 README 행의 첫 "
    "칸)의 커밋한 프로브가 다시 낸다. 프로브 README 의 행이어도 손으로 본 결과를 측정 낱말로 "
    "적었으면 무시하지 않는다. 걸린 줄({count}개):\n{lines}"
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
    """`docs/adr/` 아래 파일, `.scratch/` 아래의 `probes/README.md`, `.scratch/retro-queue/`와
    `docs/journal/` 바로 아래의 `.md`(하위 폴더 없이 직계)인가."""
    parts = [part.casefold() for part in _SPLIT.split(path) if part]
    if len(parts) < 2:
        return False
    *folders, name = parts
    if any(folders[index : index + 2] == ["docs", "adr"] for index in range(len(folders) - 1)):
        return True
    if folders[-2:] == [".scratch", "retro-queue"] and name.endswith(".md"):
        return True
    if folders[-2:] == ["docs", "journal"] and name.endswith(".md"):
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
