"""PreToolUse 훅(Bash). `git commit -F <파일>` 의 메시지를 그 저장소의 commit-msg 판정으로 먼저 대
보고, 걸리면 커밋을 막는다.

커밋 메시지 형식(제목 72자 등)은 pre-commit 의 commit-msg 단계(`tools/check_commit_msg.py`)가
판정한다. 그 단계는 pre-commit 단계의 검사가 모두 끝난 뒤라, 제목 하나 때문에 약 7~8분의 게이트를
한 번 더 돌았다. 세 번(일지 2026-10-13-06 의 484초, 2026-10-13-12·2026-10-13-30 의 약 7분)
있었다(대기열 222).
대기열 행은 "알린다"였지만 막는다. PreToolUse 의 additionalContext 는 도구 결과 옆에 들어가고
Claude 는 그것을 다음 모델 요청에서 읽는다(공식 hooks 문서, 2026-10-13 내려받아 글자 그대로 대
봤다: "next to the tool result", "Claude reads the reminder on the next model request"). 커밋이
게이트를 다 돈 뒤에야 모델이 알림을 보니 되풀이를 줄이지 못한다.

막는 것은 commit-msg 훅이 같은 파일을 거절할 커밋으로 좁힌다. 막는 훅은 지침으로 적은 뒤에도
어겨진 것이 확인된 뒤에만 더한다는 규약(.claude/rules/tools.md)을 이 훅은 새 금지로 읽지 않는다 —
막는 자리를 앞당길 뿐이어야 한다. 그래서 git 이 그 파일을 그대로 메시지로 쓰지 않거나 commit-msg
판정이 돌지 않을 수 있는 커밋은 보지 않는다. `--no-verify`·`-n`과 앞의 대입 `SKIP=…commit-msg…`(훅을
건너뛴다), `-e`·`--edit`(편집
뒤의 메시지가 판정된다), `--squash`·`--fixup`(git 이 제목에 접두를 붙여 통과 접두에 든다),
`--cleanup`(정리 방식에 따라 판정이 보는 첫 줄이 달라진다), `-F -`, 같은 명령의 다른 단순 명령에도
그 파일 인자가 나오는 것(먼저 쓰는 파일이라 PreToolUse 에서는 없거나 옛 내용이다), 커밋 앞에
`cd`·`pushd` 가 있는 것(상대 경로가 어디서 풀릴지 모른다)이다. `-F` 가 여럿이면 git 처럼 마지막 것만
본다. 판정 스크립트는 커밋하는 저장소의 것이다. 커밋 폴더(`cwd` 와 `git -C`)의 가장 가까운 `.git`
조상이 그 루트이고, 루트의 `.pre-commit-config.yaml` 이 `tools/check_commit_msg.py` 를 부르고 그
파일이 있을 때만 판정한다. 판정은 옮겨 적지 않고 그 스크립트를 자식 프로세스로 띄워 받는다. 같은
판정이 정의로 서고, 훅끼리 import 하지 않는 규약(.claude/rules/tools.md)도 지킨다. 워크트리
세션에서는 훅 파일이 주 체크아웃의 것이어도 판정은 그 워크트리의 스크립트가 한다.

찾는 것. 명령을 shlex 로 낱말로 나누고 제어 연산자(`&&`, `;`, `|`, 줄바꿈 등)에서 가른 단순
명령마다, 앞의 변수 대입을 벗긴 첫 낱말이 `git` 이고 전역 옵션 뒤의 하위 명령이 `commit` 이면 그
인자에서 `-F <파일>`·`-F<파일>`·`--file <파일>`·`--file=<파일>`·묶은 짧은 옵션(`-aF <파일>`)을
찾는다. 값을 받는 다른 옵션(`-m`, `-c`, `-C`, `-t`, `--author` 등)의 값은 건너뛰고, `--` 뒤는 보지
않는다. 줄 끝 역슬래시로 이은 줄은 한 줄로 본다. 파일은 커밋 폴더에서 풀고, `~` 와 Git Bash 의
`/c/…` 표기를 받는다.

못 보는 것(모두 지나간다): `-F -`(heredoc 이나 파이프로 넘긴 메시지)와 `-m` 의 메시지, 위에서 보지
않는다고 적은 커밋, 변수·치환이 든 경로, shlex 가 거절하는 명령(짝 없는 따옴표. heredoc 본문의
작은따옴표도 그렇다), `git` 을 다른 이름으로 부르는 것(`command git`, 전체 경로). 자식이 시간
제한(10초)을 넘기거나 판정 문장 없이 끝나도 지나간다.
"""

