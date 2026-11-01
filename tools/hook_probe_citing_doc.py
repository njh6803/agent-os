"""PostToolUse 훅(Write|Edit). 명세(`.scratch/<slug>/spec.md`), ADR(`docs/adr/`), 서브에이전트
정의(`.claude/agents/`)를 쓰거나 고치면서 프로브를 가리키는 낱말을 더했을 때, 그 근거 문장을
`.claude/rules/probes.md` 셋째 항목과 대 보라는 계기를 세션·에이전트마다 한 번 컨텍스트에 넣는다.
막지 않는다.
근거의 갈래는 `docs/agents/issue-tracker.md` 프로브와 근거 절이 원천이라 알림은 그 절을 가리킨다.

왜. 셋째 항목(해석은 양성 대조와 다른 해석을 가르는 갈래를 둔 뒤에 일반화한다)은 프로브 README 를
고칠 때만 `tools/hook_probe_conclusion.py` 가 짚는다. 그런데 프로브의 결과를 잰 상황 밖으로 넓혀
적은 문장은 README 밖에서 났다(대기열 540, 닫힌 506 이 넘긴 계기 훅 후보). design-card-build 명세는
프로브가 pnpm 을 거쳐 견준 묶음·Button 장면·빌드 CSS 를 셸 없이 띄우는 길에서도 모두 바이트까지
같았다고 적었고(대기열 540 행의 요약이고 명세의 원문이 아니다), model-plugin 티켓 04 의 `_prepare`
독스트링과 `core.md` 는 프로브가 키와 네트워크가 필요 없다는 것까지 쟀는데 "만들기는 실패할 길이
없다" 고 적어 같은 변경의 `AnthropicModels.build` 가 던지는 `PluginError` 와 어긋났다. 앞의 것은
명세에, 뒤의 것은 코드 독스트링과 규칙에 있었고 둘 다 셀프 리뷰 두 축이 잡았다(대기열 540 행이 적은
사례다. 이 훅은 그 행을 읽은 것이고 두 사례의 파일을 다시 열어 보지는 않았다). 그래서 프로브를
근거로 드는 문장을 적는 자리 가운데 명세, ADR, 서브에이전트 정의(`bug-perf-review`·`spec-reviewer`
같은 에이전트가 읽는 글)에서 짚는다. 계기 훅과 막는 훅의 가름은 `.claude/rules/tools.md` 를 따른다.
문장이 넓혔는지는 모델이 가르므로 계기다.

왜 따로 등록하는가. `hook_probe_conclusion` 은 프로브 README 의 결론과 근거의 종류를 판정한다. 이
훅은 README 밖의 글을 보고 판정(경로 셋과 더한 글의 낱말)과 알림의 몫(잰 범위 안인지)이 다르다.
하나에 얹으면 독스트링의 못 보는 것과 페이로드 표의 사례가 두 판정으로 섞이고, 세션·에이전트마다
한 번의 표지도 갈라야 한다. 표지가 하나면 README 를 먼저 고친 세션이 명세를 고칠 때 알림을 받지
못한다. `tools/hook_report.py` 도 훅 파일마다 발동을 센다. 값은 Write·Edit 마다 래퍼를 거친 파이썬
한 번(약 0.2초, `.claude/rules/tools.md` 의 시간 항목의 어림이고 이 훅은 재지 않았다)이다. 등록은 새
매처 묶음을 만들지 않고 첫 `Write|Edit` 묶음에 더한다.

판정. 도구가 Write·Edit 이고 `tool_input.file_path` 가 문자열이며, 경로를 `/`·`\\` 로 가른 토막이
다음 셋 가운데 하나이고(대소문자를 가리지 않는다), 더한 글이 프로브를 가리키는 낱말을 하나라도
들면 알린다.
- 명세: 마지막 토막이 `spec.md` 이고 그 두 토막 앞이 `.scratch` 다(`.scratch/<slug>/spec.md`).
- ADR: 마지막 토막이 `.md` 로 끝나고 `README.md` 가 아니며, 그 앞 토막이 `adr`, 그 앞이 `docs` 다.
  `docs/adr/README.md` 는 ADR 제목의 색인이라 뺀다.
- 서브에이전트 정의: 마지막 토막이 `.md` 로 끝나고 그 앞 토막이 `agents`, 그 앞이 `.claude` 다.
루트를 모르고 토막만 보므로 `.claude/worktrees/<이름>/` 아래의 사본도 든다.
더한 글은 Edit 의 `new_string`, Write 의 `content` 다. 낱말은 `probes/`, `프로브`, `탐침`
이다(대소문자를 가리지 않는다). 낱말을 요구하는 까닭은 표지가 세션·에이전트마다 하나라서다. 프로브와
상관없는 명세 편집이 그 한 번을 쓰면 뒤에 프로브를 드는 편집에는 알리지 못한다.

한 번. 표지는 `tools/launch_hook.py` 의 모양이다. 임시 폴더(`tempfile.gettempdir()`) 아래
`STATE_DIR` 에 세션 ID 와 `agent_id`(서브에이전트는 컨텍스트가 따로다)의 해시로 빈 파일을 `O_EXCL`
로 만든다. 세션을 모르거나 표지를 쓰지 못하면 호출마다 알린다 — 알리지 못하는 것보다 되풀이가
낫다(래퍼와 같다).

못 보는 것:
- Bash heredoc·`>`·`sed -i` 로 고친 글. 이 훅은 편집 도구에만 붙는다.
- 프로브를 가리키는 낱말 없이 결과만 옮긴 문장. 대기열 540 의 첫 사례처럼 셸 없이 띄우는 길에서도
  같았다고만 적고 프로브 파일 이름이 없으면 알리지 못한다. 낱말을 요구한 값이다.
- 위 셋이 아닌 글. 같은 사례가 코드 독스트링(`_prepare`)과 `.claude/rules/` 에도 있었지만 코드와
  규칙의 편집에는 알리지 않는다. 티켓(`.scratch/<slug>/issues/`)과 일지도 뺐다. 일지는
  `hook_journal_evidence` 가, 프로브 README 는 `hook_probe_conclusion` 이 맡는다.
- 문장이 잰 범위를 넘었는지. 낱말이 있으면 프로브를 잰 범위 안에서 그대로 옮긴 편집에도 알린다.
  대조는 모델이 한다.
- 안 바뀐 기존 낱말. Write 의 `content` 와 앵커가 긴 Edit 의 `new_string` 은 고치지 않은 줄도
  담는다. 프로브 낱말이 이미 든 문서를 그렇게 고치면 프로브와 상관없는 편집에도 알리고 그 한 번을
  쓴다. `old_string` 이나 기존 파일과 견주지 않는다(거짓 양성).
- 지운 글. Edit 의 `old_string` 은 보지 않는다. 프로브를 가리키는 문장이 이미 있는 줄을 프로브
  낱말 없이 다시 쓴 편집에는 알리지 않는다.
- 한 번 알린 뒤의 문장. 표지는 세션·에이전트마다 하나라, 같은 세션의 뒤 편집에는 다시 알리지 않는다.
  컨텍스트 압축이나 이어 하기로 알림 문장이 사라져도 같은 세션 ID 면 표지가 남아 알리지 않는다.
- 이 문장이 모델에게 닿는지. 서브에이전트는 입력의 `agent_id` 로 표지만 가르고 같은 문장을 낸다.
  메인 세션과 서브에이전트 모두 재지 않았다(`hook_probe_conclusion` 과 같다).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import TypedDict

TOOLS = ("Write", "Edit")
STATE_DIR = "agent-os-probe-citing-doc"
SCRATCH = ".scratch"
SPEC = "spec.md"
README = "readme.md"
CUES = ("probes/", "프로브", "탐침")
# 알림의 첫 문장. 알림이 모델에게 닿는지 잴 때 모델이 옮겼는지 볼 문구다.
LEAD = "프로브를 근거로 드는 문서를 고쳤다"
_BODY = (
    "{lead}. 이 편집이 프로브의 결과를 근거로 든 문장(무엇이 같았다, 어떻게 된다, 그럴 길이 없다)을"
    " 적거나 고쳤다면, 문장마다 그 프로브의 README 행과 대 본다. 프로브가 잰 실행 위치, 입력,"
    " 판, 길(어떤 명령으로 띄웠는지, 몇 갈래를 넣었는지) 안에서 한 말인가. 한 길에서 잰 것을 모든"
    ' 길로, 잰 부분 집합에서 "모두"·"항상"·"~할 길이 없다"로 넓혔다면'
    " `.claude/rules/probes.md` 셋째 항목이 말하는 양성 대조와 다른 해석을 가르는 갈래가 없는"
    " 것이다. 그때는 문장을 잰 범위로 좁히거나, 갈래를 더해 다시 재거나, 어림이라고 적는다."
    " 프로브가 재지 않은 길을 코드에서 읽을 수 있다면 그 길은 읽었다고 파일과 함께 적는다."
    " 근거의 종류와 사례 전체는"
    " `docs/agents/issue-tracker.md` 프로브와 근거 절이다. 그 규칙 파일은 프로브 폴더의 파일을"
    " 열 때 실리므로 이 편집에서는 실려 있지 않을 수 있다. 필요하면 Read 로 연다."
    " 프로브의 결과를 옮기지 않은 편집이면 이"
    " 알림은 무시한다. 이 알림은 세션·에이전트마다 한 번이다."
)
_SPLIT = re.compile(r"[\\/]+")


class ToolInput(TypedDict, total=False):
    file_path: object
    old_string: object
    new_string: object
    content: object


class HookPayload(TypedDict, total=False):
    """Claude Code 가 stdin 으로 주는 훅 입력 중 이 훅이 읽는 부분. `tool_input` 은 객체가 아닌 값이
    와도 `context_for` 가 런타임에 다시 본다."""

    tool_name: str
    tool_input: ToolInput
    session_id: str
    agent_id: str


def is_citing_doc(path: str) -> bool:
    """프로브를 근거로 들 수 있는 문서(명세, ADR, 서브에이전트 정의)의 경로인가."""
    parts = [part.casefold() for part in _SPLIT.split(path) if part]
    if not parts:
        return False
    name = parts[-1]
    if name == SPEC and len(parts) >= 3 and parts[-3] == SCRATCH:
        return True
    if not name.endswith(".md") or len(parts) < 3:
        return False
    parent, grandparent = parts[-2], parts[-3]
    if parent == "adr" and grandparent == "docs":
        return name != README
    return parent == "agents" and grandparent == ".claude"


def added_text(tool_input: ToolInput) -> str:
    """이 편집이 더한 글. Edit 은 `new_string`, Write 는 `content` 이고 문자열이 아니면 빈
    글이다."""
    for key in ("new_string", "content"):
        value = tool_input.get(key)
        if isinstance(value, str):
            return value
    return ""


def cites_probe(text: str) -> bool:
    """프로브를 가리키는 낱말이 하나라도 있는가."""
    folded = text.casefold()
    return any(cue in folded for cue in CUES)


def context_for(payload: HookPayload) -> str | None:
    """프로브를 드는 문서를 쓰거나 고쳤으면 컨텍스트 문장, 아니면 None."""
    if payload.get("tool_name") not in TOOLS:
        return None
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return None
    path = tool_input.get("file_path")
    if not isinstance(path, str) or not is_citing_doc(path):
        return None
    if not cites_probe(added_text(tool_input)):
        return None
    return _BODY.format(lead=LEAD)


def marker_name(session_id: str, agent_id: str) -> str:
    """세션·에이전트 하나의 표지 파일 이름. 둘의 해시다(`tools/launch_hook.py` 의 모양)."""
    joined = f"{session_id}\0{agent_id}"
    return hashlib.sha256(joined.encode("utf-8", "surrogatepass")).hexdigest()


def claim_first(name: str, directory: Path) -> bool:
    """`directory` 에 표지 `name` 을 이 호출이 처음 만들었으면 True, 이미 있으면 False. 만들지
    못하면 True 다. `O_EXCL` 생성 하나가 묻기와 기록을 겸해, 병렬 호출 둘이 함께 처음이라고 보지
    않는다. 폴더 자리의 파일은 makedirs 가 FileExistsError 로 알리므로 표지가 이미 있는 것과
    따로 잡는다(`tools/hook_probe_conclusion.py` 의 `claim_first` 와 같다)."""
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
