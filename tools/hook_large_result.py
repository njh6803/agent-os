"""PostToolUse 훅(Read|Bash|PowerShell). 범위 없이 읽은 Read 결과가 2만 자를, Bash·PowerShell 결과가
1만 자를 넘으면 결과의 크기와 문턱을 들어, 일부만 필요했으면 다음에는 범위를 좁히라는 계기를
컨텍스트에 넣는다.

근거는 `.scratch/token-usage/spec.md` 의 "큰 결과 알림 훅"이다. 큰 결과는 그대로 컨텍스트에 남아
뒤의 모든 호출에 실려 간다. 지난 7일 메인 세션에서 범위 없이 2만 자를 넘은 Read 는 Read 의 7.3%였고
기록 항목 무게의 3.43%였다(명세가 든 `.scratch/token-usage/probes/measure.py results 168`). 막지
않는다 (ADR 0033) — 전체가 필요한 읽기도 있고, 훅은 그 판단을 보지 못한다.

- 문턱은 Read 2만 자(`READ_LIMIT`), Bash·PowerShell 1만 자(`SHELL_LIMIT`)이고 넘을 때(초과) 알린다.
  명세가 측정으로 정한 값이라 바꾸지 않는다. Read 에 `offset` 이나 `limit` 을 줬으면 알리지 않는다.
- 같은 대상이 넘을 때마다 알린다. 표지를 두지 않는다(명세 "되풀이").
- 크기는 모델이 받는 결과의 글자 수다. `tool_response` 는 그 글이 아니라 도구의 구조화된 출력이라
  (명세 "크기") 거기서 셈한다. Read 는 `file.content` 에 줄마다 `<줄 번호>\\t` 접두의 글자 수를
  더하고 (줄 번호는 `file.startLine` 부터), Bash·PowerShell 은 `stdout` 과 `stderr` 의 글자 수를
  더한다. 그 셈이 같은 호출의 기록 `tool_result` 본문 길이와 맞는지는
  `.scratch/token-usage/probes/large_result/` 가 실제 페이로드로 본다(결과는 그 README 행). 글
  결과(`type` 이 `text`)가 아닌 Read 와 `isImage` 인 셸 출력은 0자다. 그림이 `image` 로 오는 것은
  프로브가 봤고, PDF·노트북의 `type` 값은 재지 않았다.
- 파일로 옮겨진 셸 출력(`persistedOutputPath` 가 있는 결과)도 0자로 센다. 프로브의 `bash_large`
  (`seq 1 8000`, 38893자)에서 Claude Code 는 출력을 파일에 저장하고 모델에는 경로와 앞부분의
  미리보기만 줬다. `stdout` 은 앞 30000자로 잘려 있었고 기록 본문은 2323자였다. 그 미리보기는 문턱
  아래라 알릴 것이 없다. 옮기는 경계가 3만 자인지는 그 표본 하나와 잘린 길이에서 어림한 것이다.

못 보는 것:
- 서브에이전트의 호출에도 같은 문장을 내지만, 그 `additionalContext` 가 서브에이전트의 모델에
  닿는지는 재지 않았다.
- 파일로 옮겨진 출력의 미리보기 길이. 0자로 세므로 미리보기가 문턱을 넘는 판이 오면 놓친다.
- 3만 자를 넘는 PowerShell 출력. 프로브에 표본이 없다. Bash 와 같은 키(`persistedOutputPath`)로
  오지 않으면 잘린 `stdout` 을 세어 알리는데, 모델은 미리보기만 받았을 수 있다(거짓 양성).
- 백그라운드로 돌린 명령의 출력을 다른 도구로 받은 것. 매처 밖이라 이 훅에 오지 않는다.
- `stdout` 과 `stderr` 가 둘 다 찬 결과의 이음새. 프로브의
  `bash_stderr`(`echo out-line; echo err-line >&2`)에서 Bash 는 stderr 를 stdout 에 합쳐 내고
  `stderr` 칸은 비어 있었다. 둘 다 찬 결과를 모델이 어떤 글로 받는지(사이에 줄바꿈이 드는지)는 보지
  못해 두 칸의 길이만 더한다.
- Read 의 결과 끝에 Claude Code 가 덧붙이는 리마인더처럼 `tool_response` 밖에서 더해지는 글.
- 노트북(`.ipynb`) 결과. 글 결과(`type` 이 `text`)가 아니라 0자로 센다.
- 결과를 무엇에 쓰는지. 전체가 필요했어도 알린다(문장이 따르지 않아도 된다고 적는다).
- 결과 객체의 키가 바뀐 판. 그러면 0자로 세어 침묵한다.
"""

