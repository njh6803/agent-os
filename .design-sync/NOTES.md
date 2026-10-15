# design-sync notes — @agent-os/ui

`web/packages/ui` 를 Claude Design 프로젝트 "Agent OS 디자인 시스템"(config 의 `projectId`)에 올린다. 첫 동기화는
2026-10-12, Claude Code 2.1.286 의 번들 스킬이다. 패키지와 결정의 배경은 ADR 0025·0026. 첫 프로젝트가 화면을 그릴
계정과 다른 계정에 올라갔다고 사용자가 알려, 같은 날 사용자가 다시 로그인한 계정에 새로 만들고 같은 빌드를 다시 올렸다(소스가
같아 채점은 이어 썼다, 일지 2026-10-12-11). 2026-10-14 에 design-refresh 의 디자인 시스템을 Claude Code 2.1.295 의 번들
스킬로 다시 올렸다(일지 2026-10-15-01).

## 돌리는 법

- 저장소 뿌리(워크트리 뿌리)에서 돈다. `pnpm -C web install --frozen-lockfile` 뒤 `pnpm -C web/packages/ui run build`(cfg.buildCmd).
- 참조 Storybook: `pnpm -C web/packages/ui exec storybook build -c .storybook -o <뿌리 절대 경로>/.design-sync/sb-reference`.
- 변환기: `--node-modules web/packages/ui/node_modules --entry web/packages/ui/dist/index.js`. 패키지 자신의 node_modules 에
  react·react-dom 이 있다.
- 변환기 의존성: `.ds-sync/` 에 `npm i esbuild ts-morph @types/react playwright@1.63.0`. Playwright 를 저장소의 판(1.63.0)에
  맞춰야 이미 깔린 chromium-1243 을 다시 받지 않는다.
- 목록 타일: driver 뒤에 `.design-sync/thumbnail.html` 을 `ds-bundle/` 에 복사한다(빌드가 `ds-bundle/` 을 지우고 새로 짓는다,
  `package-build.mjs`). `DesignSync` 의 `finalize_plan` writes 에 `thumbnail.html` 과 `_ds_needs_recompile` 을 넣고, 둘을
  올린 뒤 프로젝트를 한 번 연다. 변환기의 삭제 목록은 `components/` 경로만 내므로(`lib/remote-diff.mjs` 를 읽었다) 다시
  동기화해도 지워지지 않는다. 새 프로젝트에 올릴 때와 이 파일을 고쳤을 때만 올린다. 고쳐 올릴 때는 서버가 만든 이미지
  `.thumbnail` 도 `finalize_plan` 의 `deletes` 에 넣어 지운다. 두지 않으면 타일이 옛 그림 그대로다(아래 Re-sync risks).
  스킬은 재동기화의 삭제 목록을 `upload.deletePaths` 에서 그대로 옮기라고 하지만, `.thumbnail` 은 변환기가 짓지 않고 서버가
  만든 파일이라 그 diff 에 보이지 않는다. 그래서 이 하나는 손으로 넣는다(2026-10-14 사용자가 골랐다).
- 기초 카드: driver 뒤에 `.design-sync/foundations/` 를 통째로 `ds-bundle/foundations/` 에 복사하고(목록 타일과 같은 이유),
  `finalize_plan` writes 에 `foundations/**/*.html` 을 넣는다. 카드를 고쳤을 때와 새 프로젝트에 올릴 때 올린다.
- 사용 규약 검사: 복사까지 마친 뒤 `node .design-sync/check-conventions.mjs`. 규약의 이름, 빼는 목록, 기초 카드와 목록
  타일의 변수와 복사를 함께 본다(아래 절들).

## 카드에 올리는 스토리

- 컴포넌트 카드에는 보여 주기용 스토리(태그 `showcase`)만 오른다. 컴포넌트를 실제 자리(승인 묻기, 실행 목록, 플러그인
  줄 등)에 놓아 보이는 스토리이고, 이름은 `쓰임: …` 이다. 변형과 상태를 늘어놓는 변형 스토리(판정 스토리 `judgment`
  포함)는 스토리 테스트와 사진을 맡고 카드에서 빠진다. 보여 주기용 스토리도 스토리 테스트(afterEach, axe)와 사진을 지난다.
