"""tools/hook_bash_gate_pipe.py 의 순수 함수. stdin 을 읽는 main 은 실제 실행으로 확인한다.

대기열 19 의 네 사건이 이 테스트의 입력이다 — 게이트를 `tail` 에 넘긴 뒤 `$?` 를 읽었다.
"""

from __future__ import annotations

from tools.hook_bash_gate_pipe import is_gate, warnings_for


def test_게이트_명령_자리를_알아본다() -> None:
    assert is_gate("uv run pytest -q")
    assert is_gate("PYTHONUTF8=1 uv run --no-sync python tools/check_instructions.py")
    assert is_gate("uv run --env-file .env pytest -m llm")
    assert is_gate(" uv run ruff check .")
    assert is_gate("uv run lint-imports")
    assert is_gate("python -m pytest tests/tools")
    assert is_gate("py -3 -m pytest -q")
    assert not is_gate("echo pytest")
    assert not is_gate("git log")
    assert not is_gate("grep -rn pyright src")


def test_web_검증_명령과_Playwright_실행도_게이트다() -> None:
    """파이프 뒤 `$?` 가 판정을 속이는 것은 명령의 언어와 무관하다(web-admin 티켓 01).

    e2e 스크립트의 이름은 아직 없어서 Playwright 실행 자체를 게이트로 본다.
    """
    assert is_gate("pnpm -C web verify")
    assert is_gate("pnpm --dir web run verify")
    assert is_gate("pnpm verify")
    assert is_gate("pnpm -C web exec playwright test")
    assert is_gate("npx playwright test --project chromium")
    assert not is_gate("pnpm -C web install --frozen-lockfile")
    assert not is_gate("pnpm -C web exec playwright install --with-deps")
    assert not is_gate("echo pnpm -C web verify")


def test_파이프에_묻힌_web_검증_명령과_e2e_를_경고한다() -> None:
    assert len(warnings_for("pnpm -C web verify 2>&1 | tail -5")) == 1
    assert len(warnings_for("pnpm -C web exec playwright test | tail -20")) == 1


def test_단독으로_친_web_검증_명령과_e2e_는_조용하다() -> None:
    assert warnings_for("pnpm -C web verify") == []
    assert warnings_for("pnpm -C web exec playwright test") == []


def test_파이프_마지막이_아닌_게이트를_경고한다() -> None:
    """PR #56 세션: `| tail -3; echo $?` 로 tail 의 종료 코드를 읽었다."""
    warnings = warnings_for("PYTHONUTF8=1 uv run pytest -q 2>&1 | tail -3; echo $?")

    assert len(warnings) == 1
    assert "파이프의 마지막이 아니다" in warnings[0]


def test_서브셸_안의_파이프도_본다() -> None:
    assert len(warnings_for("(uv run pytest -q | tail -3)")) == 1


def test_파이프_경고가_있으면_dollar_question_경고는_겹쳐_내지_않는다() -> None:
    """같은 원인이다. 한 명령에 문장 둘을 넣지 않는다."""
    assert len(warnings_for("uv run pytest -q | tail -3; echo $?")) == 1


def test_체인_뒤의_dollar_question_을_경고한다() -> None:
    """대기열 11: 검사 일곱을 && 로 잇고 `$?` 를 읽었더니 앞 것이 아니라 마지막 것이었다."""
    warnings = warnings_for("uv run ruff check . && echo done; echo $?")

    assert len(warnings) == 1
    assert "$?" in warnings[0]


def test_dollar_question_마다_바로_앞_조각을_본다() -> None:
    """PR #91 리뷰: 첫 `$?` 만 보면 둘째가 echo 의 종료 코드를 읽는 것을 놓친다."""
    warnings = warnings_for("uv run ruff check .; echo $?; uv run pyright; echo done; echo $?")

    assert len(warnings) == 1
    assert "pyright" in warnings[0]


def test_인용된_옵션_값은_자리표시자로_남겨_명령_위치를_지킨다() -> None:
    """PR #91 리뷰: 인용을 지우면 뒤 낱말이 옵션 값 자리로 밀린다."""
    assert len(warnings_for('uv run --project "작업 경로" pytest -q | tail -3')) == 1


def test_게이트_바로_뒤의_dollar_question_은_경고하지_않는다() -> None:
    assert warnings_for("uv run ruff check . && uv run pyright; echo $?") == []
    assert warnings_for('uv run pytest -q; echo "exit=$?"') == []


def test_파이프_없는_게이트와_게이트_아닌_파이프는_경고하지_않는다() -> None:
    assert warnings_for("uv run pytest -q") == []
    assert warnings_for("git log --oneline | head -5") == []
    assert warnings_for("uv run ruff check . && uv run ruff format --check .") == []


def test_인용과_heredoc_안의_게이트_낱말은_보지_않는다() -> None:
    assert warnings_for("echo 'uv run pytest | tail' | cat") == []
    assert warnings_for("cat <<'EOF'\nuv run pytest | tail\nEOF\necho $?") == []
