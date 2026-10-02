"""`run.sh` 가 남긴 `<변형>.pretool.jsonl` 을 한 호출에 한 줄로 줄여 찍는다.

줄마다 훅이 시작한 때(초의 끝 세 자리), 이벤트, 도구와 명령, 서브에이전트 표지, 처음 읽었을 때 자기
tool_use 가 있었는가, 기다린 밀리초, 기다린 뒤의 꼬리(텍스트는 글, tool_use·tool_result 는 id 끝)다.
처음에 없었으면 다음 줄에 처음 읽은 꼬리를 `처음 꼬리` 로 찍는다. 지금의 `dump_pretool.py` 가 남긴
출력만 읽는다.
쓰는 법: `uv run python .scratch/harness/probes/pretool_text/summarize.py <디렉터리>`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def compact(entry: list[str]) -> str:
    side = "side:" if entry[0] == "side" else ""
    body = entry[1:] if side else entry
    if len(body) >= 4 and body[2] == "text":
        return f"{side}T({body[3]})"
    if len(body) >= 4 and body[2] == "tool_use":
        return f"{side}U({body[3][-4:]})"
    if len(body) >= 4 and body[2] == "tool_result":
        return f"{side}R({body[3][-4:]})"
    return f"{side}{body[0][0]}"


def compact_tail(tail: list[list[str]]) -> str:
    return " ".join(compact(x) for x in tail if x[-1] != "thinking")


def main() -> int:
    work = Path(sys.argv[1])
    for log in sorted(work.glob("*.pretool.jsonl")):
        print(f"== {log.name.removesuffix('.pretool.jsonl')}")
        for line in log.read_text(encoding="utf-8").splitlines():
            e = json.loads(line)
            what = e["command"] or e["tool_name"]
            agent = f" agent={e['agent_type']}" if e["agent_id_present"] else ""
            print(
                f"{e['started']:8.3f} {e['event']:<11} {what[-11:]:<11}"
                f" id={e['tool_use_id'][-4:]}{agent}"
                f" 처음={e['own_tool_use_at_start']} 기다림={e['waited_ms']}ms"
                f" 뒤={e['own_tool_use_after_wait']} | {compact_tail(e['tail'])}"
            )
            if not e["own_tool_use_at_start"]:
                print(f"{'':>9}처음 꼬리 | {compact_tail(e['tail_at_start'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
