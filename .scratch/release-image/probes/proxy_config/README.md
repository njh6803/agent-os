# proxy_config — 명세가 고른 nginx 프록시 설정 조합을 잰다

release-image 명세(`.scratch/release-image/spec.md` 의 "프록시가 뒷단을 다시 찾는 길"과 토큰 끝점의 빈도
제한 문단)가 고른 nginx 설정 조합이 실제로 맞물리는지 잰다. 결정은 하지 않는다. 잴 설정은
`nginx/proxy.conf` 이고, 시제품 `bridge_edge/nginx/edge.conf` 에서 셋을 바꿨다.

1. 뒷단은 공유 메모리 영역(`zone`)을 둔 `upstream` 묶음이고, `server <이름>:<포트> resolve;` 와
   `resolver 127.0.0.11 valid=5s ipv6=off;` 로 Docker 내장 DNS 에서 이름을 다시 푼다.
2. 모든 `proxy_pass` 는 upstream 이름에 URI 를 붙인 꼴이다(예: `proxy_pass http://up_serve/end-user/;`).
3. 토큰 끝점의 정규식 `location` 을 없앴다. http 문맥의 `map $uri $portal_token_key` 가 토큰 끝점
   (`^/portal/sites/[^/]+/token$`)이면 `$binary_remote_addr`, 아니면 빈 값을 열쇠로 내고,
   `limit_req zone=portal_token burst=10 nodelay;` 는 `location /portal/` 안에 있다(구역은
   `rate=30r/m`).

나머지(80 의 308, 443 의 TLS, HSTS `always`, `client_max_body_size 1m`, `proxy_http_version 1.1`, 덮어쓰는
`X-Forwarded-For`, `X-Forwarded-Proto`, `limit_req_status 429`, `= /end-user`·`= /portal`·`/` 의 404)는
시제품과 같다.

**지금 상태(2026-11-13)**: 항목 0~10 을 Docker Desktop(Engine 29.9.2) 위 보통의 브리지 네트워크에서
쟀다. 마지막 실행(run-final)은 37회차 모두 측정이다.

| 항목 | 무엇 |
|---|---|
| 0 | 뒷단 이름이 풀리지 않는 자리에서 `nginx -t` 가 지나는가 |
| 1 | 토큰 경로를 달리 적은 열 가지가 빈도 제한에 드는가, 뒷단이 받는 경로 |
| 2 | 한 클라이언트가 토큰 경로로 12번 연달아 보낼 때, 그 직후의 다른 경로, 빈 열쇠를 세지 않는가 |
| 3 | 허용 목록(넘기는 다섯 가지와 404 일곱 가지), 404 의 HSTS |
| 4 | 80 의 GET 이 308 과 같은 Host 의 https 주소로 가는가 |
| 5 | 클라이언트가 실어 보낸 `X-Forwarded-For` 를 덮어쓰는가 |
| 6 | SSE 가 `X-Accel-Buffering: no` 로 이벤트마다 흐르는가 |
| 7 | 본문 상한 1m 의 경계 |
| 8 | uid 101 nginx 가 키 파일 권한 둘에서 뜨는가 |
| 9 | 같은 이름으로 다시 만들어 주소가 바뀐 뒷단에 몇 초 안에 닿는가 |
| 10 | IPv6 를 켠 내부 네트워크에서 nginx 가 뒷단에 IPv6 로 거는가 |

## 다시 돌리기

저장소 루트에서

```
uv run python .scratch/release-image/probes/proxy_config/run.py
uv run python .scratch/release-image/probes/proxy_config/run.py --sections 9 --work <원본 출력을 둘 폴더>
```

`--sections` 는 위 항목 번호(기본은 전부), `--work` 는 원본 출력(`raw.log`)과 회차마다의 결과
(`results.json`)를 둘 폴더(없으면 임시 폴더), `--keep` 은 끝난 뒤 컨테이너와 네트워크를 남긴다. 한 바퀴가
이 PC 에서 약 3분이었다. 종료 코드는 `tools/probe_kit.py` 의 `Rounds` 가 정한다(표지가 없는 회차가
하나라도 있으면 1). 타입 검사는 `uv run pyright -p .scratch/release-image/probes/proxy_config --outputjson`.

