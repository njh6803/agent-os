---
status: accepted
date: 2026-10-06
---

# 디자인 시스템은 `packages/ui` 하나에 px 디자인 토큰과 두 테마를 두고, Storybook과 컨테이너 안의 사진으로 판정한다

ADR 0025는 디자인 시스템의 원천을 코드로 정하고 세부(패키지의 모양, rem과 px, 다크 모드, 접근성, 한글 글꼴, Storybook, 디자인 문서)를 design-system 기능의 설계 인터뷰로 넘겼다. 이 ADR이 그 세부다. 측정은 모두 `.scratch/design-system/probes/`에 있고, 아래에서 프로브 이름만 적은 것은 그 폴더의 것이다. **디자인 시스템은 `web/packages/ui` 패키지 하나다. 디자인 토큰(Tailwind의 `@theme` CSS)과 atoms·molecules를 들고, organisms 이상은 앱에 남는다. 처음 내는 atoms·molecules는 두 앱의 화면에서 뽑은 최소 집합(버튼, 아이콘 버튼, 글 입력(한 줄·여러 줄), 스위치, 상태 배지, 알림, 진행 표시, 표면, 아이콘)이다. 앱은 `packages/api-client`처럼 소스를 그대로 import하고, 패키지의 `build`(JS, `.d.ts`, 컴파일한 CSS를 `dist/`에 낸다)는 `/design-sync`만 쓰며 커밋하지 않는다. 디자인 토큰의 길이는 px이고, Tailwind의 기본 `@theme` 값을 비운 뒤 우리 디자인 토큰만 정의한다. 색 토큰은 쓰임새 이름뿐이고, 테마(라이트와 다크)가 같은 CSS 변수에 다른 값을 준다. 테마는 루트의 `data-theme`이 고르고, 없으면 시스템 설정을 따른다. 접근성의 목표는 WCAG 2.2 AA다. 글자와 바탕 토큰 짝의 명암비를 테마마다 단위 테스트가 계산하고, 실제 브라우저에서 axe가 돈다. 상호작용 부품은 네이티브 요소로 짓고, 변형은 의존성 없는 타입 맵이다. 한글 웹폰트는 자가 호스팅하고, 페이지 안 위젯은 사이트 문서에 고유한 family 이름으로 등록한다. 미리보기와 실제 브라우저 테스트는 패키지의 Storybook이 맡고, 스토리가 `/design-sync`의 원천이다. 시각 회귀는 정답 사진 한 벌을 판을 고정한 Playwright Linux 이미지 안에서만 찍고 비교한다. 디자인 판단 기준은 `.claude/rules/web-design.md`가 원천이고, `/design-sync`가 같은 파일을 Claude Design에 올린다.**

**패키지.** 앱 사이의 import는 ESLint가 막으므로 두 앱이 나눌 것은 `packages/`로 간다. ADR 0024가 `packages/widget-ui`를 거부한 이유는 소비자가 하나라는 것이었는데, 여기서는 위젯과 관리 화면 둘이다. 층 경계 규칙은 경로의 끝으로 맞추므로 패키지 안의 `components/atoms`에도 그대로 걸린다(`web/eslint.config.mjs`를 읽었다). 디자인 토큰과 컴포넌트를 두 패키지로 나누지 않는 것은 디자인 토큰만 쓰는 소비자가 없어서다. `/design-sync`는 컴파일된 `dist/`를 묶고, 빌드가 없으면 최후 수단으로 `src/`에서 진입점을 합성하며 그때 `.d.ts` 계약이 약해진다. Tailwind는 돌리지 않고 CSS 파일을 그대로 복사한다. 이것은 Claude Code 2.1.286 실행 파일에 압축되어 든 스킬을 풀어 읽은 것이다. 그래서 `build`가 따로 있다. `tsc`와 Tailwind CLI로 2.0초에 `dist/`가 나왔다(`storybook/build.mjs`).

