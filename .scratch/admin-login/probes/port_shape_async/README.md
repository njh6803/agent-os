# port_shape_async: 계정 포트의 비동기 모양이 실제 패키지 자리에서 타입 검사, 가져오기 계약, PostgreSQL을 지나는가

admin-login의 설계(ADR 0062 결정 "경로와 층")는 운영자 계정의 포트를 `agent_os.http`가 선언하고 PostgreSQL 구현을 `agent_os.adapters`가 들며, 어댑터는 `agent_os.http`를 가져오지 않고 시그니처로 만족한다고 정한다. 앞선 프로브 `../port_shape/`는 이 모양을 작은 모듈 둘의 동기 메서드로만 쟀다. 그 README의 "재지 못한 것"이 든 비동기 메서드, 실제 `agent_os` 패키지와 import-linter, 드라이버의 타입, 포트가 약속한 예외, 줄 여럿, 테스트 픽스처의 자리를 이 프로브가 저장소 사본에서 잰다. 뒤에 더한 트랜잭션 갈래는 명세(`.scratch/admin-login/spec.md`)의 "한 트랜잭션에 묶을 일"이 정한 모양, 곧 트랜잭션 하나를 여는 메서드가 비동기 문맥 관리자로 작업 객체를 내주는 포트를 같은 자리에서 재고, 줄 잠금과 동시성과 되돌림을 실제 PostgreSQL에서 잰다(아래 "결과: 트랜잭션 갈래"). 여기서는 결정하지 않고 본 것만 적는다. 규약은 `docs/agents/issue-tracker.md`의 "프로브와 근거"다.

근거의 종류는 문장 끝 괄호에 적는다. "프로브가 다시 낸다"는 `run.py`를 다시 돌리면 같은 출력이 나오는 것이고, "손으로 봤다"는 이 프로브를 짓는 동안 원본 출력이나 탐색 스크립트로 한 번 본 것이며, "코드 읽기"는 소스를 읽은 것, "어림"은 재지 않은 판단이다.

## 파일

| 파일 | 하는 일 |
|---|---|
| `run.py` | 측정. 저장소의 `src/agent_os`, `pyproject.toml`, `tools/database_for_tests.py`를 임시 폴더에 복사하고 `tree/`와 `patches/`를 얹어 나무 셋을 지은 뒤 pyright, 타입 우회 검사, import-linter, 런타임을 돈다. 회차의 셈은 `tools/probe_kit.py`의 `Rounds`다. 보는 것과 표지는 그 독스트링이 원천이다 |
| `drive.py` | 런타임 몫. `run.py`가 임시 사본의 `src`를 `PYTHONPATH`에 두고 띄운다. 빈 데이터베이스에 표 `accounts`를 만들고, 임시 사본의 `agent_os.main`에 붙인 조립 함수(`probe_scenario`)로 사례 열을 돌린 뒤 유일 제약 위반의 글(DETAIL 사례)을 본다. 이어 트랜잭션 갈래의 사례(겹침, 되돌림, 연결 반납)를 `WORK` 줄로 찍는다 |
| `tree/clean/` | 임시 사본의 같은 자리에 얹는 모듈. 포트(`http/accounts.py`), core의 예외(`core/conflicts.py`), 어댑터(`adapters/postgres/accounts.py`), 포트 타입을 적은 픽스처(`tests/adapters/test_accounts_probe.py`), strict 대조(`http/_probe_control.py`). 트랜잭션 갈래로 트랜잭션 포트와 작업 객체와 `http`의 판정 함수(`http/account_work.py`), 그 어댑터 두 모양과 잠그지 않는 대조군(`adapters/postgres/account_work.py`), 포트 타입을 적은 픽스처(`tests/adapters/test_account_work_probe.py`) |
| `tree/drift/` | 대조군. 어긋난 어댑터 다섯(`accounts_drift.py`), 포트가 줄 여럿을 `list`로 적은 모양(`http/accounts_list_drift.py`), 칸의 차례를 틀린 읽기 둘(`accounts_order_table.py`, `accounts_order_text.py`), NULL을 받는 칸을 타입 인자 없이 적은 판(`accounts_nullable.py`), 어긋난 어댑터를 포트 타입 자리에 두는 픽스처(`tests/adapters/test_accounts_drift_probe.py`). 트랜잭션 갈래로 어긋난 작업 객체와 문맥 관리자 다섯과 `AsyncIterator`로 적은 판(`adapters/postgres/account_work_drift.py`), 문맥 관리자의 둘째 타입 인자를 `bool`·`None`으로 적은 포트(`http/account_work_exit.py`), 그것을 포트 타입 자리와 작업 객체 타입 자리에 두는 픽스처(`tests/adapters/test_account_work_drift_probe.py`) |
| `tree/violation/` | 양성 대조. 계약을 깨는 가져오기 둘. 어댑터가 `agent_os.http`를, `http`가 SQLAlchemy를 가져온다 |
| `patches/database_imports.txt`, `patches/database_tail.txt` | 저장소의 `adapters/postgres/database.py`에 붙이는 조각. `PostgresDatabase`에 (가)의 메서드 넷과 (나1)의 공개 속성 `engine`, (나3)의 만드는 메서드 `accounts()`를 더한다 |
| `patches/main_tail.txt` | 저장소의 `main.py` 끝에 붙이는 조립. 어댑터를 지어 포트 자리에 넘기는 사례마다의 분기다 |
| `patches/main_drift_tail.txt` | drift 나무의 `main.py`에만 더 붙이는 조립. 어긋난 어댑터를 포트 자리에 넘기는 함수마다 어긋남 하나다 |
| `patches/main_work_tail.txt` | 나무 셋의 `main.py`에 `main_tail.txt` 뒤로 붙이는 트랜잭션 갈래의 조립. 모양마다 어댑터를 지어 트랜잭션 포트 자리에 넘긴다(`probe_transactions`, `probe_attempt` 등) |
| `patches/main_work_drift_tail.txt` | drift 나무의 `main.py`에만 더 붙이는 트랜잭션 갈래의 조립. 어긋난 어댑터를 트랜잭션 포트 자리에 넘기는 함수마다 어긋남 하나다 |
| `escape_control.py` | 타입 우회 검사의 양성 대조(`Any`, `cast`, 억제 주석). 나무에 복사하지 않는다 |

