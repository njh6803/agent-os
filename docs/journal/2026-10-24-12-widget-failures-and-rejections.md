# 2026-10-24 (12) 위젯의 실패와 거절(web-widget 07)

## 사용자 프롬프트

> 사용자: /implement .scratch/web-widget/issues/07-widget-failures-and-rejections.md (next-session 지시문. 나란히 여는 3 중 1, 주 체크아웃 미갱신이라 tidy-checkouts 를 먼저 돌고 EnterWorktree 로 들어간다. 브랜치 feature/07-widget-failures-and-rejections, 범위는 PR과 병합까지. 읽을 것은 일지 2026-10-24-10 의 "다음"과 나란히 도는 티켓 10·11)

## 정리(tidy-checkouts)

주 체크아웃을 6a7b23f6 에서 148652ef 로 당겼다. 쉬는 세션 넷의 `claude.exe` 를 끈 뒤 `02-runtime-relays-call-events-live` 워크트리를, 그리고 `worktree-06-nginx-and-widget-e2e` 브랜치를 지웠다. 남긴 것은 다음과 같다(사람에게 넘긴 것은 보고만 하고 답을 기다리지 않았다).

- 병합된 워크트리 여럿. `web/apps/widget/public/` 을 다시 만들 수 없는 것으로 판정했다. 위젯 빌드가 만드는 자리라 `RECREATABLE_*` 목록이 그것을 모르는 것으로 보인다(재지 않았다).
- pwsh 가 쥔 워크트리, 앱의 표지가 있는 워크트리, 병합되지 않은 브랜치.
- 임시 워크트리 `rerun-hidden-gr7n4xe7/m`. 그 자리에서 `feature/11-pilot-and-prereg` 세션이 프로세스를 거듭 띄워 끄지 않았다.
- 휴지통의 `.venv`. python pid 41176 이 쥐고 있었다.

## 결정

명세와 티켓이 정하지 않은 자리를 이 세션이 정했다.

- **422 와 429 는 교환을 대화에서 뺀다.** 요청은 부르는 쪽(`WidgetPage`)이 입력창에 넣는다. 422 의 안내와 429 의 기다림은 대화의 상태(`lib/conversation`)가 아니라 대화를 돌리는 훅(`useConversation`)의 상태다. 대화의 기억(이어 갈 실행, 읽기 영역)과 상관이 없고, 새 대화가 비우는 것도 아니기 때문이다.
- **기다림은 새 대화로 걷히지 않는다.** 서버는 상한을 대화와 상관없이 센다. 422 의 안내는 새 대화가 걷는다.
- **띠의 `role="status"` 틀은 늘 선다.** 띠가 없으면 위 테두리만 남아, 입력 자리(`form`)의 위 테두리를 대신한다. 처음부터 서 있어야 글이 바뀔 때 읽힌다.
- **띠의 숫자.** 보이는 남은 시간은 `aria-hidden` 이고, 같은 자리에 처음 시간을 `sr-only` 사본으로 둔다. 그래서 화면 읽기 프로그램은 띠가 설 때 문장 하나를 읽고, 시간이 다 되어 글이 바뀔 때 한 번 더 읽는다.
- **띠의 아이콘은 띄우지 않는다.** 디자인은 아이콘 위에 2px 를 두었지만, 작은 글자의 줄 높이가 16px 라 16px 아이콘은 그대로 첫 줄에 맞는다.
- **보내기 버튼의 자리를 잰다.** 05 는 칸 아래 글 한 줄(20px)만큼 버튼을 올렸다. 422 의 글은 400px 에서도 두 줄로 꺾여, 칸 묶음과 입력창의 아래 끝 사이를 `ResizeObserver` 로 재어 그만큼 올린다.
- **"다시 보내기"로 보낸 요청이 422·429 를 받아도 입력창의 글을 덮는다.** 명세가 "요청을 입력창으로 되돌리고"라고 정해, 쓰던 글이 있어도 되돌린 요청이 이긴다.
- **시작 항목 뒤에 결말 없이 끝난 스트림은 09 가 재접속으로 가를 때까지 500 행의 알림이다.**
- **`hourly_runs` 도 60초 아래면 초로 적는다.** 명세의 문장 틀은 "N분 뒤에"지만 "60초 이상이면 분으로 올려 적는다"를 60초 아래는 초라는 뜻으로 읽었다(셀프 리뷰 명세 축의 Nit 에서 적었다).
- **다시 시작한 대화는 교환이 비어도 대화 목록이다.** 그 시작이 422·429 로 입력창에 돌아와도 맨 위의 정보 알림이 남는다(셀프 리뷰 명세 축의 Minor 에서 정했다).

