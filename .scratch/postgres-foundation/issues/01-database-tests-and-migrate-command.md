# 01: 커밋 때 테스트 데이터베이스가 저절로 뜨고, agent-os migrate가 표를 올린다

**What to build:** 개발 세션이 커밋하면 pre-commit의 러너가 테스트 컨테이너(PostgreSQL 하나, `127.0.0.1:25432`)가 답하는지 보고, 답하지 않으면 띄운 뒤 "테스트 컨테이너를 띄웠습니다" 한 줄을 찍는다(사용자 이야기 21). 데이터베이스를 쓰는 시험은 시험마다 깨끗한 데이터베이스를 받아 돌고, 여러 워크트리와 세션이 컨테이너 하나를 함께 써도 서로의 데이터베이스를 건드리지 않는다(사용자 이야기 23, 24, 25). 손으로 친 `uv run pytest`는 컨테이너가 없으면 띄우는 명령 한 줄과 함께 setup 오류(시험 본문에 들기 전 준비 단계에서 난 오류)로 실패하고, 건너뛰지 않는다(사용자 이야기 22). 새 명령 `agent-os migrate`는 `AGENT_OS_DATABASE_URL`이 가리키는 데이터베이스에 닿을 때까지 기다린 뒤 표의 판을 견주고 마지막 판까지 올린다. 이 변경의 제품 마이그레이션 폴더는 비어 있으므로, 빈 데이터베이스에 치면 "표가 이미 마지막 판(없음)입니다."와 0이다. `serve`는 아직 데이터베이스를 쓰지 않는다(03). CI의 `python` 잡은 같은 이미지를 service container(GitHub Actions가 잡 옆에 함께 띄우는 컨테이너)로 붙여 돈다(사용자 이야기 33의 첫 몫).

이 변경이 dev에 오르는 순간부터 모든 세션의 커밋이 Docker와 테스트 컨테이너를 요구한다. 그래서 띄우는 길(러너)과 그것을 알리는 문서(명세 "모두의 커밋")를 같은 커밋에 싣고, 헌법 판을 patch로 올린다(명세 "티켓을 나눌 때 함께 둘 것"의 첫째).

근거는 명세 `.scratch/postgres-foundation/spec.md`의 "연결 문자열과 비밀번호의 변수", "비밀번호에 드는 글자", "데이터베이스 포트와 조립"의 경계 검사 항목, "뜰 때의 확인과 다시 시도", "멈출 때의 글"(`migrate`의 몫과 시험 쪽 표), "표의 판을 견주는 자리", "마이그레이션 파일", "agent-os migrate", "테스트 컨테이너", "시험 데이터베이스의 이름과 도우미", "러너가 테스트 컨테이너를 띄우는 길", "CI", "저장소 상태 시험"의 첫째, "의존성과 타입", "모두의 커밋", Testing Decisions의 첫째와 셋째, Further Notes다. 결정은 ADR 0066이다. 측정과 시제품은 `.scratch/postgres-foundation/probes/`의 `stack/`(시제품 `proto/`), `clone_xdist/`다. 이 티켓의 "명세 검토"와 그 번호(B1, S3, N5 같은 것)는 일지 `docs/journal/2026-11-19-0050-postgres-foundation-tickets.md`의 "명세 검토" 절을 가리킨다.

이 티켓이 넷 가운데 가장 크다. 세션이 도중에 인계되면 아래 묶음 단위로 끊는다. 다만 데이터베이스를 쓰는 시험과 그것을 띄우는 길(테스트 컨테이너, 러너, CI, 모두의 커밋)은 한 커밋에 들어가야 한다.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

### 의존성과 경계