## 다시 돌리기

저장소 루트에서 친다. 테스트 컨테이너가 떠 있어야 하고(`docker compose -f compose.test.yaml up -d --wait`), 네트워크로 내려받는 것은 없다. 2026-11-24 이 PC에서 트랜잭션 갈래 전의 판이 35초와 1분 36초, 그 갈래를 더한 판이 1분 37초와 1분 59초(둘 다 `--dump`)와 54초였다(손으로 봤다, 셸의 `date`). 트랜잭션 갈래의 겹침 사례가 한 번에 0.5초씩 아홉 번 기다린다.

```bash
uv run python .scratch/admin-login/probes/port_shape_async/run.py
```

`--work <절대 경로>`는 임시 폴더를 만들 부모(없으면 시스템 임시 폴더), `--keep`은 임시 폴더를 남기고, `--dump <절대 경로>`는 pyright·import-linter·`drive.py`의 원본 출력을 그 폴더에 쓴다. 지우는 것은 이 프로브가 `mkdtemp`로 새로 만들고 바로 표지 파일(`.port_shape_async_probe`)을 심은 폴더 하나와, `tools/database_for_tests.py`로 만든 데이터베이스 하나뿐이다. 지운 뒤 없어졌는지 본다. 측정이 아닌 회차가 하나라도 있으면 종료 코드가 1이다.

## 잰 판

pyright 1.1.414, import-linter 2.15, grimp 3.17, SQLAlchemy 2.1.9(저장소 잠금 `sqlalchemy[asyncio]>=2.1.8,<3`에 깔린 판), asyncpg 0.32.0, 파이썬 3.12.10, PostgreSQL 18.7(Debian 18.7-1.pgdg13+2, 테스트 컨테이너), 저장소 HEAD `7770ac0c1`이고 복사한 자리에 커밋하지 않은 변경이 없었다(프로브가 찍는다). Windows 10이다. 2026-11-24에 고친 뒤의 판으로 세 번 돌렸다. 첫 번은 NULL 칸 회차(23)와 사슬마다의 글(19)을 결과 줄에 더하기 전이라 47회차였고, 나머지 둘은 48회차였다. 겹치는 회차의 결과는 셋이 같았다(손으로 봤다, 세 실행의 출력을 견줬다).

결과를 본 뒤 바꾼 판정 기준은 둘이고 고친 조립 코드가 하나다(손으로 봤다). 어긋남마다의 낱말은 첫 실행의 원본 출력을 본 뒤 골랐다(결과 9). 칸의 차례를 틀린 `Table` 판은 첫 판이 `reportArgumentType`이 하나라도 나면 잡혔다고 셌는데, 다른 까닭의 오류와 가르려고 원본 출력에서 본 두 낱말(`parameter "name" of type "str"`, `parameter "failures" of type "int"`)이 모두 들어야 잡혔다고 세게 좁혔다. 첫 실행의 조립 쪽 오류 둘(결과 11)은 조립 코드를 고쳐 없앴고, 그 뒤 clean 나무의 오류 0을 결과로 적는다.

트랜잭션 갈래를 더한 판은 같은 날 세 번 돌렸다(손으로 봤다). 판과 HEAD(`7770ac0c1`, 복사한 자리에 커밋하지 않은 변경 없음)는 위와 같다. 첫 번은 80회차, 둘째·셋째 번은 83회차였고 셋 다 측정 아님 0, 종료 0이었다. 겹치는 회차의 결과는 셋이 같았다(셋의 출력을 견줬다). 앞선 48회차는 83회차 안에 모두 들고 결과가 앞선 판과 같았다. 트랜잭션 갈래에서 결과를 본 뒤 바꾼 판정 기준은 넷이다(손으로 봤다).

- 어긋남마다의 낱말은 첫 실행(`--dump`)의 원본 출력을 본 뒤 골랐다. 첫 판은 낱말 없이 규칙만 봤다.
- 첫 판에서 기대 없이 규칙만 적던 여섯(`AsyncIterator`로 적은 판의 어댑터와 조립, 둘째 타입 인자의 넷)은 첫 실행의 출력을 본 뒤 규칙과 낱말을 적거나 오류 0을 적는 대조로 바꿨다. 첫 실행의 규칙은 지금 판의 기대와 같았다.
- 첫 실행에서 작업 객체가 어긋난 셋의 글이 어느 메서드인지 말하지 않는 것을 보고, 작업 객체를 `AccountWork`에 바로 적는 자리 셋(`*_work`)을 더했다(그래서 80에서 83이 됐다). 그 셋의 낱말은 둘째 실행의 원본 출력을 본 뒤 골랐다. 트랜잭션 포트 자리의 글에 그 낱말이 드는지를 결과에 적는 칸(`silent`)도 그때 더했다.
- 런타임의 표지(아래 결과 34~36의 회차를 측정으로 세는 조건, `run.py` 독스트링의 `work`)는 첫 실행 전에 적었고 바꾸지 않았다.

## 결과

트랜잭션 갈래를 더하기 전의 판에서 측정 48회차, 측정 아님 0회차, 종료 코드 0이었다. 지금 판은 이 48회차를 같은 결과로 다시 내고 트랜잭션 갈래의 35회차를 더해 83회차다(프로브가 다시 낸다). 아래 1의 파일 수는 앞선 판의 것이고, 지금 판은 clean 나무 66개, drift 나무 75개를 모두 strict로 분석한다(프로브가 다시 낸다).

### 범위의 표지

