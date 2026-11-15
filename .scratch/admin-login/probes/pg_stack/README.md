# admin-login pg_stack 프로브

`admin-login` 이 계정과 로그인 상태(갱신용 번호)와 로그인 실패 횟수를 PostgreSQL 에 두기로 한 뒤, 그것을 쓰는 도구 조합을 고르는 데 쓸 사실을 잰 프로브다. 저장소에는 아직 PostgreSQL 드라이버가 없다. 보는 것은 다섯이다. 조합마다 작은 모듈이 pyright strict 와 타입 우회 검사를 우회 없이 지나는지, 실제 PostgreSQL 에서 도는지(윈도 호스트와 리눅스 컨테이너, 서버의 이벤트 루프와 pytest 설정에서), 표를 만드는 도구(마이그레이션) 셋, 테스트가 PostgreSQL 을 스스로 띄우는 길(testcontainers), 공식 이미지의 판과 크기다. 여기서는 결정하지 않고 본 것만 적는다. 규약은 `docs/agents/issue-tracker.md` 의 "프로브와 근거"다.

결과는 2026-11-14 에 `run.py` 를 항목 여섯 전부로 한 번 돌린 것이다(실행 토큰 `049174`, 측정 184 회차, 측정 아님 0 회차, 종료 코드 0). 같은 날 앞서 항목을 나눠 돌린 실행 넷(토큰 `066d9e`, `d5f2fc`, `79ee50`, `85f8d5`)의 값은 시간의 범위를 적을 때만 함께 든다.

근거의 종류는 다섯이다. 프로브가 다시 낸다(`run.py` 가 표지를 보고 센 회차), 손으로 봤다(명령과 함께 적는다), 코드를 읽었다(파일과 줄), 원문을 내려받아 봤다(주소), 어림. 원문을 내려받지 않은 웹 요약은 쓰지 않았다.

## 요약

고를 때 쓸 한 줄씩이다. 근거와 갈래는 결과 절에 있다.

1. 타입: psycopg 3(동기·비동기), asyncpg(asyncpg-stubs 와 함께), SQLAlchemy 2 Core(동기·비동기), 번호 붙인 SQL 러너, Alembic 의 모듈이 모두 pyright strict 오류 0, 타입 우회 0 이다. asyncpg 는 타입 표지(`py.typed`)가 없어 asyncpg-stubs 없이는 같은 모듈이 오류 23 이다. yoyo-migrations 는 타입이 없어 부르는 모듈이 오류 3 이다. 프로브가 다시 낸다.
2. 실행: 일곱 조합 모두 리눅스 컨테이너(`python:3.12-slim-trixie`)에서 돌았다. 윈도에서는 동기 둘과 asyncpg 둘이 어느 루프에서나 돌았고, psycopg 의 비동기 모드를 쓰는 셋은 서버와 `asyncio.run` 과 pytest 의 기본 루프(`ProactorEventLoop`)에서 거부됐다. 같은 셋이 Selector 루프에서는 돌았다. 프로브가 다시 낸다.
3. Selector 루프로 바꾼 윈도 서버: `anyio.run_process` 는 `NotImplementedError` 였고, 저장소의 MCP 어댑터와 같은 호출(`stdio_client`)로 연 stdio MCP 서버는 도구 목록까지 답했다. 프로브가 다시 낸다.
4. 표 만들기: 번호 붙인 SQL 파일 + 러너(psycopg, asyncpg), Alembic(동기 env, 비동기 env), yoyo-migrations 가 모두 새 데이터베이스에 표 둘과 색인 둘을 만들었고 다시 적용하면 아무것도 하지 않았다. 권고 잠금을 쥔 SQL 러너 둘을 함께 띄우면 판이 한 번씩만 적용됐다. 프로브가 다시 낸다.
5. testcontainers: 프로세스 하나가 `postgres:18-alpine` 하나를 띄워 준비되기까지 13.61~17.08초(Ryuk 켬), 9.61~13.45초(Ryuk 끔)였고, 같은 때 `docker run` 만으로는 9.44~12.27초였다. 부하가 큰 때의 앞선 실행은 21.49~70.0초였다. 세션 범위 픽스처는 pytest-xdist 작업자마다 따로 돌아 `-n 8` 이면 PostgreSQL 컨테이너가 여덟(Ryuk 도 여덟) 떴다. 프로브가 다시 낸다(Ryuk 여덟은 손으로 봤다).
6. 이미지: 지원 중인 주 판은 18, 17, 16, 15, 14(14 의 마지막 판 내기는 2026-11-12)다. `postgres:18-alpine` 은 풀린 크기 304MB(압축 120.2MB), `postgres:18` 은 474MB(압축 168.5MB)다. 원문을 내려받아 봤다, 프로브가 다시 낸다.

## 파일

