# 진단 전용. 보내지 않은 새 세션 화면의 입력창에서 노력 칸을 하나씩 골라 버튼 이름을 읽고 처음 칸으로 되돌린다.
# 세션에 묶인 입력창을 건드리지 않으려고, 딥링크로 표지 글이 든 새 세션 화면을 열고 그 표지가 든 입력창이
# 하나뿐일 때만 움직인다. 보내지 않는다. 끝나면 입력창의 표지를 값으로 지운다(화면은 사람이 다른 세션을 고르면 닫힌다).
# 앱 2.37337.1.0 에서 노력은 따로 된 버튼이 아니라 `모델: <모델> <노력>` 버튼의 메뉴 안 `노력 <이름>` 하위 메뉴의 라디오 항목이다.
# 하위 메뉴는 펼치기 패턴으로 열리지 않아(상태가 Collapsed 로 남는다) 그 항목에 포커스를 준 뒤 → 키를 PostMessage 로 Claude 창
# 핸들에 넣는다. 키는 앞에 있는 창이 아니라 그 핸들로만 간다. Claude 창이 앞에 없으면 열리지 않는다(post_key 줄이 실패를 적는다).
# `Ultracode` 칸은 레벨이 아니라 고르지 않는다(처음 칸이 그것이면 되돌릴 때만 고른다).
# 쓰는 법: pwsh -NoProfile -File .scratch/harness/probes/composer_effort_labels.ps1 [-Leave <이름>]
# -Leave 를 주면 처음 칸 대신 그 이름의 칸에 두고 닫는다. 보내지 않은 화면에서 고른 값이 다음 새 세션 화면의 기본값으로 남는지 볼 때 쓴다.
param([string] $Leave)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -TypeDefinition @'
using System; using System.Runtime.InteropServices;
public static class EffortProbe {
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr h, uint m, IntPtr w, IntPtr l);
}
'@
$Auto = [System.Windows.Automation.AutomationElement]
$Scope = [System.Windows.Automation.TreeScope]
$Types = [System.Windows.Automation.ControlType]
$True_ = [System.Windows.Automation.Condition]::TrueCondition

