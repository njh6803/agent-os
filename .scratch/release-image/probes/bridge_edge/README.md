# bridge_edge — 단독 배포의 가장자리를 리눅스 Docker Engine 에서 잰다

release-image 명세가 정할 것 가운데 서버의 가장자리에 걸린 여덟 가지를 잰다. 결정은 하지 않는다.

1. 프록시(nginx)가 보는 접속 주소(`$remote_addr`)가 갈래마다 무엇인가
2. 접속 주소별 빈도 제한(`limit_req`)이 이웃 둘을 따로 세는가, 한도를 넘긴 요청이 429 인가
3. `127.0.0.1` 에만 발행한 포트에 같은 L2 의 이웃이 닿는가(Engine 27 과 28 이후)
4. 뒷단 포트를 잘못 발행하면(`"8000:8000"`) 이웃이 평문으로 닿는가(양성 대조)
5. TLS(스스로 서명한 인증서), HSTS, 80 에서 443 으로 넘기기, 허용한 경로 밖의 404, root 가 아닌 nginx
6. 호스트 폴더를 붙였을 때 root 가 아닌 고정 uid 가 쓸 수 있는가, named volume 과 어떻게 다른가
7. 안쪽 네트워크에 IPv6 를 켠 배치에서 같은 L2 의 이웃이 서버를 경유해 컨테이너의 IPv6 주소에 닿는가
8. 443 과 80 을 IPv4 에만 발행한 배치(`"0.0.0.0:443:8443"`)에서 IPv6 손님은 어떻게 되고 프록시는 누구로
   보는가

**지금 상태(2026-11-13)**: 여섯 항목을 모두 프로브로 쟀다. 항목 1·3·4 는 세 엔진(27.5.1, 28.0.0,
29.9.2)과 userland-proxy 두 값으로, 항목 2·5·6 은 Engine 29.9.2(userland-proxy 켬)에서다. 실행마다 측정
아님은 0회차였다(edge-run4 268회차, edge-run5 162회차, edge-run6 19회차).

**덧붙임(2026-11-13, 항목 7·8 과 Engine 28.3.3)**: 항목 7 을 네 엔진(27.5.1, 28.0.0, 28.3.3, 29.9.2)과
두 모드로, 항목 8 을 Engine 28.3.3·29.9.2 와 두 모드로 쟀고, 항목 3 을 Engine 28.3.3 에서 다시 쟀다
(9절). 실행마다 측정 아님은 0회차였다(edge-run7 88회차, edge-run8 132회차, edge-run9 108회차).

## 요약(명세의 결정에 쓸 한 줄씩)

1. 접속 주소. 같은 L2 의 이웃이 IPv4 로 건 요청은 세 엔진·두 모드 모두 제 주소로 보인다. 안쪽
   네트워크가 IPv4 뿐이고 userland-proxy 가 켜져 있으면(Docker 기본값) IPv6 손님은 모두 안쪽 게이트웨이
   하나로 보이고, 끄면 IPv6 손님이 닿지 못한다. 안쪽 네트워크에 IPv6 를 켜면 IPv6 손님도 제 주소다
   (29.9.2). 서버 자신이 루프백으로 건 요청은 잰 엔진과 모드 모두에서 게이트웨이로 보였다. **쟀다**
2. 빈도 제한. `limit_req_zone $binary_remote_addr` 는 이웃 둘을 따로 세어 저마다 `1+burst` 개를 넘기고
   429 를 낸다(`limit_req_status 429` 가 없으면 503, `Retry-After` 는 없다). 시제품 `30r/m burst=10
   nodelay` 는 12번째 요청부터 거부했다. IPv6 손님이 게이트웨이로 뭉치는 배치에서는 한 통을 같이 쓴다.
   **쟀다**(29.9.2). 수치의 바탕은 **코드를 읽었다**와 **어림**이다.
3. 최소 Engine. 27.5.1 에서는 같은 L2 의 이웃이 서버를 경유해 `127.0.0.1` 에만 발행한 관리 화면에
   닿는다(컨테이너 주소로도, `127.0.0.1` 로도). 28.0.0 과 29.9.2 는 두 모드 모두 막는다. **쟀다**.
   firewalld 를 쓰는 서버는 28.3.3 부터다(**원문을 받아 대 봤다**, 재지 않았다).
4. 잘못 발행. 뒷단에 `"8000:8000"` 을 주면 세 엔진 모두 이웃이 평문으로 닿는다. 엔진의 보호는 발행한
   포트를 막지 않는다. **쟀다**
5. TLS 와 경로. 시제품 설정으로 443 은 TLS 만 받고(평문은 400), HSTS 는 200·404·429 모두에 붙고, 80 은
   같은 경로의 https 로 308 이며(ACME 경로 포함), 허용 목록 밖 20가지는 404, 넘기는 헤더는 덮어쓰고,
   1m 상한은 413 이다. SSE 는 뒷단의 `X-Accel-Buffering: no` 에 기댄다. 공식 nginx 를 uid 101·읽기
   전용·`cap_drop: [ALL]` 로 돌리면 키를 `root:101 640`(또는 `101:101 600`)으로 둬야 읽는다. **쟀다**
   (29.9.2)
6. 쓰기 권한. 붙인 호스트 폴더는 운영자가 미리 고정 uid 로 `chown` 해야 쓴다(없는 경로는 Docker 가 root
   소유로 만든다). 빈 named volume 은 이미지의 그 경로가 그 uid 소유면 쓴다. **쟀다**(29.9.2)
7. IPv6 경유. 안쪽 네트워크에 IPv6(`fd00:30::/64`)를 켠 배치에서 같은 L2 의 이웃이 서버를 경유해
   컨테이너의 IPv6 주소로 거는 길을 28.0.0·28.3.3·29.9.2 는 두 모드와 IPv6 FORWARD 정책 두 값 모두에서
   막았다(관리 화면, serve, 프록시). 27.5.1 은 모든 주소에 발행한 프록시에 정책과 상관없이 닿고, 관리
   화면과 serve 에는 IPv6 FORWARD 정책이 `ACCEPT` 일 때 닿는다. 서버의 IPv6 주소로 거는 `:3000`·`:8000`
   은 네 엔진 모두 refused 다. **쟀다**
8. IPv4 에만 발행. 443·80 을 `"0.0.0.0:443:8443"`, `"0.0.0.0:80:8080"` 으로 발행하면(안쪽 네트워크는
   IPv4 뿐) 이웃의 IPv6 `:443`·`:80` 과 서버 자신의 `[::1]:443`·바깥 IPv6 가 두 엔진(28.3.3, 29.9.2)과 두
   모드 모두 refused 다. 서버 안에는 IPv6 쪽 443·80 의 듣는 소켓도, `-host-ip ::` 의 docker-proxy 도,
   ip6tables 의 DNAT 도 없다. IPv4 이웃 둘은 저마다의 주소로 보이고, 서버 자신의 `127.0.0.1:443` 은 안쪽
   게이트웨이로 보인다. 1절의 시제품 배치에서 userland-proxy 를 켠 때 IPv6 손님이 게이트웨이 하나로 뭉치던
   길이 없어진다. **쟀다**
9. 28.3.3. 항목 3 의 경유 공격(A 컨테이너 주소로, B 서버의 `127.0.0.1` 로)을 두 모드와 두 정책 모두에서
   막는다. 막는 규칙의 꼴은 29.9.2 와 같다. **쟀다**

## 다시 돌리기

저장소 루트에서

```
uv run python .scratch/release-image/probes/bridge_edge/run.py
uv run python .scratch/release-image/probes/bridge_edge/run.py --sections 1 --engines 29.9.2 --modes on
uv run python .scratch/release-image/probes/bridge_edge/run.py --sections 3,7 --engines 28.3.3
uv run python .scratch/release-image/probes/bridge_edge/run.py --sections 7 --engines 29.9.2,28.0.0,27.5.1
uv run python .scratch/release-image/probes/bridge_edge/run.py --sections 8 --engines 29.9.2,28.3.3
```

항목 7·8 과 엔진 28.3.3 은 기본값에 들지 않아 위 셋째부터 다섯째 줄처럼 고른다(`--engines` 에 28.3.3 도
줄 수 있다). 결과 7절은 셋째·넷째 줄, 8절은 다섯째 줄, 9절은 셋째 줄로 잰 것이다.

`--sections` 는 위 항목 번호, `--engines` 는 `29.9.2,28.0.0,27.5.1` 에서 고르고, `--modes` 는
userland-proxy 를 켠 때(`on`)와 끈 때(`off`)다. 원본 출력은 `--work` 폴더(없으면 임시 폴더)의
`raw.log` 에, 회차마다의 결과는 `results.json` 에 남는다. 종료 코드는 `tools/probe_kit.py` 의 `Rounds`
가 정한다(표지가 없는 회차가 하나라도 있으면 1). 모두 돌면 45분 남짓이다(**어림**. 항목 1·3·4 를 여섯
시나리오로 돈 edge-run4 가 33분, 항목 1·5·6 의 edge-run5 가 24분이었다).

