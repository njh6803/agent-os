# 06: 위젯 미리보기 페이지가 고른 사이트의 설정으로 위젯을 그리고, 위젯 미리보기 페이지 e2e가 CI 잡 `e2e-portal`에서 돈다

**What to build:** 최종 사용자가 `/portal/`을 열면 디자인 시스템의 토큰과 글꼴로 칠한 페이지 하나가 뜨고, 가운데 위젯 자리(폭 400px, 높이 560px)에 첫 사이트의 설정(`heading`, `intro`, `theme`, `mode`, 에이전트)으로 그린 `<agent-os-widget>`이 보인다. `?site=<이름>`으로 열면 그 사이트가 골라지고, 페이지 제목과 화면 읽기 프로그램만 읽는 `<h1>`이 그 사이트의 `heading`이다. `/`로 들어오면 질의를 지킨 채 `/portal/`로 넘어간다. 페이지는 같은 출처의 파일만 싣고(`Content-Security-Policy: default-src 'none'; …`), 스크립트를 끈 브라우저에는 "이 페이지는 스크립트가 있어야 동작합니다." 한 줄이 보인다. 저장소 기여자에게는 위젯 미리보기 페이지 e2e(`pnpm -C web/apps/portal exec playwright test`)가 생기고 CI의 새 잡 `e2e-portal`이 그것을 ubuntu에서 돌린다(스토리 4의 앞부분, 15).

06은 05와 02 뒤이고 07을 막는다. 05의 끝점을 페이지가 부르고, 02의 `@agent-os/e2e-stack`으로 위젯 미리보기 페이지 e2e의 준비를 짓는다. 명세 묶음 C의 앞과 묶음 E의 준비이고, 묶음 E의 문서 가운데 CI 잡의 것을 이 티켓이 고친다(명세 "고칠 자리의 묶음"의 주석).

**병합 뒤에 틈이 있다(to-tickets에서 사용자가 아홉 장 분할을 골랐다).** 이 티켓만 병합된 main에서는 처음 온 브라우저가 고지 덮개 없이 위젯을 보고, 질문을 보내면 토큰 끝점이 401이라 위젯이 "로그인 정보를 받지 못했습니다."를 보인다. 고지 확인 흐름은 07이 그린다. 사이트를 고르는 셀렉트, 다크 모드 스위치, 보증 모드별 모습, 보고서 링크는 08이다. 아직 이 앱을 띄우는 배포가 없으므로 바깥에 보이는 것은 바뀌지 않는다.

근거는 `.scratch/pilot-portal/spec.md`의 "띄우기와 타입 검사"(페이지 스크립트, 토큰 CSS, 글꼴)와 그 2026-11-10 명세 검토 주석(둘째의 의존, 넷째의 `ExperimentalWarning`, 다섯째의 Linux 확인), "경로와 끝점"과 그 주석(글꼴 `ETag`), "페이지"의 첫 둘째 셋째 항목, "모양"과 그 주석, "함께 쓰는 e2e 준비와 중계"와 그 주석 둘째, "전역 `fetch` 금지의 예외"와 그 주석, "고칠 자리의 묶음"의 C·E 줄과 그 주석, Testing Decisions의 "Vitest", "Playwright e2e"의 준비와 CI 잡, "판정자와 저장소 상태"다. 측정은 `.scratch/pilot-portal/probes/node_ts_workspace.py`(`page_script_strip*`, `theme_css_build*`, `fonts_*`)와 그 `README.md`이고 다시 돌리지 않는다. 화면은 `.scratch/pilot-portal/design/`(표는 그 `README.md`)이다. 앞선 결정은 ADR 0050의 결정 "띄우기", "경로", "페이지", "모양과 화면", "함께 쓰는 코드"와 그 2026-11-09 이력 "띄우기의 어림을 잰 값으로 바꾸고 토큰 CSS와 페이지 스크립트는 시작 때 짓는다", Consequences "전역 `fetch` 금지"다. CSP와 위젯의 구성 스타일시트는 `web/apps/widget/EMBED.md`의 CSP 절이다.

**Blocked by:** 05 (사이트마다 고지 확인 끝점이 익명 식별자 쿠키를 주고, 토큰 끝점이 사이트 토큰을 낸다). 05의 토큰 끝점을 `tokenProvider`가 부른다. 02 (위젯 e2e의 준비를 `@agent-os/e2e-stack`으로 뽑는다). 02의 중계, `serve` 띄우기, 픽스처 플러그인, 키 도우미, 트레이스 폴더를 넘기는 길을 쓴다

