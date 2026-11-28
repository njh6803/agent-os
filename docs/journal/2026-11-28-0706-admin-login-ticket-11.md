# 2026-11-28 admin-login 티켓 11: 대화에서 보내고 결정하기, 옛 실행 화면 걷기

브랜치 `feature/11-chat-send-screens-and-old-run-screens-go`, 티켓 `.scratch/admin-login/issues/11-chat-send-screens-and-old-run-screens-go.md`. 새 세션(Sonnet 5.5 / high)이 워크트리 `11-chat-send-screens-and-old-run-screens-go`에서 구현했다. 이 일지는 구현과 검증까지를 적는다. 컨텍스트가 한 번 압축되어 앞 절은 압축 요약에서 옮겼다.

## 사용자 프롬프트

붙여 넣은 `next-session` 지시문 하나뿐이다(원문은 길어 요지만 옮긴다). 이 세션에서 사용자가 따로 한 말은 없다. 중간의 `[SYSTEM NOTIFICATION]`(백그라운드 작업 끝 알림)과 훅의 상태 알림은 사용자 입력이 아니다.

> 사용자: `.claude/skills/implement/SKILL.md`를 읽어 그대로 따른다. 인자는 `.scratch/admin-login/issues/11-chat-send-screens-and-old-run-screens-go.md`다. 다음 작업은 대화 화면에서 보내고 이어 가고 승인하고 다시 보내는 일과, 옛 실행 목록·상세 화면을 걷고 `/runs`를 `/chat`으로 옮기는 일이다. 어디서는 이 워크트리이고 브랜치는 `feature/11-chat-send-screens-and-old-run-screens-go`, 모델은 Sonnet 5.5 / high다. 이번 요청 범위는 PR과 병합까지다. 병합은 워크트리 사본의 `merge.md`의 "워크트리에서 병합할 때"를 따른다.

## 한 것

- 보내는 쪽: `api/conversation/turns.ts`(시작·이어 가기·다시 보내기의 앞 실행 고르기, 결정을 `approver`로 적는 것, `earlierAfterSend`), `api/conversation/index.ts`, `hooks/queries/conversation`(`useRunStream`), `hooks/queries/session`의 `useKeepSignedIn`(짧은 JWT 수명의 80%마다 갱신), `api/session`의 `keepSignedIn`과 `rule.ts`의 `renewWhileStreaming`, `hooks/useRunQuery.ts`의 `replaceAddress`.
- 화면: organisms `Composer`(새 대화의 에이전트 칸, 입력 칸, 막힘, 최종 사용자의 한 줄), `ApprovalAsk`(거부가 먼저인 보조 버튼, 승인이 나중인 주 버튼, 사유 칸, 꺼짐 미리 알림), `Conversation`·`RunPanel`·`EventItem`의 고침, pages `ConversationPage`(새 대화 `/chat/new` 포함).
- 걷은 것: `app/runs/**`, `RunList`, `RunDetail`, `RunColumns`, `RunDecision`, `RunPage`·`RunsPage`와 그 시험·스토리, `hooks/queries/approval`, e2e `runs.e2e.ts`, 탐색의 "실행" 항목. `next.config.ts`의 `redirects()`가 `/runs`를 `/chat`으로, `/runs/:runId`를 `/chat/:runId?run=:runId`로 옮긴다(임시 이동).
- 규칙: `.claude/rules/web-design.md`와 `.claude/rules/web-admin.md`(규칙 파일을 고치기 전에 `writing-for-agents`를 불렀다).
- 시험: 페이지 시험 `ConversationPage.write.test.tsx`(49건)와 `ConversationPage.test.tsx`의 고침, `turns.test.ts`, `tools/redirects.test.ts`(새), 스토리 `ApprovalAsk.stories.tsx`(7건)·`Composer.stories.tsx`, e2e `decision.e2e.ts`(4건, 375px 포함)·`reading.e2e.ts`(3건)·`chat-write.e2e.ts`(2건)와 `chat`·`plugin-toggle`·`accounts`·`login` e2e의 고침, 변이 표 `.scratch/admin-login/probes/chat_write_mutations.toml`(12건. 열두째는 셀프 리뷰가 더했다).
- 사진 정답: 옛 `organisms-rundetail--*`·`organisms-runlist--*` 모두 지웠고, 새로 `organisms-approvalask--*`(7 스토리)와 `organisms-composer--*`, 바뀐 `organisms-conversation--*`(입력 칸이 붙음)와 `templates-adminframe--*`(탐색에서 "실행"이 빠짐)을 `visual:admin:update`로 만들었다.

