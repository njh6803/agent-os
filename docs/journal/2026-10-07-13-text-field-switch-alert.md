# 2026-10-07 (13) design-system 티켓 04: 글 입력·스위치·알림

일지 2026-10-07-03의 "다음"으로 연 새 세션이다. 03(상태 배지·진행 표시·카드)과 나란히 여는 둘 가운데 둘째라
`tidy-checkouts`는 돌지 않았다(첫 세션의 몫). 지시문대로 `EnterWorktree`로 `.claude/worktrees/04-text-field-switch-alert`에
들어가 origin/main(`49d9630`)에서 `feature/04-text-field-switch-alert`를 땄다. 순번은 main의 09, 나란히 도는
`tidy-checkouts-tool` 워크트리의 10, 주 체크아웃에서 커밋 전인 11(`checkout-persist-credentials`), 형제 03의 12 다음이라
13이다.

## 이 세션이 정한 것

티켓 파일의 "이 티켓이 정한 것" 절이 원천이고 여기는 근거다.

- **글 입력의 props는 변형마다의 유니온이다.** 01의 규칙은 나머지 속성을 입력 요소에 넘기라고 하는데 그 요소가 변형마다
  다르다. 유니온의 나머지(`...control`)를 `control.variant === "multi"`로 좁힌 뒤 각 가지에서 `variant`를 꺼내 크기 클래스를
  고르는 데 쓰므로 쓰지 않는 변수 없이 `variant`가 DOM에 새지 않는다. 스토리는 두 변형을 함께 그릴 때 둘째 칸의 props를
  글자 그대로 적었다(args를 펼쳐 변형을 바꾸면 유니온의 짝이 깨진다). 한 줄 쪽의 `rows?: never`는 셀프 리뷰 뒤에 더했다
  (아래).
- **오류가 도움말의 자리를 차지한다.** 디자인 파일의 `fItem`이 `help: inv ? <오류> : <도움말>`로 한 줄을 그린다. 라벨은
  `<label for>`로 잇는다. 디자인 파일처럼 도움말까지 라벨 안에 두면 도움말이 이름에 섞이고 `aria-describedby`로 한 번 더
  읽힌다.
- **쓸 수 없는 칸의 도움말은 `muted`, 자리 글자는 `disabled-text`다.** 처음에 디자인 파일대로 도움말을 `disabled-text`로
  칠하자 axe가 `#888682`/`#f4f3f3` 3.28:1로 실패시켰다(axe는 쓸 수 없는 조작 요소와 그 라벨만 뺀다). 자리 글자는 처음
  `muted`였는데 쓸 수 없는 다크 사진에서 넣은 글보다 밝아 쓸 수 있는 칸처럼 보였다(손으로 봤다). 스토리에
  `getComputedStyle(field, "::placeholder")`의 단언을 먼저 더해 `rgb(101, 99, 95)`가 `rgb(136, 134, 130)`이 아니라고 빨간
  것을 본 뒤 고쳤다.
- **"선택"은 공백 하나와 `inline-block`의 `muted` 글자다.** `<span> 선택</span>`으로 두자 이름이 "플러그인 이름선택"이었다
  (스토리 테스트의 역할 목록). 접근 이름 계산은 `inline`이 아닌 자식의 앞뒤에만 공백을 넣는다. 처음에는 쓸 수 없음에서
  `disabled-text`로 칠했는데 디자인 파일은 늘 `muted`라 셀프 리뷰 뒤에 따랐다.
- **스위치는 라벨의 `group`으로 올림·누름을 칠한다.** 라벨 전체가 누르는 곳이라 글자 위에서도 트랙이 바뀌어야 한다.
  `group` 낱말 자체에는 규칙이 없지만 판정 함수 `selects`가 중첩 규칙의 `:where(.group)`을 찾아 afterEach를 지났다.
  이름은 라벨 하나(`aria-labelledby`)이고 상태 글은 `aria-hidden`이다. 라벨이 상태 글까지 감싸므로 그대로 두면 이름이
  켜짐·꺼짐과 함께 바뀐다.
