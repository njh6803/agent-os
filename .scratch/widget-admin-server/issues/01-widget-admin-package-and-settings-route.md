# 01: 위젯 관리 서버가 둘째 설치 묶음으로 서고, 표에 넣은 위젯 설정이 `/widget-settings/<사이트 이름>`에서 토큰 없이 읽힌다

**What to build:** 저장소에 둘째 설치 묶음 `widget-admin`(패키지 `widget_admin`, 멤버 폴더 `widget-admin/`)이 선다. 설치 묶음은 파이썬 프로그램을 깔 때 쓰는 단위(휠)이고, 지금은 루트 `pyproject.toml` 하나가 `agent-os` 묶음 하나를 짓는다. 개발 세션이 `uv sync --frozen` 한 줄을 치면 두 묶음이 모두 깔리고(사용자 이야기 37), ruff와 pyright와 타입 우회 검사가 멤버의 코드도 보며(38), 두 패키지가 서로를 import하면 `lint-imports`가 빨개진다(39). 위젯 관리 서버의 시험은 같은 테스트 컨테이너에서 자기 접두의 데이터베이스(`widget_admin_test_…`)를 받아 Agent OS의 시험과 서로의 줄에 닿지 않는다(40). 시험이 그 데이터베이스에 위젯 설정 한 줄을 SQL로 넣고 앱을 짓는 함수로 지은 앱의 `GET /widget-settings/<이름>`을 부르면, 그 값이 판 표시 `schema_version: 1`과 열아홉 열쇠로 실리고 값이 없는 칸은 `null`이다. 예외는 둘이라, 예시 질문은 값이 없으면 빈 목록 `[]`이고 밝기 스위치 숨기기는 값이 없으면 `false`다(1, 3, 34, 35). 등록되지 않은 이름과 꼴이 틀린 이름은 같은 404 봉투이고, 데이터베이스가 답하지 못하면 500 봉투라 둘이 갈린다(4, 5, 6). 봉투는 오류 답의 정해진 꼴 `{code, message, violations, request_id}`이고 Agent OS의 것과 같다. 그 접두사 아래의 답에는 다른 출처에 여는 머리 셋(`Access-Control-Allow-Origin: *`, `Access-Control-Expose-Headers: X-Request-Id`, `Cache-Control: no-store`)이 붙는다(2, 7, 8). 표 `sites`와 첫 마이그레이션 `0001_sites`가 서고, 사이트 이름이 표에서 하나뿐이라는 제약과 봉투와 접두사의 관례가 Agent OS와 같은 꼴로 선다(28~31, 33). 계약 파일 `widget-admin/openapi.json`이 코드와 어긋나면 커밋 때 빨개지고(41의 계약 몫), 판 번호 시험이 멤버의 판도 본다(42). 명령(`widget-admin serve`, `widget-admin migrate`)은 아직 없다(03).

이 티켓이 이 기능의 계약을 세우고 02와 03을 막는다(기능 계획 본문, 명세 "티켓을 나눌 때 함께 둘 것"의 첫째). 루트 `pyproject.toml`에 워크스페이스를 더하는 순간 지금 꼴의 serve 이미지가 지어지지 않으므로, serve 이미지의 멤버 파일도 이 티켓이 싣는다(명세 "이미지", 명세 검토 B1).

근거는 명세 `.scratch/widget-admin-server/spec.md`의 "설치 묶음과 패키지와 명령", "검사 도구의 자리", "경계 검사", "판 번호와 출시"의 판 번호와 `PRODUCT_PATHS` 항목, "연결 문자열과 시작"의 엔진 설정과 데이터베이스 객체와 앱을 짓는 자리와 `/health`, "경로의 접두사", "사이트 이름의 꼴", "읽는 경로", "응답 머리", "요청 수", "답의 모양", "판 표시", "표", "마이그레이션과 표를 올리는 때", "오류 봉투와 기록", "계약 파일과 생성 클라이언트"의 계약 파일 항목, "시험 폴더와 도우미", "이미지"의 serve 이미지 항목, "노트 검사와 저장소 상태 시험"의 마이그레이션 폴더 항목, "문서와 하네스"에서 첫 변경이 싣는 것, Testing Decisions의 첫째 이음매다. 결정은 ADR 0064와 ADR 0066이다. 측정은 `.scratch/widget-admin-server/probes/uv_workspace/`다. 이 티켓의 "명세 검토"와 그 번호(B1, S5 같은 것)는 일지 `docs/journal/2026-11-24-2305-widget-admin-server-tickets.md`의 "명세 검토" 절을 가리킨다.

