# 02: 짓기 명령이 나머지 산출을 내고, 파일 검사가 사용 규약 검사를 맡는다

**What to build:** `assemble`의 산출이 디자인 시스템 아티팩트에 올릴 것 전부가 된다. `tokens.json`의 테마 이름이 '녹청 라이트 (Light)'·'녹청 다크 (Dark)' 꼴이 되어, 사람이 테마 메뉴에서 이름만 보고 모드를 가르고 다크 테마의 카드가 다크로 그려질 준비가 된다. 디자인 시스템 README(`README.md`), 기초 카드 넷(`foundations/<폴더>/`), 지침(`guidelines/web-design.md`, `guidelines/index.md`)도 산출에 든다. 지금 사람이 손으로 돌리는 `.design-sync/check-conventions.mjs`의 판정은 01의 파일 검사로 옮겨, README가 드는 클래스·변수·컴포넌트 이름과 기초 카드가 읽는 토큰이 묶음에 있는지를 `pnpm -C web verify`가 본다.

README 원본과 기초 카드 원본은 지금 자리(`.design-sync/conventions.md`, `.design-sync/foundations/`)에서 읽는다. 옮기기와 README 본문 고치기는 04가 한다. 이 티켓도 아무것도 걷어 내지 않아 지금 올리기 절차가 그대로 돈다. 모드 이름은 이미 있는 `build`와 함께 쓰는 표에서 바뀌므로 `build`의 출력도 바뀌지만, 지문이 테마의 표시 이름을 보지 않아 지금 올리기에 보낼 파일이 생기지 않는다.

근거는 `.scratch/design-card-build/spec.md`의 "tokens.json", "디자인 시스템 README와 나머지 파일"의 "README 원본"과 "기초 카드와 지침", Testing Decisions "파일 검사"의 뒤쪽 넷(`tokens.json`, 사용 규약, 기초 카드, 산출 밖), "컴포넌트 카드"의 `globals` 주석과 "티켓의 차례"의 첫 줄이다. 실제 페이지에서 이름에 '(Dark)'가 든 테마의 카드가 다크로 그려진 것은 프로브 README "실제 페이지"의 판 5와 7이다.

**Blocked by:** 01

**Status:** in-progress

### 산출

- [x] `assemble`이 `tokens.json`을 산출에 둔다. 내용은 이미 있는 `build`가 짓는 것과 같고, 테마 이름의 모드 낱말만 `라이트 (Light)`와 `다크 (Dark)`다. 모드 낱말은 올리기 도구의 모드 이름 표 하나에서 오므로 `build`의 출력도 함께 바뀐다. 그 이름을 고정한 `build`의 시험과 시험 자료를 고친다. 지문 계산은 바꾸지 않는다
- [x] `README.md`는 README 원본(`.design-sync/conventions.md`)의 바이트 그대로다. 빌린 빌드의 변환기가 그 뒤에 붙이던 영어 절(`# AgentOsUi (…)` 아래의 옛 자리 안내와 컴포넌트 목록)은 짓지 않는다
- [x] `foundations/`에는 기초 카드 원본 넷(`.design-sync/foundations/` 아래)을 바이트 그대로 둔다
- [x] `guidelines/web-design.md`는 `.claude/rules/web-design.md`의 바이트이고, `guidelines/index.md`는 그 파일을 가리키는 목록이다

### 파일 검사

