# 진단 전용. 앞에 있는 창으로 가는 키(SendKeys) 없이 새 세션 입력창의 모델과 노력을 고를 수 있는지 잰다. Claude 창이 뒤에
# 있어도 되는지가 요점이다(SendKeys 는 앞에 있는 창으로 간다). 표지 글이 든 보내지 않은 새 세션 화면을 딥링크로 열고, 그 입력창 묶음의 버튼만 쓴다.
# 모델은 -Pick 으로 바꿨다가 처음 값으로 되돌리고, 노력은 -Effort 칸으로 옮겼다가 처음 칸으로 되돌린다. 끝에 표지를 값으로 지운다.
# 펼치기(ExpandCollapse)는 돌아오지 않은 적이 있어(일지 2026-09-21 open-session) 스레드 잡 안에서 8초 제한으로 부른다.
# 앱 2.37337.1.0 에서 노력은 `모델: <모델> <노력>` 버튼의 메뉴 안 `노력 <이름>` 하위 메뉴의 라디오 항목이고, 그 하위 메뉴는 펼치기로
# 열리지 않는다. 그래서 노력만은 하위 메뉴 항목에 포커스를 준 뒤 → 키를 PostMessage 로 Claude 창 핸들에 넣는다(키는 그 핸들로만 간다).
# 버튼의 모델과 노력은 이름이 아니라 자식 Text 로 읽는다. `최대` 칸의 버튼 이름에는 `3.5× 이상 사용량` 이 붙지만 Text 는 `최대` 다.
# -Background 를 주면 표지 화면을 연 뒤 메모장을 띄워 앞에 두고 조작한다(딥링크를 받은 앱은 창을 앞으로 올리므로 순서가
# 이렇다). 끝에 띄운 메모장만 닫는다. foreground-is-claude 줄이 조작 내내 False 여야 창이 뒤에 있는 조건을 잰 회차다.
# 알려진 결함: 시간을 넘긴 잡도 Remove-Job -Force 로 지워, 펼치기가 멈추면 8초 제한이 걸리지 않는다. 다시 쓸 때
# tools/open_session.ps1 의 Invoke-PatternTimed 처럼 고친다(.claude/rules/tools.md, 대기열 282).
# 쓰는 법: pwsh -NoProfile -File .scratch/harness/probes/composer_patterns.ps1 [-Pick 'Haiku 5.5'] [-Effort '높음'] [-Background]
param([string] $Pick = 'Haiku 5.5', [string] $Effort = '높음', [switch] $Background)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -TypeDefinition @'
using System; using System.Runtime.InteropServices;
public static class PatternProbe {
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
function Fg { "foreground-is-claude=$([int64][PatternProbe]::GetForegroundWindow() -eq [int64]$hwnd)" }
Fg

$marker = "pattern-probe-$(Get-Date -Format HHmmssfff)"
Start-Process ('claude://code/new?q=' + [uri]::EscapeDataString($marker))
$editCond = New-Object System.Windows.Automation.PropertyCondition($Auto::ControlTypeProperty, $Types::Edit)
$box = $null
for ($i = 0; $i -lt 40 -and -not $box; $i++) {
    Start-Sleep -Milliseconds 500
    $hits = @($win.FindAll($Scope::Descendants, $editCond) | Where-Object { try { $_.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value -eq $marker } catch { $false } })
    if ($hits.Count -eq 1) { $box = $hits[0] }
}
if (-not $box) { throw '표지가 든 입력창을 찾지 못했다.' }
"draft=$marker"
$pad = $null
if ($Background) { $pad = Start-Process notepad -PassThru; Start-Sleep -Milliseconds 1500 }
Fg

$walker = [System.Windows.Automation.TreeWalker]::ControlViewWalker
$buttonCond = New-Object System.Windows.Automation.PropertyCondition($Auto::ControlTypeProperty, $Types::Button)
$textCond = New-Object System.Windows.Automation.PropertyCondition($Auto::ControlTypeProperty, $Types::Text)
$radioCond = New-Object System.Windows.Automation.PropertyCondition($Auto::ControlTypeProperty, $Types::RadioButton)
$menuItemCond = New-Object System.Windows.Automation.PropertyCondition($Auto::ControlTypeProperty, $Types::MenuItem)
function Composer {
    $node = $box
    for ($i = 0; $i -lt 20; $i++) {
        $node = $walker.GetParent($node); if (-not $node) { return $null }
        $hits = @($node.FindAll($Scope::Descendants, $buttonCond) | Where-Object { try { $_.Current.Name.StartsWith('모델:') } catch { $false } })
        if ($hits.Count -eq 1) { return $hits[0] }
        if ($hits.Count -gt 1) { throw "'모델:' 버튼이 $($hits.Count)개다." }
    }
    return $null
}
# 버튼의 자식 Text 가운데 공백이 아닌 것. [모델, 노력] 이다.
function Texts { @((Composer).FindAll($Scope::Children, $textCond) | ForEach-Object { $_.Current.Name } | Where-Object { $_.Trim() }) }
function Show { "[$((Composer).Current.Name)] texts=[$((Texts) -join '|')]" }
function Patterns($el) { ($el.GetSupportedPatterns() | ForEach-Object { $_.ProgrammaticName -replace 'PatternIdentifiers.Pattern', '' }) -join ',' }
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
function Find-Radio([string] $name) { @($win.FindAll($Scope::Descendants, $radioCond) | Where-Object { $n = $_.Current.Name; $n -ceq $name -or $n.StartsWith("$name ") }) | Select-Object -First 1 }

# 모델
$modelButton = Composer
"model-button=$(Show) patterns=$(Patterns $modelButton)"
$orig = Texts
$origModel = $orig[0]
$origEffort = $orig[-1]
function State { try { "$((Composer).GetCurrentPattern([System.Windows.Automation.ExpandCollapsePattern]::Pattern).Current.ExpandCollapseState)" } catch { '?' } }
function Choose-Model([string] $name) {
    $e = Timed (Composer) 'expand'
    if ($e -ne 'ok') { return "expand=$e" }
    Start-Sleep -Milliseconds 800
    # 펼친 직후 창이 앞에 왔는지. 고르기 전이라 앞으로 올린 것이 펼치기인지 가른다.
    "  after-expand $(Fg)"
    $r = Find-Radio $name
    if (-not $r) { Timed (Composer) 'collapse' | Out-Null; return "no-item($name)" }
    $how = Timed $r 'select'
    Start-Sleep -Milliseconds 800
    $open = [bool](Find-Radio $name)
    if ($open) { Timed (Composer) 'collapse' | Out-Null }
    return "select=$how menu-open-after-select=$open"
}
"choose-$Pick=$(Choose-Model $Pick) button=$(Show)"
Fg
"choose-back-$origModel=$(Choose-Model $origModel) button=$(Show)"
Fg

# 노력
function Choose-Effort([string] $name) {
    $e = Timed (Composer) 'expand'
    if ($e -ne 'ok') { return "expand=$e" }
    Start-Sleep -Milliseconds 600
    $trigger = @($win.FindAll($Scope::Descendants, $menuItemCond) | Where-Object { try { $_.Current.Name.StartsWith('노력') } catch { $false } }) | Select-Object -First 1
    if (-not $trigger) { Timed (Composer) 'collapse' | Out-Null; return "no-trigger" }
    $trigger.SetFocus()
    Start-Sleep -Milliseconds 300
    $front = [int64][PatternProbe]::GetForegroundWindow() -eq [int64]$hwnd
    [PatternProbe]::PostMessage($hwnd, 0x0100, [IntPtr]0x27, [IntPtr]0x014D0001) | Out-Null
    [PatternProbe]::PostMessage($hwnd, 0x0101, [IntPtr]0x27, [IntPtr]([int64]0xC14D0001)) | Out-Null
    $r = $null
    for ($i = 0; $i -lt 10 -and -not $r; $i++) { Start-Sleep -Milliseconds 300; $r = Find-Radio $name }
    if (-not $r) { Timed (Composer) 'collapse' | Out-Null; return "submenu-not-opened(foreground-is-claude=$front)" }
    $how = Timed $r 'select'
    Start-Sleep -Milliseconds 800
    $open = [bool](Find-Radio $name)
    $modelState = State
    if ($open) { Timed $trigger 'collapse' | Out-Null }
    if ($modelState -eq 'Expanded') { Timed (Composer) 'collapse' | Out-Null }
    return "select=$how foreground-before-key=$front menu-open-after-select=$open model-menu-state-after=$modelState"
}
"choose-effort-$Effort=$(Choose-Effort $Effort) button=$(Show)"
Fg
"choose-effort-back-$origEffort=$(Choose-Effort $origEffort) button=$(Show)"
Fg

try { $box.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).SetValue(''); Start-Sleep -Milliseconds 300 } catch { "clear=실패 $($_.Exception.Message)" }
"box-after=[$(try { $box.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value.Trim() } catch { '?' })]"
Fg
if ($pad) { Stop-Process -Id $pad.Id -ErrorAction SilentlyContinue }
