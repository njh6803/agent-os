"""탐침 Stop 훅. 받은 입력과 그 순간의 트랜스크립트를 `run.sh` 가 넘긴 파일에 한 줄씩 덧붙인다.

환경 변수는 이름만 적는다(값에 토큰이 있을 수 있다, 원칙 V). 값을 적는 것은
`CLAUDE_CODE_ENTRYPOINT` 와 `PYTHONUTF8` 둘이다. 트랜스크립트에서는 assistant 텍스트 블록과
기록마다의 `entrypoint` 값(겹치지 않게)을 적는다. 첫 호출(`stop_hook_active` 가 거짓)은 멈춤을 한 번
막아, 둘째 호출의 입력과 막은 이유가 모델에게 어떻게 닿는지 보게 한다.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def read_transcript(transcript: Path) -> tuple[list[str], list[str]]:
    """트랜스크립트의 assistant 텍스트 블록 전부(사이드체인 제외, 순서대로)와 `entrypoint` 값들."""
    texts: list[str] = []
    entrypoints: set[str] = set()
    if not transcript.exists():
        return texts, []
    for line in transcript.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            record = json.loads(line)
        except ValueError:
            continue
        if record.get("entrypoint"):
            entrypoints.add(record["entrypoint"])
        if record.get("type") != "assistant" or record.get("isSidechain"):
            continue
        for block in record.get("message", {}).get("content", []):
            if block.get("type") == "text":
                texts.append(block.get("text", ""))
    return texts, sorted(entrypoints)


def main() -> int:
    out = Path(sys.argv[1])
    payload = json.loads(sys.stdin.buffer.read())
    texts, entrypoints = read_transcript(Path(payload.get("transcript_path", "")))
    entry = {
        "payload_keys": sorted(payload),
        "stop_hook_active": payload.get("stop_hook_active"),
        "stop_reason": payload.get("stop_reason"),
        "last_assistant_message": payload.get("last_assistant_message"),
        "transcript_texts_now": texts,
        "transcript_entrypoints": entrypoints,
        "env_claude_names": sorted(name for name in os.environ if name.startswith("CLAUDE")),
        "CLAUDE_CODE_ENTRYPOINT": os.environ.get("CLAUDE_CODE_ENTRYPOINT"),
        "PYTHONUTF8": os.environ.get("PYTHONUTF8"),
    }
    with out.open("a", encoding="utf-8") as log:
        log.write(json.dumps(entry, ensure_ascii=False) + "\n")
    if not payload.get("stop_hook_active"):
        print(json.dumps({"decision": "block", "reason": "Now write the single word BETA."}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
