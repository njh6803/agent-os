"""사전 등록 절과 정의에 드는 코드 상수의 대조(티켓 11, 명세 "파일럿과 사전 등록"의 주석).

절의 해시는 README 글만 보므로, 해시를 고정한 뒤 상수만 바뀌면 판정의 대조에 걸리지 않는다. 모듈마다
`PREREG_VALUES`의 항목을 `prereg_line`으로 지어 절에서 찾고, 절의 상수 줄이 모두 표에 있는지 본다.
판정 헬퍼는 절의 글을 인자로 받아, 이 저장소의 절이 지나가는 시험과 지어낸 절로 빨강을 내는 변이
시험을 함께 둔다(`.claude/rules/tests.md`의 저장소 상태 검사).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest
from tools.model_sweep_judge import percentile_ci
from tools.rerun_files import Json, prereg_line, prereg_pattern
from tools.rerun_judge import PREREG_README, PREREG_SHA256, prereg_problem, prereg_section

from tools import (
    rerun_checks,
    rerun_continue,
    rerun_cost,
    rerun_files,
    rerun_gates,
    rerun_hidden,
    rerun_judge,
    rerun_round,
    rerun_runner,
    rerun_select,
    rerun_session,
)

TABLES: tuple[tuple[str, dict[str, Json]], ...] = (
    ("rerun_files", rerun_files.PREREG_VALUES),
    ("rerun_select", rerun_select.PREREG_VALUES),
    ("rerun_hidden", rerun_hidden.PREREG_VALUES),
    ("rerun_round", rerun_round.PREREG_VALUES),
    ("rerun_session", rerun_session.PREREG_VALUES),
    ("rerun_continue", rerun_continue.PREREG_VALUES),
    ("rerun_checks", rerun_checks.PREREG_VALUES),
    ("rerun_gates", rerun_gates.PREREG_VALUES),
    ("rerun_cost", rerun_cost.PREREG_VALUES),
    ("rerun_runner", rerun_runner.PREREG_VALUES),
    ("rerun_judge", rerun_judge.PREREG_VALUES),
)
_CONSTANT_LINE = re.compile(r"rerun_[a-z]+\.[A-Z][A-Z0-9_]* = ")
_TABLE_DEF = re.compile(r"^PREREG_VALUES\b", re.MULTILINE)
_LISTS = (("과제 목록(`main.json`)", "main.json"), ("되살릴 목록(`revive.json`)", "revive.json"))


def _기대한_줄() -> list[str]:
    return [
        prereg_line(module, name, value)
        for module, table in TABLES
        for name, value in table.items()
    ]


def _이_저장소의_절() -> str:
    section = prereg_section(PREREG_README.read_text(encoding="utf-8"))
    assert section is not None, f"{PREREG_README} 에 사전 등록 절이 없다"
    return section


def _상수_줄(section: str) -> list[str]:
    return [line.strip() for line in section.splitlines() if _CONSTANT_LINE.match(line.strip())]


def _빠진_줄(section: str) -> list[str]:
    found = set(_상수_줄(section))
    return [line for line in _기대한_줄() if line not in found]


def _남는_줄(section: str) -> list[str]:
    expected = set(_기대한_줄())
    return [line for line in _상수_줄(section) if line not in expected]


def _겹친_줄(section: str) -> list[str]:
    lines = _상수_줄(section)
    return sorted({line for line in lines if lines.count(line) > 1})


def _절의_JSON(section: str, heading: str) -> Json:
    _, found, rest = section.partition(f"\n### {heading}\n")
    assert found, f"사전 등록 절에 `### {heading}` 머리가 없다"
    _, fence, body = rest.partition("```json\n")
    assert fence, f"`### {heading}` 아래에 JSON 블록이 없다"
    text, end, _ = body.partition("\n```")
    assert end, f"`### {heading}` 아래 JSON 블록이 닫히지 않았다"
    return json.loads(text)


def test_줄은_모듈_이름_값의_JSON_한_줄이다() -> None:
    assert (
        prereg_line("rerun_x", "NAME", [1, "가", {"k": 0.5}])
        == 'rerun_x.NAME = [1, "가", {"k": 0.5}]'
    )


def test_정규식은_글과_켠_플래그를_싣는다() -> None:
    assert prereg_pattern(re.compile("a.b", re.IGNORECASE | re.DOTALL)) == {
        "pattern": "a.b",
        "flags": ["IGNORECASE", "DOTALL"],
    }
    assert prereg_pattern(re.compile("a")) == {"pattern": "a", "flags": []}


def test_표마다_항목이_있다() -> None:
    assert all(table for _, table in TABLES)


def test_표를_둔_모듈은_모두_대조에_든다() -> None:
    tools = Path(__file__).resolve().parents[2] / "tools"
    having = sorted(
        path.stem
        for path in tools.glob("rerun_*.py")
        if _TABLE_DEF.search(path.read_text(encoding="utf-8"))
    )
    assert having, f"{tools} 에서 PREREG_VALUES 를 둔 모듈을 하나도 찾지 못했다"
    assert having == sorted(module for module, _ in TABLES)


def test_이_저장소의_사전_등록_절이_표의_값을_모두_든다() -> None:
    assert _빠진_줄(_이_저장소의_절()) == [], (
        "사전 등록 절에 없거나 값이 다른 상수(코드가 바뀌었으면 결과를 보기 전인지 본다)"
    )


def test_이_저장소의_사전_등록_절의_상수_줄은_모두_표에_있다() -> None:
    assert _남는_줄(_이_저장소의_절()) == []


def test_이_저장소의_사전_등록_절의_상수_줄은_한_번씩이다() -> None:
    assert _겹친_줄(_이_저장소의_절()) == []


def test_값이_바뀐_상수를_잡는다() -> None:
    line = _기대한_줄()[0]
    changed = _이_저장소의_절().replace(f"\n{line}\n", f"\n{line}0\n", 1)
    assert _빠진_줄(changed) == [line]


def test_표에_없는_상수_줄을_잡는다() -> None:
    extra = "rerun_files.NOT_IN_TABLE = 1"
    assert _남는_줄(_이_저장소의_절() + f"\n{extra}\n") == [extra]


def test_두_번_적은_상수_줄을_잡는다() -> None:
    line = _기대한_줄()[0]
    assert _겹친_줄(_이_저장소의_절() + f"\n{line}\n") == [line]


def test_판정_도구의_해시가_이_저장소의_사전_등록_절과_맞는다() -> None:
    assert prereg_problem(PREREG_README.read_text(encoding="utf-8"), PREREG_SHA256) is None


def test_절의_글이_한_글자_바뀌면_해시가_맞지_않는다() -> None:
    text = PREREG_README.read_text(encoding="utf-8")
    section = _이_저장소의_절()
    changed = text.replace(section, section.replace("\n", "\n ", 1), 1)
    assert prereg_problem(changed, PREREG_SHA256) is not None


def test_구간은_5와_95_백분위다() -> None:
    # 사전 등록 절의 "90% 구간"이 판정이 부르는 함수의 동작과 같은지(그 값은 함수 안에 있다).
    assert percentile_ci([float(i) for i in range(101)]) == (5.0, 95.0)


@pytest.mark.parametrize(("heading", "name"), _LISTS)
def test_이_저장소의_사전_등록_절의_목록은_커밋한_파일과_같다(heading: str, name: str) -> None:
    path = PREREG_README.parent / name
    expected = json.loads(path.read_text(encoding="utf-8"))
    assert _절의_JSON(_이_저장소의_절(), heading) == expected


@pytest.mark.parametrize(
    ("section", "message"),
    [
        ("\n### 다른 머리\n", "머리가 없다"),
        ("\n### 과제 목록(`main.json`)\n\n글\n", "JSON 블록이 없다"),
        ("\n### 과제 목록(`main.json`)\n\n```json\n{}", "닫히지 않았다"),
    ],
)
def test_목록_블록이_없거나_열린_채면_잡는다(section: str, message: str) -> None:
    with pytest.raises(AssertionError, match=message):
        _절의_JSON(section, _LISTS[0][0])
