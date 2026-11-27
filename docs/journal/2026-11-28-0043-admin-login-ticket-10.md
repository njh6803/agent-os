# 2026-11-28 admin-login 티켓 10: 대화 목록과 대화를 읽는 화면, 실행 패널, 도는 실행 이어 보기

브랜치 `feature/10-chat-read-screens-list-panel-and-polling`, 티켓 `.scratch/admin-login/issues/10-chat-read-screens-list-panel-and-polling.md`. 새 세션(Sonnet 5.5 / high)이 워크트리 `10-chat-read-screens-list-panel-and-polling`에서 구현했다. 이 세션의 제목은 `feature/10-chat-read-screens-list-panel-and-polling`이었고 `(인계함)`으로 바꾼다.

## 사용자 프롬프트

붙여 넣은 `next-session` 지시문 하나뿐이다(원문은 길어 요지만 옮긴다).

> 사용자: `.claude/skills/implement/SKILL.md`를 읽어 그대로 따른다. 인자는 `.scratch/admin-login/issues/10-chat-read-screens-list-panel-and-polling.md`다. 다음 작업은 대화 목록(`/chat`)과 대화를 읽는 화면, 실행 패널, 도는 실행 이어 보기를 짓는 것이다. 어디서는 새 세션(나란히 여는 3 중 1, 나머지는 티켓 12와 13)이고 브랜치는 `feature/10-chat-read-screens-list-panel-and-polling`, 모델은 Sonnet 5.5 / high다. 읽을 것은 일지 `docs/journal/2026-11-27-1656-admin-login-ticket-09.md`의 "다음" 절이다. 12도 탐색에 항목("계정")을 더하고 관리 화면 사진 정답을 늘리므로 나중에 병합하는 쪽이 충돌을 푼다. 09가 `useMe().data`에 읽을 자리만 열어 둔 `run_timeout_seconds`는 이 티켓이 pages에서 읽어 넘긴다. 이번 요청 범위는 PR과 병합까지다. 병합은 워크트리 사본의 `merge.md`의 "워크트리에서 병합할 때"를 따른다.

사용자의 정정이나 피드백은 없었다. 중간의 `[SYSTEM NOTIFICATION]`(백그라운드 작업 끝 알림)은 사용자 입력이 아니다.

## 한 것(커밋하지 않았다. 변경은 모두 스테이지했다: 120개 파일, 사진 정답 포함)

- 읽는 쪽: `api/conversation/turns.ts`(대화 거슬러 읽기와 도는 실행의 `pollInterval`, 시험 `turns.test.ts` 26건), `api/conversation/index.ts`, `api/conversations/index.ts`, `hooks/queries/conversation`(`useEndRun`, `useEarlierRuns`), `hooks/queries/conversations`, `hooks/useRunQuery.ts`(`?run=` 질의).
- 화면: organisms `ConversationList`, `Conversation`, `RunPanel`, `StatusFilter`, molecules `localTime`, `principal`, pages `ConversationsPage`(시험 18건), `ConversationPage`(시험 48건), 라우트 `app/chat/page.tsx`, `app/chat/[runId]/page.tsx`. 탐색(`AdminNav`)에 `{section:"chat", href:"/chat", icon:"message-square", label:"대화"}`를 플러그인 다음에 더했다. 옛 "실행" 항목과 `/runs`는 티켓 11이 걷을 때까지 남긴다.
- 보강: `ReadSection`, `ScreenHeader`, `TextLink`, `RunDetail`(`starter`를 내보냄), `RunList`, `RunDecision`(주체 판정을 `molecules/principal`의 `isEndUserPrincipal`로 옮김), `testing/events.ts`·`testing/network.ts`.
- 디자인 토큰: `web/packages/ui/src/styles/theme.css`에 `--spacing-panel: 480px;`을 더했다(패널 폭).
- 스토리: `ConversationList.stories.tsx`, `Conversation.stories.tsx`, `RunPanel.stories.tsx`. 사진 정답은 새로 `organisms-conversation--*`, `organisms-conversationlist--*`, `organisms-runpanel--*`(1280/320 × 라이트/다크)가 생겼고 `templates-adminframe--*` 16장이 탐색 항목이 늘어 바뀌었다.
- e2e: `e2e/chat.e2e.ts`(첫 실행과 이어 가기 실행을 API로 만든 뒤 `/chat`의 줄, `/chat/<끝 실행>`의 두 구역, "자세히"로 패널 열기와 닫기), 도우미 `e2e/channel.ts`(`startFinishedRun`, `continueRun`, `finishedOf`), `e2e/screen.ts` 주석.
- 규칙: `.claude/rules/web-admin.md`의 주기 읽기 줄에 "대화 화면의 끝 실행, 셋이다"를 더했다(규칙 파일을 고치기 전에 `writing-for-agents`를 불렀다).
- 변이 표 `.scratch/admin-login/probes/chat_read_mutations.toml`(변이 7개, 표지 `expect_output`은 실제 실패 줄의 문구로 채웠다).

## 이 세션이 정하거나 고친 것(일지에 남기고 PR 본문에도 쓸 것)

- 명세의 "다시 읽기" 버튼은 읽기 골격 `ReadSection`의 "새로 고침"으로 갈음했다.
- 큰 표와 카드의 갈래는 컨테이너 쿼리 `@split`(784px)이다. 명세의 768px(`wide`)과 다르다. 이유와 차이를 PR 본문에 적는다.
- `--spacing-panel` 토큰을 새로 더했다. 디자인 시스템 올리기 대상이 될 수 있어 "다음"에 적는다. `sync-design-system 확인`은 시작 때 돌려 `clean`(웹 편집 없음, 결정표 `continue`)이었다.
- 320px 폭의 패널 사진에서 아래에 대화가 비치는 것은 패널이 디자인(`ch-run.dc.html`)대로 `absolute right:0 width:480px`로 대화 열을 가리고, 전체 페이지 사진에서 `fixed inset-0`이 뷰포트 높이만 덮기 때문이다. PR 본문에 적는다.
- 사진에서 `stale` 대화의 320px 푸터에서 "자세히"가 한 글자씩 쪼개졌다. 푸터를 `flex-wrap`으로, 버튼을 `whitespace-nowrap`으로 고쳤다. 회귀 단언은 글자 폭이 아니라 계산 스타일(`whiteSpace`, `flexWrap`)로 건다. 스토리 시험 브라우저(Windows 로컬)와 사진 환경(Docker Linux)의 글꼴이 달라 `Range.getClientRects` 단언은 고치기 전에도 통과했기 때문이다.
- 앞 실행은 불변이라 `useEarlierRuns`는 포커스 재읽기를 끄고 "새로 고침"에서만 다시 읽는다.
- 도는 실행의 `refreshInterval`은 인라인 함수 꼴이다(`swr_poll` 프로브 1a·1b·4c). 알림 부품은 `isValidating`을 읽는다.
- 탐색 항목이 늘어 깨진 시험을 고쳤다: `SettingsPage.test.tsx`의 항목 기대, `AdminFrame.stories.tsx`의 항목 이름과 아이콘 개수(3→4), `e2e/screen.ts` 주석. 첫 `pnpm -C web verify`의 시험 실패 셋은 이것이었다.
- 타입 오류를 고쳤다: 시험의 에러 코드 `"internal"`은 계약의 `"internal_error"`다. `toolCalled` 도우미에 `extra` 매개변수를 더했다. 스토리 `PanelOpen`의 axe `aria-valid-attr-value`는 스토리가 `RunPanel`을 함께 그리게 해서 고쳤다.
- prettier 서식 12개 파일을 `prettier --write`로 맞췄다.

