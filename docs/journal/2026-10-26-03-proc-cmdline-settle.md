# 2026-10-26 (03) 막 띄운 자식의 명령 줄을 도구가 기다려 읽는다 (harness 013)

> 사용자: 대기열 456을 티켓 .scratch/harness/issues/013-proc-cmdline-linux.md로 쓰고 한다

나란히 여는 여덟 세션 가운데 넷째다. 워크트리 `013-proc-cmdline-linux`, 브랜치 `chore/013-proc-cmdline-linux`. 티켓 `.scratch/harness/issues/013-proc-cmdline-linux.md`.

## 찾은 것

- PR #382(web-widget 06, 일지 2026-10-24-10)가 이미 시험 쪽을 고쳤다. 시험이 띄운 직후 한 번만 읽던 것을 60초 기한까지 거듭 읽게 했고, 도구는 그대로 두었다. 그래서 도구를 쓰는 러너(`tools/rerun_session.py`의 `_ours`, `tools/rerun_runner.py`의 `_close_dead_rounds`)는 막 뜬 프로세스를 읽으면 여전히 같은 틈에서 "우리 것이 아니다"나 "읽지 못했다"로 간다. 이 티켓은 그 틈을 도구에서 메운다.
- 일지 2026-10-24-07 이 윈도(이 PC)의 pre-commit 에서도 같은 단언이 빨갰다고 적었다. 그래서 두 플랫폼을 함께 쟀다.

## 재현 루프

프로브 `.scratch/harness/probes/proc_cmdline_settle.py`(README 행). 회차마다 표지가 든 잠자는 자식을 띄우고 돌아온 직후 `command_line`을 한 번 부른다. 그 뒤 10초까지 다시 읽어 표지가 든 명령 줄이 나온 회차만 측정으로 센다.

- 고치기 전, 리눅스 컨테이너(`python:3.12.10-slim-bookworm`) 500회차: 첫 읽기 None 44. 늦은 진단 읽기에서 0바이트·상태 R 33, 이미 찬 97바이트·상태 R 11. 다른 명령 줄(exec 전 자식) 0.
- 고치기 전, 윈도 홀로 300회차 None 0, 넷을 함께 돌린 1200회차 None 1. 늦은 진단 읽기는 정규화된 블록을 봐서 끊긴 단계를 가르지 못했다.
- 해석: 좀비 탓이라는 해석은 상태 R 로, exec 전의 자식을 읽었다는 해석은 다른 명령 줄 0 으로 갈렸다. 빈 인자 영역이 exec 의 close-on-exec 파이프 닫기 뒤에 채워진다는 커널 순서는 코드를 읽은 어림이다.

## 고친 것

- `tools/proc_command_line.py`: 읽기가 빈 값인데 그 프로세스가 아직 살아 있으면(리눅스는 stat 의 상태가 Z·X 가 아니고, 윈도는 끝 코드가 STILL_ACTIVE) `SETTLE_SECONDS`(5초)까지 다시 읽는다. 그 규칙은 읽기·생존 판정·시계를 받는 순수 함수 `settled`다. 훅의 사본과 AST 로 대조되는 윈도 함수(`_windows_api` 등)는 고치지 않고 `_windows_alive`를 따로 두었다.
- `tests/tools/test_proc_command_line.py`: `settled`의 세 갈래(차면 돌려준다, 살아 있지 않으면 기다리지 않는다, 기한)를 가짜 시계로 고정하고, 실제 프로세스 시험의 거듭 읽기 고리를 뺐다. 시험을 먼저 써 `settled`가 없어 빨간 것을 보고 고쳤다.
- 고친 뒤 리눅스 500회차 None 0, 윈도 넷을 함께 1200회차 None 0. 고친 뒤의 0 이 다시 읽기 덕인지는 이 프로브가 직접 가르지 못한다. 리눅스는 고치기 전 비율이 약 9%라 500회차 모두 틈이 없을 확률이 무시할 만하지만, 윈도는 고치기 전에도 1/1200 이라 가르지 못한다.
- 대기열 456 을 이 티켓으로 닫았다.