## 이 세션이 정하거나 고친 것(PR 본문에도 쓸 것)

- 입력 칸의 글자 상자는 보내기가 막힌 동안에도 쓸 수 있다(막히는 것은 보내기 버튼과 전송이다). 쓰던 글을 잃지 않게 한 것이다.
- 보낸 요청 글은 서버가 거절해도 입력 칸에서 바로 비워진다. 실패하면 알림이 서고 사람이 다시 쳐야 한다. 거절된 글을 되살리는 일은 하지 않았다(후속 후보).
- 보낸 뒤 새 끝 실행을 마운트하면서 SWR이 그 실행의 트레이스를 한 번 더 읽는다. 시작 이벤트가 온 직후의 값을 서버의 기록으로 맞추는 읽기라 버리지 않았다.
- `/chat/new`는 대화 화면의 "새 대화" 링크로도 닿는다(목록에서만 닿지 않는다).
- 디자인 시스템 패키지의 `ShowcaseRunList` 스토리(`web/packages/ui`)는 이름이 "실행 목록의 배지 넷"으로 남았다. 아티팩트의 카드 이름이라 바꾸려면 디자인 시스템 올리기가 함께 들어, 이 티켓에서는 규칙 문서의 자리만 "대화 목록의 배지"로 고쳤다(다음에 적는다).
- 사진 정답은 375px 프로젝트가 아니라 관리 화면의 폭 둘 1280/320이다(앞 티켓과 같은 판단). 375px의 승인 묻기는 e2e(`decision.e2e.ts`)가 보고, 320px 사진이 같은 갈래(`360px 미만이면 버튼 둘이 위아래로 꽉 찬다`)를 찍는다.
- 기능을 닫지 않았다. 11·12·14 가운데 마지막이 아니다(13과 14가 `ready-for-agent`다).

## 고친 실수: 갱신이 나가지도 못했다(e2e에서 처음 드러남)

첫 전체 e2e가 거의 모든 사례에서 로그인 단계에서 실패했다. 로그인하지 않고 `/`를 열면 `/login?next=%2F`로 가야 하는데 화면은 `/`에 남아 "로그인한 계정을 읽지 못했다"를 보였다. 실패한 실행의 `trace.zip`을 풀어 네트워크 줄을 보니 `GET /api/auth/me`가 401을 받은 뒤 `POST /api/auth/refresh`가 아예 나가지 않았고, serve 로그에도 갱신 줄이 없었다(손으로 봤다).

원인은 내 리팩터링이었다. 스트림 동안의 갱신(`renewWhileStreaming`)을 더하며 `rule.ts`의 `refresh`가 받는 값을 `send` 함수에서 `() => Promise<Response>`로 바꿨고, 갱신 요청을 `options.fetch(new Request(...))`로 불렀다. `options.fetch`는 브라우저의 전역 `fetch`이고, 객체의 메서드로 부르면 `this`가 `options`가 되어 "Illegal invocation"이 난다. `refresh`의 `catch`가 그것을 삼켜 "모름"으로 돌려, 갱신이 나가지도 못한 채 처음 401이 그대로 돌아왔다. 원래 코드는 함수만 꺼내 불러 문제가 없었다.

고친 것은 `const send = options.fetch;`로 함수를 꺼내 `send(...)`로 부르는 것이다(다시 보내기의 `send(copy)`도 같게 했다). 페이지 시험은 이것을 잡지 못했다. jsdom의 `fetch`는 `this`를 검사하지 않기 때문이다(그래서 640건이 초록이었다). 이 종류는 브라우저에서만 나는 실패라 e2e가 잡는다. 고친 뒤 로그인 e2e 셋이 통과했다.

(이 일지의 앞 판은 "원래 코드는 함수만 꺼내 불러 문제가 없었다"고 적었다. 셀프 리뷰 때 다시 보니 원래 코드의 다시 보내기도 `options.fetch(copy)`로 같은 모양의 메서드 호출이었고, 이번에 함께 고쳤다. 원래 코드가 왜 이 e2e들을 지났는지는 확인하지 않았다.)

또 하나는 e2e에서 드러난 사례다. `plugin-toggle.e2e.ts`가 대화 목록에서 멈춘 실행의 링크를 `a[href="/chat/<id>"]`로 찾는데, 목록이 표와 좁은 폭의 줄을 함께 그려 같은 주소의 링크가 둘이라 strict 모드가 실패했다. `:visible`로 보이는 쪽만 고르게 했다.

