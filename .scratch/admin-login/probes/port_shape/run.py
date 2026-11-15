"""포트를 선언한 모듈을 가져오지 않는 어댑터가 pyright strict 에서 그 포트를 만족하는지 본다.

왜. 어댑터 층(`agent_os.adapters`)은 `agent_os.http` 를 import 하지 못한다(원칙 IV, ADR 0016,
`pyproject.toml` 의 금지 계약). ADR 0062 는 계정 포트를 `agent_os.http` 가 선언하고 PostgreSQL
구현을 어댑터 층이 든다고 정한다. 그 둘이 함께 서려면 어댑터가 포트와 그 포트가 주고받는 값의 타입을
가져오지 않고도 타입 검사가 두 쪽을 맞대야 한다. 이 프로브는 그 모양 하나를 두 모듈로 흉내 내
잰다(`http_side.py`, `adapter_side.py`, 조립은 `assemble.py`).

보는 것.
  range     pyright 가 이 폴더의 파이썬 파일을 모두 strict 로 분석했는가. 표지는 `filesAnalyzed` 가
            파일 수와 같고 `control_checks.py` 에서 `reportMissingParameterType` 이 나는 것이다.
            이 표지가 없으면 아래 pyright 회차는 모두 측정이 아니다.
  subject   `http_side.py`, `adapter_side.py`, `assemble.py` 의 오류 수.
  drift     어긋난 어댑터를 포트 자리에 넘긴 두 파일에서 `reportArgumentType` 이 나는가. 줄에 칸이
            없는 것과 인자의 타입이 다른 것이다. 이 규칙이 없는 회차는 측정이 아니다(가져오기가
            풀리지 않으면 이 규칙 대신 `reportUnknownArgumentType` 이 난다).
  imports   `adapter_side.py` 와 `adapter_drift.py` 가 `http_side` 를 가져오지 않는가. AST 로 본다.
            AST 가 가져오기를 본다는 표지는 `assemble.py` 에서 `http_side` 가 잡히는 것이다.
  escapes   재는 세 파일에 타입 우회가 없는가(`tools/check_type_escapes.py` 의 `escapes_in`).
            그 검사가 듣는다는 표지는 `control_checks.py` 에서 셋이 잡히는 것이다.
  run       `assemble.py` 를 실제로 띄워 포트를 쓰는 쪽이 어댑터를 지나는가. 표지는 `RESULT` 줄의
            값이다.

돌리기(저장소 루트에서). 네트워크와 Docker 를 쓰지 않고 수 초다.
  uv run python .scratch/admin-login/probes/port_shape/run.py

못 보는 것.
- 실제 `agent_os` 패키지와 import-linter. 두 모듈은 흉내이고, 금지 계약이 이 모양을 받는지는
  어댑터가 `http` 를 가져오지 않는다는 AST 확인으로만 본다.
- PostgreSQL 과 드라이버의 타입. 어댑터는 사전에 담는다.
- 포트의 다른 모양. 줄을 읽기 전용 Protocol 로, 받는 값을 Protocol 로 둔 모양 하나만 잰다. 비동기
  메서드, 제네릭, 변경 가능한 줄, 예외의 타입은 재지 않는다.
- pyright 의 다른 판과 다른 타입 검사기.
"""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))

from tools.check_type_escapes import escapes_in  # noqa: E402
from tools.probe_kit import Rounds  # noqa: E402

CONTROL = "control_checks.py"
SUBJECTS = ("http_side.py", "adapter_side.py", "assemble.py")
DRIFTS = ("assemble_drift_row.py", "assemble_drift_arg.py")
ADAPTERS = ("adapter_side.py", "adapter_drift.py")
DRIFT_RULE = "reportArgumentType"
STRICT_RULE = "reportMissingParameterType"
PORT_MODULE = "http_side"
EXPECTED_RESULT = {"tier": "admin", "failures": 1}

type Json = dict[str, Json] | list[Json] | str | int | float | bool | None


