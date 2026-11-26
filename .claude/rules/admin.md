---
paths:
  - "src/agent_os/admin/**"
  - "tests/test_server.py"
---

# 관리 API 규칙

관리에만 걸리는 것이다. 봉투와 어휘, 상태 코드 표, 에러 문서, `verbatim`, `operation_id`, 인증, 테스트 이음매처럼 채널과 함께 따르는 것은 `http.md`에 있다. 원천은 ADR 0010·0011·0012와 `.scratch/admin-api/spec.md`다. 아래는 확정된 결정이고, 코드와 다르면 코드를 고치거나 ADR을 남긴다.

- **관리는 실행을 일으키지 않고, 관리 라우터는 도구 연결을 여는 길(`ToolSource.connect`)을 받지 않고 접속 확인만 받는다.** 모델 포트도 받지 않는다. 조회 하나가 MCP 서버 여럿을 띄우는 길을 시그니처가 먼저 닫는다. `create_app`은 채널을 위해 두 포트를 받지만 관리 라우터에 넘기지 않고, 포트에서 접속 확인 메서드만 꺼내 담은 묶음 둘(`AutomaticChecks`·`LaunchingChecks`, `admin/connection_check.py`)을 넘긴다. 그래서 라우터에서 `connect`를 부를 길이 없다(ADR 0010의 2026-09-24 이력, ADR 0067). 관리 라우트는 409도 429도 내지 않는다 — 재개할 수 없는 상태를 만날 일이 없고, 켜고 끄는 라우트는 꺼진 것을 거부하지 않으며, 429 는 요청하는 쪽의 상한이라 원격에 열린 최종 사용자 면의 라우트만 계약에 적는다(ADR 0023).
- **관리 쪽 부재는 포트가 돌려준 `None`이나 값(`absent`)을 라우트가 `HTTPException(404)`로 말한다.** 읽을 수 없는 파일은 포트의 `PluginError`가 표를 지나 500이다. 단건 조회와 켜고 끄기의 판정 순서는 부재(404) → 깨진 매니페스트(500) → 운영자 파일의 손상(500)이라, 운영자 파일이 깨졌어도 없는 이름은 404다(ADR 0017의 2026-09-27 둘째 이력). 목록은 이름을 대지 않으므로 운영자 파일이 깨지면 전체가 500이다.
- **`/health`는 `create_app`이 주입한 값을 돌려줄 뿐 상태를 직접 읽지 않는다.** 인증 없이 경계 밖으로 나가는 유일한 응답이라 내부 구성을 싣지 않는다.
- **관리의 첫 쓰기 경로는 `PUT /plugins/{kind}/{name}/enabled`이고 그 라우트는 `async def`다.** 포트의 쓰기를 이벤트 루프에서 직접 부른다. 조회 라우트처럼 동기 `def`면 FastAPI가 워커 스레드에서 돌려 읽고 고치고 쓰기 둘이 겹쳐 갱신 하나가 사라진다 — "한 프로세스 안의 쓰기 둘은 이벤트 루프가 줄세운다"(ADR 0017)는 쓰기가 루프 위에 있을 때만 참이다. 동시 PUT 테스트의 가짜 포트가 디스크 시간을 들이는 이유는 채널의 `disk_seconds`와 같다 — 즉시 끝나면 동기 라우트도 스레드 타이밍에 따라 초록으로 지나간다. 본문 `{enabled}`는 엄격한 불린(`StrictBool`)이다 — pydantic의 `bool`은 본문에서 `"false"`·`0`·`"no"`를 거짓으로 받아 계약에 없는 값이 켜짐을 정하게 된다. 계약의 스키마는 그대로 `boolean`이다. 꺼진 집합은 요청 하나에 한 번 읽는다.
- **접속 확인은 `/plugins/{kind}/{name}/connection-check`의 오퍼레이션 둘이고 둘 다 `async def`다(ADR 0067).** `GET`(`check_connection`)은 켜 둔 원격 MCP 서버와 모델에 자동으로, `POST`(`check_connection_by_launching`)는 켜 둔 stdio MCP 서버를 한 번 띄워 눌러서 확인한다. 종류 `kind`는 닫힌 열거 `CheckableKind`(`mcp`·`model`)라 에이전트와 스킬은 422다. 판정 순서는 형식 오류(422) → 없는 플러그인(404) → 깨진 매니페스트나 깨진 운영자 파일(500) → 꺼짐 → 대상 아님 → 붙어 보기이고, 앞에서 정해지면 확인 함수를 부르지 않는다. 응답은 `status`로 가르는 판별 유니온 `ConnectionCheck`(`reached`·`unreached`·`disabled`·`not_applicable`)이고 `reason`은 `unreached`에만 있으며 비지 않는다. **붙지 못한 것은 에러가 아니라 200이다.** 오류 봉투도 서버 기록 한 줄도 없고, 확인 함수가 던진 예외만 다른 라우트처럼 500이다. 200 응답은 `Cache-Control: no-store`를 싣고 오류 응답은 싣지 않는다. 확인 함수가 지켜야 할 약속(기한, 취소, 구성 오류)은 `core/ports.py`의 독스트링이 원천이다.
- 플러그인 응답(감싼 행 둘 `Plugin`·`PluginPlaceholder`와 유니온 `PluginRow`, 본문 `SetEnabled`)의 모양은 ADR 0010의 2026-09-26 이력이 원천이고 2026-09-23 이력을 그것이 개정했다. 표지 행은 core의 표지에 켜짐을 더한 것이고 대조 테스트가 필드를 맞춘다.
- **실행 목록은 한 쪽이 본문 객체 `TracePage {runs, next_cursor}`이고 커서는 불투명하다.** 정렬 키를 JSON으로 적어 base64url로 감싼 것이고 계약은 문자 집합과 길이(`CURSOR_PATTERN`)만 약속한다. `after`는 문자 집합을 FastAPI가, 해독을 라우트가 포트 전에 보고 둘 다 `query.after`를 가리키는 422다. `next_cursor`는 받은 행이 `limit` 개일 때만 준다. 행 모델 둘은 core의 요약과 표지를 옮긴 것이고 대조 테스트가 필드를 맞춘다. 이유는 `admin/traces.py`.
- **대화 목록은 `GET /conversations`(`list_conversations`)이고 모양과 질의가 실행 목록과 같다.** 쪽은 `ConversationPage {conversations, next_cursor}`이고 행은 대화 줄(`Conversation`)이거나 읽히지 않는 트레이스의 표지(`UnreadableTrace`, 맨 뒤)다. 커서는 끝 실행의 (시작 시각, 식별자)라 실행 목록의 커서 인코딩과 같고, `status`는 끝 실행의 상태로 거른다. 묶는 규칙은 `core/conversations.py`가 소유하고 라우트는 묶지 않는다(`core.md`). 이유는 `admin/conversations.py`.
- **트레이스 상세는 본문 객체 `Trace {run_id, schema_version, events}`이고 이벤트는 `sdk`의 모델 그대로다.** 모르는 종류는 판별자 `unknown`과 원문 문자열 `raw`를 든 표지(`UnknownEvent`)로 같은 판별 유니온(`TraceEvent`)에 들어간다. 원문을 펼쳐 판별자를 얹지 않는다. 유니온은 `sdk`의 `Event`에 표지를 더한 것이라 종류를 여기서 다시 나열하지 않는다. 이벤트를 마스킹 없이 내보내는 전제는 `secret_args` 0건 불변식이 지킨다(ADR 0009의 2026-09-22 이력). 저장소를 재는 테스트라 이 이음매가 아니라 `tests/sdk/test_manifest.py`에 있다. 원천은 ADR 0010의 2026-09-22·2026-09-24 이력.