- [ ] 런타임 의존성에 `sqlalchemy[asyncio]`, `asyncpg`, `alembic` 셋을 더하고 `asyncpg-stubs`는 넣지 않는다. 판의 묶음은 이 티켓이 정한다. 우리 코드는 asyncpg를 import하지 않는다(명세 "뜰 때의 확인과 다시 시도"의 갈래 판정)
- [ ] `docs/constitution/tech.md`의 표에 셋을 더하고, 끝 문단을 ADR 0066을 가리키게 고친다(ADR 0066 Consequences "스택")
- [ ] `pyproject.toml`의 import-linter 계약 "core knows no filesystem or DB"의 금지 목록에 셋을 더하고, `agent_os.adapters` 밖의 `agent_os` 모듈이 셋을 import하지 못하게 하는 계약을 하나 더한다(명세 "데이터베이스 포트와 조립", 명세 검토 S6, 사용자 이야기 31). 어댑터 밖의 모듈 하나에 `import sqlalchemy`를 잠깐 넣어 `uv run lint-imports`가 새 계약으로 빨개지는 것을 한 번 보고 되돌린 결과를 일지에 적는다
- [ ] 스텁 없는 잠금에서 `uv run pyright`(strict)가 오류 0이고 `tools/check_type_escapes.py`가 우회 0이다(ADR 0066 Consequences "재지 않은 것"의 첫째를 실제 패키지로 다시 본다. 명세 "의존성과 타입")
- [ ] 설치한 alembic 판에서 "없는 판 폴더를 오류 없이 건너뛴다"를 소스로 다시 읽고 판과 줄 번호를 일지에 적는다. 명세 검토는 1.20.0의 `script/base.py` 135줄을 읽었다. 다르면 구현을 멈추고 명세 Testing Decisions 셋째의 마지막 사례로 돌아간다

### 어댑터와 agent-os migrate

- [ ] 연결 문자열은 `AGENT_OS_DATABASE_URL` 하나로만 받고 명령줄 인자를 두지 않는다. `postgresql://계정:비밀번호@호스트:포트/데이터베이스` 꼴만 받는다. 드라이버가 붙은 꼴, 다른 이름, 질의 문자열(`?` 뒤), `@`가 둘 이상인 주소, 읽을 때 `ValueError`가 나는 주소는 "읽지 못했다" 글과 1이고, 값을 되울리지 않는다(명세 "연결 문자열과 비밀번호의 변수", "비밀번호에 드는 글자")
- [ ] 실패를 명세의 갈래 다섯으로 가른다. 갈래는 예외와 원인 사슬의 오류 번호(SQLSTATE)와 `OSError` 여부로 가르고, 예외의 클래스로 가르지 않는다. 다시 시도는 30초, 시도 사이 1초, 첫 실패 뒤 알림 한 줄이다. 시도 하나(연결을 얻는 것부터 판을 다 읽는 것까지)를 통째로 5초의 제한 시간으로 감싼다. 드라이버의 접속 인자로만 걸지 않는다(명세 "뜰 때의 확인과 다시 시도")
- [ ] 연결 묶음은 `pool_pre_ping`(쉬던 연결을 쓰기 전에 살아 있는지 묻는 설정)을 켜고, 엔진은 `hide_parameters=True`로 짓는다(명세 "멈출 때의 글"의 "올리다 실패했다" 항목, 명세 검토 S10)
- [ ] 표의 판 견줌이 명세 "표의 판을 견주는 자리"대로다. 마이그레이션 파일이 하나도 없으면 마지막 번호는 없음이고, 그때 표가 없거나 줄이 없으면 맞다(명세 검토 S3)
- [ ] 마이그레이션 파일과 적용하는 코드는 `agent_os.adapters` 안 한 곳에 두고, `alembic.ini` 없이 설정을 코드로 짓는다. `env.py`는 어댑터가 연 연결을 받아 쓰고 스스로 이벤트 루프를 열지 않는다. 이 변경의 제품 폴더는 비어 git에 담기지 않을 수 있고, 폴더가 없어도 확인과 `migrate`가 빈 폴더와 같게 돈다(명세 "마이그레이션 파일", "티켓을 나눌 때 함께 둘 것")
- [ ] `agent-os migrate`는 인자가 없고, 명세 "agent-os migrate"대로 기다리고 견주고 올린다. 올리기 전체를 시제품과 같은 두 겹(어댑터의 `engine.begin()`과 alembic 환경이 그 연결에서 여는 트랜잭션)으로 감싼다. 플러그인, 트레이스, 토큰을 읽지 않는다
- [ ] `migrate`의 갈래를 `src/agent_os/main.py`가 OS 사용자와 모델을 확인하는 자리(143~149줄)보다 앞에 둔다. 셋째 이음매의 시험은 모델을 고르는 환경 변수 없이 부른다(명세 검토 N7)
- [ ] `main`이 어댑터를 짓는 자리는 함수 하나이고, 시험이 그 함수를 시험용 마이그레이션 폴더와 짧은 다시 시도 시간을 준 실제 어댑터로 갈아 끼운다. 주소를 읽는 일은 그 함수보다 앞에서 실제로 돈다. 그래서 변수가 없거나 읽지 못하는 사례는 갈아 끼운 어댑터에 닿기 전에 끝난다(명세 검토 S15)
- [ ] `migrate`가 찍는 글은 명세 "멈출 때의 글"의 표에서 `migrate`가 든 줄 전부이고, 시험이 글자까지 단언한다. "변수가 없거나 비었다" 글의 첫 줄은 03부터 참인 것을 알고 그대로 쓴다(같은 절)

