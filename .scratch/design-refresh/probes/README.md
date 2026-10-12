# design-refresh 프로브

명세(`../spec.md`)가 근거로 드는 측정 스크립트다. 규약은 `docs/agents/issue-tracker.md`의 "프로브와 근거".

재탐색의 디자인 파일(`.scratch/design-system/design/Agent OS Design System.dc.html`)에서 값을 뽑는 것은 design-system의 프로브 `.scratch/design-system/probes/tokens/design.mjs`의 `readRefresh()`(명령은 `--refresh`)다. 첫 탐색 v3를 읽는 `readDesign()`과 함수를 나눠, v3를 읽는 그 폴더의 `setup.mjs`·`measure.mjs`는 그대로 돈다. 이 폴더의 `contrast.mjs`와 `same-values.mjs`가 그것을 import한다.

저장소 루트에서 돈다. `contrast.mjs`와 `same-values.mjs`는 아무것도 설치하지 않고 레지스트리에 닿지 않는다. `font.mjs`는 작업 폴더(저장소 밖)에 `npm pack`으로 받아 풀고, 저장소에는 아무것도 쓰지 않는다.

```sh
node .scratch/design-system/probes/tokens/design.mjs --refresh
node .scratch/design-refresh/probes/contrast.mjs
node .scratch/design-refresh/probes/same-values.mjs
node .scratch/design-refresh/probes/font.mjs <작업 폴더>
```

| 파일 | 재는 것 | 근거로 드는 자리 | 다시 돌 때 | 잰 판 |
|---|---|---|---|---|
| `contrast.mjs` | 디자인 토큰 JSON의 쓰임새 토큰 값으로 여덟 벌(테마 넷 × 모드 둘)의 짝마다 WCAG 2.2 명암비를 센다. 반투명 바탕(`bg-hover`, `bg-active`, `bg-selected`)은 그 아래 바탕에 겹친 색으로 잰다. 짝은 셋으로 나뉜다. 디자인 파일 스크립트의 `PAIRS`를 편 35개(먼저 디자인 파일 표가 든 행마다의 가장 낮은 값과 맞댄다), 컴포넌트 상태 표를 읽고 손으로 옮긴 짝 가운데 디자인 파일이 재지 않은 8개(위험 버튼의 누름은 명세가 바꾼 `bg-selected`), 디자인 파일 상태 표가 적은 위험 버튼 누름(`bg-active`) 2개다 | 명세의 "명암비 짝 43개", "위험 버튼의 누름" | 없음. 디자인 파일을 다시 내보내면 다시 돈다 | 디자인 파일 `Agent OS Design System.dc.html`(README 표의 기준 커밋 `15e41a6`) |
| `same-values.mjs` | 한 벌 안에서 같은 원색을 가리키는 쓰임새 토큰의 짝을 여덟 벌에서 센다. 짝마다 같은 벌과 다른 벌의 수를 낸다. 계산값으로 두 토큰을 가를 수 있는 벌을 고르는 데 쓴다 | 명세의 "계산값을 가를 수 없는 짝" | 없음 | 같은 디자인 파일 |
| `font.mjs` | 고정폭 글꼴 패키지 `@fontsource/noto-sans-mono`와 지금 한글 글꼴 `@fontsource/noto-sans-kr` 5.3.0을 받아, 라이선스(OFL 본문, 저작권 줄의 예약 글꼴 이름), 설치 때 도는 스크립트, 굵기 CSS마다 `@font-face` 수와 서브셋 이름, `local(` 수, `url()`의 앞머리와 가리키는 파일의 유무, 한글(U+AC00)을 덮는 범위의 유무, woff2 바이트 합을 낸다 | 명세의 "글꼴" | 작업 폴더와 레지스트리. `--version`으로 다른 판을 잰다 | `@fontsource/noto-sans-mono` 5.3.0, `@fontsource/noto-sans-kr` 5.3.0, npm 11(Node 24.19.0) |

## 2026-10-12 결과

