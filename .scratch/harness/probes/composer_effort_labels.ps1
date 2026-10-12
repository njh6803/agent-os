# 진단 전용. 보내지 않은 새 세션 화면의 입력창에서 노력 슬라이더를 칸마다 옮겨 이름을 읽고 처음 값으로 되돌린다.
# 세션에 묶인 입력창을 건드리지 않으려고, 딥링크로 표지 글이 든 새 세션 화면을 열고 그 표지가 든 입력창이
# 하나뿐일 때만 움직인다. 보내지 않는다. 끝나면 입력창의 표지를 지운다(화면은 사람이 다른 세션을 고르면 닫힌다).
# 쓰는 법: pwsh -NoProfile -File .scratch/harness/probes/composer_effort_labels.ps1 [-Leave <칸>]
# -Leave 를 주면 처음 값 대신 그 칸에 두고 닫는다. 보내지 않은 화면에서 옮긴 값이 다음 새 세션 화면의 기본값으로 남는지 볼 때 쓴다.
param([int] $Leave = -1)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Windows.Forms
$Auto = [System.Windows.Automation.AutomationElement]
$Scope = [System.Windows.Automation.TreeScope]
$Types = [System.Windows.Automation.ControlType]
$True_ = [System.Windows.Automation.Condition]::TrueCondition

$marker = "effort-probe-$(Get-Date -Format HHmmssfff)"
$wins = @($Auto::RootElement.FindAll($Scope::Children, $True_) | Where-Object { $_.Current.Name -eq 'Claude' })
if ($wins.Count -ne 1) { throw "Claude 창이 $($wins.Count)개다." }
$win = $wins[0]

Start-Process ('claude://code/new?q=' + [uri]::EscapeDataString($marker))
$editCond = New-Object System.Windows.Automation.PropertyCondition($Auto::ControlTypeProperty, $Types::Edit)
$box = $null
for ($i = 0; $i -lt 40 -and -not $box; $i++) {
    Start-Sleep -Milliseconds 500
    $hits = @($win.FindAll($Scope::Descendants, $editCond) | Where-Object { try { $_.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value -eq $marker } catch { $false } })
    if ($hits.Count -eq 1) { $box = $hits[0] }
}
if (-not $box) { throw '표지가 든 새 세션 입력창을 찾지 못했다. 아무것도 움직이지 않았다.' }
"draft=$marker"

# 표지 입력창에서 위로 올라가며 그 이름의 버튼이 처음 보이는 조상에서 하나일 때만 쓴다. 분할 보기면 창 전체에는
# 패널마다 버튼이 있어 다른 세션의 입력창을 움직인다.
$walker = [System.Windows.Automation.TreeWalker]::ControlViewWalker
$buttonCond = New-Object System.Windows.Automation.PropertyCondition($Auto::ControlTypeProperty, $Types::Button)
function Find-Prefixed([string] $prefix) {
    $node = $box
    for ($i = 0; $i -lt 20; $i++) {
        $node = $walker.GetParent($node)
        if (-not $node) { return @() }
        $hits = @($node.FindAll($Scope::Descendants, $buttonCond) | Where-Object { try { $_.Current.Name.StartsWith($prefix) } catch { $false } })
        if ($hits.Count -gt 0) { return $hits }
    }
    return @()
}
$effortButtons = Find-Prefixed '노력:'
$modelButtons = Find-Prefixed '모델:'
"new-session-defaults model=[$(($modelButtons | ForEach-Object { $_.Current.Name }) -join ' / ')] effort=[$(($effortButtons | ForEach-Object { $_.Current.Name }) -join ' / ')]"
if ($effortButtons.Count -ne 1) {
    $box.SetFocus(); Start-Sleep -Milliseconds 200
    [System.Windows.Forms.SendKeys]::SendWait('^a'); [System.Windows.Forms.SendKeys]::SendWait('{DELETE}')
    throw "표지 입력창 가까이의 노력 버튼이 $($effortButtons.Count)개다. 움직이지 않고 표지만 지웠다."
}

$effortButtons[0].SetFocus()
Start-Sleep -Milliseconds 300
[System.Windows.Forms.SendKeys]::SendWait('{ENTER}')
Start-Sleep -Milliseconds 1000
$sliderCond = New-Object System.Windows.Automation.PropertyCondition($Auto::ControlTypeProperty, $Types::Slider)
$slider = $win.FindFirst($Scope::Descendants, $sliderCond)
if (-not $slider) { throw '슬라이더가 열리지 않았다.' }
$range = $slider.GetCurrentPattern([System.Windows.Automation.RangeValuePattern]::Pattern)
$valueP = $slider.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern)
$orig = [int]$range.Current.Value
"orig=$orig label=$($valueP.Current.Value)"

# 키로 옮긴다. 웹 슬라이더는 RangeValue.SetValue 를 받지 않을 수 있고, 사람의 조작과 같은 길이 키다.
$slider.SetFocus()
Start-Sleep -Milliseconds 200
[System.Windows.Forms.SendKeys]::SendWait('{HOME}')
Start-Sleep -Milliseconds 400
for ($v = 0; $v -le [int]$range.Current.Maximum; $v++) {
    "value=$([int]$range.Current.Value) label=$($valueP.Current.Value) button=$((Find-Prefixed '노력:' | ForEach-Object { $_.Current.Name }) -join ' / ')"
    [System.Windows.Forms.SendKeys]::SendWait('{RIGHT}')
    Start-Sleep -Milliseconds 400
}
# 되돌린다(-Leave 면 그 칸에 둔다).
$target = if ($Leave -ge 0) { $Leave } else { $orig }
[System.Windows.Forms.SendKeys]::SendWait('{HOME}')
Start-Sleep -Milliseconds 300
for ($v = 0; $v -lt $target; $v++) { [System.Windows.Forms.SendKeys]::SendWait('{RIGHT}'); Start-Sleep -Milliseconds 300 }
"restored=$([int]$range.Current.Value) label=$($valueP.Current.Value)"
[System.Windows.Forms.SendKeys]::SendWait('{ESC}')
Start-Sleep -Milliseconds 500

# 입력창의 표지를 지운다.
$box.SetFocus()
Start-Sleep -Milliseconds 200
[System.Windows.Forms.SendKeys]::SendWait('^a')
[System.Windows.Forms.SendKeys]::SendWait('{DELETE}')
Start-Sleep -Milliseconds 300
"box-after=[$(try { $box.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value } catch { '?' })]"
