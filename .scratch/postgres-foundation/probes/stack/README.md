# postgres-foundation stack 프로브

ADR 0066(`docs/adr/0066-agent-os-reaches-postgres-through-sqlalchemy-core-and-asyncpg-and-migrates-forward-only-before-serve.md`)이 명세와 첫 티켓에 넘긴 어림 가운데, 작은 시제품 하나로 잴 수 있는 것을 잰 프로브다. 시제품(`proto/`)은 명세가 정하려는 모양 그대로다. 포트 하나, 그 포트를 import하지 않는 어댑터 하나, 어댑터가 넘긴 연결 위에서만 도는 마이그레이션 환경, 표를 만들지 않는 첫 마이그레이션, 앱이 뜰 때 데이터베이스를 확인하는 자리 둘(순수 ASGI 미들웨어, FastAPI의 수명 함수)이다. 여기서는 결정하지 않고 본 것만 적는다. 결정은 명세(`.scratch/postgres-foundation/spec.md`)가 한다. 규약은 `docs/agents/issue-tracker.md`의 "프로브와 근거", 짓는 규칙은 `.claude/rules/probes.md`다.

결과는 2026-11-18에 명세의 셀프 리뷰를 반영한 뒤 `run.py`를 섹션 여덟 전부로 한 번 돌린 것이다(측정 67회차, 측정 아님 0회차, 종료 코드 0). 그 실행 전에 시제품의 글을 명세 "멈출 때의 글"의 표(첫 줄이 이유, 둘째 줄이 설명)에 맞추고, 회차를 셋 묶음 더했다. 접속을 허락하지 않는 거절(28000)의 회차 셋, 주소를 읽지 못한 것으로 보는 판정(`parse_url`)의 회차 열일곱, uvicorn이 둘째 줄을 따로 찍는지의 확인이다. 같은 날 앞서 돈 실행들(섹션 여덟 전부로 측정 43회차, `--sections types,versions`로 측정 13회차, 둘 다 측정 아님 0회차)의 값은 시간을 적을 때만 함께 든다.

근거의 종류는 넷이다. 프로브가 다시 낸다(`run.py`가 표지를 보고 센 회차), 손으로 봤다(명령과 함께 적는다), 코드를 읽었다(파일과 줄), 어림. 아래에서 따로 적지 않은 문장은 프로브가 다시 내는 것이다.

## 요약

1. 타입: asyncpg-stubs가 없는 환경에서, SQLAlchemy의 비동기 API와 alembic만 부르고 asyncpg는 import하지 않는 시제품이 pyright strict 오류 0, 타입 우회 0이다. 포트를 import하지 않는 어댑터가 조립 자리(`proto/assembly.py`)에서 포트와 맞대진다. 어긋난 어댑터 둘은 `reportArgumentType`으로 걸린다.
2. 빈 첫 마이그레이션: `upgrade`만 있고 `downgrade`가 없는, 표를 만들지 않는 마이그레이션 하나로 판 기록 표(`alembic_version`)가 생기고 줄 `0001`이 남는다. 다시 적용해도 그대로다.
3. 표의 판 견줌: 빈 데이터베이스와 아는 옛 번호는 "뒤처졌다"로, 묶음에 없는 번호는 "더 새롭다"로 갈린다. 더 새로운 표를 만난 `migrate`는 표를 건드리지 않는다. 판정 없이 alembic만 부르면 `alembic.util.exc.CommandError: Can't locate revision identified by '0002'`를 낸다. 마이그레이션 파일이 하나도 없는 폴더로는 빈 데이터베이스의 확인이 "문제 없음"이고, 올리면 줄 없는 `alembic_version` 표만 생긴다. 표를 만든 뒤 예외를 던지는 마이그레이션은 그 표까지 되돌려, 판 기록 표의 줄이 올리기 전의 `0001` 그대로 남는다.
4. 접속 실패의 꼴: 닿지 못한 것(거부, 이름 풀이 실패, 제한 시간)은 오류 번호 없는 `OSError` 계열로, PostgreSQL이 거절한 것은 오류 번호(SQLSTATE)가 달린 예외로 온다. 틀린 비밀번호는 28P01, 없는 데이터베이스는 3D000, 복구 중인 서버는 57P03이다. 로그인을 막은 계정(`NOLOGIN`)과 접속 규칙(`pg_hba.conf`)에 맞는 줄이 없는 접속은 둘 다 28000이다. 예외의 문구에 비밀번호는 실리지 않았다.
5. 다시 시도: 닿지 못한 것만 다시 시도하고 틀린 비밀번호와 28000은 바로 멈춘다. 늦게 뜬 서버에는 다시 시도로 붙는다. 접속은 받되 답하지 않는 서버에서는 시도마다 제한 시간을 주어야 정한 시간 근처에서 돌아온다. 주지 않으면 정한 3초를 넘겨 10초 뒤에도 기다리고 있었다.
6. 비밀번호의 글자: 주소에 비밀번호를 그대로 이어 붙였을 때 깨지는 것은 `@`가 든 것과 `%` 뒤에 16진수 두 자리가 오는 것이다. `:`, `/`, `?`, `#`, 빈칸, `+`, `&`, 한글, 16진수가 따르지 않는 `%`는 그대로 접속된다. 퍼센트 인코딩하면 모두 접속된다. compose가 짓는 꼴의 주소에서 호스트·포트·데이터베이스를 다르게 읽은 것은 `@`가 둘 이상인 주소뿐이었고, 시제품의 판정(`@`가 둘 이상이면 읽지 않는다)이 그것을 모두, 그리고 그것만 거부했다. 호스트에 `@`가 드는지만 보는 판정은 `@` 뒤에 `/`, `?`, `:`가 오는 비밀번호 셋을 놓쳤다.
7. uvicorn: 순수 ASGI 미들웨어가 수명 범위에서 실패를 두 줄 글과 함께 알리면 `ERROR:` 뒤의 첫 줄, 들여쓴 둘째 줄, "Application startup failed. Exiting."이 찍히고 종료 코드가 3이다. FastAPI의 수명 함수가 예외를 던지면 같은 종료 코드에 역추적까지 15줄이 찍힌다.
8. 쉬던 연결: 쓰기 전에 살아 있는지 확인하게 하면(`pool_pre_ping`) PostgreSQL이 다시 뜬 뒤 첫 질의가 성공한다. 확인하지 않으면 첫 질의가 `InterfaceError`로 실패하고 둘째가 성공한다.

