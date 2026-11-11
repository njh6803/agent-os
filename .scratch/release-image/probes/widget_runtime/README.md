# release-image widget_runtime 프로브

`release-image` 설계 인터뷰에서 "위젯을 한 번만 빌드하고, 빌드 때 굽던 값을 시작할 때(또는 요청 때)의 사이트 파일에서 읽는다"는 선택지가 되는지와 치르는 값을 본 프로브다. 위젯(`web/apps/widget`, Next 16.3.6)의 지금 빌드는 사이트 파일(`AGENT_OS_SITE_FILE`)의 허용 출처와 요청 글자 수 상한을 산출물에 굽는다. 여기서는 결정하지 않고 본 것만 적는다. 반영할 코드도 아니다. 규약은 `docs/agents/issue-tracker.md`의 "프로브와 근거"다.

근거의 종류. 아래 "결과"의 줄은 따로 적지 않은 한 `measure.mjs`(이 폴더)가 다시 내는 것이고, 2026-11-11에 돌린 출력(결과 JSON)에서 옮겼다. 결과로 옮긴 실행에는 표지를 보지 못한 회차가 없었다(단계마다 종료 코드 0). 손으로 본 것은 그 명령과 함께, 코드를 읽은 것은 파일과 줄과 함께, 재지 않은 것은 어림이라고 적었다.

시간은 범위로 읽는다. 이 PC에서 다른 세션이 여럿 함께 돌던 때다. 같은 고친 코드의 빌드가 13.8초에서 38.4초까지 흔들렸다. 한 값을 문턱으로 쓰지 않는다.

## 파일

| 파일 | 무엇 |
|---|---|
| `measure.mjs` | 측정 전체. 단계마다 무엇을 표지로 보는지는 독스트링과 단계 함수의 주석에 있다 |
| `element_build.mjs` | `element.js` 하나를 따로 짓는 도우미. `measure.mjs`가 띄운다 |
| `runtime.patch` | 실험으로 고친 추적 파일의 diff(`web/` 아래 파일 10개, 129줄 더하고 45줄 뺐다). 새 파일 둘(`proxy.ts`, `app/config/route.ts`)도 들어 있다 |
| `sites_b.toml` | 둘째 사이트 파일. 선례 `widget_build/`의 것을 복사했다. 허용 출처 둘(`https://probe-b.example`, `https://www.probe-b.example:8443`)과 글자 수 상한 583927 |
| `sites_sentinel.toml` | `sites_b.toml`에서 글자 수 상한만 자리표 918273645로 바꾼 것. `element` 단계가 쓴다 |

첫째 사이트 파일(A)은 저장소의 픽스처 `tests/fixtures/site_file/sites.toml`이다(허용 출처 셋 `https://shop.example`, `https://www.shop.example`, `http://localhost:3000`, 글자 수 상한 4000). 아래에서 "없음"은 `AGENT_OS_SITE_FILE`을 주지 않은 것이고(허용 출처 없음, 상한 20000), "없는 파일"은 그 변수가 없는 경로를 가리키는 것이다.

## 실험 판(`runtime.patch`)이 고친 것

파일마다 머리에 `[프로브 판]`이라고 적었다. 프로브 전용 환경 변수 넷(`AGENT_OS_PROBE_*`)은 갈래를 가르려고 넣은 것이다.

| 파일 | 고친 것 |
|---|---|
| `next.config.ts` | 설정의 `env`와, 헤더에 싣던 사이트 파일의 값을 뺐다. 설정을 읽을 때 `buildInput(process.env)`를 한 번 불러 사이트 파일을 검사만 한다. 모든 경로(`/:path*`)에 바닥값 `frame-ancestors 'none'`을 싣는다(`AGENT_OS_PROBE_CONFIG_CSP=off`면 싣지 않는다). `AGENT_OS_PROBE_OUTPUT=standalone`이면 `output: "standalone"`과 `outputFileTracingRoot`를 더한다 |
| `proxy.ts`(새 파일) | 요청마다 `buildInput(process.env)`로 허용 출처를 읽어 응답에 `Content-Security-Policy: frame-ancestors …`를 단다. `matcher`는 `["/"]`이다(basePath가 붙어 `/widget`) |
| `app/page.tsx` | 서버 컴포넌트가 `await connection()` 뒤에 `buildInput(process.env)`를 불러 두 값을 `WidgetPage`에 props로 넘긴다. `AGENT_OS_PROBE_STATIC_PAGE=1`로 빌드하면 `connection()`을 부르지 않는다 |
| `app/config/route.ts`(새 파일) | `GET /widget/config`. `await connection()` 뒤에 `{ requestChars }`를 JSON으로 내고 `Access-Control-Allow-Origin: *`를 단다 |
| `components/pages/WidgetPage.tsx`, `ConnectedWidget.tsx` | 두 값을 `lib/build`(번들에 박힌 값)에서 읽지 않고 props로 받는다 |
| `element/WidgetElement.tsx` | 페이지 안 방식은 지금처럼 번들에 박힌 값(`requestCharLimit()`)을 `ConnectedWidget`에 넘긴다 |
| `tools/start.ts` | `start`일 때 next를 띄우기 전에 `buildElement(process.env)`로 `public/element.js`를 다시 짓는다(`AGENT_OS_PROBE_START_ELEMENT=0`이면 짓지 않는다). 글꼴은 다시 복사하지 않는다 |
| `testing/widget.tsx`, `components/pages/WidgetPage.test.tsx` | `<WidgetPage />`를 부르는 세 자리에 props를 줬다. `next build`의 타입 검사가 프로젝트 전체를 봐서, 빌드가 되게 하려는 것뿐이다 |

