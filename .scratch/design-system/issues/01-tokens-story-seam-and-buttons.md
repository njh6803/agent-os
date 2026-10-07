# 01: 디자인 토큰과 스토리 테스트 — 다섯 테마 × 두 모드가 판정되고 아이콘·버튼·아이콘 버튼이 선다

**What to build:** 개발자가 `pnpm -C web verify`를 치면 test 단계가 실제 chromium에서 `packages/ui`의 스토리 테스트를 돈다. 디자인 토큰의 판정 스토리가 열 벌(테마 다섯 × 모드 둘)의 쓰임새 토큰 26개와 명암비 43짝, 기준 폭 둘, 글꼴 일곱 벌, rem 0을 보고, 미리보기가 모든 스토리의 그림에서 규칙 없는 클래스와 임의값을 잡는다. 판정 함수가 실제로 빨개지는지도 음성 스토리가 본다. 아이콘, 버튼, 아이콘 버튼이 스토리와 행동 테스트와 axe를 지난다. Storybook에서 테마·모드·shadow를 골라 본다. 앱은 `@agent-os/ui`의 진입점 넷을 소스 그대로 import할 수 있다. CI web 잡이 chromium을 깔고 같은 스토리 테스트를 돈다.

이 기능의 첫 티켓이고 02·03·04를 막는다. 두 앱이 기대는 계약(패키지의 `exports`, 테마 목록, `IconName`, props 타입의 모양, 판정 함수의 서브패스)과 헌법(`operations.md`)이 여기서 선다. 리뷰의 질문은 "동작하나"가 아니라 이 이름과 모양으로 오래 살 수 있느냐다.

**병합 뒤의 틈.** 사진 비교가 아직 없다(02). 그 사이 올림·누름의 색은 사진이 아니라 클래스 판정(`hover:` 규칙이 있는지)과 Matrix(그 쓰임새 토큰의 값과 명암비)만 받친다. 시스템 다크와 속성이 없는 문서·호스트가 먹인지의 영구 확인도 02다. 이 티켓이 쓰는 문장(rules, 독스트링, 헌법)은 틈 동안에도 참이어야 한다. 02~04가 들일 것을 지금 있다고 적지 않는다.

근거는 `.scratch/design-system/spec.md`의 Solution, "이음매", "패키지와 배치", "디자인 토큰의 값과 원천", 색 두 절, "테마와 모드", "디자인 토큰 CSS의 모양", "공통 크기", "글꼴", "컴포넌트 아홉"의 공통과 1~3과 아이콘 이름, "패턴과 화면은 앱이 짓는다", "Storybook과 판정 함수", "문서와 설정", Testing Decisions의 주 이음매 절과 그 2026-10-06 명세 검토·to-tickets 주석이다. ADR 0026과 이력 넷, ADR 0024(아이콘 서브패스, shadow root 보정), ADR 0021 이력, ADR 0020(원칙 III의 TS 판정자)이 앞선 결정이다. 값의 원천은 `.scratch/design-system/design/`의 v3이고 `.scratch/design-system/probes/tokens/design.mjs`가 뽑는다. 선례는 `probes/tokens/ui/`(판정 함수, 판정 스토리, 버튼)와 `probes/storybook/ui/`(미리보기와 shadow 틀)다.

**Blocked by:** None (can start immediately)

**Status:** done

### 패키지와 설치

