# 딥링크(두 번째 인스턴스)마다 그 뒤 처음으로 새 세션 화면이 선 때(`setFocusedSession: sessionId=null`),
# 앞 세션의 턴이 끝난 때, 세션이 시작한 때까지의 초를 앱의 로그에서 잰다. 읽기만 한다(일지 2026-09-30-06).
#   pwsh -NoProfile -File .scratch/harness/probes/deeplink_timeline.ps1
# 2026-09-30 결과: 09-28 22:53 까지는 대체로 page+0s 였고(+0 이 아닌 것도 있다. 09-23 17:07~17:17 과 09-26 01:51, 원인은 재지
# 않았다), 09-29 07:50 부터는 한 번도 +0s 가 아니었다(사람이 손으로 연 때에야 섰다). `setFocusedSession null` 은 사람이 세션을
# 옮길 때도 찍혀 +0s 가 아닌 값은 "딥링크가 아닌 다른 때"로만 읽는다. 두 번째 인스턴스는 딥링크만이 아니라 앱을 다시 켜려 한
# 클릭 같은 것까지 센다(09-29 10:22~10:23 의 1분에 여섯 번).
#
# 두 번째 인스턴스의 표지는 앱 판마다 다르다. 2026-10-15 까지의 판은 `Not main instance` 를 찍었다. 그 뒤 판은 제 기동 줄
# `Starting app {` 과 몇 초 뒤의 `Quit requested before 'ready'; not creating the main window` 만 남겨, 이 프로브가 2026-10-15
# 뒤로 아무 줄도 내지 않았다(대기열 360). 주 프로세스의 기동도 `Starting app {` 이라 끝내기 줄과 10초 안에 짝지은 기동만 센다.
# 로그는 `main.log` 에서 `main1.log`~`main4.log` 로 돌아(2026-10-26 에 로그 폴더를 손으로 봤다) 그 폴더의 `main*.log` 를 다
# 읽는다. 열기마다 남의 딥링크가 겹쳤는지는 `deeplink_overlap.py` 가 가른다.
$dir = "$env:LOCALAPPDATA\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Local\Claude\logs"
$pattern = 'Not main instance|setFocusedSession: sessionId=null|Starting local session|\[Stop hook\] Query completed|Starting app \{|Quit requested before ''ready'''
$events = foreach ($f in Get-ChildItem -Path $dir -Filter 'main*.log') {
    # 여러 줄 객체의 속 줄에도 문구가 들 수 있어 시각으로 시작하는 줄만 받는다.
    Select-String -LiteralPath $f.FullName -Pattern $pattern -Encoding UTF8 |
        Where-Object { $_.Line -match '^\d{4}-\d\d-\d\d \d\d:\d\d:\d\d ' } |
        ForEach-Object {
            $t = [datetime]::ParseExact($_.Line.Substring(0, 19), 'yyyy-MM-dd HH:mm:ss', $null)
            $kind = if ($_.Line -match 'Not main') { 'link' } elseif ($_.Line -match 'Starting app') { 'boot' } elseif ($_.Line -match 'Quit requested') { 'quit' } elseif ($_.Line -match 'setFocused') { 'page' } elseif ($_.Line -match 'Starting local') { 'start' } else { 'stop' }
            # 같은 초의 기동과 끝내기는 기동을 앞에 둔다.
            [pscustomobject]@{ T = $t; Kind = $kind; Rank = if ($kind -eq 'boot') { 0 } else { 1 } }
        }
}
$events = @($events | Where-Object { $_.T -ge [datetime]'2026-09-21' } | Sort-Object T, Rank)
# 끝내기 줄마다 그 앞 10초 안의 짝 없는 기동 가운데 가장 늦은 것을 딥링크로 센다. 짝 없는 기동은 주 프로세스다.
$pending = [System.Collections.Generic.List[datetime]]::new()
$paired = foreach ($e in $events) {
    if ($e.Kind -eq 'boot') { $pending.Add($e.T); continue }
    if ($e.Kind -ne 'quit') { continue }
    $boot = @($pending | Where-Object { $_ -le $e.T -and ($e.T - $_).TotalSeconds -le 10 }) | Select-Object -Last 1
    if ($null -ne $boot) {
        [void]$pending.Remove($boot)
        [pscustomobject]@{ T = $boot; Kind = 'link' }
    }
}
$links = @(@($events | Where-Object Kind -eq 'link') + @($paired) | Sort-Object T)
# 딥링크마다 그 뒤 첫 사건까지의 초. 둘 다 시각 순이라 갈래마다 앞으로만 가는 자리 하나로 찾는다(딥링크마다 전부를 훑으면
# 지금의 로그에서 한 바퀴가 2분 가까이 걸렸다).
$times = @{}
$at = @{}
foreach ($kind in 'page', 'stop', 'start') {
    $times[$kind] = @($events | Where-Object Kind -eq $kind | ForEach-Object T)
    $at[$kind] = 0
}
foreach ($l in $links) {
    $gaps = foreach ($kind in 'page', 'stop', 'start') {
        $list = $times[$kind]
        while ($at[$kind] -lt $list.Count -and $list[$at[$kind]] -lt $l.T) { $at[$kind]++ }
        if ($at[$kind] -lt $list.Count) { [int]($list[$at[$kind]] - $l.T).TotalSeconds } else { -1 }
    }
    '{0:MM-dd HH:mm:ss} page+{1}s stop+{2}s start+{3}s' -f $l.T, $gaps[0], $gaps[1], $gaps[2]
}
