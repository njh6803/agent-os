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

## 인계 (커밋 뒤)

컨텍스트가 문턱을 넘은 채 커밋 뒤 경계에 와서 인계한다. 이 세션의 제목은 `feature/05-openai-compatible-adapter-and-local-model-test (인계함)`으로 바뀐다.

- 커밋 `1b9f7b192`(pre-commit 통과)까지 했고 푸시도 PR도 아직 없다. 첫 시도는 변이 표 검사(`check-mutations`)에서 막혀 위 "돌려서 본 것"의 둘째 줄대로 고쳤다.
- 남은 일: ① `origin/dev`(PR #576, `ee01b0574`)를 이 브랜치에 합친다. 이 브랜치와 같이 고친 파일은 `.github/PULL_REQUEST_TEMPLATE.md`, `.github/workflows/ci.yml`, `CLAUDE.md`, `docs/constitution/README.md`, `docs/constitution/operations.md`(글자 충돌 후보)이고 dev의 헌법 판은 3.0.100이라 이 브랜치의 3.0.101을 그대로 둔다. 합친 뒤 게이트와 `sibling_overlap.py`를 다시 본다. ② 푸시하고 PR을 연다(티켓은 done). ③ `merge.md` 2의 봇 회차. ④ `merge.md` 3의 로컬 모델 시험: `uv run --env-file ../../../.env python tools/llm_local.py run`을 `--yes` 없이 먼저 쳐 예상 비용을 사용자에게 보이고 확인을 받은 뒤 `--yes`로 백그라운드에 띄운다. 두 모델 모두 통과해야 하고, 시험한 커밋 뒤에 범위에 드는 변경을 더 커밋하면 기록은 무효다. 합치는 일과 봇 회차의 고침은 시험 전에 끝낸다. 결과를 이 일지와 PR 코멘트에 옮기고 티켓 "병합 전"의 상자 셋과 "검증"의 마지막 상자를 그때 체크한다. ⑤ 병합과 `sweep`.
- 이 세션이 어림한 비용(웹 요약의 단가, 2026-11-13자이고 원문으로 확인하지 않았다): 구성 하나당 30분이면 약 $0.27~0.59, 90분 상한이면 $0.81~1.77. 파드는 A5000 둘이 시간당 $0.54로 먼저 시도하고 못 구하면 RTX 3090 $1.00, A40 $1.18, 공유 A40 $0.59 순이며 타이머가 90분 뒤 지운다. 실제 값은 `--yes` 없는 `run`이 찍는 예상 비용으로 다시 본다.
- 저장소 루트에 내 명령이 깨진 경로로 만든 임시물 셋(추적하지 않는다)이 남았다: `UsersUserAppDataLocalTempclaude9060abe0b92613e974a416ce-0986-4c38-a94e-784e4e22d04cscratchpadcanary-claude-md/`, 같은 접두의 `...canary-tests-rule/`, `C` 뒤 깨진 글자로 시작하는 `...scratchpadpreflight_all.txt`. `rm`을 안전 검사가 막아 지우지 못했다. 커밋에 싣지 않는다(경로를 지정해 스테이지한다). 지울 수 있으면 지우고, 지우지 못하면 PR 뒤 정리를 사용자에게 알린다.
- 티켓 03 일지 "다음" 6의 구조 정리와 PR 575 회고 확인은 아래 "셀프 리뷰"의 판단대로 병합 뒤 "다음"으로 넘긴다(06이 남아 단계를 닫는 회고는 아직 아니다).
- `check-quotes`의 경고 하나(위 "한 것"의 잔존 grep 줄의 따옴표 글자들이 저장소에 이제 없다)는 막지 않는 경고이고 그 글자들이 지운 원문의 기록이라 두었다.
- open-session을 부른다 2026-11-15T08:38Z
- 인계 못함 커밋 뒤 (open_session.ps1 호출을 자동 모드 분류기가 거부했다. 제목은 되돌렸고 이 세션이 잇는다. 워크트리 잠금은 이미 풀렸고 다시 잠그지 않는다)

## 셀프 리뷰

`/code-review`(표준·명세 두 축)와 PR 직전 버그·성능 축을 돌렸다.

- 고친 것: 모델 서버 모듈 독스트링의 문장 다듬기, `ports.py`의 `ModelSource` 독스트링을 제공사로 가르는 어댑터(`ManifestModels`)의 사실로 고침, `.claude/rules/adapters.md`의 내장 예외 문단에 문구 갈래가 넷이라는 것, `merge.md` 번호가 밀린 뒤 남은 참조(`handoff.md`, `merge.md` 머리, `KICKOFF.md`, 대기열 0383, 카나리아 `next_session_journal_before_merge.toml`), 헌법 판 충돌(형제 PR이 3.0.100을 먼저 가져가 3.0.101로 비켜 갔다), `operations.md`의 LLM 테스트 절(무효 회차 종료 코드 나열, `pyproject.toml`·`uv.lock` 변경이 범위에 드는 것).
- 남긴 것(판단): ① 어댑터 시험과 CLI 시험이 가짜 서버 응답을 짓는 보조 함수가 모양이 비슷하다. 두 곳이 서로 다른 층(어댑터 시험은 모델 객체, CLI 시험은 프로세스)이고 합치면 시험 도우미가 한 파일에 기대게 되어 두었다. ② `README.md`와 `.env.example`은 모델 설명이 제공사 하나를 전제하지 않는 문장이라 고칠 것이 없다고 판단했다(티켓 62가 가리킨 자리를 읽어 본 결과다).
- 티켓 03 일지 "다음" 6의 구조 정리(지우기 경로의 CQS, `Round` 제자리 변경, `except` 안에서 지우기, `run(yes)` 불리언, `tools/llm_local.py` 분리, `_bring_up`의 `OUT.say(state.invalid_reason)` 반복)는 05가 `tools/llm_local.py`를 고치지 않고(환경 변수 이름 상수를 import만 한다) 이 PR의 병합 전에 그 명령을 그대로 쓰므로, 명령의 모양을 바꾸지 않으려고 05 전에도 중에도 하지 않았다. 병합 뒤 "다음"에 이어 둔다.
- 03의 PR 575 봇 회차 회고(승인할 후보 없음)는 PR 코멘트에만 있어 이 일지의 "## 회고"로 옮기지 않았다. 단계를 닫는 회고 때 확인한다.
- 기본 `run`(`--` 없음)이 `--collect-only`에서 종료 코드 4로 멈추던 것은 이 티켓이 `llm_local` 시험을 더해 풀린다. 병합 전 실제 시험의 첫 호출에서 확인한다.

## 봇 회차

PR 578을 연 뒤 첫 회차(CodeRabbit, claude-review)의 지적을 건별로 판단했다. 첫 회차라 Minor와 Nit도 건별로 본다.

- Minor(PR 템플릿): 체크리스트의 `llm_local` 안내가 `--yes`를 먼저 붙여 치는 것처럼 읽혔다. 비용을 확인받은 뒤에 `--yes`를 붙인다는 순서가 `CLAUDE.md`와 어긋났으므로 고쳤다(`.github/PULL_REQUEST_TEMPLATE.md`).
- Critical(어댑터): 환경 변수 `OPENAI_CUSTOM_HEADERS`에 `Authorization`이 들어 있으면, 서버가 그 값을 오류 문구에 되울릴 때 어댑터가 가리지 못한다는 지적이다. 가짜 서버로 재 보니 라이브러리는 환경의 `Authorization`을 키에서 만든 헤더보다 앞서 보낸다(열기에서 `Bearer <환경 값>`을 서버가 받는 것을 표지로 확인했다). 그 헤더만 떼어 내려면 `default_headers`를 직접 주어야 하는데, 그러면 키 함수까지 대체되므로 깨끗하게 막을 길이 없다. 그래서 막지 않고, 서버가 되울린 그 값(전체와 스킴을 뗀 자격 증명 부분)을 키처럼 `***`로 가린다(`_ambient_authorizations`). 다른 이름의 헤더에 실은 비밀은 가리지 않으며, 이 한계는 모듈 독스트링의 알려진 한계 둘째에 적었다. 시험은 실패하는 것을 먼저 보고(키 변수 있음과 없음 두 갈래) 고쳐 통과시켰다.
- Nit(claude-review): 문구 갈래를 둘로 줄이자는 제안이다. 갈래 넷은 서버가 무엇을 되울릴 수 있는지(상태 오류, 연결 오류, 응답 검증 오류, 그 밖)에 따라 가리는 내용이 달라서 나눈 것이므로 받지 않았다. 그 이유를 PR 코멘트에 적었다.
- 손으로 본 것: 가짜 서버로 헤더 우선순위를 잰 스크래치 스크립트(`PYTHONPATH=. uv run python <스크래치>/env_auth_header_check.py`)를 돌려 위 사실을 확인했다. 스크립트는 저장소에 싣지 않았다. 근거 문장은 이 일지가 원천이다.

## 로컬 모델 시험

`--yes` 없는 `run`은 수집 단계(`--collect-only`)를 통과하고 종료 코드 4로 멈추며 예상 비용을 찍었다(A5000 파드 2개 시간당 $0.54, 어림 30분 $0.27, 최악 90분 $0.81. 못 구하면 RTX 3090 $1.00, A40 $1.18, 공유 A40 $0.59 순. 단가는 2026-11-13의 웹 요약이라 원문과 대조하지 않았다). 03이 남긴 "`llm_local` 시험이 없으면 기본 `run`이 종료 코드 4로 멈춘다"는 이 티켓의 시험 파일로 풀린 것을 이 호출에서 확인했다.

비용을 사용자에게 보이고 받은 답:

> 사용자: "돌린다 (Recommended)" 선택. 서버가 실제로 뜬 한 구성 기준으로 어림 $0.27~0.59, 90분 상한까지 가도 $0.81~1.77 안에서 두 모델 시험을 돌리고, 통과하면 병합까지 이어 간다.

시험한 커밋은 `e9d42be6c`다. 결과는 아래에 이어 적는다.

### 첫 실제 시험: 실패 (2026-11-15 09:45Z)

`uv run --env-file ../../../.env python tools/llm_local.py run --yes`를 시험한 커밋 `e9d42be6c`에서 한 번 쳤다. 종료 코드 1이고 병합 조건(두 모델 통과)을 채우지 못했다.

- 서버 띄우기: RTX A5000 둘은 "no longer any instances available"로, RTX 3090 둘도 같은 이유로 못 구했고, A40 파드 둘이 떴다(시간당 $1.18, 단가표 2026-11-13). Terraform은 두 번 실패하며 파드 하나가 만들어진 뒤 다른 하나가 재고 부족으로 거절되었고, 도구가 다음 후보로 넘어갔다. 출력에 GraphQL 401 경고가 찍혔으나 실행에는 영향이 없었다. Terraform 출력 가림은 일어났다(`terraform_output_masked: true`).
- 엔진: vLLM 0.33.0(이미지 `vllm/vllm-openai:v0.33.0`). 서버 옵션은 `skt/A.X-4.0-Light`에 `--enable-auto-tool-choice --tool-call-parser hermes`, `openai/gpt-oss-20b`에 `--enable-auto-tool-choice --tool-call-parser openai`.
- 결과: 통과 1, 실패 1(`[1]`). **정정(2026-11-15 10:50Z)**: 이 줄을 처음에는 `[1]`을 `openai/gpt-oss-20b`로 적었는데 틀렸다. 시험 이름의 `[1]`은 모델 번호 1이고, 모델 번호 1은 `skt/A.X-4.0-Light`다(Terraform 출력의 `n = "1"`). 실제로는 `gpt-oss-20b`(번호 2)가 통과했고 `skt/A.X-4.0-Light`가 실패했다(둘째 시험의 트레이스로 확인했다). 토큰 합계 5,437(입력 5,343, 출력 94), 트레이스 2개, 모델 호출 3건. 걸린 시간 178.1초(시험 44.48초). 실제 청구는 확인하지 않았다(178초에 시간당 $1.18이면 어림 $0.06 안쪽이다).
- 실패 단언: `assert "tool_called" in types`. 트레이스의 종류가 `['run_started', 'llm_called', 'run_finished']`였다. 그 앞 단언(종료 코드 0과 출력에 `42`)은 통과했다. 곧 실패한 모델(위 정정대로 `skt/A.X-4.0-Light`)이 요청 "17 더하기 25는?"에 도구를 쓰지 않고 직접 42로 답했다. 다른 모델은 같은 어댑터와 같은 요청으로 `tool_called`까지 통과했으므로 어댑터가 도구 목록을 싣는 길은 맞다.
- 원인 판단: calc의 머리 문장이 "도구가 있으면 도구로 계산한다"로 권고일 뿐이고, 17+25는 모델이 도구 없이 답할 수 있는 계산이다. 시험이 요구하는 것(도구 호출이 트레이스에 남는다)이 모델의 재량에 걸려 있다. 어댑터의 결함이라는 증거는 없다. 확인하지 못한 것: 그 실행의 요청 본문(서버가 받은 `tools` 필드)은 보지 못했다.
- 뒤처리: `sweep`을 쳐 두 상태 폴더를 치웠고 남은 파드는 없었다.
- 원칙 II에 따라 시험을 그 자리에서 고치지 않고 멈췄다. 고치는 방향(요청 문장에 도구 사용을 명시하는 것 등)은 사용자의 판단으로 넘긴다. 시험 파일은 병합 조건의 범위라 고치면 새 커밋과 새 시험(과금)이 든다.

사용자 답: 실패 보고를 보고 "고치고 다시 돌린다"를 골랐다. 고친 것은 `tests/test_local_model_llm.py`의 요청 문장 하나다. "17 더하기 25는?"을 "add 도구로 17 더하기 25를 계산해 줘"로 바꿨고 단언은 그대로다(도구 호출이 트레이스에 남아야 한다). 이 시험은 실제 모델이 있어야 돌아 로컬에서 빨강을 먼저 볼 수 없었고, 첫 실제 시험의 실패가 그 빨강이다. 고친 뒤의 시험은 병합 전 실제 시험으로만 확인한다. 같은 `-m llm_local`이 아닌 시험 일곱은 로컬에서 통과했다.

### 재실행 비용 확인

고친 커밋 `f85ae474b`로 다시 돌리기 전에 비용을 사용자에게 다시 보이고 받은 답:

> 사용자: "다시 돌린다 (Recommended)" 선택. 최악의 경우 한 구성 기준 $0.81~1.77 안에서 두 모델 시험을 다시 돌리고, 통과하면 병합까지 이어 간다. 단가표는 지난 실행과 같다(2026-11-13의 웹 요약, 원문과 대조하지 않았다).

푸시 뒤 CI는 모두 초록이고 claude-review는 성공이다. CodeRabbit은 "수동 리뷰 필요"로 건너뛰어 `@coderabbitai review`를 남겼다.

### 둘째 실제 시험: 같은 모델이 같은 단언에서 실패 (2026-11-15 10:31Z)

고친 커밋 `f85ae474b`로 `run --yes`를 다시 쳤다. 종료 코드 1이고 병합 조건을 채우지 못했다.

- 서버 띄우기: A5000 둘, 3090 둘은 재고 부족으로 거절되었고, A40 파드 둘도 하나만 만들어지고 하나가 거절되어, 마지막 후보인 공유 A40 한 장(시간당 $0.59)에 두 모델을 올렸다(포트 8000과 8001, `--gpu-memory-utilization 0.45 --kv-cache-memory=4294967296`). 같은 실패가 파드 배치(첫 시험)와 공유 배치(이번)에서 났으므로 배치 탓은 아니다.
- 결과: 통과 1, 실패 1(`[1]` = `skt/A.X-4.0-Light`. 첫 시험 기록의 정정을 보라), 같은 단언 `assert "tool_called" in types`, 트레이스 종류 `['run_started', 'llm_called', 'run_finished']`. 요청이 "add 도구로 17 더하기 25를 계산해 줘"인데도 도구를 부르지 않았다. 통과한 `gpt-oss-20b`는 `get-sum`(`everything` 서버 2.3.0의 덧셈 도구 이름. `add`가 아니다)을 `{"a":17,"b":25}`로 불러 `tool_called`와 최종 답 `42`까지 갔다.
- 트레이스로 본 것(상태 폴더의 `basetemp`에 남아 있었다): 실패한 `skt/A.X-4.0-Light`의 `llm_called`는 입력 2,581토큰, 출력 2토큰, `text` `"42"`, `tool_calls` 빈 열이다. 입력이 통과한 모델의 1,364보다 큰 것은 도구 목록이 그 모델의 대화 틀에 실렸다는 쪽의 정황이다(확정은 아니다. 서버가 받은 요청 본문은 보지 못했다). 곧 어댑터가 도구를 싣지 않은 것이 아니라 이 모델이 도구 없이 짧게 답한 것으로 읽힌다. 토큰 합계 5,502(입력 5,360, 출력 142), 모델 호출 3건, 걸린 시간 260.9초, 시험 51.46초. 실제 청구는 확인하지 않았다(어림 $0.05 안쪽).
- 판단: 첫 시험 뒤에 세운 가설("요청이 도구를 권고할 뿐이라 모델이 암산한다")이 틀렸다. 도구를 요청에 적었는데도 같다. CLAUDE.md 작업 규약 6(같은 시험이 두 번 연속 실패하면 추측 수정을 멈춘다)에 따라 요청 문장을 더 고치지 않고 `diagnosing-bugs`로 간다. 후보는 ① 도구 목록이 이 모델의 요청에 실리지 않는다(어댑터나 라이브러리 쪽), ② 서버(vLLM의 `openai` 도구 호출 파서)가 도구 호출을 `tool_calls`로 못 내고 본문에 흘린다, ③ 모델이 도구를 정말 안 쓴다. 원천인 응답 본문을 아직 보지 못했다.

### 진단 탐침 (2026-11-15 10:45Z, 공유 A40 한 장, 커밋 `f85ae474b`)

`diagnosing-bugs`의 순서로 추측 수정을 멈추고 `llm_local.py run --yes -- uv run python <탐침>`으로 같은 서버에 탐침(스크래치패드의 `probe_ax_tools.py`, 저장소에 싣지 않았다)을 돌렸다. 16회차 모두 측정이다(표지 없는 회차 0). 걸린 시간 493.6초, 어림 비용 $0.1 안쪽(공유 A40 시간당 $0.59, 실제 청구는 확인하지 않았다).

- 양성 대조: 지난 시험의 실패 입력("add 도구로 17 더하기 25를 계산해 줘")을 글자 그대로 CLI로 다시 넣으면 모델 1(`skt/A.X-4.0-Light`)이 두 번 모두 같은 실패(`tool_called=False`, 출력 `42`)를 냈고, 모델 2(`gpt-oss-20b`)는 `tool_called=True`였다. 그래서 아래 결과는 지난 실패를 설명한다.
- 요청 문장은 원인이 아니다. 모델 1은 "get-sum 도구로 …"(출력 `get-sum 도구를 사용하여 17과 25를 더하면 42입니다.`), "48271 더하기 93659는?"(`1418128`, 맞는 값은 141930이므로 틀린 암산이다), "get-sum 도구로 계산하고 도구가 돌려준 결과를 그대로 답해 줘" 모두 도구를 부르지 않았다. 모델 2도 큰 수의 덧셈은 암산했다(`141930`).
- 서버로 직접 요청(OpenAI 클라이언트, 도구는 `get-sum` 하나)하면 모델 1도 `tool_choice`가 `auto`·`required`·이름 지정 모두에서 `get-sum`을 `{"a": 17, "b": 25}`로 불렀다. 도구를 넣으면 서버가 센 prompt 토큰이 71에서 287로 늘어, 도구 목록은 모델의 대화 틀에 실린다. 곧 서버의 `hermes` 파서와 모델의 도구 호출 능력 자체는 문제가 없다.
- 어댑터의 요청 본문(가짜 모델 서버로 받아 냈다, `probe_adapter_body.py`)은 `messages`, `model`, `stream: false`, `temperature: 0`, `tools`뿐이고 낯선 필드가 없다. 도구는 16개이고 열여섯 스키마 모두에 `$schema` 키가 붙는다. 속성이 있는 열한 도구는 속성마다 설명이 붙고, 속성이 없는 도구가 다섯이다. 직접 요청의 탐침은 도구 하나에 `$schema`가 없었다.
- 결론: 어댑터 결함이라는 증거는 없다(보낸 본문이 평범하다). 같은 모델이 도구 하나일 때는 부르고 시험 경로(도구 16개, 입력 2,581토큰)에서는 안 부른다. 원인은 둘 가운데 하나로 좁혀졌지만 가르지 못했다. (가) 도구 16개가 이 모델의 도구 선택을 망친다. (나) 스키마의 `$schema` 키 등 모양 차이다. 이 탐침은 두 해석을 가르는 갈래(실제 본문을 그대로 다시 보내는 갈래와 도구를 줄이거나 `$schema`를 뗀 갈래)를 두지 않았다.
- 시험 설계의 쟁점: 시험은 calc의 실제 도구 구성(`everything`의 16개)으로 두 모델이 모두 도구를 부르기를 요구한다. 모델 1이 이 구성에서 못 부른다면, ADR 0058이 정한 모델 구성이나 시험이 요구하는 것 가운데 하나를 사용자와 정해야 한다. 이는 06(기본 에이전트 사례를 로컬 모델에서 도는 것)에도 걸리는 정보다.

### 가르는 탐침 (2026-11-15 11:0x Z, 공유 A40 한 장, 커밋 `f85ae474b`)

어댑터가 가짜 서버로 보낸 요청 본문(`probe_adapter_body.py`가 저장한 JSON)을 같은 서버에 직접 다시 보냈다(스크래치패드의 `probe_ax_split.py`, 저장소에 싣지 않았다). 14회차 모두 측정이다(표지 없는 회차 0). 걸린 시간 235.5초, 어림 비용 $0.05 안쪽(실제 청구는 확인하지 않았다).

- 양성 대조 성립: R0(본문 그대로, 도구 16개)이 두 번 모두 도구를 부르지 않았고(`finish=stop`, 본문 `42`) 서버가 센 prompt 토큰이 2,581로 지난 시험의 입력과 정확히 같았다. 이 탐침은 CLI 경로의 실패를 재현한다.
- 도구 개수와 `$schema`는 단독 원인이 아니다. 도구 16개에서 `$schema`를 떼도(R2) 부르지 않았고(prompt 2,197), 도구를 하나로 줄여도(R1 `$schema` 있음 325, R3 `$schema` 없음 301) 부르지 않았다. 4개(R4)와 8개(R5)와 `get-sum`을 맨 앞에 둔 16개(R6)도 부르지 않았다. 4개일 때는 본문에 "get-sum 도구로 17과 25를 더한다.\n\n42"를 적었다. 도구를 부르는 대신 부른다고 서술했다.
- 모든 회차에서 같은 입력의 두 번이 같은 결과였다(둘씩 보냈다).
- 이 결과는 앞의 진단 탐침과 어긋난다. 거기서는 같은 메시지와 도구 하나(`get-sum`, 속성 설명 없음, `$schema` 없음)를 `tool_choice`를 명시해 보내면 부름이 `auto`·`required`·이름 지정 모두에서 났다(prompt 287). 어긋나는 점은 둘이다. 어댑터 본문은 `tool_choice`를 싣지 않고, 어댑터의 `get-sum`은 속성 `a`·`b`에 `description`("First number", "Second number")이 붙는다(prompt 301과 287의 14토큰 차). 이 탐침은 둘을 서로 가르지 못했다. 첫 탐침의 `tool_choice` 명시 여부와 속성 설명 여부가 겹쳐 있다.
- 읽는 법(어림): 어댑터 쪽 결함이 있다면 후보는 `tool_choice` 없음이다. OpenAI 규약에서는 도구가 있고 `tool_choice`가 없으면 `auto`와 같지만, 서버(vLLM 0.33.0의 `hermes` 파서)가 이 모델에서 다르게 다루는지는 보지 못했다. `gpt-oss-20b`는 같은 본문(`tool_choice` 없음)에서 도구를 불렀으므로, 서버가 `tool_choice` 없음을 일반적으로 못 받는 것은 아니다.

### 교차 탐침: 원인은 도구 스키마의 모양이다 (2026-11-15 11:1x Z, 공유 A40 한 장, 커밋 `f85ae474b`)

`tool_choice`(생략/`auto`)와 `get-sum`의 스키마 네 모양을 교차했다(스크래치패드의 `probe_ax_cross.py`, 저장소에 싣지 않았다). 18회차 모두 측정이다. 걸린 시간 221.3초, 어림 비용 $0.05 안쪽(실제 청구는 확인하지 않았다). 같은 갈래 두 번은 모두 같은 결과였다.

- 양성 대조 둘이 앞 탐침을 재현했다. 단순한 스키마(속성 설명 없음, `$schema` 없음)에 `tool_choice: auto`는 도구를 불렀고, 어댑터 본문 그대로의 `get-sum`에 `tool_choice` 생략은 안 불렀다.
- `tool_choice`는 원인이 아니다. 생략과 `auto`가 네 모양 모두에서 같은 결과였다.
- 원인은 스키마의 모양이다. 속성 설명도 `$schema`도 없는 스키마에서만 `skt/A.X-4.0-Light`가 도구를 불렀고(prompt 287, 생략에서도), 속성 설명만 더해도(301), `$schema`만 더해도(311) 안 불렀다. 둘 다 있는 어댑터 본문 그대로(325)와 도구 16개 본문(2,581, `tool_choice: auto`를 줘도)도 안 불렀다.
- 곧 이 모델은 vLLM의 `hermes` 파서 아래에서 실제 MCP 서버가 내는 도구 스키마(속성 설명과 `$schema`가 붙는다)를 받으면 도구를 부르지 않는다. 어댑터는 도구 스키마를 그대로 싣는 것이 맞고(요청 본문은 평범하다), 어댑터에서 설명이나 `$schema`를 떼는 길은 다른 모델의 도구 선택 정보를 잃게 하므로 택하지 않는다.
- ADR 0058의 "두 모델" 결정은 이 경우를 이미 정해 두었다. "띄워 보니 도구 호출이 되지 않으면 같은 기준의 다음 후보(한국어는 A.X 3.1 Light, 해외는 Ministral 3 8B)로 바꾸고 까닭을 일지에 적는다". 그래서 병합 조건의 모델 하나를 `skt/A.X-3.1-Light`(`hermes`)로 바꾸는 것이 ADR의 범위 안의 다음 걸음이다. 바꾸기 전에 그 모델이 같은 스키마에서 도구를 부르는지 서버를 빌려 확인해야 한다(같은 파서·같은 계열이라 같은 흔들림이 있을 수 있다).

### 모델 교체 확인 시도: A.X 3.1 Light가 뜨지 않았다 (2026-11-15 12:02Z~12:32Z, 커밋하지 않은 확인)

사용자가 "바꾸고 확인한다"를 골라, `tools/llm_local.py`의 `MODELS` 하나를 `skt/A.X-3.1-Light`(`hermes`)로 바꾼 작업 트리(커밋하지 않았다)에서 확인 탐침(스크래치패드의 `probe_ax31.py`)을 돌렸다.

- 결과: 무효 회차(종료 코드 2). 서버를 띄웠으나 "준비 상한을 넘겨 지웠다"(1,834.6초, 약 30분). 공유 A40 한 장(시간당 $0.59)에서 두 서버의 옵션은 지난 회차와 같았다(`--gpu-memory-utilization 0.45 --kv-cache-memory=4294967296`). 탐침 본문은 한 줄도 돌지 못했다. 어림 비용 $0.3(30.6분 × $0.59, 실제 청구는 확인하지 않았다).
- 원인은 알 수 없다. 회차 파일(`round-0005-…json`)에 서버 기록이 실리지 않았고 파드는 이미 지워졌다. 후보는 이 모델이 4GiB KV 캐시 예산(`--kv-cache-memory`)이나 vLLM 0.33.0에서 뜨지 못함, 가중치 내려받기 지연, 모델 요구 조건(원격 코드 신뢰 등)이다. 모두 보지 못한 어림이다.
- 되돌린 것: `MODELS`의 교체는 되돌렸다(`git diff`에 `tools/llm_local.py` 변경 없음). 검증하지 못한 모델 교체를 커밋하지 않는다. `sweep`으로 남은 상태를 치웠다.
- ADR 0058의 다음 후보 규칙은 한국어 모델의 다음 후보가 A.X 3.1 Light 하나뿐이다(해외 모델 쪽 후보는 Ministral 3 8B). 한국어 모델 자리에 뜰 후보가 이제 ADR에 없다. 이 병합 조건(두 모델 모두 통과)을 다시 정하는 일은 사용자의 ADR 승인이 필요한 결정이다.

### 후보 조사와 Gemma 4 확인 (2026-11-15, 웹 요약만, 서버 시험은 아래)

> 사용자: "다른 후보 조사"
> 사용자: "해외 모델은?"
> 사용자: "Gemma4 26B 양자화는?"
> 사용자: "Gemma 4로 시험해 본다"
> 사용자: "Gemma 4 26B-A4B-it 모델의 양자화 옵션으로는 못해?"
> 사용자: "W4A16 먼저"

아래 사실은 모두 웹 요약(WebSearch·WebFetch의 작은 모델 요약)이고 원문과 대조하지 않았다.

- 한국어 후보. Kanana 1.5 8B Instruct는 Apache-2.0이지만 채팅 템플릿이 Llama 3.1 꼴(`<function=이름>`)이라 `hermes` 파서와 맞지 않아 보인다. Mi:dm 2.0은 별도 파서 플러그인이 필요해 보이고, Tri-7B는 함수 호출 문서가 없으며, HyperCLOVA X SEED Think 14B는 vLLM 본체에 도구 파서가 없다고 한다. Raon-1-nano(KRAFTON)는 모델 카드에 `--tool-call-parser raon_1`이 적혀 있으나 vLLM 0.33.0에 들어 있는지는 못 봤다.
- 해외 후보. ADR 0058에 적힌 예비는 Ministral 3 8B이고 이 세션에서 시험하거나 조사하지 않았다.
- Gemma 4 26B-A4B-it(구글, MoE 26B·활성 3.8B, 256K, 모델 카드상 Apache 2.0). vLLM 파서는 `gemma4`, 최소 vLLM 0.25.0(레시피). 모델 자체의 채팅 템플릿이 `tools`·`tool_calls`·`tool` 역할을 처리하고 도구 호출을 `<|tool_call>call:이름{…}<tool_call|>`로 적는다. 그래서 레시피의 `--chat-template` 파일은 넣지 않았다(이미지에 그 파일이 있는지 문서로 알 수 없었다).
- 양자화 판. 원본 BF16은 약 51.6GB라 A40(48GB)에도 안 들어간다. GotoAI의 W4A16(compressed-tensors, 약 15.65GB, 보정 데이터 없는 양자화, 정확도 측정 없음)이 24GB 카드와 shared 배치에 들어가는 사실상 유일한 판이다. FP8 판은 Hopper·Blackwell용, NVFP4는 Blackwell용이다. 원본에 `--quantization`을 주는 길은 Ampere에서 가중치만 8비트로 두는 방식이 될 것으로 문서가 말하나(26GB 안팎), 24GB 카드와 shared 배치(서버당 약 21.6GB)에 안 들어가고, 파드 디스크 60GB에 원본 51.6GB가 빠듯하며, 읽을 때 최대 메모리가 BF16 크기인지 문서에 없다.
- 사용자가 W4A16을 먼저 시험하기로 했다. 도구 호출 여부는 양자화와 거의 무관한 질문이라 가장 잘 뜰 판으로 먼저 답을 얻는다는 까닭을 함께 설명했다.
- 임시 설정(커밋하지 않는다). `tools/llm_local.py`의 `MODELS` 1번을 `Model(1, "GotoAI-Inc/gemma-4-26B-A4B-it-W4A16", "gemma4 --max-model-len 32768")`로 바꿨다. Terraform 변수 모양(`model_id`, `parser`)을 건드리지 않으려고 파서 칸에 서버 옵션을 덧붙였다. 이 값은 병합 기록이 아니라 도구 호출이 되는지 보는 확인용이다.

### Gemma 4 W4A16 확인 결과: 두 모델 모두 통과 (2026-11-15 13:0xZ, 커밋하지 않은 확인)

사용자가 "W4A16 먼저"를 골랐고, 앞서 보여 준 어림 비용(30분 기준 $0.27~$0.59, 최악 90분 $0.81~$1.77) 안에서 `uv run --env-file ../../../.env python tools/llm_local.py run --yes`를 돌렸다.

- 결과: 통과 2, 종료 코드 0(`uv run pytest -m llm_local`, 114.18초). 모델 1 `GotoAI-Inc/gemma-4-26B-A4B-it-W4A16`(`gemma4` 파서)과 모델 2 `openai/gpt-oss-20b`(`openai` 파서) 모두 같은 시험(calc 에이전트, 실제 MCP 도구 16개)에서 `tool_called`와 `llm_called`를 포함한 단언을 통과했다. A.X-4.0-Light가 못 넘은 바로 그 시험이다.
- 배치와 값: 공유 A40 한 장(시간당 $0.59), 경과 541.9초라 어림 비용 약 $0.09(실제 청구는 확인하지 않았다). LLM 토큰 합계 6,328(입력 6,191, 출력 137), 트레이스 2개, 모델 호출 4건. 서버 옵션은 `vllm serve GotoAI-Inc/gemma-4-26B-A4B-it-W4A16 … --tool-call-parser gemma4 --max-model-len 32768 --gpu-memory-utilization 0.45 --kv-cache-memory=4294967296`(vLLM 0.33.0). `--chat-template`은 넣지 않았다. 모델 자체의 템플릿으로 도구 호출이 되었다.
- 이 회차 앞에서 RTX A5000 둘과 RTX 3090 둘은 재고가 없었고, A40 둘은 한 대만 만들어졌다가 지워졌다. 끝난 뒤 `sweep`과 Runpod의 `list-pods`로 남은 파드가 0임을 확인했다.
- 이 회차는 병합 기록이 아니다. `MODELS` 1번이 커밋하지 않은 임시 값이고 시험 대상 커밋이 `f85ae474b`다. 병합 조건(ADR 0058, operations.md)은 최종 범위 커밋에서 정식 설정으로 다시 돌린 통과를 요구한다.
- 알게 된 것: 같은 스키마에서 `hermes` 아래의 A.X-4.0-Light는 도구를 못 불렀지만 `gemma4` 아래의 Gemma 4는 불렀다. 곧 문제는 시험이나 어댑터가 아니라 그 모델과 파서의 조합이었다는 앞의 결론과 어긋나지 않는다.
- 남은 결정(사용자 승인 필요): Gemma 4는 한국 모델이 아니다(모델 카드는 140개 이상의 언어를 지원한다고 하나 한국어 품질은 확인하지 못했다). ADR 0058이 한국어 모델 한 자리를 둔 취지와 이 교체를 어떻게 맞출지는 ADR 이력에 적고 승인받아야 한다. 이 결정을 위해 아래 "정식 반영"에서 사용자의 답을 받았다.
- 시간의 구분: 541.9초는 서버를 띄우고 지우기까지의 경과이고, 시험(`pytest -m llm_local`) 자체는 114.18초였다.

### 정식 반영 (2026-11-15)

세션이 "Gemma 4를 병합 조건의 1번 모델로 정식 반영할까요?"를 물었고(선택지 "정식 반영"과 "먼저 논의". 정식 반영의 할 일은 ADR 0058 이력 초안, 모델마다 서버 옵션을 싣는 정식 코드, 틀린 시험 주석 수정, 문서 맞춤, 그 뒤 커밋·봇 회차·최종 커밋의 실제 시험·병합이라고 안내했다) 사용자가 답했다.

> 사용자: "정식 반영"

- 가중치 판의 근거(원문). 이 PC에서 `curl`로 `https://huggingface.co/api/models/GotoAI-Inc/gemma-4-26B-A4B-it-W4A16`의 JSON을 읽었다(커밋하지 않은 한 줄 명령, 2026-11-15). `sha`는 `fdb4e380603cf157783227bd790bfbe921b64610`, `lastModified`는 `2026-08-22T09:25:29.000Z`, `cardData.license`는 `apache-2.0`이다. 앞의 통과한 임시 설정에는 `--revision`이 없었으므로, 이 해시로 띄우는 것은 아직 돌려 본 적이 없다. 최종 커밋의 실제 시험이 처음이다.
- 한 것: 실패하는 테스트를 먼저 쓰고(`Model.server_args` 없음으로 빨강 확인) `Model.server_args`, `server_options`, `terraform_env`의 `server_args`, `main.tf`의 변수와 `join`을 구현했다. `MODELS` 1번을 `GotoAI-Inc/gemma-4-26B-A4B-it-W4A16`(`gemma4`, `--max-model-len 32768 --revision <해시>`)으로 정식 값으로 넣었다. 명세, 운영 문서, 도구 독스트링의 모델 이름을 맞추고, 시험 파일의 틀린 주석을 고치고, ADR 0058에 본문 표지와 새 `## 이력` 절의 초안을 썼다(사용자 승인 전).
- 검증: `uv run python tools/run_checks.py`에서 파이썬 7,731개가 통과했고 1개(`tests/tools/test_probe_kit.py::test_배출은_줄이_계속_와도_제한_시간에_끝난다`, 0.5초 안에 자식이 줄을 내야 하는 시간 단언)가 실패했다. 같은 파일을 홀로 돌리면 15개 모두 통과했다. 이 변경이 건드리지 않은 파일이고 전체 러너가 600초에 걸려 web-verify와 겹쳐 돈 때라 부하 탓으로 어림하지만 원인을 진단하지는 않았다. pyright, lint-imports, check-instructions, check-type-escapes, run-hooks, zizmor, web-verify, `ruff check`, `ruff format --check`는 통과했다.

### 정식 반영의 셀프 리뷰 (2026-11-15, `/code-review` 두 축, 범위는 커밋하지 않은 작업 트리 전부)

- 고친 것. (1) ADR 0058의 이력이 진단 탐침의 범위를 넓게 말한 곳을 잰 범위로 좁혔다(도구 개수·`tool_choice`·`get-sum` 하나의 스키마 교차만 재고, 다른 도구의 스키마나 문구는 재지 않았다). (2) 닫힌 주장과 날짜·해시의 근거 문장을 일지의 원문(`curl` 출력)에 맞췄다. (3) `tools/llm_local.py`의 `MODELS` 주석에서 `--max-model-len`은 "고른 어림", 기본 컨텍스트가 KV 캐시 예산에 맞는지는 "재지 않았다"로 고쳤다. (4) `tests/tools/test_llm_local_state.py`의 새 시험이 "파서 바로 뒤"라는 이름과 달리 파서 뒤 어디든 통과하던 것을, 파서 < `server_args` < `--gpu-memory-utilization` 순서를 단언하게 고쳤다. (5) `.scratch/local-model/spec.md`의 예시 매니페스트를 새 모델로 맞췄다. (6) 이 일지가 도구 스키마의 속성 설명을 모든 도구에 붙는 것처럼 적은 곳을 좁혔다(열여섯 스키마에 `$schema`, 속성이 있는 열한 도구에 속성 설명, 속성이 없는 도구 다섯).
- 남긴 것. 시험 파일의 샘플 값 `skt/A.X-4.0-Light`(147·153행)는 값의 예일 뿐이라 둔다(Nit). `.scratch/plan.md`와 티켓 03의 옛 모델 이름은 그때의 기록이다. 진단 탐침 다섯(`probe_adapter_body.py`, `probe_ax_tools.py`, `probe_ax_split.py`, `probe_ax_cross.py`, `probe_ax31.py`)은 스크래치패드에 있고 커밋하지 않았다. 프로브 규칙은 ADR이 근거로 드는 탐침을 `.scratch/<slug>/probes/`에 `Rounds`와 양성 대조를 갖춰 커밋하라고 한다. 지금 스크립트는 그 꼴이 아니라 다시 짓는 일이 되어, ADR의 해당 문장이 "커밋하지 않았다"를 그대로 적게 두었고 사용자 판단으로 넘긴다.
- 다시 돌린 명령. `uv run pytest -q tests/tools/test_llm_local_state.py tests/tools/test_llm_local_rounds.py tests/test_local_model_llm.py`가 78 통과·2 deselected(`llm_local` 마커), `uv run ruff check .` 통과, `uv run ruff format --check .` 통과(셋 다 파이프로 쳐 종료 코드는 못 봤고 출력으로 판정했다). 전체 게이트는 커밋의 pre-commit 결과로 갈음한다.
- PR 직전 `bug-perf-review`에 밀 주장(이번에 새로 쓴 사실 문장). (a) "속성이 있는 11개 도구의 속성은 모두 설명을 가지고 속성이 없는 도구가 5개다". (b) "시험 114초, 서버를 띄우고 지우기까지 541.9초". (c) "`--revision` 해시는 2026-11-15에 그 저장소의 최신 판이었다". (d) "`--max-model-len 32768`은 모델 카드의 32k 기준 메모리 계산에서 고른 어림". (e) "A.X-4.0-Light 실패의 원인은 `hermes` 아래 속성 설명과 `$schema`가 든 스키마다".

### ADR 0058 이력 초안 승인 (2026-11-15)

세션이 "ADR 0058 이력 초안(1번 모델을 A.X-4.0-Light에서 Gemma 4 W4A16으로 바꾸고 한국어 모델 자리를 거둔다)을 승인하시겠어요?"를 물었고(선택지 "승인", "승인 + 탐침도 커밋", "초안 수정". "승인"의 설명은 초안 그대로 확정하고 커밋·푸시·봇 회차로 진행하며 진단 탐침 다섯 개는 스크래치패드에만 두고 ADR에 "커밋하지 않았다"고 그대로 적어 둔다는 것이었다) 사용자가 답했다.

> 사용자: "승인"

- 따라서 초안은 확정이다. 진단 탐침 다섯은 커밋하지 않고, ADR의 "스크래치패드에서 돌렸고 커밋하지 않았다" 문장을 그대로 둔다(프로브 규칙과의 틈은 위 셀프 리뷰의 "남긴 것"에 적었다. PR 본문에도 적는다).

### 정식 반영 뒤 봇 회차와 PR 직전 리뷰 (2026-11-15, 푸시한 머리 bff63961e)

- CI. `python`, `web`, `e2e`, `e2e-widget`, `e2e-portal`, `visual`, `ticket`, `verify`, `claude-review` 초록, `llm`은 건너뜀. 첫 푸시 뒤 PR이 충돌(`origin/dev`가 헌법 판 3.0.102를 가져감)이라 dev를 다시 합치고 판을 3.0.103으로 올렸다(`docs/constitution/README.md`의 비워 둔 판 문장에 병합 순서를 덧붙였다. `uv run python -m tools.check_constitution_version`이 통과했다).
- CodeRabbit. `@coderabbitai review`에 "Review rate limited"로 답해 이번 머리는 리뷰를 받지 못했다. 앞선 회차(위 "봇 회차")의 결과는 그대로이고, 이번 변경은 아래 PR 직전 리뷰로 갈음했다.
- claude-review(두 코멘트, 이번 변경이 아닌 어댑터 코드에 대한 것). Minor 둘(`_generate`·`_agenerate`의 중복 두 줄을 묶기, `_KeySource`의 가리기 책임 분리), Nit 둘(`ports.py` 독스트링의 구체 이름, 모듈 독스트링 길이)과 한쪽만 고치는 실수를 막는 시험이 두 경로를 덮는지 확인하라는 Nit. 이번 PR의 정식 반영과 무관하고 판단 항목이라 커밋을 막지 않는다. 남긴다: 동기·비동기 중복은 라이브러리 시그니처 때문에 불가피하다고 리뷰 자신이 적었고, 가리기 분리와 독스트링 길이는 모듈 독스트링이 원천이라 의도한 설계다(`.claude/rules/adapters.md`). 후속 후보로 둔다.
- PR 직전 `bug-perf-review`(커밋 `b17873e04`, 범위 파일 10개). Critical·Major 없음. `main.tf`의 낱말 순서(`--tool-call-parser`, `join(" ", m.server_args)`, `--gpu-memory-utilization`)와 빈 `server_args`에서 빈 낱말이 없음을 임시 Terraform 구성으로 재현했고 `terraform fmt -check`는 통과했다(`validate`는 프로바이더가 필요해 못 돌렸다). `TF_VAR_models`의 모양, 해시가 코드와 일지에서 같음, 114초·541.9초·6,328 토큰이 ADR과 일지에서 같음, 비밀이 새지 않음을 확인했다. 확인하지 못한 것: vLLM이 `--revision`을 토크나이저에도 적용하는지(첫 실제 시험이 검증), 시험 파일 두 개의 변경은 읽지 않았다.
  - [Minor] ADR 0057의 84행(2026-11-12 이력 항목)이 시험의 두 모델 이름으로 `skt/A.X-4.0-Light`를 적는다. 그 시점의 기록이라 고치지 않는다(`.claude/rules/adr.md`의 "앞의 이력" 갈래). 대신 새 이름이 같은 두 조건(이름이 `^o\d`에 맞는가, 소문자 이름이 `gpt-5`로 시작하고 `chat`이 없는가)에 걸리지 않음을 그 조건으로 대 봤다(`GotoAI-Inc/gemma-4-26B-A4B-it-W4A16`은 둘 다 아니다. 대조로 `o1-local`과 `gpt-5-local`은 걸렸다). 조건 자체는 라이브러리 원문이 아니라 ADR이 옮겨 적은 것을 정규식으로 옮긴 어림이다.
  - [Nit] ADR 0058의 16행(배경 목록)과 일지의 옛 이름은 그 시점의 기록이라 둔다. 해시가 ADR에는 없다는 지적은 맞다(ADR은 `<40자 해시>`만 적고 원천은 코드와 일지). 코드 주석의 "원문은 일지의 '정식 반영'"을 일지의 실제 절 이름 "가중치 판의 근거(원문)"으로 고쳤다.

### 병합 기록: 정식 설정의 실제 로컬 모델 시험 (2026-11-16, 시험한 커밋 `22b19c634`)

세션이 `llm_local.py run`을 `--yes` 없이 쳐서 예상 비용을 보여 주었고(공유 A40 한 장 시간당 $0.59, 최악 90분 $0.88. 단가는 2026-11-13에 웹 요약에서 읽은 값이라 원문과 대조하지 않았다), 사용자가 "돌린다 (Recommended)"를 골랐다. 그 뒤 `--yes`로 돌렸다.

- 결과: 통과 2, 종료 코드 0(`uv run pytest -m llm_local`, 81.57초). 모델 `GotoAI-Inc/gemma-4-26B-A4B-it-W4A16`(`gemma4` 파서, `--revision fdb4e380603cf157783227bd790bfbe921b64610`)과 `openai/gpt-oss-20b`(`openai` 파서)가 모두 통과했다. `--revision`으로 가중치 판을 고정한 정식 설정으로는 이것이 처음이고, 앞의 통과(임시 설정)는 병합 기록이 아니었다.
- 기록 묶음: 시험한 커밋 `22b19c6349107e3f45a0eb8a26330e94a1510c27`, 서빙 엔진 vLLM 0.33.0(이미지 `vllm/vllm-openai:v0.33.0`), 서버 옵션은 Gemma 쪽 `--enable-auto-tool-choice --tool-call-parser gemma4 --max-model-len 32768 --revision <해시> --gpu-memory-utilization 0.45 --kv-cache-memory=4294967296`, gpt-oss 쪽 `--enable-auto-tool-choice --tool-call-parser openai --gpu-memory-utilization 0.45 --kv-cache-memory=4294967296`. GPU는 공유 A40 한 장(시간당 $0.59), 경과 447.2초라 어림 비용 약 $0.07(`447.2 ÷ 3600 × 0.59`. 실제 청구는 확인하지 않았다). LLM 토큰 합계 6,328(입력 6,191, 출력 137), 트레이스 2개, 모델 호출 4건. Terraform 출력에서 가린 것이 있었다(`terraform_output_masked: true`). 서버 키와 주소는 적지 않는다.
- 무효 회차: 없다. 다만 띄우는 단계에서 앞 후보가 재고 부족으로 물러났다. RTX A5000 둘과 RTX 3090 둘은 "no longer any instances available"(HTTP 400)로 실패했고, A40 둘은 파드 하나가 만들어진 뒤 다른 하나가 같은 까닭으로 실패했다. 네 번째 후보인 공유 A40 한 장이 떴다. 이 실패는 시험 실패가 아니라 띄우기 실패이고 시험은 한 번만 돌았다.
- 남은 서버: `sweep`이 "치웠다"를 찍었고 Runpod `list-pods`가 빈 목록이었다. 병합 뒤에도 `sweep`을 한 번 더 친다.
- 근거의 종류: 위 수치와 서버 옵션, 통과 수, 단가, 경과는 `llm_local.py run --yes`가 찍은 기록 묶음의 값이다(탐침이 찍은 것). 약 $0.07은 그 경과와 단가로 내가 계산한 어림이다. 파드 재고 실패의 문구는 같은 명령의 Terraform 출력에서 읽었다. `list-pods`의 빈 목록은 Runpod MCP 도구로 손으로 본 것이다.
- 확인하지 못한 것: 서버 옵션에 `--revision <해시>`가 들어갔고 서버가 떠서 시험이 통과했다는 것까지는 기록에 있다. 그 해시의 가중치가 실제로 올라왔는지, 토크나이저에도 같은 판이 쓰였는지는 서버 로그를 읽지 않아 재지 않았다.
- 회차 파일: `round-0001-20261115T151829Z.json`(상태 폴더 `records/`).