| 파일 | 무엇 |
|---|---|
| `requirements.in` | 재는 후보의 판 고정(2026-11-14 의 PyPI 최신 안정판) |
| `model.py` | 조합이 함께 쓰는 `Account` 와, 드라이버가 준 값을 `isinstance` 로 좁히는 도우미 셋 |
| `stack_psycopg_sync.py`, `stack_psycopg_async.py`, `stack_asyncpg.py` | 드라이버 조합. 계정 넣기, 이름으로 읽기, 실패 횟수를 트랜잭션 안에서 올리기(`SELECT … FOR UPDATE`), 갱신용 번호 넣고 지우기 |
| `sa_tables.py`, `stack_sa_sync.py`, `stack_sa_async.py` | SQLAlchemy 2 Core 조합. 같은 다섯 동작 |
| `exercise.py` | 조합 하나를 실제 PostgreSQL 에서 도는 한 바퀴. 연결 둘이 실패 횟수를 다섯 번씩 함께 올려 10 이 되는지를 본다 |
| `friction_asyncpg_pool.py`, `friction_psycopg_dynamic_sql.py` | pyright 오류를 기대하는 대조군. 타입이 막는 자리 둘 |
| `control_checks.py` | pyright strict 와 타입 우회 검사가 이 폴더를 실제로 본다는 양성 대조 |
| `reveal.py` | 드라이버가 돌려준 값을 pyright 가 무슨 타입으로 보는지 찍는다 |
| `migrations/`, `migrate_sql.py`, `migrate_sql_asyncpg.py` | 번호 붙인 SQL 파일 둘과 러너(psycopg 판, asyncpg 판) |
| `alembic_versions/`, `alembic_sync/env.py`, `alembic_async/env.py`, `migrate_alembic.py` | Alembic. `alembic.ini` 없이 코드에서 `Config` 를 만들어 `upgrade head` |
| `migrate_yoyo.py` | yoyo-migrations 로 위 SQL 파일을 적용 |
| `loop_app.py`, `loop_client.py`, `mcp_probe_server.py` | 서버와 같은 `uvicorn.run` 호출로 띄운 작은 FastAPI 앱, 그 앱에 요청을 보내는 쪽, 그 앱이 여는 stdio MCP 서버 |
| `test_async_loop.py`, `pytest_selector/` | 저장소의 pytest 설정에서 비동기 조합을 도는 시험과, 같은 시험을 루프 공장 훅으로 Selector 루프에서 도는 갈래 |
| `tc_start.py`, `tc_xdist/` | testcontainers 로 컨테이너 하나를 띄우는 시간, 세션 픽스처가 pytest-xdist 작업자마다 따로 도는지 |
| `versions.py` | 깔린 패키지의 판, 라이선스 칸, 휠 태그, `py.typed` |
| `Dockerfile`, `Dockerfile.dockerignore` | 리눅스 갈래의 이미지. `python:3.12-slim-trixie` 에 저장소 잠금과 후보를 함께 깐다 |
| `typecheck.py`, `pyrightconfig.json` | 이 폴더를 pyright strict 로 보는 도우미와 설정 |
| `run.py` | 측정 전체. 항목마다 무엇을 표지로 보는지는 독스트링에 있다 |

## 다시 돌리기

저장소의 `pyproject.toml` 과 `uv.lock` 은 고치지 않는다. 후보는 저장소 밖 폴더의 사본에 더해 저장소의 잠금과 함께 푼다. 아래에서 `<tree>` 는 저장소 밖의 빈 폴더, `<nostubs>` 는 asyncpg-stubs 가 없는 가상 환경을 둘 폴더다. 저장소 루트에서 친다.

```sh
cp pyproject.toml uv.lock README.md <tree>/
uv add --project <tree> --no-sync -r .scratch/admin-login/probes/pg_stack/requirements.in
uv sync --project <tree> --frozen --no-install-project
uv venv --python 3.12 <nostubs>
uv pip install --python <nostubs>/Scripts/python.exe asyncpg==0.32.0
uv run --project <tree> --no-sync python .scratch/admin-login/probes/pg_stack/run.py --tree <tree> --nostubs-python <nostubs>/Scripts/python.exe
```

