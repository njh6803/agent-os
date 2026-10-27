"""PostToolUse 훅(Write|Edit). 세션이 화면 코드(`web/packages/ui/` 아래나 `web/apps/<앱>/` 아래
파일)를 처음 고치면, 디자인 시스템 아티팩트에 웹 편집이 있을 수 있으니 화면을 더 고치기 전에
`/sync-design-system` 의 확인을 부르라는 계기를 세션·에이전트마다 한 번 컨텍스트에 넣는다.

왜. 디자인 시스템의 원천은 코드이고 Claude 아티팩트의 디자인 시스템은 그 사본이다. 편집을 켜면
사람이 웹에서 그 사본을 고칠 수 있는데, 사람이 알리지 않은 웹 편집을 모른 채 화면을 고치면 그 화면
작업이 옛 코드 값으로 이어진다. 그래서 알리지 않은 웹 편집은 셋이 찾는다. 이 훅, `/ui-design` 의
그리기 전 단계, 올리기의 첫 단계다(ADR 0025 이력 2026-10-21 의 "계기", 명세
`.scratch/design-reverse-sync/spec.md` 의 "계기 훅"). 디자인 시스템 패키지뿐 아니라 앱 화면을 고치는
일도 확인한다. 이 훅은 회고가 대기열에서 더한 훅이 아니라 사용자가 설계 인터뷰에서 정한 것이라 ADR
0036 의 더하는 문턱을 거치지 않는다(같은 이력). 쓰는 순간에 알리는 계기 훅이고 막지 않는다. 알림은
첫 쓰기 뒤에 닿는다. PreToolUse 로 걸어도 계기의 알림은 그 호출의 결과와 함께 닿아 첫 쓰기를 앞서지
못하고, 앞서려면 막는 훅이어야 한다(`.claude/rules/tools.md` 의 PreToolUse 계기 항목). 한 응답에
Write·Edit 를 나란히 여럿 보내면 알림은 그 쓰기가 모두 끝난 뒤에 닿는다(모델은 나란히 보낸 호출의
결과를 함께 받는다. 재지 않은 어림이다). 그래서 문장은 방금 고친 파일은 그대로 두라고 한다. 이 훅이
병합된 뒤 디자인 시스템 아티팩트의 편집을 켜기 전까지(design-reverse-sync 티켓 10)는 찾을 웹 편집이
없어 쓸모없는 알림이 난다(명세가 받아들였다).

왜 따로 등록하는가. 대기열 336 은 Write·Edit 에 이미 붙은 훅에 판정을 더할 수 있는지 먼저 보라고
했다. 이 훅 전에 Write·Edit 의 PostToolUse 에 붙은 훅은 여덟이다. 첫 `Write|Edit` 묶음의 일곱
(`hook_journal_retro`, `hook_ruff_line_width`, `hook_line_separators`, `hook_scratch_probe_rule`,
`hook_probe_conclusion`, `hook_journal_evidence`, `hook_ui_design`)과 `Write|Edit|NotebookEdit`
묶음의 `hook_edit_during_mutate` 다. 가장 가까운 둘도 판정과 문장이 다르다. `hook_ui_design` 은
경로를 보고 스킬을 부르라고 한 번 알리지만, 경로가 기능의 디자인 폴더이고 부를 스킬이 `/ui-design`
이며 브랜치를 보지 않는다. `hook_edit_during_mutate` 는 이 훅처럼 고친 파일의 경로에서 체크아웃과
git 디렉터리를 찾지만, 판정은 변이 도구의 표지이고 한 번이 아니라 편집마다 알린다. 하나에 얹으면
독스트링의 왜·못 보는 것과 페이로드 표의 사례가 두 판정으로 섞인다(`hook_scratch_probe_rule` 의 같은
판단). 등록은 새 매처 묶음을 만들지 않고 첫 `Write|Edit` 묶음에 더한다. 값은 Write·Edit 마다 래퍼를
거친 파이썬 한 번이다. 경로가 맞을 때만 표지 파일 하나를 만들고, 그 표지가 처음일 때만 작업 트리의
`.git`·`HEAD` 와 티켓 파일 하나를 본다. git 을 띄우지 않는다. 시간은 재지 않았고 다른 계기 훅과 같은
약 0.2초로 어림한다(`.claude/rules/tools.md` 의 시간 항목).

판정. 경로, 표지, 브랜치 차례로 본다.
- 경로. 도구가 Write·Edit 이고 `tool_input.file_path` 가 문자열이며, `.`·`..` 토막을 접은
  뒤(`posixpath.normpath`) `/`·`\\` 로 가른 토막에 `web`, `packages`, `ui` 가 이어지거나 `web`,
  `apps`, 앱 토막이 이어지고 그 뒤에 토막이 하나 이상 있으면 화면 코드다(대소문자를 가리지 않는다).
  `web/tools`, `web/packages/` 아래의 다른 패키지, `web/apps/README.md` 처럼 앱 토막이 파일인 경로,
  `web/packages/ui`·`web/apps/<앱>` 그 자체(그 뒤에 토막이 없는 경로)는 지나간다. 그 아래의 폴더
  경로(`web/apps/admin/src`)는 파일과 가르지 못해 화면 코드로 본다. Write·Edit 의 대상은 파일이다.
- 표지. 경로가 맞으면 브랜치를 보기 전에 표지를 만든다. 이미 있으면 그 세션·에이전트는 판정을
  마쳤으니 침묵한다. 침묵한 판정도 표지에 남으므로, 들이기 브랜치에서 침묵한 세션의 둘째 쓰기는
  다시 판정하지 않는다.
- 브랜치. 작업 트리는 고친 파일의 폴더에서 위로 올라가 처음 `.git`(디렉터리나 워크트리의 파일)이
  있는 폴더다. `CLAUDE_PROJECT_DIR` 은 워크트리 세션에서 주 체크아웃을 가리켜 쓰지 않는다
  (`.claude/rules/tools.md` 의 디렉터리 항목). 파일 경로가 상대 경로면 페이로드의 `cwd` 에서 푼다.
  브랜치는 그 git 디렉터리(`.git` 디렉터리, 또는 `.git` 파일의 `gitdir:` 가 가리키는 곳. 상대
  경로는 그 작업 트리에서 푼다)의 `HEAD` 가 `ref: refs/heads/<브랜치>` 일 때의 그 이름이다. git 처럼
  `ref:` 뒤의 공백은 넘는다. 브랜치가 `feature/<NN>-<slug>` 이고 그 작업 트리에
  `.scratch/design-reverse-sync/issues/<NN>-<slug>.md` 가 있으면 침묵한다. 들이기 세션과 이 기능의
  구현 티켓 세션이 여기에 든다(명세 "들이기 세션 자신의 쓰기"). 들이기 세션은 자기가 들이는 편집을
  다시 확인하라는 말에 흔들리지 않아야 하고(명세 스토리 25), 구현 티켓 동안은 편집이 꺼져 있어 맞댈
  웹 편집이 없다. 작업 트리나 `HEAD` 를 읽지 못하거나, 분리 HEAD 이거나, 티켓 파일이 없으면 알린다.
  침묵은 들이기 브랜치를 알아본 때뿐이다.
- 알림. `agent_id` 가 비지 않은 문자열이면 서브에이전트다(`tools/hook_payloads.toml` 의 서브에이전트
  사례). 사람에게 묻지 못하므로 확인을 하지 말고, 끝 보고 첫머리에 `SUBAGENT_REPORT` 를 적으라고
  알린다. 그 밖에는 화면을 더 고치기 전에 Skill 도구로 확인을 부르라고 알린다. 둘 다 고를 수 있는
  답을 풀어 쓰지 않고 그 스킬의 "찾았을 때" 절을 가리키기만 한다(명세 "알리는 말").
- 꼴이 어긋난 입력(JSON 이 아니다, 풀다가 재귀 한도를 넘을 만큼 깊게 중첩됐다, 객체가 아니다,
  `tool_input` 이 객체가 아니다, `file_path` 가 문자열이 아니다)은 예외 없이 침묵한다. 작업 트리의
  `.git`·`HEAD` 를 읽다 난 오류(경로에 NUL 이 든 `gitdir:` 포함)는 읽지 못한 것으로 보아 알린다.

한 번. 표지는 `tools/launch_hook.py` 의 모양이다. 임시 폴더(`tempfile.gettempdir()`) 아래
`STATE_DIR` 에 세션 ID 와 `agent_id`(서브에이전트는 컨텍스트가 따로다)의 해시로 빈 파일을 `O_EXCL`
로 만든다. 세션을 모르거나 표지를 쓰지 못하면 호출마다 판정하고 알린다 — 알리지 못하는 것보다
되풀이가 낫다(래퍼와 같다).

못 보는 것:
- Bash(`sed -i`, heredoc, `>`)로 고친 화면 파일. 이 훅은 편집 도구에만 붙는다. 올리기의 확인이 다시
  걸러, 웹 편집이 말없이 덮어써지지는 않는다(명세).
- 화면 코드의 두 자리 밖에서 화면에 닿는 파일. `web/` 밖의 서버 라우트와 `openapi.json`, `web/` 안의
  다른 패키지(`api-client` 의 위젯 몫)다.
- 침묵한 뒤 브랜치를 바꾼 세션이 고친 파일. 표지가 판정을 한 번으로 묶어, 들이기 브랜치에서 침묵한
  세션이 다른 브랜치로 옮겨 화면을 고쳐도 다시 판정하지 않는다. 올리기의 확인이 다시 거른다(명세).
- 저장소 뿌리의 `web` 인지. 경로 어디의 `web/packages/ui/`·`web/apps/<앱>/` 이든 화면 코드로 본다.
  문서 폴더 안의 같은 꼴 경로에도 알린다.
- 이미 확인을 부른 세션인지. `/ui-design` 이나 올리기가 확인을 먼저 부른 뒤 화면을 고쳐도 한 번
  알린다. 문장이 "이 세션에서 이미 그 확인을 했으면 이 알림은 무시한다"를 든다.
- 한 번 알린 뒤. 컨텍스트 압축이나 이어 하기로 알림 문장이 사라져도 같은 세션 ID 면 표지가 남아 다시
  알리지 않는다. 화면 작업이 코드 값으로 이어질 수 있지만 올리기의 확인이 다시 돈다(명세 "멈춘
  상태의 자리").
- 이 문장이 메인 세션과 서브에이전트의 모델에게 닿는지. 재지 않았다. design-reverse-sync 티켓 10 의
  사람 확인이 첫 쓰기 뒤에 실리는지와 서브에이전트에 닿는지를 본다(명세 "계기 훅"의 주석).
"""

