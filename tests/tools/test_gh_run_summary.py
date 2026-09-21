"""tools/gh_run_summary.py의 순수 함수 검증. 셸을 부르는 fetch_log는 실제 실행으로 확인한다."""

from __future__ import annotations

import pytest
from tools.gh_run_summary import TEXT_WIDTH, main, render, summarize

PREFIX = "claude-review\tRun Claude Code Review\t2026-09-20T10:45:00.0000000Z "


def log(*lines: str) -> list[str]:
    return [PREFIX + line for line in lines]


def test_요약은_결과_블록의_턴수와_비용만_남기고_스트림_잡음은_버린다() -> None:
    summary = summarize(
        log(
            '  "subtype": "thinking_tokens",',
            '  "is_error": false,',
            '  "num_turns": 4,',
            '  "total_cost_usd": 0.18,',
        )
    )
    assert summary.results == ['"num_turns": 4', '"total_cost_usd": 0.18']


def test_허용_밖_호출은_도구별로_세어서_렌더의_결과_절에만_나타난다() -> None:
    summary = summarize(
        log(
            '  "subtype": "permission_denied",',
            '  "tool_name": "Bash",',
            '  "subtype": "permission_denied",',
            '  "tool_name": "WebFetch",',
            '  "subtype": "permission_denied",',
            '  "tool_name": "Bash",',
        )
    )
    assert summary.denied == 3
    assert summary.denied_tools == {"Bash": 2, "WebFetch": 1}
    assert summary.results == []
    assert "permission_denied 이벤트 3건 (허용 도구 밖의 호출: Bash 2, WebFetch 1)" in render(
        summary
    )


def test_워크플로_검증_건너뜀은_신호로_잡히고_결과_블록_없음을_알린다() -> None:
    summary = summarize(
        log("##[warning]Skipping action due to workflow validation: Workflow validation failed.")
    )
    assert len(summary.signals) == 1
    assert "workflow validation" in summary.signals[0]
    assert "결과 블록 없음" in render(summary)


def test_클로드의_말은_접두를_떼고_폭을_자른다() -> None:
    long_text = "가" * (TEXT_WIDTH + 50)
    summary = summarize(log(f'      "text": "{long_text}'))
    assert summary.texts == ["가" * TEXT_WIDTH]


def test_인자가_없으면_쓰임을_알리고_2를_돌려준다(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["gh_run_summary.py"]) == 2
    assert main(["gh_run_summary.py", "abc"]) == 2
    assert "쓰임" in capsys.readouterr().err
