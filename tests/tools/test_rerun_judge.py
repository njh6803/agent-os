"""tools/rerun_judge.py 검증. 다시 풀기 판정의 쓰는 회차, 수와 후보, 결론 없음, 되풀이와 탐색, 사전
등록 절 꺼내기와 명령 줄 입구.

입력은 01의 쓰는 함수(`write_task_list`, `write_record`)로 지은 과제 목록과 회차 기록, 그리고 지은
README 글이다. 결론 없음이 아닌 사례는 그 글의 해시를 판정 함수에 넘긴다. 해시 상수의 값은 단언하지
않는다. 티켓 11이 실제 값을 넣은 뒤에도 초록이어야 한다.
"""

from __future__ import annotations

import hashlib
import os
import subprocess
import sys
from collections.abc import Callable, Iterable, Mapping
from dataclasses import replace
from pathlib import Path

import pytest
import tools.rerun_judge as rerun_judge
from tools.rerun_files import (
    ARMS,
    END_CAPPED,
    END_DONE,
    END_NOT_MEASURED,
    GATE_COMMANDS,
    LIST_MAIN,
    LIST_PILOT,
    RULE_BRANCH,
    SETUP_COMMANDS,
    TIER_LARGE,
    TIER_PILOT,
    TIER_SMALL,
    End,
    Gate,
    Hidden,
    Outcome,
    Record,
    Session,
    SetupFailure,
    Spend,
    Substitute,
    Task,
    TaskList,
    Tokens,
    Window,
    judge_view,
    round_dir_name,
    write_record,
    write_task_list,
)
from tools.rerun_judge import (
    PREREG_END,
    PREREG_START,
    ArmRow,
    Judgment,
    Selection,
    claude_code_cost,
    judge_files,
    main,
    prereg_section,
    ratio_interval,
    select_rounds,
    solved,
)

ROOT = Path(__file__).resolve().parents[2]
B = "a" * 40
M = "b" * 40
VERSION = "2.1.302 (Claude Code)"
README = f"# 프로브\n\n{PREREG_START}\n정의\n{PREREG_END}\n\n## 결과\n"
README_SHA256 = "d9397809054f83997ec9e0637bc6028338880d8db674f0c973c5146e01a48fcf"  # "\n정의\n"


def _과제_id(번호: int) -> str:
    return f"model-rerun-{번호:02d}"


def _과제(번호: int, *, tier: str = TIER_SMALL, original: str | None = None) -> Task:
    return Task(
        task_id=_과제_id(번호),
        ticket=f".scratch/x/issues/{번호:02d}-x.md",
        base=B,
        merge=M,
        branch=f"feature/{번호:02d}-x",
        tier=tier,
        size=번호,
        order=번호,
        pilot=False,
        pr_cost_usd=10.0,
        round_cap_usd=40.0,
        hidden_tests=(
            "tests/test_t.py::test_a",
            "tests/test_t.py::test_b",
            "tests/test_t.py::test_c",
        ),
        support_files=(),
        original_model_effort=original,
        arm_plan=tuple(a.name for a in ARMS),
    )


def _회차(
    번호: int,
    arm: str,
    *,
    cost: float = 10.0,
    official: float | None = None,
    gates: bool = True,
    hidden: bool = True,
    end: str = END_DONE,
    reason: str | None = None,
    round_no: int = 1,
    condition: int = 1,
    pilot: bool = False,
    interventions: int = 0,
    asked: bool = False,
    version: str = VERSION,
) -> Record:
    done = end == END_DONE
    outcome = Outcome(
        commit=None, rule=None, commits_after_base=None, setup_failure=None, gates=None, hidden=None
    )
    if done:
        outcome = Outcome(
            commit=M,
            rule=RULE_BRANCH,
            commits_after_base=1,
            setup_failure=None,
            gates=tuple(
                Gate(command=c, exit_code=0 if gates or i < 2 else 1, timed_out=False)
                for i, c in enumerate(GATE_COMMANDS)
            ),
            hidden=Hidden(passed=3, total=3, failed=())
            if hidden
            else Hidden(passed=2, total=3, failed=("tests/test_t.py::test_c",)),
        )
    return Record(
        task_id=_과제_id(번호),
        arm=arm,
        round_no=round_no,
        condition_version=condition,
        pilot=pilot,
        round_dir_name=round_dir_name(_과제_id(번호), arm, round_no, "t1"),
        claude_version=version,
        account="njh6803",
        env_names=("PATH",),
        init_tools=("Bash",),
        sessions=(),
        handoffs=0,
        interventions=interventions,
        asked_at_end=asked,
        end=End(kind=end, reason=reason, resets_at=None),
        outcome=outcome,
        spend=Spend(
            claude_code_usd=cost,
            official_usd=cost if official is None else official,
            other_usd=0.0,
            tokens=Tokens(input=1, output=10, cache_read=100, cache_write=5, thinking=4),
            substitutes=(),
            wall_seconds=60.0,
            denied_calls=0,
            utilization_start=(),
            utilization_end=(),
            contamination=(),
            model_mismatch=(),
        ),
    )


def _갈래마다(
    과제수: int,
    cost: Mapping[str, float],
    *,
    unsolved: Mapping[str, Iterable[int]] | None = None,
    more_interventions: Mapping[str, Iterable[int]] | None = None,
) -> list[Record]:
    """과제 `과제수`개에 다섯 갈래의 회차를 하나씩 짓는다. `unsolved`의 과제는 게이트가 빨갛고,
    `more_interventions`의 과제는 개입이 하나다(A는 늘 0)."""
    못풂 = {a: set(v) for a, v in (unsolved or {}).items()}
    개입 = {a: set(v) for a, v in (more_interventions or {}).items()}
    return [
        _회차(
            n,
            a.name,
            cost=cost[a.name],
            gates=n not in 못풂.get(a.name, set()),
            interventions=1 if n in 개입.get(a.name, set()) else 0,
        )
        for n in range(과제수)
        for a in ARMS
    ]


