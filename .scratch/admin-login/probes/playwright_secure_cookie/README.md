# playwright_secure_cookie — Playwright 가 `Secure` 쿠키를 `http://127.0.0.1:<포트>` 에서 저장하고 보내는 길

admin-login 티켓 09. 관리 화면 e2e(`web/apps/admin/e2e/`)는 서버에 계정을 서버 명령으로 만든 뒤 로그인 요청으로
쿠키(`__Host-` 접두, `HttpOnly; Secure; SameSite=Strict; Path=/`)를 받아 브라우저 문맥에 심어야 한다. 어느 길이
되는지 실제 Chromium 으로 잰다. 결정은 하지 않고 잰 값만 적는다.

| 파일 | 무엇 |
|---|---|
| `probe.mjs` | 측정 스크립트. 서버(node `http`, `127.0.0.1` 의 빈 포트)를 직접 세우고 갈래마다 로그인 뒤 `GET /who` 가 받은 `Cookie` 머리를 읽는다. 갈래와 표지는 그 머리 주석이 원천이다 |

`expected.json` 은 두지 않았다. 갈래의 결과(되는지, 안 되는지)는 단언하지 않고, 스크립트가 단언하는 것은 아래 표지뿐이다.

## 다시 돌리기

저장소 루트에서

```
node .scratch/admin-login/probes/playwright_secure_cookie/probe.mjs [--out <원본 기록을 둘 폴더>]
```

- 필요한 것: `web/` 의 의존성(`pnpm -C web install --frozen-lockfile`)과 Playwright 의 Chromium. `@playwright/test` 는
  `web/apps/admin/package.json` 기준으로 푼다(`cookie_relay/probe.mjs` 와 같다). 네트워크를 타지 않고 앱도 파이썬 서버도 띄우지 않는다.
  한 회차가 3초 걸렸다(손으로 쟀다, 셸의 `date` 로. 표지 7개 모두 있었다).
- 종료 코드 0 은 표지가 모두 있을 때뿐이다. 결과 전체는 표준 출력과 `--out` 폴더의 `results.json`(서버가 받은 요청 기록 포함).

## 판

Playwright 1.63.0, Chromium 153.0.8010.12(기본 채널, headless shell), Node v24.19.0, Windows 10(10.0.19045). 이 판에서만 쟀다.

## 표지(2026-11-27 회차에서 모두 있었다)

1. 서버가 `POST /login` 을 네 번(a, a-localhost, b, d) 받아 `Set-Cookie` 둘을 실어 답했고, 대조의 `POST /login-plain` 을 한 번
   받아 하나를 실어 답했다.
2. 요청 문맥으로 로그인한 갈래(a, a-localhost, b)와 대조(a-control-plain)는 클라이언트가 받은 응답 머리의 `Set-Cookie` 줄이 서버가 실은
   글자 그대로였다.
3. `/who` 를 읽은 갈래마다 서버가 그 요청을 하나 받았고, 서버가 본 `Cookie` 머리가 응답 본문의 것과 같았다.
4. 페이지를 연 갈래마다 출처가 `http://127.0.0.1:<포트>` 이고 `window.isSecureContext` 가 `true` 였다.

## 결과를 본 뒤 바꾼 것

첫 회차는 갈래 a~d 와 e 의 두 모양(`url` 에 속성을 준 것, `domain·path`)만 있었고 표지는 서버의 로그인 셈, 응답 머리, `/who` 의 서버·본문 일치, 출처와
`isSecureContext` 였다. 그 회차에서 a 의 `GET /who` 에 `Cookie` 가 없는 것을 보고 두 가지를 더했다. 대조 둘(a-control-plain, a-localhost)과 로그인
셈·응답 머리 표지의 그 몫, 그리고 e 의 `{name, value, url}` 만 준 모양(`url` 모양이 거절된 것을 보고 속성 때문인지 가르려고)이다. 갈래의 결과는
단언하지 않는 점은 그대로다. 아래는 더한 뒤의 회차(2026-11-27)의 값이다.

## 결과(2026-11-27, 스크립트로 쟀다)

근거의 종류. 아래 값은 모두 탐침이 `facts` 에 찍은 것이다. "읽는다"로 끝나는 문장은 해석이고 그 갈래는 아래 절에 있다.