## 검증 결과(셀프 리뷰 전, 이 세션이 직접 친 명령의 결과)

- `pnpm -C web verify`: 탐색 시험을 고친 뒤 종료 코드 0(린트, 서식, 타입, 시험, `check:tsconfig`). 고치기 전에는 3건 실패(`Test Files 3 failed | 147 passed`, `Tests 3 failed | 3060 passed | 1 skipped`)였고 원인은 위와 같다.
- 관리 화면 e2e `pnpm -C web/apps/admin exec playwright test`: 첫 전체 실행은 13개 가운데 12개 통과, `decision.e2e.ts:12`("멈춘 실행을 승인하면 재개 스트림이 조각으로 붙고 …")가 5초 안에 `run_finished`를 보지 못해 실패했다(13.2초). 그 파일만 다시 쳐도 같게 실패(10.3초)했다. 시험 안에서 시간 창을 가진 시험이다. 실패한 시험의 `trace.zip`을 풀어 네트워크 줄을 `uv run python -I`로 뽑아 보니(손으로 본 것) 승인 요청(15:30:03) 뒤로 트레이스를 다시 읽는 `GET /api/traces/...` 요청이 없었고, 마지막 화면 그림(손으로 본 것)에서 승인 버튼은 누른 채(비활성)여서 재개 스트림이 5초 안에 끝나지 않은 것으로 읽었다. 이 PC는 그 직후 PowerShell로 본 값이 CPU 61%, node 프로세스 90개였다(손으로 본 것. 실패한 그 순간의 부하는 재지 않았다). 그래서 부하로 늦어진 것으로 본다(어림). `--repeat-each=3`으로 그 시험만 치니 3건 모두 통과(6.7~7.7초, 러너가 찍었다)했고, 전체를 다시 치니 종료 코드 0(전체 통과)이었다. 같은 시험이 부하에서 흔든 선례가 일지 `2026-10-20-20-only-pre-owner-damage-is-404.md`, `2026-10-23-50-widget-app-skeleton.md`, `2026-10-28-23-admin-adopt-design-system.md`에 있고, 대기열 306이 이 종류(부하 아래의 시간 창 시험)를 받아들여 닫았다. 이 티켓의 변경은 `useDecision`과 `RunPage`를 건드리지 않았다(`git status`와 `git diff`로 봤다). 같은 종류의 새 사례라 회차를 더하지 않고 일지에만 적는다.
- `pnpm -C web visual:admin`(비교만): 종료 코드 0. 사진 정답은 푸터 줄바꿈을 고친 뒤 `visual:admin:update`로 다시 만든 판이다.
- `uv run ruff check .`와 `uv run ruff format --check .`는 앞서 통과했다(이 일지 쓰기 전에 다시 치지 않았다).

## 인계(2026-11-28, 셀프 리뷰 직전)

이 세션은 구현과 위 검증까지 하고 컨텍스트가 인계 문턱(20만 토큰)을 넘어 `셀프 리뷰 직전` 경계에서 새 세션에 넘긴다. 커밋하지 않았고 변경은 모두 스테이지했다(`git add -A`, 120개 파일, 의도하지 않은 파일은 섞이지 않았다). 방금 `code-review` 스킬을 불렀지만 서브에이전트는 띄우지 않았다.

새 세션이 할 것(순서대로):

1. 셀프 리뷰: `/code-review`(고정점 `origin/dev`의 merge-base, 스테이지된 작업 트리)를 Skill 도구로 부르는 대신 Read로 `.claude/skills/code-review/SKILL.md`를 열어 따른다. 명세 축의 근거는 티켓과 `.scratch/admin-login/spec.md`다. Critical·Major를 고치고 고친 것이 화면 모양을 바꾸면 e2e와 사진을 다시 친다.
2. 변이 표 `.scratch/admin-login/probes/chat_read_mutations.toml`: 이 세션이 표를 쓰고 표지를 채웠지만 `uv run python tools/mutate.py --check`(원문 존재와 표지 모양)와 변이 7건의 실행 결과(기준선 초록, 변이마다 빨강)를 일지에 옮기기 전에 컨텍스트가 넘쳤다. 새 세션이 다시 쳐서 결과를 일지에 적는다. pre-commit의 `check-mutations`가 막으면 표의 `old`·`new`·`expect_output`을 실제 실패 줄에 맞춘다.
3. 티켓 파일의 체크박스를 채우고 Status를 `done`으로 바꾼다(티켓의 "시작 전" 항목 `sync-design-system 확인`은 했다. 결과는 `clean`이다). `uv run python tools/plan_table.py`를 돌려 같은 커밋에 싣는다.
4. `uv run python tools/run_checks.py`(백그라운드, 스테이지한 뒤)와 ruff 두 줄을 친다. `uv run python tools/sibling_overlap.py`와 `git branch --show-current`를 커밋 직전에 친다. 커밋은 `git commit -F`로, 끝에 `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`를 붙인다.
5. 이 일지를 마무리한다(이어서 쓴다): 위 "이 세션이 정하거나 고친 것"을 근거로 한 "셀프 리뷰" 절, 변이 표 결과, "다음". "다음"에 적을 것은 티켓 11 이어받기(보내기·이어 가기·승인 버튼을 더하고 옛 `/runs` 화면과 "실행" 탐색 항목을 걷는다), 12와 탐색·사진 정답 충돌(12가 탐색에 "계정"을 더하고 사진 정답을 늘리므로 나중에 병합하는 쪽이 푼다), `--spacing-panel`의 디자인 시스템 올리기 후속, 이 일지의 `decision.e2e.ts:12` 흔들림이다.
6. PR을 연다(제목에 느낌표 없음, 본문 끝에 `🤖 Generated with [Claude Code](https://claude.com/claude-code)`). 본문에 `@split` 784px 경계의 이유, "다시 읽기"를 "새로 고침"으로 갈음한 것, 320px 패널 사진 설명, 푸터 줄바꿈 수정과 계산 스타일 단언의 이유를 적는다. PR 직전에 `coderabbit-review` 서브에이전트(안 돌면 `bug-perf-review`)를 돌린다. PR을 연 뒤 `mcp__ccd_pr__get_status`와 `bind_pr`을 쓴다. 병합은 워크트리 사본의 `.claude/skills/next-session/merge.md`의 "워크트리에서 병합할 때"를 Read로 열어 따른다. 지시문을 낸다.

