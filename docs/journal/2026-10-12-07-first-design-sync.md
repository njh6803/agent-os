# 2026-10-12 (07) 저장소의 첫 /design-sync

next-session 지시문으로 연 admin-style 명세 세션(`docs/admin-style-spec`)이 선행 조건을 묻는 사이 사용자가 `/design-sync`를
쳤다. 명세의 전제인 그리기(화면 프롬프트의 하는 법 1~5)가 이 동기화를 기다리므로 같은 세션에서 돌았다. 결과는 명세 브랜치가
아니라 같은 워크트리에서 `origin/main`(`8fcc2a7`)으로부터 딴 `chore/first-design-sync`에 싣고 먼저 병합한다. 명세는 이 PR이
병합된 뒤 `docs/admin-style-spec`에서 이어 간다. 셀프 리뷰 뒤 `origin/main`(`02b21d0`)을 들였다(fast-forward). 순번은 07이다.
03이 비었지만 main의 04~06보다 앞서면 이 일지가 최신 파일로 읽히지 않는다.

## 계기

> 사용자: "이 세션에서 /design-sync 진행해도 돼?"

> 사용자(질문에 답): "별도 chore 브랜치로 먼저 병합 (Recommended)"

결과(`.design-sync/`의 config)에는 Claude Design 프로젝트의 ID가 든다. 다음 동기화가 같은 프로젝트를 고치게 하는 기록이다. 명세
브랜치에 실으면 그림과 명세가 끝날 때까지 main에 없어, 나란히 도는 web-widget이 동기화하면 프로젝트가 둘로 갈린다. 그래서
따로 먼저 병합한다.

> 사용자(질문에 답): "전부 고충실도로 (Recommended)"

> 사용자: "/design-login을 실행했어"

> 사용자(질문에 답): "Agent OS 디자인 시스템 (Recommended)"

> 사용자(질문에 답): "@theme static으로 전부 내보내기 (Recommended)"

## 첫 턴의 tidy-checkouts

