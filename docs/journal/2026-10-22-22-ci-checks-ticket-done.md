# 2026-10-22 (22) CI가 PR마다 커밋 검사를 하고 가리키는 티켓이 done인지 본다 (ticket-for-every-pr 04)

## 구현 (첫 세션)

> 사용자: (next-session 지시문을 첫 메시지로 받았다) "다음 작업: .scratch/ticket-for-every-pr/issues/04-ci-checks-ticket-done.md. CI가 PR 단위로 커밋 검사를 하고 가리키는 티켓이 done인지 본다 / 다음 단계: 구현 / 어디서: 새 세션. 나란히 여는 2 중 1. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고(그 스킬이 사람에게 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 브랜치의 마지막 토막)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다 / 시작 프롬프트: /implement .scratch/ticket-for-every-pr/issues/04-ci-checks-ticket-done.md / 브랜치: feature/04-ci-checks-ticket-done / 모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래 / 읽을 것: docs/journal/2026-10-22-14-commit-check-blocks-ticketless.md의 "다음", 나란히 도는 .scratch/ticket-for-every-pr/issues/05-first-turn-ticket-notice.md(둘 다 KICKOFF.md의 다른 줄을 고친다) / 이어받을 상태: PR #350 claude-review 둘째 회차에서 보류해 이 티켓으로 넘긴 둘. tools/check_ticket.py 독스트링과 명세(.scratch/ticket-for-every-pr/spec.md)의 판정 목록이 겹치니 명세에 "원천은 독스트링" 포인터를 둔다(Minor), 출력의 `check-ticket:` 접두가 세 곳(_note, _blocked, main의 GitError)에서 따로 붙는다(Nit). 일지 "다음"의 Change.deleted 열거화와 judge 쪼개기도 판정 단계를 늘릴 때 다시 본다 / 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다 / 이번 요청 범위: PR과 병합까지"

### 시작