## 다시 돌리기

저장소 루트에서 친다. `--out`은 저장소 밖의 절대 경로다(원본 출력과 결과 JSON이 남는다). 단계마다 나무의 상태를 보고, 맞지 않으면 아무것도 하지 않고 멈춘다.

```sh
# 추적하는 그대로의 나무에서
node .scratch/release-image/probes/widget_runtime/measure.mjs control --out <저장소 밖 폴더>

# 실험 판을 건 뒤에
git apply .scratch/release-image/probes/widget_runtime/runtime.patch
node .scratch/release-image/probes/widget_runtime/measure.mjs runtime --out <저장소 밖 폴더>
node .scratch/release-image/probes/widget_runtime/measure.mjs forks --out <저장소 밖 폴더>
node .scratch/release-image/probes/widget_runtime/measure.mjs live --out <저장소 밖 폴더>
node .scratch/release-image/probes/widget_runtime/measure.mjs element --rounds 3 --out <저장소 밖 폴더>
node .scratch/release-image/probes/widget_runtime/measure.mjs startup --rounds 4 --out <저장소 밖 폴더>
node .scratch/release-image/probes/widget_runtime/measure.mjs siteread --rounds 3 --out <저장소 밖 폴더>
node .scratch/release-image/probes/widget_runtime/measure.mjs standalone --out <저장소 밖 폴더>

# 되돌릴 때
git apply --reverse .scratch/release-image/probes/widget_runtime/runtime.patch
```

- 필요한 것: node 24(위젯의 시작 래퍼가 `.ts` 파일을 node로 바로 돈다), pnpm 11, 깔린 `web/node_modules`(`pnpm -C web install --frozen-lockfile`).
- 하는 일: 위젯의 빌드 산출물(`web/apps/widget/.next`, `public/element.js`)을 지우고 다시 만든다. 둘 다 `.gitignore`가 무시하는 자리다. 서버는 `127.0.0.1`의 빈 포트에만 띄우고, 끌 때는 그 pid의 명령줄에 그 회차의 표지(`--title=widget-runtime-probe-<회차>-<난수>`)가 있을 때만 끈다. `forks`는 `.next/routes-manifest.json`을 잠깐 바꿔 썼다가 되돌리고, `standalone`은 `.next/standalone` 안의 깨진 링크를 다시 만든다(아래).
- `element`와 `siteread`는 어느 나무에서도 돈다. `element.js`의 해시는 나무마다 다르다(실험 판은 `element/WidgetElement.tsx`가 달라 번들이 다르다). 결과로 옮긴 `element`는 실험 판에서 돌았다.
- 모든 빌드와 start는 `NEXT_TELEMETRY_DISABLED=1`로 돈다.
- 표지를 보지 못한 회차가 하나라도 있으면 그 단계의 종료 코드가 1이다.
- `runtime.patch`는 거꾸로 걸었다가 다시 거는 것까지 손으로 봤다(`git apply --reverse`, `control` 단계, `git apply`, `runtime` 단계 차례로).

## 환경

| 무엇 | 값 | 어떻게 봤나 |
|---|---|---|
| 날짜 | 2026-11-11 | |
| 운영체제 | Windows 10 Home 10.0.19045 x64 | `measure.mjs`가 결과 JSON마다 적는다 |
| CPU, 메모리 | AMD Ryzen 7 3700X(8코어 16스레드), 32GB | 같다 |
| node | v24.19.0 | 같다 |
| pnpm | 11.24.0 | 같다 |
| Next | 16.3.6(Turbopack) | 같다. 빌드와 start가 찍는 머리 줄에도 있다 |

## 전제(원본 출력에서 한 번 본 것)

- `next start`는 `✓ Ready in …ms` 줄을 찍은 뒤에 `next.config.ts`를 읽는다(`runtime-A-start-B.log`에서 Ready 줄이 1260ms, `✓ Running next.config.ts took 93ms` 줄이 1355ms). 그래서 Ready 줄은 "설정이 받아들여졌다"의 표지가 아니다. 없는 파일로 띄운 회차는 Ready 줄을 찍고 나서 `⨯ Failed to load next.config.ts`와 사이트 파일의 진단을 찍고 끝났다(`control-A-start-missing.log`).
- 페이지가 받은 props는 HTML에 스크립트의 문자열로 실려 따옴표가 `\"`다(`"allowedOrigins":[…]`, `"requestChars":N`). RSC 응답은 `GET /widget?_rsc`에 `RSC: 1` 헤더를 붙여 받았고 `Content-Type`이 `text/x-component`다.
- 지금 코드의 브라우저 쪽 번들에는 허용 출처가 공백으로 이은 문자열 하나로, 글자 수 상한이 `requestChars:Number("4000")` 꼴로 들어 있다. 실험 판의 번들에는 둘 다 없다.
- 실험 판의 빌드가 찍는 경로 표에는 `ƒ Proxy (Middleware)` 줄이 있다.
- `output: "standalone"`으로 지은 `server.js`도 `✓ Running next.config took 42ms` 줄을 찍는다(`standalone-A-start-missing.log`). 그 줄이 `next.config.ts`의 몸이 돌았다는 뜻은 아니다(아래 6번).

