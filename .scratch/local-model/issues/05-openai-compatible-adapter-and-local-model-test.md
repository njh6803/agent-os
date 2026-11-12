# 05: 모델 서버 어댑터와 로컬 모델 시험 — `openai-compatible` 모델이 모델 서버에 실제로 붙고, 병합 전에 두 로컬 모델로 calc를 돌린다

**What to build:** 운영자가 모델 파일에 적은 `openai-compatible`과 `base_url`로 실행이 그 주소의 Chat Completions에 붙어 돈다(스토리 1·2·17). 키 값은 호출 직전에 `api_key_env`의 변수에서 읽어 요청에만 싣고, `api_key_env`가 없으면 자리 채움 글자를 보내며, 환경의 `OPENAI_API_KEY`는 모델 서버로 가지 않는다(스토리 4·5·6). 키 변수를 빠뜨리면 실패 내용이 변수의 이름만 들고(스토리 7), 꺼진 서버와 틀린 키는 실패 내용만으로 갈리며(스토리 8), 서버가 키를 되울려도 실패 내용과 트레이스와 DEBUG 로그에 키 값이 남지 않는다(스토리 9·18). `max_tokens`와 `temperature`를 적지 않으면 서버의 기본값이 쓰인다(스토리 15). 최종 사용자는 지금과 같은 고정 문구를 본다(스토리 16). 이 저장소를 고치는 세션에게는 GPU 없이 도는 평소의 pytest에서 calc 예시가 가짜 모델 서버를 모델로 삼아 도구를 쓰고 트레이스를 남기는 시험이 생기고(스토리 19), `-m llm_local`이 같은 calc를 실제 모델 둘로 돌린다(스토리 20). 01이 둔 임시 거부 문구는 사라진다. 이 티켓의 PR은 03의 명령으로 로컬 모델 시험을 두 모델 모두 통과해야 병합한다.

이 기능의 중심 티켓이다. 어댑터, 의존 선언, 가짜 모델 서버를 쓰는 시험, 로컬 모델 시험과 마커, 규약 문서가 티켓 하나, PR 하나에 든다. ADR 0058 결정 "첫 적용"이 어댑터와 로컬 모델 시험을 같은 PR에 묶고 그 PR이 두 모델로 통과해야 병합하게 했기 때문이다. 명세의 묶음 D 가운데 먼저 병합해도 초록인 모듈 나눔(01)과 가짜 모델 서버(04)는 떼어 냈다(to-tickets에서 사용자가 여섯 장 분할을 골랐다). 어댑터는 프로브의 `adapter_candidate.py`를 옮기지 않고 거기서 본 모양을 근거로 새로 짓는다. 알려진 한계(모델 이름의 머리, 환경의 헤더 변수 넷, 되울린 키의 한계, 응답 헤더의 DEBUG 로그)는 모델 서버 모듈의 독스트링이 원천이다.

근거는 `.scratch/local-model/spec.md`의 "모델 소스와 모듈"의 "모델을 만들다 거부되는 주소", "요청", "HTTP 클라이언트"와 그 2026-11-12 주석, "키", "실패 문구와 되울린 키", "로그", "의존", "로컬 모델 시험"과 그 주석, "규약 문서"와 그 주석, "고칠 자리의 묶음"의 D 줄과 그 주석, Testing Decisions의 어댑터(D)·CLI(D)·로컬 모델 시험(D) 사례와 그 주석이다. 측정은 `.scratch/local-model/probes/openai_compat.py`(사례 108, 명세가 사례 이름을 함께 든다), `check_adapter_types.py`, `make_env.py`, 리눅스 컨테이너로 수명 사례를 돈 `linux_lifetime.sh`와 그 `README.md`이고 다시 돌리지 않는다. 앞선 결정은 ADR 0057 전부(2026-11-12 이력 "모델 이름의 머리에 따라 라이브러리가 요청을 바꾸는 것을 알려진 한계로 둔다"를 포함한다)와 ADR 0058의 결정 "시험은 두 층이다"부터 "지키게 하는 수단"까지, Consequences "규약이 서는 때"다. 원인을 잇지 않고 되울린 값을 가리는 선례는 MCP 어댑터다(`.claude/rules/adapters.md`, `adapters/mcp.py`의 `_where`).

