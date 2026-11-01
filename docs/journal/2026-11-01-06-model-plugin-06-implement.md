# 2026-11-01 (06) 모델 플러그인 티켓 06 구현

세션 제목: `feature/06-admin-model-toggle-and-decision-preview`.

## 사용자 프롬프트 원문

> 사용자: `.claude/skills/implement/SKILL.md` 를 읽어 그대로 따른다. … 인자: `.scratch/model-plugin/issues/06-admin-model-toggle-and-decision-preview.md` … 다음 단계: 구현 … 이번 요청 범위: PR과 병합까지

ADR 0019 이력 초안을 보여 주고 승인을 물었다. 선택지는 "승인한다"(초안 그대로 확정하고 커밋·PR·병합까지 이어서 진행한다)와 "고친 뒤 다시 보여 달라"였다.

> 사용자: "승인한다"

## 한 것(커밋하기 전의 작업 트리)

- 목록의 안내 줄: `PluginList.tsx`의 `WITHOUT_LOADER`에서 `model`을 뺐다(스킬만 든다). `HomePage.test.tsx`의 "스킬 행에만 … 보인다"가 모델 묶음에 안내 줄이 없음을 단언하고, `e2e/admin-token.e2e.ts`의 모델 행 단언이 그 줄이 없다는 단언으로 바뀌었다.
- 결정 칸의 미리 알림: `RunDecision.tsx`의 `disabledFor`가 에이전트 행의 `manifest.model`이 `null`이 아니고, 그 이름의 모델 행이 `manifest`를 갖고 꺼져 있을 때 `모델 <이름>`을 더한다. 모델 행이 표지이거나 `model`이 `null`이면 더하지 않는다. 독스트링에 `model`과 기본 모델을 미리 알 수 없는 까닭을 더했다.
- 시험(`RunPage.decision.test.tsx`): 에이전트가 고른 모델이 꺼진 경우(버튼 둘이 막히고 `모델 sonnet`이 보인다), 고르지 않은 모델이 꺼진 경우, `model`을 적지 않은 에이전트, 모델 행이 표지인 경우의 넷을 더했다. 모델 플러그인과 `model`을 고른 `calc`를 만드는 헬퍼 둘은 불리언 매개변수 규칙에 걸려 옵션 객체(`{ enabled }`)로 받는다.
- 변이 표 `.scratch/model-plugin/probes/decision_model_mutations.toml`: 구현 전부터 초록이던 셋(고르지 않은 모델, `model` 없음, 모델 행 표지)을 겨누는 변이 셋이다.
- 문서: README `disabled.toml` 줄에서 model을 뺐다. ADR 0019에 이력 한 항목("꺼짐 미리 알림이 에이전트가 고른 모델까지 본다")과 본문 Consequences 줄 끝의 포인터를 더했다.
- 스토리: `DisabledPlugins`(`RunDetail.stories.tsx`)에 꺼진 모델을 더하지 않기로 했다. 경고의 모양이 그대로라 사진도 바뀌지 않는다. `PluginList` 스토리의 목록에는 모델 행이 없어(모델 0) 사진이 바뀌지 않을 것이라는 티켓의 어림이 `visual:admin`으로 확인됐다.

## 검증(이 세션이 본 것)

- 첫 빨강: 새 시험 다섯(안내 줄 하나, 결정 칸 넷) 가운데 둘이 빨강이었다. `HomePage.test.tsx`의 모델 묶음에 안내 줄이 없다는 단언과, 에이전트가 고른 모델이 꺼진 실행에서 버튼이 막힌다는 단언이다. 나머지 셋은 구현 전부터 초록이었다(꺼진 모델을 모르던 코드가 막지 않으니 막지 않는다는 시험은 통과한다).
- 변이: 위 셋을 `tools/mutate.py`로 잰다. 이름 비교를 지우는 변이, `model !== null` 가드를 지우는 변이, `"manifest" in other`를 지우는 변이가 각각 해당 시험을 `not to contain '꺼진 플러그인'`으로 빨갛게 만들었다(`expect_output`까지 맞았다, 변이 3 모두 기대대로).
- `uv run ruff check .`·`uv run ruff format --check .`: 통과.
- `uv run python tools/run_checks.py`: web-verify만 `no-restricted-syntax`(불리언 매개변수, `RunPage.decision.test.tsx` 145행)로 실패했고 나머지(check-ticket, zizmor, lint-imports, check-instructions, check-type-escapes, pyright 둘, run-hooks, pytest 282.2초)는 Passed였다. 그 헬퍼를 고친 뒤 `pnpm -C web verify`를 따로 쳐 시험 96파일·1587개가 통과하고 종료 코드 0이었다.
- `pnpm -C web/apps/admin exec playwright test`: 9 passed(43.2초). `pnpm -C web visual:admin`: 72 passed(1.9분), 정답을 다시 만들지 않았다.

## 셀프 리뷰(`/code-review`, base 54c79da9)

범위: 파일 8개 변경, 커밋 0개, 미추적 1개(변이 표). 표준 축은 sonnet·high, 명세 축은 세션 모델이다.