## 필요한 것

- 도는 Docker 데몬. 이 PC 에서는 Docker Desktop(WSL2)이다. 스크립트는 이미지를 받지 않으므로 먼저
  digest 로 받아 둔다.

```
docker pull docker@sha256:9e79b879b177fbd72c34376a3dd3d91747da5db49e1f560f76aea59561471977
docker pull docker@sha256:0a9c58ebc9f86e5af35e4330f6c738dc64fce3ca2e2574b5becdfb88765b308b
docker pull docker@sha256:aa3df78ecf320f5fafdce71c659f1629e96e9de0968305fe1de670e0ca9176ce
docker pull docker@sha256:a56b3bdde89315ed2cc0e4906e582b5033d93bf20d9cb9510c2cdd4e7f7690b1
docker pull nginx@sha256:583b7f2fce1cdb8da5ad5c39ebd3c33b98b87d493190e548bdee1fa8c619c311
docker pull nginxinc/nginx-unprivileged@sha256:f5116ed4606f3eb015dd4a8e28cb9b351476dc0ad4bc6e9f93b19cec130cdf03
docker pull python@sha256:fd95fa221297a88e1cf49c55ec1828edd7c5a428187e67b5d1805692d11588db
```

- 만드는 것은 이름이 `ri-edge-` 로 시작하고 라벨 `ri-edge-probe` 가 붙은 컨테이너·네트워크와 태그 셋
  (`ri-edge-nginx:pinned`, `ri-edge-nginx-unpriv:pinned`, `ri-edge-python:pinned`)이다. 시작과 끝에
  그 라벨의 것만 지우고 태그를 뗀다. `docker system prune` 같은 전체 정리는 하지 않는다. 호스트 포트는
  쓰지 않는다.
- 시험용 인증서와 키는 서버(dind) 컨테이너 안에서 만들고 그 컨테이너와 함께 사라진다. 이웃에 건넬
  인증서(공개 쪽)만 `--work` 폴더를 거치고 끝에 지운다. 저장소에는 인증서도 키도 없다.

## 어떻게 재나

Docker Desktop 의 포트 발행은 리눅스 서버와 길이 달라, 공식 `docker:<판>-dind` 를 `--privileged` 로 띄운
컨테이너를 "리눅스 서버"(`ri-edge-server`, 10.77.0.10 / fd00:77::10)로 쓴다. 바깥 브리지 네트워크
`ri-edge-lan`(10.77.0.0/24, fd00:77::/64)에 서버와 "이웃 기기" 둘(`ri-edge-n1` 10.77.0.21,
`ri-edge-n2` 10.77.0.22)을 붙인다. 이웃이 같은 L2 구간의 다른 호스트 역할이다. 서버 안에서는 이 폴더의
`compose.yml`(시제품 배치. 프록시와 뒷단 넷)과 `compose.probe.yml`(측정 전용 덧씌움)을 띄운다. 뒷단은
실제 이미지가 아니라 `stub.py`(`0.0.0.0` 에 묶는 작은 HTTP 서버. 받은 경로·헤더·상대 주소를 본문으로
돌려준다)다. 요청은 이웃 컨테이너와 서버 자신(서버 안에서 호스트 네트워크로 띄운 컨테이너)에서
`client.py` 가 보낸다.

| 파일 | 무엇 |
|---|---|
| `run.py` | 오케스트레이터. 회차마다 표지를 보고 `Rounds` 로 센다 |
| `client.py` | 요청을 보내는 쪽. 본 것만 JSON 으로 돌려준다 |
| `stub.py` | 뒷단 대역 |
| `compose.yml` | 시제품 배치(프록시 443·80, 관리 화면 `127.0.0.1:3000`, 뒷단 셋) |
| `compose.probe.yml` | 측정 전용. 빈도 제한 조합 서버(8081)와 안쪽 대역 고정(172.30.0.0/24) |
| `compose.wrong-port.yml` | 항목 4. `serve` 에 `"8000:8000"` |
| `compose.ipv6.yml` | 항목 1 의 덧 갈래. 안쪽 네트워크에도 IPv6 |
| `compose.ipv6-listen.yml` | 항목 7. `compose.ipv6.yml` 에 더 얹어 관리 화면과 serve 대역이 `::` 에도 듣게 한다(`stub.py` 의 셋째 인자 `::`) |
| `compose.v4-publish.yml` | 항목 8. 프록시의 `ports` 를 `!override` 로 `"0.0.0.0:443:8443"`, `"0.0.0.0:80:8080"` 두 줄로 바꾼다 |
| `compose.unprivileged.yml` | 항목 5 의 덧 갈래. `nginxinc/nginx-unprivileged` 에 `edge.conf` 만 얹기 |
| `nginx/nginx.conf` | 공식 nginx 이미지를 uid 101 로 돌리는 바깥 틀(pid·임시 파일을 `/tmp` 로) |
| `nginx/edge.conf` | 프록시 설정 시제품 |
| `nginx/probe-limits.conf` | 측정 전용. 빈도 제한 조합마다 구역 하나 |
| `pyrightconfig.json` | 이 폴더를 strict 로 보는 타입 검사 설정. `uv run pyright -p .scratch/release-image/probes/bridge_edge/pyrightconfig.json` |

## 근거의 종류

- **쟀다**: 프로브(`run.py`)가 다시 낸다. 표지가 선 회차만 센다.
- **손으로 봤다**: 프로브를 짓기 전에 스크래치패드의 셸 스크립트로 띄워 출력을 눈으로 봤다(그 스크립트는
  저장소에 없다). 서버 안에서 `docker run --rm --network host ... ri-edge-python:pinned python
  /client.py <일 목록>` 으로 요청을 보내고 `docker logs ri-edge-proxy-1` 과 `iptables-save -c` 를 읽었다.
  프로브가 다시 내기 전까지는 이 이름으로 둔다.
- **원문을 받아 대 봤다**: 원문 파일을 내려받아 해당 문장을 글자로 대 봤다.
- **코드를 읽었다**, **어림**: 낱말 그대로.

결과 절의 edge-run1·edge-run2·edge-run4·edge-run5·edge-run6 은 그 실행의 `--work` 폴더 이름이다.
원본(`raw.log`, `results.json`)은 측정한 세션의 스크래치패드에 두었고 저장소에는 싣지 않았다. 다시 돌리면
같은 꼴로 다시 생긴다. 7·8·9절의 edge-run7·edge-run8·edge-run9 도 같다.

## 잰 판

| 무엇 | 판 |
|---|---|
| 바깥 Docker | Docker Desktop, Engine 29.9.2(linux/amd64), WSL2 커널 6.18.58.1-microsoft-standard-WSL2 |
| dind 이미지 | `docker:29.9.2-dind`, `docker:28.0.0-dind`, `docker:27.5.1-dind`(digest 는 위 `docker pull`) |
| 안쪽 Engine(29.9.2) | Engine 29.9.2, Compose 5.6.1, iptables v1.8.13(nf_tables), OpenSSL 3.5.9, 저장 드라이버 overlayfs, `ip_forward=1`, filter FORWARD 정책 `ACCEPT`(프로브가 적는다). API 1.56, containerd v2.4.2, runc 1.5.2 는 손으로 봤다 |
| 안쪽 Engine(27.5.1) | Engine 27.5.1, Compose 2.33.0, iptables v1.8.11(nf_tables), OpenSSL 3.3.3, 저장 드라이버 overlay2, `ip_forward=1`, filter FORWARD 정책 `ACCEPT`(프로브가 적는다) |
| 안쪽 Engine(28.0.0) | Engine 28.0.0, Compose 2.33.1, iptables v1.8.11(nf_tables), OpenSSL 3.3.3, 저장 드라이버 overlay2, `ip_forward=1`, filter FORWARD 정책 `ACCEPT`(프로브가 적는다) |
| dind 이미지(7·8·9절에서 더함) | `docker:28.3.3-dind`(2026-11-13 에 받았다. digest 는 위 `docker pull`) |
| 안쪽 Engine(28.3.3) | Engine 28.3.3, Compose 2.39.2, iptables v1.8.11(nf_tables), OpenSSL 3.5.2, 저장 드라이버 overlay2, `ip_forward=1`, filter FORWARD 정책 `ACCEPT`(프로브가 적는다) |
| 서버의 IPv6(항목 7 의 회차 0, 네 엔진) | ip6tables v1.8.13(29.9.2)·v1.8.11(그 밖의 셋), nf_tables. 안쪽 IPv6 배치를 띄운 뒤 `/proc/sys/net/ipv6/conf/all/forwarding` 이 1, ip6tables filter FORWARD 정책 `DROP`(프로브가 적는다) |
| nginx | 1.30.6(`nginx:1.30.6-alpine`, `nginxinc/nginx-unprivileged:1.30.6-alpine`) |
| 파이썬 | 3.12.10(`python:3.12.10-slim-bookworm`) |

