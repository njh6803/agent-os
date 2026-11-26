---
paths:
  - "widget-admin/**"
  - "tests/widget_admin/**"
  - "tools/export_widget_admin_openapi.py"
---

# 위젯 관리 서버 규칙

원천은 `widget-admin/`의 코드와 `tests/widget_admin/`, 결정은 ADR 0064(구조)와 ADR 0066(데이터베이스)이다. 코드와 이 문서가 다르면 코드를 고치거나 ADR을 남긴다.

- **둘째 설치 묶음이고 `agent_os`와 서로 import하지 않는다.** 패키지는 `widget_admin`이고 루트 `pyproject.toml`의 작업공간 멤버다. 곧바른 import도 다른 모듈을 거친 import도 import-linter의 `independence` 계약이 막는다. 그래서 Agent OS와 같은 뜻의 것(오류 봉투 `{code, message, violations, request_id}`, `X-Request-Id`, 접두사 비교 `is_under`)은 import하지 않고 사본으로 둔다. `code` 어휘는 같은 상태 코드에 같은 글자를 쓴다(`invalid_request`, `not_found`, `internal_error`).
- **앱을 짓는 곳은 `create_app(*, database, stderr)` 하나이고 전역 `app`이 없다.** 데이터베이스 객체(`WidgetAdminDatabase`)는 기본값 없는 인자다. 미들웨어는 바깥에서 안쪽으로 시작 점검(`CheckDatabase`), 추적 식별자, 응답 머리, 핸들러가 놓친 예외의 변환, 라우터다.
- **읽는 경로 `GET /widget-settings/{site}`는 토큰이 없다.** 등록되지 않은 이름과 꼴이 틀린 이름은 글자까지 같은 404이고, 꼴(`^[a-z][a-z0-9-]{1,62}$`)은 `re.fullmatch`로 이름 전체에 건다. 경로 인자의 `pattern`을 쓰지 않는다(맞지 않는 이름에 422가 나 404와 갈린다). 꼴이 틀린 이름은 데이터베이스에 묻지 않는다. 질의는 칸을 이름으로 골라 읽고 `SELECT *`를 쓰지 않는다.
- **다른 출처에 여는 머리 셋은 `/widget-settings` 접두사 아래의 모든 응답에만 붙는다.** 에러 응답에도 붙고 `/health`와 접두사 밖에는 붙지 않는다. 허용 메서드와 자격 증명 머리는 싣지 않는다.
- **실패 하나는 표준 오류에 한 줄이다.** 사이트 이름과 경로와 접속 주소의 조각을 싣지 않고, 예기치 않은 예외는 원인 사슬의 클래스 이름만 싣는다.
- **표의 규칙은 표가 든다.** 마이그레이션(`migrations/versions/`)은 앞으로만 가고 `downgrade`가 없으며, 이름의 식은 글자 그대로 적고 상수를 끌어 쓰지 않는다. 이미 올라간 파일은 고치지 않고 새 파일을 더한다.
- **계약 파일 `widget-admin/openapi.json`은 손으로 고치지 않는다.** `PYTHONUTF8=1 uv run python tools/export_widget_admin_openapi.py`로 뽑고 최신성은 `tests/widget_admin/test_contract.py`가 판정한다. 모델의 독스트링은 한 줄이다(`http.md`의 같은 항목).
- **시작 점검은 가장 바깥 미들웨어이고 수명 메시지만 만진다.** `CheckDatabase`(`lifespan.py`)는 앱의 시작 단계보다 먼저 닿는지와 표의 판을 보고, 문제면 `lifespan.startup.failed`에 글을 싣는다(uvicorn이 3으로 끝난다). 요청은 그대로 지나보낸다. 그래서 다른 미들웨어 뒤로 옮기지 않고, `uvicorn.run`에는 `lifespan="on"`을 준다(`auto`는 앱이 수명을 모른다고 보면 경고만 찍고 뜬다).
- **멈출 때의 글은 postgres-foundation(Agent OS)과 같고 셋만 다르다.** 변수가 없거나 비었을 때, 주소를 읽지 못했을 때, 표가 뒤처졌을 때의 글이다(`WIDGET_ADMIN_DATABASE_URL`과 `widget-admin migrate`를 말한다). 나머지는 같은 글이고 글에 ADR 번호를 싣지 않는다. 글을 짓는 함수와 상수(`retry_notice`, `unreached_text`, `misaligned_text`, `DEFAULT_RETRY_SECONDS`)는 자리표시자로 부를 수 있게 공개로 둔다(배포 안내의 시험이 안내의 표와 견주도록 04가 이 이름을 읽는다. 지금은 `tests/widget_admin/test_database_check.py`만 부른다). 루프백 규칙의 진단도 `serve`의 것에서 까닭의 줄 하나만 다르다.
- **연결 문자열은 `postgresql://계정:비밀번호@호스트:포트/데이터베이스` 꼴 하나만 받는다.** 드라이버 이름이 붙은 꼴, `?` 뒤의 질의(`sslmode` 등), `@`가 둘 이상인 값은 읽지 못한 것이고 글에 값을 싣지 않는다. 닿는 확인은 시도 전체에 5초를 건다.
- **시험은 진짜 테스트 데이터베이스를 쓴다.** `tests/widget_admin/conftest.py`가 접두 `widget_admin`의 데이터베이스를 받고, 표에는 SQL로 직접 줄을 넣는다(`support.insert_site`). 데이터베이스를 가짜로 바꾸지 않는다. 시험이 연 `WidgetAdminDatabase`는 픽스처가 닫는다. 수명(시작 점검과 닫기)은 `tests/fake_database.py`의 `LifespanDriver`로만 보고, 라우트는 `ASGITransport`로 부른다. 둘을 섞지 않는다.