def _판정(
    tmp_path: Path,
    records: Iterable[Record],
    *,
    tasks: Iterable[Task] | None = None,
    과제수: int = 6,
    readme: str = README,
    expected: str = README_SHA256,
) -> Judgment:
    tasks_path, records_dir, readme_path = _파일(tmp_path, records, tasks, 과제수, readme)
    return judge_files(tasks_path, records_dir, readme_path, expected)


def _파일(
    tmp_path: Path,
    records: Iterable[Record],
    tasks: Iterable[Task] | None = None,
    과제수: int = 6,
    readme: str = README,
) -> tuple[Path, Path, Path]:
    """과제 목록, 기록 폴더, README를 지어 그 경로를 낸다."""
    task_list = TaskList(
        kind=LIST_MAIN,
        tasks=tuple(tasks) if tasks is not None else tuple(_과제(n) for n in range(과제수)),
    )
    tasks_path = tmp_path / "tasks.json"
    write_task_list(tasks_path, task_list)
    records_dir = tmp_path / "records"
    records_dir.mkdir()
    for r in records:
        write_record(records_dir, r)
    readme_path = tmp_path / "README.md"
    readme_path.write_text(readme, encoding="utf-8", newline="\n")
    return tasks_path, records_dir, readme_path


def _줄(j: Judgment, arm: str) -> ArmRow:
    return next(r for r in j.main.rows if r.arm == arm)


# --- 사전 등록 절 ---


def test_사전_등록_절은_두_표지_사이의_글이다() -> None:
    글 = f"머리\n{PREREG_START}\n정의 하나\n정의 둘\n{PREREG_END}\n꼬리\n"
    assert prereg_section(글) == "\n정의 하나\n정의 둘\n"


def test_사전_등록_표지가_없거나_하나뿐이면_절이_없다() -> None:
    assert prereg_section("표지 없음\n") is None
    assert prereg_section(f"{PREREG_START}\n정의\n") is None
    assert prereg_section(f"정의\n{PREREG_END}\n") is None
    assert prereg_section(f"{PREREG_END}\n정의\n{PREREG_START}\n") is None


def test_사전_등록_표지가_둘_이상이면_절이_없다() -> None:
    # 글 속 문장이 표지를 적으면 그 문장의 두 표지 사이가 절로 읽힌다. 첫 판의 README 머리가 그랬다.
    문장 = f"판정 도구가 `{PREREG_START}`·`{PREREG_END}` 사이를 대 본다.\n"
    assert prereg_section(f"{문장}{PREREG_START}\n정의\n{PREREG_END}\n") is None
    assert prereg_section(f"{PREREG_START}\n정의\n{PREREG_END}\n{PREREG_END}\n") is None
    assert prereg_section(f"{PREREG_START}\n{PREREG_START}\n정의\n{PREREG_END}\n") is None


def test_사전_등록_표지가_줄_안에_섞여도_하나씩이면_절로_받는다() -> None:
    # 못 보는 것: 절이 없는 글의 한 문장이 두 표지를 적으면 그 사이를 절로 읽는다. 저장소의 README는
    # 아래 시험이 지킨다.
    assert prereg_section(f"a {PREREG_START}x{PREREG_END} b\n") == "x"


def _README_표지_어긋남(글: str) -> list[str]:
    """README 글이 표지의 두 약속을 어긴 자리. 표지가 든 줄은 표지뿐이고, 표지가 있으면 절로
    꺼내진다."""
    든_줄 = [줄 for 줄 in 글.splitlines() if PREREG_START in 줄 or PREREG_END in 줄]
    어긋남 = [
        f"표지가 다른 글과 한 줄에 있다: {줄}"
        for 줄 in 든_줄
        if 줄.strip() not in (PREREG_START, PREREG_END)
    ]
    if 든_줄 and prereg_section(글) is None:
        어긋남.append(f"표지가 {len(든_줄)}줄에 있는데 절로 꺼내지지 않는다")
    return 어긋남


def test_README_표지_약속의_어긋남을_잡는다() -> None:
    절 = f"{PREREG_START}\n정의\n{PREREG_END}\n"
    assert _README_표지_어긋남(절) == []
    assert _README_표지_어긋남("표지 없음\n") == []
    # 절이 없을 때 한 문장이 두 표지를 적으면 판정 도구가 그 사이를 절로 받는다. 첫 판의 README
    # 머리가 그랬다.
    assert _README_표지_어긋남(f"글 `{PREREG_START}`·`{PREREG_END}` 문장\n") != []
    # 표지를 홀로 한 줄에 적은 예시가 하나 더 들면 표지가 둘이 되어 판정이 결론 없음으로
    # 멈춘다.
    assert _README_표지_어긋남(f"{절}예시\n{PREREG_START}\n") != []
    assert _README_표지_어긋남(f"{PREREG_START}\n정의\n") != []


def test_이_저장소의_프로브_README가_표지_약속을_지킨다() -> None:
    assert _README_표지_어긋남(rerun_judge.PREREG_README.read_text(encoding="utf-8")) == []


def test_시험의_README_해시는_절_내용의_SHA_256_이다() -> None:
    section = prereg_section(README)
    assert section is not None
    assert hashlib.sha256(section.encode("utf-8")).hexdigest() == README_SHA256


# --- 수 ---