- **알림의 닫기 버튼은 01의 아이콘 버튼이다.** 32px이 20px 제목 줄보다 높아 `-my-1 -mr-2`(간격 단계의 음수)로 내민다.
  위젯 머리의 닫기 버튼이 오른쪽 8px인 것(디자인 파일 04절)과 맞췄다. 본문과 `actions` 사이는 디자인 파일 03.2의 10px이
  간격 단계에 없어 12px이다.
- **실제 입력.** 스위치의 두 스토리(`Off`, `On`)는 `checked`를 넘긴다. 스스로 상태를 드는 스토리를 쓰면 누름을 놓아 생긴
  click이 켜고, 그 뒤의 포커스 사진이 다른 상태를 찍는다. 켜고 끄는 확인은 스스로 상태를 드는 `Toggle`이 한다.
- **글을 넣는 확인은 `Typing`으로 뺐다.** 글 칸은 어떻게 포커스되든 `:focus-visible`이라, 기본 그림의 스토리가 글을 넣고
  끝나면 칸에 링이 남는다.

## 정적 빌드의 play에서 `userEvent`가 비어 있다

처음 만든 사진 가운데 `molecules-textfield--typing`에 넣은 글이 없었다. 호스트 chromium으로 정적 빌드를 같은 route로 여는
탐침(프로브 `.scratch/design-system/probes/static_play.mjs`로 커밋했다)을 돌리자 콘솔에 `TypeError: n.type is not a function`이
났고 `isSecureContext`가 `false`, `navigator.clipboard`가 `undefined`였다. 같은 프로브로 01의 `atoms-button--primary`도
`n.click is not a function`에서 멈춘 것을 봤다. 설치본 `storybook/dist/csf/index.js`의 `enhanceContext`가
`navigator.clipboard`가 있을 때만 `context.userEvent`를 채우고, `dist/preview/runtime.js`는 play가 errored면 afterEach를
건너뛴다(둘 다 코드를 읽었다). 그래서 사진은 늘 play의 첫 `userEvent` 전 그림이다. 출처를 보안 맥락으로 바꾸면 기존 사진이
바뀌므로 그대로 두고 `visual/storybook.ts`의 주석에 적었다. 02 일지는 공문 포커스 사진에 링이 없던 까닭을 정적 빌드의
`userEvent.tab()`이 `:focus-visible`을 걸지 않은 것으로 어림했는데, 실제로는 `tab()`이 불리지 못했다.

## 확인한 것

- **빨강 먼저.** 타입만 갖춘 빈 컴포넌트(`TextField`는 `aria-label`만 단 `<input>`, `Switch`는 맨 checkbox, `Alert`는 제목만
  든 `div`)로 스토리 24개 가운데 22개가 빨갰다. 실패는 찾는 역할·라벨이 없거나 값이 다른 것이었다. 초록이던 둘은 폭 320px
  스토리다.
- **변이.** `.scratch/design-system/probes/molecules_mutations.toml` 여덟이 모두 기대대로 빨갰다. 폭 320px 둘(도움말 줄과 알림
  본문에 `whitespace-nowrap`), 구현 뒤에 쓴 `Typing`(한 줄 칸이 빈 글을 넘김), 아이콘의 모양 비교 둘(실패 알림의
  `circle-minus`, 오류의 `info`), 셀프 리뷰가 더한 단언 셋(모두 `status`인 알림, 넘긴 `checked`보다 스스로 든 상태를 앞세운
  스위치, 닫기가 알림의 역할을 걷음)이다.
