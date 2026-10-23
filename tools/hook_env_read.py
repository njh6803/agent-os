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
  (`*` 는 셸이 점파일을 빼므로 훑기가 아니다). 빼기는 `.env` 꼴(`_ENV_SAMPLES`)을 모두 빼야 뺀
  것이다(`--exclude .env` 는 `.env.local` 을 읽는다). rg 는 기본으로 숨김·gitignore 파일을
  건너뛰므로 `--hidden` 과 `--no-ignore`(`-u` 하나가 `--no-ignore`, `-uu` 가 둘 다)가 함께 있고
  `-g '!.env*'` 도 `-t py` 같은 좁힘도 없을 때, 또는 `-g`(`--glob`·`--iglob`, 붙여 쓴 `-g.env`, 묶은
  `-ig .env`)가 `.env` 를 고를 때 같은 판정이다. rg 의 `-g` 는 무시·숨김 규칙과 `-t` 를 이기고 뒤에
  온 glob 이 이기므로 `.env` 꼴의 견본마다 맞는 마지막 glob 으로 가른다(`_rg_reads`. `--hidden` 없는
  `rg -g .env x .` 를 지나보낸 판이 있었다, 대기열 422). 묶은 짧은 옵션은 getopt 처럼 앞에서 읽어
  값 옵션의 값을 위치 인자로 세지 않는다(`rg -ig .env KEY` 는 경로가 없다). 루트인지는 페이로드의
  `cwd` 기준으로 푼 경로가 cwd·`CLAUDE_PROJECT_DIR` 이거나 그 안에 `.env` 파일이 있는지(이름만
  본다)로 가른다. `.`·`..` 는 조각마다의 cwd 를 모르므로 언제나 루트로 본다 —
  `cd src && grep -r x .` 는 오탐이다.
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
도구(숨김 파일을 읽는다), 견본(`.env`·`.env.local`·`.env.production`, `_ENV_SAMPLES`) 밖의 `.env`
꼴만 고르거나 남기는 glob. 판정이 견본에만 glob 을 대 보기 때문이다. 견본을 하나씩 모두 뺀 빼기
(`rg -uu -g '!.env' -g '!.env.local' -g '!.env.production'`), 견본만 빼는 한 glob
(`grep -r --exclude '.en*[!g]'`), 견본 밖을 고르는 glob(`rg -g .env.staging`)이 그 예이고, 셋 다
`.env.staging` 을 읽는다. 거짓 양성으로는 빼는 자리(`--exclude`, rg 의 `!`)의 중괄호가 있다. 펼치지
않아, 따옴표 없이 bash 가 펼쳐 `.env` 를 빼는 `--exclude={.env*,x}` 도 막는다. 인용된 중괄호는 grep
이 글자로 읽어 `.env` 를 빼지 않으므로 펼쳐서 뺀다고 보지 않는다. 닿는지 보는 자리는 거꾸로 펼쳐
본다. 토큰은 shlex 가 인용을 벗긴 뒤라, bash 가 펼치지 않는 인용된 중괄호(`cat '.{env,x}'`)와 쉼표
없는 묶음(`cat .{env}`, rg·Grep 도구의 glob 처럼 갈래 하나로 푼다)도 `.env` 로 보아 막는다. 갈래가
256 을 넘는 glob(`{a,b}` 아홉)은 어느 갈래도 `.env` 에 닿지 않아도 막는다. 다 펼쳐 판정하면 훅의
시간 제한을 넘어 지나가기 때문이다. rg·Grep 도구의 glob 에서 rg 는 읽지 않는데 막는 자리도 있다.
고르는 쪽의 대소문자(`-g .ENV`), 앞의 `./`(`-g ./.env`), 겹친 묶음(`{{.env}}`), 빼는 쪽의
중괄호(`-g .env -g '!{.env}'`)와 `--iglob` 의 빼기 대소문자(`_rg_excludes`), Grep 도구 glob 칸의
순서(`.env !.env` 는 뒤의 빼기가 이기지만 순서를 보지 않는다), 마지막 `/` 앞의 디렉터리
조각(`src/**` 를 `**` 로 읽는다), 디렉터리가 붙은 빼는 glob(`!sub/.env` 는 그 폴더만 빼지만 빼지
않는다고 본다, `_rg_excludes`), 빼는 glob 의 역슬래시(`!\\.env*` 는 rg 가 이스케이프로 읽어 `.env`
꼴을 빼지만 풀어 보지 않는다)이다. `tests/tools/test_hook_env_read_rg.py` 가 실제 rg 와 맞대
고정한다. grep 의 `--exclude='\\.env*'` 도 grep 이 `.env` 꼴을 빼는데(2026-10-23 GNU grep 3.1, 셀프
리뷰 표준 축이 손으로 봤다) 풀어 보지 않아 막는다. ag·ack 의 값 옵션 표(`_AG_VALUE_OPTIONS`,
`_ACK_VALUE_OPTIONS`)는 두 도구의 파서 소스를 읽어 지었고 실제로 재지 않았다. 에이전트
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
from collections.abc import Iterable
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
# `.env` 꼴의 견본. 견본 하나라도 읽으면 닿는다고 본다. 빼는지는 견본마다 본다(grep 은
# `_excludes_every_env`, rg 는 `_rg_reads`).
_ENV_SAMPLES = (".env", ".env.local", ".env.production")
# `.env`, `.env.local`, `../.env`, `$PWD/.env`, `C:/x/.env`. `.envrc`·`config.env` 는 아니다.
_ENV_FILE = re.compile(r"(?<![\w.-])(?:[\w.:~${}-]+/)*(\.env(?:\.[\w-]+)?)(?![\w.-])", re.I)
_HEREDOC_OPENER = re.compile(r"<<(-?)\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\2")
_ASSIGNMENT = re.compile(r"^[A-Za-z_]\w*=")
_SHORT_CLUSTER = re.compile(r"^-([A-Za-z.]+)\d*$")
_ESCAPE = re.compile(r"\\(.)")
# 값을 하나 더 먹는 옵션. 그 값은 경로도 패턴도 아니다.
_GREP_VALUE_OPTIONS = frozenset(
    {
        "-A", "-B", "-C", "-m", "-e", "-f", "-d", "-D", "--include", "--exclude", "--exclude-dir",
        "--exclude-from", "--regexp", "--file",
    }
)  # fmt: skip
# rg 14.1.1 의 `rg --help` 에서 값을 받는 옵션을 모두 옮겼다(`-x VALUE, --long=VALUE` 와
# `--long=VALUE` 꼴, 2026-10-23 손으로 봤다). `--maxdepth` 는 `--max-depth` 의 숨은 별칭이다. 빠진
# `-r` 뒤의 `g` 를 `-g` 로 읽어 `rg -uu -rg ^ .` 를 지나보낸 판이 있었다(PR 직전 보안 리뷰).
_RG_VALUE_OPTIONS = frozenset(
    {
        "-A", "-B", "-C", "-m", "-e", "-f", "-g", "-t", "-T", "-E", "-j", "-M", "-d", "-r",
        "--after-context", "--before-context", "--context", "--max-count", "--regexp", "--file",
        "--glob", "--iglob", "--type", "--type-not", "--type-add", "--encoding", "--threads",
        "--max-columns", "--pre", "--sort", "--sortr", "--color", "--colors", "--max-depth",
        "--context-separator", "--dfa-size-limit", "--engine", "--field-context-separator",
        "--field-match-separator", "--generate", "--hostname-bin", "--hyperlink-format",
        "--ignore-file", "--max-filesize", "--maxdepth", "--path-separator", "--pre-glob",
        "--regex-size-limit", "--replace", "--type-clear",
    }
)  # fmt: skip
# ag·ack 의 값 옵션. 다음 낱말을 값으로 먹는 것만 두고, 근거는 man 페이지가 아니라 파서의 정의다
# (ag 는 `src/options.c` 의 getopt 문자열과 `required_argument`, ack 3 은
# `lib/App/Ack/ConfigLoader.pm` 의 Getopt::Long 명세. 2026-10-23 원문을 받아 읽었다). 이 PC 와 CI
# 에 둘 다 없어 실제로 재지 않았다. 값을 먹지 않는 옵션을 표에 두면 그 뒤의 패턴을 값으로 먹어
# 파일을 패턴으로 버리고(거짓 음성), 값을 먹는 옵션을 빼면 그 값을 패턴으로 버려 파일을 파일로
# 본다(막는 쪽). 그래서 모르면 뺀다. 값이 선택인 것도 뺀다. ag 의 `--after`·`--before`·`--context`
# 는 `=` 로 붙인 값만 받고(짧은 `-A`·`-B`·`-C` 는 값을 꼭 받는다), ack 의 `-A`·`-B`·`-C`·`-p` 는
# 숫자가 아닌 다음 낱말을 먹지 않는다. ack 의 `--pager` 는 값이 선택이지만 Getopt::Long 이 `-` 로
# 시작하지 않는 다음 낱말을 값으로 먹어 둔다. 패턴을 주는 값 옵션(ack 의 `--match`)은 표에 두면서
# `_pattern_given_by_option` 에도 알려야 한다. 이 표의 앞선 두 판이 틀렸다. rg 의 표를 함께 쓴 판은
# ag 의 `-t`(--all-text)·`-f`(--follow)를 값 옵션으로 읽어 `ag -t KEY .env` 를 지나보냈고(푸시 뒤
# 자동 보안 리뷰, 대기열 422), man 페이지의 `-A NUM`·`-g PATTERN` 을 따른 판은 ack 의 `-A`·`-B`(값이
# 선택인 숫자)와 `-g`(값 없는 플래그)를 값 옵션으로 읽어 `ack -A KEY .env` 를 지나보냈다(셀프 리뷰).
_AG_VALUE_OPTIONS = frozenset(
    {
        "-A", "-B", "-C", "-G", "-g", "-m", "-p", "-W",
        "--file-search-regex", "--filename-pattern", "--max-count", "--path-to-ignore", "--width",
        "--ignore", "--ignore-dir", "--depth", "--pager", "--workers", "--color-line-number",
        "--color-match", "--color-path", "--ackmate-dir-filter",
    }
)  # fmt: skip
_ACK_VALUE_OPTIONS = frozenset(
    {
        "-m", "-t", "-T",
        "--max-count", "--type", "--match", "--output", "--and", "--or", "--not", "--range-start",
        "--range-end", "--files-from", "--ignore-dir", "--ignore-directory", "--noignore-dir",
        "--noignore-directory", "--ignore-file", "--type-add", "--type-set", "--type-del",
        "--color-match", "--color-filename", "--color-colno", "--color-lineno", "--ackrc",
        "--pager",
    }
)  # fmt: skip
_AWK_VALUE_OPTIONS = frozenset({"-F", "-v", "-f", "--file", "--source"})
_VALUE_OPTIONS = {
    "grep": _GREP_VALUE_OPTIONS,
    "egrep": _GREP_VALUE_OPTIONS,
    "fgrep": _GREP_VALUE_OPTIONS,
    "rg": _RG_VALUE_OPTIONS,
    "ag": _AG_VALUE_OPTIONS,
    "ack": _ACK_VALUE_OPTIONS,
    "sed": frozenset({"-e", "-f", "--expression", "--file"}),
    "awk": _AWK_VALUE_OPTIONS,
    "gawk": _AWK_VALUE_OPTIONS,
    "head": frozenset({"-n", "-c"}),
    "tail": frozenset({"-n", "-c"}),
    "cut": frozenset({"-d", "-f", "-c"}),
}
_RG_GLOB_OPTIONS = frozenset({"-g", "--glob", "--iglob"})
# 파일을 값으로 받아 그 파일을 읽는 옵션. 값이 `.env` 면 읽는다고 본다. 값 옵션 표가 그 값을 먹어
# 위치 인자로 보지 않으므로 따로 본다. 여기 든 옵션은 그 명령의 값 옵션 표에도 있어야 한다. 표에
# 없던 `--exclude-from` 의 값을 경로로 세어 `grep -rn --exclude-from list.txt KEY` 가 루트를 훑지
# 않는다고 본 판이 있었다(셀프 리뷰 표준 축). `--files-from` 을 값 옵션 표에 넣은 판이 `ack KEY
# --files-from .env` 를 지나보냈고, `grep -f .env`·`sed -f .env` 는 그 전부터 지나갔다(셋째 푸시 뒤
# 자동 보안 리뷰). ack 3 의 `--ignore-file` 은 파일이 아니라 거름 명세(`--ignore-file=FILTER:ARGS`,
# ack 3 의 POD)라 넣지 않는다.
_GREP_FILE_OPTIONS = frozenset({"-f", "--file", "--exclude-from"})
_SCRIPT_FILE_OPTIONS = frozenset({"-f", "--file"})
_FILE_OPTIONS = {
    "grep": _GREP_FILE_OPTIONS,
    "egrep": _GREP_FILE_OPTIONS,
    "fgrep": _GREP_FILE_OPTIONS,
    "rg": frozenset({"-f", "--file", "--ignore-file"}),
    "ag": frozenset({"-p", "--path-to-ignore"}),
    "ack": frozenset({"--files-from", "--ackrc"}),
    "sed": _SCRIPT_FILE_OPTIONS,
    "awk": _SCRIPT_FILE_OPTIONS,
    "gawk": _SCRIPT_FILE_OPTIONS,
}
# 패턴(sed·awk 는 스크립트)을 따로 줘 위치 인자가 모두 파일이 되는 긴 옵션. 명령마다 다르다. 모든
# 명령에 같은 표를 쓴 판은 `--file` 의 앞글자 견줌으로 grep 의 `--files-with-matches` 를 패턴
# 옵션으로 읽어 `grep -rn --files-with-matches KEY` 를 지나보냈고, ack 의 `--match` 를 grep 에도
# 견줘 `grep --ma=2 .env .gitignore`(`--max-count`)를 막았다(셀프 리뷰 두 축). 이 옵션들은 값 옵션
# 표에도 있다.
_GREP_PATTERN_LONG_OPTIONS = ("--regexp", "--file")
_SCRIPT_PATTERN_LONG_OPTIONS = ("--file", "--source")
_PATTERN_LONG_OPTIONS = {
    "grep": _GREP_PATTERN_LONG_OPTIONS,
    "egrep": _GREP_PATTERN_LONG_OPTIONS,
    "fgrep": _GREP_PATTERN_LONG_OPTIONS,
    "rg": _GREP_PATTERN_LONG_OPTIONS,
    "ack": ("--match",),
    "sed": ("--expression", "--file"),
    "awk": _SCRIPT_PATTERN_LONG_OPTIONS,
    "gawk": _SCRIPT_PATTERN_LONG_OPTIONS,
}
# 긴 옵션의 줄임을 받지 않는 명령. 나머지(GNU grep·sed·gawk 와 ag 의 getopt_long, ack 의
# Getopt::Long)는 겹치지 않는 앞글자를 줄임으로 받는다고 본다(ag·ack 는 재지 않았다). 줄임으로 보면
# 파일 읽기 판정은 막는 쪽으로만 기운다.
_NO_ABBREVIATION = frozenset({"rg"})


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
    if glob is not None and any(_reaches_env(piece) for piece in grep_tool_globs(glob)):
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
        value_options = _VALUE_OPTIONS.get(cmd, frozenset())
        positionals = _positionals(args, value_options)
        if (
            cmd in PATTERN_COMMANDS
            and not _pattern_given_by_option(
                args, value_options, _PATTERN_LONG_OPTIONS.get(cmd, ())
            )
            and not _abbreviates_pattern_option(cmd, args)
        ):
            positionals = positionals[1:]
        file_values = _getopt_values(
            args,
            value_options,
            _FILE_OPTIONS.get(cmd, frozenset()),
            abbreviations=cmd not in _NO_ABBREVIATION,
        )
        for positional in [*positionals, *file_values]:
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
    found = _short_value_option(option, value_options)
    return 2 if found is not None and not found[1] else 1


