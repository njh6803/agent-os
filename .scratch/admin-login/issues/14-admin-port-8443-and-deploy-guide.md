# 14: 관리 화면용 포트 8443과 배포 안내(느낌표)

**What to build:** 단독 배포를 올린 운영자가 브라우저로 `https://<서버 이름>:8443/`을 열면 관리 화면의 로그인 화면이 선다. 첫 계정을 `docker compose exec serve agent-os operator system-admin <계정 이름>`으로 만들고 로그인하면 플러그인 목록이 서고, 같은 로그인으로 운영자 채널에 요청을 보내 답의 스트림을 받는다. 방문자용 443에서는 관리 경로가 지금처럼 404다. `.env`에 `AGENT_OS_ADMIN_ADDRESS=127.0.0.1`을 넣으면 8443은 서버 자신에서만 열리고, 운영자는 SSH 포트 포워딩으로 닿는다. 로그인 기록에는 nginx가 본 접속 주소가 남는다. 배포 안내는 8443의 첫 계정과 방화벽 권고, 닫는 법, 유지 시간의 세 변수, 기록 주소의 한계를 적는다.

PR 제목에 느낌표(`feat!:`처럼 붙이는 `!`. 판을 올리는 사람이 손으로 할 일이 있다는 표지)를 붙인다. 판을 올리면 8443이 새로 열리므로 운영자가 방화벽을 먼저 봐야 하기 때문이다.

대화 목록과 대화 화면은 10과 11이 짓고 관리 화면 e2e가 덮는다. 이 티켓은 그 둘을 기다리지 않으므로, 단독 배포 e2e도 명세 Testing Decisions의 "단독 배포 e2e"대로 로그인과 플러그인 목록과 모델 없는 에이전트의 스트림 하나까지만 본다.

근거는 명세 `.scratch/admin-login/spec.md`의 "관리 화면용 포트", "배포 안내", "로그인 기록"의 "접속한 주소"와 "한계 둘", "유지 시간", "portal-admin이 기대는 것"의 포트 행, Testing Decisions의 "단독 배포 e2e", "수락 조건을 덮는 자리"의 첫 행이다. 측정은 `.scratch/admin-login/probes/admin_port_chain/`(결과 1·2·6)이고 다시 돌리지 않는다. 결정은 ADR 0062 결정 "포트와 TLS", ADR 0056과 그 이력 2026-11-14(443과 80은 IPv4에만 발행한다)다. 이 티켓의 "명세 검토"는 일지 `docs/journal/2026-11-25-1007-admin-login-tickets.md`의 "명세 검토(spec-reviewer)" 절을 가리킨다.

**Blocked by:** 13

**Status:** ready-for-agent

### nginx와 compose

- [ ] nginx에 관리 화면용 리스너(한 포트를 듣는 설정 한 덩이, 컨테이너 안 `listen 9443 ssl`)를 더한다. 인증서와 키, TLS 판, HSTS 머리(브라우저에게 이 이름은 https로만 열라고 알리는 응답 머리), 본문 상한 1MB, `proxy_http_version 1.1`, `Host $host`, `X-Forwarded-Proto $scheme`, `resolver`와 `upstream`은 방문자용 리스너와 같다. `location /` 하나로 관리 화면 컨테이너의 3000에 넘기고 허용 목록을 두지 않는다
- [ ] `X-Forwarded-For`와 `X-Real-IP`(둘 다 앞에 선 nginx가 본 접속 주소를 뒤에 넘기는 머리)를 `$remote_addr` 하나로 덮어쓴다. 받은 값에 덧붙이지 않는다
- [ ] 버퍼링을 끄는 지시문을 따로 두지 않는다(명세 "관리 화면용 포트"의 "흐르는 응답")
- [ ] compose가 `"${AGENT_OS_ADMIN_ADDRESS:-0.0.0.0}:${AGENT_OS_ADMIN_PORT:-8443}:9443"`으로 발행한다(컨테이너의 포트를 호스트의 주소와 포트에 여는 것). 기본 주소 `0.0.0.0`은 443과 80처럼 서버의 IPv4 주소에만 연다(ADR 0056 이력 2026-11-14). 관리 화면 컨테이너의 3000은 지금처럼 호스트의 `127.0.0.1`에만 발행한다. `serve`의 uvicorn 쉬는 연결 시간은 바꾸지 않는다
- [ ] widget-admin-server 티켓 04(`.scratch/widget-admin-server/issues/04-standalone-compose-adds-widget-admin.md`)도 `deploy/standalone/compose.yaml`의 머리 주석과 `ports` 항목, 방문자용 리스너를 고친다. 시작할 때 기준 브랜치를 합쳐 그 티켓이 먼저 병합됐는지 보고, 병합됐으면 그 판 위에서 아래 주석을 고친다
- [ ] 방문자용 리스너의 머리 주석과 compose 파일의 머리 주석을 넷으로 고치고, 호스트의 8443이 컨테이너 안의 9443으로 가며 컨테이너 안의 8443은 방문자용이라는 것을 적는다
- [ ] `deploy/standalone/.env.example`에 새 변수(`AGENT_OS_ADMIN_ADDRESS`, `AGENT_OS_ADMIN_PORT`, 유지 시간의 세 변수)를 주석으로 기본값과 함께 넣는다

