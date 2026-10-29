# design-card-build 프로브

명세(`.scratch/design-card-build/spec.md`)가 근거로 드는 측정이다. 규약은 `docs/agents/issue-tracker.md`의 "프로브와 근거"이고 짓는 규칙은 `.claude/rules/probes.md`다.

저장소 루트에서 돈다. `pnpm -C web install`을 한 번 한 기계여야 한다. 작업 폴더는 아직 없는 절대 경로를 준다(프로브는 어떤 폴더도 지우지 않는다).

```sh
node .scratch/design-card-build/probes/card_build.mjs <작업 폴더의 절대 경로>
node .scratch/design-card-build/probes/vite_cli.mjs <작업 폴더의 절대 경로> <card_build.mjs의 작업 폴더>
pnpm -C web exec tsc -p ../.scratch/design-card-build/probes/tsconfig.json
node .scratch/design-card-build/probes/vite_cli_tool.mts <작업 폴더의 절대 경로> <card_build.mjs의 작업 폴더>/bundle.js
node .scratch/design-card-build/probes/font_route.mjs <작업 폴더의 절대 경로>
PYTHONUTF8=1 uv run python tools/mutate.py .scratch/design-card-build/probes/assemble_mutations.toml [번호 ...]
PYTHONUTF8=1 uv run python tools/mutate.py .scratch/design-card-build/probes/upload_plan_mutations.toml [번호 ...]
```

| 파일 | 재는 것 | 근거로 드는 자리 | 다시 돌 때 | 잰 판 |
|---|---|---|---|---|
| `card_build.mjs` | 저장소가 이미 가진 도구(디자인 시스템 패키지의 vite와 Tailwind CLI)만으로 Design System 형식의 컴포넌트 묶음(전역 `AgentOsUi`의 IIFE 하나, 빌드 CSS)과 글꼴, 컴포넌트 카드의 장면(showcase 스토리)을 지을 수 있는지. 지은 카드를 페이지와 같은 차례로 실은 문서를 chromium에 띄워 오류 없이 그려지는지, 웹 편집을 흉내 낸 층 없는 토큰이 묶음 CSS의 층 안 디자인 토큰을 이기는지, 페이지가 붙이는 `data-theme`·`data-mode`와 코드 선택자의 어긋남이 색을 바꾸는지. 회차와 표지는 파일 머리 주석이 적는다 | 명세 Implementation Decisions의 짓기·카드·색·다크 테마·글꼴 항목과 Testing Decisions | `pnpm -C web install`, chromium(Playwright가 받은 것), 받은 사본 `received/page-tokens.css`. 커밋 `35028cba`가 저장소에 있어야 한다(글꼴 이름을 그 커밋의 `.design-sync/upload-output.json`과 견준다) | vite 8.3.1, rolldown 1.2.11, @tailwindcss/cli 4.3.3, React·ReactDOM 19.3.0, Node 24.19.0, Playwright 1.63.0, chromium 153.0.8010.12. 저장소 쪽은 작업 트리를 읽고, 아래 결과는 `8e43dd2c`에서 `web/packages/ui` 아래 커밋하지 않은 변경 0으로 잰 것이다(요약의 `head`·`uiUncommitted`) |
| `vite_cli.mjs` | 올리기 도구(`web/tools/sync-design-system/`)는 vite를 import할 수 없다(vite는 디자인 시스템 패키지의 개발 의존뿐이고 `web/node_modules/vite`가 없다). 그래서 도구가 vite 설정을 import 없는 글로 지어 파일에 쓰고, 패키지 자리에서 vite CLI(`pnpm -C web/packages/ui exec vite build --config <파일>`)와 Tailwind CLI(`pnpm exec tailwindcss`)를 부르는 길이 `card_build.mjs`가 JS API로 지은 것과 같은 묶음·장면·빌드 CSS·글꼴을 내는지. 장면은 Button 하나만 짓고, 견주기의 양성 대조로 Alert 카드와 견준다. 회차와 표지는 파일 머리 주석이 적는다 | 명세 Implementation Decisions의 짓기 항목(새 의존 없이 짓는 길) | `pnpm -C web install`, 같은 커밋에서 돈 `card_build.mjs`의 작업 폴더 | vite 8.3.1, @tailwindcss/cli 4.3.3, Node 24.19.0, pnpm이 `web/packages/ui`에서 띄운 CLI. 저장소 쪽은 작업 트리를 읽고, 아래 결과는 `8e43dd2c`에서 잰 것이다(요약의 `head`). 견준 산출은 같은 커밋의 `card-run-5` |
| `vite_cli_tool.mts`, `tsconfig.json` | `vite_cli.mjs`의 길을 올리기 도구가 쓸 모양 그대로 지나는지(소비 지점). TypeScript 파일이 vite를 import하지 않고 설정을 글로 지어, 셸 없이 `process.execPath`로 패키지의 `node_modules/vite/bin/vite.js`를 패키지 자리에서 띄운다. `tsconfig.json`은 `web/tsconfig.json`(strict)을 이어받아 이 파일만 든다. 공백이 든 작업 폴더를 주면 셸 없이 넘긴 인자가 갈리지 않는지도 본다. 회차와 표지는 파일 머리 주석이 적는다 | 명세 Implementation Decisions의 짓기 항목 | `pnpm -C web install`, 같은 커밋에서 돈 `card_build.mjs`의 `bundle.js` | TypeScript 5.9.3(`web`의 `tsc`), `@types/node` 24.19.0, Node 24.19.0, vite 8.3.1. 아래 결과는 `8e43dd2c`에서 잰 것이다 |
| `received/page-tokens.css` | 디자인 시스템 아티팩트 판 `1793146503-9e85`의 `tokens.css`를 받은 그대로 둔 사본(27,857바이트, sha256 `0680bd4c2a13ba8d2af7c151993980295b2d83ace00b4799d82e2d7712e06354`). 페이지가 저장할 때 `tokens.json`에서 다시 짓는 파일이다 | `card_build.mjs`의 카드 문서가 페이지의 토큰 CSS 자리에 싣는다 | 바꾸지 않는다. 다시 받으면 판과 해시를 이 줄에 고친다 | 판 `1793146503-9e85` |
| `font_route.mjs` | 짓기 시험이 카드를 싣는 길(문서의 기준 주소가 산출 폴더의 `components/<이름>/preview.html`)에서 묶음 CSS의 글꼴 주소가 `../../fonts/`면 Noto Sans KR이 실리고 `../fonts/`로 바꾸면 글꼴 오류가 나는지. `file://` 문서와 요청 가로채기(`route`)로 산출 폴더를 내준 `http` 문서의 두 길에서 본다. 짓기 명령(`assemble`)을 스스로 한 번 돌린다. 회차와 표지는 파일 머리 주석이 적는다 | 티켓 01의 "글꼴 대조를 먼저 본다"와 짓기 시험(`web/tools/sync-design-system/assemble.test.ts`)이 고른 `route` 길 | `pnpm -C web install`, chromium(Playwright가 받은 것). 짓기 명령이나 시험의 싣는 길을 바꿨을 때 | Playwright 1.63.0, chromium 153.0.8010.12, Node 24.19.0. 아래 결과의 `HEAD`와 커밋하지 않은 변경 수는 그 절이 적는다 |
| `assemble_mutations.toml` | 짓기 명령의 시험(`web/tools/sync-design-system/assemble.test.ts`)이 단언마다 빨개지는지. 변이마다 짓기나 판정의 줄 하나(둘인 것은 명령 안의 같은 판정이 짓기를 막지 않게 함께 끈다)를 바꾸고 그 사례로 좁힌다(`-t`). 티켓 02의 사용 규약·산출 밖 변이는 판정이 맞대는 두 쪽(원본이 드는 이름, 지은 묶음) 가운데 한 쪽을 바꾼다. 대개 시험이 읽는 저장소 원본(`.design-sync/conventions.md`, `.design-sync/foundations/`, 디자인 시스템 패키지의 컴포넌트와 스토리)이고, 묶음 머리의 목록을 겨누는 51은 그 목록을 짓는 `assemble.ts`다. 표지는 고른 단언이 실패할 때만 나오는 실패 머리나 diff의 `+` 줄이다 | 티켓 01·02의 "변이" | 짓기 명령(`assemble.ts`)이나 그 시험을 고쳤을 때. 변이 하나에 짓기 한 번이 든다 | vitest 5.0.2(`web`의 node 프로젝트). 아래 결과의 판은 그 절이 적는다 |
| `page_diag_card.html` | 실제 Design System 페이지가 카드 문서에 무엇을 싣는지. `components/Diag/preview.html`로 올리면 카드 안에서 React 판, `data-theme`·`data-mode`, `color-scheme`과 바탕, 글꼴의 실림과 오류, 글꼴 요청 주소, 문서의 기준 주소, 스타일시트 `<link>`·`<style>`·스크립트 주소를 글로 찍는다. 둘째 줄이 `DIAG v2 done`인 회차만 측정이다(`DIAG 기다리는 중`이면 아직 돌지 않았다). v2는 셋째 줄에 `--gray-50`과 `--bg`의 계산값을 찍는다. 판 4~7은 그 줄이 없는 v1(`DIAG v1 done`)이었다 | 명세 Implementation Decisions의 글꼴·다크 테마·배너·React 항목 | 임시 Design System 아티팩트에 `card_build.mjs`의 `stage/` 배치와 함께 올리고 앱 안 브라우저로 Components 절을 연다. 카드 iframe은 다른 출처라 도구가 안을 읽지 못해 화면을 찍어 읽는다(손으로 봤다). 아래 "실제 페이지" 절의 차례대로 판을 올린다 | 형식 판 release `1793156745-17fb`, 페이지가 실은 React·ReactDOM 18.3.1(jsDelivr UMD). 묶음과 카드는 `card-run-5`(`8e43dd2c`)의 `stage/` |
| `upload_plan_mutations.toml` | 티켓 03의 변이 표 스물여섯. 올리기 계획(`web/tools/sync-design-system/upload.ts`)의 첫 정식 올리기(이번 산출의 정식 카드, 받은 기록의 정식 카드, 기록이 없을 때의 sha256 목록, `tokens.json`을 보내는 갈래, 그 갈래가 앞 시도의 보낸 갈래보다 앞서는 것), 목록만 옛것일 때(기록과 맞대기, 지금 절차의 기록에 없는 지난 경로, 기록이 없으면 목록대로, 옛 별칭 48개), 나누기(기록·색인의 경로, 기록·색인의 바이트, 지울 경로, `_ds_sync.json`의 자리, 들지 않는 파일의 오류 종류, 남은 하나를 중간 몫으로 보내는 길, 첫 몫이 기록만 싣는 길, 첫 몫이 남기는 기록의 경로와 바이트), 보낼 색인(`libraries`, `global`, 이미 있는 `upgraded`, 첫 정식 올리기가 아닐 때)과 `record index` 명령(묶음 찾기, 계획의 `firstCanonical` 읽기, 색인 한도)을 겨눈다. 시험은 구현 전에 함수와 칸이 없어 빨갰을 뿐이고 옛 별칭 사례는 구현 전부터 초록이라, 변이마다 판정의 줄 하나를 바꾸고 `-t`로 사례 하나를 좁혀 빨개지는지 본다. 표지는 고른 단언이 실패할 때만 나오는 실패 머리나 차이 줄이고, 처음 고른 넷이 출력에 없어 변이를 손으로 넣어 받은 실패 출력에서 다시 골랐다(아래 결과) | 티켓 03의 "올리기 시험"과 "변이"(원칙 II) | `upload.ts`·`record.ts`를 고치면 `--check`로 원문을 보고 번호로 다시 돈다. 원문이 없거나 기대와 다르거나 표지가 없으면 1로 끝난다 | `f6df25c8` 위의 작업 트리, Node 24.19.0, vitest 5.0.2 |

