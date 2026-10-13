# 2026-10-13 (29) design-refresh 04: 밀도 두 벌과 공통 크기로 촘촘과 보통이 갈리고 컴포넌트 아홉이 새 치수로 선다

## 계기

일지 2026-10-13-22의 "다음"이 design-refresh 티켓 04였다. 지시문의 "어디서"대로 주 체크아웃 세션에서 `tidy-checkouts`를 먼저
돌아 루트를 `cd4f92d`에서 `628a0f6`으로 당겼고(지운 워크트리는 없다. 잠금 pid가 살아 있거나 모듈을 올린 프로세스가 있는 것이
대부분이었고, prunable 둘·분리 HEAD 둘·탐침이 남긴 옆 이름 하나·머리가 다른 하나는 사람에게 넘겼다), 주 체크아웃에서 브랜치를
따지 않은 채 `EnterWorktree(name=04-density-and-common-sizes)`로 `origin/main`에서 워크트리를 만들고 브랜치를
`feature/04-density-and-common-sizes`로 바꿨다.

> 사용자: "다음 작업: .scratch/design-refresh/issues/04-density-and-common-sizes.md. 밀도 두 벌과 공통 크기로 촘촘과 보통이 갈리고 컴포넌트 아홉이 새 치수로 선다"

## 어떻게 했나

- **밀도.** 디자인 토큰 CSS(`theme.css`)의 `@layer theme`에 밀도 변수 일곱(`--body-size`, `--body-lh`, `--table-size`,
  `--table-lh`, `--mono-size`, `--row-h`, `--control-h`)을 명세의 선택자대로 두었다. 보통은 `:root, :host`와
  `[data-density="regular"]`·`:host([data-density="regular"])`, 촘촘은 `[data-density="compact"]`·`:host([data-density="compact"])`와
  `@media (width >= 768px)` 아래의 `:root:not([data-density])`·`:host(:not([data-density]))`다. `@theme inline`이 `text-body`,
  `text-table`, `text-mono`(줄 높이는 `--table-lh`), `control`, `row`를 밀도 변수에 잇는다. 감싼 요소(`[data-ui-root]`)는 별칭
  대신 `--body-size`·`--body-lh`를 직접 읽는다.
- **공통 크기.** `@theme static`의 이름 체계는 지키고 값과 수만 디자인 파일에 맞췄다. 글자는 `title`, `small`(12/16), `badge`
  (12/16·500)이고 `heading`·`caption`·`code`·`body`(밀도로 옮김)를 뺐다. 간격 `0`~`8`, 작은 조작 `control-s`(28), 아이콘 셋, 틀
  `nav`·`nav-item`·`top-bar`, 부품 치수(`switch-w`·`switch-h`·`switch-knob`·`switch-inset`·`progress`·`badge`·`badge-start`),
  모서리 `s` 4·`m` 8·`l` 12·`full`, `spin` 0.8초다. `control-m`·`row-touch`·`field-multi`를 걷었다. 그림자 `float`는 색이 모드마다
  다른 `--shadow-color`를 읽어 `@theme inline`에 두었다.
- **컴포넌트 아홉.** 티켓의 치수대로 옮겼다. 버튼은 `h-control`·`px-3`·`font-medium`과 16px 아이콘(불러오는 중의 도는 표시도
  16px), 아이콘 버튼은 `size-control`과 `size-control-s`(28)에 아이콘 16px, 상태 배지는 `h-badge`·`pl-badge-start`·`pr-2`·
  `rounded-s`·`text-badge`, 스위치는 손잡이 `size-switch-knob`을 `switch-inset`만큼 띄우고 줄의 최소 높이를 걷었다. 글 입력은
  `h-control`이고 여러 줄의 최소 높이를 걷어 줄 수가 높이를 정한다. 라벨과 칸을 한 묶음(`gap-2`)으로 두어 칸과 도움말 사이(`gap-1`)와
  가른다. 알림의 제목과 본문은 `text-body`이고 그 사이가 4px이다. 진행 표시·카드는 디자인 토큰의 값이 바뀌어 클래스가 그대로다.
  머리 주석의 "첫 탐색 디자인 파일의 값(티켓 04가 옮긴다)"을 걷었다.
