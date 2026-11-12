# local-model 프로브

명세·ADR이 근거로 드는 측정 스크립트다. 규약은 `docs/agents/issue-tracker.md`의 "프로브와 근거", 짓는 규칙은 `.claude/rules/probes.md`다. 근거로 드는 자리는 `.scratch/local-model/spec.md`와 ADR 0057이다.

클라우드, 실제 모델 서버, 실제 키는 쓰지 않는다. 서버는 `fake_server.py`가 루프백(127.0.0.1)의 빈 포트에 사례마다 새로 띄우는 가짜 모델 서버(Chat Completions)이고, 키 자리의 글자(`probe-key-0123456789` 등)는 모두 지어낸 것이다. 그래서 여기서 본 것은 `langchain-openai`와 `openai` SDK가 요청을 어떻게 짓고 응답과 실패를 어떻게 읽는지까지다. 실제 모델 서버(vLLM이나 Ollama로 띄운 것)가 그 요청을 받아들이는지는 보지 않았다.

## 돌리는 법

`langchain-openai`가 저장소의 `pyproject.toml`에 없어 저장소의 `.venv`로는 돌지 않는다. 저장소 밖의 디렉터리(아래 `<환경 루트>`)에 환경 하나를 만들어 그 인터프리터로 돈다. `make_env.py`가 `uv export --frozen`으로 뽑은 저장소 락의 판 위에 `langchain-openai==1.6.2`를 얹고, 깔린 것을 락과 견줘 JSON 한 줄로 찍는다(패키지는 네트워크나 uv 캐시에서 받는다). 저장소의 `.venv`, `pyproject.toml`, `uv.lock`은 건드리지 않는다. 명령은 저장소 루트에서 친다(Windows, Git Bash).

```sh
uv run python .scratch/local-model/probes/make_env.py <환경 루트>
<환경 루트>/.venv/Scripts/python.exe .scratch/local-model/probes/openai_compat.py --out <출력 파일>
<환경 루트>/.venv/Scripts/python.exe .scratch/local-model/probes/openai_compat.py fail_401_echo_string guard_candidate_401
<환경 루트>/.venv/Scripts/python.exe .scratch/local-model/probes/openai_compat.py --list
uv run python .scratch/local-model/probes/check_adapter_types.py <환경 루트>
```

- `make_env.py`는 `<환경 루트>`가 이 저장소 안이거나 `pyproject.toml`이 있는 디렉터리면 아무것도 깔지 않고 2로 끝난다(손으로 봤다, 인자 자리에 워크트리 루트 `.`과 주 체크아웃의 루트). 그런 자리의 `.venv`는 그 프로젝트의 환경이라 거기에 얹으면 저장소의 환경이 바뀐다. 이미 있는 `.venv`에 이 프로브가 만들며 심은 표지 파일(`.agent-os-local-model-probe`)이 없어도 2로 끝난다(손으로 봤다. 표지 없이 만들어진 앞 환경에 다시 치니 "이 프로브가 만들지 않은 .venv 가 있다"와 2였고, 새 폴더에는 표지 파일이 심기고 0으로 끝났다). 표지가 생기기 전에 만든 환경은 지우고 다시 만든다.
- `uv run --with`로 얹는 길은 이 PC에서 쓰지 못했다. `uv run --with langchain-openai==1.6.2 python .scratch/local-model/probes/versions.py`가 jsonpointer 3.1.1의 바퀴를 임시 환경에 깔다 `invalid entry (directory) in the scripts directory`로 끝났다(손으로 봤다, 그 명령. uv 0.10.8, Windows 10. 다시 쳐도 같은 오류였다). 까닭은 보지 않았다.
- `openai_compat.py`는 사례 이름을 주면 그것만 돌고, 없으면 108 사례 전부를 돈다. `--out <파일>`을 주면 사례마다의 JSON 줄 전부는 그 파일에 쓰고 화면에는 `case`·`measured`·`result`만 찍는다. 모르는 사례 이름은 돌리지 않고 2로 끝난다(손으로 봤다, 위 셋째 명령의 사례 자리에 `bogus_case`). 표지가 없는 사례나 예외로 끝난 사례가 하나라도 있으면 1로 끝난다(`tools/probe_kit.py`의 `Rounds`).
- 첫 줄은 돈 환경의 판(`versions.py`)과 프로브가 지운 환경 변수의 이름이다. 프로브는 시작할 때 `OPENAI_`·`LANGSMITH_`·`LANGCHAIN_`·`LC_OUTPUT_`으로 시작하는 변수와 프록시 변수 넷(`HTTP_PROXY`, `HTTPS_PROXY`, `ALL_PROXY`, `NO_PROXY`)을 지우고, 사례가 필요한 것만 그 사례 동안 심는다(`support.py`의 `scrub_environment`, `environment`). 이 PC에서는 지울 것이 없었다(첫 줄의 `scrubbed_variables`가 비었다).
- `check_adapter_types.py`는 후보 어댑터와 양성 대조 파일을 `<환경 루트>/typecheck/`에 복사해 저장소 루트에서 `uv run pyright --outputjson --venvpath <환경 루트>`로 검사한다. 저장소 안의 점 폴더(`.scratch`)는 pyright가 분석하지 않아 저장소 밖의 사본을 쓴다. 저장소의 파일은 고치지 않는다. `<환경 루트>`가 저장소 안이거나 `pyproject.toml`이 있는 디렉터리면 `make_env.py`와 같이 아무것도 복사하지 않고 2로 끝난다(손으로 봤다, 인자 자리에 워크트리 루트 `.`).

- PR 봇 회차에서 표지 셋을 좁혔다(결과를 본 뒤가 아니라 봇의 지적 때문이다). `guard_candidate_key_rotation`은 지운 뒤의 호출이 요청 없이 변수 이름과 "가 없다"가 든 예외로 끝나야 측정이다. `guard_candidate_success`는 둘째 호출도 도구 호출 하나를 돌려받아야 측정이다. `candidate_connections_after_failures`는 401·500·JSON 아님 갈래의 실행이 그 갈래의 예외 글(`(HTTP 401)`, `(HTTP 500)`, `(ValueError)`와 "Unexpected response type")이 든 예외로 끝나야 기대한 대로 끝난 것으로 센다. 좁힌 뒤 108 사례 전체는 측정 108회차, 측정 아님 0회차였고 이 셋의 결과 문구는 좁히기 전과 같았다(쟀다, `.scratch/local-model/probes/openai_compat.py`).

- 리눅스는 Docker의 컨테이너로 돈다. `linux_lifetime.sh`가 컨테이너 안에서 위 환경과 같은 판(저장소 락의 런타임 의존 위에 `langchain-openai==1.6.2`)을 깔고 `openai_compat.py`를 돈다. 저장소 루트(Git Bash)에서 출력 폴더를 만든 뒤 아래처럼 친다. 사례 이름을 빼면 108 사례 전부다. 출력 폴더에 화면 출력(`stdout.txt`), 사례마다의 JSON 줄(`lifetime.jsonl`), 프로브의 종료 코드(`exit.txt`)가 생긴다. 셀프 리뷰가 이 명령 그대로 수명 사례 아홉을 돌렸다(아래 12).

```sh
MSYS_NO_PATHCONV=1 docker run --rm -v "$(pwd -W):/repo:ro" -v "<출력 폴더>:/out" python:3.12.10-slim-bookworm sh /repo/.scratch/local-model/probes/linux_lifetime.sh runs_in_one_loop candidate_connections_after_failures calls_on_one_model candidate_released_after_loop_closed keepalive_released_after_loop_closed keepalive_released_inside_loop two_loops_same_url two_loops_own_client two_loops_candidate
```

