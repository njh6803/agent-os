# 2026-10-16 (19) 사진의 빈 userEvent 고정과 디자인 토큰 덮기의 판정 자리

next-session 지시문으로 연 새 세션의 하네스 chore다. 대상 파일이 `.claude/rules/web-design.md`인 열린 대기열 행 가운데 ADR이
필요 없는 둘(149·226)을 한 PR로 닫는다. 같은 파일을 든 215는 ADR 0026 이력이 필요해 지시문이 뺐다.

> 사용자: "대기열 149·226(대상 파일이 `.claude/rules/web-design.md`인 열린 행 가운데 ADR이 필요 없는 둘)을 chore 한 PR로 반영한다" (지시문의 시작 프롬프트. 범위는 PR과 병합까지)

## 시작

- **tidy-checkouts.** 루트 main을 `990b35e4`에서 `66f969ad`로 당겼다. 지운 워크트리와 브랜치는 없다.
  `skill-check-and-retro-section`은 병합된 PR의 머리와 브랜치 끝이 달라 사람에게 넘겼다. 나머지 스물하나는 병합된 PR이 없거나,
  실행 중인 세션·살아 있는 잠금 pid·작업 디렉터리를 쥔 `claude.exe`가 있어 남겼다. 휴지통의 `.venv` 넷은 `python.exe`(pid 11804,
  25308)가 모듈을 올려 `empty-trash`가 1로 끝났다.
- **워크트리.** `EnterWorktree`(이름 `web-design-userevent-and-token-overrides`)로 들어가 브랜치 이름을 지시문의 것으로 바꿨다.
  사진 비교를 돌리려고 꺼져 있던 Docker Desktop을 켰다.

## 어떻게 했나

1. **149의 근거를 다시 봤다.** 프로브 `static_play.mjs`를 이 워크트리의 정적 빌드로 다시 돌리자 `molecules-textfield--typing`은
   `secure: false`, `clipboard: "undefined"`, 두 칸의 값이 비었고 콘솔 오류가 `TypeError: n.type is not a function`이었다.
   설치본 Storybook 10.6.1의 `dist/csf/index.js` `enhanceContext`(clipboard가 있을 때만 `context.userEvent`를 채운다)와
   `dist/preview/runtime.js`의 렌더 맥락(`userEvent: {}`로 시작한다)을 읽었다.
2. **149의 테스트.** `web/packages/ui/visual/storybook.visual.ts`에 둘째 테스트를 더했다. `Typing`을 열고 차례로 까닭(보안 맥락이
   아니고 clipboard가 없다), 표지(콘솔 오류에 `.type is not a function`이 있다), 그림(두 칸이 비었다)을 단언한다. 표지는
   `CODING_STANDARDS.md`의 "실패를 기대하는 테스트는 실패의 까닭까지 단언한다"를 따른다. 그것이 없으면 play가 아예 돌지 않아 칸이
   빈 경우와 가르지 못한다. 이미 있는 동작을 고정하는 가드라 처음부터 초록이었고, 빨강은 아래 변이로 봤다. 머리 주석을 "경계"
   하나에서 "route의 성질" 둘로 넓히고, `storybook.ts` 머리 주석에 그 테스트가 고정한다는 한 줄을 더했다.
3. **149의 규칙.** `web-design.md` 사진 비교 문단 끝에, 사진이 play가 맥락의 `userEvent`를 처음 부르기 전의 그림이라는 것과
   그 까닭(출처에 `navigator.clipboard`가 없다), 그래서 사진에 남길 상태는 args(넣은 글은 `value`)로 그리고 실제 입력의 상태는
   앞의 `INTERACTIONS`가 찍는다는 문장을 더했다. 대기열 행의 후보 문구("상호작용 상태는 `INTERACTIONS`에 더한다")는
   `INTERACTIONS`가 올림·누름·포커스만 찍어 넣은 글을 담지 못해, 넣은 글의 길(args)을 함께 적었다.
