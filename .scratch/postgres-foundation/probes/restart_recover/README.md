# postgres-foundation restart_recover 프로브

## 무엇을 왜 재나

ADR 0066(`docs/adr/0066-agent-os-reaches-postgres-through-sqlalchemy-core-and-asyncpg-and-migrates-forward-only-before-serve.md`) 결정 "compose 배치"의 어림 하나를 리눅스의 Docker Engine에서 잰 프로브다.

> 그래서 데몬이나 서버가 다시 켜진 뒤에는 `serve`가 PostgreSQL보다 먼저 뜰 수 있다고 보고, 그때는 `serve`의 다시 시도와 재시작 정책이 받친다고 본다(어림, 명세가 잰다).

배치는 그 결정의 모양만 옮겼다. PostgreSQL 하나(이름 있는 볼륨, `pg_isready` 상태 확인, 재시작 정책 `unless-stopped`), 한 번 돌고 끝나는 `migrate`(재시작 정책 `"no"`, PostgreSQL이 건강해진 뒤), 그 뒤에 뜨는 `serve`(`unless-stopped`, `migrate`가 성공으로 끝난 뒤)다. `migrate`와 `serve`는 진짜가 아니라 같은 PostgreSQL 이미지 안의 sh 스크립트(대역)다. `serve` 대역은 뜰 때 `RETRY_SECONDS`초 동안 0.5초 간격으로 `pg_isready`와 `psql -c 'select 1'`을 되풀이하고, 못 붙으면 1로 끝나 재시작 정책에 맡긴다. 측정 도구로 `watch` 컨테이너를 하나 더 둔다. 배치에 없는 것으로, 다른 컨테이너에서 새로 거는 접속이 언제 되는지를 0.2초 간격으로 끝없이 적는다.

"리눅스 서버"는 이 PC(Windows의 Docker Desktop)에 띄운 공식 Docker-in-Docker 컨테이너(`docker:29.9.2-dind`, 이하 dind)다. compose는 그 안의 Docker Engine에서 돈다. 사건 셋은 이렇게 낸다(`.scratch/release-image/probes/bridge_recover/`의 방법).

| 사건 | 내는 법 | 그 회차에 났다는 표지 |
|---|---|---|
| 데몬만 다시 켬 | dind 안의 dockerd에 TERM. dind의 첫 프로세스(`supervise.sh`)가 dockerd를 다시 띄운다 | `supervise.sh`가 센 dockerd 시작 횟수가 늘고 dockerd의 pid가 바뀌었다 |
| 서버를 정상으로 껐다 켬 | 바깥에서 `docker restart -t 120` dind | dind의 시작 시각이 바뀌었다 |
| 전원 끊김 | 바깥에서 `docker kill` dind 뒤 `docker start` | dind의 시작 시각이 바뀌었고, 돌아온 PostgreSQL의 기록에 `database system was interrupted`가 있다 |

여기서는 결정하지 않고 본 것만 적는다. 결정은 명세(`.scratch/postgres-foundation/spec.md`)가 한다. 규약은 `docs/agents/issue-tracker.md`의 "프로브와 근거", 짓는 규칙은 `.claude/rules/probes.md`다.

결과는 2026-11-18의 실행 넷에서 왔다. 모두 새로 띄운 dind에서 돌았다.

| 실행 | 회차 | 무엇에 쓰나 |
|---|---|---|
| 전체(항목 여섯, `--rounds 3`), 약 23분 | 측정 51, 측정 아님 0, 종료 코드 0 | 아래 값의 기본 |
| 그 바로 앞의 전체 | 측정 50, 측정 아님 0, 종료 코드 0 | 항목 0~3과 5의 코드가 같아 값을 괄호로 함께 든다. 항목 4는 끊긴 첫 삶의 마지막 줄을 적지 않던 판이다 |
| 항목 0만 | 측정 7, 측정 아님 0, 종료 코드 0 | 바깥의 `postgres:18`이 digest와 같은 이미지인지 확인하는 줄을 더한 뒤 |
| 항목 4만(`--sections 4`) | 측정 10, 측정 아님 0, 종료 코드 0 | 붙지 않을 때 컨테이너만 지우는 갈래(`down`, 볼륨은 남김)를 더한 판. 지금의 `run.py`가 이 판이다 |

그 앞의 판(항목 3의 KILL 표지와 항목 4의 보고를 고치기 전)의 실행에서 본 것은 "손으로 봤다(그 실행의 원본 출력)"로 따로 밝힌다.