- 빼는 법은 `cfg.overrides.<Name>.skip` 의 스토리 id 다. 변환기가 그 목록을 미리보기 격자와 스토리 조각에서 뺀다
  (2.1.286 의 `lib/emit.mjs` 의 `visibleStoryIds` 와 `lib/preview-gen-storybook.mjs` 를 읽었고, 2026-10-13 그 판의 변환기를
  로컬에서 돌려 생성된 미리보기 `.design-sync/.cache/previews/*.tsx` 의 내보내기가 보여 주기용 11개뿐인 것을 손으로
  봤다). 채점도 그 목록을 따른다. 2026-10-14 재동기화의 드라이버 로그(`[COMPARE]` 줄의 grade keys)와 시트에 아홉
  컴포넌트의 보여 주기용 11개만 있었다.
  `cfg.titleMap` 의 null 은 판정 스토리 파일(진입점, 판정,
  판정의 음성 사례)을 통째로 빼고, 컴포넌트 스토리 파일 안의 `judgment` 스토리는 빼는 목록이 뺀다.
- 규칙: 컴포넌트 스토리를 더하거나 이름을 바꾸면 빼는 목록도 고친다. 보여 주기용 태그가 없는 컴포넌트 스토리는 모두 빼는
  목록에 있고, 목록의 id 는 모두 지금 있는 변형 스토리이며, 컴포넌트마다 보여 주기용 스토리가 하나 이상이다. 검사기가
  참조 Storybook 의 `index.json`(`cfg.storybookStatic`)으로 이 셋을 본다. CI 에는 두지 않는다(design-refresh 명세의
  이음매 절, 새 이음매를 더하지 않는다). 그래서 어긋남은 동기화 때 잡힌다. 검사기의 판정이 빨개지는 것은
  `.scratch/design-refresh/probes/checker_mutations.toml`(`tools/mutate.py` 의 표)과, 파일을 만들거나 지우는 변이
  둘은 같은 자리의 `checker_mutations.mjs` 가 잰다.

## 기초 카드

- 넷이고 폴더마다 HTML 하나다: `foundations/colors`(Colors. 쓰임새 토큰의 녹청 라이트·다크, 테마 넷, 녹청의 원색),
  `foundations/type`(Type. 글자 단계, 굵기, 글꼴 둘), `foundations/spacing`(Spacing. 간격, 모서리, 틀),
  `foundations/density`(Density. 밀도 두 벌). 첫 줄이 `<!-- @dsCard group="…" -->` 다. 변환기의 자체 검사가 폴더마다 첫
  `@dsCard` HTML 하나를 고르기 때문에 카드마다 폴더를 따로 둔다(`lib/emit.mjs` 의 주석). 2026-10-14 재동기화의 첫
  업로드 뒤 디자인 시스템 창이 넷을 그룹 `Colors`·`Density`·`Spacing`·`Type` 아래에 모았고, 카드 이름은 파일 이름을 따라
  모두 `index` 로 보였다(컴포넌트 카드는 `Button.html` 이라 "Button" 이다). 아직 열린 문제다. 파일 이름을 바꾸면 고쳐질
  것으로 보지만 재지 않았다. 검사기는 폴더마다 HTML 이 하나인지만 보고 이름을 가리지 않는다. 파일 이름 `index.html` 을 든
  자리는 티켓 05 의 "정한 것" 3 과 프로브 `.scratch/design-refresh/probes/checker_mutations.mjs` 이니 함께 고친다.
- 값은 글자로 적지 않는다(ADR 0026 "디자인 토큰의 값은 코드에만"). 색과 길이는 `var(--이름)` 으로 칠하고, 칸에 보이는
  값은 카드 끝의 작은 스크립트가 그 요소의 계산값을 읽어 채운다(`data-value="--이름"`). 밀도를 따르는 글자와 높이는
  별칭(`--text-body`)이 아니라 원천인 밀도 변수(`--body-size`)로 읽는다. 별칭은 `@theme inline` 이라 CSS 변수로 나오지
  않는다. 검사기가 카드와 목록 타일의 변수를 빌드 CSS 의 선언과 맞댄다.
