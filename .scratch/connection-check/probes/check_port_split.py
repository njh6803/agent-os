"""접속 확인의 두 길을 타입으로 가르는 모양(`port_split_shape.py`)이 pyright strict에서 서는지.

ADR 0067 결정 "포트와 층"이 재지 않은 구상으로 남긴 것을 잰다. 화면이 스스로 하는 확인의 길이 원격
MCP 서버와 모델만 받게 하면, stdio MCP 서버를 그 길에 넘기는 코드가 타입 검사에 걸리는가. 그리고
관리 쪽에 포트 전체가 아니라 접속 확인 메서드만 넘기는 모양이 타입 우회 없이 서는가.

pyright는 점 디렉터리(`.scratch`) 아래의 파일을 분석하지 않고 "0 errors"로 넘긴다(operations.md 환경
규약 상세). 그래서 사본 둘을 저장소 밖 임시 폴더에 쓰고, 저장소 루트에서 `uv run pyright`에 그
경로를 넘긴다. 사본은 후보(모양 파일 그대로)와 대조군(모양 파일 뒤에 `CONTROL_TAIL`을 붙인 것)이다.
대조군을 파일로 따로 두지 않고 붙여 만드는 까닭은, 걸려야 하는 줄이 후보와 글자 그대로 같은 정의를
쓰게 하려는 것이다.

표지:
- `config_strict`: `pyproject.toml`의 `[tool.pyright].typeCheckingMode`가 `strict`다.
- `pyright_analyzed`: `summary.filesAnalyzed`가 넘긴 파일 수(2)와 같다.
- `control_caught`: 대조군의 `# 기대: <규칙>` 줄마다 그 규칙의 오류가 났고, 기대한 (줄, 규칙) 쌍이
  아닌 오류는 하나도 없다. strict에서만 나는 규칙(`reportMissingParameterType`)이 strict로 봤다는
  표지이고, `StdioServer`와 `HttpServer`를 가르는 줄이 `agent_os`의 실제 타입을 읽었다는 표지다
  (가져오기가 풀리지 않으면 그 줄들은 걸리지 않고 `reportMissingImports`가 기대 밖의 오류로 남는다).
- `candidate_clean`: 앞의 둘이 섰을 때만 후보의 진단 수를 측정으로 센다.
- `no_type_escapes`: `tools/check_type_escapes.py`의 `escapes_in`이 우회를 심은 글에서 그것을 찾을
  때만 후보와 대조군 꼬리의 우회 수를 측정으로 센다.

표지가 하나라도 없거나 후보에 진단이나 우회가 있으면 1로 끝난다.

    uv run python .scratch/connection-check/probes/check_port_split.py
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from tools.check_type_escapes import escapes_in  # noqa: E402
from tools.probe_kit import Rounds  # noqa: E402

SHAPE = "port_split_shape.py"
CANDIDATE = "port_split_candidate.py"
CONTROL = "port_split_control.py"
CALL_TIMEOUT = 600.0
EXPECT = re.compile(r"#\s*기대:\s*(?P<rules>report\w+(?:\s*,\s*report\w+)*)")
ESCAPING = "from typing import Any, cast\n\nvalue: Any = cast(int, 'x')  # type: ignore[arg-type]\n"

# 걸려야 하는 줄. 모양 파일의 글 뒤에 붙어 대조군이 된다. 줄마다 `# 기대: <규칙>`으로 표시한다.
CONTROL_TAIL = '''

def stdio_into_remote(remote: RemoteCheck, name: PluginName, server: StdioServer) -> object:
    """스스로 하는 확인의 길에 stdio 서버를 넘긴다."""
    return remote(name, server)  # 기대: reportArgumentType


def unnarrowed_into_remote(remote: RemoteCheck, manifest: PluginManifest) -> object:
    """전송을 가르지 않은 서버 칸을 그대로 넘긴다."""
    return remote(manifest.name, manifest.server)  # 기대: reportArgumentType


def stdio_check_as_remote(tools: ToolSource) -> RemoteCheck:
    """프로세스를 띄우는 확인을 스스로 하는 확인의 자리에 돌려준다."""
    return tools.check_stdio  # 기대: reportReturnType


def automatic_given_stdio(
    plugins: PluginSource, tools: ToolSource, models: ModelSource
) -> AutomaticChecks:
    """조립 층이 스스로 하는 확인의 길에 프로세스를 띄우는 확인을 넘긴다."""
    return AutomaticChecks(
        plugins=plugins,
        remote=tools.check_stdio,  # 기대: reportArgumentType
        model=models.check,
    )


def automatic_reaches_stdio(checks: AutomaticChecks) -> object:
    """스스로 하는 확인의 길이 받지 않은 확인을 꺼내려 한다. 없는 속성이라 타입도 모른다."""
    return (  # 기대: reportUnknownMemberType, reportUnknownVariableType
        checks.stdio  # 기대: reportAttributeAccessIssue
    )


class NoChecks:
    """접속 확인 메서드가 없는 옛 가짜."""

    def connect(
        self, servers: Mapping[PluginName, McpServer]
    ) -> AbstractAsyncContextManager[ToolConnection]:
        raise NotImplementedError


def port_without_checks() -> ToolSource:
    """접속 확인이 없는 가짜를 포트 자리에 넘긴다."""
    return NoChecks()  # 기대: reportReturnType


def untyped(value):  # 기대: reportMissingParameterType, reportUnknownParameterType
    return value  # 기대: reportUnknownVariableType
'''


def expected(text: str) -> set[tuple[int, str]]:
    """글에서 줄마다 기대하는 규칙. (줄 번호, 규칙)의 집합이다."""
    found = ((number, EXPECT.search(line)) for number, line in enumerate(text.splitlines(), 1))
    return {
        (number, rule.strip())
        for number, match in found
        if match is not None
        for rule in match["rules"].split(",")
    }


def run_pyright(copies: list[Path]) -> dict[str, object]:
    done = subprocess.run(
        ["uv", "run", "pyright", "--outputjson", *(str(copy) for copy in copies)],
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
    for stream in (sys.stdout, sys.stderr):
        stream.reconfigure(encoding="utf-8", errors="backslashreplace")
    shape = (HERE / SHAPE).read_text(encoding="utf-8")
    texts = {CANDIDATE: shape, CONTROL: shape + CONTROL_TAIL}
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

    with tempfile.TemporaryDirectory(prefix="connection_check_types_") as folder:
        target = Path(folder).resolve()
        copies = [target / name for name in texts]
        outside = not target.is_relative_to(ROOT) and not any(
            part.startswith(".") for part in target.parts
        )
        for copy in copies:
            copy.write_text(texts[copy.name], encoding="utf-8")

        with rounds.round("pyright_analyzed") as current:
            report = run_pyright(copies)
            summary = report["summary"]
            analyzed = (
                outside
                and isinstance(summary, dict)
                and summary.get("filesAnalyzed") == len(copies)
            )
            emit(
                "pyright_analyzed", version=report.get("version"), summary=summary, outside=outside
            )
            current.mark(
                measured=analyzed, result=f"pyright {report.get('version')} 파일 {len(copies)}"
            )

    with rounds.round("control_caught") as current:
        wanted = expected(texts[CONTROL])
        errors = {(line, rule) for line, _, rule, _ in diagnostics(report, CONTROL)}
        missing = sorted(wanted - errors)
        stray = sorted(errors - wanted)
        caught = analyzed and bool(wanted) and not missing and not stray
        emit(
            "control_caught",
            expected=sorted(wanted),
            missing=missing,
            stray=stray,
            messages=diagnostics(report, CONTROL),
        )
        current.mark(measured=caught, result=f"기대한 오류 {len(wanted)}개가 모두 났다")

    with rounds.round("candidate_clean") as current:
        found = diagnostics(report, CANDIDATE)
        emit("candidate_clean", diagnostics=found)
        current.mark(measured=analyzed and caught, result=f"후보의 진단 {len(found)}개")

    with rounds.round("no_type_escapes") as current:
        judged = escapes_in(ESCAPING)
        escapes = escapes_in(texts[CONTROL])
        emit("no_type_escapes", judge_finds_planted=judged, shape_and_tail=escapes)
        current.mark(measured=len(judged) >= 3, result=f"모양과 꼬리의 타입 우회 {len(escapes)}개")

    print(rounds.summary())
    return 1 if found or escapes else rounds.exit_code()


if __name__ == "__main__":
    raise SystemExit(main())
