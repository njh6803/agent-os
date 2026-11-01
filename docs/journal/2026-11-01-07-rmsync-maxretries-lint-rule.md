# 2026-11-01 (07) 재귀 rmSync maxRetries 규칙

세션 제목: `chore/037-rmsync-maxretries-lint-rule`.

## 사용자 프롬프트 원문

> 사용자: 대기열 543을 티켓 .scratch/harness/issues/037-rmsync-maxretries-lint-rule.md로 쓰고 한다 … 이번 요청 범위: PR과 병합까지

## 한 것(커밋하기 전의 작업 트리)

- 티켓 037을 썼다. 대기열 543이 적은 두 갈래 가운데 린트 규칙을 골랐다. 공용 도우미는 새 직접 호출을 막지 못해 결국 같은 규칙이 필요하다고 보았다.
- `web/eslint.config.mjs`의 `RESTRICTED_SYNTAX`에 selector를 더했다. `rmSync(…)`와 `<객체>.rmSync(…)` 호출의 옵션 객체 리터럴이 `recursive: true`를 갖고 `maxRetries`가 없거나 0이면 잡는다. 옵션을 변수로 넘기거나 펼친 호출은 보지 않는다(설정 주석에 적었다).
- `web/eslint.config.test.ts`에 걸리는 사례 다섯과 지나는 사례 셋을 처음 더했다(셀프 리뷰 반영 뒤 일곱과 넷). 규칙을 켜기 전에 걸리는 사례 다섯이 모두 빨갛다는 것을 `pnpm -C web exec vitest run eslint.config.test.ts -t "재귀 rmSync"`로 손으로 봤다(`expected [] to deeply equal [ StringContaining "재귀 rmSync" ]`). 켠 뒤 같은 명령에 `|지나보내는`을 붙여 23개가 통과했다(손으로 봤다).
- 켜기 전 위반은 열세 곳이다. `pnpm -C web exec eslint --max-warnings 0 .`가 낸 열두 곳(손으로 봤다)은 관리 화면·위젯의 `e2e/stack.ts` 둘, 위젯 시험 셋(`element.test.ts` 두 곳, `fonts.test.ts` 한 곳), `web/tools`의 시험 여섯과 `visual.ts`다. 열세째는 `web/eslint.config.test.ts`의 `afterAll`인데 린트를 돌리기 전에 먼저 고쳐 둬서 그 린트가 세지 않았다. 기준 커밋을 `git grep -n "rmSync(.*recursive: true" 544381eafbeee5d1aacf709ff1cbb5870ac761f2 -- web`으로 손으로 세니 재귀 `rmSync`는 열다섯 곳이고, `maxRetries`가 이미 있던 `judge-trees.ts`(5)와 `assemble.ts`(3)를 빼면 열세 곳이다. 모두 `maxRetries: 5`를 주었다. 판정에서 뺀 자리는 없다.
- 첫 커밋 시도에서 pre-commit의 변이 표 검사(`check-mutations`)가 막았다. `.scratch/web-widget/probes/widget_llm_mutations.toml`이 위젯 `e2e/stack.ts`의 `rmSync` 줄을 원문으로 드는데 이 변경이 그 줄을 바꿨기 때문이다. 표의 `old`와 `new` 두 곳에 `maxRetries: 5`를 더했고, `uv run python tools/mutate.py --staged`가 "문제 0"으로 통과했다(손으로 봤다). 다른 병렬 검사(pytest·web-verify 등)는 그 시도에서 모두 Passed였다.
- 셀프 리뷰 반영(표준·명세 두 축 모두 같은 수를 짚었다): 위 수를 열둘에서 열셋으로 바로잡았다. 명세 축이 문자열 키 `"maxRetries": 5`를 selector가 못 읽어 거짓 양성이 된다고 임시 파일로 대 봤고, 표준 축이 중첩 객체의 `maxRetries`에 속지 않는지 시험이 없다고 짚었다. selector가 키를 식별자와 문자열 둘 다 읽게 고치고(`optionKey`), 걸리는 사례 둘(문자열 키 `recursive`, 안쪽 객체에만 든 `maxRetries`)과 지나는 사례 하나(문자열 키 `maxRetries`)를 더했다. 설정 주석의 보지 못하는 자리는 `rmdirSync`, `satisfies`, 약식 속성, 괄호 접근을 더하고 목록이 전부가 아니라고 적었다. `maxRetries`를 이미 주던 `judge-trees.ts`(5)와 `assemble.ts`(3)는 그대로 두었다.