## 결과

"빌드"는 본 값이 빌드 때의 사이트 파일 것이라는 뜻이고 "시작"은 띄울 때의 사이트 파일 것이라는 뜻이다. 응답 시간은 같은 PC에서 요청마다 새 연결을 열어 차례로 100번 잰 값이다(준비 요청 한 번 뒤). "Ready까지"는 프로세스를 띄운 때부터 Ready 줄까지다.

### 1. 양성 대조: 지금 코드(`control`, 추적하는 그대로의 나무)

| 회차 | 본 것 |
|---|---|
| A로 빌드 | 18.8초(B로 빌드는 14.6초). 경로 표는 `○ /`, `○ /_not-found`. A의 허용 출처가 든 산출물이 다섯이다(`required-server-files.js`·`.json`, `routes-manifest.json`, 서버 쪽 번들 `server/chunks/ssr/apps_widget_components_pages_WidgetPage_tsx_0748fba._.js`, 브라우저 쪽 번들 `static/chunks/0a-e_pw14q1gl.js`) |
| A로 빌드한 것을 B로 start | 본 자리가 모두 "빌드"(A)다. `frame-ancestors` 헤더는 페이지, 질의가 붙은 페이지, RSC 응답, 없는 경로(404), `element.js`, 글꼴에서 모두 A였다. 번들의 허용 출처와 글자 수 상한도 A, `element.js`의 해시도 A로 지은 기준 파일과 같았다. 페이지는 `Cache-Control: s-maxage=31536000`, `x-nextjs-prerender: 1`. Ready까지 1147ms, 응답 1.0~3.4ms(중앙값 1.4) |
| B로 빌드한 것을 A로 start | 같다. 본 자리가 모두 "빌드"(B)다. Ready까지 1250ms, 응답 1.0~2.7ms(중앙값 1.5) |
| A로 빌드한 것을 없는 파일로 start | Ready 줄을 979ms에 찍고 1063ms에 종료 코드 1로 스스로 끝났다. 진단은 "파일이 없다"이고 그 파일 이름을 든다. Ready 줄을 보고 보낸 페이지 요청은 응답을 받지 못했다(`fetch failed`) |

지금 코드에서는 본 자리 가운데 `start` 때의 사이트 파일을 따른 것이 없다. `start`가 사이트 파일을 읽기는 한다(없는 파일이면 끝난다).

### 2. 실험 판의 주 갈래(`runtime`)

주 갈래는 셋을 함께 건 것이다. 설정의 바닥값 `frame-ancestors 'none'` 위에 `proxy.ts`가 요청 때의 값을 덮고, 페이지는 요청 때 그리며 props로 값을 받고, 시작 래퍼가 `start`에서 `element.js`를 다시 짓는다.

빌드: A 16.4초, B 18.0초, 없음 19.5초. 경로 표는 `ƒ /`, `○ /_not-found`, `ƒ /config`. A의 값도 B의 값도 든 산출물이 0개다.

| 빌드 → start | `frame-ancestors`(페이지, 질의 붙은 페이지, RSC) | 페이지의 props(HTML, RSC) | `/widget/config` | `element.js` | Ready까지 | 응답 시간 |
|---|---|---|---|---|---|---|
| A → B, `element.js`를 다시 짓지 않음 | 시작(B) | 시작(B) | 시작(583927) | 빌드(A) | 994ms | 4.3~11.0ms(중앙값 5.4) |
| A → B | 시작(B) | 시작(B) | 시작 | 시작(B) | 1260ms | 4.4~11.3ms(5.2) |
| A → A | A | A | A | A | 1181ms | 4.0~24.0ms(5.0) |
| A → 없음 | 시작(`'none'`) | 시작(`[]`, 20000) | 시작(20000) | 시작 | 1346ms | 3.9~16.6ms(5.8) |
| A → 다시 B | 시작(B) | 시작(B) | 시작 | 시작(B) | 1880ms | 4.3~9.7ms(5.2) |
| B → A | 시작(A) | 시작(A) | 시작 | 시작(A) | 1482ms | 4.1~24.2ms(5.8) |
| 없음 → B | 시작(B) | 시작(B) | 시작 | 시작(B) | 1234ms | 4.2~12.5ms(6.3) |

