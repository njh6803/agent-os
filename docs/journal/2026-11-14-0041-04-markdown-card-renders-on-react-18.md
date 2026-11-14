# 04 마크다운 카드가 디자인 시스템 페이지의 React 18.3.1에서 그려진다 (구현)

브랜치 `feature/04-markdown-card-renders-on-react-18`, 워크트리 `.claude/worktrees/04-markdown-card-renders-on-react-18`. 세션 제목은 인계 전 `feature/04-markdown-card-renders-on-react-18`이었다. 티켓은 `.scratch/answer-markdown/issues/04-markdown-card-renders-on-react-18.md`.

## 사용자 프롬프트(원문)

> 사용자: "/implement .scratch/answer-markdown/issues/04-markdown-card-renders-on-react-18.md" (next-session 지시문. 이번 요청 범위는 "PR과 병합까지", 모델은 "Sonnet 5.5 / high")

## 한 일(커밋하지 않았다)

- 원인 어림을 재현했다. 임시 폴더(스크래치패드 `r18/`, 커밋하지 않은 스크립트 `probe.cjs`)에 react·react-dom 18.3.1을 설치해 `renderToString`으로 돌렸다. 컨텍스트 객체를 요소로 쓰면(`<Ctx value>`) `render is not a function`을 던졌고 `<Ctx.Provider>`는 그려졌다(손으로 봤다).
- 시험 자리를 정했다. 처음에 `web/package.json`에 별칭(`"react-dom-18": "npm:react-dom@18.3.1"`)으로 두었더니 pnpm이 Storybook의 `react-dom` 피어를 18.3.1로 바꿨다. `web/packages/ui/package.json`에 두자 18.3.1 `react-dom`이 `react@19.3.0`과 짝지어졌다(락 파일 차이를 읽었다). 둘 다 되돌렸다.
- 그래서 시험 전용 워크스페이스 패키지 `web/packages/react-18/`(`@agent-os/react-18`, react·react-dom 18.3.1 판 고정, `src/index.ts`가 `REACT_18_MODULES`와 `REACT_18_VERSION`만 내보낸다)를 만들고 `web/package.json`의 devDependencies에 `workspace:*`로 들였다. 락 파일 차이는 이 패키지의 몫뿐이다.
- `web/tools/sync-design-system/assemble.test.ts`: `reactGlobals(work, modules)`가 판의 폴더를 받는다. `cardDocument`·`show`가 전역 React 문자열을 받는다. 새 사례는 "시험이 싣는 React는 18.3.1이다"와 모든 카드를 18.3.1로 그리는 `test.each`다. 고치기 전에 Markdown 카드만 `i is not a function`으로 빨갰고(`TypeError ... at Ul`) 나머지 아홉 카드와 버전 사례는 초록이었다. 버전 사례는 `react18`을 패키지 19로 바꾸는 변이로 빨강(`expected '19.3.0' to be '18.3.1'`)을 보고 되돌렸다.
- `web/packages/ui/src/components/molecules/Markdown.tsx`: `PlaceContext`(셋 자리)·`InPreContext`·`TableSectionContext`(둘 자리) 제공자 여섯 곳을 `.Provider`로 바꿨다(02가 더한 `SourcesBlock`의 `sources` 자리 포함, 다시 grep했다). `assemble.test.ts` 전체가 56건 초록이다.
- 문서: ADR 0025에 이력 `2026-11-14 카드 시험이 페이지의 React 18.3.1로도 그리게 하고, 그 두 판은 시험 전용 패키지가 든다`를 더했다(끝의 `이 이력은 ... 사용자가 승인했다` 문장은 승인 전이라 아직 없다). `docs/constitution/tech.md` 웹 행과 루트 `README.md` 트리에 `@agent-os/react-18`을 적었다.
- 티켓: `Status: done`, 체크박스 1·2는 `[x]`. 3(병합 뒤 올리기와 앱 안 브라우저 확인)은 이 PR 밖이라 문구에 `(병합 뒤, 이 PR 밖. 올리기 세션이 한다)`를 붙여 `[ ]`로 두었다. 4(검증 명령)는 아직 `[ ]`다. `tools/plan_table.py`는 돌렸고 `.scratch/plan.md`는 바뀌지 않았다. 기능 계획에 `**끝:**` 줄은 더하지 않았다(03이 `ready-for-agent`로 남아 마지막 티켓이 아니다).
- `/sync-design-system 확인`(화면 코드를 처음 고쳤다는 훅의 계기)을 했다. 결과 `clean`, 웹 편집 없음, 결정 `continue`.

