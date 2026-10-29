# 02: 짓기 명령이 나머지 산출을 내고, 파일 검사가 사용 규약 검사를 맡는다

**What to build:** `assemble`의 산출이 디자인 시스템 아티팩트에 올릴 것 전부가 된다. `tokens.json`의 테마 이름이 '녹청 라이트 (Light)'·'녹청 다크 (Dark)' 꼴이 되어, 사람이 테마 메뉴에서 이름만 보고 모드를 가르고 다크 테마의 카드가 다크로 그려질 준비가 된다. 디자인 시스템 README(`README.md`), 기초 카드 넷(`foundations/<폴더>/`), 지침(`guidelines/web-design.md`, `guidelines/index.md`)도 산출에 든다. 지금 사람이 손으로 돌리는 `.design-sync/check-conventions.mjs`의 판정은 01의 파일 검사로 옮겨, README가 드는 클래스·변수·컴포넌트 이름과 기초 카드가 읽는 토큰이 묶음에 있는지를 `pnpm -C web verify`가 본다.

README 원본과 기초 카드 원본은 지금 자리(`.design-sync/conventions.md`, `.design-sync/foundations/`)에서 읽는다. 옮기기와 README 본문 고치기는 04가 한다. 이 티켓도 아무것도 걷어 내지 않아 지금 올리기 절차가 그대로 돈다. 모드 이름은 이미 있는 `build`와 함께 쓰는 표에서 바뀌므로 `build`의 출력도 바뀌지만, 지문이 테마의 표시 이름을 보지 않아 지금 올리기에 보낼 파일이 생기지 않는다.

근거는 `.scratch/design-card-build/spec.md`의 "tokens.json", "디자인 시스템 README와 나머지 파일"의 "README 원본"과 "기초 카드와 지침", Testing Decisions "파일 검사"의 뒤쪽 넷(`tokens.json`, 사용 규약, 기초 카드, 산출 밖), "컴포넌트 카드"의 `globals` 주석과 "티켓의 차례"의 첫 줄이다. 실제 페이지에서 이름에 '(Dark)'가 든 테마의 카드가 다크로 그려진 것은 프로브 README "실제 페이지"의 판 5와 7이다.

**Blocked by:** 01

**Status:** ready-for-agent

### 산출

- [ ] `assemble`이 `tokens.json`을 산출에 둔다. 내용은 이미 있는 `build`가 짓는 것과 같고, 테마 이름의 모드 낱말만 `라이트 (Light)`와 `다크 (Dark)`다. 모드 낱말은 올리기 도구의 모드 이름 표 하나에서 오므로 `build`의 출력도 함께 바뀐다. 그 이름을 고정한 `build`의 시험과 시험 자료를 고친다. 지문 계산은 바꾸지 않는다
- [ ] `README.md`는 README 원본(`.design-sync/conventions.md`)의 바이트 그대로다. 빌린 빌드의 변환기가 그 뒤에 붙이던 영어 절(`# AgentOsUi (…)` 아래의 옛 자리 안내와 컴포넌트 목록)은 짓지 않는다
- [ ] `foundations/`에는 기초 카드 원본 넷(`.design-sync/foundations/` 아래)을 바이트 그대로 둔다
- [ ] `guidelines/web-design.md`는 `.claude/rules/web-design.md`의 바이트이고, `guidelines/index.md`는 그 파일을 가리키는 목록이다

### 파일 검사

- [ ] `tokens.json`의 테마 이름이 모두 ` (Light)`나 ` (Dark)`로 끝나고, 그 낱말이 테마 id의 모드와 맞는다
- [ ] 지금 `check-conventions.mjs`의 머리 주석이 든 판정을 하나씩 산출 폴더에서 본다. 그 스크립트가 보던 `_ds_bundle.css`·`_ds_bundle.js` 대신 정식 자리의 묶음(`components/bundle.css`·`components/bundle.js`)을 본다
  - README의 "이미 있는 유틸리티 클래스:" 뒤 백틱 묶음의 클래스는 묶음 CSS에 있다. 바로 뒤가 이름 글자인 것(`.flex-col` 안의 `.flex`)은 세지 않는다
  - "흔한 Tailwind 이름 가운데"와 "CSS 가 없어" 사이의 백틱 낱말은 묶음 CSS에 없다
  - README가 든 `--이름` 변수는 묶음 CSS에 선언이 있다. 쓰지 말라는 예시로 든 원색 토큰("테마의 재료" 문장)과 `<이름>` 자리 표시는 빼고, 여백 줄의 `-2` 꼴은 `--spacing-2`로 푼다
  - README의 `AgentOsUi.<이름>`과 예시의 `const { … } = window.AgentOsUi`가 든 이름은 묶음 JS가 내보내고, 컴포넌트 이름이면 묶음 머리의 컴포넌트 목록에도 있다. 지금 검사는 컴포넌트를 `<이름>.d.ts`로 봤지만 타입은 짓지 않는다(명세 Out of Scope)
  - README가 `data-theme`·`data-density`의 값으로 든 키마다 묶음 CSS에 그 선택자가 있다
- [ ] 기초 카드 넷이 `foundations/<폴더>/`마다 HTML 하나로 있고 첫 줄이 `@dsCard` 표지이며 원본과 같은 바이트다. 카드가 읽는 `var(--이름)`과 `data-value="--이름"`은 묶음 CSS에 선언이 있고, 카드가 쓰는 `data-theme`·`data-density` 값은 선택자가 있다. 지금 검사가 함께 보던 목록 타일(`thumbnail.html`)은 04가 지우므로 뺀다
- [ ] 산출 밖에서 둘을 본다. 컴포넌트 층 폴더의 스토리 파일마다 showcase 스토리가 하나 이상 있다(없으면 그 컴포넌트의 카드가 말없이 빠진다). showcase 스토리에 `globals`가 없다(카드의 테마와 모드는 페이지가 정한다). 지금 검사가 보던 빼는 목록(`config.json`의 skip)은 04가 지우므로 그 일치 판정은 뺀다
- [ ] 옮긴 판정과 `check-conventions.mjs` 머리 주석의 판정을 하나씩 대 본 표를 이 티켓의 결과에 적는다. 뺀 것(타입, 빼는 목록, 목록 타일, `ds-bundle/`에 복사됐는지)은 까닭과 함께 적는다
- [ ] **변이.** 새 판정마다 그 판정만 빨개지는 변이를 01이 만든 표에 더해 돌린다

### 마무리

- [ ] 검증 명령이 모두 초록이다. 모델 경로, 위젯, 관리 화면을 건드리지 않아 `-m llm`·`-m llm_widget`·e2e·사진 비교는 칠 일이 없다
