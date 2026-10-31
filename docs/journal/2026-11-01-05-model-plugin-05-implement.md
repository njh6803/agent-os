# 2026-11-01 (05) 모델 플러그인 티켓 05 구현

세션 제목: `feature/05-default-model-required-and-checked`.

## 사용자 프롬프트 원문

> 사용자: `.claude/skills/implement/SKILL.md` 를 읽어 그대로 따른다. … 인자: `.scratch/model-plugin/issues/05-default-model-required-and-checked.md` … 다음 단계: 구현 … 이번 요청 범위: PR과 병합까지

조작 지시(`tidy-checkouts`, `EnterWorktree`)는 따랐고 그 밖의 결정 질문은 없었다.

## 한 것(커밋하지 않은 작업 트리)

- 기본값 걷기: `adapters/anthropic.py`에서 `DEFAULT_MODEL`을 지웠다. `resolve_model_name`은 플래그, 환경변수 순이고 둘 다 없으면 이름을 넘기는 두 길(`--model`과 `AGENT_OS_MODEL`)을 든 `ValueError`다. 빈 값의 문구는 그대로다. `--model` 도움말과 `_add_model` 독스트링에서 "그다음 기본값"이 빠졌다.
- 시작 때 확인: `main.py`의 `_model_problem(flag, plugins_root)`가 네 갈래(이름 없음·빔, 패턴 위반, 매니페스트 없음, 읽히지 않음)를 낸다. 앞의 둘은 `_default_model`이 풀고, 뒤의 둘은 `FilesystemPlugins(...).read_manifest(PluginKind.MODEL, 이름)`로 한 번 읽는다(없으면 `기본 모델 플러그인이 없다: 이름`과 파일 경로, 읽히지 않으면 어댑터의 `PluginError` 문구 그대로). 꺼짐은 보지 않는다. `serve`는 이것을 구성 문제 목록의 한 항목으로 내고, CLI `run`·`resume`은 OS 사용자 검사 다음에 같은 함수를 불러 실패하면 표준 에러와 `EXIT_FAILED`로 끝난다.
- 재개 안내 줄: `channel/cli/main.py`의 `_inherited_options`가 기본 모델의 이름을 `--model`로 언제나 싣는다. `run_command`·`resume_command`가 이미 받던 `default_model`을 `_report`·`_show`·`_approval_request`로 내렸다.
- 시험: `tests/adapters/test_anthropic.py`의 기본값 사례를 "둘 다 없으면 두 길을 든 구성 오류"로 바꿨다. `tests/test_main.py`는 `DEFAULT_MODEL` import를 걷고, CLI 쪽 시험(이름 없음 `run`·`resume`, 매니페스트 없음, 읽히지 않음, 꺼진 기본 모델, 안내 줄이 `--model`을 싣고 환경변수 없이 그대로 쳐도 재개됨)과 `serve` 쪽 시험(이름 없음, 매니페스트 없음, 읽히지 않음, 꺼진 기본 모델이 시작을 막지 않음)을 더했다. 기존 `serve` 모델 시험의 셋째 갈래(환경변수 없이 기본값)는 빠졌다. 승인 줄을 그대로 단언하던 시험은 `--model`이 든 줄로 고쳤다.
- 프로브: `.scratch/conversation/probes/token_ratio.py`가 `DEFAULT_MODEL`을 import해 깨지므로 모델 id를 인자로 받게 고쳤다(API의 모델 id를 직접 받는 프로브라 모델 플러그인과 무관하다). 변이 표 `.scratch/model-plugin/probes/startup_check_mutations.toml`(변이 1)을 더하고 그 README 표에 줄을 넣었다.
- 문서: README `serve` 줄의 주석이 서는 조건에 기본 모델을 들고 시작 때 확인을 말한다. `.env.example`은 03이 `AGENT_OS_MODEL=claude-opus-5` 줄을 이미 넣어 두어 그대로다. `.scratch/plan.md`의 `model-plugin` 행을 갱신했다.
- 티켓은 체크박스를 모두 채우고 `Status: done`으로 바꿨다.

## 검증(이 세션이 본 것)