**단위.** 사이트에 `html { font-size: 10px }`가 있으면 rem 기반 페이지 안 위젯이 폭 320px에서 200px로 줄었다(ADR 0024, `.scratch/web-widget/probes/widget_tailwind/`). px로 두면 사이트가 닿지 않고 두 앱의 값이 한 벌이다. 기본 `@theme` 값을 비우고 px 디자인 토큰만 둔 패키지 CSS에서 rem은 0이었다(`storybook/style.mjs`, `storybook/build.mjs`). 대가는 브라우저의 기본 글자 크기 설정을 따르지 않는 것이다. 확대(zoom)는 따른다. 기본값을 비우면 `text-base`, `rounded`, `font-bold` 같은 익숙한 클래스가 오류 없이 아무 CSS도 만들지 않는다. Tailwind 기본값의 유틸리티 이름 51개 중 24개가 그랬다(`storybook/build.mjs`). 에이전트가 학습한 기본 클래스를 쓰는 실수가 조용히 지나가므로, 컴포넌트에 쓴 클래스가 모두 CSS를 만드는지 테스트가 판정한다. 방법은 첫 티켓이 잰다.

**색과 테마.** 다크를 지금 두므로 컴포넌트가 테마를 모르게 한다. 색 토큰은 쓰임새 이름(바탕, 글자, 강조, 위험 등)뿐이고 팔레트를 비우므로, 컴포넌트에는 `dark:` 클래스가 없다. 명암비 테스트가 볼 짝도 디자인 토큰 쪽 한자리에 모인다. `data-theme`은 문서에서는 `html`에, 페이지 안 위젯에서는 호스트에 둔다. 값을 바꾸면 색 토큰의 CSS 변수와 색이 바뀌었고, 속성이 없을 때는 `prefers-color-scheme`을 따랐다. 문서와 shadow 호스트 둘 다 그랬다(`storybook/style.mjs`). 관리 화면은 속성을 두지 않아 시스템을 따른다. 위젯은 사이트가 어두운데 운영체제가 밝을 수 있어서 사이트가 값을 넘기는 길이 필요하다. 그 길은 web-widget이 정한다.

**접근성.** axe는 `@storybook/addon-a11y`(axe-core 4.13.0)로 스토리 테스트 안에서 돈다. 대비가 2.56:1인 스토리를 `test: "error"`에서 `color-contrast` 위반으로 실패시켰다(`storybook/cases.mjs`). 명암비 단위 테스트는 의존성 없는 계산이고, 테마마다 같은 짝 목록을 본다.

**글꼴.** Chromium 153과 Firefox 146은 shadow root 안의 `@font-face`를 쓰지 않았다. WebKit 26(윈도우용 Playwright 빌드)은 쓰기는 했지만 그 글꼴이 사이트 문서로 샜다. 문서에 선언하면 세 브라우저 모두 shadow 안의 글자에 적용됐다. 사이트가 쓰는 이름과 같은 family로 선언하면 사이트 글자가 바뀌었고, 고유한 이름으로 선언하면 사이트 글자는 그대로였으며 `document.fonts`의 항목 하나만 남았다. 다른 출처의 글꼴은 `Access-Control-Allow-Origin`이 없으면 Chromium과 Firefox가 막았다(`font_shadow/measure.mjs`). 그래서 패키지가 글꼴 파일과 `@font-face`를 든다. 관리 화면과 iframe은 자기 문서에 선언하고, 페이지 안 위젯은 사이트 문서에 고유한 이름으로 FontFace API를 써서 한 번 등록한다. API로 등록하면 사이트의 스타일시트 수가 늘지 않았다. 글꼴 스택의 뒤에 시스템 글꼴을 두어, 사이트의 CSP가 글꼴을 막아도 시스템 글꼴로 그린다. CSP로 막히는 경우는 재지 않았다. 글꼴은 OFL이고 저자가 낸 동적 서브셋을 쓴다. 예를 들어 Pretendard 1.3.9는 예약 글꼴 이름이 붙어 있어, 직접 서브셋하면 그 이름을 쓸 수 없다. 이것은 라이선스 문서를 읽은 해석이며 법적 판단은 아니다. Pretendard의 동적 서브셋은 굵기 하나에 92조각이고, 한글 문장 하나를 그릴 때 세 조각 약 40KB를 받았다. 전체 파일은 766KB다(`font_shadow/sizes.mjs`, `font_shadow/measure.mjs`). 어떤 글꼴을 쓸지는 Claude Design 탐색이 고른다.

