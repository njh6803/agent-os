"""tools/hook_journal_retro.py 의 순수 함수. stdin 을 읽는 main 은 실제 실행으로 확인한다."""

from __future__ import annotations

from tools.hook_journal_retro import context_for


def test_일지_파일을_쓰면_retro_계기_문장을_돌려준다() -> None:
    context = context_for("C:\\project\\agent\\docs\\journal\\2026-09-21-first-slice.md")

    assert context is not None
    assert "retro" in context


def test_일지가_아닌_파일은_None이다() -> None:
    assert context_for("docs/adr/0008-x.md") is None
    assert context_for("docs/journal/notes.txt") is None
    assert context_for("journal/2026-09-21.md") is None
