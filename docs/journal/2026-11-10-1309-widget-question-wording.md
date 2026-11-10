# 2026-11-10 (13:09) 위젯 입력창을 "질문"으로 부르고 TextField에 이름표 숨김 속성을 더한다 (pilot-portal 03)

세션 제목 `feature/03-widget-question-wording-and-hidden-label`(인계하며 `(인계함)`을 붙인다). 브랜치 같은 이름, 워크트리 `.claude/worktrees/03-widget-question-wording-and-hidden-label`(기준 `a9d7d942`). 모델 Sonnet 5.5 / high(지시문).

## 사용자 프롬프트

> .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 인자: .scratch/pilot-portal/issues/03-widget-question-wording-and-hidden-label.md
>
> 다음 작업: .scratch/pilot-portal/issues/03-widget-question-wording-and-hidden-label.md. 위젯 입력창을 "질문"으로 부르고, 디자인 시스템 TextField에 이름표를 화면에서만 숨기는 선택 속성을 더한다
> 다음 단계: 구현
> 브랜치: feature/03-widget-question-wording-and-hidden-label
> 모델: Sonnet 5.5 / high
> 읽을 것: 티켓과 .scratch/pilot-portal/spec.md의 "위젯 문구와 TextField", docs/journal/2026-11-10-1013-e2e-stack-package.md의 "다음"
> 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. 병합은 이 워크트리 사본의 next-session merge.md(없으면 SKILL.md)의 "워크트리에서 병합할 때"를 Read로 열어 따른다
> 이번 요청 범위: PR과 병합까지

## 한 일

- 세션 시작: 제목을 브랜치 이름으로 바꾸고 `tidy-checkouts`를 돌았다. 루트(main)를 `2402362d`에서 `a9d7d942`로 당겼고, 지울 워크트리는 없었다(쥔 프로세스와 바뀐 파일과 병합된 PR 없음 때문에 모두 남겼다). 휴지통 하나를 비웠고 하나는 `esbuild.exe`를 쥔 프로세스 때문에 남겼다. 그 뒤 `EnterWorktree`로 들어가 브랜치를 `feature/03-widget-question-wording-and-hidden-label`로 땄다.
- `sync-design-system 확인`(화면 코드를 처음 고칠 때 훅이 알렸다): `clean`, 결정표 `continue`. 웹 편집 없음.
- 티켓을 `in-progress`로 바꾼 뒤 시험부터 썼다(원칙 II). TextField `hideLabel`의 타입 테스트 사례와 스토리 `HiddenLabel`, 위젯 시험의 이름 `{ name: "질문" }`과 새 문구를 먼저 쓰고 빨강을 봤다(위젯 `WidgetPage.test.tsx` 5건, 스토리 1건, tsc 오류).
- 구현: `TextField`에 `hideLabel?: boolean`을 더하고 라벨에 `sr-only`를 단다(`<label for>`는 그대로). `Composer.tsx`는 `label="질문"` `hideLabel` `placeholder="무엇을 도와드릴까요?"`, 422 오류 글을 "질문을 보낼 수 없습니다. 질문을 고쳐 다시 보내 주세요."로, `Welcome.tsx`를 "아래 입력창에 적어 보내 주세요."로 바꿨다. `TextField.md`에 `hideLabel` 항목을 더했다.
- 위젯의 시험·스토리·e2e(12파일)에서 옛 글 셋을 치환했다(치환 스크립트는 스크래치패드의 일회용이고 소스 두 파일은 건너뛰었다). `ask(user, "요청")`의 "요청"은 이름표가 아니라 사용자가 입력창에 넣는 글이라 그대로 뒀다. `Conversation.tsx`의 화면 읽기 전용 `요청: `도 옛 글 넷에 없어 그대로 뒀다. 소스·시험·스토리·e2e의 옛 글 넷 grep 잔존은 0이다(`Composer.tsx` 35행 주석의 "요청을 고쳐"는 개념어 주석이다).
- 변이 표 셋이 옛 글을 가리켜 고쳤다: `widget_app_mutations.toml`(Welcome 원문), `failures_mutations.toml`(422 글의 표지), `storage_mutations.toml`(표지 둘). `mutate.py --check`로 그 셋과 TextField·Composer를 가리키는 다른 표 여덟을 봤고 모두 원문이 한 번씩 있다. `.scratch/design-system/probes/atoms_mutations.toml`은 StatusBadge·Progress·Card 원문이 0번인데 이번 변경과 무관한 기존 썩음이다(내가 건드리지 않은 파일).
- 사진 비교: `visual`은 현재 정답으로 새 스토리 `HiddenLabel` 한 건만 정답 없음으로 빨갰고(나머지 110건 통과), `visual:update`로 사진 넷(라이트·다크 × 촘촘·보통)을 더했다. `visual:widget:update`로 위젯 사진 35장이 바뀌었다(입력창 위 이름표가 사라지고 문구가 바뀐 것을 `invalid-light`로 눈으로 봤다). `visual:admin`은 정답이 바뀌지 않고 통과했다.
- 검증: `pnpm -C web verify` 초록(첫 시도는 `WidgetPage.test.tsx`의 `field.labels` 타입 단언 문제를 lint가 잡아 `getByText("질문")`으로 고쳤다). 위젯 e2e는 첫 전체 실행에서 도구 호출이 걸린 4건이 실패했고(진행 표시만 보이고 `add` 도구 줄이 서지 않았다), 하나를 단독으로 돌리자 통과했고, 전체를 다시 돌리자 16건 모두 통과했다. 첫 실패의 원인은 가리지 못했다(다른 세션이 함께 돌아 부하가 컸을 수 있으나 재지 않았다). `uv run --env-file ../../../.env pytest -m llm_widget`은 1건 통과(토큰 합계 6,937, 입력 6,865, 출력 72, 트레이스 1개, 모델 호출 2건). `ruff check`와 `ruff format --check` 통과.
- 티켓 `03`을 `done`으로 바꾸고 체크박스를 채웠고(마지막 "검증 명령이 모두 초록이다" 줄은 아래 전체 실행 뒤에 채운다 — 아직 `[ ]`), `uv run python tools/plan_table.py`를 돌렸다(이 표는 티켓 상태를 싣지 않아 `.scratch/plan.md`는 바뀌지 않았다. 명세 축 서브에이전트가 `plan_table.py --check`로 이상 없음을 봤다고 보고했고 이 세션이 다시 치지는 않았다). 기능 계획에 `**슬라이스:**` 줄이 있어도 07·08·09가 열려 있어 `**끝:**` 줄은 아직 쓰지 않는다.

