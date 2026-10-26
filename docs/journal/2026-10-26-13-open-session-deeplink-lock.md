# 2026-10-26 (13) open-session 딥링크가 겹치는지 앱 로그로 가르고 기계 전체의 잠금으로 막는다 (harness 014)

## 구현

> 사용자: 대기열 360을 티켓 .scratch/harness/issues/014-open-session-deeplink-lock.md로 쓰고 한다 (next-session 지시문. 새 세션이고 나란히 여는 8 중 5, 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(014-open-session-deeplink-lock)로 들어간다. 브랜치 chore/014-open-session-deeplink-lock, 모델 Opus 5.5 / xhigh(레벨 스윕의 갈래), 범위는 PR과 병합까지. 읽을 것은 docs/agents/issue-tracker.md 와 나란히 여는 나머지 티켓 010~013·015~017. tidy-checkouts 는 묶음의 첫 세션이 돈다)

### 시작

- 제목을 브랜치 이름으로 바꿨다. `tidy-checkouts`는 묶음의 첫 세션 몫이라 돌지 않았다.
- `EnterWorktree(014-open-session-deeplink-lock)` 뒤 `chore/014-open-session-deeplink-lock`을 땄다.

### 진단

- `.scratch/harness/probes/deeplink_timeline.ps1`이 2026-10-15 뒤로 아무 줄도 내지 않은 까닭은 둘이었다. 앱의 두 번째 인스턴스가 `Not main instance` 대신 제 기동 줄 `Starting app {`과 몇 초 뒤의 `Quit requested before 'ready'`만 남기고, 로그가 `main.log`에서 `main1.log`~`main4.log`로 돈다. 끝내기 줄과 10초 안에 짝지은 기동만 딥링크로 세고 돌림 파일을 모두 읽게 고쳤다. 2026-10-26의 로그에서 784줄을 16초에 냈다(손으로 쟀다).
- 새 프로브 `.scratch/harness/probes/deeplink_overlap.py`가 이 계정의 트랜스크립트에 남은 `send`의 결과(`fired=`, `sent=`, 멈춤 문구)와 앱 로그를 맞대, 자기 딥링크 뒤 보내기 전에 남의 딥링크가 왔는지(겹침)를 갈랐다. 측정 344회차 가운데 겹침의 증상으로 멈춘 넷(입력창 없음 하나, 지시문 바뀜 셋)은 모두 겹쳤고, 다른 까닭으로 멈춘 여섯과 보낸 열기 334에는 겹침이 없었다. 넷은 대기열 360이 센 셋과 대기열이 세지 않은 2026-10-19 19:55:26이다. 측정 아닌 회차가 둘(10-19 15:08:02, 10-24 14:29:16, 둘 다 보냈다. 로그에 그 초의 두 번째 인스턴스 줄이 없다)이라 종료 코드는 1이다. 판정 기준과 결과를 본 뒤 바꾼 로그 범위는 그 프로브의 README 행에 있다.
- 넷 가운데 2026-10-19 11:50의 회차는 남의 딥링크가 11:50:28에 왔고, 그것은 앞 열기가 보낸 뒤 기본값을 되돌리며 쏜 표지 딥링크였다(로그를 손으로 봤다). 그래서 잠금은 되돌리기까지 쥔다.

### 한 것 (커밋하지 않았다)

- 티켓 `.scratch/harness/issues/014-open-session-deeplink-lock.md`(in-progress).
- `tools/open_session.ps1`: `Invoke-SendLocked`가 기계 전체의 이름 있는 뮤텍스(`Global\agent-os-open-session`)를 `-LockTimeoutSec`(기본 60) 동안 기다려 잡고, 잡으면 `lock=<시각> waited=<초>s`를 찍고 몸을 돈 뒤 `finally`에서 놓는다. 시간을 넘기면 쏘지 않고 던진다. 쥔 프로세스가 놓지 않고 끝났으면 버려진 잠금을 받아 쥐고 그 사실을 `lock=` 줄에 붙인다. 디스패처의 `send`와 `defaults`가 그 안에서 돈다. 끝내기 표지를 설명하던 주석의 두 번째 인스턴스 줄에 지금 판의 표지를 더했다.
- `tests/tools/test_open_session.py`: 잠금 시험 여섯. 다른 pwsh가 쥐고 있으면 제한 시간에 몸을 돌지 않고 멈춘다(던질 때까지의 시간도 본다), 놓을 때까지 기다렸다가 잡는다, 놓지 않고 끝나도 잡고 알린다, 몸이 끝나거나 던지면 놓는다(둘), 새 세션 화면을 쓰는 두 동작이 AST에서 잠금 안에서만 불린다. 구현 전에는 여섯 모두 `Invoke-SendLocked 가 스크립트에 없다`로 빨갰다.
- 변이 표 `.scratch/harness/probes/open_session_lock_mutations.toml`(여덟)과 프로브 README 행 셋(`deeplink_timeline.ps1` 고침, `deeplink_overlap.py`, 변이 표).
- `.claude/skills/open-session/SKILL.md`: 3단계에 잠금과 `lock=` 줄, 잠금 오류(쏘지 않았으니 같은 파일로 한 번 다시 돌리고 또 멈추면 "막히면")와 버려진 잠금의 알림을, "막히면"에 잠금 오류와 겹침을 가르는 `deeplink_overlap.py`를 더했다.
- 카나리아 명세 `.scratch/harness/probes/canary/open_session_lock.toml`. 그 스킬을 원천으로 든 명세 넷은 이미 병합된 옛 문구를 묻고, `sibling_overlap`이 이 브랜치가 스킬만 고쳤다고 알려 새로 썼다. 셋째 카나리아를 처음 `deeplink_overlap.py`로 골랐다가 사전 확인이 그 이름이 세션에 실리는 git 상태(미추적 파일 경로)에 있다고 막아, 본문에만 있는 문구로 바꿨다.
- 대기열 360을 이 티켓으로 닫았다.