- **사진.** `pnpm -C web visual:update`가 처음 새 사진 67장을 썼고 기존 사진은 하나도 바뀌지 않았다(`git status`가 `??`뿐).
  쓸 수 없는 칸의 자리 글자를 고친 뒤 다시 돌리자 그 스토리의 둘만 다시 썼고, 셀프 리뷰 뒤의 `Combinations` 둘을 더해
  69장이다. 손으로 본 것: 오류, 선택, 쓸 수 없음 다크, 스위치의 쓸 수 없음·누름·켜짐 다크 포커스, 알림의 320px·경고 다크·
  닫기 올림·열두 조합, 글 입력의 포커스.

## 셀프 리뷰

`/code-review`(base `49d9630`, 바뀐 추적 파일 5, 커밋 0, 미추적은 molecules 폴더와 사진 67장, 변이 표, 일지)를 두 축 나란히
돌렸다. 소스가 든 변경이라 sonnet으로 내리지 않았다. 지적의 근거를 보고 아래처럼 갈랐다.

- **고친 것(표준 축).** Minor 다섯. `variant`를 뺀 한 줄 칸에 `rows`를 넘기면 타입 검사를 지나 `<input>`에 샜다(한 줄 쪽에
  `rows?: never`. `variant` 없음·`"single"`·`"multi"` 세 모양을 스크래치 파일로 tsc에 넣어 앞의 둘만 TS2322인 것을 손으로
  봤다). 프로브 README에 변이 표의 줄이 없었다. 티켓이 02 일지를 원문과 다르게 따옴표로 옮겼다. `storybook.ts`가 "play와
  afterEach가 끝날 때까지 기다린다"고 했는데 play가 errored면 afterEach를 건너뛴다(설치본 `dist/preview/runtime.js`를
  읽었다). 그 주석의 "정적 빌드를 열어 봤다"가 커밋하지 않은 탐침이었다(프로브 `static_play.mjs`로 커밋했다). Nit 넷. 스토리가
  lucide의 클래스로 아이콘을 단언했다(모양 비교 `iconShape`로). 자리 글자의 "넣은 글보다 밝았다"는 다크에서만 참이다.
  `Alert.md`가 디자인 파일의 "alert로 두어"를 바꿔 옮겼다. `fieldNamed`의 독스트링이 하는 일과 달랐다. smell은 포커스 링
  기대값의 되풀이(`expectedFocusRing`), `expectTone`의 원시 문자열(`AlertTone`, `IconName`), 이름 `own`·`look`·`stateOf`
  (`selfChecked`·`switchColors`·`stateTextOf`)를 고쳤다.
- **고친 것(명세 축).** README 트리에 `molecules/`가 없었다. 알림의 "톤 셋 × `actions`·`onClose`의 있음과 없음"이 열둘 가운데
  일곱이었다(`Combinations`). 쓸 수 없는 칸의 "선택"을 디자인 파일과 달리 `disabled-text`로 칠했다. `Alert.md`의 "화면이나"가
  원문에 없었다. 티켓과 일지가 같은 사건의 이름을 다르게 적었다. 부르는 쪽의 길 둘(넘긴 `checked`에 남는 스위치, 닫아도
  스스로 걷히지 않는 알림)을 테스트가 밟지 않았다.
- **고치다 만난 것.** `iconShape`를 처음 `react-dom/server`로 그리자 Vite가 그 의존성을 실행 도중 최적화하며 테스트를 다시
  불러와 `TextField.stories.tsx` 하나가 "Vitest failed to find the current suite"로 빨갰다. 다시 돌리면 지났지만 캐시가 없는
  CI에서 같을 수 있어 `react-dom/client`로 바꾸고, 이 워크트리의 Storybook 캐시(`web/node_modules/.cache/storybook`)를 지운
  실행에서도 재최적화 없이 지나는 것을 봤다.
- **틀린 지적.** 명세 축이 사진 비교의 셈을 63으로 냈다. 실제 입력의 새 항목을 여섯으로 셌는데 다섯이다(글 입력 둘, 스위치
  둘, 알림 하나).