## 필요한 것

- 도는 Docker 데몬. 이 PC 에서는 Docker Desktop(WSL2)이다. 스크립트는 이미지를 받지 않으므로 먼저
  digest 로 받아 둔다.

```
docker pull nginx@sha256:583b7f2fce1cdb8da5ad5c39ebd3c33b98b87d493190e548bdee1fa8c619c311
docker pull python@sha256:fd95fa221297a88e1cf49c55ec1828edd7c5a428187e67b5d1805692d11588db
```

- 만드는 것은 이름이 `ri-pxy-` 로 시작하고 라벨 `ri-pxy-probe` 가 붙은 컨테이너·네트워크·볼륨이다.
  시작과 끝에 그 라벨의 것만 지운다. 이미지 태그는 만들지 않고, `docker system prune` 같은 전체 정리는
  하지 않는다. 호스트 포트는 쓰지 않는다(요청은 같은 네트워크의 클라이언트 컨테이너에서 보낸다).
- 시험용 인증서와 키는 실행 중에 도우미 컨테이너의 tmpfs 에서 만들어 이름 있는 볼륨 셋(`ri-pxy-tls`,
  `ri-pxy-tls-root600`, `ri-pxy-ca`)에 나눠 두고 끝에 볼륨째 지운다. 저장소에는 인증서도 키도 없다.

## 어떻게 재나

보통의 브리지 네트워크 `ri-pxy-net` 에 뒷단 대역 셋(`stub.py`)을 compose 의 서비스 이름처럼 네트워크
별칭(`serve`, `widget`, `portal`)으로 띄우고 그 앞에 nginx 를 띄운다. nginx 컨테이너는 서비스 정의의 꼴을
`docker run` 의 같은 뜻의 옵션으로 옮겼다(`--user 101:101`, `--read-only`, `--cap-drop ALL`,
`--security-opt no-new-privileges:true`, `--tmpfs /tmp`, `--init`). 바깥 틀 `nginx/nginx.conf` 와 잴 설정을
`/etc/nginx/conf.d/default.conf` 자리에, 키 볼륨을 `/etc/nginx/tls` 에 모두 읽기 전용으로 붙인다. 요청은
같은 네트워크의 클라이언트 컨테이너에서 `client.py` 가 보낸다. nginx 에는 별칭 `edge.test` 로 걸고, 만든
인증서만 믿어 이름까지 검증한다. 뒷단 대역은 `0.0.0.0` 에만 묶고, 받은 경로·헤더·본문 크기와 뜰 때 정한
인스턴스 표지를 본문으로 돌려준다.

요청마다 고유한 `rid` 를 `X-Probe-Rid` 헤더로 싣는다(오류 기록과 맞대야 하는 요청은 질의에도 싣는다).
잴 설정의 접근 기록 형식에는 측정 전용 칸 `rid=`(그 헤더)와 `uri="$uri"` 를 더했고 `up=` 을 따옴표로
쌌다. 그래서 요청 하나를 접근 기록(`$limit_req_status`, `$upstream_addr`, `$uri`), 오류 기록, 뒷단의
기록에서 같은 `rid` 로 찾는다. 항목마다의 표지는 `run.py` 의 독스트링에 있다.

| 파일 | 무엇 |
|---|---|
| `run.py` | 오케스트레이터. 회차마다 표지를 보고 `Rounds` 로 센다 |
| `client.py` | 요청을 보내는 쪽(`http`, `sse`, `poll`, `resolve`). 본 것만 JSON 으로 돌려준다 |
| `stub.py` | 뒷단 대역. 인스턴스 표지와 SSE(`/sse`) |
| `nginx/nginx.conf` | 공식 nginx 이미지를 uid 101 로 돌리는 바깥 틀. `bridge_edge/nginx/nginx.conf` 그대로 |
| `nginx/proxy.conf` | 잴 설정 |
| `nginx/direct.conf` | 대조. upstream 묶음과 resolver 없이 뒷단 이름을 `proxy_pass` 에 바로 쓴 꼴(항목 0, 10) |
| `pyrightconfig.json` | 이 폴더의 타입 검사 설정 |

