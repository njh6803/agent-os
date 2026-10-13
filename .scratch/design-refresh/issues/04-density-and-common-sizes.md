# 04: 밀도 두 벌과 공통 크기 — 촘촘과 보통이 갈리고 컴포넌트 아홉이 새 치수로 선다

**What to build:** 위젯과 관리 화면이 `data-density`(`compact` 촘촘, `regular` 보통)로 밀도를 고르고, 속성이 없으면 화면 폭 768px 이상에서 촘촘, 미만에서 보통이 된다. 관리 화면은 아무것도 달지 않아 데스크톱과 모바일이 갈리고, 위젯은 `regular`를 단다(그 코드는 web-widget). 버튼과 입력의 높이(32·40px), 본문·표·고정폭 글자의 크기, 표 행의 높이(36·44px)가 밀도를 따른다. 공통 크기(모서리 8·12px, 작은 글자 12/16px, 상태 배지·스위치·진행 막대의 치수, 옆 탐색과 위 막대의 틀, 떠 있는 것의 그림자)가 디자인 파일의 값이 되고, 컴포넌트 아홉이 새 치수로 선다. Storybook에서 밀도를 고를 수 있고, 사진 비교가 녹청의 라이트·다크 × 촘촘·보통을 찍는다.

03 뒤에 돈다. 05를 막는다.

근거는 `.scratch/design-refresh/spec.md`의 "밀도", "공통 크기", "컴포넌트 아홉"의 치수, "판정 스토리와 판정 함수"의 Density·ShadowRoot·ThemeTokensEmitted, "사진 비교", "문서와 설정"과 그 2026-10-12 명세 검토·to-tickets 주석이다. 결정은 ADR 0026의 2026-10-12 이력("관리 화면은 폭 768px 이상에서 촘촘, 미만에서 보통", "위젯은 보통")이다. 값의 원천은 디자인 파일이고 `design.mjs --refresh`가 뽑는다. 측정은 `.scratch/design-refresh/probes/tailwind.mjs`다.

**Blocked by:** 03

**Status:** done

### 밀도

- [x] **값.** 촘촘은 `--body-size` 14px, `--body-lh` 20px, `--table-size` 13px, `--table-lh` 18px, `--mono-size` 13px, `--row-h` 36px, `--control-h` 32px이다. 보통은 15px, 22px, 14px, 20px, 14px, 44px, 40px이다. 변수 이름은 디자인 파일의 것이다. 옮길 때 `design.mjs --refresh --out`의 JSON과 한 번 대조해 일지에 적는다
- [x] **선택자.** 보통의 값은 `:root, :host`와 `[data-density="regular"]`·`:host([data-density="regular"])`에, 촘촘의 값은 `[data-density="compact"]`·`:host([data-density="compact"])`와 `@media (width >= 768px)` 아래의 `:root:not([data-density])`·`:host(:not([data-density]))`에 둔다. 밀도의 중단점은 `wide:`와 같은 768px이고 새 중단점을 두지 않는다
- [x] **유틸리티.** `@theme inline`이 `--text-body`(줄 높이 포함), `--text-table`, `--text-mono`(줄 높이는 `--table-lh`), `--spacing-control`, `--spacing-row`를 밀도 변수에 잇는다. 그래서 `text-body`, `text-table`, `text-mono`, `h-control`, `size-control`, `h-row`가 밀도를 따른다
- [x] **패키지의 CSS는 별칭을 `var()`로 읽지 않는다**(명세 검토). 감싼 요소 `[data-ui-root]`는 지금 `var(--text-body)`를 읽는데, 그러면 inline 별칭도 뿌리에 선언으로 나온다(`tailwind.mjs`). 뿌리에서 풀린 값이 물려지므로 뿌리와 다른 밀도 안의 감싼 요소가 뿌리의 크기를 받을 수 있다(사용자 정의 속성의 상속 규칙에서 나온 어림이다. 아래 Density와 ShadowRoot가 잡는다). `[data-ui-root]`는 `--body-size`·`--body-lh`를 직접 읽는다. 사용 규약이 디자인 에이전트에게 안내할 것도 원천인 밀도 변수다(05)
- [x] **Storybook.** globals에 `density`(`auto` 기본 | `compact` | `regular`)를 더한다. `auto`이면 속성을 두지 않는다. 데코레이터와 shadow 틀이 테마·모드처럼 문서 뿌리나 호스트에 단다

