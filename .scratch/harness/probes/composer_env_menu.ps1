# 진단 전용(harness 티켓 open-session-selects-repo-folder). 표지 글이 든 새 세션 화면을 딥링크로 열어, 입력창 묶음의 `환경: <이름>`
# 버튼을 펼친 메뉴에 어떤 항목이 생기는지 찍고 접는다. 끝에 표지를 값으로 지운다. 쏘기 전에 화면을 깨운다.
# 찍는 것: 펼치기 전 입력창 묶음의 버튼, 펼치기 뒤 새로 생긴 요소의 종류·이름·활성 여부·지원 패턴·선택 여부. 이름에 -Leaf 가 든
# 요소는 hit= 줄로 다시 찍는다(저장소 폴더가 항목으로 나오는지). -Pick 이 없을 때만 아무것도 고르지 않는다. -Pick 은 앱의 마지막 폴더를 바꾸고
# 되돌리지 않는다(되돌리려면 원래 환경으로 -Pick 을 한 번 더 돌린다).
# 측정의 표지: draft= 줄(표지 입력창을 찾았다), env-button= 줄(환경 버튼을 찾았다), expand=ok(펼치기가 돌아왔다). 앞의 둘이 없으면 그 자리에서,
# expand 가 ok 가 아니면 끝에서, -Pick 항목을 찾지 못했거나 고르기(select)가 ok 가 아닐 때도 끝에서 `측정 아님` 줄을 찍고 1로 끝난다. closed= 줄은 접은 뒤 남은 새 요소 수를
# 찍는 관찰이고 판정하지 않는다. hit= 줄이 없으면 2로 끝난다(저장소 폴더 항목을 찾지 못했다).
# 펼치기는 스레드 잡 안에서 8초 제한으로 부르고, 시간을 넘긴 잡은 지우지 않고 센 뒤 끝에 프로세스를 끝낸다(.claude/rules/tools.md).
# 쓰는 법: pwsh -NoProfile -File .scratch/harness/probes/composer_env_menu.ps1 -Leaf <저장소 폴더 이름> [-Invoke]
#   -Invoke: 펼치기 패턴이 없을 때 Invoke 로 연다.
#   -Pick <환경 이름>: 펼친 메뉴에서 그 환경을 고른다(SelectionItem). 고르기 전과 뒤의 화면 폴더를 pick-before=·pick-after= 로 찍는다.
param([Parameter(Mandatory)] [string] $Leaf, [switch] $Invoke, [string] $Pick)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; public static class EnvProbeWake { [DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint f); }'
Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; public static class EnvProbeKeys { [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr h, uint m, IntPtr w, IntPtr l); }'
$Auto = [System.Windows.Automation.AutomationElement]
$Scope = [System.Windows.Automation.TreeScope]
$Types = [System.Windows.Automation.ControlType]
$True_ = [System.Windows.Automation.Condition]::TrueCondition
$script:Hung = 0

$wins = @($Auto::RootElement.FindAll($Scope::Children, $True_) | Where-Object { $_.Current.Name -eq 'Claude' })
if ($wins.Count -ne 1) { throw "Claude 창이 $($wins.Count)개다." }
$win = $wins[0]
$marker = "env-probe-$(Get-Date -Format HHmmssfff)"
"wake=$([EnvProbeWake]::SetThreadExecutionState(0x3))"
Start-Sleep -Seconds 2
Start-Process ('claude://code/new?q=' + [uri]::EscapeDataString($marker))
$editCond = New-Object System.Windows.Automation.PropertyCondition($Auto::ControlTypeProperty, $Types::Edit)
$box = $null
for ($i = 0; $i -lt 40 -and -not $box; $i++) {
    Start-Sleep -Milliseconds 500
    $hits = @($win.FindAll($Scope::Descendants, $editCond) | Where-Object { try { $_.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value -eq $marker } catch { $false } })
    if ($hits.Count -eq 1) { $box = $hits[0] }
}
if (-not $box) { '측정 아님: 표지가 든 입력창을 찾지 못했다'; exit 1 }
"draft=$marker"

