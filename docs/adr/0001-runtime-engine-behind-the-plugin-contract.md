---
status: accepted
date: 2026-09-19
---

# LangGraph를 런타임 엔진으로 쓰되 플러그인 계약 뒤에 숨긴다

런타임의 루프, 그리고 뒤에 올 체크포인트와 인터럽트를 직접 짜는 대신 LangGraph로 구현한다. anthropic SDK의 내장 도구 루프로도 첫 슬라이스는 가능했지만, 인터럽트와 되감기를 나중에 직접 만들 비용이 더 크다고 봤다. 플러그인은 `agent_os.sdk`만 보며 LangGraph를 import하지 않는다. 대가는 `langchain-mcp-adapters`가 mcp를 1.x로 고정하는 것과 패키지 30개다. 선행 저장소 ADR 0002가 버린 것은 "UI에서 그리는 선언적 그래프"이지 코드로 쓰는 그래프 라이브러리가 아니므로, "에이전트는 코드 플러그인이다"는 그대로 둔다.

## Consequences

- 첫 슬라이스부터 LangGraph로 만든다. strict 타입 마찰로 2026-09-21까지 LLM 테스트가 초록이 안 되면 SDK 내장 루프로 후퇴하고 이 ADR에 그 사실을 덧붙인다.
- 첫 슬라이스에 체크포인터는 두지 않는다. 둘째 슬라이스에서 `thread_id = run_id`로 붙인다.

## 이력

### 2026-09-21 후퇴: 루프를 langchain-core 위에 직접 쓴다

체크포인트 날짜에 후퇴 조건이 맞아 실행했다. langgraph 1.2.11의 `StateGraph.add_node`, `compile`, `CompiledStateGraph.ainvoke`가 pyright strict에서 전부 "partially unknown"이다. 라이브러리 자신의 시그니처에 `CachePolicy[Unknown]`, `Command[Unknown]`, `BaseCheckpointSaver[Unknown]` 같은 미해결 제네릭이 들어 있어 호출하는 쪽에서 타입을 적어도 사라지지 않고, `ainvoke`의 반환은 `dict[str, Any] | Any`다. 남는 길은 pyright 규칙을 끄는 것뿐인데 그것은 원칙 III 위반이다. 하루를 더 써도 풀리는 종류의 마찰이 아니라서 바로 후퇴했다.

후퇴 대상은 이 ADR이 적은 "anthropic SDK 내장 루프"가 아니라 **langchain-core `BaseChatModel` 위에 직접 쓴 루프**(`core/loop.py`, 40줄)다. 이 ADR 뒤에 ChatModel 포트가 langchain-core 추상 클래스로 정해졌고(`.claude/rules/core.md`), 첫 슬라이스 명세가 "후퇴해도 포트 다섯은 그대로이고 바뀌는 것은 루프 구현 하나"라고 못 박았기 때문이다. anthropic SDK로 가면 포트와 MCP 브리지까지 바뀐다. `langchain-anthropic`, `langchain-mcp-adapters`는 그대로 쓰고 `langgraph`만 의존성에서 뺀다.

슬라이스 2의 인터럽트와 체크포인터는 이 결정을 다시 연다. 그때 langgraph의 타입이 나아졌는지 같은 프로브로 재는 것이 첫 일이고, 아니면 직접 만든다. 이 ADR의 제목은 그때까지 그대로 둔다. 결정의 의도(엔진을 플러그인 계약 뒤에 숨긴다)는 살아 있고 엔진만 바뀌었다.
