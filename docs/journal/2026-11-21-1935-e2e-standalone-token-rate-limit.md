# 단독 배포 e2e의 질문 길 실패 원인 조사 티켓 (harness e2e-standalone-token-rate-limit)

2026-11-21. 티켓: `.scratch/harness/issues/e2e-standalone-token-rate-limit.md`. 브랜치 `chore/e2e-standalone-token-rate-limit`. 앞 일지: `2026-11-21-1346-e2e-standalone-failure-artifact.md`.

## 왜

PR #617(실패 기록을 CI 산출물로 올리는 스텝)이 dev에 병합된 뒤 출시 PR #616의 머리가 `038c81bc6`으로 바뀌어 `e2e-standalone`이 다시 돌았고(실행 44878690764) 또 빨갰다. `verify`는 그 결과를 모으는 잡이라 함께 빨갰다. 새 스텝이 처음으로 산출물 `e2e-standalone-test-results`를 올렸다.

> 사용자: 티켓 쓰기

## 산출물에서 읽은 것

아래는 모두 `gh run download`로 받은 산출물의 `compose.log`와 `error-context.md`를 손으로 읽은 것이다. 원인은 어림이고 확정하지 못했다.

- 실패한 시험은 질문 길의 시험이고 화면에는 "요청을 처리하지 못했습니다"가 떴다.
- `serve`·`postgres`·`migrate`는 정상이고 `serve`는 질문 요청을 받지 못했다.
- 프록시에 `POST /portal/sites/preview/token`이 약 90ms에 60번 들어왔다. 11개는 401(고지 확인 전의 설계된 응답), 49개는 429다. 200은 없다. 11은 `site.conf`의 `burst=10`에 처음 한 건을 더한 수와 맞는다.
- 비밀값은 로그에 없었다(토큰·비밀번호·쿠키·데이터베이스 주소를 찾았으나 없었다).
- 이 PC에서는 14개가 모두 통과한다.

## 모르는 것

- 60번을 보낸 되풀이의 자리. 포털의 토큰 함수(`web/apps/portal/browser/portal.ts`)와 위젯의 토큰 받기(`web/apps/widget/components/pages/drivers.ts`의 `authorize`)가 후보이나 읽어서 확정하지 못했다.
- 확인 쿠키가 생기기 전에 토큰을 부른 까닭.
- `compose.log`가 질문을 보낸 순간의 기록을 담았는지.

## 한 일

원인을 가르고 고치는 harness 티켓을 썼다. 코드는 건드리지 않았다.

## 회고

후보 셋: 승인 1(이미 열린 항목의 회차 더하기), 기각 2, 넘김 0. 사용자에게 넘긴 것은 없다. 만료할 항목도 없다(`tools/queue_open_rows.py`의 "만료할 항목"이 없음).

- **PR #617 반영 중 pre-commit이 메모리 부족으로 죽었다: 승인, 열린 항목에 6회차.** 사건: 같은 PC에서 다른 세션의 검증이 겹친 때 `web-verify`의 vitest 일꾼이 `Fatal process out of memory: Zone`으로 죽었고 일지 커밋이 두 번 막혔다. 단독으로 돌리면 통과했다(앞 세션에서 손으로 봤다). 층과 처방은 열린 `run-checks-out-of-memory-with-parallel-sessions`가 이미 정했다. 항목의 승인 줄에 회차만 더했다(5회차에서 6회차).
- **같은 반영 중 시간 제한이 짧은 `test_probe_kit.py`의 한 시험이 부하에서 한 번 빨갰다: 기각.** 부하에서만 빨간 시간 시험이라는 종류이고 단독으로 다시 돌리면 지나갔다. 이 세션은 그 종류의 앞선 사례를 찾아보지 않았고 사건은 하나이며 새 처방이 서지 않아 일지에만 남긴다.
- **커밋 제목이 72자를 넘어 commit-msg 훅이 막았다: 기각.** 훅이 그 자리에서 막았고 한 번 고쳐 다시 지나갔다. 이미 있는 검사가 잡은 것이다.

## 다음

