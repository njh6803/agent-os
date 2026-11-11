# release-image widget_build 프로브

`release-image` 설계 인터뷰에서 "컨테이너가 시작할 때 그 자리의 사이트 파일로 위젯을 빌드한다"는 선택지가 치르는 값을 본 프로브다. 위젯(`web/apps/widget`)의 빌드는 사이트 파일(`AGENT_OS_SITE_FILE`)의 허용 출처와 글자 수 상한을 산출물에 굽는다. 여기서는 결정하지 않고 본 것만 적는다. 규약은 `docs/agents/issue-tracker.md`의 "프로브와 근거"다.

근거의 종류. 아래 "결과"의 줄은 따로 적지 않은 한 `measure.mjs`(이 폴더)가 다시 내는 것이고, 2026-11-11에 돌린 출력에서 옮겼다. 결과로 옮긴 실행에는 표지를 보지 못한 회차가 없었다(단계마다 종료 코드 0). 손으로 본 것은 그 명령과 함께, 코드를 읽은 것은 파일과 줄과 함께, 재지 않은 것은 어림이라고 적었다.

시간은 범위로 읽는다. 이 PC에서 다른 세션이 여럿 함께 돌던 때라(PowerShell로 프로세스를 세어 손으로 봤다. claude 22개, node 44개, python 32개) 위젯의 cold 빌드가 15.2초에서 76.0초(네트워크 훅을 실은 회차)까지 흔들렸다. 한 값을 문턱으로 쓰지 않는다.

## 파일

| 파일 | 무엇 |
|---|---|
| `measure.mjs` | 측정 전체. 단계마다 무엇을 표지로 보는지는 독스트링과 단계 함수의 주석에 있다 |
| `phases.mjs` | 위젯 빌드의 앞 단계(글꼴 복사, 페이지 안 번들의 Vite 빌드)만 따로 잰다. `measure.mjs phases`가 띄운다 |
| `net_hook.cjs` | 빌드의 node 프로세스가 루프백 밖으로 거는 연결과 이름 풀기를 적고 막는 훅. `measure.mjs net`이 싣는다 |
| `net_control.mjs` | 그 훅의 양성 대조. 같은 훅을 실은 node가 어디에도 닿지 않는 주소 셋에 `fetch`를 건다 |
| `sites_b.toml` | 둘째 사이트 파일. 허용 출처 둘(`https://probe-b.example`, `https://www.probe-b.example:8443`)과 글자 수 상한 583927 |

첫째 사이트 파일은 저장소의 픽스처 `tests/fixtures/site_file/sites.toml`이다(허용 출처 셋 `https://shop.example`, `https://www.shop.example`, `http://localhost:3000`, 글자 수 상한 4000).

## 다시 돌리기

저장소 루트에서 친다. `--out`은 저장소 밖의 절대 경로다(원본 출력과 결과 JSON이 남는다).

```sh
node .scratch/release-image/probes/widget_build/measure.mjs install --out <저장소 밖 폴더>
node .scratch/release-image/probes/widget_build/measure.mjs build --cold 3 --warm 3 --out <저장소 밖 폴더>
node .scratch/release-image/probes/widget_build/measure.mjs phases --rounds 3 --out <저장소 밖 폴더>
node .scratch/release-image/probes/widget_build/measure.mjs diff --out <저장소 밖 폴더>
node .scratch/release-image/probes/widget_build/measure.mjs compare --out <저장소 밖 폴더>
node .scratch/release-image/probes/widget_build/measure.mjs net --out <저장소 밖 폴더>
node .scratch/release-image/probes/widget_build/measure.mjs sizes --whole --out <저장소 밖 폴더>
node .scratch/release-image/probes/widget_build/measure.mjs admin --rounds 2 --out <저장소 밖 폴더>
```

