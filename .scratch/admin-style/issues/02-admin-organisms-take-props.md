# 02: 관리 화면의 organisms가 데이터와 처리기를 props로 받고, 서버 데이터와 토큰은 pages가 읽는다

**What to build:** 관리 화면의 organisms가 SWR 훅과 토큰 스토어(`useTokens`)를 직접 부르지 않고, 보일 데이터와 읽는 상태(처음 가져오는 중, 다시 확인하는 중, 실패)와 처리기(켜고 끄기, 결정 보내기, 토큰 넣기와 지우기, 새로 고침, 더 보기)를 props로 받는다. 훅과 스토어를 부르는 것은 pages다. 운영자에게 보이는 것은 하나도 바뀌지 않는다. 이 옮기기가 있어야 03 이후의 티켓이 organisms를 가짜 네트워크 없이 Storybook에 그리고, 화면마다 그림의 상태를 스토리 하나씩으로 둔다.

근거는 `.scratch/admin-style/spec.md` Testing Decisions "모양"의 organisms 줄과 그 2026-10-27 명세 검토 주석(토큰 스토어도 props로, 보이는 것을 바꾸지 않는 앞 티켓, `web-admin.md`의 경로 문장), Further Notes의 티켓 차례 주석이다. 위젯의 organisms가 선례다(`web/apps/widget/components/organisms/`). Storybook에 가짜 네트워크(`msw-storybook-addon`)는 들이지 않는다. 이 티켓은 화면 파일을 따르지 않으므로 웹 편집 확인 없이 돈다.

**Blocked by:** None (can start immediately)

**Status:** done

### 옮기기

- [x] **organisms 층의 어느 파일도 `hooks/queries`의 훅과 토큰 스토어를 부르지 않는다.** pages가 부르고 그 값과 처리기를 props로 넘긴다. 데이터를 가져와 채우는 층이 pages뿐이 된다(`.claude/rules/web-workspace.md`의 templates 기준을 organisms까지 넓힌 것)
- [x] 다시 읽다 실패하면 보인 것을 지우는 행동은 지금처럼 읽기 골격 한 자리에 있다(`.claude/rules/web-admin.md`). 골격이 훅의 결과를 직접 받던 모양이면 같은 뜻의 props로 받는다
- [x] 결정 자리의 꺼짐 미리 알림이 플러그인 목록을 읽는 자리가 pages로 옮기면, `.claude/rules/web-admin.md`에서 그 행동의 자리를 경로로 든 문장을 옮긴 자리에 맞게 고친다
- [x] **지금의 페이지 시험과 e2e를 고치지 않고 초록이다.** 고쳐야 초록이 되면 보이는 것이 바뀐 것이니 멈추고 까닭을 본다. e2e는 CI의 `e2e` 잡이 본다

### 경계를 무엇이 지키나

- [x] 지금 판정자(`web/eslint.config.mjs`의 층 정책)는 organisms가 `hooks/queries`와 생성 클라이언트를 import하는 것을 허락한다. `web/eslint.config.test.ts`가 지나보낼 사례로 고정한 것은 organisms가 생성 클라이언트 패키지와 `api` barrel을 import하는 둘이고, `hooks/queries`는 barrel을 거치지 않는 import의 위반 사례에만 나온다. `docs/constitution/tech.md`의 프론트 구성도 "API 호출은 organisms 이상만"이라 적는다. 이 옮기기가 세운 경계, 곧 organisms가 훅과 스토어를 부르지 않는다는 것을 판정자로 막는 것은 그 층 경계를 바꾸는 결정이다(`CLAUDE.md` 작업 규약 1·5). 그래서 ADR 0021(`docs/adr/0021-web-workspace-stack.md`)에 이력 초안을 쓰고 셀프 리뷰를 반영한 뒤 사용자에게 보여 승인을 받는다
  - 승인되면 층 정책에 그 금지를 더하고, `web/eslint.config.test.ts`에 organisms가 `hooks/queries` barrel을 import하는 위반 사례를 더하며, 금지가 생성 클라이언트나 `api`까지 넓으면 지나보낼 사례 둘도 위반 사례로 바꾼다(기대한 규칙 ID를 본다, `.claude/rules/web-workspace.md`). 어디까지 막을지는 ADR 초안이 정한다. `tech.md`의 그 문장을 고친다. 훅이 아닌 함수가 같은 폴더에서 오면 그것도 막히니 옮길 자리를 함께 정한다
  - 거절되면 `.claude/rules/web-workspace.md`의 templates 줄을 organisms까지 넓혀 지침으로 둔다
  - 어느 쪽인지와 그 까닭을 이 티켓의 "이 티켓이 정한 것"에 적는다