- 위 여섯 줄은 폴더 자리만 `<tree>`·`<nostubs>` 로 바꿔 적은 것이다. 결과를 낸 실행 뒤에 빈 폴더 둘로 앞의 다섯 줄을 그대로 다시 쳤고(`uv sync` 가 103 개를 2분 20초에 깔았다), 마지막 줄은 `--items types` 를 붙여 돌려 측정 95 회차, 측정 아님 0 회차였다(손으로 봤다, 2026-11-15). `Scripts/python.exe` 는 윈도의 자리이고 리눅스에서는 `bin/python` 이다(리눅스 호스트에서는 돌려 보지 않았다).
- 필요한 것: 도는 Docker 데몬(리눅스 엔진, BuildKit), 네트워크(PyPI, Docker Hub, `ghcr.io/astral-sh/uv`), 이미지 `postgres:18-alpine`, `postgres:18`, `python:3.12-slim-trixie`, `testcontainers/ryuk:0.8.1`(없으면 받는다). LLM 은 부르지 않는다.
- 하는 일: PostgreSQL 컨테이너를 호스트의 `127.0.0.1` 임의 포트로 띄우고, 리눅스 갈래의 이미지 `admin-login-pg-probe-linux` 를 짓는다. 컨테이너와 네트워크는 이름이 `admin-login-pg-probe-<실행 토큰>-` 으로 시작하고 끝에서 그 접두로 찾아 익명 볼륨과 함께 지운다. testcontainers 의 Ryuk 컨테이너(`testcontainers-ryuk-<세션>`)는 스스로 지워진다. 이미지는 남긴다. 비밀번호는 실행마다 무작위이고 명령줄과 원본 기록에 싣지 않는다. 모든 명령의 원본 출력은 `--work`(없으면 시스템 임시 폴더) 아래 `raw-<실행 토큰>.log` 에 남는다.
- `--items types,migrate,windows,linux,tc,image` 로 항목을 고른다. `--pg-image`(기본 `postgres:18-alpine`), `--image-tags`, `--tc-rounds`(기본 3). 측정이 아닌 회차가 하나라도 있으면 종료 코드가 1 이다.
- `uv run --with-requirements …` 로 후보를 얹는 길은 이 PC 에서 되지 않았다(아래 "환경"의 uv 줄). 그래서 사본 폴더에 깐다.
- 항목 여섯 전부가 한 번에 8분 남짓 걸렸다(23:49:36~23:57:45. 손으로 봤다, 원본 기록의 첫 줄과 끝 줄의 시각. 이미지와 빌드 캐시가 이미 있던 때다).
- 타입 검사만: `uv run --project <tree> --no-sync python .scratch/admin-login/probes/pg_stack/typecheck.py`(pyright 의 JSON 을 낸다. 기대한 오류 10 이 있어 종료 코드는 1 이다). 린트: `uv run ruff check .scratch/admin-login/probes/pg_stack`, `uv run ruff format --check .scratch/admin-login/probes/pg_stack`.

## 환경

| 무엇 | 값 | 어떻게 봤나 |
|---|---|---|
| 날짜 | 2026-11-14 | |
| 호스트 | Windows 10 Home 10.0.19045, AMD Ryzen 7 3700X(논리 CPU 16) | 세션 환경 정보, 손으로 봤다(`Get-CimInstance Win32_Processor`) |
| Docker | 엔진 29.9.2(Docker Desktop, linux/amd64), 커널 `6.18.58.1-microsoft-standard-WSL2`, CPU 16, 메모리 16.7GB, 저장 드라이버 overlay2 | 손으로 봤다(`docker info`) |
| 부하 | 측정 내내 다른 세션들이 같은 PC 와 같은 Docker 데몬을 썼다(다른 세션의 컨테이너 `rag-engine-test-postgres-1` 이 CPU 34.73% 를 쓰고 있었다). 호스트 CPU 부하는 실행 `049174` 의 `tc` 항목 시작 때 59%, 끝(`-n 8` 직후) 때 100%, 실행 `85f8d5` 의 `tc` 항목 도중 100% 였다 | 프로브가 찍은 값(`host_load`, 회차로 세지 않는다), `85f8d5` 는 손으로 봤다(`Get-CimInstance Win32_Processor`, `docker stats --no-stream`) |
| 파이썬 | 호스트 3.12.10, 리눅스 이미지 3.12.16 | 프로브(`versions.py`) |
| uv | 호스트 0.10.8. `uv run --frozen --with-requirements requirements.in` 은 네 번 모두 pywin32 312 를 푸는 자리에서 실패했다(복사 방식은 "The wheel is invalid: Wheel contains an invalid entry (directory) in the `scripts` directory", `--link-mode hardlink` 는 "failed to remove directory … (os error 32)"). 같은 판을 `uv pip install` 과 `uv sync` 로 가상 환경에 까는 것은 됐다. pywin32 는 testcontainers 가 끌어오는 docker 패키지의 윈도 의존이고 저장소 잠금에 이미 있다 | 손으로 봤다 |
| 저장소 잠금의 도구 | pyright 1.1.414, pytest 9.1.1, pytest-asyncio 1.4.0, pytest-xdist 3.8.0, uvicorn 0.53.0, fastapi 0.141.1, anyio 4.15.1, mcp 2.3.0 | 프로브(`versions.py`), 코드를 읽었다(`uv.lock`) |
| PostgreSQL | `postgres:18-alpine` = `postgres@sha256:1018733457011bf88d81db98cf43aac6d5150afc18787dbe204771fedf80ff95`, 서버 18.7 | 손으로 봤다(`docker image inspect`), 프로브 |
| 리눅스 바탕 | `python:3.12-slim-trixie` = `python@sha256:5e2bdb1b0d542d5039cffb8181c65930093949194a65c365dfb1b0fe13a4fa5b`(`.scratch/release-image/spec.md` 가 serve 의 바탕으로 고른 것) | 손으로 봤다(`docker image inspect`) |

