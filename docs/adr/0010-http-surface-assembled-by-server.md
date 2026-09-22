---
status: accepted
date: 2026-09-22
---

# HTTP 표면은 FastAPI로 서고 `server.py` 하나가 조립한다

관리 API가 슬라이스 2의 첫 HTTP 표면이고 곧 HTTP 채널이 같은 프로세스에 붙으므로, 앱을 조립하는 자리를 지금 정한다. **FastAPI와 uvicorn을 런타임 의존성으로 더하고, `server.py`가 `create_app(*, plugins, trace, token, ...)` 하나만 내보낸다. 전역 `app` 객체를 두지 않는다.** FastAPI를 고른 이유는 `openapi.json`이 이 저장소에서 계약이기 때문이다 — 슬라이스 3의 `packages/api-client`가 그 파일에서 생성되고, `sdk`의 디스크 형식이 이미 pydantic이라 이름 있는 `$defs`가 공짜로 나온다(ADR 0008이 `StrEnum`을 고른 이유가 그것이다). 전역 `app`을 두지 않는 이유는 어댑터 주입이다. 어댑터를 만들어 넘기는 자리는 `main.py`와 `server.py`뿐이고(원칙 IV의 의존 방향), 어댑터는 자기를 스스로 조립하지 않는다(`.claude/rules/adapters.md`). 모듈 수준에서 앱을 만들면 import 시점에 `plugins/` 경로와 트레이스 디렉터리가 고정되어, 테스트가 가짜 포트 대신 진짜 파일시스템을 쓰게 된다.

## Considered Options

- **Starlette만 쓴다.** 의존성이 가볍고 FastAPI의 마법이 없다. 그러나 OpenAPI 문서를 손으로 조립해야 하고, 그 문서가 계약이라 손으로 쓴 스키마와 실제 응답이 어긋날 자리가 생긴다. 생성 클라이언트가 기대는 이름 있는 `$defs`도 직접 만들어야 한다. 거부했다.
- **모듈 수준 전역 `app`을 둔다.** `uvicorn agent_os.server:app`으로 바로 뜨고 배포가 단순하다. 그러나 어댑터를 넘길 자리가 없어져 조립 층이 둘로 갈리고, import 시점에 경로가 고정된다. 거부했다.
- **성공 응답도 봉투로 감싼다.** 모든 응답에 추적 식별자가 본문에 실린다. 그러나 생성 클라이언트가 매번 `.data`를 벗겨야 하고 OpenAPI 스키마가 두 겹이 된다. 프론트 규칙이 이미 "공용 apiClient만 쓰고 data만 반환"이라 벗기기를 클라이언트 쪽에 두라고 말한다(일지 2026-09-19의 프론트 규칙 분석). 거부했다.
- **설정 파일(`agent-os.toml`)로 서버 설정을 모은다.** 값이 늘어도 명령줄이 길어지지 않는다. 그러나 새 디스크 형식이라 `schema_version`과 ADR이 또 필요하고, 지금 값이 넷뿐이다. 거부했다.

## Consequences

- **`tech.md` 스택 표에 웹 프레임워크 행이 는다.** 런타임 의존성이 넷에서 여섯이 된다(`fastapi`, `uvicorn`). 의존성 추가는 ADR을 남긴다는 규약을 이 문서가 만족한다.
- **import-linter 계약의 `(agent_os.server)` 층이 실물이 된다.** 지금은 선택 층으로 선언만 돼 있고 파일이 없다. `server.py`가 생기는 순간 `main → server → {channel | admin | adapters} → core → sdk`가 실제로 판정된다. 채널과 관리는 서로를 import하지 않고 `server.py`가 라우터 둘을 마운트한다. 이번에는 관리 라우터만 있고 `http-channel`이 `/runs`를 더한다.
- **에러만 봉투로 감싼다.** `{code, message, violations, request_id}`. 성공 응답은 생값이고 추적 식별자는 `X-Request-Id` 헤더로 나간다. 예외를 HTTP 상태 코드로 옮기는 표는 `admin/http` 한 곳에 둔다 — 부재(포트가 `None`을 돌려준 것)는 404, `PluginError`(매니페스트 파싱 실패)는 422. `core`의 예외는 상태 코드를 모른다.
- **`main.py`에 `agent-os serve`가 는다.** `--host`(기본 `127.0.0.1`) `--port` `--traces` `--plugins-root`. 비밀만 환경변수이고, 루프백이 아닌 주소는 받지 않는다. 둘 다 ADR 0011. `--plugins-root`가 생기면서 지금 `main.py`에 `PLUGINS_ROOT = Path("plugins")`로 하드코딩된 것이 `run`·`resume`에서도 풀린다.
- **`openapi.json`이 저장소 루트에 커밋된다.** 생성기는 `tools/export_openapi.py`, 최신성은 pytest 하나가 `create_app().openapi()`와 파일을 비교한다. 검사 명령 넷이 그대로 게이트이므로 새 훅을 만들지 않는다. 계약 파일이 하나 더 생기는 것이라 이후 `sdk`와 같은 무게로 다룬다.