1. pyright는 clean 나무의 파일 63개와 drift 나무의 69개를 모두 strict로 분석했다(`filesAnalyzed`가 `[tool.pyright].include` 아래 파일 수와 같다). 대조 파일에서 strict에서만 나는 `reportMissingParameterType`이 났고, 같은 파일의 `reveal_type(AccountStore.find)`가 임시 사본에만 있는 포트를 풀었으며 `reportMissingImports`는 0이었다(프로브가 다시 낸다). 그 `reveal_type`의 전문은 `(self: AccountStore, name: str) -> CoroutineType[Any, Any, AccountRow | None]`였다(손으로 봤다. 프로브는 `AccountRow | None`만 본다).
2. import-linter가 쓰는 import 그래프(grimp)에서 `agent_os`의 자리가 임시 사본이었고, 임시 사본에만 있는 가져오기가 그래프에 있었다(프로브가 다시 낸다).

### 1. 비동기 Protocol 포트와 그것을 가져오지 않는 어댑터

3. clean 나무의 포트, core의 예외, 어댑터, 패치한 `database.py`, 패치한 `main.py`, `server.py`, 포트 타입을 적은 픽스처의 오류는 각각 0이었고, 대조 파일 밖의 오류 합도 0이었다(프로브가 다시 낸다). 곧 다음이 모두 조립 자리(`main.py`)와 픽스처 자리에서 strict를 지났다.
   - 줄 하나: 포트 `async def find(name) -> AccountRow | None`, 어댑터 `-> Row | None`(`Row`는 어댑터의 `frozen` 데이터클래스).
   - 줄 여럿: 포트 `-> Sequence[AccountRow]`, 어댑터 `-> Sequence[Row]`.
   - 아무것도 돌려주지 않는 쓰기: `async def record_failure(name, *, at) -> None`.
   - 이름이 이미 있으면 포트가 약속한 신호를 내는 쓰기 `add`의 갈래 넷(아래 5).
4. 포트를 쓰는 함수(`walk`: 넣기, 실패 두 번 적기, 찾기, 목록, 없는 이름 찾기)가 어댑터를 지나 끝까지 돌았다(5의 런타임, 프로브가 다시 낸다).

'이름이 이미 있음'을 `http`가 알아보는 갈래는 넷이다. 예외 타입을 어디에 두는지가 갈래라서 갈래마다 쟀다.

| 갈래 | 예외(신호)를 두는 자리 | `http`가 알아보는 법 | strict | 런타임 |
|---|---|---|---|---|
| core | `agent_os.core.conflicts.NameTaken`. `http`와 어댑터가 함께 가져온다 | `except NameTaken` | 오류 0 | `taken` |
| 주입 | `agent_os.http.accounts.NameTaken`. 조립이 그 클래스를 어댑터의 생성자(`taken: Callable[[str], Exception]`)에 넘긴다 | `except NameTaken` | 오류 0 | `taken` |
| 알아보기 | 어댑터의 자기 예외 `AdapterNameTaken`. 포트에 `is_name_taken(error) -> bool`을 더한다 | `except Exception` 뒤 `store.is_name_taken(error)`, 아니면 다시 올린다 | 오류 0 | `taken` |
| 값 | 예외 없음. `add`가 `AccountRow \| Literal["taken"]`을 돌려준다 | `== "taken"`으로 좁힌다 | 오류 0 | `taken` |

(표 전체가 프로브가 다시 낸다.)

5. 어댑터가 유일 제약 위반을 옮기지 않는 대조(`UntranslatedAccounts`, SQLAlchemy의 `IntegrityError`를 그대로 올린다)를 예외 갈래 셋(core, 주입, 알아보기)의 자리에 넘긴 조립은 strict를 오류 0으로 지났고, 런타임에서는 셋 모두 `sqlalchemy.exc.IntegrityError`(SQLSTATE 23505)가 `http`의 함수 밖으로 올라왔다(프로브가 다시 낸다). 곧 이 세 갈래에서 '어떤 예외를 던지는가'는 시그니처에 실리지 않아 pyright strict가 보지 못했다. 값 갈래에서 낱말이 어긋난 어댑터(`Literal["exists"]`)는 조립 자리에서 `reportArgumentType`으로 잡혔다(아래 6, 프로브가 다시 낸다).
6. 주입 갈래에서 조립이 `http`가 잡지 않는 다른 예외 클래스를 넘겨도 생성자의 타입(`Callable[[str], Exception]`)은 받는다(코드 읽기, 그런 조립은 돌리지 않았다).

### 2. 어긋난 어댑터

7. 조립 자리(`main.py`)에서 포트 자리에 넘긴 호출과 픽스처 자리(`store: AccountStore = Drift(...)`)에서 어긋남마다 기대한 규칙이 그 함수의 줄 범위에서 났고, 그 글에 어긋난 자리의 낱말이 들었다(프로브가 다시 낸다).

| 어긋남 | 조립 자리 | 픽스처 자리 | 글의 요지 |
|---|---|---|---|
| `find`가 `async`가 아님 | `reportArgumentType` | `reportAssignmentType` | `"find" is an incompatible type`, `(name: str) -> (Row \| None)`이 `CoroutineType[Any, Any, AccountRow \| None]`에 맞지 않음 |
| 돌려주는 줄에 칸 `locked_until`이 없음 | `reportArgumentType` | `reportAssignmentType` | `CoroutineType[Any, Any, ShortRow \| None]`이 `... AccountRow \| None`에 맞지 않음 |
| `find`가 이름을 `bytes`로 받음 | `reportArgumentType` | `reportAssignmentType` | `Parameter 1: type "str" is incompatible with type "bytes"` |
| 값 갈래의 낱말이 `"exists"` | `reportArgumentType` | (재지 않음) | `Literal['exists']`가 `Literal['taken']`에 맞지 않음 |
| 포트가 줄 여럿을 `list[AccountRow]`로 적음 | `reportArgumentType` | (재지 않음) | `CoroutineType[..., list[Row]]`이 `... list[AccountRow]`에 맞지 않음 |
| 대조: 같은 어댑터(`list[Row]`를 돌려준다)를 `Sequence` 포트에 넘김 | 오류 0 | | |

