"""PostToolUse 훅(Write|Edit). 세션 스크래치패드의 실행 스크립트를 쓰거나 고치면, 측정 스크립트라면
`.claude/rules/probes.md` 를 Read 로 열어 따르라는 계기를 세션·에이전트마다 한 번 컨텍스트에 넣는다.

왜. 그 규칙은 `paths`(`.scratch/**/probes/**`)에 맞는 파일을 열 때만 실린다. 세션 스크래치패드는
저장소 밖이라 실리지 않고, 거기서 지은 측정 스크립트가 규칙의 첫 항목(재려는 상황의 표지 단언)을
어긴 채 근거가 됐다가 저장소로 옮기며 다시 쟀다(대기열 323, 일지 2026-10-16-68. 약 70분). 같은
빈틈을 대기열 303·307·323 이 세 자리(명세 검토 서브에이전트, 측정 브리프, 사실 조사 문단)의 문장으로
따로 처방해 회차가 합쳐지지 않았다(대기열 336). 쓰는 순간에 알리는 계기 훅이고, 막지 않는다 —
스크래치 스크립트가 다 측정은 아니고, 측정인지는 모델이 가른다(`.claude/rules/tools.md` 의 계기·막는
훅 가름).

왜 따로 등록하는가. 대기열 336 은 Write·Edit 에 이미 붙은 훅에 판정을 더할 수 있는지 먼저 보라고
했다. 이 훅 전에 Write·Edit 에 붙은 PostToolUse 등록은 넷이다. 첫 `Write|Edit` 묶음의
`hook_journal_retro`(일지 파일의 회고 계기), `hook_ruff_line_width`(ruff),
`hook_line_separators`(파일 내용)와 `Write|Edit|NotebookEdit` 묶음의 `hook_edit_during_commit`(도는
커밋. 그 뒤 PreToolUse 에서 막는 훅으로 옮겼다, 대기열 412)이고, 저마다 다른 일을 판정한다. 고친
파일의 자리를 보는 것(일지 훅은 일지 경로, ruff 훅은 조상의 ruff 설정, 커밋 훅은 체크아웃 안인지)도
그 일의 대상을 고를 뿐 스크래치패드를 보지 않는다. 그 하나에 얹으면 독스트링의 왜·못 보는 것과
페이로드 표의 사례가 두 판정으로 섞인다. 매처가 없는 PreToolUse `hook_midturn_korean` 도 Write·Edit
에 붙지만 쓰기 전이라 쓴 파일을 알릴 자리가 아니다. 값은 Write·Edit 마다 래퍼를 거친 파이썬 한 번(약
0.2초, `.claude/rules/tools.md` 의 시간 항목의 어림이고 이 훅은 재지 않았다)이다. 등록은 새 매처
묶음을 만들지 않고 첫 `Write|Edit` 묶음에 더한다.

판정. 도구가 Write·Edit 이고 `tool_input.file_path` 가 문자열이며, 경로를 `/`·`\\` 로 가른 토막에서
`claude` 토막 다음 두 토막(프로젝트, 세션) 바로 뒤가 `scratchpad` 이고(대소문자를 가리지 않는다) 그
아래 파일의 확장자가 `SCRIPT_SUFFIXES` 이면 알린다. 이 저장소의 데스크톱 앱 세션이 받는 자리는
`…\\AppData\\Local\\Temp\\claude\\<프로젝트>\\<세션>\\scratchpad` 다(이 훅을 만든 세션의 시스템
프롬프트에서 봤다).

한 번. 표지는 `tools/launch_hook.py` 의 모양이다. 임시 폴더(`tempfile.gettempdir()`) 아래
`STATE_DIR` 에 세션 ID 와 `agent_id`(서브에이전트는 컨텍스트가 따로다)의 해시로 빈 파일을 `O_EXCL`
로 만든다. 세션을 모르거나 표지를 쓰지 못하면 호출마다 알린다 — 알리지 못하는 것보다 되풀이가
낫다(래퍼와 같다).

못 보는 것:
- Bash heredoc·`>`·`sed -i` 로 쓴 스크래치 파일. 이 훅은 편집 도구에만 붙는다. 대기열 336 이 센 사건
  셋 가운데 둘이 `spec-reviewer` 의 heredoc 이었다(그 에이전트에는 Write 가 없다). 그 몫은
  `.claude/agents/spec-reviewer.md` 의 프로브 문단(대기열 303)이 든다.
- 스크립트 파일 없이 손으로 치는 명령(정리 단계의 `taskkill /F <pid>`). 대기열 307 의 사건은 이
  꼴이 아니라 측정 스크립트 안의 `subprocess` 였고(일지 2026-10-16-36 의 307 승인 문단), 그
  스크립트를 Write·Edit 로 썼다면 이 훅이 알린다. 그래서 307 의 grilling 문장은 이 훅이
  대신한다(대기열 336).
- 측정인지. 확장자가 맞으면 측정이 아닌 스크립트에도 알린다(세션마다 한 번이라 값이 작다).
- 한 번 알린 뒤의 측정 스크립트. 표지는 세션·에이전트마다 하나라, 측정이 아닌 스크립트를 먼저 써서
  알림을 "측정이 아니면 무시"로 넘긴 세션이 뒤에 쓴 측정 스크립트에는 다시 알리지 않는다. 컨텍스트
  압축이나 이어 하기로 알림 문장이 사라져도 같은 세션 ID 면 표지가 남아 알리지 않는다.
- `SCRIPT_SUFFIXES` 밖의 스크립트(확장자 없는 셸 파일, `.toml` 변이 표). 측정의 꼴이어도 지나간다.
- 데스크톱 앱 밖의 스크래치패드 자리(클라우드·리눅스 CLI). 꼴이 위와 다르면 지나간다. 보지 않았다.
- 이 문장이 서브에이전트에게 닿는지. 입력의 `agent_id` 로 표지만 가르고 같은 문장을 낸다. 재지
  않았다. 메인 세션의 모델에게 닿는지도 아직 재지 않았다(계정 주간 한도, 일지 2026-10-17-15).
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
SCRIPT_SUFFIXES = frozenset({".py", ".sh", ".bash", ".ps1", ".js", ".mjs", ".cjs", ".ts"})
STATE_DIR = "agent-os-scratch-probe-rule"
# 알림의 첫 문장. 알림이 모델에게 닿는지 잴 때 모델이 옮겼는지 볼 문구다.
LEAD = "세션 스크래치패드의 실행 스크립트를 썼다"
_BODY = (
    "{lead}. 이 스크립트가 측정 스크립트(그 결과를 보고·명세·ADR·대기열의"
    " 근거로 쓸 것)라면, 더 짓기 전에 `.claude/rules/probes.md` 를 Read 로 열어"
    " 따른다. 그 규칙은 저장소의 `.scratch/**/probes/**` 에서만 실려 여기서는"
    " 실리지 않는다. 재려는 상황이 났다는 표지의 단언, 표지 없는 회차를 측정으로"
    " 세지 않기, pid 만 보고 프로세스를 끄지 않기, 결과 한 줄(JSON)을 처음부터"
    " 갖추면 저장소로 옮길"
    " 때 다시 재지 않는다. 측정이 아니면 이 알림은 무시한다. 이 알림은 세션·"
    "에이전트마다 한 번이다."
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


def is_scratch_script(path: str) -> bool:
    """세션 스크래치패드(`…/claude/<프로젝트>/<세션>/scratchpad/` 아래)의 실행 스크립트인가."""
    parts = [part.casefold() for part in _SPLIT.split(path) if part]
    if Path(parts[-1] if parts else "").suffix not in SCRIPT_SUFFIXES:
        return False
    # 마지막 토막은 파일이라 scratchpad 자리에서 뺀다.
    return any(
        parts[index] == "claude" and parts[index + 3] == "scratchpad"
        for index in range(len(parts) - 4)
    )


def context_for(payload: HookPayload) -> str | None:
    """스크래치패드의 실행 스크립트를 쓰거나 고쳤으면 컨텍스트 문장, 아니면 None."""
    if payload.get("tool_name") not in TOOLS:
        return None
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return None
    path = tool_input.get("file_path")
    if not isinstance(path, str) or not is_scratch_script(path):
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
    따로 잡는다(`tools/launch_hook.py` 의 `claim_first_notice` 와 같다)."""
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