def _short_value_option(option: str, value_options: frozenset[str]) -> tuple[str, str] | None:
    """짧은 옵션 묶음(`-ig.env`)을 getopt 처럼 앞에서 읽어 처음 만난 값 옵션의 글자와 그 뒤에 붙은
    값. 값이 비었으면 다음 낱말이 값이다. 값 옵션이 없으면 None 이다."""
    for index, letter in enumerate(option[1:], start=1):
        if f"-{letter}" in value_options:
            return letter, option[index + 1 :]
    return None


def _command_name(word: str) -> str:
    """`\\grep`·`/usr/bin/cat`·백틱이 붙은 것도 명령 이름으로."""
    return word.lstrip("\\`").replace("\\", "/").rsplit("/", 1)[-1]


def _shell_c_argument(args: list[str]) -> str | None:
    for index, arg in enumerate(args):
        if arg.startswith("-") and "c" in arg[1:] and index + 1 < len(args):
            return args[index + 1]
    return None


def _pattern_given_by_option(
    args: list[str], value_options: frozenset[str], long_options: tuple[str, ...]
) -> bool:
    """패턴을 `-e`·`-f` 나 그 명령의 패턴 긴 옵션(`long_options`, 이름이 같거나 `=` 로 값을
    붙인 꼴)으로 줬는가. 묶음 속의 것(`-ie KEY`)도 `_positionals` 와 같이 읽는다. `--match` 를 값
    옵션 표에만 둔 판이 패턴을 값으로 먹고 `.env` 를 패턴으로 버려 `ack --match KEY .env` 를
    지나보냈다(셀프 리뷰 명세 축)."""
    for arg in args:
        if arg in {"-e", "-f"} or arg.partition("=")[0] in long_options:
            return True
        if arg.startswith("-") and not arg.startswith("--"):
            found = _short_value_option(arg, value_options)
            if found is not None and found[0] in {"e", "f"}:
                return True
    return False


