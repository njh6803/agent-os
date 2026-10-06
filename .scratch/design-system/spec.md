# 디자인 시스템: 다섯 테마의 디자인 토큰과 컴포넌트 아홉을 `packages/ui`에 코드로 세우고 스토리 테스트로 판정한다

Status: ready-for-agent

슬라이스 4(`design-system`). 근거는 디자인 시스템의 원천을 코드로 정한 `docs/adr/0025`, 그 세부인 `docs/adr/0026`과 이력 넷(2026-10-06 "위젯은 자기 자리의 폭에, 관리 화면은 모바일까지 반응하고 기준 폭은 px 디자인 토큰이다", "테마는 색과 글꼴의 한 벌이고 다섯이며, 라이트·다크는 모드다", "색 토큰은 두 층이고 컴포넌트는 쓰임새 토큰만 본다", "글꼴은 패키지 셋에서 받고, 명암비와 없는 클래스는 스토리 테스트가, 사진은 정적 빌드의 Playwright가 판정한다"), 아이콘 서브패스와 shadow root 보정의 `docs/adr/0024`, Tailwind와 스토리 규칙의 `docs/adr/0021` 이력이다. 값의 원천은 Claude Design 탐색 결과 `.scratch/design-system/design/Agent OS 디자인 시스템 v3.dc.html`이다(그 폴더 `README.md`의 표, 기준 커밋 `eff1542` 어림). 그 밖에 `plan.md`의 design-system 행, 설계 인터뷰(`docs/journal/2026-10-06-05-design-system-design.md`), 탐색 프롬프트(일지 2026-10-06-09), 문서의 재료와 두 층과 버튼 글자(일지 2026-10-06-12), 그리고 이 명세의 일지(2026-10-06-13)다.

이 명세는 설계 인터뷰와 다른 세션에서 썼다. 인터뷰의 대화가 없으므로 ADR 0026과 이력, 탐색 프롬프트(`exploration-prompt.md`), 디자인 파일, 일지가 맥락을 대신했다. 용어는 `CONTEXT.md`의 화면 절(디자인 시스템, 디자인 토큰, 원색 토큰, 쓰임새 토큰, 테마, 모드)과 실행·인터럽트 절(일시정지, 끝남, 실패, 결말 없음, 승인, 허가, 거부)을 따른다. 단독 "토큰"은 쓰지 않는다(ADR 0026 Consequences).

**넷은 사용자가 골랐다.** 기본 테마는 먹이다(Claude Design의 추천). 테스트 이음매는 스토리 테스트 하나다. 그래서 명암비는 단위 테스트가 아니라 브라우저의 계산값으로 잰다(ADR 0026 이력). IBM Plex Mono는 저자의 패키지 `@ibm/plex-mono`에서 받고 설치 스크립트를 끈다(ADR 0026 이력). 승인 묻기의 버튼 글자는 "승인"과 "거부"다(일지 2026-10-06-12, `plan.md`). **명세가 스스로 정한 것은 각 절에 "(명세가 정했다)"로 표시한다.** 표시가 없는 것은 ADR, 탐색 결과, 기존 규칙에서 나왔다. 사진 비교 도구와 없는 클래스를 잡는 방법은 ADR 0026이 첫 티켓에 넘긴 측정이었는데, to-spec의 측정 규칙대로 이 명세가 쟀다. 바꾸는 문장이 있어 ADR 0026의 넷째 이력 초안을 이 PR에 올린다. 결정이 더 필요해지면 티켓은 멈추고 ADR 이력을 제안한다.

측정은 `.scratch/design-system/probes/tokens/`이고 결과는 `.scratch/design-system/probes/README.md`의 "결과 — tokens"다. 설계 인터뷰의 측정(`font_shadow/`, `storybook/`, `visual_docker/`)도 같은 README에 있다.

## Problem Statement

위젯(web-widget)과 관리 화면(admin-style)은 화면을 그리기 전에 같은 디자인 시스템을 기다린다. 그런데 지금 `web/`에는 스타일도 아이콘도 Storybook도 없고, 관리 화면은 브라우저의 기본 모양으로 돈다. 탐색이 고른 값(색 330개, 글꼴, 크기 단계, 컴포넌트 아홉의 상태와 치수)은 Claude Design의 디자인 파일 안에만 있다. 그것도 hex가 글자로 들어 있지 않고, 파일 끝의 스크립트가 OKLCH 공식으로 계산하는 모양이다.

화면은 Claude Design에서 디자인 시스템으로 그린다. 그러려면 그리기 직전에 `/design-sync`로 코드를 올려야 하는데(ADR 0025·0026), 올릴 원천이 없다. 값이 코드에 없으니 명암비를 다섯 테마 × 두 모드로 판정할 자리도 없다. Tailwind의 기본값을 비운 뒤 `text-base` 같은 익숙한 클래스가 오류 없이 아무것도 만들지 않는 실수를 잡을 자리도 없다(ADR 0026).

## Solution

**`web/packages/ui`(`@agent-os/ui`) 하나에 디자인 토큰 CSS, 테마 글꼴, atoms·molecules 아홉, Storybook을 둔다.** 앱은 소스를 그대로 import한다. 컴포넌트는 버튼, 아이콘 버튼, 아이콘, 상태 배지, 진행 표시, 카드, 글 입력, 스위치, 알림이다. 패턴(승인 묻기 등)과 화면은 organisms 이상이라 앱이 짓는다(ADR 0026).

**색은 두 층이다.** 테마마다 원색 토큰 66개(계열 여섯 × 단계 열하나, 50~950)가 있다. 쓰임새 토큰 26개와 그림자 색은 모드마다 그 가운데 하나를 가리킨다. 컴포넌트는 쓰임새 토큰의 유틸리티(`bg-bg`, `text-muted`, `bg-accent-hover` 등)만 쓴다. 원색 토큰은 `@theme` 밖의 CSS 변수라 유틸리티가 없다. 다크 모드는 원색을 따로 두지 않고 같은 원색의 다른 단계를 가리킨다.

**테마는 `data-theme`(muk, cheongnok, gongmun, hwangto, jadu), 모드는 `data-mode`(light, dark)가 고른다.** 둘은 같은 요소에 단다. 모드가 없으면 시스템 설정을 따르고, 아무것도 없으면 먹이다. 문서 뿌리, 안쪽 요소, shadow 호스트에서 모두 같은 규칙이 선다(측정 54사례).

**길이는 모두 px이고 Tailwind의 기본 테마를 비운다.** 글자 여섯 단계, 간격 일곱(0 포함), 조작 높이 둘, 아이콘 넷, 모서리 넷, 그림자 셋, 부품 치수 다섯, 기준 폭 둘(위젯의 자리 360px은 `@wide:`, 관리 화면의 창 768px은 `wide:`), 움직임 둘(도는 표시, 값 모름 진행 막대)이다.

**글꼴은 한글 Noto Sans KR 하나와 테마마다 고르는 고정폭 JetBrains Mono 또는 IBM Plex Mono다.** 셋 다 npm 패키지에서 받아 자가 호스팅한다. 관리 화면(Next)과 Storybook(Vite)이 패키지 CSS의 글꼴 `url()`을 실제 파일로 낸다(측정).

**판정은 스토리 테스트 하나와 사진 비교 게이트다.** 스토리 테스트는 실제 chromium에서 컴포넌트의 역할·이름·속성, axe, 열 벌의 쓰임새 토큰 값과 명암비 43짝, 규칙 없는 클래스, 임의값 클래스, 글꼴 적재, 기준 폭의 전환을 본다. 사진 비교는 Storybook 정적 빌드를 판을 고정한 Playwright Linux 이미지 안에서 먹의 라이트·다크로 찍는다. 올림·누름 같은 실제 입력의 상태와 움직임 줄이기도 그 Playwright가 본다(스토리 테스트의 `userEvent`는 합성 이벤트라 `:hover`·`:active`가 걸리지 않았다).

**스토리 한 벌이 미리보기, 브라우저 테스트, `/design-sync`의 원천이다.** 디자인 판단 기준은 `.claude/rules/web-design.md`이고, 컴포넌트별 쓰임은 스토리 옆의 `<Name>.md`다(ADR 0026).

## User Stories

### 최종 사용자(위젯을 쓰는 사람)

