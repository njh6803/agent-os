# admin_port_chain — 관리 화면용 nginx 리스너를 지나는 쿠키와 요청 머리

admin-login 명세가 쓰는 프로브다. ADR 0062 결정 "포트와 TLS"는 단독 배포의 프록시(nginx)가 관리 화면용 포트를 하나 더 듣고 TLS를 끝내 관리 화면으로 넘긴다고 정했다. 그 길에서 쿠키와 요청 머리가 실제로 어떻게 움직이는지를 실제 nginx, 실제 관리 화면 이미지(Next 중계), 실제 Chromium으로 잰다. 앞선 `../cookie_relay/`는 앞단을 node로 흉내 내 실제 nginx와 컨테이너 안을 "재지 못한 것"으로 남겼고, 이 프로브가 그 자리를 채운다. 결정은 하지 않고 결과만 낸다.

**지금 상태(2026-11-24)**: 같은 날 세 번 돌았다. 세 번 모두 35회차가 모두 측정이었고 종료 코드 0, 끝에 컨테이너와 네트워크가 남지 않았다. 셋의 결과(이름표로 바꾼 값)는 갱신용 번호 쿠키의 남은 초(1794~1797초)만 달랐다(손으로 봤다. 출력의 결과 절을 `diff`로 견줬다). 셋째 실행은 스크립트의 줄 바꿈만 고친 뒤의 판이고, 아래 결과는 그 실행의 것이다.

## 파일

| 파일 | 무엇 |
|---|---|
| `probe.mjs` | 측정 스크립트. 묶음을 띄우고 회차를 돌리고 내린다. 재는 것과 표지는 머리 주석이 원천이다 |
| `compose.yaml` | 묶음. `serve`(대역), `admin`(실제 이미지), `proxy`(후보 설정), `proxy_control`(대조 설정). 배포 파일이 아니다 |
| `nginx/nginx.conf` | 두 nginx의 주 설정. 배포의 `proxy/nginx.conf`에 접근 기록의 꼴(`probe`) 하나를 더했다 |
| `nginx/candidate/site.conf` | 후보 설정. 관리 화면용 TLS 리스너(안쪽 9443)와 방문자용 리스너 자리(안쪽 8443, 페이지 하나) |
| `nginx/control/site.conf` | 대조 설정. 관리 화면용 리스너가 `X-Forwarded-For`를 덧붙이고 `X-Real-IP`를 적지 않는다 |
| `serve_stub.py` | `serve` 자리의 대역(표준 라이브러리). 받은 머리와 TCP 상대를 적고 쿠키 둘을 심고 지운다. 같은 파일의 `client`는 네트워크 안에서 프록시에 한 번 건다 |
| `compose.port-shape.yaml` | 6번의 렌더에만 쓰는 조각. 띄우지 않는다 |

## 다시 돌리기

저장소 루트에서 친다.

```
node .scratch/admin-login/probes/admin_port_chain/probe.mjs
node .scratch/admin-login/probes/admin_port_chain/probe.mjs --web <의존성이 설치된 web 폴더> --out <원본 기록을 둘 폴더>
```

