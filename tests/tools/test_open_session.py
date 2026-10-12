"""tools/open_session.ps1 의 순수 함수. 파워셸 AST 에서 함수 하나를 떼어 pwsh 로 부른다.

딥링크를 쏘고 앱의 접근성 트리를 누르는 부분, 앱의 주 프로세스와 로그를 찾는 부분은
실제 실행으로 확인한다. pwsh 가 없으면 건너뛰지 않고 실패한다(`.claude/rules/tests.md`).
CI 의 ubuntu 러너에는 pwsh 가 있다.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[2] / "tools" / "open_session.ps1"

# 스크립트에서 이름으로 함수 하나만 떼어 정의하고, 뒤에 붙인 본문이 그 함수를 부른다. 스크립트
# 전체를 돌리면 창을 찾고 딥링크를 쏜다. pwsh 는 파이프로 가는 출력을 콘솔 코드 페이지(윈도에서
# cp949)로 쓴다. UTF-8 로 고정한다(2026-09-30 실측, 고정하지 않으면 한글 에러가 풀리지 않아 stderr
# 가 사라졌다).
_LOAD = """
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$PSStyle.OutputRendering = 'PlainText'
$language = 'System.Management.Automation.Language'
$ast = ("$language.Parser" -as [type])::ParseFile($env:OPEN_SESSION_SCRIPT, [ref]$null, [ref]$null)
$definition = "$language.FunctionDefinitionAst" -as [type]
foreach ($name in $env:OPEN_SESSION_FUNCTION -split ',') {
    $isTarget = { param($node) $node -is $definition -and $node.Name -eq $name }.GetNewClosure()
    $fn = $ast.Find($isTarget, $true)
    if ($null -eq $fn) { throw "$name 가 스크립트에 없다" }
    . ([scriptblock]::Create($fn.Extent.Text))
}
$given = $env:OPEN_SESSION_ARGS | ConvertFrom-Json
"""

_QUIT_MARKER = """
$culture = [cultureinfo]::InvariantCulture
$since = [datetime]::ParseExact($given.since, 'yyyy-MM-dd HH:mm:ss', $culture)
$found = Find-QuitMarker @($given.lines) $since
if ($null -eq $found) { '(없음)' } else { $found }
"""

_MODEL_LINE = """
$found = Read-ModelLine $given.prompt
if ($null -eq $found) { '(없음)' } else { "$($found.Model)|$($found.Effort)|$($found.Step)" }
"""


def _call(function: str, body: str, given: dict[str, object]) -> subprocess.CompletedProcess[str]:
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
        )
    except FileNotFoundError:
        pytest.fail("pwsh 가 없다. 이 테스트는 PowerShell 7 로 스크립트의 함수를 부른다")


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