def test_갈래마다_푼_수와_비용의_합과_푼_과제_하나의_비용과_비용_비를_낸다(tmp_path: Path) -> None:
    records = _갈래마다(
        6, {"A": 10.0, "B": 6.0, "C": 9.0, "D": 12.0, "E": 3.0}, unsolved={"B": [0], "E": range(6)}
    )
    j = _판정(tmp_path, records)
    assert j.tasks == tuple(_과제_id(n) for n in range(6))
    a, b, e = _줄(j, "A"), _줄(j, "B"), _줄(j, "E")
    assert (a.solved, a.cost, a.unit, a.ratio) == (6, 60.0, 10.0, 1.0)
    assert (b.solved, b.cost, b.unit) == (5, 36.0, 7.2)
    assert b.ratio == pytest.approx(0.72)
    assert (e.solved, e.cost, e.unit, e.ratio) == (0, 18.0, None, None)


def test_풀었다는_끝남이고_게이트가_초록이고_숨은_시험이_모두_통과한_것이다(tmp_path: Path) -> None:
    records = _갈래마다(6, {a.name: 10.0 for a in ARMS})
    바꿀 = {
        (0, "B"): _회차(0, "B", hidden=False),
        (1, "B"): _회차(1, "B", gates=False),
        (2, "B"): _회차(2, "B", end=END_CAPPED, reason="예산"),
    }
    records = [바꿀.get((int(r.task_id[-2:]), r.arm), r) for r in records]
    j = _판정(tmp_path, records)
    assert _줄(j, "B").solved == 3
    assert _줄(j, "B").capped == 1


# --- 쓰는 회차 ---


def _모두(cost: float = 10.0, 과제수: int = 7) -> list[Record]:
    return _갈래마다(과제수, {a.name: cost for a in ARMS})


def _빠진(j: Judgment) -> dict[str, str]:
    return {x.task_id: x.reason for x in j.excluded}


def test_파일럿_회차는_읽되_셈에_넣지_않는다(tmp_path: Path) -> None:
    # 파일럿 표시가 있는 회차가 조건 판을 올리거나 비용을 바꾸면 안 된다.
    records = [*_모두(), _회차(0, "B", cost=999.0, round_no=2, condition=2, pilot=True)]
    j = _판정(tmp_path, records, 과제수=7)
    assert _과제_id(0) in j.tasks
    assert _줄(j, "B").cost == 70.0


def test_과제마다_가장_큰_조건_판의_회차만_쓴다(tmp_path: Path) -> None:
    records = [
        *_모두(),
        *(_회차(0, a.name, cost=20.0, round_no=2, condition=2) for a in ARMS),
    ]
    j = _판정(tmp_path, records, 과제수=7)
    assert _과제_id(0) in j.tasks
    assert _줄(j, "A").cost == 80.0


def test_가장_큰_조건_판에_측정인_회차가_없는_갈래가_있으면_과제를_뺀다(tmp_path: Path) -> None:
    records = [
        *_모두(),
        *(_회차(0, a, cost=20.0, round_no=2, condition=2) for a in ("A", "B", "C")),
        _회차(0, "D", round_no=2, condition=2, end=END_NOT_MEASURED, reason="한도"),
    ]
    j = _판정(tmp_path, records, 과제수=7)
    assert _과제_id(0) not in j.tasks
    assert _빠진(j) == {_과제_id(0): "조건 판 2에 측정인 회차가 없는 갈래: D, E"}
    assert _줄(j, "A").cost == 60.0


def test_같은_조건_판에_측정인_회차가_둘이면_회차_번호가_가장_작은_것을_쓴다(
    tmp_path: Path,
) -> None:
    records = [r for r in _모두() if (r.task_id, r.arm) != (_과제_id(0), "B")]
    records += [
        _회차(0, "B", round_no=1, end=END_NOT_MEASURED, reason="오염"),
        _회차(0, "B", cost=50.0, round_no=3),
        _회차(0, "B", cost=5.0, round_no=2),
    ]
    j = _판정(tmp_path, records, 과제수=7)
    assert _줄(j, "B").cost == 65.0


def test_쓰는_회차_사이에_claude_판이_다르면_과제를_뺀다(tmp_path: Path) -> None:
    records = [r for r in _모두() if (r.task_id, r.arm) != (_과제_id(1), "D")]
    records.append(_회차(1, "D", version="2.1.303 (Claude Code)"))
    j = _판정(tmp_path, records, 과제수=7)
    assert _과제_id(1) not in j.tasks
    assert _빠진(j) == {
        _과제_id(1): "claude 판이 갈래 사이에 다르다: 2.1.302 (Claude Code), 2.1.303 (Claude Code)"
    }


def test_본_측정의_회차가_없는_과제도_까닭과_함께_뺀_과제로_적는다(tmp_path: Path) -> None:
    # 과제 6은 파일럿 회차만 있고 과제 7은 회차가 없다.
    records = [*_모두(과제수=6), *(_회차(6, a.name, pilot=True) for a in ARMS)]
    j = _판정(tmp_path, records, 과제수=8)
    assert _빠진(j) == {_과제_id(6): "본 측정의 회차가 없다", _과제_id(7): "본 측정의 회차가 없다"}
    assert f"- 뺀 과제 {_과제_id(7)}: 본 측정의 회차가 없다" in j.text


def test_과제_목록에_없는_과제의_기록은_세지_않는다(tmp_path: Path) -> None:
    records = [*_모두(과제수=6), *(_회차(9, a.name, cost=999.0) for a in ARMS)]
    j = _판정(tmp_path, records, 과제수=6)
    assert j.tasks == tuple(_과제_id(n) for n in range(6))
    assert _빠진(j) == {}
    assert _줄(j, "A").cost == 60.0


