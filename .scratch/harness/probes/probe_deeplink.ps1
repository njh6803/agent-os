# open-session 의 딥링크가 지금 먹는지 보는 루프(일지 2026-09-30-06). 딥링크로 새 세션 화면을 열고, 프롬프트가 든
# 입력창(Edit)이 서는지만 본다. 보내지 않는다. 판정: page=<ms> 면 열렸다, none 이면 열리지 않았다. 입력창의 값으로만 본다
# (대화에 찍힌 같은 글자와 섞이지 않는다). 열리면 새 세션 화면이 남으니 사람이 닫는다. 첫 줄이 매번 다르게 쓴다.
#   pwsh -NoProfile -File .scratch/harness/probes/probe_deeplink.ps1 -PromptFile <첫 줄이 고유한 파일>
# 2026-09-30 결과: 앱이 끝나는 중(tools/open_session.ps1 의 Find-QuitMarker)인 동안 ASCII 프롬프트도 none 이었다.
param([Parameter(Mandatory)] [string] $PromptFile, [int] $Seconds = 20)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$Auto = [System.Windows.Automation.AutomationElement]
$Scope = [System.Windows.Automation.TreeScope]
$Types = [System.Windows.Automation.ControlType]
$prompt = Get-Content -Path $PromptFile -Raw -Encoding UTF8
$first = ($prompt -split "`r?`n")[0]
$needle = $first.Substring(0, [Math]::Min(24, $first.Length))
$win = @($Auto::RootElement.FindAll($Scope::Children, [System.Windows.Automation.Condition]::TrueCondition) | Where-Object { $_.Current.Name -eq 'Claude' })[0]
$editCond = New-Object System.Windows.Automation.PropertyCondition($Auto::ControlTypeProperty, $Types::Edit)
function Boxes {
    @($win.FindAll($Scope::Descendants, $editCond) | Where-Object {
        try { $v = $_.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value; $v -and $v.Replace([string][char]0xFF0F, '/').StartsWith($needle) } catch { $false }
    })
}
# 첫 줄의 글자는 찍지 않는다. 대화에 찍힌 글자가 접근성 트리에 남으면 open_session.ps1 의 다음 전송이 그것을 걸러야
# 한다(stale=). 길이만 낸다.
"needle=$($needle.Length)chars before=$((Boxes).Count) url=$(('claude://code/new?q=' + [uri]::EscapeDataString($prompt)).Length)"
$start = Get-Date
Start-Process ('claude://code/new?q=' + [uri]::EscapeDataString($prompt) + '&source=open-session')
while (((Get-Date) - $start).TotalSeconds -lt $Seconds) {
    if ((Boxes).Count -gt 0) { "page=$([int]((Get-Date) - $start).TotalMilliseconds)ms"; exit 0 }
    Start-Sleep -Milliseconds 300
}
"none after ${Seconds}s"
exit 1
