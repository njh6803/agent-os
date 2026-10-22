"""PreToolUse 훅(Bash|Grep). `.env` 를 읽는 명령과 `.env` 를 경로로 준 Grep 을 막는다.

이 저장소의 `permissions.deny` 는 모든 위치의 `.env` 에 Read·Edit 를 막고(`//**/.env`. `./` 는
세션 cwd 기준이라 워크트리 세션에서 주 체크아웃에 닿지 않았다), PowerShell 의 `Get-Content`·
`Select-String`(별칭은 정규화된다)을 막는다(`.scratch/harness/probes/env_deny_probe.md`). Bash
규칙은 호출의 모양만 맞춰 grep 의 인자 자리를 못 보므로 Bash 는 이 훅이 맡는다. 2026-09-28
하네스 감사에서 서브에이전트의 grep 한 번에 `.env` 의 키 값이 도구 출력에 실렸다(대기열 43).
실패가 조용하고(실린 뒤에야 안다) 패턴이 고정돼 첫 사건에서 막는 훅으로 갔다
(`.claude/rules/tools.md`). Grep 도구는 glob 없이 훑으면 gitignore 된 파일을 건너뛰지만(숨김
파일은 읽는다), 경로로 `.env` 를 주거나 glob 의 한 갈래(중괄호면 갈래마다)가 그 파일에 바로 맞으면
읽는다(2026-09-28 가짜 `.env` 로 실측. 2026-10-22 에 손으로 봤다. 숨김 파일은 gitignore 하지 않은
가짜 파일로, `{*.md,**}` 는 gitignore 된 숨김 가짜 파일로 봤다, 대기열 369). 그래서 glob 은 중괄호
갈래마다 펼쳐 본다. Grep 도구는 glob 칸을 공백과 쉼표로 나눠 rg 의 `--glob` 여럿으로 넘기므로
(`grep_tool_globs`, 대기열 422) 나눈 조각마다 본다. 판정은 `tests/tools/test_hook_env_read_rg.py` 가
gitignore 된 가짜 `.env` 를 두고 실제 rg 와 맞댄다.
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
  도 `-t py` 같은 좁힘도 없을 때, 또는 `-g`(`--glob`·`--iglob`, 붙여 쓴 `-g.env`, 묶은
  `-ig .env`)가 `.env` 를 고를 때 같은 판정이다. rg 의 `-g` 는 무시·숨김 규칙과 `-t` 를 이기고 뒤에
  온 glob 이 이긴다 (`_rg_globs_include_env`. `--hidden` 없는 `rg -g .env x .` 를 지나보낸 판이
  있었다, 대기열 422). 루트인지는 페이로드의 `cwd` 기준으로 푼 경로가 cwd·`CLAUDE_PROJECT_DIR`
  이거나 그 안에 `.env` 파일이 있는지(이름만 본다)로 가른다. `.`·`..` 는 조각마다의 cwd 를 모르므로
  언제나 루트로 본다 — `cd src && grep -r x .` 는 오탐이다.
토큰은 shlex 로 나눈다 — 인용 안의 `|` 는 분리자가 아니고 `cat ".env"` 의 인자는 보인다. grep·sed·
awk 류의 첫 위치 인자는 패턴이라 파일로 보지 않는다(`grep .env .gitignore` 는 `.gitignore` 를 읽는
것이다). 리다이렉션 대상은 인자가 아니다(`cat x > .env` 는 쓰기다).
읽는 명령의 목록(`READERS`)에는 Claude Code 가 묻지 않고 돌린 `column`·`rev` 도 든다(대기열 162.
`.scratch/harness/probes/review_git_read.py` 가 glob 경로로 `.git/config` 를 읽거나 권한 단계를
지난 명령이다, 일지 2026-10-07-21). 명령 앞의 래퍼(`sudo`·`command`·`env`·`nice`·`timeout`·`exec`·
`time`·`nohup`·`builtin`)는 경로를 벗긴 이름으로 찾고(`/usr/bin/env`), 그 뒤의 옵션과 옵션 값까지
getopt 처럼 벗긴다(`-n5`, `-iu root`, `--user root`). 같은 프로브에서 권한 규칙이
래퍼(`env`·`command`·`nice`·`timeout`)를 벗겨 대 봤다. 이 훅은 래퍼 뒤의 옵션을 명령 이름으로 읽어
`nice -n5 cat .env`·`command -p cat .env`·`env -i cat .env` 를 지나보냈다(일지 2026-10-13-67 의
세션이 스크래치 스크립트로 찍어 봤고, 그 입력은 지금 tests/tools 가 고정한다). `command -v`·`-V` 는
명령을 찾기만 해 막지 않는다.
못 보는 것: 변수 간접 참조(`for f in .env*; do cat "$f"`), 다른 명령이 넘긴 인자(`ls -a | xargs
cat`), 언어 안의 읽기(`python -c "open('.env')"`), `cp .env x` 뒤의 `cat x`, `uv run --env-file
.env` 뒤의 `printenv`(그 명령은 LLM 테스트의 사전이라 막지 않는다), 상대 경로로 준 하위 디렉터리를
훑는 `grep -r x sub/`·`rg -g .env x sub/`(그 아래에 `.env` 가 있으면 읽는다. `..` 가 없는 상대
경로는 루트로 보지 않는다, `_is_root`), 백슬래시 경로(`C:\\x\\.env` —
shlex 가 이스케이프로 읽는다), 래퍼 스크립트 안의 읽기, 위 목록 밖의 래퍼(`stdbuf -o0 cat .env`)와
명령을 문자열 하나로 받는 래퍼 (`env -S 'cat .env'`), 래퍼의 긴 옵션을 줄여 쓴
꼴(`sudo --us root cat .env` — getopt_long 은 모호하지 않은 머리를 받지만 이 훅은 표에 적은 이름
그대로만 값 옵션으로 본다), PowerShell 도구(권한 deny 가 `Get-Content`·`Select-String` 과 그 별칭만
막고 `[IO.File]::ReadAllText` 같은 읽기는 지나간다 — 2026-09-29 가짜 `.env` 로 실측), `.env` 밖의
비밀 파일(사용자 설정의 env 값 등), gitignore 하지 않은 `.env` 가 든 폴더를 glob 없이 훑는 Grep
도구(숨김 파일을 읽는다). 거짓 양성으로는 빼는 자리(`--exclude`, rg 의 `!`)의 중괄호가 있다. 펼치지
않아, 따옴표 없이 bash 가 펼쳐 `.env` 를 빼는 `--exclude={.env*,x}` 도 막는다. 인용된 중괄호는 grep
이 글자로 읽어 `.env` 를 빼지 않으므로 펼쳐서 뺀다고 보지 않는다. 닿는지 보는 자리는 거꾸로 펼쳐
본다. 토큰은 shlex 가 인용을 벗긴 뒤라, bash 가 펼치지 않는 인용된 중괄호(`cat '.{env,x}'`)와 쉼표
없는 묶음(`cat .{env}`, rg·Grep 도구의 glob 처럼 갈래 하나로 푼다)도 `.env` 로 보아 막는다. 갈래가
256 을 넘는 glob(`{a,b}` 아홉)은 어느 갈래도 `.env` 에 닿지 않아도 막는다. 다 펼쳐 판정하면 훅의
시간 제한을 넘어 지나가기 때문이다. rg·Grep 도구의 glob 에서 rg 는 읽지 않는데 막는 자리도 있다.
고르는 쪽의 대소문자(`-g .ENV`), 앞의 `./`(`-g ./.env`), 겹친 묶음(`{{.env}}`), 빼는 쪽의
중괄호(`-g .env -g '!{.env}'`)와 `--iglob` 의 빼기 대소문자(`_rg_excludes_env`), Grep 도구 glob 칸의
순서(`.env !.env` 는 뒤의 빼기가 이기지만 순서를 보지 않는다), 마지막 `/` 앞의 디렉터리
조각(`src/**` 를 `**` 로 읽는다), 값을 먹는데 표에 없는 짧은 옵션 뒤의 `g`(`-rg .env`,
`_rg_glob_values`)다. `tests/tools/test_hook_env_read_rg.py` 가 실제 rg 와 맞대 고정한다. 에이전트
층의 두 장치(권한 deny, 이 훅)가 못 보는 것은 셋째 층이 맡는다. 키 자체다 — 사용 한도를 건 개발용
키만 두고, 도구 출력에 실린 키는 회전한다(`docs/constitution/operations.md` 가드레일).
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
        "sed", "awk", "gawk", "cut", "tr", "sort", "uniq", "nl", "column", "rev",
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
# 명령 자리 앞의 래퍼와, 그 뒤 옵션 가운데 값을 하나 더 먹는 것. 옵션 낱말은 getopt 처럼 읽는다
# (`_option_width`). `timeout` 은 옵션 뒤의 시간 하나를 더 먹는다.
_WRAPPERS: dict[str, frozenset[str]] = {
    "sudo": frozenset(
        {
            "-u",
            "-g",
            "-C",
            "-D",
            "-h",
            "-p",
            "-r",
            "-t",
            "-U",
            "-T",
            "-c",
            "-R",
            "--user",
            "--group",
            "--close-from",
            "--chdir",
            "--host",
            "--prompt",
            "--role",
            "--type",
            "--other-user",
            "--command-timeout",
            "--login-class",
            "--chroot",
        }
    ),  # fmt: skip
    "env": frozenset({"-u", "--unset", "-C", "--chdir", "-a", "--argv0"}),
    "exec": frozenset({"-a"}),
    "nice": frozenset({"-n", "--adjustment"}),
    "timeout": frozenset({"-k", "-s", "--kill-after", "--signal"}),
    "time": frozenset({"-o", "-f", "--output", "--format"}),
    "command": frozenset(),
    "nohup": frozenset(),
    "builtin": frozenset(),
}
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
    """셸이 `.env` 로 펼칠 glob 이면 그 토큰(`.e*`, `.env*`, `.{env,x}`). 점으로 시작하지 않는
    갈래는 아니다. 중괄호는 bash 가 갈래로 펼치므로 갈래마다 본다(대기열 369). 갈래는
    `_brace_branches` 가 펼쳐 bash 가 글자로 두는 꼴도 막는다(모듈 독스트링의 못 보는 것). 펼치기
    전의 토큰도 본다(`_candidates`)."""
    candidates = _candidates(token.replace("\\", "/"))
    if candidates is None:
        return token
    for branch in candidates:
        leaf = branch.rsplit("/", 1)[-1]
        if not leaf.startswith("."):
            continue
        if any(char in leaf for char in "*?[") and _matches_env(leaf):
            return token
        if branch != token and env_file_name(branch) is not None:
            return token
    return None


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

    Grep 도구는 glob 의 갈래가 바로 맞는 gitignore 된 파일도 읽으므로 `*`·`.*`·`**` 도 `.env` 에
    닿는 glob 이다. 중괄호는 갈래마다 펼쳐 한 갈래라도 닿으면 막는다(`{*.md,**}` 가 gitignore 된
    숨김 파일을 읽었다, 2026-10-22 손으로 봤다, 대기열 369). 확장자 glob(`*.py`)은 닿지 않는다.
    """
    if path is not None:
        name = env_file_name(path.replace("\\", "/"))
        if name is not None:
            return _grep_tool_reason(f"경로 `{name}`")
    if glob is not None and any(
        _reaches_env(piece.replace("\\", "/")) for piece in grep_tool_globs(glob)
    ):
        return _grep_tool_reason(f"glob `{glob}`(glob 에 맞는 gitignore 된 파일도 읽는다)")
    return None


