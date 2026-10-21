"""PostToolUse 훅(Write|Edit). 프로브 README(`.scratch/**/probes/**/README.md`)를 쓰거나 고치면,
그 행의 결론마다 `.claude/rules/probes.md` 셋째 항목(양성 대조와 다른 해석을 가르는 갈래)을 대
보라는 계기를 세션·에이전트마다 한 번 컨텍스트에 넣는다.

왜. 셋째 항목을 어긴 결론이 세 번 리뷰에서야 잡혔다(대기열 346, 닫힌 179 의 3회차). AskUserQuestion
에서만 잰 차례를 PreToolUse 계기 전부로 일반화한 것은 셀프 리뷰가, 허락 요청이 훅을 기다린다는
해석과 훅이 더 빨랐다는 해석을 가르는 갈래가 없던 것은 PR 직전 `bug-perf-review` 가 잡았고(일지
2026-10-19-04), 프로젝트 설정을 읽었다는 양성 대조 없이 "먹지 않는다" 를 적은 것은 PR 봇이
잡았다(일지 2026-10-20-17). 그 규칙은 `paths` 에 맞는 파일을 열 때 실리지만, 결론은 측정이 끝난
뒤 README 행에 적는다. 결론을 적는 자리에서 그 항목을 짚는 계기 훅이고, 막지 않는다 — 고친 것이
결론인지, 대조와 갈래가 있는지는 모델이 가른다(`.claude/rules/tools.md` 의 계기·막는 훅 가름).

왜 따로 등록하는가. 같은 규칙 파일의 계기인 `hook_scratch_probe_rule` 은 세션 스크래치패드의 실행
스크립트를 판정한다. 그 하나에 얹으면 독스트링의 왜·못 보는 것과 페이로드 표의 사례가 두 판정으로
섞이고, 표지도 판정마다 따로 있어야 한다. 그리고 `tools/hook_report.py` 는 훅 파일마다 발동을
세므로, 따로 두어야 이 계기가 창 안에서 알렸는지를 그 보고의 뺄 후보로 따로 가를 수 있다. 값은
Write·Edit 마다 래퍼를 거친 파이썬 한 번(약 0.2초, `.claude/rules/tools.md` 의 시간 항목의 어림이고
이 훅은 재지 않았다)이다. 등록은 새 매처 묶음을 만들지 않고 첫 `Write|Edit` 묶음에 더한다.

판정. 도구가 Write·Edit 이고 `tool_input.file_path` 가 문자열이며, 경로를 `/`·`\\` 로 가른 토막의
마지막이 `README.md` 이고, 그 앞 토막에 `.scratch` 가 있고 그 뒤에 `probes` 가 있으면
알린다(대소문자를 가리지 않는다). `.claude/rules/probes.md` 의 `paths`(`.scratch/**/probes/**`)가
잡는 README 를 모두 들고, 여러 파일로 된 프로브가 제 폴더에 둔
README(`.scratch/harness/probes/session_cost/README.md`)도 든다. 저장소 루트를 모르고 토막만 보므로
그 `paths` 보다 넓다. 루트가 아닌 자리의 `.scratch`(`docs/.scratch/x/probes/README.md`)에도 알린다.

한 번. 표지는 `tools/launch_hook.py` 의 모양이다. 임시 폴더(`tempfile.gettempdir()`) 아래
`STATE_DIR` 에 세션 ID 와 `agent_id`(서브에이전트는 컨텍스트가 따로다)의 해시로 빈 파일을 `O_EXCL`
로 만든다. 세션을 모르거나 표지를 쓰지 못하면 호출마다 알린다 — 알리지 못하는 것보다 되풀이가
낫다(래퍼와 같다).

못 보는 것:
- Bash heredoc·`>`·`sed -i` 로 고친 README. 이 훅은 편집 도구에만 붙는다.
- README 밖에 적은 결론. 근거 문장은 rules·ADR·명세·프로브 독스트링에도 적히고, 그 편집에는 알리지
  않는다.
- 결론인지. 경로가 맞으면 결론이 아닌 편집(변이 수만 고친 행)에도 알린다(세션마다 한 번이라 값이
  작다).
- 한 번 알린 뒤의 결론. 표지는 세션·에이전트마다 하나라, 결론이 아닌 편집으로 알림을 넘긴 세션이
  뒤에 적은 결론에는 다시 알리지 않는다. 다른 프로브의 README 여도 같다. 컨텍스트 압축이나 이어
  하기로 알림 문장이 사라져도 같은 세션 ID 면 표지가 남아 알리지 않는다.
- 결론의 내용. 대조와 갈래가 있는지는 판정하지 않는다.
- 이 문장이 모델에게 닿는지. 서브에이전트는 입력의 `agent_id` 로 표지만 가르고 같은 문장을 낸다.
  메인 세션과 서브에이전트 모두 재지 않았다(`hook_scratch_probe_rule` 과 같다).
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
STATE_DIR = "agent-os-probe-conclusion"
README = "readme.md"
SCRATCH = ".scratch"
PROBES = "probes"
# 알림의 첫 문장. 알림이 모델에게 닿는지 잴 때 모델이 옮겼는지 볼 문구다.
LEAD = "프로브 README 를 고쳤다"
_BODY = (
    "{lead}. 이 편집이 결론(무엇을 쟀고 무엇이 섰는지)을 적거나 고쳤다면, 결론마다"
    " `.claude/rules/probes.md` 셋째 항목을 대 본다. 그 해석이 맞으면 나올 결과가 실제로"
    " 나왔다는 양성 대조가 있는가, 같은 관찰을 설명하는 다른 해석을 가르는 갈래가 있는가."
    " 잰 상황 밖으로 넓힌 일반화(한 도구에서 잰 차례를 모든 도구로)도 같다. 둘 가운데"
    " 하나라도 없으면 갈래를 더해 다시 재거나 그 결론을 어림이라고 적는다. 결론을 건드리지"
    " 않은 편집이면 이 알림은 무시한다. 이 알림은 세션·에이전트마다 한 번이다."
)
_SPLIT = re.compile(r"[\\/]+")


class ToolInput(TypedDict, total=False):
    file_path: object


class HookPayload(TypedDict, total=False):
    """Claude Code 가 stdin 으로 주는 훅 입력 중 이 훅이 읽는 부분. `tool_input` 은 객체가 아닌 값이
    와도 `context_for` 가 런타임에 다시 본다."""

    tool_name: str
    tool_input: ToolInput
    session_id: str
    agent_id: str


def is_probe_readme(path: str) -> bool:
    """`.scratch` 토막 뒤의 `probes` 토막 아래에 있는 `README.md` 인가."""
    parts = [part.casefold() for part in _SPLIT.split(path) if part]
    if not parts or parts[-1] != README:
        return False
    folders = parts[:-1]
    return SCRATCH in folders and PROBES in folders[folders.index(SCRATCH) + 1 :]


def context_for(payload: HookPayload) -> str | None:
    """프로브 README 를 쓰거나 고쳤으면 컨텍스트 문장, 아니면 None."""
    if payload.get("tool_name") not in TOOLS:
        return None
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return None
    path = tool_input.get("file_path")
    if not isinstance(path, str) or not is_probe_readme(path):
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
    따로 잡는다(`tools/hook_scratch_probe_rule.py` 의 `claim_first` 와 같다)."""
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