1. 최종 사용자로서, 위젯의 글자가 오래 읽어도 피곤하지 않기를 바란다. 다섯 테마의 두 모드 모두 본문이 4.5:1 이상이기 때문이다.
2. 최종 사용자로서, 키보드로 위젯을 쓸 때 지금 어디에 있는지 보이기를 바란다. 모든 상호작용 컴포넌트가 쓰임새 토큰 `focus`로 2px 링을 그리기 때문이다.
3. 최종 사용자로서, 상태를 색만으로 구분하지 않아도 되기를 바란다. 상태 배지와 알림은 아이콘 모양과 글자를 함께 쓰기 때문이다.
4. 최종 사용자로서, 폭이 320px인 자리에서도 위젯을 가로로 밀지 않고 읽고 싶다. 길이가 px이고 기준 폭 360px 아래에서 레이아웃이 세로로 쌓이기 때문이다.
5. 최종 사용자로서, 누르는 곳이 손가락이나 포인터로 맞히기 어렵지 않기를 바란다. 조작은 32px과 40px이고 가장 작은 것도 WCAG 2.2의 24px을 넘기 때문이다.
6. 최종 사용자로서, 움직임 줄이기를 켰다면 진행 표시가 계속 움직이지 않기를 바란다.
7. 최종 사용자로서, 실행이 실패하면 화면 읽기 프로그램이 곧바로 알려 주고, 정보 알림은 읽던 글을 끊지 않기를 바란다. 실패만 `role="alert"`이기 때문이다.
8. 최종 사용자로서, 거부 사유를 적는 칸의 라벨이 글을 넣는 동안에도 보이기를 바란다. 자리 글자는 라벨을 대신하지 않기 때문이다.
9. 최종 사용자로서, 쓸 수 없는 버튼이 누를 수 있는 버튼과 다르게 보이기를 바란다.
10. 최종 사용자로서, 도구 이름과 인자를 고정폭 글꼴로 읽고 싶다. 무엇을 승인하는지 글자 그대로 보아야 하기 때문이다.

### 사이트(위젯을 넣는 바깥 서비스)

11. 사이트 개발자로서, 다섯 테마 가운데 내 사이트에 어울리는 것을 이름 하나로 고르고 싶다. `data-theme`의 값이 테마 키이기 때문이다.
12. 사이트 개발자로서, 내 사이트가 어두우면 위젯도 어둡게 보이기를 바란다. 모드를 넘기면 운영체제 설정과 무관하게 따르기 때문이다(넘기는 길은 web-widget).
13. 사이트 개발자로서, 모드를 넘기지 않으면 방문자의 시스템 설정을 따르기를 바란다.

### 운영자

14. 운영자로서, 실행 목록에서 실행마다 일시정지, 끝남, 실패, 결말 없음을 한눈에 보고 싶다. 상태 배지 넷이 그것만 보이기 때문이다.
15. 운영자로서, 플러그인의 켜짐과 꺼짐을 스위치로 바꾸고 지금 상태를 글로 보고 싶다.
16. 운영자로서, 관리 화면을 휴대폰에서도 쓰고 싶다. 768px 기준 폭이 있기 때문이다(화면은 admin-style).
17. 운영자로서, 관리 화면의 테마를 다섯 가운데 하나로 고르고 싶다(고르는 화면은 admin-style).

### 위젯 개발자(web-widget)

18. 위젯 개발자로서, 디자인 토큰과 컴포넌트를 `@agent-os/ui`에서 소스 그대로 import하고 싶다. 빌드 순서가 생기지 않기 때문이다.
19. 위젯 개발자로서, 창이 아니라 위젯 자리의 폭에 반응하는 기준 폭을 쓰고 싶다. `@container`와 `@wide:`가 360px에서 갈리기 때문이다.
20. 위젯 개발자로서, shadow root 안에서도 문서와 같은 모양이기를 바란다. 패키지가 `@layer properties` 보정과 `:host(...)` 선택자를 들기 때문이다.
21. 위젯 개발자로서, 호스트에 `data-theme`과 `data-mode`를 달면 shadow 안의 색이 바뀌기를 바란다. 문서의 CSS가 없는 사이트에서도 그렇다(측정).
22. 위젯 개발자로서, 승인 묻기를 카드, 상태 배지, 여러 줄 글 입력, 버튼 둘로 짓고 싶다. 디자인 파일의 패턴 03.1이 그 조합이기 때문이다.
23. 위젯 개발자로서, 테마 하나의 글꼴이 대화 문장을 그리는 데 얼마를 받는지 알고 싶다. 측정에서 14파일, 약 150KB였다.
24. 위젯 개발자로서, 페이지 안 위젯이 사이트 문서에 고유한 이름으로 글꼴을 등록할 때 테마의 글꼴 변수(`--sans`, `--mono`)만 감싼 요소에서 다시 정하면 되기를 바란다.

### 관리 화면 개발자(admin-style)

25. 관리 화면 개발자로서, Next의 전역 CSS에서 패키지 CSS를 import하면 디자인 토큰과 글꼴이 빌드에 실리기를 바란다. `@tailwindcss/postcss`로 `next build`가 글꼴 파일을 냈기 때문이다(측정).
26. 관리 화면 개발자로서, 화면 중단점 `wide:`(768px)로 옆 탐색과 위 막대를 가르고 싶다.
27. 관리 화면 개발자로서, 관리 화면만 쓰는 컴포넌트(표, 링크 등)는 앱에 두고 디자인 토큰만 나눠 쓰고 싶다.

### 디자인 시스템에 기여하는 에이전트

28. 기여자로서, 쓰임새 토큰의 유틸리티만 쓰면 다섯 테마 × 두 모드가 저절로 맞기를 바란다. 컴포넌트에 `dark:`도 테마별 색도 없기 때문이다.
29. 기여자로서, 디자인 토큰에 없는 클래스(`text-base`, `rounded`, `font-bold`)를 쓰면 스토리 테스트가 빨개지기를 바란다.
30. 기여자로서, 원색 토큰을 유틸리티로 쓰려 하면(`bg-gray-500`) 빨개지기를 바란다.
31. 기여자로서, 임의값(`p-[13px]`)을 쓰면 빨개지기를 바란다. 규칙은 생기지만 디자인 토큰을 건너뛰기 때문이다.
32. 기여자로서, Tailwind가 훑지 않는 파일에 클래스를 쓰면 빨개지기를 바란다(측정에서 그 경우도 잡혔다).
33. 기여자로서, 대비가 부족한 짝을 만들면 열 벌 가운데 어느 테마와 모드의 어느 짝인지 메시지로 알고 싶다.
34. 기여자로서, axe 위반이 스토리 테스트를 실패시키기를 바란다.
35. 기여자로서, 원칙 III을 어기지 않고 Storybook의 globals를 읽고 싶다. `Record<string, unknown>`으로 받아 비교로 좁히면 되기 때문이다(측정).
36. 기여자로서, 패키지나 컴포넌트 폴더의 파일을 Read하면 디자인 판단 기준이 실리기를 바란다(`.claude/rules/web-design.md`).
37. 기여자로서, 디자인 토큰 값을 바꾸면 사진 비교가 바뀐 모양을 보여 주기를 바란다.

### 디자인을 고치는 사람(사용자)

38. 사용자로서, Claude Design에서 화면을 그리기 직전에 `/design-sync`로 코드의 디자인 시스템을 올리고 싶다. 스토리와 `build`가 그 원천이기 때문이다.
39. 사용자로서, 디자인 파일의 값과 코드의 값이 옮길 때 한 번은 같다는 것을 알고 싶다.
40. 사용자로서, 그 뒤 디자인 토큰의 값이 코드 한 자리(패키지의 디자인 토큰 CSS)에만 있기를 바란다.
41. 사용자로서, 테마를 하나 더할 때 원색 66개와 글꼴 셋만 적으면 되기를 바란다.

### 리뷰어와 CI

42. 리뷰어로서, 사진 비교가 운영체제와 무관하게 같은 사진을 내기를 바란다. 같은 이미지의 컨테이너 둘이 바이트까지 같은 사진을 냈기 때문이다(측정).
43. 리뷰어로서, 설치 때 원격 측정이 돌지 않기를 바란다. `@ibm/plex-mono`의 스크립트를 `allowBuilds`에서 끄기 때문이다.
44. 리뷰어로서, 새 의존성과 그 이유를 ADR에서 찾고 싶다(ADR 0026 넷째 이력).
45. 리뷰어로서, Storybook 정적 빌드와 패키지 빌드가 판정 범위에 들지 않기를 바란다. 뿌리 `.gitignore`에 두 줄이 들기 때문이다.

