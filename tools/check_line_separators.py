"""보이지 않는 줄 구분 문자 검사. 추적 텍스트 파일의 날것 U+2028·U+2029·U+0085 를 잡는다(대기열 22).

편집 도구가 테스트 소스의 U+2028·U+2029 이스케이프를 날것 문자로 저장했다(PR #58). pytest·ruff·
pyright 가 모두 초록이었고, 리뷰어는 문자가 보이지 않아 "U+2028 테스트가 없다" 는 오탐을 냈다.
파이썬의 `str.splitlines` 는 셋을 줄 끝으로 읽으므로 줄 단위로 보는 코드가 같은 파일을 다른 줄
수로 본다.
고정된 문자 패턴이라 규칙이 아니라 검사다. 선례는 `tools/check_type_escapes.py`.

이 파일과 테스트는 그 문자를 이스케이프가 아니라 `chr()` 로 만든다. 이 검사를 쓰던 세션의 편집
도구가 역슬래시-u 이스케이프를 다시 날것으로 저장해 첫 실행에서 이 파일 자신이 잡혔다(2026-09-28).

텍스트 파일은 처음 8000 바이트에 NUL 이 없는 파일이다(git 의 `buffer_is_binary` 와 같은 경계).
UTF-8 BOM 은 벗기고 센다 — 편집기는 BOM 을 보이지 않으므로 열이 하나 밀린다. UTF-8 로 읽히지 않는
텍스트 파일과 읽을 수 없는 경로(없는 파일, 디렉터리)는 판정할 수 없어 어긋남으로 낸다 — 조용히
지나가면 훑지 않은 것이 초록이 된다. 인자 없이 부르면 인덱스의 일반 파일(모드 100644·100755)만
훑고, 작업 트리에서 지웠지만 아직 스테이지하지 않은 파일은 건너뛴다(볼 내용이 없다). 서브모듈과
심볼릭 링크는 대상이 아니다. 줄 번호는 개행(`\\n`)으로만, 열은 코드 포인트로 센다. `splitlines` 로
세면 잡으려는 문자가 줄을 늘려 자리가 틀린다.

못 보는 것: 이스케이프로 쓴 것(소스의 역슬래시-u 여섯 글자)은 날것이 아니라 잡지 않는다 — 그것이
맞는 꼴이다. 추적되지 않은 파일. UTF-16 파일 — 대개 NUL 이 있어 이진으로 보고, NUL 이 없으면
UTF-8 로 잘못 읽는다. 다른 보이지 않는 문자(BOM, 전각 공백, 줄바꿈 없는 공백, 폭 없는 공백 등)는
대상이 아니다 — 같은 세션에서 그 넷 중 셋의 이스케이프도 날것이 됐고 이 검사는 잡지 못했다.

사용: `uv run python tools/check_line_separators.py [파일 ...]`. 인자가 없으면 추적 파일 전부.
pre-commit 은 스테이지된 텍스트 파일을 한 프로세스로 넘긴다(`types: [text]`, `require_serial`).
"""

from __future__ import annotations

import io
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# 이스케이프가 아니라 chr() 다. 편집 도구가 이스케이프를 날것으로 바꾸면 이 파일이 자기 검사에
# 걸린다(2026-09-28 실제로 그랬다).
SEPARATORS = {
    chr(0x2028): "LINE SEPARATOR",
    chr(0x2029): "PARAGRAPH SEPARATOR",
    chr(0x0085): "NEXT LINE",
}
# git 의 xdiff-interface.c `FIRST_FEW_BYTES`. 이 길이 안에 NUL 이 있으면 이진이다.
_TEXT_PROBE = 8000
# 인덱스에서 내용이 있는 일반 파일의 모드. 160000(서브모듈)과 120000(링크)은 뺀다.
_REGULAR_MODES = frozenset({"100644", "100755"})
HINT = (
    "소스에 그 문자가 필요하면 chr(0x2028) 처럼 만든다. "
    "이스케이프는 편집 도구가 날것으로 바꿀 수 있다."
)


def is_text(data: bytes) -> bool:
    """git 과 같은 판정. 처음 8000 바이트에 NUL 이 없으면 텍스트다."""
    return b"\0" not in data[:_TEXT_PROBE]


def separators_in(text: str) -> list[str]:
    """날것 줄 구분 문자의 자리. 항목은 `"<줄>:<열>: U+XXXX <이름>"`. 줄은 개행으로만 나눈다."""
    found: list[str] = []
    for lineno, line in enumerate(text.split("\n"), 1):
        for column, character in enumerate(line, 1):
            name = SEPARATORS.get(character)
            if name is not None:
                found.append(f"{lineno}:{column}: U+{ord(character):04X} {name}")
    return found


def problems_in(data: bytes) -> list[str]:
    """파일 하나의 어긋남. 텍스트가 아니면 비고, UTF-8 이 아니면 그 자체가 어긋남이다."""
    if not is_text(data):
        return []
    try:
        text = data.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        where = f"{error.reason}, 바이트 {error.start}"
        return [f"0:0: UTF-8 로 읽을 수 없어 판정하지 못했다 ({where})"]
    return separators_in(text)


def tracked_files(root: Path = ROOT) -> list[Path]:
    """인덱스의 일반 파일 중 작업 트리에 있는 것. 인자 없이 부를 때의 범위다."""
    listing = subprocess.run(
        ["git", "ls-files", "-s", "-z"], cwd=root, capture_output=True, check=True
    )
    files: list[Path] = []
    for entry in listing.stdout.decode("utf-8").split("\0"):
        if not entry:
            continue
        meta, name = entry.split("\t", 1)
        path = root / name
        if meta.split(" ", 1)[0] in _REGULAR_MODES and path.is_file():
            files.append(path)
    return files


def _problems_of(path: Path) -> list[str]:
    try:
        data = path.read_bytes()
    except OSError as error:
        return [f"0:0: 파일을 읽을 수 없어 판정하지 못했다 ({error.strerror})"]
    return problems_in(data)


def main(paths: list[Path] | None = None, root: Path = ROOT) -> int:
    """`paths` 를(없으면 추적 파일 전부) 훑는다. 어긋남이 하나라도 있으면 1."""
    problems: list[str] = []
    found_separator = False
    for path in paths if paths is not None else tracked_files(root):
        shown = path.relative_to(root).as_posix() if path.is_relative_to(root) else path.as_posix()
        found = _problems_of(path)
        found_separator = found_separator or any(" U+" in problem for problem in found)
        problems.extend(f"{shown}:{problem}" for problem in found)
    for problem in problems:
        print(problem)
    if found_separator:
        print(HINT)
    return 1 if problems else 0


if __name__ == "__main__":
    stream = sys.stdout
    if isinstance(stream, io.TextIOWrapper):
        stream.reconfigure(encoding="utf-8")
    raise SystemExit(main([Path(argument) for argument in sys.argv[1:]] or None))