## 2026-10-29 결과: `upload_plan_mutations.toml` (티켓 03)

- 첫 실행은 "변이 22 중 어긋남 4"였다. 넷 다 빨강이었고 표지만 없었다. 14(`_ds_sync.json`의 자리)는 첫 판의 변이가 그 파일을 앞뒤에 두 번 넣어 다른 단언(`not.toContain`)이 빨개졌다. 앞 걸러내기와 뒤 붙이기를 함께 끄는 편집 둘로 바꿨다. 19는 실패 머리가 `to not have property "upgraded"`였고, 20·21은 `toMatchObject`의 차이 줄이 받은 쪽 `+   "libraries": false,`·`+   "upgraded": false,`였다. 변이를 손으로 넣어(커밋하지 않은 스크래치 스크립트로 원문을 바꾸고 `pnpm -C web exec vitest run --project node <시험 파일> -t <사례>`) 받은 출력에서 골랐다.
- 고친 표 전부를 다시 돌려 "변이 22 모두 기대대로"였다(도구가 찍은 줄). 기준선은 모두 초록이었다. 이 절의 번호는 아래 절에서 넷을 더하기 전의 것이다.

## 2026-10-30 결과: 셀프 리뷰 뒤 `upload_plan_mutations.toml` (티켓 03)

- 셀프 리뷰 두 축이 나누기가 남은 큰 파일 하나를 마지막 몫에 넣지 못하면 중간 호출에 들 수 있어도 `limit` 오류로 멈춘다고 짚었다. 남은 하나를 중간 몫으로 보내는 길과 첫 몫이 기록만 싣는 길을 더하고, 두 길을 겨누는 변이와 명세 축이 짚은 첫 몫의 예약(경로 하나, `RECORD_LIMIT`)을 따로 끄는 변이 둘을 15번 뒤에 더했다. 두 길의 시험은 고치기 전에 그 `limit` 오류로 빨갰다(`pnpm -C web exec vitest run --project node tools/sync-design-system/upload.test.ts -t <사례>`, 손으로 봤다). 오류 종류 변이(15)는 들여쓰기가 바뀐 원문으로 옮겼다.
- 표 전부를 돌려 "변이 26 모두 기대대로"였다(도구가 찍은 줄, 기준은 `f6df25c8` 위의 작업 트리).
- 재지 않은 것: 마지막 몫을 비우지 않게 하나를 남기는 조건과 한 파일이 한 호출에 들지 않을 때 멈추는 조건(표 머리 주석).

## 받은 사본과 카드의 토큰 CSS가 다른 자리

