# 2026-11-12 위젯의 실제 모델 e2e에 assistant 사례를 더한다 (base-agent 06)

세션 제목: `feature/06-widget-real-model-assistant-case` (인계하면 `<브랜치> (인계함)`으로 바뀐다)

## 사용자 프롬프트 원문

> 사용자: 다음 작업: .scratch/base-agent/issues/06-widget-real-model-assistant-case.md. 위젯의 실제 모델 e2e로, 위젯에서 assistant에게 물으면 출처가 붙은 답이 화면에 뜨는지 본다
> 다음 단계: 구현
> 어디서: 새 세션. 나란히 여는 3 중 3. 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 06-widget-real-model-assistant-case)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
> 시작 프롬프트: /implement .scratch/base-agent/issues/06-widget-real-model-assistant-case.md
> 브랜치: feature/06-widget-real-model-assistant-case
> 모델: Sonnet 5.5 / high
> 이번 요청 범위: PR과 병합까지

## 한 것 (커밋 전, 워크트리에 있다)

- 워크트리 `06-widget-real-model-assistant-case`에서 브랜치를 `feature/06-widget-real-model-assistant-case`로 바꿨다.
- 티켓 06을 `done`으로 바꾸고 체크박스를 채웠다. `uv run python tools/plan_table.py`로 `.scratch/plan.md`를 다시 만들었다. 이 티켓은 기능의 마지막 열린 티켓이 아니라(04, 05, 07이 열려 있다) 기능 계획의 `**끝:**` 줄은 쓰지 않는다.
- `web/packages/e2e-stack/src/plugins.ts`: 상수 `ASSISTANT_AGENT`, 함수 `pointDocSearchAt(root, url)`(복사한 `mcp/doc-search/plugin.toml`의 `url` 줄 하나만 바꾼다, 줄이 하나가 아니면 던진다), 규칙 파일에 `[agents.assistant]` 세 줄(저장소 `plugins/rules.toml`의 사본이라는 주석과 원본 경로 포함).
- `web/packages/e2e-stack/src/plugins.test.ts`(새 파일): 주소 바꾸기, 주소 줄이 없을 때의 오류, 픽스처의 assistant 표가 저장소 표와 글자 그대로 같은지.
- `web/apps/widget/e2e/env.ts`·`stack.ts`: `AGENT_OS_WIDGET_DOC_SEARCH_URL`이 있으면 `pointDocSearchAt`을 부르고, 실제 모델 모드의 사이트 에이전트에 `assistant`를 더한다.
- `web/apps/widget/e2e/llm-ask.ts`(새 파일, 두 사례의 공용): 질문을 보내 출력 문단을 읽고 주석 `화면의 출력`을 JSON(`{agent, text}`)으로 싣는다. `calc.llm.ts`는 이것을 쓰게 줄였고, `assistant.llm.ts`(새 파일)는 문서 제목("육아휴직 업무편람"), "출처", 갱신일("2026-10-01") 세 낱말만 단언한다. `[1]` 같은 대괄호 번호와 글자 그대로의 비교는 없다.
- `tests/test_widget_llm.py`: 가짜 검색 서버(`tests/fake_doc_search.py`의 `serving`)를 띄워 `AGENT_OS_WIDGET_DOC_SEARCH_URL`과 `DOC_SEARCH_AUTHORIZATION`을 자식 환경에 준다. 서버의 기록 폴더는 `tmp_path_factory`로 `tmp_path` 밖에 둔다(`record.jsonl`이 토큰 합계에 트레이스로 세이는 것을 피한다). `_failures`를 사례별 짝짓기로 바꿨다(`CASES`, `_runs`, `_case_failures`). 통과 수 기준은 2다. 계산 사례만 글자를 견주고 assistant 사례는 그 실행의 `llm_called`와 성공한 `search`를 본다. 서버가 받은 도구 호출에 `search`가 있는지도 본다. 모델 없는 단위 시험 7개를 먼저 빨갛게 보고 구현했다.
- `.scratch/web-widget/probes/widget_llm_mutations.toml`: 바뀐 메시지에 맞춰 앞의 세 변이를 고치고 변이 다섯(10~14)을 끝에 더했다.

## 결정과 고친 것