def test_기록_폴더에서_이름이_기록_꼴이_아닌_파일은_넘긴다(tmp_path: Path) -> None:
    tasks_path, records_dir, readme_path = _파일(tmp_path, _모두(과제수=6), 과제수=6)
    (records_dir / "메모.txt").write_text("기록이 아니다", encoding="utf-8")
    j = judge_files(tasks_path, records_dir, readme_path, README_SHA256)
    assert j.tasks == tuple(_과제_id(n) for n in range(6))


def test_판을_모르는_회차가_있으면_같은지_알_수_없어_과제를_뺀다(tmp_path: Path) -> None:
    # 과제 1은 모든 갈래의 판을 모르고, 과제 2는 D만 모른다. 모두 모르면 판이 하나로 모여도 뺀다.
    def 모름(r: Record) -> Record:
        빈다 = r.task_id == _과제_id(1) or (r.task_id, r.arm) == (_과제_id(2), "D")
        return replace(r, claude_version=None) if 빈다 else r

    j = _판정(tmp_path, [모름(r) for r in _모두()], 과제수=7)
    assert _빠진(j) == {
        _과제_id(1): "claude 판을 모르는 갈래: A, B, C, D, E",
        _과제_id(2): "claude 판을 모르는 갈래: D",
    }


# --- 구간 ---


def _흩어진(과제수: int = 8) -> list[Record]:
    """과제마다 비용이 다르고 갈래마다 못 푼 과제가 달라 구간이 한 점이 아닌 회차."""
    배수 = {"A": 10.0, "B": 7.0, "C": 5.0, "D": 4.0, "E": 3.0}
    못풂 = {"A": {7}, "B": {1}, "C": {2, 5}, "D": {0, 3}, "E": {4, 6}}
    return [
        _회차(n, a.name, cost=배수[a.name] * (1 + n), gates=n not in 못풂[a.name])
        for n in range(과제수)
        for a in ARMS
    ]


def _고르기(records: Iterable[Record], 과제수: int) -> Selection:
    return select_rounds([_과제_id(n) for n in range(과제수)], [judge_view(r) for r in records])


def test_비용_비가_과제마다_같으면_구간은_그_한_점이다(tmp_path: Path) -> None:
    j = _판정(tmp_path, _갈래마다(6, {"A": 10.0, "B": 5.0, "C": 10.0, "D": 20.0, "E": 10.0}))
    assert _줄(j, "B").interval == (0.5, 0.5)
    assert _줄(j, "A").interval == (1.0, 1.0)


def test_갈래를_도는_차례를_바꿔도_구간이_같다(tmp_path: Path) -> None:
    records = _흩어진()
    selection = _고르기(records, 8)
    앞 = {a: ratio_interval(selection, a, claude_code_cost, solved) for a in "BCDE"}
    뒤 = {a: ratio_interval(selection, a, claude_code_cost, solved) for a in "EDCB"}
    assert 앞 == 뒤
    assert len({앞[a] for a in "BCDE"}) == 4  # 갈래마다 구간이 달라 같은 값을 견준 것이 아니다
    j = _판정(tmp_path, records, 과제수=8)
    assert {a: _줄(j, a).interval for a in "BCDE"} == 앞


def test_다시_뽑은_표본에서_S_k_가_0_인_것이_5퍼센트를_넘으면_셀_수_없음이다(
    tmp_path: Path,
) -> None:
    # B는 여섯 가운데 하나만 푼다. 그 과제가 뽑히지 않을 확률은 (5/6)^6, 약 33%다.
    records = _갈래마다(
        6, {"A": 10.0, "B": 1.0, "C": 5.0, "D": 5.0, "E": 5.0}, unsolved={"B": range(1, 6)}
    )
    j = _판정(tmp_path, records)
    assert _줄(j, "B").interval is None
    assert _줄(j, "C").interval == (0.5, 0.5)
    assert not _줄(j, "B").candidate  # 셀 수 없는 갈래는 셋째 조건을 맞지 못한다
    assert "셀 수 없음" in j.text


def test_다시_뽑은_표본에서_S_A_가_0_인_것이_5퍼센트를_넘으면_모든_갈래가_셀_수_없음이다(
    tmp_path: Path,
) -> None:
    records = _갈래마다(
        6,
        {"A": 10.0, "B": 1.0, "C": 5.0, "D": 5.0, "E": 5.0},
        unsolved={"A": range(1, 6), "B": range(1, 6)},
    )
    j = _판정(tmp_path, records)
    assert all(_줄(j, a).interval is None for a in "ABCDE")
    # B는 S_B ≥ S_A − 1이고 개입도 없지만 셋째 조건을 맞지 못한다.
    assert not _줄(j, "B").candidate


def test_A_의_비용이_0_이면_나눌_수_없어_모든_갈래가_셀_수_없음이다(tmp_path: Path) -> None:
    j = _판정(tmp_path, _갈래마다(6, {"A": 0.0, "B": 1.0, "C": 1.0, "D": 1.0, "E": 1.0}))
    assert all(_줄(j, a).interval is None and _줄(j, a).ratio is None for a in "ABCDE")
    assert j.main.pick is None


# --- 후보와 결론 ---


