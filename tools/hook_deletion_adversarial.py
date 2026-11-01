"""PostToolUse 훅(Write|Edit). `tools/`나 `web/tools/` 아래 코드에 지우는 호출(`shutil.rmtree`,
`rmSync`, `unlink`, `git worktree remove` 등)이 든 줄을 더하면, 커밋하기 전에 그 도구의 판정을 깨는
입력으로 반박하라는 계기를 세션·에이전트마다 한 번 컨텍스트에 넣는다.

왜. `.claude/rules/tools.md` 의 "지우거나 덮어쓰는 도구" 항목이 이미 그렇게 하라고 적는다. 그런데
그 항목은 `tools/**`·`tests/tools/**` 를 Read 로 열 때 실릴 뿐이고(`web/tools/**` 는 규칙의 `paths`
에 없어 `web/tools/judge-trees.ts` 를 열어도 실리지 않는다), 지우는 호출을 써 넣는 순간에 모델이 그
문장을 보고 있다는 보장이 없다. 항목을 읽은 뒤에도 반박 시험이 판정을 깨는 입력을 빠뜨린 채 지우는
길이 셀프 리뷰를 지나 PR 직전 `bug-perf-review` 에서야 나왔다. `web/tools/judge-trees.ts` 가 사람이
지은 `web/judge-config/` 같은 폴더를 지우는 길(대기열 442), `tools/tidy_checkouts.py` 가 정션 안의
파일을 휴지통으로 옮기는 길과 MAX_PATH 에 걸린 깊은 폴더를 읽지 못하는 길(대기열 442 행의 3회차와
2회차)이다. 쓰는 순간에 알리는 계기 훅이고 막지 않는다. 지우는 호출이 자기가 만든 임시 폴더만 지우는
정리인지, 사람이 지은 폴더에 닿는지는 모델이 가른다(`.claude/rules/tools.md` 의 계기·막는 훅 가름).

왜 따로 등록하는가. Write·Edit 의 다른 PostToolUse 훅은 저마다 다른 일을 판정한다(일지 회고 계기,
ruff, 줄 구분 문자, 스크래치 스크립트, 프로브 결론, 일지 근거, 디자인 폴더, 화면 코드,
측정 낱말). 여기에 얹으면 독스트링의 왜·못 보는 것과 페이로드 표의 사례가 두 판정으로 섞인다.
등록은 첫 `Write|Edit` 묶음에 더한다. 값은 Write·Edit 마다 래퍼를 거친 파이썬 한 번이다(약 0.2초,
이 훅은 재지 않았고 `.claude/rules/tools.md` 시간 항목의 어림이다).

판정. 도구가 Write·Edit 이고 `tool_input.file_path` 가 문자열이며 `is_tool_code` 가 참이면, 더한
줄(`added_lines`) 가운데 `DELETION_CALLS` 의 꼴이 하나라도 든 줄(`deleting_lines`)을 고른다. 더한
줄은 쓰기 전 파일에 없던 쓴 뒤 파일의 줄이다. 쓰기 전 파일은 결과의 `originalFile` 이다(덮어쓴
Write 와 Edit 에서 문자열이고, 새 파일을 만든 Write 에서는 null 이다). 쓴 뒤 파일은 Write 면
`content`, Edit 면 `originalFile` 에서 `old_string` 을 `new_string` 으로 바꾼 글이다(`replace_all`
이 참이면 모두, 아니면 처음 하나). Edit 의 조각은 줄의 일부일 수 있어, 조각만 보면 같은 줄의 앞뒤를
보지 못한다. `originalFile` 이 문자열이 아니거나 `old_string` 이 그 안에 없는 Edit 은 조각 둘을 쓰기
전·뒤 글로 본다. 줄 집합의 차라 순서와 횟수는 보지 않는다. 걸린 줄은 앞의 `SHOWN_LINES` 개를
`LINE_WIDTH` 글자로 잘라 문장에 싣는다.

대상 경로. 경로를 `/`·`\\` 로 가른 토막(대소문자를 가리지 않는다) 가운데 폴더 이름이 `tools` 인
토막이 있고, 그 바로 앞 토막이 `tests` 가 아니며, 파일 확장자가 `CODE_SUFFIXES` 이고, 파일 이름이
시험 파일의 꼴(`test_*`, `*_test.*`, `conftest.py`, `*.test.*`, `*.test-d.*`, `*.spec.*`)이 아니면
도구 코드다. 시험이 임시 폴더를 지우는 것(`tmp_path` 정리)은 이 알림의 대상이 아니라서
`tests/tools/` 와 시험 파일을 뺀다.

한 번. 표지는 `tools/hook_scratch_probe_rule.py` 의 모양이다. 임시 폴더(`tempfile.gettempdir()`)
아래 `STATE_DIR` 에 세션 ID 와 `agent_id`(서브에이전트는 컨텍스트가 따로다)의 해시로 빈 파일을
`O_EXCL` 로 만든다. 걸리지 않은 편집은 표지를 쓰지 않는다. 세션을 모르거나 표지를 쓰지 못하면
호출마다 알린다(알리지 못하는 것보다 되풀이가 낫다).

못 보는 것:
- 도우미 함수 뒤의 지우기. 호출 줄이 `delete_path(folder)` 꼴이면 알리지 않는다. 도우미 안에 지우는
  호출을 쓰는 편집이 그 호출을 볼 뿐이다.
- 이미 있는 지우기 둘레의 판정을 고치는 편집. 지우는 호출 줄을 더하지 않고 그 앞의 안전 판정만
  고치면 지나간다. 반박이 가장 필요한 자리인데 줄 단위로 가를 수 없어 호출 줄만 본다(대기열 442 의
  행이 고른 "지우는 호출을 쓰는 편집" 의 범위다). 지우는 줄의 들여쓰기가 그대로일 때만 그렇다.
  보호문을 한 겹 더 둘러 지우는 줄의 들여쓰기가 바뀌면 그 줄이 더한 줄이 되어 알린다.
- 같은 글자의 줄을 또 더하는 편집. 더한 줄은 줄 집합의 차라, 파일에 이미 있는 줄과 글자가 같은
  지우는 줄(`shutil.rmtree(path)`)을 다른 함수에 또 더하면 알리지 않는다.
- 호출 목록 밖의 지우기. 리스트 인자로 부르는 `["rm", "-rf", path]`, `os.system("rm -rf x")`,
  `rm -R`, `rm --recursive`, 플래그 없는 `rm "$f"`, `rimraf.sync(`, `.Delete(`, `rmdir /s`,
  `git branch --delete`는 지나간다. 확장자가 `.bat`·`.cmd`·`.psm1` 인 파일도 대상이 아니다.
- 이름이 시험 파일 꼴인 도구 파일. `tools/test_runner.py`, `tools/latest_test.py` 는 시험 파일로
  세어 지나간다.
- 덮어쓰는 호출(`open(path, "w")`, `os.replace`, `shutil.move`). `.claude/rules/tools.md` 항목은
  "지우거나 덮어쓰는" 이라고 적지만 이 훅은 지우는 호출만 본다.
- 독스트링·문자열 안의 호출 낱말. `#`·`//` 로 시작하는 줄만 주석으로 걸러 내므로 독스트링에 든
  `shutil.rmtree(path)` 도 알린다. 같은 까닭으로 꼬리 주석(`x = 1  # shutil.rmtree(p)`), 블록
  주석 줄(`/* rmSync(x) */`, ` * rmSync(x)`), 같은 이름을 선언하는 줄(`def rmtree(a):`,
  `def unlink(self):`), 지우지 않는 `git clean -n` 도 알린다.
- Bash heredoc·`>>`·`sed -i` 로 쓴 도구 코드. 이 훅은 편집 도구에만 붙는다.
- 저장소 밖의 `tools` 폴더와 `tools` 토막이 든 다른 자리. 폴더 이름만 보므로
  `C:\\Users\\User\\tools\\x.py` 도, 저장소 안의 `web/apps/admin/tools/`, `plugins/x/tools/`,
  `node_modules/pkg/tools/` 아래 코드도 대상이다(티켓의 `tools/`·`web/tools/` 보다 넓다).
- 한 번 알린 뒤의 지우는 호출. 표지는 세션·에이전트마다 하나라, 임시 폴더 정리를 먼저 써서 알림을
  "무시"로 넘긴 세션이 뒤에 쓴 사람 폴더를 지우는 길에는 다시 알리지 않는다. 컨텍스트 압축이나 이어
  하기로 알림 문장이 사라져도 같은 세션 ID 면 표지가 남아 알리지 않는다.
- 알림이 실제 세션의 모델에게 닿는지, 서브에이전트에게 닿는지. 아직 재지 않았다.
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
CODE_SUFFIXES = frozenset(
    {".py", ".ts", ".tsx", ".mts", ".cts", ".js", ".mjs", ".cjs", ".ps1", ".sh"}
)
# 지우는 호출의 꼴. 리스트 인자로 git 을 부르는 꼴(`"worktree", "remove"`)도 든다.
DELETION_CALLS = tuple(
    re.compile(pattern)
    for pattern in (
        r"\brmtree\s*\(",
        r"\bos\.(?:remove|unlink|rmdir|removedirs)\s*\(",
        r"\b(?:unlink|rmdir)\s*\(",
        r"\b(?:rmSync|rmdirSync|unlinkSync|rimraf(?:Sync)?)\s*\(",
        r"(?<![\w$.])rm\s*\(",
        r"\.rm\s*\(",
        r"\bworktree\s+remove\b",
        r"""["']worktree["']\s*,\s*["']remove["']""",
        r"\bgit\s+(?:-\S+\s+)*clean\b",
        r"""["']clean["']\s*,\s*["']-\w+["']""",
        r"\bbranch\s+-[dD]\b",
        r"""["']branch["']\s*,\s*["']-[dD]["']""",
        r"\bRemove-Item\b",
        r"(?:^|[\s;&|(])rm\s+-\w*[rf]",
    )
)
COMMENT_PREFIXES = ("#", "//")
SHOWN_LINES = 3
LINE_WIDTH = 160
STATE_DIR = "agent-os-deletion-adversarial"
# 알림의 첫 문장. 알림이 모델에게 닿는지 잴 때 모델이 옮겼는지 볼 문구다.
LEAD = "도구 코드에 지우는 호출이 든 줄을 더했다"
_BODY = (
    '{lead}. `.claude/rules/tools.md` 의 "지우거나 덮어쓰는 도구" 항목이 정한 대로, 커밋하기 전에'
    " 임시 저장소에서 이 지우기의 판정을 깨려는 입력으로 반박한다. 시험이 고른 입력으로는 부족하다."
    " 넣어 볼 입력은 다섯이다. 첫째, 지우는 폴더와 같은 꼴의 이름으로 사람이 지은 폴더와 그 안의"
    " 커밋하지 않은 파일. 둘째, 윈도 경로 정규화가 바꾸는 이름(끝의 점, 대소문자, 짧은 이름)."
    " 셋째, 지우는 자리 안의 링크(심볼릭 링크, junction). 넷째, MAX_PATH 를 넘는 깊은 경로."
    " 다섯째, 앞에서 판정을 깬 입력을 같은 값을 견주는 다른 자리(같은 판정 안의 다른 견줌,"
    " 그 판정을 다시 하는 하위 명령)에도 넣어 본다. 지우는 대상이 이 도구가 방금 만든 임시"
    " 폴더뿐이면 이 알림은 무시한다. 이 알림은 세션·에이전트마다 한 번이다."
    " 걸린 줄({count}개):\n{lines}"
)
_SPLIT = re.compile(r"[\\/]+")