- 이 티켓을 구현한다(`/implement .scratch/harness/issues/e2e-standalone-token-rate-limit.md`). 순서는 가르기, 고치기, 회귀 시험이다.
- 이 티켓이 dev에 병합되면 출시 PR #616의 머리가 바뀌어 `e2e-standalone`과 `verify`가 다시 돈다. `uv run python tools/wait_ci.py 616 --head <git rev-parse origin/dev> --expect verify`로 기다린다. 초록이면 `gh pr merge 616 --merge --match-head-commit <headRefOid>`로 병합하고 `merge.md` "출시 PR"의 병합 뒤 일을 한다. 빨가면 새 산출물을 읽는다.
- #616은 병합하지 않았다.
- 이전 일지의 알림 셋은 사용자에게 전했다: 이전 세션이 `inspect.py`를 `inspect.py.stray-shadows-stdlib`로 이름을 바꾼 것, 주 체크아웃이 #617 병합 뒤 다시 한 커밋 뒤처진 것, 일지 `2026-11-20-1918-serve-requires-database`의 "다음" 후속 다섯을 시작하지 않은 것.

## 인계 (PR 연 뒤)

PR #619(머리 `62ac38ee6`, base dev)를 열었고 봇 회차와 병합은 새 세션이 한다. 이 세션은 컨텍스트가 인계 문턱을 넘어 넘긴다. 앞서 사용자가 "PR 열고 병합"이라 요청했다.

> 사용자: PR 열고 병합

open-session을 부른다 2026-11-21T12:22Z

## PR #619 처리 (새 세션)

새 세션이 PR #619를 이어받아 CI를 읽었다. `ticket` 검사만 빨갰다. CI 로그(`gh api repos/njh6803/agent-os/actions/jobs/136844226612/logs`)는 `브랜치 docs/e2e-standalone-token-rate-limit 가 가리키는 티켓이 done 이 아니라 PR 을 막았다`고 찍었다. 티켓의 `Status:`는 `ready-for-agent`다.

원인은 PR 본문이 "면제 모양의 `docs/` 브랜치라 통과했다"고 쓴 것이 틀렸기 때문이다. `tools/check_ticket.py`의 독스트링에 따르면 `.scratch/harness/issues/*.md`는 면제 모양이 아니고(`<slug>`가 `harness`면 면제가 아니다), `docs/<slug>` 브랜치는 판정 6으로 지나더라도 CI가 그 harness 티켓 전부의 `Status:`가 done인지 본다. 이 저장소의 규약은 "티켓은 그 일을 하는 PR에 함께 싣는다"(`docs/agents/issue-tracker.md`)다. 그래서 티켓만 쓰는 PR은 CI에서 병합할 수 없다. 로컬 pre-commit은 `Status:`를 보지 않아(독스트링 "못 보는 것") 그때는 지났다.

사용자에게 셋을 물었다. 사용자가 "PR을 닫고 구현과 합치기"를 골랐다.

> 사용자(선택): PR을 닫고 구현과 합치기 — #619를 병합하지 않고 닫습니다. 티켓과 일지는 브랜치에 남고(닫아도 브랜치는 지워지지 않습니다), 다음 세션이 원인을 가르고 고치는 PR에 티켓을 함께 실어 done으로 바꿀 때 검사가 통과합니다. 규약 그대로입니다.

한 일: 이 일지의 인계 절과 이 절을 브랜치에 커밋해 푸시하고 PR #619를 닫았다. 병합하지 않았으므로 티켓은 아직 dev에 없고, 출시 PR #616은 그대로 빨갛다.

## 다음 (갱신)

- 구현 세션은 이 브랜치(`docs/e2e-standalone-token-rate-limit`, 머리는 이 절을 실은 커밋)에서 시작한다. 티켓은 이 브랜치에만 있다. `implement` 스킬은 브랜치 이름을 `chore/e2e-standalone-token-rate-limit`로 맞추라고 하므로 `git branch -m`으로 이름을 바꾸고 새 PR을 연다. 원격의 옛 브랜치 이름과 닫힌 PR #619는 정리 대상이다.
- 첫 편집으로 티켓의 `Status:`를 `in-progress`로 바꾸고, PR을 열기 전에 `done`으로 바꾼다. 순서는 가르기, 고치기, 회귀 시험이다.
- 위 "다음"의 #616 기다림과 병합 절차는 구현 PR이 dev에 병합된 뒤에 한다.
- 이번에 안 것(사건 하나): 티켓만 쓰는 harness PR은 CI에서 병합할 수 없다. 앞 세션이 면제로 읽은 것이 사실과 달랐다. 대기열에 올릴지는 retro가 판정한다.

