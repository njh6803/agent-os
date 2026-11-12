# 01: 계약 — 모델 파일에 제공사 `openai-compatible`과 모델 서버의 주소·키 변수 칸이 생기고, 모델 소스가 제공사를 모르는 모듈로 옮긴다

**What to build:** 운영자가 모델 플러그인의 `plugin.toml`에 `provider = "openai-compatible"`과 모델 서버의 주소 `base_url`을 적고, 키가 필요한 서버면 `api_key_env`에 환경 변수의 이름을 적으면 그 파일이 읽힌다. 관리 API로 그 플러그인의 매니페스트를 읽으면 `base_url`과 `api_key_env`가 파일에 적은 글자 그대로 실리고, 다른 모든 종류와 `anthropic` 모델의 응답에는 두 칸이 `null`로 실린다. 관리 화면의 플러그인 상세에서도 그 주소와 변수 이름이 보인다. 지금의 `anthropic` 모델 파일은 한 글자도 고치지 않고 그대로 읽히고 그대로 돈다. 잘못 적으면(`openai-compatible`인데 `base_url`이 없다, 주소 모양이 아니다, `http`·`https`가 아니다, 사용자 정보가 들었다, 호스트가 없다, 쿼리 문자열이 있다, 변수 이름의 꼴이 틀렸다, `anthropic` 파일이나 모델이 아닌 종류가 두 칸을 적었다) 읽는 단계에서 어느 칸이 틀렸는지와 함께 거부되고, 문구는 적은 값을 되울리지 않는다. 관리 화면 개발자에게는 생성 TS 타입에 제공사 값과 두 칸이 생긴다. 아직 붙지는 않는다. `openai-compatible` 모델로 실행을 치면 실행 전 구성 오류 `model 플러그인 <이름> 의 provider openai-compatible 에 붙는 어댑터가 아직 없다`로 끝나고 트레이스가 남지 않는다. 같은 티켓에서 모델 소스가 제공사를 모르는 모듈(`adapters/models.py`)로 옮기고, `adapters/anthropic.py`에는 Anthropic 모델을 만드는 것만 남는다.

이 기능의 계약 티켓이고 05를 막는다(06은 05를 거쳐 막힌다). 계약은 sdk의 `ModelProvider`와 매니페스트의 두 칸, `openapi.json`, 생성 TS 타입이다(ADR 0057 Consequences "계약 변경이 첫 티켓이다"). 끌고 오는 것은 모델 소스의 모듈 나눔과 임시 거부 갈래, 관리 화면의 픽스처와 스토리와 시험 하나와 사진 정답, `.claude/rules/sdk.md`의 모델 항목, `.claude/rules/adapters.md`의 모델 소스 항목이다. 모듈 나눔은 명세의 묶음 D에서 이 티켓으로 옮겼다(to-tickets에서 사용자가 여섯 장 분할을 골랐다). 따로 떼면 이 티켓이 지금의 Anthropic 모듈에 임시 갈래를 넣고 다음 티켓이 그것을 새 모듈로 다시 옮겨야 한다. 리뷰의 질문은 "동작하나"가 아니라 이 모양과 이름으로 오래 살 수 있느냐다.

**병합 뒤에 틈이 있다.** 이 티켓만 병합된 개발 브랜치에서 `openai-compatible` 모델을 쓰는 실행은 위 문구의 실행 전 구성 오류로 끝난다. `anthropic` 모델은 바뀌지 않는다. 05가 이 갈래를 실제 어댑터로 바꾸고 이 문구를 지운다. 이 티켓이 쓰는 문장(독스트링, sdk의 칸 설명, rules)은 틈 동안에도 참이어야 한다. `openai-compatible`이 읽히고 관리 API에 보인다는 것과 아직 붙지 않는다는 것을 함께 말하고, 모델 서버에 붙는 동작은 05가 쓴다. 이 티켓의 PR에는 로컬 모델 시험의 조건이 붙지 않는다. 돌릴 시험이 아직 없기 때문이다(ADR 0058 결정 "첫 적용").