- [x] **`web/packages/ui`, 이름 `@agent-os/ui`, `"type": "module"`.** `exports`는 넷이다. 컴포넌트·`IconName`·테마 목록의 `.`, Tailwind와 디자인 토큰만 든 `./theme.css`(글꼴 없음), 글꼴의 `./fonts.css`, 판정 함수의 `./testing`. 앱은 이 넷만 import한다. 글꼴을 나누는 이유는 Vite 라이브러리 모드가 글꼴 CSS의 `url()`을 모두 data URL로 박아서다(약 18MB, 프로브 `tokens/libmode.mjs`). 자기 문서에 선언하는 쪽(관리 화면, iframe 페이지, Storybook)은 둘 다 들이고 페이지 안 번들은 `./theme.css`만 들인다
- [x] **의존성의 자리.** React는 피어다. 글꼴 셋(`@fontsource/noto-sans-kr`, `@fontsource/jetbrains-mono`, `@ibm/plex-mono`)과 `lucide-react`는 패키지의 `dependencies`, Tailwind(`tailwindcss`, `@tailwindcss/vite`, `@tailwindcss/cli`)와 Vite는 `devDependencies`다. Storybook(`storybook`, `@storybook/react-vite`, `@storybook/addon-vitest`, `@storybook/addon-a11y`)과 Vitest 브라우저 모드 패키지는 뿌리 `web/package.json`이다. 판은 잰 판(Storybook 10.6.1, Tailwind 4.3.3, 글꼴 5.3.0·5.3.0·2.5.0, lucide-react 1.51.0)에서 시작한다. 공급망 유예(`minimumReleaseAge`)를 푸는 예외는 들이지 않는다. 설치된 판이 잰 판과 major로 다르면 그 몫을 다시 재고(`docs/agents/issue-tracker.md` 프로브와 근거), 판은 일지에 적는다
- [x] **설치 조건.** `web/pnpm-workspace.yaml`의 `allowBuilds`에 esbuild, @parcel/watcher, @ibm/plex-mono를 `false`로 둔다. 없으면 pnpm 11이 설치를 멈춘다(프로브의 첫 실행에서 손으로 봤다). 패키지 tsconfig는 기준 tsconfig를 extends하고 include에 `".storybook/**/*"`를 따로 적는다. 뿌리 `.gitignore`에 앵커를 붙인 `/web/packages/ui/dist/`와 `/web/packages/ui/storybook-static/`를 더한다. Storybook 텔레메트리를 끈다
- [x] **진입점 넷을 소비자처럼 이름으로 푸는 확인이 있다**(스토리 18, 명세 검토). 상대 경로로 import하는 테스트는 `exports`가 틀려도 초록이다
- [x] **Storybook 정적 빌드의 스크립트를 둔다.** 02의 사진 비교가 그 산출물(`storybook-static/`)을 입력으로 쓴다. 한 번 지어 성공과 산출물이 판정 범위에서 빠지는 것(위 `.gitignore`)을 본다
- [x] **`build`.** `tsc -p tsconfig.build.json`과 Tailwind CLI로 `dist/`를 낸다. CSS는 디자인 토큰 CSS만이고 글꼴은 싣지 않는다(사용자가 골랐다. `/design-sync`가 글꼴 파일을 옮기는지는 처음 돌릴 때 본다). 커밋하지 않는다. 한 번 돌려 성공과 `dist/` CSS의 rem 0을 일지에 적는다

### 디자인 토큰 CSS와 글꼴 CSS

- [x] **값은 `design.mjs`가 뽑는 그대로다.** 원색 토큰 330개(테마 다섯 × 66)를 hex 소문자로 둔다. 디자인 파일의 OKLCH 공식과 생성 단계는 코드에 옮기지 않는다. 옮길 때 `design.mjs`의 출력과 코드의 값(원색, 쓰임새 대응, 공문의 예외 다섯, 크기, 굵기)이 같은지 한 번 보고 일지에 적는다. 영구 테스트는 디자인 파일을 읽지 않는다
- [x] **모양은 명세의 "디자인 토큰 CSS의 모양" 절이다.** `@import "tailwindcss" source(none)`과 패키지의 소스 전체를 덮는 `@source`. `@theme`에 `--*: initial`과 글자·간격(`0` 포함)·조작 높이·아이콘·부품 치수·모서리·굵기(`regular`, `medium` 500, `strong`)·기준 폭·움직임과 keyframes. `@theme inline`에 쓰임새 26개·글꼴·`mid`·글자 단계의 굵기·그림자 셋. `@layer theme`에 테마 선택자마다 원색과 글꼴 변수, 모드·시스템 모드·공문 예외의 선택자마다 쓰임새와 `--shadow-color`와 `color-scheme`, 모든 선택자의 `:host(…)` 짝. `@layer base`에 `html`과 `:host`의 바탕과 글자색
- [x] **글꼴 CSS.** Noto Sans KR 400·500·600과 JetBrains Mono 400·500은 Fontsource의 굵기 CSS를 `@import`하고, IBM Plex Mono 400·500은 저자의 split woff2를 `local()` 없이 다시 선언한다. 글꼴 스택은 본래 이름 뒤에 시스템 글꼴이다
- [x] **테마 목록을 진입점 `.`에서 내보낸다**(스토리 41, 명세 검토). 키, 화면의 이름(한국어), 기본 테마 `muk`이다. Storybook globals와 Matrix가 그것을 읽는다. 테마를 하나 더할 때 적는 자리는 원색 66개, 고정폭 글꼴, 테마 선택자, 이 목록의 한 줄이다
- [x] **shadow root.** 패키지가 ADR 0024의 `@layer properties` 재선언 시트를 만드는 함수와, 상속 속성(글꼴, 글자색, 줄 높이, 자간 등)을 다시 정하는 감싼 요소의 규칙을 든다