- 필요한 것: node 24(위젯의 시작 래퍼가 `.ts` 파일을 node로 바로 돈다)와 pnpm 11. `install`은 `pnpm -C web install --frozen-lockfile`을 돌리므로 pnpm 스토어에 패키지가 있거나 네트워크가 있어야 한다. `install` 밖의 단계는 `web/node_modules`가 깔려 있어야 한다.
- 하는 일: 위젯과 관리 화면의 빌드 산출물(`web/apps/widget/.next`, `public/element.js`, `public/fonts`, `web/apps/admin/.next`)을 지우고 다시 만든다. 모두 `.gitignore`가 무시하는 자리다. 추적하는 파일은 고치지 않는다. 서버는 띄우지 않는다. `diff`는 `--out`에 산출물 나무 넷(하나에 약 73MB)을 복사하고, 자기가 심은 표지 파일이 있는 나무 폴더만 지운다.
- 모든 빌드는 `NEXT_TELEMETRY_DISABLED=1`로 돈다(`net`의 둘째 빌드만 그 변수 없이 `NEXT_TELEMETRY_DEBUG=1`).
- 표지를 보지 못한 회차가 하나라도 있으면 그 단계의 종료 코드가 1이다.

## 환경

| 무엇 | 값 | 어떻게 봤나 |
|---|---|---|
| 날짜 | 2026-11-11 | |
| 운영체제 | Windows 10 Home 10.0.19045 x64 | `measure.mjs`가 결과 JSON마다 적는다(`os.type()`, `os.release()`) |
| CPU, 메모리 | AMD Ryzen 7 3700X(8코어 16스레드), 32GB | 같다 |
| node | v24.19.0 | 같다 |
| pnpm | 11.24.0 | 같다 |
| Next | 16.3.6(Turbopack) | 빌드가 찍는 머리 줄. `measure.mjs`가 원본 줄을 남긴다 |
| Vite, rolldown 바인딩 | 8.3.1, 1.2.11 | `measure.mjs sizes`가 패키지 폴더의 `package.json`에서 읽는다 |
| TypeScript, tailwindcss | 5.9.3, 4.3.3 | 같다 |

## 결과

MB는 1024×1024바이트다.

### 0. 의존성 설치

`pnpm -C web install --frozen-lockfile`은 37.9초였다(pnpm이 찍은 줄은 `Done in 37.7s using pnpm v11.24.0`). `web/node_modules`가 없던 상태였고, 패키지 445개 가운데 441개를 이 PC의 pnpm 스토어에서 하드 링크로 가져왔고 내려받은 것은 0개다. 한 번 돌렸다. 스토어가 빈 자리(막 받은 이미지)에서 내려받는 시간은 재지 않았다.

### 1. 위젯 빌드 시간

`node tools/start.ts build`를 픽스처 사이트 파일로 돌렸다. cold는 `.next`, `public/element.js`, `public/fonts`를 지운 채, warm은 바로 앞 빌드의 산출물을 둔 채다. 세 번 실행했고 실행마다 cold 셋, warm 셋이다.

| 실행 | 차례 | 회차 직전 1초의 CPU 사용률 | cold 전체 | warm 전체 |
|---|---|---|---|---|
| 첫째 | cold 셋 뒤에 warm 셋 | 적지 않았다. 끝난 직후 79%(손으로 봤다. PowerShell `Get-CimInstance Win32_Processor`의 `LoadPercentage`) | 15.2~20.8초(20.0, 15.2, 20.8) | 19.1~23.0초(19.1, 19.3, 23.0) |
| 둘째 | cold와 warm을 번갈아 | 95~100% | 38.7~49.2초(42.9, 49.2, 38.7) | 32.4~35.6초(35.6, 32.4, 33.4) |
| 셋째 | cold와 warm을 번갈아 | 32~92% | 17.0~20.0초(18.4, 17.0, 20.0) | 13.3~18.0초(13.3, 14.4, 18.0) |

구간별 시간(초). "Next 머리 줄까지"는 node 시작, 글꼴 복사, 페이지 안 번들(Vite) 빌드, next CLI 적재이고, 그 뒤가 `next build`다. `next build` 안의 구간은 Next가 찍는 줄의 도착 시각으로 갈랐다. 구간 사이의 틈(설정 읽기, 끝의 정리)이 있어 합이 전체와 같지 않다.

