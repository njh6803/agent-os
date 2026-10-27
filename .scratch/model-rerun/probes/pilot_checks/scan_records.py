"""파일럿 회차 기록(`records/*.json`)의 칸을 회차마다 몇 줄로 찍는다.

조건 판, 계정, 판, 끝, 인계, 개입, 환경 변수 이름의 유무, 세션·호출, 결과, 게이트, 숨은 테스트,
지출을 찍는다. 기록 폴더는 기본이 이 파일 옆의 `../records`다. 단언하지 않는 관찰 스크립트이고
읽기만 한다.

    uv run python .scratch/model-rerun/probes/pilot_checks/scan_records.py
"""

import argparse
import json
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument(
    "--records",
    type=Path,
    default=Path(__file__).resolve().parent.parent / "records",
    help="회차 기록 폴더(기본: probes/records)",
)
rec_dir: Path = parser.parse_args().records
for p in sorted(rec_dir.glob("*.json")):
    r = json.loads(p.read_text(encoding="utf-8"))
    print(
        "==",
        p.name,
        "cv",
        r["condition_version"],
        "dir",
        r["round_dir_name"],
        "acct",
        r["account"],
        "ver",
        r["claude_version"],
    )
    print(
        "  end",
        r["end"],
        "handoffs",
        r["handoffs"],
        "interv",
        r["interventions"],
        "asked_at_end",
        r["asked_at_end"],
    )
    print(
        "  env has GH_TOKEN?",
        "GH_TOKEN" in r["env_names"],
        "GITHUB_TOKEN?",
        "GITHUB_TOKEN" in r["env_names"],
        "ANTHROPIC_API_KEY?",
        "ANTHROPIC_API_KEY" in r["env_names"],
        "n_env",
        len(r["env_names"]),
    )
    print("  init_tools n", len(r["init_tools"]), "Ask?", "AskUserQuestion" in r["init_tools"])
    for s in r["sessions"]:
        print(
            "  session",
            s["session_id"][:8],
            "cost",
            round(s["cost_usd"], 4),
            "subst",
            s["cost_substituted"],
            "killed",
            s["runner_killed"],
        )
        for c in s["calls"]:
            print(
                "    call",
                c["kind"],
                "budget",
                c["budget_usd"],
                "exit",
                c["exit_code"],
                "results",
                [(x["subtype"], x["terminal_reason"], x["num_turns"]) for x in c["results"]],
                "dir",
                c["has_directive"],
                "q",
                c["ends_with_question"],
            )
        print("    main_lines", s["main_lines"])
        print("    sub_lines", s["subagent_lines"])
        print("    model_usage", [(m["model"], round(m["cost_usd"], 4)) for m in s["model_usage"]])
    o = r.get("outcome")
    if o:
        print(
            "  outcome commit",
            (o.get("commit") or "")[:8],
            "rule",
            o.get("rule"),
            "after_base",
            o.get("commits_after_base"),
            "setup_fail",
            o.get("setup_failure"),
        )
        print(
            "  gates",
            [(g["command"], g["exit_code"], g["timed_out"]) for g in (o.get("gates") or [])],
        )
        h = o.get("hidden")
        if h:
            print("  hidden", h["passed"], "/", h["total"])
    sp = r["spend"]
    print(
        "  spend cc",
        round(sp["claude_code_usd"], 4),
        "official",
        sp["official_usd"] and round(sp["official_usd"], 4),
        "wall",
        sp["wall_seconds"],
        "denied",
        sp["denied_calls"],
    )
    print("  util start", sp["utilization_start"], "end", sp["utilization_end"])
    print(
        "  contamination",
        sp["contamination"],
        "mismatch",
        sp["model_mismatch"],
        "subst",
        sp["substitutes"],
    )
