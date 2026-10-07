---
paths:
  - "web/packages/ui/**"
  - "web/apps/*/components/**"
---

# 디자인 판단 기준

디자인 시스템(`web/packages/ui`, `@agent-os/ui`)과 앱의 화면 부품을 쓸 때의 판단 기준이다. `/design-sync`가 같은 파일을 Claude Design의 guidelines로 올린다(ADR 0026). 디자인 토큰의 값은 디자인 토큰 CSS(`web/packages/ui/src/styles/theme.css`) 한 자리에만 있어 여기 적지 않는다. 컴포넌트마다의 쓰는 법(언제 쓰는지, 해도 되는 것과 안 되는 것)은 스토리 옆의 `<Name>.md`이고, 여기는 여러 컴포넌트와 앱에 걸친 것만 둔다. 워크스페이스 공통 기준은 `web-workspace.md`다.

## 판정하는 것

디자인 토큰에 없는 클래스(Tailwind 기본값, 원색 토큰 이름, 임의값), axe 위반, 열 벌의 명암비, 기준 폭, 글꼴, rem은 스토리 테스트가 판정한다. 명령은 `pnpm -C web verify`이고 패키지의 스토리만 돌리면 `pnpm -C web exec vitest run --project storybook`이다. 클래스 판정은 미리보기의 afterEach가 모든 스토리의 그림에 건다.

판정되는 것은 지금 패키지의 스토리뿐이다. 앱의 components에는 아직 스토리가 없다. 앱은 자기 Storybook을 `apps/<앱>/.storybook/`에 두고 미리보기는 `@agent-os/ui/storybook`을 나눠 쓴다(ADR 0026의 2026-10-07 이력). 그 일은 web-widget과 admin-style이 한다.

## 컴포넌트 공통

- 브라우저 기본 요소로 짓는다. 변형은 `satisfies Record<변형, string>` 객체로 클래스를 고른다. 헤드리스 라이브러리는 기본 요소로 지을 수 없는 부품이 생길 때 ADR로 들인다(ADR 0026).
- props 표(디자인 파일 05절)가 계약의 최소다. 표의 이름과 겹치는 기본 속성, 나머지 기본 속성, 여러 요소를 엮는 컴포넌트가 나머지를 넘기는 요소는 `web/packages/ui/src/props.ts`의 머리 주석이 정한다. `className`과 `style`은 받지 않는다.
- 클래스는 쓰임새 토큰과 공통 크기의 유틸리티만 쓴다. `dark:`도 테마마다의 색도 두지 않는다. 테마와 모드는 쓰임새 토큰이 바꾼다.
- 클래스는 상태마다 고른다. 쓸 수 없음과 불러오는 중에는 올림·누름의 클래스를 두지 않는다. 불러오는 중은 `disabled`가 아니어서 `disabled:` 변형으로는 그 상태의 올림·누름을 끌 수 없다.
- 상호작용 컴포넌트는 모두 `focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus`로 포커스 링을 그린다.
- 쓸 수 없음은 `disabled` 속성이고 `disabled-surface`·`disabled-text`로 칠한다. 명암비 기준의 대상이 아니다.
- 불러오는 중은 `disabled`가 아니다. `aria-busy`와 `aria-disabled`를 달고 누름(제출 포함)을 무시하며, 색은 기본 그대로이고 포커스가 남고 너비가 그대로다. 도는 표시는 `loader-circle`이고 `motion-reduce:animate-none`을 함께 쓴다.
- 부품의 치수는 공통 크기의 이름 있는 단계(부품 치수 포함)로만 쓴다. 컴포넌트가 스스로 쓰는 화면 문구는 그 `<Name>.md`가 적은 것뿐이고 나머지 글자는 쓰는 쪽이 넘긴다.
- 스토리는 변형·크기와 상태 prop(아이콘, 불러오는 중, 쓸 수 없음 등)이 만드는 클래스가 모두 한 번은 그려지게 둔다. 그래야 afterEach가 그 클래스까지 판정한다. 다크(`globals: { mode: "dark" }`) 스토리를 하나 이상 둔다. play는 클래스 글자를 단언하지 않고 쓰임새 토큰이 풀린 계산값으로 본다(`src/storybook/expect.ts`). 계산값은 맞대는 토큰이 이웃 토큰과 다른 값인 테마·모드에서 잰다. 먹에서는 `focus`와 `accent`가 같아 포커스 링은 공문에서 재고, `tint`와 `disabled-surface`는 열 벌 모두 같아 계산값으로 가를 수 없다.
- 판정 스토리와 음성 사례의 태그는 글자 그대로 `"judgment"`와 `"planted"`다. Storybook의 색인이 정적으로 읽어 상수를 받지 않는다. `judgment`는 사진 비교(design-system 티켓 02)가 뺄 수 있게 달고, afterEach의 판정은 `planted`를 건너뛴다.

## 쓰는 법

- 상태를 색만으로 보이지 않는다. 아이콘 모양이나 글자를 함께 쓴다.
- 글자와 함께 놓인 아이콘은 꾸밈이라 화면 읽기 프로그램에서 숨긴다. 같은 뜻을 두 번 읽게 두지 않는다.
- 아이콘은 Lucide 모양과 선 1.75(14·16px은 2)를 지킨다. 칠한 아이콘이나 다른 묶음을 섞지 않는다.

## 패턴의 앱 공통 기준

패턴과 화면(organisms 이상)은 앱이 짓는다(ADR 0026). 디자인 파일 03·04절이 근거이고, 앱을 가리지 않는 기준은 아래다.

- 승인 묻기의 버튼은 "거부"(보조)가 먼저이고 "승인"(주)이 나중이다. 자리 폭 360px 미만에서는 둘이 위아래로 꽉 찬다.
- 도구 이름과 인자는 고치거나 줄이지 않고 글자 그대로 고정폭으로 보인다. 도구 이름은 `font-medium`(500)이다.
- 위젯은 남의 화면을 덮지 않고 대화 안에 묻는다.
- 뼈대는 0.3초를 넘길 때만 보이고 움직이지 않는다.