판 `1793146503-9e85`의 `artifact-type/app.js`를 읽었다. 파일 `tokens.css`는 `KO`가 머리 주석 한 줄 뒤에 `K$(tokens, {usageComments, styleVars, fontSrc})`를 붙여 짓는다. 카드 iframe의 토큰 CSS는 `VT`가 `K$(tokens, {fontFaces: false})` 뒤에 `Hdt`의 `html{color-scheme:<모드>}`와 `html,body{background:transparent!important}`(그리고 배경색을 받았으면 `html{background:…!important}`)를 붙여 짓는다. 그래서 받은 사본은 카드의 것과 글자 그대로 같지 않다. 사본에만 있는 것은 쓰임 주석과 `:root`의 글자 꼴 변수(`styleVars`)이고, 사본에 `@font-face`는 0개다. 테마 블록 여덟(`:root, [data-theme="nokcheong-light"]`와 테마마다의 `[data-theme="<id>"]`)의 색 토큰 선언은 두 길이 같은 `K$`로 낸다(코드 읽기). 이 프로브의 카드 문서는 `Hdt`의 두 줄을 싣지 않는다. 그래서 아래 결과는 컴포넌트 요소의 색만 말하고, 투명한 `html,body` 뒤에 비치는 페이지의 바탕은 말하지 않는다.

## 2026-10-28 결과

셋째 실행(`card-run-3`): 회차 75, 측정 75, 측정 아님 0. 종료 0. 아래 항목의 수는 따로 적지 않으면 `card_build.mjs`가 요약 JSON(`summary.json`)에 찍은 것이다.

- `bundle`: 17,112바이트. `AgentOsUi` 대입이 있고 `require(`·`import` 문·`react.transitional.element`가 0이다. `</script`와 `<!--`도 0이라 페이지가 인라인 `<script>`로 실어도 끊기지 않는다.
- `css`: 23,482바이트. `@layer theme`과 `--accent-600:`이 있고 `@font-face`는 0이다. 글꼴은 묶음 CSS에 들지 않는다.
- `fonts`: 글꼴 파일 772개를 냈다. 지난 산출 목록(커밋 `35028cba`)의 `fonts/` 770개와 이름이 모두 같다. 더 나온 2개는 `assetsInlineLimit: 0` 때문으로 본다. 지난 산출의 `fonts.css`가 data URL 2개를 품은 것을 손으로 봤다(판 `1793146503-9e85`에서 받은 `fonts/fonts.css`, 268,002바이트를 `grep -o "data:font/[a-z0-9]*"`로 셌다. 둘 다 `woff2`다. 그 사본은 세션 스크래치패드의 임시 사본이라 커밋하지 않았다). 이 해석을 가르는 갈래(인라인 한도를 기본값으로 둔 빌드)는 다섯째 실행의 `stage` 회차다(아래).
- `scene:<컴포넌트>` 아홉: 모두 지어졌고 3.6~12.6KB(카드 한도 256KB 아래)이며 `AgentOsUi`를 부른다.
- `render:<컴포넌트>` 아홉: 장면 11개가 모두 그려졌다(Button 2, Alert 2, 나머지 1). 페이지 오류와 콘솔 오류는 0이다.
- `cascade:<컴포넌트>:edit` 아홉: `#root` 아래 모든 요소가 빨갰다(Button 18/18, Card 14/14, Icon 20/20, IconButton 7/7, Progress 10/10, StatusBadge 28/28, Alert 40/40, Switch 26/26, TextField 16/16).
- `cascade:<컴포넌트>:layered` 아홉: 빨간 요소가 모두 0이다.
- `mode:<컴포넌트>` 아홉: 받은 토큰 CSS와 `nokcheong-dark`에서 `data-mode`를 `light`와 `dark`로 바꾸어도 색이 다른 요소는 0이다.
- `mode-bare:<컴포넌트>` 아홉: 토큰 CSS 없이 `nokcheong`에서 `data-mode`만 바꾸면 모든 요소의 색이 다르다.
- `dark-match:<컴포넌트>` 아홉: 받은 토큰 CSS와 `nokcheong-dark`에 `data-mode="light"`로 띄운 색이, 토큰 CSS 없이 코드 선택자(`nokcheong`, `dark`)로 띄운 색과 모든 요소에서 같다.
- `theme-match:<컴포넌트>` 아홉: 받은 토큰 CSS와 페이지 id `guncheong-light`의 색이 토큰 CSS 없는 코드 선택자 `guncheong`의 색과 모든 요소에서 같다. 토큰 CSS 없이 페이지 id로 띄우면 요소 7~30개(컴포넌트마다)의 색이 코드 선택자와 다르다.

해석과 갈래:

- 층 밖이 이긴다. `edit`와 `layered`는 같은 덮기를 싣고 덮기가 층 밖이냐 묶음 CSS보다 먼저 선언한 층(`@layer page`) 안이냐만 다르다. `edit`의 빨강은 덮기가 실제로 요소 색에 닿는다는 양성 대조다. 카드 문서에서 토큰 CSS는 묶음 CSS보다 먼저 실리므로, 뒤에 실린 쪽이 이긴다는 해석이면 `edit`도 빨갛지 않았을 것이다. 그래서 페이지 쪽 토큰이 이기는 까닭은 층 밖이라는 데 있다는 해석이 선다.
- 카드 안의 컴포넌트 색은 `data-mode`를 따르지 않고 토큰 CSS를 따른다. `mode-bare`가 이 문서에서 `data-mode`가 색을 바꿀 수 있다는 양성 대조이고, 같은 문서에 받은 토큰 CSS만 더한 `mode`에서 차이가 0이다. `dark-match`는 그 색이 코드의 다크 색과 같다는 것까지 보인다. 한국어 테마 이름 때문에 페이지가 다크 테마에 `data-mode="light"`를 붙여도 컴포넌트 요소의 색은 다크다. 위 절대로 이 프로브는 `html,body`를 투명하게 하는 페이지의 줄을 싣지 않아, 바탕이 다크로 보이는지는 재지 않았다.
- 페이지 id와 코드 선택자의 어긋남은 토큰 CSS가 덮는다. `theme-match`의 토큰 CSS 없는 페이지 id 갈래가, 어긋남이 토큰 CSS 없이는 색을 바꾼다는 양성 대조다. 토큰 CSS를 실은 갈래는 코드 선택자의 색과 같다. `card_build.mjs`는 녹청 다음 테마 하나(군청 라이트)만 잰다.
- `card_build.mjs`의 카드 문서는 React 19.3.0 전역을 싣는다. 페이지와 화면(Design) 형식은 React 18.3.1 UMD를 싣는데, 그 사본이 이 저장소와 이 PC에 없다(`C:\project` 아래를 `find`로 손으로 찾았다). 묶음과 장면이 React 19 jsx-runtime의 요소를 만들지 않는 것(`bundle`의 `react.transitional.element` 0)은 그 프로브가 단언하지만, React 18 위에서 그려지는지는 재지 않았다. 컴포넌트에 React 19에만 있는 API(`use(`, `useActionState`, `useFormStatus`, `useOptimistic`)가 없다는 것은 `web/packages/ui/src`를 손으로 grep했다. 그래서 React 18에서도 그려질 것은 어림이다. `Card`처럼 `div`의 속성을 그대로 받는 컴포넌트에 `ref`를 넘기면 React 18은 `forwardRef` 없는 함수 컴포넌트의 `ref`를 버리는데, 컴포넌트 스토리 파일에 `ref`와 `useRef`가 없는 것을 손으로 grep했다.