## 파일

| 파일 | 무엇 |
|---|---|
| `../requirements.in` | 재는 도구 셋의 판 고정. `.scratch/admin-login/probes/pg_stack/`이 잰 판과 같고 asyncpg-stubs는 일부러 뺐다 |
| `proto/port.py` | 포트. 메서드 둘(`startup_problem`, `close`)인 `Protocol` |
| `proto/database.py` | 어댑터. 엔진, 접속 실패의 갈래 판정, 다시 시도, 표의 판 견줌, 마이그레이션 적용. SQLAlchemy와 alembic을 부르는 코드는 이 파일과 `migrations/`뿐이다 |
| `proto/migrations/env.py`, `proto/migrations/versions/0001_baseline.py` | 어댑터가 넘긴 연결로만 도는 alembic 환경과, 표를 만들지 않는 첫 마이그레이션. `alembic.ini`는 없다 |
| `proto/versions_next/` | 다음 판의 묶음 흉내. `0001`과 표 하나를 만드는 `0002` |
| `proto/versions_failing/` | 실패하는 묶음. `0001`과, 표 하나를 만든 뒤 예외를 던지는 `0002` |
| `proto/gate.py`, `proto/apps.py`, `proto/assembly.py` | 데이터베이스를 확인하는 순수 ASGI 미들웨어, 확인 자리가 다른 앱 둘, 연결 문자열로 어댑터를 만들어 앱에 넘기는 조립 |
| `control/wrong_adapter.py` | 양성 대조. 포트와 어긋난 어댑터 둘(반환 타입이 다른 것, 메서드가 빠진 것) |
| `serve_stub.py` | `serve`의 대역. `uvicorn.run`으로 앱을 띄운다 |
| `pyrightconfig.json` | 이 폴더를 pyright strict로 보는 설정 |
| `run.py` | 측정 전체. 섹션마다 무엇을 표지로 보는지는 독스트링과 회차의 이름에 있다 |

## 다시 돌리기

저장소의 `pyproject.toml`과 `uv.lock`은 고치지 않는다. 도구 셋은 저장소 밖 폴더의 사본에 더해 저장소의 잠금과 함께 푼다(`.scratch/admin-login/probes/pg_stack/README.md`의 방법이다). 아래에서 `<tree>`는 저장소 밖의 빈 폴더다. 저장소 루트에서 친다.

```sh
cp pyproject.toml uv.lock README.md <tree>/
uv add --project <tree> --no-sync -r .scratch/postgres-foundation/probes/requirements.in
uv sync --project <tree> --frozen --no-install-project
uv run --project <tree> --no-sync python .scratch/postgres-foundation/probes/stack/run.py
```

- 위 네 줄은 폴더 자리만 `<tree>`로 바꿔 적은 것이다. 이 측정이 실제로 친 명령이고, `uv add`가 패키지 94개를 풀었고 `uv sync`가 92개를 2분 42초에 깔았다(손으로 봤다, 2026-11-18).
- 필요한 것: 도는 Docker 데몬(리눅스 엔진)과 이미지 `postgres@sha256:b9f6b8ff03b62f3cfd9d9ba3fe56226a9991c79d3fb46fd46536263bf02be553`(없으면 `docker run`이 받는다). LLM은 부르지 않는다.
- 하는 일: 이름이 `pgf-stack-<무작위 8자>`인 PostgreSQL 컨테이너를 호스트의 `127.0.0.1` 빈 포트에 띄우고, 끝나면 그 컨테이너만 익명 볼륨과 함께 지운다. `window` 섹션은 컨테이너를 하나 더 띄운다. 비밀번호는 측정용 고정 값이고 그 컨테이너 밖에서는 쓰이지 않는다.
- `--sections types,migrate,versions,errors,url,uvicorn,preping,window`로 섹션을 고른다. 측정이 아닌 회차가 하나라도 있으면 종료 코드가 1이다.
- 타입 검사만: `uv run --project <tree> --no-sync python -m pyright -p .scratch/postgres-foundation/probes/stack`(양성 대조의 오류 둘이 있어 종료 코드는 1이다). 린트: `uv run ruff check .scratch/postgres-foundation/probes/stack`, `uv run ruff format --check .scratch/postgres-foundation/probes/stack`.
- 편집기가 이 폴더의 파일에 "sqlalchemy를 찾지 못한다"고 알리는 것은 저장소의 가상 환경에 이 셋이 없어서다. 측정은 `<tree>`의 인터프리터로 돈다.

