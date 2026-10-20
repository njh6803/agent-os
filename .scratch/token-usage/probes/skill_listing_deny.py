"""`permissions.deny`의 `Skill(이름)` 규칙이 스킬 목록에서 그 항목을 빼는지 잰다.

ADR 0033 이력 2026-10-20의 근거다. MCP 서버를 프로젝트 설정에서 끄듯 스킬을 끄는 길을 찾는다. 같은
이력에서 `skillOverrides`는 동기화된 스킬(`anthropic-skills:*`)을 앱 세션의 목록에서 빼지 못했다. 이
프로브는 그 전에, 거부 규칙이 호출만 막는지 목록에서도 빼는지를 프로젝트 스킬로 본다. 목록에서 빼지
못하면 동기화된 스킬에도 쓸 수 없다.

갈래 둘을 저장소 밖 임시 폴더에서 띄운다. 둘 다 이 저장소의 `.claude/skills`를 복사하고, A는 설정이
없고 B는 `.claude/settings.json`에 `permissions.deny`로 `Skill(grilling)`과 `Skill(retro)`만 둔다.
띄우는 명령과 기록 읽기는 같은 폴더의 `skill_listing_budget.py`의 것을 쓴다(haiku 한 턴, 설정 출처
`project,local`).

갈래 C는 B와 같은 설정에서 Skill 도구로 `grilling`을 한 번 부르게 한다(haiku, 최대 세 턴). 그
도구 결과가 오류이고 `DENIED`가 들어 있어야 B가 규칙을 읽었다는 것이 선다. 문구는 2026-10-20 같은
설정으로 한 번 띄운 원본에서 봤다.

표지: 갈래마다 `system/init`·`result` 이벤트가 있고, A와 B는 첫 모델 호출 전 `skill_listing` 첨부가
있다. 양성 대조는 셋이다. A의 목록에 두 대상이 설명과 함께 있어야 B에서 빠진 것이 규칙 탓이고, B의
목록에 거부하지 않은 `CONTROL`이 설명과 함께 있어야 B의 목록이 통째로 비거나 줄어든 것이 아니며, C의
거부 문구가 있어야 B에서 그대로인 것이 규칙을 읽지 않은 탓이 아니다. 하나라도 없으면 1로 끝난다.
판정은 대상마다 B의 `names`에 없다(목록에서 빠졌다), 이름만 남았다, 그대로다로 찍는다.

못 보는 것: 앱 세션과 동기화된 스킬. 그것은 이 결과가 "빠졌다"일 때 앱 세션을 새로 열어
`skill_listing_entries.py`로 본다.

돌리는 법: 저장소 루트에서 `uv run python .scratch/token-usage/probes/skill_listing_deny.py`.
`claude` CLI와 로그인이 든다. 갈래마다 haiku 호출 하나다.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import skill_listing_budget as budget_probe
import skill_listing_cli as cli_probe

TARGETS = ("grilling", "retro")
CONTROL = "code-review"
DENIED = "blocked by permission rules"
INVOKE_PROMPT = (
    "Skill 도구로 grilling 스킬을 한 번 부른다. 다른 도구는 쓰지 않는다. "
    "도구 결과를 그대로 옮겨 적고 끝낸다."
)


def invoke_command(claude: str) -> list[str]:
    command = cli_probe.command_for(claude)
    command[command.index(cli_probe.PROMPT)] = INVOKE_PROMPT
    command[command.index("--max-turns") + 1] = "3"
    return command


def denied_in(log: Path) -> tuple[bool, list[str]]:
    """(Skill 도구 결과가 거부 문구를 단 오류인가, 측정이 아닌 까닭)."""
    events = cli_probe.stream_events(log)
    reasons: list[str] = []
    if not any(e.get("type") == "system" and e.get("subtype") == "init" for e in events):
        reasons.append("system/init 이벤트가 없다")
    if not any(e.get("type") == "result" for e in events):
        reasons.append("result 이벤트가 없다")
    for event in events:
        message = event.get("message")
        content = message.get("content") if isinstance(message, dict) else None
        if not isinstance(content, list):
            continue
        for block in content:
            if (
                isinstance(block, dict)
                and block.get("type") == "tool_result"
                and block.get("is_error") is True
                and DENIED in str(block.get("content"))
            ):
                return True, reasons
    return False, reasons


def verdict(name: str, entries: dict[str, str], names: list[str]) -> str:
    if name not in names and name not in entries:
        return "목록에서 빠졌다"
    text = entries.get(name)
    if text is None or not budget_probe.has_description(name, text):
        return "이름만 남았다"
    return "그대로다"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--skills", type=Path, default=Path(".claude/skills"))
    parser.add_argument("--out", type=Path, default=None, help="stream-json 원본을 남길 폴더")
    args = parser.parse_args()
    claude = shutil.which("claude")
    if claude is None:
        print("claude CLI를 찾지 못했다")
        return 2
    if not args.skills.is_dir():
        print(f"{args.skills}가 폴더가 아니다")
        return 2
    unmeasured = 0
    listings: dict[str, tuple[str, list[str]]] = {}
    with tempfile.TemporaryDirectory(prefix="skill-deny-", ignore_cleanup_errors=True) as scratch:
        out_dir = args.out or Path(scratch) / "logs"
        out_dir.mkdir(parents=True, exist_ok=True)
        for variant in ("A", "B"):
            cwd = Path(scratch) / variant
            shutil.copytree(args.skills, cwd / ".claude" / "skills")
            if variant == "B":
                settings = {"permissions": {"deny": [f"Skill({t})" for t in TARGETS]}}
                (cwd / ".claude" / "settings.json").write_text(
                    json.dumps(settings), encoding="utf-8"
                )
            listing, reasons = budget_probe.run_variant(claude, cwd, out_dir / f"{variant}.jsonl")
            for reason in reasons:
                print(f"{variant}: 측정 아님: {reason}")
            unmeasured += bool(reasons)
            if listing is not None:
                listings[variant] = listing
        cwd = Path(scratch) / "C"
        shutil.copytree(args.skills, cwd / ".claude" / "skills")
        settings = {"permissions": {"deny": [f"Skill({t})" for t in TARGETS]}}
        (cwd / ".claude" / "settings.json").write_text(json.dumps(settings), encoding="utf-8")
        log = out_dir / "C.jsonl"
        with log.open("w", encoding="utf-8") as out:
            try:
                subprocess.run(
                    invoke_command(claude),
                    cwd=cwd,
                    stdin=subprocess.DEVNULL,
                    stdout=out,
                    stderr=subprocess.DEVNULL,
                    timeout=cli_probe.TIMEOUT_SECONDS,
                    check=False,
                )
            except subprocess.TimeoutExpired:
                print(f"C: 측정 아님: {cli_probe.TIMEOUT_SECONDS}초 안에 끝나지 않았다")
                unmeasured += 1
        denied, reasons = denied_in(log)
        for reason in reasons:
            print(f"C: 측정 아님: {reason}")
        unmeasured += bool(reasons)
        print(f"C: grilling 호출이 거부 문구를 단 오류로 막혔다: {denied}")
        if not denied:
            print("측정 아님: C에서 거부 문구가 없어 B가 규칙을 읽었는지 모른다")
            unmeasured += 1
    report: dict[str, dict[str, str]] = {}
    for variant, (text, names) in sorted(listings.items()):
        entries = budget_probe.entries_of(text)
        report[variant] = {n: verdict(n, entries, names) for n in (*TARGETS, CONTROL)}
        print(f"{variant}: 본문 {len(text):,}자, names {len(names)}개, {report[variant]}")
    a, b = report.get("A"), report.get("B")
    if a is not None and any(a[t] != "그대로다" for t in TARGETS):
        print("측정 아님: A의 목록에 대상이 설명과 함께 없다")
        unmeasured += 1
    if b is not None and b[CONTROL] != "그대로다":
        print(f"측정 아님: B의 목록에 거부하지 않은 {CONTROL}가 설명과 함께 없다")
        unmeasured += 1
    version = subprocess.run(
        [claude, "--version"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=60,
    )
    print(
        json.dumps(
            {
                "probe": "skill_listing_deny",
                "claude": version.stdout.strip(),
                "variants": report,
                "invoke_denied": denied,
                "unmeasured": unmeasured,
            },
            ensure_ascii=False,
        )
    )
    return 1 if unmeasured else 0


if __name__ == "__main__":
    sys.exit(main())