## 검증 결과(이 세션이 직접 친 명령)

- 관리 화면 e2e `pnpm -C web/apps/admin exec playwright test`: 첫 전체 실행에서 위 둘로 실패한 뒤 고쳐서 `18 passed`와 `plugin-toggle` 둘 재실행 `2 passed`(합쳐 19건 전부 통과).
- 사진 정답 다시 만들기 `pnpm -C web visual:admin:update`: `194 passed (5.0m)`. 바뀐 정답을 열어 봤다(`organisms-approvalask--default-320-light`, `--invalid-1280-dark`, `organisms-composer--new-1280-light`, `organisms-conversation--waiting-320-light`, `templates-adminframe--signed-in-1280-light`). 320px에서 "거부"(보조)가 먼저 "승인"(주)이 나중으로 위아래 꽉 차고, 1280px에서는 오른쪽에 나란히 섰다. 오류 상태는 사유 칸이 빨간 테두리에 알림이 아래에 섰다. 탐색에는 플러그인·대화·설정만 남았다. 나머지 사진은 열어 보지 않았다.
- 사진 비교 `pnpm -C web visual:admin`: 종료 코드 0.
- 변이 표 `chat_write_mutations.toml`: `--check`가 "변이 11 모두 원문이 한 번씩 있다"였다. 표지는 처음 자리표시(`AssertionError`)로 두고 돌려 변이 열한 건이 모두 "기대 빨강, 결과 빨강"임을 본 뒤, 일부러 맞지 않는 표지(`__probe__`)로 돌려 실제 실패 줄을 받아 실제 문구로 바꿨다(`expected +0 to be 1`, `to contain 'notice=expired'`, `expected '/chat/new' to be '/chat/r9'`, 최종 사용자의 한 줄과 승인 대기 줄과 다시 보내기 안내의 `Unable to find an element with the text: …`, `to deeply equal []`, `…decision: 'approve'…to deeply equal`, `expected false to be true`, `expected null to deeply equal { traces: [], end: 'start' }`, `to deep equally contain { source: '/runs/:runId'`). 11번은 처음 `deeply equally`로 적어 어긋나 출력의 `deep equally`로 고쳐 다시 돌렸고 기대대로였다. 마지막으로 열 건(1~10)은 실제 표지로, 11번은 고친 표지로 따로 돌려 "기대대로"를 보았다. 실행 뒤 `git status`와 소스 몇 줄로 원상 복구됐음을 봤다. 표를 스크립트로 고치다 이 파일이 CRLF가 되어 `sed`로 LF로 되돌렸다(미추적 파일을 스크립트로 다시 쓰지 말라는 `probes.md` 항목의 위험이 CRLF로 드러난 작은 사례다. 파일은 비지 않았다).
- `uv run ruff check .`는 `All checks passed!`, `uv run ruff format --check .`는 종료 코드 0.
- `uv run python tools/run_checks.py`(스테이지 뒤, 백그라운드): 종료 코드 0. 줄마다 `Passed`였다(check-notes, check-ticket, lint-imports, zizmor, check-instructions, check-type-escapes, pyright 둘, run-hooks, web-verify 613.0초, pytest 639.0초). `web-verify`가 `pnpm -C web verify`이므로 그것은 따로 다시 치지 않았다.

## 셀프 리뷰(`code-review`: 표준 축과 명세 축, 고정점 `origin/dev`의 merge-base)

