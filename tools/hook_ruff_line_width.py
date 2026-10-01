"""PostToolUse 훅(Write|Edit). 파이썬 파일을 쓴 직후 E501 로 넘친 줄을 컨텍스트에 넣는다.

ruff 는 줄 길이를 폭으로 재고 한글은 폭 2다. 줄 길이 100에 한글이면 45~50자라, 글자 수로 가늠하면
넘긴 줄을 모른 채 쓴다. 이 사실은 `docs/constitution/operations.md` 에 2026-09-20 부터 있었다("한글
한 글자가 2로 세어진다"). 그런데도 대기열 53 이 일지 2026-09-28-08(그 세션만 열 번 남짓)에서 생겨
2026-09-29-02, 2026-09-30-07, 2026-10-01-01 에 회차가 더해졌다. 대개 커밋 직전 `ruff check` 나
리뷰에서야 알았고, 한 번에 다시 감은 줄이 많게는 스물셋이었다. 한꺼번에 감으려 지은 스크래치 감기
도우미는 줄 하나로 선 `사용:` 줄을 다음 문장에 붙이고 코드 스팬을 줄에서 갈랐다(일지 2026-10-01-01).
지침이 어겨졌으니 훅이다(CLAUDE.md 교정 루프). 판정을 편집 순간으로 당기면 다시 감을 줄은 방금 쓴
몇 줄이라 감기 도구가 필요 없다. 막지 않는 계기 훅이다 — 막는 것은 커밋 전 게이트가 이미 한다.

발동 조건은 셋이다. 도구가 Write 나 Edit, 파일이 `.py`·`.pyi`, 파일의 조상에 ruff 설정(`ruff.toml`,
`.ruff.toml`, `tool.ruff` 표가 있는 `pyproject.toml`)이 있을 것. 셋째는 게이트가 보는 파일만 보려는
것이다 — ruff 는 조상에 설정이 없으면 실행 위치의 설정으로 떨어져(2026-10-01 실측), 스크래치
스크립트에 저장소의 줄 길이를 들이댄다.

ruff 는 설정을 그대로 따르게 부른다. `--select` 를 주면 설정의 `select`·`ignore` 를
덮고, `--force-exclude` 가 없으면 이름으로 넘긴 파일에 `exclude` 가 듣지 않는다(셀프
리뷰가 잡았다). 그래서 설정이 고른 규칙이 다 오고, 그중 E501 만 남긴다. import 를 먼저
쓰고 쓰는 자리를 다음 Edit 로 붙이는 동안의 F401 처럼 편집 순서가 잠깐 만드는 위반을
편집마다 울리면, 세션이 이 계기를 무시하는 법을 배운다(hook_journal_retro 의 교훈). 줄
길이는 그 줄 하나의 성질이라 순서와 무관하다. ruff 는 이 훅을 돌리는 파이썬의 `-m ruff`
로 부른다 — 훅은 표준 라이브러리만 import 한다(.claude/rules/tools.md). 캐시를 쓰지
않는다(`--no-cache`, 쓰면 `.ruff_cache` 가 생긴다). 비용은 .claude/rules/tools.md 의
실측 줄에 있다.

못 보는 것: `ruff format` 이 감을 코드 줄과 문자열·주석의 줄을 가르지 않는다(둘 다 알린다 — 코드
줄은 커밋 전 format 이 감는다). `# noqa: E501` 은 ruff 가 지나친다. `[tool]` 아래 점 키
(`ruff.line-length = 100`)로만 쓴 설정은 설정으로 보지 않아 침묵한다. ruff 가 돌지 못하면(설치되지
않았다, 시간 제한, 설정이 깨졌다) 아무것도 알리지 않는다 — 계기 훅이라 조용히 지나가고, 판정은 커밋
전 게이트에 남는다. Bash 나 다른 도구로 쓴 파일(`sed -i`, heredoc)은 Write·Edit 가 아니라 보지
않는다.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import TypedDict

PYTHON_SUFFIXES = frozenset({".py", ".pyi"})
RUFF_CONFIG_FILES = (".ruff.toml", "ruff.toml")
# `[tool.ruff]` 와 `[tool.ruff.lint]` 같은 하위 표. ruff 는 이 표가 없는 pyproject.toml 을 지나친다.
RUFF_TABLE = re.compile(r"^\s*\[tool\.ruff[\].]", re.MULTILINE)
# ruff 의 E501 메시지 "Line too long (102 > 100)" 의 괄호 안.
WIDTH = re.compile(r"\((\d+ > \d+)\)")
SHOWN = 10
# 훅 등록의 timeout(20초) 안에 이 프로세스가 스스로 끝나도록.
RUFF_TIMEOUT = 10


class ToolInput(TypedDict, total=False):
    file_path: str


class HookPayload(TypedDict, total=False):
    """Claude Code 가 stdin 으로 주는 훅 입력 중 이 훅이 읽는 부분."""

    tool_name: str
    tool_input: ToolInput


class _Location(TypedDict):
    row: int


class _Diagnostic(TypedDict):
    """`ruff check --output-format json` 의 진단 하나 중 이 훅이 읽는 부분."""

    code: str | None
    message: str
    location: _Location


def ruff_governs(path: Path) -> bool:
    """`path` 의 조상에 ruff 설정이 있는가. 없으면 게이트가 보지 않는 파일이다."""
    for directory in path.parents:
        if any((directory / name).is_file() for name in RUFF_CONFIG_FILES):
            return True
        pyproject = directory / "pyproject.toml"
        if pyproject.is_file() and RUFF_TABLE.search(
            pyproject.read_text(encoding="utf-8", errors="replace")
        ):
            return True
    return False


def long_lines(path: Path) -> list[tuple[int, str]]:
    """ruff E501 이 잡은 줄의 (행, 폭). 폭은 "102 > 100" 꼴이고, 메시지가 그 꼴이 아니면 메시지
    그대로다. ruff 가 돌지 못하면 빈 목록이다(fail-open)."""
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "ruff",
                "check",
                "--no-cache",
                "--force-exclude",
                "--output-format",
                "json",
                str(path),
            ],
            capture_output=True,
            check=False,
            timeout=RUFF_TIMEOUT,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    try:
        # 설정이 깨지면 ruff 는 종료 2에 stdout 이 비어 여기서 걸린다(2026-10-01 실측).
        diagnostics: list[_Diagnostic] = json.loads(result.stdout.decode("utf-8", "replace"))
    except json.JSONDecodeError:
        return []
    lines: list[tuple[int, str]] = []
    for diagnostic in diagnostics:
        # 설정이 고른 다른 규칙과 문법 오류(`invalid-syntax`)는 편집 중간의 상태일 수 있다.
        if diagnostic["code"] != "E501":
            continue
        width = WIDTH.search(diagnostic["message"])
        lines.append(
            (diagnostic["location"]["row"], width.group(1) if width else diagnostic["message"])
        )
    return lines


def summary(file_path: str, lines: list[tuple[int, str]]) -> str:
    """넘친 줄들을 컨텍스트 문장으로. 앞의 `SHOWN` 줄만 적고 나머지는 센다."""
    shown = ", ".join(f"{row}행 {width}" for row, width in lines[:SHOWN])
    rest = f" 외 {len(lines) - SHOWN}줄" if len(lines) > SHOWN else ""
    return (
        f"`{file_path}` 에 ruff E501(줄 길이)이 {len(lines)}줄 있다: {shown}{rest}. "
        "ruff 는 한글을 폭 2로 센다(글자 수로 가늠하면 넘긴다). 커밋 전 `ruff check` 가 막으니 "
        "넘친 줄을 지금 다시 감는다."
    )


def context_for(tool_name: str, file_path: str) -> str | None:
    """Write·Edit 가 ruff 설정 아래의 파이썬 파일에 넘친 줄을 남겼으면 컨텍스트 문장, 아니면
    None."""
    path = Path(file_path)
    if tool_name not in ("Write", "Edit"):
        return None
    # 판정이 아니라 비용이다. ruff 는 `.md` 를 넘겨도 "No Python files found" 로 지나치지만
    # (2026-10-01 실측), 일지·문서의 Write·Edit 마다 ruff 를 띄우지 않는다.
    if path.suffix not in PYTHON_SUFFIXES:
        return None
    if not ruff_governs(path):
        return None
    lines = long_lines(path)
    return summary(file_path, lines) if lines else None


def main() -> int:
    # stdin 은 바이트로. 이유는 .claude/rules/tools.md(대기열 25).
    payload: HookPayload = json.load(sys.stdin.buffer)
    file_path = payload.get("tool_input", {}).get("file_path")
    if file_path is None:
        return 0
    context = context_for(payload.get("tool_name", ""), file_path)
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
