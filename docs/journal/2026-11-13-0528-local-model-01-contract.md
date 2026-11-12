# 2026-11-13 (05:28) local-model 티켓 01 계약

세션 제목 `feature/01-contract-openai-compatible-model-provider`. 브랜치 `feature/01-contract-openai-compatible-model-provider`, 워크트리 `.claude/worktrees/01-contract-openai-compatible-model-provider`, 기준 커밋 `a4eea81ff`(origin/dev 위에서 땄고 그 뒤 origin/dev는 `f6e7cbb`까지 앞섰다). 모델 Sonnet 5.5 / high. next-session 지시문으로 연 새 세션이고, 첫 턴에 `tidy-checkouts`를 돈 뒤 `EnterWorktree`로 들어와 브랜치 이름을 바꿨다. 파일 이름의 시각은 컨텍스트가 인계 문턱을 넘어 이 일지를 처음 만든 때다. 이 일지는 인계 때문에 셀프 리뷰 직전에 만들었고, 커밋하지 않았다.

## 사용자 프롬프트

원문은 세션 기록(`C:\Users\User\.claude\projects\C--project-agent--claude-worktrees-01-contract-openai-compatible-model-provider\2c52db09-2ffa-49de-a34b-d1aff88421b6.jsonl`)의 첫 메시지다. 컨텍스트 압축을 한 번 지나 아래는 압축 요약이 옮긴 대로다.

> 사용자: `.claude/skills/implement/SKILL.md` 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent` 이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/local-model/issues/01-contract-openai-compatible-model-provider.md
>
> 다음 작업: 티켓 01(모델 제공사 값과 두 칸을 sdk 계약에 더하고 모델 소스의 모듈을 나눈다)
> 다음 단계: 구현
> 브랜치: feature/01-contract-openai-compatible-model-provider
> 모델: Sonnet 5.5 / high
> 읽을 것: docs/journal/2026-11-12-2214-local-model-tickets.md의 "다음"
> 이어받을 상태: 없음
> 이번 요청 범위: 구현·리뷰·커밋까지

PR은 열지 않는다(구현 스킬은 커밋에서 멈춘다). 지시문의 어디서 줄은 `tidy-checkouts`를 먼저 돌고 `EnterWorktree`(name은 브랜치의 마지막 토막)로 들어가 브랜치 이름을 바꾸라는 것이었다.

## 한 것

티켓 01의 구현이 끝났고 커밋하지 않은 채 작업 트리에 있다(`git status`가 원천).

- sdk: `ModelProvider.OPENAI_COMPATIBLE`, 선택 칸 `base_url`·`api_key_env`, 읽는 단계의 거부 규칙. 주소 네 규칙은 `_check_http_address`로 뽑아 원격 MCP 서버의 `url`과 나눠 쓴다. 쿼리 문자열 거부는 `base_url`에만 더했다.
- 어댑터: 새 `adapters/models.py`(`ManifestModels`, `resolve_model_name`, `MODEL_ENV`). `adapters/anthropic.py`는 `chat_anthropic`과 `MAX_TOKENS`만 든다. `openai-compatible` 갈래는 `PluginError`를 던지는 임시 갈래이고 문구는 티켓 그대로다.
- 계약: `openapi.json`과 TS 생성 타입을 같은 변경에서 다시 만들었다(두 칸 모두 직렬화 스키마에서 필수이고 null 허용).
- 관리 화면: 픽스처와 스토리 여섯 곳에 두 칸을 더하고 `PluginPage.test.tsx`에 시험 하나를 더했다. 사진 정답은 `PluginDetail`의 `Enabled`·`Disabled` 여덟 장(두 폭 × 라이트·다크)만 바뀌었고, 바뀐 것은 매니페스트 JSON에 두 줄이 늘어난 것이다. 기대와 실제를 나란히 본 것은 `enabled-1280-light` 한 장이고(그 사진에서 `"base_url": null,`·`"api_key_env": null,` 두 줄만 늘었다), 나머지 일곱은 같은 변경이 낸 같은 변화로 본 어림이다.
- 문서: `.claude/rules/sdk.md`와 `.claude/rules/adapters.md`의 모델 항목.
- 시험: sdk 매니페스트, 모델 소스, anthropic 모듈, CLI, 서버 응답의 글자 그대로 통과 시험. 구현 전의 빨강으로 확인된 것은 둘이다. sdk 시험은 `-x`로 첫 빨강(`test_제공사는_닫힌_열거이고…`)만 봤고, 모델 소스 시험은 `adapters/models.py`가 없어 수집 오류로 빨갰다. 서버·CLI·관리 화면 시험의 구현 전 빨강은 이 세션의 압축 요약에 남아 있지 않아 확인하지 못했다.
- 임시 갈래의 변이: 문구의 끝을 바꾸자 모델 소스 시험과 CLI 시험이 빨개졌고 되돌렸다.
- 티켓 `Status:`를 `done`으로 바꾸고 `uv run python tools/plan_table.py`를 돌렸다(`.scratch/plan.md` 변경). 이 티켓이 마지막이 아니어서(02~06이 남았다) 기능 계획의 `**끝:**` 줄은 달지 않았다.
- 카나리아: 규칙 둘을 바꿔 `sibling_overlap.py`가 명세 일곱을 알렸다. 사전 확인(`--preflight`)은 일곱 모두 통과했고, `adapters_rule_new_optional_fields.toml`과 `sdk_rule_two_limits.toml`은 실제로 돌려 둘 다 통과 4(claude 2.1.322)였다. 두 명세의 `# 최신 결과:` 줄을 고쳤고 `--shape`가 통과했다. 나머지 다섯(`sdk_rule_failure_cause`, `sdk_rule_shortcut_patterns`, `adapters_rule_boundary_exceptions`, `adapters_rule_rules_file_read`, `adapters_rule_http_close`)은 사전 확인만 했다. 바꾼 줄은 머리말(`paths`)이 아니라 본문이고 그 다섯이 묻는 항목은 건드리지 않았다. 그래도 실제로 돌리지 않은 것은 사실이라 PR 본문에 적는다.

