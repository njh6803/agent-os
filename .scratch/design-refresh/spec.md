# 디자인 재탐색 반영: 테마 넷과 글꼴 둘, 밀도 두 벌을 `packages/ui`에 옮기고 컴포넌트 아홉의 모양을 새 디자인에 맞춘다

Status: ready-for-agent

슬라이스 4(`design-refresh`). 결정의 근거는 `docs/adr/0026`의 2026-10-12 이력 "테마는 넷이고 색만 바꾸며, 글꼴은 모든 테마가 Noto Sans KR과 Noto Sans Mono를 쓴다"이다. 그 이력이 바꾸지 않은 구조(패키지 하나, px 디자인 토큰, 색 토큰의 두 층, `data-theme`·`data-mode`, 스토리 테스트와 사진 비교)는 ADR 0026 본문과 지난 이력, 그리고 그것을 처음 지은 `.scratch/design-system/spec.md`가 원천이다. 값의 원천은 재탐색의 디자인 파일 `.scratch/design-system/design/Agent OS Design System.dc.html`이다(그 폴더 `README.md`의 표, 기준 커밋 `15e41a6`). 비교판 `Agent OS Pairings.dc.html`은 밀도의 이름과 수치가 최종과 달라 읽지 않는다. 그 밖에 `plan.md`의 design-refresh 행, 재탐색 프롬프트 `.scratch/design-system/design/refresh-prompt.md`의 "고른 뒤" 4(함께 고칠 자리), 방향 전환의 일지(2026-10-12-11), 고른 일지(2026-10-12-22), 그리고 이 명세의 일지(2026-10-12-28)다.

이 명세는 설계 인터뷰 없이 썼다. 결정은 위 이력이 사용자 승인으로 모두 정했으므로, 이력과 디자인 파일, 일지가 대화를 대신했다. 용어는 `CONTEXT.md`의 화면 절(디자인 시스템, 디자인 토큰, 원색 토큰, 쓰임새 토큰, 테마, 모드, 밀도)과 실행·인터럽트 절(일시정지, 끝남, 실패, 결말 없음, 승인, 거부)을 따른다. 단독 "토큰"은 쓰지 않는다(ADR 0026 Consequences). 밀도는 이 명세가 용어집에 세웠고, 테마의 뜻을 "색의 한 벌"로 고쳤다.

**다섯은 사용자가 골랐다.** 컴포넌트 아홉은 모양만 새 디자인을 따르고 props는 지금 계약을 지킨다. 위험 버튼의 누름 바탕은 `bg-selected`다. 밀도는 `data-density`가 고르고 속성이 없으면 화면 폭을 따른다. 이음매는 지금 둘 그대로이고 사진은 밀도 둘을 모두 찍는다. 이 넷은 명세를 쓰기 전에 물었다. 다섯째는 Claude Design에 보일 보여 주기용 미리보기를 패키지의 스토리로 두는 것이고, 셀프 리뷰가 ADR 0026 본문과의 충돌을 짚어 물었다. 다섯 모두 추천을 맨 앞에 둔 선택 화면에서 추천대로 골랐다. **명세가 스스로 정한 것은 각 절에 "(명세가 정했다)"로 표시했고 열여덟이다.** 표시가 없는 것은 ADR, 디자인 파일, 기존 규칙에서 나왔다. **ADR 이력은 없다.** 사용자가 고른 다섯과 명세가 정한 것 가운데 ADR의 문장을 바꾸는 것이 없다. `data-density`는 테마의 키와 선택자처럼 명세가 정하는 모양의 일이다(design-system 명세의 "테마와 모드" 절). 사진에 밀도를 더해도 "기본 테마의 라이트와 다크만 찍는다"(둘째 2026-10-06 이력)는 글자 그대로 참이다. 보여 주기용 미리보기를 패키지의 스토리로 두므로 ADR 0026 본문의 "스토리 한 벌이 갤러리, 실제 브라우저 테스트, Claude Design의 원천을 함께 맡는다"도 그대로 참이다.

측정은 `.scratch/design-refresh/probes/`(`contrast.mjs`, `same-values.mjs`, `font.mjs`)와 design-system의 `.scratch/design-system/probes/tokens/design.mjs`(`--refresh`. 이 명세가 새 파일을 읽게 고쳤다)이고, 결과는 `.scratch/design-refresh/probes/README.md`의 "2026-10-12 결과"다.

## Problem Statement

사용자는 처음 올린 디자인 시스템을 보고 예쁘지 않다며 관리 화면에 맞게 다시 디자인해 달라고 했다(일지 2026-10-12-11). Claude Design에서 다시 고른 결과(테마 넷, 글꼴 둘, 밀도 두 벌, 컴포넌트 아홉의 새 모양)는 승인되어 ADR 0026의 이력이 되었지만, 값과 모양은 아직 디자인 파일 안에만 있다. 코드의 `web/packages/ui`는 여전히 옛 테마 다섯(먹 기본), 테마마다 다른 고정폭 글꼴, 한 벌의 크기, 칠한 바탕의 상태 배지와 알림을 든다.

관리 화면(admin-style)은 Claude Design에서 이 디자인 시스템으로 화면을 그리기 전에 그것이 코드에 서기를 기다린다. 그리기 직전에 `/design-sync`로 올리는 것이 코드이기 때문이다(ADR 0025·0026). 지금 올리면 옛 모양이 올라간다. 그리고 지금 Claude Design에 올라간 카드는 판정용 스토리를 그대로 옮긴 것이라 시험지처럼 보이고, 색과 글자, 간격을 소개하는 기초 카드가 없다(일지 2026-10-12-11의 진단).

## Solution

**테마는 넷이고 색만 다르다.** 군청(`guncheong`), 녹청(`nokcheong`, 기본), 자초(`jacho`), 쪽빛(`jjokbit`)이 옛 다섯을 대신한다. 테마마다 원색 토큰을 두고, 쓰임새 토큰 23개가 모드마다 그 가운데 하나를 가리킨다. 이름은 디자인 파일의 것을 그대로 쓴다. 주 버튼의 색(`primary` 묶음)도 쓰임새 토큰이라, 군청과 자초는 강조색으로, 녹청과 쪽빛은 글자색을 뒤집은 먹색으로 칠한다.

**글꼴은 모든 테마가 Noto Sans KR(400·500·600)과 Noto Sans Mono(400·500)를 쓴다.** JetBrains Mono와 IBM Plex Mono, IBM의 설치 스크립트를 끄던 줄이 빠진다.

**밀도는 두 벌(촘촘, 보통)이고 `data-density`가 고른다.** 속성이 없으면 화면 폭 768px 이상에서 촘촘, 미만에서 보통이다. 그래서 관리 화면은 아무것도 달지 않고, 위젯이 `regular`를 단다. 버튼과 입력의 높이, 본문·표·고정폭 글자의 크기가 밀도를 따른다.

**컴포넌트 아홉은 새 디자인 파일의 상태 표와 치수를 따르고 props는 지금 계약을 지킨다.** 디자인이 없앤 모양을 고르던 prop만 뺀다(버튼의 `size`, 카드의 `elevation`, 진행 표시의 `tone`, 아이콘의 `"24"`). 상태 배지와 알림은 바탕을 칠하지 않고 테두리와 아이콘으로 가르며, 카드에서 그림자가 사라진다.

**판정의 자리는 지금 둘 그대로다.** 스토리 테스트가 여덟 벌(테마 넷 × 모드 둘)의 쓰임새 토큰과 명암비 짝 43개, 밀도, 글꼴 다섯 벌을 보고, 사진 비교가 기본 테마(녹청)의 라이트·다크 × 밀도 둘을 찍는다.

**Claude Design에는 보여 주기용 스토리와 기초 카드, 새 목록 타일을 함께 올린다.** 컴포넌트마다 실제 쓰임을 보이는 스토리를 패키지에 더하고, `/design-sync`가 카드를 지을 때 판정용 스토리를 뺀다. 보여 주기용 스토리도 스토리 테스트와 사진을 지난다. 색과 글자, 간격, 밀도를 소개하는 기초 카드는 CSS 변수만 읽는 HTML이다. 올리는 것은 사람이 시작하는 `/design-sync`다.

## User Stories

### 운영자(관리 화면)

