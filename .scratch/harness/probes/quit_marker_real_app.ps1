# tools/open_session.ps1 의 `Get-AppQuitMarker` 껍질을 이 PC 의 실제 앱으로 부른다(ADR 0030 이력, 대기열 17).
#
# 선택(`Find-MainStart`·`Select-QuitLogs`)은 tests/tools/test_open_session.py 가 재고, 프로세스와 파일을 찾는 껍질은 시험 밖이다.
# 이 프로브는 껍질을 스크립트의 AST 에서 떼어 가짜 없이 부르고, 무엇을 골랐는지 찍는다. 읽은 로그 파일은 `Get-Content` 를 같은 이름의
# 함수로 가려 받은 경로를 적은 뒤 진짜 cmdlet 에 넘겨 얻는다. 읽기만 한다. 함께 UIAutomation 타입(`PropertyCondition`)이 `Add-Type`
# 전에는 없는지 찍는다. 시험이 그 타입을 쓰는 `New-Object` 를 가짜로 가리는 까닭이다.
#
# 출력: `uia-before=`·`uia-after=`(타입이 있으면 present), `started=`(주 프로세스가 선 시각), `read=`(읽은 파일, 차례대로),
# `marker=`(끝내기 표지 줄, 없으면 (없음)), `seconds=`(껍질 한 번의 벽시계 초). 앱이 떠 있어 주 프로세스를 찾았고 파일을 하나 이상
# 읽은 회차만 측정이다. 아니면 그 까닭을 찍고 1로 끝난다.
#
# 돌리는 법: 저장소 루트에서 `pwsh -NoProfile -File .scratch/harness/probes/quit_marker_real_app.ps1`. Windows 의 데스크톱 앱이 떠 있어야 한다.
param([string] $Script = (Join-Path $PSScriptRoot '..\..\..\tools\open_session.ps1'))
$ErrorActionPreference = 'Stop'

"uia-before=$(if ('System.Windows.Automation.PropertyCondition' -as [type]) { 'present' } else { 'absent' })"
Add-Type -AssemblyName UIAutomationClient
"uia-after=$(if ('System.Windows.Automation.PropertyCondition' -as [type]) { 'present' } else { 'absent' })"

$language = 'System.Management.Automation.Language'
$ast = ("$language.Parser" -as [type])::ParseFile((Resolve-Path $Script), [ref]$null, [ref]$null)
$definition = "$language.FunctionDefinitionAst" -as [type]
foreach ($name in 'Find-QuitMarker', 'Find-MainStart', 'Select-QuitLogs', 'Get-AppQuitMarker') {
    $isTarget = { param($node) $node -is $definition -and $node.Name -eq $name }.GetNewClosure()
    $fn = $ast.Find($isTarget, $true)
    if ($null -eq $fn) { throw "$name 가 스크립트에 없다" }
    . ([scriptblock]::Create($fn.Extent.Text))
}

$global:read = @()
function Get-Content {
    param([string] $LiteralPath, [string] $Encoding)
    $global:read += $LiteralPath
    Microsoft.PowerShell.Management\Get-Content -LiteralPath $LiteralPath -Encoding $Encoding
}

$started = Find-MainStart @(Get-CimInstance Win32_Process -Filter "Name = 'Claude.exe'" -ErrorAction SilentlyContinue)
"started=$(if ($null -eq $started) { '(없음)' } else { $started.ToString('yyyy-MM-dd HH:mm:ss') })"
$watch = [Diagnostics.Stopwatch]::StartNew()
$found = Get-AppQuitMarker
$seconds = [math]::Round($watch.Elapsed.TotalSeconds, 2)
foreach ($file in $global:read) { "read=$file" }
"marker=$(if ($null -eq $found) { '(없음)' } else { $found })"
"seconds=$seconds"

if ($null -eq $started) { '측정 아님: 앱의 주 프로세스를 찾지 못했다'; exit 1 }
if ($global:read.Count -eq 0) { '측정 아님: 읽은 로그 파일이 없다'; exit 1 }
