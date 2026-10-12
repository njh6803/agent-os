# design-refresh 프로브

명세(`../spec.md`)가 근거로 드는 측정 스크립트다. 규약은 `docs/agents/issue-tracker.md`의 "프로브와 근거".

재탐색의 디자인 파일(`.scratch/design-system/design/Agent OS Design System.dc.html`)에서 값을 뽑는 것은 design-system의 프로브 `.scratch/design-system/probes/tokens/design.mjs`의 `readRefresh()`(명령은 `--refresh`)다. 첫 탐색 v3를 읽는 `readDesign()`과 함수를 나눠, v3를 읽는 그 폴더의 `setup.mjs`·`measure.mjs`는 그대로 돈다. 이 폴더의 `contrast.mjs`, `same-values.mjs`, `chromium.mjs`가 그것을 import한다.

저장소 루트에서 돈다. `contrast.mjs`와 `same-values.mjs`는 아무것도 설치하지 않고 레지스트리에 닿지 않는다. `font.mjs`는 작업 폴더(저장소 밖)에 `npm pack`으로 받아 풀고, 저장소에는 아무것도 쓰지 않는다. `chromium.mjs`와 `tailwind.mjs`는 `pnpm -C web install`이 깔린 web 폴더를 인자로 받는다(기본 `web`). 워크트리에 `node_modules`가 없으면 주 체크아웃의 web 폴더를 넘긴다. 둘 다 저장소에 아무것도 쓰지 않는다.

```sh
node .scratch/design-system/probes/tokens/design.mjs --refresh
node .scratch/design-refresh/probes/contrast.mjs
node .scratch/design-refresh/probes/same-values.mjs
node .scratch/design-refresh/probes/font.mjs <작업 폴더>
node .scratch/design-refresh/probes/chromium.mjs [web 폴더]
node .scratch/design-refresh/probes/tailwind.mjs [web 폴더]
```