근거의 종류는 셋이다. 프로브가 다시 낸다(`run.py`가 표지를 보고 센 회차), 손으로 봤다(무엇을 봤는지 함께 적는다), 어림. 회차 수와 시간은 실행마다 달라지므로 차례와 크기만 읽는다.

## 결과

N은 `serve` 대역의 `RETRY_SECONDS`(다시 시도하는 초)다. "다시 뜨기 시작"은 사건 뒤 안쪽 데몬이 그 프로젝트의 컨테이너를 처음 띄운 시각이다. "ready"는 PostgreSQL 기록의 `database system is ready to accept connections`, "TCP 첫 성공"은 `watch`가 다른 컨테이너에서 새로 건 `select 1`이 처음 된 시각이다. 값은 전체 실행의 것이고(항목 4는 전체 실행과 항목 4만 돌린 실행을 합쳤다), 괄호 안은 그 앞의 전체 실행(아래 "앞의 실행")이다.

| 항목 | 결과 | 근거 |
|---|---|---|
| 1. 다시 뜨는 컨테이너 | 세 사건 모두 postgres, serve, watch가 사람 손 없이 다시 떴다. 27/27(27/27) | 프로브가 다시 낸다 |
| 1. migrate가 다시 돌지 않음 | `migrate`는 `exited(0)` 그대로였고, 표의 줄이 사건 전과 같았다(`migrate`가 다시 돌면 줄 `migrate`가 하나 는다). 27/27(27/27) | 프로브가 다시 낸다 |
| 1. 시작 차례 | serve가 postgres보다 먼저 뜬 회차가 데몬 4/9, 서버 4/9, 전원 3/9(4/9, 5/9, 1/9)다. 둘의 차이는 −0.03~+0.03초(−0.06~+0.18초)였다 | 프로브가 다시 낸다 |
| 1. serve가 붙기까지(N=30) | serve 첫 시작 뒤 최소 0.07 / 중앙값 0.65 / 최대 0.70초, n=9(0.12 / 0.78 / 5.09초). 9/9(9/9)가 첫 삶에서, 곧 재시작 없이 붙었다 | 프로브가 다시 낸다 |
| 1. 붙기 전의 실패 | `Connection refused`, `FATAL: the database system is starting up`, 앞의 실행의 전원 끊김에서 `FATAL: the database system is not yet accepting connections` 도 났다. 원문은 아래 "실패의 문구" | 프로브가 다시 낸다 |
| 1. 줄이 남음 | 사건 전에 넣은 줄이 27/27(27/27) 남았다 | 프로브가 다시 낸다 |
| 2. N=0 | 9/9(9/9)가 붙었다. 7/9(6/9)는 첫 시도가 실패해 1로 끝난 뒤 재시작 정책으로 붙었고, 재시작 횟수는 0~1(0~2)이었다 | 프로브가 다시 낸다 |
| 2. N=5 | 9/9(9/9)가 첫 삶에서 붙었다 | 프로브가 다시 낸다 |
| 2. PostgreSQL이 접속을 받기까지 | 아래 "시간의 분포". 전원 끊김이 가장 길었고, 컨테이너 시작 → TCP 첫 성공이 최대 0.69초(4.93초)다 | 프로브가 다시 낸다 |
| 3. `docker kill` postgres | 다시 뜨지 않았다(`exited(137)`, 25초 지켜봄). 2/2(2/2) | 프로브가 다시 낸다 |
| 3. postmaster를 바깥에서 KILL | 재시작 정책이 다시 띄웠다. 3/3(3/3), 죽은 뒤 0.22~0.32초(0.21~0.34초)에 컨테이너가 다시 뜨고 0.72~1.10초(0.92~3.42초)에 ready | 프로브가 다시 낸다 |
| 3. 같은 KILL, WAL을 쌓은 뒤 | 2/2(2/2)가 다시 떴고 ready까지 2.91·3.18초(6.92·6.42초). 넷 가운데 셋에서 그동안 watch가 `the database system is not yet accepting connections`를 받았다 | 프로브가 다시 낸다 |
| 3. `docker stop` postgres(대조) | 다시 뜨지 않았다(`exited(0)`). 2/2(2/2) | 프로브가 다시 낸다 |
| 3. serve 대역 | 항목 3의 모든 회차에서 시작 시각, 재시작 횟수, 기록 줄 수가 그대로였다 | 프로브가 다시 낸다 |
| 4. 초기화 중 데몬 재시작 | 첫 `up -d`가 종료 1로 끝나고 `migrate`와 `serve`는 `created`(만들었지만 띄운 적 없음)로 남았다. PostgreSQL의 초기화는 끝났다. `up -d`를 다시 치면 붙었다. 4/4(2/2) | 프로브가 다시 낸다 |
| 4. 초기화 중 전원 끊김 | 6/6(2/2) 모두 볼륨이 망가진 채 남아, `up -d`를 다시 쳐도 `migrate`가 종료 2로 끝나 붙지 않았다. 꼴은 둘이었다. 반쯤 초기화된 꼴(5/6, 2/2)은 PostgreSQL이 뜨고 상태 확인이 `healthy`인데 `database "agent_os" does not exist`와 `no pg_hba.conf entry`로 접속을 거절했다. 되풀이해 죽는 꼴(1/6)은 `FATAL:  could not open file "global/pg_filenode.map": No such file or directory`를 40초에 968줄 되풀이했고 상태 확인은 `starting`이었다 | 프로브가 다시 낸다 |
| 4. 망가진 것이 볼륨인가 | 컨테이너와 네트워크만 지우고(`docker compose down`, 볼륨은 남김) `up -d`하면 3/3 붙지 않았고, 볼륨까지 지우고(`docker compose down -v`) `up -d`하면 6/6 붙었다 | 프로브가 다시 낸다 |
| 4. 되풀이해 죽는 꼴, 앞의 판 | 그 앞의 판 실행에서도 한 회차가 같은 꼴이었다. 끊긴 첫 삶의 마지막 줄이 `creating configuration files ... ok`였고 상태 확인은 `unhealthy`까지 갔다 | 손으로 봤다(그 실행의 원본 출력) |
| 4. migrate가 일하기 전 데몬 재시작 | `migrate`는 `exited(143)`로 끝나 다시 돌지 않았고 `serve`는 `created`로 남았다. `up -d`를 다시 치면 붙었다. 2/2(1/1) | 프로브가 다시 낸다 |
| 4. serve가 migrate 없이 뜸 | 한 번도 없었다. 0/12(0/5) | 프로브가 다시 낸다 |
| 5. 권한을 좁힌 postgres | `user: "999:999"`, 읽기 전용 루트, `cap_drop: [ALL]`, `no-new-privileges`, tmpfs 둘로 처음 떴고 serve 대역이 붙었다. 데몬을 다시 켠 뒤에도 돌아와 줄이 남았다. 1/1(1/1) | 프로브가 다시 낸다 |
| 0. 이미지 옮기기 | digest 참조로 `docker save` 한 것을 안쪽에서 `docker load` 하면 digest 참조로 찾지 못한다. 태그로 옮기면 태그로 돌고 RepoDigests에는 원래와 다른 digest가 붙는다 | 프로브가 다시 낸다 |
| 0. 대역의 양성 대조 | 붙을 수 있으면 붙고 0으로 끝난다, 포트가 닫힌 이름에는 `Connection refused`를 적고 1로 끝난다, postgres가 멈춰 있으면 이름 풀이 실패를 적고 1로 끝난다 | 프로브가 다시 낸다 |

