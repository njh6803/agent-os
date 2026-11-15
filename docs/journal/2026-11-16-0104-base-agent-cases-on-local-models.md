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
