# 2026-10-24 (14) 위젯의 페이지 안 방식과 임베드 안내

## 사용자 프롬프트

> 사용자: /implement .scratch/web-widget/issues/10-widget-element-embed.md (next-session 지시문. 나란히 여는 3 중 2, 브랜치 feature/10-widget-element-embed, 범위는 PR과 병합까지. 주 체크아웃에서 브랜치를 따지 않고 워크트리에 먼저 들어간다. tidy-checkouts는 묶음의 첫 세션이 돈다)

이 세션은 컨텍스트가 한 번 압축된 뒤 이어졌다. 사용자에게 물은 것은 없다.

## 결정

- **번들은 설정 파일 없이 Vite 의 프로그램 API 로 짓는다(`tools/element.ts`).** 앱 폴더에 `vite.config.ts` 를 두면 앱 폴더에서 띄운 위젯 Storybook 의 빌더가 그것을 찾아 읽는다. 시작 래퍼가 `dev`·`build` 전에 글꼴 복사 뒤 번들을 짓고, 번들 빌드가 사이트 파일을 읽지 못하면 next 를 부르지 않고 끝난다.
- **두 방식이 화면 한 벌을 나눠 쓴다.** 토큰과 기준 주소를 `Connection`(`lib/connection.ts`)으로 묶고, iframe 페이지가 들던 대화·초안·문제 알림을 `ConnectedWidget` 으로 뽑았다. 나란히 도는 07 과 겹치는 `useConversation` 의 변경은 인자 둘(에이전트, 길)로 좁혔다.
- **글꼴은 face 목록만 번들에 싣는다.** 가상 모듈(`virtual:agent-os-widget/fonts`)이 빌드 때 글꼴 CSS 에서 뽑은 face 를 내고, 한글 글꼴의 세 굵기가 같은 글자 범위를 쓰므로 범위는 한 번씩만 싣는다. 굵기마다 실으면 목록 모듈의 글이 gzip 으로 약 71KB, 한 번씩이면 약 25KB 였다(`.scratch/web-widget/probes/font_list_size.mjs`). 번들 시험이 범위가 한 번만 실리는 것을 고정한다.
- **`document.currentScript` 가 가려지면 명세대로 위험 알림을 보인다.** `Document.prototype` 의 getter 를 직접 부르는 우회는 하지 않았다.
- **e2e 의 페이지 안 사이트 페이지는 새 파일(`e2e/element-site.ts`)에 두었다.** 07·11 도 `site.ts` 를 고칠 수 있어 `site.ts` 에는 경로 갈래 하나만 더했다. 두 e2e 파일이 함께 쓰는 도우미는 `e2e/helpers.ts` 로 옮겼다.

## 한 것

- 페이지 안 번들: `element/`(커스텀 요소 `<agent-os-widget>`, 토큰 함수, 기준 주소, 글꼴 등록, 호스트 규칙, 입구), `tools/element.ts`(IIFE 하나, 요청 글자 수 상한만 싣고 허용 출처는 싣지 않음), `next.config.ts` 의 `/element.js` ACAO `*`, 시작 래퍼의 비동기 준비, 뿌리 `.gitignore` 의 `public/element.js`.
- 단위 시험: 요소의 shadow 마운트(jsdom), 토큰 함수, 기준 주소(clobbering 사례 포함), 글꼴 등록과 호스트 규칙, 번들 빌드 설정과 실제 빌드, next 설정의 번들 헤더, 시작 래퍼의 준비 차례와 준비 실패.
- 위젯 e2e 의 페이지 안 사례 일곱(`e2e/element.e2e.ts`): 기준 주소로 최종 사용자 경로를 부름, `crossorigin="anonymous"`, `<img name="currentScript">` 로 가린 페이지, 허용 출처와 허용 밖 출처의 CORS, 사이트 CSS 의 격리와 크기, 글꼴의 출처와 ACAO, CSP `style-src 'self'`.
- 임베드 안내 `web/apps/widget/EMBED.md`. 안내가 드는 값(클레임 다섯, 수명 600초와 시계 여유 30초, RS256, `kid` 없는 헤더의 처리, 발급자의 `|` 금지, 경로, 메시지 `type` 둘과 10초, 알림 문구, 에이전트 패턴, 테마 목록)을 `src/agent_os/http/sites.py`, `src/agent_os/main.py`, `lib/token.ts`, `lib/embed.ts`, `@agent-os/ui` 의 테마 목록과 대 봤다.
- README 의 위젯 트리 줄.