## Implementation Decisions

### 이음매 (사용자가 골랐다)

- **주 이음매는 `packages/ui`의 Storybook 스토리 테스트 하나다.** `@storybook/addon-vitest`가 뿌리 `vitest.config.ts`의 `storybook` 프로젝트로 실제 chromium에서 돈다. `pnpm -C web verify`의 test 단계에 들어 pre-commit도 돈다(ADR 0026). 컴포넌트의 행동, axe(addon-a11y, `test: "error"`), 쓰임새 토큰의 값과 명암비, 규칙 없는 클래스, 임의값 클래스, 글꼴 적재, 기준 폭 전환을 모두 이 이음매에서 본다.
- **둘째는 사진 비교 게이트다**(ADR 0026과 넷째 이력). 실제 입력의 상태(올림, 누름)와 움직임 줄이기는 여기의 Playwright만 본다.
- **더하지 않는 것.** 디자인 토큰 CSS를 글자로 읽는 단위 테스트, `packages/ui`의 jsdom 테스트, 새 e2e. 관리 화면의 jsdom 페이지 테스트는 그대로다.

### 패키지와 배치 (ADR 0026과 `storybook/` 측정)

- **패키지.** `web/packages/ui`, 이름 `@agent-os/ui`, `"type": "module"`. `exports`는 컴포넌트의 진입점 `.`와 디자인 토큰 CSS `./theme.css` 둘이다. 앱은 이 둘만 import한다. React는 피어다. 글꼴 셋은 `dependencies`이고 Tailwind(`tailwindcss`, `@tailwindcss/vite`, `@tailwindcss/cli`)와 Vite는 `devDependencies`다. Storybook과 Vitest 브라우저 모드 패키지는 뿌리 `web/package.json`에 둔다(스토리 테스트가 뿌리 설정의 프로젝트이기 때문이다).
- **자리.** 패키지 안에 디자인 토큰 CSS·글꼴 CSS·shadow 보정·디자인 토큰 판정 스토리의 자리, `components/atoms`와 `components/molecules`(층 경계 규칙이 경로 끝으로 맞춘다), 판정 함수의 자리, 아이콘 이름과 서브패스 선언의 자리를 둔다. 파일 이름은 티켓이 짓는다. 스토리와 `<Name>.md`는 컴포넌트와 같은 폴더다(ADR 0021 이력). atoms는 버튼, 아이콘 버튼, 아이콘, 상태 배지, 진행 표시, 카드이고, molecules는 글 입력, 스위치, 알림이다 (명세가 정했다. 라벨·도움말·상태 글·닫기 버튼처럼 다른 부품을 엮는 셋이 molecules다).
- **설치 조건.** `pnpm-workspace.yaml`의 `allowBuilds`에 esbuild, @parcel/watcher, @ibm/plex-mono를 모두 `false`로 둔다. 패키지 tsconfig의 include에 `".storybook/**/*"`를 따로 적는다. 뿌리 `.gitignore`에 앵커를 붙인 `/web/packages/ui/dist/`와 `/web/packages/ui/storybook-static/`를 더한다. 이 줄이 없으면 정적 빌드의 번들이 lint에 걸린다(측정에서 다시 봤다).
- **빌드.** `build`는 `tsc -p tsconfig.build.json`과 Tailwind CLI로 `dist/`를 낸다. `/design-sync`만 쓰고 커밋하지 않는다(ADR 0026). 앱은 `dist`를 쓰지 않는다.

### 디자인 토큰의 값과 원천 (명세가 정했다)

- **값은 커밋한 디자인 파일이 원천이고, `.scratch/design-system/probes/tokens/design.mjs`가 뽑는 그대로다.** 원색 토큰 330개(테마 다섯 × 66)를 디자인 토큰 CSS에 hex 글자로 둔다. 디자인 파일의 OKLCH 공식과 단계 밝기 표는 코드에 옮기지 않는다. 생성 단계를 두지 않기 위해서다. 이 명세는 hex 330개를 다시 적지 않는다.
- **옮긴 뒤의 원천은 코드다**(ADR 0025·0026). 첫 티켓은 옮길 때 `design.mjs`의 출력과 코드의 값이 같은지 한 번 보고 일지에 적는다. 영구 테스트는 디자인 파일을 읽지 않는다. 디자인을 바꾸면 Claude Design에서 다시 내보내고 그 차이를 코드에 옮긴다.
- **hex는 소문자다.** Prettier가 CSS의 hex를 소문자로 바꾼다. 계산값을 비교하는 코드는 대소문자를 맞춘다(측정).

### 색 — 원색 토큰 (탐색이 골랐다. 이름은 명세가 정했다)

- **계열 여섯 × 단계 열하나.** 계열은 `gray`, `accent`, `danger`, `warning`, `success`, `info`이고 단계는 `50`, `100`, `200`, …, `900`, `950`이다. 이름은 `--<계열>-<단계>`(예: `--gray-500`)이고 다섯 테마가 같다(ADR 0026 셋째 이력이 넘긴 "단계의 수와 이름"). 단계마다 밝기가 테마 사이에 같아서 같은 단계를 가리키면 명암비도 비슷하다.
- **다크 모드용 원색을 따로 두지 않는다.** 모드는 쓰임새 토큰이 가리키는 단계를 바꾼다(셋째 이력이 넘긴 것). 다크의 바탕은 950, 글자는 50이다.
- **유틸리티가 없다.** `@theme` 밖의 CSS 변수라 `bg-gray-500`은 규칙을 만들지 않았다(측정). 그래서 규칙 없는 클래스의 판정이 원색 클래스도 잡는다.

### 색 — 쓰임새 토큰 (탐색이 골랐다. 코드의 이름과 그림자 색의 모양은 명세가 정했다)

열둘은 탐색 프롬프트가 제안한 것이고, 열넷은 상태 표가 더한 것이다. CSS 변수는 `--<이름>`이고 유틸리티는 Tailwind의 색 이름 공간(`--color-<이름>`)을 거쳐 `bg-<이름>`, `text-<이름>`, `border-<이름>`, `outline-<이름>`이다.

| 이름 | 쓰임 | 라이트 | 다크 |
|---|---|---|---|
| `bg` | 바탕 | `gray-100` | `gray-950` |
| `raised` | 올라온 바탕(카드, 입력, 위험 버튼) | `gray-50` | `gray-900` |
| `text` | 글자 | `gray-900` | `gray-50` |
| `muted` | 흐린 글자, 자리 글자, 꺼진 스위치 손잡이 | `gray-600` | `gray-400` |
| `border` | 테두리(입력, 꺼진 스위치) | `gray-500` | `gray-500` |
| `accent` | 강조(주 버튼, 켜진 스위치, 진행 막대) | `accent-600` | `accent-400` |
| `on-accent` | 강조 위 글자 | `gray-50` | `accent-950` |
| `danger` | 위험 | `danger-600` | `danger-400` |
| `warning` | 경고 | `warning-600` | `warning-400` |
| `success` | 성공 | `success-600` | `success-400` |
| `info` | 정보 | `info-600` | `info-400` |
| `focus` | 포커스 링 | `accent-600` | `accent-400` |
| `tint` | 옅은 면(보조 버튼, 요청 말풍선, 결말 없음 배지, 진행 트랙, 뼈대) | `gray-200` | `gray-800` |
| `tint-hover` | 옅은 면 올림 | `gray-300` | `gray-700` |
| `tint-press` | 옅은 면 누름 | `gray-400` | `gray-600` |
| `accent-hover` | 강조 올림 | `accent-700` | `accent-300` |
| `accent-press` | 강조 누름 | `accent-800` | `accent-200` |
| `border-hover` | 테두리 올림 | `gray-600` | `gray-400` |
| `danger-tint` | 위험 면(실패 배지·알림, 위험 버튼 올림) | `danger-100` | `danger-900` |
| `danger-tint-press` | 위험 면 누름 | `danger-200` | `danger-800` |
| `warning-tint` | 경고 면(일시정지 배지, 경고 알림) | `warning-100` | `warning-900` |
| `success-tint` | 성공 면(끝남 배지) | `success-100` | `success-900` |
| `info-tint` | 정보 면(정보 알림) | `info-100` | `info-900` |
| `disabled-surface` | 쓸 수 없음 면 | `gray-200` | `gray-800` |
| `disabled-text` | 쓸 수 없음 글자 | `gray-500` | `gray-500` |
| `divider` | 구분선, 카드 테두리 | `gray-200` | `gray-800` |