**상속.** 사이트의 `* { font-family }`나 호스트 태그 선택자는 보통의 `:host` 선언을 이겼지만, shadow 안의 감싼 요소에 둔 선언에는 닿지 않았다(`font_shadow/measure.mjs`). 잰 것은 `font-family`이고, ADR 0024가 든 `letter-spacing` 같은 다른 상속 속성도 같다고 본다(어림). 그래서 상속 속성의 재정의는 `:host`가 아니라 shadow 안의 감싼 요소에서 하고, 그 CSS는 shadow root용 보정(ADR 0024의 `@layer properties` 재선언)과 함께 패키지가 든다.

**부품과 변형.** 네이티브 요소(`<button>`, `<dialog>`, `role="switch"`인 체크박스)는 shadow root 밖으로 그리는 포털이 없다. 헤드리스 라이브러리는 네이티브 요소로 지을 수 없는 부품이 생길 때 ADR로 들인다. 변형은 `satisfies Record<변형, string>` 객체로 클래스를 고르고, 소비자가 클래스를 덧붙여 스타일을 덮는 길은 두지 않는다.

**Storybook.** `/design-sync`는 `.storybook/main.*`가 있으면 storybook 모양으로 돈다. 스토리를 컴파일하고, Storybook이 그린 참조 화면과 스크린샷을 비교해 충실도를 판정한다. 없으면 에이전트가 `.design-sync/previews/`에 미리보기를 따로 쓴다(같은 실행 파일을 읽었다). 그래서 스토리 한 벌이 갤러리, 실제 브라우저 테스트, Claude Design의 원천을 함께 맡는다. Storybook 10.6.1(`@storybook/react-vite`, `@storybook/addon-vitest`, `@storybook/addon-a11y`)과 Vitest 5.0.2의 브라우저 모드를 `web/` 사본에 설치하자, 판정자의 범위에서 아무것도 빼지 않고 우회도 없이 `pnpm -C web verify`의 여섯 단계를 지났다(`storybook/verify.mjs`, `storybook/cases.mjs`). 스토리 테스트만 돌리면 이 기계에서 11~13초였다. `storybook build`는 `index.json`(v5, `entries`)을 냈다(`storybook/style.mjs`). `/design-sync`의 storybook 모양이 이 파일을 읽는다는 것은 실행 파일을 읽은 것이고, 이 `index.json`과 `dist/`를 실제로 읽는지는 재지 못했다. 설치와 판정의 조건은 셋이다.

- pnpm 11은 esbuild와 @parcel/watcher의 빌드 스크립트에서 설치를 멈춘다. 이것은 `allowBuilds` 없이 돈 첫 `setup.mjs`에서 손으로 봤고, 지금의 프로브는 이 실패를 다시 내지 않는다. 그래서 `pnpm-workspace.yaml`의 `allowBuilds`로 둘의 스크립트를 끈다. 스크립트를 꺼도 두 바이너리는 동작했다.
- `.storybook/`은 점으로 시작해 `**/*`에 맞지 않으므로 tsconfig의 include에 따로 적는다. 빼면 ESLint가 파싱 오류를 낸다.
- `dist/`와 `storybook-static/`은 뿌리 `.gitignore`에 앵커를 붙인 줄로 적어야 판정 범위에서 빠진다. 패키지 안의 `.gitignore`나 앵커 없는 `dist/`는 판정자나 판정 범위 테스트에 걸렸다(`storybook/build.mjs`).

락에 새로 드는 패키지는 Storybook 쪽 182개(네이티브 65개), UI 쪽 35개, CSS 빌드 18개다. 기존 패키지의 판은 바뀌지 않았다(`storybook/deps.mjs`).

