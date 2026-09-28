"""tools/hook_journal_retro.py 의 순수 함수. stdin 을 읽는 main 은 실제 실행으로 확인한다.

발동 조건은 대기열 28 의 것이다 — Write 이거나 Edit 의 new_string 이 `## 다음` 을 담을 때. 경로만
보던 동안 인용 하나를 고친 Edit 마다 계기가 울렸다(대기열 28 의 5회차와 일지 둘).
"""

from __future__ import annotations

from tools.hook_journal_retro import context_for, is_journal

JOURNAL = "C:\\project\\agent\\docs\\journal\\2026-09-21-first-slice.md"


def test_일지를_Write_로_쓰면_retro_계기_문장을_돌려준다() -> None:
    context = context_for("Write", JOURNAL, None)

    assert context is not None
    assert "retro" in context


def test_다음_절을_담은_Edit_도_계기다() -> None:
    assert context_for("Edit", JOURNAL, "## 다음\n\n- web-admin 설계") is not None


def test_다음_절을_건드리지_않은_Edit_는_계기가_아니다() -> None:
    """인용 하나를 원문으로 고친 Edit 에 계기가 울리던 자리다(대기열 28, 5회차)."""
    assert context_for("Edit", JOURNAL, '"화면이 없어도 시스템이 돌고"') is None
    assert context_for("Edit", JOURNAL, None) is None


def test_일지가_아닌_파일은_도구가_무엇이든_None이다() -> None:
    assert context_for("Write", "docs/adr/0008-x.md", None) is None
    assert context_for("Edit", "docs/adr/0008-x.md", "## 다음") is None
    assert not is_journal("docs/journal/notes.txt")
    assert not is_journal("journal/2026-09-21.md")
