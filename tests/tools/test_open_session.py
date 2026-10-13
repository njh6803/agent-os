"""tools/open_session.ps1 의 순수 함수. 파워셸 AST 에서 함수 하나를 떼어 pwsh 로 부른다.

딥링크를 쏘고 앱의 접근성 트리를 누르는 부분, 앱의 주 프로세스와 로그를 찾는 부분은
실제 실행으로 확인한다. 그 안의 판정은 순수 함수로 떼어 여기서 잰다. 판정을 떼기 어려우면
시험 본문이 그 함수가 부르는 명령과 같은 이름의 함수를 정의해 가짜를 준다(ADR 0030).
pwsh 가 없으면 건너뛰지 않고 실패한다(`.claude/rules/tests.md`). CI 의 ubuntu 러너에는 pwsh 가 있다.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest
from tools.hook_prompt_directive import block_reason_for

from tools import model_sweep

SCRIPT = Path(__file__).parents[2] / "tools" / "open_session.ps1"

# 스크립트에서 이름으로 함수 하나만 떼어 정의하고, 뒤에 붙인 본문이 그 함수를 부른다. 이름이 비면
# 아무 함수도 떼지 않고 본문은 `$ast` 만 본다. 스크립트 전체를 돌리면 창을 찾고 딥링크를 쏜다. pwsh
# 는 파이프로 가는 출력을 콘솔 코드 페이지(윈도에서 cp949)로 쓴다. UTF-8 로 고정한다(2026-09-30
# 실측, 고정하지 않으면 한글 에러가 풀리지 않아 stderr 가 사라졌다).
_LOAD = """
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$PSStyle.OutputRendering = 'PlainText'
$language = 'System.Management.Automation.Language'
$ast = ("$language.Parser" -as [type])::ParseFile($env:OPEN_SESSION_SCRIPT, [ref]$null, [ref]$null)
$definition = "$language.FunctionDefinitionAst" -as [type]
foreach ($name in $env:OPEN_SESSION_FUNCTION -split ',' | Where-Object { $_ }) {
    $isTarget = { param($node) $node -is $definition -and $node.Name -eq $name }.GetNewClosure()
    $fn = $ast.Find($isTarget, $true)
    if ($null -eq $fn) { throw "$name 가 스크립트에 없다" }
    . ([scriptblock]::Create($fn.Extent.Text))
}
$given = $env:OPEN_SESSION_ARGS | ConvertFrom-Json
"""

# 시험 본문이 받은 시각 글(`yyyy-MM-dd HH:mm:ss`)을 시각으로 바꾼다. null 이면 null 이다.
_AT = """
$culture = [cultureinfo]::InvariantCulture
$at = {
    param($s)
    if ($null -ne $s) { [datetime]::ParseExact($s, 'yyyy-MM-dd HH:mm:ss', $culture) }
}
"""

_QUIT_MARKER = (
    _AT
    + """