| 구간 | 셋째 cold | 셋째 warm | 둘째 cold | 둘째 warm | 첫째 cold | 첫째 warm |
|---|---|---|---|---|---|---|
| Next 머리 줄까지 | 2.5~3.7 | 2.5~3.2 | 4.8~8.6 | 4.9~6.1 | 2.4~3.0 | 3.1~3.8 |
| 그 뒤(`next build`) | 14.5~17.2 | 10.8~15.2 | 33.9~44.2 | 27.0~29.5 | 12.8~17.8 | 15.6~19.7 |
| 컴파일 | 5.5~6.5 | 1.4~2.0 | 10.4~21.1 | 2.3~3.4 | 4.5~7.1 | 1.6~2.3 |
| 타입 검사 | 6.2~7.6 | 5.9~8.3 | 12.8~15.9 | 13.7~19.4 | 4.8~8.4 | 9.1~11.2 |
| 페이지(타입 검사 끝부터 경로 표까지) | 2.2~2.6 | 2.4~4.2 | 5.5~10.0 | 5.9~11.3 | 2.3~3.3 | 3.2~6.0 |

- 앞 단계만 따로(`measure.mjs phases`, 세 번): 프로세스 전체 2.4~2.6초. node 시작 0.12초, 모듈 적재(vite, `@tailwindcss/vite` 포함) 0.93~0.96초, 글꼴 복사 0.66~0.86초(woff2 386개), 페이지 안 번들의 Vite 빌드 0.59~0.71초(`element.js` 405,201바이트).
- 두 번째 빌드에서 줄어든 구간은 컴파일뿐이다(세 실행을 합쳐 cold 4.5~21.1초, warm 1.4~3.4초). 타입 검사와 페이지 구간은 warm에서 줄지 않았다(세 실행 모두 warm의 범위가 cold의 범위와 겹치거나 더 길었다).
- 전체 시간은 번갈아 돈 두 실행의 여섯 짝에서 warm이 바로 앞 cold보다 매번 짧았다(차이 2.0~16.9초). 셋째 실행은 cold와 warm의 범위가 겹친다.
- 다른 단계에서 돈 cold 빌드: `diff`의 다섯 번이 29.9~65.6초(직전 CPU 52~100%), `net`의 여섯 번(훅을 실은 빌드)이 25.6~76.0초(직전 CPU 75~100%)였다.
- 설치 직후의 첫 cold 빌드는 21.6초였다(한 번).

### 2. 사이트 파일이 바꾸는 산출물

픽스처 사이트 파일로 두 번(A1, A2), `sites_b.toml`로 두 번(B1, B2) cold 빌드해 산출물 나무(`.next/`와 `public/`, 나무마다 파일 1,320개)를 맞댔다.

입력이 같은 짝(A1↔A2, B1↔B2)은 둘 다 1,281개가 같고 39개가 달랐다. 빌드마다 달라지는 것이다.

| 빌드마다 달라지는 파일 | 수 | 까닭으로 본 것 |
|---|---|---|
| `.next/BUILD_ID`와 그 값을 품은 파일(`build-manifest.json`, `fallback-build-manifest.json`, `server/middleware-build-manifest.js`, 미리 그린 `server/app/*.html`·`*.rsc`·`*.segments/**`, `server/pages/404.html`·`500.html`) | 21 | 빌드 ID 자리를 자리표로 바꾸면 같아진다 |
| `.next/prerender-manifest.json`, `.next/server/server-reference-manifest.js`·`.json` | 3 | 다른 자리가 미리보기 키 셋(`previewModeId` 등)과 `encryptionKey`의 값이다(`compare`가 다른 자리의 글을 `compare.json`에 남긴다). 빌드마다 새로 만드는 키로 읽었다 |
| `.next/trace`, `.next/trace-build` | 2 | 다른 자리가 시각과 걸린 시간이다(같다) |
| `.next/cache/` 아래 | 13 | Turbopack 캐시 파일 열하나와 키 파일 둘(`.previewinfo`, `.rscinfo`). 안은 보지 않았다 |

`public/element.js`와 `public/fonts/`는 입력이 같으면 바이트까지 같았다.

두 짝 모두에서 같았는데 사이트 파일을 바꾸면(A2↔B1) 달라진 파일은 열 개다.

