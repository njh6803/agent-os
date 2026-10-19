# 2026-10-19 (17) 토큰 보고서 작업이 CPU가 꽉 찼을 때 git 10초 제한에 걸린 원인과 수정

next-session 지시문으로 연 새 세션의 기능 밖 진단이다. 작업 스케줄러 작업 `agent-os token_report daily`가 10/19 08:00에
`tools/token_report.py`의 `main_checkout()`에서 `git rev-parse` 10초 제한(`GIT_TIMEOUT`)을 넘겨 종료 코드 2로 끝난 원인을
찾고, 원인이 서서 고쳤다.

> 사용자: "다음 작업: 기능 밖 진단(토큰 보고서 스케줄러). 토큰 보고서를 매일 만드는 작업 스케줄러 작업(`agent-os token_report daily`)이 2026-10-19 08:00에 `tools/token_report.py`의 `main_checkout()`에서 `git rev-parse` 10초 제한(`GIT_TIMEOUT`)을 넘겨 종료 코드 2로 끝난 원인을 찾는다 / 다음 단계: 진단. 원인이 확인되면 구현 / 어디서: 새 세션. 이 PC의 데스크톱 앱에서 연다. 작업 스케줄러, `LastTaskResult`, 주 체크아웃의 `.scratch/token-report/scheduler.log`는 이 PC에만 있어 클라우드 세션에서는 볼 수 없다 / 시작 프롬프트: /diagnosing-bugs 작업 스케줄러 `agent-os token_report daily`가 2026-10-19 08:00에 `git rev-parse` 10초 초과(종료 코드 2)로 실패했다. docs/journal/2026-10-19-07-token-usage-09-close.md의 "작업 스케줄러 실패" 절부터 읽는다 / 브랜치: chore/token-report-git-timeout / 모델: Opus 5.5 / medium. 레벨 스윕의 갈래 / 읽을 것: docs/journal/2026-10-19-07-token-usage-09-close.md의 "경보 줄"과 "작업 스케줄러 실패" 절, .scratch/token-usage/issues/08-apply-outside-settings.md의 "이 티켓이 정할 것" 1(작업 이름과 로그 위치) / 이어받을 상태: 진단은 아직 시작하지 않았다. 제한 시간을 늘리거나 재시도를 넣는 것은 원인을 모르고 하는 추측 수정이라 하지 않기로 했다(위 일지). 앞 세션은 그 시각에 PC가 몹시 바빴을 것이라고 어림만 했다(지역 시각 07:10~08:58에 다른 세션 여럿이 돌았다) / 확인할 선행 조건: 2026-10-20 08:00 실행의 결과(`LastTaskResult`와 `scheduler.log`). 이 지시문을 쓴 클라우드 세션은 그 실행보다 먼저 쓰였고 PC를 볼 수 없어 확인하지 못했다. 같은 진단을 이미 시작한 세션이 있는지도 확인하지 못했다 / 이번 요청 범위: PR과 병합까지. 원인을 찾지 못하면 코드는 고치지 않고, 진단 결과만 일지에 적어 병합한다" (지시문 열 줄을 `/`로 이어 옮겼다)

## 선행 조건

- **10/20 08:00 실행.** 이 세션은 10/19에 열려 그 실행이 아직 오지 않았다. `Get-ScheduledTaskInfo`의 다음 실행은 10/20
  08:00이고 마지막 결과는 10/19 08:00의 2다. 병합 뒤 그 실행의 결과가 이 수정의 첫 실전 확인이다(아래 "다음").
- **같은 진단을 시작한 세션.** 워크트리 목록에 이 브랜치 이름이 없었고, 이 세션이 새로 만들었다.

## 그때 무엇이 돌았나

- **PC는 깨어 있었다.** 10/18 20:00~10/19 08:10의 시스템 기록에 절전·부팅 이벤트가 없다. 08:00 전후의 다른 예약 작업은
  07:55:55의 Office 감시 작업 하나이고, Claude 예약 세션(토큰 사용 09 마감)은 08:05에 돌았다.
- **실패한 실행은 33초 걸렸다.** `scheduler.log`의 시각이 08:00:33이다. 10/18의 성공한 실행은 08:00:09에 다 썼다.
- **다른 세션의 커밋 전 검사가 돌고 있었다.** `chore/hook-choice-facts` 세션의 커밋 로그(`commit1.log`, 08:08:47에 쓰였고
  병렬 검사 훅의 duration이 681.88s)로 보아 그 pre-commit은 07:57 무렵부터 08:08까지 돌았다. 그 안에서 pytest가 511.7초,
  web-verify가 681.2초였다. 같은 때 다른 세션들의 `cat`·`wc -l`·`git show` 같은 한 줄 명령도 결과가 오기까지 6~9초가
  걸렸다(세션 기록의 호출과 결과 시각).

