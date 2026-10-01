"""`tools/hook_stop_korean.py` 의 문턱을 실제 트랜스크립트로 잰다.

대상은 이 저장소의 세션 트랜스크립트다 — `~/.claude/projects/` 아래 `C--project-agent` 와
`C--project-agent--claude-worktrees-*` 폴더(이름이 같은 머리로 시작하는 이웃 저장소 폴더는 뺀다).
Stop 훅이 받는 답만 센다. `stop_reason` 이 `end_turn` 인 assistant 메시지의 마지막 텍스트 블록이
`last_assistant_message` 다(`stop_payload/` 탐침). 도구 호출로 이어지는 텍스트(스킬 본문 같은
메타 기록 앞의 것 포함)는 세지 않는다. 메시지 id 가 같은 답은 한 번만 센다(갈라진 트랜스크립트가
같은 답을 담는다). 사이드체인, Claude Code 가 지어 넣은 기록(모델 `<synthetic>`), SDK
세션(트랜스크립트의 `entrypoint` 가 `sdk-` 로 시작)은 판정하지 않는다. SDK 세션의 답은 수만 센다.

고친 표지: 사람이 보낸 120자 미만의 프롬프트(메타가 아닌 user 기록, 또는 작업 중에 보낸
`queued_command`)가 "한국어로"를 담으면, 그 앞의 가장 가까운 답에 표지를 붙인다.

출력: SDK 세션의 수와 그 텍스트 블록 중 지금 판정이 막을 것의 수, 판정한 답의 수, 글자가 적어
판정하지 않은 답의 수, 한글 비율 구간별 개수, 막는 답 전부, 판정하지 않은 답 중 한글이 없는 것,
표지가 붙은 답 전부. 답은 비율과 트랜스크립트 이름의 앞 여덟 글자, 메시지 id 로만 찍고 원문은 찍지
않는다 — 답에 키나 토큰이 있으면 이 출력이 도구 출력과 트레이스로 복제된다(PR #118 CodeRabbit,
CWE-532). 원문은 그 트랜스크립트에서 메시지 id 로 찾는다. 돌리는 법은 저장소 루트에서
`PYTHONUTF8=1 uv run python .scratch/harness/probes/stop_korean_ratio.py [--near 0.5]`. `--near` 는
그 비율 아래인데 막지 않은 답도 찍는다. 읽기만 한다.
"""

from __future__ import annotations

import argparse
import io
import sys
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, ValidationError

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from tools.hook_stop_korean import (  # noqa: E402
    MIN_HANGUL_RATIO,
    MIN_LETTERS,
    block_reason_for,
    is_program_session,
    letter_counts,
)

PROJECTS = Path.home() / ".claude" / "projects"
REPO_FOLDER = "C--project-agent"
WORKTREE_FOLDERS = "C--project-agent--claude-worktrees-"
CORRECTION = "한국어로"
MAX_PROMPT = 120


class _Block(BaseModel):
    type: str = ""
    text: str = ""


class _Message(BaseModel):
    id: str = ""
    model: str = ""
    stop_reason: str | None = None
    content: str | list[_Block] = []


class _Attachment(BaseModel):
    type: str = ""
    prompt: str = ""


class _Record(BaseModel):
    type: str = ""
    isSidechain: bool = False
    isMeta: bool = False
    entrypoint: str | None = None
    message: _Message | None = None
    attachment: _Attachment | None = None


@dataclass
class Answer:
    transcript: str
    message_id: str
    text: str
    corrected: bool = False


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


def _texts(message: _Message) -> list[str]:
    content = message.content
    if isinstance(content, str):
        return [content] if content.strip() else []
    return [block.text for block in content if block.type == "text" and block.text.strip()]


def _human_prompt(record: _Record) -> str | None:
    """사람이 보낸 프롬프트. 메타 기록과 도구 결과는 아니다."""
    if record.type == "attachment" and record.attachment is not None:
        if record.attachment.type == "queued_command":
            return record.attachment.prompt
        return None
    if record.type != "user" or record.isMeta or record.message is None:
        return None
    texts = _texts(record.message)
    return "\n".join(texts) if texts else None


def entrypoint_of(path: Path) -> str | None:
    """트랜스크립트에서 처음 보이는 `entrypoint`."""
    with path.open(encoding="utf-8", errors="replace") as lines:
        for line in lines:
            record = _record(line)
            if record is not None and record.entrypoint:
                return record.entrypoint
    return None