### 시간의 분포(항목 1·2, 측정인 회차만)

사건마다 회차 9(N=0, 5, 30을 셋씩)다. 값은 최소 / 중앙값 / 최대 초다.

| 사건 | postgres 컨테이너 시작 → ready | postgres 컨테이너 시작 → TCP 첫 성공 | serve 첫 시작 → TCP 첫 성공 | 다시 뜨기 시작 → ready |
|---|---|---|---|---|
| 데몬만 다시 켬 | 0.06 / 0.07 / 0.10 (0.08 / 0.09 / 0.40) | 0.09 / 0.36 / 0.42 (0.11 / 0.36 / 0.82) | 0.07 / 0.35 / 0.40 (0.07 / 0.37 / 0.85) | 1.35 / 1.51 / 1.87 (1.41 / 1.68 / 3.79) |
| 서버를 정상으로 껐다 켬 | 0.07 / 0.07 / 0.09 (0.07 / 0.10 / 0.15) | 0.09 / 0.35 / 0.38 (0.11 / 0.41 / 0.46) | 0.06 / 0.35 / 0.40 (0.09 / 0.43 / 0.51) | 0.92 / 0.96 / 1.04 (0.94 / 1.23 / 1.74) |
| 전원 끊김 | 0.28 / 0.37 / 0.46 (0.33 / 0.57 / 4.41) | 0.35 / 0.61 / 0.69 (0.59 / 0.69 / 4.93) | 0.34 / 0.59 / 0.67 (0.58 / 0.67 / 4.75) | 1.28 / 1.44 / 1.65 (1.30 / 1.71 / 7.85) |

