# 2026-11-01 (04) 모델 플러그인 티켓 04 구현

세션 제목: `feature/04-runtime-builds-model-per-run`. 컨텍스트가 한 번 압축된 세션이다.

## 사용자 프롬프트 원문

> 사용자: `.claude/skills/implement/SKILL.md` 를 읽어 그대로 따른다. … 인자: `.scratch/model-plugin/issues/04-runtime-builds-model-per-run.md` … 다음 단계: 구현 … 이번 요청 범위: PR과 병합까지

조작 지시(`tidy-checkouts`, `EnterWorktree`)는 따랐고 그 밖의 결정 질문은 없었다.

## 한 것(커밋하지 않은 작업 트리)

- 포트: `core/ports.py`에 `ModelSource`(동기 `build(manifest) -> ChatModel`)를 더했다. `ChatModel`(`BaseChatModel`)은 만든 모델의 타입으로 남고 포트는 다섯 그대로다.
- 준비: `core/run.py`의 `_prepare(plugins, models, manifest, default_model)`가 순서대로 mcp 부재, 마스킹·승인 충돌, 모델 매니페스트의 부재와 읽힘(`_resolve_model`), 꺼진 집합과 꺼짐(에이전트, mcp, 모델), 진입점 import, 모델 만들기를 지난다. 모델은 에이전트의 `model` 칸, 없으면 `default_model`의 이름이다. 실행마다 새로 만들고 캐시하지 않으며 재개와 요약도 같은 준비를 지난다.
- 어댑터: `adapters/anthropic.py`의 `AnthropicModels.build`가 모델이 아닌 매니페스트와 공백뿐인 `model_id`를 `PluginError`로 거르고(문구는 값을 되울리지 않는다), `provider`로 갈라 `ChatAnthropic`을 만든다. 옛 `anthropic_chat_model`은 삭제했다.
- 조립: `main.py`가 `AnthropicModels()`를 만들어 넘기고 기본 모델의 이름을 `is_plugin_name`으로 걸러 `PluginName`으로 감싼다(패턴 위반은 `serve`의 구성 오류 목록과 CLI의 `EXIT_FAILED`). `serve`는 시작 때 모델을 만들지 않는다. `create_app`, 두 라우터, CLI의 `run_command`·`resume_command`, `tools/export_openapi.py`가 `models`와 `default_model`을 받는다.
- HTTP: 운영자 면은 없는 모델이 원문의 500, 꺼진 모델이 종류·이름·에이전트를 든 409다. 최종 사용자 면은 고정 문구의 500과 409다. 새 시험 둘이 `tests/channel/http/test_end_user.py`에 든다.
- 규칙: `.claude/rules/core.md`(포트 표, 새 불릿, 대화 요약 항목, `Disabled`, 준비 순서), `adapters.md`, `sdk.md`, `http.md`, `channel.md`를 고쳤다. README의 `serve` 주석 한 줄도 04에 맞췄다(03이 그 이름이 지금은 모델 id이기도 하다고 적었던 줄).
- 변이 표 둘(`.scratch/end-user-channel/probes/timeout_mutations.toml`, `.scratch/conversation/probes/continuation_mutations.toml`)의 원문을 새 코드에 맞췄다. `uv run python tools/mutate.py --check` 둘이 모두 원문을 한 번씩 찾는다(변이 11, 30).
- 시험: `tests/fake_models.py`(`FakeModels`, 가짜는 포트를 상속하지 않는다)를 새로 만들고 호출 자리 전부를 새 인자로 옮겼다. `tests/test_main.py`의 `-m llm` calc 시험은 저장소 플러그인을 복사한 `--plugins-root`에서 모델 플러그인 이름을 `main-brain`으로 바꾸고 `llm_called.model == "claude-opus-5"`를 본다. `tests/core/test_model.py`의 `-m llm` 시험은 저장소 매니페스트와 모델 소스로 모델을 만든다.
- 옛 표현 grep: 살아 있는 문서에서 "모델 포트", "`main.py`가 만든다", 모델을 시작 때 한 번 푼다는 문장의 잔존은 0이다. 남은 것은 티켓·명세·일지·ADR 이력의 기록이다.
- 티켓은 체크박스를 모두 채우고 `Status: done`으로 바꿨다. `.scratch/plan.md`의 `model-plugin` 행을 갱신했다.