- [x] `tokens.json`의 테마 이름이 모두 ` (Light)`나 ` (Dark)`로 끝나고, 그 낱말이 테마 id의 모드와 맞는다
- [x] 지금 `check-conventions.mjs`의 머리 주석이 든 판정을 하나씩 산출 폴더에서 본다. 그 스크립트가 보던 `_ds_bundle.css`·`_ds_bundle.js` 대신 정식 자리의 묶음(`components/bundle.css`·`components/bundle.js`)을 본다
  - README의 "이미 있는 유틸리티 클래스:" 뒤 백틱 묶음의 클래스는 묶음 CSS에 있다. 바로 뒤가 이름 글자인 것(`.flex-col` 안의 `.flex`)은 세지 않는다
  - "흔한 Tailwind 이름 가운데"와 "CSS 가 없어" 사이의 백틱 낱말은 묶음 CSS에 없다
  - README가 든 `--이름` 변수는 묶음 CSS에 선언이 있다. 쓰지 말라는 예시로 든 원색 토큰("테마의 재료" 문장)과 `<이름>` 자리 표시는 빼고, 여백 줄의 `-2` 꼴은 `--spacing-2`로 푼다
  - README의 `AgentOsUi.<이름>`과 예시의 `const { … } = window.AgentOsUi`가 든 이름은 묶음 JS가 내보내고, 컴포넌트 이름이면 묶음 머리의 컴포넌트 목록에도 있다. 지금 검사는 컴포넌트를 `<이름>.d.ts`로 봤지만 타입은 짓지 않는다(명세 Out of Scope)
  - README가 `data-theme`·`data-density`의 값으로 든 키마다 묶음 CSS에 그 선택자가 있다
- [x] 기초 카드 넷이 `foundations/<폴더>/`마다 HTML 하나로 있고 첫 줄이 `@dsCard` 표지이며 원본과 같은 바이트다. 카드가 읽는 `var(--이름)`과 `data-value="--이름"`은 묶음 CSS에 선언이 있고, 카드가 쓰는 `data-theme`·`data-density` 값은 선택자가 있다. 지금 검사가 함께 보던 목록 타일(`thumbnail.html`)은 04가 지우므로 뺀다
- [x] 산출 밖에서 둘을 본다. 컴포넌트 층 폴더의 스토리 파일마다 showcase 스토리가 하나 이상 있다(없으면 그 컴포넌트의 카드가 말없이 빠진다). showcase 스토리에 `globals`가 없다(카드의 테마와 모드는 페이지가 정한다). 지금 검사가 보던 빼는 목록(`config.json`의 skip)은 04가 지우므로 그 일치 판정은 뺀다
- [x] 옮긴 판정과 `check-conventions.mjs` 머리 주석의 판정을 하나씩 대 본 표를 이 티켓의 결과에 적는다. 뺀 것(타입, 빼는 목록, 목록 타일, `ds-bundle/`에 복사됐는지)은 까닭과 함께 적는다
- [x] **변이.** 새 판정마다 그 판정만 빨개지는 변이를 01이 만든 표에 더해 돌린다

### 마무리

- [x] 검증 명령이 모두 초록이다. 모델 경로, 위젯, 관리 화면을 건드리지 않아 `-m llm`·`-m llm_widget`·e2e·사진 비교는 칠 일이 없다

## 결과

