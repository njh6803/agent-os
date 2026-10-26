# 01: 계약 — 최종 사용자 스트림에 "부르기 시작함" 항목이, 429에 상한의 종류가 들고, api-client가 위젯 클라이언트를 낸다

**What to build:** 최종 사용자 경로(시작, 이어 가기, 결정, 구독)의 스트림에서, 모델이 도구를 요청한 모델 호출이 `calling` 항목으로 나간다. 그 항목은 모델이 요청한 도구의 이름을 차례대로 든다. 최종 사용자 경로 넷이 429로 거절하면 봉투가 어느 상한에 걸렸는지를 `limit`(동시 실행 수, 시간당 실행 수, 구독 수)으로 말한다. `openapi.json`과 생성 타입이 그것을 싣고, api-client에 위젯이 쓸 클라이언트가 생긴다. 그 클라이언트는 최종 사용자 경로 넷만 알고, 스트림을 읽을 때 프레임의 `id`와 keepalive까지 낸다.

이 기능의 계약 티켓이고 02와 05를 막는다(명세 Further Notes의 티켓 차례). 리뷰의 질문은 "동작하나"가 아니라 이 이름과 모양으로 오래 살 수 있느냐다.

**병합 뒤에 틈이 있다.** core는 아직 모델·도구 호출의 이벤트를 에이전트가 다음 이벤트를 낼 때까지 모은다. 그래서 저장소의 계산 에이전트처럼 루프가 `ctx.llm()` 한 번인 실행에서는 `calling` 항목이 도구가 끝난 뒤, 결말 바로 앞에 나온다. 02가 실시간으로 흘리게 고친다. 이 티켓이 쓰는 문장(계약의 설명, 독스트링, rules)은 그 틈 동안에도 참이어야 하므로 `calling`의 시점을 말하지 않는다.

근거는 `.scratch/web-widget/spec.md`의 "계약 — 부르기 시작함 항목과 429의 상한 종류", "api-client — 위젯 클라이언트" 절과 Testing Decisions의 "서버의 계약"·2다. ADR 0023의 2026-10-23 이력과 ADR 0010 본문의 포인터가 앞선 결정이다.

**Blocked by:** None (can start immediately)

**Status:** done

### 계약 — `calling` 항목

- [x] **최종 사용자 항목에 `calling`(`CallingItem`)이 는다.** 필드는 `tools` 하나이고, `llm_called`의 `tool_calls` 차례대로 도구 이름을 담은 문자열 목록이며 최소 길이는 1이다. `tool_calls`가 빈 `llm_called`는 지금처럼 항목이 없다. 인자와 도구 호출 식별자는 싣지 않는다
- [x] **계약에 실리는 한 줄 설명은 시점을 말하지 않는다**(예: "모델이 요청한 도구의 이름"). 계약 모델의 독스트링은 한 줄이고 논증은 `#` 주석이다(`.claude/rules/http.md`)
- [x] **투영은 이벤트 하나를 항목 하나 또는 없음으로 옮기는 규칙을 지킨다.** 프레임의 `id`는 지금처럼 그 이벤트의 인덱스이고 `Last-Event-ID`의 뜻도 그대로다. `.claude/rules/channel.md`의 투영 항목("종류로만 가른다")에 `llm_called`의 조건과 `calling`을 더한다
- [x] **항목 유니온의 멤버가 여덟이 된다.** `tests/channel/http/test_end_user.py`의 `test_항목_유니온은_판별자_type_의_이름_있는_컴포넌트이고_멤버가_일곱이다`를 여덟으로 고친다

### 계약 — 429의 `LimitEnvelope`