이 티켓이 넷 가운데 가장 크다. 세션이 도중에 인계되면 아래 묶음 단위로 끊는다. 다만 루트 `pyproject.toml`의 워크스페이스와 serve 이미지의 멤버 파일은 한 커밋에 들어가야 하고, 그 커밋은 멤버의 코드와 시험을 함께 담는다(묶음과 검사 설정만 먼저 싣지 않는 까닭은 명세 같은 절).

**Blocked by:** None (can start immediately)

**Status:** done

### 설치 묶음과 검사 도구

- [x] 멤버 `widget-admin/pyproject.toml`이 명세 "설치 묶음과 패키지와 명령"대로다. 판 `0.0.0`, 파이썬 `==3.12.*`, hatchling, src 레이아웃의 `widget-admin/src/widget_admin/`, 런타임 의존성 여섯의 범위는 루트의 같은 이름 줄과 같은 글자다. 개발 의존성은 멤버에 두지 않는다
- [x] 루트 `pyproject.toml`의 여섯 자리를 고친다. 워크스페이스의 멤버와 원천, 개발 묶음의 멤버, ruff의 `src`, pyright의 `include`, pyright의 `extraPaths`(`src`와 `widget-admin/src`를 함께), import-linter의 `root_packages`와 독립 계약 `agent_os and widget_admin are independent (ADR 0064)`이다. 독립 계약은 import-linter의 규칙 종류(`independence`)로, 대상 패키지끼리 곧바로든 다른 모듈을 거쳐서든 서로를 import하지 못하게 막는다(명세 "검사 도구의 자리", "경계 검사")
- [x] `uv lock` 뒤 잠금에 더해진 항목이 `widget-admin 0.0.0` 하나인지 보고, `uv lock --check`와 `uv sync --frozen`이 0이며 `widget_admin`이 편집 가능한 꼴로 깔린 것을 일지에 적는다
- [x] 멤버 안의 모듈 하나에 `agent_os`의 import를 잠깐 넣어 `uv run lint-imports`가 독립 계약으로 빨개지는 것을 한 번 보고 되돌린 결과를 일지에 적는다. 반대 방향(`agent_os`가 `widget_admin`을 import)도 같다. 이 확인은 저장소 시험으로 두지 않는다(명세 Testing Decisions "경계")
- [x] 루트 `pyproject.toml`을 읽어 위 여섯 자리(독립 계약은 종류와 대상 둘까지)가 있는지 보는 저장소 상태 시험과, 그 자리 하나를 뺀 설정을 잡는 변이 시험을 둔다(명세 Testing Decisions "경계", 명세 검토 S11, `.claude/rules/tests.md`의 저장소 상태 검사 항목)
- [x] `ruff check --show-files .`의 목록에 멤버의 `.py`와 `tests/widget_admin/`의 파일이 드는 것을 손으로 한 번 보고 일지에 적는다(명세 "검사 도구의 자리"의 ruff 항목)

### 판 번호와 출시 목록의 한 줄

- [x] 판 번호 시험(`tests/test_repo_version.py`)에 셋을 더한다. 멤버 `pyproject.toml`의 판, 잠금 파일의 `widget-admin` 항목, `widget-admin/openapi.json`의 `info.version`이 모두 `0.0.0`이다(명세 "판 번호와 출시")
- [x] `tools/release.py`의 `PRODUCT_PATHS`에 `widget-admin`을 더한다. 노트 검사가 같은 목록을 쓰는지 다시 보고, 그 목록을 맞대는 시험이 있으면 함께 고친다(명세 "판 번호와 출시"의 첫 항목, 명세 검토 S9)