def test_후보_조건_셋을_모두_맞는_갈래_가운데_U_k_가_가장_작은_갈래가_새_칸이다(
    tmp_path: Path,
) -> None:
    records = _갈래마다(
        6,
        {"A": 10.0, "B": 8.0, "C": 3.0, "D": 1.0, "E": 2.0},
        unsolved={"C": [0], "D": [0, 1]},
        more_interventions={"E": [0, 1, 2]},
    )
    j = _판정(tmp_path, records)
    assert {r.arm: r.candidate for r in j.main.rows} == {
        "A": False,
        "B": True,
        "C": True,
        "D": False,  # S_D 4 < S_A − 1
        "E": False,  # 개입이 A보다 많은 과제 셋
    }
    assert _줄(j, "E").more_interventions == 3
    assert j.main.pick == "C"
    assert j.blockers == ()
    assert j.conclusion == "새 칸: Opus 5.5 / medium (갈래 C)"


def test_후보의_U_k_가_같으면_갈래_차례의_앞을_고른다(tmp_path: Path) -> None:
    j = _판정(tmp_path, _갈래마다(6, {"A": 10.0, "B": 10.0, "C": 5.0, "D": 5.0, "E": 10.0}))
    assert [r.arm for r in j.main.rows if r.candidate] == ["C", "D"]
    assert j.main.pick == "C"


def test_S_k_가_S_A_빼기_1_이고_개입이_많은_과제가_둘이면_후보다(tmp_path: Path) -> None:
    records = _갈래마다(
        6,
        {"A": 10.0, "B": 20.0, "C": 20.0, "D": 1.0, "E": 2.0},
        unsolved={"D": [0]},
        more_interventions={"E": [0, 1]},
    )
    j = _판정(tmp_path, records)
    assert _줄(j, "D").candidate
    assert _줄(j, "E").candidate
    assert j.main.pick == "D"


def test_구간_위_끝이_1_보다_작지_않으면_후보가_아니고_후보가_없으면_칸을_둔다(
    tmp_path: Path,
) -> None:
    records = _갈래마다(6, {"A": 10.0, "B": 10.0, "C": 11.0, "D": 30.0, "E": 15.0})
    j = _판정(tmp_path, records)
    assert _줄(j, "B").interval == (1.0, 1.0)
    assert not any(r.candidate for r in j.main.rows)
    assert j.main.pick is None
    assert j.conclusion == "칸을 둔다: Opus 5.5 / xhigh (후보 없음)"


# --- 결론 없음 ---


def test_T_가_여섯보다_적으면_결론_없음이다(tmp_path: Path) -> None:
    records = _갈래마다(5, {"A": 10.0, "B": 5.0, "C": 5.0, "D": 5.0, "E": 5.0})
    j = _판정(tmp_path, records, 과제수=5)
    assert j.blockers == ("T가 6보다 적다(5)",)
    assert j.conclusion == "결론 없음: T가 6보다 적다(5). 칸은 Opus 5.5 / xhigh 그대로다"
    # 결론 없음이면 세 표는 판정이 아니라 탐색이다.
    assert "## 탐색(판정이 아니다) 본 판정" in j.text


def test_T_가_여섯이면_T_로는_결론_없음이_아니다(tmp_path: Path) -> None:
    j = _판정(tmp_path, _갈래마다(6, {"A": 10.0, "B": 5.0, "C": 5.0, "D": 5.0, "E": 5.0}))
    assert j.blockers == ()
    assert "## 본 판정" in j.text


def test_S_A_가_T_의_절반보다_적으면_결론_없음이다(tmp_path: Path) -> None:
    records = _갈래마다(7, {a.name: 10.0 for a in ARMS}, unsolved={"A": range(3, 7)})
    j = _판정(tmp_path, records, 과제수=7)
    assert j.blockers == ("S_A가 T의 절반보다 적다(S_A 3, T 7)",)
    assert j.conclusion.startswith("결론 없음: S_A가")


def test_S_A_가_T_의_절반이면_결론_없음이_아니다(tmp_path: Path) -> None:
    records = _갈래마다(6, {a.name: 10.0 for a in ARMS}, unsolved={"A": range(3, 6)})
    j = _판정(tmp_path, records)
    assert j.blockers == ()


def test_사전_등록_절의_해시가_다르면_결론_없음이다(tmp_path: Path) -> None:
    records = _갈래마다(6, {"A": 10.0, "B": 5.0, "C": 5.0, "D": 5.0, "E": 5.0})
    j = _판정(tmp_path, records, expected="0" * 64)
    assert j.blockers == (
        f"사전 등록 절의 SHA-256 {README_SHA256}이 판정 도구의 상수 {'0' * 64}와 다르다",
    )
    assert j.main.pick == "B"  # 표는 탐색으로 남지만 결론은 내지 않는다
    assert j.conclusion.startswith("결론 없음: 사전 등록 절의 SHA-256")


@pytest.mark.parametrize(
    ("readme", "counts"),
    [
        ("# 프로브\n정의\n", "시작 0개, 끝 0개"),
        (f"# 프로브\n{PREREG_START}\n정의\n", "시작 1개, 끝 0개"),
        (f"# 프로브\n정의\n{PREREG_END}\n", "시작 0개, 끝 1개"),
        (f"# 프로브 `{PREREG_START}`·`{PREREG_END}`\n{README}", "시작 2개, 끝 2개"),
    ],
    ids=["표지 없음", "시작 표지뿐", "끝 표지뿐", "글 속의 표지"],
)
def test_사전_등록_표지가_하나씩이_아니면_결론_없음이다(
    tmp_path: Path, readme: str, counts: str
) -> None:
    records = _갈래마다(6, {"A": 10.0, "B": 5.0, "C": 5.0, "D": 5.0, "E": 5.0})
    j = _판정(tmp_path, records, readme=readme)
    assert j.blockers == (f"사전 등록 절의 표지가 시작과 끝 하나씩 차례대로 있지 않다({counts})",)


