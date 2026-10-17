# 2026-10-17 (09) 훅 목록 대조 시험, 시간 단언 여유 규칙, pre-commit 러너의 검사별 시간 제한을 들인다

next-session 지시문으로 연 새 세션이다. 나란히 여는 셋 가운데 첫째라 `tidy-checkouts`를 먼저 돌고 워크트리에 들어갔다.

> 사용자: "대기열 245·332·333(훅 목록 대조 시험, 시간 단언 여유 규칙, pre-commit 러너의 검사별 시간 제한)을 chore 한 PR로
> 반영한다. 각 행의 "어디로" 칸이 원천이고, 332는 306을, 333은 192를 함께 볼지 정한다"

## 정리

주 체크아웃은 깨끗한 main이었고 `aa93cf7b`에서 `544d59ac`(origin/main)로 당겼다. 당긴 커밋은 `tidy-checkouts` 스킬 파일을
바꾸지 않았다. 판정은 지울 워크트리 마흔 남짓을 냈고, 일곱(01-contract, 01-runner, 02, 04, 05, 06, 07, 08)을 지운 뒤
03의 `remove`가 `gh pr list`의 TLS 시간 초과로 종료 3이 되어 스킬대로 남은 후보를 치지 않고 멈췄다(03 폴더는 그대로다).
`chore/ruff-try-statements`는 판정이 `remove-branch`를 냈지만 나란히 도는 337 세션의 잠긴 워크트리가 그 브랜치를
체크아웃하고 있어 치지 않았다. 남은 후보는 다음 정리가 다시 본다.

## 고친 것

세 줄 계획: (1) `tools/run_hooks.py` 독스트링과 `tools/hook_payloads.toml` 머리의 수 낱말과 자리표시자 줄을 지우고
`tests/tools/test_run_hooks.py`에 대조 시험을 둔다. (2) `.claude/rules/tests.md`에 시간 단언 항목을 더한다. (3)
`tools/run_checks.py`에 검사별 시간 제한과 프로세스 트리 끝내기를 둔다. 계약(`sdk/`, `openapi.json`, 헌법)에 닿지 않는다.

- **245.** 독스트링의 자리표시자 문단(`자리표시자 —`부터 사례의 `env` 문장 앞까지)에서 뽑은 `${…}` 집합이 `fixtures()`의
  키 집합과 같은지, 표 머리의 `# 기대:` 값이 `typing.get_args(Expectation)`과 같은지 보는 저장소 상태 시험 둘과, 각각
  위반을 잡는 시험을 하나씩 두었다. 문단 밖의 `${CLAUDE_PROJECT_DIR}`(등록 명령의 전개)는 러너가 채우는 값이 아니라
  문단으로 범위를 좁혔다. 수 낱말 `스물아홉`과 `기대는 다섯`을 지웠고, 표 머리의 자리표시자 목록 줄은 러너 독스트링을
  가리키는 한 줄로 바꿨다. 첫 시험은 수 낱말이 남은 동안 빨갰다(`자리표시자 —`가 없었다).
- **333.** 검사마다 `Check.timeout`(기본 `CHECK_TIMEOUT_SECONDS` 4,200초, 관측 최대 1,048초의 네 배 남짓)을 두고
  `Popen(start_new_session=True)`과 `communicate(timeout)`으로 기다린다. 넘기면 `kill_tree`(윈도우 `taskkill /T`, POSIX
  `killpg`)로 트리를 끝내고 남은 출력을 `_drain`으로 읽은 뒤 "N초 시간 제한을 넘겼다"로 실패시킨다. 시험은 출력 파이프를
  물려받은 손자를 띄우고 120초 자는 가짜 검사에 1초 제한을 주어, 60초 안에 돌아오고 손자의 표지 파일이 15초 안에 자라기를
  멈추는지 본다. 구현 전에는 `Check`가 `timeout`을 받지 않아 빨갰고, 구현 뒤 그 파일 열일곱이 3.07초에 초록이었다.
  `tools/mutate.py`의 `_kill_tree`를 옮겨 함께 쓰지 않고 같은 길을 `run_checks`에 두었다. 나란히 도는 337 세션이 그 파일의
  try 블록을 고칠 수 있어서다. 하나로 모으는 일은 둘이 병합된 뒤의 몫이다.
- **192는 함께 하지 않았다.** 한 검사가 실패하면 나머지를 끊을지는 333과 같은 대기 자리이고, 333이 트리를 끝내는 길을
  들여 값이 싸졌다. 그러나 끊으면 다른 실패를 한 번에 보지 못하고, xdist(ADR 0035) 뒤 pytest가 짧아져 기다리는 값도
  줄었다. 둘을 다시 재지 않고 정하지 않는다. 192 행에 그렇게 적었다.
