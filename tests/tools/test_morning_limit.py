"""tools/morning_limit.py 검증. 한도 값은 2026-10-20 21:52 KST에 앱의 `get_usage`가 준 모양을
줄였다."""

from __future__ import annotations

import json
import os
import time
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path

import pytest
from tools.morning_limit import Record, estimate, main, read_account, read_records, record_of
from tools.morning_report import Json, Limit

KST = timezone(timedelta(hours=9))
AT = datetime(2026, 10, 20, 21, 52, tzinfo=KST)
RESETS = datetime(2026, 10, 26, 6, 0, tzinfo=KST)
BODY: Json = {
    "status": "ok",
    "windows": [
        {"label": "5-hour limit", "percentUsed": 36, "resetsAt": "2026-10-20T15:59:59Z"},
        {"label": "Weekly · all models", "percentUsed": 66, "resetsAt": "2026-10-25T21:00:00Z"},
        {"label": "Weekly · Fable", "percentUsed": 0, "resetsAt": "2026-10-25T21:00:00Z"},
    ],
}
PLAN: Json = {"plan": BODY}


def 기록(percent: int = 66, at: datetime = AT, account: str = "a@x") -> Record:
    return Record(at, account, percent, RESETS)


def test_get_usage의_결과에서_주간_모든_모델의_몫과_초기화_시각을_고른다() -> None:
    r = record_of(PLAN, "a@x", AT)
    assert r == Record(AT, "a@x", 66, datetime(2026, 10, 25, 21, tzinfo=UTC))


def test_plan만_넘겨도_읽는다() -> None:
    r = record_of(BODY, "a@x", AT)
    assert isinstance(r, Record)
    assert r.percent == 66


def test_주간_모든_모델의_창이_없으면_까닭이다() -> None:
    assert record_of({"plan": {"status": "unavailable", "windows": []}}, "a@x", AT) == (
        "get_usage의 결과에 주간 · 모든 모델 창이 없다"
    )


def test_주간_몫이_정수가_아니면_창이_없다고_하지_않고_그_까닭을_적는다() -> None:
    body: Json = {
        "windows": [
            {
                "label": "Weekly · all models",
                "percentUsed": 66.5,
                "resetsAt": "2026-10-25T21:00:00Z",
            }
        ]
    }
    assert record_of(body, "a@x", AT) == "get_usage의 주간 · 모든 모델 몫이 정수가 아니다: 66.5"


def test_기록은_한_줄로_쓰고_다시_읽는다() -> None:
    line = 기록().to_json()
    assert read_records(json.dumps(line) + "\n" + "{깨진 줄\n") == [기록()]


def test_환산_비율은_이번_창의_비용을_몫으로_나눈_값이다() -> None:
    # 10-20 21:52에 66%, 같은 창의 비용 $1,784였다(1% ≈ $27)
    costs = [(AT - timedelta(days=1), 1782.0), (RESETS - timedelta(days=8), 500.0)]
    limit = estimate([기록()], costs, AT - timedelta(days=1, hours=1), AT, "a@x", AT)
    assert isinstance(limit, Limit)
    assert limit.spent == 1782.0
    assert limit.rate == 27.0


def test_보고하는_날의_몫과_최근_24시간_속도로_차는_시각을_낸다() -> None:
    # 하루 $648(24%p)씩 쓰면 시간당 1%p이고, 남은 34%는 34시간 뒤에 찬다
    costs = [(AT - timedelta(hours=30), 1134.0), (AT - timedelta(hours=2), 648.0)]
    day_start = AT - timedelta(hours=20)
    limit = estimate([기록()], costs, day_start, AT, "a@x", AT)
    assert isinstance(limit, Limit)
    assert limit.day_points == 24.0
    assert limit.speed == 1.0
    assert limit.full_at == (AT + timedelta(hours=34)).isoformat()


def test_초기화_전에_차지_않으면_차는_시각이_없다() -> None:
    costs = [(AT - timedelta(hours=36), 1755.0), (AT - timedelta(hours=1), 27.0)]
    limit = estimate([기록()], costs, AT - timedelta(hours=5), AT, "a@x", AT)
    assert isinstance(limit, Limit)
    assert limit.full_at is None


def test_가장_늦은_기록을_쓰고_다른_계정의_기록과_비용은_세지_않는다() -> None:
    records = [기록(10, AT - timedelta(days=1)), 기록(66), 기록(90, account="b@x")]
    limit = estimate(records, [(AT - timedelta(hours=1), 660.0)], AT, AT, "a@x", AT)
    assert isinstance(limit, Limit)
    assert (limit.percent, limit.rate) == (66, 10.0)


