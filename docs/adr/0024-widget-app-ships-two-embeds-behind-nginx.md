---
status: accepted
date: 2026-10-03
---

# 위젯은 한 앱 폴더에서 iframe 페이지와 페이지 안 번들을 내고 nginx 뒤에 선다

`plan.md`는 위젯의 기술을 "실측으로 결정"하라고 넘겼고, 킥오프 일지는 "Vite 라이브러리 빌드 vs Next.js iframe"을 슬라이스 4로 미뤘다. ADR 0021은 공유 atoms(`packages/ui`)와 Storybook을 위젯에서 다시 보라고 넘겼는데, 같은 인터뷰가 두 앱이 디자인 시스템 하나를 나누기로 해서(ADR 0025) 그 둘은 design-system 기능으로 갔다(ADR 0021 이력 2026-10-03). **`web/apps/widget`은 같은 React 19 컴포넌트로 두 산출물을 낸다. Next 16 앱은 iframe 방식의 페이지를 내고, Vite 라이브러리 빌드는 사이트 페이지 안에 Shadow DOM 커스텀 요소로 그리는 번들을 낸다. 둘 다 nginx 뒤의 한 출처에서 서빙되고, nginx는 최종 사용자 접두사를 파이썬에 바로, 위젯 페이지를 Next에 넘기며 나머지를 404로 막는다. nginx 설정은 저장소 뿌리의 `deploy/nginx/`에 두고 CI의 e2e가 실제 nginx로 판정한다. 스타일은 Tailwind이고 토큰과 핵심 컴포넌트는 design-system 기능이 코드로 만든 것을 쓴다. 아이콘은 lucide-react 서브패스다. 화면은 명세 직전에 Claude Design에서 그 디자인 시스템으로 그려 저장소에 내보낸다.** React를 고른 이유는 Next 페이지와 element 번들이 같은 컴포넌트와 테스트 도구를 그대로 나누기 때문이다. 대가는 element 번들의 크기다. 같은 위젯을 실제로 설치한 워크스페이스 사본에서 쟀더니 React는 약 71.5KB gzip이었고 Preact와 Lit는 약 10KB였다(`.scratch/web-widget/probes/widget_stack/`). 그 차이는 사이트 쪽의 편의이고, PRD의 우선순위(실행 가능성 > 계약의 안정성 > 확장성 > 편의)에서 마지막이다. nginx가 최종 사용자 접두사를 파이썬에 바로 넘기는 이유는, 침묵 한계가 Next 중계의 30초가 아니라 nginx의 60초이고 홉이 하나 적기 때문이다(`.scratch/web-widget/probes/nginx_relay/`).

## Considered Options