- 모든 사건을 모으면(n=27) serve 첫 시작 → TCP 첫 성공은 0.06 / 0.36 / 0.67초(0.07 / 0.44 / 4.75초), N=30에서 serve 첫 시작 → 붙음은 0.07 / 0.65 / 0.70초(0.12 / 0.78 / 5.09초)다.
- 앞의 실행의 긴 값은 전원 끊김의 N=30 두 회차에서 났다(postgres 컨테이너 시작 → ready 4.41·3.57초). 그 회차의 PostgreSQL은 `database system was interrupted` 뒤 복구에 몇 초를 썼다. 같은 사건의 다른 일곱 회차는 0.33~1.97초였다. 그래서 길이는 사건의 종류보다 그때 복구할 것이 얼마나 남았는지에 달렸다고 읽는다(어림).
- 항목 3의 KILL 뒤 PostgreSQL이 ready까지 쓴 시간은 0.72~3.42초, WAL을 쌓은 뒤(150만 줄 표 하나를 만든 직후)는 2.91~6.92초였다. 그 모든 회차에서 컨테이너는 0.19~0.43초에 다시 떴다.
- `watch`의 첫 성공은 ready보다 늦게 잡힐 수 있다. 시도 하나가 `pg_isready -t 1`과 접속 제한 2초(`PGCONNECT_TIMEOUT`)를 안고 있어, PostgreSQL이 돌아오는 동안 걸린 시도는 몇 초를 쓴다. 항목 3의 KILL 회차(실행 둘, 10회차)에서 ready 뒤 0.04~2.75초 늦었다. 그래서 TCP 첫 성공은 "이때까지는 된다"는 위쪽 값으로 읽는다(어림).

### 실패의 문구

대역(serve와 watch)이 시도마다 적은 문구의 원문이다. 마지막 두 줄만 PostgreSQL의 기록과 프로브가 친 psql에서 왔다. 주소(`172.19.0.x`)만 실행마다 다르다. psql 18.7의 문구이고, 진짜 `serve`(asyncpg)의 예외 꼴은 `../stack/README.md`의 "접속 실패의 꼴"이 잰다.

| 꼴 | 원문 | 어디서 났나 |
|---|---|---|
| 접속 거부 | `psql: error: connection to server at "postgres" (172.19.0.4), port 5432 failed: Connection refused Is the server running on that host and accepting TCP/IP connections?` | 세 사건 모두, 컨테이너가 뜬 직후. KILL과 `docker stop` 직후 |
| 뜨는 중 | `psql: error: connection to server at "postgres" (172.19.0.4), port 5432 failed: FATAL: the database system is starting up` | 세 사건 모두 |
| 복구 중 | `psql: error: connection to server at "postgres" (172.19.0.2), port 5432 failed: FATAL: the database system is not yet accepting connections DETAIL: Consistent recovery state has not been yet reached.` | 전원 끊김, WAL을 쌓은 뒤의 KILL |
| 이름 풀이 실패 | `psql: error: could not translate host name "postgres" to address: Name or service not known` | postgres 컨테이너가 멈춰 있을 때(`docker kill`, `docker stop`, 대조). 대조 회차에서 시도 하나에 6618~6675ms가 걸렸다(실행 셋) |
| 서버가 끊음 | `psql: error: connection to server at "postgres" (172.19.0.2), port 5432 failed: server closed the connection unexpectedly This probably means the server terminated abnormally before or while processing the request.` | `docker kill` 직후 1번 |
| 시간 초과 | `psql: error: connection to server at "postgres" (172.19.0.2), port 5432 failed: timeout expired` | 그 앞의 판 실행의 `docker kill` 직후 1번(항목 3의 코드는 같다). 손으로 봤다(그 실행의 원본 출력) |
| 반쯤 초기화된 볼륨 | PostgreSQL 기록의 `FATAL:  no pg_hba.conf entry for host "172.19.0.3", user "agent_os", database "agent_os", no encryption`, `FATAL:  database "agent_os" does not exist` | 항목 4의 초기화 중 전원 끊김 |
| 되풀이해 죽는 PostgreSQL | 프로브가 그 컨테이너 안에서 친 psql의 `psql: error: connection to server on socket "/var/run/postgresql/.s.PGSQL.5432" failed: FATAL:  the database system is in recovery mode` | 항목 4의 되풀이해 죽는 꼴 |