## CSP `style-src 'self'` 의 결과

Chromium 에서는 막히지 않았다. `default-src 'none'` 에 `script-src`·`connect-src`·`font-src`(위젯 출처)와 `style-src 'self'`, `img-src 'self'`(파비콘) 만 연 사이트 페이지에서, 위젯의 보내기 버튼이 디자인 토큰 `--primary` 로 칠해지고 요청과 글꼴이 서며 `securitypolicyviolation` 이 하나도 없었다(위젯 e2e 의 마지막 사례). Chromium 은 shadow root 에 붙인 구성 스타일시트를 사이트의 `style-src` 로 막지 않았다. 그래서 임베드 안내의 CSP 자리에 `style-src` 를 더하지 않고, Chromium 에서는 더할 것이 없었다고 적었다. Firefox·Safari 는 재지 않았다.

## 막힌 것

- 크기 사례의 첫 실행이 빨갰다. 달라진 값은 호스트 요소 자신의 글자 속성 넷(글자 크기 10px, 줄 높이 15px, 글자 간격 3px, 낱말 간격 8px)뿐이었고, 감싼 요소·제목·입력창·버튼은 같았다. 호스트는 사이트의 light DOM 에 있어 바깥의 상속 속성을 물려받는 것이 맞고, 글자를 그리는 감싼 요소에서 디자인 토큰 CSS 가 그 값을 다시 정한다. 시험이 명세의 "위젯의 크기" 밖의 값까지 쟀던 것이라, 호스트는 상자의 크기만 보게 고쳤다. 같은 자리에서 두 페이지끼리만 견주면 `display: block` 이 빠져도 초록이라, 호스트와 감싼 요소가 사이트가 준 400×600 인지를 더 단언했다.
- `registerFonts(faces, base, add, make)` 가 타입 검사에서 `Face` 를 `unknown` 으로 정했다. 문맥으로 타입을 받는 인자는 왼쪽부터 보아 `add` 가 먼저 고정된다. `make` 를 앞으로 옮겼다.
- 요소 시험이 동기 콜백의 `act` 를 기다려 `await-thenable` 에 걸렸다. 기다리지 않게 고쳤다.

## 셀프 리뷰

`/code-review`, 기준 148652ef, 바뀐 파일 17, 미추적 22, 커밋 0. 표준 축(sonnet·high)과 명세 축 모두 Critical·Major 가 없었다. 두 축이 겹쳐 짚은 자리는 한 줄로 적는다.

고친 것:

- 임베드 안내의 공개 표면이 "속성 다섯과 `type` 둘"로 닫혀 있었다(두 축). 반례는 `tokenProvider`, 요소 이름, 번들 경로, 메시지의 `id`·`token` 이다. 사이트가 코드에 적거나 읽는 이름과 경로로 일반화하고 목록은 그 예로 두었다.
- 임베드 안내의 IP 예 `127.0.0.1` 은 픽스처 README 가 실제로 맞는다고 적은 유일한 IP 였다(두 축). 다른 사설 주소로 바꾸고, `;`·`,` 가 든 호스트는 그 뒤의 출처까지 `frame-ancestors` 에서 떨어뜨린다는 것과 포트를 앞에 0 없이 적는다는 것을 더했다.
- "`style-src`에는 더할 것이 없다"와 일지의 CSP 절이 Chromium 하나의 결과를 보편 문장으로 적었고, 시험이 `img-src 'self'` 도 연다는 것이 빠져 있었다(두 축). Chromium 에서 막지 않았다는 문장으로 좁히고 `img-src` 를 적었다.
- `async`·`defer` 문장에 shadow root 안의 script 는 `document.currentScript` 가 null 이라는 예외가 빠져 있었다(두 축). 더했다.
- `name="currentScript"` 경고가 넓었다(두 축). 이름으로 문서에 드러나는 요소가 번들 script 보다 앞에 있을 때로 좁혔다.
- 같은 에이전트 둘 금지의 까닭을 "저장하므로"라고 현재형으로 적었는데 저장은 09 의 몫이라 아직 없다(표준). 까닭을 저장이 들어온 뒤의 일로 고쳤다.
- 키 교체에서 옛 키를 내리는 때를 600초로 적었는데, 서버는 `exp` 뒤 30초까지 받고 `iat` 도 30초 앞까지 받는다(명세). 마지막으로 옛 키로 서명한 뒤 11분으로 고쳤다.
- 인라인 `tokenProvider` 예와 CSP 예를 함께 붙이면 인라인 script 가 막힌다(명세). CSP 절에 그 처리를 더했다.
- `start.ts` 머리의 "`dev`·`start` 는 손으로 봤다"와 `start.spawn.test.ts` 의 시간 주석이 번들 빌드가 앞에 서기 전의 값이었다(두 축). 지금 동작의 근거로 바꿨다.
- 근거 표기(표준): 번들 시험의 "약 46KB"와 `tools/element.ts` 의 71KB·25KB 가 세션 스크래치패드의 스크립트에 기댔다. 그 스크립트를 `.scratch/web-widget/probes/font_list_size.mjs` 로 커밋하고 다시 돌려(face 386, 범위 127, gzip 70,921·24,891바이트) 두 주석이 그 프로브를 가리키게 했다. 같은 범위가 gzip 의 창보다 멀다는 설명은 어림으로 적었다. Storybook 빌더가 `vite.config.ts` 를 읽는다는 문장에는 코드를 읽은 것이라고 적었다(`@storybook/builder-vite` 의 `dist/index.js` 1605행이 `.storybook` 의 부모를 뿌리로 `loadConfigFromFile` 을 부른다). "Vite 문서"에는 주소와 원문 구절을 붙였다(`docs/guide/build.md` 를 curl 로 받아 296행을 대 봤다).
- `WidgetSession` 의 "세션"은 `CONTEXT.md` 가 대화·실행에 피하라는 말이다(표준). `ConnectedWidget` 으로 바꿨다.
- shadow root 안의 `@font-face` 를 다룬 글꼴 주석이 가리킨 자리(디자인 토큰 CSS 머리)는 `fonts.css` 머리였고(data URL 사실은 두 머리에 다 있다), 사이트 페이지 머리의 `ELEMENT_CSP` 는 `elementCsp()` 다(표준). 고쳤다.
- `styles/widget.css` 머리가 그 파일을 싣는 쪽을 iframe 과 Storybook 둘로 적었다(명세, 잔존). 페이지 안 번들을 더했다.
- 티켓의 "글꼴 파일은 번들에 박지 않는다"를 고정하는 시험이 없었다(명세). 번들 시험에 `data:font/` 가 없다는 단언과 변이(`styles/widget.css` 에 글꼴 CSS 의 `@import`)를 더했다. 변이를 손으로 넣고 `pnpm -C web exec vitest run apps/widget/tools/element.test.ts` 를 돌려 실패 머리 `not to contain 'data:font/'` 를 본 뒤 표지로 골랐다.
- 변이 표의 `expect_output` 표지 가운데 다른 단언의 실패에도 실릴 문구(표준)를 좁혔다. e2e 의 CORS 사례는 `settled` 의 제목 기다림도 `toBeVisible() failed` 를 내므로 겨눈 글자의 `Locator:` 줄로, 가린 페이지 사례도 같은 꼴로, 사이트 문서의 시트 사례는 다른 칸의 차이에도 맥락 줄로 실리는 `"adopted": 0` 을 받은 쪽의 `+` 줄로 바꿨다. 거른 시험 안의 단언이 하나뿐인 표지는 두었다. 표의 머리에 그 기준을 적고, 프로브 README 에 표의 행과 글꼴 목록 프로브의 행을 더했다(표준).
- e2e 의 `measure(…, withWidth)` 불리언 인자와 불러온 글꼴 이름을 모으는 같은 코드 두 벌(표준, 판단 항목)을 걷었다(`measure` 는 폭을 늘 재고 제목·보내기는 부르는 쪽이 폭을 `null` 로 덮는다, `loadedFamilies`). 쓰이지 않는 `providerToken` 의 `timeoutMs` 인자(표준, 판단 항목)를 걷고 변이 표의 원문을 `TOKEN_TIMEOUT_MS` 로 맞췄다. 사이트 페이지의 `(widgetOrigin, otherOrigin)` 이 `SiteOrigins` 와 같은 Data Clump(표준, Nit)라 `elementAnswer`·`page` 가 `SiteOrigins` 를 받게 했다(`import type` 이라 실행 때 순환이 생기지 않는다).