- 필요한 것: 도는 Docker 데몬과 이미지 셋(`nginx:alpine`, `agent-os-e2e/agent-os-admin:0.1.0-rc.1`, `python:3.12-slim-trixie`). compose의 `pull_policy: never`라 없으면 내려받지 않고 멈춘다. `web/`의 의존성(Playwright와 그 Chromium. `cookie_relay`처럼 `createRequire`로 쓴다), `openssl`(자체 서명 인증서). 네트워크(Docker Hub, npm, PyPI)를 타지 않는다.
- 워크트리에 `web/node_modules`가 없으면 `--web`에 설치된 다른 체크아웃의 `web/`를 준다. 2026-11-24의 세 실행은 주 체크아웃의 `web/`(Playwright 1.63.0, 이 워크트리의 잠금 파일과 같은 판)를 읽기만 했다.
- 호스트 포트 다섯은 실행마다 OS가 비었다고 준 높은 번호다(80, 443, 3000, 8443을 피하고 20000 이상). 후보와 방문자 자리와 대조의 nginx 포트는 `0.0.0.0`에, 관리 화면의 직접 포트와 대역의 기록 포트는 `127.0.0.1`에 발행한다.
- 걸린 시간은 50초와 1분 47초였다(둘째와 셋째 실행, 셸의 `date`로 손으로 봤다).
- 종료 코드 0은 측정인 회차가 있고, 측정이 아닌 회차가 없고, 실행이 예외 없이 끝났고, 묶음을 다 내렸을 때뿐이다. 미리 적은 기대와 견주지는 않는다.
- 원본(대역이 받은 요청 전부, 이름표, 판, 내림의 결과)은 `--out` 폴더의 `results.json`, 컨테이너 넷의 로그는 같은 폴더의 `compose-<서비스>.log`다. 쿠키 값은 대역이 지은 무작위 글이고 비밀이 아니다. 인증서와 키도 그 폴더의 `tls/`에 남는다(이 실행만 쓰는 자체 서명).
- `--keep`은 끝에 묶음을 내리지 않고 내리는 명령을 찍는다. `--channel chromium`은 기본(headless shell) 대신 전체 Chromium으로 돈다(돌려 보지 않았다).
- 내리는 것은 이 실행의 프로젝트 이름(`aos-port-chain-<난수>`)으로 띄운 것뿐이고(`docker compose -p <그 이름> down -v --remove-orphans`), 내린 뒤 그 이름표를 단 컨테이너와 네트워크가 없는지 본다. 프로세스를 pid로 끄는 자리는 없다.

## 잰 판

Docker Engine 29.9.2(Docker Desktop, WSL2), Compose 5.6.1, nginx 1.31.6(`nginx:alpine`, 이미지 `sha256:311761ca…`), 관리 화면 이미지 `agent-os-e2e/agent-os-admin:0.1.0-rc.1`(이미지 `sha256:7a5a6a71…`, 라벨의 커밋 `6fde206d`, 안의 Next 16.3.6), Python 3.12.16(`python:3.12-slim-trixie`), Playwright 1.63.0, Chromium 153.0.8010.12(headless shell), Node v24.19.0, OpenSSL 1.1.1k, Windows 10. 스크립트가 실행 머리에 찍고 `results.json`의 `info.versions`에 남긴다.

배포 파일은 nginx 1.30.6(안정판)을 digest로 고정했다. 이 프로브는 이 PC에 있던 1.31.6(주선판)이다. 쓴 지시문이 두 판에서 같게 돈다는 것은 어림이다.

## 띄우는 것

```
Chromium·날 HTTPS ─▶ proxy :9443 (후보) ──────┐
                 ─▶ proxy :8443 (방문자 자리, 페이지 하나만 낸다)
                 ─▶ proxy_control :9443 (대조) ┼─▶ admin :3000 (실제 이미지의 Next 중계) ─▶ serve :8000 (대역)
날 HTTP          ─▶ admin :3000 직접(배포가 지금 127.0.0.1:3000에 여는 길) ┘
네트워크 안의 serve 컨테이너 ─▶ proxy :9443 (주소 변환 없는 길의 대조)
```

- 두 이름 `admin.test`와 `evil.test`는 Chromium의 `--host-resolver-rules`로 `127.0.0.1`에 맞춘다(DNS rebinding 흉내). 인증서는 두 이름을 모두 담은 자체 서명이고 브라우저는 인증서 오류를 무시한다.
- 대역이 고른 것(실제 serve가 다르게 고르면 다시 잰다): 쿠키 이름 `__Host-aos_at`, `__Host-aos_rt`, JWT 쿠키는 세션 쿠키, 갱신용 번호 쿠키는 `Max-Age=1800`, 지우는 줄은 같은 속성에 `Max-Age=0`과 1970년의 `Expires`. 경로 `/set`, `/clear`, `/page`, 그 밖은 받은 머리를 돌려준다.

## 후보 설정의 지시문과 까닭

`nginx/candidate/site.conf`의 관리 화면용 리스너다. 배포의 방문자용 리스너(`deploy/standalone/proxy/site.conf`)와 같은 지시문을 같은 까닭으로 옮긴 것이 대부분이다.

