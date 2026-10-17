"""`run.sh` 가 남긴 `start.jsonl` 에서 한 갈래의 마지막 줄이 재려는 상황인지 단언하고 그 줄을
찍는다.

재려는 상황은 SessionStart 의 `startup` 이 그 갈래(`headless`·`interactive`)의 탐침 훅을 실제로
불렀고, 세션 표지 변수 `CLAUDE_CODE_SESSION_ATTENDED` 가 환경에 있었다는
것이다(`.claude/rules/probes.md` 의 첫 항목). 그 갈래의 줄이 없거나 표지가 하나라도 다르면 1로
끝난다. 첫 판의 `run.sh` 는 결과를 찍기만 해 다른 상황의 줄도 성공으로 끝났다(PR #277 CodeRabbit).

쓰는 법: `uv run python <이 파일> <start.jsonl> <headless|interactive>`
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    path, label = Path(sys.argv[1]), sys.argv[2]
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    mine = [row for row in rows if row.get("label") == label]
    if not mine:
        print(f"측정 아님: {label} 갈래의 줄이 없다")
        return 1
    row = mine[-1]
    payload, env = row.get("payload", {}), row.get("env_values", {})
    problems = [
        f"{key} 가 {want!r} 가 아니다({got!r})"
        for key, want, got in (
            ("hook_event_name", "SessionStart", payload.get("hook_event_name")),
            ("source", "startup", payload.get("source")),
        )
        if got != want
    ]
    if env.get("CLAUDE_CODE_SESSION_ATTENDED") is None:
        problems.append("CLAUDE_CODE_SESSION_ATTENDED 가 훅 환경에 없다")
    if problems:
        print("측정 아님: " + "; ".join(problems))
        return 1
    print(json.dumps(row, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