def grep_tool_globs(glob: str) -> list[str]:
    """Grep 도구가 glob 칸을 rg 의 `--glob` 여럿으로 나누는 그대로 나눈다. 공백으로 나누고, 중괄호가
    없는 조각은 쉼표로도 나눈다. 중괄호가 있는 조각은 쉼표로 나누지 않는다. 2026-10-23 claude
    2.1.302 의 Grep 도구로 손으로 봤다(`*.md,x`·`*.md x` 가 무시된 `x` 를 읽었고 `{*.md},x` 는
    아무것도 내지 않았다, 대기열 422). 통째로만 본 판이 `*.md,.env` 를 지나보냈다."""
    pieces: list[str] = []
    for piece in glob.split():
        if "{" in piece and "}" in piece:
            pieces.append(piece)
        else:
            pieces.extend(part for part in piece.split(",") if part)
    return pieces


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
        "프로세스에만 넘긴다(워크트리에서의 경로는 operations.md LLM 테스트)."
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
    """명령 자리 앞의 예약어·환경변수 대입·래퍼와 그 옵션을 벗긴다. 래퍼는 경로를 벗긴 이름으로
    찾는다(`/usr/bin/env`). `command -v`·`-V` 는 명령을 찾기만 하고 돌리지 않아 빈 목록이다."""
    index = 0
    while index < len(words):
        word = words[index]
        if word in _RESERVED or _ASSIGNMENT.match(word):
            index += 1
            continue
        wrapper = _command_name(word)
        value_options = _WRAPPERS.get(wrapper)
        if value_options is None:
            break
        index += 1
        while index < len(words) and words[index].startswith("-"):
            option = words[index]
            if wrapper == "command" and not option.startswith("--") and set(option) & {"v", "V"}:
                return []
            index += _option_width(option, value_options)
        if wrapper == "timeout":
            index += 1  # 시간
    return words[index:]


