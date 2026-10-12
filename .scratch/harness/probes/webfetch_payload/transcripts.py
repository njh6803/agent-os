"""이 저장소의 트랜스크립트에 남은 WebFetch 결과를 `tools/hook_webfetch_summary.py` 의 세 갈래로
센다.

대상은 `~/.claude/projects/` 아래 `C--project-agent` 와 `C--project-agent--claude-worktrees-*`
폴더다(서브에이전트 기록 포함, 이름이 같은 머리로 시작하는 이웃 저장소 폴더는 뺀다,
`stop_korean_ratio.py` 와 같다). WebFetch 호출의 `tool_use_id` 마다 그 결과 기록의 `toolUseResult`
를 한 번만 센다(갈라진 트랜스크립트가 같은 결과를 담는다). 결과 객체가 없는 기록과 오류로 끝난
호출은 따로 센다.

갈래는 훅의 `context_for` 로 가른다. 판정을 여기서 다시 짓지 않는다 — 훅이 바뀌면 독스트링이
근거로 드는 수도 따라 바뀌어야 한다. 침묵한 것은 code 가 2xx 밖이면 그 code, 아니면 본문 통과다.
알린 것은 수를 든 문장이면 요약, 수 없는 문장이면 모양이 다른 결과 객체다. 통과와 요약은 한 줄씩
비율(결과 글자 수 / bytes), 글자 수, UTF-8 바이트 수, bytes, 주소로 찍는다. 결과의 내용은 찍지
않는다. 결과 객체가 있는 기록이 하나도 없으면 측정이 아니라 1로 끝난다. 읽기만 한다.
돌리는 법: 저장소 루트에서 `PYTHONUTF8=1 uv run python
.scratch/harness/probes/webfetch_payload/transcripts.py`.
"""

from __future__ import annotations

import io
import json
import sys
from collections import Counter
from collections.abc import Iterator
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from tools.hook_webfetch_summary import LEAD, TOOL, context_for  # noqa: E402

PROJECTS = Path.home() / ".claude" / "projects"
REPO_FOLDER = "C--project-agent"
WORKTREE_FOLDERS = "C--project-agent--claude-worktrees-"


def transcripts() -> Iterator[Path]:
    for folder in sorted(PROJECTS.iterdir()):
        if folder.name == REPO_FOLDER or folder.name.startswith(WORKTREE_FOLDERS):
            yield from sorted(folder.rglob("*.jsonl"))


def records(path: Path) -> Iterator[dict[str, object]]:
    with path.open(encoding="utf-8", errors="replace") as stream:
        for line in stream:
            if "WebFetch" not in line and "tool_result" not in line:
                continue
            try:
                record = json.loads(line)
            except ValueError:
                continue
            if isinstance(record, dict):
                yield {str(key): value for key, value in record.items()}


def blocks(record: dict[str, object]) -> list[dict[str, object]]:
    message = record.get("message")
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, list):
        return []
    return [
        {str(key): value for key, value in block.items()}
        for block in content
        if isinstance(block, dict)
    ]


def kind_of(fields: dict[str, object]) -> str:
    """훅의 판정(`context_for`)으로 가른 갈래. 침묵이면 code 로 2xx 밖과 통과를 가른다."""
    context = context_for({"tool_name": TOOL, "tool_response": fields})
    code = fields.get("code")
    if context is None:
        return f"code {code}" if isinstance(code, int) and not 200 <= code < 300 else "통과"
    return "요약" if context.startswith(LEAD) and "바이트를" in context else "모양이 다른 결과 객체"


def main() -> int:
    stream = sys.stdout
    if isinstance(stream, io.TextIOWrapper):
        stream.reconfigure(encoding="utf-8")
    calls: set[str] = set()
    seen: set[str] = set()
    tally: Counter[str] = Counter()
    rows: list[tuple[str, float, int, int, int, str]] = []
    for path in transcripts():
        for record in records(path):
            for block in blocks(record):
                if block.get("type") == "tool_use" and block.get("name") == "WebFetch":
                    calls.add(str(block.get("id")))
                    continue
                tool_use_id = str(block.get("tool_use_id"))
                if block.get("type") != "tool_result" or tool_use_id not in calls:
                    continue
                if tool_use_id in seen:
                    continue
                seen.add(tool_use_id)
                result = record.get("toolUseResult")
                if block.get("is_error"):
                    tally["오류로 끝난 호출"] += 1
                    continue
                if not isinstance(result, dict):
                    tally["결과 객체 없음"] += 1
                    continue
                fields = {str(key): value for key, value in result.items()}
                kind = kind_of(fields)
                tally[kind] += 1
                code, size, text = fields.get("code"), fields.get("bytes"), fields.get("result")
                if kind not in ("통과", "요약"):
                    continue
                if not isinstance(code, int) or not isinstance(size, int):
                    continue
                if not isinstance(text, str):
                    continue
                encoded = len(text.encode("utf-8"))
                ratio = round(len(text) / max(size, 1), 3)
                rows.append((kind, ratio, len(text), encoded, size, str(fields.get("url"))))
    for kind, ratio, chars, encoded, size, url in sorted(rows, key=lambda row: (row[0], -row[1])):
        print(f"{kind} 비율 {ratio} 결과 {chars}자 {encoded}바이트 bytes {size} {url}")
    print(f"WebFetch 호출 {len(calls)}건, 결과 기록 {len(seen)}건: {dict(sorted(tally.items()))}")
    measured = sum(count for kind, count in tally.items() if kind in ("통과", "요약"))
    if not measured:
        print("[문제] 측정 아님 — 결과 객체가 있는 2xx 기록이 없다")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