## 결과

### 후보의 판과 라이선스

판은 2026-11-14 에 `uv pip compile` 이 고른 PyPI 최신 안정판이다(손으로 봤다). 라이선스와 휠과 타입 표지는 깔린 배포판의 메타데이터에서 `versions.py` 가 읽었다(프로브가 낸다. 회차로 세지 않는 출력이다). 윈도(`win_amd64`)와 리눅스(`manylinux` x86_64) 모두 컴파일된 휠이 있어 두 곳 다 컴파일러 없이 깔렸다.

| 패키지 | 판 | 라이선스(메타데이터) | `py.typed` | 함께 오는 것 |
|---|---|---|---|---|
| psycopg | 3.3.9 | LGPL-3.0-only | 있음 | psycopg-binary 3.3.9(libpq 를 품은 휠, LGPL-3.0-only), psycopg-pool 3.3.3(LGPL-3.0-only), tzdata |
| asyncpg | 0.32.0 | Apache-2.0 | 없음 | 없음 |
| asyncpg-stubs | 0.32.0 | BSD-3-Clause | 스텁 패키지(`.pyi` 27) | asyncpg |
| SQLAlchemy | 2.1.8 | MIT | 있음 | greenlet 3.5.6(MIT AND PSF-2.0, `asyncio` extra 가 끌어온다) |
| alembic | 1.20.1 | MIT | 있음 | SQLAlchemy, Mako 1.4.3(MIT), MarkupSafe 3.0.4 |
| yoyo-migrations | 9.0.0 | Apache(메타데이터의 글자 그대로) | 없음 | sqlparse, tabulate, importlib-metadata, zipp, lazy-importer |
| testcontainers | 4.15.0 | Apache-2.0 | 있음 | docker 7.2.0(Apache-2.0), python-dotenv, wrapt. 윈도에서는 pywin32 |

후보 일곱 줄을 모두 저장소 잠금의 사본에 더하면 패키지가 84 에서 105 로 늘고(21 개), 이미 잠긴 패키지의 판은 하나도 바뀌지 않았다(손으로 봤다: `git diff --no-index --stat` 가 319 줄 추가, 삭제 0. 패키지마다의 몫은 `uv tree --frozen --package …`).

### 조합별 표

타입 열은 항목 `types`(호스트 플랫폼과 `--pythonplatform Linux` 둘 다 같았다), 윈도와 리눅스 열은 항목 `windows`·`linux` 다. 모두 프로브가 다시 낸다. "돈다"는 서버 판 18.7 이 읽히고, 연결 둘이 함께 올린 실패 횟수가 10 이고, 갱신용 번호를 지운 결과가 (지움, 없음)이고, 없는 이름이 `None` 인 것이다.

| 조합 | pyright strict | 타입 우회 | 윈도 기본 루프(Proactor) | 윈도 Selector 루프 | 리눅스 컨테이너 |
|---|---|---|---|---|---|
| psycopg 동기 | 오류 0 | 0 | 돈다(서버에서는 작업 스레드) | 돈다 | 돈다 |
| psycopg 비동기(연결 하나) | 오류 0 | 0 | 거부. `InterfaceError: Psycopg cannot use the 'ProactorEventLoop' to run in async mode` | 돈다 | 돈다 |
| psycopg 비동기 + psycopg-pool | 오류 0 | 0 | 거부. 풀을 여는 데서 `PoolTimeout: pool initialization incomplete after 8.0 sec`(풀의 로그에 위 `InterfaceError`) | 돈다 | 돈다 |
| asyncpg + asyncpg-stubs | 오류 0(스텁 없이는 23) | 0 | 돈다 | 돈다 | 돈다 |
| SQLAlchemy Core 동기 + psycopg | 오류 0 | 0 | 돈다(서버에서는 작업 스레드) | 돈다 | 돈다 |
| SQLAlchemy Core 비동기 + psycopg | 오류 0 | 0 | 거부. 같은 `InterfaceError` | 돈다 | 돈다 |
| SQLAlchemy Core 비동기 + asyncpg | 오류 0 | 0 | 돈다 | 돈다 | 돈다 |