### 결정

- 잠그는 것은 새 세션 화면을 쓰는 `send`(되돌리기까지)와 `defaults`다. `split`·`focus`는 딥링크를 쏘지 않아 잠그지 않았고, 그 둘이 다른 열기의 화면을 옮겨 놓는지는 재지 않았다(`Invoke-SendLocked` 주석의 못 보는 것).
- 제한은 60초다. 열기 하나는 몇 초에서 스무 초 남짓이고, PowerShell 도구의 기본 제한 2분 안에 기다림과 열기가 함께 들게 했다.
- 잠금 오류는 쏘기 전의 멈춤이라 `quitting=`처럼 같은 파일로 다시 돌려도 세션이 둘 생기지 않는다. 스킬은 한 번만 다시 돌린다.

### 고친 것 (이 세션이 스스로)

- "몸이 끝나거나 던지면 놓는다" 시험의 첫 판은 몸이 끝난 뒤 다른 pwsh가 바로 잡는지 봤다. 그런데 잡은 스레드가 살아 있어도 마지막 핸들이 닫히면 뮤텍스가 사라져, 놓지 않은 판도 잡혔다(커밋하지 않은 스크래치 스크립트에서 열어 둔 핸들이 없을 때 `free`, 있을 때 `held`를 손으로 봤다). 핸들을 열어 둔 채 다른 스레드에서 잡게 고쳤고, 변이 "몸 뒤에 잠금을 놓지 않는다"가 빨개졌다.
- 기다림과 버려짐 시험의 첫 판은 테스트 프로세스의 타이머가 1초 뒤 놓으라는 표지를 썼다. PC가 바빠 pwsh 서버가 늦게 뜨자 쥔 쪽이 먼저 끝나 `waited=0s`로 잡았고(변이 "버려진 잠금을 받지 않는다"의 실행. 그 시험의 기준선이 339.85초였다), 그래서 버려짐을 재지 못한 채 빨개졌다. 표지를 pwsh 서버 안에서 핸들을 하나 연 뒤 1초 있다가 쓰게 고쳤다.
- 제한 시간 시험에 던질 때까지의 시간 단언(10초 미만)을 더했다. 오류 문구는 받은 제한의 수를 적으므로, 메시지만 보는 첫 판은 그 제한을 버리고 더 오래 기다리는 판을 가르지 못한다(코드를 읽었다). 변이 "제한을 넘겨 기다린다"가 그 단언으로 빨개졌다.
- 변이 도구가 `tools/open_session.ps1`에 변이를 넣어 둔 채 도는 사이 같은 파일의 주석을 고쳤다(`hook_edit_during_mutate`가 짚었다). 도구는 어긋남 하나로 1로 끝났고, `git diff`에 변이는 남지 않았으며 주석 고침은 남았다.

### 검사 (커밋 전, 셀프 리뷰 전)

- `uv run pytest -q tests/tools/test_open_session.py -k "잠금 or 쥔_프로세스"`: 6 passed(26.79초. 다른 세션이 PC를 함께 쓰던 앞선 한 번은 같은 여섯이 7분 48초였다).
- `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/harness/probes/open_session_lock_mutations.toml`: 변이 8 모두 기대대로(표지까지). 표지를 보려고 셀프 리뷰 전에 돌렸고, 리뷰를 반영해 커밋한 뒤 다시 돈다.
- `uv run python tools/canary.py .scratch/harness/probes/canary/open_session_lock.toml <스크래치>`: 통과 4, 실패 0, "없음" 섞인 통과 0(claude 2.1.302. 대조군 주 체크아웃은 셋 다 "없음").
- `uv run python tools/sibling_overlap.py`: 번호 겹침 없음. 카나리아 알림으로 1이었고, 위 명세를 더했다. 형제 010·011이 일지 2026-10-26-10·09를 쥐었다. 그쪽이 먼저 병합되면 이 일지(08)를 그 뒤 번호로 옮긴다.
- `uv run python tools/run_checks.py`(백그라운드): lint-imports, check-ticket, zizmor, check-instructions, check-type-escapes, pyright, pyright-linux가 통과한 뒤, pytest와 web이 끝나기 전에 인계로 멈췄다(TaskStop). 멈춘 뒤 기록에 web-verify(eslint 단계)·run-hooks·pytest가 모두 188.5초 무렵 `Failed`로 찍혔고 pytest는 `node down: Not properly terminated`였다. 끊긴 흔적으로 보고 판정에 쓰지 않는다(어림).

### 인계 (셀프 리뷰 직전)

- `/code-review`(base `origin/main`)를 부르자 `hook_handoff`가 세션 컨텍스트 324,176 토큰으로 `셀프 리뷰 직전` 계기를 냈다. "인계할 때" 1의 다섯 가운데 맞는 것이 없어(요청 범위는 PR과 병합까지, 이어받을 상태 없음, 이 세션이 쓴 `인계 못함` 줄 없음, `get_session`의 `self`에 `parentSessionId` 없음) 넘긴다. 셀프 리뷰의 단계는 밟지 않았다.
- 이 세션의 지금 제목: `chore/014-open-session-deeplink-lock`(인계 전).
- 주 체크아웃은 `sibling_overlap`의 형제 줄에서 origin/main과 같은 `92b6145`였다.
- 지시문:

```
다음 작업: .scratch/harness/issues/014-open-session-deeplink-lock.md를 잇는다. 두 세션이 거의 같이 쏜 딥링크가 겹쳐 열기가 실패하는지 앱 로그로 갈랐고(겹침이었다), tools/open_session.ps1이 기계 전체의 잠금을 잡고 쏜다(대기열 360)
다음 단계: 구현
어디서: 새 세션. 같은 브랜치·워크트리라 git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 360을 티켓 .scratch/harness/issues/014-open-session-deeplink-lock.md로 쓰고 한다
브랜치: chore/014-open-session-deeplink-lock
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: .scratch/harness/issues/014-open-session-deeplink-lock.md, docs/journal/2026-10-26-13-open-session-deeplink-lock.md
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경(미추적 티켓·일지·프로브 deeplink_overlap.py·변이 표·카나리아 명세 포함)이 워크트리에 있고 셀프 리뷰(/code-review, base origin/main, 티켓 .scratch/harness/issues/014-open-session-deeplink-lock.md)부터 한다. docs/journal/2026-10-26-13-open-session-deeplink-lock.md
확인할 선행 조건: 검사 러너(tools/run_checks.py)는 pytest와 web이 끝나기 전에 인계로 멈췄다. 셀프 리뷰를 반영한 뒤 커밋의 pre-commit으로 갈음하거나 다시 돈다. 변이 표 open_session_lock_mutations.toml의 전체 실행은 리뷰를 반영해 커밋한 뒤 다시 돈다. 잠금 시험이 CI의 리눅스 pwsh에서도 버려진 뮤텍스를 받는지는 아직 보지 않았다
이번 요청 범위: PR과 병합까지
```

- 제목을 `chore/014-open-session-deeplink-lock (인계함)`으로 바꿨다. 검사 러너를 멈췄다. 워크트리 잠금을 풀었다(`git worktree unlock C:/project/agent/.claude/worktrees/014-open-session-deeplink-lock`, 출력 없음).
- open-session을 부른다 2026-10-26T08:23:12Z

## 이어서 (셀프 리뷰부터)

> 사용자: 대기열 360을 티켓 .scratch/harness/issues/014-open-session-deeplink-lock.md로 쓰고 한다 (위 인계 지시문. 범위는 PR과 병합까지)

### 시작

- 제목을 `chore/014-open-session-deeplink-lock`으로 바꿨다. `git worktree list`에서 브랜치가 `.claude/worktrees/014-open-session-deeplink-lock`에 있어 `EnterWorktree(path)`로 들어갔다. 커밋하지 않은 변경 열한 개(수정 여섯, 미추적 다섯)가 그대로 있었다.
- `git fetch origin main` 뒤에도 origin/main은 `92b6145`다.

### 셀프 리뷰