- 같은 시도의 `pg_isready`는 닿지 못할 때(접속 거부, 이름 풀이 실패) `postgres:5432 - no response`(종료 2), PostgreSQL이 뜨는 중이거나 복구 중이라 거절할 때 `postgres:5432 - rejecting connections`(종료 1)를 적었다.
- PostgreSQL 기록에는 꺼지는 동안 들어온 접속에 `FATAL:  the database system is shutting down`도 찍혔다(손으로 봤다, 전체 실행의 `raw.log`). 대역의 시도 문구로는 모이지 않았다.
- 문구 `password authentication failed`는 나지 않았다. `in recovery mode`는 위 되풀이해 죽는 꼴에서만 났고, 그때 serve 대역은 뜨지 않았다(`migrate`가 먼저 실패했다).

### 항목 3: PostgreSQL만 죽을 때

- `docker kill`(기본 신호 KILL)과 `crash.sh`의 KILL은 둘 다 컨테이너의 첫 프로세스(PostgreSQL의 postmaster)를 SIGKILL로 죽인다. 앞의 것은 다시 뜨지 않고 뒤의 것은 다시 떴다. 그래서 같은 신호로 죽어도 Docker가 시킨 멈춤이면 재시작 정책이 다시 띄우지 않는다. 재시작 정책이 살아 있고 25초가 다시 뜨기에 넉넉하다는 것은 KILL 회차가 같은 실행에서 보인다(0.19~0.43초에 다시 떴다). 뒤의 것이 다시 뜨기 전 종료 코드는 이 프로브가 적지 않았다.
- KILL은 `crash.sh`가 dind 안에서 보낸다. 그 컨테이너의 pid를 다시 읽어, 그 pid의 명령줄이 `postgres`로 시작하고 cgroup 경로에 그 컨테이너의 전체 id가 있을 때만 보낸다. 회차마다 `sent <pid> [postgres ] cgroup [0::/docker/<id> ]`가 찍혔다.
- 어느 경우에도 serve 대역은 건드려지지 않았다. 대역은 붙은 뒤 연결을 쥐지 않고 잠든다(`serve.sh`). 진짜 `serve`의 쉬던 연결이 PostgreSQL이 다시 뜬 뒤 어떻게 되는지는 `../stack/README.md`의 "쉬던 연결"이 잰다.

### 항목 4: 처음 띄우기가 끊길 때

`up -d`를 백그라운드로 치고, 그 컨테이너(초기화 중이면 postgres, 아니면 `migrate`)가 도는 것을 본 바로 뒤 사건을 냈다. 그 뒤 사람 손 없이 40초를 지켜보고, `up -d`를 다시 쳤다. 그래도 붙지 않으면 `docker compose down`(컨테이너와 네트워크만 지운다) 뒤 `up -d`, 그래도 붙지 않으면 `docker compose down -v`(볼륨까지 지운다) 뒤 `up -d`를 쳤다. serve 대역은 표(`probe_rows`)가 없으면 3으로 끝나게 해 두었다(진짜 `serve`가 "표의 판이 뒤처졌다"며 멈추는 자리).

아래는 항목 4만 다시 돌린 실행의 회차 여섯이다. 전체 실행의 회차 여섯도 같은 꼴이었고(초기화 중 전원 끊김 셋은 모두 반쯤 초기화된 꼴, `down` 갈래는 그 판에 없었다), 다른 점만 표 뒤에 적는다.

| 회차 | 끊긴 첫 삶의 마지막 기록 줄 | 첫 `up -d` | 40초 뒤 | 다시 `up -d` | `down` 뒤 `up -d` | `down -v` 뒤 `up -d` |
|---|---|---|---|---|---|---|
| 초기화 중, 데몬(2) | `database system is ready to accept connections`(초기화 끝 문구가 사건 1.20·1.18초 뒤) | 종료 1, `failed to connect to the docker API at unix:///var/run/docker.sock` | postgres `healthy`, migrate·serve `created` | 종료 0, 붙음 | (치지 않음) | (치지 않음) |
| 초기화 중, 전원, 반쯤 초기화된 꼴(2) | `running bootstrap script ... ok`(첫 삶 14줄, 초기화 끝 문구 없음) | 종료 137 | postgres `healthy`, migrate·serve `created`, `select 1`이 `database "agent_os" does not exist` | 종료 1, `service "migrate" didn't complete successfully: exit 2` | 종료 1, 같은 문구 | 종료 0, 붙음 |
| 초기화 중, 전원, 되풀이해 죽는 꼴(1) | `creating configuration files ... ok`(첫 삶 13줄, 초기화 끝 문구 없음) | 종료 137 | postgres 상태 확인 `starting`, `select 1`이 `the database system is in recovery mode` | 종료 1, 같은 문구 | 종료 1, 같은 문구 | 종료 0, 붙음 |
| migrate가 일하기 전, 데몬(1) | `database system is shut down`(초기화 끝 문구가 사건 0.79초 전) | 종료 1 | migrate `exited(143)`, serve `created` | 종료 0, 붙음 | (치지 않음) | (치지 않음) |