윈도의 "기본 루프" 열은 세 자리에서 같았다. `asyncio.run`, 서버와 같은 `uvicorn.run(app, host=, port=, timeout_graceful_shutdown=)` 호출(`src/agent_os/main.py` 의 호출 모양. 그 서버의 루프는 `ProactorEventLoop` 로 찍혔다), 저장소 루트의 pytest 설정(`asyncio_mode = "auto"`, 머리에 `rootdir`·`configfile: pyproject.toml`·`asyncio: mode=Mode.AUTO`). "Selector 루프" 열도 세 자리에서 같았다. `asyncio.run(…, loop_factory=asyncio.SelectorEventLoop)`, `uvicorn.run(…, loop="asyncio:SelectorEventLoop")`, pytest-asyncio 의 `pytest_asyncio_loop_factories` 훅을 그 폴더의 `conftest.py` 에 둔 것(`pytest_selector/`). 리눅스 열은 `asyncio.run`, 같은 `uvicorn.run` 호출(루프 `_UnixSelectorEventLoop`), 저장소 설정의 사본으로 돈 pytest 에서 같았다. pytest 는 조합의 결과를 단언하지 않고 적기만 하므로 다섯 시험이 모두 통과했고 경고가 오류로 오른 것은 없었다.

거부하는 자리는 `psycopg/connection_async.py` 108 줄이다(코드를 읽었다, psycopg 3.3.9).

### 서버의 루프를 Selector 로 바꾸면

윈도에서 `uvicorn.run(…, loop="asyncio:SelectorEventLoop")` 로 띄운 서버에서 본 것이다. 프로브가 다시 낸다.

| 무엇 | 기본(Proactor) | Selector |
|---|---|---|
| `anyio.run_process` 로 자식 프로세스 하나 | `child-ok` | `NotImplementedError` |
| stdio MCP 서버를 `stdio_client` 와 `ClientSession` 으로 열어 도구 목록 받기 | 도구 `ping` | 도구 `ping` |
| `/shutdown`(SIGINT) 뒤 서버 종료 코드 | 0 | 0 |

mcp 2.3.0 에는 윈도에서 비동기 자식 프로세스가 `NotImplementedError` 를 내면 `subprocess.Popen` 을 감싼 것으로 물러서는 길이 있다(코드를 읽었다, `mcp/os/win32/utilities.py` 136~194 줄). Selector 갈래가 그 길을 탔는지는 프로브가 보지 않았다(탔다고 보는 것은 어림이다). 저장소의 MCP 어댑터가 stdio 서버를 여는 호출은 `src/agent_os/adapters/mcp.py` 326 줄이고 윈도에서는 런처 없이 그 호출 그대로다(`.claude/rules/adapters.md`). 프로브는 열고 도구 목록을 받고 닫는 데까지만 봤다. 취소된 실행이 서버를 끄는 길(ADR 0034)과 저장소의 기존 시험이 Selector 루프에서 도는지는 재지 않았다.

uvicorn 0.53.0 은 `loop` 를 주지 않으면 uvloop 이 깔려 있을 때 그것을, 없으면 윈도에서(재시작 감시나 작업자 여럿이 아닐 때) `ProactorEventLoop` 를, 그 밖에서 `SelectorEventLoop` 를 고른다(코드를 읽었다, `uvicorn/loops/auto.py` 와 `uvicorn/loops/asyncio.py`). 저장소 잠금에는 uvloop 이 없고 리눅스 컨테이너의 서버 루프는 `_UnixSelectorEventLoop` 로 찍혔다(프로브가 다시 낸다).

### 타입이 닿는 데와 닿지 않는 데

`reveal.py` 의 `reveal_type` 을 pyright 가 푼 것이다(프로브가 낸다).

- psycopg: 기본 행은 `tuple[Any, ...] | None`, `class_row(Account)` 를 주면 `Account | None`.
- asyncpg(스텁): 행은 `Record | None`, 칸 값(`row["one"]`)과 `fetchval` 은 `Any`.
- SQLAlchemy Core: 칸을 이름에 묶어(`ACCOUNT_ID = Column("id", BigInteger, …)`) `select` 에 넣으면 행이 `Row[int, str, datetime]`, `scalar_one()` 이 `int`. `accounts.c.id` 로 꺼낸 칸과 `text("…")` 는 `Any`. NULL 을 허용하는 칸(`locked_until`)도 `datetime` 으로만 드러나 `None` 이 타입에 없다.

`Any` 로 드러난 값은 pyright strict 가 오류로 치지 않는다. 조합 모듈은 그 값을 `model.py` 의 `isinstance` 도우미로 좁혔다. 타입이 막은 자리는 둘이고 대조군이 그 오류를 다시 낸다(프로브가 다시 낸다).

- asyncpg-stubs: 풀에서 빌린 연결은 `PoolConnectionProxy[Record]` 이고 `Connection[Record]` 를 받는 함수에 넘기면 `reportArgumentType` 이다(`friction_asyncpg_pool.py`). 조합 모듈은 둘의 합집합을 받게 적었다.
- psycopg: `execute` 는 질의를 `LiteralString`·`bytes`·`sql.SQL` 로만 받아, 파일에서 읽은 `str` 을 넘기면 `reportCallIssue` 와 `reportArgumentType` 이다(`friction_psycopg_dynamic_sql.py`). SQL 러너는 파일을 바이트로 읽어 넘겼다.