## 인계 (커밋 뒤)

이 세션은 컨텍스트가 인계 문턱을 넘은 채 `커밋 뒤` 경계에 와서 구현 단계를 새 세션에 넘긴다. 위 "PR #619 처리"의 커밋(`0ccb538ce`)을 푸시했고 PR #619는 병합하지 않고 닫았다(닫는 코멘트 `pull/619#issuecomment-7062782845`). 이 세션이 받은 요청은 "PR과 병합까지"였으나 병합은 규약상 불가능해 사용자의 선택(PR을 닫고 구현과 합치기)으로 끝냈다. 새 세션은 티켓 `.scratch/harness/issues/e2e-standalone-token-rate-limit.md`를 구현한다.

open-session을 부른다 2026-11-21T12:45Z

## 구현 (새 세션)

브랜치를 `chore/e2e-standalone-token-rate-limit`로 바꾸고(`git branch -m`) 티켓을 `in-progress`로 시작했다.

**가른 결과: 티켓의 전제가 틀렸다.** 60번의 토큰 요청은 질문 길 실패를 만든 되풀이가 아니라 `deployment.e2e.ts`의 맨 마지막(열네째) 시험이 일부러 보낸 것이다. 질문 길 시험은 둘째이고, 그 뒤 데이터베이스 시험의 `docker compose down`·`up`과 재생성 시험의 `portal --force-recreate`가 컨테이너를 새로 만들어, 산출물의 `compose.log`에는 질문 길 시험이 지난 컨테이너의 기록이 없다(산출물을 `gh run download`로 받아 시각을 맞댔다: `portal` 첫 줄 07:09:58.12 직후 07:09:58.288부터 토큰 60번, `serve` 첫 줄 07:09:51). 위젯의 토큰 받기(`authorize`)와 되풀이 길(`run`·`reconnect`·`restore`)과 요소의 연결(`WidgetElement`)을 읽었으나 90ms에 60번을 만드는 자리는 없었다. 근거와 못 가른 것은 티켓의 "원인" 절에 적었다.

**고친 것:** 실패한 시험의 로그를 그 자리에서 남긴다. `web/packages/e2e-standalone/e2e/failure-logs.ts`의 `saveLogsAtFailure`와 그 시험(`failure-logs.test.ts`, 4개)을 더하고 `deployment.e2e.ts`의 `afterEach`에 이었다. 속도 제한(`site.conf`)과 위젯 코드는 건드리지 않았다.

**확인한 것(손으로 봤다):**
- 시험은 구현 전에 모듈이 없어 빨갛고(`failure-logs.ts` 없음) 구현 뒤에 4개 초록이다. 실패 판정 조건을 뒤집은 변이에서 4개 중 3개가 빨갛고 되돌리면 4개가 초록이다.
- 실제 배치에서 308 기대를 309로 일부러 바꾼 시험 하나를 돌리니 그 시험의 결과 폴더에 `compose-at-failure.log`가 생겼고, 프록시 접근 줄이 시각과 상태 코드째 들었으며 비밀값 글자는 없었다. 바꾼 기대는 되돌렸다.
- 이 PC에서 단독 배포 e2e 14개가 모두 통과했다(2.4분).

**못 가른 것:** 질문 길 실패의 원인. 화면(`error-context.md`)은 토큰을 받은 뒤 `/end-user/` 요청이 실패했음을 보일 뿐이다(5xx나 네트워크 실패이거나 시작 항목 전에 끝난 스트림). 앞선 실패 하나는 프록시 502였다. 프록시의 `serve` 이름 풀기(`resolve`, `valid=5s`)가 시작 때 `serve could not be resolved (2: Server failure)`를 남긴 것을 로그에서 봤으나 질문 길과 이어지는지는 가르지 못했고 추측으로 고치지 않았다.

## 다음 (갱신 2)

