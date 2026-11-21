# 프록시가 serve 를 못 찾고 시작해도 곧 길을 연다 (harness e2e-standalone-proxy-serve-resolve)

2026-11-22. 티켓: `.scratch/harness/issues/e2e-standalone-proxy-serve-resolve.md`. 브랜치 `chore/e2e-standalone-proxy-serve-resolve`. 앞 일지: `2026-11-21-1935-e2e-standalone-token-rate-limit.md`.

## 왜

PR #620(실패한 시험 바로 뒤에 `compose-at-failure.log`를 남기는 시험 틀)을 dev에 병합하자 출시 PR #616의 머리가 `8013ab530`으로 바뀌어 `e2e-standalone`이 다시 돌았고(실행 44915085235) 또 빨갰다. 이번에는 새 산출물에 `compose-at-failure.log`가 실패한 두 시험(질문 길 시험과 네트워크 없는 MCP 시험) 몫으로 하나씩 들어 있었다. 앞 일지가 "다음 (갱신 2)"에 적은 대로 그 로그를 읽고 원인을 잇는 새 티켓을 썼다.

> 사용자: 네, 여기서 쓰기

앞 턴의 마무리 질문("원인 조사 티켓을 이 세션에서 쓸까요?")에 대한 답이다. 티켓만 올리는 PR은 CI의 `ticket` 검사가 막는다는 것을 앞 일지가 이미 적었으므로(PR #619), 티켓을 쓰는 이 세션이 원인 가르기와 고침도 같은 PR에 실었다.

## 로그에서 읽은 것

두 시험의 `compose-at-failure.log`를 손으로 읽었다. 둘 다 같은 컨테이너 묶음의 로그다.

- 14:42:44.89 프록시가 떴고 0.01초 뒤 `serve could not be resolved (2: Server failure)`를 한 번 남겼다. 그 뒤로 같은 줄은 없다.
- 14:42:56 `serve`가 시작을 마쳤고 14:42:57 `/health`가 200이었다(`postgres`와 `migrate`를 기다려 프록시보다 12초쯤 늦었다).
- 14:43:01.586과 14:43:11.309 두 시험의 `POST /end-user/runs`가 `no live upstreams while connecting to upstream`과 502였다. 같은 때 포털과 위젯의 화면 요청(`/portal/`, `/widget/`)은 200이었고(경로 우회를 시험하는 요청의 404는 설계된 응답이다) `serve`의 로그에는 두 요청이 없다. 앞 일지(`2026-11-21-1935-e2e-standalone-token-rate-limit`)는 같은 `Server failure` 줄을 봤지만 502와 잇지 못했다.

## 가른 것(손으로 돌린 실험)

프록시만 `serve`가 없는 격리 네트워크에 띄우고 `--dns 127.0.0.2`로 바깥 DNS를 끊었다. Docker 내장 DNS는 모르는 이름을 바깥으로 넘기므로 `Server failure`가 났고, 프록시 로그가 CI 로그와 글자 그대로 같았다(`serve could not be resolved (2: Server failure)`, 이어 `no live upstreams`와 502). 같은 이미지(`compose.yaml`이 고정한 nginx 1.30.6)와 `site.conf`의 `resolver`·`upstream` 설정을 옮겨 썼고, 1초마다 요청하는 감시 컨테이너를 곁에 두었다. 한 번씩만 돌렸다.

- 지금 설정: 이름 풀기 오류 16:54:34, `serve` 시작 16:54:47, 첫 200 16:55:04. 오류 뒤 30초 만이다. `valid=5s`가 있어도 오류 뒤 30초가 걸렸다.
- `resolver_timeout 2s` 추가: 오류가 2초마다 반복되고(16:55:59, 16:56:01, 16:56:03), `serve` 시작 16:56:10 뒤 16:56:12에 첫 200이 왔다.

재시도 간격이 `resolver_timeout`이라는 설명은 이 두 실행에서 세운 것이고 nginx 소스를 읽어 확인하지 않았다. 앞선 프로브(`.scratch/release-image/probes/bridge_recover/README.md`)가 어림으로 같은 가능성을 적어 두었다. CI 러너에서 `Server failure`가 난 까닭(러너의 DNS 설정)은 보지 못했다.

## 한 일

- 회귀 시험을 먼저 썼다: `deployment.e2e.ts`의 "프록시가 serve 를 못 찾고 시작해도 serve 가 건강해지면 15초 안에 최종 사용자 길이 열린다". `serve`를 지우고 프록시를 다시 만들되 시험 전용 덧씌움 `compose.dead-dns.yaml`로 바깥 DNS를 끊고, 프록시 로그에 `Server failure`가 있는지 먼저 단언한 뒤 `serve`를 올려 15초 안에 `POST /end-user/runs`가 502가 아니기를 기대한다. 끝나면 `finally`에서 프록시를 평소 모양으로 되돌린다.
- 고치기 전에 그 사례만 돌려 29.9초 만에 502로 빨간 것을 봤다. `site.conf`에 `resolver_timeout 2s;`를 더한 뒤 단독 배포 e2e 15개가 모두 통과했다(2.5분. 새 사례는 13.6초).
- 새 사례가 프록시를 다시 만들면 그 컨테이너의 로그가 사라져 `afterEach`가 받는 로그에 실패 순간의 프록시 줄이 없었다. 그래서 실패 메시지에 프록시 로그의 끝 15줄을 싣는다.

고르지 않은 길: `compose.yaml`에서 프록시가 `serve`를 기다리게 하는 `depends_on`. 프록시가 다시 시작할 때나 `serve`를 다시 만들 때의 같은 문제를 못 막고, 운영자가 고치지 않는 배포 파일의 시작 순서를 바꾸는 값이 크다. 이 판단이 틀렸다고 드러나면 새 티켓을 쓴다.

## 회고

후보 셋: 승인 1(새 대기열 항목), 기각 2, 넘김 0. 사용자에게 넘긴 것은 없다. 만료는 3건을 닫았다.

- **일지의 "다음"이 "새 harness 티켓을 쓴다"고만 적어 티켓만 올리는 PR을 계획하게 했다: 승인, 새 항목 `ticket-only-harness-pr-blocked-at-ci`(2회차).** 사건은 앞 일지의 PR #619(CI의 `ticket` 검사가 막아 닫았다)와 이번 세션의 계획이다. 이번에는 PR을 열기 전에 앞 일지와 `tools/check_ticket.py`의 독스트링을 읽어 막혔고 손상은 없었다. 새 지침 문장이라 문턱은 다섯 번째 반복이어서 회차만 센다. 같은 일을 다룬 열린 항목은 `--search 티켓만`·`done.이.아니`·`면제.모양`으로 찾았으나 없었다(닫힌 0575는 면제 PR의 파일 자리라 다른 일이다).
- **새 사례가 프록시를 다시 만들어 그 컨테이너의 로그가 사라진 것: 기각.** 앞 티켓이 겪은 "뒤의 시험이 컨테이너를 다시 만들어 로그가 사라진다"와 같은 모양이었으나, 이 PR의 시험 코드가 실패 메시지에 로그 끝을 싣는 것으로 그 자리에서 고쳤다. 하네스가 아니라 시험 틀의 일이다.
- **`ls docs/journal`이 약 2만 3천 자를 내 큰 결과 알림이 붙었다: 기각.** 이미 있는 훅(`hook_large_result`)이 그 자리에서 알렸다.
- **만료한 항목 셋(승인 줄의 가장 늦은 날짜가 2026-11-07):** `0310`, `doc-pr-security-lens`, `probe-readme-result-cells`. 기준 브랜치(`origin/dev`)로 다시 돌린 출력에도 같은 셋이 있어 상태 줄을 `만료 2026-11-22 (ADR 0036)`로 고쳤다.

## 셀프 리뷰

`/code-review`(고정점 `origin/dev`, 변경된 파일과 미추적 파일 포함)를 표준 축과 명세 축으로 돌렸다. Critical·Major는 없었다.

- **고친 것(사실 확인이 되는 수치와 표현):** 티켓에서 "5초와 15초"를 `/health` 200 기준 "4초와 14초"로, 2초 실험의 첫 200 시각을 "시작 뒤 약 1.3초"에서 "감시 기록이 초 단위라 1초에서 3초 사이"로, 프록시를 띄운 뒤 `serve`를 올린 시간을 "13초(첫째 실행)와 11초(둘째 실행)"로, 포털과 위젯 화면 요청의 200과 경로 우회 시험의 404(설계된 응답)를 가르게, 앞 일지가 `Server failure` 줄을 보고도 502와 잇지 못했다는 것을 고쳤다. 일지의 "`valid=5s`로는 복구되지 않았다"는 "`valid=5s`가 있어도 오류 뒤 30초가 걸렸다"로, `site.conf`의 주석은 "두 번 손으로 돌렸고 nginx 소스로 확인하지 않았다"를 밝히는 말로 낮췄다. 시험의 반복 조건은 `status !== 502`에서 `status < 500`으로 넓혔다(5xx 모두 길이 열리지 않은 것으로 본다).
- **티켓에 더한 것:** "회귀 시험의 한계(코드를 읽은 것)" 문단. 고치기 전에 빨갛려면 `serve`가 15초보다 일찍 건강해져야 하는데 그 시간을 재서 적지 않았다는 것, 선행 단언이 `Server failure`에 기대어 다른 Docker에서는 단언에서 크게 실패한다는 것, 바깥 DNS가 느리게 답하는 경우는 재현하지 못했다는 것이다.
- **남긴 것:** 위 한계는 이 PR이 풀지 않는다. 한계가 드러나는 때(CI에서 이 사례가 선행 단언에서 빨갛거나 15초 안에 닿지 않는 때)에 새 티켓을 쓴다. 시험 도우미 이름(`upServe`)은 그대로 두었다.
- **다시 돌릴 것:** 이 리뷰 뒤로 시험 파일과 `site.conf` 주석만 바뀌었고 동작은 같다. 새 사례만 다시 돌리고, 나머지는 커밋의 pre-commit이 다시 돈다.
- **리뷰에 밀 주장(반영으로 새로 쓴 문장):** 티켓의 "4초와 14초(`/health` 200 기준. 프록시가 뜬 지 16초와 26초)", "13초(첫째 실행)와 11초(둘째 실행) 뒤", "시작 뒤 1초에서 3초 사이", `site.conf` 주석의 "valid 가 있어도 그랬다".

## PR 직전 리뷰

`coderabbit-review`(CodeRabbit CLI 0.7.5, `Seat: not assigned`인데도 `review_completed`까지 돌았다, 지적 1건)를 돌렸다.

- **고친 것:** 새 사례의 `finally`에서 `serve` 올리기가 던지면 프록시를 평소로 되돌리는 줄이 실행되지 않아 프록시가 죽은 DNS를 단 채 남고 뒤의 사례가 연쇄로 실패한다(Minor, 유효). `serve` 올리기를 안쪽 `try`로 감싸고 프록시 되돌리기를 그 `finally`에 넣었다.
- **남긴 것과 이유:** (가) 15초를 `serve`가 건강해진 뒤 `logs` 확인까지 끝난 다음부터 재서 그만큼 한도가 느슨하다: `compose logs`가 보통 1초 안이라 거짓 실패는 없고 앞 사례도 같은 모양이다. (나) 판정이 `status < 500`이라 프록시가 직접 낸 4xx(허용 목록에서 길이 빠진 404 등)도 통과한다: 이 사례가 지키려는 것은 "serve에 닿았다"이고 길의 허용 목록은 같은 파일의 다른 사례가 본다. (다) 프록시를 되돌린 뒤 `--wait`가 없어 바로 뒤 429 사례가 거짓 실패할 수 있다: 같은 패턴인 앞 사례가 그대로 지나갔고, 이 사례 포함 전체 15개가 통과했다. 거짓 실패가 CI에서 보이면 그때 고친다.
- **질문의 답(리뷰어):** `resolver_timeout 2s`는 질의 빈도(`valid=5s`)를 바꾸지 않고 질의가 응답을 기다리는 상한만 줄인다. 시험 전용 덧씌움은 `tools/release.py`의 묶음(`deploy/standalone`)에 들지 않는다. 리뷰어도 원인 설명이 가설이라고 같은 한계를 적었다.
- **다시 돌릴 것:** 시험 파일이 바뀌어 새 사례를 다시 돌리고 커밋의 pre-commit이 나머지를 돈다.

## 봇 회차(PR #621)

첫 회차: claude-review는 지적 없음, CodeRabbit이 인라인 둘을 냈다. 둘 다 코드를 열어 판단했다.

- **Major, 시험 제한 시간이 끝나면 프록시 복원이 안 될 수 있다: 고쳤다.** `serve`가 끝내 건강해지지 않으면 본문의 `upServe`(`UP_WAIT_SECONDS + 60`초)와 `finally`의 `upServe`가 시험 제한 시간(`UP_WAIT_SECONDS + 180`초)을 거의 다 써서 프록시 복원에 닿지 못한다. 프록시 복원은 `--no-deps`라 `serve` 없이 되므로 순서를 바꿔 프록시를 먼저 되돌리고 그 `finally`에서 `serve`를 올린다.
- **Minor, `serve`를 올리기 전에 `Server failure`가 찍혔는지 기다려 확인하라: 고쳤다.** 막지 않아도 큰 소리로 실패하는 모양이라(조용히 틀리지는 않는다) 급하지는 않지만, 고치는 값이 작아 `expect.poll`로 15초까지 로그를 기다린 뒤 `serve`를 올리게 했다. 확인이 `serve`를 올린 뒤에 있던 순서가 실행 순서에 기대는 것이었다.
- **리뷰에 밀 주장(이 회차가 새로 쓴 문장):** `finally`의 "프록시는 serve 없이도 다시 만들 수 있으므로(--no-deps)", 본문의 "serve 가 먼저 DNS 에 올라 첫 질의가 성공하면 이 시험이 보려는 상황이 아니므로, 여기서 크게 실패한다".
- **다시 돌린 것:** 새 사례만 다시 돌렸다(아래 결과는 커밋 뒤 PR 본문에 옮긴다).

## 다음

- 이 PR이 dev에 병합되면 출시 PR #616의 머리가 바뀌어 `e2e-standalone`과 `verify`가 다시 돈다. `uv run python tools/wait_ci.py 616 --head <git rev-parse origin/dev> --expect verify`를 백그라운드로 띄우고, 초록이면 `gh pr merge 616 --merge --match-head-commit <headRefOid>`로 병합해 `merge.md` "출시 PR"의 병합 뒤 일을 한다.
- 빨가면 새 산출물의 `compose-at-failure.log`를 읽는다. 새 시험이 걸러내지 못한 길이 남았다는 뜻이다(프록시가 `Server failure` 말고 다른 까닭으로 `serve`를 못 찾는 경우 등).
- 원격의 옛 브랜치 `docs/e2e-standalone-token-rate-limit`는 닫힌 PR #619의 것이다. 삭제 명령을 권한 분류기가 거부해 남아 있다. 사용자가 지워도 된다고 하면 지운다.
- 주 체크아웃(`C:/project/agent`)은 이 세션이 인계하기 직전 `git worktree list`에서 dev의 `8013ab530`이었다(다른 세션이 당겨 둔 것으로 보인다). PR #620의 병합 뒤에 이 세션이 "미갱신"이라고 전한 것은 그 사이 풀렸다. 병합이 다시 dev를 앞세우면 주 체크아웃 세션의 `/tidy-checkouts`로 당긴다(워크트리 세션은 당기지 않는다).

## 인계 (셀프 리뷰 직전)

인계 못함 셀프 리뷰 직전: 이 세션은 컨텍스트가 인계 문턱을 넘은 채 `셀프 리뷰 직전` 경계에 와서 `handoff.md`의 순서대로 제목을 `chore/e2e-standalone-proxy-serve-resolve (인계함)`으로 바꾸고 `web verify` 백그라운드를 멈췄다. 그다음 `git worktree unlock C:/project/agent/.claude/worktrees/03-serve-requires-database`를 앱의 권한 분류기가 거부했다(이유: 파괴적이거나 원치 않는 동작). 잠금을 풀지 않으면 새 세션의 `EnterWorktree(path)`가 `belongs to another running Claude Code session`으로 거부된다(`handoff.md` 4). 그래서 열지 않고 제목을 원래대로(`chore/e2e-standalone-token-rate-limit`) 되돌렸으며, 이 세션에서 셀프 리뷰부터 잇는다. 아래 "남은 일"은 이 세션이 그대로 밟는다. 이 세션이 받은 요청은 "PR과 병합까지"다(앞 세션의 인계 지시문 그대로이고, 사용자의 새 결정은 이 일지 "왜"의 `네, 여기서 쓰기` 하나다).

**이 세션이 한 것(전부 아직 커밋하지 않았다):** 브랜치 `chore/e2e-standalone-proxy-serve-resolve`를 `origin/dev`(`8013ab530`)에서 땄다. 티켓 `.scratch/harness/issues/e2e-standalone-proxy-serve-resolve.md`(`Status: done`, 수용 기준 넷 체크, 다섯째 "검증 명령이 모두 초록이다"는 아직 비었다. 일곱째 "병합 뒤 #616" 칸은 병합 뒤의 일이라 비워 둔다)를 썼다. `web/packages/e2e-standalone/compose.dead-dns.yaml`을 새로 쓰고 `e2e/deployment.e2e.ts`에 회귀 사례를 더했으며 `deploy/standalone/proxy/site.conf`에 `resolver_timeout 2s;`를 더했다. `uv run python tools/plan_table.py`를 돌렸고 `.scratch/plan.md`는 바뀌지 않았다. 이 일지와 그 회고 절을 썼고(`retro`는 이 세션이 이미 돌았다. 새 세션은 다시 돌지 않는다), 대기열에 새 항목 `ticket-only-harness-pr-blocked-at-ci`를 쓰고 항목 셋(`0310`, `doc-pr-security-lens`, `probe-readme-result-cells`)을 만료로 닫았다.

**돌려서 본 것:**
- 단독 배포 e2e 15개가 모두 통과했다(2.5분, `pnpm -C web/packages/e2e-standalone exec playwright test`로 손으로 쳤다). 새 사례는 고치기 전에 같은 명령에 `-g "serve 를 못 찾고"`를 붙여 29.9초 만에 502로 빨갛다가 고친 뒤 13.6초에 초록이다.
- `uv run ruff check .`와 `uv run ruff format --check .`가 초록이다.
- `pnpm -C web verify`는 셀프 리뷰 반영 뒤에 다시 돌려 통과했다(테스트 2777개 통과, 1개 건너뜀, 550초). 앞서 한 번은 멈춰서 중단했었다(TaskStop). 셀프 리뷰 뒤 새 사례만 다시 돌려 22.2초에 통과했다. 커밋의 pre-commit이 나머지를 다시 돌린다.
- 셀프 리뷰(`/code-review`)는 위 "셀프 리뷰" 절대로 이 세션이 마쳤다(인계 직전에는 하지 못했다).

**남은 일(순서):**
1. 셀프 리뷰 `/code-review`(고정점 `origin/dev`)를 하고 Critical·Major를 반영한다. 리뷰에 밀 주장: 티켓 "원인" 절과 일지 "가른 것"의 사실 문장(30초와 2초의 복구 시각, "`valid=5s`가 있어도 오류 뒤 30초가 걸렸다", 프록시가 `serve`보다 먼저 뜨고 `depends_on`이 없다는 것, 두 실패 시험의 502 시각). 근거는 이 일지와 티켓이 같다(CI 로그와 이 PC의 손 실험, 실험은 한 번씩만 돌렸다는 것도 적혀 있다). 재시도 간격이 `resolver_timeout`이라는 설명은 두 실행에서 세운 것이지 nginx 소스를 읽은 것이 아니라고 이미 적었다.
2. 커밋 전 `uv run python tools/sibling_overlap.py`를 치고(번호 겹침 없음이었다), `git branch --show-current`로 브랜치를 본다. 커밋하고(pre-commit이 `Skipped`로 건너뛴 검사가 없는지 본다) `git push -u origin chore/e2e-standalone-proxy-serve-resolve`로 푼다.
3. PR 직전 `coderabbit-review`를 돌리고 PR을 연다. 제목 접두는 `chore:`이고 느낌표는 붙이지 않는다(운영자가 올릴 때 손댈 것이 없다. `site.conf`는 배포 묶음 안의 파일이지만 운영자가 고치는 파일이 아니고 값 하나가 더해질 뿐이다). 본문은 `.github/PULL_REQUEST_TEMPLATE.md`를 채운다. 변경된 영역은 `deploy/`와 `web/`(시험 틀)과 `docs/`·`.scratch/`다. 계약 영향 없음. 체크리스트는 실제로 한 것만 체크한다(위 "돌려서 본 것"). PR을 연 뒤 `get_status`로 앱이 그 PR을 보는지 보고 아니면 `bind_pr`.
4. `merge.md`의 순서(봇 회차, 병합)를 따른다. 병합은 승인 없이 진행한다(메모리: 병합은 승인 없이).
5. 병합 뒤: 위 "다음"의 #616 기다림과 병합.