- 전체 실행에서는 초기화 끝 문구가 데몬 회차의 사건 1.23·1.38초 뒤였고, 전원 회차 셋의 마지막 줄이 모두 `running bootstrap script ... ok`였다.
- 첫 `up -d`의 종료 코드는 데몬 회차가 1(compose가 데몬의 소켓을 잃었다), 전원 회차가 137(dind를 죽이며 그 안에서 돌던 `docker exec`가 함께 죽었다)이다.
- 데몬이 다시 켜질 때 `created` 상태의 컨테이너는 띄우지 않았다. 그래서 `migrate`가 끝나기 전에 끊긴 배치는 `serve`가 뜨지 않은 채 머물렀고, 다시 `up -d`를 친 뒤에야 `migrate`, `serve` 차례로 떴다.
- 전원 끊김 뒤의 PostgreSQL은 `PostgreSQL Database directory appears to contain a database; Skipping initialization`을 찍고 초기화를 건너뛰었다. 공식 이미지의 진입 스크립트는 데이터 폴더에 `PG_VERSION` 파일이 있으면 이미 초기화된 것으로 본다(손으로 봤다, `postgres@sha256:b9f6…e553`의 `/usr/local/bin/docker-entrypoint.sh` 246줄을 `grep -n`). `pg_hba.conf`에 바깥 접속의 줄을 더하는 일(285줄)과 데이터베이스를 만드는 일(`docker_setup_db`, 217줄)은 초기화 뒤에 한다. 그래서 그 파일이 생긴 뒤에 끊긴 볼륨은 다시 띄워도 고쳐지지 않는다고 읽는다(어림. 끊는 때를 골라 내지 않았다).
- 꼴은 끊긴 첫 삶의 마지막 줄과 짝을 이뤘다. `running bootstrap script ... ok`인 다섯 회차는 모두 반쯤 초기화된 꼴, `creating configuration files ... ok`인 한 회차(와 앞의 판 실행의 한 회차, 손으로 봤다)는 되풀이해 죽는 꼴이었다. 앞의 것은 시스템 카탈로그까지 만든 뒤, 뒤의 것은 그 전에 끊겼다고 읽는다(어림).
- 첫 삶의 마지막 기록 줄은 기록에 닿은 마지막 줄이다. 전원 끊김은 진입 스크립트의 출력이 기록에 닿기 전에 죽였을 수 있어, 실제로 끊긴 자리는 그 줄보다 뒤일 수 있다(어림).
- 반쯤 초기화된 꼴에서 상태 확인(`pg_isready -h 127.0.0.1 -U agent_os -d agent_os`)은 데이터베이스가 없어도 `healthy`였다. 40초 동안 기록의 `database "agent_os" does not exist`가 20줄인 것은 2초 간격의 상태 확인이 찍은 것으로 본다(어림, 셈이 간격과 맞는다는 것만 봤다). 되풀이해 죽는 꼴은 상태 확인의 시작 유예(`start_period: 60s`) 안이라 40초 뒤 `starting`이었다.
- 갈래: `down`(볼륨은 남김) 뒤 `up -d`는 3/3 붙지 않았고 `down -v` 뒤 `up -d`는 같은 데몬에서 3/3 붙었다(전체 실행의 `down -v` 3/3까지 6/6). 그래서 붙지 않은 까닭은 남은 컨테이너나 네트워크, 데몬이나 이미지가 아니라 볼륨이다.

### 항목 5: 권한을 좁힌 postgres

`compose.narrow.yml`을 겹쳐 postgres 서비스에 `user: "999:999"`, `read_only: true`, `cap_drop: [ALL]`, `security_opt: [no-new-privileges:true]`, tmpfs `/var/run/postgresql`과 `/tmp`를 주었다. 컨테이너 안 `id`는 `uid=999(postgres) gid=999(postgres) groups=999(postgres)`, 루트에 쓰면 `touch: cannot touch '/probe-ro': Read-only file system`이었다. 이 모양으로 빈 볼륨에서 초기화하고 떴고, 데몬을 다시 켠 뒤 `database system was shut down at` 뒤 돌아와 넣어 둔 줄이 남았다. 서버 재시작, 전원 끊김, 초기화 중의 끊김은 이 모양으로 재지 않았다.