범위 밖으로 둔 것: `tools/hook_edit_during_commit.py`가 git 프로세스를 훑으며 읽는 리눅스 cmdline 도 같은 틈이 있다. 훅은 단독 실행이라 `settled`를 가져다 쓰지 못하고, 이 PC(윈도)에서 돈다. 티켓의 Comments 에 적었다.

## 인계 (셀프 리뷰 직전)

- 이 세션의 지금 제목: `chore/013-proc-cmdline-linux`. 인계하며 `chore/013-proc-cmdline-linux (인계함)`으로 바꾼다.
- 셀프 리뷰(`/code-review`)를 부르자 인계 계기(세션 컨텍스트 206,778 토큰, 경계 `셀프 리뷰 직전`)가 와서 리뷰 단계를 밟지 않고 넘긴다. 띄워 둔 `tools/run_checks.py`는 결과 전에 멈춘다. 그 앞에 ruff 둘은 초록, `tests/tools/test_proc_command_line.py`는 10 passed 였다. 다른 게이트는 아직 치지 않았다.
- 커밋하지 않은 변경: `tools/proc_command_line.py`, `tests/tools/test_proc_command_line.py`, `.scratch/harness/probes/README.md`(행 하나), `.scratch/retro-queue.md`(456 닫힘), 새 파일 `.scratch/harness/issues/013-proc-cmdline-linux.md`, `.scratch/harness/probes/proc_cmdline_settle.py`, 이 일지.
- 셀프 리뷰가 밀 주장(나열 밖도 잰다): 모듈 독스트링의 "리눅스 500회차 가운데 44회차·윈도 1200회차 가운데 1회차", "상태는 R", `SETTLE_SECONDS` 주석의 "다시 읽은 표본의 다수가 아직 비어 있을 만큼"(33/44), 커널 순서가 어림이라는 문장, 티켓 Comments 의 `hook_edit_during_commit` 범위 밖 문장, 프로브 README 행의 해석 갈래 문장.

지시문:

```
다음 작업: 받는 세션이 이어 쓸 .scratch/harness/issues/013-proc-cmdline-linux.md. 리눅스 CI에서 tools/proc_command_line.py가 띄운 직후의 자식 명령 줄을 None으로 읽는 까닭을 재현 루프로 가르고 고친다(대기열 456)
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 456을 티켓 .scratch/harness/issues/013-proc-cmdline-linux.md로 쓰고 한다
브랜치: chore/013-proc-cmdline-linux
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: docs/agents/issue-tracker.md, docs/journal/2026-10-26-03-proc-cmdline-settle.md
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review origin/main)부터 한다. 밀 주장과 멈춘 검사 러너는 일지의 인계 절에 있다. docs/journal/2026-10-26-03-proc-cmdline-settle.md
확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. tidy-checkouts는 묶음의 첫 세션이 돈다. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다
이번 요청 범위: PR과 병합까지
```

open-session을 부른다 2026-10-26T06:48:15Z

## 이어받은 세션: 셀프 리뷰

> 사용자: 대기열 456을 티켓 .scratch/harness/issues/013-proc-cmdline-linux.md로 쓰고 한다

`tidy-checkouts`: 루트는 이미 `origin/main`(92b61458)과 같았다. 지운 것은 브랜치 `worktree-010-journal-evidence-hook`, `worktree-013-proc-cmdline-linux` 둘이고, 워크트리는 모두 남겼다(병합된 PR 없음, 다시 만들 수 없는 `web/apps/widget/public/`, 앱의 표지, 쥔 프로세스).

인계에서 멈췄다던 `tools/run_checks.py`를 고치기 전 판으로 다시 돌려 열여섯 게이트가 모두 초록이었다.

`/code-review origin/main`(base 92b61458, 수정 넷·미추적 셋, 커밋 0). 표준 축의 보고와 판정:

- 하드: 프로브가 이제 기다리는 `command_line`을 불러, README 의 고치기 전 수를 다시 내지 못한다. 고쳤다. 프로브는 `command_line`과 같은 부름을 읽기를 세는 함수로 감싸, 그 안의 첫 읽기를 고치기 전의 한 번 읽기로 세고 도구가 메웠는지를 함께 적는다. 다시 잰 결과: 리눅스 500회차 가운데 첫 읽기 None 8 이 모두 `도구가 메움`, 윈도 넷을 함께(`proc_cmdline_settle_four.sh`, 새로 더했다) 1200회차 가운데 None 1 이 `도구가 메움`.
- 하드: "CI 와 같은 판의 컨테이너"는 거짓이다. 프로브 독스트링과 티켓을 `python:3.12.10-slim-bookworm`, CI 와 판이 다르다로 고쳤다.
- 재지 않은 단정 둘: 티켓의 `hook_edit_during_commit` 범위 밖 문장을 코드를 읽은 어림으로, 모듈 독스트링의 기한까지 기다린 뒤 None 문장을 코드를 읽은 것이라고 고쳤다.
- `SETTLE_SECONDS` 주석의 "다시 읽은 표본의 다수"는 틈의 길이를 잰 것이 아니다. "틈의 길이는 재지 않았고"로 좁혔다.
- 해석 갈래에 양성 대조가 없고, 다른 명령 줄 0 은 갈래가 못 된다. README 를 그렇게 고쳤다.
- 남긴 것(Minor, 판단): `_read_once`·`_alive`·`pids_named`의 같은 플랫폼 분기와 예외 튜플(같은 모양이 셋이고 고치면 훅 사본 대조의 범위가 흔들린다), 실제 프로세스 시험의 기다림이 60초에서 도구의 5초로 줄어든 것(부하 걸린 CI 에서 모자랄 수 있다는 것은 어림이고, 빨개지면 `SETTLE_SECONDS`를 늘린다).

본 세션이 직접 찾아 고친 것: 윈도의 `_windows_alive`가 조회 권한만으로 열어, 읽기 권한으로는 열리지 않는 프로세스를 살아 있다고 보고 하나마다 5초를 기다렸다. 손으로 본 것(커밋하지 않은 스크래치 스크립트): 791 가운데 7이 그 상황이고 부른 셋이 모두 5.0초 뒤 None. 읽기와 같은 권한으로 열게 고친 뒤 새 프로브 `proc_cmdline_alive_gap.py`가 772 가운데 7 모두 `즉시 None`(0.00~0.01초)을 단언했다. `rerun_runner`의 `_close_dead_rounds`가 이름으로 훑은 pid 마다 읽으므로 그 지연이 거기에 닿는다.

명세 축의 보고와 판정:

- Major "CI 와 같은 판", 재지 않은 git 범위 밖 단정, "상태는 R"이 늦은 진단 읽기의 값이라는 것, `SETTLE_SECONDS` 주석: 표준 축과 겹쳐 위에서 고쳤다(독스트링은 "늦게 다시 읽은 상태는 R").
- 같은 사용자의 권한 상승된 프로세스가 5초를 기다린다는 반례(코드를 읽은 어림): 본 세션이 찾은 `_windows_alive` 고침이 덮는다.
- 시험의 빈틈 둘을 고쳤다. `command_line`이 `settled`로 감싸는 배선을 가짜 읽기로 고정하는 시험을 더했고, 끝난 자식 시험이 마지막 읽기의 걸린 시간을 `SETTLE_SECONDS / 2` 밑으로 단언하게 했다. 감쌈을 빼는 변이와 `_alive`가 늘 참인 변이를 손으로 넣어 각각 그 시험만 빨개지는 것을 보고 되돌렸다.
- 남긴 것: `tools/rerun_continue.py`도 같은 `command_line`을 받는다는 것(동작은 `_ours`와 같아 고칠 것이 없다), rerun 시험 넷의 711초가 새 기다림 탓인지 가르지 않은 것(기준선을 재지 않았다).

