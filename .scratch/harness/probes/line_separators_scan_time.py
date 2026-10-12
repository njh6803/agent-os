"""`tools/check_line_separators.py` 의 저장소 전체 훑기 시간을 세 판으로 견준다(대기열 52).

- 옛 판: 줄 구분 문자 셋만 보던 판. `git show <리비전>:tools/check_line_separators.py` 로 꺼낸다.
- 글자마다: 지금 판의 판정에서 `.py` 의 비 ASCII 글자마다 범주를 묻는 판. 이 프로브 안에 둔다.
- 지금 판: 작업 트리의 판. 서로 다른 글자(`set`)에만 범주를 묻는다.

세 판 모두 같은 추적 파일 목록을 받고, 판마다 `ROUNDS` 번 돌아 가장 짧은 시간을 적는다. 출력은
판마다 한 줄(어긋남 수, 초)이다. 어긋남 수가 판끼리 다르면 판정이 갈린 것이니 시간을 견주지 않는다.

사용: 저장소 루트에서 `uv run python .scratch/harness/probes/line_separators_scan_time.py [리비전]`.
리비전의 기본값은 대기열 52 를 들이기 전의 main(`67dbb4a`)이다.
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import re
import subprocess
import sys
import tempfile
import time
import unicodedata
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[3]
ROUNDS = 3


def load(name: str, path: Path) -> ModuleType:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"{path} 를 불러오지 못했다")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def per_character(current: ModuleType) -> ModuleType:
    """지금 판을 하나 더 불러 `.py` 의 판정을 비 ASCII 글자마다 범주를 묻는 꼴로 바꾼다."""
    module = load("per_character", ROOT / "tools" / "check_line_separators.py")
    non_ascii = re.compile(f"[{chr(0x80)}-{chr(0x10FFFF)}]")
    either = re.compile(f"{current._SEPARATOR_PATTERN}|{non_ascii.pattern}")

    def problems_in(data: bytes, suffix: str) -> list[str]:
        if not module.is_text(data):
            return []
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError:
            return ["0:0: UTF-8 로 읽을 수 없다"]
        if suffix not in module.SOURCE_SUFFIXES:
            return module.separators_in(text)
        found: list[str] = []
        for line, column, character in module._spots(text, either):
            name = module.SEPARATORS.get(character)
            if name is None and unicodedata.category(character) in {"Zs", "Cf"}:
                name = unicodedata.name(character, "")
            if name is not None:
                found.append(f"{line}:{column}: U+{ord(character):04X} {name}")
        return found

    module.problems_in = problems_in
    return module


def timed(module: ModuleType, files: list[Path]) -> tuple[int, float]:
    best = float("inf")
    count = 0
    for _ in range(ROUNDS):
        started = time.perf_counter()
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            module.main(files, root=ROOT)
        best = min(best, time.perf_counter() - started)
        count = sum(1 for line in captured.getvalue().splitlines() if " U+" in line)
    return count, best


def main() -> int:
    revision = sys.argv[1] if len(sys.argv) > 1 else "67dbb4a"
    old_source = subprocess.run(
        ["git", "show", f"{revision}:tools/check_line_separators.py"],
        cwd=ROOT,
        capture_output=True,
        check=True,
    ).stdout
    with tempfile.TemporaryDirectory() as scratch:
        old_path = Path(scratch) / "old_check.py"
        old_path.write_bytes(old_source)
        old = load("old_check", old_path)
        current = load("current_check", ROOT / "tools" / "check_line_separators.py")
        files = current.tracked_files(ROOT)
        print(f"추적 파일 {len(files)}개, 판마다 {ROUNDS}번 가운데 가장 짧은 시간")
        for label, module in (
            (f"옛 판({revision})", old),
            ("글자마다", per_character(current)),
            ("지금 판", current),
        ):
            count, seconds = timed(module, files)
            print(f"{label}: 어긋남 {count}, {seconds:.3f}초")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