### 공통 크기

명세 "공통 크기"의 표다. 크기의 디자인 토큰은 지금의 이름 체계(Tailwind의 숫자 뜻을 지키는 간격, `s`·`m`·`l` 모서리)를 지키고 값과 수만 디자인 파일에 맞춘다. 옮길 때 디자인 토큰 JSON과 한 번 대조해 일지에 적는다.

- [x] **글자.** `title`은 그대로다. `body`·`table`·`mono`는 밀도를 따른다. `small`은 12/16px다. `badge`(12/16px, 500)가 는다. `heading`, `caption`, `code`를 뺀다
- [x] **조작과 행.** `control`(밀도)과 28px의 `control-s`, 밀도를 따르는 `row`다. 지금의 `control-m`(40)과 32px의 `control-s`는 없어진다
- [x] **틀.** `nav` 256px, `nav-item` 36px, `top-bar` 52px가 는다
- [x] **부품 치수.** `switch-w` 40, `switch-h` 24, `switch-knob` 20, `switch-inset` 2, `progress` 4, `badge` 22, `badge-start` 6px다. `row-touch`와 `field-multi`를 뺀다
- [x] **모서리와 그림자, 움직임.** 모서리는 `s` 4, `m` 8, `l` 12, `full` 999px다. 그림자는 떠 있는 것(위젯 창, 메뉴)에만 쓰는 `float` 하나(`0 8px 24px`와 `0 1px 2px`, 색은 `--shadow-color`)다. `spin`은 한 바퀴 0.8초다
- [x] **`@theme static`은 그대로다.** 글자 그대로의 값은 쓰이지 않아도 모두 CSS 변수로 나온다(ThemeTokensEmitted). 밀도를 따르는 다섯은 `@theme inline`의 별칭이라 그 밖이다
- [x] **옛 크기의 디자인 토큰을 걷는다.** 컴포넌트를 모두 옮긴 뒤 위에서 빠진다고 한 것을 디자인 토큰 CSS에서 지운다. 남은 클래스가 있으면 afterEach가 잡는다

### 컴포넌트 아홉의 치수

명세 "컴포넌트 아홉"의 치수다. 색은 03이 옮겼다. (03 메모: 아이콘 버튼·상태 배지·글 입력·스위치·알림의 머리 주석과 디자인 토큰 CSS의 머리 주석이 치수가 아직 첫 탐색 디자인 파일의 값이고 이 티켓이 옮긴다고 적었다. 치수를 옮기면 그 말을 걷는다. 그리고 `small`이 400이 되어(03) 글 입력의 도움말과 "선택", 스위치의 상태 글, 알림의 본문이 `text-small`에 붙인 `font-regular`는 덮을 것이 없어졌다. 글자를 옮길 때 함께 본다)

- [x] **버튼.** 높이 `h-control`, 안쪽 좌우 12px, 아이콘과 글자 사이 8px, 아이콘 16px, 모서리 `m`, 글자 `text-body`·500
- [x] **아이콘 버튼.** 모서리 `m`, 아이콘 16px. `"m"`(기본)은 `size-control`이라 밀도를 따르고 `"s"`는 28px다. 알림의 닫기는 `"s"`다
- [x] **상태 배지.** 높이 22px(`badge`), 안쪽 왼쪽 6px(`badge-start`)·오른쪽 8px, 아이콘과 글자 사이 4px, 아이콘 14px, 모서리 `s`, 글자 `text-badge`
- [x] **진행 표시.** 막대의 높이 4px(`progress`), 모서리 `full`
- [x] **카드.** 모서리 `l`. 그림자는 02가 뺐다 (02 메모: 버튼·카드·진행 표시의 머리 주석(`Button.tsx`, `Card.tsx`, `Progress.tsx`)이 치수가 아직 첫 탐색 디자인 파일의 값이라고 적었다. 치수를 옮기면 그 말을 걷는다)
- [x] **글 입력.** 한 줄의 높이 `h-control`, 안쪽 좌우 12px, 여러 줄의 안쪽 위아래 8px, 모서리 `m`, 라벨과 칸 사이 8px, 칸과 도움말 사이 4px. 여러 줄의 높이는 줄 수(`rows`, 기본 3)가 정한다(명세가 정했다)
- [x] **스위치.** 트랙 40×24px, 손잡이 20px과 안쪽 띄움 2px, 모서리 `full`, 글자와 사이 8px. 줄의 최소 높이를 뺀다. 누르는 곳은 여전히 라벨 전체다
- [x] **알림.** 모서리 `l`, 안쪽 위아래 12px·좌우 16px, 아이콘 20px, 아이콘과 글 사이 12px, 제목과 본문 사이 4px
- [x] **높이의 단언.** 밀도 globals를 정한 스토리에서 버튼, 아이콘 버튼 `"m"`, 한 줄 글 입력의 높이가 촘촘 32px, 보통 40px인지 본다. 아이콘 버튼 `"s"`는 28px다. 스위치 줄의 높이 48px 이상과 여러 줄 입력의 높이 88px 이상의 단언은 뺀다