1. 운영자로서, 관리 화면이 Claude Console이나 OpenAI Platform처럼 조용하기를 바란다. 바탕과 회색이 무채색이거나 아주 옅은 색조이고, 강조색은 선택·링크·포커스에만 쓰이기 때문이다.
2. 운영자로서, 데스크톱에서 실행 목록을 한 화면에 많이 훑고 싶다. 폭 768px 이상에서 밀도가 촘촘(행 36px, 본문 14px)이기 때문이다.
3. 운영자로서, 휴대폰에서 관리 화면을 열면 손가락으로 누르기 쉬운 크기이기를 바란다. 768px 미만에서 밀도가 보통(조작 40px, 본문 15px)이기 때문이다.
4. 운영자로서, 실행의 상태 넷을 배지의 아이콘과 글자로 가르고 싶다. 배지가 바탕을 칠하지 않고 상태색의 글자와 아이콘, 옅은 테두리로 그려지기 때문이다.
5. 운영자로서, 실패 알림이 표와 카드 사이에서 눈에 띄되 화면을 물들이지 않기를 바란다. 알림이 올라온 바탕에 상태색 아이콘과 제목으로 그려지기 때문이다.
6. 운영자로서, 테마를 넷 가운데 하나로 고르고 싶다(고르는 화면은 admin-style). 테마 목록이 넷을 들기 때문이다.
7. 운영자로서, 어느 테마를 골라도 글꼴과 크기, 모서리가 같기를 바란다. 테마는 색만 바꾸기 때문이다.
8. 운영자로서, 실행 ID와 시각, 도구 이름을 같은 고정폭 글꼴로 읽고 싶다. 모든 테마가 Noto Sans Mono를 쓰기 때문이다.
9. 운영자로서, 어둡게 쓰는 운영체제에서도 모든 글자를 편하게 읽고 싶다. 여덟 벌 모두 명암비 짝 43개가 기준을 넘기 때문이다.
10. 운영자로서, 위험 버튼을 누르는 순간에도 글자가 흐려지지 않기를 바란다. 누름 바탕이 다크에서도 4.5:1을 넘는 `bg-selected`이기 때문이다.
11. 운영자로서, 주 버튼과 링크를 혼동하지 않기를 바란다. 녹청과 쪽빛에서 주 버튼은 먹색이고 강조색은 링크와 선택에만 남기 때문이다.
12. 운영자로서, 키보드로 관리 화면을 쓸 때 모든 조작에 포커스 링이 보이기를 바란다.

### 최종 사용자(위젯)

13. 최종 사용자로서, 위젯이 사이트의 창 폭과 상관없이 같은 크기로 보이기를 바란다. 위젯이 `data-density="regular"`를 달기 때문이다(그 코드는 web-widget).
14. 최종 사용자로서, 위젯의 버튼을 손가락으로 쉽게 누르고 싶다. 보통의 조작은 40px이기 때문이다.
15. 최종 사용자로서, 승인 묻기의 도구 이름과 인자를 고정폭 글자 그대로 읽고 싶다.
16. 최종 사용자로서, 움직임 줄이기를 켰다면 불러오는 중의 도는 표시가 멈추기를 바란다.

### 위젯 개발자(web-widget)

17. 위젯 개발자로서, 호스트에 `data-density="regular"`만 달면 사이트 창이 넓어도 보통으로 그리고 싶다. 속성이 없을 때만 화면 폭을 따르기 때문이다.
18. 위젯 개발자로서, 페이지 안 번들이 사이트 문서에 등록할 고정폭 글꼴이 하나이기를 바란다. 테마가 글꼴을 바꾸지 않기 때문이다.
19. 위젯 개발자로서, 테마를 바꿔도 등록한 글꼴을 다시 받지 않기를 바란다.
20. 위젯 개발자로서, 디자인 토큰 CSS를 shadow root에 넣어도 밀도와 테마가 호스트의 속성을 따르기를 바란다(`:host(...)` 짝).

### 관리 화면 개발자(admin-style)

21. 관리 화면 개발자로서, `html`에 밀도 속성을 달지 않아도 데스크톱과 모바일의 밀도가 갈리기를 바란다. 스크립트 없이 CSS가 고르기 때문이다.
22. 관리 화면 개발자로서, 표의 행 높이와 표 글자, 고정폭 글자를 밀도를 따르는 유틸리티(`h-row`, `text-table`, `text-mono`)로 쓰고 싶다.
23. 관리 화면 개발자로서, 옆 탐색의 폭(256px), 탐색 항목의 높이(36px), 위 막대의 높이(52px)를 디자인 토큰으로 쓰고 싶다.
24. 관리 화면 개발자로서, 설정 화면의 테마 카드 넷이 패키지의 테마 목록(키, 이름, 기본)을 읽게 하고 싶다.
25. 관리 화면 개발자로서, 고른 탐색 항목과 표의 행 올림을 `bg-selected`·`bg-hover`로 칠하고 싶다. 쓰임새 토큰에 반투명 바탕 셋이 있기 때문이다.

### 디자인 시스템에 기여하는 에이전트

26. 기여자로서, 쓰임새 토큰의 이름이 디자인 파일과 같기를 바란다. 디자인 파일의 상태 표를 읽고 그대로 클래스로 옮길 수 있기 때문이다.
27. 기여자로서, 옛 쓰임새 토큰(`tint`, `danger-tint`, `divider` 등)의 클래스를 쓰면 스토리 테스트가 빨개지기를 바란다. 규칙이 없는 클래스는 afterEach가 잡기 때문이다.
28. 기여자로서, 밀도를 따르는 높이를 숫자로 박지 않고 `h-control`로 쓰고 싶다.
29. 기여자로서, 반투명 바탕 위의 명암비도 판정되기를 바란다. 판정 함수가 그 아래 바탕에 겹쳐 재기 때문이다.
30. 기여자로서, 대비가 부족한 짝을 만들면 여덟 벌 가운데 어느 테마·모드의 어느 짝인지 메시지로 알고 싶다.
31. 기여자로서, 아이콘의 선이 크기와 상관없이 화면에서 1.5px이기를 바란다.
32. 기여자로서, 테마를 하나 더할 때 원색 블록 하나와 테마 목록의 한 줄, 그리고 주 버튼이 강조색이면 그 대응 묶음만 적으면 되기를 바란다.
33. 기여자로서, 바꾼 모양이 사진 비교에서 밀도마다 보이기를 바란다.
34. 기여자로서, Claude Design에 올라갈 보여 주기용 스토리도 판정용 스토리처럼 axe와 클래스 판정, 사진을 지나기를 바란다. 같은 패키지의 스토리이기 때문이다.

### 디자인을 고치는 사람(사용자)

35. 사용자로서, Claude Design에서 디자인 시스템을 열면 컴포넌트마다 실제 쓰임을 보이는 카드를 보고 싶다. 판정용 스토리의 나열은 시험지처럼 보이기 때문이다.
36. 사용자로서, 색(원색과 쓰임새), 글자 단계, 간격과 모서리, 밀도를 소개하는 기초 카드를 보고 싶다.
37. 사용자로서, 프로젝트 목록의 타일이 새 기본 테마의 색으로 보이기를 바란다.
38. 사용자로서, 디자인 파일의 값과 코드의 값이 옮길 때 한 번은 같다는 것을 알고 싶다. 그 뒤의 원천은 코드다.

### 리뷰어와 CI

39. 리뷰어로서, 사진 비교의 정답이 바뀐 PR에서 밀도마다의 사진을 보고 싶다.
40. 리뷰어로서, 설치 때 원격 측정 스크립트가 돌 일이 사라지기를 바란다. `@ibm/plex-mono`가 빠지고, 새 글꼴 패키지에는 설치 스크립트가 없기 때문이다.
41. 리뷰어로서, 살아 있는 문서에 옛 테마 이름과 옛 글꼴이 남지 않기를 바란다.

## Implementation Decisions

### 이음매 (사용자가 골랐다)

- **주 이음매는 지금 그대로 `packages/ui`의 스토리 테스트다.** 판정 스토리와 컴포넌트 스토리, Storybook 미리보기 설정의 afterEach(규칙 없는 클래스와 임의값), axe가 실제 chromium에서 돈다(design-system 명세의 이음매 절).
- **둘째는 사진 비교 게이트다.** 실제 입력의 올림·누름과 움직임 줄이기, 속성이 없을 때의 시스템 모드와 화면 폭은 여기의 Playwright가 본다.
- **더하지 않는 것.** 새 이음매, 디자인 토큰 CSS를 글자로 읽는 단위 테스트, 디자인 파일을 읽는 영구 테스트.

### 값의 원천과 옮기기 (명세가 정했다)