### Storybook과 이음매

- [x] **뿌리 `web/vitest.config.ts`에 `storybook` 프로젝트를 더한다.** `@storybook/addon-vitest`로 실제 chromium에서 돈다. 기존 `node`·`pages` 프로젝트는 그대로다. `pnpm -C web verify`의 test 단계에 들어 pre-commit과 CI web 잡이 함께 돈다
- [x] **미리보기.** 디자인 토큰 CSS와 글꼴 CSS를 전역으로 싣는다. globals는 `theme`(테마 목록, 기본 `muk`), `mode`(`system` 기본 | `light` | `dark`. `system`이면 속성을 두지 않는다), `shadow`(`off` | `on` | `raw`)이고 데코레이터가 문서 뿌리나 shadow 호스트에 단다. globals는 `Record<string, unknown>`으로 받아 비교로 좁힌다(원칙 III). addon-a11y는 `test: "error"`다
- [x] **모든 스토리의 그림에 클래스 판정을 건다**(명세 검토 should-fix). 미리보기의 `afterEach`(Storybook 10.6.1 설치본의 타입이 play 뒤의 사후 단언 자리로 적는다)가 그린 요소에서 규칙 없는 클래스와 임의값을 찾아 있으면 실패시킨다. 판정 스토리처럼 뺄 것은 태그로 고른다. 그래서 컴포넌트를 더하는 티켓이 판정 스토리를 고치지 않아도 판정된다. **보통 스토리에 `text-base`를 심은 변이로 스토리 테스트가 빨개지는 것을 보고 일지에 적는다.** `afterEach`의 예외가 테스트 실패로 이어지지 않으면 멈추고 자리를 다시 고른다
- [x] **스토리의 이름.** play가 있는 스토리는 `name`이 행동을 말하는 한국어 문장이다. 내보내기 이름은 영어 식별자다

### 판정 함수와 판정 스토리

- [x] **`./testing`이 `contrastRatio`, `sheetsDefining`, `classesWithoutRules`, `arbitraryClasses`를 내보낸다.** 의존성이 없고 진입점 `.`에 넣지 않는다. 정의 없는 `var()`의 판정은 두지 않는다
- [x] **Matrix.** 안쪽 요소에 열 벌을 달아 쓰임새 26개가 모두 `#RRGGBB`로 풀리고, 다섯 테마의 `accent`가 모두 다르며, 짝 43개(명세의 목록)가 기준을 넘는다. 실패 메시지는 테마·모드·짝을 든다. 쓰임새 토큰의 값은 디자인 파일과 맞대지 않는다
- [x] **Responsive.** `@container`인 요소의 폭 359px에서 `@wide:`가 걸리지 않고 360px에서 걸린다. 시트의 조건이 `(width >= 360px)`과 `(width >= 768px)`이다
- [x] **Fonts.** 글꼴 일곱 벌(Noto Sans KR 400·500·600, JetBrains Mono 400·500, IBM Plex Mono 400·500)이 `document.fonts.load`로 `loaded`다
- [x] **음성 사례**(명세 검토 should-fix, 스토리 29~33). 심은 클래스(`text-base`, `rounded`, `font-bold`, `bg-gray-500`, `p-5`, `animate-pulse` 등)를 규칙 없는 클래스의 판정이, `p-[13px]`·`bg-[var(--nope)]`를 임의값의 판정이 잡는다. `contrastRatio("#000000", "#ffffff")`가 21이고 같은 색끼리는 1이다. 기준 미달 짝을 Matrix와 같은 메시지 만들기에 넣으면 테마·모드·짝이 든 메시지가 나온다. 심은 클래스와 기준 미달 짝을 그리는 이 스토리들은 `afterEach`의 판정과 axe에서 빠진다
- [x] **rem 0.** 디자인 토큰 CSS의 시트(`sheetsDefining`이 고른 것)와 글꼴 CSS의 시트를 CSSOM으로 훑어 rem이 없다(명세 검토 should-fix). 글꼴 CSS는 `--gray-50`을 정의하지 않으므로 그 시트를 고르는 방법을 따로 둔다
- [x] **명세의 Classes 스토리는 따로 두지 않는다.** 위 `afterEach`가 모든 스토리에서 그 일을 한다. 도는 표시처럼 상태로만 그려지는 것은 그 컴포넌트의 상태 스토리가 그린다
- [x] **shadow 표본.** 같은 컴포넌트(버튼)를 문서와 shadow 호스트(속성은 호스트에) 안에 함께 그리고, 문서 쪽 계산값을 먼저 읽은 뒤 문서의 시트를 모두 끈 채 shadow 안의 계산값이 같은지 본다. 같은 표본이 사이트를 흉내 낸 문서의 `*` 규칙(글꼴, 글자색, 줄 높이, 자간)을 둔 채 감싼 요소 안의 계산값이 우리 값인지도 본다(ADR 0026이 `font-family` 밖을 어림으로 둔 것). play가 끝나면 시트를 되돌린다
- [x] **판정 스토리(Matrix, Responsive, Fonts, 음성 사례, rem, shadow 표본)는 모두 태그로 표시해 02의 사진 비교가 뺄 수 있게 한다**

