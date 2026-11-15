# cookie_relay — 관리 화면의 중계와 같은 호스트의 다른 포트 사이에서 쿠키가 움직이는 모양

admin-login 설계가 관리 화면의 로그인 상태(짧은 JWT 와 갱신 번호)를 스크립트가 읽지 못하는 쿠키에 두려 한다.
관리 화면은 브라우저의 `/api/*` 를 Next `rewrites` 로 파이썬 서버에 넘기고(ADR 0019), 배포에서는 방문자용
페이지와 호스트가 같고 포트만 다르다. 이 프로브는 그 구조에서 쿠키와 요청 머리가 실제로 어떻게 움직이는지
실제 관리 화면(Next)과 실제 Chromium 으로 잰다. 결정은 하지 않는다.

**지금 상태(2026-11-14)**: 기본 채널로 두 번(스냅샷을 쓴 회차와 그것과 견준 회차), 전체 Chromium 채널로 한 번
돌았다. 세 회차 모두 표지 35개가 있었고 `next start` 와 `next dev` 의 결과가 같았다. 견준 회차는 스냅샷과
모두 같았고, 전체 Chromium 은 한 가지(아래 "판")만 달랐다.

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
  회차의 결과로 스냅샷을 다시 쓴다. `--channel chromium` 은 기본(headless shell) 대신 전체 Chromium 으로 돈다.
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

두 모드의 결과를 자리마다 견줘 다른 자리가 0 이었다(1 과 2 를 포함한 전부).

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

- 실제 nginx. https 갈래의 앞단은 node 로 흉내 낸 것이다. Host 에서 포트를 떼는 것은
  `.scratch/release-image/probes/proxy_config/nginx/proxy.conf` 의 `proxy_set_header Host $host` 를 읽고 흉내 냈다.
- Chromium 말고 다른 브라우저(Firefox, WebKit).
- 실제 도메인. `.test` 이름과 자체 서명 인증서(오류 무시)였다. 하위 도메인 사이는 재지 않았다.
- 실제 파이썬 서버가 내는 Set-Cookie, 실제 관리 화면의 페이지와 그 API 클라이언트. A 의 페이지는 중계를 지난
  빈 문서(`/api/page`)였다.
- SSE 같은 흐르는 응답, HTTP/2, 배포 이미지(컨테이너) 안의 실행. 배포 이미지가 `next build` 뒤 시작 래퍼로
  `next start` 를 띄운다는 것은 `.scratch/release-image/spec.md` 를 읽은 것이다.
