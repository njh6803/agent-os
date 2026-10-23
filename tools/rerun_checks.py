"""다시 풀기 회차의 측정 아님 가르기. 회차를 열기 전에 전용 설정 폴더의 계정과 설정을 대 보고,
호출마다 원본 줄과 세션 기록 파일에서 설정·모델·오염·한도를 본다.

명세는 `.scratch/model-rerun/spec.md`의 "클론과 설정 폴더"의 계정과 설정 폴더의 설정, "한도",
"오염 검사", "모델 확인"이고 티켓은 `.scratch/model-rerun/issues/09-not-measured-checks.md`다. 설계
5절이 원천이고 명세가 고친 자리는 명세가 원천이다. 한도 표지의 선례는 `tools/canary.py`다. 걸린
회차를 다시 돌지, 과제를 뺄지, 러너를 멈출지는 10이 정한다.

판정과 바깥. 판정하는 함수는 값만 받는다(`account_problem`, `settings_env_problem`,
`init_outside`, `resolve_model`, `agent_model`, `model_mismatch`, `limit_of`, `windows_of`,
`strip_commit_messages`, `command_patterns`, `path_patterns`). 바깥을 읽는 몫은
`read_auth_status`(하위 프로세스, `AUTH_TIMEOUT`), `before_round`, `allowed_plugins`,
`harness_models`, `watched_paths`, `Screen`, `screen_for`다.

자리 둘. 회차를 열기 전에는 `before_round`가 계정과 설정 폴더의 `env` 키를 보고 걸린
까닭(`Refusal`)을 낸다. 설정 폴더의 잘못이면 그 회차의 끝(측정 아님(설정))도 싣는다. 명세 "설정
폴더의 설정"이 `env` 키와 init 을 묶어 측정 아님(설정)으로 적으라고 하고, 명세가 기록 없이 멈추라고
한 것은 계정 불일치뿐이다. 계정을 확인하지 못한 때(세션 환경에 설정 폴더가 없음, `auth status`를
읽지 못함)도 계정 쪽이라 기록 없이 멈춘다. 까닭에는 이메일을 싣지 않는다. 회차 안에서는 `Screen`이
`tools/rerun_continue.py`의 `run_sessions`에 두 자리로 들어간다. `Screen.watch`는 `drive`가 줄을
받을 때마다 불려, 허용 밖의 init 을 받은 그 줄에서 호출을 끄게 한다(`tools/rerun_session.py`의
`Stop.HALTED_*`). `Screen` 자체는 호출이 끝날 때마다 불려 그 호출의 원본 줄과 그 세션의 기록 파일을
보고, 앞 세션들에서 쌓아 둔 모델 견줌과 함께 끝을 낸다. 여럿이 걸리면 설정, 모델, 오염, 한도의
차례다. 모델과 오염도 호출마다 보아 걸리면 다음 호출을 하지 않는다. 기록의 칸(거부 수, 사용률, 오염
적중, 모델 불일치)은 `Screen.findings`가 낸다.

설정. init 이벤트의 `mcp_servers`가 빈 목록이고 `plugins`의 항목마다 `source`가 허용 모임 안이어야
한다. 허용 모임은 내장 셋(`<이름>@builtin`)과 클론의 `.claude/settings.json`의 `enabledPlugins`에서
값이 참인 키다. 명세는 첫 호출의 init 을 보라고 했지만 모든 호출의 모든 init 을 본다. 세션이 클론의
설정을 고쳐 다음 호출에 플러그인을 싣는 길까지 막으려는 것이다.

모델. 본 세션의 기록 파일은 `<synthetic>`을 뺀 줄이 모두 갈래의 (모델, 노력)이어야 하고,
서브에이전트 기록은 모델만 허용 모임(갈래의 모델, 하네스 모델, 그 세션의 Agent 입력이 고른 모델)과
견준다. 앞 세션이 고른 모델은 인계 뒤 세션으로 물려주지 않는다. 하네스 모델은 클론의
`.claude/agents/*.md` 머리말의 `model`과 `code-review`가 표준 축에 주는 `CODE_REVIEW_MODEL`이다.
별칭은 `MODEL_ALIASES`로 풀고, `inherit`과 빈 값과 없는 값은 갈래의 모델이다. 걸린 줄은 (모델,
노력)마다 더해 적고, 서브에이전트의 줄은 노력을 비운다.

오염. 도구 입력은 assistant 이벤트의 `tool_use`이고 서브에이전트의 것(`parent_tool_use_id`가 붙은
이벤트)도 든다. 결과 이벤트들의 `permission_denials`의 `tool_use_id`에 든 호출은 보지 않고 그 수를
거부 수로 센다. 찾는 꼴은 이름이 있는 상수다(`PATTERN_NAMES`).
- 셸 명령(`SHELL_TOOLS`의 `command`)은 주소 셋(`github.com`, `githubusercontent.com`,
  `njh6803/agent-os`), `open_session.ps1`, `claude://`를 명령 전체에서 찾고, 낱말 `gh`(앞뒤가 낱말
  글자가 아닌 것)는 `strip_commit_messages`로 커밋 메시지를 뗀 글에서 찾는다. 명세의 셸(Bash,
  PowerShell)에 `Monitor`를 더했다. 셸 명령을 돌리는 도구이고, `Bash(gh:*)` 꼴의 막는 규칙이 그
  명령에도 걸리는지는 재지 않았다.
- 웹 도구(`WEB_TOOLS`)의 입력과 `Monitor`의 웹소켓 입력(`SOCKET_KEY`)은 모든 글에서 여섯 꼴을
  찾는다. 웹소켓 입력이 있다는 것은 Claude Code 가 주는 `Monitor` 도구의 입력 스키마(`ws.url`,
  `ws.protocols`)에서 봤다.
- 쓰기의 내용(Write `content`, Edit `new_string`, NotebookEdit `new_source`)은 대상이 `.md`가 아니고
  클론의 `tests/` 밖일 때만 주소 셋을 찾는다.
- 경로. 모든 도구 입력의 글 값(글 칸 `FREE_TEXT_KEYS`와 Grep 의 `pattern`은 뺀다)에서 주 체크아웃,
  사용자의 `~/.claude`, 같은 뿌리 아래의 다른 회차 폴더, 전용 설정 폴더를 찾는다. 뒤의 둘은 04
  메모의 결정이다. 막는 규칙이 막지 않아 다른 갈래의 풀이와 세션 기록을 읽는 길이다. 자기 회차
  폴더와 자기 세션 기록 폴더(`<설정 폴더>/projects/<자기 세션 기록 파일의 폴더 이름>`, 자동 메모리와
  큰 도구 결과가 그 안이다)는 뺀다. 경로마다 링크를 풀지 않은 꼴과 푼 꼴을 둘 다 본다(04 메모의
  결정, 막는 규칙의 `deny_heads`와 같다). 글은 `\\`를 `/`로, 겹친 `/`를 하나로 바꾸고 대소문자를
  접어 견주고, 드라이브 경로는 Git Bash 의 `/c/` 꼴도 본다. 걸리는 것은 찾는 경로 뒤가 글의 끝이거나
  `BOUNDARY`의 글자일 때뿐이다. 명세의 넷(경로 구분자, 따옴표, 공백, 끝)에 셸의 제어 글자, glob
  글자(`*?`), 중괄호(`{}`. 중괄호 확장과 `${X:-…}`)를 더했다. 대괄호는 더하지 않았다. 대괄호
  glob 은 한 글자에 맞아 `~/.claude[a]`는 이웃 이름(`~/.claudea`)이다. 이웃
  이름(`~/.claude-rerun`, `~/.claude.json`)은 이름 글자로 이어져 걸리지 않는 것이 같다. 홈 아래의
  찾는 경로(`~/.claude`, 홈 아래에 둔 설정 폴더와 뿌리)는 `~`, `$HOME`, `%USERPROFILE%` 같은 홈을
  대신하는 이름(`HOME_ALIASES`)으로 적은 꼴도, 설정 폴더는 `CLAUDE_CONFIG_DIR`의
  꼴(`CONFIG_ALIASES`)도 본다. 경로 칸(`PATH_KEYS`)의 값은 클론에서 푼 꼴(`..` 정리)도 본다.
- 막은 바깥 도구(`tools/rerun_round.py`의 `BLOCKED_TOOLS`)의 이름과 Skill 입력의 `open-session`(앞의
  `/`와 `:` 앞을 뗀다)을 찾는다.
기록에는 걸린 꼴의 이름과 도구 이름만 남기고 입력은 옮기지 않는다. 도구 이름도 그 회차의 init 도구
목록이나 이 모듈이 아는 이름(`KNOWN_TOOLS`)이고 기록의 꼴일 때만 옮기고, 아니면
`UNKNOWN_TOOL`이다(`.claude/rules/tools.md`의 허용 목록 항목).

커밋 메시지 떼기(`strip_commit_messages`). git 이 메시지를 받는 길을 나열하고 길마다 시험을 둔다.
- `-m <값>`, `-m<값>`, `-am <값>`처럼 짧은 옵션 묶음의 `m`(여럿이어도 모두), `--message=<값>`,
  `--message <값>`, 그 줄임(`--m`부터). 짧은 묶음에서 `F`·`c`·`C`·`t`는 값을 받고(붙였으면 묶음의
  나머지), `u`·`S`는 붙인 값만 받는다. `--` 뒤는 경로라 떼지 않는다.
- `-F -`, `-F-`, `--file=-`, `--file -`(줄임 `--fil`부터)로 표준 입력에서 받을 때 그 명령의 heredoc
  본문.
- `-m "$(cat <<'EOF'` … `EOF` … `)"` 꼴의 heredoc 본문. `$(cat`이 메시지 옵션 바로 뒤에 있고,
  구분자에 따옴표가 있거나 본문에 명령 치환이 없으며, 종결자 다음 줄이 `)`로 시작할 때다.
- `-F <파일>`은 메시지가 명령에 없어 뗄 것이 없다. 그 값을 파일로 읽어 뒤의 낱말을 옵션으로
  잘못 읽지 않는다.
명령은 선례 `tools/hook_bash_commit_msg.py`처럼 줄 이음을 잇고 heredoc 본문을 뺀 뒤 shlex 로 나누고
제어 연산자에서 가른다. 명령 앞의 셸 예약어(`{`, `!`, `if`, `then`, `do`, `time` 등)와 환경 대입과
git 의 전역 옵션(`-C`, `-c`, `--git-dir` 등)을 지난다.
명령이 되는 글은 떼지 않는다. 명령 치환(`$(`, 백틱)이 든 메시지 값, 따옴표 없는 구분자의 heredoc
본문 가운데 명령 치환이 든 것, `bash`나 `python`에 넘긴 heredoc 본문이다. shlex 가 나누지 못하면(짝
없는 따옴표) 명령을 그대로 본다. 메시지 떼기는 낱말 `gh`에만 쓴다.

한도. `rate_limit_event`의 `status`가 `rejected`이거나 결과 이벤트의 `api_error`가
`usage_limit_reached`면 측정 아님(한도)이다. 풀리는 시각은 거절마다의 `resetsAt`(초 단위 유닉스
시각, 소수는 올린다)의 가장 늦은 값이다. `api_error`만 있거나 거절 가운데 하나라도 `resetsAt`이
비거나 시각으로 읽히지 않으면(숫자가 아니거나 `bool`이거나 음수이거나 날짜로 바꾸지 못하면)
비운다. 사용률은 `rate_limit_event`마다 `unifiedWindows`의 창을, 그것이 없으면 `rateLimitType`과
`utilization`을 읽어 창마다 회차의 첫 값과 끝 값을 적는다. `allowed_warning`은 사용률로만 남는다.

못 보는 것.
- 커밋 메시지 떼기가 나열한 길(위) 밖으로 넘긴 메시지는 떼지 않아, 그 안의 낱말 `gh`가
  걸린다(거짓 양성). 예: 다른 명령의 출력이나 heredoc 을 파이프로 받은 커밋(`cat <<'EOF' | git
  commit -F -`, `echo … | git commit -F -`), here-string(`git commit -F - <<< '…'`), 명령 앞의
  래퍼(`env`, `command`). 따옴표를 벗긴 낱말로 보므로 작은따옴표 안의 `$(`(`-m '$(gh)'`)도 명령
  치환으로 읽어 떼지 않는다.
- 셸이 글을 풀어야 나오는 경로는 풀지 않는다(거짓 음성). 예: 셸 명령의 상대 경로(`cat ../../<다른
  회차>/x`), 대신하는 이름 밖의 변수(`d=~; cat $d/.claude`), glob(`~/.cl*`), 절대 경로 안의
  `..`(`<뿌리>/<자기 회차>/../<다른 회차>`). 경로 칸의 값만 클론에서 풀고 `..`를 정리한다. 같은
  까닭으로 절대 경로 안의 `.` 조각(`<뿌리>/./<자기 회차>`)을 회차 폴더 이름으로 읽어 다른 회차로
  건다(거짓 양성).
- init 의 플러그인 항목에 `source`가 없으면 이름을 허용 키의 `@` 앞과 견주어, 다른 마켓의 같은 이름
  플러그인을 지나보낸다. 마켓 플러그인이 init 에 실리는 꼴은 재지 않았다(파일럿이 본다).
- 서브에이전트가 거부된 호출이 본 세션 결과의 `permission_denials`에 실리는지는 재지 않았다. 실리지
  않으면 그 호출이 오염으로 걸린다(거짓 양성 쪽).
- 내장 에이전트(Explore 등)를 Agent 입력의 `model` 없이 불렀을 때 무엇으로 도는지는 재지 않았다.
  그 모델이 갈래·하네스·Agent 입력의 모델이 아니면 그 줄이 허용 밖이라 측정 아님(모델)으로
  건다(거짓 양성 쪽). 허용 모임은 파일럿(11)이 사람과 정한다.
"""