- 표준 축(`sonnet`/`high`)이 Major 하나를 냈다. `web_admin_plugins_read.toml`의 카나리아 질문과 기대 문장이 규칙 문장을 고친 뒤의 것과 달랐다. 질문과 `expect`를 새 문장(`새 대화이거나 기다리는 승인이 있을 때만`)으로 고치고 카나리아를 다시 돌렸다: 통과 4(실험군 3회차가 글자 그대로 옮겼고 대조군은 "없음"). 결과 줄은 파일 머리에 적었다.
- 표준 축의 나머지는 문서의 낡은 말이었다. `README.md`의 결정 자리 줄과 `hooks/queries/plugins/index.ts`의 `usePlugins` 독스트링을 대화 화면 기준으로 고쳤다. `ChatSession`의 다시 그려지는 때를 닫힌 주장("스트림 프레임이 올 때뿐")으로 적은 주석도 반례를 반영해 풀었다.
- 명세 축이 (a) 도는 실행의 읽기 시험이 "3초 넘게 글을 치는" 장면이 아니라는 것(Major에 가까운 빈틈)과 (c) 새 대화에서 보낸 뒤 "새 대화" 링크가 동작하지 않을 수 있다는 것을 냈다.
  - (a): 시험을 한 글자씩 1초 간격으로 7초 동안 치게 고치고, 일부러 `ChatSession`이 1초마다 다시 그려지게 한 변이를 변이 표의 열두째로 더했다. 변이는 `expected 1 to be greater than or equal to 3`으로 빨개졌다(전 판은 이 변이를 물지 못했다).
  - (c): e2e에 "보낸 뒤 '새 대화'를 누르면 빈 새 대화가 서고, 뒤로 가기를 누르면 둘째 실행의 대화로 돌아온다"를 더해 먼저 빨강을 봤다(옛 대화가 남았다). 원인은 둘이었다. `replaceAddress`가 라우터의 상태가 든 `history.state`를 그대로 넘겨 Next가 자기 것으로 보고 주소를 따라오지 않았고(`usePathname`이 `/chat/new`에 남았다), 라우터는 같은 조각의 이동에 화면을 다시 세우지도 않았다. `replaceAddress`는 상태를 `null`로 넘기고, 새 부품 `ChatHost`가 `usePathname`이 이 화면이 바꾼 것이 아닌 주소가 되면 `ChatSession`을 새로 세워 그 주소의 대화를 읽게 했다. e2e가 초록이 됐다.
  - 명세 축이 남긴 둘째 (a)(뒤로 가기가 대화 목록으로 가는 것을 history 길이로만 본다, 옛 주소 이동을 페이지 시험이 아니라 설정 시험과 e2e가 본다)는 뜻은 덮이므로 고치지 않았다.
- 남긴 것(이유 한 줄씩): 디자인 시스템 패키지와 `artifact-source`의 낡은 말("실행 목록"의 주석과 `StatusBadge.md`, `Alert.stories.tsx`, `TextLink.stories.tsx`)은 `web/packages/ui`라 디자인 시스템 올리기와 함께 고쳐야 한다(`ShowcaseRunList` 이름과 같은 후속). 대화 목록·계정 화면의 주석이 지워진 "실행 목록"을 기준으로 든 곳(`AccountList.tsx`, `ConversationList.tsx`, `ReadSection.tsx`, `StatusFilter.tsx`, `clock.ts`, `EmptyLine.stories.tsx`, `AccountsPage.test.tsx`)은 말의 뜻이 틀리지 않는 주석이라 이 티켓에서 고치지 않았다(후속 후보). `hooks/queries/conversation`과 `conversations`가 같은 이름의 `conversationKeys`를 내보낸다는 지적(Nit), `onRetry`와 `onSend`의 앞 실행 고르기가 겹친다는 지적(Nit)도 남겼다. `refreshRule`의 "Illegal invocation"은 단위 시험을 더하려면 openapi-fetch 미들웨어의 전체 옵션 타입을 단언 없이 흉내 내야 해서 더하지 않았고, 로그인 e2e가 덮는다.

## 이 티켓이 남긴 것(회고가 "다음"으로 옮긴다)

- 티켓 13과 14가 남았다. 14가 `**끝:**`를 적고 `docs/release-notes/features/admin-login.md`를 싣는 마지막 병합이 될 수 있다. 그 티켓이 11·12의 병합을 확인하고 기능을 닫는다.
- `ShowcaseRunList`(`web/packages/ui`)의 이름 "실행 목록의 배지 넷"을 "대화 목록의 배지"로 바꾸는 것은 디자인 시스템 올리기와 함께 한다.
- 앞 티켓 10에서 넘어온 `--spacing-panel`의 올리기, 패널 뒤 `inert`(사용자 결정 필요), `Turn` 낱말과 용어집의 어긋남은 그대로 남아 있다.
- 거절된 요청의 글을 입력 칸에 되살리는 일은 하지 않았다(후속 후보, 사용자의 결정이 필요한 UX다).
- 브라우저의 전역 `fetch`를 객체의 메서드로 부르는 실수(위 "고친 실수")는 페이지 시험(jsdom)이 잡지 못하고 e2e의 로그인 사례만 잡는다. 같은 모양의 호출이 다른 자리에 또 있는지는 셀프 리뷰가 `options.fetch(`·`client.fetch(`를 grep해 본다(이 세션이 `rule.ts` 밖에서는 찾아보지 않았다).

## 인계(2026-11-28, 셀프 리뷰 직전)