## 근거의 종류

- **쟀다**: 프로브(`run.py`)가 다시 낸다. 표지가 선 회차만 센다.
- 결과 절의 run-final 은 마지막 실행의 `--work` 폴더 이름이다. try1(항목 0·1), try2(항목 2~7),
  try3(항목 8~10)은 그 앞의 실행이고 항목을 나눠 돌았다. 그 뒤 항목 9 를 고쳤고("결과를 본 뒤 바꾼 것")
  다른 항목의 표지와 판정은 그대로다. 원본(`raw.log`, `results.json`)은 측정한 세션의 스크래치패드에
  두었고 저장소에는 싣지 않았다. 다시 돌리면 같은 꼴로 다시 생긴다.
- **손으로 봤다**: 원본 `raw.log` 를 눈으로 본 것. 프로브가 표지로 세지 않는다.
- **어림**: 낱말 그대로.

## 잰 판

| 무엇 | 판 |
|---|---|
| Docker | Docker Desktop, Engine 29.9.2(linux/amd64), WSL2 커널 6.18.58.1-microsoft-standard-WSL2 |
| nginx | 1.30.6(`nginx:1.30.6-alpine`, 위 digest. 실행마다 `nginx -v` 로 적는다) |
| nginx 작업 프로세스 | 16개(`worker_processes auto`, 이 PC) |
| 파이썬(뒷단 대역과 클라이언트) | 3.12.10(`python:3.12.10-slim-bookworm`, 위 digest) |
| 인증서를 만든 openssl | OpenSSL 3.0.16(파이썬 이미지 안) |

## 결과

### 0. 이름이 풀리지 않는 자리의 `nginx -t`

**쟀다**(run-final 과 try1, 설정마다 1회차씩. 같았다). `--network none` 으로 띄운 nginx(uid 101, 같은
옵션)에서 `nginx -t` 를 돌렸다. `proxy.conf` 는 지났다(`test is successful`). 대조인 `direct.conf` 는
`[emerg] host not found in upstream "serve" in /etc/nginx/conf.d/default.conf:27` 로 실패했다. 대조의
실패가 그 자리에서 이름이 실제로 풀리지 않았다는 것을 보이고, `resolve` 를 붙인 설정은 설정을 읽을 때
뒷단 이름을 요구하지 않았다.

### 1. 토큰 경로 변형

**쟀다**(run-final 2회차와 try1 2회차, 네 회차가 같았다). 빈도 제한의 통이 빈 새 클라이언트가 열 가지를
POST 로 한 번씩 보냈다. 표지는 요청마다 접근 기록에 그 `rid` 의 줄이 있는 것이다. `limit` 칸은 접근
기록의 `$limit_req_status` 다(`PASSED` 는 제한을 거쳐 지났다, `-` 는 그 구역이 세지 않았다).

| 보낸 경로 | `limit` | `$uri` | 뒷단이 받은 경로 |
|---|---|---|---|
| `/portal/sites/demo/token` | `PASSED` | `/portal/sites/demo/token` | `/portal/sites/demo/token` |
| `/portal/sites/demo/token?x=1` | `PASSED` | `/portal/sites/demo/token` | `/portal/sites/demo/token?x=1` |
| `/portal/sites/de%6Do/token` | `PASSED` | `/portal/sites/demo/token` | `/portal/sites/demo/token` |
| `/portal//sites/demo/token` | `PASSED` | `/portal/sites/demo/token` | `/portal/sites/demo/token` |
| `/portal/sites/demo/x/../token` | `PASSED` | `/portal/sites/demo/token` | `/portal/sites/demo/token` |
| `/portal/sites/demo/token/` | `-` | `/portal/sites/demo/token/` | `/portal/sites/demo/token/` |
| `/portal/sites/demo/TOKEN` | `-` | `/portal/sites/demo/TOKEN` | `/portal/sites/demo/TOKEN` |
| `/portal/sites/demo/token%2F` | `-` | `/portal/sites/demo/token/` | `/portal/sites/demo/token/` |
| `/portal/sites/demo/token;x` | `-` | `/portal/sites/demo/token;x` | `/portal/sites/demo/token;x` |
| `/portal//sites/de%6Do/x/../token?x=1`(이 프로브가 더했다) | `PASSED` | `/portal/sites/demo/token` | `/portal/sites/demo/token?x=1` |