### 데이터베이스 객체와 표

- [x] 데이터베이스를 다루는 모듈 하나가 연결 문자열로 엔진을 짓고(`hide_parameters=True`, `pool_pre_ping`), 표를 마지막 판까지 올리고, 위젯 설정을 읽고, 닫는다. 앱을 짓는 함수가 그 객체를 기본값 없는 인자로 받는다. 연결 문자열의 판정과 뜰 때의 확인·다시 시도와 판 견줌은 03이 더한다(명세 "연결 문자열과 시작"의 위젯 관리 서버 항목, 명세 검토 S1)
- [x] 마이그레이션 파일과 적용하는 코드는 `widget_admin` 패키지 안에 두고, 꼴은 postgres-foundation 명세 "마이그레이션 파일"과 같다. 첫 파일은 `0001_sites`이고 명세 "표"대로 `sites`를 짓는다(열쇠, 이름의 꼴 제약, 열아홉 칸의 형과 제약, 제약 이름 `sites_<열>_check`)
- [x] 시험 폴더 `tests/widget_admin/`의 `conftest.py`가 `tests/database.py`의 픽스처 함수에 자기 마이그레이션을 올리는 함수와 접두 `widget_admin`을 넘긴다. 시험이 연 데이터베이스 객체는 픽스처가 닫는다. 닫지 않은 엔진이 경고를 내는지 보고(명세 검토 "확인하지 못한 것"), 경고가 나면 닫는 자리를 고친다
- [x] 마이그레이션 폴더의 꼴 시험(`tests/test_postgres_migration_shape.py`)이 두 제품 폴더를 모두 훑고, 폴더마다 파일이 하나 이상인지 본다(명세 "노트 검사와 저장소 상태 시험"). 지금 그 시험은 Agent OS 쪽 폴더 하나를 노트 검사의 `PRODUCT_MIGRATIONS`(`tools/check_notes.py`)에서 읽는다. 노트 검사에 위젯 쪽 폴더를 더하는 일은 04가 하므로(명세 "티켓을 나눌 때 함께 둘 것": 배포의 변경 전까지는 위젯 쪽 표를 올리는 운영자가 없어 백업을 알릴 대상이 없다. 이 티켓에서 켜면 위젯 쪽 첫 마이그레이션을 더하는 이 티켓의 PR 제목에도 느낌표가 붙어야 한다), 이 티켓은 위젯 쪽 폴더를 꼴 시험 안에 더하고 `PRODUCT_MIGRATIONS`는 고치지 않는다. 폴더 목록의 원천을 하나로 줄이는 일은 04가 한다

### 읽는 경로와 봉투

