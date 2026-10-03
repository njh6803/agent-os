"""소비 지점 모듈을 저장소의 pyright strict 설정과 타입 우회 판정자로 검사한다.

pyright 는 점 디렉터리와 `include` 밖을 검사 없이 "0 errors"로 넘기므로(operations.md 환경 규약
상세) 검사하는 동안만 파일을 `tests/_probe_web_widget_*.py`로 복사하고 끝나면 지운다. 실행 위치는
저장소 루트, 명령은 `uv run pyright`이고, 임시 환경은 `--venvpath`로 넘긴다(`venv` 설정이
`.venv`라 `<환경 루트>/<후보>/.venv`를 읽는다). 저장소 `.venv`에는 pyjwt 가 이미 간접 의존으로
깔려 있어 그 판도 따로 잰다. 분석 여부는 `summary.filesAnalyzed`로 본다.

    PYTHONUTF8=1 uv run python .scratch/web-widget/probes/jwt_verify/check_types.py <환경 루트>
"""

from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
TESTS = ROOT / "tests"
PREFIX = "_probe_web_widget_"

# (표시 이름, 후보 환경 이름 또는 None=저장소 .venv, 배포 이름, 검사할 파일들)
TARGETS: list[tuple[str, str | None, str, list[str]]] = [
    ("pyjwt(임시 환경)", "pyjwt", "pyjwt", ["consume_pyjwt.py", "control_pyjwt.py"]),
    ("pyjwt(저장소 .venv)", None, "pyjwt", ["consume_pyjwt.py", "control_pyjwt.py"]),
    ("joserfc(임시 환경)", "joserfc", "joserfc", ["consume_joserfc.py", "control_joserfc.py"]),
    ("jwcrypto(임시 환경)", "jwcrypto", "jwcrypto", ["consume_jwcrypto.py", "control_jwcrypto.py"]),
]

# 대조군의 줄마다 기대. 주석이 없는 줄과 "오류 없음" 줄에는 오류가 없어야 한다.
EXPECT = re.compile(r"#\s*기대:\s*(?P<rules>report\w+(?:\s*,\s*report\w+)*)")


def expected_errors(name: str) -> set[tuple[str, int, str]]:
    lines = (HERE / name).read_text(encoding="utf-8").splitlines()
    found = ((number, EXPECT.search(text)) for number, text in enumerate(lines, start=1))
    return {
        (name, number, rule.strip())
        for number, match in found
        if match is not None
        for rule in match["rules"].split(",")
    }


def interpreter(env: Path) -> Path:
    windows = env / "Scripts" / "python.exe"
    return windows if windows.exists() else env / "bin" / "python"


def installed_version(env_root: Path, env: str | None, dist: str) -> str:
    code = f"import importlib.metadata as m; print(m.version({dist!r}))"
    if env is None:
        command = ["uv", "run", "python", "-c", code]
    else:
        command = [str(interpreter(env_root / env / ".venv")), "-c", code]
    done = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, check=True)
    return done.stdout.strip()


def type_escapes(source: str) -> list[str]:
    spec = importlib.util.spec_from_file_location(
        "check_type_escapes", ROOT / "tools" / "check_type_escapes.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.escapes_in(source)


def pyright(env_root: Path, env: str | None, files: list[str]) -> dict[str, object]:
    copies = [TESTS / f"{PREFIX}{name}" for name in files]
    try:
        for name, copy in zip(files, copies, strict=True):
            shutil.copyfile(HERE / name, copy)
        command = ["uv", "run", "pyright", "--outputjson"]
        if env is not None:
            command += ["--venvpath", str(env_root / env)]
        command += [str(copy.relative_to(ROOT)) for copy in copies]
        done = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
    finally:
        for copy in copies:
            copy.unlink(missing_ok=True)
    return json.loads(done.stdout)


def main() -> int:
    if len(sys.argv) != 2:
        print("인자: <환경 루트>", file=sys.stderr)
        return 2
    env_root = Path(sys.argv[1]).resolve()
    version = subprocess.run(
        ["uv", "run", "pyright", "--version"], cwd=ROOT, capture_output=True, text=True, check=True
    )
    print(f"pyright: {version.stdout.strip()}")
    for label, env, dist, files in TARGETS:
        print(f"\n== {label}: {dist} {installed_version(env_root, env, dist)}")
        report = pyright(env_root, env, files)
        summary = report["summary"]
        assert isinstance(summary, dict)
        print(
            f"filesAnalyzed={summary['filesAnalyzed']} errorCount={summary['errorCount']}"
            f" warningCount={summary['warningCount']}"
        )
        diagnostics = report["generalDiagnostics"]
        assert isinstance(diagnostics, list)
        actual: set[tuple[str, int, str]] = set()
        for diagnostic in diagnostics:
            assert isinstance(diagnostic, dict)
            file = Path(str(diagnostic["file"])).name.removeprefix(PREFIX)
            line = diagnostic["range"]["start"]["line"] + 1
            rule = diagnostic.get("rule", "-")
            message = str(diagnostic["message"]).replace("\n", " / ")
            print(f"  {diagnostic['severity']} {file}:{line} [{rule}] {message}")
            if diagnostic["severity"] == "error":
                actual.add((file, line, rule))
        expected = set().union(*(expected_errors(name) for name in files))
        if actual == expected and summary["filesAnalyzed"] == len(files):
            print(f"  기대와 같다: 오류 {len(expected)}개, 분석한 파일 {len(files)}개")
        else:
            print(f"  기대와 다르다: 기대 {sorted(expected)} 실제 {sorted(actual)}")
        for name in files:
            found = type_escapes((HERE / name).read_text(encoding="utf-8"))
            print(f"  타입 우회 {name}: {found if found else '없음'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
