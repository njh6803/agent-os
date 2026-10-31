# 2026-11-01 (03) 모델 플러그인 티켓 03 구현

세션 제목: `feature/03-default-model-plugin-and-explicit-flag`. 인계 때 `feature/03-default-model-plugin-and-explicit-flag (인계함)`으로 바꾼다. 컨텍스트가 인계 문턱을 넘은 `셀프 리뷰 직전`에 넘긴다. 이 일지는 새 세션이 이어 쓰고 커밋한다.

## 사용자 프롬프트 원문

> 사용자: `.claude/skills/implement/SKILL.md` 를 읽어 그대로 따른다. … 인자: `.scratch/model-plugin/issues/03-default-model-plugin-and-explicit-flag.md` … 다음 단계: 구현 … 이번 요청 범위: PR과 병합까지

조작 지시(제목 바꾸기, `tidy-checkouts`, 워크트리 진입)는 따랐고 그 밖의 결정 질문은 없었다.

## 한 것(커밋하지 않은 작업 트리)

- 저장소: `plugins/models/claude-opus-5/plugin.toml`(공통 넷 + `provider = "anthropic"`, `model_id = "claude-opus-5"`, `max_tokens = 16000`, `temperature` 없음)을 두었다. `.env.example`에 `AGENT_OS_MODEL=claude-opus-5` 줄을 `ANTHROPIC_API_KEY=` 다음에 더했다(그 파일에는 주석이 없어 따를 주석 모양이 없다). README의 `serve` 줄이 `--model claude-opus-5`를 적는다.
- 새 시험: `tests/test_default_model_plugin.py`가 저장소의 모델 파일을 실제 `FilesystemPlugins`로 읽어 종류·제공사·모델 id·`max_tokens`·없는 `temperature`와, 목록에서 표지 행이 아니라 읽힌 매니페스트로 서는 것을 본다. 구현 전에 셋 모두 파일이 없어 빨강이었다.
- `tests/test_main.py`: `MODEL_PLUGIN`·`MODEL_MANIFEST`·`_write_model_plugin`·`_main`을 더했다. `_main`은 `main()`을 부르되 인자에 `--model`이 없으면 서브명령 뒤에 `--model claude-opus-5`를 끼운다. `_write_plugin`이 루트마다 모델 매니페스트를 함께 둔다(`_write_model_plugin`은 덮어쓴다). 실행 전 오류의 매개변수 시험은 "없는 에이전트" 사례를 위해 직접 부른다. `_copy_repo_plugins`는 `("models", MODEL_PLUGIN)`도 복사한다. `-m llm` 시험의 `_cli`·`_cli_run`·`_serving`은 `--model claude-opus-5`를 넘긴다. 직접 `main(` 호출 72곳을 `_main(`으로 바꿨고, 안내 줄을 먹이는 호출(569·652·653·697·699·720·725·2265·2400줄과 603줄은 손으로 지은 인자라 뒤의 셀프 리뷰가 `_main`으로 바꿨다. 바꾸기 전 번호)과 이름을 푸는 규칙을 재는 `main(["serve"])` 둘(1064·1066줄)은 그대로 `main(`이다. 안내 줄에 `--model`을 싣게 하는 것은 05의 몫이다.
- 두 e2e 스택: 관리 화면 `web/apps/admin/e2e/stack.ts`는 `DEFAULT_MODEL = "claude-opus-5"` 상수를 두고 `models/claude-opus-5`를 쓰며 `serve`에 `--model`을 넘긴다(`models/sonnet`은 01이 고친 그대로). 위젯 `web/apps/widget/e2e/plugins.ts`는 `DEFAULT_MODEL`을 내고 같은 값의 모델 픽스처를 쓰며(`max_tokens = 16000`까지 저장소 파일과 바이트가 같다), `stack.ts`가 `serve`에 `--model`을 넘긴다.
- 티켓은 체크박스를 모두 채우고 `Status: done`으로 바꿨다. 셀프 리뷰가 끝나기 전의 값이라 리뷰가 고칠 것이 있으면 되돌린다.

## 검증(이 세션이 본 것)