- 가짜 서버의 `Authorization` 값은 시험용 상수(`Bearer widget-llm-test-token`)다. 서버의 기록에 원문이 실리므로 실제 비밀을 쓰지 않는다.
- 변이 도구가 첫 판의 표지(`가짜 문서 검색 서버가 받은 도구 호출에 search 가 없다`)를 시험 원문에 글자 그대로 있다며 거부했다. 메시지에 값을 넣는 꼴(`받은 도구 호출 [] 에 search 가 없다`)로 고쳤다. 변이 13의 표지는 `+`가 아니라 `-` 쪽(`- allow = ["doc-search:search"]`)이었다.
- 화면의 답을 `run_finished` 출력과 글자로 견주지 않는다(answer-markdown 이 먼저 오든 나중에 오든 깨지지 않게). answer-markdown 03은 아직 `ready-for-agent`라 그 짝짓기와 비교 규칙을 가져오지 않았다. 그 티켓이 들어올 때 이 짝짓기에 맞춘다(그 티켓이 `.scratch/answer-markdown/issues/03-widget-renders-answers-as-markdown.md`에서 같은 짝짓기를 짓는다고 적었다).

## 돌려서 본 것 (이 세션에서)

- `uv run --env-file ../../../.env pytest -m llm_widget`: 통과 1, 217초, 트레이스 2개, 모델 호출 4건, 토큰 합계 16,873(입력 16,611, 출력 262). `assistant`가 `search`를 한 번 불러 "육아휴직 업무편람, 2.1 휴직 기간 (갱신일 2026-10-01)"이 든 답을 냈고, 표본 조각에 심은 지시문은 답에 따라오지 않았다(손으로 트레이스를 읽었다).
- `uv run --env-file ../../../.env pytest -m llm_portal`: 통과 1, 71초, 토큰 합계 6,997.
- 질문 페이지 e2e(`pnpm -C web/apps/portal exec playwright test`): 초록(종료 코드 0).
- 위젯 e2e(`pnpm -C web/apps/widget exec playwright test`): 첫 실행에서 16개 가운데 1개(`widget.e2e.ts:33`, 도구 줄이 5초 안에 선다)가 빨갛고 그 사례만 다시 돌리면 3.7초에 초록이었다(부하로 의심, 다른 세션의 pytest가 함께 돌았다). 전체 재실행 둘은 준비 단계에서 `serve 가 서지 않았다`(출력이 빔)로 끝났다. 손으로 `uv run python -m agent_os.main serve ...`를 쳐 68초, `uv run python -c "import agent_os.main"`을 15초와 11초로 쟀고(`uv run python -c "print(1)"`은 1.3초), 그때 `Win32_Processor`의 `LoadPercentage`가 100이고 python·node 프로세스가 138개 떠 있었다(이 워크트리의 것은 없었다). 기동 대기의 상한이 60초(`process.ts`의 `STARTUP_MS`)이므로 느린 임포트가 그 상한을 넘긴 것으로 본다(어림, 부하의 출처는 재지 않았다). 세 번째 전체 실행은 준비를 통과했고 16개 가운데 12개가 초록, 4개(`widget.e2e.ts`의 33·83·142·168번째 줄 사례, 모두 5초 대기 단언)가 빨갰다. `widget.e2e.ts` 파일만 다시 돌리니 9개 중 8개가 초록이고 142번째 줄 사례만 빨갰다. 빨간 사례가 실행마다 달랐고 그 사례들은 이 변경이 건드리지 않은 실제 모델 없는 경로(`llm`이 꺼진 준비)다. 그래서 부하로 5초 대기를 넘긴 흔들림으로 보지만(어림, 기준 브랜치에서 같은 흔들림이 나는지는 재지 않았다) 초록으로 확정하지 못했다.
- 변이: 13과 14(노드 러너)는 기대대로 빨갰다. 10(갱신일 낱말)과 11(주소 바꾸기 생략)은 실제 모델로 기대대로 빨갰고 그 앞의 기준선은 초록이었다. 12(assistant의 search 성공을 거꾸로 보기)는 돌리지 않았고 같은 단언을 모델 없는 단위 시험이 빨갛게 본다.
- `uv run ruff check .`와 `ruff format --check .`: 초록. `uv run python tools/run_checks.py`: pytest(734.6초)·pyright·run-hooks·check-instructions·check-type-escapes 등 초록, web-verify는 prettier가 `assistant.llm.ts`를 지적해 빨갰고 `prettier --write`로 고친 뒤 `pnpm -C web verify`를 다시 쳐 초록이다. 러너 전체는 다시 치지 않았다. 커밋의 pre-commit이 같은 명령을 돈다.