- 위의 A로 시작하는 다섯 줄은 빌드 하나를 그대로 두고 start만 다섯 번 한 것이다. 회차마다 띄우기 전후에 `.next`의 산출물 해시가 같았다(start가 산출물을 고치지 않았다).
- proxy가 지나는 경로(`/widget`)의 헤더는 값 하나다. 바닥값과 나란히 실리지 않았다.
- proxy가 지나지 않는 경로(없는 경로의 404, `element.js`, 글꼴, `/widget/config`)는 언제나 바닥값 `frame-ancestors 'none'`이었다.
- 페이지는 `Cache-Control: private, no-cache, no-store, max-age=0, must-revalidate`이고 `x-nextjs-prerender` 헤더가 없다.
- `/widget/config`는 200이고 `Access-Control-Allow-Origin: *`가 붙었다.
- 없는 파일로 start, `element.js`를 다시 짓는 판: 549ms에 종료 코드 1로 끝났고 next까지 가지 않았다(머리 줄이 없다). `element.js`를 짓는 길이 먼저 사이트 파일을 읽기 때문으로 읽었다(코드를 읽은 것: `web/apps/widget/tools/element.ts` 41행 `buildInput(env)`).
- 없는 파일로 start, 다시 짓지 않는 판: 지금 코드와 같다. Ready 줄을 1151ms에 찍고 1317ms에 종료 코드 1로 끝났고, 그 사이의 페이지 요청은 응답을 받지 못했다.

### 3. 다른 갈래(`forks`)

| 갈래 | 본 것 |
|---|---|
| 페이지에서 `connection()`을 빼고 설정의 바닥값도 뺀 판을 A로 빌드(13.8초) | 경로 표가 `○ /`로 돌아간다. 미리 그린 파일 넷(`server/app/index.html`, `index.rsc`, `index.segments/_full.segment.rsc`, `index.segments/__PAGE__.segment.rsc`)에 A의 값이 들어 있다 |
| 그것을 B로 start | 페이지의 props는 빌드(A)다. `frame-ancestors`는 페이지에서 시작(B)이고, proxy가 지나지 않는 경로에는 헤더가 없다. 페이지는 다시 `s-maxage=31536000`. 응답 1.9~17.8ms(중앙값 3.1) |
| 그것을 없음으로 start | 페이지의 props는 여전히 A, 헤더는 `'none'`. 응답 1.9~10.5ms(중앙값 3.1) |
| 주 갈래를 없음으로 빌드(17.7초)하고, start 전에 `.next/routes-manifest.json`의 `frame-ancestors 'none'`(한 곳)을 B의 값으로 바꿔 쓴 뒤 A로 start | proxy가 지나는 페이지는 A(시작), proxy가 지나지 않는 경로(404, `element.js`, 글꼴)는 바꿔 쓴 B였다. 응답 4.3~19.2ms(중앙값 5.3). 끝나고 파일을 되돌렸다 |

- 첫 갈래는 헤더와 페이지의 값이 따로 움직인다는 것을 보인다. proxy는 미리 그린 페이지에도 요청 때의 헤더를 달지만, 페이지가 받는 값은 `connection()` 없이는 빌드 때 굳는다.
- 마지막 갈래는 서버 파일 없이 헤더를 바꾸는 길 하나다. `next start`는 start 전에 바꿔 쓴 `routes-manifest.json`의 헤더를 그대로 냈다. 바꿔 쓴 것은 헤더뿐이다. 이 회차에서 페이지의 props가 시작의 값(A)인 것은 주 갈래의 `connection()` 때문이고 바꿔 쓰기와는 무관하다. proxy 없이 이 길만으로 페이지의 헤더를 내는 판은 돌리지 않았다(proxy가 지나지 않는 경로에서 본 것으로 미루어 같을 것으로 본다. 어림).

### 4. 떠 있는 서버가 사이트 파일의 바뀐 내용을 따라가는가(`live`)

`--out` 아래에 사이트 파일의 사본(A의 내용)을 두고 그 경로로 start한 뒤, 서버를 끄지 않고 사본을 고쳤다. 한 번 돌렸다(빌드 38.4초, Ready까지 2229ms).

| 때 | 헤더(페이지) | 페이지의 props | `/widget/config` | `element.js` |
|---|---|---|---|---|
| 바꾸기 전 | A | A | A | A |
| 사본의 내용을 B로 바꾼 뒤(같은 프로세스) | B | B | B | A(그대로) |
| 사본을 지운 뒤(같은 프로세스) | 페이지가 500이고 `Content-Security-Policy` 헤더가 없다. props도 없다 | | 500 | 200 |

- 실험 판은 요청마다 사이트 파일을 읽으므로, 다시 띄우지 않아도 다음 요청부터 바뀐 값을 낸다. `element.js`는 띄울 때 한 번 지으므로 따라가지 않는다. 그래서 떠 있는 동안 파일이 바뀌면 iframe 방식과 페이지 안 방식의 글자 수 상한이 갈린다.
- 사본을 지운 뒤에도 서버는 떠 있었다. 500 응답에는 바닥값 헤더도 없었다. 500 응답의 몸은 저장하지 않았다.

### 5. `element.js`에 글자 수 상한을 실행 중에 주는 길