결과를 본 뒤 바꾼 것: 첫 실행은 글꼴 빌드 옵션(`cssCodeSplit`), 가상 엔트리를 받지 않는 lib 모드, 작업 폴더의 엔트리에서 `react`를 찾지 못한 것으로 측정 아님 회차가 있어 종료 1이었다. 도구를 부르는 법만 고쳤고 표지는 바꾸지 않았다. 둘째 실행(48회차, 종료 0)의 `mode` 결과를 본 뒤 그 양성 대조 `mode-bare`와 `dark-match`·`theme-match`를 더했다. 이미 있던 회차의 표지와 판정은 바꾸지 않았다.

재지 않은 것(이 실행): 실제 페이지의 Components 절에 카드가 뜨는지, 페이지가 글꼴을 인라인으로 실을 때 묶음 CSS의 상대 글꼴 경로가 풀리는지, 이름을 바꾼 다크 테마에서 페이지의 바탕과 모드가 다크인지, 색인의 `upgraded`로 배너가 사라지는지, 다시 그리기가 목업의 옛 사본을 지우는지. 앞의 넷은 아래 절에서 손으로 봤다.

다섯째 실행(`card-run-5`)은 `stage` 회차를 더해 회차 76, 측정 76, 종료 0이었다. `stage`는 카드 9, 카드 README 9, 글꼴 770개(13,421,708바이트), 글꼴 주소 가운데 `../fonts/`도 data URL도 아닌 것 0(프로브는 data URL을 이 셈에서 뺐다. 같은 묶음 CSS의 data URL 둘은 아래 둘째 문단이 손으로 셌다), `components/bundle.css` 296,490바이트, 테마 이름 여덟이 모두 ` (Light)`나 ` (Dark)`로 끝난다. 나머지 회차의 결과는 셋째 실행과 같다. `stage`가 묶음 CSS에 쓰는 `../fonts/`는 아래 절의 판 4에서 실제 페이지가 풀지 못했다. 그 판의 입력으로 남기려고 프로브는 고치지 않았고, 판 5는 올리기 전에 `sed`로 바꿨다.

`stage`는 글꼴을 vite의 인라인 한도 기본값으로 지었다(셋째 실행의 `fonts` 회차는 한도 0이다). 그 글꼴 파일 770개의 이름을 지난 산출 목록(커밋 `35028cba`)의 `fonts/` 770개와 `diff`로 맞대니 차이가 없었다. 묶음 CSS의 글꼴 주소는 파일을 가리키는 것 770건과 `data:font/woff2` 2건이었다(판 9에서 Artifact 도구의 `read`로 받은 `components/bundle.css`를 `grep -o`로 셌다. 판 5의 `sed`는 파일 주소만 바꿨다). 그래서 한도 0에서 더 나온 2개는 기본 한도에서 data URL로 품는 작은 글꼴이라는 셋째 실행의 해석이 선다. 이 둘은 2026-10-28 셀프 리뷰를 반영한 세션이 손으로 봤다(일지 `2026-10-29-13`의 셀프 리뷰 절).

여섯째 실행(`card_build.mjs`, 작업 폴더 `card-run-timed`, 같은 세션, `HEAD` `06a8f85b`, `web/packages/ui` 아래 커밋하지 않은 변경 0)은 회차 76, 측정 76, 종료 0이었다. 한 바퀴의 걸린 시간은 그 명령을 셸의 `time`으로 감싸 손으로 봤고 69.1초(real)였다. 이 프로브는 한 바퀴에 카드 문서를 chromium에 108번 띄운다(컴포넌트마다 `render` 1, `cascade`·`mode`·`mode-bare`·`dark-match` 2씩, `theme-match` 3. 코드를 읽었다). 한 번 잰 값이고, 그때 이 PC에 다른 세션이 돌았는지는 보지 않았다.

## 2026-10-28 실제 페이지(임시 아티팩트)

나만 보는 임시 Design System 아티팩트(형식 판 release `1793156745-17fb`)를 새로 만들어 판을 차례로 올리고, 앱 안 브라우저(Chromium)로 열어 화면을 찍어 읽었다(손으로 봤다). 올린 것은 `card-run-5`의 `stage/` 가운데 글꼴은 woff2 385개만이고(woff 385개는 뺐다), 색인 `design-system.json`은 `layout: "files"`, `namespace: "AgentOsUi"`, `libraries`에 react·react-dom 18.3.1을 적었다. 255개 한도 때문에 첫 판은 호출 둘로 보냈다. 판마다 바꾼 것과 본 것은 아래다.

| 판 | 바꾼 것 | 본 것 |
|---|---|---|
| 3 (`1793175915-d22e`) | `stage/`의 정식 자리 배치와 색인(`source` 없음) | Components 절에 카드 아홉(Button, Card, Icon, IconButton, Progress, StatusBadge, Alert, Switch, TextField)이 모두 그려졌다. 스크롤해 들어온 카드는 몇 초 뒤에 그려졌다. Overview에 배너가 없다. 테마 메뉴와 Colors 표의 머리에 '녹청 다크 (Dark)'처럼 바꾼 이름이 보인다. 바깥 페이지의 콘솔 오류는 0이다(카드 iframe은 다른 출처라 그 콘솔은 도구가 읽지 못했다) |
| 4 (`1793176525-a46d`) | 진단 카드(`page_diag_card.html`)를 더하고 색인에 `source: {app: "claude-design", at: …}`를 넣었다 | Overview에 "No move is perfect" 배너와 "Finish setting up" 단추가 떴다(판 `1793146503-9e85`의 `app.js`에서 같은 문구 `A1e`·`k1e`를 찾았다). 진단 카드(다크): `react=18.3.1`, `reactdom=18.3.1-next-f1338f8080-20240426`, `data-theme=nokcheong-dark data-mode=dark`, `color-scheme=dark`, `html`과 `body` 바탕 `rgba(0, 0, 0, 0)`, 글꼴 386개 가운데 실림 0·오류 5, 글꼴 요청 10건의 첫 주소 `/_f/<판>/project/components/fonts/noto-sans-kr-….woff2`, 기준 주소 `/_f/<판>/project/components/Diag/preview.html`, 스타일시트 `<link>` 0개, `<style>` 3개, 스크립트 `npm/react@18.3.1/umd/react.production.min.js`·`npm/react-dom@18.3.1/umd/react-dom.production.min.js`·`/_f/<판>/project/components/bundle.js`, `AgentOsUi`의 키 14개 |
| 5 (`1793176900-cac3`) | `components/bundle.css`의 `url(../fonts/` 770건을 `url(../../fonts/`로 바꿨다(`sed`) | 진단 카드(다크): 실림 9·오류 0, 실린 글꼴 이름 `Noto Sans KR`, 글꼴 요청의 첫 주소 `/_f/<판>/project/fonts/noto-sans-kr-100-400-normal-….woff2`. 탭의 색 모드를 라이트로 흉내 내자 `data-theme=nokcheong-light data-mode=light`, `color-scheme=light`, 실림 9·오류 0 |
| 6 (`1793177051-c49f`) | 색인에 `upgraded: {at: …}`를 더했다(`source`는 남겼다) | 라이트에서 Overview에 배너가 없고 Colors 표에 편집 단추가 보인다. 판 7을 다크로 열었을 때도 배너가 없었다 |
| 7 (`1793177475-2113`) | `tokens.json`의 테마 이름에서 ` (Light)`·` (Dark)`를 뺐다(id는 그대로) | 다크에서 테마 메뉴가 '녹청 라이트'로 열렸고 진단 카드는 `data-theme=nokcheong-light data-mode=light`, `color-scheme=light`, `html` 바탕 `rgb(244, 248, 251)`이다. 메뉴에서 '녹청 다크'를 고르자 `data-theme=nokcheong-dark data-mode=light`, `color-scheme=light`, `html` 바탕 `rgb(15, 18, 20)`이다. 컴포넌트는 어두운 색으로 그려졌다 |
| 웹 저장 (`1793178461-b394`) | 판 7을 연 페이지의 Colors 표에서 녹청 라이트 `gray-50`을 `#F4F8FB`에서 `#F4F8FC`로 고쳤다. 페이지가 스스로 새 판을 저장했다 | 그 판의 `design-system.json`(Artifact 도구의 `read`로 받았다)에 `source`와 `upgraded`가 그대로 있고, 페이지가 `libraries`의 두 항목에 `global`(`React`, `ReactDOM`)을 덧붙였고 `docs.readme`(`project/README.md`)를 적었다. `lastChange`는 바꾸지 않았다. 다시 연 Overview에 배너가 없고 Files의 수가 408에서 420으로 늘었다 |
| 9 (`1793183138-b526`) | 웹 저장 판 위에서 진단 카드만 v2로 바꿨다. 이 판의 `tokens.json`은 녹청 라이트 `gray-50`이 웹에서 고친 `#f4f8fc`이고 녹청 다크는 `#f4f8fb`다 | 탭의 색 모드를 라이트로 흉내 내고 테마 메뉴 '녹청 라이트'에서 진단 카드: `gray50=#f4f8fc bg=#f4f8fc`, `data-theme=nokcheong-light data-mode=light`, `react=18.3.1`, 글꼴 386개 가운데 실림 11·오류 0, 실린 글꼴 이름 `Noto Sans KR`, 글꼴 요청 27건의 첫 주소 `/_f/<판>/project/fonts/noto-sans-kr-100-400-normal-….woff2`. 카드 아홉도 그려졌다. 카드 칸의 높이는 그려진 내용을 따라 달랐고(Alert와 TextField의 칸이 다른 칸보다 높았다), Alert의 장면 둘은 칸 폭 안에 들었다(앱 안 브라우저 폭 800px). 진단 카드는 2초 넘게 기다린 뒤 글을 바꿔, 칸이 늘어난 글을 다 담지 못하고 `fontres=` 줄까지만 보였다 |

