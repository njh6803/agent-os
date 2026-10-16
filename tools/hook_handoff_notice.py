"""Stop 훅. 세션 컨텍스트가 인계 문턱을 넘은 채 턴이 끝나면 사람에게 한 번 알린다. 막지 않는다.

`hook_handoff`(PostToolUse)는 단계 경계에서 모델에게 인계를 지시한다. 그 경계 전에 사람이 지금
세션이 곧 넘어간다는 것을 알게 하는 몫이 이 훅이다(ADR 0033, 명세 `.scratch/token-usage/spec.md`
"인계 훅"). 훅 러너가 한 훅을 이벤트 하나에만 받아(`tools/run_hooks.py` 의 `registered_hooks`) 두
파일로 나눴다. 알림은 사람에게만 가는 `systemMessage` 다. Stop 의 `additionalContext` 는 대화를 잇게
하므로 쓰지 않는다 (`.claude/rules/tools.md`).

한 번만 알리는 표지는 `tools/launch_hook.py` 의 모양이다. 임시 폴더(`tempfile.gettempdir()`) 아래
`STATE_DIR` 에 세션 ID 의 해시를 이름으로 한 빈 파일을 `O_EXCL` 로 만들고, 이 호출이 처음 만들었을
때만 알린다. 임시 폴더를 환경(`TEMP`·`TMP`·`TMPDIR`)으로 줄 수 있어 시험과 러너 사례가 빈 폴더를
쓴다. `hook_handoff` 가 인계를 지시할 때도 같은 이름의 표지를 만들어, 인계한 턴의 끝에는 알리지
않는다. 표지를 쓰지 못하거나 세션을 모르면 알리지 않는다 — 세션마다 거듭 보이는 것보다 놓치는 것이
낫다.

문턱, 세션 컨텍스트 셈(`session_context`, `tail_lines`), 표지 이름(`STATE_DIR`, `marker_name`)은
`tools/hook_handoff.py` 와 같다. 훅은 서로 import 하지 않아 따로 두고,
tests/tools/test_hook_handoff.py 의 `test_두_훅의_문턱과_셈과_표지_이름이_같다` 가 대조한다. 셈의
풀이와 침묵하는 자리(서브에이전트, 클라우드 세션)는 그 훅의 독스트링과 같다.

못 보는 것:
- 끝 `TAIL_BYTES` 안에 모델 응답이 없거나 마지막 응답 뒤에 압축 경계가 있는 트랜스크립트. 침묵한다.
- 표지의 수명. 임시 폴더에 세션마다 빈 파일 하나가 남고 지우지 않는다. 같은 세션 ID 로 이어 한
  세션은 다시 알리지 않는다.
- 알림이 데스크톱 앱에서 어떻게 보이는지(`tools/launch_hook.py` 독스트링과 같다).
- 데스크톱 세션 안에서 띄운 `claude -p` 세션. 대화형과 가르지 못한다.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TypedDict

# 아래 넷과 `session_context`·`tail_lines`·`marker_name` 은 tools/hook_handoff.py 와 같다.
THRESHOLD = 200_000
TAIL_BYTES = 2 * 1024 * 1024
STATE_DIR = "agent-os-handoff"


class HookPayload(TypedDict, total=False):
    """Claude Code 가 stdin 으로 주는 Stop 훅 입력 중 이 훅이 읽는 부분."""

    agent_id: str
    session_id: str
    transcript_path: str


class Usage(TypedDict, total=False):
    input_tokens: object
    cache_creation_input_tokens: object
    cache_read_input_tokens: object


class Message(TypedDict, total=False):
    model: str
    usage: Usage


class Record(TypedDict, total=False):
    type: str
    subtype: str
    isSidechain: bool
    message: Message


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


def notice_for(size: int) -> str:
    """사람에게 보일 알림."""
    return (
        f"세션 컨텍스트가 {size:,} 토큰으로 인계 문턱 {THRESHOLD:,} 을 넘었다. 다음 단계 경계(셀프 "
        "리뷰 직전, 커밋 뒤, PR 연 뒤)에서 이 세션은 지시문을 내고 같은 브랜치의 새 세션으로 "
        "넘어간다. 이 세션이 받은 범위가 그 경계에서 끝나거나, 인계로 연 세션이 넘겨받은 것과 "
        "같은 경계에 다시 오면 넘기지 않는다. 이 알림은 이 세션에서 한 번만 낸다."
    )


def claim_first(session_id: str) -> bool:
    """이 세션의 표지를 이 호출이 처음 만들었으면 True. 이미 있거나 만들지 못하면 False 다."""
    try:
        directory = os.path.join(tempfile.gettempdir(), STATE_DIR)
        os.makedirs(directory, exist_ok=True)
        path = os.path.join(directory, marker_name(session_id))
        os.close(os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
    except OSError:
        return False
    return True


def notice(payload: HookPayload, environ: Mapping[str, str]) -> str | None:
    """알릴 문장, 아니면 None. 표지는 문턱을 넘었을 때만 만든다."""
    if "agent_id" in payload or environ.get("CLAUDE_CODE_REMOTE") == "true":
        return None
    session_id = payload.get("session_id")
    transcript_path = payload.get("transcript_path")
    if not session_id or not transcript_path:
        return None
    size = session_context(tail_lines(Path(transcript_path), TAIL_BYTES))
    if size is None or size <= THRESHOLD or not claim_first(session_id):
        return None
    return notice_for(size)


def main() -> int:
    # stdin 은 바이트로. 이유는 .claude/rules/tools.md(대기열 25).
    payload: HookPayload = json.load(sys.stdin.buffer)
    message = notice(payload, os.environ)
    if message is None:
        return 0
    # ASCII 로 낸다. 훅 환경의 stdout 은 cp949 일 수 있다(대기열 25).
    print(json.dumps({"systemMessage": message}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
