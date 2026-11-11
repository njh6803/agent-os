# release-image netns 프로브

`release-image` 설계 인터뷰의 첫 후보 배치를 본 프로브다. 후보는 프로세스마다 컨테이너를 따로 두되, 모든 컨테이너가 프록시(nginx) 컨테이너의 네트워크 이름공간을 함께 쓰는 것이다(compose의 `network_mode: "service:proxy"`). 네 프로세스는 `127.0.0.1`·`::1`이 아닌 주소에 묶이면 시작을 거부하므로, 프록시를 그 루프백 안으로 들이는 배치다. 항목 7은 뒤에 받은 지시로, 이름공간의 주인을 프록시가 아니라 아무 일도 하지 않는 전용 컨테이너(`holder`)로 두는 배치를 같은 방식으로 본다. 여기서는 결정하지 않고 본 것만 적는다. 규약은 `docs/agents/issue-tracker.md`의 "프로브와 근거"다.

근거의 종류. 아래 "결과"의 줄은 따로 적지 않은 한 `run.py`(이 폴더)가 다시 내는 것이고, 2026-11-11에 마지막 판의 스크립트로 전체(항목 1~7)를 한 번 돌린 출력에서 옮겼다(71회차 모두 표지를 봤고 종료 코드 0). 그 앞에 스크립트를 고쳐 가며 돌린 실행이 항목 1~6은 항목마다 세 번 이상, 항목 7은 한 번 더 있었고 닿는지의 결과는 같았다. 실행마다 달랐던 것(항목 3의 오류 문구, 띄운 직후의 첫 응답)은 그 자리에 적었다. 손으로 본 것은 그 명령과 함께, 재지 않은 것은 어림이라고 적었다.

## 파일

| 파일 | 무엇 |
|---|---|
| `run.py` | 측정 전체. 항목마다 무엇을 표지로 보는지는 독스트링에 있다 |
| `compose.shared.yml` | 이름공간 공유 배치(항목 1·3·4·5) |
| `compose.bridge.yml` | 이름공간을 함께 쓰지 않는 대조군(항목 2) |
| `compose.ports-on-app.yml` | 이름공간을 빌린 서비스에 `ports`를 직접 준 파일(항목 4) |
| `compose.depends.yml`, `compose.depends-restart.yml`, `compose.restart-policy.yml` | 항목 3의 덧씌움(`depends_on` 짧은 꼴, `restart: true`, 재시작 정책) |
| `compose.loopback6.yml`, `nginx.loopback6.conf` | 덧붙인 항목 6(`::1`에만 묶인 서버) |
| `nginx.conf` | 프록시 설정(둘째 `listen`, `limit_req`, 접근 기록 형식) |
| `compose.holder.yml`, `compose.holder-restart-policy.yml` | 항목 7의 배치(주인이 `holder`)와 그 재시작 정책 덧씌움 |
| `nginx.holder.conf` | 항목 7의 프록시 설정. `nginx.conf`에서 빈도 제한을 빼고, 다시 읽기 갈래가 쓰는 `include` 한 줄을 더했다 |
| `compose.reload-conf.yml` | 항목 7.5에서 주인이 proxy인 배치의 nginx 설정을 `nginx.holder.conf`로 바꾸는 덧씌움 |
| `pyrightconfig.json` | `run.py`의 타입 검사 설정(아래 "다시 돌리기") |

## 다시 돌리기

저장소 루트에서 친다.

```sh
uv run python .scratch/release-image/probes/netns/run.py
```