### 테스트 컨테이너와 도우미

- [ ] 저장소 루트의 `compose.test.yaml`이 명세 "테스트 컨테이너"대로다. 프로젝트 이름 `agent-os-test`, 서비스 `postgres`, 컨테이너 `agent-os-test-postgres`, 같은 digest, 계정·비밀번호·데이터베이스 `agent_os`, `127.0.0.1:25432`, 데이터 폴더 tmpfs(디스크가 아니라 메모리에 두는 폴더), 디스크에 안전하게 쓰려고 기다리는 설정 셋을 끄는 서버 인자, `pg_isready -h 127.0.0.1 -U agent_os -d agent_os`의 상태 확인이다
- [ ] 데이터베이스를 쓰는 일은 `tools/database_for_tests.py`, pytest 픽스처는 `tests/database.py`다(명세 검토 N5가 이름을 바꿨다). 둘 다 `agent_os`를 import하지 않고, 패키지마다 다른 것(마이그레이션을 올리는 함수와 이름의 접두)은 그 패키지의 `conftest.py`가 인자로 넘긴다(명세 "시험 데이터베이스의 이름과 도우미")
- [ ] 이름은 `<접두>_template_<32자>`, `<접두>_test_<32자>`, `<접두>_e2e_<32자>`이고 agent_os의 접두는 `agent_os`다. 접두가 소문자·숫자·밑줄이 아니거나 21자를 넘으면 시험을 띄우기 전에 멈춘다
- [ ] 템플릿은 `loop_scope="session"`인 비동기 세션 범위 픽스처가 작업자마다 만들고 세션 끝에 지운다. 시험마다의 데이터베이스는 템플릿을 복제하고 끝나면 `DROP DATABASE … WITH (FORCE)`로 지운다. 관리 연결은 `NullPool`(연결을 모아 두지 않고 쓸 때마다 열고 닫는 설정)이다
- [ ] 템플릿을 거치지 않는 빈 데이터베이스 픽스처를 둔다. 이름과 지우는 때는 시험마다의 데이터베이스와 같다(명세 같은 절의 "빈 데이터베이스", 명세 검토 S5)
- [ ] 주소를 담는 값의 `repr`과 문자열에 비밀번호가 없다. `AGENT_OS_TEST_DATABASE_URL`에 질의 문자열이나 `@` 둘 이상이 들면 명세 "멈출 때의 글"의 시험 쪽 표의 셋째·넷째 줄로 멈추고 비밀번호의 조각이 글에 없다
- [ ] 서버가 답하지 않으면 주소를 고르는 세션 범위 픽스처가 `pytest.fail`로 실패하고, 그 픽스처를 받는 시험이 모두 시험 쪽 글로 setup 오류다(skip이 아니다. 원칙 II)
- [ ] 명령줄 입구 `create <접두>`는 템플릿을 거치지 않은 빈 데이터베이스를 `<접두>_e2e_…`로 만들고 주소를 한 줄로 찍는다. `drop <이름>`은 "이름"의 꼴에 맞는 이름만 받고, 맞지 않으면(`agent_os` 같은 이름) 아무것도 지우지 않고 1이다(명세 검토 S12). 둘 다 서버가 답하지 않으면 시험 쪽 글과 1이다. 이 입구를 처음 부르는 것은 03의 e2e-stack이다
- [ ] 로그인을 막은 계정(`NOLOGIN`)을 쓰는 사례는 무작위 이름으로 계정을 만들고 시험이 끝나면 지운다. 시험 프로세스가 죽어 남은 계정은 컨테이너를 다시 띄우면 사라진다(명세 검토 "확인하지 못한 것")

