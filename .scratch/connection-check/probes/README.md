# connection-check 프로브

명세와 ADR이 근거로 드는 측정 스크립트다. 규약은 `docs/agents/issue-tracker.md`의 "프로브와 근거", 짓는 규칙은 `.claude/rules/probes.md`다. 근거로 드는 자리는 `.scratch/connection-check/spec.md`와 ADR 0067의 2026-11-21 이력이다.

`model_requests_live.py` 하나만 바깥에 닿는다. 실제 Anthropic API에 GET 요청만 보내고 모델은 부르지 않는다. 나머지 둘은 바깥 네트워크와 실제 키를 쓰지 않는다.

| 파일 | 재는 것 | 근거로 드는 자리 | 다시 돌 때 | 잰 판 |
|---|---|---|---|---|
| `check_port_split.py`(모양 `port_split_shape.py`) | 접속 확인의 두 길을 타입으로 가르는 모양이 저장소의 pyright strict 설정에서 서는지. 도구 포트에 원격 확인과 stdio 확인을 따로 두고, 관리 쪽에는 포트가 아니라 확인 함수만 넘기며, 화면이 스스로 하는 확인의 길이 받는 묶음에는 stdio 확인이 없다. 표지는 설정이 strict인 것, pyright가 두 사본을 분석한 것(`filesAnalyzed`), 일부러 넣은 줄 아홉에 기대한 진단 열하나(줄과 규칙의 쌍. 포트의 모양을 어긴 일곱 줄에 여덟, 설정이 strict인지를 보는 두 줄에 셋)가 모두 나고 기대 밖의 진단이 없는 것, 타입 우회 판정자(`tools/check_type_escapes.py`)가 심은 우회를 찾는 것이다 | 명세 "포트와 층", ADR 0067 결정 "포트와 층" | `uv run python .scratch/connection-check/probes/check_port_split.py`(저장소 루트). 사본을 저장소 밖 임시 폴더에 쓰고 지운다. 한 번에 몇 초가 걸렸다(시간은 재지 않았다) | pyright 1.1.414(저장소의 `[tool.pyright]`, `typeCheckingMode = "strict"`), Python 3.12.10. Windows 10(이 PC)만. 2026-11-21 |
| `model_requests_loopback.py` | `anthropic`과 `openai` SDK가 모델에 붙었는지 묻는 요청을 어떻게 보내고 실패를 어떻게 올리는지. 요청의 메서드·경로·헤더, 오류 상태마다의 예외 종류, 서버가 본문에 되울린 글과 키가 예외의 글에 실리는지, 재시도 횟수, 닫힌 포트와 늦는 서버, 목록이 여러 쪽일 때의 요청 수, 실행이 쓰는 `ChatAnthropic`의 공개 칸으로 만든 클라이언트가 실행과 같은 서버·같은 키로 묻는지, 로그 수준 셋에서 찍히는 줄. 회차마다의 표지는 그 독스트링 | 명세 "모델을 확인하는 법", "화면에 보이는 글과 비밀", "기한", "결과가 남는 자리", ADR 0067의 2026-11-21 이력 | `uv run python .scratch/connection-check/probes/model_requests_loopback.py`(저장소 루트). 서버는 사례마다 127.0.0.1의 빈 포트에 띄우는 표준 라이브러리 HTTP 서버다. 전부에 십몇 초가 걸렸다(시간은 재지 않았다) | anthropic 1.7.0, openai 3.49.0, httpx2 2.13.0, langchain-anthropic 1.7.2, Python 3.12.10(저장소의 `.venv`). Windows 10(이 PC)만. 2026-11-21 |
| `model_requests_live.py` | 실제 Anthropic Models API가 그 요청에 어떻게 답하는지. 모델 파일의 `model_id` 하나를 묻는 요청, 날짜를 뗀 이름, 없는 id, 틀린 키, 목록의 쪽 수와 날짜를 뗀 이름이 목록에 실리는지, 응답 본문과 헤더에 쓴 양이나 속도 제한이 실리는지. 회차마다의 표지는 그 독스트링 | 명세 "모델을 확인하는 법"과 Further Notes, ADR 0067의 2026-11-21 이력 | `uv run --env-file ../../../.env python .scratch/connection-check/probes/model_requests_live.py`(워크트리 루트. `.env`의 경로가 그 자리에 매인다). `https://api.anthropic.com`에 GET 여섯 번이고(회차마다 한 번) 모델을 부르지 않는다. 키가 없으면 요청 없이 2로 끝난다 | anthropic 1.7.0, Python 3.12.10. 저장소 주인의 키 하나, 2026-11-21의 응답. Windows 10(이 PC)만 |