## 피드백 루프와 원인

작업은 등록 때 우선순위를 주지 않아 기본값 `Priority` 7(BELOW_NORMAL_PRIORITY_CLASS)로 돈다(`Get-ScheduledTask`의
`Settings.Priority`, 일지 2026-10-16-71의 등록 명령). 그 아래의 cmd·uv·python·git도 그 클래스를 물려받는다고 본다(프로브의 `inherit`는 파이썬이 띄운 파이썬 한 단계만 쟀고, cmd·uv·git은 같은 규칙을 따른다고 어림한다). 보통 우선순위의
프로세스가 CPU를 다 쓰면 BELOW_NORMAL 프로세스는 거의 돌지 못한다.

`.scratch/token-usage/probes/git_priority_load.py`가 이것을 잰다. 보통 우선순위의 CPU 소모 프로세스를 논리 CPU(16)의 두 배
띄우고 같은 git 명령을 다섯 번씩 쟀다(이 PC, 2026-10-19).

| 갈래 | 중앙값 | 최대 | 10초 초과 |
|---|---|---|---|
| 부하 없음, 보통 | 50ms | 77ms | 0/5 |
| 부하, 보통 | 731ms | 1,159ms | 0/5 |
| 부하, BELOW_NORMAL | 29,468ms | 30,368ms | 5/5 |

BELOW_NORMAL로 띄운 파이썬이 플래그 없이 띄운 손자의 클래스는 16384(BELOW_NORMAL)였다(`inherit`). 그래서 원인은 앞 세션의
어림대로 "PC가 바빴다"가 맞고, 그 위에 작업이 양보하는 우선순위로 돌아 보통 우선순위의 세션 명령(1초 안팎)보다 수십 배
더 굶었다는 것이다.

## 고친 것

- **`main_checkout()`이 git을 띄우지 않는다.** `main_checkout_of(checkout)`이 `.git`을 읽는다. 폴더면 그 체크아웃이, 파일이면
  `gitdir:`이 가리키는 폴더의 `commondir`(없으면 그 폴더)의 부모가 주 체크아웃이다. 선례는 `tools/hook_bash_commit_msg.py`의
  `_common_dir`이다. `GIT_TIMEOUT`과 `subprocess` import를 걷었다.
- **제한을 늘리지 않은 까닭.** 같은 부하에서 BELOW_NORMAL로 띄운 파이썬은 시작만으로 300초를 넘겨 `main_checkout()`에 닿지도
  못했다(프로브의 첫 실행). CPU가 그렇게 굶는 동안에는 어느 제한이든 걸릴 수 있다. 굶는 자리를 없애면 작업은 늦게 끝날 뿐
  실패하지 않는다(작업의 `ExecutionTimeLimit`은 1시간이다).
- **우선순위를 올리지 않은 까닭.** 배경 작업이 세션의 작업에 양보하는 것은 바라는 동작이고, 등록을 바꾸면 저장소 밖 상태를
  바꾸는 일이라 승인이 든다. 고친 코드에서는 남은 일이 모두 시간 제한 없이 돈다.
- **시험.** 넷을 더했다. 프로세스를 띄우면 실패하는 시험(`subprocess.Popen`을 막는다), 주 저장소·연결된 워크트리·
  `--separate-git-dir` 저장소에서 git의 `--git-common-dir` 부모와 같은지 맞대는 시험, `gitdir:` 줄이 없는 `.git` 파일이
  `OSError`인 시험, `.git`이 없으면 `main()`이 "주 체크아웃을 찾지 못했다"로 2를 내는 시험이다.

## 고친 판의 확인

같은 프로브의 `tool` 갈래는 자식 파이썬이 보통 우선순위로 import까지 마친 뒤 스스로 BELOW_NORMAL로 내려가
`main_checkout()` 한 번만 잰다. 고치기 전 판은 `origin/main`(그때 `a60e2ddd`)의 파일을 `tools/_old_token_report.py`로 꺼내 쟀고, 잰 뒤 지웠다.

| 판 | 결과 | 시간 |
|---|---|---|
| 고치기 전 | 5회 모두 `TimeoutExpired` | 37,314~62,001ms(자식 전체) |
| 고친 판 | 5회 모두 성공 | 1ms씩(함수만) |

고치기 전 판이 제한 10초인데 37~62초 걸린 것은, 시간 초과 뒤 git을 끝내고 기다리는 데에도 CPU가 들기 때문으로 어림한다.
08:00 실행이 33초 걸린 것과 같은 꼴이다.