**Blocked by:** 01(계약과 모델 소스의 모듈 나눔. 이 티켓이 임시 갈래를 실제 어댑터로 바꾼다), 02(인자가 깨진 도구 호출. CLI 시험의 한 사례가 그 실패를 본다), 03(모델 서버를 띄우는 명령. 병합 전에 이 명령으로 로컬 모델 시험을 돌리고, 시험이 그 환경 변수 이름의 상수를 import한다), 04(가짜 모델 서버. 어댑터 시험과 CLI 시험이 붙는다)

**Status:** ready-for-agent

### 모델 서버 모듈: 만들기와 요청

- [ ] 모델 서버 모듈은 `adapters/openai_compatible.py`이고, 01의 모델 소스가 `openai-compatible` 갈래에서 이 모듈에게 모델을 만들게 한다. 01의 임시 문구(`… 에 붙는 어댑터가 아직 없다`)를 지우고 코드와 rules(`src`, `tests`, `.claude/rules`)에서 그 문구가 0건인 것을 grep으로 본다. 명세와 티켓과 일지는 그 갈래를 적은 기록이라 문구가 남는다
- [ ] `ChatOpenAI`의 하위 클래스로 모델을 만들고 생성자에 모두 이름으로 넘긴다. 매니페스트에서 `model`(`model_id`), `base_url`, `max_completion_tokens`(`max_tokens`, 없으면 없음), `temperature`(없으면 없음. 키를 빼지 않고 언제나 이름으로 넘긴다)이고, 어댑터가 짓는 `api_key`(아래 키 함수)와 `http_async_client`(아래 클라이언트)다. 고정하는 넷은 `use_responses_api=False`, `disable_streaming=True`, `openai_proxy=None`, `output_version=None`이다
- [ ] 모델을 만들 때마다 그 모델만 쓰는 클라이언트를 새로 만들어 넘긴다. `openai.DefaultAsyncHttpxClient`에 `httpx2.Limits(max_connections=1000, max_keepalive_connections=0)`을 준 것이다. 포트에 닫기를 더하지 않는다
- [ ] 모델 만들기는 키도 네트워크도 요구하지 않는다. 모델을 만드는 자리에서 난 예외는 종류를 가리지 않고 `PluginError("model 플러그인 <이름> 의 base_url 로 모델을 만들 수 없다 (<예외 종류의 이름>)")`로 바꾸고 라이브러리의 글은 싣지 않는다. 다른 실행 전 구성 오류처럼 트레이스가 남지 않는다
- [ ] 모듈 독스트링이 알려진 한계 넷(모델 이름의 머리가 요청을 바꾼다, 환경의 `OPENAI_ORG_ID`·`OPENAI_ORGANIZATION`·`OPENAI_PROJECT_ID`·`OPENAI_CUSTOM_HEADERS`가 서버로 간다, 잘라 내거나 인코딩해 되울린 키는 가리지 못한다, 응답 헤더의 값이 DEBUG 로그에 찍힌다)과 그 근거를 적는다

### 키와 실패 문구

