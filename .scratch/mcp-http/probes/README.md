# mcp-http 프로브

명세·ADR이 근거로 드는 측정 스크립트다. 규약은 `docs/agents/issue-tracker.md`의 "프로브와 근거", 짓는 규칙은 `.claude/rules/probes.md`다. 근거로 드는 자리는 `.scratch/mcp-http/spec.md`와 ADR 0049의 2026-11-09 이력이다.

## 돌리는 법

저장소의 `.venv`에 mcp 2.3.0, httpx2 2.13.0, anyio 4.15.1, uvicorn 0.53.0, starlette 1.6.0이 있어(`uv.lock`) 그대로 돈다. 저장소 루트에서 돈다(Windows, Git Bash). `http_close.py`는 인자 없이 돌리면 사례 열둘을 세 회차씩 돌고, 사례 이름을 주면 그것만 돈다(`--repeat`로 회차 수를 바꾼다. 모르는 이름은 돌리지 않고 2로 끝낸다). `manifest_shape.py`는 openapi-typescript와 tsc를 `web/node_modules`에서 찾는다. 워크트리에는 `node_modules`가 없어 주 체크아웃의 것을 준다. `--branch field`나 `--branch callable`로 한 갈래만 돌 수 있다.

```sh
uv run python .scratch/mcp-http/probes/http_close.py
uv run python .scratch/mcp-http/probes/http_close.py deadline_shield_finally deadline_shield_finally_hang
uv run python .scratch/mcp-http/probes/manifest_shape.py --node-modules <주 체크아웃>/web/node_modules
```

Linux는 Docker 컨테이너에서 돈다. `linux.sh`가 컨테이너 안에 환경 하나를 만들어(판은 저장소의 `uv.lock`과 같게 고정한다) `http_close.py`를 돌고 끝에 `exit <코드>`를 찍은 뒤 그 코드로 끝난다. 그래서 `docker run`의 종료 코드가 프로브의 것이다(PR 직전 리뷰 전에는 마지막 `echo`의 0이 덮어 프로브가 1로 끝나도 `docker run`은 0이었다. 고친 뒤 모르는 사례 이름 `bogus_case`로 돌려 `docker run`이 2로 끝나는 것을 봤다. 손으로 봤다, 아래 명령의 끝에 `bogus_case`). 저장소 루트를 `/repo`에 읽기 전용으로 붙인다(프로브가 `tools/probe_kit.py`를 저장소 루트에서 가져온다). 네트워크로 패키지를 받는다. 인자는 그대로 프로브에 넘긴다.

```sh
MSYS_NO_PATHCONV=1 docker run --rm --init -v "<저장소 루트>:/repo:ro" python:3.12.10-slim-bookworm sh /repo/.scratch/mcp-http/probes/linux.sh
```

`--init`은 컨테이너의 첫 프로세스가 고아가 된 프로세스를 거두게 한다(mcp-shutdown 프로브와 같다). 프로브는 픽스처 서버를 사례마다 새 프로세스로 띄우고 자기가 쥔 `Popen` 핸들로만 끈다. 번호를 보고 끄지 않는다(`.claude/rules/probes.md`).

