"""`run.sh`가 남긴 변형별 stream-json에서 init 이벤트의 `tools`·`mcp_servers`·`skills`만 찍는다.

답의 원문과 그 밖의 필드는 찍지 않는다. init에는 세션 id와 경로 같은 것도 있어 필요한 셋만 고른다.
MCP 도구는 이름 대신 서버 머리(`mcp__<서버>__`)별 개수로 찍는다. 스킬은 개수와 `code-review`가
있는지만 찍는다 — 좁힌 세션에서도 프로젝트 스킬이 실려야 카나리아가 그 스킬을 부를 수 있다.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path


def init_event(path: Path) -> dict[str, object] | None:
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        # claude 가 중간에 끝나면 마지막 줄이 잘릴 수 있다. 그 줄로 요약이 멈추지 않게 건너뛴다.
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(event, dict):
            continue
        if event.get("type") == "system" and event.get("subtype") == "init":
            return {str(key): value for key, value in event.items()}
    return None


def _strings(value: object) -> list[str]:
    return [str(item) for item in value] if isinstance(value, list) else []


def main() -> int:
    out = Path(sys.argv[1])
    for path in sorted(out.glob("*.jsonl")):
        event = init_event(path)
        if event is None:
            err = path.with_suffix(".err")
            tail = err.read_text(encoding="utf-8").strip().splitlines()[-1:] if err.exists() else []
            print(f"{path.stem}: init 없음 {tail}")
            continue
        tools = _strings(event.get("tools"))
        builtin = [name for name in tools if not name.startswith("mcp__")]
        per_server = Counter(name.split("__")[1] for name in tools if name.startswith("mcp__"))
        servers = event.get("mcp_servers")
        server_pairs = (
            [f"{s.get('name')}={s.get('status')}" for s in servers if isinstance(s, dict)]
            if isinstance(servers, list)
            else []
        )
        skills = _strings(event.get("skills"))
        print(f"{path.stem}: tools {len(tools)} 내장 {builtin} MCP {dict(per_server)}")
        print(f"{path.stem}: mcp_servers {len(server_pairs)} {server_pairs}")
        print(f"{path.stem}: skills {len(skills)} code-review {'code-review' in skills}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
