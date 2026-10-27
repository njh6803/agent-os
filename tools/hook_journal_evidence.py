"""PostToolUse 훅(Write|Edit). 일지(`docs/journal/<이름>.md`)를 쓰거나 고치면, 결과를 적은 문장마다
근거의 종류(탐침이 단언하거나 찍은 것, 손으로 본 것과 그 명령, 코드를 읽은 것, 어림)를 밝히고
문서에서 읽은 것은 그 문서를 출처로 적으라는 계기를 세션·에이전트마다 한 번 컨텍스트에 넣는다.
근거의 갈래는 `docs/agents/issue-tracker.md` 프로브와 근거 절이 원천이라 알림은 그 절을 가리킨다.

왜. 프로브 README 의 계기(`tools/hook_probe_conclusion.py`, 대기열 421)가 선 뒤에도 일지가 보지 않은
것을 본 것처럼 적었다(대기열 445, 421 부터 세어 9~11회차). 일지 2026-10-23-27 의 단계 줄이 Design
형식 지침의 문장 "테마 메뉴에 hex가 보인다" 를 캔버스를 렌더하지 않은 채 관찰처럼 적었고, 같은
세션의 `design/README.md` 초안은 대 보지 않은 "그린 뒤에 main에 들어와" 를 적었다. 둘 다 프로브
README 밖이라 그 계기가 닿지 않았다. 일지는 단계마다 결과를 적는 자리라, 그 자리에서 짚는 계기
훅이고 막지 않는다 — 고친 것이 결과 문장인지, 근거를 밝혔는지는 모델이
가른다(`.claude/rules/tools.md` 의 계기·막는 훅 가름).

왜 따로 등록하는가. 프로브 README 계기의 판정을 넓히면 독스트링의 왜·못 보는 것과 페이로드 표의
사례가 두 경로로 섞이고, 알림 문장도 경로마다 달라야 한다(일지에는 양성 대조와 갈래를 짚을 까닭이
없다). 그리고 `tools/hook_report.py` 는 훅 파일마다 발동을 세므로, 따로 두어야 이 계기가 창 안에서
알렸는지를 그 보고의 뺄 후보로 따로 가를 수 있다. 표지 폴더도 따로라, 같은 세션에서 한 계기가 뜬
것이 다른 계기를 끄지 않는다. 값은 Write·Edit 마다 래퍼를 거친 파이썬 한 번(약 0.2초,
`.claude/rules/tools.md` 의 시간 항목의 어림이고 이 훅은 재지 않았다)이다. 등록은 새 매처 묶음을
만들지 않고 첫 `Write|Edit` 묶음에 더한다.

판정. 도구가 Write·Edit 이고 `tool_input.file_path` 가 문자열이며, 경로의 마지막 세 토막이
`docs`·`journal`·`<이름>.md` 이면 알린다. `tools/hook_journal_retro.py` 의 `is_journal` 과 같은
뜻이다 (훅은 서로 import 하지 않는다, `.claude/rules/tools.md`).

한 번. 표지는 `tools/launch_hook.py` 의 모양이다. 임시 폴더(`tempfile.gettempdir()`) 아래
`STATE_DIR` 에 세션 ID 와 `agent_id`(서브에이전트는 컨텍스트가 따로다)의 해시로 빈 파일을 `O_EXCL`
로 만든다. 세션을 모르거나 표지를 쓰지 못하면 호출마다 알린다 — 알리지 못하는 것보다 되풀이가
낫다(래퍼와 같다).

못 보는 것:
- Bash heredoc·`>>`·`sed -i` 로 고친 일지. 이 훅은 편집 도구에만 붙는다.
- 일지 밖에 적은 결과 문장. 대기열 445 의 둘째 사례(`design/README.md`)처럼 디자인 표·명세·ADR 에
  적은 결과에는 알리지 않는다. 프로브 README 는 `hook_probe_conclusion` 이 맡는다.
- 대소문자가 다른 경로(`Docs\\Journal`, `.MD`). `is_journal` 과 같이 대소문자를 구별해, 글자가 같은
  경로만 일지로 본다.
- 결과 문장인지. 경로가 맞으면 머리 한 줄만 쓴 새 일지에도 알린다.
- 한 번 알린 뒤의 결과 문장. 표지는 세션·에이전트마다 하나라, 세션 첫머리에 머리 한 줄로 일지를
  만들며 알림을 쓴 세션이 단계를 닫으며 적는 결과에는 다시 알리지 않는다. 그 알림은 컨텍스트에
  남아 있다고 기대한다. 컨텍스트 압축이나 이어 하기로 문장이 사라져도 같은 세션 ID 면 표지가 남는다.
- 결과 문장의 내용. 근거의 종류를 밝혔는지는 판정하지 않는다. 이미 밝힌 편집에도 알린다.
- 이 문장이 모델에게 닿는지. 서브에이전트는 입력의 `agent_id` 로 표지만 가르고 같은 문장을 낸다.
  메인 세션과 서브에이전트 모두 재지 않았다(`hook_probe_conclusion` 과 같다).
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from pathlib import Path, PurePath
from typing import TypedDict

TOOLS = ("Write", "Edit")
STATE_DIR = "agent-os-journal-evidence"
JOURNAL_PARTS = ("docs", "journal")
# 알림의 첫 문장. 알림이 모델에게 닿는지 잴 때 모델이 옮겼는지 볼 문구다.
LEAD = "일지를 고쳤다"
_BODY = (
    "{lead}. 이 편집이 결과(무엇을 했고 무엇이 됐는지, 무엇이 보였는지)를 적거나 고쳤다면 결과를"
    " 적은 문장마다 근거의 종류를 밝힌다. 탐침이 단언하거나 찍은 것인가, 손으로 본 것인가, 코드를"
    " 읽은 것인가, 어림인가. 손으로 본 것은 그 명령과 함께 적는다. 문서에서 읽은 것은 그 문서를"
    " 출처로 적는다. 지침이나 명세가 그렇다고 적은 것을 화면이나 출력에서 본 것처럼 쓰지 않는다."
    " 이 브랜치가 돌리지 않은 것, 렌더하지 않은 화면처럼 보지 않은 것을 본 것처럼 적지 않고, 보지"
    " 않았다고 적거나 어림이라고 적는다. 웹 요약까지 든 근거의 갈래 전체와 사례는"
    " `docs/agents/issue-tracker.md` 프로브와 근거 절이다. 결과를 건드리지 않은 편집이면 이 알림은"
    " 무시한다. 이 알림은 세션·에이전트마다 한 번이다."
)


class ToolInput(TypedDict, total=False):
    file_path: object


class HookPayload(TypedDict, total=False):
    """Claude Code 가 stdin 으로 주는 훅 입력 중 이 훅이 읽는 부분. `tool_input` 은 객체가 아닌 값이
    와도 `context_for` 가 런타임에 다시 본다."""

    tool_name: str
    tool_input: ToolInput
    session_id: str
    agent_id: str


def is_journal(file_path: str) -> bool:
    """docs/journal/<name>.md 인가(`tools/hook_journal_retro.py` 의 `is_journal` 과 같다)."""
    path = PurePath(file_path.replace("\\", "/"))
    parts = path.parts
    if path.suffix != ".md" or len(parts) < 3:
        return False
    return tuple(parts[-3:-1]) == JOURNAL_PARTS


def context_for(payload: HookPayload) -> str | None:
    """일지를 쓰거나 고쳤으면 컨텍스트 문장, 아니면 None."""
    if payload.get("tool_name") not in TOOLS:
        return None
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return None
    path = tool_input.get("file_path")
    if not isinstance(path, str) or not is_journal(path):
        return None
    return _BODY.format(lead=LEAD)


def marker_name(session_id: str, agent_id: str) -> str:
    """세션·에이전트 하나의 표지 파일 이름. 둘의 해시다(`tools/launch_hook.py` 의 모양)."""
    joined = f"{session_id}\0{agent_id}"
    return hashlib.sha256(joined.encode("utf-8", "surrogatepass")).hexdigest()


def claim_first(name: str, directory: Path) -> bool:
    """`directory` 에 표지 `name` 을 이 호출이 처음 만들었으면 True, 이미 있으면 False. 만들지
    못하면 True 다(`tools/hook_probe_conclusion.py` 의 `claim_first` 와 같다)."""
    try:
        os.makedirs(directory, exist_ok=True)
    except OSError:
        return True
    try:
        os.close(os.open(directory / name, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
    except FileExistsError:
        return False
    except OSError:
        return True
    return True


def main() -> int:
    payload: HookPayload = json.load(sys.stdin.buffer)
    context = context_for(payload)
    if context is None:
        return 0
    session = payload.get("session_id")
    agent = payload.get("agent_id")
    if isinstance(session, str) and session:
        name = marker_name(session, agent if isinstance(agent, str) else "")
        try:
            directory = Path(tempfile.gettempdir()) / STATE_DIR
        except OSError:
            # 쓸 수 있는 임시 폴더가 없다. 표지를 쓰지 못한 것과 같이 알린다.
            directory = None
        if directory is not None and not claim_first(name, directory):
            return 0
    print(
        json.dumps(
            {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": context}}
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