| 파일 | 재는 것 | 근거로 드는 자리 | 다시 돌 때 | 잰 판 |
|---|---|---|---|---|
| `http_close.py`(픽스처 서버 `http_fixture_server.py`, Linux 실행 `linux.sh`) | mcp 2.3.0의 `streamable_http_client`와 `ClientSession`을 직접 열고, 실행 타임아웃처럼 취소 범위가 연결 전체를 감싼 채 닫는 길마다 세션 종료 요청(DELETE)이 서버에 닿는지, 기한의 표지(`cancelled_caught`)가 참인지, 예외가 새는지, 걸린 시간. 사례는 정상 닫기(`normal`), 명세가 고른 길(`terminate_on_close=False`, `try`·`finally`의 보호와 프로브의 DELETE)로 닫는 정상 닫기(`normal_own_delete`), 보호 없는 닫기(`deadline_plain`, 대조군), ADR 0049의 첫째 안(`deadline_shield_exit`), 라이브러리의 종료 요청을 끄고 같은 자리에 보호를 둔 갈래(`deadline_shield_delete`), 답하지 않는 서버에서의 첫째 안(`deadline_shield_exit_hang`), 문맥을 닫은 다음 문장에 보호를 둔 갈래(`deadline_shield_after`), `try`와 `finally`로 나눈 보호(`deadline_shield_finally`), 답하지 않는 서버에서의 그것(`deadline_shield_finally_hang`). 접속 실패는 닫힌 포트(`closed_port`)와 401(`unauthorized`)의 예외 종류와 글, 응답 훅이 받는 상태, 거부까지의 시간. 모든 사례에서 쿼리 문자열과 토큰 값이 예외 글과 `mcp`·`httpx2`·`httpcore2` 로거의 DEBUG 줄에 실리는지(`query_url_normal`이 쿼리가 서버에 닿는 양성 대조, 서버 기록의 `authorization_seen`이 토큰이 닿는 양성 대조). 표지는 독스트링 | `spec.md`의 Problem Statement, "접속", "실패 문구", "닫기", "로그", Testing Decisions, Further Notes. ADR 0049의 2026-11-09 이력 | 위 명령. 기다리는 사례는 회차마다 1초의 기한과 2초의 유예가 들고, 답하지 않는 서버의 사례는 그 위에 2초 더 든다. 전부(열두 사례 36회차)의 시간은 재지 않았다 | mcp 2.3.0, httpx2 2.13.0, anyio 4.15.1, uvicorn 0.53.0, starlette 1.6.0, Python 3.12.10. Windows 10(이 PC, httpcore2 2.13.0)과 Docker의 Debian bookworm(WSL2 커널 6.18. httpcore2는 httpx2가 끌어온 판이고 기록하지 않았다). 2026-11-09 |
| `manifest_shape.py` | `[server]`를 `transport`로 가르는 판별 유니온을 두 갈래(pydantic의 보통 판별자 `field`, `transport` 없음을 stdio로 읽는 호출 가능 판별자 `callable`)로 두고, 읽기 사례 여섯(칸 없음, http 모양, http에 `command`, 모르는 값, stdio에 `url`, stdio에 `command` 없음)의 읽힌 모델과 거부의 위치·종류, FastAPI 앱이 뽑은 OpenAPI 스키마의 모양(`server`의 anyOf와 oneOf, discriminator, 두 모델의 required. 표지는 oneOf의 갈래가 두 모델의 `$ref`인 것), openapi-typescript 7.13.0이 만든 TS 타입의 `transport` 리터럴과 tsc 5.9.3 `--strict`가 `transport`로 좁힌 소비 코드를 지나게 하고 좁히지 않고 `url`을 읽은 코드(양성 대조)를 TS2339로 거부하는지(소비 지점). 표지는 독스트링 | `spec.md`의 "매니페스트", "계약과 관리 화면", Testing Decisions | 위 명령. 임시 폴더에 TS 파일을 쓰고 Node 도구 둘을 띄운다. 시간은 재지 않았다 | pydantic 2.13.5, fastapi 0.141.1, Python 3.12.10, openapi-typescript 7.13.0, typescript 5.9.3(주 체크아웃의 `web/node_modules`). Windows(이 PC)만. 2026-11-09 |

## 2026-11-09 결과

### 닫기 — `http_close.py`

같은 날 네 번 돌린 실행 가운데 마지막(응답 훅의 상태 기록, 토큰 로그, `httpcore2` 로거를 더한 판)의 것이다. 앞선 세 실행은 사례와 기록 칸을 더해 가며 돌았고 겹치는 사례의 판정은 마지막 실행과 같았다(출력은 세션 스크래치패드에 두고 커밋하지 않았다). Windows와 Linux 모두 33회차가 측정이고 측정 아님은 0, 종료 코드 0이었다. 시간은 초이고 세 회차의 범위다. Windows의 0.0은 시계(`time.monotonic`)의 해상도 아래라는 뜻으로 본다(어림. 같은 사례의 Linux 값이 수 밀리초다). `normal_own_delete`는 셀프 리뷰 뒤 더한 사례라 같은 날 `normal`과 함께 두 OS에서 따로 돌렸다(두 사례 각 3회차. 두 OS 모두 6회차 측정, 측정 아님 0, 종료 코드 0). 그 행의 괄호 안 `normal` 값은 그 실행의 것이다.

