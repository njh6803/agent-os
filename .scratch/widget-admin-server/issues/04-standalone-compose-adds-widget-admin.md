# 04: 단독 compose를 띄우면 위젯 쪽 PostgreSQL과 위젯 관리 서버가 함께 뜨고, 방문자용 포트의 `/widget-settings/<사이트 이름>`이 위젯 설정을 낸다

**What to build:** 운영자가 새 판의 배포 파일 묶음으로 `compose.yaml`을 바꾸고 `.env`에 `WIDGET_ADMIN_DATABASE_PASSWORD` 한 줄을 더한 뒤 `docker compose up -d`를 치면, 위젯 쪽 PostgreSQL(`widget-admin-postgres`)이 뜨고 `widget-admin-migrate`가 위젯 쪽 표를 올린 뒤 `Exited (0)`으로 남으며, 위젯 관리 서버(`widget-admin`)가 뜬다(사용자 이야기 10, 11, 13). 위젯 쪽 데이터는 Agent OS 쪽과 다른 데이터베이스와 볼륨 `agent-os_widget-database`에 들고(9), 내렸다 다시 띄워도 남는다. 그 줄이 빠진 채 띄우면 compose가 어느 줄이 없는지 말하고 아무것도 띄우지 않는다(12). 위젯 쪽 PostgreSQL과 위젯 관리 서버는 어느 주소에도 발행되지 않고(20), 방문자용 포트의 프록시는 `/widget-settings/`만 넘기며 `/operator/`와 `/internal/`은 프록시의 404다(22). 판 내기가 위젯 관리 서버의 이미지 `agent-os-widget-admin`을 Agent OS의 이미지와 같은 판 번호로 짓고 올리며(24), 그 이미지에는 Agent OS의 코드와 모델 SDK가 없고(25), 컨테이너는 uid 10001과 읽기 전용 루트로 돈다(26). uid는 컨테이너 안에서 프로그램이 도는 사용자의 번호이고, 10001은 관리자(root, 0번)가 아닌 앱 사용자다. 배포 안내가 위젯 쪽 비밀번호를 바꾸는 절차와 인터넷이 막힌 서버로 새 이미지까지 옮기는 명령을 적는다(19, 23). 위젯 쪽 마이그레이션 파일을 더하는 PR은 느낌표 없이 지나가지 않고, 그 판의 노트가 백업을 알린다(27, 44).

운영자가 `compose.yaml`을 바꾸고 비밀번호 줄을 더해야 하므로 PR 제목에 느낌표를 붙인다(명세 "티켓을 나눌 때 함께 둘 것"의 넷째, ADR 0066 결정 "승인 때 함께 확인받는 세부"의 첫째와 같은 까닭). 이 티켓은 03을 기다린다. 시작 검사가 없는 서버를 compose에 띄우면 표가 없을 때 멈추지 않고 떠서 모든 요청에 500을 낸다.

근거는 명세 `.scratch/widget-admin-server/spec.md`의 "판 번호와 출시"(이미지의 목록과 하이픈 고침과 목록 맞대기), "이미지", "단독 compose", "프록시", "배포 안내", "노트 검사와 저장소 상태 시험", "문서와 하네스"에서 배포의 변경이 싣는 것, "사람이 할 일", Testing Decisions의 둘째 이음매다. 그 절들이 원천으로 가리키는 postgres-foundation 명세 `.scratch/postgres-foundation/spec.md`의 "단독 compose의 PostgreSQL과 migrate"와 "배포 안내"도 근거이고, 선례 티켓은 `.scratch/postgres-foundation/issues/02-standalone-compose-adds-postgres.md`다. 결정은 ADR 0064 결정 "배포에 느는 것", ADR 0066, ADR 0056이다. 측정은 `.scratch/widget-admin-server/probes/uv_workspace/`의 images 갈래와 `.scratch/postgres-foundation/probes/compose_shape/`다. 이 티켓의 "명세 검토"와 그 번호(S10, S12 같은 것)는 일지 `docs/journal/2026-11-24-2305-widget-admin-server-tickets.md`의 "명세 검토" 절을 가리킨다.

이 티켓은 크다. 사용자가 이것을 둘로 더 나누는 "5장"을 고르지 않았다(같은 일지의 "사용자에게 물은 것 하나"). 짓기 대상과 compose의 참조를 가르면 앞 변경이 지금 시험(`tests/tools/test_release_ci.py`의 `test_배포_compose의_이미지_줄은_짓기_목록의_저장소_이름과_같다`)을 잠시 느슨하게 고쳐야 하기 때문이다. 세션이 도중에 인계되면 아래 묶음 단위로 끊되, 짓기 목록과 compose와 배포 안내의 대응표는 한 커밋에 든다.