**05가 넘긴 메모.** 05가 순수 처리기를 `handle(request, context)`로 바꿨다. `context`는 `server/context.ts`의 `PortalContext`(공개 출처, `kid`, 개인 키, 사이트마다 이름·발급자·`audience`·보증 모드, `now`와 `newAnonymousId`)이고 `tools/start.ts`가 `portalContext(loaded, {now, newAnonymousId})`로 짓는다. 이 티켓의 페이지·정적 파일 경로는 같은 `handle`에 더하고, 페이지가 데이터 블록에 쓸 사이트 값(`heading`, `intro`, `theme`, `mode`, `assurance`, `notice`, `reportUrl`)은 `PortalContext`의 `SiteContext`에 없어 더하거나 설정에서 따로 받는다. `handle`의 `/portal/sites/` 아래 응답에 `Cache-Control: no-store`를 다는 자리는 `handler.ts`의 `handle`이고 페이지와 정적 파일의 `no-cache`와 `ETag`는 그와 다른 길이다. `respond`·`noContent`·`methodNotAllowed`는 `handler.ts` 안에서만 쓰는 도우미다. `serve.ts`의 `answer`는 처리기가 던진 예외를 500 `SERVER_ERROR`(`text/plain`, `no-store`)로 바꾸고 오류의 이름만 stderr에 남긴다. 글꼴 파일을 흘려보내는 `serve.ts`의 길은 그 `try`/`catch` 밖에서 읽기 오류를 따로 다뤄야 한다(`handle`이 파일 경로만 돌려주므로 `createReadStream`의 `error`는 `answer`가 잡지 못한다).

**Status:** done

### 페이지 HTML과 경로

- [x] **`GET /portal/`은 명세 "페이지" 첫 항목의 HTML을 낸다.** 질의와 쿠키를 보지 않고 같은 HTML이다. `lang="ko"`, 뿌리의 `data-density="regular"`와 첫 사이트의 `data-theme`·`data-mode`, 토큰 CSS·글꼴 CSS·페이지 CSS 링크, 데이터 블록 `<script type="application/json">`(사이트마다 `name`, `agent`, `heading`, `intro`, `theme`, `mode`, `assurance`, `notice`(전문), `reportUrl`과 쿠키 수명 일수. `<`는 `\u003c`로 이스케이프한다), 페이지 스크립트, 위젯 번들 `/widget/element.js`, `<noscript>`의 한 줄이다. 인라인 스크립트와 인라인 스타일은 없다
- [x] **응답 헤더에 `Content-Security-Policy: default-src 'none'; script-src 'self'; connect-src 'self'; style-src 'self'; font-src 'self'; img-src 'self'; frame-ancestors 'none'; base-uri 'none'`을 글자 그대로 단다**
- [x] **`GET /`는 302 `Location: /portal/`이고 질의를 그대로 붙인다.** `/portal`(끝 슬래시 없음)은 302하지 않는다(명세 "경로와 끝점"의 거부한 안)

### 정적 파일

- [x] **페이지 스크립트는 앱 안 `browser/` 폴더의 `.ts` 파일 하나다.** 서버가 시작 때 `node:module`의 `stripTypeScriptTypes`(`strip` 모드)로 타입만 벗겨 메모리에 두고 `/portal/portal.js`로 낸다. import와 export가 없는 고전 스크립트이고 함수 하나로 감싼다. 앱의 tsconfig `lib`에 DOM을 더한다
- [x] **시작 때 찍히는 `ExperimentalWarning` 두 줄을 끌지 정하고 그 까닭을 `start` 스크립트 곁 주석과 일지에 적는다.** 끄면 `node --disable-warning=ExperimentalWarning`이다(명세 "띄우기와 타입 검사"의 주석 넷째)
- [x] **토큰 CSS는 서버가 시작 때 Tailwind CLI(`tailwindcss -i <theme.css>`, `-o`를 주지 않으면 CSS가 표준 출력으로 나온다)를 자식 프로세스로 돌려 그 출력을 메모리에 읽고 `/portal/theme.css`로 낸다. 임시 폴더를 만들고 지우는 길은 없다.** `@agent-os/ui`의 `tailwindcss`를 dependencies로 옮기고 앱은 `@tailwindcss/cli`만 `@agent-os/ui`와 같은 판으로 제 의존성에 든다(명세 "띄우기와 타입 검사"의 주석 둘째. 옛 문장 "앱은 `@tailwindcss/cli`와 `tailwindcss`를"은 이 주석이 바로잡는다)
- [x] **글꼴은 복사하지 않는다.** `@agent-os/ui/fonts`의 목록으로 `/portal/fonts.css`(`url()`은 `/portal/fonts/<파일 이름>`)를 메모리에 짓고, `/portal/fonts/<파일 이름>`은 목록의 woff2만 디스크에서 흘려보낸다. 목록 밖 이름은 404다. 글꼴의 `ETag`는 시작 때 파일마다 내용 해시로 짓고, 순수 처리기는 본문으로 파일 경로를 돌려주며 `node:http`의 겉이 흘려보낸다(명세 "경로와 끝점"의 주석)
- [x] **페이지와 정적 파일에는 `Cache-Control: no-cache`와 내용 해시의 `ETag`를 달고 조건부 요청에 304로 답한다.** 콘텐츠 타입은 명세 "경로와 끝점" 표대로다