해석과 갈래:

- 카드는 묶음 CSS를 `<link>`가 아니라 문서 안의 `<style>`로 싣고, 그 문서의 기준 주소는 `components/<이름>/preview.html`이다(판 4의 `links=`가 비었고 `baseURI`가 그 자리다). 그래서 묶음 CSS 안의 상대 주소는 묶음 파일(`components/bundle.css`)이 아니라 카드 파일의 자리에서 풀린다. `../fonts/`는 `components/fonts/`로 풀려 글꼴이 하나도 실리지 않았고, `../../fonts/`는 `fonts/`로 풀려 실렸다. 판 4와 판 5는 글꼴 주소만 다르다. 판 5가 같은 글꼴 파일이 이 페이지에서 실릴 수 있다는 양성 대조이고, 판 4의 실패가 파일이 없거나 깨져서라는 해석을 가른다.
- 페이지 코드(판 `1793146503-9e85`의 `VT`)에는 묶음 CSS를 주소로 싣는 다른 갈래(`urls.bundleCss`)가 있다. 이 측정에서는 그 갈래가 돌지 않았고(`<link>` 0개), 언제 도는지는 재지 않았다. 그 갈래에서 상대 주소가 어디서 풀리는지도 재지 않았다.
- 카드의 모드는 테마 **이름**이 정한다. 판 5에서 이름에 '(Dark)'가 있는 `nokcheong-dark`는 `data-mode=dark`, `color-scheme=dark`, 투명한 바탕이었고, 판 7에서 이름만 '녹청 다크'로 둔 같은 id는 `data-mode=light`, `color-scheme=light`였고 페이지가 바탕을 칠했다. id에 이미 `dark`가 든 것만으로는 모드가 다크가 되지 않는다는 갈래다. 페이지 코드의 `HU`가 `FU(a.name)`(`/dark|night/i`)로 모드를 정하는 것과 맞는다(코드 읽기). 다크인 앱에서 처음 보이는 테마도 판 7에서는 첫 테마(녹청 라이트)였다.
- 배너는 색인의 옮김 표시가 띄우고 `upgraded`가 거둔다. 판 3(`source` 없음)에는 없고, 판 4(`source.app`이 `claude-design`)에는 떴고, 판 6(`source`에 `upgraded`를 더함)에는 없다. 판 4가 이 페이지에서 배너가 뜰 수 있다는 양성 대조다. 판 6은 라이트, 판 4는 다크에서 봤고, 판 7을 다크로 열어도 배너가 없어 색 모드가 배너를 가른다는 해석은 서지 않는다. `upgraded` 대신 `source`를 지우는 길(형식 지시문이 마지막 호출에서 `editing`과 `source`를 지우라고 적은 길)은 판 3이 `source` 없는 색인에 배너가 없다는 것까지만 보인다. 웹 저장 판은 사람이 웹에서 고쳐 저장해도 페이지가 `upgraded`를 지워 배너를 되살리지 않는다는 것을 보인다. 웹 저장 한 번(색 값 하나)만 봤고, 다른 편집(README, 글자, 지우기)의 저장은 보지 않았다.
- React 18.3.1 위에서 React 19.3.0으로 지은 묶음과 카드가 그려졌다(판 3~7의 화면, 진단 카드의 `react=18.3.1`). 카드 iframe의 콘솔은 읽지 못해 오류가 0이라고는 적지 않는다.
- 층 안의 디자인 토큰은 실제 페이지에서도 페이지 토큰 CSS에 진다(판 9). 그 판의 묶음 CSS(Artifact 도구의 `read`로 받은 `components/bundle.css`)는 `:root,:host,[data-theme=nokcheong],:host([data-theme=nokcheong]){…--gray-50:#f4f8fb…}`를 `@layer theme{…}` 안에 둔다(파이썬으로 그 블록의 괄호 깊이를 따라 `--gray-50:#f4f8fb`가 블록 안에 있는 것을 봤다). 카드 문서의 `html`은 `:root`라 그 규칙이 언제나 맞는다. 그런데 진단 카드가 찍은 계산값은 웹 저장이 `tokens.json`의 녹청 라이트에 적은 `#f4f8fc`였다. 묶음이 이겼다면 `#f4f8fb`가 나와 두 해석이 갈린다. 묶음 CSS가 그 문서에 실렸다는 표지는 Noto Sans KR가 `project/fonts/`에서 실린 것이다. 그 `@font-face`는 묶음 CSS에만 있고(`tokens.json`에 `type.fonts`가 없다), 판 4와 판 5가 묶음 CSS의 글꼴 주소만 바꿔 실림을 바꿨다. 페이지 토큰이 층 밖이라 이긴 것인지 다른 까닭(더 뒤의 층, 인라인 스타일)인지는 가르지 않았고, 명세가 기대는 것은 페이지 토큰이 이긴다는 관찰이다. 본 것은 `--gray-50`과 그것을 쓰는 `--bg`의 계산값이고, 그 토큰으로 칠한 컴포넌트의 색은 보지 않았다.
- 카드 칸의 높이는 형식의 `height=N` 없이도 그려진 장면을 따랐다(판 9의 Alert·TextField). 진단 카드가 잘린 것은 칸의 높이를 정한 뒤에 글이 늘어서로 본다(어림. 페이지가 높이를 언제 재는지는 코드를 읽지 않았다).