- [x] 앱을 짓는 자리는 함수 하나이고 모듈 수준 전역 앱이 없다. 끝 `/`를 고치는 되돌려 보내기를 끄고, `/health`는 데이터베이스에 묻지 않는다(명세 "연결 문자열과 시작", "경로의 접두사")
- [x] 읽는 경로가 명세 "읽는 경로"의 갈래 넷대로다. 꼴은 이름 전체로 판정하고(끝에 붙은 줄바꿈 `%0A`도 꼴이 틀린 이름이다), 경로 인자의 `pattern`으로 422를 내지 않는다(명세 "사이트 이름의 꼴", 명세 검토 S5). 꼴이 틀린 이름은 데이터베이스에 묻지 않는다
- [x] 답이 명세 "답의 모양"의 열아홉 열쇠와 `schema_version`만 싣는다. 시험은 값을 넣지 않은 칸이 `null`이고, 예시 질문은 `[]`, 밝기 스위치 숨기기는 `false`인 것까지 본다(명세 "답의 모양", Testing Decisions 첫째 이음매의 "읽는 경로"). 계약에는 `schema_version`을 빠지지 않는 `integer`로 싣고 `const`나 `enum`으로 좁히지 않는다(명세 "판 표시", 명세 검토 B2). FastAPI가 그 칸을 필수로 싣는지 내보낸 계약에서 본다(명세 검토 "확인하지 못한 것")
- [x] 봉투와 상태 코드 표와 추적 식별자와 접두사 비교를 `widget_admin` 안에 사본으로 둔다(명세 "오류 봉투와 기록", 머리 문단의 사본 문장). 실패 하나가 표준 오류에 추적 식별자와 함께 한 줄 남고, 경로도 사이트 이름도 적지 않는다
- [x] 머리 셋을 `/widget-settings` 접두사(접두사 비교와 같은 범위라 `/widget-settings` 자체도 든다)의 모든 답에, 핸들러가 놓친 예외의 500까지 단다. `GET` 밖의 메서드(`HEAD`와 `OPTIONS` 포함)는 405 봉투다. 미들웨어의 차례는 명세 "응답 머리"의 끝 항목대로이고, 그 가장 바깥의 데이터베이스 확인은 03이 더한다(명세 "응답 머리", "읽는 경로", 명세 검토 N3)
- [x] 라우트에 `operation_id`를 적고, 읽는 경로는 404와 500을 계약에 적는다

### 계약 파일

- [x] `widget-admin/openapi.json`을 손으로 고치지 않고 내보내기 도구로 뽑는다. 앱을 짓는 함수가 데이터베이스 객체를 받으므로, 내보내기는 데이터베이스에 닿지 않는 자리표시자로 앱을 짓는다(선례는 `tools/export_openapi.py`의 같은 자리). 최신성은 pytest 하나가 판정한다(명세 "계약 파일과 생성 클라이언트"의 첫 항목)

### serve 이미지

- [x] `deploy/images/serve.Dockerfile`과 그 `.dockerignore`에 멤버의 `pyproject.toml`만 들인다. 멤버의 소스는 들이지 않는다(명세 "이미지", 명세 검토 B1)
- [x] 단독 배포 e2e를 로컬에서 돌려 serve 이미지가 지어지고 지금의 사례가 모두 지나는 것을 일지에 적는다. serve의 짓는 파일을 고치므로 `CLAUDE.md` 검증 명령의 단독 배포 e2e 계기에 들고, dev로 가는 PR의 CI는 이 이미지를 짓지 않는다(명세 "이미지"의 같은 항목). 이미지 안에 `agent-os`가 있고 `widget_admin`이 없는지도 본다

### 문서와 하네스

- [x] `docs/constitution/tech.md`의 패키지 관리 칸, 경계 칸, 끝 문단(위젯 관리 서버의 문단)을 고치고 헌법 판을 patch로 올린다. 판은 커밋 직전의 `tools/sibling_overlap.py`가 낸 형제의 가장 높은 판보다 높게 고른다(명세 "문서와 하네스", ADR 0038의 선례). 레지스트리 칸과 CI 칸은 04가 고친다
- [x] `CLAUDE.md`의 레이어 목록에 `widget-admin/`과 `tests/widget_admin/`을 더한다. 고치기 전에 Skill 도구로 `writing-for-agents`를 부른다(`.claude/rules/agent-docs.md`)
- [x] 루트 `README.md`의 트리에 `widget-admin/`과 `tests/widget_admin/`을 더한다. 시작 절의 세 명령은 03이 더한다
- [x] `.claude/rules/http.md`의 첫 항목에 그 범위가 `agent_os`라는 것과 위젯 관리 서버가 봉투와 추적 식별자와 접두사 비교를 따로 든다는 것을 한 줄 더한다
- [x] `.claude/rules/widget-admin.md`를 새로 두고 `paths`에 `widget-admin/**`와 `tests/widget_admin/**`를 적는다. 담는 것은 명세 "문서와 하네스"의 그 항목이다. 바꾼 규칙 둘은 새 세션에서 불러 본다(작업 규약 3)

### 시험(명세 Testing Decisions 첫째 이음매)