def _abbreviates_pattern_option(cmd: str, args: list[str]) -> bool:
    """그 명령의 패턴 긴 옵션을 줄여 썼는가(`--reg=KEY`, `--e=1p`). getopt_long 은 겹치지 않는
    줄임을 받아(GNU grep 3.1 의 `--reg=` 와 sed 4.8 의 `--exp=`·`--e=` 가 파일을 읽었다, 2026-10-23
    이 세션과 셀프 리뷰 두 축이 손으로 봤다), 이것을 몰랐던 판이 `grep --reg=KEY .env`·`sed --exp=1p
    .env` 의 `.env` 를 패턴으로 버렸다(셋째 푸시 뒤 자동 보안 리뷰). 줄임의 최소 길이는 명령마다
    달라(sed 는 `--e`, grep 의 `--r` 은 겹쳐 거부한다) 앞글자 하나부터 본다. 겹쳐 하류가 거부하는
    줄임도 줄임으로 보니 막는 쪽으로 기운다. 파일 읽기 판정만 쓴다. 참이면 첫 위치 인자도 파일로
    보아 막는 쪽으로만 기운다. 훑기 판정(`_paths_reach_root`)에 쓰면 `grep -rn --reg KEY` 의 `KEY`
    를 경로로 읽어 루트를 훑지 않는다고 볼 것이라 쓰지 않는다."""
    if cmd in _NO_ABBREVIATION:
        return False
    return any(_long_option(arg, _PATTERN_LONG_OPTIONS.get(cmd, ())) for arg in args)