PR 직전 리뷰에 밀 주장(반영으로 새로 쓴 사실 문장):

- `tools/element.ts`: "`@storybook/builder-vite` 가 `.storybook` 의 부모를 뿌리로 Vite 의 `loadConfigFromFile` 을 부른다", "라이브러리 빌드는 `process.env.*` 를 바꾸지 않는다(… "`process.env.*` usage are not")", "굵기마다 실으면 목록 모듈의 글이 gzip 으로 약 71KB, 한 번씩 실으면 약 25KB 였다", "같은 범위가 gzip 의 창(32KB)보다 멀리 떨어져 되풀이가 줄지 않은 것으로 어림한다".
- `tools/element.test.ts`: "범위를 굵기마다 실으면 목록이 gzip 으로 약 46KB 늘었다", "위젯의 CSS 가 글꼴 CSS 를 들이면 글꼴 파일이 모두 data URL 로 박힌다".
- `.scratch/web-widget/probes/README.md` 의 두 행과 `element_mutations.toml` 머리의 표지 기준.
- 앞 절의 `EMBED.md` 고침(11분, 포트, IP, `;`·`,`, CSP 의 인라인 script, Chromium 의 `style-src`, shadow root 안의 script, 공개 표면).

남긴 것:

- 문제 목록의 글이 같으면 console.error 를 다시 남기지 않는 차이(명세, Nit). 질의가 바뀌지 않았으면 같은 문제를 다시 알릴 까닭이 없다.
- `providerToken` 이 약속 대신 문자열을 곧바로 받아 주는 것(명세, Nit). 사이트의 실수를 너그럽게 받는 쪽이고 그 판정은 `token.ts` 머리에 적혀 있다.
- 시험을 구현과 함께 쓴 것(표준, 판단 항목). 변이 표가 각 시험의 빨강을 본다.
- 사이트 페이지의 `PageOptions` 불리언 넷(표준, Nit). 질의의 판 넷을 하나씩 그대로 옮긴 것이라 묶을 것이 없다.

다시 돌린 것:

- `pnpm -C web verify`: 종료 코드 0. 린트·Prettier·타입체크·tsconfig 검사가 지났고 vitest 는 파일 46, 시험 751 이 모두 통과했다.
- `uv run ruff check .`·`uv run ruff format --check .`: 둘 다 지났다(파이썬 파일은 바꾸지 않았다).
- `pnpm -C web/apps/widget exec playwright test`: 13 이 모두 통과했다(45.8초, iframe 사례와 페이지 안 사례 일곱).
- `pnpm -C web visual:widget`(Docker): 13 이 모두 통과했다(36.4초). 위젯의 사진 정답은 바꾸지 않았다.
- 첫 커밋의 pre-commit: 변이 표 검사 하나만 빨갰다(회고 12). 나머지(`tools/run_checks.py` 의 검사 열하나, 마크다운 표, 줄 구분 문자, 인용)는 지났다. `widget_app_mutations.toml` 의 원문 셋을 맞추고 `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/web-widget/probes/widget_app_mutations.toml 16 28 33` 으로 셋을 돌려 모두 기대대로였다.

## 회고

