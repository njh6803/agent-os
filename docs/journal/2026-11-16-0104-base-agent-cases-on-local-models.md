# 2026-11-16 기본 에이전트의 사례를 두 로컬 모델로 기록한다 (local-model 06)

세션 제목: `feature/06-base-agent-cases-on-local-models` (인계하면 `<브랜치> (인계함)`으로 바뀐다)

## 사용자 프롬프트 원문

> 사용자: 다음 작업: 기능 local-model의 .scratch/local-model/issues/06-base-agent-cases-on-local-models.md. 기본 에이전트(assistant)의 실제 모델 사례를 두 로컬 모델로 한 번 돌려 결과를 기록하는, 이 기능의 마지막 티켓
> 다음 단계: 구현
> 시작 프롬프트: /implement .scratch/local-model/issues/06-base-agent-cases-on-local-models.md
> 브랜치: feature/06-base-agent-cases-on-local-models
> 모델: Sonnet 5.5 / high
> 이번 요청 범위: PR과 병합까지

## 시작

- `tidy-checkouts`: 주 체크아웃을 `d80690da1`에서 `6cc678448`(origin/dev)로 당겼다. 지운 워크트리와 브랜치는 없다(판정이 `지운다`를 내지 않았다). 휴지통 일곱은 `node.exe`와 `esbuild.exe`가 쥐고 있어 남았다.
- 같은 이름의 브랜치를 맡은 다른 세션은 `list_sessions`에 없었다(지시문의 선행 조건).

## 사용자에게 물은 것

### 비용 확인 (`run`을 `--yes` 없이 친 뒤)

질문: 기본 에이전트(assistant)의 실제 모델 시험 열네 사례를 두 로컬 모델(Gemma 4 26B-A4B-it 양자화 판, gpt-oss-20b)로 한 번 돌리려고 Runpod 서버를 빌립니다. 아래 비용으로 진행할까요?

> 사용자: 돌린다 (Recommended) — 방금 `--yes` 없이 친 명령이 찍은 값입니다. 먼저 시도하는 구성은 RTX A5000 파드 둘이고 시간당 $0.54, 어림 30분 $0.27, 최악 90분 $0.81입니다. 재고가 없으면 RTX 3090 둘($1.00/시, 최악 $1.50), A40 둘($1.18/시, 최악 $1.77), 공유 A40 한 장($0.59/시, 최악 $0.88) 순으로 넘어갑니다. 파드는 90분 뒤 스스로 지워집니다. 단가는 2026-11-13 웹 요약 값이라 원문과 대조하지 않았습니다.

(`--yes` 없는 호출의 출력은 위 값과 같았다. 종료 코드 4.)

## 한 일

- 이음매: `tests/test_assistant_llm.py`의 모델 자리가 상수 둘(`MODEL`, `MODEL_KEY`)이었다. 목록이 아니고 모델 파일을 더하지 못해 이 티켓이 넓혔다. 모델 차림(`ModelSetup`: 모델 플러그인 이름, 환경에 있어야 하는 변수, 복사한 루트에 더할 모델 파일을 쓰는 함수)의 목록 `MODELS`를 한 자리에서 정하고, 열네 사례가 그 목록으로 매개변수화되며(`pytestmark`의 `parametrize("model", …)`), CLI의 `--model`과 `serve`의 `--model`이 차림의 이름을 따른다. 기본 목록은 Anthropic 모델 하나다. 환경 변수 `ASSISTANT_LLM_MODELS=local`이면 두 로컬 모델이고 모델 파일은 `tests/test_local_model_llm.py`의 `model_manifest`·`model_name`을, 환경 변수 이름은 `tools/llm_local.py`의 `env_names`를 쓴다. 사례의 단언은 고치지 않았다.
- 수집: 기본 목록은 14건(`[claude-opus-5]`), `ASSISTANT_LLM_MODELS=local`은 28건(`[local-model-1]`, `[local-model-2]`)이다.