- **Storybook.** globals에 `density`(`auto` 기본)를 더하고, 데코레이터가 문서 뿌리에, shadow 틀이 호스트에 `data-density`를 단다
  (티켓의 "이 티켓이 정한 것" 1).
- **판정 스토리.** Density를 새로 두고(같은 곳 2), ShadowRoot에 밀도를 달았다. 떠 있는 것의 그림자를 보는 FloatShadow를 더했다
  (아래 "정한 것" 3). Fonts의 고정폭은 `text-mono`로 그린다.
- **컴포넌트 스토리.** 높이를 재던 스토리에서 높이를 걷고, 버튼·아이콘 버튼·글 입력에 globals로 밀도를 정한 `Compact`·`Regular`
  스토리를 더해 높이와 그 밖의 치수를 본다. 상태 배지·진행 표시·카드·스위치·알림의 치수 단언을 새 값으로 고쳤다. 여러 줄 입력은
  "88px 이상" 대신 높이가 줄 셋과 안쪽 위아래, 테두리의 합인지 본다.
- **사진 비교.** 차례를 모드 둘 × 밀도 둘로 돌리고 두 루프가 그려진 모드와 밀도로 거른다(같은 곳 3). 미디어 특성 테스트에 창의
  폭 사례를 더했다.
- **문서.** `.claude/rules/web-design.md`의 판정하는 것(Density), 사진의 밀도 둘, 크기의 이름, 밀도와 그 유틸리티, 높이를 재는
  스토리의 globals, 그림자를 고쳤다. 컴포넌트 문서 둘(진행 표시의 "14px", 스위치의 "높이가 48px 이상")을 고쳤다. 05 티켓의 사용
  규약 줄에 04가 걷고 더한 이름을 메모로 넘겼다.

## 정한 것

티켓 파일의 "이 티켓이 정한 것"에 셋을 적었다(데코레이터와 틀의 자리, Density의 표본 구조, 사진 비교가 밀도를 돌리는 법과 미디어
특성의 사례 이름). 그 밖에 이 세션이 정한 것은 셋이다.

1. **알림의 제목과 본문은 `text-body`다.** 티켓의 알림 줄에는 글자 크기가 없지만, 디자인 파일의 알림 표본은 제목(600)과 본문을
   본문 크기로 물려받아 그린다. `small`이 13/20에서 12/16으로 줄어 그대로 두면 알림의 글이 디자인보다 작아진다. 그래서 둘 다
   밀도를 따른다. 닫기(28px)가 제목 줄보다 높아 위아래로 내미는 `-my-1`은 그대로 두었다(셈으로는 보통의 제목 줄 22px에서 닫기의 가운데가
   제목 줄의 가운데보다 1px 위다. 재지 않았다).
2. **글 입력의 라벨은 500이다.** 디자인 파일의 라벨은 12/16·500이다. 03 전에는 `small`이 테마의 중간 굵기였는데 03이 400으로 바꿔
   라벨이 400이 됐다. 03 메모의 `font-regular`를 함께 보면서, 도움말·스위치의 상태 글·알림의 본문에서는 덮을 것이 없어 걷고, 라벨
   안의 "선택"에서는 라벨의 500을 덮으므로 남겼다.
3. **떠 있는 것의 그림자는 판정 스토리 FloatShadow가 본다.** 티켓의 판정 스토리 목록에는 없지만 새로 서는 디자인 토큰이고, 색을
   놓인 요소에서 읽어야 한다는 성질은 이것만 지킨다. 모드마다 하나씩 그려 뿌리와 다른 모드에서도 그 자리의 `--shadow-color`인지
   본다. 처음에는 inline에 두는 것이 그 성질의 까닭이라고 어림했는데, 변이와 프로브가 그렇지 않음을 보였다(아래 "검사"). 그래도
   inline에 둔 것은 static이면 뿌리에 `--shadow-float` 선언이 나와, 그 변수를 `var()`로 읽는 자리가 밀도의 별칭처럼 뿌리의 모드로
   풀린 색을 받을 것이라서다(어림).

## 검사

- **빨강부터.** 스토리를 새 값으로 고친 뒤 구현 전에 돌려 91개 가운데 26개가 빨간 것을 봤다. Density·ShadowRoot·FloatShadow와
  컴포넌트의 치수 단언, Fonts(afterEach가 `text-mono`에 규칙이 없다고 잡았다)다. 구현 뒤 91개가 모두 지났다.
