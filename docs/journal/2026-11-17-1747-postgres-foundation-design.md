# 2026-11-17 (17:47) agent-os에 PostgreSQL을 들이는 설계 인터뷰 (postgres-foundation)

세션 제목 `docs/postgres-foundation-design`. 브랜치 `docs/postgres-foundation-design`, 워크트리 `.claude/worktrees/postgres-foundation-design`(기준 `origin/dev` `21e7d8d63`). 모델 Opus 5.5. 지시문 없이 연 세션이다. 설계 인터뷰라 티켓 없이 `docs/<slug>` 브랜치다.

## 사용자 프롬프트

> 사용자: 설계 인터뷰나 작업할 티켓 있어?

프론티어 다섯(`base-agent`, `diag-bundle`, `ops-backup-upgrade`, `postgres-foundation`, `widget-runtime-values`)을 보였다. 티켓은 base-agent 07 하나이고 다른 저장소의 `rag-engine:release-image`를 기다린다. 설계 인터뷰를 기다리는 것은 셋(postgres-foundation, ops-backup-upgrade, diag-bundle)이고, 뒤에 선 기능이 가장 많은 postgres-foundation을 추천했다.

> 사용자: postgres-foundation 설계 인터뷰

## 시작 전 확인

- 나란히 도는 세션: `ListAgents`, 다른 세션 기록의 `postgres-foundation` 검색, `git branch -a`와 `git worktree list`. 이 기능을 맡은 브랜치·워크트리·세션은 없었다. 다른 세션의 기록에는 이 행을 "기다린다"로만 들었다.
- 주 체크아웃(`dev`)에서 시작해 `EnterWorktree`로 들어온 뒤 브랜치 이름을 바꾸고 세션 제목을 맞췄다.

## 읽은 것

- `.scratch/postgres-foundation/plan.md`(이 행이 볼 물음의 목록), `.scratch/admin-login/probes/pg_stack/README.md`(드라이버·표 관리 도구·testcontainers·이미지의 측정), ADR 0062 결정 "저장"·"자격"·"경로와 층"과 Consequences "다른 행"·"한계", ADR 0064 결정 "데이터베이스"와 Consequences "운영", ADR 0056 결정 "컨테이너 배치", ADR 0048, ADR 0035, ADR 0049 Consequences "매니페스트 저자와 운영자".
- `deploy/standalone/compose.yaml`(컨테이너 다섯, 비밀 값은 `.env`로 `serve` 하나만 받는다), `.github/workflows/ci.yml`(`python` 잡은 `ubuntu-24.04`에서 service container 없이 한 프로세스), `pyproject.toml`의 import-linter 계약 "core knows no filesystem or DB"(금지 목록 `pathlib`, `os`, `sqlite3`).
- `.scratch/ops-backup-upgrade/plan.md`, `.scratch/widget-admin-server/plan.md`.

## 사실 확인

- rag-engine의 선례(서브에이전트, 읽기만. rag-engine HEAD `6957194`). 코드를 읽었다는 보고를 줄였다.
  - ADR 0011: SQLAlchemy 2.1 Core 비동기 + psycopg 3 + alembic. 버린 것은 psycopg 직접 호출과 손으로 쓰는 마이그레이션(스키마 이력을 직접 관리), asyncpg(`py.typed` 없음), ORM(strict 타입 마찰, 그 ADR이 어림이라 적음). 윈도의 Selector 루프가 필요하다는 것은 psycopg 문서를 읽은 것이고 재지 않았다고 그 ADR이 적는다.
  - 윈도에서는 모든 진입점이 Selector 루프를 고른다. 서버 `uvicorn.run(..., loop="asyncio:SelectorEventLoop")`, 작업자와 관리 명령 `asyncio.Runner(loop_factory=asyncio.SelectorEventLoop)`, alembic env, pytest의 `pytest_asyncio_loop_factories`. 윈도의 Selector 루프는 열린 소켓이 없으면 신호에 깨지 않아 작업자가 소켓 쌍과 `set_wakeup_fd`로 깨운다.
  - 테스트 DB는 testcontainers가 아니라 미리 띄운 compose 하나(`compose.test.yml`, 127.0.0.1:55432, tmpfs, fsync 끔, `pg_isready -h 127.0.0.1`). pre-commit 러너가 답하지 않으면 띄우고 내리지 않으며, 모든 워크트리와 세션이 함께 쓴다. xdist 작업자마다 템플릿 DB를 만들어 마이그레이션을 한 번 올리고 시험마다 `CREATE DATABASE … TEMPLATE`로 복제한다. DB가 없으면 실패하고 skip이 하나라도 있으면 세션을 실패로 끝낸다. CI는 `services: postgres`.
  - 마이그레이션은 운영자가 치는 명령(`rag-engine migrate`)이고 서버가 뜰 때 저절로 돌지 않는다. 첫 판의 downgrade는 `NotImplementedError`다. 배포 compose와 백업 도구는 아직 없다. 서버는 DB 없이 뜨고(첫 질의 때 연결) `/health`는 DB를 보지 않는다.
- agent-os의 `src`에는 `anyio.run_process`와 asyncio 자식 프로세스 호출이 없다. stdio MCP 서버는 mcp 라이브러리의 `stdio_client`가 띄우고, 윈도에서는 런처 없이 그 호출 그대로다(코드를 읽었다, `src/agent_os/adapters/mcp.py` `_parameters`). `tests`에도 그 호출은 없다(grep).
- stdio MCP 서버에는 `env`를 넘기지 않아 라이브러리의 기본 환경만 간다. http 모양의 매니페스트는 `[server.headers]`로 `serve`의 아무 환경 변수나 제 주소로 보낼 수 있다(코드를 읽었다, 같은 파일 `_http_session`. ADR 0049).
- 공식 이미지의 진입 스크립트는 `POSTGRES_PASSWORD_FILE`처럼 `_FILE`로 끝나는 변수에서 값을 읽는다(손으로 봤다, `postgres:18-alpine`과 `postgres:18`의 `/usr/local/bin/docker-entrypoint.sh`를 grep). 사용자는 Alpine이 uid 70, Debian이 uid 999이고, `postgres:18`의 바탕은 Debian trixie다(손으로 봤다, `id postgres`와 `/etc/os-release`).
- 실제 serve를 띄우는 e2e는 넷이다. 관리 화면·위젯·위젯 미리보기 페이지는 `web/packages/e2e-stack`으로, 단독 배포는 compose로 띄운다(코드를 읽었다, `web/apps/*/e2e/stack.ts`, `e2e-stack/src/serve.ts`).

## 라운드 1

> 사용자: 운영 서버(serve)를 띄울 때 데이터베이스가 없거나 닿지 않으면 어떻게 할까요? → "없으면 뜨지 않음 (Recommended)"

— 설명: 연결 문자열이 없거나, 뜰 때 몇 번 다시 시도해도 데이터베이스에 닿지 않으면 serve가 이유를 한 줄로 찍고 멈춥니다. 서버가 도는 길이 하나라서 시험도 한 벌입니다. 명령줄 실행(agent-os run)은 데이터베이스 없이 그대로 돕니다. 대가: 실제 serve를 띄우는 e2e 넷(관리 화면, 위젯, 미리보기 페이지는 e2e-stack으로, 단독 배포는 compose로 띄웁니다)에 이 기능이 데이터베이스를 붙여야 하고, 플러그인 개발자가 위젯으로 확인하려고 serve를 띄울 때도 데이터베이스가 있어야 합니다.

> 사용자: 데이터베이스를 쓰는 테스트는 데이터베이스(Docker)가 없는 환경에서 어떻게 할까요? → "실패로 알림 (Recommended)"

— 설명: 데이터베이스 테스트는 기본 실행(uv run pytest -q와 pre-commit 러너, CI)에 들어 있고, Docker나 데이터베이스를 띄우지 못하면 건너뛰지 않고 실패하며 원인을 한 줄로 알립니다. 헌법 원칙 II('환경 부재로 skip된 테스트는 초록이 아니다')를 그대로 따릅니다. 대가: Docker가 꺼진 PC에서는 pytest 전체가 빨갛게 나옵니다.

> 사용자: agent-os 데이터베이스의 백업과 복원은 어느 기능에서 만들까요? → "ops-backup-upgrade가 맡음 (Recommended)"

— 설명: 이 기능(postgres-foundation)은 데이터베이스와 거기 닿는 길까지만 만들고, 백업·복원·판 올림은 ops-backup-upgrade가 플러그인 폴더·트레이스 폴더·데이터베이스를 한 명령으로 묶어 만듭니다. ADR 0064는 위젯 쪽 데이터베이스의 백업을 어느 기능이 더할지를 이 선택과 같게 한다고 적었습니다. 그래서 이 선택이면 위젯 쪽도 기반 기능(widget-admin-server)이 아니라 백업 기능이 맡는다고 읽습니다(어림. 합의 요약에서 확인합니다). 대가: 이 기능이 끝나고 ops-backup-upgrade가 끝나기 전까지는 데이터베이스 백업 방법이 문서에 없습니다. 0.1 판(pilot-release)은 deploy-package를, deploy-package는 ops-backup-upgrade를 기다리므로 0.1 판 전에는 둘 다 끝납니다.

## 라운드 2

> 사용자: 데이터베이스에 접근하는 도구 묶음(드라이버, 쿼리 층, 마이그레이션)을 무엇으로 할까요? → "드라이버만 asyncpg (Recommended)"

— 설명: SQLAlchemy 2.1 Core 비동기 + asyncpg + alembic. 쿼리 층과 마이그레이션은 rag-engine과 같고 드라이버만 다릅니다. admin-login의 측정(판 SQLAlchemy 2.1.8, asyncpg 0.32.0, alembic 1.20.1)에서 윈도 기본 루프·Selector 루프·리눅스 컨테이너 모두에서 돌았고 pyright strict 오류 0이었습니다. 그래서 agent-os의 이벤트 루프와 stdio MCP 서버를 띄우는 길을 건드리지 않습니다. 대가: rag-engine과 드라이버가 달라집니다. asyncpg는 자체 타입 표지가 없고, rag-engine은 그 까닭으로 asyncpg를 버렸습니다. 우리 코드가 SQLAlchemy만 부르면 asyncpg의 타입은 드러나지 않는다고 봅니다(어림. 측정 환경에는 asyncpg-stubs가 함께 깔려 있었습니다).

> 사용자: 판을 올릴 때 데이터베이스의 표 변경(마이그레이션)은 누가 언제 적용할까요? → "reg-engine 저장소랑 동일하게"

선택지 밖의 답이다. rag-engine의 ADR 0011 21줄을 읽었다: `rag-engine migrate`가 `alembic upgrade head`를 돌리고 서버 기동 때 자동으로 돌리지 않으며, compose는 서버 앞에 한 번 도는 마이그레이션 서비스를 둔다(문서를 읽었다, `C:/project/rag-engine/docs/adr/0011-sqlalchemy-core-async-and-alembic.md`. 그 compose 서비스는 rag-engine에 아직 구현되지 않았다는 것은 서브에이전트가 코드를 읽은 보고다). 첫 선택지 "compose가 serve 앞에 돌림"과 같은 배치로 받고, serve가 표의 판이 다르면 멈춘다는 부분은 rag-engine에 없는 것이라 합의 요약에서 따로 확인한다. 화면에 올린 그 선택지의 설명은 아래다.

— 설명(선택지 "compose가 serve 앞에 돌림 (Recommended)"): 마이그레이션을 적용하는 명령(예: agent-os migrate)을 두고, 단독 compose에서 같은 이미지로 한 번 돌고 끝나는 서비스가 serve보다 먼저 그 명령을 돌립니다. 운영자는 판 번호를 바꾸고 docker compose up만 칩니다. serve는 뜰 때 표의 판이 자기가 아는 마지막 판과 다르면 이유를 찍고 멈춥니다. rag-engine도 ADR에 같은 배치를 적었지만 아직 구현하지 않았습니다. 대가: compose에 한 번 돌고 끝나는 서비스가 하나 늘고, 배포 안내가 그것을 설명해야 합니다.

