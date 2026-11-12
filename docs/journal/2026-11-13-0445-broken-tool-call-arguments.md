# 2026-11-13 인자가 깨진 도구 호출을 원인 model_call의 실패로 거절한다 (local-model 02)

세션 제목: `feature/02-broken-tool-call-arguments-fail-model-call` (인계하면 `<브랜치> (인계함)`으로 바뀐다)

## 사용자 프롬프트 원문

> 사용자: 다음 작업: .scratch/local-model/issues/02-broken-tool-call-arguments-fail-model-call.md. 인자가 깨진 도구 호출을 원인 model_call의 실패로 거절한다
> 다음 단계: 구현
> 어디서: 새 세션. 나란히 여는 3 중 2. 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 브랜치의 마지막 토막)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
> 시작 프롬프트: /implement .scratch/local-model/issues/02-broken-tool-call-arguments-fail-model-call.md
> 브랜치: feature/02-broken-tool-call-arguments-fail-model-call
> 모델: Sonnet 5.5 / high
> 이어받을 상태: 도구 이름에 키가 실리면 run_failed에 키가 남는 한계는 티켓과 명세가 가리지 않는 한계로 적었다. 막자는 요청이 나오면 명세의 결정을 바꾸는 일이라 사용자에게 다시 묻는다
> 이번 요청 범위: 구현·리뷰·커밋까지

## 한 것

- 워크트리 `02-broken-tool-call-arguments-fail-model-call`에 들어가 브랜치를 `feature/02-broken-tool-call-arguments-fail-model-call`로 바꿨다. 티켓을 `in-progress`로 쓴 뒤 `done`으로 바꾸고 체크박스를 채웠다. `uv run python tools/plan_table.py`를 돌렸다. 이 티켓은 기능의 마지막 열린 티켓이 아니라(01·03·04·05가 열려 있다) 기능 계획의 `**끝:**` 줄은 쓰지 않는다.
- `src/agent_os/core/model.py`의 `reply_from`: 메시지의 `invalid_tool_calls`가 비어 있지 않으면 `ValueError("모델이 낸 도구 호출의 인자가 올바른 JSON 이 아니다: <이름들>")`을 던진다. 이름은 응답의 순서대로 쉼표로 잇고 빈 이름은 `(이름 없음)`이다. 깨진 인자의 글과 라이브러리의 `error` 글은 싣지 않는다. 멀쩡한 호출이 섞여도 응답 전체를 거절한다. 확인은 `invalid_tool_calls`만 본다.
- `tests/core/test_run.py`: 깨진 호출 다섯 사례(하나, 둘의 순서, 이름이 빔, 이름이 빈 것이 뒤, 멀쩡한 호출과 섞임)가 트레이스 `[run_started, run_failed]`, 원인 `model_call`, 문구에 도구 이름 포함, 깨진 인자의 글(`sk-leak`)과 라이브러리 `error`의 글이 없음을 본다. 이름만 빈 멀쩡한 호출이 이 확인에 걸리지 않고 루프로 가서 `tool_called(ok=false)`가 되는 시험을 더했다.
- `.claude/rules/core.md`의 실패 정책에 한 문장을 더했다(`writing-for-agents`를 먼저 불렀다). 루프의 모델 호출이 그렇고, 도구를 붙이지 않는 대화 요약에는 이 길이 없다고 한정했다.
- `.scratch/local-model/probes/broken_tool_calls_mutations.toml`(변이 셋)과 프로브 README의 한 줄, 카나리아 명세 `.scratch/local-model/probes/canary/core_rule_broken_tool_call.toml`.

## 돌려서 본 것

- 첫 빨강: 새 시험 여섯 가운데 다섯이 빨강이었다. 지금까지 실행은 `run_started, llm_called, …, run_finished`로 끝났다(`At index 1 diff: 'llm_called' != 'run_failed'`). 이름만 빈 멀쩡한 호출 시험은 구현 전부터 초록인 가드다.
- 구현 뒤 `tests/core/test_run.py`와 `tests/core/test_model.py`(Anthropic 실제 호출 제외) 484개 초록.
- 변이 도구(`tools/mutate.py`): 셋 모두 기대대로 빨강. 첫 변이(이름이 빈 멀쩡한 호출도 거절)가 구현 전부터 초록이던 가드의 이빨을 본다. 첫 판의 표지(`Left contains`, `올바른 JSON 이 아니다: add, `)는 실제 실패 출력과 달라 어긋남으로 나왔고, 출력에서 본 문구(`'run_failed' != 'llm_called'`, `SON 이 아니다: (이름 없음)`)로 고쳐 다시 돌렸다(결과를 본 뒤 바꾼 기준이다).
- `uv run ruff check .`, `ruff format --check .`: 초록.
- `uv run python tools/run_checks.py`(셀프 리뷰와 겹쳐 돌았다): pyright·pyright-linux·lint-imports·check-instructions·check-type-escapes·run-hooks·web-verify 초록. pytest는 7230 통과, 3 실패(`tests/channel/cli/test_interrupt.py`의 Ctrl-C 시험 셋). 그 파일만 단독으로 돌리면 6개 모두 통과(119초)였다. 서브에이전트 둘과 함께 돌던 부하 탓으로 어림하며 부하는 재지 않았다. 같은 시험이 앞선 `06-widget-real-model-assistant-case` 일지에서도 부하로 흔들렸다. 커밋의 pre-commit이 러너를 다시 돈다.
- `uv run --env-file ../../../.env pytest -m llm`: 9개 통과, 238초, 토큰 합계 63,447.
- 카나리아(`tools/canary.py`, claude 2.1.322): 통과 4(실험군 3 모두 `invalid_tool_calls`와 `reply_from`을 옮겼고 대조군은 "없음"). 첫 사전 확인은 표지 `core/model.py`가 `git status`의 바뀐 경로에 들어 있어 답이 그쪽에서 올 수 있다며 막았다. 그 표지와 질문 항목을 뺐다.