- **공문의 예외.** 라이트에서 `accent`는 `accent-700`, `accent-hover`는 `accent-800`, `accent-press`는 `accent-900`, `focus`는 `warning-600`을 가리킨다. 다크에서 `focus`는 `warning-400`이다. 나머지 넷은 위 표 그대로다.
- **그림자 색.** `--shadow-color`다. 라이트는 `gray-900`의 14%, 다크는 `gray-950`을 검정과 반씩 섞은 색의 70%다(`color-mix`로 적는다). 디자인 파일의 이름은 `--shadow`인데, Tailwind의 그림자 이름 공간(`--shadow-1` 등)과 읽을 때 헷갈려 이름을 바꿨다 (명세가 정했다).
- **`color-scheme`.** 라이트·다크 규칙이 `color-scheme`도 함께 바꾼다. 스크롤바와 폼 기본 요소가 모드를 따른다 (명세가 정했다).

### 테마와 모드 (ADR 0026 둘째 이력. 키와 선택자는 명세가 정했다)

| 키 | 이름 | 고정폭 글꼴 | 중간 굵기 | 라이트 강조 | 탐색의 한 줄 |
|---|---|---|---|---|---|
| `muk` | 먹(기본) | JetBrains Mono | 600 | `#285cc2` | 따뜻한 회색에 파랑 하나. 어느 사이트에서도 가장 덜 튄다 |
| `cheongnok` | 청록 | IBM Plex Mono | 500 | `#00736e` | 차가운 회색과 청록 |
| `gongmun` | 공문 | JetBrains Mono | 600 | `#21469c` | 남색 강조, 포커스 링은 주황 |
| `hwangto` | 황토 | IBM Plex Mono | 600 | `#974c00` | 종이 같은 바탕과 갈색 강조, 위험은 자홍 쪽 |
| `jadu` | 자두 | JetBrains Mono | 500 | `#7847a6` | 자두색 강조 |

- **고르는 법.** `data-theme`에 키를, `data-mode`에 `light`나 `dark`를 둘 다 같은 요소에 단다. 모드가 없으면 `prefers-color-scheme`을 따른다. 속성이 없는 문서와 호스트는 먹이다. 문서(관리 화면, iframe 위젯)는 `html`에, 페이지 안 위젯은 호스트에 단다(ADR 0026). 스토리처럼 한 문서에 여러 벌을 나란히 둘 때는 어느 요소에 달아도 그 아래가 바뀐다(측정에서 안쪽 요소 열 벌).
- **값은 로마자 키, 화면의 이름은 한국어다.** 속성 값에 한글을 쓰지 않는다.

### 디자인 토큰 CSS의 모양 (명세가 정했다. 모양은 프로브 `tokens/setup.mjs`의 생성 CSS에서 왔다)

- **디자인 토큰 CSS 하나**(`./theme.css`로 낸다)가 `@import "tailwindcss" source(none)`, 글꼴 CSS의 `@import`, 그리고 `@source`를 둔다. `@source`는 컴포넌트와 스토리를 모두 덮는다(패키지의 소스 전체). 프로브의 첫 실행에서 컴포넌트 폴더만 두자 스토리 파일에 쓴 `flex`가 규칙을 만들지 않았고 판정 함수가 그것을 잡았다(손으로 봤다. 커밋한 프로브는 고친 뒤의 모양이다).
- **`@theme`에는 값이 글자 그대로인 것을 둔다.** `--*: initial`로 기본값을 비우고 글자 크기, 간격, 조작 높이, 아이콘, 부품 치수, 모서리, 굵기(regular, strong), 기준 폭, 움직임과 그 keyframes를 둔다.
- **`@theme inline`에는 테마나 모드마다 바뀌는 CSS 변수를 읽는 것을 둔다.** `--color-<쓰임새>: var(--<쓰임새>)` 26개, `--font-sans: var(--sans)`, `--font-mono: var(--mono)`, `--default-font-family`, `--default-mono-font-family`, `--font-weight-mid: var(--weight-mid)`, 중간 굵기를 쓰는 글자 단계의 `--text-<단계>--font-weight`, 그림자 셋이다. inline이라 유틸리티가 그 변수를 바로 읽는다(`bg-bg`는 `background-color: var(--bg)`).
- **`@layer theme`에 원색과 쓰임새를 선언한다.** 원색 66개와 글꼴 변수(`--sans`, `--mono`, `--weight-mid`)는 테마 선택자(`:root, :host, [data-theme="muk"]`와 테마마다 `[data-theme="<키>"]`)에 둔다. 쓰임새 26개와 `--shadow-color`, `color-scheme`은 라이트를 `:root, :host, [data-theme], [data-mode]`에, 다크를 `[data-mode="dark"]`에, 그리고 `prefers-color-scheme: dark` 아래의 `:root:not([data-mode])`, `[data-theme]:not([data-mode])`에 둔다. 공문의 예외는 그 뒤에 `[data-theme="gongmun"][data-mode=…]`와 시스템 모드 짝으로 둔다. 모든 선택자는 `:host(…)` 짝을 함께 쓴다.
- **쓰임새를 테마를 다는 요소마다 다시 선언하는 이유.** 사용자 정의 속성의 `var()`는 선언한 요소에서 풀린다. 쓰임새를 `:root`에만 두면, 안쪽 요소의 `data-theme`이 원색을 바꿔도 쓰임새는 뿌리에서 이미 풀린 값을 물려받는다.
- **shadow root.** 패키지가 ADR 0024의 `@layer properties` 재선언 시트를 만드는 함수를 든다(설계 측정 `storybook/`의 표본 그대로). 상속 속성(글꼴, 글자색, 줄 높이, 자간 등)을 다시 정하는 감싼 요소의 규칙도 패키지가 든다(ADR 0026). 그 표시의 이름은 첫 티켓이 짓고, 실제 커스텀 요소 안의 측정은 web-widget이 한다.
- **`@layer base`.** `html`과 `:host`에 `background-color: var(--bg)`, `color: var(--text)`를 둔다.

### 공통 크기 (탐색이 골랐다. Tailwind의 이름은 명세가 정했다)

| 묶음 | 디자인 토큰 | 값 | 유틸리티 |
|---|---|---|---|
| 글자 | `title` | 24/32px, strong | `text-title` |
| | `heading` | 18/26px, strong | `text-heading` |
| | `body` | 15/24px, regular | `text-body` |
| | `small` | 13/20px, mid | `text-small` |
| | `caption` | 12/16px, mid | `text-caption` |
| | `code` | 13/20px, regular, 고정폭과 함께 | `text-code font-mono` |
| 간격 | `0` `1` `2` `3` `4` `6` `8` | 0 4 8 12 16 24 32px | `p-4`, `gap-2`, `inset-y-0` 등. `--spacing`은 두지 않는다 |
| 조작 높이 | `control-m` `control-s` | 40 32px | `h-control-m` |
| 아이콘 | `icon-xs` `icon-s` `icon-m` `icon-l` | 14 16 20 24px | `size-icon-m` |
| 부품 치수 | `switch-w` `switch-h` `row-touch` `progress` `field-multi` | 36 20 48 6 88px | `w-switch-w`, `min-h-row-touch`, `h-progress`, `min-h-field-multi` |
| 모서리 | `s` `m` `l` `full` | 4 6 10 999px | `rounded-m` |
| 그림자 | `1` `2` `3` | `0 1px 2px`, `0 4px 16px`, `0 12px 32px` + `--shadow-color` | `shadow-1` |
| 굵기 | `regular` `mid` `strong` | 400, 테마의 중간(500·600), 600 | `font-mid` |
| 기준 폭 | 위젯의 자리 | 360px(컨테이너) | `@container`의 자식에 `@wide:` |
| | 관리 화면의 창 | 768px(미디어) | `wide:` |
| 움직임 | `spin` `progress` | `spin 1s linear infinite`, `progress 1.2s ease-in-out infinite` | `animate-spin`, `animate-progress` |

