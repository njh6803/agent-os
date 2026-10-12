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
'@

$Auto = [System.Windows.Automation.AutomationElement]
$Scope = [System.Windows.Automation.TreeScope]
$Types = [System.Windows.Automation.ControlType]
# 지시문의 모델 줄대로 고르기 전 새 세션 화면에 있던 모델과 노력 슬라이더 칸. 보낸 뒤 Restore-DraftDefaults 가 되돌린다.
$script:DraftModel = $null
$script:DraftEffortStep = $null

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
    # 고르다 멈추거나 `held=` 로 멈추면 이 스크립트가 보내지 않아 기본값을 되돌릴 때가 없다. 사람이 보낸 뒤 칠 복구를 남긴다.
    if ($pick) {
        try { Set-ComposerModel $win $box $pick }
        catch {
            if ($script:DraftModel) { "restore=필요: 새 세션 화면의 기본값이 바뀌었을 수 있다. 사람이 보낸 뒤 $(Get-RepairHint)" }
            throw
        }
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
        if ($pick) { "restore=필요: 사람이 보낸 뒤 $(Get-RepairHint)" }
        return
    }

    $send = Wait-For { Find-EnabledSendButton $win } '활성 보내기 버튼'
    $how = Press-Element $send
    Wait-For {
        try { -not (Test-Needle ($box.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value) $needle) } catch { $false }
    } '제출된 뒤 비워진 입력창(요소를 못 읽으면 비운 것으로 치지 않는다)' 10 | Out-Null
    "sent=$(Get-Date -Format HH:mm:ss.fff) via $how"
    if ($pick) { Restore-DraftDefaults $win }
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
# 레벨은 API 이름 그대로 소문자이고, 칸은 입력창 노력 슬라이더의 위치다. 앱 2.19675.0.0 에서 0~4 칸의 이름이 낮음·중간·
# 높음·엑스트라·최대였고 여섯째 칸(5)은 레벨이 아닌 `Ultracode` 라 고르지 않는다(.scratch/harness/probes/composer_effort_labels.ps1,
# 2026-10-12). 0·1·2·4 는 그 칸으로 연 시험 세션의 get_session 이 low·medium·high·max 였고, 3 은 엑스트라로 연 세션의
# get_session 이 xhigh 였다(손으로 봤다).
# 줄 머리에서 시작하는 줄만 본다. 지시문 형식은 불릿이나 인용 없이 줄 머리이고, 다른 칸의 글 속 `모델:` 은 줄이 아니다.
# 결정표의 칸(`Opus 5.5 / xhigh`)을 그대로 옮긴 줄도 읽도록 백틱을 벗긴다(hook_prompt_directive 가 `브랜치:` 값에서 하는 것과 같다).
function Get-EffortSteps { return @('low', 'medium', 'high', 'xhigh', 'max') }

# 노력 버튼에 보이는 칸의 이름(앱 2.19675.0.0, 한국어). 버튼은 이름 뒤에 덧붙임이 붙을 수 있다(`최대 3.5× 이상 사용량`).
# Get-EffortSteps 와 차례가 같다. 고른 뒤 버튼이 이 이름을 보이는지 보고, 고르기 전의 값을 이 이름으로 읽는다.
function Get-EffortLabels { return @('낮음', '중간', '높음', '엑스트라', '최대') }

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

# 지시문 입력창과 같은 입력창 묶음의 버튼(`모델: …`, `노력: …`). 분할 보기면 패널마다 입력창이 있어 창 전체에서 찾으면 다른
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

function Test-ButtonShows($button, [string] $label) {
    try { $name = $button.Current.Name } catch { return $false }
    return [bool]($name -ceq $label -or $name.StartsWith("$label "))
}

# 노력 버튼이 보이는 칸. 이름이 Get-EffortLabels 밖이면(Ultracode, 앱이 바꾼 이름) $null 이다.
function Get-EffortButtonStep($button) {
    $labels = Get-EffortLabels
    for ($i = 0; $i -lt $labels.Count; $i++) { if (Test-ButtonShows $button "노력: $($labels[$i])") { return $i } }
    return $null
}

function Get-EditValue($el) {
    try { return $el.GetCurrentPattern([System.Windows.Automation.ValuePattern]::Pattern).Current.Value } catch { return '' }
}