### 검증

- [x] 검증 명령이 모두 초록이다(`CLAUDE.md` 검증 명령. 판정자를 바꿨으면 `pnpm -C web verify`가 그 사례를 돈다. 모델 경로를 건드리지 않아 `-m llm`·`-m llm_widget`은 칠 일이 없다)

### 이 티켓이 정한 것

- **경계는 판정자가 막는다.** 사용자가 ADR 0021의 2026-10-27 이력 초안을 승인했다(2026-10-27, 일지 2026-10-27-10). organisms·templates가 `hooks/queries`·`stores`·`swr`·생성 클라이언트·`api/failure` 밖의 `api/` 도메인을 값으로 import하면 `boundaries/dependencies`가 빨갛고, atoms·molecules도 `stores`를 import하지 않는다. `import type`과 `api/failure`는 지난다. organisms가 값으로 쓰는 `api/`는 요청 함수가 없는 `api/failure`뿐이고, 요청 함수가 든 도메인에서는 타입만 `import type`으로 가져오기 때문이다. 판정자는 import한 파일이 놓인 자리만 보므로, 요청 함수가 막지 않는 자리(`api/failure`, `hooks/queries` 밖의 훅, `lib/`의 함수)를 거쳐 organisms에 닿는 길은 `.claude/rules/web-workspace.md`의 templates 줄에 지침으로 둔다(organisms는 서버 요청을 props로 받은 처리기로만 일으킨다). 훅이 아닌데 `hooks/queries`에 있던 `isRejection`은 `api/failure`로 옮겼다. 지나보낼 사례 둘(생성 클라이언트, `api` barrel)은 모두 위반 사례로 옮기고, barrel 판정 사례와 barrel을 거친 import 사례는 pages로 옮겼다. 셀프 리뷰가 organism의 `swr`·요청 함수 import가 지나는 반례를 찾아 `swr`를 막는 범위에 더했고, PR 직전 버그 축 리뷰가 `api/`를 막지 않는 까닭으로 든 문장("같은 barrel의 응답 타입과 실패 해석")이 사실과 다르다는 것을 찾아 `api/failure` 밖의 `api/`도 막는 범위에 더했다(사용자가 이 넓힘을 2026-10-27에 다시 승인했다, 일지 2026-10-27-10).
- **훅을 마운트하는 깊이.** pages가 옮기기 전의 organism 자리에 `Connected*` 컴포넌트(`ConnectedPluginList`, `ConnectedPluginDetail`, `ConnectedRunList`, `ConnectedRunDetail`, `ConnectedRunDecision`)를 두고 그 안에서 훅을 부른다. 그 자리는 관리 토큰이 받아들여진 뒤, 주소를 푼 뒤에만 서서 요청이 시작되는 때가 옮기기 전과 같다. 토큰 스토어는 `AdminScreen`이 읽어 넣는 자리 둘에 넘긴다. 결정의 훅(`useDecision`)은 `RunDetail`의 `decision` 슬롯, 곧 트레이스 값의 갈래 안에서 부른다. 다시 읽다 실패하면 그 훅도 함께 걷혀 보낸 결정의 연결을 끊는 옮기기 전 동작을 지킨다. 꺼짐 미리 알림의 목록은 `usePlugins(decisionPlaceStands(…))`로 결정 자리가 설 때만 읽는다.
- **시험이 고정하지 않는 두 자리.** 결정 자리가 서지 않을 때 목록을 읽지 않는 것과, 결정의 훅이 트레이스 값의 갈래 안에 서는 것이다. 실행 하나의 시험은 관리 토큰 확인 때문에 `GET /plugins`에 늘 빈 목록을 답해 더 읽은 목록이 처리하지 않은 요청이 되지 않고, 목록 요청의 수를 세는 시험도 없다. 변이 표(`.scratch/admin-style/probes/organisms_props_mutations.toml`)의 첫째와 다섯째가 그 자리를 깨도 초록인 것을 적는다. 옮기기 전에도 고정되지 않던 자리이고 이 티켓의 체크박스가 요구하지 않아 시험을 더하지 않았다.
