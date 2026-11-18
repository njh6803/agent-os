# 03: serve는 표의 판이 맞는 데이터베이스에 닿아야 뜬다

**What to build:** `serve`는 `AGENT_OS_DATABASE_URL`이 없거나 읽히지 않으면 지금 토큰이 빠졌을 때처럼 이유를 찍고 1로 멈춘다(사용자 이야기 38). 값이 있으면 앱의 수명이 열릴 때 데이터베이스에 닿는지와 표의 판을 확인하고, 닿지 않으면 30초 동안 다시 시도한다(사용자 이야기 8). 그래도 닿지 않거나, 비밀번호를 받아들이지 않거나(기다리지 않고 바로, 사용자 이야기 9), 표가 뒤처졌거나 더 새로우면 명세 "멈출 때의 글"의 그 갈래의 글(한 줄이거나 두 줄)을 찍고 3으로 멈추며, MCP 서버 같은 앱의 시작 일은 하나도 돌지 않는다(사용자 이야기 6, 7, 11, 39). 찍는 글에는 비밀번호가 없다(사용자 이야기 10). `/health`는 지금처럼 프로세스만 본다(사용자 이야기 19). 단독 compose에서 `serve`가 PostgreSQL에 닿는다(기능 계획의 첫째 수락 조건 가운데 "`serve`가 그 데이터베이스에 닿는다").

이 변경이 오른 뒤로는 데이터베이스 없이 `serve`가 뜨지 않는다. 그래서 `serve`를 띄우는 모든 시험이 같은 변경에서 데이터베이스를 얻는다. e2e-stack은 테스트 컨테이너에 자기 데이터베이스를 만들어 `migrate` 뒤에 `serve`를 띄우고(사용자 이야기 27), CI의 `llm`, `e2e`, `e2e-widget`, `e2e-portal` 잡이 service container를 붙인다(사용자 이야기 33의 나머지). 개발 PC에서 `serve`를 띄우는 세 명령이 README에 선다(사용자 이야기 26).

근거는 명세 `.scratch/postgres-foundation/spec.md`의 "데이터베이스 포트와 조립", "뜰 때의 확인과 다시 시도"(`serve`의 몫), "멈출 때의 글"(`serve`의 몫), "개발 PC에서 serve가 붙는 데이터베이스", "실제 serve를 띄우는 시험의 데이터베이스", "CI", "모두의 커밋"의 끝 문단, "의존성과 타입"(포트의 모양), Testing Decisions의 둘째, "티켓을 나눌 때 함께 둘 것"의 셋째다. 결정은 ADR 0066과 ADR 0062 결정 "경로와 층"이다. 측정과 시제품은 `.scratch/postgres-foundation/probes/stack/`(시제품 `proto/gate.py`, README "uvicorn의 실패 출력")이다. 이 티켓의 "명세 검토"와 그 번호는 일지 `docs/journal/2026-11-19-0050-postgres-foundation-tickets.md`의 "명세 검토" 절을 가리킨다.

이 기능의 마지막 티켓은 이것과 04다. 둘 가운데 늦게 병합하는 쪽이 같은 커밋에서 기능 계획에 `**끝:**` 줄을 적고 `uv run python tools/plan_table.py`를 돌리며, 기능 단락 `docs/release-notes/features/postgres-foundation.md`를 싣는다. 병합 직전에 `git fetch origin` 뒤 기준 브랜치를 합치고 저장소 상태 시험(`test_이_저장소의_…`)을 돌린다(`docs/agents/issue-tracker.md`의 "나란히 돈 마지막 티켓 둘").

이 티켓은 헌법(`docs/constitution/operations.md`)을 고치고 판을 올리지만 04를 막지 않는다. `docs/agents/issue-tracker.md`의 "계약(… 헌법)을 바꾸는 티켓은 그 기능의 첫 티켓이며 다른 티켓을 막는다"의 예외다. 고치는 문장은 `serve`가 데이터베이스를 요구하게 되는 때에야 참이라 이 변경에 실어야 하고(명세 "모두의 커밋"), 04는 그 문장도 헌법 판도 읽거나 고치지 않는다. 03과 04를 나란히 돌리는 것은 티켓을 나눌 때 사용자가 골랐다(일지 `docs/journal/2026-11-19-0050-postgres-foundation-tickets.md` "사용자에게 물은 것 하나").

**Blocked by:** 01, 02