## 결과

### 1. 프록시가 보는 접속 주소

**쟀다**(Engine 27.5.1·28.0.0·29.9.2 마다 userland-proxy 를 켠 때와 끈 때, 실행 둘(edge-run4,
edge-run5)에서 갈래마다 2회차씩, 같은 갈래의 회차는 모두 같은 값. edge-run4 는 27.5.1·28.0.0 의 게이트웨이를
읽지 못해 `172.30.0.1` 을 "그 밖"으로 적었고, 게이트웨이를 프록시 컨테이너의 엔드포인트에서 읽게 고친
edge-run5 가 같은 값을 안쪽 게이트웨이로 갈랐다). 요청마다 고유한 `rid` 를 질의에 붙이고, 뒷단이 받은
`X-Forwarded-For`(프록시가 `$remote_addr` 로 덮어쓴다. 보낸 쪽은 `203.0.113.9` 를 실어 보냈다)와 프록시
접근 기록의 그 `rid` 줄의 `$remote_addr` 가 같은 회차만 센다. 닿지 않은 회차는 같은 길의 대조(이웃과
서버 자신이 서버 호스트의 `[::]` 대조 포트에 닿는다)가 선 때만 센다. userland-proxy 는 켠 때
`docker-proxy` 프로세스가 7개, 끈 때 0개였다.

안쪽 네트워크가 IPv4 뿐인 배치(시제품). 세 엔진의 값이 같았다.

| 요청 | userland-proxy 켬(Docker 기본값) | userland-proxy 끔 |
|---|---|---|
| 이웃 n1·n2 → 서버의 IPv4 `:443` | 보낸 이웃의 주소(`10.77.0.21`, `10.77.0.22`) | 같다 |
| 이웃 n1·n2 → 서버의 IPv6 `:443` | **둘 다 안쪽 게이트웨이 `172.30.0.1`** | 닿지 않음(refused) |
| 서버 자신 → `127.0.0.1:443` | 안쪽 게이트웨이 `172.30.0.1` | 같다 |
| 서버 자신 → `[::1]:443` | 안쪽 게이트웨이 `172.30.0.1` | 닿지 않음(refused) |
| 서버 자신 → 자기 바깥 IPv4 `10.77.0.10:443` | 자기 주소 `10.77.0.10` | 안쪽 게이트웨이 `172.30.0.1` |
| 서버 자신 → 자기 바깥 IPv6 `[fd00:77::10]:443` | 안쪽 게이트웨이 `172.30.0.1` | 닿지 않음(refused) |

안쪽 네트워크에도 IPv6 를 켠 배치(`compose.ipv6.yml`, Engine 29.9.2 만).

| 요청 | userland-proxy 켬 | userland-proxy 끔 |
|---|---|---|
| 이웃 n1·n2 → 서버의 IPv4 `:443` | 보낸 이웃의 주소 | 같다 |
| 이웃 n1·n2 → 서버의 IPv6 `:443` | 보낸 이웃의 주소(`fd00:77::21`, `fd00:77::22`) | 같다 |
| 서버 자신 → `127.0.0.1:443` | 안쪽 IPv4 게이트웨이 `172.30.0.1` | 같다 |
| 서버 자신 → `[::1]:443` | 안쪽 IPv6 게이트웨이 `fd00:30::1` | 닿지 않음(timeout) |
| 서버 자신 → 자기 바깥 IPv4 | 자기 주소 `10.77.0.10` | 안쪽 IPv4 게이트웨이 `172.30.0.1` |
| 서버 자신 → 자기 바깥 IPv6 | 자기 주소 `fd00:77::10` | 안쪽 IPv6 게이트웨이 `fd00:30::1` |

- 같은 L2 의 이웃이 IPv4 로 건 요청은 세 엔진과 두 모드 모두에서 nginx 가 이웃마다의 주소로 봤다.
  그래서 IPv4 로 오는 손님은 주소별 빈도 제한의 열쇠가 손님마다 갈린다.
- 주소가 하나로 뭉치는 갈래는 둘이다. 서버 자신이 건 요청(루프백은 모든 갈래에서, 자기 바깥 주소는
  userland-proxy 를 끈 때)과, 안쪽 네트워크가 IPv4 뿐이고 userland-proxy 를 켠 때 IPv6 로 온 요청이다.
  뒤의 것은 이웃 둘이 같은 `172.30.0.1` 로 보였다. userland-proxy 를 끄면 같은 IPv6 요청이 모두
  refused 였다(그 길의 대조인 `[::]` 대조 포트에는 닿았다). 그래서 IPv4 뿐인 안쪽 네트워크에서 IPv6
  손님을 받는 길은 `docker-proxy` 하나이고, 그 길로 온 손님은 모두 게이트웨이로 보인다.
- 안쪽 네트워크에 IPv6 를 켜면 두 모드 모두 IPv6 손님도 제 주소로 보인다. 대신 nginx 가 뒷단 이름의
  IPv6 주소로도 건다. `0.0.0.0` 에만 묶은 뒷단에 8번 보낸 요청이 두 모드 모두 8번 200 이었지만, 프록시
  오류 기록에 뒷단의 IPv6 주소(`[fd00:30::3]:8000`, `[fd00:30::4]:8000`)로 건 연결이 실패한 줄이 모드마다
  1줄 있었다(nginx 가 다음 주소로 다시 걸어 200 이 됐다). 실제 뒷단이 `::` 에도 묶는지는 재지 않았다.
- userland-proxy 를 끈 이중 스택 배치에서 서버 자신의 `[::1]:443` 은 refused 가 아니라 시간 초과였다
  (2회차). 까닭은 재지 않았다.
- 앞선 실행(edge-run1)의 "안쪽 IPv6 켬" 배치는 IPv4 대역이 고정되지 않아 `127.0.0.1` 요청이
  `172.18.0.1` 로 보였다. compose 는 덧씌울 때 `ipam.config` 목록을 잇지 않고 바꾼다(Compose v5.6.1 의
  `docker compose ... config` 로 손으로 봤다). `compose.ipv6.yml` 에 IPv4 대역을 다시 적은 뒤의 위
  표에서는 `172.30.0.1` 이다.

### 2. 접속 주소별 빈도 제한

**쟀다**(Engine 29.9.2, userland-proxy 켬. 원본은 edge-run2, 16회차 모두 측정). 측정 전용 서버(8081)에
조합마다 구역 하나를 두고, 이웃 n1 과 n2 가 같은 때에 `1+burst+5` 번씩 차례로 보냈다. 표지는 보낸 요청마다 프록시 접근 기록에 그 `rid` 줄이
있고, 200 이 아닌 응답마다 오류 기록에 그 구역의 `limiting requests` 줄이 있는 것이다. 주소별로 따로
센다는 해석은 두 이웃이 저마다 `1+burst` 개를 받는 것이고, 한 통에서 센다는 해석은 둘의 합이
`1+burst` 인 것이다(묶음이 걸린 시간에 채워지는 몫만큼 더 받을 수 있게 폭을 둔다. 이번에는 묶음이
0.1초 안에 끝나 그 몫이 0 이었다).

| 설정 | n1 이 받은 수 | n2 가 받은 수 | 첫 거부 | 거부 코드 |
|---|---|---|---|---|
| `rate=10r/m`, burst 없음 | 1 | 1 | 2번째 요청 | 429 |
| `rate=10r/m burst=5 nodelay` | 6 | 6 | 7번째 | 429 |
| `rate=30r/m burst=10 nodelay` | 11 | 11 | 12번째 | 429 |
| `rate=60r/m burst=20 nodelay` | 21 | 21 | 22번째 | 429 |
| 시제품 토큰 경로(443), `rate=30r/m burst=10 nodelay` | 11 | 11 | 12번째 | 429 |

- 네 조합과 시제품 모두 이웃 둘을 따로 셌고, 저마다 정확히 `1+burst` 개를 받은 뒤 429 였다.
- 거부 코드는 `limit_req_status 429` 를 적었을 때 429 이고, 적지 않으면 503 이었다(`rate=60r/m`,
  `limit_req_status` 없음: 200 503 503).
- 429 응답에는 `Retry-After` 가 없었다. HSTS 는 있었고 본문은 nginx 의 429 쪽이다. 응답 헤더는
  `connection`, `content-length`, `content-type`, `date`, `server`, `strict-transport-security` 뿐이다.
- 시제품 토큰 경로에서 한도를 넘긴 n1 이 바로 뒤에 부른 다른 경로(`/portal/`,
  `/portal/sites/demo/acknowledgement`, `/widget`, `/end-user/runs`, `/`)는 모두 200 이었고 접근 기록의
  `limit` 칸이 `-`(그 구역 밖)였다. 그 뒤 다시 부른 토큰 경로는 429 였다.