def _long_option(arg: str, options: Iterable[str]) -> str | None:
    """긴 옵션 낱말(`--opt`, `--opt=값`)이 줄임까지 쳐서 맞는 `options` 의 옵션. 이름이 `--` 와 한
    글자 이상이어야 하고, 여럿에 맞으면 처음 것이다."""
    name = arg.partition("=")[0]
    if not name.startswith("--") or len(name) < 3:
        return None
    return next((option for option in options if option.startswith(name)), None)


def _grep_sweeps_root(args: list[str], cwd: str | None) -> bool:
    recursive = any(
        arg in {"--recursive", "--dereference-recursive"}
        or ((match := _SHORT_CLUSTER.match(arg)) is not None and set("rR") & set(match.group(1)))
        for arg in args
    )
    if not recursive:
        return False
    if _excludes_every_env(_option_values(args, {"--exclude"})):
        return False
    includes = _option_values(args, {"--include"})
    if includes and not any(_reaches_env(value) for value in includes):
        return False
    return _paths_reach_root(args, _GREP_VALUE_OPTIONS, _GREP_PATTERN_LONG_OPTIONS, cwd)


def _rg_sweeps_root(args: list[str], cwd: str | None) -> bool:
    clusters = [match.group(1) for arg in args if (match := _SHORT_CLUSTER.match(arg))]
    u_count = sum(cluster.count("u") for cluster in clusters) + args.count("--unrestricted")
    hidden = "--hidden" in args or any("." in cluster for cluster in clusters) or u_count >= 2
    no_ignore = u_count >= 1 or any(
        arg.startswith("--no-ignore") and arg != "--no-ignore-messages" for arg in args
    )
    typed = any(arg in {"-t", "--type"} or arg.startswith("--type=") for arg in args)
    unrestricted = hidden and no_ignore and not typed
    globs = _rg_glob_values(args)
    if not any(_rg_reads(globs, sample, unrestricted=unrestricted) for sample in _ENV_SAMPLES):
        return False
    return _paths_reach_root(args, _RG_VALUE_OPTIONS, _GREP_PATTERN_LONG_OPTIONS, cwd)