스토리 테스트는 뿌리 vitest 설정의 프로젝트로 두어 `pnpm -C web verify`의 test 단계에서 돈다. 그래서 pre-commit도 돌리고, CI의 web 잡은 chromium을 설치한다. 검증 명령의 수는 그대로다. shadow root의 판정은 문서에 전역 CSS가 없는 자리에서 한다. 문서에 전역 CSS가 실리면 보정 CSS를 빼도 shadow 안이 같아 보였다(`storybook/style.mjs`).

**시각 회귀.** 같은 표본을 Windows와 Linux 컨테이너에서 찍자, 도형만 있는 상자는 바이트까지 같았고 글자가 든 사진은 페이지 픽셀의 약 8.4%가 달랐다. 같은 글꼴 파일인데 글자열 폭이 Linux에서는 정수, Windows에서는 소수였다. 같은 이미지(`mcr.microsoft.com/playwright:v1.63.0-noble`)로 컨테이너를 따로 두 번 띄워 찍은 사진 16장은 바이트까지 같았다(`visual_docker/run.mjs`). 그래서 정답 사진은 한 벌이고, 그 이미지 안에서만 찍고 비교한다. 이미지의 판은 Playwright의 판과 함께 올린다. 사진 비교는 별도 명령이다. CI에서는 그 이미지를 컨테이너로 쓰는 잡이 돌고, 필수 검사 `verify`가 `needs`로 모은다. pre-commit에는 넣지 않고, 로컬에서는 `packages/ui`를 건드렸을 때 Docker로 친다. e2e와 같은 자리다. 이미지는 받는 양이 약 956MB, 디스크가 2.5GB였고 한 번 실행에 14~32초가 걸렸다. GitHub Actions 러너에서 같은 사진이 나오는지는 재지 못했고, 구현 PR의 첫 CI가 본다. 값을 직접 확인하는 브라우저 테스트(계산 스타일, 역할, axe)는 그대로 둔다.

**디자인 문서.** 디자인 판단 기준은 `.claude/rules/web-design.md`(paths: `web/packages/ui/**`, `web/apps/*/components/**`)에 둔다. 그 경로의 파일을 Read하면 실리고, `/design-sync`의 `guidelinesGlob`이 같은 파일을 Claude Design의 guidelines로 올린다. 그래서 사본이 없다. `/design-sync`에 관한 이 절의 사실은 모두 같은 실행 파일을 읽은 것이다. `guidelinesGlob`은 패키지 밖이라도 저장소 안의 `.md`를 받고, 패키지 루트의 README.md나 DESIGN.md는 기본값으로 올리지 않는다. 앱별 기준은 필요할 때 `web-design-widget.md`와 `web-design-admin.md`로 더한다. 컴포넌트별 쓰임은 스토리 옆의 `<Name>.md`에 적고, `/design-sync`가 그 컴포넌트의 설명으로 올린다. 디자인 토큰의 값은 코드에만 둔다.

**동기화.** Claude Design에서 화면을 그리기 직전에 `/design-sync`를 돈다. 맞추지 않은 디자인 시스템이 해를 끼치는 것은 그 순간이기 때문이다. `/design-sync`의 상태(`.design-sync/`의 config, NOTES, conventions, overrides)는 스킬의 규약대로 저장소 루트에 커밋하고, 산출물(`ds-bundle/`, `.ds-sync/`, 캐시)은 무시한다.

## Considered Options