- **루트.** main이고 깨끗했다. `7a9e58f`에서 `8fcc2a7`(#177)로 당겼다. 스킬 파일은 바뀌지 않았다.
- **종료 1로 남은 것.** `review-workflow-guards`(WinError 32)와 `spec-pipeline-and-pytest-ids`(`.venv`의 `.pyd`, WinError 5).
  일지 2026-10-12-04와 같은 둘이다.
- **사람에게 넘긴 것.** prunable `05-admin-hides-decision-for-end-user`, PR 머리가 다른 `skill-check-and-retro-section`, 분리 HEAD
  넷, 등록 없는 폴더 여섯. 지시문대로 답을 기다리지 않았다.

## 동기화

Claude Code 2.1.286의 번들 스킬이다. 패키지에 `.storybook/main.ts`가 있어 storybook 모양으로 돌았다. 처음 만든 디자인 시스템
프로젝트 "Agent OS 디자인 시스템"에 아홉 컴포넌트(Button, Card, Icon, IconButton, Progress, StatusBadge, Alert, Switch, TextField)를
올렸다. 처음에는 `DesignSync`가 권한 없음으로 거부했다. 도구의 문구는 "/design-login cannot run in this non-interactive session"이었고
사람에게 그 기계의 대화형 세션에서 한 번 치라고 했다. 사용자가 대화형 터미널에서 `/design-login`을 친 뒤 지나갔다.

변환기가 받지 못한 것은 다섯이었고, 패키지 소스가 아니라 `.design-sync/`의 설정과 포크로 맞춘 것이 셋이다. 고친 순서대로다.

- **lucide 서브패스.** 번들이 `lucide-react/dist/esm/icons/<이름>`을 풀지 못했다. 1.51.0에 exports 맵이 없고 파일이 `.mjs`인데
  esbuild의 기본 확장자에 `.mjs`가 없다. `cfg.tsconfig`로 그 경로만 매핑한 `.design-sync/esbuild-paths.json`을 주었다. 변환기의
  paths 플러그인이 `.mjs`까지 붙여 찾는다(`lib/bundle.mjs`를 읽었다). ADR 0024의 import 모양은 그대로다.
- **공개 export 0개.** `exports`가 `src/index.ts`를 가리키고 `types`가 없어 ts-morph가 `index.d.ts`를 찾지 못했다. 변환기는
  디스크에 있으면 `publishConfig.types`를 `types`보다 먼저 본다(`lib/dts.mjs`를 읽었다). 패키지 `package.json`에
  `publishConfig.types: ./dist/index.d.ts`를 더했다. 저장소에서 그 필드를 읽는 것은 변환기뿐이다(grep).
- **스토리의 상수.** Card·Icon·StatusBadge 미리보기가 `.map` of undefined로 깨졌다. 스토리가 컴포넌트 모듈에서 함께 import하는
  상수 넷은 진입점이 내보내지 않는데, 변환기는 컴포넌트 모듈의 import를 번들 전역으로 돌린다. `.design-sync/story-constants.js`가
  `dist`에서 다시 내보내고 `cfg.extraEntries`가 전역에 합친다. 같은 `dist` 파일이라 컴포넌트가 두 벌이 되지 않는다.
- **스토리의 globals.** 다크·공문 스토리 열넷이 라이트·먹으로 그려졌다. 변환기의 `compose`가 `ctx.globals`를 비우고, 테마를
  거는 프로젝트 데코레이터는 `.storybook/preview.tsx`가 `...storyPreview(css)`로 펼쳐 내보내 실리지 않는다. 실려도 그 길은
  `initialGlobals`만 넘긴다(`lib/source-storybook.mjs`를 읽었다). 스킬이 허용하는 포크 지점 `preview-gen-storybook.mjs`를
  `.design-sync/overrides/`에 복사해, 스토리의 globals를 `data-theme`/`data-mode`를 단 감싸는 div로 옮겼다(`cfg.libOverrides`).
- **쓰이지 않은 토큰.** 올린 CSS에 `--text-title`, `--spacing-8`, `--radius-s`가 없었다. 아래 "패키지" 절이다.

글꼴은 걱정과 달랐다. 변환기는 `build`가 낸 `dist/theme.css`를 쓰지 않는다. 고르는 CSS는 JS가 import한 CSS, `cfg.cssEntry`,
`dist/styles.css` 같은 정해진 이름뿐이라(`package-build.mjs`를 읽었다) 그 어느 것도 없어 참조 Storybook의 컴파일된 CSS로
대신했고(`[CSS_FROM_STORYBOOK]`), 그 안의 글꼴 파일을 옮겼다. 테마 다섯의 글꼴 파일(woff2 390개, woff 382개)과
`fonts/fonts.css`가 올라갔고 `[FONT_MISSING]`이 없었다. 비교 사진에서도 Noto Sans KR로 그려졌다. 그래서 `plan.md`가 조건으로 둔
패키지 `build` 고치기는 하지 않았다.

### 채점

스토리 78개 가운데 컴포넌트 아홉의 69개를 Storybook 참조 화면과 미리보기 화면의 쌍으로 하나씩 봤다. `디자인 토큰/*` 스토리
아홉은 컴포넌트가 아니라 `cfg.titleMap`에서 뺐다. 아홉 모두 `match` 또는 `close`이고 `mismatch`는 없다. `match`가 55개,
`close`가 14개다.

- 13개는 Storybook만 `play` 함수(클릭, Tab, 입력)를 돌려 포커스 링이나 넣은 글자가 남은 스토리다. 미리보기는 `play`를 돌리지
  않는다. 정적 모양은 같다. 미리보기에서 포커스를 흉내 내면 카드 전체가 포커스 상태로 보여 고치지 않았다.
- 1개는 Card의 320px 스토리다. 본문의 줄바꿈 자리가 한 글자 다르다. 글꼴·크기·폭은 같다.

마지막 driver 실행(`resync.mjs`, 원격 기준 없음)은 `ok: true`, 채점 대기 0, 아홉 모두 carried forward였다. 렌더 검사는 9/9 깨끗했다.

### 올리기

빈 프로젝트라 확인을 마친 묶음을 차례로 올렸다. 첫 묶음(Button·Alert·Icon·TextField)에 공유 파일과 `fonts/`의 773개(글꼴
파일 772개와 `fonts.css`)를, 둘째 묶음에 나머지 다섯과 다시 지은 공유 파일을 실었다. 마무리에서 글꼴 파일을 뺀 54개를 다시
올렸다. 글꼴 파일은 이름에 내용 해시가 붙어 있고 첫 묶음 뒤로 이름이 하나도 바뀌지 않아(이름 대조로 추가 0·누락 0) 다시
올리지 않았다. 원격 목록을 이번 빌드와 대조해 지울 것이 없었고, 표지(`_ds_needs_recompile`)를 다시 올린 뒤 `_ds_sync.json`을
마지막으로 올렸다. `report_validate`는 9개 가운데 bad 0이다. 셀프 리뷰가 사용 규약을 고쳐 README가 바뀌었으므로 같은 차례로
글꼴 파일을 뺀 54개와 `_ds_sync.json`을 다시 올렸다(아래 셀프 리뷰 절).

### 사용 규약

`.design-sync/conventions.md`를 써서 `cfg.readmeHeader`로 README 앞에 붙였다. 디자인 에이전트가 읽는다. 컴포넌트는 `className`과
`style`을 받지 않아 에이전트의 배치는 번들 CSS에 이미 있는 클래스와 `var(--…)`로만 짓는다. 그래서 배치에 쓸 클래스와 변수를
글자 그대로 나열했다. 번들 CSS에는 컴포넌트가 안에서 쓰는 클래스도 있지만(목록 밖 96개) 배치용으로 보장하지 않는다. 적은
이름은 모두 빌드에 있고, CSS가 없다고 든 이름(`text-base`, `p-6`, `gap-8`, `rounded-s`, `dark:`)은 정말 없다. 판정은
`.design-sync/check-conventions.mjs`다(아래 회고 절).

## 패키지

> 사용자(질문에 답): "@theme static으로 전부 내보내기 (Recommended)"

Tailwind v4는 `@theme`의 토큰 가운데 소스가 쓴 것만 CSS 변수로 낸다. 그래서 디자인 에이전트가 제목 글자와 넓은 여백을
`var(--…)`로 적을 수 없었다. 원칙 II대로 판정 스토리 `ThemeTokensEmitted`를 먼저 썼다. 디자인 토큰 CSS의 소스(`?raw`)에서
inline이 아닌 `@theme` 블록의 토큰 이름을 읽어 모두 문서 뿌리에서 풀리는지 본다. 빨강이었다(넷이 풀리지 않았다). `theme.css`의
`@theme`을 `@theme static`으로 바꾸자 초록이 됐다. `?raw`의 타입 선언을 `.storybook/css-inline.d.ts`에 더했다. `@theme inline`의
별칭(`--color-*`, `--shadow-*` 등)은 그대로 변수로 나오지 않는다. 결정은 ADR 0026의 둘째 2026-10-12 이력 "디자인 토큰은 쓰이지
않아도 모두 CSS 변수로 낸다"에 적었다.

로컬 사진 비교(`pnpm -C web visual`)는 Docker 데몬이 꺼져 있어 돌리지 못했다. 표준 축 리뷰어가 Tailwind CLI로 두 판을 컴파일해
보니 차이는 그 변수 네 줄뿐이었다. 새 스토리는 `judgment`라 사진을 찍지 않는다. CI의 `visual` 잡이 판정한다.

## 고친 문서

- `.scratch/plan.md`: web-widget·admin-style 행에서 첫 `/design-sync`의 그림이 시스템 글꼴이면 `build`를 고친다는 조건을 결과로
  바꿨다.
- `.scratch/admin-style/design/screens-prompt.md`: 하는 법 1의 조건부 절차를 결과와 고를 디자인 시스템의 이름으로 바꿨다.
- ADR 0026에 같은 날의 이력이 둘이 되어, 날짜만으로 가리키던 인용(`plan.md`, `tech.md`, 화면 프롬프트)을 "첫째·둘째 2026-10-12
  이력"으로 좁혔다. `tech.md`가 바뀌어 헌법을 3.0.24로 올렸다. 본문의 두 문장(`build`는 `/design-sync`만 쓴다, CSS를 그대로
  복사한다)에 포인터를 달았다.