- 카드는 손으로 고치는 정적 HTML 이다. 처음 판은 세션 스크래치의 생성 스크립트로 한 번 써 냈고 그 스크립트는 커밋하지
  않았다. 그래서 카드 넷이 머리의 `<style>`(바탕, 제목, 값 글자)과 끝의 값 채우기 스크립트를 똑같이 들고, 고치면 넷을 함께
  고친다. 고친 뒤 `ds-bundle/` 에 복사해 내장 브라우저로 보고 검사기를 돌린다.
- 테마를 단 줄과 칸은 `data-mode` 도 함께 단다. 빼면 그 줄은 시스템 설정을 따라, 다크 설정의 브라우저에서 다크로
  그려진다(2026-10-13 내장 브라우저에서 색 카드의 테마 줄이 그랬다).

## 고친 것

- [GENERAL] 변환기가 공개 export 를 0개로 봤다 → 패키지 `package.json` 에 `types` 가 없고 `exports` 가 `src/index.ts` 를 가리켜
  ts-morph 가 `index.d.ts` 를 찾지 못했다 → 패키지에 `publishConfig.types: ./dist/index.d.ts` 를 더했다. 변환기는
  `publishConfig.types` 를 `types` 보다 먼저 본다(dts.mjs). 저장소에 publishConfig 를 읽는 것은 없고 패키지는 private 이다.
- [GENERAL] 번들이 `lucide-react/dist/esm/icons/<이름>` 을 풀지 못했다 → lucide-react 1.51.0 에 exports 맵이 없고 파일이
  `.mjs` 인데 esbuild 의 기본 확장자 목록에 `.mjs` 가 없다(Vite·Next 는 푼다) → `cfg.tsconfig` 로
  `.design-sync/esbuild-paths.json` 을 주었다. 변환기의 paths 플러그인이 `.mjs` 까지 붙여 찾는다. 패키지의 import 모양
  (ADR 0024)은 그대로다.
- [GENERAL] Card·Icon·StatusBadge 미리보기가 `.map` of undefined 로 깨졌다 → 스토리가 컴포넌트 모듈에서 상수
  (지금은 `ICON_NAMES`, `ICON_SIZES`, `STATUS_BADGE_STATUSES`)를 함께 import 하는데, 컴포넌트 모듈의 import 는
  번들 전역으로 돌려지고 패키지 진입점은 그 상수를 내보내지 않는다 → `.design-sync/story-constants.js` 가 dist 에서 다시
  내보내고 `cfg.extraEntries` 가 전역에 합친다. 스토리가 컴포넌트 모듈에서 새 상수를 import 하면 이 파일에 한 줄 더한다.
- [GENERAL] `globals` 로 다크나 기본이 아닌 테마를 고른 스토리(첫 동기화 때 열넷)가 라이트·기본 테마로 그려졌다 → 원본
  compose 가 ctx.globals 를 비우고, 테마·모드를 거는 것은 프로젝트 데코레이터(`storyPreview` 의 withTheme)인데
  `.storybook/preview.tsx` 가 `...storyPreview(css)` 로 펼쳐 내보내 변환기가 데코레이터를 싣지 않는다(글자 `decorators`
  가 없다). 실어도 그 경로는 initialGlobals 만 넘긴다 → `preview-gen-storybook.mjs` 를 포크(`cfg.libOverrides`)해 스토리의
  globals 를 `data-theme`/`data-mode`/`data-density` 를 단 감싸는 div(바탕 `var(--bg)`, 글자 `var(--text)`, 여백 16px)로
  옮긴다. 디자인 토큰이 `[data-theme]`·`[data-mode]` 요소마다 쓰임새를, `[data-density]` 요소마다 밀도 변수를 다시 선언해
  그 안만 그렇게 그린다. 밀도는 2026-10-13(design-refresh 티켓 05)에 더했다.