## 인계 시점의 상태 (셀프 리뷰 직전, 컨텍스트 문턱을 넘어 인계)

- 커밋: 없다. 브랜치 `feature/06-base-agent-cases-on-local-models`(워크트리 `C:/project/agent/.claude/worktrees/06-base-agent-cases-on-local-models`). 바뀐 것: `tests/test_assistant_llm.py`(이음매), 티켓 `Status: in-progress`, 이 일지(미추적).
- 이음매 검증(손으로 봤다): `uv run pyright tests/test_assistant_llm.py` 0 오류, `uv run ruff check`·`ruff format --check` 통과, `--collect-only`가 기본 목록 14건·`ASSISTANT_LLM_MODELS=local` 28건.
- Anthropic `-m llm` 확인(티켓 "차림" 첫 상자, "검증")은 백그라운드로 도는 중이다. 명령: `uv run --env-file ../../../.env pytest -m llm tests/test_assistant_llm.py -q -p no:cacheprovider`, 로그 `C:/Users/User/AppData/Local/Temp/claude/9060abe0b92613e9/0bd23aef-c306-4f30-adf7-6c09a1525a17/scratchpad/anthropic_llm.log`(인계할 때 점 다섯이 찍혔고 끝나지 않았다). 인계 절차의 "대기 멈추기"를 일부러 하지 않았다. 멈추면 이미 쓴 Anthropic 호출이 버려진다. 새 세션은 로그가 `14 passed`로 끝났는지 본다. 실패나 중단(프로세스가 없고 요약 줄이 없음)이면 같은 명령을 다시 쳐서 고치지 않고 보고한다(사례 단언을 느슨하게 하지 않는다. 원칙 II).
- 로컬 모델 `run`: `--yes` 없이 쳐 예상 비용을 찍었고(종료 코드 4) 사용자가 "돌린다"를 골랐다(위 "사용자에게 물은 것"). 새 세션은 다시 물을 필요가 없다. 비용 값이 달라졌으면(단가표를 고친 커밋이 있으면) 다시 묻는다. 돌릴 명령: `ASSISTANT_LLM_MODELS=local uv run --env-file ../../../.env python tools/llm_local.py run --yes -- uv run pytest -m llm tests/test_assistant_llm.py`. 시험한 커밋을 남기려면 이음매를 먼저 커밋하고(셀프 리뷰 반영 뒤) 그 커밋에서 돌린다. 아직 `--yes` 호출은 하지 않았고 서버는 빌리지 않았다.
- 남은 일(티켓 순서): ① 셀프 리뷰(`/code-review`, 고정점 `origin/dev`)와 반영, ② 이음매 커밋(pre-commit이 게이트를 돈다), ③ 위 `run --yes`를 백그라운드로 돌리고 끝난 턴에 기록 묶음을 일지에 옮긴다(회차 파일은 상태 폴더 `records/`), ④ `.scratch/local-model/probes/README.md`에 날짜 절(사례별 두 모델의 통과·실패, 실패 단언, 기록 묶음, 돌린 명령, 세 갈래별 결과), ⑤ 실패 사례를 `.scratch/pilot-release/plan.md` 본문 끝에 적고(오픈 모델로 answer-eval을 다시 돌리는 입력) `uv run python tools/plan_table.py`, 스킬 문구를 고칠 일은 일지 "다음"에 적어 사용자가 고르게 한다, ⑥ 티켓을 `done`으로 바꾸고 `.scratch/local-model/plan.md`에 `**끝:** 2026-11-16`(커밋 날짜), 제품 변경을 담았으면 기능 단락 `docs/release-notes/features/local-model.md`, `plan_table.py`, ⑦ PR(`/git-pr`)과 병합(`merge.md`), 병합 뒤 `sweep`.
- 이 세션이 번복하거나 고친 것: 없다. 티켓이 "차림"에서 정한 두 갈래 가운데, base-agent 05가 모델 자리를 상수 둘로만 두고 닫혀 있어 이 티켓이 이음매를 넓히는 갈래를 밟았다. 환경 변수 `ASSISTANT_LLM_MODELS`(anthropic·local)로 목록을 고르게 한 것은 이 세션의 선택이다(커밋된 코드로 같은 기록을 다시 낼 수 있게 하려고. 티켓은 목록을 코드에서 바꾼다고만 적었다).
- 이 세션의 제목: `feature/06-base-agent-cases-on-local-models` (인계하면 `(인계함)`이 붙는다).
- open-session을 부른다 2026-11-15T16:06:48Z (셀프 리뷰 직전 인계)