PR 직전 리뷰(CodeRabbit CLI, 같은 날) 뒤 `unauthorized`의 표지에 응답 훅이 401 응답을 받았다는 조건을 더했다. 그 전 표지는 예외가 났고 서버 기록에 헤더 없는 POST가 있다는 것뿐이라 401 아닌 까닭의 예외도 측정으로 세어졌다(픽스처가 기대와 다른 `Authorization`을 모두 401로 막아 그런 회차가 실제로 난 적은 없다). 그 사례만 두 OS에서 다시 돌려 각 3회차 측정, 측정 아님 0, 종료 코드 0이었고 세 회차 모두 훅이 `POST 401 Unauthorized`를 받았다(프로브가 찍은 `statuses`). 위 33회차의 셈은 마지막 실행의 것이고, 그 실행의 `unauthorized` 3회차도 훅이 401을 받았으므로(아래 "접속 실패" 표의 응답 훅 칸) 새 표지로도 33회차가 측정이다. 같은 리뷰 뒤 모르는 사례 이름을 거부하게 했다. 그 전에는 모르는 이름이 기본 갈래로 돌아 측정으로 세어졌다(`bogus_case`를 주니 세 회차가 `initialized`와 add 3으로 측정이 되고 0으로 끝났다. 손으로 봤다, `uv run python .scratch/mcp-http/probes/http_close.py bogus_case`). 지금은 돌리지 않고 2로 끝난다(같은 명령).

| 사례 | 기한 표지 | 종료 요청 | 새어 나온 예외 | Windows | Linux |
|---|---|---|---|---|---|
| `normal` | 기한 없음 | 라이브러리가 보냄. 닿음, 세션 일치, 200 | 없음 | 닫기 0.0~0.016 | 닫기 0.002~0.003 |
| `normal_own_delete`(따로 돌림) | 기한 없음 | 프로브가 보냄. 닿음, 세션 일치, 200, 유예 안(`grace_expired` 거짓) | 없음 | 닫기 0.0~0.015(같은 실행의 `normal` 0.015) | 닫기 0.003~0.005(같은 실행의 `normal` 0.003~0.004) |
| `deadline_plain` | 참 | 닿지 않음 | 없음 | 기한에서 돌아오기까지 0.008~0.023 | 0.003 |
| `deadline_shield_exit` | 기록 없음(예외로 끝남) | 라이브러리가 보냄. 닿음, 세션 일치, 200 | `RuntimeError: Attempted to exit a cancel scope that isn't the current tasks's current cancel scope` | 열기에서 예외까지 1.017~1.02 | 1.007~1.01 |
| `deadline_shield_delete` | 기록 없음 | 닿지 않음 | 같은 `RuntimeError` | 1.001~1.014 | 1.009 |
| `deadline_shield_exit_hang` | 기록 없음 | 닿음(서버 기록. 답은 30초 뒤라 받지 못함) | 같은 `RuntimeError` | 닫기 2.0~2.015, 열기에서 예외까지 3.019~3.046 | 닫기 2.003, 3.01~3.011 |
| `deadline_shield_after` | 참 | 닿지 않음. `grace_expired`가 기록되지 않음(보호 문장이 돌지 않았다) | 없음 | 기한에서 돌아오기까지 0.005~0.019 | 0.003~0.004 |
| `deadline_shield_finally` | 참 | 프로브가 보냄. 닿음, 세션 일치, 200, 유예 안(`grace_expired` 거짓) | 없음 | 닫기 0.0, 기한에서 돌아오기까지 0.012~0.022 | 닫기 0.002~0.008, 0.005~0.011 |
| `deadline_shield_finally_hang` | 참 | 닿음(서버 기록). 유예 2초에 끊음(`grace_expired` 참) | 없음 | 닫기 2.0~2.016, 기한에서 돌아오기까지 1.998~2.034 | 닫기 2.003, 2.005~2.006 |