## 환경

| 무엇 | 값 | 어떻게 봤나 |
|---|---|---|
| 날짜 | 2026-11-18 | |
| 호스트 | Windows 10 Home 10.0.19045 | 세션 환경 정보 |
| Docker | Docker Desktop 4.97.0, 엔진 29.9.2(linux/amd64) | 손으로 봤다(`docker version`) |
| 파이썬 | 3.12.10 | 손으로 봤다(`python --version`, `<tree>`의 인터프리터) |
| 잰 도구 | SQLAlchemy 2.1.8, asyncpg 0.32.0, alembic 1.20.1, asyncpg-stubs 없음 | 프로브가 찍는다(`types` 섹션의 관찰 줄) |
| 저장소 잠금의 도구 | pyright 1.1.414, uvicorn 0.53.0, fastapi 0.141.1 | pyright는 프로브가 찍는다. 나머지는 코드를 읽었다(`uv.lock`) |
| PostgreSQL | `postgres@sha256:b9f6…e553`. ADR 0066이 `postgres:18`(Debian trixie, 18.7)의 digest로 적은 값이다 | 프로브가 이 digest로 띄운다. 서버의 판 번호는 이 프로브가 읽지 않았다 |
| 부하 | 측정하는 동안 같은 PC의 같은 Docker 데몬에서 다른 프로브 셋(`clone_xdist/`, `compose_shape/`, `restart_recover/`)과 다른 세션의 컨테이너가 함께 돌았다 | 손으로 봤다 |

## 결과

### 타입(`types`)

시제품 `proto/`의 파이썬 파일 전부가 pyright strict 오류 0이고 타입 우회 검사(`tools/check_type_escapes.py`의 `escapes_in`)에 걸리는 줄이 0이다. pyright는 이 폴더의 파일 15개를 분석했다(`proto/versions_failing/`을 더하기 전의 전체 실행에서는 13개).

- 환경에 asyncpg-stubs가 없다는 것을 회차 하나가 먼저 본다. 시제품은 asyncpg를 import하지 않고, 접속 실패를 예외의 클래스가 아니라 오류 번호(`sqlstate` 속성이 문자열인지)와 `OSError` 여부로 가른다. `.scratch/admin-login/probes/pg_stack/README.md`는 asyncpg를 직접 import하는 모듈이 스텁 없이는 오류 23이라고 적는다.
- 어댑터(`proto/database.py`)는 포트(`proto/port.py`)를 import하지 않는다. 둘이 맞대지는 자리는 조립(`proto/assembly.py`가 어댑터를 `gate_app(database: Database)`에 넘긴다)이다.
- 양성 대조: `control/wrong_adapter.py`의 두 호출이 각각 `reportArgumentType`이다(`Argument of type "WrongReturn" cannot be assigned to parameter "database" of type "Database" in function "gate_app"`, `MissingClose`도 같은 꼴). 그래서 오류 0은 pyright가 이 폴더를 보지 않아서도, 구조를 맞대지 않아서도 아니다. 타입 우회 검사는 `Any`를 쓴 두 줄짜리 견본을 잡는 것을 같은 회차에서 본다.

### 빈 첫 마이그레이션과 표의 판 견줌(`migrate`, `versions`)

| 상황 | 시제품이 낸 것 | 데이터베이스에 남은 것 |
|---|---|---|
| 빈 데이터베이스를 확인한다 | "데이터베이스의 표가 이 판보다 뒤처져 있습니다. agent-os migrate 를 먼저 돌리십시오."와 둘째 줄 "  표의 판은 없음이고 이 판의 마지막 판은 0001입니다." | 표 없음 |
| 빈 데이터베이스에 첫 마이그레이션을 적용한다 | 문제 없음 | 표 `alembic_version` 하나, 줄 `0001` |
| 올린 뒤 확인한다 | 문제 없음 | |
| 한 번 더 적용한다 | 문제 없음 | 줄 `0001` 그대로 |
| 다음 판의 묶음(`0001`, `0002`)으로 `0001`인 데이터베이스를 확인한다 | 같은 "뒤처져 있습니다" 문구와 둘째 줄 "  표의 판은 0001이고 이 판의 마지막 판은 0002입니다." | 줄 `0001` |
| 다음 판의 묶음으로 적용한다 | 문제 없음 | 표 `probe_marker`가 생기고 줄 `0002` |
| 옛 판의 묶음(`0001`뿐)으로 `0002`인 데이터베이스를 확인한다 | "데이터베이스가 이 판보다 새롭습니다. 되돌리려면 올리기 전의 백업을 복원하십시오."와 둘째 줄 "  표의 판은 0002이고 이 판이 아는 마지막 판은 0001입니다." | |
| 옛 판의 묶음으로 `migrate`를 부른다 | 같은 "새롭습니다" 문구 | 줄 `0002`와 표 `probe_marker` 그대로 |
| 옛 판의 묶음으로 판정 없이 alembic의 `upgrade`만 부른다 | `alembic.util.exc.CommandError: Can't locate revision identified by '0002'` | 줄 `0002` 그대로 |
| 파일이 없는 빈 폴더로 빈 데이터베이스를 확인한다 | 문제 없음 | 표 없음 |
| 같은 빈 폴더로 `migrate`를 부른다 | 문제 없음(예외 없음) | 표 `alembic_version` 하나, 줄 없음 |
| 그 뒤 빈 폴더로 다시 확인한다 | 문제 없음 | |
| `0001`인 데이터베이스에 실패하는 묶음(`proto/versions_failing/`)으로 `migrate`를 부른다 | `0002`가 던진 `RuntimeError`가 그대로 올라온다 | 표 `alembic_version` 하나, 줄 `0001` 그대로. `0002`가 만든 `probe_broken`은 없다 |