## 2026-11-21 결과

아래에서 "쟀다"는 위 프로브가 낸 값이고, 프로브마다 마지막 실행의 출력이다. 출력 파일은 남기지 않았다(같은 명령이 다시 낸다). 코드를 읽은 것은 "읽었다"와 파일로, 공식 문서를 읽은 것은 "읽었다"와 주소로, 재지 않은 수와 해석은 "어림"으로 적는다.

### 결과를 본 뒤 바꾼 것

- **타입 프로브의 기대 한 줄, 두 번.** 첫 실행에서 받지 않은 확인을 꺼내는 줄(`checks.stdio`)에 기대한 `reportAttributeAccessIssue` 말고 `reportUnknownMemberType`과 `reportUnknownVariableType`이 함께 나서 대조군 회차가 측정 아님으로 끝났다(후보의 "진단 0개"도 그 실행에서는 세지 않았다). 없는 속성이라 타입을 모른다는 진단이 따라 나는 것이 맞아 기대에 더했다. 세 규칙을 한 줄에 적으면 줄 길이를 넘어 `return (`과 `checks.stdio`의 두 줄로 나눴는데, 둘째 실행에서 뒤의 두 규칙이 `return (` 줄에 나는 것을 보고 기대를 그 줄로 옮겼다. 후보 쪽의 판정(진단 0개, 우회 0개)은 바꾸지 않았다.
- **루프백 프로브의 잡음.** 첫 실행에서 클라이언트가 쉬는 연결을 끊을 때 표준 라이브러리 서버가 그 추적을 표준 오류에 찍었다. 연결 쪽 오류(`OSError`)만 삼키게 고쳤고 표지와 결과 문구는 바꾸지 않았다. 고친 뒤의 실행도 열한 회차가 모두 측정이었고 결과 문구가 첫 실행과 같았다(닫힌 포트와 늦는 서버의 초만 0.01~0.03초 달랐다).
- **실제 API 프로브의 응답 읽기.** 첫 판은 `with_raw_response`의 `parse()`를 기다리지 않았다. 편집기의 타입 진단이 코루틴이라고 짚어 돌리기 전에 고쳤다.
- **표지 셋을 좁혔다(셀프 리뷰 표준 축의 지적).** 루프백 프로브의 `refused` 회차는 두 호출이 예외로 끝났다는 것만 봤는데, 두 SDK의 호출이 모두 `APIConnectionError`(`APITimeoutError`는 아니다)로 끝난 것을 보게 고쳤다. `timed_out` 회차에는 두 호출이 `APITimeoutError`로 끝난 것을 더했다. 실제 API 프로브의 `retrieve_alias` 회차에는 날짜를 뗀 이름이 목록에 없는 것을 더했다. 앞선 표지는 엉뚱한 예외로 끝난 회차와 목록에 있는 이름을 물은 회차도 측정으로 셌을 것이기 때문이다. 고친 뒤 두 프로브를 다시 돌렸고 루프백은 열한 회차, 실제 API는 여섯 회차가 모두 측정이었다. 결과 문구는 앞선 실행과 같고 초만 달랐다(아래).
- **로그 회차의 표지를 좁히고, 실제 API 프로브가 싣는 예외의 글에서 키를 가린다(PR 직전 리뷰의 지적).** 루프백 프로브의 `log_lines` 회차는 INFO에서 `httpx2` 로거가 한 줄을 찍은 것만 표지로 봤다. 그러면 WARNING과 DEBUG 수준에서 요청이 나가지 않은 실행도 "WARNING 0줄"로 읽힌다. 수준마다 요청 셋이 저마다의 서버에 한 건씩 닿아 성공, 401, 성공으로 끝난 것을 표지에 더했다. 실제 API 프로브는 예외의 글(`str(예외)`)의 앞 200자를 출력에 실었는데, 서버가 받은 키를 그 글에 되울리면 키가 출력에 남는다. 환경의 키 값이 그 글에 있으면 `<가린 키>`로 바꾼 뒤에 싣게 고쳤다. 고친 뒤 루프백을 두 번(둘째는 줄 나눔만 고친 뒤다), 실제 API를 한 번 다시 돌렸고 루프백은 열한 회차, 실제 API는 여섯 회차가 모두 측정이었다. 결과 문구는 앞선 실행과 같고 초만 달랐다(아래). 루프백의 `log_lines` 결과 문구에는 수준마다 닿은 요청과 끝난 모양이 더 붙는다.