def _option_width(option: str, value_options: frozenset[str]) -> int:
    """래퍼의 옵션 낱말 하나가 먹는 낱말 수. 짧은 옵션 묶음은 getopt 처럼 읽는다 — 값을 먹는 글자가
    나오면 그 뒤의 글자가 값이고(`-n5`, `-uroot`), 뒤가 비었으면 다음 낱말이 값이다(`-iu root`)."""
    if option.startswith("--"):
        return 2 if option in value_options else 1
    letters = option[1:]
    for index, letter in enumerate(letters):
        if f"-{letter}" in value_options:
            return 1 if letters[index + 1 :] else 2
    return 1


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
    if includes and not any(_reaches_env(value) for value in includes):
        return False
    return _paths_reach_root(args, _GREP_VALUE_OPTIONS, cwd)


def _rg_sweeps_root(args: list[str], cwd: str | None) -> bool:
    globs = _rg_glob_values(args)
    if _rg_globs_include_env(globs):
        return _paths_reach_root(args, _RG_VALUE_OPTIONS, cwd)
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
    if any(_rg_excludes_env(glob[1:]) for glob in globs if glob.startswith("!")):
        return False
    positives = [glob for glob in globs if not glob.startswith("!")]
    if positives and not any(_reaches_env(glob) for glob in positives):
        return False
    return _paths_reach_root(args, _RG_VALUE_OPTIONS, cwd)