## 검증(이 세션이 손으로 본 것)

- `uv run ruff check .`·`uv run ruff format --check .`: 통과.
- `uv run python tools/run_checks.py`(셀프 리뷰 반영 전 상태): `web-verify`가 실패했는데 리뷰 서브에이전트가 임시로 둔 `web/tools/zz-probe.ts`의 타입 오류 때문이었고, 파일은 이미 지워졌다. pytest는 2 failed, 6021 passed(977초)였다. 실패는 `tests/channel/cli/test_interrupt.py`(자식이 30초 안에 끝나지 않았다)와 `tests/tools/test_rerun_runner.py`(`test_첫_인계가_나면_새_회차를_열지_않는다`)이고, 이 변경은 파이썬을 건드리지 않았다. 두 파일만 `uv run pytest -q tests/channel/cli/test_interrupt.py tests/tools/test_rerun_runner.py`로 다시 치니 69 passed(201.9초)였다. 전체 실행 때 e2e 둘과 리뷰 서브에이전트 둘이 함께 돌아 부하가 컸다는 것은 어림이다.
- `pnpm -C web verify`(반영 뒤 서식을 맞춘 최종 상태): 96파일 1598개 통과.

## 셀프 리뷰(`/code-review`, base 544381ea)

범위: 파일 14개 변경, 커밋 0개, 미추적 2개. 표준 축은 sonnet·high, 명세 축은 세션 모델이다.

- 반영(고친 것): 위반 수를 열둘에서 열셋으로 바로잡았다(두 축 모두 짚었다). 문자열 키 `"maxRetries"`가 거짓 양성이 되던 selector를 고쳤다. 안쪽 객체 사례를 시험에 더했다. 설정 주석의 보지 못하는 자리를 늘리고 목록이 전부가 아니라고 적었다. 자세한 것은 위 "한 것"의 마지막 항목이다.
- 남긴 것: `maxRetries: undefined`·음수·`recursive: !0`·`fs["rmSync"]`·`rmdirSync`·`satisfies` 같은 가장자리 입력은 지나간다(Minor). 설정 주석에 이름만 적었다. 수용 기준 4번(e2e)은 "쳤다"까지만 덮였다는 명세 축 지적은 맞다. 일지의 e2e 절이 그 한계를 적고 있어 그대로 두었다.

## e2e로 본 것(손으로 봤다)

- `pnpm -C web/apps/widget exec playwright test`: 15 passed(1.6분), 출력 파일에 `EPERM`이 없었다.
- `pnpm -C web/apps/admin exec playwright test` 첫 실행(`| tail -40`으로 앞을 잘라 받았다): 8 passed, 1 failed(`e2e/decision.e2e.ts:39`, `run_finished`가 안 보인다)와 "1 error was not a part of any test"였다. 시험 밖 오류의 본문은 잘려 못 봤다. 같은 `decision.e2e.ts:39` 실패와 시험 밖 오류는 이 변경 전 일지(`2026-10-30-11-admin-settings-theme.md` 47행)에도 있다. 같은 명령을 파일로 받아 다시 친 둘째 실행은 9 passed(52.1초)에 오류가 없었다.
- 따라서 이 변경이 `stack.ts`의 `EPERM`을 없앴다고 말할 수 없다. 첫 실행의 시험 밖 오류가 `EPERM`이었는지 못 봤고 둘째 실행은 지났을 뿐이다. 규칙이 닫은 것은 재시도 없이 끝나는 종류이고, 재시도 뒤에도 나는 `EPERM`이 있으면 새 대기열 행으로 쓴다. `decision.e2e.ts:39` 실패는 이 티켓의 일이 아니다.