| 파일 | 재는 것 | 근거로 드는 자리 | 다시 돌 때 | 잰 판 |
|---|---|---|---|---|
| `linux_lifetime.sh` | `openai_compat.py`의 사례를 Docker의 리눅스 컨테이너에서 돈다. 저장소는 읽기 전용으로 붙이고 환경은 컨테이너 안에 새로 깐다 | 명세 "HTTP 클라이언트"의 2026-11-12 주석, 티켓 05의 수명 사례 | Docker, 이미지 `python:3.12.10-slim-bookworm`, 네트워크(uv 0.10.8과 패키지를 받는다). 위 "돌리는 법"의 명령 | `openai_compat.py`와 같다. Python 3.12.10, uv 0.10.8 |
| `openai_compat.py`(사례 모듈 `cases_request.py`·`cases_key.py`·`cases_response.py`·`cases_failure.py`·`cases_guard.py`·`cases_logs.py`·`cases_lifetime.py`, 가짜 서버 `fake_server.py`, 공용 `support.py`, 판 `versions.py`) | `ChatOpenAI`를 가짜 서버에 붙여 core의 길(`core/loop.py`의 `model_caller`가 하는 `bind_tools` 뒤 `ainvoke`, `core/model.py`의 `reply_from`)로 부른 108 사례. 요청의 경로·본문·헤더, 환경 변수가 요청에 실리는지, 키 함수가 불리는 때와 횟수, 인증 헤더에 실을 수 없는 키, 깨진 도구 호출 인자, 실패가 닿는 예외의 종류·글·원인 사슬·재시도 횟수와 그 안의 키·주소, 후보 어댑터가 그 예외를 바꾸는지, 읽는 단계의 주소 검사(sdk의 `HttpServer`)를 지난 주소가 모델을 만들다 거부되는지, DEBUG 로그에 키·프롬프트·주소가 실리는지, `usage`와 `model`과 사고 글의 해석, 모델마다 준 HTTP 클라이언트의 연결이 모델을 놓은 뒤와 실패·취소한 호출 뒤에 닫히는지. 사례마다의 표지는 사례 모듈의 독스트링 | `.scratch/local-model/spec.md`의 Problem Statement, Implementation Decisions(매니페스트, 요청, HTTP 클라이언트, 키, 실패 문구와 되울린 키, 인자가 깨진 도구 호출, 로그, 의존)와 Testing Decisions, ADR 0057과 그 2026-11-12 이력 둘 | 위 명령. 환경이 먼저 있어야 한다. 닫힌 포트 사례 셋이 각 7.3~7.5초, 재시도가 드는 사례 일곱이 각 1.2~1.5초 걸렸다. 전부의 시간은 재지 않았다 | langchain-openai 1.6.2, openai 3.49.0, langchain-core 1.6.3, httpx2 2.13.0, httpcore2 2.13.0, h11 0.16.0, anyio 4.15.1, pydantic 2.13.5, Python 3.12.10. Windows 10(이 PC)만. 2026-11-12 |
| `adapter_candidate.py`(검사 `check_adapter_types.py`, 양성 대조 `adapter_types_control.py`) | 후보 어댑터(`ChatOpenAI`를 상속해 `_generate`와 `_agenerate`를 감싼 모양)가 저장소의 pyright strict 설정을 진단 0개로 지나고 타입 우회(`Any`, `cast`, 억제 주석)가 없는지. 표지는 설정이 strict인 것, pyright가 두 파일을 분석한 것(`filesAnalyzed`), 일부러 넣은 타입 오류 여덟 쌍(줄과 규칙)이 모두 나고 기대 밖의 진단이 없는 것, 타입 우회 판정자(`tools/check_type_escapes.py`)가 심은 우회를 찾는 것. 후보의 동작은 윗줄의 `guard_candidate_*` 사례가 본다 | 같은 명세의 실패 문구와 되울린 키, ADR 0057 | 위 다섯째 명령. 환경이 먼저 있어야 한다. 시간은 재지 않았다 | pyright 1.1.414(저장소의 `[tool.pyright]`, `typeCheckingMode = "strict"`), 윗줄의 판. Windows 10(이 PC)만. 2026-11-12 |
| `make_env.py` | 저장소 락의 판 위에 `langchain-openai==1.6.2`를 얹으면 새로 드는 패키지(`new`)와 락과 달라지는 판(`moved`). `moved`가 비지 않으면 1로 끝난다 | 같은 명세의 의존, ADR 0057 | 위 첫째 명령. 패키지를 받는다. 시간은 재지 않았다 | uv 0.10.8, Python 3.12.10, 저장소의 `uv.lock`(브랜치 `docs/local-model-spec`의 2026-11-12 판). Windows 10(이 PC)만. 2026-11-12 |
| `outside_worktree.py` | 워크트리 세션의 명령 하나가 사용자 홈 아래(작업 폴더 밖)에 파일을 쓰고 읽고 지울 수 있는지, 주 체크아웃의 `.env`를 `uv run --env-file`로 넘긴 환경에 `ANTHROPIC_API_KEY`(넘겼다는 표지)와 `RUNPOD_API_KEY`의 이름이 있는지, `--env-file` 없이 띄운 환경에는 그 표지 변수가 없는지(음성 대조). 값은 읽어 견주지도 찍지도 않는다. 표지는 그 독스트링 | 같은 명세의 모델 서버를 띄우는 명령(자리, 걸음 2)과 Further Notes, ADR 0058 | 그 독스트링의 명령 둘(워크트리 루트에서). 둘째는 `.env`의 경로가 워크트리 자리에 매인다. 시간은 재지 않았다 | Python 3.12.10(저장소 `.venv`), uv 0.10.8. Windows 10(이 PC)의 워크트리 세션만. 2026-11-12 |

## 2026-11-12 결과

아래에서 따로 밝히지 않은 값은 모두 `.scratch/local-model/probes/openai_compat.py`의 여덟째 전체 실행이 낸 것이다(쟀다, `probes/openai_compat.py`). 108 사례가 모두 측정이고 측정 아님은 0, 종료 코드 0이었다. 같은 날 전체를 열 번 돌렸다. 뒤의 둘은 PR 직전 리뷰를 받은 세션이 새로 만든 환경에서 돌린 108 사례 실행이고(리뷰를 반영하기 전의 판과 반영한 뒤의 판), 둘 다 108 사례가 모두 측정이었다. 앞의 여덟은 이렇다(88 사례, 사례를 더해 93 사례 두 번, 다시 더해 97 사례, 후보를 고치고 사례를 더해 102 사례, 다시 고치고 더해 104 사례, 셀프 리뷰를 반영해 후보를 고치고 사례를 더해 108 사례, 그 가운데 한 사례의 주소에 줄 구분 문자를 더해 다시 108 사례). 그 사이에 더하거나 고친 사례만 따로 돌린 실행이 여덟 있다. 측정 아님은 그 가운데 하나에서 한 번 났다. 셀프 리뷰 뒤 고친 사례 11개를 따로 돌린 실행에서 `guard_candidate_newline_url`이 표지 없이 끝났고 종료 코드가 1이었다(아래 "결과를 본 뒤 바꾼 것"의 "모델을 만들다 거부되는 주소"). 그 사례를 다시 짠 뒤의 실행 넷(두 사례만 돌린 둘과 108 사례 전체 둘)에는 없었다. 겹치는 사례의 결과 갈래(`result`)는 실행마다 같았는데 두 군데가 달랐다. 97 사례 실행과 102 사례 실행 사이에서 넷이 달랐다. 후보의 HTTP 클라이언트를 바꿔(아래 "결과를 본 뒤 바꾼 것") `two_loops_candidate`가 실패에서 성공으로, 후보의 로그 사례 셋(`logs_success_candidate`, `logs_401_candidate`, `logs_401_query_url`)이 두 줄씩 늘었다(질문 10의 "누가 닫았는가"). 104 사례 실행과 108 사례 실행 사이에서는 하나가 달랐다. 후보가 예외 글에 주소를 글자 그대로 싣게 되어 `guard_candidate_userinfo_401`이 "암호 없음"에서 "암호 글에 있음"으로 바뀌었다(102 사례 실행과 104 사례 실행 사이에서는 102 사례가 모두 같았다). 108 사례 실행 둘 사이에서는 사례를 고친 `guard_candidate_odd_url_401` 하나만 달랐다. PR 직전 리뷰를 반영하기 전과 뒤의 실행 사이에서는 `env_gateway_used_when_omitted` 하나만 달랐다(간 키를 결과 갈래에 싣게 고친 사례다. 아래 "결과를 본 뒤 바꾼 것"의 "PR 직전 리뷰가 짚은 표지와 후보"). 두 출력의 견줌은 세션 스크래치패드의 스크립트로 손으로 봤다. 시간은 여덟째 실행의 값이다. 출력 파일은 세션 스크래치패드에 두고 커밋하지 않았다. 코드를 읽은 것은 "읽었다"와 파일·판으로, 재지 않은 수와 해석은 "어림"으로 적는다.

깔린 판은 ADR 0057이 적은 판과 같았다(langchain-core 1.6.3, langchain-openai 1.6.2, openai 3.49.0). `make_env.py`의 출력은 설치 61개, 락에 없던 패키지 넷(`langchain-openai` 1.6.2, `openai` 3.49.0, `regex` 2026.11.9, `tiktoken` 0.14.0), 락과 달라진 판 없음이었다. openai 3.49.0은 HTTP를 `httpx2`·`httpcore2`로 보낸다(예외의 원인 사슬과 로거 이름이 그 이름이다).

### 결과를 본 뒤 바꾼 것