세 길 가운데 (가)는 서버까지, (나)는 파일까지, (다)는 서버 쪽 절반만 쟀다.

**(가) start가 다시 짓는다.** 2번의 표대로 `element.js`가 시작의 값을 따른다. 드는 시간은 아래다.

| 무엇 | 값 |
|---|---|
| `element.js` 하나를 따로 짓는 프로세스 전체(`element` 단계, 아홉 번) | 774~1804ms(중앙값 955) |
| 그 가운데 모듈 적재(vite, `@tailwindcss/vite`) | 409~1236ms(중앙값 504) |
| 그 가운데 Vite 빌드 | 258~428ms(중앙값 290) |
| 다시 짓지 않는 start의 Ready까지(`startup` 단계, 번갈아 네 짝) | 896~1366ms(1105, 1366, 896, 1047) |
| 다시 짓는 start의 Ready까지 | 1160~1665ms(1665, 1164, 1160, 1258) |

두 start의 범위는 겹친다. 네 짝 가운데 셋에서 다시 짓는 쪽이 길었다. 두 갈래 모두 시작 래퍼가 vite를 적재한다(코드를 읽은 것: 지금의 래퍼가 `element.ts`를 import하고 `element.ts`가 `vite`와 `@tailwindcss/vite`를 import한다. 선례 `widget_build/README.md`의 4번이 그 줄을 든다). 다시 짓는 데는 실행 자리에 vite와 페이지 안 번들의 원본 파일이 있어야 한다(어림. 어느 파일까지 필요한지는 재지 않았다).

**(나) 자리표로 지어 두고 start 때 숫자만 바꿔 넣는다.** 파일까지만 쟀다(`element` 단계).

- 같은 사이트 파일로 세 번 지으면 세 번 모두 바이트가 같았다(A 405,227바이트, B 405,230바이트, 자리표 405,233바이트).
- 자리표로 지은 파일에 `918273645`는 한 곳뿐이다(`function si(){return 918273645}`).
- 그 숫자를 `583927`로 바꾼 파일은 B로 바로 지은 파일과 바이트까지 같았다.
- `4000`으로 바꾼 파일은 A로 바로 지은 파일과 같지 않았다. 압축기가 4000을 `4e3`으로 쓰기 때문이고, `4e3`으로 바꾸면 같았다. 값으로는 같은 수다.
- 그렇게 바꾼 파일을 서버가 내는 것은 재지 않았다. (가)에서 start 전에 디스크의 `public/element.js`를 갈아 둔 것이 그대로 나갔으므로 같을 것으로 본다(어림).

**(다) 요청 때 값을 내는 경로에서 받는다.** `GET /widget/config`가 시작의 값(`requestChars`)을 `Access-Control-Allow-Origin: *`와 함께 낸다(2번, 4번). 페이지 안 번들이 그 경로를 받아 쓰게 고치는 쪽은 짓지 않았고 재지 않았다.

### 6. `output: "standalone"`(`standalone`)

실험 판을 `AGENT_OS_PROBE_OUTPUT=standalone`으로 A로 빌드했다(19.3초). 한 번 돌렸다.

크기(MB는 1024×1024바이트).

| 무엇 | 크기 | 파일 |
|---|---|---|
| `.next/standalone`(지은 그대로) | 17.6MB | 1,204(링크 26) |
| 그 가운데 `node_modules` | 16.5MB | 1,109 |
| 문서대로 `public`을 복사한 것 | 6.0MB | 387 |
| 문서대로 `.next/static`을 복사한 것 | 13.7MB | 784 |
| 복사한 뒤의 전체 | 37.3MB | 2,375 |

견줄 값으로, 선례 `widget_build/README.md`의 4번은 지금 방식에 드는 의존성 묶음을 394.9~443.8MB로 적는다(Windows, 의존 그래프로 닿는 패키지 전체).

- 지은 그대로는 이 PC에서 뜨지 않았다. `node server.js`가 `Error: EPERM: operation not permitted, stat '…\.next\standalone\node_modules\.pnpm\next@16.3.6_…\node_modules\react'`로 종료 코드 1이었다. standalone 나무의 링크 26개 가운데 9개가 따라가지지 않았다(디렉터리를 가리키는데 `stat`이 EPERM이다). 그 9개를 디렉터리 접합(junction)으로 다시 만든 뒤에 아래 회차를 돌았다.

| start | 본 것 | Ready까지 | 응답 시간 |
|---|---|---|---|
| B | 헤더, 페이지의 props, `/widget/config`는 시작(B). `element.js`는 빌드(A). proxy가 지나지 않는 경로는 `'none'` | 972ms | 4.6~22.7ms(중앙값 7.3) |
| A | 모두 A | 507ms | 4.6~13.5ms(5.7) |
| 없음 | 헤더 `'none'`, props `[]`·20000. `element.js`는 빌드(A) | 786ms | 5.4~19.7ms(7.6) |
| 없는 파일 | 서버가 뜨고(Ready 561ms) 요청 뒤에도 떠 있었다. 페이지는 500이고 `Content-Security-Policy` 헤더가 없다. `/widget/config`도 500, `element.js`는 200. 출력에 사이트 파일의 진단이 찍힌다 | | |