### 1. 두 길을 타입으로 가르는 모양 — `check_port_split.py`

다섯 회차가 모두 측정이고 종료 코드 0이었다(쟀다, `.scratch/connection-check/probes/check_port_split.py`).

- **후보는 진단 0개, 타입 우회 0개다.** 포트의 메서드를 `tools.check_remote`처럼 묶인 메서드로 꺼내 `Callable` 타입의 칸에 넘기는 조립이 strict에서 그대로 선다. 관리 쪽이 받는 묶음에는 `connect`가 없다.
- **걸리는 줄.** stdio 서버를 원격 확인에 넘기는 줄과, 전송을 가르지 않은 서버 칸(`McpServer | None`)을 그대로 넘기는 줄은 `reportArgumentType`이다. stdio 확인을 원격 확인의 자리에 돌려주거나 조립에서 넘기는 줄은 `reportReturnType`과 `reportArgumentType`이다(`Parameter 2: type "HttpServer" is incompatible with type "StdioServer"`). 스스로 하는 확인의 묶음에서 `stdio`를 꺼내는 줄은 `reportAttributeAccessIssue`다. 접속 확인 메서드가 없는 옛 가짜를 포트 자리에 넘기는 줄은 `reportReturnType`이다(`"check_remote" is not present`).
- **타입이 막지 못하는 것.** 스스로 하는 확인의 묶음에 stdio 확인의 칸을 새로 더하는 변경은 타입 오류가 아니다. 그 변경은 묶음의 정의를 고치는 것이라 리뷰와 아키텍처 테스트의 몫이다(어림. 재지 않았다). 포트보다 넓게 받는 구현(`WideTools`)은 포트를 만족하지만, 부르는 쪽은 포트의 좁은 타입으로만 넘길 수 있어 위의 줄들이 그대로 걸린다(후보에 그 구현이 들어 있고 진단이 없다). 받은 확인 함수에서 `__self__`로 포트에 거슬러 올라가는 길은 재지 않았다.

### 2. SDK가 보내는 요청 — `model_requests_loopback.py`

열한 회차가 모두 측정이고 종료 코드 0이었다(쟀다, `.scratch/connection-check/probes/model_requests_loopback.py`).