# 모델 메뉴의 항목은 RadioButton 이고 기본값이면 이름 뒤에 표시가 붙는다(`Sonnet 5.5 기본값`, 2026-10-12 손으로 봤다,
# .scratch/harness/probes/composer_menu_tree.ps1). 그래서 이름이 같거나 이름 뒤에 공백이 오는 것을 고른다. 메뉴와 아래의
# 노력 슬라이더는 입력창 묶음이 아니라 창 전체에서 찾는다. 한 번에 하나만 열려 있고, 방금 연 것이 그것이다.
function Find-ModelItem($win, [string] $model) {
    $radioCond = New-Object System.Windows.Automation.PropertyCondition($Auto::ControlTypeProperty, $Types::RadioButton)
    return @($win.FindAll($Scope::Descendants, $radioCond) | Where-Object { try { $n = $_.Current.Name; $n -ceq $model -or $n.StartsWith("$model ") } catch { $false } }) | Select-Object -First 1
}

# 입력창 묶음의 모델 버튼이 그 모델을 보이게 한다. 이미 그 모델이면 메뉴를 열지 않는다. 바꾼 뒤 버튼 이름으로 맞았는지 본다.
function Select-ComposerModelItem($win, $box, [string] $model) {
    $label = "모델: $model"
    $button = Wait-For { Find-ComposerButton $box '모델:' } '입력창의 모델 버튼' 5
    if (Test-ButtonShows $button $label) { return }
    Press-Element $button | Out-Null
    $item = Wait-For { Find-ModelItem $win $model } "모델 메뉴의 '$model'" 5
    if (-not $item.Current.IsEnabled) {
        [System.Windows.Forms.SendKeys]::SendWait('{ESC}')
        throw "모델 메뉴의 '$($item.Current.Name)'가 비활성이다. 사람이 메뉴를 보고 판단한다."
    }
    Press-Element $item | Out-Null
    Wait-For { $b = Find-ComposerButton $box '모델:'; if ($b -and (Test-ButtonShows $b $label)) { $b } } "'$label' 로 바뀐 모델 버튼" 5 | Out-Null
}

# 지시문의 모델 줄대로 새 세션 입력창의 모델과 노력을 고른다. 딥링크는 모델을 싣지 못하고(앱의 `code/new` 처리기는
# q·prompt·folder·file 과 SSH 인자만 읽는다, 앱 2.19675.0.0 번들을 읽었다), 보낸 뒤 바꾸는 도구는 다음 턴부터라 첫 턴에 늦다.
# 모델을 먼저 고른다. 모델을 바꾸면 노력이 그 모델의 값으로 바뀔 수 있다. 모델은 버튼 이름으로, 노력은 슬라이더 칸과 버튼
# 이름으로 맞았는지 보고, 아니면 보내지 않고 멈춘다. 앱이 칸의 뜻을 바꾸면 이름이 어긋나 여기서 멈춘다. 메뉴는 Esc 로
# 닫는다. 고속 모드 체크박스와 슬라이더의 여섯째 칸은 건드리지 않는다.
# 새 세션 화면의 모델과 노력은 앱이 다음 새 세션 화면의 기본값으로 기억하고, 노력은 보내지 않고 옮기기만 해도 남는다
# (.scratch/harness/probes/composer_effort_labels.ps1 로 손으로 봤다, 2026-10-12). 그래서 고르기 전의 값을 버튼 이름으로 먼저
# 읽어 두고 보낸 뒤 Restore-DraftDefaults 가 되돌린다. 사람이 다음에 직접 여는 세션이 지시문의 값으로 열리지 않게 한다.
function Set-ComposerModel($win, $box, $pick) {
    $button = Wait-For { Find-ComposerButton $box '모델:' } '지시문 입력창의 모델 버튼' 5
    $effortButton = Wait-For { Find-ComposerButton $box '노력:' } '지시문 입력창의 노력 버튼' 5
    $script:DraftModel = $button.Current.Name.Substring('모델:'.Length).Trim()
    $script:DraftEffortStep = Get-EffortButtonStep $effortButton
    $before = if ($null -eq $script:DraftEffortStep) { "$($effortButton.Current.Name)(되돌리지 않는다)" } else { (Get-EffortSteps)[$script:DraftEffortStep] }

    Select-ComposerModelItem $win $box $pick.Model
    "model=$($pick.Model) 원래 $script:DraftModel"

    $effortButton = Wait-For { Find-ComposerButton $box '노력:' } '지시문 입력창의 노력 버튼' 5
    $moved = Move-EffortSlider $win $effortButton $pick.Step
    if ($pick.Step -gt $moved.Max) { throw "노력 슬라이더의 끝이 $($moved.Max) 칸이라 '$($pick.Effort)'($($pick.Step)) 를 고를 수 없다. 보내지 않았다." }
    if ($moved.After -ne $pick.Step) { throw "노력 슬라이더가 $($moved.After) 칸이다('$($pick.Effort)' 는 $($pick.Step) 칸). 보내지 않았다." }
    $label = "노력: $((Get-EffortLabels)[$pick.Step])"
    Wait-For { $b = Find-ComposerButton $box '노력:'; if ($b -and (Test-ButtonShows $b $label)) { $b } } "'$label' 를 보이는 노력 버튼(보내지 않았다)" 5 | Out-Null
    "effort=$($pick.Effort) 원래 $before"
}