**Status:** ready-for-agent

### 포트와 조립

- [ ] 포트 `Database`를 `agent_os.http`에 선언한다. 메서드는 비동기 `startup_problem()`(문제가 없으면 없음, 있으면 멈출 때의 글)과 `close()`다. 어댑터는 포트를 import하지 않고 시그니처로 만족한다(원칙 IV, ADR 0016). 포트는 SQLAlchemy의 타입을 주고받지 않는다
- [ ] 포트의 모양을 실제 패키지에서 다시 본다. 조립 자리에서 pyright가 어댑터를 포트와 맞대고, 메서드 하나를 일부러 어긋낸 어댑터가 `reportArgumentType`으로 걸리는 것을 한 번 보고 되돌린 결과를 일지에 적는다(명세 "의존성과 타입", 명세 검토 S2)
- [ ] `main`이 01의 함수로 어댑터를 지어 `create_app`에 넘기고, 다시 시도한다는 알림을 찍을 자리로 표준 오류를 함께 넘긴다. `create_app`의 새 인자는 기본값이 없다. 데이터베이스가 필요 없는 기존 시험은 가짜 데이터베이스를 넘긴다
- [ ] `tools/export_openapi.py`는 데이터베이스에도 불리면 곧바로 터지는 자리표시자를 넘기고, 계약 파일 `openapi.json`이 바뀌지 않는다
- [ ] 확인은 `create_app`이 더하는 순수 ASGI 미들웨어가 한다. 수명이 열리는 첫 메시지에서 앱의 시작 단계보다 먼저 `startup_problem()`을 부르고, 글이 오면 연결 묶음을 닫고 앱의 시작 단계를 부르지 않은 채 `lifespan.startup.failed`에 그 글을 싣는다. 예외가 오면 "확인하다 멈췄다" 글을 싣고 예외의 글과 역추적을 싣지 않는다. 닫기가 실패해도 `lifespan.startup.failed`를 보낸다. 수명이 끝날 때는 `lifespan.shutdown.complete`를 붙잡아 연결 묶음을 닫은 뒤에 넘기고, 닫다 실패하면 "닫다 실패했다" 글을 실어 `lifespan.shutdown.failed`를 보낸다(명세 "데이터베이스 포트와 조립"의 두 하위 항목)
- [ ] `serve`가 uvicorn에 `lifespan="on"`을 넘긴다
- [ ] `.claude/rules/http.md` 26줄이 적는 미들웨어의 차례에 확인 미들웨어를 더하고, 37줄의 예외에 "시작 단계"를 더해 넓힌다(사용자가 고른 넓힘, 명세 Testing Decisions 둘째). 고치기 전에 Skill 도구로 `writing-for-agents`를 부르고(`.claude/rules/agent-docs.md`), 고친 규칙은 새 세션에서 불러 본다(작업 규약 3, 명세 "티켓을 나눌 때 함께 둘 것")

### 구성 오류와 글

- [ ] 변수가 없거나 비면 "변수가 없거나 비었다" 글과 1, 읽지 못하면 "읽지 못했다" 글과 1이다. 01의 판정을 그대로 쓴다
- [ ] 뜰 때의 확인에서 멈춘 글은 명세 "멈출 때의 글"의 표에서 `serve`가 든 줄이고 종료 코드는 3이다. `serve`가 3을 1로 바꾸게 하지 않는다

### 실제 serve를 띄우는 시험

- [ ] e2e-stack(`web/packages/e2e-stack`)이 `serve`를 띄우기 전에 `tools/database_for_tests.py create agent_os`로 자기 데이터베이스를 만들고, 그 주소로 `agent-os migrate`를 돌린 뒤 같은 주소를 `AGENT_OS_DATABASE_URL`로 주어 `serve`를 띄운다. 부모의 환경에 같은 변수가 있어도 자기 값으로 덮는다. 정리할 때 `drop`으로 지운다. 테스트 컨테이너가 없으면 시험 쪽 글로 실패한다(명세 "실제 serve를 띄우는 시험의 데이터베이스")
- [ ] `-m llm`, `-m llm_widget`, `-m llm_portal`의 시험도 같은 길로 데이터베이스를 얻는다. pytest 쪽은 픽스처가, 위젯과 위젯 테스트 페이지의 e2e는 e2e-stack이 맡는다
- [ ] 단독 compose에서 `serve`가 실제 PostgreSQL에 닿아 뜨는 것을 이 PC의 단독 배포 e2e로 본다. 판 기록 표를 지운 데이터베이스나 모르는 번호를 넣은 데이터베이스로 `serve`만 다시 띄워, uvicorn이 두 줄 글을 역추적 없이 찍고 3으로 끝나는 것을 리눅스 컨테이너에서 한 번 보고 일지에 적는다(stack 프로브 README "재지 못한 것"의 둘째 항목. 그 항목은 uvicorn이 찍는 줄이 윈도의 것이라고 적고 리눅스 몫을 `restart_recover/`에 넘기는데, 그 프로브의 `serve`는 psql로 붙어 보는 대역이라(그 README의 대역 문구 절) 리눅스의 uvicorn 줄은 아직 아무도 보지 않았다)

