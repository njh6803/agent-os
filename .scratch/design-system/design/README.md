# design-system 화면과 탐색

Claude Design에서 그리거나 고른 것을 내보낸 자리다. 규약은 `docs/agents/issue-tracker.md`의 화면 디자인 절이다. 탐색을 시작하는 프롬프트는 `exploration-prompt.md`(2026-10-06 첫 탐색)이고, 관리 화면 기준의 재탐색은 `refresh-prompt.md`(2026-10-12)다.

기본 테마: 녹청(`nokcheong`). 2026-10-12 재탐색에서 사용자가 추천을 맨 앞에 둔 선택 화면으로 골랐다(ADR 0026의 2026-10-12 이력 "테마는 넷이고 색만 바꾸며, 글꼴은 모든 테마가 Noto Sans KR과 Noto Sans Mono를 쓴다"). 코드는 design-refresh가 반영하기 전까지 옛 기본 테마 먹(`muk`)이다. 먹은 2026-10-06 명세 세션에서 사용자가 Claude Design의 추천대로 골랐다(둘째 2026-10-06 이력).

내보낸 파일을 내려받아 이 폴더에 옮기고 아래 표를 채우는 일은 명세 세션이 한다. 차례는 `exploration-prompt.md`의 "고른 뒤"다. 재탐색(2026-10-12)은 `refresh-prompt.md`의 "고른 뒤"대로 했고, 그 뒤는 명세가 아니라 ADR 0026의 새 이력과 반영이다.

`Agent OS Design System.dc.html`은 재탐색의 디자인 시스템 문서이고, `Agent OS Pairings.dc.html`은 고르기 전에 네 안을 나란히 그린 비교판이다. 비교판에는 바꾸기 전의 안 이름과 옛 상태 이름이 남아 있고, 밀도의 이름과 수치도 최종과 다르다(비교판의 "보통"이 최종의 촘촘이다). 값은 `Agent OS Design System.dc.html`에서만 읽는다. 두 파일도 같은 폴더의 `support.js`로 그려진다(새 ZIP의 `support.js`가 옛 것과 바이트까지 같았다). 디자인 토큰의 hex 값은 파일 끝의 스크립트가 계산하고, 그 스크립트의 `renderVals()`가 돌려주는 `tokensJson`이 디자인 토큰 JSON이다. 값을 뽑는 프로브 `design.mjs`는 v3만 읽는다(키가 `tokJson`이고 테마 이름이 다르다). 새 파일을 읽는 길은 반영하는 기능이 그 프로브를 고쳐 만든다.

`Agent OS 디자인 시스템 v3.dc.html`은 Claude Design의 Project archive(ZIP)에서 푼 것이고, 같은 폴더의 `support.js`가 있어야 브라우저에서 그려진다(글꼴은 Google Fonts에서 받는다). 디자인 토큰의 hex 값은 파일에 글자로 들어 있지 않고 파일 끝의 스크립트가 계산한다. 값을 뽑는 길은 `.scratch/design-system/probes/tokens/design.mjs`다.

| 파일 | 근거 문서 | 기준 커밋 | 동기화한 커밋 |
|---|---|---|---|
| `Agent OS 디자인 시스템 v3.dc.html` | `.scratch/design-system/design/exploration-prompt.md`, `docs/adr/0026-design-system-is-one-package-judged-by-storybook.md` | `eff1542` (어림) | 없음 |
| `Agent OS Design System.dc.html` | `.scratch/design-system/design/refresh-prompt.md`, `docs/adr/0026-design-system-is-one-package-judged-by-storybook.md` | `15e41a6` | 없음 |
| `Agent OS Pairings.dc.html` | `.scratch/design-system/design/refresh-prompt.md`, `docs/adr/0026-design-system-is-one-package-judged-by-storybook.md` | `15e41a6` | 없음 |