open-session을 부른다 2026-11-27T15:44:50Z

## 이어받은 세션: 셀프 리뷰(2026-11-28)

새 세션(Sonnet 5.5 / high)이 같은 워크트리를 이어받았다. 시작 때 제목을 브랜치 이름으로 바꿨다. 고정점은 `origin/dev`의 merge-base `a11fffed48fb38fd5c25ddc4eb20152cd42824f1`이다. 본 범위는 이 SHA 이후 커밋 0개, 스테이지된 120개 파일(사진 정답 PNG 포함, 소스 약 47개), 미추적 0개다. 표준 축은 sonnet·high, 명세 축은 세션 모델이다. 두 축 모두 Critical·Major는 없었다.

### 표준 축 보고와 판정

- 고침: `.claude/rules/web-admin.md` 주기 읽기 줄의 "셋이다"(같은 예외를 둘로 셈. ADR 0063 "주기 읽기의 예외" 절이 가리키는 것이 끝 실행이다). 이제 "대화 화면의 끝 실행(ADR 0063)과 플러그인 목록의 접속 확인, 둘이다". 명세 축도 같은 곳을 짚었다.
- 고침: `hooks/queries/conversations/index.ts` 머리 주석의 "예외는 대화 화면의 실행 하나뿐이다"(접속 확인이 반례). "대화 쪽의 주기 읽기는 대화 화면의 끝 실행뿐이다"로 좁혔다. 명세 535행의 문장을 옮긴 것이라 그 문장은 명세에서 대화 목록을 두고 한 말이다.
- 고침: `TextLink`의 `clip?: boolean`(갈래를 고르는 불리언 칸. `CODING_STANDARDS.md` 불리언 기준)을 `fit: "inline" | "clip"`으로. `Conversation.tsx`의 `last`와 `stale` 불리언 둘을 `Place`(`earlier`·`end`·`end-stale`) 하나로.
- 고침: 쓰이지 않던 `formatClockTime`(`localTime.ts`)을 지웠다(Speculative Generality).
- 고침: 닫힌 패널의 "자세히"가 없는 id를 `aria-controls`로 가리키던 것을 열린 때만 달았다(`AccountMenu`의 선례).
- 고침: 패널을 닫으면 열기 전에 포커스가 있던 "자세히"로 돌아오게 했다(시험 먼저: `ConversationPage.test.tsx`의 "자세히로 연 패널을 닫으면 포커스가 그 자세히 버튼으로 돌아온다", 고치기 전에 `document.activeElement`가 `body`여서 빨강이었다. `pnpm -C web exec vitest run --project pages apps/admin/components/pages/ConversationPage.test.tsx -t 포커스가`를 손으로 쳐서 봤다).
- 남김: `--spacing-panel`이 `.claude/rules/web-design.md`의 이름 있는 치수 열거(틀 `nav`·`nav-item`·`top-bar`)에 없다. 이 파일은 디자인 시스템 아티팩트 지침 문서로 올라가는 파일이라 `--spacing-panel`의 디자인 시스템 올리기와 함께 고친다("다음").
- 남김: 폭 768 미만에서 패널이 화면을 덮는데 `inert`나 포커스 가둠이 없다. 디자인(`ch-run.dc.html`)과 명세가 모달 동작을 요구하지 않았고 덮개도 두지 않는다고 정했다. 모달로 바꾸는 것은 사용자의 결정이라 후속 후보로 남긴다.
- 남김: `ConversationList`와 `RunList`가 `EmptyFiltered`·`HEAD_CELL`·`Field`·`SkeletonTable` 같은 모양을 되풀이하고, `Conversation.tsx`의 `BADGE`와 `StatusFilter.tsx`의 `BADGE`가 같은 배지를 잇는다. 티켓 11이 옛 `RunList`(`/runs`)를 걷으므로 그때 하나가 사라진다. 지금 뽑으면 걷을 코드를 위해 추상화를 더하는 셈이다.
- 남김: `CONTEXT.md`의 `교환` 피할 말에 있는 "턴"을 코드가 `Turn`·`turnOf`로 쓰고, `Outcome.kind: "running"`이 "실행 중" 피하기와 어긋난다는 지적. 대화 화면의 한 실행을 가리키는 코드 이름이라 용어집 결정이 먼저다. retro 후보로 올린다.
- 남김: `api/conversation`과 `api/conversations`의 한 글자 차이, 컴포넌트와 타입의 같은 이름 `Conversation`, 두 `ConversationProps`는 이름 취향의 Nit이다.
- 표준 축 서브에이전트가 확인하고 문제 없다고 보고함(코드와 문서를 읽은 것이고 이 세션이 다시 재지는 않았다): `swr_poll` 결과 1a·1b·1c·4c 인용은 그 README의 표와 맞고 `READ_CAP`=100도 맞다. 정지 조건(결말, 제한 시간, 일시정지)과 정리, 가려짐·실패 시험도 맞다.
- 변이 표가 덮지 않던 `hasOutcome`의 일시정지 갈래와 "앞의 일시정지가 남은 재개 실행"을 변이 둘로 표에 더했다(아래 변이 결과).

### 명세 축 보고와 판정