| 사이트 파일이 바꾸는 파일 | 든 값 | 비고 |
|---|---|---|
| `.next/routes-manifest.json` | 허용 출처 | 응답 헤더 `frame-ancestors`의 값 |
| `.next/required-server-files.json`, `.next/required-server-files.js` | 허용 출처, 글자 수 상한 | 설정의 `env`를 옮겨 둔 자리 |
| `.next/server/chunks/ssr/apps_widget_components_pages_WidgetPage_tsx_0748fba._.js` | 허용 출처, 글자 수 상한 | 서버 쪽 번들 |
| `.next/static/chunks/<내용 해시>.js` | 허용 출처, 글자 수 상한 | 브라우저 쪽 번들. 내용이 바뀌어 파일 이름도 바뀐다(`0a-e_pw14q1gl.js` → `2pyoc7cejb-7r.js`) |
| `public/element.js` | 글자 수 상한 | 수 하나다. 손으로 봤다(두 나무의 파일을 Grep으로 찾으니 `function bt(){return 4e3}`과 `function bt(){return 583927}`이었다). 압축기가 4000을 `4e3`으로 쓴다. 허용 출처는 이 파일에 없다 |
| `.next/server/app/page_client-reference-manifest.js` | 없음 | 바뀐 브라우저 쪽 번들의 파일 이름을 가리킨다 |
| `.next/diagnostics/route-bundle-stats.json` | 없음 | 같다. 바이트 수도 함께 바뀐다 |
| `.next/server/app/page.js.nft.json` | 없음 | 파일 해시 |
| 서버 쪽 번들의 `.js.map` | 없음 | 소스 맵 |

그 밖에 미리 그린 페이지 넷(`server/app/index.html`, `index.rsc`, `index.segments/_full.segment.rsc`, `index.segments/__PAGE__.segment.rsc`)도 바뀐 브라우저 쪽 번들의 파일 이름을 품는다. 이 넷은 빌드 ID 때문에 빌드마다 달라지는 쪽에 들어 있다.

코드를 읽은 것: 허용 출처와 글자 수 상한은 `web/apps/widget/next.config.ts`가 사이트 파일에서 읽어(25행 `buildInput(process.env)`) 설정의 `env`(31~35행)와 `headers()`(36~51행)에 넣고, 페이지 안 번들은 `web/apps/widget/tools/element.ts`의 Vite `define`으로 글자 수 상한을 받는다.

### 3. 빌드가 네트워크를 쓰는가

`net_hook.cjs`를 실어 cold 빌드를 돌렸다. 훅은 node의 `net.Socket.connect`와 `dns.lookup`을 바꿔 끼워, 루프백 밖으로 가는 시도를 적고 걸지 않은 채 오류로 끝낸다.

| 갈래 | 본 것 |
|---|---|
| 양성 대조(`net_control.mjs`): 같은 훅을 실은 node가 `http://192.0.2.1/`, `http://widget-build-probe.invalid/`, `https://widget-build-probe.invalid/`에 `fetch` | 셋 다 훅의 기록에 루프백 밖의 연결로 적혔고, 셋 다 응답 없이 훅의 문구가 든 오류(`ECONNREFUSED probe: …`)로 끝났다 |
| 빌드, `NEXT_TELEMETRY_DISABLED=1` | 빌드가 종료 0으로 끝났다. 훅이 프로세스 8개의 스레드 9개에 실렸고(시작 래퍼와 그 워커 스레드, Turbopack의 PostCSS 프로세스, `tsc` 둘, Next의 작업 프로세스 넷) 스레드마다 미끼 연결이 적혔다. 루프백 밖으로 가는 연결과 이름 풀기는 0건, 루프백 연결은 1건(PostCSS 프로세스가 `127.0.0.1`의 임시 포트로)이다 |
| 빌드, 그 변수 없이 `NEXT_TELEMETRY_DEBUG=1` | 같다. 루프백 밖으로 가는 시도 0건. 빌드가 `[telemetry]` 줄 39개를 stderr에 찍었다 |

빌드 두 갈래는 세 번씩 돌렸고 세 번 모두 0건이었다. 양성 대조가 측정으로 선 것은 마지막 실행뿐이다(첫 실행에는 대조가 없었고, 둘째 실행의 대조는 아래 "결과를 본 뒤 바꾼 것"의 까닭으로 측정이 아니었다).

코드를 읽은 것(Next 16.3.6, `web/node_modules/.pnpm/next@16.3.6_*/node_modules/next/dist/`):