> 사용자: 판을 올렸다가 옆 판으로 되돌리고 싶을 때 데이터베이스는 어떻게 되돌릴까요? → "보통 어떻게 해? 조사해봐"

선택지 밖의 답이다. 설치형 제품과 마이그레이션 도구의 관행을 웹에서 조사하는 서브에이전트를 띄웠다(원문을 받아 본 것과 검색 요약을 가르게 했다). 결과를 보고 다시 묻는다. 화면의 두 선택지는 "백업에서 복원 (Recommended)"(앞으로만 가는 마이그레이션, 옛 판 serve는 새 스키마에서 멈춤, 올리기 전 백업을 복원, 백업 뒤 데이터는 잃음)과 "되돌리는 스크립트 작성"(downgrade를 쓰고 CI가 올리기→되돌리기→다시 올리기를 시험)이었다.

> 사용자: 테스트가 데이터베이스를 어떻게 얻을까요? → "미리 띄운 컨테이너 하나 (Recommended)"

— 설명: rag-engine 방식입니다. 테스트용 compose 파일의 PostgreSQL 컨테이너 하나(데이터는 메모리, 127.0.0.1의 정해진 포트)를 pre-commit 러너가 답이 없을 때 띄우고 내리지 않으며, 모든 워크트리와 세션이 함께 씁니다. xdist 작업자마다 템플릿 데이터베이스를 만들고 시험마다 복제합니다. CI는 같은 이미지를 service container로 붙입니다. 위젯 관리 서버의 시험도 같은 컨테이너에서 데이터베이스 이름만 달리해 씁니다. 대가: 손으로 치는 uv run pytest는 컨테이너를 띄우지 않아, 없으면 '이 명령으로 띄우십시오'라고 알리며 실패합니다.

## 라운드 3

올리기 전에 대 본 것: `deploy/images/serve.Dockerfile`의 `PYTHON_IMAGE` digest가 pg_stack README의 `python:3.12-slim-trixie`와 같다(코드를 읽었다). `deploy/standalone/.env.example`의 비밀 값 칸은 두 토큰과 `ANTHROPIC_API_KEY`다(코드를 읽었다). `/health`는 `src/agent_os/admin/http.py`의 `read_health`이고 요약이 "살아 있는지만 답한다"다(코드를 읽었다). 이미지 크기와 지원 끝 날짜는 pg_stack README의 표다.

> 사용자: 배포에 넣을 PostgreSQL 이미지는 어느 것으로 할까요? → "PostgreSQL 18 Debian (Recommended)"

— 설명: 공식 postgres:18(바탕 Debian trixie)을 digest로 고정해 단독 compose, 테스트용 compose, CI가 같은 것을 씁니다. serve 이미지의 바탕(python:3.12-slim-trixie)·rag-engine의 데이터베이스 이미지와 같은 Debian trixie입니다. 압축 168.5MB(풀린 크기 474MB)이고, 18의 지원은 2030-11-14까지입니다(2026-11-14의 측정). 대가: Alpine보다 압축 크기가 48MB 큽니다.

> 사용자: 데이터베이스 비밀번호는 배포 파일에서 어떻게 넘길까요? → ".env에 둠"

— 설명: 연결 문자열을 .env의 한 줄로 두고, compose가 같은 비밀번호를 PostgreSQL 컨테이너에도 넘깁니다. 다른 비밀 값(API 키)과 같은 자리라 운영자가 고칠 파일이 하나입니다. 대가: ADR 0049의 길에 놓입니다. 매니페스트 저자가 그 변수 이름을 헤더에 적으면 비밀번호가 그 주소로 갑니다. 지금의 API 키도 같은 처지입니다.

추천("비밀 파일로 넘김")과 다른 답이다. 그 대가는 ADR의 Consequences에 적고, 환경 변수 이름을 서버마다 허락하는 일은 mcp-trust가 이미 받은 요구(ADR 0049, `.scratch/mcp-trust/plan.md`)에 이 변수도 든다고 적는다.

> 사용자: 설치처가 이미 운영하는 PostgreSQL(예: 클라우드의 관리형 DB)에 붙는 것도 지원할까요? → "동봉한 것만 지원 (Recommended)"

— 설명: 지원하는 것은 단독 compose가 띄우는 PostgreSQL 18 하나입니다. serve는 연결 문자열을 받지만 다른 PostgreSQL에 붙이는 것은 지원 범위 밖이라 시험하거나 안내하지 않습니다. rag-engine(ADR 0002)도 같습니다. 대가: 회사가 자기 PostgreSQL을 쓰고 싶어도 공식 길이 없습니다.

> 사용자: serve가 뜨고 난 뒤 데이터베이스가 내려가면 /health는 무엇을 답할까요? → "지금처럼 프로세스만 (Recommended)"

— 설명: /health는 지금 코드처럼 '살아 있는지만 답한다'로 두고 데이터베이스를 보지 않습니다. 운영 중에 데이터베이스가 내려가면 데이터베이스가 필요한 요청만 실패합니다(지금의 에러 표에서는 예기치 않은 실패의 500). 계약(openapi.json)의 /health와 compose의 healthcheck는 그대로입니다. rag-engine도 같습니다. 대가: 데이터베이스가 내려가도 serve 컨테이너는 정상으로 보여, 운영자는 요청이 실패하는 것을 보고 알게 됩니다.

## 라운드 4

올리기 전에 대 본 것: 공식 이미지의 진입 스크립트는 `DATABASE_ALREADY_EXISTS`가 비었을 때만 `/docker-entrypoint-initdb.d/*`를 돌린다(손으로 봤다, `postgres:18`의 `/usr/local/bin/docker-entrypoint.sh` 347~363줄을 grep). CI의 e2e 잡 이름은 `e2e`, `e2e-widget`, `e2e-portal`이다(코드를 읽었다, `.github/workflows/ci.yml`). e2e-stack은 `uv run`으로 실제 serve를 띄운다(코드를 읽었다, `web/packages/e2e-stack/src/serve.ts`).

> 사용자: 마이그레이션 서비스와 serve는 데이터베이스에 같은 계정으로 접속할까요? → "계정 하나 (Recommended)"

— 설명: PostgreSQL 이미지가 처음 뜰 때 만드는 계정 하나(POSTGRES_USER)로 마이그레이션 서비스와 serve가 함께 접속합니다. .env에는 연결 문자열 한 줄이면 됩니다. 대가: serve의 계정에 표를 지우고 바꿀 권한도 있어, serve가 뚫리면 표의 구조까지 망가뜨릴 수 있습니다.

> 사용자: PostgreSQL의 주 판(18에서 19로)을 올리는 길은 언제 어느 기능에서 만들까요? → "ops-backup-upgrade가 만듦 (Recommended)"

— 설명: 주 판을 올리는 길은 ops-backup-upgrade가 만드는 백업(덤프)을 새 주 판의 컨테이너에 복원하는 것으로 하고, 그 기능 계획에 적습니다. 같은 주 판 안의 올림(지금 18.7에서 다음 부 판으로)은 이미지 digest만 바꾸면 된다고 봅니다(어림. PostgreSQL이 부 판 사이의 데이터 파일 호환을 약속한다는 것은 원문을 받아 보지 않았습니다). 대가: ops-backup-upgrade의 범위가 조금 늘어납니다.

> 사용자: 실제 serve를 띄우는 e2e(관리 화면·위젯·위젯 미리보기 페이지)는 데이터베이스를 어떻게 얻을까요? → "테스트 컨테이너를 같이 씀 (Recommended)"

— 설명: e2e-stack이 띄우는 serve도 pytest와 같은 미리 띄운 테스트 컨테이너에 자기 데이터베이스 이름으로 붙고, 컨테이너가 없으면 같은 문구로 실패합니다. CI의 e2e 잡 셋(e2e, e2e-widget, e2e-portal)에는 같은 이미지의 service container를 붙입니다. 단독 배포 e2e는 compose의 PostgreSQL을 그대로 씁니다. 대가: 로컬에서 playwright를 치기 전에 테스트 컨테이너가 떠 있어야 합니다.

## 조사: 판을 되돌릴 때의 데이터베이스

라운드 2의 "보통 어떻게 해? 조사해봐"에 답한 웹 조사다. 서브에이전트가 공식 문서와 코드를 WebFetch로 받아 보고했고, 받은 페이지는 세션 스크래치패드(`…/scratchpad/web/`, 저장소 밖)에 있다. 그 가운데 넷은 이 세션이 저장한 원문을 grep해 보고와 같은 문장이 있는 것을 봤다(손으로 봤다): Nextcloud의 "Downgrading is not supported", Forgejo의 "refuse to start because it would damage the content of the database", Synapse의 `compat_version`과 시작 거부, Flyway의 "no substitute for having a robust backup/restore strategy". 나머지는 서브에이전트의 보고다.

- 설치형 11개 가운데 8개(GitLab, Gitea, Forgejo, Keycloak, Nextcloud, Grafana, Sentry, Discourse)가 판 내리기를 지원하지 않거나 백업 복원을 안내한다. 그중 공식 문서로 확인한 것은 6개라고 보고했다. Mattermost 1개가 새 판 바이너리의 `db downgrade`로 내린다. Synapse는 여러 판에 걸친 호환 창과 `compat_version`의 시작 거부를 쓴다. Zulip은 부 판만 코드 교체로 되돌린다.
- 옛 판이 더 새 스키마를 만나면 시작을 거부하는 선례: Forgejo, Synapse, Nextcloud(`lib/private/Updater.php`), Gitea(오류 문구는 검색 요약).
- 도구: Flyway의 undo는 유료 판(Teams) 기능이고, 롤백 스크립트가 백업·복원 전략을 대신하지 못한다고 적는다. Alembic 문서는 downgrade의 기능만 설명하고 운영 환경의 권고를 두지 않는다. Liquibase의 차례 되돌리기는 모든 판에 있고 하나만 되돌리기는 유료 판이다.
- 운영 관행: expand/contract(Fowler의 ParallelChange, Prisma, GitLab 개발 문서의 열 삭제 세 판 나누기, Discourse의 배포 전후 마이그레이션 나누기).
- Forgejo는 백업 복원이 올린 직후에만 잃는 데이터가 없다고 적었다.

## 라운드 5

> 사용자: 조사 결과를 보고 고르실 때, 판을 올렸다가 옆 판으로 되돌릴 때 데이터베이스는 어떻게 할까요? → "백업 복원 + 옛 판은 멈춤 (Recommended)"

— 설명: 조사한 11개 가운데 8개(GitLab, Gitea, Forgejo, Keycloak, Nextcloud 등)의 방식입니다(서브에이전트가 공식 문서를 받아 본 보고이고, 저는 그중 원문 넷을 대 봤습니다). 마이그레이션은 앞으로만 가고 되돌리는 스크립트는 쓰지 않습니다. 옛 판 serve가 자기가 모르는 더 새 표의 판을 만나면 '데이터베이스가 이 판보다 새롭습니다. 되돌리려면 올리기 전의 백업을 복원하십시오'라고 찍고 멈춥니다(Forgejo와 Nextcloud가 이렇게 멈추는 것을 문서와 코드로 확인했습니다). 릴리스 노트의 '올릴 때 할 일'에 올리기 전 백업을 적습니다. 대가: 되돌리면 백업을 뜬 뒤에 쌓인 데이터(새 계정, 로그인 기록)를 잃습니다. Forgejo는 그래서 백업 복원이 올린 직후에만 쓸 길이라고 적었습니다.

## 갈래 밟기

