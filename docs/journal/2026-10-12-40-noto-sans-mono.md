# 2026-10-12 (40) design-refresh 티켓 01: 모든 테마가 Noto Sans KR과 Noto Sans Mono를 쓴다

## 계기

일지 2026-10-12-36의 "다음"이 design-refresh 티켓 01과 02를 나란히 구현하는 것이었다. 지시문의 "어디서"대로 이 세션이 먼저
주 체크아웃에서 `tidy-checkouts`를 돌고 워크트리 `01-noto-sans-mono`에 들어가 브랜치 `feature/01-noto-sans-mono`를 땄다. 나란히
도는 티켓 02는 `feature/02-icon-stroke-and-removed-props` 세션이 한다.

`tidy-checkouts`는 루트를 `bb14aae`에서 `6b439aa`로 당겼다. 판정에서 지울 후보는 없었다. 넘긴 것은 제목이 어느 브랜치와도 맞지
않는 실행 중 세션 둘("모델과 추론 레벨 자동 선택", "회고 후보를 에이전트가 판단해 승인하게 바꾸기") 때문에 넘긴 워크트리 열여덟,
분리 HEAD 둘, prunable 둘, 머리가 다른 것 하나(`skill-check-and-retro-section`), 등록 없는 폴더 일곱이다. 새 세션의 첫 턴이라 답을
기다리지 않았다.

## 한 것

- **패키지.** `packages/ui`의 `dependencies`에서 `@fontsource/jetbrains-mono`와 `@ibm/plex-mono`를 빼고 `@fontsource/noto-sans-mono`
  5.3.0을 더했다. `pnpm -C web install`이 멈추지 않고 지났고 `pnpm-workspace.yaml`에 `minimumReleaseAgeExclude`가 생기지 않았다.
  락에서 `@ibm/telemetry-js`도 함께 빠졌다(`Packages: +1 -3`). 설치한 판이 잰 판(`font.mjs`의 5.3.0)과 같아 다시 재지 않았다.
- **설치 조건.** `allowBuilds`에서 `@ibm/plex-mono` 줄을 빼고 머리 주석을 esbuild·@parcel/watcher만 남긴 문장으로 고쳤다.
- **글꼴 CSS.** Noto Sans Mono의 `400.css`·`500.css`를 `@import`하고, JetBrains Mono의 `@import` 둘과 IBM split 파일의
  `@font-face` 열 개를 지웠다.
- **글꼴 변수.** 다섯 테마 블록의 `--sans`·`--mono`를 지우고 `@layer theme` 맨 앞의 `:root, :host` 블록에 한 번 두었다. 고정폭
  스택은 `"Noto Sans Mono", ui-monospace, monospace`다. `--weight-mid`는 티켓대로 두었다(03이 뺀다).
- **Fonts.** 판정 스토리가 다섯 벌(Noto Sans KR 400·500·600, Noto Sans Mono 400·500)의 적재를 본다. 테마마다 되풀이하던 그림을
  한 벌로 줄이고, 다섯 벌이 모두 한 번씩 그려지게 두었다. 먼저 기대만 바꿔 돌려 Noto Sans Mono 두 벌이 "없음"으로 빨간 것을 본
  뒤 구현했다. 셀프 리뷰 뒤에 본문과 고정폭 문단의 계산된 `font-family` 첫 이름을 보는 단언을 더했다(아래).
- **변이.** `.scratch/design-system/probes/ui_mutations.toml`의 Fonts 변이가 지운 줄(`jetbrains-mono/500.css`)을 겨누고 있었다.
  Noto Sans Mono 500으로 다시 겨누고, 뿌리의 `--mono`를 지우는 변이를 더했다. 둘 다 돌려 기대대로 빨강을 봤다(기준선은 초록).
  변이 파일 셋(`ui`, `atoms`, `visual`)의 `--check`는 모두 원문이 있었다.
- **헌법.** `tech.md` 웹 행의 글꼴 줄과 글꼴 패키지를 고치고, `allowBuilds`에서 끄던 설치 스크립트의 괄호를 두 패키지에 설치
  스크립트가 없다는 것으로 고치고, 테마 문장에서 "글꼴"을 뺐다. 그때 열려 있던 PR #199(`chore/review-rate-limits`)가 3.0.28을
  먼저 매겨 3.0.29로 올렸다. 커밋 뒤 그 PR이 먼저 병합되어(`c1903e0`) origin/main을 합치며 헌법 README의 판 줄과 대기열에서 난
  충돌을 풀었고, 비워 둔다고 적었던 3.0.28의 문장은 뺐다.
- **주석.** 글꼴 CSS의 머리 주석, 테마 목록의 머리 주석("색과 글꼴의 한 벌", "고정폭 글꼴"), 디자인 토큰 CSS의 `@theme inline`
  설명을 고쳤다. 글꼴 변수가 inline인 까닭은 이제 테마가 아니라 페이지 안 위젯이 감싼 요소에서 다시 정할 수 있게 하는 것이다.

## 확인한 것