## 검사 결과

- `uv run python tools/run_checks.py`: 모두 통과(pytest 934.8초, web-verify 1025.4초 포함). 이 실행은 카나리아 명세 고치기 전의 작업 트리에서 돌았다.
- `uv run ruff check .`와 `uv run ruff format --check .`: 통과.
- `pnpm -C web verify`: 통과(vitest 2156 통과, 1 skip).
- `uv run --env-file ../../../.env pytest -m llm`: 9 통과. `LLM 토큰 합계 63,567(입력 62,381, 출력 1,186). 트레이스 13개, 모델 호출 26건. 트레이스를 남기지 않은 LLM 테스트 1개는 세지 못했다.`
- `pnpm -C web visual:admin`: 처음에는 `PluginDetail` 넷이 빨개졌고(위 설명), `visual:admin:update`로 정답 여덟 장을 다시 만들었다. 다시 돌려 초록인지는 보지 않았다. 새 사진이 같은 환경에서 만든 것이라 한 번 더 도는 것은 PR의 CI `visual` 잡에 맡긴다.
- 관리 화면 e2e: 9개 중 8 통과. `decision.e2e.ts`의 첫 시험(승인 뒤 재개 스트림)이 `run_finished`를 5초 안에 못 봤다. 단독으로 다시 돌려도 같았고, 그 기대의 제한만 40초로 임시로 늘리면 통과했다(16.1초). 제한은 되돌렸고 `git status`가 e2e 폴더를 깨끗하다고 본다. 같은 시험이 이 변경이 닿지 않은 브랜치에서도 같은 까닭으로 실패했다고 일지 2026-10-30-11·2026-11-01-07·2026-11-11-2050이 적는다. 이 PC에서 MCP 픽스처 서버의 시작에 4~6초가 걸린다. 같은 시험을 이 변경 없는 `main`에서 돌려 대조하지는 않았다.
- 위젯 e2e: 16개 중 14 통과. 새로 고친 뒤 도는 실행에 붙는 시험 둘이 5초 제한에 걸렸고, `expect` 제한을 30초로 임시로 늘리면 둘 다 통과했다(7.4초, 10.1초). 설정은 되돌렸다. 같은 MCP 시작 지연으로 본다. 이것도 변경 없는 판과 대조하지 않았다. CI의 `e2e-widget` 잡이 판정한다.
- 관리 화면 e2e 로그에 `stack.ts:68`의 `rmSync` `EPERM`(시험 밖 오류)이 있었다. 제한을 늘려 통과한 단독 실행도 시험은 `ok`인데 이 오류 때문에 종료 코드가 1이었다(손으로 봤다). 일지 2026-11-01-07이 `stack.ts`의 `EPERM`으로 적은 것과 같은 종류로 보지만(어림), 그 일지도 첫 실행의 시험 밖 오류가 `EPERM`이었는지는 못 봤다고 적었다.
- 모델 소스 만들기 시간(일회용 점검, 근거로 쓰지 않는다): `ManifestModels().build`는 3회에 3ms, 가져오기는 5.6초(langchain). 이 변경이 실행 시간에 더하는 비용은 보지 못했다.