- **값은 커밋한 디자인 파일이 원천이고 `design.mjs --refresh`가 뽑는 디자인 토큰 JSON 그대로다.** 이 명세는 hex를 다시 적지 않는다. 디자인 파일의 OKLCH 공식과 단계 밝기 표는 코드에 옮기지 않는다(design-system 명세와 같은 이유: 생성 단계를 두지 않는다).
- **옮길 때 한 번 대조한다.** 디자인 토큰 CSS를 바꾸는 티켓은 `design.mjs --refresh --out`의 JSON과 코드의 값(원색, 쓰임새 대응과 주 버튼의 갈래, 밀도, 공통 크기)이 같은지 한 번 보고 일지에 적는다. 쓰임새 토큰의 이름이 디자인 파일과 같아(아래) 이름으로 맞댈 수 있다. 영구 테스트는 디자인 파일을 읽지 않는다.
- **hex는 소문자다.** Prettier가 CSS의 hex를 소문자로 바꾼다. 디자인 파일 JSON은 대문자다.

### 색 — 원색 토큰 (디자인 파일이 골랐다. 이름은 명세가 정했다)

- **계열과 단계는 디자인 파일 그대로다.** `gray`는 13단계(`0`, `50`, `100`, …, `800`, `850`, `900`, `950`. `0`은 흰색), `accent`·`danger`·`warning`·`success`·`info`는 11단계(`50`~`950`)다. 이름은 `--<계열>-<단계>`(예: `--gray-850`)이고 네 테마가 같다.
- **반투명 계열 `overlay`는 일곱이고 테마와 무관하다.** `black-4`, `black-7`, `black-12`, `black-40`, `white-6`, `white-10`, `white-16`(뒤 숫자는 불투명도 %)이고 이름은 `--overlay-black-4`다. 값이 테마마다 같아 테마 선택자가 아니라 뿌리(`:root`, `:host`)에 한 번 둔다 (명세가 정했다).
- **테마 사이에 같은 값도 있다.** 위험·경고·성공 계열은 네 테마가 같고, 회색은 군청과 자초가 같다(디자인 파일이 같은 채도와 색상각을 썼다). 그래도 원색 블록은 테마마다 다 적는다. 테마 하나를 읽으면 그 값이 다 보이게 하기 위해서다.
- **유틸리티가 없다.** 지금처럼 `@theme` 밖의 CSS 변수다.

### 색 — 쓰임새 토큰 (디자인 파일이 골랐다. 코드의 이름은 명세가 정했다)

**쓰임새 토큰의 이름은 디자인 파일의 이름을 그대로 쓴다.** CSS 변수는 `--<이름>`이고 유틸리티는 지금처럼 `--color-<이름>`을 거친다. 그래서 `bg-bg-raised`, `text-text-muted`, `outline-focus-ring`처럼 머리가 겹치는 클래스가 생긴다. 이름을 줄여(`raised`, `muted`) 겹침을 피하는 대신 디자인 파일의 상태 표와 이름으로 맞대는 쪽을 골랐다. 예외는 그림자 하나다. 디자인 파일의 `shadow`는 코드에서 `--shadow-color`다. Tailwind의 그림자 이름 공간(`--shadow-*`)과 읽을 때 헷갈리기 때문이고, design-system 명세가 같은 이유로 같은 이름을 골랐다.

| 이름 | 쓰임 | 라이트 | 다크 |
|---|---|---|---|
| `bg` | 바탕 | `gray-50` | `gray-950` |
| `bg-raised` | 올라온 바탕(카드, 알림, 입력, 표) | `gray-0` | `gray-900` |
| `text` | 글자 | `gray-900` | `gray-100` |
| `text-muted` | 흐린 글자, 자리 글자, 진행 막대의 채움 | `gray-500` | `gray-300` |
| `border` | 장식 테두리(카드, 배지, 알림, 보조·위험 버튼). 명암비 기준이 없다 | `gray-200` | `gray-800` |
| `accent` | 강조(링크, 선택, 켜진 스위치) | `accent-600` | `accent-400` |
| `on-accent` | 강조 위 글자, 켜진 스위치의 손잡이 | `gray-0` | `accent-950` |
| `danger` | 위험 | `danger-600` | `danger-400` |
| `warning` | 경고 | `warning-600` | `warning-400` |
| `success` | 성공 | `success-600` | `success-400` |
| `info` | 정보 | `info-600` | `info-400` |
| `focus-ring` | 포커스 링 | `accent-600` | `accent-400` |
| `border-control` | 조작의 테두리(입력, 꺼진 스위치의 트랙) | `gray-400` | `gray-400` |
| `primary` | 주 버튼 | 아래 갈래 | 아래 갈래 |
| `on-primary` | 주 버튼 위 글자 | `gray-0` | 아래 갈래 |
| `primary-hover` | 주 버튼 올림 | 아래 갈래 | 아래 갈래 |
| `primary-active` | 주 버튼 누름 | 아래 갈래 | 아래 갈래 |
| `bg-hover` | 올림 바탕(겹친다) | `overlay-black-4` | `overlay-white-6` |
| `bg-active` | 누름 바탕(겹친다), 진행 막대의 트랙 | `overlay-black-12` | `overlay-white-16` |
| `bg-selected` | 고른 바탕(겹친다), 위험 버튼 누름 | `overlay-black-7` | `overlay-white-10` |
| `text-disabled` | 쓸 수 없는 글자. 명암비 기준이 없다 | `gray-400` | `gray-600` |
| `bg-disabled` | 쓸 수 없는 바탕 | `gray-100` | `gray-800` |
| `shadow-color` | 떠 있는 것의 그림자 | `overlay-black-12` | `overlay-black-40` |

- **주 버튼의 갈래.** 녹청과 쪽빛(먹색)은 라이트에서 `primary`·`primary-hover`·`primary-active`가 `gray-900`·`gray-800`·`gray-700`이고, 다크에서 `gray-100`·`gray-200`·`gray-300`이며 `on-primary`는 `gray-950`이다. 군청과 자초(강조색)는 라이트에서 `accent-600`·`accent-700`·`accent-800`이고, 다크에서 `accent-400`·`accent-300`·`accent-200`이며 `on-primary`는 `accent-950`이다.
- **기본 대응은 기본 테마의 갈래다 (명세가 정했다).** 쓰임새 블록(`:root, :host, [data-theme], [data-mode]`와 다크의 짝)은 녹청의 먹색 갈래로 두고, 군청과 자초의 `primary` 묶음을 그 뒤에 `[data-theme="guncheong"][data-mode=…]`와 시스템 모드의 짝, `:host(…)`의 짝으로 덮는다. 지금 공문의 예외와 같은 모양이다. 나머지 열아홉은 네 테마 모두 위 표 그대로다.
- **`color-scheme`.** 지금처럼 라이트·다크 규칙이 함께 바꾼다.
- **쓰임새를 테마나 모드를 다는 요소마다 다시 선언하는 이유는 그대로다.** 사용자 정의 속성의 `var()`는 선언한 요소에서 풀린다(design-system 명세의 "디자인 토큰 CSS의 모양" 절).

### 테마 (ADR 0026의 2026-10-12 이력. 선택자는 명세가 정했다)

| 키 | 이름 | 주 버튼 | 디자인 파일의 한 줄 |
|---|---|---|---|
| `guncheong` | 군청 | 강조색 | 짙은 군청을 강조로 쓴다. 회색은 무채색이다 |
| `nokcheong` | 녹청(기본) | 먹색 | 푸른 녹청을 강조로 쓴다. 회색에 아주 옅은 푸른 기운이 있다 |
| `jacho` | 자초 | 강조색 | 자줏빛을 강조로 쓴다. 회색은 무채색이다 |
| `jjokbit` | 쪽빛 | 먹색 | 쪽빛을 강조로 쓴다. 회색에 아주 옅은 따뜻한 기운이 있다 |

- **테마 목록.** 패키지가 진입점 `.`에서 내보내는 테마 목록(키, 이름)이 넷이 되고 기본 테마는 `nokcheong`이다. 순서는 위 표(디자인 파일의 순서)다. Storybook globals, 판정 스토리, 사진 비교, 앱의 고르기 화면이 그 목록을 읽는다.
- **선택자.** 원색 블록은 `:root, :host, [data-theme="nokcheong"]`(기본)와 테마마다 `[data-theme="<키>"]`, 그리고 `:host(…)` 짝이다. 속성이 없는 문서와 호스트는 녹청이다.
- **테마가 바꾸지 않는 것.** 글꼴, 굵기, 크기, 모서리, 밀도. 지금 테마 블록이 들던 `--sans`, `--mono`, `--weight-mid`는 테마 블록에서 빠진다. 글꼴 변수(`--sans`, `--mono`)는 뿌리에 한 번 둔다 (명세가 정했다). 페이지 안 위젯이 감싼 요소에서 그 둘을 다시 정하는 길(design-system 명세의 글꼴 절)은 그대로다.

