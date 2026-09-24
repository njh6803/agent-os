# open-session 스킬의 손발. 데스크톱 앱에 새 Code 세션을 연다. 첫 줄이 이 저장소의 스킬을 부르는 슬래시
# 명령이면 쏘기 전에 그 스킬 파일을 읽어 따르라는 한 줄로 옮겨(`Convert-StartLine`) 사람 손 없이 보낸다.
# 옮기지 못한 슬래시 명령은 앱이 `/` 를 전각으로 바꿔 넣으므로 보내기 전에 멈추고(`held=`) 사람이 고쳐 보낸다.
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
        "start=$($startLine.Substring(0, $startLine.IndexOf(' ')))"
    }
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

    # 앱은 링크로 온 슬래시 명령을 그대로 실행하지 않는다. 첫 `/` 를 전각 `／`(U+FF0F)로 바꿔 넣어,
    # 그대로 보내면 명령이 아니라 글자가 된다 — `/implement` 가 사용자 호출로 먹지 않는다(2026-09-23 실측,
    # 입력창의 값 첫 글자가 U+FF0F). 스크립트는 되돌려 넣지 않는다. 어디서 왔는지 모르는 링크가 명령을
    # 일으키지 못하게 한 앱의 장치를 통째로 우회하는 일이다 — 되돌린 `/` 는 내장 명령을 포함해 아무 슬래시
    # 명령이나 일으킨다. 위의 `Convert-StartLine` 도 효과로는 그 장치를 비껴가지만 가리킬 수 있는 것이 이
    # 저장소의 스킬 파일뿐이다. 그렇게 옮긴 것은 여기 오지 않으므로, 여기 걸리는 것은 옮기지 못한 슬래시
    # 명령뿐이다(스킬 파일이 없다).
    # 보내기를 누르지 않고 멈춘다. 스킬이 사람에게 부탁하고 턴을 끝낸다.
    $value = try { $box.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value } catch { '' }
    if ($value -and [int][char]$value[0] -eq 0xFF0F) {
        "held=$(Get-Date -Format HH:mm:ss.fff) 입력창의 첫 글자가 U+FF0F 다(옮기지 못한 슬래시 명령). 사람이 / 로 고쳐 보낸다"
        return
    }

    $send = Wait-For { Find-EnabledSendButton $win } '활성 보내기 버튼'
    $how = Press-Element $send
    Wait-For {
        try { -not (Test-Needle ($box.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value) $needle) } catch { $false }
    } '제출된 뒤 비워진 입력창(요소를 못 읽으면 비운 것으로 치지 않는다)' 10 | Out-Null
    "sent=$(Get-Date -Format HH:mm:ss.fff) via $how"
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
# 옮기지 않아 아래 `held=` 가 받는다.
# 문구는 hook_prompt_directive 의 대체 안내와 같은 뜻이다. 인자에 지시문 전문이 드는 것도 슬래시 명령과 같다.
function Convert-StartLine([string] $line, [string] $root) {
    if ($root -and $line -cmatch '^/([a-z0-9][a-z0-9-]*)(?:\s+(.*))?$') {
        $skill = ".claude/skills/$($Matches[1])/SKILL.md"
        $rest = $Matches[2]
        if (Test-Path -LiteralPath (Join-Path $root $skill) -PathType Leaf) {
            return "$skill 를 읽어 그대로 따른다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: $rest".TrimEnd()
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

Wake-Display
switch ($Action) {
    'send' { Send-Prompt }
    'split' { Split-Session }
    'focus' { Focus-Session }
}