후보 열둘, 승인 0·넘김 0·기각 12. 대기열에 더하거나 회차를 올린 행은 없다. `tools/queue_open_rows.py` 를 작업 트리와 `--ref origin/main` 으로 돌려 만료할 행이 둘 다 없었다.

1. 도구 호출 사이의 산문을 영어로 썼다. `hook_midturn_korean` 이 압축 전 구간에서 여섯 번, 압축 뒤 셀프 리뷰를 반영하고 커밋하는 동안 다섯 번 더 알려 모두 열한 번이었고, 알린 뒤에도 같은 세션에서 다시 났다. 기각: 그 자리에서 계기 훅이 알렸다. 그 훅은 닫힌 대기열 94 의 처방이고, 이 사건은 리뷰가 잡은 지침 위반도 열린 행이 처방한 사건도 아니다. 다음 회고가 셀 수 있게 횟수를 여기 적는다.
2. 변수와 명령 치환(`$(ls …)`)이 든 Bash 명령을 워크트리 가드가 두 구간에서 거부했다. 기각: 앱 가드가 그 자리에서 막았고, `CLAUDE.md` 환경 함정이 그 모양을 이미 적는다.
3. Bash 에서 `cd web/apps/widget` 을 쳤다. 기각: 훅이 막았다.
4. `ConnectedWidget`(그때 이름 `WidgetSession`)에 `// eslint-disable-line` 을 썼다. 기각: ESLint 의 인라인 설정 끄기와 경고 0 이 잡았다.
5. `registerFonts` 의 인자 순서로 타입 추론이 빗나갔고, 색인 접근을 펼친 객체에 `as const` 를 붙였다. 기각: tsc 가 잡았다.
6. 동기 콜백의 `act` 를 기다렸다. 기각: ESLint 의 `await-thenable` 이 잡았다.
7. Prettier 형식이 어긋난 파일 여덟. 기각: `pnpm -C web verify` 가 잡았다.
8. 크기 e2e 의 첫 빨강. 기각: e2e 가 잡았다. 시험이 호스트 요소의 상속 글자 속성까지 쟀는데, 티켓이 "상속 속성은 그 감싼 요소에서 패키지 CSS가 다시 정한다"고 적어 호스트가 바깥의 값을 받는 것은 명세가 예상한 동작이다. 그래서 시험을 명세 범위로 맞춘 것으로 보고 원칙 II(시험을 고치지 않고 멈춰 보고한다)의 대상이 아니라고 판단했다. 이 판단은 사용자 보고에도 적는다.
9. 번들에 `process.` 가 남았다(React 와 openapi-fetch 의 `typeof process` 가드). 기각: 번들 시험이 잡았다.
10. 임베드 안내의 `<script>` 에 SRI 를 권하는 보안 훅 알림. 기각: 훅이 그 자리에서 알렸다.
11. 임베드 안내의 값을 원천 여러 곳(`sites.py`, `main.py`, ADR 0023, 사이트 파일 픽스처 README, 테마 목록)에서 모아 대 봤다. 기각: 틀린 값이나 헛걸음이 없었다(사건 없음).
12. 첫 커밋이 pre-commit 의 변이 표 검사(`tools/mutate.py --staged`)에 막혔다. 앞 티켓의 `widget_app_mutations.toml` 에서 이 브랜치가 옮기거나 고친 코드를 가리키던 원문 셋(`WidgetPage.tsx` 의 `console.error`, 두 번이 된 `next.config.ts` 의 ACAO 줄, `start.ts` 의 준비 부르기)이 맞지 않았다. 기각: 검사가 그 자리에서 잡았다.

## 다음

- web-widget 07(실패와 거절)과 11(실제 모델 e2e)이 나란히 돈다. 07 이 화면을 더하면 두 방식에 함께 선다(`ConnectedWidget`). 07 과 `useConversation`·`api/runs/index.ts`·`WidgetPage.tsx` 가, 11 과 `e2e/stack.ts`·`.scratch/web-widget/probes/README.md` 가 겹쳐(커밋 직전 `tools/sibling_overlap.py`) 뒤에 병합하는 쪽이 글자 충돌을 푼다.