### 컴포넌트 셋 (명세의 "컴포넌트 아홉" 공통과 1~3)

- [x] **props 타입의 모양을 정한다**(명세 검토 should-fix). 표가 계약의 최소이고 `className`·`style`은 받지 않는다. 표의 이름이 그 요소의 기본 속성과 겹치는 자리(버튼의 `onClick: () => void`와 `children: string` 등)를 어떻게 다루는지, 표에 없는 기본 속성을 어떤 타입으로 받는지를 정해 "이 티켓이 정한 것"과 일지에 적는다. 03·04가 그것을 따르므로 복합 컴포넌트(글 입력, 스위치)가 나머지 속성을 어느 요소로 넘길지도 규칙으로 적는다
- [x] **아이콘.** `IconName`은 명세의 열여섯이고 `loader-circle`은 컴포넌트 안에서만 쓴다. import는 서브패스(`lucide-react/dist/esm/icons/<이름>`)와 손으로 둔 모듈 선언이다. 설치한 판에서 열일곱이 파일로 있는지 본다(1.51.0에는 있었다). `label`이 없으면 `aria-hidden`, 있으면 `role="img"`와 이름이다. 크기 넷의 폭이 14·16·20·24px이다
- [x] **버튼.** 이름으로 찾는다. 기본 `type`이 `button`이다. 크기 둘의 높이가 40·32px이다. 변형 셋의 배경·글자색(위험은 테두리도)이 쓰임새 토큰의 계산값이다. `icon`은 글자 앞이다. `disabled`이면 눌러도 `onClick`이 불리지 않고 색이 `disabled-surface`·`disabled-text`다
- [x] **불러오는 중은 `disabled`가 아니다**(명세 검토 should-fix). `aria-disabled="true"`와 `aria-busy="true"`를 달고 누름을 무시하며, 색은 기본 그대로이고 포커스가 남으며 너비가 그대로다. 도는 표시는 `loader-circle`이고 `motion-reduce:animate-none`을 함께 쓴다
- [x] **아이콘 버튼.** 접근 이름과 `title`이 `label`이다. 크기 둘이 정사각형 40·32px이다. 투명 변형이 기본이다. 불러오는 중에도 이름이 그대로다. `disabled`이면 눌러도 불리지 않고, 쓸 수 없음의 색이 디자인 파일 상태 표대로다(주·보조는 `disabled-surface`·`disabled-text`, 투명은 `disabled-text`만)
- [x] **포커스 링.** 버튼과 아이콘 버튼 모두 Tab으로 포커스하면 outline이 `solid`이고 색이 `--focus`의 값이다
- [x] **스토리.** 컴포넌트마다 변형·크기와 상태 prop의 조합(아이콘, 불러오는 중, 쓸 수 없음)을 스토리로 둔다. 그래야 `afterEach`가 그 클래스까지 판정한다. globals `mode: "dark"`인 스토리가 하나 이상이다. 버튼 묶음을 폭 320px의 자리에 그려 `scrollWidth`가 `clientWidth`를 넘지 않는다. 모든 스토리가 axe를 지난다
- [x] **`<Name>.md`.** 스토리 옆에 디자인 파일의 "쓰는 법"(언제 쓰는지, 해도 되는 것과 안 되는 것)을 옮긴다
- [x] **원칙 III.** 판정 함수, 스토리, 미리보기는 `as`·`any`·`!` 없이 쓴다. `instanceof`로 규칙과 요소를 좁힌다. 판정자의 범위에서 빼는 목록을 두지 않는다