### CI

- [ ] `.github/workflows/ci.yml`의 `llm`, `e2e`, `e2e-widget`, `e2e-portal` 잡에 01의 `python` 잡과 같은 service container와 `AGENT_OS_TEST_DATABASE_URL`을 붙인다. 01의 digest 시험은 `ci.yml`의 PostgreSQL service container를 수를 세지 않고 모두 읽으므로, 새로 붙인 넷의 digest도 고치지 않은 그 시험이 대 본다(명세 "저장소 상태 시험"의 첫째). 워크플로 감사(zizmor)가 초록이다

### 모두의 커밋의 나머지

- [ ] `docs/constitution/operations.md`의 LLM 테스트 절이 적은 문장을 `serve`를 띄우는 마커 셋(`llm`, `llm_widget`, `llm_portal`)까지 넓힌다
- [ ] `CLAUDE.md` 검증 명령의 괄호에 LLM 시험과 e2e를 손으로 칠 때 테스트 컨테이너가 떠 있어야 한다는 것을 더한다. 고치기 전에 Skill 도구로 `writing-for-agents`를 부른다
- [ ] `README.md`의 시작 절에 개발 PC의 세 명령(테스트 컨테이너 띄우기, 그 기본 데이터베이스 주소로 `agent-os migrate`, 같은 주소로 `agent-os serve`)과 컨테이너를 다시 띄우면 `migrate`부터 다시 친다는 것을 더한다(명세 "개발 PC에서 serve가 붙는 데이터베이스"). 그 세 명령을 이 PC에서 돌려 `serve`가 뜨는 것을 일지에 적는다
- [ ] 헌법 판을 patch로 올린다. 판은 커밋 직전의 `tools/sibling_overlap.py`가 낸 형제의 가장 높은 판보다 높게 고른다

### 시험(명세 Testing Decisions 둘째)

- [ ] 둘째 이음매의 사례가 모두 있다. `_main(["serve"])`을 부르고 `uvicorn_calls` 픽스처(`tests/test_main.py`)가 붙잡은 앱의 수명을 전체 ASGI 앱으로 직접 돌린다. 어댑터를 짓는 함수는 가짜 데이터베이스로 갈아 끼운다. 읽지 못하는 값 셋과 질의가 든 값에서 표준 오류에 `secret`, `leak`이 없다. `uvicorn_calls`가 붙잡은 인자에 `lifespan="on"`이 있다
- [ ] 실제 `serve` 프로세스를 띄우는 시험은 기본 실행에 더하지 않는다(사용자가 골랐다)

### 검증

- [ ] CLAUDE.md의 검증 명령이 모두 초록이다
- [ ] `main.py`와 `src/agent_os/adapters/`를 고치므로 `-m llm`과 로컬 모델 시험(`tools/llm_local.py run`. `--yes` 없이 쳐 예상 비용을 사용자에게 보여 확인받은 뒤에만 `--yes`)의 병합 조건에 든다(`docs/constitution/operations.md` LLM 테스트)
- [ ] `-m llm_widget`과 `-m llm_portal`도 로컬에서 친다. 리눅스 러너의 `llm` 잡은 main으로 가는 PR에서만 돌아, 다음 출시 PR이 처음 본다(명세 "티켓을 나눌 때 함께 둘 것", 명세 검토 S9)
- [ ] 서버의 시작과 e2e-stack을 고치므로 관리 화면 e2e, 위젯 e2e, 위젯 테스트 페이지 e2e, 단독 배포 e2e를 로컬에서 친다(CLAUDE.md 검증 명령의 web 괄호)