| 지시문 | 까닭 |
|---|---|
| `listen 9443 ssl` | 안쪽 8443은 이미 방문자용이다. 호스트의 기본 번호 8443이 안쪽 9443으로 오게 발행한다(`"…:8443:9443"`). 호스트 쪽과 안쪽의 같은 숫자가 다른 리스너를 가리키는 것은 명세가 이름을 정할 때 볼 자리다 |
| `ssl_certificate`, `ssl_certificate_key`, `ssl_protocols TLSv1.2 TLSv1.3` | ADR 0062가 방문자용과 같은 인증서를 쓴다고 정했다. 같은 파일을 읽는다 |
| `add_header Strict-Transport-Security … always` | 방문자용과 같다. HSTS가 포트가 아니라 이름에 걸린다는 것은 어림이다(규격을 이 세션에서 읽지 않았다) |
| `client_max_body_size 1m` | 방문자용과 같다. 관리 API의 몸 크기는 재지 않았다 |
| `proxy_http_version 1.1`, `proxy_set_header Host $host` | 방문자용과 같다. `$host`는 포트를 뗀다(결과 1) |
| `proxy_set_header X-Forwarded-For $remote_addr` | 받은 값에 덧붙이지 않고 덮는다. 클라이언트가 지어 보낸 값이 뒤로 가지 않게 한다(결과 1에서 쟀다) |
| `proxy_set_header X-Real-IP $remote_addr` | 같은 값을 한 값짜리 머리로도 준다. 로그인 기록이 어느 쪽을 읽을지 가르려고 둘 다 뒀다 |
| `proxy_set_header X-Forwarded-Proto $scheme` | 방문자용과 같다 |
| `resolver 127.0.0.11 valid=5s ipv6=off`, `resolver_timeout 2s`, `upstream … server admin:3000 resolve` | 방문자용과 같다(컨테이너를 다시 만들어도 이름을 다시 푼다) |
| `location / { proxy_pass http://up_admin/; }` | 관리 화면 전체(페이지, 정적 파일, `/api/*`)를 넘긴다. URI를 붙인 꼴이라 nginx가 정규화한 경로를 넘긴다. 허용 목록을 두지 않았다 |
| `proxy_set_header X-Probe-Hop`, `X-Probe-Remote-Addr`, `access_log … probe` | 프로브의 표지다. 후보의 일부가 아니다 |

## 표지

회차마다 재려는 상황이 실제로 났다는 것을 본다. 하나라도 없으면 그 회차는 측정이 아니고 종료 코드가 0이 아니다. 셈은 `tools/probe_kit.py`의 `Rounds`와 같은 뜻을 `probe.mjs` 안에 지었다(측정 스크립트가 node라 그 모듈을 가져오지 못한다).

- 요청이 그 nginx와 Next를 지났다: 대역이 받은 `X-Probe-Hop`이 그 설정의 이름이고, Next의 중계가 붙이는 `x-forwarded-host`가 있고, TCP 상대가 관리 화면 컨테이너의 주소다. 직접 길은 `X-Probe-Hop`이 없어야 한다.
- 그 태그의 요청이 대역에 하나만 닿았다.
- 지어 보낸 값이 nginx에 실제로 닿았다: nginx 접근 기록의 그 요청 줄에 지어 보낸 세 값이 있다. 이것이 없으면 "대역에 없다"를 "덮었다"로 읽을 수 없다.
- 브라우저가 그 요청을 실제로 보냈다: CDP의 `requestWillBeSent`에 그 태그가 있다.
- 쿠키가 실릴 수 있는 상황이었다: 그 요청 직전에 브라우저 저장소에 `admin.test`의 쿠키 둘이 있다. 이것이 없으면 "실리지 않았다"를 읽을 수 없다.
- 렌더가 그 회차의 환경으로 났다: 렌더 결과의 `PROBE_RENDER_CASE`가 그 회차의 이름이다. 실패한 렌더는 오류 글에 그 회차의 값이 있다.

결과를 본 뒤 바꾼 판정 기준은 없다.

## 결과(2026-11-24, `probe.mjs`가 쟀다)

근거의 종류. 아래 값은 모두 탐침이 결과(`facts`)에 찍은 것이다. 세 실행의 값이 같았다는 것은 손으로 봤다(위 "지금 상태"의 `diff`). "읽는다"·"뜻이다"로 끝나는 문장은 해석이고 그 대조와 갈래는 아래 절에 있다. 쿠키 값과 포트와 주소는 이름표다. 이 실행에서 안쪽 네트워크는 `172.22.0.0/16`, 안쪽 게이트웨이는 `172.22.0.1`, 관리 화면 컨테이너는 `172.22.0.3`이었다.

### 1. nginx와 Next를 지나 대역에 닿는 머리