from __future__ import annotations

import json
import math
import os
import posixpath
import re
import shlex
import subprocess
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from tools.rerun_cost import HAIKU
from tools.rerun_files import (
    END_NOT_MEASURED,
    IDENT_FORM,
    MODEL_FORM,
    OPUS,
    REASON_LIMIT,
    SONNET,
    Arm,
    End,
    Hit,
    Json,
    LineCount,
    Window,
)
from tools.rerun_round import BLOCKED_TOOLS, CONFIG_DIR_VAR, RoundDir
from tools.rerun_session import (
    SYNTHETIC,
    Launched,
    parse_event,
    transcript_counts,
    transcript_files,
)

AUTH_TIMEOUT = 60  # `claude auth status --json` 한 번

# 측정 아님의 하위 이유. `tools/rerun_files.py`의 NOT_MEASURED_REASONS 에 든다(시험이 본다). 한도는
# 그 파일의 REASON_LIMIT 이다.
REASON_SETTINGS = "설정"
REASON_MODEL = "모델"
REASON_CONTAMINATION = "오염"
_SETTINGS_END = End(END_NOT_MEASURED, REASON_SETTINGS, None)

# --- 설정 ---

# 프로브가 init 에서 본 내장 플러그인 셋(`.scratch/model-rerun/probes/README.md`).
BUILTIN_PLUGINS = ("cc-plugin-agents-md", "cc-plugin-telemetry", "cc-plugin-plugin-authoring")
_BUILTIN_SOURCE = "builtin"