class ToolInput(TypedDict, total=False):
    file_path: object
    content: object
    old_string: object
    new_string: object
    replace_all: object


class ToolResponse(TypedDict, total=False):
    type: str
    originalFile: object


class HookPayload(TypedDict, total=False):
    """Claude Code 가 stdin 으로 주는 훅 입력 중 이 훅이 읽는 부분. `tool_input`·`tool_response` 는
    객체가 아닌 값이 와도 `context_for` 가 런타임에 다시 본다."""

    tool_name: str
    tool_input: ToolInput
    tool_response: ToolResponse
    session_id: str
    agent_id: str


def _is_test_file(name: str) -> bool:
    stem = name.rsplit(".", 1)[0]
    return (
        name == "conftest.py"
        or stem.startswith("test_")
        or stem.endswith("_test")
        or any(mark in name for mark in (".test.", ".test-d.", ".spec."))
    )


def is_tool_code(path: str) -> bool:
    """`tools` 폴더 아래의 시험 파일이 아닌 코드 파일인가. 바로 앞 폴더가 `tests` 인 `tools` 는
    시험의 하네스라 뺀다."""
    parts = [part.casefold() for part in _SPLIT.split(path) if part]
    if not parts:
        return False
    *folders, name = parts
    if "." not in name or "." + name.rsplit(".", 1)[1] not in CODE_SUFFIXES:
        return False
    if _is_test_file(name):
        return False
    return any(
        folder == "tools" and (index == 0 or folders[index - 1] != "tests")
        for index, folder in enumerate(folders)
    )


