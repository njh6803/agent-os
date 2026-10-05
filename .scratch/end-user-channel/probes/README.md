# end-user-channel 프로브

명세·ADR·코드 주석이 근거로 드는 측정 스크립트다. 규약은 `docs/agents/issue-tracker.md`의 "프로브와 근거". 라이브러리와 알고리즘을 고른 측정은 `.scratch/web-widget/probes/jwt_verify/`이고(설계 인터뷰), 여기는 명세가 정할 것을 설치된 판으로 잰 것이다.

다섯 다 저장소 루트에서 저장소 `.venv`로 돈다. 임시 환경을 만들지 않는다.

```sh
PYTHONUTF8=1 uv run python .scratch/end-user-channel/probes/sse_id_frames.py
PYTHONUTF8=1 uv run python .scratch/end-user-channel/probes/check_types.py
PYTHONUTF8=1 uv run python .scratch/end-user-channel/probes/cors_scoped.py
PYTHONUTF8=1 uv run python .scratch/end-user-channel/probes/jwt_claims.py
PYTHONUTF8=1 uv run python .scratch/end-user-channel/probes/run_timeout.py
```

| 파일 | 재는 것 | 근거로 드는 자리 | 다시 돌 때 | 잰 판 |
|---|---|---|---|---|
| `sse_id_frames.py` | 최종 사용자 스트림이 프레임마다 SSE `id`를 싣고도 계약에 항목 유니온이 이름 있는 컴포넌트로 서는지. 모양 셋(A: `ServerSentEvent` 주해, C: `SkipJsonSchema`로 멤버를 더한 별칭 주해, E: 같은 유니온을 별칭 없이)마다 응답 바이트의 `id:` 줄, `itemSchema.properties.data`가 가리키는 것, 컴포넌트 목록, 어디서도 가리키지 않는 컴포넌트, pydantic 단독 `$defs`를 찍는다. 모양 B(항목 유니온 주해에 `ServerSentEvent` yield)는 pyright가 거부하는 모양이라 여기 없고 `check_types.py`에만 있다 | `spec.md`의 "최종 사용자 스트림 — 프레임과 항목 유니온" | 인자 없음. 네트워크 없이 `ASGITransport`로 돈다 | fastapi 0.141.1, starlette 1.6.0, pydantic 2.13.5, httpx 0.28, Python 3.12.10. 2026-10-05 |
| `check_types.py` | 모양 B·C·E가 저장소의 pyright strict와 타입 우회 검사(`tools/check_type_escapes.py`)를 지나는지. 검사하는 동안만 `tests/_probe_end_user_*.py`를 만들고 지운다(pyright는 `include` 밖을 검사 없이 "0 errors"로 지난다). B는 오류가 나야 하는 대조군이다 | 같은 절 | 인자 없음. `uv run pyright --outputjson`을 파일마다 한 번, 타입 우회 검사를 저장소 루트에 모양마다 한 번 부른다. 수십 초 | pyright 1.1.414, 위와 같은 판. 2026-10-05 |
| `cors_scoped.py` | Starlette `CORSMiddleware`를 경로 접두사 하나에만 걸고(접두사로 가르는 ASGI 분기 하나) 그 안쪽의 `RequireToken`이 낸 401에도 CORS 헤더가 붙는지. 사례 여섯: 접두사 아래 preflight(토큰 없음), 접두사 밖 preflight, 접두사 아래 토큰 없는 POST의 401, 접두사 아래 라우트가 낸 429의 `Retry-After` 노출, 허용 목록 밖 출처, 접두사 밖의 출처 있는 요청 | `spec.md`의 "CORS" | 인자 없음. 저장소의 `agent_os.http.auth`·`errors`를 그대로 import한다 | fastapi 0.141.1, starlette 1.6.0, httpx 0.28. 2026-10-05 |
| `run_timeout.py` | 실행 타임아웃을 core의 몸통(`_drive`) 안에 두면 걸린 모델 호출이 `run_failed`로 끝나는지. core `_drive`를 흉내 낸 async generator가 `anyio.fail_after` 안에서 실제 `McpTools`로 픽스처 서버(`tests/adapters/mcp_fixture_server.py`)에 붙고 모델 호출 자리에서 오래 자며, 소비자는 채널 `Runs._drive`처럼 태스크 그룹의 다른 태스크에서 await 없이 흐름에 넣는다. 대조군은 소비자가 바깥에서 `move_on_after`로 자르는 것(ADR 0014가 거부한 모양). 항목의 도착 시각, 마지막 항목, 태스크 그룹의 예외를 찍는다 | `spec.md`의 "실행 타임아웃" | 인자 없음. 픽스처 서버를 실제로 띄우므로 두 사례에 약 7초씩 든다. 타임아웃(6초)은 서버가 뜨는 시간(이 기계에서 1초 남짓)보다 길어야 한다 — 처음 1초로 돌렸을 때는 연결 중에 끊겨 yield를 건넌 뒤의 취소를 재지 못했다. 재는 것은 모델 호출 자리의 취소이고 도구 호출 중의 취소와 서버 프로세스의 소멸은 재지 않는다 | anyio 4.15.1, langchain-mcp-adapters 0.3.2, mcp 1.30.0, Python 3.12.10. 2026-10-05 |
| `jwt_claims.py` | 설치된 PyJWT로 명세가 정할 클레임 규칙이 서는지. `options={"require": [...]}`가 `iat`·`sub` 없는 토큰을 거부, 미래 `iat` 거부(라이브러리), 최대 수명 `exp - iat`는 소비 지점이 센다, `kid`로 키 고르기(없는 `kid` 거부, `kid` 없으면 목록을 차례로, 교체 중 키 둘 모두 수락), 서명 검증 전에 `iss`로 사이트 항목 고르기(모르는 발급자는 키를 보기 전에 거부), 사례 열넷, 그리고 RS256 2048비트 검증 한 번의 시간 | `spec.md`의 "서명 토큰" | 인자 없음. 키는 실행마다 새로 만든다. 끝 줄 "기대와 다른 사례"가 0이어야 한다 | pyjwt 2.14.0, cryptography 50.0.1, Python 3.12.10. 2026-10-05 |

