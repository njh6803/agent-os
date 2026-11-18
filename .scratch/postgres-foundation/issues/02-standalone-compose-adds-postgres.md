# 02: 단독 compose를 띄우면 PostgreSQL과 한 번 도는 migrate가 함께 뜬다

**What to build:** 운영자가 `.env`에 `openssl rand -hex 32`로 만든 비밀번호 한 줄(`AGENT_OS_DATABASE_PASSWORD`)을 더하고 `docker compose up -d --wait`를 치면, PostgreSQL 컨테이너가 정상이 된 뒤 `migrate`가 표를 `0001`까지 올리고 `Exited (0)`으로 끝나며, 그 뒤 `serve`가 떠서 명령이 0으로 돌아온다(사용자 이야기 1, 2, 4, 5). 줄이 없거나 비면 compose가 컨테이너를 하나도 만들지 않고 까닭을 찍는다. PostgreSQL은 밖으로 포트를 열지 않고 좁힌 권한으로 돈다(사용자 이야기 14, 15). `docker compose down`과 다시 띄우기 뒤에도 데이터가 남는다(사용자 이야기 13, 기능 계획의 첫째 수락 조건 가운데 "넣어 둔 줄이 남는다"). `serve`는 이 변경에서 연결 문자열을 받지만 아직 쓰지 않는다. 쓰는 것은 03이다.

배포 안내(`deploy/standalone/README.md`)는 비밀번호를 만드는 명령, 띄운 뒤 보이는 상태, 띄우기가 끊겼을 때, 비밀번호 바꾸기, PostgreSQL 이미지까지 인터넷이 막힌 서버로 옮기는 명령을 적는다(사용자 이야기 3, 12, 16, 20, 39). 운영자가 `compose.yaml`을 바꾸고 비밀번호 줄을 더해야 하므로 PR 제목에 느낌표를 붙이고 올릴 때 할 일의 원고를 싣는다(사용자 이야기 17, 18).

근거는 명세 `.scratch/postgres-foundation/spec.md`의 "연결 문자열과 비밀번호의 변수"(compose가 짓는 주소), "비밀번호에 드는 글자", "단독 compose의 PostgreSQL과 migrate", "데이터베이스 비밀번호 바꾸기", "배포 안내", "실제 serve를 띄우는 시험의 데이터베이스"의 단독 배포 e2e 항목, "노트 검사의 짝"의 원고 항목, "저장소 상태 시험"의 첫째와 셋째, "마이그레이션 파일", Testing Decisions의 넷째, "티켓을 나눌 때 함께 둘 것"의 둘째다. 결정은 ADR 0066이다. 측정은 `.scratch/postgres-foundation/probes/`의 `compose_shape/`, `restart_recover/`다. 이 티켓의 "명세 검토"와 그 번호는 일지 `docs/journal/2026-11-19-0050-postgres-foundation-tickets.md`의 "명세 검토" 절을 가리킨다.

**Blocked by:** 01

**Status:** ready-for-agent

### compose 파일

- [ ] `deploy/standalone/compose.yaml`에 `postgres` 서비스를 더한다. 이미지는 `postgres@sha256:b9f6b8ff03b62f3cfd9d9ba3fe56226a9991c79d3fb46fd46536263bf02be553`이고 그 줄 위에 `postgres:18`(Debian trixie) 주석을 단다. 환경, 이름 있는 볼륨 `database`를 `/var/lib/postgresql`에, `ports` 없음, `unless-stopped`가 명세 "단독 compose의 PostgreSQL과 migrate"대로다
- [ ] `postgres`의 권한이 `user: "999:999"`, `read_only: true`, `cap_drop: [ALL]`, `security_opt: ["no-new-privileges:true"]`, tmpfs(디스크가 아니라 메모리에 두는 폴더) `/var/run/postgresql`, `init: true`다. 상태 확인은 TCP로 묻는 `pg_isready`이고 시간 설정은 지금 파일의 공용 앵커다
- [ ] `migrate` 서비스는 `serve`와 같은 이미지로 `agent-os migrate`를 돌리고, 재시작 정책 `"no"`, `postgres`의 `service_healthy`, 환경은 `AGENT_OS_DATABASE_URL` 하나, 읽기 전용 루트, 볼륨 없음이다. `.env`를 통째로 받지 않는다
- [ ] `serve`에 `migrate`의 `service_completed_successfully`와 `AGENT_OS_DATABASE_URL`을 더한다. 프록시와 다른 서비스에는 `depends_on`을 두지 않는다
- [ ] `POSTGRES_PASSWORD`가 `${AGENT_OS_DATABASE_PASSWORD:?.env 에 AGENT_OS_DATABASE_PASSWORD 가 없다}`이고, 줄이 없거나 빈 `.env`에서 `docker compose config`와 `up -d`가 그 글로 1이며 컨테이너가 하나도 생기지 않는 것을 이 PC에서 한 번 보고 일지에 적는다
- [ ] 파일 머리의 주석과 `user` 줄의 주석을 명세 같은 절의 끝에서 둘째 항목대로 고친다
- [ ] `.env.example`에 값이 빈 줄 `AGENT_OS_DATABASE_PASSWORD=`를 둔다

### 첫 마이그레이션

- [ ] 제품 마이그레이션 폴더에 `0001`을 더한다. 표를 만들지 않고 `upgrade`만 두며 `downgrade`가 없다(명세 "마이그레이션 파일", ADR 0066 결정 "이 행이 짓는 표")
- [ ] 01의 제품 폴더 사례(판 기록 표가 제품 폴더의 마지막 번호와 같다)가 고치지 않고 `0001`로 초록이다

### 배포 안내

