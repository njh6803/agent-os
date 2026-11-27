# cookie_relay — 관리 화면의 중계와 같은 호스트의 다른 포트 사이에서 쿠키가 움직이는 모양

admin-login 설계가 관리 화면의 로그인 상태(짧은 JWT 와 갱신 번호)를 스크립트가 읽지 못하는 쿠키에 두려 한다.
관리 화면은 브라우저의 `/api/*` 를 Next `rewrites` 로 파이썬 서버에 넘기고(ADR 0019), 배포에서는 방문자용
페이지와 호스트가 같고 포트만 다르다. 이 프로브는 그 구조에서 쿠키와 요청 머리가 실제로 어떻게 움직이는지
실제 관리 화면(Next)과 실제 Chromium 으로 잰다. 결정은 하지 않는다.

**지금 상태(2026-11-14)**: 기본 채널로 두 번(스냅샷을 쓴 회차와 그것과 견준 회차), 전체 Chromium 채널로 한 번
돌았다. 세 회차 모두 표지 35개가 있었고 `next start` 와 `next dev` 의 결과가 같았다. 견준 회차는 스냅샷과
모두 같았고, 전체 Chromium 은 한 가지(아래 "판")만 달랐다.

**`[::1]` 갈래를 더한 회차(2026-11-27, admin-login 티켓 09)**: `http://[::1]:<포트>` 갈래 둘을 더해 `next dev` 모드로만
돌았다(`--mode dev --update`). 표지 25개가 모두 있었고, 앞 회차(2026-11-14)에서 있던 갈래와 `wire`의 값은 하나도 달라지지 않았다. `next start`
모드는 그 회차에 돌지 못했다. 그때 이 워크트리의 관리 화면이 `next build` 에서 실패했다(티켓 09가 짓던 `app/login/page.tsx` 와 그 아래 파일이
서버 컴포넌트에서 `useState` 같은 클라이언트 훅을 가져온다는 Turbopack 오류. 2026-11-27 에 두 번 모두 같았다). 같은 날 뒤에 앱이 빌드되는 판이 되어
`--mode start --update` 로 한 번 더 돌았다(종료 코드 0, 손으로 봤다). `next start` 의 `[::1]` 갈래 둘(`http://[::1]` 와 시작 래퍼가 직접 묶은 갈래)이
`next dev` 의 같은 이름 갈래와 하나도 다르지 않았고, 앞의 2026-11-14 의 `start` 몫은 한 줄도 바뀌지 않았다(`git diff --stat` 이 추가만 보였다).
그래서 `expected.json` 의 `start` 와 `dev` 몫 모두 `[::1]` 갈래를 든다.

| 파일 | 무엇 |
|---|---|
| `probe.mjs` | 측정 스크립트. 무엇을 재고 어떤 표지를 보는지는 그 머리 주석이 원천이다 |
| `servers.mjs` | 띄우는 서버(상류 스텁, 방문자용 페이지 자리의 서버, TLS 앞단). 의존성이 없다 |
| `expected.json` | 포트와 쿠키 값을 이름표로 바꾼 결과의 스냅샷. 미리 적은 기대가 아니라 첫 측정을 받아 적은 것이다 |

## 다시 돌리기

저장소 루트에서

```
node .scratch/admin-login/probes/cookie_relay/probe.mjs
node .scratch/admin-login/probes/cookie_relay/probe.mjs --mode start --out <원본 기록을 둘 폴더>
```

- 필요한 것: `web/` 의 의존성(`pnpm -C web install --frozen-lockfile`), Playwright 의 Chromium, `openssl`(https
  갈래의 자체 서명 인증서. 없으면 그 갈래를 재지 못했다고 적고 넘어간다). 네트워크를 타지 않는다.
- 약 3분이다(2026-11-14 의 두 회차가 2분 44초와 2분 56초. 손으로 봤다, 출력을 받은 파일의 생긴 시각과 고친
  시각을 `stat` 으로). 관리 화면을 `next build` 하므로 `web/apps/admin/.next/`
  를 다시 쓴다. 그 폴더는 `.gitignore` 가 무시한다. 앱의 소스와 설정은 고치지 않는다.
- 종료 코드 0 은 실패가 없고, 표지가 모두 있고, 결과가 `expected.json` 과 같을 때뿐이다. `--update` 는 이
  회차의 결과로 스냅샷을 다시 쓴다. 한 모드만 돈 회차(`--mode start` 나 `--mode dev`)의 `--update` 는 그 모드의 몫만 바꾸고 다른 모드의
  몫은 앞의 파일에서 그대로 둔다(2026-11-27 에 더했다). `--channel chromium` 은 기본(headless shell) 대신 전체 Chromium 으로 돈다.
