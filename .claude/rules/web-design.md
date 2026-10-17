---
paths:
  - "web/packages/ui/**"
  - "web/apps/*/components/**"
---

# 디자인 판단 기준

디자인 시스템(`web/packages/ui`, `@agent-os/ui`)과 앱의 화면 부품을 쓸 때의 판단 기준이다. `/design-sync`의 빌드가 같은 파일을 디자인 시스템의 guidelines로 담고, Claude Code가 그것을 디자인 시스템 아티팩트에 올린다(ADR 0026, ADR 0025의 2026-10-16 이력). 디자인 토큰의 값은 디자인 토큰 CSS(`web/packages/ui/src/styles/theme.css`) 한 자리에만 있어 여기 적지 않는다. 컴포넌트마다의 쓰는 법(언제 쓰는지, 해도 되는 것과 안 되는 것)은 스토리 옆의 `<Name>.md`이고, 여기는 여러 컴포넌트와 앱에 걸친 것만 둔다. 워크스페이스 공통 기준은 `web-workspace.md`다.

## 판정하는 것

디자인 토큰에 없는 클래스(Tailwind 기본값, 원색 토큰 이름, 임의값), axe 위반, 여덟 벌(테마 넷 × 모드 둘)의 명암비(반투명 바탕은 아래 바탕에 겹쳐 잰다), 밀도 두 벌의 값과 그것을 따르는 유틸리티(판정 스토리 Density), 기준 폭, 글꼴, rem은 스토리 테스트가 판정한다. 명령은 `pnpm -C web verify`이고 패키지의 스토리만 돌리면 `pnpm -C web exec vitest run --project storybook`이다. 클래스 판정은 미리보기의 afterEach가 모든 스토리의 그림에 건다.

사진은 사진 비교가 판정한다. 판정 스토리를 뺀 패키지의 스토리를 기본 테마(녹청)의 라이트·다크 × 밀도 둘(촘촘, 보통)로 찍어 `web/packages/ui/visual/snapshots/`의 정답과 픽셀까지 비교하고, 상호작용 컴포넌트는 실제 마우스·키보드의 올림·누름·포커스를 밀도마다 더 찍는다. 스토리가 globals로 모드나 밀도를 정했으면 그 값만 찍는다(상호작용도 같다). 속성이 없을 때 밀도가 창의 폭을 따르는 것은 같은 자리의 미디어 특성 테스트가 창 1280px과 375px로 본다. 누름은 스토리 테스트가 걸지 못해 여기서 잰다. 보조·위험 버튼은 누른 순간의 계산 바탕이 그 쓰임새 토큰인지, 녹청 다크의 카드 안 위험 버튼은 칠한 픽셀과 글자의 명암비가 4.5 이상인지 본다. 사진은 기본 테마만이라(ADR 0026) 다른 테마를 정한 스토리가 오면 실패한다. 명령은 `pnpm -C web visual`이고 Docker가 있어야 한다. 스토리를 더하거나 모양을 바꾸면 `pnpm -C web visual:update`로 정답을 컨테이너 안에서 다시 만들고, 바뀐 사진을 사람이 보고 PR 본문에 적는다. 상호작용 컴포넌트를 더하면 `web/packages/ui/visual/stories.visual.ts`의 `INTERACTIONS`에 변형마다 스토리 하나를 더하고, 움직이는 표시가 있으면 `web/packages/ui/visual/media.visual.ts`의 `SPINNERS`처럼 움직임 줄이기의 사례를 더한다.

판정되는 것은 지금 패키지의 스토리뿐이다. 앱의 components에는 아직 스토리가 없다. 앱은 자기 Storybook을 `apps/<앱>/.storybook/`에 두고 미리보기는 `@agent-os/ui/storybook`을 나눠 쓴다(ADR 0026의 2026-10-07 이력). 그 일은 web-widget과 admin-style이 한다.

## 컴포넌트 공통

