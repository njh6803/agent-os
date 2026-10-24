# 2026-10-25 (01) 위젯의 승인 묻기(web-widget 08)

## 사용자 프롬프트

> 사용자: /implement .scratch/web-widget/issues/08-widget-approval.md (next-session 지시문. 새 세션이고 tidy-checkouts 를 먼저 돌고 EnterWorktree(08-widget-approval)로 들어간다. 브랜치 feature/08-widget-approval, 범위는 PR과 병합까지. 읽을 것은 일지 2026-10-24-15 의 "다음"과 "사진 비교의 흔들림". 티켓 10 을 다른 세션(feature/10-widget-element-embed)이 맡아 `api/runs/index.ts`·`WidgetPage.tsx`·`useConversation.ts` 에서 글자 충돌이 날 수 있다)

## 정리(tidy-checkouts)

주 체크아웃은 깨끗한 main 이라 `origin/main`(1ef75a12)으로 당겼다. 병합된 07 의 `worktree-07-widget-failures-and-rejections` 브랜치를 지우고 휴지통을 비웠다.

## 결정

명세와 티켓이 정하지 않은 자리를 이 세션이 정했다.

- **카드는 이름 "승인 묻기"의 묶음(`role="group"`)이다.** 화면 디자인은 이름 있는 `<section>`(영역)이었지만, 한 대화에 카드가 여럿 서면 같은 이름의 영역이 겹쳐 axe 의 landmark-unique 가 스토리에서 잡았다.
- **도구 줄은 카드 자리마다 잘라 시간 차례대로 그린다.** 카드마다 그때까지 끝난 도구 수(`after`)를 들고, 카드 사이의 도구 줄은 05 의 규칙대로 결말이 오면 저마다 접힌다.
- **멈출 때 부르는 중인 도구를 비우지 않는다.** 승인하면 그 도구가 불리므로, 결정이 닿은 뒤 진행 표시의 이름표가 그 도구의 이름이다(화면 디자인 mk-approval).
- **사유는 다듬지 않고 적은 그대로 보낸다.** 비었는지만 서버의 `str.strip()` 과 같은 글자(파이썬 `str.isspace()` 가 참인 29 글자, `lib/approval`)로 가른다. 다듬는 것은 서버다.
- **결정의 429 기다림은 새 대화가 걷는다.** 보내기의 기다림(07)은 서버가 대화와 상관없이 세므로 새 대화로 걷히지 않지만, 결정의 기다림은 걷힌 카드의 버튼을 막는 것뿐이라 남길 까닭이 없다. 띠의 문구는 기다림의 쓰임(`purpose`)으로 "다시 보낼 수 있습니다"와 "다시 고를 수 있습니다"를 고르고, 결정의 기다림이 다 되면 준비 문구 대신 승인 띠로 돌아간다.
- **409 의 다시 구독.** 아무것도 없이 닫히면 충돌 알림("결정을 보내지 못했습니다."), 구독이 거절되거나 항목은 왔지만 결정 항목이 없으면 처리하지 못한 것이다.
- **404 뒤의 "다시 붙을 실행을 비운다".** 다시 붙을 실행은 새로 고친 뒤 다시 붙는 상태(티켓 09)라 지금 상태에는 그 칸이 없다. 교환의 결말을 `expired` 로 두어 멈춘 교환이 아니게 하는 것으로 이 티켓의 몫을 닫았다. 09 가 저장할 때 `expired` 를 비우는 쪽에 넣는다.
- **포커스는 스크롤 없이 옮긴다**(`preventScroll`). 포커스가 대화를 위로 굴리면 대화가 끝을 보고 있지 않은 것이 되어 결정 뒤의 출력으로 내려가지 않는다. 사진에서 처음 봤다. 이미 결정된 채 그려진 카드는 포커스를 가져가지 않는다.
- **결정을 보내는 동안 "새 대화"를 막는다.** 결정을 기다리기만 할 때는 열려 있다(티켓).

## 한 것