- **디자인 토큰만 패키지로 두고 컴포넌트는 앱마다 짓는다.** 같은 컴포넌트가 두 벌이 되고 Claude Design에 올릴 원천도 둘이 된다. 거부했다. **tokens와 ui 두 패키지**는 디자인 토큰만 쓰는 소비자가 없어 거부했다.
- **rem을 원천으로 두고 페이지 안 번들만 `:host`에서 px로 덮는다.** 관리 화면과 iframe이 브라우저의 글자 크기 설정을 따른다. 그러나 값이 두 벌이고, 덮는 목록이 Tailwind의 `@theme` 값과 어긋나지 않는지 보는 검사가 하나 더 든다. 거부했다. **rem을 그대로 두고 임베드 안내에 적는 안**도 거부했다.
- **쓰임새 토큰을 두고 다크는 나중에 값만 더한다.** 인터뷰가 추천한 안이었지만, 사용자가 라이트와 다크를 지금 둘 다 골랐다.
- **쓰임새 이름을 테마마다 따로 두고 컴포넌트가 `dark:`로 고른다, 또는 팔레트를 남긴다.** 컴포넌트마다 색을 두 벌 적고, 명암비 테스트가 볼 짝이 흩어진다. 거부했다.
- **시스템 설정만 따른다.** 사이트가 어둡고 운영체제가 밝으면 위젯이 밝게 뜬다. 거부했다. 관리 화면의 테마 토글은 들이지 않았다.
- **명암비 테스트만 두거나, eslint-plugin-jsx-a11y를 더한다.** 앞의 것은 역할과 포커스의 위반을 리뷰에 맡긴다. 뒤의 것은 `web/eslint.config.mjs`의 "새 플러그인을 들이지 않는다"를 바꾼다. 거부했다.
- **cva, tailwind-merge, clsx.** 소비자 클래스로 충돌을 덮을 수 있다. 그러나 의존성이 늘고, 덮어야 할 자리가 아직 없다. 거부했다.
- **Radix나 React Aria.** 키보드와 포커스 동작을 라이브러리가 맡는다. 그러나 포털이 기본값으로 `document.body`에 그려 shadow root 밖으로 나간다. 이것은 문서에서 얻은 지식이며 재지 않았다. 거부했다.
- **페이지 안 번들만, 또는 두 앱 모두 시스템 글꼴.** 같은 위젯이 임베드 방식에 따라 다르게 보이거나, 운영체제마다 글꼴이 다르다. 거부했다. **shadow root 안의 `@font-face`**는 Chromium과 Firefox가 쓰지 않아(`font_shadow/measure.mjs`) 거부했다. **상속 속성을 `:host`에 `!important`로 다시 정하는 안**은 측정에서 사이트의 보통 선언과 `!important` 선언을 모두 이겼다(같은 프로브). 그러나 사이트가 호스트 요소에 두는 선언과 계속 겨루게 되고, 감싼 요소는 사이트의 선택자가 닿지 않아 겨룰 일이 없다. 거부했다.
- **DESIGN.md 파일과 그것을 가리키는 rules.** 자동으로 실리는 것이 포인터뿐이다. **`docs/design/` 아래 문서**는 실리지 않는다. 둘 다 거부했다.
- **Vitest 브라우저 모드만 두거나 갤러리 페이지를 직접 만든다.** `/design-sync`가 package 모양으로 돌아, 테스트의 예시와 미리보기가 두 벌이 되거나 갤러리를 손으로 유지한다. 거부했다.
- **앱도 `dist`를 쓴다.** 앱의 타입 검사와 테스트 전에 패키지를 빌드해야 해서 `verify`에 빌드 순서가 든다. **빌드 없이 `src` 합성에 맡기는 안**은 스킬이 최후 수단으로 적은 길이다. 둘 다 거부했다.
- **시각 회귀를 두지 않는다.** 디자인 토큰 하나가 여러 컴포넌트의 모양을 한꺼번에 바꾸는 변화를 값 단언만으로는 다 덮지 못한다. **운영체제마다 정답 사진을 둔다**는 모양을 바꿀 때마다 두 벌을 갱신한다. **허용 오차를 넓혀 한 벌로 쓴다**는 글자 차이를 덮을 만큼 넓히면 작은 진짜 변화도 통과할 것으로 본다(어림). 셋 다 거부했다.
- **스토리 테스트를 별도 명령으로 둔다.** 게이트가 늘고 pre-commit이 보지 못한다. 거부했다. **사진 비교를 e2e 잡이나 `verify` 안에 둔다**는 e2e 잡을 컨테이너로 옮기거나, 모든 커밋이 Docker를 요구한다. 거부했다.
- **`packages/ui`를 바꾼 PR마다 동기화하거나 훅이 경고한다.** PR마다 사용자가 스킬을 시작해야 하거나, 마지막 동기화를 저장소가 알 길이 따로 든다. 거부했다.

## Consequences

