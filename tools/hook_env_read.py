"""PreToolUse 훅(Bash|Grep). `.env` 를 읽는 명령과 `.env` 를 경로로 준 Grep 을 막는다.

이 저장소의 `permissions.deny` 는 모든 위치의 `.env` 에 Read·Edit 를 막고(`//**/.env`. `./` 는
세션 cwd 기준이라 워크트리 세션에서 주 체크아웃에 닿지 않았다), PowerShell 의 `Get-Content`·
`Select-String`(별칭은 정규화된다)을 막는다(`.scratch/harness/probes/env_deny_probe.md`). Bash
규칙은 호출의 모양만 맞춰 grep 의 인자 자리를 못 보므로 Bash 는 이 훅이 맡는다. 2026-09-28
하네스 감사에서 서브에이전트의 grep 한 번에 `.env` 의 키 값이 도구 출력에 실렸다(대기열 43).
실패가 조용하고(실린 뒤에야 안다) 패턴이 고정돼 첫 사건에서 막는 훅으로 갔다
(`.claude/rules/tools.md`). Grep 도구는 glob 없이 훑을 때는 숨김·gitignore 파일을 건너뛰지만,
경로로 `.env` 를 주거나 glob(`*`·`.*`·`.env*`)이 있으면 읽는다(2026-09-28 가짜 `.env` 로 실측).
`.env.example` 은 읽어도 된다. 파일 이름은 대소문자를 가리지 않는다(Windows 는 `.ENV` 도 같은
파일이다).

Bash 에서 막는 모양 셋.
- 읽는 명령의 인자에 `.env` 파일. `cat .env`, `grep KEY .env`, `sed -n 1p ../.env`, `source .env`,
  `diff .env x`, `find … -exec cat {} +`, `git diff --no-index .env x`. 셸이 `.env` 로 펼칠 glob
  (`cat .e*`)도 — `*` 는 점파일을 빼므로 `cat *` 은 아니다. `bash -c "…"`·`eval`·`$(…)`·백틱·`<(…)`
  안의 명령도 한 겹씩 풀어 본다.
- 입력 리다이렉션 `< .env`.
- 저장소 전체를 훑는 grep. `grep -r` 이 경로 없이, 또는 `.`·`..`·절대 경로·`$PWD` 같은 루트 표기로
  돌면서 `--exclude=.env*` 도 `--include=*.py` 같은 좁힘도 없다. grep 은 숨김 파일을 건너뛰지 않는다
  (`*` 는 셸이 점파일을 빼므로 훑기가 아니다). rg 는 기본으로 숨김·gitignore 파일을 건너뛰므로
  `--hidden` 과 `--no-ignore`(`-u` 하나가 `--no-ignore`, `-uu` 가 둘 다)가 함께 있고 `-g '!.env*'`
  도 `-t py` 같은 좁힘도 없을 때만 같은 판정이다. 루트인지는 페이로드의 `cwd` 기준으로 푼 경로가
  cwd·`CLAUDE_PROJECT_DIR` 이거나 그 안에 `.env` 파일이 있는지(이름만 본다)로 가른다. `.`·`..` 는
  조각마다의 cwd 를 모르므로 언제나 루트로 본다 — `cd src && grep -r x .` 는 오탐이다.
토큰은 shlex 로 나눈다 — 인용 안의 `|` 는 분리자가 아니고 `cat ".env"` 의 인자는 보인다. grep·sed·
awk 류의 첫 위치 인자는 패턴이라 파일로 보지 않는다(`grep .env .gitignore` 는 `.gitignore` 를 읽는
것이다). 리다이렉션 대상은 인자가 아니다(`cat x > .env` 는 쓰기다).
못 보는 것: 변수 간접 참조(`for f in .env*; do cat "$f"`), 다른 명령이 넘긴 인자(`ls -a | xargs
cat`), 언어 안의 읽기(`python -c "open('.env')"`), `cp .env x` 뒤의 `cat x`, `uv run --env-file
.env` 뒤의 `printenv`(그 명령은 LLM 테스트의 사전이라 막지 않는다), `.env` 가 없는 하위 디렉터리를
훑는 `grep -r x sub/`, 백슬래시 경로(`C:\\x\\.env` — shlex 가 이스케이프로 읽는다), 래퍼 스크립트
안의 읽기, PowerShell 도구(권한 deny 가 `Get-Content`·`Select-String` 과 그 별칭만 막고
`[IO.File]::ReadAllText` 같은 읽기는 지나간다 — 2026-09-29 가짜 `.env` 로 실측), `.env` 밖의 비밀
파일(사용자 설정의 env 값 등).
에이전트 층의 두 장치(권한 deny, 이 훅)가 못 보는 것은 셋째 층이 맡는다. 키 자체다 — 사용 한도를 건
개발용 키만 두고, 도구 출력에 실린 키는 회전한다(`docs/constitution/operations.md` 가드레일).
"""