def _rg_globs_include_env(globs: list[str]) -> bool:
    """rg 의 glob 가운데 `.env` 를 두고 마지막으로 말한 것이 고르는 glob 인가. rg 의 `-g` 는 무시
    규칙과 숨김 규칙을 이기고(`--hidden`·`--no-ignore` 없이 `-g .env` 가 gitignore 된 `.env` 를
    읽었다), `-t` 로 좁혀도 읽으며, 뒤에 온 glob 이 이긴다(`-g '!.env*' -g .env` 는 읽고 거꾸로는
    읽지 않았다). 2026-10-23 rg 14.1.1 로 손으로 봤고 `tests/tools/test_hook_env_read_rg.py` 가
    실제 rg 와 맞댄다(대기열 422). 빼는 glob 은 `_rg_excludes_env` 로 본다."""
    included = False
    for glob in globs:
        if glob.startswith("!"):
            if _rg_excludes_env(glob[1:]):
                included = False
        elif _reaches_env(glob):
            included = True
    return included


def _rg_excludes_env(pattern: str) -> bool:
    """rg 의 빼는 glob(`!` 뒤)이 `.env` 를 빼는가. 펼치지 않고 대소문자를 가려 본다. rg 의 `-g` 는
    대소문자를 가려, Windows 에서도 `-g .env -g '!.ENV'` 가 `.env` 를 읽었다(2026-10-23 rg 14.1.1,
    셀프 리뷰 명세 축이 손으로 봤다). `--iglob` 과 `--glob-case-insensitive` 의 빼기도 가려 보아,
    `--iglob '!.ENV'` 는 빼지 않는다고 본다(거짓 양성)."""
    return _matches_env(pattern, case_sensitive=True)