$found = Find-QuitMarker @($given.lines) (& $at $given.since)
if ($null -eq $found) { '(없음)' } else { $found }
"""
)

_MODEL_LINE = """
$found = Read-ModelLine $given.prompt
if ($null -eq $found) { '(없음)' } else { "$($found.Model)|$($found.Effort)|$($found.Step)" }
"""


# pwsh 하나에 주는 시간. 대기 루프(`Wait-For`)를 부르는 사례가 회귀로 끝나지 않아도 pytest 가
# 멈추지 않고 그 사례가 빨개진다(ADR 0030). 사례 하나는 1초 안팎이고, 가장 긴 사례(이 시간 제한을
# 3초로 재는 사례)도 몇 초다.
_TIMEOUT_SEC = 60.0


# 이음매의 값을 재는 프로브 .scratch/harness/probes/pwsh_test_seam.py 가 이 `_call` 과 이 파일의
# `_MODEL_LINE`·`_MODEL_LINES`·`DIRECTIVE`·`NOISE`·`MAIN_STARTED` 를 이름으로 불러 쓴다(ADR 0030).
# 이름을 바꾸면 그 프로브도 함께 고친다.
def _call(
    function: str, body: str, given: dict[str, object], timeout: float = _TIMEOUT_SEC
) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(
            ["pwsh", "-NoProfile", "-NonInteractive", "-Command", _LOAD + body],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env={
                **os.environ,
                "OPEN_SESSION_SCRIPT": str(SCRIPT),
                "OPEN_SESSION_FUNCTION": function,
                "OPEN_SESSION_ARGS": json.dumps(given),
            },
            check=False,
            timeout=timeout,
        )
    except FileNotFoundError:
        pytest.fail("pwsh 가 없다. 이 테스트는 PowerShell 7 로 스크립트의 함수를 부른다")
    except subprocess.TimeoutExpired:
        pytest.fail(
            f"pwsh 가 {timeout:g}초 안에 끝나지 않았다. 대기 루프가 끝나지 않는 회귀일 수 있다"
        )


def test_끝나지_않는_pwsh_는_기다리지_않고_그_사례를_실패로_끝낸다() -> None:
    with pytest.raises(pytest.fail.Exception, match="3초 안에 끝나지 않았다"):
        _call("", "Start-Sleep -Seconds 30", {}, timeout=3)


# 앱의 주 프로세스가 선 시각. 실제 사건(2026-09-29)의 모양이다.
MAIN_STARTED = "2026-09-29 10:28:14"

# 표지 없는 로그. 여러 줄 객체의 속(시각이 없는 줄)도 섞는다.
NOISE = [
    "2026-09-29 10:28:14 [info] Starting app {",
    "  appVersion: '2.9939.2',",
    "}",
    "2026-09-29 11:02:03 [info] [updater] Host busy for 1 h; checking for updates anyway",
    "2026-09-29 12:19:26 [info] [stealth-update] Triggering stealth update after idle timeout",
]


def _find_quit_marker(lines: list[str], since: str = MAIN_STARTED) -> str:
    completed = _call("Find-QuitMarker", _QUIT_MARKER, {"lines": lines, "since": since})
    assert completed.returncode == 0, completed.stderr
    return completed.stdout.strip()


def _read_model_line(prompt: str) -> subprocess.CompletedProcess[str]:
    return _call("Get-EffortSteps,Read-ModelLine", _MODEL_LINE, {"prompt": prompt})


def _model_line_of(prompt: str) -> str:
    completed = _read_model_line(prompt)
    assert completed.returncode == 0, completed.stderr
    return completed.stdout.strip()


def _model_line_error(prompt: str) -> str:
    completed = _read_model_line(prompt)
    assert completed.returncode != 0, f"멈춰야 하는데 읽었다: {completed.stdout.strip()}"
    return completed.stderr


@pytest.mark.parametrize(
    "marker",
    [
        # 자동 업데이트가 끝내기 직전에 부르는 처리기가 JA 를 켰다
        "beforeQuitForUpdate handler fired, going down for update",
        # 업데이트를 위한 끝내기 함수가 JA 를 켠 뒤에 찍는 줄 셋
        "Update check still in flight after 15000ms; quitting without relaunch",
        "Session stop before update took 1591ms",
        "[CCD] CLI exit before update: 2 of 2 exited within 1591ms",
        # 정리를 마쳐 XA 를 켰다
        "Successully ran all onQuitCleanup handlers, marking readyForQuit",
    ],
)
def test_주_프로세스가_선_뒤에_끝내기가_시작됐으면_그_줄을_준다(marker: str) -> None:
    line = f"2026-09-29 12:19:28 [info] {marker}"

    found = _find_quit_marker([*NOISE, line])

    assert found == f"2026-09-29 12:19:28 {marker}"


def test_주_프로세스가_서기_전의_끝내기는_지난_일이라_없다() -> None:
    before = "2026-09-29 03:24:28 [info] beforeQuitForUpdate handler fired, going down for update"

    assert _find_quit_marker([before, *NOISE]) == "(없음)"


def test_끝내기_표지가_없으면_없다() -> None:
    assert _find_quit_marker(NOISE) == "(없음)"


def test_끝내기_처리기가_돌았던_표지만으로는_끝나는_중이_아니다() -> None:
    # 그 처리기가 켜는 깃발(YA)은 정리가 끝나면 실패해도 풀린다. 앱은 멀쩡히 딥링크를 받는다.
    lines = [
        *NOISE,
        "2026-09-29 12:30:00 [info] beforeQuit: handler is not yet run, "
        "preventing quit and cleaning things up",
        "2026-09-29 12:30:02 [error] Failed to run onQuitCleanup handlers: boom",
    ]

    assert _find_quit_marker(lines) == "(없음)"


def test_표지가_여럿이면_가장_이른_것을_준다() -> None:
    lines = [
        *NOISE,
        "2026-09-29 12:19:27 [info] [CCD] CLI exit before update: 2 of 2 exited within 1591ms",
        "2026-09-29 12:19:28 [info] beforeQuitForUpdate handler fired, going down for update",
    ]

    assert _find_quit_marker(lines).startswith("2026-09-29 12:19:27 [CCD] CLI exit before update")


# 끝내기 표지를 찾기 전의 선택 둘. 프로세스와 로그 파일을 찾는 일은 `Get-AppQuitMarker` 가 실제
# 실행으로 하고, 무엇을 고를지는 이 둘이 받은 값만으로 정한다.
_MAIN_START = (
    _AT
    + """