- **양성 대조 파일의 모양.** `adapter_types_control.py`의 첫 판은 후보 모듈을 import했다. 저장소 밖의 사본에서 그 import가 풀리지 않아 기대하지 않은 진단이 났고 `control_caught`가 측정 아님으로 끝났다(후보의 "진단 0개"도 그 실행에서는 세지 않았다). 대조가 후보를 import하지 않고 `ChatOpenAI`를 바로 쓰게 고쳤다.
- **양성 대조의 기대 한 쌍.** 고친 뒤 타입 없는 인자를 그대로 돌려주는 줄(`return value`)에 `reportUnknownVariableType`이 기대 밖으로 났다. strict가 그 줄에도 진단을 내는 것이 맞아 기대에 더했다(여덟 쌍이 됐다). 후보 쪽의 판정(진단 0개, 우회 0개)은 바꾸지 않았다.
- **결과 갈래의 낱말.** 찾는 글자(키, 주소)가 예외에 "있다"는 낱말이 처음에는 자리를 가르지 않았다. 닫힌 포트 사례에서 주소가 예외가 쥔 요청의 헤더(Host)에만 있는데 "있음"으로 찍혔다. 글(`str`, `repr`, 트레이스백 글)에 있는 것은 "글에 있음", openai 예외가 쥔 `request.headers`와 `body`에만 있는 것은 "예외가 쥔 요청·응답에만 있음"으로 갈랐다(`support.py`의 `leaked`). "글에 있음"은 맨 위 예외만이 아니라 원인 사슬의 어느 예외의 글에 있어도 찍힌다. 자리는 출력의 `leaks`가 하나씩 적는다. 측정 여부(`measured`)의 조건은 바꾸지 않았다.
- **주소의 사용자 정보에서 찾는 글자.** 사용자 정보 사례가 처음에는 암호 글자만 찾아 후보의 결과가 "암호 없음"이었는데, 서버가 되울린 Basic 인증 값(사용자 정보의 base64 꼴)이 글에 있었다. 찾는 글자에 그 값을 더했다(`support.py`의 `USER_BASIC`).
- **후보가 검증 예외에서 싣는 것.** 102 사례 실행까지 후보는 pydantic의 검증 예외도 다른 예외처럼 글 전체를 실었다. 질문 5에서 그 글의 `input_value`에 도구 호출의 인자가 실린다는 것을 보고, 틀린 자리(`loc`)만 싣게 고친 뒤 `guard_candidate_args_*` 둘을 더했다.
- **후보가 예외 글에 싣는 주소, 두 번.** 후보의 첫 판은 `base_url` 전체를 실었다. 사용자 정보와 쿼리가 따라 실리므로 스킴·호스트·포트만 싣게 고쳤다(104 사례 실행까지의 `_server`). 셀프 리뷰가 그 판이 ADR 0057의 결정("주소는 비밀이 아닌 것으로 본다", 실패 문구에 그대로 실린다)과 어긋나고 경로를 잃어 `/v1`을 빠뜨린 주소를 문구로 가르지 못한다고 짚어, 모델 파일에 적은 글자 그대로 싣고 찍히지 않는 글자만 이스케이프하게 되돌렸다(`adapter_candidate.py`의 `_address`. MCP 어댑터의 `_where`와 같은 방식이다). 사용자 정보와 쿼리는 읽는 단계가 거부하는 것으로 막는다. 그래서 그 둘이 든 주소를 후보에 바로 넣는 사례의 글에는 이제 그 둘이 실린다(`guard_candidate_userinfo_401`의 결과가 바뀐 까닭).
- **모델을 만들다 거부되는 주소.** 주소를 글자 그대로 싣게 고친 뒤 개행이 든 주소의 예외 글을 보려고 `guard_candidate_newline_url`을 더했는데, 따로 돌린 실행에서 그 사례가 표지(예외 글에 개행 뒤의 글자가 있다) 없이 끝났다. 모델을 만드는 순간 `httpx2.InvalidURL`이 나서 요청이 0건이었다. 사례의 결함이 아니라 재려던 상황(호출의 실패)이 나지 않는 주소였다. 그 사례를 둘로 갈라 다시 짰다. 읽는 단계의 검사를 지난 주소가 만들기에서 거부되는지를 보는 `build_rejects_address`와, 검사도 만들기도 지나는 이상한 주소가 예외 글에 실리는 꼴을 보는 `guard_candidate_odd_url_401`이다. 읽는 단계의 검사는 sdk의 `HttpServer`를 그대로 불러 본다(`support.py`의 `passes_read_stage`).
- **응답 사례의 표지.** 도구 호출과 `usage` 사례는 처음에 서버가 요청을 한 건 이상 받았는지만 봤다. 셀프 리뷰가 그 표지는 라이브러리가 응답을 읽기 전에 실패해도 선다고 짚어, 요청이 정확히 한 건이고(재시도가 없었다) 결과가 메시지이거나 `openai` 계열이 아닌 예외인 것(응답을 읽는 데까지 갔다)으로 좁혔다(`cases_response.py`의 `_read_the_reply`). 좁힌 뒤에도 그 사례들의 결과는 같았다.
- **후보의 HTTP 클라이언트, 두 번.** 97 사례 실행까지 후보는 라이브러리가 주소별로 캐시한 클라이언트를 나눠 써 `two_loops_candidate`가 실패했다. 모델마다 제 클라이언트(`openai.DefaultAsyncHttpxClient()`)를 주게 고치니 그 사례가 통과했다. 그 클라이언트를 닫는 자리가 없어 질문 10의 사례를 더했고, `runs_in_one_loop`에서 한 루프에 놓인 모델의 연결이 하나도 닫히지 않아 쉬는 연결을 두지 않는 클라이언트(`_own_client`)로 다시 고쳤다. 앞의 클라이언트는 `cases_lifetime.py`의 `keepalive_*` 갈래로 남겼다.
- **가짜 서버의 연결 셈.** 질문 10을 재려고 `fake_server.py`에 받은 연결과 끝난 연결의 수(`opened_connections`, `closed_connections`)를 더했다. 다른 사례의 응답은 바꾸지 않았다.
- **더한 사례.** 첫 전체 실행 뒤 해석을 가르려고 `two_loops_own_client`·`two_loops_candidate`(둘째 루프의 실패가 나눠 쓰는 클라이언트 때문인지), `userinfo_url_401`·`guard_candidate_userinfo_401`, `logs_401_query_url`을 더했다. 이 글을 쓰다가 넷을 더 더했다. `env_identity_headers`에서 `OPENAI_ORGANIZATION`이 실리지 않은 것이 "읽지 않는다"인지 "`OPENAI_ORG_ID`에 가려졌다"인지 갈리지 않아 `env_legacy_org_alone`을, 라이브러리 코드에서 게이트웨이 변수를 읽는 자리를 보고 `env_gateway_explicit_wins`와 양성 대조 `env_gateway_used_when_omitted`를, 어림으로 적었던 자리를 `env_http_proxy_candidate`로 바꿨다. 97 사례 실행 뒤에는 명세가 주소의 쿼리와 조각을 어떻게 다룰지 정하려고 `path_with_fragment`를, 질문 10의 사례 넷을 더했다. 104 사례 실행 뒤에는 셀프 리뷰가 재지 않았다고 짚은 것을 재려고 `candidate_connections_after_failures`와 `calls_on_one_model`을, 위의 두 사례(`build_rejects_address`, `guard_candidate_odd_url_401`)를 더했다. `outside_worktree.py`에는 `--env-file` 없는 실행의 음성 대조 회차를 더했다.
- **PR 직전 리뷰가 짚은 표지와 후보.** PR 직전 리뷰(CodeRabbit CLI와 버그·성능 축)가 짚은 것을 고쳤다. 사례는 더하지 않았다. 표지는 여섯 군데를 고쳤다. 로그 사례는 호출이 고른 갈래대로 끝났는지(성공 갈래는 메시지가 돌아왔다, 상태 코드 갈래는 예외의 글이 그 코드를 든다)와 쿼리 갈래에서 서버가 받은 요청 줄에 쿼리가 있는지를 함께 본다(`cases_logs.py`). 응답 사례의 `_read_the_reply`는 `openai` 계열의 예외 전체를 빼던 것을 전송·상태의 실패 둘(`openai.APIConnectionError`, `openai.APIStatusError`)만 빼게 고쳤다. 그 계열 가운데 응답 본문을 읽다 나는 예외는 재려는 상황이기 때문이다(위 "응답 사례의 표지"가 적은 판을 다시 고친 것이다). 200으로 온 실패 사례는 요청이 정확히 한 건인 것을 본다(`cases_failure.py`의 `_odd_body`). 키 변수 없음과 실을 수 없는 키 사례는 예외의 글이 변수 이름만이 아니라 그 거부의 문구를 드는 것을, 취소 사례는 기한이 실제로 호출을 끊으려 한 것(`cancel_called`)을 본다(`cases_guard.py`). 실패한 호출의 연결 사례는 500 갈래에서 서버가 받은 요청이 호출 수보다 많은 것(재시도가 들었다)을 본다(`cases_lifetime.py`). 결과 갈래는 한 군데를 고쳤다. `env_gateway_used_when_omitted`가 간 인증 헤더가 게이트웨이 키인지를 결과에 싣는다. 후보는 예외 글에서 키를 찾는 값을 둘로 늘렸다. 호출을 시작하며 읽어 둔 값과 예외를 바꾸는 때의 환경 값이다(`adapter_candidate.py`의 `masked`). 호출 도중에 환경의 값이 바뀌는 갈래는 사례가 없어 재지 않았다. `make_env.py`는 저장소 안이나 `pyproject.toml`이 있는 디렉터리를 거부한다(위 "돌리는 법"). `outside_worktree.py`는 "작업 폴더 밖"을 그 폴더가 작업 폴더의 하위가 아닌 것 하나로 본다. 앞의 판은 작업 폴더가 홈 아래에 있지 않다는 조건을 함께 봐서, 체크아웃이 홈 아래에 있으면 밖에 쓰고도 "밖이 아니다"로 끝났다. 고친 뒤의 108 사례 실행은 측정 아님이 0이었고, `check_adapter_types.py`는 다섯 회차가 모두 측정이며 후보의 진단과 타입 우회가 0개였다.