from __future__ import annotations

import hashlib
import json
import os
import posixpath
import re
import sys
import tempfile
from pathlib import Path
from typing import TypedDict

TOOLS = ("Write", "Edit")
STATE_DIR = "agent-os-web-edit-check"
SKILL = "sync-design-system"
# 알림이 가리키는 그 스킬의 절. 시험이 스킬 파일에 이 제목이 있는지 대 본다.
FOUND_SECTION = "찾았을 때"
# 들이기 세션과 이 기능의 구현 티켓 세션을 알아보는 티켓 폴더(작업 트리 뿌리에서).
TICKETS = Path(".scratch", "design-reverse-sync", "issues")
# 알림의 첫 문장. 알림이 모델에게 닿는지 잴 때 모델이 옮겼는지 볼 문구다.
LEAD = "디자인 시스템 아티팩트에 웹 편집이 있을 수 있다"
SUBAGENT_LEAD = "서브에이전트가 `web/` 아래 화면 코드를 고쳤다"
# 서브에이전트가 끝 보고 첫머리에 적을 문장(명세 "계기 훅"의 서브에이전트).
SUBAGENT_REPORT = (
    "`web/` 아래를 고쳤다. 부모 세션이 이 세션에서 `/sync-design-system` 확인을 했는지 본다"
)
_MAIN = (
    "{lead}. 이 세션이 화면 코드(`web/packages/ui` 나 `web/apps/<앱>` 아래)를 처음 고쳤다. 방금"
    " 고친 파일은 그대로 두고, 화면을 더 고치기 전에 Skill 도구로 `{skill}` 을 인자 `확인` 으로"
    " 불러(`/{skill} 확인`) 그 순서를 따른다. 웹 편집을 찾았거나 판단할 수 없으면 그 스킬의"
    ' "{section}" 절대로 묻고 멈춘다. 이 세션에서 이미 그 확인을 했으면 이 알림은 무시한다.'
    " 이 알림은 세션·에이전트마다 한 번이다."
)
_SUBAGENT = (
    "{lead}. 디자인 시스템 아티팩트에 웹 편집이 있을 수 있지만, 서브에이전트는 사람에게 묻지"
    " 못하므로 `/{skill}` 의 확인을 하지 않는다. 맡은 일을 이어 하고, 끝 보고 첫머리에"
    ' "{report}"를 적는다. 확인과, 웹 편집을 찾았을 때 묻는 일은 부모 세션이 그 스킬의'
    ' "{section}" 절대로 한다. 이 알림은 에이전트마다 한 번이다.'
)
# 알릴 문장. 서브에이전트에는 확인 대신 끝 보고에 적을 것을 알린다.
MAIN_CONTEXT = _MAIN.format(lead=LEAD, skill=SKILL, section=FOUND_SECTION)
SUBAGENT_CONTEXT = _SUBAGENT.format(
    lead=SUBAGENT_LEAD, skill=SKILL, report=SUBAGENT_REPORT, section=FOUND_SECTION
)
_SEPARATORS = re.compile(r"[\\/]+")
_TICKET_BRANCH = re.compile(r"feature/(\d+-[^/\\]+)")
_REF = "ref:"
_HEADS = "refs/heads/"


