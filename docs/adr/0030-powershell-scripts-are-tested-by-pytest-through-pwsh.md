---
status: accepted
date: 2026-10-13
---

# `tools/`의 PowerShell 스크립트는 pytest가 pwsh로 함수를 떼어 시험하고, Pester는 들이지 않는다

`tools/open_session.ps1`(open-session 스킬의 손발)의 판정 로직에는 저장소의 회귀 시험이 없었다. 전각 슬래시를 되돌리는 `Normalize-Slash`·`Test-Needle`(PR #50)과 첫 줄의 스킬 명령을 옮기는 `Convert-StartLine`은 AST에서 떼어 잰 시험이 스크래치패드에만 남았다. 스킬이 넘긴 `focus -TimeoutSec 90`을 `Find-RowByTitle`의 10초가 덮고 있던 것은 세션이 스크립트를 읽다가 찾았다(PR #60). 대기열 17이 이렇게 3회차를 넘겼다. PR #107이 이음매를 처음 세웠다. `tests/tools/test_open_session.py`가 스크립트의 AST에서 이름으로 고른 함수만 정의한 뒤 시험 본문을 `pwsh`로 돌리고, pwsh가 없으면 실패한다. 이 결정을 쓸 때(`185fe61`) 그 파일은 `Find-QuitMarker`·`Read-ModelLine`·`Get-EffortButtonStep`·`Test-DraftChanged`·`Get-RepairHint`의 사례 36개를 쟀고, 같은 날 PR #209가 `Get-PendingRestoreLine`의 사례 셋을 더했다. 그러나 Pester로 옮길지는 정하지 않았고, 그 이음매로 `uv run pytest -q`가 pwsh를 전제하게 됐는데 `tech.md`에는 그 사실이 없다(PR #107 claude-review Minor). **PowerShell 스크립트의 회귀 시험은 이 이음매 하나로 둔다. 시험 사례는 pytest의 사례 하나이고, pytest가 `pwsh -NoProfile -NonInteractive -Command`로 스크립트의 AST에서 이름으로 고른 함수만 정의하고 시험 본문을 돌린다. Pester는 들이지 않는다. `uv run pytest -q`는 PATH의 PowerShell 7(`pwsh`)을 전제하고, pwsh가 없으면 건너뛰지 않고 실패한다(원칙 II).**

**함수만 떼는 까닭.** 스크립트 파일을 그대로 dot-source하면 함수 밖의 코드가 돈다. 머리에서 UIAutomation 어셈블리와 C# 타입을 싣고(`Add-Type`), 끝에서 화면을 깨우고(`Wake-Display`) 필수 인자 `-Action`에 따라 창을 조작한다(`switch`). AST에서 함수 정의만 떼면 그것들이 돌지 않는다. 그래서 이 시험은 이 PC(Windows)의 pre-commit과 CI의 ubuntu 러너에서 함께 돈다. main의 CI 실행 38320792513(`185fe61`)은 이 파일을 포함한 2294개를 통과했다(그 실행의 로그를 손으로 봤다). 대가로, 스크립트 범위의 값(`$Auto`·`$Types`·`$TimeoutSec` 등)에 기대는 함수는 시험 본문이 그 값을 먼저 정의해야 한다.

**무엇을 시험하는가.** 판정이 인자에만 달린 함수를 시험한다. 접근성 트리를 누르고 프로세스와 로그를 찾는 부분은 실제 실행으로 확인하고, 그 안의 판정은 순수 함수로 떼어 시험한다. `Get-AppQuitMarker`에서 `Find-QuitMarker`를 뗀 모양이다. 판정을 떼기 어려우면 시험 본문이 그 함수가 부르는 cmdlet과 같은 이름의 함수를 정의해 가짜를 준다. PowerShell은 같은 이름이면 함수를 cmdlet보다 먼저 찾으므로, AST에서 떼어 낸 함수도 그 가짜를 부른다. 가짜가 받은 인자를 적어 내면 pytest가 부른 쪽이 넘긴 인자도 단언한다. Pester의 `Mock`과 `Should -Invoke`가 하는 일 가운데 가짜를 주는 일과 넘긴 인자를 단언하는 일이 이것으로 된다.

**판.** pwsh의 판은 저장소가 고정하지 않는다. 이 PC는 7.6.6이다. CI의 `python` 잡은 러너 이미지에 깔린 판을 쓴다. 위 실행이 쓴 이미지는 `ubuntu-24.04` 20261004.327.1이고, 그 판의 README(`actions/runner-images`의 `images/ubuntu/Ubuntu2404-Readme.md`)를 받아 grep하니 PowerShell 7.6.6이었다(손으로 봤다). 클라우드 세션은 `.scratch/harness/cloud-setup.sh`가 깐다(대기열 138). 판이 갈려 결과가 갈리면 이미지를 올린 CI나 판을 올린 PC가 먼저 본다.

측정은 `.scratch/harness/probes/pwsh_test_seam.py`가 다시 낸다(pwsh 7.6.6, Windows 10). 사례 하나·차례로·같은 이름 함수의 갈래는 위 시험 파일의 `_call`을 그대로 부르고, 기동과 runspace의 갈래는 `_call`이 늘 붙이는 AST 추출을 빼야 해서 pwsh를 직접 띄운다. 프로브를 두 번 돌렸고, 한 번에 기동은 다섯 번, 사례 하나는 열 번 잰다.

- **기동과 사례 하나.** 글자 `up`만 내는 명령으로 pwsh를 띄우는 데 중앙값 0.40~0.41초, 이음매로 `Read-ModelLine` 사례 하나를 부르는 데 0.92초였다. 차이 약 0.5초는 스크립트를 파싱하고 함수를 정의하는 몫으로 본다(두 중앙값의 차이라 어림이다).
- **한 프로세스.** `Read-ModelLine`의 정상 사례 36개를 pwsh 하나에서 차례로 부르면 0.92초였다. 사례마다 새 runspace에서 부르면 1.50~1.59초였고, 앞 사례가 전역에 둔 값이 다음 사례에 보이지 않았다. 같은 글을 바깥과 같은 runspace에서 부른 대조군은 둘째 사례부터 35개 모두 그 값을 봤다. 환경 변수는 달랐다. 프로세스에 하나라서, 새 runspace에서도 앞 사례가 바꾼 값이 둘째 사례부터 35개 모두 보였다.
- **같은 이름 함수.** 시험 본문이 `Get-CimInstance`를 함수로 정의하고 `APPDATA`·`LOCALAPPDATA`를 임시 폴더로 돌리면, 떼어 낸 `Get-AppQuitMarker`가 가짜가 준 주 프로세스의 시각으로 임시 로그의 표지 줄을 냈다. 가짜가 렌더러만 주거나 아무것도 주지 않으면 표지가 없었다. 세 갈래는 가짜가 주는 프로세스만 다르므로, 진짜 cmdlet이 불렸다면 세 결과가 같았어야 한다. 결과가 갈렸으니 가짜가 불렸다. 세 갈래 모두 가짜가 받은 `-Filter` 값(`Name = 'Claude.exe'`)이 본문의 출력에 나왔다.

## Considered Options

- **Pester 5.** PowerShell의 표준 시험 틀이고, 한 프로세스에서 모든 사례를 돌며 `Mock`·`Should -Invoke`와 코드 커버리지가 있다. 거부한 까닭은 셋이다. 첫째, pwsh는 어느 길이든 필요하다. 스크립트가 pwsh에서 돌고 시험도 그 위에서 돈다. Pester는 그 위에 판을 고정하지 못하는 의존성을 하나 더 들인다. `uv.lock`도 `pnpm-lock.yaml`도 PowerShell 모듈을 고정하지 못하고, 그 판은 이미 갈려 있다. 러너 이미지는 Pester 5.9.0을 깔아 두지만(같은 README), 이 PC의 pwsh가 보는 것은 Windows PowerShell의 모듈 폴더에 있는 3.4.0뿐이다(프로브의 env 갈래). major가 다르니 같은 시험이 두 자리에서 다른 Pester로 돈다. 맞추려면 기계마다 `Install-Module`로 깔아야 하고, 그 명령이 판의 원천이 된다. 둘째, Pester는 둘째 시험 러너다. pre-commit 러너(`tools/run_checks.py`의 `CHECKS`)와 CI에 명령이 하나씩 늘고, `tests/conftest.py`가 skip을 세션 실패로 만드는 규약(원칙 II)을 Pester 쪽에 따로 세워야 한다. 변이 도구 `tools/mutate.py`의 판정자는 pytest·vitest·playwright·tsc 넷이라(코드를 읽었다), open_session의 변이 표 둘(`open_session_quit_mutations.toml`, `open_session_model_line_mutations.toml`)을 이으려면 판정자를 하나 더 지어야 한다. 셋째, Pester의 이점 가운데 가짜와 호출 단언은 위의 같은 이름 함수로 되고, 한 프로세스의 이점은 아래 Consequences의 조건 안에서 이 이음매로도 얻을 수 있다. 코드 커버리지는 이 이음매로 얻지 못하는 대가다. 이 저장소는 파이썬에도 아직 커버리지 판정자가 없다(대기열 13).
- **pytest가 pwsh로 `Invoke-Pester`를 한 번 부른다.** 게이트는 pytest 하나로 남지만, Pester의 판 문제는 그대로다. 그리고 pytest에는 Pester 실행 전체가 사례 하나로 보여, 어느 사례가 빨간지와 변이의 판정이 Pester 출력을 해석하는 코드에 걸린다. 거부했다.
- **판정 로직을 파이썬으로 옮기고 스크립트가 그것을 부른다.** 시험은 pytest만으로 되지만, 스크립트가 쏠 때마다 `uv run python`을 띄우고 한 화면 조작의 흐름이 두 언어로 갈린다. 접근성 트리를 누르는 몫은 어차피 PowerShell에 남는다. 거부했다.
- **순수 함수를 모듈(`.psm1`)로 옮기고 시험이 `Import-Module`한다.** AST를 다루지 않아도 되지만, 스크립트가 파일 둘이 되고 무엇이 순수한지를 파일 경계가 정한다. AST로 떼면 시험이 스크립트의 모양을 정하지 않는다. 거부했다. 되돌리기 쉬운 선택이라 스크립트가 커지면 다시 본다.
- **pwsh가 없으면 건너뛴다.** 원칙 II의 "환경 부재로 skip된 테스트는 초록이 아니다"에 걸린다. 거부했다.

## Consequences

- **사례마다 pwsh를 하나 띄운다.** 이 PC에서 시험 파일 하나(`185fe61`의 사례 36개)만 돌리면 29.94초였고, 같은 날 pytest 전체는 325초였다(둘 다 손으로 봤다. 전체는 다른 작업과 겹친 회차다). pre-commit의 pytest는 `always_run`이라 이 값을 커밋마다 낸다. 이 브랜치의 커밋에서 pytest는 347.0초로 함께 띄운 검사 가운데 가장 늦게 끝났다(web-verify 176.5초, 그 출력을 손으로 봤다). CI에서 이 파일이 쓰는 시간은 재지 않았다(위 실행의 pytest 전체는 125초였다). 이 파일의 시간이 지금(사례 36개에 약 30초)의 두 배를 넘으면 pwsh 하나에서 사례마다 새 runspace로 부르게 묶을지 정한다. 묶을 때의 조건은 셋이다.
  - 위의 1.50~1.59초는 정상 사례만 잰 수다. 사례마다의 출력·오류·실패 여부를 pytest의 그 사례로 돌려주는 규약과, 실패를 단언하는 사례의 값은 재지 않았다.
  - 환경 변수는 runspace 사이에 샌다. 환경을 바꾸는 사례(위의 같은 이름 함수처럼 `APPDATA`를 돌리는 본문)는 묶지 않거나 앞뒤로 되돌린다.
  - 사례마다 pytest의 사례로 빨강이 남아야 한다. 남으면 위 결정(시험 사례는 pytest의 사례 하나다)을 바꾸지 않는다. 남지 않으면 `Invoke-Pester`를 거부한 까닭과 같은 대가이므로 그때 다시 정한다.
- **pwsh 전제를 적는다.** `tech.md`의 테스트 행, `operations.md` 가드레일의 기계마다 까는 것(chromium 옆), `README.md`의 시작 절, `.pre-commit-config.yaml` 머리의 준비 목록이다. 헌법 버전은 patch다. 게이트 수와 손으로 치는 검증 명령은 그대로다.
- **못 보는 것.** 판을 고정하지 않으므로 pwsh 7의 판 사이의 동작 차이는 그 판이 CI나 이 PC에 들어온 뒤에야 본다. Windows PowerShell 5.1에서의 동작은 보지 않는다(스킬은 `pwsh`로 부른다). 접근성 트리와 앱의 동작은 시험 밖이고 실제 실행으로만 본다. 같은 이름 함수로 가짜를 주는 길은 Windows에서만 쟀다. 그 길로 쓴 시험이 ubuntu 러너에서도 같은지는 그 시험을 들일 때 CI가 처음 본다.
- 대기열 17의 남은 몫은 이 이음매로 따로 간다. `Normalize-Slash`·`Test-Needle`·`Convert-StartLine`의 시험, `-TimeoutSec`처럼 스킬이 넘긴 인자가 실제로 먹는지의 시험, `Get-AppQuitMarker`의 선택을 순수 함수로 떼어 재는 것이다. 지금의 `_call`은 pwsh에 시간 제한을 두지 않아, 대기 루프를 부르는 시험이 회귀로 끝나지 않으면 pytest가 멈춘다. 그런 시험을 들일 때 `_call`에 시간 제한을 단다. 같은 파일의 대기열 18(`stale=` 경로)도 그 판정을 떼면 같은 이음매로 잴 수 있다.