8. 마지막 두 줄로 `list`는 원소의 타입에서 불변이라 포트를 `list[AccountRow]`로 적으면 자기 줄 타입의 `list`를 돌려주는 어댑터가 맞지 않고, `Sequence`로 적으면 맞는다(프로브가 다시 낸다).
9. 어긋남마다의 낱말은 첫 실행(`--dump`)의 원본 출력을 본 뒤 골랐다(손으로 봤다). 그 어긋남이 아니면 글에 나오지 않는 조각(비동기가 아닌 반환, 칸이 없는 줄의 클래스 이름, 인자의 타입, 값의 낱말, 원소 타입)이다.

### 3. 엔진을 받는 모양

| 모양 | 조립 자리 | strict | import-linter | 런타임 |
|---|---|---|---|---|
| (가) `PostgresDatabase` 한 객체가 `Database` 포트와 계정 포트를 함께 만족 | `_probe_both_ports(database, database)`, `walk(database, ...)` | 오류 0 | 모두 KEPT | 끝까지 돌았다, 두 자리의 객체가 같다 |
| (나1) 공개 속성 `engine`을 조립이 별도 어댑터에 넘김 | `PostgresAccounts(database.engine)` | 오류 0 | 모두 KEPT | 끝까지 돌았다 |
| (나2) 비공개 `_engine`을 조립이 꺼냄 | `PostgresAccounts(database._engine)` | `reportPrivateUsage` | (같은 나무의 계약은 따로 재지 않았다) | 돌리지 않았다 |
| (나3) `database.accounts()`가 같은 엔진을 쥔 별도 어댑터를 지어 줌 | `database.accounts()` | 오류 0 | 모두 KEPT | 끝까지 돌았다 |

(표 전체가 프로브가 다시 낸다.)

10. (나1)에서 `main.py`는 `AsyncEngine` 값을 받아 넘기기만 하고 SQLAlchemy를 가져오지 않아 "only the adapters import DB libraries" 계약이 KEPT였다(프로브가 다시 낸다). 이 계약은 가져오기만 보고 값이 지나는 것은 보지 않으며, `allow_indirect_imports = true`라 어댑터를 거쳐 닿는 SQLAlchemy도 막지 않는다(코드 읽기, `pyproject.toml`).
11. 첫 실행에서 strict가 조립 쪽에 오류 둘을 냈다(손으로 봤다). (가)의 자리를 `database is accounts`로 견주자 두 Protocol(`Database`, `AccountStore`)이 겹치지 않는다며 `reportUnnecessaryComparison`이 났고, `main.py`에 붙인 밑줄 시작 함수(`_probe_scenario`, `_drift_*`)를 모듈 안에서 쓰지 않는다며 `reportUnusedFunction`이 났다. 지금 판은 `id`로 견주고 공개 이름을 쓴다.
12. 각 모양이 치르는 값은 코드에서 보인다(코드 읽기). (가)는 포트의 메서드마다 `PostgresDatabase`에 메서드가 하나씩 늘고, 계정 포트만 쓰는 시험도 데이터베이스 어댑터 전체를 짓는다. (나1)은 엔진이 어댑터의 공개 표면이 되어 그 객체를 쥔 쪽 누구나 SQL을 직접 보낼 수 있다. (나3)은 `database.py`가 계정 어댑터 모듈을 가져오고 포트마다 만드는 메서드가 하나씩 는다. 셋 다 엔진을 닫는 것은 `PostgresDatabase.close()` 하나다.

### 4. import-linter(저장소 계약 그대로)

13. clean 나무는 8 kept, 0 broken, 종료 0이었다. core 갈래의 가져오기(어댑터 → `agent_os.core.conflicts`, `http` → 같은 모듈)도 그래프에 있고 계약을 깨지 않았다(프로브가 다시 낸다).
14. violation 나무는 6 kept, 2 broken, 종료 1이었다. 깨진 계약은 "adapters are not an HTTP surface (principle IV, ADR 0016)"과 "only the adapters import DB libraries (principle IV, ADR 0066)"이고, 그 글이 임시 사본에만 있는 가져오기 `agent_os.adapters.postgres.accounts_violation -> agent_os.http.accounts`와 `agent_os.http.accounts_violation -> sqlalchemy`를 들었다(프로브가 다시 낸다). 곧 `http`가 SQLAlchemy의 예외를 직접 잡으려고 가져오면 계약이 깨진다. asyncpg도 같은 계약의 금지 목록에 든다(코드 읽기, `pyproject.toml`).
15. import-linter의 출력은 긴 계약 이름을 줄을 바꿔 감는다(손으로 봤다). 프로브는 공백을 펴서 이름을 맞댄다.

### 5. 실제 PostgreSQL