- 빈 폴더의 세 회차는 폴더가 비었고 데이터베이스에 표가 없다는 것을 표지로 보고, 판정과 올리기의 결과는 회차의 결과 칸에서 읽는다. 같은 빈 데이터베이스를 파일 있는 폴더로 확인하면 "뒤처졌다"로 나오는 것은 위 첫 줄이 보므로, "문제 없음"은 폴더가 비어 마지막 번호가 없기 때문이다.
- 실패하는 묶음의 회차는 그 `0002`가 던진 글(`probe: 일부러 실패하는 마이그레이션`)을 표지로 본다. 그 글은 표를 만드는 문장 뒤에서 던지므로, 그 글이 오면 표를 만드는 문장이 돈 뒤다. 그런데도 `probe_broken`이 없고 줄이 `0001`이므로, 만든 표까지 되돌려졌다. 시제품의 트랜잭션은 두 겹이다. 어댑터가 올리기 전체를 `engine.begin()`으로 감싸고, 그 연결을 받은 `env.py`가 다시 `context.begin_transaction()`을 연다(코드를 읽었다). 둘 가운데 어느 것이 되돌렸는지는 갈래로 가르지 않았다. 명세가 이 회차로 세우는 것은 "실패하면 판과 표가 올리기 전 그대로"라는 결과뿐이다.
- 첫 마이그레이션 파일에 함수가 `upgrade` 하나뿐이라는 것을 회차가 그 파일을 파싱해 본다. `downgrade`가 없어도 alembic은 파일을 읽고 적용했다.
- 견줌은 판 기록 표에서 읽은 번호를 묶음과 대는 것이다. 번호가 묶음의 마지막과 같으면 문제 없음, 번호가 없거나 묶음에 있는 번호면 뒤처짐, 묶음에 없는 번호면 더 새로움이다. 묶음에 없는 번호가 "더 새로운 판"이 아니라 "남의 데이터베이스"일 수도 있다는 것은 이 견줌이 가르지 못한다.
- 마이그레이션은 어댑터가 연 연결을 `config.attributes["connection"]`으로 넘겨 `run_sync` 안에서 적용했다. `env.py`가 `asyncio.run`을 부르지 않으므로 이미 도는 이벤트 루프 안에서 불렸고, 적용한 것은 다른 연결(컨테이너 안의 `psql`)에서 보였다. `alembic.ini`는 없다.

### 접속 실패의 꼴(`errors`의 앞 넷, `window`)

SQLAlchemy로 붙어 질의 하나를 했을 때 온 예외다. 사슬은 바깥에서 안쪽 순이다.

| 상황 | 예외의 사슬 | `OSError`인가 | 오류 번호 | 시제품의 갈래 |
|---|---|---|---|---|
| 듣는 포트가 없다 | `ConnectionRefusedError` | 예 | 없음 | 다시 시도 |
| 이름이 풀리지 않는다 | `socket.gaierror` | 예 | 없음 | 다시 시도 |
| 접속은 받되 답하지 않는다(시도의 제한 시간 1초) | `TimeoutError` | 예(시제품이 다시 시도한 것으로 본다) | 없음 | 다시 시도 |
| 틀린 비밀번호 | `sqlalchemy.exc.DBAPIError` ← `…asyncpg.AsyncAdapt_asyncpg_dbapi.Error` ← `asyncpg.exceptions.InvalidPasswordError` | 아니오 | 28P01 | 바로 멈춤 |
| 없는 데이터베이스 | 같은 사슬의 `asyncpg.exceptions.InvalidCatalogNameError` | 아니오 | 3D000 | 바로 멈춤 |
| 로그인을 막은 계정(`create role … nologin`) | 같은 사슬의 `asyncpg.exceptions.InvalidAuthorizationSpecificationError` | 아니오 | 28000 | 바로 멈춤 |
| 접속 규칙(`pg_hba.conf`)에서 TCP 줄을 모두 지우고 설정을 다시 읽힌 서버 | 같은 사슬의 `asyncpg.exceptions.InvalidAuthorizationSpecificationError` | 아니오 | 28000 | 바로 멈춤 |
| 강제로 죽인 서버가 복구하는 동안 | `DBAPIError`(안쪽은 찍지 않았다) | | 57P03 | 다시 시도 |
| 같은 동안 | `ConnectionError` | 예 | 없음 | 다시 시도 |