# --- 모델 ---

MODEL_ALIASES = {"sonnet": SONNET, "haiku": HAIKU, "opus": OPUS}
_INHERIT = ("", "inherit")
# `code-review` 스킬이 표준 축 서브에이전트에 주는 모델(시험이 이 저장소의 스킬에서 본다).
CODE_REVIEW_MODEL = "sonnet"
_FRONT_MATTER = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.DOTALL)
_MODEL_LINE = re.compile(r"^model:[ \t]*(.*?)[ \t]*$", re.MULTILINE)

# --- 한도(`tools/canary.py`와 같은 표지) ---

LIMIT_REJECTED = "rejected"
USAGE_LIMIT = "usage_limit_reached"

# --- 오염 ---

GITHUB = "github-주소"
GITHUBUSERCONTENT = "githubusercontent-주소"
REPOSITORY = "저장소-이름"
GH_WORD = "낱말-gh"
OPEN_SESSION_SCRIPT = "open-session-스크립트"
CLAUDE_LINK = "claude-링크"
MAIN_CHECKOUT = "주-체크아웃"
USER_CLAUDE = "사용자-claude"
OTHER_ROUND = "다른-회차"
CONFIG_FOLDER = "설정-폴더"
BLOCKED_TOOL = "막은-도구"
OPEN_SESSION_SKILL = "open-session-스킬"
PATTERN_NAMES = (
    GITHUB,
    GITHUBUSERCONTENT,
    REPOSITORY,
    GH_WORD,
    OPEN_SESSION_SCRIPT,
    CLAUDE_LINK,
    MAIN_CHECKOUT,
    USER_CLAUDE,
    OTHER_ROUND,
    CONFIG_FOLDER,
    BLOCKED_TOOL,
    OPEN_SESSION_SKILL,
)

_ADDRESSES = (
    (GITHUB, re.compile(r"github\.com", re.IGNORECASE)),
    (GITHUBUSERCONTENT, re.compile(r"githubusercontent\.com", re.IGNORECASE)),
    (REPOSITORY, re.compile(r"njh6803/agent-os", re.IGNORECASE)),
)
# 윈도의 셸은 명령 이름의 대소문자를 가리지 않아 `GH`도 gh 를 띄운다.
_GH = re.compile(r"(?<!\w)gh(?!\w)", re.IGNORECASE)
_SESSION_OPENERS = (
    (OPEN_SESSION_SCRIPT, re.compile(r"open_session\.ps1", re.IGNORECASE)),
    (CLAUDE_LINK, re.compile(r"claude://", re.IGNORECASE)),
)

MONITOR = "Monitor"
SHELL_TOOLS = ("Bash", "PowerShell", MONITOR)
WEB_TOOLS = ("WebFetch", "WebSearch")
SOCKET_KEY = "ws"  # `Monitor`가 웹소켓을 여는 입력(`url`, `protocols`)
# 쓰기 도구마다 (대상 칸, 내용 칸)
CONTENT_TOOLS = {
    "Write": ("file_path", "content"),
    "Edit": ("file_path", "new_string"),
    "NotebookEdit": ("notebook_path", "new_source"),
}
AGENT_TOOLS = ("Agent", "Task")  # init 목록에는 `Task`, tool_use 에는 `Agent`로 실렸다(프로브)
SKILL_TOOL = "Skill"
OPEN_SESSION = "open-session"
# 경로가 아니라 글을 담는 칸. 경로를 찾지 않는다
FREE_TEXT_KEYS = frozenset(
    {"content", "old_string", "new_string", "new_source", "description", "prompt", "message"}
)
_FREE_TEXT_BY_TOOL = {"Grep": frozenset({"pattern"})}  # 찾는 글이다
PATH_KEYS = frozenset({"file_path", "notebook_path", "path"})
KNOWN_TOOLS = frozenset(
    {
        *SHELL_TOOLS,
        *WEB_TOOLS,
        *CONTENT_TOOLS,
        *AGENT_TOOLS,
        *BLOCKED_TOOLS,
        SKILL_TOOL,
        "Read",
        "Glob",
        "Grep",
        "SubagentHandback",
    }
)
UNKNOWN_TOOL = "unknown"
_TOOL_FORM = re.compile(r"[A-Za-z][A-Za-z0-9_-]*")  # 기록의 도구 이름 꼴(`tools/rerun_files.py`)

BOUNDARY = frozenset("/'\"` \t\r\n\f\v;|&<>(),:*?{}")
HOME_ALIASES = (
    "~",
    "$home",
    "${home}",
    "$userprofile",
    "${userprofile}",
    "$env:home",
    "${env:home}",
    "$env:userprofile",
    "${env:userprofile}",
    "%userprofile%",
)
CONFIG_ALIASES = (
    f"${CONFIG_DIR_VAR}",
    f"${{{CONFIG_DIR_VAR}}}",
    f"$env:{CONFIG_DIR_VAR}",
    f"${{env:{CONFIG_DIR_VAR}}}",
    f"%{CONFIG_DIR_VAR}%",
)
_PROJECTS = "projects"
_DRIVE = re.compile(r"^([a-z]):/")


# --- JSON ---


def _parse_json(text: str) -> Json:
    # `json.loads`의 반환형은 Any라 `Json`으로 받아 뒤의 좁히기가 타입 검사를 지나게 한다.
    return json.loads(text)


def _object(text: str) -> dict[str, Json] | None:
    """JSON 객체로 풀리면 그 객체, 아니면 None. 앞의 BOM 은 뗀다."""
    try:
        value = _parse_json(text.removeprefix("\ufeff"))
    except (ValueError, RecursionError):
        return None
    return value if isinstance(value, dict) else None


def _dict(v: Json) -> dict[str, Json]:
    return v if isinstance(v, dict) else {}


def _list(v: Json) -> list[Json]:
    return v if isinstance(v, list) else []


def _read_or_none(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError):
        return None


# --- 계정과 설정 폴더(회차를 열기 전) ---