- 이 PR이 dev에 병합되면 출시 PR #616의 머리가 바뀌어 `e2e-standalone`과 `verify`가 다시 돈다. `uv run python tools/wait_ci.py 616 --head <git rev-parse origin/dev> --expect verify`를 백그라운드로 띄우고, 초록이면 `gh pr merge 616 --merge --match-head-commit <headRefOid>`로 병합해 `merge.md` "출시 PR"의 병합 뒤 일을 한다.
- 빨가면 새 산출물의 `compose-at-failure.log`에서 실패한 시험의 프록시 접근 줄·오류 줄·`serve` 로그를 읽고 원인을 가려 잇는 새 harness 티켓을 쓴다. 후보로 본 것은 프록시의 이름 풀기 지연뿐이고 근거는 아직 없다.
- 원격의 옛 브랜치 `docs/e2e-standalone-token-rate-limit`는 닫힌 PR #619와 함께 남는다. 병합 뒤 정리를 확인한다.

## 인계 (셀프 리뷰 직전)

이 세션은 컨텍스트가 인계 문턱을 넘은 채 `셀프 리뷰 직전` 경계에 와서 리뷰부터 뒤를 새 세션에 넘긴다. 이 세션의 제목은 `chore/e2e-standalone-token-rate-limit`였고 `<브랜치> (인계함)`으로 바꾼다. 이 세션이 받은 요청은 "PR과 병합까지"다. 앞서 받은 요청에 사용자 결정은 새로 없었다(첫 지시문이 전부다).

**이 세션이 한 것(전부 아직 커밋하지 않았다):** 브랜치 이름을 `chore/e2e-standalone-token-rate-limit`로 바꿈, 티켓 `Status:`를 `done`으로 바꿈과 "원인" 절·수용 기준 쓰기(`uv run python tools/plan_table.py`를 돌렸고 `.scratch/plan.md`는 바뀌지 않았다), `failure-logs.ts`와 `failure-logs.test.ts` 새로 쓰기, `deployment.e2e.ts`의 `afterEach` 잇기, 이 일지 갱신.

**돌려서 본 것:**
- 린트 `uv run ruff check . && uv run ruff format --check .`가 초록이다.
- `uv run python tools/run_checks.py`는 첫 바퀴에서 `web-verify`가 빨갰다. `FailedTest.status`가 선택 속성(`TestInfo.status`)이라 타입 오류였고, `readonly status?: string | undefined;`로 고친 뒤 `pnpm -C web verify`만 다시 돌려 초록이다. 같은 바퀴의 나머지(pytest 640초 포함)는 초록이었고 고친 것은 TS 한 줄이라 러너를 처음부터 다시 돌리지 않았다. 커밋의 pre-commit이 전체를 다시 돌린다.
- 단독 배포 e2e 14개가 모두 통과했다(2.4분). 일부러 실패시킨 시험에서 `compose-at-failure.log`가 생기는 것도 봤다.
- `failure-logs.test.ts` 4개: 구현 전 빨강(모듈 없음), 구현 뒤 초록, 실패 판정 조건을 뒤집은 변이에서 3개 빨강과 되돌린 뒤 초록.

**남은 일(순서):**
1. 셀프 리뷰 `/code-review`(고정점은 `origin/dev`)를 하고 Critical·Major를 반영한다. 리뷰에 밀 주장: 티켓 "원인" 절의 사실 문장(시험 순서 2번째와 14번째, 로그 시각 07:09:51·07:09:58.12·07:09:58.288, 컨테이너 재생성으로 로그가 사라짐, 위젯 코드에 90ms 60번의 되풀이 길이 없음). 전부 이 일지의 앞 절과 같은 근거다.
2. 커밋하고(pre-commit이 `Skipped`로 건너뛴 검사가 없는지 본다) 푸시한다. 브랜치 이름이 바뀌었으므로 `git push -u origin chore/e2e-standalone-token-rate-limit`이다. 옛 원격 브랜치 `docs/e2e-standalone-token-rate-limit`와 닫힌 PR #619는 병합 뒤 정리한다.
3. PR을 연다. 제목 접두는 `chore:`이고 느낌표는 붙이지 않는다(운영자가 올릴 때 손댈 것이 없다. 시험 틀만 바뀌었다). 이어 `merge.md`의 순서(봇 회차, 병합)를 따른다. 병합은 승인 없이 진행한다(메모리: 병합은 승인 없이).
4. 병합 뒤: 위 "다음 (갱신 2)"의 #616 기다림과 병합.

