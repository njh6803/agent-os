# open-session 스킬의 손발. 데스크톱 앱에 새 Code 세션을 연다. 첫 줄이 이 저장소의 스킬을 부르는 슬래시
# 명령이면 쏘기 전에 그 스킬 파일을 읽어 따르라는 한 줄로 옮겨(`Convert-StartLine`) 사람 손 없이 보낸다.
# 옮기지 못한 슬래시 명령은 앱이 `/` 를 전각으로 바꿔 넣으므로 보내기 전에 멈추고(`held=`) 사람이 고쳐 보낸다.
#
# `send`: 딥링크 `claude://code/new?q=<프롬프트>`로 프롬프트가 채워진 새 세션 화면을 열고 접근성
# 트리(UI Automation)의 "보내기"를 호출한다. `split`: 사이드바 행 메뉴 "다음에서 열기 → 분할 보기".
# 왜 이 둘인지(자동 제출 파라미터가 없고 배치 도구가 거부한다)와 실측은 일지 2026-09-21 open-session.
# 지시문에 `모델: <모델 메뉴의 이름> / <low|medium|high|xhigh|max>` 줄이 있으면 보내기 전에 입력창의 모델과 노력을 그대로
# 고르고(`Set-ComposerModel`), 보낸 뒤 새 세션 화면의 모델과 노력 기본값을 고르기 전으로 되돌린다(`Restore-DraftDefaults`).
#
# 사용:
#   pwsh -NoProfile -File tools/open_session.ps1 -Action send  -Folder <절대경로> -PromptFile <파일>
#   pwsh -NoProfile -File tools/open_session.ps1 -Action split -Title <세션 제목>
#   pwsh -NoProfile -File tools/open_session.ps1 -Action focus -Title <세션 제목>   (이미 패널에 있을 때)
#   pwsh -NoProfile -File tools/open_session.ps1 -Action defaults -Model <모델 메뉴의 이름> -Effort <레벨>   (기본값 복구)
param(
    [Parameter(Mandatory)] [ValidateSet('send', 'split', 'focus', 'defaults')] [string] $Action,
    [string] $Folder,
    [string] $PromptFile,
    [string] $Title,
    [string] $Model,
    [string] $Effort,
    # 사이드바 행이 새 제목으로 갱신되는 데 몇 초 걸린다. 넉넉히 둔다. `focus` 는 새 세션이 첫 턴에
    # 스스로 이름을 붙일 때까지 기다리므로 스킬이 더 늘려 준다.
    [int] $TimeoutSec = 30
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type -AssemblyName System.Windows.Forms
Add-Type -TypeDefinition @'
using System; using System.Runtime.InteropServices;
public static class OpenSessionPower {
    [DllImport("kernel32.dll")] public static extern uint SetThreadExecutionState(uint flags);
    [StructLayout(LayoutKind.Sequential)] struct LastInput { public uint cbSize; public uint dwTime; }
    [DllImport("user32.dll")] static extern bool GetLastInputInfo(ref LastInput info);
    // 실패하면 -1. GetLastInputInfo 는 실패를 예외가 아니라 false 로 알린다.
    public static long IdleSeconds() { var l = new LastInput(); l.cbSize = (uint)Marshal.SizeOf(l); if (!GetLastInputInfo(ref l)) { return -1; } return ((uint)Environment.TickCount - l.dwTime) / 1000; }
}
public static class OpenSessionKeys {
    [DllImport("user32.dll")] public static extern bool PostMessage(IntPtr window, uint message, IntPtr wParam, IntPtr lParam);
}
'@

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

# 모델 고르기와 되돌리기는 앞에 있는 창으로 가는 키(SendKeys)를 쓰지 않는다. 사람이 다른 앱을 쓰는 동안 Claude 창의 요소에
# SetFocus 를 해도 Claude 창은 앞으로 오지 않았다(Chrome 이 앞에 있을 때 .scratch/harness/probes/foreground_window.ps1 로
# 손으로 봤다, 2026-10-12). 그래서 접근성 패턴(펼치기, 항목 선택, 값 설정)을 쓰고, 패턴으로 열리지 않는 노력 하위 메뉴 하나만
# Claude 창 핸들에 PostMessage 로 넣는 키로 연다(Open-EffortSubmenu). 그 키는 앞에 있는 창이 아니라 그 핸들로만 간다.
# 펼치기는 돌아오지 않은 적이 있어(일지 2026-09-21 open-session, 사이드바 행) 스레드 잡 안에서 8초 제한으로 부른다.
# 입력창의 모델 버튼에서는 돌아왔다(.scratch/harness/probes/composer_patterns.ps1, 2026-10-12·2026-10-16).
# 시간을 넘긴 잡은 지우지 않고 남긴다. 멈춘 스레드 잡의 Remove-Job -Force 는 그 호출이 끝날 때까지 기다려 제한 시간이 걸리지
# 않았다. 남긴 스레드는 pwsh 가 끝날 때도 기다리므로 $script:HungCalls 로 세어 두고, 스크립트 끝(Invoke-Action)이 출력을 마친 뒤
# 프로세스를 끝낸다. 멈춘 호출을 15초 잠으로 흉내 내고 제한을 2초로 둔 .scratch/harness/probes/hung_thread_job.ps1 에서, 지우는
# 모양은 15.1초에 돌아왔고, 남기는 모양은 2.1초에 돌아왔지만 프로세스가 15.7초에 끝났으며, 끝내는 모양은 3초 안에 출력과 종료
# 코드(던졌으면 1)를 남기고 끝났다(2026-10-16).
$script:HungCalls = 0
function Invoke-PatternTimed($el, [string] $action, [int] $timeoutSec = 8) {
    $job = Start-ThreadJob -ArgumentList $el, $action -ScriptBlock {
        param($e, $a)
        switch ($a) {
            'expand' { $e.GetCurrentPattern([System.Windows.Automation.ExpandCollapsePattern]::Pattern).Expand() }
            'collapse' { $e.GetCurrentPattern([System.Windows.Automation.ExpandCollapsePattern]::Pattern).Collapse() }
            'select' { $e.GetCurrentPattern([System.Windows.Automation.SelectionItemPattern]::Pattern).Select() }
        }
        'ok'
    }
    if (-not (Wait-Job $job -Timeout $timeoutSec)) {
        $script:HungCalls++
        return "$action-hung"
    }
    try {
        $out = Receive-Job $job -ErrorAction SilentlyContinue -ErrorVariable failed
        if ($failed) { return "$action-error: $($failed[0])" }
        return $out
    } finally { Remove-Job $job -Force }
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
    $startLine = Convert-StartLine $firstLine $Folder
    if ($startLine -cne $firstLine) {
        $prompt = $startLine + $prompt.Substring($firstLine.Length)
        $firstLine = $startLine
        "start=$($startLine.Substring(0, $startLine.IndexOf(' 를 읽어')))"
    }
    # 모델 줄은 쏘기 전에 읽는다. 읽을 수 없는 줄이면 여기서 멈춰 세션이 생기지 않는다.
    $pick = Read-ModelLine $prompt
    if (-not $pick) { 'model=unset 지시문에 모델 줄이 없어 입력창에 있던 값으로 연다' }
    # `folder`를 실으면 앱이 외부에서 온 폴더로 보고(`src=external`) 신뢰를 다시 묻고, 그 대화상자를
    # 거치면 폴더가 떨어져 스크래치 워크스페이스로 열린다(실측 9). 폴더는 싣지 않는다. 앱은 마지막
    # 폴더를 기본으로 잡고, 여는 세션이 저장소에서 돌고 있으니 그것이 루트다. 맞는지는 스킬이
    # `list_sessions`의 cwd 로 확인한다.
    $url = 'claude://code/new?q=' + [uri]::EscapeDataString($prompt) + '&source=open-session'
    # 윈도가 프로토콜 핸들러에 URL 을 명령줄로 넘기고 그 명령줄이 잘린다. 넘치면 앱이 딥링크를 아예
    # 받지 못하고, 스크립트는 아래 `page=` 에서 "화면을 못 찾았다"로 끝나 원인을 가린다. 실측: 9766자는
    # 화면이 열리지 않았고, 같은 지시문을 6589자로 줄이자 열렸다(2026-09-23, 티켓 03 세션). 그 사이 어디가
    # 상한인지는 재지 않았다. 흔히 쓰는 명령줄 상한 8191 아래로 둔다. 전에는 30000 이었는데 그 값이 이
    # 실패를 통과시켰다.
    $maxUrl = 8000
    if ($url.Length -gt $maxUrl) { throw "URL 이 $($url.Length)자다(상한 $maxUrl). 지시문의 '읽을 것'을 경로 목록으로 줄인다. 넘치면 앱이 딥링크를 받지 못한다." }
    # 앱이 끝나는 중이면 딥링크를 로그 없이 버린다(`Find-QuitMarker`). 쏘면 `page=` 에서 원인 없이 기다리다 끝나므로 쏘기 전에
    # 멈춘다. 쏘지 않았으니 앱을 다시 시작한 뒤 다시 돌려도 세션이 둘 생기지 않는다. 판정 자체가 실패하면 막지 않는다. 판정은
    # 돕는 일이고, 막으면 관계없는 에러가 여는 일을 막는다. 그 사실은 `quitcheck=` 로 남긴다.
    $quitMarker = $null
    try { $quitMarker = Get-AppQuitMarker } catch { "quitcheck=판정하지 못했다: $($_.Exception.Message)" }
    if ($quitMarker) {
        "quitting=$quitMarker"
        # 앱 안의 재시작(업데이트 배너, 메뉴의 끝내기)은 같은 깃발에 막혀 아무 일도 하지 않는다(앱 2.9939.2 번들의 `QA`·`$A` 의
        # `ej()||`. 축약 이름이라 판이 바뀌면 달라진다. 뜻은 `Find-QuitMarker` 앞의 주석).
        throw "앱이 끝나는 중이라(위 quitting= 의 로그 줄부터) 딥링크를 버린다. 쏘지 않았다. 앱 안의 재시작(업데이트 배너, 메뉴의 끝내기)은 이 상태에서 아무 일도 하지 않는다. 사람이 작업 관리자에서 Claude 를 끝내고 다시 켠 뒤 이 스크립트를 다시 돌린다."
    }

    $win = Get-ClaudeWindow
    # 접근성 트리는 프롬프트를 문단 단위 Text 요소로 내므로 첫 줄의 앞부분으로 찾는다. 앱이 첫 `/` 를
    # 전각 `／` 로 바꿔 넣으므로(아래 `held=`) 비교는 Test-Needle 한 곳에서 한다.
    $needle = $firstLine.Substring(0, [Math]::Min(24, $firstLine.Length))
    $textCond = New-Object System.Windows.Automation.PropertyCondition($Auto::ControlTypeProperty, $Types::Text)
    # 쏘기 전에 이미 있던 매칭을 기억해 두고 새로 생긴 것만 화면으로 친다. 앞 시도가 실패하면 그 진단이
    # needle 을 지금 대화에 그대로 인쇄하고, 트리 탐색은 화면 밖 요소도 돌려주므로 그 글자가 새 세션
    # 화면으로 오인된다. 그러면 `page=` 가 거짓으로 찍혀 "딥링크는 열렸다"로 읽힌다. 실제 보내기는 아래
    # 입력창 확인이 막지만(그 입력창은 비어 있다) 진단이 거짓말을 하게 된다(2026-09-23 실측).
    $stale = @{}
    foreach ($el in @($win.FindAll($Scope::Descendants, $textCond))) {
        try { $n = $el.Current.Name } catch { $n = $null }
        $key = Get-RuntimeKey $el
        if ((Test-Needle $n $needle) -and $key) { $stale[$key] = $true }
    }
    if ($stale.Count -gt 0) { "stale=$($stale.Count)" }

    Start-Process $url
    "fired=$(Get-Date -Format HH:mm:ss.fff)"

    # Name 이 null 인 Text 요소가 있다. 먼저 거른다.
    # Name 은 한 번만 읽는다. 두 번 읽는 사이에 요소가 다시 그려져 두 번째가 null 이 된 적이 있다.
    $page = Wait-For { $win.FindAll($Scope::Descendants, $textCond) | Where-Object { try { $n = $_.Current.Name; (Test-Needle $n $needle) -and -not $stale.ContainsKey((Get-RuntimeKey $_)) } catch { $false } } | Select-Object -First 1 } "프롬프트 첫 줄('$needle…')이 채워진 새 세션 화면"
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

    # 창이 분할 보기면 "보내기"가 패널마다 하나씩 있고 빈 입력창의 것은 비활성이다. 활성인 것만
    # 고른다. 처음 찾은 것을 누르면 비활성 쪽에 걸려 Invoke 가 빈 예외로 끝난다(2026-09-22 실측,
    # 티켓 03 세션). 활성 버튼도 Invoke 가 빈 예외를 내고 제출이 안 된 적이 있어 Press-Element 로
    # 포커스+Enter 까지 간다. 제출됐는지는 입력창이 비었는지로 본다. 눌렀다는 것은 보냈다는 뜻이 아니다.
    # 확인의 대상은 누르기 전에 잡는다. 지시문이 든 입력창을 못 찾으면 무엇이 비었는지 판정할 수 없고,
    # 그 상태에서 "빈 입력창이 없다"를 성공으로 치면 확인이 공허해진다(PR #33 리뷰). 못 찾으면 멈춘다.
    $box = Wait-For { Find-PromptBox $win $needle } "지시문('$needle…')이 든 입력창" 6

    # 모델 줄은 아래 `held=` 보다 먼저 고른다. `held=` 면 사람이 첫 글자만 고쳐 보내므로, 그때도 첫 턴이 줄의 값으로 돈다.
    # 고른 뒤 `sent=` 전에 멈추면(고르기·보내기 버튼·제출 확인의 실패, `held=`) 이 스크립트가 되돌릴 때가 없다. 기본값이 바뀌었으면
    # 사람이 보낸 뒤(제출 확인의 시간 초과면 이미 보냈을 수 있다) 칠 복구를 남긴다(PR 직전 버그·성능 리뷰, Get-PendingRestoreLine).
    $draft = $null
    try {
        if ($pick) {
            $draft = Read-DraftDefaults $box
            Set-ComposerModel $win $box $pick $draft
            # 메뉴를 여닫는 키가 입력창에 닿지 않았는지 본다. 지시문이 바뀌었으면 보내지 않는다.
            if (-not (Test-Needle (Get-EditValue $box) $needle)) { throw '모델을 고르는 사이 입력창의 지시문이 바뀌었다. 보내지 않았다. 사람이 입력창을 본다.' }
        }

        # 앱은 링크로 온 슬래시 명령을 그대로 실행하지 않는다. 첫 `/` 를 전각 `／`(U+FF0F)로 바꿔 넣어,
        # 그대로 보내면 명령이 아니라 글자가 된다 — `/implement` 가 사용자 호출로 먹지 않는다(2026-09-23 실측,
        # 입력창의 값 첫 글자가 U+FF0F). 스크립트는 되돌려 넣지 않는다. 어디서 왔는지 모르는 링크가 명령을
        # 일으키지 못하게 한 앱의 장치를 통째로 우회하는 일이다 — 되돌린 `/` 는 내장 명령을 포함해 아무 슬래시
        # 명령이나 일으킨다. 위의 `Convert-StartLine` 도 효과로는 그 장치를 비껴가지만 가리킬 수 있는 것이 이
        # 저장소의 스킬 파일뿐이다. 그렇게 옮긴 것은 여기 오지 않으므로, 여기 걸리는 것은 옮기지 못한 슬래시
        # 명령뿐이다(스킬 파일이 없다).
        # 보내기를 누르지 않고 멈춘다. 스킬이 사람에게 부탁하고 턴을 끝낸다.
        $value = Get-EditValue $box
        if ($value -and [int][char]$value[0] -eq 0xFF0F) {
            "held=$(Get-Date -Format HH:mm:ss.fff) 입력창의 첫 글자가 U+FF0F 다(옮기지 못한 슬래시 명령). 사람이 / 로 고쳐 보낸다"
            Get-PendingRestoreLine $draft $pick
            return
        }

        $send = Wait-For { Find-EnabledSendButton $win } '활성 보내기 버튼'
        $how = Press-Element $send
        Wait-For {
            try { -not (Test-Needle ($box.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value) $needle) } catch { $false }
        } '제출된 뒤 비워진 입력창(요소를 못 읽으면 비운 것으로 치지 않는다)' 10 | Out-Null
    } catch {
        Get-PendingRestoreLine $draft $pick
        throw
    }
    "sent=$(Get-Date -Format HH:mm:ss.fff) via $how"
    if ($pick) { Restore-DraftDefaults $win $draft $pick }
}

function Get-RuntimeKey($el) {
    # 요소가 살아 있는 동안 같은 값이라 다시 찾아도 같은 요소인지 가를 수 있다. 못 읽으면 빈 문자열이고
    # 그러면 어떤 기억과도 겹치지 않아 새 것으로 친다 — 못 읽는 것을 오래된 것으로 치면 진짜 화면을 놓친다.
    try { return ($el.GetRuntimeId() -join '.') } catch { return '' }
}

# 첫 줄이 이 저장소의 스킬을 부르는 슬래시 명령(`/<이름> <인자>`)이면 그 스킬 파일을 읽어 따르라는 한 줄로
# 옮긴다. 딥링크의 슬래시 명령은 앱이 전각으로 바꿔 명령이 되지 못하고 사람이 고쳐 보내야 했다. 스킬 파일을
# 가리키는 문장은 명령이 아니라 지시라 그대로 보낼 수 있다. 왜 이렇게 하는지와 그 대가는 open-session 스킬.
# 이름은 훅의 전각 대체 경로와 같은 kebab 한 토막이라 `.claude/skills/` 밖을 가리키지 못하고, 파일이 없으면
# 옮기지 않아 아래 `held=` 가 받는다. 인자에 지시문 전문이 드는 것은 슬래시 명령과 같다.
# 딥링크가 폴더를 싣지 않아 새 세션은 앱의 마지막 폴더에서 열린다. 그래서 두 겹으로 막는다. 경로는 상대 경로라
# 저장소가 아닌 폴더에서는 파일을 못 찾아 멈추고, 연 저장소를 표지로 실어 새 세션의 훅이 자기 작업 폴더와
# 다르면 프롬프트를 막는다(PR #65 의 CodeRabbit). 문구는 hook_prompt_directive 의 `_OPENED_LINE` 이 글자로
# 파싱하는 형식이라, 바꾸면 tests/tools 의 대조 테스트가 빨개진다.
function Convert-StartLine([string] $line, [string] $root) {
    if ($root -and $line -cmatch '^/([a-z0-9][a-z0-9-]*)(?:\s+(.*))?$') {
        $skill = ".claude/skills/$($Matches[1])/SKILL.md"
        $rest = $Matches[2]
        if (Test-Path -LiteralPath (Join-Path $root $skill) -PathType Leaf) {
            return "$skill 를 읽어 그대로 따른다. 이 세션을 연 저장소는 ``$root``이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: $rest".TrimEnd()
        }
    }
    return $line
}

function Normalize-Slash([string] $s) {
    # 앱이 딥링크로 온 슬래시 명령의 첫 `/` 를 전각 `／`(U+FF0F)로 바꿔 넣는다. 찾을 때만 되돌려 비교한다.
    # 문화권 비교는 둘을 같게 보지 않는다 — 고치기 전의 needle 이 그 화면을 끝내 못 찾은 이유다.
    if ($s -and [int][char]$s[0] -eq 0xFF0F) { return '/' + $s.Substring(1) }
    return $s
}

function Test-Needle([string] $s, [string] $needle) {
    # needle 비교는 여기 한 곳이다. 쏘기 전 스냅숏, 화면 확인, 입력창 찾기, 제출 확인이 모두 부른다. 규칙이
    # 네 자리에 흩어지면 하나를 빠뜨린 자리가 곧 다음 실패다 — 전각 슬래시 버그가 바로 그 모양이었다.
    return [bool]($s -and (Normalize-Slash $s).StartsWith($needle))
}

# 지시문이 든 입력창. 이름은 로케일에 따르므로 이름이 아니라 값으로 고른다. 값을 못 읽는 요소는 후보가 아니다.
function Find-PromptBox($win, [string] $needle) {
    $editCond = New-Object System.Windows.Automation.PropertyCondition($Auto::ControlTypeProperty, $Types::Edit)
    $boxes = @($win.FindAll($Scope::Descendants, $editCond) | Where-Object {
        try { Test-Needle ($_.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value) $needle } catch { $false }
    })
    if ($boxes.Count -gt 1) { throw "지시문이 든 입력창이 $($boxes.Count)개다. 앞선 실행이 남긴 페이지가 있다. 사람이 하나만 남긴다." }
    if ($boxes.Count -eq 1) { return $boxes[0] }
    return $null
}

function Find-EnabledSendButton($win) {
    $buttons = @()
    foreach ($name in @('보내기', 'Send')) {
        $cond = New-Object System.Windows.Automation.AndCondition(
            (New-Object System.Windows.Automation.PropertyCondition($Auto::ControlTypeProperty, $Types::Button)),
            (New-Object System.Windows.Automation.PropertyCondition($Auto::NameProperty, $name)))
        $buttons += @($win.FindAll($Scope::Descendants, $cond) | Where-Object { try { $_.Current.IsEnabled } catch { $false } })
    }
    if ($buttons.Count -gt 1) { throw "활성 보내기 버튼이 $($buttons.Count)개다. 다른 패널의 입력창에도 글이 있다. 사람이 판단한다." }
    if ($buttons.Count -eq 1) { return $buttons[0] }
    return $null
}

# 지시문의 `모델:` 줄(`모델: <모델 메뉴의 이름> / <레벨>`)을 읽는다. 줄이 없으면 $null 이고 입력창에 있던 값으로 연다.
# 줄이 있는데 읽을 수 없으면 쏘기 전에 멈춘다. 틀린 줄을 건너뛰고 열면 지시문이 정한 것과 다른 모델로 첫 턴이 돈다.
# 레벨은 API 이름 그대로 소문자이고, 칸은 입력창 노력 칸의 차례다. 앱 2.19675.0.0 에서는 노력 슬라이더였고 0~4 칸의 이름이
# 낮음·중간·높음·엑스트라·최대, 여섯째 칸(5)은 레벨이 아닌 `Ultracode` 였다. 0·1·2·4 는 그 칸으로 연 시험 세션의
# get_session 이 low·medium·high·max 였고, 3 은 엑스트라로 연 세션의 get_session 이 xhigh 였다(손으로 봤다, 2026-10-12).
# 앱 2.37337.1.0 에서는 슬라이더가 모델 메뉴 안의 노력 하위 메뉴가 되었고, 항목의 차례와 덧붙임을 뗀 이름은 같다(낮음, 중간 추천,
# 높음, 엑스트라, 최대 3.5× 이상 사용량, Ultracode. .scratch/harness/probes/composer_effort_labels.ps1, 2026-10-16). Ultracode 는
# 고르지 않는다.
# 줄 머리에서 시작하는 줄만 본다. 지시문 형식은 불릿이나 인용 없이 줄 머리이고, 다른 칸의 글 속 `모델:` 은 줄이 아니다.
# 결정표의 칸(`Opus 5.5 / xhigh`)을 그대로 옮긴 줄도 읽도록 백틱을 벗긴다(hook_prompt_directive 가 `브랜치:` 값에서 하는 것과 같다).
function Get-EffortSteps { return @('low', 'medium', 'high', 'xhigh', 'max') }

# 노력 칸의 이름(앱 2.37337.1.0, 한국어). Get-EffortSteps 와 차례가 같다. 입력창의 모델 버튼은 이 이름을 자식 Text 로 보이고
# (Split-ComposerTexts), 노력 하위 메뉴의 항목은 이름 뒤에 덧붙임이 붙을 수 있다(`중간 추천`, `최대 3.5× 이상 사용량`).
function Get-EffortLabels { return @('낮음', '중간', '높음', '엑스트라', '최대') }

# 노력 칸 이름의 차례. 목록 밖이면(Ultracode, 앱이 바꾼 이름) $null 이고, 그 칸은 스크립트가 고르지도 되돌리지도 않는다.
function Get-EffortLabelStep([string] $label) {
    $i = [array]::IndexOf((Get-EffortLabels), $label)
    if ($i -lt 0) { return $null }
    return $i
}

# 입력창의 `모델:` 버튼 하나가 모델과 노력을 함께 보인다(앱 2.37337.1.0). 이름은 `최대` 칸에서 `모델: Opus 5.5 최대 3.5× 이상
# 사용량` 이라 이름으로는 모델과 노력을 가르지 못하고, 자식 Text 가 [모델, 공백, 노력] 이다(composer_effort_labels.ps1,
# 2026-10-16). 고속 모드가 켜지면 그 사이에 `빠름` 이 들었다(composer_menu_tree.ps1, 같은 날). 그래서 공백이 아닌 첫 글을 모델로,
# 마지막 글을 노력으로 읽는다. 둘보다 적으면 앱이 모양을 바꾼 것이라 멈춘다. 보내기 전에 멈춰 사람이 값을 맞춰 보낸다. 마지막 글이
# 노력 칸이 아니면(Ultracode, 노력이 없는 모양) Get-EffortLabelStep 이 $null 을 내어 그 칸은 되돌리지 않는다.
function Split-ComposerTexts([string[]] $texts) {
    $parts = @($texts | Where-Object { $_ -and $_.Trim() } | ForEach-Object { $_.Trim() })
    if ($parts.Count -lt 2) { throw "모델 버튼의 글이 [모델, 노력] 보다 적다([$($texts -join '|')]). 앱이 입력창의 모양을 바꿨다." }
    return [pscustomobject]@{ Model = $parts[0]; EffortLabel = $parts[-1] }
}

# 메뉴 항목의 이름이 그 칸인지. 이름이 같거나 이름 뒤에 공백과 덧붙임이 온다(`Sonnet 5.5 기본값`, `중간 추천`).
function Test-NameShows([string] $name, [string] $label) {
    return [bool]($name -and ($name -ceq $label -or $name.StartsWith("$label ", [StringComparison]::Ordinal)))
}

function Read-ModelLine([string] $prompt) {
    $steps = Get-EffortSteps
    $lines = @($prompt -split "`r?`n" | Where-Object { $_.StartsWith('모델:') })
    if ($lines.Count -eq 0) { return $null }
    if ($lines.Count -gt 1) { throw "모델: 줄이 $($lines.Count)개다. 지시문 하나에 하나만 둔다." }
    $form = "형식은 '모델: <모델 메뉴의 이름> / <$($steps -join '|')>' 다"
    $line = $lines[0].Replace('`', '')
    if ($line -cnotmatch '^모델:(?<model>[^/]*)/\s*(?<effort>[A-Za-z]+)(?![A-Za-z])') { throw "모델: 줄을 읽지 못했다('$($lines[0])'). $form." }
    $model = $Matches['model'].Trim()
    $effort = $Matches['effort']
    if (-not $model) { throw "모델: 줄에 모델 이름이 없다('$($lines[0])'). $form." }
    if ($steps -cnotcontains $effort) { throw "모델: 줄의 레벨 '$effort' 를 모른다. $form." }
    return [pscustomobject]@{ Model = $model; Effort = $effort; Step = [array]::IndexOf($steps, $effort) }
}

# 지시문 입력창과 같은 입력창 묶음의 버튼(`모델: …`). 분할 보기면 패널마다 입력창이 있어 창 전체에서 찾으면 다른
# 세션의 버튼을 누른다. 입력창에서 위로 올라가며 그 이름의 버튼이 처음 보이는 조상에서 하나일 때만 돌려준다.
function Find-ComposerButton($box, [string] $prefix) {
    $walker = [System.Windows.Automation.TreeWalker]::ControlViewWalker
    $buttonCond = New-Object System.Windows.Automation.PropertyCondition($Auto::ControlTypeProperty, $Types::Button)
    $node = $box
    for ($i = 0; $i -lt 20 -and $node; $i++) {
        $node = $walker.GetParent($node)
        if (-not $node) { break }
        $hits = @($node.FindAll($Scope::Descendants, $buttonCond) | Where-Object { try { $_.Current.Name.StartsWith($prefix) } catch { $false } })
        if ($hits.Count -gt 1) { throw "지시문 입력창 가까이에 '$prefix' 버튼이 $($hits.Count)개다. 어느 것이 새 세션의 것인지 가를 수 없다." }
        if ($hits.Count -eq 1) { return $hits[0] }
    }
    return $null
}

function Get-EditValue($el) {
    try { return $el.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value } catch { return '' }
}

# 입력창 묶음의 모델 버튼이 지금 보이는 모델과 노력. 자식 Text 로 읽는다(Split-ComposerTexts 의 주석).
function Read-ComposerButton($button) {
    $textCond = New-Object System.Windows.Automation.PropertyCondition($Auto::ControlTypeProperty, $Types::Text)
    return Split-ComposerTexts @($button.FindAll($Scope::Children, $textCond) | ForEach-Object { $_.Current.Name })
}

# 입력창 묶음의 모델 버튼이 -Model 이나 -EffortLabel 로 준 것을 보이면 그 버튼, 아니면 $null. 주지 않은 쪽은 보지 않는다.
# Wait-For 가 부른다. 버튼을 못 읽는 것은 아직 다시 그려지는 중일 수 있어 맞지 않는 것으로 친다.
function Find-ComposerShowing($box, [string] $Model, [string] $EffortLabel) {
    $button = Find-ComposerButton $box '모델:'
    if (-not $button) { return $null }
    try { $read = Read-ComposerButton $button } catch { return $null }
    if ($Model -and $read.Model -cne $Model) { return $null }
    if ($EffortLabel -and $read.EffortLabel -cne $EffortLabel) { return $null }
    return $button
}

# 모델 메뉴와 노력 하위 메뉴의 항목은 RadioButton 이고 이름 뒤에 덧붙임이 붙을 수 있다(`Sonnet 5.5 기본값`, `중간 추천`,
# .scratch/harness/probes/composer_menu_tree.ps1). 그래서 Test-NameShows 로 고른다. 메뉴는 입력창 묶음이 아니라 창 전체에서
# 찾는다. 한 번에 하나만 열려 있고, 방금 연 것이 그것이다.
function Find-MenuRadio($win, [string] $label) {
    $radioCond = New-Object System.Windows.Automation.PropertyCondition($Auto::ControlTypeProperty, $Types::RadioButton)
    return @($win.FindAll($Scope::Descendants, $radioCond) | Where-Object { try { Test-NameShows $_.Current.Name $label } catch { $false } }) | Select-Object -First 1
}

# 펼친 메뉴의 항목을 고른다. 모델 항목을 고르면 모델 메뉴가, 노력 항목을 고르면 하위 메뉴와 모델 메뉴가 함께 스스로 닫혔다
# (composer_patterns.ps1·composer_effort_labels.ps1 의 menu-open-after-select·model-menu-state-after 줄, 2026-10-16).
function Select-MenuRadio($win, [string] $label, [string] $what) {
    $item = Wait-For { Find-MenuRadio $win $label } "${what}의 '$label'" 5
    if (-not $item.Current.IsEnabled) { throw "${what}의 '$($item.Current.Name)'가 비활성이다. 사람이 메뉴를 보고 판단한다." }
    $chosen = Invoke-PatternTimed $item 'select'
    if ($chosen -ne 'ok') { throw "${what}의 '$label'을 고르지 못했다($chosen)." }
}

# 입력창 묶음의 모델 버튼이 그 모델을 보이게 한다. 이미 그 모델이면 메뉴를 열지 않는다. 바꾼 뒤 버튼의 글로 맞았는지 본다.
function Select-ComposerModelItem($win, $box, [string] $model) {
    $button = Wait-For { Find-ComposerButton $box '모델:' } '입력창의 모델 버튼' 5
    if ((Read-ComposerButton $button).Model -ceq $model) { return }
    $opened = Invoke-PatternTimed $button 'expand'
    if ($opened -ne 'ok') { throw "모델 메뉴를 펼치지 못했다($opened)." }
    # 메뉴를 연 뒤 멈추면 메뉴가 열린 채 남는다. 닫고 던진다.
    try { Select-MenuRadio $win $model '모델 메뉴' }
    catch {
        Invoke-PatternTimed $button 'collapse' | Out-Null
        throw
    }
    Wait-For { Find-ComposerShowing $box -Model $model } "'$model' 을 보이는 모델 버튼" 5 | Out-Null
}

# 입력창 묶음의 모델 버튼이 그 노력 칸을 보이게 한다. 노력은 모델 메뉴 안의 `노력 <이름>` 하위 메뉴의 항목이다(앱 2.37337.1.0).
# 이미 그 칸이면 메뉴를 열지 않는다. 바꾼 뒤 버튼의 글로 맞았는지 본다. 칸이 그 모델의 메뉴에 없으면 항목을 찾지 못해 멈춘다.
function Select-ComposerEffortItem($win, $box, [int] $step) {
    $label = (Get-EffortLabels)[$step]
    $button = Wait-For { Find-ComposerButton $box '모델:' } '입력창의 모델 버튼' 5
    if ((Read-ComposerButton $button).EffortLabel -ceq $label) { return }
    $opened = Invoke-PatternTimed $button 'expand'
    if ($opened -ne 'ok') { throw "모델 메뉴를 펼치지 못했다($opened)." }
    $trigger = $null
    try {
        $trigger = Wait-For { Find-EffortSubmenu $win } "모델 메뉴의 '노력' 항목" 5
        Open-EffortSubmenu $win $trigger
        # 열렸는지를 항목보다 먼저 본다. 열리지 않은 것(창이 뒤에 있다)과 그 모델의 메뉴에 그 칸이 없는 것을 가른다. 항목은 매번
        # 다시 찾는다. 다시 그려져 낡은 요소는 상태를 읽지 못해 열린 메뉴를 놓친다.
        Wait-For { $t = Find-EffortSubmenu $win; if ($t -and (Test-Expanded $t)) { $t } } '열린 노력 하위 메뉴(Claude 창이 앞에 있어야 열린다)' 3 | Out-Null
        Select-MenuRadio $win $label '노력 메뉴'
    } catch {
        if ($trigger -and (Test-Expanded $trigger)) { Invoke-PatternTimed $trigger 'collapse' | Out-Null }
        Invoke-PatternTimed $button 'collapse' | Out-Null
        throw
    }
    Wait-For { Find-ComposerShowing $box -EffortLabel $label } "'$label' 을 보이는 모델 버튼" 5 | Out-Null
}

function Test-Expanded($el) {
    try { return [bool]($el.GetCurrentPattern([System.Windows.Automation.ExpandCollapsePattern]::Pattern).Current.ExpandCollapseState -eq 'Expanded') } catch { return $false }
}

function Find-EffortSubmenu($win) {
    $menuItemCond = New-Object System.Windows.Automation.PropertyCondition($Auto::ControlTypeProperty, $Types::MenuItem)
    return @($win.FindAll($Scope::Descendants, $menuItemCond) | Where-Object { try { $_.Current.Name.StartsWith('노력', [StringComparison]::Ordinal) } catch { $false } }) | Select-Object -First 1
}

# 노력 하위 메뉴는 펼치기 패턴으로 열리지 않는다. 펼치기는 돌아오지만 상태가 Collapsed 로 남고 새 요소가 0개였다
# (composer_menu_tree.ps1 -Effort 의 `after expand-pattern` 줄, 2026-10-16). 그래서 그 항목에 포커스를 준 뒤 → 키를 PostMessage 로
# Claude 창 핸들에 넣는다. SendKeys 는 앞에 있는 창으로 가지만 PostMessage 는 "지정한 창을 만든 스레드의 메시지 큐"에 넣는
# Win32 호출이라(learn.microsoft.com 의 PostMessageW 문서 원문을 받아 대 봤다, 2026-10-16) 다른 앱으로 가지 않는다.
# Claude 창이 앞에 없으면 하위 메뉴가 열리지 않았다. 메모장을 앞에 둔 composer_menu_tree.ps1 -Effort -Behind 한 회차였고, 같은
# 고속 모드 화면에서 창이 앞에 있던 회차는 열렸다. 모델 메뉴를 펼치면 앱이 창을 스스로 앞으로 올렸다(메모장을 앞에 둔
# composer_patterns.ps1 -Background 에서 첫 펼치기 직후의 `after-expand` 줄이 True, 2026-10-16 한 회차). 열리지 않으면 부르는
# 쪽이 열린 하위 메뉴를 기다리다 멈추고 보내지 않는다.
function Open-EffortSubmenu($win, $trigger) {
    $WM_KEYDOWN = 0x0100
    $WM_KEYUP = 0x0101
    $VK_RIGHT = 0x27
    # lParam: 반복 횟수 1, 스캔 코드 0x4D(16~23비트), 확장 키(24비트). 뗄 때는 이전 상태·전이 비트(30·31)를 더한다.
    $downInfo = 0x014D0001
    $upInfo = [int64]0xC14D0001
    $trigger.SetFocus()
    Start-Sleep -Milliseconds 300
    $window = [IntPtr]$win.Current.NativeWindowHandle
    # 핸들이 0이면 PostMessage 는 부른 스레드의 큐에 넣고 참을 낸다. 받는 창이 더 높은 권한이면(UIPI) 거짓을 낸다. 둘 다 창이 뒤에
    # 있다는 안내로 잘못 읽히지 않게 여기서 멈춘다.
    if ($window -eq [IntPtr]::Zero) { throw 'Claude 창의 핸들을 읽지 못해 노력 하위 메뉴를 열 키를 넣지 못했다.' }
    $down = [OpenSessionKeys]::PostMessage($window, $WM_KEYDOWN, [IntPtr]$VK_RIGHT, [IntPtr]$downInfo)
    $up = [OpenSessionKeys]::PostMessage($window, $WM_KEYUP, [IntPtr]$VK_RIGHT, [IntPtr]$upInfo)
    if (-not ($down -and $up)) { throw "Claude 창에 노력 하위 메뉴를 열 키를 넣지 못했다(PostMessage down=$down up=$up. 앱이 더 높은 권한으로 돌면 그렇다)." }
}

# 새 세션 입력창에 지금 있는 모델과 노력(앱이 기억한 새 세션 화면의 기본값). 고르기 전에 읽어 두고, 보낸 뒤
# Restore-DraftDefaults 가 이 값으로 되돌린다. 노력의 칸은 모델 버튼의 글로 읽고, 이름이 Get-EffortLabels 밖이면(Ultracode)
# 칸은 $null 이고 되돌리지 않는다. 고르기를 시작하기 전에 따로 읽는 것은, 고르다 던져도 부르는 쪽이 원래 값을 알아야
# 사람에게 복구를 남길 수 있어서다.
function Read-DraftDefaults($box) {
    $button = Wait-For { Find-ComposerButton $box '모델:' } '지시문 입력창의 모델 버튼' 5
    $read = Read-ComposerButton $button
    return [pscustomobject]@{
        Model = $read.Model
        EffortStep = Get-EffortLabelStep $read.EffortLabel
        EffortLabel = $read.EffortLabel
    }
}

# 고른 값이 원래 값과 다른지. 같으면 기본값이 바뀌지 않으므로 되돌리지 않는다(같은 값이 흔하다). 다르면 고르다 멈췄어도
# 바뀌었을 수 있는 것으로 친다.
function Test-DraftChanged($draft, $pick) {
    return [bool](($draft.Model -cne $pick.Model) -or ($draft.EffortStep -ne $pick.Step))
}

# 고른 뒤 `sent=` 전에 멈춘 길(`held=`, 고르기·보내기 버튼·제출 확인의 실패)이 남기는 복구 줄. 원래 값을 읽기 전($draft 없음)이나
# 고른 값이 원래 값과 같으면 기본값이 그대로라 아무것도 내지 않는다. 두 길이 같은 조건과 문장을 쓰도록 여기 한 곳에 둔다.
function Get-PendingRestoreLine($draft, $pick) {
    if (-not $draft -or -not (Test-DraftChanged $draft $pick)) { return }
    return "restore=필요: 새 세션 화면의 기본값이 바뀌었을 수 있다. 사람이 보낸 뒤 $(Get-RepairHint $draft)"
}

# 지시문의 모델 줄대로 새 세션 입력창의 모델과 노력을 고른다. 딥링크는 모델을 싣지 못하고(앱의 `code/new` 처리기는
# q·prompt·folder·file 과 SSH 인자만 읽는다, 앱 2.19675.0.0 번들을 읽었다. 2.37337.1.0 은 그 밖에 출처를 적는 source 를 더 읽는다),
# 보낸 뒤 바꾸는 도구는 다음 턴부터라 첫 턴에 늦다.
# 모델을 먼저 고른다. 모델을 바꾸면 노력이 그 모델의 값으로 바뀔 수 있다. 모델과 노력은 입력창의 모델 버튼이 보이는 글로
# 맞았는지 보고, 아니면 보내지 않고 멈춘다. 앱이 칸의 이름을 바꾸면 항목을 찾지 못해 여기서 멈춘다. 앞에 있는 창으로 가는
# 키는 쓰지 않는다(Invoke-PatternTimed 의 주석). 고속 모드 체크박스와 노력 메뉴의 Ultracode 칸은 건드리지 않는다.
# 새 세션 화면의 모델과 노력은 앱이 다음 새 세션 화면의 기본값으로 기억하고, 노력은 보내지 않고 옮기기만 해도 남는다
# (.scratch/harness/probes/composer_effort_labels.ps1 로 손으로 봤다, 2026-10-12, 슬라이더였던 앱 2.19675.0.0). 그래서 부르는
# 쪽이 고르기 전의 값을 Read-DraftDefaults 로 읽어 두고 보낸 뒤 Restore-DraftDefaults 가 되돌린다. $draft 는 진행 줄에 원래
# 값을 적는 데만 쓴다.
function Set-ComposerModel($win, $box, $pick, $draft) {
    Select-ComposerModelItem $win $box $pick.Model
    "model=$($pick.Model) 원래 $($draft.Model)"
    Select-ComposerEffortItem $win $box $pick.Step
    $before = if ($null -eq $draft.EffortStep) { "$($draft.EffortLabel)(되돌리지 않는다)" } else { (Get-EffortSteps)[$draft.EffortStep] }
    "effort=$($pick.Effort) 원래 $before"
}

# 표지 글이 든 새 세션 화면을 연다. 보내지 않는 화면이라 그 입력창의 버튼만 움직이고, 끝나면 Clear-PromptBox 로 표지를 지운다.
function Open-MarkerDraft($win, [string] $purpose) {
    $marker = "open-session-$purpose-$(Get-Date -Format HHmmssfff)"
    Start-Process ('claude://code/new?q=' + [uri]::EscapeDataString($marker))
    return Wait-For { Find-PromptBox $win $marker } "표지('$marker')가 든 새 세션 입력창" 10
}

# 표지를 지운다. 키(`^a{DELETE}`)가 아니라 값을 비운다. 키는 그 순간 앞에 있는 앱으로 가서 다른 앱의 글을 지울 수 있다.
# 던지지 않는다. 표지가 남는 것은 해가 없고, 지우기의 실패가 앞서 끝난 고르기를 실패로 보이게 하면 안 된다. 지웠는지는
# Test-PromptBoxEmpty 로 본다.
function Clear-PromptBox($box) {
    try { $box.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).SetValue('') } catch { return }
    Start-Sleep -Milliseconds 200
}