# --- 되풀이 ---


def _공식(records: list[Record], official: Mapping[str, float]) -> list[Record]:
    return [
        replace(r, spend=replace(r.spend, official_usd=official[r.arm])) if r.arm in official else r
        for r in records
    ]


def _숨은_실패(records: list[Record], arm: str, 과제들: Iterable[int]) -> list[Record]:
    고른 = {_과제_id(n) for n in 과제들}
    return [
        _회차(int(r.task_id[-2:]), arm, cost=r.spend.claude_code_usd, hidden=False)
        if r.arm == arm and r.task_id in 고른
        else r
        for r in records
    ]


def test_공식_단가의_되풀이가_다른_갈래를_고르면_단가에_따라_갈린다를_붙인다(
    tmp_path: Path,
) -> None:
    records = _갈래마다(6, {"A": 10.0, "B": 5.0, "C": 8.0, "D": 20.0, "E": 20.0})
    records = _공식(records, {"B": 20.0, "C": 3.0})
    j = _판정(tmp_path, records)
    assert (j.main.pick, j.official.pick, j.no_hidden.pick) == ("B", "C", "B")
    assert j.conclusion == "새 칸: Opus 5.5 / high (갈래 B) (단가에 따라 갈린다)"


def test_숨은_시험_없이_센_되풀이가_다른_갈래를_고르면_숨은_시험에_따라_갈린다를_붙인다(
    tmp_path: Path,
) -> None:
    records = _갈래마다(6, {"A": 10.0, "B": 8.0, "C": 20.0, "D": 2.0, "E": 20.0})
    records = _숨은_실패(records, "D", [0, 1, 2])
    j = _판정(tmp_path, records)
    assert (_줄(j, "D").solved, next(r for r in j.no_hidden.rows if r.arm == "D").solved) == (3, 6)
    assert (j.main.pick, j.official.pick, j.no_hidden.pick) == ("B", "B", "D")
    assert j.conclusion == "새 칸: Opus 5.5 / high (갈래 B) (숨은 시험에 따라 갈린다)"


def test_되풀이_둘이_모두_다르면_둘_다_붙이고_후보_없음에도_붙인다(tmp_path: Path) -> None:
    records = _갈래마다(6, {"A": 10.0, "B": 10.0, "C": 20.0, "D": 2.0, "E": 20.0})
    records = _숨은_실패(_공식(records, {"C": 3.0}), "D", [0, 1, 2])
    j = _판정(tmp_path, records)
    assert (j.main.pick, j.official.pick, j.no_hidden.pick) == (None, "C", "D")
    assert j.conclusion == (
        "칸을 둔다: Opus 5.5 / xhigh (후보 없음) (단가에 따라 갈린다, 숨은 시험에 따라 갈린다)"
    )


def test_결론_없음에는_갈린다를_붙이지_않는다(tmp_path: Path) -> None:
    records = _갈래마다(5, {"A": 10.0, "B": 5.0, "C": 8.0, "D": 20.0, "E": 20.0})
    j = _판정(tmp_path, _공식(records, {"B": 20.0, "C": 3.0}), 과제수=5)
    assert j.official.pick != j.main.pick
    assert j.conclusion == "결론 없음: T가 6보다 적다(5). 칸은 Opus 5.5 / xhigh 그대로다"


# --- 셈에 섞인 몫 ---


def _비용_대신(r: Record) -> Record:
    세션 = Session(
        session_id="0f8e2c1a-1b2c-4d3e-8f90-123456789abc",
        calls=(),
        cost_usd=r.spend.claude_code_usd,
        cost_substituted=True,
        runner_killed=True,
        model_usage=(),
        main_lines=(),
        subagent_lines=(),
    )
    return replace(r, sessions=(세션,))


def _준비_실패(r: Record) -> Record:
    실패 = SetupFailure(command=SETUP_COMMANDS[0], exit_code=1, timed_out=False)
    return replace(r, outcome=replace(r.outcome, setup_failure=실패, gates=None, hidden=None))


def _사용량_대신(r: Record) -> Record:
    몫 = Substitute(
        model="claude-haiku-5-5",
        tokens=Tokens(input=1, output=2, cache_read=3, cache_write=4, thinking=None),
    )
    return replace(r, spend=replace(r.spend, substitutes=(몫,)))


def test_대신_넣은_비용과_준비_실패와_사용량으로_대신_셈한_회차를_갈래마다_센다(
    tmp_path: Path,
) -> None:
    def 그대로(r: Record) -> Record:
        return r

    바꿀: dict[tuple[int, str], Callable[[Record], Record]] = {
        (0, "B"): _비용_대신,
        (1, "B"): _비용_대신,
        (2, "C"): _준비_실패,
        (3, "D"): _사용량_대신,
        (4, "D"): _사용량_대신,
        (5, "E"): _사용량_대신,
    }
    records = [
        바꿀.get((int(r.task_id[-2:]), r.arm), 그대로)(r)
        for r in _갈래마다(6, {a.name: 10.0 for a in ARMS})
    ]
    # T 밖 과제의 회차는 세지 않는다.
    records += [_비용_대신(_회차(6, a.name)) for a in ARMS if a.name != "E"]
    j = _판정(tmp_path, records, 과제수=7)
    assert {
        c.arm: (c.cost_substituted, c.setup_failed, c.official_substituted) for c in j.mixed
    } == {
        "A": (0, 0, 0),
        "B": (2, 0, 0),
        "C": (0, 1, 0),
        "D": (0, 0, 2),
        "E": (0, 0, 1),
    }
    assert _줄(j, "C").solved == 5  # 준비가 실패한 회차는 풀지 못한 것이다
    assert "공식 단가 셈에 modelUsage로 대신 셈한 몫이 든 회차: 3" in j.text