16. 표 `accounts`(이름에 유일 제약 `accounts_name_key`)를 만들고 (가), (나1), (나3)의 어댑터로 `walk`를 돌렸다. 셋 모두 넣은 이름을 돌려받았고, 실패를 두 번 적은 뒤 `failures`가 2, 잠금 시각이 넣은 시각(`2026-11-24T09:00:00+00:00`) 그대로 돌아왔으며, 목록에 넣은 이름이 있고 없는 이름의 찾기는 `None`이었다(프로브가 다시 낸다).
17. 같은 이름을 두 번 넣으면 갈래 넷 모두 `http`의 함수가 `taken`을 냈다. 어댑터는 예외의 클래스가 아니라 원인 사슬에서 SQLSTATE `23505`를 찾아 알아보고, 포트의 신호는 `except` 밖에서 낸다(프로브가 다시 낸다, 알아보는 법은 코드 읽기).
18. 유일 제약 위반의 원인 사슬은 `sqlalchemy.exc.IntegrityError` → `sqlalchemy.dialects.postgresql.asyncpg.UniqueViolationError` → `asyncpg.exceptions.UniqueViolationError`였다(프로브가 다시 낸다).
19. DETAIL이 값을 드러내는지. 넣은 이름은 실행마다 무작위로 지어 소스에 나오지 않는다.
    - 저장소 엔진(`hide_parameters=True`)이 낸 `IntegrityError`의 글에는 넣은 이름도 `DETAIL` 낱말도 없었다. 글은 제약 이름, SQL 문, `[SQL parameters hidden due to hide_parameters=True]`였다(프로브가 다시 낸다).
    - 사슬의 두 항목이 지닌 `detail` 속성은 `Key (name)=(<넣은 이름>) already exists.`였다(프로브가 다시 낸다).
    - 사슬마다의 `str`은 맨 끝의 asyncpg 예외만 넣은 이름을 실었다(`[False, False, True]`, 프로브가 다시 낸다). 그래서 그 `IntegrityError`를 원인으로 이은 예외의 역추적(`traceback.format_exception`)에도 넣은 이름이 실렸다(프로브가 다시 낸다). 옮기지 않은 `IntegrityError`를 역추적과 함께 기록하는 길은 넣으려던 값을 기록에 싣는다(어림. 기록하는 코드는 재지 않았다). 저장소의 `database.py` 독스트링도 같은 한계를 적는다(코드 읽기).
    - 포트의 신호로 옮긴 예외(core 갈래)는 원인(`__cause__`)과 문맥(`__context__`)이 모두 `None`이었고, 그 역추적에 넣은 이름이 없었으며, 글은 `이름이 이미 있다`였다(프로브가 다시 낸다).
20. 시험 데이터베이스는 끝에 지웠고 없어진 것을 봤다. 임시 폴더도 지웠다(프로브가 다시 낸다).

### 쿼리를 `Table`로 둘지 `text()`로 둘지

21. 칸을 모듈 수준의 `Column` 객체로 이름에 묶은 `Table`에서 `select(NAME, TIER, ...)`의 행은 `Row[str, str, str | None, int, datetime | None]`처럼 칸마다 타입을 지녔다. 칸의 차례를 틀려 풀자 줄을 짓는 자리에서 `reportArgumentType` 둘(`parameter "name" of type "str"`, `parameter "failures" of type "int"`)이 났다(프로브가 다시 낸다).
22. 같은 읽기를 `text()`로 쓰면 행이 `Row[*tuple[Any, ...]]`이고 차례를 틀려도 오류가 0이었다(프로브가 다시 낸다). 이 `Any`는 소스에 `Any`라고 적지 않아 타입 우회 검사(`tools/check_type_escapes.py`)도 잡지 않았다(프로브가 다시 낸다. 그 파일을 포함한 20개에서 우회 0건).
23. NULL을 받는 칸을 타입 인자 없이 `Column("password_hash", Text, nullable=True)`로 적으면 `select`가 그 칸을 `Select[str]`로 풀어 `None`을 품지 않았다(프로브가 다시 낸다). `Column[str | None]`으로 적은 칸은 `str | None`으로 풀렸다(21의 행 타입, 프로브가 다시 낸다).
24. 행을 속성(`row.name`)으로 읽으면 `Any`이고, `accounts.c.name`처럼 표에서 꺼낸 칸은 `Column[Any]`이었다(손으로 봤다, 탐색 스크립트). 그래서 이 프로브는 칸을 모듈 수준의 타입 붙은 `Column`으로 두고 행을 풀어 읽는다.
25. `insert(...).values(...)`와 `update(...).values(...)`의 키워드는 `**kwargs: Any`라 쓰기의 칸 이름과 값의 타입은 타입 검사가 보지 않는다(코드 읽기, SQLAlchemy 2.1.9 `sql/dml.py`).
26. `Table`의 정의와 실제 표의 정의(이 프로브는 `drive.py`의 DDL)는 따로 적혀, 둘이 어긋나는 것은 타입 검사가 보지 못한다(어림, 어긋난 판은 돌리지 않았다). 이 프로브의 `Table`은 DDL의 `id` 칸을 적지 않았는데도 돌았다(프로브가 다시 낸다).

## 결과: 트랜잭션 갈래

명세의 "한 트랜잭션에 묶을 일"이 정한 모양을 잰다. 포트(`AccountTransactions`)의 메서드는 `def transaction(self) -> AbstractAsyncContextManager[AccountWork]` 하나다. 작업 객체(`AccountWork`)는 줄을 잠가 읽는 `async def lock(name) -> AccountRow | None`과 횟수와 잠금 시각을 적는 `async def write_failures(name, *, failures, locked_until) -> None`을 가진다. 판정(몇 번째에 잠그는지)은 `http`의 함수 `record_failed_attempt`가 하고, 그 함수는 블록 안에서 잠가 읽고, 견주고(`compare`), 적는다. 83회차 가운데 35회차가 이 갈래이고 모두 측정이었다(프로브가 다시 낸다).

### 6. 타입 모양

27. pyright는 포트의 반환을 `AbstractAsyncContextManager[AccountWork, bool | None]`로 풀었다(프로브가 다시 낸다, 대조 파일의 `reveal_type`). 둘째 타입 인자(`__aexit__`의 반환)를 적지 않으면 `bool | None`이 된다(코드 읽기, 번들 typeshed `contextlib.pyi` 31행의 `_ExitT_co` 기본값).
28. clean 나무의 트랜잭션 포트(`http/account_work.py`), 어댑터(`adapters/postgres/account_work.py`), 픽스처(`tests/adapters/test_account_work_probe.py`), 패치한 `main.py`의 오류가 각각 0이었고 대조 파일 밖의 오류 합도 0이었다. 타입 우회 검사는 더하거나 고친 29개 파일에서 0건이었다(프로브가 다시 낸다). 곧 어댑터가 `agent_os.http`를 가져오지 않은 채 다음 두 모양이 조립 자리(`probe_transactions`의 포트 타입 반환, `probe_attempt`의 인자)와 픽스처 자리(`store: AccountTransactions = ...`)에서 strict를 지났다.
    - `ContextTransactions`: `@asynccontextmanager`로 지은 메서드 `async def transaction(self) -> AsyncGenerator[PgWork]`가 `engine.begin()` 안에서 작업 객체를 내준다.
    - `ClassTransactions`: 메서드가 `__aenter__ -> PgWork`와 `__aexit__ -> None`을 가진 클래스를 돌려준다. `__aexit__`는 예외가 없으면 적고(commit) 있으면 되돌린 뒤(rollback) 연결을 닫는다.
    - 두 모양 모두 작업 객체 `PgWork.lock`은 `-> Row | None`(어댑터의 데이터클래스)이고 포트는 `-> AccountRow | None`이다.