- [GENERAL] 다크 설정의 브라우저에서 컴포넌트 카드의 본문 글자가 흰 바탕 위에서 거의 보이지 않았다 → 카드의 스토리가
  globals 를 정하지 않아 감싸는 요소가 없었고, `data-mode` 가 없으면 쓰임새 토큰이 보는 사람의 시스템 설정(다크)을 따라
  글자색이 밝아지는데 카드 바탕은 앱이 칠한 흰색이다 → 포크가 globals 없는 스토리도 `data-theme="nokcheong"`·
  `data-mode="light"` 로 감싸고 글자색을 그 안에서 `var(--text)` 로 다시 푼다(여백과 바탕은 더하지 않는다). 2026-10-14
  재동기화의 첫 업로드 뒤 내장 브라우저에서 그 탭의 색 설정을 다크와 라이트로 에뮬레이트하며 손으로 봤다. compare 의 chromium 은 라이트라 두 쪽이 같아 보여
  잡지 못한다. 기초 카드와 목록 타일이 `data-mode` 를 다는 것과 같은 까닭이다.
- 글꼴: 패키지 `build` 의 `dist/theme.css` 에는 `@font-face` 가 없다(글꼴 CSS 는 따로 있다). 변환기가 `_ds_bundle.css` 를
  찾지 못해 참조 Storybook 의 컴파일된 CSS 로 대신하고(`[CSS_FROM_STORYBOOK]`), 거기서 `@font-face`(2026-10-13 로컬
  빌드에서 386개, Noto Sans KR 과 Noto Sans Mono)와 woff2·woff 파일을 `fonts/` 로 옮긴다. 그래서 `[FONT_MISSING]` 이 없다. 패키지 `build`
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
  컴포넌트. 2026-10-13 에 더한 빼는 목록·기초 카드·밀도 키의 판정은 `checker_mutations.toml` 과 `.mjs` 가 잰다).
- 2026-10-13 에 새 결정(테마 넷과 녹청 기본, 밀도와 그 변수, 새 클래스와 변수)으로 고쳐 썼다. 밀도를 따르는 클래스
  (`text-body`, `h-control` 등)는 `@theme inline` 의 별칭이라 클래스는 있어도 CSS 변수로는 나오지 않는다. 그래서 인라인
  `style` 의 변수 목록에는 원천인 밀도 변수 일곱을 든다.

## Re-sync risks

- 목록 타일은 프로젝트 뿌리의 `thumbnail.html` 에서 나오는 것으로 보인다. 앱의 기본 디자인 시스템 다섯은 앱이 가진
  `thumbnail.html` 을 작은 창으로 그린다(Modernist 의 것을 읽었다). 이 프로젝트는 같은 짜임의 파일과 마커를 올리고 다시 연 뒤
  서버의 썸네일 이미지가 생겼고, 그 그림이 이 파일과 같았다. 올리기 전에 연 때는 없었다. 한 번 본 것이다(2026-10-12 내장
  브라우저에서 손으로 봤다, 일지 2026-10-12-11). 2026-10-14 에 녹청으로 다시 그린 파일을 올리고 프로젝트를 연 뒤에도
  이미지는 옛 그림(띠 넷)이었다. 이미지의 URL 시각은 연 순간으로 바뀌었지만 그림은 같았다. 원격 `.thumbnail` 을 지우고 다시
  연 뒤에야 새 그림(녹청, 띠 셋)이 생겼다. 서버가 `.thumbnail` 이 없을 때만 `thumbnail.html` 을 그리는 것으로 보인다(그날 내장
  브라우저에서 이미지 URL 을 열어 손으로 봤다). `<html>` 과 띠의 테마 키는 글자로 들었다(검사기가 선택자와 맞댄다). 기본
  테마나 테마 목록이 바뀌면 고쳐 다시 올리고 `.thumbnail` 을 지운다.