- `/code-review`(base `92b61458`, 파일 열한 개, 커밋 0, 미추적 다섯). 표준 축은 sonnet·high, 명세 축은 이 세션의 모델로 돌렸다. 두 브리프에 .NET `Mutex` 문서의 Remarks 발췌(https://learn.microsoft.com/en-us/dotnet/api/system.threading.mutex)와 갈래 밟기 문단을 실었다.
- 표준 축(Major 1, Minor 7, Nit 다섯 묶음): (M) 스킬 3단계가 잠금 오류에 "턴을 끝낸다"와 "한 번 다시 돌린다"를 함께 말한다. (m) 60초와 PowerShell 도구의 기본 2분이라는 말의 근거가 없고, 트랜스크립트로 재니 열기의 도구 호출이 중앙값 8.9초·최대 49초라 기다림 60초를 더하면 2분에 닿는다. (m) 잠금 뒤에도 겹치면 옛 사본이거나 사람의 손이라는 닫힌 주장의 반례로 잠금 없이 딥링크를 쏘는 프로브(`composer_*.ps1`, `probe_deeplink.ps1`)가 있다. (m) 344/334와 784줄이 지금 다시 돌리면 348/338, 789줄이다. (m) 변이 표 README 행이 "결과는 아직 없다"인데 일지는 돌렸다고 적었다. (m) `Send-Prompt`의 앞 점검이 잠금 안에서 돈다. (m) "뒤의 딥링크가 입력창을 덮었다"는 동시 발생만 쟀다. (m) "막히면"의 `deeplink_overlap.py` 안내가 출력 가운데 무엇을 볼지, 종료 코드가 늘 1이라는 것을 말하지 않는다. (n) 표지 딥링크는 모델 줄이 있을 때만 쏜다, 마지막 핸들이 닫히면 뮤텍스가 사라진다는 문장에 근거 표기가 없다, 이름이 좁고 인자 `$timeoutSec`이 스크립트의 `$TimeoutSec`과 대소문자만 다르다, 일지의 "여섯 모두 같은 문구로 빨갰다"는 AST 시험에 맞지 않을 수 있다, 두 프로브의 짝짓기 중복, `_Holder`의 `mode: str`.
- 명세 축(Minor 9, Nit 넷): 변이 README 행(표준 축과 같다), 스킬 3단계의 어긋남(같다), `held=`·폴더 오류로 놓은 뒤 기다리던 열기가 사람을 기다리는 화면을 덮는 것을 스킬이 알리지 않는다, 닫힌 주장의 반례(같다), 784줄이 짝지은 끝내기 줄 780을 넘는다, 일지의 "여섯 모두"(같다), `Select-QuitLogs`·`Get-AppQuitMarker`가 아직 "옆 돌림 파일 `main1.log`"를 전제한다, 되돌리기가 잠금 안에 있는지 고정하는 시험이 없다, README의 "판정 기준은 대조군 전에 정했다"에 기록이 없다. (n) 11:50:28 문장의 근거 종류, `defaults`의 잠금 오류 문구에 "같은 파일로", overlap 독스트링의 로그 범위 서술, 5초 창이 남의 딥링크를 자기 것으로 잡을 수 있다.
- 리뷰 밖에서 이 세션이 찾은 것(Major): 인자 이름을 따라가다 PowerShell의 동적 범위를 손으로 재현했다. `Invoke-SendLocked`의 인자와 지역 변수가 몸이 부르는 `Send-Prompt`에 그대로 보여, `Wait-For`의 기본값 `$TimeoutSec`이 스크립트 파라미터(30) 대신 `$timeoutSec`(= `-LockTimeoutSec`, 60)이 된다. `$name`도 잠금 이름으로 보인다(스크래치 `pwsh -Command`로 `TimeoutSec=60 name=lockname`). 인자를 `param` 안의 `$private:`로 적어도 새었고, 함수 안에서 `Set-Variable -Option Private`로 다시 매기면 막혔다.

### 반영

- 고쳤다(동적 범위, Major): `Invoke-SendLocked`가 몸에 들어가기 전에 인자 셋을 `Set-Variable -Option Private`로 다시 매기고 지역 변수를 `$private:`로 둔다. 시험 `test_몸은_잠금_함수의_인자와_지역_변수를_보지_않는다`가 몸 안에서 보이는 이름을 바깥과 견주고 `$TimeoutSec`의 값을 따로 본다. 변이 셋(인자 셋을 가리지 않는다, 제한 인자만 가리지 않는다, `$mutex`를 가리지 않는다)이 표지까지 빨갰고, 둘째의 표지 `몸이 바깥의 TimeoutSec 대신 5을 봤다`가 고치기 전의 버그 모양이다.
- 고쳤다(되돌리기 시험, 명세 축 Minor): AST 시험을 "딥링크는 잠금 안에서만 쏜다"로 넓혔다. `Start-Process`를 부르는 함수와 그것을 거쳐 부르는 함수를 모으고(`Open-MarkerDraft`, `Restore-DraftDefaults`, `Send-Prompt`, `Set-Defaults`), 함수 밖의 호출마다 `Invoke-SendLocked` 안인지 본다. 변이 "되돌리기를 잠금 밖에서 부른다"가 `Restore-DraftDefaults=False`로 빨갰다.
- 고쳤다(Nit): `_Holder`의 `mode`를 `Literal["release", "abandon"]`로, 잠금 오류 문구에서 `defaults`에 맞지 않는 "같은 파일로"를 뺐다, 표지 딥링크는 모델 줄이 있을 때만 쏜다고 고쳤다, 11:50:28 문장에 "로그를 손으로 봤다"를, 마지막 핸들 문장에 Win32 `CreateMutexW` 문서의 문장(https://learn.microsoft.com/en-us/windows/win32/api/synchapi/nf-synchapi-createmutexw)과 시험 주석의 손으로 본 기록을 붙였다. "못 보는 것"의 겨루지 않는 상대를 "잠금을 잡지 않고 새 세션 화면을 쓰는 것"으로 적고 옛 사본·진단 프로브·사람의 손을 그 예로 들었다(닫힌 주장, 두 축 Minor).
- `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/harness/probes/open_session_lock_mutations.toml 9 10 11 12`: 변이 4 모두 기대대로.
- 고쳤다(수치와 시간 제한, 표준 축 Minor 둘): `deeplink_overlap.py`가 `--until`(그 로컬 시각까지 쏜 열기만 센다)을 받고, 열기의 길이(쏘고 보내기까지, 호출을 적은 기록부터 결과를 적은 기록까지)의 중앙값·최대와 20·60·120초를 넘은 수를 찍는다. `uv run python .scratch/harness/probes/deeplink_overlap.py --until "2026-10-26 18:00"`(18:22, 종료 코드 1): 측정 349, 측정 아님 2, 증상 멈춤 4 모두 겹침, 다른 멈춤 6과 보냄 339 모두 겹침 없음, 쏘고 보내기까지 483회 중앙값 4.4초·최대 17.2초, 호출 전체 541회 중앙값 16.3초·최대 127.6초(20초 넘음 175, 60초 넘음 9, 120초 넘음 2). 그래서 열기 하나가 보통 몇 초에서 스무 초 남짓이라던 옛 주석은 틀렸고, 기다림 60초를 더하면 도구의 기본 2분에 들지 않는다. `-LockTimeoutSec` 주석을 이 수로 고치고, 스킬 3단계가 PowerShell 도구에 `timeout` 300000을 주게 했다. 344/334는 그 뒤의 열기가 늘어 다시 나지 않던 수라 `--until`을 붙인 349/339로 주석·README·대기열 360을 고쳤다.
- 고쳤다(타임라인 수치, 두 축 Minor): 18:24에 `deeplink_timeline.ps1`을 `Stopwatch`로 재니 791줄을 10.1초에 냈고, MSIX 로그 폴더를 `Select-String`으로 세니 `Starting app {` 796줄, 끝내기 줄 792줄, `Not main instance` 0줄이었다(둘 다 손으로 쟀다). 앞 절의 "784줄을 16초에"는 같은 때의 끝내기 줄 780을 넘어 맞지 않는다. README와 프로브 독스트링을 새 수로 고쳤다.
- 고쳤다(스킬 3단계, 두 축이 함께 낸 Major·Minor): 앞 호출이 멈출 때 턴을 끝내는 목록에서 잠금 오류를 빼고, 잠금 오류는 그 파일만 다시 돌리고 `sent=`가 나오면 나머지를 이어 쏜다고 적었다. 또 멈추면 나머지 파일도 쏘지 않고 "막히면"으로 간다. 원인 서술은 다른 세션의 딥링크가 끼어든 열기만 멈췄다는 뜻으로(표준 축 Minor, 동시 발생만 쟀다), "막히면"에는 출력에서 그 열기의 `fired=` 시각으로 시작하는 줄의 `남의 [...]`를 보라는 것과 종료 코드로 가르지 않는다는 것, 잠금 뒤의 겹침을 "잠금을 잡지 않고 새 세션 화면을 쓴 것"으로 적고 예를 든 것을 넣었다. 카나리아가 묻는 세 문구는 그대로다.
- 고쳤다(근거의 종류, 명세 축 Minor·Nit): README와 프로브 독스트링에 판정 기준을 정한 차례는 이 세션의 기록이고 해시로 고정한 사전 등록이 아니라고, 다른 해석(PC가 바빴다)이 내야 할 칸(겹침 없는 증상 멈춤, 겹치고도 보낸 열기)이 둘 다 0이라고, 입력창의 글은 재지 않았다고 적었다. 독스트링의 로그 범위 서술을 파일마다의 범위로 고치고, 자기 줄이 빠진 회차의 5초 창이 남의 딥링크를 자기 것으로 잡을 수 있다는 것을 못 보는 것에 더했다.
- 바로잡는다(앞 절의 기록): "구현 전에는 여섯 모두 `Invoke-SendLocked 가 스크립트에 없다`로 빨갰다"는 AST 시험에 맞지 않는다. 그 시험은 함수를 떼지 않고(`_call("", …)`) 목록 단언으로 빨개진다(두 축이 코드를 읽어 짚었다. 그때의 출력은 남지 않았다).
- 남긴 것: `Send-Prompt`의 앞 점검(인자, URL 길이, 모델 줄, `quitting=`)이 잠금 안에서 돈다(표준 축 Minor). 다른 열기가 잠금을 쥐었을 때만 잘못된 호출이 늦게 실패하고, 앞 점검을 잠금 앞으로 빼려면 `Send-Prompt`의 차례를 갈라야 해 이 티켓의 변경보다 크다. `held=`·폴더·모델 오류로 멈춘 화면을 기다리던 열기가 덮는 것(명세 축 Minor)은 잠금이 사람을 기다릴 수 없어 그대로 두고 `Invoke-SendLocked`의 못 보는 것에 남겼다. 이름 `Invoke-SendLocked`가 `defaults`까지 감싸 좁다는 것과 두 프로브의 짝짓기 중복(Nit)은 판단 항목이라 두었다. `Select-QuitLogs`·`Get-AppQuitMarker`가 "옆 돌림 파일 `main1.log`"를 전제하는데 지금 돌림은 `main1`이 가장 최근 돌림 파일이 아니다(명세 축 Minor, 18:20에 로그 폴더를 손으로 보니 `main2.log`가 10-22~10-24 14:58, `main1.log`는 10-24 14:29~14:42의 1650바이트였다). 끝내기 판정의 고침이라 이 잠금과 따로 시험을 세울 일이어서 새 작업으로 제안한다.
- 스킬을 고친 뒤 카나리아 `uv run python tools/canary.py .scratch/harness/probes/canary/open_session_lock.toml <스크래치>`(claude 2.1.302): 통과 4(워크트리 3/3, 주 체크아웃의 옛 판 `92b61458` 1/1), 실패 0, "없음" 섞임 0. 대조군은 세 문구가 없는 옛 판이라 1에 `stale=` 문장을 옮기고 2·3에 "없음"이라 답했다. `# 최신 결과:` 줄은 같은 수라 그대로 뒀다.
- 바꾼 표현의 잔존: 살아 있는 문서에서 고칠 자리는 변이 표 README 행 하나였다(전체 실행 뒤 고친다). 일지 앞 절(22·23·31·32행)은 기록이라 두고 위 바로잡는 줄로 갈음했고, 대기열 382~384의 일치는 닫힌 행의 기록이다.
- 변이 표 전체(셀프 리뷰를 반영한 커밋 전 판, 18:34~18:50): 변이 12 모두 기대대로, 종료 코드 0. README 행을 열둘과 이 결과로 고쳤다. 도구는 커밋하지 않은 변경이 있는 전체 실행이라고 알렸다(대기열 359). PR 직전 리뷰를 반영해 커밋한 뒤 다시 돈다.
- 시간이 튄 회차: 그 실행에서 버려짐 시험의 기준선이 572.43초, 변이 4가 153.31초, 변이 2가 175.84초였다. 18:43에 그 pytest는 자식 프로세스 없이 스레드 하나로 CPU를 쓰고 있었다. 18:54~18:57에 버려짐 시험을 혼자 세 번 돌리니 5.29·6.02·8.11초였고(`--durations`의 call 4.4~5.2초), 변이 4만 다시 돌리니 기준선 7.94초, 변이 8.57초였다. 그래서 시험의 길이 아니라 그때의 PC로 본다. 까닭은 어림이다. pytest 9.1.1은 세션을 닫을 때 최근 셋을 뺀 옛 `pytest-of-User/pytest-N`을 지우고(`tmpdir.py`의 `register=self._exit_stack.callback`, 코드를 읽었다), 같은 때 다른 워크트리(`011-mutate-check-and-marker`)의 xdist 여덟 일꾼이 18:34:58에 떴으며, 남은 `garbage-*` 폴더 하나(17:53~18:01의 xdist 실행)가 파일 43,337개·폴더 34,786개라 훑기만 130.8초였다(손으로 쟀다). 9분을 쓴 것이 그 지우기라는 것은 재지 않았다. 회고 후보로 남긴다: 이 PC에서는 pytest 하나가 남의 큰 임시 트리를 지우느라 몇 분을 더 쓸 수 있어, 변이 도구의 600초 제한과 pre-commit 시간에 닿는다.
- PR 직전 `bug-perf-review`에 밀 주장으로 넘길, 반영하며 새로 쓴 사실 문장(원문):
  - `tools/open_session.ps1`의 `-LockTimeoutSec` 주석: "`send` 호출 하나는 541회 가운데 중앙값 16.3초, 60초를 넘은 것이 아홉, 가장 긴 것이 127.6초였다(deeplink_overlap.py --until "2026-10-26 18:00" 의 호출 전체. 훅과 허락을 기다린 시간도 든다). 그래서 60초면 거의 모든 열기를 기다리고, 넘기면 스킬이 한 번 다시 돌린다."
  - 스킬 3단계: "기본 2분에는 잠금을 기다리는 60초와 가장 긴 열기(128초)가 함께 들지 않는다", "자기 딥링크 뒤 보내기 전에 다른 세션의 딥링크가 끼어든 열기만 입력창을 찾지 못하거나 지시문이 바뀌었다며 멈췄다(대기열 360)", "잠금 오류로 멈추면 아래대로 그 파일만 다시 돌리고, 거기서 `sent=`가 나오면 나머지를 이어 쏜다."
  - `Invoke-SendLocked` 머리 주석: "아무도 기다리지 않았으면 마지막 핸들과 함께 뮤텍스가 사라져 다음 열기는 새 뮤텍스를 잡는다(Win32 CreateMutexW 문서의 "The mutex object is destroyed when its last handle has been closed."", "`param` 안에 `$private:` 를 붙인 판도 샜고, 몸에 들어가기 전에 `Set-Variable -Option Private` 로 다시 매기니 막혔다."
  - README `deeplink_overlap.py` 행: "그때 PC가 바빠 화면이 늦게 섰다는 다른 해석이면 겹침 없는 증상 멈춤과 겹치고도 보낸 열기가 나와야 하는데 둘 다 0이었다." README `deeplink_timeline.ps1` 행: "낸 줄은 끝내기 줄과 짝지은 기동이라 끝내기 줄 수를 넘지 않는다."
  - `deeplink_overlap.py` 독스트링의 못 보는 것: "자기 딥링크의 줄이 로그에 없고 그 5 초 안에 남의 딥링크가 있으면 그것을 자기 것으로 잡아, 측정 아님이 아니라 측정으로 센다."

### 검사 (셀프 리뷰 반영 뒤, 커밋 전)

- `uv run python tools/run_checks.py`(19:02 무렵~19:16, 백그라운드): 열 가지 모두 Passed, 종료 코드 0. 오래 걸린 것은 pytest 872.0초, web-verify 760.2초, run-hooks 328.2초다(다른 워크트리 세션의 검사가 함께 돌았다).
- `uv run ruff check .`: All checks passed. `uv run ruff format --check .`: 1055 files already formatted.
- 티켓 AC7을 체크하고 Status를 done으로 바꿨다.

### 커밋

- 첫 `git commit -F`(19:19)의 pre-commit이 실패했다. `pyright --pythonplatform Linux`가 19:20부터 node 자식 없이 CPU 0.5초만 쓰며 멈췄고(러너의 제한은 4200초), 19:53에 같은 명령을 따로 치니 57초에 `0 errors, 0 warnings, 0 informations`였다. 그래서 명령 줄이 이 워크트리의 그 pyright인지 본 뒤 그 트리를 `taskkill /T /F`로 껐다(`pyright-linux ... Failed (2093.6s)`). 같은 실행의 pytest는 1001.13초에 셋이 빨갰다(`test_probe_kit.py`의 배출 제한 시간, `test_interrupt.py`의 닫기 중 중단, `test_rerun_runner.py`의 오염 재실행). 셋 다 이 브랜치가 건드리지 않은 파일이고, 20:00에 혼자 돌리니 37.69초에 모두 통과했다. 다른 세션의 검사(`pnpm -C web verify`, `pnpm -C web visual`)가 함께 돌던 때의 시간 단언으로 본다(어림이다).
- 인용 대조가 경고 6건을 냈다. 모두 위 셀프 리뷰·반영 절에서 고치기 전의 문장이나 뜻을 따옴표로 옮긴 자리라, 따옴표를 떼고 풀어 썼다.
- 다시 친 커밋은 `SKIP=pyright-linux`로 그 검사만 뺐다. 19:54에 손으로 친 결과가 초록이고, 그 뒤 고친 것은 이 일지 하나다(CLAUDE.md 검증 명령 절의 `SKIP`으로 뺀 검사는 손으로 친다).
- 그 커밋(20:02~20:21)도 pytest 하나로 실패했다. 1080.09초에 5596 통과, `test_rerun_runner.py::test_오염이_한_번이면_다시_돌고_두_번이면_그_과제를_모든_갈래에서_뺀다`가 `assert 1 == 0`이었고(`_끝남(task, hang=3.0)`을 쓰는 시간 시험이다), 나머지 아홉 검사는 지났다. 같은 시험이 첫 커밋에서도 빨갰다. 20:23에 그 파일 전체를 혼자 돌리니 53 passed in 168.06s였다. 이 브랜치는 그 파일과 그것이 부르는 도구를 바꾸지 않았고, 같은 파일의 다른 시험이 부하 아래에서만 빨간 일을 일지 2026-10-24-10과 2026-10-25-02가 대기열 306이 받아들여 닫은 종류로 보고 일지에만 적었다. 그래서 회차를 더하지 않는다. 다른 세션의 검사가 계속 돌아 다시 쳐도 또 빨개질 수 있어, 셋째 커밋은 `SKIP=pyright-linux,pytest`로 쳤다. pytest는 이 커밋과 같은 나무에서 위 실행이 그 시험 하나 말고 모두 지났고 그 파일은 혼자 지났으며, CI가 리눅스에서 전체를 다시 돈다.
- 셋째 커밋 `1ecdb2a2`(20:27~20:32): 나머지 검사가 모두 지났다.

### 인계 (커밋 뒤)

- 커밋 뒤 `hook_handoff`가 컨텍스트 344,213 토큰(문턱 200,000)으로 인계를 알렸다. next-session "인계할 때" 1의 인계하지 않는 다섯에 들지 않는다. 커밋은 성공했고, 요청 범위는 PR과 병합까지이며, 이 세션의 지시문은 `인계: 셀프 리뷰 직전`이라 다른 경계이고, 이 세션이 쓴 `인계 못함` 줄은 없으며, `get_session self`에 `parentSessionId`가 없다.
- 이 세션의 지금 제목: `chore/014-open-session-deeplink-lock`. 넘기며 `chore/014-open-session-deeplink-lock (인계함)`으로 바꾼다.
- 이 절은 커밋하지 않았다. 새 세션이 이어 쓰고 커밋한다.
- 지시문:

```
다음 작업: .scratch/harness/issues/014-open-session-deeplink-lock.md. open-session 이 딥링크를 쏘기 전에 기계 전체의 잠금을 잡는 변경의 PR 직전 리뷰, PR, 병합
다음 단계: 구현
어디서: 새 세션. 같은 브랜치·워크트리라 git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 360을 티켓 .scratch/harness/issues/014-open-session-deeplink-lock.md로 쓰고 한다
브랜치: chore/014-open-session-deeplink-lock
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-26-13-open-session-deeplink-lock.md의 "이어서" 절 끝(반영의 밀 주장 목록, 검사, 커밋, 인계), docs/agents/issue-tracker.md
이어받을 상태: 인계: 커밋 뒤. 1ecdb2a2에 셀프 리뷰 반영, 검증 명령, 카나리아 통과 4, 커밋 전 판의 변이 표 열둘, 티켓 done을 담았다(pre-commit은 SKIP=pyright-linux,pytest. 까닭은 일지 "커밋" 절). 일지의 인계 절은 그 뒤에 더했고 커밋하지 않았다. 남은 것은 origin/main 합치기, PR 직전 리뷰(CodeRabbit CLI는 Seat: not assigned라 /security-review와 bug-perf-review를 나란히. bug-perf-review 브리프에는 일지의 "PR 직전 bug-perf-review에 밀 주장" 목록을 싣는다)와 반영, 반영을 커밋한 뒤 변이 표 전체를 다시 돌려 README 행과 일지를 고치기, 푸시, /git-pr(체크리스트에 대체 리뷰 둘과 SKIP의 근거), 봇 회차, 워크트리에서 병합, 회고와 "다음"이다. Select-QuitLogs·Get-AppQuitMarker가 main1.log를 옆 돌림 파일로 전제하는 것은 새 작업 카드로 제안할 일이고 아직 내지 않았다. docs/journal/2026-10-26-13-open-session-deeplink-lock.md
확인할 선행 조건: 잠금 시험이 CI의 리눅스 pwsh에서도 버려진 뮤텍스를 받는지는 아직 보지 않았다(PR CI에서 처음 본다). 이 커밋의 나무에서 pytest 전체가 한 번에 다 지난 실행은 아직 없다(일지 "커밋" 절. CI의 python 잡이 본다)
이번 요청 범위: PR과 병합까지
```

- 제목을 `chore/014-open-session-deeplink-lock (인계함)`으로 바꿨다. 이 세션이 띄운 백그라운드 작업은 모두 끝나 있었다. `git worktree unlock`은 `is not locked`였다.
- open-session을 부른다 2026-10-26T11:35:13Z

## 이어서 (PR 직전 리뷰부터)

> 사용자: 대기열 360을 티켓 .scratch/harness/issues/014-open-session-deeplink-lock.md로 쓰고 한다 (위 "커밋 뒤" 인계 지시문. 범위는 PR과 병합까지)

### 시작

- 제목을 `chore/014-open-session-deeplink-lock`으로 바꿨다. 첫 `git worktree list`는 승인 창에서 거부됐고, 사용자가 실수였다고 해 다시 쳤다. 브랜치가 `.claude/worktrees/014-open-session-deeplink-lock`에 있어 `EnterWorktree(path)`로 들어갔다. HEAD는 `1ecdb2a2`, 커밋하지 않은 변경은 이 일지 하나였다.
- `git fetch origin main` 뒤 origin/main은 `3acbd867`(harness 013 #389, harness 011 #388)이었고 `git merge --no-edit origin/main`이 충돌 없이 합쳤다.
- `uv run python tools/sibling_overlap.py`가 1로 끝났다. 011의 일지 2026-10-26-09가 병합돼 이 일지(그때 08)가 이름순으로 앞섰다. `--move`로 2026-10-26-13으로 옮겼고, 인용은 프로브 README, 카나리아 명세, 대기열, 이 일지에서 고쳐졌다. 위 "검사" 절의 "이 일지(08)"는 그때의 기록이라 두었다.
- main에서 온 규약: 변이 도구의 `--check`가 빨강을 기대한 변이의 표지가 시험 원문에 글자 그대로 있으면 알린다(대기열 417). `PYTHONUTF8=1 uv run python tools/mutate.py --check .scratch/harness/probes/open_session_lock_mutations.toml --since 92b61458`: 변이 12를 골랐고 알림 없이 `원문 확인: 변이 12 모두 원문이 한 번씩 있다`였다.

### PR 직전 리뷰

- CodeRabbit CLI 대신 `/security-review`와 `bug-perf-review`(base `3acbd867`)를 나란히 돌렸다. `bug-perf-review` 브리프에는 위 "PR 직전 bug-perf-review에 밀 주장" 다섯을 원문으로 실었다.
- `/security-review`: 찾는 서브태스크가 신뢰도 8 이상의 후보를 내지 않아 거르는 서브태스크는 띄우지 않았다. 고정된 뮤텍스 이름을 같은 PC의 다른 주체가 쥐면 열기가 멈추는 것은 서비스 거부라 범위 밖이라고 적었다.
- `bug-perf-review`(호출 29, Critical·Major 없음, 유효 4·보류 2·오탐 5): 그 서브에이전트가 `tests/tools/test_open_session.py` 전체를 돌려 111 통과(92초)였고, `deeplink_overlap.py --until "2026-10-26 18:00"`의 출력이 README와 주석의 수와 같았다고 했다. 밀 주장 다섯은 모두 근거와 맞았고, 1·2의 "열기"라는 말만 아래 첫 지적으로 냈다.
- 판정(이 세션이 코드를 다시 열어 보았다):
  - 유효, 고쳤다: 스킬 3단계의 "가장 긴 열기(128초)"와 `-LockTimeoutSec` 주석의 "가장 긴 열기"는 열기가 아니라 호출 전체다(`deeplink_overlap.py`의 `calling`은 호출을 적은 기록부터 결과를 적은 기록까지). 주석에 쏘고 보내기까지(483회, 최대 17.2초)를 함께 적고, 명령만의 길이는 재지 않았으며 두 수가 그 아래와 위 끝이라고 고쳤다. 5분 제한은 그대로다.
  - 유효, 고쳤다: "막히면"과 그 프로브 독스트링의 "`fired=` 시각으로 시작하는 줄"은 출력과 다르다. 줄은 `%Y-%m-%d %H:%M:%S.%f`의 날짜로 시작한다(`deeplink_overlap.py` 329행). "날짜 뒤에 그 열기의 `fired=` 시각이 오는 줄"로 고치고, 보낸 열기는 겹쳤을 때만 줄이 찍힌다는 것을 더했다(351행의 조건).
  - 유효, 고쳤다(성능): 그 진단 호출에 시간 제한이 없다. 서브에이전트가 출력 파일의 만든 시각과 끝난 시각으로 82초를 봤다(다른 시험과 함께 돈 때). "막히면"이 도구에 `timeout` 300000을 주게 했다.
  - 유효, 고쳤다: 모델을 고른 뒤 끊긴 열기의 버려진 잠금을 받은 열기는 그 열기가 고른 값을 원래 값으로 읽어 되돌린다(`Read-DraftDefaults`가 새 세션 화면의 값을 읽는다). 잠금 전에도 있던 일이라 `$note`와 스킬 3단계에 그 말을 더하는 데서 그쳤다. 변이 4의 `old`도 같은 문구로 고쳤다.
  - 보류, 두었다: `split`·`focus`가 잠금 밖이라, 잠금을 놓은 열기의 세션이 이어 거는 행 누르기(Invoke)와 메뉴 키(Enter, →, Esc)가 막 쏜 뒤 열기의 새 세션 화면을 옮기거나 그 입력창에 들어갈 수 있다. 잠금은 그 차례를 만든다(앞 열기가 놓자마자 뒤 열기가 쏜다). 겹친 회차는 세지 않았다. 고치려면 `focus`가 행 제목을 기다리는 동안(스킬은 90초) 잠금을 쥐지 않게 `Focus-Session`을 갈라야 하고, 시험·변이와 스킬 5단계의 시간 제한까지 바뀐다. `Invoke-SendLocked`의 못 보는 것을 이 길로 고쳐 적고 새 작업으로 제안한다.
  - 보류, CI에서 본다: 리눅스 pwsh가 `[Environment]::Exit(0)`로 끝난 프로세스의 뮤텍스를 버려진 것으로 알리는지. 인계 지시문의 선행 조건과 같다.