- 쉰 뒤에는 다시 받는다. `rate=10r/m` 에서 6.4초 쉰 뒤 3번 보내면 200 429 429 였다. `30r/m` 에서 2.4초,
  `60r/m` 에서 1.4초 쉰 뒤에는 200 200 429 였다. 쉰 시간에 `docker exec` 를 띄우는 지연이 더해져 한
  간격보다 길게 쉰 것으로 보인다(**어림**. 실제로 쉰 시간은 적지 않았다).
- `nodelay` 가 없으면(`rate=60r/m burst=3`) 한꺼번에 보낸 7번 가운데 4번이 0, 1, 2, 3초 늦춰져 200 이었고
  3번이 429 였다.
- **뭉침(양성 대조)**: 안쪽 네트워크가 IPv4 뿐일 때 이웃 둘이 IPv6 로 같은 때에 11번씩 보내면
  (`rate=10r/m burst=5 nodelay`) n1 이 6, n2 가 0 을 받았다. 두 이웃의 `$remote_addr` 가 모두
  `172.30.0.1` 이었고 한 통에서 셌다. 이 방법이 주소가 뭉친 경우를 가려낸다는 대조다.
- 토큰 경로를 다르게 적은 요청(서버 자신에서 보냈다):

| 보낸 경로 | 빈도 제한 | 뒷단이 받은 경로 |
|---|---|---|
| `/portal/sites/demo/token` | 안 | `/portal/sites/demo/token` |
| `/portal/sites/demo/token?x=1` | 안 | 같다(질의 포함) |
| `/portal/sites/de%6Do/token` | 안 | `/portal/sites/de%6Do/token`(원문 그대로) |
| `/portal//sites/demo/token` | 안 | `/portal//sites/demo/token`(원문 그대로) |
| `/portal/sites/demo/x/../token` | 안 | `/portal/sites/demo/x/../token`(원문 그대로) |
| `/portal/sites/demo/token/` | 밖 | `/portal/sites/demo/token/` |
| `/portal/sites/demo/TOKEN` | 밖 | `/portal/sites/demo/TOKEN` |
| `/portal/sites/demo/token%2F` | 밖 | `/portal/sites/demo/token/`(정규화됨) |
| `/portal/sites/demo/token;x` | 밖 | `/portal/sites/demo/token;x` |

  정규식 `location` 은 정규화한 경로로 고르고, `proxy_pass` 에 URI 가 없어 받은 원문을 그대로 넘긴다.
  빈도 제한 밖으로 빠진 네 가지는 위젯 미리보기 페이지가 토큰을 내지 않는 경로다. 그 페이지는 원문
  경로를 풀지 않은 채 `^/portal/sites/([^/]+)/(acknowledgement|token)$` 에 대고 이름을 설정의 이름과 글자
  그대로 견준다(`web/apps/portal/server/paths.ts` 의 `SITE_ENDPOINT`, `handler.ts` 의 `siteEndpoint`,
  `serve.ts` 의 `splitTarget`. **코드를 읽었다**). 그래서 그 페이지가 토큰을 내는 요청은 사이트 이름에
  `%` 가 없는 한 모두 nginx 의 제한 `location` 을 지난다(**코드를 읽었다**와 위 표를 맞댄 **어림**).
  이 토큰 경로만은 아래 ADR 0024 목록의 "`proxy_pass` 에 URI 를 붙여 정규화한 경로를 넘긴다"를 따르지
  않는다. 정규식 `location` 의 `proxy_pass` 에는 URI 를 붙일 수 없기 때문이다(nginx 문서의 규칙으로 안다.
  **어림**). 토큰 경로를 `/portal/` 접두 `location` 에 두고 `map` 으로 그 경로에만 빈도 제한의 열쇠를
  주는(그 밖에는 빈 열쇠) 배치는 재지 않았다.

수치 후보의 바탕(**코드를 읽었다**). 위젯 미리보기 페이지의 토큰 함수(`web/apps/portal/browser/portal.ts`
의 `tokenProviderOf`)는 토큰을 모아 두지 않고 부를 때마다 `POST /portal/sites/<이름>/token` 을 보낸다.
위젯은 요청을 보낼 때마다 그 함수를 부른다(`web/apps/widget/element/token.ts`, 토큰 수명은 120초,
`.scratch/pilot-portal/spec.md`). 부르는 자리는 질문 보내기, 승인 결정, 끊긴 실행 다시 잇기(물러서며
되풀이), 붙자마자 저장한 대화 되돌리기다(`web/apps/widget/components/pages/drivers.ts` 의 `authorize`).
그래서 사람 하나가 10초마다 질문하면 분당 6번쯤이다(**어림**). 시제품의 후보는 그 다섯 배인 분당
30번에 `burst=10 nodelay` 이고, 비교를 위해 분당 10·60번도 함께 쟀다. 그 후보로 실제 거부가 났다(위 표,
12번째 요청부터 429).

### 3. `127.0.0.1` 에만 발행한 포트와 경유 공격

**쟀다**(Engine 27.5.1·28.0.0·29.9.2 마다 userland-proxy 를 켠 때와 끈 때, 서버의 filter FORWARD 정책을
`ACCEPT`(dind 의 처음 값)와 `DROP` 으로 바꿔 가며 2회차씩. 원본은 edge-run4).

- 모든 엔진과 모드에서 서버 자신의 `127.0.0.1:3000` 은 관리 화면 대역의 200 이었다(양성 대조.
  `docker port` 가 `3000/tcp -> 127.0.0.1:3000`). 이웃 n1 에서 서버의 IPv4·IPv6 `:3000` 과 발행하지 않은
  `:8000` 은 모두 refused 였다. 서버의 주소로 거는 길로는 닿지 않는다.
- 경유 공격은 이웃이 서버를 경유지(게이트웨이)로 삼아 서버의 바깥 주소가 아닌 목적지로 바로 거는
  길이다. A 는 이웃 n1 이 안쪽 대역 `172.30.0.0/24` 를 서버로 보내는 경로를 더하고 컨테이너 주소로 건다.
  B 는 이웃 n3 이 자기 루프백의 local 경로를 지우고 `127.0.0.1` 을 서버로 보내(`route_localnet=1`)
  서버의 `127.0.0.1:3000` 으로 건다. 회차의 표지는 공격 패킷이 서버의 eth0 에 닿은 것(raw PREROUTING
  맨 앞에 넣은 셈 전용 규칙의 패킷 수)이다. 막힌 회차에는 그 사이 패킷 수가 늘어난 DROP 규칙을 적었다.

| 목적지 | 27.5.1 | 28.0.0 | 29.9.2 |
|---|---|---|---|
| A. 관리 화면 컨테이너 `:3000`(`127.0.0.1` 에만 발행) | **닿는다**(8/8, 정책과 상관없이) | 막힌다(8/8). raw `-d <그 컨테이너> ! -i br-<id> -p tcp --dport 3000 -j DROP` 이 셌다 | 막힌다(8/8). raw `-d <그 컨테이너> ! -i br-<id> -j DROP` 이 셌다 |
| A. serve 컨테이너 `:8000`(발행 안 함) | 정책 `ACCEPT` 면 **닿는다**(4/4), `DROP` 이면 막힌다(4/4, 정책의 DROP 이 셌다) | 막힌다(8/8). filter `DOCKER` 의 `! -i br-<id> -o br-<id> -j DROP` 이 셌다 | 막힌다(8/8). raw, 위와 같은 꼴 |
| A. 프록시 컨테이너 `:8443`(모든 주소의 443 으로 발행) | 닿는다(8/8) | 막힌다(8/8). raw `--dport 8443` 의 DROP | 막힌다(8/8). raw |
| B. 서버의 `127.0.0.1:3000` | **닿는다**(8회차 가운데 6, 관리 화면의 200) | 막힌다(8/8). raw `-d 127.0.0.1/32 ! -i lo -p tcp --dport 3000 -j DROP` 이 셌다 | 막힌다(8/8). 같은 규칙 |
| 양성 대조. 보호를 끈 네트워크(`gateway_mode_ipv4=nat-unprotected`)의 컨테이너 `:8000` | 그 모드가 없어 돌지 않음 | 닿는다(2/2) | 닿는다(2/2) |