- 필요한 것: 도는 Docker 데몬과 compose, 로컬에 이미 있는 이미지 둘, 비어 있는 호스트 포트 39411~39417. 이미지는 받지 않는다(`pull_policy: never`). 다른 판으로 보려면 `--nginx-image`, `--python-image`에 로컬에 있는 참조를 준다.
- 하는 일: compose 프로젝트 `release-image-netns-probe` 하나만 만들고, 갈래마다 그리고 끝에서 `down -v --remove-orphans`로 지운다. 호스트 포트는 `127.0.0.1`에만 연다. 모든 명령의 원본 출력은 `--work`(없으면 시스템 임시 폴더) 아래 `raw.log`에 남는다.
- `--sections 1,4,5`처럼 항목을 고를 수 있다(1~7). 측정이 아닌 회차(표지를 보지 못한 회차)가 하나라도 있으면 종료 코드가 1이다.
- Docker 데몬은 건드리지 않는다. 컨테이너를 다시 시작하거나 죽이는 명령(`docker restart`, `docker kill`)은 이 프로젝트의 라벨로 찾은 컨테이너에만 친다.
- 타입 검사: `uv run pyright -p .scratch/release-image/probes/netns --outputjson`. 이 폴더는 저장소의 pyright 범위(`pyproject.toml`의 `include`는 `src`, `tests`, `tools`) 밖이고 점 디렉터리 아래라, 저장소 루트에서 파일 경로만 주면 분석하지 않고 "0 errors"를 낸다(`summary.filesAnalyzed`가 0). 그래서 이 폴더의 `pyrightconfig.json`(strict)을 `-p`로 준다.
- 걸린 시간: 실행마다 크게 달랐다(손으로 봤다. 각 실행의 `raw.log`에 찍힌 명령의 시각). 마지막 전체 실행(항목 1~7, 71회차)은 18분 45초였고(12:05:39~12:24:24) 그 가운데 항목 1~6이 약 6분, 항목 7이 약 12분 30초였다. 그 앞에 항목 7만 돌린 실행(23회차)은 3분이었고(12:01:30~12:04:29), 항목 1~6만의 전체 실행 둘은 4분 47초와 8분 2초였다. 마지막 실행의 뒤쪽에서는 docker 명령 하나하나가 느렸고 까닭은 보지 않았다. 10분을 넘을 수 있다고 보고 돌린다.

## 환경

| 무엇 | 값 | 어떻게 봤나 |
|---|---|---|
| 날짜 | 2026-11-11 | |
| 호스트 | Windows 10 Home 10.0.19045 | 손으로 봤다(PowerShell `[System.Environment]::OSVersion.VersionString`, `(Get-CimInstance Win32_OperatingSystem).Caption`) |
| Docker | Docker Desktop 4.97.0 (244584). 엔진 29.9.2, 클라이언트 29.9.2, 커널 `6.18.58.1-microsoft-standard-WSL2` | `run.py`가 첫머리에 찍는다(`docker version`, `docker info`). 엔진이 linux/amd64, 클라이언트가 windows/amd64, 컨텍스트가 `desktop-linux`인 것은 손으로 봤다(`docker version`) |
| Compose | v5.6.1 | `run.py`가 찍는다(`docker compose version`) |
| podman | 없다 | 손으로 봤다(Git Bash에서 `podman --version`이 `command not found`, 종료 127) |
| nginx 이미지 | `nginx@sha256:c8497b180665e631ec92a5091125bec5b214f0e2b99409e30653a125b37557da`. 로컬 태그 `nginx:alpine`, nginx 1.31.6 | `run.py`가 찍는다(`docker image inspect`, 컨테이너 안의 `nginx -v`) |
| python 이미지 | `python@sha256:fd95fa221297a88e1cf49c55ec1828edd7c5a428187e67b5d1805692d11588db`. 로컬 태그 `python:3.12.10-slim-bookworm`, Python 3.12.10 | 같다(`python --version`) |

이미지는 이 PC에 이미 있던 것만 썼다. nginx는 판을 고정한 태그(1.28 계열 등)가 로컬에 없어 `nginx:alpine`(nginx 1.31.6)을 digest로 고정해 썼다. 이미지에 넣을 nginx 판이 정해지면 그 판으로 다시 돈다.

## 결과

### 1. 이름공간 공유 배치가 동작하는가

동작한다.

| 갈래 | 본 것 |
|---|---|
| 호스트 → `127.0.0.1:39411`(proxy의 8080) → `proxy_pass http://127.0.0.1:8000` → 루프백에만 묶인 app | 닿는다(200, 본문이 app의 표지). 표지로 app의 `NetworkMode`가 `container:<proxy id>`이고 두 컨테이너의 `/proc/self/ns/net`이 같은 값임을 봤다. 띄운 직후의 첫 요청은 실행에 따라 502이거나(app의 서버가 서기 전) 200이었다 |
| 같은 이름공간의 다른 컨테이너(admin)에서 `127.0.0.1:8000` | app이 답한다 |
| 같은 이름공간에서 proxy의 eth0 주소(`172.20.0.x`)의 8000 | 거부(`ConnectionRefusedError`). 양성 대조인 같은 주소의 8080(nginx)은 닿는다 |

### 2. 이름공간을 함께 쓰지 않으면 닿지 않는가(대조군)

두 길 모두 닿지 않는다.

