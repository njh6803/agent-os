"""본 세션 기록 하나에서 인계 계기 뒤 모델이 '인계'를 말한 글과 도구 입력의 언저리를 찍는다.

세션 기록(`--session`, 전용 설정 폴더의 `<세션 id>.jsonl`)에서 '인계 문턱 200,000 을 넘'이 든 첫
비assistant 줄의 시각을 `[계기]`로, 그 뒤 본 세션 assistant의 글·도구 입력에서 '인계' 앞 120자와 뒤
200자를 `[모델]`로 찍는다. 단언하지 않는 관찰 스크립트이고 읽기만 한다.

    uv run python .scratch/model-rerun/probes/pilot_checks/handoff_reasons.py \
        --session C:/Users/User/.claude-rerun/projects/<프로젝트>/<세션 id>.jsonl
"""

import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--session", type=Path, required=True, help="본 세션 기록 파일(.jsonl)")
p: Path = parser.parse_args().session
seen_trigger = False
for line in p.open(encoding="utf-8", errors="replace"):
    try:
        d = json.loads(line)
    except json.JSONDecodeError:
        continue
    blob = line
    if "인계 문턱 200,000 을 넘" in blob and d.get("type") != "assistant":
        if not seen_trigger:
            print("[계기]", d.get("timestamp"), d.get("type"))
        seen_trigger = True
    if d.get("type") != "assistant" or d.get("isSidechain"):
        continue
    for c in (d.get("message") or {}).get("content") or []:
        if not isinstance(c, dict):
            continue
        text = c.get("text") if c.get("type") == "text" else None
        if c.get("type") == "tool_use":
            text = json.dumps(c.get("input"), ensure_ascii=False)
        if text and "인계" in text and seen_trigger:
            i = text.find("인계")
            print(
                "[모델]",
                d.get("timestamp"),
                c.get("type"),
                text[max(0, i - 120) : i + 200].replace("\n", " / "),
            )