- 27.5.1 에서는 `127.0.0.1` 에만 발행해도 같은 L2 의 이웃이 경유로 관리 화면에 닿는다. 27.5.1 의
  `iptables-save -c` 에는 raw 규칙이 없고, filter `DOCKER` 사슬의 `-A DOCKER -d <관리 화면> ! -i br-<id>
  -o br-<id> -p tcp --dport 3000 -j ACCEPT` 이 호스트 주소(`127.0.0.1`)를 가리지 않아 A 의 패킷을 셌다.
  그래서 FORWARD 정책을 `DROP` 으로 바꿔도 닿았다. B 는 nat `-A DOCKER -d 127.0.0.1/32 ! -i br-<id> -p
  tcp --dport 3000 -j DNAT --to-destination <관리 화면>:3000` 이 셌다(원본 raw.log 의 마지막 "경유 공격
  뒤의 iptables-save -c").
- 27.5.1 의 B 에서 닿지 않은 두 회차는 모드마다의 첫 회차였다(시간 초과, 늘어난 DROP 없음). 서버가
  n3 과 처음 주고받는 회차였고, 까닭은 재지 않았다.
- 28.0.0 과 29.9.2 는 두 모드와 두 정책 모두에서 A 와 B 를 다 막았다. 막은 규칙의 꼴은 판마다 다르다.
  같은 경유 경로로 보호를 끈 네트워크의 컨테이너에는 닿아(양성 대조), 막은 것은 경로가 아니라 그
  규칙이다.
- Docker 문서 원문(**원문을 받아 대 봤다**). 원문은 docker/docs 저장소 `main` 의 커밋
  `9634e73c0931b93cea6e20477b240fbf8cd68b2b` 에서 받은
  `content/manuals/engine/network/port-publishing.md` 와 Engine 28 릴리스 노트다.
  - port-publishing: 28.0.0 보다 오래된 판에서는 같은 L2 구간의 호스트가 localhost 에 발행한 포트에
    닿는다고 적고 moby/moby#45610 을 든다("hosts within the same L2 segment ... can reach ports
    published to localhost"). 그리고 `nat` 모드 네트워크에서는 루프백에 발행한 포트에 원격 호스트가
    닿지 못한다고, 원격 호스트는 기본으로 컨테이너 주소에 바로 닿지 못하고 호스트 주소에 발행한 포트로만
    닿는다고 적는다.
  - 릴리스 노트 28.0.0(2025-02-19): 원격 호스트가 발행한 포트로 컨테이너에 바로 닿던 보안 문제와,
    이웃 호스트가 루프백 주소에 발행한 포트에 닿던 보안 문제를 고쳤다(둘 다 moby/moby#49325). 발행하지
    않은 컨테이너 포트로의 직접 경유 접근을 `DOCKER` 사슬에서 막는다(moby/moby#48724).
  - 릴리스 노트 28.0.2: `CONFIG_IP_NF_RAW` 가 없는 커널을 위해 `DOCKER_INSECURE_NO_IPTABLES_RAW=1` 을
    더했고, 그 값을 쓰면 `127.0.0.1` 에 발행한 포트에 로컬 네트워크의 호스트가 경유로 닿을 수 있다고
    적는다.
  - 릴리스 노트 28.3.3: CVE-2025-54388. firewalld 를 다시 읽으면 루프백에만 발행한 포트도 로컬
    네트워크에서 닿을 수 있던 문제를 고쳤다(moby/moby#50506).
- 최소 판으로 읽을 수 있는 것. 잰 것으로는 28.0.0 부터 같은 L2 의 이웃이 `127.0.0.1` 에만 발행한 관리
  화면에 경유로 닿지 못하고, 27.5.1 은 닿는다(**쟀다**). firewalld 를 쓰는 서버는 원문으로 28.3.3 부터다
  (**원문을 받아 대 봤다**, 재지 않았다). 28.0.2 이후의 `DOCKER_INSECURE_NO_IPTABLES_RAW=1` 은 원문대로면
  그 보호를 끈다(재지 않았다).

### 4. 잘못 발행한 포트

**쟀다**(Engine 27.5.1·28.0.0·29.9.2, userland-proxy 켬, 엔진마다 1회차. 원본은 edge-run4). 시제품
배치에서 이웃 n1 이 서버의 `:8000` 에 걸면 refused 였다. `compose.wrong-port.yml`(serve 에
`"8000:8000"`)을 덧씌워 다시 띄우면 `docker port` 가 `8000/tcp -> 0.0.0.0:8000` 과 `8000/tcp ->
[::]:8000` 을 보였고, n1 이 평문 HTTP 로 serve 의 200 을 받았다. 세 엔진이 같았다. 항목 3 의 보호는
발행한 포트를 막지 않는다. `ports` 에 호스트 주소를 적지 않은 뒷단은 서버의 주소로 닿는 손님에게 TLS
도 빈도 제한도 없이 열린다(같은 L2 의 이웃에서 쟀다).

### 5. TLS, HSTS, 80, 404, root 가 아닌 nginx

**쟀다**(Engine 29.9.2, userland-proxy 켬, 갈래마다 1회차. 원본은 edge-run5 와, 프로세스의 사용자를
다시 잰 edge-run6). 설정은 이 폴더의 `nginx/edge.conf` 와 `nginx/nginx.conf` 그대로다.

- 자체 서명 인증서. 서버(dind, OpenSSL 3.5.9) 안에서 아래 한 줄로 만들었다. 이름은 `CN=edge.test`,
  SAN 은 `DNS:edge.test`, `IP:10.77.0.10`, `IP:127.0.0.1`, `IP:fd00:77::10`, `IP:::1` 이었다. 키는
  `chgrp 101` 과 `chmod 640` 으로 `0:101 640`, 인증서는 `0:0 644` 다.

```
openssl req -x509 -newkey rsa:2048 -nodes -days 30 -keyout privkey.pem -out fullchain.pem -subj /CN=edge.test -addext subjectAltName=DNS:edge.test,IP:10.77.0.10,IP:127.0.0.1,IP:fd00:77::10,IP:::1
```

- 이웃 n1 이 443 에 TLS 로 걸면 TLSv1.3 이었고, 받은 인증서의 SHA-256 지문이 만든 인증서와 같았다(그
  인증서만 믿는 설정으로 이름까지 검증했다). 443 에 평문 HTTP 로 걸면 nginx 의 400("The plain HTTP
  request was sent to HTTPS port")이었고 뒷단으로 넘기지 않았다.
- HSTS. `Strict-Transport-Security: max-age=31536000` 이 200·404·429 응답에 모두 있었다(`always`).
- 80. GET 넷(`/portal/?a=1`, `/end-user/runs`, `/.well-known/acme-challenge/x`, `/`)과 POST 하나
  (`/end-user/runs`)가 모두 308 이었고, `Location` 이 같은 경로와 질의의 `https://edge.test…` 였다.
  뒷단이 답한 것은 없었다. ACME 확인 경로도 넘기기만 한다.
- 경로. 넘기는 10가지는 모두 그 뒷단의 200 이었고 뒷단이 받은 경로가 기대와 같았다. 404 20가지는 모두
  nginx 의 404 였고 뒷단의 표지가 없었다. 기대와 다른 것은 없었다.
  - 넘긴 것: `GET /`, `GET /?site=demo&`, `GET /portal/`, `GET /portal/health`,
    `GET /portal/sites/demo/acknowledgement`(위젯 미리보기 페이지), `GET /widget`,
    `GET /widget?agent=calc&`, `GET /widget/element.js`(위젯), `POST /end-user/runs`,
    `GET /runs/../end-user/x`(serve 가 `/end-user/x` 로 받았다)
  - 404: `/runs`, `/health`, `/docs`, `/openapi.json`, `/admin`, `/api/runs`, `/plugins`, `/widgetx`,
    `/widget-admin`, `/end-userx/a`, `/end-user`, `/portal`, `/portalx`, `/END-USER/runs`, `/Widget`,
    `/end-user/../runs`, `/end-user/%2e%2e/runs`, `/portal/../runs`, `/widget/../admin`,
    `/.well-known/acme-challenge/x`
- 넘기는 헤더. 이웃이 `X-Forwarded-For: 203.0.113.9`, `X-Forwarded-Proto: http`, `Host: edge.test` 를
  실어 보내면 뒷단은 `X-Forwarded-For: 10.77.0.21`(이웃의 주소), `X-Forwarded-Proto: https`,
  `Host: edge.test`, HTTP/1.1 로 받았다.
- 본문 상한(`client_max_body_size 1m`). 512KiB 는 뒷단이 그 바이트 수 그대로 받았고, 2MiB 는 nginx 의
  413 이었다.
- SSE. 뒷단이 0.5초 간격으로 낸 data 줄 넷이 `X-Accel-Buffering: no` 가 있으면 0.01·0.51·1.01·1.51초에
  닿았고, 그 헤더가 없으면(대조) 넷 모두 1.51초에 한꺼번에 닿았다. 시제품 설정은 버퍼링을 끄지 않으므로
  뒷단의 그 헤더에 기댄다.
- 키 파일의 권한과 `nginx -t`(서비스 정의 그대로 `compose run` 으로 돌렸다).

| 사용자 | 키 파일 | `nginx -t` |
|---|---|---|
| uid 101(서비스 정의 그대로) | `root:root 600` | 키를 읽지 못한다(Permission denied) |
| uid 101 | `root:101 640` | 지난다 |
| uid 101 | `101:101 600` | 지난다 |
| root(`--user 0:0`), `cap_drop: [ALL]` 그대로 | `root:root 600` | 실패. 임시 폴더의 소유자를 worker 사용자로 바꾸는 `chown` 이 `Operation not permitted` |
| root 에 `CHOWN` 을 더함 | `root:root 600` | 지난다 |

- uid 101 과 `cap_drop: [ALL]` 로 띄운 파이썬 소켓이 컨테이너 안의 80·443 에 바로 묶였다(컨테이너 안의
  `net.ipv4.ip_unprivileged_port_start=0`). nginx 로 80·443 에 묶어 보지는 않았다.
- 프록시 컨테이너(공식 `nginx:1.30.6-alpine`, `user: "101:101"`, `read_only: true`, `cap_drop: [ALL]`,
  `/tmp` tmpfs)의 프로세스 18개(master 하나와 worker)가 모두 실제·유효 uid 101 이었다. 서버 커널의
  `/proc/<pid>/status` 로 봤다. dind 의 `docker top` 은 BusyBox `ps` 를 불러 첫 칸이 UID 가 아니라 PID
  여서, edge-run5 의 이 회차는 PID 를 적었고 결론에 쓰지 않았다.
- `nginxinc/nginx-unprivileged:1.30.6-alpine` 에 `edge.conf` 만 얹은 배치(`compose.unprivileged.yml`)도
  같은 인증서로 위젯 미리보기 페이지의 200 을 냈고 프로세스가 모두 uid 101 이었다.
- edge-run6 은 이 항목 전체를 다시 돌았고(19회차 모두 측정) 위의 다른 결과도 edge-run5 와 같았다.
- `edge.conf` 의 `listen [::]:8443 ssl` 과 `listen [::]:8080` 은 안쪽 네트워크가 IPv4 뿐인 배치에서도
  nginx 를 멈추지 않았다(그 배치의 회차 0 이 모든 실행에서 섰다).

### 6. 호스트 폴더의 쓰기 권한

**쟀다**(Engine 29.9.2, 갈래마다 1회차. 원본은 edge-run5). 컨테이너를 고정 uid `10001:10001` 로 띄워
`/data` 에 붙인 것에 파일을 만들어 봤다. 표지는 컨테이너 안의 `id -u` 가 10001 이고, 실패한 회차는 stderr
에 `Permission denied` 가 있는 것이다.

| 붙인 것 | 컨테이너가 본 `/data` | 10001 이 쓰나 |
|---|---|---|
| root 가 만든 호스트 폴더(`mkdir`) | `0:0 755` | 못 쓴다 |
| 없는 호스트 경로(Docker 가 만든다) | `0:0 755` | 못 쓴다 |
| 호스트에서 `chown 10001:10001` 한 폴더 | `10001:10001 755` | 쓴다. 새 파일은 호스트에서 `10001:10001` |
| 빈 named volume, 이미지에 `/data` 없음 | `0:0 755` | 못 쓴다 |
| 빈 named volume, 이미지의 `/data` 가 10001 소유 | `10001:10001 755` | 쓴다(처음 붙을 때 이미지의 소유자를 물려받았다) |
| root 컨테이너가 먼저 붙여 쓴 named volume, 그 뒤 이미지의 `/data` 가 10001 소유 | `0:0 755` | 못 쓴다 |

- 호스트 폴더를 붙이면 Docker 는 소유자를 바꾸지 않는다. 운영자가 미리 그 uid 로 `chown` 해야 쓴다. 없는
  경로는 Docker 가 root 소유로 만들어 그대로 못 쓴다.
- 빈 named volume 은 이미지의 `/data` 가 10001 소유일 때 그 소유자로 붙었다. root 컨테이너가 먼저 붙여
  파일을 쓴 volume 은 그 뒤 그 이미지로 붙여도 root 소유로 남았다. 먼저 붙은 컨테이너의 이미지에 경로가
  없던 것과 volume 에 이미 파일이 있던 것 가운데 무엇이 갈랐는지는 가르지 않았다.

### 7. 안쪽 IPv6 를 켠 배치의 IPv6 경유 공격

**쟀다**(Engine 27.5.1·28.0.0·28.3.3·29.9.2 마다 userland-proxy 를 켠 때와 끈 때, 서버의 ip6tables filter
FORWARD 정책을 처음 값과 다른 값으로 바꿔 가며 대상마다 2회차. 원본은 28.3.3 이 edge-run7, 나머지 셋이
edge-run8). 배치는 `compose.yml`, `compose.probe.yml`, `compose.ipv6.yml`(안쪽 `fd00:30::/64`),
`compose.ipv6-listen.yml`(관리 화면과 serve 대역이 `::` 에도 듣는다)을 겹친 것이다. 경유 공격은 3절의 A 를
IPv6 로 옮긴 것이다. 이웃 n1 이 `fd00:30::/64` 를 서버의 바깥 주소 `fd00:77::10` 으로 보내는 경로를 더하고
(`ip -6 route get` 이 `via fd00:77::10`), 컨테이너의 IPv6 주소로 바로 건다. 회차의 표지는 공격 패킷이 서버의
eth0 에 닿은 것(ip6tables raw PREROUTING 맨 앞에 넣은 셈 전용 규칙의 패킷 수)과, 그 대상이 IPv6 로 답한다는
양성 대조(서버 자신에서 그 컨테이너의 IPv6 주소로 걸어 그 대역의 200)다. 막힌 회차에는 그 사이 패킷 수가
늘어난 ip6tables 의 DROP 규칙을 적었다.

- 회차 0(배치 띄우기)은 네 엔진과 두 모드 모두 섰다. 안쪽 네트워크의 `EnableIPv6` 가 `true` 이고 관리
  화면·serve·프록시가 `fd00:30::/64` 의 주소를 받았다. 그때 서버의 IPv6 포워딩은 1, ip6tables filter
  FORWARD 정책은 네 엔진 모두 `DROP` 이었다(IPv4 의 처음 값 `ACCEPT` 와 다르다. 한계 절). 관리 화면의
  `docker port` 는 `3000/tcp -> 127.0.0.1:3000` 하나였다.
- 양성 대조. 서버 자신에서 세 컨테이너의 IPv6 주소로 걸면 모든 엔진과 모드에서 그 대역의 200 이었다
  (프록시는 `/portal/health` 를 위젯 미리보기 페이지 대역까지 넘겼다). 서버 자신의 `127.0.0.1:3000` 은
  관리 화면의 200 이었다.
- 서버의 주소로 거는 길. 이웃 n1 에서 서버의 IPv6 `:3000` 과 `:8000` 은 네 엔진과 두 모드 모두
  refused 였다.

| 경유 목적지(IPv6) | 27.5.1 | 28.0.0 | 28.3.3 | 29.9.2 |
|---|---|---|---|---|
| 관리 화면 컨테이너 `:3000`(`127.0.0.1` 에만 발행) | 정책 `ACCEPT` 면 **닿는다**(4/4), `DROP` 이면 막힌다(4/4, 정책의 DROP 이 셌다) | 막힌다(8/8). filter `DOCKER` 의 `! -i br-<id> -o br-<id> -j DROP` 이 셌다 | 막힌다(8/8). raw `-d <그 컨테이너>/128 ! -i br-<id> -j DROP` 이 셌다 | 막힌다(8/8). 28.3.3 과 같은 꼴의 raw |
| serve 컨테이너 `:8000`(발행 안 함) | 정책 `ACCEPT` 면 **닿는다**(4/4), `DROP` 이면 막힌다(4/4, 정책의 DROP) | 막힌다(8/8). 위와 같은 filter 규칙 | 막힌다(8/8). 같은 꼴의 raw | 막힌다(8/8). 같은 꼴의 raw |
| 프록시 컨테이너 `:8443`(모든 주소의 443 으로 발행) | **닿는다**(8/8, 정책과 상관없이) | 막힌다(8/8). raw `-d <그 컨테이너>/128 ! -i br-<id> -p tcp -m tcp --dport 8443 -j DROP` 이 셌다 | 막힌다(8/8). 포트를 가리지 않는 raw | 막힌다(8/8). 같은 꼴의 raw |
| 양성 대조. 보호를 끈 네트워크(`gateway_mode_ipv6=nat-unprotected`)의 컨테이너 `:8000` | 그 모드가 없어 돌지 않음 | 닿는다(4/4) | 닿는다(4/4) | 닿는다(4/4) |

- 칸의 수는 두 모드 × 정책 두 값 × 2회차다(대조는 모드와 정책마다 1회차). 막은 회차마다 그 규칙의 패킷
  수가 3 늘었고, 늘어난 DROP 규칙은 회차마다 하나였다. 28.0.0 이후는 정책을 `ACCEPT` 로 바꾼 회차도 같은
  규칙이 셌다.
- 27.5.1. 모든 주소에 발행한 프록시의 `:8443` 에는 IPv6 FORWARD 정책을 `DROP` 으로 둔 채로도 경유로
  닿았다. 공격 뒤의 `ip6tables-save -c` 에서 filter `DOCKER` 의 `-A DOCKER -d <프록시>/128 ! -i br-<id> -o
  br-<id> -p tcp -m tcp --dport 8443 -j ACCEPT` 의 패킷 수가 두 모드 모두 4(닿은 회차 수)였다(원본
  raw.log). 관리 화면과 serve 는 정책이 갈랐다(`ACCEPT` 면 닿고 `DROP` 이면 정책의 DROP 이 셌다). 닿은
  대역이 본 상대 주소는 이웃의 주소 `fd00:77::21` 그대로였다. IPv4(3절)와 견주면 프록시와 serve 는 같은
  모양이고 관리 화면이 다르다. IPv4 에서는 `127.0.0.1` 발행의 허용 규칙이 호스트 주소를 가리지 않아
  정책과 상관없이 닿았는데, IPv6 의 `ip6tables-save` 에는 관리 화면의 허용 규칙이 없었다(관리 화면은
  IPv6 쪽 발행이 없다).
- 28.0.0 은 관리 화면과 serve 를 filter `DOCKER` 의 DROP 으로, 프록시를 `--dport 8443` 이 붙은 raw DROP
  으로 막았다. IPv4(3절)에서 관리 화면을 막은 것은 `--dport 3000` 이 붙은 raw 였는데, IPv6 에서는 발행 안
  한 serve 와 같은 규칙이 셌다. 관리 화면은 IPv6 쪽 발행이 없다(위 `docker port`).
- 28.3.3 과 29.9.2 는 세 대상을 모두 컨테이너의 IPv6 주소마다 포트를 가리지 않는 raw DROP 으로 막았다.
  IPv4(3절, 9절)와 같은 꼴이다.
- 보호를 끈 네트워크의 대역은 상대 주소를 이웃의 주소 `fd00:77::21` 그대로 봤고 늘어난 DROP 은 없었다.
  같은 경유 경로가 통하므로 28.0.0 이후에서 막은 것은 경로가 아니라 위 규칙이다. 27.5.1 에서는 이 대조가
  돌지 않았지만(`unknown gateway mode nat-unprotected`), 같은 경로로 프록시와(정책 `ACCEPT` 에서) 관리
  화면·serve 에 닿은 회차가 경로가 통한다는 것을 보인다.

### 8. 443 과 80 을 IPv4 에만 발행한 배치

**쟀다**(Engine 29.9.2·28.3.3 마다 userland-proxy 를 켠 때와 끈 때. 원본은 edge-run9). 안쪽 네트워크는
시제품 그대로 IPv4 뿐이고, `compose.v4-publish.yml` 이 프록시의 `ports` 를 `!override` 로
`"0.0.0.0:443:8443"`, `"0.0.0.0:80:8080"` 두 줄로 바꾼다. 배치는 `docker port ri-edge-proxy-1` 이
`8080/tcp -> 0.0.0.0:80` 과 `8443/tcp -> 0.0.0.0:443` 두 줄뿐일 때 떴다고 센다. 그 배치에서 1절의 갈래를
1절과 같은 표지(요청의 rid, 프록시 접근 기록의 `$remote_addr` 와 뒷단이 받은 `X-Forwarded-For` 가 같다)로
갈래마다 2회차 돌았다(회차 이름은 `1.<시나리오>.443·80 IPv4 에만 발행.…`). 닿지 않은 IPv6 회차는 그
배치에서 다시 띄운 서버 호스트의 `[::]` 대조 포트에 이웃 n1·n2 가 모두 닿았을 때만 센다(서버 자신의
회차는 서버 자신이 `[::1]` 과 바깥 IPv6 의 대조 포트에 닿았을 때만). `!override` 가 앞 파일의 `ports` 를
잇지 않고 바꾸는 것은 28.3.3 의 Compose 2.39.2 로 `docker compose -f compose.yml -f compose.probe.yml -f
compose.v4-publish.yml config --format json` 을 쳐 프록시의 `ports` 가 `0.0.0.0` 의 443·80 두 줄뿐인 것을
**손으로 봤다**(프로브는 배치마다 `docker port` 로 같은 것을 본다).

- 배치. 두 엔진과 두 모드 모두 `docker port ri-edge-proxy-1` 이 위의 두 줄뿐이었다.
- 서버 안의 443·80. 서버(dind) 안에서 듣는 소켓(BusyBox `netstat -ltn`), docker-proxy 의 인자(`ps -o
  args`), nat 표의 DNAT 규칙(`iptables-save -t nat`, `ip6tables-save -t nat`)을 봤다. 같은 시나리오에서
  시제품 배치(443·80 을 모든 주소에 발행)를 먼저 같은 방법으로 봤고(관찰의 대조), 회차는 같은 방법이
  IPv4 쪽 443 을 볼 때만 센다. 두 엔진의 값이 같았다.

| 서버 안에서 본 것 | 시제품 배치, userland-proxy 켬 | 시제품 배치, 끔 | IPv4 에만 발행, 켬 | IPv4 에만 발행, 끔 |
|---|---|---|---|---|
| 듣는 소켓 | `0.0.0.0:80`, `0.0.0.0:443`, `:::80`, `:::443` | `0.0.0.0:80`, `0.0.0.0:443` | `0.0.0.0:80`, `0.0.0.0:443` | `0.0.0.0:80`, `0.0.0.0:443` |
| docker-proxy | 80·443 마다 `-host-ip 0.0.0.0` 과 `-host-ip ::` 하나씩(넷) | 없음 | 80·443 마다 `-host-ip 0.0.0.0` 하나씩(둘) | 없음 |
| DNAT(`--dport 80`·`443`) | iptables 에 둘, ip6tables 에 없음 | 같다 | 같다 | 같다 |

- 1절의 갈래를 이 배치에서 다시 돈 것과 80. 두 엔진의 값이 같았다(갈래마다 2회차, 같은 갈래의 회차는
  모두 같은 값).

| 요청 | userland-proxy 켬 | userland-proxy 끔 |
|---|---|---|
| 이웃 n1·n2 → 서버의 IPv4 `:443` | 보낸 이웃의 주소(`10.77.0.21`, `10.77.0.22`) | 같다 |
| 이웃 n1·n2 → 서버의 IPv6 `:443` | 닿지 않음(refused) | 같다 |
| 이웃 n1·n2 → 서버의 IPv6 `:80` | 닿지 않음(refused) | 같다 |
| 이웃 n1 → 서버의 IPv4 `:80`(대조) | nginx 의 308(`Location: https://edge.test/portal/`) | 같다 |
| 서버 자신 → `127.0.0.1:443` | 안쪽 게이트웨이 `172.30.0.1` | 같다 |
| 서버 자신 → `[::1]:443` | 닿지 않음(refused) | 같다 |
| 서버 자신 → 자기 바깥 IPv4 `10.77.0.10:443` | 자기 주소 `10.77.0.10` | 안쪽 게이트웨이 `172.30.0.1` |
| 서버 자신 → 자기 바깥 IPv6 `[fd00:77::10]:443` | 닿지 않음(refused) | 같다 |

- 닿지 않은 IPv6 회차의 대조. 시나리오마다 이 배치를 띄운 뒤 서버 호스트의 `[::]:39459` 대조 포트에
  이웃 n1·n2 와 서버 자신(`[::1]`, 바깥 IPv6)이 모두 닿았다. 그래서 refused 는 IPv6 길이 끊긴 것이 아니라
  IPv6 쪽 443·80 에 아무것도 듣지 않는 것이다(위 표의 듣는 소켓).
- 1절의 시제품 배치와 견주면 바뀐 것은 userland-proxy 를 켠 때의 IPv6 갈래뿐이다. 시제품 배치에서는 이웃의
  IPv6 `:443` 과 서버 자신의 `[::1]:443`·바깥 IPv6 가 안쪽 게이트웨이 `172.30.0.1` 로 보였는데(1절), 이
  배치에서는 `-host-ip ::` 의 docker-proxy 와 `:::443` 소켓이 없고 refused 였다. 끈 때는 시제품 배치도
  IPv6 쪽에 443·80 이 없어(위 표) 1절과 같이 refused 다. IPv4 갈래의 값은 1절과 같다.
- 80 의 회차 이름은 `8.<시나리오>.ri-edge-n1→서버의 IPv6:80#n` 처럼 이웃의 컨테이너 이름을 쓴다.
- 회차 수. 시나리오마다 27회차, 넷 합 108회차가 모두 측정이었다(edge-run9).

### 9. 항목 3 을 Engine 28.3.3 에서 다시

**쟀다**(Engine 28.3.3, userland-proxy 를 켠 때와 끈 때, 서버의 filter FORWARD 정책 `ACCEPT`·`DROP`
마다 2회차. 원본은 edge-run7. 방법과 표지는 3절 그대로다). 3절이 재지 않은 28.0.0 과 29.9.2 사이의 판
가운데 firewalld 의 문제를 고친 28.3.3(3절의 원문 대조)을 잰다.

- 두 모드에서 서버 자신의 `127.0.0.1:3000` 은 관리 화면 대역의 200 이었다(양성 대조. `docker port` 가
  `3000/tcp -> 127.0.0.1:3000`). 이웃 n1 에서 서버의 IPv4 `:3000`, IPv4 `:8000`, IPv6 `:3000` 은 모두
  refused 였다.

| 목적지 | 28.3.3(두 모드, 두 정책) |
|---|---|
| A. 관리 화면 컨테이너 `:3000`(`127.0.0.1` 에만 발행) | 막힌다(8/8). raw `-d <그 컨테이너>/32 ! -i br-<id> -j DROP` 이 셌다 |
| A. serve 컨테이너 `:8000`(발행 안 함) | 막힌다(8/8). 같은 꼴의 raw 규칙 |
| A. 프록시 컨테이너 `:8443`(모든 주소의 443 으로 발행) | 막힌다(8/8). 같은 꼴의 raw 규칙 |
| B. 서버의 `127.0.0.1:3000` | 막힌다(8/8). raw `-d 127.0.0.1/32 ! -i lo -p tcp -m tcp --dport 3000 -j DROP` 이 셌다 |
| 양성 대조. 보호를 끈 네트워크(`gateway_mode_ipv4=nat-unprotected`)의 컨테이너 `:8000` | 닿는다(2/2) |

- 막은 회차마다 그 규칙의 패킷 수가 3 늘었다(3초 안에 보낸 SYN 과 재전송). FORWARD 정책을 `DROP` 으로
  바꾼 회차도 그 raw 규칙만 늘었고 정책의 패킷 수는 늘지 않았다(raw 가 먼저 버렸다).
- 막은 규칙의 꼴은 29.9.2 와 같다(컨테이너 주소마다 포트를 가리지 않는 raw DROP). 28.0.0 의 꼴(관리 화면은
  `--dport 3000` 이 붙은 raw, serve 는 filter `DOCKER` 의 DROP)과 다르다.

## ADR 0024 가 프록시에 요구하는 규칙(재지 않고 적은 목록)

`docs/adr/0024-*.md` 와 `docs/adr/0050-*.md` 에서 옮긴다(**코드를 읽었다**가 아니라 문서를 읽었다).

- 443 은 TLS 만, HSTS 를 붙인다. 80 은 443 으로 넘기기만 한다.
- `location` 허용 목록 밖은 `return 404`. 위젯 미리보기 페이지 쪽은 `= /` 와 `/portal/` 둘뿐이다(ADR 0050).
- `proxy_pass` 에 URI 를 붙여 정규화한 경로를 넘긴다. 리눅스에서 `location` 은 대소문자를 가른다.
- `X-Forwarded-For` 와 `X-Forwarded-Proto` 는 받은 값을 잇지 않고 덮어쓴다.
- `client_max_body_size` 는 사이트 파일의 요청 크기보다 크게 두어 파이썬의 422 가 답하게 한다.
- 슬래시 없는 위젯 경로는 `location =` 로 받는다. `proxy_http_version 1.1`.
- SSE 는 FastAPI 가 붙이는 `X-Accel-Buffering: no` 덕에 흐른다. keepalive 15초가
  `proxy_read_timeout` 60초 안이다.
- TLS 인증서는 운영자가 준다. 토큰 끝점의 빈도 제한은 프록시가 맡는다(ADR 0050).

## 한계(dind 로 흉내 낸 것과 실제 서버의 차이)

- 바깥 "LAN" 은 Docker Desktop VM 안의 브리지다. 실제 스위치가 아니고, 그 VM 의 iptables(br_netfilter)를
  지난다.
- 서버가 컨테이너라 세 엔진 판이 모두 같은 커널(Docker Desktop 의 WSL2 커널)과 그 nf_tables 위에서 돈다.
- dind 안에서는 IP 포워딩이 처음부터 켜져 있어 Docker 가 filter FORWARD 정책을 `DROP` 으로 바꾸지
  않고 `ACCEPT` 로 둔다(세 엔진 모두 회차 0 이 `ip_forward=1`, `forward_policy=ACCEPT` 를 적었다). 실제
  서버에서는 Docker 가 포워딩을 켜며 `DROP` 으로 바꾼다고 알려져 있다(**어림**). 그래서 항목 3 은 정책을
  두 값으로 바꿔 가며 잰다.
- IPv6 는 처음 값이 달랐다. 항목 7 의 회차 0 에서 네 엔진 모두 ip6tables filter FORWARD 정책이 `DROP`
  이었다(안쪽 IPv6 배치를 띄운 뒤에 읽었고, 띄우기 전의 값은 보지 않았다). 그래서 항목 7 도 그 정책을
  `ACCEPT` 로 바꾼 회차를 함께 돈다. 실제 서버의 값은 재지 않았다.
- dind 의 `docker top` 은 BusyBox `ps` 를 불러 표의 꼴이 리눅스 배포판의 것과 다르다(항목 5).

## 재지 못한 것

- rootless Docker. 포트 발행이 rootlesskit 을 거쳐 프록시가 보는 주소와 경유 공격의 길이 다를 수 있다.
- firewalld·ufw 가 있는 서버. 28.3.3 이 고친 CVE-2025-54388(firewalld 를 다시 읽으면 루프백에만
  발행한 포트가 열리던 문제)은 원문으로만 봤다.
- `DOCKER_INSECURE_NO_IPTABLES_RAW=1` 을 준 28.0.2 이후, nftables 방화벽 뒷단, 데몬을 다시 켠 뒤.
- 잰 네 판(27.5.1, 28.0.0, 28.3.3, 29.9.2) 밖의 판. 28.3.3 은 항목 3·7·8 만(9·7·8절) 쟀고, 항목 8 은
  28.3.3 과 29.9.2 만 쟀다. 28.0.0 과 28.3.3 사이, 28.3.3 과 29.9.2 사이의 판과 27.5.1 보다 오래된 판은
  재지 않았다.
- 실제 뒷단 이미지(serve, 관리 화면, 위젯, 위젯 미리보기 페이지). 뒷단은 `stub.py` 다. 실제 뒷단이
  `::` 에도 묶는지는 보지 않았다.
- 실제 스위치와 서로 다른 커널. 세 엔진이 모두 Docker Desktop 의 WSL2 커널 위에서 돈다.
- 손님이 NAT(회사망, 통신사의 CGNAT) 뒤에 있으면 여러 사람이 한 주소로 보인다. 이 배치에서는 재지
  않았고, 주소별 빈도 제한이 그 사람들을 한 통에서 센다는 것은 **어림**이다.
- 항목 2·5·6 은 Engine 29.9.2(userland-proxy 켬)에서만 쟀다. IPv6 손님이 한 통을 같이 쓰는 회차도
  29.9.2 에서만 돌았다. 다른 엔진에서는 항목 1 이 같은 주소(`172.30.0.1`)를 보였다는 데서 미루었다
  (**어림**).
- 443·80 을 IPv4 에만 발행한 배치(8절)의 빈도 제한(항목 2)과 TLS·경로(항목 5), 그 배치의 27.5.1·28.0.0.
  그 배치에서 이름에 AAAA 레코드가 있을 때 손님(브라우저)이 IPv6 의 refused 뒤 IPv4 로 넘어가는지도 재지
  않았다. 8절의 손님은 주소로 바로 건 `client.py` 다.
- 항목 7 의 덧 갈래. 공인 IPv6 대역(GUA)이나 `gateway_mode_ipv6=routed` 를 쓴 안쪽 네트워크, ip6tables 를
  끈 데몬(`--ip6tables=false`), IPv6 가 꺼진 커널이나 ip6tables 가 돌지 않는 서버에서 `compose.ipv6.yml`
  배치가 뜨는지, 28.0.2 이후의 `DOCKER_INSECURE_NO_IPTABLES_RAW=1` 이 IPv6 의 raw 규칙도 끄는지. 경유
  공격 B 의 IPv6 판(목적지 `::1` 을 서버로 보내기)은 돌지 않았다. 관리 화면은 `127.0.0.1` 에만 발행해
  `[::1]` 에 발행한 것이 없다.
- 27.5.1 의 IPv6 양성 대조(보호를 끈 네트워크). 27.5.1 에는 `nat-unprotected` 가 없어 돌지 않았고
  `routed` 로 대신하지 않았다(7절).
- 항목 7 의 대역은 `stub.py` 를 `::` 에 묶어 IPv6 로 답하게 했다. 실제 뒷단이 `::` 에 묶이지 않으면 경유
  패킷이 컨테이너에 닿아도 그 포트는 답하지 않는다(재지 않았다).
- nginx 자신이 root 아닌 사용자로 80·443 에 묶는 것(파이썬 소켓으로만 봤다).
- 까닭: userland-proxy 를 끈 이중 스택에서 서버 자신의 `[::1]:443` 이 시간 초과인 것, 27.5.1 의 경유
  공격 B 에서 모드마다 첫 회차가 시간 초과인 것.
- 빈도 제한이 쉰 뒤 다시 채워지는 시각의 정밀한 값(쉰 시간에 `docker exec` 의 지연이 섞였다).
