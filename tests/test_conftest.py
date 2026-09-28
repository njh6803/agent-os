"""tests/conftest.py 의 skip 판정. 이 스위트 안에서는 skip 을 만들 수 없어 pytester 로 잰다."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest_plugins = "pytester"

CONFTEST = (Path(__file__).resolve().parent / "conftest.py").read_text(encoding="utf-8")


def test_skip_이_하나라도_있으면_세션이_실패한다(pytester: pytest.Pytester) -> None:
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile(
        "import pytest\n\n"
        "def test_skipped():\n    pytest.skip('환경 부재')\n\n"
        "def test_ok():\n    assert True\n"
    )

    result = pytester.runpytest("-p", "no:cacheprovider")

    assert result.ret == pytest.ExitCode.TESTS_FAILED
    result.stdout.fnmatch_lines(["*skip 1건*"])


def test_skip_이_없으면_그대로_통과한다(pytester: pytest.Pytester) -> None:
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile("def test_ok():\n    assert True\n")

    result = pytester.runpytest("-p", "no:cacheprovider")

    assert result.ret == pytest.ExitCode.OK


def test_deselect_는_skip_이_아니다(pytester: pytest.Pytester) -> None:
    """기본 실행의 `-m "not llm"` 이 이 판정에 걸리면 매 실행이 빨강이다."""
    pytester.makeconftest(CONFTEST)
    pytester.makeini("[pytest]\nmarkers =\n    llm: 실제 호출\n")
    pytester.makepyfile(
        "import pytest\n\n"
        "@pytest.mark.llm\ndef test_llm():\n    assert False\n\n"
        "def test_ok():\n    assert True\n"
    )

    result = pytester.runpytest("-p", "no:cacheprovider", "-m", "not llm")

    assert result.ret == pytest.ExitCode.OK