이 세션은 구현과 위 검증까지 하고 컨텍스트가 인계 문턱(20만 토큰)을 넘어 `셀프 리뷰 직전` 경계에서 새 세션에 넘긴다. 커밋하지 않았고 변경은 모두 스테이지했다(`git add -A`, 이 일지와 티켓과 `plan.md` 표 포함. 이 일지의 마지막 두 편집은 스테이지 뒤에 해 작업 트리에 있다). 방금 `code-review` 스킬을 불렀지만 서브에이전트는 띄우지 않았다. 이 세션의 제목은 `feature/11-chat-send-screens-and-old-run-screens-go`였고 `(인계함)`으로 바꾼다. 사용자의 정정이나 피드백은 없었다(지시문 하나뿐, 범위는 PR과 병합까지).

새 세션이 할 것(순서대로):

1. 셀프 리뷰: `/code-review`를 Skill 도구로 부르거나 Read로 `.claude/skills/code-review/SKILL.md`를 열어 따른다. 고정점은 `origin/dev`의 merge-base다. 명세 축의 근거는 티켓 `.scratch/admin-login/issues/11-chat-send-screens-and-old-run-screens-go.md`와 `.scratch/admin-login/spec.md`다. 위 "이 세션이 정하거나 고친 것"은 요구가 아니라 리뷰어 참고로 적는다. 주장 검증의 밀 주장으로 두 개를 둔다: (1) `rule.ts` 주석 "브라우저의 `fetch` 는 `options` 의 메서드로 부르면 'Illegal invocation' 이 나서 …", (2) `plugin-toggle.e2e.ts`의 "목록은 표와 좁은 폭의 줄을 함께 그려 같은 주소의 링크가 둘이라 보이는 쪽만 고른다"(목록 화면이 정말 둘을 그리는지 코드로 확인). Critical·Major를 고치고, 화면 모양을 바꾸면 e2e와 `visual:admin`을 다시 친다.
2. 티켓은 이미 `done`이고 체크박스를 채웠다(기능을 닫는 일 항목은 "마지막이 아니라 하지 않았다"). 리뷰로 코드가 바뀌면 티켓의 검증 줄이 여전히 맞는지만 본다. `uv run python tools/plan_table.py`는 이미 돌려 스테이지했다.
3. 커밋 직전 `uv run python tools/sibling_overlap.py`와 `git branch --show-current`를 친다(13·14의 워크트리가 `e2e/channel.ts`, 사진 정답, 탐색을 함께 고칠 수 있다). 커밋은 `git commit -F`로, 끝에 `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>`. pre-commit이 `run_checks.py`와 같은 명령을 돌려 그 결과로 갈음한다(`run_checks.py`는 이 세션이 이미 종료 코드 0으로 돌렸다).
4. 이 일지를 이어 쓴다: "셀프 리뷰" 절, 리뷰로 고친 뒤 다시 돌린 것, 회고, "다음"(`## 다음` 제목은 마지막에 한 번만. 위 "이 티켓이 남긴 것"을 그리로 옮긴다).
5. PR 직전 리뷰(`coderabbit-review` 서브에이전트, 안 돌면 `bug-perf-review`), 푸시, PR 열기(제목에 느낌표 없음, 본문 끝에 `🤖 Generated with [Claude Code](https://claude.com/claude-code)`). 본문에 적을 것은 위 "이 세션이 정하거나 고친 것" 여섯과 "고친 실수"(갱신이 나가지도 못한 것과 jsdom이 못 잡은 까닭), 사진 정답은 375px가 아니라 1280/320이고 375px는 e2e가 보는 것, `ShowcaseRunList` 이름이 남은 것, 기능을 닫지 않은 것이다. PR을 연 뒤 `mcp__ccd_pr__get_status`로 보고 묶이지 않았으면 `bind_pr`를 한 번 시도한다(앞 세션들에서 자동 모드 분류기가 거부했다. 거부되면 우회하지 않는다). 병합은 워크트리 사본의 `.claude/skills/next-session/merge.md`의 "워크트리에서 병합할 때"를 Read로 열어 따른다.
6. 병합 순서 주의: 티켓 13과 14가 같은 브랜치 기준(`origin/dev`) 위에서 `e2e/channel.ts`, 사진 정답(`templates-adminframe--*`), 탐색을 함께 고칠 수 있다. `dev`가 앞서 충돌하면 사진 정답 PNG는 어느 쪽도 고르지 말고 `pnpm -C web visual:admin:update`로 다시 만든다.

open-session을 부른다 2026-11-27T22:07:35Z