| 파일 | 재는 것 | 근거로 드는 자리 | 다시 돌 때 | 잰 판 |
|---|---|---|---|---|
| `contrast.mjs` | 디자인 토큰 JSON의 쓰임새 토큰 값으로 여덟 벌(테마 넷 × 모드 둘)의 짝마다 WCAG 2.2 명암비를 센다. 반투명 바탕(`bg-hover`, `bg-active`, `bg-selected`)은 그 아래 바탕에 겹치고 채널마다 정수로 반올림한 색으로 잰다(디자인 파일의 `over`와 같다). 짝은 넷으로 나뉜다. 디자인 파일 스크립트의 `PAIRS`를 편 35개(먼저 디자인 파일 표의 행마다 가장 낮은 값과 맞대고 대조한 행 수를 낸다), 컴포넌트 상태 표를 읽고 손으로 옮긴 짝 가운데 디자인 파일이 재지 않은 8개(위험 버튼의 누름은 명세가 바꾼 `bg-selected`), 디자인 파일 상태 표가 적은 위험 버튼 누름(`bg-active`) 2개, 반투명이 두 겹 겹치는 자리 2개(명세의 판정 밖)다. 끝으로 앞의 둘(43개)에서 반올림 없이 겹치면 판정이 뒤집히는 자리를 낸다 | 명세의 "명암비 짝 43개", "반투명 바탕의 명암비", "판정은 놓인 바탕 위의 한 겹까지다", "위험 버튼의 누름", 티켓 03의 수용 기준 | 없음. 디자인 파일을 다시 내보내면 다시 돈다 | 디자인 파일 `Agent OS Design System.dc.html`(README 표의 기준 커밋 `15e41a6`) |
| `same-values.mjs` | 한 벌 안에서 같은 원색을 가리키는 쓰임새 토큰의 짝을 여덟 벌에서 센다. 짝마다 같은 벌과 다른 벌의 수를 낸다. 계산값으로 두 토큰을 가를 수 있는 벌을 고르는 데 쓴다 | 명세의 "계산값을 가를 수 없는 짝", 티켓 03의 수용 기준 | 없음 | 같은 디자인 파일 |
| `chromium.mjs` | 실제 Chromium에서 두 가지를 본다. 1) 원색 `overlay` 일곱(hex 8자리)을 사용자 정의 속성에 두고 `background-color`로 쓴 요소의 계산값과 `getPropertyValue`의 꼴. 2) 다크 네 테마에서 `bg-selected`를 `bg-raised`·`bg`에 겹친 상자의 칠한 픽셀(상자 안에 글자가 없을 때와 있을 때)과 `danger` 글자색의 명암비, 그리고 판정(반올림)과 반올림 없는 값. 직렬화는 넣은 hex를 그대로 돌려주고 계산값의 RGB와 알파가 그 hex와 맞는 회차만, 픽셀은 스크린샷이 1×1·깊이 8·RGB(A)·인터레이스 없음의 PNG이고 아래 바탕과 다른 회차만 측정으로 센다. 측정한 회차가 기대(직렬화 7, 픽셀 16)보다 적어도 종료 코드가 1이다 | 명세의 "위험 버튼의 누름", "판정 스토리와 판정 함수"의 Matrix, Further Notes의 "재지 못한 것"에 단 명세 검토·to-tickets 주석, 티켓 03의 수용 기준 | `pnpm -C web install`이 깔린 web 폴더(인자)와 그 Playwright의 chromium | Playwright 1.63.0, Chromium 153.0.8010.12(Windows headless) |
| `tailwind.mjs`, `tailwind-input.css` | 입력 CSS를 Tailwind로 컴파일해 두 가지를 본다. 1) `@theme inline`의 별칭(`--text-body: var(--body-size)`)을 손으로 쓴 `var()`가 읽으면 `:root, :host`에 선언으로 나오는지, 유틸리티만 쓰는 별칭(`--spacing-control`)은 나오지 않는지. 그 `var()` 규칙을 뺀 입력도 컴파일해 까닭을 가른다. 2) `optimize`(Lightning CSS)가 사용자 정의 속성의 hex를 짧은 꼴로 바꾸는지(`minify` 둘). 테마 블록(`@layer theme {`) 안에 `@theme static`의 `--text-title:`이 나오고(양성 대조) `.h-control` 규칙이 있어야 1)을, 결과에 입력의 사용자 정의 속성 셋이 모두 있어야 2)를 측정으로 센다 | 명세의 밀도 절 "유틸리티"와 "hex는 소문자다"에 단 명세 검토 주석, 티켓 04·05의 수용 기준 | `pnpm -C web install`이 깔린 web 폴더(인자) | `@tailwindcss/node` 4.3.3 |
| `font.mjs` | 고정폭 글꼴 패키지 `@fontsource/noto-sans-mono`와 지금 한글 글꼴 `@fontsource/noto-sans-kr` 5.3.0을 받아, 라이선스(OFL 본문, 저작권 줄의 예약 글꼴 이름), 설치 때 도는 스크립트, 굵기 CSS마다 `@font-face` 수와 서브셋 이름, `local(` 수, `url()`의 앞머리와 가리키는 파일의 유무, 한글(U+AC00)을 덮는 범위의 유무, woff2 바이트 합을 낸다 | 명세의 "글꼴", 티켓 01의 수용 기준 | 작업 폴더와 레지스트리. `--version`으로 다른 판을 잰다 | `@fontsource/noto-sans-mono` 5.3.0, `@fontsource/noto-sans-kr` 5.3.0, npm 11(Node 24.19.0) |
| `icon_props_mutations.toml` | 티켓 02의 변이 표 여덟. 구현 전에 빨갛던 스토리에서도 앞 단언이 먼저 실패해 가려진 뒤 단언(아이콘의 화면 1.5px 선, 값 모름 진행 표시의 도는 표시의 선·크기·색·이름과의 사이)과, 겨누는 자리를 옮긴 사진 비교의 움직임 줄이기 사례(줄이기가 없을 때 돌고 줄이기에서 멈춘다)를 겨눈다. 변이마다 그 단언이 재는 값 하나만 바꾸고 그 단언이 든 스토리나 사례 하나로 좁혀(`-t`, `-g`) 그것이 빨개지는지 본다. 한 스토리 안의 어느 단언이 실패했는지는 가르지 않는다. `tools/mutate.py`로 돈다 | 티켓 02의 수용 기준(아이콘의 단언, 값 모름 진행 표시, 움직임 줄이기 사례) | 사진 변이 둘은 Docker와 판을 고정한 이미지 | lucide-react 1.51.0, Vitest 5.0.2(Storybook 10.6 스토리 테스트, Chromium), Playwright 1.63.0 이미지(`web/tools/visual.ts`의 `IMAGE`). 결과는 일지 2026-10-12-42 |
| `canary/web_design_props_icon_card.toml` | 티켓 02가 고친 `.claude/rules/web-design.md`의 세 문장(props의 계약, 아이콘의 선과 크기, 카드의 그림자)이 `paths` 안의 파일을 Read로 열 때 새 `claude -p` 세션에 실리는지. `tools/canary.py`로 돈다 | 티켓 02의 수용 기준(고친 rules의 확인) | `claude` | 머리 주석의 `# 최신 결과:` 줄 |