from __future__ import annotations

import fnmatch
import json
import os
import re
import shlex
import sys
from typing import NamedTuple, TypedDict

READERS = frozenset(
    {
        "cat", "tac", "head", "tail", "less", "more", "bat",
        "grep", "egrep", "fgrep", "rg", "ag", "ack",
        "sed", "awk", "gawk", "cut", "tr", "sort", "uniq", "nl",
        "strings", "xxd", "od", "hexdump", "base64",
        "diff", "cmp", "comm", "paste",
        "source", ".",
    }
)  # fmt: skip
PATTERN_COMMANDS = frozenset({"grep", "egrep", "fgrep", "rg", "ag", "ack", "sed", "awk", "gawk"})
SHELLS = frozenset({"bash", "sh", "zsh", "dash"})
GIT_READING_SUBCOMMANDS = frozenset({"diff", "show", "grep", "blame"})
ALLOWED_ENV_FILES = frozenset({".env.example"})
_RESERVED = frozenset(
    {"if", "then", "else", "elif", "fi", "do", "done", "while", "until", "for", "{", "}", "!"}
)
_WRAPPERS = frozenset({"sudo", "command", "exec", "time", "nohup", "env", "builtin"})
_ROOTISH = frozenset({".", "./", "..", "../"})
# `.env`, `.env.local`, `../.env`, `$PWD/.env`, `C:/x/.env`. `.envrc`·`config.env` 는 아니다.
_ENV_FILE = re.compile(r"(?<![\w.-])(?:[\w.:~${}-]+/)*(\.env(?:\.[\w-]+)?)(?![\w.-])", re.I)
_HEREDOC_OPENER = re.compile(r"<<(-?)\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\2")
_ASSIGNMENT = re.compile(r"^[A-Za-z_]\w*=")
_SHORT_CLUSTER = re.compile(r"^-([A-Za-z.]+)\d*$")
# 값을 하나 더 먹는 옵션. 그 값은 경로도 패턴도 아니다.
_GREP_VALUE_OPTIONS = frozenset(
    {"-A", "-B", "-C", "-m", "-e", "-f", "-d", "-D", "--include", "--exclude", "--exclude-dir"}
)
_RG_VALUE_OPTIONS = frozenset(
    {
        "-A", "-B", "-C", "-m", "-e", "-f", "-g", "-t", "-T", "-E", "-j", "-M",
        "--after-context", "--before-context", "--context", "--max-count", "--regexp", "--file",
        "--glob", "--iglob", "--type", "--type-not", "--type-add", "--encoding", "--threads",
        "--max-columns", "--pre", "--sort", "--sortr", "--color", "--colors", "--max-depth",
    }
)  # fmt: skip
_AWK_VALUE_OPTIONS = frozenset({"-F", "-v", "-f"})
# ag·ack 는 rg 의 옵션표를 그대로 쓴다 — 값을 먹는 짧은 옵션(-A -B -C -g -t 등)이 같은 이름이다.
_VALUE_OPTIONS = {
    "grep": _GREP_VALUE_OPTIONS,
    "egrep": _GREP_VALUE_OPTIONS,
    "fgrep": _GREP_VALUE_OPTIONS,
    "rg": _RG_VALUE_OPTIONS,
    "ag": _RG_VALUE_OPTIONS,
    "ack": _RG_VALUE_OPTIONS,
    "sed": frozenset({"-e", "-f"}),
    "awk": _AWK_VALUE_OPTIONS,
    "gawk": _AWK_VALUE_OPTIONS,
    "head": frozenset({"-n", "-c"}),
    "tail": frozenset({"-n", "-c"}),
    "cut": frozenset({"-d", "-f", "-c"}),
}


