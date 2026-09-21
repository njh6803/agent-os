---
paths:
  - "src/agent_os/core/**"
---

# core 규칙

헥사고날은 core가 프로세스 밖과 닿는 지점에만 쓴다. 포트는 다섯이고 닫힌 목록이다.

| 포트 | 무엇 | 첫 어댑터 |
|---|---|---|
| TraceStore | 이벤트 쓰기와 한 실행의 트레이스 읽기 | JSONL 파일 |
| PluginSource | 매니페스트와 코드 읽기 | 파일시스템(ADR 0003) |
| ToolSource | 도구 목록과 호출 | MCP(langchain-mcp-adapters) |
| ChatModel | 모델 호출 | langchain-anthropic. 포트 자체는 langchain-core의 추상 클래스 |
| Clock | 시각과 run_id | 시스템 시계, uuid4 |

- 포트를 더하려면 core가 바깥과 닿는 새 지점이어야 하고 ADR을 남긴다.
- 유스케이스 클래스, 커맨드·결과 객체, 도메인별 포트는 두지 않는다. 채널과 관리는 core의 함수와 클래스를 직접 부른다.
- core는 `langchain_anthropic`, `langchain_mcp_adapters`, channel, admin, adapters를 import하지 않는다. import-linter가 판정한다. 프로바이더 교체는 core 밖의 일이다.
- 루프는 `core/loop.py`가 langchain-core `BaseChatModel` 위에 직접 돌린다. 플러그인은 그것을 모른다(ADR 0001과 그 2026-09-21 이력 둘).
- `secret_args`로 선언된 인자는 core 가 이벤트를 만들 때 가린다. 어댑터가 아니다. 원칙 V 가 금하는 것이 파일이 아니라 이벤트이고 `secret_args`를 아는 것도 core 이기 때문이다(ADR 0009). 실제 도구 호출에는 진짜 값이 간다.
- 체크포인터라는 부품은 두지 않는다. 일시정지한 실행은 트레이스를 재생해 재개한다(ADR 0009). 재생이 성립하려면 `run()`에 들어가는 비결정적인 값이 전부 `AgentContext`를 지나야 한다.
- `run_started`와 `run_failed`는 런타임이 발행한다. 에이전트는 `RunFinished` 하나를 마지막에 yield하고, 에이전트가 yield한 다른 이벤트는 그대로 통과시킨다.
- 실패 정책: MCP 서버 시작 실패는 `run_failed`. 도구 에러는 `tool_called(ok=false)`로 모델에 되돌려 계속. 루프 상한은 10턴. LLM API 에러는 SDK 재시도 뒤 `run_failed`. `secret_args`와 `requires_approval`이 겹치는 매니페스트는 실행 식별자가 생기기 전에 `PluginError`이고 트레이스가 없다(ADR 0009).
