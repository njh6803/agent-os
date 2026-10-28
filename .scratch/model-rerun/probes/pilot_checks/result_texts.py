"""회차 폴더 하나의 stream 파일마다 결과 이벤트 글의 끝을 찍는다.

`<회차>/stream/*.jsonl`의 result 이벤트마다 `result` 글의 끝 `--tail`자(기본 300)를 줄바꿈을 ` / `로
바꿔 찍는다. 단언하지 않는 관찰 스크립트이고 읽기만 한다.

    uv run python .scratch/model-rerun/probes/pilot_checks/result_texts.py \
        --round C:/Users/User/rerun-rounds/<회차> --tail 300
"""

import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--round", type=Path, required=True, help="회차 폴더 하나")
parser.add_argument("--tail", type=int, default=300, help="찍을 끝 글자 수(기본 300)")
args = parser.parse_args()

for sf in sorted((args.round / "stream").glob("*.jsonl")):
    print("--", sf.name)
    for line in sf.open(encoding="utf-8", errors="replace"):
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        if ev.get("type") == "result":
            t = (ev.get("result") or "").replace("\n", " / ")
            print("  result:", t[-args.tail :])
