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

## 인계 (커밋 뒤)

커밋 `945b2931` 뒤에 세션 컨텍스트가 인계 문턱을 넘어(`hook_handoff`, 약 33만 토큰) 새 세션에 넘긴다. 이 세션의 지금 제목은 `feature/10-widget-element-embed` 이고 넘기며 `feature/10-widget-element-embed (인계함)` 으로 바꾼다. 이 절은 커밋하지 않았다. 새 세션이 이어 쓰고 커밋한다.

지시문:

```text
다음 작업: .scratch/web-widget/issues/10-widget-element-embed.md. 위젯의 요소 임베드
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/web-widget/issues/10-widget-element-embed.md
브랜치: feature/10-widget-element-embed
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-24-14-widget-element-embed.md의 "셀프 리뷰"(밀 주장 목록 포함)·"회고"·"인계" 절. 나란히 도는 티켓 .scratch/web-widget/issues/07-widget-failures-and-rejections.md, .scratch/web-widget/issues/11-widget-real-model-e2e.md
이어받을 상태: 인계: 커밋 뒤. 커밋 945b2931 에 구현, 셀프 리뷰 반영, 검증(verify, ruff 두 줄, 위젯 e2e, visual:widget), 앞 티켓 widget_app_mutations.toml 의 원문 셋 맞춤이 들었다. 아직 푸시하지 않았고 PR 도 없다. 남은 단계는 차례로 변이 전체(PYTHONUTF8=1 uv run python tools/mutate.py .scratch/web-widget/probes/element_mutations.toml, 25. e2e 변이 여덟은 하나에 1~2분)를 백그라운드로 돌려 실제 출력으로 표지를 맞추고 .scratch/web-widget/probes/README.md 의 element_mutations.toml 행 "잰 판" 칸("아직 전체를 돌리지 않았다")을 채우기, 티켓 49행 검증 줄 [x]와 Status done, 일지 마무리(이 인계 절 포함) 커밋, PR(/git-pr. PR 직전 리뷰에 일지의 "PR 직전 리뷰에 밀 주장" 목록을 넘긴다), 병합(next-session "워크트리에서 병합할 때")이다. 새 표지 가운데 셋(가린 페이지와 CORS 사례의 Locator: getByText(…) 줄, 시트 사례의 `+   "adopted": 0,`)은 변이를 손으로 넣어 출력을 보지 않고 Playwright 의 출력 꼴로 짐작해 골랐다. 일지 docs/journal/2026-10-24-14-widget-element-embed.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

제목을 바꾸고 워크트리 잠금을 풀었다(`git worktree unlock C:/project/agent/.claude/worktrees/10-widget-element-embed`, 오류 없음). 멈출 백그라운드 작업은 없었다.

open-session을 부른다 2026-10-24T13:27:38Z

## 이어받은 세션 (커밋 뒤 → 셀프 리뷰 직전)

> 사용자: /implement .scratch/web-widget/issues/10-widget-element-embed.md (위 인계 지시문 그대로. 이번 요청 범위는 PR과 병합까지)

이 세션의 처음 제목은 `feature/10-widget-element-embed` 다. 워크트리 `C:/project/agent/.claude/worktrees/10-widget-element-embed` 에 `EnterWorktree(path)` 로 들어갔다. origin/main 은 기준 148652ef 에서 움직이지 않았다.

### 차례를 바꾼 것

인계 지시문은 변이 전체 실행을 PR 직전 리뷰보다 앞에 두었지만, `tools/mutate.py` 독스트링이 "전체 실행은 셀프 리뷰와 PR 직전 리뷰(보안·버그·성능)를 반영해 커밋한 뒤에 한 번 돈다"고 정한다(대기열 265·359). 그래서 PR 직전 리뷰를 먼저 돌렸다. 변이 전체는 아직 돌리지 않았다.

### PR 직전 리뷰

`coderabbit auth status` 가 `Seat: not assigned` 라 CLI 대신 대체 둘을 나란히 돌렸다(operations.md 리뷰 파이프라인 2).

- `/security-review`(기준 148652ef, 커밋 945b2931): 신뢰도 8 이상의 High·Medium 없음. 기준 주소와 토큰이 가는 곳, 토큰 함수, 요청 경로(자격 증명 없음), React 출력, 글꼴·CSS 의 상수, `/element.js` 의 ACAO `*`, 빌드 도구를 따라갔다. 기록만 한 설계상 선택은 open shadow root(같은 페이지 스크립트는 `tokenProvider` 를 직접 부를 수 있어 `closed` 가 막지 못한다)와 번들이 두 번 실릴 때 먼저 정의한 쪽이 이기는 것이다.
- `bug-perf-review`(기준 148652ef, 범위 43, 호출 40): 유효 1, 보류 3, 오탐 5. 밀 주장(이 일지 "PR 직전 리뷰에 밀 주장")은 대 본 것이 모두 맞았다(빌더 1605행, gzip 70,921·24,891바이트와 차 46,030, 11분, 포트·`;`·`,` 문장). Vite 문서 인용과 CSP3 원문, `lib/token.ts` 의 `type` 둘은 대 보지 못했다고 적었다.

판정과 반영:

- [Major, 유효] Vite 의 `build` 가 `NODE_ENV` 를 production 으로 채우고 되돌리지 않아, 시작 래퍼가 같은 프로세스에서 이어 부르는 `next dev` 가 production 으로 선다. `vite/dist/node/chunks/node.js` 37262행(`if (!isNodeEnvSet) process.env.NODE_ENV = defaultNodeEnv;`)과 `next/dist/bin/next` 의 `preAction`(값이 있으면 그대로 두고 `dev` 에 production 이면 경고)을 열어 확인했다. 고침: `buildElement` 가 빌드 전의 값으로 되돌린다(`tools/element.ts`). 시험 "빌드는 비어 있던 NODE_ENV 를 비운 채로 둔다"를 먼저 써서 `expected 'production' to be undefined` 로 빨강을 본 뒤 고쳤다. Next 의 타입이 `NODE_ENV` 를 늘 있는 값으로 적어 ESLint `no-unnecessary-condition` 에 걸려, `process.env` 를 `Record<string, string | undefined>` 변수로 받았다(단언 없음). `next dev` 를 실제로 띄워 경고가 사라진 것은 보지 않았다.
- [Minor, 보류 → 일부 유효] `site_file_mutations.toml` 43 "래퍼가 풀어 낸 경로를 next 에 넘기지 않으면…"이 살아남을 것이라는 지적. 돌려 보니 빨갛고 표지도 맞았다. 그러나 손으로 넣어 출력을 보니 실패한 단언은 진단의 절대 경로(`사이트 파일 sites.toml 을 받아들일 수 없다` 를 받음)였고, 표지 "파일이 없다"는 실패 줄 옆에 보인 시험의 주석(`// 앱 폴더에서 풀었다면 "파일이 없다" 다.`)에서만 맞았다. 이름과 표지를 `+ 사이트 파일 sites.toml 을 받아들일 수 없다` 로 바꾸고 다시 돌려 기대대로였다(종료 0).
- [Minor, 보류 → 유효] 대화 도중 `agent` 속성이 바뀌면 앞 에이전트의 `continueFrom` 을 새 에이전트로 이어 보낸다. 서버의 이어 가기는 주체와 결말만 보고 에이전트가 같은지 보지 않는다(`core/continuation.py` 의 판정). 고침: 요소가 `ConnectedWidget` 에 `key={embed.agent ?? ""}` 를 주어 에이전트가 바뀌면 위젯 한 벌을 새로 띄운다. 시험 "agent 를 바꾸면 위젯을 새로 띄워 대화를 새로 시작하고, 다른 속성은 그 자리에서 다시 그린다"(입력창이 새 요소인지)를 먼저 써서 빨강(`not to be <textarea …>`)을 본 뒤 고쳤다. `WidgetElement.tsx` 머리 주석과 `EMBED.md` 속성 절에 한 문단씩 더했다.
- [Minor, 보류 → 그대로] `element_mutations.toml` 의 표지 셋(`AssertionError: expected`, `to be null`, `Received: undefined`). 앞의 둘은 고른 시험 안의 단언이 하나뿐이라 표 머리의 기준에 맞고, 셋째는 같은 시험의 다른 단언이 `toBeVisible` 실패라 `Received: undefined` 를 내지 않는다. 전체 실행으로 실제 출력을 본다.