## 2026-10-12 결과

- 디자인 파일: 테마 넷(`guncheong`, `nokcheong`, `jacho`, `jjokbit`)이 모두 원색 계열 일곱(`gray` 13단계, `accent`·`danger`·`warning`·`success`·`info` 11단계, `overlay` 7개)과 쓰임새 토큰 23개를 같은 이름으로 든다. 글꼴은 모두 Noto Sans KR과 Noto Sans Mono다. 밀도 촘촘은 본문 14/20px, 표 13/18px, 고정폭 13px, 행 36px, 조작 32px이고 보통은 15/22px, 14/20px, 14px, 44px, 40px다(`design.mjs --refresh`).
- 명암비: 디자인 파일 표가 든 값과 이 프로브의 셈이 테마 넷의 판정 행 44개 모두에서 소수 둘째 자리까지 같았다(어긋남 0). 디자인 파일의 짝 35개는 여덟 벌 모두 기준을 넘었다. 가장 낮은 값은 녹청 라이트의 `border-control`/`bg` 3.14(기준 3)와 `text-muted`/`bg`에 겹친 `bg-selected` 4.77(기준 4.5)이다.
- 디자인 파일 상태 표의 위험 버튼 누름(`danger`를 `bg-active`에 겹친 바탕 위에)은 다크에서 테마 넷 모두 미달했다. `bg` 위 4.05~4.09, `bg-raised` 위 3.67~3.69다(이 프로브의 "바꾸기 전" 묶음).
- 컴포넌트의 짝 8개(위험 버튼 누름은 `bg-selected`)는 여덟 벌 모두 넘었다. 가장 낮은 값은 녹청 다크의 카드 안 위험 버튼 누름 4.507(기준 4.5), 녹청 라이트의 꺼진 스위치 손잡이와 트랙 3.349(기준 3), 녹청 다크의 카드 안 진행 막대 채움과 트랙 3.979(기준 3)다. `bg` 위의 위험 버튼 누름(`danger`/`bg`에 겹친 `bg-selected`)은 디자인 파일의 짝에 있어 따로 세지 않았고, 가장 낮은 값은 군청 다크의 4.95다.
- 반올림: 43개 × 여덟 벌 가운데 반올림 없이 겹치면 판정이 뒤집히는 자리는 녹청 다크의 카드 안 위험 버튼 누름 하나다(반올림 4.507, 반올림 없이 4.494).
- 두 겹(명세의 판정 밖): 행 올림(`bg-hover`, 행은 `bg-raised`) 안의 위험 버튼은 다크에서 테마 넷 모두 미달했다. 올림 4.296~4.314, 누름 3.748~3.764다.
- 같은 값: 여덟 벌 가운데 한 벌이라도 같은 원색을 가리키는 짝은 12개다. 여덟 벌 모두 같은 것은 `accent`와 `focus-ring` 하나다. 나머지 열하나는 값이 다른 벌이 있다(`same-values.mjs`). 그 열하나는 `bg-raised`=`on-accent`(라이트 넷, 스위치 손잡이의 꺼짐과 켜짐), `text`=`primary`(녹청·쪽빛), `accent`=`primary`와 `focus-ring`=`primary`(군청·자초), `text-muted`=`primary-active`(녹청·쪽빛 다크), `bg-raised`=`on-primary`(라이트 넷), `on-accent`=`on-primary`(라이트 넷과 군청·자초 다크), `bg`=`on-primary`(녹청·쪽빛 다크), `border-control`=`text-disabled`(라이트 넷), `border`=`bg-disabled`(다크 넷), `bg-active`=`shadow`(라이트 넷)다.
- 글꼴: `@fontsource/noto-sans-mono` 5.3.0은 `license`가 OFL-1.1이고 LICENSE에 OFL 본문이 있으며, 저작권 줄("Copyright 2022 The Noto Project Authors (https://github.com/notofonts/latin-greek-cyrillic)")에 예약 글꼴 이름이 없다. 설치 때 도는 스크립트(`preinstall`, `install`, `postinstall`, `prepare`)가 없다. 굵기 400·500의 CSS는 각각 `@font-face` 7개(cyrillic-ext, cyrillic, greek-ext, greek, vietnamese, latin-ext, latin)이고 `local(`이 없으며, `url()` 14개가 모두 `./files/`의 있는 파일을 가리킨다. 한글을 덮는 범위는 없다. woff2 합은 400이 103,112바이트, 500이 105,508바이트다. 같은 판의 `@fontsource/noto-sans-kr`도 `./files/` 앞머리, `local(` 0, 설치 스크립트 없음이 같다.
- 손으로 본 것: google/fonts의 `ofl/notosansmono/OFL.txt`(`https://raw.githubusercontent.com/google/fonts/main/ofl/notosansmono/OFL.txt`)를 `curl`로 받아 머리 네 줄을 읽었다. 같은 저작권 줄이고 그 아래가 OFL 본문의 첫 줄이라 예약 글꼴 이름이 없다.
- 재지 못한 것: Noto Sans Mono의 CSS를 Vite(Storybook 빌드)와 Next가 실제 파일로 내는지는 재지 않았다. 같은 Fontsource 모양의 Noto Sans KR은 둘 다 냈다(`.scratch/design-system/probes/tokens/measure.mjs`). 판정은 반영하는 티켓의 Fonts 판정 스토리다.