- **남긴 것.** 명세 축의 "요구하지 않은 행동" 둘(스위치가 `checked` 없이 스스로 상태를 드는 것, `value` 없는 글 입력)은
  props 표의 기본값이 정하지 않은 쓰임이고 브라우저 기본 요소의 제어·비제어와 같은 모양이라 두었다(티켓의 결정 1·5).
  버튼·아이콘 버튼 스토리의 포커스 링 단언과 폭 320px 넘침 확인의 되풀이는 01의 파일이라 손대지 않았다. 상태 맵 옆의
  `disabled ? … : …` 삼항은 표준 축도 판단 항목이라 했다. 알림이 `actions={조건 && …}`의 `false`를 받으면 빈 줄과 간격이
  남는다(축 밖 참고). 받는 쪽은 앱이고 `null`을 넘기면 된다.

## 검사

- 검증 명령: `uv run pytest -q` 1750 통과(7 deselected), `ruff check`·`ruff format --check`, `pyright`, `lint-imports`,
  `pnpm -C web verify`(25파일 338개) 모두 초록. 사진 비교 `pnpm -C web visual`은 63개 통과다(사진 45, 실제 입력 11, 미디어 특성
  5, 정적 빌드 밖 경로 1, 그리고 셀프 리뷰 뒤의 `Combinations` 1). 판정 명령은 파이프 없이 돌리고 로그 파일로 봤다.
- **PR 직전 축.** `coderabbit auth status`가 `Plan: Free`, `Seat: not assigned`라 `coderabbit-review`는 돌리지 않았다. 대기열 136의
  승인된 처방대로 내장 `/security-review`를 돌렸고 확신도 8 이상의 발견은 없었다(프로브 `static_play.mjs`의 route가 디코딩한
  경로를 정적 빌드 안에 가두지 않는 것은 공격자가 조종할 입력이 없어 확신도 3 이하였다).