날 HTTPS 클라이언트(node)로 `GET /api/echo`를 건 회차다. 지어 보낸 값은 `X-Forwarded-For: 203.0.113.7`, `X-Real-IP: 203.0.113.8`, `X-Forwarded-Proto: gopher`다.

| 길 | 건 자리 | 지어 보냄 | nginx의 `$remote_addr` | 대역의 `X-Forwarded-For` | 대역의 `X-Real-IP` | 대역의 `X-Forwarded-Proto` | 대역의 `x-forwarded-host` |
|---|---|---|---|---|---|---|---|
| 후보 | 호스트 `127.0.0.1` | 아니오 | 안쪽 게이트웨이 | 안쪽 게이트웨이 | 안쪽 게이트웨이 | `https` | `admin.test` |
| 후보 | 호스트 `127.0.0.1` | 예 | 안쪽 게이트웨이 | 안쪽 게이트웨이 | 안쪽 게이트웨이 | `https` | `admin.test` |
| 후보 | 호스트의 LAN 주소 | 아니오 | 안쪽 게이트웨이 | 안쪽 게이트웨이 | 안쪽 게이트웨이 | `https` | `admin.test` |
| 대조 | 호스트 `127.0.0.1` | 아니오 | 안쪽 게이트웨이 | 안쪽 게이트웨이 | 없음 | `https` | `admin.test` |
| 대조 | 호스트 `127.0.0.1` | 예 | 안쪽 게이트웨이 | `203.0.113.7, <안쪽 게이트웨이>` | `203.0.113.8` | `https` | `admin.test` |
| 직접(nginx 없음) | 호스트 `127.0.0.1` | 아니오 | (nginx 없음) | 없음 | 없음 | 없음 | `127.0.0.1:<직접 포트>` |
| 직접(nginx 없음) | 호스트 `127.0.0.1` | 예 | (nginx 없음) | `203.0.113.7` | `203.0.113.8` | `gopher` | `127.0.0.1:<직접 포트>` |
| 후보 | 네트워크 안의 serve 컨테이너 | 아니오 | serve 컨테이너 | serve 컨테이너 | serve 컨테이너 | `https` | `admin.test` |

- 지어 보낸 회차에서 nginx의 접근 기록은 세 값을 받은 그대로 적었다. 후보 설정에서는 대역에 그 값이 하나도 닿지 않았고, 대조 설정에서는 `X-Forwarded-For`가 지어 보낸 값 뒤에 덧붙여졌고 `X-Real-IP`는 그대로 닿았다. `X-Forwarded-Proto`는 두 설정 모두 `https`로 덮였다.
- 대역이 받은 `Host`는 모든 회차에서 `serve:8000`이고, TCP 상대는 모든 회차에서 관리 화면 컨테이너였다. nginx를 지난 길이든 직접 길이든 같다.
- Next가 붙인 머리는 `x-forwarded-host` 하나다. 그 값은 Next가 받은 `Host`이고, nginx가 `Host $host`로 포트를 떼어 넘기므로 nginx를 지난 길에서는 포트가 없다(`admin.test`). Next는 `X-Forwarded-For`, `X-Real-IP`, `X-Forwarded-Proto`를 더하지도 바꾸지도 않았다. 직접 길에서 지어 보낸 세 값이 그대로 대역에 닿았다.
- 호스트에서 건 요청은 `127.0.0.1`로 건 것도 LAN 주소로 건 것도 nginx에 안쪽 게이트웨이(`172.22.0.1`)로 보였다. 네트워크 안의 컨테이너가 건 요청은 그 컨테이너의 주소로 보였다.
- 날 클라이언트의 요청에는 `Origin`, `Sec-Fetch-*`, `Cookie`가 없다(보내지 않았다).

### 2. `Set-Cookie` 두 줄이 Next와 nginx를 지나는 모양

- 날 HTTPS 클라이언트가 받은 줄은 대역이 낸 줄과 줄 수(둘, 응답 머리에서도 따로 두 줄), 차례, 글자가 같았다. 심는 줄과 지우는 줄 모두다.
  - `__Host-aos_at=<at>; HttpOnly; Secure; SameSite=Strict; Path=/`
  - `__Host-aos_rt=<rt>; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=1800`
  - 지우는 줄: `<이름>=; HttpOnly; Secure; SameSite=Strict; Path=/; Max-Age=0; Expires=Thu, 01 Jan 1970 00:00:00 GMT`