- 읽는 쪽 전부(간격 함수, 멈출 때, 거슬러 읽기 100개와 끊김, `?run=` 패널, 표지 줄, 요청한 계정 칸의 "최종 사용자")는 명세와 맞다고 보고했다.
- (c) 틀린 문장 셋: 위의 규칙 줄과 훅 주석은 고쳤고, `theme.css`의 "관리 화면의 틀" 묶음 주석 한가운데 `--spacing-panel`이 끼어 묶음 설명이 틀린 것은 `--spacing-panel`을 묶음 밖으로 빼 제 주석을 달아 고쳤다.
- (a) 사진은 375px가 아니라 1280/320으로 정답이 있다. 관리 화면 사진 비교의 폭 둘이 1280과 320이라(`web-design.md`) 375px 프로젝트를 새로 만들지 않았다. 320px가 카드 갈래의 사진이고 컨테이너 쿼리 `@split`(784px)의 경계 근처는 jsdom이 컨테이너 쿼리를 재지 못해 시험이 없다. PR 본문에 적는다.
- (a) 카드의 `clip` 줄바꿈 걱정: 첫 요청 링크는 `block max-w-form truncate`다(`TextLink.tsx`를 읽은 것). 그래서 붙여 쓴 긴 글도 말줄임표로 줄 것으로 본다(화면에서 보지 않았다, 어림). 보고의 우려는 `truncate`를 놓친 것으로 읽었다.
- (b) 패널 여닫기를 `replaceState`로 해 뒤로 가기가 목록으로 가는 것: 코드 주석이 근거를 적었고 변이 표의 한 줄("패널을 열 때 방문 기록을 늘린다")이 지킨다. 명세는 패널의 방문 기록을 말하지 않았다. PR 본문에 결정으로 적는다.
- (b) 앞 실행에 "이 실행은 결말 없이 끝났다"를 보이는 것: 명세에 문구는 없지만 결말 없는 앞 실행이 빈 칸으로 남지 않게 한 것이다. PR 본문에 적는다.
- 의도한 차이 셋("새로 고침", `@split` 784px, `--spacing-panel`)은 타당하다고 판정했다. 뷰포트 768~1040px에서 명세의 표 대신 카드가 서는 폭이 명세 592행의 "768px 미만만 카드"보다 넓다는 점은 PR 본문에 적는다.

### 고친 뒤 다시 돌린 것(이 세션이 직접 친 명령의 결과)

- `uv run python tools/mutate.py --check .scratch/admin-login/probes/chat_read_mutations.toml`: 변이 7개(그때) 모두 원문이 한 번씩 있다고 나왔다. 그 뒤 변이 둘(8: 일시정지가 결말로 세어지지 않는다, 9: 앞의 일시정지가 남은 재개 실행을 결말로 센다)을 표에 더했다.
- `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/admin-login/probes/chat_read_mutations.toml`(셀프 리뷰 수정 뒤): 기준선 9건 모두 초록, 변이 9건 모두 "기대 빨강, 결과 빨강", 마지막 줄 "변이 9 모두 기대대로", 종료 코드 0. 실행 뒤 `git status`로 소스가 원상 복구된 것을 봤다. 알림 하나(고르지 않은 전체 실행인데 커밋하지 않은 변경이 있다)는 막지 않는 알림이다.
- `pnpm -C web verify`: 첫 판은 새로 만든 `placeOf(isEnd: boolean, stale: boolean)`을 불리언 매개변수 기준(eslint `no-restricted-syntax`)이 막아 빨강이었고, 이름 붙인 옵션 객체로 고쳤다. 둘째 판은 prettier가 그 파일을 막아 `prettier --write`로 맞췄다. 셋째 판은 종료 코드 0.
- `uv run ruff check .`는 `All checks passed!`, `uv run ruff format --check .`는 `2710 files already formatted`.
- `uv run python tools/run_checks.py`(스테이지 뒤): 마지막 줄까지 모두 `Passed`(check-notes, check-ticket, lint-imports, zizmor, check-instructions, check-type-escapes, pyright 둘, run-hooks, web-verify 626.6초, pytest 646.5초), 종료 코드 0.
- 관리 화면 e2e `pnpm -C web/apps/admin exec playwright test`: `13 passed (1.2m)`. 앞 세션이 본 `decision.e2e.ts:12` 흔들림은 이번 판에서 나지 않았다(부하가 덜한 때였는지는 재지 않았다).
- 관리 화면 사진 비교 `pnpm -C web visual:admin`: `140 passed (7.7m)`. 정답 사진은 이 세션이 바꾸지 않았다(`git status`에 스테이지된 것 말고 바뀐 사진이 없다).
- 카나리아(`web-admin.md`를 원천으로 든 명세 둘): `uv run python tools/canary.py --preflight`로 둘 다 통과한 뒤 `claude -p`(2.1.325)로 돌려 둘 다 통과 4·실패 0·"없음" 섞임 0이었다. 실험군은 고친 문장을 글자 그대로 옮겼고 대조군은 "없음"이었다(`web_admin_periodic_read.toml`의 기대 문장은 "둘이다" 문장으로 바꿨다). 두 명세의 `# 최신 결과:` 줄을 고쳤다.
- 첫 커밋 시도: pre-commit이 `check-mutations`에서 막았다(종료 코드 1, 나머지 훅은 모두 `Passed`). 앞 세션이 옮기거나 고친 소스를 겨누던 옛 변이 표 4개(`admin-style/probes/frame_common_states_mutations.toml`, `plugin_screens_mutations.toml`, `run_list_mutations.toml`, `end-user-channel/probes/admin_hides_decision_mutations.toml`)의 원문 7건이 0번 있었다. 고친 것: `ReadSection.tsx`는 들여쓰기가 바뀌어 원문의 들여쓰기를, `TextLink.tsx`는 `inline-flex min-h-6 items-center`가 `${FIT_CLASS[fit]} min-h-6`가 되어 그 꼴을, `ScreenHeader.tsx`는 `</h1>`이 `</Heading>`이 되어 그것을 맞췄고, `RunList.tsx`의 `hourCycle`은 `molecules/localTime.ts`로, `RunDecision.tsx`의 구분자 판정은 `molecules/principal.ts`(`PRINCIPAL_SEPARATOR`)와 `isEndUserPrincipal` 호출로 옮겨져 변이의 `file`과 `old`를 새 자리로 바꿨다. 그 7건을 표마다 번호로 돌려(`PYTHONUTF8=1 uv run python tools/mutate.py <표> <번호…>`) 기준선 초록, 변이 7건 모두 "기대 빨강, 결과 빨강"이었고 네 표 모두 "모두 기대대로"로 끝났다(손으로 쳐서 봤다). 표를 고치자 `end-user-channel/probes/admin_hides_decision_mutations.toml`의 두 변이에 옛부터 없던 `expect_output`(대기열 350)이 걸려, 변이를 손으로 넣어 실패 출력을 본 뒤(손으로 쳤다) 표지를 적었다: 변이 1은 `</section> to be null`(첫 단언의 실패 줄 `expected <section …(2)>…(1)</section> to be null`), 변이 2는 `Unable to find role="region" and name "결정"`. 표지를 단 두 변이를 다시 돌려 둘 다 기대 빨강이었고 `mutate.py --staged`는 "문제 0"이었다.
- 둘째 커밋 시도: pre-commit의 `parallel-checks`가 pytest에서 `3 failed, 8896 passed ... in 1095.14s`로 빨갰다(앞선 `run_checks.py`의 pytest는 646.5초였다). 실패는 모두 `tests/channel/cli/test_interrupt.py`의 "Ctrl+C 를 누른 자식이 30초 안에 끝나지 않았다"였다. 이 커밋의 변경은 `.scratch`와 문서뿐이라 Python은 달라지지 않았다(`git diff`로 본 것). 그 파일만 `uv run pytest -q tests/channel/cli/test_interrupt.py`로 다시 치니 `6 passed in 140.35s`였다. 이 PC에서 다른 세션이 함께 돌아 느렸다고 어림한다(부하는 재지 않았다). 대기열 306이 받아들여 닫은 종류(부하 아래의 시간 창 시험)의 새 사례라 회차는 더하지 않는다.
- 스킬이 정한 대로, 고쳐서 새로 쓴 사실 문장(PR 직전 리뷰에 밀 주장): (1) "주기 읽기의 예외는 대화 화면의 끝 실행(ADR 0063)과 플러그인 목록의 접속 확인, 둘이다"(`web-admin.md`) (2) "대화 쪽의 주기 읽기는 대화 화면의 끝 실행뿐이다, ADR 0063"(`hooks/queries/conversations/index.ts`) (3) "닫히면 열기 전에 포커스가 있던 곳("자세히")으로 돌아온다"(`RunPanel.tsx` 독스트링) (4) `Place` 타입의 설명: 끝 실행이 아니면 `earlier`, 끝 실행이면 `end`, 끝 실행인데 멈출 때까지 결말이 없으면 `end-stale`(`Conversation.tsx`).

