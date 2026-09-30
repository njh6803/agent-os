"""tools/open_session.ps1 의 순수 함수. 파워셸 AST 에서 함수 하나를 떼어 pwsh 로 부른다.

딥링크를 쏘고 앱의 접근성 트리를 누르는 부분, 앱의 주 프로세스와 로그를 찾는 부분은
실제 실행으로 확인한다. pwsh 가 없으면 건너뛰지 않고 실패한다(`.claude/rules/tests.md`).
CI 의 ubuntu 러너에는 pwsh 가 있다.
"""

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[2] / "tools" / "open_session.ps1"

# 스크립트에서 이름으로 함수 하나만 떼어 정의하고 부른다. 스크립트 전체를 돌리면 창을 찾고
# 딥링크를 쏜다. pwsh 는 파이프로 가는 출력을 콘솔 코드 페이지(윈도에서 cp949)로 쓴다. UTF-8 로
# 고정한다(2026-09-30 실측, 고정하지 않으면 한글 에러가 풀리지 않아 stderr 가 사라졌다).
_CALL = """
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$PSStyle.OutputRendering = 'PlainText'
$language = 'System.Management.Automation.Language'
$ast = ("$language.Parser" -as [type])::ParseFile($env:OPEN_SESSION_SCRIPT, [ref]$null, [ref]$null)
$definition = "$language.FunctionDefinitionAst" -as [type]
$isTarget = { param($node) $node -is $definition -and $node.Name -eq 'Find-QuitMarker' }
$fn = $ast.Find($isTarget, $true)
if ($null -eq $fn) { throw 'Find-QuitMarker 가 스크립트에 없다' }
. ([scriptblock]::Create($fn.Extent.Text))
$given = $env:OPEN_SESSION_ARGS | ConvertFrom-Json
$culture = [cultureinfo]::InvariantCulture
$since = [datetime]::ParseExact($given.since, 'yyyy-MM-dd HH:mm:ss', $culture)
$found = Find-QuitMarker @($given.lines) $since
if ($null -eq $found) { '(없음)' } else { $found }
"""

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
    try:
        completed = subprocess.run(
            ["pwsh", "-NoProfile", "-NonInteractive", "-Command", _CALL],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            env={
                **os.environ,
                "OPEN_SESSION_SCRIPT": str(SCRIPT),
                "OPEN_SESSION_ARGS": json.dumps({"lines": lines, "since": since}),
            },
            check=False,
        )
    except FileNotFoundError:
        pytest.fail("pwsh 가 없다. 이 테스트는 PowerShell 7 로 스크립트의 함수를 부른다")
    assert completed.returncode == 0, completed.stderr
    return completed.stdout.strip()


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