프로브의 첫 판은 ctypes에 핸들 형을 주지 않아 우선순위를 읽고 바꾸는 호출이 조용히 실패했다(`inherit`가 `"0"`, 고치기 전
판도 1초 안에 성공). 자식이 내려간 뒤의 클래스를 `PRIO 16384`로 찍게 해 표지로 삼았다.

## 못 본 것

- 실제 작업 스케줄러 아래에서 부하를 걸고 작업을 돌려 보지는 않았다. 프로브는 BELOW_NORMAL을 `creationflags`와
  `SetPriorityClass`로 흉내 낸다.
- 다른 훅(`hook_session_usage` 등)도 git으로 주 체크아웃을 찾는다. 그 훅들은 세션 아래(보통 우선순위)에서 돌아 이번 꼴에
  들지 않아 보지 않았다.

## 인계(셀프 리뷰 직전)

이 세션(제목 `chore/token-report-git-timeout`)은 컨텍스트가 인계 문턱을 넘은 채 셀프 리뷰 직전에 와서 넘긴다. 커밋하지 않은
변경이 워크트리에 있다(`tools/token_report.py`, `tests/tools/test_token_report.py`, 새 프로브와 README 행, 티켓 09 한 줄,
대기열 366, 이 일지). 린트 둘은 초록이었고 `tests/tools/test_token_report.py`는 87개 통과였다. `tools/run_checks.py`는 띄웠다가
인계하며 멈춰 결과가 없다. 회고와 "다음"은 이 세션이 이미 썼다. 셀프 리뷰에서 PR 직전 `bug-perf-review`에 밀 주장은 이 일지의
"원인", "고친 것", "고친 판의 확인" 절의 사실 문장과 `main_checkout_of` 독스트링이다.

인계 지시문:

```
다음 작업: 토큰 보고서 작업이 CPU가 꽉 찼을 때 git 10초 제한에 걸린 원인을 고친 변경(`main_checkout`이 git을 띄우지 않는다)을 셀프 리뷰하고 커밋·PR·병합까지 마친다
다음 단계: 진단. 원인이 확인되면 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /diagnosing-bugs 작업 스케줄러 `agent-os token_report daily`가 2026-10-19 08:00에 `git rev-parse` 10초 초과(종료 코드 2)로 실패했다. docs/journal/2026-10-19-07-token-usage-09-close.md의 "작업 스케줄러 실패" 절부터 읽는다
브랜치: chore/token-report-git-timeout
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-19-17-token-report-git-timeout.md 전체(원인, 고친 것, 인계 절)
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(`/code-review`, 기준 origin/main, 미추적 포함)부터 한다. 진단과 수정, 프로브 확인, 회고, "다음"은 끝났다. `tools/run_checks.py`는 멈춰 결과가 없다. docs/journal/2026-10-19-17-token-report-git-timeout.md
확인할 선행 조건: 2026-10-20 08:00 작업 실행은 병합하고 주 체크아웃을 당긴 뒤여야 고친 파일로 돈다(일지 "다음")
이번 요청 범위: PR과 병합까지
```

open-session을 부른다 2026-10-19T06:53:19Z

## 셀프 리뷰(이어받은 세션)

`/code-review`, 기준 `a60e2ddd`(origin/main), 커밋 0, 바뀐 파일 5, 미추적 2. 표준 축은 하드 위반 0, 명세 축은
Major 셋을 냈다. 두 축이 함수를 불러 본 반례가 겹쳤다.

고친 것:
- **깨진 `.git`에서 `OSError`가 아니거나 엉뚱한 부모를 돌려줬다**(두 축, Major). UTF-8이 아닌 `.git`은
  `UnicodeDecodeError`로 `main()`의 `except OSError`를 뚫었고, 없는 `gitdir:` 대상과 빈 `commondir`은 git이 128로 거절할
  것을 조용히 다른 폴더로 돌려줬다. `_read_utf8`이 디코드 오류를 `OSError`로 바꾸고, `gitdir:` 폴더·빈 `commondir`·
  공용 디렉터리가 없으면 `OSError`를 낸다. 시험 넷을 더했다(없는 gitdir 폴더, 빈 commondir, 없는 공용 디렉터리, UTF-8이
  아닌 `.git`). 독스트링의 "git과 같다"를 세 꼴(주 저장소, 연결된 워크트리, `--separate-git-dir`)로 좁히고 상위 폴더 찾기와
  `GIT_DIR`을 따르지 않는다고 적었다.
- **잔존**(명세, Major). `tools/hook_session_usage.py` 독스트링의 "`main_checkout` 도 같은 인자를 쓰고 그 확인이 없다"를
  "`tools/token_report.py` 의 `main_checkout` 은 git 을 띄우지 않고 `.git` 을 읽는다"로 고쳤다.