class ToolInput(TypedDict, total=False):
    file_path: object


class HookPayload(TypedDict, total=False):
    """Claude Code 가 stdin 으로 주는 훅 입력 중 이 훅이 읽는 부분. 값의 형은 `output_for` 가
    런타임에 다시 본다."""

    tool_name: object
    tool_input: ToolInput
    session_id: object
    agent_id: object
    cwd: object


type JsonValue = HookPayload | list[object] | str | float | bool | None


def is_screen_code(path: str) -> bool:
    """`web/packages/ui/` 아래나 `web/apps/<앱>/` 아래 파일인가."""
    normalized = posixpath.normpath(_SEPARATORS.sub("/", path))
    parts = [part.casefold() for part in normalized.split("/") if part]
    # 마지막 토막은 파일이라, 그 앞에 web 과 두 토막이 있어야 한다.
    for index in range(len(parts) - 3):
        if parts[index] != "web":
            continue
        if parts[index + 1] == "apps" or parts[index + 1 : index + 3] == ["packages", "ui"]:
            return True
    return False


def screen_file(payload: HookPayload) -> str | None:
    """Write·Edit 가 화면 코드를 고쳤으면 그 파일 경로, 아니면 None."""
    if payload.get("tool_name") not in TOOLS:
        return None
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return None
    path = tool_input.get("file_path")
    if not isinstance(path, str) or not is_screen_code(path):
        return None
    return path