- 빼는 목록을 채점도 따르는 것은 2026-10-14 에 봤다(위 "카드에 올리는 스토리"). 컴포넌트 폴더 밖의 `@dsCard`
  카드(`foundations/`)도 그날 처음 올렸고 디자인 시스템 창이 모았다(위 "기초 카드"). 변환기는 스킬 판마다 다시
  비교한다. 2026-10-14 에 덮어쓰기 전의 2.1.286 사본(무시된 `.ds-sync/`)을 세션 스크래치에 보관하고 2.1.295 스킬 폴더와
  `diff -rq` 로 견줬다(`node_modules`·`package*.json` 제외). `lib/` 는 다른 파일이 없었고, 다른 것은 셋이었다. 캡처 서버
  `storybook/http-serve.mjs` 가 HTML·JS 에 `charset=utf-8` 을 붙인 것, 새 `package-capture.mjs`, `non-storybook/SKILL.md`
  다. 그 사본은 커밋하지 않아 다시 볼 수 없다. 다음 판에서도 `lib/emit.mjs` 의 `overrides.<Name>.skip` 과 `cardByDir`,
  포크의 원본 `lib/preview-gen-storybook.mjs` 를 먼저 비교한다.
- 원격 `fonts/` 에 옛 고정폭 글꼴(IBM Plex Mono 10개, JetBrains Mono 18개)이 남아 있다. 새 빌드는 Noto Sans Mono 만
  내고 `fonts/fonts.css` 도 그것만 가리켜 화면에는 영향이 없다. 드라이버의 `upload.deletePaths` 가 `components/` 경로만
  비교해 비어 있었고, 스킬이 재동기화의 삭제 목록을 손으로 짓지 말라고 해 2026-10-14 에 지우지 않았다. 지우려면 사람이
  승인한 `finalize_plan` 의 `deletes` 에 그 경로를 들어야 한다.
- Alert 는 `cfg.overrides.Alert.cardMode: "column"` 이다. 2026-10-14 validate 가 보여 주기용 스토리 둘이 격자 칸보다
  넓다고(`[GRID_OVERFLOW] wide`) 알렸다. 표시 키라 채점에 들지 않는다.
- config 의 `projectId` 가 `get_project` 에서 `404` 이고 `list_projects`(쓸 수 있는 것만 보인다)에 없으면, 프로젝트가
  지워졌거나 다른 계정으로 로그인했을 수 있다. 2026-10-12 에는 다른 계정이었다(사용자가 알렸다). 새 프로젝트를 만들기 전에
  사람에게 지금 로그인한 계정이 그리는 계정인지 묻는다. 두 계정이 같아야 한다는 규약은 `docs/agents/issue-tracker.md` 화면
  디자인 절이다. 목록에 프로젝트가 있으면 그 owner 를 함께 보이면 묻기 쉽다(`DesignSync` 도구 설명이 `list_projects` 가 owner 를
  돌려준다고 적는다).
- 포크 파일은 채점 계약의 일부다. 주석만 고쳐도 다음 driver 실행이 모든 컴포넌트의 채점을 지우고 기본 상한(스토리 6개)으로만
  다시 캡처한다(2026-10-12 셀프 리뷰 뒤 한 번 겪었다). 포크를 고치면 `compare.mjs --max-stories 12` 로 다시 캡처해 다시 채점한다.
  줄바꿈도 계약의 바이트다. 포크는 작업 트리에서 LF 여야 한다(`git ls-files --eol .design-sync` 의 `w/lf`). 스킬 폴더에서
  `cp` 로 만든 첫 사본이 CRLF 여서 계약이 CRLF 로 찍혔고, 그대로 두면 LF 로 받은 체크아웃의 첫 동기화가 채점을 모두 지운다.
  2026-10-12 PR 직전 리뷰가 짚어 LF 로 맞추고 다시 찍었다. 다시 찍을 때 driver 가 `ds-bundle/` 을 새로 지어 이전 캡처가
  지워지므로, 바이트로 견주려면 driver 전에 `_screenshots/compare/raw/` 를 보관한다.
- 포크 `overrides/preview-gen-storybook.mjs` 는 2.1.286 의 원본(2.1.295 도 같다)에 감싸는 요소 하나만 더했다. globals 를
  정한 스토리는 그 값으로, 정하지 않은 스토리는 기본 테마·라이트로 감싼다(위 "고친 것"의 둘). 스킬이 올라가면 원본과 다시
  맞춘다(`[OVERRIDE]` 줄이 빌드 로그에 뜬다). 감싸는 div 의 기본 테마 `nokcheong` 과 밀도 값 둘은 `themes.ts` 의
  `DEFAULT_THEME`·`DENSITIES` 와 같아야 한다. 라이트 고정은 `themes.ts` 에 짝이 없다(패키지는 모드가 없으면 시스템을
  따른다). 2026-10-14 동기화가 2026-10-13 의 포크 변경 뒤에 한 번, 그날 고친 포크 뒤에 한 번 아홉 컴포넌트를 모두
  다시 채점했다(아래 "채점").