### 밀도 (사용자가 골랐다. 값은 디자인 파일이고 변수와 유틸리티의 이름은 명세가 정했다)

- **고르는 법.** `data-density`의 값은 `compact`(촘촘)와 `regular`(보통)이고, 테마·모드와 같은 요소에 단다. 속성이 없으면 화면 폭 768px 이상에서 촘촘, 미만에서 보통이다. 모드가 속성이 없으면 시스템 설정을 따르는 것과 같은 모양이다. 관리 화면은 아무것도 달지 않고(ADR 0026 이력의 "관리 화면은 폭 768px 이상에서 촘촘, 미만에서 보통"), 위젯은 호스트(페이지 안)와 iframe 문서의 `html`에 `regular`를 단다(같은 이력의 "위젯은 보통"). 위젯이 빠뜨리면 페이지 안 위젯이 사이트의 넓은 창에서 촘촘해진다. 그것을 막는 일은 web-widget이다.
- **값.** 촘촘은 `--body-size` 14px, `--body-lh` 20px, `--table-size` 13px, `--table-lh` 18px, `--mono-size` 13px, `--row-h` 36px, `--control-h` 32px이다. 보통은 15px, 22px, 14px, 20px, 14px, 44px, 40px이다. 변수 이름은 디자인 파일이 쓴 CSS 변수 그대로다.
- **선택자.** 보통의 값은 `:root, :host`와 `[data-density="regular"]`·`:host([data-density="regular"])`에, 촘촘의 값은 `[data-density="compact"]`·`:host([data-density="compact"])`와 `@media (width >= 768px)` 아래의 `:root:not([data-density])`·`:host(:not([data-density]))`에 둔다. 값이 `var()`가 아닌 글자 그대로라 쓰임새 토큰처럼 요소마다 다시 선언할 일이 없고 물려받는다. 속성이 없는 안쪽 요소는 바깥 요소의 밀도를 따른다.
- **유틸리티.** `@theme inline`이 `--text-body: var(--body-size)`와 그 `--line-height`, `--text-table`, `--text-mono`(줄 높이는 `--table-lh`. 디자인 파일의 코드 칸이 "mono / table-lh"다), `--spacing-control: var(--control-h)`, `--spacing-row: var(--row-h)`를 둔다. 그래서 `text-body`, `text-table`, `text-mono`, `h-control`, `size-control`, `h-row`가 밀도를 따른다. 이 별칭은 inline이라 CSS 변수로 나오지 않는다(둘째 2026-10-12 이력). Claude Design의 디자인 에이전트가 인라인 `style`에 쓸 것은 원천인 밀도 변수(`--body-size` 등)이고, 밀도 선택자에서 늘 나온다.
- **화면 중단점은 하나다.** 밀도의 미디어 조건은 `wide:`와 같은 768px이고 새 중단점을 두지 않는다. 판정 스토리 Responsive가 보는 시트의 px 조건은 지금처럼 `(width >= 360px)`과 `(width >= 768px)` 둘이다.
- **Storybook.** globals에 `density`(`auto` 기본 | `compact` | `regular`)를 더한다. `auto`이면 속성을 두지 않는다. 데코레이터와 shadow 틀이 테마·모드처럼 문서 뿌리나 호스트에 단다 (명세가 정했다. 지금 `mode`의 `system`과 같은 모양이다).

### 공통 크기 (디자인 파일이 골랐다. Tailwind의 이름은 명세가 정했다)

**크기의 디자인 토큰은 지금의 이름 체계를 지키고 값과 수만 디자인 파일에 맞춘다.** 간격은 Tailwind의 숫자 뜻(`p-4`가 16px)을 지켜야 에이전트가 학습한 숫자가 틀린 px를 조용히 내지 않는다. 디자인 파일의 `space-5`(24px)를 `--spacing-5`로 두면 `p-5`가 Tailwind 기본의 20px이 아니라 24px이 된다. 모서리도 Tailwind 기본 이름(`rounded-md`는 6px)과 겹치지 않게 지금 이름(`s`, `m`, `l`)을 쓴다. 굵기는 Tailwind 기본과 값이 같은 `semibold`(600)로 바꾼다.

| 묶음 | 디자인 토큰 | 값 | 지금과 다른 것 |
|---|---|---|---|
| 글자 | `title` | 24/32px, 600 | 그대로 |
| | `body`, `table`, `mono` | 밀도를 따른다(위 절) | `body`가 밀도를 따른다. `table`과 `mono`가 는다 |
| | `small` | 12/16px | 13/20px에서 줄었고 테마의 중간 굵기를 쓰지 않는다 |
| | `badge` | 12/16px, 500 | 는다(상태 배지) |
| | `heading`, `caption`, `code` | 없음 | 빠진다. 디자인 파일의 글자 단계에 없다 |
| 굵기 | `regular` `medium` `semibold` | 400 500 600 | `strong`이 `semibold`가 되고 테마의 `mid`가 빠진다 |
| 간격 | `0` `1` `2` `3` `4` `6` `8` | 0 4 8 12 16 24 32px | 그대로(디자인 파일의 `space-1`~`space-6`) |
| 조작 높이 | `control`, `control-s` | 밀도를 따른다, 28px | `control-m`(40)·`control-s`(32)가 `control`과 28px의 `control-s`가 된다 |
| 행 높이 | `row` | 밀도를 따른다 | 는다(표) |
| 아이콘 | `icon-xs` `icon-s` `icon-m` | 14 16 20px | `icon-l`(24)이 빠진다 |
| 틀 | `nav`, `nav-item`, `top-bar` | 256 36 52px | 는다(옆 탐색의 폭, 탐색 항목의 높이, 768px 미만의 위 막대) |
| 부품 치수 | `switch-w` `switch-h` `switch-knob` `switch-inset` `progress` `badge` `badge-start` | 40 24 20 2 4 22 6px | 스위치(36×20, 손잡이 12)와 진행 트랙(6)이 바뀌고, 손잡이·띄움·배지가 는다. `row-touch`(48)와 `field-multi`(88)는 빠진다 |
| 모서리 | `s` `m` `l` `full` | 4 8 12 999px | `m`이 6에서, `l`이 10에서 바뀐다 |
| 그림자 | `float` | `0 8px 24px` + `0 1px 2px`, 색은 `--shadow-color` | `1`·`2`·`3`이 `float` 하나가 된다. 떠 있는 것(위젯 창, 메뉴)에만 쓴다 |
| 기준 폭 | 위젯의 자리 360px(`@wide:`), 관리 화면의 창 768px(`wide:`) | | 그대로. 디자인 파일에는 360px이 없지만 승인 묻기의 버튼 쌓기(`web-design.md`)가 쓴다 |
| 움직임 | `spin` | `spin 0.8s linear infinite` | 1초에서 디자인 파일의 "한 바퀴 800ms"로 바뀐다. `progress`(값 모름 막대)는 빠진다(아래 진행 표시) |

- **화면 여백**(데스크톱 32px, 모바일 16px)은 간격 `8`과 `4`로 쓰고 따로 두지 않는다. **위젯 자리의 최소 폭 320px**은 리플로의 하한이라 디자인 토큰이 아니라 테스트의 폭이다. **누름 목표의 최소 24px**은 ADR 0026의 첫째 2026-10-06 이력이 정한 하한이고 디자인 토큰이 아니다. **테두리 1px, 포커스 링 2px과 띄움 2px**은 지금처럼 Tailwind의 숫자 유틸리티로 쓴다.
- **부품 치수의 이름**은 위 표대로이고, 쓰는 컴포넌트는 아래 절이다. 스위치 줄의 최소 높이(`row-touch`)와 여러 줄 입력의 최소 높이(`field-multi`)는 디자인 파일의 치수에 없어 뺀다. 여러 줄 입력의 높이는 줄 수(`rows`, 기본 3)가 정한다 (명세가 정했다).
- **`@theme static`은 그대로다.** 그 블록의 디자인 토큰(글자 그대로의 값)은 쓰이지 않아도 모두 CSS 변수로 나온다(둘째 2026-10-12 이력). 판정 스토리 ThemeTokensEmitted가 본다. 밀도를 따르는 `body`·`table`·`mono`·`control`·`row`는 `@theme inline`의 별칭이라 이 문장 밖이다(위 밀도 절).

### 글꼴 (ADR 0026의 2026-10-12 이력. 확인은 이 명세가 했다)