### 배포 안내

- [ ] `deploy/standalone/README.md`의 첫 계정과 로그인 안내를 `https://<이름>:8443/`으로 바꾼다(13이 둔 `127.0.0.1:3000`의 안내)
- [ ] 8443이 기본으로 인터넷에 열린다는 것과 방화벽으로 운영자가 쓰는 주소로 좁히기를 권하는 것, `AGENT_OS_ADMIN_ADDRESS=127.0.0.1`과 `ssh -L 8443:127.0.0.1:8443 <서버>`로 닫는 법을 적는다
- [ ] 유지 시간의 세 변수의 뜻과 범위와 어기면 `serve`가 뜨지 않는다는 것을 적는다
- [ ] 로그인 기록의 주소의 한계 둘(서버의 `127.0.0.1:3000`으로 들어온 요청은 주소를 지어낼 수 있다, Docker Desktop에서는 모든 주소가 도커의 관문 주소로 보인다)을 적는다
- [ ] 7절 "고치지 말 것"의 `ports` 경고를 443과 80과 3000에만 남기고, 관리 화면용 포트는 두 설정으로 바꾸거나 닫는다고 적는다
- [ ] `tests/tools/test_deploy_guide.py`의 필수 낱말을 맞춘다
- [ ] 이 PR의 `docs/release-notes/upgrade/` 조각에 "올리면 관리 화면용 포트 8443이 새로 열립니다. 올리기 전에 방화벽을 보십시오"와, 올린 뒤 첫 계정을 만들고 8443에서 로그인하는 안내를 싣는다. 이 기능이 새로 들인 환경 변수 다섯(`AGENT_OS_ADMIN_ADDRESS`, `AGENT_OS_ADMIN_PORT`, 유지 시간의 셋)과 기본값도 싣는다(명세 "배포 안내"의 "올리는 사람에게 요구하는 셋", 이야기 76)

### 시험

- [ ] 단독 배포 e2e(선례 `web/packages/e2e-standalone/e2e/deployment.e2e.ts`): `docker compose exec -T serve agent-os operator system-admin <이름>`에 파이프로 비밀번호를 넣어 계정을 만들고, `https://127.0.0.1:8443`으로 로그인해 플러그인 목록을 읽고, 모델 없는 에이전트로 대화 하나의 스트림을 받는다. 방문자용 443이 관리 경로를 404로 막고, 발행된 호스트 포트가 넷(80, 443, 3000, 8443)이며 3000만 루프백인 것을 본다
- [ ] 단독 배포 e2e가 호스트의 8443도 쓰게 되므로 `CLAUDE.md` 검증 명령의 단독 배포 e2e 괄호("호스트의 80·443·3000 포트가 비어 있어야 한다")에 8443을 더한다. 지침 파일을 고치기 전에 Skill 도구로 `writing-for-agents`를 부른다
- [ ] e2e가 관리 화면 중계의 500(uvicorn이 쉬는 연결을 닫는 순간과 겹친 것)을 보면 명세 "관리 화면용 포트"의 "uvicorn이 쉬는 연결을 닫는 시간"을 다시 본다

### 기능을 닫는 일

- [ ] 11, 12, 14 가운데 마지막으로 병합하는 티켓이면, 병합하기 전에 `git fetch origin`으로 기준 브랜치를 합치고 기능 계획(`.scratch/admin-login/plan.md`)에 `**끝:** YYYY-MM-DD`를 적고 `uv run python tools/plan_table.py`를 돌린 뒤 기능 단락 `docs/release-notes/features/admin-login.md`를 같은 커밋에 싣는다(`docs/agents/issue-tracker.md`의 "끝 줄을 적는 때"). 저장소 상태 시험을 돌려 본다

### 검증

- [ ] `CLAUDE.md`의 검증 명령이 모두 초록이다
- [ ] `deploy/`의 배포 파일 묶음을 고치므로 단독 배포 e2e(`pnpm -C web/packages/e2e-standalone exec playwright test`, Docker와 빈 80·443·3000·8443 포트)를 로컬에서 친다. 그 잡의 시험은 base가 main인 PR에서만 돌고 dev로 가는 PR에서는 곧바로 성공으로 끝난다(`.github/workflows/ci.yml`의 머리 주석)