## 2026-10-12 명세 검토 결과

명세 검토(spec-reviewer 서브에이전트)가 스크래치 프로브로 짚은 것을 to-tickets가 이 폴더의 `chromium.mjs`와 `tailwind.mjs`로 옮겨 다시 돌렸다. 주 체크아웃의 web 폴더를 인자로 넘겼다.

- 직렬화(`chromium.mjs` 1): Chromium 153은 hex 8자리 반투명을 쓴 요소의 `background-color` 계산값을 `rgba(0, 0, 0, 0.04)`·`rgba(255, 255, 255, 0.1)`처럼 알파 소수로 내고, 사용자 정의 속성의 `getPropertyValue`는 넣은 hex(`#0000000a`) 그대로 돌려줬다. 일곱 모두 그랬다. 지금 스토리 도우미 `semanticColor`(`web/packages/ui/src/storybook/expect.ts`)는 `#RRGGBB`가 아니면 던진다(코드를 읽었다).
- 칠한 픽셀(`chromium.mjs` 2): 반투명 상자 안에 글자가 없으면 여덟 자리 모두 칠한 픽셀이 판정(반올림)과 같았다. 글자가 있으면 셋에서 한 채널이 한 단위 어두웠다. 녹청 `bg-raised` 위는 칠한 (46,49,51)이 4.520이고 판정 (47,49,51)은 4.507이다. 녹청 `bg` 위는 4.990 대 4.985, 쪽빛 `bg-raised` 위는 4.540 대 4.535다. 나머지 다섯은 같았다. 그래서 이 기계의 Chromium에서는 칠한 픽셀의 명암비가 판정의 명암비보다 낮은 자리가 없었다(칠한 RGB가 한 단위 어두운 셋은 밝은 `danger` 글자와의 명암비가 오히려 높다). 글자가 있으면 왜 다르게 칠하는지는 가르지 않았고, Linux의 Playwright 이미지(사진 비교의 컨테이너)는 재지 않았다. 티켓 03이 사진 비교에서 그 자리의 칠한 픽셀로 잰다.
- 별칭(`tailwind.mjs` 1): `@theme inline`의 `--text-body: var(--body-size)`는 손으로 쓴 `[data-ui-root] { font-size: var(--text-body) }`가 읽자 `:root, :host`에 선언으로 나왔고, 유틸리티(`h-control`)만 쓰는 `--spacing-control`은 나오지 않았다. 그 규칙을 뺀 입력에서는 `--text-body`도 나오지 않았다. 그래서 별칭이 나오는 까닭은 손으로 쓴 `var()`다. 뿌리에 선언된 `var(--body-size)`는 뿌리에서 풀려 안쪽 요소에 물려진다(사용자 정의 속성의 상속 규칙에서 나온 어림이다. 계산값은 재지 않았다).
- hex(`tailwind.mjs` 2): `optimize`는 `minify`와 상관없이 `#ffffff`를 `#fff`로, `#00000066`을 `#0006`으로 바꿨고 `#ffffff1a`는 그대로 두었다. `@tailwindcss/vite`가 빌드 때만 `optimize`를 부른다는 것은 명세 검토가 설치본을 읽은 것이다(이 프로브는 보지 않는다).
