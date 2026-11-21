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
