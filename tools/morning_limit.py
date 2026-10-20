"""주간 한도를 찍어 남기고, 남긴 점과 장부 비용으로 한도의 몫을 어림한다.

앱의 `get_usage` 도구가 계정 전체의 한도(5시간, 주간 · 모든 모델, 주간 · Fable)를 정수 퍼센트와
초기화 시각으로 준다. 파이썬 도구와 훅은 이 도구를 부르지 못하고 앱 세션의 모델만 부르므로, 아침
보고 예약 작업의 모델이 그 결과를 파일로 쓰고 `record`가 계정과 함께 한 줄을
`<보고 폴더>/limit.jsonl`에 덧붙인다. 수집 도구(`tools/morning_collect.py`)는 그 줄들과 같은 계정의
장부 비용으로 `estimate`를 불러 보고의 주간 한도 절과 `주간 한도(%p)` 칸을 낸다.

어림. 세션·작업·모델마다 한도를 몇 % 썼는지는 앱이 주지 않는다. 그래서 한도가 API 환산 비용에
비례해 찬다고 놓고, 이번 창(초기화 시각의 7일 앞부터 찍은 시각까지)의 비용을 찍은 몫으로 나눠 "1% =
$X"를 얻는다(`Limit.rate`). 보고하는 날의 몫, 최근 24시간의 속도, 그 속도로 차는 시각은 그 비율로
센다. 설계는 `.scratch/morning-report-split/design.md`의 "주간 한도"이고, 2026-10-20 21:52의 첫
어림(66%, $1,784, 1% ≈ $27)은 커밋하지 않은 스크립트로 손으로 센 값이다.

못 보는 것.
- 비례 가정은 재지 않았다. 모델(Opus·Sonnet)이나 캐시 읽기를 한도가 API 단가와 다르게 세면 비율이
  모델 구성에 따라 흔들린다. 몫은 어림이다. 점은 보고 다섯이 09:00~10:15에 잇달아 찍으므로 하루
  안에 모델 구성이 다른 점이 쌓이지 않고, 며칠이 쌓여도 비율이 고른지는 날 사이의 비교로만 볼 수
  있다.
- 장부 밖의 사용(claude.ai 대화, 클라우드 세션, 다른 PC)도 한도를 채운다. 그 몫이 비율에 섞여 1%당
  달러가 작게, 작업의 몫이 크게 나온다.
- 장부는 하루 한 번(08:00 토큰 보고서) 채워진다. 그래서 비율은 장부를 채운 시각(수집 도구가 월별
  장부 파일의 수정 시각으로 준다) 전에 찍은 점으로 낸다. 그 시각 뒤에 찍은 점으로 내면 그 사이의
  비용이 빠져 1%당 달러가 작게 나왔다(2026-10-20 23:39에 찍은 70%로 $13, 손으로 잰 값은 $27). 그
  앞의 점이 없는 첫날은 환산하지 않는다. 장부를 채운 뒤 새 호출이 없으면 파일 시각이 그만큼 이르게
  잡혀 쓸 수 있는 점을 버릴 수 있지만, 비율을 틀리게 내지는 않는다.
- 계정은 `~/.claude.json`의 `oauthAccount`의 이메일(없으면 `accountUuid`)이고 장부의 세션
  계정(`token_report.read_accounts`)과 글자로 맞댄다. 둘 다 없으면 `record`가 쓰지 않고 2로 끝난다.

쓰임: `uv run python -m tools.morning_limit record --reports <폴더> --plan <get_usage 결과 JSON>`.
종료 0은 한 줄을 덧붙였다. 2는 쓰지 않았다는 뜻이고 까닭은 stderr에 있다. 결과 파일을 읽지
못했거나 15분보다 오래됐거나(실패한 호출 뒤에 옛 파일로 다시 치면 낡은 값이 지금 시각의 점이 된다),
주간 · 모든 모델 창이 없거나, 계정을 읽지 못했거나, 기록을 쓰지 못한 경우다.
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from tools.morning_report import Json, Limit, json_int, json_list, json_obj, json_str, json_time

WEEKLY = "Weekly · all models"
LOG = "limit.jsonl"
WINDOW = timedelta(days=7)
RECENT = timedelta(hours=24)
MAX_AGE = timedelta(minutes=15)


@dataclass(frozen=True)
class Record:
    """한도 한 점. `percent`는 주간 · 모든 모델의 쓴 몫, `resets`는 그 창의 초기화 시각이다."""

    at: datetime
    account: str
    percent: int
    resets: datetime

    def to_json(self) -> Json:
        return {
            "at": self.at.isoformat(),
            "account": self.account,
            "percent": self.percent,
            "resets": self.resets.isoformat(),
        }

    @staticmethod
    def of(j: Json) -> Record | None:
        o = json_obj(j)
        at, resets = json_time(o.get("at")), json_time(o.get("resets"))
        n = json_int(o.get("percent"))
        if at is None or resets is None or n is None:
            return None
        return Record(at, json_str(o.get("account")), n, resets)


def record_of(result: Json, account: str, now: datetime) -> Record | str:
    """`get_usage`의 결과(전체나 `plan`만)에서 주간 · 모든 모델 창을 골라 한 점을 짓는다."""
    o = json_obj(result)
    plan = json_obj(o.get("plan")) if "plan" in o else o
    for w in json_list(plan.get("windows")):
        window = json_obj(w)
        if json_str(window.get("label")) != WEEKLY:
            continue
        percent, resets = json_int(window.get("percentUsed")), json_time(window.get("resetsAt"))
        if percent is not None and resets is not None:
            return Record(now, account, percent, resets)
    return "get_usage의 결과에 주간 · 모든 모델 창이 없다"


def read_records(text: str) -> list[Record]:
    """`limit.jsonl`의 줄. 읽지 못한 줄은 건너뛴다(남기는 쪽이 모델이라 한 줄이 깨질 수 있다)."""
    out: list[Record] = []
    for line in text.splitlines():
        try:
            j: Json = json.loads(line)
        except ValueError:
            continue
        r = Record.of(j)
        if r is not None:
            out.append(r)
    return out


def _between(costs: Iterable[tuple[datetime, float]], start: datetime, end: datetime) -> float:
    return sum(c for t, c in costs if start <= t < end)


def estimate(
    records: Sequence[Record],
    costs: Sequence[tuple[datetime, float]],
    day_start: datetime,
    day_end: datetime,
    account: str,
    ledger_at: datetime,
) -> Limit | str:
    """`account`의 점과 그 계정의 호출 비용(`costs`, 시각과 달러)으로 짓는 어림. 보고하는 날은
    `day_start`부터 `day_end` 앞까지다. 지금 몫은 가장 늦은 점이고, 비율은 장부를 채운
    시각(`ledger_at`) 전에 찍은 가장 늦은 점으로 낸다. 그 뒤에 찍은 점에는 장부에 아직 없는 비용이
    들어 1%당 달러가 작게 나온다. 그런 점이 없거나 그 점의 몫이나 비용이 0이면 환산하지 않는다.
    속도도 장부를 채운 시각까지의 24시간으로 센다."""
    mine = [r for r in records if r.account == account]
    if not mine:
        return f"{account}의 한도 기록이 없다(예약 작업이 get_usage를 남기지 않았다)"
    r = max(mine, key=lambda x: x.at)
    covered = [x for x in mine if x.at <= ledger_at]
    basis = max(covered, key=lambda x: x.at) if covered else None
    spent = 0.0
    rate: float | None = None
    if basis is not None:
        spent = _between(costs, basis.resets - WINDOW, basis.at + timedelta(microseconds=1))
        rate = spent / basis.percent if basis.percent > 0 and spent > 0 else None
    day_points = speed = None
    full_at: str | None = None
    if rate is not None:
        day_points = _between(costs, day_start, day_end) / rate
        end = min(r.at, ledger_at)
        speed = _between(costs, end - RECENT, end + timedelta(microseconds=1)) / rate / 24
        if speed > 0:
            full = r.at + timedelta(hours=max(0, 100 - r.percent) / speed)
            full_at = full.isoformat() if full < r.resets else None
    return Limit(
        percent=r.percent,
        at=r.at.isoformat(),
        resets=r.resets.isoformat(),
        account=account,
        rate=rate,
        spent=spent,
        day_points=day_points,
        speed=speed,
        full_at=full_at,
        basis_at=basis.at.isoformat() if basis is not None and rate is not None else None,
        basis_percent=basis.percent if basis is not None and rate is not None else None,
    )


def read_account(home: Path) -> str:
    """`~/.claude.json`의 로그인 계정. 장부(`token_report.read_accounts`)처럼 이메일이고, 없으면
    계정 ID다. 둘 다 없거나 읽지 못하면 빈 글이다."""
    try:
        j: Json = json.loads((home / ".claude.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ""
    oauth = json_obj(json_obj(j).get("oauthAccount"))
    return json_str(oauth.get("emailAddress")) or json_str(oauth.get("accountUuid"))


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="주간 한도를 찍어 남긴다")
    sub = p.add_subparsers(dest="command", required=True)
    record = sub.add_parser("record", help="get_usage 결과 한 점을 덧붙인다")
    record.add_argument("--reports", type=Path, required=True, help="보고 폴더")
    record.add_argument("--plan", type=Path, required=True, help="get_usage 결과를 쓴 JSON 파일")
    record.add_argument("--home", type=Path, default=Path.home(), help="~/.claude.json이 든 폴더")
    return p


def main(argv: list[str]) -> int:
    args = _parser().parse_args(argv)
    reports: Path = args.reports
    plan_path: Path = args.plan
    home: Path = args.home
    now = datetime.now(UTC).astimezone()
    try:
        result: Json = json.loads(plan_path.read_text(encoding="utf-8"))
        age = now - datetime.fromtimestamp(plan_path.stat().st_mtime, UTC)
    except (OSError, ValueError) as error:
        sys.stderr.write(f"get_usage 결과를 읽지 못했다: {error}\n")
        return 2
    if age > MAX_AGE:
        minutes = int(age.total_seconds() // 60)
        sys.stderr.write(
            f"get_usage 결과 파일이 {minutes}분 전 것이라 지금 시각의 점으로 남기지 않는다."
            " get_usage를 다시 불러 파일을 새로 쓴다\n"
        )
        return 2
    account = read_account(home)
    if not account:
        sys.stderr.write(f"계정을 읽지 못했다({home / '.claude.json'}의 oauthAccount)\n")
        return 2
    r = record_of(result, account, now)
    if isinstance(r, str):
        sys.stderr.write(f"{r}\n")
        return 2
    line = json.dumps(r.to_json(), ensure_ascii=False)
    try:
        reports.mkdir(parents=True, exist_ok=True)
        with (reports / LOG).open("a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError as error:
        sys.stderr.write(f"한도 기록을 쓰지 못했다: {error}\n")
        return 2
    print(line)
    return 0


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(encoding="utf-8")
    raise SystemExit(main(sys.argv[1:]))
