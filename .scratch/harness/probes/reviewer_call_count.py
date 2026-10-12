"""`bug-perf-review` 서브에이전트가 실제로 부른 도구 수와 스스로 센 수를 견준다(대기열 169·198).

대상은 이 저장소의 세션 트랜스크립트 폴더(`~/.claude/projects/` 아래 `C--project-agent` 와
`C--project-agent--claude-worktrees-*`)의 서브에이전트 기록이다. `subagents/agent-*.meta.json` 의
`agentType` 이 `bug-perf-review` 인 것의 짝 `.jsonl` 을 읽는다. 워크트리 세션의 기록은 두 폴더에
함께 남기도 해서 같은 에이전트 id 는 사건이 가장 많은 사본 하나만 센다.

기록마다 찍는 것.
- 호출: assistant 사건의 `tool_use` 블록 수. 보고를 넘기는 `SubagentHandback` 은 세지 않는다.
- 응답: 그 호출을 담은 assistant 메시지 id 의 수. 한 응답에서 도구를 여럿 나란히 부르면 호출이
  응답보다 많다. 호출이 많은 다섯 기록이 정확히 60응답(정의의 `maxTurns: 60`)에서 멈춰 `maxTurns`
  가 이 단위를 센다고 본다. 멈춘 까닭은 기록에 없어 어림이다.
- 표지: 응답의 텍스트에 적은 `[호출 n]`(정의의 보고 형식 절, 대기열 198). 표지를 단 응답 수,
  증분 어긋남(직전 응답의 표지에서 늘어난 수가 그 응답의 호출 수와 다른 응답 수. 한 번 틀린 셈이
  뒤로 이어져도 한 번만 센다. 직전 응답에 표지가 없으면 그 응답은 보지 않는다), 표지가 있는 마지막
  응답의 n 과 그 응답까지의 실제 누적 수.
- 보고 n: 보고에 적은 첫 `[호출 n]` 의 n(정의가 보고 첫 줄에 적게 한다). 실제 호출 수와 견준다.
- 자기 셈: 보고에서 "도구 호출" 이나 "호출" 뒤에 수가 든 첫 문장. 표지 전의 옛 보고를 읽으려는
  것이다. 80자에서 자른다. 보고 원문 전체는 찍지 않는다. 수를 적지 않은 보고는 빈칸이다.

보고는 `SubagentHandback` 의 메시지다. 그 호출이 없는 기록(2026-10-07 의 옛 회차, 다른 프로브가
`claude -p` 로 띄운 회차)은 마지막 텍스트가 보고라, 표지가 하나도 없는 기록만 마지막 텍스트로
대신한다. 표지가 있는 기록은 응답마다 텍스트가 있어, 대신하면 아직 돌고 있는 리뷰도 보고가 있는
것으로 센다.

측정의 표지는 호출이 하나 이상이고 보고가 있는 것이다. 호출이 0 인 기록(도구를 쓰지 말라고 한
카나리아 질문)은 리뷰가 아니라 세지 않고 수만 찍는다. 호출은 있는데 보고가 없는 기록(아직 돌고
있거나 보고 전에 끊겼다)은 측정이 아니라고 따로 찍는다. 그런 기록이 하나라도 있거나 측정이 하나도
없으면(창이 비었다, 저장소 폴더 이름이 다르다) 1 로 끝난다. 실제 리뷰가 아닌 측정(다른 프로브가
띄운 회차)도 찍힌다. 시각과 브랜치로 가른다.

못 보는 것.
- 그 회차에 어느 판의 정의가 실렸는지. 기록에는 서브에이전트의 지시문이 없다. 표지가 없는 회차는
  옛 정의가 실린 것과 새 정의를 따르지 않은 것을 가르지 못한다. 정의를 바꾼 커밋이 main 에 병합된
  시각을 `--since` 로 주고 브랜치를 본다. 그 뒤에도 병합 전에 딴 워크트리에서는 옛 정의가 돈다.
- 트랜스크립트가 지워진 회차. 수는 이 PC 에 남은 기록만이다.

돌리는 법은 저장소 루트에서 아래 명령이다. `--since`·`--until` 은 첫 사건의 UTC 시각이 그 값
이상인, 그 값 미만인 기록만 고른다(문자열 비교). 기록은 계속 쌓이므로 근거로 적는 수는 두 값을
함께 준 결과다. 읽기만 한다.

    PYTHONUTF8=1 uv run python .scratch/harness/probes/reviewer_call_count.py
        [--since <시각>] [--until <시각>]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

PROJECTS = Path.home() / ".claude" / "projects"
REPO_FOLDER = "C--project-agent"
WORKTREE_FOLDERS = "C--project-agent--claude-worktrees-"
AGENT_TYPE = "bug-perf-review"
HANDBACK = "SubagentHandback"
MARKER = re.compile(r"\[호출 (\d+)\]")
SELF_COUNT = re.compile(r"[^\n.]*(?:도구 호출|호출 ?\d)[^\n.]*")
SELF_COUNT_WIDTH = 80


@dataclass
class Record:
    agent_id: str
    events: int
    started: str
    branch: str
    calls: int
    responses: int
    marked: int
    step_mismatched: int
    last_marker: int | None
    last_marker_actual: int | None
    report_n: int | None
    report: str


def record_folders() -> list[Path]:
    return [
        p
        for p in sorted(PROJECTS.iterdir())
        if p.is_dir() and (p.name == REPO_FOLDER or p.name.startswith(WORKTREE_FOLDERS))
    ]


def is_reviewer(meta_path: Path) -> bool:
    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return isinstance(meta, dict) and meta.get("agentType") == AGENT_TYPE


def message_id_and_blocks(event: dict[str, object]) -> tuple[str, list[dict[str, object]]]:
    message = event.get("message")
    if not isinstance(message, dict):
        return "", []
    content = message.get("content")
    if not isinstance(content, list):
        return "", []
    message_id = message.get("id")
    blocks = [b for b in content if isinstance(b, dict)]
    return (message_id if isinstance(message_id, str) else ""), blocks


def read_record(path: Path) -> Record:
    events = 0
    started = branch = report = last_text = ""
    calls = 0
    response_ids: list[str] = []
    texts: dict[str, list[str]] = {}
    calls_at: dict[str, int] = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(event, dict):
                continue
            events += 1
            timestamp = event.get("timestamp")
            if not started and isinstance(timestamp, str):
                started = timestamp
            git_branch = event.get("gitBranch")
            if not branch and isinstance(git_branch, str):
                branch = git_branch
            if event.get("type") != "assistant":
                continue
            message_id, blocks = message_id_and_blocks(event)
            for block in blocks:
                kind = block.get("type")
                if kind == "text":
                    text = block.get("text")
                    if isinstance(text, str):
                        texts.setdefault(message_id, []).append(text)
                        last_text = text
                elif kind == "tool_use":
                    tool_input = block.get("input")
                    if block.get("name") == HANDBACK:
                        if isinstance(tool_input, dict):
                            message = tool_input.get("message")
                            if isinstance(message, str):
                                report = message
                        continue
                    calls += 1
                    if message_id not in response_ids:
                        response_ids.append(message_id)
                    calls_at[message_id] = calls
    marked = step_mismatched = 0
    last_marker: int | None = None
    last_marker_actual: int | None = None
    previous_marker: int | None = 0
    previous_calls = 0
    for message_id in response_ids:
        found = [int(m) for t in texts.get(message_id, []) for m in MARKER.findall(t)]
        actual = calls_at[message_id]
        if found:
            marked += 1
            marker = found[-1]
            if previous_marker is not None and marker - previous_marker != actual - previous_calls:
                step_mismatched += 1
            last_marker, last_marker_actual = marker, actual
            previous_marker = marker
        else:
            previous_marker = None
        previous_calls = actual
    report = report or ("" if marked else last_text)
    report_markers = MARKER.findall(report)
    return Record(
        agent_id=path.stem,
        events=events,
        started=started,
        branch=branch,
        calls=calls,
        responses=len(response_ids),
        marked=marked,
        step_mismatched=step_mismatched,
        last_marker=last_marker,
        last_marker_actual=last_marker_actual,
        report_n=int(report_markers[0]) if report_markers else None,
        report=report,
    )


def self_count(report: str) -> str:
    match = SELF_COUNT.search(report)
    if match is None:
        return ""
    return " ".join(match.group(0).split())[:SELF_COUNT_WIDTH]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--since", default="", help="첫 사건의 UTC 시각 하한(ISO 문자열)")
    parser.add_argument("--until", default="~", help="첫 사건의 UTC 시각 상한, 그 값은 빼고")
    args = parser.parse_args()
    since: str = args.since
    until: str = args.until

    chosen: dict[str, Record] = {}
    for folder in record_folders():
        for meta_path in sorted(folder.glob("*/subagents/agent-*.meta.json")):
            jsonl = meta_path.with_name(meta_path.name.removesuffix(".meta.json") + ".jsonl")
            if not jsonl.is_file() or not is_reviewer(meta_path):
                continue
            record = read_record(jsonl)
            kept = chosen.get(record.agent_id)
            if kept is None or record.events > kept.events:
                chosen[record.agent_id] = record

    records = sorted(
        (r for r in chosen.values() if since <= r.started < until), key=lambda r: r.started
    )
    no_tools = [r for r in records if r.calls == 0]
    no_report = [r for r in records if r.calls > 0 and not r.report.strip()]
    measured = [r for r in records if r.calls > 0 and r.report.strip()]

    for r in measured:
        marker = (
            "표지 없음"
            if r.marked == 0
            else f"표지 {r.marked}(증분 어긋남 {r.step_mismatched},"
            f" 마지막 {r.last_marker}/실제 {r.last_marker_actual})"
        )
        report_n = "" if r.report_n is None else f" 보고 n {r.report_n}"
        print(
            f"{r.started[:16]} {r.branch} 호출 {r.calls} 응답 {r.responses} {marker}{report_n}"
            f' 자기 셈 "{self_count(r.report)}"'
        )
    print(f"측정 {len(measured)}, 도구 0회라 세지 않음 {len(no_tools)}, 보고 없음 {len(no_report)}")
    for r in no_report:
        print(
            f"보고 없음(측정 아님, 돌고 있거나 끊겼다): {r.started[:16]} {r.branch}"
            f" {r.agent_id} 호출 {r.calls}"
        )
    if not measured:
        print("측정이 하나도 없다. 창이나 저장소 폴더 이름(REPO_FOLDER)을 본다")
    return 1 if no_report or not measured else 0


if __name__ == "__main__":
    sys.exit(main())
