# 진단 전용. 키 없이 접근성 패턴만으로 새 세션 입력창의 모델과 노력을 고를 수 있는지 잰다. Claude 창이 뒤에 있어도 되는지가
# 요점이다(키는 앞에 있는 창으로 간다). 표지 글이 든 보내지 않은 새 세션 화면을 딥링크로 열고, 그 입력창 묶음의 버튼만 쓴다.
# 모델은 -Pick 으로 바꿨다가 처음 값으로 되돌리고, 노력은 칸 -Step 으로 옮겼다가 처음 칸으로 되돌린다. 끝에 표지를 값으로 지운다.
# 펼치기(ExpandCollapse)는 돌아오지 않은 적이 있어(일지 2026-09-21 open-session) 스레드 잡 안에서 8초 제한으로 부른다.
# -Background 를 주면 표지 화면을 연 뒤 메모장을 띄워 앞에 두고 조작한다(딥링크를 받은 앱은 창을 앞으로 올리므로 순서가
# 이렇다). 끝에 띄운 메모장만 닫는다. foreground-is-claude 줄이 조작 내내 False 여야 창이 뒤에 있는 조건을 잰 회차다.
# 쓰는 법: pwsh -NoProfile -File .scratch/harness/probes/composer_patterns.ps1 [-Pick 'Haiku 5.5'] [-Step 2] [-Background]
param([string] $Pick = 'Haiku 5.5', [int] $Step = 2, [switch] $Background)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -TypeDefinition @'
using System; using System.Runtime.InteropServices;
public static class PatternProbe { [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow(); }
'@
$Auto = [System.Windows.Automation.AutomationElement]
$Scope = [System.Windows.Automation.TreeScope]
$Types = [System.Windows.Automation.ControlType]
$True_ = [System.Windows.Automation.Condition]::TrueCondition
$wins = @($Auto::RootElement.FindAll($Scope::Children, $True_) | Where-Object { $_.Current.Name -eq 'Claude' })
if ($wins.Count -ne 1) { throw "Claude 창이 $($wins.Count)개다." }
$win = $wins[0]
function Fg { "foreground-is-claude=$([int64][PatternProbe]::GetForegroundWindow() -eq [int64]$win.Current.NativeWindowHandle)" }
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
function Composer([string] $prefix) {
    $node = $box
    for ($i = 0; $i -lt 20; $i++) {
        $node = $walker.GetParent($node); if (-not $node) { return $null }
        $hits = @($node.FindAll($Scope::Descendants, $buttonCond) | Where-Object { try { $_.Current.Name.StartsWith($prefix) } catch { $false } })
        if ($hits.Count -eq 1) { return $hits[0] }
        if ($hits.Count -gt 1) { throw "'$prefix' 버튼이 $($hits.Count)개다." }
    }
    return $null
}
function Patterns($el) { ($el.GetSupportedPatterns() | ForEach-Object { $_.ProgrammaticName -replace 'PatternIdentifiers.Pattern', '' }) -join ',' }
function Expand-Timed($el, [string] $how) {
    $job = Start-ThreadJob -ArgumentList $el, $how -ScriptBlock {
        param($e, $h)
        $p = $e.GetCurrentPattern([System.Windows.Automation.ExpandCollapsePattern]::Pattern)
        if ($h -eq 'expand') { $p.Expand() } else { $p.Collapse() }
        'ok'
    }
    if (Wait-Job $job -Timeout 8) { $r = Receive-Job $job -ErrorAction SilentlyContinue -ErrorVariable err; Remove-Job $job -Force; if ($err) { return "error: $($err[0])" }; return $r }
    Remove-Job $job -Force; return 'timeout(8s)'
}

# 모델
$modelButton = Composer '모델:'
"model-button=[$($modelButton.Current.Name)] patterns=$(Patterns $modelButton)"
$origModel = $modelButton.Current.Name.Substring('모델:'.Length).Trim()
"expand=$(Expand-Timed $modelButton 'expand')"
Start-Sleep -Milliseconds 800
$radioCond = New-Object System.Windows.Automation.PropertyCondition($Auto::ControlTypeProperty, $Types::RadioButton)
$radios = @($win.FindAll($Scope::Descendants, $radioCond))
"radios=$($radios.Count)"
foreach ($r in $radios) { "  [$($r.Current.Name)] enabled=$($r.Current.IsEnabled) patterns=$(Patterns $r)" }
function Choose([string] $name) {
    $r = @($win.FindAll($Scope::Descendants, $radioCond) | Where-Object { $n = $_.Current.Name; $n -ceq $name -or $n.StartsWith("$name ") }) | Select-Object -First 1
    if (-not $r) { return "no-item($name)" }
    try { $r.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern).Select(); return 'select' } catch {}
    try { $r.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke(); return 'invoke' } catch {}
    return 'no-pattern'
}
if ($radios.Count -gt 0) {
    "choose-$Pick=$(Choose $Pick)"
    Start-Sleep -Milliseconds 800
    "model-button-after=[$((Composer '모델:').Current.Name)]"
    # 창에는 모델 메뉴 밖의 라디오 버튼(`Claude`, `Code`)도 있다. 메뉴가 열렸는지는 처음 모델 이름의 항목이 있는지로 본다.
    $menuOpen = [bool](@($win.FindAll($Scope::Descendants, $radioCond) | Where-Object { $_.Current.Name.StartsWith($origModel) }).Count)
    "menu-open-after-select=$menuOpen"
    if (-not $menuOpen) { "expand-again=$(Expand-Timed (Composer '모델:') 'expand')"; Start-Sleep -Milliseconds 800 }
    "choose-back-$origModel=$(Choose $origModel)"
    Start-Sleep -Milliseconds 800
    "model-button-restored=[$((Composer '모델:').Current.Name)]"
}
Fg

# 노력
$effortButton = Composer '노력:'
"effort-button=[$($effortButton.Current.Name)] patterns=$(Patterns $effortButton)"
"expand=$(Expand-Timed $effortButton 'expand')"
Start-Sleep -Milliseconds 800
$sliderCond = New-Object System.Windows.Automation.PropertyCondition($Auto::ControlTypeProperty, $Types::Slider)
$slider = $win.FindFirst($Scope::Descendants, $sliderCond)
if ($slider) {
    $range = $slider.GetCurrentPattern([System.Windows.Automation.RangeValuePattern]::Pattern)
    $orig = [int]$range.Current.Value
    "slider orig=$orig"
    try { $range.SetValue($Step); Start-Sleep -Milliseconds 600; "setvalue=$Step got=$([int]$range.Current.Value) button=[$((Composer '노력:').Current.Name)]" } catch { "setvalue=실패 $($_.Exception.Message)" }
    try { $range.SetValue($orig); Start-Sleep -Milliseconds 600; "setvalue-back=$orig got=$([int]$range.Current.Value) button=[$((Composer '노력:').Current.Name)]" } catch { "setvalue-back=실패 $($_.Exception.Message)" }
    "collapse=$(Expand-Timed (Composer '노력:') 'collapse')"
} else { 'slider=없음(펼치기가 메뉴를 열지 못했다)' }
Fg

try { $box.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).SetValue(''); Start-Sleep -Milliseconds 300 } catch { "clear=실패 $($_.Exception.Message)" }
"box-after=[$(try { $box.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value.Trim() } catch { '?' })]"
Fg
if ($pad) { Stop-Process -Id $pad.Id -ErrorAction SilentlyContinue }