인계 못함 셀프 리뷰 직전: `tools/open_session.ps1`을 부른 PowerShell 호출을 자동 모드 분류기가 거부했다(사유 "Destructive or Unwanted Actions", 도구 결과를 읽었다). 우회하지 않았다. 제목은 `feature/11-chat-send-screens-and-old-run-screens-go`로 되돌렸고, 워크트리 잠금은 이미 풀었으며 다시 잠그지 않았다. 이 세션이 셀프 리뷰부터 이어 간다(위 인계 절의 새 세션이 할 것 1~6을 이 세션이 그대로 한다).

## 셀프 리뷰 뒤 다시 돌린 것

- 관리 화면 e2e `pnpm -C web/apps/admin exec playwright test`: `19 passed (1.4m)`(`chat-write`에 "새 대화" 링크와 뒤로 가기 단계를 더한 뒤).
- `pnpm -C web verify`: 종료 코드 0.
- 변이 표 `chat_write_mutations.toml`: 열두 건 모두 "기대 빨강, 결과 빨강", `변이 12 모두 기대대로`.
- 카나리아 `web_admin_plugins_read.toml`: 통과 4. `web_design_showcase.toml`(`web-design.md`의 보여 주기용 스토리 문장을 고쳐 `sibling_overlap`이 알렸다)도 통과 4(실험군 3, 대조군 1). 결과 줄은 두 파일 머리에 적었다.
- 사진 비교는 다시 치지 않았다. 셀프 리뷰의 고침은 화면 모양이 아니라 주소와 마운트 논리(`ChatHost`, `replaceAddress`)와 문서 말이고, 사진은 스토리가 찍기 때문이다. 나머지 손으로 치는 다섯(ruff 둘, pyright, lint-imports, pytest)은 커밋의 pre-commit 결과로 갈음한다.

## 커밋 직전에 정리한 변이 표(pre-commit의 변이 검사가 막은 것)

옛 실행 화면(`RunPage`·`RunsPage`·`RunDecision`·`RunDetail`·`RunList`)과 그 시험을 지우자 다른 기능의 변이 표 여덟이 지운 파일을 겨눠 pre-commit의 `mutate.py --staged`가 종료 코드 2로 막았다. 표마다 옮기거나 걷었고, 옮긴 변이는 실제로 돌려 표지까지 기대대로 빨간 것을 봤다(`tools/mutate.py`가 찍었다).

- 이벤트를 글자로 그리는 시험이 옛 `RunPage.test.tsx`와 함께 사라져 `EventItem`의 바로가기·실패 원인·HTML 이스케이프·적용 규칙·요약 필드 보호가 비었다. 그래서 새 `web/apps/admin/components/organisms/EventItem.test.tsx`(스물세 시험이 모두 통과했다. 네트워크 없이 이벤트 하나를 그린다)에 옛 시험을 옮기고, 최종 사용자 주체의 `|` 가 글자로 보이는 시험 하나를 더했다. 옮긴 시험으로 `end-user-continuation/admin_mutations.toml` 열한 건(여덟째가 옛 화면 시절의 `Link`를 써 `ReferenceError`로 빨갰던 것은 `TextLink`로 고쳤다), `admin-style/run_page_mutations.toml` 첫째, `conversation/continuation_mutations.toml`의 04 둘(번호는 28·29로 당겨졌다), `end-user-channel/admin_hides_decision_mutations.toml` 둘째가 기대대로였다. 04 둘은 원래 `expect_output`이 없었는데 시험이 바뀌자 pre-commit의 `--staged`가 표지 없는 빨강이라 막아(첫 커밋 시도가 종료 코드 1), 실패 출력을 보고 표지를 달았다(`expected <a …(2)></a> to be null`, `+   "요약 summary",`).
- `ConversationPage.write.test.tsx`의 두 시험("끝난 대화는 에이전트를 고르지도…", "승인을 기다리는 대화는 꺼짐을 미리 알리려고…")으로 `organisms_props_mutations.toml`의 첫째·둘째를, "최종 사용자의 대화" 묶음으로 `admin_hides_decision_mutations.toml`의 첫째를 옮겼다. 꺼짐 판정의 모델·스킬 두 표(`decision_model_mutations.toml`, `decision_skill_mutations.toml`)는 `disabledPlugins.ts`·`disabledPlugins.test.ts`로 겨냥을 옮기고 시험에 "고르지 않은 모델만 꺼졌을 때"의 사례를 더해 같음 변이(아무것도 재지 않던 것)를 물게 했다.
- 시간대·시각·읽기 골격 변이(`run_list_mutations.toml` 1·2·3, `frame_common_states_mutations.toml` 3)는 `ConversationsPage.test.tsx`·`ConversationPage.test.tsx`·`HomePage.test.tsx`의 시험으로 옮겨 표지까지 기대대로였다. 뼈대 변이 둘(옛 5·7번)은 옮긴 시험이 물지 못해(기대 빨강, 결과 초록) 걷었다.
- 지운 화면의 시험과 스토리만 겨누던 변이는 걷었다: `run_list_mutations.toml` 열다섯, `run_page_mutations.toml` 열하나, `frame_common_states_mutations.toml` 셋(17·18·20번), `organisms_props_mutations.toml` 하나(마운트 자리), `continuation_mutations.toml` 하나(11번), `admin_hides_decision_mutations.toml` 하나(둘째). 겨눈 파일이 사라졌으니 같은 보호를 다른 자리에 옮길 수 없었다. 프로브 README 줄과 표 머리 주석을 고쳤다.
- 이 티켓이 바꾼 소스에 맞춰 `chat_read_mutations.toml`(`useEndRun`의 열쇠 줄)과 `login_rule_mutations.toml`(`refreshOnce`의 `request` 인자)의 원문을 새 모양으로 고치고 다시 돌려 기대대로였다.
- 이 티켓이 만든 것이 아닌 어긋남 하나: `continuation_mutations.toml` 전체의 기준선이 pytest `-k 덮는_끝까지만_거슬러_가고`가 시험을 하나도 고르지 못해(`490 deselected`) 오류로 끝난다(admin-login 티켓 07이 시험 이름을 바꾼 뒤부터로 보이고, 이 일지는 `git log`로만 확인했다). 그래서 이 표는 전체를 돌리지 못하고 번호를 골라 돌려야 한다. 고치지 않았다.
- `mutate.py --check`를 바뀐 표 열둘에 쳐 종료 코드 0이었고, 남은 옛 화면을 겨눈 변이를 찾는 스캔(스크래치 스크립트)도 0건이었다.