## 이어받은 세션 (새 세션, 워크트리 재진입)

- 제목을 `feature/06-base-agent-cases-on-local-models`로 바꾸고 워크트리(`C:/project/agent/.claude/worktrees/06-base-agent-cases-on-local-models`)에 들어갔다. 선행 조건 없음.
- Anthropic `-m llm` 확인(티켓 "차림" 첫 상자, "검증"): `uv run --env-file ../../../.env pytest -m llm tests/test_assistant_llm.py -q -p no:cacheprovider`가 `14 passed in 946.17s (0:15:46)`로 끝났다. 토큰 합계 195,126(입력 191,259, 출력 3,867), 트레이스 17개, 모델 호출 36건. `[100%]`가 찍힌 뒤 요약 줄까지 몇 분이 걸려 한동안 끝나지 않은 것처럼 보였다(프로세스가 살아 있었고 끝나자 줄이 찍혔다). 이 실행은 이음매를 만든 뒤 독스트링 두 곳과 실패 메시지를 고치기 전의 파일로 돌았다. 그 뒤의 수정은 독스트링과 메시지 문구뿐이다.

### 셀프 리뷰 (`/code-review`, 고정점 `origin/dev` = `6cc678448`, 파일 2, 커밋 0, 미추적 1)

- 표준 축: Critical·Major 없음. 타입 우회 없음(`check_type_escapes.py` 0, pyright 0 오류).
  - 고침: 독스트링의 "모델 파일 둘을 적는다"는 틀렸다. 사례마다 해당 차림의 모델 파일 하나다. "환경 변수 넷"도 모호해 `env_names`의 앞의 둘이고 키 변수는 요구하지 않는다고 고쳤다. `model_env`의 실패 메시지가 로컬 차림에서는 `.env`를 가리켜 틀려서 `llm_local.py run`이 채우는 환경도 말하게 했다.
  - 남김: `doc_search`와 `model`이 함께 다니는 Data Clumps, `_local_setup`과 `model_manifest`가 `env_names`를 두 번 푸는 중복, 다른 시험 모듈(`tests.test_local_model_llm`)의 `model_manifest`·`model_name` import는 모두 판단 항목이다. 이 티켓이 05의 모양을 그대로 쓰라고 했고(같은 모양을 두 곳에 두면 갈라진다), 두 번째 쓰는 자리라 공용으로 올리는 것은 다음 쓰는 자리가 생길 때 한다.
- 명세 축: Critical·Major 없음. `_local_setup(n).manifest(os.environ)`의 출력이 `model_manifest`의 출력과 문자열이 같음을 불러 대 보았다. 수집은 기본 14건, `ASSISTANT_LLM_MODELS=local` 28건.
  - 고침: 독스트링의 예시 명령에서 `--yes`를 빼고, 먼저 `--yes` 없이 쳐 비용을 확인한 뒤 붙이라는 설명을 더했다.
  - `ASSISTANT_LLM_MODELS`는 경미한 범위 넘침이나 수용했다. 같은 기록을 커밋된 코드로 다시 내려는 요구(티켓 "기록")에 기여하고, 잘못된 값은 수집 때 `ValueError`로 막힌다.
- 근거의 종류: Anthropic `14 passed`·토큰 합계는 pytest가 로그에 찍은 줄이고 내가 로그를 읽었다. pyright 0 오류·수집 14/28건·`model_manifest` 출력 일치·`check_type_escapes.py` 0은 리뷰 서브에이전트 둘이 각자 불러 본 보고이며 내가 다시 치지 않았다(커밋의 pre-commit이 pyright·타입 우회 검사를 다시 돈다). 이 세션이 직접 친 것은 수정한 파일의 `ruff check`·`ruff format --check` 통과뿐이다.

