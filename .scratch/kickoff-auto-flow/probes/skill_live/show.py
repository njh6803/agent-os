"""`run.py` 가 남긴 stream-json 기록 하나를 사람이 읽을 줄로 찍는다.

턴마다 `system/init` 의 스킬 목록에 프로브 스킬이 있었는지, 다시 낸 사용자 입력(인식된 명령이면
`<command-name>` 태그다), 모델의 글, 결과를 찍는다.

돌리는 법: `uv run python .scratch/kickoff-auto-flow/probes/skill_live/show.py <기록.jsonl>`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def _flat(text: str) -> str:
    return " | ".join(text.splitlines())[:300]


def _blocks(content: object) -> list[str]:
    if isinstance(content, str):
        return [f"글 {_flat(content)}"]
    shown: list[str] = []
    if not isinstance(content, list):
        return shown
    for block in content:
        if not isinstance(block, dict):
            continue
        kind = block.get("type")
        if kind == "text":
            shown.append(f"글 {_flat(str(block.get('text')))}")
        elif kind == "tool_use":
            shown.append(f"도구 호출 {_flat(json.dumps(block.get('input'), ensure_ascii=False))}")
        elif kind == "tool_result":
            shown.append(f"도구 결과 {_flat(str(block.get('content')))}")
    return shown


def main() -> int:
    for line in Path(sys.argv[1]).read_text(encoding="utf-8").splitlines():
        # run.py 는 JSON 이 아닌 줄도 기록에 그대로 남긴다.
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            print(f"(JSON 아님) {_flat(line)}")
            continue
        if not isinstance(event, dict):
            continue
        kind = event.get("type")
        if kind == "system" and event.get("subtype") == "init":
            skills = event.get("skills")
            commands = event.get("slash_commands")
            names = [
                *(skills if isinstance(skills, list) else []),
                *(commands if isinstance(commands, list) else []),
            ]
            probes = sorted({name for name in names if "probe" in str(name)})
            print(f"init: 프로브 스킬 {probes or '없음'}")
        elif kind in ("user", "assistant"):
            message = event.get("message")
            if isinstance(message, dict):
                for shown in _blocks(message.get("content")):
                    print(f"{kind}: {shown}")
        elif kind == "result":
            print(f"result: {_flat(str(event.get('result')))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