- 브라우저(CDP의 `responseReceivedExtraInfo`)가 받은 줄도 대역이 낸 두 줄과 같았고 거절한 줄은 없었다. 저장소에는 `domain=admin.test`(호스트 전용), `path=/`, `httpOnly=true`, `secure=true`, `sameSite=Strict`로 들었다. JWT 쿠키는 세션 쿠키, 갱신용 번호 쿠키는 만료가 약 1800초 뒤였다.
- 지우는 두 줄을 받은 뒤 `admin.test`의 두 쿠키가 저장소에서 사라졌다. 그때 저장소에 있던 `evil.test`의 같은 이름 쿠키 둘(3의 갈래가 심은 것)은 남았다.

### 3. 다른 이름(`evil.test`, 같은 주소, 같은 포트)의 페이지

`https://admin.test:<관리 포트>`에서 쿠키를 심은 뒤의 요청이다. 페이지는 모두 그 이름으로 관리 화면용 포트에서 연 문서(`/api/page`)다.

| 페이지 → 요청 | 대역의 `Cookie` | `Sec-Fetch-Site` / `-Mode` | `Origin` | `x-forwarded-host` | 브라우저(CDP)가 실은 것과 뺀 것 |
|---|---|---|---|---|---|
| `admin.test` → 같은 출처 `fetch` GET(양성 대조) | `at(admin)`, `rt(admin)` | `same-origin` / `cors` | 없음 | `admin.test` | 둘 실음 |
| `admin.test` → 같은 출처 `fetch` POST(`text/plain`) | `at(admin)`, `rt(admin)` | `same-origin` / `cors` | `https://admin.test:<관리 포트>` | `admin.test` | 둘 실음 |
| `evil.test` → 같은 출처 `fetch` GET | 없음 | `same-origin` / `cors` | 없음 | `evil.test` | 실은 것도 뺀 것도 없음 |
| `evil.test` → 같은 출처 `fetch` POST(`text/plain`) | 없음 | `same-origin` / `cors` | `https://evil.test:<관리 포트>` | `evil.test` | 실은 것도 뺀 것도 없음 |
| `evil.test` → `https://admin.test:<관리 포트>`로 `fetch` GET(`no-cors`, `credentials: "include"`) | 없음 | `cross-site` / `no-cors` | 없음 | `admin.test` | 둘 뺌(`SchemefulSameSiteStrict`) |
| 갈래: `evil.test`에서 `/api/set`을 부른 뒤 `evil.test` → GET | `at(evil)`, `rt(evil)` | `same-origin` / `cors` | 없음 | `evil.test` | `evil.test`의 둘 실음 |
| 그 뒤 `admin.test` → GET | `at(admin)`, `rt(admin)` | `same-origin` / `cors` | 없음 | `admin.test` | `admin.test`의 둘 실음 |

- 다섯 줄 모두 요청 직전 저장소에 `admin.test`의 쿠키 둘이 있었다(표지).
- `evil.test`의 페이지가 같은 출처로 보낸 요청은 `Sec-Fetch-Site: same-origin`으로 대역에 닿았다. 그 요청이 진짜 이름의 요청과 다른 것은 `Origin`의 이름(POST)과 `x-forwarded-host`, 그리고 쿠키가 없다는 것이었다.
- `evil.test`에서 심은 쿠키는 `domain=evil.test`로 따로 들었고 `admin.test`의 값을 덮지 않았다.

### 4. 주소창 이동과 같은 이름의 다른 포트

| 요청 | 대역의 `Cookie` | `Sec-Fetch-Site` / `-Mode` | `Origin` | 페이지가 본 결과 |
|---|---|---|---|---|
| 주소창으로 `https://admin.test:<관리 포트>/api/echo` 이동 | 둘 다 | `none` / `navigate` | 없음 | 문서가 열렸다 |
| `https://admin.test:<방문자 포트>` 페이지 → 관리 포트로 `fetch` GET(`credentials: "include"`) | 둘 다 | `same-site` / `cors` | `https://admin.test:<방문자 포트>` | `TypeError: Failed to fetch` |
| 같은 페이지 → `fetch` POST(`text/plain`) | 둘 다 | `same-site` / `cors` | `https://admin.test:<방문자 포트>` | `TypeError: Failed to fetch` |
| 같은 페이지의 링크 이동 | 둘 다 | `same-site` / `navigate` | 없음 | 문서가 열렸다 |