$processes = foreach ($p in $given.processes) {
    $created = & $at $p.created
    [pscustomobject]@{ ExecutablePath = $p.path; CommandLine = $p.command; CreationDate = $created }
}
$started = Find-MainStart @($processes)
if ($null -eq $started) { '(없음)' } else { $started.ToString('yyyy-MM-dd HH:mm:ss', $culture) }
"""
)

# 일반 설치(Squirrel)와 MSIX 설치의 앱 경로. 같은 이름의 CLI(`claude.exe`)는 경로가 다르다.
_SQUIRREL_APP = r"C:\Users\u\AppData\Local\AnthropicClaude\app-2.9939.2\Claude.exe"
_MSIX_APP = r"C:\Program Files\WindowsApps\Claude_2.19675.0.0_x64__test\app\Claude.exe"
_CLI = r"C:\Users\u\.local\bin\claude.exe"


def _processes(app: str) -> list[dict[str, str]]:
    """앱이 떠 있을 때의 모양. 주 프로세스보다 먼저 선 CLI, 늦게 선 렌더러와 두 번째 인스턴스."""
    return [
        {
            "path": app,
            "command": f'"{app}" claude://code/new?q=x',
            "created": "2026-09-29 12:00:00",
        },
        {"path": app, "command": f'"{app}" --type=renderer', "created": "2026-09-29 10:28:15"},
        {"path": _CLI, "command": "claude", "created": "2026-09-29 09:00:00"},
        {"path": app, "command": f'"{app}"', "created": MAIN_STARTED},
    ]


def _main_start(processes: Sequence[Mapping[str, str | None]]) -> str:
    completed = _call("Find-MainStart", _MAIN_START, {"processes": processes})
    assert completed.returncode == 0, completed.stderr
    return completed.stdout.strip()


@pytest.mark.parametrize("app", [_SQUIRREL_APP, _MSIX_APP])
def test_주_프로세스는_type_없이_가장_먼저_선_앱_프로세스다(app: str) -> None:
    assert _main_start(_processes(app)) == MAIN_STARTED


def test_렌더러와_CLI_만_떠_있으면_주_프로세스가_없다() -> None:
    processes = [p for p in _processes(_MSIX_APP) if p["path"] == _CLI or "--type=" in p["command"]]

    assert _main_start(processes) == "(없음)"


def test_시각을_모르는_앱_프로세스가_있으면_주_프로세스를_가리지_않는다() -> None:
    # 어느 것이 먼저 섰는지 모르면 늦게 선 두 번째 인스턴스를 주 프로세스로 고를 수 있다.
    processes: list[dict[str, str | None]] = [
        {**p, "created": None} if p["created"] == MAIN_STARTED else {**p}
        for p in _processes(_MSIX_APP)
    ]

    assert _main_start(processes) == "(없음)"


# 후보 폴더마다 main.log 와 그 옆 돌림 파일 main1.log 가 마지막으로 쓰인 시각(없으면 null).
_QUIT_LOGS = (
    _AT
    + """
$dirs = foreach ($d in $given.dirs) {
    [pscustomobject]@{
        Main = "$($d.name)/main.log"; MainWritten = & $at $d.main
        Rotated = "$($d.name)/main1.log"; RotatedWritten = & $at $d.rotated
    }
}
$files = @(Select-QuitLogs @($dirs) (& $at $given.since))
if ($files.Count -eq 0) { '(없음)' } else { $files -join ',' }
"""
)


@pytest.mark.parametrize(
    ("dirs", "files"),
    [
        (  # 가장 최근에 쓰인 main.log 의 폴더를 고르고, 앞선 줄이 든 돌림 파일을 먼저 읽는다
            [
                {"name": "msix", "main": "2026-09-29 12:00:00", "rotated": "2026-09-29 11:00:00"},
                {
                    "name": "roaming",
                    "main": "2026-09-29 12:30:00",
                    "rotated": "2026-09-29 11:30:00",
                },
            ],
            "roaming/main1.log,roaming/main.log",
        ),
        (  # 주 프로세스가 서기 전에 마지막으로 쓰인 돌림 파일은 볼 것이 없다
            [{"name": "roaming", "main": "2026-09-29 12:30:00", "rotated": "2026-09-29 09:00:00"}],
            "roaming/main.log",
        ),
        (  # main.log 도 서기 전에 쓰였으면 읽을 것이 없다
            [{"name": "roaming", "main": "2026-09-29 09:00:00", "rotated": None}],
            "(없음)",
        ),
        (  # main.log 가 없는 폴더는 돌림 파일이 있어도 고르지 않는다
            [{"name": "msix", "main": None, "rotated": "2026-09-29 12:40:00"}],
            "(없음)",
        ),
    ],
)
def test_읽을_로그는_가장_최근_폴더에서_주_프로세스가_선_뒤에_쓰인_것이다(
    dirs: list[dict[str, str | None]], files: str
) -> None:
    completed = _call("Select-QuitLogs", _QUIT_LOGS, {"dirs": dirs, "since": MAIN_STARTED})

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == files


# 껍질(`Get-AppQuitMarker`)이 찾은 프로세스와 파일을 선택 둘에 잇는지. 껍질이 만든 속성 이름이
# 선택이 읽는 이름과 갈리면 판정이 늘 null 이라 가드가 조용히 꺼진다(PR 직전 버그·성능 리뷰).
# 프로세스와 파일 시스템은 같은 이름의 함수로 가린다. `Join-Path` 의 구분자가 플랫폼마다 달라 경로는
# `\` 로 맞춰 대 본다.
_SHELL = (
    _AT
    + r"""