def _rg_reads(globs: list[str], sample: str, *, unrestricted: bool) -> bool:
    """rg 가 `.env` 꼴의 견본 하나를 읽는가. 그 견본에 맞는 마지막 glob 이 정한다. rg 의 `-g` 는
    무시 규칙과 숨김 규칙을 이기고(`--hidden`·`--no-ignore` 없이 `-g .env` 가 gitignore 된 `.env` 를
    읽었다), `-t` 로 좁혀도 읽으며, 뒤에 온 glob 이 이긴다(`-g '!.env*' -g .env` 는 읽고 거꾸로는
    읽지 않았다). 2026-10-23 rg 14.1.1 로 손으로 봤고 `tests/tools/test_hook_env_read_rg.py` 가
    실제 rg 와 맞댄다(대기열 422). 맞는 glob 이 없으면 고르는 glob 이 하나도 없고 무시·숨김 규칙을
    모두 끄고 `-t` 로 좁히지 않은(`unrestricted`) 때만 읽는다. 견본마다 보지 않고 `.env` 꼴 하나라도
    빼면 뺀다고 본 판이 `-g '.env*' -g '!.env'`·`-uu -g '!.env'` 의 `.env.local` 을 지나보냈다(푸시
    뒤 자동 보안 리뷰)."""
    decision: bool | None = None
    for glob in globs:
        if glob.startswith("!"):
            if _rg_excludes(glob[1:], sample):
                decision = False
        elif _rg_selects(glob, sample):
            decision = True
    if decision is not None:
        return decision
    return unrestricted and all(glob.startswith("!") for glob in globs)