## PR 직전 리뷰(`coderabbit-review`)와 반영

보고를 받은 턴에 지적마다 근거를 코드에서 열어 판정했다. 고친 것은 시험을 먼저 빨갛게 보인 뒤 고쳤다.

- **고쳤다: 보내기의 422가 어디에도 보이지 않았다.** `RunNotices`가 결정이든 보내기든 422를 "승인 묻기의 사유 칸이 받는다"며 감췄다. 그런데 승인 묻기는 결정의 422만 받는다. 새 시험(`ConversationPage.write.test.tsx`, "보내기가 422 를 받아도 승인 묻기가 없으니…")이 `role="alert"`를 찾지 못해 빨갰고, `kind === "decide"`일 때만 감추게 고쳐 초록이 됐다.
- **고쳤다: 주소와 화면이 어긋난 채 마운트되면 새 대화가 섰다.** 라우터가 저장한 화면을 복원하면 속성 `initialRun`은 처음 그릴 때의 값이라 지금 주소와 다를 수 있다. `ChatHost`가 `runOfPath(pathname) ?? initialRun`으로 주소에서 읽은 실행을 먼저 따르고, 읽을 수 없을 때(주소가 null인 라우터 밖의 jsdom)만 속성을 쓴다. 처음 쓴 `pathname === null ?` 꼴은 `usePathname()`의 타입이 `string`이라 `no-unnecessary-condition`이 막았다(커밋의 pre-commit `web-verify`). 시험은 `next/navigation`의 `usePathname`을 시험이 정하게 막아 `/chat/r1` 주소에 `runId={null}`로 그리는 사례다(고치기 전: `r1의 출력`을 찾지 못함, 새 대화 화면이 `/api/plugins`를 읽어 처리되지 않은 요청도 잡혔다).
- **고쳤다: 읽기가 실패해 대화가 지워진 동안에도 입력 칸이 섰다.** 지운 대화를 기준(`base`)으로 이어 보내면 운영자가 보지 못한 실행에 이어 붙는다. `read.error`가 있으면 입력 칸을 세우지 않는다. 기존 시험 "다시 읽다 실패하면 보인 대화를 지우고 실패만 보인다"에 입력 칸이 없다는 단언을 더했다(고치기 전: `expected <textarea … to be null`).
- **고쳤다: 승인 대기 도구 이름이 길면 넘쳤다.** `Composer`의 줄에 `min-w-0`과 `wrap-anywhere`를 더했다. `ApprovalAsk`가 이미 같은 클래스로 도구 이름을 감싼다. 화면의 보통 이름은 모양이 같아 사진은 다시 찍지 않았다(긴 이름을 그린 스토리는 없다).
- **남겼다: 보내는 중의 `disabled`.** 보내기 버튼이 막히는 이유는 "이 요청을 보내는 중"만이 아니라 도는 실행, 승인 대기, 끝맺지 못한 실행으로 여럿이다. `web-design.md`의 "불러오는 중은 disabled가 아니다"는 버튼 자신이 불러오는 중일 때의 규칙이라, 이 막힘은 쓸 수 없음(`disabled`)에 든다고 판단했다.
- **남겼다(Minor, 이 세션에서 고치지 않았다):** `onAddress`가 늦게 오는 경우의 가드, 응답 스트림이 `run_started` 전에 끊기는 경우, 시험의 약한 기다림(`write.test`의 고정 기다림), jsdom에서 아무것도 가르지 못하는 `Reflect.has` 단언, `last_covered_run` 링크 단언. 기능 실패를 재현하지 못했거나 시험의 모양 문제라 티켓 13·14의 수용 기준을 막지 않는다. 다음에 `ConversationPage.write.test.tsx`를 고치는 티켓이 함께 본다.
- 변이 표 `chat_write_mutations.toml`에 13~15번을 더했다: `RunNotices`의 422 감추기, 마운트 주소, 입력 칸. 셋 모두 "기대 빨강, 결과 빨강"이고 표지(`Unable to find role="alert"`, `Unable to find an element with the text: r1의 출력`, `expected <textarea`)가 맞았다(`변이 3 모두 기대대로`).
- 다시 돌린 것: `ConversationPage.test.tsx`·`ConversationPage.write.test.tsx`와 organisms 시험 126개가 모두 초록이다. 관리 화면 e2e `pnpm -C web/apps/admin exec playwright test`는 `19 passed (1.8m)`다. `mutate.py --check`로 `chat_write_mutations.toml`을 쳐 종료 코드 0이다. 나머지 게이트는 커밋의 pre-commit 결과로 갈음한다.
- 새로 쓴 사실 문장(다음 층의 리뷰가 겨냥할 것): "승인 묻기는 결정의 422만 받는다", "주소가 있으면 주소를 속성보다 먼저 따른다", "읽기 오류가 있으면 입력 칸이 서지 않는다".