function Patterns($el) { ($el.GetSupportedPatterns() | ForEach-Object { $_.ProgrammaticName -replace 'PatternIdentifiers.Pattern', '' }) -join ',' }
function Snapshot {
    $map = @{}
    foreach ($el in @($win.FindAll($Scope::Descendants, $True_))) { try { $map[($el.GetRuntimeId() -join '.')] = $el } catch {} }
    return $map
}
function Timed($el, [string] $how) {
    $job = Start-ThreadJob -ArgumentList $el, $how -ScriptBlock {
        param($e, $h)
        switch ($h) {
            'expand' { $e.GetCurrentPattern([System.Windows.Automation.ExpandCollapsePattern]::Pattern).Expand() }
            'collapse' { $e.GetCurrentPattern([System.Windows.Automation.ExpandCollapsePattern]::Pattern).Collapse() }
            'invoke' { $e.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke() }
            'select' { $e.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern).Select() }
        }
        'ok'
    }
    if (-not (Wait-Job $job -Timeout 8)) { $script:Hung++; return "$how-hung" }
    try {
        $out = Receive-Job $job -ErrorAction SilentlyContinue -ErrorVariable failed
        if ($failed) { return "$how-error: $($failed[0])" }
        return $out
    } finally { Remove-Job $job -Force }
}
function State($el) { try { "$($el.GetCurrentPattern([System.Windows.Automation.ExpandCollapsePattern]::Pattern).Current.ExpandCollapseState)" } catch { '?' } }

$walker = [System.Windows.Automation.TreeWalker]::ControlViewWalker
$buttonCond = New-Object System.Windows.Automation.PropertyCondition($Auto::ControlTypeProperty, $Types::Button)
$textCond = New-Object System.Windows.Automation.PropertyCondition($Auto::ControlTypeProperty, $Types::Text)
$node = $box; $group = $null; $envButton = $null
for ($i = 0; $i -lt 20 -and -not $group; $i++) {
    $node = $walker.GetParent($node); if (-not $node) { break }
    $model = @($node.FindAll($Scope::Descendants, $buttonCond) | Where-Object { try { $_.Current.Name.StartsWith('모델:') } catch { $false } })
    if ($model.Count -eq 0) { continue }
    $group = $node
    $envs = @($node.FindAll($Scope::Descendants, $buttonCond) | Where-Object { try { $_.Current.Name.StartsWith('환경:') } catch { $false } })
    "env-buttons=$($envs.Count)"
    if ($envs.Count -eq 1) { $envButton = $envs[0] }
}
if (-not $group) { '측정 아님: 모델 버튼이 든 입력창 묶음을 찾지 못했다'; exit 1 }
'--- 입력창 묶음의 버튼 ---'
foreach ($b in @($group.FindAll($Scope::Descendants, $buttonCond))) { "  [$($b.Current.Name)] patterns=$(Patterns $b)" }
'--- 입력창 묶음의 드라이브 경로 글 ---'
foreach ($t in @($group.FindAll($Scope::Descendants, $textCond))) { try { if ($t.Current.Name -match '^[A-Za-z]:\\') { "  [$($t.Current.Name)]" } } catch {} }
if (-not $envButton) {
    try { $box.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).SetValue('') } catch {}
    '측정 아님: 환경 버튼이 하나가 아니다'; exit 1
}
"env-button=[$($envButton.Current.Name)] patterns=$(Patterns $envButton) state=$(State $envButton)"