- standalone은 시작 래퍼를 거치지 않으므로 `element.js`를 다시 짓지 않는다. 빌드 때의 값이 남는다.
- standalone의 `server.js`는 없는 파일에도 뜬다. 시작 래퍼로 띄운 2번에서는 같은 없는 파일이 start를 끝냈다.

### 7. 요청마다 드는 값

- 페이지 응답 시간(같은 PC, 차례로, 새 연결): 미리 그린 지금 코드 1.0~3.4ms(중앙값 1.4~1.5, 두 회차). 미리 그린 페이지에 proxy만 건 갈래 1.9~17.8ms(중앙값 3.1, 두 회차). 요청 때 그리는 주 갈래 3.9~24.2ms(중앙값 5.0~6.3, 일곱 회차). standalone의 주 갈래 4.6~22.7ms(중앙값 5.7~7.6, 세 회차).
- 사이트 파일 읽기(`siteread` 단계): `buildInput` 한 번이 0.132~0.180ms다(1000번씩 여섯 묶음, 중앙값 0.148. 파일은 1,214~1,627바이트). 실험 판은 페이지 요청 하나에 두 번(proxy, 서버 컴포넌트), `/widget/config` 요청 하나에 한 번 부른다.

### 8. 손으로 본 것: 실험 판이 지금의 게이트에 걸리는 자리

| 명령 | 결과 |
|---|---|
| `pnpm -C web exec eslint`에 고친 파일 10개 | 오류 4건. `proxy.ts`와 `app/config/route.ts`가 "Next 서버가 돌리는 파일(route, middleware, proxy, instrumentation)을 두지 않는다 … (ADR 0019)"에, `app/page.tsx`와 `app/config/route.ts`가 "app/ 의 파일은 components/pages 와 components/templates 만 import 한다 … (ADR 0021)"에 걸린다(`@agent-os/site-file`을 import했다) |
| `pnpm -C web/apps/widget exec tsc --noEmit -p tsconfig.json --diagnostics` | 오류 없음 |
| `pnpm -C web exec vitest run apps/widget/next.config.test.ts apps/widget/tools/start.test.ts apps/widget/components/pages apps/widget/lib/build.test.ts apps/widget/element` | 파일 14개 가운데 1개, 시험 269개 가운데 5개가 실패했다. 다섯 모두 `apps/widget/next.config.test.ts`다. 출력에서 읽은 넷은 설정의 `env`와 `/:path*` 헤더가 사이트 파일의 값을 싣는다는 단언이다(남은 출력의 앞부분이 잘려 첫 실패의 이름은 보지 못했다) |

e2e(`playwright`), 사진 비교, `-m llm_widget`은 실험 판으로 돌리지 않았다.

## 코드를 읽은 것

Next 16.3.6 설치본(`web/apps/widget/node_modules/next/dist/`)이다.

- `docs/01-app/03-api-reference/03-file-conventions/proxy.md`: `proxy.ts`는 프로젝트 루트(또는 `src`)에 두고 기본 런타임이 Node.js다. 실행 차례는 설정의 `headers`, `redirects`, 그다음 Proxy다. `matcher`는 빌드 때 읽는 상수여야 한다. 응답 헤더는 `NextResponse.next()`에 `response.headers.set`으로 단다.
- `docs/01-app/02-guides/self-hosting.md`의 "Environment Variables": 실행 중에 환경 변수를 읽으려면 요청 때 그리게 해야 하고 `await connection()` 뒤에 `process.env`를 읽는 예를 든다. 그렇게 하면 한 이미지를 여러 환경에 쓸 수 있다고 적는다.
- `docs/01-app/03-api-reference/04-functions/connection.md`: `connection()`은 그 뒤의 코드를 빌드 때의 미리 그리기에서 뺀다.
- `docs/01-app/03-api-reference/03-file-conventions/route.md` 669행: `GET` 핸들러는 v15부터 기본이 요청 때 실행이다.
- `docs/01-app/03-api-reference/05-config/01-next-config-js/output.md`: standalone은 `public`과 `.next/static`을 복사하지 않으므로 손으로 복사한다. `PORT`와 `HOSTNAME`으로 듣는 자리를 정한다. 모노레포는 `outputFileTracingRoot`를 준다.
- `build/analysis/get-page-static-info.js` 353~354행: `matcher`의 경로 앞에 basePath를 붙인다. 그래서 `"/"`가 `/widget`에 맞는다.
- `server/lib/router-utils/filesystem.js` 223행, 289~302행: 운영 모드의 서버는 헤더·리다이렉트·리라이트를 `.next/routes-manifest.json`에서 읽는다. 설정 파일에서 다시 만드는 것은 개발 모드다(305행). 1번에서 헤더가 빌드의 값으로 남는 까닭이고, 3번의 바꿔 쓰기가 듣는 까닭이다.
- `server/lib/router-utils/resolve-routes.js` 461~462행(proxy의 응답 헤더를 `resHeaders[key] = value`로 싣는다), 552~562행(설정의 헤더도 같은 자리에 싣는다). 2번에서 proxy의 값이 바닥값을 덮는 것과 맞는다.
- 빌드가 만든 `.next/standalone/apps/widget/server.js` 18~20행: 빌드 때의 설정을 `const nextConfig = {…}`로 적어 두고 `__NEXT_PRIVATE_STANDALONE_CONFIG`로 넘긴다. standalone의 start가 `next.config.ts`의 몸(사이트 파일 검사)을 돌리지 않는 까닭으로 읽었다.