class ToolInput(TypedDict, total=False):
    command: str
    path: str
    glob: str


class HookPayload(TypedDict, total=False):
    """Claude Code 가 stdin 으로 주는 훅 입력 중 이 훅이 읽는 부분."""

    tool_name: str
    tool_input: ToolInput
    cwd: str


class Segment(NamedTuple):
    """제어 연산자로 가른 명령 조각. `inputs` 는 `<` 리다이렉션의 대상들."""

    words: list[str]
    inputs: list[str]


def env_file_name(token: str) -> str | None:
    """토큰이 `.env` 파일을 가리키면 그 파일 이름, `.env.example` 이거나 아니면 None.

    glob 문자가 든 토큰은 여기서 보지 않는다 — `.env.ex*` 는 `.env.example` 만 펼치므로
    `_glob_reaching_env` 가 fnmatch 로 가른다.
    """
    if any(char in token for char in "*?["):
        return None
    match = _ENV_FILE.search(token)
    if match is None or match.group(1).lower() in ALLOWED_ENV_FILES:
        return None
    return match.group(1)


def _glob_reaching_env(token: str) -> str | None:
    """셸이 `.env` 로 펼칠 glob 이면 그 토큰(`.e*`, `.env*`). 점으로 시작하지 않으면 아니다."""
    leaf = token.replace("\\", "/").rsplit("/", 1)[-1]
    if not leaf.startswith(".") or not any(char in leaf for char in "*?["):
        return None
    return token if _matches_env(leaf) else None


def deny_reason_for_command(command: str, cwd: str | None = None) -> str | None:
    """Bash 명령이 `.env` 를 읽으면 막는 이유, 아니면 None. `cwd` 는 루트 판정의 기준이다."""
    segments, nested = _parse(command)
    for segment in segments:
        reason = _segment_reason(segment.words, segment.inputs, cwd)
        if reason is not None:
            return reason
    for inner in nested:
        reason = deny_reason_for_command(inner, cwd)
        if reason is not None:
            return reason
    return None


def deny_reason_for_grep_tool(path: str | None, glob: str | None) -> str | None:
    """Grep 도구의 경로나 glob 이 `.env` 파일에 닿으면 막는 이유, 아니면 None.

    glob 이 있으면 Grep 도구는 숨김·gitignore 파일도 읽으므로(2026-09-28 실측) `*`·`.*` 도 `.env` 에
    닿는 glob 이다. 확장자 glob(`*.py`)은 닿지 않는다.
    """
    if path is not None:
        name = env_file_name(path.replace("\\", "/"))
        if name is not None:
            return _grep_tool_reason(f"경로 `{name}`")
    if glob is not None:
        leaf = glob.replace("\\", "/").rsplit("/", 1)[-1]
        if leaf.lower() not in ALLOWED_ENV_FILES and _matches_env(leaf):
            return _grep_tool_reason(f"glob `{glob}`(숨김·gitignore 파일도 읽는다)")
    return None


def _grep_tool_reason(target: str) -> str:
    return (
        f"Grep 도구의 {target} 이 `.env` 에 닿는다. `.env` 는 비밀이라 도구 출력에 싣지 않는다"
        "(대기열 43). 확장자 glob 이나 하위 경로를 주고, 키 이름은 `.env.example` 에서 본다."
    )


