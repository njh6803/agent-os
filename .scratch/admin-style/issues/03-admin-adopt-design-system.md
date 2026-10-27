# 03: 관리 화면이 디자인 시스템을 들이고, 관리 토큰 넣기 화면이 그림대로 서며, 관리 화면의 Storybook과 사진 비교가 선다

**What to build:** 운영자가 관리 토큰 없이 관리 화면을 열면, 틀 없이 "Agent OS"와 화면 머리 "관리 토큰 넣기", 카드 하나에 가린 입력 "관리 토큰"과 주 버튼 "넣기"가 디자인 시스템의 글꼴과 기본 테마(녹청)로 선다. 거부되거나 서버에 닿지 못하면 무엇이 실패했고 무엇을 할지 알림으로 보고, 이 탭에 채널 토큰이 남아 있으면 카드 아래에서 지운다. 휴대폰 폭에서도 같은 한 칸이 가로로 밀리지 않는다. 관리 화면 앱은 디자인 토큰 CSS와 글꼴 CSS를 싣고, 관리 화면의 Storybook과 스토리 테스트 프로젝트 둘(폭 1280과 320), 사진 비교(`visual:admin`)와 그 CI 단계가 이 티켓에서 선다.

다른 화면(플러그인, 실행, 틀)은 04~09가 다시 그린다. 이 티켓이 디자인 토큰 CSS를 실으면 Tailwind의 기본 초기화도 함께 실려, 그 화면들은 04~09가 병합될 때까지 브라우저 기본 모양(버튼 테두리, 제목 크기)을 잃는다. 조작과 시험은 역할과 이름으로 찾으므로 그대로다.

근거는 `.scratch/admin-style/spec.md`의 "디자인 시스템 들이기", "관리 토큰 넣기"(2026-10-27 주석의 최대 폭 `form`), "화면 머리와 공통 상태"의 관리 토큰 넣기 알림 문단, Testing Decisions "모양"의 Storybook·스토리 테스트 프로젝트·사진 비교 줄과 그 주석(테마 단언을 두지 않는 것, 틀과 부품의 단언), "e2e"의 주석(글꼴 e2e), "검증과 문서"와 그 주석, Further Notes의 웹 편집 확인 주석이다. ADR 0026과 그 2026-10-07 이력(앱마다의 Storybook)이 앞선 결정이고, 위젯이 선례다(`web/apps/widget/.storybook/`, `web/apps/widget/visual/`, `.scratch/web-widget/issues/03-widget-app-skeleton.md`). 측정은 `.scratch/admin-style/probes/`의 `next_fonts.mjs`, `storybook_next_link.mjs`, `storybook_viewport.mjs`다.

**Blocked by:** 01, 02

**Status:** ready-for-agent

### 시작 전

- [ ] **웹 편집 확인을 사람과 함께 먼저 한다.** 이 티켓이 화면 파일(`mk-token.dc.html`, `mk-token-m.dc.html`)을 처음 읽는다. 명세를 쓴 세션의 계정은 화면 Design 아티팩트를 읽지 못했다("artifact not found", 명세 머리). 그래서 시작하면서 사람을 불러 그 아티팩트의 주인이나 편집자인 계정으로 맞춰 달라고 하고, `/ui-design`의 "웹 편집 확인"(화면 파일과 옮긴 `canvas.json`마다 sha256)을 한다. 지금 계정이 여전히 읽지 못하면 멈추고 사람에게 넘긴다. 다르면 멈추고 사람에게 묻는다

### 들이기

- [ ] 관리 화면 앱이 `@agent-os/ui`(워크스페이스), `@tailwindcss/postcss`, `tailwindcss`를 들이고, Storybook에 쓰는 것(`@tailwindcss/vite`와 Storybook 묶음)은 위젯 앱과 같은 판으로 들인다
- [ ] PostCSS 설정은 `@tailwindcss/postcss` 하나다
- [ ] 앱의 전역 CSS가 디자인 토큰 CSS(`@agent-os/ui/theme.css`)를 import하고 `@source`로 앱의 소스를 덮으며, 글꼴 CSS(`@agent-os/ui/fonts.css`)는 따로 import한다. 둘을 import하는 것은 모든 화면이 지나는 pages 층의 공통 컴포넌트다(`app/`은 판정자가 pages·templates와 next·react만 들이게 막는다)
- [ ] 문서 뿌리에 `data-mode`와 `data-density`를 달지 않는다

### 관리 토큰 넣기 화면

- [ ] "Agent OS"(제목 요소가 아닌 글자), `h1` "관리 토큰 넣기"와 설명 "agent-os serve 를 띄울 때 AGENT_OS_ADMIN_TOKEN 에 준 값이다. 이 탭에만 남고 탭을 닫으면 사라진다.", 카드, 아래 줄이 최대 폭 `form`의 한 칸에 선다
- [ ] 카드(`Card`, 안쪽 4) 안에 가린 한 줄 입력("관리 토큰", `type` `password`, `autocomplete` off, 도움말 "넣으면 플러그인 목록을 한 번 읽어 맞는 토큰인지 본다.")과 주 버튼 "넣기"(제출)다. 넣는 즉시 칸을 비우는 지금의 행동은 그대로다
- [ ] 거부면 `Alert` 위험의 제목 "관리 토큰이 거부됐다"와 본문 "서버를 띄울 때 준 값과 같은지 보고 다시 넣는다.", 서버에 닿지 못하면 제목 "서버에 닿지 못했다"와 본문 "agent-os serve가 떠 있는지 보고 다시 넣는다."다
- [ ] 이 탭에 채널 토큰이 남아 있으면 카드 아래에 "이 탭에 채널 토큰이 남아 있다."와 보조 버튼 "토큰 지우기"다(지금 행동)
- [ ] 페이지 시험(`HomePage.test.tsx`)의 이 화면 단언이 새 문구와 `h1`을 보고, 레이블이 입력을 감싼다고 단언한 곳은 레이블로 찾는 단언으로 바뀐다(가린 입력은 `TextField`라 `<label for>`로 이어진다)