def _rg_selects(pattern: str, sample: str) -> bool:
    """rg 의 고르는 glob 이 견본에 닿는가. 중괄호 갈래마다 대소문자 없이 본다(`_reaches_env` 와 같은
    너그러움, 모듈 독스트링의 거짓 양성). 갈래가 너무 많으면 닿는다고 본다. 역슬래시는
    `_glob_readings` 의 글을 모두 본다."""
    for reading in _glob_readings(pattern):
        candidates = _candidates(reading)
        if candidates is None:
            return True
        if any(
            fnmatch.fnmatch(sample, branch.rsplit("/", 1)[-1].replace("[^", "[!").lower())
            for branch in candidates
        ):
            return True
    return False


def _rg_excludes(pattern: str, sample: str) -> bool:
    """rg 의 빼는 glob(`!` 뒤)이 견본을 빼는가. 펼치지 않고 대소문자를 가려 본다. rg 의 `-g` 는
    대소문자를 가려, Windows 에서도 `-g .env -g '!.ENV'` 가 `.env` 를 읽었다(2026-10-23 rg 14.1.1,
    셀프 리뷰 명세 축이 손으로 봤다). `--iglob` 과 `--glob-case-insensitive` 의 빼기도 가려 보아,
    `--iglob '!.ENV'` 는 빼지 않는다고 본다(거짓 양성). 앞의 `**/` 를 뗀 뒤에도 `/` 가 남은 glob 은
    한 폴더만 빼므로 빼지 않는다고 본다. `-g .env -g '!sub/.env'` 는 루트의 `.env` 를,
    `-uu -g '!/.env'` 는 `sub/.env` 를 읽었는데 마지막 `/` 앞을 떼고 본 판이 둘을
    지나보냈다(2026-10-23 rg 14.1.1, PR 직전 bug-perf-review 가 손으로 봤다). 그래서 `!sub/**` 처럼
    그 폴더만 빼는 glob 도 빼지 않는다고 본다(거짓 양성)."""
    while pattern.startswith("**/"):
        pattern = pattern[3:]
    return "/" not in pattern and fnmatch.fnmatchcase(sample, pattern.replace("[^", "[!"))


def _rg_glob_values(args: list[str]) -> list[str]:
    """rg 의 `-g`·`--glob`·`--iglob` 값들. 차례는 인자의 차례다. 짧은 옵션은 묶음 안의 `g` 도
    본다(`-ig.env`, `-ug .env`). rg 는 묶음을 앞에서부터 읽어 값을 먹는 옵션을 만나면 그 뒤를 값으로
    읽는다(`-tg` 의 `g` 는 `-t` 의 값이다. rg 14.1.1 이 `-t g` 처럼 `unrecognized file type: g` 로
    끝났다, 2026-10-23 손으로 봤다). 값을 먹는 짧은 옵션은 `_RG_VALUE_OPTIONS` 에 든 것만 안다. 그
    표가 rg 의 값 옵션을 다 담지 못하면 그 옵션의 값 `g` 를 `-g` 로 읽어, 뒤의 낱말이 `.env` 가 아닌
    고르는 glob 이 되어 훑기를 지나보낸다(`-rg ^` 가 그랬다, PR 직전 보안 리뷰). 묶음 꼴을
    지나보낸 판이 있었다(셀프 리뷰 두 축, 대기열 422)."""
    return _getopt_values(args, _RG_VALUE_OPTIONS, _RG_GLOB_OPTIONS)


