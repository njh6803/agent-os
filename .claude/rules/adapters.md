---
paths:
  - "src/agent_os/adapters/**"
---

# adapters 규칙

- 어댑터는 core가 선언한 포트 Protocol을 상속하지 않는다. 시그니처로 만족한다. 드리프트는 테스트 픽스처의 포트 타입 annotate가 잡는다(`.claude/rules/tests.md`).
- 파일, DB, 외부 서비스, 시계에 닿는 코드는 여기에만 산다. core로 새면 원칙 IV 위반이다.
- 어댑터는 channel과 admin을 import하지 않는다. 조립은 `main.py`와 `server.py`가 한다.
- 첫 슬라이스의 어댑터: JSONL TraceSink(`traces/<run_id>.jsonl`, 첫 줄 헤더에 `schema_version`), 파일시스템 PluginSource, MCP ToolSource(langchain-mcp-adapters), 시스템 Clock(UTC, uuid4). ChatAnthropic 인스턴스는 `adapters/anthropic.py`의 factory로 `main.py`가 만든다. 어댑터는 자기를 스스로 조립하지 않는다.
- 반환은 항상 새 객체다. 인자로 받은 객체를 제자리에서 바꿔 결과를 돌려주지 않는다.