# 노력 메뉴를 열어 슬라이더를 칸으로 옮기고 닫는다. 웹 슬라이더라 값은 사람의 조작과 같은 키로 옮긴다. 처음으로 간 뒤 칸
# 수만큼 오른쪽. 칸이 슬라이더의 끝을 넘으면 옮기지 않는다. 옮기기 전과 뒤의 칸, 끝 칸을 돌려준다.
function Move-EffortSlider($win, $button, [int] $step) {
    Press-Element $button | Out-Null
    $sliderCond = New-Object System.Windows.Automation.PropertyCondition($Auto::ControlTypeProperty, $Types::Slider)
    $slider = Wait-For { $win.FindFirst($Scope::Descendants, $sliderCond) } '노력 슬라이더' 5
    $range = $slider.GetCurrentPattern([System.Windows.Automation.RangeValuePattern]::Pattern)
    $before = [int]$range.Current.Value
    $max = [int]$range.Current.Maximum
    if ($step -le $max) {
        $slider.SetFocus()
        Start-Sleep -Milliseconds 200
        [System.Windows.Forms.SendKeys]::SendWait('{HOME}')
        Start-Sleep -Milliseconds 300
        for ($i = 0; $i -lt $step; $i++) { [System.Windows.Forms.SendKeys]::SendWait('{RIGHT}'); Start-Sleep -Milliseconds 250 }
    }
    $after = [int]$range.Current.Value
    [System.Windows.Forms.SendKeys]::SendWait('{ESC}')
    Start-Sleep -Milliseconds 400
    return [pscustomobject]@{ Before = $before; After = $after; Max = $max }
}

# 표지 글이 든 새 세션 화면을 연다. 보내지 않는 화면이라 그 입력창의 버튼만 움직이고, 끝나면 Clear-PromptBox 로 표지를 지운다.
function Open-MarkerDraft($win, [string] $purpose) {
    $marker = "open-session-$purpose-$(Get-Date -Format HHmmssfff)"
    Start-Process ('claude://code/new?q=' + [uri]::EscapeDataString($marker))
    return Wait-For { Find-PromptBox $win $marker } "표지('$marker')가 든 새 세션 입력창" 10
}

function Clear-PromptBox($box) {
    $box.SetFocus()
    Start-Sleep -Milliseconds 200
    [System.Windows.Forms.SendKeys]::SendWait('^a')
    [System.Windows.Forms.SendKeys]::SendWait('{DELETE}')
    Start-Sleep -Milliseconds 200
}

# 새 세션 화면의 기본값을 고르기 전으로 돌리는 사람의 길. 원래 노력이 Get-EffortLabels 밖이면 스크립트가 고르지 않는
# 칸이라(Ultracode) 명령 대신 화면에서 고르라고 한다.
function Get-RepairHint {
    if ($null -eq $script:DraftEffortStep) { return "새 세션 화면에서 모델을 '$script:DraftModel' 로, 노력을 원래 값으로 고른다" }
    return "친다: pwsh -NoProfile -File tools/open_session.ps1 -Action defaults -Model '$script:DraftModel' -Effort $((Get-EffortSteps)[$script:DraftEffortStep])"
}