이 설계는 pre-commit 러너(`tools/run_checks.py`)가 하는 일을 바꾼다. 러너의 pytest는 문서만 바꾼 커밋에서도 돈다(코드를 읽었다, 같은 파일 17~18줄과 123줄). 그래서 이 기능이 병합된 뒤에는 모든 세션의 모든 커밋이 Docker와 함께 쓰는 테스트 컨테이너를 요구하고, Docker가 꺼져 있으면 커밋이 데이터베이스 테스트의 실패로 막힌다. 합의 요약에 넣어 확인받는다. 실제 serve를 띄우는 것은 e2e 셋만이 아니다. `-m llm`·`-m llm_widget`·`-m llm_portal`의 시험도 serve를 띄우므로(`.claude/rules/http.md`의 테스트 항목) CI의 `llm` 잡과 그 손 명령도 데이터베이스가 있어야 한다. `release.yml`은 단독 배포 시험을 compose로 돌아(코드를 읽었다, 125줄) compose에 PostgreSQL이 들면 따라온다.

## 합의 요약을 확인받았다

화면에 올린 요약을 글자 그대로 옮긴다(에이전트가 쓴 글이다).

고르신 것

1. serve와 데이터베이스: 연결 문자열이 없으면 serve가 구성 오류로 바로 멈춥니다. 연결 문자열이 있으면 뜰 때 잠시 다시 시도하고, 그래도 닿지 않으면 이유를 찍고 멈춥니다. 명령줄 실행(`agent-os run`)은 데이터베이스와 무관합니다.
2. 도구 묶음: SQLAlchemy 2.1 Core 비동기 + asyncpg + alembic입니다. 윈도의 이벤트 루프는 바꾸지 않습니다.
3. 표 올리기: `agent-os migrate` 명령을 두고, 단독 compose의 일회성 서비스가 serve보다 먼저 이 명령을 돌립니다(rag-engine ADR 0011과 같은 배치). serve는 뜰 때 표의 판을 봅니다. 판이 뒤처져 있으면 "migrate를 먼저 돌리십시오", 자기가 모르는 더 새 판이면 "올리기 전 백업을 복원하십시오"라고 찍고 멈춥니다.
4. 판 되돌리기: 마이그레이션은 앞으로만 가고, 되돌리는 스크립트는 쓰지 않습니다. 릴리스 노트의 "올릴 때 할 일"에 올리기 전 백업을 적습니다.
5. 테스트 DB: 데이터베이스 테스트는 기본 실행에 들고, 데이터베이스가 없으면 건너뛰지 않고 실패합니다. 미리 띄운 테스트 컨테이너 하나를 씁니다. 데이터는 메모리에 두고, 127.0.0.1의 정해진 포트를 쓰되 rag-engine의 55432·55433과는 겹치지 않게 합니다. pre-commit 러너는 컨테이너가 없으면 띄우고 내리지 않습니다. xdist 작업자마다 템플릿 DB를 만들고 시험마다 복제합니다. CI는 같은 이미지를 service container로 붙입니다.
6. e2e: e2e-stack이 띄우는 serve도 같은 테스트 컨테이너에 자기 데이터베이스 이름으로 붙습니다. CI의 `e2e`·`e2e-widget`·`e2e-portal` 잡에는 service container를 붙이고, 단독 배포 e2e는 compose의 PostgreSQL을 씁니다.
7. 이미지: `postgres:18`(Debian trixie)을 digest로 고정하고, 배포·테스트·CI가 모두 같은 것을 씁니다.
8. 지원 범위: compose가 띄우는 PostgreSQL 18 하나만 지원합니다.
9. 비밀번호와 계정: 비밀번호는 `.env`에 두고, 마이그레이션과 serve는 같은 계정 하나로 접속합니다.
10. `/health`: 지금처럼 프로세스만 봅니다.
11. 백업과 주 판 올림: agent-os 데이터베이스의 백업·복원과 PostgreSQL 주 판 올림(백업을 새 주 판에 복원하는 방식)은 ops-backup-upgrade가 맡습니다. ADR 0064가 "같게 한다"고 적었으므로, 위젯 쪽 데이터베이스의 백업도 widget-admin-server가 아니라 ops-backup-upgrade가 맡는다고 읽었습니다.

제가 채운 세부

12. 층: 데이터베이스 코드는 `agent_os.adapters` 안 한 곳에 둡니다. 엔진 만들기, 마이그레이션 파일, 저장 구현이 모두 여기 들고, 마이그레이션 파일은 패키지 안에 있으므로 이미지에 함께 들어갑니다. import-linter는 SQLAlchemy·asyncpg·alembic을 core·http·channel·admin이 import하지 못하게 막습니다. `main`이 연결 문자열로 엔진을 만들어 `create_app`에 넘기고, 앱은 뜰 때 연결과 표의 판을 확인하며 내려갈 때 연결 묶음을 닫습니다.
13. compose: 계속 도는 컨테이너는 다섯에서 여섯(PostgreSQL 추가)이 되고, 한 번 돌고 끝나는 마이그레이션 서비스가 하나 붙습니다. 받는 바깥 이미지는 nginx와 postgres 둘이 되고, 이름 있는 볼륨이 하나 늡니다. ADR 0056의 "컨테이너는 다섯이다"와 "받을 바깥 이미지는 nginx 하나다"에는 포인터를 답니다. PostgreSQL 컨테이너의 권한을 좁히는 설정(읽기 전용 루트, 권한 빼기)은 명세가 리눅스에서 잽니다.
14. 이 기능이 짓는 표: 없습니다. alembic의 판 기록 표만 생기고, 운영자 계정 표는 admin-login이 짓습니다. 수락 조건 "다시 띄워도 넣어 둔 줄이 남는다"는 그 판 기록으로 봅니다.
15. 위젯 관리 서버: 같은 도구 묶음을 쓰되, 엔진과 마이그레이션은 자기 패키지 안에 따로 둡니다. 두 패키지는 서로를 import하지 못하므로 코드를 나눠 쓰지 않습니다. 테스트는 같은 테스트 컨테이너에서 데이터베이스 이름만 달리합니다. 테스트 도우미를 `tests/` 안에 하나 두고 두 패키지가 함께 쓸 수 있는지는 명세가 확인합니다(어림).
16. 프로브 폴더: admin-login 아래에 그대로 두고 경로로 인용합니다. 옮기면 Dockerfile과 실행 스크립트의 경로를 고쳐 측정을 다시 돌려야 합니다.
17. 의존성: 새로 드는 것은 `sqlalchemy[asyncio]`(greenlet이 함께 옵니다), `asyncpg`, `alembic`입니다. 판의 묶음은 첫 티켓이 정하고 `docs/constitution/tech.md`의 표를 고칩니다. `asyncpg-stubs`는 우리 코드가 asyncpg를 직접 부를 때만 넣습니다.
18. 용어집: 더할 말이 없습니다. 이번 결정은 제품의 개념이 아니라 구현의 도구와 배치이기 때문입니다.

모두에게 닿는 결과

- 이 기능이 병합된 뒤에는 모든 커밋이 Docker를 요구합니다. pre-commit의 pytest가 문서만 바꾼 커밋에서도 돌기 때문입니다. Docker가 꺼져 있으면 커밋이 막힙니다(rag-engine도 같습니다).
- 실제 serve를 띄우는 시험이 모두 데이터베이스를 요구합니다. 그래서 CI의 `python`·`llm`·e2e 세 잡에 service container가 붙고, 손으로 치는 `-m llm`·`-m llm_widget`·`-m llm_portal`도 테스트 컨테이너가 떠 있어야 합니다.
- `.env`의 데이터베이스 비밀번호는 ADR 0049의 길(매니페스트가 환경 변수를 밖으로 보내는 길)에 놓입니다. 이 사실을 ADR의 Consequences와 mcp-trust 기능 계획에 적습니다.

> 사용자: 위 합의 요약(고르신 것 1~11, 제가 채운 세부 12~18, 모두에게 닿는 결과)대로 설계를 확정하고 ADR 초안을 쓸까요? → "이대로 확정 (Recommended)"

— 설명: 요약대로 설계를 확정합니다. 다음으로 ADR 초안(새 의존성과 배치의 결정, 바뀌는 ADR에 다는 포인터)과 기능 계획의 설계 줄을 쓰고, 셀프 리뷰를 반영한 뒤에 그 초안을 보여 드려 승인을 받습니다. ops-backup-upgrade와 mcp-trust의 기능 계획에도 이 설계가 넘기는 일을 적습니다.

## ADR 초안

ADR 0066을 `proposed`로 썼다(번호는 `tools/sibling_overlap.py`로 겹침이 없는 것을 봤다). 색인에 행을 더했고, ADR 0056 결정 "컨테이너 배치"의 포인터 `(바뀜: ADR 0064)` 뒤에 `(바뀜: ADR 0066)`을 이었다. ADR 0062와 ADR 0064의 해당 문장은 "postgres-foundation이 정한다"고만 적어 지금도 참이라 달지 않았다.

초안을 쓰며 대 본 것:

- 배포 안내 9절(`deploy/standalone/README.md`)은 digest로 고정한 nginx 이미지가 `docker save`·`docker load`를 지나며 digest를 잃어 태그를 붙여 옮긴다(읽었다). postgres도 digest로 고정하므로 같은 처지다. compose에 PostgreSQL을 더하는 티켓이 그 절의 명령을 고친다고 Consequences "운영"에 적었다.
- 공식 이미지 `postgres:18`의 설정은 `PGDATA=/var/lib/postgresql/18/docker`, `VOLUME /var/lib/postgresql`, 사용자 빈칸이다(손으로 봤다, `docker image inspect`). 진입 스크립트는 58줄에서 데이터 폴더의 소유를 `postgres`로 맞추고 343줄에서 `exec gosu postgres`로 내려간다(손으로 봤다, 컨테이너 안에서 grep). 이 PC가 받아 둔 이미지의 digest는 `sha256:b9f6b8ff03b62f3cfd9d9ba3fe56226a9991c79d3fb46fd46536263bf02be553`이다(손으로 봤다).
- 릴리스 노트의 "올릴 때 할 일"은 느낌표 PR이 `docs/release-notes/upgrade/`에 싣는 조각뿐이다(`docs/constitution/operations.md`, `tools/release.py`를 읽었다). ADR 0056 결정 "번호"는 운영자가 손댈 것이 있는 변경에 느낌표를 붙이고 가운데 자리를 올린다. 그래서 합의 요약 4("릴리스 노트의 '올릴 때 할 일'에 올리기 전 백업을 적습니다")를 따르면 마이그레이션을 더하는 PR은 느낌표 PR이 되고 그 판은 가운데 자리가 오른다. 합의 요약에 없던 갈래라 ADR 결정 "승인 때 함께 확인받는 세부"의 첫째로 올렸다.
- 합의 요약 12는 "`main`이 연결 문자열로 엔진을 만들어 `create_app`에 넘기고"라고 적었다. 엔진을 그대로 넘기면 `server.py`가 SQLAlchemy를 import하게 되어 같은 항목의 "데이터베이스 코드는 `agent_os.adapters` 안 한 곳"과 어긋난다. 포트를 넘기고 import 금지에 `agent_os.server`를 넣는 것으로 채워 같은 절의 둘째로 올렸다.
- Considered Options에는 화면에 올린 선택지의 설명을 대화 기록에서 꺼내 옮겼다. psycopg 동기와 yoyo-migrations는 선택지에 올리지 않았다고 적었다.

기능 계획을 고쳤다. ops-backup-upgrade(백업·복원·주 판 올림과 올리기 전 백업), mcp-trust(데이터베이스 비밀번호의 변수도 허락 목록의 대상), widget-admin-server(고른 도구와 그 명세가 정할 셋), trace-postgres(testcontainers와 "CLI run도 DB"를 다시 볼 자리), deploy-package(반입 명령과 외부 PostgreSQL 문장), postgres-foundation(답의 원천이 ADR 0066)이다. `.scratch/admin-login/probes/README.md`의 `pg_stack/` 줄이 근거로 드는 자리를 ADR 0066으로 고쳤다. `uv run python tools/plan_table.py`는 0으로 끝났고 `.scratch/plan.md`는 바뀌지 않았다.