- 앞의 넷(거부, 이름 풀이, 틀린 비밀번호, 없는 데이터베이스)은 예외의 문구에 접속에 쓴 비밀번호가 없다는 것까지 회차가 본다. 틀린 비밀번호의 문구는 `password authentication failed for user "agent_os"`였다.
- 28000의 두 회차는 서버가 그 까닭을 적은 문구를 표지로 본다. 로그인을 막은 계정은 `role "<이름>" is not permitted to log in`, 접속 규칙은 `no pg_hba.conf entry for host "172.17.0.1", user "agent_os", database "agent_os", no encryption`이었다. 뒤의 것은 처음 띄우기가 끊긴 볼륨에서 PostgreSQL이 다른 컨테이너의 접속을 거절한 문구(`../restart_recover/README.md` 항목 4)와 앞머리가 같다. 그 볼륨에서 실제로 받은 거절의 오류 번호는 이 프로브가 보지 않았다(그 프로브의 대역은 `psql`이라 번호를 싣지 않는다). 같은 문구를 같은 서버 판이 내므로 같은 28000이라고 읽는다(어림). 로그인을 막은 계정은 회차마다 무작위 이름으로 만들고 회차 끝에 지운다.
- 복구 중: 체크포인트를 미룬 서버(`checkpoint_timeout=1h`, `max_wal_size=16GB`)에 400만 줄을 넣고 `docker kill -s KILL`로 죽인 뒤 다시 띄워, 접속이 될 때까지 되풀이했다. 표지는 서버 로그의 "database system was interrupted"나 "redo starts"다. 결과를 낸 실행에서 실패는 57P03이 487번, 오류 번호 없는 `ConnectionError`가 12번이었고 다른 갈래는 없었다. 앞선 실행 둘에서는 57P03만 495번, 57P03 603번과 `ConnectionError` 17번이었다. 횟수는 복구에 걸린 시간에 따라 달라지므로 갈래만 읽는다.
- 재지 못한 갈래가 있다. 08로 시작하는 번호는 만들어 보지 못했다. 시제품이 08 계열을 "다시 시도"에 넣은 것은 PostgreSQL의 오류 번호 표를 기억에 기대어 읽은 어림이다. 57P03도 복구 중일 때만 봤고 보통의 시작과 종료 도중에는 따로 만들지 않았다.

### 다시 시도(`errors`의 뒤 여섯)

| 상황 | 시제품에 준 값 | 본 것 |
|---|---|---|
| 듣는 포트가 없다 | 다시 시도 3초, 간격 0.5초 | 4.6초 뒤 "닿지 못했습니다. 3초 동안 다시 시도했습니다(ConnectionRefusedError)", 알림 1줄 |
| 틀린 비밀번호 | 다시 시도 30초 | 0.0초 뒤 "계정이나 비밀번호를 받아들이지 않았습니다(오류 번호 28P01)"와 둘째 줄, 알림 0줄 |
| 접속 규칙에 맞는 줄이 없다 | 다시 시도 30초 | 0.0초 뒤 "이 접속을 허락하지 않았습니다(오류 번호 28000)"와 둘째 줄, 알림 0줄 |
| 서버를 멈춘 채 확인을 시작하고 4초 뒤 서버를 띄운다 | 다시 시도 90초, 간격 0.5초 | 4초 시점에 아직 기다리는 중이었고 4.6초 뒤 붙어 표의 판을 읽었다, 알림 1줄 |
| 접속은 받되 답하지 않는 서버 | 다시 시도 3초, 시도의 제한 시간 1초 | 4.1초 뒤 "닿지 못했습니다. 3초 동안 다시 시도했습니다(TimeoutError)", 알림 1줄 |
| 같은 서버(대조) | 다시 시도 3초, 시도의 제한 시간 없음 | 10초 뒤에도 돌아오지 않았다 |

- 멈출 때의 글의 괄호에는 오류 번호가 든다. 번호가 없으면 가장 안쪽 `OSError`의 이름이다(`ConnectionRefusedError`, `TimeoutError`). 드라이버의 문구는 싣지 않는다. 계정 이름이나 주소의 조각이 섞일 수 있어서다(`proto/database.py`의 `reason_of`, 코드를 읽었다). 글에 비밀번호가 없다는 것은 틀린 비밀번호와 28000의 회차가 본다.

- 시도의 제한 시간은 SQLAlchemy의 `connect_args={"timeout": 초}`로 주었고 asyncpg가 접속 전체에 건다. 주지 않으면 asyncpg의 기본값인데 그 값(60초라고 기억한다)은 이 프로브가 읽지 않았다(어림). 대조 갈래가 본 것은 10초를 넘긴다는 것까지다.
- 다시 시도의 마감은 시도와 시도 사이에서만 본다. 그래서 돌아오는 때는 정한 시간에 마지막 시도 하나가 걸린 시간을 더한 것이다. 윈도에서는 거부된 접속 한 번이 2초 가까이 걸려(3초 설정에 4.6~5.8초, 실행 넷) 정한 시간을 그만큼 넘겼다. 리눅스에서 거부가 바로 돌아오는지는 이 프로브가 재지 않았다.
- 알림은 첫 실패 뒤 한 번만 찍는다. 정한 시간이 첫 시도 하나에 다 가면 알림 없이 끝난다(앞선 실행에서 다시 시도 2초로 준 회차가 그래서 측정이 아니었다).
- 이름이 풀리지 않는 것도 다시 시도한다. 그래서 호스트 이름을 잘못 적은 주소는 정한 시간이 지난 뒤에야 문구가 나온다.