- 원본 기록(상류와 방문자용 서버가 받은 요청 전부, 관리 화면의 출력 머리, 표지)은 `--out` 폴더의 `results.json`.

## 판

Next 16.3.6, Playwright 1.63.0, Chromium 153.0.8010.12, Node v24.19.0, Windows 10. `next dev` 는 Turbopack 이다.
전체 Chromium 채널(`--channel chromium`, 같은 153.0.8010.12)은 스냅샷과 `headerNamesAtBackend` 여덟 자리만
달랐다. 상류가 받는 머리에 `accept-language` 가 하나 더 온다. 쿠키와 아래 결과의 다른 값은 모두 같았다. 그
채널의 종료 코드는 그 차이 때문에 1 이다.

## 띄우는 것과 갈래

- A 는 관리 화면(시작 래퍼 `tools/start.ts` 로 띄운 실제 앱), 상류는 요청 머리를 그대로 적는 스텁, B 는 호스트가
  같고 포트가 다른 서버(방문자용 페이지 자리), C 는 사이트가 다른 페이지(대조)다.
- 브라우저가 치는 주소는 넷이다. `http://localhost`, `http://127.0.0.1`, `http://probe.test`(평문 대조),
  `https://probe.test`(배포와 닮은 꼴. node 로 지은 TLS 앞단이 A 앞에 선다). `probe.test` 와 `other.test` 는
  Chromium 의 `--host-resolver-rules` 로 127.0.0.1 에 맞춘다.
- `[::1]` 갈래는 둘이다(2026-11-27). 둘 다 IPv6 루프백 `http://[::1]:<포트>` 를 브라우저가 친다.
  - `http://[::1]`: 관리 화면은 앞의 셋과 같은 프로세스(`127.0.0.1` 에 묶임)이고, 그 앞에 `::1` 에 서는 TCP 중계(`servers.mjs` 의
    `tcpFront6`)가 선다. 바이트를 그대로 넘기므로 관리 화면이 받는 `Host` 는 브라우저가 보낸 `[::1]:<앞단 포트>` 다. B 는 `::1` 에 따로
    서는 평문 서버(`createPlainVisitor`)이고 사이트가 다른 C 는 `http://127.0.0.1:<B 포트>` 다. 범위는 `localhost`·`127.0.0.1` 갈래와 같다(`full`).
  - `http://[::1] 시작 래퍼가 직접 묶음`: 앞단 없이 관리 화면의 시작 래퍼를 `--hostname ::1` 로 띄운 프로세스를 친다. `next dev` 는 한 폴더에서 둘째
    프로세스를 함께 띄우지 못해, 두 모드 모두 `127.0.0.1` 의 관리 화면을 내린 뒤 그 자리에서 다시 띄운다. 범위는 쿠키 저장과 같은 출처
    `GET` 하나(`cookies`)다.
  - 서버를 `::1` 에 세우지 못하면 둘 다 건너뛰고 `info.ipv6Measured` 가 `false` 이며 까닭이 `info.ipv6Problem` 에 남는다. 이 PC 에서는
    열렸다(`ipv6Measured` 가 `true`).
- 상류가 `/set` 에 싣는 쿠키는 넷이고 모두 `HttpOnly; Secure; SameSite=Strict` 다. `__Host-probe_at`(Path=/),
  `__Host-probe_rt`(Path=/, Max-Age), `probe_plain`(Path=/), `probe_scoped`(Path=/api/echo).

## 결과(2026-11-14, 스크립트로 쟀다)

근거의 종류. 아래 값은 모두 탐침이 결과(`facts`)에 찍어 `expected.json` 에 박은 것이고, 다시 돈 회차가 그
스냅샷과 견준다. 탐침이 단언하는 것은 표지(머리 주석의 일곱 가지)뿐이다. 값이 무엇이어야 한다는 기대를 미리
적지는 않았다. "읽는다"로 끝나는 문장은 해석이고 그 대조와 갈래는 아래 절에 있다.

네 갈래 가운데 `http://localhost`, `http://127.0.0.1`, `https://probe.test` 의 결과는 호스트 이름과 앞단이 붙이는
머리 말고는 같았다(손으로 봤다. 호스트 이름을 이름표로 바꿔 두 갈래를 견주는 스크래치 스크립트로 봤고, 그
스크립트는 커밋하지 않았다). 아래에서 갈래를 따로 적지 않은 줄은 셋 모두의 것이다.

### 1. Set-Cookie 가 중계를 지나는 모양