- [ ] `api_key`에는 키를 읽는 함수 객체를 넘긴다. 함수는 환경을 읽기만 하고 셋을 돌려주거나 던진다. `api_key_env`가 없으면 `no-key`, 변수가 없거나 값이 비었으면 `RuntimeError("모델 서버의 키를 읽을 환경 변수 <이름> 가 없다")`, 값에 인증 헤더로 보낼 수 없는 글자가 있으면(보이는 ASCII가 아니거나 공백이 앞뒤에 있다) `RuntimeError("환경 변수 <이름> 의 값에 인증 헤더로 보낼 수 없는 글자가 있다")`다. 앞뒤 공백을 떼어 보내지 않는다
- [ ] 하위 클래스가 `_agenerate`와 `_generate`를 재정의해 감싼다. `**kwargs: object`로 받아 타입 우회 없이 pyright strict를 지난다. 감싼 메서드는 라이브러리를 부르기 전에 키 함수를 한 번 먼저 불러 그 값을 쥐고, 위 두 실패를 그 문구 그대로 core에 낸다
- [ ] `Exception` 전부를 받고 `CancelledError`는 받지 않는다. 바꾼 예외는 `except` 블록 밖에서 던져 `__cause__`도 `__context__`도 없고 타입은 내장이다
- [ ] 문구는 넷이다. 상태 오류는 `RuntimeError("모델 서버 <주소> 가 요청을 거절했다 (HTTP <코드>): <글>")`, 연결 오류(시간 초과 포함)는 `ConnectionError("모델 서버 <주소> 에 닿지 못했다: <글>")`이고 원인 사슬의 글을 덧붙이지 않는다, 검증 예외는 `RuntimeError("모델 서버 <주소> 의 응답을 읽지 못했다: <자리> 의 꼴이 틀렸다")`이고 글과 도구 이름을 싣지 않는다, 그 밖은 `RuntimeError("모델 서버 <주소> 호출이 실패했다 (<원래 예외의 종류 이름>): <글>")`다. `<주소>`는 모델 파일의 `base_url`을 글자 그대로 싣고 찍히지 않는 글자만 이스케이프한다. `<글>`은 원래 예외의 `str`에서 키 값 둘(먼저 읽어 쥔 값과 예외를 바꾸는 때의 환경 값)을 글자 그대로 찾아 `***`로 바꾼 것이다. 한 호출 안에서 환경의 값이 두 번 이상 바뀌면 가운데 값을 놓칠 수 있다(명세 "실패 문구와 되울린 키"의 "되울린 키의 한계", 재지 않았다)

### 의존

- [ ] `langchain-openai`와 `openai`를 런타임 직접 의존으로 선언하고 판의 묶음을 `uv lock`으로 풀어 본 뒤 정한다. 명세는 저장소 락 위에 `langchain-openai==1.6.2`를 얹어 새로 드는 패키지가 넷이고 판이 바뀌는 패키지가 없음을 쟀다(`make_env.py`). 풀어 본 결과가 다르면 이 티켓이 까닭을 적는다
- [ ] import-linter의 금지 목록 둘("core knows no provider", "sdk knows no engine")에 `langchain_openai`와 `openai`를 더한다
- [ ] `docs/constitution/tech.md` 런타임 의존성 행의 "local-model의 구현 티켓이 선언하고 … 그때까지 `pyproject.toml`에는 없다"를 들인 사실로 고치고 헌법 판을 올린다

### 어댑터 시험

