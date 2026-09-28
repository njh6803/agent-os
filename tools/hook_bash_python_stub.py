"""PreToolUse 훅(Bash). 맨 `python` 호출을 막고 `uv run python` 으로 안내한다.

CLAUDE.md 환경 함정 "맨 `python`은 프로젝트 인터프리터가 아니다"가 지침으로 적힌 뒤에도
(당시 문구는 스토어 스텁을 들었다) 2026-09-22 세션에서 어겨졌다. 기계적 패턴이라 훅이다
(교정 루프: 지침으로 적은 뒤에도 어겨지면 막는 훅 후보). 맨 python 이 무엇으로 풀리는지는
PC 마다 다르다 — Windows 스토어 스텁이면 "Python" 한 줄만 찍고 종료 코드 0 으로 조용히 끝나고,
pyenv shim 이면 프로젝트가 아닌 다른 버전이 돈다(2026-09-28 실측, 이 PC 는 3.11.9 shim).
어느 쪽이든 `.venv` 의 인터프리터가 아니라 검사가 엉뚱한 환경에서 돈다. 이 훅은 Windows 밖에서도
뜻이 있다. 못 보는 것: 활성화된 venv 의 python(그때는 맞는 인터프리터인데 막는다 — 거짓 양성),
PowerShell 도구(매처가 Bash 다).

명령어 자리의 `python`, `python3`, `python3.12` 만 본다. 명령어 자리는 명령의 시작, 파이프·연결·
세미콜론·서브셸 뒤, 그리고 `do`·`then` 같은 셸 키워드 뒤이고, 그 앞의 환경변수 대입은 건너뛴다.
`uv run python` 은 `run` 뒤라 명령어 자리가 아니다. 인자나 문자열 안의 python 도, heredoc 본문의
python 도 명령어 자리가 아니다. heredoc 본문은 heredoc 훅과 같은 규칙으로 벗긴다.
"""

from __future__ import annotations

import json
import re
import sys
from typing import TypedDict


class ToolInput(TypedDict, total=False):
    command: str


class HookPayload(TypedDict, total=False):
    """Claude Code 가 stdin 으로 주는 훅 입력 중 이 훅이 읽는 부분."""

    tool_input: ToolInput


_KEYWORDS = r"do|then|else|elif|if|while|until|exec|time|nohup"
_COMMAND_WORD = re.compile(
    rf"(?:^\s*|[|&;(){{`]\s*|\$\(\s*|\b(?:{_KEYWORDS})\s+)"  # 명령어 자리. `)` 는 case 분기
    r"(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*"  # 환경변수 대입 접두
    r"(python3?(?:\.\d+)?)(?=\s|$)",  # python, python3, python3.12
    re.MULTILINE,
)
_HEREDOC_OPENER = re.compile(r"<<(-?)\s*(['\"]?)([A-Za-z_][A-Za-z0-9_]*)\2")


def bare_python_calls(command: str) -> list[str]:
    """명령어 자리에 선 python 들. 없으면 비어 있다."""
    return _COMMAND_WORD.findall(_without_heredoc_bodies(command))


def _without_heredoc_bodies(command: str) -> str:
    """heredoc 본문 줄을 뺀 명령. 종료 줄 판정은 hook_bash_heredoc 과 같다. `<<-` 는 탭만 벗긴다."""
    kept: list[str] = []
    lines = command.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        kept.append(line)
        index += 1
        match = _HEREDOC_OPENER.search(line)
        if match is None:
            continue
        strips_tabs = match.group(1) == "-"
        terminator = match.group(3)
        while index < len(lines):
            candidate = lines[index].lstrip("\t") if strips_tabs else lines[index]
            index += 1
            if candidate == terminator:
                break
    return "\n".join(kept)


def reason_for(command: str) -> str | None:
    calls = bare_python_calls(command)
    if not calls:
        return None
    return (
        f"`{calls[0]}` 을(를) 직접 불렀다. 맨 python 은 프로젝트 인터프리터가 아니다 — "
        "스토어 스텁이면 아무것도 하지 않고, pyenv shim 이면 다른 버전이 돈다"
        "(CLAUDE.md 환경 함정). `uv run python` 을 쓴다."
    )


def main() -> int:
    # stdin 은 바이트로. 이유는 .claude/rules/tools.md(대기열 25).
    payload: HookPayload = json.load(sys.stdin.buffer)
    command = payload.get("tool_input", {}).get("command")
    reason = reason_for(command) if command is not None else None
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
