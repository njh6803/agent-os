"""파일럿 회차의 stream-json 원본을 훑어 설계 8절 확인에 쓸 값을 찍는다.

회차 뿌리(`--rounds`) 아래 `<회차>/stream/*.jsonl`마다 init 칸, 이벤트 종류 수, 모델,
rate_limit_event 칸, 결과 이벤트, 도구 호출 수, 환경 변수를 본 명령, 커밋 호출의 훅 줄을 찍는다.
단언하지 않는 관찰 스크립트이고 읽기만 한다.

    uv run python .scratch/model-rerun/probes/pilot_checks/scan_streams.py \
        --rounds C:/Users/User/rerun-rounds
"""

import argparse
import json
import re
from collections import Counter
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--rounds", type=Path, required=True, help="회차 폴더들의 뿌리")
ROOT: Path = parser.parse_args().rounds


def events(path: Path):
    with path.open(encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                yield {"type": "__bad__"}


def text_of(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        out = []
        for c in content:
            if isinstance(c, dict):
                if c.get("type") == "text":
                    out.append(c.get("text", ""))
                elif "content" in c:
                    out.append(text_of(c["content"]))
        return "\n".join(out)
    return ""


for rd in sorted(ROOT.iterdir()):
    if not rd.is_dir():
        continue
    print("=" * 30, rd.name)
    for sf in sorted((rd / "stream").glob("*.jsonl")):
        print("--", sf.name)
        types = Counter()
        main_models = Counter()
        sub_models = Counter()
        rl_keys = set()
        rl_util = []
        results = []
        tool_uses = Counter()
        commit_cmds = []
        tool_use_by_id = {}
        commit_results = []
        env_cmds = []
        gh_token_hits = 0
        ask = []
        for ev in events(sf):
            t = ev.get("type")
            types[t] += 1
            if t == "system" and ev.get("subtype") == "init":
                plugins = [p.get("source") or p.get("name") for p in ev.get("plugins", [])]
                print(
                    f"  init model={ev.get('model')} mode={ev.get('permissionMode')}"
                    f" apiKeySource={ev.get('apiKeySource')}"
                    f" ver={ev.get('claude_code_version')} mcp={ev.get('mcp_servers')}"
                    f" plugins={plugins}"
                    f" ask_in_tools={'AskUserQuestion' in ev.get('tools', [])}"
                    f" style={ev.get('output_style')}"
                )
                print(f"  init memory_paths={ev.get('memory_paths')}")
            elif t == "assistant":
                m = ev.get("message", {}).get("model")
                if ev.get("parent_tool_use_id"):
                    sub_models[m] += 1
                else:
                    main_models[m] += 1
                for c in ev.get("message", {}).get("content", []) or []:
                    if isinstance(c, dict) and c.get("type") == "tool_use":
                        name = c.get("name")
                        tool_uses[name] += 1
                        inp = c.get("input", {})
                        tool_use_by_id[c.get("id")] = (name, inp)
                        if name in ("AskUserQuestion",) or (
                            name == "ToolSearch" and "AskUser" in json.dumps(inp)
                        ):
                            ask.append((name, json.dumps(inp, ensure_ascii=False)[:200]))
                        if name in ("Bash", "PowerShell"):
                            cmd = inp.get("command", "")
                            if re.search(r"git\s+(-C\s+\S+\s+)?commit", cmd):
                                commit_cmds.append(c.get("id"))
                            if re.search(
                                r"\b(printenv|env\b|Get-ChildItem\s+env:|\$env:|GH_TOKEN|GITHUB_TOKEN)",
                                cmd,
                            ):
                                env_cmds.append(cmd[:160])
            elif t == "user":
                for c in ev.get("message", {}).get("content", []) or []:
                    if isinstance(c, dict) and c.get("type") == "tool_result":
                        txt = text_of(c.get("content"))
                        if "GH_TOKEN" in txt or "GITHUB_TOKEN" in txt:
                            gh_token_hits += 1
                        if c.get("tool_use_id") in commit_cmds:
                            commit_results.append(txt)
            elif t == "rate_limit_event":
                info = ev.get("rate_limit_info", {})
                rl_keys |= set(info.keys())
                rl_util.append((info.get("status"), info.get("utilization")))
            elif t == "result":
                results.append(
                    dict(
                        subtype=ev.get("subtype"),
                        cost=ev.get("total_cost_usd"),
                        has_mu=bool(ev.get("modelUsage")),
                        mu=sorted((ev.get("modelUsage") or {}).keys()),
                        denials=len(ev.get("permission_denials") or []),
                        terminal=ev.get("terminal_reason"),
                    )
                )
        print("  types", dict(types))
        print("  main_models", dict(main_models), "sub_models", dict(sub_models))
        print("  rate_limit keys", sorted(rl_keys), "n", len(rl_util), "first", rl_util[:1])
        for r in results:
            print("  result", r)
        print("  tool_uses", dict(tool_uses.most_common(25)))
        print("  ask", ask)
        print("  env_cmds", env_cmds[:6])
        print("  GH_TOKEN/GITHUB_TOKEN in tool results:", gh_token_hits)
        print("  commit calls", len(commit_cmds), "results", len(commit_results))
        for txt in commit_results:
            hook_lines = [
                ln
                for ln in txt.splitlines()
                if re.search(r"(Passed|Failed|Skipped|\.\.\.\.|check-ticket|commit-msg|hook)", ln)
            ]
            print("   commit result head:", repr(txt[:120]))
            print(f"   hook lines ({len(hook_lines)}):", [h[:90] for h in hook_lines[:8]])
