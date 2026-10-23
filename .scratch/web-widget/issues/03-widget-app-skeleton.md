# 03: 위젯 앱의 뼈대 — `/widget` iframe 페이지가 첫 화면을 사이트가 고른 테마로 그리고, 위젯의 Storybook과 사진 비교가 선다

**What to build:** `web/apps/widget` 앱이 생기고, Next의 `basePath` `/widget` 아래 iframe 페이지가 뜬다. `/widget?agent=…&heading=…&intro=…&theme=…&mode=…`로 열면 위쪽 띠에 이름과 "새 대화" 글자 버튼이, 대화 자리에 할 수 있는 일 한 줄(있을 때)과 "아래에 요청을 적어 보내 주세요."가, 아래에 여러 줄 입력창과 보내기 버튼이 선다. 사이트가 준 테마와 라이트·다크 모드로 그려지고, 질의를 잘못 주면 무엇이 틀렸는지 보인다. 요청을 보내는 길은 05가 잇는다. 위젯의 Storybook, 화면 동작 테스트와 스토리 테스트의 vitest 프로젝트, 사진 비교가 이 앱에서 선다. 사진 비교 도우미는 디자인 시스템 패키지에서 `@agent-os/ui/visual` 하위 경로로 옮겨 위젯과 함께 쓴다.

사이트 파일은 아직 읽지 않는다(04). 그동안 iframe 페이지의 `frame-ancestors`는 `'none'`이다. ADR 0024의 fail-closed가 처음부터 서게 하기 위해서다.

근거는 `.scratch/web-widget/spec.md`의 "위젯 앱의 배치와 빌드"(경로, 스타일, 아이콘, 테스트 프로젝트, 사진 비교, ADR 0024가 넘긴 셋), "임베드"(iframe 방식의 질의, 잘못 준 속성, 크기), "테마·모드·밀도·글꼴", "대화 화면"의 첫 화면 절과 Testing Decisions 1·3이다. ADR 0024, ADR 0026과 그 이력이 앞선 결정이다. 화면은 `.scratch/web-widget/design/`의 `mk-conversation`, `mk-dark`, `mk-themes`이고 위쪽 띠는 고른 A다.

**Blocked by:** None (can start immediately)

**Status:** done

### 앱과 빌드

- [x] **Next의 `basePath`는 `/widget`이고 iframe 페이지는 `/widget`이다**(ADR 0024 이력 2026-10-23). 글꼴 파일은 `/widget/fonts/` 아래에서 Next의 `public/`으로 나간다
- [x] **ADR 0024가 티켓에 넘긴 셋 가운데 둘을 이 티켓이 정한다.** 시작 래퍼를 공유 자리로 옮길지 위젯이 자기 래퍼를 둘지, 워크스페이스의 vite 판을 고정할지다. vite는 디자인 시스템 패키지가 이미 `^8.3.1`로 선언했고 잠금 파일은 8.3.1이다. 셋째(Node의 TOML 파서)는 04가 정한다
- [x] **스타일.** 위젯의 CSS는 디자인 토큰 CSS를 `@import`하고 `@source`로 위젯 소스를 덮는다. iframe 페이지는 글꼴 CSS도 싣는다
- [x] **아이콘은 `IconName` 열여섯으로 그린다.** 새 아이콘이 필요해지면 앱이 lucide를 직접 들이지 않고 `IconName`에 더한다
- [x] **글꼴 응답에는 `next.config`의 헤더가 `Access-Control-Allow-Origin: *`를 단다.** 자격 증명 없이 받는 공개 파일이다
- [x] **iframe 페이지의 `frame-ancestors`는 `'none'`이다**(04가 사이트 파일에서 허용 출처를 넣을 때까지)

### 첫 화면과 질의

- [x] **질의 다섯**(`agent` 필수, `heading`, `intro`, `theme`, `mode`)의 이름과 뜻은 명세 "임베드"의 속성 다섯과 같다. `heading`이 없으면 `agent` 값을 보이고, `intro`가 없으면 그 줄을 그리지 않는다
- [x] **잘못 준 질의.** `agent`가 없거나 플러그인 이름의 패턴(`^[a-z][a-z0-9-]{1,62}$`) 밖이면 대화 자리에 위험 알림(제목 "위젯 설정이 올바르지 않습니다.", 본문 "사이트 관리자에게 알려 주세요.")을 보이고 입력창을 막으며, 질의 이름을 든 `console.error`를 남긴다. `theme`이나 `mode`가 목록 밖이면 기본값으로 그리고 `console.error`만 남긴다
- [x] **테마·모드·밀도.** 문서의 `html`에 `data-theme`·`data-mode`와 `data-density="regular"`를 단다. 테마 값의 검사는 디자인 시스템 패키지가 내보내는 테마 목록을 읽는다. `mode`가 없으면 시스템 설정을 따른다
- [x] **크기.** 위젯은 자기 자리(iframe의 크기)를 채운다. 지원하는 가장 좁은 폭은 320px이고 레이아웃의 기준 폭은 `@wide:`(360px)다