def _file_reason(cmd: str, name: str) -> str:
    return (
        f"`{cmd}` 가 `{name}` 을 읽는다. `.env` 는 비밀이라 도구 출력에 싣지 않는다(대기열 43 — "
        "2026-09-28 감사에서 grep 한 번에 키가 실렸다). 키 이름은 `.env.example` 에 있고 값은 "
        "사용자가 넣는다. LLM 테스트는 `uv run --env-file .env pytest -m llm` 으로 값을 "
        "프로세스에만 넘긴다."
    )


def _sweep_reason(cmd: str, hint: str) -> str:
    return (
        f"`{cmd}` 가 저장소 전체를 훑으며 `.env` 를 빼지 않는다. `{hint}` 를 붙이거나 "
        "`src/ tests/ docs/` 같은 경로를 준다. 2026-09-28 감사에서 전체 grep 한 번에 `.env` 의 "
        "키가 도구 출력에 실렸다(대기열 43)."
    )


def _segment_reason(words: list[str], inputs: list[str], cwd: str | None) -> str | None:
    for target in inputs:
        name = env_file_name(target)
        if name is not None:
            return _file_reason("<", name)
    words = _strip_prefix(words)
    if not words:
        return None
    cmd, args = _command_name(words[0]), words[1:]
    if cmd in SHELLS:
        inner = _shell_c_argument(args)
        return deny_reason_for_command(inner, cwd) if inner is not None else None
    if cmd == "eval":
        return deny_reason_for_command(" ".join(args), cwd)
    if cmd in READERS:
        positionals = _positionals(args, _VALUE_OPTIONS.get(cmd, frozenset()))
        if cmd in PATTERN_COMMANDS and not _pattern_given_by_option(args):
            positionals = positionals[1:]
        for positional in positionals:
            name = env_file_name(positional) or _glob_reaching_env(positional)
            if name is not None:
                return _file_reason(cmd, name)
    if cmd == "find" and any(_command_name(arg) in READERS for arg in args):
        for arg in args:
            name = env_file_name(arg) or _glob_reaching_env(arg)
            if name is not None:
                return _file_reason("find -exec", name)
    if cmd == "git" and args and args[0] in GIT_READING_SUBCOMMANDS:
        for arg in args[1:]:
            name = env_file_name(arg)
            if name is not None:
                return _file_reason(f"git {args[0]}", name)
    if cmd in {"grep", "egrep", "fgrep"} and _grep_sweeps_root(args, cwd):
        return _sweep_reason(cmd, "--exclude=.env*")
    if cmd == "rg" and _rg_sweeps_root(args, cwd):
        return _sweep_reason(cmd, "-g '!.env*'")
    return None


def _strip_prefix(words: list[str]) -> list[str]:
    """명령 자리 앞의 예약어·환경변수 대입·래퍼를 벗긴다."""
    index = 0
    while index < len(words):
        word = words[index]
        if word in _RESERVED or word in _WRAPPERS or _ASSIGNMENT.match(word):
            index += 1
        elif word == "timeout":
            index += 1
            while index < len(words) and words[index].startswith("-"):  # `-k 3`, `--foreground`
                index += 2 if words[index] in {"-k", "-s", "--kill-after", "--signal"} else 1
            index += 1  # 시간
        elif word == "nice":
            index += 3 if index + 1 < len(words) and words[index + 1] == "-n" else 1
        else:
            break
    return words[index:]


def _command_name(word: str) -> str:
    """`\\grep`·`/usr/bin/cat`·백틱이 붙은 것도 명령 이름으로."""
    return word.lstrip("\\`").replace("\\", "/").rsplit("/", 1)[-1]


def _shell_c_argument(args: list[str]) -> str | None:
    for index, arg in enumerate(args):
        if arg.startswith("-") and "c" in arg[1:] and index + 1 < len(args):
            return args[index + 1]
    return None


def _pattern_given_by_option(args: list[str]) -> bool:
    return any(arg in {"-e", "-f"} or arg.startswith(("--regexp", "--file")) for arg in args)