- 열 가지 모두 200 이었고 기대와 같았다. `%6D`, `//`, `x/../` 와 그 겹침은 제한에 들었고 뒷단은 정규화한
  경로를 받았다. 나머지 넷은 제한 밖이었다.
- 열 가지 모두 제한을 가른 경로(`$uri`)와 뒷단이 받은 경로(질의를 뺀 것)가 같았다. 시제품(정규식
  `location`, URI 없는 `proxy_pass`)에서는 앞의 세 변형을 뒷단이 원문 그대로 받았다(`bridge_edge`
  README 2절의 표).
- `PASSED` 가 실제로 제한을 건 것이라는 양성 대조는 항목 2 다(같은 경로의 12번째가 `REJECTED` 와 429).
  "`/portal/` 의 요청은 모두 제한에 든다"는 해석은 넷의 `-` 가 가른다.

### 2. 한도를 넘긴 요청과 빈 열쇠

**쟀다**(run-final 과 try2, 갈래마다 2회차씩. 모두 같았다). 표지는 보낸 요청마다 접근 기록에 그 `rid` 의
줄이 있고, 429 마다 오류 기록에 그 `rid` 와 구역 이름이 든 `limiting requests` 줄이 있는 것이다.

- 새 클라이언트 하나가 `POST /portal/sites/demo/token` 을 12번 연달아(0.47초 안에) 보내면 11번 200
  (`PASSED`), 12번째 429(`REJECTED`)였다. 오류 기록은 `limiting requests, excess: 10.781 by zone
  "portal_token", client: 172.20.0.9, ... request: "POST /portal/sites/demo/token?rid=63c742-11 HTTP/1.1"`
  꼴이다. 0.47초 동안 채워지는 몫은 0 이라 기대는 정확히 `1+burst`(11)였다.
- 곧바로 같은 클라이언트가 보낸 `GET /portal/` 와 `POST /portal/sites/demo/acknowledgement` 는 200 이고
  `limit` 이 `-` 였다. 그 뒤 다시 보낸 토큰 경로는 429(오류 기록에 거부 줄)였다. 그래서 다른 경로가 200 인
  것은 한도가 풀려서가 아니라 제한 밖이라서다.
- 빈 열쇠. 새 클라이언트가 확인 경로로 15번 보낸 뒤 토큰 경로로 12번 보내면, 확인 경로는 15번 모두
  200(`-`)이었고 토큰 경로는 11번 200, 12번째 429 였다. 빈 열쇠의 요청을 한 통에서 센다면 확인 경로가
  12번째부터 거부됐을 것이고, 확인 경로가 그 클라이언트의 몫을 먹는다면 토큰 경로가 12번째보다 먼저
  거부됐을 것이다. 둘 다 나지 않았다.

### 3. 허용 목록

**쟀다**(run-final 과 try2, 2회차씩. 같았다). 넘기는 다섯 가지는 모두 기대한 뒷단의 200 이었고 뒷단이
받은 경로가 기대와 같았다(`/`→portal `/`, `/widget`→widget `/widget`, `/widget/x`→widget `/widget/x`,
`/end-user/runs`→serve `/end-user/runs`, `/portal/`→portal `/portal/`). 404 일곱 가지(`/health`,
`/admin`, `/api/agents`, `/end-user`, `/portal`, `/plugins`, `/WIDGET`)는 모두 nginx 의 404 였고 HSTS
(`max-age=31536000`)가 붙었으며, 세 뒷단 어느 기록에도 그 `rid` 가 없었다. 넘긴 다섯 가지의 `rid` 를 뒷단
기록에서 찾은 것이 그 찾는 방법이 듣는다는 양성 대조다.

### 4. 80

**쟀다**(run-final 과 try2, 2회차씩. 같았다). 8080 으로 보낸 `GET /portal/?a=1` 은 `Host: edge.test` 와
`Host: edge.test:8080` 둘 다 308 이고 `Location: https://edge.test/portal/?a=1` 였다. Host 에 포트가 있어도
`Location` 에는 포트가 없었다(`$host` 로 짓는다). 둘 다 접근 기록에 308 줄이 있었고 뒷단 기록에는 없었다.
같은 요청을 443 으로 보낸 양성 대조는 뒷단 기록에 있었다.