### 앱 판정의 자리 (사용자가 골랐다. 추천은 받는 기능에 넘기는 것이었다)

- [x] **앱의 스토리를 어디에 둘지 정한다.** 패키지의 Storybook이 앱 폴더도 훑는지, 앱마다 Storybook을 두고 패키지의 미리보기를 나눠 쓰는지 같은 길 가운데 고른다. 조건은 넷이다. `/design-sync`가 올리는 것은 디자인 시스템의 스토리뿐이다(organisms는 앱에 남는다, ADR 0026). 02의 사진 비교가 앱의 스토리도 찍을 수 있다. 앱의 스토리도 `./testing`의 판정과 axe를 지난다. 층 경계(앱 사이 import 금지, 패키지는 앱을 모른다)를 지킨다
- [x] **여러 앱과 패키지에 걸친 배치라 ADR 0026 이력 초안을 보이고 승인을 받는다.** 셀프 리뷰를 반영한 뒤에 묻는다(대기열 126). 본문의 "미리보기와 실제 브라우저 테스트는 패키지의 Storybook이 맡고"가 바뀌면 포인터를 단다(`.claude/rules/adr.md`). 같은 이력에 to-tickets가 바꾼 일 배정 둘을 적고 Consequences의 그 문장들에 포인터를 단다. CI web 잡의 chromium 설치는 게이트 티켓이 아니라 01이 했고, GitHub 러너의 사진 일치는 첫 구현 PR이 아니라 02의 PR CI가 본다(명세의 "CI와 로컬" 항목 주석)
- [x] **앱이 실제 스토리를 두는 일은 web-widget과 admin-style이다.** 이 티켓은 결정과 `./testing`과, 그 결정이 요구하는 공용 자리(예: 나눠 쓰는 미리보기)까지 둔다. 앱의 스토리가 아직 없으므로 앱이 판정된다는 문장을 지금 사실로 적지 않는다. `.scratch/plan.md`의 두 행에 결정을 적는다

### 지침과 문서