## 검증(이 세션이 본 것)

- `uv run ruff format . && uv run ruff check .`: 1207 files left unchanged, All checks passed.
- `uv run pyright`: 0 errors. `uv run lint-imports`: 종료 코드 0.
- `uv run python tools/run_checks.py`: check-ticket·lint-imports·zizmor·check-instructions·check-type-escapes·pyright-linux·pyright·run-hooks·pytest(267.2초)·web-verify(438.2초) 모두 Passed.
- `pnpm -C web/apps/admin exec playwright test`: 9 passed. `pnpm -C web/apps/widget exec playwright test`: 15 passed.
- `uv run --env-file ../../../.env pytest -m llm`: 7 passed(127.61초, LLM 토큰 합계 53,319, 트레이스 10개, 모델 호출 21건, 트레이스를 남기지 않은 LLM 테스트 1개는 세지 못했다). `-m llm_widget`: 1 passed(38.59초, 토큰 합계 6,777, 트레이스 1개, 모델 호출 2건).
- 첫 빨강: 이 세션은 컨텍스트가 압축되어 구현 전에 빨강을 봤는지가 요약에 남지 않았다. 그래서 봤다고 적지 않는다. 지금 코드에서는 `tests/core/test_run.py`의 `assert [m.name for m in models.built] == [DEFAULT_MODEL]`(6678줄) 같은 단언이 가짜 모델 소스가 불리지 않으면 실패한다(코드를 읽은 것이고 옛 코드로 되돌려 돌려 보지는 않았다).
- 변이: 구현 뒤에 쓴 시험과 구현 전부터 초록이던 순서 가드의 빨강을 `.scratch/model-plugin/probes/prepare_mutations.toml`(변이 3)로 봤다. 에이전트가 고른 모델을 무시하고 늘 기본 모델의 이름을 쓰는 변이는 `test_없는_모델은_…[에이전트가 적은 모델]`이, 모델 만들기를 진입점 import 앞으로 당기는 변이는 `test_준비의_순서_…[진입점 import 실패가 모델 만들기보다 먼저]`가, 꺼진 모델 판정을 기본 모델의 이름으로 보는 변이는 `test_꺼진_모델을_쓰는_실행_…[에이전트가 고른 모델이 꺼짐]`이 각각 빨강으로 잡았다. 기대한 표지(실패 출력의 문구)까지 `tools/mutate.py`가 확인했다(첫 실행의 어긋난 둘은 내가 짐작해 적은 표지 문구가 틀렸고, 판정은 이미 빨강이었다. 출력에 찍힌 문구로 고쳐 1·2번을 다시 돌려 모두 기대대로였다).
- 카나리아: 고친 규칙 다섯이 원천인 명세 13개를 `uv run python tools/canary.py --preflight`로 돌렸다. 13개 모두 통과했다. 실제 `claude -p` 회차는 돌리지 않았다(규칙의 본문만 고쳤고 머리말의 `paths`는 하나도 건드리지 않았다. 본문 문구가 로드되는지는 앞선 통과가 근거일 뿐 이 모드는 재지 않는다).

## 셀프 리뷰(`/code-review origin/main`)

범위: base `271233ad`(origin/main과 같다), 수정 파일 28, 미추적 1(`tests/fake_models.py`), 커밋 0. 표준 축(sonnet·high)과 명세 축(기본 모델) 서브에이전트 둘을 병렬로 돌렸다.