- **PR [njh6803/agent-os#165](https://github.com/njh6803/agent-os/pull/165)의 CI.** 다섯 잡과 `verify`가 초록이다. claude-review는
  지적 없음이었고, CodeRabbit은 무료 한도에 걸려 리뷰하지 않았다(`@coderabbitai review`도 rate limit).
- **병합 직전.** 그 사이 main에 PR #161(`tools/sibling_overlap.py`)이 들어와 `origin/main`을 이 브랜치에 병합했다(충돌 없음).
  새 규약대로 그 도구를 돌렸고 번호 겹침이 없었다. 03(PR #166)과 함께 고친 파일은 `src/index.ts`와 프로브 README다.
  `origin/main`의 03은 `ready-for-agent`라 이 PR은 마지막 병합이 아니고 기능을 닫지 않는다.
- **둘째 CI의 흔들림.** PR #164·#163이 병합되며 대기열에서 충돌이 나 다시 합친 뒤(`ac03742`), `web` 잡에서 스토리 다섯이
  빨갰다(run 37586861917). `Single`·`SingleDark`의 테두리가 `border-hover`, 스위치 `Off`·`On`·`Toggle`의 트랙·테두리가
  올림 색이었다. 첫 CI(`427f4b7`)와 로컬에서는 지났고 컴포넌트 코드는 그대로였다. 그 실행의 보고에서 `TextField.stories.tsx`가
  첫 파일이었고 파일은 차례로 돈다(`fileParallelism: false`). 그래서 앞선 스토리가 포인터를 옮긴 것이 아니라 실제 포인터가 화면 위쪽에 머물러 있었던 것으로 본다(어림).
  폭을 채운 글 입력의 라벨과 스위치의 줄(라벨)이 그 아래에 있었고, 라벨이 `:hover`면 그 칸도 `:hover`다(정적 빌드에서
  Playwright의 마우스를 라벨 위에 두자 칸의 `matches(":hover")`가 참인 것을 스크래치 탐침으로 손으로 봤다). 스토리
  테스트의 `userEvent`는 합성 이벤트라 포인터를 옮기지 못하므로, 쉬는 색의 단언을 요소가 `:hover`면 올림 토큰, 아니면 쉬는
  토큰과 견주게 바꿨다(`src/storybook/expect.ts`의 `hoverAwareColor`). `Multi`도 같은 단언이라 운으로 지난 것이어서 함께
  바꿨다. 올림 갈래가 실제로 초록인지는 재지 못했다. 다시 그리는 동안 포인터를 움직여도 play가 도는 순간에는 올림이 아직
  걸리지 않아, `border`를 그대로 둔 대조군도 지났다. 근거는 CI가 받은 값이 정확히 올림 토큰(`border-hover` 101·99·95,
  `accent-hover` 23·69·160, 다크 `border-hover` 178·177·174)이었다는 것과, 계산 스타일에 올림이 걸리면 그 요소의
  `matches(":hover")`도 참이라는 것이다.

## 회고

후보 셋을 냈고 셋 모두 승인됐다. 이 PR에서는 반영하지 않았다.

> 사용자(질문에 답): "1 사진의 userEvent 가드,2 Vite 재최적화,3 대기열 136 회차"

1. **사진 비교가 play의 `userEvent` 뒤 상태를 찍지 못하는 것을 테스트 하나와 지침 한 줄로 고정한다 → 대기열 149(새 행, 1회차).**
   위 "정적 빌드의 play에서 `userEvent`가 비어 있다"의 사건이다. 지금은 우연히 결정적이고, 출처가 보안 맥락이 되면 기존
   사진이 조용히 바뀐다. `Typing`을 쓰며 play로 넣은 글이 사진에 든다고 기대했다.
2. **스토리 테스트가 처음 쓰는 의존성의 Vite 재최적화 → 대기열 150(새 행, 1회차).** 셀프 리뷰의 "고치다 만난 것"이다. 캐시가
   없는 CI에서 나는지는 재지 않아, 재는 것부터가 그 행의 일이다.
3. **CLI 좌석이 없고 PR 봇이 rate limit이라 버그·성능 축이 비었다 → 대기열 136(3회차).** PR #156, #158에 이어 이 PR이다.
   보안 축은 승인된 처방(`/security-review`)으로 채웠다.

일지에만 남기는 것:

- 워크트리 가드가 변수를 쓴 `sed`와 복합 명령(파이썬 heredoc, `mkdir`과 heredoc의 체인)을 세 번 거부했다. `CLAUDE.md`의 환경
  함정이 이미 덮는 모양이라 그대로 따르지 않은 것이다. 파일 도구와 단일 명령으로 돌았다.
- `cd`로 작업 폴더를 두 번 옮겨 다음 명령이 다른 자리에서 돌 뻔했다.
- 명세 축 리뷰어가 사진 비교의 수를 63으로 셌다(실제 입력의 새 항목을 여섯으로 봤다). 근거를 보고 받아들이지 않았다.
- 새 행을 main의 마지막(141) 다음인 142·143으로 매겼다가, `tools/sibling_overlap.py`가 열린 PR #162·#163이 먼저 가져간
  번호라고 알려 149·150으로 옮겼다. PR #161이 세운 규약이 이 세션 안에서 바로 동작했다.

## 다음

- **PR #165의 병합.** 워크트리에서 열었으니 next-session의 "워크트리에서 병합할 때"를 따른다. 주 체크아웃 미갱신: 루트는
  `chore/checkout-persist-credentials`(PR #162가 열려 있다).
- **design-system에 남은 것은 03(PR #166)이다.** 그 세션이 돌고 있고 늦게 병합되는 쪽이라, main을 받아 `src/index.ts`의
  내보내기와 프로브 README 표를 합친 뒤 기능을 닫는다(03 티켓의 마지막 체크박스). 이 세션은 03의 지시문을 내지 않는다.
- **대기열.** 149·150이 새로 섰고 136이 3회차다. design-system을 닫는 세션이 next-session 결정표의 chore 배치 조건으로 본다.
