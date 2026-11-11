"""PostToolUse 훅(Bash). `pyright` 에 파일·폴더 인자를 줬는데 그 경로가 pyright 가 기본으로 분석하지
않는 자리(점으로 시작하는 폴더, `node_modules`, `__pycache__` 아래)에 있으면, 그 호출의
`0 errors` 는 판정이 아니니 사본을 점 없는 폴더(`tests/` 아래)에 두고 `--outputjson` 의
`summary.filesAnalyzed` 를 보라는 계기를 세션·에이전트마다 한 번 컨텍스트에 넣는다.

왜. `uv run pyright <.scratch 아래 프로브>` 가 `0 errors` 를 냈는데 `filesAnalyzed` 가 0 이었다
(대기열 431, 5회차부터 세어 8회차). 그 지침(`CLAUDE.md` 환경 함정의 "검사 도구가 내가 생각하는 것을
실제로 봤는지 먼저 확인한다"와 `docs/constitution/operations.md` 환경 규약 상세의 pyright 프로브
항목)은 치기 전에 따르지 않았고, 모델은 바로 다음 호출에서 스스로 잡아 결론에 쓰지 않았다. 사건마다
스스로 잡았지만 번번이 한 호출을 헛돌렸으므로, 호출 결과와 함께 짚는 계기 훅이다. 막지 않는다.
틀린 호출도 돌아와 `filesAnalyzed` 를 보게 하는 편이 낫고, 판정은 글로 가르는 것이라 거짓 양성이
있다(`.claude/rules/tools.md` 의 계기·막는 훅 가름).

무엇이 분석되지 않는가. 이 브랜치에서 pyright 1.1.414 에 `uv run pyright --outputjson <경로>` 를
파일 하나씩 쳐서 `summary.filesAnalyzed` 를 손으로 봤다. 점 폴더 아래의 파일(`.scratch/_pp/a.py`)과
폴더 인자(`.scratch/_pp`), `node_modules` 아래, `__pycache__` 아래는 0 이었다. `[tool.pyright]` 의
`include`(`src`·`tests`·`tools`) 밖이지만 점 없는 폴더의 파일(`docs/_pp/a.py`)과 폴더 인자
(`docs/_pp`), 저장소 밖 파일은 1 이었다. 곧 `include` 는 인자 없이 칠 때의 범위이고, 인자로 명시한
경로에는 기본 제외(`**/node_modules`, `**/__pycache__`, `**/.*`)만 걸린다. 대기열 431 은 "검사 범위
밖이거나 점 디렉터리 아래"라고 적었으나 앞 절반은 틀렸고, 이 훅은 뒤 절반만 짚는다. 점으로
시작하는 파일 이름(`tests/.pp_dot_probe.py`)도 0 이었고, 저장소 밖 점 폴더 아래의 파일은 1
이었다. 프로브로 커밋하지 않은 손으로 본 값이라 쟀다고 적지 않는다.

판정. 도구가 Bash 이고 `tool_input.command` 가 문자열이면, 제어
연산자(`|`·`;`·`&`·`&&`·`||`·줄바꿈)로 가른 단순 명령마다 `pyright` 를 부른 명령인지 본다. 명령
낱말이어야 한다. 낱말 앞에는 셸 예약어(`if`·`then`·`do`·`!`·`{` 등)와 여는 괄호, 래퍼
(`uv run`·`uv tool run` 과 그 옵션, `uvx`, `python -m`, `env` 와 그 옵션 값(`-u NAME`), `npx`,
`time`, `sudo`, 환경 변수 대입)만 올 수 있고, 낱말의 이름(경로의 마지막 토막, `.exe`·`.cmd`·
`.bat` 제외)이 `pyright` 와 같아야 한다. 래퍼가 작업 폴더를 바꾸는 옵션(`--directory`, `--chdir`,
`-C`)을 앞에 주면 그 호출은 판정하지 않는다. `pyright` 뒤의 옵션이 아닌 낱말이 경로 인자다. 값을
받는 옵션(`pyright --help` 1.1.414 의 `--createstub`, `--pythonpath`, `-v`·`--venvpath`, `--level`
등)의 값과 리다이렉트 (`>`·`2>`·`>>`·`<` 와 대상, `2>&1`)는 인자가 아니다. `#` 으로 시작하는
낱말부터는 주석이라 버린다(낱말 안의 `#` 은 주석이 아니다). `$`·백틱·괄호가 든 낱말과
`~` 로 시작하는 낱말은 판정하지 않는다. 경로는 프로젝트 루트(작업 폴더에서 위로 올라가 처음
만나는 `[tool.pyright]` 가 든 `pyproject.toml` 이나 `pyrightconfig.json` 이 있는 폴더) 기준으로
바꾼다. 절대 경로(Git Bash 꼴의 `/c/…` 는 `C:/…` 로 바꿔 읽는다)와 작업 폴더 기준의 상대
경로(`..` 포함)를 루트 기준으로 바꾸며, 이 저장소의 워크트리는 `.claude/worktrees/<이름>/` 아래라
절대 경로가 `.claude` 를 품지만 루트 기준으로는 아니므로 분석된다. 바꾼 경로에 `.` 로 시작하는
토막(`.` 과 `..` 제외)이나 `node_modules`, `__pycache__` 가 있으면 알린다. 막지 않는 계기라 셸
파서를 따르지 않고 글로 가른다(백슬래시는 슬래시로 바꾸고 `shlex` 로 나눈다). 그 값은 아래 못
보는 것이다.

한 번. 표지는 `tools/hook_journal_evidence.py` 와 같은 모양이다(훅은 서로 import 하지 않는다,
`.claude/rules/tools.md`). 임시 폴더(`tempfile.gettempdir()`) 아래 `STATE_DIR` 에 세션 ID 와
`agent_id` 의 해시로 빈 파일을 `O_EXCL` 로 만든다. 세션을 모르거나 표지를 쓰지 못하면 호출마다
알린다. 한 세션에서 두 번째 알림은 첫 알림이 컨텍스트에 남아 있다고 기대하고 생략한다.

못 보는 것:
- PowerShell 로 친 `pyright`. 등록 매처에 PowerShell 이 없다(Bash 호출마다 파이썬이 한 번 뜨는 값은
  PowerShell 호출에는 붙이지 않았다).
- `--project`·`-p` 를 쓴 호출과 작업 폴더를 바꾸는 래퍼 옵션(`uv run --directory`, `env -C`)을
  쓴 호출. 제외 규칙의 기준 폴더가 바뀌어 루트를 알 수 없고, 그 호출은 판정하지 않고 지나간다.
- 셸 변수나 명령 치환이 든 경로(`pyright "$f"`, `pyright $(ls .scratch)`, 백틱)와 괄호가 든
  낱말. 건너뛰므로 셸이 확장한 결과는 보지 못한다(거짓 음성). `(…)` 묶음 안의 호출은 마지막 인자에
  닫는 괄호가 붙어 그 인자를 건너뛰고 앞 인자만 본다. 글롭(`pyright .scratch/*.py`)은 글자 그대로
  점 폴더로 읽어 알린다.
- 주석 글 안의 `;`·`&`. 글 가르기가 주석을 벗기기 전에 그 자리에서 명령을 갈라, 주석 글 뒤쪽이
  명령으로 읽힌다(거짓 양성).
- 이스케이프한 공백이 든 경로(`pyright .scratch/a\\ b.py`). 백슬래시를 슬래시로 바꾸어 `a/` 와
  `b.py` 로 갈라 읽는다.
- 래퍼 앞의 `cd` 로 바뀐 작업 폴더. `cd .scratch && pyright x.py` 는 페이로드의 `cwd`(호출 앞의
  작업 폴더)를 기준으로 `x.py` 를 읽어 분석되는 경로로 본다(거짓 음성).
- 래퍼 앞에 옵션 값이 든 알려지지 않은 래퍼(`uv run --foo bar pyright`)와 목록 밖의 래퍼(`xargs`,
  `bash -c "pyright …"`). 낱말 앞이 목록 밖이면 `pyright` 를 부른 명령으로 보지 않는다.
- 저장소 밖 경로와 홈(`~`) 아래. 손으로 봤을 때 저장소 밖 파일은 점 폴더 아래여도 분석됐고(1)
  알리지 않는다.
- 따옴표가 닫히지 않은 명령. `shlex` 가 실패하면 공백으로 나누고 따옴표를 벗겨 본다.
- 이 알림이 모델에게 닿는지. 메인 세션과 서브에이전트 모두 재지 않았다(서브에이전트는 입력의
  `agent_id` 로 표지만 가른다).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import sys
import tempfile
from collections.abc import Iterable
from pathlib import Path, PureWindowsPath
from typing import TypedDict

BASH = "Bash"
STATE_DIR = "agent-os-pyright-unchecked-path"
# 알림의 첫 문장. 알림이 모델에게 닿는지 잴 때 모델이 옮겼는지 볼 문구다.
LEAD = "pyright 가 분석하지 않는 경로를 받았다"
_BODY = (
    "{lead}. 넘긴 경로 {paths} 는 점으로 시작하는 폴더, `node_modules`, `__pycache__` 아래라"
    " pyright 가 기본으로 분석하지 않는다. 이 호출이 낸 `0 errors` 는 그 파일을 검사한 결과가"
    " 아니어서 판정이 아니다. 사본을 점 없는 폴더(`tests/` 아래)에 두고 `--outputjson` 의"
    " `summary.filesAnalyzed` 가 0 이 아닌지 본다. `include` 밖이어도 점 없는 폴더의 경로는"
    " 명시하면 분석된다(손으로 봤다). 근거는 `docs/constitution/operations.md` 환경 규약 상세의"
    " pyright 프로브 항목이다. 이 알림은 세션·에이전트마다 한 번이다."
)
SHOWN_PATHS = 3
UNCHECKED_NAMES = frozenset({"node_modules", "__pycache__"})
CONFIG_NAMES = ("pyrightconfig.json",)

_CONTINUATION = re.compile(r"\\\r?\n")
# `2>&1`, `>&2` 의 `&` 는 제어 연산자가 아니다. 나누기 전에 지운다. 앞에 숫자가 오지 않게
# 막아 숫자만 이어진 긴 낱말에서 시작 자리마다 끝까지 되읽는 제곱 시간을 피한다(손으로 봤다:
# 숫자 4만 자에서 막지 않은 판 13초, 막은 판 0.00초).
_FD_DUP = re.compile(r"(?<!\d)\d*[<>]&\d+")
_SEPARATOR = re.compile(r"\|\||&&|[|;&\n]")
# 리다이렉트: 연산자만 있는 낱말(대상이 다음 낱말)과 대상이 붙은 낱말(`>out.txt`).
_REDIRECT_ONLY = re.compile(r"^\d*[<>]{1,2}\|?$")
_REDIRECT_ATTACHED = re.compile(r"^\d*[<>]{1,2}\|?\S")
_ENV_ASSIGNMENT = re.compile(r"^[A-Za-z_]\w*=")
_PYTHON = re.compile(r"^python[\d.]*$")
# pyright 명령 낱말 앞에 올 수 있는 래퍼와, 값을 따로 받는 래퍼 옵션.
_WRAPPERS = frozenset(
    {"uv", "run", "tool", "uvx", "env", "npx", "time", "sudo", "exec", "command", "nice", "py"}
)
_WRAPPER_VALUE_OPTIONS = frozenset(
    {"--project", "--env-file", "--python", "--with", "--group", "--extra", "-p", "-u", "--unset"}
)
# 작업 폴더를 바꾸는 래퍼 옵션. 이 옵션이 pyright 앞에 있으면 경로의 기준 폴더를 알 수 없다.
_CWD_OPTIONS = frozenset({"--directory", "--chdir", "-C"})
_CWD_OPTION_PREFIXES = ("--directory=", "--chdir=")
# 명령 낱말 앞에 올 수 있는 셸 예약어와 묶음 기호(`if x; then pyright …`, `! pyright …`).
_SHELL_PREFIXES = frozenset({"if", "then", "elif", "else", "do", "while", "until", "!", "{"})
# 셸이 확장하는 글자(변수, 명령 치환, 백틱)와 괄호가 든 낱말은 경로로 읽지 않는다.
_SHELL_SYNTAX = re.compile(r"[$`()]")
# Git Bash 가 주는 `/c/…` 꼴의 절대 경로.
_GIT_BASH_DRIVE = re.compile(r"^/([A-Za-z])(?:/|$)")
# pyright 의 옵션 가운데 값을 따로 받는 것(`pyright --help`, 1.1.414). `--threads` 는 값이 선택이라
# 따로 본다.
_PYRIGHT_VALUE_OPTIONS = frozenset(
    {
        "--createstub",
        "--pythonpath",
        "--pythonplatform",
        "--pythonversion",
        "-t",
        "--typeshedpath",
        "-v",
        "--venvpath",
        "--level",
        "--verifytypes",
    }
)
_PROJECT_OPTIONS = frozenset({"-p", "--project"})


class ToolInput(TypedDict, total=False):
    command: object


class HookPayload(TypedDict, total=False):
    """Claude Code 가 stdin 으로 주는 훅 입력 중 이 훅이 읽는 부분. 값이 기대한 꼴이 아니어도
    `context_for` 가 런타임에 다시 본다."""

    tool_name: str
    tool_input: ToolInput
    cwd: object
    session_id: str
    agent_id: str


def _tokens(segment: str) -> list[str]:
    """단순 명령 하나를 낱말로 나눈다. 따옴표가 닫히지 않아 `shlex` 가 실패하면 공백으로 나누고
    따옴표를 벗긴다. `#` 으로 시작하는 낱말부터는 주석이라 버린다."""
    try:
        tokens = shlex.split(segment, posix=True)
    except ValueError:
        tokens = [token.strip("'\"") for token in segment.split()]
    for index, token in enumerate(tokens):
        if token.startswith("#"):
            return tokens[:index]
    return tokens


def _without_redirects(tokens: list[str]) -> list[str]:
    kept: list[str] = []
    skip_target = False
    for token in tokens:
        if skip_target:
            skip_target = False
        elif _REDIRECT_ONLY.match(token):
            skip_target = True
        elif not _REDIRECT_ATTACHED.match(token):
            kept.append(token)
    return kept


def _is_pyright(token: str) -> bool:
    name = token.rsplit("/", 1)[-1].lower()
    for suffix in (".exe", ".cmd", ".bat"):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    return name == "pyright"


def _pyright_index(tokens: list[str]) -> int | None:
    """명령 낱말 `pyright` 의 자리. 그 앞이 래퍼뿐이 아니면 None."""
    skip_value = False
    for index, token in enumerate(tokens):
        if skip_value:
            skip_value = False
            continue
        # 서브셸의 여는 괄호(`(uv run pyright …)`)와 셸 예약어는 명령 낱말이 아니다.
        token = token.lstrip("(")
        if not token or token in _SHELL_PREFIXES:
            continue
        if _is_pyright(token):
            return index
        if token in _CWD_OPTIONS or token.startswith(_CWD_OPTION_PREFIXES):
            return None
        name = token.rsplit("/", 1)[-1].lower()
        name = name.removesuffix(".exe")
        if token in _WRAPPER_VALUE_OPTIONS:
            skip_value = True
        elif (
            token.startswith("-")
            or name in _WRAPPERS
            or _PYTHON.match(name)
            or _ENV_ASSIGNMENT.match(token)
        ):
            continue
        else:
            return None
    return None


def _path_arguments(tokens: list[str]) -> list[str]:
    """`pyright` 낱말 뒤의 경로 인자. `--project`·`-p` 를 쓰면 판정하지 않는다."""
    paths: list[str] = []
    skip_value = False
    after_dashes = False
    for index, token in enumerate(tokens):
        if skip_value:
            skip_value = False
        elif after_dashes:
            paths.append(token)
        elif token == "--":
            after_dashes = True
        elif token in _PROJECT_OPTIONS or token.startswith(("--project=", "-p=")):
            return []
        elif token in _PYRIGHT_VALUE_OPTIONS:
            skip_value = True
        elif token == "--threads":
            following = tokens[index + 1 : index + 2]
            skip_value = bool(following) and following[0].isdigit()
        elif not token.startswith("-"):
            paths.append(token)
    return paths


def pyright_paths(command: str) -> list[str]:
    """명령 글에서 `pyright` 를 부른 단순 명령마다 경로 인자를 모은다(백슬래시는 슬래시로
    바꾼다)."""
    text = _CONTINUATION.sub(" ", command).replace("\\", "/")
    text = _FD_DUP.sub(" ", text)
    paths: list[str] = []
    for segment in _SEPARATOR.split(text):
        tokens = _without_redirects(_tokens(segment))
        start = _pyright_index(tokens)
        if start is not None:
            arguments = _path_arguments(tokens[start + 1 :])
            paths.extend(arg for arg in arguments if not _SHELL_SYNTAX.search(arg))
    return paths


def _has_pyright_config(directory: Path) -> bool:
    try:
        if any((directory / name).is_file() for name in CONFIG_NAMES):
            return True
        pyproject = directory / "pyproject.toml"
        if pyproject.is_file():
            return "[tool.pyright]" in pyproject.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return False


def find_root(cwd: str) -> Path | None:
    """`cwd` 에서 위로 올라가 pyright 설정이 처음 나오는 폴더(프로젝트 루트). 없으면 None."""
    if not cwd:
        return None
    try:
        start = Path(cwd)
        if not start.is_dir():
            return None
        return next((d for d in (start, *start.parents) if _has_pyright_config(d)), None)
    except OSError:
        return None


def _collapse(parts: Iterable[str]) -> tuple[str, ...] | None:
    """`.` 를 지우고 `..` 로 앞 토막을 지운다. 처음보다 위로 올라가면 None."""
    kept: list[str] = []
    for part in parts:
        if part == "..":
            if not kept:
                return None
            kept.pop()
        elif part not in ("", "."):
            kept.append(part)
    return tuple(kept)


def root_relative(arg: str, cwd: str | None, root: Path | None) -> tuple[str, ...] | None:
    """경로 인자를 루트 기준 토막으로 바꾼다. 루트 밖이거나 풀 수 없으면 None. 홈(`~`)은 저장소
    밖이라 풀지 않고, Git Bash 꼴의 `/c/…` 는 `C:/…` 로 바꿔 읽는다."""
    if arg.startswith("~"):
        return None
    drive = _GIT_BASH_DRIVE.match(arg)
    if drive:
        arg = f"{drive.group(1).upper()}:/{arg[drive.end() :]}"
    path = PureWindowsPath(arg)
    if path.drive and not path.root:
        return None
    if path.anchor:
        if root is None:
            return None
        collapsed = _collapse(path.parts[1:])
        if collapsed is None:
            return None
        try:
            return PureWindowsPath(path.anchor, *collapsed).relative_to(PureWindowsPath(root)).parts
        except ValueError:
            return None
    if cwd is None or root is None:
        return _collapse(path.parts)
    try:
        base = PureWindowsPath(cwd).relative_to(PureWindowsPath(root)).parts
    except ValueError:
        return None
    return _collapse((*base, *path.parts))


def _is_unchecked(arg: str, cwd: str | None, root: Path | None) -> bool:
    parts = root_relative(arg, cwd, root)
    if parts is None:
        return False
    return any(part.startswith(".") or part.lower() in UNCHECKED_NAMES for part in parts)


def unchecked_paths(command: str, cwd: str | None) -> list[str]:
    """`command` 의 pyright 경로 인자 가운데 pyright 가 분석하지 않는 자리의 것(슬래시 꼴)."""
    arguments = pyright_paths(command)
    if not arguments:
        return []
    root = find_root(cwd) if cwd else None
    return [arg for arg in arguments if _is_unchecked(arg, cwd, root)]


def context_for(payload: HookPayload) -> str | None:
    """분석하지 않는 경로를 받았으면 컨텍스트 문장, 아니면 None."""
    if payload.get("tool_name") != BASH:
        return None
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return None
    command = tool_input.get("command")
    if not isinstance(command, str):
        return None
    cwd = payload.get("cwd")
    found = unchecked_paths(command, cwd if isinstance(cwd, str) and cwd else None)
    if not found:
        return None
    shown = ", ".join(f"`{path}`" for path in found[:SHOWN_PATHS])
    if len(found) > SHOWN_PATHS:
        shown += f" 외 {len(found) - SHOWN_PATHS}개"
    return _BODY.format(lead=LEAD, paths=shown)


def marker_name(session_id: str, agent_id: str) -> str:
    """세션·에이전트 하나의 표지 파일 이름. 둘의 해시다(`tools/launch_hook.py` 의 모양)."""
    joined = f"{session_id}\0{agent_id}"
    return hashlib.sha256(joined.encode("utf-8", "surrogatepass")).hexdigest()


def claim_first(name: str, directory: Path) -> bool:
    """`directory` 에 표지 `name` 을 이 호출이 처음 만들었으면 True, 이미 있으면 False. 만들지
    못하면 True 다(`tools/hook_journal_evidence.py` 의 `claim_first` 와 같다)."""
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
