"""회차마다 압축 경계, 훅 이벤트 속 인계 언급, 클론 장부의 다른 세션 id를 센다.

`<회차>/stream/*.jsonl`마다 system 이벤트의 subtype 수, `compact_boundary`의 메타데이터, 훅 이벤트
이름 수, 훅 이벤트에 '인계'·`handoff`가 든 수, 첫 사용자 메시지 앞 160자를 찍는다. 클론 장부
(`accounts.jsonl`)에서 `session-ids.txt`에 없는 세션 id는 전용 설정 폴더(`--projects`)에서 이름이
맞는 파일을 찾아 함께 찍는다. 단언하지 않는 관찰 스크립트이고 읽기만 한다.

    uv run python .scratch/model-rerun/probes/pilot_checks/compact_handoff.py \
        --rounds C:/Users/User/rerun-rounds --projects C:/Users/User/.claude-rerun/projects
"""

import argparse
import json
from collections import Counter
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--rounds", type=Path, required=True, help="회차 폴더들의 뿌리")
parser.add_argument("--projects", type=Path, required=True, help="전용 설정 폴더의 projects")
args = parser.parse_args()
ROOT: Path = args.rounds
CFG: Path = args.projects

for rd in sorted(ROOT.iterdir()):
    ids = [x.strip() for x in (rd / "session-ids.txt").read_text().splitlines() if x.strip()]
    print("==", rd.name, "ids", [i[:8] for i in ids])
    for sf in sorted((rd / "stream").glob("*.jsonl")):
        sub = Counter()
        compacts = []
        handoff_mentions = 0
        hook_names = Counter()
        first_user = None
        for line in sf.open(encoding="utf-8", errors="replace"):
            try:
                ev = json.loads(line)
            except json.JSONDecodeError:
                continue
            if ev.get("type") == "system":
                st = ev.get("subtype")
                sub[st] += 1
                if st == "compact_boundary":
                    compacts.append(ev.get("compact_metadata"))
                if st in ("hook_response", "hook_started"):
                    hook_names[ev.get("hook_name") or ev.get("hook_event")] += 1
                    blob = json.dumps(ev, ensure_ascii=False)
                    if "인계" in blob or "handoff" in blob:
                        handoff_mentions += 1
            if ev.get("type") == "user" and first_user is None and not ev.get("parent_tool_use_id"):
                c = ev.get("message", {}).get("content")
                first_user = c if isinstance(c, str) else json.dumps(c, ensure_ascii=False)
        print("  ", sf.name, "system subtypes", dict(sub))
        print(
            "     compacts",
            compacts,
            "hook events",
            dict(hook_names),
            "handoff-in-hook",
            handoff_mentions,
        )
        print("     first user msg:", (first_user or "")[:160].replace("\n", " | "))
    acc = rd / "clone" / ".scratch" / "token-report" / "ledger" / "accounts.jsonl"
    if acc.exists():
        others = []
        for line in acc.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            sid = r.get("session_id")
            if sid not in ids:
                where = [str(p.relative_to(CFG)) for p in CFG.rglob(f"*{sid}*")][:2]
                others.append((sid[:8] if sid else sid, r.get("source"), where))
        print("  ledger rows not in session-ids:", others)
