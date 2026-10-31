# 01: 계약 — 모델 매니페스트가 제공사·모델 id·파라미터를 들고, 에이전트가 `model`로 모델을 고른다

**What to build:** 운영자가 `plugins/models/<이름>/plugin.toml`에 공통 넷과 함께 `provider = "anthropic"`, `model_id`, 선택 `max_tokens`·`temperature`를 적으면 그 매니페스트가 읽히고, 관리 API의 목록(`GET /plugins`)과 상세가 새 칸을 싣는다. 에이전트 매니페스트에는 선택 칸 `model = "<모델 플러그인 이름>"`을 적을 수 있다. 오타(모르는 칸, 모르는 제공사, 빈 모델 id), 범위 밖의 값(`max_tokens = 0`, `temperature = 1.5`), 종류에 맞지 않는 칸(mcp에 적은 `model_id`, 모델에 적은 `model`)은 읽는 단계에서 거부된다. 공통 넷만 적은 옛 모델 파일은 거부되어 목록에서는 그 파일의 행만 표지 행이고 상세는 500이다. 관리 화면은 새 칸을 아는 생성 타입으로 컴파일되고, 모델 상세는 새 칸을 매니페스트 JSON 그대로 보인다.

이 기능의 계약 티켓이고 03과 04를 막는다(05·06은 04를 거쳐 막힌다). 계약은 sdk의 칸·열거·종류별 거부, `openapi.json`, 생성 타입이다. 끌고 오는 것은 생성 타입을 단 관리 화면의 리터럴, 매니페스트 JSON을 그리는 모델 상세의 사진 정답, 공통 넷만 적어 sdk가 바뀌는 순간 깨지는 모델 픽스처 둘, `.claude/rules/sdk.md`의 두 문장이다. **포트의 모양(`ModelSource`)과 `default_model`은 여기 들지 않는다.** 둘 다 `openapi.json`에 실리지 않고, 포트를 바꾸면 core가 모델 매니페스트를 읽어야 모델을 얻어 런타임 전체가 끌려온다(명세의 "계약" 절 2026-10-31 명세 검토 주석). 리뷰의 질문은 "동작하나"가 아니라 이 칸 이름과 모양으로 오래 살 수 있느냐다.

**병합 뒤에 틈이 있다(to-tickets에서 사용자가 분할을 골랐다).** 런타임은 아직 모델 매니페스트를 읽지 않는다. 에이전트의 `model` 칸은 받아들여지되 효과가 없어 그 에이전트는 기본 모델로 돌고, 모델 파일의 `max_tokens`·`temperature`도 효과가 없다. to-tickets 시점(main `d4221552`)에 저장소에 `model`을 적은 에이전트는 없다. 04가 이 틈을 닫는다. 이 티켓이 쓰는 문장(독스트링, 주석, rules)은 틈 동안에도 참이어야 한다. 런타임이 무엇을 하는지가 아니라 계약이 무엇을 약속하는지를 말한다(conversation 01과 plugin-toggle 01의 규칙).

근거는 `.scratch/model-plugin/spec.md`의 "모델 매니페스트의 칸", "에이전트 매니페스트의 `model` 칸", "계약" 절과 그 2026-10-31 명세 검토 주석, Testing Decisions의 "sdk 매니페스트"·"HTTP 두 면"·"관리 화면"이다. 앞선 결정은 ADR 0040, ADR 0008의 2026-10-31 이력(`schema_version` "1" 유지), ADR 0010의 2026-09-23 이력(늘 실리는 칸을 required로 내보낸다)이다. 받고 거부하는 경계는 프로브 `.scratch/model-plugin/probes/manifest_fields.py`가 sdk와 같은 설정의 시제품으로 쟀고, 거부의 표지는 그 `README.md`에 있다.

**Blocked by:** None (can start immediately)

**Status:** done

### sdk — 모델 매니페스트의 칸

