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

ADR을 먼저 확인하는 상황 넷: 스택이나 라이브러리를 바꿀 때, 디렉터리나 층 경계를 바꿀 때, 디스크 형식(매니페스트, 이벤트)을 바꿀 때, 기존 코드가 왜 이렇게 되어 있는지 이해되지 않을 때.
