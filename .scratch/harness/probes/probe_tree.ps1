# 진단 전용. 아무것도 클릭하지 않고 Claude 창의 접근성 트리를 읽기만 한다.
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

$Auto = [System.Windows.Automation.AutomationElement]
$Scope = [System.Windows.Automation.TreeScope]
$Types = [System.Windows.Automation.ControlType]

$root = $Auto::RootElement
$wins = $root.FindAll($Scope::Children, [System.Windows.Automation.Condition]::TrueCondition)
$claude = @($wins | Where-Object { $_.Current.Name -eq 'Claude' })
"claude-windows=$($claude.Count)"
if ($claude.Count -ne 1) {
    "window-names=" + (($wins | ForEach-Object { $_.Current.Name }) -join ' | ')
    exit 0
}
$win = $claude[0]

$textCond = New-Object System.Windows.Automation.PropertyCondition($Auto::ControlTypeProperty, $Types::Text)
$texts = @($win.FindAll($Scope::Descendants, $textCond) | ForEach-Object { try { $_.Current.Name } catch { $null } } | Where-Object { $_ })
"text-elements=$($texts.Count)"
"--- implement 로 시작하는 것 ---"
$hit = @($texts | Where-Object { $_ -like '*implement*' })
"implement-hits=$($hit.Count)"
$hit | Select-Object -First 5 | ForEach-Object { "  [" + $_.Substring(0, [Math]::Min(60, $_.Length)) + "]" }

"--- 앞쪽 Text 요소 25개 ---"
$texts | Select-Object -First 25 | ForEach-Object { "  [" + $_.Substring(0, [Math]::Min(70, $_.Length)) + "]" }

"--- 버튼 이름 ---"
$btnCond = New-Object System.Windows.Automation.PropertyCondition($Auto::ControlTypeProperty, $Types::Button)
$btns = @($win.FindAll($Scope::Descendants, $btnCond) | ForEach-Object { try { $_.Current.Name } catch { $null } } | Where-Object { $_ })
"buttons=$($btns.Count)"
$btns | Select-Object -First 30 | ForEach-Object { "  <" + $_ + ">" }

"--- Edit/Document 요소 ---"
foreach ($t in @($Types::Edit, $Types::Document)) {
    $c = New-Object System.Windows.Automation.PropertyCondition($Auto::ControlTypeProperty, $t)
    $els = @($win.FindAll($Scope::Descendants, $c))
    "$($t.ProgrammaticName) count=$($els.Count)"
    $els | Select-Object -First 5 | ForEach-Object {
        $n = try { $_.Current.Name } catch { '' }
        $v = try { $_.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value } catch { '' }
        "   name=[" + $n.Substring(0, [Math]::Min(45, $n.Length)) + "] value=[" + $v.Substring(0, [Math]::Min(45, $v.Length)) + "]"
    }
}