### 비밀번호의 글자(`url`)

회차마다 계정의 비밀번호를 그 값으로 바꾼 뒤 세 가지로 붙었다. `URL.create`로 지은 주소(양성 대조), 글자를 그대로 이어 붙인 주소, 비밀번호만 퍼센트 인코딩한 주소다. 양성 대조와 인코딩한 주소는 열세 값 모두 접속됐다. 그래서 그대로 이어 붙인 주소의 실패는 서버가 그 비밀번호를 받지 않아서가 아니라 주소가 다르게 읽혀서다.

| 비밀번호 | 그대로 이어 붙인 주소를 SQLAlchemy가 읽은 것 | 그 주소로 접속 |
|---|---|---|
| 16진수 64자 | 같게 읽음 | 접속 |
| `p@ss` | 다르게 읽음(host가 `ss@127.0.0.1`) | 실패(닿지 못함 쪽으로 간다) |
| `p:ss` | 같게 읽음 | 접속 |
| `p/ss` | 같게 읽음 | 접속 |
| `p@s:s/w` | `ValueError`로 거부. 그 문구에 비밀번호와 주소가 실리지 않았다 | 읽지 못함 |
| `p%41ss` | 다르게 읽음(host는 같고 비밀번호가 다르다) | 실패(비밀번호 거절) |
| `p%ss` | 같게 읽음 | 접속 |
| `p?ss`, `p#ss`, `p ss`, `p+ss`, `p&ss`, `비밀번호` | 같게 읽음 | 접속 |

- `@`가 든 비밀번호는 host에 `@`가 든 주소로 읽혀, 그 이름을 풀다 실패하므로 "닿지 못함"으로 다시 시도하게 된다. 비밀번호가 문제라는 것이 드러나지 않는다.
- `%` 뒤에 16진수 두 자리가 오면 그 셋이 한 글자로 풀려 다른 비밀번호가 된다. 주소만 보고는 알아챌 수 없다.
- compose가 값을 바꾸지 않고 그대로 끼워 넣는다는 것은 ADR 0066이 손으로 본 것이고, 이 프로브는 SQLAlchemy가 읽는 쪽만 쟀다.

주소를 읽지 못한 것으로 보는 판정(`parse_url`)은 서버 없이 읽기만 해서 쟀다. 위 열세 값에 `@` 뒤로 `/`, `?`, `:`가 오는 비밀번호 셋(`x@h/db`, `x@h?q=1`, `x@h:1/db`)을 더한 열여섯 값을 compose가 짓는 꼴(`postgresql://agent_os:<값>@postgres:5432/agent_os`)에 넣고, SQLAlchemy의 `make_url`이 읽은 호스트·포트·데이터베이스가 그 꼴의 것(`postgres`, `5432`, `agent_os`)과 다른지를 판정의 거부와 견줬다.

| 비밀번호 | `make_url`이 읽은 것 | 판정 |
|---|---|---|
| `p@ss` | 호스트 `ss@postgres` | 거부 |
| `p@s:s/w` | 읽다 거부 | 거부 |
| `x@h/db`, `x@h?q=1`, `x@h:1/db` | 호스트 `h`(데이터베이스나 포트도 다르다) | 거부 |
| `p%41ss` | 자리는 같고 비밀번호만 다르다 | 받는다 |
| 나머지 열 | 같게 읽음 | 받는다 |

- 판정은 자리를 다르게 읽은 다섯을 모두 거부했고, 자리를 같게 읽은 열하나는 하나도 거부하지 않았다. 다섯 모두 주소에 `@`가 둘 이상이다.
- 대조: 호스트에 `@`가 드는지만 보는 판정은 `x@h/db`, `x@h?q=1`, `x@h:1/db`를 놓친다. 셋 모두 호스트가 `h`로 읽혀 `@`가 남지 않는다. 회차가 판정을 따로 돌린 것이 아니라 읽은 호스트에 `@`가 없다는 것으로 센다.
- `p%41ss`는 자리를 같게 읽으므로 판정이 받는다. 그 주소는 접속에서 비밀번호 거절(28P01)로 드러난다(위 표). 판정은 자리만 지키고 비밀번호가 바뀌는 것은 막지 않는다.

### uvicorn의 실패 출력(`uvicorn`)

`serve_stub.py`를 하위 프로세스로 띄워 표준 오류와 종료 코드를 봤다. 저장소의 `serve`와 같이 `uvicorn.run(app, host=, port=)`으로 띄운다.