## 인계

셀프 리뷰(`/code-review`)를 부른 직후 인계 계기(`셀프 리뷰 직전`, 세션 컨텍스트 311,056 토큰)가 왔다. 리뷰의 서브에이전트는 띄우지 않았다. 이 세션의 제목은 `docs/postgres-foundation-design`이었다. 커밋하지 않은 변경 전부(ADR 0066 초안, 색인, ADR 0056 포인터, 기능 계획 여섯, 프로브 README, 이 일지)가 워크트리에 있다. 낸 지시문:

다음 작업: 기능 postgres-foundation. ADR 0066 초안을 셀프 리뷰하고 사용자 승인을 받은 뒤 설계 줄을 적고 커밋·PR·병합한다
다음 단계: 설계 인터뷰
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: postgres-foundation 설계 인터뷰
브랜치: docs/postgres-foundation-design
모델: Fable 5.1 / xhigh. 2의 잇는 지시문
읽을 것: 일지 docs/journal/2026-11-17-1747-postgres-foundation-design.md의 "합의 요약을 확인받았다", "ADR 초안", "인계" 절
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리에 있고 셀프 리뷰(`/code-review`, 고정점 origin/dev, 명세는 `.scratch/postgres-foundation/plan.md`와 일지의 합의 요약)부터 한다. 설계 인터뷰는 끝났고 합의 요약을 사용자가 "이대로 확정"으로 확인했다. 리뷰를 반영한 뒤 ADR 0066을 보여 승인을 받는다. 그때 결정 "승인 때 함께 확인받는 세부"의 둘(표를 바꾸는 PR은 느낌표 PR이 되어 판의 가운데 자리가 오른다, `create_app`에 포트를 넘기고 import 금지에 `agent_os.server`를 넣는다)을 따로 확인받는다. 승인 뒤 ADR과 색인의 상태를 accepted로, `.scratch/postgres-foundation/plan.md`의 `**Blocked by:**` 줄 뒤에 `**설계:** ADR 0066`을 적고 `uv run python tools/plan_table.py`를 돈 뒤 일지에 승인과 "다음"(다음 단계는 사용자가 부르는 to-spec)을 적고 커밋·PR·병합한다. 일지 docs/journal/2026-11-17-1747-postgres-foundation-design.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지

open-session을 부른다 2026-11-17T09:45:54Z

open-session의 send가 2026-11-17T09:48:23Z에 딥링크를 쏘고, 새 세션 화면의 폴더를 `C:\project\rag-engine`에서 `C:\project\agent`로 고친 뒤 모델을 고르다 멈췄다. 출력은 "5초 안에 모델 메뉴의 'Fable 5.1' 을(를) 찾지 못했다."이고 종료 코드는 1이다. 지시문은 보내지 않은 채 새 세션 화면에 남았고, 사람에게 모델과 노력을 골라 보내 달라고 부탁했다. 결정표(`docs/model-selection.md`, `next-session` 스킬의 결정표)는 설계 인터뷰와 명세 칸을 `Fable 5.1 / xhigh`로 적는데, 이 날 앱의 모델 메뉴에는 그 이름이 없었다(스크립트의 오류로만 봤고 메뉴의 항목은 보지 않았다). 결정표를 메뉴에 맞추는 일은 이 세션의 몫이 아니다. 세션 카드는 훅이 막아(ADR 0037 "세션 카드") 회고 후보로 남긴다. 이어받는 세션이 단계를 닫는 회고에서 대기열에 올릴지 판정한다. 고칠 자리는 `docs/model-selection.md`, `next-session` 스킬의 결정표, `directive.md`이고, 메뉴에 지금 있는 이름부터 확인해야 한다.

사용자가 다시 보내 달라고 해, `.scratch/harness/probes/composer_menu_tree.ps1`로 모델 메뉴를 펼쳐 봤다(손으로 봤다). 첫 층의 모델은 Fable 5.2, Opus 5.5, Sonnet 5.5(기본값), Haiku 5.5이고 그 밖은 '더 많은 모델' 하위 메뉴다. 그 하위 메뉴는 열지 않아 Fable 5.1이 거기 있는지는 모른다. 진단 뒤 입력창은 비어 있었다. 지시문의 모델 줄만 `Fable 5.2 / xhigh`로 바꿔 다시 보냈다. 결정표의 모델 칸을 5.2로 바꾸는 일은 위의 회고 후보에 그대로 남긴다(`docs/model-selection.md`의 규약대로 공식 원문을 다시 대 봐야 한다).

## 이어받음

위 지시문으로 연 새 세션이다(2026-11-17 19시대). 세션 제목 `docs/postgres-foundation-design`, 모델 Fable 5.2. 주 체크아웃에서 시작해 `EnterWorktree(path)`로 이 워크트리에 들어왔다.

> 사용자: postgres-foundation 설계 인터뷰

첫 메시지는 위 "인계"의 지시문 그대로이고 모델 줄만 `Fable 5.2 / xhigh`다.

- 시작 전 확인: `ListAgents`에 이 기능을 맡은 세션은 같은 제목의 앞 세션(인계함) 하나였다. `git status`는 인계가 적은 변경 그대로였다. `uv run python tools/sibling_overlap.py`는 "번호 겹침 없음", "함께 고친 파일 없음"이었다(기준 `origin/dev` `21e7d8d`).
- ADR 초안을 고치기 전에 `domain-modeling`을 불렀다(`.claude/rules/adr.md`).

## 셀프 리뷰

`/code-review`를 돌렸다. 본 범위: base `21e7d8d63`, 추적 파일 9개, 커밋 0개, 미추적 2개(ADR 0066 초안, 이 일지). 표준 축은 sonnet·high로, 명세 축은 본 세션의 모델로 띄웠다. 명세는 기능 계획의 base 판, 위 라운드 1~5의 답, 합의 요약이다. 웹 조사 원문 넷의 발췌와 rag-engine ADR의 경로를 두 브리프에 실었다. 아래는 두 보고를 줄여 옮긴 것이다(서브에이전트가 쓴 글이다).

### Standards

도구: `check_adr_pointers`·`check_md_tables`·`check_instructions` 종료 0, `plan_table` 종료 0이고 `.scratch/plan.md` 불변.

- Major 1. 포인터 누락(`.claude/rules/adr.md` 둘째 항목). ADR 0042 결정 "18 저장소 교체"(51줄)의 "테스트는 pytest가 testcontainers로 PostgreSQL·Redis를 스스로 띄우고 없으면 실패한다"와 94줄 "testcontainers는 18", ADR 0043 17줄 "pytest가 testcontainers로 스스로 띄우고 … 쪽을 골랐다", ADR 0048 24줄 "배포 환경에 이미 PostgreSQL이 있으면 연결 문자열만 바꿔 그쪽에 붙일 수 있다". 0066은 "ADR 0048 그대로다"라 적었는데 deploy-package 계획의 새 문장은 같은 문장이 "agent-os의 데이터베이스에는 맞지 않고"라 적어 서로 어긋난다.
- Minor 2. "8개 … 공식 문서를 받아 본 보고다"가 일지의 "공식 문서로 확인한 것은 6개"를 뺐다. 선례의 Nextcloud는 저장한 `Updater.php` 214줄 "downgrades are unsupported"이고 스키마를 만나 시작을 거부하는 것과 다르다.
- Minor 3. pywin32는 pg_stack README가 "저장소 잠금에 이미 있다"고 적어, testcontainers를 거부하는 까닭으로 들기에 어긋난다.
- Minor 4. "프로브가 … Debian 판에서는 … 진입 스크립트와 사용자(uid 999)만 봤다"의 출처. README에는 `postgres --version`만 있고 나머지는 설계 세션의 `docker inspect`다(대 보니 값은 맞다).
- Minor 5. 용어. `CONTEXT.md`의 "제품 판"과 겹치게 "표의 판", "판 파일", "판 기록 표", "주 판"을 쓰고도 더할 말이 없다고 적었다.
- Minor 6. ADR 0056 24줄 "컨테이너는 root가 아닌 사용자로 돌고"가 포인터 범위 밖이다. 0066은 PostgreSQL 컨테이너가 root로 뜬다고 적었다.
- Minor 7. ops-backup-upgrade 계획이 PGDATA, uid 999, root 기동을 옮겨 적었다. "다른 행" 서술이 deploy-package diff의 "외부 PostgreSQL 지원 범위 밖" 문장을 말하지 않는다. diag-bundle 계획 5줄 "컨테이너는 다섯"은 손대지도 넘기지도 않았다.
- Minor 8. "모두의 커밋"의 갱신 목록. ADR 0038 22줄의 선례는 전제 환경을 tech.md 테스트 행, operations.md 가드레일 "기계마다 까는 것", README.md 시작 절, `.pre-commit-config.yaml` 머리 넷에 적고 헌법 판 patch를 말한다. 0066은 셋만 든다.
- Minor 9. compose가 연결 문자열을 짓고 비밀번호가 `.env` 한 줄이면 `@:/` 같은 글자의 퍼센트 인코딩이 열려 있다.
- Minor 10. "이 행의 PR도 느낌표 PR이다"는 이 문서 PR이 아니다. rc.1에서 올릴 때 `compose.yaml`도 바꿔야 한다는 것이 노트 대상으로 적히지 않았다.
- Nit 11. "`agent-os run` … 데이터베이스와 무관"에 "지금은"이 필요하다(ADR 0042의 trace-postgres). "새 런타임 의존성 셋"은 직접 의존성만 센 것이다. Ryuk 여덟은 README가 "손으로 봤다"로 적는데 ADR은 구분 없이 같은 문장에 넣었다.
- 확인함: `_configuration_problems`, pyproject 계약 이름과 주석, `run_checks.py` 17~18·123줄, ci.yml 잡 이름, release.yml 125줄, compose의 컨테이너 다섯과 포트 셋, README 9·11절, ADR 0056 인용 둘과 포인터 모양, ADR 0062·0064·0048·0049·0012·0034·0035 서술, tech.md·PRD 인용, http.md, pg_stack README 수치 전부, 일지의 사용자 인용 전부, 슬라이스 10·14, Blocked by 사슬, `v0.1.0-rc.1` 태그, port_shape, rag-engine ADR 0011·0002, 원문 사본 넷, 11개 중 8개의 이름 수.

### Spec

