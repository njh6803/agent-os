"""tools/token_report.py. 가짜 세션 기록 폴더를 넣고 명령을 부른 뒤 장부와 보고서 파일을 본다.

이음매는 명령 하나다(`.scratch/token-usage/spec.md` 이음매, 사용자가 골랐다). 모든 시험은
`--today`와 `--tz`를 줘 벽시계에 기대지 않는다. 가격은 `claude-opus-5-5`(입력 $4, 출력 $20, 캐시
읽기 $0.20, 5분 쓰기 $5, 1시간 쓰기 $8, 백만 토큰당)와 `claude-sonnet-5-5`(입력 $2, 출력 $10, 캐시
읽기 $0.20)로 손으로 셈한다. 지표 7~12는 재료를 한 판(`_전부_판`)에 모아 절마다 단언한다.
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
from tools.hook_large_result import READ_LIMIT, SHELL_LIMIT, HookPayload, context_for
from tools.token_report import folder_name_of, main, main_checkout

OPUS = "claude-opus-5-5"
SONNET = "claude-sonnet-5-5"
SID_A = "aaaaaaaa-0000-0000-0000-000000000001"
SID_B = "bbbbbbbb-0000-0000-0000-000000000002"
SID_C = "cccccccc-0000-0000-0000-000000000003"
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


def 사람(at: str, text: str = "시작", *, origin: str | None = "human") -> Rec:
    """첫 사람 입력. 데스크톱 앱의 세션은 `origin.kind`가 `human`이고 헤드리스 세션은 `origin`이
    없다(그 판정의 근거는 도구의 `human_of`)."""
    rec: Rec = {"type": "user", "timestamp": at, "message": {"role": "user", "content": text}}
    if origin is not None:
        rec["origin"] = {"kind": origin}
    return rec


def 도구(tid: str, name: str, **inp: object) -> Rec:
    return {"type": "tool_use", "id": tid, "name": name, "input": inp}


def 결과(at: str, tid: str, text: str, *, is_error: bool = False) -> Rec:
    block: Rec = {"type": "tool_result", "tool_use_id": tid, "content": text}
    if is_error:
        block["is_error"] = True
    return {"type": "user", "timestamp": at, "message": {"role": "user", "content": [block]}}


def 첨부(at: str, attachment: Rec) -> Rec:
    return {"type": "attachment", "timestamp": at, "attachment": attachment}


def 압축(at: str, uid: str, trigger: str = "auto", *, pre: int | None = None) -> Rec:
    """압축 경계. `pre`는 Claude Code가 압축할 때 센 값(`preTokens`)이고 없으면 칸을 두지 않는다."""
    meta: Rec = {"trigger": trigger}
    if pre is not None:
        meta["preTokens"] = pre
    return {
        "type": "system",
        "subtype": "compact_boundary",
        "timestamp": at,
        "uuid": uid,
        "compactMetadata": meta,
    }


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
                "--repo",
                FOLDER,
            ]
        )

    def 장부(self) -> list[Rec]:
        rows: list[Rec] = []
        for p in sorted((self.out / "ledger").glob("????-??.jsonl")):
            body = p.read_text(encoding="utf-8")
            rows.extend(json.loads(x) for x in body.split("\n") if x)
        return rows

    def 호출(self) -> list[Rec]:
        return [r for r in self.장부() if r["kind"] == "call"]

    def 세션_행(self, sid: str) -> Rec:
        [row] = [r for r in self.장부() if r["kind"] == "session" and r["session"] == sid]
        return row

    def 칸(self, sid: str, key: str) -> list[Rec]:
        """세션 행의 목록 칸. JSON으로 다시 읽어 행의 모양으로 받는다."""
        rows: list[Rec] = json.loads(json.dumps(self.세션_행(sid)[key]))
        return rows

    def 장부_바이트(self) -> dict[str, bytes]:
        return {p.name: p.read_bytes() for p in sorted((self.out / "ledger").iterdir())}

    def 일간(self, day: str = DAY) -> str:
        return (self.out / "daily" / f"{day}.md").read_text(encoding="utf-8")

    def 요약(self) -> str:
        return (self.out / "summary.txt").read_text(encoding="utf-8")

    def 주간(self, week: str) -> str:
        return (self.out / "weekly" / f"{week}.md").read_text(encoding="utf-8")

    def 사주(self, weeks: str) -> str:
        return (self.out / "four-weeks" / f"{weeks}.md").read_text(encoding="utf-8")

    def 이름들(self, folder: str) -> list[str]:
        return sorted(p.name for p in (self.out / folder).iterdir())


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
        {
            "v": 1,
            "kind": "session",
            "session": SID_A,
            "start": "2026-10-15T00:00:00Z",
            "handoff": False,
            "human": True,
            "start_parts": {"skills": {}, "deferred_tools": 0, "instructions": 0, "other": 0},
            "large": [],
            "reads": [],
            "compactions": [],
            "prs": [],
        }
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
    assert [r["id"] for r in t.호출()] == ["m1"], "한 시간 전보다 앞선 파일을 다시 읽지 않음"
    now = time.time()
    os.utime(p, (now, now))
    t.돌린다("ingest")
    assert [r["id"] for r in t.호출()] == ["m1", "m2"], "한 시간 여유 안의 파일을 다시 읽음"


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
    ], "포크의 응답 주인"
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
    assert [r["id"] for r in t.호출()] == ["m1"], "synthetic 기록은 장부에 없음"
    assert "경보 없음" in t.요약()


def test_잘린_마지막_줄은_경보_없이_넘기고_깨진_줄은_경보다(tmp_path: Path) -> None:
    t = _판(tmp_path)
    메인(t.projects, SID_A, [응답("m1", "2026-10-15T00:00:00Z", 입력=1)], 끝='{"type": "assis')
    assert t.돌린다("daily") == 0
    assert "경보 없음" in t.요약(), "잘린 마지막 줄은 경보 없음"
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
    assert "| a@example.com | 8.00 | 80.0% | 2 |" in report, "null이 아닌 마지막 계정"
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


def _링크(target: Path, link: Path) -> bool:
    """폴더 링크. 윈도는 junction, 그 밖은 심볼릭 링크다. 만들지 못하면 거짓이다."""
    if sys.platform == "win32":
        import _winapi

        _winapi.CreateJunction(str(target), str(link))
        return True
    try:
        link.symlink_to(target, target_is_directory=True)
    except OSError:
        return False
    return True


@pytest.mark.parametrize(
    ("folder", "names"),
    [
        ("daily", ["2026-01-01.md", "2026-01-02.md.bak", "2026-01-03.md", "2026-01-04.md"]),
        ("weekly", ["2026-W01.md", "2026-W02.md.bak", "2026-W03.md", "2026-W04.md"]),
    ],
)
def test_보관_수를_넘은_보고서는_그_이름_모양의_파일만_지운다(
    tmp_path: Path, folder: str, names: list[str]
) -> None:
    old, bak, as_dir, as_link = names
    t = _판(tmp_path)
    reports = t.out / folder
    reports.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    target = outside / "keep.md"
    target.write_text("밖", encoding="utf-8")
    (reports / old).write_text("옛 보고서", encoding="utf-8")
    (reports / "notes.md").write_text("", encoding="utf-8")
    (reports / bak).write_text("", encoding="utf-8")
    (reports / as_dir).mkdir()
    links: list[Path] = []
    try:
        (reports / as_link).symlink_to(target)
        links.append(reports / as_link)
    except OSError:
        pass
    junction = reports / as_link.replace("4", "5")
    if sys.platform == "win32" and _링크(outside, junction):
        links.append(junction)
    assert links, "링크를 하나도 만들지 못했다"
    assert t.돌린다("report") == 0
    left = set(t.이름들(folder))
    assert old not in left
    assert {"notes.md", bak, as_dir} <= left
    assert {p.name for p in links} <= left, "보관을 넘은 링크를 지우지 않음"
    assert target.read_text(encoding="utf-8") == "밖"


@pytest.mark.parametrize("folder", ["daily", "weekly", "four-weeks"])
def test_보고서_폴더가_링크면_쓰지도_지우지도_않는다(
    tmp_path: Path, capsys: pytest.CaptureFixture[str], folder: str
) -> None:
    t = _판(tmp_path)
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "2026-01-01.md").write_text("밖", encoding="utf-8")
    (outside / "2026-W01.md").write_text("밖", encoding="utf-8")
    t.out.mkdir()
    assert _링크(outside, t.out / folder), "링크를 만들지 못했다"
    assert t.돌린다("report") == 2, "링크 폴더의 report 종료 코드"
    assert (
        f"보고서 폴더가 링크라 쓰지도 지우지도 않는다: {t.out / folder}" in capsys.readouterr().err
    )
    assert sorted(p.name for p in outside.iterdir()) == ["2026-01-01.md", "2026-W01.md"]
    assert not (t.out / "summary.txt").exists()


def test_보고서_폴더를_지운_뒤_report가_같은_파일을_다시_만든다(tmp_path: Path) -> None:
    t = _판(tmp_path)
    메인(t.projects, SID_A, [응답("m1", "2026-10-12T00:00:00Z", 입력=1)])
    t.돌린다("daily")
    folders = ("daily", "weekly", "four-weeks")
    before = {f: {p.name: p.read_bytes() for p in (t.out / f).iterdir()} for f in folders}
    summary = t.요약()
    for f in folders:
        for p in (t.out / f).iterdir():
            p.unlink()
        (t.out / f).rmdir()
    (t.out / "summary.txt").unlink()
    t.돌린다("report")
    assert {f: {p.name: p.read_bytes() for p in (t.out / f).iterdir()} for f in folders} == before
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


def test_보고서_머리는_한도의_차감을_usage에서_보라고_적는다(tmp_path: Path) -> None:
    t = _판(tmp_path)
    assert t.돌린다("daily") == 0
    assert (
        "구독 한도에서 무엇이 차감됐는지는 `/usage`의 플랜 사용량 내역"
        "(이 기계의 기록으로 어림한 값)을 본다." in t.일간()
    )


def test_압축의_요약_요청은_기록에_usage가_없어_비용에_들지_않는다(tmp_path: Path) -> None:
    """못 보는 것의 첫 항목. 요약 요청의 usage는 세션 기록에 없어 장부가 놓친다.

    압축 경계 앞뒤 기록에 usage가 없는 것은 2026-10-17에 이 PC의 세션 기록 일곱을 손으로 본
    것이다(usage가 든 것은 모델이 `<synthetic>`인 기록 하나, 일지 2026-10-17-04). 이 시험이 고정하는
    것은 비용이 usage가 든 응답의 합이라는 것이다. 압축 경계의 `preTokens`(압축 직전 컨텍스트의
    크기. 요약 요청이 읽는 양과 비슷하다고 어림한다) 100만은 비용에도 호출에도 들지 않는다.
    """
    t = _판(tmp_path)
    요약: Rec = {
        "type": "user",
        "timestamp": "2026-10-15T00:03:00Z",
        "isCompactSummary": True,
        "message": {"role": "user", "content": "이 세션은 앞선 대화를 요약해 잇는다."},
    }
    메인(
        t.projects,
        SID_A,
        [
            사람("2026-10-15T00:00:00Z"),
            응답("a1", "2026-10-15T00:01:00Z", 입력=1_000_000),
            압축("2026-10-15T00:02:00Z", "c1", pre=1_000_000),
            요약,
            응답("a2", "2026-10-15T00:04:00Z", 캐시읽기=1_000_000),
        ],
    )
    assert t.돌린다("daily") == 0
    assert "모델 호출 2회, 환산 비용 $4.20" in t.일간()


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
    assert _표(_절(_지표_판(tmp_path).일간(), 6)) == [
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
    """10월 days의 날마다 $4, 10월 15일에 $마지막(정수 달러)을 쓴다. 출력 토큰으로 써 세션
    컨텍스트가 0이라 40만 경보가 섞이지 않는다."""
    recs = [응답(f"d{d}", f"2026-10-{d:02}T03:00:00Z", 출력=200_000) for d in days]
    recs.append(응답("last", "2026-10-15T03:00:00Z", 출력=마지막 * 50_000))
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
    # 보고서는 4주 요약의 첫날 7일 앞(오늘이 10월 16일이면 8월 31일)부터 달 파일을 다 읽는다. 그보다
    # 앞선 6월 파일은 세션 행만 읽는다.
    t = _판(tmp_path)
    메인(
        t.projects,
        SID_A,
        [사람("2026-06-20T00:00:00Z"), 응답("m1", "2026-10-15T00:00:00Z", 입력=1)],
    )
    t.돌린다("daily")
    assert sorted(p.name for p in (t.out / "ledger").iterdir()) == [
        "2026-06.jsonl",
        "2026-10.jsonl",
    ]
    assert "| aaaaaaaa | C--project-agent | feature/a | 2026-06-20 09:00 |" in t.일간(), (
        "앞선 달 세션의 시작 시각"
    )


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
    assert t.돌린다("ingest") == 2, "기록 폴더 없는 ingest의 종료 코드"
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
    assert [(r["at"], r["output"]) for r in t.호출()] == [("2026-10-15T00:00:05Z", 9)], (
        "다음 줄 시각으로 든 응답"
    )
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


# 지표 7~12. 재료를 한 판에 모은다(명세 Testing Decisions). 날짜는 모두 2026-10-15이다.

BIG = "C:/project/agent/.claude/worktrees/x/tools/big.py"
BIG_KEY = "c:/project/agent/tools/big.py"
# 출처별 글자: (프로젝트·내장) 23, example-skills 31+13(이어지는 줄), anthropic-skills 28. 합 95.
스킬_목록 = "\n".join(
    [
        "- git-branch: 브랜치를 만든다",
        "- example-skills:pdf: PDF를 다룬다",
        "  설명이 이어지는 줄",
        "- anthropic-skills:docs: 문서",
    ]
)


def _시작_첨부(at: str) -> list[Rec]:
    """첫 호출 전의 첨부. 지연 도구 12자, 지침 파일 100자, 그 밖 40자(environment의 JSON).
    prompt_snapshot은 모델로 가지 않는 진단 기록이라 세지 않는다."""
    instructions: Rec = {"path": "C:/x/CLAUDE.md", "type": "Project", "content": "가" * 100}
    return [
        첨부(at, {"type": "skill_listing", "isInitial": True, "content": 스킬_목록}),
        첨부(at, {"type": "deferred_tools_delta", "addedLines": ["ToolA", "ToolB"]}),
        첨부(at, {"type": "instructions", "files": [instructions]}),
        첨부(at, {"type": "environment", "snapshot": "x"}),
        첨부(at, {"type": "prompt_snapshot", "systemPrompt": "긴" * 1000}),
    ]


def _전부_판(tmp_path: Path) -> 판:
    """A(feature/a): 큰 Read 둘(같은 파일, 둘째는 다시 읽기), 큰 Bash 하나(비밀이 든 명령),
    `gh pr create`, 86분 휴지 뒤의 캐시 재작성, 40만을 넘는 호출, 자동 압축. A의 서브에이전트 하나.
    B(feature/b): 인계 지시문으로 열렸다. C(feature/b). B와 C도 같은 파일을 읽어 셋이 읽은 파일이다.

    비용: A는 a1 $1, a2 $0.05, a3 $1, a4 $1, a5 $2(1시간 쓰기), a6 $2, a7 $1로 $8.05이고,
    서브에이전트·B·C가 $1씩이라 합계 $11.05다. 메인 세션 호출 아홉의 세션 컨텍스트는 a6만
    500,000이고 나머지는 250,000이다."""
    t = _판(tmp_path)
    secret_cmd = "TOKEN=s3cr3t curl -H 'Authorization: s3cr3t' https://example.com"
    a = [
        *_시작_첨부("2026-10-15T00:00:00Z"),
        사람("2026-10-15T00:00:00Z"),
        응답(
            "a1", "2026-10-15T00:01:00Z", 입력=250_000, content=[도구("tr1", "Read", file_path=BIG)]
        ),
        결과("2026-10-15T00:01:10Z", "tr1", "x" * 25_000),
        # 첫 호출 뒤의 첨부는 시작 구성에 들지 않는다.
        첨부("2026-10-15T00:01:20Z", {"type": "environment", "snapshot": "x"}),
        응답(
            "a2",
            "2026-10-15T00:02:00Z",
            캐시읽기=250_000,
            content=[도구("tr2", "Read", file_path=BIG)],
        ),
        결과("2026-10-15T00:02:10Z", "tr2", "y" * 25_000),
        응답(
            "a3",
            "2026-10-15T00:03:00Z",
            입력=250_000,
            content=[도구("tb1", "Bash", command=secret_cmd)],
        ),
        결과("2026-10-15T00:03:10Z", "tb1", "z" * 12_000),
        응답(
            "a4",
            "2026-10-15T00:04:00Z",
            입력=250_000,
            content=[도구("tp1", "Bash", command="gh pr create --title t --body b")],
        ),
        결과("2026-10-15T00:04:30Z", "tp1", "https://github.com/o/r/pull/1"),
        응답("a5", "2026-10-15T01:30:00Z", 쓰기1시간=250_000),
        응답("a6", "2026-10-15T01:35:00Z", 입력=500_000),
        # 압축 직전의 세션 컨텍스트는 마지막 호출(a6의 500,000)이 아니라 preTokens다.
        압축("2026-10-15T01:40:00Z", "cb1", pre=510_000),
        응답("a7", "2026-10-15T01:50:00Z", 입력=250_000),
    ]
    메인(t.projects, SID_A, a)
    서브(
        t.projects,
        SID_A,
        "x1",
        [응답("s1", "2026-10-15T00:30:00Z", model=SONNET, 입력=500_000)],
        {"agentType": "Explore"},
    )
    directive = "다음 작업: 티켓\n이어받을 상태: 인계: 커밋 뒤. 일지는 docs/journal/x.md\n"
    b = [
        *_시작_첨부("2026-10-15T02:00:00Z"),
        사람("2026-10-15T02:00:00Z", directive),
        응답(
            "b1",
            "2026-10-15T02:01:00Z",
            입력=250_000,
            branch="feature/b",
            content=[도구("tr3", "Read", file_path="C:/project/agent/tools/big.py")],
        ),
        결과("2026-10-15T02:01:10Z", "tr3", "b" * 100),
    ]
    메인(t.projects, SID_B, b)
    c = [
        *_시작_첨부("2026-10-15T03:00:00Z"),
        사람("2026-10-15T03:00:00Z"),
        응답(
            "c1",
            "2026-10-15T03:01:00Z",
            입력=250_000,
            branch="feature/b",
            content=[
                도구("tr4", "Read", file_path="C:\\project\\agent\\tools\\big.py"),
                도구("tp9", "Bash", command="gh pr create --fill"),
            ],
        ),
        결과("2026-10-15T03:01:10Z", "tr4", "c" * 100),
        # 실패한 PR 만들기는 PR이 아니다. feature/b는 PR 시각 모름이다.
        결과("2026-10-15T03:01:20Z", "tp9", "no commits", is_error=True),
    ]
    메인(t.projects, SID_C, c)
    assert t.돌린다("daily") == 0
    return t


def _절(report: str, n: int) -> str:
    return report.split(f"## {n}.")[1].split("\n## ")[0]


def _표(section: str) -> list[str]:
    """절 안 표들의 본문 줄. 머리 줄(다음 줄이 구분 줄인 것)은 뺀다."""
    lines = section.splitlines()
    heads = {i for i in range(len(lines) - 1) if lines[i + 1].startswith("|-")}
    return [ln for i, ln in enumerate(lines) if ln.startswith("| ") and i not in heads]


def test_세션_행은_인계와_시작_구성과_도구와_압축과_PR을_든다(tmp_path: Path) -> None:
    t = _전부_판(tmp_path)
    a = t.세션_행(SID_A)
    assert a["handoff"] is False
    assert t.세션_행(SID_B)["handoff"] is True
    assert a["start_parts"] == {
        "skills": {"(프로젝트·내장)": 23, "example-skills": 44, "anthropic-skills": 28},
        "deferred_tools": 12,
        "instructions": 100,
        "other": 40,
    }, "첫 호출 전의 시작 구성"
    assert a["large"] == [
        {
            "id": "tr1",
            "at": "2026-10-15T00:01:10Z",
            "tool": "Read",
            "chars": 25_000,
            "target": BIG,
            "carried": 5,
        },
        {
            "id": "tr2",
            "at": "2026-10-15T00:02:10Z",
            "tool": "Read",
            "chars": 25_000,
            "target": BIG,
            "carried": 4,
        },
        {
            "id": "tb1",
            "at": "2026-10-15T00:03:10Z",
            "tool": "Bash",
            "chars": 12_000,
            "target": "curl",
            "carried": 3,
        },
    ], "큰 결과의 실려 간 호출"
    assert a["reads"] == [
        {"id": "tr1", "at": "2026-10-15T00:01:10Z", "path": BIG, "chars": 25_000, "again": False},
        {"id": "tr2", "at": "2026-10-15T00:02:10Z", "path": BIG, "chars": 25_000, "again": True},
    ]
    assert a["compactions"] == [
        {"id": "cb1", "at": "2026-10-15T01:40:00Z", "trigger": "auto", "context": 510_000}
    ]
    assert a["prs"] == [{"at": "2026-10-15T00:04:30Z", "branch": "feature/a"}]


def test_Bash의_큰_결과는_프로그램_이름만_남고_명령의_비밀은_장부에_없다(tmp_path: Path) -> None:
    t = _전부_판(tmp_path)
    for p in [*(t.out / "ledger").iterdir(), *(t.out / "daily").iterdir()]:
        assert "s3cr3t" not in p.read_text(encoding="utf-8"), f"Bash 장부에 비밀이 남았다: {p}"
    assert "| Bash | 12,000 | 3 | curl | aaaaaaaa |" in t.일간(), (
        "Bash 큰 결과의 대상은 프로그램 이름"
    )


def test_PowerShell의_변수_대입을_벗기고_비밀을_남기지_않는다(tmp_path: Path) -> None:
    # 낱말 경계를 믿을 수 없는 대입(따옴표 없는 명령 치환, 이스케이프한 공백)과 따옴표에서 온 첫
    # 낱말은 남기지 않는다. 래퍼는 벗기지 않아 그 이름이 남는다(못 보는 것).
    t = _판(tmp_path)
    commands = [
        ("tp1", "PowerShell", "$env:K='s3cr3t'; Invoke-WebRequest -Headers @{a=$env:K} x"),
        ("tp2", "PowerShell", "$h = 's3cr3t'\nInvoke-RestMethod -Uri x"),
        ("tp3", "Bash", '"$HOME/s3cr3t/tool" --flag'),
        ("tp4", "Bash", "A=1 B='s3cr3t x' env=1 ./run.sh"),
        ("tp5", "Bash", "API_KEY=$(echo s3cr3t) curl x"),
        ("tp6", "Bash", "FOO=bar\\ s3cr3t curl x"),
        ("tp7", "Bash", "'s3cr3t' | gh auth login --with-token"),
        ("tp8", "PowerShell", '"tok-s3cr3t" | Set-Content k'),
        ("tp9", "PowerShell", "[Environment]::SetEnvironmentVariable('K','s3cr3t'); tool"),
        ("tpa", "Bash", "sudo curl x"),
        # here-string 안의 홀수 따옴표가 인용 상태를 흐려 그 뒤 비밀 줄이 조각으로 갈리던 길
        ("tpb", "PowerShell", "$cfg = @'\n# don't commit\ns3cr3t-key\n'@\nSet-Content .env $cfg"),
        ("tpc", "PowerShell", '$b = @"\nHe said "hi\ns3cr3t-tok\n"@\ngh x'),
        # 여러 줄 해시테이블은 다음 줄의 키를 프로그램으로 읽던 길
        (
            "tpd",
            "PowerShell",
            "$h = @{\nAuthorization = 'Bearer s3cr3t'\n}\nInvoke-RestMethod -H $h",
        ),
    ]
    recs: list[Rec] = []
    for i, (tid, name, cmd) in enumerate(commands):
        at = f"2026-10-15T00:{i:02}:00Z"
        recs += [
            응답(f"m{i}", at, 입력=1, content=[도구(tid, name, command=cmd)]),
            결과(at, tid, "o" * 10_001),
        ]
    메인(t.projects, SID_A, recs)
    assert t.돌린다("daily") == 0
    targets = [r["target"] for r in t.칸(SID_A, "large")]
    assert targets == [
        "Invoke-WebRequest",
        "Invoke-RestMethod",
        None,
        "./run.sh",
        None,
        None,
        None,
        None,
        None,
        "sudo",
        None,
        None,
        None,
    ], "PowerShell 큰 결과의 대상"
    for p in (t.out / "ledger").iterdir():
        assert "s3cr3t" not in p.read_text(encoding="utf-8"), p


def test_범위를_준_Read와_문턱까지의_결과는_큰_결과가_아니다(tmp_path: Path) -> None:
    t = _판(tmp_path)
    uses = [
        (도구("t1", "Read", file_path="a.py", limit=2000), 30_000),
        (도구("t2", "Read", file_path="b.py", offset=1), 30_000),
        (도구("t3", "Read", file_path="c.py"), 20_000),
        (도구("t4", "Bash", command="ls"), 10_000),
        (도구("t5", "PowerShell", command="dir"), 10_000),
        (도구("t6", "Read", file_path="d.py"), 20_001),
        (도구("t7", "Bash", command="ls"), 10_001),
    ]
    recs: list[Rec] = []
    for i, (use, n) in enumerate(uses):
        at = f"2026-10-15T00:0{i}:00Z"
        recs += [응답(f"m{i}", at, 입력=1, content=[use]), 결과(at, str(use["id"]), "o" * n)]
    메인(t.projects, SID_A, recs)
    assert t.돌린다("daily") == 0
    large = t.칸(SID_A, "large")
    assert [(r["id"], r["chars"]) for r in large] == [("t6", 20_001), ("t7", 10_001)], (
        "문턱까지와 범위를 준 결과는 큰 결과 아님"
    )


def _큰_결과_훅_입력(tool: str, inp: dict[str, object], chars: int) -> HookPayload:
    """큰 결과 알림 훅이 받는 PostToolUse 입력. 훅이 셈하는 글자 수가 `chars`가 되게 짓는다. Read는
    한 줄 본문에 줄 번호 접두 `1\\t`(2자)가 붙는다(그 훅의 `numbered_chars`). 훅처럼 JSON에서 읽어
    타입 밖의 값(`offset: null`)도 넣는다."""
    if tool == "Read":
        response: Rec = {"type": "text", "file": {"content": "o" * (chars - 2), "startLine": 1}}
    else:
        response = {"stdout": "o" * chars, "stderr": ""}
    raw: Rec = {"tool_name": tool, "tool_input": inp, "tool_response": response}
    payload: HookPayload = json.loads(json.dumps(raw))
    return payload


@pytest.mark.parametrize(
    ("tool", "limit"),
    [("Read", READ_LIMIT), ("Bash", SHELL_LIMIT), ("PowerShell", SHELL_LIMIT)],
    ids=["Read", "Bash", "PowerShell"],
)
def test_같은_크기의_결과를_큰_결과_알림_훅과_같이_판정한다(
    tmp_path: Path, tool: str, limit: int
) -> None:
    """06(큰 결과 알림 훅)이 먼저 병합되어, 두 문턱이 같은지 보는 시험을 이 티켓이 더한다(06 티켓).
    문턱은 훅의 상수에서 받아 어느 한쪽의 값만 바꿔도 빨개진다. 값만 대지 않고 문턱 그 자리, 한
    글자 위, 범위를 준 Read(`offset`만, `limit`만, 정수가 아닌 값)를 두 쪽에 넣어 비교(초과)와
    범위 판정까지 견준다. 장부는 기록 본문을, 훅은 구조화된 출력을 세는데 두 셈이 같은 값을 내는지는
    06의 프로브가 실제 페이로드로 봤다(03 티켓의 "메모(06에서)")."""
    target: dict[str, object] = {"file_path": "a.py"} if tool == "Read" else {"command": "ls"}
    cases: list[tuple[int, dict[str, object], bool]] = [(limit, {}, False), (limit + 1, {}, True)]
    if tool == "Read":
        ranged: list[tuple[int, dict[str, object], bool]] = [
            (limit + 1, {"offset": 1}, False),
            (limit + 1, {"limit": 100}, False),
            (limit + 1, {"offset": None}, False),
            (limit + 1, {"limit": None}, False),
            (limit + 1, {"offset": True, "limit": "1"}, False),
        ]
        cases += ranged
    t = _판(tmp_path)
    recs: list[Rec] = []
    for i, (chars, ranges, _) in enumerate(cases):
        at = f"2026-10-15T00:0{i}:00Z"
        use = 도구(f"t{i}", tool, **target, **ranges)
        recs += [응답(f"m{i}", at, 입력=1, content=[use]), 결과(at, f"t{i}", "o" * chars)]
    메인(t.projects, SID_A, recs)
    assert t.돌린다("daily") == 0
    ledger = [r["id"] for r in t.칸(SID_A, "large")]
    expected = [large for _, _, large in cases]

    assert [f"t{i}" in ledger for i in range(len(cases))] == expected, "장부의 판정"
    hook = [context_for(_큰_결과_훅_입력(tool, target | r, c)) is not None for c, r, _ in cases]
    assert hook == expected, "훅의 판정"


def test_7절은_40만을_넘은_세션과_자동_압축_직전의_세션_컨텍스트를_든다(tmp_path: Path) -> None:
    section = _절(_전부_판(tmp_path).일간(), 7)
    assert "세션 컨텍스트가 40만을 넘은 메인 세션 1개" in section
    assert "압축 자동 1회, 수동 0회" in section
    assert (
        "자동 압축 직전의 세션 컨텍스트: 최소 510,000, 중앙값 510,000, 최대 510,000" in section
    ), "자동 압축 직전의 세션 컨텍스트"


def test_8절은_60분_넘게_쉰_뒤_캐시를_다시_쓴_호출을_든다(tmp_path: Path) -> None:
    section = _절(_전부_판(tmp_path).일간(), 8)
    assert "1회, 캐시 쓰기 환산 비용 $2.00(전체 비용의 18.1%)" in section


def test_9절은_시작_컨텍스트와_출처별_스킬_목록을_든다(tmp_path: Path) -> None:
    section = _절(_전부_판(tmp_path).일간(), 9)
    assert "메인 세션 3개의 첫 호출 세션 컨텍스트 중앙값 250,000" in section
    assert _표(section) == [
        "| 스킬 목록 합 | 95 |",
        "| 스킬 목록: example-skills | 44 |",
        "| 스킬 목록: anthropic-skills | 28 |",
        "| 스킬 목록: (프로젝트·내장) | 23 |",
        "| 지연 도구 목록 | 12 |",
        "| 지침 파일 | 100 |",
        "| 그 밖 | 40 |",
    ], "9절의 출처별 스킬 목록"


def test_10절은_브랜치별_비용과_인계와_PR_앞뒤를_가른다(tmp_path: Path) -> None:
    section = _절(_전부_판(tmp_path).일간(), 10)
    assert _표(section) == [
        "| feature/a | 9.05 | 81.9% | 1 | 0 | 33.7% · 66.3% |",
        "| feature/b | 2.00 | 18.1% | 2 | 1 | PR 시각 모름 |",
    ]


def test_11절은_호출당_세션_컨텍스트와_캐시_읽기의_몫이다(tmp_path: Path) -> None:
    section = _절(_전부_판(tmp_path).일간(), 11)
    assert "메인 세션 호출 9회, 호출당 평균 세션 컨텍스트 277,778, 캐시 읽기의 몫 10.0%" in section


def test_12절은_큰_결과와_셋이_읽은_파일과_다시_읽기_후보다(tmp_path: Path) -> None:
    section = _절(_전부_판(tmp_path).일간(), 12)
    assert "문턱을 넘은 결과 3개" in section
    rows = _표(section)
    assert rows[:3] == [
        f"| Read | 25,000 | 5 | {BIG_KEY} | aaaaaaaa |",
        f"| Read | 25,000 | 4 | {BIG_KEY} | aaaaaaaa |",
        "| Bash | 12,000 | 3 | curl | aaaaaaaa |",
    ]
    assert rows[3:] == [f"| {BIG_KEY} | 3 | 4 | 50,200 |"]
    assert (
        f"다시 읽기 후보 1회 25,000자(Read 글자의 49.8%), 가장 많은 파일 {BIG_KEY} 25,000자"
        in section
    )


def test_40만을_넘은_세션이_있으면_경보(tmp_path: Path) -> None:
    t = _전부_판(tmp_path)
    assert "경보: 세션 컨텍스트가 40만을 넘은 세션 1개" in t.요약().splitlines(), "40만 경보"
    assert "- 경보: 세션 컨텍스트가 40만을 넘은 세션 1개" in _절(t.일간(), 1)


def _시작_판(tmp_path: Path, days: list[int], 오늘: int) -> 판:
    """10월 days의 날마다 시작 컨텍스트 100,000인 세션 하나, 15일에 오늘인 세션 하나."""
    t = _판(tmp_path)
    for d in days:
        sid = f"0000{d:04}-0000-0000-0000-000000000000"
        at = f"2026-10-{d:02}T03:00:00Z"
        메인(t.projects, sid, [사람(at), 응답(f"d{d}", at, 입력=100_000)])
    메인(
        t.projects,
        SID_A,
        [사람("2026-10-15T03:00:00Z"), 응답("last", "2026-10-15T03:00:00Z", 입력=오늘)],
    )
    assert t.돌린다("daily") == 0
    return t


def test_시작_컨텍스트_중앙값이_지난_7일보다_10퍼센트_넘게_크면_경보(tmp_path: Path) -> None:
    t = _시작_판(tmp_path, [8, 9, 10, 12], 오늘=110_001)
    line = (
        "경보: 시작 컨텍스트 중앙값 110,001이 지난 7일 가운데 시작한 세션이 있던 4일의"
        " 중앙값 100,000보다 10% 넘게 크다"
    )
    assert line in t.요약().splitlines()


def test_시작_컨텍스트가_10퍼센트까지_크면_경보가_없다(tmp_path: Path) -> None:
    t = _시작_판(tmp_path, [8, 9, 10, 12], 오늘=110_000)
    assert "경보 없음" in t.요약()


def test_시작한_세션이_있던_날이_넷보다_적으면_시작_컨텍스트를_비교하지_않는다(
    tmp_path: Path,
) -> None:
    t = _시작_판(tmp_path, [8, 9, 12], 오늘=300_000)
    assert "경보 없음" in t.요약()
    assert (
        "- 시작 컨텍스트는 비교하지 않았다: 지난 7일 가운데 시작한 세션이 있던 날이 3일로"
        " 넷보다 적다" in t.일간()
    )


def test_9절은_이_저장소와_그_워크트리의_세션만_센다(tmp_path: Path) -> None:
    t = _판(tmp_path)
    at = "2026-10-15T00:00:00Z"
    메인(t.projects, SID_A, [사람(at), 응답("m1", at, 입력=100)])
    메인(t.projects, SID_B, [사람(at), 응답("m2", at, 입력=300)], FOLDER + "--claude-x")
    메인(t.projects, SID_C, [사람(at), 응답("m3", at, 입력=900)], FOLDER + "-2")
    assert t.돌린다("daily") == 0
    assert "메인 세션 2개의 첫 호출 세션 컨텍스트 중앙값 200" in _절(t.일간(), 9), (
        "이 저장소 세션만의 9절"
    )


def test_9절과_시작_컨텍스트_경보는_헤드리스_세션을_따로_적는다(tmp_path: Path) -> None:
    t = _판(tmp_path)
    at = "2026-10-15T00:00:00Z"
    메인(t.projects, SID_A, [사람(at), 응답("m1", at, 입력=100)])
    메인(t.projects, SID_B, [사람(at, origin=None), 응답("m2", at, 입력=700)])
    메인(t.projects, SID_C, [사람(at, origin=None), 응답("m3", at, 입력=900)])
    assert t.돌린다("daily") == 0
    section = _절(t.일간(), 9)
    assert "사람이 연 이 저장소의 메인 세션 1개의 첫 호출 세션 컨텍스트 중앙값 100." in section, (
        "사람이 연 세션만의 중앙값"
    )
    assert "SDK, 칸이 없는 옛 행) 2개는 아래 중앙값에 넣지 않았다" in section
    assert "그 첫 호출 세션 컨텍스트 중앙값은 800이다." in section
    assert t.세션_행(SID_B)["human"] is False


def test_세션_하나뿐인_날도_시작_컨텍스트_중앙값을_낸다(tmp_path: Path) -> None:
    t = _판(tmp_path)
    at = "2026-10-15T00:00:00Z"
    메인(t.projects, SID_A, [사람(at), 응답("m1", at, 입력=1_000_000)])
    assert t.돌린다("daily") == 0
    assert "메인 세션 1개의 첫 호출 세션 컨텍스트 중앙값 1,000,000" in _절(t.일간(), 9)


def test_명령_위치의_gh_pr_create만_PR로_센다(tmp_path: Path) -> None:
    # 따옴표 안의 글(훅 시험의 페이로드)과 --help는 PR이 아니다. 명령 치환 안, 괄호 묶음, 래퍼 뒤,
    # 값이 -h인 옵션은 놓치고 heredoc 본문의 줄 머리는 센다(못 보는 것).
    t = _판(tmp_path)
    commands = [
        """echo '{"command":"gh pr create --fill"}' > p.json""",
        "PR_URL=$(gh pr create --fill) && echo $PR_URL",
        "gh pr create --help",
        "GH_TOKEN=x gh pr create --fill",
        "(gh pr create --fill)",
        "uv run gh pr create --fill",
        "gh pr create --title t --body '-h'",
        "cat <<'EOF'\ngh pr create --fill\nEOF",
        # 붙여 쓴 -H값은 머리로 읽지 않는다(다른 옵션의 값을 머리로 읽지 않게). 기록의 브랜치로
        # 센다.
        "gh pr create -Hme:feature/z --fill",
        # 줄 이음 뒤의 옵션도 같은 조각이다.
        "gh pr create --title x \\\n  --head feature/c",
        "gh pr create --fill \\\n  --dry-run",
    ]
    recs: list[Rec] = []
    for i, c in enumerate(commands):
        at = f"2026-10-15T00:{i:02}:00Z"
        recs += [
            응답(f"m{i}", at, 입력=1, content=[도구(f"t{i}", "Bash", command=c)]),
            결과(at, f"t{i}", "ok"),
        ]
    메인(t.projects, SID_A, recs)
    assert t.돌린다("daily") == 0
    assert t.칸(SID_A, "prs") == [
        {"at": "2026-10-15T00:03:00Z", "branch": "feature/a"},
        {"at": "2026-10-15T00:07:00Z", "branch": "feature/a"},
        {"at": "2026-10-15T00:08:00Z", "branch": "feature/a"},
        {"at": "2026-10-15T00:09:00Z", "branch": "feature/c"},
    ], "명령 위치의 gh pr create만 PR"


def test_PR의_브랜치는_head_인자를_기록의_브랜치보다_앞세운다(tmp_path: Path) -> None:
    # 주 체크아웃(main)에서 다른 브랜치의 PR을 연다. 앞 명령의 `curl -H`는 머리가 아니다.
    t = _판(tmp_path)
    cmd = "curl -H 'X: y' https://example.com; gh pr create --head \"me:feature/x\" --fill"
    메인(
        t.projects,
        SID_A,
        [
            응답("m1", "2026-10-15T00:00:00Z", 입력=1_000_000, branch="feature/x"),
            응답(
                "m2",
                "2026-10-15T00:10:00Z",
                입력=1,
                branch="main",
                content=[도구("p", "Bash", command=cmd)],
            ),
            결과("2026-10-15T00:10:05Z", "p", "https://github.com/o/r/pull/9"),
            응답("m3", "2026-10-15T00:20:00Z", 입력=1_000_000, branch="feature/x"),
        ],
    )
    mcp = "mcp__plugin_github_github__create_pull_request"
    메인(
        t.projects,
        SID_B,
        [
            응답(
                "b1",
                "2026-10-15T01:00:00Z",
                입력=1,
                branch="main",
                content=[도구("q", mcp, head="feature/y")],
            ),
            결과("2026-10-15T01:00:05Z", "q", "{}"),
        ],
    )
    assert t.돌린다("daily") == 0
    assert t.칸(SID_A, "prs") == [{"at": "2026-10-15T00:10:05Z", "branch": "feature/x"}], (
        "gh의 --head가 PR의 브랜치"
    )
    assert t.칸(SID_B, "prs") == [{"at": "2026-10-15T01:00:05Z", "branch": "feature/y"}], (
        "MCP의 head가 PR의 브랜치"
    )
    rows = _표(_절(t.일간(), 10))
    assert "| feature/x | 8.00 | 100.0% | 1 | 0 | 50.0% · 50.0% |" in rows
    assert "| main | 0.00 | 0.0% | 2 | 0 | PR 시각 모름 |" in rows


def test_새_칸이_없는_옛_세션_행은_모름으로_적는다(tmp_path: Path) -> None:
    t = _판(tmp_path)
    ledger = t.out / "ledger"
    ledger.mkdir(parents=True)
    rows: list[Rec] = [
        {"v": 1, "kind": "session", "session": SID_A, "start": "2026-10-15T00:00:00Z"},
        {
            "v": 1,
            "kind": "call",
            "id": "m1",
            "at": "2026-10-15T00:01:00Z",
            "session": SID_A,
            "agent": None,
            "project": FOLDER,
            "model": OPUS,
            "input": 1_000_000,
            "context": 1_000_000,
        },
    ]
    쓴다(ledger / "2026-10.jsonl", rows)
    assert t.돌린다("report") == 0
    report = t.일간()
    assert "모델 호출 1회, 환산 비용 $4.00" in report
    assert "새 칸이 없는 옛 세션 행 1개는 7·9·10·12절에서 모름이다" in report


# 대기열 273: 작은 입력의 시험


def _다시_읽기_판(tmp_path: Path, between: list[Rec]) -> 판:
    """세션마다 같은 파일을 읽고, between의 도구 호출 하나를 하고, 다시 읽는다."""
    t = _판(tmp_path)
    for i, use in enumerate(between):
        sid = f"{i:08}-0000-0000-0000-000000000000"
        recs = [
            응답(
                f"r{i}a",
                "2026-10-15T00:00:00Z",
                입력=1,
                content=[도구(f"a{i}", "Read", file_path="f.py")],
            ),
            결과("2026-10-15T00:00:01Z", f"a{i}", "o" * 10),
            응답(f"r{i}b", "2026-10-15T00:01:00Z", 입력=1, content=[use]),
            결과("2026-10-15T00:01:01Z", str(use["id"]), "끝"),
            응답(
                f"r{i}c",
                "2026-10-15T00:02:00Z",
                입력=1,
                content=[도구(f"c{i}", "Read", file_path="f.py")],
            ),
            결과("2026-10-15T00:02:01Z", f"c{i}", "o" * 10),
        ]
        메인(t.projects, sid, recs)
    assert t.돌린다("daily") == 0
    return t


def test_작업_트리를_바꾸지_않는_git_명령_뒤의_읽기는_다시_읽기_후보다(tmp_path: Path) -> None:
    commands = [
        "git merge-base origin/main HEAD",
        "git worktree list --porcelain",
        'git commit -m "merge reset switch pull stash"',
        "git -C ../x log --oneline",
        "echo git-merge",
        "git stash list",
    ]
    uses = [도구(f"g{i}", "Bash", command=c) for i, c in enumerate(commands)]
    t = _다시_읽기_판(tmp_path, uses)
    assert "다시 읽기 후보 6회 60자" in _절(t.일간(), 12)


def test_압축_뒤의_읽기는_다시_읽기_후보가_아니다(tmp_path: Path) -> None:
    t = _판(tmp_path)
    recs = [
        응답("r1", "2026-10-15T00:00:00Z", 입력=1, content=[도구("a", "Read", file_path="f.py")]),
        결과("2026-10-15T00:00:01Z", "a", "o" * 10),
        압축("2026-10-15T00:30:00Z", "cb"),
        응답("r2", "2026-10-15T01:00:00Z", 입력=1, content=[도구("c", "Read", file_path="f.py")]),
        결과("2026-10-15T01:00:01Z", "c", "o" * 10),
    ]
    메인(t.projects, SID_A, recs)
    assert t.돌린다("daily") == 0
    assert "다시 읽기 후보 0회 0자" in _절(t.일간(), 12), "압축 뒤의 읽기는 다시 읽기 아님"


def test_포크에_복사된_도구_결과와_압축은_한_번만_센다(tmp_path: Path) -> None:
    t = _판(tmp_path)
    copied = [
        응답("r1", "2026-10-15T00:01:00Z", 입력=1, content=[도구("big", "Read", file_path="f.py")]),
        결과("2026-10-15T00:01:10Z", "big", "o" * 30_000),
        압축("2026-10-15T00:20:00Z", "cb"),
    ]
    메인(t.projects, SID_A, [사람("2026-10-15T00:00:00Z"), *copied])
    메인(
        t.projects,
        SID_FORK,
        [사람("2026-10-15T00:30:00Z"), *copied, 응답("r2", "2026-10-15T00:40:00Z", 입력=1)],
    )
    assert t.돌린다("daily") == 0
    report = t.일간()
    assert "문턱을 넘은 결과 1개" in _절(report, 12), "포크에 복사된 큰 결과는 한 번"
    assert "| Read | 30,000 | 0 | f.py | aaaaaaaa |" in _절(report, 12)
    assert "압축 자동 1회, 수동 0회" in _절(report, 7), "포크에 복사된 압축은 한 번"
    # preTokens가 없는 압축은 그 앞 마지막 호출의 세션 컨텍스트(r1의 1)를 쓴다.
    assert [r["context"] for r in t.칸(SID_A, "compactions")] == [1]


def test_작업_트리를_바꾸는_git_명령이나_고친_파일_뒤의_읽기는_다시_읽기_후보가_아니다(
    tmp_path: Path,
) -> None:
    commands = [
        "git pull",
        "git -C ../x checkout main",
        "git -c core.longpaths=true merge --ff-only origin/main",
        "git worktree add ../w",
        "git stash push -u",
        "git --no-pager pull",
        "git revert HEAD",
        # 못 보는 것: 커밋 메시지 안의 `git merge` 글자도 걸린다(거짓 양성, 후보를 적게 센다).
        'git commit -m "fix: git merge 실패"',
    ]
    uses = [도구(f"g{i}", "Bash", command=c) for i, c in enumerate(commands)]
    uses.append(도구("e1", "Edit", file_path="F.py", old_string="a", new_string="b"))
    uses.append(도구("n1", "NotebookEdit", notebook_path="f.py", new_source="x"))
    t = _다시_읽기_판(tmp_path, uses)
    assert "다시 읽기 후보 0회 0자" in _절(t.일간(), 12)


def test_경로에_줄_구분_문자가_든_읽기도_장부를_다시_읽을_수_있다(tmp_path: Path) -> None:
    # json.dumps(ensure_ascii=False)는 U+2028을 그대로 쓴다. 읽는 쪽이 거기서 줄을 가르면 행이 깨져
    # 그 뒤 모든 ingest·report가 그 달 파일에서 죽는다(PR 직전 보안 리뷰가 함수를 불러 봤다).
    t = _판(tmp_path)
    path = f"a{chr(0x2028)}b.py"
    recs = [
        응답("r1", "2026-10-15T00:00:00Z", 입력=1, content=[도구("a", "Read", file_path=path)]),
        결과("2026-10-15T00:00:01Z", "a", "o" * 10),
    ]
    p = 메인(t.projects, SID_A, recs)
    assert t.돌린다("daily") == 0
    now = time.time()
    os.utime(p, (now, now))
    assert t.돌린다("daily") == 0
    assert [r["path"] for r in t.칸(SID_A, "reads")] == [path]


def test_실패한_Read_뒤의_범위_읽기는_다시_읽기_후보가_아니다(tmp_path: Path) -> None:
    # 너무 커서 실패한 범위 없는 읽기 뒤에 범위를 주어 읽는 흐름이다. 실패한 읽기는 Read로 세지도
    # 않는다.
    t = _판(tmp_path)
    recs = [
        응답("r1", "2026-10-15T00:00:00Z", 입력=1, content=[도구("a", "Read", file_path="f.py")]),
        결과("2026-10-15T00:00:01Z", "a", "너무 크다", is_error=True),
        응답(
            "r2",
            "2026-10-15T00:01:00Z",
            입력=1,
            content=[도구("c", "Read", file_path="f.py", offset=1, limit=100)],
        ),
        결과("2026-10-15T00:01:01Z", "c", "o" * 10),
    ]
    메인(t.projects, SID_A, recs)
    assert t.돌린다("daily") == 0
    assert "다시 읽기 후보 0회 0자(Read 글자의 0.0%)" in _절(t.일간(), 12), (
        "실패한 Read 뒤의 범위 읽기"
    )
    assert [r["id"] for r in t.칸(SID_A, "reads")] == ["c"]


# 주간과 4주 요약


def _날짜에(t: 판, days: list[str]) -> None:
    """날마다 $4(opus 입력 백만)인 메인 세션 하나."""
    for i, day in enumerate(days):
        sid = f"{i:08}-1111-0000-0000-000000000000"
        메인(t.projects, sid, [응답(f"w{i}", f"{day}T03:00:00Z", 입력=1_000_000)])


def test_주가_끝난_다음_날_주간_보고서가_난다(tmp_path: Path) -> None:
    t = _판(tmp_path)
    _날짜에(t, ["2026-10-12", "2026-10-18"])
    assert t.돌린다("daily", today="2026-10-18") == 0
    assert "2026-W42.md" not in t.이름들("weekly"), "끝나지 않은 주의 주간 보고서 없음"
    assert t.돌린다("report", today="2026-10-19") == 0
    assert t.이름들("weekly") == ["2026-W39.md", "2026-W40.md", "2026-W41.md", "2026-W42.md"]
    week = t.주간("2026-W42")
    assert week.startswith("# 토큰 사용 주간 보고서: 2026-W42(2026-10-12 ~ 2026-10-18)\n")
    assert "모델 호출 2회, 환산 비용 $8.00" in week
    trend = _표(_절(week, 13))
    assert len(trend) == 7
    assert trend[0].startswith("| 2026-10-12 | 1 | 4.00 |")
    assert trend[1].startswith("| 2026-10-13 | 0 | 0.00 |")
    assert trend[6].startswith("| 2026-10-18 | 1 | 4.00 |")


def test_주간은_최근_넷만_남고_4주_요약은_지우지_않는다(tmp_path: Path) -> None:
    t = _판(tmp_path)
    assert t.돌린다("daily", today="2026-10-19") == 0
    assert t.이름들("four-weeks") == ["2026-W37-W40.md"]
    assert t.돌린다("report", today="2026-11-09") == 0
    assert t.이름들("weekly") == ["2026-W42.md", "2026-W43.md", "2026-W44.md", "2026-W45.md"], (
        "주간은 최근 넷"
    )
    assert t.이름들("four-weeks") == ["2026-W37-W40.md", "2026-W41-W44.md"]


def test_4주_요약은_묶음이_끝난_뒤_주별_추이를_든다(tmp_path: Path) -> None:
    t = _판(tmp_path)
    _날짜에(t, ["2026-09-07", "2026-10-04", "2026-10-05"])
    assert t.돌린다("daily", today="2026-10-19") == 0
    group = t.사주("2026-W37-W40")
    assert group.startswith("# 토큰 사용 4주 요약: 2026-W37~W40(2026-09-07 ~ 2026-10-04)\n")
    assert "모델 호출 2회, 환산 비용 $8.00" in group
    assert [row.split(" | ")[0] for row in _표(_절(group, 13))] == [
        "| 2026-W37",
        "| 2026-W38",
        "| 2026-W39",
        "| 2026-W40",
    ]


def test_53주가_있는_해는_마지막_묶음에_53주를_넣는다(tmp_path: Path) -> None:
    t = _판(tmp_path)
    _날짜에(t, ["2026-11-30", "2027-01-03", "2027-01-04"])
    assert t.돌린다("daily", today="2027-01-03") == 0
    assert "2026-W49-W53.md" not in t.이름들("four-weeks"), "53주는 마지막 묶음"
    assert t.돌린다("report", today="2027-01-04") == 0
    assert "2026-W53.md" in t.이름들("weekly")
    group = t.사주("2026-W49-W53")
    assert group.startswith("# 토큰 사용 4주 요약: 2026-W49~W53(2026-11-30 ~ 2027-01-03)\n")
    assert "모델 호출 2회, 환산 비용 $8.00" in group
    assert len(_표(_절(group, 13))) == 5


def test_주간_보고서의_경보_절은_날마다의_경보를_모은다(tmp_path: Path) -> None:
    t = _판(tmp_path)
    메인(t.projects, SID_A, [응답("m1", "2026-10-14T03:00:00Z", 입력=500_000)])
    assert t.돌린다("daily", today="2026-10-19") == 0
    alarms = _절(t.주간("2026-W42"), 1)
    assert "- 2026-10-14: 경보: 세션 컨텍스트가 40만을 넘은 세션 1개" in alarms
