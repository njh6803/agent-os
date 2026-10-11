"""`tools/rewrap_comments.py` 의 폭과 넘친 줄 판정을 ruff 의 E501 과 대조한다(대기열 112).

그 도구의 독스트링과 상수 주석, `tests/tools/test_rewrap_comments.py` 의 시험 넷(폭, 조합형 한글
자모, URL·덩어리 하나, 줄 끝 지시 주석)이 근거로 든다. 재는 것은 둘이다.

1. 폭. 이 저장소의 추적 파이썬 파일 전부를 `ruff check --isolated --select E501 --line-length 1` 로
   돌리면 덩어리가 둘 이상인 줄마다 "Line too long (폭 > 1)" 이 나온다. 그 폭을 도구가 재는
   부분(`measured` — 줄 끝 지시 주석을 뺀다)의 `width` 와 줄마다 견준다. 한글, 가운뎃점, 화살표,
   줄표, `# noqa: E402` 로 끝나는 줄 같은 이 저장소의 실제 줄이 든다. 저장소에 없는 결합 문자, 폭
   없는 공백, 조합형(NFD) 한글 자모는 임시 파일의 줄로 더한다.
2. 넘친 줄의 예외. 덩어리가 하나인 줄, 줄 길이 안에서 시작한 URL 로 끝나는 줄, 줄 끝 지시 주석(ruff
   가 빼는 것과 빼지 않는 것), 코드를 들지 않은 noqa 와 그 반례를 임시 파일에 두고
   `--line-length 100` 의 E501 과 도구의 `overlong` 을 줄마다 견준다.

어긋난 줄을 찍고, 하나라도 있으면 1로 끝난다. 이 저장소는 읽기만 하고 임시 파일은 끝에 지운다.
돌리는 법: `PYTHONUTF8=1 uv run python .scratch/harness/probes/rewrap_width.py`
"""

import json
import subprocess
import sys
import tempfile
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))

from tools.rewrap_comments import comment_columns, measured, overlong, width  # noqa: E402

URL = "https://example.com/" + "a" * 30
LONG_CODE = "x = " + "1 + " * 30 + "1"
# 이스케이프가 아니라 chr() 다. 편집 도구가 이스케이프를 날것으로 바꾼다(대기열 160).
EXTRA_WIDTH_LINES = [
    "# " + ("e" + chr(0x0301) + " ") * 10,
    "# " + ("a" + chr(0x200B) + "b ") * 10,
    "# " + "가나 " * 10,
    "# " + (unicodedata.normalize("NFD", "한글을") + " ") * 10,
    "# " + (chr(0x1100) + chr(0x1161) + chr(0xD7B0) + chr(0xD7CB) + " ") * 10,
]
EXCEPTION_LINES = [
    "# see " + "b" * 70 + " " + URL,
    "# " + "b" * 100 + " " + URL,
    "#" + "c" * 120,
    "# " + "c" * 120,
    "# " + "가" * 49,
    "# " + "가" * 50,
    "x = 1  # " + "d " * 50,
    "x = 1  # noqa: B010 " + "d " * 50,
    "x = 1  # NOQA " + "d " * 50,
    "x = 1  # nosec " + "d " * 50,
    "x = 1  # pyright: basic " + "d " * 50,
    "x = 1  # pylint: disable=x " + "d " * 50,
    "x = 1  # flake8: noqa " + "d " * 50,
    "x = 1  # ruff: noqa " + "d " * 50,
    "x = 1  # isort: skip " + "d " * 50,
    "x = 1  # fmt: skip " + "d " * 50,
    "x = 1  # mypy: x " + "d " * 50,
    "x = 1  # pragma: no cover " + "d " * 50,
    LONG_CODE + "  # noqa",
    LONG_CODE + "  # noqa: E501",
    LONG_CODE + "  # noqa: B010",
    "# noqa: B010 " + "d " * 50,
]


def ruff(paths: list[str], line_length: int) -> dict[tuple[str, int], str]:
    """(파일, 행) 마다 E501 메시지."""
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "ruff",
            "check",
            "--isolated",
            "--no-cache",
            "--select",
            "E501",
            "--line-length",
            str(line_length),
            "--output-format",
            "json",
            *paths,
        ],
        capture_output=True,
        check=False,
        cwd=ROOT,
    )
    diagnostics = json.loads(completed.stdout.decode("utf-8"))
    return {
        (Path(item["filename"]).resolve().as_posix(), item["location"]["row"]): item["message"]
        for item in diagnostics
        if item["code"] == "E501"
    }


def ruff_width(message: str) -> int:
    """E501 메시지 "Line too long (102 > 1)" 의 102."""
    return int(message.split("(", 1)[1].split(" > ", 1)[0])


def main() -> int:
    version = subprocess.run(
        [sys.executable, "-m", "ruff", "--version"], capture_output=True, text=True, check=False
    ).stdout.strip()
    listed = subprocess.run(
        ["git", "ls-files", "-z", "*.py"], cwd=ROOT, capture_output=True, check=True
    )
    files = [(ROOT / name).resolve() for name in listed.stdout.decode("utf-8").split("\0") if name]
    mismatches: list[str] = []
    with tempfile.TemporaryDirectory() as scratch:
        extra = (Path(scratch) / "extra_width.py").resolve()
        extra.write_text("\n".join(EXTRA_WIDTH_LINES) + "\n", encoding="utf-8", newline="\n")
        exceptions = (Path(scratch) / "exceptions.py").resolve()
        exceptions.write_text("\n".join(EXCEPTION_LINES) + "\n", encoding="utf-8", newline="\n")

        widths = ruff([str(path) for path in [*files, extra]], 1)
        for path in [*files, extra]:
            source = path.read_bytes().decode("utf-8")
            columns = comment_columns(source)
            for row, line in enumerate(source.split("\n"), 1):
                message = widths.get((path.as_posix(), row))
                if message is None:
                    continue
                part = measured(line.removesuffix("\r"), columns.get(row - 1))
                ours = None if part is None else width(part)
                if ruff_width(message) != ours:
                    shown = path.relative_to(ROOT) if path.is_relative_to(ROOT) else path.name
                    mismatches.append(f"폭 {shown}:{row}: ruff {ruff_width(message)}, 도구 {ours}")

        flagged = ruff([str(exceptions)], 100)
        columns = comment_columns(exceptions.read_text(encoding="utf-8"))
        for row, line in enumerate(EXCEPTION_LINES, 1):
            by_ruff = (exceptions.as_posix(), row) in flagged
            by_tool = overlong(line, 100, columns.get(row - 1))
            if by_ruff != by_tool:
                mismatches.append(f"예외 {row}행: ruff {by_ruff}, 도구 {by_tool}: {line[:40]}")

    for mismatch in mismatches:
        print(mismatch)
    print(
        f"{version}. 폭 대조 {len(widths)}줄(파일 {len(files)}개와 더한 줄 "
        f"{len(EXTRA_WIDTH_LINES)}), 예외 대조 {len(EXCEPTION_LINES)}줄, "
        f"어긋남 {len(mismatches)}줄."
    )
    return 1 if mismatches else 0


if __name__ == "__main__":
    raise SystemExit(main())