29. import-linter는 clean 나무에서 8 kept, 0 broken이었다. grimp 그래프에 `agent_os.adapters.postgres.account_work → sqlalchemy`, `agent_os.main → agent_os.adapters.postgres.account_work`, `agent_os.main → agent_os.http.account_work`가 있었고, 어댑터에서 `agent_os.http.account_work`와 `agent_os.http.accounts`로 가는 가져오기는 없었다(프로브가 다시 낸다).

어긋난 어댑터는 다음과 같이 잡혔다. 낱말은 "잰 판"의 둘째 단락대로 원본 출력을 본 뒤 골랐다.

| 어긋남 | 조립 자리 | 픽스처 자리 | 작업 객체 자리(`work: AccountWork = ...`) | 글의 요지 |
|---|---|---|---|---|
| `@asynccontextmanager`를 빠뜨림 | `reportArgumentType` | `reportAssignmentType` | (해당 없음) | `"AsyncGenerator[PgWork, None]" is incompatible with protocol "AbstractAsyncContextManager[AccountWork, bool \| None]"` |
| 작업 객체의 `lock`이 비동기가 아님 | `reportArgumentType` | (재지 않음) | `reportAssignmentType` | 트랜잭션 자리는 `_AsyncGeneratorContextManager[SyncLockWork, None]`이 맞지 않다는 데서 끝남. 작업 객체 자리는 `"lock" is an incompatible type`, `(name: str) -> (Row \| None)` |
| 작업 객체에 `write_failures`가 없음 | `reportArgumentType` | `reportAssignmentType` | `reportAssignmentType` | 트랜잭션 자리는 `[LockOnlyWork, None]`에서 끝남. 작업 객체 자리는 `"write_failures" is not present` |
| `write_failures`가 횟수를 `str`로 받음 | `reportArgumentType` | (재지 않음) | `reportAssignmentType` | 트랜잭션 자리는 `[TextFailuresWork, None]`에서 끝남. 작업 객체 자리는 `Keyword parameter "failures" of type "int" is incompatible with type "str"` |
| 클래스 모양의 `__aenter__`가 작업 객체 대신 자기를 돌려줌 | `reportArgumentType` | `reportAssignmentType` | (해당 없음) | `"SelfEnterTransaction" is incompatible with protocol "AbstractAsyncContextManager[AccountWork, bool \| None]"` |

(표 전체가 프로브가 다시 낸다. 조립 자리와 픽스처 자리의 글에는 모두 `"transaction" is an incompatible type`이 들었다.)

30. 작업 객체가 어긋난 셋에서, 트랜잭션 포트 자리의 글은 문맥 관리자의 타입(그 안의 작업 객체 클래스 이름)이 맞지 않는다는 데서 끝나고 어느 메서드가 왜 어긋났는지 적지 않았다. 조립 셋과 픽스처 하나 모두 "어긋난 메서드의 글 없음"이었다(프로브가 다시 낸다). 그 글은 머리 줄 아래 다섯 겹이었다(손으로 봤다, 첫 실행 `--dump`의 `pyright_drift.json`). pyright가 글의 겹을 정해진 깊이에서 자르는 것인지는 재지 않았다(어림). 같은 작업 객체를 `AccountWork` 타입 자리에 바로 적으면 메서드 이름과 까닭이 나왔다(프로브가 다시 낸다).

### 7. 적는 법의 갈래(`__aexit__`의 반환 타입, `AsyncIterator`)

| 갈래 | 자리 | 결과 |
|---|---|---|
| `@asynccontextmanager` 메서드의 반환을 `AsyncIterator[PgWork]`로 적음 | 어댑터 클래스 | `reportDeprecated`(오류). 글은 `` Annotating the return type as `-> AsyncIterator[Foo]` with `@asynccontextmanager` is deprecated. Use `-> AsyncGenerator[Foo]` instead. `` |
| 위 어댑터를 트랜잭션 포트 자리에 넘김(대조) | 조립 | 오류 0 |
| 포트의 둘째 인자를 `None`으로 적음(`AbstractAsyncContextManager[AccountWork, None]`), `@asynccontextmanager` 어댑터를 넘김 | 조립 | `reportArgumentType`. `"_AsyncGeneratorContextManager[PgWork, None]" is not assignable to "AbstractAsyncContextManager[AccountWork, None]"` |
| 같은 `None` 포트에 클래스 어댑터(`__aexit__ -> None`)를 넘김(대조) | 조립 | 오류 0 |
| 기본(`bool \| None`) 포트에서, 블록 안에서 지은 이름을 블록 뒤에서 씀(대조) | 포트 쪽 함수 | 오류 0 |
| 둘째 인자를 `bool`로 적은 포트에서, 같은 함수 | 포트 쪽 함수 | `reportPossiblyUnboundVariable`. `"failures" is possibly unbound` |

(표 전체가 프로브가 다시 낸다.)

