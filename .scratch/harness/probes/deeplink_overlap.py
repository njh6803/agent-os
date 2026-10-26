"""`tools/open_session.ps1 -Action send` 의 열기마다, 자기 딥링크 뒤 보내기 전에 남의 딥링크가
왔는지(겹침)를 앱의 로그로 가르고, 열기의 결과(보냈다, 겹침의 증상으로 멈췄다, 다른 까닭으로
멈췄다)와 맞댄다(대기열 360, harness 티켓 014).

왜. 두 세션의 `send` 가 몇 초 사이로 딥링크를 쏘면 뒤의 딥링크가 앞 세션의 새 세션 화면 입력창을 제
글로 덮어, 앞 세션이 지시문이 든 입력창을 찾지 못하거나(`입력창 을(를) 찾지 못했다`) 모델을 고르는
사이 지시문이 바뀌었다며(`지시문이 바뀌었다`) 멈춘다고 세 일지가
보았다(2026-10-19-13·2026-10-21-06·2026-10-23-14). 셋 다 앱 로그로 가르지 않았다. 이 프로브가
가른다.

무엇을 맞대나.
- 열기. 이 계정의 트랜스크립트(`~/.claude/projects/*/*.jsonl`)에서, 명령에 `open_session.ps1` 과
  `-Action send` 가 든 PowerShell·Bash 호출의 결과를 읽는다. 결과의 `fired=` 가 쏜 시각(로컬),
  `sent=` 가 보낸 시각이다. `fired=` 는 시각만 찍으므로 날짜는 그 결과를 적은 기록의 시각(UTC)을
  로컬로 바꿔 붙이고, 쏜 시각이 기록보다 늦으면 하루 앞으로 돌린다. 같은 결과가 여러 트랜스크립트에
  실리면(갈라진 세션) 쏜 시각으로 하나만 센다. 여기에 대기열 360 의 세 회차를 일지가 적은 시각으로
  이름 붙여 더한다(`NAMED`). 셋째는 이 계정의 트랜스크립트에서 찾지 못했다. 트랜스크립트에도 있으면
  거기서 읽은 결과를 쓴다.
- 딥링크. 앱의 로그(`main.log` 와 돌림 파일 `main1.log`~, MSIX 설치와 일반 설치의 두 폴더)에서 두
  번째 인스턴스의 기동을 딥링크로 센다. 2026-10-15 까지의 판은 `Not main instance` 를 찍었고(일지
  2026-09-30-06), 지금 판은 제 기동 줄 `Starting app {` 과 몇 초 뒤
  `Quit requested before 'ready'; not creating the main window` 만 남긴다(2026-10-26 에 지금의
  로그를 손으로 봤다. 18:24 에 MSIX 로그 폴더를 `Select-String` 으로 세니 `Not main instance` 0 줄,
  `Starting app {` 796 줄, 끝내기 줄 792 줄이었다). 주 프로세스의 기동도 `Starting app {` 이라
  끝내기 줄과 10 초 안에 짝지은 기동만 센다.
- 세션 시작. `Starting local session <id> in <폴더>` 줄. 보고에 함께 찍는다(판정에는 쓰지 않는다).

판정. 표지는 자기 딥링크다. 쏜 시각의 초부터 5 초 안의 첫 두 번째 인스턴스를 자기 딥링크로 보고,
없으면 그 회차는 측정이 아니다(로그에 이 열기가 보이지 않는다). 겹침은 자기 딥링크 뒤, 보내기 전에
온 다른 두 번째 인스턴스다. 보낸 열기는 `sent=` 의 초 전까지 본다(보낸 뒤 기본값을 되돌리는 표지
딥링크가 같은 초에 올 수 있어 그 초는 뺀다). 멈춘 열기는 결과를 적은 기록의 시각까지 본다(멈춘
뒤에는 이 스크립트가 쏘지 않는다). 기록의 시각을 모르는 이름 붙은 회차는 자기 딥링크 뒤 30 초까지
본다(어림이다). 이 기준은 세 회차의 로그를 손으로 본 뒤에, 대조군(나머지 열기)을 돌리기 전에 정했다.
그 차례는 이 일을 한 세션의 기록이고, 판정 정의를 해시로 고정한 사전 등록은 아니다.

해석의 갈래. 겹침이 멈춤의 까닭이라면 (가) 증상 멈춤에는 겹침이 있고 (나) 보낸 열기에는 대개 겹침이
없다. (나)가 없으면, 곧 보낸 열기에도 겹침이 흔하면 겹침은 멈춤을 설명하지 못한다. 다른 해석은 그때
PC 가 바빠 새 세션 화면이 늦게 섰다는 것이다. 그 해석이면 겹침 없이 증상으로 멈춘 열기와 겹치고도
보낸 열기가 나와야 한다(표의 `증상 멈춤/겹침 없음` 과 `보냄/겹침`). 바쁨이 겹침과 함께 오는지(여러
세션이 함께 돌 때)는 가르지 않는다. 결과 표가 이 칸들을 센다. 입력창에 든 글은 재지 않으므로, 뒤의
딥링크가 앞 열기의 입력창을 덮었다는 것은 이 동시 발생에서 읽은 것이다.

열기의 길이. 끝 두 줄은 쏘고 보내기까지(`fired=` 에서 `sent=`)와 호출 전체(그 호출을 적은 기록부터
결과를 적은 기록까지. 훅과 허락을 기다린 시간도 든다)의 중앙값·최대와 20·60·120 초를 넘은 수다. 로그
밖의 열기도 센다. `tools/open_session.ps1` 의 `-LockTimeoutSec` 와, `open-session` 스킬이 PowerShell
도구에 주는 제한의 근거다.

못 보는 것.
- 남의 딥링크가 다른 세션의 `send` 인지 사람의 클릭인지. 앱을 다시 켜려는 클릭도 두 번째 인스턴스다.
  보고의 세션 시작 줄(겹친 딥링크 몇 초 뒤 같은 폴더에서 선 세션)이 `send` 의 모양인지 사람이 본다.
- 1 초 안의 차례. 로그의 시각이 초 단위라 같은 초의 두 딥링크는 어느 쪽이 자기 것인지 가르지 못한다.
- 이 계정 밖의 트랜스크립트(다른 계정 폴더)에 남은 열기. 그 열기의 딥링크는 남의 딥링크로만 보인다.
- 로그가 없는 때의 열기. 어느 로그 파일의 첫 줄과 끝 줄 사이에도 들지 않는 열기(돌림 파일 밖으로
  밀린 것, 일반 설치의 옛 로그와 MSIX 로그 사이의 빈 기간에 든 것)는 회차로 세지 않고 수만 찍는다.
- 자기 줄이 빠진 회차의 남의 딥링크. 자기 딥링크의 줄이 로그에 없고 그 5 초 안에 남의 딥링크가
  있으면 그것을 자기 것으로 잡아, 측정 아님이 아니라 측정으로 센다.

쓰임: 저장소 루트에서 `uv run python .scratch/harness/probes/deeplink_overlap.py`. 읽기만 한다.
`--until "YYYY-MM-DD HH:MM"` 을 주면 그 로컬 시각까지 쏜 열기만 세어, 뒤의 열기가 늘어도 같은 수가
난다 (트랜스크립트와 로그가 남아 있는 동안). 이번 열기의 겹침을 볼 때는 출력에서 그 열기의 `fired=`
시각으로 시작하는 줄의 `남의 [...]` 를 본다. 측정 아닌 회차가 하나라도 있으면 종료 코드가 1 이다.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from tools.probe_kit import Rounds  # noqa: E402

LOG_LINE = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d) \[\w+\] (.*)$")
SESSION = re.compile(r"^Starting local session (\S+) in (.*)$")
FIRED = re.compile(r"fired=(\d\d:\d\d:\d\d\.\d{3})")
SENT = re.compile(r"sent=(\d\d:\d\d:\d\d\.\d{3})")
PAIR_WINDOW = timedelta(seconds=10)
OWN_WINDOW = timedelta(seconds=5)
NAMED_SPAN = timedelta(seconds=30)

# 결과 글의 문구로 가르는 멈춤의 갈래. 겹침이 내리라 본 증상은 앞의 둘이다.
SYMPTOMS = {
    "입력창-없음": "이 든 입력창 을(를) 찾지 못했다",
    "지시문-바뀜": "모델을 고르는 사이 입력창의 지시문이 바뀌었다",
}
OTHER_STOPS = {
    "화면-없음": "새 세션 화면 을(를) 찾지 못했다",
    "held": "held=",
    "폴더": "새 세션 화면의 폴더가",
    "폴더-못읽음": "폴더 경로를 찾지 못했다",
    "신뢰-폴더": "신뢰 대화상자의 폴더가",
}

# 대기열 360 의 세 회차. (쏜 시각, 일지가 적은 멈춤, 출처)
NAMED = [
    ("2026-10-19 11:50:25.635", "입력창-없음", "일지 2026-10-19-13 인계 못함"),
    ("2026-10-21 15:03:16.129", "지시문-바뀜", "일지 2026-10-21-06 인계 (커밋 뒤)"),
    ("2026-10-23 03:50:39.518", "지시문-바뀜", "일지 2026-10-23-14 인계 (커밋 뒤)"),
]


@dataclass(frozen=True)
class Send:
    fired: datetime
    stop: str  # "보냄" 이거나 멈춤의 갈래
    sent: datetime | None
    recorded: datetime | None  # 결과를 적은 기록의 로컬 시각. 이름 붙은 회차만 None 일 수 있다
    source: str
    called: datetime | None = None  # 그 호출(tool_use)을 적은 기록의 로컬 시각


@dataclass(frozen=True)
class Timeline:
    links: list[datetime]
    sessions: list[tuple[datetime, str]]
    # 로그 파일마다 첫 줄과 끝 줄의 시각. 일반 설치의 옛 로그와 MSIX 설치의 로그 사이에 빈 기간이
    # 있어 전체의 처음과 끝으로는 그 기간의 열기를 로그 안으로 잘못 센다.
    ranges: list[tuple[datetime, datetime]]

    def covers(self, at: datetime) -> bool:
        return any(first <= at <= last for first, last in self.ranges)


def log_dirs() -> list[Path]:
    packages = Path(os.environ["LOCALAPPDATA"]) / "Packages"
    dirs = [p / "LocalCache" / "Local" / "Claude" / "logs" for p in packages.glob("Claude_*")]
    dirs.append(Path(os.environ["APPDATA"]) / "Claude" / "logs")
    return [d for d in dirs if d.is_dir()]


def read_timeline() -> Timeline:
    boots: list[datetime] = []
    quits: list[datetime] = []
    links: list[datetime] = []
    sessions: list[tuple[datetime, str]] = []
    ranges: list[tuple[datetime, datetime]] = []
    for directory in log_dirs():
        for path in sorted(directory.glob("main*.log")):
            seen: list[datetime] = []
            with path.open(encoding="utf-8", errors="replace") as lines:
                for line in lines:
                    match = LOG_LINE.match(line)
                    if not match:
                        continue
                    at = local(match.group(1), "%Y-%m-%d %H:%M:%S")
                    message = match.group(2)
                    seen.append(at)
                    if message.startswith("Starting app {"):
                        boots.append(at)
                    elif message.startswith("Quit requested before 'ready'"):
                        quits.append(at)
                    elif "Not main instance" in message:
                        links.append(at)
                    elif session := SESSION.match(message):
                        sessions.append((at, f"{session.group(1)} {session.group(2).strip()}"))
            if seen:
                ranges.append((min(seen), max(seen)))
    if not ranges:
        raise SystemExit("앱의 로그 줄을 하나도 읽지 못했다. 로그 폴더를 본다")
    # 끝내기 줄마다 그 앞 10 초 안의 짝 없는 기동 가운데 가장 늦은 것과 짝짓는다. 짝 없는 기동은 주
    # 프로세스다.
    pending = sorted(boots)
    for quit_at in sorted(quits):
        candidates = [b for b in pending if b <= quit_at and quit_at - b <= PAIR_WINDOW]
        if candidates:
            boot = candidates[-1]
            pending.remove(boot)
            links.append(boot)
    return Timeline(sorted(links), sorted(sessions), sorted(ranges))


def text_of(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                text = item.get("text")
                if isinstance(text, str):
                    parts.append(text)
        return "\n".join(parts)
    return ""


def classify(text: str) -> str:
    if SENT.search(text):
        return "보냄"
    for name, phrase in {**SYMPTOMS, **OTHER_STOPS}.items():
        if phrase in text:
            return name
    return "다른-멈춤"


def local(text: str, form: str) -> datetime:
    """로그와 `fired=` 의 시각은 이 PC 의 로컬 시각이다."""
    return datetime.strptime(text, form).astimezone()


def at_local(day: datetime, clock: str) -> datetime:
    return local(f"{day:%Y-%m-%d} {clock}", "%Y-%m-%d %H:%M:%S.%f")


def is_send_call(item: object) -> str | None:
    if not isinstance(item, dict) or item.get("type") != "tool_use":
        return None
    command = item.get("input", {})
    command = command.get("command") if isinstance(command, dict) else None
    if isinstance(command, str) and "open_session.ps1" in command and "-Action send" in command:
        ident = item.get("id")
        return ident if isinstance(ident, str) else None
    return None


def read_sends() -> list[Send]:
    found: dict[datetime, Send] = {}
    for path in (Path.home() / ".claude" / "projects").glob("*/*.jsonl"):
        try:
            raw = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "open_session.ps1" not in raw:
            continue
        calls: dict[str, datetime | None] = {}
        for line in raw.splitlines():
            if '"tool_use"' in line and "open_session.ps1" in line:
                record = json.loads(line)
                content = record.get("message", {}).get("content", [])
                stamp = record.get("timestamp")
                called = stamped(stamp) if isinstance(stamp, str) else None
                for item in content if isinstance(content, list) else []:
                    if ident := is_send_call(item):
                        calls[ident] = called
            elif "fired=" in line and '"tool_result"' in line:
                record = json.loads(line)
                content = record.get("message", {}).get("content", [])
                for item in content if isinstance(content, list) else []:
                    if not isinstance(item, dict) or item.get("tool_use_id") not in calls:
                        continue
                    text = text_of(item.get("content"))
                    fired = FIRED.search(text)
                    stamp = record.get("timestamp")
                    if not fired or not isinstance(stamp, str):
                        continue
                    recorded = stamped(stamp)
                    fired_at = at_local(recorded, fired.group(1))
                    if fired_at > recorded:
                        fired_at -= timedelta(days=1)
                    sent = SENT.search(text)
                    sent_at = at_local(fired_at, sent.group(1)) if sent else None
                    if sent_at and sent_at < fired_at:
                        sent_at += timedelta(days=1)
                    found.setdefault(
                        fired_at,
                        Send(
                            fired_at,
                            classify(text),
                            sent_at,
                            recorded,
                            path.parent.name,
                            calls[item["tool_use_id"]],
                        ),
                    )
    for clock, stop, source in NAMED:
        fired_at = local(clock, "%Y-%m-%d %H:%M:%S.%f")
        known = found.get(fired_at)
        found[fired_at] = Send(
            fired_at,
            known.stop if known else stop,
            known.sent if known else None,
            known.recorded if known else None,
            f"{source}" + (f" · {known.source}" if known else " · 트랜스크립트 없음"),
            known.called if known else None,
        )
    return sorted(found.values(), key=lambda s: s.fired)


def stamped(stamp: str) -> datetime:
    """트랜스크립트 기록의 시각(UTC)을 로컬로."""
    return datetime.fromisoformat(stamp.replace("Z", "+00:00")).astimezone()


def spread(label: str, seconds: list[float]) -> str:
    if not seconds:
        return f"{label} 0회"
    over = {limit: sum(1 for s in seconds if s > limit) for limit in (20, 60, 120)}
    return (
        f"{label} {len(seconds)}회 중앙값 {median(seconds):.1f}초 최대 {max(seconds):.1f}초"
        + "".join(f" {limit}초 넘음 {n}회" for limit, n in over.items())
    )


def group_of(stop: str) -> str:
    if stop == "보냄":
        return "보냄"
    if stop in SYMPTOMS:
        return "증상 멈춤"
    return "다른 멈춤"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--until", help="이 로컬 시각(YYYY-MM-DD HH:MM)까지 쏜 열기만 센다")
    until = parser.parse_args().until
    cutoff = local(until, "%Y-%m-%d %H:%M") if until else None
    timeline = read_timeline()
    sends = [s for s in read_sends() if cutoff is None or s.fired <= cutoff]
    print(f"쏜 시각 {until} 까지" if until else "쏜 시각 끝까지(--until 없음)")
    named = {local(c, "%Y-%m-%d %H:%M:%S.%f") for c, _, _ in NAMED}
    named_labels = {c for c, _, _ in NAMED}
    rounds = Rounds()
    outside = 0
    table: Counter[tuple[str, str]] = Counter()
    spans = ", ".join(f"{a:%m-%d %H:%M}~{b:%m-%d %H:%M}" for a, b in timeline.ranges)
    print(f"로그 [{spans}], 딥링크 {len(timeline.links)}, 열기 {len(sends)}")
    for send in sends:
        if not timeline.covers(send.fired):
            outside += 1
            continue
        label = f"{send.fired:%Y-%m-%d %H:%M:%S.%f}"[:-3]
        with rounds.round(label) as current:
            base = send.fired.replace(microsecond=0)
            own = next((t for t in timeline.links if base <= t <= base + OWN_WINDOW), None)
            if own is None:
                current.mark(
                    measured=False, result=f"자기 딥링크를 로그에서 찾지 못했다({send.stop})"
                )
                continue
            if send.sent is not None:
                end, inclusive = send.sent.replace(microsecond=0), False
            elif send.recorded is not None:
                end, inclusive = send.recorded, True
            else:
                end, inclusive = own + NAMED_SPAN, True
            foreign = [
                t for t in timeline.links if own < t and (t <= end if inclusive else t < end)
            ]
            group = group_of(send.stop)
            verdict = "겹침" if foreign else "겹침 없음"
            table[(group, verdict)] += 1
            current.mark(measured=True, result=f"{group}/{verdict}")
            if send.fired in named or group != "보냄" or foreign:
                starts = [f"{t:%H:%M:%S} {s}" for t, s in timeline.sessions if own <= t <= end]
                print(
                    f"{label} {send.stop} 자기 {own:%H:%M:%S}"
                    f" 남의 [{', '.join(f'{t:%H:%M:%S}' for t in foreign)}]"
                    f" 끝 {end:%H:%M:%S} 세션 [{'; '.join(starts)}] ({send.source})"
                )
    print(f"로그 밖의 열기 {outside}")
    print(rounds.summary())
    for group in ("증상 멈춤", "다른 멈춤", "보냄"):
        print(f"{group}: 겹침 {table[(group, '겹침')]}, 겹침 없음 {table[(group, '겹침 없음')]}")
    # 열기 하나의 길이. 잠금을 쥐는 시간(`-LockTimeoutSec` 을 고른 근거)과, 기다림을 더한 호출이
    # 부르는 도구의 제한 안에 드는지를 본다. 로그 밖의 열기도 센다.
    firing = [(s.sent - s.fired).total_seconds() for s in sends if s.sent]
    calling = [(s.recorded - s.called).total_seconds() for s in sends if s.recorded and s.called]
    print(spread("쏘고 보내기까지", firing))
    print(spread("호출 전체(기록한 호출부터 결과까지)", calling))
    result = {
        "table": {f"{g}/{v}": n for (g, v), n in sorted(table.items())},
        "unmeasured": len(rounds.unmeasured),
        "outside": outside,
        "named": {e.label: e.result for e in rounds.entries if e.label in named_labels},
        "until": until,
        "at": datetime.now(UTC).isoformat(timespec="seconds"),
    }
    print(json.dumps(result, ensure_ascii=False))
    return rounds.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
