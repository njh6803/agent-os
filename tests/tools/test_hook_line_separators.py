"""tools/hook_line_separators.py. 대기열 160: Edit 도구에 넘긴 U+2028 의 이스케이프가 날것 문자로
저장됐고, pre-commit 의 줄 구분 문자 검사가 커밋을 막고서야 드러났다(일지 2026-10-07-19, 한 세션에
두 번). stdin 을 읽는 main 은 tools/run_hooks.py 가 실제 실행으로 본다.

문자는 이스케이프가 아니라 chr() 로 짓는다. 이 훅이 알리려는 바로 그 사고다.
"""

from __future__ import annotations

import codecs
from pathlib import Path

import pytest
from tools.check_line_separators import SEPARATORS as CHECKED
from tools.hook_line_separators import SEPARATORS, context_for

LS = chr(0x2028)
PS = chr(0x2029)
NEL = chr(0x0085)
BACKSLASH = chr(0x5C)


def _쓴다(tmp_path: Path, data: bytes, name: str = "module.py") -> str:
    path = tmp_path / name
    path.write_bytes(data)
    return str(path)


def test_날것_줄_구분_문자의_줄과_열을_알린다(tmp_path: Path) -> None:
    path = _쓴다(tmp_path, f'x = 1\nTEXT = "a{LS}b"\n'.encode())

    context = context_for("Edit", path)

    assert context is not None
    assert "2행 10열 U+2028 LINE SEPARATOR" in context
    assert "chr(0x2028)" in context
    assert "tools/check_line_separators.py" in context


def test_커밋_전_검사와_같은_세_문자를_본다() -> None:
    """훅은 단독 실행이라 검사를 import 하지 않고 같은 판정을 옮겨 적었다. 갈리면 여기서 잡는다."""
    assert SEPARATORS == CHECKED


def test_줄은_개행으로만_세고_열은_코드_포인트로_센다(tmp_path: Path) -> None:
    """`splitlines` 로 세면 잡으려는 문자가 줄을 늘려 자리가 틀린다."""
    context = context_for("Write", _쓴다(tmp_path, f"a{LS}b{PS}c\n가{NEL}\n".encode()))

    assert context is not None
    assert "1행 2열 U+2028" in context
    assert "1행 4열 U+2029 PARAGRAPH SEPARATOR" in context
    assert "2행 2열 U+0085 NEXT LINE" in context


def test_BOM_은_벗기고_열을_센다(tmp_path: Path) -> None:
    context = context_for("Edit", _쓴다(tmp_path, codecs.BOM_UTF8 + f"a{LS}\n".encode()))

    assert context is not None
    assert "1행 2열" in context


def test_이스케이프로_쓴_것은_맞는_꼴이라_침묵한다(tmp_path: Path) -> None:
    escaped = f'TEXT = "{BACKSLASH}u2028"\nSEPARATOR = chr(0x2028)\n'

    assert context_for("Edit", _쓴다(tmp_path, escaped.encode())) is None


def test_이진_파일과_UTF8_이_아닌_파일은_침묵한다(tmp_path: Path) -> None:
    """UTF-8 로 읽히지 않는 파일은 커밋 전 검사가 판정하지 못했다고 막는다."""
    assert context_for("Write", _쓴다(tmp_path, b"\0" + LS.encode(), "a.bin")) is None
    assert context_for("Write", _쓴다(tmp_path, b"\xff" + LS.encode(), "b.txt")) is None


def test_NUL_은_처음_8000_바이트_안에서만_이진의_표지다(tmp_path: Path) -> None:
    """git 의 `buffer_is_binary` 와 같은 경계다(검사의 독스트링)."""
    assert context_for("Edit", _쓴다(tmp_path, b"a" * 7999 + b"\0" + LS.encode())) is None
    assert context_for("Edit", _쓴다(tmp_path, b"a" * 8000 + b"\0" + LS.encode())) is not None


def test_Write_와_Edit_밖의_도구는_보지_않는다(tmp_path: Path) -> None:
    assert context_for("NotebookEdit", _쓴다(tmp_path, LS.encode())) is None


def test_줄_구분_문자가_없으면_침묵한다(tmp_path: Path) -> None:
    assert context_for("Write", _쓴다(tmp_path, "# 한글 주석\nx = 1\n".encode())) is None


def test_많으면_앞의_열_개만_적고_나머지는_센다(tmp_path: Path) -> None:
    context = context_for("Edit", _쓴다(tmp_path, (LS * 12).encode()))

    assert context is not None
    assert "12개" in context
    assert "1행 10열" in context
    assert "1행 11열" not in context
    assert "외 2개" in context


def test_읽지_못하거나_없는_파일은_침묵한다(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """계기 훅은 fail-open 이다. 판정은 커밋 전 검사에 남는다."""
    path = _쓴다(tmp_path, LS.encode())

    assert context_for("Write", str(tmp_path / "gone.py")) is None
    assert context_for("Write", str(tmp_path)) is None

    def unreadable(self: Path) -> bytes:
        raise PermissionError(self)

    monkeypatch.setattr(Path, "read_bytes", unreadable)

    assert context_for("Edit", path) is None