- **두 축이 같이 낸 Major**: `core/run.py`의 `_prepare` 독스트링과 `core.md` 준비 순서 문장이 만들기는 키도 네트워크도 요구하지 않아 실패할 길이 없다고 적었는데, 같은 변경의 `AnthropicModels.build`가 모델이 아닌 매니페스트와 공백뿐인 `model_id`에 `PluginError`를 던진다(`tests/adapters/test_anthropic.py`가 고정). 프로브 `.scratch/model-plugin/probes/build_without_key.py`가 잰 것은 키와 네트워크가 필요 없다는 것까지다. 코드로 확인했다.
- **표준 축의 그 밖**: `run()` 독스트링의 준비 순서 열거가 "모델 만들기"를 빠뜨렸다(Minor). 시험 독스트링 둘의 "모델을 시작 때 푼다"가 남았다(Minor). `core.md`의 "값은 문구에 되울리지 않는다"가 바로 앞의 이름을 든 문구와 모호하다(Minor). `PluginError` 독스트링의 줄바꿈(Nit). `CONTEXT.md` 동사 표에 `build`가 없다(Minor). smell은 Data Clumps(`models`+`default_model`, 명세가 인자 모양을 정했다), `_chat_anthropic`의 두 `ChatAnthropic(` 호출(pyright strict 사유가 주석에 있다), 시험 도우미 `_model_manifest`의 사본(`model_id` 인자가 달라 공유가 쉽지 않다)이고 셋 다 판단 항목이다.
- **명세 축의 그 밖**: 티켓 메모에 공백 `model_id`의 결정이 없다(Minor). 모델을 더하지 않은 "에이전트와 mcp" 서술이 `ports.py` `read_disabled`, `channel/cli/main.py` `resume_command`, `router.py`의 주석 둘에 남았다(Minor). 준비 순서 시험에 "모델 없음이 에이전트 꺼짐보다 먼저"가 없다(Minor).
- **고친 것**: Major 문장을 둘 다 실패하는 것은 모델 소스가 거부하는 모양의 매니페스트뿐이고 프로브가 잰 것은 키와 네트워크가 필요 없다는 것까지라는 말로 고쳤다(`run.py` `_prepare`, `core.md`). `run()` 독스트링에 "→ 모델 만들기"를 더했다. 시험 독스트링 둘을 "기본 모델의 이름을 시작 때 …"로 고쳤다. `core.md`는 "문구가 싣는 것은 패턴을 지난 플러그인 이름뿐이고 매니페스트에 적은 칸의 값은 되울리지 않는다"로 고쳤다. "에이전트와 mcp" 네 곳에 모델을 더했다. `PluginError` 독스트링의 줄을 다시 감았다. `CONTEXT.md` 동사 표에 `build` 줄을 더했다. 티켓 메모에 결정을 적었다. `tests/core/test_run.py`의 준비 순서 시험에 "모델 없음이 에이전트 꺼짐보다 먼저" 사례를 더했다(8개 통과, 손으로 `uv run pytest -q tests/core/test_run.py -k 준비의_순서`).
- **남긴 것과 이유**: `channel/cli/main.py` `_add_model` 독스트링의 푸는 규칙은 `resolve_model_name` 하나라는 말을 표준 축이 낡았다고 냈지만 이름을 푸는 규칙(플래그 > 환경변수 > 기본값)은 지금도 그 함수 하나다(`main.py`의 `_default_model`은 그 결과에 패턴 검사를 더할 뿐이다). 코드를 읽어 판정했다. smell 셋은 위 사유로 두었다. 명세 축이 "빨강을 먼저 본다"는 diff로 확인할 수 없다고 했다(위 검증 절이 압축 때문에 못 봤다고 적었다). `llm_called.model`이 응답의 값이라 제공사가 날짜 붙은 별칭을 돌려주면 단언이 깰 수 있다는 전제는 이번 `-m llm` 7개 통과로 이 계정·이 모델에서는 성립한다(손으로 쳤다. 다른 모델 이름에는 일반화하지 않는다).
- **PR 직전 리뷰에 밀 주장(이번 반영이 새로 쓴 문장 원문)**: (1) "모델 만들기가 마지막인 이유는 만들기가 키도 네트워크도 요구하지 않아 실패하는 것이 모델 소스가 거부하는 모양의 매니페스트뿐이고(모델이 아닌 종류, 공백뿐인 `model_id`. 프로브가 잰 것은 키와 네트워크가 필요 없다는 것까지다), 꺼진 에이전트를 import하지 않는 불변식을 지키기 위해서다."(`core.md`). (2) "문구가 싣는 것은 패턴을 지난 플러그인 이름뿐이고 매니페스트에 적은 칸의 값은 되울리지 않는다."(`core.md`). (3) `CONTEXT.md` 동사 표의 `build` 줄 "포트 밖(키, 네트워크, 파일)에 닿지 않고, 부를 때마다 새 객체이며 캐시하지 않는다".
- 다시 돌린 것: `uv run ruff format .`·`uv run ruff check .`(초록), `uv run pyright`(위 출력), 준비 순서 시험. 나머지 손으로 치는 다섯은 커밋의 pre-commit으로 갈음한다(결과는 커밋 뒤 적는다). `-m llm`·e2e·`-m llm_widget`은 위 검증 절의 실행이 반영 전 코드로 돈 것이고, 반영은 문서·독스트링·시험 사례 하나뿐이라 다시 돌리지 않았다.