from __future__ import annotations

import json
import sys
from typing import TypedDict

READ = "Read"
SHELLS = ("Bash", "PowerShell")
READ_LIMIT = 20_000
SHELL_LIMIT = 10_000
# 알림의 첫 문장. 수가 들지 않아 프로브가 모델이 이 문장을 옮겼는지 본다.
LEAD = "이 도구 결과는 큰 결과 알림의 문턱을 넘었다"
# 알림에 드는 명령은 이만큼만 든다.
SHOWN = 80


class ToolInput(TypedDict, total=False):
    file_path: str
    offset: int
    limit: int
    command: str


class ReadFile(TypedDict, total=False):
    filePath: str
    content: str
    numLines: int
    startLine: int
    totalLines: int


class ToolResponse(TypedDict, total=False):
    """`tool_response` 의 칸. Read 는 `type`·`file` 을, Bash·PowerShell 은 나머지를 쓴다. 모양은
    `.scratch/token-usage/probes/large_result/payloads.jsonl` 에서 옮겼다. 실제 값이 이 모양과
    다를 수 있어 읽을 때마다 형을 본다."""

    type: str
    file: ReadFile
    stdout: str
    stderr: str
    interrupted: bool
    isImage: bool
    noOutputExpected: bool
    persistedOutputPath: str
    persistedOutputSize: int


class HookPayload(TypedDict, total=False):
    """Claude Code 가 stdin 으로 주는 훅 입력 중 이 훅이 읽는 부분."""

    tool_name: str
    tool_input: ToolInput
    tool_response: ToolResponse


def numbered_chars(content: str, start: int) -> int:
    """줄마다 `<줄 번호>\\t` 를 붙인 글의 글자 수."""
    if not content:
        return 0
    count = content.count("\n") + 1
    return len(content) + sum(len(str(start + n)) + 1 for n in range(count))


def read_chars(response: ToolResponse) -> int:
    if response.get("type") != "text":
        return 0
    file = response.get("file")
    if not isinstance(file, dict):
        return 0
    content = file.get("content")
    start = file.get("startLine")
    if not isinstance(content, str):
        return 0
    return numbered_chars(content, start if isinstance(start, int) else 1)


def shell_chars(response: ToolResponse) -> int:
    if response.get("isImage") is True or "persistedOutputPath" in response:
        return 0
    return sum(
        len(value)
        for value in (response.get("stdout"), response.get("stderr"))
        if isinstance(value, str)
    )


def result_chars(payload: HookPayload) -> int:
    """모델이 받는 결과의 글자 수를 `tool_response` 에서 셈한 값. 모르면 0이다."""
    response = payload.get("tool_response")
    if not isinstance(response, dict):
        return 0
    tool = payload.get("tool_name")
    if tool == READ:
        return read_chars(response)
    if tool in SHELLS:
        return shell_chars(response)
    return 0


def context_for(payload: HookPayload) -> str | None:
    """결과가 문턱을 넘었으면 컨텍스트 문장, 아니면 None."""
    tool = payload.get("tool_name")
    tool_input = payload.get("tool_input")
    fields: ToolInput = tool_input if isinstance(tool_input, dict) else {}
    if tool == READ:
        if "offset" in fields or "limit" in fields:
            return None
        limit = READ_LIMIT
        target = f"`{fields.get('file_path', '')}`"
        narrower = "Grep 으로 필요한 줄을 찾아 Read 의 offset·limit 로 그 부분만 읽는다"
    elif tool in SHELLS:
        limit = SHELL_LIMIT
        command = str(fields.get("command", ""))
        shown = command if len(command) <= SHOWN else command[:SHOWN] + "…"
        target = f"명령 `{shown}`"
        narrower = (
            "명령의 출력을 거른다(`head`, `Select-Object -First`, `git diff --stat` 같은 요약)"
        )
    else:
        return None
    chars = result_chars(payload)
    if chars <= limit:
        return None
    return (
        f"{LEAD}. {tool} {target} 의 결과가 약 {chars:,}자로 문턱 {limit:,}자보다 크다. 이 결과는"
        " 그대로 컨텍스트에 남아 뒤의 모든 호출에 함께 실려 간다. 일부만 필요했으면 다음에는"
        f" {narrower}. 전체가 필요했으면 이 알림은 따르지 않아도 된다."
    )


def main() -> int:
    payload: HookPayload = json.load(sys.stdin.buffer)
    context = context_for(payload)
    if context is None:
        return 0
    print(
        json.dumps(
            {"hookSpecificOutput": {"hookEventName": "PostToolUse", "additionalContext": context}}
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