### 페이지 스크립트와 페이지 CSS

- [x] **스크립트는 `?site=`의 사이트를, 없거나 모르면 첫 사이트를 고른다.** 고르면 뿌리의 `data-theme`·`data-mode`를 그 사이트의 값으로(`mode`가 없으면 시스템 설정으로) 두고, `<agent-os-widget>`의 속성 다섯을 채우고, `tokenProvider`를 그 사이트의 토큰 끝점을 POST로 불러 200의 글을 그대로 돌려주고 200이 아니면 던지는 함수로 두며, `?site=`를 `history.replaceState`로 적고, 페이지 제목과 `<h1>`을 그 사이트의 `heading`으로 둔다(명세 "페이지", "토큰")
- [x] **페이지 CSS(`/portal/portal.css`)는 손으로 쓴 파일 하나이고 명세 "모양"과 그 주석의 규칙을 따른다.** 클래스 이름은 모두 `pp-` 접두, 토큰은 `var(--…)`로만 읽고, 밀도를 따르는 높이와 글자는 `--control-h`·`--body-size`를 읽는다(`.claude/rules/web-design.md`). 위젯 자리는 폭 400px, 높이 560px, `bg-raised`이고 좁은 폭에서는 좌우 16px 여백에 남은 폭이다. 그림자는 `0 8px 24px var(--shadow-color), 0 1px 2px var(--shadow-color)`를 직접 적고 그 원천인 `theme.css`의 `--shadow-float`를 주석으로 가리킨다. 토큰 CSS 산출의 유틸리티 클래스는 쓰지 않는다
- [x] **이 티켓이 그리는 것은 위쪽 띠의 자리, 위젯 자리, 위젯이다.** 셀렉트·다크 모드 스위치·정보 글·단추 줄·보고서 링크는 08이, 덮개·뼈대·짧은 고지·"고지 전문" 단추는 07이 그린다. 디자인 시스템 부품(Alert, Button, Switch)을 HTML로 옮기는 것과 인라인 SVG 아이콘 다섯은 그것을 그리는 티켓이 한다(명세 "모양"의 주석 둘째)

### 전역 `fetch` 금지의 예외

- [x] **`web/eslint.config.mjs`에 앱의 `browser/` 페이지 스크립트 파일 하나만을 `files`로 드는 블록을 두어, `no-restricted-globals`와 `no-restricted-properties`를 `fetch`를 뺀 HTTP 전역 목록으로 다시 건다.** 규칙째 끄지 않는다. 설정 파일에 경로와 이유(부르는 것이 Agent OS의 API가 아니라 위젯 미리보기 페이지 자신의 끝점이다)를 함께 적는다(명세 "전역 `fetch` 금지의 예외"와 그 주석, `.claude/rules/web-workspace.md`)
- [x] **`web/eslint.config.test.ts`에 사례 셋을 더한다.** 그 파일에서 `fetch`가 지난다, 그 앱의 다른 파일에서 `fetch`가 걸린다, 그 파일에서도 `XMLHttpRequest`가 걸린다

### 중계의 셋째 상류

- [x] **`@agent-os/e2e-stack`의 중계가 위젯 미리보기 페이지 상류(선택)를 받는다.** `/`(정확히)와 `/portal/` 아래는 위젯 미리보기 페이지로 넘기고, 상류를 주지 않으면 그 둘도 404라 위젯 e2e의 동작은 그대로다. 응답은 흘려보낸다(명세 "함께 쓰는 e2e 준비와 중계")
- [x] **Vitest에 `upstreamOf`의 셋째 상류 두 규칙과 상류가 없을 때의 404 사례를 더한다**

### 위젯 미리보기 페이지 e2e의 준비

- [x] **`web/apps/portal`의 Playwright 설정과 `globalSetup`이 `@agent-os/e2e-stack`으로 실제 `serve`(픽스처 플러그인), 그 사이트 파일로 빌드한 위젯 Next, 위젯 미리보기 페이지, 상류 셋의 중계를 띄운다.** 공개 출처는 `http://portal.localhost:<중계 포트>`이고, 사이트 파일의 모든 사이트가 그것과 08의 둘째 인스턴스가 쓸 루프백 출처를 허용 출처로 든다. 사이트는 넷이다. 익명 사이트 둘(같은 픽스처 에이전트. 하나는 `hourly_runs_per_site = 1`), 둘 다 사이트 하나, 로그인 사이트 하나다(명세 "Playwright e2e"). `*.localhost` 이름 풀기는 위젯 e2e처럼 Playwright 설정이 맡는다
- [x] **다른 출처 `http://other.localhost:<포트>`의 작은 페이지 하나가 확인 끝점으로 폼 POST를 보낸다.** 그 사례는 07이 쓴다
- [x] **준비가 위젯 미리보기 페이지 프로세스의 출력을 모아 시험이 읽을 수 있는 자리에 남기고, 02의 길로 트레이스 폴더를 넘긴다.** 07의 "출력에 쿠키와 토큰이 없다" 사례와 트레이스 주체 사례가 쓴다