### 러너

- [ ] `tools/run_checks.py`가 pytest 검사를 띄우기 전에 명세 "러너가 테스트 컨테이너를 띄우는 길"대로 판정한다. 변수가 있으면 보지 않는다, 5초로 접속해 답하면 띄우지 않는다, 답하지 않으면 `docker compose -f compose.test.yaml up -d --wait --wait-timeout 60`을 180초 제한 안에서 치고 한 줄을 찍는다, 0이 아니면 같은 명령을 한 번만 더 치고 제한 시간을 넘긴 때는 다시 치지 않는다(명세 검토 S1), 띄우기가 실패해도 까닭 한 줄을 찍고 pytest 검사를 띄운다, 컨테이너를 내리지 않는다
- [ ] 그 판정은 Docker도 접속도 부르지 않는 함수로 떼어 `tests/tools/test_run_checks.py`에서 본다(`.claude/rules/tests.md`의 `tools/` 항목)
- [ ] 테스트 컨테이너를 내린 채 러너를 한 번 돌려 컨테이너가 뜨고 한 줄이 찍히는 것을 일지에 적는다
- [ ] 테스트 컨테이너를 내린 채 `uv run pytest -q`를 한 번 쳐서 시험 쪽 글로 setup 오류가 나고 skip이 없는 것을 일지에 적는다(기능 계획의 둘째 수락 조건, 명세 Testing Decisions 넷째의 끝)
- [ ] 러너에서 모든 시험이 끝난 뒤 멈추는 일이 보이면 pytest의 `--basetemp`부터 본다(명세 Further Notes "세션 끝의 멈춤")

### CI

- [ ] `.github/workflows/ci.yml`의 `python` 잡에 같은 digest의 PostgreSQL을 service container로 붙인다. 계정·비밀번호·데이터베이스 `agent_os`, 데이터 폴더 tmpfs, 러너의 5432, 잡의 환경 `AGENT_OS_TEST_DATABASE_URL`, 같은 상태 확인 명령이다(명세 "CI")
- [ ] 그 PR의 CI에서 템플릿 복제가 도는지, service container가 데이터 폴더의 tmpfs를 받는지를 보고 일지와 PR에 적는다(ADR 0066 Consequences "재지 않은 것", 명세 검토 "확인하지 못한 것"). 테스트 컨테이너가 끄는 속도 설정 셋을 service container에 넣을지는 그 PR의 CI 시간을 보고 정해 일지에 적는다
- [ ] 워크플로 감사(zizmor)가 초록이다

### 저장소 상태 시험

- [ ] PostgreSQL 이미지의 digest를 `compose.test.yaml`과 `ci.yml`의 PostgreSQL service container에서 읽어 모두 같은지 보는 시험을 둔다. 하나만 바꾸면 빨갛고, `ci.yml`에 PostgreSQL service container가 하나도 없어도 빨갛다. 셋째 자리(단독 compose)는 02가 더한다(명세 "저장소 상태 시험"의 첫째, 명세 검토 N8). 이 저장소가 지금 통과함을 재는 시험과 위반을 잡는 변이 시험을 하나씩 둔다(`.claude/rules/tests.md`의 `tools/` 항목과 같은 꼴)

