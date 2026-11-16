# opener_message: URL 방식의 창이 자기를 연 페이지와 메시지를 주고받는 조건

ADR 0061 결정 "URL 방식"은 사이트의 페이지가 연 창 전체가 위젯이고, 그 창이 자기를 연 페이지에 토큰을 묻는다고 정했다. 다른 출처의 창끼리 그 통로가 서는지는 재지 않은 채 이 기능의 e2e에 넘겼다(같은 ADR Consequences "재지 않은 것"). 통로가 서지 않으면 URL 방식의 결정을 다시 봐야 하므로 명세를 쓰는 자리에서 `probe.mjs`로 쟀다. 위젯 코드는 아직 없어, 위젯의 창이 보낼 물음과 사이트의 페이지가 낼 답을 흉내 낸다(메시지의 이름은 프로브의 것이다). 재는 칸, 표지, 띄우는 것은 그 스크립트의 머리 주석이 원천이다. 인증서와 프록시는 옆 프로브와 함께 쓰는 `../kit.mjs`의 것이다.

## 다시 돌리기

```bash
node .scratch/widget-login-state/probes/opener_message/probe.mjs --engine chromium
```

- 필요한 것: `web/`의 의존성(`pnpm -C web install --frozen-lockfile`), Playwright의 Chromium, `openssl`(Git Bash의 것으로 돌렸다). 네트워크를 타지 않는다. hosts 파일을 건드리지 않는다.
- 약 20초다(2026-11-16에 `time`으로 20초).
- 결과가 같은 폴더의 `expected.json`과 같고 표지가 모두 있으면 0으로 끝난다. 원본 기록은 `--out`으로 준 폴더(주지 않으면 임시 폴더)의 `results.json`이다.
- `--engine`을 주지 않으면 세 엔진을 모두 띄우려 한다. 이 PC에는 Playwright 1.63.0이 찾는 Firefox와 WebKit 빌드가 없어 그 둘은 "브라우저를 띄웠다" 표지가 없고 1로 끝난다.

## 잰 판

Playwright 1.63.0, Chromium 153.0.8010.12(Playwright가 내려받은 headless shell, 기본 프로필), Node v24.19.0, OpenSSL 1.1.1k, Windows 10. 2026-11-16.

## 결과

Chromium 하나의 결과다. 아래 표는 프로브가 끝에 찍는 `요약` 줄을 옮긴 것이고, 칸마다의 값(33칸)은 프로브가 `expected.json`과 견준다. "주고받았다"는 사이트의 페이지가 위젯의 창이 보낸 물음을 받았고 위젯의 창이 답을 받았다는 뜻이다. 위젯의 창의 출처 셋(사이트의 페이지와 같은 출처, 등록 도메인이 같은 다른 출처, 등록 도메인이 다른 출처)은 모든 줄에서 같은 결과를 냈다.

| 여는 법과 그 뒤의 일 | 결과(출처 셋 모두) |
|---|---|
| `window.open(주소)` | 주고받았다 |
| `window.open(주소, "_blank", "width=420,height=680")`(크기를 준 창) | 주고받았다 |
| `window.open(주소, "_blank", "noopener")` | 주고받지 못했다. 위젯의 창의 `window.opener`가 `null`이다 |
| `<a target="_blank">`를 눌러 연다(`rel`을 적지 않는다) | 주고받지 못했다. `window.opener`가 `null`이다 |
| `<a target="_blank" rel="opener">`를 눌러 연다 | 주고받았다 |
| 위젯의 창의 응답이 `Cross-Origin-Opener-Policy: same-origin`을 싣는다 | 주고받지 못했다. `window.opener`가 `null`이다 |
| 사이트의 페이지의 응답이 `Cross-Origin-Opener-Policy: same-origin`을 싣는다 | 주고받지 못했다. `window.opener`가 `null`이다 |
| 사이트의 페이지의 응답이 `Cross-Origin-Opener-Policy: same-origin-allow-popups`를 싣는다 | 주고받았다 |
| 연 뒤 위젯의 창을 새로 고친다 | 주고받았다 |
| 연 뒤 사이트의 페이지가 같은 출처의 다른 문서로 간다 | 주고받지 못했다. `window.opener`는 남아 있고 답이 없다 |
| 연 뒤 사이트의 페이지를 닫는다 | 주고받지 못했다. `window.opener`가 `null`이다 |