## 2026-10-05 결과

`sse_id_frames.py`.

- 넷 모두 `ServerSentEvent(data=항목, id="…")`를 yield하면 프레임이 `data:` 줄과 `id:` 줄로 나간다. `data`는 항목 모델의 `model_dump_json()`이다.
- A의 `itemSchema.properties.data`는 `{"type": "string"}`이라 항목 스키마가 없다.
- C는 `contentSchema`가 `EndUserFrame`을 가리키고 그 컴포넌트는 `{"$ref": "#/components/schemas/EndUserItem"}` 하나다. E는 `contentSchema`가 `EndUserItem`을 바로 가리킨다. 둘 다 `EndUserItem`은 `oneOf`와 `discriminator`를 든 이름 있는 컴포넌트다.
- C와 E 모두 FastAPI의 정의 수집이 `ServerSentEvent`를 어디서도 가리키지 않는 컴포넌트로 남긴다. pydantic 단독(`TypeAdapter(...).json_schema()`)의 `$defs`는 `EndUserItem`·`Finished`·`Started`뿐이다. 지금 루트 `openapi.json`은 컴포넌트 37개가 모두 참조된다(같은 날 `json.dumps` 뒤 `$ref` grep으로 손으로 봤다).
- `openapi` 판은 3.1.0 그대로다.

`check_types.py`. B는 분석 1 파일에 pyright 오류 1(`"ServerSentEvent" is not assignable to "EndUserItem"`), C와 E는 분석 1 파일에 오류 0. 타입 우회 검사는 셋 다 종료 0(프로브 파일에 우회가 없다).

`cors_scoped.py`.

| 사례 | 상태 | 헤더 |
|---|---|---|
| (1) 접두사 아래 preflight, 토큰 없음 | 200 | `Access-Control-Allow-Origin: https://site.example`, `Allow-Methods: GET, POST`, `Allow-Headers`에 `Authorization`·`Last-Event-ID` |
| (2) 접두사 밖 preflight, 토큰 없음 | 401 | CORS 헤더 없음 |
| (3) 접두사 아래 토큰 없는 POST | 401 | `Allow-Origin`, `Vary: Origin`, `Expose-Headers: Retry-After, X-Request-Id`, `WWW-Authenticate: Bearer` |
| (4) 접두사 아래 라우트의 429 | 429 | 위 셋과 `Retry-After: 7` |
| (5) 허용 밖 출처 | 200 | `Allow-Origin` 없음(`Expose-Headers`만 붙는다 — Starlette가 단순 헤더를 출처와 무관하게 붙인다) |
| (6) 접두사 밖, 출처 있는 GET | 200 | CORS 헤더 없음 |

`run_timeout.py`(타임아웃 6초, 모델 호출 자리에서 100초 잠).

| 모양 | 항목(도착 초) | 마지막 | 걸린 시간 | 태스크 그룹 예외 |
|---|---|---|---|---|
| 안쪽(core 몸통의 `fail_after`) | tools(1.21), llm_called(1.21), run_failed(6.03) | `run_failed`, `TimeoutError` | 6.03s | 없음 |
| 바깥(소비자의 `move_on_after`, 대조군) | tools(1.06), llm_called(1.06) | `llm_called` | 6.01s | 없음 |

- 안쪽에 두면 MCP 연결이 열린 채 yield를 건넌 뒤에도 취소가 `TimeoutError`로 바뀌어 결말(`run_failed`)이 붙고, 태스크 그룹이 예외 없이 닫혔다(MCP 어댑터의 anyio 범위가 깨지지 않았다). 바깥에서 자르면 결말이 없다.
- 픽스처 서버가 뜨는 데 약 1.1~1.2초가 들었다(`tools` 항목의 도착 시각).

`jwt_claims.py`. 사례 열넷이 모두 기대와 같았다(기대와 다른 사례 0). `require`에 든 `iat`·`sub`가 빠지면 `MissingRequiredClaimError`, 미래 `iat`는 `ImmatureSignatureError`(라이브러리), 수명 11분은 소비 지점의 검사가 거부하고 10분 꼭은 수락, 모르는 `kid`·모르는 발급자·남의 키·숫자 `sub`는 거부, `kid` 없는 토큰은 키 둘인 사이트에서 차례로 시도해 수락, `aud` 배열에 우리가 들면 수락. RS256 2048비트 검증(헤더와 클레임 읽기, 사이트 고르기, `decode`, 수명 검사)은 1000회 226~230ms로 한 번 약 0.23ms였다(세 번 돌려 두 값, 이 기계, 윈도우 10).