def added_lines(old: str, new: str) -> list[str]:
    """`new` 의 비지 않은 줄 가운데 `old` 에 없던 줄."""
    before = set(old.splitlines())
    return [line for line in new.splitlines() if line.strip() and line not in before]


def deleting_lines(lines: list[str]) -> list[str]:
    """지우는 호출의 꼴이 든 줄. `#`·`//` 로 시작하는 주석 줄은 뺀다."""
    return [
        line
        for line in lines
        if not line.lstrip().startswith(COMMENT_PREFIXES)
        and any(call.search(line) for call in DELETION_CALLS)
    ]


def _before_after(payload: HookPayload, tool_input: ToolInput) -> tuple[str, str] | None:
    """(쓰기 전 글, 쓴 뒤 글). 꼴이 어긋나면 None."""
    response = payload.get("tool_response")
    original = response.get("originalFile") if isinstance(response, dict) else None
    if payload.get("tool_name") == "Edit":
        old, new = tool_input.get("old_string"), tool_input.get("new_string")
        if not isinstance(old, str) or not isinstance(new, str):
            return None
        if isinstance(original, str) and old and old in original:
            count = -1 if tool_input.get("replace_all") is True else 1
            return original, original.replace(old, new, count)
        return old, new
    content = tool_input.get("content")
    if not isinstance(content, str):
        return None
    return (original if isinstance(original, str) else ""), content


def context_for(payload: HookPayload) -> str | None:
    """도구 코드에 지우는 호출 줄을 더했으면 컨텍스트 문장, 아니면 None."""
    if payload.get("tool_name") not in TOOLS:
        return None
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return None
    path = tool_input.get("file_path")
    if not isinstance(path, str) or not is_tool_code(path):
        return None
    texts = _before_after(payload, tool_input)
    if texts is None:
        return None
    flagged = deleting_lines(added_lines(*texts))
    if not flagged:
        return None
    shown = "\n".join(f"- {line.strip()[:LINE_WIDTH]}" for line in flagged[:SHOWN_LINES])
    return _BODY.format(lead=LEAD, count=len(flagged), lines=shown)


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
