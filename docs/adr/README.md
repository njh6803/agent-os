# ADR 색인

번호열은 하나다. 지역 결정도 여기 넣고 제목에 범위를 적는다. 형식은 domain-modeling 스킬의 ADR-FORMAT(짧게, 결정과 이유). 새 ADR을 쓰면 이 표에 한 줄 더한다.

| 번호 | 제목 | 상태 | 날짜 |
|---|---|---|---|
| [0001](0001-runtime-engine-behind-the-plugin-contract.md) | 런타임 엔진은 플러그인 계약 뒤에 숨긴다 | accepted | 2026-09-19 |
| [0002](0002-agent-declares-its-mcp-servers.md) | 에이전트는 쓸 MCP 서버를 매니페스트에 명시한다 | accepted | 2026-09-19 |
| [0003](0003-filesystem-is-the-source-of-truth.md) | 플러그인의 진실의 원천은 파일시스템이다 | accepted | 2026-09-19 |
| [0004](0004-place-instructions-by-load-timing.md) | 지침은 로드 시점 기준으로 배치한다 | accepted | 2026-09-20 |
| [0005](0005-remote-ci-pr-from-day-one.md) | 원격, CI, PR은 첫날부터다 | accepted | 2026-09-20 |
| [0006](0006-review-pipeline.md) | 리뷰는 두 단계 세 축이다 | accepted | 2026-09-20 |
| [0007](0007-pytest-asyncio-auto-mode.md) | 비동기 테스트는 pytest-asyncio auto 모드로 돌린다 | accepted | 2026-09-21 |
| [0008](0008-manifest-schema-version-and-event-principal.md) | 매니페스트는 형식 버전을, 시작 이벤트는 주체를 필수로 가진다 | accepted | 2026-09-21 |
| [0009](0009-resume-by-replaying-the-trace.md) | 일시정지한 실행은 트레이스를 재생해 재개한다 | accepted | 2026-09-21 |
| [0010](0010-http-surface-assembled-by-server.md) | HTTP 표면은 FastAPI로 서고 `server.py` 하나가 조립한다 | accepted | 2026-09-22 |
| [0011](0011-admin-api-is-fail-closed.md) | 관리 API는 fail-closed 토큰 인증으로 선다 | accepted | 2026-09-22 |
| [0012](0012-ports-stay-five-lists-are-added.md) | 포트는 다섯 그대로이고 기존 포트에 목록이 는다 | accepted | 2026-09-22 |
| [0013](0013-principle-iii-has-its-own-judge.md) | 원칙 III의 판정자는 pyright가 아니라 전용 검사 하나다 | accepted | 2026-09-22 |
| [0014](0014-http-channel-streams-the-run.md) | HTTP 채널의 응답은 실행의 이벤트 스트림이고 실행은 연결에 묶이지 않는다 | accepted | 2026-09-24 |
| [0015](0015-http-channel-has-its-own-token.md) | HTTP 채널은 자기 토큰으로 서고 주체는 `serve`의 OS 사용자다 | accepted | 2026-09-24 |
| [0016](0016-shared-http-layer.md) | HTTP 표면의 공용 배관은 `agent_os.http` 층에 둔다 | accepted | 2026-09-24 |
| [0017](0017-plugin-enablement-lives-in-an-operator-file.md) | 플러그인의 켜짐은 플러그인 루트의 운영자 파일이 든다 | accepted | 2026-09-26 |
| [0018](0018-plugin-boundary-is-judged-by-a-test.md) | 원칙 IV의 플러그인 경계는 import-linter가 아니라 테스트가 판정한다 | accepted | 2026-09-28 |
| [0019](0019-admin-ui-browser-holds-the-tokens.md) | 관리 화면은 브라우저가 토큰을 들고 Next는 무상태 중계다 | accepted | 2026-09-28 |
| [0020](0020-principle-iii-covers-typescript.md) | 원칙 III은 TypeScript에도 걸리고 typescript-eslint가 판정한다 | accepted | 2026-09-28 |
| [0021](0021-web-workspace-stack.md) | web 워크스페이스의 스택과 API 클라이언트는 계약에서 생성해 커밋한다 | accepted | 2026-09-28 |
| [0022](0022-conversation-is-a-chain-of-finished-runs.md) | 대화는 끝난 실행을 가리키는 고리이고 에이전트는 자기 교환과 요약만 안다 | accepted | 2026-10-03 |
| [0023](0023-end-user-channel-is-signed-by-the-site.md) | 최종 사용자는 사이트가 서명한 토큰으로 자기 접두사의 채널을 쓰고 스트림은 걸러 받는다 | accepted | 2026-10-03 |
| [0024](0024-widget-app-ships-two-embeds-behind-nginx.md) | 위젯은 한 앱 폴더에서 iframe 페이지와 페이지 안 번들을 내고 nginx 뒤에 선다 | accepted | 2026-10-03 |
| [0025](0025-design-system-source-is-code.md) | 디자인 시스템은 코드가 원천이고 Claude Design은 탐색과 화면을 맡는다 | accepted | 2026-10-03 |
| [0026](0026-design-system-is-one-package-judged-by-storybook.md) | 디자인 시스템은 `packages/ui` 하나에 px 디자인 토큰과 두 테마를 두고, Storybook과 컨테이너 안의 사진으로 판정한다 | accepted | 2026-10-06 |
| [0027](0027-workflow-hardening-is-judged-by-zizmor.md) | 워크플로 하드닝은 zizmor가 판정하고, 판은 uv 개발 의존성이 고정한다 | accepted | 2026-10-07 |

ADR을 먼저 확인하는 상황 넷: 스택이나 라이브러리를 바꿀 때, 디렉터리나 층 경계를 바꿀 때, 디스크 형식(매니페스트, 이벤트)을 바꿀 때, 기존 코드가 왜 이렇게 되어 있는지 이해되지 않을 때.
