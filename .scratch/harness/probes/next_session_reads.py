"""next-session 스킬 파일의 Read 를 길과 세션으로 가르고, 하루마다 합과 세션당 글자 수를 낸다
(harness 티켓 027).

재는 것. 토큰 장부(`tools/token_report.py` 의 `ledger/YYYY-MM.jsonl`) 세션 행의 `reads` 가운데
경로에 `/.claude/skills/next-session/` 이 든 Read 다. 나눈 뒤의 파일도 같은 폴더라 든다. 글자는
장부의 `chars`(모델이 받은 줄 번호 붙은 글의 글자 수)이고, 날은 Read 결과 기록의 시각을 `--tz` 로
옮긴 날이다. 장부는 메인 세션의 Read 만 적는다. 서브에이전트의 Read, Skill 도구로 실은 본문, 셸로
읽은 것(`grep`, `sed`)은 들지 않고, 실패한 Read(파일이 너무 커 거부된 것)도 들지 않는다.

길. 장부에 없는 값이라 세션 기록(`--projects` 아래 폴더마다의 `<세션 ID>.jsonl`, 같은 이름이
여럿이면 가장 큰 것)에서 그 Read 의 tool_use id 를 찾아 그 앞의 기록으로 가른다. 아래 차례로 처음
맞는 것이다.
- 고침: 그 세션이 어느 때든 next-session 폴더의 파일을 Edit·Write·NotebookEdit 로 고쳤다. 고치려고
  읽은 것이라 쓰임과 따로 센다(이 티켓과 harness 025 의 세션이 든다).
- 인계 훅: 마지막 사람 입력(user 기록의 `origin.kind` 가 `human`) 뒤, 그 Read 앞에 `hook_handoff` 의
  계기(`hook_additional_context` 첨부의 글에 `인계 문턱`)가 왔다. 작업 알림과 서브에이전트 보고는
  사람 입력이 아니라 턴을 끊지 않는다.
- 인계 받음: 장부의 세션 행이 `handoff` 다(첫 사람 입력이 `이어받을 상태: 인계:` 줄을 든 지시문).
  인계를 받은 세션이 남은 단계(봇 회차, 병합)를 보려고 연 것이다.
- 병합 뒤: 그 Read 앞에 main 을 합치는 명령(셸의 `git … merge`·`git … pull`, 앱의
  `sync_with_base_branch`)이 있었다. `CLAUDE.md` 환경 함정이 합친 뒤 바뀐 스킬을 Read 로 열게 한다.
- 그 밖: 위 넷에 들지 않는다.
- 기록 없음: 세션 기록이나 그 tool_use id 를 찾지 못했다. 장부의 합에는 들고 길은 모른다.

표지와 회차. Read 하나가 회차다. 세션 기록에서 그 Read 의 tool_use 를 찾은 회차만 길을 잰
측정이다(`tools/probe_kit.py` 의 `Rounds`). 기록 없음이 하나라도 있으면 종료 코드가 1 이다. 날마다의
합과 세션당 글자 수는 장부만으로 서므로 기록 없음도 든다.

절. 길마다 Read 결과 글에 든 `## ` 머리를 센다. 범위를 준 Read 가 절 가운데서 시작하면 그 절의
머리가 없어 세지 않는다. 그래서 이 수는 그 절을 읽은 Read 수의 아래 한계다.

해석의 갈래(티켓 027). 길의 몫이 절을 나누는 근거가 되려면 (가) 길마다 실제로 머리가 든 절이 달라야
하고 (나) 전체 Read(범위 없음)가 많은 길은 나눠도 줄지 않을 수 있다. 셋째 해석인 "한 번에 다 읽지
못해 범위를 나눠 거듭 열었다"는 범위 Read 의 `limit` 합이 파일 줄 수에 닿는 세션이 많을 때 선다.
이 프로브는 세션마다 범위 Read 수와 전체 Read 수를 함께 내 그 갈래를 가를 값을 준다.

사용:
    uv run --no-project python .scratch/harness/probes/next_session_reads.py \
        --first 2026-10-21 --last 2026-10-27 [--tz +09:00] [--ledger 폴더] [--projects 폴더]
읽기만 한다. 끝 줄은 결과 JSON 한 줄이다.

못 보는 것:
- 지워진 세션 기록. 지운 워크트리의 기록 폴더가 함께 사라진 세션은 기록 없음이다.
- 길의 까닭. 앞선 계기와 명령으로 가를 뿐 모델이 왜 열었는지는 모른다. 병합 뒤의 Read 가운데
  병합 절차를 미리 보려고 연 것과 스킬 사본이 낡아 연 것을 가르지 않는다.
- 한 Read 가 여러 길에 걸친 때. 차례에서 처음 맞는 하나로만 센다.
- 인계 계기를 받고도 넘기지 않고(인계하지 않는 때) 같은 턴에서 이어 간 세션. 그 턴의 뒤 Read 도
  인계 훅으로 센다(과대). 2026-10-21 `e2fb0e60` 세션은 계기 뒤 첫 Read 다음에 PR 직전 리뷰와 PR
  열기를 이어 가며 세 번 더 읽었고, 셋 다 인계 훅으로 셌다(`--list` 와 그 세션 기록의 글을 손으로
  맞댔다).
- 다른 세션이 보낸 인계 요청(주간 한도 등). 사람 입력이 아니라 턴을 끊지 않고, 계기도 아니라 앞선
  계기가 없으면 인계 받음·병합 뒤·그 밖으로 간다.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from tools.probe_kit import Rounds  # noqa: E402

FOLDER = "/.claude/skills/next-session/"
EDITS = frozenset({"Edit", "Write", "NotebookEdit", "MultiEdit"})
SHELLS = frozenset({"Bash", "PowerShell"})
HANDOFF_MARK = "인계 문턱"
MERGE = re.compile(r"\bgit\s+(?:(?:-C|-c)\s+\S+\s+|--no-pager\s+)*(?:merge|pull)(?![\w-])")
HEADER = re.compile(r"^\s*\d+\t(## .+?)\s*$", re.MULTILINE)
ROUTES = ("고침", "인계 훅", "인계 받음", "병합 뒤", "그 밖", "기록 없음")
GIT_TIMEOUT = 10


@dataclass(frozen=True)
class Read:
    session: str
    id: str
    at: datetime
    chars: int
    handoff_session: bool


@dataclass
class Seen:
    """세션 기록에서 Read 하나에 대해 찾은 것."""

    route: str
    ranged: bool
    headers: tuple[str, ...]


@dataclass
class Tally:
    reads: int = 0
    chars: int = 0
    sessions: set[str] = field(default_factory=set[str])
    full: int = 0
    headers: Counter[str] = field(default_factory=Counter[str])

    def add(self, read: Read, seen: Seen | None) -> None:
        self.reads += 1
        self.chars += read.chars
        self.sessions.add(read.session)
        if seen is not None:
            self.full += 0 if seen.ranged else 1
            self.headers.update(seen.headers)


def tz_of(text: str) -> timezone:
    match = re.fullmatch(r"([+-])(\d{2}):(\d{2})", text)
    if match is None:
        raise SystemExit(f"--tz 는 +09:00 꼴이어야 한다: {text}")
    sign = 1 if match.group(1) == "+" else -1
    return timezone(sign * timedelta(hours=int(match.group(2)), minutes=int(match.group(3))))


def main_checkout() -> Path:
    """git 공용 디렉터리의 부모. 장부는 주 체크아웃에만 있다(`.gitignore`)."""
    out = subprocess.run(
        ["git", "-C", str(ROOT), "rev-parse", "--path-format=absolute", "--git-common-dir"],
        capture_output=True,
        text=True,
        timeout=GIT_TIMEOUT,
        check=True,
    )
    return Path(out.stdout.strip()).parent


def _obj(value: object) -> dict[str, object]:
    return {str(k): v for k, v in value.items()} if isinstance(value, dict) else {}


def _list(value: object) -> list[object]:
    return list(value) if isinstance(value, list) else []


def _str(value: object) -> str:
    return value if isinstance(value, str) else ""


def ledger_reads(ledger: Path, first: date, last: date, tz: timezone) -> list[Read]:
    """장부의 세션 행에서 next-session 폴더의 Read. 같은 세션 행이 여럿이면 뒤의 것이다."""
    rows: dict[str, dict[str, object]] = {}
    for path in sorted(ledger.glob("[0-9][0-9][0-9][0-9]-[0-9][0-9].jsonl")):
        for line in path.read_text(encoding="utf-8").splitlines():
            if '"kind": "session"' not in line:
                continue
            row = _obj(json.loads(line))
            if row.get("kind") == "session":
                rows[_str(row.get("session"))] = row
    reads: list[Read] = []
    for session, row in rows.items():
        for item in _list(row.get("reads")):
            r = _obj(item)
            if FOLDER not in _str(r.get("path")).replace("\\", "/").lower():
                continue
            at = datetime.fromisoformat(_str(r.get("at")).replace("Z", "+00:00"))
            if not first <= at.astimezone(tz).date() <= last:
                continue
            chars = r.get("chars")
            reads.append(
                Read(
                    session,
                    _str(r.get("id")),
                    at,
                    chars if isinstance(chars, int) else 0,
                    row.get("handoff") is True,
                )
            )
    return reads


def transcripts(projects: Path, sessions: set[str]) -> dict[str, Path]:
    """세션 ID 마다 가장 큰 기록 파일. 폴더 바로 아래의 것만 본다(서브에이전트 기록은 아래 폴더)."""
    found: dict[str, Path] = {}
    for folder in projects.iterdir():
        if not folder.is_dir():
            continue
        for session in sessions:
            path = folder / f"{session}.jsonl"
            if path.is_file() and (
                session not in found or path.stat().st_size > found[session].stat().st_size
            ):
                found[session] = path
    return found


def _text_of(content: object) -> str:
    if isinstance(content, str):
        return content
    return "\n".join(_str(_obj(b).get("text")) for b in _list(content))


def _edits_folder(line: str) -> bool:
    """이 기록 줄이 메인 세션에서 next-session 폴더의 파일을 고친 도구 호출을 드는가."""
    try:
        record = _obj(json.loads(line))
    except ValueError:
        return False
    if record.get("type") != "assistant" or record.get("isSidechain") is True:
        return False
    for item in _list(_obj(record.get("message")).get("content")):
        block = _obj(item)
        tool_input = _obj(block.get("input"))
        target = (
            _str(tool_input.get("file_path")) or _str(tool_input.get("notebook_path"))
        ).replace("\\", "/")
        if block.get("type") == "tool_use" and _str(block.get("name")) in EDITS:
            if FOLDER in target.lower():
                return True
    return False


def scan(path: Path, wanted: dict[str, Read]) -> dict[str, Seen]:
    """세션 기록 하나를 차례로 훑어 `wanted` 의 Read 마다 길과 범위와 머리를 찾는다."""
    lines = path.read_text(encoding="utf-8", errors="replace").split("\n")
    edits = any(_edits_folder(line) for line in lines if "next-session" in line)
    handoff_turn = False
    merged = False
    uses: dict[str, tuple[str, bool]] = {}
    seen: dict[str, Seen] = {}
    for line in lines:
        if not line:
            continue
        try:
            record = _obj(json.loads(line))
        except ValueError:
            continue
        if record.get("isSidechain") is True:
            continue
        kind = record.get("type")
        if kind == "attachment":
            attachment = _obj(record.get("attachment"))
            if (
                attachment.get("type") == "hook_additional_context"
                and attachment.get("hookEvent") == "PostToolUse"
                and HANDOFF_MARK in json.dumps(attachment.get("content"), ensure_ascii=False)
            ):
                handoff_turn = True
            continue
        message = _obj(record.get("message"))
        if kind == "user":
            if _obj(record.get("origin")).get("kind") == "human":
                handoff_turn = False
            for item in _list(message.get("content")):
                block = _obj(item)
                tid = _str(block.get("tool_use_id"))
                if block.get("type") == "tool_result" and tid in uses:
                    route, ranged = uses.pop(tid)
                    text = _text_of(block.get("content"))
                    seen[tid] = Seen(route, ranged, tuple(HEADER.findall(text)))
            continue
        if kind != "assistant":
            continue
        for item in _list(message.get("content")):
            block = _obj(item)
            if block.get("type") != "tool_use":
                continue
            name = _str(block.get("name"))
            tool_input = _obj(block.get("input"))
            if name in SHELLS and MERGE.search(_str(tool_input.get("command"))):
                merged = True
            elif name.endswith("sync_with_base_branch"):
                merged = True
            tid = _str(block.get("id"))
            read = wanted.get(tid)
            if name != "Read" or read is None:
                continue
            if edits:
                route = "고침"
            elif handoff_turn:
                route = "인계 훅"
            elif read.handoff_session:
                route = "인계 받음"
            elif merged:
                route = "병합 뒤"
            else:
                route = "그 밖"
            ranged = "offset" in tool_input or "limit" in tool_input
            uses[tid] = (route, ranged)
    return seen


def _per_session(reads: list[Read]) -> list[int]:
    by: dict[str, int] = defaultdict(int)
    for r in reads:
        by[r.session] += r.chars
    return sorted(by.values())


def _line(label: str, reads: list[Read]) -> str:
    per = _per_session(reads)
    total = sum(per)
    if not per:
        return f"{label}: Read 0"
    return (
        f"{label}: Read {len(reads)}, 세션 {len(per)}, 글자 {total:,}, 세션당 평균 "
        f"{total // len(per):,}, 중앙값 {int(statistics.median(per)):,}, 최대 {per[-1]:,}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--first", required=True, type=date.fromisoformat)
    parser.add_argument("--last", required=True, type=date.fromisoformat)
    parser.add_argument("--tz", default="+09:00")
    parser.add_argument("--ledger", type=Path)
    parser.add_argument("--projects", type=Path, default=Path.home() / ".claude" / "projects")
    parser.add_argument("--list", action="store_true", help="Read 마다 세션·시각·글자·길을 찍는다")
    args = parser.parse_args()
    tz = tz_of(args.tz)
    ledger: Path = args.ledger or main_checkout() / ".scratch" / "token-report" / "ledger"
    reads = ledger_reads(ledger, args.first, args.last, tz)
    sessions = {r.session for r in reads}
    files = transcripts(args.projects, sessions)
    by_session: dict[str, dict[str, Read]] = defaultdict(dict)
    for r in reads:
        by_session[r.session][r.id] = r
    seen: dict[str, Seen] = {}
    for session, wanted in by_session.items():
        path = files.get(session)
        if path is not None:
            seen.update(scan(path, wanted))

    rounds = Rounds()
    routes: dict[str, Tally] = {name: Tally() for name in ROUTES}
    ranged_by_session: dict[str, list[bool]] = defaultdict(list)
    for r in reads:
        with rounds.round(f"{r.session[:8]} {r.id}") as current:
            found = seen.get(r.id)
            route = found.route if found is not None else "기록 없음"
            routes[route].add(r, found)
            if found is not None:
                ranged_by_session[r.session].append(found.ranged)
            current.mark(measured=found is not None, result=route)

    if args.list:
        for r in sorted(reads, key=lambda x: (x.session, x.at)):
            found = seen.get(r.id)
            route = found.route if found is not None else "기록 없음"
            ranged = "범위" if found is not None and found.ranged else "전체"
            when = r.at.astimezone(tz).strftime("%m-%d %H:%M")
            print(f"{r.session[:8]} {when} {r.chars:>6} {route} {ranged}")
    print(f"장부: {ledger}  기간: {args.first}~{args.last} ({args.tz})")
    print(_line("전체", reads))
    print("\n날마다")
    days: dict[date, list[Read]] = defaultdict(list)
    for r in reads:
        days[r.at.astimezone(tz).date()].append(r)
    for day in sorted(days):
        print(_line(f"  {day}", days[day]))
    print("\n길마다")
    for name in ROUTES:
        tally = routes[name]
        picked = [r for r in reads if (seen[r.id].route if r.id in seen else "기록 없음") == name]
        extra = f", 범위 없는 Read {tally.full}" if name != "기록 없음" else ""
        print(_line(f"  {name}", picked) + extra)
        for header, count in tally.headers.most_common():
            print(f"      {count:>4}  {header}")
    only_ranged = sum(1 for v in ranged_by_session.values() if all(v))
    with_full = sum(1 for v in ranged_by_session.values() if not all(v))
    multi_ranged = sum(1 for v in ranged_by_session.values() if all(v) and len(v) > 1)
    print(
        f"\n세션(기록 있음 {len(ranged_by_session)}): 범위 Read 만 {only_ranged}"
        f"(그 가운데 둘 이상 {multi_ranged}), 범위 없는 Read 가 하나라도 {with_full}"
    )
    # 측정 아닌 회차는 모두 기록 없음이라 회차마다 찍지 않고 세션 수로 줄인다.
    print("\n" + "\n".join(rounds.summary().splitlines()[:2]))
    missing = {r.session for r in reads if r.id not in seen}
    print(f"측정 아님의 세션 {len(missing)}: 세션 기록이나 그 Read 의 tool_use 를 찾지 못했다")
    result = {
        "first": args.first.isoformat(),
        "last": args.last.isoformat(),
        "tz": args.tz,
        "reads": len(reads),
        "sessions": len(sessions),
        "chars": sum(r.chars for r in reads),
        "days": {
            d.isoformat(): {
                "reads": len(v),
                "sessions": len({r.session for r in v}),
                "chars": sum(r.chars for r in v),
            }
            for d, v in sorted(days.items())
        },
        "routes": {
            name: {"reads": t.reads, "sessions": len(t.sessions), "chars": t.chars, "full": t.full}
            for name, t in routes.items()
        },
        "measured": len(rounds.measured),
        "unmeasured": len(rounds.unmeasured),
        "at": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    print(json.dumps(result, ensure_ascii=False))
    return rounds.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