- 방문자 포트의 페이지는 nginx의 방문자용 리스너가 낸 문서다(제목 `visitor`를 표지로 봤다).
- 이 값은 node 앞단으로 잰 `../cookie_relay/README.md` 결과 2의 표(A의 주소창 이동, B의 fetch GET·POST, B의 링크)와 같다(그 표를 읽어 손으로 견줬다). 실제 nginx와 컨테이너 안의 Next를 지나도 브라우저가 붙인 `Sec-Fetch-Site`와 `Origin`이 그대로 대역에 닿았다.
- `fetch`가 거부된 것은 대역이 CORS 머리를 내지 않아서라고 읽는다. 콘솔의 까닭 글은 받아 두지 않아 갈래가 없는 어림이다. 요청은 쿠키와 함께 대역에 닿았다.

### 5. Playwright의 API 요청 문맥

| 문맥 | 요청 | 대역이 받은 머리(nginx와 Next가 붙인 것 밖) | `Origin`, `Sec-Fetch-*` |
|---|---|---|---|
| `request.newContext()` | GET | `user-agent: Playwright/1.63.0 (x64; windows 10.0) node/24.19`, `accept: */*`, `accept-encoding: gzip,deflate,br` | 없음 |
| `request.newContext()` | POST(`data`에 객체) | 위에 `content-length`, `content-type: application/json` | 없음 |
| 브라우저 문맥의 `context.request` | GET | `user-agent`가 `HeadlessChrome/153.0.8010.12`를 든 브라우저의 것, `accept`, `accept-encoding` | 없음 |
| 브라우저 문맥의 `context.request` | POST(`data`에 객체) | 위에 `content-length`, `content-type: application/json` | 없음 |

- 주소는 `https://127.0.0.1:<관리 포트>`다. API 요청 문맥은 브라우저 밖(node)에서 걸려 `--host-resolver-rules`가 걸리지 않는다.
- 덤. 두 문맥 모두 `/api/set`의 `Set-Cookie` 두 줄을 받아 `domain=127.0.0.1`, `httpOnly`, `secure`, `sameSite=Strict`로 저장했고, 다음 요청에 두 쿠키를 실었다. `request.newContext()`는 같은 문맥의 다음 요청에, `context.request`는 같은 브라우저 문맥의 페이지 이동에 실었다(브라우저 문맥과 쿠키 통을 함께 쓴다).

### 6. 발행 포트 후보 모양의 렌더

`"${AGENT_OS_ADMIN_ADDRESS:-0.0.0.0}:${AGENT_OS_ADMIN_PORT:-8443}:9443"`을 `docker compose config --format json`으로 렌더했다(띄우지 않았다). `--env-file`로 빈 파일을 줘 `.env`를 읽지 않게 했고, 셸의 두 변수는 지운 뒤 회차의 값만 넣었다.

| 입력 | 관리 화면 줄 `host_ip` | `published` | `target` |
|---|---|---|---|
| 없음 | `0.0.0.0` | `8443` | 9443 |
| `AGENT_OS_ADMIN_PORT=18443` | `0.0.0.0` | `18443` | 9443 |
| `AGENT_OS_ADMIN_ADDRESS=127.0.0.1` | `127.0.0.1` | `8443` | 9443 |
| 둘 다(`127.0.0.1`, `18443`) | `127.0.0.1` | `18443` | 9443 |
| 둘 다 빈 글 | `0.0.0.0` | `8443` | 9443 |
| 환경 변수 파일(`--env-file`)에 `127.0.0.1`, `28443` | `127.0.0.1` | `28443` | 9443 |
| `AGENT_OS_ADMIN_PORT=abc` | 렌더 실패, 종료 1, `invalid hostPort: abc` | | |

- 빈 글은 `:-`가 없는 값으로 다뤄 기본값이 됐다. 같은 렌더의 다른 두 줄(`0.0.0.0:443→8443`, `0.0.0.0:80→8080`)은 모든 회차에서 그대로였다.

## 해석의 대조와 갈래