| 확인 자리 | 데이터베이스 | 찍힌 것 | 종료 코드 |
|---|---|---|---|
| 순수 ASGI 미들웨어 | 표가 뒤처짐 | 5줄. `Started server process`, `Waiting for application startup.`, `ERROR: <첫 줄>`, 들여쓴 둘째 줄 `  표의 판은 없음이고 이 판의 마지막 판은 0001입니다.`가 그대로 한 줄, `ERROR: Application startup failed. Exiting.` 역추적 없음 | 3 |
| FastAPI의 수명 함수가 예외를 던진다 | 표가 뒤처짐 | 15줄. 역추적이 든다(글이 한 줄이던 앞선 실행에서는 14줄이었고 `proto.apps.DatabaseNotReady: <문구>`를 봤다). 끝 세 줄은 둘째 줄, 빈 줄, 같은 `Application startup failed. Exiting.`이다 | 3 |
| 순수 ASGI 미들웨어 | 듣는 포트가 없다(다시 시도 7초) | 알림 한 줄("데이터베이스(…)에 아직 닿지 못해 최대 7초 동안 다시 시도합니다.") 뒤에 `ERROR: 데이터베이스(…)에 닿지 못했습니다. …`와 `Application startup failed. Exiting.` | 3 |
| 순수 ASGI 미들웨어(양성 대조) | 올린 데이터베이스 | `Application startup complete.`와 `Uvicorn running on …` | 떴다 |

- 미들웨어(`proto/gate.py`)는 수명 범위의 첫 메시지를 받은 뒤 포트의 `startup_problem`을 부르고, 문제가 있으면 `close`를 부른 뒤 `lifespan.startup.failed`에 그 문구를 실어 보낸다. 문제가 없으면 받은 첫 메시지를 안쪽 앱에 다시 건넨다.
- 같은 프로세스에서 uvicorn을 띄웠다 정상 종료시키면 `startup_problem`이 한 번, `close`가 한 번 불렸다.
- 종료 코드 3은 uvicorn이 내는 것이다. 저장소의 구성 오류(`src/agent_os/main.py`의 `_serve`)는 1로 끝나므로 둘이 다르다(코드를 읽었다).
- 윈도 호스트에서 본 것이다. 리눅스 컨테이너의 `serve`가 같은 줄을 찍는지는 이 프로브가 재지 않았다.

### 쉬던 연결(`preping`)

엔진 둘(확인하는 것, 확인하지 않는 것)로 질의를 한 번씩 해 연결을 묶음에 둔 뒤 PostgreSQL 컨테이너를 `docker restart`했다. 다시 뜬 뒤 확인하는 엔진은 첫 질의가 성공했다. 확인하지 않는 엔진은 첫 질의가 `InterfaceError`로 실패하고 둘째가 성공했다.

## PR 봇이 짚은 틈