- **간격 `0` (명세가 정했다).** 디자인 파일의 간격 단계에는 0이 없다. `--spacing`을 비우면 `inset-y-0` 같은 0도 규칙을 만들지 않아(측정) `0`을 둔다.
- **부품 치수 (명세가 정했다).** 디자인 파일의 스위치 트랙(36×20px), 스위치 줄(48px 이상), 진행 트랙(6px), 여러 줄 입력(88px 이상)은 간격 단계에 없다. 임의값을 쓰지 않으려고 이름 있는 간격으로 둔다. 손잡이 12px과 띄움 4px·16px은 간격 단계(`3`, `1`, `4`)다.
- **움직임 (명세가 정했다).** 디자인 파일에는 움직임이 없다(도는 표시를 정지 그림으로 그렸다). 기본값을 비우면 Tailwind의 `animate-spin`과 그 keyframes도 사라져 우리 값으로 둘을 둔다. 쓰는 자리는 불러오는 중의 도는 표시와 값 모름 진행 막대이고 둘 다 `motion-reduce:animate-none`을 함께 쓴다. 측정: 정의하지 않은 `animate-pulse`는 규칙이 없었고, 우리 둘은 돌았으며, 움직임 줄이기에서 animation-name이 `none`이었다.
- **테두리 1px, 포커스 링 2px과 바깥 띄움 2px**은 디자인 토큰을 두지 않고 Tailwind의 숫자 유틸리티(`border`, `outline-2`, `outline-offset-2`)로 쓴다. 기본값을 비워도 규칙을 만들었다(측정의 표본 버튼).
- **기준 폭은 이 둘을 정의한다.** 표본이 두 변형을 쓰자 시트의 px 조건이 `(width >= 360px)`과 `(width >= 768px)`이었다(측정). 폭 359px에서 `@wide:flex-row`는 column, 360px부터 row였다. 그 밖의 중단점과 컨테이너 크기는 두지 않는다.
- **누르는 목표.** WCAG 2.2 AA의 24px이 하한이다. 조작은 32px과 40px이고 스위치는 라벨 전체가 누르는 곳(높이 48px 이상)이라, 터치에서 더 크게 두지 않는다 (명세가 정했다. ADR 0026 첫째 이력이 넘긴 것).
- **rem은 0이다.** 패키지 CSS에 rem이 없어야 한다(ADR 0026). 글꼴 CSS도 rem을 쓰지 않는다.

### 글꼴 (사용자가 IBM의 길을 골랐다. 나머지는 명세가 정했다. ADR 0026 넷째 이력)

- **글꼴과 굵기.** 한글은 다섯 테마 모두 Noto Sans KR이고 굵기는 400, 500, 600을 싣는다(500은 청록·자두의 중간 굵기). 고정폭은 먹·공문·자두가 JetBrains Mono, 청록·황토가 IBM Plex Mono이고 굵기는 400과 500이다(500은 승인 묻기의 도구 이름).
- **패키지.** `@fontsource/noto-sans-kr`(굵기 CSS 셋을 `@import`. Google Fonts의 동적 서브셋 조각이 굵기마다 124개다(측정)), `@fontsource/jetbrains-mono`(400, 500), `@ibm/plex-mono`(저자의 split woff2를 `local()` 없이 패키지의 글꼴 CSS에서 다시 선언. 굵기 400·500의 바른 모양). 판은 측정 판(5.3.0, 5.3.0, 2.5.0)에서 시작한다.
- **글꼴 스택.** `"Noto Sans KR", system-ui, sans-serif`와 `"<고정폭>", ui-monospace, monospace`다. 글꼴이 막히면 시스템 글꼴로 그린다.
- **빌드.** Storybook(Vite)과 관리 화면(Next 16, `@tailwindcss/postcss`)이 Fontsource CSS의 상대 `url()`을 실제 파일로 냈다(누락 0). Fontsource CSS는 woff도 함께 적어 빌드 산출물에 woff가 들지만 브라우저는 woff2만 받았다(측정). woff를 빼는 것은 하지 않는다.
- **양.** 테마 하나로 위젯의 대화 문장 둘과 도구 이름을 그릴 때 14파일, 148,704~156,292바이트를 받았다(측정). 위젯의 예산은 web-widget이 본다.
- **페이지 안 위젯.** 패키지 CSS의 글꼴 이름은 글꼴의 본래 이름이다. 페이지 안 위젯은 사이트 문서에 고유한 이름으로 FontFace API를 써서 등록하고(ADR 0026), 감싼 요소에서 `--sans`와 `--mono`만 그 이름으로 다시 정한다. 그 코드와 글꼴 파일 목록은 web-widget이다.

### 컴포넌트 아홉 (탐색이 골랐다. 공통 규칙과 props의 차이는 명세가 정했다)

props의 원천은 디자인 파일 05절의 props 표다. 상태 표(기본, 올림, 누름, 포커스, 쓸 수 없음, 오류, 불러오는 중)와 해부도는 디자인 파일 02절이다. 아래는 그 요약과 이 저장소의 규칙에 맞춘 차이다.

**공통 (명세가 정했다. ADR 0026)**

- 브라우저 기본 요소로 짓는다. 변형은 `satisfies Record<변형, string>` 객체로 클래스를 고른다. `className`과 `style` prop은 두지 않는다.
- props 표가 계약의 최소다. 표에 없는 그 요소의 기본 속성(`aria-*`, `id`, `name`, `maxLength` 등)이 필요하면 `className`·`style`을 뺀 채로 받는다. 그 타입의 모양은 티켓이 정한다.
- 클래스는 쓰임새 토큰과 공통 크기의 유틸리티만 쓴다. `dark:`, 원색, 임의값(`[...]`)을 쓰지 않는다.
- 모든 상호작용 컴포넌트는 `focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-focus`로 포커스 링을 그린다.
- 쓸 수 없음은 `disabled` 속성이고 `disabled-surface`·`disabled-text`를 쓴다. 명암비 기준의 대상이 아니다.
- 불러오는 중은 `aria-busy="true"`이고, 너비가 그대로이며, 다시 누를 수 없다. 도는 표시는 `loader-circle` 아이콘이고 `motion-reduce`에서 멈춘다.
- 컴포넌트가 스스로 쓰는 화면 문구는 다음뿐이다. 상태 배지의 일시정지·끝남·실패·결말 없음(용어집의 말), 스위치의 켜짐·꺼짐(관리 화면의 지금 문구), 글 입력의 "선택", 알림 닫기 버튼의 이름 "닫기"다. 나머지 글자는 쓰는 쪽이 넘긴다.
- 부품의 치수는 공통 크기의 이름 있는 단계(부품 치수 포함)로만 쓴다.

**atoms**

1. **버튼(`Button`).** `<button>`. `variant`: `"primary"`(기본) | `"secondary"` | `"danger"`. `size`: `"m"`(40px, 기본) | `"s"`(32px). `children: string`(글자, 동사로 짧게), `onClick`, `icon?: IconName`(글자 앞), `loading`, `disabled`, `type`: `"button"`(기본) | `"submit"`. 주는 `accent`·`on-accent`, 보조는 `tint`·`text`, 위험은 `raised` 바탕에 `danger` 글자와 테두리다. 올림·누름은 `accent-hover`·`accent-press`, `tint-hover`·`tint-press`, `danger-tint`·`danger-tint-press`다. 오류 상태는 없다(실패는 알림으로 알린다).
2. **아이콘 버튼(`IconButton`).** `<button>`. `variant`: `"primary"` | `"secondary"` | `"ghost"`(기본). `size`: `"m"`(40×40, 기본) | `"s"`(32×32). `icon: IconName`, `label: string`(필수, `aria-label`과 `title`), `onClick`, `loading`, `disabled`. 투명은 바탕 없이 `muted`이고, 올리면 `tint`·`text`, 누르면 `tint-hover`·`text`다.
3. **아이콘(`Icon`).** `<svg>`. `name: IconName`, `size`: `"14"` | `"16"` | `"20"`(기본) | `"24"`, `label: string | null`(기본 `null`이면 `aria-hidden="true"`, 있으면 `role="img"`와 `aria-label`). 색은 `currentColor`, 선은 1.75px(14·16px은 2px), 끝과 꺾임은 둥글다.
4. **상태 배지(`StatusBadge`).** `<span>`. `status`: `"paused"` | `"done"` | `"failed"` | `"no-outcome"`. 글자는 일시정지·끝남·실패·결말 없음이고, 아이콘은 `circle-pause`·`circle-check`·`circle-x`·`circle-minus`, 색은 `warning`/`warning-tint`, `success`/`success-tint`, `danger`/`danger-tint`, `muted`/`tint`다. 높이 24px, `text-caption`. 누르는 곳이 아니다.
5. **진행 표시(`Progress`).** `<div role="progressbar">`. `value: number | null`(`null`이면 값 모름), `max`(기본 1), `label: string`(보이는 이름이자 접근 이름), `tone`: `"accent"`(기본) | `"danger"`. 트랙은 `tint`, 막대는 `accent`나 `danger`, 높이 `progress`(6px). 값을 모르면 `aria-valuenow`가 없고 막대가 `animate-progress`로 옮겨 다니며 `motion-reduce`에서 멈춘다.
6. **카드(`Card`).** `as`: `"div"`(기본) | `"section"` | `"article"`. `elevation`: `"0"` | `"1"`(기본) | `"2"` | `"3"`(`shadow-n`, `"0"`은 그림자 없음), `padding`: `"3"` | `"4"`(기본), `children`(내용). 바탕 `raised`, 테두리 `divider`, 모서리 `l`. 카드 전체를 누르는 곳으로 만들지 않는다.