## 이 세션이 번복하거나 고친 것

- 규칙 문서를 쓰다 `writing-for-agents`를 먼저 불렀다.
- 임시 갈래의 문구 변이를 되돌렸다(`grep`으로 "아직 없다"를 확인했다).
- e2e 진단용으로 `decision.e2e.ts`와 위젯 `playwright.config.ts`를 임시로 고쳤다가 곧바로 되돌렸다.

## 셀프 리뷰(이 이어받은 세션)

범위: 기준 `a4eea81ff`, 수정 30개 파일, 커밋 0개, 미추적 3개(`models.py`, `test_models.py`, 이 일지). 표준 축(sonnet·high)과 명세 축 서브에이전트 둘을 병렬로 돌렸다. Critical 없음, Major 하나.

- 고친 것(Major): `ManifestModels.build`가 `chat_anthropic`에 `max_tokens`와 `temperature`를 넘기는 자리를 지나는 시험이 없었다(옛 `test_anthropic.py`는 모델 소스를 지나 쟀는데 옮기며 빠졌다). `test_models.py`에 `test_매니페스트의_max_tokens_와_temperature_가_모델에_닿는다`를 더했다. 인자 순서를 바꾼 변이를 일시로 넣어 그 시험이 빨개지는 것을 보고 되돌렸다(변이 파일 `tools/mutate.py`는 쓰지 않은 손 변이다). 명세 축 서브에이전트가 그 변이 순간의 파일을 읽어 "인자 순서가 뒤바뀐 채 디스크에 있다"고 냈는데, 이미 되돌렸고 `grep`으로 원래 순서를 확인했다.
- 고친 것(Minor): `tests/sdk/test_manifest.py`의 `test_openai_compatible_의_두_칸은_모델이_아닌_종류와_anthropic_에서만_막힌다`를 지웠다. 이름이 말하는 "모델이 아닌 종류"는 보지 않았고 읽히는 경우(893행)와 anthropic의 거부(`test_anthropic_은_주소와_키_변수를_갖지_못한다`)와 겹쳤다. 모델이 아닌 종류의 두 칸 거부는 `test_모델이_아니면_모델의_칸을_갖지_못한다`가 맡는다.
- 넘긴 것: 05 티켓의 옛 표현 목록(작업 규약 4의 잔존 grep)에 글자가 달라 임시 문구 grep에 안 걸리는 두 문장(`sdk/manifest.py`의 "모델 서버에 붙는 동작은 아직 없다", `.claude/rules/sdk.md` 모델 항목의 "어댑터는 아직 없다")을 더했다. 05의 문서 항목에는 `core.md` 모델 포트 행의 구현 칸("`ChatAnthropic`")과 `core/ports.py`의 `ModelSource` 독스트링을 더했다.
- 남긴 것과 이유: (a) `core.md` 포트 표의 구현 칸은 이 티켓에서 고치지 않았다. 고쳐 보았다가 되돌렸다. 그 파일을 원천으로 든 카나리아 명세 여섯(`core_rule_*`)이 걸리고 02 워크트리도 같은 파일을 고치고 있으며, 지금 문장은 거짓이 아니라서(`ManifestModels`가 만드는 것이 `ChatAnthropic`) Minor로 판정했다. (b) `base_url`의 앞 공백·호스트 안 공백·잘못된 포트(`:99999`)는 읽는 단계가 받는다. 티켓이 정한 네 규칙 밖이고 원격 MCP `url`도 같은 검사라 기존 동작이며, 요청을 만드는 05에서 첫 호출의 실패로 드러난다. (c) `adapters/models.py`의 미래형 주석("어댑터 티켓이 이 갈래를…")은 티켓이 요구한 임시 갈래 표지이고 05가 지운다. (d) 지난 프로브 `.scratch/approval-rules/probes/all_deny_resume_call.py`는 기록이라 고치지 않았다(위와 같다).
- 주장 검증(서브에이전트 둘의 보고이고 이 세션이 재현하지 않았다): 표준 축이 `base_url`·`api_key_env`의 경계 입력(조각, 빈 쿼리, 대문자 호스트, 사용자 정보, 호스트 없음, 하이픈이 든 키 모양)을 `uv run python`으로 대 보았다고 보고했고, 명세 축이 거부 문구를 파일시스템 읽기를 지나게 해 값이 되울리지 않는 것을 확인했다고 보고했다. 원격 MCP `url`의 동작과 문구는 바뀌지 않았다. `AnthropicModels`의 살아 있는 문서 잔존은 0건이다.
- 돌린 명령: `uv run pytest tests/adapters/test_models.py tests/sdk/test_manifest.py`는 228 통과, `uv run ruff check .`와 `uv run ruff format --check .`는 통과. 전체 게이트는 커밋의 pre-commit이 돌린다(결과는 커밋 뒤 PR 본문에 적는다).

