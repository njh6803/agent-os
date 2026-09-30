# 딥링크(두 번째 인스턴스의 `Not main instance`)마다 그 뒤 처음으로 새 세션 화면이 선 때(`setFocusedSession: sessionId=null`),
# 앞 세션의 턴이 끝난 때, 세션이 시작한 때까지의 초를 앱의 로그에서 잰다. 읽기만 한다(일지 2026-09-30-06).
#   pwsh -NoProfile -File .scratch/harness/probes/deeplink_timeline.ps1
# 2026-09-30 결과: 09-28 22:53 까지는 대체로 page+0s 였고(+0 이 아닌 것도 있다. 09-23 17:07~17:17 과 09-26 01:51, 원인은 재지
# 않았다), 09-29 07:50 부터는 한 번도 +0s 가 아니었다(사람이 손으로 연 때에야 섰다). `setFocusedSession null` 은 사람이 세션을
# 옮길 때도 찍혀 +0s 가 아닌 값은 "딥링크가 아닌 다른 때"로만 읽는다. `Not main instance` 도 딥링크만이 아니라 앱을 다시 켜려 한
# 클릭 같은 것까지 센다(09-29 10:22~10:23 의 1분에 여섯 번).
$dir = "$env:LOCALAPPDATA\Packages\Claude_pzs8sxrjxfjjc\LocalCache\Local\Claude\logs"
$events = foreach ($f in @('main1.log', 'main.log')) {
    Select-String -Path (Join-Path $dir $f) -Pattern 'Not main instance|setFocusedSession: sessionId=null|Starting local session|\[Stop hook\] Query completed' |
        ForEach-Object {
            $t = [datetime]::ParseExact($_.Line.Substring(0, 19), 'yyyy-MM-dd HH:mm:ss', $null)
            $kind = if ($_.Line -match 'Not main') { 'link' } elseif ($_.Line -match 'setFocused') { 'page' } elseif ($_.Line -match 'Starting local') { 'start' } else { 'stop' }
            [pscustomobject]@{ T = $t; Kind = $kind }
        }
}
$events = $events | Where-Object { $_.T -ge [datetime]'2026-09-21' } | Sort-Object T
$links = $events | Where-Object Kind -eq 'link'
foreach ($l in $links) {
    $page = $events | Where-Object { $_.Kind -eq 'page' -and $_.T -ge $l.T } | Select-Object -First 1
    $stop = $events | Where-Object { $_.Kind -eq 'stop' -and $_.T -ge $l.T } | Select-Object -First 1
    $start = $events | Where-Object { $_.Kind -eq 'start' -and $_.T -ge $l.T } | Select-Object -First 1
    $p = if ($page) { [int]($page.T - $l.T).TotalSeconds } else { -1 }
    $s = if ($stop) { [int]($stop.T - $l.T).TotalSeconds } else { -1 }
    $st = if ($start) { [int]($start.T - $l.T).TotalSeconds } else { -1 }
    '{0:MM-dd HH:mm:ss} page+{1}s stop+{2}s start+{3}s' -f $l.T, $p, $s, $st
}
