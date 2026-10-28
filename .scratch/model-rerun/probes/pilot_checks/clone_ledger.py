"""회차 클론의 사용량 장부가 그 회차의 세션 id를 드는지 센다.

회차마다 `<회차>/clone/.scratch/token-report/` 아래 파일 목록, `ledger/accounts.jsonl`의 행 수,
`<회차>/session-ids.txt`의 id가 든 행 수, 행의 키와 `source` 값을 찍는다. 이메일 칸의 값은 찍지
않는다. 단언하지 않는 관찰 스크립트이고 읽기만 한다.

    uv run python .scratch/model-rerun/probes/pilot_checks/clone_ledger.py \
        --rounds C:/Users/User/rerun-rounds
"""

import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--rounds", type=Path, required=True, help="회차 폴더들의 뿌리")
ROOT: Path = parser.parse_args().rounds
for rd in sorted(ROOT.iterdir()):
    tr = rd / "clone" / ".scratch" / "token-report"
    ids = [x.strip() for x in (rd / "session-ids.txt").read_text().splitlines() if x.strip()]
    if not tr.exists():
        print(rd.name, "token-report 없음")
        continue
    files = [p for p in tr.rglob("*") if p.is_file()]
    acc = tr / "ledger" / "accounts.jsonl"
    rows = (
        [json.loads(line) for line in acc.read_text(encoding="utf-8").splitlines() if line.strip()]
        if acc.exists()
        else []
    )
    keys = sorted(rows[0].keys()) if rows else []
    hit = sum(1 for r in rows if any(i in json.dumps(r) for i in ids))
    sources = sorted({str(r.get("source")) for r in rows})
    print(
        rd.name,
        "files",
        [str(p.relative_to(tr)) for p in files],
        "rows",
        len(rows),
        "id-hits",
        hit,
        "keys",
        keys,
        "sources",
        sources,
    )
