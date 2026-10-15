# 진단 전용. 값이 -Marker 인 입력창에 붙은 `모델:` 버튼의 이름과 자식 Text(그 화면의 모델과 노력 기본값)를 읽는다. 누르지 않는다.
# 새 세션 화면의 기본값이 앞서 open_session.ps1 이 고른 값을 따라가는지(끈적임) 볼 때 쓴다. 표지 글이 든 새 세션 화면은
# composer_effort_labels.ps1 이나 딥링크(`claude://code/new?q=<표지>`)로 연다. -Clear 를 주면 읽은 뒤 표지를 값으로 지운다.
# 앱 2.37337.1.0 에서 노력은 따로 된 `노력:` 버튼이 없고 `모델: <모델> <노력>` 버튼 하나가 둘을 보인다. 자식 Text 가 [모델, 노력] 이다.
# 쓰는 법: pwsh -NoProfile -File .scratch/harness/probes/composer_defaults.ps1 -Marker <표지> [-Clear]
param([Parameter(Mandatory)] [string] $Marker, [switch] $Clear)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$Auto = [System.Windows.Automation.AutomationElement]
$Scope = [System.Windows.Automation.TreeScope]
$Types = [System.Windows.Automation.ControlType]
$True_ = [System.Windows.Automation.Condition]::TrueCondition

$wins = @($Auto::RootElement.FindAll($Scope::Children, $True_) | Where-Object { $_.Current.Name -eq 'Claude' })
if ($wins.Count -ne 1) { throw "Claude 창이 $($wins.Count)개다." }
$win = $wins[0]
$editCond = New-Object System.Windows.Automation.PropertyCondition($Auto::ControlTypeProperty, $Types::Edit)
$boxes = @($win.FindAll($Scope::Descendants, $editCond) | Where-Object { try { $_.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value -eq $Marker } catch { $false } })
if ($boxes.Count -ne 1) { throw "값이 '$Marker' 인 입력창이 $($boxes.Count)개다." }
$box = $boxes[0]

$walker = [System.Windows.Automation.TreeWalker]::ControlViewWalker
$buttonCond = New-Object System.Windows.Automation.PropertyCondition($Auto::ControlTypeProperty, $Types::Button)
$textCond = New-Object System.Windows.Automation.PropertyCondition($Auto::ControlTypeProperty, $Types::Text)
foreach ($prefix in @('모델:', '노력:')) {
    $node = $box
    $found = $null
    for ($i = 0; $i -lt 20 -and -not $found; $i++) {
        $node = $walker.GetParent($node)
        if (-not $node) { break }
        $hits = @($node.FindAll($Scope::Descendants, $buttonCond) | Where-Object { try { $_.Current.Name.StartsWith($prefix) } catch { $false } })
        if ($hits.Count -gt 1) { throw "'$prefix' 버튼이 같은 조상 아래 $($hits.Count)개다." }
        if ($hits.Count -eq 1) { $found = $hits[0] }
    }
    $texts = if ($found) { @($found.FindAll($Scope::Children, $textCond) | ForEach-Object { $_.Current.Name } | Where-Object { $_.Trim() }) -join '|' } else { '' }
    "draft $prefix [$(if ($found) { $found.Current.Name } else { '없음' })] texts=[$texts]"
}
$all = @($win.FindAll($Scope::Descendants, $buttonCond) | Where-Object { try { $_.Current.Name -match '^(모델|노력):' } catch { $false } } | ForEach-Object { $_.Current.Name })
"window buttons [$($all -join ' / ')]"

if ($Clear) {
    try { $box.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).SetValue(''); Start-Sleep -Milliseconds 300 } catch { "clear=실패 $($_.Exception.Message)" }
    "cleared=[$(try { $box.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value.Trim() } catch { '?' })]"
}