## 검증 상황

- `uv run ruff check .`와 `uv run ruff format --check .` 초록.
- `uv run python tools/run_checks.py`는 check-ticket·lint-imports·zizmor·check-instructions·check-type-escapes·pyright·pyright-linux·run-hooks·pytest(399초)가 초록이었고, web 단계는 끝나기 전에 인계로 멈췄다(백그라운드 작업을 TaskStop으로 멈춘다). 로그는 스크래치패드 `gate.log`에 있었으나 새 세션은 그것에 기대지 않고 pre-commit이 부르는 같은 명령으로 갈음한다.
- `pnpm -C web visual`(Docker) 134건 초록. 위젯과 관리 화면은 아직 Markdown을 쓰지 않아(03이 남음) `visual:widget`·`visual:admin`은 치지 않았다.

## 사용자에게 남은 판단

- ADR 0025 이력 초안의 승인(CLAUDE.md 작업 규약 5, 헌법 거버넌스). 새 의존(`@agent-os/react-18`)은 tech.md가 ADR을 요구한다. 셀프 리뷰를 반영한 뒤 초안을 AskUserQuestion으로 보여 주고, 승인되면 이력 끝에 `이 이력은 2026-11-14에 사용자가 승인했다.`를 더한다.
- 티켓 체크박스 3(올리기 확인)을 이 PR 밖으로 돌린 것. 앞 티켓 01·02는 "병합 뒤 올리기가 올린다(이 티켓의 일이 아니다)"로 적었다. 04는 수용 기준에 올리기가 들어 있어 `[ ]`로 남겼다. 올리기는 사용자 계정의 아티팩트에 보내는 일이라 이번 요청 범위(PR과 병합까지)에 넣지 않았다.

## 셀프 리뷰(새 세션, 2026-11-14)

범위: base `6cb9bf3bbd2190425c7a4ec68a0c378868438a4b`, 파일 8개 수정, 커밋 0개, 미추적 2곳(`web/packages/react-18/`, 이 일지). 표준 축(sonnet·high)과 명세 축(본 세션 모델)을 병렬로 돌렸다.

- 표준 축: Critical 없음, Major 1, Minor 3, Nit 1. 명세 축: Critical·Major 없음, Minor 4(둘 다 아래에 판정).
- **고친 것**
  - Major. 명세 `.scratch/design-card-build/spec.md` 235행이 "카드 그리기 시험은 저장소의 React 19(...)로 돈다(사용자가 골랐다). 새 의존이 들지 않는다."라고 적어 이번 결정과 어긋났다(235행을 직접 읽어 확인했다). 그 항목에 2026-11-14에 이 티켓이 결정을 바꿨다는 괄호를 더했고, 같은 항목의 "React 19에만 있는 API를 쓴 컴포넌트는 이 시험이 잡지 못하고"도 더는 맞지 않는다고 적었다. 194·252행은 페이지 자체의 그림이 자동 검사 밖이라는 말이라 그대로 참이다. ADR 이력은 "이 이력은 그 결정을 바꾼다"로 밝히고 "함께 고치는 것"에 명세를 더했다.
  - Minor. ADR의 "다른 패키지의 의존성에는 들지 않는다"는 거짓이었다(`web/package.json`의 devDependencies에 `workspace:*`로 든다). "다른 패키지와 앱의 의존성에는 들지 않고 `web/` 뿌리의 devDependency로만 든다"로 고쳤고, 락 파일 문장에 뿌리 importer 링크 한 줄을 더했고, `tech.md` 웹 행에 "`web/` 뿌리가 devDependency로 쓴다"를 더했다.
  - Minor. `REACT_18_VERSION`과 `upload.ts`의 `LIBRARIES` 판이 따로 적혀 있었다. 버전 사례에 `withLibraries({}).libraries`가 두 판과 같은지 맞대는 단언을 더했다.
  - Minor. 재현 스크립트가 저장소에 없는 문제는 ADR에 "저장소에 남기지 않았다. 근거는 일지와 시험의 빨강이다"라고 밝혔다.
  - Minor(명세 축 4). ADR이 2026-10-28 이력 항목이 React 19로만 실었다고 쓴 것은 그 이력에 없는 사실이었다. "그 항목은 React를 적지 않았고, 명세가 ... 사용자가 골랐다고 적었다"로 고쳤다.
  - Nit. `index.ts` 주석의 흐린 문장을 "18.3.1의 `react-dom`이 19의 `react`와 엮인다"로 고쳤다.
  - 티켓 3번 문구의 "병합 뒤" 중복을 "(이 PR 밖. 올리기 세션이 한다) 병합 뒤"로 줄였다.
