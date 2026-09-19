---
paths:
  - "src/agent_os/core/**"
---

# core 규칙

헥사고날은 core가 프로세스 밖과 닿는 지점에만 쓴다. 포트는 다섯이고 닫힌 목록이다.

| 포트 | 무엇 | 첫 어댑터 |
|---|---|---|
| TraceSink | 이벤트 쓰기 | JSONL 파일 |
| PluginSource | 매니페스트와 코드 읽기 | 파일시스템(ADR 0003) |
| ToolSource | 도구 목록과 호출 | MCP(langchain-mcp-adapters) |
| ChatModel | 모델 호출 | langchain-anthropic. 포트 자체는 langchain-core의 추상 클래스 |
| Clock | 시각과 run_id | 시스템 시계, uuid4 |

- 포트를 더하려면 core가 바깥과 닿는 새 지점이어야 하고 ADR을 남긴다.
- 유스케이스 클래스, 커맨드·결과 객체, 도메인별 포트는 두지 않는다. 채널과 관리는 core의 함수와 클래스를 직접 부른다.
- core는 `langchain_anthropic`, `langchain_mcp_adapters`, channel, admin, adapters를 import하지 않는다. import-linter가 판정한다. 프로바이더 교체는 core 밖의 일이다.
- 런타임은 LangGraph로 루프를 돌린다. 플러그인은 그것을 모른다(ADR 0001). 첫 슬라이스에는 체크포인터를 두지 않는다.
- `run_started`와 `run_failed`는 런타임이 발행한다. 에이전트는 `RunFinished` 하나를 마지막에 yield하고, 에이전트가 yield한 다른 이벤트는 그대로 통과시킨다.
- 실패 정책: MCP 서버 시작 실패는 `run_failed`. 도구 에러는 `tool_called(ok=false)`로 모델에 되돌려 계속. 루프 상한은 10턴. LLM API 에러는 SDK 재시도 뒤 `run_failed`.