- `lib/approval.ts`(새것): 인자의 글(`JSON.stringify(args, null, 2)`)과 사유가 비었는지.
- `lib/chars.ts`(새것): 입력창과 사유가 함께 쓰는 글자 수 표시(90% 의 센 수, 넘은 글). `Composer` 의 셈을 옮겼다.
- `lib/conversation.ts`: 교환의 승인 묻기 목록, 결정 중·거절·`expired` 동작, `waitingApproval`.
- `api/runs`: `sendDecision`(결정 경로)과 `subscribeRun`(`Last-Event-ID` 를 단 구독).
- `lib/limit.ts`: 기다림의 쓰임(`send`·`decide`)과 문장 끝.
- `useConversation`: `decide`. 404 는 1초 뒤 한 번 다시, 409 는 다시 구독, 429 는 결정의 기다림.
- 부품: `organisms/ApprovalCard`(새것). `Conversation` 이 카드를 도구 줄 사이에 그리고, `Composer` 가 승인 띠를, `WidgetScreen` 이 결정 버튼의 막음을, `WidgetPage` 가 "새 대화"의 막음을 잇는다.
- 시험: `pages/WidgetApproval.test.tsx`(새것, 36건), `WidgetConversation.test.tsx` 의 05 틈 시험을 이 티켓의 규칙으로 바꿈. 스토리 `ApprovalCard`(새것, 여섯)와 `WidgetScreen` 의 Paused·PausedLimitedWide. 사진 15장이 새로 섰다.

## 변이

`.scratch/web-widget/probes/approval_mutations.toml` 16.
열여섯 모두 기대대로였다(도구가 판정했다). 표지는 변이를 스크래치 스크립트로 하나씩 넣어 실패 출력을 손으로 본 뒤 골랐다(프로브 README 행). 표를 쓰며 시험이 없던 두 규칙에 시험을 더했다. "승인이 닿으면 진행 표시의 이름표가 멈췄던 도구의 이름이다"와 "결정의 429 를 기다리는 동안 '새 대화'를 누르면 그 기다림이 걷혀 바로 요청을 보낼 수 있다"다.

## 이 세션이 고친 것

- 카드를 처음에 `<section>` 으로 지었다가 axe 의 landmark-unique 로 `role="group"` 으로 바꿨다.
- 포커스가 대화를 위로 굴려 끝에서 벗어나는 것과, 이미 결정된 카드가 포커스를 가져가는 것을 사진에서 보고 고쳤다(`preventScroll`, 처음 그릴 때 기다리던 카드만 포커스를 옮긴다).

## 검사(인계 전까지)

- 화면 동작 시험 `widget-pages` 125 통과(시험 둘을 더하기 전). 승인 시험 파일만 다시 돌려 36 통과.
- 사진 비교: 새 정답 15장을 눈으로 봤고, `-g approvalcard --repeat-each=10` 60 통과, `-g widgetscreen--paused --repeat-each=10` 20 통과.
- 위젯 e2e 6 통과. ruff 둘 깨끗.
- `tools/run_checks.py` 는 띄웠다가 인계하며 멈췄다. 새 세션이 셀프 리뷰를 반영한 뒤 돌린다.

## 셀프 리뷰(이어받은 세션)

`/code-review` 를 기점 `origin/main`(1ef75a12)에서 돌렸다. 파일 15개를 고쳤고 커밋은 0, 미추적 파일은 22개(사진 15장 포함)다. 두 축 모두 Critical·Major 가 없었다.

고친 것:

- 명세(Minor): 409 뒤 다시 구독이 401 을 받으면 "요청을 처리하지 못했습니다."가 떴다. 명세 "넷 모두" 행의 401 대로 "로그인 정보를 받지 못했습니다."로 가게 `follow()` 를 고쳤다. 시험을 먼저 더해 빨강을 봤다(시험 37건).
- 표준(Minor): 결정의 타입 이름 `Verdict` 가 `CONTEXT.md` 가 피하라는 "판정"이라 용어집의 `Decision` 으로 바꿨다. 변이 표의 원문 하나를 함께 고쳤다(`--check` 16 모두 한 번씩).
- 두 축(Nit): 주석의 `pauseIndex` 를 실제 필드 `pause_index` 로, `subscribeRun` 의 "`lastEventId` 를 주면"(필수 인자)을 고쳤다. `useConversation` 머리의 옛 문장(열린 스트림을 끊는 것이 새 대화와 페이지를 떠나는 것뿐이라는 문장)은 닫힌 주장이라 새 요청과 결정도 끊는다고 고쳤다. `ComposerBand` 와 그 스토리 머리의 "08 이 채운다"는 미래형을 완료형으로 바꿨다.

다시 돌린 명령(리뷰 반영 뒤):