### 1. 요청의 모양 — `cases_request.py`

- **경로.** `base_url`이 `…/v1`이든 `…/v1/`이든 `POST /v1/chat/completions`다(`path_plain`, `path_trailing_slash`). `/v1` 없이 주면 `POST /chat/completions`다(`path_without_v1`). 쿼리가 든 주소는 경로가 쿼리 뒤에 붙어 `POST /v1/?probe_token=query-secret-4b9dchat/completions`로 깨진다(`path_with_query`). 조각(`#probe-fragment`)이 든 주소는 조각이 빠지고 `POST /v1/chat/completions`다(`path_with_fragment`).
- **본문.** 도구를 묶어 부르면 키는 `messages`, `model`, `stream`(false), `tools` 넷이다. 도구 하나는 `{"type": "function", "function": {"name", "parameters", "description"}}`이고 `strict`가 없다. `tool_choice`, `parallel_tool_calls`, `max_tokens`, `max_completion_tokens`, `temperature`, `stream_options`, `n`은 실리지 않는다(`body_with_tools`). 도구 없이 부르면 `tools`도 없다(`body_without_tools`).
- **주면 실리는 이름.** 생성자에 `max_completion_tokens=256`을 주든 `max_tokens=256`을 주든 본문에는 `max_completion_tokens`로 실린다. `temperature=0.2`는 `temperature`로 실린다(`body_with_options`). `max_tokens`라는 이름으로는 보내지 않으므로, 그 이름만 아는 서버가 있으면 값을 무시한다(어림. 실제 서버로 보지 않았다).
- **Responses API로 가지 않는다.** `use_responses_api=False`면 모델 이름이 `gpt-5-pro-local`이나 `my-codex-model`이어도, 환경에 `LC_OUTPUT_VERSION=responses/v1`이 있어도 `/v1/chat/completions`로 간다(`route_pro_name_off`, `route_codex_name_off`, `route_env_version_off`, 후보는 `route_candidate_env_version`). 양성 대조는 그 값을 주지 않은 세 사례이고 셋 다 `POST /v1/responses`로 갔다(`route_pro_name_auto`, `route_codex_name_auto`, `route_env_version_auto`). 보통 이름에 아무것도 주지 않으면 chat completions다(`route_plain`).
- **헤더.** `authorization: Bearer probe-key-0123456789`가 간다. 그 밖에 `user-agent: AsyncOpenAI/Python 3.49.0`과 `x-stainless-*` 아홉(언어, 패키지 판, OS, 아키텍처, 런타임과 그 판, 비동기 여부, raw-response, 재시도 횟수)이 실린다(`authorization_header`).
- **모델 이름이 요청을 바꾼다.** `use_responses_api=False`인 채로도 이름이 `o1-local`·`o3-local`이면 시스템 메시지가 `role: developer`로 가고, `gpt-5-local`·`gpt-5-pro-local`이면 준 `temperature=0.2`가 빠진다. `local-model`과 `my-codex-model`은 그대로다(`model_name_quirks`). 어떤 이름 꼴이 걸리는지의 전부는 보지 않았다(이 여섯 이름만 넣었다).

### 2. 환경 변수 — `cases_request.py`

- **키와 주소는 명시한 것이 이긴다.** 환경에 `OPENAI_API_KEY`, `OPENAI_BASE_URL`, `OPENAI_API_BASE`를 다른 서버와 다른 키로 심고 키와 주소를 명시하면, 요청은 명시한 서버로만 가고(다른 서버 0건) 다른 키는 헤더와 본문 어디에도 없다(`env_explicit_wins`). 양성 대조: 키를 빼면 환경의 키가 가고(`env_key_used_when_omitted`), 주소를 빼면 `OPENAI_BASE_URL`과 `OPENAI_API_BASE`의 주소로 간다(`env_base_url_used_when_omitted`, `env_api_base_used_when_omitted`).
- **LangSmith 게이트웨이 변수도 명시한 것에 진다.** 환경에 `LANGSMITH_GATEWAY`(주소)와 `LANGSMITH_GATEWAY_API_KEY`를 심어도 키와 주소를 명시한 요청은 명시한 서버로만 가고 게이트웨이 쪽은 0건이다(`env_gateway_explicit_wins`). 양성 대조: 키와 주소를 둘 다 빼면 요청이 그 변수의 주소로 `POST /openai/v1/chat/completions`, `Bearer <게이트웨이 키>`로 간다(`env_gateway_used_when_omitted`). 키와 주소 가운데 하나만 뺀 갈래는 넣지 않았다. 그 우선순위는 읽은 것이다(langchain-core 1.6.3의 `utils/_gateway.py`, `_resolve_gateway_config`. 명시한 주소 > `OPENAI_API_BASE` > 게이트웨이, 명시한 키는 그대로).
- **그래도 실리는 변수 넷.** 키와 주소를 명시해도 `OPENAI_ORG_ID`는 `openai-organization` 헤더로, `OPENAI_PROJECT_ID`는 `openai-project` 헤더로, `OPENAI_CUSTOM_HEADERS`는 거기 적은 헤더로 서버에 닿는다. 후보 어댑터도 같다(`env_identity_headers`, `env_identity_headers_candidate`). 그 사례에서 함께 심은 `OPENAI_ORGANIZATION`은 실리지 않았는데, `OPENAI_ORG_ID`에 가려진 것이다. 그것만 심으면 같은 `openai-organization` 헤더로 닿는다(`env_legacy_org_alone`). `OPENAI_ADMIN_KEY`와 `OPENAI_WEBHOOK_SECRET`은 헤더와 본문에 없었다. 생성자 인자로는 막지 못한다고 본다. 두 라이브러리 모두 값이 없으면 환경에서 채운다(읽었다, langchain-openai 1.6.2의 `chat_models/base.py`와 openai 3.49.0의 `lib/_client_auth.py`). 막는 길은 찾지 못했고 해 보지 않았다.
- **프록시.** `OPENAI_PROXY`가 있으면 보통 모델의 요청은 키와 함께 그 프록시로 간다(`env_openai_proxy`). 후보는 `openai_proxy=None`으로 못박아 곧바로 간다(`env_openai_proxy_candidate`). `HTTP_PROXY`가 있으면 127.0.0.1로 가는 요청도 키와 함께 그 프록시로 간다. 보통 모델도 후보도 같다(`env_http_proxy`, `env_http_proxy_candidate`). `NO_PROXY`를 함께 준 갈래는 넣지 않았다.

### 3. 키를 함수로 줄 때 — `cases_key.py`

- 모델을 만들 때는 부르지 않고(0회) 요청마다 한 번 부른다. 두 번 부르니 `Bearer probe-key-call-0001`, `Bearer probe-key-call-0002`가 갔다. 부른 스레드는 이벤트 루프의 스레드(`MainThread`)가 아니라 실행기 스레드(`asyncio_0`)다(`key_function_per_request`). 재시도가 든 `bad_key_newline_function`과 `bad_key_trailing_space_function`에서는 호출 한 번에 세 번 불렸다. 시도마다 다시 부르는 것으로 본다(이 두 사례에서 본 것이다. 429·500의 재시도에 키 함수를 준 사례는 없다).
- 함수가 `RuntimeError("변수 PROBE_MODEL_KEY 가 없다")`를 던지면 그 예외 객체가 그대로 `ainvoke`를 부른 쪽에 닿는다. 원인 사슬이 없고, 함수는 한 번 불렸고, HTTP 요청은 0건이고, 재시도하지 않았다(`key_function_raises`).

### 4. 인증 헤더에 실을 수 없는 키 — `cases_key.py`

- **끝에 개행이나 공백이 든 키.** 요청이 서버에 닿지 않고(0건) 1.25~1.42초 뒤 `langchain_openai.chat_models.base.OpenAIConnectionError("Connection error.")`로 끝난다. 함수로 준 사례에서 키 함수가 세 번 불렸으므로 세 번 시도한 것이다. 맨 위 글에는 키가 없지만 원인 사슬의 `httpx2.LocalProtocolError`, `httpcore2.LocalProtocolError`, `h11._util.LocalProtocolError`의 글이 `Illegal header value b'Bearer nl-key-4f7a91c2\n'`처럼 키를 싣고, 트레이스백 글과 예외가 쥔 요청 헤더에도 있다(`bad_key_newline_string`, `bad_key_trailing_space_string`, 함수로 준 것은 `…_function`). 키가 틀렸다는 뜻이 "연결 실패"로 읽힌다.
- **ASCII가 아닌 글자가 든 키.** 내장 `UnicodeEncodeError`(`'ascii' codec can't encode character '키' in position 11…`)로 바로 끝난다. 원인 사슬이 없고 요청 0건이다. 글(`str`)에는 키가 없고 `repr`에 있다(`bad_key_unicode_string`, `bad_key_unicode_function`).