### 관리 화면의 Storybook

- [ ] Storybook은 `apps/admin/.storybook/`이다. 미리보기는 앱의 전역 CSS와 글꼴 CSS를 싣고 `@agent-os/ui/storybook`의 `storyPreview`에 그 전역 CSS(`?inline`)를 넘긴다. 밀도 globals는 "auto"(속성을 달지 않음)다
- [ ] `next/link`는 `viteFinal`에서 평범한 `<a>`를 그리는 앱의 대역으로 별칭한다. 스토리 테스트와 정적 빌드 두 길 모두 그 별칭을 지난다
- [ ] **스토리 테스트 프로젝트는 둘(`admin-storybook-wide`, `admin-storybook-narrow`)이고 같은 `configDir`을 나눠 쓴다.** 미리보기의 `parameters.viewport.options`에 1280×900과 320×640 항목을 두고, 프로젝트마다 `storybookTest`의 `initialGlobals`로 그 항목을 고른다. 프로젝트의 `test.browser.viewport`는 쓰지 않는다(스토리마다 1200×900으로 덮였다). 두 프로젝트에서 창이 1280과 320인지 한 번 단언한다. ADR 0026의 2026-10-07 이력이 적은 조건(프로젝트 이름이 겹치지 않는다)을 지킨다. 문서 뿌리의 테마가 기본인지는 단언하지 않는다(명세 주석)
- [ ] 미리보기는 스토리마다 그리기 전에 localStorage를 비운다
- [ ] 좁은 프로젝트에서 미리보기의 afterEach가 문서의 가로 스크롤이 없는지(`scrollWidth`가 창 폭을 넘지 않는지) 본다
- [ ] axe의 `target-size` 규칙(포인터 목표 24px)이 관리 화면 미리보기에서 켜져 있는지 보고, 꺼져 있으면 켠다. 켠 뒤 24px 미만의 목표를 잠시 그려 빨개지는 것을 한 번 손으로 본다(커밋하지 않는다)
- [ ] 관리 토큰 넣기의 스토리가 빈 상태, 거부, 서버에 닿지 못함, 채널 토큰이 남은 상태를 하나씩 그리고, 두 프로젝트에서 클래스 판정과 axe를 지난다. 표본 값은 그림의 것이다

### 사진 비교

- [ ] 사진 비교는 `apps/admin/visual/`의 Playwright 설정이고 정적 빌드를 여는 길은 `@agent-os/ui/visual`을 나눠 쓴다. 프로젝트는 폭 1280(높이 900)과 320(높이 640) 둘이고 둘 다 `timezoneId` Asia/Seoul, `locale` ko-KR, `maxDiffPixels` 0이다
- [ ] 판정 스토리를 뺀 관리 화면의 스토리를 기본 테마의 라이트·다크로 찍고, 밀도는 달지 않아 폭이 고른다. 정답은 `apps/admin/visual/snapshots/`이고 이름은 `<스토리 id>-<폭>-<모드>.png`다. 상호작용(올림·누름)의 사진은 더하지 않는다
- [ ] 명령 `pnpm -C web visual:admin`과 `visual:admin:update`(`web/tools/visual.ts apps/admin`)가 선다. `web/package.json`의 `typecheck`가 `apps/admin/visual`의 tsconfig를 더 보고, CI(`.github/workflows/ci.yml`)의 `visual` 잡이 관리 화면의 단계와 결과 아티팩트를 더한다

### e2e

- [ ] **글꼴 e2e 하나.** 빌드한 앱의 문서에 Noto Sans KR과 Noto Sans Mono의 `@font-face`가 있고, 패밀리마다 woff2 하나를 받아 200인지 본다. 측정(`next_fonts.mjs`)뿐이던 Next 쪽 글꼴을 남는 시험으로 둔다
- [ ] `admin-token.e2e.ts`의 문구와 조회가 새 화면에 맞는다. localStorage 단언을 좁히는 것은 09다

### 문서

- [ ] 사진 비교 명령을 적은 살아 있는 문서(`CLAUDE.md` 검증 명령의 web 괄호, `docs/constitution/operations.md`, `docs/constitution/README.md`, `README.md`, `.claude/rules/web-design.md`)에 `visual:admin`과 그것을 칠 때(관리 화면이나 패키지를 건드렸을 때)를 더한다. `web-design.md`의 "관리 화면의 스토리는 admin-style이 세운다"는 선 모양으로 고친다
- [ ] `docs/constitution/tech.md` 웹 줄의 "아직 스타일과 아이콘이 없다(admin-style이 들인다, ADR 0021 이력)"를 들인 모양으로 고친다. 테마의 localStorage 문장은 09다
- [ ] 옛 표현을 저장소 전체에서 grep해 살아 있는 문서에 잔존이 0인지 본다(`CLAUDE.md` 작업 규약 4)

### 검증

- [ ] 검증 명령이 모두 초록이고, `pnpm -C web visual:admin`(Docker)과 관리 화면 e2e(`pnpm -C web/apps/admin exec playwright test`)도 초록이다. 모델 경로를 건드리지 않아 `-m llm`·`-m llm_widget`은 칠 일이 없다
