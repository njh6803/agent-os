---
paths:
  - "src/agent_os/admin/**"
  - "tests/test_server.py"
---

# 관리 API 규칙

관리에만 걸리는 것이다. 봉투와 어휘, 상태 코드 표, 에러 문서, `verbatim`, `operation_id`, 인증, 테스트 이음매처럼 채널과 함께 따르는 것은 `http.md`에 있다. 원천은 ADR 0010·0011·0012와 `.scratch/admin-api/spec.md`다. 아래는 확정된 결정이고, 코드와 다르면 코드를 고치거나 ADR을 남긴다.

- **관리는 실행을 일으키지 않고, 관리 라우터는 도구 포트를 받지 않는다.** 조회 하나가 MCP 서버 여럿을 띄우는 길을 시그니처가 먼저 닫는다. `create_app`도 도구 포트를 받지 않는다. 관리 라우트는 409를 내지 않는다 — 재개할 수 없는 상태를 만날 일이 없다.
- **관리 쪽 부재는 포트가 돌려준 `None`을 라우트가 `HTTPException(404)`로 말한다.** 읽을 수 없는 파일은 포트의 `PluginError`가 표를 지나 500이다.
- **`/health`는 `create_app`이 주입한 값을 돌려줄 뿐 상태를 직접 읽지 않는다.** 인증 없이 경계 밖으로 나가는 유일한 응답이라 내부 구성을 싣지 않는다.
- 매니페스트 응답의 모양은 ADR 0010의 2026-09-23 이력이 원천이다.
- **실행 목록은 한 쪽이 본문 객체 `TracePage {runs, next_cursor}`이고 커서는 불투명하다.** 정렬 키를 JSON으로 적어 base64url로 감싼 것이고 계약은 문자 집합과 길이(`CURSOR_PATTERN`)만 약속한다. `after`는 문자 집합을 FastAPI가, 해독을 라우트가 포트 전에 보고 둘 다 `query.after`를 가리키는 422다. `next_cursor`는 받은 행이 `limit` 개일 때만 준다. 행 모델 둘은 core의 요약과 표지를 옮긴 것이고 대조 테스트가 필드를 맞춘다. 이유는 `admin/traces.py`.
- **트레이스 상세는 본문 객체 `Trace {run_id, schema_version, events}`이고 이벤트는 `sdk`의 모델 그대로다.** 모르는 종류는 판별자 `unknown`과 원문 문자열 `raw`를 든 표지(`UnknownEvent`)로 같은 판별 유니온(`TraceEvent`)에 들어간다. 원문을 펼쳐 판별자를 얹지 않는다. 유니온은 `sdk`의 `Event`에 표지를 더한 것이라 종류를 여기서 다시 나열하지 않는다. 이벤트를 마스킹 없이 내보내는 전제는 `secret_args` 0건 불변식이 지킨다(ADR 0009의 2026-09-22 이력). 저장소를 재는 테스트라 이 이음매가 아니라 `tests/sdk/test_manifest.py`에 있다. 원천은 ADR 0010의 2026-09-22·2026-09-24 이력.