def checkout_of(directory: str) -> Path | None:
    """`directory` 에서 위로 올라가 처음 `.git`(디렉터리나 워크트리의 파일)이 있는 폴더. 없거나
    읽지 못하면 None."""
    try:
        current = Path(os.path.realpath(directory))
        for candidate in (current, *current.parents):
            if (candidate / ".git").exists():
                return candidate
    except (OSError, ValueError):
        return None
    return None


def _first_line(path: Path) -> str | None:
    """파일의 첫 줄(앞뒤 공백을 벗긴다). 읽지 못하면(경로에 NUL 이 든 ValueError 포함) None."""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except (OSError, ValueError):
        return None
    return lines[0].strip() if lines else ""


def git_dir_of(checkout: Path) -> Path | None:
    """그 작업 트리의 git 디렉터리. `.git` 이 디렉터리면 그것, 파일이면 `gitdir:` 줄이 가리키는
    곳(상대 경로는 그 작업 트리에서 푼다). 읽지 못하면 None."""
    dot_git = checkout / ".git"
    try:
        if dot_git.is_dir():
            return dot_git
    except OSError:
        return None
    line = _first_line(dot_git)
    if line is None or not line.startswith("gitdir:"):
        return None
    target = line.removeprefix("gitdir:").strip()
    return checkout / target if target else None