### 5. 깨진 도구 호출 인자 — `cases_response.py`

- **JSON이 아닌 인자는 예외를 내지 않는다.** `arguments`가 `{"a": 2, "b":`이면 `tool_calls`는 비고 `invalid_tool_calls`에 `{"type": "invalid_tool_call", "id": "call_1", "name": "add", "args": <받은 글 그대로>, "error": "Function add arguments:…are not valid JSON. Received JSONDecodeError …"}`가 든다. `text`는 빈 글이다. `reply_from`은 도구 호출을 보지 못하므로(`reply.tool_calls`가 비었다) 루프는 이 응답을 빈 최종 답으로 읽는다(`tool_args_broken`). 뒤 문장은 `reply_from`의 출력까지 본 것이고 루프를 끝까지 돌리지는 않았다.
- **섞인 응답.** 멀쩡한 호출 하나와 깨진 호출 하나가 오면 앞의 것은 `tool_calls`에, 뒤의 것은 `invalid_tool_calls`에 든다(`tool_args_mixed`). 루프는 멀쩡한 것만 실행하게 된다(어림. `reply_from`의 출력까지만 봤다).
- **이름이 빈 호출.** 깨진 인자에 이름이 비면 `invalid_tool_calls`에 `name: ""`로 든다(`tool_args_broken_empty_name`). 멀쩡한 인자에 이름이 비면 `tool_calls`에 이름 `""`로 든다(`tool_args_valid_empty_name`).
- **그 밖의 꼴.** `arguments`가 빈 글이나 `null`이면 `args {}`인 멀쩡한 호출이다(`tool_args_empty_string`, `tool_args_null`). `"[1, 2]"`(JSON이지만 객체가 아님)는 `pydantic_core._pydantic_core.ValidationError`(`ValueError`의 하위, 글은 `tool_calls.0.args Input should be a valid dictionary`)다(`tool_args_not_object`). 글이 아니라 JSON 객체로 온 `arguments`도 같은 예외다(글은 `invalid_tool_calls.0.args Input should be a valid string`, `tool_args_object_value`). 두 예외의 글에는 받은 인자가 `input_value`로 실린다(질문 7의 `guard_candidate_args_*`가 대조로 본다). `id`가 없는 호출은 `id None`으로 들고 `reply_from`은 `""`로 읽는다(`tool_call_missing_id`).

### 6. 실패가 닿는 모양 — `cases_failure.py`

예외는 `openai`의 것이 아니라 `langchain_openai.chat_models.base`의 하위 클래스로 닿는다. 그 클래스는 `openai`의 예외와 `langchain_core.exceptions`의 예외를 함께 상속하고, 원래의 `openai` 예외가 `__cause__`에 있다.

| 사례 | 닿는 예외 | 글 | 서버가 받은 요청 | 걸린 시간(초) |
|---|---|---|---|---|
| `fail_401_echo_string` (서버가 키를 되울린다) | `OpenAIAuthenticationError` | `Error code: 401 - Incorrect API key provided: probe-key-0123456789. 키를 확인하라.` | 1건 | 0.015 |
| `fail_400` | `OpenAIInvalidRequestError` | `Error code: 400 - ` 뒤에 서버의 글 | 1건 | 0.0 |
| `fail_404` | `OpenAIModelNotFoundError` | `Error code: 404 - ` 뒤에 서버의 글 | 1건 | 0.0 |
| `fail_429` | `OpenAIRateLimitError` | `Error code: 429 - ` 뒤에 서버의 글 | 3건 | 1.36 |
| `fail_500` | `OpenAIAPIError` | `Error code: 500 - ` 뒤에 서버의 글 | 3건 | 1.296 |
| `fail_closed_port` | `OpenAIConnectionError` | `Connection error.` | 닿지 않음(재시도 로그 2줄) | 7.328 |

- **401의 원인 사슬.** `__cause__`가 `openai.AuthenticationError`(같은 글)이고 그 `__context__`가 `httpx2.HTTPStatusError`다. 뒤의 글에는 요청의 주소 전체가 실린다(`Client error '401 Unauthorized' for url 'http://127.0.0.1:<포트>/v1/chat/completions'…`). 되울린 키는 맨 위 예외의 `str`·`repr`·`body`, 원인의 같은 자리, 트레이스백 글, 그리고 세 예외가 쥔 요청 헤더에 있다. 키를 함수로 줘도 같고 요청은 1건이다(`fail_401_echo_function`).
- **재시도.** 400·401·404는 한 번에 끝나고 429·500은 세 번 보낸다(SDK의 `max_retries`가 2다, `client_defaults`). 닫힌 포트도 두 번 더 시도해 7.3~7.5초가 걸렸다(`fail_closed_port`, `query_url_closed_port`, `guard_candidate_closed_port`). 그 시간이 어디에 드는지는 가르지 않았다. Windows가 거부된 연결을 시도마다 2초쯤 붙들고 재시도 사이의 기다림이 더해진 것으로 본다(어림).
- **닫힌 포트의 원인 사슬.** `openai.APIConnectionError` → `httpx2.ConnectError` → `httpcore2.ConnectError` → `OSError` → `ConnectionRefusedError([WinError 1225] …)`다. 주소는 어느 예외의 글에도 없고 예외가 쥔 요청 헤더(Host)에만 있다. 그래서 글만 보면 어느 서버에 닿지 못했는지 알 수 없다.
- **주소의 쿼리.** 쿼리가 든 주소로 401을 받으면 `httpx2.HTTPStatusError`의 글에 쿼리까지 든 주소가 실린다(`query_url_401`). 닫힌 포트에서는 쿼리가 어느 글에도 없다(`query_url_closed_port`).
- **주소의 사용자 정보.** `http://probe-user:probe-pass-77c3@…`로 주면 서버는 `Authorization: Bearer <키>`가 아니라 `Authorization: Basic <base64>`를 받는다. 키는 가지 않는다. 암호 글자는 `httpx2.HTTPStatusError`의 글(주소)에, 서버가 되울린 Basic 값은 맨 위 예외의 글에 실린다(`userinfo_url_401`).
- **200으로 온 실패는 `openai` 예외가 아니다.** 200에 `error` 칸이 든 본문은 내장 `ValueError`이고 글이 그 칸의 `repr`이다(`{'message': 'upstream rejected key probe-key-0123456789', 'code': 'invalid_api_key'}`). 200에 JSON이 아닌 본문은 `ValueError`(`Unexpected response type from OpenAI-compatible endpoint. … got str: '<본문>'`)이고 본문이 글에 그대로 실린다. `choices`가 `null`인 본문은 `TypeError`이고 글은 본문의 키 이름만 든다. 셋 다 원인 사슬이 없고 요청 1건이다(`ok_status_error_body`, `ok_status_not_json`, `ok_status_null_choices`).

### 7. 어댑터가 사이에 설 수 있는가 — `cases_guard.py`, `adapter_candidate.py`

설 수 있다. `ChatOpenAI`를 상속해 `_agenerate`와 `_generate`를 감싸는 첫째 안이 루프의 길에서 듣는다. 다만 이 프로브를 짓기 전에 세운 첫째 안의 꼴 그대로(`openai.OpenAIError`만 받아 `except` 안에서 `from None`으로 던지기)는 두 군데가 샌다. 위임 래퍼(둘째 안)는 첫째 안이 서서 짓지 않았다.