이 반영으로 새로 쓴 사실 문장(셀프 리뷰와 다음 PR 직전 리뷰에 밀 주장):

- `tools/element.ts`: "Vite 의 `build` 는 `NODE_ENV` 가 비었으면 production 으로 채우고 되돌리지 않는다(vite 8.3.1 의 `resolveConfig`)", "Next 의 타입은 NODE_ENV 를 늘 있는 값으로 적는다".
- `element/WidgetElement.tsx`: "서버의 이어 가기는 앞 실행의 에이전트가 같은지 보지 않아(core/continuation.py), 그대로 두면 앞 에이전트와 나눈 대화가 새 에이전트의 실행으로 이어진다", "iframe 방식은 질의가 바뀌면 문서가 새로 뜬다".
- `EMBED.md`: "페이지 안 방식에서 속성을 바꾸면 위젯이 곧바로 다시 그린다. `agent`를 바꾸면 대화를 새로 시작하고, 앞 에이전트와 나눈 대화는 새 에이전트로 이어지지 않는다."
- `site_file_mutations.toml` 43 위 주석: "번들 빌드가 next 보다 먼저, 앱 폴더로 옮기기 전에 사이트 파일을 읽는다", "옛 표지 "파일이 없다" 는 실패 줄 옆에 보이는 시험의 주석에서만 맞았다".