| 갈래 | 본 것 |
|---|---|
| 양성 대조: `0.0.0.0:8000`에 묶은 app-open을 호스트에서 발행 포트로 | 닿는다 |
| 양성 대조: app-open을 다른 컨테이너(client)에서 `app-open:8000`으로 | 닿는다 |
| (가) 루프백에만 묶인 app을 호스트에서 발행 포트(`127.0.0.1:39414`)로 | 닿지 않는다. TCP 연결은 맺어지고 응답 없이 끊긴다(`RemoteDisconnected`). app은 자기 컨테이너 안의 `127.0.0.1:8000`에서는 답한다 |
| (나) 같은 app을 client에서 `http://app:8000`으로 | 닿지 않는다(`ConnectionRefusedError`. 이름 풀이는 됐다). 두 컨테이너의 `/proc/self/ns/net`은 다른 값이다 |

### 3. 프록시 컨테이너를 다시 띄우면

갈래마다 배치를 새로 띄우고 조작 하나를 한 뒤 공개 포트로 app에 닿는지 8초까지 봤다. "502"인 칸은 모두 같은 모양이었다. proxy와 app의 `/proc/self/ns/net`이 서로 다른 값이 됐고, app은 자기 루프백에서 답했고, nginx 오류 기록에 `connect() failed (111: Connection refused)`가 있었다. app이 죽은 것이 아니라 옛 이름공간에 남은 것이다.

| 조작 | `depends_on` 없음 | `depends_on` 짧은 꼴 | `depends_on`의 `restart: true` |
|---|---|---|---|
| `docker compose config`가 푼 app의 `depends_on` | `proxy`: `service_started`, `restart: true`(적지 않았는데 들어 있다) | `proxy`: `service_started`(`restart` 없음) | `proxy`: `service_started`, `restart: true` |
| `docker compose restart proxy` | 닿는다. compose가 app도 다시 시작했다 | 502. app은 그대로다. `restart app`으로 회복 | 닿는다. app도 다시 시작됐다 |
| `docker compose up -d --force-recreate proxy` | 502. app은 그대로다. `restart app`은 실패하고(아래) app을 멈춘 채 둔다. 이어서 친 `up -d`가 app을 다시 만들어 회복. `restart app` 없이 바로 `up -d`를 쳐도(app이 옛 이름공간에서 도는 채로) app을 다시 만들어 회복 | 같다. 바로 `up -d`를 치는 갈래는 돌리지 않았다 | 같다. 바로 `up -d`를 치는 갈래는 돌리지 않았다 |
| proxy의 환경 값을 바꾼 뒤 `docker compose up -d` | 닿는다. proxy와 app이 모두 다시 만들어졌다 | 같다 | 같다 |
| `docker compose restart`(서비스 이름 없이) | 닿는다. 둘 다 다시 시작됐다 | 502, 명령이 종료 1. app이 멈춘 채 남았다(아래). `restart app`으로 회복 | 닿는다 |
| `docker restart <proxy 컨테이너>`(compose를 거치지 않고) | 502. app은 그대로다. `restart app`으로 회복 | 돌리지 않았다 | 502. 같다 |
| 재시작 정책(`restart: always`)을 두고 proxy 안에서 `nginx -s stop`. Docker 데몬이 proxy를 다시 띄운다 | 502. app은 그대로다. `restart app`으로 회복 | 돌리지 않았다 | 502. 같다 |

오류 문구(원본 출력에서 옮겼다).

- `up -d --force-recreate proxy` 뒤의 `restart app`: `Cannot restart container …: joining network namespace of container: No such container: <id>`. 그 id는 다시 만들기 전 proxy 컨테이너의 것이고 app의 `NetworkMode`가 `container:<그 id>`였다(손으로 봤다. 한 실행의 `raw.log`에서 오류의 id와 그 앞 `docker inspect` 출력을 맞대 봤다).
- `depends_on` 짧은 꼴의 이름 없는 `restart`: 다섯 실행에서 다섯 번 모두 종료 1이었고 app이 멈춘 채 남았다. 문구는 두 가지였다. 세 번은(마지막 실행 포함) `cannot join network namespace of a non running container: container release-image-netns-probe-proxy-1 is exited`, 두 번은 `OCI runtime create failed: … namespace path: lstat /proc/<pid>/ns/net: no such file or directory`. proxy가 다시 뜨는 도중에 app을 다시 시작하려다 난 것으로 읽었다(어림. 두 컨테이너가 다시 시작되는 차례를 따로 재지 않았다).