4. **226의 규칙.** 컴포넌트 공통에서 계산값 스토리 항목 바로 뒤에 한 항목을 더했다. 행은 "스토리 항목"이라 했지만 그 항목이 이미
   길고 다루는 것(컴포넌트 스토리가 재는 법)과 이 항목(컴포넌트 스토리가 재지 못하는 것)이 달라 따로 세웠다. 대응과 덮기는
   컴포넌트 스토리가 같은 토큰끼리 맞대 함께 바뀌므로, 바꾸면 컴포넌트 밖에서 맞대는 사례를 그 갈래가 도는 자리에 더하고 지우는
   변이로 빨강을 본다. 어디서 무엇과 맞대는지는 코드를 읽고 적었다. 판정 스토리 Matrix의 `primaryBranchFailures`는 명시 모드
   여덟 벌과 시스템(스토리 테스트라 라이트)에서 `primary`와 다크의 `on-primary`를 이웃 토큰(`accent`·`text`, `on-accent`·`bg`)과,
   `media.visual.ts`의 군청 시스템 모드 시험은 문서 뿌리와 shadow 호스트의 주 버튼 묶음 넷을 그 모드를 명시한 탐침과, 판정 스토리
   ShadowRoot는 녹청 라이트와 군청 다크의 shadow 값을 문서 쪽과 맞댄다. 셀프 리뷰 뒤에 테마마다 맞댄다는 문장을 더했다(아래).

## 고치다 만난 것

- 같은 프로브에서 `atoms-button--primary`의 play는 `userEvent.click`에 닿기 전에, `molecules-textfield--single`의 play(맥락의
  `userEvent`를 받지 않는다)는 색을 맞대는 단언에서 `semanticColor`(`src/storybook/expect.ts`)가 `--on-primary`·`--bg-raised`의
  `#fff`를 `#RRGGBB`가 아니라며 던져 멈췄다. 정적 빌드의 CSS는 hex를 짧게 줄이고(`stories.visual.ts`의 `backgrounds`는 그래서
  3·4자리도 받는다), 스토리 쪽 도우미는 6·8자리만 받는다. 사진은 여전히 첫 `userEvent` 전의 그림이고 스토리 테스트는 개발 서버라
  판정이 바뀌지는 않는다. 다만 "첫 호출에서 멈춘다"는 보편 문장이 아니라서 규칙과 `storybook.ts` 머리 주석을 "늦어도 그 첫
  호출에서 멈춘다"로 썼고, 프로브 README의 `static_play.mjs` 행에 이 재실행을 덧붙였다.

## 변이

`.scratch/design-system/probes/static_play_mutations.toml` 셋이 모두 기대대로였다(기준선 `storybook.visual.ts` 2 passed).

1. 출처를 `https://storybook.invalid`(보안 맥락)로 바꾸면 까닭의 단언이 빨갛다. 표지 `"secure": true`.
2. `addInitScript`로 `navigator.clipboard`를 심고 까닭의 단언을 걷으면 표지의 단언이 빨갛다. 첫 판의 표지 `콘솔의 오류`.
3. 2에 더해 표지의 단언도 걷으면 그림의 단언이 빨갛다. 첫 판의 표지 `주문 조회`.

2·3은 Storybook이 clipboard 없이도 `userEvent`를 채우게 바뀐 판을 흉내 낸다. 그때 까닭의 단언은 지나므로 표지와 그림이 잡아야 한다.
2·3의 첫 판 표지는 그 단언에서만 나오는 문구가 아니었다(아래 셀프 리뷰). 고친 표지로 표 전체를 다시 돈 결과는 아래 검사 절이다.

## 카나리아

`.scratch/harness/probes/canary/web_design_rule_userevent_and_overrides.toml`. 첫 사전 확인은 149의 카나리아로 고른 테스트 파일
경로가 세션에 실리는 git 상태의 바뀐 경로에도 있다며 막았다. 규칙 본문에만 있는 조각("넣은 글은 `value`")으로 바꿔 사전 확인을
지났고, 실제 실행은 통과 4였다(실험군 셋이 제목·조각·출처를 모두 옮기고 대조군은 "없음", claude 2.1.300, 커밋 전의 워크트리 사본).
그 뒤 셀프 리뷰가 두 문장의 본문만 고쳤고, 머리말과 명세의 칸은 그대로이며 카나리아 조각 셋이 묻는 자리에 남아 사전 확인으로
갈음했다(`--preflight` 통과).

## 셀프 리뷰

기점 `66f969ad`, 커밋 없음, 바뀐 파일 다섯, 미추적 셋(변이 표, 카나리아 명세, 이 일지). 리뷰를 띄우기 전에 테스트 머리 주석과 변이
표·README 행의 "play가 끝까지 돈다"를 "첫 `userEvent`를 지나 이어 돈다"로 고쳤다(위 고치다 만난 것의 반례).