function Test-PromptBoxEmpty($box) {
    return -not (Get-EditValue $box).Trim()
}

function Get-LeftoverNote($box) {
    if (Test-PromptBoxEmpty $box) { return '' }
    return ' 표지 글이 새 세션 화면에 남았다(해는 없다).'
}

# 새 세션 화면의 기본값을 고르기 전($draft)으로 돌리는 사람의 길. 원래 노력이 Get-EffortLabels 밖이면 스크립트가 고르지
# 않는 칸이라(Ultracode) 명령 대신 화면에서 고르라고 한다.
function Get-RepairHint($draft) {
    if ($null -eq $draft.EffortStep) { return "새 세션 화면에서 모델을 '$($draft.Model)' 로, 노력을 원래 값으로 고른다" }
    return "친다: pwsh -NoProfile -File tools/open_session.ps1 -Action defaults -Model '$($draft.Model)' -Effort $((Get-EffortSteps)[$draft.EffortStep])"
}

# 보낸 뒤 새 세션 화면의 모델과 노력 기본값을 고르기 전($draft)으로 되돌린다(Set-ComposerModel 의 주석). 세션은 이미
# 열렸으므로 실패해도 멈추지 않고 사람의 길(Get-RepairHint)을 한 줄로 남긴다. 표지 화면은 스킬의 5단계(split·focus)가 새
# 세션으로 덮는다. 원래 노력이 목록 밖이면 모델만 되돌린다. 고른 값이 원래 값과 같았으면 화면을 열지 않는다.
function Restore-DraftDefaults($win, $draft, $pick) {
    if (-not (Test-DraftChanged $draft $pick)) { return 'restored=바뀐 것 없음(고른 값이 원래 값과 같았다)' }
    $left = ''
    try {
        $box = Open-MarkerDraft $win 'restore'
        try {
            Select-ComposerModelItem $win $box $draft.Model
            if ($null -ne $draft.EffortStep) { Select-ComposerEffortItem $win $box $draft.EffortStep }
        } finally {
            Clear-PromptBox $box
            $left = Get-LeftoverNote $box
        }
    } catch {
        return "restore=실패: $($_.Exception.Message) 사람이 $(Get-RepairHint $draft)"
    }
    if ($null -eq $draft.EffortStep) { return "restored=$($draft.Model). 원래 노력은 스크립트가 고르지 않는 칸이라 두었다. 사람이 $(Get-RepairHint $draft)$left" }
    return "restored=$($draft.Model) / $((Get-EffortSteps)[$draft.EffortStep])$left"
}