### 항목 0: 이미지 옮기기

dind 안의 엔진은 이미지를 받지 않고 바깥의 것을 `docker save`/`docker load`로 넣었다.

- digest 참조(`postgres@sha256:b9f6…e553`)로 내보내 넣으면 `Loaded image ID: sha256:c5a8d356…`만 찍히고 이름이 없다. 안쪽에서 그 digest로 찾으면 `Error response from daemon: No such image: postgres@sha256:b9f6b8ff03b62f3cfd9d9ba3fe56226a9991c79d3fb46fd46536263bf02be553`이다.
- 태그(`postgres:18`)로 내보내 넣으면 `Loaded image: postgres:18`이고, RepoDigests는 `postgres@sha256:c5a8d35629759fd9e45b90caffaf1deff00c501bc251df7c9d94de362250c17b`다. 바깥의 digest `b9f6…`과 다르다. 안의 `postgres --version`은 `postgres (PostgreSQL) 18.7 (Debian 18.7-1.pgdg13+2)`이다.
- 그래서 측정은 태그로 옮긴 이미지로 돈다. 바깥의 `postgres:18`이 그 digest와 같은 이미지(id `sha256:3cccc725…`)라는 것은 `run.py`가 dind를 띄우기 전에 확인한다.
- 바깥 엔진은 Docker Desktop의 것이고 안쪽은 dind의 것이라, 같은 이미지의 id가 바깥 `3cccc725…`, 안쪽 `c5a8d356…`로 달랐다. 이미지 저장 방식의 차이로 본다(어림, 저장 방식을 따로 보지 않았다).

## 파일

| 파일 | 무엇 |
|---|---|
| `run.py` | 측정 전체. 항목마다 무엇을 표지로 보는지는 독스트링과 회차의 이름에 있다 |
| `compose.yml` | dind 안에서 띄우는 배치. postgres, migrate 대역, serve 대역, watch |
| `compose.narrow.yml` | 항목 5가 겹치는 postgres의 좁힌 권한 |
| `serve.sh` | serve 대역과 watch. 시도마다 `probe-attempt …` 한 줄을 찍는다 |
| `migrate.sh` | migrate 대역. 표를 만들고 줄 `migrate`를 넣은 뒤 0으로 끝난다 |
| `crash.sh` | 항목 3의 KILL. 명령줄과 cgroup을 확인한 뒤에만 보낸다 |
| `supervise.sh` | dind의 첫 프로세스. dockerd를 띄우고, 끝나면 다시 띄우며 횟수를 센다 |
| `pyrightconfig.json` | 이 폴더를 pyright strict로 보는 설정 |

## 다시 돌리기

저장소 루트에서 친다.

```sh
uv run python .scratch/postgres-foundation/probes/restart_recover/run.py
```

- 전체 실행은 약 23분, 항목 4만 돌린 실행은 약 18분 걸렸다. `--sections 0,1,2,3,4,5`로 항목을, `--rounds`로 항목 1·2·3의 되풀이 횟수(기본 3)를 고른다. `--work <폴더>`를 주면 원본 출력(`raw.log`, 컨테이너 기록과 명령의 출력 전부)을 그 아래에 둔다. 주지 않으면 시스템 임시 폴더다.
- 필요한 것: `--privileged` 컨테이너를 띄울 수 있는 Docker(이 측정은 Docker Desktop의 리눅스 엔진), 이 PC에 받아 둔 이미지 둘(`docker:29.9.2-dind`와 `postgres@sha256:b9f6b8ff03b62f3cfd9d9ba3fe56226a9991c79d3fb46fd46536263bf02be553`, 그리고 같은 이미지를 가리키는 태그 `postgres:18`). 없으면 받지 않고 멈춘다. LLM은 부르지 않는다.
- 하는 일: 이름이 `pgf-recover-dind-<무작위 6자>`인 dind 컨테이너와 `pgf-recover-data-<같은 6자>` 볼륨을 라벨 `pgf-recover-probe=<같은 6자>`와 함께 만들고, 끝나면 그 라벨 값이 맞는 것만 지운다. 호스트 포트를 열지 않는다. 비밀번호(`probe-only`)는 측정용 고정 값이고 그 dind 안에서만 쓰인다.
- 측정이 아닌 회차가 하나라도 있으면 종료 코드가 1이다. 앞 회차의 것이 안쪽 엔진에 남으면 그 뒤의 회차는 모두 측정 아님으로 센다.
- `--reuse`는 떠 있는 dind를 다시 쓰고 `--keep`은 끝나도 지우지 않는다. 고치는 동안 쓰는 것이고, 결과는 둘 없이 낸다.
- 타입 검사: `uv run pyright -p .scratch/postgres-foundation/probes/restart_recover`. 린트: `uv run ruff check .scratch/postgres-foundation/probes/restart_recover`, `uv run ruff format --check .scratch/postgres-foundation/probes/restart_recover`.

