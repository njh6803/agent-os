# 2026-10-13 (40) origin/main보다 뒤처진 푸시를 막는 훅

## 계기

일지 2026-10-13-38(PR #223, CI 자동 대기)과 같은 세션의 이어지는 PR이다. 그 세션에서 사용자가 CI가 여러 번 도는 것을 물었고,
`.scratch/harness/probes/ci_wait/runs_per_pr.py`가 CI 실행의 갈래를 냈다(main 합치기가 실행의 약 3분의 1). 답을 듣고
사용자가 골랐다.

> 사용자: (AskUserQuestion "푸시 직전에 main보다 뒤처졌는지 알려 주는 훅(git push 때 origin/main과 비교해 '먼저 합치고 푸시하라'고 알림, 막지는 않음)을 어떻게 넣을까요?") "이 PR 병합 뒤 별도 PR (추천)"

같은 세션의 회고가 승인한 rules 문장(기다리는 도구의 외부 호출에 시간 제한)과, PR #223의 claude-review가 두 회차 짚은
`GH_TIMEOUT` 이름(git 호출도 쓴다)도 이 PR이 함께 맡았다.

## 첫 판: 커밋 뒤 알림

질문의 전제는 푸시 직전의 알림이었다. 짓다 보니 계기만 주는 PreToolUse 훅은 명령을 그대로 돌려, 알림이 푸시가 나간 뒤에야
읽힌다고 봤다(훅 실행 순서에서 끌어낸 판단이고 재지 않았다). 그래서 첫 판은 막지 않는 성격을 지키려고 PostToolUse의
`git commit` 뒤에 알렸다(`hook_commit_behind_main`). 시험, 변이 여덟, 시간 프로브, rules 카나리아(통과 4)까지 마쳤다.

## 셀프 리뷰가 첫 판을 뒤집었다

`/code-review`, base `47013fc`, 바뀐 파일 10·미추적 6·커밋 0. 표준 축은 기본 모델이었다.

- **명세 축 Major.** 이 저장소의 커밋은 pre-commit 때문에 늘 백그라운드로 돈다. PostToolUse는 도구가 돌아오는 순간, 곧
  커밋을 띄운 직후에 돌아 알림이 커밋이 도는 동안 온다. 그 말대로 바로 합치면 도는 커밋과 부딪치고, 커밋이 도는 십여 분 동안
  main이 움직인 것은 놓친다.
- **표준 축 Major.** 커밋 판정이 `git -C <경로> commit`·`git -c k=v commit`·`git --no-pager commit`을 놓쳤다. 같은 판정을
  하는 `hook_git_main_commit`은 이 셋을 잡는다(정규식과 인용 자리표시자 `_`, PR #91 리뷰). 새 훅이 `hook_pr_next_session`을
  복사한 탓이다.
- 그 밖에 Minor: KICKOFF.md의 계기·막는 훅 분류 문장, 못 보는 것의 하위 입력이 시험으로 고정되지 않은 것, 근거 없는
  "푸시가 나간 뒤에야 읽힌다", 시간 제한의 합을 잘못 센 주석, 독스트링에 복사한 프로브 수치, 시간 프로브의 회차 표지, 알림이
  안내하는 길에서 빠진 검증 명령과 `sibling_overlap.py`(충돌 없는 `git merge`에는 pre-commit이 돌지 않는다), 실제 세션 확인.

정확한 시점은 푸시하는 순간뿐이고, 그 순간에 효과를 내려면 막아야 한다. 처음 물을 때 "막지 않음"을 전제로 했으므로 다시
물었다. 같은 처지(PreToolUse 계기는 명령을 그대로 돌린다)였던 대기열 86도 구현 전에 물어 사용자가 막기를 골랐다.

> 사용자: (AskUserQuestion "푸시 전 뒤처짐 훅을 어느 방식으로 할까요? (커밋 뒤 알림은 커밋이 백그라운드로 12분 도는 동안 도착해 시점이 어긋납니다)") "푸시를 막는 훅 (추천)"

## 둘째 판: 푸시를 막는다

첫 판의 파일(훅, 시험, 변이 표, 시간 프로브, 카나리아 명세)을 걷고 `tools/hook_push_behind_main.py`를 PreToolUse
`Bash|PowerShell`(이미 `hook_git_main_commit`·`hook_pr_head_sync`가 있는 묶음)에 들였다.

- **판정.** 명령 위치의 `git push`(`hook_git_main_commit`과 같은 정규식으로 `-C`·`-c`·`--no-pager`를 잡고, 인용은
  자리표시자 `_`로 바꾼다). 지우는 푸시(`--delete`, `-d`, `:<브랜치>`)와 `PUSH_BEHIND_OK`가 든 명령은 지나간다. main 위나
  detached HEAD는 재지 않는다. fetch 뒤 뒤처졌으면 deny하고, 이유에 합치는 길(`git merge origin/main`, 검증 명령,
  `sibling_overlap.py`, 다시 푸시)과 탈출구를 적는다. git 호출마다 시간 제한(5·8·5초)이 있고 실패하면 지나간다.
- **시험을 먼저.** `tests/tools/test_hook_push_behind_main.py`를 먼저 써서 모듈이 없어 빨간 것을 본 뒤 훅을 썼다. 못 보는
  것 다섯(래퍼 뒤의 푸시와 큰따옴표 안의 치환, `cd`·`git -C`, 원격·기본 브랜치, fetch 실패·시간 초과, 판정 뒤의 main 움직임)
  가운데 앞의 넷은 시험이 하나씩 고정한다. 마지막은 판정 뒤의 일이라 시험 밖이다.
- **새 훅의 넷.** 등록, 순수 함수 시험(30), `tools/hook_payloads.toml`의 deny 하나(이 세션이 PR을 열 때 친 첫 푸시 모양)와
  침묵 하나(병합 뒤 실제로 친 원격 브랜치 지우기), `tools/run_hooks.py`(85건 어긋남 0). 러너에 자리표시자 `${BEHIND_REPO}`를
  더하고 그 모양을 `tests/tools/test_run_hooks.py`가 고정한다.

## 측정

- **변이(`.scratch/harness/probes/push_behind_hook_mutations.toml`).** 첫 판은 조각 어디서든 찾는 변이가 초록으로 살아남았다.
  데이터 쪽 시험이 모두 인용이나 heredoc 안이었다. 인용 없이 다른 명령의 인자로 든 `git push`의 시험을 더하자 빨강이었고
  대조군은 초록 그대로였다. 열하나가 빨강, 대조군 하나가 초록이다.
- **시간(`.scratch/harness/probes/push_behind_hook_time.py`).** 등록 모양으로 푸시 아님 167~177ms, 뒤처진 푸시
  375~444ms, 표지(푸시 아님은 종료 0과 빈 출력, 푸시는 deny와 훅의 문구)는 열 회차 모두 맞았다. 원격이 로컬 경로라 네트워크
  fetch는 재지 않았다. `.claude/rules/tools.md`의 훅 시간 문단에 적었다.
- **카나리아(`.scratch/harness/probes/canary/tools_rule_call_timeout_push_hook.toml`).** 통과 4. 실험군(paths 안의
  `tools/hook_env_read.py`) 세 회차가 시간 제한 항목의 `CALL_TIMEOUT`, 새 훅 이름, 그 밖의 명령의 시간 범위를 글자 그대로
  옮겼고 대조군(README.md)은 둘 다 "없음"이었다.
- **`CALL_TIMEOUT`.** `tools/wait_ci.py`의 `GH_TIMEOUT`을 바꾼 이름이다. 원문이 바뀐 변이 둘을 `--since origin/main`으로
  돌려 둘 다 빨강이었다.

## 셀프 리뷰에서 남긴 것

- 뒤처진 저장소를 짓는 코드가 시험, `run_hooks._behind_repository`, 시간 프로브에 따로 있다(Duplicated Code). 시험은 변형
  (앞선 수, 원격 이름, 기본 브랜치)이 필요하고, 프로브는 재는 도구에 기대지 않게 두었다.
- `behind_count`가 fetch로 원격 추적 ref를 옮기는 것(질의가 상태를 바꾼다)은 독스트링에 부수 효과로 적었다.
- 페이로드의 침묵 사례는 지우는 푸시 하나다. "뒤처지지 않은 푸시"는 순수 함수 시험이 0을 지나간다고 고정한다.

## PR 직전 리뷰

CodeRabbit CLI 대신 `bug-perf-review`(버그·성능)와 내장 `/security-review`(보안)를 돌렸다. 기준 `65685b28`, 범위 파일
16, 커밋 `ab5d697`과 main을 합친 `85b5947`.

- **보안.** 신뢰도 8 이상의 지적이 없었다. 페이로드의 명령 원문은 정규식 판정에만 쓰이고 git 인자는 모두 고정값이며, 이유
  문장에 끼우는 것은 뒤처진 커밋 수 하나다.
- **버그·성능.** Critical·Major 없음, 유효 6·보류 2·오탐 6. 유효한 것은 이 PR에서 고쳤다.
  - fetch가 멈추면 시간 제한이 늦게 끝난다. 출력을 붙잡은 `subprocess.run`은 kill 뒤에도 손자 프로세스가 쥔 파이프를
    기다린다. fetch만 `quiet_git`(표준 입출력을 모두 DEVNULL로)으로 돌리고, 자식 환경에 `GIT_TERMINAL_PROMPT=0`을 넣었다.
    `ext::sleep 12` 전송으로 2초 제한을 재는 시험을 더했고, 출력을 붙잡는 변이에서 그 시험이 12.80초 걸려 빨갛다.
  - deny 이유의 탈출구가 Bash 문법뿐이었다. PowerShell 형태(`$env:PUSH_BEHIND_OK='1'; git push …`)를 더했다.
  - 인용한 지우기 refspec(`":old"`)과 합친 짧은 옵션(`-fd`)을 지우는 푸시로 보지 못해 막았다. 인용 자리표시자가 머리의
    콜론을 남기고, 짧은 옵션 묶음 안의 `d`를 잡는다.
  - PowerShell 제어 블록(`if ($?) { git push }`)과 `time` 접두를 못 보는 것과, `--tags`만 올리는 푸시도 재는 것을 독스트링
    "못 보는 것"에 적었다. 앞의 둘은 지나간다고, 태그 푸시는 잰다고 시험이 고정한다.
  - `run_git`에 `encoding="utf-8", errors="replace"`를 줬다(재현하지 않은 지적이고 `wait_ci._gh`와 같은 모양이다).
- **보류.** 형제 세션의 fetch와 ref 잠금이 겹칠 수 있다는 것은 훅 쪽이 실패하면 지나가고 재현하지 않았다. KICKOFF와
  rules의 막는 훅 분류에 이 훅이 맞지 않는다는 것은 보류하지 않고 고쳤다. 예외에 "계기로는 때를 맞출 수 없어 사용자가
  막기를 고른 것"을 더했다(대기열 86의 행이 `hook_pr_head_sync`를 "사용자 결정으로 계기 대신 deny"로 적는다).
- **같은 모양의 다른 도구.** `tools/sibling_overlap.py`의 `_run`(ls-remote, fetch)과 `tools/wait_ci.py`의 `_gh`도
  `capture_output`에 시간 제한을 쓴다. 앞의 것은 출력이 필요해 버릴 수 없고, 어느 쪽도 멈춘 사건이 없고 재지 않았다.
  `.claude/rules/tools.md`의 시간 제한 항목에 이 함정과 `quiet_git`을 한 문장으로 적었다.

검사.

- 변이 18(`push_behind_hook_mutations.toml`, 원문 넷을 고치고 여섯을 더했다). 시험을 더했으므로 전체를 돌렸고 모두
  기대대로였다(대조군 초록). 그 뒤 태그 푸시 시험을 더하고 대조군만 다시 돌려 초록이었다.
- 카나리아(`tools_rule_call_timeout_push_hook.toml`)에 셋째 질문(`quiet_git`)을 더해 다시 돌렸다. 둘째 판은 대조군이
  셋 모두 "없음"이라 답하고도 설명에 훅 이름을 적어 실패로 판정됐다. 커밋하지 않은 훅 파일이 `claude -p` 세션의 git
  status에 실린 것으로 보고 훅 이름을 기대에서 뺐다. 셋째 판은 통과 4다.
