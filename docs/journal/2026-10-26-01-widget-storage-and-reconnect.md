# 2026-10-26 (01) 위젯이 대화를 저장하고 새로 고친 뒤와 끊긴 뒤 같은 실행에 다시 붙는다 (web-widget 09)

## 사용자 프롬프트

> 사용자: /implement .scratch/web-widget/issues/09-widget-storage-and-reconnect.md (next-session 지시문. 새 세션이고 tidy-checkouts 를 먼저 돌고 EnterWorktree(09-widget-storage-and-reconnect)로 들어간다. 브랜치 feature/09-widget-storage-and-reconnect, 범위는 PR과 병합까지. 읽을 것은 일지 2026-10-25-01 의 "다음". 이어받을 상태는 PR #385 셋째 회차 claude-review 가 보류한 Minor·Nit 셋과 "다음" 1(골격 모으기). 티켓 10(PR #386)이 `api/runs/index.ts`·`WidgetPage.tsx`·`WidgetScreen.tsx`·`useConversation.ts` 를 함께 고쳐 글자 충돌이 날 수 있다)

첫 세션은 2026-10-25 에 위 지시문으로 시작해 구현과 main 합치기까지 하고 계정의 주간 한도에 걸려 멈췄다. 2026-10-26 에 다른 계정의 새 세션이 이어받았다.

> 사용자: feature/09-widget-storage-and-reconnect 다른 계정에서 작업하던거 이어받아서 진행할 수 있어?

이어받은 세션이 커밋 e9ecae81 뒤에 인계했고, 셋째 세션이 아래 "인계 (커밋 뒤)"의 지시문으로 시작했다.

> 사용자: /implement .scratch/web-widget/issues/09-widget-storage-and-reconnect.md (next-session 지시문. PR 직전 리뷰부터 PR과 병합까지)

## 정리(tidy-checkouts)

주 체크아웃을 `origin/main` 으로 당겼다(1ef75a12 → cb6d9c39). 지운 것은 없다. 병합된 위젯 워크트리 여덟이 접힌 `web/apps/widget/public/` 때문에 남았고(tidy_checkouts 의 버그, 아래 "다음"), pwsh 가 쥔 워크트리 셋과 python(pid 41176)이 쥔 휴지통의 `worktree-overrides-pc-check~~.venv` 가 남았다.

셋째 세션의 정리: 주 체크아웃을 cb6d9c39 → 8ad99ca6 으로 당겼다. 워크트리 셋(`01-harness-ticket-numbers`, `07-morning-report-harness-branches`, `design-reverse-sync-spec`)과 그 브랜치, 체크아웃되지 않은 브랜치 `worktree-09-widget-storage-and-reconnect`, 휴지통의 `worktree-overrides-pc-check~~.venv` 를 지웠다. 위젯 워크트리 아홉은 같은 `public/` 버그로, `06-round-drive-record` 는 바뀐 파일이 있어 남았다.

## 결정

명세와 티켓이 정하지 않은 자리를 정했다. 마지막 둘은 이어받은 세션이 셀프 리뷰에서 정했고 나머지는 첫 세션이 정했다.

- **비동기 일을 `components/pages/drivers.ts` 로 모았다(일지 2026-10-25-01 "다음" ①).** 시작·이어 가기(`run`), 결정(`decide`), 409 뒤 따라가기(`follow`), 다시 잇기(`reconnect`), 되돌리기(`restore`)가 토큰 받기와 묶음 견주기(`authorize`), 요청 열기(`open`), 스트림 넘기기(`pump`), 받은 것 세기(`Received`)를 나눠 쓴다. 상태 코드 → 다음 걸음은 순수 함수(`lib/rejection` 의 `runStep`·`decisionStep`·`subscriptionStep`·`followNotice`)로 뺐다(PR #385 보류 셋째). `readItems` 의 `any` 이름과 명령·질의 섞임은 `Received` 가 넘기기만 하고 무엇을 받았는지는 필드로 묻는 꼴로 닫았다(보류 둘째). 429 를 `error instanceof RunRejected` 와 겹쳐 가르던 자리는 `open` 이 모든 실패를 `RunRejected` 로 바꿔 돌려주어 사라졌다(보류 첫째).
- **`expired` 가 다시 붙을 실행을 비운다(같은 "다음" ②).**
- **409 뒤 다시 구독의 404 는 "요청을 처리하지 못했습니다."로 둔다(같은 "다음" ③).** 구독 404 행(1초 뒤 한 번 더, 또 404 면 저장과 화면을 비운다)은 끊긴 실행에 다시 붙는 구독의 행이다. 결정의 409 뒤 따라가기에서 404 가 나면 카드가 다시 결정을 받고, 다시 고르면 실행이 없어 결정이 404 를 두 번 받아 `expired` 로 정리된다.
- **`Connection` 을 `Session` 에 실었다.** 티켓 10 이 들인 길(기준 주소와 토큰 함수)을 일 하나가 들고, 모든 요청이 그 길의 기준 주소로 간다. 09 의 화면은 `ConnectedWidget` 을 거쳐 iframe 과 페이지 안 방식에 함께 선다(일지 2026-10-25-02 "다음").
- **45초 무응답의 끊기는 타이머 콜백이 아니라 `Promise.race` 의 이어짐에서 한다.** 아래 "진단".
- **상한의 카운트다운은 갱신 함수 안에서 남은 초를 센다.** 화면 동작 시험의 `act` 가 시계를 돌리는 동안 그리기를 미루어, 타이머가 울린 때 센 값이 적용될 때는 이미 지난 값이었다(07 의 카운트다운 시험 셋이 빨갰다).
- **기존 시험의 토큰을 풀 수 있는 JWT 꼴(`testing/site.ts` 의 `siteToken`)로 바꿨다.** 명세가 "풀지 못한 토큰은 받지 못한 토큰과 같다"고 정해, 글자 그대로의 가짜 토큰은 이제 토큰을 받지 못한 것이다. 단언은 바꾸지 않았다.
- **e2e 의 사이트 페이지가 토큰 주체(`sub`)를 고정한다.** `signToken` 이 토큰마다 무작위 `sub` 를 주어, 새로 고친 뒤의 토큰이 앞 사람의 것으로 읽혔다. `/?sub=` 와 `/token?sub=` 로 고정한다(`e2e/site.ts`).
- **다시 잇기가 붙어서 새 항목을 받았을 때만 간격을 처음부터 센다.** 명세는 간격(1, 2, 4, 8, 16초, 그 뒤 30초)과 "붙으면 띠가 걷힌다"만 정했다. 붙어서 새 항목을 받으면 한 번의 다시 잇기가 끝난 것으로 본다. 붙었지만 아무것도 받지 못하고 닫히면 이어서 센다. 그러지 않으면 곧바로 닫는 서버에 1초마다 붙는다.
- **다시 잇기가 멈춰도(세 번의 처리하지 못한 거절, 구독의 401) 다시 붙을 실행은 비우지 않는다.** 새로 고치면 처음부터 다시 붙어 본다. 실행은 서버에서 아직 돌 수 있고, 401 의 알림은 바로 "페이지를 새로 고쳐 주세요"라고 안내한다. 거절이 다시 붙을 실행을 비우는 것은 실행이 사라졌다고 서버가 말한 때(구독과 결정의 둘째 404)뿐이다.

## 한 것

- `lib/storage.ts`(새것): 키 `agent-os-widget:<에이전트>`, 토큰 페이로드의 묶음(`bundleOf`, 검증 없이 base64url 을 풀어 읽는다), 대화의 저장할 몫(`snapshotOf`)과 되돌리기(`conversationOf`), 판 번호와 실행 중의 모양 검사(`load`), 용량의 세 단계(`save`), 막힌 저장소.
- `lib/reconnect.ts`(새것): 간격(1, 2, 4, 8, 16초, 그 뒤 30초), 45초 무응답, 마지막 항목으로 가르기(`endingOf`), 재접속 띠의 상태와 글.
- `lib/rejection.ts`(새것): 시작·이어 가기, 결정, 구독, 409 뒤 따라가기의 상태 코드 → 다음 걸음.
- `lib/conversation.ts`: 다시 붙을 실행(`reattach`)과 그 옮김, 동작 `restored`·`switched`·`vanished`·`lost`, 결말 `lost`. `ended` 는 시작 항목 전에만 쓴다.
- `lib/limit.ts`: 기다림의 쓰임 `subscribe` 와 그 문구("연결이 많아 N초 뒤에 다시 잇습니다. 받은 내용은 그대로 있습니다.").
- `api/runs`: `subscribeRun` 의 `Last-Event-ID` 가 null 이면 헤더 없이 처음부터 받는다.
- `components/pages/drivers.ts`(새것)와 `useConversation.ts`: 비동기 일을 drivers 로 옮기고, 훅은 일의 자리, 되돌리기(`restore`)의 자리, 재접속 띠, 저장을 든다.
- 부품: `Composer` 가 재접속 띠를 맨 앞에 세우고, `Conversation` 이 다시 잇는 동안 목록의 진행 표시를 숨기며 빈 요청 상자를 그리지 않는다. `FailureAlert` 이 `lost`("새 대화"만)를, `WidgetScreen` 이 되돌리는 동안의 진행 표시와 토큰을 받지 못한 알림을, `ConnectedWidget` 이 보내기와 "새 대화"의 막음을 잇는다.
- 시험: `pages/WidgetStorage.test.tsx`·`pages/WidgetReconnect.test.tsx`(새것), 기존 시험의 토큰을 `siteToken` 으로. `WidgetFailures.test.tsx` 의 "시작 항목 뒤에 결말 없이 끝난 스트림" 행은 끊김이라 재접속 시험으로 옮겼다. 스토리 `WidgetScreen` 의 Restoring·RestoreUnauthorizedWide·Reconnecting·ReconnectLimitedWideDark, `ComposerBand`·`FailureAlert`·`Conversation` 의 재접속 몫. 사진 7장이 새로 서고 4장이 바뀌었다.
- e2e: 승인 대상에서 멈추는 에이전트(`approval`)를 임시 플러그인 루트에 더하고, 새로 고친 뒤 도는 실행과 멈춘 실행에 다시 붙는 사례 둘.
- 변이 표: `storage_mutations.toml`(새것, 13), `widget_e2e_mutations.toml` 의 7·8, 그리고 원문이 옮겨 간 표들의 원문 맞추기.

## 진단

재접속 시험의 새로 고침 테스트가 45초 테스트 뒤에서만 빨갰다. diagnosing-bugs 로 좁혔다. 45초 무응답을 타이머 콜백(매크로태스크)에서 끊으면 undici 가 `assert(!this.aborted)` 에 걸렸고, 뒤 테스트가 같은 출처로 보낸 요청이 실패했다. 탐침(`.scratch/web-widget/probes/msw_abort_order.mjs`)이 마이크로태스크에서 끊는 대조와 전역 디스패처를 새것으로 바꾸는 갈래로, 끊기 자체가 탈이 아니라는 것과 망가진 것이 MSW 가 아니라 undici 의 연결이라는 것을 갈랐다. 가짜 소켓이 매크로태스크에서 끊기면 close 를 error 보다 먼저 낸다는 까닭은 인터셉터의 소스를 읽은 어림이다. `Promise.race` 의 이어짐에서 끊게 고치자 그 실패와 처리되지 않은 에러가 함께 사라졌다. 결과는 그 README 의 "2026-10-25 결과 — 끊는 자리" 절이고, 회귀 가드는 `storage_mutations.toml` 의 6 이다.

## 이어받은 세션의 검사 (셀프 리뷰 전)

main 을 합친 작업 트리에서 돌렸다.

- `uv run python tools/run_checks.py`: 검사 열 모두 지났다(check-ticket, zizmor, lint-imports, check-instructions, check-type-escapes, pyright-linux, pyright, run-hooks, pytest, web-verify).
- `uv run ruff check .`·`uv run ruff format --check .`: 둘 다 지났다.
- `pnpm -C web/apps/widget exec playwright test`: 15 가 모두 통과했다. 첫 회에 한 사례가 빨갰다가 다시 돌리자 지났다. 앞 세션에서도 본 플레이크라 이것이 두 번째 관찰이다.
- `uv run --env-file ../../../.env pytest -m llm_widget`: 1 이 통과했다. 토큰 6,555(입력 6,483, 출력 72), 트레이스 1, 모델 호출 2.
- `pnpm -C web visual:widget`(Docker): 42 가 모두 통과했다.
- 변이 표 `widget_e2e_mutations.toml` 의 7·8 은 main 을 합치며 겨눈 줄이 옮겨 가 표지의 줄 번호를 157:57, 180:22 로 맞췄다.

## 셀프 리뷰

`/code-review`, 기준 8ad99ca6(origin/main), 커밋 0(모두 작업 트리), 바뀐 추적 파일과 미추적 파일은 커밋 직전에 세어 35·16(plan.md 는 반영 때 처음 고쳤다). 표준 축(sonnet·high)과 명세 축 모두 Critical·Major 가 없었다.

고친 것:

- 구독의 404 사이에 다른 거절이 끼면(404 → 500 → 404) 뒤의 404 를 "또 404"로 읽어 1초 뒤 한 번 더 없이 저장과 화면을 비웠다(명세, 두 축이 함께 짚었다). 시험을 먼저 써서 빨강(덤프에 "이전 대화를 이어 갈 수 없어"가 섰다)을 본 뒤, 구독의 거절마다 그 걸음이 "한 번 더"일 때만 다음 404 를 "또 404"로 읽게 고쳤다.
- 구독의 422 와 표 밖의 상태(503)를 시험하지 않았다(명세). 500 시험을 422·500·503 으로 넓혔다.
- 결정의 둘째 404 뒤 새로 고치면 구독하지 않는 것, 다시 잇기가 멈춘 뒤(세 번의 500, 401) 새로 고치면 처음부터 다시 붙는 것, 용량이 다시 붙을 교환의 요청 글까지 뺀 뒤 새로 고치면 요청 상자 없이 다시 붙는 것을 시험하지 않았다(명세). 셋을 더했다. 위의 넷은 고친 판에서 처음부터 초록이라 변이 일곱(`storage_mutations.toml` 7~13)을 더했다. 변이를 손으로 넣고 `pnpm -C web exec vitest run --project widget-pages <파일> -t <이름>` 의 실패 출력을 본 뒤 표지를 골랐다.
- 409 뒤 따라가기의 거절 갈래를 순수 함수 `followNotice` 로 뺐다(명세, 판단 항목).
- `pump` 주석이 측정과 어림을 섞었다(표준). 탐침이 잰 것과 소스를 읽은 어림을 갈랐다.
- `msw_abort_order.mjs` 머리는 셋 가운데 하나라도 빼면 초록이었다고만 적어 셋이 무엇인지 없었고 README 와도 달랐다(표준). README 와 같은 사실(둘은 빼면 초록, `signal` 은 빼도 빨강, 손으로 본 것)로 고쳤다.
- 프로브 README 가 든 `widget-pages` 전체의 수(174개)가 어느 판의 수인지 없었다(표준). main 을 합치기 전의 판이라고 적었다.
- `bundleOf` 주석이 `sub` 가 빈 글자인 토큰도 거절한다는 것을 빠뜨렸다(표준). 더했다.
- 불리언 인자 `reconnect(…, fromStart)`(표준, 판단 항목)를 `"after-cut" | "after-reload"` 로 바꾸고 e2e 변이 7 의 원문을 맞췄다. `Session.claim` 이 묻기와 바꾸기를 함께 했다(표준, CQS). `matches`·`hold` 로 나눴다. `Restore` 가 drivers 의 `Restored` 를 되풀이했다(표준). `"loading" | Restored` 로 두었다. `runStep`·`decisionStep` 의 불리언 위치 인자(표준)를 `subscriptionStep` 처럼 객체 인자로 바꿨다.
- 원문이 옮겨 간 변이 표 원문을 맞췄다(`storage_mutations.toml` 1 의 import 자리). 표 열하나의 `--check` 가 모두 지났다.

PR 직전 리뷰에 밀 주장(반영으로 새로 쓴 사실 문장):

- `drivers.ts` 의 `pump` 주석: "마이크로태스크 안에서 끊으면 둘 다 나지 않았고, 망가진 것이 MSW 가 아니라 undici 의 연결이라는 것도 갈랐다(… msw_abort_order.mjs 가 쟀다). 가짜 소켓이 타이머 콜백에서 끊기면 close 를 error 보다 먼저 낸다는 까닭은 인터셉터의 소스를 읽은 어림이고 재지 않았다."
- `drivers.ts` 의 다시 잇기 주석: "1초 뒤 한 번 더 보낸 것만 "또 404"다. 그 사이에 다른 거절이 끼면 다음 404 는 다시 첫 404 다."
- `msw_abort_order.mjs` 머리: ""스트림을 읽다 마이크로태스크에서 끊기"와 "한 틱 기다리기"는 하나라도 빼면 초록이었고, 구독의 `signal` 은 빼도 빨갰다. 이 줄임은 임시 테스트 파일로 손으로 본 것이다."
- `storage.ts` 의 `bundleOf`: "풀지 못하거나, 둘 중 하나라도 없거나 문자열이 아니거나, `sub` 가 빈 글자면 null 이다."
- `rejection.ts` 의 `followNotice`: "401 은 로그인 정보를 받지 못한 것이고 그 밖은 처리하지 못한 것이다. 404 도 그렇다."
- 프로브 README 의 저장 표 행(변이 13 과 그 목록), e2e 표 행(변이 8), "174개. origin/main 을 합치기 전의 판에서 센 수다", `storage_mutations.toml` 의 머리와 7 부터의 절 머리.
- `.scratch/plan.md`: "web-widget 이 2026-10-26 에 닫혔다(티켓 01~11, PR #375 부터 …). 그것을 기다리던 기능은 없어 프론티어는 admin-style, design-reverse-sync 둘이다."
- 위 "결정"의 마지막 둘.

남긴 것:

- `reconnect()` 의 길이(표준, 판단 항목). 거절 표 하나를 그대로 옮긴 상태 기계이고 갈래마다 시험이 있다. 나누면 표의 한 행이 두 자리로 흩어진다.
- `authorize` 뒤의 같은 꼴 분기 넷(표준, Duplicated Code). 토큰을 받지 못했을 때와 묶음이 바뀌었을 때 할 일이 부르는 쪽마다 다르다(시작은 `no-token`, 결정은 카드 아래 알림, 다시 잇기는 띠를 걷고 알림).
- `Session` 이라는 이름(표준). `CONTEXT.md` 가 대화·실행에 피하라는 "세션"과 겹친다는 지적인데, 이것은 일 하나가 화면에 닿는 길이다. 대안(Job, Task, Slot)이 다른 피할 말이나 화면 용어와 겹쳐 두었다.
- 간격을 세는 `backoff` 를 함수 안에 둔 것, `reconnecting` 이 여러 자리에서 불리는 것, `(storage, key)` 쌍(표준, 판단 항목). 지역 셈이고 한 훅 안의 짝이다.
- 스토리가 `CUT_TEXT` 와 같은 글을 따로 적은 것(표준, Duplicated Code). 시험과 스토리가 명세 문구를 글자 그대로 보아야 문구가 바뀌면 빨개진다.
- 되돌리는 동안의 진행 표시 이름표 "이전 대화를 불러오고 있습니다."가 명세에 없는 글이라는 지적(명세). 진행 표시 부품(`Progress`)은 이름표가 있어야 하고 그것이 화면 읽기 프로그램이 읽는 이름이다.
- 새 항목을 받으면 간격이 처음으로 돌아가는 것이 명세 밖이라는 지적(명세). 위 "결정"에 적었다.
- 앞 티켓들의 미래형 문장("09 가 닫는다")을 고치라는 지적(명세). 이 PR 로 web-widget 이 닫히면 그 티켓들은 기록이다(`docs/constitution/operations.md` 문서 위치).

다시 돌린 것:

- `pnpm -C web exec vitest run --project widget-pages`: 파일 8, 시험 196 이 모두 통과했고 처리되지 않은 에러가 없었다.
- `pnpm -C web/apps/widget exec tsc --noEmit -p .`, `pnpm -C web exec eslint apps/widget/components/pages apps/widget/lib`, `pnpm -C web exec prettier --check apps/widget/components/pages apps/widget/lib`: 모두 지났다(Prettier 가 `useConversation.ts` 하나를 고친 뒤).
- `PYTHONUTF8=1 uv run python tools/mutate.py --check` 로 web-widget 표 열하나: 모두 원문이 한 번씩 있었다.
- 손으로 치는 다섯은 커밋의 pre-commit 으로 갈음한다.

## 인계 (커밋 뒤)

이 세션(지금 제목 `feature/09-widget-storage-and-reconnect`)이 커밋 e9ecae81 뒤에 인계 계기를 받았다(세션 컨텍스트 336,273 토큰, 문턱 200,000). 곁 세션이 아니고(`get_session` 의 `self` 에 `parentSessionId` 가 없다) 범위가 PR과 병합까지라 새 세션에 넘긴다. 이 절과 위 고친 것의 두 줄(인용의 따옴표를 뗐다)은 커밋하지 않았고, 새 세션이 이어 쓰고 커밋한다.

- 커밋 e9ecae81 의 pre-commit: run_checks 의 열(check-ticket, lint-imports, zizmor, check-instructions, check-type-escapes, pyright, pyright-linux, run-hooks, pytest, web-verify)이 모두 지났다. ruff 둘은 스테이지된 `.py` 가 없어 Skipped 였다(이 변경에 `.py` 가 없다). 변이 표 원문 검사(`mutate.py --staged`), 마크다운 표, 줄 구분 문자, 커밋 메시지 검사도 지났다.
- 같은 커밋의 인용 대조가 이 일지의 인용 둘(고친 것의 `msw_abort_order.mjs` 줄과 README 의 수 줄)을 경고했다. 둘 다 고치기 전의 글이라 저장소에 남지 않은 인용이어서 따옴표를 뗐다.
- 넘긴 지시문:

```
다음 작업: .scratch/web-widget/issues/09-widget-storage-and-reconnect.md. 위젯 저장과 재접속(web-widget 의 마지막 티켓)을 PR 직전 리뷰부터 PR과 병합까지 마친다
다음 단계: 구현
어디서: 새 세션. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고(그 스킬이 사람에게 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/web-widget/issues/09-widget-storage-and-reconnect.md
브랜치: feature/09-widget-storage-and-reconnect
모델: Opus 5.5 / xhigh
읽을 것: docs/journal/2026-10-26-01-widget-storage-and-reconnect.md 의 "셀프 리뷰" 절(특히 "PR 직전 리뷰에 밀 주장")과 "인계 (커밋 뒤)" 절
이어받을 상태: 인계: 커밋 뒤. 커밋 e9ecae81 까지 구현, 셀프 리뷰와 그 반영(TDD 고침 하나, 시험 넷, 변이 일곱), 티켓 done, plan.md 의 기능 done 을 마쳤다. 일지의 인계 절과 인용 둘의 따옴표 떼기는 커밋하지 않은 채 작업 트리에 있다. 남은 단계는 차례로 ① 스태시 `09-widget-storage-before-main-merge-1a02f1d4`(759a2eae64cb5b2285fdcd30c3efbdc29b07fa11, main 을 합치기 전에 떠 둔 사본이고 합친 결과는 e9ecae81 에 들었다)를 이름표로 stash@{n}을 다시 찾아 drop ② PR 직전 리뷰(CodeRabbit CLI, 안 되면 /security-review 와 bug-perf-review). 브리프에 일지의 "PR 직전 리뷰에 밀 주장"을 넣고, 반영을 커밋 ③ 변이 실행: storage_mutations 전체(13), 원문을 고친 변이(conversation 7·8·23, widget_app 17, failures 8, approval 5·7·8·9·10), widget_e2e 7·8. 그 결과로 probes/README 의 "잰 판" 칸을 채운다 ④ 셀프 리뷰가 위젯을 고친 판에서 위젯 e2e, -m llm_widget, pnpm -C web visual:widget 을 다시 돈다(일지의 검사 절은 셀프 리뷰 전의 판이다) ⑤ 일지의 검사 절, 회고(retro), ## 다음(정리 절의 tidy_checkouts 가 접힌 web/apps/widget/public/ 때문에 병합된 워크트리를 남기는 버그 포함) ⑥ 푸시, PR(본문에 사진 7장이 새로 서고 FailureAlert 의 4장이 바뀌었다고 적는다), ccd_pr get_status·bind_pr, 봇 회차, "워크트리에서 병합할 때"로 병합, next-session. 일지: docs/journal/2026-10-26-01-widget-storage-and-reconnect.md
확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다
이번 요청 범위: PR과 병합까지
```

- 제목을 `feature/09-widget-storage-and-reconnect (인계함)` 으로 바꿨다. 띄운 백그라운드 작업은 남지 않았다(커밋이 끝났다). 워크트리 잠금은 이미 풀려 있었다(`is not locked`).
- open-session을 부른다 2026-10-26T02:59:38Z

## PR 직전 리뷰 (셋째 세션)

스태시 `09-widget-storage-before-main-merge-1a02f1d4` 를 이름표로 다시 찾아 지웠다. 브랜치는 이미 origin/main(8ad99ca6) 위라 다시 합칠 것이 없었다. CodeRabbit CLI 는 로그인은 됐지만 좌석이 없었다(`coderabbit auth status` 의 `Seat : not assigned`, Free). 그래서 보안은 `/security-review`, 버그·성능은 `bug-perf-review` 서브에이전트가 봤고, 브리프에 위 "PR 직전 리뷰에 밀 주장" 여덟을 넣었다.

- `/security-review`: 발견이 없었다. `bundleOf` 는 무엇을 그리고 지울지만 가르고 권한을 주지 않는다, 토큰은 저장하지 않는다, HTML 로 그리는 글이 없다, 실행의 주인은 서버가 `read_own_run` 으로 본다.
- `bug-perf-review`: Critical·Major 가 없었다. 밀 주장 여덟은 모두 맞았다.

고친 것:

- 구독의 429 가 `Retry-After: 0` 이면 기다림 없이 곧바로 다시 구독해 되풀이했다(타당). 서버는 1 이상만 보내지만 사이의 프록시가 0 을 보낼 수 있다. 시험을 먼저 써서 빨강(간격이 `[ +0 ]`)을 본 뒤, 기다림의 바닥을 재접속의 첫 간격(1초)으로 두었다.
- `drivers.ts` 의 `sleep` 이 시간이 다 돼 깨어날 때 `abort` 리스너를 떼지 않았다(타당). 다시 잇는 동안 30초마다 잠들어 일이 끝날 때까지 리스너가 쌓인다. 떼게 고쳤다. 화면에서 보이는 차이가 없어 시험은 없고, 기존 시험이 그대로 지났다.
- 프로브 README 의 저장 표 행이 커밋 전 작업 트리에서 판정한 변이 여섯을 "잰 판"으로 들었다(타당). 아래 변이 실행 뒤에 다시 쓴다.

남긴 것(보류):

- 응답 머리를 기다리는 동안에는 45초 무응답의 끊기가 걸리지 않는다. 명세의 45초가 머리를 기다리는 시간도 덮는지 정해야 하고, 덮으면 시작·이어 가기의 길도 함께 바뀐다. PR 본문의 남긴 위험에 적는다.
- 처리하지 못한 거절의 셈(`errors`)이 붙어서 새 항목을 받을 때만 처음으로 돌아간다. 붙은 구독에서 처음으로 돌리는 기존 시험과 같은 뜻이고, 명세는 "세 번"이 이어진 세 번인지 정하지 않았다.
- 용량이 찬 저장소에 쓰기를 세 단계로 되풀이한다. 실제 크기에서는 드물어 성능 문제로 보지 않았다.

## 진단: 저장 시험의 플레이크 (셋째 세션)

PR 직전 리뷰의 반영을 돌리다 `WidgetStorage.test.tsx` 의 "판과 모양" 사례가 가끔 빨갰다. 새로 고친 뒤 WELCOME 대신 앞 대화가 그려졌다. diagnosing-bugs 로 좁혔다. 사례를 200회 되풀이하는 임시 탐침을 node 바쁜 루프 열 개의 부하 아래 돌려 재현률을 올렸고, 같은 탐침을 고치기 전 판(e9ecae81 의 임시 워크트리)에서 대조로 돌렸다. 두 판 모두 200회 가운데 1회 빨갰다. 이 세션의 고침 탓이 아니라 앞부터 있던 경합이다. 빨간 회차마다 시험이 읽은 저장에 출력이 아직 없었고, 걷기(`cleanup`)가 저장을 다시 썼다. 지난 회차는 모두 그 반대였다.

까닭: 저장은 그린 뒤의 효과(`useEffect`)가 쓴다. `findOutput` 은 출력이 DOM 에 선 순간 풀려, 그 커밋의 저장이 밀린 채 시험이 저장을 읽고 고친다. 그 뒤 `reload` 의 걷기가 밀린 효과를 비우며 멀쩡한 저장으로 시험이 고친 값을 덮는다. 고침은 시험 쪽이다. `testing/widget.tsx` 에 저장이 조건을 지날 때까지 기다리는 `untilSaved` 를 두고, 저장을 읽거나 저장이 비었는지 보는 자리 다섯(`WidgetStorage.test.tsx` 넷, `WidgetReconnect.test.tsx` 하나)에 걸었다. 같은 부하에서 같은 고친 판을 기다림만 켜고 끄고 400회씩 돌리자, 기다리지 않으면 7회 빨갰고 기다리면 400회 모두 지났다. 탐침과 `[DEBUG-st09]` 표지는 지웠다(grep 0).

다시 돌린 것:

- `pnpm -C web exec vitest run --project widget-pages`: 파일 8, 시험 197 이 모두 통과했다.
- `pnpm -C web/apps/widget exec tsc --noEmit -p .`, `pnpm -C web exec eslint apps/widget/components/pages apps/widget/lib apps/widget/testing`, 같은 폴더의 `prettier --check`: 모두 지났다.
- `PYTHONUTF8=1 uv run python tools/mutate.py --check` 로 web-widget 표 여섯(storage, conversation, widget_app, failures, approval, widget_e2e): 모두 원문이 한 번씩 있었다.

## 검사 (셋째 세션, PR 직전 리뷰 반영 뒤)

커밋 3b96b7bb 에서 돌렸다.

- 커밋 3b96b7bb 의 pre-commit: run_checks 의 열(zizmor, check-ticket, lint-imports, check-instructions, check-type-escapes, pyright-linux, pyright, run-hooks, pytest, web-verify)과 변이 표 원문 검사, 마크다운 표, 줄 구분 문자, 인용 대조, 커밋 메시지 검사가 지났다. ruff 둘은 스테이지된 `.py` 가 없어 Skipped 였고, 손으로 친 `uv run ruff check .`·`uv run ruff format --check .` 가 지났다.
- `pnpm -C web/apps/widget exec playwright test`: 15 passed(47.0초). 이번에는 플레이크가 나지 않았다.
- `uv run --env-file ../../../.env pytest -m llm_widget -q`: 1 passed. 토큰 6,555(입력 6,483, 출력 72), 트레이스 1, 모델 호출 2.
- `pnpm -C web visual:widget`(Docker): 42 passed.
- 푸시하고 PR #387 을 열었다. 변이는 PR 을 연 뒤에도 임시 워크트리에서 돌았다(아래 "변이").
- PR #387 의 첫 CI(헤드 3b96b7b): CodeRabbit, claude-review, e2e, e2e-widget, python, ticket, verify, visual, web 이 모두 SUCCESS 였다. CodeRabbit 은 "manual review required for this OSS repository" 로 리뷰를 건너뛰었다.

## 변이 (셋째 세션)

지시문은 storage 전체와 원문을 고친 변이(conversation 7·8·23, widget_app 17, failures 8, approval 5·7·8·9·10), widget_e2e 7·8 을 골랐다. 이 브랜치가 conversation·failures·approval 의 시험 파일 자체를 고쳤으므로(풀 수 있는 토큰, 시험 행 하나를 재접속 시험으로 옮김) `tools/mutate.py` 독스트링의 "시험을 고치거나 지웠으면 전체"를 따라 그 셋과 widget_e2e(e2e 의 사이트 페이지와 픽스처 플러그인을 고쳤다)를 전체로 넓혔다. widget_app 은 그 시험이 바뀌지 않아 17 만 돌렸다. element 표는 사이트 페이지의 변경이 `?sub=` 를 줄 때만 달라지는 덧붙임이라 돌리지 않았다. 모두 커밋 3b96b7bb 를 임시 워크트리(`git worktree add --detach`)에서 그 워크트리의 도구로 돌렸다.

- storage 13, failures 15, approval 16, widget_app 17, widget_e2e 8: 도구가 모두 기대대로로 판정했다.
- conversation: 26 의 기준선이 고를 시험이 없어 오류였고, 표 전체가 변이를 넣지 않고 멈췄다. 그 변이가 고르던 "시작 항목 뒤에 결말 없이" 시험은 이 티켓이 재접속 시험으로 옮겼다. 지시문이 고른 번호만 돌렸다면 보지 못했을 썩음이다. 26 이 `ended` 의 남은 갈래("시작 항목 전에 끝난 스트림")를 겨누게 고쳤다. 고르기 전에 변이를 이 워크트리에 손으로 넣고 `-t "시작 항목 전에 끝난 스트림"` 의 실패 머리에 표지 `Unable to find role="alert"` 가 있는 것을 본 뒤 되돌렸다. 고친 표(작업 트리 판)를 임시 워크트리의 도구로 전체 돌리니 26 가운데 24 가 기대대로였다.
- 어긋난 1·3(토큰 손잡이의 보낸 창, `id`)은 고른 단언이 빨갛지만 표지 `Bearer from-other-window`·`Bearer for-other-request` 가 없었다. 변이를 손으로 넣어 실패 출력을 보니 받은 값 줄이 `Bearer <머리>.<페이로드>.from-other-window` 였다. 이 티켓이 시험의 토큰을 서명 자리가 이름인 JWT 꼴로 바꿔서다. 표지를 `.from-other-window",`·`.for-other-request",` 로 바꾸고(첫 결과를 본 뒤 바꾼 기준이다) 1·3 을 다시 돌려 도구가 둘 모두 기대대로로 판정했다.
- 프로브 README 의 여섯 행(storage, widget_e2e, failures, approval, widget_app, conversation)의 "잰 판" 칸에 위를 적었다. 임시 워크트리는 지웠다.

## 회고

셋째 세션이 이 일지와 그 세션을 원천으로 돌렸다. 후보 열, 승인 넷(모두 대기열, 이 세션에서 반영한 것 없음), 기각 여섯, 넘김 0. 넘긴 것이 없어 사용자에게 묻지 않았다.

승인(심각도 순):

1. **`tools/tidy_checkouts.py` 가 접힌 `web/apps/widget/public/` 때문에 병합된 위젯 워크트리를 남긴다**(위 "정리"의 두 판에서 여덟과 아홉). 사건이 있고, 고칠 자리가 도구이며(층), PR 하나로 되돌린다. 도구의 버그라 고침이지만 이 PR 의 범위(위젯)가 아니라 대기열 464 에 회차를 더했다(3회차). `.gitignore` 의 `web/apps/widget/public/element.js`(티켓 10)도 `RECREATABLE_PATHS` 에 없어, 접힌 폴더를 풀어도 element.js 를 빌드한 워크트리는 남는다.
2. **위젯 페이지 시험이 출력을 찾은 직후 `sessionStorage` 를 읽어 저장 효과보다 앞섰다**(위 "진단: 저장 시험의 플레이크"). 사건이 있고, 같은 꼴을 막을 수 있는 가장 높은 층은 린트 규칙이며, PR 하나로 되돌린다. 새 검사라 더하는 것이고 첫 번째라 대기열 472 새 행(1회차)에 두었다. 시험 다섯 자리의 고침은 이 PR 에 실렸다. 대기열 306(부하에서만 빨간 시간 시험)의 종류는 아니다. 시계가 아니라 시험이 효과를 기다리지 않은 논리의 경합이고, 기다리면 부하에서도 400회 모두 지났다.
3. **`tools/mutate.py` 의 "시험을 고치거나 지웠으면 전체"가 표 넷 전체(conversation 26, failures 15, approval 16, widget_e2e 8)를 요구했다**(위 "변이"). 썩은 셋(26 의 기준선, 1·3 의 표지)은 모두 고친 시험 파일을 쓰는 변이라, 그 행이 처방한 `--since` 의 고친 시험 파일 고르기로도 잡힌다. 열린 행이 이미 처방한 사건이라 회차로 세어 대기열 418 에 더했다(2회차).
4. **`tools/mutate.py` 의 `_details` 가 끝 10줄만 보여, 표지가 없는 1·3 의 실패 머리를 보려고 변이를 손으로 넣었다**(위 "변이"). 열린 행이 처방한 사건이라 대기열 455 에 더했다(2회차).

기각:

- 워크트리 가드가 리다이렉트와 이스케이프한 공백이 든 vitest 명령을 거부했다. 앱 가드가 그 자리에서 막았고, `CLAUDE.md` 환경 함정의 길(파일로 쓰고 경로를 넘긴다)로 바로 풀었다.
- 스크래치패드로 옮기는 `cd` 를 훅이 막았다. 훅이 그 자리에서 막았다.
- 8.8MB 세션 기록에 앞뒤 600자를 뽑는 grep 이 2분 제한을 넘겼다. Bash 의 시간 제한이 그 자리에서 멈췄고, 한 번 쓴 조회라 고칠 층이 없다.
- `mutate.py --help` 가 없는 옵션이었고 표 없는 `--check` 가 독스트링을 찍었다. 도구가 그 자리에서 쓰는 법을 알렸다.
- Edit 의 `Found 3 matches`(대기열 파일). 도구가 그 자리에서 알렸다.
- `@coderabbitai review` 를 남기기 전에 띄운 `tools/wait_ci.py` 가 종료 4로 끝났다. `next-session` 순서 1의 2가 정한 순서를 어긴 것이지만, 리뷰가 아니라 도구가 그 자리에서 할 일을 끝 줄로 알렸다.

만료: `tools/queue_open_rows.py` 와 `--ref origin/main` 두 출력에 모두 든 168 을 닫았다.

## 다음

- 이 PR(#387)이 병합되면 web-widget 은 닫힌다. 다음 프론티어는 `.scratch/plan.md` 가 원천이다.
- 대기열 464 가 3회차라 `next-session` 결정표의 하네스 chore 배치 조건에 닿았다. 위 회고 1의 두 가지(접힌 `public/` 와 `RECREATABLE_PATHS` 에 없는 `public/element.js`)를 함께 고쳐야, 위젯 워크트리 아홉(위 "정리")이 다음 정리에서 지워진다.
- PR #387 의 남긴 위험 둘은 명세가 정하지 않은 자리다. 45초 무응답이 응답 머리를 기다리는 시간도 덮는지(덮으면 시작·이어 가기의 길도 바뀐다), 처리하지 못한 거절 "세 번"이 이어진 세 번인지(지금은 붙어서 새 항목을 받을 때만 처음으로 돌아간다). 정하려면 명세를 고치는 사용자 승인이 먼저다.
- 주 체크아웃 미갱신: 루트는 main. 이 세션은 워크트리에서 병합하므로 당기기와 병합된 워크트리 지우기는 다음 새 세션의 `tidy-checkouts` 가 한다.
