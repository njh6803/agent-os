# compose_shape: 단독 compose 에 PostgreSQL 과 한 번 도는 migrate 를 더한 모양

## 무엇을 왜 재는가

ADR 0066은 단독 compose에 PostgreSQL 컨테이너 하나와 한 번 돌고 끝나는 `migrate` 서비스를 더하기로 하고, 그 모양의 세부를 명세에 넘겼다. 이 프로브는 그 가운데 Docker와 compose가 정하는 것을 실제 컨테이너로 잰다. 결정은 하지 않고 본 것만 적는다. 규약은 `docs/agents/issue-tracker.md`의 "프로브와 근거"다.

ADR이 넘긴 문장은 이렇다.

- 결정 "compose 배치": "그래서 그 컨테이너의 권한을 좁히는 설정(읽기 전용 루트, 권한 빼기, `user`)과 PostgreSQL의 상태 확인은 명세가 리눅스에서 잰다." 공식 이미지는 root로 떠서 진입 스크립트가 데이터 폴더의 소유를 맞춘 뒤 `gosu`로 uid 999가 된다고 같은 결정이 적었다. → 1, 2
- 결정 "표를 올리는 때": "`serve`는 그 서비스가 성공으로 끝난 뒤에 뜬다. 운영자는 판 번호를 바꾸고 `docker compose up -d`만 친다." 그리고 Consequences "명세가 짓는 것"의 "`migrate` 서비스와 PostgreSQL의 상태 확인과 `depends_on` 조건", "`migrate` 서비스의 재시작 정책". → 3
- Consequences "명세가 짓는 것": "이미 데이터가 있는 볼륨에서 비밀번호를 바꾸는 길과 그 절차를 배포 안내에 적는 것." 같은 문단은 `.env`만 고치면 접속이 실패한다고 코드를 읽어 적고 "비밀번호를 바꾼 볼륨으로 실제로 띄워 보지는 않았다"고 했다. → 4
- 결정 "비밀번호와 계정"과 Consequences "재지 않은 것": "compose의 변수 치환에 연결 문자열에서 비밀번호를 떼어 낼 다른 문법이 없는지(명세. `#`와 `%` 치환이 거부되는 것만 손으로 봤다)", "`@`, `:`, `/`가 든 비밀번호로 지은 주소를 SQLAlchemy가 어떻게 읽는지(명세)". 이 프로브는 compose가 무엇을 하는지와 libpq(`psql`)가 그 주소를 받는지까지만 본다. SQLAlchemy는 보지 않는다. → 5

## 판정 기준을 바꾼 것

결과를 본 뒤 고친 것이 여섯이고, 아래 결과는 모두 고친 판으로 다시 돌린 실행의 것이다(어느 실행인지는 "다시 돌리기").