- "후보 설정은 클라이언트가 지어 보낸 `X-Forwarded-For`와 `X-Real-IP`를 덮는다."
  - 양성 대조: 같은 요청을 대조 설정으로 보내면 지어 보낸 값이 대역에 닿았다(덧붙인 `X-Forwarded-For`, 그대로인 `X-Real-IP`). 이 탐침은 덮이지 않은 값을 잡아낸다.
  - 갈래: 대역에 없는 까닭이 "nginx가 받지 못해서"일 수 있다. 그 회차의 nginx 접근 기록에 세 값이 있었다(표지).
- "Next 중계는 `X-Forwarded-For`, `X-Real-IP`, `X-Forwarded-Proto`를 바꾸지 않고 넘긴다."
  - 양성 대조: 직접 길에서 지어 보낸 세 값이 대역에 그대로 닿았다. nginx를 지난 길에서는 대역의 값이 nginx가 적은 값(`X-Probe-Remote-Addr`와 같은 주소)이었다.
  - 갈래가 하나 더 있다. Next가 그 셋을 스스로 붙이는지. 직접 길에서 지어 보내지 않으면 셋 다 없었다.
- "호스트에서 건 요청이 안쪽 게이트웨이로 보이는 것은 Docker Desktop의 포트 전달이 출발 주소를 바꾸기 때문이다."
  - 양성 대조: 네트워크 안의 컨테이너가 건 요청은 그 컨테이너의 주소로 보였다. nginx의 `$remote_addr`는 TCP 상대를 적고, 이 설정이 주소를 지어내지 않는다.
  - 갈래: 루프백만의 일일 수 있다. 호스트의 LAN 주소로 건 요청도 같은 게이트웨이로 보였다.
  - 리눅스 Docker Engine에서는 이 프로브로 재지 않았다. 같은 L2의 이웃이 IPv4로 건 요청은 제 주소로, 서버 자신이 루프백으로 건 요청은 게이트웨이로 보였다는 것은 `.scratch/release-image/probes/bridge_edge/README.md` 요약 1과 8이 그 프로브로 잰 것이다. 관리 화면용 리스너에서도 같으리라는 것은 어림이다.
- "`evil.test`의 페이지가 보낸 요청에 로그인 쿠키가 실리지 않은 것은 쿠키가 호스트 `admin.test`에 묶였기 때문이다."
  - 양성 대조: `admin.test`의 페이지가 보낸 같은 요청에는 두 쿠키가 실렸다. 그리고 요청 직전 저장소에 그 쿠키가 있었다(표지).
  - 갈래: 까닭이 "`evil.test`의 페이지에서는 쿠키가 실리지 않는다"일 수 있다. 그 이름으로 심은 쿠키는 그 이름의 요청에 실렸다.
  - 갈래가 없는 것: `__Host-` 접두사가 없는 호스트 전용 쿠키(`Domain` 없음)도 같은지. 재지 않았다. 묶는 것이 접두사가 아니라 `Domain`이 없는 것이라는 것은 쿠키 규격을 읽은 어림이고, `__Host-`는 `Domain`을 두지 못하게 강제한다.
- "`Sec-Fetch-Site`로는 다른 이름의 페이지가 같은 서버에 보낸 요청을 가르지 못한다."
  - 관찰: 그 요청의 `Sec-Fetch-Site`는 진짜 이름의 요청과 같은 `same-origin`이었다. 가르는 머리는 `x-forwarded-host`(nginx가 `$host`로 넘긴 이름)와 POST의 `Origin`이었다.
  - ADR 0062 결정 "요청 출처 검사"의 규칙(`Sec-Fetch-Site`가 있으면 `same-origin`만 받는다)을 이 머리에 대 보면 그 요청은 통과한다. 규칙을 읽은 추론이고 검사 코드는 아직 없어 재지 않았다. 쿠키로 여는 경로는 쿠키가 없어 401일 것이고, 로그인 없이 열리는 경로(로그인, 갱신, 링크로 비밀번호 정하기)는 그 요청을 받는다(어림).
  - 이 프로브의 인증서는 `evil.test`도 담았고 브라우저가 인증서 오류를 무시했다. 실제 인증서가 관리 화면의 이름만 담으면 `evil.test`로 건 TLS 연결에서 브라우저가 이름이 맞지 않는다며 막을 것이라는 것은 어림이다. 이 결과는 TLS가 막지 않을 때(사람이 인증서 경고를 넘긴 이름, 자체 서명 배치)의 모양이다.