- 텔레메트리는 끄지 않으면 `https://telemetry.nextjs.org/api/v1/record`로 `fetch`한다(`telemetry/post-telemetry-payload.js` 17~45행. 제한 5초, 다시 시도 1번, 실패는 삼킨다). `NEXT_TELEMETRY_DISABLED`가 있으면 보내지 않고(`telemetry/storage.js` 231~234행, 290~295행), `NEXT_TELEMETRY_DEBUG`가 있으면 보내는 대신 찍고 돌아간다(같은 파일 213~230행). 그래서 위의 셋째 갈래는 "끄지 않으면 보낼 이벤트가 39건 있다"까지만 보인다.
- 위젯은 `next/font`를 쓰지 않는다(`web/apps/widget`을 `next/font`로 Grep해 0건). 글꼴은 `@fontsource/*` 패키지의 파일을 `public/fonts/`로 복사한다(`web/packages/ui/node/fonts.ts`).
- 네이티브 컴파일러(SWC) 바인딩을 적재하지 못하면 내려받기를 시도하는 길이 있다(`build/swc/index.js` 332~337행, 361~366행). 이 PC에서는 바인딩이 깔려 있어 그 길을 지나지 않았다.

### 4. 크기

산출물(마지막 빌드의 것).

| 무엇 | 크기 | 파일 |
|---|---|---|
| `.next/` 전체 | 66.9MB | 933 |
| `.next/cache/`(Turbopack 캐시. 다음 빌드의 컴파일을 줄인다) | 48.8MB | 15 |
| `.next/`에서 `cache/`를 뺀 것 | 18.1MB | 918 |
| 그 가운데 `static/` | 13.7MB | 784 |
| 그 가운데 `server/` | 3.4MB | 98 |
| `public/element.js` | 0.4MB | 1 |
| `public/fonts/` | 5.6MB | 386 |

의존성. 위젯의 `package.json`에서 뿌리를 골라, pnpm이 깐 폴더에서 의존성과 선택 의존성과 선택이 아닌 peer 의존성을 따라가 닿는 바깥 패키지의 폴더 크기를 더했다. 실제로 적재되는 파일이 아니라 의존 그래프로 닿는 패키지 전체의 크기다.

| 뿌리 | 패키지 | 크기 | 큰 것 |
|---|---|---|---|
| 위젯의 `dependencies`(next, react, react-dom, 워크스페이스 패키지 셋) | 28 | 394.9MB | next 176.2, `@next/swc-win32-x64-msvc` 101.3, `@fontsource/noto-sans-kr` 49.0, lucide-react 33.9, `@img/sharp-win32-x64` 18.9, react-dom 7.7 |
| 위에 `vite`, `@tailwindcss/vite`를 더한 것(지금의 시작 래퍼가 `start`에서도 적재한다) | 55 | 443.8MB | 더해진 것: `@rolldown/binding-win32-x64-msvc` 19.8, `lightningcss-win32-x64-msvc` 두 판 9.1씩, `@tailwindcss/oxide-win32-x64-msvc` 3.0, vite 2.3 |
| 위에 빌드가 import하는 개발 의존성을 더한 것(`@tailwindcss/postcss`, `tailwindcss`, `typescript`, `@types/node`, `@types/react`, `@types/react-dom`) | 63 | 470.7MB | 더해진 것: typescript 22.5, `@types/node` 2.5 |
| 위젯의 개발 의존성 전부 | 128 | 503.0MB | 더해진 것: playwright-core 12.8, playwright 4.9 |
| `web/node_modules` 전체(워크스페이스 뿌리의 개발 의존성까지) | | 636.8MB | 파일 30,477개 |

Next가 빌드 때 적어 둔 실행 추적 목록(`.next/**/*.nft.json`)이 `.next` 밖에서 가리키는 파일은 906개 14.0MB다(next 11.4, react-dom 1.4, sharp 0.6). 이 목록의 파일만으로 서버가 선다는 것은 재지 않았다.

코드를 읽은 것:

- 시작 래퍼 `web/apps/widget/tools/start.ts`는 35행에서 `./element.ts`를 import하고, `element.ts`는 29~30행에서 `@tailwindcss/vite`와 `vite`를 import한다. 그래서 `node tools/start.ts start`는 빌드를 하지 않아도(75행 `prepare: command === "dev"`) 그 두 개발 의존성을 적재한다. 둘째 줄의 뿌리가 그것이다.
- 빌드가 import하는 개발 의존성은 `vite`와 `@tailwindcss/vite`(`tools/element.ts`), `@tailwindcss/postcss`(`postcss.config.mjs`), `tailwindcss`, `typescript`다.
- `next build`의 타입 검사는 `tsc --project <위젯의 tsconfig.json>`을 따로 띄워 프로젝트 전체를 본다. Next 16.3.6의 기본값이 `experimental.useTypeScriptCli: true`이고(`server/config-shared.js` 257행) 그 길은 프로젝트 전체를 검사한다고 적혀 있다(`lib/verify-typescript-setup.js` 209~220행). 그 `tsc` 프로세스가 뜬 것은 손으로 봤다(`net` 단계의 훅 기록 `net-telemetry-off.jsonl`의 `loaded` 줄에 `tsc --showConfig --project`와 `tsc --project …/apps/widget/tsconfig.json`이 있다). 위젯의 `tsconfig.json`은 `**/*.ts`, `**/*.tsx`, `.storybook/**/*`를 들고 `node_modules`와 `visual`만 뺀다. 시험·스토리·e2e 파일이 그 안에 있고, 그 파일들이 vitest, `@testing-library/*`, msw, `@playwright/test`, storybook, `@agent-os/e2e-stack`을 import한다(Grep으로 파일 36개에서 61건. 그 가운데 둘은 tsconfig가 빼는 `visual/` 아래다). 그래서 타입 검사를 지금대로 두면 빌드에 그 패키지들의 타입도 필요할 것으로 본다(어림. 그 패키지 없이 빌드를 돌려 보지 않았다). 그러면 빌드에 드는 것은 셋째 줄(470.7MB)이 아니라 마지막 줄(636.8MB)에 가깝다.

### 5. 관리 화면 빌드 시간(견줄 값)

`web/apps/admin`의 `next build`를 `.next`를 지운 채 세 번 돌렸다. `AGENT_OS_UPSTREAM`은 주지 않아 기본값(`http://127.0.0.1:8000`)이다.

| 회차 | 전체 | 컴파일 | 타입 검사 | 페이지 | 직전 1초의 CPU 사용률 |
|---|---|---|---|---|---|
| 첫 실행의 한 번 | 26.7초 | 9.9초 | 9.1초 | 3.6초 | 71% |
| 둘째 실행의 첫째 | 31.0초 | 9.4초 | 13.0초 | 7.3초 | 32% |
| 둘째 실행의 둘째 | 40.6초 | 11.5초 | 17.0초 | 9.6초 | 99% |

관리 화면의 첫 실행, 위젯의 셋째 실행(cold 17.0~20.0초), 관리 화면의 둘째 실행 차례로 이어서 돌았고 그 사이에 이 프로브의 다른 단계는 돌지 않았다. 세 회차 모두 그 위젯 cold 셋보다 길었다.

## 해석과 그 갈래

- "두 번째 빌드는 컴파일만 줄인다"고 읽었다. 컴파일 구간은 세 실행 모두에서 warm이 cold보다 짧았고 범위가 겹치지 않았다. 전체 시간은 첫째 실행에서 warm이 cold보다 길었는데, 그 실행은 cold 셋을 먼저 돌고 warm 셋을 뒤에 돌아 PC의 부하가 바뀐 것과 가를 수 없었다. 그래서 번갈아 돌게 고쳐 다시 돌렸고(아래), 번갈아 돈 두 실행에서는 warm 전체가 바로 앞 cold보다 매번 짧았다. 줄어든 것이 `.next/cache/turbopack` 덕이라는 것은 어림이다(그 폴더만 지우거나 남기는 갈래를 두지 않았다).
- "사이트 파일이 바꾸는 파일"은 입력이 같은 짝 둘에서 한 번도 달라지지 않았고 입력이 다른 짝에서 달라진 파일이다. 가끔만 달라지는 파일이 섞였을 수 있다는 해석은 짝 둘로만 갈랐다. 값이 든 파일 여섯은 B의 값(허용 출처 문자열, 583927)이 글자로 들어 있는지를 함께 봐서, 우연히 달라진 것과 갈린다. 표지로 두 나무의 `routes-manifest.json`이 저마다 자기 사이트 파일의 출처를 품었는지 본다.
- "node 쪽에서 밖으로 가는 시도가 없다"고 읽었다. 훅이 그런 시도를 적지 못한다는 해석은 양성 대조(같은 훅 아래의 `fetch` 셋이 적히고 막혔다)와 스레드마다의 미끼로 갈린다. 훅이 아예 보지 못하는 길(아래 "재지 못한 것")은 갈리지 않는다.
- 4번의 의존성 크기는 의존 그래프를 따라간 값이다. "이만큼이 있어야 돈다"가 아니라 "이 뿌리를 pnpm으로 깔면 이만큼이 깔린다"로 읽는다. 표지로 뿌리가 모두 풀렸는지, next가 묶음에 들었는지, 묶음이 뿌리를 더할수록 커지는지를 본다.