# 보낸 뒤 새 세션 화면의 모델과 노력 기본값을 고르기 전으로 되돌린다(Set-ComposerModel 의 주석). 세션은 이미 열렸으므로
# 실패해도 멈추지 않고 사람의 길(Get-RepairHint)을 한 줄로 남긴다. 표지 화면은 스킬의 5단계(split·focus)가 새 세션으로 덮는다.
# 원래 노력이 목록 밖이면 모델만 되돌린다.
function Restore-DraftDefaults($win) {
    if (-not $script:DraftModel) { return }
    $got = $null
    try {
        $box = Open-MarkerDraft $win 'restore'
        try {
            Select-ComposerModelItem $win $box $script:DraftModel
            if ($null -ne $script:DraftEffortStep) {
                $button = Wait-For { Find-ComposerButton $box '노력:' } '되돌릴 화면의 노력 버튼' 5
                $got = (Move-EffortSlider $win $button $script:DraftEffortStep).After
            }
        } finally { Clear-PromptBox $box }
    } catch {
        return "restore=실패: $($_.Exception.Message) 사람이 $(Get-RepairHint)"
    }
    if ($null -eq $script:DraftEffortStep) { return "restored=$script:DraftModel. 원래 노력은 스크립트가 고르지 않는 칸이라 두었다. 사람이 $(Get-RepairHint)" }
    if ($got -ne $script:DraftEffortStep) { return "restore=실패: 노력 슬라이더가 $got 칸이다(원래 $script:DraftEffortStep). 사람이 $(Get-RepairHint)" }
    return "restored=$script:DraftModel / $((Get-EffortSteps)[$script:DraftEffortStep])"
}

# 새 세션 화면의 모델과 노력 기본값을 맞춘다. 되돌리기가 실패했을 때의 복구다. 표지 화면을 열어 고르고 표지를 지운다.
function Set-Defaults {
    if (-not $Model -or -not $Effort) { throw 'defaults 에는 -Model 과 -Effort 가 필요하다.' }
    $pick = Read-ModelLine "모델: $Model / $Effort"
    $win = Get-ClaudeWindow
    $box = Open-MarkerDraft $win 'defaults'
    try { Set-ComposerModel $win $box $pick } finally { Clear-PromptBox $box }
    "defaults=$Model / $Effort"
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

# 도는 앱의 주 프로세스가 선 뒤에 끝내기 표지가 있으면 그 줄, 없으면 null 이다. 주 프로세스나 로그를 못 찾으면 null 이다
# (판정하지 못하면 막지 않는다. 판정 중의 예외는 부르는 쪽이 `quitcheck=` 로 남기고 지나간다). 주 프로세스는
# `app\Claude.exe` 가운데 `--type=` 이 없는 가장 오래된 것이다. 딥링크마다 잠깐 뜨는 두 번째 인스턴스도 같은 모양이지만 더
# 늦게 선다. 같은 이름의 CLI(`claude.exe`)는 경로가 다르다. 로그는 MSIX 설치(`Packages\Claude_*`)와 일반 설치
# (`%APPDATA%\Claude`) 가운데 가장 최근에 쓰인 곳이다. 표지가 돌림 파일로 밀렸을 수 있어 `main1.log` 도 읽되, 주 프로세스가
# 서기 전에 마지막으로 쓰인 돌림 파일은 볼 것이 없어 건너뛴다(10MB 인 그 파일까지 읽으면 판정 전체가 2.66초였다, 셀프 리뷰).
function Get-AppQuitMarker {
    $main = @(Get-CimInstance Win32_Process -Filter "Name = 'Claude.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.ExecutablePath -match '\\app(-[\d.]+)?\\Claude\.exe$' -and $_.CommandLine -notmatch '--type=' } |
        Sort-Object CreationDate)
    if ($main.Count -eq 0 -or $null -eq $main[0].CreationDate) { return $null }
    $started = $main[0].CreationDate
    $dirs = @(Get-ChildItem -Path "$env:LOCALAPPDATA\Packages" -Directory -Filter 'Claude_*' -ErrorAction SilentlyContinue |
        ForEach-Object { Join-Path $_.FullName 'LocalCache\Local\Claude\logs' }) + @("$env:APPDATA\Claude\logs")
    $logs = @($dirs | ForEach-Object { Join-Path $_ 'main.log' } | Where-Object { Test-Path -LiteralPath $_ } |
        Sort-Object { (Get-Item -LiteralPath $_).LastWriteTime } -Descending)
    if ($logs.Count -eq 0) { return $null }
    $files = @((Join-Path (Split-Path $logs[0]) 'main1.log'), $logs[0]) |
        Where-Object { (Test-Path -LiteralPath $_) -and (Get-Item -LiteralPath $_).LastWriteTime -ge $started }
    $lines = foreach ($file in $files) { Get-Content -LiteralPath $file -Encoding UTF8 }
    return Find-QuitMarker @($lines) $started
}

Wake-Display
switch ($Action) {
    'send' { Send-Prompt }
    'split' { Split-Session }
    'focus' { Focus-Session }
    'defaults' { Set-Defaults }
}