- `.gitignore`: `/design-sync`의 산출물과 검증 상태(`.ds-sync/`, `ds-bundle/`, `.design-sync/` 아래 셋). `README.md`의 트리에
  `.design-sync/`를 더했다.
- 회고가 고친 것: `docs/agents/issue-tracker.md` 화면 디자인 절, `.design-sync/check-conventions.mjs`, `.scratch/retro-queue.md`의
  177(아래 회고 절).

## 잔존 grep

"첫 `/design-sync`", "시스템 글꼴이면", "글꼴을 `dist/`에 싣", "`build`를 고치"를 md·py·ts·tsx·mjs·toml·json·yml에서 찾았다. 살아
있는 문서의 옛 서술은 `plan.md` 두 행과 화면 프롬프트였고 결과로 바꿨다. 나머지는 일지, done인 design-system 명세, ADR 0026의
지난 이력이라 기록이다. "0026의 2026-10-12 이력"은 헌법 README의 3.0.22 문장(버전 이력, 기록)과 일지 2026-10-12-01만 남았다.

## 셀프 리뷰

`/code-review`(기준 `8fcc2a7`, 수정 10·미추적 8, 커밋 0). 파이썬 소스가 없어 표준 축은 sonnet이다. 명세는 이 세션의 결정을
요구와 리뷰어 참고로 갈라 넘겼다. Critical은 없었다. 표준 축은 반증된 주장 여섯과 문서 일관성 여덟, smell 넷, 명세 축은 Major
셋과 Minor 하나, 틀린 주장 여덟을 냈다. 두 축이 겹친 것이 많았다.

