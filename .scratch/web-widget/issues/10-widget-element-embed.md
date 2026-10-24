# 10: 페이지 안 방식과 임베드 안내 — 사이트가 script 한 줄과 `<agent-os-widget>` 하나로 위젯을 넣고, 안내 문서만 읽고 연동한다

**What to build:** 사이트 개발자가 `<script src="https://<위젯 출처>/widget/element.js">`와 `<agent-os-widget agent="…">` 하나를 넣고 요소의 `tokenProvider`에 토큰 함수를 주면, 사이트 페이지 안에 iframe 방식과 같은 위젯이 선다. 위젯은 open 모드의 shadow root에 그려져 사이트의 CSS가 위젯을 깨지 않고 위젯의 CSS가 사이트로 새지 않으며, 사이트의 `html { font-size }`와 무관하게 크기가 같다. 글꼴은 위젯 출처에서 받아 위젯만 쓰는 이름으로 등록한다. 위젯 앱 폴더의 임베드 안내 하나가 두 방식의 태그와 속성, 서명 토큰, 허용 출처, postMessage, CSP를 적어, 사이트 개발자가 서버 코드를 읽지 않고 붙인다.

화면 컴포넌트는 iframe 방식과 같은 것을 쓴다. 이 티켓은 07~09와 나란히 갈 수 있다. 그 티켓들이 더하는 화면은 두 방식에 함께 선다.

근거는 `.scratch/web-widget/spec.md`의 "임베드"(번들의 꼴, 페이지 안 방식, 토큰을 받지 못한 경우, 잘못 준 속성, 크기, Shadow DOM, API의 기준 주소, 같은 에이전트 둘, 임베드 안내), "테마·모드·밀도·글꼴", "위젯 앱의 배치와 빌드"(경로, 스타일) 절과 Testing Decisions 1·4다. ADR 0024(한 앱 폴더에서 두 산출물, 페이지 안 번들, 사이트의 의무)와 ADR 0026과 그 이력(호스트 속성, `:host(...)`, 상속 속성)이 앞선 결정이다. 설계 인터뷰가 IIFE 번들과 shadow root 안의 Tailwind를 잰 것이 `.scratch/web-widget/probes/`의 `widget_stack/`과 `widget_tailwind/`이다(README의 2026-10-03·2026-10-04 결과).

**Blocked by:** 06 (nginx 틀과 위젯 e2e)

**Status:** ready-for-agent

### 번들

- [ ] **element 번들은 모듈이 아니라 즉시 실행되는 classic 스크립트 하나(IIFE)다.** 청크로 나뉘지 않는다. 빌드가 Next의 `public/`에 넣어 `/widget/element.js`로 나간다
- [ ] **번들 응답에도 글꼴과 같은 `Access-Control-Allow-Origin: *`를 `next.config`의 헤더로 단다.** 사이트가 `<script>`에 `crossorigin="anonymous"`를 붙이면 classic 스크립트도 CORS로 받아, 그 헤더가 없으면 번들이 실리지 않는다. 자격 증명 없는 공개 파일이라 `*`로 둔다
- [ ] **element 번들의 입력창 상한도 04의 값이다.** Vite 빌드 설정이 `web/apps/widget/tools/site-file.ts`의 `buildInput`을 불러 가장 작은 요청 글자 수 상한을 싣고, 변수가 준 파일을 읽지 못하면 빌드가 실패하는 것도 같다(fail-closed, ADR 0024). 페이지 안 방식은 postMessage를 쓰지 않아 허용 출처는 싣지 않는다. 상대 경로의 `AGENT_OS_SITE_FILE`은 시작 래퍼가 푼다(04)
- [ ] **디자인 토큰 CSS만 `?inline`으로 싣는다.** 글꼴 파일은 번들에 박지 않는다(라이브러리 모드는 `?url` 자산도 박는다)
- [ ] **API의 기준 주소는 번들 스크립트의 출처다.** 번들이 처음 실행될 때 `document.currentScript`가 `HTMLScriptElement`의 인스턴스일 때만 그 `src` 속성(property)에서 출처를 읽어 둔다. 최종 사용자 경로는 그 아래 `/end-user`다
- [ ] **인스턴스가 아니면 요청을 보내지도 토큰 함수를 부르지도 않는다.** `document`의 이름 있는 속성이 내장 속성을 가려(DOM clobbering), 사이트 페이지의 `<img name="currentScript" src="https://<다른 출처>/">`가 `document.currentScript` 자리에 설 수 있다. 그 `src`를 기준 주소로 쓰면 요청마다 서명 토큰이 그 출처로 간다. 그래서 `getAttribute("src")`나 `"src" in`으로 좁히지 않고, 인스턴스가 아니면(없음, 다른 요소, 컬렉션) 잘못 준 속성과 같은 위험 알림과 `console.error`를 남긴다(명세 "API의 기준 주소")

### 요소