- [ ] 어댑터 시험은 04의 가짜 모델 서버에 붙어 명세 Testing Decisions의 어댑터(D) 사례를 모두 덮는다. 만들기(키 변수가 없어도, 서버가 꺼져 있어도 만들어진다, 두 제공사에 같은 거부, 제공사로 가르기, 부를 때마다 새 객체, 개행이 든 주소와 포트가 숫자가 아닌 주소의 `PluginError`가 플러그인 이름과 예외 종류의 이름을 들고 주소의 글자를 싣지 않는다), 요청(경로, 본문의 키 넷과 빠지는 키, 도구의 모양, 상한과 온도가 없을 때와 있을 때, 인증 헤더의 키, 자리 채움 글자, 환경에 심은 `OPENAI_API_KEY`·`OPENAI_BASE_URL`·`OPENAI_PROXY`·`LC_OUTPUT_VERSION`이 요청을 바꾸지 않는 것), 응답(글, 도구 호출, 토큰 수, 응답의 모델 이름과 없을 때의 `unknown`, 깨진 인자가 예외 없이 `invalid_tool_calls`에 그 도구 이름으로 드는 것), 실패(위 문구 넷과 키 함수의 실패, 401에 되울린 키가 `***`로 바뀐 것, 요청을 받은 뒤 환경의 키를 바꾸고 옛 키를 되울린 401에서 옛 키도 새 키도 없는 것, 모든 실패에서 `__cause__`와 `__context__`가 없고 내장 타입인 것, 문구의 주소가 경로까지 글자 그대로인 것)다. 꺼진 서버와 500은 재시도로 몇 초가 걸려(닫힌 포트 7.3~7.5초를 쟀다) 사례 수를 줄여 둔다
- [ ] 수명과 취소 사례. 환경의 키를 바꾸면 다음 요청의 헤더가 바뀐다. 한 루프에서 모델 다섯을 만들어 부르고 놓은 뒤, 401로 끝난 호출과 기한에 끊긴 호출 뒤에 가짜 모델 서버의 연결이 모두 닫혀 있다. 실행 기한(`anyio.move_on_after`)이 답을 기다리는 호출을 끊고 취소가 다른 예외로 바뀌지 않는다
- [ ] 모델 하나를 쥔 채 여러 번 부른 뒤 놓기 전에 연결이 모두 닫혀 있는 사례를 둔다. 리눅스에서는 기본값 클라이언트도 놓으면 연결을 닫아(쟀다, `.scratch/local-model/probes/linux_lifetime.sh`, 그 `README.md`의 12) 놓인 모델의 셈은 윈도에서만 퇴행을 가른다. 두 OS에서 크게 가른 것은 이 사례다(후보는 4개 중 4, 기본값은 1개 중 0). 이 사례가 CI의 리눅스 러너에서도 초록인 것을 PR의 CI로 본다
- [ ] 한 프로세스에서 `asyncio.run`을 두 번 돌려 같은 주소를 불러도 되는 사례는 동기 시험 함수(`def`) 안에서 부르고, 시험의 독스트링이 까닭(이벤트 루프 둘을 차례로 여닫는 것 자체를 재므로 pytest-asyncio의 루프를 쓸 수 없다)을 적는다. `.claude/rules/tests.md`의 "`asyncio.run()`을 직접 부르지 않는다"의 예외다
- [ ] 로그의 수락 시험. 키를 적은 모델로 가짜 모델 서버를 부르며 루트 로거를 DEBUG로 켜고 모은 모든 레코드의 메시지와 인자에 키 값이 없다. 갈래는 성공과 401(서버가 키를 되울린다)이고, 가짜 모델 서버가 그 키를 받았다는 것과 레코드에 `httpx2`의 요청 줄이 있다는 것을 함께 단언한다. 로그 필터는 두지 않는다

### CLI 시험

- [ ] calc의 평소 시험. `tests/test_main.py`의 실제 모델 calc 시험과 같은 모양으로 플러그인을 임시 루트에 복사하고, 가짜 모델 서버를 가리키는 `openai-compatible` 모델 파일을 적어 `--model`로 준다. calc의 MCP 서버는 같은 파일이 쓰는 stdio 픽스처(`tests/adapters/mcp_fixture_server.py`)로 바꾸고 `_replace_in`의 선례를 따른다. 가짜 모델 서버의 응답은 `add` 호출과 그 결과를 든 글의 답 둘이다. 단언은 종료 코드 0, 출력의 계산 결과, 트레이스의 마지막 `run_finished`, `llm_called` 둘과 성공한 `tool_called`(인자와 결과), 가짜 모델 서버가 받은 첫 요청에 `tools`가 있다는 것이다. 기본 pytest와 CI에서 돈다
- [ ] 인자가 깨진 도구 호출의 CLI 시험. 위와 같은 모양에서 첫 응답의 `add` 호출 인자만 깨진 JSON으로 바꾼다. 종료 코드가 0이 아니고, 트레이스의 마지막이 원인 `model_call`의 `run_failed`이며, 그 메시지가 `add`를 들고 깨진 인자의 글자를 싣지 않고, `tool_called`가 없다

### 로컬 모델 시험