def sdk_texts(path: Path) -> Iterator[tuple[str, str]]:
    """SDK 세션의 assistant 텍스트 블록 전부(메시지 id, 텍스트). 그 세션은 `end_turn` 답이 없다."""
    with path.open(encoding="utf-8", errors="replace") as lines:
        for line in lines:
            record = _record(line)
            if record is None or record.isSidechain or record.type != "assistant":
                continue
            if record.message is not None:
                for text in _texts(record.message):
                    yield record.message.id, text


def answers(path: Path) -> Iterator[Answer]:
    """`end_turn` 메시지마다 마지막 텍스트 블록. 고친 표지는 다음 사람 프롬프트가 붙인다."""
    found: list[Answer] = []
    with path.open(encoding="utf-8", errors="replace") as lines:
        for line in lines:
            record = _record(line)
            if record is None or record.isSidechain:
                continue
            message = record.message
            if record.type == "assistant" and message is not None:
                texts = _texts(message)
                if not texts or message.stop_reason != "end_turn":
                    continue
                if message.model == "<synthetic>":
                    continue
                if found and found[-1].message_id == message.id:
                    found[-1].text = texts[-1]
                else:
                    found.append(Answer(path.name, message.id, texts[-1]))
                continue
            prompt = _human_prompt(record)
            if prompt and len(prompt) < MAX_PROMPT and CORRECTION in prompt and found:
                found[-1].corrected = True
    yield from found


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--near", type=float, default=0.0)
    args = parser.parse_args()
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")
    paths = transcripts()
    seen: set[str] = set()
    sdk_seen: set[tuple[str, str]] = set()
    judged = program = sdk_sessions = sdk_blocked = 0
    buckets = [0] * 11
    blocked: list[tuple[float, Answer]] = []
    near: list[tuple[float, Answer]] = []
    corrected: list[tuple[float, Answer]] = []
    skipped: list[tuple[int, int, Answer]] = []
    for path in paths:
        sdk = is_program_session(entrypoint_of(path))
        if sdk:
            sdk_sessions += 1
            for key in sdk_texts(path):
                if key in sdk_seen:
                    continue
                sdk_seen.add(key)
                if block_reason_for(key[1]) is not None:
                    sdk_blocked += 1
        for answer in answers(path):
            if answer.message_id in seen:
                continue
            seen.add(answer.message_id)
            if sdk:
                program += 1
                continue
            hangul, latin = letter_counts(answer.text)
            letters = hangul + latin
            ratio = hangul / letters if letters else 0.0
            if answer.corrected:
                corrected.append((ratio, answer))
            if letters < MIN_LETTERS:
                skipped.append((hangul, latin, answer))
                continue
            judged += 1
            buckets[int(ratio * 10)] += 1
            if block_reason_for(answer.text) is not None:
                blocked.append((ratio, answer))
            elif ratio < args.near:
                near.append((ratio, answer))
    print(
        f"트랜스크립트 {len(paths)}개, 문턱 MIN_LETTERS={MIN_LETTERS} "
        f"MIN_HANGUL_RATIO={MIN_HANGUL_RATIO}"
    )
    print(
        f"SDK 세션 트랜스크립트 {sdk_sessions}개: end_turn 답 {program}개(판정하지 않았다), "
        f"텍스트 블록 {len(sdk_seen)}개 중 지금 판정이 막을 것 {sdk_blocked}개"
    )
    print(f"판정한 답 {judged}개, 글자가 적어 판정하지 않은 답 {len(skipped)}개")
    for index, count in enumerate(buckets):
        print(f"  비율 {index / 10:.1f}~ : {count}")
    print(f"막는 답 {len(blocked)}개")
    for ratio, answer in sorted(blocked, key=lambda item: item[0]):
        mark = "고침" if answer.corrected else "    "
        print(f"  [{mark}] {ratio:.3f} {answer.transcript[:8]} {answer.message_id}")
    unseen = [item for item in skipped if item[0] == 0 and item[1] > 0]
    print(f"판정하지 않은 답 중 한글이 없는 것 {len(unseen)}개")
    for _, latin, answer in unseen:
        print(f"  라틴 {latin} {answer.transcript[:8]} {answer.message_id}")
    if args.near:
        print(f"막지 않았지만 비율 {args.near} 아래인 답 {len(near)}개")
        for ratio, answer in sorted(near, key=lambda item: item[0]):
            print(f"  {ratio:.3f} {answer.transcript[:8]} {answer.message_id}")
    print(f"고친 표지(다음 사람 프롬프트가 '{CORRECTION}') {len(corrected)}개")
    for ratio, answer in corrected:
        verdict = "막는다" if block_reason_for(answer.text) is not None else "지나간다"
        print(f"  {ratio:.3f} {verdict} {answer.transcript[:8]} {answer.message_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