- **ADR 0021·0024·0025의 문장 다섯이 바뀌거나 정해진다.** 각 문장 뒤에 이 ADR을 가리키는 포인터를 달았다.
  - ADR 0024 "Shadow DOM의 격리" 절의 "위젯은 `:host`에서 상속 속성을 다시 정한다"는 shadow 안의 감싼 요소에서 다시 정하는 것으로 바뀐다.
  - ADR 0024 "스타일" 절의 "단위는 design-system이 정한다"는 px로 정해졌다.
  - ADR 0025 Consequences의 "세부는 design-system 기능의 인터뷰가 정한다"는 이 ADR로 정해졌다.
  - ADR 0025 Consequences의 "코드가 바뀌면 `/design-sync`로 다시 맞춘다"는 화면을 그리기 직전에 맞추는 것으로 좁아졌다.
  - ADR 0021 Consequences의 "스토리 규칙은 Storybook을 들이는 날 다시 보고"는 스토리를 컴포넌트와 같은 폴더에 두는 것으로 정해졌다.
- **web-widget에 넘기는 것.** 사이트가 위젯에 테마를 넘기는 길, 글꼴 파일을 위젯 출처에서 `Access-Control-Allow-Origin`과 함께 내는 것(nginx와 Next), 페이지 안 번들이 사이트 문서에 글꼴을 등록하는 코드, 그리고 사이트의 CSP가 글꼴을 막을 때 시스템 글꼴로 내려간다는 것을 임베드 안내에 적는 일이다.
- **admin-style.** 관리 화면은 `data-theme`을 두지 않고 시스템을 따른다. 패키지를 들이는 일과 관리 화면만 쓰는 컴포넌트는 그 기능이 한다.
- **게이트가 열둘이 된다.** 사진 비교는 e2e에 이어 CI에서만 도는 둘째 게이트다. `CLAUDE.md`의 검증 명령 절, `docs/constitution/operations.md`, `tech.md` 원격·CI 행과 `ci.yml` 머리 주석의 잡 수, `ci.yml`의 새 잡과 `verify`의 `needs`, CI web 잡의 chromium 설치는 그 게이트를 들이는 티켓이 함께 고친다. 보호 설정(`tools/protection.json`)은 바뀌지 않는다.
- **`pnpm-workspace.yaml`에 `allowBuilds`가 든다.** esbuild와 @parcel/watcher의 설치 스크립트를 끈다. 공급망 유예(`minimumReleaseAge`)는 건드리지 않는다.
- **`tech.md`의 웹 행과 프론트 구성 행**을 이 결정에 맞춘다. 스토리를 컴포넌트와 같은 폴더에 두는 것은 09-20 씨앗의 스토리 규칙이다.
- **`.scratch/<slug>/design/`의 규약을 `docs/agents/issue-tracker.md`에 더한다(ADR 0025).** 화면을 그리기 직전에 `/design-sync`를 돌고, 그 폴더의 `README.md`에 화면마다 내보낸 파일, 근거 문서의 전체 경로, 기준 커밋, 동기화한 커밋을 적는다.
- **design-system의 순서.** 이 인터뷰 다음은 Claude Design 탐색(색과 글꼴 짝, 라이트와 다크, 대략의 화면)이다. 사용자가 진행하고, 고른 방향은 `.scratch/design-system/design/`에 내보낸다. 그다음이 명세, 티켓, 코드다. 디자인 토큰의 값은 탐색이 정한다.
- **첫 티켓이 잴 것.** 디자인 토큰에 없는 클래스를 잡는 방법, 관리 화면(Next)과 Vite가 패키지의 글꼴 `url()`을 내는 방법, 사진 비교의 도구(Vitest 브라우저 모드의 스크린샷이나 Playwright), GitHub 러너에서의 사진 일치다.
- **용어.** `CONTEXT.md`에 디자인 시스템, 디자인 토큰, 테마를 세웠다. 단독 "토큰"은 채널 토큰이나 서명 토큰과 섞이므로 디자인 쪽 문서와 코드 이름은 "디자인 토큰"을 쓴다.