- **고치기 전 판의 기점**(두 축). 프로브 README 행과 프로브 독스트링의 `git show origin/main:…`을 `git show a60e2ddd:…`로
  고정했다. 병합 뒤에는 origin/main이 고친 판이다.
- **근거의 종류**(두 축, Minor). 이 일지의 상속 문장을 "물려받는다고 본다(프로브의 `inherit`는 파이썬이 띄운 파이썬 한
  단계만 쟀다)"로, 대기열 366의 "CPU를 채운 때"를 "돌던 때"로, "자식까지"를 "자식에게. 파이썬이 띄운 파이썬 한 단계를
  쟀다"로 고쳤다.
- **주석 과장**(표준). "`ingest`는 저장소 밖에서도 돈다"를 "`--out`을 주면"으로 좁혔다.
- **시험 단언**(표준). `match="gitdir"`가 `tmp_path` 이름에도 걸려 "gitdir: 줄이 없다"로 좁혔고, `.git`이 없는 경우의 시험
  이름을 `test_dot_git이_없으면_…`으로 바꿨다.

남긴 것: `main_checkout_of`가 `hook_bash_commit_msg._common_dir`과 같은 논리를 다시 쓴 것(Duplicated Code 판단)은 둔다. 그
함수는 훅의 비공개 함수이고, 읽지 못하면 `None`을 내며 없는 폴더를 거르지 않아 이 도구의 계약(`OSError`)과 다르다. `CHECKOUT` 이름(판단)은 이 파일의 다른 상수와
겹치지 않아 둔다. 10/18의 08:00:09, 07:55:55의 Office 작업, `commit1.log`의 681.88s는 이 세션에서 다시 볼 수 없었다.

다시 돌린 것: 린트 둘 초록, `tests/tools/test_token_report.py`와 `tests/tools/test_hook_session_usage.py` 126개 통과. `tools/run_checks.py`는
pytest 하나만 빨강이었다(3566 통과, 1 실패, 15분 56초). 실패는 `tests/tools/test_open_session.py`의
`test_패턴_호출은_제한_시간에_돌아오고_멈춘_호출을_센다[0-ok-0]`가 `ok` 대신 `expand-hung`을 받은 것으로, 이 변경이 건드리지
않은 `tools/open_session.ps1`의 시간 제한 단언이다. 그 시험만 홀로 다시 돌리니 2개 통과(12.65초)였다. 같은 러너의 web-verify가
582초를 쓰던 때다. 나머지 검사 일곱은 초록이었다. 커밋 직전의 손으로 치는 다섯은 pre-commit으로 갈음한다.

PR 직전 리뷰에 밀 주장: `main_checkout_of` 독스트링 전체(특히 "세 꼴에서 git과 같다", "없으면 `OSError`다"), `_read_utf8`
독스트링, `hook_session_usage.py`의 고친 두 줄, 이 일지의 "원인"·"고친 것"·"고친 판의 확인"과 이 절의 사실 문장, 대기열 366
행.

## 회고

후보 넷, 승인 1, 기각 셋, 넘김 0이다.

1. **배경 작업 아래의 짧은 외부 호출 제한**(승인, 대기열 366, 1회차). 사건: 작업 스케줄러가 BELOW_NORMAL로 돌린 git이 10초
   제한을 넘겨 하루치 보고서가 빠졌다. 층: 검사로 판정하기 어렵고(어느 도구가 작업 스케줄러 아래에서 도는지는 코드가 모른다),
   행동이 일어나는 자리는 `.claude/rules/tools.md`의 시간 제한 항목이다. 되돌림: 문장 하나다. rules를 바꾸면 카나리아가 따라와
   이 PR에 싣지 않고 대기열에 둔다.
2. **프로브 첫 판의 ctypes 핸들 형**(기각). 우선순위를 읽고 바꾸는 호출이 조용히 실패했으나, 프로브 규칙대로 둔 표지
   (`inherit`가 16384가 아니면 종료 코드 1)가 첫 실행에서 잡았다. 이미 있는 규칙이 제 몫을 했다.
3. **워크트리 가드가 heredoc과 변수가 든 명령을 두 번 거부했다**(기각). 앱 가드가 그 자리에서 막았고, `CLAUDE.md` 환경 함정이
   이미 적는다. 절대 경로와 Edit 도구로 바꿔 지났다.
4. **전체 세션 기록을 넓은 패턴으로 grep해 120초를 넘겼다**(기각). 사건 하나이고 곧 구간을 좁힌 스크립트로 바꿨다. 고를 층이
   없다.

## 다음

- 병합 뒤 주 체크아웃을 당겨야 작업이 고친 파일로 돈다(작업 디렉터리가 주 체크아웃이다). 10/20 08:00 실행의
  `LastTaskResult`와 `scheduler.log`를 본다.