# --- 탐색 ---


def test_탐색은_크기_층마다_갈래의_푼_수와_비용_비를_낸다(tmp_path: Path) -> None:
    tasks = [_과제(n, tier=TIER_SMALL if n < 3 else TIER_LARGE) for n in range(6)]
    records = _갈래마다(
        6, {"A": 10.0, "B": 5.0, "C": 10.0, "D": 10.0, "E": 10.0}, unsolved={"B": [3, 4]}
    )
    j = _판정(tmp_path, records, tasks=tasks)
    줄 = {(t.tier, t.arm): (t.tasks, t.solved, t.ratio) for t in j.explore.tiers}
    assert 줄[(TIER_SMALL, "B")] == (3, 3, 0.5)
    assert 줄[(TIER_LARGE, "B")] == (3, 1, 1.5)
    assert 줄[(TIER_LARGE, "A")] == (3, 3, 1.0)


def test_탐색은_싼_갈래로_먼저_열고_못_풀면_비싼_갈래로_다시_여는_짝의_비용을_낸다(
    tmp_path: Path,
) -> None:
    records = _갈래마다(
        6, {"A": 10.0, "B": 8.0, "C": 6.0, "D": 2.0, "E": 4.0}, unsolved={"D": [0, 1], "C": [0]}
    )
    j = _판정(tmp_path, records)
    짝 = {(e.first, e.then): (e.solved, e.cost, e.unit) for e in j.explore.escalations}
    # D가 못 푼 두 과제만 A로 다시 연다: 2×6 + 10×2 = 32.
    assert 짝[("D", "A")] == (6, 32.0, pytest.approx(32.0 / 6))
    # C로 다시 열어도 과제 0은 둘 다 못 푼다: 2×6 + 6×2 = 24.
    assert 짝[("D", "C")] == (5, 24.0, pytest.approx(24.0 / 5))
    assert ("A", "D") not in 짝  # 비싼 갈래로 먼저 여는 짝은 없다
    assert len(짝) == 10


def test_탐색은_붙여_넣은_글의_D_에서_C_로_올리는_짝을_D_가_비싸도_낸다(tmp_path: Path) -> None:
    records = _갈래마다(6, {"A": 10.0, "B": 8.0, "C": 4.0, "D": 6.0, "E": 2.0}, unsolved={"D": [0]})
    j = _판정(tmp_path, records)
    짝 = {(e.first, e.then): (e.solved, e.cost) for e in j.explore.escalations}
    # 본 판정의 C는 D 36, C 24로 C가 싸지만 D→C는 붙여 넣은 글의 규칙이라 낸다: 6×6 + 4×1 = 40.
    assert 짝[("D", "C")] == (6, 40.0)
    assert ("C", "D") in 짝
    assert len(짝) == 11
    assert "붙여 넣은 글의 규칙은 D에서 C로 올리는 짝이다" in j.text


def test_탐색은_갈래마다_시간_토큰_생각_토큰의_몫_물으며_끝남_상한_거부_수를_낸다(
    tmp_path: Path,
) -> None:
    def 바꿈(r: Record) -> Record:
        if r.arm != "B":
            return r
        n = int(r.task_id[-2:])
        spend = replace(
            r.spend,
            wall_seconds=100.0 * (n + 1),
            denied_calls=n,
            tokens=Tokens(input=1, output=20, cache_read=2, cache_write=3, thinking=5),
        )
        return replace(r, spend=spend, asked_at_end=n < 2)

    records = [바꿈(r) for r in _갈래마다(6, {a.name: 10.0 for a in ARMS})]
    records = [
        _회차(5, "C", end=END_CAPPED, reason="시간")
        if (r.arm, r.task_id) == ("C", _과제_id(5))
        else r
        for r in records
    ]
    j = _판정(tmp_path, records)
    b = next(e for e in j.explore.effort if e.arm == "B")
    assert b.wall_median == 350.0
    assert (b.input, b.output, b.cache_read, b.cache_write, b.thinking) == (6, 120, 12, 18, 30)
    assert b.thinking_share == 0.25
    assert (b.asked, b.capped, b.denied) == (2, 0, 15)
    assert next(e for e in j.explore.effort if e.arm == "C").capped == 1


def test_탐색의_토큰_합은_빈_칸이_하나라도_있으면_모름이다(tmp_path: Path) -> None:
    records = _갈래마다(6, {a.name: 10.0 for a in ARMS})
    빈 = Tokens(input=1, output=10, cache_read=100, cache_write=5, thinking=None)
    records = [
        replace(r, spend=replace(r.spend, tokens=빈))
        if (r.arm, r.task_id) == ("A", _과제_id(0))
        else r
        for r in records
    ]
    j = _판정(tmp_path, records)
    a = next(e for e in j.explore.effort if e.arm == "A")
    assert (a.output, a.thinking, a.thinking_share) == (60, None, None)


def test_탐색은_원래_세션이_xhigh_인_과제로만_A_와_원래_세션의_비용_비를_낸다(
    tmp_path: Path,
) -> None:
    원래 = ["claude-opus-5-5/xhigh", "claude-opus-5-5/medium", None, "claude-opus-5-5/xhigh"]
    tasks = [_과제(n, original=원래[n] if n < 4 else None) for n in range(6)]
    records = _갈래마다(6, {"A": 20.0, "B": 10.0, "C": 10.0, "D": 10.0, "E": 10.0})
    records = [
        replace(r, spend=replace(r.spend, claude_code_usd=30.0))
        if (r.arm, r.task_id) == ("A", _과제_id(3))
        else r
        for r in records
    ]
    j = _판정(tmp_path, records, tasks=tasks)
    o = j.explore.original
    # 과제 0과 3: A의 비용 20 + 30, 원래 세션의 PR 앞 비용 10 + 10.
    assert (o.tasks, o.a_cost, o.pr_cost, o.ratio) == (2, 50.0, 20.0, 2.5)