### 이음매 커밋과 게이트

- 이음매는 `05e1999ce`(`test: 기본 에이전트 시험의 모델 차림을 목록으로`)로 커밋했다. 첫 시도는 pre-commit의 `pytest`에서 `tests/tools/test_rerun_runner.py`의 사례 하나가 빨개 막혔고(7731건 통과, 1건 실패), 둘째 시도는 커밋 메시지 훅 사전 점검이 제목 87자를 짚었으며, 제목을 67자로 줄여 다시 쳤더니 `tests/channel/cli/test_interrupt.py`의 Ctrl+C 30초 한도 사례 하나가 빨개 막혔다. 둘 다 이 변경과 겹치지 않는 시간 의존 사례이고, 각각 단독으로 다시 돌리면 통과했다(손으로 봤다: `uv run pytest tests/tools/test_rerun_runner.py -k 두_회차가_함께` 1 passed in 276s, `uv run pytest tests/channel/cli/test_interrupt.py -k 닫기를_마치고_중단으로` 종료 코드 0). 셋째 시도에서 게이트 열일곱이 모두 통과했다. 같은 시험이 두 번 연속 실패한 것이 아니라 서로 다른 시험이 한 번씩 빨갰으므로 작업 규약 6의 진단은 부르지 않았다. 다른 세션의 `pytest -n 8`이 함께 돌아 부하가 컸다는 것은 어림이다(프로세스 목록에서 같은 시각의 다른 워크트리 pytest를 봤을 뿐 부하를 재지 않았다).

### 로컬 모델 회차 (`run --yes`, 회차 1)

기록 묶음과 사례 결과의 원천은 `.scratch/local-model/probes/README.md`의 2026-11-16 절이다. 값은 거기를 우선한다.

- 시험한 커밋 `05e1999ce484161bf87207a3830e0fbbfdaac2da`. 모델 `GotoAI-Inc/gemma-4-26B-A4B-it-W4A16`, `openai/gpt-oss-20b`. 엔진 vLLM 0.33.0(`vllm/vllm-openai:v0.33.0`). GPU 공유 A40 한 장, 시간당 $0.59. 통과 18/28. 토큰 입력 186,529, 출력 8,522, 호출 67건. 걸린 시간 1719.2초. Terraform 출력에서 가린 것 있음.
- 띄우기: A5000 두 장, RTX 3090 두 장은 재고 없음(HTTP 400), A40 두 장은 파드 하나가 선 뒤 둘째가 재고 없음으로 실패, 공유 A40 한 장에서 섰다. 끝난 뒤 `list-pods`가 `pods: []`(손으로 봤다).
- 무효 회차 0. 연달은 무효 회차 세기: 회차 파일은 `round-0001-20261115T183149Z.json` 하나다.
- 결과: Gemma 7건 통과(6, 7, 9, 10, 12, 13, 14), gpt-oss 11건 통과(9, 13, 14를 뺀 열한 사례). Gemma의 실패는 검색을 부르지 않고 정해진 문장으로 바로 답한 것(1, 3, 4, 5), 정해진 문장 앞에 `<|channel>thought`가 붙은 것(2), 둘째 실행에서 검색어가 없는 것(11), 앞의 답을 다듬을 때 `[1]`이 없는 것(8)이다. gpt-oss의 실패는 전문 읽기에서 멈추지 않고 끝난 것(13, 14)과 끝 넘음을 재지 못한 것(9)이다. 원인은 가르지 않았다.
- 스킬 문구(`cite-sources`)를 고칠지는 사용자가 고른다. 이 세션은 문구를 고치지 않았다. 입력은 `.scratch/pilot-release/plan.md` 본문 끝에 적었다.

### 이 티켓을 닫는 변경