- ruff 둘 깨끗.
- `tools/run_checks.py`: web-verify 만 Prettier 로 빨갰다(이전 세션이 고친 `WidgetScreen.stories.tsx` 의 서식). `prettier --write` 로 맞춘 뒤 `pnpm -C web verify` 를 다시 돌려 822 통과. 나머지 검사(pytest, pyright 둘, 경계, 지침, 타입 우회, 훅, zizmor, 티켓)는 첫 바퀴에서 통과했다.
- 위젯 e2e 6 통과.
- `-m llm_widget` 1 통과. LLM 토큰 합계 6,555(입력 6,483, 출력 72), 트레이스 1개, 모델 호출 2건.
- 첫 커밋을 pre-commit 의 변이 표 검사가 막았다. 이 티켓이 옮긴 코드(`Composer` 의 셈을 `lib/chars` 로, `useConversation` 의 `reset` 과 `NOT_FOUND_RETRY_MS`)를 05·07 의 변이 표 다섯 항목이 옛 원문으로 겨눴다. 원문을 지금 코드로 고치고(이어 가기의 1초 기다림은 결정 쪽과 모양이 같아 앞의 주석 줄까지 원문에 넣었다), 다섯을 다시 돌려 모두 기대대로 빨간 것을 봤다(`conversation_mutations.toml` 13·14·15, `failures_mutations.toml` 7·8).
- 사진 비교는 다시 돌리지 않았다. 반영으로 바뀐 것은 이름, 주석, 서식, 다시 구독의 401 갈래라 그림이 바뀌지 않는다. CI 의 `visual` 잡이 본다.

PR 직전 리뷰에 밀 주장(반영으로 새로 쓴 문장):

- "열린 스트림은 하나이고, 새 요청이나 결정이 앞의 것을 끊고 자리를 잇는다. 새 대화와 페이지를 떠나는 것도 그것을 끊는다."(`useConversation.ts` 머리)
- "구독이 401 이면 로그인 정보를 받지 못한 것이고, 그 밖의 거절은 처리하지 못한 것이다."(`follow()` 독스트링)
- "상한은 티켓 07, 승인 기다림은 08 이 채웠고, 재접속은 09 가 채운다."(`ComposerBand.tsx` 머리)

남긴 것과 이유(모두 표준 축의 판단 항목):

- `ApprovalCard` 의 알림 문구가 `FailureAlert` 의 문구를 되풀이한다. 두 부품의 알림 모양이 달라 문구만 모으는 자리를 정하는 일이 이 티켓 밖이다.
- 시험 도우미 `spoken()`·`advance()` 가 `WidgetFailures.test.tsx` 와 같다. 위젯 시험의 공통 도우미를 `testing/` 으로 올리는 정리는 따로 할 일이다.
- `purpose === "decide"` 를 네 자리가 따로 가르는 것, `WidgetScreen`→`Conversation` 으로 흐르는 결정 props 묶음, `readItems` 가 넘기기와 셈을 함께 하는 것, `useCallback` 의존성의 메모 효과, 이름의 Nit(`blankReason`, `tail`, `before`, `waited`)은 동작에 닿지 않아 남긴다.
- 일지의 "사용자 프롬프트"가 원문이 아니라 요약이라는 지적: 그 프롬프트는 next-session 지시문이라는 조작 지시이고, 메모리 규약은 조작 지시를 원문 기록에서 뺀다.

## PR 직전 리뷰

CodeRabbit CLI 는 `Seat: not assigned` 로 돌지 못해 대체 둘을 나란히 돌렸다(커밋 ca2774e6, 기점 origin/main 1ef75a12).

- `/security-review`: 발견 0건. 새 API 호출은 기존 `sendRun` 과 같은 클라이언트·헤더를 쓰고, 도구 이름·인자·사유는 React 텍스트로만 그려진다.
- `bug-perf-review`: 유효 0, 보류 1, 오탐 4. 밀 주장 셋은 모두 코드와 맞았고, `follow()` 독스트링이 토큰을 받지 못한 경우를 말하지 않는다는 누락 하나를 짚었다.
  - 고친 것: `follow()` 독스트링을 "토큰을 받지 못하거나 구독이 401 이면 로그인 정보를 받지 못한 것이고, 그 밖의 거절은 처리하지 못한 것이다."로 고쳤다.
  - 보류(Minor): 409 뒤 다시 구독이 404 로 거절되면 "요청을 처리하지 못했습니다."가 서고 카드가 다시 결정을 받는다. 명세의 "구독 404" 행은 새로 고친 뒤 다시 붙는 구독(티켓 09)의 행이고, 티켓 08 의 409 행은 따라가기와 아무것도 없이 닫힘만 정한다. 그 상태에서 다시 고르면 실행이 없어 결정이 404 를 두 번 받아 "이 승인 묻기는 더 이상 받을 수 없습니다."로 정리된다. 고치지 않고 PR 체크리스트에 적는다.

## 인계