def test_탐색은_D_E_의_비용_비를_붙여_넣은_글의_55_60퍼센트와_견준다(tmp_path: Path) -> None:
    j = _판정(tmp_path, _갈래마다(6, {"A": 10.0, "B": 10.0, "C": 10.0, "D": 6.0, "E": 5.5}))
    assert "D(Sonnet 5.5 / high): R 0.60 [0.60, 0.60], 붙여 넣은 글은 Opus 비용의 55~60%" in j.text
    assert (
        "E(Sonnet 5.5 / medium): R 0.55 [0.55, 0.55], 붙여 넣은 글은 Opus 비용의 55~60%" in j.text
    )


def test_탐색은_한도_사용률의_회차마다의_변화를_창마다_낸다(tmp_path: Path) -> None:
    def 사용률(r: Record) -> Record:
        n = int(r.task_id[-2:])
        start = (Window(window="five_hour", utilization=0.1),)
        end = (
            Window(window="five_hour", utilization=0.1 + 0.1 * n),
            Window(window="seven_day", utilization=0.5),  # 첫 사용률에 없는 창은 셈하지 않는다
        )
        spend = replace(r.spend, utilization_start=start, utilization_end=end)
        return replace(r, spend=spend) if r.arm == "E" else r

    records = [사용률(r) for r in _갈래마다(6, {a.name: 10.0 for a in ARMS})]
    j = _판정(tmp_path, records)
    줄 = {(u.arm, u.window): (u.rounds, u.median_change) for u in j.explore.utilization}
    assert 줄 == {("E", "five_hour"): (6, pytest.approx(0.25))}


# --- 명령 줄 입구 ---


def _입구(tmp_path: Path) -> list[str]:
    tasks_path, records_dir, readme_path = _파일(tmp_path, _모두(), 과제수=7)
    return ["--tasks", str(tasks_path), "--records", str(records_dir), "--readme", str(readme_path)]


def test_명령_줄은_해시_상수를_판정_함수에_넘긴다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    # 상수의 값은 단언하지 않는다. 상수를 README 절의 해시로 바꾸면 해시 결론 없음이 사라지고,
    # 다른 값으로 바꾸면 그 값이 결론 줄에 든다.
    argv = _입구(tmp_path)
    monkeypatch.setattr(rerun_judge, "PREREG_SHA256", README_SHA256)
    assert main(argv) == 0
    assert "결론: 칸을 둔다" in capsys.readouterr().out
    monkeypatch.setattr(rerun_judge, "PREREG_SHA256", "c" * 64)
    assert main(argv) == 0
    out = capsys.readouterr().out
    assert "결론: 결론 없음: 사전 등록 절의 SHA-256" in out
    assert f"상수 {'c' * 64}와 다르다" in out


def test_명령_줄은_기록_폴더가_없으면_2로_끝난다(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    argv = _입구(tmp_path)
    argv[argv.index("--records") + 1] = str(tmp_path / "없음")
    assert main(argv) == 2
    assert "기록 폴더가 없다" in capsys.readouterr().err


def test_명령_줄은_꼴이_틀린_과제_목록이면_2로_끝난다(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    argv = _입구(tmp_path)
    Path(argv[argv.index("--tasks") + 1]).write_text("{}", encoding="utf-8")
    assert main(argv) == 2
    assert "읽지 못했다" in capsys.readouterr().err


def test_명령_줄은_UTF_8_이_아닌_README_면_2로_끝난다(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    argv = _입구(tmp_path)
    Path(argv[argv.index("--readme") + 1]).write_bytes("사전 등록".encode("cp949"))
    assert main(argv) == 2
    assert "README: UTF-8이 아니다" in capsys.readouterr().err


def test_모듈로_띄우면_판정을_UTF_8_로_찍고_0_으로_끝난다(tmp_path: Path) -> None:
    """쓰는 법은 `uv run python -m tools.rerun_judge`다. 자식의 `PYTHONIOENCODING`을 cp949로 두어
    출력을 UTF-8로 다시 열지 않으면 빨갛게 한다. 해시 상수의 값과 상관없이 결론 없음이다(지은
    README의 해시는 어떤 실제 절과도 다르다)."""
    done = subprocess.run(
        [sys.executable, "-m", "tools.rerun_judge", *_입구(tmp_path)],
        cwd=ROOT,
        capture_output=True,
        env={**os.environ, "PYTHONIOENCODING": "cp949"},
        check=False,
        timeout=60,
    )
    assert done.returncode == 0, done.stderr.decode("utf-8", errors="replace")
    out = done.stdout.decode("utf-8").replace("\r\n", "\n")  # 윈도의 글 모드 줄바꿈
    assert out.startswith("# 다시 풀기 판정\n")
    assert "결론: 결론 없음: 사전 등록 절의 SHA-256" in out


def test_파일럿_과제_목록은_판정하지_않고_2로_끝난다(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    argv = _입구(tmp_path)
    pilot = replace(_과제(0), pilot=True, tier=TIER_PILOT)
    write_task_list(Path(argv[argv.index("--tasks") + 1]), TaskList(LIST_PILOT, (pilot,)))
    assert main(argv) == 2
    assert "본 측정의 과제 목록이 아니다" in capsys.readouterr().err