### e2e 사례(이 티켓의 몫)

- [x] **페이지에 CSP 위반 콘솔 메시지가 없고 본문의 글꼴 변수가 토큰 값으로 풀린다**(명세 "Playwright e2e")
- [x] **첫 사이트의 설정으로 위젯 요소의 속성 다섯이 채워지고, `?site=<이름>`으로 열면 그 사이트가 골라지며 페이지 제목이 그 사이트의 `heading`이다**

### CI 잡과 문서

- [x] **`.github/workflows/ci.yml`에 잡 `e2e-portal`을 `e2e-widget`과 같은 모양으로 더하고 `verify`의 `needs`에 넣는다.** `timeout-minutes`는 지난 실행이 없는 첫 값이라 어림이고, 머리 주석의 규칙대로 그 잡이 든 실행으로 프로브를 다시 돌려 고친다. 머리 주석의 잡 수("잡 여섯")를 고친다. 이 잡이 ubuntu에서 실제 위젯 미리보기 페이지를 띄우는 것이 Linux 확인이다(명세 "띄우기와 타입 검사"의 주석 다섯째)
- [x] **CI 잡의 문서를 고친다.** `CLAUDE.md` 검증 명령에 로컬 명령 `pnpm -C web/apps/portal exec playwright test`와 치는 때(위젯 미리보기 페이지, `e2e-stack`, 서버의 최종 사용자 경로를 건드렸을 때)를 적고, 게이트 수 문장("게이트는 열여섯", "남은 셋인 관리 화면 e2e, 위젯 e2e, 사진 비교는 CI만 돈다")을 고친다. `docs/constitution/operations.md`의 CI 잡 서술(잡 목록과 `verify`가 기다리는 잡 수), `docs/constitution/tech.md` 원격·CI 행, e2e를 둘로 세는 `.claude/rules/http.md`와 `ci.yml` 머리 주석의 "두 e2e"도 고친다. 실제 `serve`를 띄우는 곳을 나열하는 문장에 위젯 미리보기 페이지 e2e를 더한다. 지금은 `web/apps/admin/e2e/stack.ts`의 머리 주석이 그 목록을 닫아 들고(02가 그 주석의 위젯 준비 경로를 고친다), 다른 자리는 "실제 `serve`"로 grep해 찾는다. 헌법을 고치면 판을 patch로 올린다. 옛 수("여섯 잡", "잡 여섯", "열여섯", "두 e2e")의 grep 잔존이 살아 있는 문서에서 0이다. 바꾼 rules는 새 세션에서 그 경로의 파일을 Read로 열어 실리는 것을 본다(작업 규약 3)

### Vitest

- [x] **node 프로젝트에서 순수 함수를 부르는 사례를 명세 "Vitest" 가운데 이 티켓의 몫으로 둔다.** 페이지 HTML(데이터 블록이 `</script>`가 든 고지 글을 이스케이프하고, CSP 헤더가 글자 그대로이며, `nosniff`가 있고, 인라인 스크립트가 없고, 뿌리에 `data-density="regular"`가 있다), 리다이렉트가 질의를 지키는 것, 정적 파일의 콘텐츠 타입과 `ETag`·304, 글꼴 목록 밖 이름의 404, 벗긴 페이지 스크립트가 JavaScript로 파싱된다(`vm.Script`). 벗긴 스크립트의 글자나 CSS 산출의 바이트 수는 단언하지 않는다(명세 "좋은 시험")

### 검증

- [x] **빨강을 먼저 본다**(헌법 원칙 II). 페이지 HTML과 정적 파일의 Vitest, 이 티켓의 e2e 사례가 구현 전에 빨갛다
- [x] **위젯 미리보기 페이지 e2e와 위젯 e2e(`pnpm -C web/apps/widget exec playwright test`)가 로컬에서 초록이다.** 중계를 바꿨으므로 위젯 e2e도 친다. `packages/ui`의 `package.json`을 고쳤으므로 사진 비교 셋(`pnpm -C web visual`, `visual:widget`, `visual:admin`)도 친다
- [x] **CI의 `e2e-portal` 잡이 초록이다**
- [x] **검증 명령이 모두 초록이다.** 손으로 치는 다섯과 위의 e2e 둘·사진 비교다