- 제목을 브랜치 이름으로 바꿨다.
- `tidy-checkouts`: 루트 main을 `96fbe241` → `e62eb052`(그때의 origin/main, #350)로 당겼다. 워크트리 `design-reverse-sync-tickets`를 쥔 쉬는 세션 다섯을 `end-holders`로 끝내고 그 워크트리와 브랜치 `docs/design-reverse-sync-tickets`를 지웠다. 휴지통의 `worktree-overrides-pc-check~~.venv`는 모듈을 올린 python.exe(pid 41176) 때문에 남았다. 병합된 PR이 없는 워크트리, 쥔 프로세스가 있는 워크트리, 실행 중 세션의 `03-commit-check-blocks-ticketless`, 앱 표지 둘은 남겼다.
- `EnterWorktree(04-ci-checks-ticket-done)` 뒤 `feature/04-ci-checks-ticket-done`을 땄다.

### 한 것 (커밋하지 않았다)

- 티켓 `Status:`를 in-progress로(첫 편집).
- `tools/check_ticket.py`: `--ci`로 부르면 환경 변수 `PR_HEAD_REF`·`PR_HEAD_SHA`·`PR_BASE_SHA`를 받아 PR 단위로 판정한다(`judge_pr`). 기준은 `origin/main` 대신 base 커밋, 바뀐 파일은 merge-base에서 머리 커밋의 트리까지(`tree_changes`), 판정 1은 체크아웃이 아니라 머리 브랜치 이름으로 본다. 판정 5·6으로 지나면 가리키는 티켓의 `Status:`를 머리 커밋에서 읽어(`status_of`, 줄 머리가 `Status:`나 `**Status:**`인 첫 줄의 첫 낱말) done이 아니면 막는다. 판정 전에 받은 세 값과 병합 커밋의 첫 부모를 한 줄 찍는다(`inputs_line`). push 실행은 한 줄을 찍고 0. 받은 커밋 값이 비었거나 없으면 2. 독스트링에 CI, `Status:`를 읽는 규칙, CI의 막는 글을 더하고 못 보는 것을 고쳤다(03이 비워 둔 "CI가 같은 판정을 한다"와 "훅을 건너뛴 커밋은 CI가 잡는다").
- `tests/tools/test_check_ticket.py`: CI 시험 열여덟(매개변수로 사례 스물. 티켓의 사례 전부와 입력 줄, base 커밋을 찾지 못한 2, 머리가 main인 PR, 머리 커밋에는 있지만 PR 변경에 없는 티켓의 알림)과, 쌓은 브랜치의 거짓 양성 하나(아래). 병합 커밋은 시험이 base로 분리 HEAD를 만든 뒤 `merge --no-ff`로 짓는다.
- 빨강: CI 갈래를 쓰기 전에 새 사례 19개가 빨갰다. 쓴 뒤 63개 모두 초록(쌓은 브랜치 사례를 더해 지금 64개). 첫 판부터 초록이던 것은 변이로 봤다.
- 변이 `.scratch/ticket-for-every-pr/probes/check_ticket_mutations.toml`: 03의 여덟(원문 셋을 이번 코드에 맞게 고쳤다)에 CI 여섯을 더했다. Status를 보지 않음, 줄 어디서든 첫 출현, 판정 1을 체크아웃으로, 변경을 origin/main에, 전환을 origin/main에 견줌, base 값을 풀지 않음. `PYTHONUTF8=1 uv run python tools/mutate.py …`가 `변이 14 모두 기대대로`.
- `.github/workflows/ci.yml`: 새 잡 `ticket`(체크아웃 기본, `fetch-depth: 0`, `persist-credentials: false`, PR 값은 `env`, `::stop-commands::` 뒤 `python3 tools/check_ticket.py --ci`, `timeout-minutes: 10`은 어림), `verify`의 needs에 `ticket`, 머리 주석의 잡 다섯. zizmor 지적 없음.
- 문서: `docs/constitution/operations.md` 가드레일(두 자동 검사의 차이에서 커밋 검사를 pre-commit에만 있는 검사에서 빼고, CI `ticket` 잡의 문장, `verify`의 다섯 잡), `docs/constitution/tech.md` 원격·CI 행(잡 다섯, 러너의 `python3`), 헌법 3.0.51(`docs/constitution/README.md`, 형제가 쓴 가장 높은 판 3.0.50), `CLAUDE.md` 검증 명령 절(커밋 검사를 "CI도 돌리고" 무리로 옮기고 "아직 pre-commit에서만 돈다"를 지웠다. 게이트 수는 그대로), `KICKOFF.md` ci.yml 줄, 명세의 판정 목록 아래 "원천은 독스트링" 주석(Minor).
- 잔존 grep: "잡 넷", "네 잡", "넷이 모두", "아직 pre-commit", "pre-commit에만 있고"를 저장소에서 다시 셌다. 남은 것은 일지·ADR 0021 이력의 실측 기록·헌법 README의 옛 판 문단·명세와 이 티켓의 계획 문장·이 문맥과 상관없는 "넷이 모두"였다. `tools/run_checks.py` 독스트링과 `.pre-commit-config.yaml` 러너 주석("CI 도 도는 검사")은 이번 변경과 맞는다.

### 결정

- CI 모드는 환경 변수가 있는지가 아니라 `--ci` 플래그로 가른다. push 이벤트에서 `github.head_ref`가 빈 값으로 들어오는지 없는 것으로 들어오는지에 판정이 기대지 않게 했고, 손으로 친 커밋 검사가 셸에 남은 변수로 CI 판정을 하는 길도 막는다.
- 커밋 판정과 CI 판정을 한 함수의 불리언 갈래로 두지 않고 진입점 둘(`judge`, `judge_pr`)로 나눴다. 막는 글에서 둘이 달리 쓰는 말은 값 `Wording`(`COMMIT_WORDING`, `PR_WORDING`)이다(`CODING_STANDARDS.md`의 불리언 플래그 인자와 갈래를 고르는 불리언 칸). 03 claude-review가 보류한 "judge 쪼개기"는 이것으로 다시 봤다. 두 진입점이 공통 도우미(`before_convention`, `merge_base`, `_outside`, `_present`, `pointed`, `_blocked`)를 나눠 쓴다.
- `Change.deleted`는 열거로 바꾸지 않았다. 갈래를 고르는 칸이 아니라 git이 준 사실(지운 파일인가)을 담는 칸이고, 03 회고 2가 같은 판단을 적었다.
- 출력 접두 `check-ticket: `는 `_write` 한 곳에서 붙인다(Nit). 판정은 접두 없는 글을 돌려준다.
- CI의 알림 티켓(가리키는데 PR 변경에 들지 않은 것)은 디스크가 아니라 머리 커밋의 트리(`ls-tree`)에서 찾는다. CI의 작업 트리는 병합 커밋이라 머리 커밋과 다를 수 있다.
- 잡은 uv 없이 러너의 `python3`(ubuntu-latest의 3.12)으로 돈다. 도구가 표준 라이브러리만 쓴다.
- 출력에 PR이 고른 브랜치·파일 이름이 실리므로 그동안 워크플로 명령을 `::stop-commands::<무작위>`로 멈춘다. `uuidgen`이 러너에 있는지는 실제 실행에서 본다.

### 도중의 일

- 다른 브랜치를 base로 둔 CI 사례를 쓰다가, 시험의 클론에 건 커밋 검사 심이 그 브랜치 위의 docs 커밋을 막았다. 커밋 검사는 `origin/main`에 견줘 base 브랜치의 변경까지 세기 때문이다. CI 사례의 그 커밋은 `--no-verify` 도우미(`_훅을_건너뛰고_커밋한다`)로 치고, 이 거짓 양성을 독스트링의 못 보는 것에 적어 막는다고 단언하는 시험 하나로 고정했다(`.claude/rules/tools.md`의 못 보는 것 항목).
- 본문의 `Status:` 사례는 처음에 본문이 `` `Status:` done``처럼 코드 스팬을 들어, 줄 어디서든 첫 출현을 읽는 변이에서도 첫 낱말이 `` ` ``라 막혀 빨강을 내지 못했다. 본문을 기능을 닫는 판정의 문장 꼴("Status: done 이다")로 바꾸자 변이가 빨갰다.
- base 커밋을 찾지 못하는 시험은 구현 전에도 2로 끝나 초록이었다. stderr에 `PR_BASE_SHA`가 드는지까지 단언하고, 값을 풀지 않는 변이로 빨강을 봤다.
- 실수로 주 체크아웃 경로의 `ci.yml`을 고치는 Edit를 보냈고 앱이 워크트리 격리로 막았다. 바뀐 것은 없다.
- 이 브랜치를 딴 뒤 origin/main이 `c47bedce`(#351, model-rerun 명세)로 움직였다. 이 브랜치가 고치는 파일과 겹치지 않는다.
- 검증: `uv run ruff check .` 0, `uv run ruff format --check .`은 시험 한 곳의 문자열 이음을 고친 뒤 0, `uv run python tools/run_checks.py` 열 검사 모두 Passed(pytest 474.6초, web-verify 328.0초). 쌓은 브랜치 시험은 그 뒤에 더해 그 시험과 CI 짝만 따로 돌렸다(2 passed).
- 워크트리 가드가 한글 `-k` 인자를 든 `uv run pytest`를 따옴표가 없어도 거부했고, 스크래치 스크립트를 `sh`로 부르는 명령도 리다이렉트와 `echo exit=$?`를 붙이자 거부했다. 리다이렉트 없는 `sh <스크립트>` 한 줄은 지났다.

### 인계 (셀프 리뷰 직전)

`code-review`를 부른 직후 인계 계기가 왔다(세션 컨텍스트 263,536 토큰, 경계 `셀프 리뷰 직전`). 인계하지 않는 때 다섯에 들지 않았다(곁 세션 아님: `get_session`의 `self`에 `parentSessionId`가 없다). 셀프 리뷰는 밟지 않았다. 이 세션의 지금 제목은 `feature/04-ci-checks-ticket-done`이고 넘기기 전에 `(인계함)`을 붙인다. 커밋은 아직 없다.

지시문:

```
다음 작업: .scratch/ticket-for-every-pr/issues/04-ci-checks-ticket-done.md. CI가 PR 단위로 커밋 검사를 하고 가리키는 티켓이 done인지 본다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/ticket-for-every-pr/issues/04-ci-checks-ticket-done.md
브랜치: feature/04-ci-checks-ticket-done
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-22-22-ci-checks-ticket-done.md의 "구현 (첫 세션)" 절
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review)부터 한다. 일지 docs/journal/2026-10-22-22-ci-checks-ticket-done.md
확인할 선행 조건: 러너에 uuidgen이 있는지와 ticket 잡의 timeout-minutes 10(어림)은 첫 CI 실행에서 본다
이번 요청 범위: PR과 병합까지
```

제목을 `feature/04-ci-checks-ticket-done (인계함)`으로 바꿨고, 멈출 백그라운드 작업은 없었으며, `git worktree unlock`은 출력 없이 끝났다.

open-session을 부른다 2026-10-22T12:41:16Z

## 구현 (둘째 세션)

> 사용자: (open-session이 연 새 세션의 첫 메시지로 위 인계 지시문을 받았다) "다음 작업: .scratch/ticket-for-every-pr/issues/04-ci-checks-ticket-done.md. CI가 PR 단위로 커밋 검사를 하고 가리키는 티켓이 done인지 본다 / 다음 단계: 구현 / 어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다 / … / 이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review)부터 한다 / 확인할 선행 조건: 러너에 uuidgen이 있는지와 ticket 잡의 timeout-minutes 10(어림)은 첫 CI 실행에서 본다 / 이번 요청 범위: PR과 병합까지"

### 시작

- 제목을 브랜치 이름으로 바꾸고 `EnterWorktree(path=.claude/worktrees/04-ci-checks-ticket-done)`로 들어갔다. 커밋하지 않은 변경 11개와 이 일지가 그대로 있었다.

### 셀프 리뷰

- 범위: base `e62eb052`, 바뀐 파일 11개, 커밋 0개, 미추적 1개(이 일지). 표준 축(sonnet·high)과 명세 축을 나란히 띄웠다.
- 명세 축 보고(요지). (1) Major: `.scratch/harness/probes/ci_job_durations.py`의 `JOBS`와 독스트링, 프로브 README 행이 잡 다섯(python, web, e2e, visual, verify)이라 `ticket`을 재지 못한다. 넣으면 옛 실행이 모두 측정 아님이 되어 1로 끝난다. (2) Minor: `tech.md`와 헌법 README 3.0.51의 "uv 없이 러너의 `python3`으로 돈다(ADR 0037)"는 티켓이 요구하지 않았고 ADR 0037에 그 결정이 없다. (3) Minor: 독스트링의 "티켓 열한 장"이 지금은 맞지 않다(판정 문장에 다시 드는 것 12장, 줄 머리가 아닌 자리에 한 번 더 드는 것 19장). (4) Minor: 계획한 두 시도(첫 실행과 `rerun --failed`)는 같은 페이로드라 base 값과 병합 커밋 첫 부모가 갈리는 상황을 만들지 못한다. 임시 저장소에서 base 값을 첫 부모보다 오래된 커밋으로 주고 main을 합친 docs PR을 치면 잘못 막혔다. (5) Nit: 러너에 `uuidgen`이 없으면 `bash -e`에서도 빈 토큰으로 이어진다(손으로 재현, 종료 0). (6) Nit: 모르는 인자를 주면 argparse가 접두 없이 2로 끝나 "모든 출력의 첫 줄", "2는 git 실패"의 반례다. (7) Nit: 코드 블록 안 줄 머리의 `Status:`도 읽는다. (8) Nit: 쌓은 PR의 base 브랜치를 squash 병합해 PR의 base가 main으로 바뀐 뒤 rebase 없이 푸시하면 base 브랜치의 파일로 막히고, 막는 글의 할 일(티켓 쓰기, 이름 바꾸기)이 맞는 길(`rebase --onto`)과 다르다. (9) Nit: 이미 done인 티켓의 브랜치를 다시 쓴 PR에서 CI 알림 "done으로 고쳐 커밋"은 고칠 것이 없다. (10) Nit: 이 티켓만은 in-progress로 draft PR을 여는데 인계 지시문의 "이어받을 상태"에 그 예외가 없다.
- 표준 축 보고(요지). Critical·Major 없음. 시험 64개 통과, 변이 14, zizmor 지적 없음, 게이트 수("여덟", "열다섯", 잡 다섯)와 못 보는 것 새 항목 셋의 시험은 맞았다. Minor: (1) "티켓 열한 장"이 지금 19장이다. (2) 쌓은 PR의 base 브랜치를 squash 병합해 base가 main으로 바뀌면 base 브랜치의 파일로 막히고 막는 글이 엉뚱한 길로 보낸다(스크래치 `retarget.py`로 재현). 못 보는 것과 시험이 없다. `pull_request` 기본 types라 base 바꾸기만으로는 다시 돌지 않는다. (3) `.scratch/ticket-for-every-pr/probes/README.md`의 변이 행이 "변이 여덟"으로 낡았다(지금 14). (4) `echo "::stop-commands::$(uuidgen)"`는 `uuidgen`이 없어도 빈 토큰으로 지난다. (5) `ci.yml` 머리 주석의 "최근 성공 실행 최대의 네 배 이상"과 달리 `ticket`의 10분은 어림인데 그렇게 적지 않았다. (6) 까닭을 보지 않는 막힘 시험 둘(`rebase한_규약_전_머리`, `전환에_base_브랜치`)과 `_not_done`의 "값이 비었다" 갈래의 시험이 없다. 막는 글의 갈래: base에서 이미 done인 티켓은 "done으로 고쳐 커밋"으로 풀리지 않는다. Nit: 포크에 훅이 없다는 말("포크 사용자가 그 훅을 쓰지 않는다"가 정확), argparse의 종료 2와 접두 없는 출력, `ci.yml`이 문서 이름만 들고 웹 요약임을 밝히지 않음과 재개 없는 "그동안", 머리 주석의 줄바꿈, 시험 도우미 `_pr`·`_ci`·`Pr`이 영문(`.claude/rules/tools.md`), 변이 표지 "CI 가 막아야 한다"가 함수 소스에도 실림. 스멜(판단): `judge`·`judge_pr`과 `tickets_on_disk`·`tickets_in_tree`의 중복(일지의 결정), "PR 을 막았다" 리터럴이 `PR_WORDING`과 `_statuses`에 따로 있음, Data Clumps, `pointed`·`_received`·`BASE`와 `base`의 이름, `judge_ci`의 Middle Man. 실제 실행으로만 닫히는 것: `base.sha`가 병합 커밋의 첫 부모와 같은지.
- 고친 것.
  - 명세 1(Major): `ci_job_durations.py`의 `JOBS`에 `ticket`을 넣고 독스트링·출력을 잡 여섯으로, 둘째 인자 `[브랜치]`를 더해 `gh run list --branch`로 그 잡이 든 실행만 받게 했다. PR의 실행이 머리 브랜치로 걸리는 것은 PR #350의 머리 브랜치로 쳐서 `pull_request` 실행 둘이 나온 것을 손으로 봤다. 하네스 프로브 README 행도 고쳤다.
  - 명세 2: `tech.md`와 헌법 README 3.0.51에서 "uv 없이 러너의 `python3`" 문장(ADR 0037에 근거 없음)을 뺐다. 그 사실은 `ci.yml` 주석에 남는다.
  - 두 축의 "열한 장": 수를 빼고 "상태 줄보다 앞에 드는 티켓도 있다(이 기능의 04)"로 바꿨다.
  - 표준 4·명세 5(`uuidgen`): `marker=$(uuidgen)` 대입으로 받아 없으면 그 자리에서 실패하게 했다(`bash -e`에서 대입 꼴은 127, echo 인자 꼴은 0으로 이어지는 것을 손으로 봤다). `ci.yml` 주석의 GitHub 문서 인용은 본문(`docs.github.com/api/article/body?pathname=…/workflow-commands`)을 내려받아 대 봤고 URL과 함께 적었다. 문서 예시도 `ubuntu-latest`에서 `stopMarker=$(uuidgen)`이다. 재개 없는 "그동안"을 "이 스텝 끝까지 다시 켜지 않는다"로 고쳤다.
  - 표준 5: `ci.yml` 머리 주석과 `ticket` 잡 주석에 새 잡의 첫 값이 어림이라고 적었다. 머리 주석의 어색한 줄바꿈도 고쳤다.
  - 표준 2·명세 8(쌓은 PR의 base가 main으로 바뀐 뒤): 독스트링 못 보는 것에 거짓 양성과 길(`git rebase --onto origin/main <옛 base 브랜치>`), base 바꾸기만으로는 CI가 다시 돌지 않는다는 것을 적고, 막힘과 안내한 길로 지나는 것을 시험 하나로 고정했다.
  - 표준·명세의 이미 done인 티켓: CI 알림에 "이미 done 이면 앞서 닫힌 티켓이니 아래 할 일대로 이 PR 의 티켓을 새로 쓴다"를 더하고 독스트링 막는 글 절과 시험 단언을 맞췄다.
  - 표준 6: 까닭을 보지 않던 막힘 시험 둘에 파일 단언(`tools/c.py`가 들고 `tools/b.py`가 없다, `tools/b.py`가 든다)을, `_not_done`의 값이 빈 갈래에 시험을 더했다.
  - 명세 6·표준 Nit(argparse): "모든 출력의 첫 줄"을 "판정과 git 실패의 출력"으로 좁히고 종료 코드 2에 argparse를 더했다. 시험 하나로 고정했다.
  - 표준 Nit: 포크의 훅 문장을 "Claude 세션 훅이라 포크의 main 에서 친 커밋이 그 훅을 거쳤다고 볼 수 없다"로(`.claude/settings.json`의 PreToolUse 등록을 확인했다). 시험 도우미 `Pr`·`_pr`·`_ci`를 `PR값`·`_PR_병합_커밋`·`_CI로_친다`로(`.claude/rules/tools.md`). `_statuses`의 "PR 을 막았다"는 `PR_WORDING.blocked`를 쓴다.
  - 표준 Nit(변이 표지): 단언이 둘인 도우미를 겨누는 표지 일곱을 `AssertionError: ` 줄로 바꿨다. 둘째 단언이 실패한 출력의 함수 소스에도 첫 단언 문구가 실리고 `AssertionError: CI 가 막아야 한다` 줄은 없는 것을 스크래치 시험으로 봤다. 변이 README 행을 티켓 04의 여섯까지 고쳤다.
- 남긴 것.
  - 명세 4(base 값 질문이 두 시도로는 갈리지 않음): 티켓이 이미 "물을 것은 그 값이 명세가 가정한 base인지다"로 적었다. 실제 실행에서 찍힌 base 값과 첫 부모를 견주고, PR을 연 뒤 main이 움직였다면 다음 푸시의 실행에서도 견준다. 다르면 티켓대로 사람에게 묻는다.
  - 명세 7(코드 블록 안의 줄 머리 `Status:`): 독스트링의 규칙이 "줄 머리가 … 인 첫 줄"이라 서술과 동작이 같다. 티켓의 상태 줄은 9~21번째 줄로 코드 블록보다 앞이다(명세의 셈). 회고 후보로 넘기지 않는다.
  - 명세 10(인계 지시문의 예외): 코드 몫이 아니다. 이 세션이 다시 인계하면 "이 티켓만은 in-progress로 draft PR을 연다"를 이어받을 상태에 적는다.
  - 표준 스멜(`judge`·`judge_pr` 중복, Data Clumps, `pointed`·`_received`·`BASE` 이름, `judge_ci`): 판단 항목이다. 둘로 나눈 진입점은 첫 세션의 결정(불리언 갈래를 두지 않는다)이고, `judge_ci`는 `--ci`에서 PR이 아닌 실행을 가르는 자리라 두었다.
- 다시 돌린 명령. `uv run pytest -q -n 4 tests/tools/test_check_ticket.py` 67 passed(새로 셋: 값이 빈 상태 줄, argparse, 쌓은 PR의 base가 main으로 바뀐 사례). 구현 뒤에 쓴 단언의 빨강을 보려고 변이 둘을 더했다(쌓은 브랜치 전환 사례에서 바뀐 파일을 origin/main에 견줌, 값이 빈 상태 줄을 따로 알리지 않음). `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/ticket-for-every-pr/probes/check_ticket_mutations.toml`이 `변이 16 모두 기대대로`(커밋 전이라 도구가 전체 실행은 커밋 뒤에 한 번 돌라고 알렸다. PR 직전 리뷰를 반영한 뒤 다시 돈다). `uv run ruff check .` 0, `uv run ruff format --check .` 0. 나머지 손으로 치는 셋(pyright, lint-imports, run_checks의 pytest·web)은 커밋의 pre-commit으로 갈음했다.
- PR 직전 리뷰(`bug-perf-review` 등)에 밀 주장. 반영하며 새로 쓴 사실 문장이다.
  - `ci.yml` `ticket` 잡 주석: "bash -e 에서 echo 의 인자 안의 명령 치환은 실패해도 이어진다", "2026-10-22 에 그 본문을 내려받아 대 봤다. 토큰은 실행마다 무작위로 고유해야 하고, 문서의 ubuntu-latest 예시가 토큰을 uuidgen 으로 짓는다", "timeout-minutes 는 지난 실행이 없을 때 정한 어림이다(머리 주석)".
  - `ci.yml` 머리 주석: "지난 실행이 없는 새 잡의 첫 값은 어림이고, 그 잡이 든 실행으로 프로브를 다시 돌려 고친다."
  - `ci_job_durations.py` 독스트링: "PR 의 실행은 머리 브랜치로 걸린다. 2026-10-22 에 PR #350 의 머리 브랜치를 주어 그 PR 의 `pull_request` 실행 둘이 나온 것을 손으로 봤다".
  - `check_ticket.py` 독스트링: "그 자리가 상태 줄보다 앞인 티켓도 있다(`.scratch/ticket-for-every-pr/issues/` 의 04)", "인자를 잘못 주면 argparse 가 사용법을 그 접두 없이 찍는다", "인자를 잘못 준 것도 argparse 가 2 로 끝낸다", "main 위 커밋을 막는 훅(`tools/hook_git_main_commit.py`)은 이 저장소의 Claude 세션 훅이라, 포크의 main 에서 친 커밋이 그 훅을 거쳤다고 볼 수 없다", "base 브랜치가 squash 로 병합되어 PR 의 base 가 main 으로 바뀐 뒤에는 … CI 도 그 변경을 이 PR 의 것으로 세어 막는다", "`git rebase --onto origin/main <옛 base 브랜치>` 로 이 브랜치의 커밋만 옮겨 푸시하면 지난다", "base 만 바꾸는 것은 워크플로의 `pull_request` 기본 계기(opened, synchronize, reopened)가 아니라서 CI 가 다시 돌지 않고, 다음 푸시에서 돈다"(GitHub 문서 events-that-trigger-workflows 본문을 내려받아 그 문장을 대 봤다), 막는 글 절의 "이미 done 이면 앞서 닫힌 티켓이라 이 PR 의 티켓을 새로 쓰라고 한다".
  - `check_ticket_mutations.toml` 머리 주석: "단언이 둘인 `_막혔다`·`_CI가_막았다` 는 둘째 단언이 실패해도 pytest 가 보이는 함수 소스에 첫 단언의 문구가 실리므로"(스크래치 시험으로 봤다).

### 커밋

- `f7e30606 feat: CI 가 PR 마다 커밋 검사를 하고 가리키는 티켓이 done 인지 본다`. 티켓 `Status:`는 in-progress 그대로다(이 티켓만은 in-progress로 draft PR을 열어 빨강을 먼저 본다). pre-commit 러너의 검사 모두 Passed(pytest 287.2초, web-verify 231.0초), 카나리아 명세 모양은 대상 파일이 없어 Skipped, 커밋 메시지 Passed.

### 인계 (커밋 뒤)

커밋 직후 인계 계기가 왔다(세션 컨텍스트 319,030 토큰, 경계 `커밋 뒤`). 인계하지 않는 때 다섯에 들지 않았다: 커밋은 성공했고, 요청 범위는 병합까지이며, 이어받은 경계는 `셀프 리뷰 직전`이라 다르고, `인계 못함` 줄이 없고, `get_session`의 `self`에 `parentSessionId`가 없다. 이 세션의 지금 제목은 `feature/04-ci-checks-ticket-done`이고 넘기기 전에 `(인계함)`을 붙인다. 열린 PR은 없다(아직 푸시하지 않았다).

지시문:

```
다음 작업: .scratch/ticket-for-every-pr/issues/04-ci-checks-ticket-done.md. CI가 PR 단위로 커밋 검사를 하고 가리키는 티켓이 done인지 본다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/ticket-for-every-pr/issues/04-ci-checks-ticket-done.md
브랜치: feature/04-ci-checks-ticket-done
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-22-22-ci-checks-ticket-done.md의 "구현 (첫 세션)"과 "구현 (둘째 세션)" 절
이어받을 상태: 인계: 커밋 뒤. 셀프 리뷰를 반영한 커밋 f7e30606까지 했고 아직 푸시하지 않았다(열린 PR 없음). 남은 단계는 차례로 origin/main을 합치기, PR 직전 리뷰(CLI가 돌지 못하면 /security-review와 bug-perf-review를 나란히, 밀 주장은 일지의 "PR 직전 리뷰에 밀 주장" 목록)와 반영, 반영을 커밋한 뒤 변이 전체 실행 한 번, 티켓의 Status를 in-progress로 둔 채 draft PR을 열어 ticket 잡과 verify의 빨강 보기, gh run rerun --failed, 잡이 찍은 base 값과 병합 커밋의 첫 부모 견주기, done으로 바꿔 푸시해 초록 보기, ci_job_durations.py에 브랜치를 주어 timeout-minutes 고치기, ready와 봇 회차, 병합. 이 티켓만은 PR을 열기 전에 done으로 바꾸지 않는다(티켓의 검증 절). 일지 docs/journal/2026-10-22-22-ci-checks-ticket-done.md
확인할 선행 조건: 러너에 uuidgen이 있는지(없으면 스텝이 127로 실패한다), ticket 잡의 timeout-minutes 10(어림), 잡이 찍은 base 커밋 값이 병합 커밋의 첫 부모와 같은지(PR을 연 뒤 main이 움직였으면 다음 푸시의 실행에서도 견주고, 다르면 티켓대로 사람에게 묻는다)는 CI 실행에서 본다
이번 요청 범위: PR과 병합까지
```

제목을 `feature/04-ci-checks-ticket-done (인계함)`으로 바꿨고, 멈출 백그라운드 작업은 없었으며, 잠금 풀기는 `is not locked`로 끝났다(EnterWorktree(path)로 들어온 자리라 이 세션이 잠그지 않았다).

open-session을 부른다 2026-10-22T13:37:08Z

## 구현 (셋째 세션)

> 사용자: (open-session이 연 새 세션의 첫 메시지로 위 인계 지시문을 받았다) "다음 작업: .scratch/ticket-for-every-pr/issues/04-ci-checks-ticket-done.md. CI가 PR 단위로 커밋 검사를 하고 가리키는 티켓이 done인지 본다 / 다음 단계: 구현 / 어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다 / … / 이어받을 상태: 인계: 커밋 뒤. 셀프 리뷰를 반영한 커밋 f7e30606까지 했고 아직 푸시하지 않았다(열린 PR 없음). 남은 단계는 차례로 origin/main을 합치기, PR 직전 리뷰 …, 병합. 이 티켓만은 PR을 열기 전에 done으로 바꾸지 않는다(티켓의 검증 절) / 확인할 선행 조건: 러너에 uuidgen이 있는지 …, 잡이 찍은 base 커밋 값이 병합 커밋의 첫 부모와 같은지 …는 CI 실행에서 본다 / 이번 요청 범위: PR과 병합까지"

### 시작

- 제목을 브랜치 이름으로 바꾸고 `EnterWorktree(path=.claude/worktrees/04-ci-checks-ticket-done)`로 들어갔다. HEAD는 `f7e30606`이고 커밋하지 않은 것은 이 일지뿐이었다.
- origin/main(`b104f8fa`, #351·#352)을 합쳤다. 겹친 파일 `KICKOFF.md`와 `.scratch/harness/probes/README.md`는 자동으로 합쳐졌다. main에 일지 `2026-10-22-21`이 들어와 `tools/sibling_overlap.py`가 이 일지를 `-22`로 옮기라고 해 `--move`로 옮겼다. 옛 번호의 잔존은 grep으로 0이다.

### PR 직전 리뷰

- CodeRabbit CLI는 `coderabbit auth status`가 `Seat: not assigned`라 돌지 못해, 대체 둘을 나란히 돌렸다(합친 뒤 base `b104f8fa`).
- `/security-review`: 지적 없음. PR 값은 `env`로만 넘어가고, 계기는 `pull_request`뿐이며 권한은 `contents: read`다. git 호출은 리스트 꼴이고, 브랜치 이름은 git 인자로 쓰이지 않는다. 잡은 병합 커밋의 도구를 돌리므로 PR 작성자가 이미 쥔 것 밖을 얻는 길이 없다.
- `bug-perf-review`: 유효 Minor 넷, 보류 하나, 오탐 일곱. 근거를 코드에서 확인한 뒤 넷을 모두 고쳤다.
  - 얕은 체크아웃: CI에서 merge-base를 못 찾으면 커밋 검사처럼 알리고 0으로 지나 모든 PR이 판정 없이 초록이 된다. `judge_pr`이 merge-base를 전환보다 먼저 구하고 못 찾으면 git 실패(2)로 끝나게 했다. 시험은 병합 커밋을 `--depth 2`로 받은 체크아웃이다.
  - PR 실행의 빈 `PR_HEAD_REF`: 워크플로의 env 이름이 어긋나면 PR이 push처럼 지난다. 러너의 `GITHUB_EVENT_NAME`이 `pull_request`인데 비면 2로 끝나게 했다(GitHub 문서 Variables reference의 그 행을 본문으로 내려받아 대 봤다). 시험 도우미 `_CI로_친다`는 이벤트 이름을 직접 정한다. CI의 python 잡이 PR 실행에서 돌면 그 값을 물려받아 push 사례가 빨개지기 때문이다.
  - 두 시험은 고치기 전에 빨간 것을 봤다(얕은 체크아웃은 "얕은 클론이라 … 지난다"로 0). 변이 표는 `--check`로 원문 16이 그대로 맞는다.
  - 독스트링의 "base 에 없는 머리의 커밋 가운데 가장 오래된 것"을 위 전환의 정의(부모가 모두 base 쪽인 것)로 고쳤다.
  - `rebase --onto` 뒤 "푸시하면 지난다"에 강제 푸시(`--force-with-lease`)와 옛 base 브랜치를 지웠을 때 끝 커밋을 주는 것을 더했다.
  - 보류(base 값이 병합 커밋의 첫 부모보다 오래됐을 수 있다)는 계획대로 실제 실행의 "CI 입력" 줄로 본다.
- 다시 돌린 것: `tests/tools/test_check_ticket.py` 69 passed, pyright 0, 두 파일의 ruff 0.