- 첫 빨강: 새 시험 13개를 구현 전에 돌려 9개가 빨강, 4개가 초록이었다(구현 세션은 10개와 3개로 적었으나, 셀프 리뷰가 `src/`의 변경을 `git apply -R`로 잠시 되돌려 `-k`로 고른 시험을 다시 돌려 세었고 이 수가 맞다). 빨강은 어댑터의 "둘 다 없으면 구성 오류", `run`·`resume`의 이름 없음, `resume`의 매니페스트 없음, `resume`의 읽히지 않음, 안내 줄, `serve`의 이름 없음·매니페스트 없음·읽히지 않음이다. 초록 넷은 `run`의 매니페스트 없음과 읽히지 않음(코어 준비가 같은 문구를 내서)과 꺼진 기본 모델의 `run`·`serve`(구현 전부터 시작이 꺼짐을 보지 않아서)다.
- 변이: 초록이던 `serve`의 꺼짐 시험을 `.scratch/model-plugin/probes/startup_check_mutations.toml`로 잰다. 시작 확인이 꺼진 기본 모델을 막게 바꾸는 변이가 `test_꺼진_기본_모델은_serve_의_시작을_막지_않는다`를 `assert 1 == 0`으로 빨갛게 만들었다(`tools/mutate.py`, 변이 1 모두 기대대로). `run`의 매니페스트 없음·읽히지 않음 사례는 코어 준비가 같은 문구를 내므로 `run`만으로는 시작 확인을 가르지 못한다. 가르는 몫은 `resume`과 `serve`의 사례다.
- `uv run ruff check .`·`uv run ruff format --check .`: 통과. `uv run pyright`: 0 errors.
- `uv run python tools/run_checks.py`: check-ticket·zizmor·lint-imports·check-instructions·check-type-escapes·pyright-linux·pyright·run-hooks·pytest(266.4초)·web-verify(445.2초) 모두 Passed, 종료 코드 0.
- `pnpm -C web/apps/admin exec playwright test`: 9 passed(43.0초). `pnpm -C web/apps/widget exec playwright test`: 15 passed(32.4초).
- `uv run --env-file ../../../.env pytest -m llm`: 7 passed(131.97초, LLM 토큰 합계 53,051, 트레이스 10개, 모델 호출 21건, 트레이스를 남기지 않은 LLM 테스트 1개는 세지 못했다). 그 가운데 안내 줄을 그대로 먹여 실제 CLI 프로세스로 재개하는 시험이 `--model` 없이 안내 줄만으로 끝까지 갔다.

- `uv run --env-file ../../../.env pytest -m llm_widget`: 1 passed(38.79초, LLM 토큰 합계 6,777, 트레이스 1개, 모델 호출 2건).

## 보류와 메모

- ADR 0010(159줄)의 "`--model` > `AGENT_OS_MODEL` > 기본값" 문장은 `(바뀜: ADR 0040)` 표시가 없다. 구현 세션은 ADR 본문 편집이라 승인이 필요하다고 보아 고치지 않았다. 셀프 리뷰 세션이 포인터를 달았다가 거두었다(아래 "셀프 리뷰").
- 모델 매니페스트 사본 넷(저장소 파일, 두 e2e 스택, `MODEL_MANIFEST`)의 `max_tokens`·`temperature`를 이 티켓이 바꾸지 않았으므로 동기화할 것이 없다.

## 인계(셀프 리뷰 직전)

이 세션의 컨텍스트가 인계 문턱을 넘은 채 `code-review`를 부른 순간(셀프 리뷰 직전) 인계 계기가 왔다. 이 세션이 번복하거나 고친 결정은 없다. 세션 제목은 인계 전 `feature/05-default-model-required-and-checked`였고 `feature/05-default-model-required-and-checked (인계함)`으로 바꾼다. 워크트리의 변경은 모두 커밋하지 않았고, 구현·시험·문서·검증(위 "검증")은 끝났다. 남은 것은 셀프 리뷰(`/code-review origin/main`), Critical·Major 반영, 커밋, PR 직전 리뷰, PR, 봇 회차, 병합, 회고다.

인계 지시문(새 세션이 이 일지를 이어 쓴다):

```
다음 작업: .scratch/model-plugin/issues/05-default-model-required-and-checked.md. 코드의 기본 모델 이름을 걷고, 서버(serve)와 CLI가 시작할 때 기본 모델의 이름·패턴·매니페스트를 확인한다
다음 단계: 구현
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/model-plugin/issues/05-default-model-required-and-checked.md
브랜치: feature/05-default-model-required-and-checked
모델: Sonnet 5.5 / high. 2의 잇는 지시문
읽을 것: docs/journal/2026-11-01-05-model-plugin-05-implement.md (구현·검증은 끝났고 "인계" 절이 남은 단계를 말한다)
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(/code-review origin/main)부터 한다. 구현·시험·문서·검증 명령(run_checks, e2e 둘, -m llm, -m llm_widget)은 이 세션이 초록으로 끝냈다. 일지: docs/journal/2026-11-01-05-model-plugin-05-implement.md
확인할 선행 조건: 04의 규칙 편집에 대한 카나리아 실제 `claude -p` 회차는 돌지 않았다(preflight만). 이 티켓과 무관하고 tools/sibling_overlap.py가 그 알림을 계속 낸다. 병합은 이 워크트리 사본의 next-session merge.md(없으면 SKILL.md)의 "워크트리에서 병합할 때"를 Read로 열어 따른다
이번 요청 범위: PR과 병합까지
```

