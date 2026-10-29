"""PostToolUse 훅(Bash|PowerShell|Skill|GitHub MCP 의 PR 만들기). 세션 컨텍스트가 문턱을 넘은 채
단계 경계에 오면 인계를 지시한다. 막지 않는 계기 훅이다.

세션 컨텍스트가 20만 토큰을 넘은 세션은 단계 경계에서 같은 브랜치·워크트리의 새 세션으로 넘긴다
(ADR 0033, 명세 `.scratch/token-usage/spec.md` "인계 훅"). 경계는 셋이고 사용자가 골랐다. 셀프 리뷰
직전(Skill 의 `code-review`), 커밋 뒤(명령 위치의 `git commit`), PR 연 뒤(셸의 `gh pr create`,
`pulls` 에 POST 하는 `gh api`, MCP 의 PR 만들기)다. 문장은 경계를 글자 그대로
`셀프 리뷰 직전`·`커밋 뒤`·`PR 연 뒤` 로 부른다 — `next-session` 의 `handoff.md` 가 지시문의
`이어받을 상태: 인계: <경계>` 를 이 글자로 견준다.

판정의 차례. 도구 이름과 명령 문자열, 스킬 이름으로 경계인지 먼저 가르고, 경계일 때만 트랜스크립트
끝 `TAIL_BYTES` 를 연다. 경계가 아닌 호출은 파이썬을 띄우는 값만 쓴다. 세션 컨텍스트는 메인 세션의
마지막 모델 응답(사이드체인이 아니고 모델이 `<synthetic>` 이 아닌 assistant 기록)의 usage 에서
`input_tokens + cache_creation_input_tokens + cache_read_input_tokens` 다. 그 응답은 경계를 일으킨
도구 호출을 낸 응답이라 그 도구의 결과는 들지 않는다. 그 응답 뒤에 압축 경계 기록(`type: system`,
`subtype: compact_boundary`)이 있으면 압축 전의 큰 값이라 침묵한다. 성공했는지는 가르지 않고
문장에 "성공했으면"을 단다(`hook_pr_next_session` 의 선례).

문장은 `next-session` 의 인계 절차 파일을 Read 로 열어 따르라고 한다. Skill 도구로 부르라고 하지
않는다. 실행 중이던 세션의 Skill 도구는 주 체크아웃을 당긴 뒤에도 옛 사본을 실을 수 있고(`CLAUDE.md`
환경 함정) 옛 사본에는 인계 절차가 없다. 가리키는 파일은 `skill_for` 가 고른다. 세션이 일하는
체크아웃(페이로드의 `cwd` 에서 위로 올라가 처음 만나는 사본)에 `handoff.md` 가 있으면 그것이다. 없고
그 `SKILL.md` 에 인계 절(`SECTION`)이 있으면 그 `SKILL.md` 다. 절차를 `handoff.md` 로 나누기
전(harness 027)에 딴 워크트리이고, 그 판은 결정표의 인계 줄을 따른다. 둘 다 아니면 이 훅 파일과 같은
체크아웃의 `handoff.md`(`HANDOFF_PATH`)다. 훅은
`CLAUDE_PROJECT_DIR`(워크트리 세션에서도 주 체크아웃)의 파일로 돌아 뒤의 것은 훅과 같은 판이지만,
작업 폴더 밖이다. 기본 권한 모드에서 추가 작업 폴더 없이(`--setting-sources local`) 워크트리를
작업 폴더로 띄운 `claude -p` 세션은 주 체크아웃의 그 파일 Read 를 거부당했고(승인 질문의 비대화형
모양), 같은 자리의 워크트리 사본은 열었다(`.scratch/token-usage/probes/handoff_reach.py` 의 C·D,
일지 2026-10-16-63). auto 모드에 추가 작업 폴더로 `C:/project` 를 둔 데스크톱 세션에서는 묻지 않고
열렸다(같은 일지, 손으로 한 번 봤다). 대화형 기본 모드에서 승인 질문이 뜨는지는 재지 않았다. 승인할
사람이 없는 인계는 거기서 멈출 수 있으므로 작업 폴더 안의 사본을 먼저 고른다. 인계를 지시하면
`hook_handoff_notice`(Stop)와 같은 이름의 표지를 만든다(이미 있으면 둔다). 그래서 문턱과 경계가 한
턴에 함께 와 인계한 턴의 끝에는 "넘어갈 것이다"라는 알림이 나지 않는다. 표지는 Stop 알림만 거른다.
인계 지시는 표지가 있든 없든 경계마다 낸다.

문턱, 세션 컨텍스트 셈(`session_context`, `tail_lines`), 표지 이름(`STATE_DIR`, `marker_name`)은
`tools/hook_handoff_notice.py` 와 같아야 한다. 훅은 서로 import 하지 않아 따로 두고,
tests/tools/test_hook_handoff.py 의 `test_두_훅의_문턱과_셈과_표지_이름이_같다` 가 대조한다. 커밋
판정은 `tools/hook_git_main_commit.py` 의 `_GIT_COMMIT` 과 `commits_in`, PR 판정은
`tools/hook_pr_next_session.py` 의 `_GH_PR` 과 같은 방식이다.

침묵하는 자리: 서브에이전트(입력에 `agent_id` 가 온다. 그 기록은 메인 트랜스크립트에 없다), 클라우드
세션(환경의 `CLAUDE_CODE_REMOTE` 가 `true`. `open-session` 을 쓸 수 없어 인계 지시가 사람 없는
세션을 경계에서 멈추게 한다. 압축이 받는다).

못 보는 것:
- 사람이 슬래시 명령으로 친 `/code-review`. Skill 도구 호출이 아니라 이 훅이 돌지 않는다.
- 별칭(`git ci`)이나 스크립트 안의 커밋. 명령 위치에 `git commit` 이 없다.
- 명령 앞의 래퍼(`time`, `env X=1`, `sudo`, `!`)와 경로로 부른 git(`/usr/bin/git`). 명령 위치를
  셸 문법 밖에서 가르지 않아 놓친다(거짓 음성).
- 인용 없이 옵션 자리에 둔 값. `git commit -m -h` 의 `-h` 는 메시지인데 도움말로 읽어 놓친다.
- 줄인 옵션(`git commit --dry`)과 줄 잇기(줄 끝 역슬래시와 줄바꿈) 뒤의 `-h`. 실행하지 않는 명령인데
  경계로 센다(거짓 양성). 문턱 위에서 문장 하나를 낼 뿐이다.
- 인계를 지시한 뒤 모델이 인계하지 않는 때로 보고 이은 세션. 표지가 이미 있어, 그 세션의 Stop
  알림은 그 뒤로도 나지 않는다. 인계했는지는 훅이 알 수 없다.
- 실패한 커밋과 PR 만들기. 문장이 "성공했으면"으로 미룬다. 실패한 셸 명령이 PostToolUse 를
  일으키는지 PostToolUseFailure 로 가는지는 재지 않았다.
- 끝 `TAIL_BYTES` 안에 모델 응답이 없는 트랜스크립트. 침묵한다.
- 서브에이전트가 한 커밋. 위의 침묵이다.
- 병렬 호출의 앞쪽 호출에서 그 호출을 낸 응답이 아직 기록되지 않은 때. 그 앞의 응답을 읽어 조금 작게
  나온다. 다음 경계가 받는다(어림).
- 클라우드 세션. 인계하지 않는다.
- 다른 저장소에 한 커밋. `git -C <임시 저장소> commit` 도 경계로 센다(거짓 양성).
- `gh api graphql` 의 `createPullRequest` 와 변수로 준 엔드포인트(`gh api "$ENDPOINT"`)로 연 PR.
  `repos/<주인>/<이름>/pulls` 를 글자로 보지 못해 놓친다(거짓 음성).
- `transcript_path` 가 더 쓰이지 않는 사본을 가리킬 때의 낡은 값(`hook_midturn_korean` 독스트링).
- 데스크톱 세션 안에서 띄운 `claude -p` 세션. 대화형과 가르지 못한다.
- `handoff.md` 도 인계 절도 없는 옛 워크트리(이 훅을 들인 커밋 전에 딴 브랜치)의 세션. 훅과 같은
  체크아웃의 `handoff.md` 를 가리켜, 그 경로가 작업 폴더 밖이면 Read 가 승인을 물을 수 있다(위의 C).
- `cwd` 가 다른 저장소일 때. 그 저장소의 사본에 `handoff.md` 나 인계 절이 있으면 그것을 가리킨다.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Literal, TypedDict

Boundary = Literal["셀프 리뷰 직전", "커밋 뒤", "PR 연 뒤"]

# 아래 넷(문턱, 끝에서 읽는 바이트, 표지 폴더, `marker_name`)과 `session_context`·`tail_lines` 는
# tools/hook_handoff_notice.py 와 같다.
THRESHOLD = 200_000
TAIL_BYTES = 2 * 1024 * 1024
STATE_DIR = "agent-os-handoff"
SKILL_RELATIVE = Path(".claude") / "skills" / "next-session" / "SKILL.md"
HANDOFF_RELATIVE = SKILL_RELATIVE.with_name("handoff.md")
HANDOFF_PATH = Path(__file__).resolve().parent.parent / HANDOFF_RELATIVE
# 인계 절차가 든 판의 next-session `SKILL.md` 에만 있는 절의 머리. 나눈 판은 그 머리 아래에
# `handoff.md` 를 가리켜, 이 머리를 찾는 옛 훅도 새 판에서 길을 잃지 않는다. tests/tools 가 이
# 저장소의 사본에 있는지 본다.
SECTION = "## 인계할 때"

SHELL_TOOLS = frozenset({"Bash", "PowerShell"})
SKILL_TOOL = "Skill"
SKILL = "code-review"
PATH_PREFIX = ".claude"
_PATH_PREFIXES = (f"{PATH_PREFIX}/", f"{PATH_PREFIX}\\")
# tools/hook_pr_next_session.py 의 `MCP_TOOLS` 가운데 "create" 인 이름. 시험이 대조한다.
MCP_CREATE_TOOLS = (
    "mcp__plugin_github_github__create_pull_request",
    "mcp__github__create_pull_request",
)
_NOT_RUNNING = frozenset({"--dry-run", "--help", "-h"})

# 판정은 hook_git_main_commit 에서 출발해 `--git-dir=`·`--work-tree=` 를 더 지난다.
# `commit-tree`·`commit-graph` 는 배관이다. `gh pr new` 는 `gh pr create` 의 별칭이다.
_GIT_COMMIT = re.compile(
    r"git\s+(?:(?:-C|-c)\s+\S+\s+|--no-pager\s+|--(?:git-dir|work-tree)=\S+\s+)*commit(?![\w-])"
)
_GH_PR_CREATE = re.compile(r"gh\s+(?:(?:-R|--repo)\s+\S+\s+)*pr\s+(?:create|new)(?![\w-])")
_HEREDOC_OPENER = re.compile(r"<<(-?)\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\2")
_QUOTED = re.compile(r"'[^']*'|\"(?:[^\"\\]|\\.)*\"")
_SEPARATOR = re.compile(r"\|\||&&|\$\(|`|(?<![<>])[&|]|[;\n]")
_COMMAND_PREFIX = re.compile(r"^(?:\s+|[({]|[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*")

# `gh api` 로 `pulls` 에 POST 하는 PR 만들기(대기열 408). 아래 상수와
# `opens_pr_by_api`·`_api_segments` 는 tools/hook_pr_next_session.py 와 같고, 두 시험이 같은
# 표(`tests/tools/gh_api_cases.py`)를 쓴다.
_GH_API = re.compile(r"gh\s+api(?![\w-])")
_NOT_WORD = re.compile(r"[^\w./{}:@=+,-]")
_PULLS = re.compile(r"(?:^|/)repos/[^/]+/[^/]+/pulls/?$")
_API_VALUE_OPTIONS = frozenset(
    {
        "-X",
        "--method",
        "-f",
        "--raw-field",
        "-F",
        "--field",
        "-H",
        "--header",
        "--input",
        "-q",
        "--jq",
        "-t",
        "--template",
        "--hostname",
        "-p",
        "--preview",
        "--cache",
    }
)
_API_BODY_OPTIONS = frozenset({"-f", "--raw-field", "-F", "--field", "--input"})
_CONTINUATION = re.compile(r"`\n")


class HookPayload(TypedDict, total=False):
    """Claude Code 가 stdin 으로 주는 PostToolUse 훅 입력 중 이 훅이 읽는 부분."""

    agent_id: str
    session_id: str
    transcript_path: str
    cwd: str
    tool_name: str
    tool_input: dict[str, object]


class Usage(TypedDict, total=False):
    input_tokens: object
    cache_creation_input_tokens: object
    cache_read_input_tokens: object


class Message(TypedDict, total=False):
    model: str
    usage: Usage


class Record(TypedDict, total=False):
    """트랜스크립트 JSONL 한 줄 중 이 훅이 읽는 부분."""

    type: str
    subtype: str
    isSidechain: bool
    message: Message


def boundary_of(tool_name: str, tool_input: Mapping[str, object]) -> Boundary | None:
    """이 도구 호출이 단계 경계면 그 이름, 아니면 None. 트랜스크립트를 보지 않는다."""
    if tool_name in MCP_CREATE_TOOLS:
        return "PR 연 뒤"
    if tool_name == SKILL_TOOL:
        skill = tool_input.get("skill")
        return "셀프 리뷰 직전" if isinstance(skill, str) and is_this_skill(skill) else None
    command = tool_input.get("command")
    if tool_name not in SHELL_TOOLS or not isinstance(command, str):
        return None
    segments = _executed_segments(command)
    if any(_runs(_GIT_COMMIT, segment) for segment in segments):
        return "커밋 뒤"
    if any(_runs(_GH_PR_CREATE, segment) for segment in segments):
        return "PR 연 뒤"
    if any(opens_pr_by_api(segment) for segment in _api_segments(command)):
        return "PR 연 뒤"
    return None


def is_this_skill(name: str) -> bool:
    """이 저장소의 `code-review` 인가. 앞의 `/` 를 벗긴 그대로의 이름이거나, `.claude` 폴더나 그
    아래를 가리키는 경로 접두에 `:code-review` 가 붙은 것이다. 플러그인의 `code-review:code-review`
    는 아니다(hook_grill_design_check 의 `is_this_skill` 과 같은 방식)."""
    prefix, colon, skill = name.lstrip("/").rpartition(":")
    in_folder = prefix == PATH_PREFIX or prefix.startswith(_PATH_PREFIXES)
    return skill == SKILL and (not colon or in_folder)


def _runs(pattern: re.Pattern[str], segment: str) -> bool:
    """조각이 `pattern` 의 명령을 실제로 돌리는가. `--dry-run`·`--help`·`-h` 는 돌리지 않는다.
    `--` 뒤는 경로라 옵션으로 보지 않는다."""
    match = pattern.match(segment)
    if match is None:
        return False
    words = segment[match.end() :].split()
    options = words[: words.index("--")] if "--" in words else words
    return not _NOT_RUNNING.intersection(options)


def _executed_segments(command: str) -> list[str]:
    """명령 위치부터 시작하는 조각들. 인용은 `_` 로 바꿔 옵션 값 자리를
    남긴다(hook_git_main_commit)."""
    joined = _QUOTED.sub("_", "\n".join(_without_heredoc_bodies(command)))
    return [_COMMAND_PREFIX.sub("", piece, count=1) for piece in _SEPARATOR.split(joined)]


def opens_pr_by_api(segment: str) -> bool:
    """조각이 `gh api` 로 `repos/<주인>/<이름>/pulls` 에 POST 하는가. 메서드는 `-X`·`--method` 가
    정하고, 없으면 몸(`-f`·`-F`·`--input`)이 있을 때 POST 다(`gh api --help`,
    `.scratch/harness/probes/gh_api_method.py`)."""
    match = _GH_API.match(segment)
    if match is None:
        return False
    words = segment[match.end() :].split()
    method: str | None = None
    body = False
    endpoint: str | None = None
    index = 0
    while index < len(words):
        word = words[index]
        index += 1
        if word == "--":
            if endpoint is None and index < len(words):
                endpoint = words[index]
            break
        if not word.startswith("-") or word == "-":
            endpoint = word if endpoint is None else endpoint
            continue
        if word in _NOT_RUNNING:
            return False
        if word.startswith("--"):
            option, equals, value = word.partition("=")
        else:
            option, value = word[:2], word[2:]
            equals = "=" if value else ""
            value = value.removeprefix("=")  # `-X=POST` 의 `=` 는 값이 아니다
        if not equals and option in _API_VALUE_OPTIONS:
            value = words[index] if index < len(words) else ""
            index += 1
        if option in ("-X", "--method"):
            method = value.upper()
        elif option in _API_BODY_OPTIONS:
            body = True
    if endpoint is None or _PULLS.search(endpoint) is None:
        return False
    return method == "POST" if method is not None else body


def _api_segments(command: str) -> list[str]:
    """`_executed_segments` 와 같되 인용 구간을 그 안의 글로 남긴다. 엔드포인트가 인용되기
    쉽다(`"repos/{owner}/{repo}/pulls"`). 공백과 셸 문자는 `_` 로 바꿔 한 낱말로 두고, 빈 인용도
    `_` 로 자리를 지킨다. PowerShell 의 줄 이음(줄 끝 백틱)은 이어 붙인다."""
    lines = _CONTINUATION.sub(" ", "\n".join(_without_heredoc_bodies(command)))
    joined = _QUOTED.sub(lambda quoted: _NOT_WORD.sub("_", quoted.group(0)[1:-1]) or "_", lines)
    return [_COMMAND_PREFIX.sub("", piece, count=1) for piece in _SEPARATOR.split(joined)]


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


def tail_lines(path: Path, limit: int) -> list[str]:
    """파일 끝 `limit` 바이트의 줄들. 앞이 잘렸으면 첫 줄을 버린다. 읽지 못하면 빈 목록."""
    try:
        with path.open("rb") as transcript:
            size = transcript.seek(0, os.SEEK_END)
            start = max(0, size - limit)
            transcript.seek(start)
            data = transcript.read()
    except OSError:
        return []
    # JSONL 은 LF 로만 가른다. `splitlines` 는 기록 안의 날것 U+2028·U+0085 에서도 가른다.
    lines = [line.rstrip("\r") for line in data.decode("utf-8", errors="replace").split("\n")]
    lines = [line for line in lines if line]
    return lines[1:] if start > 0 else lines


def session_context(lines: Sequence[str]) -> int | None:
    """메인 세션의 마지막 모델 응답이 든 입력 토큰. 그런 응답이 없거나 그 뒤에 압축 경계가 있으면
    None 이다."""
    context: int | None = None
    for line in lines:
        # 도구 결과처럼 큰 user 기록은 풀지 않는다.
        if '"assistant"' not in line and '"compact_boundary"' not in line:
            continue
        try:
            record: Record = json.loads(line)
        except ValueError:
            continue
        if record.get("isSidechain"):
            continue
        if record.get("type") == "system" and record.get("subtype") == "compact_boundary":
            context = None
            continue
        message = record.get("message")
        if record.get("type") != "assistant" or not isinstance(message, dict):
            continue
        usage = message.get("usage")
        if message.get("model") == "<synthetic>" or not isinstance(usage, dict):
            continue
        context = sum(
            value
            for value in (
                usage.get("input_tokens", 0),
                usage.get("cache_creation_input_tokens", 0),
                usage.get("cache_read_input_tokens", 0),
            )
            if isinstance(value, int)
        )
    return context


def marker_name(session_id: str) -> str:
    """한 세션의 Stop 알림 표지 파일 이름. 세션 ID 의 해시다(tools/launch_hook.py 의 모양)."""
    return hashlib.sha256(session_id.encode("utf-8", "surrogatepass")).hexdigest()


def skill_for(cwd: str | None) -> Path:
    """문장이 가리킬 인계 절차 파일. `cwd` 에서 위로 올라가 next-session `SKILL.md` 가 처음 나오는
    폴더에 `handoff.md` 가 있으면 그것, 없고 그 `SKILL.md` 에 인계 절이 있으면 그 `SKILL.md`, 둘 다
    아니면 훅과 같은 체크아웃의 `handoff.md` 다. 사본은 `SKILL.md` 로 알아보므로 `handoff.md` 만
    있는 폴더는 지나친다. 처음 만난 사본에서 더 올라가지 않는다 — 워크트리는 주 체크아웃 아래에
    있어, 올라가면 승인을 묻는 주 체크아웃의 사본에 닿는다."""
    start = Path(cwd) if cwd else None
    # 상대 경로(`C:` 처럼 드라이브만 남은 것도)는 훅의 작업 폴더에 기대므로 고르지 않는다.
    if start is None or not start.is_absolute():
        return HANDOFF_PATH
    for folder in (start, *start.parents):
        skill = folder / SKILL_RELATIVE
        if not skill.is_file():
            continue
        handoff = folder / HANDOFF_RELATIVE
        if handoff.is_file():
            return handoff
        try:
            has_section = SECTION in skill.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return HANDOFF_PATH
        return skill if has_section else HANDOFF_PATH
    return HANDOFF_PATH


def context_for(boundary: Boundary, size: int, skill: Path = HANDOFF_PATH) -> str:
    """모델에게 넣을 인계 문장. `skill` 은 Read 로 열 인계 절차 파일이다(`skill_for`)."""
    done = "방금 불린" if boundary == "셀프 리뷰 직전" else "방금 친 명령이 성공했으면"
    follow = (
        "그 파일의 결정표에서 인계 줄을 따른다"
        if skill.name == SKILL_RELATIVE.name
        else "그 파일의 순서를 따른다"
    )
    lead = (
        f"세션 컨텍스트가 {size:,} 토큰으로 인계 문턱 {THRESHOLD:,} 을 넘은 채 단계 경계 "
        f"`{boundary}` 에 왔다({done} 그 경계다). 인계의 계기다. 사용자에게 묻지 말고 "
        f"`{skill.as_posix()}` 를 Read 도구로 연다. Skill 도구로 부르지 않는다(실행 중이던 "
        f"세션의 Skill 도구는 인계 절차가 없는 옛 사본을 실을 수 있다). {follow}. 그 파일의 "
        "인계하지 않는 때에 들면 넘기지 않고 잇는다."
    )
    if boundary == "셀프 리뷰 직전":
        return lead + (
            " 넘길 때는 방금 불린 code-review 의 단계를 밟지 않는다. 셀프 리뷰는 새 세션이 한다."
        )
    if boundary == "PR 연 뒤":
        return lead + (
            " 봇 회차와 병합도 새 세션이 한다. 함께 온 hook_pr_next_session 의 계기(Skill 도구로 "
            "next-session 을 돌려 병합까지 먼저 마친다)보다 이것이 앞선다."
        )
    return lead


def mark_handed_off(session_id: str | None) -> None:
    """Stop 알림이 이 세션에서 다시 나지 않게 표지를 만든다. 이미 있거나 만들지 못하면 둔다."""
    if not session_id:
        return
    try:
        directory = os.path.join(tempfile.gettempdir(), STATE_DIR)
        os.makedirs(directory, exist_ok=True)
        os.close(
            os.open(os.path.join(directory, marker_name(session_id)), os.O_CREAT | os.O_WRONLY)
        )
    except OSError:
        return


def handoff_context(payload: HookPayload, environ: Mapping[str, str]) -> str | None:
    """인계를 지시할 문장, 아니면 None. 경계일 때만 트랜스크립트를 연다."""
    if "agent_id" in payload or environ.get("CLAUDE_CODE_REMOTE") == "true":
        return None
    tool_input = payload.get("tool_input")
    boundary = boundary_of(
        payload.get("tool_name", ""), tool_input if isinstance(tool_input, dict) else {}
    )
    transcript_path = payload.get("transcript_path")
    if boundary is None or not transcript_path:
        return None
    size = session_context(tail_lines(Path(transcript_path), TAIL_BYTES))
    if size is None or size <= THRESHOLD:
        return None
    return context_for(boundary, size, skill_for(payload.get("cwd")))


def main() -> int:
    # stdin 은 바이트로. 이유는 .claude/rules/tools.md(대기열 25).
    payload: HookPayload = json.load(sys.stdin.buffer)
    context = handoff_context(payload, os.environ)
    if context is None:
        return 0
    mark_handed_off(payload.get("session_id"))
    output = {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": context}}
    # ASCII 로 낸다. 훅 환경의 stdout 은 cp949 일 수 있다(대기열 25).
    print(json.dumps(output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
