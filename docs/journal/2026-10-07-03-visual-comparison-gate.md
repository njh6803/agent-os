# 2026-10-07 (03) design-system 티켓 02: 사진 비교 게이트

일지 2026-10-07-01의 "다음"으로 연 새 세션이다. 지시문대로 주 체크아웃에서 `tidy-checkouts`를 먼저 돌았고, 루트 main을
`cbb6a6c`에서 `162ae54`(PR #156 병합)로 당겼다. 병합되고 깨끗한 워크트리 열셋 가운데 셋을 지운 뒤 넷째
`mutate-any-runner`에서 `git worktree remove`가 "failed to delete … Invalid argument"로 끝나 스킬대로 나머지 삭제를 모두
멈췄다. git 2.32가 등록만 지우고 폴더는 `.git` 없이 남았다(브랜치 `chore/mutate-any-runner`는 남겼다). 보고만 하고
지시문을 이었다. 그 뒤 `EnterWorktree`로 `.claude/worktrees/02-visual-comparison-gate`에 들어가 origin/main(`162ae54`)에서
`feature/02-visual-comparison-gate`를 땄다. 순번은 main과 형제 워크트리의 `docs/journal/`에 01(main)과 02(나란히 도는
카나리아 세션)가 있어 03이다.

## 이미지

Docker 엔진 24.0.7이 돌고 있었고 `mcr.microsoft.com/playwright:v1.63.0-noble`이 이미 있었다. 이미지 ID
`sha256:2c1f4e0fd6450f43ddb46d60c2a6df30855a8588e165b1f2559fb0eda8d7ff35`가 프로브 README의 잰 이미지와 같았다.
`docker manifest inspect`와 `docker buildx imagetools inspect`로 레지스트리를 읽었다. 태그는 여전히 index
`sha256:eff16c30…`를 가리키고, 그 안의 linux/amd64 매니페스트가 `sha256:bc6ab0d6d44ff4826e4cb8c1e6d801e185bfc42bb0753f8e2a30efc70db054c7`
(README의 `bc6ab0d6d44f…`), arm64가 `sha256:a0f44989…`이며, amd64 매니페스트의 config가 위 이미지 ID다. 태그에 amd64
digest를 붙인 이름으로 `docker run`하자 매니페스트만 받고 층은 받지 않았으며(`Downloaded newer image`, 층의 `Pull complete`
없음) 받은 이미지의 ID가 같았다. `/ms-playwright/.docker-info`의 `driverVersion`은 1.63.0, node는 24.20.0이었다.

## 설치한 판

`@playwright/test`를 `web/packages/ui`의 devDependency(`^1.63.0`, 관리 화면과 같은 모양)로 더했다. 락은 이미 1.63.0을
들고 있어 importer 줄 셋만 늘었다. 이미지 태그의 판과 같다.

## 이 세션이 정한 것

티켓 파일의 "이 티켓이 정한 것" 절이 원천이고 여기는 근거다.

- **digest는 amd64 매니페스트의 것이다.** index의 digest는 arm64 호스트에서 다른 이미지로 풀린다. 같은 이미지라야 같은
  사진이라는 측정에 기대는 게이트라, 잰 이미지 하나를 가리키는 쪽을 골랐다. arm64 호스트에서 amd64 이미지를 에뮬레이션으로
  돌린 사진이 같은지는 재지 않았다.
- **`threshold: 0`을 더했다.** 명세와 ADR은 `maxDiffPixels: 0`만 적었다. Playwright의 기본 색 차이 기준(0.2)이면 그보다 작은
  차이는 다른 픽셀로 세지 않는다. 같은 이미지의 사진은 바이트까지 같았으므로(프로브) 차이를 하나도 허용하지 않는 쪽이 측정과
  맞고, 러너에서 미세한 차이가 나도 덮지 않고 드러낸다. 프로브도 이 설정으로 16/16 지났다. 아래 변이 표의 "파랑 한 단위"와
  그 대조(기준을 0.2로 돌리면 지난다)가 그 몫을 잰다.
- **스토리는 play와 afterEach가 끝난 뒤 찍는다.** 정적 빌드도 play를 돌린다. Storybook 10.6.1의 렌더 단계는 playing → played
  → completing → completed → afterEach → finished이고(설치본의 preview 런타임 `chunk-M6YZR3ZW.js`를 읽었다), 오류가 나도
  finished로 끝나며 오류 화면을 띄운다. 그래서 `__STORYBOOK_PREVIEW__.currentRender.phase`가 `finished`가 되기를 기다린 뒤
  오류 화면(`body.sb-show-errordisplay`)이 없는지 본다. `completing`의 `waitForAnimations`는 무한 애니메이션을 빼고 기다려
  도는 표시에서 멈추지 않는다(같은 런타임).
- **스토리의 globals가 URL의 globals를 이긴다.** 정답이 없을 때의 첫 실행에서 `atoms-button--primary-dark`의 첫 누락 이름이
  `-dark.png`였다. 라이트를 요청한 차례가 다크로 그려져 찍지 않고 넘어간 것이다. 그래서 요청한 모드와 그려진 `data-mode`가
  다르면 그 차례는 찍지 않고, 찍은 모드가 하나도 없으면 실패한다.
- **실제 입력은 버튼과 아이콘 버튼의 변형 여섯 모두다.** 올림·누름의 클래스가 변형마다 다르다. 올림·누름·포커스마다
  `:hover`·`:active`·`:focus-visible`이 실제로 걸렸는지 먼저 본다. 측정의 첫 실행에서 Tab이 버튼에 오지 않았는데 사진만 보면
  조용히 포커스 없는 사진이 정답이 된다. 항목마다 찍을 상태를 든다. 04의 글 입력은 디자인 파일의 상태 표에 누름이 없다(명세
  축 리뷰가 짚었다).
- **공문의 포커스 스토리 둘은 사진에서 뺀다.** 처음에는 스토리의 globals가 URL을 이겨 공문으로 4장 찍혔다. 명세 축 리뷰가
  ADR 0026 둘째 이력의 "정답 사진은 기본 테마의 라이트와 다크만"과 어긋난다고 짚었다. ADR을 바꾸지 않고, 공문에서 포커스
  링의 값을 재는 그 스토리 둘에 `judgment`를 달고 먹이 아닌 테마로 그려진 스토리가 사진 테스트에 오면 실패하게 했다.
  `judgment`는 사진 비교만 읽는 태그라(afterEach는 `planted`를 본다) 다른 영향은 없다. 그 사진에는 링도 없었다
  (`atoms-button--focus-light.png`를 손으로 봤다). 정적 빌드의 play가 쓰는 `userEvent.tab()`이 Playwright가 연 페이지에서
  `:focus-visible`을 걸지 않은 것으로 본다(어림. 재지 않았다). 실제 키보드 포커스는 실제 입력의 `-focus` 사진이 찍는다.
- **미디어 특성의 기대값.** 같은 빌드에 `data-theme="muk"`과 `data-mode`를 단 요소를 하나 두고 그 `--bg`를 읽는다. 속성을
  지우는 두 사례는 청록에 시스템과 반대 모드를 달아 지우기 전의 값이 기대값과 다른 것도 본다. shadow 사례는 측정처럼 문서의
  시트를 모두 끈 뒤 감싼 요소(`[data-ui-root]`)를 읽는다.
- **설정은 이미지 밖에서 던진다.** "호스트에서 정답을 쓰는 길을 두지 않는다"를 문서가 아니라 설정이 지킨다. 표지는
  `/ms-playwright/.docker-info`다.
- **`visual/`의 tsconfig를 따로 둔다.** 테스트는 node 타입과 DOM 타입이 함께 필요하다. 패키지 tsconfig에 node 타입을 넣으면
  컴포넌트의 프로그램에 `process` 같은 전역이 열린다. 그래서 `visual/tsconfig.json`을 두고 web의 `typecheck`에
  `tsc --noEmit -p packages/ui/visual`을 더했다. ESLint의 프로젝트 서비스는 가장 가까운 tsconfig를 쓴다.
- **하나씩 돈다(`workers: 1`).** 측정과 같은 조건이다. 로컬 비교는 테스트 34개에 약 48초, 정적 빌드에 약 15초였다.

## 확인한 것

- **정답이 없으면 빨갛다.** 정답 사진 없이 `pnpm -C web visual`을 치자 사진 테스트 31개가 모두 "A snapshot doesn't exist at
  …"로 실패했고 미디어 특성 테스트 다섯은 지났다(종료 코드 1).
- **정답 만들기.** `pnpm -C web visual:update`가 36개 통과로 83장을 썼다. `--update-snapshots=changed`가 없는 정답도
  썼다. 주 버튼 라이트의 기본과 올림, 위험 버튼 다크의 포커스, 불러오는 중 다크, 아이콘 열여섯, 포커스 링 스토리를 손으로
  봤다. 한글이 Noto Sans KR로, 올림이 더 진한 강조색으로, 포커스가 바깥 2px의 링으로 그려졌다. 리뷰 반영으로 공문 스토리의
  4장을 지워 79장, 파일 크기의 합 232,189바이트다.
- **같은 사진.** 새 컨테이너로 두 번 비교해 두 번 모두 36개 통과했다(48.9초, 50.0초). 리뷰 반영 뒤에는 34개 통과다. 정적 빌드
  밖으로 나간 요청은 0이었다(픽스처가 실패시킨다).
- **이미지 고정 테스트.** CI 잡을 더하기 전에 "CI 의 visual 잡이 같은 이미지를 잡의 컨테이너로 쓴다"만 빨갰고 더한 뒤
  초록이다.
- **게이트 훅.** 테스트를 먼저 더해 `is_gate("pnpm -C web visual")`이 빨간 것을 본 뒤 정규식을 고쳤다. `tools/run_hooks.py`가
  새 두 사례를 포함해 63건 어긋남 0이었다.

## TDD와 변이

정답이 없을 때 사진 테스트가 빨갛고(위), 이미지 고정의 CI 테스트와 게이트 훅의 테스트도 구현 전에 빨갛게 썼다. 정답이 있는
상태의 사진·미디어 특성·가드는 변이 표 `.scratch/design-system/probes/visual_mutations.toml`(첫 판 16개, 리뷰 뒤 18개)로 빨강을 봤다. visual 러너는
정적 빌드부터 다시 지어 컨테이너에서 도는데, `-g`로 좁힌 실행 하나가 십여 초라 기준선 열넷과 변이 열여섯이 이 기계에서 약
8분이었다(띄운 시각과 로그의 마지막 쓴 시각으로 봤다).

첫 판에서 둘이 초록으로 어긋났다. 둘 다 테스트가 아니라 변이의 기대가 틀렸다.

- **play의 실패는 오류 화면을 띄우지 않는다.** 작은 버튼 스토리의 play 기대값을 33px로 바꿨는데 사진 테스트가 지났다. 정적
  빌드는 play의 실패를 상호작용 패널에 두고 화면은 그대로 그린다. 오류 화면 확인은 그리다 예외가 날 때의 장치라, 변이를
  `render`에서 던지는 것으로 바꾸고 `storybook.ts`의 주석에 이 사실을 적었다. play의 실패는 스토리 테스트(`verify`)가 잡는다.
- **문서 뿌리는 시스템 다크의 두 선택자에 함께 걸린다.** `[data-theme]:not([data-mode])` 하나를 빼도 데코레이터가
  `data-theme`을 단 뿌리는 `:root:not([data-mode])`에 걸려 지났다. 묶음 전체를 시스템 라이트에 거는 변이로 바꿨다.

고친 두 변이와, 셀프 점검으로 바꾼 코드(아래)를 겨누는 넷(shadow 호스트, 이미지 고정 셋)을 다시 돌려 여섯 모두 기대대로
빨갰다. 오류 화면의 빨강은 같은 변이를 손으로 넣어 실패 메시지가 `locator('body.sb-show-errordisplay')`의 `Received: 1`인
것까지 봤다. 표 전체의 원문 확인(`--check`, 16개)도 지났다.

커밋 전 셀프 점검에서 `CODING_STANDARDS.md`의 두 기준에 걸린 자리를 고쳤다. `web/tools/visual.ts`의 `main`이 불리언
인자(`update`)를 받던 것을 `playwright test`의 인자 목록 하나로 바꿨고, shadow 사례의 `read(bare)`가 시트를 끄고 속성을
지우면서 값도 돌려주던 것(명령과 질의)을 끄기·지우기와 읽기로 나눴다.

셀프 리뷰를 반영한 뒤 변이를 둘 더했다. 색 차이 기준을 Playwright 기본값(0.2)으로 돌린 대조(같은 파랑 한 단위가 지나야
한다)와, 공문 포커스 스토리의 `judgment`를 떼면 기본 테마 확인이 빨간 것이다. 코드가 옮겨 가 표 18개 전체를 다시 돌렸고 모두
기대대로였다(대조는 초록, 나머지 열일곱은 빨강).

## 하네스 확인

- **규칙.** 고친 `.claude/rules/web-design.md`를 새 `claude -p` 세션(sonnet, `--setting-sources project,local
  --strict-mcp-config --tools Read`, 워크트리에서)으로 불렀다. 지시문대로 헌법의 거부 플래그(`--disallowed-tools
  'Read(./.claude/**)'`)는 빼고(대기열 131, 다른 세션이 고치는 중) `--output-format stream-json --verbose`로 읽은 파일을 함께
  봤다. 카나리아는 규칙에만 있는 목록 이름 `INTERACTIONS`와 그 파일이다. 패키지의 `IconButton.tsx`를 연 세 번 모두 init의
  `tools`가 `Read` 하나, `mcp_servers`가 0이었고, 읽은 파일은 그 하나였으며 `visual/stories.visual.ts`의 `INTERACTIONS`를
  옮겼다. paths 밖의 `web/package.json`을 연 대조군은 "없음"이었다. 세 번 가운데 둘이 `visual/`이 어느 패키지 아래인지
  규칙에 없다고 짚어 규칙의 두 경로를 `web/packages/ui/visual/…`로 고치고 `media.visual.ts`의 목록 이름 `SPINNERS`를 더했다. 고친
  뒤 같은 질문의 한 번은 `IconButton.tsx` 하나만 읽고 전체 경로와 `SPINNERS`를 옮겼다. 리뷰 반영으로 규칙에 "기본 테마가
  아닌 테마에서 값을 재는 스토리(공문의 포커스 링)도 `judgment`를 단다"를 더한 뒤 그것을 묻는 카나리아도 세 번 모두
  `IconButton.tsx` 하나만 읽고 그 문장을 옮겼고, 같은 질문의 대조군(`web/package.json`)은 "없음"이었다.
- **훅.** `tools/hook_bash_gate_pipe.py`는 `tests/tools/`의 순수 함수 테스트와 `tools/run_hooks.py`의 실제 실행(63건 어긋남 0)으로
  봤다. 워크트리 세션의 훅은 주 체크아웃의 파일이 돌아 이 세션의 Bash 호출로는 바뀐 훅을 확인할 수 없다(`.claude/rules/tools.md`).
- **`CLAUDE.md`.** 매 세션 실려 카나리아를 따로 두지 않았다. 지침 검사가 본다.

## 셀프 리뷰

`/code-review`(base `162ae54`, 바뀐 파일 17, 커밋 0, 미추적 5묶음)를 두 축 나란히 돌렸다. 소스가 든 변경이라 sonnet으로
내리지 않았다. 두 축의 지적은 근거를 보고 모두 받아들였다.

- **명세 축, 고쳤다.** Minor 넷. 공문 포커스 스토리 4장이 ADR 0026의 "기본 테마만"과 어긋났다(위 "공문의 포커스 스토리 둘은
  사진에서 뺀다"). `INTERACTIONS`가 누름을 모든 항목에 강제해 04의 글 입력을 받을 모양이 아니었다(항목마다 상태를 든다).
  앱의 정적 빌드를 "같은 길로 찍는다"고 단정했고 받는 쪽에 넘기지 않았다(티켓에 어림으로 고치고 `plan.md`의 web-widget·
  admin-style 행에 적었다). 변이 표의 "기본 기준이면 지나는 차이"가 대조 없이 측정처럼 적혔다(대조 변이를 더했다). Nit
  셋. `media.visual.ts` 머리의 "스토리 테스트는 브라우저의 미디어 특성을 바꾸지 못하고"는 근거 없는 보편 주장이라 걷었다.
  `operations.md`의 tsc 목록에 `packages/ui/visual`을 더했다. 티켓의 체크박스와 상태는 아래 검사 뒤에 닫는다.
- **표준 축, 고쳤다.** Minor 넷. 변이 표 머리가 형제 워크트리의 일지 02를 인용했다(03). 정답 사진의 "416KB"는 `du`의 할당량이었다
  (파일 크기의 합으로 고쳤다). `CLAUDE.md`의 web 괄호에 `packages/ui`에만 걸리는 정답 갱신 절차를 넣어 규칙과 겹쳤다(명령과
  치는 때만 남겼다). `visual.ts`의 `try` 안에서 경로 변환과 인자 조립을 함께 했다(`containerArgs`와 `buildStorybook`으로 뺐다).
  Nit. 변이 표의 "변이 하나에 1분 남짓"이 실제(십여 초)와 어긋났다. 설정 주석의 "14장"의 출처에 visual_docker가 섞였다.
  "스토리 전부"라는 보편 주장에 모드·테마를 정한 스토리의 반례가 있었다(규칙과 주석에 적었다). smell로 쓰지 않는
  `StoryEntry.title`, 문자열 사전으로 받던 globals(`Globals` 타입과 `muk()`으로), 세 벌의 `--bg` 읽기(하나로), 테스트가 다시 쓴
  패키지 찾기(`locatePackage`를 내보냈다), CI 테스트가 `ci.yml` 어디든 이미지 줄만 보던 것(`visual` 잡의 `container` 아래를
  본다), 이름 `stage`·`OTHER`(`copyPlaywright`·`OPPOSITE`)를 고쳤다.
- **재서 맞은 것(표준 축).** 게이트 열둘의 셈, 잡 넷, 헌법 3.0.16(병합 뒤 3.0.17), 네이티브 파일 0개(`visual_docker/run.mjs`가 센다), 렌더
  단계의 주장, 따옴표 인용, 살아 있는 문서의 잔존 0.

## 검사

- 검증 명령: `uv run pytest -q` 1644 통과(7 deselected), `ruff check`·`ruff format --check`, `pyright`, `lint-imports`,
  `pnpm -C web verify`(22파일 312개) 모두 초록. 사진 비교 `pnpm -C web visual` 초록. 판정 명령은 파이프 없이 돌리고 로그
  파일로 봤다. 커밋의 pre-commit도 모두 지났다(제목 78자로 commit-msg만 한 번 빨갰다).
- **PR [njh6803/agent-os#158](https://github.com/njh6803/agent-os/pull/158)의 CI.** 다섯 잡과 `verify`가 초록이다. `visual` 잡은
  러너가 고정한 digest로 이미지를 받아(27초) `--ipc=host`로 띄우고, 그 안에서 설치하고 Linux로 정적 빌드를 지은 뒤 34개를
  모두 지났다(40.1초). **GitHub 러너의 사진이 이 기계의 컨테이너가 Windows 빌드로 만든 정답과 `threshold: 0`에서 같았다.**
  명세와 ADR 0026이 남겨 둔 측정이 이것으로 닫혔다(명세의 두 자리에 날짜 주석을 달았다).
- **PR 리뷰.** claude-review는 Critical·Major·Minor 없이 Nit 둘이었다. `buildStorybook`이 띄우기 실패를 보지 않는다는 것은
  고쳤다(`run`을 걷고 띄운 결과에서 종료 코드를 읽는 `exitCode` 하나로 두 자리를 처리한다. 불리언 인자를 다시 들이지 않았다).
  정적 빌드가 없으면 질의가 던진다는 것은 리뷰어도 재량이라 했고 원칙 II와 맞아 두었다. CodeRabbit은 첫 커밋에서 두 번 모두
  rate limit이었고 PR 직전 CLI는 `Seat: not assigned`라 돌지 않았다(대기열 136).
- **둘째 푸시(`90ecd09`)의 리뷰.** CodeRabbit이 이번에는 HEAD까지 리뷰해 Minor 셋을 남겼고 근거를 보고 모두 고쳤다. `visual`
  잡의 체크아웃에 `persist-credentials: false`(CWE-522. 같은 모양인 python·web·e2e 잡은 이 PR 밖이라 작업 칩으로 띄웠다).
  route가 디코딩한 경로를 정적 빌드 안으로 묶는다(CWE-22. 인코딩한 `/`는 URL 파서가 접지 않아 `..%2Fpackage.json`이 패키지의
  `package.json`을 냈다. 그것을 묻는 테스트 `storybook.visual.ts`를 먼저 써서 `Received: 200`으로 빨간 것을 본 뒤 고쳤다). 대기열
  136의 문구는 `/security-review`가 보안만 본다는 것에 맞췄다. claude-review의 둘째 코멘트는 Nit 하나라 테마 읽기를
  `renderedMode`와 같은 모양의 `renderedTheme`으로 맞췄다. 사진 비교는 35개 통과다.

## 회고

후보 넷을 냈고 넷 모두 승인됐다. 이 PR에서는 반영하지 않았다. 앞의 둘은 새 행으로 적었고, 뒤의 둘은 회차를 더하려다 병합
직전에 main을 받아 보니 같은 날 PR #157(`chore/canary-procedure-and-runner`)이 122·129를 닫았다. 이 세션의 두 사건은 #157이
들기 전의 기준(`162ae54`)에서 났으므로 닫힌 행에 회차를 더하지 않고 main의 행을 그대로 받았다.

> 사용자(질문에 답): "1 tidy-checkouts 판정 2,2 보안 축 대체,3 가드 거부 (122),4 카나리아 스크립트 (129)"

1. **`tidy-checkouts`가 `.git` 없는 워크트리 폴더의 상태를 루트의 것으로 읽는다 → 대기열 135(새 행, 1회차).** 이 세션의
   첫 정리에서 `05-admin-hides-decision-for-end-user`(`prunable`)의 `git -C <경로> status`가 루트 저장소에 닿았다. 무시된 목록에
   `.env`와 `.claude/worktrees/`가 보여서 알아챘다. 스킬은 이 확인을 자기 자리(1단계의 `--show-prefix`)에서만 한다.
2. **보안·버그 축 리뷰가 두 PR 연속 없었다 → 대기열 136(새 행, 2회차).** PR #156과 이 PR이다. CodeRabbit은 rate limit, CLI는
   좌석이 없다. 좌석이 없을 때 내장 `/security-review`를 PR 직전에 대신 돌리는 처방이고, 리뷰 파이프라인을 바꾸므로 ADR 이력이
   필요할 수 있다.
3. **워크트리 가드가 `.github` 경로, 변수로 계산한 인자, heredoc을 거부했다 → 대기열 122(#157이 닫았다).** `prettier …
   ../.github/workflows/ci.yml`이 "git을 부른다"로, `node $C/…`가 계산한 인자로 거부됐다. 파일 도구(Write)로 쓰고 경로를 글자
   그대로 주어 돌았다. #157의 `CLAUDE.md` 가드 문장(변수 대신 절대 경로, 긴 입력은 파일로)이 이 모양을 덮는다.
4. **카나리아 스크립트를 또 스크래치에 새로 썼다 → 대기열 129(#157이 `tools/canary.py`로 닫았다).** 실행기 셋과 stream-json
   요약기 하나다. 다음 세션부터는 그 러너를 쓴다.

일지에만 남기는 것:

- 변이의 기대 둘이 틀렸다(정적 빌드의 play 실패가 오류 화면을 띄운다고 봤고, 문서 뿌리가 시스템 다크의 선택자 하나에만 걸린다고
  봤다). 변이 도구가 초록으로 어긋남을 알려 잡혔다.
- 재지 않은 시간("약 40분")을 먼저 적었다가 로그의 시각으로 8분임을 보고 고쳤다. 리뷰도 "416KB"(`du`의 할당량)와 "변이 하나에
  1분 남짓"을 잡았다. 리뷰 브리프의 근거 항목이 동작했다.
- ADR 0026의 "정답 사진은 기본 테마만"을 구현 때 놓쳐 공문 사진 4장을 만들었고 명세 축이 잡았다.
- 도구 호출 사이의 문장을 영어로 쓴 것을 훅이 세 번 짚었다.
- 첫 `tidy-checkouts`의 판정과 삭제를 스크래치 스크립트로 새로 지었다. #157이 연 대기열 132와 같은 모양이다(묻지 않아 회차를
  더하지 않았다).

## 다음

- **PR #158의 병합.** 워크트리에서 열었으니 next-session의 "워크트리에서 병합할 때"를 따른다. 나란히 돌던 PR #157이 먼저
  병합돼 헌법 3.0.16을 가져갔다. origin/main을 이 브랜치에 병합하며 이 브랜치의 항목을 3.0.17로 고쳤고, 대기열은 #157의
  132~134 뒤에 이 브랜치의 135·136을 두었다. 병합 직전에 #159가 또 들어와(헌법은 그대로 3.0.16, 대기열 137) 한 번 더
  병합하고 대기열을 번호 순서대로 135·136·137로 두었다. 그 CI가 끝난 뒤 #160(pre-commit 검사 러너)이 또 들어왔다. #160은
  이 브랜치의 3.0.17을 비워 두고 3.0.18로 올렸으므로 이 브랜치의 항목을 3.0.18과 3.0.16 사이에 두었고, 게이트 훅의 목록에는
  #160의 `tools/run_checks.py`와 이 브랜치의 사진 비교를 함께 두었다. `operations.md` 9행과 클론 문단은 main의 줄에 이 브랜치의
  문장을 다시 얹었다. 마지막 커밋(`90ecd09..cb724f2`, CodeRabbit의 지적 셋과 Nit 하나의
  반영)은 CodeRabbit이 rate limit으로 보지 못했고 claude-review는 지적 없음이었다.
- **design-system의 다음은 티켓 03과 04다.** 둘 다 01·02 뒤라 나란히 연다. 자기 컴포넌트의 정답 사진은 `pnpm -C web visual:update`로
  만들고, 실제 입력과 움직임 줄이기의 자리와 공문에서 재는 스토리의 태그는 `.claude/rules/web-design.md`에 있다.
- **첫 정리가 멈춘 자리.** 이 세션의 `tidy-checkouts`가 `mutate-any-runner`의 `git worktree remove` 실패("Invalid argument")에서
  멈췄다. 그 폴더는 등록 없이 남았고, 판정을 지난 워크트리 아홉과 등록 없는 폴더 넷, `05-admin-hides-decision-for-end-user`의
  반쯤 지워진 폴더가 남았다. 다음 정리가 다시 보고, 등록 없는 폴더는 사람에게 넘긴다.