- **고친 것.**
  - 대기열 182가 main의 177(쥔 프로세스의 이름, 3회차)과 같은 처방이었다. 182를 걷고 177에 4회차를 더했다. main을 들이며
    알았다.
  - 같은 날의 이력이 둘이라 날짜만의 인용이 모호했고, ADR 본문 두 문장이 새 이력으로 범위가 바뀌었는데 포인터가 없었다.
  - 변환기가 CSS를 고르는 조건을 `dist/`에 컴파일한 CSS를 따로 내면 고른다고 잘못 적었다(ADR, NOTES). 정해진 이름만 본다.
  - 쓰이지 않아도 모두 CSS 변수로 낸다는 결정이 `@theme inline`의 별칭에서 깨졌다. 결정과 주석을 inline이 아닌 블록으로 좁혔다.
  - 앱도 `var(--text-title)`을 읽지 못했다는 주석은 재지 않은 것이었다. 앱은 자기 `@source`로 컴파일한다. 지웠다.
  - 앱의 스토리는 올라가지 않는다는 어림이 맞았다고 적었는데, 그 어림은 시험된 적이 없다. 앱의 Storybook이 아직 없다. 시험되지
    않았다고 고쳤다.
  - ADR의 "같은 실행이 쟀다"는 커밋한 프로브가 없다. 손으로 보고 코드를 읽었다고 고쳤다. issue-tracker의 `/design-login` 줄도
    한 번 손으로 본 것으로 좁히고, 도구의 문구를 위 동기화 절에 적었다.
  - 일지의 수(72·16·15)는 69·14·13이었고, `@font-face` 392개는 `fonts.css`의 수라 글꼴 파일 수로 고쳤다.
  - 사용 규약의 "목록에 없는 클래스는 CSS가 없다"는 거짓이었다(목록 밖 96개). 배치에는 목록의 것만 쓴다는 문장으로 바꿨다.
    "원색 변수"는 용어집의 "원색 토큰"으로 고쳤다. 그래서 README를 다시 지어 Claude Design에 다시 올렸다.
  - 검사기가 `--text-<이름>--line-height`에서 가짜 `--line-height`를 뽑고 다른 변수의 일부로 통과시켰고, `.flex`를 `.flex-col`로
    통과시켰다. 자리 표시를 걷고 이름의 경계를 보게 했다. 변이 셋(`--line-height`, `flex-co`, 없다는 목록의 `flex`)을 잡는 것을
    보고 되돌렸다.
  - 그 밖에 `.gitignore` 주석(커밋하는 파일이 더 있다), README 트리의 `.design-sync/`, 판정 스토리 머리의 판정 목록, 포크 머리의
    import 경로와 `DEFAULT_THEME` 중복, 이 일지의 "다음"이 회고를 명세 PR로 미룬다고 적은 것.
  - 포크의 머리 주석을 고치자 다음 driver 실행이 아홉 컴포넌트의 채점을 모두 지웠다("contract changed"). 스킬은 포크 편집을
    채점 계약에 넣는다고 적었는데 주석이라 괜찮다고 보고 놓쳤다. 69개를 `--max-stories 12`로 다시 캡처해 쌍 사진을 모두 다시
    보고 같은 판정으로 다시 적었다. driver를 다시 돌리자 아홉 모두 carried forward, 지워진 채점 0이었다. NOTES의 위험 절에 적었다.