### 5. 전달 머리

**쟀다**(run-final 과 try2, 2회차씩. 같았다). 클라이언트가 `X-Forwarded-For: 203.0.113.9` 와
`X-Forwarded-Proto: http` 를 실어 nginx 로 보내면 뒷단(serve)은 `X-Forwarded-For: 172.20.0.5` 하나와
`X-Forwarded-Proto: https` 를 받았다. `172.20.0.5` 는 클라이언트 컨테이너의 주소이고 접근 기록의
`$remote_addr` 와 같았다. 같은 머리를 뒷단에 바로 보낸 양성 대조에서는 뒷단이 `203.0.113.9`, `http` 를
그대로 돌려줘, 뒷단 대역이 받은 머리를 그대로 보인다는 것을 확인했다.

### 6. SSE

**쟀다**(run-final 과 try2, 2회차씩). `/end-user/` 아래의 대역 끝점이 0.5초 간격으로 이벤트 넷을 내고
연결을 닫는다. 뒷단이 `X-Accel-Buffering: no` 를 붙이면 넷이 0.005·0.505·1.005·1.506초(2회차는
0.006·0.506·1.006·1.507초)에 따로 닿았다. 붙이지 않은 양성 대조는 넷 모두 1.51초에 한꺼번에 닿았다
(대조가 한꺼번에가 아니면 그 회차는 측정 아님으로 센다). 클라이언트가 받은 응답에는 `X-Accel-Buffering`
머리가 없었다. 이 설정은 프록시의 버퍼링을 끄지 않으므로, 이벤트가 따로 흐르는 것은 뒷단의 그 머리에
기댄다.

### 7. 본문 상한

**쟀다**(run-final 과 try2, 2회차씩. 같았다). POST 본문 1,000,000 바이트와 1,048,576 바이트(1m 그대로)는
200 이고 뒷단이 그 바이트 수를 받았다. 1,048,577 바이트는 nginx 의 413 이었고 뒷단 기록에 없었으며, 오류
기록에 `client intended to send too large body: 1048577 bytes` 줄이 있었다. 상한 아래의 두 본문은
`a client request body is buffered to a temporary file /tmp/client_temp/0000000001` 같은 warn 줄과 함께
tmpfs 인 `/tmp` 에 쓰였다(run-final 의 `raw.log`, **손으로 봤다**). 읽기 전용 루트에서도 그 길이 섰다.

### 8. 키 파일 권한

**쟀다**(run-final 과 try3, 갈래마다 2회차씩. 같았다). 키는 도우미 컨테이너가 만들어 이름 있는 볼륨에
두었고(`chown`, `chmod` 뒤 `stat` 으로 적었다), uid 101 nginx 에 읽기 전용으로 붙였다.

| 키 파일 | uid 101 nginx |
|---|---|
| `root:root 0600` | 뜨지 못한다. 종료 코드 1, `[emerg] cannot load certificate key "/etc/nginx/tls/privkey.pem": BIO_new_file() failed (SSL: error:8000000D:system library::Permission denied:calling fopen(/etc/nginx/tls/privkey.pem, r) ...)` |
| `root:101 0640` | 뜬다. TLSv1.3 으로 연결되고 받은 인증서의 SHA-256 지문이 만든 것과 같다 |

### 9. 다시 만든 뒷단

**쟀다**(run-final 2회차. 걸린 시간은 이 두 회차의 값이고 이 PC 의 부하를 함께 탄다). portal 대역을
`docker rm -f` 로 지우고 같은 이름과 별칭으로 다시 띄웠다. 새 컨테이너가 옛 주소를 다시 받지 않게, 지운
직후 자리 채움 컨테이너를 옛 주소를 받을 때까지 띄우고 새 컨테이너가 뜬 뒤 모두 지웠다(옛 주소는 빈다).
그 뒤 클라이언트가 `/portal/x` 를 0.5초 간격으로(요청 하나의 제한 3초) 보내 응답의 인스턴스 표지가 새
컨테이너의 것이 될 때까지 기다렸다. 표지는 주소가 실제로 바뀌었고, 새 컨테이너가 자기 주소에서 스스로
답했고, 지우기 직전의 요청이 옛 인스턴스에 닿았고, 닿았다고 센 요청이 새 컨테이너의 기록에 있는 것이다.