$global:read = @()
$files = @{}
foreach ($f in $given.files) { $files[$f.path] = $f }
function Get-CimInstance {
    [CmdletBinding()] param($ClassName, $Filter)
    foreach ($p in $given.processes) {
        $created = & $at $p.created
        [pscustomobject]@{
            ExecutablePath = $p.path; CommandLine = $p.command; CreationDate = $created
        }
    }
}
function Get-ChildItem {
    [CmdletBinding()] param($Path, [switch] $Directory, $Filter)
    foreach ($name in $given.packages) { [pscustomobject]@{ FullName = "$Path\$name" } }
}
function Test-Path {
    param([string] $LiteralPath)
    $files.ContainsKey($LiteralPath.Replace('/', '\'))
}
function Get-Item {
    param([string] $LiteralPath)
    [pscustomobject]@{ LastWriteTime = & $at $files[$LiteralPath.Replace('/', '\')].written }
}
function Get-Content {
    param([string] $LiteralPath, $Encoding)
    $key = $LiteralPath.Replace('/', '\')
    $global:read += $key
    $files[$key].lines
}
$env:LOCALAPPDATA = 'local'
$env:APPDATA = 'roaming'
$found = Get-AppQuitMarker
foreach ($file in $global:read) { "read=$file" }
"marker=$(if ($null -eq $found) { '(없음)' } else { $found })"
"""
)

_SHELL_FUNCTIONS = "Find-QuitMarker,Find-MainStart,Select-QuitLogs,Get-AppQuitMarker"

_MSIX_LOGS = r"local\Packages\Claude_test\LocalCache\Local\Claude\logs"


def test_껍질은_찾은_프로세스와_로그를_선택에_이어_가장_이른_표지를_준다() -> None:
    rotated_marker = "[CCD] CLI exit before update: 2 of 2 exited within 1591ms"
    files = [
        {  # MSIX 설치의 돌림 파일. 주 프로세스가 선 뒤에 쓰였고 앞선 표지가 들었다
            "path": rf"{_MSIX_LOGS}\main1.log",
            "written": "2026-09-29 11:00:00",
            "lines": [f"2026-09-29 10:59:00 [info] {rotated_marker}"],
        },
        {  # 가장 최근에 쓰인 main.log
            "path": rf"{_MSIX_LOGS}\main.log",
            "written": "2026-09-29 12:30:00",
            "lines": [*NOISE, "2026-09-29 12:19:28 [info] beforeQuitForUpdate handler fired"],
        },
        {  # 일반 설치의 main.log. 더 일찍 쓰여 읽지 않는다
            "path": r"roaming\Claude\logs\main.log",
            "written": "2026-09-29 12:00:00",
            "lines": ["2026-09-29 11:30:00 [info] Session stop before update took 1591ms"],
        },
    ]
    given: dict[str, object] = {
        "processes": _processes(_MSIX_APP),
        "packages": ["Claude_test"],
        "files": files,
    }

    completed = _call(_SHELL_FUNCTIONS, _SHELL, given)

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip().splitlines() == [
        rf"read={_MSIX_LOGS}\main1.log",
        rf"read={_MSIX_LOGS}\main.log",
        f"marker=2026-09-29 10:59:00 {rotated_marker}",
    ]


# 지시문의 `모델:` 줄. 줄 머리에서 시작하고(지시문 형식은 불릿이나 인용 없이 줄 머리다), 모델 메뉴의
# 이름과 레벨을 `/` 로 가른다. 칸은 입력창 노력 슬라이더의 위치다
# (.scratch/harness/probes/composer_effort_labels.ps1).
DIRECTIVE = """다음 작업: 기능 x. 요약
다음 단계: 구현
어디서: 새 세션
시작 프롬프트: /implement .scratch/x/issues/01-y.md
브랜치: feature/01-y
{model}
읽을 것: 없음
"""


def test_모델_줄이_없으면_고르지_않는다() -> None:
    assert _model_line_of(DIRECTIVE.format(model="")) == "(없음)"


@pytest.mark.parametrize(
    ("effort", "step"),
    [("low", 0), ("medium", 1), ("high", 2), ("xhigh", 3), ("max", 4)],
)
def test_모델_줄에서_이름과_레벨과_슬라이더_칸을_읽는다(effort: str, step: int) -> None:
    prompt = DIRECTIVE.format(model=f"모델: Opus 5.5 / {effort}")

    assert _model_line_of(prompt) == f"Opus 5.5|{effort}|{step}"


def test_레벨_뒤에_붙은_이유는_읽지_않는다() -> None:
    prompt = DIRECTIVE.format(model="모델: Sonnet 5.5 / high. 결정표의 PR 반영·병합")

    assert _model_line_of(prompt) == "Sonnet 5.5|high|2"


def test_줄_머리가_아닌_모델은_지시문의_줄이_아니다() -> None:
    prompt = DIRECTIVE.format(model="이어받을 상태: 모델: Opus 5.5 / high 로 열었다")

    assert _model_line_of(prompt) == "(없음)"


def test_결정표_칸을_백틱째_옮긴_줄도_읽는다() -> None:
    prompt = DIRECTIVE.format(model="모델: `Sonnet 5.5 / high`. 결정표의 PR 반영·병합")

    assert _model_line_of(prompt) == "Sonnet 5.5|high|2"


@pytest.mark.parametrize(
    ("line", "cause"),
    [
        ("모델: Opus 5.5 / ultracode", "를 모른다"),  # 슬라이더의 여섯째 칸은 레벨이 아니다
        ("모델: Opus 5.5 / High", "를 모른다"),  # 레벨은 API 이름 그대로 소문자다
        ("모델: Opus 5.5", "읽지 못했다"),  # 레벨이 없다
        ("모델:  / high", "모델 이름이 없다"),
        ("모델: Opus 5.5 / high\n모델: Sonnet 5.5 / high", "줄이 2개다"),
    ],
)
def test_읽을_수_없는_모델_줄이면_까닭과_함께_쏘기_전에_멈춘다(line: str, cause: str) -> None:
    error = _model_line_error(DIRECTIVE.format(model=line))

    assert cause in error


_NEXT_SESSION = Path(__file__).parents[2] / ".claude" / "skills" / "next-session" / "SKILL.md"

_MODEL_LINES = """
foreach ($prompt in $given.prompts) {
    $found = Read-ModelLine $prompt
    "$($found.Model)|$($found.Effort)|$($found.Step)"
}
"""


def _decision_table_model_cells() -> list[str]:
    """next-session 결정표의 "모델" 칸에서 백틱으로 감싼 값(`<모델> / <레벨>`)을 모두 뽑는다."""
    rows = [
        line
        for line in _NEXT_SESSION.read_text(encoding="utf-8").splitlines()
        if line.startswith("| ")
    ]
    header = next((row for row in rows if "| 모델 |" in row), None)
    assert header, (
        f'{_NEXT_SESSION} 에서 머리 칸에 "모델"이 든 표를 찾지 못했다. 결정표의 열 이름이 바뀌었나'
    )
    column = [cell.strip() for cell in header.strip("|").split("|")].index("모델")
    cells: list[str] = []
    for row in rows[rows.index(header) + 2 :]:
        cell = row.strip("|").split("|")[column]
        cells += re.findall(r"`([^`]+ / [a-z]+)`", cell)
    return cells


def test_이_저장소의_결정표_모델_칸은_스크립트가_읽는다() -> None:
    cells = _decision_table_model_cells()
    assert len(cells) >= 2, f"결정표에서 모델 칸을 찾지 못했다: {cells}"

    completed = _call(
        "Get-EffortSteps,Read-ModelLine",
        _MODEL_LINES,
        {"prompts": [f"모델: {cell}" for cell in cells]},
    )

    assert completed.returncode == 0, completed.stderr
    read = completed.stdout.strip().splitlines()
    assert [line.rsplit("|", 1)[0].replace("|", " / ") for line in read] == cells


def test_레벨_스윕의_갈래_값은_스크립트가_읽는다() -> None:
    # next-session 3단계가 결정표 칸 대신 tools/model_sweep.py 의 값을 모델 줄에 옮긴다(ADR 0029
    # 이력).
    arms = list(model_sweep.ARMS)

    completed = _call(
        "Get-EffortSteps,Read-ModelLine",
        _MODEL_LINES,
        {"prompts": [f"모델: {arm}. 레벨 스윕의 갈래" for arm in arms]},
    )

    assert completed.returncode == 0, completed.stderr
    read = completed.stdout.strip().splitlines()
    assert [line.rsplit("|", 1)[0].replace("|", " / ") for line in read] == arms


# 노력 버튼의 이름(앱 2.19675.0.0, 한국어)에서 칸을 읽는다. 버튼은 이름 뒤에 덧붙임이 붙을 수 있다.
_EFFORT_BUTTON = """
$button = [pscustomobject]@{ Current = [pscustomobject]@{ Name = $given.name } }
$step = Get-EffortButtonStep $button
if ($null -eq $step) { '(없음)' } else { "$step" }
"""


@pytest.mark.parametrize(
    ("name", "step"),
    [
        ("노력: 낮음", "0"),
        ("노력: 중간", "1"),
        ("노력: 엑스트라", "3"),
        ("노력: 최대 3.5× 이상 사용량", "4"),  # Opus 의 최대 칸은 사용량 덧붙임이 붙는다
        ("노력: Ultracode", "(없음)"),  # 레벨이 아닌 칸은 되돌리지 않는다
        ("노력: 높음이", "(없음)"),  # 이름 뒤에 공백 없이 붙은 글은 다른 이름이다
    ],
)
def test_노력_버튼의_이름에서_칸을_읽는다(name: str, step: str) -> None:
    completed = _call(
        "Get-EffortLabels,Test-ButtonShows,Get-EffortButtonStep", _EFFORT_BUTTON, {"name": name}
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == step


# 고르기 전의 값(Read-DraftDefaults 가 돌려주는 모양)을 받아 쓰는 순수 함수들.
_DRAFT = """
$step = if ($null -eq $given.step) { $null } else { [int]$given.step }
$draft = [pscustomobject]@{ Model = $given.model; EffortStep = $step; EffortLabel = '' }
"""

_REPAIR_HINT = _DRAFT + "Get-RepairHint $draft\n"

_DRAFT_CHANGED = (
    _DRAFT
    + """
$pick = [pscustomobject]@{ Model = $given.pick_model; Effort = ''; Step = [int]$given.pick_step }
"$(Test-DraftChanged $draft $pick)"
"""
)


@pytest.mark.parametrize(
    ("model", "step", "pick_model", "pick_step", "changed"),
    [
        ("Opus 5.5", 3, "Opus 5.5", 3, "False"),  # 같으면 되돌릴 것이 없다
        ("Opus 5.5", 3, "Sonnet 5.5", 3, "True"),
        ("Opus 5.5", 3, "Opus 5.5", 2, "True"),
        ("Opus 5.5", None, "Opus 5.5", 3, "True"),  # 원래 노력이 목록 밖이면 고른 칸과 다르다
    ],
)
def test_고른_값이_원래_값과_다를_때만_기본값이_바뀐_것으로_친다(
    model: str, step: int | None, pick_model: str, pick_step: int, changed: str
) -> None:
    given: dict[str, object] = {
        "model": model,
        "step": step,
        "pick_model": pick_model,
        "pick_step": pick_step,
    }
    completed = _call("Test-DraftChanged", _DRAFT_CHANGED, given)

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == changed


def test_복구_안내는_원래_값으로_돌리는_명령이다() -> None:
    completed = _call(
        "Get-EffortSteps,Get-RepairHint", _REPAIR_HINT, {"model": "Opus 5.5", "step": 3}
    )

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == (
        "친다: pwsh -NoProfile -File tools/open_session.ps1 -Action defaults"
        " -Model 'Opus 5.5' -Effort xhigh"
    )


# 보내기 전에 멈춘 길(`held=`, 고르기·보내기·제출 확인의 실패)이 함께 쓰는 복구 줄. 고르기 전에
# 멈췄으면 $draft 가 없다.
_PENDING_RESTORE = """
$draft = $null
if ($null -ne $given.model) {
    $draft = [pscustomobject]@{ Model = $given.model; EffortStep = [int]$given.step }
}
$pick = [pscustomobject]@{ Model = $given.pick_model; Effort = ''; Step = [int]$given.pick_step }
$line = Get-PendingRestoreLine $draft $pick
if ($null -eq $line) { '(없음)' } else { $line }
"""

_PENDING_RESTORE_FUNCTIONS = (
    "Get-EffortSteps,Get-RepairHint,Test-DraftChanged,Get-PendingRestoreLine"
)


@pytest.mark.parametrize(
    ("model", "pick_model"),
    [
        (None, "Sonnet 5.5"),  # 원래 값을 읽기 전에 멈췄다
        ("Sonnet 5.5", "Sonnet 5.5"),  # 고른 값이 원래 값과 같다
    ],
)
def test_보내기_전에_멈춰도_기본값이_그대로면_복구를_남기지_않는다(
    model: str | None, pick_model: str
) -> None:
    given: dict[str, object] = {"model": model, "step": 3, "pick_model": pick_model, "pick_step": 3}
    completed = _call(_PENDING_RESTORE_FUNCTIONS, _PENDING_RESTORE, given)

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == "(없음)"


def test_보내기_전에_멈추면_바뀐_기본값을_되돌리는_명령을_남긴다() -> None:
    given: dict[str, object] = {
        "model": "Opus 5.5",
        "step": 3,
        "pick_model": "Sonnet 5.5",
        "pick_step": 2,
    }
    completed = _call(_PENDING_RESTORE_FUNCTIONS, _PENDING_RESTORE, given)

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == (
        "restore=필요: 새 세션 화면의 기본값이 바뀌었을 수 있다. 사람이 보낸 뒤"
        " 친다: pwsh -NoProfile -File tools/open_session.ps1 -Action defaults"
        " -Model 'Opus 5.5' -Effort xhigh"
    )


def test_원래_노력이_목록_밖이면_복구_안내는_화면에서_고르라고_한다() -> None:
    completed = _call(
        "Get-EffortSteps,Get-RepairHint", _REPAIR_HINT, {"model": "Opus 5.5", "step": None}
    )

    assert completed.returncode == 0, completed.stderr
    assert "-Effort" not in completed.stdout
    assert "새 세션 화면에서 모델을 'Opus 5.5' 로" in completed.stdout


# 쏘기 전의 스냅숏, 화면 확인, 입력창 찾기, 제출 확인이 모두 이 비교로 지시문을 알아본다. 앱은
# 딥링크로 온 슬래시 명령의 첫 `/` 를 전각 `／`(U+FF0F)로 바꿔 넣는다. 문화권 비교는 둘을 같게 보지
# 않아, 고치기 전에는 그 화면을 끝내 못 찾았다(PR #50).
_NORMALIZE_SLASH = """
"[$(Normalize-Slash $given.text)]"
"""

_TEST_NEEDLE = """
"$(Test-Needle $given.text $given.needle)"
"""

# 지시문 첫 줄의 앞 24자(`Send-Prompt` 의 needle). 프롬프트 파일에서 온 글이라 슬래시가 반각이다.
NEEDLE = "/implement .scratch/x/is"


@pytest.mark.parametrize(
    ("text", "restored"),
    [
        ("／implement .scratch/x", "/implement .scratch/x"),
        ("x ／implement", "x ／implement"),  # 앱이 바꾸는 것은 첫 글자뿐이다
    ],
)
def test_첫_글자의_전각_슬래시만_반각으로_되돌린다(text: str, restored: str) -> None:
    completed = _call("Normalize-Slash", _NORMALIZE_SLASH, {"text": text})

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == f"[{restored}]"


@pytest.mark.parametrize(
    ("text", "found"),
    [
        ("/implement .scratch/x/issues/01-y.md", "True"),
        ("／implement .scratch/x/issues/01-y.md", "True"),  # 앱이 바꿔 넣은 화면
        (None, "False"),  # 이름이 없는 요소
        ("/implement .scratch", "False"),  # 첫 줄의 앞부분만 있다
        ("다음 작업: /implement .scratch/x/issues", "False"),  # 줄 가운데의 같은 글
    ],
)
def test_화면의_글이_지시문_첫_줄로_시작할_때만_그_화면으로_친다(
    text: str | None, found: str
) -> None:
    completed = _call("Normalize-Slash,Test-Needle", _TEST_NEEDLE, {"text": text, "needle": NEEDLE})

    assert completed.returncode == 0, completed.stderr
    assert completed.stdout.strip() == found


# 첫 줄의 스킬 명령을 스킬 파일을 읽으라는 한 줄로 옮긴다. 딥링크의 슬래시 명령은 앱이 전각으로 바꿔
# 명령이 되지 못한다. 옮기지 못한 줄은 그대로 두고, 쏜 뒤 `held=` 가 받는다.
_START_LINE = """
Convert-StartLine $given.line $given.root
"""


@pytest.fixture
def skills_root(tmp_path: Path) -> Path:
    """스킬 둘이 있는 저장소. `.claude/skills/` 밖의 SKILL.md 도 하나 둔다."""
    for skill in (".claude/skills/implement", ".claude/skills/retro", "docs"):
        (tmp_path / skill).mkdir(parents=True)
        (tmp_path / skill / "SKILL.md").write_text("# x\n", encoding="utf-8")
    return tmp_path


def _start_line(line: str, root: str) -> str:
    completed = _call("Convert-StartLine", _START_LINE, {"line": line, "root": root})
    assert completed.returncode == 0, completed.stderr
    # 끝의 공백까지 본다. 인자가 없는 줄은 '인자:' 로 끝난다.
    return completed.stdout.rstrip("\n")


@pytest.mark.parametrize(
    ("line", "skill", "args"),
    [
        ("/implement .scratch/x/issues/01-y.md", "implement", "인자: .scratch/x/issues/01-y.md"),
        ("/retro", "retro", "인자:"),
    ],
)
def test_첫_줄의_스킬_명령은_그_스킬_파일을_읽으라는_한_줄로_옮긴다(
    skills_root: Path, line: str, skill: str, args: str
) -> None:
    converted = _start_line(line, str(skills_root))

    assert converted.startswith(f".claude/skills/{skill}/SKILL.md 를 읽어 그대로 따른다.")
    assert f"`{skills_root}`" in converted
    assert converted.endswith(args)


@pytest.mark.parametrize(
    ("line", "has_root"),
    [
        pytest.param("/to-spec x", True, id="스킬_파일이_없다"),
        # 대소문자를 가리지 않는 파일 시스템(윈도)에서도 옮기지 않는다
        pytest.param("/Implement x", True, id="이름은_소문자_kebab"),
        pytest.param("/../../docs x", True, id="스킬_폴더_밖을_가리킨다"),
        pytest.param("/implement x", False, id="연_저장소를_모른다"),
    ],
)
def test_이_저장소의_스킬_파일을_가리킬_수_없는_첫_줄은_그대로_둔다(
    skills_root: Path, line: str, has_root: bool
) -> None:
    assert _start_line(line, str(skills_root) if has_root else "") == line


def test_옮긴_첫_줄을_받는_세션의_훅이_알아보고_작업_폴더를_가른다(skills_root: Path) -> None:
    """문구의 원천은 이 스크립트이고 훅(`hook_prompt_directive`)은 그것을 글자로 파싱한다.

    고정 머리 뒤만 갈리면 훅이 막지만(fail-closed), 머리까지 바뀌면 조용히 지나가므로 한 체크아웃
    안의 두 문구 대조는 여기서 잡는다(체크아웃 사이는 못 잡는다).
    """
    first = _start_line("/implement .scratch/x/issues/01-y.md", str(skills_root))
    prompt = f"{first}\n\n{DIRECTIVE.format(model='')}"

    assert block_reason_for(prompt, str(skills_root)) is None
    assert block_reason_for(prompt, str(skills_root / "elsewhere")) is not None


# 새 세션이 첫 턴에 스스로 이름을 붙일 때까지 사이드바 행을 기다린다. 스킬은 `-TimeoutSec 90` 을
# 넘기는데, 행을 찾는 함수의 10초가 그 값을 덮고 있었다(PR #60). 앱의 접근성 트리 대신 가짜를 준다.
# UIAutomation 타입은 ubuntu 러너에 없고 윈도의 pwsh 에도 `Add-Type` 전에는 없어
# (.scratch/harness/probes/quit_marker_real_app.ps1), 조건을 만드는 `New-Object` 를 같은 이름의
# 함수로 가리고 `$Auto`·`$Types`·`$Scope` 의 정적 멤버를 클래스로 흉내 낸다. 창은 `shows_at` 번째
# 탐색부터 `rows` 를, 그 전에는 `rows_before` 를 버튼 이름으로 준다.
_FOCUS = """
class FakeUia {
    static [string] $ControlTypeProperty = 'ControlType'
    static [string] $Button = 'Button'
    static [string] $Descendants = 'Descendants'
}
$Auto = $Types = $Scope = [FakeUia]
function New-Object { param([string] $TypeName, [object[]] $ArgumentList) $TypeName }
$win = [pscustomobject]@{ Polls = 0 }
$win | Add-Member -MemberType ScriptMethod -Name FindAll -Value {
    param($scope, $condition)
    $this.Polls++
    $names = if ($this.Polls -ge $given.shows_at) { $given.rows } else { $given.rows_before }
    foreach ($name in $names) { [pscustomobject]@{ Current = [pscustomobject]@{ Name = $name } } }
}
function Get-ClaudeWindow { $win }
function Invoke-Row([string] $rowName) { $global:pressed = $rowName; 'invoke' }
$Title = $given.title
$TimeoutSec = $given.timeout
$watch = [Diagnostics.Stopwatch]::StartNew()
try { Focus-Session } catch { "error=$($_.Exception.Message)" }
"pressed=$global:pressed"
"waited=$($watch.Elapsed.TotalSeconds)"
"""

_FOCUS_FUNCTIONS = "Wait-For,Find-RowByTitle,Focus-Session"

TITLE = "feature/01-y"

# 행이 아닌 버튼. 옵션 버튼은 제목 뒤에 글이 붙고, 다른 세션의 제목은 이 제목으로 끝나도 앞이 공백이
# 아니다.
OTHER_BUTTONS = [f"{TITLE}에 대한 더 많은 옵션", f"유휴 chore/{TITLE}"]


def _focus(given: dict[str, object]) -> dict[str, str]:
    completed = _call(_FOCUS_FUNCTIONS, _FOCUS, {"title": TITLE, **given})
    assert completed.returncode == 0, completed.stderr
    lines = completed.stdout.strip().splitlines()
    return {key: value for key, _, value in (line.partition("=") for line in lines)}


def test_focus_는_스킬이_넘긴_시간만큼_행을_기다린다() -> None:
    shown = _focus({"timeout": 1, "shows_at": 1, "rows": OTHER_BUTTONS, "rows_before": []})

    assert shown["error"] == f"1초 안에 행 '{TITLE}' 을(를) 찾지 못했다."
    assert float(shown["waited"]) < 9, shown  # 행을 찾는 함수의 기본값 10초가 아니다
    assert shown["pressed"] == ""


def test_focus_는_제목으로_끝나는_행이_나타나면_그_행을_누른다() -> None:
    row = f"실행 중 {TITLE}"
    given: dict[str, object] = {
        "timeout": 5,
        "shows_at": 2,
        "rows": [*OTHER_BUTTONS, row],
        "rows_before": OTHER_BUTTONS,
    }

    shown = _focus(given)

    assert "error" not in shown, shown
    assert shown["focus"].endswith(" via invoke")
    assert shown["pressed"] == row


# 스킬과 스크립트의 사용·복구 줄이 스크립트를 부르는 명령. 위 focus 시험은 본문이 `$TimeoutSec` 을
# 직접 정의하므로, 명령 줄의 `-<이름>` 이 스크립트의 인자(`param` 블록)에 묶이는 고리는 여기서 잰다.
_OPEN_SESSION_SKILL = Path(__file__).parents[2] / ".claude" / "skills" / "open-session" / "SKILL.md"

_PARAMS = """
$ast.ParamBlock.Parameters | ForEach-Object { $_.Name.VariablePath.UserPath }
"""


def test_스킬과_복구_안내가_넘기는_인자는_모두_스크립트가_받는다() -> None:
    commands = [
        line.split("tools/open_session.ps1", 1)[1]
        for source in (_OPEN_SESSION_SKILL, SCRIPT)
        for line in source.read_text(encoding="utf-8").splitlines()
        if "tools/open_session.ps1 -Action" in line
    ]
    passed = {name for command in commands for name in re.findall(r"(?<!\S)-([A-Z]\w+)", command)}
    assert "TimeoutSec" in passed, commands  # 스킬이 focus 에 넘긴다

    completed = _call("", _PARAMS, {})

    assert completed.returncode == 0, completed.stderr
    params = set(completed.stdout.split())
    assert passed <= params, f"스크립트가 받지 않는 인자: {passed - params}"