- [ ] 명세 "배포 안내"의 항목을 모두 반영한다. 3-1(비밀번호 칸, 만드는 명령, 영문자와 숫자만 쓰는 까닭, "세 번", 통째로 받는 컨테이너 문장, 새 12절 가리키기), 4(받는 이미지, 서비스 표 두 행, 컨테이너 다섯과 프록시, `ps -a`의 `Exited (0)`), 4의 새 하위 절 "띄우기가 끊겼을 때", 5절 머리의 둘, 7, 8, 9, 11, 새 12절이다
- [ ] 4의 "`up`이 `service "migrate" didn't complete successfully: exit 1`로 끝나면" 문장은 마지막 줄이 아니라 `docker compose logs migrate`가 찍은 멈춤 글을 보라고 적는다(명세 검토 S11)
- [ ] 11의 인용은 원문 "`.env`의 `AGENT_OS_VERSION` 한 줄만 새 판 번호로 바꾼 뒤"를 그대로 둔다(명세 검토 N6)
- [ ] 9절의 고친 명령(인터넷이 되는 PC의 `AGENT_OS_DATABASE_PASSWORD=unused` 두 명령, `postgres@` 태그 붙이기, `save.txt`, 덮어쓰기 파일의 `image: agent-os-postgres:local`)을 실제로 돌려 보고, 명세의 글자가 아니라 돌려 본 꼴로 싣는다. 돌려 본 명령과 결과를 일지와 PR에 남긴다(ADR 0066 Consequences "운영", ADR 0056 결정 "인터넷이 막힌 곳")
- [ ] "띄우기가 끊겼을 때"의 세 줄(`down`, `docker volume rm agent-os_database`, `up -d --wait`)을 갓 띄운 배치에서 돌려 볼륨 이름이 맞고 새 볼륨으로 처음 띄우기가 다시 도는 것을 일지에 적는다(명세 같은 절)

### 단독 배포 e2e

- [ ] `web/packages/e2e-standalone`이 지어 쓰는 `.env`에 무작위 비밀번호 줄을 더한다. 판 내기의 시험(`.github/workflows/release.yml`)도 같은 패키지를 돌리므로 그 줄을 함께 받는다(명세 "실제 serve를 띄우는 시험의 데이터베이스")
- [ ] 사례 하나를 더한다. 띄운 뒤 판 기록 표의 줄이 저장소의 제품 마이그레이션 폴더의 마지막 번호와 같다. 번호는 그 폴더에서 읽고 `0001`을 글자로 적지 않는다(명세 검토 S4, S8). 이것이 휠과 이미지에 그 폴더가 들었는지를 본다(`__init__.py` 없는 판 폴더가 휠에 드는지도 여기서 선다)
- [ ] 같은 사례가 PostgreSQL 컨테이너 안의 `psql`로 시험 전용 표에 무작위 값 한 줄을 넣고, `docker compose down`(볼륨은 남긴다)과 `up -d --wait` 뒤에 `serve`가 정상이고 그 값이 그대로 읽히는 것을 본다(명세 Testing Decisions의 넷째)
- [ ] 실제 `agent-os migrate`가 읽기 전용 루트에서 도는 것을 이 시험의 첫 실행이 본다(명세 "단독 compose의 PostgreSQL과 migrate"의 `migrate` 서비스)
- [ ] 이 PC의 Docker로 `pnpm -C web/packages/e2e-standalone exec playwright test`를 돌린 결과를 일지에 적는다. 리눅스 러너의 이 잡은 main으로 가는 PR에서만 돌아, 다음 출시 PR이 처음 본다(명세 "티켓을 나눌 때 함께 둘 것", 명세 검토 S9)

### 저장소 상태 시험

- [ ] 01의 digest 시험에 셋째 자리 `deploy/standalone/compose.yaml`을 더한다(명세 "저장소 상태 시험"의 첫째)
- [ ] 배포 안내 7절의 전제(`postgres`에 `ports`가 없고 `user`가 `"999:999"`)와 권한 넷(`read_only: true`, `cap_drop: [ALL]`, `no-new-privileges:true`, `init: true`)이 compose 파일과 맞는지 보는 시험을 둔다(명세 "저장소 상태 시험"의 셋째, 명세 검토 S16). 선례는 `tests/tools/test_deploy_guide.py`의 `test_compose가_우리_이미지에_user를_더하지_않는다는_안내의_전제가_맞다`와 `compose의_user`다. 하나씩 빼는 변이 시험을 둔다

### 노트

- [ ] PR 제목에 느낌표를 붙이고 `docs/release-notes/upgrade/`에 원고를 싣는다. 원고는 새 묶음의 `compose.yaml`로 통째로 바꾸라는 것, `.env`에 비밀번호 줄을 더하라는 것(만드는 명령과 함께), "올리기 전에 데이터베이스를 백업하십시오. 되돌리려면 그 백업을 복원합니다"를 싣는다(명세 "노트 검사의 짝", "배포 안내"의 11, ADR 0066 결정 "승인 때 함께 확인받는 세부"의 첫째). 노트 검사의 짝은 04가 더하므로 이 PR의 느낌표는 기계가 아니라 이 수용 기준이 지킨다

### 검증

- [ ] CLAUDE.md의 검증 명령이 모두 초록이다
- [ ] 제품 마이그레이션 폴더가 `src/agent_os/adapters/` 안이므로 `-m llm`과 로컬 모델 시험(`tools/llm_local.py run`. `--yes` 없이 쳐 예상 비용을 사용자에게 보여 확인받은 뒤에만 `--yes`)의 병합 조건에 든다(`docs/constitution/operations.md` LLM 테스트)