### 4. 바깥에 공개하지 않는 프로세스에 운영자가 닿는 길

| 갈래 | 본 것 |
|---|---|
| 이름공간을 빌린 app에 `ports`를 직접 준 파일로 `up -d` | 거부(종료 1). Docker 데몬이 `conflicting options: port publishing and the container type network mode`로 거부한다. compose가 파일을 읽는 단계에서 막는 것이 아니라, 네트워크와 proxy 컨테이너를 만든 뒤 app을 만들 때 난다(만든 차례는 `raw.log`에서 손으로 봤다) |
| proxy 서비스가 이름공간의 8000을 대신 발행(`127.0.0.1:39413:8000`) | 닿지 않는다(`RemoteDisconnected`). 항목 2의 (가)와 같은 모양이다 |
| nginx에 둘째 `listen 8081`을 두어 admin(`127.0.0.1:8001`)으로 넘기고 `127.0.0.1:39412:8081`로 발행 | 닿는다(200, 본문이 admin의 표지) |
| 그 포트에 이 호스트의 다른 주소로 TCP 연결 | `127.0.0.1`은 연결되고, 루프백이 아닌 IPv4 주소 둘(`172.29.x.x`, `192.168.x.x`)과 `::1`은 모두 `ConnectionRefusedError`. 이 호스트 안에서 건 연결이다 |
| 그 포트를 듣는 호스트 소켓(`netstat -ano`) | 로컬 주소가 `127.0.0.1` 하나다 |

### 5. 빈도 제한

| 갈래 | 본 것 |
|---|---|
| `limit_req`(분당 2회, burst 없음)의 한도를 넘긴 요청, 기본값 | 연달아 다섯 번의 상태가 200, 503, 503, 503, 503. 거부 넷 모두 nginx 오류 기록에 그 구역의 `limiting requests, excess: …` 줄이 있다 |
| 같은 것에 `limit_req_status 429` | 200, 429, 429, 429, 429. 거부 넷 모두 같은 줄이 있다 |
| 호스트에서 발행 포트로 온 요청의 `$remote_addr` | `172.20.0.1`. compose 네트워크(`172.20.0.0/16`)의 게이트웨이 주소다. 호스트의 주소가 아니다 |
| 같은 compose 네트워크의 다른 컨테이너(peer)에서 `proxy:8080`으로 온 요청의 `$remote_addr` | peer 자신의 주소(`172.20.0.x`) |
| 호스트가 한도를 넘긴 구역에 peer가 요청 | 호스트 둘째 429, peer 첫째 200, peer 둘째 429, 그 뒤 호스트 429. 주소가 다르면 따로 센다 |

### 6. `::1`에만 묶인 서버(지시문에 없는 덧붙임)

네 프로세스의 규칙이 `::1`도 받으므로 같은 배치에서 IPv6 루프백도 봤다.

| 갈래 | 본 것 |
|---|---|
| proxy의 이름공간을 빌린 서버가 `::1:8002`에만 묶이고 nginx가 `proxy_pass http://[::1]:8002`로 넘긴다. 호스트에서 `127.0.0.1:39417`로 요청 | 닿는다(200, 본문이 그 서버의 표지). 띄운 직후의 첫 요청은 502였다. 서버 컨테이너는 돌고 있고 자기 `::1`에서 답한다 |

### 7. 이름공간의 주인을 `holder`로 두는 배치(뒤에 받은 지시)

`holder`는 `sleep infinity` 하나만 도는 컨테이너다(python 이미지, `init: true`). 호스트 포트 둘(`127.0.0.1:39411:8080`, `127.0.0.1:39412:8081`)을 `holder`에 발행하고, `proxy`(nginx)와 `app`과 `admin`이 모두 `network_mode: "service:holder"`로 빌린다. `depends_on`은 적지 않았다. `docker compose config`가 푼 모델에는 빌린 셋 모두에 `depends_on`의 `holder`: `service_started`, `required: true`, `restart: true`가 들어 있다.

아래 표에서 "그대로"는 같은 컨테이너 id에 같은 `State.StartedAt`, "다시 시작됨"은 같은 id에 새 `StartedAt`, "다시 만들어짐"은 새 id다. "닿는다"는 공개 포트로 app에, 관리 포트로 admin에 모두 닿은 것이다(8초까지 봤다).