def _getopt_values(
    args: list[str],
    value_options: frozenset[str],
    wanted: frozenset[str],
    *,
    abbreviations: bool = False,
) -> list[str]:
    """`wanted` 에 든 값 옵션의 값들을 getopt 처럼 읽는다. 차례는 인자의 차례다. 긴 옵션은
    `--opt 값`·`--opt=값`, 짧은 옵션은 묶음을 앞에서 읽어 처음 만난 값 옵션의 뒤나 다음 낱말이
    값이다 (`_short_value_option`). 짧은 옵션은 `value_options` 에도 있어야 묶음에서 찾는다. `--`
    뒤는 보지 않는다. `abbreviations` 면 `value_options` 의 이름과 같지 않은 긴 옵션을 `wanted` 의
    줄임으로도 본다(`sed --fi=.env`, `_long_option`)."""
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
            abbreviated = (
                abbreviations
                and name not in value_options
                and _long_option(arg, sorted(wanted)) is not None
            )
            if name in wanted or abbreviated:
                if eq:
                    values.append(value)
                elif nxt is not None:
                    values.append(nxt)
                    index += 1
            elif not eq and name in value_options:
                index += 1
            continue
        if not arg.startswith("-") or len(arg) < 2:
            continue
        found = _short_value_option(arg, value_options)
        if found is None:
            continue
        letter, rest = found
        if not rest:
            index += 1
            rest = nxt or ""
        if f"-{letter}" in wanted and (rest or nxt is not None):
            values.append(rest)
    return values


def _matches_env(pattern: str) -> bool:
    """glob 이 `.env` 나 `.env.<무엇>` 에 닿는가. `**/.env*` 는 앞의 디렉터리 조각을 뗀다. 중괄호는
    펼치지 않는다. 대괄호의 `[^` 는 `[!` 로 읽는다. bash·GNU grep·ripgrep 은 둘 다 부정으로 읽고
    fnmatch 는 `^` 를 글자로 읽어, `.en[^x]` 를 지나보내고 `--exclude=.en[^v]` 가 `.env` 를 뺀다고
    봤다(PR 직전 보안 리뷰)."""
    return any(_env_samples_matched(pattern))


def _excludes_every_env(patterns: list[str]) -> bool:
    """grep 의 `--exclude` 값들이 합쳐 `.env` 꼴의 견본을 모두 빼는가. 견본마다 그것을 빼는 값이
    하나라도 있어야 한다(`--exclude .env --exclude '.env.*'` 는 모두 뺀다). 중괄호는 펼치지 않아,
    인용된 중괄호를 글자로 읽는 grep 이 `.env` 를 빼지 않는데도 뺀다고 보지 않게 한다. 하나만 빼는
    glob(`.env`, `.env.local`)은 남은 꼴을 읽는다. 값 하나라도 견본 하나에 맞으면 뺀다고 본 판이
    `grep -r --exclude .env` 를 지나보냈고(푸시 뒤 자동 보안 리뷰가 rg 의 같은 판정에서 찾았다,
    대기열 422), 값마다 견본 모두를 요구한 판은 합쳐야 모두 빼는 명령을 막았다(셀프 리뷰 두 축.
    GNU grep 3.1 로 `--exclude .env` 가 `.env.local` 을 읽고 둘을 합치면 읽지 않는 것을 손으로
    봤다). rg 도 견본마다 본다(`_rg_reads`). 빼기는 대소문자를 가려 본다. GNU grep 3.1 이
    `--exclude='.ENV*'` 로 `.env` 를 읽었는데 대소문자 없이 견준 판이 뺀다고 봤다(2026-10-23 손으로
    봤다, 푸시 뒤 자동 보안 리뷰)."""
    matched = [_env_samples_excluded(pattern) for pattern in patterns]
    return bool(matched) and all(any(row[i] for row in matched) for i in range(len(_ENV_SAMPLES)))