- **대조: 감싸지 않으면 샌다.** 보통 `ChatOpenAI`로 401을 받으면 core에 닿는 것은 `langchain_openai…OpenAIAuthenticationError`이고 글에 키가 있다(`guard_control_plain`).
- **글자 그대로의 첫째 안이 새는 두 곳.** `except openai.OpenAIError` 안에서 `raise RuntimeError(…) from None`을 하면 맨 위 글은 가려지지만 `__context__`에 원래 예외가 남는다. 그 글·`body`·요청 헤더에 키가 있고, 사슬에 `langchain_openai`·`openai`·`httpx2`의 예외 셋이 달려 온다(`guard_first_plan_401`. `__suppress_context__`가 참이라 트레이스백 글에는 찍히지 않는다). 그리고 200에 `error` 칸이 든 응답의 `ValueError`는 `openai.OpenAIError`가 아니라 그대로 지나가 키가 글에 실린다(`guard_first_plan_ok_error_body`).
- **후보가 그 둘을 막는 법.** `Exception`을 받고, 바꾼 예외를 `except` 블록 밖에서 던진다. 401, 500, 200의 `error` 본문, JSON이 아닌 본문, `choices: null`이 모두 내장 `RuntimeError`로, 닫힌 포트가 내장 `ConnectionError`로 닿는다. 글의 키는 `***`로 가려지고, `__cause__`와 `__context__`가 없고, 예외 객체에 내장이 아닌 종류가 달려 오지 않는다(`guard_candidate_401`, `guard_candidate_500`, `guard_candidate_ok_error_body`, `guard_candidate_not_json`, `guard_candidate_null_choices`, `guard_candidate_closed_port`). 글의 꼴은 `모델 서버 http://127.0.0.1:<포트>/v1 가 요청을 거절했다 (HTTP 401): Error code: 401 - Incorrect API key provided: ***. 키를 확인하라.`다. 닫힌 포트는 `모델 서버 http://127.0.0.1:<포트>/v1 에 닿지 못했다: Connection error.`, 200의 `error` 본문은 `모델 서버 http://127.0.0.1:<포트>/v1 호출이 실패했다 (ValueError): {'message': 'upstream rejected key ***', 'code': 'invalid_api_key'}`다(세 글은 108 사례 실행의 저장한 출력에서 손으로 봤다, Grep 도구로 `"text": "모델 서버 `로 시작하는 토막을 찾았다).
- **루프의 길이 재정의를 지난다.** `bind_tools` 뒤 `ainvoke`는 `_agenerate`를, `astream`도 (`disable_streaming=True`라서) `_agenerate`를, 동기 `invoke`는 `_generate`를 지난다(`guard_paths`. 지나간 메서드를 하위 클래스가 적어 본다). `disable_streaming`을 켜지 않은 대조에서는 `astream`이 `_astream`으로 가서 두 메서드를 비켜 가고 키가 샌다(`guard_stream_bypass_control`). 후보의 `astream`과 동기 `invoke`도 401을 같은 꼴로 바꾼다(`guard_candidate_astream_401`, `guard_candidate_invoke_401`). 스트리밍 콜백이 붙은 `ainvoke`가 같은 길이라는 것은 읽은 것이다(langchain-core 1.6.3의 `language_models/chat_models.py`, `_agenerate_with_cache`). 사례가 없다.
- **인자의 꼴이 틀린 도구 호출.** 인자가 `["args-secret-6e1f", 2]`(JSON이지만 객체가 아님)이거나 글이 아닌 객체로 오면 손대지 않은 모델의 예외 글에 그 글자가 실린다(양성 대조). 후보는 둘 다 내장 `RuntimeError`이고 글에 그 글자가 없다. 글은 `모델 서버 http://127.0.0.1:<포트>/v1 의 응답을 읽지 못했다: tool_calls.0.args 의 꼴이 틀렸다`이고, 객체로 온 것은 자리가 `invalid_tool_calls.0.args`다(`guard_candidate_args_not_object`, `guard_candidate_args_object_value`. 글은 108 사례 실행의 저장한 출력에서 손으로 봤다, 윗줄과 같은 Grep). 도구 이름은 글에 없다.
- **읽는 단계를 지나고 모델을 만들다 거부되는 주소.** 꼴이 이상한 주소 열과 보통 주소 하나를 sdk의 `HttpServer`(원격 MCP 서버의 `url`에 거는 검사)와 후보의 만들기에 차례로 넣었다(`build_rejects_address`). 검사를 지났는데 만들다 `httpx2.InvalidURL`로 끝난 것이 넷이다. 개행이 든 주소와 탭이 든 주소(글은 `Invalid non-printable ASCII character in URL, '\n' at position 24.` 꼴), 포트가 숫자가 아닌 주소(글은 `Invalid port: 'odd-part-3c7e'`로 주소의 그 조각을 되울리고 `__context__`에 `ValueError`가 달린다), 경로가 7만 자인 주소(글은 `URL too long`)다. 검사도 만들기도 지난 것은 넷이다. 경로에 공백이 든 주소, 포트가 99999인 주소, 호스트가 한글인 주소, 호스트에 빈 마디가 든 주소(`a..b`)다. 표지는 보통 주소가 검사를 지나고 만들어진 것(만들기가 도는 양성 대조)과 사용자 정보가 든 주소와 닫지 않은 대괄호 주소가 검사에서 거부된 것(검사가 실제로 돈 음성 대조)이다. 만들기는 네트워크에 닿지 않는다. 넣은 열하나만 봤다. 라이브러리가 거부하는 꼴의 전부가 아니고, 만들어진 넷 가운데 부를 때 어떻게 끝나는지 본 것은 경로에 공백이 든 꼴뿐이다(다음 항목). 후보는 그 예외를 바꾸지 않는다(무엇으로 바꿀지는 명세가 정한다).
- **이상한 주소가 예외 글에 실리는 꼴.** 경로에 공백, 한글, 유니코드 줄 구분 문자(U+2028)가 든 주소로 401을 받으면 서버가 받은 요청 줄은 `/v1/odd-part-3c7e%20%ED%95%9C%E2%80%A8%EA%B8%80/chat/completions`이고(라이브러리가 퍼센트 인코딩했다), 후보의 예외 글에는 주소가 모델 파일에 적은 글자 그대로 실리되 줄 구분 문자는 날것이 아니라 이스케이프한 꼴로 실린다(`guard_candidate_odd_url_401`). ASCII 제어 문자가 든 주소의 이스케이프는 호출로 보지 못한다. 그런 주소는 윗 항목대로 만들기에서 먼저 거부된다.
- **키 변수가 없을 때.** 모델은 키 없이도 만들어지고, 호출하면 요청 0건으로 `RuntimeError("모델 서버의 키를 읽을 환경 변수 PROBE_MODEL_KEY 가 없다")`가 닿는다. 사슬이 없다(`guard_candidate_missing_key`). 키는 호출 때 읽는다. 환경의 값을 바꾸면 다음 요청의 헤더가 바뀌고, 만든 뒤 변수를 지우면 같은 예외다(`guard_candidate_key_rotation`).
- **실을 수 없는 키.** 개행, 끝 공백, ASCII 아닌 글자가 든 값은 요청 0건으로 `RuntimeError("환경 변수 PROBE_MODEL_KEY 의 값에 인증 헤더로 보낼 수 없는 글자가 있다")`다. 값이 글에 없고 재시도로 1초를 쓰지 않는다(`guard_candidate_bad_key_newline`, `…_unicode`, `…_trailing_space`. 질문 4의 같은 값과 견준다).
- **키 변수를 적지 않은 모델.** `Authorization: Bearer no-key`가 간다(`guard_candidate_no_key_variable`). 자리 채움 글자를 두는 것은 SDK가 키 없이는 클라이언트를 만들지 않아서다(읽었다, openai 3.49.0의 `lib/_client_auth.py`가 `Missing credentials…`로 거절한다. 사례는 없다).
- **성공하는 길은 그대로다.** 도구 호출이 `reply_from`까지 같은 모양으로 읽히고, `max_tokens`와 `temperature`는 주지 않으면 본문에 없고 주면 `max_completion_tokens`와 `temperature`로 실린다(`guard_candidate_success`).
- **취소는 받지 않는다.** 1.5초 뒤에 답하는 서버를 0.5초 기한(`anyio.move_on_after`)으로 감싸면 기한의 `cancelled_caught`가 참이고 후보가 취소를 다른 예외로 바꾸지 않는다(`guard_candidate_cancelled`).
- **pyright strict와 타입 우회.** `check_adapter_types.py`의 다섯 회차가 모두 측정이었다. 설정은 `typeCheckingMode = "strict"`, pyright 1.1.414가 두 파일을 분석했고(`filesAnalyzed` 2), 양성 대조의 기대 여덟 쌍이 모두 났고 기대 밖의 진단이 없었고, 후보의 진단은 0개, 타입 우회는 0개였다(쟀다, `probes/check_adapter_types.py`). `_agenerate`의 재정의는 `**kwargs: object`로 받아 `Any` 없이 지난다.

후보의 한계 셋.

- **가리는 것은 키 값뿐이다.** 찾는 값은 호출을 시작하며 읽어 둔 값과 예외를 바꾸는 때의 환경 값 둘이다. 호출 도중에 환경의 값이 바뀐 뒤 서버가 옛 키를 되울리는 갈래는 사례가 없다(둘 가운데 앞의 값이 그 갈래를 받는다고 본다. 어림). 주소에 사용자 정보가 있으면 키 대신 Basic 값이 가고, 서버가 그것을 되울린 글은 가려지지 않는다. 주소를 글자 그대로 싣기 때문에 암호 글자도 글에 실린다(`guard_candidate_userinfo_401`. 암호 글자와 base64 꼴이 둘 다 글에 있다). 쿼리도 같다(후보에 쿼리가 든 주소를 넣은 `logs_401_query_url`의 예외 글에 `…/v1?probe_token=query-secret-4b9d`가 실렸다. 108 사례 실행의 저장한 출력에서 손으로 봤다, 위와 같은 Grep). 사용자 정보와 쿼리가 든 주소는 모델 파일을 읽을 때 거절해야 막힌다. 서버가 키를 바꿔(잘라서, 인코딩해서) 되울리는 것도 놓친다(사례가 없다. 글자 그대로 찾아 바꾸는 코드라서 그렇다).
- **환경의 헤더 변수 넷과 `HTTP_PROXY`는 막지 못한다.** 질문 2의 `OPENAI_ORG_ID`, `OPENAI_ORGANIZATION`, `OPENAI_PROJECT_ID`, `OPENAI_CUSTOM_HEADERS`, 그리고 프록시.
- **호출마다 연결을 새로 맺는다.** 모델마다 준 클라이언트가 쉬는 연결을 두지 않아서다(질문 10). 그 값(TLS 주소에서 호출마다 드는 악수의 시간)은 재지 않았다. 가짜 서버는 평문 HTTP다.