| 회차 | 주소 | 지우기 시작한 뒤 새 컨테이너가 뜨기까지 | 그 뒤 첫 요청까지 | 요청 |
|---|---|---|---|---|
| 1 | `172.20.0.4`→`172.20.0.13`(자리 채움 1개) | 1.7초 | 0.2초와 `docker exec` 를 띄우는 몫 | 첫 요청은 옛 주소로 가(`up="172.20.0.4:3000"`) 클라이언트 제한 3초까지 매달렸다(접근 기록의 상태는 499. run-final 의 `raw.log`, **손으로 봤다**). 둘째 요청(첫 요청 뒤 3.5초)이 새 컨테이너에 닿았다(`up="172.20.0.13:3000"`) |
| 2 | `172.20.0.13`→`172.20.0.14`(자리 채움 2개) | 6.8초 | 1.2초와 그 몫 | 첫 요청이 새 컨테이너에 닿았다(`up="172.20.0.14:3000"`) |

- 두 회차 모두 nginx 를 다시 읽히지 않고 새 컨테이너에 닿았다.
- 1회차의 두 요청으로 보면, nginx 가 새 주소로 옮긴 때는 옛 컨테이너를 지우기 시작한 뒤 1.9초와
  5.4초 사이(둘 다 `docker exec` 를 띄우는 몫만큼 더 늦다)다(**어림**: 요청 시각에서 셈했다). `valid=5s`
  와 어긋나지 않는다. 2회차는 새 컨테이너가 뜬 뒤 첫 요청까지(1.2초와 그 몫) 이미 옮겨 있었다.
- 두 회차 동안 nginx 오류 기록(notice 이상)에는 이름을 풀지 못했다는 줄(`could not be resolved`)도, 이
  요청들의 warn 이상 줄도 없었다(프로브가 세어 적는다). 프록시의 기록 전체에서 warn 이상은 항목 2 의
  거부 6줄, 항목 7 의 413 2줄과 임시 파일 4줄뿐이었다(run-final 의 `raw.log`, **손으로 봤다**).
- try3 의 1회차(요청 하나의 제한이 10초였다)도 첫 요청이 옛 주소에서 10초 매달린 뒤 둘째 요청이 새
  컨테이너에 닿았다(poll 시작 뒤 10.5초). try3 의 2회차는 주소가 바뀌지 않아(`172.20.0.7`→`172.20.0.7`)
  측정 아님이었다.

### 10. IPv6 를 켠 내부 네트워크

**쟀다**(run-final 과 try3, 설정마다 3회차씩. 두 실행의 수가 같았다).

- `docker network create --ipv6` 에 대역을 주지 않아도 Docker 가 IPv6 대역을 잡았다(두 실행 모두
  `fd8e:1b35:8c7f::/64` 와 `172.21.0.0/16`). 그 네트워크의 클라이언트에서 뒷단 이름 셋이 A 와 AAAA 로
  풀렸다(getaddrinfo).
- 같은 네트워크에 nginx 둘(대조 `direct.conf` 와 `proxy.conf`)을 띄워, 회차마다 뒷단마다 20번(모두
  60번)씩 번갈아 보냈다. 뒷단 대역은 `0.0.0.0` 에만 묶었다. 회차 사이는 11초 쉬어, nginx 가 실패한
  주소를 쉬게 두는 시간(`fail_timeout` 기본 10초)이 지나게 했다.

| 설정 | 200 | `$upstream_addr` 에 IPv6 가 든 요청 | 오류 기록의 IPv6 연결 실패 |
|---|---|---|---|
| 대조. 뒷단 이름을 `proxy_pass` 에 바로 쓴 `direct.conf` | 60/60, 세 회차 | 5, 6, 6 | 5, 6, 6줄(기록 전체 17줄) |
| `proxy.conf`(`resolve`, `ipv6=off`) | 60/60, 세 회차 | 0, 0, 0 | 0줄(기록 전체에 warn 이상 줄이 없다) |