def branch_of(checkout: Path) -> str | None:
    """그 작업 트리의 브랜치. `HEAD` 가 `refs/heads/` 아래를 가리키지 않거나(분리 HEAD 등) 읽지
    못하면 None."""
    git_dir = git_dir_of(checkout)
    if git_dir is None:
        return None
    line = _first_line(git_dir / "HEAD")
    if line is None or not line.startswith(_REF):
        return None
    ref = line.removeprefix(_REF).strip()
    if not ref.startswith(_HEADS):
        return None
    return ref.removeprefix(_HEADS) or None


def is_import_session(checkout: Path, branch: str) -> bool:
    """브랜치가 `feature/<NN>-<slug>` 이고 그 작업 트리에 이 기능의 그 티켓 파일이 있는가."""
    matched = _TICKET_BRANCH.fullmatch(branch)
    if matched is None:
        return False
    try:
        return (checkout / TICKETS / f"{matched.group(1)}.md").is_file()
    except (OSError, ValueError):
        return False


def marker_name(session_id: str, agent_id: str) -> str:
    """세션·에이전트 하나의 표지 파일 이름. 둘의 해시다(`tools/launch_hook.py` 의 모양)."""
    joined = f"{session_id}\0{agent_id}"
    return hashlib.sha256(joined.encode("utf-8", "surrogatepass")).hexdigest()


def claim_first(name: str, directory: Path) -> bool:
    """`directory` 에 표지 `name` 을 이 호출이 처음 만들었으면 True, 이미 있으면 False. 만들지
    못하면 True 다. 폴더 자리의 파일은 makedirs 가 FileExistsError 로 알리므로 표지가 이미 있는 것과
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


def _absolute(path: str, cwd: object) -> str:
    """상대 경로는 페이로드의 `cwd`(없으면 이 프로세스의 작업 폴더)에서 푼다."""
    if os.path.isabs(path):
        return path
    base = cwd if isinstance(cwd, str) and cwd else os.getcwd()
    return os.path.join(base, path)


def output_for(raw: bytes, state_dir: Path | None) -> str | None:
    """훅 입력 바이트에 대한 표준 출력. 알리지 않으면 None. `state_dir` 는 표지 폴더이고, None 이면
    표지를 쓸 수 없는 것으로 보아 호출마다 판정한다."""
    try:
        payload: JsonValue = json.loads(raw)
    except (ValueError, RecursionError):
        return None
    if not isinstance(payload, dict):
        return None
    path = screen_file(payload)
    if path is None:
        return None
    session = payload.get("session_id")
    agent = payload.get("agent_id")
    agent_id = agent if isinstance(agent, str) else ""
    if isinstance(session, str) and session and state_dir is not None:
        if not claim_first(marker_name(session, agent_id), state_dir):
            return None
    checkout = checkout_of(os.path.dirname(_absolute(path, payload.get("cwd"))))
    if checkout is not None:
        branch = branch_of(checkout)
        if branch is not None and is_import_session(checkout, branch):
            return None
    context = SUBAGENT_CONTEXT if agent_id else MAIN_CONTEXT
    return json.dumps(
        {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": context}}
    )


def main() -> int:
    try:
        state_dir: Path | None = Path(tempfile.gettempdir()) / STATE_DIR
    except OSError:
        # 쓸 수 있는 임시 폴더가 없다. 표지를 쓰지 못한 것과 같이 호출마다 판정한다.
        state_dir = None
    # stdin 은 바이트로. 이유는 .claude/rules/tools.md(대기열 25).
    output = output_for(sys.stdin.buffer.read(), state_dir)
    if output is not None:
        print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
