"""`tools/hook_midturn_korean.py` 의 판정을 트랜스크립트의 중간 문장에 돌린다(대기열 94).

대상은 `stop_korean_ratio.py` 와 같다 — 이 저장소와 그 워크트리의 세션 트랜스크립트. 중간 문장은
훅이 보는 것과 같게 고른다. 사이드체인이 아닌 assistant 메시지에서 `tool_use` 블록마다, 같은
메시지의 앞선 `tool_use` 뒤(없으면 메시지 처음)부터 그 블록까지의 텍스트 블록을 이은 것이다. 같은
메시지의 병렬 호출은 둘째부터 앞이 `tool_use` 라 텍스트가 없다. 메시지 id 와 글이 같은 것은 한
번만 센다. Claude Code 가 지어 넣은 기록(모델 `<synthetic>`)과 SDK 세션은 판정하지 않는다.

출력: 판정한 중간 문장의 수, 글자가 적어 판정하지 않은 수, 한글 비율 구간별 개수, 알리는 것의 수와
트랜스크립트별 개수, 알리는 것 중 비율이 가장 높은 열, 알리지 않은 것 중 비율이 가장 낮은 열. 원문은
찍지 않고 비율, 글자 수, 트랜스크립트 이름의 앞 여덟 글자, 메시지 id 만 찍는다(CWE-532,
`stop_korean_ratio.py` 와 같은 이유). 원문은 그 트랜스크립트에서 메시지 id 로 찾는다. 돌리는 법은
저장소 루트에서 `PYTHONUTF8=1 uv run python .scratch/harness/probes/midturn_korean_ratio.py`.
읽기만 한다.
"""

from __future__ import annotations

import io
import sys
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, ValidationError

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from tools.hook_midturn_korean import (  # noqa: E402
    MIN_HANGUL_RATIO,
    MIN_LETTERS,
    letter_counts,
    notice_for,
)

PROJECTS = Path.home() / ".claude" / "projects"
REPO_FOLDER = "C--project-agent"
WORKTREE_FOLDERS = "C--project-agent--claude-worktrees-"
SDK_PREFIX = "sdk-"
NEAREST = 8


class _Block(BaseModel):
    type: str = ""
    text: str = ""


class _Message(BaseModel):
    id: str = ""
    model: str = ""
    content: str | list[_Block] = []


class _Record(BaseModel):
    type: str = ""
    isSidechain: bool = False
    entrypoint: str | None = None
    message: _Message | None = None


@dataclass
class Midturn:
    transcript: str
    message_id: str
    text: str


def transcripts() -> list[Path]:
    """이 저장소와 그 워크트리의 트랜스크립트."""
    return sorted(
        path
        for folder in PROJECTS.iterdir()
        if folder.name == REPO_FOLDER or folder.name.startswith(WORKTREE_FOLDERS)
        for path in folder.glob("*.jsonl")
    )


def _record(line: str) -> _Record | None:
    if not line.lstrip().startswith("{"):
        return None
    try:
        return _Record.model_validate_json(line)
    except ValidationError:
        return None


def midturns(path: Path) -> Iterator[Midturn]:
    """`tool_use` 마다 같은 메시지에서 그 앞의 텍스트. 기록은 블록 하나씩 쓰인다."""
    pending: list[str] = []
    current = ""
    sdk = False
    with path.open(encoding="utf-8", errors="replace") as lines:
        for line in lines:
            record = _record(line)
            if record is None:
                continue
            if record.entrypoint and record.entrypoint.startswith(SDK_PREFIX):
                sdk = True
            message = record.message
            if record.type != "assistant" or record.isSidechain or message is None:
                continue
            if message.model == "<synthetic>" or isinstance(message.content, str):
                continue
            if message.id != current:
                current = message.id
                pending = []
            for block in message.content:
                if block.type == "text" and block.text.strip():
                    pending.append(block.text)
                elif block.type == "tool_use":
                    if pending and not sdk:
                        yield Midturn(path.name, message.id, "\n\n".join(pending))
                    pending = []


def main() -> int:
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")
    paths = transcripts()
    seen: set[tuple[str, str]] = set()
    judged = skipped = 0
    buckets = [0] * 11
    noticed: list[tuple[float, int, Midturn]] = []
    passed: list[tuple[float, int, Midturn]] = []
    for path in paths:
        for midturn in midturns(path):
            key = (midturn.message_id, midturn.text)
            if key in seen:
                continue
            seen.add(key)
            hangul, latin = letter_counts(midturn.text)
            letters = hangul + latin
            if letters < MIN_LETTERS:
                skipped += 1
                continue
            judged += 1
            ratio = hangul / letters
            buckets[int(ratio * 10)] += 1
            target = noticed if notice_for(midturn.text) is not None else passed
            target.append((ratio, letters, midturn))
    print(
        f"트랜스크립트 {len(paths)}개, 문턱 MIN_LETTERS={MIN_LETTERS} "
        f"MIN_HANGUL_RATIO={MIN_HANGUL_RATIO}"
    )
    print(f"판정한 중간 문장 {judged}개, 글자가 적어 판정하지 않은 것 {skipped}개")
    for index, count in enumerate(buckets):
        print(f"  비율 {index / 10:.1f}~ : {count}")
    per_transcript = Counter(m.transcript[:8] for _, _, m in noticed)
    print(f"알리는 것 {len(noticed)}개, 트랜스크립트 {len(per_transcript)}개에 걸쳐")
    for name, count in per_transcript.most_common(NEAREST):
        print(f"  {name} {count}")
    print(f"알리는 것 중 비율이 높은 {NEAREST}개")
    for ratio, letters, midturn in sorted(noticed, key=lambda item: -item[0])[:NEAREST]:
        print(f"  {ratio:.3f} 글자 {letters} {midturn.transcript[:8]} {midturn.message_id}")
    print(f"알리지 않은 것 중 비율이 낮은 {NEAREST}개")
    for ratio, letters, midturn in sorted(passed, key=lambda item: item[0])[:NEAREST]:
        print(f"  {ratio:.3f} 글자 {letters} {midturn.transcript[:8]} {midturn.message_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