#### 7.1 배치가 동작하는가

동작한다.

| 갈래 | 본 것 |
|---|---|
| 호스트 → `127.0.0.1:39411`(holder의 8080) → nginx → 루프백에만 묶인 app | 닿는다(200, 본문이 app의 표지) |
| 호스트 → `127.0.0.1:39412`(holder의 8081) → nginx의 둘째 `listen` → admin | 닿는다(200, 본문이 admin의 표지) |
| 표지 | 빌린 셋의 `NetworkMode`가 `container:<holder id>`이고, 네 컨테이너의 `/proc/self/ns/net`이 같은 값이다. 발행 포트는 holder의 `docker inspect`에 `127.0.0.1`로만 보인다 |

#### 7.2 proxy를 다시 띄우면

여섯 조작 모두 닿는다. 이름 없는 `restart`를 뺀 다섯에서 app은 그대로였다.

| 조작 | 닿는가 | holder | proxy | app | admin |
|---|---|---|---|---|---|
| `docker compose restart proxy` | 닿는다 | 그대로 | 다시 시작됨 | 그대로 | 그대로 |
| `docker compose up -d --force-recreate proxy` | 닿는다 | 그대로 | 다시 만들어짐 | 그대로 | 그대로 |
| proxy의 환경 값을 바꾼 뒤 `docker compose up -d` | 닿는다 | 그대로 | 다시 만들어짐 | 그대로 | 그대로 |
| `docker compose restart`(서비스 이름 없이) | 닿는다 | 다시 시작됨 | 다시 시작됨 | 다시 시작됨 | 다시 시작됨 |
| `docker restart <proxy 컨테이너>`(compose를 거치지 않고) | 닿는다 | 그대로 | 다시 시작됨 | 그대로 | 그대로 |
| 재시작 정책(`restart: always`)을 두고 proxy 안에서 `nginx -s stop` | 닿는다 | 그대로 | 다시 시작됨(`RestartCount` 0→1) | 그대로 | 그대로 |

#### 7.3 holder를 다시 띄우면

compose가 holder를 다시 시작하는 갈래 하나만 닿고, 나머지 넷은 닿지 않는다. 닿지 않은 칸은 모두 같은 모양이었다. proxy와 app과 admin은 그대로 돌면서 옛 이름공간에 남았고(셋의 `/proc/self/ns/net`은 조작 전의 값, holder는 새 값이거나 멈춤), 셋끼리는 닿았다(admin 컨테이너 안에서 `127.0.0.1:8080`의 nginx를 거쳐 app의 답). 항목 3의 502와 달리 호스트에서 건 요청은 nginx에 닿지도 못한다.

| 조작 | 닿는가 | holder | proxy·app·admin | 회복 |
|---|---|---|---|---|
| `docker compose restart holder` | 닿는다 | 다시 시작됨 | compose가 셋도 다시 시작했다 | 필요 없다 |
| `docker restart <holder 컨테이너>`(compose를 거치지 않고) | 닿지 않는다(`RemoteDisconnected`) | 다시 시작됨 | 그대로 | `docker compose up -d`는 아무것도 바꾸지 않아 회복되지 않는다. 이어서 친 `docker compose restart proxy app admin`으로 회복 |
| 재시작 정책을 두고 `docker kill <holder 컨테이너>` | 닿지 않는다(`ConnectionRefusedError`) | 멈춘 채 남았다(`RestartCount` 0→0). Docker가 다시 띄우지 않았다 | 그대로 | `docker compose up -d`가 holder만 다시 시작하고 셋은 그대로라 회복되지 않는다(`RemoteDisconnected`). 이어서 친 `docker compose restart proxy app admin`으로 회복 |
| 재시작 정책을 두고 holder의 프로세스가 스스로 끝남(양성 대조. holder 안에서 `kill -TERM 1`) | 닿지 않는다(`RemoteDisconnected`) | Docker가 다시 띄웠다(`RestartCount` 0→1) | 그대로 | `docker compose up -d`는 아무것도 바꾸지 않는다. `docker compose restart proxy app admin`으로 회복 |
| `docker compose up -d --force-recreate holder` | 닿지 않는다(`RemoteDisconnected`) | 다시 만들어짐 | 그대로 | `docker compose up -d`가 셋을 다시 만들어 회복 |

#### 7.4 app 하나만 다시 만들면