- **산출.** `assemble`이 `tokens.json`, `README.md`, `foundations/<colors|density|spacing|type>/index.html`, `guidelines/web-design.md`, `guidelines/index.md`를 더 짓는다. `tokens.json`은 `build`와 같은 함수(`buildTokensJson`)로 패키지의 디자인 토큰 CSS(`DEFAULT_CSS`)에서 짓고, 나머지는 저장소 원본을 바이트 그대로 둔다. `guidelines/index.md`는 지금 아티팩트에 올라간 판(`1793259788-d3cd`)의 그 파일과 같은 글이다(아티팩트를 읽어 손으로 봤다. 셀프 리뷰 때 Artifact 도구의 read가 그 판의 46바이트와 sha256 `a9bd8e3a…`를 냈고, 지은 파일과 `cmp`로 맞댔다). 원본을 읽지 못하거나 기초 카드 원본 폴더가 비면 `input` 오류로 끝나고, 문서를 빌드보다 먼저 지어 그 오류가 vite·Tailwind를 띄우기 전에 난다. 이 오류 갈래는 원본 경로가 고정이라 시험이 지나지 않는다(코드를 읽은 것이다).
- **모드 낱말.** `build.ts`의 모드 이름 표(`MODE_NAMES`)를 `라이트 (Light)`·`다크 (Dark)`로 바꿔 `build`의 출력도 함께 바뀐다. 그 이름을 고정한 `build.test.ts`의 기대값만 고쳤다. 시험 자료 `uploaded-tokens.json`·`page-saved-tokens.json`은 받은 바이트라 옛 이름 그대로 두었고, 지문 계산은 손대지 않았다. 고친 뒤 이 폴더에서 `assemble.test.ts`를 뺀 시험 14파일(`build`·`check`·`claim`·`color`·`decide`·`file-hash`·`import`·`main`·`record-check`·`sync-record`·`theme-css`·`tokens-json`·`tokens-overlay`·`upload`의 `.test.ts`) 457개가 vitest node 프로젝트에서 지났다(셀프 리뷰 때 그 14파일을 이름으로 주어 돌려 손으로 봤다). 전체 판정은 아래 마무리의 검증 명령이다.
- **짓기의 나누기.** PR #433 claude-review의 Minor(`assembleInto`가 산출 파일마다 내용을 쓰는 몫과 카드를 짓는 반복을 섞는다)를 받아 `assembleInto`를 문서(`writeDocuments`), 묶음(`writeBundles`), 카드(`writeCards`) 셋을 이 차례로 부르는 함수로 나눴다. 문서가 먼저인 것은 저장소 원본이 없을 때 빌드를 띄우기 전에 끝내려는 것이다(셀프 리뷰가 차례를 바꿨다). 01의 변이가 겨누는 줄은 들여쓰기까지 그대로 옮겨, `uv run python tools/mutate.py --check`가 변이 55 모두 원문이 한 번씩 있다고 찍었다.
- **판정 대조.** `check-conventions.mjs` 머리 주석의 판정과 옮긴 자리(`web/tools/sync-design-system/assemble.test.ts`의 사례 이름)를 하나씩 맞댄다. 그 스크립트의 `_ds_bundle.css`·`_ds_bundle.js` 대신 정식 자리 `components/bundle.css`·`components/bundle.js`를 본다.

| `check-conventions.mjs`의 판정 | 옮긴 사례 | 달라진 것 |
|---|---|---|
| "이미 있는 유틸리티 클래스:" 묶음의 클래스가 묶음 CSS에 있다(바로 뒤가 이름 글자면 세지 않는다) | README 가 이미 있다고 든 유틸리티 클래스가 묶음 CSS 에 모두 있다 | 없음 |
| "흔한 Tailwind 이름 가운데"와 "CSS 가 없어" 사이의 낱말은 없다(변형은 `.<이름>\:`) | README 가 CSS 가 없다고 든 흔한 Tailwind 이름은 묶음 CSS 에 없다 | 없음 |
| `--이름`은 선언이 있다("테마의 재료" 줄과 `<이름>` 자리 표시는 빼고 `-2`는 `--spacing-2`로 푼다) | README 가 든 CSS 변수는 묶음 CSS 에 선언이 있다 | 없음 |
| `AgentOsUi.<이름>`과 `const { … } = window.AgentOsUi`의 이름이 번들의 내보내기 블록에 있다 | 사용 규약: README 가 든 AgentOsUi 의 이름은 묶음이 전역으로 내보내고, 컴포넌트 이름이면 묶음 머리의 목록에도 있다 | 압축된 IIFE의 글(`return e.Alert=Pe,…`)을 풀지 않고 chromium에 React와 묶음을 실어 `Object.keys(window.AgentOsUi)`로 본다 |
| 컴포넌트는 `components/` 아래 `<이름>.d.ts`가 있다 | 같은 사례의 "묶음 머리의 목록" | 타입은 짓지 않아(명세 Out of Scope) `components/bundle.js` 첫 줄의 `@ds-bundle` 머리가 든 `components`의 이름으로 본다 |
| `data-theme`·`data-density`의 키마다 선택자가 있다 | README 가 data-theme·data-density 의 값으로 든 키마다 묶음 CSS 에 그 선택자가 있다 | 없음 |
| 컴포넌트마다 `showcase` 스토리가 하나 이상 있다(참조 Storybook 색인) | 층 폴더의 스토리 파일마다 showcase 스토리가 하나 이상 있다 | 색인 대신 층 폴더의 스토리 소스를 읽는다 |
| 기초 카드 폴더 넷, 폴더마다 HTML 하나, 첫 줄 `@dsCard` | 기초 카드 넷이 폴더마다 HTML 하나로 있고 첫 줄이 @dsCard 표지이며 원본과 같은 바이트다 | 산출 폴더의 `foundations/`를 보고 원본과 바이트를 맞댄다. 옛 검사처럼 넷 밖의 폴더도 HTML 하나와 표지를 본다 |
| 카드와 `thumbnail.html`이 읽는 `var(--이름)`·`data-value="--이름"`은 선언이, `data-theme`·`data-density` 값은 선택자가 있다 | 기초 카드가 읽는 변수는 묶음 CSS 에 선언이 있고 카드가 쓰는 data-theme·data-density 값은 선택자가 있다 | `thumbnail.html`은 뺀다 |
| (없음) | showcase 스토리와 그 파일의 meta 에 globals 가 없다 | 새 판정. meta의 `globals`도 모든 스토리에 걸려 함께 본다 |
| (없음) | `tokens.json` 바이트, 테마 이름, README·지침 바이트의 사례 넷 | 새 판정 |

