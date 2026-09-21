"""tools/hook_bash_heredoc.py 의 순수 함수. stdin 을 읽는 main 은 실제 실행으로 확인한다."""

from __future__ import annotations

from tools.hook_bash_heredoc import MAX_LINES, longest_heredoc, reason_for


def _heredoc(lines: int, marker: str = "'EOF'") -> str:
    body = "\n".join(f"line {i}" for i in range(lines))
    return f"cat > out.txt <<{marker}\n{body}\nEOF\necho done"


def test_heredoc이_없으면_0이다() -> None:
    assert longest_heredoc("git status && ls -la") == 0


def test_heredoc_본문_줄_수를_센다() -> None:
    assert longest_heredoc(_heredoc(7)) == 7
    assert longest_heredoc(_heredoc(3, marker="EOF")) == 3


def test_heredoc이_여럿이면_가장_긴_것이다() -> None:
    command = _heredoc(5) + "\n" + _heredoc(12)

    assert longest_heredoc(command) == 12


def test_상한_이하는_통과하고_넘으면_이유를_돌려준다() -> None:
    assert reason_for(_heredoc(MAX_LINES)) is None
    reason = reason_for(_heredoc(MAX_LINES + 1))
    assert reason is not None
    assert "Write" in reason