반영 뒤 `tools/run_checks.py`는 pyright 둘이 빨갰다(새 배선 시험의 타입 없는 lambda). 이름 있는 함수로 고쳐 pyright 를 손으로 다시 쳐 초록이었고, 나머지 다섯은 커밋의 pre-commit 으로 갈음한다. `-m llm`·e2e·사진 비교는 이 변경(`tools/`·`tests/tools/`·`.scratch/`)이 닿지 않아 치지 않았다.

커밋의 pre-commit 첫 번은 ruff 가 시험 파일의 import 를 고쳐 멈췄고, 둘째 번은 pytest 넷이 빨갰다. `tests/channel/cli/test_interrupt.py`의 둘(Ctrl+C 를 누른 자식이 30초 안에 끝나지 않았다), `test_check_ticket.py`의 `test_CI는_두_꼴의_상태_줄을_모두_읽는다[Status: in-progress]`(PR_HEAD_SHA 커밋을 찾지 못해 종료 2), `test_rerun_runner.py`의 `test_오염이_한_번이면_다시_돌고_두_번이면_그_과제를_모든_갈래에서_뺀다`. 이 PC 에 세션 여덟이 함께 돌던 때다. 홀로 다시 돌리자 뒤의 둘은 지나갔고, `test_interrupt.py`는 한 번 더 하나가 빨갰다가 셋째 번에 여섯 모두 지나갔다. `test_interrupt.py`는 이 변경이 닿지 않는다(`proc_command_line`·`rerun`을 grep 해 0). `test_rerun_runner.py`의 판은 실제 `command_line`을 쓰지만 앞의 두 전체 실행과 홀로 돈 실행에서 초록이었다. 부하 아래의 흔들림으로 보고 다시 커밋했다(어림이다).

셋째 번 pre-commit 은 `test_rerun_runner.py`의 그 시험 하나만 빨갰다. 같은 시험이 두 번 연달아 빨개 `diagnosing-bugs`로 갈랐다. 루프는 커밋하지 않은 스크래치 스크립트로, 그 시험 하나를 pytest 여덟 개로 동시에 두 바퀴 돌려 빨간 수를 센다. 이 브랜치의 `tools/proc_command_line.py`로 16 가운데 6, 그 파일만 `origin/main`의 판으로 바꿔 16 가운데 10 이 빨갰다(손으로 봤다). 그래서 이 브랜치의 기다림이 원인이 아니라 부하 아래에서 원래 흔들리는 시험이다. 빨간 실행의 출력에는 러너가 1 을 낸 까닭이 없었다. 까닭은 가르지 않았다.

회고 후보: `tests/tools/test_rerun_runner.py`의 `test_오염이_한_번이면_다시_돌고_두_번이면_그_과제를_모든_갈래에서_뺀다`가 부하 아래에서 흔들린다(동시 여덟에서 origin/main 판으로 10/16). 커밋을 막는 pre-commit 의 흔들림이라 고침(사건 하나) 후보다.

넷째 번 pre-commit 은 `test_interrupt.py`의 `test_서버를_닫기_시작한_뒤에_한_번_누르면_닫기를_마치고_중단으로_끝난다` 하나만 빨갰다(Ctrl+C 를 누른 자식이 30초 안에 끝나지 않았다). 위의 둘과 같은 시험 파일의 다른 시험이고, 이 변경이 닿지 않는다.

PR 직전 리뷰에 밀 주장(반영으로 새로 쓴 문장): 모듈 독스트링의 "두 실행에서 500회차 가운데 44회차와 8회차", "두 실행 모두 1200회차 가운데 1회차", "두 번째 실행의 빈 값 아홉(리눅스 8, 윈도 1)은 모두 그 다시 읽기가 메웠다", "윈도에서 읽기 권한으로 열지 못하는 프로세스(다른 사용자의 것 등) … 기다리지 않고 None"; `_windows_alive` 독스트링의 프로세스 이름들; README 두 행의 결과 문장과 "넷을 함께 띄운 방법은 적히지 않았다"; 티켓 Comments 의 새 두 줄.