저장소 쪽.

- `docs/adr/0024-*.md` 20~21행, 35~36행: 앞서 시작 래퍼가 값을 넘기는 길을 시도했다가 헤더가 빌드 때 굳어 접었고, ADR 0019에 proxy 예외를 두는 안을 물리쳤다고 적는다.
- `web/eslint.config.mjs` 92~96행, 327~333행: 서버가 돌리는 파일을 막는 규칙.

## 해석과 그 갈래

- "지금 코드는 start 때의 사이트 파일을 따르지 않는다"고 읽었다. 양성 대조는 1번의 두 방향이다(A로 빌드해 B로, B로 빌드해 A로). 한 방향만이면 "어느 쪽이든 A를 낸다"와 가를 수 없다. "start가 사이트 파일을 아예 읽지 않는다"는 해석은 없는 파일로 띄운 회차가 가른다(읽고 끝난다).
- "실험 판은 헤더와 페이지의 값이 start 때의 사이트 파일을 따른다"고 읽었다. 양성 대조는 같은 빌드 하나로 B, A, 없음, 다시 B를 차례로 띄운 것과 빌드를 바꾼 두 방향(B → A, 없음 → B)이다. "start가 산출물을 고쳐서 그렇다"는 해석은 띄우기 전후의 산출물 해시가 같다는 표지가 가른다. "값이 우연히 맞았다"는 해석은 세 사이트 파일의 값이 서로 다르고 본 값이 그 가운데 하나로 갈려야 측정으로 세는 것이 가른다.
- "헤더는 proxy가, 페이지의 값은 `connection()`이 바꾼다"고 읽었다. 3번의 첫 갈래가 둘을 떼어 놓는다(`connection()`을 빼면 props만 빌드의 값으로 돌아가고 헤더는 시작의 값이다). proxy를 빼고 `connection()`만 둔 갈래는 돌리지 않았다. 그 자리는 2번에서 proxy가 지나지 않는 경로가 바닥값만 낸 것으로 본다.
- "`element.js`는 다시 지어야 따른다"고 읽었다. 2번의 첫 줄(다시 짓지 않으면 빌드의 값)과 둘째 줄(다시 지으면 시작의 값)이 같은 빌드에서 갈린다. standalone의 세 회차도 다시 짓지 않아 빌드의 값이었다.
- "요청 때 읽는다(시작 때 한 번이 아니다)"는 4번이 가른다. 같은 프로세스에서 파일 내용만 바꿔 값이 바뀌었고, 바꾸기 전에 A였다는 것이 그 사본을 읽는다는 양성 대조다. 한 번 돌렸다.
- "요청 때 그리면 응답이 느려진다"는 범위로만 읽는다. 지금 코드의 두 회차(최대 3.4ms)와 주 갈래 일곱 회차(최소 3.9ms)의 범위는 이 측정에서 겹치지 않았다. 다만 회차마다 서버를 새로 띄워 차례로 100번 잰 값이고 부하를 고르게 맞추지 않았다. 늘어난 몫이 proxy 것인지 그리기 것인지는 3번 첫 갈래(proxy만, 중앙값 3.1)로 어림할 뿐 가르지 않았다.
- 5번 (가)의 "다시 지으면 Ready가 늦어진다"는 네 짝 가운데 셋에서만 그랬고 범위가 겹친다. 늦어진다고 단정하지 않는다.
- 6번의 "standalone은 없는 파일에도 뜬다"는 한 번 본 것이다. 같은 없는 파일이 시작 래퍼의 start를 끝낸 회차(1번, 2번)가 대조다. 까닭(설정 파일의 몸이 돌지 않는다)은 코드를 읽은 것이다.
- 모든 가름은 이 PC에서 시작 래퍼의 `start`(안에서 `next start`를 돈다)와 standalone의 `server.js` 두 가지로 띄운 것에 한한다. 다른 띄우는 길(사용자 정의 서버, 다른 호스팅)로 넓히지 않는다.

## 결과를 본 뒤 바꾼 것

