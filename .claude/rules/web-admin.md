---
paths:
  - "web/apps/admin/**"
---

# 관리 화면 앱 규칙

워크스페이스 공통 기준은 `web-workspace.md`다. 여기는 이 앱에만 걸리는 판단 기준이다. 바인딩과 상류의 루프백, 서버 파일과 Server Actions, `app/`의 import는 시작 래퍼·설정 파일·판정자가 판정하므로 적지 않는다.

- Next 코드를 쓰기 전에 설치본의 해당 가이드(`web/apps/admin/node_modules/next/dist/docs/`)를 읽는다. 이 판은 API, 관례, 파일 구조가 학습 데이터와 다를 수 있고, 가이드의 폐기 안내를 따른다. `next.config.ts`의 `agentRules: false`가 끈 블록의 요지다(ADR 0021).
- Next의 판을 바꾸면 `.scratch/web-admin/probes/admin_relay.mjs`를 다시 돈다. `rewrites`가 빌드에 박히는지, IPv6 목적지를 컴파일하는지, 압축이 꺼졌는지가 판마다 다를 수 있다(ADR 0011의 2026-09-30 이력). 판을 고정한 테스트(`tools/next-version.test.ts`)가 올리는 순간 빨개져 계기를 준다. 결과가 달라졌으면 그 값과 함께 설정이나 ADR 이력을 고친다.
- 서버 데이터를 다시 읽다 실패하면 이미 보인 것을 지우고 실패만 보인다. `web-workspace.md`의 "다시 확인하는 동안 보인 것을 지우지 않는다"는 응답을 기다리는 동안의 일이다. 운영자가 무엇이 꺼져 있는지 모르는 채 옛 값을 믿지 않게 한다(web-admin 스토리 16, 티켓 05에서 사용자가 골랐다). 플러그인 목록은 페이지 테스트가 이 행동을 고정한다.
