"""tools/open_session.ps1 회귀 시험의 이음매(ADR 0030)를 받치는 수.

지금의 이음매는 `tests/tools/test_open_session.py` 의 `_call` 이다. pytest 가 사례마다 pwsh 를
띄우고, 스크립트의 AST 에서 이름으로 고른 함수만 정의한 뒤 본문을 돌린다. 이 프로브는 그 이음매가
치르는 값과 Pester 없이 할 수 있는 것을 잰다. per_call·batched·shadow 갈래는 그 `_call` 을 그대로
부르고, startup·runspace 갈래는 `_call` 이 늘 앞에 붙이는 AST 추출을 빼야 해서 pwsh 를 직접 띄운다.
시험 모듈의 비공개 이름(`_call`, `_MODEL_LINE`, `_MODEL_LINES`, `DIRECTIVE`, `NOISE`,
`MAIN_STARTED`)에 기대므로 그 이름이 바뀌면 이 프로브는 AttributeError 로 멈춘다.

갈래:
- env: pwsh 판과 pwsh 가 보는 Pester 모듈(판과 자리).
- startup: 글자 `up` 만 내는 명령으로 pwsh 를 띄우는 데 드는 초. 그 글자가 나온 회차만 센다.
- per_call: 지금의 이음매로 `Read-ModelLine` 사례 하나를 부르는 데 드는 초. 사례마다 pwsh 하나다.
- batched: 같은 사례 여럿을 pwsh 하나에서 차례로 부른다(`_MODEL_LINES`, 결정표 대조 테스트의 본문).
- runspace: 같은 사례 여럿을 pwsh 하나에서 사례마다 새 runspace 로 부른다. 앞 사례가 전역에 둔 값이
  다음 사례에 보이면 `leaked` 를 낸다. 대조군은 같은 글을 바깥과 같은 runspace 에서 부르고, 둘째
  사례부터 모두 `leaked` 를 내야 한다(누수를 알아보는 장치가 도는지의 양성 대조). 앞 사례가 바꾼
  환경 변수가 보이면 `env-leaked` 를 따로 낸다. 환경 변수는 프로세스에 하나라 새 runspace 에서도
  둘째 사례부터 모두 보여야 한다(PR 직전 버그·성능 리뷰가 손으로 본 것을 이 갈래가 다시 낸다).
- shadow: 시험 본문이 `Get-CimInstance` 와 같은 이름의 함수를 정의하면, AST 에서 떼어 낸
  `Get-AppQuitMarker` 가 그 함수를 부르는지. 가짜가 주 프로세스를 줄 때만 표지 줄이 나와야 하고,
  렌더러만 줄 때와 아무것도 주지 않을 때는 없어야 한다. 세 갈래는 가짜가 주는 프로세스만 다르므로
  진짜 cmdlet 이 불리면 세 결과가 같다. 결과가 갈리는 것이 가짜가 불렸다는 표지다. 가짜는 받은
  `-Filter` 값을 전역에 적고 본문이 그것을 내어, 부른 쪽이 넘긴 인자를 pytest 가 단언할 수 있는지도
  본다. 로그 폴더는 `APPDATA`·`LOCALAPPDATA` 를 임시 폴더로 돌려 준다.

모든 사례는 출력이 기대한 글자와 같은지까지 본다. 같지 않은 갈래는 측정으로 세지 않고 종료 코드를
1로 둔다. 시간은 그 회차의 벽시계 초다. 사례의 수(36)는 이 프로브를 지을 때(`185fe61`) 테스트 파일의
사례 수에 맞췄지만 모두 `Read-ModelLine` 의 정상 사례라, 실패를 단언하는 사례(종료 코드·stderr)를
묶는 값은 재지 않는다.

돌리는 법: 저장소 루트에서 `PYTHONUTF8=1 uv run python .scratch/harness/probes/pwsh_test_seam.py`.
pwsh(PowerShell 7)가 PATH 에 있어야 하고, shadow 갈래가 Windows 경로를 쓰므로 Windows 에서 돈다.
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[3]
TEST_FILE = ROOT / "tests" / "tools" / "test_open_session.py"
SCRIPT = ROOT / "tools" / "open_session.ps1"

EFFORTS = [("low", 0), ("medium", 1), ("high", 2), ("xhigh", 3), ("max", 4)]
CASES = 36
PER_CALL_RUNS = 10
STARTUP_RUNS = 5


class NotMeasured(Exception):
    """출력이 기대한 글자와 달라 그 갈래가 측정이 아니다."""


def _load_seam() -> ModuleType:
    # 시험 모듈이 `tools` 를 import 한다. pytest 는 `pythonpath` 설정으로 루트를 넣는다.
    sys.path.insert(0, str(ROOT))
    spec = importlib.util.spec_from_file_location("open_session_seam", TEST_FILE)
    if spec is None or spec.loader is None:
        raise SystemExit(f"{TEST_FILE} 를 불러오지 못했다")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _pwsh(command: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["pwsh", "-NoProfile", "-NonInteractive", "-Command", command],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env={**os.environ, **(env or {})},
        check=False,
    )


def _cases(directive: str) -> tuple[list[str], list[str]]:
    prompts: list[str] = []
    expected: list[str] = []
    for i in range(CASES):
        effort, step = EFFORTS[i % len(EFFORTS)]
        prompts.append(directive.format(model=f"모델: Opus 5.5 / {effort}"))
        expected.append(f"Opus 5.5|{effort}|{step}")
    return prompts, expected


def _summary(name: str, seconds: list[float]) -> str:
    return (
        f"{name} n={len(seconds)} median={statistics.median(seconds):.2f}s "
        f"min={min(seconds):.2f}s max={max(seconds):.2f}s"
    )


def env_branch() -> list[str]:
    done = _pwsh(
        "$PSVersionTable.PSVersion.ToString(); "
        "Get-Module -ListAvailable Pester | "
        'ForEach-Object { "Pester $($_.Version) $($_.ModuleBase)" }'
    )
    if done.returncode != 0:
        raise NotMeasured(f"env 실패: {done.stderr.strip()}")
    lines = done.stdout.strip().splitlines()
    pesters = [f"env {line}" for line in lines[1:]] or ["env Pester 없음"]
    return [f"env pwsh={lines[0]}", *pesters]


def startup_branch() -> list[str]:
    seconds: list[float] = []
    for _ in range(STARTUP_RUNS):
        started = time.perf_counter()
        done = _pwsh("'up'")
        elapsed = time.perf_counter() - started
        if done.returncode != 0 or done.stdout.strip() != "up":
            raise NotMeasured(f"startup: {done.stdout.strip()!r} {done.stderr.strip()}")
        seconds.append(elapsed)
    return [_summary("startup", seconds)]


def per_call_branch(seam: ModuleType, prompts: list[str], expected: list[str]) -> list[str]:
    seconds: list[float] = []
    for prompt, want in list(zip(prompts, expected, strict=True))[:PER_CALL_RUNS]:
        started = time.perf_counter()
        done = seam._call("Get-EffortSteps,Read-ModelLine", seam._MODEL_LINE, {"prompt": prompt})
        elapsed = time.perf_counter() - started
        if done.returncode != 0 or done.stdout.strip() != want:
            raise NotMeasured(f"per_call: {done.stdout.strip()!r} {done.stderr.strip()}")
        seconds.append(elapsed)
    return [_summary("per_call", seconds)]


def batched_branch(seam: ModuleType, prompts: list[str], expected: list[str]) -> list[str]:
    started = time.perf_counter()
    done = seam._call("Get-EffortSteps,Read-ModelLine", seam._MODEL_LINES, {"prompts": prompts})
    elapsed = time.perf_counter() - started
    if done.returncode != 0 or done.stdout.strip().splitlines() != expected:
        raise NotMeasured(f"batched: {done.stdout.strip()!r} {done.stderr.strip()}")
    return [f"batched n={len(prompts)} total={elapsed:.2f}s per_case={elapsed / len(prompts):.2f}s"]


# 함수 정의는 바깥 pwsh 가 AST 에서 한 번 떼고, 사례마다 runspace 에 그 글을 다시 정의한다.
# `SEAM_MODE=current` 면 사례를 바깥과 같은 runspace 에서 불러 누수가 보이는 대조군이 된다.
_RUNSPACE = """
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$language = 'System.Management.Automation.Language'
$ast = ("$language.Parser" -as [type])::ParseFile($env:SEAM_SCRIPT, [ref]$null, [ref]$null)
$definition = "$language.FunctionDefinitionAst" -as [type]
$texts = foreach ($name in 'Get-EffortSteps', 'Read-ModelLine') {
    $isTarget = { param($node) $node -is $definition -and $node.Name -eq $name }.GetNewClosure()
    $ast.Find($isTarget, $true).Extent.Text
}
$case = @'
$leak = Get-Variable -Scope Global -Name seamLeak -ErrorAction SilentlyContinue
if ($null -ne $leak) { 'leaked' }
if ($env:SEAM_ENV_LEAK) { 'env-leaked' }
$global:seamLeak = 1
$env:SEAM_ENV_LEAK = '1'
$found = Read-ModelLine $args[0]
"$($found.Model)|$($found.Effort)|$($found.Step)"
'@
$source = ($texts -join "`n") + "`n" + $case
$modes = [System.Management.Automation.RunspaceMode]
$mode = if ($env:SEAM_MODE -eq 'current') { $modes::CurrentRunspace } else { $modes::NewRunspace }
foreach ($prompt in ($env:SEAM_ARGS | ConvertFrom-Json).prompts) {
    $ps = [powershell]::Create($mode)
    try {
        $ps.AddScript($source).AddArgument($prompt).Invoke()
        if ($ps.Streams.Error.Count -gt 0) { throw $ps.Streams.Error[0] }
    } finally { $ps.Dispose() }
}
"""


def _runspace(prompts: list[str], mode: str) -> tuple[float, subprocess.CompletedProcess[str]]:
    started = time.perf_counter()
    done = _pwsh(
        _RUNSPACE,
        {
            "SEAM_SCRIPT": str(SCRIPT),
            "SEAM_ARGS": json.dumps({"prompts": prompts}),
            "SEAM_MODE": mode,
        },
    )
    return time.perf_counter() - started, done


_MARKS = ("leaked", "env-leaked")


def _split_marks(done: subprocess.CompletedProcess[str]) -> tuple[list[str], int, int]:
    """사례의 결과 줄, 전역 누수 수, 환경 변수 누수 수."""
    lines = done.stdout.strip().splitlines()
    results = [line for line in lines if line not in _MARKS]
    return results, lines.count("leaked"), lines.count("env-leaked")


def runspace_branch(prompts: list[str], expected: list[str]) -> list[str]:
    # 둘째 사례부터 모두 보여야 하는 누수의 수다.
    every = len(prompts) - 1
    elapsed, done = _runspace(prompts, "new")
    results, leaked, env_leaked = _split_marks(done)
    if done.returncode != 0 or results != expected or leaked != 0 or env_leaked != every:
        raise NotMeasured(
            f"runspace(leaked={leaked}, env_leaked={env_leaked}): {results[:3]!r} "
            f"{done.stderr.strip()}"
        )
    _, control = _runspace(prompts, "current")
    control_results, control_leaked, _ = _split_marks(control)
    if control.returncode != 0 or control_results != expected or control_leaked != every:
        raise NotMeasured(
            f"runspace 대조군(leaked={control_leaked}): {control_results[:3]!r} "
            f"{control.stderr.strip()}"
        )
    return [
        f"runspace n={len(prompts)} total={elapsed:.2f}s per_case={elapsed / len(prompts):.2f}s "
        f"leaked=0 env_leaked={env_leaked} control_leaked={control_leaked}"
    ]


_SHADOW = """
function Get-CimInstance {
    [CmdletBinding()] param($ClassName, $Filter)
    $global:cimFilter = $Filter
    $culture = [cultureinfo]::InvariantCulture
    foreach ($p in $given.processes) {
        [pscustomobject]@{
            ExecutablePath = $p.path
            CommandLine = $p.command
            CreationDate = [datetime]::ParseExact($p.created, 'yyyy-MM-dd HH:mm:ss', $culture)
        }
    }
}
$env:LOCALAPPDATA = $given.local
$env:APPDATA = $given.roaming
$found = Get-AppQuitMarker
if ($null -eq $found) { '(없음)' } else { $found }
"filter=$global:cimFilter"
"""

# `Get-AppQuitMarker` 와 그것이 부르는 순수 함수. 그 함수의 선택을 떼어 낸 뒤(대기열 17) 목록이
# 늘었다.
_SHADOW_FUNCTIONS = "Find-QuitMarker,Find-MainStart,Select-QuitLogs,Get-AppQuitMarker"
_APP = r"C:\Program Files\WindowsApps\Claude_1.0.0.0_x64__test\app\Claude.exe"
_MARKER = "beforeQuitForUpdate handler fired, going down for update"
_FILTER = "filter=Name = 'Claude.exe'"


def shadow_branch(seam: ModuleType) -> list[str]:
    with tempfile.TemporaryDirectory() as tmp:
        roaming = Path(tmp) / "roaming"
        local = Path(tmp) / "local"
        logs = roaming / "Claude" / "logs"
        logs.mkdir(parents=True)
        local.mkdir()
        lines = [*seam.NOISE, f"2026-09-29 12:19:28 [info] {_MARKER}"]
        (logs / "main.log").write_text("\n".join(lines) + "\n", encoding="utf-8")
        main = {"path": _APP, "command": f'"{_APP}"', "created": seam.MAIN_STARTED}
        renderer = {**main, "command": f'"{_APP}" --type=renderer'}
        branches = {
            "main": ([main], [f"2026-09-29 12:19:28 {_MARKER}", _FILTER]),
            "renderer": ([renderer], ["(없음)", _FILTER]),
            "none": ([], ["(없음)", _FILTER]),
        }
        for name, (processes, want) in branches.items():
            given = {"processes": processes, "local": str(local), "roaming": str(roaming)}
            done = seam._call(_SHADOW_FUNCTIONS, _SHADOW, given)
            got = done.stdout.strip().splitlines()
            if done.returncode != 0 or got != want:
                raise NotMeasured(f"shadow {name}: {got!r} {done.stderr.strip()}")
        return ["shadow main=ok renderer=ok none=ok filter=ok"]


def main() -> int:
    if shutil.which("pwsh") is None:
        print("pwsh 가 PATH 에 없다. 이 프로브는 PowerShell 7 로 잰다", file=sys.stderr)
        return 1
    seam = _load_seam()
    prompts, expected = _cases(seam.DIRECTIVE)
    branches: list[Callable[[], list[str]]] = [
        env_branch,
        startup_branch,
        lambda: per_call_branch(seam, prompts, expected),
        lambda: batched_branch(seam, prompts, expected),
        lambda: runspace_branch(prompts, expected),
        lambda: shadow_branch(seam),
    ]
    misses: list[str] = []
    for branch in branches:
        try:
            lines = branch()
        except NotMeasured as miss:
            misses.append(str(miss))
            continue
        for line in lines:
            print(line)
    for miss in misses:
        print(f"측정 아님: {miss}", file=sys.stderr)
    print("결과: 기대대로" if not misses else f"결과: 측정 아닌 갈래 {len(misses)}")
    return 1 if misses else 0


if __name__ == "__main__":
    raise SystemExit(main())