open-session을 부른다 2026-11-10T04:11:25Z

## 인계 지점

컨텍스트가 인계 문턱을 넘은 채 셀프 리뷰 직전에 왔다. 커밋하지 않은 변경이 워크트리에 있다. 새 세션이 `/code-review`부터 이어서 한다.

- `uv run python tools/run_checks.py`는 이 세션이 백그라운드로 띄웠으나 끝을 보지 못하고 멈춘다. 새 세션이 다시 돌린다(리뷰 반영 뒤 커밋의 pre-commit이 손으로 치는 다섯을 갈음한다. 그 전에 한 번 전체를 보려면 새로 돌린다).
- 티켓 마지막 체크박스(검증 명령이 모두 초록)는 `run_checks.py`와 위의 e2e·`-m llm_widget`·사진 비교 결과가 모두 초록일 때 채운다. 지금까지 e2e·`llm_widget`·사진 비교·`pnpm -C web verify`·ruff는 초록이고, `run_checks.py`의 한 바퀴는 아직 보지 못했다.
- 디자인 시스템 아티팩트에 `TextField.md` 카드를 올리는 일(`sync-design-system 올리기`)은 하지 않았다. 티켓 범위에 없다. 병합 뒤 필요한지는 `docs/agents/issue-tracker.md`와 그 스킬의 `upload.md`로 새 세션이 판단한다.
- 이 세션은 백그라운드 `run_checks.py`를 멈췄고(`TaskStop`), 그 pytest가 남긴 시험용 서버 프로세스(이 워크트리의 `tests/mcp_http_server.py` 둘, pid 55468과 40904)를 끄고(`taskkill /T /F`), 워크트리 잠금을 풀었다(`git worktree unlock`).
- 셀프 리뷰가 시험을 고치면 `tools/mutate.py`로 새 시험이 지키는 코드(`TextField.tsx`의 `hideLabel`)에 변이를 넣어 빨강을 보는 일(implement 스킬의 변이 규칙)이 남았을 수 있다. 이번 시험은 구현 전에 빨강을 봤으므로(위 한 일) 필수는 아니고, 리뷰가 시험을 고쳤을 때만 본다.

## 이어받은 세션: 셀프 리뷰 (2026-11-10)

세션 제목 `feature/03-widget-question-wording-and-hidden-label`. 같은 워크트리에서 이어받았다. 지시문 모델은 Sonnet 5.5 / high.

### 사용자 프롬프트

> .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 인자: .scratch/pilot-portal/issues/03-widget-question-wording-and-hidden-label.md (이번 요청 범위: PR과 병합까지)

### 한 일

리뷰 지적의 사실 판정은 두 서브에이전트의 보고다(코드를 읽고 grep한 것이고, 스토리·시험은 돌리지 않았다고 명세 축이 밝혔다). 이 세션이 직접 다시 연 것은 `WidgetFailures.test.tsx` 머리 독스트링, 두 명세의 해당 줄, `git diff --stat -- .scratch/plan.md`(변경 없음)다. 고친 파일 셋의 `prettier --check`는 이 세션이 손으로 쳐 통과했다.