31. 마지막 두 줄로, pyright strict는 `__aexit__`가 `bool`을 돌려주는 문맥 관리자를 블록의 예외를 삼킬 수 있는 것으로 보아 블록 뒤에서 블록 안의 이름을 묶이지 않았을 수 있다고 봤고, 기본(`bool | None`)은 그렇게 보지 않았다(프로브가 다시 낸다). 기본으로 적은 포트에서는 블록 안에서 `return`하지 않고 블록 뒤에서 값을 써도 strict가 오류를 내지 않는다.
32. 포트를 `None`으로 적으면 `@asynccontextmanager` 어댑터가 맞지 않았다(프로브가 다시 낸다). `_AsyncGeneratorContextManager`의 `__aexit__`가 `bool | None`을 돌려주기 때문이다(코드 읽기, `contextlib.pyi` 101~108행). 기본으로 적으면 두 모양이 모두 맞는다(결과 28).
33. `AsyncIterator`로 적은 판은 번들 typeshed의 `asynccontextmanager` 겹침 가운데 `@deprecated`가 붙은 쪽에 맞고(코드 읽기, `contextlib.pyi` 112~117행), strict가 그 자리를 오류로 냈다(프로브가 다시 낸다). 포트를 만족하는지는 다르지 않았다(조립 오류 0, 프로브가 다시 낸다).

### 8. 줄 잠금, 겹침, 되돌림(실제 PostgreSQL)

34. 겹침 사례의 짜임(`drive.py`의 `overlap`). 한 계정(실패 0번)에 `record_failed_attempt` 둘을 한 이벤트 루프에서 함께 돌린다. 첫째는 줄을 읽은 뒤 견줌의 자리에서 0.5초를 기다리고, 둘째는 첫째가 읽은 뒤에 트랜잭션을 연다. 그동안 셋째 연결(AUTOCOMMIT)이 0.05초마다 `pg_locks`와 `pg_stat_activity`를 이어 이 데이터베이스에서 기다리는 잠금을 훑는다. 모양마다 세 번, 실행 하나에 아홉 번이다(코드 읽기).

| 모양 | 적은 횟수(첫째, 둘째, 끝) | 둘째가 트랜잭션을 연 뒤 읽기를 받기까지 | 훑은 기다림 |
|---|---|---|---|
| `@asynccontextmanager`, `FOR UPDATE` | 1, 2, 2 | 0.505~0.531초 | `transactionid`의 `ShareLock`, `wait_event_type` `Lock`, 기다린 연결의 문장에 `FOR UPDATE`. 표본 6~9개 |
| 클래스, `FOR UPDATE` | 1, 2, 2 | 0.478~0.522초 | 같음. 표본 8~9개 |
| 대조: 잠그지 않음(`SELECT` 뒤 읽은 값에 1을 더해 `UPDATE`) | 1, 1, 1 | 0.010~0.040초 | 없음(표본 0개) |

(회차마다의 값은 프로브가 다시 낸다. 범위는 세 실행의 스물일곱 회차를 견준 것이다, 손으로 봤다.)

35. 줄을 잠그는 두 모양 모두, 둘째 시도는 첫째의 트랜잭션이 끝날 때까지 `FOR UPDATE` 읽기에서 기다렸다. 그 뒤 첫째가 적은 1을 읽어 2를 적었고 끝 횟수가 2였다(프로브가 다시 낸다). 잠그지 않는 대조는 같은 짜임에서 두 시도가 모두 0을 읽고 1을 적어 끝 횟수가 1이었다. 실패 한 번을 잃었다(프로브가 다시 낸다). 둘째는 첫째가 끝나기 전에 읽고 적고 끝났다(둘째 끝 0.02~0.07초, 첫째 끝 0.52~0.56초, 손으로 봤다, 세 실행의 출력).
36. 되돌림. 두 모양 모두, 횟수 0에 5를 더해 적고 같은 트랜잭션에서 다시 읽은 값이 5였다(쓰기가 났다는 표지). 그 뒤 낸 예외(`AbortedAfterWrite`)는 블록과 `http`의 함수 밖으로 나왔고, 새 트랜잭션에서 읽은 횟수는 0이었다(프로브가 다시 낸다). 대조(예외 없이 블록을 나옴)는 5를 돌려받았고 새 트랜잭션에서도 5였다(프로브가 다시 낸다).
37. 사례를 다 돈 뒤 저장소 엔진의 연결 묶음(`AsyncAdaptedQueuePool`)에서 빌려 간 채인 연결은 0이었다(프로브가 다시 낸다). 일부러 돌려주지 않은 연결이 이 수에 잡히는지는 재지 않았다(양성 대조 없음).
38. 저장소 엔진은 연결 묶음의 클래스를 정하지 않아 기본 묶음을 쓴다(코드 읽기, `database.py`의 `create_async_engine` 인자). 두 시도는 연결 둘을 함께 빌렸고, 잠근 모양의 둘째가 기다린 것이 연결 묶음이 아니라 줄 잠금이었다는 것은 훑은 기다림(`transactionid`, `FOR UPDATE`)과 같은 짜임의 대조가 기다리지 않은 것으로 가른다(프로브가 다시 낸다).

## 해석의 갈래와 대조

