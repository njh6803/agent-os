"""tools/probe_kit.py 의 두 가지. 회차의 표지 세기(`Rounds`)와 하위 프로세스의 줄을 제한 시간
안에 읽기(`LineReader`)다. 읽기는 실제 파이프(`os.pipe`)에 이 시험이 줄을 쓰고 닫아 본다.
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

import pytest
from tools.probe_kit import LineReader, Rounds


def test_모든_회차가_측정이면_0으로_끝난다() -> None:
    rounds = Rounds()
    rounds.record("1회차", measured=True, result="알렸다")
    rounds.record("2회차", measured=True, result="알렸다")

    assert rounds.exit_code() == 0
    assert [entry.label for entry in rounds.measured] == ["1회차", "2회차"]
    assert rounds.unmeasured == []


def test_측정이_아닌_회차가_하나라도_있으면_1로_끝나고_따로_적는다() -> None:
    rounds = Rounds()
    rounds.record("1회차", measured=True, result="알렸다")
    rounds.record("2회차", measured=False, result="커밋이 뜨기 전에 끝났다")

    assert rounds.exit_code() == 1
    summary = rounds.summary()
    assert "측정 1회차" in summary
    assert "측정 아님 1회차" in summary
    assert "2회차: 커밋이 뜨기 전에 끝났다" in summary


def test_회차가_없으면_측정한_것이_없어_1로_끝난다() -> None:
    rounds = Rounds()

    assert rounds.exit_code() == 1
    assert "측정 0회차" in rounds.summary()


def test_측정인_회차의_결과를_갈래마다_센다() -> None:
    rounds = Rounds()
    for result in ("알렸다", "침묵", "알렸다"):
        rounds.record("회차", measured=True, result=result)

    assert "알렸다 2" in rounds.summary()
    assert "침묵 1" in rounds.summary()


def test_회차_안의_예외는_측정_아님으로_적고_앞서_모은_회차를_지킨다() -> None:
    rounds = Rounds()
    with rounds.round("1회차") as current:
        current.mark(measured=True, result="알렸다")
    with rounds.round("2회차"):
        raise FileNotFoundError("기록 파일이 없다")
    with rounds.round("3회차") as current:
        current.mark(measured=True, result="알렸다")

    assert [entry.label for entry in rounds.measured] == ["1회차", "3회차"]
    assert [entry.label for entry in rounds.unmeasured] == ["2회차"]
    assert "FileNotFoundError" in rounds.unmeasured[0].result
    assert rounds.exit_code() == 1


@pytest.mark.parametrize("error", [KeyboardInterrupt(), SystemExit(1)])
def test_못_보는_것_프로브를_끊는_예외는_회차로_적지_않고_그대로_올린다(
    error: BaseException,
) -> None:
    rounds = Rounds()
    with rounds.round("1회차") as current:
        current.mark(measured=True, result="알렸다")

    with pytest.raises(type(error)), rounds.round("2회차"):
        raise error

    assert [entry.label for entry in rounds.entries] == ["1회차"]


def test_표지를_적지_않고_끝난_회차는_측정이_아니다() -> None:
    rounds = Rounds()
    with rounds.round("1회차"):
        pass

    assert [entry.label for entry in rounds.unmeasured] == ["1회차"]
    assert rounds.exit_code() == 1


def _pipe() -> tuple[LineReader, int]:
    read_end, write_end = os.pipe()
    return LineReader(os.fdopen(read_end, "rb")), write_end


def test_줄을_받으면_돌려주고_바이트는_풀어_준다() -> None:
    reader, writer = _pipe()
    os.write(writer, "첫 줄\n둘째 줄\n".encode())

    assert reader.readline(5) == "첫 줄\n"
    assert reader.readline(5) == "둘째 줄\n"
    os.close(writer)


def test_줄이_오지_않으면_제한_시간에_None_으로_돌아온다() -> None:
    reader, writer = _pipe()

    started = time.monotonic()
    assert reader.readline(0.2) is None
    assert time.monotonic() - started < 2
    assert not reader.ended
    os.close(writer)


def test_EOF_를_꺼낸_뒤의_읽기와_배출은_기다리지_않는다() -> None:
    reader, writer = _pipe()
    os.write(writer, b"last\n")
    os.close(writer)

    assert reader.readline(5) == "last\n"
    assert reader.readline(5) is None
    assert reader.ended
    started = time.monotonic()
    assert reader.readline(30) is None
    assert reader.drain(30) == []
    assert time.monotonic() - started < 2


def test_배출은_EOF_가_오지_않아도_제한_시간에_끝난다() -> None:
    reader, writer = _pipe()
    os.write(writer, b"a\nb\n")

    started = time.monotonic()
    assert reader.drain(0.3) == ["a\n", "b\n"]
    assert time.monotonic() - started < 3
    assert not reader.ended
    os.close(writer)


def test_글_모드의_흐름도_읽는다(tmp_path: Path) -> None:
    script = tmp_path / "child.py"
    script.write_text("print('하나')\nprint('둘')\n", encoding="utf-8")
    process = subprocess.Popen(
        [sys.executable, str(script)],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONIOENCODING": "utf-8"},
    )
    assert process.stdout is not None
    reader = LineReader(process.stdout)

    assert reader.drain(30) == ["하나\n", "둘\n"]
    assert reader.ended
    process.wait(timeout=30)


def test_글_모드의_흐름에_풀지_못하는_바이트가_와도_앞뒤_줄을_잃지_않는다(tmp_path: Path) -> None:
    """글 흐름의 `readline` 은 덩어리째 풀다 `UnicodeDecodeError`(`ValueError`)를 던져, 흐름을
    닫았다고 보고 읽기를 멈추면 앞 줄까지 잃고 자식은 파이프가 차서 멈춘다(PR 직전 리뷰가 재현)."""
    script = tmp_path / "child.py"
    script.write_text(
        "import sys\nsys.stdout.buffer.write(b'ok1\\n\\xff\\xfe\\nok2\\n')\n", encoding="utf-8"
    )
    process = subprocess.Popen(
        [sys.executable, str(script)],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        encoding="utf-8",
    )
    assert process.stdout is not None
    reader = LineReader(process.stdout)

    assert reader.drain(30) == ["ok1\n", "��\n", "ok2\n"]
    assert reader.ended
    process.wait(timeout=30)


def test_배출은_줄이_계속_와도_제한_시간에_끝난다(tmp_path: Path) -> None:
    """제한 시간은 배출 전체의 마감이다. 줄 사이에만 걸면 계속 쓰는 자식 앞에서 돌아오지 않는다."""
    script = tmp_path / "child.py"
    script.write_text(
        "import time\nwhile True:\n    print('줄', flush=True)\n    time.sleep(0.05)\n",
        encoding="utf-8",
    )
    process = subprocess.Popen(
        [sys.executable, str(script)], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
    )
    assert process.stdout is not None
    reader = LineReader(process.stdout)
    try:
        started = time.monotonic()
        lines = reader.drain(0.5)
        assert time.monotonic() - started < 10
        assert lines
    finally:
        process.kill()
        process.wait(timeout=30)