| 조작 | 닿는가 | holder | proxy | app | admin |
|---|---|---|---|---|---|
| `docker compose up -d --force-recreate app` | 닿는다. admin은 두 실행 모두 처음부터 200이었고, app은 앞의 실행에서 502 뒤 200(새 app의 서버가 서기 전), 마지막 실행에서 처음부터 200이었다 | 그대로 | 그대로 | 다시 만들어짐 | 그대로 |
| app의 환경 값을 바꾼 뒤 `docker compose up -d`(이미지 하나만 바꾸는 장면에 가깝게) | 같다 | 그대로 | 그대로 | 다시 만들어짐 | 그대로 |

#### 7.5 `nginx -s reload`

proxy 컨테이너 안의 설정 폴더(`nginx.holder.conf`의 `include`가 들이는 `/tmp/probe-extra/`)에 `location = /reloaded` 하나를 써 넣고 `docker compose exec proxy nginx -s reload`를 쳤다.

| 배치 | 본 것 |
|---|---|
| holder 배치 | `/reloaded`가 다시 읽기 전 404(app으로 넘어갔다), 뒤 200(새 설정의 답). app과 admin에 닿는다. 네 컨테이너 모두 그대로(proxy의 `StartedAt`이 같다) |
| 주인이 proxy인 배치(`compose.shared.yml`) | 같다. 다시 읽기 전 404, 뒤 200. app에 닿는다. proxy와 app 모두 그대로 |

## 해석과 그 갈래

- 항목 2에서 app이 닿지 않는 까닭을 묶는 주소로 읽었다. 같은 배치에서 `0.0.0.0`에 묶은 app-open은 두 길 모두 닿았고(양성 대조), app은 자기 루프백에서 답했고, client의 오류는 이름 풀이 실패가 아니라 연결 거부였다. 포트 발행이 깨졌다, 이름이 풀리지 않는다, 서버가 서지 않았다는 세 해석이 이것으로 갈린다.
- 항목 3의 502를 "app이 옛 이름공간에 남았다"로 읽었다. 근거는 그 칸마다 본 세 관찰이다(위 문단). app이 죽었다는 해석은 app이 자기 루프백에서 답한 것으로, nginx가 아직 서지 않았다는 해석은 nginx가 502를 답하고 오류 기록에 상류 연결 거부를 남긴 것으로 갈린다.
- 항목 3에서 app을 함께 다시 시작한 것을 compose의 일로 읽었다. `config`가 푼 모델에 적지 않은 `depends_on`(`restart: true`)이 있고, 짧은 꼴을 적어 그 `restart`가 빠지면 같은 `restart proxy`에도 app이 그대로였고, compose를 거치지 않은 두 조작에서도 app이 그대로였다. Docker 데몬이 이름공간을 빌린 컨테이너를 스스로 다시 띄운다는 해석이 뒤의 둘로 갈린다. compose의 코드를 읽지는 않았다.
- 항목 5에서 `$remote_addr`가 게이트웨이인 것은 이 PC의 호스트에서 `127.0.0.1`로 건 요청 하나의 갈래에서 본 것이다. 다른 기기에서 온 요청이 어떻게 보이는지는 보지 않았다(포트를 `127.0.0.1`에만 열었다).
- 항목 7.2에서 proxy를 어떻게 다시 띄워도 닿은 것을 "이름공간의 주인이 proxy가 아니어서"로 읽었다. 같은 조작 여섯 가운데 셋(`up -d --force-recreate proxy`, `docker restart <proxy>`, 재시작 정책)이 주인이 proxy인 배치의 같은 판(`depends_on` 없음, 항목 3)에서는 502였다. 두 배치는 이미지와 서버와 조작이 같고 주인이 다르다. 다만 nginx 설정 파일도 다르고(빈도 제한이 없다), 항목 7에는 `depends_on` 짧은 꼴 갈래가 없다.
- 항목 7.3에서 닿지 않는 까닭을 "빌린 셋이 옛 이름공간에 남았다"로 읽었다. 그 칸마다 셋의 이름공간 값이 조작 전과 같고 holder의 것과 달랐으며, 셋끼리는 닿았다. 셋이 죽었다는 해석은 셋끼리 닿은 것으로 갈린다. 주인만 바뀌었을 뿐 항목 3과 같은 일이다. 주인이 다시 뜨면 빌린 쪽이 남는다.
- 항목 7.3에서 `docker kill` 뒤 holder가 멈춘 채 남은 것을, 재시작 정책이 걸려 있지 않아서가 아니라 `docker kill`이라서로 읽었다. 같은 덧씌움(`restart: always`)에서 holder의 프로세스가 스스로 끝난 갈래는 Docker가 다시 띄웠다(`RestartCount` 0→1). 사람이 멈춘 컨테이너는 정책이 다시 띄우지 않는다는 Docker 문서의 설명에 해당하는 것으로 보지만 문서를 다시 대 보지는 않았다(어림). 기다린 시간은 죽인 뒤 10초와 그 뒤 관찰에 든 시간이다.
- 항목 7.3에서 `docker compose up -d`가 회복하는 것은 holder가 다시 만들어진 갈래뿐이었다. holder가 같은 컨테이너로 다시 시작된 갈래에서는 `up -d`가 빌린 셋을 건드리지 않았다. compose가 무엇을 보고 다시 만드는지는 재지 않았다. 항목 3에서도 `up -d`는 proxy가 다시 만들어진 뒤에만 쳐 봤다.
- 항목 7.5의 다시 읽기는 컨테이너 안에 써 넣은 파일 하나로 봤다. 호스트에서 얹은 설정 파일을 고친 뒤의 다시 읽기는 보지 않았다.

