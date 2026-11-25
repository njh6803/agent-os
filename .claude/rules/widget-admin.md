---
paths:
  - "widget-admin/**"
  - "tests/widget_admin/**"
  - "tools/export_widget_admin_openapi.py"
---

# 위젯 관리 서버 규칙

원천은 `widget-admin/`의 코드와 `tests/widget_admin/`, 결정은 ADR 0064(구조)와 ADR 0066(데이터베이스)이다. 코드와 이 문서가 다르면 코드를 고치거나 ADR을 남긴다.

- **둘째 설치 묶음이고 `agent_os`와 서로 import하지 않는다.** 패키지는 `widget_admin`이고 루트 `pyproject.toml`의 작업공간 멤버다. 곧바른 import도 다른 모듈을 거친 import도 import-linter의 `independence` 계약이 막는다. 그래서 Agent OS와 같은 뜻의 것(오류 봉투 `{code, message, violations, request_id}`, `X-Request-Id`, 접두사 비교 `is_under`)은 import하지 않고 사본으로 둔다. `code` 어휘는 같은 상태 코드에 같은 글자를 쓴다(`invalid_request`, `not_found`, `internal_error`).
- **앱을 짓는 곳은 `create_app(*, database, stderr)` 하나이고 전역 `app`이 없다.** 데이터베이스 객체(`WidgetAdminDatabase`)는 기본값 없는 인자다. 미들웨어는 바깥에서 안쪽으로 추적 식별자, 응답 머리, 핸들러가 놓친 예외의 변환, 라우터다.
- **읽는 경로 `GET /widget-settings/{site}`는 토큰이 없다.** 등록되지 않은 이름과 꼴이 틀린 이름은 글자까지 같은 404이고, 꼴(`^[a-z][a-z0-9-]{1,62}$`)은 `re.fullmatch`로 이름 전체에 건다. 경로 인자의 `pattern`을 쓰지 않는다(맞지 않는 이름에 422가 나 404와 갈린다). 꼴이 틀린 이름은 데이터베이스에 묻지 않는다. 질의는 칸을 이름으로 골라 읽고 `SELECT *`를 쓰지 않는다.
- **다른 출처에 여는 머리 셋은 `/widget-settings` 접두사 아래의 모든 응답에만 붙는다.** 에러 응답에도 붙고 `/health`와 접두사 밖에는 붙지 않는다. 허용 메서드와 자격 증명 머리는 싣지 않는다.
- **실패 하나는 표준 오류에 한 줄이다.** 사이트 이름과 경로와 접속 주소의 조각을 싣지 않고, 예기치 않은 예외는 원인 사슬의 클래스 이름만 싣는다.
- **표의 규칙은 표가 든다.** 마이그레이션(`migrations/versions/`)은 앞으로만 가고 `downgrade`가 없으며, 이름의 식은 글자 그대로 적고 상수를 끌어 쓰지 않는다. 이미 올라간 파일은 고치지 않고 새 파일을 더한다.
- **계약 파일 `widget-admin/openapi.json`은 손으로 고치지 않는다.** `PYTHONUTF8=1 uv run python tools/export_widget_admin_openapi.py`로 뽑고 최신성은 `tests/widget_admin/test_contract.py`가 판정한다. 모델의 독스트링은 한 줄이다(`http.md`의 같은 항목).
- **시험은 진짜 테스트 데이터베이스를 쓴다.** `tests/widget_admin/conftest.py`가 접두 `widget_admin`의 데이터베이스를 받고, 표에는 SQL로 직접 줄을 넣는다(`support.insert_site`). 데이터베이스를 가짜로 바꾸지 않는다. 시험이 연 `WidgetAdminDatabase`는 픽스처가 닫는다.