근거는 `.scratch/local-model/spec.md`의 "매니페스트", "계약과 관리 화면"과 그 2026-11-12 주석, "모델 소스와 모듈"과 그 주석, "규약 문서"의 마지막 항목과 그 주석, "고칠 자리의 묶음"의 A 줄과 그 주석, Testing Decisions의 "sdk(A)"·"관리 화면(A)"과 그 주석이다. 측정은 `.scratch/local-model/probes/openai_compat.py`(주소의 경로와 쿼리·조각 사례 `path_plain`, `path_trailing_slash`, `path_without_v1`, `path_with_query`, `path_with_fragment`)와 그 `README.md`이고 다시 돌리지 않는다. 앞선 결정은 ADR 0057의 결정 "제공사", "모델 파일", "주소는 비밀이 아닌 것으로 본다"와 그 2026-11-12 이력 "모델 파일의 주소에 쿼리 문자열이 있으면 읽는 단계에서 거부한다", ADR 0049(원격 MCP 서버의 주소 규칙과 헤더 변수 이름의 꼴), ADR 0040(모델은 플러그인이고 모델 만들기는 키도 네트워크도 요구하지 않는다), ADR 0010(직렬화 스키마에서 선택 칸도 required)이다. 임시 갈래의 선례는 mcp-http 01이 http 갈래에 둔 임시 실패다(`.scratch/mcp-http/issues/01-contract-mcp-server-transport-stdio-or-http.md`).

**Blocked by:** None (can start immediately)

**Status:** done

### sdk

- [ ] `ModelProvider`에 값 `openai-compatible`을 더하고, 매니페스트에 선택 칸 `base_url`과 `api_key_env`를 더한다. 둘 다 문자열이고 기본은 없음이다. `schema_version`은 `"1"` 그대로다
- [ ] `base_url`은 글자 그대로 보관한다(`AnyHttpUrl`을 쓰지 않는다). 검사는 원격 MCP 서버의 `url`과 같은 규칙 넷(주소 모양이 아니다, `http`나 `https`가 아니다, 사용자 정보가 들었다, 호스트가 없다)이고, 같은 규칙을 두 자리에 따로 적지 않고 나눠 쓴다. 문구는 칸 이름만 다른 같은 모양이고 적은 값을 되울리지 않는다
- [ ] `base_url`에만 규칙이 하나 더 있다. 조각(`#` 뒤)을 뗀 주소에 `?`가 있으면 `base_url 에 쿼리 문자열을 적을 수 없다`로 거부한다. 빈 쿼리(`…/v1?`)도 거부하고, 조각이 든 주소는 받는다. 원격 MCP 서버의 `url` 규칙은 바꾸지 않는다
- [ ] `api_key_env`는 `[server.headers]`의 환경 변수 이름과 같은 타입 제약을 써서(글자·숫자·밑줄만이고 비지 않는다) 그 패턴이 `openapi.json`에 실린다
- [ ] 종류와 제공사에 맞지 않는 칸은 "적었는가"로 판정해 읽는 단계에서 거부한다. `openai-compatible`인데 `base_url`이 없으면 `provider 가 openai-compatible 인 model 플러그인은 base_url 이 필요하다`, `anthropic`인데 둘 가운데 하나를 적었으면 `provider 가 anthropic 인 model 플러그인은 <칸 이름> 을 갖지 않는다`, 모델이 아닌 종류가 적었으면 지금의 `<종류> 플러그인은 <칸 이름> 을 갖지 않는다`(그 검사가 도는 칸의 목록에 둘을 더한다)다. 문구가 싣는 것은 칸 이름과 제공사 값뿐이다
- [ ] 두 칸의 설명이 `openapi.json`에 실린다. `base_url`은 모델 서버의 API 뿌리까지 적는다는 것(vLLM이면 `/v1`까지이고, 그 뒤에 `chat/completions`가 붙으며 끝의 `/`는 있어도 없어도 같다), `api_key_env`는 키 값이 아니라 런타임이 호출 때 읽을 환경 변수의 이름이라는 것이다. 계약에 실리는 설명은 한 줄로 쓰고 논증은 `#` 주석에 둔다(`.claude/rules/http.md`)
- [ ] 직렬화 스키마에서 두 칸은 다른 선택 칸처럼 required이고 `null`을 허락한다
- [ ] sdk 매니페스트 시험이 명세 Testing Decisions의 "sdk(A)" 사례를 모두 덮는다. `openai-compatible`에 `base_url`만 적은 파일과 `api_key_env`까지 적은 파일이 읽히고 값이 글자 그대로다. 거부와 그 위치·문구는 `base_url` 없음, 주소 모양 아님, `http`·`https` 아님, 사용자 정보, 호스트 없음, 쿼리(빈 쿼리 포함), `api_key_env`의 꼴, `anthropic` 파일의 두 칸, 모델이 아닌 종류의 두 칸이다. 조각이 든 주소는 읽힌다. 거부 문구에 적은 값이 없다. 직렬화 스키마의 두 칸이 required이고 `null`을 허락한다. 지금의 `anthropic` 파일이 그대로 읽힌다(스토리 3)