### 테스트 프로젝트와 Storybook

- [x] **뿌리 `vitest.config.ts`에 위젯의 페이지 테스트 프로젝트(jsdom, 이름 `widget-pages`)와 스토리 테스트 프로젝트(chromium, 이름 `widget-storybook`)를 더한다.** 패키지의 `storybook`, 관리 화면의 `pages`와 겹치지 않는다
- [x] **위젯의 Storybook은 `apps/widget/.storybook/`이다**(ADR 0026 이력, design-system 티켓 01). 위젯의 CSS가 Storybook에서 서는지를 스토리 시험이 본다
- [x] **사진 비교 도우미**(Storybook 정적 빌드를 열고 스토리를 찍는 테스트 도구)를 정적 빌드의 자리를 인자로 받게 바꿔 `@agent-os/ui/visual` 하위 경로로 내보낸다. 패키지의 컴포넌트와 토큰은 바뀌지 않는다. 위젯은 자기 설정과 정답 사진을 위젯 앱 안에 둔다. 로컬 명령은 지금처럼 사진 비교 명령에 패키지 경로(`apps/widget`)를 준다
- [x] **CI의 `visual` 잡**이 같은 컨테이너에서 위젯의 Storybook 정적 빌드와 비교를 한 단계씩 더하고, 실패하면 위젯의 결과도 아티팩트로 올린다. 디자인 시스템 패키지의 사진 비교는 옮긴 뒤에도 그대로 초록이다

### 시험

- [x] **화면 동작 테스트(`widget-pages`).** 첫 화면의 글(`intro`가 있을 때와 없을 때), 잘못 준 질의의 알림과 `console.error`, 목록 밖의 `theme`·`mode`, `data-density`. TS 시험의 이름은 행동을 말하는 한국어 문장이다(`.claude/rules/web-workspace.md`)
- [x] **위젯 스토리(`widget-storybook`).** 폭 320px과 400px에서 첫 화면을 그려 분류 판정(`@agent-os/ui/testing`), 접근성(addon-a11y), 사진을 본다. 디자인 시스템 패키지의 스토리가 선례다
- [x] **빌드 설정의 시험**(선례는 관리 화면의 `next.config.test.ts`). `frame-ancestors 'none'`과 글꼴 응답의 `Access-Control-Allow-Origin: *`

### 검증

- [x] `CLAUDE.md`의 검증 명령이 모두 초록이다. `packages/ui`를 건드리므로 사진 비교를 Docker로 친다(`pnpm -C web visual`)

### 이 티켓이 정한 것

근거와 고른 까닭은 일지 2026-10-23-50이다.

1. **위젯이 자기 시작 래퍼(`apps/widget/tools/start.ts`)를 둔다**(ADR 0024가 넘긴 첫째). 관리 화면의 래퍼를 공유 자리로 옮기면 그 e2e와 시험을 함께 옮겨야 하고, 위젯의 래퍼는 빌드 전에 글꼴을 복사하는 일이 더 있다. 대가로 루프백 목록이 세 벌(`serve`의 `src/agent_os/main.py`, 관리 화면의 `tools/loopback.ts`, 위젯 래퍼)이고, 세 자리 모두에 "셋을 함께 고친다"를 적었다.
2. **vite 판은 고정하지 않는다**(둘째). 위젯도 `^8.3.1`로 선언하고 잠금 파일이 8.3.1 하나를 든다.
3. **글꼴은 래퍼가 `dev`·`build` 전에 `public/fonts/`로 복사한다.** Next의 `public/`은 워크스페이스 패키지의 파일을 가리킬 수 없다. 복사본은 `.gitignore`가 무시하고 `tools/tidy_checkouts.py`가 다시 만들 수 있는 자리로 본다.
4. **디자인 시스템 `themes.ts`는 `./styles/contrast.ts`를 `.ts` 확장자로 들인다.** 위젯의 `next build`(Turbopack)가 `.js`를 이웃 `.ts`로 풀지 못했다. 패키지 tsconfig에 `rewriteRelativeImportExtensions`를 켰고 컴포넌트와 토큰은 바뀌지 않았다.
5. **컨테이너 안에서 위젯이 `workspace:`로 기대는 패키지는 복사하지 않고 `/web/...`로 링크를 건다**(`web/tools/visual.ts`). Playwright 1.63이 실제 경로가 `node_modules` 아래인 파일을 TypeScript로 바꾸지 않기 때문이다.
6. **빈 질의 값.** 보일 글인 `heading`·`intro`의 빈 값만 주지 않은 것으로 읽고, `agent`·`theme`·`mode`의 빈 값은 준 값이라 패턴·목록 밖으로 본다(셀프 리뷰 명세 축).
