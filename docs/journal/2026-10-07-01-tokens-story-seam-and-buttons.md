# 2026-10-07 (01) design-system 티켓 01: 디자인 토큰과 스토리 테스트 이음매, 아이콘·버튼·아이콘 버튼

일지 2026-10-06-14의 "다음"으로 연 새 세션이다. 주 체크아웃(main, `9a7821b`)에서 `EnterWorktree`로
`.claude/worktrees/01-tokens-story-seam-and-buttons`에 들어가 origin/main(`3fddbb1`, PR #155 병합)에서
`feature/01-tokens-story-seam-and-buttons`를 땄다. 순번은 main과 형제 워크트리의 `docs/journal/`에 2026-10-07이 없어 01이다.
앞 세션의 측정 사본(스크래치의 `ds/storybook`)은 남아 있어 그 생성물을 옮겼다.

## 설치한 판

잰 판과 모두 같다. storybook·@storybook/react-vite·@storybook/addon-vitest·@storybook/addon-a11y 10.6.1, @vitest/browser-playwright
5.0.2(vitest 5.0.2에 맞췄다. 5.0.3이 나와 있다), playwright 1.63.0, tailwindcss·@tailwindcss/vite·@tailwindcss/cli 4.3.3, vite
8.3.1(인스턴스 하나), @fontsource/noto-sans-kr·@fontsource/jetbrains-mono 5.3.0, @ibm/plex-mono 2.5.0, lucide-react 1.51.0(1.52.0이
나와 있지만 잰 판에서 시작했다), React 19.3.0. 글꼴 셋과 lucide-react는 판을 고정했다. 설치는 `pnpm-workspace.yaml`의 `allowBuilds`
셋 밖으로 아무것도 쓰지 않았다(공급망 유예는 그대로). lucide-react 1.51.0에 아이콘 열일곱(`IconName` 열여섯과 `loader-circle`)이
`dist/esm/icons/<이름>.mjs`로 모두 있었다.

## 이 세션이 정한 것

티켓 파일의 "이 티켓이 정한 것" 절이 원천이고 여기는 근거다.

- **props의 모양(03·04가 따른다).** 디자인 파일의 props 표가 계약의 최소이고, 표의 이름이 요소의 기본 속성과 겹치면 표의 타입이
  이긴다(버튼의 `onClick: () => void`, `children: string`). 나머지 기본 속성은 `NativeProps<요소, 표의 이름 | 컴포넌트가 정하는 이름>`
  (`ComponentProps`에서 `className`·`style`과 그 이름들을 뺀 것, `ref` 포함)으로 받아 그 요소에 넘긴다. 컴포넌트가 정하는 속성(불러오는
  중의 `aria-busy`·`aria-disabled`, 아이콘 버튼의 `aria-label`·`title`·`type`)은 받지 않아 쓰는 쪽이 덮지 못한다. 글 입력·스위치처럼
  요소를 엮는 컴포넌트는 나머지를 입력 요소에 넘긴다(`name`, `id`, `autoComplete`, `aria-*`가 그 요소의 것이다). 원천은
  `web/packages/ui/src/props.ts`의 머리 주석이다.
- **앱 스토리의 자리.** 앱마다의 Storybook(`apps/<앱>/.storybook/`)이고 패키지가 미리보기 본체를 다섯째 진입점 `./storybook`으로
  낸다. ADR 0026의 2026-10-07 이력(조건 넷과 거부한 안 셋)이다. 이 결정으로 티켓의 "`exports`는 넷"이 다섯이 되었고, 명세에
  날짜 주석을 달았다. 셀프 리뷰를 반영한 뒤 초안의 요지와 거부한 안 둘을 보이고 물었다(대기열 126).

  > 사용자(질문에 답): "이대로 확정 (Recommended)"
- **아이콘의 모듈 선언을 앱이 보게 하는 길.** 스크래치에 패키지와 소비자 tsconfig를 두고 tsc로 손으로 봤다. 앰비언트
  `declare module "lucide-react/dist/esm/icons/*"`는 패키지의 tsc에서는 지났지만 패키지 소스를 import하는 소비자의 tsc에서
  TS2307이었다. 모듈 파일 안에 둔 와일드카드 선언을 `import type {}`로 끌어와도 TS2307이었다. 그것을 쓰는 파일의 `/// <reference path>`만
  지났다. 그래서 `Icon.tsx`가 경로로 참조하고, ESLint는 그 한 파일에서만 `triple-slash-reference`의 경로를 푼다(판정자 테스트에
  패키지의 다른 파일과 앱 atoms의 빨강 둘, `Icon.tsx`의 초록 하나).
- **lucide의 클래스.** lucide-react는 React에서 svg에 `lucide lucide-<이름>`을 늘 붙인다. 1.51.0의 `Icon.mjs`는
  `includeDefaultClasses`를 넘기지 않아 끌 길이 없다(`buildLucideIconNode.mjs`와 함께 읽었다). 아이콘별 `__iconData`는 공개 타입에
  없어 쓰지 않았다. 그래서 afterEach의 판정이 그 두 꼴의 클래스만 뺀다. 빼지 않으면 아이콘 스토리가 빨갛다(변이).
- **불러오는 중의 버튼.** 디자인 파일은 도는 표시를 글자 앞에 그렸는데, 아이콘이 없는 버튼은 그만큼 넓어져 티켓의 "너비가
  그대로"와 어긋난다. 글자 자리를 `opacity-0`으로 그대로 두고 도는 표시를 가운데에 겹쳤다. 이름은 그대로 읽힌다.
- **상태마다 클래스를 고른다.** 쓸 수 없음과 불러오는 중에는 올림·누름의 클래스를 두지 않는다. 불러오는 중은 `disabled`가 아니어서
  `disabled:` 변형으로는 그 상태의 올림·누름을 끌 수 없기 때문이다. 처음에는 Tailwind가 `hover:`를 `disabled:` 뒤에 내어 올림 색이
  이긴다는 것을 이유로 적었는데 거짓이었다. 셀프 리뷰가 짚었고, 4.3.3 CLI로 `hover:`·`active:`·`disabled:`를 함께 컴파일하자
  `disabled:`가 맨 뒤에 나왔다(스크래치에서 손으로 봤다).
- **판정 스토리의 태그는 글자 그대로다.** 메타의 `tags`에 상수를 넣자 Storybook 10.6.1의 색인이 "CSF: Expected tag to be string
  literal"로 그 파일을 색인하지 못했다(손으로 봤다). 미리보기의 기본 내보내기도 함수 호출이면 "CSF Parsing error: Expected
  'ObjectExpression'" 경고가 나서 객체 리터럴로 펼쳤다.
- **Fonts 판정의 굵기.** `document.fonts.load`는 그 굵기의 글꼴이 없으면 가까운 굵기를 받아도 `loaded`로 답한다(프로브의 판정은
  그것만 봤다). 받은 글꼴의 `weight`까지 보게 고쳤고, JetBrains Mono 500을 빼는 변이가 빨갛다.
- **포커스 링은 공문에서 잰다.** 먹은 `focus`와 `accent`가 같은 색이라 링이 `accent`를 읽어도 지난다. 두 Focus 스토리를
  `globals: { theme: "gongmun" }`으로 돌린다.
- **버튼 셋의 320px.** `flex-wrap`이면 넘침이 줄바꿈으로 가려져 무엇을 잘못해도 초록이다. 한 줄(`flex`)로 그리게 고쳤고 안쪽 여백을
  넓히는 변이가 빨갛다.

## 확인한 것

- **값의 대조(티켓의 "옮길 때 한 번").** 커밋한 디자인 토큰 CSS를 스크래치 스크립트로 읽어 `design.mjs`의 출력과 맞댔다. 원색
  330개, 쓰임새 26개 × 열 벌의 대응(기본 둘과 테마·모드의 예외), 공문의 예외 다섯(라이트 넷과 다크 `focus`), 시스템 다크 규칙이 다크와
  같은 것, 테마마다 `--sans`·`--mono`·`--weight-mid`, 글자 여섯 단계의 크기·줄 높이·굵기, 간격·조작 높이·아이콘·모서리·기준 폭·그림자가
  어긋남 0이었다. 디자인 파일에 없는 것(간격 `0`, 부품 치수, 움직임, `medium` 500, 감싼 요소)은 명세가 정한 것이다.
- **afterEach.** 판정 태그가 없는 보통 스토리(버튼 셋의 320px)에 `text-base`를 심자 그 스토리 테스트가 빨갰다(`tools/mutate.py`,
  아래 변이 표의 첫째. 그 play는 클래스를 보지 않으므로 빨강은 afterEach의 것이다). 판정 스토리(RemFree)에 심어도 같았다.
  afterEach의 예외가 스토리 테스트의 실패로 이어진다.
- **진입점.** 패키지 안에서 자기 이름을 import하는 스토리가 다섯을 `exports`대로 풀었다. 워크스페이스 링크(`node_modules/@agent-os`)가
  뿌리에도 패키지에도 없는 자리였다. Node의 `import.meta.resolve`와 tsc(bundler 해석)도 같은 파일을 냈다(손으로 봤다).
- **`build`.** `pnpm -C web/packages/ui run build`가 `dist/`를 냈고 `dist/theme.css`는 25,363바이트에 rem 0, `@font-face` 0이었다.
  처음에는 `tsc`의 선언 생성이 `storyPreview`의 추론 타입을 이름 붙이지 못해(TS2742) 반환 타입을 `Preview`로 적었다.
- **정적 빌드.** `build-storybook`이 성공했고 `index.json`의 항목 34개 가운데 판정 스토리에 `judgment`, 음성 사례에 `planted`가
  실렸다. `dist/`와 `storybook-static/`은 `git status --ignored`에서 무시로 나왔다.
- **브라우저가 없을 때.** `PLAYWRIGHT_BROWSERS_PATH`를 빈 폴더로 두고 스토리 프로젝트를 돌리자 종료 코드 1로 실패했다("Executable
  doesn't exist at …\chromium_headless_shell-1243\…"). 건너뛰지 않는다. 찾은 실행 파일이 헤드리스 셸이라 CI와 클론 블록의
  `--only-shell chromium`이면 된다(셸만 깐 폴더로 돌려 보지는 않았다. CI가 처음 본다).
- **Vite의 의존성 최적화.** 캐시가 있는 체크아웃에 lucide 서브패스 import가 처음 들어오자 Vite가 실행 중에 최적화하고 페이지를 다시
  읽어 그 실행이 깨졌다("Vite unexpectedly reloaded a test"). 캐시(`web/node_modules/.vite`, `.cache`)를 지운 실행은 처음부터 모두
  지났다. CI처럼 캐시가 없는 첫 실행은 괜찮고, 새 의존성을 처음 import한 로컬 실행만 한 번 깨진다.
- **스토리 테스트 시간.** 스토리 프로젝트만 돌리면 6파일 34개에 약 5초, `verify`의 test 단계 전체는 113초였다.

## TDD와 변이

스토리(행동 테스트)를 컴포넌트보다 먼저 썼다. 처음 돌렸을 때 실패한 것은 둘이다. 버튼의 아이콘 순서 확인이 글자를 요소로 찾아
텍스트 노드를 놓쳤고(확인 방법을 고쳤다), 판정 스토리의 태그가 색인을 멈췄다(위). 구현 뒤에 쓰거나 처음부터 초록이던 스토리는
변이 표 `.scratch/design-system/probes/ui_mutations.toml`(36개, 셀프 리뷰 뒤 보통 스토리의 `text-base`를 더해 37개)로 빨강을 봤다. 첫 판에서 하나가 초록으로 어긋났다. 쓸 수 없는 버튼의
바탕을 `tint`로 바꾼 변이인데, `tint`와 `disabled-surface`는 열 벌 모두 같은 원색(라이트 `gray-200`, 다크 `gray-800`)을 가리켜
계산값으로는 가를 수 없다. 값이 다른 `raised`로 겨눠 빨강을 봤다. 같은 까닭으로 둘을 바꿔 쓰는 실수는 계산값의 테스트가 잡지
못한다.

## 하네스 확인

새 규칙 `.claude/rules/web-design.md`와 고친 implement 스킬을 새 `claude -p` 세션(Claude Code 2.1.291, sonnet, `--setting-sources
project,local --strict-mcp-config`, 워크트리에서)으로 불렀다.

- 헌법에 적힌 규칙 카나리아 명령(`--tools Read --disallowed-tools 'Read(./.claude/**)'`)으로는 새 규칙뿐 아니라 이미 있던
  `web-admin.md`(일지 2026-10-06-08이 같은 명령으로 실린 것을 봤다)까지 "없음"이었다. 주 체크아웃에서 돌려도 같았다. `CLAUDE.md`는
  실렸다. 거부 플래그만 빼자 실렸다. 2.1.291에서는 그 거부가 하네스의 path 규칙 적재까지 막는 것으로 본다(손으로 봤다. 판의 변경
  기록은 읽지 않았다). 고치는 일은 작업 칩으로 띄웠다(아래 회고).
- 그래서 거부 플래그 없이 `--output-format stream-json --verbose`로 모델이 읽은 파일이 지정한 하나뿐인지 함께 봤다. 패키지의
  `Button.tsx`를 연 세 번과 관리 화면의 `components/organisms/ReadSection.tsx`를 연 한 번 모두 태그 둘(`"judgment"`, `"planted"`)을
  옮겼고 읽은 파일은 그 하나였다. paths 밖의 `web/package.json`을 연 대조군은 "없음"이었다.
- 스킬은 `--tools Skill`(init의 `tools`가 `Skill` 하나, `mcp_servers` 0)로 `/implement` 머리의 카나리아에 세 번 모두
  `pnpm -C web exec playwright install --only-shell chromium`을 옮겼다. 파일을 읽을 도구가 없고 옛 본문에는 이 명령이 없다.

## 셀프 리뷰

`/code-review`(base `3fddbb1`, 바뀐 파일 20, 커밋 0, 미추적 4묶음)를 두 축 나란히 돌렸다. 소스가 든 변경이라 sonnet으로 내리지 않았다.

- **고쳤다, 표준 축.** Major 하나: rules와 버튼 주석이 Tailwind가 `hover:`를 `disabled:` 뒤에 낸다고 단언했는데 거짓이었다(위
  "상태마다 클래스를 고른다"). Minor 둘: 프로브 README의 "10분 남짓(한 번 쟀다)"을 손으로 본 것으로, 한 패키지에서 두 뜻으로 쓰인
  "token"을 `semanticColor`(쓰임새 토큰)와 `name`(class 낱말)으로 갈랐다. Nit 셋: rules의 "조합마다 스토리"를 "만드는 클래스가 모두
  한 번은 그려지게"로, 02의 사진 비교를 현재형으로 적은 세 자리를 "뺄 수 있게 단다"로, 티켓의 "진입점 넷" 자리들을 "정한 것" 7이
  모두 가리키게 했다. 쓰는 곳이 없는 공개 이름(`JUDGMENT_TAG`, 미리보기의 `themeOf`·`modeOf`, 진입점의 `propertyDefaults`·변형과
  크기의 배열)을 걷고 변형과 크기는 유니온 타입으로 두었다. ADR 이력의 앱이 `@source`를 빠뜨리면 스토리 테스트가 잡는다는 문장을
  패키지 소스에 없는 클래스로 좁히고, 앱은 shadow 틀에도 자기 CSS를 넘긴다는 것을 독스트링·ADR·`plan.md`에 적었다.
- **고쳤다, 명세 축.** props의 모양을 일지에 적었다(위). afterEach 변이를 판정 태그 없는 보통 스토리에 하나 더 겨눴다. ADR과
  `plan.md`의 "앱마다 `storybook` 프로젝트"는 Vitest 5.0.2가 겹치는 이름을 거부하므로("Project name … is not unique", 설치본의
  `dist/chunks`를 읽었다) 이름이 다른 프로젝트로 고쳤다. ADR의 `/design-sync`가 패키지의 `.storybook/`만 읽는다는 문장은 근거 없는 닫힌
  주장이라 어림으로 낮췄다. 진입점 스토리의 타입 검사는 CSS 둘이 `?inline` 와일드카드 선언으로 풀려 셋만 본다고 고쳐 적었다.
  Matrix가 쓰임새 26개의 수도 단언한다. 02 티켓의 메모에서 그 티켓이 정할 일을 새로 얹은 문장을 사실만 남겼다.
- **남겼다.** 버튼과 아이콘 버튼의 누름 처리와 상태 클래스 식이 같다(Duplicated Code). 불러오는 중을 가진 컴포넌트가 둘뿐이라
  셋째가 생길 때 뽑는다. CSS 규칙을 훑는 순회가 판정 함수와 판정 스토리에 따로 있다. `./testing`이 내는 이름을 명세의 넷보다 늘리지
  않으려고 두었다. CI의 web·e2e 잡이 Playwright 설치 단계를 같은 모양으로 되풀이한다. 같은 모양을 일부러 따랐고, 합치는 것은 별도의
  일이다.
- 반영 뒤 바꾼 원문의 변이 넷을 다시 돌려 모두 기대대로였고, 표 전체의 원문 확인(`--check`, 37개)도 지났다.

## 검사

- 검증 명령: `uv run pytest -q` 1638 통과(7 deselected), `ruff check`·`ruff format --check`, `pyright` 0 오류, `lint-imports` 5 계약,
  `pnpm -C web verify`(21파일 309개, 스토리 34개 포함) 모두 초록. 판정 명령은 파이프 없이 돌리고 로그 파일로 봤다.
- 지침 검사, 타입 우회 검사, 바뀐 마크다운의 표 검사 초록.
- 변이 36개 모두 기대대로(위). e2e는 중계·시작 래퍼·api-client·서버 라우트를 건드리지 않아 CI가 돈다.