### 모두의 커밋

- [ ] 테스트 컨테이너라는 전제와 띄우는 명령(`docker compose -f compose.test.yaml up -d --wait`)을 명세 "모두의 커밋"의 자리 여섯에 적는다. `docs/constitution/tech.md`의 테스트 줄, `docs/constitution/operations.md` 가드레일의 기계마다 까는 것, 같은 파일의 LLM 테스트 절(기본 `pytest -q`의 데이터베이스 시험이 컨테이너를 요구하고 마커 넷의 시험은 아직 데이터베이스를 쓰지 않는다), `README.md`의 시작 절, `.pre-commit-config.yaml` 머리의 준비 목록, `CLAUDE.md` 검증 명령의 테스트 줄(기본 실행이 컨테이너를 요구하고 러너는 스스로 띄운다)이다. 자리마다 이 변경이 오른 때 참인 것만 적고, `serve`를 띄우는 시험의 전제와 개발 PC의 `serve` 명령 셋은 03이 더한다(명세 검토 N3)
- [ ] `CLAUDE.md`를 고치기 전에 Skill 도구로 `writing-for-agents`를 부른다(`.claude/rules/agent-docs.md`)
- [ ] 헌법 판을 patch로 올린다. 판은 커밋 직전의 `tools/sibling_overlap.py`가 낸 형제의 가장 높은 판보다 높게 고른다(ADR 0038의 선례, `tools/check_constitution_version.py`가 본다)

### 시험(명세 Testing Decisions)

- [ ] 첫째 이음매(어댑터)의 사례가 모두 있다. 시험용 마이그레이션 폴더의 번호는 `9001`과 `9002`이고 빈 데이터베이스를 쓴다(명세 "마이그레이션 파일", 명세 검토 S5). 파일이 없는 폴더에서 빈 데이터베이스가 맞다는 사례를 더한다(명세 검토 S3)
- [ ] 셋째 이음매(`migrate` 명령)의 사례가 모두 있다. 실패하는 셋째 마이그레이션 `9003`은 표 하나를 만든 뒤 시험이 고른 표지 글자를 바인드 값으로 넘기는 문장이 데이터베이스에서 실패하게 짓는다. 실패는 서버와 드라이버의 글이 값을 싣지 않는 것(0으로 나누기 같은 것)으로 고른다. 형 변환 실패와 유일 제약 위반은 서버의 글이 값을 싣는다(명세 "멈출 때의 글"의 "올리다 실패했다" 항목). 역추적까지 든 표준 오류에 `[SQL parameters hidden due to hide_parameters=True]`가 있어 바인드 값을 넘긴 그 문장이 실패한 것을 보이고, `agent_os:agent_os@`도 표지 글자도 없다(명세 검토 S10, 명세 Testing Decisions 셋째)
- [ ] 제품 폴더로 빈 데이터베이스를 올리는 사례는 판 기록 표가 제품 폴더의 마지막 번호와 같은지(이 변경에서는 폴더가 비어 `migrate`가 alembic을 부르지 않으므로 표가 없거나 줄이 없는지) 본다. 번호를 글자로 적지 않는다(명세 검토 S4, S8)
- [ ] 선례는 시제품의 측정 `.scratch/postgres-foundation/probes/stack/run.py`의 `errors`, `versions`, `migrate` 섹션이다. 판에 기대는 측정(접속 실패의 꼴, 빈 첫 마이그레이션)이 설치한 판에서 명세와 다르면 구현을 멈추고 명세와 ADR 0066으로 돌아간다(명세 Further Notes "다시 잴 때")

### 검증

- [ ] CLAUDE.md의 검증 명령이 모두 초록이다
- [ ] `src/agent_os/adapters/`와 `main.py`를 고치므로 `-m llm`과 로컬 모델 시험(`tools/llm_local.py run`. `--yes` 없이 쳐 예상 비용을 사용자에게 보여 확인받은 뒤에만 `--yes`)의 병합 조건에 든다(`docs/constitution/operations.md` LLM 테스트)
