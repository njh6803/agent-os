# ticket-cites-path-spec-did-not-assign: **0400의 4회차. 티켓 01이 `web/apps/widget/public/runtime.json`을, 티켓 03이 `.dockerignore`를 들었는데 둘 다 명세가 고칠 자리로 정하지 않은 구현 파일 경로라, 셀프 리뷰 명세 축이 Nit으로 잡았고 그 두 자리를 명세에 정하는 것으로 고쳤다**

**상태:** 열림
**어디로:** `tools/`의 알림 검사 후보: 기능 티켓(`.scratch/<slug>/issues/*.md`)의 백틱 경로 가운데 같은 기능의 `spec.md`, `.claude/rules/`, `docs/adr/`에 없고 시험 파일(`tests/`, `e2e`, `*.test.*`, `*.stories.*`)도 아닌 것을 알린다. 거짓 양성이 많을 수 있어 막는 게이트로 만들지 않는다. 검사로 옮길 수 없으면 `.claude/skills/to-tickets/SKILL.md` 템플릿 뒤 문단에 쓰는 순간 대 보는 문장으로 간다. 다섯 번째에 반영한다
**승인:** 자체 승인 2026-11-27, 0400의 4회차(0400은 30의 3회차), 일지 2026-11-27-1523-widget-runtime-values-tickets.md. ADR 불필요