- "임시 사본을 분석했다"의 양성 대조는 임시 사본에만 있는 포트를 푼 `reveal_type`과 임시 사본에만 있는 가져오기가 든 grimp 그래프다. 가져오기가 풀리지 않았다면 그 줄 대신 `reportMissingImports`가 나고 그래프에 그 모듈이 없다.
- "strict로 분석했다"의 양성 대조는 strict에서만 나는 `reportMissingParameterType`이다.
- "어긋남을 잡았다"는 기대한 규칙만이 아니라 그 함수의 줄 범위와 어긋난 자리의 낱말까지 본다. 대조(같은 어댑터를 `Sequence` 포트에)는 오류 0이어서, `list` 포트의 오류가 어댑터 자체의 다른 문제가 아니라 포트의 `list`에서 온 것을 가른다.
- "import-linter가 계약을 지킨다"의 양성 대조는 violation 나무다. 같은 계약이 임시 사본의 가져오기를 들어 깨졌으므로 clean 나무의 KEPT가 계약이 이 모듈을 보지 않아서가 아님을 가른다.
- "예외 갈래는 타입 검사가 보지 못한다"는 옮기지 않는 어댑터를 넘긴 조립의 오류 0과 그 조립의 런타임 `IntegrityError`로 본다. 같은 어댑터가 런타임에 `taken`을 냈다면 해석이 틀린 것인데 그렇지 않았다. 값 갈래는 낱말이 어긋난 어댑터가 잡히는 것이 양성 대조다.
- "포트의 예외에 값이 실리지 않는다"의 양성 대조는 원인을 이은 예외의 역추적에 넣은 이름이 실린 것이다. 같은 무작위 이름 방식으로 실리는 길이 실제로 보였으므로, 포트 예외의 역추적에 없는 것이 찾는 방식의 탓이 아니다.
- "`text()`가 `Any` 행을 낸다"의 대조는 같은 차례 틀림을 `Table`로 쓴 판이 잡힌 것이다.
- "줄 잠금이 둘째 시도를 기다리게 해 횟수가 2가 됐다"에는 다른 해석이 둘 있다. 두 트랜잭션이 겹치지 않았다(둘째가 첫째가 끝난 뒤에 읽었다)는 해석과, 연결 묶음이 둘째를 기다리게 했다는 해석이다. 앞의 것은 같은 짜임에서 잠그지 않는 대조가 한 번을 잃은 것(겹침이 실제로 났다는 양성 대조)으로, 뒤의 것은 훑은 기다림이 `FOR UPDATE` 문장의 `transactionid` 잠금이었고 대조의 둘째는 0.04초 안에 읽은 것으로 가른다. 잠근 모양의 회차는 그 기다림을 훑었고 둘째가 0.25초(0.5초의 절반) 넘게 기다렸을 때만, 대조의 회차는 두 시도가 모두 1을 적어 끝이 1이고 둘째가 첫째가 끝나기 전에 읽었을 때만 측정으로 센다.
- "예외가 나면 되돌린다"에는 쓰기가 아예 나지 않았다는 해석과 새 트랜잭션의 읽기가 늘 0을 낸다는 해석이 있다. 앞의 것은 같은 트랜잭션의 다시 읽기가 5였던 것(그 회차를 측정으로 세는 조건)으로, 뒤의 것은 예외 없이 나온 대조가 새 트랜잭션에서 5를 읽은 것으로 가른다.
- "기본 둘째 인자는 블록 뒤를 묶이지 않은 자리로 보지 않는다"의 양성 대조는 둘째 인자를 `bool`로 적은 포트의 같은 함수에서 `reportPossiblyUnboundVariable`이 난 것이다. 그래서 기본 판의 오류 0이 pyright가 이 흐름을 보지 않아서가 아니다.
- "트랜잭션 포트 자리의 글이 어긋난 메서드를 말하지 않는다"의 양성 대조는 같은 작업 객체를 `AccountWork` 자리에 적은 판의 글에 그 낱말이 든 것이다. 그래서 '없음'이 찾는 낱말을 잘못 골라서가 아니다.
- "`None` 포트가 `@asynccontextmanager` 어댑터를 받지 않는다"의 대조는 같은 포트가 클래스 어댑터를 오류 0으로 받은 것이다. 그래서 오류가 포트를 잘못 적어서가 아니라 어댑터의 `__aexit__` 반환에서 온다.

## 재지 못한 것

- `create_app`과 라우터·미들웨어가 포트를 받는 자리. 조립은 `main.py` 끝에 붙인 함수로만 봤다.
- pytest로 픽스처를 실제로 돌리는 것. 픽스처의 자리는 타입 검사만 봤다.
- 리눅스, pyright·import-linter·SQLAlchemy·asyncpg의 다른 판, 다른 타입 검사기.
- 같은 이름을 동시에 넣기. 동시성과 줄 잠금은 트랜잭션 갈래가 실패 적기 둘의 겹침으로만 쟀다(결과 34~35).
- 트랜잭션 갈래의 겹침에서, 시도가 셋 이상인 겹침, READ COMMITTED 밖의 격리 수준, 잠금을 기다리다 끝나는 제한 시간(`lock_timeout`), 교착, 없는 이름을 `FOR UPDATE`로 읽을 때(잠글 줄이 없다).
- 블록 안에서 작업이 취소될 때(`asyncio.CancelledError`, 요청이 끊김)의 되돌림과 연결 반납. 되돌림은 `Exception`의 하위 예외 하나로만 쟀다.
- 견줌의 자리는 `asyncio.sleep`이다. 실제 비밀번호 해시 견줌(CPU 일, 스레드로 넘기는지)은 이 프로브가 재지 않는다.
- 연결 반납(결과 37)의 양성 대조. 일부러 돌려주지 않은 연결이 그 수에 잡히는지.
- 작업 객체를 블록 밖으로 들고 나가 쓰는 잘못(블록 뒤의 `work.lock`)을 타입 검사가 막는지. 막지 못할 것으로 본다(어림, 그런 판은 돌리지 않았다).
- 트랜잭션 갈래의 픽스처 자리에서 `lock`이 비동기가 아닌 판과 횟수를 `str`로 받는 판(표의 "재지 않음").
- 예외를 내장 예외(`ValueError` 등)로 두는 갈래와, 예외를 `agent_os.sdk`에 두는 갈래.
- 주입 갈래에서 조립이 다른 예외 클래스를 넘기는 어긋남(6, 코드 읽기만).
- 값 갈래에서 `taken`으로 좁히지 않고 줄의 칸을 읽는 호출이 strict에서 잡히는지.
- (나2)의 나무에 대한 import-linter와 런타임.
- 옮기지 않은 `IntegrityError`가 실제 로그 설정(`logging`의 `exception`)에서 값을 싣는지(19의 넷째 줄은 `traceback.format_exception`으로만 봤다).
- `Table` 정의와 실제 표가 어긋난 판(26).