## PR 직전 리뷰와 PR

origin/dev(`f6e7cbb12`) 위로 rebase했다(충돌 없음, `tools/plan_table.py --check` 종료 0). `coderabbit-review` 서브에이전트가 CLI 0.7.5로 `coderabbit review --agent --committed --base origin/dev`를 끝까지 돌렸다(`review_completed`, 34개 파일, `Seat: not assigned`, 서브에이전트의 보고이고 이 세션이 재현하지 않았다). 즉시 고칠 Critical·Major는 없었다.

- 유효, 보류(Minor): `base_url`이 앞 공백·개행·잘못된 포트를 받는다. 원격 MCP `url`과 나눠 쓰는 `_check_http_address`의 동작이라 고치면 `url`의 동작이 바뀌고, 티켓이 `url` 규칙을 바꾸지 않는다고 정했다. 요청을 만드는 05 티켓의 항목으로 넘겼다(받는 쪽은 05이고 05의 Blocked by가 01을 포함한다). 고치는 값은 한 함수에 검사 둘을 더하고 `url` 시험 사례를 더하는 정도다(어림).
- 유효, 보류(Minor): 경로·`;` 매개변수·조각에 실린 비밀은 막지 못한다. 코드로 막을 수 없고 ADR 0057의 "주소는 비밀이 아닌 것으로 본다"가 그 결정이다. 05 항목에 같이 적었다.
- 오탐: CodeRabbit이 `openapi.json`에서 낸 "클라이언트와 `web/apps/admin`의 `provider` 분기 일관성" 지적은, 생성 타입이 `"anthropic" | "openai-compatible"`을 이미 싣고 admin 소스에 `provider`로 분기하는 코드가 없어 깨질 곳이 없었다(서브에이전트가 확인했다고 보고했다).

## 남은 일과 보고에 적을 것

- 커밋 직전에 `git branch --show-current`와 `uv run python tools/sibling_overlap.py`를 쳤다. 새 번호 겹침은 없다. `core.md`를 고쳤을 때는 그 파일을 원천으로 든 카나리아 여섯의 알림이 났고, 되돌린 뒤 다시 친 `sibling_overlap.py`는 종료 코드 0에 그 알림이 없었다(손으로 봤다). origin/dev가 `f6e7cbb`까지 앞섰고 이 브랜치와 겹치는 파일은 `.scratch/plan.md` 하나다(02·04 워크트리와 mcp-shutdown-spec도 같은 파일을 고쳤다). 병합 때 글자 충돌이 나면 `uv run python tools/plan_table.py`로 다시 만든다. PR은 열지 않는다.
- 닫는 보고에 적을 것: (1) `tidy-checkouts`가 휴지통에 남긴 막힌 항목(esbuild·node가 쥔 것)과 `04-fake-model-server-fixture` 워크트리는 이 세션의 첫 턴이 사람에게 넘긴 것이다(압축 요약이 적은 대로이고 이 세션이 그 출력을 다시 읽지는 않았다). (2) `.scratch/approval-rules/probes/all_deny_resume_call.py`는 지난 프로브라 고치지 않았지만 `AnthropicModels`를 import해 지금 돌리면 깨진다. (3) 관리·위젯 e2e의 시간 지연 실패와 `EPERM`(위). (4) 카나리아 다섯을 사전 확인만 한 것(위). (5) `visual:admin`을 정답을 다시 만든 뒤 다시 돌지 않은 것.
- 커밋하지 않은 변경을 되돌릴 일은 없다. 새 세션은 `git status`로 시작하면 된다.

## 인계

제목을 `feature/01-contract-openai-compatible-model-provider (인계함)`으로 바꿨고 워크트리 잠금을 풀었다. 멈출 백그라운드 작업은 없었다.

open-session을 부른다 2026-11-12T20:31:56Z