칸마다 찍은 줄에서 손으로 읽은 것이다(값은 `expected.json`에 있다).

- 주고받은 칸에서 사이트의 페이지가 받은 물음의 `event.origin`은 위젯의 창의 출처였고, `event.source`는 `window.open`이 돌려준 손잡이와 같았다. 위젯의 창이 받은 답의 `event.origin`은 사이트의 페이지의 출처였고, `event.source`는 `window.opener`와 같았다.
- 링크로 연 칸에서는 사이트의 페이지에 창 손잡이가 없다. `rel="opener"`를 적은 칸에서 사이트의 페이지는 물음의 출처만 보고 `event.source`에 답했다.
- `Cross-Origin-Opener-Policy: same-origin`을 실은 칸(위젯의 창 쪽이든 사이트의 페이지 쪽이든)에서 `window.open`은 손잡이를 돌려줬지만 그 손잡이의 `closed`가 참이었다. 사이트의 페이지가 그 머리를 실은 칸은 위젯의 창이 사이트의 페이지와 같은 출처일 때도 그랬다. 위젯의 창의 응답에는 그 머리가 없어 두 문서의 값이 달랐다.

## 읽는 법

- **다른 출처의 창끼리도 통로가 선다.** `window.open`으로 연 창은 사이트와 등록 도메인이 다른 출처에서도 물음과 답을 주고받았다. 그 답이 연결을 타고 온 것이라는 것은 음성 대조가 가른다. `noopener`로 연 칸에서는 위젯의 창의 `window.opener`가 `null`이었고 답이 오지 않았다.
- **연결을 끊는 길은 넷을 봤다.** `noopener` 옵션, `rel`을 적지 않은 `target="_blank"` 링크, 위젯의 창의 응답 머리, 사이트의 페이지의 응답 머리다. 머리를 실은 칸이 주고받지 못한 까닭이 그 머리라는 것은 같은 출처 관계의 `window.open(주소)` 칸(머리만 없다)이 주고받은 것과 견줘 갈랐고, 머리가 실제로 실렸다는 것은 서버의 기록으로 칸마다 봤다(표지).
- **사이트의 페이지가 `Cross-Origin-Opener-Policy: same-origin`을 내면 URL 방식의 통로가 서지 않는다.** 그 사이트는 그 머리의 값을 `same-origin-allow-popups`로 두어야 한다. ADR 0061은 위젯 쪽의 응답 머리만 적었고 사이트 쪽은 적지 않았다.
- **사이트의 페이지를 닫으면 위젯의 창은 물을 곳이 없다는 것을 곧바로 알 수 있고**(`window.opener`가 `null`이다), **사이트의 페이지가 다른 문서로 가면 답이 오지 않는 것으로만 안다**(`window.opener`는 남는다). 프로브는 답을 2초 기다렸다. 옮겨 간 문서에는 답하는 코드가 없었고, 그 문서가 물음을 받았는지는 보지 않았다.

## 재지 못한 것

- Firefox와 WebKit, 제품 브라우저, 휴대폰의 브라우저. 잰 것은 Playwright의 Chromium headless shell 하나다. `rel`을 적지 않은 `target="_blank"` 링크와 `Cross-Origin-Opener-Policy`의 동작은 엔진과 판마다 다를 수 있다(어림).
- 브라우저의 팝업 차단. Playwright는 스크립트가 여는 창을 막지 않는다. 사람이 누른 순간에 여는 창이 막히지 않는지는 이 기능의 e2e가 본다.
- 위젯의 실제 코드와 프록시를 거친 주소. 프록시가 `Cross-Origin-Opener-Policy`를 내는지는 e2e가 본다.
- 사이트의 페이지가 다른 출처의 문서로 가는 경우, 사이트의 페이지를 새로 고친 경우(답하는 코드는 다시 서지만 창 손잡이를 잃는다고 본다, 어림), `Cross-Origin-Opener-Policy`의 다른 값(`noopener-allow-popups`)과 `Cross-Origin-Embedder-Policy`.
- 사이트의 페이지가 iframe 안에서 창을 여는 경우, 위젯의 창이 다시 창을 여는 경우(로그인 창).