- [x] 첫째 이음매의 사례 가운데 이 티켓의 것이 모두 있다. 읽는 경로, 표에 칸을 더해도 답이 그대로, 없는 이름과 꼴이 틀린 이름(끝 줄바꿈 포함), 데이터베이스 실패(무작위 꼬리를 단 이름으로 불러 기록 줄과 봉투에 그 이름과 요청 경로와 `계정:비밀번호@` 꼴이 없다, 명세 검토 S6), 머리(끝 `/` 없는 `/widget-settings`의 404 포함), 접두사, 표의 제약(끝 줄바꿈이 붙은 이름 포함. PostgreSQL 정규식이 그 이름을 거절하는지가 여기서 처음 보인다, 명세 검토 "확인하지 못한 것"), 계약 최신성과 판 번호다. 시작과 닫기와 루프백 사례는 03이 더한다
- [x] 데이터베이스를 가짜로 바꾸지 않는다. 핸들러가 놓친 예외만 지은 앱에 예외를 던지는 시험용 경로를 붙여 일으킨다(선례는 `tests/test_server.py`의 `_route_that_raises`)
- [x] 퍼센트 인코딩은 인코딩한 글자로 민다(`.claude/rules/http.md`의 `verbatim` 항목)

### 검증

- [x] `CLAUDE.md`의 검증 명령이 모두 초록이다
- [x] 이 티켓은 LLM 시험의 범위(`docs/constitution/operations.md` LLM 테스트)에 드는 경로를 고치지 않는다. 고치게 되면 그 조건을 따른다
- [ ] (PR의 CI가 돈 뒤 일지 끝에 적는다) 이 티켓의 PR에서 CI `python` 잡의 시간과 pytest 단계의 시간을 일지에 적는다. 그 잡의 제한은 25분이다. 15분이던 제한에 잡이 닿아 잇달아 취소되자 2026-11-24에 올렸고, 그때 성공한 실행 40개의 최대가 15.0분이었다(`.github/workflows/ci.yml`의 그 잡 주석, `.scratch/harness/issues/ci-python-job-timeout-25.md`). 이 티켓의 데이터베이스 시험이 그 시간을 늘리므로 잰 값을 그 최대와 제한에 견주고, 제한에 다시 가까워 보이면 사람에게 알린다(명세 검토 N5)
- [ ] (CI 몫은 PR의 CI가 돈 뒤 일지 끝에 적는다) 프로브가 재지 못한 넷 가운데 이 티켓이 보는 둘을 일지에 적는다(명세 "검사 도구의 자리"의 "재지 못한 것"). 하나는 CI의 리눅스에서 `uv sync --frozen`과 검사 도구가 두 묶음으로 도는 것과 CI가 받은 uv의 판이다(`setup-uv`에 판을 적지 않았다). 이 티켓 PR의 CI 기록에서 읽는다. 다른 하나는 pre-commit 러너(`tools/run_checks.py`)가 통째로 도는 것이고, 이 티켓의 커밋이 부르는 pre-commit의 결과로 본다

### 다시 돌릴 때만 하는 일

이 티켓은 프로브(`.scratch/widget-admin-server/probes/uv_workspace/run.py`)를 다시 돌리지 않아도 된다. 검사 도구의 자리는 실제 저장소에서 위 저장소 상태 시험과 손으로 본 양성 대조가 본다. 프로브를 다시 돌리게 되면 먼저 그 `Tree.run`이 시간 제한을 넘긴 명령(`TimeoutExpired`)의 출력을 로그에 남기게 고치고, 표준 출력을 가리는 `secret_stdout`도 그 길에 건다. 지금은 900초를 넘긴 회차의 원본 출력이 사라진다(일지 `docs/journal/2026-11-24-1637-widget-admin-server-spec.md`의 "다음"). 셋째 사본 나무의 `.probe-logs/28-database-create.log`에는 시험 컨테이너의 비밀번호가 남아 있으니 사본 나무를 다시 쓰지 말고 새로 짓는다.
