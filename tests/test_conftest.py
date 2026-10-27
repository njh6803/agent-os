"""tests/conftest.py 의 skip 판정과 LLM 토큰 합계. 이 스위트 안에서는 skip 을 만들 수 없고 LLM
테스트를 돌릴 수 없어 pytester 로 잰다."""

from __future__ import annotations

import os
import shlex
import tomllib
from pathlib import Path

import pytest

pytest_plugins = "pytester"

CONFTEST = (Path(__file__).resolve().parent / "conftest.py").read_text(encoding="utf-8")
ROOT = Path(__file__).resolve().parents[1]


def _default_markers() -> str:
    """기본 실행이 거르는 마커 식. `pyproject.toml` 의 `addopts` 에서 `-m` 의 값을 읽어, 그 식이
    바뀌면 이 파일의 시험도 따라간다."""
    config = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    options = shlex.split(config["tool"]["pytest"]["ini_options"]["addopts"])
    return options[options.index("-m") + 1]


DEFAULT_MARKERS = _default_markers()


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


LLM_INI = "[pytest]\nmarkers =\n    llm: 실제 호출\n    llm_widget: 위젯의 실제 호출\n"


def test_deselect_는_skip_이_아니다(pytester: pytest.Pytester) -> None:
    """기본 실행의 마커 제외(`addopts` 의 `-m`)가 이 판정에 걸리면 매 실행이 빨강이다."""
    pytester.makeconftest(CONFTEST)
    pytester.makeini(LLM_INI)
    pytester.makepyfile(
        "import pytest\n\n"
        "@pytest.mark.llm\ndef test_llm():\n    assert False\n\n"
        "@pytest.mark.llm_widget\ndef test_llm_widget():\n    assert False\n\n"
        "def test_ok():\n    assert True\n"
    )

    result = pytester.runpytest("-p", "no:cacheprovider", "-m", DEFAULT_MARKERS)

    assert result.ret == pytest.ExitCode.OK


# 트레이스 줄은 토큰 칸만 둔다. 무엇을 세는지는 tests/tools/test_llm_tokens.py 가 잰다.
TRACED = (
    "import json\n"
    "import pytest\n\n"
    'LINE = json.dumps({"type": "llm_called", "input_tokens": 20, "output_tokens": 3}) + "\\n"\n\n'
    "@pytest.mark.llm\n"
    "def test_traced(tmp_path):\n"
    '    (tmp_path / "t").mkdir()\n'
    '    (tmp_path / "t" / "r1.jsonl").write_text(LINE * 2, encoding="utf-8")\n\n'
    "@pytest.mark.llm\n"
    "def test_direct():\n"
    "    assert True\n\n"
    "@pytest.mark.llm\n"
    "def test_elsewhere(tmp_path_factory):\n"
    '    (tmp_path_factory.mktemp("other") / "r3.jsonl").write_text(LINE, encoding="utf-8")\n\n'
    "def test_fake_model(tmp_path):\n"
    '    (tmp_path / "r2.jsonl").write_text(LINE, encoding="utf-8")\n'
)


def test_llm_테스트가_tmp_path_에_남긴_트레이스의_토큰_합계를_끝에_찍는다(
    pytester: pytest.Pytester,
) -> None:
    """가짜 모델로 도는 테스트의 트레이스는 세지 않는다. 기본 실행의 트레이스도 `llm_called` 를
    든다. `tmp_path` 를 쓰지 않는 LLM 테스트와 `tmp_path_factory` 로 만든 디렉터리에 쓴 테스트는
    세지 못하고(`tools/llm_tokens.py` 의 못 보는 것), 합계 줄이 그 수를 적는다. 실패가 없으면 합계
    줄은 통과 수 줄 바로 위다."""
    pytester.makeconftest(CONFTEST)
    pytester.makeini(LLM_INI)
    pytester.makepyfile(TRACED)

    result = pytester.runpytest("-p", "no:cacheprovider")

    assert result.ret == pytest.ExitCode.OK
    result.stdout.fnmatch_lines(
        [
            "*LLM 토큰 합계 46(입력 40, 출력 6)*트레이스 1개*모델 호출 2건*"
            "*트레이스를 남기지 않은 LLM 테스트 2개는 세지 못했다*",
            "*= 4 passed in *",
        ],
        consecutive=True,
    )


# `llm_widget` 마커의 시험은 위젯 e2e 를 자식으로 돌리고 serve 의 트레이스 자리로 `tmp_path` 아래를
# 준다 (`tests/test_widget_llm.py`).
WIDGET_TRACED = (
    "import json\n"
    "import pytest\n\n"
    'LINE = json.dumps({"type": "llm_called", "input_tokens": 20, "output_tokens": 3}) + "\\n"\n\n'
    "@pytest.mark.llm_widget\n"
    "def test_widget(tmp_path):\n"
    '    (tmp_path / "traces").mkdir()\n'
    '    (tmp_path / "traces" / "r1.jsonl").write_text(LINE * 2, encoding="utf-8")\n\n'
    "@pytest.mark.llm\n"
    "def test_llm(tmp_path):\n"
    '    (tmp_path / "r2.jsonl").write_text(LINE, encoding="utf-8")\n\n'
    "def test_fake_model(tmp_path):\n"
    '    (tmp_path / "r3.jsonl").write_text(LINE, encoding="utf-8")\n'
)


def test_llm_widget_시험이_tmp_path_에_남긴_트레이스도_합계에_든다(
    pytester: pytest.Pytester,
) -> None:
    """`-m llm_widget` 실행이다. 그 시험의 트레이스만 세고 `llm` 시험과 가짜 모델의 시험은 돌지
    않는다."""
    pytester.makeconftest(CONFTEST)
    pytester.makeini(LLM_INI)
    pytester.makepyfile(WIDGET_TRACED)

    result = pytester.runpytest("-p", "no:cacheprovider", "-m", "llm_widget")

    assert result.ret == pytest.ExitCode.OK
    result.stdout.fnmatch_lines(
        [
            "*LLM 토큰 합계 46(입력 40, 출력 6)*트레이스 1개, 모델 호출 2건. 일지*",
            "*= 1 passed, 2 deselected in *",
        ],
        consecutive=True,
    )


def test_기본_실행은_두_LLM_마커를_돌리지_않고_합계를_찍지_않는다(
    pytester: pytest.Pytester,
) -> None:
    """기본 실행의 마커 제외(`pyproject.toml` 의 `addopts` 의 `-m`)다. 끝에 0 이 찍히면 LLM 테스트를
    돌렸다고 읽힌다."""
    pytester.makeconftest(CONFTEST)
    pytester.makeini(LLM_INI)
    pytester.makepyfile(WIDGET_TRACED)

    result = pytester.runpytest("-p", "no:cacheprovider", "-m", DEFAULT_MARKERS)

    assert result.ret == pytest.ExitCode.OK
    result.stdout.fnmatch_lines(["*= 1 passed, 2 deselected in *"])
    assert "LLM 토큰 합계" not in result.stdout.str()
