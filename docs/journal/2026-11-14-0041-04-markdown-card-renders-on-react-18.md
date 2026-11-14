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

## 인계(2차, 2026-11-14 `커밋 뒤`)

사용자 프롬프트 원문은 첫 세션과 같다(위 "사용자 프롬프트(원문)"). 이 세션(2차)이 한 일은 위 "셀프 리뷰(새 세션, 2026-11-14)"와 "전체 검증과 판 올림(새 세션)"에 있다. 결정은 ADR 0025 이력 `2026-11-14 카드 시험이 페이지의 React 18.3.1로도 그리게 하고, 그 두 판은 시험 전용 패키지가 든다`의 사용자 승인(AskUserQuestion, 답 "승인")이다. 세션 제목은 인계 전 `feature/04-markdown-card-renders-on-react-18`이었다.

커밋 `e2451faa5`(`fix: 마크다운 카드가 React 18에서 그려진다 (04-markdown-card-renders-on-react-18)`)까지 했고 pre-commit이 통과했다. 남은 것은 푸시, PR 열기, 봇 회차, 병합이다(요청 범위 "PR과 병합까지"). 티켓 3번(올리기와 앱 안 브라우저 확인)은 이 PR 밖이라 `[ ]`로 둔다. origin/dev가 앞서 있어(581903f, 03 위젯 마크다운 병합) 병합 전에 `docs/constitution/operations.md`의 브랜치와 병합 규약대로 기준 브랜치를 맞춘다. 앞서 있는 변경에 이 브랜치가 고친 파일은 없었다(`git diff --name-only HEAD...origin/dev`로 봤다).

open-session을 부른다 2026-11-14T02:25:46Z

## PR 직전 리뷰와 PR(3차 세션, 2026-11-14)

사용자 프롬프트 원문은 첫 세션과 같다(위 "사용자 프롬프트(원문)"). 세션 제목은 인계 전 `마크다운 카드 React 18 렌더링`이었다가 `feature/04-markdown-card-renders-on-react-18`로 바꿨다.

- 일지 커밋(2차 인계)을 한 뒤 `git rebase origin/dev`를 했다. origin/dev가 581903f(03 위젯 마크다운, PR 563)로 앞서 있었고 rebase 출력이 `Successfully rebased`였다(손으로 봤다). `git diff --name-only HEAD...origin/dev`는 출력이 비었다(손으로 쳤다). 합친 상태에서 `pnpm -C web exec vitest run tools/sync-design-system/assemble.test.ts`가 56건 초록, 29초였다(손으로 쳤다). `uv run python tools/sibling_overlap.py`는 종료 코드 0, 번호 겹침 없음(헌법 3.0.97)이었다(손으로 쳤다).
- PR 직전 `coderabbit-review` 서브에이전트의 보고(이 세션이 CLI를 다시 돌리지 않았고 보고를 옮긴 것이다): CLI 0.7.5가 종료 코드 0으로 `review_completed`, findings 0건이었다(`Seat: not assigned`, `Plan: Free`. 좌석이 없어도 리뷰가 끝까지 돌았다고 보고했다). 대상은 변경 14개 파일 전부(150개 한도 안)였다. 트리아지할 지적이 없어 유효·오탐·보류가 모두 0건이다. 서브에이전트가 diff를 읽고 낸 소견은 문제 없음이었다(`.Provider` 여섯 곳이 모두 바뀌었고 웹 전체에 `<XContext value>` 꼴이 남지 않았다. 락 파일의 추가는 react·react-dom 18.3.1, scheduler 0.23.2, loose-envify 1.4.0뿐이라고 했다. 이 소견은 읽은 것이고 재지 않았다).
- 일지 커밋의 pre-commit(러너, 610.7초)에서 pytest 둘이 빨갰다(러너 출력을 읽었다. 7307 passed, 2 failed).
  - `tests/test_plan_status.py`의 끝 줄 시험: rebase로 03(PR 563)이 들어오며 `answer-markdown`의 티켓 네 장이 모두 done이 되어, 이 PR이 마지막 티켓을 닫는다. 그래서 `.scratch/answer-markdown/plan.md`에 `**끝:** 2026-11-14`를 더하고 `uv run python tools/plan_table.py`를 돌려 `.scratch/plan.md`까지 같은 커밋에 싣는다(규칙은 `docs/agents/issue-tracker.md`의 전체 계획 절, `implement` 스킬을 읽었다). 앞 세션이 끝 줄을 더하지 않은 것은 그때 03이 `ready-for-agent`였기 때문이다(위 "한 일").
  - `tests/tools/test_rerun_runner.py`의 "첫 인계 뒤 멈추고 확인 인자를 주면 잇는다": 단독으로 `uv run pytest -q tests/tools/test_rerun_runner.py -k 본_측정에서_첫_인계 -p no:xdist`를 치면 통과했다(손으로 쳤다, 1 passed). 이 PR이 건드린 파일(`web/`, 문서)과 이어지는 경로를 찾지 못했고 부하가 높은 병렬 실행에서만 빨간 것으로 어림한다. 원인은 가르지 못했다. 다시 돌린 pre-commit이 초록이면 그대로 두고, 또 빨가면 diagnosing-bugs로 간다.