PR 606의 봇(CodeRabbit) 첫 회차가 이 프로브에 Major 여덟(#3~#10)을 냈다. 여덟 모두 코드로는 맞는 지적이고, 위 결과는 그대로 선다. 프로브 코드는 고치지 않았다. 고치면 다시 돌려 이 README의 판과 명세의 수치를 바꿔야 하기 때문이다. 다시 돌릴 사람은 항목마다의 고침을 먼저 넣는다. 판정은 잰 판의 라이브러리 소스(SQLAlchemy 2.1.8, asyncpg 0.32.0, uvicorn 0.53.0, Starlette 1.6.0)를 읽어 했다. 위 결과를 낸 실행의 원본은 남아 있지 않다(그 뒤의 실행 하나가 남았지만 복구 중 회차의 횟수가 57P03 563번, `ConnectionError` 13번으로 위 표와 달라 다른 실행이다). 그래서 결론이 서는 까닭은 위 표에 적힌 값과 코드로 든다.

- **#3 질의 문자열(`proto/database.py`의 `parse_url`).** 질의의 `database`와 `host`가 경로를 덮는다. asyncpg 방언의 `create_connect_args`가 질의를 연결 인자 위에 덮어쓴다(함수를 불러 봤다). 이 프로브가 지은 주소에는 질의가 없어 결과에 닿지 않는다. 명세는 질의가 든 주소를 받지 않게 정했다("연결 문자열과 비밀번호의 변수"). 고침: `parse_url`이 질의가 든 주소에 `None`을 돌려준다.
- **#4 판 읽기의 제한 시간(`_reach`).** 접속 인자 `timeout`은 연결을 맺는 데만 걸리고, 질의의 제한 시간 `command_timeout`은 기본이 없다. 답하지 않는 서버 회차는 연결을 맺는 데서 멈추므로 위 값은 그대로다. 명세는 시도 하나를 통째로 제한 시간으로 감싸게 정했다("뜰 때의 확인과 다시 시도"). 고침: 시도 하나를 `asyncio.timeout`으로 감싸고, 판 기록 표를 다른 연결이 잠근 갈래를 더한다.
- **#5 대조 psql의 종료 코드(`run.py`의 `rows`).** psql이 실패해도 빈 목록을 돌려준다. 롤백 회차는 기록에 값이 있어 psql이 성공했다. 빈 결과를 증거로 쓴 셋(`migrate` 섹션의 "빈 데이터베이스는 뒤처진 것으로 본다"와 `versions` 섹션의 "빈 마이그레이션 폴더로 빈 데이터베이스를 확인한다"가 표지로 쓴 표 없음, 빈 폴더에서 올린 뒤의 `줄 []`)은 기록만으로 psql 실패와 가르지 못한다. 같은 회차의 앞뒤 psql이 값을 냈으므로 실패했을 가능성은 낮다고 본다(어림). 고침: 종료 코드가 0이 아니면 예외로 그 회차를 측정 아님으로 센다.
- **#6 uvicorn의 `SystemExit(3)`(`uvicorn` 섹션의 `serve_and_stop`).** 데이터베이스가 그 사이 내려가 시작이 실패하면 uvicorn이 `sys.exit(3)`을 부르고, 그 예외가 태스크 밖으로 나와 남은 섹션과 집계를 잃는다. 기록된 실행에서는 나지 않았다(모든 회차가 찍혔다). 고침: 태스크 안에서 `SystemExit`를 받아 그 회차의 결과로 적는다.
- **#7 롤백 회차의 앞 판(`versions` 섹션의 `failing_migration_round`).** 첫 `migrate`가 실패하면 그 결과를 버리고 실패용 묶음을 올린다. 그 갈래였다면 결과가 `표 [], 줄 []`였을 텐데 기록은 `['0001']`이라 결론에 닿지 않는다. 고침: 첫 `migrate`의 결과가 문제 없음일 때만 이어 간다.
- **#8 섹션 밖의 예외(`main`).** 회차 밖에서 예외를 던지는 자리가 열하나라, 거기서 터지면 모은 회차를 찍지 못한다. 기록된 실행은 모두 찍혔다. 고침: 섹션마다 예외를 받아 측정 아님 한 줄로 남기고, 모은 결과를 찍은 뒤 1로 끝낸다.
- **#9 확인이 예외로 끝날 때(`proto/gate.py`).** 확인이 글 대신 예외를 던지면 시제품은 `lifespan.startup.failed`를 보내지 않고, `lifespan="auto"`인 uvicorn은 "appears unsupported"를 찍고 그대로 뜬다(uvicorn `lifespan/on.py`를 읽었다). 이 프로브의 양성 대조 "떴다"의 표지는 그 갈래에서도 나와 둘을 가르지 못한다. 다만 같은 데이터베이스에서 닫기가 한 번 불린 회차가 정상 길을 받친다(그 갈래면 시제품은 닫기를 부르지 않는다). 명세는 예외도 고정 글로 시작 실패를 보내고 `serve`가 `lifespan="on"`을 넘기게 정했다("데이터베이스 포트와 조립"). 고침: 시제품을 명세대로 고치고, 확인이 예외를 던지는 가짜를 갈래로 더한다.
- **#10 닫기와 종료 완료의 차례(`proto/gate.py`).** 시제품은 앱의 `lifespan.shutdown.complete`를 넘긴 뒤에 닫는다. uvicorn은 완료를 받으면 더 기다리지 않아, 닫는 도중에 프로세스가 끝날 수 있다. 측정의 `Recording`은 `await` 전에 세므로 "닫기가 한 번 불렸다"는 맞지만 닫기가 끝났다는 것은 보이지 못한다. 명세는 닫은 뒤에 완료를 넘기게 정했다(같은 절). 고침: 시제품을 명세대로 고치고, `Recording`이 닫기가 끝난 뒤에 세게 한다.

둘째 회차는 이 프로브에 Major 하나를 냈고, 위 #5와 같은 자리다(빈 데이터베이스 회차의 표 없음 표지가 psql 실패와 빈 결과를 가르지 못한다). 판단과 고침은 #5 그대로다. 셋째 회차의 Major 하나도 같은 자리다.

## 재지 못한 것

- 실제 `agent_os` 패키지. 같은 모양의 시제품이고, import-linter 계약과 실제 `create_app`의 미들웨어 차례는 여기에 없다.
- 리눅스에서 도는 `serve`. 호스트가 윈도라, 거부된 접속이 돌아오는 시간과 uvicorn이 찍는 줄은 윈도의 것이다. 리눅스 컨테이너 안에서 `serve` 대역을 돌리는 것은 `../restart_recover/`가 맡는다.
- 08 계열, 보통의 시작과 종료 도중의 57P03, 처음 띄우기가 끊긴 볼륨이 실제로 낸 거절의 오류 번호(위 "접속 실패의 꼴").
- asyncpg의 기본 접속 제한 시간의 값.
- 연결 묶음의 크기, 동시 요청, 질의의 성능.
- `migrate` 둘이 같은 데이터베이스에 함께 도는 경우(ADR 0066이 multi-instance에 넘겼다).
- 설치된 휠과 읽기 전용 루트의 이미지에서 alembic이 패키지 안의 마이그레이션 파일을 읽는지. 시제품은 저장소의 폴더에서 읽었다.
- 묶음에 없는 번호가 "더 새로운 판"인지 "남의 데이터베이스"인지.
- 시간의 분포. 회차마다 한 번씩만 돌았고 다른 프로브가 같은 데몬을 쓰고 있었다. 위의 초 단위 값은 차례와 크기만 읽는다.

## 남긴 것

- 컨테이너와 볼륨: 없다. 끝에서 `docker ps -a --filter name=pgf-stack`이 비었다(손으로 봤다).
- 이미지: 받아 둔 `postgres@sha256:b9f6…e553`을 그대로 썼고 새로 받거나 지은 것이 없다.
- 저장소 밖의 `<tree>` 폴더(가상 환경 포함)는 측정한 세션의 임시 폴더에 있고 저장소에 들지 않는다.