## 셀프 리뷰 (이어받은 세션, 기준 SHA 9714908a0, 파일 7개 변경과 미추적 3개, 커밋 0)

표준 축은 Critical·Major가 없었고 확정 Minor 둘과 smell 셋을, 명세 축은 문서 잔존 둘과 약한 시험 하나를 냈다.

- 고친 것
  - `tests/test_widget_llm.py`의 `_write_run`의 키워드 전용 불리언 `llm`을 `llm_calls: int`로 바꿨다(CODING_STANDARDS 불리언 플래그 줄).
  - `_annotations`가 JSON이 아닌 주석에서 던지던 것을 빼고 넘기게 했고, 그 사례가 화면의 출력이 빈 것으로 알려지는지 시험을 더했다(`test_JSON_이_아닌_화면_주석은_…`).
  - `plugins.test.ts`: 주소 줄이 없는 사례의 단언을 `주소 줄 하나를 찾지 못했다`로 조이고, 주소 줄이 둘인 사례를 더했다. 판정 조건 `another !== -1`을 잠시 빼면 그 시험이 빨갛다(손으로 봤다).
  - 낡은 문장: `tests/fake_doc_search.py` 머리의 "지금 쓴다" 목록, `plugins.ts` 머리의 "저장소의 계산 에이전트", 프로브 README 41행과 변이 표 머리의 변이 수·모델을 부르는 변이, answer-markdown 03 티켓 34행의 위젯 로케이터 자리(`llm-ask.ts`).
- 남긴 것과 이유
  - ADR 0053 24행의 "`calc.llm.ts` 둘"은 그 ADR이 센 당시의 기록이라 고치지 않는다(ADR의 이력은 결정 단위로 쌓는다).
  - 명세 축의 범위 넘침 셋(assistant에도 하나씩이라는 검사, 가짜 서버가 `search`를 받았는지, 규칙 표의 글자 일치 시험)은 해롭지 않고 실제 사고를 막아 둔다. 명세는 "손으로 맞춘다"였으나 일치 시험이 그 손을 지킨다. 유지한다.
  - smell(`_case_failures`의 calc/else 갈림, `(agent, text)`·`(name, events)` 튜플, `_by_agent`·`shown`·`mine` 이름)은 판단 항목이다. 사례는 둘뿐이고 새 사례는 answer-markdown 03이 짝짓기를 짓는 자리에서 다시 보므로, 지금 타입이나 맵을 들이지 않는다.

## 이어받은 세션이 돌려서 본 것 (2026-11-13)

- 위젯 e2e 전체(`pnpm -C web/apps/widget exec playwright test`): 16개 모두 초록, 2.2분. 앞 세션의 흔들림(실행마다 다른 5초 대기 사례)은 이번에 나지 않았다. 부하가 낮았던 것으로 어림하며 부하는 재지 않았다.
- 변이 1~3(실제 모델): 도구가 기대대로로 판정했다. 첫 실행은 1과 3의 표지가 단위 시험 원문에 글자 그대로 있어 거부되어, 단위 시험의 가짜 통계를 `{'expected': 0, 'skipped': 2, …}`로, 계산 사례의 단언을 `startswith("calc")`와 `화면에 선 출력 ['…']`로 쪼개 표지가 실제 실행에서만 나오게 했다. 3의 실제 출력은 `calc: 화면에 선 출력 [] 이 …`였고 그 꼴로 표지를 바꿨다(결과를 본 뒤 바꾼 기준이다). 13·14(노드 러너)도 기대대로.
- `uv run ruff check .`, `ruff format --check .`, `uv run python tools/run_checks.py`: 모두 초록(pytest 861.6초, web-verify 1052.8초).

## 커밋 (이어받은 세션)