- [x] **제공사는 sdk의 닫힌 열거 `ModelProvider`(`StrEnum`)이고 값은 `anthropic` 하나다.** 그 이름 그대로 `openapi.json`의 컴포넌트가 된다(`PluginKind`처럼 이름 있는 정의여야 생성 클라이언트가 재사용한다, ADR 0008). 둘째 제공사는 값 하나를 더하는 가산 변경이다(스토리 26)
- [x] **모델 종류는 `provider`와 `model_id`(비지 않은 문자열)가 필수이고, `max_tokens`와 `temperature`는 선택이다.** `max_tokens`는 `conversation_limit`과 같은 엄격 검증(`strict=True`, 1 이상)이고 sdk에 숫자 기본값을 두지 않는다. 없을 때의 16000은 04에서 어댑터가 든다. `temperature`는 0 이상 1 이하의 엄격한 실수이고, TOML의 정수 `0`·`1`은 실수 `0.0`·`1.0`으로 받는다
- [x] **거부 사례는 프로브 README의 표지 그대로 시험이 단언한다.** `max_tokens`의 `0`·`2.0`·`true`·`"16"`, `temperature`의 `1.5`·`-0.1`·`"0.5"`·`true`, 모르는 `provider`, 빈 `model_id`, 모르는 칸이다. 실패를 기대하는 시험은 pydantic 오류의 `type`이나 검증자의 문구로 까닭을 단언한다(`CODING_STANDARDS.md`). 받는 사례(정수 `0`·`1`의 `temperature`, 칸을 생략한 모델)도 같은 자리에서 본다
- [x] **모델이 아닌 종류가 네 칸 가운데 하나라도 적으면 거부한다.** 선례는 `tests/sdk/test_manifest.py`의 `test_mcp가_아니면_서버_표를_갖지_못한다`와 `test_에이전트가_아니면_한도를_갖지_못한다`다
- [x] **공통 넷만 적은 모델 매니페스트는 필수 칸이 없어 거부된다.** `schema_version`은 "1" 그대로다(ADR 0008의 2026-10-31 이력. 실행 경로가 읽은 적 없고 실물 파일도 없던 종류의 첫 필수 칸이라 버전을 올리지 않는다)
- [x] **칸 이름 `model_id`와 `model`이 pydantic의 보호 이름 공간 경고를 내지 않는다.** sdk가 `protected_namespaces`를 손대지 않는다(프로브가 2.13.5에서 쟀다. 설치된 판이 다르면 시험 하나로 경고가 없음을 본다)

### sdk — 에이전트의 `model` 칸

- [x] **에이전트 매니페스트의 `model`은 플러그인 이름 패턴(sdk의 `PluginName`)의 선택 칸이고 기본은 없음이다.** 없음은 기본 모델을 쓴다는 뜻이다. 패턴을 어긴 값은 읽는 단계에서 거부되어 런타임이 다시 검증하지 않는다
- [x] **에이전트가 아닌 종류가 `model`을 적으면 `requires_approval`처럼 거부한다**
- [x] **가리키는 모델 플러그인이 실재하는지는 여기서 보지 않는다.** 매니페스트만으로는 알 수 없어 04의 실행 준비가 본다
- [x] **계약에 실리는 모델의 독스트링은 한 줄이고 논증은 `#` 주석에 둔다**(`.claude/rules/sdk.md`, `.claude/rules/http.md`의 "계약에 박히는 것 둘")

### 계약 파일과 생성 타입