## 결과를 본 뒤 바꾼 것

- 표지 하나를 좁혔다. 항목 4 첫 갈래(이름공간을 빌린 app에 `ports`)의 표지는 거부 문구에 `port`가 있는 것이었는데, `port`와 `network mode`가 함께 있는 것으로 바꿨다. 포트가 이미 쓰여 난 실패도 `port`를 들기 때문이다. 본 문구는 바꾸기 전에도 뒤에도 표지에 맞는다. 바꾼 뒤의 표지로 돈 실행 셋(`--sections 4` 하나와 전체 둘)에서 그 갈래는 모두 같은 거부 문구로 측정이 됐다. 나머지 표지는 바꾸지 않았다.
- 항목 3에 회복을 `up -d`부터 치는 갈래를 더했다. 그 앞의 실행들은 회복 명령을 `restart app`, `up -d` 차례로 쳐서, `up -d`를 실패한 `restart app`이 app을 멈춘 뒤에만 봤다. app이 아직 도는 채로 `up -d`만 쳐도 되는지는 그 차례로는 알 수 없어 `depends_on` 없음 갈래 하나에 더했고, 그 뒤의 전체 실행 둘에서 한 번씩 돌았다.
- 항목 3의 첫 실행에서 `restart proxy`가 app까지 다시 시작한 것을 보고, 그것이 compose의 일인지 Docker 데몬의 일인지 가르려고 `docker restart` 갈래와 `config`가 푼 `depends_on`을 찍는 줄을 더했다. 재시작 정책 갈래는 처음부터 있었다.
- 항목 3에서 닿는지 기다리는 창을 12초에서 8초로 줄였다. 창이 12초였던 첫 실행에서 닿은 회차는 모두 첫 응답이 200이었고, 닿지 않은 회차는 12초 내내 502였다. 8초로 돈 실행에서 닿은 회차는 첫 응답이 200이거나 502 뒤 곧 200이었다.
- 항목 6은 항목 1~5의 결과를 본 뒤 더했다.
- 항목 7은 항목 1~6의 결과를 보고한 뒤 받은 지시로 더했다. 갈래와 표지는 돌리기 전에 정했고(`docker kill`이 다시 띄워지지 않을 수 있다고 보고 프로세스가 스스로 끝나는 양성 대조를 미리 뒀다), 첫 실행 뒤 바꾸지 않았다. 지시문에 없던 갈래는 넷이다. `docker compose restart holder`, 그 양성 대조, app의 환경 값을 바꾼 뒤 `up -d`, 주인이 proxy인 배치의 `nginx -s reload`.
- 항목 7을 더하면서 항목 1~6이 함께 쓰는 자리를 고쳤다. docker와 compose의 JSON을 읽는 자리를 타입을 좁혀 읽게 바꿨고(모양이 기대와 다르면 예외 대신 빈 값이 나오고, 그 값으로는 표지가 서지 않는다), proxy를 다시 시작시키는 도움 함수 둘을 서비스 이름을 받게 넓혔다. 판정과 표지는 바꾸지 않았다. 고친 뒤 전체를 다시 돌렸고 항목 1~6의 닿는지의 결과는 그 앞의 실행과 같았다.

## 재지 못한 것