### 8. DEBUG 로그 — `cases_logs.py`

루트 로거를 DEBUG로 두고 모든 레코드를 모았다. 성공 한 번에 17줄, 401 한 번에 20줄이다.

- `openai._base_client`(DEBUG): `Building HTTP request: method=POST retries_taken=0`, `Sending HTTP Request: POST`, `HTTP Response: POST 200`, `request_id: None`. 401에서는 `Encountered an HTTP status error: 401`, `Not retrying`, `Re-raising status error`가 더 난다.
- `httpcore2.connection`(DEBUG): `connect_tcp.started host='127.0.0.1' port=<포트> … timeout=None …`과 `connect_tcp.complete`.
- `httpcore2.http11`(DEBUG): 요청·응답의 단계 열 줄. 응답 헤더의 값(`Server`, `Date`, `Content-Type` 등)이 찍힌다. 요청 헤더의 값은 찍히지 않는다.
- `httpx2`(INFO): `HTTP Request: POST http://127.0.0.1:<포트>/v1/chat/completions "HTTP/1.1 200 OK"`.

키 값, `Bearer `라는 글자, 프롬프트는 어느 레코드에도 없었다. 보통 모델과 후보 모두, 성공과 401 모두 그렇다(`logs_success_plain`, `logs_success_candidate`, `logs_401_plain`, `logs_401_candidate`). 표지는 다섯이다. 찾는 글자를 심은 레코드를 탐지가 찾는다(탐지의 자기 시험), 서버가 그 키가 든 인증 헤더를 받았다, 서버가 받은 본문에 그 프롬프트가 있다, 호출이 고른 갈래대로 끝났다(성공 갈래는 메시지가 돌아왔고 401 갈래는 예외의 글이 그 코드를 든다), 쿼리 갈래는 서버가 받은 요청 줄에 그 쿼리가 있다. 주소가 `httpx2`의 줄에서 찾히는 것은 찾을 것이 있으면 찾는다는 양성 대조다(측정 여부의 조건에는 넣지 않았다). 주소 전체는 `httpx2`의 INFO 줄에 실린다. 쿼리가 든 주소면 쿼리까지 실린다(`logs_401_query_url`, 줄은 `…/v1/?probe_token=query-secret-4b9dchat/completions "HTTP/1.1 401 Unauthorized"`). INFO라서 DEBUG를 켜지 않아도 `httpx2` 로거가 INFO 이상이면 나온다(어림. 수준을 바꿔 가며 보지 않았다).

### 9. 응답 해석 — `cases_response.py`

- **`usage`.** `prompt_tokens` 11, `completion_tokens` 7, `total_tokens` 18이 `usage_metadata`의 `input_tokens` 11, `output_tokens` 7, `total_tokens` 18이 되고 `reply_from`도 11과 7을 읽는다(`response_usage_and_model`). `prompt_tokens_details.cached_tokens`는 `input_token_details.cache_read`로, `completion_tokens_details.reasoning_tokens`는 `output_token_details.reasoning`으로 든다(`response_usage_details`). `usage`가 없으면 `usage_metadata`가 `None`이고 `reply_from`은 0과 0을 읽는다(`response_without_usage_and_model`).
- **`model`.** 서버가 답한 `model`(`served-model-name`)이 `response_metadata["model_name"]`이 된다. 요청에 적은 이름(`requested-model-id`)이 아니다. 서버가 `model`을 주지 않으면 `model_name`이 `None`이고 `reply_from`은 `unknown`으로 읽는다. `response_metadata`의 키는 `token_usage`, `model_provider`(`openai`), `model_name`, `system_fingerprint`, `id`, `finish_reason`, `logprobs`다.
- **사고 글.** 메시지의 `reasoning_content`와 `reasoning` 칸은 버려진다. `text`와 `content`는 `pong`뿐이고 `additional_kwargs`에도 들지 않는다(`response_reasoning_content`). 사고 글을 `content` 안에 `<think>` 꼴로 섞어 보내는 서버는 넣어 보지 않았다. 그 글은 `text`에 그대로 남을 것이다(어림).

### 그 밖에 본 것 — `cases_request.py`

- **타임아웃과 재시도의 기본값.** 보통 모델과 후보 모두 SDK 클라이언트의 `max_retries`가 2, `timeout`이 `None`이다(`client_defaults`. 속성을 읽은 것이다). DEBUG 로그의 `connect_tcp.started … timeout=None`도 같은 값이다. 답하지 않는 서버에서 실제로 끝없이 기다리는지는 재지 않았다(긴 대기를 하지 않았다). 같은 사례에서 환경에 `OPENAI_PROXY`와 `LC_OUTPUT_VERSION`을 심으면 보통 모델의 `openai_proxy`와 `output_version`이 그 값이 되고, 후보는 둘 다 `None`이다.
- **같은 프로세스의 둘째 이벤트 루프.** 한 루프에서 부른 뒤 그 루프를 닫고 새 루프에서 같은 주소를 부르면 내장 `RuntimeError("Event loop is closed")`로 끝난다(`__context__`는 `AttributeError: 'NoneType' object has no attribute 'send'`. `two_loops_same_url`). 모델마다 제 클라이언트(`http_async_client=openai.DefaultAsyncHttpxClient()`)를 주면 둘째 루프도 된다(`two_loops_own_client`). 그래서 까닭은 주소별로 캐시해 나눠 쓰는 클라이언트다(캐시는 읽었다, langchain-openai 1.6.2의 `chat_models/_client_utils.py`, `_cached_async_httpx_client`). 후보도 97 사례 실행까지는 나눠 쓰는 클라이언트라 같은 실패가 `모델 서버 … 호출이 실패했다 (RuntimeError): Event loop is closed`로 닿았다. 모델마다 제 클라이언트를 주게 고친 뒤로는 둘째 루프도 된다(`two_loops_candidate`). `asyncio.run`을 시험마다 따로 도는 테스트와 한 프로세스에서 루프를 다시 만드는 실행 경로가 걸린다. Windows(Proactor 루프)에서만 봤다. 제 클라이언트를 준 모델의 연결이 언제 닫히는지는 질문 10이 본다.

### 10. 모델마다 준 HTTP 클라이언트가 놓일 때 — `cases_lifetime.py`

core는 실행을 준비할 때마다 모델을 만들고 실행이 끝나면 놓는다. 모델마다 준 클라이언트는 닫는 자리가 없으므로, 놓인 모델의 연결이 어떻게 되는지 봤다. 가짜 서버는 쉬는 연결을 스스로 닫지 않는다.

