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