## 셀프 리뷰 (기준 SHA a4eea81ff, 변경 4개와 미추적 1개, 커밋 0)

표준 축은 Critical·Major가 없었고 Minor 둘과 판단 항목 둘을, 명세 축은 Critical·Major 없이 사소한 불일치 하나를 냈다.

- 고친 것
  - 프로브 README의 표에 `broken_tool_calls_mutations.toml` 줄을 더했다(프로브마다 README 표에 한 줄이라는 규약, `docs/agents/issue-tracker.md`).
  - `core.md`의 새 문장이 대화 요약 경로까지 포함하는 것처럼 읽혔다. `reply_from`을 부르는 곳은 둘이고 요약 쪽은 `cause="conversation_summary"`로 바뀐다. 문장에 "루프의 모델 호출이 그렇다. 도구를 붙이지 않는 대화 요약에는 이 길이 없다"를 더했다.
  - `reply_from`의 독스트링에서 라이브러리가 예외 없이 `invalid_tool_calls`에 넣는다는 서술을 비스트리밍 응답에서만 맞는 것으로 한정했다. 서브에이전트가 스트리밍 조각 경로(`AIMessageChunk`)는 잘린 JSON을 고쳐 `tool_calls`로 만들기도 한다고 손으로 대 봤다(그 프로브는 커밋하지 않았다).
  - 변이 표 머리의 시험 절 이름을 실제 위치로 고쳤다. 시험 헬퍼 인자 `id`를 `call_id`로 바꿨다(내장 이름을 가렸다).
- 남긴 것과 이유
  - `reply_from` 단위 경계(이름이 `None`, `invalid_tool_calls=[]`)를 `tests/core/test_model.py`에서 따로 시험하지 않았다. 서브에이전트가 손으로 대 봤고(맞았다), `test_run.py`의 통합 시험이 같은 확인을 지난다. 티켓의 시험 항목이 core 시험 하나를 요구했다.
  - 대화 요약 경로의 시험은 더하지 않았다. 요약에는 도구가 붙지 않아 깨진 호출이 나올 길이 없다는 것이 명세 174행의 어림이다.
  - 이름에 키가 실리면 `run_failed`에 남는 한계는 티켓과 명세가 이미 가리지 않는 한계로 적었다(막자는 요청은 명세의 결정을 바꾸는 일이라 사용자에게 다시 묻는다).
- 다시 돌린 명령: 변이 셋, `-m llm`, 카나리아는 리뷰 반영 뒤에 돌렸다. ruff 둘과 러너 전체는 반영 전(러너)과 후(ruff)에 돌렸고, 커밋 직전의 손으로 치는 다섯은 pre-commit 결과로 갈음한다.

## 커밋

- 커밋 `17fc95d1c`(`feat: 인자가 깨진 호출을 거절한다 (02-broken-tool-call-arguments-fail-model-call)`)를 브랜치에 만들었다. 푸시하지 않았고 PR도 없다. 이 세션의 요청 범위가 구현·리뷰·커밋까지라 인계하지 않았다(`handoff.md` 1).
- pre-commit이 네 번째 시도에서 통과했다. 앞의 세 시도는 이 변경이 건드리지 않은 시간 단언 시험이 빨개 막혔다. 첫째는 `tests/channel/cli/test_interrupt.py`의 도구 호출 도중 중단 시험(30초 안에 끝나지 않았다), 둘째는 `tests/tools/test_probe_kit.py`의 배출 시험, 셋째는 `test_interrupt.py`의 셋과 `tests/tools/test_hook_push_behind_main.py`의 시간 제한 시험이었다. 앞의 둘은 따로 돌리면 통과했고(`test_interrupt.py` 6개 119초, `test_probe_kit.py` 15개 227초) 같은 PC의 부하(세 번째 실패 직후 `Win32_Processor`의 `LoadPercentage`가 100, python·node 프로세스 148개, 이 워크트리의 것은 없었다. 손으로 쟀다)로 어림한다. 부하의 출처는 재지 않았고 기준 브랜치에서 같은 흔들림이 나는지도 재지 않았다. 앞선 세션의 일지(2026-11-12-2327)에도 같은 두 시험의 부하 흔들림이 적혀 있다.
- 첫 시도의 인용 대조가 이 일지의 따옴표 문구(저장소에 글자 그대로 없는 문장)를 경고해, 따옴표를 떼어 고쳤다.

## 이어받을 일

1. 이 티켓의 PR은 `core/model.py`를 고친다. ADR 0058의 로컬 모델 시험 병합 조건 범위에 들지만 돌릴 시험이 아직 없어 조건이 붙지 않는다. 05의 로컬 모델 시험이 이 변경까지 지난다(티켓 본문).
2. 01(계약)과 `tests/core/test_model.py`를 함께 고칠 수 있다. 나중에 병합하는 쪽이 개발 브랜치를 합쳐 푼다.
3. `.claude/rules/core.md`는 다른 세션의 PR도 고친다. 병합 충돌 후보다.
