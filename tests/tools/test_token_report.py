"""tools/token_report.py. 가짜 세션 기록 폴더를 넣고 명령을 부른 뒤 장부와 보고서 파일을 본다.

이음매는 명령 하나다(`.scratch/token-usage/spec.md` 이음매, 사용자가 골랐다). 모든 시험은
`--today`와 `--tz`를 줘 벽시계에 기대지 않는다. 가격은 `claude-opus-5-5`(입력 $4, 출력 $20, 캐시
읽기 $0.20, 5분 쓰기 $5, 1시간 쓰기 $8, 백만 토큰당)와 `claude-sonnet-5-5`(입력 $2, 출력 $10, 캐시
읽기 $0.20)로 손으로 셈한다. 지표 7~12, 주간·4주 보고서, 큰 도구 결과는 티켓 03의 몫이라 여기 없다.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

import pytest
from tools.token_report import folder_name_of, main, main_checkout

OPUS = "claude-opus-5-5"
SONNET = "claude-sonnet-5-5"
SID_A = "aaaaaaaa-0000-0000-0000-000000000001"
SID_B = "bbbbbbbb-0000-0000-0000-000000000002"
SID_FORK = "00000000-0000-0000-0000-00000000f0f0"
FOLDER = "C--project-agent"
TODAY = "2026-10-16"
DAY = "2026-10-15"

type Rec = dict[str, object]


def 응답(
    mid: str,
    at: str,
    *,
    model: str = OPUS,
    입력: int = 0,
    캐시읽기: int = 0,
    쓰기5분: int = 0,
    쓰기1시간: int = 0,
    출력: int = 0,
    effort: str | None = "medium",
    branch: str = "feature/a",
    content: list[Rec] | None = None,
) -> Rec:
    usage: Rec = {
        "input_tokens": 입력,
        "cache_creation_input_tokens": 쓰기5분 + 쓰기1시간,
        "cache_read_input_tokens": 캐시읽기,
        "output_tokens": 출력,
        "cache_creation": {
            "ephemeral_5m_input_tokens": 쓰기5분,
            "ephemeral_1h_input_tokens": 쓰기1시간,
        },
    }
    rec: Rec = {
        "type": "assistant",
        "timestamp": at,
        "gitBranch": branch,
        "isSidechain": False,
        "message": {"id": mid, "model": model, "usage": usage, "content": content or []},
    }
    if effort is not None:
        rec["effort"] = effort
    return rec


def 사람(at: str, text: str = "시작") -> Rec:
    return {"type": "user", "timestamp": at, "message": {"role": "user", "content": text}}


def 쓴다(path: Path, recs: list[Rec], 끝: str = "") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "".join(json.dumps(r, ensure_ascii=False) + "\n" for r in recs)
    path.write_text(body + 끝, encoding="utf-8")
    return path


def 메인(projects: Path, sid: str, recs: list[Rec], folder: str = FOLDER, 끝: str = "") -> Path:
    return 쓴다(projects / folder / f"{sid}.jsonl", recs, 끝)


def 서브(projects: Path, sid: str, aid: str, recs: list[Rec], meta: Rec | None = None) -> Path:
    base = projects / FOLDER / sid / "subagents"
    if meta is not None:
        base.mkdir(parents=True, exist_ok=True)
        (base / f"agent-{aid}.meta.json").write_text(json.dumps(meta), encoding="utf-8")
    return 쓴다(base / f"agent-{aid}.jsonl", recs)


def 계정(out: Path, lines: list[Rec]) -> None:
    쓴다(out / "ledger" / "accounts.jsonl", lines)


@dataclass
class 판:
    tmp: Path
    tz: str = "+09:00"
    projects: Path = field(init=False)
    out: Path = field(init=False)

    def __post_init__(self) -> None:
        self.projects = self.tmp / "projects"
        self.out = self.tmp / "out"
        self.projects.mkdir(parents=True)

    def 돌린다(self, *args: str, today: str = TODAY) -> int:
        cmd, *rest = args
        return main(
            [
                cmd,
                *rest,
                "--projects",
                str(self.projects),
                "--out",
                str(self.out),
                "--tz",
                self.tz,
                "--today",
                today,
            ]
        )

    def 장부(self) -> list[Rec]:
        rows: list[Rec] = []
        for p in sorted((self.out / "ledger").glob("????-??.jsonl")):
            rows.extend(json.loads(x) for x in p.read_text(encoding="utf-8").splitlines())
        return rows

    def 호출(self) -> list[Rec]:
        return [r for r in self.장부() if r["kind"] == "call"]

    def 장부_바이트(self) -> dict[str, bytes]:
        return {p.name: p.read_bytes() for p in sorted((self.out / "ledger").iterdir())}

    def 일간(self, day: str = DAY) -> str:
        return (self.out / "daily" / f"{day}.md").read_text(encoding="utf-8")

    def 요약(self) -> str:
        return (self.out / "summary.txt").read_text(encoding="utf-8")


def _판(tmp_path: Path) -> 판:
    return 판(tmp_path)


# 장부


def test_호출_행은_명세의_칸을_모두_든다(tmp_path: Path) -> None:
    t = _판(tmp_path)
    메인(
        t.projects,
        SID_A,
        [
            사람("2026-10-15T00:00:00Z"),
            응답(
                "m1", "2026-10-15T00:01:00Z", 입력=10, 캐시읽기=20, 쓰기5분=30, 쓰기1시간=40, 출력=5
            ),
            응답("m2", "2026-10-15T00:03:30Z", 입력=1, effort=None, branch="feature/b"),
        ],
    )
    assert t.돌린다("ingest") == 0
    first, second = t.호출()
    assert first == {
        "v": 1,
        "kind": "call",
        "id": "m1",
        "at": "2026-10-15T00:01:00Z",
        "session": SID_A,
        "agent": None,
        "agent_type": None,
        "project": FOLDER,
        "branch": "feature/a",
        "model": OPUS,
        "effort": "medium",
        "input": 10,
        "cache_read": 20,
        "cache_write_5m": 30,
        "cache_write_1h": 40,
        "output": 5,
        "context": 100,
        "gap_s": None,
    }
    assert second["gap_s"] == 150.0
    assert second["effort"] is None
    assert second["branch"] == "feature/b"
    sessions = [r for r in t.장부() if r["kind"] == "session"]
    assert sessions == [
        {"v": 1, "kind": "session", "session": SID_A, "start": "2026-10-15T00:00:00Z"}
    ]


def test_모든_행에_형식_판_칸이_있고_달_파일로_나뉜다(tmp_path: Path) -> None:
    t = _판(tmp_path)
    메인(t.projects, SID_A, [응답("m1", "2026-09-30T23:00:00Z", 입력=1)])
    메인(t.projects, SID_B, [응답("m2", "2026-10-02T00:00:00Z", 입력=1)])
    assert t.돌린다("ingest") == 0
    # +09:00에서 9월 30일 23시(UTC)는 10월 1일이다.
    assert sorted(p.name for p in (t.out / "ledger").iterdir()) == ["2026-10.jsonl"]
    assert all(r["v"] == 1 for r in t.장부())
    assert (t.out / "state.json").is_file()


def test_응답마다_출력_토큰이_가장_큰_usage를_쓴다(tmp_path: Path) -> None:
    t = _판(tmp_path)
    메인(
        t.projects,
        SID_A,
        [
            응답("m1", "2026-10-15T00:00:00Z", 입력=7, 출력=10),
            응답("m1", "2026-10-15T00:00:05Z", 입력=7, 출력=500),
            응답("m1", "2026-10-15T00:00:06Z", 입력=7, 출력=20),
        ],
    )
    t.돌린다("ingest")
    [row] = t.호출()
    assert (row["output"], row["at"]) == (500, "2026-10-15T00:00:00Z")


def test_다시_읽은_기록의_행은_새_값으로_갈아_끼운다(tmp_path: Path) -> None:
    # 세션이 응답을 쓰는 도중에 읽으면 출력 토큰이 스트리밍 중간값이다.
    t = _판(tmp_path)
    첫 = [응답("m1", "2026-10-15T00:00:00Z", 입력=7, 출력=10)]
    메인(t.projects, SID_A, 첫)
    t.돌린다("ingest")
    메인(t.projects, SID_A, [*첫, 응답("m1", "2026-10-15T00:00:05Z", 입력=7, 출력=500)])
    t.돌린다("ingest")
    assert [(r["id"], r["output"]) for r in t.호출()] == [("m1", 500)]


def test_겹친_사본은_한_번만_세고_긴_사본을_읽는다(tmp_path: Path) -> None:
    t = _판(tmp_path)
    짧은 = [응답("m1", "2026-10-15T00:00:00Z", 입력=1)]
    긴 = [*짧은, 응답("m2", "2026-10-15T00:01:00Z", 입력=2)]
    메인(t.projects, SID_A, 긴, folder=FOLDER)
    메인(t.projects, SID_A, 짧은, folder=FOLDER + "--claude-worktrees-x")
    t.돌린다("ingest")
    assert [(r["id"], r["project"]) for r in t.호출()] == [("m1", FOLDER), ("m2", FOLDER)]


def test_같은_입력으로_두_번_돌려도_장부가_같다(tmp_path: Path) -> None:
    t = _판(tmp_path)
    메인(t.projects, SID_A, [응답("m1", "2026-10-15T00:00:00Z", 입력=1)])
    메인(t.projects, SID_B, [응답("m2", "2026-10-15T00:00:00Z", 입력=2)])
    t.돌린다("ingest")
    before = t.장부_바이트()
    t.돌린다("ingest", "--full")
    assert t.장부_바이트() == before


def test_기록_파일을_지워도_장부의_행은_남는다(tmp_path: Path) -> None:
    t = _판(tmp_path)
    p = 메인(t.projects, SID_A, [응답("m1", "2026-10-15T00:00:00Z", 입력=1)])
    t.돌린다("ingest")
    p.unlink()
    t.돌린다("ingest")
    assert [r["id"] for r in t.호출()] == ["m1"]
    t.돌린다("ingest", "--full")
    assert [r["id"] for r in t.호출()] == ["m1"]


def test_긴_사본이_지워진_뒤_짧은_사본을_다시_읽어도_행이_남는다(tmp_path: Path) -> None:
    t = _판(tmp_path)
    짧은 = [응답("m1", "2026-10-15T00:00:00Z", 입력=1)]
    긴 = 메인(t.projects, SID_A, [*짧은, 응답("m2", "2026-10-15T00:01:00Z", 입력=2)])
    메인(t.projects, SID_A, 짧은, folder=FOLDER + "--claude-worktrees-x")
    t.돌린다("ingest")
    긴.unlink()
    t.돌린다("ingest", "--full")
    assert [r["id"] for r in t.호출()] == ["m1", "m2"]


def test_시작을_모르는_세션끼리_겹친_응답은_먼저_장부에_든_쪽에_남는다(tmp_path: Path) -> None:
    # 부모 기록이 없는 서브에이전트는 세션 시작 시각을 모른다.
    t = _판(tmp_path)
    shared = 응답("m1", "2026-10-15T00:00:00Z", 입력=1)
    서브(t.projects, SID_B, "x1", [shared])
    t.돌린다("ingest")
    서브(t.projects, SID_A, "x2", [shared])
    t.돌린다("ingest")
    assert [(r["session"], r["agent"]) for r in t.호출()] == [(SID_B, "x1")]


def test_지난_실행_한_시간_전보다_앞선_파일은_다시_읽지_않는다(tmp_path: Path) -> None:
    t = _판(tmp_path)
    recs = [응답("m1", "2026-10-15T00:00:00Z", 입력=1)]
    p = 메인(t.projects, SID_A, recs)
    t.돌린다("ingest")
    메인(t.projects, SID_A, [*recs, 응답("m2", "2026-10-15T00:05:00Z", 입력=1)])
    old = time.time() - 2 * 3600
    os.utime(p, (old, old))
    t.돌린다("ingest")
    assert [r["id"] for r in t.호출()] == ["m1"]
    now = time.time()
    os.utime(p, (now, now))
    t.돌린다("ingest")
    assert [r["id"] for r in t.호출()] == ["m1", "m2"]


def test_full은_state를_무시하고_계정_기록을_남긴다(tmp_path: Path) -> None:
    t = _판(tmp_path)
    recs = [응답("m1", "2026-10-15T00:00:00Z", 입력=1)]
    p = 메인(t.projects, SID_A, recs)
    t.돌린다("ingest")
    계정(t.out, [{"v": 1, "session_id": SID_A, "account_uuid": "u1", "email": "a@example.com"}])
    accounts = (t.out / "ledger" / "accounts.jsonl").read_bytes()
    메인(t.projects, SID_A, [*recs, 응답("m2", "2026-10-15T00:05:00Z", 입력=1)])
    old = time.time() - 2 * 3600
    os.utime(p, (old, old))
    t.돌린다("ingest", "--full")
    assert [r["id"] for r in t.호출()] == ["m1", "m2"]
    assert (t.out / "ledger" / "accounts.jsonl").read_bytes() == accounts


def test_포크에_복사된_응답은_먼저_시작한_세션에_한_번만_든다(tmp_path: Path) -> None:
    t = _판(tmp_path)
    원본 = [사람("2026-10-15T00:00:00Z"), 응답("m1", "2026-10-15T00:01:00Z", 입력=1)]
    포크 = [사람("2026-10-15T00:30:00Z"), 원본[1], 응답("m2", "2026-10-15T00:40:00Z", 입력=1)]
    # 포크만 있을 때 들인 뒤, 원본이 나중에 나타나도 원본으로 옮겨 간다.
    메인(t.projects, SID_FORK, 포크)
    t.돌린다("ingest")
    assert [(r["id"], r["session"]) for r in t.호출()] == [("m1", SID_FORK), ("m2", SID_FORK)]
    메인(t.projects, SID_A, 원본)
    t.돌린다("ingest")
    assert sorted((str(r["id"]), str(r["session"])) for r in t.호출()) == [
        ("m1", SID_A),
        ("m2", SID_FORK),
    ]
    before = t.장부_바이트()
    t.돌린다("ingest", "--full")
    assert t.장부_바이트() == before


def test_synthetic_기록은_장부에도_경보에도_들지_않는다(tmp_path: Path) -> None:
    t = _판(tmp_path)
    메인(
        t.projects,
        SID_A,
        [
            응답("m1", "2026-10-15T00:00:00Z", 입력=1),
            응답("s1", "2026-10-15T00:01:00Z", model="<synthetic>"),
        ],
    )
    assert t.돌린다("daily") == 0
    assert [r["id"] for r in t.호출()] == ["m1"]
    assert "경보 없음" in t.요약()


def test_잘린_마지막_줄은_경보_없이_넘기고_깨진_줄은_경보다(tmp_path: Path) -> None:
    t = _판(tmp_path)
    메인(t.projects, SID_A, [응답("m1", "2026-10-15T00:00:00Z", 입력=1)], 끝='{"type": "assis')
    assert t.돌린다("daily") == 0
    assert "경보 없음" in t.요약()
    p = t.projects / FOLDER / f"{SID_B}.jsonl"
    p.parent.mkdir(parents=True, exist_ok=True)
    body = json.dumps(응답("m2", "2026-10-15T00:00:00Z", 입력=1)) + "\n깨진 줄\n"
    p.write_text(body, encoding="utf-8")
    assert t.돌린다("daily") == 0
    assert "경보: 읽지 못한 기록 줄 1개" in t.요약()


def test_잠금이_있으면_둘째_ingest는_알리고_끝난다(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    t = _판(tmp_path)
    메인(t.projects, SID_A, [응답("m1", "2026-10-15T00:00:00Z", 입력=1)])
    t.out.mkdir()
    (t.out / "ingest.lock").write_text("", encoding="utf-8")
    assert t.돌린다("ingest") == 3
    assert "잠금 파일" in capsys.readouterr().err
    assert not (t.out / "ledger").exists()
    assert t.돌린다("daily") == 3
    assert t.돌린다("report") == 3
    assert not (t.out / "daily").exists()
    (t.out / "ingest.lock").unlink()
    assert t.돌린다("ingest") == 0
    assert not (t.out / "ingest.lock").exists()


def test_서브에이전트_유형은_meta와_부모의_Agent_호출로_잇는다(tmp_path: Path) -> None:
    t = _판(tmp_path)
    agent_use: Rec = {
        "type": "tool_use",
        "id": "tu1",
        "name": "Agent",
        "input": {"subagent_type": "Explore"},
    }
    result: Rec = {
        "type": "user",
        "timestamp": "2026-10-15T00:02:00Z",
        "toolUseResult": {"agentId": "a2", "agentType": "Explore"},
        "message": {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "tu1"}]},
    }
    메인(
        t.projects, SID_A, [응답("m1", "2026-10-15T00:00:00Z", 입력=1, content=[agent_use]), result]
    )
    서브(
        t.projects,
        SID_A,
        "a1",
        [응답("s1", "2026-10-15T00:01:00Z", 입력=1)],
        {"agentType": "coderabbit-review"},
    )
    서브(t.projects, SID_A, "a2", [응답("s2", "2026-10-15T00:01:00Z", 입력=1)])
    서브(t.projects, SID_A, "a3", [응답("s3", "2026-10-15T00:01:00Z", 입력=1)])
    t.돌린다("ingest")
    got = {str(r["id"]): (r["session"], r["agent"], r["agent_type"]) for r in t.호출()}
    assert got == {
        "m1": (SID_A, None, None),
        "s1": (SID_A, "a1", "coderabbit-review"),
        "s2": (SID_A, "a2", "Explore"),
        "s3": (SID_A, "a3", None),
    }


# 계정


def test_계정은_null이_아닌_마지막_줄이고_서브에이전트는_부모의_것이다(tmp_path: Path) -> None:
    t = _판(tmp_path)
    메인(t.projects, SID_A, [응답("m1", "2026-10-15T00:00:00Z", 입력=1_000_000)])
    서브(t.projects, SID_A, "a1", [응답("s1", "2026-10-15T00:01:00Z", 입력=1_000_000)])
    메인(t.projects, SID_B, [응답("m2", "2026-10-15T00:00:00Z", 입력=500_000)])
    at = "2026-10-15T00:00:00Z"
    계정(
        t.out,
        [
            {
                "v": 1,
                "at": at,
                "session_id": SID_A,
                "source": "startup",
                "account_uuid": "u0",
                "email": "old@example.com",
            },
            {
                "v": 1,
                "at": at,
                "session_id": SID_A,
                "source": "resume",
                "account_uuid": "u1",
                "email": "a@example.com",
                "새_키": 1,
            },
            {
                "v": 1,
                "at": at,
                "session_id": SID_A,
                "source": "compact",
                "account_uuid": None,
                "email": None,
            },
        ],
    )
    assert t.돌린다("daily") == 0
    report = t.일간()
    assert "| a@example.com | 8.00 | 80.0% | 2 |" in report
    assert "| 계정 모름 | 2.00 | 20.0% | 1 |" in report
    assert "old@example.com" not in report
    assert "환산 비용 $10.00 (a@example.com $8.00, 계정 모름 $2.00)" in t.요약()


# 날짜


def test_지역_날짜는_시간대_인자를_따라_갈린다(tmp_path: Path) -> None:
    # UTC로는 10월 14일 16시, +09:00에서는 10월 15일 01시다.
    t = _판(tmp_path)
    메인(t.projects, SID_A, [응답("m1", "2026-10-14T16:00:00Z", 입력=1_000_000)])
    t.돌린다("daily")
    assert "모델 호출 1회, 환산 비용 $4.00" in t.일간("2026-10-15")
    assert "호출 없음" in t.일간("2026-10-14")
    u = 판(tmp_path / "utc", tz="+00:00")
    메인(u.projects, SID_A, [응답("m1", "2026-10-14T16:00:00Z", 입력=1_000_000)])
    u.돌린다("daily")
    assert "모델 호출 1회, 환산 비용 $4.00" in u.일간("2026-10-14")
    assert "호출 없음" in u.일간("2026-10-15")


def test_빠진_날을_모두_만들고_일간은_최근_일곱만_남는다(tmp_path: Path) -> None:
    t = _판(tmp_path)
    메인(t.projects, SID_A, [응답("m1", "2026-10-12T00:00:00Z", 입력=1)])
    t.돌린다("daily")
    names = sorted(p.name for p in (t.out / "daily").iterdir())
    assert names == [f"2026-10-{d:02}.md" for d in range(9, 16)]
    t.돌린다("report", today="2026-10-20")
    names = sorted(p.name for p in (t.out / "daily").iterdir())
    assert names == [f"2026-10-{d:02}.md" for d in range(13, 20)]
    assert t.요약().splitlines()[0] == "보고서 날짜: 2026-10-19"


def test_보관_수를_넘은_보고서는_그_이름_모양의_파일만_지운다(tmp_path: Path) -> None:
    t = _판(tmp_path)
    daily = t.out / "daily"
    daily.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    target = outside / "keep.md"
    target.write_text("밖", encoding="utf-8")
    (daily / "2026-01-01.md").write_text("옛 보고서", encoding="utf-8")
    (daily / "notes.md").write_text("", encoding="utf-8")
    (daily / "2026-01-02.md.bak").write_text("", encoding="utf-8")
    (daily / "2026-01-03.md").mkdir()
    links: list[Path] = []
    try:
        (daily / "2026-01-04.md").symlink_to(target)
        links.append(daily / "2026-01-04.md")
    except OSError:
        pass
    if sys.platform == "win32":
        import _winapi

        _winapi.CreateJunction(str(outside), str(daily / "2026-01-05.md"))
        links.append(daily / "2026-01-05.md")
    assert links, "링크를 하나도 만들지 못했다"
    assert t.돌린다("report") == 0
    left = {p.name for p in daily.iterdir()}
    assert "2026-01-01.md" not in left
    assert {"notes.md", "2026-01-02.md.bak", "2026-01-03.md"} <= left
    assert {p.name for p in links} <= left
    assert target.read_text(encoding="utf-8") == "밖"


def test_daily_폴더가_링크면_쓰지도_지우지도_않는다(tmp_path: Path) -> None:
    t = _판(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "2026-01-01.md").write_text("밖", encoding="utf-8")
    t.out.mkdir()
    if sys.platform == "win32":
        import _winapi

        _winapi.CreateJunction(str(outside), str(t.out / "daily"))
    else:
        (t.out / "daily").symlink_to(outside, target_is_directory=True)
    assert t.돌린다("report") == 2
    assert [p.name for p in outside.iterdir()] == ["2026-01-01.md"]


def test_보고서_폴더를_지운_뒤_report가_같은_파일을_다시_만든다(tmp_path: Path) -> None:
    t = _판(tmp_path)
    메인(t.projects, SID_A, [응답("m1", "2026-10-12T00:00:00Z", 입력=1)])
    t.돌린다("daily")
    before = {p.name: p.read_bytes() for p in (t.out / "daily").iterdir()}
    summary = t.요약()
    for p in (t.out / "daily").iterdir():
        p.unlink()
    (t.out / "daily").rmdir()
    (t.out / "summary.txt").unlink()
    t.돌린다("report")
    assert {p.name: p.read_bytes() for p in (t.out / "daily").iterdir()} == before
    assert t.요약() == summary


def test_빈_기록_폴더에서도_호출_없음_보고서와_요약을_쓴다(tmp_path: Path) -> None:
    t = _판(tmp_path)
    assert t.돌린다("daily") == 0
    report = t.일간()
    assert "호출 없음" in report
    assert "모델 호출 0회, 환산 비용 $0.00" in report
    assert t.요약().splitlines() == [
        f"보고서 날짜: {DAY}",
        "환산 비용 $0.00",
        "경보 없음",
        f"보고서: {t.out / 'daily' / f'{DAY}.md'}",
    ]


def test_report는_돌_때마다_summary를_다시_쓴다(tmp_path: Path) -> None:
    t = _판(tmp_path)
    t.돌린다("daily")
    (t.out / "summary.txt").write_text("낡은 요약", encoding="utf-8")
    t.돌린다("report")
    assert t.요약().startswith(f"보고서 날짜: {DAY}\n")


# 지표 2~6


def _지표_판(tmp_path: Path) -> 판:
    t = _판(tmp_path)
    메인(
        t.projects,
        SID_A,
        [
            사람("2026-10-15T00:00:00Z"),
            응답("a1", "2026-10-15T00:01:00Z", 입력=1_000_000, effort="high"),
            응답("a2", "2026-10-15T00:02:00Z", 캐시읽기=1_000_000, 출력=100_000, effort="high"),
        ],
    )
    서브(
        t.projects,
        SID_A,
        "x1",
        [응답("s1", "2026-10-15T00:01:30Z", model=SONNET, 입력=1_000_000)],
        {"agentType": "Explore"},
    )
    메인(
        t.projects,
        SID_B,
        [
            응답(
                "b1",
                "2026-10-15T01:00:00Z",
                model=SONNET,
                쓰기1시간=1_000_000,
                effort="low",
                branch="feature/b",
            )
        ],
    )
    계정(t.out, [{"v": 1, "session_id": SID_A, "account_uuid": "u1", "email": "a@example.com"}])
    assert t.돌린다("daily") == 0
    return t


def test_합계와_계정별_비용(tmp_path: Path) -> None:
    report = _지표_판(tmp_path).일간()
    assert "모델 호출 4회, 환산 비용 $12.20" in report
    assert "| a@example.com | 8.20 | 67.2% | 3 |" in report
    assert "| 계정 모름 | 4.00 | 32.8% | 1 |" in report


def test_메인_세션과_서브에이전트(tmp_path: Path) -> None:
    report = _지표_판(tmp_path).일간()
    assert "| 메인 세션 | 10.20 | 83.6% | 3 |" in report
    assert "| 서브에이전트 | 2.00 | 16.4% | 1 |" in report


def test_모델과_노력별(tmp_path: Path) -> None:
    report = _지표_판(tmp_path).일간()
    rows = [
        ln for ln in report.split("## 4.")[1].split("## 5.")[0].splitlines() if ln.startswith("| ")
    ]
    assert rows[1:] == [
        "| 메인 세션 | opus-5-5 | high | 6.20 | 50.8% | 2 |",
        "| 메인 세션 | sonnet-5-5 | low | 4.00 | 32.8% | 1 |",
        "| 서브에이전트 | sonnet-5-5 | medium | 2.00 | 16.4% | 1 |",
    ]


def test_서브에이전트_유형별(tmp_path: Path) -> None:
    report = _지표_판(tmp_path).일간()
    assert "| Explore | 2.00 | 16.4% | 1 |" in report


def test_상위_세션(tmp_path: Path) -> None:
    report = _지표_판(tmp_path).일간()
    rows = [ln for ln in report.split("## 6.")[1].splitlines() if ln.startswith("| ")]
    assert rows[1:] == [
        "| aaaaaaaa | C--project-agent | feature/a | 2026-10-15 09:00 | 8.20 | 1,000,000 | 3 |",
        "| bbbbbbbb | C--project-agent | feature/b | 2026-10-15 10:00 | 4.00 | 1,000,000 | 1 |",
    ]


def test_세션_하나뿐인_하루도_셈이_끝난다(tmp_path: Path) -> None:
    t = _판(tmp_path)
    메인(t.projects, SID_A, [응답("m1", "2026-10-15T00:00:00Z", 입력=1_000_000)])
    assert t.돌린다("daily") == 0
    assert "| 메인 세션 | 4.00 | 100.0% | 1 |" in t.일간()
    assert "| 서브에이전트 | 0.00 | 0.0% | 0 |" in t.일간()


# 경보와 요약


def _날마다(t: 판, days: list[int], 마지막: int) -> None:
    """10월 days의 날마다 $4, 10월 15일에 $마지막(정수 달러)을 쓴다."""
    recs = [응답(f"d{d}", f"2026-10-{d:02}T03:00:00Z", 입력=1_000_000) for d in days]
    recs.append(응답("last", "2026-10-15T03:00:00Z", 입력=마지막 * 250_000))
    메인(t.projects, SID_A, recs)


def test_하루_비용이_지난_7일_중앙값의_1점5배를_넘으면_경보(tmp_path: Path) -> None:
    t = _판(tmp_path)
    _날마다(t, [8, 9, 10, 12, 14], 마지막=7)
    t.돌린다("daily")
    line = "경보: 환산 비용 $7.00이 지난 7일 가운데 호출이 있던 5일의 중앙값 $4.00의 1.5배를 넘는다"
    assert f"- {line}" in t.일간()
    assert line in t.요약().splitlines()


def test_1점5배를_넘지_않으면_비용_경보가_없다(tmp_path: Path) -> None:
    t = _판(tmp_path)
    _날마다(t, [8, 9, 10, 12, 14], 마지막=6)
    t.돌린다("daily")
    assert "경보 없음" in t.요약()
    assert "- 없음" in t.일간()


def test_호출이_있던_날이_넷보다_적으면_비교하지_않고_적는다(tmp_path: Path) -> None:
    t = _판(tmp_path)
    _날마다(t, [8, 10, 14], 마지막=20)
    t.돌린다("daily")
    assert (
        "- 비용 급증은 비교하지 않았다: 지난 7일 가운데 호출이 있던 날이 3일로 넷보다 적다"
        in t.일간()
    )
    assert "경보 없음" in t.요약()


def test_단가표에_없는_모델이면_경보(tmp_path: Path) -> None:
    t = _판(tmp_path)
    메인(
        t.projects,
        SID_A,
        [
            응답("m1", "2026-10-15T00:00:00Z", 입력=1_000_000),
            응답("m2", "2026-10-15T00:01:00Z", model="claude-mystery-1", 입력=1_000_000),
        ],
    )
    t.돌린다("daily")
    line = "경보: 단가표에 없는 모델의 호출 1회(claude-mystery-1)"
    assert line in t.요약().splitlines()
    assert "모델 호출 2회, 환산 비용 $4.00" in t.일간()


def test_요약은_여덟_줄_이하이고_첫_줄이_보고서_날짜다(tmp_path: Path) -> None:
    t = _판(tmp_path)
    _날마다(t, [8, 9, 10, 12, 14], 마지막=9)
    p = t.projects / FOLDER / f"{SID_B}.jsonl"
    body = json.dumps(응답("x", "2026-10-15T00:00:00Z", model="claude-mystery-1")) + "\n깨진 줄\n"
    p.write_text(body, encoding="utf-8")
    t.돌린다("daily")
    lines = t.요약().splitlines()
    assert len(lines) <= 8
    assert lines[0] == f"보고서 날짜: {DAY}"
    assert sum(ln.startswith("경보: ") for ln in lines) == 2
    assert lines[-1] == f"보고서: {t.out / 'daily' / f'{DAY}.md'}"


# 그 밖


def test_기록_폴더_이름은_주_체크아웃_경로에서_만든다() -> None:
    assert folder_name_of(Path("C:/project/agent")) == "C--project-agent"
    assert folder_name_of(Path("C:/project/agent/.claude/worktrees/x_y")) == (
        "C--project-agent--claude-worktrees-x-y"
    )


def test_앞선_달에_시작한_세션도_시작_시각이_보인다(tmp_path: Path) -> None:
    t = _판(tmp_path)
    메인(
        t.projects,
        SID_A,
        [사람("2026-08-20T00:00:00Z"), 응답("m1", "2026-10-15T00:00:00Z", 입력=1)],
    )
    t.돌린다("daily")
    assert sorted(p.name for p in (t.out / "ledger").iterdir()) == [
        "2026-08.jsonl",
        "2026-10.jsonl",
    ]
    assert "| aaaaaaaa | C--project-agent | feature/a | 2026-08-20 09:00 |" in t.일간()


def test_시간대를_바꿔_다시_돌려도_행이_겹치거나_빠지지_않는다(tmp_path: Path) -> None:
    # UTC로 9월 30일 20시는 +09:00에서 10월 1일이다. 같은 행이 다른 달 파일로 옮겨 간다.
    t = _판(tmp_path)
    p = 메인(t.projects, SID_A, [응답("m1", "2026-09-30T20:00:00Z", 입력=1_000_000)])
    t.돌린다("ingest")
    t.tz = "+00:00"
    now = time.time()
    os.utime(p, (now, now))
    t.돌린다("ingest")
    assert [r["id"] for r in t.호출()] == ["m1"]
    t.돌린다("report", today="2026-10-01")
    assert "모델 호출 1회, 환산 비용 $4.00" in t.일간("2026-09-30")


def test_시간대를_바꾼_증분이_읽지_않은_이웃_달_파일을_덮어쓰지_않는다(tmp_path: Path) -> None:
    # +09:00에서 8월 1일(UTC 7월 31일 15시)인 A의 행은 8월 파일에 든다. +00:00으로 B만 다시 읽으면
    # 8월과 9월 파일을 읽는데, 다시 읽지 않은 A의 행을 새 시간대로 7월에 옮겨 쓰면 읽지 않은 7월
    # 파일(C의 행)을 덮는다.
    t = _판(tmp_path)
    a = 메인(t.projects, SID_A, [응답("a1", "2026-07-31T15:30:00Z", 입력=1)])
    b = 메인(t.projects, SID_B, [응답("b1", "2026-09-15T00:00:00Z", 입력=1)])
    c = 메인(t.projects, SID_FORK, [응답("c1", "2026-07-10T00:00:00Z", 입력=1)])
    t.돌린다("ingest")
    old = time.time() - 3 * 86400
    for p in (a, c):
        os.utime(p, (old, old))
    t.tz = "+00:00"
    now = time.time()
    os.utime(b, (now, now))
    t.돌린다("ingest", today="2026-09-20")
    assert sorted(str(r["id"]) for r in t.호출()) == ["a1", "b1", "c1"]


def test_기록_폴더가_없으면_state를_올리지_않고_끝난다(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    t = _판(tmp_path)
    p = 메인(t.projects, SID_A, [응답("m1", "2026-10-15T00:00:00Z", 입력=1)])
    old = time.time() - 3 * 86400
    os.utime(p, (old, old))
    real = t.projects
    t.projects = tmp_path / "없는 폴더"
    assert t.돌린다("ingest") == 2
    assert "세션 기록 폴더가 없다" in capsys.readouterr().err
    assert not (t.out / "state.json").exists()
    t.projects = real
    t.돌린다("ingest")
    assert [r["id"] for r in t.호출()] == ["m1"]


def test_미래_날짜_보고서가_있어도_보고할_7일은_지우지_않는다(tmp_path: Path) -> None:
    t = _판(tmp_path)
    daily = t.out / "daily"
    daily.mkdir(parents=True)
    (daily / "2026-12-01.md").write_text("", encoding="utf-8")
    (daily / "2026-10-01.md").write_text("", encoding="utf-8")
    t.돌린다("report")
    names = sorted(p.name for p in daily.iterdir())
    assert names == [*(f"2026-10-{d:02}.md" for d in range(9, 16)), "2026-12-01.md"]


def test_첫_줄에만_시각이_없는_응답은_다음_줄의_시각으로_든다(tmp_path: Path) -> None:
    t = _판(tmp_path)
    첫 = 응답("m1", "", 입력=1, 출력=1)
    del 첫["timestamp"]
    메인(t.projects, SID_A, [첫, 응답("m1", "2026-10-15T00:00:05Z", 입력=1, 출력=9)])
    t.돌린다("daily")
    assert [(r["at"], r["output"]) for r in t.호출()] == [("2026-10-15T00:00:05Z", 9)]
    assert "경보 없음" in t.요약()


def test_주_체크아웃은_git_공용_디렉터리의_부모다() -> None:
    # 워크트리에서 돌면 워크트리가 아니라 주 체크아웃(.git이 폴더인 곳)이 나온다.
    assert (main_checkout() / ".git").is_dir()


def test_가상_환경_없이_도움말이_돈다() -> None:
    root = Path(__file__).resolve().parents[2]
    done = subprocess.run(
        ["uv", "run", "--no-project", "python", str(root / "tools" / "token_report.py"), "--help"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=120,
        check=False,
    )
    assert done.returncode == 0, done.stderr
    assert all(word in done.stdout for word in ("ingest", "report", "daily"))