**molecules**

7. **글 입력(`TextField`).** `<label>`과 `<input type="text">` 또는 `<textarea>`. `variant`: `"single"`(기본, 높이 `control-m`) | `"multi"`(최소 `field-multi`, 세로로만 늘인다). `label`, `value`, `onChange(value: string)`, `placeholder`, `help: string | null`, `error: string | null`(있으면 `aria-invalid="true"`, 테두리와 도움말이 `danger`, 아이콘과 글로 함께 알린다), `optional`(라벨 옆 "선택"), `disabled`, `rows`(기본 3). 도움말은 `aria-describedby`로 잇는다.
8. **스위치(`Switch`).** `<label>` 안의 `<input type="checkbox" role="switch">`. `checked`, `onChange(checked: boolean)`, `label`, `disabled`. 라벨 아래에 지금 상태를 켜짐·꺼짐으로 적는다. 트랙 `switch-w`×`switch-h`(36×20px), 손잡이 12px, 줄 높이 `row-touch` 이상. 꺼짐은 `raised` 트랙에 `border` 테두리와 `muted` 손잡이, 켜짐은 `accent`에 `on-accent` 손잡이다. 오류 상태는 없다(바꾸지 못하면 쓰는 쪽이 되돌리고 알림으로 알린다).
9. **알림(`Alert`).** `<div>`. `tone`: `"danger"` | `"warning"` | `"info"`(기본). `title`, `children`(본문), `actions`(버튼과 링크의 자리), `onClose`(있으면 투명·작은 아이콘 버튼 `x`, 이름 "닫기"). 실패만 `role="alert"`, 경고와 정보는 `role="status"`다. 바탕은 `<tone>-tint`, 아이콘은 `<tone>` 색, 제목은 `text`, 본문은 `muted`다.

**아이콘 이름 (명세가 정했다).** `IconName`은 디자인 파일의 열여섯을 Lucide의 이름으로 옮긴 것이다. `send`(보내기), `x`(닫기), `check`(승인), `shield-check`(승인 묻기), `circle-pause`(일시정지), `circle-check`(끝남), `circle-x`(실패), `circle-minus`(결말 없음), `triangle-alert`(경고), `info`(정보), `wrench`(도구), `plug`(플러그인), `list`(실행), `search`(찾기), `menu`(메뉴), `ellipsis`(더 보기)다. 불러오는 중의 `loader-circle`은 컴포넌트 안에서만 쓴다. import는 ADR 0024의 서브패스(`lucide-react/dist/esm/icons/<이름>`)와 손으로 둔 모듈 선언이다. 이름이 그 판에 있는지는 티켓이 파일로 확인한다.

### 패턴과 화면은 앱이 짓는다 (ADR 0026. 명세가 정했다)

- 디자인 파일의 패턴 넷(03.1 승인 묻기, 03.2 실행 실패 알림, 03.3 빈 목록, 03.4 불러오는 중인 목록)과 화면 셋(04절)은 organisms·templates라 패키지에 두지 않는다. web-widget과 admin-style이 그 절을 근거로 짓는다.
- 그 가운데 앱을 가리지 않는 판단 기준은 `.claude/rules/web-design.md`에 든다. 승인 묻기의 버튼은 "거부"(보조)가 먼저이고 "승인"(주)이 나중이다. 자리 폭 360px 미만에서는 둘이 위아래로 꽉 찬다. 도구 이름과 인자는 고치거나 줄이지 않고 글자 그대로, 고정폭으로 보인다. 위젯은 남의 화면을 덮지 않고 대화 안에 묻는다. 뼈대는 0.3초를 넘길 때만 보이고 움직이지 않는다.

### Storybook과 판정 함수 (측정. 명세가 정했다)

- **미리보기.** 미리보기 설정이 디자인 토큰 CSS를 전역으로 싣는다. globals는 셋이다. `theme`(키 다섯, 기본 `muk`), `mode`(`system`(기본) | `light` | `dark`. `system`이면 속성을 두지 않는다), `shadow`(`off` | `on` | `raw`). 데코레이터가 문서 뿌리나 shadow 호스트에 단다. globals는 `Record<string, unknown>`으로 받아 비교로 좁힌다(원칙 III, `storybook/` 측정).
- **스토리의 이름.** play가 있는 스토리는 `name`을 행동을 말하는 한국어 문장으로 둔다. 테스트 이름이 되기 때문이다(`.claude/rules/web-workspace.md`의 TS 테스트 이름 규칙). 내보내기 이름은 영어 식별자이고, 아래의 Matrix 같은 이름은 이 명세가 부르는 이름이다.
- **판정 함수**는 패키지 안의 자기 자리에 두고 의존성이 없다. 패키지의 공개 표면(진입점 `.`)에 넣지 않는다.
  - `contrastRatio(a, b)`: WCAG 2.2의 대비. `#RRGGBB`를 받는다.
  - `sheetsDefining(name, sheets)`: 디자인 시스템의 시트(`--gray-50`을 정의하는 시트)만 고른다. Storybook 자신의 시트를 뺀다.
  - `classesWithoutRules(root, sheets)`: 그린 요소의 class 낱말 가운데, `@media`·`@layer`·`@container`·CSS 중첩 안까지 내려가도 그것을 고르는 규칙이 없는 것.
  - `arbitraryClasses(root)`: `[`가 든 class 낱말.
  - 측정에서 넣어 본 정의 없는 `var()`의 판정은 두지 않는다. 임의값 판정이 이미 잡는 것만 잡았다.