이 세션의 제목은 `feature/08-widget-approval` 이었다. 컨텍스트가 문턱을 넘은 채 `셀프 리뷰 직전` 에 와서 인계한다. 셀프 리뷰(`/code-review`)는 하지 않았다.

### 인계 지시문

```
다음 작업: .scratch/web-widget/issues/08-widget-approval.md. 위젯이 승인 묻기를 대화 안에서 묻고 답을 보낸다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/web-widget/issues/08-widget-approval.md
브랜치: feature/08-widget-approval
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-25-01-widget-approval.md
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review, 기점 origin/main)부터 한다. 구현·시험·스토리·사진 정답·변이 표(16 모두 기대대로)·티켓 체크박스(검증 줄 빼고)·일지 초안까지 했다. tools/run_checks.py 는 인계하며 멈춰 아직 결과가 없다. 리뷰를 반영한 뒤 돌리고, 티켓 Status 를 done 으로 바꾼 뒤 커밋·PR·병합으로 간다. docs/journal/2026-10-25-01-widget-approval.md
확인할 선행 조건: 티켓 10(feature/10-widget-element-embed)이 .scratch/web-widget/probes/README.md, web/apps/widget/api/runs/index.ts, WidgetPage.tsx, useConversation.ts 를 함께 고쳐 나중에 병합하는 쪽에서 글자 충돌이 날 수 있다. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다
이번 요청 범위: PR과 병합까지
```

open-session을 부른다 2026-10-24T16:40:18Z

## 인계(둘째 세션)

이 세션은 첫 인계 지시문(`인계: 셀프 리뷰 직전`)으로 열렸고 제목은 `feature/08-widget-approval` 이었다. 셀프 리뷰 반영, 검증 명령, 커밋 둘(ca2774e6, accbf49c), PR 직전 리뷰(위 절)까지 했다. 컨텍스트가 문턱을 넘은 채 `커밋 뒤` 에 와서 인계한다. 둘째 커밋(accbf49c)의 pre-commit 은 모두 통과했다. 아직 푸시하지 않았고 PR 도 없다.

### 인계 지시문

```
다음 작업: .scratch/web-widget/issues/08-widget-approval.md. 위젯이 승인 묻기를 대화 안에서 묻고 답을 보낸다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/web-widget/issues/08-widget-approval.md
브랜치: feature/08-widget-approval
모델: Opus 5.5 / medium. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-25-01-widget-approval.md
이어받을 상태: 인계: 커밋 뒤. 셀프 리뷰 반영·검증 명령·티켓 done·커밋 둘(ca2774e6, accbf49c)·PR 직전 리뷰(security-review 0건, bug-perf-review 유효 0)까지 했다. 남은 것은 푸시, PR 열기(/git-pr. 체크리스트에 CodeRabbit CLI 좌석 미배정으로 대체 둘을 돌린 것과 보류 1건 — 409 뒤 다시 구독의 404 — 을 적는다), 봇 회차, 병합이다. 사진 비교는 로컬에서 다시 돌리지 않았고 CI의 visual 잡에 맡긴다. 일지의 회고와 "다음"은 아직 없다. docs/journal/2026-10-25-01-widget-approval.md
확인할 선행 조건: 티켓 10(feature/10-widget-element-embed)이 .scratch/web-widget/probes/README.md, web/apps/widget/api/runs/index.ts, WidgetPage.tsx, WidgetScreen.tsx, useConversation.ts 를 함께 고쳐 나중에 병합하는 쪽에서 글자 충돌이 날 수 있고, 그쪽 일지 2026-10-25-02 가 이 브랜치의 일지 번호보다 뒤라 번호는 겹치지 않는다. 병합은 이 워크트리 사본의 next-session "워크트리에서 병합할 때"를 Read로 열어 따른다
이번 요청 범위: PR과 병합까지
```

open-session을 부른다 2026-10-24T17:34:10Z

## PR 과 봇 회차(셋째 세션)

인계 기록을 커밋(1181b5f2)하고 PR #385 를 열었다. 첫 회차에서 검사는 모두 초록이었고, CodeRabbit 과 claude-review 가 리뷰했다.