재지 않은 것(이 절): 묶음 CSS를 주소로 싣는 갈래, 카드 iframe 안의 콘솔 오류, 웹 편집으로 바꾼 색으로 칠한 컴포넌트의 모양(판 9는 토큰의 계산값만 찍었다), Typography 절의 글자 견본이 Noto Sans KR로 그려지는지(`tokens.json`에 `type.fonts`가 없어 페이지가 글꼴 CSS를 짓지 않는다. Typography 절의 "Font files" 목록에는 올린 글꼴 파일이 한 줄씩 지우기 단추와 함께 보였고 경고 문구는 보이지 않았다).

## 2026-10-28 vite CLI(`vite_cli.mjs`)

둘째 실행(`vite-cli-2`, `card-run-5`와 견줌): 회차 6, 측정 6, 측정 아님 0. 종료 0. 첫 실행(`vite-cli-1`)은 묶음과 장면, 설정 파일의 import 셋째 회차만 있었고 셋 다 측정이었다. 그 결과를 본 뒤 견주기의 양성 대조, 빌드 CSS, 글꼴 회차를 더했고 이미 있던 회차의 표지는 바꾸지 않았다.

- `bundle`: CLI가 0으로 끝났고(3,046ms) 묶음 17,112바이트가 `card-run-5/bundle.js`와 바이트까지 같다. `require(`·`import` 문·`react.transitional.element`가 모두 0이다.
- `scene:Button`: CLI가 0으로 끝났고(2,198ms) 장면 9,456바이트가 `card-run-5`의 Button 카드 스크립트와 같다. 장면은 패키지를 전역 `AgentOsUi`로 부른다.
- `control:scene-differs`: 같은 장면을 Alert 카드의 스크립트와 견주면 같지 않다고 나온다. 위 두 "같다"가 견주기가 늘 참을 내서 나온 것이 아니라는 양성 대조다.
- `css`: `pnpm exec tailwindcss`가 0으로 끝났고(2,046ms) 빌드 CSS 23,482바이트가 `card-run-5/bundle.css`와 같다. `card_build.mjs`는 같은 CLI를 `node <패키지>/node_modules/@tailwindcss/cli/dist/index.mjs`로 띄웠다.
- `fonts`: CLI가 0으로 끝났고(4,528ms) 글꼴 772개를 냈다. `card-run-5/stage/fonts/`의 770개가 모두 그 안에 같은 이름으로 있다(`stage`는 인라인 한도 기본값으로 지어 770개를 냈다. 위 다섯째 실행 절).
- `config-has-no-import`: 지은 설정 파일 셋에 `import` 문이 0이다. 플러그인(JSX 대체 모듈, Storybook 시험 도구 대체 모듈, 컴포넌트를 전역으로 돌리는 해석기)은 설정 글 안의 객체로 두었다.

해석: 올리기 도구는 vite를 import하지 않고, 설정을 글로 지어 패키지 자리의 CLI로 넘겨도 JS API와 같은 산출을 낸다. 설정은 실행 중에 쓰는 데이터라 도구의 TypeScript 소스에는 vite의 타입이 들지 않는다. pnpm의 실행 shim(`web/packages/ui/node_modules/.bin/vite`)이 띄우는 파일은 `node_modules/vite/bin/vite.js`다(shim을 읽었다). 그 파일을 셸 없이 띄우는 도구 모양이 타입 검사와 실행을 지나는지는 아래 `vite_cli_tool.mts`가 잰다.

도구 모양(`vite_cli_tool.mts`):

- 타입 검사: `tsc -p .scratch/design-card-build/probes/tsconfig.json`이 0으로 끝났다. 검사가 이 파일과 `@types/node`를 실제로 본다는 것은 `--listFilesOnly`의 목록(181줄)에 둘이 든 것으로 봤다. 양성 대조로 같은 파일 끝에 `const wrong: number = rounds.length > 0 ? "x" : 1;`을 붙인 사본을 같은 설정으로 검사하자 TS2322로 2에 끝났다. 처음에는 확장자를 `.ts`로 두어, `web/` 밖이라 가장 가까운 `package.json`에 `"type": "module"`이 없어 CommonJS로 읽히고 TS1295가 났다. `.mts`로 바꿨다. 도구는 `web/` 안이라 이 갈래에 들지 않는다.
- 실행(`vite cli tool 1`, 공백이 든 작업 폴더): 회차 2, 측정 2, 종료 0. `bundle:bin`은 vite가 0으로 끝났고(647ms) 묶음 17,112바이트가 `card-run-5/bundle.js`와 같다. `control:compare`는 같은 산출 끝에 공백 하나를 붙인 글과 견주면 같지 않다고 나왔다. 셸을 거치지 않아 공백이 든 경로가 그대로 넘어갔다. stderr에는 `lucide-react`의 `"use client"` 지시문이 보존되지 않을 수 있다는 rolldown 경고가 실렸고 종료 코드는 0이다. 그래서 짓는 명령은 stderr가 비지 않은 것을 실패로 보면 안 된다.
- 같은 묶음이 pnpm을 거친 `vite_cli.mjs`에서는 3,046ms, 실행 파일을 바로 띄운 여기서는 647ms였다. 차이의 대부분은 pnpm을 띄우는 값으로 본다(한 번씩 잰 값이라 어림).

재지 않은 것(이 절): 장면 아홉을 모두 짓는 시간(실행 파일을 바로 띄우면 빌드 하나가 1초 안팎이라 묶음·CSS·글꼴·장면 아홉을 더해 한 번 짓기에 15초 안팎으로 어림한다), 실행 파일을 바로 띄우는 길로 장면·빌드 CSS·글꼴을 짓는 것(위 `vite_cli.mjs`가 pnpm을 거쳐 같은 CLI로 지었다), 도구의 소스가 eslint(`pnpm -C web verify`의 typescript-eslint)를 지나는지. 이 프로브 파일은 그 뒤에도 eslint로 재지 않았다. 같은 모양으로 지은 티켓 01의 짓기 명령(`web/tools/sync-design-system/assemble.ts`)은 `web/`의 eslint와 strict 타입 검사를 지났다(그 티켓의 결과).

## 2026-10-29 글꼴 대조(`font_route.mjs`)

둘째 실행(`font_route_d89970e7`, 2026-10-30, `HEAD` `d89970e7`, 짓기 명령과 디자인 시스템 패키지 아래 커밋하지 않은 변경 0): 회차 4, 측정 4, 측정 아님 0, `splits`는 `file`·`route` 모두 `true`. 종료 0. 수는 프로브가 요약에 찍은 것이다. 셀프 리뷰가 표지에 문서의 자리를 더하고 길마다의 갈림(`splits`)을 찍게 고친 판으로 잰 것이다. 네 회차 모두 문서가 카드 자리에서 열렸다(`at`이 `file` 길은 산출 폴더의 `components/Button/__font_route.html`, `route` 길은 `/components/Button/preview.html`).

