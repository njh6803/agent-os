"""세션 셸에서 허용 목록 밖 변수(ANTHROPIC_API_KEY, GH_TOKEN 등)를 본 명령과 그 결과를 찍는다.

`<회차>/stream/*.jsonl`의 Bash·PowerShell 호출 가운데 그 변수 이름이나
`printenv`·`env`·`Get-ChildItem env:`가 든 명령을 골라, 명령의 그 언저리와 도구 결과의 앞 120자를
찍는다. 결과 앞 120자에 변수의 값이 실리면 그대로 찍히니 출력을 커밋하기 전에 본다. 단언하지 않는
관찰 스크립트이고 읽기만 한다.

    uv run python .scratch/model-rerun/probes/pilot_checks/key_checks.py \
        --rounds C:/Users/User/rerun-rounds
"""

import argparse
import json
import re
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--rounds", type=Path, required=True, help="회차 폴더들의 뿌리")
ROOT: Path = parser.parse_args().rounds
PAT = re.compile(
    r"ANTHROPIC_API_KEY|GH_TOKEN|GITHUB_TOKEN|printenv|\benv\b\s*($|\||;)|Get-ChildItem\s+env:"
)
for sf in sorted(ROOT.glob("*/stream/*.jsonl")):
    want: dict[str, str] = {}
    for line in sf.open(encoding="utf-8", errors="replace"):
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        for c in (
            (ev.get("message") or {}).get("content") or []
            if isinstance(ev.get("message"), dict)
            else []
        ):
            if not isinstance(c, dict):
                continue
            if c.get("type") == "tool_use" and c.get("name") in ("Bash", "PowerShell"):
                cmd = c.get("input", {}).get("command", "")
                if PAT.search(cmd):
                    want[c["id"]] = cmd
            elif c.get("type") == "tool_result" and c.get("tool_use_id") in want:
                content = c.get("content")
                txt = (
                    content
                    if isinstance(content, str)
                    else " ".join(x.get("text", "") for x in content or [] if isinstance(x, dict))
                )
                cmd = want[c["tool_use_id"]]
                seg = re.search(
                    r".{0,60}(ANTHROPIC_API_KEY|GH_TOKEN|GITHUB_TOKEN|printenv).{0,60}", cmd
                )
                print(
                    sf.parent.parent.name,
                    "| cmd~",
                    (seg.group(0) if seg else cmd[:100]).replace("\n", " "),
                    "| result~",
                    txt[:120].replace("\n", " / "),
                )