- CodeRabbit(Minor): 변이 1의 표지가 시험 이름이라, Vitest 가 실패한 파일의 트리 줄(`✓ 이름`)에 통과한 시험 이름도 찍어 표지가 되지 못한다. 변이를 손으로 넣어 출력을 보니 맞았다(트리 줄 `× 이름` 과 실패 머리 `FAIL … > 이름` 둘 다에 이름이 있다). 표지를 실패 머리에만 나오는 `> 이름` 꼴로 바꾸고 변이 1을 도구로 다시 돌려 기대대로 빨간 것을 봤다. 표의 다른 표지 열다섯은 단언의 실패 문구라 같은 모양이 아니다.
- claude-review(Minor): `decide` 의 `useCallback` 의존 `waiting` 이 렌더마다 새 객체라 메모가 값을 하지 못한다. 결정을 받을 수 있을 때만 값이 있는 원시값 `pauseId` 로 좁혔다. 그 코드를 겨누던 변이 2의 원문을 고치고 다시 돌려 기대대로 빨간 것을 봤다.
- claude-review(Minor, 보류): `run()`·`runDecision()`·`follow()` 가 토큰 받기·끊김 확인·상태 코드 뽑기·`readItems` 의 골격을 되풀이한다. 티켓 09(재접속)가 네 번째 구독을 더하므로 그 티켓에서 함께 모은다(아래 "다음").
- claude-review(Minor, 보류): 알림 문구와 시험 도우미의 중복. PR 본문의 "남긴 위험"에 이미 적었고 세 번째 쓰임이 생기면 모은다.
- claude-review(Nit 둘, 보류): `updateWaiting` 의 `null` 결말과 `status === 429 && instanceof` 의 겹침. 동작에 닿지 않는다.

둘째 회차(adaa8f3b)는 CI 의 `python` 잡이 이 PR 이 건드리지 않은 `tests/tools/test_rerun_session.py` 의 `test_자식의_표준_입출력이_없으면_명령_줄을_본_뒤_끄고_예외를_올린다` 하나로 빨갰다(`argv` 가 `None`, 5589 통과). 바로 앞 헤드(1181b5f2)에서는 같은 잡이 초록이었다. 대기열 306 이 받아들여 닫은 종류(부하에서만 빨간 시간 시험)의 새 사례라 회차를 더하지 않고 여기에만 적고, 이 일지를 푸시해 다시 돌린다. CodeRabbit 은 이 회차에 한도에 걸려 리뷰하지 않았다.

## 회고

이 일지의 세 세션(구현, 셀프 리뷰, PR)을 함께 봤다. 후보 일곱, 승인 1(회차로 셈), 기각 6, 넘김 0.

- **승인(회차로 셈).** 변이 1의 표지를 시험 이름으로 골라, 통과한 시험도 Vitest 의 트리 줄에 이름이 찍혀 표지가 되지 못했다. 구현 때 실리는 `.claude/rules/probes.md` 첫 항목(고른 단언이 실패할 때만 나오는 문구, 고르기 전에 출력을 본다)을 어겨 PR 의 CodeRabbit 이 잡았다. 같은 일(표지를 시험 이름으로 고름)을 처방한 열린 행 417 에 회차를 더했다(290 의 4회차). 417 의 처방(표지가 시험 파일의 원문에 글자 그대로 있으면 `--check` 가 알린다)이 Vitest 의 시험 이름도 잡는다. 회차 3 이상이라 chore 배치의 계기다.
- 기각(이미 있는 검사가 그 자리에서 잡았다): 카드의 `<section>` 이 겹치는 영역을 axe 의 landmark-unique 가 잡음, 포커스가 대화를 굴린 것을 사진 비교에서 봄, 옮긴 코드를 겨누던 05·07 변이 원문을 pre-commit 의 변이 표 검사가 막음, `WidgetScreen.stories.tsx` 의 서식을 Prettier 가 잡음, `cd web` 을 훅이 막음, git 이 든 복합 명령을 워크트리 가드가 거부함.

## 다음

- 티켓 09(`.scratch/web-widget/issues/09-widget-storage-and-reconnect.md`)가 08 의 병합으로 막힘이 풀린다. 티켓 10 은 다른 세션이 맡고 있다.
- 09 에 넘긴 것 셋. ① `useConversation.ts` 의 `run()`·`runDecision()`·`follow()` 가 같은 골격(토큰 받기, 끊김 확인, 상태 코드 뽑기, `readItems`)을 되풀이한다. 09 가 재접속 구독을 더하면 네 번째가 되니 그때 모은다(PR #385 claude-review). ② 404 뒤 교환의 결말을 `expired` 로 둔 것은 "다시 붙을 실행을 비운다"의 대신이다. 09 가 저장할 때 `expired` 를 비우는 쪽에 넣는다. ③ 409 뒤 다시 구독이 404 로 거절되면 "요청을 처리하지 못했습니다."가 서고 카드가 다시 결정을 받는다(PR 본문의 보류). 09 의 "구독 404" 행을 지을 때 이 갈래도 그 행을 따를지 본다.