- **표준 축.** Critical 없음, Major 하나, Minor 둘, Nit 넷.
  - 고친 것: [Major] 226 항목이 실제보다 넓게 덮인다고 적었다. 미디어 특성 시험은 군청만, ShadowRoot는 녹청 라이트와 군청 다크만
    보아 자초의 시스템 다크와 `:host` 넷, 군청 명시 라이트의 `:host`는 어느 판정도 보지 않는다(코드로 확인했다). 그래서 자초의
    선택자만 지우는 변이는 잡히지 않는다. 항목을 "어디서 맞댄다"는 서술에서 "그 갈래가 도는 자리에 더한다"는 지시로 바꾸고, 반례를
    일반 조항으로 올렸다. 한 선택자 목록에 여러 테마가 들면 테마마다 맞대고, 블록과 테마마다의 선택자를 지우는 변이로 본다. 대기열
    226의 닫힘 문구도 같은 뜻으로 고치고 지금의 빈자리(군청뿐)를 적었다. 자초 사례를 시험에 더하는 것은 이 행의 몫(규칙 한 줄)을
    넘어 넘김으로 둔다(아래 회고).
  - 고친 것: [Minor] 149 문장이 보편 주장이었다. 리뷰는 반례 둘을 들었다. `storybook/test`가 내보내는 모듈 수준의 `userEvent`는
    clipboard와 상관없이 돈다는 것(리뷰가 코드를 읽었고 돌리지 않았다, 이 세션도 재지 않았다)과, 첫 `userEvent` 앞에서 부른
    `.focus()`는 사진에 든다는 것이다. 규칙과 테스트 주석을 "play 맥락의 `userEvent`"로 좁히고 까닭에 실제 조건(`navigator.clipboard`가
    없다)을 적었다. 테스트 이름도 "play 맥락은 … Typing 의 play 가 첫 입력에서 멈추고 넣으려던 글이 그림에 없다"로 좁혔다.
  - 고친 것: [Minor] 변이 2·3의 표지가 그 단언에서만 나오는 문구가 아니었다(`.claude/rules/probes.md` 첫 항목). 2·3을 손으로 넣어
    실패 출력을 받아 보니 3의 호출 기록에 `placeholder="예: 주문 조회"`가 찍혔고, 코드 조각은 실패 줄의 위 두 줄까지 보였다. 표지를
    `Error: 콘솔의 오류`와 `Received: "주문 조회"`로 바꾸고 그 까닭을 표 머리에 적었다.
  - 고친 것: [Nit] 테스트 머리 주석의 "기존 사진이 조용히 바뀐다"는 틀렸다. 사진 비교는 빨개지고 조용한 것은 까닭이다. "사진만으로는
    까닭이 보이지 않아 이 테스트가 그 까닭을 이름으로 알린다"로 고쳤다. [Nit] 일지가 Matrix가 "주 버튼 묶음"을 맞댄다고 썼는데
    `primary`와 다크의 `on-primary`뿐이라 고쳤다. [Nit] 카나리아 머리의 `paths`를 둘 다 적었다. [Nit] 새 문장의 `INTERACTIONS`
    안내가 같은 문단 앞 문장과 겹쳐 "앞의 `INTERACTIONS`가 찍는다"로 줄였다.
- **명세 축.** Critical·Major 없음, Minor 둘, Nit 넷, 확인 불가 하나.
  - 고친 것: [Minor] 지시문의 `pnpm -C web visual` 전체 실행이 일지에 없었다. 돌렸고 아래 검사 절에 적었다.
  - 고친 것: [Minor] `storybook.ts` 머리 주석의 "첫 호출에서 멈추고"가 남아 있었다. "늦어도"로 고치고 프로브 README의
    `static_play.mjs` 행에 2026-10-16 재실행을 덧붙였다.
  - 고친 것: [Nit] 일지가 `molecules-textfield--single`의 play도 "`userEvent`에 닿기 전에" 멈췄다고 썼는데 그 play는 맥락의
    `userEvent`를 받지 않는다. [Nit] 카나리아 머리의 인용이 원문과 띄어쓰기가 달랐다(따옴표를 걷고 풀어 썼다). [Nit] Matrix의
    "묶음"(표준 축과 같은 지적).
  - 남긴 것: [Nit] 226 항목을 행이 말한 "스토리 항목" 안이 아니라 바로 뒤에 따로 세운 것은 리뷰도 받아들일 만하다고 했다. 까닭은
    위 어떻게 했나 4. 확인 불가로 남은 사용자 인용은 지시문의 시작 프롬프트 원문이다.
- **다시 돌린 것.** 카나리아 `--preflight` 통과, 변이 표 `--check` 원문 맞음. 나머지는 아래 검사 절.

## 검사

- **리뷰 전.** `pnpm -C web verify` 초록(테스트 28파일 380개). `pnpm -C web visual` 전체 108 passed(4.9분, Docker의 Playwright
  1.63.0 이미지). 셀프 리뷰 뒤 테스트는 이름과 주석만 바뀌었고 단언은 같다. 마크다운 표 검사와 지침 검사도 초록이었다.
