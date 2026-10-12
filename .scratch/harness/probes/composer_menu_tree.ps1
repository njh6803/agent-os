# 진단 전용. 입력창의 모델·노력 버튼을 하나 골라 메뉴를 연 뒤 새로 생긴 요소를 찍고 Esc 로 닫는다. 아무것도 고르지 않는다.
# 쓰는 법: pwsh -NoProfile -File .scratch/harness/probes/composer_menu_tree.ps1 -Prefix '노력:'   (또는 '모델:')
# 버튼이 여럿이면(분할 보기) 첫 것을 연다. 그 패널의 세션 설정은 바뀌지 않는다(Esc 로 닫는다).
param([Parameter(Mandatory)] [string] $Prefix)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Windows.Forms
$Auto = [System.Windows.Automation.AutomationElement]
$Scope = [System.Windows.Automation.TreeScope]
$True_ = [System.Windows.Automation.Condition]::TrueCondition

$wins = @($Auto::RootElement.FindAll($Scope::Children, $True_) | Where-Object { $_.Current.Name -eq 'Claude' })
if ($wins.Count -ne 1) { throw "Claude 창이 $($wins.Count)개다." }
$win = $wins[0]

function Snapshot {
    $map = @{}
    foreach ($el in @($win.FindAll($Scope::Descendants, $True_))) {
        try {
            $key = ($el.GetRuntimeId() -join '.')
            $map[$key] = "$($el.Current.ControlType.ProgrammaticName -replace 'ControlType\.','')|$($el.Current.Name)|enabled=$($el.Current.IsEnabled)"
        } catch {}
    }
    return $map
}

$buttons = @($win.FindAll($Scope::Descendants, $True_) | Where-Object { try { $_.Current.Name.StartsWith($Prefix) } catch { $false } })
"buttons=$($buttons.Count)"
$buttons | ForEach-Object { "  [$($_.Current.Name)] $($_.Current.ControlType.ProgrammaticName)" }
if ($buttons.Count -eq 0) { exit 1 }
$target = $buttons[0]

$before = Snapshot
$target.SetFocus()
Start-Sleep -Milliseconds 300
[System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
Start-Sleep -Milliseconds 1200
$after = Snapshot
"--- 메뉴를 연 뒤 새로 생긴 요소 ---"
foreach ($key in $after.Keys) { if (-not $before.ContainsKey($key)) { "  $($after[$key])" } }
# 슬라이더면 범위와 값, 지원하는 패턴을 찍는다. 값을 바꾸지 않는다.
$sliderCond = New-Object System.Windows.Automation.PropertyCondition($Auto::ControlTypeProperty, [System.Windows.Automation.ControlType]::Slider)
foreach ($s in @($win.FindAll($Scope::Descendants, $sliderCond))) {
    $pats = ($s.GetSupportedPatterns() | ForEach-Object { $_.ProgrammaticName -replace 'PatternIdentifiers.Pattern', '' }) -join ','
    "slider [$($s.Current.Name)] patterns=$pats"
    try {
        $rv = $s.GetCurrentPattern([System.Windows.Automation.RangeValuePattern]::Pattern).Current
        "  range min=$($rv.Minimum) max=$($rv.Maximum) value=$($rv.Value) small=$($rv.SmallChange) large=$($rv.LargeChange) readonly=$($rv.IsReadOnly)"
    } catch { "  range: 읽지 못했다 $($_.Exception.Message)" }
    try { "  value-pattern=$($s.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value)" } catch {}
    try { "  help=$($s.Current.HelpText) itemstatus=$($s.Current.ItemStatus)" } catch {}
}
[System.Windows.Forms.SendKeys]::SendWait('{ESC}')
Start-Sleep -Milliseconds 600
$closed = Snapshot
$left = @($after.Keys | Where-Object { -not $before.ContainsKey($_) -and $closed.ContainsKey($_) }).Count
"closed: 남은 새 요소 $left 개"
