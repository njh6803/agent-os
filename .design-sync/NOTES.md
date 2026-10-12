# design-sync notes — @agent-os/ui

`web/packages/ui` 를 Claude Design 프로젝트 "Agent OS 디자인 시스템"(config 의 `projectId`)에 올린다. 첫 동기화는
2026-10-12, Claude Code 2.1.286 의 번들 스킬이다. 패키지와 결정의 배경은 ADR 0025·0026. 첫 프로젝트가 화면을 그릴
계정과 다른 계정에 올라갔다고 사용자가 알려, 같은 날 사용자가 다시 로그인한 계정에 새로 만들고 같은 빌드를 다시 올렸다(소스가
같아 채점은 이어 썼다, 일지 2026-10-12-11).

## 돌리는 법

- 저장소 뿌리(워크트리 뿌리)에서 돈다. `pnpm -C web install --frozen-lockfile` 뒤 `pnpm -C web/packages/ui run build`(cfg.buildCmd).
- 참조 Storybook: `pnpm -C web/packages/ui exec storybook build -c .storybook -o <뿌리 절대 경로>/.design-sync/sb-reference`.
- 변환기: `--node-modules web/packages/ui/node_modules --entry web/packages/ui/dist/index.js`. 패키지 자신의 node_modules 에
  react·react-dom 이 있다.
- 변환기 의존성: `.ds-sync/` 에 `npm i esbuild ts-morph @types/react playwright@1.63.0`. Playwright 를 저장소의 판(1.63.0)에
  맞춰야 이미 깔린 chromium-1243 을 다시 받지 않는다.

## 고친 것

- [GENERAL] 변환기가 공개 export 를 0개로 봤다 → 패키지 `package.json` 에 `types` 가 없고 `exports` 가 `src/index.ts` 를 가리켜
  ts-morph 가 `index.d.ts` 를 찾지 못했다 → 패키지에 `publishConfig.types: ./dist/index.d.ts` 를 더했다. 변환기는
  `publishConfig.types` 를 `types` 보다 먼저 본다(dts.mjs). 저장소에 publishConfig 를 읽는 것은 없고 패키지는 private 이다.
- [GENERAL] 번들이 `lucide-react/dist/esm/icons/<이름>` 을 풀지 못했다 → lucide-react 1.51.0 에 exports 맵이 없고 파일이
  `.mjs` 인데 esbuild 의 기본 확장자 목록에 `.mjs` 가 없다(Vite·Next 는 푼다) → `cfg.tsconfig` 로
  `.design-sync/esbuild-paths.json` 을 주었다. 변환기의 paths 플러그인이 `.mjs` 까지 붙여 찾는다. 패키지의 import 모양
  (ADR 0024)은 그대로다.
- [GENERAL] Card·Icon·StatusBadge 미리보기가 `.map` of undefined 로 깨졌다 → 스토리가 컴포넌트 모듈에서 상수
  (`CARD_ELEVATIONS`, `ICON_NAMES`, `ICON_SIZES`, `STATUS_BADGE_STATUSES`)를 함께 import 하는데, 컴포넌트 모듈의 import 는
  번들 전역으로 돌려지고 패키지 진입점은 그 상수를 내보내지 않는다 → `.design-sync/story-constants.js` 가 dist 에서 다시
  내보내고 `cfg.extraEntries` 가 전역에 합친다. 스토리가 컴포넌트 모듈에서 새 상수를 import 하면 이 파일에 한 줄 더한다.
- [GENERAL] `globals: { mode: "dark" }`·`{ theme: "gongmun" }` 스토리 열넷이 라이트·먹으로 그려졌다 → 원본 compose 가
  ctx.globals 를 비우고, 테마·모드를 거는 것은 프로젝트 데코레이터(`storyPreview` 의 withTheme)인데
  `.storybook/preview.tsx` 가 `...storyPreview(css)` 로 펼쳐 내보내 변환기가 데코레이터를 싣지 않는다(글자 `decorators`
  가 없다). 실어도 그 경로는 initialGlobals 만 넘긴다 → `preview-gen-storybook.mjs` 를 포크(`cfg.libOverrides`)해 스토리의
  globals 를 `data-theme`/`data-mode` 를 단 감싸는 div(바탕 `var(--bg)`, 글자 `var(--text)`, 여백 16px)로 옮긴다. 디자인
  토큰이 `[data-theme]`·`[data-mode]` 요소마다 쓰임새를 다시 선언해 그 안만 그 테마·모드로 그린다.
- 글꼴: 패키지 `build` 의 `dist/theme.css` 에는 `@font-face` 가 없다(글꼴 CSS 는 따로 있다). 변환기가 `_ds_bundle.css` 를
  찾지 못해 참조 Storybook 의 컴파일된 CSS 로 대신하고(`[CSS_FROM_STORYBOOK]`), 거기서 `@font-face` 392개(Noto Sans KR,
  JetBrains Mono, IBM Plex Mono)와 woff2·woff 파일을 `fonts/` 로 옮긴다. 그래서 `[FONT_MISSING]` 이 없다. 패키지 `build`
  를 고치는 PR(plan.md admin-style 행의 조건)은 필요 없었다.
- `디자인 토큰/*` 스토리(진입점, 판정, 판정의 음성 사례)는 컴포넌트가 아니라 `cfg.titleMap` 에서 null 로 뺐다. 변환기는
  제목의 마지막 토막을 공백 없이 본다(`판정의음성사례`).