| 갈래 | 쿠키 저장소에 든다 | 다음 요청에 실린다(서버가 본 `Cookie` 머리) |
|---|---|---|
| a. `request.newContext({ baseURL })` 로 `POST /login`, 같은 문맥의 `GET /who` | `storageState()` 에 둘 다 든다(`httpOnly`, `secure`, `sameSite=Strict`, `domain=127.0.0.1`, `path=/`. `__Host-t_rt` 는 만료 시각이 있고 `__Host-t_at` 은 세션) | **안 실린다**(`Cookie` 머리 없음) |
| b. 브라우저 문맥의 `context.request.post('/login')` | `context.cookies()` 에 둘 다 든다(같은 속성) | 같은 `context.request.get('/who')` 는 **안 실린다**. 그 문맥의 `page.goto('/')` 한 페이지의 `fetch('/who')` 는 **실린다**(`__Host-t_at=v1; __Host-t_rt=v2`). 페이지의 `document.cookie` 는 빈 글 |
| c. a 의 `storageState()` 를 `browser.newContext({ storageState })` 에 넘김 | 문맥이 서자마자 `context.cookies()` 에 둘 다 있다 | 그 문맥 페이지의 `fetch('/who')` 에 **실린다** |
| d. 대조: 페이지의 `fetch('/login', { method: 'POST' })` | 둘 다 든다 | 같은 페이지의 `fetch('/who')` 에 **실린다** |
| a-control-plain. a 와 같은 흐름에 Secure 도 `__Host-` 도 없는 쿠키(`t_plain=v3; HttpOnly; SameSite=Strict; Path=/`) | 든다 | **실린다**(`t_plain=v3`) |
| a-localhost. a 와 같은 흐름을 `http://localhost:<포트>` 로 | 든다(`domain=localhost`) | **실린다**(`__Host-t_at=v1; __Host-t_rt=v2`) |
| e. 덤, `context.addCookies`(로그인 요청 없이, 값은 a 의 `storageState` 에서) | `domain: "127.0.0.1", path: "/"` 에 `httpOnly`·`secure`·`sameSite: "Strict"` 를 준 모양은 든다(`__Host-t_rt` 는 만료 시각을 주지 않아 세션으로 든다). `url: <주소>` 로 주는 모양은 둘 다(속성을 준 것과 `{name, value, url}` 만 준 것) `Protocol error (Storage.setCookies): Invalid cookie fields` 로 거절됐다 | `domain·path` 모양으로 심은 문맥 페이지의 `fetch('/who')` 에 **실린다** |

- 요약. 이 판에서 `http://127.0.0.1:<포트>` 의 `Secure`·`__Host-` 쿠키는 브라우저(Chromium) 쪽에서는 저장되고 실린다(b의 페이지, c, d, e의
  domain·path 모양). Playwright 의 요청 문맥(a 와 b 의 `context.request`)은 같은 쿠키를 저장소에는 두지만 `127.0.0.1` 로 가는 다음 요청에는
  싣지 않는다. 같은 흐름이 `localhost` 로는 싣는다(a-localhost).
- 한 가지 길로 e2e 를 짠다면 이 표에서 되는 길은 (a 로 로그인해 `storageState` 를 얻어 c 로 새 브라우저 문맥에 넘기기), (b 로 로그인해 같은 브라우저
  문맥의 페이지를 쓰기), (d 의 페이지 fetch), (e 의 `addCookies` 의 domain·path 모양)이다. 요청 문맥에서 로그인한 같은 문맥으로 이어서 보호된
  경로를 치는 길(a 와 b 의 `context.request.get`)은 `127.0.0.1` 에서 안 된다.

## 해석의 대조와 갈래

- "a 와 b 의 `context.request` 가 안 싣는 것은 `Secure` 쿠키를 평문 `127.0.0.1` 에서 거르는 요청 문맥의 규칙 때문"이라고 읽는다. 대조 둘이
  받친다. a-control-plain 은 같은 흐름(로그인 뒤 같은 문맥의 `GET`)이 `Secure` 없는 쿠키는 나른다는 양성 대조이고, a-localhost 는 같은
  `Secure` 쿠키를 호스트만 `localhost` 로 바꾸면 나른다는 대조다. 다만 a-control-plain 은 `Secure` 와 `__Host-` 접두사 둘을 한꺼번에 뺐다.
  거르는 까닭이 `Secure` 속성 하나인지 접두사도 관여하는지는 가르지 못했다. 요청 문맥의 내부 구현은 읽지 않았다.
- "브라우저 쪽이 `127.0.0.1` 의 `Secure` 를 받아들이는 것은 Chromium 의 루프백 예외"라고 읽는다. 대조는 같은 폴더가 아니라
  `../cookie_relay/` 의 평문 `http://probe.test`(루프백이 아닌 이름. `Secure` 쿠키가 거절됐다)다. 이 폴더는 루프백이 아닌 이름을 따로
  재지 않았다. 다만 표지 4 가 이 브라우저 문맥이 `isSecureContext` 였음을 보인다.
- `e` 의 `url` 모양이 거절된 까닭은 가르지 못했다. 속성을 준 모양과 이름·값·`url` 만 준 모양이 같은 오류였고, 그 오류 글이 원인을 말해 주지
  않는다. 거절됐다는 사실만 적는다.

## 재지 못한 것

- 실제 관리 화면과 파이썬 서버가 낸 `Set-Cookie`. 서버는 이 스크립트가 짠 스텁이고 쿠키 값은 `v1`·`v2` 같은 고정 문자열이다.
- 같은 쿠키가 갱신(`Max-Age=0` 로 지우기, 값 바꾸기)될 때의 저장소 모양. 로그인 한 번만 봤다.
- `localhost` 와 `127.0.0.1` 말고 `[::1]` 의 요청 문맥(요청 문맥의 `Secure` 거르기가 `[::1]` 에도 있는지). 브라우저 쪽 `[::1]` 은 `../cookie_relay/` 가 잰다.
- Firefox, WebKit. Playwright 의 `webServer` 로 앱을 띄우는 길, `globalSetup` 이나 `fixtures` 에 이 흐름을 넣었을 때.
- 판이 다르면 다르게 나올 수 있다(Playwright 와 Chromium 의 판을 올릴 때 다시 돈다).
