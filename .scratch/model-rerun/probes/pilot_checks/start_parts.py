"""설계 8절 8: 시작 컨텍스트(start_parts)를 다시 풀기 세션과 원래 브랜치의 실제 세션에서 견준다.

다시 풀기 쪽은 전용 설정 폴더(`--projects`)의 본 세션 기록에서 `tools/token_report.py`의
`start_parts_of`와 같은 셈(첫 모델 호출 전 첨부: skill_listing 출처별, deferred_tools_delta,
instructions, 그 밖. prompt_snapshot 빼기)을 옮겨 한다. 원래 쪽은 주 체크아웃 장부
폴더(`--ledger`)의 `<달>.jsonl`에서 session 행의 start_parts를 그대로 읽는다. 원래 세션은 그
브랜치의 call 행이 든 본 세션(agent가 null)이다. 브랜치 목록은 이 파일 옆의 `../pilot.json`이다.
단언하지 않는 관찰 스크립트이고 읽기만 한다.

    uv run python .scratch/model-rerun/probes/pilot_checks/start_parts.py \
        --rounds C:/Users/User/rerun-rounds --projects C:/Users/User/.claude-rerun/projects \
        --ledger C:/project/agent/.scratch/token-report/ledger
"""

import argparse
import json
import re
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--rounds", type=Path, required=True, help="회차 폴더들의 뿌리")
parser.add_argument("--projects", type=Path, required=True, help="전용 설정 폴더의 projects")
parser.add_argument("--ledger", type=Path, required=True, help="주 체크아웃의 장부 폴더")
parser.add_argument("--month", default="2026-10", help="장부 파일의 달(기본: 2026-10)")
args = parser.parse_args()
LEDGER: Path = args.ledger / f"{args.month}.jsonl"
CFG: Path = args.projects
ROOT: Path = args.rounds
PILOT = Path(__file__).resolve().parent.parent / "pilot.json"
SKILL_SOURCE = re.compile(r"^- ([^\s:]+):")


def skill_sources(listing: str) -> dict[str, int]:
    out: dict[str, int] = {}
    source = "(프로젝트·내장)"
    for line in listing.splitlines():
        if line.startswith("- "):
            m = SKILL_SOURCE.match(line)
            source = m.group(1) if m else "(프로젝트·내장)"
        out[source] = out.get(source, 0) + len(line) + 1
    return out


def start_parts(path: Path) -> dict:
    skills: dict[str, int] = {}
    deferred = instructions = other = 0
    for line in path.open(encoding="utf-8", errors="replace"):
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        if d.get("type") == "assistant":
            m = d.get("message") or {}
            if isinstance(m.get("usage"), dict) and m.get("model") != "<synthetic>":
                break
        if d.get("type") != "attachment":
            continue
        a = d.get("attachment") or {}
        kind = a.get("type")
        if kind == "skill_listing":
            for s, n in skill_sources(a.get("content") or "").items():
                skills[s] = skills.get(s, 0) + n
        elif kind == "deferred_tools_delta":
            deferred += sum(len(x or "") + 1 for x in a.get("addedLines") or [])
        elif kind == "instructions":
            instructions += sum(len((f or {}).get("content") or "") for f in a.get("files") or [])
        elif kind != "prompt_snapshot":
            other += len(json.dumps(a, ensure_ascii=False))
    return {
        "skills": skills,
        "deferred_tools": deferred,
        "instructions": instructions,
        "other": other,
    }


def total(sp: dict) -> int:
    return sum(sp["skills"].values()) + sp["deferred_tools"] + sp["instructions"] + sp["other"]


pilot = json.loads(PILOT.read_text(encoding="utf-8"))
branches = {t["branch"]: t["task_id"] for t in pilot["tasks"]}
sess_branch: dict[str, str] = {}
sess_rows: dict[str, dict] = {}
for line in LEDGER.open(encoding="utf-8"):
    if '"kind": "call"' in line:
        if not any(b in line for b in branches):
            continue
        r = json.loads(line)
        if r.get("branch") in branches and r.get("agent") is None:
            sess_branch.setdefault(r["session"], r["branch"])
    elif '"kind": "session"' in line:
        r = json.loads(line)
        sess_rows[r["session"]] = r

print("## 원래 브랜치의 세션(주 체크아웃 장부)")
for sid, br in sorted(sess_branch.items(), key=lambda x: sess_rows.get(x[0], {}).get("start", "")):
    r = sess_rows.get(sid)
    if not r:
        print(branches[br], sid[:8], "session 행 없음")
        continue
    sp = r.get("start_parts")
    print(
        branches[br],
        sid[:8],
        r["start"],
        "human",
        r.get("human"),
        "handoff",
        r.get("handoff"),
        "total",
        sp and total(sp),
        json.dumps(sp, ensure_ascii=False),
    )

print("## 다시 풀기 본 세션(전용 설정 폴더, 판 2)")
for rd in sorted(ROOT.iterdir()):
    ids = []
    for x in (rd / "session-ids.txt").read_text().splitlines():
        if x.strip() and x.strip() not in ids:
            ids.append(x.strip())
    proj = CFG / ("C--Users-User-rerun-rounds-" + rd.name + "-clone")
    for sid in ids:
        sp = start_parts(proj / f"{sid}.jsonl")
        print(rd.name, sid[:8], "total", total(sp), json.dumps(sp, ensure_ascii=False))