- [ ] **`<agent-os-widget>`의 속성은 다섯이다**(`agent` 필수, `heading`, `intro`, `theme`, `mode`). 이름과 뜻은 03의 질의와 같다. HTML 전역 속성 `title`은 쓰지 않는다
- [ ] **서명 토큰은 요소의 속성(property) `tokenProvider`(`() => Promise<string>`)로 받고, 요청을 보낼 때마다 부른다.** 함수가 없거나, 거부되거나, 문자열이 아닌 값을 주거나, 10초 안에 답하지 않으면 요청을 보내지 않고 401과 같은 화면을 보인다
- [ ] **잘못 준 속성.** iframe 방식의 질의와 같다. `agent`가 없거나 패턴 밖이면 위험 알림과 막힌 입력창, 속성 이름을 든 `console.error`. `theme`이나 `mode`가 목록 밖이면 기본값과 `console.error`만
- [ ] **크기.** 호스트는 `display: block`이고 폭과 높이는 사이트가 정한다. 위젯은 자기 자리를 채운다
- [ ] **Shadow DOM은 `open` 모드다**

### 테마·모드·밀도·글꼴

- [ ] **`theme`과 `mode`는 호스트의 `data-theme`·`data-mode`로 옮겨 패키지 CSS의 `:host(...)`가 받는다.** 호스트에 `data-density="regular"`를 단다. 빠뜨리면 넓은 창에서 촘촘해진다
- [ ] **shadow 안의 감싼 요소가 컨테이너이고, 레이아웃의 기준 폭은 `@wide:`(360px)다.** 상속 속성은 그 감싼 요소에서 패키지 CSS가 다시 정한다
- [ ] **글꼴.** 위젯 출처의 `/widget/fonts/`에서 `FontFace`로 사이트 문서에 등록한다. family 이름은 위젯만 쓰는 고유한 이름이고, 감싼 요소에서 `--sans`·`--mono`를 그 이름으로 다시 정한다

### 임베드 안내(위젯 앱 폴더의 마크다운 하나)

- [ ] **목차.** 두 방식의 태그와 속성. 서명 토큰(RS256, 클레임 다섯 `iss`·`sub`·`aud`·`exp`·`iat`, 수명 600초 이하, 키 교체의 `kid`, `sub`는 사이트가 인증한 오래 가는 사용자 식별자여야 한다는 사이트의 의무). 허용 출처의 표기(04의 규칙. IP 호스트의 출처와 CSP의 문법 밖인 호스트(밑줄, `$`, 빈 라벨이 든 것)의 출처는 iframe 방식에서 맞지 않을 수 있어, 영문자·숫자·하이픈으로 된 호스트 이름을 쓰라고 적는다. CSP3 2026-09-16 Working Draft의 문법은 호스트 글자를 그 셋으로 두고, host-part 대조는 host가 domain이 아니면 맞지 않는다, `tests/fixtures/site_file/README.md`). postMessage에서 사이트가 지킬 것(그 iframe의 창에만, 위젯 출처를 대상으로 보낸다). 사이트의 CSP에서 열어 둘 자리(`script-src`·`connect-src`·`font-src`에 위젯 출처, iframe 방식은 `frame-src`). CSP가 글꼴을 막으면 시스템 글꼴로 그려진다는 것. 같은 에이전트를 한 페이지에 둘 두지 않는 것. 사이트가 기대는 공개 표면(속성 다섯, postMessage의 `type` 둘)을 바꿀 때는 옛 이름을 한동안 함께 받는다는 것
- [ ] 안내가 드는 값(클레임, 수명, 경로, 메시지의 `type`)이 코드와 같은지를 이 티켓을 마치기 전에 대 본다

### 시험

- [ ] **단위 시험.** shadow root에 마운트되는 것만 본다. 화면 동작은 05~09의 `widget-pages`가 light DOM에서 이미 본다
- [ ] **위젯 e2e(06의 준비 위).** 다른 출처의 사이트 페이지에서 `<script src>` 한 줄로 번들이 실리고 번들이 읽은 기준 주소로 최종 사용자 경로를 부른다. `crossorigin="anonymous"`를 붙인 `<script>`로도 실린다. 번들의 `<script>` 앞에 `<img name="currentScript" src="https://<다른 출처>/">`를 둔 페이지에서는 그 출처로 요청이 하나도 가지 않고 `tokenProvider`가 불리지 않으며 위젯이 위험 알림을 보인다. `tokenProvider`로 토큰을 넘긴다. 페이지 안 방식의 CORS는 허용 출처의 페이지에서 읽히고 허용 밖 출처에서 읽히지 않는다. 사이트의 `letter-spacing`과 `html { font-size: 10px }`가 위젯의 크기를 바꾸지 않고, 위젯의 CSS가 사이트로 새지 않으며, 호스트에 `data-density`가 있다. 글꼴이 위젯 출처에서 `Access-Control-Allow-Origin`과 함께 온다
- [ ] **CSP가 `style-src 'self'`인 사이트 페이지에서 페이지 안 위젯이 스타일을 갖는지 본다.** 막히면 임베드 안내의 CSP 자리에 `style-src`를 더하고, 이 사례는 그 자리를 열어 둔 페이지에서 스타일이 서는 것을 본다. 어느 쪽이었는지 일지에 적는다

### 검증

- [ ] `CLAUDE.md`의 검증 명령이 모두 초록이고, 위젯 e2e를 로컬에서 친다