## 결과를 본 뒤 바꾼 것

- 빌드 시간의 차례. 첫째 실행은 cold 셋 뒤에 warm 셋이었다. warm 전체가 cold보다 길게 나온 것을 보고, 부하의 변화와 가르려고 cold와 warm을 번갈아 돌게 바꾸고 회차 직전 1초의 CPU 사용률을 적게 했다. 첫째 실행의 수는 버리지 않고 위 표에 함께 뒀다. CPU 사용률은 적기만 하고 회차를 거르는 데 쓰지 않는다.
- 맞대기의 규칙. 처음 판은 설명되지 않는 차이를 손으로 읽었다. 그 뒤 넷을 더했다. 파일 경로의 빌드 ID를 자리표로 바꾼다. 글자 수 상한은 십진 꼴과 압축기가 쓰는 지수 꼴(4000 → `4e3`)을 함께 찾는다. 입력이 같은 짝을 하나(A1↔A2)에서 둘(B1↔B2 추가)로 늘린다. 차이를 "빌드마다", "값이 든", "따라 바뀐"으로 가른다. 한 번은 고친 판이 나무마다 자기 규칙만 써서 한쪽의 무관한 `4e3`을 자리표로 바꿔 짝짓기를 깨뜨렸고, 두 나무의 규칙을 합쳐 양쪽에 쓰게 고쳤다. 위 표는 마지막 판의 출력이다.
- 의존성 묶음. 처음 판은 선택 peer 의존성까지 따라가 next의 선택 peer인 `@playwright/test`가 첫째 줄에 들었다(33개 414MB). 선택 peer는 따라가지 않게 바꿨다(28개 394.9MB). 워크스페이스 패키지에서만 `dist` 같은 폴더를 건너뛰게도 고쳤다(바깥 패키지의 `dist`는 센다).
- 네트워크의 양성 대조는 빌드 두 갈래의 결과(0건)를 본 뒤에 더했다. 대조의 첫 판은 첫 대상이 `http://192.0.2.1:9/`였는데, `fetch`가 9번 포트를 연결 전에 거절해(`bad port`) 훅에 닿지 않았고 그 회차는 측정 아님으로 세어져 종료 코드 1이었다. 포트를 기본값으로 바꿔 다시 돌렸다.
- 관리 화면은 한 번 돌린 뒤 두 번을 더 돌렸다. 위젯의 셋째 실행과 같은 때의 값과 견주려는 것이다.

## 재지 못한 것

- 리눅스 컨테이너에서의 모든 값. 이 프로브는 Windows에서만 돌았다.
- 개발 의존성 없이(또는 시험 쪽 패키지 없이) 빌드가 되는지. 4번의 "타입 검사에 시험 쪽 타입이 필요할 것"은 어림이다.
- 네트워크가 실제로 없는 자리의 빌드. 훅은 node의 `net`과 `dns.lookup`만 본다. Turbopack(Rust)이 직접 여는 소켓, node가 아닌 프로세스, UDP, `dns.resolve*`는 보지 못한다.
- 텔레메트리를 끄지 않은(디버그도 아닌) 빌드. 훅이 놓치면 바깥 서비스로 나가는 요청이라 돌리지 않았다. 네트워크가 없을 때 그 빌드가 얼마나 늦어지는지도 모른다.
- `start`. 띄우지 않았다. 사이트 파일을 바꾼 뒤 다시 빌드하지 않고 `start`만 하면 무엇이 옛 값으로 남는지도 보지 않았다.
- 빌드가 쓰는 메모리와, CPU 수를 줄인 자리(컨테이너의 CPU 제한)의 시간.
- 막 받은 이미지의 첫 빌드. cold는 앱 폴더의 산출물만 지운 것이라 운영체제의 파일 캐시와 node의 컴파일 캐시는 그대로다.
- Next의 실행 추적 목록(14.0MB)만 두고 서버가 서는지, `output: "standalone"`으로 지었을 때의 크기.