- node 의 날 HTTP 로 받은 응답에서, 상류가 낸 Set-Cookie 네 줄과 중계를 지난 네 줄이 줄 수, 차례, 글자까지
  같았다. 합쳐지지 않았고 속성도 바뀌지 않았다. 응답 머리의 이름과 차례도 같았다.
- 204, 401, 303 응답에 실은 Set-Cookie 두 줄도 그대로 지났다. 303 의 `Location: /page` 는 `/api/page` 로
  고쳐지지 않고 그대로 왔다.
- 브라우저(CDP)가 받은 줄도 같은 네 줄이었고, 저장소에는 `httpOnly`, `secure`, `sameSite=Strict`, 적은 Path
  그대로 들었다. Path 는 고쳐지지 않는다. `Path=/api/echo` 쿠키는 브라우저 주소 `/api/echo` 에만 실렸고
  `/api/other` 에서는 `NotOnPath` 로 빠졌다.
- 401 응답에 실은 `Max-Age=0` 두 줄을 브라우저가 받아들여 그 둘이 저장소에서 지워졌다.

### 2. 상류가 받는 머리

| 요청 | Cookie | Origin | Sec-Fetch-Site / Mode | Referer |
|---|---|---|---|---|
| A 의 페이지 fetch GET | 넷 다 | 없음 | same-origin / cors | 페이지의 전체 주소 |
| A 의 페이지 fetch POST(text/plain, JSON) | 넷 다 | A 의 출처 | same-origin / cors | 페이지의 전체 주소 |
| 주소창으로 A 의 `/api/echo` 이동 | 넷 다 | 없음 | none / navigate | 없음 |
| B 의 페이지 fetch GET | 넷 다 | B 의 출처 | same-site / cors | B 의 출처만 |
| B 의 페이지 fetch POST(text/plain) | 넷 다 | B 의 출처 | same-site / cors | B 의 출처만 |
| B 의 페이지 fetch POST(`no-cors`) | 넷 다 | B 의 출처 | same-site / no-cors | B 의 출처만 |
| B 의 페이지 fetch POST(JSON) | 닿지 않음. `OPTIONS` 만 닿았다 | | | |
| B 의 페이지 폼 POST | 넷 다 | B 의 출처 | same-site / navigate | B 의 출처만 |
| B 의 페이지 링크 GET | 넷 다 | 없음 | same-site / navigate | B 의 출처만 |

- `Host` 는 언제나 상류의 주소(`127.0.0.1:<상류 포트>`)다. 브라우저가 친 호스트는 `x-forwarded-host` 로만 온다.
- Next 가 붙이는 `X-Forwarded-*` 는 `x-forwarded-host` 하나다. `x-forwarded-for`, `-proto`, `-port` 는 붙이지
  않는다. 앞단이 실은 `x-forwarded-for` 와 `x-forwarded-proto` 는 그대로 지난다.
- 클라이언트가 지어 보낸 머리(날 HTTP): `x-forwarded-host` 는 Next 가 받은 Host 로 덮였고, `x-forwarded-for`,
  `x-forwarded-proto`, `x-forwarded-port`, `forwarded`, `Origin` 은 지어 보낸 값 그대로 상류에 닿았다.
- 앞단이 Host 에서 포트를 떼어 넘기면(`frontHostWithoutPort`) 상류가 받는 `x-forwarded-host` 는 `probe.test`
  이고 `Origin` 은 `https://probe.test:<포트>` 다. 둘이 글자로 같지 않다.
- 평문 `http://probe.test` 에서는 `sec-fetch-*` 와 `sec-ch-ua*` 가 오지 않았다.

### 3. localhost 와 127.0.0.1 의 Secure, `__Host-`

- `http://localhost:<포트>` 와 `http://127.0.0.1:<포트>` 둘 다 네 쿠키(`Secure`, `__Host-` 포함)가 저장되고
  다음 요청에 실렸다.
- 접두사 규칙은 걸린다. `Path=/api` 인 `__Host-` 쿠키와 `Secure` 없는 `__Host-` 쿠키는 두 주소에서 모두
  `InvalidPrefix` 로 거절됐다.
- 대조인 평문 `http://probe.test` 에서는 넷 다 거절됐다(`__Host-` 둘은 `InvalidPrefix`, 나머지 둘은
  `SecureOnly`). 저장소가 비었고 Cookie 가 실리지 않았다.

### 4. 호스트가 같고 포트가 다른 둘

- (가) A 가 심은 쿠키는 B 로 가는 요청(이동과 fetch)에 실렸다. `Path=/api/echo` 쿠키는 B 의 `/api/echo` 에만
  실렸다. B 의 `document.cookie` 는 빈 글이었다(HttpOnly).