- 다른 기기에서 오는 요청. 실제 클라이언트 주소가 `$remote_addr`에 보이는지, 관리 포트가 다른 기기에서 닿지 않는지. 호스트 포트를 `127.0.0.1`에만 열어, `0.0.0.0`에 열면 다른 주소로 닿는다는 양성 대조도 두지 않았다.
- Docker 데몬이나 호스트를 다시 켠 뒤 컨테이너가 서는 차례와 그때 빌린 컨테이너가 새 이름공간에 붙는지. 두 배치 모두 보지 않았다(이 PC의 다른 컨테이너가 죽으므로 데몬을 다시 시작하지 않았다). holder 배치에서 holder가 다시 뜨는 길 가운데 가장 흔할 이 길이 비어 있다.
- 리눅스 호스트의 Docker Engine과 podman(이 PC에 없다). `network_mode: "service:…"`를 podman이 어떻게 받는지도 보지 않았다.
- app을 다시 시작하는 데 드는 시간과 그동안 끊기는 요청. 표의 "app도 다시 시작됐다"는 proxy를 건드릴 때마다 app 프로세스가 내려갔다 올라온다는 뜻이다.
- 호스트에서 얹은 nginx 설정 파일을 고친 뒤의 `nginx -s reload`. 항목 7.5는 컨테이너 안에 써 넣은 파일로 봤다.
- holder 배치에 `depends_on`을 짧은 꼴로 적은 판. 항목 3에서는 짧은 꼴이 `restart: true`를 빼서 compose의 재시작이 깨졌다. holder 배치에서도 `restart holder`와 이름 없는 `restart`가 그렇게 되는지는 보지 않았다.
- holder가 죽는 다른 길(메모리 부족으로 죽는 것, `docker stop` 뒤 `docker start`, 호스트에서 프로세스를 죽이는 것)과, holder에 재시작 정책을 두지 않은 판에서 holder의 프로세스가 끝나는 것.
- holder 배치에서 빌린 셋을 다시 시작하는 동안 끊기는 요청과 그 시간.
- 되풀이. 한 실행은 조작마다 한 번만 한다. 항목 3의 compose 조작과 재시작 정책 갈래는 다섯 실행에서 한 번씩 다섯 번, `docker restart` 갈래는 네 번, 회복을 `up -d`부터 치는 갈래는 두 번 했고 닿는지의 결과는 매번 같았다. 항목 7은 두 실행에서 한 번씩 두 번 했고 결과가 같았다. 차례에 달린 조작(이름 없는 `restart`)이 늘 같은 결과인지는 이 횟수로는 말할 수 없다.

## 이 PC라서 리눅스 서버와 다를 수 있는 것

모두 어림이다. 이 프로브는 Windows의 Docker Desktop(WSL2)에서만 돌았다.

- 발행 포트로 온 요청의 `$remote_addr`. 여기서는 게이트웨이 주소였다. Docker Desktop은 호스트의 포트를 받아 VM 안으로 넘기므로 nginx가 보는 상대가 실제 클라이언트가 아니다. 리눅스의 Docker Engine은 바깥에서 온 연결을 주소 변환만 해서 넘겨 실제 주소가 보이는 것으로 알려져 있지만, 호스트 자신이 건 연결과 rootless 모드는 다를 수 있다. 접속 주소별 한도를 쓰려면 배포할 환경에서 이 갈래를 다시 본다.
- `127.0.0.1`에만 연 포트가 다른 인터페이스로 닿지 않는 것. 여기서 호스트 쪽 소켓을 듣는 것은 Docker Desktop의 프로세스다. 리눅스에서는 Docker가 방화벽 규칙과 자신의 프록시로 처리해 길이 다르다.
- 호스트에서 루프백에만 묶인 컨테이너 포트로 걸었을 때의 모양(여기서는 연결이 맺어진 뒤 끊겼다). 리눅스에서는 연결 거부로 보일 수 있다. 항목 7.3에서 holder가 새 이름공간으로 다시 뜬 뒤의 모양(`RemoteDisconnected`)과 holder가 멈춘 동안의 모양(`ConnectionRefusedError`)도 같은 까닭으로 다를 수 있다.
- 이름공간 공유 자체(항목 1)와 compose의 `depends_on` 처리(항목 3)는 리눅스 커널과 compose의 동작이라 같을 것으로 보지만, 판이 다르면 다시 본다. 여기서 쓴 Compose는 v5.6.1이다.