- 디자인 파일: 테마 넷(`guncheong`, `nokcheong`, `jacho`, `jjokbit`)이 모두 원색 계열 일곱(`gray` 13단계, `accent`·`danger`·`warning`·`success`·`info` 11단계, `overlay` 7개)과 쓰임새 토큰 23개를 같은 이름으로 든다. 글꼴은 모두 Noto Sans KR과 Noto Sans Mono다. 밀도 촘촘은 본문 14/20px, 표 13/18px, 고정폭 13px, 행 36px, 조작 32px이고 보통은 15/22px, 14/20px, 14px, 44px, 40px다(`design.mjs --refresh`).
- 명암비: 디자인 파일 표가 든 값과 이 프로브의 셈이 테마 넷의 판정 행 모두에서 소수 둘째 자리까지 같았다(어긋남 0). 디자인 파일의 짝 35개는 여덟 벌 모두 기준을 넘었다. 가장 낮은 값은 녹청 라이트의 `border-control`/`bg` 3.14(기준 3)와 `text-muted`/`bg`에 겹친 `bg-selected` 4.77(기준 4.5)이다.
- 디자인 파일 상태 표의 위험 버튼 누름(`danger`를 `bg-active`에 겹친 바탕 위에)은 다크에서 테마 넷 모두 미달했다. `bg` 위 4.05~4.09, `bg-raised` 위 3.67~3.69다(이 프로브의 "바꾸기 전" 묶음).
- 컴포넌트의 짝 8개(위험 버튼 누름은 `bg-selected`)는 여덟 벌 모두 넘었다. 가장 낮은 값은 녹청 다크의 카드 안 위험 버튼 누름 4.51(기준 4.5), 녹청 라이트의 꺼진 스위치 손잡이와 트랙 3.35(기준 3), 녹청 다크의 카드 안 진행 막대 채움과 트랙 3.98(기준 3)이다. `bg` 위의 위험 버튼 누름(`danger`/`bg`에 겹친 `bg-selected`)은 디자인 파일의 짝에 있어 따로 세지 않았고, 가장 낮은 값은 군청 다크의 4.95다.
- 같은 값: 여덟 벌 가운데 한 벌이라도 같은 원색을 가리키는 짝은 12개다. 여덟 벌 모두 같은 것은 `accent`와 `focus-ring` 하나다. 나머지 열하나는 값이 다른 벌이 있다(`same-values.mjs`). 그 가운데 컴포넌트 판정에 걸리는 것은 `bg-raised`=`on-accent`(라이트 넷, 스위치 손잡이의 꺼짐과 켜짐), `text`=`primary`(녹청·쪽빛), `accent`=`primary`(군청·자초), `border-control`=`text-disabled`(라이트 넷), `border`=`bg-disabled`(다크 넷), `bg-active`=`shadow`(라이트 넷)다.
- 글꼴: `@fontsource/noto-sans-mono` 5.3.0은 `license`가 OFL-1.1이고 LICENSE에 OFL 본문이 있으며, 저작권 줄("Copyright 2022 The Noto Project Authors (https://github.com/notofonts/latin-greek-cyrillic)")에 예약 글꼴 이름이 없다. 설치 때 도는 스크립트(`preinstall`, `install`, `postinstall`, `prepare`)가 없다. 굵기 400·500의 CSS는 각각 `@font-face` 7개(cyrillic-ext, cyrillic, greek-ext, greek, vietnamese, latin-ext, latin)이고 `local(`이 없으며, `url()` 14개가 모두 `./files/`의 있는 파일을 가리킨다. 한글을 덮는 범위는 없다. woff2 합은 400이 103,112바이트, 500이 105,508바이트다. 같은 판의 `@fontsource/noto-sans-kr`도 `./files/` 앞머리, `local(` 0, 설치 스크립트 없음이 같다.
- 손으로 본 것: google/fonts의 `ofl/notosansmono/OFL.txt` 머리도 같은 저작권 줄이고 예약 글꼴 이름이 없다(WebFetch로 읽었다).
- 재지 못한 것: Noto Sans Mono의 CSS를 Vite(Storybook 빌드)와 Next가 실제 파일로 내는지는 재지 않았다. 같은 Fontsource 모양의 Noto Sans KR은 둘 다 냈다(`.scratch/design-system/probes/tokens/measure.mjs`). 판정은 반영하는 티켓의 Fonts 판정 스토리다.