- **남긴 것**
  - 티켓 `Status: done`인데 체크박스 3·4가 `[ ]`로 남는 것이 `tools/check_ticket.py`나 저장소 상태 시험에 걸리는지는 pre-commit과 전체 검증이 판정한다(걸리면 그때 고친다).
  - 읽은 것을 잰 것으로 적었다는 지적(명세 축 3)은 ADR이 이미 "손으로 봤다"로 표시했고, 고치기 전 빨강은 이 세션 앞 단계에서 직접 봤으므로 더 하지 않았다.
- **다시 돌린 명령**: `pnpm -C web exec vitest run tools/sync-design-system/assemble.test.ts` 56건 초록, 27초(고친 뒤 새 판). 전체 검증은 아래에 적는다.
- ADR 0025 이력 승인(AskUserQuestion). 질문 요지는 "카드 시험이 React 19와 함께 18.3.1로도 카드를 그린다, 시험 전용 패키지 `@agent-os/react-18`이 판 고정으로 들고 `web/` 뿌리 devDependency로만 연결한다, design-card-build 명세의 '시험은 React 19로만, 새 의존 없음'을 뒤집는다, 치르는 값은 새 패키지와 락 46줄과 카드마다 한 번 더 도는 시험, 거부한 안 넷". 답: 라벨 "승인", 설명 "이력 끝에 '이 이력은 2026-11-14에 사용자가 승인했다.'를 더하고 전체 검증과 PR로 진행합니다." ADR 끝에 승인 문장을 더했다.

## 전체 검증과 판 올림(새 세션)

- `uv run ruff check .`와 `uv run ruff format --check .` 초록(2196개 파일).
- `uv run python tools/run_checks.py` 종료 코드 0. check-ticket·lint-imports·zizmor·check-type-escapes·check-instructions·pyright·pyright-linux·run-hooks·pytest(416.2초)·web-verify(635.4초)가 모두 Passed였다(러너 출력을 읽었다). 사진 비교는 앞 세션이 Markdown.tsx를 고친 뒤 `pnpm -C web visual`로 134건 초록을 봤고, 이 세션은 Markdown.tsx를 더 고치지 않았다(시험 파일·ADR·명세·주석만 고쳤다).
- `tools/sibling_overlap.py`가 헌법 `tech.md`를 고치고 판을 올리지 않았다고 종료 코드 1로 알렸다. `docs/constitution/README.md`의 판을 3.0.96에서 3.0.97로(문구 수정이라 patch), Last Amended를 2026-11-14로 올렸고 다시 돌려 번호 겹침 없음을 봤다.
- 티켓 4번(검증 명령이 모두 초록이다)을 `[x]`로 바꿨다. `tools/plan_table.py`를 돌렸고 `.scratch/plan.md`는 바뀌지 않았다.
- origin/dev가 581903f로 앞서 있다(03 위젯 마크다운 병합). `git diff --name-only HEAD...origin/dev`의 파일에 이 브랜치가 고친 파일은 없다.

## 인계

컨텍스트가 인계 문턱을 넘은 채 `셀프 리뷰 직전` 경계에서 인계했다. 새 세션이 `/code-review`부터 한다.

open-session을 부른다 2026-11-13T15:42:55Z
