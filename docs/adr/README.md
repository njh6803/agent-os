# ADR 색인

번호열은 하나다. 지역 결정도 여기 넣고 제목에 범위를 적는다. 형식은 domain-modeling 스킬의 ADR-FORMAT(짧게, 결정과 이유). 새 ADR을 쓰면 이 표에 한 줄 더한다.

| 번호 | 제목 | 상태 | 날짜 |
|---|---|---|---|
| [0001](0001-langgraph-as-runtime-engine.md) | LangGraph를 런타임 엔진으로 쓰되 플러그인 계약 뒤에 숨긴다 | accepted | 2026-09-19 |
| [0002](0002-agent-declares-its-mcp-servers.md) | 에이전트는 쓸 MCP 서버를 매니페스트에 명시한다 | accepted | 2026-09-19 |
| [0003](0003-filesystem-is-the-source-of-truth.md) | 플러그인의 진실의 원천은 파일시스템이다 | accepted | 2026-09-19 |
| [0004](0004-place-instructions-by-load-timing.md) | 지침은 로드 시점 기준으로 배치한다 | accepted | 2026-09-20 |

ADR을 먼저 확인하는 상황 넷: 스택이나 라이브러리를 바꿀 때, 디렉터리나 층 경계를 바꿀 때, 디스크 형식(매니페스트, 이벤트)을 바꿀 때, 기존 코드가 왜 이렇게 되어 있는지 이해되지 않을 때.