- **글꼴과 굵기.** 한글은 Noto Sans KR 400·500·600, 고정폭은 Noto Sans Mono 400·500이다. 고정폭 500은 승인 묻기의 도구 이름(`font-medium`)이다.
- **패키지.** `@fontsource/noto-sans-mono` 5.3.0을 `packages/ui`의 `dependencies`에 더하고 `@fontsource/jetbrains-mono`와 `@ibm/plex-mono`를 뺀다. 글꼴 CSS는 Noto Sans KR처럼 굵기 CSS 둘(`400.css`, `500.css`)을 `@import`하고, IBM split 파일의 `@font-face` 열 개를 지운다. `web/pnpm-workspace.yaml`의 `allowBuilds`에서 `@ibm/plex-mono` 줄을 빼고 머리 주석을 고친다.
- **잰 것.** `@fontsource/noto-sans-mono` 5.3.0은 OFL-1.1이고 저작권 줄에 예약 글꼴 이름이 없으며, 설치 때 도는 스크립트가 없어 `allowBuilds`에 더할 것이 없다. 굵기 CSS는 `@font-face` 7개(라틴, 키릴, 그리스, 베트남어 서브셋)이고 `local()`이 없으며 `url()`이 모두 `./files/`의 있는 파일을 가리킨다. Noto Sans KR과 같은 모양이다(`font.mjs`). google/fonts 사본(`ofl/notosansmono/OFL.txt`)의 머리에도 예약 글꼴 이름이 없다(WebFetch로 손으로 봤다). ADR 0026 이력이 "들이는 기능이 확인한다"로 넘긴 예약 글꼴 이름과 서브셋은 이것으로 닫혔다.
- **한글은 덮지 않는다.** 고정폭 글꼴 스택은 `"Noto Sans Mono", ui-monospace, monospace`이고, 고정폭 칸의 한글은 지금 JetBrains Mono·IBM Plex Mono 때처럼 대체 글꼴로 그린다 (명세가 정했다. 스택에 Noto Sans KR을 넣으면 한글은 고르지만 고정폭이 아니다. 디자인 파일 스크립트의 `MONO`도 같은 스택이다. 그 파일의 디자인 토큰 JSON의 `font.mono`에는 `ui-monospace`가 없다).
- **양.** 테마 하나의 글꼴로 위젯의 대화 문장을 그릴 때 받는 양(옛 측정은 14파일, 약 150KB)은 고정폭이 바뀌어 달라진다. web-widget이 예산을 볼 때 다시 잰다. 그 행에 적었다.
- **재지 않은 것.** Noto Sans Mono의 CSS를 Vite(Storybook)와 Next가 실제 파일로 내는지는 재지 않았다(어림: 낸다). 같은 Fontsource 모양(`./files/` 상대 경로, `local()` 없음)의 Noto Sans KR은 둘 다 냈다(design-system 프로브 `tokens/measure.mjs`). 그래서 새 결정을 낳지 않는다고 보고 넘긴다. 판정 스토리 Fonts가 다섯 벌(Noto Sans KR 셋, Noto Sans Mono 둘)의 적재와 굵기를 본다.

### 아이콘 (명세가 정했다)

- **모양은 Lucide 그대로다.** 디자인 파일은 아이콘을 16 격자에 직접 그렸지만, 아이콘의 출처는 lucide-react의 서브패스다(ADR 0024, design-system 명세). `IconName` 열여섯과 그 이름은 바꾸지 않는다. 디자인 파일의 이름(`pause`, `dash`, `refresh`, `sliders` 등)에 맞는 Lucide 아이콘은 관리 화면이 필요할 때 `IconName`에 더한다(ADR 0026의 첫째 2026-10-12 이력).
- **선은 화면에서 1.5px이다.** 디자인 파일의 `icon-stroke` 1.5px을 크기와 상관없이 지킨다. 지금은 24 격자의 굵기를 크기마다 골라(14·16px은 2, 20·24px은 1.75), 화면의 굵기가 크기마다 다르다(24 격자의 굵기에 크기/24를 곱하면 1.17~1.75px이다. 셈이고 재지 않았다). lucide-react 1.51.0의 `nonScalingStroke`가 그린 요소마다 `vector-effect: non-scaling-stroke`를 달아 `strokeWidth` 1.5가 화면의 px가 된다(설치본 `dist/esm/shared/src/build/buildLucideIconNode.mjs`를 읽었다). `absoluteStrokeWidth`는 `size` prop으로 나누는데 우리는 크기를 클래스로 주어 맞지 않는다(같은 파일).
- **크기는 셋이다.** `"14"`, `"16"`, `"20"`이고 기본은 지금처럼 `"20"`이다. `"24"`는 디자인 파일에 없어 뺀다(사용자가 골랐다. 디자인이 없앤 모양을 고르던 prop은 뺀다).

### 컴포넌트 아홉 (사용자가 골랐다. 모양은 새 디자인이고 props는 지금 계약이다)

모양의 원천은 디자인 파일 2절의 상태 표와 해부도, 그리고 그 표본 그림이다(`design.mjs --refresh`의 `components`가 상태 표와 치수를 낸다). props의 원천은 지금 코드다. **디자인 파일 5.2절의 props 표는 Claude Design이 "구현 연결 (초안)"으로 낸 것이고 따르지 않는다.** 그 표와 지금 코드의 차이(`TextField`와 `TextInput`, `done`과 `ended`, 카드의 `title`·`meta`, 진행 표시의 `kind` 등)는 바꾸지 않는다. 뺄 prop은 디자인이 없앤 모양을 고르던 것 넷뿐이다. 아래는 지금과 달라지는 것의 요약이고, 공통 규칙(기본 요소로 짓기, 변형 맵, `className`·`style` 없음, 상태마다 클래스 고르기, 포커스 링, 불러오는 중이 `disabled`가 아님)은 `web-design.md` 그대로다.

**atoms**

1. **버튼(`Button`).** 높이 `h-control`(밀도), 안쪽 좌우 12px, 아이콘과 글자 사이 8px, 아이콘 16px, 모서리 `m`(8), 글자 `text-body`·500. 주는 `primary`/`on-primary`이고 올림 `primary-hover`, 누름 `primary-active`다. 보조는 바탕 없이 `border` 테두리와 `text` 글자이고 올림 `bg-hover`, 누름 `bg-active`다. 위험은 바탕 없이 `border` 테두리와 `danger` 글자이고 올림 `bg-hover`, **누름 `bg-selected`**다(사용자가 골랐다. 아래 "위험 버튼의 누름"). 쓸 수 없음은 `bg-disabled` 바탕과 테두리, `text-disabled` 글자다. **`size` prop을 뺀다.** 높이는 밀도가 정한다. 기본 변형은 지금처럼 `primary`다.
2. **아이콘 버튼(`IconButton`).** 모서리 `m`, 아이콘 16px. `size`는 `"m"`(기본, `size-control`이라 밀도를 따른다)과 `"s"`(28px)다. `"s"`는 디자인 파일이 코드 칸 머리에 쓰는 작은 크기이고, 알림의 닫기도 지금 계약대로 이것을 쓴다 (명세가 정했다. 값의 뜻만 바뀌고 이름은 지금 것이다). 투명은 바탕 없이 `text-muted` 아이콘이고 올림 `bg-hover`·`text`, 누름 `bg-active`·`text`다. 주는 버튼의 주와 같다. 보조는 디자인 파일이 상태를 적지 않아 버튼의 보조와 같게 둔다 (명세가 정했다). 쓸 수 없음은 투명이면 `text-disabled` 아이콘만, 주·보조면 `bg-disabled`·`text-disabled`다.
3. **아이콘(`Icon`).** 위 "아이콘" 절. 색은 `currentColor`다.
4. **상태 배지(`StatusBadge`).** 높이 22px(`badge`), 안쪽 왼쪽 6px(`badge-start`)·오른쪽 8px, 아이콘과 글자 사이 4px, 아이콘 14px, 모서리 `s`(4), 글자 `text-badge`(12/16, 500). **바탕을 칠하지 않는다.** 테두리는 `border`이고, 글자와 아이콘은 일시정지 `warning`, 끝남 `success`, 실패 `danger`, 결말 없음 `text-muted`다. 상태 키(`done` 등)와 아이콘 이름은 그대로다.
5. **진행 표시(`Progress`).** 값을 알면 막대이고, 트랙은 `bg-active`, 채움은 `text-muted`, 높이 4px(`progress`), 모서리 `full`이다. **값을 모르면(`value`가 `null`) 막대 대신 도는 표시(16px, `text-muted`)를 보인다.** 디자인 파일이 "끝을 모르는데 막대를 채운다"를 피하는 짝으로 들었다. 이름은 `text-muted`이고 막대와 사이가 8px이다. **`tone` prop을 뺀다.** 채움은 `text-muted` 하나다. `role="progressbar"`, 값을 모를 때 `aria-valuenow`가 없는 것, `value`·`max`·`label`은 그대로다. 값 모름 막대의 움직임(`animate-progress`)은 빠진다.
6. **카드(`Card`).** 바탕 `bg-raised`, 테두리 `border` 1px, 모서리 `l`(12), 그림자 없음. **`elevation` prop을 뺀다.** `as`, `padding`, `children`은 그대로다. 디자인 파일의 카드 머리(종류와 시각)는 쓰는 쪽이 `children`으로 짓는다(사용자가 골랐다. props는 지금 계약이다).