- Major 1. (a) 받는 행이 기다리지 않는다. ops-backup-upgrade의 `**Blocked by:** release-image`에 postgres-foundation도 widget-admin-server도 없다. 그 행은 지금 프론티어라 데이터베이스 없이 설계와 수락이 끝날 수 있다.
- Major 2. (a) 포인터 누락. ADR 0042 51줄, ADR 0048 24줄, ADR 0056 8줄 머리 문단 "컨테이너 다섯"(ADR 0064는 8·24줄 모두 달았다). ADR 0043 17줄은 사용자가 전에 "docker compose로 먼저 띄운 것에 붙고"를 거부했다고 적으니 반전임을 Considered에 밝혀야 한다.
- Major 3. (c) "표를 바꾸는 판은 가운데 자리가 오른다"는 출시 후보 단계에서 거짓이다. `tools/release.py`의 `_next_number`를 불러 보니 `feat!` 커밋이 rc 단계에서 `0.1.0-rc.2`, 정식 판 뒤에서 `0.2.0`이었다.
- Major 4. (c) 결정 "표를 올리는 때"와 "판 되돌리기"가 어긋난다. compose에서는 옛 판의 `migrate`가 `serve`보다 먼저 더 새 표를 만나 실패하므로(alembic의 동작은 어림) 라운드 5 설명의 "옛 판 serve가 … 찍고 멈춥니다"의 문구가 나오지 않는다.
- Major 5. (c) 결정 "compose 배치"의 `depends_on`. deploy-package 계획이 "다섯 컨테이너의 재시작 정책은 `unless-stopped`이고 `depends_on`은 두지 않는다"고 적는다(근거로 든 release-image 명세 336줄은 데몬이 다시 켜질 때 `depends_on`이 차례를 정하지 않았다고 적는다. 그 명세가 드는 프로브는 `.scratch/release-image/probes/bridge_recover/README.md`다). 언급도 "재지 않은 것" 항목도 없다.
- Major 6. (c) "비밀번호는 `.env`에 한 줄"은 고른 설명 둘("연결 문자열을 .env의 한 줄로", ".env에는 연결 문자열 한 줄이면 됩니다")과 다르다. 세 번째 확인 세부로 올린다.
- Minor 7. (a) multi-instance 계획에 "migrate 둘" 넘김이 없고, diag-bundle 계획의 "컨테이너는 다섯"을 누가 고치는지 없다.
- Minor 8. (c) widget-admin-server 계획의 "정할 것은 셋"과 ADR "다른 행"의 둘이 다르다. ops 계획의 "root로 떠서"는 단정인데 ADR은 `user`를 명세에 넘겼다.
- Minor 9. (a) 라운드 4의 대가 "ops-backup-upgrade의 범위가 조금 늘어납니다"와 수락 "테스트가 데이터베이스를 스스로 띄워"의 재해석이 빠졌다.
- Minor 10. (a) "명세가 짓는 것"에 digest 셋의 시험과 개발자의 로컬 데이터베이스가, "재지 않은 것"에 CI service container와 port_shape의 비동기 메서드가 없다.
- Minor 11. (c) "8개 … 공식 문서를 받아 본 보고"가 일지의 6개와 다르다.
- Nit. 세부 2의 인용이 합의 요약 12와 글자가 다르다. 빈 첫 판은 합의 요약 14와 어긋나지 않지만 확인 세부에 없다.
- 확인함: 기능 계획의 물음 전부, 합의 요약 1~18과 "모두에게 닿는 결과", 라벨 인용, rag-engine ADR 0011과의 일치와 차이 표시, pg_stack README의 수치, 배포 안내 9·11절, ADR 0056 24줄 포인터, mcp-trust·trace-postgres·deploy-package·widget-admin-server의 `Blocked by`, Considered Options.

요약: 표준 축 Major 1·Minor 9·Nit 1이고 가장 큰 것은 다른 ADR 셋의 포인터 누락이다. 명세 축 Major 6·Minor 5·Nit 2이고 가장 큰 것은 옛 판의 `migrate`가 `serve`보다 먼저 더 새 표를 만나는 갈래다.

### 반영

지적마다 근거를 이 세션에서 열어 본 뒤 판정했다. 고친 것은 열하나다.

- 포인터(표준 Major 1, 명세 Major 2, 표준 Minor 6). ADR 0042 51·94줄, ADR 0043 17줄, ADR 0048 24줄, ADR 0056 8·24줄을 읽어 문장을 대 봤다. `(바뀜: ADR 0066)`을 다섯 자리에 더 달아 모두 일곱이다. ADR 0056의 머리 문단과 결정 "컨테이너 배치"의 root 문장, ADR 0042의 두 자리, ADR 0043의 Considered Options 한 자리, ADR 0048의 한 자리다. ADR 0066 Consequences "다른 ADR"에 일곱을 적고, 결정 "테스트 데이터베이스"에 ADR 0042·0043이 고른 것을 PostgreSQL에 대해 뒤집는다고 적었다.
- 출시 후보 단계의 번호(명세 Major 3). `tools/release.py`의 `_next_number`(375~414줄)를 읽었다. 출시 후보 칸이 있으면 커밋을 보지 않고 차례만 올리고, 정식 판 뒤에는 `feat`이거나 느낌표면 가운데 자리를 올린다. 확인 세부 1과 Consequences "운영"의 11절 문장을 고쳤다.
- 옛 판의 `migrate`(명세 Major 4). 결정 "표를 올리는 때"에 `agent-os migrate`도 더 새 표의 판을 만나면 표를 건드리지 않고 같은 문구로 멈춘다고 채우고 확인 세부 넷째로 올렸다. alembic이 모르는 번호를 만났을 때의 동작은 어림으로 적었다.
- `depends_on`(명세 Major 5). `.scratch/release-image/spec.md` 336줄과 `.scratch/release-image/probes/bridge_recover/README.md` 결론 9를 읽었다. 결정 "compose 배치"에 그 명세가 `depends_on`을 두지 않기로 한 까닭과 이 ADR이 더하는 조건이 둘뿐이라는 것, 데몬이 다시 켜진 뒤의 갈래를 적고 deploy-package 계획에 한 문장을 더했다.
- `.env`의 한 줄(명세 Major 6, 표준 Minor 9). 결정 "비밀번호와 계정"에 고른 설명 둘을 글자 그대로 옮기고, 초안이 그 한 줄을 비밀번호로 채웠다는 것과 까닭(어림)을 적어 확인 세부 셋째로 올렸다. 비밀번호의 글자 문제를 "명세가 짓는 것"에 올렸다.
- 받는 행의 선행 조건(명세 Major 1). ops-backup-upgrade의 `**Blocked by:**`에 postgres-foundation과 widget-admin-server를 더하고 확인 세부 다섯째로 올렸다. 기능 계획들의 `**Blocked by:**` 줄을 grep으로 모아 순환이 없는 것을 봤다(손으로 봤다, Grep `^\*\*Blocked by:\*\*`).
- 근거의 표기(표준 Minor 2·3·4, 명세 Minor 11, 표준 Nit의 Ryuk). 8개 가운데 공식 문서로 확인했다고 보고된 것이 6개라는 것을 더했다. Nextcloud는 저장한 `nextcloud_updater.html` 214줄(`Updates between multiple major versions and downgrades are unsupported.`)을 grep으로 봤고, 시작을 거부하는 선례에서 빼 따로 적었다. pywin32 문장은 pg_stack README 73줄(저장소 잠금에 이미 있다)을 읽고 뺐다. Debian 판에서 프로브가 본 것과 설계 세션이 손으로 본 것을 갈랐다.
- 용어(표준 Minor 5). `CONTEXT.md` 51~52줄을 읽었다. ADR 머리에 "표의 판"과 "주 판"이 제품 판과 다른 말이라고 적고, "판 파일"을 "마이그레이션 파일"로 바꿨다.
- 넘김(표준 Minor 7, 명세 Minor 7·8). multi-instance 계획에 `migrate` 둘이 함께 도는 경우를, diag-bundle 계획에 컨테이너가 늘고 `serve`와 `migrate`가 멈추는 경우가 생긴다는 것을 적었다. ADR "다른 행"을 실제 diff에 맞췄다(deploy-package의 외부 PostgreSQL 문장, widget-admin-server가 정할 것 셋). ops 계획의 단정 "root로 떠서"를 공식 이미지의 기본 설정으로 좁혔다.
- 전제 환경을 적을 자리(표준 Minor 8). ADR 0038 22줄을 읽고 Consequences "모두의 커밋"의 목록을 그 넷과 헌법 판으로 넓혔다.
- 나머지(표준 Minor 10, 표준 Nit 11, 명세 Minor 9·10, 명세 Nit의 인용). 느낌표 PR이 되는 것은 단독 compose에 PostgreSQL을 더하는 티켓의 PR이고 `compose.yaml`도 바꿔야 한다고 적었다. `agent-os run`의 문장에 trace-postgres가 다시 정할 때까지라는 범위를 달았다. 직접 의존성 셋이라고 적었다. 라운드 4의 대가와 수락 조건의 읽기를 더했다. "명세가 짓는 것"과 "재지 않은 것"에 빠진 항목을 더했다. 확인 세부 2의 인용을 합의 요약 12의 글자로 고쳤다.

남긴 것은 둘이다.

- 표준 Minor 7 가운데 ops 계획이 PGDATA와 uid 999를 옮겨 적은 것. 넘기는 것은 받는 쪽 기능 계획 본문에 적는 것이 규칙이고(`code-review` 6단계 4) 같은 파일의 앞선 "넘긴 것" 문단들이 같은 모양이라 두었다.
- 명세 Nit 가운데 빈 첫 마이그레이션을 확인 세부에 올리는 것. 결정 "이 행이 짓는 표"가 어림으로 적어 명세에 넘겼고 합의 요약 14와 어긋나지 않아 올리지 않았다.

반영하며 새로 쓴 사실 문장이다(PR 직전 리뷰에 밀 주장으로 넘긴다).

- "0.1.0 전의 출시 후보 단계에서는 느낌표 PR이 들어도 `0.1.0-rc.N`의 차례만 오르고, 정식 판 뒤에는 가운데 자리가 오른다"
- "Nextcloud는 업데이터가 판 내리기를 예외로 거부한다"
- "release-image 명세는 `depends_on`을 두지 않기로 했다 … 프록시가 뒷단을 기다리느라 사이트 전체가 막히지 않게 하려는 것이었으므로"
- "그 명세의 프로브에서 `depends_on: service_healthy`는 데몬이 다시 켜져 컨테이너를 다시 띄울 때 차례를 정하지 않았다"
- "deploy-package는 portal-admin을 거쳐 이미 그 둘을 기다린다"
- "ADR 0038이 `rg`를 전제로 들일 때 적은 자리 넷"과 "ADR 0038의 선례는 patch였다"
- "포인터를 단 자리는 일곱이다"와 그 목록
- "port_shape 프로브는 작은 모듈 둘로 흉내 낸 모양 하나만 봤다"
- "그 절은 `.env`의 판 번호 한 줄만 말하므로"(배포 안내 11절)

다시 돌린 명령: `uv run python tools/check_adr_pointers.py`, `tools/check_md_tables.py`, `tools/check_line_separators.py`, `tools/check_instructions.py`는 넷 다 출력 없이 끝났다. `uv run python tools/plan_table.py`는 `.scratch/plan.md`의 두 줄을 바꿨다(ops-backup-upgrade 행의 선행 조건, 프론티어 목록에서 그 행이 빠짐). 손으로 치는 검증 명령 다섯은 커밋의 pre-commit 결과로 갈음하고, 결과는 커밋 뒤에 적는다.

### 승인 화면에 적을 사실을 대 봤다

승인 화면의 첫 호출을 훅(`hook_choice_facts`)이 막아, 화면의 설명에 적을 사실을 대 봤다. 셋 다 커밋하지 않은 스크래치 파일로 손으로 본 것이다.

- 판 번호. `tools/release.py`의 `_next_number`를 손으로 불렀다(`uv run python <스크래치>/next_number_check.py`). 출시 후보 칸이 `0.1.0`이고 지난 판이 `v0.1.0-rc.1`이면 `feat!` 커밋에서도 보통 `fix` 커밋에서도 `0.1.0-rc.2`였다. 칸이 없고 지난 판이 `v0.1.0`이면 `feat!`와 `fix!`가 `0.2.0`, 보통 `fix`가 `0.1.1`이었다. 명세 축의 보고와 같다. ADR 확인 세부 1의 괄호에 설계 세션도 불러 봤다고 더했다.
- compose의 변수 치환. 이 PC의 Docker Compose v5.6.1에서 `${DB_URL#postgresql://}`와 `${DB_URL%@*}`를 넣은 compose 파일의 `docker compose config`가 둘 다 `invalid interpolation format`으로 끝났다(종료 1). ADR 결정 "비밀번호와 계정"의 어림을 손으로 본 것과 남은 어림(다른 문법이 없다는 것, Compose 명세의 원문은 대 보지 않았다)으로 갈랐다.
- compose가 지은 주소. `--env-file`로 `DB_PASSWORD=p@s:s/w`를 주자 `docker compose config`가 `postgresql://agent_os:p@s:s/w@postgres:5432/agent_os`를 냈다. 값을 바꾸지 않고 끼워 넣는다. 그 주소를 SQLAlchemy가 어떻게 읽는지는 보지 않아 ADR에 어림으로 적고 "재지 않은 것"에 올렸다.
- 노트 규약. `docs/constitution/operations.md` 43줄("올릴 때 할 일 `upgrade/<이름>.md`. 제목 접두에 느낌표를 붙인 PR이 그 PR에 새로 싣는다")과 `tools/check_notes.py` 독스트링 31~33줄(느낌표가 없는데 `upgrade/` 파일을 새로 더하면 빨강)을 읽었다.