- 2나(데이터가 있는 볼륨으로 다시 띄운 대조): 첫 판은 다섯 회차 가운데 넷이 측정이 아니었다. 다시 띄우면 0.3초 안에 준비되기도 해서, `docker exec`로 띄운 안쪽 표본의 첫 줄이 이미 준비된 서버를 봤다(표지 "안쪽 표본의 첫 줄이 아직 답하지 않는다"가 서지 않았다). 그래서 2가와 2나는 진입 스크립트 앞에 5초를 기다리게 했다(`HOLD_SECONDS`). 시각은 컨테이너 시작에서 잰 그대로라 2가·2나의 값에는 그 5초가 든다. 2다는 늦추지 않는다.
- 2다(상태 확인 꼴의 견줌): 첫 판은 `health_status: healthy` 이벤트와 다른 컨테이너의 첫 성공 시각을 견줬다. 한 회차가 0.03초 차이로 "healthy가 먼저"로 갈렸는데, 표본 간격(0.2~0.3초) 안의 차이였다. 그래서 판정을 "healthy 뒤에 시작한 다른 컨테이너의 접속 가운데 실패한 것의 수"로 바꾸고, 그 뒤에 표본이 남게 바깥 표본이 성공 다섯 번 대신 열다섯 번 이어지면 멈추게 했다. healthy 뒤에 바깥 표본이 하나도 없는 회차는 측정이 아니다.
- 1(권한)의 멈춤: 처음에는 "received fast shutdown request" 줄이 로그 어디에 있는지만 봤다. 처음 띄우는 회차에서는 초기화용 임시 서버를 멈출 때도 그 줄이 찍혀, 1다 + init에서 멈춤이 실패했는데도 맞다고 읽었다(원본 출력에서 tini의 실패 줄을 보고 알았다). 그래서 마지막 준비 줄 뒤에 `database system is shut down`이 찍혔는지로 바꾸고, 그 까닭을 가르는 갈래(1다 + init + KILL)를 더했다.
- 3사(`docker compose restart`): 고치기 전 판은 serve가 돌아오자마자 migrate의 종료 코드를 읽었다. 한 실행에서 migrate가 아직 도는 동안 읽어 "종료 0(줄 2→2)"으로 적혔는데, 같은 실행의 `docker inspect`를 보면 migrate는 그 뒤에 끝났다(원본 출력에서 끝난 시각과 읽은 시각을 대 봤다). 그래서 migrate가 끝난 것(`exited`)을 기다린 뒤 읽고, 끝나지 않으면 측정이 아니게 했다. 결과 문구의 "migrate도 다시 시작했다"도 시작 시각이 바뀐 것을 보고서야 적게 했다.
- PR 606의 봇(CodeRabbit) 첫 회차가 짚은 일곱(지적 #19~#21, #23~#26): 3사는 다시 띄우기 전의 줄 조회가 실패해 빈 목록이어도 "넣어 둔 줄이 남았다"가 참이 됐다. 앞뒤 조회가 모두 줄을 냈을 때만 측정으로 센다(#20). 3다의 두 꼴은 앞 꼴이 남긴 실패 컨테이너를 뒤 꼴이 읽어도 측정이 됐다. 그 명령의 출력에 migrate 실패 문구가 있을 때만 측정으로 센다(#21). 3다의 고친 뒤 회차는 `up`이 제한 시간으로 끊겼거나 대역의 종료 값이 0으로 바뀌지 않았어도 측정이 됐다. 둘을 함께 본다(#19). 5라는 대역이 돌지 않아도 측정이 됐다. 대역의 성공 줄이나 이번 실행의 `psql: error:`가 있을 때만 센다(#23). 4마의 틈은 모든 종류의 줄 가운데 마지막 시각에서 재 바꾸기 직전의 새 접속 줄을 빼먹을 수 있었다. 절차 전의 마지막 `serve-new`·`serve-start` 줄부터 잰다(#24). 4마의 절차는 셸에 남은 옛 값이 `.env`를 덮는 갈래를 재지 않았고(러너가 그 변수를 지운 환경으로 쳤다), 앞 줄이 실패해도 다음 줄을 쳤다. 절차의 첫 줄에 `unset`을 두고 뒤의 세 줄을 `&&`로 이었으며, 4마는 옛 값을 내보낸 부모 셸에서 줄마다 그 첫 줄을 앞에 붙여 치고 0이 아닌 줄에서 멈춘다(#25·#26). 같은 회차의 Critical 하나가 서버가 거절한 `ALTER ROLE`이 평문째 로그에 남는다고 짚어, 셋째 줄을 `\password`로 바꾸고 그 실패 갈래 4바를 더했다. 고친 뒤 `--sections 3,4,5`로 다시 돌렸다.
- PR 606의 봇 둘째 회차가 짚은 하나: 운영자의 셸에 `COMPOSE_ENV_FILES`가 다른 파일을 가리키면 compose가 `.env`를 읽지 않아, `.env`를 고쳐도 세 줄이 모두 0으로 끝나며 비밀번호는 바뀌지 않는다. 4마는 러너가 `COMPOSE_` 변수를 지운 환경으로 쳐서 그 갈래를 재지 않았다. 빈 폴더의 compose 파일 하나로 `docker compose config`를 쳐, 그 변수가 `other.env`를 가리키면 `.env`의 값 대신 `other.env`의 값이 들고, `unset`하면 `.env`로 돌아오는 것을 봤다(Docker Compose 5.6.1, 손으로 봤다. 세션 스크래치패드의 스크립트, 커밋하지 않았다). 절차의 첫 줄을 `unset AGENT_OS_DATABASE_PASSWORD COMPOSE_ENV_FILES`로 바꾸고, 4마는 옛 값을 든 `stale.env`를 가리키는 `COMPOSE_ENV_FILES`까지 내보낸 부모 셸에서 치게 했다. 4마의 표지(첫 줄이 이 글자이고 세 줄을 다 쳤으며 데이터베이스가 새 비밀번호만 받는다)는 고치기 전 첫 줄이었다면 compose가 `stale.env`의 옛 값으로 PostgreSQL을 다시 만들어 서지 않는다(위의 손으로 본 것으로 가늠했다). 고친 뒤 `--sections 4`로 다시 돌렸다. 첫 시도는 표지가 비교하는 첫 줄의 상수를 고치지 않아 4마가 측정 아님으로 세어졌고 종료 1이었다(`run-20261118-223609-138176`). 상수를 고친 둘째 시도가 아래 "다시 돌리기"의 실행이다.

## 결과

근거의 종류는 넷이다. "프로브가 다시 낸다"는 `run.py`의 마지막 실행(아래 "다시 돌리기")이 표지를 단언한 회차에서 낸 값이고, 그 값에만 "쟀다"를 쓴다. "손으로 봤다"는 저장한 원본 출력이나 이미지 안의 파일을 명령으로 따로 본 것, "원문을 받아 읽었다"는 위 "받아 읽은 원문"의 것, "어림"은 보지 않고 짐작한 것이다. 1의 회차는 처음 띄우기(빈 볼륨)와 다시 띄우기(컨테이너를 지우고 데이터가 있는 볼륨으로 새로 만들기)를 한 쌍으로 돈다. 뜨는 조합의 다시 띄우기는 앞 회차가 만든 볼륨을, 실패를 기대하는 조합의 다시 띄우기는 따로 만든 볼륨(1나 tmpfs 없음은 1나로, 1다의 권한 빼기는 1다의 넷으로, 1라는 1가로 만든 것)을 쓴다.

### 1. PostgreSQL 컨테이너의 권한

| 항목 | 결과 | 근거의 종류 |
|---|---|---|
| 1가 기준(아무것도 좁히지 않음) | 처음·다시 모두 떴다. PID 1은 `postgres`(uid 999, 진입 스크립트가 root로 떠서 `gosu`로 바꾼 뒤), 가진 권한(CapEff) 0, 경계(CapBnd) `a80425fb`(Docker 기본 묶음), 루트 파일시스템에 쓰기가 된다. 볼륨 안은 `/var/lib/postgresql` 999:999 755, `18` 0:0 755, `18/docker`(PGDATA) 999:0 700 | 프로브가 다시 낸다 |
| 1나 `user: "999:999"` + `read_only: true` + `cap_drop: [ALL]` + `no-new-privileges:true` + tmpfs `/var/run/postgresql` | 처음·다시 모두 떴다. PID 1 `postgres` uid 999, CapEff·CapBnd 모두 0, NoNewPrivs 1. 루트에 쓰면 `Read-only file system`으로 거부된다(대조: 1가에서는 같은 쓰기가 된다). 빈 이름 있는 볼륨이 이미지의 소유(999:999)를 받아, 볼륨 안이 `18`·`18/docker`까지 999:999다 | 프로브가 다시 낸다 |
| 1나에서 tmpfs를 뺌 | 처음·다시 모두 종료 1, `could not create lock file "/var/run/postgresql/.s.PGSQL.5432.lock": Read-only file system`. 1나는 이 tmpfs 하나로 떴으므로 다른 쓰기 자리(`/tmp` 등)는 필요 없었다 | 프로브가 다시 낸다 |
| 1나의 tmpfs를 `uid=999,gid=999,mode=0700`으로 | 떴다. 소켓 폴더는 0700이 아니라 999:999 3775였다. 진입 스크립트 45줄의 `chmod 03775 /var/run/postgresql \|\| :`이 폴더의 주인일 때 모드를 바꾼다. 옵션 없는 tmpfs(0:0 3777)에서는 그 chmod가 실패하고 넘어간다 | 값은 프로브가 다시 낸다. 까닭인 45줄은 손으로 봤다(`docker run --rm --network none --entrypoint grep <이미지> -n -e run/postgresql -e chmod -e "find " //usr/local/bin/docker-entrypoint.sh`) |
| 1가(root)로 만든 볼륨을 1나로 다시 띄움 | 떴다. `18`은 0:0, `18/docker`는 999:0 700 그대로이고 999가 PGDATA의 주인이라 된다 | 프로브가 다시 낸다 |
| 1다 root로 떠서 `gosu` + `cap_drop: [ALL]` + `cap_add: [CHOWN, DAC_OVERRIDE, SETGID, SETUID]` + 읽기 전용 + `no-new-privileges` + tmpfs | 처음·다시 모두 떴다. PID 1 `postgres` uid 999, CapEff 0, CapBnd `c3`(넷) | 프로브가 다시 낸다 |
| 1다에서 넷을 하나씩 뺌 | CHOWN: 처음 `chown: changing ownership of '/var/lib/postgresql/18/docker': Operation not permitted`, 다시 `chown: changing ownership of '/var/run/postgresql': Operation not permitted`. DAC_OVERRIDE: 처음 `mkdir: cannot create directory ‘/var/lib/postgresql/18’: Permission denied`, 다시 `find: ‘/var/lib/postgresql/18/docker’: Permission denied`. SETGID와 SETUID: 처음·다시 모두 `error: failed switching to 'postgres': operation not permitted`. 모두 종료 1 | 프로브가 다시 낸다 |
| 1다의 DAC_OVERRIDE를 DAC_READ_SEARCH로 | 처음은 `mkdir … Permission denied`로 끝나고, 데이터가 있는 볼륨에서는 떴다 | 프로브가 다시 낸다 |
| 넷이라는 묶음을 찾은 길 | Docker 기본 묶음에서 하나씩 빼 보며 찾았다. 넷만으로 뜨는 것(그래서 FOWNER, FSETID, KILL 등 나머지가 필요 없는 것)과 넷 가운데 무엇을 빼도 실패하는 것은 위 두 줄이 다시 낸다 | 찾은 길은 손으로 봤다(세션 스크래치패드의 탐색 스크립트) |
| 1라 `cap_drop: [ALL]`만(root로 뜨고 나머지는 기본) | 처음 `mkdir … Permission denied`, 다시 `find … Permission denied`, 모두 종료 1 | 프로브가 다시 낸다 |
| `init: true` | 1나 + init: PID 1이 `docker-init`(uid 999), 깨끗이 멈췄다. 1다 + init: PID 1이 `docker-init`(uid 0, CapEff `c3`)이고, 멈출 때 `[FATAL tini (1)] Unexpected error when forwarding signal: 'Operation not permitted'`를 찍고 종료 1로 끝났다(처음·다시 모두). 그 다음 시작은 `database system was not properly shut down; automatic recovery in progress`를 돌았다. 1다 + init에 KILL을 더하면(CapEff `e3`) 처음·다시 모두 깨끗이 멈추고 다음 시작에 복구가 없었다 | 프로브가 다시 낸다. "root인 tini가 uid 999의 PostgreSQL에 신호를 넘기려면 KILL이 있어야 한다"는 KILL 갈래가 가른 해석이다 |
| 멈춤 | 뜬 조합은 모두 `docker compose stop --timeout 10`에 마지막 준비 줄 뒤 `database system is shut down`을 찍고 종료 0으로 멈췄다(위 1다 + init만 아니다). 걸린 시간은 0.4~0.9초였다. 1다 + init의 다시 띄우기도 넣어 둔 줄은 남아 있었다 | 프로브가 다시 낸다 |
| 뜨는 데 걸린 시간 | `up -d`가 돌아온 뒤 안에서 친 `pg_isready -h 127.0.0.1`이 0을 낼 때까지 처음 1.4~2.0초, 다시 0.2~0.6초. 앞선 실행(다른 세션과 함께 돈 부하 아래)에서는 처음 2.2~5.2초, 다시 0.3~1.7초였다 | 마지막 실행의 값은 프로브가 다시 낸다. 앞선 실행의 값은 그 원본을 손으로 봤다 |

### 2. 상태 확인

세 확인을 견줬다. 컨테이너 안에서 유닉스 소켓으로 친 `pg_isready`, 컨테이너 안에서 `-h 127.0.0.1`(TCP)로 친 `pg_isready`, 같은 네트워크의 다른 컨테이너에서 TCP로 친 `psql -c "select 1"`이다. 셋째가 `migrate`와 `serve`가 실제로 겪는 것이다. 2가·2나는 진입 스크립트를 5초 늦춰 띄웠으므로 시각에 그 5초가 든다. 2다는 늦추지 않았다. 안쪽 표본 줄 사이의 간격은 회차마다의 가운데 값이 0.15~0.20초였다.

| 항목 | 결과 | 근거의 종류 |
|---|---|---|
| 2가 빈 볼륨으로 처음 띄우기(다섯 번) | 처음 0을 낸 때가 유닉스 소켓 6.05~6.80초, 127.0.0.1 6.52~7.12초, 다른 컨테이너 6.52~7.17초였다. 다섯 번 모두 유닉스 소켓이 먼저였고, 유닉스 소켓만 답한 표본이 1~2개(길이 0~0.19초) 있었다. 다섯 번 모두 유닉스 소켓이 처음 0을 낸 뒤 다시 실패한 표본이 있었다. 로그의 준비 줄(`database system is ready to accept connections`)은 둘이고 0.45~0.48초 떨어져 있다 | 프로브가 다시 낸다 |
| 2나 데이터가 있는 볼륨으로 다시 띄우기(대조, 다섯 번) | 안쪽의 두 확인이 같은 표본 줄에서 처음 0을 냈고(5.18~5.29초), 다른 컨테이너는 5.16~5.31초였다. 유닉스 소켓만 답한 표본도, 처음 0 뒤에 다시 실패한 표본도 없었다. 준비 줄은 하나다 | 프로브가 다시 낸다 |
| 유닉스 소켓만 답하는 틈의 까닭 | 처음 띄울 때 진입 스크립트는 초기화용 임시 서버를 TCP를 듣지 않게 띄운다(`docker-entrypoint.sh` 297줄 `-c listen_addresses=''`). 임시 서버가 있는 2가에만 틈과 다시 실패한 표본이 있고, 없는 2나에는 둘 다 없다 | 297줄은 손으로 봤다(1의 45줄과 같은 `grep`). 틈과 다시 실패한 표본의 있고 없음은 프로브가 다시 낸다 |
| 2다 compose의 상태 확인 꼴 넷(빈 볼륨, 꼴마다 세 번) | 아래 표 | 프로브가 다시 낸다 |

| 상태 확인(`interval` 30s 등 나머지는 앵커 그대로) | `healthy`가 된 때(시작에서) | 다른 컨테이너의 첫 성공에서 `healthy`를 뺀 값 | `healthy` 뒤에 시작한 다른 컨테이너의 접속 |
|---|---|---|---|
| 유닉스 소켓 `pg_isready -U agent_os -d agent_os`, `start_interval: 200ms` | 1.21~1.64초 | +0.30~+0.41초(`healthy`가 먼저) | 세 번 모두 17개 가운데 실패 2개 |
| TCP `pg_isready -h 127.0.0.1 -U agent_os -d agent_os`, `200ms` | 1.72~1.73초 | −0.12~−0.26초 | 13~14개 가운데 실패 0개 |
| TCP, `1s` | 2.27~3.47초 | −0.58~−0.99초 | 8~10개 가운데 실패 0개 |
| TCP, `2s`(지금 앵커) | 2.22~4.30초 | −0.52~−1.75초 | 3~11개 가운데 실패 0개 |

모든 회차에 `health_status: unhealthy` 이벤트는 없었다. 유닉스 소켓 꼴은 임시 서버가 답하는 틈에 `healthy`가 되고, 임시 서버가 멈췄다가 마지막 서버가 뜨는 1초 안팎은 다음 확인보다 먼저 끝나 `unhealthy`로 바뀌지 않는다고 읽는다(어림. Docker가 확인을 친 때도, 그 간격을 정하는 Docker 코드도 보지 않았다). 그렇다면 `service_healthy`만 기다린 `migrate`가 처음 설치에서 접속에 실패할 수 있다(어림). 이 프로브는 그 자리에 `migrate`를 띄워 보지 않고, `healthy` 뒤 다른 컨테이너의 접속이 실패한 것까지 봤다.

TCP 꼴에서 `healthy`는 다른 컨테이너가 이미 접속할 수 있게 된 뒤에 왔고, 늦는 정도는 `start_interval`을 넘지 않았다(200ms에서 0.12~0.26초, 1s에서 0.58~0.99초, 2s에서 0.52~1.75초). 상태 확인은 TCP(`-h 127.0.0.1`)로 하고 `start_interval`은 앵커의 2s를 그대로 두기를 제안한다. 늦어도 2초 안쪽이고, 그 늦음은 PostgreSQL 컨테이너가 시작할 때마다 한 번 난다(제안. 부하가 큰 엔진에서는 재지 않았다).

### 3. `depends_on`과 한 번 도는 `migrate`

같은 폴더의 `compose.yaml`을 그대로 띄웠다. 대역은 `probe_rows` 표에 누가 어느 판으로 언제 줄을 넣었는지 남긴다. migrate는 한 번 넣고 끝나고, serve는 시작할 때 한 번 넣은 뒤 쥐고 있는 접속 하나와 매번 새로 맺는 접속으로 0.5초마다 넣는다.

아래 표의 수치는 전체 실행 `run-20261118-163425-b6e060`의 것이다. 봇이 짚은 표지를 고친 뒤의 실행 `run-20261118-212254-d49023`은 모든 회차에서 같은 결과 문구를 냈고, 수치는 이렇게 달랐다. 3가의 `up -d`가 9.6초, `--wait`이 든 셋이 6.6~6.8초에 돌아왔다. 3나는 healthy 2.24초 → migrate 시작 2.70초 → 끝 2.93초 → serve 시작 3.41초였다. 3마의 serve 줄이 없던 동안은 1.73초였고, 3아의 쥐고 있던 접속의 줄은 27→27이었다. 같은 PC에서 다른 세션이 함께 돌아 걸린 시간은 실행마다 흔들린다(아래 "환경").

| 항목 | 결과 | 근거의 종류 |
|---|---|---|
| 3가 `up` 꼴 넷(빈 볼륨에서 처음) | 넷 모두 종료 0. `up -d`는 4.0초에 돌아왔고, 그때 migrate는 `Exited (0)`, serve는 떠 있으나 상태 확인이 `starting`이었다. `--wait`이 든 셋(`up -d --wait`, `up -d --wait --wait-timeout 600`, `up --detach --wait --wait-timeout 600`)은 6.5~8.6초에 돌아왔고 그때 serve가 `healthy`였다. 0으로 끝난 migrate를 `--wait`이 실패로 보지 않았다 | 프로브가 다시 낸다 |
| 3나 시작 차례 | postgres가 시작한 때에서 `healthy` 4.55초 → migrate 시작 4.74초 → migrate 끝 4.94초 → serve 시작 5.42초 | 프로브가 다시 낸다 |
| 3바 끝난 migrate를 보는 길 | `docker compose ps`에는 migrate가 없고, `ps -a`에 `Exited (0)`, `logs migrate`에 대역의 줄이 남는다 | 프로브가 다시 낸다 |
| 3라 모두 뜬 채 `up -d`를 다시 | migrate가 같은 컨테이너로 다시 돌아 migrate의 줄이 1→2가 됐고, `up -d --wait`으로 한 번 더 2→3이 됐다. serve는 그대로였다(`Running`). `up -d`를 칠 때마다 migrate가 돈다 | 프로브가 다시 낸다 |
| 3마 판 바꾸기(판을 나타내는 환경 변수 하나를 바꾸고 `up -d --wait`) | 옛 serve가 멈춘 뒤 0.8초에 새 migrate가 시작하고 1.09초에 끝났으며, 1.56초에 새 serve가 시작했다. 옛 serve의 마지막 줄에서 새 serve의 첫 줄까지 2.31초 동안 serve의 줄이 없었다. 옛 serve와 새 migrate는 겹치지 않았다 | 프로브가 다시 낸다 |
| 3사 `down`(볼륨은 남김) 뒤 `up -d --wait` | 넣어 둔 줄이 모두 남았고 migrate가 다시 돌았다(v2 줄 1→2) | 프로브가 다시 낸다 |
| 3사 `docker compose restart` | 세 서비스가 한꺼번에 다시 시작했고 `depends_on`을 기다리지 않았다(시작 이벤트가 migrate, postgres, serve 차례). migrate는 `psql: error: could not translate host name "postgres" to address: Name or service not known`으로 종료 2였다(줄은 늘지 않았다). serve 대역은 다시 시도하는 고리라 RestartCount 0인 채 새 접속이 돌아왔고, 넣어 둔 줄은 남았다 | 프로브가 다시 낸다. 고치기 전 판의 한 실행에서는 시작 차례가 migrate, serve, postgres였고, migrate가 `Connection refused`로 종료 2, serve 대역은 시작 이벤트가 둘이고 RestartCount 1이었다(한 번 끝났다가 재시작 정책으로 다시 떴다). 차례는 실행마다 다르다(원본 출력을 손으로 봤다) |
| 3아 `docker compose restart postgres` | serve 컨테이너는 그대로였다(id, 시작 시각, RestartCount가 같다). 새 접속의 줄은 다시 늘었다(23→30). 쥐고 있던 접속은 `FATAL:  terminating connection due to administrator command`로 끊긴 채 다시 맺지 않았다(줄 25→25. 대역이 다시 맺지 않게 지어졌다) | 프로브가 다시 낸다 |
| 3다 migrate가 1로 끝날 때(빈 볼륨에서 처음) | `up -d`와 `up -d --wait` 모두 종료 1, 마지막 줄 `service "migrate" didn't complete successfully: exit 1`. serve는 `created`(시작한 적 없음)였다. 고친 뒤 `up -d --wait`은 migrate를 새 컨테이너로 다시 만들어 0으로 끝내고 serve가 `healthy`가 됐다 | 프로브가 다시 낸다 |

### 4. 데이터가 있는 볼륨에서 비밀번호 바꾸기

모두 3의 모양을 띄워 줄을 넣어 둔 뒤 바꿨다. 비밀번호가 바뀌었다는 것은 다른 컨테이너에서 새 값으로 들어가지고 옛 값이 `password authentication failed`로 막히는 것으로 봤다.

| 항목 | 결과 | 근거의 종류 |
|---|---|---|
| 4가 `.env`의 비밀번호만 바꾸고 `up -d` | `up` 종료 1. postgres는 새 값으로 다시 만들어졌지만 데이터베이스의 비밀번호는 옛것 그대로라, migrate가 `FATAL:  password authentication failed for user "agent_os"`로 종료 2. serve는 `created`(떠 있지 않음)였다 | 프로브가 다시 낸다 |
| 4나 컨테이너 안의 유닉스 소켓으로 `ALTER ROLE`(옛 비밀번호를 묻지 않는다) 뒤 `up -d --wait` | `ALTER ROLE` 종료 0, `up` 종료 0, migrate 종료 0, serve `healthy`, 넣어 둔 줄이 남았다 | 프로브가 다시 낸다 |
| 4다 serve가 떠 있는 채 `ALTER ROLE`을 먼저 | 4초 동안 이미 맺은 접속의 줄은 +9, 새 접속의 줄은 +0이었다(serve 로그에 인증 실패 문구). 이어서 `.env`를 고치고 `up -d --wait`하면 셋이 다시 만들어지고 모두 정상이었다 | 프로브가 다시 낸다 |
| 4라 `pg_hba.conf`와 비밀번호 저장 | 로컬 소켓 `trust`, `127.0.0.1/32`와 `::1/128` `trust`, 그 밖의 TCP `scram-sha-256`. `password_encryption`은 `scram-sha-256`이고 저장된 값은 `SCRAM-SHA-256`으로 시작한다. `log_statement`는 `none` | 프로브가 다시 낸다 |
| 4라 `ALTER ROLE`의 비밀번호가 PostgreSQL 로그에 남는가 | 성공한 `ALTER ROLE` 두 번의 비밀번호는 로그에 없었다. 문법이 틀려 실패한 문장은 `STATEMENT:  ALTER ROLE agent_os PASSWORD 'ctl-…' BOGUS`로 비밀번호째 남았다(`log_min_error_statement`가 `error`) | 프로브가 다시 낸다 |
| 4마 제안하는 절차(`change_password.sh`를, 옛 값과 옛 값을 든 env 파일을 가리키는 `COMPOSE_ENV_FILES`를 내보낸 부모 셸의 Git Bash로 한 줄씩) | `unset` 뒤의 세 줄의 종료 코드 [0, 0, 0]. 데이터베이스는 새 비밀번호만 받았다. 둘째 줄 뒤에도 migrate와 serve는 건드려지지 않았다. 셋째 줄의 psql은 묻는 글 두 줄(`Enter new password for user "agent_os":`, `Enter it again:`)을 찍고 기다리지 않았다. 마지막에 migrate 종료 0, serve `healthy`, 넣어 둔 줄이 남았고 새 비밀번호는 로그에 없었다. serve의 새 접속 줄 사이의 가장 긴 틈은 6.8초였다 | 프로브가 다시 낸다. 값은 `run-20261118-223809-ef866e`의 것이다(아래 "다시 돌리기"). `COMPOSE_ENV_FILES` 없이 같은 꼴의 절차를 친 앞 실행(`run-20261118-212254-d49023`)에서 같은 틈은 2.8초였고, 앞선 두 절차(값을 `-v`로 넘긴 첫 판, `\getenv`로 읽은 둘째 판)의 실행에서는 2.7초, 2.7초, 5.7초, 6.8초였으며, 뒤의 둘은 원본 출력을 손으로 봤다. `COMPOSE_ENV_FILES`가 다른 파일을 가리키면 compose가 `.env`를 읽지 않는 것은 `docker compose config`로 손으로 봤다(위 "판정 기준을 바꾼 것"의 여섯째). 묻는 글은 원본 출력을 손으로 봤다 |
| 4바 절차의 셋째 줄(`\password`)이 서버에서 실패할 때 | 없는 계정(`probe_missing_role`)에 같은 꼴로 `\password`를 치자 psql이 종료 1(`ERROR:  role "probe_missing_role" does not exist`)이었다. PostgreSQL 로그에 그 문장이 `STATEMENT` 줄로 남았고, 그 안의 비밀번호는 `SCRAM-SHA-256$`으로 시작하는 해시였다. 넣은 평문 표지는 로그 어디에도 없었다 | 프로브가 다시 낸다 |

### 5. 변수 치환과 `.env`

| 항목 | 결과 | 근거의 종류 |
|---|---|---|
| 5가 치환 꼴(`docker compose config`) | 받음: `${V}`, `${V:-d}`, `${U-d}`, `${V:+r}`, `${V+r}`, `${V:?e}`(양성 대조). 거부(종료 1): `${V#prefix-}`, `${V%-suffix}`, `${V##*-}`, `${V/body/x}`, `${V:0:6}`, `${#V}`. 거부 문구는 모두 `invalid interpolation format for services.probe.environment.OUT.`와 `You may need to escape any $ with another $.`다. 연결 문자열에서 비밀번호를 떼어 낼 문법은 없었다 | 프로브가 다시 낸다. 꼴의 목록은 원문을 받아 읽었다(아래 "받아 읽은 원문") |
| 5나 `:?`(줄이 없을 때와 빈 값일 때) | `config`와 `up -d` 모두 종료 1, `required variable AGENT_OS_DATABASE_PASSWORD is missing a value: .env 에 AGENT_OS_DATABASE_PASSWORD 가 없다`, 만든 컨테이너 0개 | 프로브가 다시 낸다 |
| 5나 부모 셸의 같은 이름 변수 | 셸에 있으면 `.env`보다 셸의 값이 든다 | 프로브가 다시 낸다 |
| 5마 배포 안내 9절의 이미지 받기와 목록(`.env`의 비밀번호 줄이 빈 값) | `docker compose pull`과 `docker compose config --images` 모두 종료 1, 5나와 같은 `required variable … is missing a value` 문구. 같은 `.env`에 셸 값을 앞에 붙이면(`AGENT_OS_DATABASE_PASSWORD=unused docker compose …`) `pull`은 종료 0에 `Image postgres@sha256:… Pulled`, `config --images`는 종료 0에 세 줄이고 겹치는 줄을 빼면 이미지 하나(세 서비스가 같은 이미지다) | 프로브가 다시 낸다(5번만 다시 돌린 실행, 아래 "다시 돌리기") |
| 5다 `.env` 값과 컨테이너가 받은 값 | 그대로: 16진수 64자, `p@s:s/w`, `abc#def`, `a b`, `a%b`, `a\b`. 바뀜: `abc$def` → `abc`(경고 `The "def" variable is not set`), `abc #def` → `abc`, `'quoted'`와 `"quoted"` → `quoted`. `$`를 넣으려면 `abc$$def`나 `'abc$def'`(둘 다 `abc$def`가 든다) | 프로브가 다시 낸다 |
| 5라 띄워서 본 접속(연결 문자열 `postgresql://agent_os:<값>@postgres:5432/agent_os`) | 데이터베이스의 비밀번호는 다섯 값 모두 컨테이너가 받은 값이었다. migrate 대역의 `psql`은 16진수와 `$$`에서 접속했고, `@ : /`는 `invalid integer value "s" for connection option "port"`, 공백은 `unexpected spaces found in "a b", use percent-encoded spaces (%20) instead`, `%`는 `invalid percent-encoded token: "a%b"`로 종료 2 | 프로브가 다시 낸다 |

## 제안하는 compose 조각과 비밀번호 바꾸기 절차

이 폴더의 `compose.yaml`에서 대역에만 있는 것(`PROBE_` 변수, `command`, `serve`의 `init`과 `stop_grace_period`)을 뺀 모양이다. 3·4·5가 이 모양을 그대로 띄웠고, PostgreSQL 서비스의 권한 줄은 1나, 상태 확인은 2다가 잰 것이다. 변수 이름(`AGENT_OS_DATABASE_PASSWORD`, `AGENT_OS_DATABASE_URL`)은 이 프로브가 붙인 것이고 명세가 정한다. `migrate`의 `image`와 `command`, `serve`의 나머지 줄은 지금의 `deploy/standalone/compose.yaml`을 따른다고 보고 적었다(재지 않았다).

```yaml
x-health: &health            # deploy/standalone/compose.yaml 의 앵커 그대로
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 30s
  start_interval: 2s

services:
  postgres:
    image: postgres@sha256:b9f6b8ff03b62f3cfd9d9ba3fe56226a9991c79d3fb46fd46536263bf02be553
    user: "999:999"            # 진입 스크립트의 chown 과 gosu 가 돌지 않는다
    read_only: true
    cap_drop: [ALL]
    security_opt: ["no-new-privileges:true"]
    tmpfs:
      - /var/run/postgresql    # 없으면 잠금 파일을 못 만들어 뜨지 못한다
    restart: unless-stopped
    environment:
      POSTGRES_USER: agent_os
      POSTGRES_DB: agent_os
      POSTGRES_PASSWORD: ${AGENT_OS_DATABASE_PASSWORD:?.env 에 AGENT_OS_DATABASE_PASSWORD 가 없다}
    volumes:
      - pgdata:/var/lib/postgresql
    healthcheck:
      <<: *health
      test: [CMD, pg_isready, -h, 127.0.0.1, -U, agent_os, -d, agent_os]   # 유닉스 소켓이 아니라 TCP

  migrate:
    image: ${AGENT_OS_NAMESPACE}/agent-os-runtime:${AGENT_OS_VERSION}      # serve 와 같은 이미지
    command: [agent-os, migrate]
    restart: "no"
    depends_on:
      postgres:
        condition: service_healthy
    environment:
      AGENT_OS_DATABASE_URL: postgresql://agent_os:${AGENT_OS_DATABASE_PASSWORD:?.env 에 AGENT_OS_DATABASE_PASSWORD 가 없다}@postgres:5432/agent_os

  serve:
    # (지금의 줄 그대로)
    depends_on:
      migrate:
        condition: service_completed_successfully
    environment:
      AGENT_OS_DATABASE_URL: postgresql://agent_os:${AGENT_OS_DATABASE_PASSWORD:?.env 에 AGENT_OS_DATABASE_PASSWORD 가 없다}@postgres:5432/agent_os

volumes:
  pgdata: {}
```

볼륨 이름 `pgdata`는 이 프로브가 쓴 이름이다. 명세는 단독 compose의 데이터베이스 볼륨을 `database`(Docker의 이름은 `agent-os_database`)로 정했으므로, 이 조각을 옮길 때는 마운트와 맨 아래 선언을 모두 `database`로 쓴다(PR 봇이 짚었다).

비밀번호는 `openssl rand -hex 32`처럼 0~9와 a~f만 든 값이어야 한다. 5다·5라에서 그런 값만 compose와 libpq 둘을 모두 바뀌지 않고 지났다.

데이터가 있는 볼륨에서 비밀번호를 바꾸는 절차는 이 폴더의 `change_password.sh`이고, 4마가 이 파일의 줄을 Git Bash로 한 줄씩 쳤다. 먼저 `.env`의 `AGENT_OS_DATABASE_PASSWORD` 줄을 새 값으로 고치고, 묶음을 푼 폴더에서 네 줄을 그대로 붙여 넣는다.

```bash
unset AGENT_OS_DATABASE_PASSWORD COMPOSE_ENV_FILES
docker compose up -d --wait postgres &&
docker compose exec -T postgres sh -c 'printf "%s\n%s\n" "$POSTGRES_PASSWORD" "$POSTGRES_PASSWORD" | psql -U agent_os -d agent_os -v ON_ERROR_STOP=1 -c "\password agent_os"' &&
docker compose up -d --wait --wait-timeout 600
```

첫 줄은 셸에 남은 같은 이름의 변수를 지운다. 셸의 값이 `.env`를 덮기 때문이다(5나). 같은 줄은 `COMPOSE_ENV_FILES`도 지운다. 그 변수가 다른 파일을 가리키면 compose는 `.env` 대신 그 파일을 읽는다(손으로 봤다, 위 "판정 기준을 바꾼 것"의 여섯째). 둘째 줄은 PostgreSQL 컨테이너만 새 `.env`로 다시 만든다(데이터베이스의 비밀번호는 아직 옛것이고, `migrate`와 `serve`는 건드리지 않는다). 셋째 줄은 그 컨테이너 안에서 새 값으로 계정의 비밀번호를 바꾼다. 값은 컨테이너의 환경 변수 `POSTGRES_PASSWORD`에서 오고, psql의 `\password`가 표준 입력에서 두 번 받아 SCRAM 해시로 바꿔 보낸다. 그래서 운영자가 치는 명령줄에도 컨테이너 안 프로세스의 인자에도 값이 실리지 않고(명령의 글에 변수 이름만 있고, 그 이미지의 `sh`인 dash에서 `printf`는 내장 명령이다. 그 이미지에서 `command -v printf`가 `printf`를 낸 것을 손으로 봤다), 서버가 그 문장을 거절해도 로그에는 해시만 남았다(4바). 컨테이너 안의 유닉스 소켓은 `trust`라 옛 비밀번호를 묻지 않고, 새 값은 PostgreSQL 로그에 남지 않았다(4마). 넷째 줄은 `migrate`와 `serve`를 새 연결 문자열로 다시 만든다. 뒤의 세 줄은 `&&`로 이어져, 한 줄이 실패하면 다음 줄을 치지 않는다. 셋째 줄이 끝난 뒤부터 넷째 줄이 `serve`를 다시 띄울 때까지 옛 `serve`의 새 접속은 인증에 실패한다.

앞선 두 판의 절차는 이렇게 바뀌었다. 첫 판은 값을 `sh -c '… psql -v new="$POSTGRES_PASSWORD"'`로 넘겨 psql 프로세스의 인자에 실었고, PR 직전 리뷰가 짚어 둘째 판에서 psql의 `\getenv`로 읽어 `ALTER ROLE agent_os PASSWORD :'new'`를 보내게 바꿨다. 둘째 판은 서버가 그 문장을 거절하면 평문째 로그에 남고(4라의 문법 오류와 같은 길), 셸에 남은 옛 값과 앞 줄의 실패를 다루지 않아 PR 봇이 짚었다(위 "판정 기준을 바꾼 것"의 다섯째).

## 받아 읽은 원문(5번)

2026-11-18 15:44(KST)에 받아 세션 스크래치패드에 두고 읽었다. 요청에는 일반 User-Agent 하나만 실었다. 웹 요약은 쓰지 않았다.

| 원문 | 주소 | 판 | 읽은 줄 |
|---|---|---|---|
| Compose 명세 `12-interpolation.md` | `https://raw.githubusercontent.com/compose-spec/compose-spec/6b3a2a93e77c30ded1aa8264307e74d1208a6eae/12-interpolation.md` | 받은 때의 `main` 머리 `6b3a2a93e77c…`. 이 파일을 마지막으로 고친 커밋은 `6c91ee691fad…`(2024-11-13) | 8~18줄(`:-`, `-`, `:?`, `?` 넷만 적는다), 26~27줄 |
| Docker 문서 "Interpolation" | `https://docs.docker.com/reference/compose-file/interpolation.md`(같은 내용의 HTML 판도 받았다) | 받은 날의 판 | 13~24줄(위 넷에 `:+`, `+`를 더해 여섯), 32~33줄 |
| compose-go `template/template.go` | `https://raw.githubusercontent.com/compose-spec/compose-go/v2.16.1/template/template.go` | v2.16.1. Compose v5.6.1의 `go.mod`(`https://raw.githubusercontent.com/docker/compose/v5.6.1/go.mod`)가 드는 판 | 32줄(중괄호 안의 문법), 233~238줄(연산자 여섯) |
| compose-go `dotenv/parser.go` | `https://raw.githubusercontent.com/compose-spec/compose-go/v2.16.1/dotenv/parser.go` | v2.16.1 | 152~161줄(따옴표 없는 값), 192~202줄(큰따옴표 값) |

두 문서는 같은 문장으로 끝난다. 명세 26~27줄과 Docker 문서 32~33줄의 "Other extended shell-style features, such as `${VARIABLE/foo/bar}`, are not supported by Compose."다. 구현은 중괄호 안을 `[_a-z][_a-z0-9]*(?::?[-+?](.*))?`(template.go 32줄)로만 받아, 이름 뒤에 올 수 있는 것은 `:-`, `-`, `:?`, `?`, `:+`, `+` 여섯뿐이다(233~238줄). 값의 앞뒤를 떼는 `#`, `%`나 바꾸기 `/`는 이 꼴에 들지 않는다. `.env` 파서는 따옴표 없는 값을 줄 끝까지 읽고, 거기서 처음 나오는 ` #`(공백 뒤 `#`) 앞에서 자르고, 오른쪽 공백을 떼고, 변수를 치환한다(parser.go 154~160줄). 작은따옴표 값은 그대로 두고, 큰따옴표 값은 이스케이프를 푼 뒤 치환한다(192~202줄). 명세와 Docker 문서가 다른 곳은 하나다. 명세는 `:+`와 `+`를 적지 않는다.

## 다시 돌리기

저장소 루트에서 친다.

```
uv run python .scratch/postgres-foundation/probes/compose_shape/run.py
```

- 항목을 고르려면 `--sections 1,3,4,5,2`(기본은 이 차례로 모두). `--repeat`은 2가·2나의 되풀이 수(기본 5), `--bash`는 4마의 절차를 칠 bash(비우면 PATH에서 찾고, `docker compose version`이 도는지 먼저 본다. 윈도에서는 Git Bash), `--verbose`는 회차마다 본 것 전부를 화면에도 찍는다.
- 원본 출력은 `--work`(기본은 시스템 임시 폴더의 `pgf-shape`) 아래 실행마다 새 폴더의 `raw.log`(명령마다 종료 코드와 출력)와 `rounds.jsonl`(회차마다 본 것 전부)이다. 첫 줄에 그 경로가 찍힌다.
- 필요한 것: Docker Engine과 Compose 플러그인, 로컬에 이미 받아 둔 `postgres@sha256:b9f6b8ff…be553`. 이미지가 없으면 받지 않고 종료 1로 멈춘다. 호스트 포트는 열지 않는다. compose 프로젝트 이름은 `pgf-shape-<무작위>-<회차>`이고, 이 실행이 만든 프로젝트만 `down -v`로 지우고 끝에 남은 것이 없는지 본다(남으면 측정 아님으로 센다).
- 걸린 시간: 마지막 실행(원본 출력 폴더 `run-20261118-163425-b6e060`)은 16:34:25에 시작해 16:43:19에 끝났다(약 9분, 108회차, 측정 아님 0회차, 종료 0). 그 바로 앞의 실행도 약 11분이었다.
- 그 뒤 명세의 셀프 리뷰가 배포 안내 9절의 명령을 짚어 5마를 더하고 `--sections 5`로 5번만 다시 돌렸다(원본 출력 폴더 `run-20261118-180923-713484`, 약 1분, 39회차, 측정 아님 0회차, 종료 0). 5마의 값은 이 실행의 것이고, 5번의 나머지 회차도 이 실행에서 위 표와 같은 값을 다시 냈다. 5마의 셸 값 `pull`은 레지스트리에 닿는다(이미 받은 digest라 새로 받은 층은 없다). 5마의 표지는 실행 전에 같은 꼴의 compose 파일 하나로 두 명령의 출력을 손으로 보고 골랐다(세션 스크래치패드의 스크립트, 커밋하지 않았다).
- 그 뒤 PR 직전 리뷰(CodeRabbit CLI)가 4마의 둘째 줄이 새 비밀번호를 psql 프로세스의 인자에 싣는다고 짚어, `change_password.sh`의 둘째 줄을 `\getenv`로 바꾸고 `--sections 4`로 4번만 다시 돌렸다(원본 출력 폴더 `run-20261118-193353-4b48d5`, 19:33:53에 시작해 19:34:51에 끝났다, 측정 7회차, 측정 아님 0회차, 종료 0). 이 실행의 4마는 둘째 판의 절차를 쟀다.
- 그 뒤 PR 606의 봇 첫 회차를 반영해(위 "판정 기준을 바꾼 것"의 다섯째) 절차를 지금의 네 줄로 바꾸고 4바를 더한 뒤 `--sections 3,4,5`로 다시 돌렸다(원본 출력 폴더 `run-20261118-212254-d49023`, 21:22:54에 시작해 마지막 명령을 21:26:15에 쳤다, 측정 62회차, 측정 아님 0회차, 종료 0). 4바의 값과 3의 다른 수치(3의 머리 문단)는 이 실행의 것이고, 3·4·5의 나머지 회차도 이 실행에서 위 표와 같은 결과 문구를 다시 냈다.
- 그 뒤 PR 606의 봇 둘째 회차를 반영해(위 "판정 기준을 바꾼 것"의 여섯째) 절차의 첫 줄에 `COMPOSE_ENV_FILES`를 더하고 `--sections 4`로 4번만 다시 돌렸다(원본 출력 폴더 `run-20261118-223809-ef866e`, 22:38:09에 시작해 마지막 명령을 22:39:11에 쳤다, 측정 8회차, 측정 아님 0회차, 종료 0). 4마의 값은 이 실행의 것이고, 4번의 나머지 회차도 이 실행에서 위 표와 같은 결과 문구를 다시 냈다.
- 종료 코드는 표지가 서지 않은 회차가 하나라도 있으면 1이다(`tools/probe_kit.py` `Rounds`).
- 타입 검사: `uv run pyright -p .scratch/postgres-foundation/probes/compose_shape`(이 폴더의 `pyrightconfig.json`, strict).

## 환경

2026-11-18, Windows 10 Home 19045의 Docker Desktop. 엔진 29.9.2(클라이언트도 29.9.2), 엔진이 도는 커널 `6.18.58.1-microsoft-standard-WSL2`(Docker Desktop이 WSL2에 띄운 리눅스 VM), Docker Compose 5.6.1. 이미지는 `postgres@sha256:b9f6b8ff03b62f3cfd9d9ba3fe56226a9991c79d3fb46fd46536263bf02be553`(이미지 id `sha256:3cccc725163a…`, PostgreSQL 18.7, Debian trixie)이고 새로 받지 않았다. 같은 엔진에서 다른 세션의 컨테이너(rag-engine의 시험 데이터베이스와 평가 컨테이너, 이 기능의 다른 프로브)가 함께 돌았다. 그래서 걸린 시간은 부하에 따라 흔들린다(1의 처음 띄우기가 앞선 실행에서 2.2~5.2초, 마지막 실행에서 1.4~2.0초였다). `run.py`가 시작할 때 이 판들을 찍는다.

## PR 봇이 짚었지만 고치지 않은 것

PR 606의 봇 첫 회차가 짚은 이 프로브의 지적 가운데 둘, 둘째 회차의 Major 둘, 셋째 회차의 Major 둘은 코드를 고치지 않았다. 셋째 회차의 둘 가운데 `--image`는 첫 회차 #22와 같은 자리다. 둘째·셋째 회차의 Minor는 PR 코멘트에 보류 이유를 남겼다.

- **원본 출력에 남는 시험용 비밀번호(Critical).** `raw.log`에는 명령의 인자와 출력이 그대로 남아 `PGPASSWORD`, 컨테이너의 환경, 5다·5라의 비밀번호 값이 든다. 그 값은 모두 이 실행이 무작위로 만들었거나 5다·5라가 일부러 고른 시험용 값이고(`run.py`의 `secrets.token_hex`와 5다의 값 표), 러너는 운영 값이 든 변수를 지운 환경으로 하위 명령을 띄우며(`child_env`), 데이터베이스는 호스트에 포트를 열지 않고 실행이 끝나면 `down -v`로 지운다. 원본 폴더는 저장소 밖(시스템 임시 폴더)이다. 그래서 지금 쓰이는 비밀은 실리지 않는다고 판단했다. 이 프로브를 운영 값이 든 셸에서 고쳐 쓸 사람은 `child_env`가 그 변수를 지우는지 먼저 본다.
- **`--image`(Major #22).** 사전 검사만 `--image`의 digest를 보고 compose 파일들은 고정 digest를 쓴다. 원본 출력이 남은 세 실행(`run-20261118-180923-713484`, `…-193353-4b48d5`, `…-212254-d49023`)은 첫 줄에 고정 digest를 찍어 두 값이 같았으므로 결과에 닿지 않는다. 전체 실행 `run-20261118-163425-b6e060`의 원본은 임시 폴더에 남아 있지 않아 다시 보지 못했다. 다른 이미지로 다시 잴 사람은 이 옵션을 지우거나 compose 파일과 5마의 표지까지 같은 digest를 쓰게 고친다.
- **3아의 복구 판정(둘째 회차 Major).** `restart` 전에 줄 수를 읽은 뒤 PostgreSQL이 실제로 멈추기 전에 대역이 줄을 세 개 더 쓰면, 재시작 뒤 접속이 한 번도 성공하지 않아도 "새 접속은 돌아왔다"가 참이 된다. 마지막 실행(`run-20261118-212254-d49023`)의 3아는 새 접속 줄이 23에서 31로 여덟 늘었고, serve 로그에 `새 접속이 실패했다`와 `Connection refused`가 있어 재시작 동안 접속이 끊겼던 것은 보인다. 대역은 줄 하나를 쓰고 0.5초를 쉬므로, 멈추기 전의 틈에 여덟이 다 쓰였을 가능성은 낮다고 본다(어림. 멈춘 시각과 줄의 시각을 견주지는 않았다). 다시 잴 사람은 줄의 `at`을 같은 데이터베이스의 `pg_postmaster_start_time()`과 견줘, 다시 띄운 뒤에 쓴 줄만 센다.
- **2다의 표본 구간(둘째 회차 Major).** 바깥 표본은 성공 열다섯 번에서 멈추므로, `healthy`가 늦게 온 회차에서는 그 뒤의 표본이 없어 측정 아님으로 빠질 수 있다. 그러면 확인이 늦는 꼴(`start_interval: 2s`)의 회차만 골라 빠진다. 2다를 잰 마지막 전체 실행(`run-20261118-163425-b6e060`)은 측정 아님이 0회차였으므로(아래 "다시 돌리기") 빠진 회차가 없고, 위 2다 표는 꼴마다 세 번을 모두 담는다. 다시 잴 사람은 성공 횟수 대신 `healthy` 뒤 몇 초까지 표본을 이어 간다.
- **3가의 측정 표지(셋째 회차 Major).** 회차를 측정으로 세는 표지는 `up`이 돌아온 뒤 90초 안에 serve가 `healthy`가 되는지라서, `--wait`이 serve의 정상을 기다리지 않고 돌아왔어도 측정으로 센다. 위 3가 행의 결론(`--wait`이 든 셋이 돌아온 때 serve가 `healthy`였다)은 그 표지가 아니라, `up`이 돌아온 직후에 읽은 컨테이너 상태(결과 문구의 serve 상태와 건강)에서 왔다. 같은 자리에서 `up -d`는 `starting`을 냈으므로, 돌아온 직후의 상태는 기다렸다는 해석과 기다리지 않았다는 해석을 가르고, 결론은 그 관찰로 선다고 본다. 다만 표지가 그 상태를 단언하지 않아, `--wait`이 기다리지 않은 회차도 측정으로 셌을 수 있다. 다시 잴 사람은 표지를 돌아온 직후의 상태로 옮긴다.

## 재지 못한 것

- 리눅스 서버의 Docker Engine. ADR은 1·2를 "리눅스에서 잰다"고 했는데, 이 프로브는 Docker Desktop이 WSL2에 띄운 리눅스 엔진에서 돌았다. 커널의 권한 검사와 이름 있는 볼륨의 소유는 같은 리눅스 커널이 정한다고 보지만(어림), 서버의 엔진(다른 스토리지 드라이버, SELinux·AppArmor 정책)에서는 다시 보지 않았다.
- 호스트 폴더를 붙인 볼륨(bind mount)의 소유. 이름 있는 볼륨만 봤다. 운영자가 `/var/lib/postgresql`을 호스트 폴더로 바꾸면 1나(uid 999로 띄우기)는 그 폴더의 소유에 따라 실패할 수 있다(어림).
- rootless Docker와 userns-remap.
- 데몬이나 서버를 다시 켠 뒤의 복귀(이 기능의 다른 프로브가 맡는다).
- 실제 `agent-os migrate`와 `serve`. 대역은 PostgreSQL 이미지의 `psql`을 부르는 셸이다. 실제 `serve`의 다시 시도, 멈출 때의 문구, 실제 마이그레이션이 도는 시간은 이 프로브에 없다.
- SQLAlchemy와 asyncpg가 연결 문자열을 읽는 방식. 5라의 주소 판정은 libpq(`psql`)의 것이다. asyncpg는 libpq를 쓰지 않으므로 같은 주소를 다르게 읽을 수 있다(어림).
- migrate의 다른 재시작 정책(`on-failure` 등). `restart: "no"` 하나만 띄웠다.
- 실제 마이그레이션이 길어 `--wait-timeout`(600초)에 닿는 경우. 대역의 migrate는 1초 안에 끝난다.
- 유닉스 소켓 꼴의 상태 확인으로 `service_healthy`를 기다린 migrate가 실제로 실패하는지. 2다는 `healthy` 뒤 다른 컨테이너의 접속이 실패한 것까지 봤다.
- 부하가 큰 엔진에서 `start_interval`의 차이. 2다의 값은 이 PC에서 다른 세션과 함께 돈 때의 것이다.
- 2의 걸린 시간을 낳는 원인(WSL2의 시계, 부하). 표본 줄의 시각은 컨테이너 안의 `date`이고 준비 줄의 시각은 Docker가 로그를 받은 때라, 둘 사이에 수십 밀리초의 어긋남이 있을 수 있다(어림).