- 없는 파일로 띄우는 회차의 표지. 첫 판은 "Ready 줄이 끝내 없다"를 표지로 뒀다. 원본 출력에서 Ready 줄이 설정 읽기보다 먼저 찍히는 것을 보고, 표지를 "스스로 0이 아닌 코드로 끝났고 출력에 그 파일의 진단이 있다"로 바꾸고 Ready 줄은 관찰로 적게 했다.
- 응답 시간을 재는 법. 첫 판은 연결을 재사용하는 `fetch`로 20번 쟀고, 미리 그린 페이지와 요청 때 그리는 페이지가 모두 중앙값 16ms 언저리였다(이 PC의 타이머 눈금으로 봤다. 어림). 요청마다 새 연결을 여는 `node:http`로 100번 재게 바꾸고 `control`과 `runtime`을 다시 돌렸다. 위 표는 다시 돌린 값이다. 처음 돌린 `control`의 Ready까지는 1091ms, 1404ms였고 가름은 같았다.
- 더한 갈래. 질의가 붙은 페이지 요청, `routes-manifest.json` 바꿔 쓰기, `startup`, `siteread`, `live`는 주 갈래의 결과를 본 뒤에 더했다.
- standalone. 첫 판은 지은 그대로 띄웠고 EPERM으로 뜨지 않았다. 링크를 조사하는 단계와 "지은 그대로 띄우기"를 관찰로 남기는 단계를 더하고, 따라가지지 않는 링크를 접합으로 다시 만든 뒤 회차를 돌게 했다. 없는 파일로 띄우는 회차도 그때 더했다.
- 범위의 평균을 소수 한 자리로 반올림하던 것을 세 자리로 고쳤다. `siteread.json`에 남은 평균(0.1)은 고치기 전의 것이고 다시 돌리지 않았다. 최소·중앙값·최대는 맞다.

## 재지 못한 것

- 리눅스 컨테이너에서의 모든 값. 이 프로브는 Windows에서만 돌았다.
- 브라우저. 헤더와 응답에 실린 글자만 봤다. 허용 출처 밖의 사이트가 iframe을 실제로 품지 못하는지, 위젯이 받은 값으로 postMessage를 거르고 글자 수를 세는지는 보지 않았다.
- 5번 (다)의 브라우저 쪽 절반(페이지 안 번들이 `/widget/config`를 받아 쓰는 것)과 그 요청이 실패하거나 늦을 때의 화면.
- 5번 (나)로 갈아 넣은 파일을 서버가 내는 것.
- 사용자 정의 서버(custom server)로 헤더를 다는 길, 앞단 프록시(nginx 등)가 헤더를 다는 길.
- proxy의 `matcher`를 없애 모든 경로에 걸었을 때의 값, 사이트 파일을 시작 때 한 번만 읽어 기억해 두는 판.
- 사이트 파일이 없어진 뒤의 500 응답에 `frame-ancestors`를 싣는 판(proxy가 예외를 잡아 `'none'`을 내는 판). 지금 실험 판은 그 응답에 헤더가 없다.
- 동시 요청과 처리량, 메모리. 응답 시간은 차례로 하나씩 보낸 값이다.
- e2e, 사진 비교, 실제 모델 e2e(`-m llm_widget`)를 실험 판으로 돌린 결과.
- standalone 나무에 `element.js`를 다시 짓는 데 드는 것(vite와 원본 파일)이 들어 있는지. standalone은 시작 래퍼를 거치지 않아 보지 않았다.
- 실험 판의 start가 쓰는 디스크(`public/element.js`를 덮어쓴다)가 읽기 전용인 자리.

## 이 PC라서 리눅스 컨테이너와 다를 수 있는 것

따로 적지 않은 한 어림이다.

- 시간 전부. 여기서도 같은 빌드가 부하에 따라 두 배 넘게 흔들렸다.
- standalone의 깨진 링크. Windows에서 디렉터리를 가리키는 링크가 따라가지지 않은 것이라, 리눅스에서는 지은 그대로 뜰 것으로 본다. 돌려 보지 않았다.
- standalone의 크기. `node_modules` 16.5MB에는 이 플랫폼의 네이티브 패키지가 들어 있다(선례 `widget_build/README.md`가 플랫폼별 패키지 크기를 적는다).
- 내용 해시가 든 파일 이름과 경로 구분 문자.
- 가름(무엇이 빌드의 값이고 무엇이 시작의 값인지)은 같을 것으로 보지만 리눅스에서 돌려 보지 않았다.

## `probes/README.md` 표에 넣을 줄

이 폴더 위의 `probes/README.md`는 이 프로브가 만들지 않았다(파일을 이 폴더 아래에만 두기로 했다). 표를 만들 때 넣을 줄이다.

| 프로브 | 무엇을 재는지 | 어디가 근거로 드는지 | 다시 돌 때 필요한 것 | 판 |
|---|---|---|---|---|
| `widget_runtime/`(`measure.mjs`, `element_build.mjs`, `runtime.patch`, `sites_b.toml`, `sites_sentinel.toml`) | 위젯을 한 번 빌드한 산출물이 start 때(요청 때)의 사이트 파일을 따르는지. 지금 코드의 대조, proxy와 요청 때 그리기와 `element.js` 다시 짓기를 건 실험 판, 그 갈래, 떠 있는 서버, `element.js`의 세 길, standalone | release-image 설계 인터뷰(아직 명세와 ADR이 들지 않았다) | node 24, pnpm 11, 깔린 `web/node_modules`, 저장소 밖의 `--out` 폴더. `control` 밖의 서버 단계는 `runtime.patch`를 건 나무 | Windows 10, node v24.19.0, pnpm 11.24.0, Next 16.3.6 |