- **명암비 짝 43개.** 디자인 파일이 재는 짝에 컴포넌트가 쓰는 짝을 더했다. 4.5:1인 짝은 `text`, `muted`, `accent`, `danger`, `warning`, `success`, `info` 각각을 `bg`·`raised`와 맞댄 14개, `on-accent`/`accent`, `text`/`tint`, `muted`/`tint`, `text`/`tint-hover`, `text`/`tint-press`, `on-accent`/`accent-hover`, `on-accent`/`accent-press`, `danger`/`danger-tint`, `muted`/`danger-tint`, `danger`/`danger-tint-press`, `warning`/`warning-tint`, `muted`/`warning-tint`, `success`/`success-tint`, `info`/`info-tint`, `muted`/`info-tint`, 그리고 알림 제목의 `text`를 알림 면 셋(`danger-tint`, `warning-tint`, `info-tint`)과 맞댄 셋이다. 3:1인 짝은 `border`·`focus`를 `bg`·`raised`와 맞댄 넷, `border-hover`를 `bg`·`raised`와 맞댄 둘, 알림 안 버튼의 포커스 링 `focus`를 알림 면 셋과 맞댄 셋, 진행 막대의 `accent`/`tint`, `danger`/`tint`다. 성공 톤의 알림은 없어 `success-tint` 위의 제목 짝은 두지 않는다. 열 벌 모두 넘었다(측정. 가장 낮은 값은 먹·청록 라이트의 `border`/`bg` 3.28이고, 디자인 파일이 재지 않은 짝 가운데 가장 낮은 것은 청록 라이트의 `accent`/`tint` 4.59다. 이 둘째 값은 `design.mjs`의 출력으로 손으로 셈했다).
- **디자인 토큰의 판정 스토리**: Matrix(안쪽 요소에 열 벌을 달아 쓰임새 26개가 모두 `#RRGGBB`로 풀리고, 테마를 바꾸면 `accent`의 값이 바뀌며(다섯이 모두 다르다. 위험·성공 계열처럼 테마 사이에 같은 값도 있다), 짝 43개가 기준을 넘는다), Responsive(위 기준 폭 둘), Fonts(글꼴 일곱 벌이 `document.fonts.load`로 `loaded`), Classes(컴포넌트 아홉의 모든 변형과 크기, 도는 표시와 진행 막대를 그리고 규칙 없는 클래스와 임의값이 없다).
- **상태 색.** 스토리 테스트의 `userEvent`(`storybook/test`)는 합성 이벤트라 `:hover`·`:active`가 걸리지 않았고 배경이 그대로였다. Tab 포커스는 `:focus-visible`이 걸렸다(측정). 그래서 포커스 링은 스토리 테스트가, 올림과 누름은 사진 비교가 Playwright의 실제 입력으로 본다. 올림·누름의 색이 쓰임새 토큰인지는 규칙 없는 클래스의 판정(`hover:bg-accent-hover`의 규칙이 있다)과 Matrix(그 쓰임새 토큰의 값과 명암비)가 함께 받친다.

### 사진 비교 게이트 (ADR 0026과 넷째 이력. 모양은 명세가 정했다)