$marker = "effort-probe-$(Get-Date -Format HHmmssfff)"
$wins = @($Auto::RootElement.FindAll($Scope::Children, $True_) | Where-Object { $_.Current.Name -eq 'Claude' })
if ($wins.Count -ne 1) { throw "Claude 창이 $($wins.Count)개다." }
$win = $wins[0]
$hwnd = [IntPtr]$win.Current.NativeWindowHandle

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
$textCond = New-Object System.Windows.Automation.PropertyCondition($Auto::ControlTypeProperty, $Types::Text)
$radioCond = New-Object System.Windows.Automation.PropertyCondition($Auto::ControlTypeProperty, $Types::RadioButton)
$menuItemCond = New-Object System.Windows.Automation.PropertyCondition($Auto::ControlTypeProperty, $Types::MenuItem)
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
function Describe-Button {
    $b = @(Find-Prefixed '모델:')
    if ($b.Count -ne 1) { return "버튼 $($b.Count)개" }
    $texts = @($b[0].FindAll($Scope::Children, $textCond) | ForEach-Object { $_.Current.Name })
    return "[$($b[0].Current.Name)] texts=[$($texts -join '|')]"
}
function Timed($el, [string] $how) {
    $job = Start-ThreadJob -ArgumentList $el, $how -ScriptBlock {
        param($e, $h)
        switch ($h) {
            'expand' { $e.GetCurrentPattern([System.Windows.Automation.ExpandCollapsePattern]::Pattern).Expand() }
            'collapse' { $e.GetCurrentPattern([System.Windows.Automation.ExpandCollapsePattern]::Pattern).Collapse() }
            'select' { $e.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern).Select() }
        }
        'ok'
    }
    if (Wait-Job $job -Timeout 8) { $r = Receive-Job $job -ErrorAction SilentlyContinue -ErrorVariable err; Remove-Job $job -Force; if ($err) { return "error: $($err[0])" }; return $r }
    Remove-Job $job -Force; return 'timeout(8s)'
}
$effortNames = '^(낮음|중간|높음|엑스트라|최대|Ultracode)( |$)'
function Get-EffortItems { @($win.FindAll($Scope::Descendants, $radioCond) | Where-Object { try { $_.Current.Name -match $effortNames } catch { $false } }) }
# 모델 메뉴를 펼치고 노력 하위 메뉴를 연다. 열린 노력 항목을 돌려준다.
function Open-EffortMenu {
    $button = @(Find-Prefixed '모델:')
    if ($button.Count -ne 1) { throw "표지 입력창 가까이의 모델 버튼이 $($button.Count)개다." }
    $expanded = Timed $button[0] 'expand'
    if ($expanded -ne 'ok') { throw "모델 메뉴를 펼치지 못했다($expanded)." }
    Start-Sleep -Milliseconds 600
    $trigger = @($win.FindAll($Scope::Descendants, $menuItemCond) | Where-Object { try { $_.Current.Name.StartsWith('노력') } catch { $false } }) | Select-Object -First 1
    if (-not $trigger) { throw "모델 메뉴에 '노력' 항목이 없다." }
    $trigger.SetFocus()
    Start-Sleep -Milliseconds 300
    $front = [int64][EffortProbe]::GetForegroundWindow() -eq [int64]$hwnd
    $down = [EffortProbe]::PostMessage($hwnd, 0x0100, [IntPtr]0x27, [IntPtr]0x014D0001)
    $up = [EffortProbe]::PostMessage($hwnd, 0x0101, [IntPtr]0x27, [IntPtr]([int64]0xC14D0001))
    for ($i = 0; $i -lt 10; $i++) {
        Start-Sleep -Milliseconds 300
        $items = Get-EffortItems
        if ($items.Count -gt 0) { return [pscustomobject]@{ Button = $button[0]; Trigger = $trigger; Items = $items } }
    }
    Timed $button[0] 'collapse' | Out-Null
    throw "노력 하위 메뉴가 열리지 않았다(post_key down=$down up=$up foreground-is-claude=$front)."
}
function Close-Menus($opened) {
    if ((Get-EffortItems).Count -gt 0) { Timed $opened.Trigger 'collapse' | Out-Null; Start-Sleep -Milliseconds 300 }
    try { $state = $opened.Button.GetCurrentPattern([System.Windows.Automation.ExpandCollapsePattern]::Pattern).Current.ExpandCollapseState } catch { $state = '?' }
    if ("$state" -eq 'Expanded') { Timed $opened.Button 'collapse' | Out-Null; Start-Sleep -Milliseconds 300 }
}
function Select-Effort([string] $name) {
    $opened = Open-EffortMenu
    $item = $opened.Items | Where-Object { $_.Current.Name -ceq $name } | Select-Object -First 1
    if (-not $item) { Close-Menus $opened; return "없음($name)" }
    $how = Timed $item 'select'
    Start-Sleep -Milliseconds 800
    $menuLeft = (Get-EffortItems).Count -gt 0
    # 하위 메뉴 항목이 사라진 것과 모델 메뉴가 닫힌 것은 다르다. 모델 버튼의 상태를 따로 찍는다.
    $modelState = try { "$($opened.Button.GetCurrentPattern([System.Windows.Automation.ExpandCollapsePattern]::Pattern).Current.ExpandCollapseState)" } catch { '?' }
    Close-Menus $opened
    return "select=$how effort-menu-open-after=$menuLeft model-menu-state-after=$modelState button=$(Describe-Button)"
}

"new-session-defaults button=$(Describe-Button)"
$opened = Open-EffortMenu
$items = @($opened.Items | ForEach-Object {
    $sel = try { $_.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern).Current.IsSelected } catch { '?' }
    [pscustomobject]@{ Name = $_.Current.Name; Selected = $sel }
})
"items=[$(($items | ForEach-Object { "$($_.Name)$(if ($_.Selected -eq $true) { '*' })" }) -join ' / ')]"
Close-Menus $opened
$orig = @($items | Where-Object { $_.Selected -eq $true } | ForEach-Object { $_.Name })
if ($orig.Count -ne 1) { throw "고른 노력 칸이 $($orig.Count)개다. 움직이지 않았다." }
"orig=$($orig[0])"

foreach ($it in $items) {
    if ($it.Name -match '^Ultracode') { "skip=$($it.Name)(레벨이 아니다)"; continue }
    "$($it.Name): $(Select-Effort $it.Name)"
}
$target = if ($Leave) { @($items | Where-Object { $_.Name -ceq $Leave -or $_.Name.StartsWith("$Leave ") } | ForEach-Object { $_.Name })[0] } else { $orig[0] }
if (-not $target) { throw "-Leave '$Leave' 칸이 없다. 마지막으로 고른 칸에 남았다." }
"restored=$target $(Select-Effort $target)"

try { $box.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).SetValue(''); Start-Sleep -Milliseconds 300 } catch { "clear=실패 $($_.Exception.Message)" }
"box-after=[$(try { $box.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value.Trim() } catch { '?' })]"