### 판정 스토리

- [x] **Density.** 새 판정 스토리다. `data-density`가 `compact`와 `regular`인 표본에서 밀도 변수 일곱이 위의 값이고, 그 안의 `h-control`·`text-body`·`text-table`·`text-mono`·`h-row`의 계산값이 그 값을 따른다. **표본마다 반대 밀도의 조상 안에 둔다**(명세 검토). 스토리 테스트의 창은 1200×900이라(설치본을 읽은 것이다. 처음 돌 때 창의 폭을 본다) 속성이 없는 문서 뿌리가 촘촘이어서, `compact` 표본은 선택자가 없어도 뿌리에서 물려받아 초록이기 때문이다. 그리고 여덟 벌(테마 넷 × 모드 둘)에서 밀도 변수가 같은지 본다
- [x] **ShadowRoot.** 문서 뿌리의 밀도를 globals로 정하고, 문서 쪽 표본과 shadow 호스트에 그와 다른 같은 밀도를 달아 높이까지 맞댄다. 양쪽이 뿌리와 같으면 물려받은 값으로도 지나 위 별칭 문제를 가린다
- [x] **ThemeTokensEmitted, RemFree, Responsive**는 그대로 돈다. Responsive가 보는 시트의 px 조건은 지금처럼 `(width >= 360px)`과 `(width >= 768px)` 둘이다

### 사진 비교

- [x] **찍는 것.** 판정 스토리를 뺀 패키지의 스토리를 녹청의 라이트·다크 × 밀도 둘(`compact`, `regular`)로 찍는다. 상호작용 컴포넌트의 올림·누름·키보드 포커스도 밀도마다 찍는다. 스토리가 globals로 모드나 밀도를 정했으면 그 값만 찍는다. 일반 루프와 상호작용 루프 모두에 그려진 밀도로 거르는 가드를 둔다(03이 상호작용 루프에 모드 가드를 둔 것과 같은 모양이다. 가드가 없으면 밀도를 정한 스토리가 두 밀도 이름으로 찍힌다). 03이 더한 위험 버튼 누름의 계산 바탕과 칠한 픽셀의 단언도 밀도마다 지난다
- [x] **이름.** `<스토리 id>-<모드>-<밀도>.png`, 실제 입력의 상태는 `<스토리 id>-<모드>-<밀도>-<상태>.png`다. 정답을 컨테이너에서 모두 다시 만들고 옛 이름의 정답은 지운다. 남은 사진이 모두 지금 스토리와 밀도의 것인지 본다
- [x] **미디어 특성.** 속성이 없는 문서 뿌리와 shadow 호스트가 창의 폭 1280px에서 촘촘, 375px에서 보통의 `--control-h`를 받는지 본다. 지금의 시스템 모드 사례와 같은 자리다
- [x] **정적 빌드의 hex.** 사진 비교 쪽에서 정적 빌드의 CSS를 글자로 읽는 검사가 있으면 6·8자리 hex를 가정하지 않는다. `optimize`가 `#ffffff`를 `#fff`로 줄였고(`tailwind.mjs`), `@tailwindcss/vite`는 빌드 때 그것을 부른다(명세 검토가 설치본을 읽었다)