def _rg_glob_values(args: list[str]) -> list[str]:
    """rg 의 `-g`·`--glob`·`--iglob` 값들. 차례는 인자의 차례다. 짧은 옵션은 묶음 안의 `g` 도
    본다(`-ig.env`, `-ug .env`). rg 는 묶음을 앞에서부터 읽어 값을 먹는 옵션을 만나면 그 뒤를 값으로
    읽는다(`-tg` 의 `g` 는 `-t` 의 값이다. rg 14.1.1 이 `-t g` 처럼 `unrecognized file type: g` 로
    끝났다, 2026-10-23 손으로 봤다). 값을 먹는 짧은 옵션은 `_RG_VALUE_OPTIONS` 에 든 것만 알고, 그
    밖의 값 옵션(`-r`, `-d`)은 값을 먹지 않는 것으로 읽어 `-rg .env` 를 glob 으로 본다(거짓 양성).
    묶음 꼴을 지나보낸 판이 있었다(셀프 리뷰 두 축, 대기열 422)."""
    values: list[str] = []
    index = 0
    while index < len(args):
        arg = args[index]
        nxt = args[index + 1] if index + 1 < len(args) else None
        index += 1
        if arg == "--":
            break
        if arg.startswith("--"):
            name, eq, value = arg.partition("=")
            if name in {"--glob", "--iglob"}:
                if eq:
                    values.append(value)
                elif nxt is not None:
                    values.append(nxt)
                    index += 1
            elif not eq and name in _RG_VALUE_OPTIONS:
                index += 1
            continue
        if not arg.startswith("-") or len(arg) < 2:
            continue
        for position in range(1, len(arg)):
            if f"-{arg[position]}" not in _RG_VALUE_OPTIONS:
                continue
            rest = arg[position + 1 :]
            if not rest:
                index += 1
                rest = nxt or ""
            if arg[position] == "g" and (rest or nxt is not None):
                values.append(rest)
            break
    return values


def _matches_env(pattern: str, *, case_sensitive: bool = False) -> bool:
    """glob 이 `.env` 나 `.env.<무엇>` 에 닿는가. `**/.env*` 는 앞의 디렉터리 조각을 뗀다. 중괄호는
    펼치지 않는다. 빼는 자리(`--exclude`, rg 의 `!`)가 이것을 써, 인용된 중괄호를 글자로 읽는 도구가
    `.env` 를 빼지 않는데도 뺀다고 보지 않게 한다. 대괄호의 `[^` 는 `[!` 로 읽는다. bash·GNU grep·
    ripgrep 은 둘 다 부정으로 읽고 fnmatch 는 `^` 를 글자로 읽어, `.en[^x]` 를 지나보내고
    `--exclude=.en[^v]` 가 `.env` 를 뺀다고 봤다(PR 직전 보안 리뷰). `case_sensitive` 면 대소문자를
    가린다(`_rg_excludes_env`)."""
    leaf = pattern.rsplit("/", 1)[-1].replace("[^", "[!")
    if not case_sensitive:
        return any(fnmatch.fnmatch(sample, leaf.lower()) for sample in (".env", ".env.local"))
    return any(fnmatch.fnmatchcase(sample, leaf) for sample in (".env", ".env.local"))


def _reaches_env(pattern: str) -> bool:
    """중괄호 갈래 가운데 하나라도 `.env` 에 닿는가(`.env.example` 만 맞는 갈래는 아니다). 닿는지
    보는 자리(Grep 도구의 glob, rg 의 glob, grep 의 `--include`)가 쓴다. 갈래가 너무 많으면 닿는다고
    본다(`_brace_branches`)."""
    candidates = _candidates(pattern)
    if candidates is None:
        return True
    return any(
        branch.rsplit("/", 1)[-1].lower() not in ALLOWED_ENV_FILES and _matches_env(branch)
        for branch in candidates
    )


def _candidates(pattern: str) -> list[str] | None:
    """닿는지 볼 glob 들. 펼친 갈래와 펼치기 전의 패턴이다. 대괄호 안의 `{`·`}` 는 bash·GNU grep·
    ripgrep 이 글자로 읽어 `.en[!{}]` 가 `.env` 에 맞는데, 펼치면 `[!{}]` 가 `[!]` 로 깨져 맞지
    않는다. 펼친 갈래만 본 판이 그것을 지나보냈다(옛 판은 막았다, PR 직전 보안 리뷰). 갈래가
    너무 많으면 None 이다."""
    branches = _brace_branches(pattern)
    if branches is None:
        return None
    return branches if pattern in branches else [pattern, *branches]


