# 2026-11-13 (21:49) answer-markdown 티켓 02: 마크다운 부품이 출력을 다듬는다

세션 제목 `feature/02-markdown-citations-sources-and-stars`. 브랜치 `feature/02-markdown-citations-sources-and-stars`, 워크트리 `.claude/worktrees/confident-wright-2d3ebf`, 기준 커밋 `0e06c9cf7`(origin/dev). 모델 Opus 5.5. 다른 세션(`local_bcac6d8c-…`)이 연 곁 세션이고, U+FFFD 고침 세션(`ds-upload-fffd`)과 나란히 돌았다. 파일 이름의 시각은 명세에 d49의 조건을 더하며 이 일지를 가리킨 때다. 컨텍스트 압축을 한 번 지났다.

## 사용자 프롬프트

원문은 세션 기록(`C:\Users\User\.claude\projects\C--project-agent--claude-worktrees-confident-wright-2d3ebf\fc795862-afb4-47bd-9d91-fe98c4d326b4.jsonl`)의 첫 메시지다. 연 쪽은 사람이 아니라 다른 세션이고, 아래는 그 메시지에서 앱이 붙인 알림을 뺀 것이다.

> 사용자: Background (from the session that started this one):
> Agent OS 저장소(`C:\project\agent`, 기준 브랜치 `dev`)의 기능 answer-markdown은 모델이 지은 답을 마크다운으로 그리는 공유 부품을 디자인 시스템(`web/packages/ui`)에 세우고 위젯에 적용하는 기능이다. 티켓 01(공유 마크다운 부품)은 done이고, 02가 부품의 출력 다듬기, 03이 위젯 적용이며 03은 02를 기다린다. 2026-11-13 기준으로 02를 맡은 세션이나 워크트리는 없다. 사용자가 이 일과 디자인 시스템 올리기 도구의 U+FFFD 고침을 나란히 돌리기로 했다. 같은 시각에 도는 다른 일(local-model 03, release-image 명세, 위젯 로그인 상태 설계 인터뷰, U+FFFD 고침)은 `web/packages/ui`를 건드리지 않는다. 디자인 시스템 아티팩트에 올리는 것은 이 티켓의 일이 아니고 병합 뒤 `/sync-design-system 올리기`가 한다. 그 올리기는 지금 U+FFFD 문제(`.scratch/retro-queue/ds-upload-replacement-char-rejected.md`)로 거부되므로, 그 고침이 먼저 병합됐는지 보고 올린다.
>
> Task:
> 티켓 `.scratch/answer-markdown/issues/02-markdown-citations-sources-and-stars.md`(상태 `ready-for-agent`)를 구현한다.
>
> 시작하기 전에:
> - `CLAUDE.md` 작업 규약과 `docs/agents/issue-tracker.md`대로 티켓 상태를 `in-progress`로 바꾸고, 브랜치 이름을 `feature/02-markdown-citations-sources-and-stars`로 맞추며, 세션 제목을 그 브랜치로 바꾼다.
> - 명세 `.scratch/answer-markdown/spec.md`, 기능 계획 `.scratch/answer-markdown/plan.md`, ADR 0053(2026-11-10, 2026-11-11 이력 포함), 앞 티켓 01과 그 일지를 읽는다.
>
> 고칠 자리: `web/packages/ui`의 마크다운 부품(변환의 차례 2·3·5·6, 위첨자와 출처 덩이의 클래스, `MarkdownText`), 디자인 토큰 CSS의 "부품 치수" 묶음에 더하는 `cite-start`, `.claude/rules/web-design.md`의 부품 치수 목록, 사례 파일과 단위 시험, 스토리. 위젯 앱(`web/apps/widget`)은 건드리지 않는다. 위젯에 적용하는 것은 티켓 03의 일이다.
>
> 끝난 모습:
> - 티켓의 체크리스트가 모두 채워진다.
> - `CLAUDE.md`의 검증 명령이 초록이고, `packages/ui`를 건드렸으므로 Docker로 `pnpm -C web visual`, `pnpm -C web visual:widget`, `pnpm -C web visual:admin` 셋을 친다.
> - 사람이 사진을 화면 파일(`mk-cite-320`, `mk-cite-400`, `mk-side-320`)과 견준 결과와 번호 2,000·4,000·8,000개를 그리는 데 걸린 시간을 PR 본문에 적는다.
> - `/code-review` 셀프 리뷰를 반영한 뒤 PR을 열고, 규약대로 병합까지 한 뒤 `next-session`으로 지시문을 낸다.
>
> Shared notes folder for this group of sessions (outside the repo; read siblings' notes there, leave hand-over notes or large findings there instead of pasting them into messages): C:\Users\User\AppData\Roaming\Claude\side-session-notes\local_bcac6d8c-7fb8-459e-9df0-4092dca2dbe6

## 한 일

- 변환: 차례 2(`unclosed-emphasis.ts`), 3(`literal-marks.ts`), 5(`sources.ts`), 6(`citations.ts`)을 새 모듈로 세우고, `plugin.ts`가 1부터 8까지를 명세의 차례로 부른다. 위첨자는 `emphasis`에 `hName: "sup"`을, 출처 덩이는 `blockquote`에 `hName: "div"`를 달아 내고, 표지는 `data.hProperties`(`data-cite`, `data-sources`)에 둔다. 허용 목록에 `sup`과 `div`를 더하되 `allowElement`가 표지 달린 것만 들인다.
- 부품: `Cite`(왼쪽 틈 `ml-cite-start`, 이어진 번호는 `ml-1`, `text-small leading-0 text-text-muted`)와 `SourcesBlock`(위 선, `pt-3`, 블록 사이 `gap-1`, 놓인 자리 `sources`)을 더했다. 출처 덩이 안의 목록은 항목 사이 틈이 없고 제목은 덩이의 글자 크기와 색을 물려받는다. `MarkdownText`는 위첨자 앞에 공백을 두고 출처 덩이를 감싸지 않은 채 글을 낸다.
- 토큰: `--spacing-cite-start: 2px`를 부품 치수 묶음에, 그 이름을 `web-design.md`의 치수 목록에 더했다.
- 사례 파일: `emphasis.ts`(CJK 34, LITERAL 60), `cite.ts`(CITE 48, 경계 입력 13), `sources.ts`(SOURCES 32), `combined.ts`(COMBINED 17), 변환의 차례(INTERPLAY 11). 목표가 없는 입력은 지금의 결과를 `pinned`로 고정했고, 고정하기 전에 명세의 문장과 맞는지 하나씩 봤다(아래 "고정값").
- 스토리: `CitationsAndSources`(mk-cite), `SideEffects`(mk-side 두 입력), `CitationGaps`(번호 사이 틈과 줄 높이), `SourcesHeading`(출처 덩이 안의 제목). 모두 계산값으로 잰다.
- 01 일지의 "다음" 가운데 이 티켓 몫 둘을 했다. 각주 정의의 표지를 파서의 `label` 대신 원문에서 잘라 짓고(`[^a\*b]`, `[^a&amp;b]`가 원문 그대로 남는다), `unwrapBlocks`와 `unwrapRoot`를 제네릭 함수 하나(`unwrapDefinitions`)로 합쳤다.

## 고친 것과 명세에 더한 것

- `d49`(`2*(3+4)*5`): 변환을 모두 켜니 기울어졌다. 파서는 이 꼴을 강조로 읽지 않는데, 차례 2가 두 별표를 짝지어 위치 없는 강조를 만들고, 차례 3은 위치 없는 노드를 건드리지 않아 그대로 남았다. 차례 2에 "여는 묶음의 바로 앞과 닫는 묶음의 바로 뒤가 둘 다 ASCII 숫자인 짝은 짓지 않는다"를 더했고, 명세 "한국어에서 닫히지 않는 굵게"에 같은 조건과 까닭을 적었다. 시제품 `shape.mjs`는 `d49`를 "(다)" 묶음에서 그 변환만 켜고 돌렸고, 두 변환을 함께 켠 "(나)와 (다)" 묶음에는 그 꼴이 없어 이 겹침을 보지 못했다(`shape-cases.mjs`와 `shape-entry.tsx`를 읽었다. 셀프 리뷰의 표준 축이 처음 문장의 반쪽을 짚어 고쳤다).
- `k13`(새 경계 입력): 차례 5가 표지가 붙은 문단을 가르면 앞 본문의 위치가 사라져, 차례 6이 `\[1\]`을 역슬래시로 쓴 대괄호로 알아보지 못할 수 있다. 가른 본문 노드에 원문 위치를 남기도록(줄 끝 수가 맞을 때) 고쳤고 `k13`이 그것을 고정한다.
- `s31`: 처음 적은 기대(출처 덩이가 생긴다)가 틀렸다. 빈 줄 없이 이어진 `출처`는 마크다운 문법상 앞 목록의 마지막 항목에 붙으므로, 지금의 결과(덩이 없음)로 고쳐 고정했다.

## 고정값 (목표가 없는 입력, 명세와 맞대 봤다)

- 글자로 남는 것: `d04`, `d36`, `d40`, `d54`, `c10`, `c11`, `c20`, `c34`, `c48`, `n22`(취소선 기호).
- 강조로 남는 것: `d35`, `d37`, `d47`, `d57`~`d60`(글자로 시작하는 식은 명세가 기울어진다고 적었다).
- 위첨자가 되는 것: `c04`, `c12`, `c17`, `c45`. 링크 정의(`[1]: 주소`)가 있어 링크가 되는 것: `c25`, `c26`. 각주 글자: `c27`. 자동 링크가 흡수: `c44`.
- 출처 덩이가 생기지 않는 것: `s21`, `s31`. 받아들이는 한계: `n13`(겹친 굵게), `n34`(파일 패턴).

## 변이 (손으로 넣고 돌렸다, 각각 되돌렸다)

| 변이 | 결과 |
|---|---|
| 이어진 번호의 표지를 무시하고 언제나 `ml-cite-start` | 스토리 `CitationGaps`가 빨갰다(`vitest run --project storybook`을 그 스토리만 걸러 돌렸다. `1 failed \| 19 skipped (20)`) |
| 차례 5가 가른 본문의 위치를 버린다 | `k13`이 빨갰다(`vitest run --project ui-pages`를 그 시험만 걸러 돌렸다. `1 failed \| 470 skipped (471)`) |
| 각주 표지를 고치기 전의 코드 | 새 각주 시험 둘이 빨갰다(시험을 먼저 쓰고 손으로 돌렸다. 고친 뒤 초록) |
| (셀프 리뷰 뒤) 출처 덩이의 `[숫자]` 줄 문단 앞에서 옛 판정(앞 블록 전체가 표지일 때만)으로 되돌림, 그리고 허용 판정이 표지 없는 `sup`을 들임 | 둘을 함께 넣고 `Markdown.test.tsx` 전체를 돌려 `3 failed \| 472 passed (475)`. 빨간 것은 `t01`, `t02`, 허용 판정 시험이다. 되돌린 뒤 475 통과 |

## 번호 2,000·4,000·8,000개를 그리는 시간

손으로 돌려 본 기록이다. `가나 [1] `을 되풀이한 줄바꿈 없는 한 줄을 Node에서 `renderToStaticMarkup(Markdown)`으로 그렸다(esbuild로 CommonJS 묶음을 지어 `node`로 쳤다). 스크립트는 세션 스크래치패드의 `timing/entry.tsx`이고 커밋하지 않았다. 티켓이 이 수를 시험으로 단언하지 않는 기록으로 정했고 명세·코드 주석이 근거로 들지 않기 때문이다. 회차마다 그린 결과의 위첨자 수가 번호 수와 같은지를 표지로 보고, 맞지 않은 회차는 측정으로 세지 않았다(두 실행 모두 측정 아님 0). 대조는 같은 길이의 `가나 (1) ` 줄이다. 둘째 실행의 다섯 회차는 아래다.

| 번호 수 | 걸린 시간(초) | 대조(초) |
|---|---|---|
| 2,000 | 0.095~0.170 | 0.008~0.020 |
| 4,000 | 0.166~0.232 | 0.012~0.019 |
| 8,000 | 0.354~0.438 | 0.026~0.053 |

번호 수가 두 배가 될 때 시간도 대략 두 배다. 첫 실행은 4,000개의 앞 세 회차가 0.73~0.77초로 튀었고 뒤 두 회차는 0.15~0.17초였다(원인은 파지 않았다. 가비지 수집으로 어림한다). 시제품의 수치(0.3~0.4, 0.5~0.6, 1.5~3.5초)와 재는 자리가 같은지는 보지 않았다. 기록이고 시험으로 단언하지 않는다.

## 사진

패키지 사진은 `pnpm -C web visual:update`로 정답을 만들었고(새 스토리 넷 × 모드 둘 × 밀도 둘 = 16장, 134 통과, 종료 코드 0), 이어서 `pnpm -C web visual`이 134 통과, 종료 코드 0이었다(둘 다 출력을 파일로 받아 손으로 봤다). 그때 기존 사진은 하나도 바뀌지 않았다(`git status`에 새 사진만 보였다). 셀프 리뷰 뒤 보여 주기용 스토리의 글을 바꿔 그 사진 넷을 다시 만들었다(아래 셀프 리뷰 절). 화면 파일(`mk-cite-320`, `mk-cite-400`, `mk-side-320`의 `.dc.html`)은 디자인 토큰 변수를 문서 밖에서 받는 정적 스냅샷이라, 앞 티켓과 같이 그림 대 그림으로 견주지 못했다. 대신 세 가지로 갈음했다.

- 새 사진 넷(`citations-and-sources`, `side-effects`, `citation-gaps`, `sources-heading`)을 보통 밀도로 열어 눈으로 봤다. 위첨자는 작고 흐리게 앞말에 붙고, 출처 덩이는 선 아래 작은 흐린 글자이며 항목 사이 틈이 없고, `2*3*4 = 24`와 `__init__.py`는 글자 그대로이고 `민법 제750조(불법행위)`는 굵다.
- 화면 파일의 CSS 규칙(`.md sup`: `text-small`, 줄 높이 0, `text-muted`, 왼쪽 2px. `.md .sources`: 위 선 1px `border`, 선 아래 `spacing-3`, `text-small`, `text-muted`, 블록 사이 `spacing-1`, 항목 사이 0)을 읽어 스토리 play의 계산값 단언(2px, 12px, 4px, 0, 줄 높이 0)과 맞댔다(코드를 읽었다). `mk-side-320`의 설명 글(굵게는 조사가 붙어도 닫힌다, `#` 줄은 제목이 된다, `__init__.py`는 글자다)과 사진이 같다.
- 이어진 번호의 4px은 그림에 없어 명세의 값으로 스토리가 잰다.

나머지(그림 대 그림의 견주기)는 리뷰하는 사람의 몫이고 PR 본문에 적는다.

## 셀프 리뷰 (`/code-review`, 고정점 `origin/dev` = 0e06c9cf7, 변경 파일 14개, 미추적 25개 가운데 사진 16장, 커밋 0)

표준 축(sonnet, high)은 Critical·Major 0, Minor 6, Nit 6이었고 명세 축은 Critical·Major 0, Minor 5, Nit 2였다. 두 보고는 서브에이전트가 낸 것이고, 아래 판정은 이 세션이 코드·명세·프로브를 열어 내렸다. 명세 축 서브에이전트가 리뷰 도중 표준 축의 임시 시험 파일(`Tmp.test.tsx`)을 보았는데, 이 세션이 확인한 때는 이미 지워져 있었다(`git status`).

고친 것:

- 두 축이 함께 낸 것: 앞 문단에 붙은 `출처`와 `[숫자]` 줄 문단이 함께 오면(`본문\n출처\n\n[1] 가`) 출처 덩이가 생기지 않았다. 명세 "출처 덩이"는 두 꼴을 각각 알아보라고 적었다. 표지 앞 블록을 보는 판정을 `labelBefore` 하나로 모아 목록과 `[숫자]` 줄 문단이 함께 쓰게 했고, 경계 입력 `t01`·`t02`(`SOURCE_EDGES`)를 더했다. 고치기 전 동작은 스크래치 탐침(`probe-src/entry.tsx`, esbuild 묶음을 `node`로 쳤다)으로 손으로 봤고, 고친 뒤의 변이는 위 표에 있다.
- 명세 d49 문장의 반쪽(표준 축): 위 "고친 것과 명세에 더한 것"의 문장으로 고쳤다.
- `Markdown.md`(표준 축과 명세 축): "문장 끝의 `[1]`"을 "글 속의 `[1]`(문장 끝이 아니어도)"로, `\[1\]`의 예외(사례 `k7`·`k8`)를 더했고, 표지 목록을 꼴 나열 대신 규칙(글이 "출처"인 한 줄, 콜론·굵게·기울임·제목, 앞 문단에 붙은 줄)으로 고쳤다. 예외 문장은 처음에 고친 자리 뒤의 `\[1\]`만 위첨자가 될 수 있다는 꼴로 썼다가, 고친 자리 앞의 `\[1\]`도 위첨자가 되는 것을 탐침으로 손으로 보고(`가 \[1\] 나 2*3*4`) "그 문단의"로 고쳤다.
- 카드(명세 축): 디자인 시스템 카드에는 `showcase` 스토리만 오르는데 그 글에 번호도 출처도 없었다. 티켓 "What to build"의 "디자인 시스템의 카드와 단위 시험이 이 모양을 보인다"를 따라 보여 주기용 스토리의 글에 번호 하나와 출처 덩이를 더했고, 그 사진 넷을 `visual:update --grep showcase-widget-output`으로 다시 만들어 눈으로 봤다.
- 허용 판정을 지키는 시험이 없었다(명세 축이 `allowElement: undefined`로 그려 봐 결과가 같았다고 보고). `allowElement`를 내보내 직접 부르는 시험을 더했다.
- 표지 이름의 흩어짐(표준 축): `options.ts`가 `CITE_PROPERTY`·`SOURCES_PROPERTY`를 읽고, 두 판정(`isCitation`, `isSourcesBlock`)은 `tree.ts`의 `hastName`을 쓴다. `isAsciiDigit`도 `tree.ts`로 옮겼고, `forEachPhrasingParent`는 `skip`을 받게 된 `forEachNode`를 부른다. `sources.ts`의 `before`·`wrap`은 `childrenBefore`·`sourcesBlock`으로 이름을 바꿨다.
- 낡은 미래형(명세 축): `cases/danger.ts` 머리의 "뒤의 티켓(02)이 … 바꾸므로"를 지금의 사실로 고쳤다.
- `unclosed-emphasis.ts` 머리의 "같은 길이끼리 앞에서부터 짝짓고"를 실제 동작("가장 가까운 여는 묶음")으로 고쳤다(표준 축).
- 일지: `c25`·`c26`의 분류(링크가 된다), 변이 표의 걸러 돌린 실행의 집계, 시간 기록이 커밋하지 않은 스크립트를 손으로 돌린 것임을 고쳤다.

남긴 것(이유):

- `[1] [2] 문서`(줄 머리의 첫째만 글자)와 `A[1] [2]`(둘째만 위첨자): 명세 "문장 끝 번호"의 묶음 규칙은 "이어 붙은 번호"(`A[1][2]`)만 정하고 공백을 둔 꼴은 정하지 않는다. 지금 동작은 머리 주석의 "바로 붙은"과 같다. 정할 일이면 명세의 몫이다.
- `sources.ts`의 여러 책임(Divergent Change)과 `hugs`·`rewrite`의 이름(Nit): 위치 자르기는 `k13`이 지키는 것이고, 나머지는 판단 항목이다.
- `rewrite(…, { startsLine })`: 갈래를 고르는 플래그가 아니라 입력의 사실이라 표준 위반이 아니다(표준 축의 판정과 같다).
- 시간 칸의 체크(두 축): 이 세션이 커밋 직후 PR 본문에 적는다. 그 사이에만 칸과 실제가 어긋난다.

다음 리뷰 층(PR 직전 리뷰)에 밀 주장으로 넘기는, 반영하며 새로 쓴 사실 문장:

- `Markdown.md`: "다만 같은 문단에서 숫자 사이의 별표나 닫히지 않은 굵게를 고쳤으면 그 문단의 `\[1\]`은 역슬래시 없이 쓴 `[1]`처럼 다뤄져 위첨자가 될 수 있습니다."
- `Markdown.md`: "표지는 글이 "출처"인 한 줄이고, 콜론(`출처:`)이나 굵게·기울임(`**출처**`)을 붙이거나 제목(`## 출처`)으로 써도, 앞 문단에 빈 줄 없이 붙어도 알아봅니다."
- `spec.md` 184줄 근처: "`shape.mjs`는 `d49`를 "(다)" 묶음에서 그 변환만 켜고 돌렸고 두 변환을 함께 켠 "(나)와 (다)" 묶음에는 그 꼴이 없어 이 겹침을 보지 못했고"
- `sources.ts`의 `labelBefore` 독스트링, `cases/sources.ts`의 `SOURCE_EDGES` 독스트링, `cases/danger.ts` 머리 둘째 문단, `unclosed-emphasis.ts`의 짝짓기 줄, `Markdown.stories.tsx`의 `SHOWCASE_TEXT` 주석.

다시 돌린 것(반영 뒤, 이 세션이 쳤다):

- `Markdown.test.tsx` 전체 475 통과(반영 전 471에 `t01`·`t02`와 그 수 단언, 허용 판정 시험이 더해졌다), Markdown 스토리 20 통과(`vitest run --project storybook`을 그 파일로 돌렸다), 바꾼 파일의 ESLint 종료 코드 0, Prettier는 바꾼 것 없음.
- 반영 전에 띄운 전체 러너(`uv run python tools/run_checks.py`)는 pytest 하나만 실패했다(7297 통과, 1 실패). `tests/tools/test_rerun_runner.py::test_같은_갈래가_두_번_든_파일럿의_두_회차가_함께_돌아도_번호가_다르다`가 동시에 도는 회차 수의 최댓값을 2로 기대했는데 1이었다. 그때 Docker 사진 비교와 리뷰 서브에이전트 둘이 함께 돌았다. 이 변경이 건드리지 않은 `tools/`의 시험이고, 그 파일만 다시 치니 63개가 모두 통과했다(`uv run pytest -q tests/tools/test_rerun_runner.py`). 부하에 기대는 시험이 한 번 흔들린 것으로 보고 원인은 파지 않았다. 나머지 단계(check-ticket, zizmor, lint-imports, check-instructions, check-type-escapes, pyright 둘, run-hooks, web-verify)는 통과했다. 반영 뒤의 손으로 치는 다섯은 커밋의 pre-commit으로 갈음한다.
- `uv run python tools/sibling_overlap.py`는 번호 겹침이 없고, 카나리아 알림 하나로 종료 코드 1이다. `.claude/rules/web-design.md`의 치수 목록에 `cite-start` 한 이름만 더했기 때문이다. 그 규칙을 원천으로 든 명세 여덟에 `tools/canary.py --preflight`를 쳤고 다섯은 통과, 셋(`web_design_artifact.toml`, `web_design_colors.toml`, `web_design_props_icon_card.toml`)은 "원천에 카나리아가 없다"로 실패했다. 앞 티켓 일지(2026-11-12-1809)가 같은 셋을 이 변경 이전부터 낡은 명세로 적었다. `claude -p`로 카나리아를 돌리지 않았고, 고친 한 줄이 파일 머리의 `paths`와 카나리아 문구를 건드리지 않아 사전 확인으로 갈음한다. 출력의 기준 브랜치 줄이 `ad7dff5`로 움직였고, `git diff --name-only HEAD...origin/dev`의 다섯 파일(U+FFFD 고침의 티켓·대기열·일지와 `web/tools/sync-design-system/assemble.ts`·그 시험)은 이 브랜치가 고친 파일과 겹치지 않는다.
- 셀프 리뷰를 반영한 뒤 사진 세 벌을 다시 쳤다. `pnpm -C web visual` 134 통과, `pnpm -C web visual:widget` 43 통과, `pnpm -C web visual:admin` 72 통과, 셋 다 종료 코드 0이다(출력을 파일로 받아 손으로 봤다). 두 앱의 사진은 바뀌지 않았다.

## PR 직전 리뷰 (CodeRabbit CLI)

`coderabbit-review` 서브에이전트가 돌았다(CLI 0.7.5, `Seat: not assigned`, Plan Free). `coderabbit review --agent --uncommitted --include-untracked --base origin/dev --dir web/packages/ui`가 종료 코드 0으로 끝났고 findings는 1건이다. `--dir` 밖의 `.claude/rules/web-design.md`와 `.scratch/` 문서는 CLI가 보지 않았다. 보안·버그 축은 확정된 지적이 없다고 서브에이전트가 보고했고, 그것은 코드를 읽은 판단이라고 스스로 적었다. 아래 판정은 이 세션이 내렸다.

| 지적 | 판정 | 이유 |
|---|---|---|
| (Major, 성능) `literal-marks.ts`의 `beyondRun`이 겹친 강조 노드마다 같은 별표 묶음을 처음부터 걸어, 별표 n개가 이어진 입력에서 시간이 n²로 는다 | 고침 | 손으로 재 보니 맞았다. 원문의 별표 묶음마다 앞뒤 자리를 처음 물을 때 한 번 훑어 적어 두는 `StarRuns`로 바꿨다. 아래 측정 |

측정은 스크래치 탐침(`stars/entry.tsx`, `stars/lib.tsx`. esbuild로 묶어 `node`로 쳤다, 커밋하지 않았다)을 손으로 돌린 것이다. 입력은 `2` + 별표 n + `x` + 별표 n + `3`(숫자 갈래)과 앞뒤를 `a`·`b`로 바꾼 것(글자 갈래)이고, 회차마다 그린 HTML의 표지(숫자 갈래는 강조 요소가 없고 별표 2n개가 남는다, 글자 갈래와 라이브러리 대조는 강조 요소가 있다)를 보고 맞지 않은 회차는 세지 않았다(세 실행 모두 측정 아님 0). 세 회차의 초다.

| n | 고치기 전 숫자 / 글자 | 고친 뒤 숫자 / 글자 | 라이브러리만(react-markdown + remark-gfm) 숫자 / 글자 |
|---|---|---|---|
| 2,000 | 0.279~0.296 / 0.212~0.226 | 0.162~0.201 / 0.162~0.169 | 0.152~0.166 / 0.151~0.162 |
| 4,000 | 0.891~1.105 / 0.888~0.951 | 0.711~0.932 / 0.701~0.713 | 0.583~0.606 / 0.576~0.597 |

n이 두 배가 될 때 시간이 서너 배로 느는 모양은 라이브러리만으로 그려도 같다. 곧 제곱 시간의 대부분은 파서와 그리기의 몫이고, 이 변환이 더한 몫은 4,000개에서 약 0.3~0.5초가 약 0.1~0.3초로 줄었다(라이브러리 대조를 뺀 어림). 라이브러리 몫은 이 티켓이 고치지 않는다. 묶음 표가 판정에 쓰이는지는 변이 둘로 봤다. 앞쪽(`charBefore`)이나 뒤쪽(`charAfter`)을 바로 이웃 글자만 보게 바꾸면 각각 `d44`가 빨갰다(`Markdown.test.tsx` 전체, `1 failed | 474 passed (475)`). 되돌린 뒤 475 통과, ESLint 종료 코드 0, Prettier 통과.

첫 커밋 시도는 pre-commit의 `web-verify`에서 막혔다. `StarRuns`의 생성자 매개변수 속성(`constructor(private readonly source: string)`)을 `tsc`가 `erasableSyntaxOnly` 위반(TS1294)으로 거부했다. 반영 뒤 ESLint와 단위 시험만 치고 타입체크를 치지 않은 탓이다. 필드를 선언하고 생성자에서 넣는 꼴로 고쳤고, `pnpm -C web/packages/ui exec tsc --noEmit` 종료 코드 0, `Markdown.test.tsx` 475 통과다. 같은 시도에서 pytest(524초)를 비롯한 나머지 단계는 통과했다.

## PR

둘째 커밋 시도(`1e17efff6`)의 pre-commit은 모두 통과했다(pytest 704초, web-verify 874초). 푸시하려니 훅이 `origin/dev`보다 한 커밋 뒤처졌다고 막아, `ad7dff5`(U+FFFD 고침)를 충돌 없이 합쳤다. 들어온 변경이 카드를 짓는 `assemble.ts`라 `web/tools/sync-design-system/assemble.test.ts`(45 통과)와 일지·대기열 이름 시험(23 통과)을 다시 쳤다. PR은 https://github.com/njh6803/agent-os/pull/561 이다.

## PR 봇 첫 회차 (헤드 `b2dbd52`)

검사 열 개는 모두 통과했다(`llm`은 건너뜀). 두 봇 모두 이 PR의 첫 리뷰라 Minor·Nit도 지적마다 판단했다.

| 봇 | 지적 | 판정 | 이유 |
|---|---|---|---|
| CodeRabbit | (Minor) 출력 끝에 참조형 링크 정의가 있으면 마지막 자식이 `definition`이라 출처 덩이가 생기지 않고, 출처 안의 `[2]`가 위첨자가 된다 | 고침 | 사례 `t03`(`SOURCE_EDGES`)을 먼저 더해 빨강을 봤다(덩이 없음, `<sup>2</sup>`). `wrapSources`가 끝의 정의를 건너뛰고 그 앞 두 블록을 보게 고쳐 476 통과다. 정의는 화면에 그려지지 않아 화면상의 끝은 여전히 출처 덩이이므로, 명세 "출처 덩이"의 "마지막 두 블록" 문장에 정의를 세지 않는다는 조건과 사례를 더했고 `sources.ts` 머리 주석도 같게 고쳤다 |
| claude-review | (Minor) `hName`·`hProperties`를 짓는 자리가 셋으로 흩어졌다 | 일부 고침 | 같은 모양을 짓는 `citations.ts`와 `sources.ts`는 `tree.ts`의 새 `hastData`로 모았다. `heading-marks.ts`(티켓 01)는 기존 `data`를 펼치고 `hName` 없이 속성만 다는 다른 모양이라 그대로 뒀다 |
| claude-review | (Minor) 번호 표지는 DOM 이름과 hast 이름을 둘 다 상수로 두는데 출처 표지는 hast 이름만 둔다 | 보류 | 읽는 자리가 달라서다. 출처 표지는 허용 판정(hast 이름)만 읽고 부품의 `SourcesBlock`은 표지를 읽지 않는다. 번호 표지는 허용 판정(hast 이름)과 부품의 `Cite`(DOM 이름)가 함께 읽는다. 쓰지 않는 상수를 더하지 않는다 |
| claude-review | (Nit) `CITE_FIRST`를 밖에서 쓰지 않는데 내보낸다 | 고침 | 내보내지 않게 했다 |
| claude-review | (Nit) `sources.ts`가 표지 알아보기와 문단 자르기를 함께 맡는다 | 보류 | 셀프 리뷰가 같은 판단 항목을 남겼다(위 "셀프 리뷰"). 위치 자르기는 `k13`이 지킨다 |

다시 돌린 것: `Markdown.test.tsx` 476 통과, `pnpm -C web/packages/ui exec tsc --noEmit` 종료 코드 0, 바꾼 파일 다섯의 ESLint 종료 코드 0, Prettier 통과. 손으로 치는 다섯은 반영 커밋의 pre-commit으로 갈음한다.

## 회고

후보 아홉(아래 표 여덟과 일지에만 남기는 사례 하나), 승인 하나(대기열 새 항목), 기각 일곱, 일지에만 남기는 것 하나(받아들여 닫은 결함 종류의 새 사례), 넘김 0이다.

| 후보 | 판정 | 근거(retro 4단계) |
|---|---|---|
| 카나리아 명세 셋(`web_design_artifact`, `web_design_colors`, `web_design_props_icon_card`)이 `--preflight`에서 "원천에 카나리아가 없다"로 실패한다. 앞 티켓 일지(2026-11-12-1809)와 이 세션이 잇달아 봤다 | 승인(고침, 대기열 새 항목 `stale-web-design-canaries`, 0539의 2회차) | 사건: 이 세션이 `web-design.md` 한 줄을 고치고 사전 확인을 칠 때 셋이 막혔다. 층: 고침(기대 글을 지금 원천으로)이고 다섯 번째에 0539가 적은 검사로 올린다. 되돌림: PR 하나. 0539는 오늘 만료됐으므로 retro 5단계의 만료 뒤 잇기대로 새 항목이 회차를 잇는다. 이 PR의 범위(티켓 02) 밖이라 지금 반영하지 않는다 |
| 마크다운 부품의 출력을 Node에서 보는 탐침이 저장소에 없어, 이 세션이 esbuild 묶음을 셋(`probe-src`, `timing`, `stars`) 손으로 지었고 `pnpm exec esbuild`가 찾지 못해 바이너리 경로를 찾느라 몇 번 더 쳤다 | 기각 | 사건은 있지만 더하는 것(새 도구)이고 같은 실수의 반복이 아니라 비용이다. 다음 티켓(03)은 위젯에 붙이는 일이라 같은 탐침이 다시 필요할지 서지 않는다. 사건 없이 떠올린 일반화에 가깝다 |
| 셀프 리뷰가 잡은 출처 덩이의 빠진 조합(앞 문단에 붙은 표지 + `[숫자]` 줄 문단) | 기각 | 명세 축 리뷰가 제 몫을 했다. 사례 파일이 두 꼴을 따로만 들었고, 조합을 만드는 검사는 판단 항목이다 |
| 카드에 오르는 보여 주기용 스토리에 번호와 출처가 없었다(티켓 "What to build"의 "카드와 단위 시험이 이 모양을 보인다") | 기각 | 명세 축 리뷰가 잡았다. 티켓 문장을 놓친 것이고 `web-design.md`의 지침(카드에는 showcase만 오른다)을 어긴 것은 아니다 |
| PR 직전 리뷰가 잡은 별표 묶음의 제곱 시간(`beyondRun`) | 기각 | PR 직전 리뷰(버그·성능 축)가 제 몫을 했다. 셀프 리뷰의 두 축은 성능을 보지 않는다 |
| `Markdown.md`의 예외 문장을 처음에 "그 뒤의 `\[1\]`"로 썼다가 탐침으로 틀린 것을 보고 "그 문단의"로 고쳤다 | 기각 | 커밋 전에 이 세션이 스스로 탐침으로 잡았다. 리뷰가 잡은 사건이 아니라 회차에 들지 않는다 |
| 스크래치 탐침에 sed로 넣은 문자열의 역슬래시가 하나 빠졌다 | 기각 | 이 세션 안에서 Edit 도구로 바로 고쳤고 비용이 작다 |
| PR 직전 리뷰를 반영한 `StarRuns`의 생성자 매개변수 속성이 `erasableSyntaxOnly`에 걸려 첫 커밋이 막혔다(반영 뒤 ESLint와 단위 시험만 쳤다) | 기각 | 이미 있는 검사(pre-commit의 `web-verify` 안 `tsc`)가 그 자리에서 막았다. 커밋 시도 한 번(약 9분)이 더 들었을 뿐 손상은 없다 |

일지에만 남기는 것: 반영 전 전체 러너에서 `tests/tools/test_rerun_runner.py::test_같은_갈래가_두_번_든_파일럿의_두_회차가_함께_돌아도_번호가_다르다`가 부하 아래에서 한 번 빨갰다(동시 회차 최댓값 기대 2, 실제 1. 따로 돌리면 63 통과). 대기열 306(부하에서 흔들리는 시간 시험)은 ADR 0036으로 받아들여 닫은 끝이 열린 결함 종류라, 새 사례는 회차를 더하지 않고 여기에만 적는다.

인계 계기: `hook_handoff`가 세 번 왔다(커밋 뒤 경계에서 세션 컨텍스트 364,113 토큰과 압축 뒤 251,685 토큰, PR 연 뒤 경계에서 266,876 토큰). 이 세션은 다른 세션이 연 곁 세션(`parentSessionId` 있음, `detached` 거짓)이라 `handoff.md` 1의 다섯째 갈래대로 넘기지 않고 이었다.

만료: 이 워크트리에서 `uv run python tools/queue_open_rows.py`의 "만료할 항목"이 없음이라, 두 출력에 모두 든 항목도 없어 닫은 항목이 없다.

## 다음

- 티켓 03(`.scratch/answer-markdown/issues/03-widget-renders-answers-as-markdown.md`)이 막힌 것 없이 남았다. 01과 02가 done이다.
- 디자인 시스템 아티팩트에는 이 PR의 병합 뒤 `/sync-design-system 올리기`가 마크다운 부품의 카드(보여 주기용 스토리에 번호와 출처를 더한 것)를 올린다. 이 티켓의 일이 아니다. 그 올리기가 기다리던 U+FFFD 고침은 이미 dev에 병합됐다.
- 회고가 대기열에 둔 고침 하나: `stale-web-design-canaries`(카나리아 명세 셋의 기대 글이 원천에 없다).