- `file`·`positive`와 `route`·`positive`: 문서의 Noto Sans KR FontFace 372개 가운데 실림 5, 문서 전체의 글꼴 오류 0.
- `file`·`negative`와 `route`·`negative`: 실림 0, 글꼴 오류 5.

첫 실행(`font-route-1`, `HEAD` `f6df25c8`, 커밋하지 않은 변경 4. 티켓 01의 `assemble.ts`·`assemble.test.ts`·`main.ts`·시험 자료가 커밋 전이었다)은 표지에 문서의 자리가 없고 갈림을 찍지 않던 판이었다. 회차 4, 측정 4, 종료 0이었고 네 회차의 실림과 글꼴 오류는 둘째 실행과 같았다.

해석: 두 길 모두 묶음 CSS 안의 상대 주소가 카드 파일의 자리(`components/<이름>/`)에서 풀린다. 양성 갈래가 이 문서에서 같은 글꼴 파일이 실릴 수 있다는 대조이고, 음성 갈래는 주소의 앞머리만 바꿔 실림을 0으로 만들었다. 실제 페이지의 판 4·5(위 "실제 페이지" 절)와 같은 갈림이다. 짓기 시험은 `route` 길을 골랐다. `file://` 길은 진단 문서를 산출 폴더 안에 써야 하고, `route` 길은 산출을 고치지 않으며 페이지처럼 `http` 출처에서 싣는다. 티켓을 시작할 때 커밋하지 않은 스크래치 스크립트로 같은 네 갈래를 먼저 봤고 수가 같았다(손으로 봤다). 그 스크립트를 이 프로브로 옮기며 짓기 명령을 스스로 돌게 했다.

## 2026-10-29 짓기 명령의 변이(`assemble_mutations.toml`)

첫 전체 실행은 변이 24 가운데 어긋남 4였다. 넷 다 빨강은 기대대로였고 표지가 없었다. 변이를 손으로 넣어 실패 출력을 본 뒤(손으로 봤다) 표지와 시험을 고쳤다.

- 비지 않은 산출 폴더: vitest가 실패 머리에 0을 `+0`으로 찍는다(`expected +0 to be 1`).
- 그리기의 장면 수·그려진 장면 수·글꼴 오류: 칸마다 단언이 따로라 장면 수와 그려진 장면 수가 같은 꼴의 문구(`expected … to be 2`)를 냈고, `-t` `Button 카드는`이 IconButton 사례까지 골랐다. 그리기 시험의 칸 넷(오류, 장면 수, 그려진 장면 수, 글꼴 오류)을 한 객체로 맞대게 바꾸고, 표지를 diff의 `+` 줄(`+   "filled": 0,` 따위)로, 좁히기를 `(?<!Icon)Button 카드는`으로 바꿨다.

같이, 다른 단언의 실패에도 실리는 표지 셋을 고쳤다. 보고의 `"bytes":`는 diff의 문맥 줄에도 실려 `+` 줄로 바꿨다. 묶음의 금지 문자열 표지는 장면 쪽 실패 문구(`Button: expected [ … ]`)에도 들어 있어 실패 머리 `AssertionError: expected …`로 바꿨다. 글꼴 주소 시험은 두 단언(앞머리, 가리키는 파일이 있음)이 같은 문구(`<주소>: expected false to be true`)를 내어, 파일마다 앞머리가 틀린 주소와 파일이 없는 주소를 나눠 한 번에 맞대게 바꾸고 표지를 `+     "misplaced": [`로 했다. 가리키는 파일이 있음 칸을 재는 변이(woff 파일을 내지 않는다)를 더해 변이는 25다. 표지를 바꾼 것과 새것 열(1, 6, 9, 10, 19~24)을 다시 돌려 모두 기대대로였다. 시험을 고쳤으므로 전체는 셀프 리뷰를 반영해 커밋한 뒤 다시 돈다.

둘째 전체 실행(2026-10-30, `HEAD` `3892f94a`, 셀프 리뷰와 PR 직전 리뷰를 모두 반영해 커밋한 판)은 "변이 29 모두 기대대로"였다(도구가 찍은 줄). 좁힌 사례마다의 기준선 21이 모두 초록이었고, 시작 줄에 표·짓기 명령·시험의 커밋하지 않은 변경을 알리는 줄이 없었다(실행 로그의 `기준선` 줄을 `grep`으로 세고 로그 머리를 손으로 봤다). 첫 실행 뒤 더한 넷(지금 표의 번호)은 셀프 리뷰가 짚은 옛 이름 묶음 JS가 정식 자리와 같은 것(11), 크기와 다른 규칙을 함께 어긴 섞인 경우(20), 목록 파일이 산출 폴더 안인 자리(21)와, PR 직전 버그 축이 짚은 임시 폴더를 만들지 못하는 자리(23)다. 이 넷과 셀프 리뷰가 겨누는 줄이나 표지를 바꾼 변이가 이 실행에서 처음 함께 돌았다(23은 앞서 단독으로 돌아 기대대로였다).

재지 않은 것: "지은 산출은 판정을 지난다"(대조, 표의 머리 주석), 명령이 판정을 부르는 줄(`assertAssembled(stage)`)을 지우는 변이(지은 산출이 판정을 지나 어느 사례도 빨개지지 않는다. 판정의 갈래는 규칙 판정 사례가 같은 함수를 불러 잰다. 표의 머리 주석), 카드 셋째 줄 뒤의 모양 단언(장면 스크립트 하나, 끝 줄바꿈), 크기 사례의 묶음 CSS·카드·README 한도(크기 변이는 묶음 JS 하나만 키운다. 판정 쪽은 넷을 함께 끄는 변이가 잰다), 글꼴 주소 시험 끝의 파일 이름 차례 맞대기 둘, 경로 목록 사례의 `project/` 머리와 차례 단언(앞의 글 맞대기가 같은 것을 먼저 본다).

## 2026-10-30 티켓 02의 변이(`assemble_mutations.toml` 30~64)