def _grep_sweeps_root(args: list[str], cwd: str | None) -> bool:
    recursive = any(
        arg in {"--recursive", "--dereference-recursive"}
        or ((match := _SHORT_CLUSTER.match(arg)) is not None and set("rR") & set(match.group(1)))
        for arg in args
    )
    if not recursive:
        return False
    if any(_matches_env(value) for value in _option_values(args, {"--exclude"})):
        return False
    includes = _option_values(args, {"--include"})
    if includes and not any(_matches_env(value) for value in includes):
        return False
    return _paths_reach_root(args, _GREP_VALUE_OPTIONS, cwd)


def _rg_sweeps_root(args: list[str], cwd: str | None) -> bool:
    clusters = [match.group(1) for arg in args if (match := _SHORT_CLUSTER.match(arg))]
    u_count = sum(cluster.count("u") for cluster in clusters) + args.count("--unrestricted")
    hidden = "--hidden" in args or any("." in cluster for cluster in clusters) or u_count >= 2
    no_ignore = u_count >= 1 or any(
        arg.startswith("--no-ignore") and arg != "--no-ignore-messages" for arg in args
    )
    if not (hidden and no_ignore):
        return False
    if any(arg in {"-t", "--type"} or arg.startswith("--type=") for arg in args):
        return False
    globs = _option_values(args, {"-g", "--glob", "--iglob"})
    if any(_matches_env(glob[1:]) for glob in globs if glob.startswith("!")):
        return False
    positives = [glob for glob in globs if not glob.startswith("!")]
    if positives and not any(_matches_env(glob) for glob in positives):
        return False
    return _paths_reach_root(args, _RG_VALUE_OPTIONS, cwd)


def _matches_env(pattern: str) -> bool:
    """glob 이 `.env` 나 `.env.<무엇>` 에 닿는가. `**/.env*` 는 앞의 디렉터리 조각을 뗀다."""
    leaf = pattern.rsplit("/", 1)[-1].lower()
    return any(fnmatch.fnmatch(sample, leaf) for sample in (".env", ".env.local"))


def _paths_reach_root(args: list[str], value_options: frozenset[str], cwd: str | None) -> bool:
    positionals = _positionals(args, value_options)
    paths = positionals if _pattern_given_by_option(args) else positionals[1:]
    return not paths or any(_is_root(path, cwd) for path in paths)


def _is_root(path: str, cwd: str | None) -> bool:
    """경로가 저장소 루트(또는 `.env` 가 있는 디렉터리)인가. 확장 전 변수·홈은 보수적으로 루트."""
    if path in _ROOTISH:
        return True
    if path.startswith(("$", "~")):
        return True
    if not (
        os.path.isabs(path) or path.startswith("/") or ".." in path.replace("\\", "/").split("/")
    ):
        return False
    base = cwd or os.getcwd()
    resolved = os.path.normpath(os.path.join(base, path))
    if _same_path(resolved, base):
        return True
    project = os.environ.get("CLAUDE_PROJECT_DIR")
    if project and _same_path(resolved, project):
        return True
    if os.path.isfile(os.path.join(resolved, ".env")):
        return True
    return path.startswith("/") and not os.path.isdir(resolved)  # `/c/…` 처럼 못 푸는 절대 경로


def _same_path(left: str, right: str) -> bool:
    return os.path.normcase(os.path.normpath(left)) == os.path.normcase(os.path.normpath(right))


def _positionals(args: list[str], value_options: frozenset[str]) -> list[str]:
    """옵션과 옵션 값을 뺀 위치 인자들."""
    positionals: list[str] = []
    skip = False
    for arg in args:
        if skip:
            skip = False
            continue
        if arg in value_options:
            skip = True
            continue
        if arg.startswith("-") and arg != "-":
            continue
        positionals.append(arg)
    return positionals