- **Preact 11.** element 번들이 약 9.7KB gzip이고 워크스페이스 판정을 모두 지났다. 그러나 11.0.0은 2026-09-30에 나온 판이고, Next 앱과 한 폴더에 두면 Preact 파일마다 jsx 프라그마가 필요하다. 거부했다.
- **Lit 3.** 약 9.6KB gzip이다. 표준 데코레이터는 Vite와 Vitest에서 변환되지 않고, Next(SWC)는 `AutoAccessor`에서 빌드가 실패했다. 레거시 데코레이터는 Next 빌드에서 반응 속성이 클래스 필드에 가려져 갱신이 그려지지 않았다. 데코레이터 없이는 동작하지만 컴포넌트 모델이 React와 달라 관리 화면과 나눌 것이 없다. 거부했다.
- **프레임워크 없음.** 약 4.3KB gzip으로 가장 작다. 그러나 승인 화면, 재접속, 대화 상태를 DOM 위에 손으로 관리한다. 거부했다.
- **공유 컴포넌트를 `packages/widget-ui`로 뺀다.** 판정을 지났고 크기도 같다. 그러나 소비자가 하나인 패키지가 생기고, 용어집이 앱을 "따로 배포되는 단위"로 정의한 것과 위젯이 일대일로 맞지 않는다. 거부했다. element 번들을 별도 앱으로 두고 위젯 앱을 import하는 모양은 ESLint의 "앱 사이에서 import 하지 않는다" 규칙에 막혔다.
- **정적 파일을 nginx가 서빙한다(Next 없음).** 바깥에 Node 서버가 서지 않는다. 고르지 않았다. iframe 페이지를 관리 화면과 같은 Next 스택으로 두는 쪽을 골랐다. 파이썬이 정적 파일까지 서빙하는 안은 파이썬 서버가 web 빌드 산출물을 알게 되어 거부했다.
- **nginx가 최종 사용자 접두사를 Next를 거쳐 넘긴다.** 관리 화면과 모양이 같다. 그러나 침묵 한계가 30초로 짧아지고 홉이 하나 는다. Next가 죽으면 API도 막힌다. 거부했다.
- **Caddy, 또는 특정 프록시를 고르지 않는다.** Caddy는 인증서를 스스로 받고 갱신한다. 고르지 않았다. 프록시를 고르지 않으면 경로 허용 목록을 실제로 판정할 길이 없다. 거부했다.
- **nginx 설정을 pytest가 글로 읽어 판정한다.** nginx 없이 어디서나 돈다. 그러나 nginx의 실제 경로 정규화를 재지 못하고, 설정 문법을 정규식으로 읽게 된다. 거부했다.
- **frame-ancestors를 Next 시작 래퍼가 넘긴 값으로 낸다.** 인터뷰에서 처음 고른 안이다. 그러나 `next.config`의 헤더는 빌드 때 박혀서 `next start`에 넘긴 값은 반영되지 않는다. PR #128의 리뷰가 찾았고, 사이트 파일을 빌드의 입력으로 삼는 쪽으로 바꿨다.
- **frame-ancestors를 nginx가 사이트 파일에서 생성한 include로 낸다.** 위젯을 다시 빌드하지 않고 nginx를 다시 읽으면 바뀐다. 그러나 생성 단계가 하나 늘고 nginx 설정이 생성물에 기댄다. 거부했다. 헤더만 내는 Next proxy를 ADR 0019의 서버 파일 금지에서 예외로 두는 안은, 금지한 서버 파일이 생겨 거부했다.
- **직접 쓴 CSS 하나.** 새 의존성이 없다. 고르지 않았다. ADR 0021이 적은 스택(Tailwind)을 따른다.
- **아이콘을 들이지 않거나 인라인 SVG를 쓴다.** 의존성이 늘지 않는다. 고르지 않았다. ADR 0021이 적은 lucide-react를 따른다.

## Consequences

- **임베드의 모양.**
  - 사이트는 script 한 줄로 커스텀 요소를 넣거나 iframe 태그를 넣는다.
  - 서명 토큰은 사이트가 준 손잡이로 요청할 때마다 새로 받는다. 페이지 안 방식은 사이트가 넘긴 함수이고, iframe 방식은 postMessage다. 토큰은 요청을 시작할 때만 검증되므로 열린 스트림은 만료와 무관하게 이어진다.
  - iframe 방식의 postMessage는 양쪽이 규약을 지킨다. 위젯은 `event.source`가 `window.parent`이고 출처가 허용 출처일 때만 받는다. 사이트(부모)는 토큰을 그 위젯 iframe의 창에만, 위젯 출처를 대상으로 지정해 보낸다. 같은 페이지의 다른 프레임(광고, 제3자 임베드)이 토큰을 요청해 받아 가는 길을 막기 위해서다. 사이트 쪽의 규약은 임베드 안내에 적는다.
  - 쿠키는 쓰지 않는다. 그래서 ADR 0019가 남긴 쿠키와 DNS rebinding의 물음이 여기에는 생기지 않는다.
  - 화면의 교환과, 이어 갈 마지막으로 끝난 실행과, 다시 붙을 실행(돌고 있거나 멈춘 것)의 run_id를 sessionStorage에 둔다. 이어 갈 수 있는 것은 끝난 실행뿐이다(ADR 0022). 저장은 토큰의 발급자와 `sub`에 묶는다. 둘이 바뀌거나 이어 가기와 구독이 404를 받으면 저장을 지우고 새 대화로 시작한다. 같은 탭에서 사이트 계정이 바뀌었을 때 앞 사용자의 교환이 화면에 남지 않게 하기 위해서다. 같은 탭에서 새로 고치면 대화를 이어 가고, 다시 붙을 실행에는 구독으로 붙어 승인 묻기도 다시 세운다(ADR 0023). 탭을 닫으면 새 대화다.
  - 모델이 지은 출력과 일시정지의 인자는 텍스트로 그린다. 마크다운을 그리게 되면 원시 HTML을 끈 렌더러만 쓴다. 페이지 안 방식에서 위젯은 사이트의 출처에서 돌고, Shadow DOM은 스크립트의 경계가 아니기 때문이다. `dangerouslySetInnerHTML`은 이미 워크스페이스의 ESLint가 막는다. e2e가 HTML 조각이 든 출력을 그려 실행되지 않는지 본다.