### 문서

- [x] **`.claude/rules/web-design.md`.** 밀도와 그 유틸리티, 크기의 디자인 토큰, 그림자는 떠 있는 것에만 쓴다는 것, 사진의 밀도 둘, 판정하는 것(Density)을 고친다. 고친 rules는 새 세션에서 Read해 실리는지 본다
- [x] **`<Name>.md`.** 아홉 가운데 치수와 어긋나는 문장을 고친다. 스위치의 "높이가 48px 이상"을 포함한다(명세 검토)
- [x] **함께 고칠 말.** 명세 잔존 grep 절의 옛 크기와 굵기(`control-m`, `row-touch`, `field-multi`, `text-heading`, `text-caption`, `text-code` 등)가 살아 있는 문서와 코드에서 0인지 본다. 기록은 제외한다. `.design-sync/`와 화면 프롬프트는 05가 고친다
- [x] **원칙 III.** `as`·`any`·`!` 없이 쓴다
- [x] `CLAUDE.md`의 검증 명령이 모두 초록이고 사진 비교 명령도 로컬에서 초록이다

### 이 티켓이 정할 것

1. Storybook 데코레이터와 shadow 틀이 밀도를 다는 자리
2. Density 판정 스토리의 표본 구조(반대 밀도의 조상)
3. 사진 비교가 밀도를 돌리는 방법과 미디어 특성 테스트의 사례 이름

### 이 티켓이 정한 것

근거와 고른 까닭은 일지 2026-10-13-49다.

1. **데코레이터는 문서 뿌리에, shadow 틀은 호스트에 `data-density`를 단다.** 모드와 같은 자리다. globals `density`가 `auto`이면 뿌리에서 속성을 지우고(`removeAttribute`), 틀은 그 값(`null`)을 받아 호스트에 속성을 두지 않는다. 툴바의 이름은 화면 폭·촘촘·보통이다. 밀도 목록(`DENSITIES`, `Density`)은 모드 목록처럼 `themes.ts`에 두고, 진입점 `.`에서는 내지 않는다. 쓰는 쪽(위젯)이 생기면 그 기능이 더한다(셀프 리뷰가 요청 밖의 공개 이름이라고 짚었다).
2. **Density의 표본은 밀도마다 하나이고 반대 밀도의 조상 안에 둔다.** 표본 안에 `h-control`, `text-body`, `text-table`, `font-mono text-mono`, `h-row`의 요소와 감싼 요소(`data-ui-root`)를 둔다. 밀도 변수 일곱은 스토리의 상수(디자인 파일의 값)와 맞대고, 유틸리티와 감싼 요소의 계산값은 그 상수에서 나온 값과 맞댄다. 그 뒤 표본마다 `data-theme`·`data-mode`를 여덟 벌로 바꿔 가며 밀도 변수가 상수 그대로인지 본다. ShadowRoot는 globals로 뿌리를 보통에 두고 문서 쪽 표본과 shadow 호스트를 촘촘으로 단다. 보통 호스트는 `:host`의 기본과 같아 `:host([data-density="regular"])`를 가르지 못하지만, 촘촘 호스트는 문서의 시트를 끈 뒤 `:host([data-density="compact"])`만이 그 값을 준다. 창(1200px)에서는 속성이 없는 호스트도 촘촘이라 호스트가 그 속성을 달았는지도 본다.
3. **사진 비교는 globals의 `density`로 밀도를 돌린다.** 차례는 모드 둘 × 밀도 둘(`TURNS`)이고, 두 루프가 같은 질의(`renderedAs`)로 그려진 모드와 밀도가 요청과 같은지 보고 다르면 찍지 않는다. 사진 비교의 창(480px)은 그대로이고 속성을 달아 창의 폭과 무관하게 그린다. 미디어 특성 사례는 "data-density 가 없는 문서 뿌리와 shadow 호스트는 창의 폭 1280px 에서 촘촘, 375px 에서 보통의 --control-h 를 받는다"이고, `setViewportSize`로 창을 바꾸며 같은 빌드에서 그 밀도를 단 탐침과 맞댄다.