- **요청의 모양.** `anthropic`의 `models.retrieve("probe-model")`는 `GET /v1/models/probe-model` 한 건이고 키는 `x-api-key` 헤더로 간다(`authorization` 헤더는 없다). `openai`의 `models.list()`는 `base_url`이 `…/v1`일 때 `GET /v1/models` 한 건이고 키는 `Authorization: Bearer`로 간다. `openai`의 `models.retrieve("served-a")`는 `GET /v1/models/served-a`다.
- **목록의 쪽.** `anthropic`의 `models.list()`는 쿼리 없이 `GET /v1/models`를 보내고, `limit=1000`을 주면 `?limit=1000`이 붙는다. 서버가 `has_more: true`를 주면 첫 쪽만 읽을 때는 요청 한 건이고, 끝까지 돌면(`async for`) `after_id`가 든 둘째 요청이 간다. `openai`의 목록은 서버가 `has_more: true`를 줘도 끝까지 요청 한 건이다.
- **실패가 닿는 예외.** 재시도 0회로 부르면 상태마다 요청 한 건이고 예외는 이렇다. `anthropic`: 401 `AuthenticationError`, 403 `PermissionDeniedError`, 404 `NotFoundError`, 429 `RateLimitError`, 500 `InternalServerError`, 529 `OverloadedError`. `openai`: 401 `AuthenticationError`, 404 `NotFoundError`, 429 `RateLimitError`, 500 `InternalServerError`. 모두 그 SDK의 `APIStatusError`이고 `status_code`가 서버가 준 상태다. 닫힌 포트는 두 SDK 모두 `APIConnectionError`("Connection error.")이고 2.0~2.1초가 걸렸다(표지를 고친 뒤의 실행도 2.05초와 2.1초였다. 셀프 리뷰 표준 축의 서브에이전트는 자기가 다시 돌린 실행에서 2.47초와 2.7초였다고 보고했다. PR 직전 리뷰를 반영한 뒤의 두 실행은 2.23초와 2.59초, 2.2초와 2.79초였다. 실행마다 흔들리는 값이다). 답이 3초 늦는 서버에 기한 0.5초를 주면 두 SDK 모두 0.51초에 `APITimeoutError`(`APIConnectionError`의 하위)로 끝났다(PR 직전 리뷰를 반영한 뒤의 두 실행은 모두 0.51초와 0.52초였다).
- **재시도.** 기본 설정의 `anthropic` 클라이언트는 500에 요청을 세 건 보내고 1.36초가 걸렸다(PR 직전 리뷰를 반영한 뒤의 두 실행은 1.4초와 1.46초였다). `max_retries=0`이면 한 건이다.
- **예외의 글에 서버의 글이 실린다.** 서버가 오류 본문에 적은 글(`probe-echo-7f3a …`)과 되울린 키가 두 SDK 모두 `str(예외)`에 그대로 있었다. `anthropic`은 본문 전체를, `openai`는 `error.message`를 싣는다. 그래서 예외의 글을 화면에 그대로 보이면 서버가 쓴 글이 화면에 닿는다.
- **실행과 같은 주소와 키.** 환경에 `ANTHROPIC_API_URL`과 `ANTHROPIC_API_KEY`를 심고 실행과 같은 인자로 `ChatAnthropic`을 만들면 `anthropic_api_url`이 그 주소다. 그 모델의 `ainvoke`가 보낸 `POST /v1/messages`와, 그 모델의 공개 칸(`anthropic_api_url`, `anthropic_api_key`)으로 만든 `anthropic.AsyncAnthropic`의 `GET /v1/models/probe-model`이 같은 서버에 같은 키로 닿았다. 같은 환경에서 인자 없이 만든 `anthropic.AsyncAnthropic()`의 주소는 `https://api.anthropic.com`이었다. 곧 SDK 클라이언트를 환경에만 맡기면 `ANTHROPIC_API_URL`로 주소를 바꾼 배포에서 확인과 실행이 다른 서버에 묻는다. 인자 없는 클라이언트는 주소만 읽었고 요청을 보내지 않았다.
- **로그.** 수준마다 요청 셋을 보냈고, 셋이 저마다의 서버에 한 건씩 닿아 성공, 401, 성공으로 끝났다(세 수준 모두). 루트 로거가 기본 수준(WARNING)이면 그 요청 셋(성공 둘, 401 하나)에 찍힌 줄이 0이었다. INFO면 `httpx2` 로거가 요청마다 한 줄, 모두 세 줄을 찍는다(`HTTP Request: GET http://127.0.0.1:<포트>/v1/models/probe-model "HTTP/1.1 200 OK"` 꼴이고 주소 전체와 응답 상태가 실린다). DEBUG면 다섯 로거가 59줄을 찍었다(`anthropic._base_client`, `openai._base_client`, `httpx2`, `httpcore2.connection`, `httpcore2.http11`). 세 수준 어디에도 키 글자가 든 줄은 없었다. `serve` 안에서 루트 로거의 수준이 무엇인지는 재지 않았다. `src/agent_os`에 로깅을 구성하는 코드가 없다는 것은 읽었다(`adapters/mcp.py`의 필터 하나뿐이다).

### 3. 실제 Anthropic Models API — `model_requests_live.py`

여섯 회차가 모두 측정이고 종료 코드 0이었다(쟀다, `.scratch/connection-check/probes/model_requests_live.py`). 세 번 돌렸다. 둘째는 `retrieve_alias`의 표지를 좁힌 뒤이고, 셋째는 예외의 글에서 키를 가리게 고친 뒤다. 세 실행의 결과 문구가 초만 빼고 같았고, 아래의 초는 첫 실행의 값이다(둘째 실행은 차례로 0.44초, 0.27초, 0.21초, 셋째 실행은 1.0초, 0.27초, 0.24초였다). 셋째 실행에서 환경의 키로 물은 없는 id의 회차가 출력에 실은 예외의 글은 오류의 종류(`not_found_error`), 물은 id, 요청 식별자뿐이었고 `<가린 키>`가 없었다(손으로 봤다, 위 명령으로 돌린 셋째 실행의 출력). 가리는 함수가 키가 든 글에서 실제로 키를 바꾸는지를 보는 회차는 두지 않았으므로, 이 프로브가 "실제 Anthropic은 키를 되울리지 않는다"를 잰 것은 아니다.