- [GENERAL] 올린 CSS 에 `--text-title`, `--spacing-8`, `--radius-s` 같은 토큰이 없었다 → Tailwind v4 는 소스가 쓴
  토큰만 CSS 변수로 낸다 → 사용자가 고른 대로 패키지의 `theme.css` 를 `@theme static` 으로 바꿨다(판정 스토리
  `ThemeTokensEmitted` 가 먼저 빨강이었다). 유틸리티 클래스는 여전히 소스가 쓴 것만 있다. 그래서 사용 규약
  (`conventions.md`)이 있는 클래스와 변수를 글자 그대로 나열한다.

## 사용 규약(conventions.md)

- `cfg.readmeHeader` 로 README 앞에 붙는다. 디자인 에이전트가 읽는다. 컴포넌트가 `className`·`style` 을 받지 않아
  에이전트의 배치는 번들 CSS 에 있는 클래스와 `var(--…)` 로만 짓는다는 것이 요지다.
- 다시 동기화할 때 고쳐 쓰지 않고 이름만 다시 검증한다. 클래스 목록은 소스가 클래스를 더하거나 빼면 바뀐다. 검증은
  `node .design-sync/check-conventions.mjs` 이고, 무엇을 어떻게 읽는지는 그 머리 주석이 원천이다. 규약의 문장 모양을
  바꾸면 검사기도 함께 고친다(2026-10-12 변이 넷으로 잡히는 것을 봤다: 없는 클래스, 없다고 적은 클래스, 없는 변수, 없는
  컴포넌트).

## Re-sync risks

- config 의 `projectId` 가 `get_project` 에서 `404` 이고 `list_projects`(쓸 수 있는 것만 보인다)에 없으면, 프로젝트가
  지워졌거나 다른 계정으로 로그인했을 수 있다. 2026-10-12 에는 다른 계정이었다(사용자가 알렸다). 새 프로젝트를 만들기 전에
  사람에게 지금 로그인한 계정이 그리는 계정인지 묻는다. 목록에 프로젝트가 있으면 그 owner 를 함께 보인다
  (`docs/agents/issue-tracker.md` 화면 디자인 절).
- 포크 파일은 채점 계약의 일부다. 주석만 고쳐도 다음 driver 실행이 모든 컴포넌트의 채점을 지우고 기본 상한(스토리 6개)으로만
  다시 캡처한다(2026-10-12 셀프 리뷰 뒤 한 번 겪었다). 포크를 고치면 `compare.mjs --max-stories 12` 로 다시 캡처해 다시 채점한다.
  줄바꿈도 계약의 바이트다. 포크는 작업 트리에서 LF 여야 한다(`git ls-files --eol .design-sync` 의 `w/lf`). 스킬 폴더에서
  `cp` 로 만든 첫 사본이 CRLF 여서 계약이 CRLF 로 찍혔고, 그대로 두면 LF 로 받은 체크아웃의 첫 동기화가 채점을 모두 지운다.
  2026-10-12 PR 직전 리뷰가 짚어 LF 로 맞추고 다시 찍었다. 다시 찍을 때 driver 가 `ds-bundle/` 을 새로 지어 이전 캡처가
  지워지므로, 바이트로 견주려면 driver 전에 `_screenshots/compare/raw/` 를 보관한다.
- 포크 `overrides/preview-gen-storybook.mjs` 는 2.1.286 의 원본에 globals 감싸기만 더했다. 스킬이 올라가면 원본과 다시
  맞춘다(`[OVERRIDE]` 줄이 빌드 로그에 뜬다). 감싸는 div 의 기본 테마 `muk` 은 `themes.ts` 의 `DEFAULT_THEME` 과 같아야
  한다.
- `story-constants.js` 는 스토리가 컴포넌트 모듈에서 함께 import 하는 상수를 손으로 든다. 스토리가 새 상수를 쓰면
  미리보기가 `.map` of undefined 로 깨지고 validate 의 `[RENDER]` 가 잡는다.
- `esbuild-paths.json` 은 lucide-react 의 exports 맵 부재에 기댄다. lucide-react 가 exports 맵을 들이거나 아이콘 파일이
  `.js` 가 되면 지워도 된다.
- 판정 스토리(`judgment`)와 play 로 포커스·입력을 만드는 스토리는 `close` 로 받아 두었다. 정적 모양만 검증됐다.
- `close` 로 받은 Card 의 320px 스토리는 한 글자 차이의 줄바꿈이다. 다음 동기화에서 차이가 커지면 다시 본다.
- 글꼴은 참조 Storybook 의 컴파일된 CSS 에서 온다(`[CSS_FROM_STORYBOOK]`). 변환기는 `build` 가 낸 `dist/theme.css` 를
  쓰지 않는다. 고르는 CSS 는 JS 가 import 한 CSS, `cfg.cssEntry`, `dist/styles.css`·`dist/style.css` 같은 정해진 이름뿐이다
  (`package-build.mjs`). 패키지 JS 가 CSS 를 import 하거나 그 이름의 CSS 가 생기면 변환기가 그것을 고르고 글꼴이 빠질 수
  있다. `[FONT_MISSING]` 을 본다.
- Playwright 는 저장소 판(1.63.0)에 맞췄다. 저장소가 올리면 `.ds-sync` 의 판도 맞춘다.

## 채점

- 스토리 대부분이 `play` 함수(클릭, Tab)를 가진 판정 스토리다. Storybook 은 play 를 돌려 포커스 링을 남기고 미리보기는
  돌리지 않는다. 그 차이만 있는 스토리는 `close` 로 두었다(고칠 수단이 없다. 미리보기에서 포커스를 흉내 내면 카드가
  포커스 상태로 보인다).
- 감싸는 div 때문에 다크·공문 스토리는 미리보기에서 여백 16px 의 칠한 상자로 보이고 Storybook 은 문서 전체를 칠한다.
  틀의 차이라 `match` 로 둔다.