- 커밋 `44830188e`(`test: 위젯 모델 e2e에 assistant 사례를 더한다 (06-widget-real-model-assistant-case)`)를 브랜치에 만들었다. 푸시하지 않았고 PR도 없다.
- 첫 커밋 시도의 pre-commit에서 `tests/channel/cli/test_interrupt.py`의 도구 호출 도중 중단 시험과 `tests/tools/test_probe_kit.py`의 배출 시험이 빨갰다(둘 다 시간 단언). 같은 러너가 직전에는 초록이었고 그 둘만 따로 돌리면 87.78초에 통과했다(손으로 쳤다). 이 변경이 건드리지 않은 시험이라 부하의 흔들림으로 보고(어림, 부하는 재지 않았다) 같은 커밋을 다시 쳐 통과했다.

- 푸시 훅이 `origin/dev`보다 2커밋 뒤처졌다고 막아 `git merge origin/dev`로 합쳤다(충돌 없음, `uv run python tools/plan_table.py --check`와 `sibling_overlap.py` 통과). 이 일지 수정 커밋이 합친 뒤의 전체 pre-commit을 겸한다. 같은 커밋의 앞 시도 둘은 커밋 메시지 제목이 72자를 넘어(83자) 한 번, 이 변경과 무관한 시간 단언 시험(`test_interrupt`·`test_probe_kit`·`test_rerun_runner`)이 빨개 한 번 막혔다. 그 셋만 따로 돌리면 한 사례(`test_rerun_runner`의 두 회차 동시 실행)가 다시 빨갰고 부하(이 PC에 세션이 여럿 돈다)로 어림하며 재지 않았다.

## PR과 봇 회차 (PR 551)

- PR `njh6803/agent-os#551`(머리 `4c27ff824`)을 열었다. 푸시 직전 `coderabbit-review` 서브에이전트(`coderabbit review --agent --include-untracked --base origin/dev`)가 `review_completed`로 끝났고 findings는 0건이었다(서브에이전트의 보고를 옮겼다. `Seat: not assigned`, `Plan: Free`, CLI 0.7.5).
- CI: `gh pr checks`의 `wait_ci.py` 결과가 verify·python·web·e2e·e2e-widget·e2e-portal·visual·ticket 모두 SUCCESS이고 `llm`은 SKIPPED였다(`tools/wait_ci.py 551`의 출력을 읽었다).
- CodeRabbit의 PR 리뷰는 `Review rate limited`(무료 한도)로 리뷰가 없었다. 보안·버그 축은 위 CLI 결과가 대신한다.
- claude-review 첫 회차(코멘트를 읽었다): Critical·Major 없음, Minor 하나와 Nit 하나. 둘 다 고치지 않고 보류한다(보류 이유는 PR 코멘트에도 남겼다).
  - [Minor] `_case_failures`가 `agent == CALC`가 아니면 모두 assistant 규칙으로 판정하므로, 세 번째 사례가 늘면 그 규칙이 조용히 따라붙는다. 사례가 둘뿐이고 새 사례는 answer-markdown 03이 짝짓기를 짓는 자리에서 들어오므로 그때 `elif agent == ASSISTANT`로 좁히고 나머지는 실패로 돌린다.
  - [Nit] `assistant.llm.ts`가 문서 제목·갱신일·질문 문구를 상수로 갖는다. 주석이 표본을 고치면 함께 고치라고 적고 판정이 모델 e2e에서만 나므로, 현재 규모에서는 둔다.

## 이어받을 일

1. 병합까지가 이번 요청 범위였고, 병합 뒤에는 이 브랜치에서 남은 일이 없다.
2. answer-markdown 03이 위젯 로케이터를 `llm-ask.ts`에서 고치는 것으로 티켓을 맞췄다. 그 티켓이 들어올 때 이 변경의 사례별 짝짓기(`tests/test_widget_llm.py`의 `_case_failures`)에 맞추고, 위 Minor(`else`를 `elif agent == ASSISTANT`로 좁힌다)도 그 자리에서 한다.
3. `tests/fake_doc_search.py`를 05 워크트리의 세션(`05-real-model-assistant-answers-with-sources`)도 고치고 있어, 나중에 병합하는 쪽에서 글자 충돌이 날 수 있다(`sibling_overlap.py` 출력).

open-session을 부른다 2026-11-12T16:08Z