**Blocked by:** 03(`widget-admin serve`와 `widget-admin migrate`가 서고, 데이터베이스가 준비되지 않으면 서버가 이유를 한 줄로 찍고 멈춘다)

**Status:** ready-for-agent

### 사람이 할 일

- [ ] 이 티켓이 든 판을 처음 내기 전에, Docker Hub의 계정 아래에 공개 저장소 `agent-os-widget-admin`을 사람이 미리 만든다. 이 티켓의 세션이 그 일을 사람에게 알리고, 판 내기의 워크플로가 그 저장소를 쓰기 전에 만들었는지 확인받는다(명세 "사람이 할 일")

### 이미지

- [ ] `deploy/images/widget-admin.Dockerfile`과 그 `.dockerignore`가 명세 "이미지"대로다. 바탕 이미지와 uv 이미지는 serve 이미지와 같은 digest(이미지 내용의 해시로 판을 하나로 못 박은 값), 앱 사용자 uid 10001, 표지 파일 `/etc/agent-os/image`(우리 이미지 안에서 돈다는 것을 프로그램이 알아보게 이미지에 굽는 파일. 서버가 이 컴퓨터 안에서만 닿는 주소에만 열리게 하는 루프백 규칙이 컨테이너에서 `0.0.0.0`을 받는 예외를 이 파일로 가른다), 읽기 전용 루트, 멤버 하나만 까는 파이썬 단계, 짓는 동안 멤버 `pyproject.toml`의 사본에 판 번호를 넣는 것, `http://127.0.0.1:8100/health`를 부르는 상태 확인이다
- [ ] 지은 이미지 안에 `agent-os` 묶음도 `agent_os` 패키지도 LangChain도 없고, `widget-admin` 묶음 판이 넣은 판 번호이며, 마이그레이션 `0001`과 명령 `widget-admin`이 있는 것을 본다(사용자 이야기 25, 명세 검토 S12). 손으로 본 것이면 일지에 적고, 단독 배포 e2e의 사례로 둘 수 있으면 둔다
- [ ] 짓기 설정 `deploy/images/docker-bake.hcl`에 대상 `widget-admin`(태그 `${NAMESPACE}/agent-os-widget-admin:${TAG}`)을 더하고, `group "default"`의 `targets`와 머리 주석과 이름을 나열한 줄을 고친다

### 판 내기 목록

- [ ] `tools/release_ci.py`의 `IMAGES`에 `widget-admin`을 더한다
- [ ] `.github/workflows/release.yml`이 이미지 이름을 직접 적은 자리를 모두 고친다. 반복문 셋(점검, 올린 digest의 조회, 번호 태그), 노트를 짓는 명령의 `--grype` 인자, 첫째 잡의 출력, 둘째 잡의 환경 `DIGEST_*`, 아티팩트 대조의 인자, 머리 주석의 "이미지 넷"이다(명세 "판 번호와 출시"의 줄 번호는 기준 커밋의 것이라 다시 찾는다)
- [ ] 번호 태그의 반복문이 이미지 이름에서 변수 이름을 지을 때 하이픈이 남지 않게 고친다. 이미지와 짓기 대상과 저장소의 이름은 그대로 `widget-admin`과 `agent-os-widget-admin`이다. 고친 반복문을 리눅스의 bash(컨테이너든 CI든)에서 한 번 돌려 다섯 이름이 모두 풀리는 것을 일지에 적는다(이 PC의 Git Bash가 `bad substitution`이었고 리눅스도 같다고 본 것은 어림이다)
- [ ] `tests/tools/test_release_ci.py`에 워크플로의 반복문 셋과 `--grype` 인자와 첫째 잡의 출력과 둘째 잡의 환경, 짓기 설정의 `group "default"`가 `IMAGES`와 같은 이름들인지 보는 사례를 더하고, 하나를 뺀 변이 사례를 둔다(명세 "판 번호와 출시"의 목록 맞대기)
- [ ] 워크플로 감사(zizmor)가 초록이다

### 단독 compose와 프록시

- [ ] `deploy/standalone/compose.yaml`에 서비스 셋(`widget-admin-postgres`, `widget-admin-migrate`, `widget-admin`)과 볼륨 `widget-database`를 명세 "단독 compose"대로 더하고, 파일 머리와 `ports`·`user` 항목과 `serve`의 `env_file` 위 주석을 고친다. `.env`를 통째로 받는 것은 `serve`뿐이다
- [ ] 세 서비스의 `WIDGET_ADMIN_DATABASE_PASSWORD`가 모두 `:?`꼴이고, 줄이 없거나 빈 `.env`에서 `docker compose config`와 `up -d`가 그 이름을 든 글로 1이며 컨테이너가 하나도 생기지 않는 것을 이 PC에서 한 번 보고 일지에 적는다(사용자 이야기 12, 명세 검토 S12. 선례 티켓의 같은 기준)
- [ ] `deploy/standalone/proxy/site.conf`에 상류 `up_widget_admin`과 location 둘(`/widget-settings/`, `= /widget-settings`)을 명세 "프록시"대로 더한다. location에 `add_header`와 `limit_req`를 적지 않는다. nginx가 `%0A`와 `%2F`가 든 이름을 어떤 꼴로 넘기는지는 아래 e2e의 404 사례가 처음 본다(명세 검토 "확인하지 못한 것")
- [ ] `deploy/standalone/.env.example`에 값이 빈 `WIDGET_ADMIN_DATABASE_PASSWORD=`를 더한다