- 브라우저 기본 요소로 짓는다. 변형은 `satisfies Record<변형, string>` 객체로 클래스를 고른다. 헤드리스 라이브러리는 기본 요소로 지을 수 없는 부품이 생길 때 ADR로 들인다(ADR 0026).
- props는 지금 코드가 계약이다. 재탐색 디자인 파일 5.2절의 props 표는 Claude Design이 낸 초안이라 따르지 않고, 디자인이 없앤 모양을 고르던 prop만 뺀다(design-refresh 명세). props와 겹치는 기본 속성, 나머지 기본 속성, 여러 요소를 엮는 컴포넌트가 나머지를 넘기는 요소는 `web/packages/ui/src/props.ts`의 머리 주석이 정한다. `className`과 `style`은 받지 않는다.
- 클래스는 쓰임새 토큰과 공통 크기의 유틸리티만 쓴다. `dark:`도 테마마다의 색도 두지 않는다. 테마와 모드는 쓰임새 토큰이 바꾼다. 쓰임새 토큰의 이름은 디자인 파일 그대로라 `bg-bg-raised`, `text-text-muted`, `border-border-control`처럼 머리가 겹친다. 반투명 셋(`bg-hover`, `bg-active`, `bg-selected`)은 놓인 바탕에 겹쳐 칠한다.
- 클래스는 상태마다 고른다. 쓸 수 없음과 불러오는 중에는 올림·누름의 클래스를 두지 않는다. 불러오는 중은 `disabled`가 아니어서 `disabled:` 변형으로는 그 상태의 올림·누름을 끌 수 없다.
- 상호작용 컴포넌트는 모두 `focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus-ring`으로 포커스 링을 그린다.
- 쓸 수 없음은 `disabled` 속성이고 `bg-disabled`·`text-disabled`로 칠한다. 명암비 기준의 대상이 아니다.
- 보조·위험 버튼은 바탕 없이 `border` 테두리로 서고 올림에 `bg-hover`를 겹친다. 누름은 보조가 `bg-active`, 위험이 `bg-selected`다. `bg-active` 위의 `danger` 글자는 다크에서 4.5:1에 못 미쳤다(design-refresh 명세의 "위험 버튼의 누름").
- 불러오는 중은 `disabled`가 아니다. `aria-busy`와 `aria-disabled`를 달고 누름(제출 포함)을 무시하며, 색은 기본 그대로이고 포커스가 남고 너비가 그대로다. 도는 표시는 `loader-circle`이고 `motion-reduce:animate-none`을 함께 쓴다.
- 부품의 치수는 공통 크기의 이름 있는 단계로만 쓴다. 간격은 Tailwind의 숫자 뜻을 지키는 `0`·`1`·`2`·`3`·`4`·`6`·`8`(`p-4`가 16px)이고, 나머지는 이름이다(모서리 `s`·`m`·`l`·`full`, 아이콘 `icon-xs`·`icon-s`·`icon-m`, 작은 조작 `control-s`, 틀 `nav`·`nav-item`·`top-bar`, 부품 치수 `switch-*`·`progress`·`badge`·`badge-start`). 컴포넌트가 스스로 쓰는 화면 문구는 그 `<Name>.md`가 적은 것뿐이고 나머지 글자는 쓰는 쪽이 넘긴다.
- 밀도는 `data-density`(`compact` 촘촘, `regular` 보통)가 테마·모드와 같은 요소에서 고르고, 속성이 없으면 폭 768px 이상에서 촘촘, 미만에서 보통이다. 관리 화면은 달지 않고 위젯은 `regular`를 단다. 밀도를 따르는 높이와 글자는 `h-control`·`size-control`·`h-row`·`text-body`·`text-table`·`text-mono`로 쓰고 px로 박지 않는다. 이 이름은 `@theme inline`의 별칭이다. 패키지의 CSS와 인라인 `style`은 별칭을 `var()`로 읽지 않고 원천인 밀도 변수(`--body-size`, `--control-h` 등)를 읽는다. 별칭을 `var()`로 읽으면 그것이 뿌리에 선언으로 나와 뿌리의 밀도로 풀린 값이 물려지고(판정 스토리 Density·ShadowRoot가 잡는다), 읽지 않으면 CSS 변수로 나오지 않는다.
- 밀도를 따르는 높이나 글자 크기를 px로 재는 스토리는 globals로 밀도를 정한다. 스토리 테스트의 창은 1200×900이라 속성이 없는 문서 뿌리는 촘촘이다. 놓인 자리의 밀도 변수와 맞대는 단언은 그러지 않아도 된다.
- 스토리는 변형·크기와 상태 prop(아이콘, 불러오는 중, 쓸 수 없음 등)이 만드는 클래스가 모두 한 번은 그려지게 둔다. 그래야 afterEach가 그 클래스까지 판정한다. 다크(`globals: { mode: "dark" }`) 스토리를 하나 이상 둔다. play는 클래스 글자를 단언하지 않고 쓰임새 토큰이 풀린 계산값으로 본다(`src/storybook/expect.ts`. 대상과 같은 부모 안의 탐침으로 재어 반투명도 받는다). 계산값은 맞대는 토큰이 이웃 토큰과 다른 값인 테마·모드에서 잰다. 여덟 벌 모두 같은 짝은 `accent`와 `focus-ring` 하나라 포커스 링은 기본 테마에서 `primary`·`border`와 갈라 잰다. 라이트 넷에서 같은 짝(`bg-raised`와 `on-accent`·`on-primary`, `border-control`과 `text-disabled`, `bg-active`와 `shadow-color`)은 다크에서, 다크 넷에서 같은 짝(`border`와 `bg-disabled`)은 라이트에서 잰다. 주 버튼 묶음은 테마의 갈래를 따른다. 바탕(`primary`)은 녹청·쪽빛에서 `text`와, 군청·자초에서 `accent`·`focus-ring`과 같아 두 갈래를 하나씩 재고, `primary-active`는 녹청·쪽빛 다크에서 `text-muted`와 같다. 글자(`on-primary`)는 군청·자초 다크에서 `on-accent`와, 녹청·쪽빛 다크에서 `bg`와 같아 `on-accent`와는 녹청 다크에서, `bg`와는 녹청 라이트에서 잰다. 목록의 원천은 design-refresh 명세의 "계산값으로 가를 수 없는 짝"이다.
- 판정 스토리와 음성 사례의 태그는 글자 그대로 `"judgment"`와 `"planted"`다. Storybook의 색인이 정적으로 읽어 상수를 받지 않는다. `judgment`가 붙은 스토리는 사진 비교가 찍지 않고, afterEach의 판정은 `planted`를 건너뛴다. 기본 테마가 아닌 테마에서 값을 재는 스토리(군청의 주 버튼)도 `judgment`를 단다.
- 컴포넌트 스토리는 둘로 나뉜다. 변형과 상태를 늘어놓고 단언하는 변형 스토리, 그리고 컴포넌트를 실제 자리(승인 묻기의 버튼 쌍, 실행 목록의 배지, 플러그인 줄의 스위치 등)에 놓아 보이는 보여 주기용 스토리다. 보여 주기용 스토리는 태그 `"showcase"`를 달고 이름을 `쓰임: …`으로 짓는다. `judgment`는 달지 않는다(달면 사진에서 빠진다). 단언은 두지 않아도 되고, afterEach의 클래스 판정과 axe, 사진 비교를 그대로 지난다. 컴포넌트마다 하나 이상 둔다. 자리와 문구는 관리 화면과 위젯에 실제로 있는 동작(`.scratch/plan.md`의 그 기능 행과 화면 프롬프트)에서 고른다. 디자인 에이전트가 카드를 보고 그 기능을 그리기 때문이다. 컴포넌트를 엮어 보일 뿐이고 패턴과 화면(organisms 이상)을 패키지에 짓지 않는다.
- Claude Design의 컴포넌트 카드에는 보여 주기용 스토리만 오른다. 변형 스토리는 `.design-sync/config.json`의 `overrides.<Name>.skip`에 스토리 id로 든다. 컴포넌트 스토리를 더하거나 이름을 바꾸면 그 목록도 고친다. 어긋남은 동기화 때 도는 `.design-sync/check-conventions.mjs`가 잡고, 규칙은 `.design-sync/NOTES.md`의 "카드에 올리는 스토리"다.