from __future__ import annotations

import json
import os
import posixpath
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import NamedTuple, TypedDict

CHECKER = "tools/check_commit_msg.py"
PRE_COMMIT_CONFIG = ".pre-commit-config.yaml"
CHECK_TIMEOUT = 10.0
_CONTROL = re.compile(r"^[;&|()<>\n]+$")
_ASSIGNMENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
# git 의 전역 옵션 가운데 값을 다음 낱말로 받는 것.
_GLOBAL_WITH_VALUE = frozenset({"-C", "-c", "--git-dir", "--work-tree", "--namespace"})
# `git commit` 의 짧은 옵션 가운데 값을 받는 것. 값은 붙여 쓰거나 다음 낱말이다.
_SHORT_WITH_VALUE = frozenset("mcCtF")
# 값을 붙여서만 받는 짧은 옵션(`-S[<keyid>]`, `-u[<mode>]`). 그 뒤의 글자는 값이다.
_SHORT_WITH_ATTACHED = frozenset("Su")
# 이 짧은 옵션이 있으면 보지 않는다(독스트링). `-n` 은 `--no-verify`, `-e` 는 `--edit` 다.
_SHORT_UNJUDGED = frozenset("ne")
_LONG_UNJUDGED = frozenset({"--no-verify", "--edit", "--squash", "--fixup", "--cleanup"})
_LONG_WITH_VALUE = frozenset(
    {
        "--message",
        "--reuse-message",
        "--reedit-message",
        "--fixup",
        "--squash",
        "--author",
        "--date",
        "--template",
        "--cleanup",
        "--trailer",
        "--pathspec-from-file",
    }
)
_DIRECTORY_CHANGERS = frozenset({"cd", "pushd", "popd"})
_UNRESOLVABLE = re.compile(r"[$`*?\[]")
_MSYS_DRIVE = re.compile(r"^/([A-Za-z])(?=/|$)")
_ABSOLUTE = re.compile(r"^(?:/|[A-Za-z]:/)")


class ToolInput(TypedDict, total=False):
    command: str


class HookPayload(TypedDict, total=False):
    """Claude Code 가 stdin 으로 주는 훅 입력 중 이 훅이 읽는 부분."""

    tool_input: ToolInput
    cwd: str


class MessageFile(NamedTuple):
    """커밋 하나의 메시지 파일 인자와 그 커밋의 `git -C` 폴더(없으면 빈 문자열)."""

    directory: str
    file: str


def message_files(command: str) -> list[MessageFile]:
    """판정할 `git commit` 마다 마지막 `-F`·`--file` 의 파일 인자. 보지 않는 커밋은 뺀다."""
    # 줄 끝 역슬래시는 줄을 잇는다. 그대로 두면 shlex 가 이스케이프된 줄바꿈을 값으로 읽는다.
    lexer = shlex.shlex(command.replace("\\\n", " "), posix=True, punctuation_chars=";&|()<>\n")
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    lexer.commenters = ""
    try:
        tokens = list(lexer)
    except ValueError:
        return []
    commands: list[list[str]] = [[]]
    for token in tokens:
        if _CONTROL.match(token) is None:
            commands[-1].append(token)
        elif commands[-1]:
            commands.append([])
    found: list[MessageFile] = []
    for index, words in enumerate(commands):
        message = _commit_message(words)
        if message is None:
            continue
        others = commands[:index] + commands[index + 1 :]
        if any(other and other[0] in _DIRECTORY_CHANGERS for other in commands[:index]):
            continue
        if any(message.file in other for other in others):
            continue
        found.append(message)
    return found


def _commit_message(words: list[str]) -> MessageFile | None:
    index = 0
    while index < len(words) and _ASSIGNMENT.match(words[index]):
        name, _, value = words[index].partition("=")
        if name == "SKIP" and "commit-msg" in value.split(","):
            return None
        index += 1
    if index >= len(words) or words[index] != "git":
        return None
    index += 1
    directory = ""
    while index < len(words) and words[index].startswith("-"):
        option = words[index]
        index += 1
        if option in _GLOBAL_WITH_VALUE and index < len(words):
            if option == "-C":
                directory = posixpath.join(directory, words[index]) if directory else words[index]
            index += 1
    if index >= len(words) or words[index] != "commit":
        return None
    file = _last_file_argument(words[index + 1 :])
    if file is None or file == "-":
        return None
    return MessageFile(directory, file)