- [x] **`.claude/rules/web-design.md`를 새로 둔다**(paths: `web/packages/ui/**`, `web/apps/*/components/**`). 컴포넌트 공통 규칙, 디자인 파일의 "쓰는 법", 패턴의 앱 공통 기준(승인 묻기의 버튼은 "거부"(보조)가 먼저이고 "승인"(주)이 나중, 자리 360px 미만에서 위아래로 꽉 참, 도구 이름과 인자는 글자 그대로 고정폭이고 도구 이름은 `font-medium`, 위젯은 대화 안에 묻는다, 뼈대는 0.3초를 넘길 때만 보이고 움직이지 않는다)을 담는다. 판정 함수와 axe가 잡는 것은 실행 명령만 적는다. 앱의 components가 어디서 판정되는지는 위 결정대로 적되 앱의 스토리가 아직 없다는 것을 거짓 없이 적는다. 새 세션에서 패키지와 관리 화면 components의 파일을 Read해 실리는지 보고 일지에 적는다(스토리 36, `CLAUDE.md` 작업 규약 3)
- [x] **헌법.** `docs/constitution/operations.md`에 web verify의 Vitest가 스토리 테스트를 실제 chromium에서 돈다는 것과 chromium을 까는 명령을 적고, `docs/constitution/README.md`의 버전을 올린다(문구 수정이면 patch). 브라우저는 Playwright의 브라우저 캐시(Windows는 `%LOCALAPPDATA%\ms-playwright`)에 기계마다 판마다 깔리므로, 까는 때는 체크아웃마다가 아니라 처음과 Playwright 판이 바뀔 때다. 게이트 수는 그대로다(02가 고친다)
- [x] **클론 뒤 준비를 적은 자리.** `README.md`의 트리에 `packages/ui`를, 클론 블록에 chromium 설치를 더한다. `.pre-commit-config.yaml`의 머리 주석과 implement 스킬의 워크트리 준비 문장(`uv sync`와 `pnpm -C web install`)도 같은 사실로 맞춘다. 바꾼 스킬은 새 세션에서 불러 본다(`CLAUDE.md` 작업 규약 3)
- [x] **CI.** `.github/workflows/ci.yml`의 web 잡이 `pnpm -C web verify` 전에 chromium을 깐다. e2e 잡처럼 Playwright 판으로 캐시할지는 이 티켓이 정한다. 브라우저가 없을 때 스토리 테스트가 건너뛰지 않고 실패하는지 확인해 일지에 적는다(설계 측정은 재지 못했다). `ci.yml`만 바꾼 PR도 claude-review는 돈다(`operations.md` 리뷰 파이프라인). 판정은 코멘트가 실제로 있는가다
- [x] **`docs/constitution/tech.md`.** 웹 행의 "둘 다 design-system이 처음 들인다"와 "Storybook과 시각 회귀와 글꼴은 design-system이 들인다"를 이 티켓이 들인 것은 지난 사실로 고치고, 시각 회귀는 02의 것으로 둔다. 설치한 판이 행의 판(Storybook 10)과 맞는지 본다. `tech.md`를 바꾸면 헌법 버전도 함께 올린다
- [x] **잔존 grep.** `design-system이 처음 들인다`, `design-system이 들인다`, `아직 스타일과 아이콘이 없다`(관리 화면은 admin-style 전까지 참이라 둘레를 읽고 둔다), `토큰과 컴포넌트를 나누는 자리`를 저장소 전체에서 찾는다. 기록(일지, ADR의 지난 이력, done인 기능의 `.scratch/`, 대기열의 닫힌 행)과 이 기능의 `.scratch/design-system/`, `.claude/worktrees/`는 제외한다
- [x] 이 기능의 첫 병합이라 `.scratch/plan.md`의 design-system 행을 `in-progress`로 바꾼다
- [x] `CLAUDE.md`의 검증 명령이 모두 초록이다. web 파일만 바꾸므로 LLM 테스트는 돌리지 않는다. e2e는 CI가 돈다(중계·시작 래퍼·api-client·서버 라우트를 건드리지 않는다)

### 이 티켓이 정할 것

PR에서 사용자가 이름을 본다. 결정과 근거는 일지에 적고, 여기 "이 티켓이 정한 것" 절을 더한다.

1. 패키지 안 파일의 이름과 자리(디자인 토큰 CSS, 글꼴 CSS, shadow 보정, 판정 함수, 아이콘의 모듈 선언, 판정 스토리)
2. 감싼 요소의 표시 이름
3. props 타입의 모양(겹치는 기본 속성, 나머지 속성의 타입, 복합 컴포넌트가 넘기는 요소)
4. 모든 스토리에 판정을 거는 자리와 판정 스토리를 빼는 태그의 이름(02가 사진에서 뺄 때도 쓴다)
5. 진입점을 이름으로 푸는 확인의 방법
6. 테마 목록의 이름과 모양
7. 앱 스토리의 자리(ADR 0026 이력 초안)
8. CI web 잡의 chromium 설치와 캐시의 모양
9. Storybook 정적 빌드 스크립트의 이름

### 이 티켓이 정한 것 (2026-10-07, 일지 2026-10-07-01)