티켓 02가 더한 사례 열셋을 겨누는 변이 서른셋이다. 산출 파일 넷(`tokens.json`의 바이트와 테마 이름, README, 기초 카드, 지침)을 겨누는 여덟(30~37)은 짓기 명령의 쓰기 줄이나 모드 이름 표, 기초 카드 원본을 바꾼다. 사용 규약을 겨누는 열넷(38~51)과 산출 밖 스토리 파일을 겨누는 넷(52~55)은 대개 README 원본, 기초 카드 원본, 패키지의 컴포넌트·스토리를 바꾸고, 51만 묶음 머리의 목록을 짓는 `assemble.ts`를 바꾼다. 셀프 리뷰가 더한 셋(56~58)은 넷 밖의 기초 카드 폴더에 표지 없는 HTML을 쓰는 것(56), README가 다른 변수의 꼬리로만 선언된 `--line-height`를 드는 것(57. 변수 판정의 앞 글자 가드가 없으면 `--text-title--line-height:` 안에서 맞아 초록이 될 자리다. 그 가드를 끈 대조는 돌리지 않았다), 기초 카드 폴더에 원본에 없는 `.txt`를 쓰는 것(58)이다. PR 직전 버그·성능 리뷰가 짚은 두 자리(README 키의 글자 거르기와 합쳐 센 개수, showcase 스토리가 펼쳐 넣은 스토리의 `globals`)를 고치며 더한 넷(59~62)은 README의 밀도 괄호에서 백틱을 걷는 것(59. 속성마다 세지 않으면 테마 키로 지날 자리다), README의 밀도 키를 `regular-2`로 바꾸는 것(60), 기초 카드의 밀도 값을 `compact-2`로 바꾸는 것(61. 60과 61은 옛 글자 거르기 `[a-z]+`라면 그 키가 빠져 초록이 될 자리다), Button의 showcase 스토리에 `globals`가 든 `DisabledDark`를 펼쳐 넣는 것(62)이다. 고치기 전 판으로 돌린 대조는 없고, 고치기 전이면 초록이었다는 것은 시험 코드를 읽은 것이다. 없다고 든 변형(41)은 README 원본이 아니라 컴포넌트 `Card.tsx`에 `dark:bg-bg`를 넣어, README가 없다고 든 `dark:`의 클래스(`.dark\:`)가 묶음에 생기게 했다. 이 브랜치의 작업 트리로 지은 `components/bundle.css`에는 변형 클래스가 `active`·`focus-visible`·`hover`·`motion-reduce`·`placeholder`·`wide`의 18곳에 있고 `.dark\:`는 없다(셀프 리뷰 때 `grep -o -E '\.[a-z-]+[\\]:'`로 세어 손으로 봤다). 표지는 사례마다 맞대는 객체의 diff에서 받은 쪽 `+` 줄(`+     "zz-mutant",` 따위)이나 실패 머리(`expected false to be true`, `Object.is equality`)다.

첫 실행(`HEAD` `d312a806` 위의 작업 트리. 표·짓기 명령·시험·`build.ts`가 커밋 전이었다)은 "변이 26 모두 기대대로"였다(도구가 찍은 줄). 좁힌 사례마다의 기준선 13이 모두 초록이었고, 실행 로그에 `표지 없음` 줄이 없었다(`grep`으로 셌다). 52(Progress 스토리의 `showcase` 표지를 지운다)만 시험 수가 43이 아니라 42였다(도구가 찍은 요약 줄). 시험 파일이 chromium의 카드 사례를 스토리 소스의 showcase 스토리에서 지어(`expectedCards`), Progress의 카드 사례가 생기지 않았다고 본다(시험 코드를 읽은 것이다). 그래서 카드가 빠져도 카드 사례는 빨개지지 않고, 그 빠짐은 이 변이가 겨눈 showcase 사례만 잡는다.

56~58만 돌린 실행(셀프 리뷰 때, `HEAD` `d312a806` 위의 작업 트리)은 "변이 3 모두 기대대로"였고 좁힌 사례의 기준선 둘이 초록이었다(도구가 찍은 줄). 표지는 고른 단언의 맞대는 객체에만 그 값이 실린다고 시험 코드를 읽어 골랐고, 셋 모두 도구가 그 표지를 출력에서 찾았다. 그 뒤 표지를 일부러 틀리게 둔 임시 표(커밋하지 않고 지웠다)로 셋을 다시 돌려, 도구가 낸 출력의 끝에서 실패한 단언의 자리를 손으로 봤다. 56은 기초 카드 사례의 폴더별 맞대기(`expect(seen)`), 58은 그 뒤의 파일 목록 맞대기(`expect(files)`), 57은 변수 사례의 `undeclared` 맞대기에서 멈췄다. 출력의 끝에는 diff 줄이 실리지 않아, 표지 문구 자체는 앞 실행에서 도구가 찾은 것만 근거다.

59~62만 돌린 실행(PR 직전 리뷰를 반영할 때, `HEAD` `e7d71a72` 위의 작업 트리)은 "변이 4 모두 기대대로"였고 좁힌 사례의 기준선 셋이 초록이었다(도구가 찍은 줄). 그 전에 `--check`가 "변이 62 모두 원문이 한 번씩 있다"였다. 표지는 59가 `withoutKeys`의 `+     "data-density",`, 60·61이 `noSelector`·`cardNoSelector`의 `=regular-2`·`=compact-2` 줄, 62가 펼친 덩이의 이름까지 든 `+     "Button ShowcaseApprovalPair DisabledDark",`이다. 59의 사례에서 다른 단언(`noSelector`)은 값이 `<속성>=<키>` 꼴이라 그 표지를 내지 못하고, 62의 표지는 펼친 덩이를 따라가는 길에서만 생긴다(시험 코드를 읽은 것이다. 변이를 손으로 넣어 실패 출력을 따로 보지는 않았다).

전체 실행(2026-10-30, `HEAD` `9c800d32`, 셀프 리뷰와 PR 직전 리뷰를 모두 반영해 커밋한 판)은 "변이 62 모두 기대대로"였다(도구가 찍은 줄). 좁힌 사례마다의 기준선 34가 모두 초록이었고, 실행 로그에 `표지 없음` 줄과 커밋하지 않은 변경을 알리는 줄이 없었다(로그를 `grep`으로 셌다).

PR 봇 회차(PR #434 claude-review의 Nit)를 받아 더한 둘(63·64)은 `build.test.ts`의 새 사례("다크 벌의 이름만")를 겨눈다. 그 사례는 페이지가 카드의 모드를 가르는 정규식 `/dark|night/i`를 여덟 벌의 이름에 대 보고, 31이 겨누는 "테마 이름은 모두" 사례는 이름 끝의 모드 낱말만 본다. 63은 쪽빛의 표시 이름을 `쪽빛 Midnight`로, 64는 다크의 모드 이름을 `다크`로 바꾼다. 63·64만 돌린 실행(`HEAD` `b4252b72` 위의 작업 트리)은 "변이 2 모두 기대대로"였고 좁힌 사례의 기준선 하나가 초록이었다(도구가 찍은 줄). 그 전에 `--check`가 "변이 64 모두 원문이 한 번씩 있다"였다. 표지(`+     true,`·`+     false,`)는 변이를 손으로 넣어 실패 출력의 diff에서 받은 쪽 줄을 보고 골랐고, 그 사례의 단언은 하나다(시험 코드를 읽은 것이다). 63을 손으로 넣은 채 두 사례를 한 실행으로 돌리자 새 사례만 빨갛고 "테마 이름은 모두" 사례는 지났다(vitest 요약 줄 `1 failed | 1 passed`를 손으로 봤다). 라이트 이름에 night가 든 자리를 옛 사례가 놓친다는 것은 그 실행이 근거다.

재지 않은 것: 저장소 원본을 읽지 못하거나 기초 카드 원본 폴더가 빌 때의 `input` 오류(원본 경로가 `SOURCES`로 고정이라 시험이 지나지 않는다), 판정이 README 문장을 찾지 못하면 던지는 갈래(`section`. 문장 모양을 바꾸는 변이를 두지 않았다), 변수 판정이 빼는 두 자리("테마의 재료" 줄과 `<이름>` 자리 표시. 빼기를 끄는 변이는 판정이 원본을 잘못 막는지를 재는 대조인데 두지 않았다), 라이트 테마 이름의 모드 낱말(31은 다크 쪽만 바꾼다. 라이트 이름에 night가 드는 자리는 63이 build 사례로 잰다), 지침 폴더에 다른 파일이 더 생기는 갈래.