- **창의 폭.** 스토리 테스트의 창은 1200×900이고 속성이 없는 문서 뿌리의 `--control-h`는 32px(촘촘)이었다. Density에 잠깐 실패하는
  단언을 두어 그 메시지에서 읽고 되돌렸다.
- **값의 대조.** `design.mjs --refresh --out`의 JSON과 디자인 토큰 CSS를 스크래치 스크립트로 맞대어 59(밀도 21, 기본 밀도, 간격·
  모서리·아이콘·틀·기준 폭·글자·굵기·그림자·별칭, 해부도에서 온 부품 치수와 작은 아이콘 버튼, 회전 빠르기)이 어긋남 0이었다. 사본에
  모서리와 손잡이를 틀리게 심자 둘을 냈다. `small`의 굵기 400은 JSON에 없는 코드의 값(03이 정했다)이다.
- **rules.** 고친 `web-design.md`의 네 문장이 새 `claude -p` 세션에서 `paths` 안의 파일(`StatusBadge.tsx`)을 Read할 때 실리는지
  `tools/canary.py`로 봤다. 통과 4이고 "없음" 섞인 통과는 0이다(대조군 `README.md`는 "없음", claude 2.1.296). 명세는
  `.scratch/design-refresh/probes/canary/web_design_density.toml`이다.
- **변이(`.scratch/design-refresh/probes/density_sizes_mutations.toml`) 스물넷.** 모두 기대대로였다. 밀도 선택자 셋(보통, 촘촘,
  호스트의 촘촘 짝), 감싼 요소가 별칭을 `var()`로 읽는 것(Density의 보통 표본과 ShadowRoot의 문서 쪽이 각각 빨갛다), 테마 블록이
  밀도 변수를 다시 정하는 것(여덟 벌), 고정폭의 줄 높이, 밀도의 미디어 조건(Responsive), shadow 틀과 데코레이터가 밀도를 빠뜨리는
  것, 그림자 색을 모드와 무관한 원색으로 두는 것, 컴포넌트 치수 여덟이 빨갛다. 사진 변이 넷(Docker)도 빨갛다. 사진 루프의 밀도
  가드를 빼면 촘촘을 정한 버튼 스토리가 보통 이름으로 찍혀 정답이 없고, 속성 없는 뿌리·호스트의 미디어 규칙을 하나씩 빼거나 그
  블록의 행 높이만 틀리게 하면 창 폭 사례가 빨갛다. 첫 판에서 하나가 어긋났다. 그림자를 `@theme static`으로 옮기면 FloatShadow가
  빨갈 것이라 기대했는데 초록이었다. 컴파일해 보니(`.scratch/design-refresh/probes/shadow.mjs`) 두 블록의 `.shadow-float` 규칙이
  같았다. Tailwind가 그림자 값을 유틸리티에 풀어 쓰기 때문이고, 다른 것은 뿌리에 선언이 나오는지뿐이다. 그 변이를 초록의 대조군으로
  바꾸고, 그림자 색을 모드와 무관하게 두는 시험을 더해 둘을 다시 돌렸다. 상호작용 루프의 밀도 가드는 `INTERACTIONS`에 밀도를 정한
  스토리가 없어 빨강을 볼 수 없었다. 일반 루프와 같은 질의(`renderedAs`)를 쓴다. 누름 탐침의 hex 자릿수(3·4·6·8)도 지금 값으로는
  가를 변이가 없다.
- **옛 변이 표.** 이번에 고친 코드를 겨누던 표를 `--check`로 봤다. 03의 `theme_colors_mutations.toml`은 41개 가운데 17개가 원문을
  잃었고(상태 배지의 클래스, 걷은 `renderedMode`, 지운 정답 사진의 이름), 02의 `icon_props_mutations.toml`은 8개 가운데 2개가 03 때
  이미 잃었다. 변이 도구의 독스트링대로 고치지 않았다(아래 "셀프 리뷰").
- **잔존 grep.** 옛 크기의 말(`control-m`, `row-touch`, `field-multi`, `text-heading`, `text-caption`, `text-code`, 그리고 02·03이 걷은
  `icon-l`, `shadow-1`~`3`)이 살아 있는 문서와 코드에서 `.design-sync/conventions.md`(05의 몫) 말고는 0이다. 나머지는 기록(일지,
  design-system의 명세·티켓·프로브, 첫 탐색 디자인 파일)과 이 기능의 명세·티켓이 바꿀 대상으로 드는 문장이다.