## 한 것

커밋하지 않았다. 티켓의 수용 기준은 검증 줄(61)을 빼고 모두 체크했다.

- `lib/limit.ts`(새것): `Retry-After` 를 읽고(없거나 숫자가 아니면 5초), 남은 초를 세고, 60초부터는 분으로 올려 적는다. 상한(`concurrent_runs`·`hourly_runs`·모름)마다의 문장과 다 됐을 때의 글.
- `api/runs`: 거절(`RunRejected`)이 상한 이름과 `Retry-After` 를 함께 든다.
- `lib/conversation.ts`: 결말에 401·404·409·처리하지 못한 것(`error`, 세 번째 거듭부터 "새 대화")을 더하고, 422·429 는 교환을 뺀다. 이어 가기가 두 번 404 면 같은 요청으로 다시 시작한다(`restarted`).
- `useConversation`: 이어 가기 404 는 1초 뒤 한 번 다시, 두 번째면 새로 시작한다. 시작 404 는 콘솔에 에이전트 이름과 함께 적는다. 422 는 안내를, 429 는 기다림을 세우고 요청을 입력창으로 돌린다. 기다림은 새 대화로 걷히지 않는다.
- 부품: 입력창 위의 띠(`molecules/ComposerBand`, 재접속 → 상한 → 승인의 차례로 하나만), 실패 알림(`organisms/FailureAlert`, 원인 아홉과 거절 여섯의 문구·버튼). `Composer` 는 띠와 422 의 안내, 잰 버튼 자리를, `Conversation` 은 알림과 다시 시작했다는 안내를 그린다. `WidgetScreen` 은 단계 상한 실패에서 입력창으로 포커스를 보낸다.
- 시험: `pages/WidgetFailures.test.tsx`(새것, 47건)와 `WidgetConversation.test.tsx` 의 상태 영역 둘. 스토리 `ComposerBand`·`FailureAlert`(새것)와 `Conversation`·`WidgetScreen` 의 새 이야기. 사진은 `organisms-conversation--failures-dark` 하나가 바뀌고 31장이 새로 섰다(`visual:widget:update` 30 통과).
- 이 세션이 고친 것: 띠가 늘 서면서 상태 영역이 둘이 되어 `WidgetConversation` 의 두 시험을 둘로 고쳤다. 남은 시간을 찾는 시험 도우미가 숨긴 아이콘을 먼저 집어 빈 글을 걸렀다. 05 의 한 줄만큼 올리기가 두 줄 글에서 16px 어긋나 재는 판으로 바꿨다.

## 변이

`.scratch/web-widget/probes/failures_mutations.toml` 의 14 개가 모두 기대대로다(13 개를 한 번에, 포커스 차례 변이 하나는 뒤에 따로 돌렸다). 칸 아래 글 한 줄만큼만 올리는 변이는 두 줄인 422 스토리에서 빨갛고 한 줄인 글자 수 스토리에서 초록이라(대조군), 빨강이 두 줄 때문이라는 것을 가른다.

## 인계

- 이 세션의 제목: `feature/07-widget-failures-and-rejections`.
- 셀프 리뷰 직전에 인계 계기가 왔다(컨텍스트 358,682 토큰). `/code-review` 의 단계는 밟지 않았다.
- 검증: 위젯 화면 동작 85·스토리 30, tsc·eslint·prettier, ruff 둘은 초록이었다. `run_checks.py` 는 인계하며 멈췄다(멈출 때까지 pre-commit 쪽 여덟은 통과였고 pytest·web 은 끝을 보지 못했다). 위젯 e2e 는 돌리지 않았다.
- 판단을 남긴 자리: "다시 보내기"가 422·429 를 받으면 입력창의 글을 덮는다(결정 7번째 줄). 거절을 되돌리는 쪽(`refuse`)이 끊긴 요청을 거르는 것은 시험이 없다. 나란히 도는 티켓 10 이 `useConversation` 을 고치면 겹칠 수 있다.
- 낸 지시문:

```
다음 작업: .scratch/web-widget/issues/07-widget-failures-and-rejections.md. 위젯의 실패와 거절(입력창 위의 띠 부품과 거절 알림)
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/web-widget/issues/07-widget-failures-and-rejections.md
브랜치: feature/07-widget-failures-and-rejections
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-24-12-widget-failures-and-rejections.md의 "## 인계"
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review, 고정점 origin/main, 명세 .scratch/web-widget/spec.md)부터 한다(docs/journal/2026-10-24-12-widget-failures-and-rejections.md). run_checks.py는 인계하며 멈춰 pytest·web의 끝을 보지 못했고 위젯 e2e는 돌리지 않았다. 티켓의 검증 줄과 Status done, 일지의 셀프 리뷰·"다음"이 남았다
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

- 제목을 `feature/07-widget-failures-and-rejections (인계함)` 으로 바꾸고, `run_checks.py` 를 멈추고, 워크트리 잠금을 풀었다.
- open-session을 부른다 2026-10-24T12:23:43Z

## 이어받은 세션

> 사용자: /implement .scratch/web-widget/issues/07-widget-failures-and-rejections.md (위 "인계"의 지시문. 셀프 리뷰부터, 범위는 PR과 병합까지)

워크트리 `07-widget-failures-and-rejections` 에 `EnterWorktree(path)` 로 들어왔다. origin/main 은 148652ef 그대로였다. 리뷰를 띄우며 함께 돌린 `run_checks.py` 는 리뷰 전의 작업 트리에서 열 검사가 모두 통과였다(pytest 442초, web-verify 439초).

## 셀프 리뷰

`/code-review`, base 148652ef(origin/main), 수정 13개, 커밋 0개, 미추적 40개(코드·시험·표·일지 9, 사진 31).

### 표준 축(sonnet·high)

- **Major. 변이 표의 빨강 기대 13 가운데 10에 표지(`expect_output`)가 없다.** `.claude/rules/probes.md` 첫 항목. 같은 디렉터리의 앞선 표는 모두 달았다. → 고친다. 변이를 손으로 넣어 실패 출력을 본 뒤, 고른 단언이 실패할 때만 나오는 문구로 고른다.
- **Minor. 프로브 README 에 `failures_mutations.toml` 의 줄이 없다**(`docs/agents/issue-tracker.md` 프로브 절). → 고친다.
- **Nit. `Composer` 의 `style={{ marginBottom: lift }}`**(`web-design.md` 의 이름 있는 단계). → 잰 값이라 인라인이라는 것을 주석에 더한다.
- **Nit. 시험 이름 `상한의 띠: 59초`**(`web-workspace.md` 의 행동을 말하는 문장). → 문장으로 고친다.
- 냄새 "limit 이 네 뜻"(Minor). → `useConversation` 이 돌려주는 `limit` 을 `wait` 로 바꾼다. `Composer`·`WidgetScreen` 이 이미 `wait` 로 받는다. 봉투의 `limit`(`LimitDetail.limit`, `LimitWait.limit`)은 계약의 필드 이름이고, 띠의 `limit` 칸은 명세의 "상한" 띠라 둔다.
- 냄새 Divergent Change(`Composer` 가 띠 문구를 엮는다). → 남긴다. `lib/limit.ts` 는 JSX 없는 규칙이고, 숫자를 `aria-hidden` 과 `sr-only` 로 가르는 것은 그리는 쪽의 일이다.
- 냄새: `attempt` 의 빈 `catch` 가 `dispatch` 까지 감싼다. → 남긴다. 05 의 판도 같은 범위(`for await` 와 `dispatch`)를 잡았고, 바뀐 것은 끊김을 `rejected(null)` 대신 `ended` 로 넘기는 것뿐이다. 둘 다 500 행의 알림이다.
- 냄새 `new RunRejected(null, undefined, { cause })`, `LimitWait.remaining` 이 `until` 에서 나온다(Nit). → 남긴다. 앞의 것은 호출이 둘뿐이고, 뒤의 것은 남은 초가 바뀔 때만 다시 그리려고 상태로 든다.
- 주장 "서버는 0 이상의 정수 초만 보낸다"가 느슨하다(서버는 1 이상, `limits.py` 35행). → "1 이상"으로 고친다. `"0"` 과 소수의 시험이 없다(Minor). → 시험 표에 더한다.
- 일지의 "`visual:widget:update` 30 통과"가 새 사진 31·바뀐 사진 1과 맞는지 볼 길이 없다(Nit). → 사진 비교를 다시 돌린 결과로 적는다.
- `refuse` 의 끊긴 요청 거르기에 시험이 없다(Minor). → 남긴다. 실행이 도는 동안에는 새 대화(`newConversationDisabled`)와 보내기·"다시 보내기"(`sendBlocked`)가 막혀, 끊는 길은 페이지를 떠나는 것(unmount)뿐이다. 그 뒤의 `setDraft` 는 화면에 아무것도 바꾸지 않는다.
- 1초 기다림 도중의 끊기에 시험이 없다(Minor, 규칙 9). → 시험은 남기지만, 기다림에서 끊겨 돌아오면 토큰을 다시 청하지 않고 멈추게 고친다. 지금 판은 끊긴 뒤에도 부모 창에 토큰을 한 번 더 청한다.
- `restarted` 가 다음 교환에도 남는다(Minor). → 남긴다. 그 알림은 다시 시작한 대화의 맨 위에 서는 것이라 새 대화까지 참이다. 교환이 비면 사라지는 것은 명세 축의 첫 지적으로 고친다.
- Nit. `FailureAlert` 의 주석이 `focusFor` 를 `organisms/Composer` 의 것으로 적었지만 `pages/WidgetScreen` 의 것이다. → 고친다.

### 명세 축(본 세션의 모델)

빠진 요구와 범위 넘침은 없다고 했다. 문구는 스크립트로 명세 원문과 맞대 모두 글자 그대로였고, `retryAfterSeconds`·`waitText`·`remainingAt`·`untilNextTick` 은 node 로 불러 경계가 맞았다.

- **Minor. 다시 시작한 뒤의 시작이 422·429 를 받으면 정보 알림이 사라진다.** 명세 "정보 알림 … 를 남긴 채 같은 요청을 시작으로 보낸다". 교환이 빠져 비면 화면이 `Welcome` 으로 바뀐다. → 고친다. `restarted` 이면 교환이 비어도 대화를 그린다. 실패하는 시험부터 쓴다.
- **Nit. `hourly_runs` 의 60초 미만을 초로 적는다.** 명세의 문장 틀은 "N분 뒤에"다. → 남긴다. 명세의 "60초 이상이면 분으로 올려 적는다"를 60초 아래는 초로 적는다는 뜻으로 읽었고 시험이 59초를 고정한다. 아래 "결정"에 더한다.
- **Minor. 09 티켓 11행이 `ended` 동작은 그 교환을 `rejected` 로 닫는다고 적어 거짓이 된다.** → 받는 쪽(09 티켓)을 고친다. `ended` 는 처리하지 못한 것(`error`)으로 닫고 셈을 올리며, 시작 항목 뒤의 끊김도 그 셈에 든다는 것을 적는다.
- **Nit. 미래형과 지금형이 남았다.** 05 티켓 7행("그동안 이 티켓은 … 그린다")·28행("07이 더한다"), 07 티켓 13행(실패 항목의 `cause` 와 `run_id` 가 지금 상태에 담기지 않는다고 적었다). web-widget 는 진행 중인 기능이라 done 인 05 티켓도 살아 있는 문서다(`operations.md` 문서 위치). → 고친다.
- **Nit. "알림이 띠보다 먼저 읽힌다"를 고정하는 시험이 없다.** → 남긴다. 차례는 역할이 정한다. WAI-ARIA 1.2 는 `alert` 를 암묵의 `aria-live="assertive"`, `status` 를 `"polite"` 로 정한다(https://www.w3.org/TR/wai-aria-1.2/#alert, #status). 시험은 두 역할을 본다.

### 반영

- **고친 것.** 변이 표의 표지 열(변이를 스크래치 스크립트로 하나씩 넣어 실패 머리를 보고 골랐다. 새 대화 뒤의 띠를 보는 단언은 앞의 `waitFor` 와 같은 문구를 찍어, 띠의 문장 전체를 보는 단언으로 바꿨다), 다시 시작한 대화의 빈 교환(`WidgetScreen`, 시험 둘을 먼저 빨갛게 봤다), `useConversation` 의 `limit` → `wait` 와 `RunRejected.limit` → `detail`, 1초 기다림에서 끊기면 멈추기(`sleep` 이 참·거짓을 돌려준다. 같은 반복의 앞 확인이 `signal.aborted` 를 좁혀 둬 바로 다시 보는 확인을 ESLint 가 늘 거짓으로 봤다. 시험 하나와 변이 8번을 더했다), 상한 띠 시험의 이름과 `"0"`·소수 사례, 주석 셋(`limit.ts`, `FailureAlert`, `Composer`), 티켓 셋(05·07·09)의 문장.
- **PR 직전 리뷰에 밀 주장**(반영하며 새로 쓴 사실 문장, 원문).
  - `WidgetScreen.tsx` 머리: "다시 시작한 대화는 교환이 비어도(그 시작이 422·429 로 입력창에 돌아왔을 때) 대화 목록이다. 맨 위의 정보 알림을 남긴 채 보내기 때문이다(web-widget 명세 "요청이 거절될 때"의 이어 가기 404)."
  - `lib/limit.ts` 머리: "서버는 1 이상의 정수 초만 보낸다(`channel/http/limits.py`). HTTP 날짜 꼴은 읽지 않는다. 0 은 읽어 곧바로 다시 보낼 수 있다는 글을 보인다."
  - `FailureAlert.tsx`: "버튼이 없고 포커스가 입력창으로 간다(pages/WidgetScreen 의 `focusFor` 를 organisms/Composer 가 받는다)."
  - `Composer.tsx`: "잰 값이라 공통 크기의 이름 있는 단계가 아니라 인라인 `style` 로 준다."
  - `api/runs/index.ts` 의 `RunRejected.detail`: "상한의 종류와 `Retry-After`. 그것을 들지 않은 응답이면 둘 다 null 이다."
  - `useConversation.ts`: "기다리는 동안 끊겼으면 토큰을 다시 청하지 않는다.", `sleep`: "기다린다. 끝까지 기다렸으면 참이고, 끊으면 곧바로 거짓으로 돌아온다.", "이미 끊긴 신호에는 abort 가 다시 오지 않는다."
  - 09 티켓 11행: "스트림이 결말 없이 끝나면 지금은 `lib/conversation.ts`의 `ended` 동작이 그 교환을 처리하지 못한 것(`error`)으로 닫고 처리하지 못한 거절의 셈(`errorStreak`)을 하나 올린다(05가 정한 것 2를 07이 거절 표의 500 행으로 바꿨다). 읽는 도중에 끊긴 스트림도 `components/pages/useConversation.ts`의 `attempt`가 `ended`로 넘긴다. 그래서 시작 항목 뒤의 끊김도 그 셈에 들어, 세 번째로 거듭되면 알림에 "새 대화"가 붙는다."
  - 05 티켓 7행: "실패 원인마다의 알림과 거절의 표는 07이 들였고 … 07 전까지 이 티켓은 … 그렸고 … 그렸다." 28행: "상한의 기다림으로 막히는 것은 07이 더했다."
  - 07 티켓 13행: "05가 넘길 때 실패 항목의 `cause`와 `run_id`는 상태에 담기지 않았다."
  - 변이 표: 머리 주석의 "앞의 여덟은 화면 동작 테스트(`widget-pages`), 뒤의 일곱은 위젯 스토리", "빨강을 기대한 열넷은 모두 고른 단언이 빨개졌다는 것을 그 단언의 실패 머리나 값이 든 줄(`expect_output`)로 본다.", "첫 판은 열셋 가운데 셋에만 표지가 있어", 12번 "보내기의 아래 끝이 입력창보다 16px(두 줄 글의 둘째 줄) 낮다", 14번 "20px(칸과 글 사이 4px 와 글 한 줄 16px) 낮다", 8번 괄호의 이어 가기 수 단언(PR 직전 리뷰가 거짓으로 짚어 고쳤다, 아래 "PR 직전 리뷰").
- **사진 비교의 "30 통과"(표준 축 Nit).** 다시 돌린 `visual:widget` 이 "30 passed" 였다. 30 은 Playwright 시험의 수이고 시험 하나가 스토리 하나의 그려진 모드를 모두 찍어, 정답 사진의 장수와 다르다. 어긋남이 아니다.
- **남긴 것과 이유.** 위 두 축의 "남긴다" 줄이다(Divergent Change, 빈 `catch`, `RunRejected` 의 인자 차례, `LimitWait.remaining`, `refuse` 의 끊긴 요청 시험, `hourly_runs` 의 초, 알림과 띠의 읽는 차례).
- **다시 돌린 명령.** 위젯 화면 동작·스토리 121(91·30), 위젯의 eslint·tsc·prettier, ruff 둘, `visual:widget` 30, 위젯 e2e 6 이 모두 초록이었다. 손으로 치는 다섯은 커밋의 pre-commit 으로 갈음한다.
- **나란히 도는 티켓 10.** 커밋 직전의 `sibling_overlap.py` 가 번호 겹침은 없고, `10-widget-element-embed` 워크트리가 같은 파일 셋(`api/runs/index.ts`, `WidgetPage.tsx`, `useConversation.ts`)을 고친다고 알렸다. 나중에 병합하는 쪽에서 글자 충돌 후보다.

### 첫 커밋이 막힌 것

- 첫 커밋 시도의 pre-commit 에서 검사 열(pytest 531초, web-verify 394초 포함)과 마크다운 표·줄 구분 문자는 통과했고, ruff 둘은 `.py` 가 없어 `Skipped` 였다. 변이 표 검사(`tools/mutate.py --staged`)가 앞 티켓의 변이 표 둘에서 원문 일곱이 깨졌다고 막았다. `conversation_mutations.toml`(티켓 05)의 여섯은 이 티켓이 거절의 결말을 상태 코드로 가르고(`settleError`, `withdraw`), 실패 항목에 원인과 실행 식별자를 담고, 보내기 버튼을 잰 값으로 올리고, "다시 보내기"를 `FailureAlert` 로 옮긴 데서 났다. `widget_app_mutations.toml` 의 하나는 다크 모드 스토리(`LimitedHourlyWideDark`)를 더해 같은 줄이 둘이 된 데서 났다.
- 일곱 모두 같은 뜻의 변이를 지금 코드에 다시 걸었다. 결말 없이 끝난 스트림의 시험은 `WidgetFailures.test.tsx` 의 거절 표로 옮겨 가, 그 변이는 `tests` 도 바꿨다. 다시 건 변이를 도구로 돌리니 `conversation_mutations.toml` 의 여섯(7·8·9·16·22·26)과 `widget_app_mutations.toml` 의 하나(26)가 모두 표지까지 기대대로였다. 뒤의 것의 필터 `wide-dark 를` 은 이제 사진 시험 넷을 고르지만, 변이가 바꾸는 스토리는 `WideDark` 하나라 빨강도 하나였다.
- 인용 대조 경고 일곱 가운데 여섯을 고쳤다. 넷은 리뷰 지적이나 이미 고친 옛 문장을 따옴표로 적은 것이라 따옴표를 뗐고, 둘은 변이 표 머리 주석을 줄여 옮긴 것이라 원문 그대로 고쳤다. 남은 하나(`lib/limit.ts` 머리의 인용)는 원문과 같고, 원문이 주석의 줄바꿈으로 갈려 있어 검사가 맞추지 못한다.
- 다시 친 커밋의 pre-commit 은 검사 열(pytest 343초, web-verify 335초 포함)과 변이 표 검사까지 모두 통과했다. ruff 둘은 `.py` 가 없어 `Skipped` 였고, 이 커밋은 `.py` 를 고치지 않았다. 셀프 리뷰를 반영한 커밋은 여기서 들었고 푸시는 하지 않았다.

## 둘째 인계

이 세션(제목 `feature/07-widget-failures-and-rejections`)은 컨텍스트가 인계 문턱을 넘은 채 `커밋 뒤` 경계에 와서 넘긴다. 첫 커밋 시도에서도 계기가 왔지만 그 커밋이 pre-commit 에 막혀 경계가 아니었다(next-session "인계할 때" 1). 이 세션이 번복하거나 고친 것은 위 "첫 커밋이 막힌 것"의 변이 표 둘과 일지의 인용이다.

```
다음 작업: .scratch/web-widget/issues/07-widget-failures-and-rejections.md. 위젯의 실패와 거절(입력창 위의 띠 부품과 거절 알림)
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/web-widget/issues/07-widget-failures-and-rejections.md
브랜치: feature/07-widget-failures-and-rejections
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-24-12-widget-failures-and-rejections.md의 "## 둘째 인계"와 "### 반영"의 "PR 직전 리뷰에 밀 주장"
이어받을 상태: 인계: 커밋 뒤. 셀프 리뷰를 반영한 변경을 한 커밋으로 들었고 푸시하지 않았으며 PR은 없다. 남은 단계는 차례로 PR 직전 리뷰(docs/constitution/operations.md 리뷰 파이프라인 2. 일지의 "PR 직전 리뷰에 밀 주장"을 브리프에 싣는다)와 그 반영 커밋, failures_mutations.toml의 고르지 않은 전체 실행 한 번, .scratch/web-widget/probes/README.md에 그 표의 줄, 티켓 07의 검증 체크박스와 Status done, 일지의 "다음", /git-pr로 PR을 열고 봇 회차, next-session "워크트리에서 병합할 때"로 병합이다(docs/journal/2026-10-24-12-widget-failures-and-rejections.md)
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