## 환경

| 무엇 | 값 | 어떻게 봤나 |
|---|---|---|
| 날짜 | 2026-11-18 | |
| 호스트 | Windows 10 Home 10.0.19045 | 세션 환경 정보 |
| 바깥 Docker | Docker Desktop 4.97.0 (244584), 엔진 29.9.2 | 프로브가 찍는다 |
| dind | `docker:29.9.2-dind`(`docker@sha256:9e79b879b177fbd72c34376a3dd3d91747da5db49e1f560f76aea59561471977`) | 프로브가 찍는다 |
| 안쪽 엔진 | Engine 29.9.2, Compose 5.6.1, Alpine Linux v3.24(containerized), 커널 6.18.58.1-microsoft-standard-WSL2, 저장 드라이버 overlayfs, cgroup v2, x86_64 | 프로브가 찍는다 |
| PostgreSQL | `postgres:18`(바깥 digest `b9f6…e553`), 18.7 (Debian 18.7-1.pgdg13+2) | 프로브가 찍는다 |
| 파이썬 | 3.12.10 | 손으로 봤다(`uv run python --version`) |
| 부하 | 측정하는 동안 같은 Docker 데몬에서 다른 세션의 컨테이너가 함께 돌았다 | 손으로 봤다 |

## 재지 못한 것

- 진짜 리눅스 서버. dind는 Docker Desktop의 가상 머신 위 컨테이너라, 서버를 다시 켜는 갈래에는 systemd가 `docker.service`와 containerd를 띄우는 차례, 커널이 다시 뜨는 것, 디스크 검사가 없다. 전원 끊김도 dind 안의 프로세스를 한꺼번에 KILL한 것일 뿐 가상 머신의 커널은 살아 있어, 디스크에 아직 쓰지 않은 쓰기 버퍼가 날아가는 일이 없다. 진짜 전원 끊김에서 볼륨이 더 나빠지는지, PostgreSQL의 복구가 더 걸리는지는 모른다.
- 진짜 `serve`와 `agent-os migrate`. 대역은 psql로 시도하고, 진짜는 asyncpg로 접속하며 표의 판을 견준다. 대역의 다시 시도 간격(0.5초)과 시도의 제한 시간도 명세가 정할 값이 아니다.
- 큰 데이터베이스의 복구 시간. 표는 줄 몇 개이거나 150만 줄 하나였다. 복구는 마지막 체크포인트 뒤에 쌓인 WAL에 따라 길어지므로 실제 운영의 시간은 여기 값보다 길 수 있다(어림).
- 다른 기기의 디스크 속도, live-restore를 켠 데몬, rootless Docker, Podman.
- 권한을 좁힌 postgres의 서버 재시작, 전원 끊김, 초기화 중의 끊김.
- 초기화가 끊기는 자리마다의 결과. 끊는 때를 "postgres 컨테이너가 돌기 시작한 직후" 하나로만 냈고, 꼴이 회차마다 갈렸다(위 항목 4). `initdb`가 끝난 뒤 진입 스크립트가 데이터베이스를 만드는 도중처럼 다른 자리에서 끊긴 경우는 골라 내지 못했다.
- 문구 `in recovery mode`, `password authentication failed`와, 꺼지는 동안의 거절(`the database system is shutting down`)을 대역이 받는 경우.
- 끊긴 초기화의 볼륨을 고치는 다른 길(데이터 폴더만 비우기 등). `down -v`만 쟀다.
- 시간의 분포는 실행 둘에서 사건마다 회차 18개다. 앞의 실행에서만 3~5초의 회차가 났듯 실행마다 갈린다.

## 남긴 것

- 컨테이너와 볼륨: 없다. 끝에서 `docker ps -a --filter label=pgf-recover-probe`와 `docker volume ls --filter label=pgf-recover-probe`가 비었다(손으로 봤다).
- 이미지: 받아 둔 둘을 그대로 썼고 새로 받거나 지은 것이 없다. 안쪽으로 옮긴 사본은 dind의 볼륨과 함께 지워졌다.
- 원본 출력(`raw.log`)은 측정한 세션의 임시 폴더에 있고 저장소에 들지 않는다.