# 새 세션 화면의 모델과 노력 기본값을 맞춘다. 되돌리기가 실패했을 때의 복구다. 표지 화면을 열어 고르고 표지를 지운다.
function Set-Defaults {
    if (-not $Model -or -not $Effort) { throw 'defaults 에는 -Model 과 -Effort 가 필요하다.' }
    $pick = Read-ModelLine "모델: $Model / $Effort"
    $win = Get-ClaudeWindow
    $box = Open-MarkerDraft $win 'defaults'
    $left = ''
    try { Set-ComposerModel $win $box $pick (Read-DraftDefaults $box) }
    finally {
        Clear-PromptBox $box
        $left = Get-LeftoverNote $box
    }
    "defaults=$Model / $Effort$left"
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
    # 세 번 다 닫혔으면 옆 패널을 포기하고 그 세션 행을 눌러 메인 패널에 포커스로 띄운다.
    $rowButton = $null
    try { $rowButton = Find-RowByTitle $win $Title } catch {}
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
        # Get-ClaudeWindow 와 같은 가드. 잡은 다른 런스페이스라 함수를 못 쓴다. 창이 둘이면 조용히 고르지 않는다.
        $wins = @($Auto::RootElement.FindAll($Scope::Children, [System.Windows.Automation.Condition]::TrueCondition) | Where-Object { $_.Current.Name -eq 'Claude' })
        if ($wins.Count -ne 1) { return "window-ambiguous:$($wins.Count)" }
        $row = $wins[0].FindFirst($Scope::Descendants, (New-Object System.Windows.Automation.PropertyCondition($Auto::NameProperty, $name)))
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

# 사이드바 행 버튼. 이름은 "<상태> <제목>"("유휴 …", "실행 중 …", "#30 · 열기 …")이라 끝이 제목인 버튼을 찾는다.
# 옵션 버튼은 "…에 대한 더 많은 옵션"이라 안 걸린다. 이름은 한 번만 읽는다(두 번 읽는 사이 요소가 바뀐 적이 있다).
function Find-RowByTitle($win, [string] $title, [int] $seconds = 10) {
    $rowCond = New-Object System.Windows.Automation.PropertyCondition($Auto::ControlTypeProperty, $Types::Button)
    return Wait-For { $win.FindAll($Scope::Descendants, $rowCond) | Where-Object { try { $n = $_.Current.Name; $n -and $n.EndsWith(" ${title}") } catch { $false } } | Select-Object -First 1 } "행 '${title}'" $seconds
}

function Focus-Session {
    if (-not $Title) { throw 'focus 에는 -Title 이 필요하다.' }
    $win = Get-ClaudeWindow
    # 새 세션은 첫 턴에 스스로 이름을 붙이므로(hook_prompt_directive) 행이 그 제목이 되기까지 기다린다.
    $rowButton = Find-RowByTitle $win $Title $TimeoutSec
    $how = Invoke-Row $rowButton.Current.Name
    if ($how -ne 'invoke') { throw "행 '${Title}'을 누르지 못했다($how)." }
    "focus=$(Get-Date -Format HH:mm:ss.fff) via $how"
}

# 모니터가 꺼져 있으면 앱(Electron)이 창을 가려진 것으로 보고 그리지 않는다. 딥링크가 와도 새 세션 화면이
# 접근성 트리에 오르지 않아 `page=`에서 끝난다. 사람이 자리를 비워 입력 없이 30분(이 PC의 화면 끄기 설정)이
# 지나면 그렇게 된다 — "잘 되다가 갑자기"의 정체다(2026-09-23 실측, 04→05와 →06 두 번 다 그 조건이었다).
# 실측: 모니터를 끄고 쏘면 두 번 다 못 찾았고, 아래 호출 뒤에 쏘면 두 번 다 1.2초에 찾았다. `split`·`focus`는
# 재지 않았지만 같은 화면의 메뉴와 행을 누르므로 함께 깨운다. 잠금 화면은 이 호출로 풀리지 않는다. `idle=`은
# 마지막 입력 뒤의 초라 다음 실패의 첫 단서다. 깨우기는 돕는 일이라 실패해도 본 동작을 막지 않는다. 두 호출은
# 실패를 반환값으로 알리므로 반환값으로 가르고, 드물게 예외가 나도 받는다. 어느 쪽이 실패해도 먼저 읽은 단서는
# 남긴다(PR #62 리뷰 넷: try 가 단서를 삼킨다, 반환값을 버린다 둘, try 가 없다).
function Wake-Display {
    $line = 'idle=?'
    try {
        $idle = [OpenSessionPower]::IdleSeconds()
        if ($idle -ge 0) { $line = "idle=${idle}s" }
        # ES_SYSTEM_REQUIRED(0x1) | ES_DISPLAY_REQUIRED(0x2). ES_CONTINUOUS 없이 한 번 되돌리기만 하고 켜 두지 않는다.
        # 실패하면 0 이다.
        if ([OpenSessionPower]::SetThreadExecutionState(0x3) -eq 0) { $line += ' 화면을 깨우지 못했다(SetThreadExecutionState 가 0)' }
    } catch {
        $line += " 화면을 깨우지 못했다: $($_.Exception.Message)"
    }
    $line
}

# 앱이 끝나는 중이면 딥링크를 받지 않는다. 데스크톱 앱(2.9939.2)의 `second-instance` 처리기는 첫 줄 `if(ej())return;` 에서
# 끝내기 깃발 셋(`JA||YA||XA`)을 보고 로그 없이 돌아간다. 딥링크를 받은 두 번째 인스턴스는 제 기동 줄(`Starting app` 에서
# `Not main instance` 까지)만 남기고 물러나므로 스크립트는 `page=` 에서 원인 없이 끝난다. 깃발 가운데 업데이트를 위한
# 끝내기(`JA`)와 끝낼 준비(`XA`)는 한 번 켜지면 풀리는 자리가 없다. 업데이트를 위한 끝내기가 시작되고 앱이 끝나지 않으면, 밖에서
# 앱을 끝낼 때까지 모든 딥링크가 버려졌다(2026-09-29 12:19 부터 32시간 넘게). 앱 안의 재시작(업데이트 배너, 메뉴의 끝내기)도
# 같은 깃발에 막힌다(`QA`·`$A` 의 `ej()||`). 설치본의 app.asar 와 main.log 를 읽었다. 경위는 일지 2026-09-30-06. 그래서 쏘기
# 전에 앱의 로그에서 주 프로세스가 선 뒤의 끝내기 표지를 찾는다.
#
# 이 함수는 순수하다. 로그 줄과 주 프로세스가 선 시각을 받아, 그 뒤에 선 표지 줄 가운데 가장 이른 것을 `시각 메시지` 로
# 준다. 없으면 null 이다. 시각이 없는 줄(여러 줄 객체의 속)은 건너뛴다. 표지는 `JA`·`XA` 를 켠 뒤의 줄이다.
#   - `beforeQuitForUpdate handler fired`: 자동 업데이트가 끝내기 직전에 부르는 처리기가 `JA` 를 켰다.
#   - `Update check still in flight`, `Session stop before update took`, `CLI exit before update`: 업데이트를 위한 끝내기
#     함수(`Hln`, 배너와 스텔스 업데이트가 함께 부른다)가 첫 줄에서 `JA` 를 켠 뒤에 찍는다. 마지막 것은 로컬 CLI 세션이 있을
#     때만 찍힌다.
#   - `marking readyForQuit`: 끝내기 정리를 마쳐 `XA` 를 켰다.
# 끝내기 처리기가 도는 중(`YA`)의 표지는 보지 않는다. 정리가 끝나면 실패해도 풀려(`finally`), 로그에 남은 표지가 지금 켜져 있다는
# 뜻이 아니다. 못 보는 것: 문구가 바뀐 판의 끝내기, `JA` 를 켜고 표지를 찍기 전에 멈춘 끝내기. 그때는 전처럼 `page=` 에서 끝난다.
function Find-QuitMarker([string[]] $Lines, [datetime] $Since) {
    $markers = 'beforeQuitForUpdate handler fired|Update check still in flight|Session stop before update took|CLI exit before update|marking readyForQuit'
    foreach ($line in $Lines) {
        if ($line -notmatch '^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d) \[\w+\] (.*)$') { continue }
        $time = $Matches[1]
        $message = $Matches[2]
        $at = [datetime]::ParseExact($time, 'yyyy-MM-dd HH:mm:ss', [cultureinfo]::InvariantCulture)
        if ($at -ge $Since -and $message -match $markers) { return "$time $message" }
    }
    return $null
}

# 도는 앱의 주 프로세스가 선 시각. 주 프로세스는 `app\Claude.exe` 가운데 `--type=` 이 없는 가장 오래된 것이다. 딥링크마다
# 잠깐 뜨는 두 번째 인스턴스도 같은 모양이지만 더 늦게 선다. 같은 이름의 CLI(`claude.exe`)는 경로가 다르다. 없으면 null 이다.
# 시각을 모르는 앱 프로세스가 하나라도 있으면 정렬이 그것을 맨 앞에 두어 null 이다. 어느 것이 먼저 섰는지 모르면 두 번째 인스턴스를
# 고를 수 있어 판정하지 않는다. 순수하다. 프로세스는 `Get-AppQuitMarker` 가 찾아 넘긴다.
function Find-MainStart($Processes) {
    $main = @($Processes |
        Where-Object { $_.ExecutablePath -match '\\app(-[\d.]+)?\\Claude\.exe$' -and $_.CommandLine -notmatch '--type=' } |
        Sort-Object CreationDate)
    if ($main.Count -eq 0) { return $null }
    return $main[0].CreationDate
}

# 끝내기 표지를 찾을 로그 파일. 후보 폴더마다 `main.log`(Main)와 그 옆 돌림 파일 `main1.log`(Rotated)의 경로와 마지막으로
# 쓰인 시각(MainWritten·RotatedWritten, 없는 파일이면 null)을 받아, `main.log` 가 가장 최근에 쓰인 폴더의 두 파일 가운데
# 주 프로세스가 선 뒤($Since)에 쓰인 것을 앞선 줄이 든 돌림 파일부터 준다. 표지가 돌림 파일로 밀렸을 수 있어 그것도 읽되, 서기
# 전에 마지막으로 쓰인 돌림 파일은 볼 것이 없어 건너뛴다(10MB 인 그 파일까지 읽으면 판정 전체가 2.66초였다, 셀프 리뷰).
# `main.log` 가 없는 폴더는 고르지 않는다. 순수하다. 파일은 `Get-AppQuitMarker` 가 찾아 넘긴다.
function Select-QuitLogs($Dirs, [datetime] $Since) {
    $latest = @($Dirs | Where-Object { $null -ne $_.MainWritten } | Sort-Object MainWritten -Descending) | Select-Object -First 1
    if ($null -eq $latest) { return }
    if ($null -ne $latest.RotatedWritten -and $latest.RotatedWritten -ge $Since) { $latest.Rotated }
    if ($latest.MainWritten -ge $Since) { $latest.Main }
}

# 도는 앱의 주 프로세스가 선 뒤에 끝내기 표지가 있으면 그 줄, 없으면 null 이다. 주 프로세스나 로그를 못 찾으면 null 이다
# (판정하지 못하면 막지 않는다. 판정 중의 예외는 부르는 쪽이 `quitcheck=` 로 남기고 지나간다). 로그의 후보 폴더는 MSIX
# 설치(`Packages\Claude_*`)와 일반 설치(`%APPDATA%\Claude`)다. 무엇을 고를지는 `Find-MainStart`·`Select-QuitLogs` 가 정하고,
# 여기서는 프로세스와 파일을 찾아 넘긴다.
function Get-AppQuitMarker {
    $started = Find-MainStart @(Get-CimInstance Win32_Process -Filter "Name = 'Claude.exe'" -ErrorAction SilentlyContinue)
    if ($null -eq $started) { return $null }
    $dirs = @(Get-ChildItem -Path "$env:LOCALAPPDATA\Packages" -Directory -Filter 'Claude_*' -ErrorAction SilentlyContinue |
        ForEach-Object { Join-Path $_.FullName 'LocalCache\Local\Claude\logs' }) + @("$env:APPDATA\Claude\logs")
    $writtenAt = { param($path) if (Test-Path -LiteralPath $path) { (Get-Item -LiteralPath $path).LastWriteTime } }
    $logs = foreach ($dir in $dirs) {
        $log = Join-Path $dir 'main.log'
        $rotated = Join-Path $dir 'main1.log'
        [pscustomobject]@{ Main = $log; MainWritten = & $writtenAt $log; Rotated = $rotated; RotatedWritten = & $writtenAt $rotated }
    }
    $lines = foreach ($file in (Select-QuitLogs @($logs) $started)) { Get-Content -LiteralPath $file -Encoding UTF8 }
    return Find-QuitMarker @($lines) $started
}

# 스크립트의 끝. 멈춘 접근성 호출이 남았으면(Invoke-PatternTimed 의 주석) pwsh 가 그 스레드를 기다려 끝나지 않는다. 출력과 오류
# 문구를 낸 뒤 프로세스를 끝낸다. 남은 호출이 없으면 여느 때처럼 끝나고 오류도 그대로 던진다.
function Invoke-Action([scriptblock] $run) {
    try { & $run }
    catch {
        if ($script:HungCalls -eq 0) { throw }
        [Console]::Error.WriteLine("$($_.Exception.Message) (멈춘 접근성 호출 $script:HungCalls 개가 남아 프로세스를 끝낸다)")
        [Environment]::Exit(1)
    }
    if ($script:HungCalls -gt 0) { [Environment]::Exit(0) }
}

Wake-Display
Invoke-Action {
    switch ($Action) {
        'send' { Send-Prompt }
        'split' { Split-Session }
        'focus' { Focus-Session }
        'defaults' { Set-Defaults }
    }
}