- **첫째 안의 예외는 보호의 자리 때문이다.** 라이브러리의 종료 요청을 끄고 같은 자리에 보호를 둔 갈래(`deadline_shield_delete`)도 같은 `RuntimeError`로 끝났으므로 원인은 종료 요청이 아니다. 보호의 자리만 `finally`로 옮긴 `deadline_shield_finally`는 예외 없이 종료 요청이 닿아 양성 대조가 된다. anyio 문구의 뜻(라이브러리가 안에서 연 취소 범위가 아직 현재 범위인 채로 바깥의 보호 범위를 나가게 된다)은 문구를 읽은 해석이고 anyio의 코드로 확인하지 않았다.
- **취소된 범위에서 문맥 닫기의 `await` 뒤 문장은 돌지 않는다.** `deadline_shield_after`와 `deadline_shield_finally`는 같은 코드에서 `try`와 `finally`로 나눴는지만 다르다. 앞은 `grace_expired`가 기록되지 않고 종료 요청이 닿지 않았고, 뒤는 둘 다 됐다.
- **2초 유예가 닫기를 끊는다.** 답하지 않는 서버의 두 사례에서 닫기가 두 OS 모두 2.0초 안팎이었고, `deadline_shield_finally_hang`에서 `grace_expired`가 참이었다. 답하는 서버(`deadline_shield_finally`)에서는 거짓이다.
- **종료 요청 도달의 양성 대조**는 `normal`(라이브러리가 보내 닿는다)과 `deadline_plain`(보호 없이는 닿지 않는다)이다. 서버 기록의 `mcp-session-id`가 응답 훅이 받아 둔 세션 식별자와 같은 것으로 세션 일치를 봤다.
- **기한의 결말.** `cancelled_caught`를 기록한 네 사례(`deadline_plain`, `deadline_shield_after`, `deadline_shield_finally`, `deadline_shield_finally_hang`) 모두 참이었다. ADR 0034가 stdio에서 본 양상(안쪽 task group이 취소를 삼켜 거짓이 된다)은 어느 사례에서도 나지 않았다.
- **정상 종료가 명세의 길을 지날 때.** `normal_own_delete`가 같은 실행의 `normal`과 같은 범위였다(Windows 0.0~0.015 대 0.015, Linux 0.003~0.005 대 0.003~0.004). 종료 요청은 프로브가 보내 같은 세션으로 닿았고(200) 유예 안에 끝났다. 명세 "닫기"와 ADR 0049 이력의 "정상 종료는 늦지 않는다"는 이 측정에 기댄다. 첫 실행에서는 이 사례가 없어 어림으로 두었던 자리다.

### 접속 실패와 쿼리 문자열 — `http_close.py`

세 사례 모두 주소에 쿼리 문자열(`?token=query-secret-4b9d`)을 넣어 열었다. 시간은 초다.

| 사례 | 예외 | 응답 훅 | 쿼리 문자열 | 걸린 시간 Windows / Linux |
|---|---|---|---|---|
| `closed_port` | `ExceptionGroup`(하위 하나) 안의 `httpx2.ConnectError: All connection attempts failed` | 응답 없음 | 예외 글에 없음. 로그 `mcp.client.streamable_http` DEBUG 한 줄(`Connecting to StreamableHTTP endpoint: <주소 전체>`)에 있음. 로그 네 줄 | 거부까지 2.036~2.037 / 0.002 |
| `unauthorized` | `mcp.shared.exceptions.MCPError: Server returned an error response` | `POST 401 Unauthorized` | 예외 글에 없음. 로그 `mcp` DEBUG 한 줄과 `httpx2` INFO 한 줄(`HTTP Request: POST <주소 전체> "HTTP/1.1 401 Unauthorized"`)에 있음. 로그 13줄 | 예외까지 0.003~0.004 / 0.004~0.006 |
| `query_url_normal` | 없음(add가 3) | 2xx뿐 | 서버 기록의 요청 여섯(DELETE 포함)이 모두 `/mcp?token=…`로 닿음(양성 대조). 로그 `mcp` DEBUG 한 줄과 `httpx2` INFO 여섯 줄에 있음. 로그 89줄 | 닫기 0.0~0.015 / 0.003~0.004 |

- `unauthorized`의 서버 기록은 헤더 없는 `POST` 하나뿐이었다. 라이브러리는 401에 다시 보내지 않았다.
- 표지를 더한 뒤 다시 돌린 `unauthorized`(위 "닫기"의 문단)는 예외까지 Windows 0.004~0.005, Linux 0.003~0.004로 위 표의 범위와 같았다(프로브가 찍은 값).
- Windows의 닫힌 포트 2초는 루프백에서 IPv6와 IPv4를 차례로 시도하며 생기는 거부 지연으로 본다(어림. 가르지 않았다. 설계 일지 2026-11-09-1229가 손으로 본 2.175초와 같은 자리다). Linux에서는 그 지연이 없었다.

### 토큰 값은 로그에 실리지 않는다 — `http_close.py`