## 승인

### 확인 세부 넷을 확인받았다

ADR 0066 결정 "승인 때 함께 확인받는 세부"의 첫째부터 넷째까지를 선택 화면 하나로 물었다. 넷 다 추천을 골랐다. 질문과 고른 라벨과 그 설명을 글자 그대로 옮긴다.

1. 질문: "데이터베이스의 표 구조를 바꾸는 변경을 '올릴 때 운영자가 할 일이 있는 변경'으로 표시해서, 릴리스 노트에 '올리기 전에 데이터베이스를 백업하십시오'가 실리게 할까요?"

   > 사용자: 표시하고 노트에 싣는다 (Recommended)

   설명: "표 구조를 바꾸는 PR과, 배포 파일에 PostgreSQL을 처음 더하는 PR의 제목에 느낌표가 붙고, 릴리스 노트의 '올릴 때 할 일'에 백업 안내가 실립니다. 치르는 값은 판 번호입니다. 정식 판(0.1.0) 뒤에는 느낌표가 붙은 변경이 든 판의 가운데 자리가 오릅니다(예: 0.1.0 → 0.2.0. 새 기능이 든 판도 원래 그렇게 오릅니다). 0.1.0 전의 출시 후보 단계에서는 rc 차례만 오릅니다(0.1.0-rc.1 → 0.1.0-rc.2). 두 경우 모두 판 번호를 계산하는 함수를 직접 불러 확인했습니다."

   고르지 않은 선택지: "표시하지 않는다"(백업 안내를 배포 안내 문서에 따로 적는다).

2. 질문: "데이터베이스 라이브러리(SQLAlchemy)를 다루는 코드를 어댑터 층 한 곳으로 제한하면서, 서버를 조립하는 코드(server.py)도 그 라이브러리를 import하지 못하게 검사로 막을까요?"

   > 사용자: 조립 코드도 막는다 (Recommended)

   설명: "시작 코드(main)가 어댑터의 데이터베이스 객체를 만들어 넘기고, 서버 조립 코드는 미리 약속한 메서드 묶음(포트)으로만 그것을 씁니다. 나중에 데이터베이스 라이브러리를 바꿀 때 고칠 곳이 어댑터 한 곳입니다. 치르는 값은 포트를 하나 선언해야 한다는 것입니다."

   고르지 않은 선택지: "조립 코드에는 허용한다"(시작 코드가 엔진을 만들어 그대로 넘긴다).

3. 질문: "운영자가 .env 파일에 적는 한 줄을 '데이터베이스 연결 주소 전체'가 아니라 '비밀번호만'으로 할까요? (연결 주소는 배포 파일 compose가 그 비밀번호로 조립합니다.)"

   > 사용자: 비밀번호만 적는다 (Recommended)

   설명: "운영자는 비밀번호를 한 번만 적고, 배포 파일이 그 값으로 서버용 연결 주소를 만들며 같은 값을 PostgreSQL 컨테이너에도 넘깁니다. 치르는 값은 비밀번호의 글자 제약입니다. compose는 비밀번호를 주소에 그대로 끼워 넣기 때문에(직접 확인했습니다) @, :, / 같은 글자가 들면 주소가 깨질 수 있고, 그래서 배포 안내가 안전한 비밀번호를 만드는 명령을 주어야 합니다."

   고르지 않은 선택지: "연결 주소 전체를 적는다"(같은 비밀번호를 `.env`의 두 줄에 적게 된다).

4. 질문: "새 판으로 올렸다가 옛 판으로 되돌린 운영자에게, 서버보다 먼저 도는 migrate도 '데이터베이스가 이 판보다 새롭습니다. 되돌리려면 올리기 전의 백업을 복원하십시오'를 찍고 멈추게 할까요?"

   > 사용자: migrate도 안내하고 멈춘다 (Recommended)

   설명: "옛 판의 migrate가 표를 건드리지 않고 그 안내를 찍은 뒤 실패로 끝나며, 서버는 뜨지 않습니다. 운영자가 화면에서 원인과 해결 방법을 바로 봅니다."

   고르지 않은 선택지: "서버만 판정한다"(운영자가 alembic이 내는 오류를 보게 될 수 있다).

넷 다 초안이 채운 그대로라 ADR의 결정은 고치지 않았다.

### 다섯째 세부와 ADR 0066을 승인받았다

둘째 선택 화면으로 다섯째 세부와 ADR의 승인을 물었다. 띄우기 전에 기능 계획들의 `**Blocked by:**` 줄을 Grep으로 모아 다시 읽었다(손으로 봤다). deploy-package는 portal-admin을, portal-admin은 widget-admin-server와 admin-login을, 그 둘은 postgres-foundation을 기다린다. ops-backup-upgrade가 새로 기다리는 둘(postgres-foundation, widget-admin-server) 가운데 ops-backup-upgrade를 기다리는 것은 없어 순환이 없다.

5. 질문: "백업 기능(ops-backup-upgrade)의 설계를 '지금 바로 시작할 수 있는 기능' 목록에서 빼고, agent-os의 데이터베이스와 위젯 관리 서버의 데이터베이스가 생긴 뒤에 시작하게 할까요?"

   > 사용자: 데이터베이스가 생긴 뒤에 시작한다 (Recommended)

   설명: "백업 기능의 선행 조건에 postgres-foundation과 widget-admin-server를 더합니다. 백업 설계가 두 데이터베이스를 빠뜨리지 않게 됩니다. 치르는 값은 백업 기능을 미리 해 둘 수 없다는 것입니다. 새로 막히는 다른 기능은 없습니다. 배포 패키지(deploy-package)는 portal-admin을 거쳐 이미 그 둘을 기다리고 있습니다(기능 계획들의 선행 조건 줄을 읽어 확인했습니다)."

   고르지 않은 선택지: "지금처럼 바로 시작할 수 있게 둔다"(데이터베이스의 백업과 복원이 그 기능에서 빠질 수 있다).

6. 질문: "앞에서 확인하신 세부를 포함해서, ADR 0066(agent-os가 PostgreSQL에 닿는 방법, 표를 올리는 방법, 테스트 데이터베이스를 띄우는 방법)을 승인하시겠습니까?"

   > 사용자: 승인한다

   설명: "ADR 0066의 상태를 승인됨(accepted)으로 바꾸고, 기능 계획에 설계 줄을 적은 뒤 커밋과 PR과 병합까지 진행합니다. 그 다음 단계는 사용자가 부르는 명세 작성(to-spec)입니다."

   고르지 않은 선택지: "고칠 곳이 있다".

승인 화면 앞의 글로 함께 알린 것은 셋이다. 테스트 컨테이너 선택이 ADR 0042와 ADR 0043의 예전 결정을 PostgreSQL에 한해 뒤집는다는 것, "동봉한 것만 지원"이 ADR 0048의 문장을 agent-os의 데이터베이스에서는 지원하지 않는 길로 만든다는 것, 조사 근거에서 Nextcloud를 시작을 거부하는 선례에서 빼 따로 적었다는 것이다.

승인 뒤에 고친 것은 넷이다. ADR 0066의 `status`를 `accepted`로, `docs/adr/README.md`의 0066 행을 `accepted`로 바꿨다. ADR 결정 "승인 때 함께 확인받는 세부"의 머리에 다섯을 확인받았다는 문장을 더했다. `.scratch/postgres-foundation/plan.md`의 `**Blocked by:**` 줄 뒤에 `**설계:** ADR 0066`을 적었다.

`uv run python tools/plan_table.py`를 다시 돌렸고 `.scratch/plan.md`는 바뀌지 않았다(표에는 설계 줄의 칸이 없다). 커밋 전에 `git branch --show-current`는 `docs/postgres-foundation-design`이었고, `uv run python tools/sibling_overlap.py`는 "번호 겹침 없음"과 함께 고친 파일 하나(`mcp-shutdown-spec` 워크트리의 `.scratch/plan.md`)를 냈다. 그 파일은 도구가 만드는 파일이라, 그 브랜치가 먼저 병합되어 충돌하면 기준 브랜치를 합친 뒤 `plan_table.py`로 다시 만든다.

## 커밋과 인계 (커밋 뒤)

### 커밋

`4830b7ef8` "docs: PostgreSQL을 들이는 설계를 ADR 0066으로 남긴다 (postgres-foundation)". 파일 17개다. 커밋은 Bash의 600초 제한을 넘겨 백그라운드로 넘어간 뒤 종료 0으로 끝났다. pre-commit의 결과는 다음과 같다.

- `checks`(`tools/run_checks.py`의 CHECKS), markdown tables, line separators, mutation tables, quotes, commit message: Passed.
- ruff check, ruff format: 스테이지된 `.py`가 없어 Skipped. 손으로 쳤다. `uv run ruff check .`는 "All checks passed!", `uv run ruff format --check .`는 "2410 files already formatted"였다.
- canary specs, constitution version: 해당 파일이 없어 Skipped.

손으로 치는 검증 명령 다섯은 이 pre-commit 결과와 위의 ruff 둘로 갈음했다. LLM 시험과 e2e와 사진 비교는 이 변경(문서만)의 범위가 아니라 치지 않았다.

quotes 검사는 경고 25건을 냈고(막지 않는다) 하나씩 봤다.

- 일지 23건. 승인 화면의 질문과 설명을 옮긴 것이 12건(원문은 이 세션의 선택 화면이다), 인터뷰의 라벨이 2건, 저장소 밖 원문(Forgejo, Flyway 등)의 인용이 3건, 리뷰 보고가 그때의 초안을 줄여 옮긴 것이 5건이다. 남은 1건은 "ADR 초안" 절이 합의 요약 12를 "넘긴다"로 옮긴 것이고 원문은 "넘기고"라서 고쳤다(커밋 뒤의 수정이라 아직 커밋하지 않았다).
- ADR 0066의 2건. `serve`가 찍을 문구와 노트에 실을 문구로, 이 ADR이 새로 정하는 문장이라 저장소에 원문이 없다.

### PR 직전 리뷰에 더 밀 주장

"반영"의 목록에 더해, 승인 화면의 사실을 대 보며 ADR에 새로 쓴 문장 넷이다.

- "이 PC의 Docker Compose v5.6.1은 `${DB_URL#postgresql://}`와 `${DB_URL%@*}`를 `invalid interpolation format`으로 거부했다"
- "compose는 값을 바꾸지 않고 그대로 끼워 넣는다. 비밀번호 `p@s:s/w`로 지은 값이 `postgresql://agent_os:p@s:s/w@postgres:5432/agent_os`였다"
- "설계 세션도 2026-11-17에 그 함수를 손으로 불러 같은 값을 봤다. `fix!` 커밋도 정식 판 뒤에서 `0.2.0`이었다"
- "승인 화면에서 다섯을 하나씩 물어 확인받았다"로 시작하는 문장(고른 라벨 다섯과 "승인한다")

### 인계