SQLAlchemy 2.1 은 `Row.tuple()` 을 2.0.19 부터, `Row._tuple()` 을 2.1.0 부터 폐기 경고로 낸다. 이 프로브의 첫 판이 `tuple()` 을 써서 pytest 가 `SADeprecationWarning` 넷을 냈고(실행 `d5f2fc`, 손으로 봤다), 행을 바로 풀게 고친 뒤에는 경고가 없었다.

asyncpg-stubs 없는 환경(asyncpg 0.32.0 만 깐 가상 환경)으로 같은 파일을 보면 `stack_asyncpg.py` 가 오류 23(`reportMissingTypeStubs`, `reportInvalidTypeArguments`, `reportUnknown…`), `migrate_sql_asyncpg.py` 가 오류 14 다. 그 환경을 실제로 봤다는 표지는 거기 없는 psycopg 의 가져오기가 풀리지 않았다는 오류다(프로브가 다시 낸다).

### 표 만들기

새 데이터베이스마다 적용하고 한 번 더 적용했다. 표지는 표 `accounts`·`refresh_tokens` 와 색인 `accounts_locked_until`·`refresh_tokens_account` 가 생긴 것이다. 프로브가 다시 낸다.

| 방법 | pyright strict | 타입 우회 | 적용 | 다시 적용 | 남기는 표 |
|---|---|---|---|---|---|
| 번호 붙인 SQL + 러너(psycopg, 39 줄) | 오류 0 | 0 | 러너 둘을 함께 띄워 한쪽이 둘 다, 다른 쪽이 0 개 | 0 개 | `schema_migrations` |
| 번호 붙인 SQL + 러너(asyncpg) | 오류 0 | 0 | 2 개 | 0 개 | `schema_migrations` |
| Alembic 1.20.1, 동기 env + psycopg | 오류 0 | 0 | `upgrade head` | 변화 없음 | `alembic_version` |
| Alembic 1.20.1, 비동기 env + asyncpg | 오류 0 | 0 | `upgrade head` | 변화 없음 | `alembic_version` |
| yoyo-migrations 9.0.0(같은 SQL 파일) | 오류 3(`reportMissingTypeStubs`, `reportUnknownVariableType` 둘) | 0 | 2 개 | 0 개 | `_yoyo_log`, `_yoyo_migration`, `_yoyo_version`, `yoyo_lock` |

Alembic 은 `alembic.ini` 없이 코드에서 `Config` 를 만들어 불렀고(`migrate_alembic.py`), 판 파일은 손으로 쓴 `op.create_table` 이다. 자동 생성(`--autogenerate`)과 내리기(`downgrade`)는 재지 않았다. SQL 러너의 "함께 띄우기"는 스레드 둘이 같은 데이터베이스에 `pg_advisory_lock` 을 쥐고 도는 것이고, 프로세스 둘이나 컨테이너 둘로는 재지 않았다. 잠금을 뺀 러너와 견주는 갈래가 없어, 한 번씩만 적용된 것이 잠금 덕인지는 가르지 않았다.

### testcontainers

testcontainers 4.15.0 의 `PostgresContainer` 로 `postgres:18-alpine` 을 띄웠다. 이미지는 이미 받아 둔 때다. 가져오는 이름은 `testcontainers.community.postgres` 이고 `testcontainers.postgres` 는 폐기 경고를 내는 옛 이름이다. 생성자의 `driver` 기본값이 `psycopg2` 라 `driver=None` 을 줘야 `postgresql://` 주소가 나온다. `start()` 는 컨테이너를 만들고 `docker exec … psql -c 'select version();'` 이 될 때까지 기다린다. Ryuk 은 그 프로세스의 첫 `start()` 가 함께 띄우는 정리용 컨테이너(`testcontainers/ryuk:0.8.1`)이고 `TESTCONTAINERS_RYUK_DISABLED=true` 로 끈다(이 문단은 코드를 읽었다, `testcontainers/postgres.py`, `testcontainers/community/postgres/__init__.py` 55~100 줄, `testcontainers/core/config.py`).

프로세스 하나가 컨테이너 하나를 띄우는 시간(초)이다. 대조는 같은 이미지를 `docker run -d` 로 띄워 psycopg 의 첫 질의가 답하기까지다. 세 갈래를 번갈아 세 번 돌았다. 프로브가 다시 낸다(실행 `049174`, 시작 때 호스트 CPU 부하 59%).

| 갈래 | 가져오기(import) | 띄워서 준비까지 | 끄기 | 프로세스 전체 |
|---|---|---|---|---|
| 대조: `docker run` 만 | 해당 없음 | 9.44, 12.03, 12.27 | 재지 않았다 | 재지 않았다 |
| testcontainers, Ryuk 켬(기본) | 4.91, 3.67, 2.48 | 13.61, 16.01, 17.08 | 0.61, 1.02, 0.89 | 20.17, 22.56, 21.56 |
| testcontainers, Ryuk 끔 | 2.47, 2.58, 2.42 | 9.61, 13.45, 13.0 | 0.64, 0.72, 0.56 | 13.22, 17.36, 16.59 |

