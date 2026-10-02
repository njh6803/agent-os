"""run.sh 가 남긴 변형별 stream-json 에서 Bash 호출의 명령과 도구 결과(오류 여부, 앞부분)만 찍는다.

잘린 줄은 건너뛴다(canary_init/summarize.py 와 같다).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def _blocks(event: object, role: str) -> list[dict[str, object]]:
    if not isinstance(event, dict) or event.get("type") != role:
        return []
    message = event.get("message")
    if not isinstance(message, dict):
        return []
    content = message.get("content")
    if not isinstance(content, list):
        return []
    return [block for block in content if isinstance(block, dict)]


def _text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [part.get("text", "") for part in content if isinstance(part, dict)]
        return " ".join(str(part) for part in parts)
    return str(content)


def summarize(path: Path) -> list[str]:
    """Bash 호출과 도구 결과, 훅의 systemMessage(`informational` 이벤트, 대기열 93), 모델의 답
    텍스트."""
    lines: list[str] = []
    for raw in path.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict) and event.get("subtype") == "informational":
            lines.append(f"  사용자 알림: {str(event.get('content'))[:160]}")
        for block in _blocks(event, "assistant"):
            if block.get("type") == "tool_use":
                tool_input = block.get("input")
                command = tool_input.get("command") if isinstance(tool_input, dict) else None
                lines.append(f"  호출 {block.get('name')}: {command}")
            if block.get("type") == "text":
                lines.append(f"  답: {' '.join(str(block.get('text')).split())[:240]}")
        for block in _blocks(event, "user"):
            if block.get("type") == "tool_result":
                text = " ".join(_text(block.get("content")).split())
                lines.append(f"  결과 is_error={block.get('is_error', False)}: {text[:240]}")
    return lines or ["  Bash 호출 없음"]


def main() -> int:
    out = Path(sys.argv[1])
    for path in sorted(out.glob("*.jsonl")):
        print(path.stem)
        for line in summarize(path):
            print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