### 배포 안내

- [ ] `deploy/standalone/README.md`의 3-1, 4, 7, 8, 9, 11, 12절을 명세 "배포 안내"대로 고친다
- [ ] 9절의 고친 명령(`WIDGET_ADMIN_DATABASE_PASSWORD=unused`를 더한 두 명령, `save.txt`, 덮어쓰기 파일의 `widget-admin-postgres:` 아래 `image: agent-os-postgres:local`)과 12절의 위젯 쪽 비밀번호 바꾸기 네 줄(데이터가 있는 위젯 쪽 볼륨에서)을 실제로 돌려 보고, 명세의 글자가 아니라 돌려 본 꼴로 싣는다. 돌려 본 명령과 결과를 일지와 PR에 남긴다(ADR 0056 결정 "인터넷이 막힌 곳")
- [ ] 19와 23(위젯 쪽 비밀번호 바꾸기, 인터넷이 막힌 서버로 새 이미지까지 옮기기)의 낱말이 안내에 있는지 `tests/tools/test_deploy_guide.py`가 보는 자리에 더한다(명세 검토 S12). 지금 그 시험이 Agent OS 쪽의 같은 절을 보는 꼴을 따른다

### 저장소 상태 시험과 기존 시험

- [ ] `tests/test_postgres_image_pin.py`가 단독 compose의 PostgreSQL 서비스 둘을 모두 보고, 둘이 같은 digest여야 한다
- [ ] `tests/tools/test_deploy_guide.py`의 7절 전제와 권한 시험을 `widget-admin-postgres`에도 걸고, 위젯 관리 서버의 서비스에 `ports`가 없고 `user`를 더하지 않는다는 것을 "우리 이미지" 전제에 넣는다. 하나씩 빼는 변이 시험을 둔다
- [ ] 지금 시험 셋을 새 서비스에 맞게 고친다(명세 검토 S10). `tests/tools/test_release_ci.py`의 compose 대조가 짓기 대상이 아닌 서비스로 `migrate` 하나만 빼는 것(467줄)을 `widget-admin-migrate`도 위젯 관리 서버의 저장소 이름으로 빼게 고치고, 배포 안내 대응표의 정규식(477줄 `` `([a-z]+)` ``)이 하이픈이 든 서비스 이름을 읽게 고친다. 단독 배포 e2e의 서비스 목록(`web/packages/e2e-standalone/e2e/deployment.e2e.ts`의 `SERVICES`)에 새 서비스를 더한다. 줄 번호는 기준 커밋의 것이라 다시 찾는다

### 노트 검사와 판의 원고

- [ ] `tools/check_notes.py`의 `PRODUCT_MIGRATIONS`에 위젯 쪽 제품 마이그레이션 폴더를 더하고, `tests/tools/test_check_notes.py`에 그 폴더의 사례(느낌표 없이 파일을 더한 PR을 막는다)를 더한다(명세 "노트 검사와 저장소 상태 시험"의 첫 항목)
- [ ] 그 값을 읽는 마이그레이션 꼴 시험(`tests/test_postgres_migration_shape.py`)도 함께 고친다. 01은 그 시험 안에 위젯 쪽 폴더를 따로 더해 두었으므로, 이 티켓이 `PRODUCT_MIGRATIONS`를 두 폴더로 바꾸면 꼴 시험이 그 값 하나에서 폴더 목록을 읽게 바꾸고 따로 더한 자리를 걷는다. 폴더 목록의 원천이 노트 검사 하나가 된다. 걷은 뒤에도 그 시험이 두 폴더를 모두 훑고 폴더마다 파일이 하나 이상인지 보는지 확인한다
- [ ] PR 제목에 느낌표를 붙이고 `docs/release-notes/upgrade/`에 원고를 싣는다. 원고는 새 묶음의 `compose.yaml`로 통째로 바꾸라는 것, `.env`에 `WIDGET_ADMIN_DATABASE_PASSWORD` 줄을 더하라는 것(만드는 명령 `openssl rand -hex 32`와 함께, Agent OS 쪽과 다른 값), 위젯 쪽 데이터베이스가 새로 생긴다는 것을 싣는다(명세 "티켓을 나눌 때 함께 둘 것"의 넷째)