## 회고

후보 5개를 냈고 판정은 승인 0, 넘김 0, 기각 5다. 대기열에 새로 쓴 항목은 없다. 근거는 이 일지의 앞 절들이다.

- 기각 5, 첫 커밋 시도가 pre-commit `check-mutations`에 막힌 것. 앞 세션이 옮기고 고친 소스(`ReadSection`·`TextLink`·`ScreenHeader`·`RunList`·`RunDecision`)를 겨누던 옛 변이 표 4개의 원문 7건이 어긋났다(`implement`의 "코드를 옮기거나 고쳤으면 그 코드를 겨누던 변이 파일을 `--check`로 본다"를 두 세션 모두 지나쳤다). 이미 있는 훅(`mutate.py --staged`)이 커밋 앞에서 막고 손실 없이 고쳤다. 이미 있는 검사가 막은 것이라 기각이다.

- 기각 1, 앞 세션이 쓴 규칙 줄의 "셋이다"(같은 예외를 둘로 센 닫힌 주장). 사건은 있었지만 `code-review`의 주장 검증 1(닫힌 주장의 반례)이 두 축 모두에서 이것을 잡았다. 리뷰가 잡도록 둔 기준을 어겨 리뷰가 잡은 사건이라 회차로 세지 않고(4단계), 검사로 옮길 수 있는 꼴(문장의 수 세기)도 아니다.
- 기각 2, 새로 만든 `placeOf(isEnd: boolean, stale: boolean)`을 불리언 매개변수 기준이 막은 것. `web/eslint.config.mjs`의 `no-restricted-syntax`가 그 자리에서 막아 고쳤다. 이미 있는 검사가 막은 것이다.
- 기각 3, `TextLink`의 `clip?: boolean`과 `last`·`stale` 같은 인터페이스의 불리언 칸. `CODING_STANDARDS.md`가 "린터가 보지 못한다"고 적은 자리를 표준 축 리뷰가 잡았다. 리뷰가 제 몫을 한 것이고 React의 `disabled` 같은 정당한 불리언 속성이 많아 린터로 올리면 거짓 양성이 크다(원칙: 거짓 양성이 많은 규칙을 하드 게이트로 만들지 않는다).
- 기각 4, 복합 git 명령(`git fetch …; git merge-base …`)을 앱의 워크트리 가드가 한 번 거부한 것. `CLAUDE.md` 환경 함정이 이미 "명령은 하나씩 치고"라고 적었고 가드가 그 자리에서 막았다. 하나씩 쳐서 지나갔고 손실은 없었다.
- 지켜본 것: 앞 세션이 `web-admin.md`의 주기 읽기 줄을 고치고도 `sibling_overlap`을 커밋 직전에 돌리기 전이라 카나리아 알림을 보지 못했다. 알림은 이 세션이 `sibling_overlap`을 돌려 받았고 카나리아 둘을 돌려 닫았다. 인계가 커밋 전에 끊긴 사건이고 지침(`CLAUDE.md`의 커밋 전 `sibling_overlap`)이 이미 그 자리를 덮는다. 같은 일이 되풀이되면 인계 지침에 카나리아 확인을 더할지 본다(회차로 세지 않았다).
- 대기열 만료: `uv run python tools/queue_open_rows.py`와 `--ref origin/dev` 두 출력에 모두 든 6개(`answer-estimate-before-reading-adr`, `measure-word-misses-adnominal-form`, `mutation-table-checked-late`, `probe-readme-run-claim-without-actor`, `raw-replacement-char-in-tracked-text`, `ui-design-abandoned-prompt-state`)의 상태를 `만료 2026-11-28 (ADR 0036)`로 닫았다. 승인 줄의 가장 늦은 날짜가 모두 2026-11-13이었다(도구 출력). 그 가운데 `mutation-table-checked-late`는 같은 날 티켓 12(#659)가 둘째 승인으로 다시 열어 `dev`에 들어왔다. 병합 뒤 CodeRabbit 첫 회차가 알려 `열림`으로 되돌렸고(이 브랜치의 그 파일 변경은 0이다), 그래서 만료는 다섯 개다.
- 일지에만 남기는 것: 이 세션의 카나리아·변이·e2e 결과는 위 "고친 뒤 다시 돌린 것"에 있다.

## 다음

- 티켓 11 이어받기: 대화 화면에 보내기·이어 가기·승인 버튼을 더하고, 옛 `/runs` 화면과 탐색의 "실행" 항목을 걷는다. 그때 `RunList`와 `ConversationList`의 되풀이 모양(`EmptyFiltered`·`HEAD_CELL`·`Field`·`SkeletonTable`)이 하나로 줄어든다(`/runs`가 사라지기 때문). 패널의 승인·재개 쪽 요구가 생기면 이 티켓이 둔 패널과 끝 실행 열쇠 공유(`traceKeys.one`)를 그대로 쓴다.
- 티켓 12와의 충돌: 12가 탐색(`AdminNav`)에 "계정"을 더하고 관리 화면 사진 정답(`templates-adminframe--*`)을 늘리므로 나중에 병합하는 쪽이 글자 충돌을 푼다. `sibling_overlap`이 PR #659와 12의 워크트리가 `AdminNav.tsx`, `RunList.tsx`, `AdminFrame.stories.tsx`, 사진 정답 8장을 함께 고쳤다고 알렸다. 13은 `e2e/channel.ts`를 함께 고쳤다.
- `--spacing-panel`(480px, 이 티켓이 `theme.css`에 더한 토큰)의 디자인 시스템 올리기: `.claude/rules/web-design.md`의 이름 있는 치수 열거(틀 `nav`·`nav-item`·`top-bar`)에 `panel`을 함께 더하고 `/sync-design-system 올리기`로 올린다. 이 티켓에서 하지 않은 까닭은 그 지침 문서가 아티팩트로 올라가는 파일이라 올리기와 한 번에 하려는 것이다.
- 후속 후보(사용자의 결정이 필요): 폭 768 미만에서 패널이 화면을 덮을 때 뒤의 대화를 `inert`로 막고 포커스를 가두는 모달 동작을 줄지. 지금 명세와 디자인은 덮개와 모달을 요구하지 않았다.
- retro 후보: 코드의 `Turn`·`turnOf`(대화 화면의 한 실행)가 `CONTEXT.md`의 `교환` 피할 말(턴)과 겹치고 `Outcome.kind: "running"`이 "실행 중" 피하기와 어긋난다. 용어집이 대화 화면 쪽 낱말을 정해야 코드 이름이 맞는다.
- 흔들림 기록: 앞 세션이 본 `decision.e2e.ts:12`의 부하 아래 시간 창 실패는 대기열 306이 받아들인 종류의 새 사례다(앞 세션의 판정). 회차는 더하지 않았다.
- PR 직전 리뷰가 남긴 Minor(뒤로 넘긴다, 아래 "이어받은 세션: PR 직전 리뷰"): (a) 폭 `wide` 미만에서 패널이 화면을 덮는데 뒤의 대화가 `inert`가 아니라 Tab이 패널 밖으로 샌다(위 후속 후보와 같은 일이다), (b) `RunPanel`의 Esc 핸들러가 `document` 전체에 걸려 `event.defaultPrevented`를 보지 않는다(메뉴가 열린 채 Esc를 누르면 패널도 닫히는지 손으로 한 번 본다), (c) `turns.ts`의 `isPastTimeout`이 `Date.parse`가 NaN이면 영원히 멈추지 않는다(PR 봇 첫 회차 뒤 고쳤다. 아래 "PR 봇 첫 회차"), (d) `Conversation.tsx`의 `<summary>`에 앱의 포커스 링 클래스가 없다.

## 인계(2026-11-28, 커밋 뒤)

이 세션은 커밋(`73f0539ed`, 브랜치 `feature/10-chat-read-screens-list-panel-and-polling`)까지 하고 컨텍스트가 인계 문턱(20만 토큰)을 넘어 `커밋 뒤` 경계에서 새 세션에 넘긴다. 작업 트리는 깨끗하다(이 인계 절을 쓰기 전 `git status`가 비었다). 이 인계 절만 커밋하지 않은 변경이다. 새 세션이 같은 파일에 이어 쓰고 커밋한다. 이 세션의 제목은 `feature/10-chat-read-screens-list-panel-and-polling`이었고 `(인계함)`으로 바꾼다.

사용자 프롬프트는 앞 세션과 같은 `next-session` 지시문 하나뿐이고 정정·피드백은 없었다(이번 요청 범위는 PR과 병합까지다).

새 세션이 할 것(순서대로):

1. PR 직전 리뷰: `coderabbit-review` 서브에이전트(CLI가 안 돌면 `bug-perf-review`)를 돈다. 위 "고쳐서 새로 쓴 사실 문장" 네 줄을 그 브리프에 밀 주장으로 나열한다(CodeRabbit CLI는 주장 인자가 없어 CLI가 돌면 넘기지 못한다. 그 경우 이 줄은 건너뛴다). Critical·Major를 고치면 그 변경이 화면을 바꾸면 e2e와 사진을 다시 친다.
2. 푸시와 PR 열기(제목에 느낌표 없음. 이 티켓의 변경은 운영자가 올릴 때 손댈 것이 없다고 봤다: 새 설정 칸·명령 없음, 읽기 화면만 더함, 어림). 본문 끝에 `🤖 Generated with [Claude Code](https://claude.com/claude-code)`. 본문에 적을 것: (a) `@split` 784px 경계의 이유(큰 표와 카드의 갈래는 컨테이너 쿼리, 명세의 768px(`wide`)과 다르고 뷰포트 768~1040px에서 명세의 표 대신 카드가 선다), (b) "다시 읽기" 버튼을 읽기 골격 `ReadSection`의 "새로 고침"으로 갈음한 것, (c) 320px 패널 사진에서 아래에 대화가 비치는 까닭(패널이 디자인 `ch-run.dc.html`대로 `absolute right:0 width:480px`이고 전체 페이지 사진에서 `fixed inset-0`이 뷰포트 높이만 덮는다), (d) 푸터 `flex-wrap`과 `whitespace-nowrap` 수정과 회귀 단언이 글자 폭이 아니라 계산 스타일(`whiteSpace`, `flexWrap`)인 까닭(Windows 로컬의 스토리 시험 브라우저와 Docker Linux 사진 환경의 글꼴이 달라 `Range.getClientRects` 단언은 고치기 전에도 통과했다), (e) 패널 여닫기를 `replaceState`로 해 패널이 열린 채 뒤로 가기를 누르면 대화 목록으로 가는 것(코드 주석과 변이 표가 지킨다. 명세는 패널의 방문 기록을 말하지 않았다), (f) 앞 실행에 "이 실행은 결말 없이 끝났다"를 보이는 것(명세에 문구 없음), (g) 사진 정답은 375px 프로젝트가 아니라 관리 화면의 폭 둘 1280/320이고 `@split` 경계 근처는 jsdom이 컨테이너 쿼리를 재지 못해 시험이 없는 것, (h) `--spacing-panel` 토큰의 디자인 시스템 올리기는 후속, (i) 셀프 리뷰 반영(불리언 칸을 `fit`·`Place`로, 포커스 복귀, `aria-controls`, 쓰이지 않던 `formatClockTime` 삭제), (j) 변이 표 9건과 옛 표 7건의 원문 수리, 카나리아 둘.
3. PR을 연 뒤 `mcp__ccd_pr__get_status`로 보고 그 PR이 아니면 `bind_pr`한다. 병합은 이 워크트리 사본의 `.claude/skills/next-session/merge.md`의 "워크트리에서 병합할 때"를 Read로 열어 따른다. 병합 순서 주의: PR #659(admin-login 12)가 `AdminNav.tsx`, `RunList.tsx`, `AdminFrame.stories.tsx`와 사진 정답 8장을 함께 고쳤고 12는 먼저 열렸다. 12가 먼저 병합되면 이 PR이 `dev`와 글자 충돌을 낸다(`merge.md`의 충돌 절차를 따른다. 사진 정답 PNG는 어느 쪽을 고르지 말고 `pnpm -C web visual:admin:update`로 다시 만든다). 13은 `e2e/channel.ts`를 함께 고쳤다.
4. 지시문을 낸다(`next-session`).

이 세션이 직접 친 마지막 검증은 위 "고친 뒤 다시 돌린 것"에 있다. 커밋 직전 pre-commit은 `parallel-checks`(pytest 포함)가 부하로 한 번 빨갛다 다시 통과했다(위 둘째 커밋 시도).
open-session을 부른다 2026-11-27T17:37:59Z

## 이어받은 세션: PR 직전 리뷰(2026-11-28)

새 세션(Sonnet 5.5 / high)이 같은 워크트리를 이어받았다. 시작 때 제목을 브랜치 이름으로 바꿨고 `sync-design-system 확인`을 다시 돌려 `clean`(결정 `continue`)을 봤다. 사용자의 정정이나 피드백은 없었다(지시문 하나뿐, 범위는 PR과 병합까지).

- `coderabbit-review` 서브에이전트: CodeRabbit CLI 0.7.5가 돌아 `review_completed`였다(좌석 `not assigned`, Plan Free, 리뷰는 끝까지 돌았다). Critical 0, Major 0, Minor 6이다. 앞 절 "밀 주장" 넷 가운데 1·2·4는 코드와 맞고 3은 "처음 연 자리"로 좁혀야 한다고 했다. 이 절의 리뷰 판정은 모두 서브에이전트가 코드를 읽고 보고한 것이고 이 세션이 다시 재거나 화면에서 보지 않았다(아래 오탐 판정도 같다). `sync-design-system 확인`의 `clean`만 이 세션이 `check judge`와 `decide`를 쳐서 읽은 출력이다.
- 고친 것(주석 둘, 코드 변경 없음): `hooks/queries/admin/index.ts`의 머리 주석이 주기 읽기를 접속 확인 하나로 적고 도메인을 둘로 적어 문장 1과 어긋나던 것을 "접속 확인과 대화 화면의 끝 실행 둘", "플러그인, 실행, 대화 도메인"으로 고쳤다. `RunPanel.tsx` 독스트링은 "처음 패널을 열 때 포커스가 있던 곳"으로 좁히고, 열린 채 다른 "자세히"를 눌러도 돌아가는 곳은 처음 연 버튼이라고 적었다(`key={runId}`로 다시 마운트하는 길은 "이미 열린 채 바뀔 때는 포커스를 옮기지 않는다"와 부딪혀 독스트링을 고치는 쪽을 골랐다).
- 남긴 것은 위 "다음"의 첫 항목 (a)~(d)이다. (a)는 앞 절의 후속 후보와 같은 일이다.
- 오탐으로 판정: 스토리의 다크·`showcase` 지적은 `packages/ui`의 규칙이고 관리 앱은 사진 비교가 라이트·다크를 모두 찍는다. 보안과 성능 축은 문제 없다고 보고했다(경로는 인코딩되고 사용자 글은 텍스트로만 들어간다, 끝 실행 읽기는 3초 간격으로 멈출 때가 정해져 있고 패널과 열쇠를 나눠 쓴다).

## 병합 전 충돌 풀기(2026-11-28)

PR #659(admin-login 12)가 먼저 병합돼 `origin/dev`를 두 번째로 합쳤다(첫 합치기는 #658이라 충돌이 없었다). `git merge origin/dev`의 충돌 출력으로 본 것이다.

- `AdminNav.tsx`: `Section`에 "chat"과 "accounts"를 둘 다 두고 항목 차례를 플러그인, 대화, 실행, 계정, 설정으로 했다.
- 시각 도우미 둘이 같은 일을 했다: 12가 `components/atoms/clock.ts`(`localClock`, `formatTime`, `formatMinute`, `formatClockTime`)를 만들었고 이 브랜치는 `molecules/localTime.ts`(`localClock`, `formatTime`)를 만들었다. 함수 본문은 같았다(두 파일을 읽어 맞댔다). `atoms/clock.ts` 하나로 모으고 `localTime.ts`를 지웠으며 `Conversation`, `ConversationList`, `RunList`의 import를 `atoms/clock`으로 바꿨다. `clock.ts` 머리 주석에 대화 목록과 대화 화면이 쓴다고 더했다. `run_list_mutations.toml`의 변이 둘은 `atoms/clock.ts`를 가리키는 12의 쪽을 남겼다.
- `AdminFrame.stories.tsx`의 `SystemAdmin` 기대 목록에 "대화"를 더했다. 합친 뒤 `pnpm -C web verify`가 2건 실패했다(출력 끝줄 `Tests 2 failed | 3219 passed`, 둘의 이름은 출력 앞부분이 잘려 보지 못했고 같은 스토리의 넓은 폭과 좁은 폭으로 어림했다). 고친 뒤 `pnpm -C web exec vitest run --project admin-storybook-wide --project admin-storybook-narrow AdminFrame.stories.tsx`는 10건 통과(종료 코드 0, 파이프 없이 쳤다)했고 전체 `verify`는 다시 돌리지 않았다. 커밋의 pre-commit과 `run_checks.py`가 다시 돌린다.
- 사진 정답 8장(`templates-adminframe--*`)은 충돌이라 `dev`의 판을 놓고 `pnpm -C web visual:admin:update`로 다시 만들었다(`188 passed (7.0m)`, 바뀐 사진은 그 8장뿐). `system-admin-1280-light` 한 장을 열어 보니 탐색에 플러그인, 대화, 실행, 계정, 설정이 차례로 서고 설정이 선택돼 있었다. 나머지 7장은 열어 보지 않았다.

## 인계(2026-11-28, PR 연 뒤)

이 세션은 PR #660(https://github.com/njh6803/agent-os/pull/660)을 열고 컨텍스트가 인계 문턱(20만 토큰)을 넘어 `PR 연 뒤` 경계에서 새 세션에 넘긴다. 이 세션의 제목은 `feature/10-chat-read-screens-list-panel-and-polling`이었고 `(인계함)`으로 바꾼다. 사용자의 정정이나 피드백은 없었다(지시문 하나뿐, 범위는 PR과 병합까지). 이 일지 인계 절 외에 커밋하지 않은 변경은 없다.

한 것: 리뷰 반영 커밋(`8ba78adf7`), `origin/dev` 합치기 둘(#658은 충돌 없음, #659는 위 "병합 전 충돌 풀기"), 푸시, PR 열기. PR 본문 파일은 이 세션의 스크래치패드에 있고 `gh pr view 660`으로 읽을 수 있다. 앱은 이 PR을 이 세션에 이미 묶었다(`get_status`가 `bound: true`, 이때 검사는 통과 1·진행 8·건너뜀 2, `mergeStateStatus`는 `BLOCKED`로 검사가 끝나기 전이다).

새 세션이 할 것(순서대로):

1. `@coderabbitai review` 코멘트를 남기고 `merge.md` 2(봇 회차)대로 기다린다. PR #660의 본문과 위 일지가 이미 결정을 적었다. 합친 뒤의 관리 화면 e2e와 `pnpm -C web verify` 전체는 이 세션이 다시 돌리지 않았다(`AdminFrame` 스토리 둘만 고쳐 돌렸다). CI의 `e2e`와 `verify` 잡이 도는 것을 보고, 빨강이면 그 실패를 읽어 고친다.
2. 봇 지적 가운데 Critical·Major만 고치고(첫 회차는 Minor·Nit을 지적마다 판단), 뒤로 넘기는 것은 일지 "다음"에 적어 같은 커밋으로 푸시한다.
3. 병합은 이 워크트리 사본의 `merge.md`의 "워크트리에서 병합할 때"를 Read로 열어 따른다. 로컬 모델 시험은 이 PR의 변경이 `web/apps/admin`과 일지·규칙 줄뿐이라 `llm_local` 범위가 아니다(`operations.md` LLM 테스트의 범위를 열어 확인한다).
4. 병합 뒤 일지 "다음"의 항목(위)으로 지시문을 낸다.

open-session을 부른다 2026-11-27T19:08:44Z

## 이어받은 세션: PR 봇 첫 회차(2026-11-28)

새 세션(Sonnet 5.5 / high)이 PR #660을 이어받았다. 시작 때 제목을 브랜치 이름으로 바꾸고 `tidy-checkouts`를 돌아 주 체크아웃을 `origin/dev`까지 당겼다(워크트리 하나와 브랜치 하나를 지웠다). `sync-design-system 확인`은 `clean`(결정 `continue`)이었다. 사용자의 정정이나 피드백은 없었다(지시문 하나뿐, 범위는 PR과 병합까지). 앱의 `bind_pr` 도구는 자동 모드 분류기가 거부해 PR이 이 세션에 묶이지 않았고, 우회하지 않았다(대기는 `wait_ci.py`로 한다).

`@coderabbitai review`를 남기고 `wait_ci.py`가 낸 끝 줄은 `끝: 모두 통과. CodeRabbit: Finished`였다(검사 열한 줄 SUCCESS, `llm`만 건너뜀, 합친 뒤의 `e2e`·`verify`·`visual` 포함. 도구 출력). CodeRabbit 첫 회차는 인라인 Minor 6건, claude-review는 Minor 3건과 Nit 1건을 냈다. 지적마다 판단한 것이다(코드를 읽어 판정했고 화면에서 보지는 않았다).

- 고쳤다(5): (1) `.scratch/retro-queue/mutation-table-checked-late.md`가 티켓 12(#659)의 둘째 승인으로 `dev`에서 다시 열린 항목인데 이 브랜치의 만료 일괄 편집이 `만료`로 되돌려 있었다. `열림`으로 되돌렸고 이 브랜치의 그 파일 변경은 0이다(`git diff origin/dev -- .scratch/retro-queue`가 비었다). 일지의 만료 문장을 6개에서 5개로 고쳤다. (2) `turns.ts`의 `decide`가 결정한 계정이 비면 시작 이벤트의 주체(`principal`)를 써 요청자가 승인한 것처럼 보였다. 계약의 `approver`(결정한 주체)를 쓰게 하고 `decide`의 `principal` 인자를 뺐다. 요청 주체와 승인자가 다른 시험을 `turns.test.ts`(승인과 거부 모두)와 `ConversationPage.test.tsx`에 더했고, 옛 페이지 시험이 옛 동작(`hong`)을 고정하고 있어 그것을 `ops-cli`로 고쳤다. (3) 시작 이벤트가 없는 트레이스는 `startedAt`이 빈 글이라 `formatTime`이 `RangeError`를 던질 수 있었다. `Conversation.tsx`의 `TurnView`가 시각이 비면 시각 칸을 그리지 않게 했다(트레이스 로더는 시작 이벤트의 존재를 확인하지 않는다는 지적은 코드로 확인하지 않았다. 처리 계층은 화면으로 정했다). 시험은 `ConversationPage.test.tsx`의 "시작 이벤트가 없는 트레이스도…"다. (4) `ConversationPage.test.tsx`의 `getByText("support-bot")`을 `findByText`로 바꿨다(제목은 데이터와 무관하게 먼저 그려진다). (5) claude-review의 `isPastTimeout` NaN: 읽을 수 없는 시각이면 지난 것으로 본다(`Number.isNaN`). 시험 하나(`pollInterval`)와 변이 하나를 더했다.
- 변이 표 `.scratch/admin-login/probes/chat_read_mutations.toml`: `isPastTimeout`을 고쳐 변이 2의 원문이 어긋나(`--check`가 알렸다) 고쳤고, NaN 가드를 지우는 변이 3을 더했다. `mutate.py --check`는 "변이 10 모두 원문이 한 번씩 있다"였고, 변이 2와 3을 돌려 둘 다 기대대로 빨강이었다(손으로 쳤다, `변이 2 모두 기대대로`).
- 뒤로 넘겼다(PR 코멘트에 보류 이유를 남기고 일지 "다음"의 기존 항목이 받는다): 폭 `wide` 미만에서 패널 뒤를 `inert`로 막는 일(Minor, 이미 "다음"의 후속 후보와 (a)이고 사용자의 결정이 필요하다), `RunPanel`의 Esc 핸들러가 `defaultPrevented`를 보지 않는 일(claude-review Minor, "다음"의 (b)), 스토리의 다크 모드(CodeRabbit Minor: 앞 세션이 오탐으로 판정했다. 관리 화면 사진 비교가 라이트·다크를 모두 찍는다), `RunList`·`ConversationList` 되풀이 모양(티켓 11이 `/runs`를 걷으며 줄인다, "다음" 첫 항목), `stale`의 `Date.now()` 의존을 `turns.ts` 독스트링에 적는 일(Nit).