## 셀프 리뷰

`/code-review`를 기준점 `628a0f6`으로 돌렸다(사진을 뺀 추적 파일 34개, 미추적 글 파일 셋과 새 사진 378장, 커밋 0).

- **표준 축(Major 1, Minor 4, Nit 5).** 고친 것: 프로브 README가 변이 결과를 이 일지에 있다고 적었는데 없었다(Major). 변이 표를
  돌려 위 "검사"에 적었다. "별칭을 `var()`로 읽으면 뿌리의 밀도로 풀린 값이 물려진다"의 근거로 `tailwind.mjs`만 들었는데 그
  프로브는 선언이 나오는지만 본다. 상속의 결과는 변이 표의 감싼 요소 변이가 Density·ShadowRoot에서 잡은 것을 근거로 다시 적었다.
  같은 지적이 든 FloatShadow 주석("`@theme static`에 두면 … 뿌리의 모드로 풀린다")은 변이를 돌려 보니 틀렸다(위 "검사"의 변이).
  그 주석과 디자인 토큰 CSS의 그림자 주석을 프로브 `shadow.mjs`의 결과로 고쳤다.
  "이 블록의 이름은 CSS 변수로 나오지 않는다"를 "`var()`로 읽지 않는 한"으로 좁혔다(같은 diff 안에 반례). `web-design.md`의
  "높이나 글자 크기를 재는 스토리는 globals로 밀도를 정한다"를 같은 diff의 스토리(배지, 스위치, 진행 표시, 알림, 여러 줄 입력)가
  어겼다. "밀도를 따르는 높이나 글자 크기를 px로 재는 스토리"로 좁히고, 놓인 자리의 밀도 변수와 맞대는 단언은 그러지 않아도 된다고
  적었다. 미디어 특성 사례가 촘촘의 값 일곱을 다시 적은 미디어 블록에서 `--control-h`만 맞대 나머지 여섯이 어긋나도 초록이었다.
  일곱을 모두 맞대게 고치고 그 블록의 행 높이만 틀리게 하는 변이를 더했다. 크기 이름 목록에 `icon-*`를 더했다. 카나리아 머리
  주석의 셋째 문장을 expect와 맞췄다. 탐침의 속성을 `ThemeKey`·`Mode`·`Density`로 좁혔다. 미리보기 도우미를
  `setOrRemoveAttribute`로 바꿨다. 알림 닫기의 주석을 두 밀도 모두로 고쳤다.
- **명세 축(Minor 4, Nit 4. 넷은 표준 축과 같다).** 고친 것: 사진 비교의 누름 탐침이 정적 빌드의 토큰 값을 6·8자리 hex로만
  받았다. 티켓 58은 정적 빌드의 CSS가 `optimize`로 짧은 hex(`#0006`)를 가질 수 있으니 가정하지 말라고 했다. 3·4·6·8자리를 받게
  고쳤다(지금 네 값은 줄어들지 않아 빨강을 낼 변이는 두지 않았다). 진입점 `.`의 `DENSITIES`·`Density`는 요청 밖의 공개 이름이라
  걷었다(쓰는 쪽이 생기면 그 기능이 더한다). 05 메모가 02·03이 걷은 이름(`shadow-1`~`3`, `font-strong`)과 전부터 있던
  `size-control-s`를 04의 것으로 적어 고쳤다. 남긴 것: 03의 변이 표 `theme_colors_mutations.toml`이 지운 정답 사진의 이름과
  걷은 `renderedMode`를 겨눠 41개 가운데 17개가 원문을 잃었다(`--check`). 02의 표 `icon_props_mutations.toml`은 8개 가운데 2개가
  03이 클래스 이름을 바꿀 때 이미 원문을 잃었다. 변이 도구의 독스트링이 "옛 프로브의 원문은 코드가 바뀌면 썩어도 되고, 다시 돌리거나
  고쳐 커밋할 때 이 확인이 알린다"고 정해 고치지 않았다. 넷 가운데 셋(알림의 `text-body`, 라벨 500, FloatShadow)은 명세 축이
  디자인 파일과 티켓에 비추어 정당하다고 봤다.
