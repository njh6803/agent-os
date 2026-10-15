# 진단 전용. 표지 글이 든 새 세션 화면을 딥링크로 열어 그 입력창 묶음의 버튼을 찍고, `모델:` 버튼의 메뉴를 펼쳐 새로 생긴 요소를
# 찍은 뒤 접는다. -Effort 면 그 메뉴 안 `노력 <이름>` 하위 메뉴도 열어 찍는다. 아무것도 고르지 않는다. 끝에 표지를 값으로 지운다.
# 펼치기는 접근성 패턴으로 한다(스레드 잡 안에서 8초 제한). 노력 하위 메뉴는 펼치기 패턴으로 열리지 않아(state 줄이 Collapsed 로
# 남는다) 그 항목에 포커스를 준 뒤 → 키를 PostMessage 로 Claude 창 핸들에 넣는다. 키는 앞에 있는 창이 아니라 그 핸들로만 간다.
# 표지 입력창에서 위로 올라가 그 묶음의 버튼만 쓰므로 분할 보기의 다른 패널은 건드리지 않는다.
# -Behind 면 노력 항목에 포커스를 준 뒤 메모장을 띄워 앞에 두고 키를 넣는다. Claude 창이 뒤에 있을 때 그 키가 하위 메뉴를 여는지
# 본다. 키를 넣기 전 줄이 foreground-is-claude=False 인 회차만 그 조건의 측정이고, 아니면 1로 끝난다. 끝에 띄운 메모장만 닫는다.
# PostMessage 는 받는 창의 메시지 큐에 넣는 Win32 호출이라 메모장에 닿는지는 재지 않는다.
# 쓰는 법: pwsh -NoProfile -File .scratch/harness/probes/composer_menu_tree.ps1 [-Effort [-Behind]]
param([switch] $Effort, [switch] $Behind)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -TypeDefinition @'
using System; using System.Runtime.InteropServices;
public static class MenuProbe {
    [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
    [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr h, uint m, IntPtr w, IntPtr l);
}
'@
$Auto = [System.Windows.Automation.AutomationElement]
$Scope = [System.Windows.Automation.TreeScope]
$Types = [System.Windows.Automation.ControlType]
$True_ = [System.Windows.Automation.Condition]::TrueCondition

$wins = @($Auto::RootElement.FindAll($Scope::Children, $True_) | Where-Object { $_.Current.Name -eq 'Claude' })
if ($wins.Count -ne 1) { throw "Claude 창이 $($wins.Count)개다." }
$win = $wins[0]
$hwnd = [IntPtr]$win.Current.NativeWindowHandle
$marker = "menu-probe-$(Get-Date -Format HHmmssfff)"
Start-Process ('claude://code/new?q=' + [uri]::EscapeDataString($marker))
$editCond = New-Object System.Windows.Automation.PropertyCondition($Auto::ControlTypeProperty, $Types::Edit)
$box = $null
for ($i = 0; $i -lt 40 -and -not $box; $i++) {
    Start-Sleep -Milliseconds 500
    $hits = @($win.FindAll($Scope::Descendants, $editCond) | Where-Object { try { $_.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value -eq $marker } catch { $false } })
    if ($hits.Count -eq 1) { $box = $hits[0] }
}
if (-not $box) { throw '표지가 든 입력창을 찾지 못했다. 아무것도 열지 않았다.' }
"draft=$marker"

function Patterns($el) { ($el.GetSupportedPatterns() | ForEach-Object { $_.ProgrammaticName -replace 'PatternIdentifiers.Pattern', '' }) -join ',' }
function Snapshot {
    $map = @{}
    foreach ($el in @($win.FindAll($Scope::Descendants, $True_))) { try { $map[($el.GetRuntimeId() -join '.')] = $el } catch {} }
    return $map
}
function Show-New($before) {
    $after = Snapshot
    foreach ($key in $after.Keys) {
        if ($before.ContainsKey($key)) { continue }
        $el = $after[$key]
        try {
            $sel = try { " selected=$($el.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern).Current.IsSelected)" } catch { '' }
            "  $($el.Current.ControlType.ProgrammaticName -replace 'ControlType\.','')|$($el.Current.Name)|enabled=$($el.Current.IsEnabled)|patterns=$(Patterns $el)$sel"
        } catch {}
    }
}
function Timed($el, [string] $how) {
    $job = Start-ThreadJob -ArgumentList $el, $how -ScriptBlock {
        param($e, $h)
        $p = $e.GetCurrentPattern([System.Windows.Automation.ExpandCollapsePattern]::Pattern)
        if ($h -eq 'expand') { $p.Expand() } else { $p.Collapse() }
        'ok'
    }
    if (Wait-Job $job -Timeout 8) { $r = Receive-Job $job -ErrorAction SilentlyContinue -ErrorVariable err; Remove-Job $job -Force; if ($err) { return "error: $($err[0])" }; return $r }
    Remove-Job $job -Force; return 'timeout(8s)'
}
function State($el) { try { "$($el.GetCurrentPattern([System.Windows.Automation.ExpandCollapsePattern]::Pattern).Current.ExpandCollapseState)" } catch { '?' } }

$walker = [System.Windows.Automation.TreeWalker]::ControlViewWalker
$buttonCond = New-Object System.Windows.Automation.PropertyCondition($Auto::ControlTypeProperty, $Types::Button)
$textCond = New-Object System.Windows.Automation.PropertyCondition($Auto::ControlTypeProperty, $Types::Text)
$node = $box; $group = $null; $modelButton = $null
for ($i = 0; $i -lt 20 -and -not $group; $i++) {
    $node = $walker.GetParent($node); if (-not $node) { break }
    $hits = @($node.FindAll($Scope::Descendants, $buttonCond) | Where-Object { try { $_.Current.Name.StartsWith('모델:') } catch { $false } })
    if ($hits.Count -gt 1) { throw "표지 입력창 가까이의 모델 버튼이 $($hits.Count)개다." }
    if ($hits.Count -eq 1) { $group = $node; $modelButton = $hits[0] }
}
if (-not $group) { throw '표지 입력창 가까이에 모델 버튼이 없다.' }
'--- 입력창 묶음의 버튼 ---'
foreach ($b in @($group.FindAll($Scope::Descendants, $buttonCond))) { "  [$($b.Current.Name)] patterns=$(Patterns $b)" }
"model-button texts=[$(@($modelButton.FindAll($Scope::Children, $textCond) | ForEach-Object { $_.Current.Name }) -join '|')]"

$before = Snapshot
"expand=$(Timed $modelButton 'expand')"
Start-Sleep -Milliseconds 1200
'--- 모델 메뉴를 펼친 뒤 새로 생긴 요소 ---'
Show-New $before

if ($Effort) {
    $menuItemCond = New-Object System.Windows.Automation.PropertyCondition($Auto::ControlTypeProperty, $Types::MenuItem)
    $trigger = @($win.FindAll($Scope::Descendants, $menuItemCond) | Where-Object { try { $_.Current.Name.StartsWith('노력') } catch { $false } }) | Select-Object -First 1
    if (-not $trigger) { "effort-trigger=없음" } else {
        "effort-trigger=[$($trigger.Current.Name)] state=$(State $trigger)"
        $before2 = Snapshot
        "expand-pattern=$(Timed $trigger 'expand')"
        Start-Sleep -Milliseconds 1200
        # 키를 넣기 전의 새 요소 수. 라디오 항목이 펼치기 패턴과 → 키 가운데 어느 쪽에서 생겼는지 가른다.
        $afterExpand = Snapshot
        "after expand-pattern state=$(State $trigger) new=$(@($afterExpand.Keys | Where-Object { -not $before2.ContainsKey($_) }).Count)"
        $trigger.SetFocus()
        Start-Sleep -Milliseconds 300
        if ($Behind) { $pad = Start-Process notepad -PassThru; Start-Sleep -Milliseconds 1500 }
        $front = [int64][MenuProbe]::GetForegroundWindow() -eq [int64]$hwnd
        "foreground-is-claude=$front"
        if ($Behind -and $front) { $notMeasured = $true; '측정 아님: 메모장이 앞에 오지 않았다' }
        "post-key down=$([MenuProbe]::PostMessage($hwnd, 0x0100, [IntPtr]0x27, [IntPtr]0x014D0001)) up=$([MenuProbe]::PostMessage($hwnd, 0x0101, [IntPtr]0x27, [IntPtr]([int64]0xC14D0001)))"
        Start-Sleep -Milliseconds 1200
        "after post-key state=$(State $trigger)"
        '--- 노력 하위 메뉴를 연 뒤 새로 생긴 요소 ---'
        Show-New $before2
        if ((State $trigger) -eq 'Expanded') { "collapse-effort=$(Timed $trigger 'collapse')"; Start-Sleep -Milliseconds 400 }
    }
}
"collapse=$(Timed $modelButton 'collapse')"
Start-Sleep -Milliseconds 600
$closed = Snapshot
"closed: 남은 새 요소 $(@($closed.Keys | Where-Object { -not $before.ContainsKey($_) }).Count) 개"
try { $box.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).SetValue(''); Start-Sleep -Milliseconds 300 } catch { "clear=실패 $($_.Exception.Message)" }
"box-after=[$(try { $box.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value.Trim() } catch { '?' })]"
if ($pad) { Stop-Process -Id $pad.Id -ErrorAction SilentlyContinue }
if ($notMeasured) { exit 1 }
