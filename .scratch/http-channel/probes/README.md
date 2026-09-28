# http-channel 프로브

명세·ADR·코드 주석이 근거로 든 측정 스크립트다. 규약은 `docs/agents/issue-tracker.md`. 2026-09-28에
세션 스크래치패드에서 옮겼고(대기열 29), 바꾼 것은 ruff를 지나게 한 형식뿐이다. 옮기기 전의 근거는
프로브를 날짜, "명세 검토의 프로브", "스크래치 프로브" 같은 말로 가리킨다. 이 표가 그 말을 파일로 잇는다.

돌리는 법은 저장소 루트에서 `PYTHONUTF8=1 uv run python .scratch/http-channel/probes/<파일>`이다.
"옛 `create_app`"은 채널 라우트가 붙기 전의 시그니처(`plugins`, `trace`, `token`, `stderr`)다. 지금
코드에서 그대로 돌리려면 앱 구성을 고쳐야 한다.

| 파일 | 재는 것 | 근거로 드는 자리 | 다시 돌 때 |
|---|---|---|---|
| `probe_sse.py` | yield 라우트가 첫 항목 전에 던지면 나가는 상태 코드, 끊기면 제너레이터가 받는 것 | ADR 0014의 Considered Options("끊기면 실행도 취소한다")와 Consequences(실행 전 실패는 봉투로), 명세 Problem Statement("연결은 끊긴다") | 그대로 |
| `probe_mw_sse.py` | `BaseHTTPMiddleware` 둘 뒤에서 SSE가 조각별로 가는지, 끊김이 제너레이터에 닿는지, 요청 밖 태스크가 끝까지 가는지 | 명세 Problem Statement, Implementation Decisions "실행은 앱이 소유한다", Testing Decisions "둘째 구동자"의 모양 | 그대로 |
| `probe_openapi_sse.py` | 별칭 없이 `AsyncIterator[Event]`를 쓰면 계약의 스트림 항목이 어떻게 인라인되는지 | 명세 Implementation Decisions "스트림" | 저장소 venv |
| `probe_named_event.py` | `type Event = sdk.Event` 별칭이 이름 있는 컴포넌트가 되는지, `TraceEvent`와 멤버를 함께 가리키는지 | 명세 Implementation Decisions "스트림" | 저장소 venv |
| `probe_contract.py` | 인자로 변형을 고른다. `collide`(결정 멤버를 이벤트 이름으로 지으면 컴포넌트가 `-Input`·`-Output`으로 갈라지는지), `default_discriminator`(판별자에 기본값을 두면 required에서 빠지는지), `sse_items`·`plain_response`(스트림 항목 스키마) | 티켓 03·04의 "명세 검토의 프로브", `channel/http/router.py`의 요청 본문 모델 주석, ADR 0014의 2026-09-24 이력 "계약의 스트림 항목 스키마는 FastAPI의 정형 그대로 둔다", `tests/channel/http/test_router.py`의 계약 컴포넌트 이름 주석과 본문·결정 스키마 테스트 독스트링 | 옛 `create_app` |
| `probe_dep.py` | 첫 이벤트를 의존성에서 기다리면 실행 전 실패가 봉투가 되는지, 제너레이터 안에서 던지면 예외 그룹을 거쳐 고정 문구의 500이 되는지, 판별자 없는 `{}`가 거부되는지 | 티켓 03(500 테스트의 `message` 단언), 티켓 04(판별자 기본값), `tests/channel/http/test_router.py`의 실행 전 구성 오류 500 테스트 독스트링 | 옛 `create_app` |
| `probe_log.py` | 본문 검증 오류가 서버 기록 한 줄에 무엇을 싣는지(가짜 키 값으로) | 티켓 03의 "명세 검토가 쟀다" | 옛 `create_app` |
| `probe_uvicorn_shutdown.py` | 연결이 남은 SSE 스트림이 있을 때 uvicorn 0.53.0이 멈추는 순서와 걸리는 시간. 인자는 유예 초 또는 `none` | ADR 0014의 2026-09-24 이력 "서버를 멈출 때 연결이 남은 실행도 유예 뒤에 취소한다", 명세 Further Notes | 루프백 포트를 연다. 인자가 필수다 |
| `shadow/pkg/` | 패키지 안의 `http/`가 스크립트로 실행할 때 표준 라이브러리 `http`를 가리는지. `PYTHONUTF8=1 uv run python .scratch/http-channel/probes/shadow/pkg/main.py`가 `No module named 'http.cookies'`로 끝나면 가린 것이다 | ADR 0016의 2026-09-25 이력 "표준 라이브러리와 부딪치지 않는 것은 모듈 실행에서만 참이다", http-channel 티켓 01 | 그대로 |
| `bisect_fastapi.py` + `locked.txt` | 잠긴 의존성 위에서 fastapi만 0.135.0~0.141.1로 바꿔 가며 채널·서버 테스트가 서는 가장 낮은 버전을 찾는다. 이름과 달리 이분 탐색이 아니라 차례로 훑는다 | ADR 0014의 2026-09-26 이력 "fastapi의 하한은 …", 티켓 03, `pyproject.toml`의 fastapi 하한 주석 | 전용 venv가 있어야 한다. 스크립트의 `SCRATCH`·`PYTHON`이 옛 스크래치패드를 가리키고, venv는 `locked.txt`(`uv export`)와 편집 설치한 `agent_os`로 만들었다. PyPI에 닿고 그 venv의 fastapi를 바꾼다 |
| `probe_scope.py` | 취소 범위 안에서 yield하는 제너레이터를 소비하는 태스크가 이벤트 사이에 await해도, 취소가 없으면 끝까지 가는지(아래의 대조군) | `channel/http/runs.py`의 `_drive` 독스트링("스크래치 프로브로 쟀다") | 그대로 |
| `probe_scope_cancel.py` | 그 await에서 취소되면 제너레이터가 취소 범위 안에 멈춘 채 남아 태스크 그룹이 깨지는지 | 같은 독스트링 | 그대로 |