**molecules**

7. **글 입력(`TextField`).** 한 줄의 높이 `h-control`(밀도), 안쪽 좌우 12px, 여러 줄의 안쪽 위아래 8px, 모서리 `m`. 라벨과 칸 사이 8px, 칸과 도움말 사이 4px. 기본은 `bg-raised`·`border-control`·`text`이고 자리 글자 `text-muted`, 올림에 테두리 `text-muted`다. 쓸 수 없음은 `bg-disabled`·`text-disabled`와 테두리 `border`다. 오류는 테두리 `danger`와 칸 아래 `danger` 글(`circle-x` 아이콘과 함께), `aria-invalid`다. props는 그대로다.
8. **스위치(`Switch`).** 트랙 40×24px(`switch-w`·`switch-h`), 손잡이 20px(`switch-knob`)과 안쪽 띄움 2px(`switch-inset`), 모서리 `full`, 글자와 사이 8px. 꺼짐은 트랙 `border-control`에 손잡이 `bg-raised`, 켜짐은 트랙 `accent`에 손잡이 `on-accent`이고, 상태 글(켜짐·꺼짐)은 `text-muted`다. 올림은 트랙 위에 `bg-active`를 겹친다. 쓸 수 없음은 트랙 `bg-disabled`, 손잡이 `text-disabled`다. 줄의 최소 높이(`row-touch`)는 뺀다. 누르는 곳은 여전히 라벨 전체다. props는 그대로다.
9. **알림(`Alert`).** **바탕을 칠하지 않는다.** `bg-raised` 바탕에 `border` 테두리, 모서리 `l`, 안쪽 위아래 12px·좌우 16px, 아이콘 20px(`danger`·`warning`·`info`), 아이콘과 글 사이 12px, 제목 `text`, 본문 `text-muted`, 제목과 본문 사이 4px. 역할(실패만 `role="alert"`)과 `actions`·`onClose`는 그대로다. 닫기는 작은 아이콘 버튼(28px)이다. 디자인 파일의 알림에는 닫기가 없지만 지금 계약이라 남긴다.

**위험 버튼의 누름 (사용자가 골랐다).** 디자인 파일의 상태 표는 보조·위험 버튼의 누름을 `bg-active`로 적었다. 그 위의 `danger` 글자는 다크에서 테마 넷 모두 4.5:1에 못 미쳤다(`bg` 위 4.05~4.09, `bg-raised` 위 3.67~3.69, `contrast.mjs`의 "바꾸기 전" 묶음). 위험 버튼의 누름만 `bg-selected`로 두면 여덟 벌 모두 넘고(가장 낮은 값은 녹청 다크의 카드 안 4.51), 올림(`bg-hover`)과 여전히 다르다. 보조 버튼의 누름은 `bg-active` 그대로다(가장 낮은 값 9.33).

### 판정 스토리와 판정 함수 (명세가 정했다)

- **Matrix.** 여덟 벌(테마 넷 × 모드 둘)에서 쓰임새 토큰 23개가 풀리는지 본다. 형식은 `#RRGGBB`이고, 반투명 넷(`bg-hover`, `bg-active`, `bg-selected`, `shadow-color`)은 `#RRGGBBAA`다. 테마를 바꾸면 `accent`가 바뀌어 모드마다 넷이 모두 다르다. 그리고 명암비 짝 43개가 기준을 넘는다.
- **명암비 짝 43개.** 디자인 파일이 재는 짝 35개와 컴포넌트가 쓰는데 디자인 파일이 재지 않은 짝 8개다. ADR 0026 이력이 든 디자인 파일의 "판정 44개"는 테마 넷 × 판정하는 행 열하나의 수라 이 짝의 수와 다르다.
  - 디자인 파일의 35개: `text`와 `text-muted`, 그리고 상태 넷(`danger`, `warning`, `success`, `info`)을 바탕 넷(`bg`, `bg-raised`, `bg`에 겹친 `bg-selected`, `bg-raised`에 겹친 `bg-hover`)과 맞댄 24개(4.5). `accent`를 `bg`, `bg-raised`, `bg-raised`에 겹친 `bg-hover`와 맞댄 3개(4.5). `on-accent`/`accent` 1개(4.5). `focus-ring`과 `border-control`을 `bg`·`bg-raised`와 맞댄 4개(3). `on-primary`를 `primary`·`primary-hover`·`primary-active`와 맞댄 3개(4.5).
  - 컴포넌트의 8개: `text`를 `bg`에 겹친 `bg-hover`·`bg-active`, `bg-raised`에 겹친 `bg-active`와 맞댄 3개(4.5. 보조 버튼과 투명 아이콘 버튼의 올림·누름). `danger`를 `bg`에 겹친 `bg-hover`, `bg-raised`에 겹친 `bg-selected`와 맞댄 2개(4.5. 위험 버튼의 올림과 카드 안의 누름. `bg` 위의 누름은 디자인 파일의 짝에 있다). `text-muted`를 `bg`·`bg-raised`에 겹친 `bg-active`와 맞댄 2개(3. 진행 막대의 채움과 트랙). `bg-raised`/`border-control` 1개(3. 꺼진 스위치의 손잡이와 트랙).
  - 기준이 없는 것: `border`(장식), `text-disabled`·`bg-disabled`(쓸 수 없음). 디자인 파일도 뺐다.
  - 여덟 벌 모두 넘었다(`contrast.mjs`의 "디자인 파일"과 "컴포넌트" 묶음). 가장 낮은 값은 디자인 파일의 짝에서 녹청 라이트의 `border-control`/`bg` 3.14, 컴포넌트의 짝에서 녹청 라이트의 꺼진 스위치 3.35와 녹청 다크의 카드 안 위험 버튼 누름 4.51이다. 브라우저의 계산값으로 다시 재는 것이 Matrix다.
- **반투명 바탕의 명암비.** 짝의 바탕 쪽은 쓰임새 토큰 하나이거나 [반투명 토큰, 그 아래 바탕]이다. 판정 함수가 반투명 색을 그 아래 바탕에 알파로 겹친 색으로 명암비를 잰다. 디자인 파일 스크립트의 `over`와 같은 셈이고 `contrast.mjs`가 그것으로 디자인 파일의 표와 소수 둘째 자리까지 맞았다. 기준 미달의 메시지는 지금처럼 테마, 모드, 짝, 잰 값, 기준을 든다. 음성 사례(`contrastRatio`의 21과 1, 기준 미달 짝의 메시지)에 겹친 바탕의 사례 하나를 더한다.
- **Density.** 새 판정 스토리다. `data-density`가 `compact`와 `regular`인 요소에서 밀도 변수 일곱이 디자인 파일의 값이고, 그 안의 `h-control`·`text-body`·`text-table`·`text-mono`·`h-row`의 계산값이 그 값을 따른다. 속성이 없을 때 화면 폭을 따르는 것은 스토리 테스트가 창의 폭을 바꾸지 못해 사진 비교의 Playwright가 본다(아래).
- **Fonts.** 다섯 벌(Noto Sans KR 400·500·600, Noto Sans Mono 400·500)의 적재와 굵기를 본다.
- **ThemeTokensEmitted, RemFree, Responsive**는 그대로 돈다. ThemeTokensEmitted의 표본 이름(`--text-title`, `--spacing-8`, `--radius-s`)은 그대로 있다.
- **ShadowRoot.** 표본의 테마를 기본 테마로 바꾸고 밀도도 단다. 문서 쪽과 shadow 호스트가 같은 `data-density`를 달아 높이까지 맞댄다.
- **계산값으로 가를 수 없는 짝이 바뀐다.** 계산값을 맞대는 단언은 맞대는 쓰임새 토큰이 이웃 쓰임새 토큰과 다른 값인 벌에서 잰다(`web-design.md`). 여덟 벌 가운데 한 벌이라도 같은 원색을 가리키는 짝은 12개다(`same-values.mjs`).
  - 여덟 벌 모두 같은 것은 `accent`와 `focus-ring` 하나라 값으로 가를 수 없다. 그래서 지금 공문에서 포커스 링을 재던 판정 스토리와 `web-design.md`의 그 문장은 빠진다.
  - 나머지는 값이 다른 벌에서 잰다. 컴포넌트 판정에 걸리는 것은 다음이다. `bg-raised`와 `on-accent`는 라이트 넷에서 같아, 스위치 손잡이의 꺼짐과 켜짐은 다크에서 가른다. `primary`는 녹청·쪽빛에서 `text`와, 군청·자초에서 `accent`와 같아 주 버튼의 바탕은 두 갈래를 하나씩 잰다. `border-control`과 `text-disabled`는 라이트 넷에서, `border`와 `bg-disabled`는 다크 넷에서, `bg-active`와 `shadow-color`는 라이트 넷에서 같다.
  - 기본 테마가 아닌 테마에서 재는 스토리는 지금처럼 `judgment`를 단다.