### 모델 소스의 모듈과 임시 갈래

- [ ] 모델 소스를 제공사를 모르는 모듈 `adapters/models.py`로 옮긴다. 그 모듈이 모델 소스와, 기본 모델의 이름을 정하는 `resolve_model_name`과 `AGENT_OS_MODEL`을 든다. `adapters/anthropic.py`에는 `ChatAnthropic`을 만드는 것과 상한 16000만 남는다. 모델 서버 모듈(`adapters/openai_compatible.py`)은 05가 만든다
- [ ] 모델 소스는 포트 `ModelSource`의 구현 하나이고 `provider`로 갈라 제공사의 모듈에게 모델을 만들게 한다. 모델이 아닌 종류의 매니페스트와 공백뿐인 `model_id`의 거부는 가르기 전에 있어 두 제공사에 같다. 모델 소스의 타입 이름도 제공사를 말하지 않게 짓는다(파일의 이름과 독스트링이 거짓이 되는 것을 명세가 거부했다)
- [ ] `openai-compatible` 갈래는 `PluginError("model 플러그인 <이름> 의 provider openai-compatible 에 붙는 어댑터가 아직 없다")`를 낸다. 시험이 둘이다. 그 매니페스트로 모델을 만들면 모델 소스가 이 문구의 `PluginError`를 내고, 그 모델을 `--model`로 준 CLI `run`은 종료 코드가 0이 아니며 진단에 이 문구가 있고 트레이스를 남기지 않는다. pyright는 갈래가 있는지만 보고 무엇을 던지는지는 보지 않으므로 이 시험이 그 자리를 덮는다
- [ ] 옮기며 닿는 자리를 고친다. 명세의 주석이 `grep -rn "AnthropicModels\|resolve_model_name\|MODEL_ENV"`로 손으로 센 자리는 `main.py`의 import 한 줄, 모델 이름을 푸는 한 줄, 조립 자리 셋, `tests/adapters/test_anthropic.py`, `tests/test_main.py`(`MODEL_ENV`의 import 한 줄과 그것을 쓰는 여섯 자리, 모델 소스를 바꿔 끼우는 세 자리), `tests/core/test_model.py`다. 함수와 상수의 이름을 지키면 모델 이름을 푸는 줄과 `MODEL_ENV`를 쓰는 자리는 그대로이고 import만 바뀐다. 모델 소스의 타입 이름이 바뀌므로 조립 자리 셋과 바꿔 끼우는 세 자리는 바뀐다. 모델 소스와 모델 이름을 푸는 함수의 시험도 모듈을 따라 옮긴다(`tests/`는 `src/`를 미러링한다, `CLAUDE.md`의 레이어). `channel/cli/main.py`의 독스트링은 함수 이름 `resolve_model_name`을 지키면 그대로이고, `tools/hook_probe_citing_doc.py`의 독스트링은 지난 사례의 기록이라 고치지 않는다
- [ ] `anthropic` 모델의 실행은 바뀌지 않는다. 지금의 모델 소스 시험과 CLI·`serve` 시험이 고친 import 말고는 그대로 초록이다