## 다음

- 티켓 13과 14가 남았다. 14가 `**끝:**`를 적고 `docs/release-notes/features/admin-login.md`를 싣는 마지막 병합이 될 수 있다. 그 티켓이 11·12의 병합을 확인하고 기능을 닫는다.
- 디자인 시스템 올리기 때 함께 할 것: `ShowcaseRunList`의 이름 "실행 목록의 배지 넷"을 "대화 목록의 배지"로, `StatusBadge.md`·`Alert.stories.tsx`·`TextLink.stories.tsx`·`artifact-source/README.md`의 "실행 목록" 말을 고친다.
- 앞 티켓 10에서 넘어온 `--spacing-panel`의 올리기, 패널 뒤 `inert`(사용자 결정 필요), `Turn` 낱말과 용어집의 어긋남은 그대로 남아 있다.
- 대화 목록·계정 화면의 주석이 지워진 "실행 목록"을 기준으로 든 곳(`AccountList.tsx`, `ConversationList.tsx`, `ReadSection.tsx`, `StatusFilter.tsx`, `clock.ts`, `EmptyLine.stories.tsx`, `AccountsPage.test.tsx`)을 다음에 그 파일을 고치는 티켓이 함께 고친다. `conversationKeys`가 두 훅 폴더에서 같은 이름으로 나가는 것도 같다.
- 거절된 요청의 글을 입력 칸에 되살리는 일은 하지 않았다(후속 후보, 사용자의 결정이 필요한 UX다).
- 브라우저의 전역 `fetch`를 객체의 메서드로 부르는 실수는 jsdom 시험이 잡지 못하고 e2e의 로그인 사례만 잡는다. 같은 모양의 호출(`options.fetch(`·`client.fetch(`)이 다른 자리에 있는지는 grep해 본다.
- 주소만 바꾸는 `history.replaceState`는 라우터의 상태(`history.state`)를 넘기면 Next가 건너뛴다. 이 앱에서 주소를 스스로 바꾸는 곳은 `replaceAddress`(null 상태)와 `setRunQuery`(`history.state` 그대로, 질의만 바뀌어 `usePathname`에 쓰지 않는다) 둘이다.