- **남긴 것.**
  - 검사기에 회귀 테스트가 없다. 저장소의 테스트는 파이썬과 web 워크스페이스에 있고, 이 스크립트는 둘 밖의 node 스크립트라
    부르려면 픽스처 빌드가 필요하다. 변이 일곱을 이 세션에서 손으로 봤다. 다시 동기화할 때 규약을 고치면 같은 변이를 다시 본다.
  - `.claude/rules/web-design.md`의 "판정하는 것"에 새 판정 스토리를 더하지 않았다. 그 문단은 무엇을 판정하는지의 개요이고, 규칙을
    바꾸면 카나리아로 다시 불러 봐야 한다(작업 규약 3). 판정 스토리 머리의 목록에는 더했다.
  - `css-inline.d.ts`가 이제 `?raw`도 선언해 이름이 좁다. 프로브와 진입점 스토리 주석이 그 이름을 가리키고, 머리 주석이 두
    쿼리를 모두 적는다.
  - 판정 스토리의 음성 사례(`planted`)는 두지 않았다. `static`이 없는 CSS를 같은 Storybook에 함께 실을 길이 없다. 빨강은 바꾸기
    전의 실행에서 봤다.
  - 같은 사실(`publishConfig`, 글꼴)이 ADR 이력, NOTES, 이 일지에 있다. ADR은 결정의 근거, NOTES는 다음 동기화의 작업 메모, 일지는
    기록이라 읽는 쪽이 다르다.

반영한 ADR 초안을 보이고 승인을 받았다.

> 사용자(질문에 답): "승인, 커밋·PR·병합 (Recommended)"

## PR 직전 리뷰

CodeRabbit CLI는 `coderabbit auth status`가 `Seat: not assigned`라 돌지 못해, 커밋(`cbac132`) 뒤에 대체 둘을 돌렸다.
`/security-review`는 후보가 없었다(검사기는 정해진 로컬 파일만 읽고 셸·네트워크가 없다, 포크의 감싸는 div는 React가 속성을
이스케이프한다, `projectId`는 UUID다). `bug-perf-review`는 턴 한도(60)에서 보고 없이 멈춰 이어 붙여 받았다(대기열 169와 같은
증상). 유효 다섯(Minor 셋, Nit 둘), 오탐 셋(`@theme static`이 앱에 주는 영향, 감싸는 div가 다른 칸에 새는 것, `publishConfig`가
pnpm·TypeScript에 주는 영향)이었다.

- **고친 것.**
  - 검사기의 `.d.ts` 판정이 `endsWith`라 `IconButton.d.ts`로 `Button`이 통과했다. 파일 이름을 통째로 비교한다. 번들에 있다는
    판정이 번들 전체의 낱말이라 내보내지 않은 내부 이름(`var GLYPHS`)도 통과했다. 내보내기 블록의 이름만 본다. 변이 둘
    (`AgentOsUi.GLYPHS`, `Button.d.ts`를 치운 빌드)을 잡는 것을 보고 되돌렸다.
  - 포크 파일이 작업 트리에서 CRLF였다. 스킬 폴더에서 `cp`로 만든 사본의 줄바꿈이 그대로 남았고, git은 LF로 커밋했지만 채점
    계약은 작업 트리의 CRLF 바이트로 찍혔다. LF로 맞추고 driver를 돌리자 아홉 컴포넌트의 채점이 지워져 그 추정이 맞았다. 다시
    캡처한 69쌍을 모두 다시 보고 같은 판정으로 되돌린 뒤 driver가 아홉 모두 carried forward였다. 글꼴 파일을 뺀 54개와
    `_ds_sync.json`을 다시 올렸다. 지금 고치지 않았으면 병합 뒤 LF로 받은 체크아웃(web-widget의 재동기화)이 같은 재채점을 했을
    것이다. NOTES의 위험 절에 적었다.
