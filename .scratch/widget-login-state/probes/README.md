# widget-login-state 프로브

widget-login-state의 명세(`.scratch/widget-login-state/spec.md`)가 근거로 든 측정 스크립트의 색인이다. 규약은 `docs/agents/issue-tracker.md`의 "프로브와 근거", 짓는 규칙은 `.claude/rules/probes.md`다. 이 폴더의 코드는 프로브의 것이고 제품 코드가 아니다. 프로브의 폴더에 든 `README.md`가 돌리는 법, 판, 결과, 재지 못한 것의 원천이고, 아래 표는 한 줄씩의 길잡이다. `kit.mjs`는 두 프로브가 함께 쓰는 것(자체 서명 인증서, 이름을 127.0.0.1에 맞추는 프록시, `expected.json`과의 견줌)이고 스스로 재는 것이 없다.

| 파일 | 재는 것 | 근거로 드는 자리 | 다시 돌 때 | 잰 판 |
|---|---|---|---|---|
| `logout_fetch/` | 위젯이 로그아웃 주소를 창 없이 부를 때(본문 없는 POST, `credentials: "include"`) 브라우저가 사이트의 쿠키를 싣고 응답의 지우는 `Set-Cookie`를 받아들이는지. 위젯이 도는 자리 일곱(페이지 안 방식 셋, iframe 방식 둘, URL 방식 둘)과 쿠키의 `SameSite` 셋과 부르는 법 다섯(명세가 고른 `mode: "cors"`, `redirect: "manual"` 포함)을 곱해 보고, 끝점이 받는 `Origin`과 `Sec-Fetch-Site`, 위젯 쪽 `fetch`의 끝을 본다. 끝점이 303으로 답할 때는 같은 자리와 `SameSite`에서 `redirect`의 두 값을 본다 | 명세의 "로그아웃" 절, ADR 0061 이력 2026-11-16 | `web/`의 의존성, Playwright의 Chromium, `openssl`. 네트워크를 타지 않는다. 약 4분. 명령은 `logout_fetch/README.md` "다시 돌리기" | Playwright 1.63.0, Chromium 153.0.8010.12, Node v24.19.0, OpenSSL 1.1.1k, Windows 10. Firefox와 WebKit은 재지 못했다 |
| `opener_message/` | URL 방식의 창이 자기를 연 페이지(`window.opener`)와 물음과 답을 주고받는지. 위젯의 창의 출처 셋(사이트의 페이지와 같은 출처, 등록 도메인이 같은 다른 출처, 등록 도메인이 다른 출처)과 여는 법과 그 뒤의 일 열하나(`window.open`, 크기를 준 창, `noopener`, 링크 둘, `Cross-Origin-Opener-Policy`를 실은 응답 셋, 위젯의 창 새로 고침, 사이트의 페이지가 옮겨 감, 사이트의 페이지를 닫음)를 곱해 본다 | 명세의 "URL 방식" 절과 "재지 않은 것이 어긋났을 때" 절, ADR 0061 이력 2026-11-16 | 위와 같다. 약 20초. 명령은 `opener_message/README.md` "다시 돌리기" | 위와 같다 |