- 티켓 06을 `done`으로, `.scratch/local-model/plan.md`에 `**끝:** 2026-11-16`, `docs/release-notes/features/local-model.md`(기능 단락. 티켓 05가 `src/`와 `uv.lock`을 고쳐 제품 변경을 담았다), `uv run python tools/plan_table.py`로 `.scratch/plan.md`를 갱신했다.
- 기능 단락의 마지막 문장(모델 서버가 올바른 JSON이 아닌 인자를 돌려주면 빈 답이 아니라 모델 호출의 실패로 끝나고 그 도구는 불리지 않는다)은 티켓 02의 서술을 읽고 옮긴 것이고 이 세션이 돌려 보지 않았다. PR 직전 리뷰에 밀 주장이다.
- 셀프 리뷰 반영의 고친 문장(PR 직전 리뷰에 밀 주장): 시험 모듈 독스트링의 "사례마다 복사한 루트에 그 차림의 `openai-compatible` 모델 파일 하나를 적는다. 키 변수는 요구하지 않는다", `model_env`의 실패 메시지 "`.env` 나 `llm_local.py run` 이 채우는 환경을 확인한다".

## 푸시와 PR (세 번째 세션, 워크트리 재진입)

- 제목을 `feature/06-base-agent-cases-on-local-models`로 바꾸고 워크트리에 들어갔다. `sibling_overlap.py`: 번호 겹침 없음. 이전 인계가 남긴 이 일지의 인계 절은 커밋하지 않은 변경이었다.
- 그 절을 커밋하려 했으나 pre-commit의 `pytest`가 두 시도 모두 시간 의존 시험으로 막았다. 첫 시도(1727.67초)는 `tests/channel/cli/test_interrupt.py`의 `test_서버를_닫기_시작한_뒤에_한_번_누르면_닫기를_마치고_중단으로_끝난다`가 "30초 안에 끝나지 않았다"로, 둘째 시도(2102.8초, `web-verify`는 1749.0초)는 `tests/tools/test_rerun_runner.py`의 `test_오염이_한_번이면_다시_돌고_두_번이면_그_과제를_모든_갈래에서_뺀다`가 `assert 1 == 0`으로 빨갰다. 앞의 것은 단독으로 다시 돌려 통과했다(손으로 봤다, 종료 코드 0). 이때 `pytest`를 포함한 파이썬 프로세스 가운데 pytest 명령줄을 가진 것이 14개였고 둘째 시도 직전에 6개였다(PowerShell로 한 번씩 셌다). 일지만 바뀐 커밋이라 이 변경과 겹치지 않는 빨강이고 훅은 건너뛰지 않았다. 이 세션은 일지를 이 PR의 마지막 커밋에 싣기로 하고 이미 커밋된 둘을 먼저 푸시했다.
- PR 직전 `coderabbit-review`: CLI 0.7.5가 `--committed --base origin/dev`로 끝까지 돌아 `review_completed`, `findings: 0`(이 PR의 커밋 파일 8개). `Seat: not assigned`, `Plan: Free`. 유효·오탐·보류 0건이고 미추적·스테이지 파일은 범위 밖이었다. 서브에이전트가 `tests/test_assistant_llm.py`의 diff도 직접 읽었으나 보안·버그·성능 문제를 찾지 못했다는 보고다(내가 다시 읽지는 않았다).
- 푸시했고 PR [#586](https://github.com/njh6803/agent-os/pull/586)을 `dev` 기준으로 열었다. 본문은 PR 서식을 채웠고 기록 묶음과 사례별 표를 실었다. PR 코멘트에도 기록 묶음을 올렸다. 마지막 푸시 뒤에 `@coderabbitai review`를 남겼다.
- 로컬 모델 시험은 다시 돌지 않았다. 시험한 커밋 `05e1999ce` 뒤의 변경은 `.scratch/`·`docs/`뿐이라 병합 조건 범위의 경로가 없다(`git diff --name-only 05e1999ce HEAD`를 쳐 보니 `.scratch/` 다섯 파일, 이 일지, `docs/release-notes/features/local-model.md`뿐이었다. 손으로 봤다).

### 봇 회차 1

- 헤드 `65662bb`. 검사 일곱 잡과 `verify`가 모두 SUCCESS(`llm`은 SKIPPED). CodeRabbit은 "Review rate limited"로 리뷰가 없어 회차로 세지 않는다("다음 포함 리뷰는 18분 뒤"라고 적었다). claude-review는 코멘트를 남겼다(Critical·Major 없음, Minor 셋과 Nit 둘). 첫 회차이므로 지적마다 판단했다.
  - Minor, 다른 시험 모듈에서 `model_manifest`·`model_name`을 import한다: 보류. 티켓 05가 이 모양을 그대로 쓰라고 했고, 이 파일이 두 번째 쓰는 자리다. 공용으로 올리는 일은 세 번째 쓰는 자리가 생길 때 한다(일지 "다음"에 적었다).
  - Minor, 잘못된 `ASSISTANT_LLM_MODELS`를 확인하는 자동 시험이 없다: 보류. 분기가 `_models()`의 마지막 `raise` 한 줄이고 메시지가 변수 이름과 받은 값을 함께 적어 수집 때 바로 알린다(`tests/test_assistant_llm.py:121`을 읽었다). 시험을 더하면 새 커밋과 30분 넘는 게이트와 봇 한 바퀴가 든다.
  - Minor, `ModelSetup`의 갈래를 열거로 드러내라: 보류. 모델 종류가 둘뿐이다. 세 번째 종류가 생기면 한다(일지 "다음"에 적었다).
  - Nit, `claude-opus-5` 문자열이 독스트링 예와 이중이다. Nit, `모델 차림`이 `CONTEXT.md`에 없다: 보류. 시험 안에서만 쓰는 말이다.
  - claude-review가 작성자 몫으로 남겼다고 한 기능 단락 마지막 문장은 이 세션이 티켓 02의 체크박스("실행이 원인 `model_call`의 `run_failed`로 끝나고, 그 호출의 `llm_called`와 `tool_called`가 트레이스에 없다")와 대 보았다. 돌려 본 것은 아니다.

## 회고

- 낸 후보 셋: 승인 1, 기각 2, 넘김 0.
- 승인: 문서만 바꾼 커밋의 pre-commit 한 바퀴가 길다. 사건은 위 두 시도다(1727.67초와 2102.8초, `web-verify` 1749.0초). 층은 이미 정해진 재기 chore이고 열린 항목 `docs-only-commit-precommit-slow-again`(0309의 4회차)에 5회차로 이었다. 새 항목을 쓰지 않았다. 같은 처방(안쪽을 재어 줄일 길을 고른다)이고 검사를 건너뛰는 길은 넣지 않는다. 이 세션의 한 바퀴는 나란히 돈 pytest가 14개였을 때 나왔다. 부하 때문인지 러너가 느려진 것인지는 이번에도 가르지 못했다. 이 항목이 회차 5가 되어 `next-session` 결정표의 하네스 chore 배치 조건이 찬다.
- 기각, 부하에서 서로 다른 시간 의존 시험이 번갈아 빨갰다(`test_interrupt.py`, `test_rerun_runner.py`): 대기열 306이 ADR 0036으로 닫은 종류(부하에서 시간 시험이 빨개지면 그 커밋을 다시 치는 값을 받아들인다)이고 새 사례는 회차를 더하지 않고 일지에만 적는다(retro 5단계). 위가 그 기록이다.
- 기각, 워크트리 가드가 `&&`로 이은 Bash 호출과 Monitor의 긴 `until` 명령을 거부했다: `CLAUDE.md` 환경 함정이 이미 알리고, 단일 명령 둘로 나눠 치는 것으로 지났다.

### 다음

- 이 PR은 봇 회차 1을 거쳤다. 이 일지를 푸시한 뒤 CI와 CodeRabbit(한도에 걸렸으면 PR 코멘트로 남긴다)을 마저 보고 병합한다. 병합한 뒤 `uv run --env-file ../../../.env python tools/llm_local.py sweep`으로 남은 서버와 상태 폴더를 치운다(주 체크아웃 아님).
- 뒤로 넘긴 일(봇 회차 1에서 보류한 것): `tests/test_assistant_llm.py`가 다른 시험 모듈에서 `model_manifest`·`model_name`을 가져온다. 세 번째 쓰는 자리가 생기면 `tests/` 아래 시험이 아닌 공용 모듈로 올린다. `ModelSetup`의 갈래(저장소 플러그인이냐 복사 때 생성이냐)는 세 번째 모델 종류가 생기면 열거로 드러낸다.
- 이 기능의 티켓은 모두 닫혔다. 병합 뒤 결정표: 기능의 마지막 티켓이고 열린 항목 `docs-only-commit-precommit-slow-again`이 회차 5라 하네스 chore 배치(`queue_open_rows.py`로 다시 센다)이며, `**끝:**` 줄이 dev에만 있으므로 출시 PR 계기도 함께 본다(`git log origin/main..origin/dev -G'^\*\*끝:\*\*'`).
- 사용자가 고를 것: `plugins/skills/cite-sources/SKILL.md`의 문구를 Gemma의 실패(검색을 부르지 않고 정해진 문장으로 바로 답함)를 줄이는 쪽으로 고칠지. 이 한 번의 결과로는 고치지 않았다. 고르는 자리는 base-agent의 후속 티켓이거나 answer-eval(오픈 모델로 다시 돌릴 때)이다.

## 인계 시점의 상태 (커밋 뒤, 두 번째 인계)

- 이 브랜치에 커밋 둘이 있고 푸시하지 않았다. `05e1999ce`(이음매), `65662bb24`(티켓 06 done, `**끝:**` 줄, 기능 단락 `docs/release-notes/features/local-model.md`, 프로브 README의 2026-11-16 절, pilot-release 계획의 넘김 문단, 이 일지). 작업 트리는 이 절을 빼면 깨끗하다.
- 로컬 모델 회차는 끝났다(회차 1, 18/28 통과). 다시 돌지 않는다. 결과와 기록 묶음은 프로브 README의 2026-11-16 절과 위 "로컬 모델 회차" 절에 있다.
- 남은 일: ① 푸시와 PR(`/git-pr`. 제목은 커밋 제목과 같은 꼴, 본문에 기록 묶음을 옮긴다), ② 봇 회차와 병합(`merge.md`), ③ 병합 뒤 `sweep`과 회고. 기록 묶음은 PR 코멘트에도 옮긴다(티켓 "기록"의 마지막 항목).
- 커밋 게이트의 `pytest`가 부하 때문에 서로 다른 시간 의존 시험에서 다섯 번 시도 가운데 넷을 막았다(`test_rerun_runner.py` 사례, `test_interrupt.py` 사례들, `test_hook_push_behind_main.py`, `test_probe_kit.py` 사례). 모두 단독으로는 통과했다(손으로 봤다). 형제 세션의 pytest가 14~24개 돌 때 막혔고 6개로 내려간 뒤 통과했다. 훅은 건너뛰지 않았다. 다음 세션이 푸시 전에 다시 커밋할 일은 없지만, 병합 전 CI의 `python` 잡이 같은 시험으로 빨개지면 단독으로 돌려 보고 다시 돌린다. 이 반복은 `.claude/rules/tests.md`의 시간 단언 항목과 같은 유형이라 회고 후보다(대기열 332·306의 다음 회차).
- 이 세션이 번복하거나 고친 것: 없다. 셀프 리뷰 반영은 위 "셀프 리뷰" 절에 있다.
- 이 세션의 제목: `feature/06-base-agent-cases-on-local-models` (인계하면 `(인계함)`이 붙는다).
- open-session을 부른다 2026-11-15T20:23:14Z (커밋 뒤 인계)