- 대조에서 IPv6 로 건 요청은 IPv6 주소에서 `connect() failed (111: Connection refused)` 와
  `upstream server temporarily disabled` 줄을 낸 뒤(프로브가 문구별로 센다) IPv4 로 다시 걸어 200 이 됐다.
  뒷단 셋 모두에서 났다. 접근 기록의 `up` 칸은 `"[fd8e:1b35:8c7f::2]:8000, 172.21.0.2:8000"` 꼴이었다
  (run-final 의 `raw.log`, **손으로 봤다**).
- `proxy.conf` 는 같은 네트워크, 같은 뒷단, 같은 때에 한 번도 IPv6 로 걸지 않았다. 대조가 같은 자리에서
  17번 IPv6 로 걸었으므로 "이 자리에서는 IPv6 로 걸 일이 없었다"는 해석은 서지 않는다.
- 이 네트워크에서 클라이언트는 nginx 에 IPv6 로 걸었다(오류 기록의 `client: fd8e:1b35:8c7f::5` 는
  프로브가 찍은 실패 줄의 예에, 접근 기록의 같은 주소는 run-final 의 `raw.log` 에 있다. 뒤의 것은 **손으로
  봤다**). `listen [::]:8443 ssl` 이 그 연결을 받았다.

## 결과를 본 뒤 바꾼 것

- 항목 9. try3 의 2회차가 측정 아님이었다. 자리 채움 컨테이너 하나가 옛 주소(`.7`)가 아니라 그보다 낮은
  빈 주소(`.4`)를 받아 새 컨테이너가 옛 주소를 다시 받았다. Docker 가 빈 주소 가운데 낮은 것부터 주는
  것으로 보고(**어림**: 이 PC 의 실행들에서 본 차례다) 자리 채움을 옛 주소를 받을 때까지(여덟까지)
  띄우게 바꿨다. 같이 요청 하나의 제한을 10초에서 3초로 줄였다(try3 의 1회차가 옛 주소에서 10초를 다
  썼다). 표지와 판정은 바꾸지 않았다.
- 항목 3 과 항목 10 은 보이는 글(경로마다의 줄, 실패 줄의 예, 기록 전체의 셈)만 더했다.

## 재지 못한 것

- 실제 뒷단 이미지(serve, 위젯, 위젯 미리보기 페이지). 뒷단은 `stub.py` 다. 실제 serve 가 SSE 에
  `X-Accel-Buffering: no` 를 붙이는지, 실제 뒷단이 `::` 에도 묶는지는 보지 않았다.
- compose. `docker run` 으로 같은 옵션을 주고 서비스 이름을 네트워크 별칭으로 흉내 냈다.
  `docker compose up -d` 가 컨테이너를 다시 만들 때의 차례와 주소는 재지 않았다.
- 리눅스 서버의 Docker Engine. Docker Desktop(WSL2) 위의 Engine 29.9.2 하나다. IPv6 대역을 스스로 잡는
  것과 빈 주소를 주는 차례는 이 데몬에서 본 것이다.
- 다른 nginx 판. 이 프로브는 1.30.6 이다(명세가 드는 `bridge_recover` 는 1.31.6 에서 쟀다).
- 클라이언트가 끊지 않을 때 옛 주소로 간 요청이 얼마나 매달리고 nginx 가 무엇으로 답하는지.
- 다시 풀 때 Docker 내장 DNS 가 답하지 않거나 오류를 내는 경우. 항목 9 에 이름을 풀지 못했다는 줄이
  없었던 까닭은 가르지 않았다.
- `nginx -s reload` 뒤의 빈도 제한 상태, 쉰 뒤 다시 받는 몫(`30r/m` 의 채움), 여러 클라이언트와 NAT,
  IPv6 로 온 손님의 열쇠, 요청이 작업 프로세스 여럿에 갈렸는지.
- 걸린 시간(항목 6, 9)은 이 PC 의 부하를 함께 탄다. 항목 9 는 측정 두 회차(앞선 실행까지 셋)뿐이다.