- "Playwright의 API 요청 문맥은 `Origin`과 `Sec-Fetch-*`를 붙이지 않는다."
  - 양성 대조: 같은 길에서 브라우저의 `fetch`는 `Sec-Fetch-Site`를, POST에는 `Origin`을 붙였고 대역에 닿았다(3, 4). 이 탐침은 그 머리가 닿는 것을 잡아낸다.
  - 그 요청이 ADR 0062의 "그 머리가 없으면 `Origin`도 없을 때만 받는다"를 지난다는 것은 규칙을 읽은 추론이다.

## 로그인 기록의 접속 주소에 대한 읽기(어림)

결과 1에서 끌어낸 읽기이고 명세가 정할 일이다. 잰 것과 아닌 것을 문장마다 가른다.

- `serve`가 보는 TCP 상대는 언제나 관리 화면 컨테이너다(쟀다). 접속 주소로 쓸 수 없다.
- 믿을 수 있는 값은 nginx가 `$remote_addr`로 덮어쓴 한 값이다. 후보 설정에서 `X-Forwarded-For`와 `X-Real-IP`가 같은 값을 실었다(쟀다). 둘 가운데 어느 머리를 읽어도 값은 같고, 배포의 방문자용 리스너는 이미 `X-Forwarded-For`만 덮으므로 두 리스너에 같은 규칙을 걸기에는 `X-Forwarded-For`가 쉽다(어림).
- 그 믿음은 `serve`에 닿는 모든 길이 그 덮어쓰기를 지날 때만 선다. nginx를 거치지 않는 직접 길(지금 배포가 `127.0.0.1:3000`에 여는 관리 화면)에서는 지어 보낸 값이 그대로 닿았고, `serve`가 보는 TCP 상대는 nginx를 지난 길과 같아 둘을 가를 수 없었다(쟀다). 직접 길을 남기면 서버에 들어올 수 있는 사람은 기록의 주소를 지어낼 수 있다(어림).
- 그 값이 손님의 주소인지는 배치에 달렸다. 이 PC(Docker Desktop)에서는 호스트에서 건 모든 요청이 안쪽 게이트웨이 하나였다(쟀다). 리눅스 Engine의 IPv4 손님은 제 주소였다는 것은 다른 프로브의 결과이고(`bridge_edge` 요약 1, 8), 서버 앞에 다른 프록시나 부하 분산기가 서면 nginx가 보는 것은 그 장비의 주소일 것이다(어림, 재지 않았다).

## 재지 못한 것

- 리눅스 Docker Engine. 이 PC의 Docker Desktop(WSL2)에서만 돌았다. 결과 1의 `$remote_addr`가 이 배치에 달려 있다.
- IPv6 손님, 다른 프록시나 부하 분산기가 앞에 선 배치, nginx의 `real_ip` 모듈.
- 배포가 고정한 nginx 1.30.6. 이 프로브는 1.31.6이다.
- 실제 `serve`(uvicorn, FastAPI). uvicorn의 프록시 머리 처리(`--proxy-headers`, `--forwarded-allow-ips`)가 이 값을 어떻게 다루는지는 코드도 문서도 보지 않았다. 대역은 받은 머리를 그대로 적을 뿐이다.
- 실제 관리 화면의 페이지와 그 API 클라이언트, 실제 로그인 흐름. 페이지는 중계를 지난 작은 문서(`/api/page`)였다.
- 흐르는 응답(SSE). 관리 화면의 실행 스트림이 이 리스너를 지날 때 nginx의 버퍼링과 `proxy_read_timeout`(기본 60초. 실행은 기본 600초까지 간다, ADR 0062 결정 "로그인 상태")이 어떻게 걸리는지는 재지 않았다. 후보 설정은 그 둘을 적지 않았다.
- HTTP/2, 쉬는 연결의 수명, 동시 요청.
- 실제 인증서와 실제 도메인. 다른 이름에서 TLS의 이름 검사가 막는지(3의 해석).
- `Host $http_host`처럼 포트를 남겨 넘기는 꼴. `x-forwarded-host`와 `Origin`의 글자가 같아지는지는 재지 않았다.
- `127.0.0.1`로 닫은 발행의 실제 동작. 6은 렌더만 봤다. 닫았을 때 다른 주소에서 refused인지는 재지 않았다.
- 전체 Chromium 채널(`--channel chromium`), Firefox, WebKit.
- `__Host-` 접두사가 없는 호스트 전용 쿠키(3의 해석).