커밋 명령 직후 인계 계기(`커밋 뒤`, 세션 컨텍스트 301,453 토큰)가 왔다. `handoff.md`의 인계하지 않는 때 다섯을 봤다. 커밋은 종료 0으로 성공했다. 이 세션이 받은 요청 범위는 PR과 병합까지라 커밋에서 끝나지 않는다. 이 세션의 지시문은 `인계: 셀프 리뷰 직전`으로 시작해 경계가 다르다. 이 세션이 쓴 `인계 못함` 줄이 없다. `get_session`의 `self`에 `parentSessionId`가 없다. 그래서 넘긴다. 이 세션의 제목은 `docs/postgres-foundation-design`이었다. 이 절과 175줄의 인용 고침은 커밋하지 않은 채 워크트리에 있다.

회고 후보는 앞 세션이 "인계" 절에 남긴 하나(결정표의 `Fable 5.1`이 앱 모델 메뉴의 첫 층에 없다)이고, 단계를 닫는 세션이 판정한다. 이 세션에서 더한 후보는 없다.

낸 지시문:

다음 작업: 기능 postgres-foundation. 승인된 ADR 0066의 커밋을 PR 직전 리뷰하고 회고한 뒤 PR을 열어 병합한다
다음 단계: 설계 인터뷰
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: postgres-foundation 설계 인터뷰
브랜치: docs/postgres-foundation-design
모델: Fable 5.2 / xhigh. 2의 잇는 지시문. 칸의 Fable 5.1은 앱 모델 메뉴의 첫 층에 없어 앞 인계의 open-session이 멈췄고, 그때 사용자가 다시 보내 달라고 해 5.2로 보냈으므로 같은 값을 쓴다
읽을 것: 일지 docs/journal/2026-11-17-1747-postgres-foundation-design.md의 "셀프 리뷰"의 "반영", "승인", "커밋과 인계 (커밋 뒤)" 절
이어받을 상태: 인계: 커밋 뒤. 이 브랜치에 커밋 하나가 있고 푸시하지 않았으며 PR은 없다. 그 커밋까지 한 것은 셀프 리뷰와 반영, ADR 0066의 사용자 승인(확인 세부 다섯 포함), ADR과 색인의 accepted, 기능 계획의 설계 줄이다. ADR 승인을 받았으므로 병합은 묻지 않는다. 일지의 "커밋과 인계 (커밋 뒤)" 절과 "ADR 초안" 절의 인용 고침 한 줄은 커밋하지 않은 채 워크트리에 있다. 남은 단계는 PR 직전 리뷰(`docs/constitution/operations.md` 리뷰 파이프라인 2. 밀 주장은 일지 "반영"의 목록과 "PR 직전 리뷰에 더 밀 주장"의 넷)와 그 반영, 회고(retro. 일지 "인계" 절이 남긴 모델 결정표 후보를 함께 판정한다)와 일지 "다음"(다음 단계는 사용자가 부르는 to-spec), 푸시와 PR, `merge.md`의 봇 회차와 병합, 다음 지시문이다. 일지 docs/journal/2026-11-17-1747-postgres-foundation-design.md
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지

제목을 `docs/postgres-foundation-design (인계함)`으로 바꿨다. 멈출 백그라운드 작업은 없었다. `git worktree unlock`은 `is not locked`로 끝나 넘어갔다.

open-session을 부른다 2026-11-17T11:23:55Z

## 이어받음 (PR 직전 리뷰부터)

위 "커밋과 인계 (커밋 뒤)"의 지시문으로 연 새 세션이다(2026-11-17 20시대). 세션 제목 `docs/postgres-foundation-design`, 모델 Fable 5.2. 주 체크아웃(`dev`)에서 시작해 `EnterWorktree(path)`로 이 워크트리에 들어왔다.

> 사용자: postgres-foundation 설계 인터뷰

첫 메시지는 위 "인계"의 지시문 그대로다.

- 시작 전 확인: `ListAgents`에 이 기능을 맡은 세션은 같은 제목의 앞 세션(인계함) 하나였다. `git status`는 인계가 적은 대로 이 일지 하나만 고쳐져 있었다. `git rev-parse --short origin/dev`는 `21e7d8d63`으로 이 브랜치의 기준과 같아 합칠 것이 없었다. `uv run python tools/sibling_overlap.py`는 "번호 겹침 없음"과 함께 고친 파일 하나(`mcp-shutdown-spec` 워크트리의 `.scratch/plan.md`)를 냈다.
- 스킬 사본: 이 세션이 시작한 주 체크아웃(`327b8e413`)과 이 브랜치의 기준(`21e7d8d63`) 사이에 `.claude/` 아래 파일은 바뀌지 않았다(`git diff --name-only`로 봤다). 그래서 Skill 도구가 싣는 사본과 디스크의 스킬이 같다.

## PR 직전 리뷰