- 사진 비교(`pnpm -C web visual`)가 82개 모두 초록이었고 정답을 하나도 바꾸지 않았다.
- 명세가 "재지 않았다"고 둔 Vite 빌드: 사진 비교가 지은 Storybook 정적 빌드의 `assets/`에 Noto Sans Mono 파일 26개가 나왔다.
  굵기 둘의 서브셋 일곱 × woff2·woff 28개 가운데 빠진 둘은 베트남어 woff2(3,748바이트와 3,780바이트)이고, 빌드 CSS에
  `data:font/woff2`가 둘 있었다. Vite의 기본 인라인 한도(4096바이트)보다 작은 파일이 data URL로 들어간 것으로 본다(한도 값은
  설정을 읽지 않은 어림이다). 손으로 봤고 프로브는 없다. Next 쪽은 명세의 주석대로 admin-style이 본다.
- 잔존 grep: 옛 글꼴의 말이 남은 곳은 셋이다. 바꾸는 일 자체를 적은 design-refresh 명세와 이 티켓, 기록(일지, design-system
  명세·티켓·프로브, ADR 0026의 지난 이력, 헌법 README의 판 기록, 디자인 파일 v3, 재탐색 프롬프트의 첫 보내기 경위와 "고른 뒤"
  목록), 그리고 05가 고치는 `.design-sync/NOTES.md`다.
- 검증 명령: `uv run pytest -q`(2197 통과), ruff 둘, pyright, lint-imports, `pnpm -C web verify`(357 통과)가 셀프 리뷰 전에
  모두 초록이었다. 리뷰 뒤의 재실행은 커밋의 pre-commit으로 갈음하고 결과는 아래 셀프 리뷰 절에 적는다.

## 셀프 리뷰

`/code-review`(기준 `6b439aa`, 표준 축 sonnet). 표준 축은 Critical·Major 0, Minor 2, Nit 5였고, 명세 축은 누락 0, 범위 넘침
하나, 틀린 곳 둘이었다.

- 두 축이 함께 짚은 것: 뿌리의 `--sans`·`--mono` 값을 보는 판정이 없었다. Fonts는 `document.fonts.load`에 글꼴 이름을 글자로
  넘기므로 `--mono`가 비거나 옛 이름이어도 초록이었다. 본문과 고정폭 문단의 계산된 `font-family` 첫 이름을 단언하고, 뿌리의
  `--mono`를 지우는 변이로 빨강을 봤다. `font-family: var(--mono)`가 풀리지 않으면 부모의 Noto Sans KR을 물려받는다.
- 고친 것: 코드 주석 셋의 "2026-10-12 이력"을 "셋째"로 특정했다(그날 이력이 셋이다). `tech.md`에 새로 쓴 `allowBuilds` 문장은
  `pnpm-workspace.yaml`과 ADR 0026에 있는 사실을 되풀이해 뺐다. 테마 목록의 주석이 "색의 한 벌"과 "중간 굵기"를 함께 적어
  어긋나, 테마가 색과 중간 굵기를 고른다고 고쳤다. 글꼴 CSS의 라이브러리 모드 문장이 옛 파일을 잰 것임을 적었다. "감싼 요소가 다시
  정한다"는 그 코드가 아직 없어, 다시 정할 수 있고 그 코드는 web-widget이라고 고쳤다. 일지의 잔존 문장(반례: design-refresh 명세와 티켓),
  "보낸 글", 링크 괄호, 워크트리 수(열여섯을 열여덟로)를 고쳤다.
- 남긴 것: Fonts의 그림과 `FONT_FACES`가 같은 다섯 벌을 두 번 적는 것(Duplicated Code, 경미). 클래스가 정적 문자열이어야 해서
  두었다.
- 다시 돌린 것: 커밋 `0eee152`의 pre-commit에서 pytest, web verify, pyright, lint-imports, 타입 우회 검사, 훅 러너, 변이 표
  확인이 모두 지났다. ruff 둘은 `.py`가 없어 `Skipped`였고, 리뷰 뒤에 `.py`를 바꾸지 않아 리뷰 전에 손으로 친 초록이 그대로다.
  사진 비교도 다시 돌려 82개 모두 초록이었다.

## 회고

후보 하나를 냈고 승인됐다.

> 사용자(질문에 답): "회차를 더한다 (Recommended)"

- 헌법 판의 겹침(대기열 행 199, 2회차): `tools/sibling_overlap.py`가 PR #199의 헌법 판 3.0.28을 보여 주지 않아 `git show
  69965cb:docs/constitution/README.md`로 손으로 봤다. 대기열 행 199의 모양 그대로라 그 행에 회차를 더했다.
- 일지에만 남기는 것: Bash의 `cd`로 작업 폴더가 같은 체크아웃의 하위 폴더(`web/`, `web/packages/ui`)로 옮겨져 되돌렸다. 일지
  2026-10-12-36에 이어 둘째다. `hook_bash_cd_outside`는 체크아웃 밖으로 가는 `cd`만 막고, 이번 것은 같은 체크아웃 안이라 해가
  없었다. Grep 도구의 `!**/node_modules/**` glob을 `.env` 훅이 막아 `git grep`으로 바꿨다(훅이 설계대로 돌았다). 불필요한 빈
  파일(`themes.ts.head`) 하나를 잘못 만들어 바로 지웠다.

## 다음

- 티켓 01을 병합한 뒤, 02가 병합되면 03(테마 넷과 색)이다.