def account_problem(stdout: str, *, account: str, config_dir: str) -> str | None:
    """`claude auth status --json`의 stdout 이 회차를 열 수 있는 계정인지. 문제가 없으면 None,
    있으면 그 까닭이다. 까닭에는 이메일을 싣지 않는다."""
    status = _object(stdout)
    if status is None:
        return "claude auth status --json 의 출력이 JSON 객체가 아니다"
    if status.get("loggedIn") is not True:
        return "전용 설정 폴더에 로그인하지 않았다(loggedIn 이 참이 아니다)"
    email = status.get("email")
    if not isinstance(email, str) or "@" not in email:
        return "auth status 에 email 이 없거나 주소의 꼴이 아니다"
    if email.partition("@")[0] != account:
        return f"로그인한 계정이 {account} 가 아니다"
    if status.get("configDirectory") != config_dir:
        return f"auth status 의 configDirectory 가 넘긴 설정 폴더({config_dir})와 다르다"
    return None


def settings_env_problem(text: str | None) -> str | None:
    """설정 폴더의 `settings.json` 글(없으면 None)에 `env` 키가 없는지."""
    if text is None:
        return None
    settings = _object(text)
    if settings is None:
        return "설정 폴더의 settings.json 이 JSON 객체가 아니다"
    if "env" in settings:
        return "설정 폴더의 settings.json 에 env 키가 있다"
    return None