`docs/constitution/operations.md` 리뷰 파이프라인 2다. 서브에이전트 둘을 나란히 띄웠다. `coderabbit-review`에는 기준 브랜치가 `origin/dev`라는 것을 일러 `--base origin/dev`를 붙이게 했다. CLI에는 주장을 넘기는 인자가 없으므로(`code-review` 6단계 1) 밀 주장 열셋(위 "반영"의 아홉과 "PR 직전 리뷰에 더 밀 주장"의 넷)은 `bug-perf-review`의 브리프에 자리와 근거를 붙여 넣었고 "나열 밖도 잰다"를 붙였다. 저장소 밖 근거로는 앞 세션이 저장한 웹 원문의 폴더(`…\352fc545-0015-4a24-a0d5-927f9bb450ce\scratchpad\web\`)와 rag-engine ADR 0011의 경로를 일렀다.

### bug-perf-review

아래는 보고를 줄여 옮긴 것이다(서브에이전트가 쓴 글이다). 기준 `21e7d8d63`, 범위는 파일 17개와 커밋하지 않은 일지 하나, 마지막 `[호출 36]`.

- 밀 주장 열셋은 모두 맞다고 했다.
  - 1·12. `tools/release.py`의 `_next_number`를 불렀다. 출시 후보 칸이 `0.1.0`이고 지난 판이 `v0.1.0-rc.1`이면 `feat!`·`fix!`·`fix` 모두 `0.1.0-rc.2`였고, 칸이 없고 지난 판이 `v0.1.0`이면 `feat!`와 `fix!`가 `0.2.0`, 보통 `fix`가 `0.1.1`이었다.
  - 2. 저장한 `nextcloud_updater.html` 210~215줄의 `doUpgrade`가 `isUpgradePossible`이 거짓이면 그 문장으로 예외를 던진다.
  - 3·4. `.scratch/release-image/spec.md` 336줄과 `bridge_recover/README.md` 25줄 결론 9가 ADR의 서술과 같다.
  - 5. `**Blocked by:**` 줄을 따라가니 deploy-package는 portal-admin을 거쳐 그 둘을 이미 기다리고, ops-backup-upgrade의 새 선행 조건에서 거슬러 올라가도 deploy-package가 나오지 않아 순환이 없다.
  - 6. ADR 0038 22줄에 자리 넷과 "헌법 버전은 patch다"가 있다.
  - 7. `(바뀜: ADR 0066)`은 ADR 0042에 둘(51·94줄), 0043에 하나(17줄), 0048에 하나(24줄), 0056에 셋(8줄과 24줄의 두 곳)으로 일곱이다. 인용한 본문 글자와 "ADR 0062·0064의 포인터 뒤에 잇는다"는 서술도 맞다.
  - 8. `port_shape/README.md` 3줄이 "그 모양 하나를 작은 모듈 둘로 흉내 내 잰다"고 적는다.
  - 9. 배포 안내 9절의 서술은 맞다. 11절은 끝자리만 오른 판에 `.env`의 `AGENT_OS_VERSION` 한 줄만 바꾸라고 하고 가운데 자리가 오른 판은 노트에 맡긴다. 그래서 "`.env`의 판 번호 한 줄만 말한다"는 엄밀히는 끝자리 판에 대한 서술이다(Minor). 그 절에 `compose.yaml`을 바꾸라는 안내가 없다는 결론은 그대로다.
  - 10·11. `docker compose version`은 v5.6.1이었고, `${DB_URL#postgresql://}`와 `${DB_URL%@*}`는 둘 다 `invalid interpolation format`으로 거부됐다. `DB_PASSWORD=p@s:s/w`를 `--env-file`로 주니 `postgresql://agent_os:p@s:s/w@postgres:5432/agent_os`가 그대로 나왔다.
  - 13. 일지 "승인" 절의 `> 사용자:` 줄 여섯이 ADR의 라벨 다섯과 "승인한다"에 글자가 같다(일지의 `(Recommended)`는 ADR이 뺐다).
- 나열 밖에서 대 본 것: pg_stack README의 수치(판 셋, 168.5MB·474MB, 120.2MB·304MB, 27.39~30.45초, 65.36~82.8초, 9.44~12.27초, 39줄, 2030-11-14), 코드 인용 다섯(`main.py`의 `_configuration_problems`, `adapters/mcp.py`의 `_http_session`, `pyproject.toml`의 주석, `run_checks.py` 17~18·123줄, `release.yml` 125줄), 기능 계획 여섯의 diff가 ADR "다른 행"의 서술과 맞았다.
- 유효 지적 0, Minor 서술 정밀도 하나(위 9), 보류 한 묶음. 보류는 예산 때문에 열지 못한 것이다. deploy-package·ops-backup-upgrade·trace-postgres 계획의 긴 변경 줄, ADR 0042 94줄이 Consequences 절 안인지, mcp-trust가 슬라이스 10인지다.

### 보류를 본 세션이 대 봤다

- 계획 셋의 변경 줄은 `git diff --word-diff=porcelain 21e7d8d63 HEAD`의 더한 줄을 읽었다(손으로 봤다). deploy-package에는 배포 안내 9절의 반입 명령이 postgres에도 태그를 붙여 옮기게 바뀐다는 것, "배포 환경에 이미 PostgreSQL이 있으면 연결 문자열만 바꿔 그쪽에 붙인다"가 agent-os의 데이터베이스에는 맞지 않는다는 것, "`depends_on`은 두지 않는다"가 프록시와 뒷단 사이에만 맞는다는 것이 있다. ops-backup-upgrade에는 두 데이터베이스의 백업과 복원, 주 판 올림, 올리기 전 백업, 선행 조건을 더한 까닭이 있다. trace-postgres에는 testcontainers를 거부하고 미리 띄운 컨테이너를 고른 것과 `agent-os run`이 데이터베이스와 무관하다는 것이 있다. 셋 다 ADR 0066 Consequences "다른 행"의 서술과 맞는다.
- ADR 0042의 94줄은 90줄 `## Consequences` 아래 항목이다(파일을 읽었다). `.scratch/mcp-trust/plan.md` 2줄은 `**슬라이스:** 10`이다(파일을 읽었다).

### 반영 (bug-perf-review)

고친 것은 둘이다.

- Minor 9. `deploy/standalone/README.md` 289줄(11절의 본문 한 문단)을 읽고 ADR 0066 Consequences "운영"의 문장을 고쳤다. "그 절은 `.env`의 판 번호 한 줄만 말하므로"를 "그 절은 끝자리만 오른 판에 `.env`의 판 번호 한 줄만 바꾸라고 하고 가운데 자리가 오른 판은 노트에 맡길 뿐 `compose.yaml`을 바꾸라는 말이 없으므로"로 바꿨다. ADR을 고치기 전에 `domain-modeling`을 불렀다(`.claude/rules/adr.md`).
- 보류를 대 보다 본 것. ops-backup-upgrade 계획의 넘김 문단이 "옛 판의 `serve`는 더 새 표를 만나면 백업을 복원하라고 찍고 멈춘다"고만 적었다. 셀프 리뷰 반영(명세 Major 4)으로 ADR 결정 "표를 올리는 때"는 단독 compose에서 먼저 도는 `migrate`가 그 문구를 찍고 `serve`는 뜨지 않는다고 정했으므로, 그 문장을 "`agent-os migrate`와 `serve`는 … (단독 compose에서는 먼저 도는 `migrate`가 그 문구를 찍고 `serve`는 뜨지 않는다)"로 맞췄다.

남긴 것은 없다.

### coderabbit-review

아래는 보고를 줄여 옮긴 것이다(서브에이전트가 쓴 글이다). CLI 0.7.5, `Plan: Free`, `Seat: not assigned`. `coderabbit review --agent --include-untracked --base origin/dev`가 끝까지 돌아 `review_completed`를 냈고(`--base`는 거부되지 않았고 `review_context`의 baseBranch가 `origin/dev`였다) 지적은 셋이다. 유효 0, 보류 2, 오탐 1.

- [Major, 보류] ADR 0066 20줄. 데이터베이스 비밀번호가 `serve`의 환경 변수에 놓이면 http 모양의 MCP 매니페스트가 `[server.headers]`로 그 값을 바깥 주소로 보낼 수 있다. 위험은 실재하지만 ADR 결정 "비밀번호와 계정"과 Consequences "신뢰와 노출"이 같은 노출을 이미 적었고, 사용자가 추천(비밀 파일) 대신 ".env에 둠"을 골랐다. 문서의 결함이 아니라 결정에 대한 이의다.
- [Major, 보류] `.scratch/mcp-trust/plan.md` 5줄. 같은 쟁점이다. 0.1 판의 연결 경로에 보호를 넣고 슬라이스 10의 허락 목록에 기대지 말라는 요구다. 그 문단은 "0.1 판에는 이 노출이 그대로 있다"고 적는다. 앞당길지는 계획의 순서와 범위를 바꾸는 판단이다.
- [오탐] ADR 0048 24줄. 그 문장과 ADR 0066 포인터를 지우라는 지적이다. `.claude/rules/adr.md`는 다른 ADR이 본문의 결정을 바꾸면 그 문장 뒤에 포인터를 달고 본문의 글자는 고치지 않게 한다.

이 서브에이전트는 CLI를 백그라운드로 띄운 채 리뷰가 끝나기 전에 중간 보고로 턴을 끝냈다. 본 세션이 출력 파일의 이벤트 종류를 `grep -o`로 보고(`finding` 셋과 `review_completed`. 손으로 봤다) 서브에이전트를 다시 불러 트리아지를 시켰다. 다시 부른 턴의 보고는 "결과마다 보고 하나"로 거부되어 오지 않았고, 한 번 더 불러서 받았다.

### 반영 (coderabbit-review)

고친 것은 없다. 남긴 것은 보류 둘이고 같은 쟁점이다.

- 판정: 둔다. 사용자가 라운드 3에서 대가(ADR 0049의 길에 놓인다, 지금의 API 키도 같은 처지다)를 적은 설명을 보고 ".env에 둠"을 골랐고, ADR 0066이 거부한 안("비밀번호를 비밀 파일로 넘긴다")과 대가를 적었으며, 승인 화면의 셋째에서 같은 자리를 다시 확인받았다.
- 고치는 데 드는 값: 작지 않다. 비밀 파일로 바꾸는 것은 승인된 ADR의 결정을 뒤집는 일이고, mcp-trust의 허락 목록 가운데 이 변수의 몫만 앞당기는 것은 기능 계획의 순서를 바꾸는 일이라 둘 다 사용자의 판단이다. PR 본문의 "남긴 위험"과 체크리스트의 그 줄에 적는다.

### 커밋 전 확인

`git branch --show-current`는 `docs/postgres-foundation-design`이었다. `uv run python tools/sibling_overlap.py`는 "번호 겹침 없음"으로 끝났다(이 브랜치의 새 번호는 ADR 0066이고 `origin/dev`는 `21e7d8d` 그대로다). 함께 고친 파일로는 `mcp-shutdown-spec` 워크트리의 `.scratch/plan.md`가 나왔다. 나중에 병합하는 쪽의 글자 충돌 후보다. `tools/check_adr_pointers.py`, `tools/check_md_tables.py`, `tools/check_line_separators.py`, `tools/check_instructions.py`는 출력 없이 끝났고, `tools/plan_table.py`를 돌린 뒤 `.scratch/plan.md`는 바뀌지 않았다(손으로 봤다, 이 세션).

## 회고

단계(설계 인터뷰)를 닫으며 돌렸다. 원천은 이 일지 전체(설계 세션, 셀프 리뷰 세션, 이 세션)다. `writing-for-agents`를 불렀다. 낸 후보는 아홉이고 승인 여섯(모두 회차로 세는 것이거나 대기열의 새 항목), 기각 셋, 넘김 0이다. 이 세션에서 반영한 것은 없어 harness 티켓을 쓰지 않았다.

1. **승인(회차).** 셀프 리뷰를 넘기던 `open-session`이 "5초 안에 모델 메뉴의 'Fable 5.1' 을(를) 찾지 못했다."로 멈췄고(위 "인계"), 사용자가 다시 보내 달라고 해 `Fable 5.2`로 보냈다. 열린 항목 `model-menu-name-fable-5-1-stale`이 처방한 사건이라 그 항목에 더했다. 4회차다. 앞 세션이 "인계" 절에 남긴 모델 결정표 후보가 이것이다. 이름을 무엇으로 바꿀지는 그 항목이 적은 대로 사용자의 몫이고 ADR 0029의 이력이 든다.
2. **승인(회차).** ADR 0066 초안이 바꾸는 다른 ADR의 본문 문장(ADR 0042의 두 자리, ADR 0043, ADR 0048, ADR 0056의 머리 문단과 root 문장)에 포인터를 달지 않아 셀프 리뷰 두 축이 잡았다(위 "셀프 리뷰"의 표준 Major 1·Minor 6, 명세 Major 2). 구현 때 실리는 지침(`.claude/rules/adr.md`)을 어겨 리뷰가 잡은 사건이다. 열린 항목 `adr-pointer-missed-on-uncited-sentence`에 더했다. 7회차다.
3. **승인(회차).** ADR 초안이 조사 보고의 "8개 가운데 공식 문서로 확인한 것은 6개"를 빼고 옮겼고, Nextcloud를 저장한 원문과 다른 선례 묶음에 넣었으며, 프로브 README에 `postgres --version`만 있는 Debian 판을 프로브가 더 본 것처럼 적어 셀프 리뷰 두 축이 잡았다(표준 Minor 2·4, 명세 Minor 11). 열린 항목 `adr-evidence-stronger-than-journal`이 처방한 사건이라 그 항목에 더했다. 6회차다.
4. **승인(회차).** 문서만 바꾼 커밋 `4830b7ef8`의 pre-commit이 Bash의 600초 제한을 넘겨 백그라운드로 넘어갔다(위 "커밋"). 열린 항목 `docs-only-commit-precommit-slow-again`에 더했다. 11회차다.
5. **승인(회차).** 일지의 "조사" 절이 웹 원문을 저장한 폴더를 `…/scratchpad/web/`로 줄여 적어, 이 세션이 `bug-perf-review`의 브리프에 넣을 경로를 찾느라 임시 폴더를 두 번 훑었다(`ls` 출력 둘, 약 32,000자). 열린 항목 0528(인계 일지에 저장소 밖 근거 사본의 절대 경로를 적는다)이 처방한 사건이라 그 항목에 더했다. 3회차다.
6. **승인(새 항목).** `coderabbit-review`가 CLI를 백그라운드로 띄운 채 리뷰가 끝나기 전에 중간 보고로 턴을 끝내, 본 세션이 두 번 다시 불러서야 트리아지를 받았다(위 "coderabbit-review"). 사건이 있고, 고칠 자리가 서브에이전트 정의의 문장이라 검사로는 옮길 수 없으며, PR 하나로 되돌릴 수 있다. 더하는 것이라 다섯 번째까지 회차를 센다. 같은 일을 다룬 항목을 `queue_open_rows.py --search`로 찾았고(낱말 `coderabbit-review`, `SubagentHandback`, `review_completed`, `백그라운드로.넘`), 턴 한도에서 보고 없이 멈춘 0559는 같은 정의의 다른 사건이라 새 항목 `coderabbit-review-hands-back-before-cli-finishes`를 썼다. 1회차다.
7. **기각.** 셀프 리뷰 명세 축이 잡은 설계의 빈 곳 넷(받는 행의 선행 조건, 옛 판의 `migrate`가 먼저 도는 갈래, `depends_on`, `.env`의 한 줄)과 출시 후보 단계의 번호. 리뷰가 잡도록 둔 기준(`code-review` 두 브리프의 명세 대조와 주장 검증)이 잡은 것이라 회차로 세지 않고, 검사로 옮길 수 없으며 표준에 더할 새 기준도 아니다.
8. **기각.** 이 세션의 큰 도구 출력 둘. 큰 결과 알림 훅이 그 자리에서 알렸고, 원인은 5로 셌다.
9. **기각.** ADR 0066의 파일 이름을 추측해 Read가 한 번 실패한 것. 도구가 바로 오류로 알렸고 Glob 한 번으로 찾았다.

만료: `uv run python tools/queue_open_rows.py`의 "만료할 항목"은 없었다.

## 다음

- **postgres-foundation의 설계는 닫혔다.** ADR 0066이 승인됐고 기능 계획에 `**설계:**` 줄이 있다. 이 기능을 막던 release-image는 done이라(`.scratch/plan.md`) 이 기능의 다음 단계는 명세다. 명세는 사용자가 부른다(`/to-spec`). 명세가 정할 것은 ADR 0066 Consequences "명세가 짓는 것"이 목록으로 들고, 결정 절이 명세에 넘긴 어림 둘(표를 만들지 않는 첫 마이그레이션으로 판 기록 표에 줄이 남는지, `tests/` 안의 테스트 도우미 하나를 두 패키지의 시험이 함께 쓸 수 있는지)은 명세가 잰다.
- **이 기능을 기다리는 행은 셋이다.** admin-login, widget-admin-server, ops-backup-upgrade다(`.scratch/plan.md`). widget-admin-server의 명세는 이 행이 짓는 테스트 도우미를 그 패키지의 시험이 쓰는 방법과 그 서버의 표를 올리는 때를 정하고(ADR 0066 결정 "위젯 관리 서버"), ops-backup-upgrade는 데이터베이스의 백업과 복원, 옛 판으로 돌아가는 길을 받았다(그 기능 계획의 넘김 문단. PR 직전 리뷰에서 한 문장을 고쳤다).
- **0.1 판에는 데이터베이스 비밀번호의 노출이 남는다.** 비밀번호가 `.env`를 거쳐 `serve`의 환경 변수에 놓이므로 http 모양의 MCP 매니페스트가 그 값을 밖으로 보낼 수 있고(ADR 0049의 길), 그것을 막는 mcp-trust는 슬라이스 10이다. CodeRabbit CLI가 이것을 두 번 짚었고 두었다(위 "반영 (coderabbit-review)"). 사용자가 라운드 3에서 대가를 보고 고른 값이라, 바꾸려면 ADR 0066의 이력에 쌓는다.
- **대기열.** 새 항목 `coderabbit-review-hands-back-before-cli-finishes`(1회차). 회차를 더한 다섯은 `model-menu-name-fable-5-1-stale`(4회차), `adr-pointer-missed-on-uncited-sentence`(7회차), `adr-evidence-stronger-than-journal`(6회차), `docs-only-commit-precommit-slow-again`(11회차), 0528(3회차)이다. `model-menu-name-fable-5-1-stale`은 사용자가 이름을 정해야 닫히고, 그때까지 설계 인터뷰나 명세 지시문의 "모델" 줄은 지금 메뉴에 있는 이름(`Fable 5.2`)으로 적는다. 회차 5 이상인 열린 항목은 스물하나다(`uv run python tools/queue_open_rows.py`의 "회차 5 이상").