Ryuk 을 켠 회차마다 Ryuk 컨테이너가 하나 떠 있었고 끈 회차에는 없었다(프로브가 `docker ps` 로 센다). 같은 날 앞선 실행 `85f8d5` 는 호스트 CPU 부하가 100% 로 보이던 때였고, `start()` 가 Ryuk 켬에서 70.0, 32.12, 35.66초(첫 회차는 그 실행의 첫 컨테이너였다), Ryuk 끔에서 21.49, 26.64, 24.17초였다. 그 실행에는 대조 갈래가 없었다. 시간은 부하에 따라 두 배 넘게 갈렸으므로 범위로 읽는다.

pytest-xdist 와 함께. `tc_xdist/` 는 세션 범위 픽스처 하나가 컨테이너를 띄우고 시험 서른둘(시험마다 질의 하나와 0.3초 기다림)이 그것을 쓴다. 저장소 루트의 pytest 설정으로 돌렸다. `tools/run_checks.py` 의 pytest 는 `-n <논리 CPU 의 절반>` 이고 이 PC 에서 8 이다(코드를 읽었다, `tools/run_checks.py` 의 `pytest_workers`). 프로브가 다시 낸다.

| 실행 | 띄운 PostgreSQL 컨테이너 | 픽스처가 뜨는 데(초) | pytest 전체(초) |
|---|---|---|---|
| `-n` 없음, 실행 `049174` | 1(프로세스 1) | 8.72 | 29.12 |
| `-n 8`, 실행 `049174` | 8(프로세스 8) | 27.39~30.45 | 50.99 |
| `-n` 없음, 실행 `85f8d5`(부하 100%) | 1(프로세스 1) | 29.09 | 69.56 |
| `-n 8`, 실행 `85f8d5`(부하 100%) | 8(프로세스 8) | 65.36~82.8 | 127.97 |

`-n 8` 이 도는 동안 `docker ps` 에는 `testcontainers-ryuk-<세션>` 컨테이너도 여덟이 보였다(실행 `85f8d5`, 손으로 봤다). testcontainers 의 세션 ID 는 프로세스마다 가져올 때 새로 만드는 값이고 Ryuk 컨테이너의 이름에 든다(코드를 읽었다, `testcontainers/core/labels.py` 7 줄, `testcontainers/core/container.py` 492~499 줄). 컨테이너 하나를 작업자들이 나눠 쓰는 배치(러너가 먼저 하나를 띄우고 주소를 환경 변수로 넘기는 것 등)는 재지 않았다. CI 의 `python` 잡은 `-n` 없이 한 프로세스로 돈다(코드를 읽었다, `.github/workflows/ci.yml`).

### 공식 이미지

지원 중인 주 판(원문을 내려받아 봤다, `https://www.postgresql.org/support/versioning/`, 2026-11-14).

| 주 판 | 지금 판 | 지원 | 첫 판 | 마지막 판 내기 |
|---|---|---|---|---|
| 18 | 18.7 | Yes | 2025-09-25 | 2030-11-14 |
| 17 | 17.12 | Yes | 2024-09-26 | 2029-11-08 |
| 16 | 16.16 | Yes | 2023-09-14 | 2028-11-09 |
| 15 | 15.20 | Yes | 2022-10-13 | 2027-11-11 |
| 14 | 14.25 | Yes | 2021-09-30 | 2026-11-12 |
| 13 | 13.23 | No | 2020-09-24 | 2025-11-13 |

14 는 표의 마지막 판 내기 날짜가 이 측정의 이틀 전이고 표에는 아직 Yes 로 적혀 있었다. 공식 이미지의 태그 목록(원문을 내려받아 봤다, `https://raw.githubusercontent.com/docker-library/official-images/master/library/postgres`)에는 18.7(`latest`), 17.12, 16.16, 15.20, 14.25 와 19rc2 가 있고, 판마다 Debian(trixie, bookworm)과 Alpine(3.24, 3.23) 변형이 있다.

크기. 압축 크기는 Docker Hub 의 태그 API 응답에서 linux/amd64 를 읽었다(원문을 내려받아 봤다, `https://hub.docker.com/v2/repositories/library/postgres/tags/<태그>`, 2026-11-14. 모두 2026-11-12 에 올라온 것이다). 풀린 크기는 `docker image inspect` 의 `Size` 다(프로브가 다시 낸다, 두 태그만).