def _last_file_argument(arguments: list[str]) -> str | None:
    """마지막 `-F` 의 값. 없거나 보지 않는 커밋(`_SHORT_UNJUDGED`, `_LONG_UNJUDGED`)이면 None."""
    file: str | None = None
    index = 0
    while index < len(arguments):
        word = arguments[index]
        index += 1
        if word == "--":
            break
        if word.startswith("--"):
            name, has_value, value = word.partition("=")
            if name in _LONG_UNJUDGED:
                return None
            if name == "--file":
                if has_value:
                    file = value
                elif index < len(arguments):
                    file = arguments[index]
                    index += 1
            elif name in _LONG_WITH_VALUE and not has_value:
                index += 1
            continue
        if not word.startswith("-") or word == "-":
            continue
        for position, flag in enumerate(word[1:], start=1):
            if flag in _SHORT_UNJUDGED:
                return None
            if flag in _SHORT_WITH_ATTACHED:
                break
            if flag in _SHORT_WITH_VALUE:
                value = word[position + 1 :]
                if not value and index < len(arguments):
                    value = arguments[index]
                    index += 1
                if flag == "F" and value:
                    file = value
                break
    return file


def _native(path: str) -> str:
    """Git Bash 의 `/c/…` 를 `C:/…` 로, 역슬래시를 슬래시로."""
    text = path.replace("\\", "/")
    msys = _MSYS_DRIVE.match(text)
    return f"{msys.group(1).upper()}:{text[2:]}" if msys else text


def resolve(path: str, cwd: str, home: str) -> str | None:
    """인자를 `cwd` 에서 푼 경로. 변수·치환·글롭이 들었으면 None."""
    if _UNRESOLVABLE.search(path):
        return None
    if path == "~" or path.startswith("~/"):
        return posixpath.normpath(f"{_native(home)}/{path[2:]}")
    text = _native(path)
    if _ABSOLUTE.match(text):
        return posixpath.normpath(text)
    return posixpath.normpath(f"{_native(cwd)}/{text}")


def checker_for(directory: str) -> str | None:
    """`directory` 에서 커밋하면 commit-msg 단계가 돌릴 판정 스크립트. 그 저장소의 pre-commit
    설정이 그것을 부르지 않거나 파일이 없으면 None."""
    parts = directory.rstrip("/").split("/")
    for end in range(len(parts), 0, -1):
        root = "/".join(parts[:end]) or "/"
        if not os.path.exists(f"{root}/.git"):
            continue
        checker = f"{root}/{CHECKER}"
        try:
            config = Path(root, PRE_COMMIT_CONFIG).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return None
        return checker if CHECKER in config and os.path.isfile(checker) else None
    return None


def problems_of(path: str, checker: str, timeout: float = CHECK_TIMEOUT) -> list[str]:
    """`checker` 가 그 파일에 내는 문장들. 통과하거나 판정 문장 없이 끝나거나 `timeout` 초를
    넘기면 빈다."""
    environment = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    try:
        result = subprocess.run(
            [sys.executable, checker, path],
            capture_output=True,
            env=environment,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if result.returncode != 1:
        return []
    return result.stdout.decode("utf-8", "replace").splitlines()


def deny_reason(command: str, cwd: str, home: str) -> str | None:
    """판정할 커밋의 메시지 파일이 그 저장소의 commit-msg 판정에 걸리면 막는 이유, 아니면 None."""
    if "commit" not in command:
        return None
    for message in message_files(command):
        directory = resolve(message.directory or ".", cwd, home)
        path = None if directory is None else resolve(message.file, directory, home)
        if directory is None or path is None or not os.path.isfile(path):
            continue
        checker = checker_for(directory)
        problems = [] if checker is None else problems_of(path, checker)
        if problems:
            return (
                f"커밋 메시지 파일 `{message.file}` 이 commit-msg 훅({CHECKER})의 판정에"
                f" 걸린다: {' / '.join(problems)}. 이대로 치면 pre-commit 단계의 검사(약 8분)를"
                " 모두 돈 뒤 commit-msg 단계에서 막혀 게이트를 한 번 더 돈다(대기열 222)."
                " 파일의 제목을 고치고 다시 친다."
            )
    return None


def main() -> int:
    # stdin 은 바이트로. 이유는 .claude/rules/tools.md(대기열 25).
    payload: HookPayload = json.load(sys.stdin.buffer)
    command = payload.get("tool_input", {}).get("command")
    cwd = payload.get("cwd")
    if command is None or cwd is None:
        return 0
    reason = deny_reason(command, cwd, str(Path.home()))
    if reason is None:
        return 0
    output = {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",
        "permissionDecisionReason": reason,
    }
    sys.stdout.buffer.write(json.dumps({"hookSpecificOutput": output}).encode("utf-8"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