다시 돌린 것: 바꾼 네 파일의 `eslint`(종료 0)와 `prettier --check`(0), `vitest --project node apps/widget/tools/element.test.ts`(7 통과), `vitest --project widget-pages apps/widget/element/WidgetElement.test.tsx`(통과), `mutate.py --check` 로 세 표(site_file 43, element 25, widget_app 34)의 원문이 모두 한 번씩 맞았다. `pnpm -C web verify`, `tools/run_checks.py`, 위젯 e2e 는 이 반영 뒤에 돌리지 않았다.

## 인계 (셀프 리뷰 직전)

PR 직전 리뷰를 반영한 변경을 커밋하기 전에 `/code-review 945b2931` 을 불렀을 때 `hook_handoff`(약 29만 토큰, 경계 `셀프 리뷰 직전`)가 와서 새 세션에 넘긴다. 셀프 리뷰는 밟지 않았다. 이 세션의 제목은 `feature/10-widget-element-embed (인계함)` 으로 바꾼다.

지시문:

```text
다음 작업: .scratch/web-widget/issues/10-widget-element-embed.md. 위젯의 요소 임베드
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/web-widget/issues/10-widget-element-embed.md
브랜치: feature/10-widget-element-embed
모델: Opus 5.5 / xhigh. 레벨 스윕의 갈래
읽을 것: docs/journal/2026-10-24-14-widget-element-embed.md의 "PR 직전 리뷰에 밀 주장"과 "이어받은 세션 (커밋 뒤 → 셀프 리뷰 직전)" 절(새 밀 주장 목록 포함). 나란히 도는 티켓 .scratch/web-widget/issues/07-widget-failures-and-rejections.md, .scratch/web-widget/issues/11-widget-real-model-e2e.md
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review 945b2931, 이 반영만)부터 한다. 변경은 PR 직전 리뷰(/security-review 지적 없음, bug-perf-review 유효 1·보류 3)의 반영이다: buildElement 의 NODE_ENV 되돌리기, agent 가 바뀌면 ConnectedWidget 을 새로 띄우는 key, site_file_mutations.toml 43 의 이름과 표지, 그리고 시험 둘과 EMBED.md 한 문단. 셀프 리뷰를 반영한 뒤 커밋하고, 그 뒤에 변이 전체(PYTHONUTF8=1 uv run python tools/mutate.py .scratch/web-widget/probes/element_mutations.toml, 25, 백그라운드)를 돌려 실제 출력으로 표지를 맞추고 .scratch/web-widget/probes/README.md 의 element_mutations.toml 행 "잰 판" 칸을 채운다. 이어서 티켓 49행 [x]와 Status done, 일지 마무리(회고 포함) 커밋, PR(/git-pr. 체크리스트의 PR 직전 리뷰 줄에 이 일지의 결과를 옮긴다. 셀프 리뷰가 시험을 고치지 않았으면 PR 직전 리뷰를 다시 돌리지 않는다), 병합(next-session "워크트리에서 병합할 때")이다. pnpm -C web verify·run_checks·위젯 e2e 는 이 반영 뒤에 돌리지 않았다. 일지 docs/journal/2026-10-24-14-widget-element-embed.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

제목을 바꿨다. 멈출 백그라운드 작업은 없었다(리뷰 서브에이전트 둘은 끝났다). 잠금 풀기는 `is not locked` 로 넘어갔다.

open-session을 부른다 2026-10-24T13:50:53Z

## 이어받은 세션 (셀프 리뷰 직전 → 병합)

> 사용자: /implement .scratch/web-widget/issues/10-widget-element-embed.md (위 인계 지시문 그대로. 이번 요청 범위는 PR과 병합까지)

이 세션의 처음 제목은 `위젯 요소 임베드 구현` 이었고 `feature/10-widget-element-embed` 로 바꿨다. 워크트리에 `EnterWorktree(path)` 로 들어갔다. origin/main 은 기준 148652ef 에서 움직이지 않았다. 나란한 07 과 11 은 둘 다 브랜치에 커밋이 있고 아직 병합되지 않았다.

### 셀프 리뷰 (PR 직전 리뷰의 반영)

`/code-review 945b2931`, 기준 945b2931, 바뀐 파일 7, 미추적 0, 커밋 0. 표준 축(sonnet·high)과 명세 축을 나란히 돌렸다. 표준 축은 Major 하나·Minor 둘·Nit 하나, 명세 축은 Minor 둘·Nit 셋이었다. 두 축 모두 밀 주장 가운데 Vite 의 `NODE_ENV`(34306행의 `"production"`, 37262행), Next 의 `preAction` 과 타입(`next/types/global.d.ts` 23행), 시작 래퍼가 같은 프로세스에서 빌드 뒤 `chdir` 하고 next 를 부르는 것, 변이 표 43 의 주석을 대 보고 맞다고 했다. 표준 축은 43 을 `mutate.py` 로 돌려 기대대로 빨간 것도 봤다.

고친 것:

- [Major·Minor, 두 축] `WidgetElement.tsx` 머리 주석의 "그대로 두면 앞 에이전트와 나눈 대화가 새 에이전트의 실행으로 이어진다"가 core 와 어긋났다. 거슬러 읽기는 지금 에이전트의 교환만 모아 새 에이전트는 앞 에이전트의 교환을 받지 않는다(`continuation.py` 모듈 독스트링 "거슬러 읽기", `tests/core/test_run.py` 의 `test_에이전트를_바꿔_쓰면_각자_자기_교환만_받는다`). 앞 세션의 PR 직전 리뷰 판정 줄("서버의 이어 가기는 주체와 결말만 보고 에이전트가 같은지 보지 않는다")은 맞았고, 주석으로 옮기며 뒤 절반을 덧붙인 것이 틀렸다. `key` 를 다는 까닭을 화면과 상태의 어긋남으로 고쳤다: 화면의 대화와 이어 갈 실행은 위젯 한 벌(`useConversation` 의 `useReducer`)이 들어, 그대로 두면 새 에이전트 아래에 앞 대화가 보이고 다음 요청이 앞 에이전트의 실행을 이어 가는데 새 에이전트는 그 대화를 받지 못한다.
- [Minor, 두 축] `EMBED.md` 의 "iframe 방식에서 질의를 바꾸면 위젯 페이지가 새로 뜨는 것과 같다"는 `agent` 에만 맞았다. iframe 은 질의의 어느 값을 바꾸든 새로 뜨고 페이지 안 방식은 `agent` 밖의 속성에서 대화를 둔다. 명세 축은 "대화를 새로 시작"이 09 의 저장(키가 에이전트)이 들어오면 거짓이 된다고도 짚었다. 문단을 "속성을 바꾸면 그 자리에서 다시 그리고 대화는 그대로 둔다. `agent` 만 다르다. `agent` 를 바꾸면 위젯을 새로 띄워, 앞 에이전트와 나눈 대화를 새 에이전트 아래에 두지도 이어 가지도 않는다. iframe 방식은 질의의 어느 값을 바꾸든 위젯 페이지가 새로 뜬다"로 고쳤다. 저장이 들어와도 앞 에이전트의 대화를 새 에이전트 아래에 두지 않는 것은 그대로라 09 에 넘길 것은 없다.
- [Minor, 표준] 시험 주석 "jsdom 의 shadow root 에서는 글을 넣을 수 없어"가 넓었다. ADR 0024 의 근거는 user-event 로 친 글자가 React 의 `onChange` 에 닿지 않았고 `fireEvent.input` 은 닿았다는 것이다. user-event 로 좁혔다(주석만, 시험의 동작은 그대로).

남긴 것:

- [Nit, 명세] 시험 이름의 "다른 속성"과 달리 바꾸는 것은 `heading`·`theme` 둘이다. `key` 가 `embed.agent` 하나만 보므로 둘로 그 자리 다시 그리기를 보면 되고, 속성마다의 다시 그리기는 앞 시험 "호스트에 테마와 모드와 보통 밀도가 달리고, 속성을 바꾸면 다시 그린다"가 본다.
- [Nit, 명세] 사이트가 응답 도중 `agent` 를 바꾸면 "새 대화"의 막힘이 걸리지 않고 그 응답이 끊긴다. 사이트가 속성을 바꾸는 때는 사이트의 몫이고, iframe 방식에서 질의를 바꿔 문서가 새로 뜰 때와 같다.
- [Nit, 명세] 새로 띄운 위젯은 그대로인 `theme`·`mode`·기준 주소 문제를 `console.error` 로 다시 남긴다. 새로 띄운 한 벌의 첫 그리기이고 iframe 문서가 새로 뜰 때와 같다. `ConnectedWidget.tsx` 머리의 "다시 그려도 글이 같으면 다시 남기지 않는다"는 같은 한 벌의 다시 그리기를 말한다.
- [Nit, 명세] `agent` 를 바꾸면 대화를 새로 띄우는 것이 명세에 없는 새 약속이라는 지적. 티켓의 "이름과 뜻은 03의 질의와 같다"와 iframe 의 질의 바꾸기가 그 뜻이라 명세를 고치지 않는다.
- [Nit, 표준] `process.env` 를 넓은 타입으로 받는 줄이 구현과 시험에 한 벌씩이다(Duplicated Code). 시험 쪽은 그 시험의 준비이고 구현의 도우미에 기대게 하지 않는다.

이 반영으로 새로 쓴 사실 문장(PR 봇에 밀 주장):

- `element/WidgetElement.tsx`: "화면의 대화와 이어 갈 실행은 위젯 한 벌(useConversation)이 들어, 그대로 두면 새 에이전트 아래에 앞 에이전트와 나눈 대화가 보이고 다음 요청이 앞 에이전트의 실행을 이어 간다", "서버의 이어 가기는 앞 실행의 에이전트가 같은지 보지 않고 지금 에이전트의 교환만 모아(core/continuation.py), 새 에이전트는 화면에 보인 그 대화를 받지 못한다".
- `element/WidgetElement.test.tsx`: "jsdom 의 shadow root 에서는 user-event 로 친 글자가 React 의 onChange 에 닿지 않아(ADR 0024)".
- `EMBED.md`: "페이지 안 방식에서 속성을 바꾸면 위젯이 그 자리에서 다시 그리고 대화는 그대로 둔다. `agent`만 다르다. `agent`를 바꾸면 위젯을 새로 띄워, 앞 에이전트와 나눈 대화를 새 에이전트 아래에 두지도 이어 가지도 않는다. iframe 방식은 질의의 어느 값을 바꾸든 위젯 페이지가 새로 뜬다."

셀프 리뷰가 시험의 동작을 고치지 않아(주석 한 줄만) PR 직전 리뷰는 다시 돌리지 않는다.

다시 돌린 것:

- 바꾼 파일의 `prettier --check`(0), `eslint`(0), `vitest --project widget-pages apps/widget/element/WidgetElement.test.tsx`(7 통과).
- 커밋의 pre-commit 첫 번: `web-verify`(312.9초)를 포함한 검사 열하나 가운데 pytest 하나만 빨갰다(587.7초, 5585 통과 1 실패). 실패는 `tests/adapters/test_filesystem.py::test_다른_스레드가_운영자_파일을_연_채여도_교체가_재시도_안에서_성공한다` 의 `PermissionError`(WinError 5)였고 따로 돌리면 1.26초에 지났다. 이 커밋은 파이썬을 바꾸지 않았고, 대기열 306 이 받아들여 닫은 종류(전체 스위트의 부하 아래에서만 빨간 시간 시험)라 회차를 더하지 않고 여기에만 적고 커밋을 다시 쳤다.

## 다음

- web-widget 07(실패와 거절)과 11(실제 모델 e2e)이 나란히 돈다. 07 이 화면을 더하면 두 방식에 함께 선다(`ConnectedWidget`). 07 과 `useConversation`·`api/runs/index.ts`·`WidgetPage.tsx` 가, 11 과 `e2e/stack.ts`·`.scratch/web-widget/probes/README.md` 가 겹쳐(커밋 직전 `tools/sibling_overlap.py`) 뒤에 병합하는 쪽이 글자 충돌을 푼다.