- [x] **`openapi.json`을 `uv run python tools/export_openapi.py`로 다시 뽑는다.** `PluginManifest`에 다섯 칸(`model`, `provider`, `model_id`, `max_tokens`, `temperature`)이 들고 직렬화 스키마에서 모두 `required`이며 `null`을 허락한다(`json_schema_serialization_defaults_required`, `conversation_limit`과 같다). `ModelProvider`가 컴포넌트로 선다. 최신성 시험이 이것을 판정한다. 컴포넌트 이름의 집합을 단언하는 시험이 있으면 `ModelProvider`를 더한다
- [x] **생성 타입을 다시 만든다.** 다섯 칸이 `… | null`의 필수로 든다. 같은 장치의 결과인 `conversation_limit: number | null`이 이미 있어(`web/packages/api-client/src/generated/openapi.ts`) 리터럴이 타입 검사에서 깨지는 것이 첫 빨강이다
- [x] **관리 화면의 매니페스트 리터럴에 다섯 칸을 적는다.** to-tickets 시점에 `conversation_limit: null`을 적은 파일은 여섯이다(`PluginDetail.stories.tsx`, `PluginList.stories.tsx`, `RunDetail.stories.tsx`, `HomePage.test.tsx`, `PluginPage.test.tsx`, `RunPage.decision.test.tsx`, 모두 `web/apps/admin/components/` 아래). 모델 종류의 리터럴은 `provider: "anthropic"`과 실제 같은 `model_id`를 적어 서버가 낼 수 있는 모양으로 두고, 다른 종류는 다섯 칸이 `null`이다. 매니페스트를 펼친 문자열 픽스처가 있으면 타입 검사가 아니라 vitest에서 빨개지니 함께 본다(conversation 01의 2026-10-04 명세 검토)
- [x] **모델 상세(`PluginDetail`)의 사진 정답이 바뀌면 다시 만든다.** 상세가 매니페스트 JSON을 높이 제한 없이 그려, 리터럴에 다섯 칸이 들면 정답 여덟 장(`web/apps/admin/visual/snapshots/organisms-plugindetail--{enabled,disabled}-{1280,320}-{light,dark}.png`)이 바뀔 것이다(명세 검토의 코드 읽기, 돌리지 않았다). `pnpm -C web visual:admin`으로 빨강을 보고 `pnpm -C web visual:admin:update`로 정답을 컨테이너 안에서 다시 만든 뒤 바뀐 사진을 PR 본문에 적는다(`.claude/rules/web-design.md`). 다른 사진이 바뀌면 그것도 적는다
- [x] **관리 API의 경로는 늘지 않는다.** 화면은 모델 상세를 지금처럼 매니페스트 JSON으로 그리고(스토리 12), 모델 전용 화면이나 편집은 범위 밖이다. 모델 행의 안내 줄("로더가 생기기 전에는 효과가 없다")은 이 티켓에서 걷지 않는다. 걷는 것은 켜고 끄기가 실제로 듣게 된 뒤인 06이다

### 픽스처와 관리 API

- [x] **공통 넷만 적은 모델 픽스처 둘을 받아들여지는 모델 매니페스트로 고친다.** `tests/test_server.py`의 `SONNET`(모듈을 import할 때 `parse_manifest`가 돌아, 고치지 않으면 sdk가 바뀌는 순간 파일 수집이 오류다)과 관리 화면 e2e 스택(`web/apps/admin/e2e/stack.ts`)의 `models/sonnet`이다. 지우지 않는다. 목록에 모델이 둘 있어야 04·06이 켜고 끄기와 에이전트가 고른 모델을 잰다(명세의 "저장소의 기본 모델 플러그인과 격리 루트")
- [x] **파일시스템 어댑터 시험의 종류별 픽스처(`tests/adapters/test_filesystem.py`의 `_KIND_EXTRA`)에서 모델 칸을 채운다.** 지금 빈 문자열이라 존재만 보는 시험은 초록이어도 읽히지 않는 모델 파일을 만든다
- [x] **`GET /plugins`가 모델 행을 새 칸과 함께 내고, 공통 넷만 적은 모델 파일은 그 행만 표지 행(`reason`에 거부 까닭)이며 단건 상세는 500이다**(스토리 9·12). 목록 전체가 500이 되지 않는다. 선례는 `tests/test_server.py`의 `_admin_app`과 `test_읽을_수_없는_매니페스트는_목록에서는_표지이고_단건으로는_500이다`다
- [x] **에이전트 행의 매니페스트에 `model`이 실린다.** 적지 않은 에이전트는 없음이다

### 문서

- [x] **`.claude/rules/sdk.md`의 두 문장을 고친다.** 종류별 칸을 적는 불릿(`agent`만 `entrypoint`·`mcp`, `mcp`만 `[server]`)에 모델의 네 칸과 에이전트의 `model`을 더하고, "첫 슬라이스는 `kind`와 디렉터리만 예약한다"를 칸의 모양으로 바꾼다. 틈 동안에도 참인 문장이어야 하므로 런타임이 읽는다는 말은 04가 쓴다
- [x] **옛 표현을 저장소 전체에서 grep해 살아 있는 문서에 잔존이 0인지 본다**(`CLAUDE.md` 작업 규약 4). 기록(일지, 대기열, ADR 이력)은 고치지 않는다

### 검증

- [x] **빨강을 먼저 본다**(헌법 원칙 II). 첫 빨강은 리터럴이 타입 검사에서 깨지는 것과 `openapi.json` 최신성 시험이다
- [x] **검증 명령이 모두 초록이다.** 손으로 치는 다섯에 더해 관리 화면 e2e(`pnpm -C web/apps/admin exec playwright test`. 스택의 `models/sonnet`을 고쳤다)와 사진 비교 `pnpm -C web visual:admin`을 친다. 위젯·`-m llm`은 이 티켓이 닿지 않는다
