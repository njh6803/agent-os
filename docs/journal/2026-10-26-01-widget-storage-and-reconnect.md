# 2026-10-26 (01) 위젯이 대화를 저장하고 새로 고친 뒤와 끊긴 뒤 같은 실행에 다시 붙는다 (web-widget 09)

## 사용자 프롬프트

> 사용자: /implement .scratch/web-widget/issues/09-widget-storage-and-reconnect.md (next-session 지시문. 새 세션이고 tidy-checkouts 를 먼저 돌고 EnterWorktree(09-widget-storage-and-reconnect)로 들어간다. 브랜치 feature/09-widget-storage-and-reconnect, 범위는 PR과 병합까지. 읽을 것은 일지 2026-10-25-01 의 "다음". 이어받을 상태는 PR #385 셋째 회차 claude-review 가 보류한 Minor·Nit 셋과 "다음" 1(골격 모으기). 티켓 10(PR #386)이 `api/runs/index.ts`·`WidgetPage.tsx`·`WidgetScreen.tsx`·`useConversation.ts` 를 함께 고쳐 글자 충돌이 날 수 있다)

첫 세션은 2026-10-25 에 위 지시문으로 시작해 구현과 main 합치기까지 하고 계정의 주간 한도에 걸려 멈췄다. 2026-10-26 에 다른 계정의 새 세션이 이어받았다.

> 사용자: feature/09-widget-storage-and-reconnect 다른 계정에서 작업하던거 이어받아서 진행할 수 있어?

## 정리(tidy-checkouts)

주 체크아웃을 `origin/main` 으로 당겼다(1ef75a12 → cb6d9c39). 지운 것은 없다. 병합된 위젯 워크트리 여덟이 접힌 `web/apps/widget/public/` 때문에 남았고(tidy_checkouts 의 버그, 아래 "다음"), pwsh 가 쥔 워크트리 셋과 python(pid 41176)이 쥔 휴지통의 `worktree-overrides-pc-check~~.venv` 가 남았다.

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
- `msw_abort_order.mjs` 머리의 "그 셋 가운데 하나라도 빼면 초록이었다"는 셋이 무엇인지 없었고 README 와도 달랐다(표준). README 와 같은 사실(둘은 빼면 초록, `signal` 은 빼도 빨강, 손으로 본 것)로 고쳤다.
- 프로브 README 의 "`widget-pages` 전체(174개)"가 어느 판의 수인지 없었다(표준). main 을 합치기 전의 판이라고 적었다.
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