- **한 루프에서 실행이 이어질 때(`runs_in_one_loop`).** 한 루프에서 모델을 다섯 번 새로 만들어 한 번씩 부르고 놓은 뒤 1초를 기다려 서버 쪽의 연결을 셌다. 라이브러리 기본값 클라이언트(`openai.DefaultAsyncHttpxClient()`, 쉬는 연결을 풀에 남긴다)를 준 갈래는 연결 5개 가운데 닫힌 것이 0개였다. 양성 대조로 같은 갈래에서 놓기 전에 클라이언트를 닫으면 5개가 모두 닫혔다. 쉬는 연결을 두지 않는 클라이언트(`max_keepalive_connections=0`, 지금 후보)는 닫지 않고 놓아도 5개가 모두 닫혔다. 손대지 않은 `ChatOpenAI`(나눠 쓰는 클라이언트)는 연결 하나를 다섯 번 다시 써 연결 1개 가운데 닫힌 것이 0개였다. 그래서 기본값 클라이언트를 모델마다 주면 `serve`처럼 루프 하나가 오래 도는 프로세스에서 실행마다 쉬는 연결이 하나씩 남는다고 본다. 서버가 그 연결을 닫을 때까지다(어림. `serve`의 루프로 돌리지 않고 이 사례의 루프 하나에서 다섯 번만 봤다). 실제 모델 서버의 keep-alive 제한 시간이 그 연결을 닫는 갈래는 넣지 않았다.
- **누가 닫았는가.** 후보의 로그 사례가 97 사례 실행보다 두 줄 길어졌고(`logs_success_candidate`가 17줄에서 19줄. 두 출력을 견준 스크래치 스크립트로 손으로 봤다), 102 사례 실행의 저장한 출력에서 그 사례의 레코드에 `close.started`와 `close.complete`가 있었다(손으로 봤다, `grep -o -E 'close\.(started|complete)'`). 클라이언트 쪽이 닫은 것으로 본다(어림. 서버가 받은 요청 헤더의 `Connection` 값과 레코드의 로거 이름은 보지 않았다).
- **놓일 때 나는 것.** 기본값 클라이언트의 모델을 루프가 아직 돌 때 놓으면 unraisable 예외와 경고가 0건이다(`keepalive_released_inside_loop`). 놓기 직전 그 풀에 열린 연결이 1이었으니 정리할 것이 있었는데 아무것도 나지 않았다. 루프가 닫힌 뒤에 놓으면 `ResourceWarning: unclosed transport <_ProactorSocketTransport …>`가 1건 난다(`keepalive_released_after_loop_closed`). 후보의 모델은 루프가 닫힌 뒤에 놓아도 0건이다(`candidate_released_after_loop_closed`. 놓기 전에 서버가 받은 연결 1개가 이미 닫혀 있었다). 탐지의 자기 시험(`__del__`에서 예외와 경고를 내는 객체)은 세 사례 모두에서 잡혔다. `ResourceWarning`은 파이썬의 기본 필터가 숨기고, 저장소의 `pyproject.toml`의 `filterwarnings`는 `RuntimeWarning`과 unraisable 경고만 오류로 올린다(읽었다).
- **실패하거나 취소된 호출의 연결(`candidate_connections_after_failures`).** 후보의 모델을 세 번 새로 만들어 한 번씩 부르고 놓은 뒤 1초를 기다려 서버 쪽의 연결을 셌다. 401로 끝난 호출은 연결 3개 가운데 3개가, 500으로 끝난 호출은(재시도 두 번이 들어) 9개 가운데 9개가, 200에 JSON이 아닌 본문으로 끝난 호출은 3개 가운데 3개가, 1.5초 뒤에 답하는 서버를 0.5초 기한으로 끊은 호출은 3개 가운데 3개가 닫혔다. 대조로 기본값 클라이언트를 준 갈래의 401은 3개 가운데 닫힌 것이 0개였다(그 갈래에서 연결이 남는다는 것이 이 셈이 닫히지 않은 연결을 셀 수 있다는 표지다). 그래서 포트에 닫기를 두지 않아도 후보의 실패·취소한 호출이 연결을 남기지 않는다고 본다. 넣은 갈래 넷에서 본 것이다. 연결 도중에 끊기는 꼴(TLS 악수 중, 응답 본문을 읽는 중)은 넣지 않았다.
- **한 모델을 여러 번 부를 때(`calls_on_one_model`).** 모델 하나를 놓지 않고 네 번 부르면 후보는 연결 4개를 맺고, 넷째 호출이 끝나고 1초를 기다린 시점(모델을 아직 쥐고 있을 때)에 4개가 모두 닫혀 있었다. 호출이 끝난 바로 그 순간의 값은 재지 않았다. 대조인 기본값 클라이언트는 연결 1개를 네 번 다시 썼고 놓기 전에도 놓은 뒤에도 닫힌 것이 0개였다. 그래서 도구 호출로 모델을 여러 번 부르는 실행에서 후보는 호출 수만큼 연결을 맺고 그때그때 닫는다. 대가는 호출마다의 연결 수립이다(위 "후보의 한계").
- **재지 않은 것.** Linux의 이벤트 루프. 이 폴더의 값은 모두 Windows(Proactor 루프)의 것이다. 쉬는 연결을 두지 않는 것은 연결 풀의 설정이라 루프의 종류에 덜 기댈 것으로 본다(어림). 구현 티켓의 어댑터 시험이 CI의 리눅스에서 같은 연결 셈을 본다(명세의 Testing Decisions). (2026-11-12 셀프 리뷰: 이 절의 사례 아홉은 아래 12에서 리눅스 컨테이너로도 쟀다, `probes/linux_lifetime.sh`.)

### 11. 워크트리 밖 쓰기와 `.env` — `outside_worktree.py`

워크트리 세션(이 세션)에서 두 명령을 쳤다(쟀다, `probes/outside_worktree.py`). 음성 대조를 더한 뒤 한 번씩, "작업 폴더 밖"의 판정을 고친 뒤(위 "결과를 본 뒤 바꾼 것") 한 번씩 다시 쳤고, 그때마다 명령마다 두 회차(워크트리 밖 쓰기, 환경) 모두 측정이었다. 홈 아래 이 프로브만 쓰는 이름의 폴더에 파일을 쓰고 읽고 지웠고, 그 자리는 작업 폴더 밖이었다. `--env-file` 없이 친 명령의 환경에는 `ANTHROPIC_API_KEY`가 없었고(음성 대조), `--env-file`로 주 체크아웃의 `.env`를 넘긴 명령의 환경에는 있었다. 그래서 그 변수는 `--env-file`이 넘긴 것이다. `RUNPOD_API_KEY`는 넘긴 환경에도 없었다. 이 결과는 명령이 그날 훅과 데스크톱 앱의 가드를 지났다는 것까지다. 가드는 같은 모양의 명령에도 결과가 갈린 적이 있다(`CLAUDE.md` 환경 함정).

### 12. 리눅스의 이벤트 루프 — `linux_lifetime.sh` (2026-11-12 명세 검토와 셀프 리뷰)

위 10의 수명 사례 아홉을 Docker의 리눅스 컨테이너(이미지 `python:3.12.10-slim-bookworm`, WSL2 커널 6.18.58.1, glibc 2.36)에서 돌렸다. 판은 Windows의 실행과 같다(첫 줄의 판. langchain-openai 1.6.2, openai 3.49.0, langchain-core 1.6.3, httpx2 2.13.0). 명세 검토가 세션 스크래치패드의 같은 스크립트로 한 번 손으로 돌렸고, 셀프 리뷰가 그 스크립트를 이 폴더에 옮겨 "돌리는 법"의 명령으로 다시 돌려 사례마다 같은 결과 문구를 얻었다(쟀다, `probes/linux_lifetime.sh`. 측정 9회차, 측정 아님 0회차, 프로브의 종료 코드 0). 리눅스 컨테이너 하나에서 한 번씩 돈 값이고 CI의 ubuntu 러너에서는 돌리지 않았다.

- **후보는 Windows와 같다.** 놓인 모델 5개 중 5, 401 3개 중 3, 500 9개 중 9, JSON 아님 3개 중 3, 기한에 끊긴 호출 3개 중 3, 쥔 모델을 네 번 부른 뒤 놓기 전 4개 중 4가 닫혀 있었다. 루프가 닫힌 뒤에 놓아도 unraisable과 경고가 0건이고, 둘째 루프도 됐다.
- **대조인 기본값 클라이언트는 Windows와 다르다.** 놓인 모델 5개 중 5가 닫혔고(Windows 0), 401로 끝난 호출은 3개 중 2가 닫혔고(Windows 0), 쥔 모델은 놓기 전 1개 중 0(Windows와 같다), 놓은 뒤 1개 중 1(Windows 0)이었다. 루프가 돌 때 놓으면 경고가 1건이었다(Windows 0건). 그래서 놓인 모델의 셈은 리눅스에서 후보와 기본값을 가르지 못하고, 401의 셈은 하나 차이(3개 중 3과 3개 중 2)로만 갈렸다. 두 실행에서 모두 크게 가른 것은 쥔 모델의 놓기 전 셈이다(후보 4개 중 4, 기본값 1개 중 0). 기본값이 리눅스에서 놓은 뒤 닫히는 까닭(루프의 종류인지 쓰레기 수거의 때인지)은 가르는 갈래를 넣지 않아 모른다.
- **나눠 쓰는 클라이언트의 둘째 루프는 리눅스에서도 실패했다**(`two_loops_same_url`). 모델마다 클라이언트를 준 두 갈래는 둘째 루프도 됐다.

### 돌려 보지 못한 것

- 실제 모델 서버와 클라우드(지시대로 쓰지 않았다). `max_completion_tokens`라는 이름, `developer` 역할, `x-stainless-*` 헤더를 실제 모델 서버가 받는지. 쿼리가 든 주소로 깨진 요청 줄(질문 1)을 실제 모델 서버가 어떻게 받는지.
- Linux. 닫힌 포트의 시간과 수명 사례 밖의 사례는 모두 Windows의 값이다. 둘째 루프의 실패와 연결의 셈(질문 10)은 12에서 리눅스 컨테이너로도 쟀다(2026-11-12 셀프 리뷰, `probes/linux_lifetime.sh`).
- 만들기에서 난 예외를 어댑터가 바꾸는 것. 후보는 바꾸지 않고, 읽는 단계의 검사에 명세가 더하는 쿼리 거부도 여기서는 돌려 보지 않았다(sdk에 아직 없는 규칙이다).
- 수백 초의 타임아웃(지시대로 하지 않았다).
- 스트리밍 콜백이 붙은 `ainvoke`, `content` 안의 `<think>` 글, 서버가 키를 바꿔 되울리는 것, 호출 도중에 환경의 키 값이 바뀐 뒤 되울린 옛 키. 위에 어림이나 읽은 것으로 적었다.
- 응답 헤더에 비밀을 싣는 서버(받은 키를 헤더로 되울리는 서버, `Set-Cookie`를 주는 게이트웨이). 응답 헤더의 값이 DEBUG 로그에 찍힌다는 것(질문 8)에서 그 값도 찍힐 것으로 본다(어림).
- 위임 래퍼(둘째 안). 첫째 안이 서서 짓지 않았다.
- 환경의 헤더 변수 넷과 `HTTP_PROXY`를 막는 길.
- TLS 주소에서 호출마다 연결을 새로 맺는 값, 실제 서버의 keep-alive 제한 시간이 쉬는 연결을 닫는 갈래(질문 10).