- **도구.** Playwright Test의 `toHaveScreenshot`, `maxDiffPixels: 0`이다. 입력은 Storybook 정적 빌드이고, 스토리 `iframe.html`을 route로 파일에서 낸다. 이미지는 `mcr.microsoft.com/playwright:v1.63.0-noble`이고 Playwright 판과 함께 올린다. CI와 로컬 비교는 태그에 digest까지 붙여(`<이미지>:<태그>@sha256:<digest>`) 같은 이미지를 쓴다. 같은 태그가 다시 빌드되면 글꼴과 라이브러리가 바뀌어 코드 변경 없이 정답 사진이 모두 깨질 수 있기 때문이다. digest의 값은 사진 비교 티켓이 그때 받은 이미지에서 적고, Playwright 판을 올릴 때 태그와 함께 바꾼다(PR #153의 CodeRabbit 지적).
- **찍는 것.** 패키지의 스토리 전부를 먹의 라이트와 다크로 찍는다(ADR 0026 둘째 이력). 판정 스토리(Matrix 등)는 뺀다. 상호작용 컴포넌트는 실제 입력의 올림, 누름, 키보드 포커스를 더 찍는다(누른 뒤에는 빈 자리를 눌러 순차 탐색의 출발점을 돌린 다음 Tab을 누른다. 측정에서 그러지 않자 포커스가 버튼에 오지 않았다).
- **움직임 줄이기.** 같은 Playwright가 `reducedMotion: "reduce"`에서 도는 표시와 값 모름 진행 막대의 animation-name이 `none`인지 본다. 사진은 Playwright가 움직임을 멈춰 찍으므로 사진으로는 가르지 못한다.
- **정답 사진**은 한 벌이고 컨테이너 안에서만 만든다. 자리는 패키지 안이고 커밋한다. 갱신 명령도 컨테이너에서만 돈다.
- **CI와 로컬.** CI는 이미지를 컨테이너로 쓰는 새 잡이 그 안에서 설치하고(네트워크는 설치에만 쓴다) 정적 빌드를 지은 뒤 비교한다. 필수 검사 `verify`가 `needs`로 모은다. 로컬에서는 `packages/ui`를 건드렸을 때 정적 빌드를 호스트에서 짓고 비교만 `--network none` 컨테이너에서 한다. 정적 빌드는 밖으로 요청을 내지 않았다(측정). 게이트가 열둘이 되는 문서 갱신(ADR 0026 Consequences의 목록)은 이 게이트를 들이는 티켓이 한다.
- **측정.** Windows에서 지은 정적 빌드를 컨테이너 둘이 찍은 14장(스토리 넷 × 라이트·다크, 주 버튼의 올림·누름·포커스 × 라이트·다크)이 바이트까지 같았다. 같은 이미지의 컨테이너 안에서 Linux로 지은 정적 빌드도 그 정답을 바이트까지 같게 지났다(Further Notes의 Linux 빌드). 실제 마우스의 올림·누름은 열 벌 모두 `accent-hover`·`accent-press`의 값이었다. GitHub 러너는 로컬에서 잴 수 없어 첫 구현 PR의 CI가 본다.

### 문서와 설정 (티켓이 고친다. 이 PR이 고친 것은 따로 적었다)

- **`.claude/rules/web-design.md`**(paths: `web/packages/ui/**`, `web/apps/*/components/**`)를 새로 둔다. 디자인 판단 기준이고 `/design-sync`의 guidelines다(ADR 0026). 위 컴포넌트 공통 규칙, 디자인 파일의 "쓰는 법"(해도 되는 것과 안 되는 것), 패턴의 앱 공통 기준을 담는다. 판정 함수가 잡는 것(원색·임의값·없는 클래스)은 실행 명령만 적는다.
- **`<Name>.md`.** 컴포넌트마다 디자인 파일의 "쓰는 법"(언제 쓰는지, 해도 되는 것과 안 되는 것)을 옮긴다.
- **`.design-sync/`.** `/design-sync`를 처음 돌릴 때 생긴다. 상태 파일은 커밋하고 산출물은 무시한다(ADR 0026). 돌리는 것은 사용자다.
- **바뀌는 설정.** `web/pnpm-workspace.yaml`의 `allowBuilds`, 뿌리 `.gitignore` 두 줄, `web/vitest.config.ts`의 `storybook` 프로젝트, `web/package.json`의 Storybook 패키지, CI web 잡의 chromium 설치, 사진 비교 잡과 `verify`의 `needs`.
- **바뀌는 문서.** `README.md`의 트리(`packages/ui`), `CLAUDE.md`의 검증 명령과 게이트 수, `docs/constitution/operations.md`, `ci.yml`의 머리 주석(사진 비교 티켓). `docs/constitution/tech.md`의 웹 행은 이 PR이 글꼴을 더했다.
- **잔존 grep.** 사진 비교 티켓이 `게이트는 열하나`, `열하나(린트는`을 찾는다. 명암비를 단위 테스트로 적은 살아 있는 문장(`plan.md`의 design-system 행)은 이 PR이 고쳤고, ADR 0026 본문의 그 문장들은 포인터로 넷째 이력을 가리킨다. 기록은 제외한다(`docs/constitution/operations.md`의 문서 위치).

## Testing Decisions

**좋은 테스트는 바깥 행동만 본다.** 역할과 접근 이름, `aria-*`와 기본 속성, 쓰임새 토큰이 풀린 계산값(색, 높이, outline), axe 위반, 시트에 규칙이 있는지, 사진이다. 클래스 글자를 단언하지 않는다(`className`에 `bg-accent`가 있는지 보지 않는다). 쓰임새 토큰의 값은 디자인 파일과 맞대지 않고, 형식(`#RRGGBB`), 테마 사이의 차이, 명암비로 본다.

### 주 이음매 — 스토리 테스트 (새 `packages/ui`)

- **디자인 토큰.** Matrix, Responsive, Fonts, Classes(위 절). shadow 표본 하나는 같은 컴포넌트를 문서와 shadow 호스트(속성은 호스트에) 안에 함께 그리고, 문서 쪽의 계산값을 먼저 읽은 뒤 문서의 시트를 모두 끈 채 shadow 안의 계산값이 같은지 본다. ADR 0026의 "shadow root의 판정은 문서에 전역 CSS가 없는 자리에서 한다"를 지키는 길이고(미리보기가 디자인 토큰 CSS를 전역으로 싣기 때문이다), 시트를 끄고 읽는 방법은 측정 `tokens/measure.mjs`와 같다. play가 끝나면 시트를 다시 켠다.
- **폭 320px.** 알림, 글 입력(두 변형), 카드, 버튼 묶음을 폭 320px의 자리에 그려 가로로 넘치지 않는다(`scrollWidth`가 `clientWidth`를 넘지 않는다). 패키지에는 기준 폭으로 레이아웃이 갈리는 컴포넌트가 없다. 폭마다 도는 스토리와 사진(ADR 0026 첫째 이력)은 기준 폭을 쓰는 앱의 organisms를 짓는 web-widget과 admin-style이 한다.
- **버튼.** 이름으로 찾는다. 기본 `type`이 `button`이다. 크기 둘의 높이가 40·32px이다. 변형 셋의 배경과 글자색이 각 쓰임새 토큰의 계산값이다. `disabled`이면 눌러도 `onClick`이 불리지 않는다. `loading`이면 `aria-busy`이고 눌러도 불리지 않으며 너비가 그대로다. Tab으로 포커스하면 outline이 `solid`이고 색이 `--focus`다.
- **아이콘 버튼.** 접근 이름과 `title`이 `label`이다. 크기 둘이 정사각형 40·32px이다. 불러오는 중에도 이름이 그대로다.
- **아이콘.** `label`이 없으면 `aria-hidden`이고, 있으면 `role="img"`와 이름이다. 크기 넷의 폭이다.
- **상태 배지.** 넷의 글자가 용어집의 말이고, 아이콘이 숨겨져 있다. 색이 쓰임새 토큰이다.
- **진행 표시.** `role="progressbar"`와 `aria-valuenow`·`aria-valuemax`, 값을 모르면 `aria-valuenow`가 없다. 접근 이름이 `label`이다.
- **카드.** `as`의 요소, `elevation` `"0"`은 `box-shadow`가 `none`이고 나머지는 아니다.
- **글 입력.** 라벨로 찾는다(`getByLabelText`). 글을 넣으면 `onChange`가 값을 받는다. `error`이면 `aria-invalid`이고 도움말이 `aria-describedby`로 이어진다. `optional`이면 "선택"이 보인다. `multi`의 높이가 88px 이상이다.
- **스위치.** `role="switch"`, 라벨을 눌러도 바뀌고 `onChange`가 새 값을 받는다. 상태 글이 켜짐·꺼짐이다. `disabled`이면 바뀌지 않는다.
- **알림.** 실패는 `role="alert"`, 경고와 정보는 `role="status"`다. `onClose`가 있으면 이름이 "닫기"인 버튼이 있고 누르면 불린다.
- **모든 스토리**는 axe(`test: "error"`)를 지난다. 다크는 컴포넌트마다 globals `mode: "dark"`인 스토리 하나 이상이다.
- **선례.** `.scratch/design-system/probes/tokens/ui/`(판정 함수, Matrix·Classes·Responsive·Fonts, 버튼의 States 측정), `.scratch/design-system/probes/storybook/ui/`(미리보기와 shadow 틀), 관리 화면의 `apps/admin/components/**/*.test.tsx`(Testing Library의 역할·이름 질의).

### 사진 비교 (새 게이트)

- 스토리 전부 × 먹의 라이트·다크, 상호작용 컴포넌트의 올림·누름·포커스. 같은 이미지의 컨테이너에서 `maxDiffPixels: 0`.
- **선례.** `.scratch/design-system/probes/tokens/visual.mjs`와 `visual.spec.mjs`, `visual_docker/`.

### 바깥 이음매

- 늘리지 않는다. 이 기능은 파이썬과 LLM 호출에 닿지 않는다. `pnpm -C web/apps/admin exec playwright test`(e2e)는 관리 화면이 패키지를 들이지 않으므로 그대로다.

## Out of Scope

- **패턴과 화면.** 승인 묻기, 실행 실패 알림, 빈 목록, 불러오는 중인 목록, 위젯의 대화·승인 묻기 화면, 관리 화면의 실행 목록은 web-widget과 admin-style이 디자인 파일 03·04절을 근거로 짓는다. 두 행에 적었다.
- **관리 화면에 패키지를 들이는 일.** Next의 `postcss.config.mjs`와 전역 CSS, 운영자가 테마를 고르는 화면과 고른 것을 두는 자리, `html`의 `data-theme`, 관리 화면만 쓰는 컴포넌트(표, 링크), 결정 버튼 "허가"를 "승인"으로 바꾸는 일은 admin-style이다. 패키지 CSS를 `@tailwindcss/postcss`로 import하면 글꼴까지 빌드된다는 측정을 그 행에 적었다.
- **위젯에서 테마와 글꼴을 쓰는 일.** 사이트가 위젯에 테마와 모드를 넘기는 길, 페이지 안 번들이 사이트 문서에 고유한 이름으로 글꼴을 등록하는 코드와 `--sans`·`--mono`의 재정의, 글꼴 파일을 위젯 출처에서 `Access-Control-Allow-Origin`과 함께 내는 것, CSP가 글꼴을 막을 때의 안내, 감싼 요소를 실제 커스텀 요소 안에서 재는 것, 페이지 안 번들의 Vite 라이브러리 모드 빌드가 패키지 CSS와 글꼴을 내는 것은 web-widget이다(ADR 0026). 이 명세의 측정은 Storybook(Vite 앱 빌드)과 Next까지다. 글꼴 양(테마 하나에 약 150KB)과 함께 그 행에 적었다.
- **`/design-sync`를 돌리는 것.** 사용자가 시작하는 스킬이고, 코드가 생긴 뒤 화면을 그리기 직전에 돈다(ADR 0026).
- **GitHub 러너에서의 사진 일치.** 로컬에서 잴 수 없어 첫 구현 PR의 CI가 본다.
- **Firefox·WebKit의 스토리 테스트.** 설계 측정이 남긴 것이고 그대로 둔다.
- **헤드리스 라이브러리, 대화상자, 링크, 일반 체크박스, 표 컴포넌트.** 앱에 두거나 필요가 생기면 ADR로 본다(ADR 0026).
- **움직임의 길이와 곡선 단계, 변형 글꼴, woff를 빼는 것, 테마를 사람이 고르는 위젯 부품.** 지금 쓰는 자리가 없다. 움직임은 도는 표시와 값 모름 진행 막대의 둘만 둔다(공통 크기 절). 위젯에서 최종 사용자가 테마를 고르는 것은 ADR 0026이 거부했다.
- **디자인 파일의 OKLCH 생성기를 코드로 옮기는 것.** 위 "디자인 토큰의 값과 원천" 절.

## Further Notes

- **측정은 `.scratch/design-system/probes/tokens/`다.** `design.mjs`(디자인 파일에서 값 뽑기), `setup.mjs`(두 층 CSS와 글꼴과 표본을 사본에 얹기), `measure.mjs`(스토리 테스트, 정적 빌드의 전환 54사례와 상태 색과 움직임, 테마별 글꼴, Next 빌드와 실행), `visual.mjs`(컨테이너 사진과 Linux 빌드). 결과는 `.scratch/design-system/probes/README.md`의 "결과 — tokens"다.
- **Linux 빌드.** 같은 이미지의 컨테이너 안에서 사본 `web/`을 설치하고 정적 빌드를 짓는 데 56.3~56.5초가 걸렸고, 그 빌드를 찍은 14장이 Windows에서 지은 빌드의 정답과 바이트까지 같았다(`toHaveScreenshot` 테스트 10개 통과). 그래서 정답 사진은 어느 쪽에서 지은 정적 빌드로 만들어도 된다.
- **원칙 III.** 판정 함수와 스토리는 `as`·`any`·`!` 없이 쓴다. `instanceof`로 규칙과 요소를 좁히고, globals는 비교로 좁힌다. 표본을 얹은 사본의 `pnpm verify`가 여섯 단계를 지났다(프로브 README의 명령 차례 마지막 줄).
- **디자인 파일의 문구.** v3의 버튼 글자는 "승인"·"거부"이고 탐색 프롬프트의 말(실행, 요청, 출력, 승인, 허가, 거부 등)을 따른다. 그 파일에 "허가"라는 글자는 한 번도 나오지 않는다(파일을 grep했다).
- **열린 문제.** 없다. 사진 비교의 러너 일치는 위 Out of Scope다. 그 밖에 재지 못한 것(Firefox·WebKit, 페이지 안 위젯의 글꼴 등록, Vite 라이브러리 모드)은 프로브 README의 "재지 못한 것"이고 받는 쪽은 위 Out of Scope다.
