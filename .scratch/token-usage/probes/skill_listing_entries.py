"""세션 기록에서 첫 스킬 목록에 무엇이 실렸는지 출처별로 꺼낸다(ADR 0033 이력 2026-10-20).

측정 때 프로젝트 설정에 둔 `enabledPlugins`(`slack`, `cowork-plugin-management@synced`)와
`skillOverrides`(`anthropic-skills:<이름>`)가 새 세션의 스킬 목록에서 그 항목을 빼는지 봤다. 먹은
`slack`만 `.claude/settings.json`에 남았다. 기록
(`~/.claude/projects/<폴더>/<세션>.jsonl`)에서 첫 모델 호출 전의 `skill_listing` 첨부를 모두 읽는다.
그 첨부가 모델에게 간 스킬 목록이고, `tools/token_report.py`의 `start_parts_of`도 같은 첨부를 같은
자리에서 센다. 출처는 그 파일의 `skill_sources_of`처럼 `- 출처:이름` 줄 머리로 가르고, 출처가 없는
`- ` 줄은 프로젝트·사용자 레벨(`~/.claude/skills`의 `git-*` 등)·내장이다.

항목마다 설명이 남았는지(`- 이름: 설명`)와 이름만 남았는지(`- 이름`)를 가르고, 첨부의 `names` 수를
본문 항목 수와 함께 찍는다. 두 수가 같으면 예산이 항목을 통째로 빼지 않은 것이라, 목록에 없는 항목은
설정이 뺀 것으로 읽는다(공식 skills 문서는 목록이 늘 모든 스킬의 이름을 담는다고 적는다). 첫 모델
호출 뒤에 다시 온 `skill_listing` 첨부는 시각과 글자 수, `names` 수를 찍는다.

표지 셋이 모두 있어야 측정이다. 첫 모델 호출 전에 `skill_listing` 첨부가 있다. 기록의 첫 `cwd`가
`--cwd`로 준 폴더와 같다(`normcase`·`normpath`로 견준다). `anthropic-skills:built-in-browser`가
목록에 있다. 셋째는 끄지 않고 남기는 항목이라, 다른 `anthropic-skills:*`가 없을 때 "그 출처가 아예
실리지 않았다"는 해석과 "`skillOverrides`가 하나씩 뺐다"는 해석을 가르는 양성 대조다. 하나라도
없으면 그 까닭을 찍고 1로 끝난다. `jira-*`(사용자 레벨 스킬, 프로젝트 설정이 이미 끈다)가 없는 것은
그 세션이 프로젝트 설정의 `skillOverrides`를 읽었다는 대조로 함께 찍는다.

못 보는 것: 기록에 남지 않고 모델에게만 간 목록이 있다면 보지 못한다. 첫 모델 호출 뒤에 다시 온
첨부는 항목을 가르지 않고, 왜 다시 왔는지(설정을 다시 읽었는지, 압축 뒤에 다시 붙였는지)도 모른다.

돌리는 법: 저장소 루트에서 `uv run python .scratch/token-usage/probes/skill_listing_entries.py
<기록.jsonl> --cwd <세션의 작업 폴더>`. 모델을 부르지 않는다.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

WATCHED = ("anthropic-skills", "slack", "cowork-plugin-management")
CONTROL = "anthropic-skills:built-in-browser"
OTHER = "(프로젝트·사용자·내장)"
_ENTRY = re.compile(r"- ([\w.-]+(?::[\w.-]+)?)(?::\s|:$|$)")


def entry_of(line: str) -> str | None:
    """`- 출처:이름: 설명` 줄이면 `출처:이름`, `- 이름: 설명` 줄이면 `이름`, 항목이 아니면 None."""
    if not line.startswith("- "):
        return None
    m = _ENTRY.match(line)
    return m.group(1) if m else None


def source_of(entry: str) -> str:
    return entry.split(":", 1)[0] if ":" in entry else OTHER


def same_dir(a: str, b: str) -> bool:
    return os.path.normcase(os.path.normpath(a)) == os.path.normcase(os.path.normpath(b))


def read_records(path: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(rec, dict):
                records.append(rec)
    return records


def is_model_call(rec: dict[str, object]) -> bool:
    message = rec.get("message")
    return isinstance(message, dict) and isinstance(message.get("usage"), dict)


def listing_attachment(rec: dict[str, object]) -> dict[str, object] | None:
    if rec.get("type") != "attachment":
        return None
    attachment = rec.get("attachment")
    if not isinstance(attachment, dict) or attachment.get("type") != "skill_listing":
        return None
    return attachment


def listing_text(rec: dict[str, object]) -> str | None:
    attachment = listing_attachment(rec)
    if attachment is None:
        return None
    content = attachment.get("content")
    return content if isinstance(content, str) else ""


def names_count(rec: dict[str, object]) -> int | None:
    """첨부의 `names` 수. 그 키가 목록이 아니면 None."""
    attachment = listing_attachment(rec)
    names = attachment.get("names") if attachment is not None else None
    return len(names) if isinstance(names, list) else None


def has_description(line: str) -> bool:
    """항목 줄에 이름 뒤 설명이 있는지. `- 이름`과 `- 이름:`은 이름만 남은 것이다."""
    entry = entry_of(line)
    return entry is not None and line[2 + len(entry) :].lstrip(":").strip() != ""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("transcript", type=Path)
    parser.add_argument("--cwd", required=True, help="그 세션이 일한 폴더")
    args = parser.parse_args()
    records = read_records(args.transcript)
    first_cwd = next((r["cwd"] for r in records if isinstance(r.get("cwd"), str)), None)
    version = next((r["version"] for r in records if isinstance(r.get("version"), str)), None)
    start: list[str] = []
    start_names = 0
    later: list[str] = []
    called = False
    for rec in records:
        if is_model_call(rec):
            called = True
        text = listing_text(rec)
        if text is None:
            continue
        n_names = names_count(rec)
        if called:
            stamp = rec.get("timestamp")
            names_part = "names 없음" if n_names is None else f"names {n_names}개"
            later.append(f"{stamp}: {len(text):,}자, {names_part}")
        else:
            start.append(text)
            start_names += n_names or 0
    entries: list[str] = []
    name_only: list[str] = []
    chars: dict[str, int] = {}
    for text in start:
        source = OTHER
        for line in text.splitlines():
            entry = entry_of(line)
            if entry is not None:
                entries.append(entry)
                source = source_of(entry)
                if not has_description(line):
                    name_only.append(entry)
            chars[source] = chars.get(source, 0) + len(line) + 1
    print(f"기록 {args.transcript.name}, cwd {first_cwd}, claude {version}")
    print(f"첫 모델 호출 전 skill_listing 첨부 {len(start)}개, 그 뒤 {len(later)}개")
    for line in later:
        print(f"  그 뒤 {line}")
    print(f"첫 목록 합 {sum(chars.values()):,}자, 항목 {len(entries)}개, names {start_names}개")
    for source, n in sorted(chars.items(), key=lambda kv: -kv[1]):
        print(f"  {source}: {n:,}자")
    described = len(entries) - len(name_only)
    print(f"설명이 남은 항목 {described}개, 이름만 남은 항목 {len(name_only)}개")
    print(f"  이름만: {', '.join(name_only) or '-'}")
    for source in WATCHED:
        names = [e for e in entries if source_of(e) == source]
        print(f"{source} 항목 {len(names)}개: {', '.join(names) or '-'}")
    jira = [e for e in entries if e.startswith("jira-")]
    print(f"jira-* 항목 {len(jira)}개(대조, 프로젝트 설정이 끈다): {', '.join(jira) or '-'}")
    reasons: list[str] = []
    if not start:
        reasons.append("첫 모델 호출 전 skill_listing 첨부가 없다")
    if first_cwd is None or not same_dir(first_cwd, args.cwd):
        reasons.append(f"기록의 cwd가 {args.cwd}가 아니다")
    if CONTROL not in entries:
        reasons.append(f"양성 대조 {CONTROL}가 목록에 없다")
    for reason in reasons:
        print(f"측정 아님: {reason}")
    return 1 if reasons else 0


if __name__ == "__main__":
    sys.exit(main())