### 계약 파일과 생성 타입

- [ ] `uv run python tools/export_openapi.py`로 `openapi.json`을 다시 뽑고 생성 TS 타입을 다시 만들어 같은 커밋에 싣는다. 제공사 값, 두 칸, 키 변수 이름의 패턴, 두 칸의 설명이 실린다
- [ ] 관리 API 응답의 시험을 `tests/test_server.py`의 선례(`test_모델_행은_제공사_모델_id_파라미터를_매니페스트에_싣는다`, `test_http_모양의_mcp_매니페스트는_파일에_적은_글자_그대로_내보낸다`)대로 둔다. 임시 플러그인 루트에 `openai-compatible` 매니페스트를 두고 응답의 `base_url`과 `api_key_env`가 파일에 적은 글자 그대로인지 본다. 주소는 대문자가 든 호스트와 끝의 `/`로 적어 `AnyHttpUrl`을 쓰지 않은 결정을 고정한다(스토리 14)

### 관리 화면

- [ ] 매니페스트 값을 생성 타입으로 적은 테스트 픽스처와 스토리에 두 칸을 더한다(명세는 `temperature`를 적은 줄로 세어 테스트 파일 셋에 열 줄, 스토리 파일 셋에 다섯 줄로 어림했다)
- [ ] 관리 화면의 플러그인 상세 시험에 사례 하나를 더한다. `openai-compatible` 모델의 매니페스트를 열면 주소와 키 변수 이름이 화면에 보인다. 새 스토리와 화면 변경은 두지 않는다
- [ ] 사진 정답을 `pnpm -C web visual:admin`으로 본다. 매니페스트를 그리는 자리가 `PluginDetail.tsx`의 `formatJson(plugin.manifest)` 하나이고 두 스토리의 매니페스트가 모든 칸을 `null`까지 싣으므로 `PluginDetail`의 `Enabled`와 `Disabled`가 모두 바뀔 것으로 본다(명세의 어림이고 렌더하지 않았다). 바뀐 사진은 두 칸의 줄이 는 것인지 보고 정답을 고치고, 그 밖의 사진이 바뀌면 까닭을 찾는다

### 문서

- [ ] `.claude/rules/sdk.md`의 모델 항목("값은 `anthropic` 하나", 모델 칸의 목록)을 고친다
- [ ] `.claude/rules/adapters.md`의 모델 소스 항목을 모듈의 자리와 임시 거부 갈래로 고친다. 모델 서버 어댑터의 동작은 05가 같은 항목에 쓴다
- [ ] rules를 고치기 전에 Skill 도구로 `writing-for-agents`를 부른다(`.claude/rules/agent-docs.md`). 고친 rules는 새 세션에서 불러 본다(작업 규약 3)

### 검증

- [ ] **빨강을 먼저 본다**(헌법 원칙 II). 첫 빨강은 sdk 매니페스트 시험, `openapi.json` 최신성 시험, 관리 API 응답 시험, 임시 갈래의 모델 소스 시험과 CLI 시험, 관리 화면의 플러그인 상세 시험이다
- [ ] **검증 명령이 모두 초록이다.** 손으로 치는 다섯에 더해 관리 화면 e2e(`pnpm -C web/apps/admin exec playwright test`. api-client가 바뀐다)와 사진 비교 `pnpm -C web visual:admin`을 친다. 생성 타입의 바뀐 몫이 위젯이 쓰는 api-client에 닿으면 위젯 e2e(`pnpm -C web/apps/widget exec playwright test`)도 친다. 모델 소스를 옮겨 실제 모델이 지나는 조립이 바뀌므로 `-m llm`도 친다