- (나) 위 표의 B 줄. 페이지의 fetch 는 `TypeError: Failed to fetch` 로 거부됐지만 GET 과 단순 POST 는 쿠키와
  함께 상류에 닿았다. 거부는 상류가 CORS 머리를 내지 않아서라고 읽는다(콘솔의 까닭 글은 받아 두지 않았다).
  JSON POST 는 사전 요청(`OPTIONS`, Cookie 없음)만 닿고 본 요청은 가지 않았다. 스텁은 `OPTIONS` 에 CORS 머리
  없는 204 로 답한다. 실제 서버는 관리 경로의 사전 요청에 토큰이 없으면 CORS 머리 없는 401 이다(코드를
  읽었다, `tests/test_server.py` 571~587줄). 상류가 사전 요청을 허락하는 머리로 답하는 경우는 재지 않았다.
- (다) B 의 스크립트가 `document.cookie` 로 쓴 것과 그 뒤 A 의 `/api/echo` 로 간 Cookie:

| B 가 쓴 것 | 저장소 | 상류가 받은 것 |
|---|---|---|
| `__Host-probe_at=…; Secure; Path=/` (같은 키) | 그대로 | A 의 값 |
| `probe_plain=…; Secure; Path=/` (같은 키) | 그대로 | A 의 값 |
| `probe_plain=…; Path=/api` (`Secure` 있는 것과 없는 것 둘 다) | 둘째 쿠키가 들었다 | `probe_plain` 이 둘. B 의 값이 앞 |
| `__Host-probe_at=…; Secure; Path=/api` | 그대로 | A 의 값 |
| 새 이름(`__Host-probe_new`, `probe_new`) | 들었다 | A 의 넷과 새 쿠키 |
| HttpOnly 가 아닌 A 의 쿠키 `__Host-probe_open` 과 같은 키 | B 의 값으로 덮였다 | B 의 값 |

- 덤. B 의 서버가 응답의 Set-Cookie 로 같은 이름 둘을 실으면 `__Host-probe_at` 과 `probe_plain` 이 모두
  덮였고 상류는 B 의 값을 받았다. A 가 심기 전에 B 의 스크립트가 `__Host-probe_at` 을 먼저 심으면 상류는 그
  값을 받았고, A 의 Set-Cookie 가 온 뒤에는 A 의 값으로 바뀌었다.

### 5. `next start` 와 `next dev`

2026-11-14 회차에서 두 모드의 결과를 자리마다 견줘 다른 자리가 0 이었다(1 과 2 를 포함한 전부). 2026-11-27 회차는 `dev` 만 돌아 이 견줌은 새
갈래(6)에는 하지 못했다.

### 6. `[::1]` 에서 `Secure`·`__Host-` 쿠키(2026-11-27, `next dev` 만, 스크립트로 쟀다)

근거의 종류. 아래 값은 모두 탐침이 `facts` 에 찍어 `expected.json` 의 `dev` 몫에 박은 것이다. 같은 호스트 대조의 견줌(첫 항목의 "같다")은
손으로 봤다. `expected.json` 에서 `http://127.0.0.1` 과 `http://[::1]` 의 `facts.dev` 를 꺼내 호스트 이름과 포트를 이름표로 바꾼 뒤 견주는 커밋하지
않은 스크래치 스크립트로 봤고(세션 스크래치패드의 `six.py`), 다른 자리는 사이트가 다른 C 의 호스트 이름(`localhost` 와 `127.0.0.1`)이 `Origin`·
`Referer` 에 찍힌 것 아홉이 전부였다.

- 두 갈래 모두 네 쿠키(`Secure`, `__Host-` 포함)가 저장소에 들었다. 저장소의 `domain` 은 대괄호를 낀 `[::1]` 이고 `httpOnly`, `secure`,
  `sameSite=Strict`, 적은 Path 그대로다. 쿠키가 다음 요청에 실렸다(같은 출처 `GET /api/echo`에서 네 쿠키가 모두 상류에 닿았다).
- 접두사 규칙이 `[::1]` 에서도 걸린다. `Path=/api` 인 `__Host-` 쿠키와 `Secure` 없는 `__Host-` 쿠키는 `InvalidPrefix` 로 거절됐다.
- 앞단 `[::1]` 갈래의 나머지 관찰은 `http://127.0.0.1` 갈래와 같았다. B 로 가는 요청에 A 의 쿠키가 실리고(`probe_scoped` 는 `NotOnPath`), 사이트가 다른
  C 의 요청에서는 넷 모두 `SchemefulSameSiteStrict` 로 빠졌으며, 401 의 `Max-Age=0` 두 줄이 받아들여져 둘이 지워졌다.