def test_장부를_채운_뒤에_찍은_기록은_비율에_쓰지_않고_그_앞의_기록으로_비율을_낸다() -> None:
    # 장부는 하루 한 번 채워진다. 그 뒤에 찍은 66%에는 장부에 없는 비용이 들어 1%당 달러가 작게
    # 나왔다(2026-10-20 23:39에 찍은 70%로 1% ≈ $13, 손으로 잰 값은 $27)
    earlier = 기록(50, AT - timedelta(hours=24))
    costs = [(AT - timedelta(hours=38), 1000.0), (AT - timedelta(hours=14), 240.0)]
    ledger_at = AT - timedelta(hours=12)
    limit = estimate([earlier, 기록(66)], costs, AT, AT, "a@x", ledger_at)
    assert isinstance(limit, Limit)
    assert (limit.percent, limit.basis_percent, limit.rate) == (66, 50, 20.0)
    assert limit.basis_at == earlier.at.isoformat()
    # 속도는 장부를 채운 시각까지의 24시간이다: $240 ÷ $20 ÷ 24시간
    assert limit.speed == 0.5
    assert limit.full_at == (AT + timedelta(hours=68)).isoformat()


def test_장부를_채우기_전에_찍은_기록이_없으면_환산하지_않는다() -> None:
    limit = estimate(
        [기록()], [(AT - timedelta(hours=2), 10.0)], AT, AT, "a@x", AT - timedelta(hours=1)
    )
    assert isinstance(limit, Limit)
    assert limit.percent == 66
    assert (limit.rate, limit.basis_at, limit.day_points, limit.speed) == (None, None, None, None)


def test_그_계정의_기록이_없으면_까닭이다() -> None:
    assert estimate([기록(account="b@x")], [], AT, AT, "a@x", AT) == (
        "a@x의 한도 기록이 없다(예약 작업이 get_usage를 남기지 않았다)"
    )


def test_몫이나_비용이_0이면_환산하지_않는다() -> None:
    limit = estimate([기록(0)], [(AT - timedelta(hours=1), 10.0)], AT, AT, "a@x", AT)
    assert isinstance(limit, Limit)
    assert (limit.rate, limit.day_points, limit.speed, limit.full_at) == (None, None, None, None)


def test_record는_계정과_함께_한_줄을_덧붙인다(tmp_path: Path) -> None:
    home = tmp_path / "home"
    home.mkdir()
    account = {"oauthAccount": {"accountUuid": "u", "emailAddress": "a@x"}}
    (home / ".claude.json").write_text(json.dumps(account), encoding="utf-8")
    plan = tmp_path / "plan.json"
    plan.write_text(json.dumps(PLAN), encoding="utf-8")
    reports = tmp_path / "reports"
    args = ["record", "--reports", str(reports), "--plan", str(plan), "--home", str(home)]
    assert main(args) == 0
    assert main(args) == 0
    records = read_records((reports / "limit.jsonl").read_text(encoding="utf-8"))
    assert [(r.account, r.percent) for r in records] == [("a@x", 66), ("a@x", 66)]


def 인자(tmp_path: Path, plan: Json = PLAN, email: str | None = "a@x") -> list[str]:
    home = tmp_path / "home"
    home.mkdir(exist_ok=True)
    oauth = {} if email is None else {"emailAddress": email}
    (home / ".claude.json").write_text(json.dumps({"oauthAccount": oauth}), encoding="utf-8")
    path = tmp_path / "plan.json"
    path.write_text(json.dumps(plan), encoding="utf-8")
    return ["record", "--reports", str(tmp_path / "r"), "--plan", str(path), "--home", str(home)]


def test_record는_창이_없으면_쓰지_않고_까닭과_함께_2로_끝난다(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(인자(tmp_path, {"plan": {"windows": []}})) == 2
    assert "주간 · 모든 모델 창이 없다" in capsys.readouterr().err
    assert not (tmp_path / "r" / "limit.jsonl").exists()


def test_record는_결과_파일이_없으면_그_까닭으로_2로_끝난다(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    args = 인자(tmp_path)
    os.remove(args[4])
    assert main(args) == 2
    assert "get_usage 결과를 읽지 못했다" in capsys.readouterr().err


def test_record는_오래된_결과_파일이면_지금_시각으로_남기지_않고_2로_끝난다(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # get_usage가 실패한 뒤 어제의 결과 파일로 record만 다시 치면 낡은 값이 지금 시각의 점이 된다
    args = 인자(tmp_path)
    old = time.time() - 3600
    os.utime(args[4], (old, old))
    assert main(args) == 2
    assert "분 전" in capsys.readouterr().err
    assert not (tmp_path / "r" / "limit.jsonl").exists()


def test_record는_계정을_읽지_못하면_빈_계정으로_남기지_않고_2로_끝난다(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # 빈 계정의 점은 어떤 계정의 장부 비용과도 맞지 않아 보고에 매일 "내일부터 나옵니다"만 찍힌다
    assert main(인자(tmp_path, email=None)) == 2
    assert "계정" in capsys.readouterr().err
    assert not (tmp_path / "r" / "limit.jsonl").exists()


def test_계정은_이메일이고_없으면_장부처럼_계정_ID다(tmp_path: Path) -> None:
    def 쓰기(oauth: Json) -> None:
        (tmp_path / ".claude.json").write_text(
            json.dumps({"oauthAccount": oauth}), encoding="utf-8"
        )

    assert read_account(tmp_path) == ""
    쓰기({"emailAddress": "a@x", "accountUuid": "u"})
    assert read_account(tmp_path) == "a@x"
    쓰기({"accountUuid": "u"})
    assert read_account(tmp_path) == "u"
    쓰기({})
    assert read_account(tmp_path) == ""
