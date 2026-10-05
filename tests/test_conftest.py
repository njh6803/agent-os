"""tests/conftest.py 의 skip 판정. 이 스위트 안에서는 skip 을 만들 수 없어 pytester 로 잰다."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

pytest_plugins = "pytester"

CONFTEST = (Path(__file__).resolve().parent / "conftest.py").read_text(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]


def test_agent_os_가_다른_체크아웃에서_불리면_세션을_시작하지_않는다(
    pytester: pytest.Pytester, monkeypatch: pytest.MonkeyPatch
) -> None:
    """다른 체크아웃의 `.venv` 로 돌리면 `agent_os` 가 그쪽 `src` 에서 불려 브랜치의 코드가 검사되지
    않는다(2026-10-05 워크트리 감사 12). 가짜 `agent_os` 를 경로 앞에 두어 그 상태를 만든다.
    in-process 로는 이미 불린 `agent_os` 가 남아 재현되지 않아 subprocess 로 돈다."""
    other = pytester.mkdir("other_checkout")
    (other / "agent_os").mkdir()
    (other / "agent_os" / "__init__.py").write_text("", encoding="utf-8")
    monkeypatch.setenv("PYTHONPATH", os.pathsep.join([str(other), str(ROOT)]))
    pytester.makeconftest(CONFTEST)
    pytester.makepyfile("def test_ok():\n    assert True\n")

    result = pytester.runpytest_subprocess("-p", "no:cacheprovider")

    assert result.ret == pytest.ExitCode.USAGE_ERROR
    assert "other_checkout" in result.stderr.str()
    assert "uv run pytest" in result.stderr.str()


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