- **모델 파일의 id.** `plugins/models/claude-opus-5/plugin.toml`의 `claude-opus-5`를 하나만 물으면 200이고 같은 id가 돌아온다. 0.46초가 걸렸다.
- **날짜를 뗀 이름.** 목록에 있던 `claude-opus-4-5-20251101`에서 날짜를 뗀 `claude-opus-4-5`를 하나만 물으면 200이고 `claude-opus-4-5-20251101`이 돌아온다. 그 이름은 목록(15개)에 없었다. 그래서 목록에 그 글자가 있는지로 가르면, 날짜를 뗀 이름을 적은 모델 파일을 없는 모델로 잘못 가른다. 모델을 부르는 요청이 그 이름을 받는지는 여기서 재지 않았다. 공식 문서의 모델 쪽은 표 아래 각주에서, 4.6 세대 앞의 모델은 별칭이 날짜 붙은 id를 가리키는 이름이라고 적는다(웹 요약, `https://platform.claude.com/docs/en/about-claude/models/overview`. 2026-11-21에 받은 그 쪽의 글에 `claude-opus-4-5`라는 글자는 없었고, 표에는 최신 모델 넷만 있었다).
- **없는 id와 틀린 키.** 없는 id는 404 `NotFoundError`(본문의 종류 `not_found_error`, 0.24초), 지어낸 키는 401 `AuthenticationError`(`authentication_error`, 0.21초)다.
- **목록의 쪽.** `limit` 없이 물으면 15개에 `has_more`가 거짓이고, `limit=1000`도 같다. 지금은 한 쪽에 다 온다. 문서는 기본을 20개로 적는다(웹 요약, `https://platform.claude.com/docs/en/api/models/list`).
- **쓴 양과 요금.** 하나를 묻는 응답의 본문에 `usage` 키가 없었다(키는 `capabilities`, `created_at`, `deprecated_at`, `display_name`, `id`, `lifecycle`, `line`, `max_input_tokens`, `max_tokens`, `retires_at`, `type`). 응답 헤더 가운데 `anthropic-`으로 시작하거나 속도 제한을 적는 이름은 `anthropic-organization-id`, `anthropic-workspace-id`, `request-id` 셋뿐이었다. 공식 문서의 Models API 두 쪽, 속도 제한 쪽, 가격 쪽에는 이 요청에 요금이나 한도를 매기는 문장이 없었다(웹 요약이다. 앞 세션이 WebFetch로 받은 글에서 찾지 못한 것이고 가격 쪽은 서브에이전트의 보고다. 이어받은 세션이 다시 받은 것은 목록 쪽 `https://platform.claude.com/docs/en/api/models/list` 하나이고, 그 쪽에도 요금이나 속도 제한의 문장이 없었다). 그래서 이 요청에 요금이 붙는다는 근거는 찾지 못했다(어림. 붙지 않는다고 적은 문서도 없다). 30초마다 묻는 것이 어떤 한도에 걸리는지는 재지 않았다.
- **"붙었다"가 뜻하는 것.** 200은 제공사가 답했고, 키를 받아들였고, 그 id를 안다는 데까지다. 그 키로 그 모델을 실제로 부를 수 있는지(한도, 권한, 모델을 부르는 쪽의 장애)는 이 요청으로 가르지 못한다(어림).

### 4. 모델 서버(`openai-compatible`)

띄운 모델 서버로는 재지 않았다. 빌린 vLLM 서버가 `GET /v1/models`에 답해 준비 확인이 통과했다는 것은 읽었다(일지 `docs/journal/2026-11-13-1423-llm-local-command-rents-model-servers.md`의 준비 확인 기록, `tools/llm_local.py`의 `fetch_models`). id 하나를 묻는 요청(`GET /v1/models/<id>`)을 그런 서버가 받는지는 보지 않았다.

### 5. 손으로 본 것 — `docker compose`

지어낸 값만 든 임시 프로젝트(서비스 하나, `env_file` 하나, 이미지는 받지 않았다)에서 세 명령을 손으로 쳤다(Docker 29.9.2, Compose 5.6.1, Windows 10의 Git Bash, 2026-11-21). 프로젝트 파일은 세션 스크래치패드에 두고 커밋하지 않았다.

- `docker compose config`는 `env_file`의 값과 `${변수}`로 끼워 넣은 값을 모두 평문으로 찍는다(지어낸 비밀번호와 키 글자가 출력에 그대로 있었다).
- `docker compose config --images`는 이미지 이름과 태그 한 줄만 찍는다.
- `docker compose ps --all`의 머리줄은 `NAME IMAGE COMMAND SERVICE CREATED STATUS PORTS`다. 컨테이너가 없어 줄은 없었다.

배포 묶음의 compose 파일로는 치지 않았다. `serve`가 `env_file: .env`를 쓴다는 것은 읽었다(`deploy/standalone/compose.yaml`).
