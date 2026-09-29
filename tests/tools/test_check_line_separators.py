"""tools/check_line_separators.py. 날것 U+2028·U+2029·U+0085 를 잡는 검사(대기열 22).

이 파일은 그 문자를 `chr()` 로 만든다. 역슬래시-u 이스케이프로 쓰면 편집 도구가 날것으로 저장할 수
있고(PR #58, 그리고 이 검사를 쓰던 2026-09-28 세션에서 다시), 그러면 검사가 이 파일을 잡는다.
고정하는 것은 셋을 잡는 것, 이스케이프 여섯 글자는 잡지 않는 것, 줄 번호를 개행으로만 세는 것.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from tools.check_line_separators import (
    ROOT,
    is_text,
    main,
    problems_in,
    separators_in,
    tracked_files,
)

LINE_SEPARATOR = chr(0x2028)
PARAGRAPH_SEPARATOR = chr(0x2029)
NEXT_LINE = chr(0x0085)


def test_날것_줄_구분_문자_셋을_줄과_열로_잡는다() -> None:
    text = f"a\nb{LINE_SEPARATOR}c\nd{PARAGRAPH_SEPARATOR}\n{NEXT_LINE}e\n"

    assert separators_in(text) == [
        "2:2: U+2028 LINE SEPARATOR",
        "3:2: U+2029 PARAGRAPH SEPARATOR",
        "4:1: U+0085 NEXT LINE",
    ]


def test_줄_번호는_개행으로만_센다() -> None:
    """U+2028 이 줄을 늘리면 그 뒤의 자리가 전부 밀린다. `splitlines` 가 아니라 `split` 이다."""
    assert separators_in(f"a{LINE_SEPARATOR}b\nc{PARAGRAPH_SEPARATOR}d\n") == [
        "1:2: U+2028 LINE SEPARATOR",
        "2:2: U+2029 PARAGRAPH SEPARATOR",
    ]


def test_이스케이프로_쓴_것은_잡지_않는다() -> None:
    """소스에 역슬래시-u 여섯 글자로 쓴 것이 맞는 꼴이다."""
    source = 'text = "\\u2028\\u2029\\x85"\n'

    assert "\\u2028" in source
    assert separators_in(source) == []
    assert problems_in(source.encode("utf-8")) == []


def test_NUL_이_있는_파일은_텍스트가_아니라_보지_않는다() -> None:
    binary = b"PNG\0\0\0" + LINE_SEPARATOR.encode("utf-8")

    assert not is_text(binary)
    assert problems_in(binary) == []


def test_이진_판정의_경계는_git_과_같은_8000_바이트다() -> None:
    """git 의 buffer_is_binary 는 처음 8000 바이트를 본다. 그 뒤의 NUL 은 텍스트다."""
    assert not is_text(b"a" * 7999 + b"\0")
    assert is_text(b"a" * 8000 + b"\0")


def test_UTF_8_BOM_은_열로_세지_않는다() -> None:
    """편집기는 BOM 을 보이지 않는다. 첫 줄의 열이 하나 밀리면 둘째 줄과 기준이 갈린다."""
    data = b"\xef\xbb\xbf" + f"a{LINE_SEPARATOR}b\nc{LINE_SEPARATOR}d\n".encode()

    assert problems_in(data) == ["1:2: U+2028 LINE SEPARATOR", "2:2: U+2028 LINE SEPARATOR"]


def test_BOM_뒤의_무효_바이트는_파일의_바이트_자리로_알린다() -> None:
    """utf-8-sig 는 BOM 을 떼고 센다. 알리는 자리는 파일 기준이어야 편집기에서 찾는다."""
    problems = problems_in(b"\xef\xbb\xbf\xff")

    assert len(problems) == 1
    assert "바이트 3)" in problems[0]


def test_UTF_8_로_읽히지_않는_텍스트_파일은_어긋남이다() -> None:
    """판정할 수 없는 파일을 조용히 통과시키지 않는다."""
    problems = problems_in("한글".encode("cp949"))

    assert len(problems) == 1
    assert "UTF-8" in problems[0]


def test_읽을_수_없는_경로는_트레이스백이_아니라_어긋남이고_나머지는_판정한다(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    dirty = tmp_path / "dirty.txt"
    dirty.write_text(f"a{LINE_SEPARATOR}b\n", encoding="utf-8", newline="\n")
    (tmp_path / "adir").mkdir()

    assert main([tmp_path / "없다.txt", tmp_path / "adir", dirty], root=tmp_path) == 1

    lines = capsys.readouterr().out.splitlines()
    assert lines[0].startswith("없다.txt:0:0: 파일을 읽을 수 없어")
    assert lines[1].startswith("adir:0:0: 파일을 읽을 수 없어")
    assert lines[2] == "dirty.txt:1:2: U+2028 LINE SEPARATOR"


def test_디코드_실패만_있으면_chr_힌트를_붙이지_않는다(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """힌트는 날것 문자의 처방이다. cp949 파일의 처방이 아니다."""
    cp949 = tmp_path / "cp949.txt"
    cp949.write_bytes("한글".encode("cp949"))

    assert main([cp949], root=tmp_path) == 1
    assert "chr(0x2028)" not in capsys.readouterr().out


def _git(repo: Path, *arguments: str) -> str:
    process = subprocess.run(
        ["git", *arguments], cwd=repo, capture_output=True, text=True, check=True
    )
    return process.stdout.strip()


def test_인자_없이_부르면_지운_파일과_서브모듈은_건너뛴다(tmp_path: Path) -> None:
    """인덱스에는 있고 작업 트리에서 지운 파일, gitlink(160000)가 트레이스백을 내지 않는다."""
    _git(tmp_path, "init", "-q")
    (tmp_path / "a.txt").write_text("a\n", encoding="utf-8", newline="\n")
    (tmp_path / "b.txt").write_text("b\n", encoding="utf-8", newline="\n")
    _git(tmp_path, "add", "a.txt", "b.txt")
    commit = _git(tmp_path, "hash-object", "-w", "a.txt")
    _git(tmp_path, "update-index", "--add", "--cacheinfo", f"160000,{commit},sub")
    (tmp_path / "sub").mkdir()
    (tmp_path / "b.txt").unlink()

    assert tracked_files(tmp_path) == [tmp_path / "a.txt"]
    assert main(root=tmp_path) == 0


def test_이_저장소의_추적_파일에_날것_줄_구분_문자가_없다() -> None:
    assert main() == 0


def test_날것_문자가_있는_파일이_섞이면_실패한다(tmp_path: Path) -> None:
    clean = tmp_path / "clean.txt"
    clean.write_text("a\nb\n", encoding="utf-8", newline="\n")
    dirty = tmp_path / "dirty.py"
    dirty.write_text(f'x = "a{LINE_SEPARATOR}b"\n', encoding="utf-8", newline="\n")

    assert main([clean]) == 0
    assert main([clean, dirty]) == 1


def test_CLI_진입점이_인자로_받은_파일의_날것_문자를_출력한다(tmp_path: Path) -> None:
    """pre-commit 이 부르는 진입점 그대로 — 파일 경로를 인자로 받는다(tests.md)."""
    dirty = tmp_path / "dirty.py"
    dirty.write_text(f'x = "a{LINE_SEPARATOR}b"\n', encoding="utf-8", newline="\n")

    process = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "check_line_separators.py"), str(dirty)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=ROOT,
        env={**os.environ, "PYTHONUTF8": "1"},
        check=False,
    )

    assert process.returncode == 1
    assert "dirty.py:1:7: U+2028 LINE SEPARATOR" in process.stdout
    assert "chr(0x2028)" in process.stdout