- 새 세션이라 `sync-design-system 확인`을 다시 돌렸다. 결과 `clean`, 결정표 `continue`(웹 편집 없음). `main.ts check judge`와 `decide`의 출력을 이 세션이 손으로 봤다.
- `/code-review`: base `a9d7d942`, 수정 57개(사진 PNG 포함)와 미추적 5개, 커밋 0개. 표준 축은 sonnet·high 서브에이전트, 명세 축은 본 세션 모델.
- 명세 축: 빠진 요구와 범위 넘침 없음. 지적은 셋이었다.
  - `WidgetFailures.test.tsx` 머리 독스트링이 422 글을 옛 명세 표에서 그대로 옮겼다고 적어 거짓이 됐다. → 고쳤다(pilot-portal 명세가 바꾼 글이라고 덧붙였다).
  - 일지가 plan.md까지 갱신했다고 적은 것은 diff에 plan.md 변경이 없어 과했다. → 위 문장을 고쳤다.
  - 티켓 `Status: done`과 마지막 체크박스 `[ ]`가 어긋난 채 커밋된다. → `run_checks.py`가 초록이면 체크박스를 채운다(남은 일).
- 표준 축: Critical·Major 없음. Minor 하나를 고쳤다. `hideLabel` 뒤에도 "라벨이 칸 위에 늘 보입니다/보이고"가 남은 `TextField.md` 표와 `TextField.tsx` 머리 주석을 "기본으로 칸 위에 보입니다/보이고"로 바꿨다. `TextField.stories.tsx` 72행의 "라벨은 칸 밖에 늘 보이는 글자이고"는 `hideLabel`이 없는 기본 스토리의 문장이라 그대로 뒀다.

### 남긴 것과 이유

- `.scratch/web-widget/spec.md` 30·230·296행의 옛 글. 끝난 기능의 명세라 기록이고(`docs/constitution/operations.md` 문서 위치), 잔존으로 세지 않는다.
- 입력창을 찾는 `{ name: "질문" }`이 12파일에 흩어진 Shotgun Surgery 냄새. 판단 항목이고 티켓 범위 밖이다. 시험은 `testing/widget.tsx`의 도우미, e2e는 `helpers.ts`의 도우미로 모으면 다음 이름 변경이 한 곳이 된다. 지금 PR에서 반드시 고칠 일은 아니다.
- 422 오류 글 `INVALID`가 소스·시험·스토리에 세 벌인 것은 시험이 원문을 박는 의도로 본다.
- 입력창 밖에 남은 사람에게 보이는 "요청"(`FailureAlert.tsx`의 "요청을 나눠 보내 주세요.", `ApprovalCard.tsx`, 진행 표시의 이름). 티켓이 명시한 글 넷이 아니고 개념어는 그대로 "요청"이라는 명세와 맞는다. 후속이 필요한지는 사용자 판단이다.
- 위젯은 이제 눈에 보이는 안내가 placeholder뿐이다. 접근 이름은 라벨에서 나오고 `TextField.md`가 "둘레 글로 뻔할 때만" 쓰라는 단서를 단다. 설계 결정이라 보고만 한다.

### 고치며 새로 쓴 문장(PR 직전 리뷰에 밀 주장)

- `TextField.md` 표: "라벨은 기본으로 칸 위에 보입니다."
- `TextField.tsx` 머리 주석: "라벨이 기본으로 칸 위에 보이고,"
- `WidgetFailures.test.tsx` 머리 주석: "다만 422의 오류 글은 pilot-portal 명세(.scratch/pilot-portal/spec.md)의 "위젯 문구와 TextField"가 바꾼 글이다."

### 첫 커밋 시도의 pre-commit 결과

`checks`(run_checks의 열 단계 전부, 719초)와 표·줄 구분 문자 검사는 통과했고, 변이 표 검사(`check-mutations`)가 빨개 커밋이 막혔다(손으로 본 pre-commit 출력). `.scratch/web-widget/probes/failures_mutations.toml`의 6번 변이가 표지로 든 422 글이 시험 원문(`WidgetFailures.test.tsx`의 `INVALID`)에 글자 그대로 있어 표지가 못 된다는 지적이다. 옛 글도 같은 모양이었으나 이 표를 고쳐 커밋하는 이번에야 걸렸다(옛 시험 원문 `a9d7d942`에 `const INVALID = "요청을 보낼 수 없습니다…"`가 있었던 것을 `git show`로 봤고, 옛 표지가 통과했는지는 돌려 보지 않았다).

- 고침: 표지를 실제 빨강 출력에서 골랐다. 임시 표지 `__PROBE__`로 변이를 한 번 돌려 실패 출력(`AssertionError: expected <p id="_r_0_-note" …(1)>…(1)</p> to be null`)을 본 뒤, 앞의 `<p id=…>`는 뗀 `</p> to be null`로 바꿨다. 이 표지가 단언 풀이 줄에서 나오는 것은 그 출력이 보였다.
- 다시 돌림: `mutate.py … --since origin/main`이 변이 1을 "모두 기대대로"로 끝냈다(손으로 쳤다, 종료 0). 표지 주석의 "useId 라 값이 바뀔 수 있다"는 id 모양(`_r_0_`)에서 낸 어림이고 여러 번 돌려 보지 않았다.
