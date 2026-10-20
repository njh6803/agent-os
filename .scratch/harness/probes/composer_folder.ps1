# 진단 전용(대기열 378). 표지 글이 든 새 세션 화면을 딥링크로 열어, 그 화면이 어느 폴더에서 열리는지를 접근성 트리의 어디에
# 보이는지 찍는다. 표지 입력창에서 위로 올라가며 층마다 새로 보이는 버튼·글·하이퍼링크·메뉴 항목의 종류, 이름, 도움말,
# 자식 Text 를 찍고, 그 가운데 이름·도움말·자식 Text 에 -Leaf(폴더 이름)나 드라이브 경로가 든 것을 hit= 줄로 다시 찍는다.
# 아무것도 누르거나 고르지 않는다. 끝에 표지를 값으로 지운다. 쏘기 전에 화면을 깨운다(tools/open_session.ps1 의 Wake-Display).
# 사람이 40분 넘게 자리를 비운 2026-10-20 에 깨우지 않은 첫 두 회차는 20초 안에 표지 입력창이 생기지 않았고, 깨운 셋째 회차는
# 바로 생겼다.
# 측정의 표지: draft= 줄(표지 입력창을 찾았다)과 group= 줄(모델 버튼이 든 입력창 묶음을 찾았다). 둘 중 하나가 없으면 측정이
# 아니고 1로 끝난다. hit= 줄이 없으면 2로 끝난다(폴더를 이름으로 보이는 요소를 찾지 못했다).
# 쓰는 법: pwsh -NoProfile -File .scratch/harness/probes/composer_folder.ps1 -Leaf <앱의 마지막 폴더 이름> [-Levels 6]
param([Parameter(Mandatory)] [string] $Leaf, [int] $Levels = 6)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; public static class FolderProbeWake { [DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint f); }'
$Auto = [System.Windows.Automation.AutomationElement]
$Scope = [System.Windows.Automation.TreeScope]
$Types = [System.Windows.Automation.ControlType]
$True_ = [System.Windows.Automation.Condition]::TrueCondition

$wins = @($Auto::RootElement.FindAll($Scope::Children, $True_) | Where-Object { $_.Current.Name -eq 'Claude' })
if ($wins.Count -ne 1) { throw "Claude 창이 $($wins.Count)개다." }
$win = $wins[0]
$marker = "folder-probe-$(Get-Date -Format HHmmssfff)"
# ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED. 실패하면 0 이다.
"wake=$([FolderProbeWake]::SetThreadExecutionState(0x3))"
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

$textCond = New-Object System.Windows.Automation.PropertyCondition($Auto::ControlTypeProperty, $Types::Text)
$kinds = @($Types::Button, $Types::Text, $Types::Hyperlink, $Types::MenuItem, $Types::ComboBox, $Types::SplitButton)
function Describe($el) {
    $c = $el.Current
    $children = @($el.FindAll($Scope::Children, $textCond) | ForEach-Object { $_.Current.Name } | Where-Object { $_ })
    return [pscustomobject]@{
        Kind = $c.ControlType.ProgrammaticName -replace 'ControlType\.', ''
        Name = $c.Name
        Help = $c.HelpText
        Texts = $children -join '|'
    }
}

$walker = [System.Windows.Automation.TreeWalker]::ControlViewWalker
$seen = @{}
$node = $box
$group = $false
$found = 0
for ($level = 1; $level -le 20 -and $node; $level++) {
    $node = $walker.GetParent($node)
    if (-not $node) { break }
    $items = @($node.FindAll($Scope::Descendants, $True_) | Where-Object { try { $kinds -contains $_.Current.ControlType } catch { $false } })
    if (-not $group -and @($items | Where-Object { try { $_.Current.ControlType -eq $Types::Button -and $_.Current.Name.StartsWith('모델:') } catch { $false } }).Count -gt 0) {
        $group = $true
        "group=level $level"
        $levelOfGroup = $level
    }
    if (-not $group) { continue }
    "--- level $level (묶음에서 $($level - $levelOfGroup) 층 위) ---"
    foreach ($el in $items) {
        try { $key = $el.GetRuntimeId() -join '.' } catch { continue }
        if ($seen.ContainsKey($key)) { continue }
        $seen[$key] = $true
        try { $d = Describe $el } catch { continue }
        "  $($d.Kind)|$($d.Name)|help=$($d.Help)|texts=$($d.Texts)"
        $all = "$($d.Name) $($d.Help) $($d.Texts)"
        if ($all.Contains($Leaf) -or $all -match '[A-Za-z]:\\') { "hit=level $level $($d.Kind)|$($d.Name)|help=$($d.Help)|texts=$($d.Texts)"; $found++ }
    }
    if ($level - $levelOfGroup -ge $Levels) { break }
}
try { $box.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).SetValue(''); Start-Sleep -Milliseconds 300 } catch { "clear=실패 $($_.Exception.Message)" }
"box-after=[$(try { $box.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value.Trim() } catch { '?' })]"
if (-not $group) { '측정 아님: 모델 버튼이 든 입력창 묶음을 찾지 못했다'; exit 1 }
"hits=$found"
if ($found -eq 0) { exit 2 }