- **뺀 것.** 타입(`<이름>.d.ts`)은 짓지 않아 묶음 머리의 목록으로 갈음했다(명세 Out of Scope). 빼는 목록(`config.json`의 skip)과 그 일치 판정은 04가 그 목록을 지우므로 뺐다. 목록 타일(`thumbnail.html`)도 04가 지운다. `ds-bundle/`에 같은 내용으로 복사됐는지는 산출 폴더가 곧 올릴 것이라 볼 자리가 없고, 기초 카드·README·지침은 원본과 바이트를 맞대는 사례가 그 몫을 맡는다.
- **검증.** 셀프 리뷰를 반영한 작업 트리에서 `uv run ruff check .`와 `uv run ruff format --check .`가 지났고, `uv run python tools/run_checks.py`의 열 검사(`check-ticket`, `zizmor`, `lint-imports`, `check-instructions`, `check-type-escapes`, `pyright-linux`, `pyright`, `run-hooks`, `pytest`, `web-verify`)가 모두 `Passed`였다(러너 출력을 손으로 봤다).
- **판정의 원천.** 문장을 찾는 정규식과 이름 가드(`hasClass`의 뒤 글자, 변수의 앞 글자)는 `check-conventions.mjs`의 것을 옮겼다. 그 스크립트는 04가 지울 때까지 그대로 둔다.
- **변이.** `probes/assemble_mutations.toml`에 30~55의 스물여섯을 더했다. `PYTHONUTF8=1 uv run python tools/mutate.py .scratch/design-card-build/probes/assemble_mutations.toml 30 … 55`가 "변이 26 모두 기대대로"를 찍었다(기준선 13 모두 초록, `표지 없음` 줄 없음). 셀프 리뷰가 56~58의 셋(넷 밖의 기초 카드 폴더, 변수 판정의 앞 글자 가드, 기초 카드 폴더의 파일 목록)을 더했고, 그 셋만 돌린 실행이 "변이 3 모두 기대대로"를 찍었다. 결과와 재지 않은 것은 프로브 README "2026-10-30 티켓 02의 변이"다. 시험은 구현 전에 열하나가 빨갰고(산출 파일이 없었다), 산출 밖 사례 둘은 구현 전부터 초록이라 변이로 빨강을 봤다(구현 전의 빨강과 초록은 앞 회차가 일지에 적은 것이고, 어떻게 봤는지는 적히지 않았다).