| 태그 | 압축(linux/amd64) | 풀린 크기 | `postgres --version` |
|---|---|---|---|
| `18`(= `latest`) | 168.5MB | 474MB | 18.7 (Debian 18.7-1.pgdg13+2) |
| `18-alpine` | 120.2MB | 304MB | 18.7 |
| `17` | 167.3MB | 재지 않았다 | |
| `17-alpine` | 117.4MB | 재지 않았다 | |
| `16` | 166.2MB | 재지 않았다 | |
| `16-alpine` | 116.2MB | 재지 않았다 | |
| `15` | 164.2MB | 재지 않았다 | |
| `15-alpine` | 115.4MB | 재지 않았다 | |
| `14` | 163.1MB | 재지 않았다 | |
| `14-alpine` | 114.8MB | 재지 않았다 | |

### GitHub Actions 의 service container

이 PC 에서 띄울 수 없어 재지 못했다. 읽은 것만 적는다.

- 저장소의 CI 에는 지금 service container 가 없다. `python` 잡은 `runs-on: ubuntu-24.04` 에서 러너 위에 바로 `uv run pytest -q` 를 돈다(코드를 읽었다, `.github/workflows/ci.yml`).
- GitHub 문서의 예는 잡의 `services:` 아래에 `image: postgres`, `env: POSTGRES_PASSWORD`, `options: --health-cmd pg_isready …` 를 두고, 잡이 러너 위에서 바로 돌면 `ports: - 5432:5432` 로 열어 `localhost:5432` 로 붙는다. 예의 주석은 service container 와 컨테이너 잡에 리눅스 러너가 있어야 한다고 적는다(원문을 내려받아 봤다, `https://raw.githubusercontent.com/github/docs/main/content/actions/tutorials/use-containerized-services/create-postgresql-service-containers.md`).
- service container 는 CI 에만 있는 것이라, 이 PC 의 `tools/run_checks.py` 와 pre-commit 이 도는 pytest 는 그것으로 PostgreSQL 을 얻지 못한다(위 문서와 `tools/run_checks.py` 를 읽은 어림).

## 재지 못한 것

- GitHub Actions 의 service container 와, CI 러너(ubuntu-24.04)에서의 testcontainers. 이 PC 에서 띄울 수 없다.
- 리눅스 호스트의 testcontainers. 리눅스 갈래의 컨테이너 안에는 Docker 소켓이 없어 돌리지 않았다.
- 부하가 없는 때의 시간. 측정 내내 다른 세션이 같은 PC 와 같은 Docker 데몬을 썼다.
- psycopg 의 `binary` 가 아닌 설치(`psycopg[c]`, 순수 파이썬 + 시스템 libpq). `binary` 휠만 쟀다.
- 성능(질의 지연, 처리량)과 연결 풀의 크기. 조합마다 연결 둘이 다섯 번씩 올리는 한 바퀴만 돌았다.
- 저장소의 기존 시험 전체를 Selector 루프에서 도는 것, 취소된 실행이 stdio MCP 서버를 끄는 길이 Selector 루프에서 그대로인지.
- Alembic 의 자동 생성과 내리기, 여러 프로세스가 함께 띄우는 마이그레이션.
- 다른 마이그레이션 도구(파이썬이 아닌 실행 파일로 오는 것 포함). yoyo-migrations 하나만 더 봤다.
- 17 이하 이미지의 풀린 크기, arm64 이미지와 휠.
- import-linter 계약. `core` 가 DB 라이브러리를 import 하지 못하게 하는 계약(`pyproject.toml` 의 "core knows no filesystem or DB")에 새 드라이버 이름을 더하는 일은 이 프로브의 범위 밖이다.
- 실패로 끝난 조합이 재려던 까닭으로 실패했는지. `run.py` 의 `outcome_text` 는 실패한 조합의 회차를 오류 문구가 비어 있지 않으면 측정으로 센다(코드를 읽었다). 그래서 드라이버와 루프의 조합이 아닌 까닭(데이터베이스에 닿지 못함 등)으로 실패한 회차도 측정으로 세어진다. 위 "조합별 표"의 거부 칸은 오류 문구를 함께 적으므로 읽는 쪽이 그 문구로 가른다. 다시 돌릴 때는 기대하는 오류 문구가 있을 때만 측정으로 세게 고친다(PR 직전 리뷰의 지적, 일지 2026-11-14-2152 "PR 직전 리뷰의 보고와 판정").

## 남긴 것

- 이미지: `admin-login-pg-probe-linux`(603MB, 이 프로브가 지었다. 지우려면 `docker image rm admin-login-pg-probe-linux`). 받은 것은 `postgres:18`, `postgres:18-alpine`, `testcontainers/ryuk:0.8.1` 이다.
- 컨테이너, 네트워크, 볼륨: 없다. 끝에서 `docker ps -a --filter name=admin-login-pg-probe`, `docker ps -a --filter name=testcontainers-ryuk`, `docker network ls --filter name=admin-login-pg-probe` 가 비었다(손으로 봤다). 이름 없는 볼륨 둘이 남아 있으나 2026-11-13 에 만들어진 것이라 이 프로브의 것이 아니다(손으로 봤다, `docker volume inspect`).