- **iframe 페이지의 출처 검사.** iframe 페이지는 CSP `frame-ancestors`를 사이트 파일의 허용 출처로 내고, postMessage도 그 출처에서 온 것만 받는다. 남의 페이지가 승인 버튼을 품어 클릭을 가로채는 길을 막는다.
  - **허용 출처는 위젯 빌드의 입력이다.** 헤더는 `next.config`가 내는데, Next는 운영 모드에서 그 값을 빌드 산출물(`routes-manifest.json`)에서 읽는다. 관리 화면의 `next.config.ts` 주석이 rewrites에 대해 같은 사실을 적었고, Next 16.3.6의 코드도 그렇다(PR #128의 리뷰가 코드를 읽었다). 그래서 빌드도 래퍼를 지나 사이트 파일(ADR 0023)을 읽고, 페이지가 postMessage를 거르는 데 쓰는 목록도 같은 빌드에서 들어간다.
  - 사이트 파일을 바꾸면 위젯을 다시 빌드하고 `serve`를 다시 시작한다. 빌드 때 사이트 파일이 없으면 `frame-ancestors 'none'`을 내어 어떤 사이트도 품지 못한다(fail-closed).
  - e2e가 빌드된 앱의 응답 헤더를 판정한다. 허용 출처의 표기(스킴, 호스트, 포트, 와일드카드 금지)는 파이썬(CORS)과 Node(CSP)가 같은 픽스처로 판정한다. 두 언어가 같은 파일을 따로 읽기 때문이다.
  - Node에 TOML 파서 의존성이 하나 늘고, 그 판은 티켓이 잰다. 워크스페이스는 Next의 서버 파일을 금지하므로 헤더는 `next.config`가 낸다.
- **Next는 루프백에만 선다.** 위젯의 Next도 관리 화면과 같은 모양의 시작 래퍼를 거친다(ADR 0011 이력 2026-09-28). 관리 화면의 래퍼는 그 앱 안에 있어서 위젯이 import하면 앱 사이 import 규칙에 걸린다. 공유 자리로 옮길지 위젯이 자기 래퍼를 둘지는 티켓이 정한다. API를 부르는 서버 코드를 두지 않는다는 ADR 0019의 규칙은 ESLint 판정 그대로 위젯에도 걸린다. 위젯의 `next.config`에는 rewrites를 두지 않는다. API는 nginx가 파이썬에 바로 넘기므로, 처음 바깥에 열리는 Next가 중계가 되지 않게 하기 위해서다. 설정 테스트가 판정한다.
- **배치.** Vite의 입구는 `app/` 밖에 둔다. `app/`의 import 정책은 Next 전용이다. element 번들은 Vite 빌드가 Next의 `public/` 아래로 내고, Next가 위젯 페이지와 같은 출처와 경로 아래에서 내준다. 그래서 nginx가 넘기는 위젯 경로 하나에 둘 다 든다. 빌드 산출물이 린트와 포맷 범위에 들지 않게 무시 규칙을 그 자리에 묶어 둔다. 뿌리 `.gitignore`의 `/dist/`는 앱 안의 자리를 빼지 못하고, 맨 `dist/` 패턴은 `eslint.config.test.ts`의 단언과 부딪힌다. `vitest.config.ts`에 위젯의 jsdom 프로젝트를 더한다. 모든 후보가 Vite를 선언하면서 워크스페이스의 vite가 8.3.1에서 8.3.2로 올랐다. 고정할지는 티켓이 정한다.
- **테스트.** jsdom의 shadow root 안에서는 user-event로 친 글자가 React 19의 `onChange`에 닿지 않았다. `fireEvent.input`은 닿았고 실제 chromium에서는 동작했다. 그래서 동작 테스트는 컴포넌트를 light DOM에 그려서 하고, shadow root는 마운트만 단위 테스트가 본다. 실제 shadow 동작은 e2e가 본다.
- **Shadow DOM의 격리.** 사이트의 CSS는 대부분 막혔지만, 호스트 태그를 겨냥한 규칙(`agent-os-widget{letter-spacing:5px}`)과 body의 `letter-spacing`은 안으로 상속됐다. 위젯은 `:host`에서 상속 속성을 다시 정한다.
- **api-client.** 위젯 클라이언트를 `packages/api-client`에 더한다. 기준 주소를 인자로 받고 최종 사용자 경로만 안다. 지금의 채널 클라이언트는 기준 주소가 같은 출처의 `/api`로 고정되어 있고 `POST /runs`를 모른다. 최종 사용자 항목은 판별자 술어로 좁힌다(ADR 0021). `readFrames`의 프레임 크기 상한은 두지 않는다. 위젯의 상류는 nginx와 TLS를 지나도 운영자의 서버다. web-admin이 넘긴 (7)은 제3자의 상류를 읽게 되는 날 다시 본다.
- **nginx.**
  - 바깥을 향해 평문으로 토큰을 받지 않는다. 443은 TLS로만 듣고 HSTS를 낸다. 평문 80은 인증서 발급의 확인 경로(ACME HTTP-01, `/.well-known/acme-challenge/`)와 HTTPS로 넘기는 것만 하고, 안으로는 아무것도 넘기지 않는다. 위젯은 언제나 `https` 기준 주소로만 부른다. 그래서 위젯이 보낸 토큰이 평문으로 나가는 길은 없다(ADR 0011 이력 2026-10-03의 CWE-319 논증이 여기에 기댄다). 다만 리다이렉트는 잘못 설정된 클라이언트가 이미 평문으로 보낸 토큰을 되돌리지 못한다. HSTS가 두 번째 요청부터 그것을 막는다. e2e가 80과 443의 동작을 판정한다. 측정의 설정에는 비교를 위한 평문 포트가 있었다.
  - `location`으로 최종 사용자 접두사는 파이썬에, 위젯 경로는 Next에 넘기고, 나머지는 `return 404`로 막는다. 측정에서 쓴 이름(`/chat`, `/widget`)으로 `..`, 퍼센트 인코딩, `/chatx`처럼 접두사 안에서 밖으로 나가는 우회를 막는 것을 쟀고, 어긋난 것은 아래의 대소문자 하나였다. 실제 이름은 계약 티켓이 짓는다.
  - **넘기는 URI는 nginx가 정규화한 것이다.** `proxy_pass`에 URI를 붙이지 않으면 nginx는 정규화한 경로로 `location`을 고르고 상류에는 받은 원문을 넘긴다. 그러면 `/runs/../chat/x`처럼 밖에서 출발해 정규화하면 접두사 안이 되는 경로가 통과하고, 파이썬은 `/runs/…`를 보고 운영자 토큰을 판정하게 된다. 그래서 `proxy_pass`에 URI를 붙여 정규화된 경로를 넘긴다. e2e의 허용 목록에는 밖에서 안으로 들어오는 사례를 더하고, 파이썬이 접두사 밖 경로를 받지 않는지 판정한다. PR #128의 리뷰가 찾았다.
  - nginx는 `X-Forwarded-For`와 `X-Forwarded-Proto`를 받은 값에 덧붙이지 않고 덮어써 넘긴다. 파이썬은 클라이언트 IP를 어떤 판정에도 쓰지 않는다. 상한은 주체로 센다(ADR 0023).
  - 본문 크기 상한(`client_max_body_size`)은 사이트 파일의 요청 크기보다 크게 두어 파이썬의 422가 답하게 한다(ADR 0023).
  - Next의 `basePath` 아래에서 위젯 경로의 끝 슬래시를 두고 nginx와 Next가 서로 되돌려 보내는 리다이렉트 고리가 생긴다. 끝 슬래시 없는 경로를 정확히 맞추는 `location =`을 두어 푼다.
  - `proxy_http_version 1.1`을 명시한다. 잰 판 가운데 1.24.0과 1.28.3은 기본 설정에서 파이썬이 응답 도중 죽어도 클라이언트에게 정상 종료로 보였고, 1.30.5는 잘림이 드러났다. nginx의 CHANGES를 읽으면 1.29.7에서 상류의 기본 HTTP 판이 1.0에서 1.1로 바뀌었다.
  - SSE는 FastAPI가 붙이는 `X-Accel-Buffering: no` 덕분에 기본 설정에서도 흘렀다. keepalive(FastAPI 기본 15초)가 nginx의 `proxy_read_timeout`(기본 60초)을 덮는다. 둘은 짝이다.
  - Windows의 nginx는 `location`을 대소문자 없이 맞춰 `/CHAT/x`가 파이썬까지 갔다. 운영과 CI는 Linux이고, 그곳에서 막히는 것은 e2e가 판정한다. 그 사례는 Linux에서만 도는 판정으로 두어, 이 저장소의 개발 기계(Windows)에서 로컬 e2e가 그 사례 하나로 빨개지지 않게 한다.
  - TLS 인증서는 운영자가 마련한다(ADR 0011 이력 2026-10-03).
- **nginx의 판정.** CI의 e2e가 러너에 깔린 nginx로 설정을 띄워 허용 목록과 SSE 흐름을 재고, 필수 검사 `verify`가 그 결과를 모은다. 러너의 nginx는 ubuntu-24.04가 1.24.0이고, `ubuntu-latest`가 2026년 11월에 26.04로 바뀌면 1.28.3이다(`actions/runner-images`의 이미지 README와 공지를 읽었다). 두 판이 모두 받는 문법(`listen … ssl http2`)으로 쓴다. 로컬에서 돌리려면 nginx가 필요하고, 관리 화면 e2e처럼 해당 파일을 건드렸을 때 친다.
- **스타일.** Tailwind v4(4.3.3으로 쟀다)를 쓴다. Tailwind는 design-system이 토큰과 함께 처음 들이고(ADR 0025, 기능 순서는 `plan.md`), 위젯은 그것을 쓴다. 측정은 위젯의 모양으로 했다. 관리 화면에는 아직 없고 admin-style이 들인다(ADR 0021 이력 2026-10-03). 아래는 `.scratch/web-widget/probes/widget_tailwind/`가 잰 것이다.
  - **shadow root에서는 그대로 넣으면 깨진다.** `@property` 등록은 문서 단위라 shadow root 안에서는 되지 않는다. 손대지 않은 CSS는 light DOM과 비교한 58곳(유틸리티 표본과 부모 값이 새는 사례, 의사 요소) 중 31곳이 다르게 그려졌다(테두리, 그림자, ring, outline, 한 축 변형, gradient). `:host`에 `@property`의 초기값을 두면 8곳, 대체 블록의 값을 두면 4곳이 남았다(부모의 값이 자식에게 샌다). Tailwind가 생성 CSS에 넣어 두는 대체 블록의 선언을 `@layer properties { *, ::before, ::after, ::backdrop {…} }`로 다시 넣으면 58곳이 라이트와 다크에서 모두 같았다. 층 밖에 두면 유틸리티를 이겨 33곳이 달라진다. 문서에 `@property`를 등록하는 길은 사이트 문서로 값이 샌다.
  - CSS 원본 하나를 element는 `?inline` 문자열로 `adoptedStyleSheets`에, Next 페이지는 전역 import로 쓴다. 세 산출물의 유틸리티, `@property`, 테마 변수 집합이 같았다. 전역 CSS를 `app/layout.tsx`에서 import하면 층 경계 규칙이 막으므로 `components/pages`에서 import한다. `?inline`을 위한 모듈 선언이나 tsconfig의 `vite/client`가 필요하다.
  - element 번들은 Tailwind와 아이콘 둘로 약 4.9KB gzip이 늘어 약 76.4KB다.
  - Vitest는 기본 설정에서 `?inline`을 빈 문자열로 주고 CSS를 넣지 않는다. jsdom은 `@property`를 버린다. 그래서 스타일은 단위 테스트가 아니라 e2e가 본다. 설정을 바꾸는 길은 처리되지 않은 원본이 jsdom에서 파싱 에러를 내서 택하지 않는다.
  - **rem이 사이트를 따라간다.** 사이트에 `html { font-size: 10px }`가 있으면 페이지 안 위젯이 따라 줄었다(폭 320px이 200px, 글자 14px이 8.75px). iframe은 영향이 없다. 단위는 design-system이 정한다.
  - 새로 드는 일반 패키지는 15개이고(프로브 README), 네이티브 바이너리(oxide, lightningcss)는 설치 스크립트 없이 들어온다. lightningcss가 두 판이 된다. Linux 바이너리는 WSL에서 링크만 확인했고 CI가 첫 실제 로드다.
- **아이콘.** lucide-react를 서브패스로 import한다. 1.51.0에도 `exports` 맵이 없다. 서브패스는 `lucide-react/dist/esm/icons/<이름>`이고 Vite와 Next 둘 다 빌드됐다. 아이콘별 타입 선언이 없어서 `declare module "lucide-react/dist/esm/icons/*"`를 손으로 두고 타입은 `import("lucide-react")`의 `LucideIcon`으로 준다. 이 선언은 경로와 타입의 대응을 TypeScript가 검증하지 않는다. 루트 import는 ESLint가 막고 서브패스는 지난다. 아이콘 둘이 약 1.4KB gzip이다. 아이콘은 design-system이 핵심 컴포넌트와 함께 처음 들이고(ADR 0025), 그 티켓이 이것을 따른다. web-admin이 넘긴 (8)이 이것으로 닫힌다.
  - **공급망 유예를 풀지 않는다.** 측정 때는 나온 지 하루가 안 된 판이라 pnpm 11이 `pnpm-workspace.yaml`에 `minimumReleaseAgeExclude`를 스스로 썼다. 티켓은 그 예외를 들이지 않고, 유예를 지난 판을 쓴다.
- **화면.** 위젯의 화면(대화, 승인 묻기, 실패, 재접속 중, 상한에 걸림)은 web-widget의 명세 직전에 Claude Design에서 design-system의 디자인 시스템으로 Wireframe과 UI mockups로 그리고, `.scratch/web-widget/design/`에 내보내 근거 문서(이때는 ADR과 `plan.md`의 행)와 기준 커밋을 함께 적는다(ADR 0025).
- **`tech.md`.** 웹 행과 프론트 구성 행을 이 결정에 맞추고, 배치 행에 nginx를 더한다.