1. **파일의 자리.** `web/packages/ui/src/` 아래 디자인 토큰 CSS `styles/theme.css`, 글꼴 CSS `styles/fonts.css`, shadow 보정 `styles/shadow.ts`, 판정 함수 `testing/index.ts`, 아이콘의 모듈 선언 `components/atoms/lucide-icons.d.ts`, 판정 스토리 `styles/DesignTokens.stories.tsx`(Matrix, Responsive, Fonts, RemFree, ShadowRoot)와 그 음성 사례 `testing/Checks.stories.tsx`, 진입점 확인 `Entrypoints.stories.tsx`다. 그 밖에 테마 목록 `themes.ts`, props의 공통 모양 `props.ts`, Matrix의 짝과 메시지 `styles/contrast.ts`, 미리보기 본체 `storybook/preview.tsx`와 shadow 틀 `storybook/ShadowFrame.tsx`, 스토리 도우미 `storybook/expect.ts`를 두었다. 아이콘의 모듈 선언은 앰비언트라 앱의 tsc에 실리지 않아(스크래치 tsc로 TS2307을 봤다) `Icon.tsx`가 경로로 참조하고, ESLint는 그 한 파일에서만 경로 참조를 푼다(`web/eslint.config.mjs`, 판정자 테스트에 빨강 둘과 초록 하나).
2. **감싼 요소의 표시는 `data-ui-root` 속성이다**(값은 빈 글자, 상수 `UI_ROOT_ATTRIBUTE`). 규칙은 디자인 토큰 CSS의 `@layer base`에 있고 글꼴, 글자색, 크기, 굵기, 기울임, 줄 높이, 자간, 낱말 간격, 대소문자, 들여쓰기, 정렬, 공백, 글꼴 기능을 우리 값(본문 15/24px)으로 다시 정한다.
3. **props의 모양**은 `props.ts`의 머리 주석이 원천이다. 표의 이름은 표의 타입이 이기고(겹치는 기본 속성의 타입을 지운다), 나머지 기본 속성은 `NativeProps<요소, 표의 이름 | 컴포넌트가 정하는 이름>`(`className`·`style` 제외, `ref` 포함)으로 받아 그 요소에 넘긴다. 컴포넌트가 정하는 속성(`aria-busy`, `aria-disabled`, 아이콘 버튼의 `aria-label`·`title`·`type`)은 받지 않는다. 복합 컴포넌트(03·04의 글 입력, 스위치)는 나머지 속성을 입력 요소에 넘긴다.
4. **판정의 자리**는 미리보기 본체의 `afterEach`이고, 판정 스토리의 태그는 `judgment`, 심은 것을 그려 afterEach와 axe에서 빠지는 음성 사례는 `planted`도 단다. 태그는 글자 그대로 적는다(Storybook 10.6.1의 색인이 상수를 받지 않고 "Expected tag to be string literal"로 색인을 멈췄다). lucide-react가 svg에 스스로 붙이는 `lucide`·`lucide-<이름>` 클래스는 afterEach의 판정에서 뺀다(React 판은 끌 길이 없다).
5. **진입점을 이름으로 푸는 확인**은 패키지 안의 자기 참조다. `Entrypoints.stories.tsx`가 진입점 다섯을 패키지 이름으로 import하고 상대 경로로 푼 같은 파일과 견준다. play는 다섯 모두 Vite의 해석을 보고, 타입 검사는 셋(`.`, `./testing`, `./storybook`)의 TypeScript 해석을 본다(CSS 둘은 `?inline`이 붙어 와일드카드 선언으로 풀린다). 워크스페이스 링크가 없는 자리라 `exports` 맵만으로 풀렸다.
6. **테마 목록**은 진입점 `.`의 `THEMES`(`{ key, name }` 다섯, `as const satisfies readonly ThemeEntry[]`), `ThemeKey`, `DEFAULT_THEME`(`"muk"`), `MODES`, `Mode`다.
7. **앱 스토리의 자리**는 앱마다의 Storybook이고, 패키지가 미리보기 본체를 다섯째 진입점 `./storybook`으로 낸다(ADR 0026의 2026-10-07 이력. 셀프 리뷰 뒤 사용자가 승인했다). 그래서 위 "What to build"의 "진입점 넷", "패키지와 설치" 절의 "`exports`는 넷"·"앱은 이 넷만 import한다"·"진입점 넷을 소비자처럼"은 다섯이 되었다.
8. **CI web 잡**은 e2e 잡과 같은 모양이다. Playwright 판을 키로 `~/.cache/ms-playwright`를 캐시하고, 없으면 `--with-deps --only-shell chromium`으로 깔며, 있으면 시스템 의존성만 깐다.
9. **정적 빌드 스크립트**는 패키지의 `build-storybook`(`storybook build`)이고 산출물은 `storybook-static/`이다.

그 밖에 고른 것: 불러오는 중인 버튼은 너비를 지키려고 글자 자리를 그대로 두고 보이지 않게 한 뒤 도는 표시를 가운데에 그린다(디자인 파일은 도는 표시를 글자 앞에 그렸다). 포커스 링의 색은 `focus`와 `accent`가 다른 공문에서 잰다. 클래스는 상태마다 골라, 쓸 수 없음과 불러오는 중에는 올림·누름의 클래스를 두지 않는다.