- 남은 것: 푸시, PR 열기, 봇 회차, 병합. 티켓 3번(올리기와 앱 안 브라우저 확인)은 이 PR 밖이다.

## 봇 첫 회차(PR 564, 3차 세션)

- 머리 6df8f15에서 `uv run python tools/wait_ci.py 564`가 `끝: 모두 통과. CodeRabbit: Finished`였다(출력을 읽었다. verify·python·web·e2e 셋·visual·ticket·claude-review SUCCESS, llm SKIPPED).
- claude-review(코멘트를 읽었다): 지적 없음, Nit 1. `web/packages/react-18/src/index.ts` 독스트링이 "코드는 없다"는데 경로 계산과 상수를 내보낸다는 지적이었다. 맞아서 "시험이 읽을 값(자리와 판 문자열)만 내보낸다"로 고쳤다.
- CodeRabbit(코멘트를 읽었다. 첫 회차): Minor 1과 병합 위험 요약의 같은 취지. `Status: done`인 티켓 04에 열린 체크박스(올리기)가 남아 추적되지 않는다는 지적이었다. 앞 티켓 01·02는 올리기를 "이 티켓의 일이 아니다"로 닫았으므로 04도 그 서식으로 맞췄고(티켓 13행), 남은 일은 아래 "다음"에 적었다. 새 티켓을 따로 쓰지 않은 까닭은, 올리기는 사용자 계정의 아티팩트에 보내는 일이라 올리기 세션(`sync-design-system`)이 harness 티켓으로 쓰는 것이 이 저장소의 길이기 때문이다(앞의 `ds-upload-markdown-cards`가 그랬다. 그 티켓 이름을 읽었다).
- 푸시 하나에 위 둘과 이 일지를 함께 실었다. CodeRabbit은 이 PR의 시간당 포함 리뷰가 0 남았다고 적었으므로(코멘트를 읽었다) 둘째 회차는 한도로 비거나 지연될 수 있다. 둘째 회차부터는 Critical·Major만 고친다(`merge.md` 2).

## 다음

- 이 PR이 병합되면 디자인 시스템 아티팩트(https://claude.ai/artifact/8ttLDZQqchfD2ao1XG56GH)는 아직 옛 묶음이라 Markdown 카드가 그대로 깨져 있다. `/sync-design-system 올리기`로 고친 부품을 올리고, 앱 안 브라우저로 Components 절의 Markdown 카드가 그려지고 칸 아래가 잘리지 않는지 본다. 올리기는 사용자 계정의 아티팩트에 보내는 일이라 올리기 세션이 harness 티켓으로 쓰고 한다. 이 세션은 올리지 않았다.
- `answer-markdown`의 네 티켓이 모두 닫혀 기능 계획에 `**끝:** 2026-11-14`를 적었다. 병합 뒤 결정표의 출시 PR 줄 조건(끝 줄을 적은 커밋이 dev에만 있다)이 찬다. 전제(main CI 초록)는 병합 뒤 `merge.md`의 "출시 PR"대로 확인한다.
- pre-commit pytest의 `test_rerun_runner.py` 시험 하나가 병렬 실행에서 한 번 빨갰다(단독 실행은 초록). 같은 시험이 또 빨가면 diagnosing-bugs로 원인을 찾는다. 이 PR이 건드린 경로와 이어지는 곳은 못 찾았다.
- 봇 회차 반영 커밋의 pre-commit pytest(622.8초, 7308 passed, 1 failed)에서는 다른 시험 `tests/tools/test_probe_kit.py::test_배출은_줄이_계속_와도_제한_시간에_끝난다`가 빨갰다(러너 출력을 읽었다. `reader.drain(0.5)`가 빈 목록을 돌려줬다). 단독으로 `uv run pytest -q tests/tools/test_probe_kit.py -p no:xdist`를 치면 15건이 통과했다(손으로 쳤다). 이 커밋은 티켓 문장, 독스트링 한 줄, 일지만 바꿨으므로 이어지는 경로가 없고, 자식 프로세스가 0.5초 안에 첫 줄을 내야 하는 시험이라 다른 세션이 함께 돌아 부하가 높은 때에 시작이 늦은 것으로 어림한다(원인은 가르지 못했다). 서로 다른 시간 민감 시험이 한 번씩 빨간 것이라 같은 시험이 두 번 연속 빨간 것은 아니다(`CLAUDE.md` 작업 규약 6의 조건 밖). 병렬 부하에서 시간 민감 시험이 흔들리는지는 retro가 대기열에서 회차를 센다.