def parse(text: str) -> Json:
    try:
        parsed: Json = json.loads(text)
    except ValueError:
        return None
    return parsed


def dig(value: Json, *keys: str) -> Json:
    for key in keys:
        value = value.get(key) if isinstance(value, dict) else None
    return value


def probe_files() -> list[str]:
    paths = [path for path in HERE.rglob("*.py") if "__pycache__" not in path.parts]
    return sorted(path.relative_to(HERE).as_posix() for path in paths)


def typecheck() -> Json:
    done = subprocess.run(
        [sys.executable, "-m", "pyright", "--outputjson", "-p", str(HERE)],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
        check=False,
    )
    return parse(done.stdout)


def errors_by_file(report: Json) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    diagnostics = dig(report, "generalDiagnostics")
    for item in diagnostics if isinstance(diagnostics, list) else []:
        if dig(item, "severity") != "error":
            continue
        file, rule = dig(item, "file"), dig(item, "rule")
        name = Path(file).name if isinstance(file, str) else "(파일 없음)"
        found.setdefault(name, []).append(rule if isinstance(rule, str) else "(규칙 없음)")
    return found


def imported_modules(name: str) -> set[str]:
    tree = ast.parse((HERE / name).read_text(encoding="utf-8"))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            modules.add(node.module.split(".")[0])
    return modules


def run_assemble() -> Json:
    done = subprocess.run(
        [sys.executable, str(HERE / "assemble.py")],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
        check=False,
    )
    lines = [line for line in done.stdout.splitlines() if line.startswith("RESULT ")]
    return parse(lines[-1].removeprefix("RESULT ")) if lines else None


def main() -> int:
    rounds = Rounds()
    files = probe_files()
    report = typecheck()
    errors = errors_by_file(report)
    analyzed = dig(report, "summary", "filesAnalyzed")
    seen = analyzed == len(files) and STRICT_RULE in errors.get(CONTROL, [])
    print(f"pyright {dig(report, 'version')}, filesAnalyzed {analyzed}/{len(files)}")
    with rounds.round("range pyright 분석 범위") as current:
        current.mark(measured=seen, result="분석했다" if seen else "분석 범위의 표지가 없다")
    for name in SUBJECTS:
        rules = errors.get(name, [])
        print(f"{name}: 오류 {len(rules)} {sorted(set(rules))}")
        with rounds.round(f"subject {name}") as current:
            current.mark(measured=seen, result=f"오류 {len(rules)}")
    for name in DRIFTS:
        rules = errors.get(name, [])
        print(f"{name}: 오류 {len(rules)} {sorted(set(rules))}")
        with rounds.round(f"drift {name}") as current:
            caught = seen and DRIFT_RULE in rules
            current.mark(measured=caught, result="조립하는 자리에서 잡혔다" if caught else "")
    ast_sees = PORT_MODULE in imported_modules("assemble.py")
    for name in ADAPTERS:
        modules = imported_modules(name)
        print(f"{name}: 가져오는 모듈 {sorted(modules)}")
        with rounds.round(f"imports {name}") as current:
            result = "포트 모듈을 가져온다" if PORT_MODULE in modules else "가져오지 않는다"
            current.mark(measured=ast_sees, result=result)
    control = escapes_in((HERE / CONTROL).read_text(encoding="utf-8"))
    listening = all(any(word in line for line in control) for word in ("`Any`", "`cast`", "억제"))
    for name in SUBJECTS:
        found = escapes_in((HERE / name).read_text(encoding="utf-8"))
        print(f"{name}: 타입 우회 {found}")
        with rounds.round(f"escapes {name}") as current:
            current.mark(measured=listening, result=f"우회 {len(found)}")
    result = run_assemble()
    print(f"assemble.py 실행: {result}")
    with rounds.round("run assemble.py") as current:
        passed = result == EXPECTED_RESULT
        current.mark(measured=passed, result="포트를 쓰는 쪽이 어댑터를 지났다" if passed else "")
    print(rounds.summary())
    return rounds.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