- [ ] 마커 `llm_local`을 `pyproject.toml`의 마커 선언과 기본 실행의 제외(`addopts`)에 더하고, `tests/conftest.py`의 실제 모델 마커 목록(`_LLM_MARKERS`)에 더해 실행 끝에 토큰 합계가 찍히게 한다
- [ ] 시험은 시험 파일 하나에 모은다. calc를 CLI 프로세스로 돌리는 사례 하나를 두 모델로 매개변수화한 것이고 선례는 `tests/test_main.py`의 `test_calc_에이전트가_실제_모델로_답하고_트레이스에_모델_호출이_남는다`다. 저장소의 플러그인을 임시 루트에 복사하고 `openai-compatible` 모델 파일 하나(`base_url`과 `model_id`는 환경 변수에서, `temperature = 0`, `max_tokens`는 적지 않음, 키 변수가 환경에 있으면 `api_key_env`에 그 이름)를 적어 `--model`로 준다. calc의 MCP 서버는 저장소의 `everything` 그대로다. 시험은 키 값을 읽지 않는다
- [ ] 환경 변수 여섯의 이름은 03의 `tools/llm_local.py` 상수를 import해 쓴다. 필수 넷(`_BASE_URL`, `_MODEL_ID`) 가운데 하나라도 없으면 skip이 아니라 실패하고 문구가 없는 변수의 이름을 든다. 그 환경 검사 함수를 마커 없이 부르는 사례를 기본 pytest에 둔다
- [ ] 단언은 `-m llm`의 calc 시험과 같고 두 군데만 다르다. `tool_called` 가운데 성공한 것(`ok`가 참)이 하나 이상 있어야 하고, `llm_called.model`은 `model_id`와 같은지가 아니라 비어 있지 않고 `unknown`이 아닌지를 본다. 시험 안에 다시 시도를 두지 않는다

### 규약 문서

- [ ] 가장 늦게 든 마커 `llm_portal`로 저장소를 grep해 자리를 다시 찾고 아래를 고친다. 에이전트가 읽는 문서(`CLAUDE.md`, rules, 스킬)를 고치기 전에 Skill 도구로 `writing-for-agents`를 부르고(`.claude/rules/agent-docs.md`), 고친 스킬과 rules는 새 세션에서 불러 본다(작업 규약 3)
- [ ] `docs/constitution/operations.md`의 LLM 테스트 절(헌법 판을 올린다). `-m llm_local`의 뜻과 명령, 병합 조건의 범위, 두 모델 모두와 한 번 실패하면 실패, 무효 회차(연달아 둘이면 세션이 멈춰 보고한다), 기록과 그 유효함의 판정, 워크트리에서 `.env`를 넘기는 꼴, 조건이 붙는 PR(개발 브랜치로 가는 티켓 PR과 운영 브랜치로 바로 가는 핫픽스 PR. 운영 브랜치로 가는 PR의 CI가 돌리는 LLM 테스트에는 `llm_local`이 들지 않는다), 제품 판을 내기 전에도 한 번 돌린다는 것과 그 절차는 pilot-release와 deploy-package가 정한다는 것이다
- [ ] `CLAUDE.md`의 검증 명령, `.claude/rules/tests.md`, `.claude/rules/http.md`, `.github/PULL_REQUEST_TEMPLATE.md`의 체크리스트, `.github/workflows/ci.yml`의 주석, `.coderabbit.yaml`, `tools/llm_tokens.py`와 그 시험, `tools/hook_env_read.py`의 문구, `tools/mutate.py`의 독스트링, `tests/test_main.py`와 `tests/test_calc_plugin.py`의 독스트링, `tests/test_conftest.py`, `web/apps/portal/playwright.config.ts`와 `web/packages/e2e-stack/src/plugins.ts`의 주석
- [ ] 카나리아 명세 셋(`.scratch/web-widget/probes/canary/claude_md_llm_widget.toml`, `tests_rule_llm_widget.toml`, `http_rule_llm_widget.toml`)은 위에서 고친 `CLAUDE.md`·`.claude/rules/tests.md`·`.claude/rules/http.md`의 문장을 기대 글자로 든다. `tools/canary.py --shape`는 원천 문서를 보지 않아 어긋나도 조용하므로, 그 문장을 바꾸면 기대 글자도 함께 고친다(선례는 pilot-portal 09, 그 toml의 머리 주석)
- [ ] `.claude/skills/next-session/merge.md`의 "병합 전". 범위에 드는 변경이면 로컬 모델 시험과 비용 확인의 단계를 밟고, 기록이 유효한지를 시험한 커밋과 브랜치 끝 사이의 차이로 가르며, "병합할지는 사용자에게 묻지 않는다"에 과금 확인의 예외를 적고, 병합 뒤 `sweep`을 친다
- [ ] `.claude/rules/adapters.md`의 모델 소스 항목(01이 쓴 임시 갈래를 모델 서버 어댑터의 동작으로), `.claude/rules/core.md`의 모델 포트 행, `README.md`와 `.env.example`의 모델 설명
- [ ] `docs/constitution/tech.md`의 시험용 모델 서버 행을 마커와 로컬 모델 시험까지 든 사실로 다시 고친다(03이 도구만 든 사실로 고쳐 두었다). 위 의존 행과 함께 헌법 판을 한 번 올린다
- [ ] 바꾼 결정이나 옛 표현을 저장소 전체에서 grep해 살아 있는 문서에 잔존이 0인지 본다(작업 규약 4). 옛 표현은 `.claude/rules/sdk.md`의 "값은 `anthropic` 하나"(01이 고친다), 임시 문구, `docs/constitution/tech.md`의 "그때까지 이 마커와 도구는 저장소에 없다"(03이 고친다)와 "그때까지 `pyproject.toml`에는 없다"다. grep은 원문 글자로 친다. 글자가 다른 말로 치면 늘 0건이라 잔존을 못 잡는다