## 이 PC라서 리눅스 컨테이너와 다를 수 있는 것

따로 적지 않은 한 어림이다.

- 시간 전부. 파일 시스템, 백신, CPU 수, 함께 도는 일이 다르다. 여기서도 같은 빌드가 부하에 따라 두 배 넘게 흔들렸다.
- 플랫폼 패키지의 크기. 4번의 묶음에는 Windows용 네이티브 패키지가 들어 있다. 레지스트리가 적은 푼 크기를 손으로 봤다(`pnpm view <패키지>@<판> dist.unpackedSize`. 바이트를 MB로 옮겼다).

  | 패키지 | Windows(여기 깔린 것) | 리눅스 x64 |
  |---|---|---|
  | `@next/swc-*` 16.3.6 | win32-x64-msvc 101.3MB | linux-x64-gnu 92.3MB, linux-x64-musl 90.4MB |
  | `@img/sharp-*` 0.35.5 | win32-x64 18.9MB | linux-x64 0.4MB와 그것이 끌어오는 `@img/sharp-libvips-linux-x64` 1.3.4 17.8MB |
  | `@rolldown/binding-*` 1.2.11 | win32-x64-msvc 19.8MB | linux-x64-gnu 18.3MB |
  | `lightningcss-*` 1.33.0 | win32-x64-msvc 9.1MB | linux-x64-gnu 9.6MB |
  | `@tailwindcss/oxide-*` 4.3.3 | win32-x64-msvc 3.0MB | linux-x64-gnu 2.9MB |

  Windows 쪽 두 값(`@next/swc-win32-x64-msvc` 101.3MB, `@img/sharp-win32-x64` 18.9MB)은 같은 명령으로 본 레지스트리 값과 디스크에서 센 값이 같았다. 이 표대로면 리눅스의 묶음은 여기보다 10MB쯤 작다(어림. 리눅스에서 깔아 세지 않았다).
- `.next/diagnostics/route-bundle-stats.json`의 경로 구분 문자(여기서는 `\\`).
- 산출물의 파일 목록과 2번의 가름은 같을 것으로 보지만 리눅스에서 돌려 보지 않았다. 내용 해시가 든 파일 이름은 다를 수 있다.
- pnpm의 하드 링크. 여기서는 스토어와 `node_modules`가 같은 드라이브라 하드 링크였다. 이미지 안에서는 깔리는 방식에 따라 디스크 크기가 다르게 보일 수 있다.

## `probes/README.md` 표에 넣을 줄

이 폴더 위의 `probes/README.md`는 이 프로브가 만들지 않았다(파일을 이 폴더 아래에만 두기로 했다). 표를 만들 때 넣을 줄이다.

| 프로브 | 무엇을 재는지 | 어디가 근거로 드는지 | 다시 돌 때 필요한 것 | 판 |
|---|---|---|---|---|
| `widget_build/`(`measure.mjs`, `phases.mjs`, `net_hook.cjs`, `net_control.mjs`, `sites_b.toml`) | 위젯 빌드의 시간(cold·warm, 구간), 사이트 파일이 바꾸는 산출물, 빌드의 node 쪽 네트워크 시도, 산출물과 의존성의 크기, 관리 화면 빌드 시간 | release-image 설계 인터뷰(ADR 0056의 결정 "위젯 이미지") | node 24, pnpm 11, 깔린 `web/node_modules`(없으면 `install` 단계), 저장소 밖의 `--out` 폴더 | Windows 10, node v24.19.0, pnpm 11.24.0, Next 16.3.6, Vite 8.3.1, TypeScript 5.9.3 |
