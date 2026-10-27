"""`skillListingBudgetFraction`을 낮추면 스킬 목록에서 어느 항목의 설명이 먼저 줄거나 빠지는지 잰다.

ADR 0033 이력 2026-10-20의 근거다. 그 이력이 고르지 않은 안 가운데 "스킬 목록 예산을 낮춘다"가
무엇을 치르는지 보려고 한다. 예산은 문맥 창에 이 비율을 곱한 값이라(기본 0.01) 모델마다 다르고, 이
프로브는 비율을 바꿔 가며 줄어드는 차례를 본다.

갈래마다 저장소 밖 임시 폴더에 이 저장소의 `.claude/skills`를 복사하고, `.claude/settings.json`에
`skillListingBudgetFraction`만 둔다(기본 갈래는 설정 파일을 두지 않는다). 훅은 옮기지 않는다. 설정
출처는 `project,local`로 고정한다. 까닭은 같은 폴더의 `skill_listing_cli.py` 독스트링과 같다(이
기계의 사용자 설정은 Stop 훅으로 턴마다 Slack에 알림을 보낸다). 그래서 목록에는 프로젝트 스킬과
내장 스킬만 있고, 앱 세션의 `anthropic-skills:*`와 플러그인 스킬은 없다.

갈래마다 `claude -p`(haiku) 한 턴을 띄우고, 그 세션의 기록에서 첫 모델 호출 전 `skill_listing`
첨부를 읽는다. 첨부에는 본문(`content`)과 이름 목록(`names`)이 따로 있다(2026-10-20 앱 세션의
기록에서 봤다). 본문은 `- 이름: 설명` 줄로 항목을 가르고, 항목 줄이 아닌 줄은 앞 항목에 붙인다.
가장 큰 비율의 갈래가 대조다. 다른 갈래의 항목마다 대조와 견줘 그대로, 줄었다, 이름만(설명 없이
`- 이름`), 본문에 없다(`names`에는 있다), 아예 없다로 가른다.

표지: 갈래마다 `system/init`과 `result` 이벤트, 기록, 첫 모델 호출 전 `skill_listing` 첨부가 있다.
양성 대조는 둘이다. 대조 갈래의 본문에 `diagnosing-bugs`가 설명과 함께 있어야 복사한 프로젝트
스킬이 실렸다는 것이 서고, 대조보다 본문이 짧은 갈래가 하나라도 있어야 이 설정 출처에서 비율을
읽었다는 것이 선다. 하나라도 없으면 1로 끝난다.

못 보는 것: 앱 세션의 목록. 앱 세션은 문맥 창(2026-10-20 이 세션은 입력 토큰이 36만을 넘었다)과
항목의 수가 달라 같은 비율에서 줄어드는 항목이 다를 수 있다. 여기서 보는 것은 줄어드는 차례의
모양이다.

돌리는 법: 저장소 루트에서 `uv run python .scratch/token-usage/probes/skill_listing_budget.py`.
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

import skill_listing_cli as cli_probe
import skill_listing_entries as entries_probe

FRACTIONS: tuple[float | None, ...] = (0.05, None, 0.005, 0.0025, 0.001)
CONTROL_SKILL = "diagnosing-bugs"


def label_of(fraction: float | None) -> str:
    return "기본" if fraction is None else str(fraction)


def first_listing(transcript: Path) -> tuple[str, list[str]] | None:
    """첫 모델 호출 전 `skill_listing` 첨부들의 (본문을 이은 것, 이름 목록). 없으면 None."""
    texts: list[str] = []
    names: list[str] = []
    for rec in entries_probe.read_records(transcript):
        if entries_probe.is_model_call(rec):
            break
        text = entries_probe.listing_text(rec)
        if text is None:
            continue
        texts.append(text)
        attachment = rec.get("attachment")
        raw = attachment.get("names") if isinstance(attachment, dict) else None
        if isinstance(raw, list):
            names.extend(str(n) for n in raw)
    if not texts:
        return None
    return "\n".join(texts), names


def entries_of(text: str) -> dict[str, str]:
    """항목 이름마다 그 항목의 글(뒤따르는 항목 아닌 줄까지)."""
    out: dict[str, str] = {}
    current: str | None = None
    for line in text.splitlines():
        entry = entries_probe.entry_of(line)
        if entry is not None:
            current = entry
            out[entry] = line
        elif current is not None:
            out[current] += "\n" + line
    return out


def has_description(name: str, text: str) -> bool:
    return len(text) > len(f"- {name}:")


def compare(control: dict[str, str], other: dict[str, str], names: list[str]) -> dict[str, object]:
    shortened: list[str] = []
    name_only: list[str] = []
    body_missing: list[str] = []
    gone: list[str] = []
    for name, text in control.items():
        now = other.get(name)
        if now is None:
            (body_missing if name in names else gone).append(name)
        elif not has_description(name, now):
            name_only.append(name)
        elif len(now) < len(text):
            shortened.append(f"{name}({len(text)}→{len(now)})")
    return {
        "shortened": shortened,
        "name_only": name_only,
        "body_missing": body_missing,
        "gone": gone,
    }


def run_variant(
    claude: str, cwd: Path, log: Path
) -> tuple[tuple[str, list[str]] | None, list[str]]:
    """(첫 목록, 측정이 아닌 까닭)."""
    reasons: list[str] = []
    with log.open("w", encoding="utf-8") as out:
        try:
            subprocess.run(
                cli_probe.command_for(claude),
                cwd=cwd,
                stdin=subprocess.DEVNULL,
                stdout=out,
                stderr=subprocess.DEVNULL,
                timeout=cli_probe.TIMEOUT_SECONDS,
                check=False,
            )
        except subprocess.TimeoutExpired:
            reasons.append(f"{cli_probe.TIMEOUT_SECONDS}초 안에 끝나지 않았다")
    events = cli_probe.stream_events(log)
    init = next(
        (e for e in events if e.get("type") == "system" and e.get("subtype") == "init"), None
    )
    if init is None:
        reasons.append("system/init 이벤트가 없다")
        return None, reasons
    if not any(e.get("type") == "result" for e in events):
        reasons.append("result 이벤트가 없다")
    session_id = init.get("session_id")
    transcript = cli_probe.transcript_of(session_id) if isinstance(session_id, str) else None
    if transcript is None:
        reasons.append(f"세션 {session_id}의 기록을 찾지 못했다")
        return None, reasons
    listing = first_listing(transcript)
    if listing is None:
        reasons.append(f"기록 {transcript.name}에 첫 모델 호출 전 skill_listing 첨부가 없다")
    return listing, reasons


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
    with tempfile.TemporaryDirectory(prefix="skill-budget-", ignore_cleanup_errors=True) as scratch:
        out_dir = args.out or Path(scratch) / "logs"
        out_dir.mkdir(parents=True, exist_ok=True)
        for i, fraction in enumerate(FRACTIONS):
            label = label_of(fraction)
            cwd = Path(scratch) / f"v{i}"
            shutil.copytree(args.skills, cwd / ".claude" / "skills")
            if fraction is not None:
                settings = {"skillListingBudgetFraction": fraction}
                (cwd / ".claude" / "settings.json").write_text(
                    json.dumps(settings), encoding="utf-8"
                )
            listing, reasons = run_variant(claude, cwd, out_dir / f"v{i}.jsonl")
            for reason in reasons:
                print(f"{label}: 측정 아님: {reason}")
            unmeasured += bool(reasons)
            if listing is not None:
                listings[label] = listing
    control_label = label_of(FRACTIONS[0])
    report: dict[str, object] = {}
    control = listings.get(control_label)
    if control is None:
        print(f"측정 아님: 대조 갈래 {control_label}의 목록이 없다")
        unmeasured += 1
    else:
        control_entries = entries_of(control[0])
        control_text = control_entries.get(CONTROL_SKILL)
        if control_text is None or not has_description(CONTROL_SKILL, control_text):
            print(f"측정 아님: 대조 갈래 본문에 {CONTROL_SKILL}가 설명과 함께 없다")
            unmeasured += 1
        print(f"대조 {control_label}: 본문 {len(control[0]):,}자, 항목 {len(control_entries)}개")
        bound = False
        for fraction in FRACTIONS[1:]:
            label = label_of(fraction)
            listing = listings.get(label)
            if listing is None:
                continue
            text, names = listing
            diff = compare(control_entries, entries_of(text), names)
            bound = bound or len(text) < len(control[0])
            report[label] = {"chars": len(text), **diff}
            print(f"{label}: 본문 {len(text):,}자, names {len(names)}개")
            for key, title in (
                ("shortened", "줄었다"),
                ("name_only", "이름만"),
                ("body_missing", "본문에 없다"),
                ("gone", "아예 없다"),
            ):
                values = diff[key]
                if isinstance(values, list) and values:
                    print(f"  {title} {len(values)}개: {', '.join(str(v) for v in values)}")
        if not bound:
            print("측정 아님: 대조보다 본문이 짧은 갈래가 없어 이 출처에서 비율을 읽었는지 모른다")
            unmeasured += 1
        report[control_label] = {"chars": len(control[0])}
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
                "probe": "skill_listing_budget",
                "claude": version.stdout.strip(),
                "variants": report,
                "unmeasured": unmeasured,
            },
            ensure_ascii=False,
        )
    )
    return 1 if unmeasured else 0


if __name__ == "__main__":
    sys.exit(main())