- 반영(고친 것): 변이 표에 `expect_output`이 없다는 표준 축 지적(probes 규칙 첫 항목)을 `not to contain '꺼진 플러그인'`으로 고쳤고, 다시 돌려 세 변이가 그 표지와 함께 빨개지는 것을 봤다. ADR 초안이 관리 API에 기본 모델의 이름을 내는 자리를 더하는 안을 계약 변경이라 거부했다고 적은 문장은 명세에도 일지에도 그 안을 따져 거부한 기록이 없어(두 축이 모두 짚었다, 명세는 전제만 적었다) 걷고, 표지 처리의 근거를 명세가 아니라 티켓 06(PR #444의 CodeRabbit 첫 회차)으로 바로잡았다. `PluginList.tsx`의 `WITHOUT_LOADER` 주석에서 모델이 런타임이 실행마다 읽어 빠졌다는 이력 서술을 지웠다.
- 남긴 것: `disabledFor`가 mcp와 모델에서 `rows.some(...)` 꼴을 두 번 쓰는 중복(Minor)은 mcp는 `manifest`를 보지 않고 모델은 본다는 비대칭이 티켓에 의도로 적혀 있어 합치지 않았다. 콜백 인자 이름 `other`(Nit)와 시험 파일의 `setTimeout(resolve, 100)` 대기(기존 관용)도 그대로다.
- 명세 축: Critical·Major 없음. 체크박스는 모두 덮였다.

## 보류와 메모

- 티켓이 "시작할 때 고른다"고 한 `DisabledPlugins` 스토리의 꺼진 모델 사례는 더하지 않기로 했다(위 한 것의 스토리 줄).
- 옛 표현 잔존: 살아 있는 문서(README, CONTEXT.md, `.claude/rules`, 소스 주석과 독스트링, ADR 본문)에서 0이다. ADR 0017 49행의 "skill과 model은 로더가 생길 때 … 지금은 효과가 없다"는 이미 `(바뀜: ADR 0040)`이 달려 있다.

## 인계(커밋 뒤)

구현 세션의 컨텍스트가 인계 문턱을 넘은 채 커밋 뒤 경계에 와서, 이어받은 새 세션이 남은 단계(PR 직전 리뷰, 푸시, PR, 봇 회차, 병합, 회고)를 맡았다. ADR 0019 이력 초안은 구현 세션이 사용자에게 보여 승인("승인한다")을 받았고 커밋 `466bf2ad`에 들었다.

## PR 직전 리뷰

`coderabbit auth status`가 `Plan: Free`, `Seat: not assigned`라 CodeRabbit CLI는 돌지 못했다. 대체 둘을 나란히 돌렸다(`docs/constitution/operations.md` 리뷰 파이프라인 2). 커밋 `466bf2ad`는 origin/main(`54c79da9`) 위에 그대로 서 있어 합칠 것이 없었다.

- `bug-perf-review` 서브에이전트(코드·시험 파일 5개): 지적 0건. 근거는 코드를 읽은 것이다. `disabledFor`를 런타임 판정(`src/agent_os/core/run.py`)과 대 보고, 모델 행이 표지일 때 꺼짐으로 세지 않는 것이 런타임 순서(읽히지 않음이 꺼짐보다 먼저 거부)와 맞는다고 읽었다. 시험은 이 리뷰가 돌리지 않았고, 시험을 돌린 근거는 위 "검증"이다.
- 내장 `/security-review`: 발견 0건. 근거는 소스 diff(`PluginList.tsx`, `RunDecision.tsx`)를 읽은 것이다. 변경은 JSX 텍스트로 모델 이름을 보이는 표시뿐이고 `dangerouslySetInnerHTML`이 없으며, 실행을 막는 판정은 서버의 409 봉투가 맡는다는 것은 티켓과 `RunDecision.tsx` 독스트링에서 읽었고 서버 코드는 이 리뷰에서 열지 않았다.

## 회고

이 세션이 한 일은 PR 직전 리뷰, 푸시, PR 쪽이라 새 실수가 없었다. 후보 셋을 모두 기각했다. 승인 0, 넘김 0, 기각 3.

- 기각: 구현 세션에서 `RunPage.decision.test.tsx`의 헬퍼가 불리언 매개변수 규칙에 걸려 `pnpm -C web verify`가 빨갰던 일. 린터가 그 자리에서 잡았고 옵션 객체로 고쳤다(이미 있는 검사가 막은 것).
- 기각: ADR 초안에 기본 모델 이름을 내는 안을 계약 변경이라 거부했다는 근거 없는 문장이 들었던 일. 셀프 리뷰 두 축이 잡았다(리뷰가 제 몫을 한 것이라 회차로 세지 않는다).
- 기각: 이 세션에서 `cd <하위 폴더> && …` 복합 명령을 훅이 막았던 일. 훅이 첫 시도에서 알렸고 경로 인자로 다시 쳐 풀렸다(이미 있는 훅이 막은 것).
- 만료: `queue_open_rows.py --ref origin/main`의 만료할 행이 없다.

## 다음

모델 플러그인(`model-plugin`) 기능의 티켓 01~06이 이 PR로 모두 `done`이다. 마지막 티켓이므로 `next-session` 결정표의 "그 기능의 마지막 티켓이었고 …" 줄을 본다. `.scratch/retro-queue.md`에 회차 3 이상인 열린 행이 있어(`uv run python tools/queue_open_rows.py --ref origin/main`의 "회차 3 이상" 줄을 손으로 세니 28개였다) 그 줄의 하네스 chore 배치가 다음 작업이다. 어느 행을 묶을지는 병합 뒤 `next-session` 순서 2가 대기열 행의 대상 파일과 실행 중 세션을 견주어 정한다.