def _option_values(args: list[str], options: set[str]) -> list[str]:
    """`-g '!x'` 와 `--glob=!x` 두 꼴의 값들."""
    values: list[str] = []
    for index, arg in enumerate(args):
        if arg in options and index + 1 < len(args):
            values.append(args[index + 1])
        for option in options:
            if arg.startswith(option + "="):
                values.append(arg[len(option) + 1 :])
    return values


def _parse(command: str) -> tuple[list[Segment], list[str]]:
    """명령을 (단어들, 입력 리다이렉션 대상들) 조각과 안에 든 명령 치환들로 나눈다."""
    text = "\n".join(_without_heredoc_bodies(command))
    # 줄 이음은 붙이고, 줄바꿈과 백틱은 분리자로. 백틱은 shlex 가 모르므로 여기서 가른다.
    text = re.sub(r"\\\r?\n", " ", text).replace("\n", " ; ").replace("`", " ; ")
    tokens = _tokens(text)
    nested = [inner for token in tokens for inner in _nested_commands(token)]
    segments: list[Segment] = []
    words: list[str] = []
    inputs: list[str] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        index += 1
        if _is_separator(token):
            if words or inputs:
                segments.append(Segment(words, inputs))
                words, inputs = [], []
            continue
        if _is_redirect(token):
            if words and len(words[-1]) == 1 and words[-1].isdigit():
                words.pop()  # `2>` 의 파일 서술자
            if index < len(tokens) and tokens[index] == "(":
                continue  # `<(…)` 는 리다이렉션이 아니라 명령 치환
            if index < len(tokens) and not _is_separator(tokens[index]):
                target = tokens[index]
                index += 1
                if token.startswith("<") and not token.startswith("<<"):
                    inputs.append(target)
            continue
        words.append(token)
    if words or inputs:
        segments.append(Segment(words, inputs))
    return segments, nested


def _tokens(text: str) -> list[str]:
    lexer = shlex.shlex(text, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    try:
        return list(lexer)
    except ValueError:
        return text.split()


def _is_separator(token: str) -> bool:
    return bool(token) and all(char in ";|&()" for char in token)


def _is_redirect(token: str) -> bool:
    return bool(token) and ("<" in token or ">" in token) and all(char in "<>&|" for char in token)


def _nested_commands(token: str) -> list[str]:
    """인용된 토큰 안의 `$(…)`·`<(…)` 명령 치환 본문들. 인용 밖의 것은 shlex 가 이미 갈랐다."""
    inner: list[str] = []
    for match in re.finditer(r"\$\(|<\(", token):
        depth, index = 1, match.end()
        while index < len(token) and depth:
            depth += {"(": 1, ")": -1}.get(token[index], 0)
            index += 1
        inner.append(token[match.end() : index - 1 if depth == 0 else index])
    return inner


def _without_heredoc_bodies(command: str) -> list[str]:
    lines = command.splitlines()
    kept: list[str] = []
    index = 0
    while index < len(lines):
        line = lines[index]
        kept.append(line)
        index += 1
        opener = _HEREDOC_OPENER.search(line)
        if opener is None:
            continue
        strips_tabs = opener.group(1) == "-"
        terminator = opener.group(3)
        while index < len(lines):
            candidate = lines[index].lstrip("\t") if strips_tabs else lines[index]
            index += 1
            if candidate == terminator:
                break
    return kept


def reason_for(tool_name: str, tool_input: ToolInput, cwd: str | None = None) -> str | None:
    if tool_name == "Grep":
        return deny_reason_for_grep_tool(tool_input.get("path"), tool_input.get("glob"))
    command = tool_input.get("command")
    return deny_reason_for_command(command, cwd) if command is not None else None


def main() -> int:
    # stdin 은 바이트로. 이유는 .claude/rules/tools.md(대기열 25).
    payload: HookPayload = json.load(sys.stdin.buffer)
    reason = reason_for(
        payload.get("tool_name", ""), payload.get("tool_input", {}), payload.get("cwd")
    )
    if reason is None:
        return 0
    print(
        json.dumps(
            {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason,
                }
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