- **남긴 것.** 검사기와 판정 스토리 파서의 잠재 지점(빈 묶음의 통과, 이스케이프 집합, 줄바꿈 위치에 기대는 건너뛰기, 한 줄에
  선언 둘, 같은 줄의 블록 머리 등)은 오늘 규약과 `theme.css` 모양에서 틀리지 않는다. 모양을 바꿀 때 변이로 다시 본다.

## 검사

- 검증 명령: `uv run pytest -q`, `ruff check`·`ruff format --check`, `pyright`, `lint-imports`, `pnpm -C web verify`가 모두 초록이다.
  `verify`는 처음에 Prettier가 새 스토리의 서식을 짚어 빨강이었고, `prettier --write` 뒤 초록이다. 셀프 리뷰를 반영하고 main을
  들인 뒤 모두 다시 돌렸다.
- `node .design-sync/check-conventions.mjs`: 클래스 50, 변수 44, 내보내기 6이 모두 빌드에 있다.
- 마지막 검증 명령: pytest 1982 통과(7 deselected), web verify 28파일 357개.
- 헌법은 처음에 3.0.23으로 썼다가 커밋 직전의 `tools/sibling_overlap.py`가 형제 워크트리 `run-summary-and-lock-holder`의 같은
  판을 알려 3.0.24로 옮겼다.

## 회고

후보 다섯을 냈고 다섯 모두 사용자가 고른 대로 갔다(셋은 이 PR에서 반영, 하나는 대기열, 하나는 일지에만).

> 사용자(질문에 답): "1·2·3 이 PR에서 반영 (Recommended),4 대기열에 적기 (Recommended),5 일지에만 남기기 (Recommended)"

- **`/design-sync`의 결과를 `chore/` PR로 먼저 병합한다.** 이번에는 대화로 정했고 규약에 없었다. 이 PR에서
  `docs/agents/issue-tracker.md` 화면 디자인 절에 적었다. 화면 `README.md` 표의 동기화한 커밋이 그 PR의 병합 커밋이라는 것도 함께
  적었다.
- **처음이면 대화형 터미널에서 `/design-login`.** 업로드 도구가 권한 없음으로 거부한 뒤에야 사람에게 부탁해 한 번 오갔다. 같은
  절에 적었다.
- **사용 규약의 이름 검증을 스크립트로.** 스크래치의 일회용 스크립트로 확인했는데, 스킬은 다시 동기화할 때마다 이 검증을
  요구한다. `.design-sync/check-conventions.mjs`로 커밋했다. 규약에 틀린 이름 넷(없는 클래스, 없다고 적은 클래스, 없는 변수,
  없는 컴포넌트)을 섞어 넣자 넷 다 잡고 종료 1이었고, 되돌리자 0이었다. 셀프 리뷰가 짚은 약한 판정을 고친 뒤 변이 셋을 더 봤다.
- **tidy-checkouts가 같은 워크트리 둘을 되풀이해 남긴다.** 새 행으로 적었다가 main의 177이 같은 처방이라 177에 4회차로 더했다.
- **일지에만.** 첫 업로드에서 글꼴 파일 772개(woff2 390개, woff 382개)를 파일 목록으로 넘기느라 업로드 호출의 대부분을 썼다.
  다시 동기화할 때는 driver의 차이가 바뀐 파일만 올리므로 한 번만 드는 비용이다. 반복문으로 묶은 `node -e` 명령 하나를 워크트리
  가드가 거부해 파일로 써서 다시 쳤다. `CLAUDE.md` 환경 함정에 이미 있는 규칙(명령은 하나씩)이고 처음 어긴 것이라 후보로 내지
  않았다.

## 다음

- 이 PR이 병합되면 같은 세션이 `docs/admin-style-spec`으로 돌아가 `origin/main`을 들인다. 그다음은 사람이 그 프롬프트의 하는 법
  2~5(Wireframe으로 안을 고르고 UI mockups로 완성)를 마치고 Claude Design 프로젝트의 링크를 이 세션에 주는 것이다. 디자인
  시스템은 "Agent OS 디자인 시스템"을 고른다.
- web-widget이 그리기 전에 `/design-sync`를 다시 돌면 `.design-sync/config.json`의 `projectId`가 같은 프로젝트를 가리킨다. 바뀐
  것만 다시 확인한다.
