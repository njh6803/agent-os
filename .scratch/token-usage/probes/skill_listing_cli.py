"""`skillOverrides`가 동기화된 스킬(`anthropic-skills:*`)을 CLI 세션의 목록에서 빼는지 잰다.

ADR 0033 이력 2026-10-20의 근거다. 공식 skills 문서는 `skillOverrides`가 플러그인 스킬에는 먹지
않는다고만 적고, 동기화된 스킬에 먹는지는 적지 않았다(2026-10-20 서브에이전트가 문서를 읽었다).

갈래 둘을 저장소 밖 임시 폴더에서 `claude -p`(haiku) 한 턴으로 띄운다. A는 프로젝트 설정이 없고,
B는 `skillOverrides`만 둔 `.claude/settings.json`을 둔다. 그 값은 `--settings`로 준 파일의
`skillOverrides`이고, 주지 않으면 2026-10-20 실행 때 프로젝트 설정에 있던 끄는 키
열여섯(`MEASURED_OFF`, `anthropic-skills:*` 가운데 `built-in-browser`를 뺀 전부)이다. 먹지 않아 그
키를 프로젝트 설정에서 뺐으므로 기본값을 그 파일에서 읽지 않는다. 끄는 `anthropic-skills:*` 키가
하나도 없으면 측정이 아니다. 훅은 옮기지 않는다. 설정 출처는 `project,local`로 고정한다. 이
기계의 사용자 설정은 Stop 훅으로 턴마다 Slack에 알림을 보내기 때문이다
(`.scratch/kickoff-auto-flow/probes/skill_live/run.py` 독스트링). 그래서 사용자 설정의
`enabledPlugins`도 실리지 않아 플러그인 스킬(`slack:*` 등)은 두 갈래 모두 없고, 이 프로브는
`enabledPlugins`를 재지 않는다.

갈래마다 stream-json의 `system/init`에서 세션 ID와 `skills`를 읽고, 그 세션의 기록
(`~/.claude/projects/*/<세션 ID>.jsonl`)을 같은 폴더의 `skill_listing_entries.py`로 읽어 모델에게 간
첫 스킬 목록의 항목을 꺼낸다. 표지는 `system/init`과 `result` 이벤트가 있고 기록에 첫 모델 호출 전
`skill_listing` 첨부가 있는 것이다. 양성 대조는 셋이다. A의 목록에 `anthropic-skills:*`가 있어야
이 설정 출처에서도 동기화된 스킬이 실린다는 것이 서고, 끄지 않은 `CONTROL`이 A와 B의 목록에 모두
있어야 B에서 빠진 항목이 그 출처 전체가 아니라 하나씩 빠진 것이다(A에 없으면 그 대조를 할 수 없어
측정 아님으로 센다). 그리고 두 갈래의 `.claude/skills`에 같은 프로젝트 스킬 `PROBE_SKILL`을 두고 B의
`skillOverrides`에서만 끈다. 그 스킬이 A의 목록에 있고 B의 목록에 없어야 B가 프로젝트 설정의
`skillOverrides`를 읽은 것이다. 이 대조가 없으면 B에 `anthropic-skills:*`가 남은 결과를 "먹지
않는다"와 "B가 그 설정을 읽지 않았다"로 가르지 못한다(PR #320의 CodeRabbit 지적). 표지나 대조가
하나라도 없으면 1로 끝난다.

못 보는 것: 데스크톱 앱 세션. 앱은 동기화 폴더 밖의 `anthropic-skills:*`(2026-10-20 이 PC에서
`consolidate-memory`·`explain-usage`·`schedule`·`setup-claude`)도 싣는데 CLI에는 없다. 그것은 앱
세션의 기록을 `skill_listing_entries.py`로 읽어 본다.

돌리는 법: 저장소 루트에서 `uv run python .scratch/token-usage/probes/skill_listing_cli.py`.
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

import skill_listing_entries as entries_probe

PROMPT = "도구를 쓰지 않고 '끝'이라고만 답한다."
TIMEOUT_SECONDS = 240
CONTROL = entries_probe.CONTROL
PROBE_SKILL = "skill-listing-probe-control"
SOURCE = "anthropic-skills"
MEASURED_OFF = tuple(
    f"{SOURCE}:{name}"
    for name in (
        "chrome-browser",
        "computer-use",
        "consolidate-memory",
        "deep-research",
        "docs",
        "docx",
        "explain-usage",
        "google-workspace",
        "import-memory",
        "morning",
        "pdf",
        "pptx",
        "schedule",
        "setup-claude",
        "skill-creator",
        "xlsx",
    )
)


def stream_events(path: Path) -> list[dict[str, object]]:
    events: list[dict[str, object]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def transcript_of(session_id: str) -> Path | None:
    found = sorted((Path.home() / ".claude" / "projects").glob(f"*/{session_id}.jsonl"))
    return found[0] if found else None


def start_entries(transcript: Path) -> list[str] | None:
    """기록의 첫 모델 호출 전 `skill_listing` 첨부의 항목. 첨부가 없으면 None."""
    texts: list[str] = []
    for rec in entries_probe.read_records(transcript):
        if entries_probe.is_model_call(rec):
            break
        text = entries_probe.listing_text(rec)
        if text is not None:
            texts.append(text)
    if not texts:
        return None
    out: list[str] = []
    for text in texts:
        for line in text.splitlines():
            entry = entries_probe.entry_of(line)
            if entry is not None:
                out.append(entry)
    return out


def command_for(claude: str) -> list[str]:
    """갈래 하나를 띄우는 명령. 같은 폴더의 `skill_listing_budget.py`도 쓴다."""
    return [
        claude,
        "-p",
        PROMPT,
        "--output-format",
        "stream-json",
        "--verbose",
        "--model",
        "haiku",
        "--strict-mcp-config",
        "--setting-sources",
        "project,local",
        "--max-turns",
        "1",
    ]


def run_variant(claude: str, cwd: Path, log: Path) -> tuple[list[str], list[str] | None, list[str]]:
    """(init 의 skills, 기록의 첫 목록 항목, 측정이 아닌 까닭)."""
    reasons: list[str] = []
    with log.open("w", encoding="utf-8") as out:
        try:
            subprocess.run(
                command_for(claude),
                cwd=cwd,
                stdin=subprocess.DEVNULL,
                stdout=out,
                stderr=subprocess.DEVNULL,
                timeout=TIMEOUT_SECONDS,
                check=False,
            )
        except subprocess.TimeoutExpired:
            reasons.append(f"{TIMEOUT_SECONDS}초 안에 끝나지 않았다")
    events = stream_events(log)
    init = next(
        (e for e in events if e.get("type") == "system" and e.get("subtype") == "init"), None
    )
    if init is None:
        reasons.append("system/init 이벤트가 없다")
        return [], None, reasons
    if not any(e.get("type") == "result" for e in events):
        reasons.append("result 이벤트가 없다")
    raw_skills = init.get("skills")
    skills = [str(s) for s in raw_skills] if isinstance(raw_skills, list) else []
    session_id = init.get("session_id")
    transcript = transcript_of(session_id) if isinstance(session_id, str) else None
    if transcript is None:
        reasons.append(f"세션 {session_id}의 기록을 찾지 못했다")
        return skills, None, reasons
    listed = start_entries(transcript)
    if listed is None:
        reasons.append(f"기록 {transcript.name}에 첫 모델 호출 전 skill_listing 첨부가 없다")
    return skills, listed, reasons


def overrides_of(settings: Path) -> dict[str, object]:
    data = json.loads(settings.read_text(encoding="utf-8"))
    overrides = data.get("skillOverrides") if isinstance(data, dict) else None
    if not isinstance(overrides, dict):
        raise SystemExit(f"{settings}에 skillOverrides 객체가 없다")
    return overrides


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--settings", type=Path, default=None, help="skillOverrides를 옮길 설정 파일"
    )
    parser.add_argument("--out", type=Path, default=None, help="stream-json 원본을 남길 폴더")
    args = parser.parse_args()
    claude = shutil.which("claude")
    if claude is None:
        print("claude CLI를 찾지 못했다")
        return 2
    if args.settings is None:
        overrides: dict[str, object] = dict.fromkeys(MEASURED_OFF, "off")
    else:
        overrides = overrides_of(args.settings)
    off = sorted(k for k, v in overrides.items() if k.startswith(f"{SOURCE}:") and v == "off")
    if not off:
        print(f"측정 아님: 끄는 {SOURCE}:* 키가 없어 B가 A와 같다")
        return 1
    unmeasured = 0
    results: dict[str, list[str] | None] = {}
    with tempfile.TemporaryDirectory(prefix="skill-cli-", ignore_cleanup_errors=True) as scratch:
        out_dir = args.out or Path(scratch) / "logs"
        out_dir.mkdir(parents=True, exist_ok=True)
        for variant in ("A", "B"):
            cwd = Path(scratch) / variant
            skill_dir = cwd / ".claude" / "skills" / PROBE_SKILL
            skill_dir.mkdir(parents=True)
            (skill_dir / "SKILL.md").write_text(
                f"---\nname: {PROBE_SKILL}\ndescription: 대조용 프로젝트 스킬\n---\n\n대조용\n",
                encoding="utf-8",
            )
            if variant == "B":
                settings = {"skillOverrides": {**overrides, PROBE_SKILL: "off"}}
                (cwd / ".claude" / "settings.json").write_text(
                    json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8"
                )
            skills, listed, reasons = run_variant(claude, cwd, out_dir / f"{variant}.jsonl")
            results[variant] = listed
            in_init = [s for s in skills if s.startswith(f"{SOURCE}:")]
            in_listing = [e for e in listed or [] if e.startswith(f"{SOURCE}:")]
            counts = f"init의 {SOURCE} {len(in_init)}개, 첫 목록의 {SOURCE} {len(in_listing)}개"
            print(f"{variant}: {counts}")
            print(f"  첫 목록: {', '.join(in_listing) or '-'}")
            for reason in reasons:
                print(f"  측정 아님: {reason}")
            unmeasured += bool(reasons)
    a = [e for e in results.get("A") or [] if e.startswith(f"{SOURCE}:")]
    b = [e for e in results.get("B") or [] if e.startswith(f"{SOURCE}:")]
    if results.get("A") is not None and not a:
        print(f"측정 아님: A의 첫 목록에 {SOURCE}:*가 없어 이 설정 출처에서 실리는지 모른다")
        unmeasured += 1
    elif results.get("A") is not None and CONTROL not in a:
        print(f"측정 아님: A의 첫 목록에 {CONTROL}가 없어 B의 빠짐을 하나씩 뺀 것과 가르지 못한다")
        unmeasured += 1
    if results.get("B") is not None and CONTROL in a and CONTROL not in b:
        print(f"측정 아님: B의 첫 목록에 끄지 않은 {CONTROL}가 없다")
        unmeasured += 1
    listed_a, listed_b = results.get("A"), results.get("B")
    if listed_a is not None and listed_b is not None:
        if PROBE_SKILL not in listed_a or PROBE_SKILL in listed_b:
            in_a = "있음" if PROBE_SKILL in listed_a else "없음"
            in_b = "있음" if PROBE_SKILL in listed_b else "없음"
            where = f"A {in_a}, B {in_b}"
            print(
                f"측정 아님: 프로젝트 스킬 {PROBE_SKILL}가 A에만 있지 않아({where}) "
                "B가 skillOverrides를 읽었는지 모른다"
            )
            unmeasured += 1
    left = [name for name in off if name in b]
    gone = [name for name in off if name in a and name not in b]
    print(f"끈 {len(off)}개 가운데 A에 있고 B에서 빠진 것 {len(gone)}개, B에 남은 것 {len(left)}개")
    if left:
        print(f"  B에 남은 것: {', '.join(left)}")
    version = subprocess.run(
        [claude, "--version"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=60,
    )
    print(f"claude {version.stdout.strip()}, 측정이 아닌 것 {unmeasured}")
    return 1 if unmeasured else 0


if __name__ == "__main__":
    sys.exit(main())
