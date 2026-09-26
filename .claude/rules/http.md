---
paths:
  - "src/agent_os/http/**"
  - "src/agent_os/admin/**"
  - "src/agent_os/channel/http/**"
  - "src/agent_os/server.py"
  - "tools/export_openapi.py"
  - "openapi.json"
  - "tests/test_server.py"
  - "tests/channel/http/**"
  - "tests/tools/test_export_openapi.py"
---

# HTTP 표면 규칙

관리와 채널이 함께 따르는 것이다. 원천은 ADR 0010(조립과 에러 봉투)·0011(fail-closed 인증)·0014(채널의 스트림과 실행 전 실패)·0015(채널 토큰)·0016(공용 층)이다. 관리에만 걸리는 것은 `admin.md`에, 채널에만 걸리는 것은 `channel.md`에 있다. 아래는 확정된 결정이고, 코드와 다르면 코드를 고치거나 ADR을 남긴다.

- **공용 배관은 `agent_os.http` 한 곳이고 사본을 두지 않는다.** 같은 스키마가 둘이면 컴포넌트 이름이 부딪히거나 언젠가 어긋난다. 이 층은 core와 sdk만 import하고, 채널과 관리와 `server`가 이것을 import한다. 어댑터는 이것을 import하지 않는다 — HTTP 표면이 아니다(원칙 IV, ADR 0016). 모듈은 쓰는 쪽으로 갈린다. `errors`(봉투, 표, 핸들러, 추적 식별자)와 `auth`는 `server`가 앱에 걸고, `routes`(에러 문서, `verbatim`)는 라우트를 선언하는 쪽이 쓴다.
- **이 층의 이름은 표준 라이브러리 `http`와 같다.** `src/agent_os/` 안의 파일을 스크립트로 실행하면 그 디렉터리가 `sys.path` 첫머리에 서서 이 패키지가 표준 라이브러리 자리에 들어온다. `http/__init__.py`가 그것을 알아채 처방을 담은 `ImportError`로 막는다. 실행은 `agent-os`나 `python -m agent_os.main`이다(ADR 0016의 2026-09-25 이력).
- **앱을 만드는 자리는 `create_app()` 하나이고 모듈 수준 전역 `app`이 없다.** 전역 앱은 import 시점에 경로를 고정해 테스트가 가짜 포트 대신 진짜 파일시스템을 쓰게 만든다. 어댑터를 만들어 넘기는 자리는 `main.py`와 `server.py`뿐이고 어댑터도 라우터도 자기를 스스로 조립하지 않는다.
- **보호는 미들웨어가 기본으로 걸고 라우트가 opt-in 하지 않는다.** 라우트에 `Depends(토큰 검사)`를 달지 않는다. 그렇게 하면 라우트를 더하며 잊은 것이 곧 공개가 되고, 잊었다는 사실을 아는 길이 전수 검사 테스트 하나뿐이 된다. 미들웨어가 라우팅보다 바깥이라 문서에 없는 경로도 401이다.
- **토큰은 둘이고 미들웨어가 받는 접두사→토큰 표가 가른다.** `/runs` 아래는 채널 토큰(`AGENT_OS_CHANNEL_TOKEN`)만, 그 밖은 관리 토큰(`AGENT_OS_ADMIN_TOKEN`)만 연다. 표는 `server`가 넘기고, 표에 없는 경로의 기본값이 관리 토큰이라 채널 경로를 접두사 밖에 두는 실수는 틀린 토큰으로 막힐 뿐 열리지 않는다. 접두사는 경로 조각 단위로 본다(`/runsx`는 채널이 아니다). 두 토큰의 비교는 상수 시간 비교 한 곳을 지난다. `create_app`은 빈 토큰과 같은 두 토큰을 거부하고, 진단으로 말하는 것은 `serve`다(ADR 0015, ADR 0011의 2026-09-24 이력).
- **인증 없이 지나가는 경로는 `PUBLIC_PATHS`이고 원소는 `/health` 하나다.** 자라면 ADR 0011의 이력에 쌓는다. 테스트와 문서 둘 다가 조건이고, 목록이 문서 없이 자라는 것이 fail-open으로 돌아가는 길이다.
- **성공 응답은 봉투로 감싸지 않는다.** 생값이고 추적 식별자는 `X-Request-Id` 헤더로 나간다. 에러만 `{code, message, violations, request_id}` 봉투이고 네 필드가 전부 required다. `code` 어휘는 다섯(`unauthorized` 401, `invalid_request` 422, `not_found` 404, `conflict` 409, `internal_error` 500)이고 표의 상태 코드와 1:1이며, 늘리는 것은 계약 변경이다. **표 밖의 상태 코드는 계열로 접는다** — 프레임워크가 내는 405 같은 것이 그때마다 어휘를 늘리면 생성 클라이언트가 아는 값의 집합이 조용히 자란다. 테스트가 그 접기를 고정한다. `violations`의 `field`는 `query.limit`처럼 점으로 이은 경로 문자열 하나다. 판별 유니온 멤버 안의 필드는 판별자 값이 경로에 든다(`body.deny.reason`) — pydantic이 오류 위치에 태그를 넣고, 판별자가 없거나 모르는 값이면 `body` 하나다.
- **예외를 상태 코드로 옮기는 표는 `http/errors.py`의 `failure_for()` 한 곳이다.** 상태 코드와 문구와 형식 오류가 한 항목이라 예외 하나를 더할 때 고치는 자리도 하나다. 라우트는 상태 코드를 스스로 정하지 않는다. 포트가 `None`을 돌려준 부재는 라우트가 `HTTPException(404)`로 말한다. core의 실행 전 실패는 타입으로 갈려 오고 표가 MRO로 옮긴다 — `Absent` 404, `NotResumable` 409, 그 밖의 `PluginError` 500(ADR 0014, ADR 0010의 2026-09-24 이력). 하위 타입의 갈래가 기반 타입보다 먼저여야 하고, 뒤집히면 둘 다 500이 되는 것을 테스트가 잡는다. `PluginError`가 500인 이유는 요청을 고쳐서 풀리는 것이 앞의 둘로 갈려 남는 것이 "서버의 구성이나 기록이 깨졌다"뿐이기 때문이다. `core`의 예외는 상태 코드를 모른다.
- **에러 하나가 서버 표준 에러에 그 추적 식별자로 한 줄 남는다.** 봉투를 만드는 것(`error_envelope`, 질의)과 기록하는 것(`AssignRequestId`, 명령)을 가르고, 부르는 쪽은 `remember_failure()`로 남길 문구를 적어 둘 뿐이다. 경로도 주체도 적지 않는다 — 감사 로그는 비목표이고 이 한 줄은 실패 하나의 상관 키다. 요청이 들고 온 토큰은 응답에도 기록에도 싣지 않는다(원칙 V). 예기치 않은 실패의 원인은 기록에만 가고 밖으로는 고정 문구가 나간다.
- **계약 파일은 루트 `openapi.json`이고 손으로 고치지 않는다.** `PYTHONUTF8=1 uv run python tools/export_openapi.py`로 뽑고, 최신성은 pytest 하나가 판정한다. 라우트나 모델을 건드린 커밋은 이 파일을 함께 담는다. 슬라이스 3의 `packages/api-client`가 여기서 생성되므로 `sdk`와 같은 무게다.
- **계약에 박히는 것 둘을 손으로 준다.** pydantic이 클래스 독스트링을 스키마의 `description`으로 그대로 싣고 FastAPI가 라우트 함수 이름으로 `operationId`를 짓는다. 그래서 **계약에 실리는 모델의 독스트링은 한 줄로 쓰고 논증은 `#` 주석에 두며**(그러지 않으면 주석을 다듬는 것이 계약 변경으로 보인다), **라우트에는 `operation_id`를 적는다**(기본값 `read_health_health_get` 꼴이 그대로 생성 클라이언트의 함수 이름이 된다).
- **라우트는 자기가 내는 에러를 `responses=documented_errors(...)`로 적는다.** 401은 미들웨어가 내는 것이라 프레임워크가 스키마에 넣어 주지 않고, 422는 적지 않으면 FastAPI가 제 모양(`HTTPValidationError`)을 붙여 계약이 봉투가 아닌 것을 약속한다. 500은 라우터가 모든 라우트에 건다. `/health`에 401이 없는 것은 allowlist라 실제로 내지 않기 때문이고, 그 밖의 모든 라우트는 낸다. **스트림 라우트(`EventSourceResponse`)는 라우터 단위의 것까지 `documented_stream_errors(...)`로 적는다.** FastAPI는 에러 문서의 모델을 라우트 응답 클래스의 미디어 타입 아래에 싣는데, 스트림 라우트에서 그것은 `text/event-stream`이라 계약이 "봉투가 스트림으로 온다"고 말하게 된다. 에러는 스트림이 시작되기 전에 JSON 봉투로 나간다. 모든 에러 응답의 미디어 타입이 JSON 하나라는 것은 테스트가 잰다.
- **스트림의 프레임은 `data:` 한 줄이고 `event:`·`id:`를 싣지 않는다.** 종류는 JSON의 `type` 한 곳에 있다(ADR 0014). 그런데 계약의 스트림 항목 스키마(`itemSchema`)는 FastAPI의 정형이라 `event`·`id`·`retry`를 선택 필드로 광고한다. 끄는 인자가 없고, 생성된 스키마를 후처리하면 FastAPI를 올릴 때마다 어긋날 자리가 되므로 광고를 그대로 둔다(ADR 0014의 2026-09-24 이력). **계약만 보고 서버가 `event:`를 보내도록 "고치지" 않는다.** 광고와 전송이 맞아지는 것은 재접속을 만들어 `id`가 실제로 실리는 날이다. 서버가 `data`만 보낸다는 것은 테스트가 고정한다.
- **파일 경로로 조립되는 경로 파라미터는 `verbatim` 변환기와 `sdk`의 패턴으로 받는다**(`{name:verbatim}`에 `Path(pattern=PLUGIN_NAME_PATTERN)`, `{run_id:verbatim}`에 `Path(pattern=RUN_ID_PATTERN)`). 기본 변환기와 `path` 변환기는 슬래시나 개행이 든 값을 검증까지 데려오지 못해 422 대신 라우팅 404가 되거나 개행이 떼어진 채 읽힌다. 이유는 `http/routes.py`의 `_Verbatim`. 테스트는 퍼센트 인코딩으로 민다 — httpx가 맨 `..` 조각을 보내기 전에 지워 요청이 다른 경로로 간다. 포트의 호출 횟수가 0인지와 `violations`의 필드가 그 파라미터인지를 같이 단언한다.
- **테스트는 `create_app()`에 가짜 포트를 주입하고 httpx `AsyncClient` + `ASGITransport`로 민다.** 가짜는 포트 Protocol을 상속하지 않고 시그니처로 만족하며 픽스처가 포트 타입으로 annotate한다. 네트워크도 디스크도 타지 않는다. uvicorn이 실제로 포트를 여는 것은 이 스위트가 증명하지 않는다 — 가짜로 증명할 수 없는 주장이 조립 세 줄과 서드파티의 동작뿐이기 때문이다. **예외는 하나다.** 같은 앱을 `app(scope, receive, send)`로 직접 부르는 구동자는 스트림의 수명 넷(조각별 전달, 끊겨도 실행은 끝까지, 느린 수신자, 서버가 멈추면 결말 없음)에만 쓴다. `ASGITransport`는 응답을 끝까지 모은 뒤에야 `http.disconnect`를 보내고 lifespan을 돌리지 않아 그것들을 잴 수 없다. 일반 요청으로 번지면 ADR 0010의 2026-09-22 이력이 클라이언트를 손으로 짜는 안을 거부한 논증이 그대로 걸린다 — 그 코드는 자기가 테스트되지 않는다.