- `story-constants.js` 는 스토리가 컴포넌트 모듈에서 함께 import 하는 상수를 손으로 든다. 스토리가 새 상수를 쓰면
  미리보기가 `.map` of undefined 로 깨지고 validate 의 `[RENDER]` 가 잡는다.
- `esbuild-paths.json` 은 lucide-react 의 exports 맵 부재에 기댄다. lucide-react 가 exports 맵을 들이거나 아이콘 파일이
  `.js` 가 되면 지워도 된다.
- 카드에는 보여 주기용 스토리만 오르고 그 스토리에는 play 가 없다. 2026-10-12 첫 동기화의 채점(아래 "채점")은 변형
  스토리를 올리던 때의 것이라 지금 카드의 근거가 아니다. 지금의 근거는 2026-10-14 채점이다.
- 글꼴은 참조 Storybook 의 컴파일된 CSS 에서 온다(`[CSS_FROM_STORYBOOK]`). 변환기는 `build` 가 낸 `dist/theme.css` 를
  쓰지 않는다. 고르는 CSS 는 JS 가 import 한 CSS, `cfg.cssEntry`, `dist/styles.css`·`dist/style.css` 같은 정해진 이름뿐이다
  (`package-build.mjs`). 패키지 JS 가 CSS 를 import 하거나 그 이름의 CSS 가 생기면 변환기가 그것을 고르고 글꼴이 빠질 수
  있다. `[FONT_MISSING]` 을 본다.
- Playwright 는 저장소 판(1.63.0)에 맞췄다. 저장소가 올리면 `.ds-sync` 의 판도 맞춘다.

## 채점

- 2026-10-12 첫 동기화: 스토리 대부분이 `play` 함수(클릭, Tab)를 가진 변형 스토리였다. Storybook 은 play 를 돌려 포커스
  링을 남기고 미리보기는 돌리지 않는다. 그 차이만 있는 스토리는 `close` 로 두었다(고칠 수단이 없다. 미리보기에서 포커스를
  흉내 내면 카드가 포커스 상태로 보인다). 감싸는 div 때문에 다크와 기본이 아닌 테마의 스토리는 미리보기에서 여백 16px 의
  칠한 상자로 보이고 Storybook 은 문서 전체를 칠했다. 틀의 차이라 `match` 로 두었다. 이 스토리들은 이제 빼는 목록에
  들어 카드에 오르지 않는다.
- 2026-10-14 재동기화: 보여 주기용 11개를 모두 `match` 로 매겼다. 스토리가 하나나 둘이라 한 장씩 모두 보았고 Button 과
  StatusBadge 는 raw 쌍도 열었다. 글꼴(Noto Sans KR, Noto Sans Mono), 녹청 색, 구성이 같고 차이는 틀뿐이다(미리보기는
  여백 24px 의 흰 칸, 참조는 `var(--bg)` 바탕). 올린 뒤 다크 설정에서 카드 글자가 흐린 것을 보고 포크를 고쳐(위 "고친
  것") 아홉을 다시 캡처해 다시 모두 `match` 로 매겼다. 라이트에서 그린 시트 아홉은 앞의 판과 눈으로 같아 보였다(바이트
  비교는 하지 않았다. 앞의 캡처를 보관하지 않았다). 마지막 드라이버 실행에서 아홉 모두 `carried forward` 였다. 다시 올린
  뒤 다크 설정의 앱에서 Button 과 StatusBadge 카드의 글자가 진하게 보이는 것을 손으로 봤고, 나머지 일곱은 다크에서 열어
  보지 않았다. 창의 목록에는 컴포넌트 아홉(atoms 여섯, molecules 셋)이 모두 있었다.
