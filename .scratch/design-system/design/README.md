# design-system 화면과 탐색

Claude Design에서 그리거나 고른 것을 내보낸 자리다. 규약은 `docs/agents/issue-tracker.md`의 화면 디자인 절이다. 탐색을 시작하는 프롬프트는 `exploration-prompt.md`다.

기본 테마: 먹(`muk`). 2026-10-06 명세 세션에서 사용자가 Claude Design의 추천대로 골랐다(ADR 0026의 둘째 2026-10-06 이력).

내보낸 파일을 내려받아 이 폴더에 옮기고 아래 표를 채우는 일은 명세 세션이 한다. 차례는 `exploration-prompt.md`의 "고른 뒤"다.

`Agent OS 디자인 시스템 v3.dc.html`은 Claude Design의 Project archive(ZIP)에서 푼 것이고, 같은 폴더의 `support.js`가 있어야 브라우저에서 그려진다(글꼴은 Google Fonts에서 받는다). 디자인 토큰의 hex 값은 파일에 글자로 들어 있지 않고 파일 끝의 스크립트가 계산한다. 값을 뽑는 길은 `.scratch/design-system/probes/tokens/design.mjs`다.

| 파일 | 근거 문서 | 기준 커밋 | 동기화한 커밋 |
|---|---|---|---|
| `Agent OS 디자인 시스템 v3.dc.html` | `.scratch/design-system/design/exploration-prompt.md`, `docs/adr/0026-design-system-is-one-package-judged-by-storybook.md` | `eff1542` (어림) | 없음 |