open-session을 부른다 2026-11-21T13:25Z

## 셀프 리뷰 (새 세션)

고정점 `origin/dev`(base `71182274e`), 파일 셋과 미추적 둘, 커밋 셋. 표준 축과 명세 축을 병렬로 돌렸다.

**지적과 판정:**
- 위젯 주장이 틀렸다(Major). `authorize`는 `useConversation`이 아니라 `components/pages/drivers.ts`가 다섯 곳(`run`·결정·따라가기·`reconnect`·`restore`)에서 부른다. "거절의 되풀이는 모두 간격을 둔다"도 거짓이다. `run`의 `restart`와 `reconnect`의 `from-start`는 기다림 없이 곧바로 다시 부른다. 코드로 확인했고(`lib/rejection.ts`의 `runStep`은 `target`이 빈 뒤 `restart`를 다시 내지 않고, `subscriptionStep`은 처음부터 구독한 뒤의 409를 `error`로 보낸다) 둘 다 한 번씩으로 묶여 90ms에 60번은 못 만든다. 결론은 같고 서술을 고쳤다.
- 글자 그대로가 아닌 인용 둘(Major). 따옴표를 뗐다(`질문 요청을 한 번도 받지 못했다`, postgres 줄의 번역).
- 수치 어긋남(Major). 원인 절의 "약 60ms"를 뺐다. 앞 단락의 약 90ms와 07:09:xx 시각은 산출물이 저장소에 없어 이 세션이 다시 대지 못했다고 적었다.
- `failure-logs.ts` 머리 주석의 "맨 끝 시험이 남긴 기록뿐"이 부정확했다. 데이터베이스·재생성 시험이 다시 만든 컨테이너의 기록이라고 고쳤다.
- `Compose.call`은 던지지 않고 `Outcome`을 돌려주므로 비정상 종료나 시간 초과가 조용히 쓰였다(Major, 시험이 가짜로 reject만 했다). `LogOutcome`을 받아 정상이 아니면 파일 첫 줄에 그 사실을 적게 했고, 시험을 7개로 늘렸다(비정상 종료, 시간 초과, 쓰기 실패 추가).
- 명세 축: 체크박스 문구가 요구를 낮췄다(Major). 티켓에 처음 기준과 줄어든 범위를 그대로 적었다. 질문 길 실패 자체를 다시 만드는 시험은 없다고도 적었다.
- 헬퍼 이름(`test_`, `source`, `FailedTest`)이 흐리다(Minor). `finishedAs`, `logsSaying`, `FinishedTest`로 바꿨다.

**남긴 것:** `afterEach`의 `compose()`가 통과한 시험에서도 만들어지는 것(환경 변수는 `globalSetup`이 정하고 `compose()`는 상태가 없어 위험이 낮다)과 `calc.llm.ts`에 같은 훅이 없는 것(이 PR이 겨눈 길이 아니다)은 고치지 않았다. 시간 초과 뒤 `afterEach`의 60초가 훅 예산에 걸리는지는 확인하지 못했다. 다음 실패 산출물에 `compose-at-failure.log`가 없으면 그 자리를 본다. 수용 기준 둘째의 줄어든 범위는 위 판정대로 둔다.

**PR 직전 리뷰에 밀 주장:** 티켓 "원인" 절 넷째 항목의 새 문장(`restart`는 한 번뿐, `from-start`는 한 번뿐), `failure-logs.ts` 머리 주석의 "그 시험 뒤에 돈 데이터베이스 시험과 재생성 시험이 다시 만든 컨테이너의 기록만 있었다".

**다시 돌린 것:** `pnpm -C web verify`(타입 129 파일 2777 시험 통과), `uv run ruff check .`와 `ruff format --check .`가 초록이다. 단독 배포 e2e `pnpm -C web/packages/e2e-standalone exec playwright test`는 14개가 모두 통과했다(2.4분, 손으로 쳤다). 나머지는 pre-commit이 갈음한다.