## 쓰는 법

- 상태를 색만으로 보이지 않는다. 아이콘 모양이나 글자를 함께 쓴다.
- 글자와 함께 놓인 아이콘은 꾸밈이라 화면 읽기 프로그램에서 숨긴다. 같은 뜻을 두 번 읽게 두지 않는다.
- 아이콘은 Lucide 모양이고 선은 크기와 상관없이 화면 1.5px이다. 크기는 14·16·20px 셋이다. 칠한 아이콘이나 다른 묶음을 섞지 않는다.
- 그림자는 떠 있는 것(위젯 창, 메뉴)에만 `shadow-float`로 쓴다. 카드, 표, 알림은 그림자 없이 바탕과 테두리로 선다.

## 패턴의 앱 공통 기준

패턴과 화면(organisms 이상)은 앱이 짓는다(ADR 0026). 디자인 파일 03·04절이 근거이고, 앱을 가리지 않는 기준은 아래다.

- 승인 묻기의 버튼은 "거부"(보조)가 먼저이고 "승인"(주)이 나중이다. 자리 폭 360px 미만에서는 둘이 위아래로 꽉 찬다.
- 도구 이름과 인자는 고치거나 줄이지 않고 글자 그대로 고정폭으로 보인다. 도구 이름은 `font-medium`(500)이다.
- 위젯은 남의 화면을 덮지 않고 대화 안에 묻는다.
- 뼈대는 0.3초를 넘길 때만 보이고 움직이지 않는다.