### 병합 전

- [ ] 03의 명령으로 로컬 모델 시험을 돌린다. `--yes` 없이 친 예상 비용을 사용자에게 보여 확인받은 뒤 `--yes`로 다시 치고, 두 모델 모두 통과(종료 코드 0)해야 병합한다. 한 번 실패하면 실패이고 고친 뒤 처음부터 다시 돌린다. 무효 회차는 실패로 세지 않고 다시 띄울 때도 비용 확인을 받으며, 연달아 둘이면 멈춰 보고한다. 연달은 수는 일지와 03이 상태 폴더에 남긴 회차 파일로 센다. 끊긴 뒤 이어받은 세션도 그 둘로 센다
- [ ] 기록 묶음(시험한 커밋, 두 모델, 서빙 엔진의 판과 서버 옵션, GPU, 통과 수와 토큰 합계, 걸린 시간, 실제 단가, Terraform 출력에서 가린 것이 있었는지)과 무효 회차의 까닭을 명령이 끝난 그 턴에 일지에 옮기고 PR 코멘트에도 옮긴다. 옮기기 전에 끊겼으면 이어받은 세션이 상태 폴더의 회차 파일에서 옮긴다. 시험한 커밋 뒤에 범위에 드는 변경을 더 커밋했으면 그 기록은 유효하지 않아 다시 돌린다
- [ ] 병합 뒤 `sweep`을 친다

### 검증

- [ ] **빨강을 먼저 본다**(헌법 원칙 II). 첫 빨강은 어댑터 시험, CLI 시험 둘, 로컬 모델 시험의 환경 검사 사례다. 지금은 `openai-compatible` 모델이 01의 임시 문구로 끝난다
- [ ] **검증 명령이 모두 초록이다.** 손으로 치는 다섯에 더해 `-m llm`(모델 소스와 `tests/conftest.py`가 바뀐다)과 위 "병합 전"의 `-m llm_local`을 친다. `web/packages/e2e-stack`의 주석을 고치므로 질문 페이지 e2e(`pnpm -C web/apps/portal exec playwright test`)도 친다