def _env_samples_matched(pattern: str) -> list[bool]:
    """glob 의 마지막 조각이 `.env` 꼴의 견본마다 맞는가. 닿는지 보는 자리라 대소문자는 가리지
    않는다(거짓 양성 쪽)."""
    leaf = pattern.rsplit("/", 1)[-1].replace("[^", "[!").lower()
    return [fnmatch.fnmatch(sample, leaf) for sample in _ENV_SAMPLES]


def _env_samples_excluded(pattern: str) -> list[bool]:
    """grep 의 빼는 glob 의 마지막 조각이 견본마다 맞는가. 대소문자를 가린다
    (`_excludes_every_env`)."""
    leaf = pattern.rsplit("/", 1)[-1].replace("[^", "[!")
    return [fnmatch.fnmatchcase(sample, leaf) for sample in _ENV_SAMPLES]


def _reaches_env(pattern: str) -> bool:
    """중괄호 갈래 가운데 하나라도 `.env` 에 닿는가(`.env.example` 만 맞는 갈래는 아니다). 닿는지
    보는 자리(Grep 도구의 glob, rg 의 glob, grep 의 `--include`)가 쓴다. 갈래가 너무 많으면 닿는다고
    본다(`_brace_branches`). 역슬래시는 `_glob_readings` 의 글을 모두 본다."""
    for reading in _glob_readings(pattern):
        candidates = _candidates(reading)
        if candidates is None:
            return True
        if any(
            branch.rsplit("/", 1)[-1].lower() not in ALLOWED_ENV_FILES and _matches_env(branch)
            for branch in candidates
        ):
            return True
    return False


def _glob_readings(pattern: str) -> set[str]:
    """닿는지 볼 glob 의 글들. 그대로의 글, 역슬래시를 이스케이프로 지운 글, `\\` 를 `/` 로
    바꾼 글이다. 하나라도 닿으면 닿는다고 본다(`.claude/rules/tools.md` 의 이스케이프 항목). 실제 rg
    14.1.1 이 Windows 에서도 `-g '\\.env'`·`-g '\\.e\\nv'` 로 `.env` 를 읽고(`_BASH_RG_SAME`), GNU
    grep 3.1 이 `--include='\\.env'`·`--include='.e\\nv'` 로 읽었는데(2026-10-23 셀프 리뷰 표준 축이
    손으로 봤다), 역슬래시를 글자나 `/` 로만 본 판이 rg·Grep 도구·grep 의 셋을 지나보냈다(푸시 뒤
    자동 보안 리뷰, 셀프 리뷰 표준 축)."""
    return {pattern, _ESCAPE.sub(r"\1", pattern), pattern.replace("\\", "/")}


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


def _paths_reach_root(
    args: list[str],
    value_options: frozenset[str],
    pattern_options: tuple[str, ...],
    cwd: str | None,
) -> bool:
    positionals = _positionals(args, value_options)
    given = _pattern_given_by_option(args, value_options, pattern_options)
    paths = positionals if given else positionals[1:]
    return not paths or any(_is_root(path, cwd) for path in paths)


def _is_root(path: str, cwd: str | None) -> bool:
    """경로가 저장소 루트(또는 `.env` 가 있는 디렉터리)인가. 확장 전 변수·홈은 보수적으로 루트.
    `.` 을 다르게 쓴 꼴(`./.`, `.//`)도 루트다. 그 꼴을 루트로 보지 않아 `rg -g .env x ./.` 를
    지나보낸 판이 있었다(PR 직전 bug-perf-review)."""
    if path in _ROOTISH or os.path.normpath(path.replace("\\", "/")) in _ROOTISH:
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
    """옵션과 옵션 값을 뺀 위치 인자들. 옵션 낱말은 getopt 처럼 읽는다(`_option_width`). 묶음 속의
    값 옵션을 보지 않은 판이 `rg -ig .env KEY` 의 `.env` 를 패턴, `KEY` 를 경로로 읽어, 경로 없이
    루트를 훑는 명령을 지나보냈다(푸시 뒤 자동 보안 리뷰, 대기열 422)."""
    positionals: list[str] = []
    index = 0
    while index < len(args):
        arg = args[index]
        if arg.startswith("-") and arg != "-":
            index += _option_width(arg, value_options)
            continue
        positionals.append(arg)
        index += 1
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
