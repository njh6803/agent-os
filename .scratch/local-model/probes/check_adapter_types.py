"""후보 어댑터(`adapter_candidate.py`)가 저장소의 pyright strict 설정을 타입 우회 없이 지나는지.

pyright 는 점 디렉터리(`.scratch`)의 파일을 분석하지 않고 "0 errors"로 넘긴다(operations.md 환경
규약 상세). 그래서 후보와 대조군(`adapter_types_control.py`)을 `<환경 루트>/typecheck/`에 복사해 그
사본을 넘긴다. 저장소의 `tests/`에는 쓰지 않는다. 실행 위치는 저장소 루트, 명령은 `uv run
pyright`(저장소 락의 판)이고, langchain-openai 가 깔린 환경은 `--venvpath <환경 루트>`로 넘긴다
(`[tool.pyright]`의 `venv`가 `.venv`라 `<환경 루트>/.venv`를 읽는다). 환경은 `make_env.py`가 만든다.

표지:
- `config_strict`: `pyproject.toml`의 `[tool.pyright].typeCheckingMode`가 `strict`다.
- `pyright_analyzed`: `summary.filesAnalyzed`가 넘긴 파일 수와 같다.
- `control_caught`: 대조군의 `# 기대: <규칙>` 줄마다 그 규칙의 오류가 났고, 표시가 없는 줄에는
  오류가 없다. strict 에서만 나는 규칙(`reportMissingParameterType`)이 strict 로 봤다는 표지이고,
  langchain-openai 의 형식에 기대는 줄(`ChatOpenAI`에 대입, 생성자 인자)이 그 패키지의 형식을
  읽었다는 표지다.
- `candidate_clean`: 앞의 둘이 섰을 때만 후보의 진단 수를 측정으로 센다.
- `no_type_escapes`: `tools/check_type_escapes.py`의 `escapes_in`이 우회를 넣은 글에서 그것을 찾을
  때만 후보의 우회 수를 측정으로 센다.

표지가 하나라도 없거나, 후보에 진단이나 우회가 있으면 1 로 끝난다.

    uv run python .scratch/local-model/probes/check_adapter_types.py <환경 루트>
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from tools.check_type_escapes import escapes_in  # noqa: E402
from tools.probe_kit import Rounds  # noqa: E402

CANDIDATE = "adapter_candidate.py"
CONTROL = "adapter_types_control.py"
CALL_TIMEOUT = 600.0
EXPECT = re.compile(r"#\s*기대:\s*(?P<rules>report\w+(?:\s*,\s*report\w+)*)")
ESCAPING = "from typing import Any, cast\n\nvalue: Any = cast(int, 'x')  # type: ignore[arg-type]\n"


def expected(path: Path) -> set[tuple[int, str]]:
    """대조군에서 줄마다 기대하는 규칙. (줄 번호, 규칙)의 집합이다."""
    lines = path.read_text(encoding="utf-8").splitlines()
    found = ((number, EXPECT.search(text)) for number, text in enumerate(lines, start=1))
    return {
        (number, rule.strip())
        for number, match in found
        if match is not None
        for rule in match["rules"].split(",")
    }


def run_pyright(env_root: Path, copies: list[Path]) -> dict[str, object]:
    command = ["uv", "run", "pyright", "--outputjson", "--venvpath", str(env_root)]
    done = subprocess.run(
        [*command, *(str(copy) for copy in copies)],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=CALL_TIMEOUT,
    )
    report = json.loads(done.stdout)
    if not isinstance(report, dict):
        raise TypeError("pyright 의 출력이 JSON 객체가 아니다")
    return report


def diagnostics(report: dict[str, object], name: str) -> list[tuple[int, str, str, str]]:
    """그 파일의 진단. (줄 번호, 심각도, 규칙, 글)이다."""
    found: list[tuple[int, str, str, str]] = []
    listed = report.get("generalDiagnostics")
    for item in listed if isinstance(listed, list) else []:
        if not isinstance(item, dict) or Path(str(item.get("file"))).name != name:
            continue
        line = item["range"]["start"]["line"] + 1
        text = str(item.get("message", "")).replace("\n", " / ")
        found.append((line, str(item.get("severity")), str(item.get("rule", "-")), text))
    return found


def emit(case: str, **data: object) -> None:
    print(json.dumps({"case": case, **data}, ensure_ascii=False, default=repr), flush=True)


def main() -> int:
    if len(sys.argv) != 2:
        print("인자: <환경 루트>", file=sys.stderr)
        return 2
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    env_root = Path(sys.argv[1]).resolve()
    target = env_root / "typecheck"
    target.mkdir(parents=True, exist_ok=True)
    copies = [target / name for name in (CANDIDATE, CONTROL)]
    for copy in copies:
        shutil.copyfile(HERE / copy.name, copy)
    rounds = Rounds()
    report: dict[str, object] = {}
    analyzed = caught = False
    found: list[tuple[int, str, str, str]] = []
    escapes: list[str] = []

    with rounds.round("config_strict") as current:
        settings = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        mode = settings["tool"]["pyright"]["typeCheckingMode"]
        emit("config_strict", typeCheckingMode=mode, include=settings["tool"]["pyright"]["include"])
        current.mark(measured=mode == "strict", result=f"typeCheckingMode={mode}")

    with rounds.round("pyright_analyzed") as current:
        report = run_pyright(env_root, copies)
        summary = report["summary"]
        analyzed = isinstance(summary, dict) and summary.get("filesAnalyzed") == len(copies)
        emit("pyright_analyzed", version=report.get("version"), summary=summary)
        current.mark(
            measured=analyzed, result=f"pyright {report.get('version')} 파일 {len(copies)}"
        )

    with rounds.round("control_caught") as current:
        wanted = expected(HERE / CONTROL)
        errors = {(line, rule) for line, severity, rule, _ in diagnostics(report, CONTROL)}
        missing = sorted(wanted - errors)
        stray = sorted(error for error in errors if error[0] not in {line for line, _ in wanted})
        caught = analyzed and bool(wanted) and not missing and not stray
        emit("control_caught", expected=sorted(wanted), missing=missing, stray=stray)
        current.mark(measured=caught, result=f"기대한 오류 {len(wanted)}개가 모두 났다")

    with rounds.round("candidate_clean") as current:
        found = diagnostics(report, CANDIDATE)
        emit("candidate_clean", diagnostics=found)
        current.mark(measured=analyzed and caught, result=f"후보의 진단 {len(found)}개")

    with rounds.round("no_type_escapes") as current:
        judged = escapes_in(ESCAPING)
        escapes = escapes_in((HERE / CANDIDATE).read_text(encoding="utf-8"))
        emit("no_type_escapes", judge_finds_planted=judged, candidate=escapes)
        current.mark(measured=len(judged) >= 3, result=f"후보의 타입 우회 {len(escapes)}개")

    print(rounds.summary())
    return 1 if found or escapes else rounds.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