$before = Snapshot
$opened = if ($Invoke) { Timed $envButton 'invoke' } else { Timed $envButton 'expand' }
"expand=$opened"
Start-Sleep -Milliseconds 1200
"state-after=$(State $envButton)"
'--- 환경 메뉴를 펼친 뒤 새로 생긴 요소 ---'
$after = Snapshot
$found = 0
foreach ($key in $after.Keys) {
    if ($before.ContainsKey($key)) { continue }
    $el = $after[$key]
    try {
        $sel = try { " selected=$($el.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern).Current.IsSelected)" } catch { '' }
        $line = "  $($el.Current.ControlType.ProgrammaticName -replace 'ControlType\.','')|$($el.Current.Name)|enabled=$($el.Current.IsEnabled)|patterns=$(Patterns $el)$sel"
        $line
        if ($el.Current.Name.Contains($Leaf)) { "hit=$line"; $found++ }
    } catch {}
}
function Get-EditValue($el) { try { return $el.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value } catch { return '(읽지 못함)' } }
function Read-Shown {
    $names = @($group.FindAll($Scope::Descendants, $textCond) | ForEach-Object { try { $_.Current.Name } catch { $null } })
    return @($names | Where-Object { $_ -cmatch '^[A-Za-z]:\\' -and $_ -notmatch '[\r\n]' } | Select-Object -Unique) -join ', '
}
if ($Pick) {
    # 고르면 메뉴가 스스로 닫히는지, 화면의 폴더가 따라 바뀌는지 본다.
    $item = @($after.Values | Where-Object { try { $_.Current.ControlType -eq $Types::RadioButton -and $_.Current.Name.StartsWith("$Pick ,") } catch { $false } }) | Select-Object -First 1
    if (-not $item) { "pick=항목 없음 [$Pick]"; $pickFailed = $true }
    else {
        "pick-before=$(Read-Shown)"
        $picked = Timed $item 'select'
        "pick=$picked"
        if ($picked -ne 'ok') { $pickFailed = $true }
        for ($i = 0; $i -lt 10; $i++) { Start-Sleep -Milliseconds 500; if ((Read-Shown) -and (State $envButton) -ne 'Expanded') { break } }
        "pick-after=$(Read-Shown) env-button=[$($envButton.Current.Name)] state=$(State $envButton)"
        # 고른 뒤에도 같은 입력창 요소에 표지 글이 남아 있는지, 표지가 든 입력창이 하나 그대로인지 본다(보내기 전 요소를 다시 찾아야 하는지).
        "pick-box-value=[$(Get-EditValue $box)]"
        $again = @($win.FindAll($Scope::Descendants, $editCond) | Where-Object { try { $_.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value -eq $marker } catch { $false } })
        "pick-box-found=$($again.Count) same-element=$(if ($again.Count -eq 1) { ($again[0].GetRuntimeId() -join '.') -eq ($box.GetRuntimeId() -join '.') } else { '?' })"
    }
}
# 접는다. 패턴으로 접히지 않으면 Esc 를 Claude 창 핸들에 넣는다(앞에 있는 창으로 가는 키는 쓰지 않는다).
if (-not $Pick -or $pickFailed) { $collapsed = Timed $envButton 'collapse'; "collapse=$collapsed" }
Start-Sleep -Milliseconds 600
if ((State $envButton) -eq 'Expanded') {
    $h = [IntPtr]$win.Current.NativeWindowHandle
    "esc=$([EnvProbeKeys]::PostMessage($h, 0x0100, [IntPtr]0x1B, [IntPtr]0x00010001))"
    Start-Sleep -Milliseconds 600
}
$closed = Snapshot
"closed=남은 새 요소 $(@($closed.Keys | Where-Object { -not $before.ContainsKey($_) }).Count) 개"
try { $box.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).SetValue(''); Start-Sleep -Milliseconds 300 } catch { "clear=실패 $($_.Exception.Message)" }
"box-after=[$(try { $box.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value.Trim() } catch { '?' })]"
"hits=$found"
$code = 0
if ($opened -ne 'ok') { "측정 아님: 펼치기가 ok 로 돌아오지 않았다($opened)"; $code = 1 }
elseif ($Pick -and $pickFailed) { "측정 아님: -Pick 항목을 찾지 못했거나 고르지 못했다 [$Pick]"; $code = 1 }
elseif ($found -eq 0) { $code = 2 }
if ($script:Hung -gt 0) { [Environment]::Exit($code) }
exit $code