`open-session을 부른다` 줄은 열기 직전에 아래에 적는다.

open-session을 부른다 2026-10-31T22:18:26Z

## 셀프 리뷰(이어받은 세션)

범위: 기준 `ac1ce3db`, 수정 10개·미추적 2개·커밋 0개. 표준 축은 sonnet·high, 명세 축은 세션 모델이다. 두 축 모두 Critical·Major 없음.

고친 것:

- `tests/test_default_model_plugin.py` 독스트링이 "그 상수를 걷는 것이 05"라는 미래형을 그대로 두었다(표준 축 Minor). 상수가 없어졌다는 현재형으로 고쳤다.
- `.scratch/plan.md`의 model-plugin 행이 "01·02·03·04 는 병합됐거나 병합을 앞두고 있다"로 적혀 있었고 상태가 `todo`였다(표준 축 Minor). 04가 #448로 병합되었고 `docs/agents/issue-tracker.md`가 첫 티켓의 병합 때 `in-progress`로 바꾸라고 하므로 "병합됐다"와 `in-progress`로 고쳤다.
- 표준 축·명세 축이 ADR 0010 159줄에 포인터가 없다고 Minor로 냈다. 포인터를 달아 커밋하니 pre-commit의 `test_이_저장소의_ADR_포인터는_전부_이력_제목과_맞는다`가 빨개졌다(출력: `0010-…md:159: (바뀜: ADR 0040) — 이력 절 안에 있다`). 159줄은 `## 이력` 절의 `### 2026-09-24 채널이 붙으며 앱의 인자와 에러 어휘가 는다` 항목 안이고, `.claude/rules/adr.md`는 지난 이력 항목을 기록으로 본다. 그래서 편집을 `git restore`로 거두었다. 0022의 97줄도 `### 2026-10-15 거슬러 읽기는 …` 항목 안(`## 이력` 44줄 뒤)이라 같은 기록이다. 두 축의 지적이 둘 다 오탐이다.
- 일지의 첫 빨강 수가 틀렸다(명세 축 Minor). `src/`의 변경을 `git apply -R`로 잠시 되돌려 새 시험을 다시 돌려 세니 빨강 9개, 초록 4개였다(`run`의 읽히지 않음도 코어 준비가 같은 문구를 내서 구현 전부터 초록). 위 "검증"을 고쳤다. 되돌린 `src/`는 패치와 `fc`로 같음을 확인했다.
- `_model_problem` 독스트링의 "그것을 쓰는 실행이 409다"는 CLI에 맞지 않아 HTTP는 409, CLI는 실행 준비의 진단이라 고쳤다(명세 축 Nit).
- `_model_problem`의 본문이 같은 `except` 둘을 `except (ValueError, PluginError)` 하나로 합쳤다(표준 축 Nit).

남긴 것과 이유:

- ADR 0010 159줄과 0022 97줄의 `기본값` 문장: 위 이유로 기록이라 그대로 둔다. 결정이 바뀐 사실은 ADR 0040과 ADR 0014·0022 본문(33줄)의 포인터가 말한다.
- 표준 축 냄새(`default_model, traces, plugins_root`의 묶음, `_as_argument`의 매개변수 이름 `path`, 같은 문구 `기본 모델 플러그인이 없다`가 `core/run.py`와 `main.py`에 따로 있는 것, `_model_problem`이 `FilesystemPlugins`를 직접 만들어 소스를 갈아 끼울 이음매가 없는 것): 모두 판단 항목이고 Nit·Minor다. 문구의 중복은 원칙 IV 때문에 core가 상수를 공유할 수 없고, 두 자리를 시험이 각각 단언한다.

다시 돌린 명령(이 세션이 본 것): `uv run ruff check src tests`·`uv run ruff format --check src tests` 통과, `uv run pytest tests/test_main.py tests/test_default_model_plugin.py tests/adapters/test_anthropic.py -q`는 233 passed(56.42초, 독스트링을 고치기 전). 독스트링을 고친 뒤 `ruff check src`·`ruff format --check src` 통과. 전체는 커밋의 pre-commit 결과로 갈음한다.

PR 직전 리뷰에 밀 주장(이 리뷰 반영에서 새로 쓴 사실 문장): (1) ADR 0010 159줄과 0022 97줄은 `## 이력` 절의 항목 안이라 포인터를 달지 않는다, (2) 04가 #448로 병합됐다, (3) 새 시험 13개를 구현 전에 돌리면 빨강 9개, 초록 4개다.

첫 커밋 시도는 위 ADR 포인터 검사 하나(1 failed, 6022 passed)로 실패했고 커밋은 만들어지지 않았다. 포인터를 거둔 뒤 다시 커밋한다.
