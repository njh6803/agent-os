"""GitHub Actions 실행 로그 요약. 초록 체크가 실제로 무엇을 했는지 한 번에 본다.

`gh run view <run-id> --log`의 출력에서 판정에 필요한 줄만 뽑는다. 네 갈래이고 무엇을
잡는지는 아래 상수가 원천이다.

- 결과 블록(`RESULT_KEYS`)과 허용 도구 밖 호출 횟수(`DENIED`)
- 경고·건너뜀·코멘트 게시 흔적(`SIGNAL_PATTERNS`)
- Claude의 말(`TEXT_PATTERN`. 워크플로에 `show_full_output: true`가 켜져 있을 때만 있다)

쓰임: `uv run python tools/gh_run_summary.py 35505690924`. 리뷰 파이프라인의 "코멘트 없는 초록"이
리뷰를 했는지 안 했는지는 이 요약으로 판정한다(`docs/constitution/operations.md`).
"""

from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass, field

RESULT_KEYS = ("num_turns", "total_cost_usd", "permission_denials_count")
DENIED = '"subtype": "permission_denied"'
DENIED_TOOL = re.compile(r'"tool_name": "([^"]+)"')
SIGNAL_PATTERNS = (
    re.compile(r"::warning|::error"),
    re.compile(r"Skipping|Trigger result|workflow validation", re.IGNORECASE),
    re.compile(r"buffered inline comments|posted comment|create_comment", re.IGNORECASE),
)
TEXT_PATTERN = re.compile(r'"text": "(.*)')
PREFIX = re.compile(r"^[^\t]*\t[^\t]*\t\S*\s?")  # "<job>\t<step>\t<timestamp> " 접두
TEXT_LIMIT = 12
TEXT_WIDTH = 200


@dataclass
class Summary:
    results: list[str] = field(default_factory=list[str])
    signals: list[str] = field(default_factory=list[str])
    texts: list[str] = field(default_factory=list[str])
    denied: int = 0
    denied_tools: dict[str, int] = field(default_factory=dict[str, int])


def strip_prefix(line: str) -> str:
    return PREFIX.sub("", line, count=1).rstrip()


def summarize(lines: list[str]) -> Summary:
    summary = Summary()
    awaiting_tool_name = False
    for raw in lines:
        line = strip_prefix(raw)
        if DENIED in line:
            summary.denied += 1
            awaiting_tool_name = True
            continue
        tool_match = DENIED_TOOL.search(line) if awaiting_tool_name else None
        if tool_match:
            name = tool_match.group(1)
            summary.denied_tools[name] = summary.denied_tools.get(name, 0) + 1
            awaiting_tool_name = False
            continue
        if any(f'"{key}"' in line for key in RESULT_KEYS):
            summary.results.append(line.strip().rstrip(","))
            continue
        text_match = TEXT_PATTERN.search(line)
        if text_match:
            summary.texts.append(text_match.group(1)[:TEXT_WIDTH])
            continue
        if any(pattern.search(line) for pattern in SIGNAL_PATTERNS):
            summary.signals.append(line.strip())
    return summary


def render(summary: Summary) -> str:
    out: list[str] = []
    out.append("## 결과")
    out.extend(summary.results or ["(결과 블록 없음. 실행이 Claude 단계 전에 끝났다)"])
    if summary.denied:
        tools = ", ".join(f"{name} {count}" for name, count in summary.denied_tools.items())
        out.append(f"permission_denied 이벤트 {summary.denied}건 (허용 도구 밖의 호출: {tools})")
    out.append("## 경고·건너뜀·코멘트 흔적")
    out.extend(summary.signals or ["(없음)"])
    out.append(f"## Claude의 말 (처음 {TEXT_LIMIT}줄)")
    if summary.texts:
        out.extend(summary.texts[:TEXT_LIMIT])
        if len(summary.texts) > TEXT_LIMIT:
            out.append(f"... 외 {len(summary.texts) - TEXT_LIMIT}줄")
    else:
        out.append("(없음. show_full_output이 꺼져 있거나 Claude 단계가 돌지 않았다)")
    return "\n".join(out)


def fetch_log(run_id: str) -> list[str]:
    """`gh`가 실패하면 CalledProcessError를 올린다. 실패의 형태는 예외 하나다."""
    completed = subprocess.run(
        ["gh", "run", "view", run_id, "--log"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=True,
    )
    return completed.stdout.splitlines()


def main(argv: list[str]) -> int:
    if len(argv) != 2 or not argv[1].isdigit():
        sys.stderr.write("쓰임: uv run python tools/gh_run_summary.py <run-id>\n")
        return 2
    try:
        lines = fetch_log(argv[1])
    except subprocess.CalledProcessError as error:
        sys.stderr.write(str(error.stderr))
        return error.returncode
    print(render(summarize(lines)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
