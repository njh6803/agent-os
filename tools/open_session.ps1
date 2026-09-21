# open-session 스킬의 손발. 데스크톱 앱에 새 Code 세션을 클릭 없이 연다.
#
# `send`: 딥링크 `claude://code/new?q=<프롬프트>`로 프롬프트가 채워진 새 세션 화면을 열고 접근성
# 트리(UI Automation)의 "보내기"를 호출한다. `split`: 사이드바 행 메뉴 "다음에서 열기 → 분할 보기".
# 왜 이 둘인지(자동 제출 파라미터가 없고 배치 도구가 거부한다)와 실측은 일지 2026-09-21 open-session.
#
# 사용:
#   pwsh -NoProfile -File tools/open_session.ps1 -Action send  -Folder <절대경로> -PromptFile <파일>
#   pwsh -NoProfile -File tools/open_session.ps1 -Action split -Title <세션 제목>
#   pwsh -NoProfile -File tools/open_session.ps1 -Action focus -Title <세션 제목>   (이미 패널에 있을 때)
param(
    [Parameter(Mandatory)] [ValidateSet('send', 'split', 'focus')] [string] $Action,
    [string] $Folder,
    [string] $PromptFile,
    [string] $Title,
    # 사이드바 행이 새 제목으로 갱신되는 데 몇 초 걸린다. 넉넉히 둔다.
    [int] $TimeoutSec = 30
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Windows.Forms

$Auto = [System.Windows.Automation.AutomationElement]
$Scope = [System.Windows.Automation.TreeScope]
$Types = [System.Windows.Automation.ControlType]

function Get-ClaudeWindow {
    $root = $Auto::RootElement
    $wins = $root.FindAll($Scope::Children, [System.Windows.Automation.Condition]::TrueCondition)
    $found = @($wins | Where-Object { $_.Current.Name -eq 'Claude' })
    if ($found.Count -eq 0) { throw 'Claude 창을 찾지 못했다. 데스크톱 앱이 떠 있어야 한다.' }
    # 창이 둘이면 아무 창이나 골라 그 창에 보내기·신뢰·분할이 들어간다. 조용히 틀리지 않게 멈춘다.
    if ($found.Count -gt 1) { throw "이름이 'Claude'인 창이 $($found.Count)개다. 팝아웃 창을 닫고 다시 돌린다." }
    return $found[0]
}

function Find-ByName($win, [string[]] $names, $type) {
    foreach ($name in $names) {
        $cond = New-Object System.Windows.Automation.PropertyCondition($Auto::NameProperty, $name)
        if ($type) {
            $typeCond = New-Object System.Windows.Automation.PropertyCondition($Auto::ControlTypeProperty, $type)
            $cond = New-Object System.Windows.Automation.AndCondition($typeCond, $cond)
        }
        $el = $win.FindFirst($Scope::Descendants, $cond)
        if ($el) { return $el }
    }
    return $null
}

function Wait-For([scriptblock] $probe, [string] $what, [int] $Seconds = $TimeoutSec) {
    $deadline = (Get-Date).AddSeconds($Seconds)
    while ((Get-Date) -lt $deadline) {
        $found = & $probe
        if ($found) { return $found }
        Start-Sleep -Milliseconds 500
    }
    throw "${Seconds}초 안에 $what 을(를) 찾지 못했다."
}

# 마우스를 쓰지 않는다. 사용자가 마우스를 움직이는 중에도 돌아야 한다. Invoke 를 지원하는 요소
# ("분할 보기", "보내기")는 Invoke 로, 아니면(행 옵션 버튼, "다음에서 열기") 포커스를 주고 키를
# 보낸다(Enter, 하위 메뉴는 →). 키는 포커스된 요소로만 간다. ExpandCollapse 는 쓰지 않는다.
# 실측에서 호출이 돌아오지 않고 멈춘 적이 있다(일지 2026-09-21 open-session).
function Press-Element($el, [string] $key = '{ENTER}') {
    try { $el.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke(); Start-Sleep -Milliseconds 600; return 'invoke' } catch {}
    # 이름을 바꾼 직후에는 사이드바가 다시 그려지는 사이라 SetFocus 가 빈 메시지로 던진다. 짧게 다시 시도한다.
    # ScrollIntoView 도 Expand 처럼 돌아오지 않은 적이 있어 부르지 않는다. 실측에서 통한 호출만 쓴다.
    $focused = $false
    for ($i = 0; $i -lt 5 -and -not $focused; $i++) {
        try { $el.SetFocus(); $focused = $true } catch { Start-Sleep -Milliseconds 400 }
    }
    if (-not $focused) { throw "요소 '$($el.Current.Name)'에 포커스를 줄 수 없다." }
    Start-Sleep -Milliseconds 300
    [System.Windows.Forms.SendKeys]::SendWait($key)
    Start-Sleep -Milliseconds 600
    return "key:$key"
}

function Send-Prompt {
    if (-not $Folder -or -not $PromptFile) { throw 'send 에는 -Folder 와 -PromptFile 이 필요하다.' }
    $prompt = Get-Content -Path $PromptFile -Raw -Encoding UTF8
    $firstLine = ($prompt -split "`r?`n")[0]
    # `folder`를 실으면 앱이 외부에서 온 폴더로 보고(`src=external`) 신뢰를 다시 묻고, 그 대화상자를
    # 거치면 폴더가 떨어져 스크래치 워크스페이스로 열린다(실측 9). 폴더는 싣지 않는다. 앱은 마지막
    # 폴더를 기본으로 잡고, 여는 세션이 저장소에서 돌고 있으니 그것이 루트다. 맞는지는 스킬이
    # `list_sessions`의 cwd 로 확인한다.
    $url = 'claude://code/new?q=' + [uri]::EscapeDataString($prompt) + '&source=open-session'
    if ($url.Length -gt 30000) { throw "URL 이 $($url.Length)자다. 프롬프트를 줄인다(핸들러가 자르면 지시문 꼬리가 사라진다)." }

    $win = Get-ClaudeWindow
    Start-Process $url
    "fired=$(Get-Date -Format HH:mm:ss.fff)"

    # 접근성 트리는 프롬프트를 문단 단위 Text 요소로 내므로 첫 줄의 앞부분으로 찾는다.
    $needle = $firstLine.Substring(0, [Math]::Min(24, $firstLine.Length))
    $textCond = New-Object System.Windows.Automation.PropertyCondition($Auto::ControlTypeProperty, $Types::Text)
    # Name 이 null 인 Text 요소가 있다. 먼저 거른다.
    # Name 은 한 번만 읽는다. 두 번 읽는 사이에 요소가 다시 그려져 두 번째가 null 이 된 적이 있다.
    $page = Wait-For { $win.FindAll($Scope::Descendants, $textCond) | Where-Object { try { $n = $_.Current.Name; $n -and $n.StartsWith($needle) } catch { $false } } | Select-Object -First 1 } "프롬프트 첫 줄('$needle…')이 채워진 새 세션 화면"
    "page=$(Get-Date -Format HH:mm:ss.fff)"

    # 기본 폴더가 아직 신뢰되지 않았으면 앱이 워크스페이스 신뢰를 묻는다. 대화상자에 적힌 폴더가
    # -Folder 와 정확히 같을 때만 수락한다(사용자 승인, 일지 2026-09-21 open-session).
    $trust = Find-ByName $win @('작업 공간 신뢰', 'Trust workspace') $Types::Button
    if ($trust) {
        # 대화상자만 전체 경로를 Text 로 보인다(사이드바는 폴더 이름뿐). 창에 보이는 전체 경로가
        # 전부 -Folder 와 같을 때만 수락한다. 다른 경로가 하나라도 있으면 사람이 판단한다.
        $paths = @($win.FindAll($Scope::Descendants, $textCond) | ForEach-Object { $_.Current.Name } | Where-Object { $_ -match '^[A-Za-z]:\\' })
        if ($paths.Count -eq 0 -or @($paths | Where-Object { $_ -ne $Folder }).Count -gt 0) {
            throw "신뢰 대화상자의 폴더가 '$Folder'가 아니다(보이는 경로: $($paths -join ', ')). 사람이 판단한다."
        }
        $trust.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke()
        "trusted=$(Get-Date -Format HH:mm:ss.fff)"
    }

    $send = Wait-For { Find-ByName $win @('보내기', 'Send') $Types::Button } '보내기 버튼'
    $send.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke()
    "sent=$(Get-Date -Format HH:mm:ss.fff)"
}

function Split-Session {
    if (-not $Title) { throw 'split 에는 -Title 이 필요하다.' }
    $win = Get-ClaudeWindow
    # `"$Title에"` 는 PowerShell 이 `$Title에` 라는 변수로 읽는다(한글이 변수 이름 문자다). 중괄호가 필수다.
    # 메뉴는 사용자가 앱 안 다른 곳을 클릭하면 닫힌다. 열려 있는 시간을 짧게(단계마다 3초) 두고
    # 세 번까지 다시 연다. 행은 시도마다 다시 찾는다. 다시 그려지면 앞서 잡은 요소가 무효다.
    $last = $null
    # 화면이 방금 바뀌었으면 사이드바가 다시 그려지는 중이다. 잠깐 정착시킨다.
    Start-Sleep -Milliseconds 1000
    for ($attempt = 1; $attempt -le 3; $attempt++) {
        try {
            $row = Wait-For { Find-ByName $win @("${Title}에 대한 더 많은 옵션", "More options for ${Title}") $Types::Button } "사이드바 행 '${Title}'의 옵션 버튼"
            $how1 = Press-Element $row
            $openIn = Wait-For { Find-ByName $win @('다음에서 열기', 'Open in') $Types::MenuItem } "'다음에서 열기' 메뉴" 6
            $how2 = Press-Element $openIn '{RIGHT}'
            $split = Wait-For { Find-ByName $win @('분할 보기', 'Split view') $Types::MenuItem } "'분할 보기' 메뉴" 6
            $how3 = Press-Element $split
            "split=$(Get-Date -Format HH:mm:ss.fff) attempt=$attempt via $how1,$how2,$how3"
            return
        } catch {
            $last = $_
            # 메뉴를 연 채로 다음 시도로 가지 않는다.
            [System.Windows.Forms.SendKeys]::SendWait('{ESC}{ESC}')
            Start-Sleep -Milliseconds 700
        }
    }
    # 세 번 다 닫혔으면 옆 패널을 포기하고 그 세션 행을 눌러 메인 패널에 포커스로 띄운다. 행 이름은
    # "<상태> <제목>"("유휴 …", "실행 중 …")이라 끝이 제목인 버튼을 찾는다. 옵션 버튼은 "…에 대한"이라 안 걸린다.
    $rowCond = New-Object System.Windows.Automation.PropertyCondition($Auto::ControlTypeProperty, $Types::Button)
    $rowButton = $null
    try {
        $rowButton = Wait-For { $win.FindAll($Scope::Descendants, $rowCond) | Where-Object { try { $n = $_.Current.Name; $n -and $n.EndsWith(" ${Title}") } catch { $false } } | Select-Object -First 1 } "행 '${Title}'" 10
    } catch {}
    if (-not $rowButton) { throw "분할 메뉴가 세 번 닫혔고 행 '${Title}'도 못 찾았다. 새 세션은 열려 있다. 마지막 오류: $($last.Exception.Message)" }
    $how = Invoke-Row $rowButton.Current.Name
    if ($how -ne 'invoke') { throw "분할 메뉴가 세 번 닫혔고 행 '${Title}'도 누르지 못했다($how). 새 세션은 열려 있다." }
    "focus=$(Get-Date -Format HH:mm:ss.fff) via $how (분할 메뉴가 세 번 닫혀 포커스로 대신했다: $($last.Exception.Message))"
}

# 세션 행을 눌러 메인 패널에 포커스로 띄운다(사이드바 행 클릭과 같다). 행 버튼은 키(Enter, Space)에
# 반응하지 않고 Invoke 에만 반응한다. Invoke 는 돌아오지 않은 적이 있어 잡 안에서 8초 제한으로 부른다.
function Invoke-Row([string] $rowName) {
    $job = Start-Job -ScriptBlock {
        param($name)
        Add-Type -AssemblyName UIAutomationClient; Add-Type -AssemblyName UIAutomationTypes
        $Auto = [System.Windows.Automation.AutomationElement]; $Scope = [System.Windows.Automation.TreeScope]
        $win = $Auto::RootElement.FindAll($Scope::Children, [System.Windows.Automation.Condition]::TrueCondition) | Where-Object { $_.Current.Name -eq 'Claude' } | Select-Object -First 1
        $row = $win.FindFirst($Scope::Descendants, (New-Object System.Windows.Automation.PropertyCondition($Auto::NameProperty, $name)))
        if (-not $row) { return 'row-missing' }
        $row.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern).Invoke()
        return 'invoke'
    } -ArgumentList $rowName
    try {
        if (Wait-Job $job -Timeout 8) { return (Receive-Job $job) }
        Stop-Job $job
        return 'invoke-hung'
    } finally { Remove-Job $job -Force }
}

function Focus-Session {
    if (-not $Title) { throw 'focus 에는 -Title 이 필요하다.' }
    $win = Get-ClaudeWindow
    $rowCond = New-Object System.Windows.Automation.PropertyCondition($Auto::ControlTypeProperty, $Types::Button)
    $rowButton = Wait-For { $win.FindAll($Scope::Descendants, $rowCond) | Where-Object { try { $n = $_.Current.Name; $n -and $n.EndsWith(" ${Title}") } catch { $false } } | Select-Object -First 1 } "행 '${Title}'" 10
    $how = Invoke-Row $rowButton.Current.Name
    if ($how -ne 'invoke') { throw "행 '${Title}'을 누르지 못했다($how)." }
    "focus=$(Get-Date -Format HH:mm:ss.fff) via $how"
}

switch ($Action) {
    'send' { Send-Prompt }
    'split' { Split-Session }
    'focus' { Focus-Session }
}