def read_auth_status(claude: Sequence[str], *, env: Mapping[str, str], cwd: Path) -> str | None:
    """`claude auth status --json`의 stdout. 종료 코드는 보지 않는다(로그아웃이면 1로 끝나고 JSON 을
    낸다). 띄우지 못했거나 시간을 넘기면 None 이다."""
    try:
        done = subprocess.run(
            [*claude, "auth", "status", "--json"],
            cwd=cwd,
            env=dict(env),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=AUTH_TIMEOUT,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return done.stdout


@dataclass(frozen=True)
class Refusal:
    """회차를 열기 전에 걸린 것. `why`는 사람에게 넘길 까닭이고 이메일을 싣지 않는다. `end`가
    있으면 그 회차를 그 끝으로 적는다(설정 폴더의 잘못, 측정 아님(설정)). 없으면 회차를 열지 않아
    기록이 없다(계정과 세션 환경). 걸리면 새 회차를 열지 않고 러너를 멈춘다(10)."""

    why: str
    end: End | None = None


def before_round(
    claude: Sequence[str], *, env: Mapping[str, str], cwd: Path, account: str
) -> Refusal | None:
    """회차를 열기 전의 확인. `env`는 세션에 넘길 환경이고 설정 폴더는 그 `CLAUDE_CONFIG_DIR`의 글
    그대로다. 계정, 설정 폴더의 `settings.json`의 차례로 보고 문제가 없으면 None 이다."""
    config = env.get(CONFIG_DIR_VAR)
    if not config:
        return Refusal(f"세션 환경에 {CONFIG_DIR_VAR} 가 없다")
    stdout = read_auth_status(claude, env=env, cwd=cwd)
    if stdout is None:
        return Refusal("claude auth status --json 을 띄우지 못했거나 시간을 넘겼다")
    problem = account_problem(stdout, account=account, config_dir=config)
    if problem is not None:
        return Refusal(problem)
    path = Path(config) / "settings.json"
    try:
        text = path.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        return None  # 설정 파일이 없으면 env 키도 없다
    except (OSError, UnicodeDecodeError):
        return Refusal("설정 폴더의 settings.json 을 읽지 못했다", _SETTINGS_END)
    problem = settings_env_problem(text)
    return None if problem is None else Refusal(problem, _SETTINGS_END)


# --- init 의 설정 ---


def enabled_plugins(text: str | None) -> tuple[str, ...]:
    """settings.json 글의 `enabledPlugins`에서 값이 참인 키."""
    settings = _object(text) if text is not None else None
    enabled = (settings or {}).get("enabledPlugins")
    if not isinstance(enabled, dict):
        return ()
    return tuple(sorted(key for key, on in enabled.items() if on is True))


def allowed_plugins(clone: Path) -> frozenset[str]:
    """허용 모임. 내장 셋과 클론의 `.claude/settings.json`(B의 것)이 켠 플러그인의 키다."""
    builtin = (f"{p}@{_BUILTIN_SOURCE}" for p in BUILTIN_PLUGINS)
    enabled = enabled_plugins(_read_or_none(clone / ".claude" / "settings.json"))
    return frozenset({*builtin, *enabled})


def _plugin_allowed(entry: Json, allowed: frozenset[str]) -> bool:
    if isinstance(entry, str):
        name, source = entry, None
    elif isinstance(entry, dict):
        raw_name, raw_source = entry.get("name"), entry.get("source")
        name = raw_name if isinstance(raw_name, str) else None
        source = raw_source if isinstance(raw_source, str) else None
    else:
        return False
    if source is not None:
        return source in allowed
    return name is not None and name in {key.partition("@")[0] for key in allowed}


def _is_init(event: Mapping[str, Json]) -> bool:
    return event.get("type") == "system" and event.get("subtype") == "init"


def init_outside(event: Mapping[str, Json], allowed: frozenset[str]) -> bool:
    """init 이벤트가 허용 밖인가. `mcp_servers`가 빈 목록이 아니거나 `plugins`가 목록이 아니거나 그
    항목 하나라도 허용 모임 밖이면 그렇다."""
    servers = event.get("mcp_servers")
    plugins = event.get("plugins")
    if not isinstance(servers, list) or servers or not isinstance(plugins, list):
        return True
    return not all(_plugin_allowed(p, allowed) for p in plugins)


# --- 모델 ---


def resolve_model(value: Json, arm: Arm) -> str | None:
    """에이전트 정의나 Agent 입력의 `model` 값을 전체 이름으로. 모르는 값은 None 이다."""
    if value is None:
        return arm.model
    if not isinstance(value, str):
        return None
    name = value.strip().casefold()
    if name in _INHERIT:
        return arm.model
    if name in MODEL_ALIASES:
        return MODEL_ALIASES[name]
    return name if MODEL_FORM.fullmatch(name) and name != SYNTHETIC else None


def agent_model(text: str) -> str | None:
    """에이전트 파일 머리말의 `model` 값(따옴표를 뗀다). 머리말이나 그 줄이 없으면 None 이다."""
    front = _FRONT_MATTER.match(text.removeprefix("\ufeff"))
    if front is None:
        return None
    line = _MODEL_LINE.search(front.group(1))
    return None if line is None else line.group(1).strip("'\"")


def harness_models(clone: Path, arm: Arm) -> frozenset[str]:
    """하네스가 정한 서브에이전트 모델. 클론의 `.claude/agents/*.md`와 `CODE_REVIEW_MODEL`이다."""
    found = {resolve_model(CODE_REVIEW_MODEL, arm)}
    for path in sorted((clone / ".claude" / "agents").glob("*.md")):
        text = _read_or_none(path)
        if text is not None:
            found.add(resolve_model(agent_model(text), arm))
    return frozenset(m for m in found if m is not None)


def model_mismatch(
    main: Iterable[LineCount], side: Iterable[LineCount], *, arm: Arm, allowed: Iterable[str]
) -> tuple[LineCount, ...]:
    """허용 밖의 줄 수. 본 세션은 `<synthetic>`을 뺀 줄의 (모델, 노력)이 갈래의 것이어야 하고,
    서브에이전트는 `<synthetic>`을 뺀 줄의 모델이 갈래의 모델이나 `allowed` 안이어야 한다.
    서브에이전트의 줄은 노력을 비워 모델마다 더한다."""
    ok = {arm.model, *allowed}
    found = [
        c for c in main if c.model != SYNTHETIC and (c.model, c.effort) != (arm.model, arm.effort)
    ]
    found.extend(
        LineCount(model=c.model, effort=None, lines=c.lines)
        for c in side
        if c.model != SYNTHETIC and c.model not in ok
    )
    return _summed(found)


def _summed(counts: Iterable[LineCount]) -> tuple[LineCount, ...]:
    """(모델, 노력)마다 줄 수를 더해 모델과 노력의 차례로 낸다."""
    total: dict[tuple[str, str | None], int] = {}
    for c in counts:
        total[(c.model, c.effort)] = total.get((c.model, c.effort), 0) + c.lines
    ordered = sorted(total.items(), key=lambda kv: (kv[0][0], kv[0][1] or ""))
    return tuple(LineCount(model=m, effort=e, lines=n) for (m, e), n in ordered)


# --- 한도 ---


@dataclass(frozen=True)
class Limit:
    resets_at: int | None  # 풀리는 시각(유닉스 초). 모르면 빈 값


def _resets(value: Json) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    if not math.isfinite(value) or value < 0:
        return None
    try:
        datetime.fromtimestamp(value, UTC)
    except (OverflowError, OSError, ValueError):
        return None
    return math.ceil(value)


def limit_of(events: Iterable[Mapping[str, Json]]) -> Limit | None:
    """한도 표지. 없으면 None 이다."""
    resets: list[int | None] = []
    usage = False
    for event in events:
        kind = event.get("type")
        if kind == "rate_limit_event":
            info = _dict(event.get("rate_limit_info"))
            if info.get("status") == LIMIT_REJECTED:
                resets.append(_resets(info.get("resetsAt")))
        elif kind == "result" and event.get("api_error") == USAGE_LIMIT:
            usage = True
    if resets:
        known = [r for r in resets if r is not None]
        return Limit(max(known) if len(known) == len(resets) else None)
    return Limit(None) if usage else None


def _ratio(v: Json) -> float | None:
    if isinstance(v, bool) or not isinstance(v, int | float):
        return None
    try:
        f = float(v)
    except OverflowError:
        return None
    return f if math.isfinite(f) and f >= 0 else None


def windows_of(event: Mapping[str, Json]) -> tuple[Window, ...]:
    """한도 이벤트 하나의 창마다의 사용률. 창의 이름은 영소문자 식별자만 옮긴다."""
    if event.get("type") != "rate_limit_event":
        return ()
    info = _dict(event.get("rate_limit_info"))
    found: list[Window] = []
    for name, raw in sorted(_dict(info.get("unifiedWindows")).items()):
        used = _ratio(_dict(raw).get("utilization"))
        if IDENT_FORM.fullmatch(name) and used is not None:
            found.append(Window(window=name, utilization=used))
    if found:
        return tuple(found)
    name = info.get("rateLimitType")
    used = _ratio(info.get("utilization"))
    if isinstance(name, str) and IDENT_FORM.fullmatch(name) and used is not None:
        return (Window(window=name, utilization=used),)
    return ()


# --- 커밋 메시지 떼기 ---

# here-string `<<<` 은 heredoc 이 아니다. `tools/hook_bash_commit_msg.py`와 같은 모양이다.
_HEREDOC_OPENER = re.compile(r"(?<!<)<<(?!<)(-?)\s*\\?(['\"]?)([^\s;&|<>()'\"\\]+)\2")
_CONTROL = re.compile(r"[;&|()<>\n]+")
_ASSIGNMENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=")
# 단순 명령 앞에 올 수 있는 셸 예약어. 그 뒤가 명령이다
_RESERVED_WORDS = frozenset(
    {"{", "!", "if", "then", "else", "elif", "do", "while", "until", "time"}
)
_RUNS_COMMANDS = re.compile(r"\$\(|`")
_CAT_SUBSTITUTION = re.compile(r"\$\(\s*cat\s*$")
_GIT_GLOBAL_WITH_VALUE = frozenset(
    {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--config-env", "--super-prefix"}
)
_COMMIT_LONG_WITH_VALUE = frozenset(
    {
        "--author",
        "--date",
        "--template",
        "--trailer",
        "--reuse-message",
        "--reedit-message",
        "--fixup",
        "--squash",
        "--cleanup",
        "--pathspec-from-file",
    }
)
_SHORT_WITH_VALUE = frozenset("mFcCt")
_SHORT_WITH_ATTACHED = frozenset("uS")


def _tokens(text: str) -> list[str] | None:
    lexer = shlex.shlex(text, posix=True, punctuation_chars=";&|()<>\n")
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    lexer.commenters = ""
    try:
        return list(lexer)
    except ValueError:  # 짝 없는 따옴표
        return None


def _segments(tokens: Iterable[str]) -> list[list[str]]:
    """제어 연산자에서 가른 단순 명령들."""
    segments: list[list[str]] = [[]]
    for token in tokens:
        if _CONTROL.fullmatch(token) is None:
            segments[-1].append(token)
        elif segments[-1]:
            segments.append([])
    return [s for s in segments if s]


def _is_git(word: str) -> bool:
    return re.split(r"[/\\]", word)[-1].casefold() in ("git", "git.exe")


def _commit_args(words: Sequence[str]) -> int | None:
    """단순 명령이 `git commit`이면 `commit` 뒤 인자의 첫 자리, 아니면 None."""
    index = 0
    while index < len(words) and (
        words[index] in _RESERVED_WORDS or _ASSIGNMENT.match(words[index])
    ):
        index += 1
    if index >= len(words) or not _is_git(words[index]):
        return None
    index += 1
    while index < len(words) and words[index].startswith("-"):
        option = words[index]
        index += 1
        if option in _GIT_GLOBAL_WITH_VALUE:
            index += 1
    if index < len(words) and words[index] == "commit":
        return index + 1
    return None


def _is_message_long(name: str) -> bool:
    return len(name) >= len("--m") and "--message".startswith(name)


def _is_file_long(name: str) -> bool:
    return len(name) >= len("--fil") and "--file".startswith(name)  # `--fi`는 `--fixup`과 겹친다


def _inert(value: str) -> bool:
    """명령 치환이 없어 셸이 돌리지 않는 글인가."""
    return _RUNS_COMMANDS.search(value) is None


def _without_messages(args: Sequence[str]) -> tuple[list[str], bool]:
    """`git commit`의 인자에서 메시지 값을 뺀 것과, 메시지를 표준 입력에서 읽는지."""
    kept: list[str] = []
    stdin = False
    index = 0
    while index < len(args):
        word = args[index]
        index += 1
        if word == "--":
            kept.extend(args[index - 1 :])
            break
        if word.startswith("--"):
            name, eq, value = word.partition("=")
            if not (
                _is_message_long(name) or _is_file_long(name) or name in _COMMIT_LONG_WITH_VALUE
            ):
                kept.append(word)
                continue
            if not eq:
                if index >= len(args):
                    kept.append(word)
                    continue
                value = args[index]
                index += 1
            if _is_message_long(name) and _inert(value):
                kept.append(name)
                continue
            stdin = stdin or (_is_file_long(name) and value == "-")
            kept.extend((word,) if eq else (word, value))
            continue
        if not word.startswith("-") or word == "-":
            kept.append(word)
            continue
        kept.append(word)
        for position, flag in enumerate(word[1:], start=1):
            if flag in _SHORT_WITH_ATTACHED:
                break
            if flag in _SHORT_WITH_VALUE:
                value = word[position + 1 :]
                separate = not value and index < len(args)
                if separate:
                    value = args[index]
                    index += 1
                if flag == "m" and _inert(value):
                    kept[-1] = word[: position + 1]
                elif separate:
                    kept.append(value)
                stdin = stdin or (flag == "F" and value == "-")
                break
    return kept, stdin


def _last_commit(text: str) -> list[str] | None:
    """글의 마지막 단순 명령이 `git commit`이면 그 `commit` 뒤 인자, 아니면 None."""
    tokens = _tokens(text)
    if tokens is None or (tokens and _CONTROL.fullmatch(tokens[-1])):
        return None
    segments = _segments(tokens)
    if not segments:
        return None
    start = _commit_args(segments[-1])
    return None if start is None else segments[-1][start:]


def _awaits_message(word: str) -> bool:
    """값을 다음에 받는 메시지 옵션(`-m`, `-am`, `--message`, `--message=`)인가."""
    if word.startswith("--"):
        name, _, value = word.partition("=")
        return _is_message_long(name) and not value
    if not word.startswith("-"):
        return False
    for position, flag in enumerate(word[1:], start=1):
        if flag in _SHORT_WITH_ATTACHED:
            return False
        if flag in _SHORT_WITH_VALUE:
            return flag == "m" and not word[position + 1 :]
    return False


def _message_substitution(prefix: str) -> int | None:
    """heredoc 여는 표지 앞 글이 `git commit … -m "$(cat`로 끝나면 `$(cat`의 자리."""
    found = _CAT_SUBSTITUTION.search(prefix)
    if found is None:
        return None
    head = prefix[: found.start()].removesuffix('"')
    args = _last_commit(head)
    if not args or not _awaits_message(args[-1]):
        return None
    return found.start()


def _reads_message_stdin(prefix: str) -> bool:
    """heredoc 여는 표지 앞 글이 메시지를 표준 입력에서 읽는 `git commit`으로 끝나는가."""
    args = _last_commit(prefix)
    return args is not None and _without_messages(args)[1]


def _split_heredocs(given: Sequence[str]) -> tuple[list[str], list[str]]:
    """명령 줄과 남길 heredoc 본문. 커밋 메시지인 본문은 뺀다."""
    lines = list(given)  # 메시지 치환을 닫는 `)`를 떼며 고친다
    kept: list[str] = []
    bodies: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        index += 1
        cut: int | None = None
        for opener in _HEREDOC_OPENER.finditer(line):
            strips_tabs = opener.group(1) == "-"
            terminator = opener.group(3)
            body: list[str] = []
            closed = False
            while index < len(lines):
                row = lines[index]
                index += 1
                if (row.lstrip("\t") if strips_tabs else row) == terminator:
                    closed = True
                    break
                body.append(row)
            text = "\n".join(body)
            quoted = bool(opener.group(2)) or "\\" in opener.group(0)
            prefix = line[: opener.start()]
            message = closed and (quoted or _inert(text))  # 셸이 본문에서 명령을 돌리지 않는다
            if message and _reads_message_stdin(prefix):
                continue
            place = _message_substitution(prefix) if message and cut is None else None
            if place is not None and index < len(lines) and lines[index].lstrip().startswith(")"):
                cut = place
                lines[index] = lines[index].lstrip()[1:]
                continue
            bodies.append(text)
        kept.append(line if cut is None else line[:cut])
    return kept, bodies


def strip_commit_messages(command: str) -> str:
    """셸 명령에서 `git commit`의 메시지를 뗀 글(모듈 독스트링의 커밋 메시지 떼기). 남긴 낱말을
    공백으로 잇고 남긴 heredoc 본문을 뒤에 붙인다. shlex 가 나누지 못하면 명령 그대로다."""
    kept, bodies = _split_heredocs(command.replace("\\\n", "").split("\n"))
    tokens = _tokens("\n".join(kept))
    if tokens is None:
        return command
    words: list[str] = []
    for segment in _segments(tokens):
        start = _commit_args(segment)
        if start is None:
            words.extend(segment)
        else:
            words.extend(segment[:start])
            words.extend(_without_messages(segment[start:])[0])
    return "\n".join((" ".join(words), *bodies))


# --- 오염의 꼴 ---


def content_patterns(text: str) -> tuple[str, ...]:
    """쓰기 내용에서 찾는 꼴. 주소 셋이다."""
    return tuple(name for name, pattern in _ADDRESSES if pattern.search(text))


def _six_patterns(text: str, *, words: str) -> tuple[str, ...]:
    """여섯 꼴. 주소 셋과 세션을 여는 꼴은 `text`에서, 낱말 `gh`는 `words`에서 찾는다."""
    found = list(content_patterns(text))
    if _GH.search(words):
        found.append(GH_WORD)
    found.extend(name for name, pattern in _SESSION_OPENERS if pattern.search(text))
    return tuple(found)


def command_patterns(command: str) -> tuple[str, ...]:
    """셸 명령에서 찾는 꼴. 주소 셋과 세션을 여는 꼴은 명령 전체에서, 낱말 `gh`는 커밋 메시지를 뗀
    글에서 찾는다."""
    return _six_patterns(command, words=strip_commit_messages(command))


def _web_patterns(value: Json) -> tuple[str, ...]:
    """웹에 닿는 입력(웹 도구의 입력 전부, `Monitor`의 `ws`)의 모든 글에서 여섯 꼴을 찾는다."""
    text = "\n".join(t for _, t in _leaves(value, frozenset()))
    return _six_patterns(text, words=text)


# --- 경로 ---


def _fold(text: str) -> str:
    """`\\`를 `/`로, 겹친 `/`를 하나로 바꾸고 대소문자를 접는다."""
    return re.sub(r"/{2,}", "/", text.replace("\\", "/")).casefold()


def _plain(text: str) -> str:
    """윈도 `realpath`가 남긴 장치 접두(`\\\\?\\`, `\\\\?\\UNC\\`)를 뗀다."""
    if text.startswith("\\\\?\\UNC\\"):
        return "\\\\" + text[len("\\\\?\\UNC\\") :]
    return text.removeprefix("\\\\?\\")


def head_forms(texts: Iterable[str]) -> tuple[str, ...]:
    """찾는 경로의 꼴. 접은 글에서 끝의 `/`를 떼고, 드라이브 경로면 Git Bash 의 `/c/` 꼴도 낸다."""
    forms: list[str] = []
    for text in texts:
        folded = _fold(text).rstrip("/")
        found = [folded]
        if drive := _DRIVE.match(folded + "/"):
            found.append(f"/{drive.group(1)}{folded[2:]}")
        forms.extend(f for f in found if f and f not in forms)
    return tuple(forms)


@dataclass(frozen=True)
class Watched:
    """오염으로 찾는 경로들의 꼴(`head_forms`)."""

    main_checkout: tuple[str, ...]
    user_claude: tuple[str, ...]
    root: tuple[str, ...]
    round_name: str  # 접은 자기 회차 폴더 이름
    config: tuple[str, ...]


def _with_home_aliases(forms: tuple[str, ...], homes: tuple[str, ...]) -> tuple[str, ...]:
    """꼴마다, 홈 아래이면 홈을 대신하는 이름(`HOME_ALIASES`)으로 적은 꼴을 더한다."""
    found = list(forms)
    for form in forms:
        for home in homes:
            if form == home or form.startswith(home + "/"):
                found.extend(f"{alias}{form[len(home) :]}" for alias in HOME_ALIASES)
    return tuple(dict.fromkeys(found))


def watched_from(
    *,
    main_checkout: Iterable[str],
    home: Iterable[str],
    user_claude: Iterable[str],
    root: Iterable[str],
    round_name: str,
    config: Iterable[str],
) -> Watched:
    """경로의 글에서 `Watched`를 짓는다. 홈 아래의 찾는 경로는 홈을 대신하는 이름의 꼴을, 설정
    폴더는 `CLAUDE_CONFIG_DIR`의 꼴을 더한다."""
    homes = head_forms(home)

    def forms(texts: Iterable[str]) -> tuple[str, ...]:
        return _with_home_aliases(head_forms(texts), homes)

    return Watched(
        main_checkout=forms(main_checkout),
        user_claude=forms(user_claude),
        root=forms(root),
        round_name=round_name.casefold(),
        config=forms((*config, *CONFIG_ALIASES)),
    )


def _texts(path: Path) -> tuple[str, str]:
    """링크를 풀지 않은 꼴과 푼 꼴(막는 규칙의 `deny_heads`와 같다)."""
    return os.path.abspath(path), _plain(os.path.realpath(path))


def watched_paths(*, main_checkout: Path, home: Path, place: RoundDir, config_dir: Path) -> Watched:
    """회차 하나가 찾는 경로. 뿌리는 회차 폴더의 부모다."""
    return watched_from(
        main_checkout=_texts(main_checkout),
        home=_texts(home),
        user_claude=_texts(home / ".claude"),
        root=_texts(place.path.parent),
        round_name=place.name,
        config=_texts(config_dir),
    )


def _segment(rest: str) -> str:
    """`/`로 시작하는 글의 첫 조각. 아니면 빈 글이다."""
    if not rest.startswith("/"):
        return ""
    out: list[str] = []
    for ch in rest[1:]:
        if ch in BOUNDARY:
            break
        out.append(ch)
    return "".join(out)


def _found(folded: str, heads: Iterable[str], counts: Callable[[str], bool]) -> bool:
    """접은 글에 그 꼴이 조각 경계로 있고, 그 뒤의 글(`rest`)을 `counts`가 셀 때 참이다."""
    for head in heads:
        for match in re.finditer(re.escape(head), folded):
            rest = folded[match.end() :]
            if rest and rest[0] not in BOUNDARY:
                continue
            if counts(rest):
                return True
    return False


def path_patterns(
    text: str, watched: Watched, *, own_slugs: frozenset[str] = frozenset()
) -> tuple[str, ...]:
    """글에서 찾는 경로의 꼴. `own_slugs`는 접은 자기 세션 기록 폴더 이름이다."""
    folded = _fold(text)

    def other_round(rest: str) -> bool:
        return _segment(rest) != watched.round_name

    def not_own_records(rest: str) -> bool:
        first = _segment(rest)
        return first != _PROJECTS or _segment(rest[1 + len(first) :]) not in own_slugs

    found: list[str] = []
    if _found(folded, watched.main_checkout, lambda _rest: True):
        found.append(MAIN_CHECKOUT)
    if _found(folded, watched.user_claude, lambda _rest: True):
        found.append(USER_CLAUDE)
    if _found(folded, watched.root, other_round):
        found.append(OTHER_ROUND)
    if _found(folded, watched.config, not_own_records):
        found.append(CONFIG_FOLDER)
    return tuple(found)


def _resolved(text: str, clone: str) -> str:
    """경로 칸의 값을 클론에서 풀고 `..`를 정리한 접은 글."""
    folded = _fold(text)
    if not (folded.startswith("/") or _DRIVE.match(folded)):
        folded = f"{_fold(clone).rstrip('/')}/{folded}"
    return posixpath.normpath(folded)


def _content_watched(target: str, clone: str) -> bool:
    """쓰기 내용을 볼 대상인가. `.md`가 아니고 클론의 `tests/` 밖이다."""
    path = _resolved(target, clone)
    if path.endswith(".md"):
        return False
    for base in head_forms((clone,)):  # Git Bash 의 `/c/` 꼴로 적은 대상도 클론 안이다
        if path.startswith(base + "/"):
            relative = path[len(base) + 1 :]
            return relative != "tests" and not relative.startswith("tests/")
    return True  # 클론 밖


# --- 도구 입력 ---


@dataclass(frozen=True)
class ToolUse:
    use_id: str | None
    name: str
    tool_input: dict[str, Json]


def tool_uses(events: Iterable[Mapping[str, Json]]) -> list[ToolUse]:
    """assistant 이벤트(서브에이전트의 것도)의 `tool_use`."""
    found: list[ToolUse] = []
    for event in events:
        if event.get("type") != "assistant":
            continue
        for item in _list(_dict(event.get("message")).get("content")):
            block = _dict(item)
            if block.get("type") != "tool_use":
                continue
            use_id, name = block.get("id"), block.get("name")
            found.append(
                ToolUse(
                    use_id=use_id if isinstance(use_id, str) else None,
                    name=name if isinstance(name, str) else "",
                    tool_input=_dict(block.get("input")),
                )
            )
    return found


def denied_ids(events: Iterable[Mapping[str, Json]]) -> frozenset[str]:
    """결과 이벤트들의 `permission_denials`의 도구 호출 id 를 합친 것."""
    ids: set[str] = set()
    for event in events:
        if event.get("type") != "result":
            continue
        for denial in _list(event.get("permission_denials")):
            use_id = _dict(denial).get("tool_use_id")
            if isinstance(use_id, str):
                ids.add(use_id)
    return frozenset(ids)


def _leaves(
    value: Json, skip: frozenset[str], key: str | None = None
) -> Iterator[tuple[str | None, str]]:
    """입력의 글 값과 그 칸 이름. `skip`의 칸은 들어가지 않는다."""
    if isinstance(value, str):
        yield key, value
    elif isinstance(value, dict):
        for k, v in value.items():
            if k not in skip:
                yield from _leaves(v, skip, k)
    elif isinstance(value, list):
        for v in value:
            yield from _leaves(v, skip, key)


def _skill_name(value: Json) -> str | None:
    if not isinstance(value, str):
        return None
    return value.strip().removeprefix("/").rpartition(":")[2].casefold()


def use_patterns(
    use: ToolUse, *, watched: Watched, clone: str, own_slugs: frozenset[str]
) -> tuple[str, ...]:
    """도구 호출 하나에서 걸린 꼴(중복 없이 처음 본 차례)."""
    found: list[str] = []
    name, given = use.name, use.tool_input
    if name in BLOCKED_TOOLS:
        found.append(BLOCKED_TOOL)
    if name == SKILL_TOOL and _skill_name(given.get("skill")) == OPEN_SESSION:
        found.append(OPEN_SESSION_SKILL)
    command = given.get("command")
    if name in SHELL_TOOLS and isinstance(command, str):
        found.extend(command_patterns(command))
    if name in WEB_TOOLS:
        found.extend(_web_patterns(given))
    if name == MONITOR and SOCKET_KEY in given:
        found.extend(_web_patterns(given[SOCKET_KEY]))
    if name in CONTENT_TOOLS:
        target_key, content_key = CONTENT_TOOLS[name]
        target, content = given.get(target_key), given.get(content_key)
        if isinstance(content, str) and (
            not isinstance(target, str) or _content_watched(target, clone)
        ):
            found.extend(content_patterns(content))
    skip = FREE_TEXT_KEYS | _FREE_TEXT_BY_TOOL.get(name, frozenset())
    for key, text in _leaves(given, skip):
        found.extend(path_patterns(text, watched, own_slugs=own_slugs))
        if key in PATH_KEYS:
            found.extend(path_patterns(_resolved(text, clone), watched, own_slugs=own_slugs))
    return tuple(dict.fromkeys(found))


# --- 회차 안의 판정 ---


@dataclass(frozen=True)
class Findings:
    """회차 기록의 칸 가운데 이 모듈이 짓는 것(`tools/rerun_session.py`의 `Elsewhere`로 간다)."""

    denied_calls: int
    utilization_start: tuple[Window, ...]
    utilization_end: tuple[Window, ...]
    contamination: tuple[Hit, ...]
    model_mismatch: tuple[LineCount, ...]


class Screen:
    """회차 하나의 판정. 호출마다 `run_sessions`가 부르고(`__call__`), 줄마다 `drive`가
    부른다(`watch`). 상태는 회차 안에서 쌓인다."""

    def __init__(
        self,
        arm: Arm,
        *,
        clone: Path,
        config_dir: Path,
        watched: Watched,
        allowed_plugins: frozenset[str],
        harness_models: frozenset[str],
    ) -> None:
        self._arm = arm
        self._clone = str(clone)
        self._config_dir = config_dir
        self._watched = watched
        self._allowed_plugins = allowed_plugins
        self._harness_models = harness_models
        self._sessions: list[str] = []
        self._tools: set[str] = set()
        self._chosen: dict[str, set[str]] = {}  # 세션마다 Agent 입력이 고른 모델
        self._denied: set[str] = set()
        self._hits: list[Hit] = []
        self._start: dict[str, float] = {}
        self._end: dict[str, float] = {}
        self._mismatch_by_session: dict[str, tuple[LineCount, ...]] = {}
        self._mismatch: tuple[LineCount, ...] = ()

    def watch(self, line: str) -> bool:
        """그 줄이 허용 밖의 init 이면 참이다. 호출을 끄라는 뜻이다."""
        event = parse_event(line)
        return event is not None and _is_init(event) and init_outside(event, self._allowed_plugins)

    def __call__(self, launched: Launched) -> End | None:
        """호출 하나가 끝난 뒤의 끝. 걸린 것이 없으면 None 이다."""
        events = [e for e in map(parse_event, launched.drove.lines) if e is not None]
        if launched.session_id not in self._sessions:
            self._sessions.append(launched.session_id)
        settings = False
        for event in events:
            if _is_init(event):
                self._tools.update(t for t in _list(event.get("tools")) if isinstance(t, str))
                settings = settings or init_outside(event, self._allowed_plugins)
            for window in windows_of(event):
                self._start.setdefault(window.window, window.utilization)
                self._end[window.window] = window.utilization
        denied = denied_ids(events)
        self._denied |= denied
        uses = [u for u in tool_uses(events) if u.use_id is None or u.use_id not in denied]
        chosen = self._chosen.setdefault(launched.session_id, set())
        for use in uses:
            if use.name in AGENT_TOOLS:
                model = resolve_model(use.tool_input.get("model"), self._arm)
                if model is not None:
                    chosen.add(model)
        self._record(uses)
        self._mismatch_by_session[launched.session_id] = self._models(launched.session_id)
        self._mismatch = _summed(c for v in self._mismatch_by_session.values() for c in v)
        if settings:
            return _SETTINGS_END
        if self._mismatch:
            return End(END_NOT_MEASURED, REASON_MODEL, None)
        if self._hits:
            return End(END_NOT_MEASURED, REASON_CONTAMINATION, None)
        limit = limit_of(events)
        if limit is not None:
            return End(END_NOT_MEASURED, REASON_LIMIT, limit.resets_at)
        return None

    def _own_slugs(self) -> frozenset[str]:
        slugs: set[str] = set()
        for session_id in self._sessions:
            main, _ = transcript_files(self._config_dir, session_id)
            slugs.update(p.parent.name.casefold() for p in main)
        return frozenset(slugs)

    def _record(self, uses: Iterable[ToolUse]) -> None:
        own = self._own_slugs()
        known = KNOWN_TOOLS | self._tools
        for use in uses:
            tool = (
                use.name if use.name in known and _TOOL_FORM.fullmatch(use.name) else UNKNOWN_TOOL
            )
            for pattern in use_patterns(
                use, watched=self._watched, clone=self._clone, own_slugs=own
            ):
                hit = Hit(pattern=pattern, tool=tool)
                if hit not in self._hits:
                    self._hits.append(hit)

    def _models(self, session_id: str) -> tuple[LineCount, ...]:
        """그 세션의 기록을 그 세션이 Agent 입력으로 고른 모델까지 허용해 견준다. 방금 끝난 호출의
        세션만 읽는다. 다른 세션의 기록과 고른 모델은 그 세션의 마지막 호출 뒤로 바뀌지 않는다.
        호출마다 모든 세션을 다시 읽으면 세션을 이을수록 끝난 세션의 기록까지 거듭 읽는다."""
        main, side = transcript_counts(self._config_dir, session_id)
        allowed = {*self._harness_models, *self._chosen.get(session_id, ())}
        return model_mismatch(main, side, arm=self._arm, allowed=allowed)

    def findings(self) -> Findings:
        return Findings(
            denied_calls=len(self._denied),
            utilization_start=tuple(Window(k, v) for k, v in sorted(self._start.items())),
            utilization_end=tuple(Window(k, v) for k, v in sorted(self._end.items())),
            contamination=tuple(self._hits),
            model_mismatch=self._mismatch,
        )


def screen_for(
    place: RoundDir, arm: Arm, *, config_dir: Path, main_checkout: Path, home: Path
) -> Screen:
    """회차 하나의 `Screen`. 클론의 설정과 에이전트 파일은 지을 때 한 번 읽는다(B의 것)."""
    return Screen(
        arm,
        clone=place.clone,
        config_dir=config_dir,
        watched=watched_paths(
            main_checkout=main_checkout, home=home, place=place, config_dir=config_dir
        ),
        allowed_plugins=allowed_plugins(place.clone),
        harness_models=harness_models(place.clone, arm),
    )
