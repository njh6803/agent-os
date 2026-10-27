# 02: 관리 화면의 organisms가 데이터와 처리기를 props로 받고, 서버 데이터와 토큰은 pages가 읽는다

**What to build:** 관리 화면의 organisms가 SWR 훅과 토큰 스토어(`useTokens`)를 직접 부르지 않고, 보일 데이터와 읽는 상태(처음 가져오는 중, 다시 확인하는 중, 실패)와 처리기(켜고 끄기, 결정 보내기, 토큰 넣기와 지우기, 새로 고침, 더 보기)를 props로 받는다. 훅과 스토어를 부르는 것은 pages다. 운영자에게 보이는 것은 하나도 바뀌지 않는다. 이 옮기기가 있어야 03 이후의 티켓이 organisms를 가짜 네트워크 없이 Storybook에 그리고, 화면마다 그림의 상태를 스토리 하나씩으로 둔다.

근거는 `.scratch/admin-style/spec.md` Testing Decisions "모양"의 organisms 줄과 그 2026-10-27 명세 검토 주석(토큰 스토어도 props로, 보이는 것을 바꾸지 않는 앞 티켓, `web-admin.md`의 경로 문장), Further Notes의 티켓 차례 주석이다. 위젯의 organisms가 선례다(`web/apps/widget/components/organisms/`). Storybook에 가짜 네트워크(`msw-storybook-addon`)는 들이지 않는다. 이 티켓은 화면 파일을 따르지 않으므로 웹 편집 확인 없이 돈다.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

### 옮기기

- [ ] **organisms 층의 어느 파일도 `hooks/queries`의 훅과 토큰 스토어를 부르지 않는다.** pages가 부르고 그 값과 처리기를 props로 넘긴다. 데이터를 가져와 채우는 층이 pages뿐이 된다(`.claude/rules/web-workspace.md`의 templates 기준을 organisms까지 넓힌 것)
- [ ] 다시 읽다 실패하면 보인 것을 지우는 행동은 지금처럼 읽기 골격 한 자리에 있다(`.claude/rules/web-admin.md`). 골격이 훅의 결과를 직접 받던 모양이면 같은 뜻의 props로 받는다
- [ ] 결정 자리의 꺼짐 미리 알림이 플러그인 목록을 읽는 자리가 pages로 옮기면, `.claude/rules/web-admin.md`에서 그 행동의 자리를 경로로 든 문장을 옮긴 자리에 맞게 고친다
- [ ] **지금의 페이지 시험과 e2e를 고치지 않고 초록이다.** 고쳐야 초록이 되면 보이는 것이 바뀐 것이니 멈추고 까닭을 본다. e2e는 CI의 `e2e` 잡이 본다

### 경계를 무엇이 지키나

- [ ] 지금 판정자(`web/eslint.config.mjs`의 층 정책)는 organisms가 `hooks/queries`와 생성 클라이언트를 import하는 것을 허락한다. `web/eslint.config.test.ts`가 지나보낼 사례로 고정한 것은 organisms가 생성 클라이언트 패키지와 `api` barrel을 import하는 둘이고, `hooks/queries`는 barrel을 거치지 않는 import의 위반 사례에만 나온다. `docs/constitution/tech.md`의 프론트 구성도 "API 호출은 organisms 이상만"이라 적는다. 이 옮기기가 세운 경계("organisms는 훅과 스토어를 부르지 않는다")를 판정자로 막는 것은 그 층 경계를 바꾸는 결정이다(`CLAUDE.md` 작업 규약 1·5). 그래서 ADR 0021(`docs/adr/0021-web-workspace-stack.md`)에 이력 초안을 쓰고 셀프 리뷰를 반영한 뒤 사용자에게 보여 승인을 받는다
  - 승인되면 층 정책에 그 금지를 더하고, `web/eslint.config.test.ts`에 organisms가 `hooks/queries` barrel을 import하는 위반 사례를 더하며, 금지가 생성 클라이언트나 `api`까지 넓으면 지나보낼 사례 둘도 위반 사례로 바꾼다(기대한 규칙 ID를 본다, `.claude/rules/web-workspace.md`). 어디까지 막을지는 ADR 초안이 정한다. `tech.md`의 그 문장을 고친다. 훅이 아닌 함수가 같은 폴더에서 오면 그것도 막히니 옮길 자리를 함께 정한다
  - 거절되면 `.claude/rules/web-workspace.md`의 templates 줄을 organisms까지 넓혀 지침으로 둔다
  - 어느 쪽인지와 그 까닭을 이 티켓의 "이 티켓이 정한 것"에 적는다

### 검증

- [ ] 검증 명령이 모두 초록이다(`CLAUDE.md` 검증 명령. 판정자를 바꿨으면 `pnpm -C web verify`가 그 사례를 돈다. 모델 경로를 건드리지 않아 `-m llm`·`-m llm_widget`은 칠 일이 없다)
