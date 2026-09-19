---
status: accepted
date: 2026-09-19
---

# LangGraph를 런타임 엔진으로 쓰되 플러그인 계약 뒤에 숨긴다

런타임의 루프, 그리고 뒤에 올 체크포인트와 인터럽트를 직접 짜는 대신 LangGraph로 구현한다. anthropic SDK의 내장 도구 루프로도 첫 슬라이스는 가능했지만, 인터럽트와 되감기를 나중에 직접 만들 비용이 더 크다고 봤다. 플러그인은 `agent_os.sdk`만 보며 LangGraph를 import하지 않는다. 대가는 `langchain-mcp-adapters`가 mcp를 1.x로 고정하는 것과 패키지 30개다. 선행 저장소 ADR 0002가 버린 것은 "UI에서 그리는 선언적 그래프"이지 코드로 쓰는 그래프 라이브러리가 아니므로, "에이전트는 코드 플러그인이다"는 그대로 둔다.

## Consequences

- 첫 슬라이스부터 LangGraph로 만든다. strict 타입 마찰로 2026-09-21까지 LLM 테스트가 초록이 안 되면 SDK 내장 루프로 후퇴하고 이 ADR에 그 사실을 덧붙인다.
- 첫 슬라이스에 체크포인터는 두지 않는다. 둘째 슬라이스에서 `thread_id = run_id`로 붙인다.