- 제목을 `feature/07-widget-failures-and-rejections (인계함)` 으로 바꿨다. 띄운 백그라운드 작업은 모두 끝나 멈출 것이 없었고, 워크트리 잠금은 이미 풀려 있었다(`is not locked`).
- open-session을 부른다 2026-10-24T13:31:45Z

## 셋째 세션

> 사용자: /implement .scratch/web-widget/issues/07-widget-failures-and-rejections.md (위 "둘째 인계"의 지시문. PR 직전 리뷰부터, 범위는 PR과 병합까지)

워크트리 `07-widget-failures-and-rejections` 에 `EnterWorktree(path)` 로 들어왔다. origin/main 은 148652ef 그대로라 합칠 것이 없었다.

## PR 직전 리뷰

CodeRabbit CLI 는 `coderabbit auth status` 가 `Plan: Free`, `Seat: not assigned` 라 돌지 못했다. 대체 둘(`operations.md` 리뷰 파이프라인 2)을 나란히 돌렸다. 기준은 148652ef 이고 커밋 85f9ddbb 를 봤다.

- **보안(`/security-review`).** 지적 없음. 서버가 준 값(`limit`, `Retry-After`, `run_id`, `cause`)은 정한 표에서 고른 문장이나 React 텍스트로만 그려지고, 토큰은 `location.origin` 에만 가며, 시작 404 의 `console.error` 는 에이전트 이름만 적는다.
- **버그·성능(`bug-perf-review`, sonnet).** 유효 Minor 둘, 보류 하나, 오탐 셋. 밀 주장 열 가운데 아홉은 맞았고 하나(변이 표 8번의 괄호)가 어긋났다.
  - 유효 Minor. 실패한 교환의 "다시 보내기"가 422·429 를 받으면 쓰던 글을 덮는데, `WidgetPage.tsx` 의 주석은 "쓰던 글은 그대로 둔다"고 적었다. → 주석을 고쳤다. 동작은 둔다. 명세 표의 422·429 행이 시작과 이어 가기 모두 "요청을 입력창으로 되돌리고"라고 정해 "다시 보내기"를 가르지 않고, 이 일지의 결정 7번째 줄이 그것을 골랐다. 바꾸려면 명세를 고쳐야 한다(리뷰의 제안은 "다시 보내기"는 되돌리지 않는 것이다. 실패한 교환과 그 버튼이 남아 요청을 잃지 않는다). PR 체크리스트에 적는다.
  - 유효 Minor. 변이 표 8번의 괄호가 이어 가기 수의 뒤 단언도 빨개지는 것처럼 적었다. 그 변이는 토큰을 한 번 더 청한 뒤 `signal.aborted` 확인에서 돌아와 `attempt` 에 닿지 않아 이어 가기의 수는 1로 남는다(`useConversation.ts` 의 `run`). → 괄호를 그 동작대로 고쳤다.
  - 보류. 띠의 `role="status"` 는 `aria-atomic` 이 기본(참)이고 안의 `aria-hidden` 숫자가 매초 바뀐다. 화면 읽기 프로그램이 숨긴 숫자의 변경에도 영역을 다시 읽는지는 코드로 닫히지 않는다. 시험은 `aria-hidden` 을 뗀 DOM 의 글만 본다. → 둔다. NVDA 같은 실제 화면 읽기 프로그램으로 한 번 재야 하고, PR 체크리스트에 적는다.
  - 오탐. 둘째 404 뒤 끊김을 보기 전에 토큰을 청하는 틈, `ResizeObserver` 의 반복 그리기와 정리, 매초의 다시 그리기와 타이머 정리.
- 고친 뒤 `tools/mutate.py --check` 로 표 셋(failures 15, conversation 26, widget_app 34)의 원문이 모두 한 번씩 있는 것을 봤다.