- **332.** `.claude/rules/tests.md`에 시간 단언의 상한을 홀로 잰 시간의 넉넉한 배수로 두는 항목을 더했다. 잰 배수
  (`test_mutate`의 20초 단언이 4.56초, 10.60초, 27초)와 `PACED`의 처방, 끝나기를 거듭 견주는 `_stops_growing`을 선례로
  든다. 같은 PR에서 306의 제목을 "부하 아래에서 따로 돌리면 지나는 시간 시험이 막는다, 사례마다 고친다"로 넓히고
  2026-10-16-50(`test_open_session`의 `expand-hung`)을 넷째 회차로 더했다. 형제 `chore/filesystem-read-retry-under-load`가
  같은 306 행을 고치는 중이라 나중에 병합하는 쪽이 글자 충돌을 푼다.
- **332의 카나리아.** `.scratch/harness/probes/canary/tests_rule_timing_margin.toml`은 사전 확인을 지났고, 실제 네 회차는
  모두 측정이 아니다. 계정 주간 한도로 세션이 답하지 못했다("You've hit your weekly limit · resets Oct 19, 6am
  (Asia/Seoul)"). 그래서 332는 닫지 않고 반영 상태로 열어 두었다.

## 검사

- 변이 `.scratch/harness/probes/hook_list_and_timing_guards_mutations.toml` 여덟 모두 기대대로 빨갰다(기준선 넷 초록, 변이마다
  `expect_output` 표지가 맞았다). 길게 기다리는 변이는 211초, 자식만 끝내는 변이는 47초였다.
- `tests/tools/test_run_hooks.py` 54 passed(59.6초), `tests/tools/test_run_checks.py` 17 passed(3.07초), 바꾼 파이썬 넷의
  pyright 0 errors. 나머지 손으로 치는 검사는 커밋의 pre-commit으로 갈음한다(아직 커밋하지 않았다).
- 카나리아 사전 확인 통과. 실제 회차는 위 "332의 카나리아".

## 인계

셀프 리뷰 직전(`/code-review`를 부른 순간)에 세션 컨텍스트가 약 26.5만 토큰으로 인계 문턱을 넘어 인계 계기가 왔다.
`next-session`의 인계 줄을 따랐다. 변경은 커밋하지 않은 채 이 워크트리
(`C:\project\agent\.claude\worktrees\hook-list-check-and-timing-guards`, 브랜치 `chore/hook-list-check-and-timing-guards`)에
있다. 이 세션의 제목은 `chore/hook-list-check-and-timing-guards`였고 넘기며 `(인계함)`을 붙인다.

```
다음 작업: 기능 harness. 대기열 245·332·333을 한 PR로 반영하는 작업의 셀프 리뷰부터 병합까지
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 245·332·333(훅 목록 대조 시험, 시간 단언 여유 규칙, pre-commit 러너의 검사별 시간 제한)을 chore 한 PR로 반영한다. 각 행의 "어디로" 칸이 원천이고, 332는 306을, 333은 192를 함께 볼지 정한다
브랜치: chore/hook-list-check-and-timing-guards
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-17-09-hook-list-check-and-timing-guards.md
이어받을 상태: 인계: 셀프 리뷰 직전. 구현과 변이·카나리아 사전 확인까지 마친 변경이 커밋하지 않은 채 워크트리에 있고, 셀프 리뷰(/code-review origin/main, 명세는 대기열 245·332·333 행과 이 일지)부터 한다. 332의 카나리아 실제 회차는 계정 주간 한도로 2026-10-19 06:00(KST) 뒤에 돌린다. 이 PR이 병합된 뒤 열 차례인 일은 334(손으로 치는 전체 검사를 러너로, ADR 0035 이력 초안을 보이고 사용자에게 다시 묻는다)와 336(스크래치 측정 알림 훅, 303·307·323 묶음과 함께)이고 일지 "다음"에 옮긴다. 일지는 docs/journal/2026-10-17-09-hook-list-check-and-timing-guards.md
확인할 선행 조건: 주 체크아웃 미갱신일 수 있다: 첫 세션의 tidy-checkouts가 03 워크트리에서 gh TLS 시간 초과로 멈춰 병합된 워크트리 서른 남짓이 남았다(루트는 544d59ac로 당겼다). 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다. 형제 chore/filesystem-read-retry-under-load(아직 PR 없음)가 대기열 306·309 행과 ADR 0035 이력을 고치는 중이라 나중에 병합하는 쪽이 306 행의 글자 충돌을 푼다. 나란히 도는 337 세션이 tools/mutate.py의 try 블록을 고칠 수 있어 _kill_tree는 옮기지 않았다
이번 요청 범위: PR과 병합까지
```

open-session을 부른다 2026-10-17T11:58Z

## 이어받은 세션

> 사용자: "인계한 세션(chore/hook-list-check-and-timing-guards (인계함))을 멈추고 워크트리에 들어가 이어가라."

인계한 세션은 이미 유휴였지만 그 프로세스(pid 20984)가 살아 있어 워크트리 잠금이 남았고 `EnterWorktree`가 거부했다.
미커밋 변경을 스크래치패드에 패치와 사본으로 받아 둔 뒤 `git worktree unlock`으로 풀고 들어갔다. 시험 실행 중 이 워크트리의
`.venv`로 도는 표지 파일 쓰기 루프 넷이 남아 있었다(앞 세션의 변이 실행이 남긴 것으로 보인다. 부모 pid가 모두 사라졌다).
모두 끝냈다.

## 셀프 리뷰

`/code-review` 기준 `544d59ac`, 바뀐 파일 여덟, 커밋 0, 미추적 셋. 표준 축(sonnet·high)과 명세 축.

- 표준 축 Major 1(판단): `start_new_session=True` 뒤 POSIX의 자식은 터미널 Ctrl-C를 받지 못하는데, 러너가 Ctrl-C에 남은
  검사를 끝내는 길이 없었다. **고쳤다.** 작업 스레드는 `KeyboardInterrupt`를 받지 못하므로 주 스레드가 `Running`(잠금과 멈춤
  표지를 가진 자식 집합)으로 남은 트리를 끝내고 다시 던진다. `stop` 뒤에 띄운 자식은 받지 않아 띄운 스레드가 곧바로 끝낸다.
  처리는 `with` 안에 둔다(밖이면 `shutdown(wait=True)`가 먼저 기다린다). 시험은 손자의 표지 파일이 생긴 뒤에 끝나는 빠른 검사와
  멈춘 검사를 함께 돌리고 첫 줄을 쓰는 순간 `KeyboardInterrupt`를 던진다. 고치기 전에는 끝나지 않고 멈췄다(손자가 쥔 파이프를
  `with`가 기다렸다). 변이 하나를 더했다.
- 표준 축 Major 2(판단): 시간 제한 시험의 1초 제한이 부모와 손자 두 파이썬의 기동을 1초 안에 요구했다. **고쳤다.** 5초로 넓혔다.
- 표준 축 Minor 3: `.claude/rules/tests.md`의 "다른 세션의 부하 아래에서 27초"는 일지 2026-10-16-52와 다르다(같은 러너가 함께
  띄운 web-verify가 500초를 쓰던 때). **고쳤다.** test_mutate의 20초 단언은 그 파일에 하나뿐이라 "같은 단언"은 맞다.
- 표준 축 Minor 4: "관측 최대 1,048초"는 손으로 친 pytest 17분 42초(일지 2026-10-16-60)가 반례다. **고쳤다.** 러너 주석과 시험
  독스트링을 "pre-commit의 관측 최대"로 좁혔다.
- 표준 축 Minor 5·명세 축 Nit: 수 낱말 잔존(`tools/run_hooks.py`의 "기대가 다섯 밖"·"기대 다섯 중", 시험 이름
  `test_표의_기대는_다섯_중_하나여야_한다`). **고쳤다.** token-usage 티켓 05의 체크 상자와 명세 322행의 "수"는 병합된 티켓의 기록이라
  두었다.
- 명세 축 Minor 1: 러너 독스트링이 192를 정한 결정처럼 썼다. **고쳤다.** "지금은 나머지를 끝까지 기다린다. 곧바로 멈출지는 아직
  정하지 않았다(대기열 192)".
- 명세 축 Minor 2: 306 행의 회차 칸에 회차 밖의 서술이 붙었다(retro 규약은 회차 수와 일지 파일명만). **고쳤다.**
- 명세 축 Minor 3: 카나리아 `# 최신 결과:` 줄에 자리와 claude 판이 없었다. **고쳤다.** 실제 회차의 판은 적어 두지 않아 그렇게 적었다.
- Nit: 독스트링 재줄바꿈의 공백, `_docstring_placeholders`의 맨 `ValueError`, POSIX 길의 현재형. 앞의 둘은 고쳤고 셋째는 "Ctrl-C의
  테스트가 … CI의 Linux에서 잰다"로 다시 썼다(CI가 전체 pytest를 Linux에서 돈다).
- 남긴 것: 332 행의 "반영, 카나리아 실제 회차가 남아 열어 둔다" 표지는 새 형식이지만 열린 행으로 둔 것이 규약과 맞아 두었다.
  카나리아 머리의 한도 메시지 인용은 저장소에 원본 출력이 없어 글자 대조를 하지 못했다.

반영 뒤 검사:
- 변이 아홉 모두 기대대로 빨갰다. 첫 회차에서 5(길게 기다리기)가 변이 도구의 600초 상한에 걸렸다. 제한을 5초로 넓히자
  `check.timeout * 200`이 1,000초가 된 것이다. 그 변이를 `check.timeout + 90`으로, 5~7의 `-k`를 `손자까지_끝내고`로 좁혀
  (`손자까지`가 Ctrl-C 시험도 골랐다) 5~7만 다시 돌렸다(97.47초, 32.46초, 7.36초). 9(Ctrl-C에 끝내지 않기)는 45.72초.
  6은 일부러 손자를 남기므로 돌린 뒤 표지 파일 쓰기 루프를 끝냈다(README 행에 적었다).
- `tests/tools/test_run_checks.py` 18 passed(8.56초), `tests/tools/test_run_hooks.py` 54 passed(208.42초. 같은 때 변이가 돌았다).

PR 직전 리뷰에 밀 주장(반영하며 새로 쓴 문장):
- `.claude/rules/tests.md`: "`tests/tools/test_mutate.py`의 20초 단언은 한 프로세스에서 4.56초, xdist에서 10.60초였고(ADR 0035),
  같은 러너가 함께 띄운 web-verify가 500초를 쓰던 때 27초였다(일지 2026-10-16-52)"
- `tools/run_checks.py` 독스트링: "기다리는 도중 Ctrl-C 가 나면 남은 검사의 트리를 끝내고 다시 던진다. POSIX 에서 자식은 제
  세션을 이끌어 터미널의 Ctrl-C 를 받지 못하기 때문이다", "시간 제한과 Ctrl-C 의 테스트가 윈도우의 `taskkill /T` 길은 이 PC
  에서 재고, POSIX 의 프로세스 그룹 길은 CI 의 Linux 에서 잰다"
- `Running` 독스트링: "`stop` 뒤에 띄운 자식은 `add` 가 받지 않아, 띄운 스레드가 곧바로 끝낸다"
- 시험 독스트링: "멈춘 검사의 제한(45초)은 러너가 끝내지 않을 때도 시험이 그때 돌아와 경과의 상한(30초)으로 빨개지게 하려는 것이다"

## 커밋

- 첫 커밋은 pre-commit의 pytest 하나가 빨개 서지 않았다. `tests/adapters/test_filesystem.py`의
  `test_다른_프로세스가_교체하는_동안의_읽기가_재시도_안에서_성공한다`가 `PermissionError`로 실패했다(410.1초. 같은 때 web-verify
  442.2초). 이 변경이 닿지 않는 파일이고, 형제 `chore/filesystem-read-retry-under-load`가 고치는 부하 아래의 흔들림이다(대기열 306).
  같은 스테이지로 다시 친 커밋 `199d3b52`는 모든 검사가 통과했다(pyright 31.2초, run-hooks 70.6초, pytest 220.8초, web-verify
  244.9초). 손으로 치는 다섯은 이 pre-commit으로 갈음한다.

## 인계 (둘째)

커밋 `199d3b52` 직후 세션 컨텍스트가 약 26.3만 토큰으로 인계 문턱을 넘어 `커밋 뒤` 경계에서 인계 계기가 왔다. 이 세션의 지시문의
"이어받을 상태"는 `인계: 셀프 리뷰 직전`이라 같은 경계가 아니다. 이 세션의 제목은 `chore/hook-list-check-and-timing-guards`였고
넘기며 `(인계함)`을 붙인다. 아직 푸시하지 않았고 PR도 없다. origin/main은 `528bd257`(#289, retro 스킬과 대기열)로 움직였고
합치지 않았다. 그 커밋은 `.scratch/retro-queue.md`를 함께 고쳐 글자 충돌 후보다.

```
다음 작업: 기능 harness. 대기열 245·332·333을 한 PR로 반영하는 작업의 main 합치기·푸시·PR부터 병합까지
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: 대기열 245·332·333(훅 목록 대조 시험, 시간 단언 여유 규칙, pre-commit 러너의 검사별 시간 제한)을 chore 한 PR로 반영한다. 각 행의 "어디로" 칸이 원천이고, 332는 306을, 333은 192를 함께 볼지 정한다
브랜치: chore/hook-list-check-and-timing-guards
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-17-09-hook-list-check-and-timing-guards.md
이어받을 상태: 인계: 커밋 뒤. 셀프 리뷰를 반영한 커밋 199d3b52까지 했다(구현, 변이 아홉, 셀프 리뷰 두 축과 반영, pre-commit 모두 초록). 남은 단계는 origin/main(528bd257, .scratch/retro-queue.md 충돌 후보) 합치기, 푸시, PR 직전 리뷰(bug-perf-review 또는 coderabbit-review. 밀 주장은 일지 "셀프 리뷰"의 목록), PR, 봇 회차, 병합이다. 열린 PR은 없고 푸시하지 않았다. 332의 카나리아 실제 회차는 계정 주간 한도로 2026-10-19 06:00(KST) 뒤에 돌린다. 이 PR이 병합된 뒤 열 차례인 일은 334(손으로 치는 전체 검사를 러너로, ADR 0035 이력 초안을 보이고 사용자에게 다시 묻는다)와 336(스크래치 측정 알림 훅, 303·307·323 묶음과 함께)이고 일지 "다음"에 옮긴다. 일지는 docs/journal/2026-10-17-09-hook-list-check-and-timing-guards.md
확인할 선행 조건: 앞 세션 둘의 프로세스가 살아 있으면 워크트리 잠금이 남아 EnterWorktree가 거부한다. 그때는 일지 밖의 미커밋 변경이 없는지 보고(일지의 인계 절은 커밋하지 않고 남겼다) git worktree unlock으로 푼다(일지 "이어받은 세션"). 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다. 형제 chore/filesystem-read-retry-under-load(PR #288)가 대기열 306·309 행과 .scratch/harness/probes/README.md를 고쳐 나중에 병합하는 쪽이 306 행의 글자 충돌을 푼다. 나란히 도는 337 세션이 tools/mutate.py의 try 블록을 고칠 수 있어 _kill_tree는 옮기지 않았다
이번 요청 범위: PR과 병합까지
```

open-session을 부른다 2026-10-17T13:08Z

## 이어받은 세션 (셋째)

워크트리 잠금은 없어 `EnterWorktree`가 곧바로 들어갔다. 앱의 합치기 도구(`sync_with_base_branch`)는 이 워크트리를 앱이
만든 것이 아니라며 거부해, 일지 변경을 스크래치패드에 받아 두고 `git merge origin/main`(`528bd257`)으로 합쳤다. 글자
충돌은 없었다(`.scratch/retro-queue.md`도 자동으로 합쳐졌다). `tools/sibling_overlap.py`는 번호 겹침 없음을 냈다.

## PR 직전 리뷰

CodeRabbit CLI는 좌석이 배정되지 않아(`Seat: not assigned`) 돌지 않았다. 대체 둘을 돌렸다.

- `/security-review`: 발견 없음. 자식과 `taskkill`은 목록 인자로 띄우고 `shell=True`가 없다. Ctrl-C 길에서 거둔 pid가
  재사용되면 `killpg`가 남의 그룹에 갈 수 있다는 것은 이론적인 경쟁이라 접었다.
- `bug-perf-review`: Critical·Major 없음, Minor 1·Nit 2. 밀 주장 넷(tests.md의 수치, Ctrl-C 독스트링, `Running`의
  `stop`/`add`, 시험의 45초와 30초)은 모두 코드와 원문에 맞다고 판정했다.
  - Minor: 멈추는 중에 거절된 검사를 끝낸 뒤 `process.communicate()`에 시간 제한이 없어, 트리를 떠난 손자가 파이프를
    쥐면 러너가 Ctrl-C 뒤에 멈춘다. **고쳤다.** `_drain` 뒤 `wait`로 바꿨다. 시험
    `test_멈춘_뒤에_띄운_검사는_곧바로_끝내고_실패로_알린다`는 그 갈래가 도는지만 고정한다. 트리를 떠난 손자는 띄운 직후
    끝내는 순서라 시험으로 만들지 못했다.
  - Nit: `pool.submit` 반복이 `try` 밖이다. **고쳤다.** `try` 안으로 옮겼다.
  - Nit: `stop()`이 잠금 밖에서 `kill_tree`를 불러 pid 재사용의 이론적 창이 있다. 두었다(보안 리뷰와 같은 판정).
- `tests/tools/test_run_checks.py` 19 passed(145.53초. 홀로 8.56초였던 파일이라 다른 세션의 부하로 본다).
