"""tools/check_instructions.py 의 사본 센티널 검사.

`npx skills update -p` 가 덧댄 사본을 되돌리면 리뷰 범위와 반영 절차가 조용히 사라진다.
변이로 빨강을 한 번 본 것은 일회성이라, 회귀는 이 테스트가 막는다.
"""

from __future__ import annotations

from collections.abc import Container
from pathlib import Path

from tools.check_instructions import PATCHED_SKILLS, SENTINEL, patched_skills_without_sentinel


def _사본을_만든다(root: Path, *, 센티널을_넣을_스킬: Container[str]) -> None:
    for name in PATCHED_SKILLS:
        path = root / ".claude" / "skills" / name / "SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        주석 = f"<!-- {SENTINEL}. 원본에 무엇을 더했는지 -->\n"
        머리말 = 주석 if name in 센티널을_넣을_스킬 else ""
        path.write_text(f"{머리말}본문\n", encoding="utf-8")


def test_사본마다_센티널이_있으면_문제가_없다(tmp_path: Path) -> None:
    _사본을_만든다(tmp_path, 센티널을_넣을_스킬=set(PATCHED_SKILLS))

    assert patched_skills_without_sentinel(tmp_path) == []


def test_센티널이_사라진_사본을_잡는다(tmp_path: Path) -> None:
    _사본을_만든다(tmp_path, 센티널을_넣을_스킬=set(PATCHED_SKILLS) - {"code-review"})

    problems = patched_skills_without_sentinel(tmp_path)

    assert len(problems) == 1
    assert "code-review" in problems[0]


def test_사본_파일이_통째로_사라진_것도_잡는다(tmp_path: Path) -> None:
    _사본을_만든다(tmp_path, 센티널을_넣을_스킬=set(PATCHED_SKILLS))
    (tmp_path / ".claude" / "skills" / "retro" / "SKILL.md").unlink()

    problems = patched_skills_without_sentinel(tmp_path)

    assert len(problems) == 1
    assert "retro" in problems[0]


def test_이_저장소의_사본들은_지금_온전하다() -> None:
    assert patched_skills_without_sentinel() == []