### 문서

- [ ] `docs/constitution/tech.md`의 레지스트리 칸("공개 저장소 넷"을 다섯으로)과 CI 칸("이미지 넷"을 다섯으로)을 고치고 헌법 판을 patch로 올린다. 판은 커밋 직전의 `tools/sibling_overlap.py`가 낸 형제의 가장 높은 판보다 높게 고른다(ADR 0038의 선례)
- [ ] "이미지 넷"과 "네 이미지"와 "우리 이미지 넷" 같은 옛 표현을 저장소 전체에서 grep해 살아 있는 문서와 주석의 잔존이 0인지 본다(작업 규약 4). 일지와 닫힌 티켓 같은 기록은 고치지 않는다(`docs/constitution/operations.md` 문서 위치)

### 단독 배포 e2e(명세 Testing Decisions 둘째 이음매)

- [ ] `web/packages/e2e-standalone/e2e/stack.ts`의 짓기에 위젯 관리 서버의 이미지를 더하고, 지어 쓰는 `.env`에 무작위 `WIDGET_ADMIN_DATABASE_PASSWORD` 줄을 더한다. `psql` 도우미가 서비스와 계정과 데이터베이스 이름을 받게 하고, 마지막 번호를 읽는 도우미(`web/packages/e2e-standalone/e2e/migrations.ts`)가 두 폴더를 읽게 한다
- [ ] 명세 Testing Decisions 둘째 이음매의 사례 여덟이 모두 있다. 넣은 위젯 설정의 200과 머리 셋, 등록되지 않은 이름과 퍼센트 인코딩된 `/`(`%2F`)가 든 이름과 끝에 퍼센트 인코딩된 줄바꿈(`%0A`)이 붙은 이름의 404 봉투와 머리 셋, `down` 뒤 `up -d --wait`로 다시 띄워도 남는 값, `widget-admin-migrate`의 `Exited (0)`과 위젯 쪽 `alembic_version`, uid 10001과 묶음 판, 지금의 셋 그대로인 호스트 포트, 방문자용 포트에서 프록시가 끊는 네 경로, `AGENT_OS_CONTAINER_NETWORK` 없는 `--host 0.0.0.0`의 루프백 진단이다
- [ ] 단독 배포 e2e를 로컬에서 돌린다. dev로 가는 PR의 CI는 이 e2e를 돌리지 않는다(명세 "티켓을 나눌 때 함께 둘 것"). 이미지마다 짓는 시간과 e2e 전체 시간을 재서 일지에 적고 제한과 견준다. 짓기는 다섯이 나란히 돌고 하나마다 `BUILD_MS`(15분, `web/packages/e2e-standalone/e2e/stack.ts`)를 받으므로 가장 오래 걸린 하나를 그 값과 견준다. e2e 전체는 CI `e2e-standalone` 잡의 제한(20분)과, 위젯 관리 서버 이미지를 짓는 몫은 판 내기 `build` 잡의 제한(30분)과 견준다. 이 PC에서 잰 시간은 CI 리눅스의 시간이 아니므로 견준 결과는 어림으로 적는다. 20분은 `.github/workflows/ci.yml`의 그 잡 머리 주석이 CI 실행 넷의 최대와 캐시가 빈 짓기의 어림에 여유 배수를 두어 정한 값이다. 다섯째 이미지로 그 여유가 주석이 적은 배수보다 줄어 보이면 사람에게 알리고 제한을 올릴지 묻는다. 제한을 올리는 것은 멈춘 일을 늦게 끊게 하는 쪽이라 이 티켓이 혼자 정하지 않는다. 이 시간을 재는 일은 명세의 어림과 일지 `docs/journal/2026-11-24-1637-widget-admin-server-spec.md`의 "다음"이 넘긴 "처음 보는 것" 가운데 하나다

### 마지막 티켓이면

- [ ] 이 티켓과 02 가운데 늦게 병합하는 쪽이 이 기능의 마지막 티켓이다. 이 티켓이 늦으면 병합 직전에 `git fetch origin` 뒤 기준 브랜치를 합치고 저장소 상태 시험(`test_이_저장소의_…`)을 돌린 뒤, 이 티켓을 닫는 커밋이 기능 계획 `.scratch/widget-admin-server/plan.md`에 `**끝:**` 줄을 적고 기능 단락 `docs/release-notes/features/widget-admin-server.md`를 싣는다(`docs/agents/issue-tracker.md`의 "끝 줄을 적는 때"와 "나란히 돈 마지막 티켓 둘")

### 검증

- [ ] `CLAUDE.md`의 검증 명령이 모두 초록이다
- [ ] 이 티켓은 LLM 시험의 범위(`docs/constitution/operations.md` LLM 테스트)에 드는 경로를 고치지 않는다. 고치게 되면 그 조건을 따른다
