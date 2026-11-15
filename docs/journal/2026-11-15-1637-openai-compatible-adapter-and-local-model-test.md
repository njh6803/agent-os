# 2026-11-15 OpenAI 호환 모델 어댑터와 로컬 모델 시험 (local-model 05)

세션 제목: `feature/05-openai-compatible-adapter-and-local-model-test` (인계하면 `<브랜치> (인계함)`으로 바뀐다)

## 사용자 프롬프트 원문

> 사용자: 다음 작업: .scratch/local-model/issues/05-openai-compatible-adapter-and-local-model-test.md. OpenAI 호환 모델 어댑터와 로컬 모델 시험(llm_local 마커)을 만든다
> 다음 단계: 구현
> 어디서: 새 세션. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고(그 스킬이 사람에게 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 주 체크아웃에서 브랜치를 따지 않고 EnterWorktree(name은 05-openai-compatible-adapter-and-local-model-test)로 새 워크트리에 먼저 들어가 거기서 브랜치를 바꾼다
> 시작 프롬프트: /implement .scratch/local-model/issues/05-openai-compatible-adapter-and-local-model-test.md
> 브랜치: feature/05-openai-compatible-adapter-and-local-model-test
> 모델: Sonnet 5.5 / high
> 읽을 것: docs/journal/2026-11-13-1423-llm-local-command-rents-model-servers.md의 "다음"
> 이어받을 상태: 티켓 03의 PR(njh6803/agent-os#575)이 병합됐다. (1) 일지 "다음" 6의 구조 정리(지우기 경로의 CQS와 Round 제자리 변경, except 안 지우기, run(yes) 불리언, tools/llm_local.py 분리)에 더해, PR 575의 셋째 봇 회차가 낸 새 항목이 PR 코멘트에만 있다. _bring_up의 실패 분기마다 OUT.say(state.invalid_reason)를 되풀이하는 것이다. 05가 이 파일에 기대므로 05 전에 정리할지는 05 세션이 정한다. (2) 이 PR의 봇 회차 회고는 승인할 후보가 없다고 PR 코멘트에만 적었고 일지 "## 회고"에는 없다. (3) 기본 run(-- 없음)은 llm_local 마커의 시험이 생기기 전까지 --collect-only 확인에서 종료 코드 4로 멈춘다. 05가 그 시험을 더하면 풀리고, 이 확인은 50초쯤 든다.
> 확인할 선행 조건: 주 체크아웃 미갱신: 루트는 dev. 병합은 이 워크트리 사본의 next-session merge.md(없으면 SKILL.md)의 "워크트리에서 병합할 때"를 Read로 열어 따른다
> 이번 요청 범위: PR과 병합까지

## 한 것

- 모델 서버 모듈 `src/agent_os/adapters/openai_compatible.py`: `ChatOpenAI`의 하위 클래스로 모델을 만든다. 생성자 인자 넷을 고정하고, 모델마다 쉬는 연결이 없는 전용 비동기 클라이언트를 넘기며, 키는 호출 직전에 환경에서 읽는 함수로 넘긴다. 호출의 예외는 키 값을 가리고 원인을 잇지 않은 내장 예외 넷으로 바꾼다. 모델 소스(`adapters/models.py`)의 `openai-compatible` 갈래가 이 모듈을 부른다(01의 임시 문구를 지웠다).
- 의존성: `langchain-openai==1.6.2`, `openai==3.49.0`. `uv.lock`에 새 패키지 넷(`langchain-openai`, `openai`, `regex`, `tiktoken`)이 들고 판이 바뀐 패키지는 없다. import-linter의 금지 목록 둘에 두 모듈을 더했다.
- 시험: `tests/adapters/test_openai_compatible.py`(가짜 모델 서버 위의 어댑터), `tests/test_main.py`의 calc CLI 시험 둘(가짜 서버로 도구를 부르는 길, 인자가 깨진 도구 호출이 원인 `model_call`로 끝나는 길), `tests/test_local_model_llm.py`(`llm_local` 마커의 calc 시험과 환경 검사). 마커 `llm_local`은 `pyproject.toml`과 `tests/conftest.py`의 `_LLM_MARKERS`에 들었다.
- 문서와 하네스: `docs/constitution/operations.md`의 LLM 테스트 절(마커 넷, `llm_local` 문단), `tech.md`(의존 행과 시험용 모델 서버 행), 헌법 판 3.0.101(형제 PR #576이 3.0.100을 먼저 가져가 비켜 갔다), `.claude/skills/next-session/merge.md`의 "병합 전"(로컬 모델 시험 단계와 비용 확인의 예외, 번호가 하나씩 밀려 참조 다섯을 고쳤다), `CLAUDE.md`, rules, PR 템플릿, 카나리아 명세 둘.
- 잔존 grep: 원문 글자("붙는 어댑터가 아직", "어댑터는 아직", "동작은 아직", "그때까지 `pyproject", "그때까지 이 마커", "값은 `anthropic` 하나")로 살아 있는 문서에서 0건이다. ADR 0057은 결정 시점의 서술이라 두었다.

## 돌려서 본 것

- `uv run python tools/run_checks.py`(pre-commit 러너): check-ticket, lint-imports, zizmor, check-instructions, check-type-escapes, pyright, pyright-linux, run-hooks, pytest, web-verify 모두 통과했다. `ruff check`와 `ruff format --check`도 통과했다.
- 첫 커밋 시도의 pre-commit은 변이 표 검사(`check-mutations`)에서 막혔다. `pyproject.toml`의 `addopts`에 `llm_local` 제외를 더해, 그 줄을 원문으로 든 `.scratch/web-widget/probes/widget_llm_mutations.toml`의 변이 8이 원문 0번이 되었다. 원문과 변경 값을 새 `addopts`에 맞췄고, `tests/test_conftest.py`의 중첩 시험이 이제 `1 passed, 4 deselected`를 단언하므로 표지도 그 값으로 고쳤다(처음에는 표지만 옛 값 `3 deselected`라 도구가 "표지 없음"으로 어긋남을 냈다). 8만 다시 돌려 기준선 `1 passed`, 변이 `1 failed`로 기대대로 판정했다. 프로브 README의 그 행에 적었다.- `-m llm`: 23건 통과, 토큰 합계 262,413(입력 257,128, 출력 5,285), 트레이스 30개, 모델 호출 63건이다.
- 카나리아 둘(`claude_md_llm_widget.toml`, `tests_rule_llm_widget.toml`): 둘 다 통과 4다. `최신 결과` 줄을 고쳤다.
- 카나리아 하나를 더 짓고 돌렸다. `.scratch/local-model/probes/canary/next_session_local_model_test.toml`이 새 `merge.md` "병합 전" 3(로컬 모델 시험)의 문장 둘이 새 세션에 실리는지 본다. 통과 4, 대조군(`--control-commit 8f891430`)은 "없음"이다. `next_session_journal_before_merge.toml`은 번호가 하나씩 밀려 기대 글자를 "5(병합 길)의 …"로 고쳤고 다시 돌려 통과 4다. 두 명세의 `최신 결과` 줄을 고쳤다.
- 카나리아 사전 확인(`tools/canary.py --preflight`)은 바꾼 하네스 파일을 원천으로 든 명세 전부에 돌렸다(통과 77, 실패 120. claude는 돌리지 않았다). 실패는 이 브랜치가 만든 것이 아니다. 대조군 사본의 원천에 카나리아가 이미 있는 것(이미 병합된 PR의 명세)과 옛 판 체크아웃(`agent-canary-*`)이 이 PC에 없는 것이 대부분이고, 실험군 쪽의 "원천에 카나리아가 없다" 일곱 가운데 셋은 이 브랜치가 건드리지 않은 `web-design.md`이며 나머지 넷의 문장(`next-session/SKILL.md` 둘, `handoff.md`, `tidy-checkouts/SKILL.md`)은 `git grep`으로 기준 커밋 `8f891430`에도 없는 것을 확인했다. 이 브랜치가 바꾼 문장을 기대 글자로 든 명세(`claude_md_llm_widget`, `tests_rule_llm_widget`, `http_rule_llm_widget`, `next_session_journal_before_merge`, 새 `next_session_local_model_test`)는 실제 `claude -p`로 돌렸다.
- `/sync-design-system 확인`은 부르지 않았다. 웹 편집이 주석 한 줄(`web/apps/portal/playwright.config.ts`, `web/packages/e2e-stack/src/plugins.ts`)이라 화면 코드가 바뀌지 않았다.
- `uv run pyright`는 0 오류다. 도구가 낸 힌트 하나(`tests/test_main.py`의 `_missing(directory)`의 안 쓰는 인자)는 이 브랜치의 변경에 들지 않은 기존 코드이고(`git diff 8f891430 -- tests/test_main.py`에 그 함수가 없다) 같은 꼴의 호출 자리(`_other_principal(directory)`)와 서명을 맞춘 것이라 두었다.

## 셀프 리뷰

`/code-review`(표준·명세 두 축)와 PR 직전 버그·성능 축을 돌렸다.

- 고친 것: 모델 서버 모듈 독스트링의 문장 다듬기, `ports.py`의 `ModelSource` 독스트링을 제공사로 가르는 어댑터(`ManifestModels`)의 사실로 고침, `.claude/rules/adapters.md`의 내장 예외 문단에 문구 갈래가 넷이라는 것, `merge.md` 번호가 밀린 뒤 남은 참조(`handoff.md`, `merge.md` 머리, `KICKOFF.md`, 대기열 0383, 카나리아 `next_session_journal_before_merge.toml`), 헌법 판 충돌(형제 PR이 3.0.100을 먼저 가져가 3.0.101로 비켜 갔다), `operations.md`의 LLM 테스트 절(무효 회차 종료 코드 나열, `pyproject.toml`·`uv.lock` 변경이 범위에 드는 것).
- 남긴 것(판단): ① 어댑터 시험과 CLI 시험이 가짜 서버 응답을 짓는 보조 함수가 모양이 비슷하다. 두 곳이 서로 다른 층(어댑터 시험은 모델 객체, CLI 시험은 프로세스)이고 합치면 시험 도우미가 한 파일에 기대게 되어 두었다. ② `README.md`와 `.env.example`은 모델 설명이 제공사 하나를 전제하지 않는 문장이라 고칠 것이 없다고 판단했다(티켓 62가 가리킨 자리를 읽어 본 결과다).
- 티켓 03 일지 "다음" 6의 구조 정리(지우기 경로의 CQS, `Round` 제자리 변경, `except` 안에서 지우기, `run(yes)` 불리언, `tools/llm_local.py` 분리, `_bring_up`의 `OUT.say(state.invalid_reason)` 반복)는 05가 `tools/llm_local.py`를 고치지 않고(환경 변수 이름 상수를 import만 한다) 이 PR의 병합 전에 그 명령을 그대로 쓰므로, 명령의 모양을 바꾸지 않으려고 05 전에도 중에도 하지 않았다. 병합 뒤 "다음"에 이어 둔다.
- 03의 PR 575 봇 회차 회고(승인할 후보 없음)는 PR 코멘트에만 있어 이 일지의 "## 회고"로 옮기지 않았다. 단계를 닫는 회고 때 확인한다.
- 기본 `run`(`--` 없음)이 `--collect-only`에서 종료 코드 4로 멈추던 것은 이 티켓이 `llm_local` 시험을 더해 풀린다. 병합 전 실제 시험의 첫 호출에서 확인한다.