- 시작 래퍼 직접 갈래: 래퍼가 `--hostname ::1` 을 받아 `::1` 에만 묶였다(`::1` 로 200, 같은 포트의 `127.0.0.1` 은 연결 거절, 상류가
  `x-forwarded-host: [::1]:<포트>` 를 받았다). 쿠키 저장과 같은 출처 요청의 결과는 앞단 갈래와 같았다(저장소와 거절의 줄, 상류가 받는 머리의 이름).
  상류 주소는 `127.0.0.1` 이었다(`[::1]` 상류는 `loopback.ts` 가 막는다).

## `[::1]` 해석의 대조

- "`[::1]` 에서 `Secure` 쿠키가 받아들여진다"의 대조는 같은 회차의 `http://probe.test`(평문, 루프백이 아닌 이름)다. 같은 브라우저에서 같은 쿠키가
  거절되는 것이 보였다(3절. 2026-11-27 의 `dev` 회차도 그 몫이 앞 회차와 같았다). 그래서 `[::1]` 의 저장은 이 브라우저가 `Secure` 를 아무 데서나
  받아서가 아니라 `[::1]` 을 루프백으로 다뤄서라고 읽는다. 어느 규칙이(Chromium 의 어느 판정이) 그렇게 가르는지는 읽지 않았다.
- 두 `[::1]` 갈래가 같은 결과를 낸 것은 브라우저가 친 주소가 둘 다 `[::1]` 이기 때문이라고 읽는다. 앞단이 `Host` 를 건드리지 않았다는 것은 두 갈래 모두에서
  상류가 받은 `x-forwarded-host` 가 `[::1]:<브라우저가 친 포트>` 인 것이 받친다(탐침이 `facts` 에 찍은 값이다).

## 해석의 대조와 갈래

- "Strict 쿠키가 B 에서 실린다"는 포트가 사이트를 가르지 않아서라고 읽는다. 대조는 사이트가 다른 C 에서 같은
  요청 여섯을 보낸 갈래다. 요청은 상류에 닿았지만 Cookie 가 없었고, CDP 는 빠진 까닭을
  `SchemefulSameSiteStrict` 로 적었다. 까닭의 이름에 `Schemeful` 이 붙는 까닭은 가르지 못했다.
- "같은 키를 덮지 못한다"는 HttpOnly 때문이라고 읽는다. 쓰기 자체가 되는 환경이라는 것은 새 이름이 드는
  갈래가, 다른 속성이 아니라 HttpOnly 가 가른다는 것은 HttpOnly 만 뺀 쿠키가 덮이는 갈래가 받친다. 그 대조는
  `__Host-` 이름으로만 뒀다. 접두사 없는 `probe_plain` 에 같은 까닭을 대는 것은 어림이다.
- "localhost 에서 Secure 가 받아들여진다"의 대조는 평문 `http://probe.test` 갈래다. 거기서는 거절되는 것이
  같은 브라우저에서 보였다.
- 요청이 중계를 지났다는 표지(`x-forwarded-host`)와 모드의 표지(dev 전용 경로)는 `probe.mjs` 머리 주석.

## 재지 못한 것

- `[::1]` 갈래의 `next start` 몫(위 "지금 상태"의 까닭). `[::1]` 의 https(자체 서명 인증서의 `[::1]` 주소)와 `[::1]` 이 상류인 경우는 재지 않았다.
  상류는 시작 래퍼가 `127.0.0.1` 만 받는다(`loopback.ts`). 이 PC 의 IPv6 루프백만 봤다.

- 실제 nginx. https 갈래의 앞단은 node 로 흉내 낸 것이다. Host 에서 포트를 떼는 것은
  `.scratch/release-image/probes/proxy_config/nginx/proxy.conf` 의 `proxy_set_header Host $host` 를 읽고 흉내 냈다.
- Chromium 말고 다른 브라우저(Firefox, WebKit).
- 실제 도메인. `.test` 이름과 자체 서명 인증서(오류 무시)였다. 하위 도메인 사이는 재지 않았다.
- 실제 파이썬 서버가 내는 Set-Cookie, 실제 관리 화면의 페이지와 그 API 클라이언트. A 의 페이지는 중계를 지난
  빈 문서(`/api/page`)였다.
- SSE 같은 흐르는 응답, HTTP/2, 배포 이미지(컨테이너) 안의 실행. 배포 이미지가 `next build` 뒤 시작 래퍼로
  `next start` 를 띄운다는 것은 `.scratch/release-image/spec.md` 를 읽은 것이다.