두 OS 33회차 모두 `token_in_exception`이 거짓이고 `token_in_log`가 빈 목록이었다. 곧 헤더 값(`Bearer fixture-token-7c1e`)은 예외 글에도 세 로거(`mcp`, `httpx2`, `httpcore2`)의 DEBUG 줄에도 없다. 세 로거의 줄 수는 `normal`·`query_url_normal` 89, `deadline_shield_finally` 74, `deadline_shield_finally_hang` 69, `deadline_plain`·`deadline_shield_after` 59, `unauthorized` 13, `closed_port` 4였다. 양성 대조는 연결을 연 모든 사례의 서버 기록 `authorization_seen`이 그 값인 것이다(값이 요청에 실려 서버에 닿았다). 그 사례는 아홉(27회차)이다. `unauthorized`는 헤더 없이 열어 양성 대조가 없고, `closed_port`는 실었으나 서버에 닿지 않아 양성 대조가 없다. 그 6회차의 "로그에 없다"는 양성 대조 없는 관찰이다. `httpcore2`는 httpx2의 전송 층이라 이 실행에서 함께 달았다.

### 매니페스트 — `manifest_shape.py`

Windows에서 돌았다(`--node-modules`는 주 체크아웃). 첫 실행은 14회차 측정이었다. 셀프 리뷰 뒤 stdio에 `command` 없음 사례와 스키마 표지(oneOf의 갈래가 두 모델의 `$ref`인지. 그 전 표지는 갈래의 수만 봐 `anyOf [X, null]`에도 참이었다)를 더해 전체를 다시 돌렸고 16회차가 측정, 측정 아님 0, 종료 코드 0이었다. PR 직전 리뷰(CodeRabbit CLI, 같은 날) 뒤 거부 사례의 표지를 어떤 검증 오류든 있으면 측정에서 기대한 위치·종류의 쌍(`REJECTED` 표)이 오류에 있을 때만 측정으로 바꾸고 전체를 한 번 더 돌렸다. 바꾼 까닭은 입력 오타 같은 엉뚱한 까닭의 거부도 측정으로 세어졌기 때문이다. 16회차 측정, 측정 아님 0, 종료 코드 0이었고 아래 표의 값은 그대로였다(거부 회차의 결과 줄이 기대 쌍을 함께 찍는다). 아래 표는 그 실행들의 것이다.

| 사례 | `field`(보통 판별자) | `callable`(호출 가능 판별자) |
|---|---|---|
| `transport` 없음 | 거부. 위치 `server`, 종류 `union_tag_not_found` | `StdioServer`로 읽힘(`transport`가 `"stdio"`로 채워짐) |
| http 모양 | `HttpServer` | `HttpServer` |
| http에 `command` | 거부. 위치 `server.http.command`, 종류 `extra_forbidden` | 같다 |
| 모르는 값(`grpc`) | 거부. 위치 `server`, 종류 `union_tag_invalid`. 문구가 기대 태그 `'stdio', 'http'`와 받은 값을 든다 | 같다(문구의 판별자 이름만 함수 이름이다) |
| stdio에 `url` | 거부. 위치 `server.stdio.url`, 종류 `extra_forbidden` | 같다 |
| stdio에 `command` 없음 | 거부. 위치 `server.stdio.command`, 종류 `missing` | 같다 |
| OpenAPI 스키마 | `server`는 anyOf에 oneOf(`StdioServer`, `HttpServer`)와 null. oneOf에 `discriminator.mapping`이 있다. 두 모델의 required에 `transport`가 든다 | 같되 `discriminator`가 없다 |
| TS 소비 | 타입에 `transport: "stdio"`와 `transport: "http"` 리터럴. 좁힌 코드는 tsc 0, 좁히지 않고 `url`을 읽은 코드는 TS2339(양성 대조) | 같다 |

- 거부의 위치는 pydantic의 판별 유니온이 태그 이름을 경로에 넣는 모양이다(`server.http.command`). 지금 `server.command`인 stdio의 `command` 없음은 두 갈래 모두 `server.stdio.command`(종류 `missing`)로 거부된다. 첫 실행에서는 stdio에 `url`을 섞은 사례에서 미루어 봤던 것을 다시 돌린 `.scratch/mcp-http/probes/manifest_shape.py`의 실행이 쟀다.
- 명세가 고른 것은 `callable`이다. 두 갈래의 차이는 칸 없음의 처리와 스키마의 `discriminator` 유무뿐이고, TS 소비 지점은 같았다.
