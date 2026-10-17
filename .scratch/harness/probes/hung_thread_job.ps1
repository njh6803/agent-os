# 진단 전용. `tools/open_session.ps1` 의 Invoke-PatternTimed 가 멈춘 접근성 호출을 스레드 잡으로 끊을 때, 잡을 지우는 모양과
# 남기는 모양에서 함수가 언제 돌아오고 pwsh 프로세스가 언제 끝나는지 잰다. 멈춘 호출은 15초 잠으로 흉내 내고 제한은 2초다.
# 갈래 셋을 각각 자식 pwsh 로 돌린다.
#   remove: 시간을 넘겨도 finally 에서 Remove-Job -Force (고치기 전의 모양)
#   leave:  시간을 넘긴 잡은 지우지 않고 돌아온다
#   exit:   leave 에 더해, 멈춘 잡이 남았으면 출력을 낸 뒤 [Environment]::Exit 로 끝낸다(오류를 던진 경우도)
# 회차마다 자식이 `returned=hung` 을 찍었어야 멈춘 호출을 잰 회차다. 그 표지가 없는 회차가 있으면 1로 끝난다.
# 쓰는 법: pwsh -NoProfile -File .scratch/harness/probes/hung_thread_job.ps1
param([ValidateSet('', 'remove', 'leave', 'exit')] [string] $Mode = '', [switch] $Throw)
$ErrorActionPreference = 'Stop'

if ($Mode) {
    $script:HungCalls = 0
    $start = Get-Date
    function Call-Timed {
        $job = Start-ThreadJob -ScriptBlock { [System.Threading.Thread]::Sleep(15000); 'ok' }
        if ($Mode -eq 'remove') {
            try {
                if (-not (Wait-Job $job -Timeout 2)) { return 'hung' }
                return Receive-Job $job
            } finally { Remove-Job $job -Force }
        }
        if (-not (Wait-Job $job -Timeout 2)) { $script:HungCalls++; return 'hung' }
        try { return Receive-Job $job } finally { Remove-Job $job -Force }
    }
    $run = {
        "returned=$(Call-Timed) after=$([int]((Get-Date) - $start).TotalMilliseconds)ms"
        if ($Throw) { throw '던진 오류' }
        'last-line'
    }
    if ($Mode -ne 'exit') { & $run; return }
    try { & $run }
    catch {
        if ($script:HungCalls -eq 0) { throw }
        [Console]::Error.WriteLine("$($_.Exception.Message) (hung=$script:HungCalls)")
        [Environment]::Exit(1)
    }
    if ($script:HungCalls -gt 0) { [Environment]::Exit(0) }
    return
}

$notMeasured = 0
foreach ($case in @(@('remove', $false), @('leave', $false), @('exit', $false), @('exit', $true))) {
    $mode = $case[0]
    $args_ = @('-NoProfile', '-File', $PSCommandPath, '-Mode', $mode)
    if ($case[1]) { $args_ += '-Throw' }
    $watch = [System.Diagnostics.Stopwatch]::StartNew()
    $out = & pwsh @args_ 2>&1 | ForEach-Object { "$_" }
    $code = $LASTEXITCODE
    $label = "$mode$(if ($case[1]) { '+throw' })"
    if (-not ($out -match '^returned=hung')) { $notMeasured++; "측정 아님($label): returned=hung 줄이 없다" }
    "$label process-exit=$($watch.ElapsedMilliseconds)ms exit=$code out=[$($out -join ' / ')]"
}
if ($notMeasured -gt 0) { exit 1 }