# 펼칠 갈래의 상한. 갈래는 묶음 수에 지수로 늘어(`{a,b}` 열여섯에 65536), 다 펼쳐 판정하면 열여섯에
# 7초가 걸렸고 훅의 시간 제한(20초)을 넘으면 막지 않고 지나간다(fail-open, PR 직전 리뷰가 쟀다).
_BRANCH_LIMIT = 256


def _brace_branches(pattern: str) -> list[str] | None:
    """중괄호 갈래를 모두 펼친 glob 들. 여러 묶음과 겹친 묶음(`{a,{b,c}}`)도 푼다. 쉼표가 없는
    묶음(`{x}`)은 갈래 하나로 푼다. Grep 도구의 glob 이 그렇게 읽는다(2026-10-22 손으로 봤다.
    `.ignore` 에 든 숨김 파일을 glob 없이는 건너뛰고 `{<그 이름>}` 으로는 읽었으며, `{*.md}` 는
    마크다운을 찾았다). rg 의 `-g '{.env}'` 도 같고, 실제 rg 와 맞대는 시험이
    `tests/tools/test_hook_env_read_rg.py` 다(대기열 422). rg 14.1.1 은 겹친 묶음(`{{.env}}`)을 풀지
    못해 오류로 끝나는데 여기서는 펼쳐 막는다(거짓 양성). bash 는 그것을 글자로 두는데, 대괄호
    밖이면 글자로 둔 갈래는 `{`·`}` 가 남아 `.env` 에 바로 맞지 않는다. 대괄호 안이면 맞을 수 있어
    부르는 쪽이 펼치기 전의 패턴도 본다(`_candidates`). 짝이 없는 `{` 는 bash 처럼 글자로 두고 그
    뒤의 묶음을 푼다(`{{a,b}` 는 `{a`·`{b`). 갈래가 `_BRANCH_LIMIT` 를 넘으면 펼치기를 멈추고 None
    이다."""
    done: list[str] = []
    pending = [pattern]
    while pending:
        current = pending.pop()
        group = _first_group(current)
        if group is None:
            done.append(current)
        else:
            head, options, tail = group
            pending.extend(head + option + tail for option in reversed(options))
        if len(done) + len(pending) > _BRANCH_LIMIT:
            return None
    return done


def _first_group(pattern: str) -> tuple[str, list[str], str] | None:
    """짝이 맞는 첫 중괄호 묶음의 앞, 갈래들, 뒤. 묶음이 없으면 None 이다."""
    start = pattern.find("{")
    while start != -1:
        depth = 0
        commas: list[int] = []
        end = -1
        for index in range(start, len(pattern)):
            char = pattern[index]
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
                if depth == 0:
                    end = index
                    break
            elif char == "," and depth == 1:
                commas.append(index)
        if end == -1:
            start = pattern.find("{", start + 1)
            continue
        bounds = [start, *commas, end]
        options = [
            pattern[left + 1 : right] for left, right in zip(bounds, bounds[1:], strict=False)
        ]
        return pattern[:start], options, pattern[end + 1 :]
    return None


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
    """`--exclude x` 와 `--exclude=x` 두 꼴의 값들. rg 의 glob 은 `_rg_glob_values` 가 본다."""
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


# 막기는 호출 단위라 같은 호출에 묶은 편집도 돌지 않는다. 편집과 `.env` 글자가 든 검색을 한
# 호출에 묶었다가 편집이 빠질 뻔했다(대기열 111, 일지 2026-10-06-02).
WHOLE_CALL_NOTE = (
    " 이 Bash 호출 전체가 돌지 않았다. 편집 같은 다른 명령을 묶었으면 그것만 따로 다시 친다"
    "(대기열 111)."
)


def reason_for(tool_name: str, tool_input: ToolInput, cwd: str | None = None) -> str | None:
    if tool_name == "Grep":
        return deny_reason_for_grep_tool(tool_input.get("path"), tool_input.get("glob"))
    command = tool_input.get("command")
    reason = deny_reason_for_command(command, cwd) if command is not None else None
    return None if reason is None else reason + WHOLE_CALL_NOTE


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