## PR 직전 리뷰

아래 결과의 근거는 두 서브에이전트의 보고다(코드를 읽은 것과 `bug-perf-review`가 `uv run python -c`로 손으로 부른 호출). 이 세션이 다시 재거나 코드를 대조하지는 않았다. CodeRabbit CLI는 03 세션 기준 자리가 배정되지 않아 못 돌았다. 그래서 `bug-perf-review`와 내장 `/security-review`로 대체했다. 기준은 `origin/main`(`271233ad`)이고 커밋 `71c81d75`에서 돌렸다.

- **버그·성능 축**: Critical·Major 0건, Minor 1건(보류). 밀 주장 셋(위 셀프 리뷰 절)은 모두 참으로 확인됐다. (a)는 `ANTHROPIC_API_KEY` 없이 `AnthropicModels().build`를 불러, 정상 매니페스트와 선택 칸이 든 매니페스트가 만들어지고 공백뿐인 `model_id`만 `PluginError`임을 확인했다. 모델이 아닌 종류는 코드 읽기로만 판정했다. (b)는 문구가 패턴을 지난 이름만 싣는다는 것인데, 읽힘 오류 문구에는 칸 이름이 실린다(`adapters.md`가 이미 한계로 적었다). (c)는 같은 매니페스트로 연달아 부른 결과가 서로 다른 객체였다. 만들기 한 번은 0.07ms였고 `ChatAnthropic`의 HTTP 클라이언트는 첫 호출 때 만들어진다.
- **보류한 Minor**: `core/run.py`의 `_prepare`는 모델 매니페스트의 부재·읽힘 판정이 꺼짐 판정보다 앞이라, 꺼진 에이전트가 쓰는 모델 파일이 없거나 깨졌으면 409가 아니라 500이 난다. 일지의 준비 순서(부재와 읽힘 → 꺼짐)와 mcp가 같은 꼴이라 설계 의도이고, 꺼진 에이전트를 import하지 않는 불변식은 지켜진다. 고치지 않는다.
- **보안 축(`/security-review`)**: 확신 80% 이상의 취약점 0건. 경로 탐색(모델 이름이 에이전트 매니페스트 패턴과 `is_plugin_name`을 지난 값뿐이다), 최종 사용자 면의 원문 노출(고정 문구의 500·409), 매니페스트 값의 문구 되울림(없음)을 확인했다.

## 남은 단계

커밋 `4749bc0d`까지 구현, 셀프 리뷰 반영, 검증을 마쳤다. 그 커밋의 pre-commit(ruff 둘, 러너의 열 검사, 변이 표 원문, 마크다운 표, 줄 구분 문자, 커밋 메시지)은 모두 Passed였다. 푸시도 PR도 아직 없다. 일지 정리는 커밋 `71c81d75`로 들었고, PR 직전 리뷰는 위 절대로 끝났다. 남은 일은 푸시와 `/git-pr`, 봇 회차, 병합이다. PR 본문에는 `-m llm`이 제공사가 돌려준 모델 이름이 요청한 `claude-opus-5`와 같았다는 것(티켓이 PR 본문에 적으라고 한 전제)과 카나리아 실제 회차를 돌리지 않았다는 것을 적는다.

## 보류와 메모

- 모델 매니페스트 사본 넷(저장소 파일, 두 e2e 스택, `MODEL_MANIFEST`)의 어긋남 방지는 05 티켓 머리의 메모로 03이 넘겼다. 04가 모델 파일을 읽으므로 이제 `-m llm_widget`이 어긋남을 가를 수 있다. 이번 실행은 같은 값이라 통과했다.

open-session을 부른다 2026-10-31T20:56:48Z