### 사진 비교 (사용자가 밀도 둘을 골랐다. 모양은 명세가 정했다)

- **찍는 것.** 판정 스토리를 뺀 패키지의 스토리(아래 보여 주기용 스토리 포함)를 기본 테마(녹청)의 라이트·다크 × 밀도 둘(`compact`, `regular`)로 찍는다. 상호작용 컴포넌트의 올림·누름·키보드 포커스도 밀도마다 찍는다. 스토리가 globals로 모드나 밀도를 정했으면 그 값만 찍는다(지금 모드의 규칙과 같다).
- **이름.** `<스토리 id>-<모드>-<밀도>.png`, 실제 입력의 상태는 `<스토리 id>-<모드>-<밀도>-<상태>.png`다.
- **정답은 모두 다시 만든다.** 색, 크기, 모서리, 글꼴이 모두 바뀌어 지금 정답 181장은 하나도 남지 않는다. `pnpm -C web visual:update`로 컨테이너 안에서 만든다(Docker). 지금 수로 셈하면 보여 주기용 스토리를 빼고도 약 두 배다(어림).
- **미디어 특성.** 미디어 특성 테스트의 기대값(`data-theme`을 단 탐침의 `--bg`)을 기본 테마로 바꾼다. 그리고 속성이 없는 문서 뿌리와 shadow 호스트가 창의 폭 1280px에서 촘촘, 375px에서 보통의 `--control-h`를 받는지 본다. 지금의 시스템 모드 사례와 같은 자리다.
- **찍지 않는 것.** 다른 테마 셋. 색만 다르므로 Matrix와 스토리 테스트가 본다(둘째 2026-10-06 이력).

### `/design-sync`에 올릴 것 (plan.md의 design-refresh 행. 보여 주기용 스토리의 자리는 사용자가 골랐다. 나머지 모양은 명세가 정했다)

- **보여 주기용 스토리 (사용자가 골랐다).** 컴포넌트 아홉마다 실제 쓰임(승인 묻기의 버튼 쌍, 실행 목록의 배지 넷, 플러그인 줄의 스위치 등)을 보이는 스토리 몇을 패키지의 Storybook에 더한다. 변형과 상태를 빠짐없이 늘어놓는 판정용 스토리는 그대로 남아 스토리 테스트와 사진을 맡는다. 보여 주기용 스토리도 스토리 테스트(axe, 클래스 판정)와 사진을 지나므로 Claude Design에 올라가는 그림이 판정 밖에 놓이지 않는다. 이것은 ADR 0026 본문의 "스토리 한 벌이 갤러리, 실제 브라우저 테스트, Claude Design의 원천을 함께 맡는다"를 지키는 길이다. 따로 쓰는 `.design-sync/previews/`는 저장소의 판정자를 지나지 않아 고르지 않았다.
- **카드에서 판정용 스토리를 뺀다.** 변환기는 동기화 설정의 컴포넌트별 `overrides.<Name>.skip`에 든 스토리를 카드에서 뺀다(변환기 `package-build.mjs`의 `OVERRIDES`와 `emit.mjs`의 `visibleStoryIds`를 읽었다. 2.1.286 판의 변환기, 다른 워크트리의 무시된 사본). 판정용 스토리를 더하면 그 목록에도 더하고, 그 규칙을 `.design-sync/NOTES.md`에 적는다. 빼는 목록을 채점(Storybook과 카드의 비교)도 따르는지는 처음 동기화가 본다.
- **기초 카드.** 색(원색과 쓰임새, 테마 넷), 글자 단계, 간격과 모서리, 밀도 두 벌을 보이는 HTML 카드다. 첫 줄이 `<!-- @dsCard group="…" -->`인 HTML을 Claude Design의 디자인 시스템 창이 카드로 모은다(`DesignSync` 도구 설명을 읽었다. 그룹의 예로 "Colors", "Type", "Spacing"을 든다). 그 창은 폴더마다 첫 `@dsCard` HTML 하나만 모으므로(변환기 `emit.mjs`의 주석 "cardByDir stores the first @dsCard .html per directory"를 읽었다) 카드마다 폴더를 따로 둔다. **값은 글자로 적지 않고 올린 `styles.css`의 CSS 변수(`var(--gray-50)` 등)로만 읽는다.** ADR 0026의 "디자인 토큰의 값은 코드에만 둔다"를 지키기 위해서다. 자리는 `.design-sync/` 아래이고 목록 타일처럼 빌드 뒤 `ds-bundle/`에 복사해 올린다. 컴포넌트 폴더 밖의 카드가 실제로 모이는지는 재지 않았다. 처음 올릴 때 본다.
- **목록 타일.** `.design-sync/thumbnail.html`을 새 기본 테마의 색으로 다시 그린다.
- **사용 규약과 그 검사기, 변환기 포크, 스토리 상수 모듈.** 사용 규약 `.design-sync/conventions.md`(테마 키, 밀도와 그 변수, 클래스와 변수의 목록, 예시)와 그 검사기를 고친다. 변환기 포크의 기본 테마(`muk`)를 녹청으로 바꾸고 밀도 globals를 감싸는 요소로 옮긴다. 포크를 고치면 다음 동기화가 모든 컴포넌트를 다시 채점한다(`.design-sync/NOTES.md`의 Re-sync risks). 스토리 상수 모듈에서 뺀 상수(`CARD_ELEVATIONS`)를 걷는다.
- **올리는 것은 사람이 시작하는 `/design-sync`다.** 카드의 render check와 채점은 그 실행이 한다. 그래서 이 일을 맡은 티켓은 사람이 그 세션에서 `/design-sync`를 시작하는 것으로 닫는다.

### 문서와 설정 (티켓이 고친다. 이 PR이 고친 것은 따로 적었다)

- **이 PR이 고친 것.** `CONTEXT.md`(밀도를 세우고 테마의 뜻을 "색의 한 벌"로), `.scratch/plan.md`의 design-refresh·admin-style·web-widget 행(명세의 자리와 넘기는 것)과 프론티어 문장, `.scratch/design-system/design/README.md`(새 파일을 읽는 길), `.scratch/design-system/probes/README.md`(`design.mjs`의 `--refresh`), `kickoff/prompting.md`(보여 주기용 미리보기의 자리).
- **컴포넌트마다의 쓰는 법 `<Name>.md`(아홉).** `/design-sync`가 그 파일을 컴포넌트의 설명으로 올려 Claude Design의 디자인 에이전트가 읽는다(ADR 0026 디자인 문서 절). 아홉 모두 출처를 디자인 파일 v3에서 재탐색 파일로 바꾸고, 새 모양과 어긋나는 문장을 고친다. 지금 어긋나는 것은 진행 표시의 위험 톤, 카드의 그림자 단계, 아이콘의 선 굵기와 24px다.
- **`.claude/rules/web-design.md`.** 판정하는 것(여덟 벌, 밀도, 글꼴 다섯), 사진(녹청, 밀도 둘), 컴포넌트 공통의 props 문장("props 표(디자인 파일 05절)가 계약의 최소다"를 "props는 지금 코드가 계약이고 재탐색 디자인 파일의 props 표는 초안이다"로), 포커스 링과 쓸 수 없음의 클래스 이름, 계산값을 가를 수 없는 짝, 아이콘의 선(1.5px), 그림자(떠 있는 것에만), 보여 주기용 스토리를 두는 법과 동기화에서 판정용 스토리를 빼는 목록.
- **`docs/constitution/tech.md`** 웹 행의 테마("색과 글꼴의 한 벌로 다섯"을 "색의 한 벌로 넷"), 글꼴 줄과 패키지, `allowBuilds`의 문장. 헌법 버전은 `docs/constitution/README.md`에서 patch로 올린다.
- **코드 주석.** 디자인 토큰 CSS와 글꼴 CSS, 테마 목록, Storybook 미리보기 설정의 본체, 사진 비교의 머리 주석이 든 먹·다섯·글꼴 셋·`muk`.
- **`.scratch/admin-style/design/screens-prompt.md`.** 기본 테마 "먹", 테마 다섯의 이름, 배치와 밀도의 수치를 새 결정으로(재탐색 프롬프트의 "고른 뒤" 4).
- **잔존 grep.** 마지막 티켓이 아래 말을 살아 있는 문서와 코드에서 찾아 0인지 본다. 기록(일지, 지난 명세와 티켓, ADR의 지난 이력, 디자인 파일 v3와 첫 탐색 프롬프트)은 제외한다(`docs/constitution/operations.md`의 문서 위치).
  - 옛 글꼴: `JetBrains Mono`, `IBM Plex`, `plex-mono`, `jetbrains-mono`.
  - 옛 테마: `muk`, `cheongnok`, `gongmun`, `hwangto`, `jadu`, `테마 다섯`, `다섯 테마`, `색과 글꼴의 한 벌`.
  - 옛 쓰임새 토큰: `--tint`, `tint-hover`, `danger-tint`, `divider`, `outline-focus`(`outline-focus-ring`이 아닌 것), `disabled-surface`, `disabled-text`, `accent-hover`, `accent-press`, `border-hover`.
  - 옛 크기와 굵기: `control-m`, `row-touch`, `field-multi`, `icon-l`, `shadow-1`, `font-strong`, `font-mid`, `weight-mid`, `text-heading`, `text-caption`, `text-code`.
  - 뺀 prop과 옛 설명: `elevation`, `ProgressTone`, `animate-progress`, `1.75`, `디자인 파일 v3`(컴포넌트의 `<Name>.md`와 코드 주석에서).