- `uv run ruff check . && uv run ruff format .`: 초록(1205 files left unchanged).
- `uv run python tools/run_checks.py`: check-ticket·zizmor·lint-imports·check-instructions·check-type-escapes·pyright·pyright-linux·run-hooks·pytest(334.8초)·web-verify(460.1초) 모두 Passed(`checks.log`를 읽었다). 이 실행은 티켓을 `done`으로 바꾸기 전(`in-progress`)에 돌았다.
- `pnpm -C web/apps/admin exec playwright test`: 9 passed. `pnpm -C web/apps/widget exec playwright test`: 15 passed.
- `uv run --env-file ../../../.env pytest -m llm`: 7 passed(275.72초, LLM 토큰 합계 56,776, 트레이스 10개, 모델 호출 22건, 트레이스를 남기지 않은 LLM 테스트 1개는 세지 못했다). `-m llm_widget`: 1 passed(40.28초, 토큰 합계 6,777, 트레이스 1개, 모델 호출 2건).
- 첫 빨강: `tests/test_default_model_plugin.py` 셋(파일 없음). 나머지는 지금 코드에서 이미 초록인 자리를 명시로 바꾼 것이라 바꾼 뒤에도 초록인 것을 위 실행들로 봤다.

## 남은 단계

셀프 리뷰(`/code-review origin/main`), 반영, 커밋, 푸시와 `/git-pr`, 봇 회차, 병합이다. 아직 커밋하지 않았다. `git status`의 변경은 `.env.example`, `README.md`, 티켓 파일, `tests/test_main.py`, 두 e2e 스택, 새 `plugins/models/claude-opus-5/`, 새 `tests/test_default_model_plugin.py`, 이 일지다.

## 보류와 메모

- `_fields_belong_to_their_kind`의 종류별 거부 연쇄를 종류별 허용 칸 표로 옮기는 후보(01의 PR 봇 둘째 회차에서 보류)는 03이 sdk를 건드리지 않아 여기서 하지 않았다. 지시문의 이어받을 상태가 이미 말한 후보다.
- Edit 훅이 `sync-design-system 확인`을 불러 보라고 알렸으나 이 세션이 고친 것은 e2e 스택 파일뿐이고 화면 코드가 아니어서 부르지 않았다. 새 세션이 화면 코드를 고칠 일은 없다.
- README `serve` 줄의 주석 열이 다른 줄과 맞지 않는다(`--model claude-opus-5` 뒤의 공백). 셀프 리뷰가 낼 수 있는 Nit이다.

open-session을 부른다 2026-10-31T18:47:48Z

## 셀프 리뷰(`/code-review origin/main`)

범위: base `55414f1c`(origin/main과 같다), 수정 파일 7, 미추적 3, 커밋 0.

- 표준 축이 낸 것: README `serve` 줄의 "plugins/models/<이름>의 이름" 문장이 이 커밋에서 거짓이다(`main.py`가 이름을 `anthropic_chat_model`에 바로 넘기고 파일은 04가 읽는다. 코드를 열어 확인했다). 주석 열이 어긋났다. `_write_model_plugin` 독스트링이 "그대로 둔다"로 코드(덮어쓴다)와 달랐다. `_main`이 `--model=값` 꼴을 놓친다. 시험 독스트링이 코드 상수와 맞댄다고 읽힌다.
- 명세 축이 낸 것: `test_거부하면_…`의 손으로 지은 `resume` 인자가 `--model` 없이 `main(`으로 갔다(안내 줄이 아니라 시험이 지은 인자라 허용 범위 밖). 나머지 요구는 충족이다.
- 고친 것: README 문장을 "기본 모델의 이름"까지로 줄이고 주석을 명령 위로 올렸다. 독스트링 정정. `_main`이 `--model=` 꼴도 인식한다. 시험 독스트링에 코드 상수와 맞대지 않는 이유(05가 상수를 걷는다)를 적었다. 위 손으로 지은 `resume` 호출을 `_main`으로 바꿨다.
- 남긴 것: 모델 매니페스트 리터럴 중복(저장소 파일, `MODEL_MANIFEST`, 두 e2e 스택)과 두 TS `DEFAULT_MODEL` 중복은 앱 경계를 넘는 판단 항목이라 두었다. 저장소 파일과 스택 픽스처의 동일성을 자동으로 재는 검사는 없다. 03이 요구하지 않았고 04가 모델 파일을 읽기 시작하면 `-m llm_widget`이 어긋남을 잡는다. `plugins/models/.gitkeep`은 Nit으로 둔다.
- 다시 돌린 것: ruff와 `tests/test_main.py`·`tests/test_default_model_plugin.py` 단일 실행 초록. 나머지 손으로 치는 다섯은 커밋의 pre-commit으로 갈음한다(결과는 커밋 뒤 적는다).