- [x] **최종 사용자 경로 넷의 429만 별도 스키마 `LimitEnvelope`를 가리킨다.** 그 넷의 다른 상태 코드와 운영자·관리 경로의 모든 에러는 `ErrorEnvelope` 그대로다. `Retry-After` 헤더의 문서도 그대로다
- [x] **`LimitEnvelope`의 네 필드는 `ErrorEnvelope`와 글자 그대로 같고, 필수 필드 `limit`이 하나 는다.** `code`는 `ErrorCode`를 가리키고 값은 늘 `too_many_requests`다. `message`는 지금의 글 그대로다
- [x] **`limit`의 값 집합은 이름 있는 컴포넌트 `LimitKind`이고 값은 `concurrent_runs`, `hourly_runs`, `subscriptions`다.** 동시 실행의 세 범위(주체별, 사이트별, 전역)는 모두 `concurrent_runs`, 시간당의 두 범위는 `hourly_runs`, 구독은 `subscriptions`다. 범위는 싣지 않는다(명세 Out of Scope). 지금 서버의 상한 열거는 값이 봉투 문구에 드는 한국어 이름이라, 문구는 그대로 두고 `LimitKind`로의 대응을 이 티켓이 짓는다
- [x] **`.claude/rules/http.md`를 고친다.** 봉투 항목("네 필드가 전부 required다")에 429의 다섯째 필드를, 예외 표 항목("봉투의 문구는 어느 상한인지만 말하고")에 `limit`을 더한다
- [x] **봉투를 단언하는 시험 둘을 위 규칙으로 고친다.** `tests/test_server.py`의 `test_문서화된_에러_응답이_전부_봉투이고_내는_에러를_빠뜨리지_않는다`와 `tests/channel/http/test_end_user.py`의 `test_경로_넷이_지은_operation_id_와_봉투_에러_문서와_항목_유니온을_든다`다. 둘은 지금 모든 에러를 `ErrorEnvelope` 하나로 견준다

### 계약 — 문서와 시험

- [x] **운영자 채널(`/runs`)과 관리 API의 계약은 바뀌지 않는다**
- [x] **`openapi.json`을 다시 뽑는다.** 최신성 시험이 초록이다
- [x] **HTTP 사례**(`create_app()`과 `ASGITransport`, 선례는 그 파일의 "구독", "상한", "계약" 절). `tool_calls`가 든 `llm_called`가 `calling` 항목(도구 이름의 차례)이 되고 빈 것은 항목이 없으며, 프레임의 `id`가 그 이벤트의 인덱스다. 429 봉투의 `limit`이 상한마다 위 대응대로다
- [x] **`tests/test_main.py`의 LLM 시험 `test_실제_serve_에서_서명한_토큰으로_시작한_실행을_최종_사용자_경로로_이어_가면_앞_대화를_안다`의 독스트링**에서 "모델 호출은 항목이 없어"의 앞에 '도구를 요청하지 않은'을 붙인다. 그 시험의 에이전트는 도구가 없어 단언은 그대로다

### api-client — 위젯 클라이언트

- [x] **api-client를 다시 생성한다.** 관리 화면이 새 생성 타입으로 컴파일된다
- [x] **위젯 클라이언트를 더한다.** 기준 주소(`URL`)를 인자로 받고, 타입에 드는 경로는 최종 사용자 경로 넷뿐이다. 서명 토큰은 클라이언트가 들지 않고 부르는 쪽이 요청마다 `Authorization` 헤더로 넘긴다. 구독의 `Last-Event-ID`는 계약의 헤더 파라미터로 보낸다. 스트림은 `EventSource`가 아니라 fetch로 읽고 프레임 크기 상한은 두지 않는다(ADR 0024)
- [x] **최종 사용자 항목을 읽는 함수를 하나 더한다.** 프레임마다 `id`(십진 정수)와 항목을 내고, 항목은 `type`의 판별자 술어(`calling` 포함)로 좁힌다. 모르는 `type`이나 읽지 못한 프레임은 원문으로 낸다. `data` 없이 주석만 든 블록(서버의 keepalive)도 그것이 왔다는 값으로 낸다. 운영자 쪽 `readFrames`의 동작은 바뀌지 않는다
- [x] **단위 시험**(선례 `packages/api-client/src/stream.test.ts`). 프레임의 `id`를 읽고, 항목을 술어로 좁히며(`calling` 포함), 모르는 `type`이 원문이 되고, 주석만 든 블록이 keepalive 값이 되며(그 파일의 `streamOf`로 조각을 넣는다), 구독이 `Last-Event-ID` 헤더를 보낸다
- [x] **타입 시험**(선례 `clients.test-d.ts`). 위젯 클라이언트가 운영자 경로를 받지 않고, 429 응답의 `limit`이 늘 있는 `LimitKind` 값으로 좁혀진다

### 검증

- [x] `CLAUDE.md`의 검증 명령이 모두 초록이다. `channel/`을 건드리므로 `uv run --env-file .env pytest -m llm`도 돌리고 일지에 통과 수와 토큰 합계 줄을 적는다(`docs/constitution/operations.md` LLM 테스트)