## Testing Decisions

**좋은 테스트는 바깥 행동만 본다.** 역할과 접근 이름, `aria-*`와 기본 속성, 쓰임새 토큰과 밀도 변수가 풀린 계산값(색, 높이, 글자 크기, outline, 테두리), axe 위반, 시트에 규칙이 있는지, 사진이다. 클래스 글자를 단언하지 않는다. 쓰임새 토큰의 값은 디자인 파일과 맞대지 않고 형식, 테마 사이의 차이, 명암비로 본다(design-system 명세와 같다).

### 주 이음매 — 스토리 테스트

- **판정 스토리.** 위 "판정 스토리와 판정 함수" 절의 Matrix(여덟 벌, 23개, 짝 43개), Density, Fonts(다섯 벌), ThemeTokensEmitted, RemFree, Responsive, ShadowRoot와 음성 사례.
- **컴포넌트 스토리.** 지금 단언의 모양을 지키고 값만 새 모양으로 바꾼다. 높이는 `size` 대신 밀도 globals를 정한 스토리에서 32·40px을 본다. 상태 배지와 알림은 바탕이 칠해지지 않고(배지는 `background-color`가 투명, 알림은 `bg-raised`) 테두리가 `border`인지 본다. 위험 버튼은 사진 비교의 누름 사진과 `bg-selected`의 명암비 짝이 함께 받친다. 진행 표시는 값을 모를 때 `aria-valuenow`가 없고 도는 표시가 있는지 본다. 아이콘은 그린 요소의 `vector-effect`가 `non-scaling-stroke`이고 `stroke-width`가 1.5인지 본다. 다크 스토리는 컴포넌트마다 하나 이상이다. 색의 단언은 위 "계산값으로 가를 수 없는 짝"의 벌을 고른다.
- **보여 주기용 스토리.** 단언을 두지 않아도 afterEach의 클래스 판정과 axe를 지난다. 사진도 찍힌다.
- **빠지는 스토리와 단언.** 버튼의 크기 둘, 카드의 그림자 단계, 진행 표시의 위험 톤과 값 모름 막대의 움직임, 아이콘의 24px, 공문의 포커스 링, 스위치 줄의 높이 48px 이상, 여러 줄 입력의 높이 88px 이상. 그 단언이 받치던 모양이 사라졌기 때문이다.
- **선례.** 지금 패키지의 판정 스토리 `web/packages/ui/src/styles/DesignTokens.stories.tsx`와 판정 함수 `web/packages/ui/src/testing/`, 컴포넌트 스토리 `web/packages/ui/src/components/**/*.stories.tsx`, 계산값 단언 `web/packages/ui/src/storybook/expect.ts`.

### 사진 비교

- 녹청의 라이트·다크 × 밀도 둘, 상호작용 컴포넌트의 올림·누름·포커스. 같은 이미지의 컨테이너에서 `maxDiffPixels: 0`. 속성이 없을 때의 밀도는 미디어 특성 테스트가 창의 폭 둘로 본다.
- **선례.** `web/packages/ui/visual/stories.visual.ts`, `media.visual.ts`.

### 바깥 이음매

- 늘리지 않는다. 이 기능은 파이썬과 LLM 호출, 관리 화면의 앱 코드에 닿지 않는다. e2e는 관리 화면이 아직 패키지를 들이지 않아 그대로다.

## Out of Scope

- **관리 화면만 쓰는 컴포넌트.** 디자인 파일의 표, 링크, 옆 탐색 항목, 코드 칸, 테마 카드는 앱에 둔다(design-system 명세의 Out of Scope, admin-style 행). 이 기능은 그것들이 쓸 디자인 토큰(밀도, 행 높이, 표·고정폭 글자, 틀의 크기, 반투명 바탕 셋)만 낸다. admin-style 행에 적었다.
- **관리 화면에 패키지를 들이는 일과 화면.** 설정 화면의 테마 카드 넷, `html`의 `data-theme`, 화면 그리기는 admin-style이다. 관리 화면은 `data-density`를 달지 않는다. 그 행에 적었다.
- **위젯이 밀도를 다는 일.** 호스트와 iframe 문서에 `data-density="regular"`를 다는 코드와 그것을 빠뜨리지 않게 하는 테스트, 새 고정폭 글꼴로 다시 재는 글꼴 양은 web-widget이다. 그 행에 적었다.
- **패턴과 화면.** 승인 묻기, 실행 실패 알림, 빈 목록, 불러오는 중인 목록, 표의 거르기는 organisms 이상이라 앱이 짓는다(design-system 명세와 같다). 받는 쪽은 admin-style과 web-widget이고, 근거는 첫 탐색 v3의 03·04절에서 재탐색 디자인 파일의 3절(패턴 다섯)과 4절(화면)로 바뀐다. 두 행에 적었다. 두 행의 Blocked by는 design-refresh를 든다.
- **디자인 파일의 props 표와 아이콘 그림.** props는 지금 계약을 지키고(사용자가 골랐다), 아이콘은 Lucide다(위 "아이콘" 절).
- **디자인 파일의 OKLCH 생성기를 코드로 옮기는 것.** 위 "값의 원천과 옮기기" 절.
- **Firefox·WebKit의 스토리 테스트.** design-system 명세가 남긴 것 그대로다.

## Further Notes

- **측정.** `design.mjs --refresh`(디자인 파일의 값), `contrast.mjs`(여덟 벌의 짝 43개와 바꾸기 전의 위험 버튼 누름), `same-values.mjs`(같은 값의 짝), `font.mjs`(Noto Sans Mono 패키지). 결과는 `.scratch/design-refresh/probes/README.md`다.
- **이어지는 묶음 (어림).** 쓰임새 토큰의 이름이 바뀌면 옛 클래스(`bg-tint` 등)가 규칙을 잃어 afterEach가 모든 컴포넌트 스토리를 빨갛게 한다. 그래서 디자인 토큰 CSS를 바꾸는 티켓은 컴포넌트의 클래스도 함께 옮기고 사진 정답도 다시 만든다. 나눠도 되는 것은 컴포넌트의 새 모양(atoms, molecules), 보여 주기용 스토리, `/design-sync`에 올릴 것이다. 쪼개는 일은 to-tickets다.
- **재지 못한 것.** Noto Sans Mono를 Vite와 Next가 실제 파일로 내는지(위 글꼴 절), 동기화 설정의 빼는 목록을 채점이 따르는지, 컴포넌트 폴더 밖의 `@dsCard` 카드가 모이는지(둘 다 사람이 시작하는 `/design-sync`가 처음 본다), 속성이 없는 shadow 호스트가 사이트 창의 폭을 따르는 것이 위젯 자리에서 문제인지(web-widget이 `regular`를 달아 피한다).
- **열린 문제.** 없다. 위의 재지 못한 것은 받는 쪽이 정해져 있다.
