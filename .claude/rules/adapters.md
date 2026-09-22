---
paths:
  - "src/agent_os/adapters/**"
---

# adapters 규칙

- 어댑터는 core가 선언한 포트 Protocol을 상속하지 않는다. 시그니처로 만족한다. 드리프트는 테스트 픽스처의 포트 타입 annotate가 잡는다(`.claude/rules/tests.md`).
- 파일, DB, 외부 서비스, 시계에 닿는 코드는 여기에만 산다. core로 새면 원칙 IV 위반이다.
- 어댑터는 channel과 admin을 import하지 않는다. 조립은 `main.py`와 `server.py`가 한다.
- 첫 슬라이스의 어댑터: JSONL TraceStore(`traces/<run_id>.jsonl`, 첫 줄 헤더에 `schema_version`. 한 실행을 쓴 순서대로 읽고 형식 1 파일도 읽는다. 목록은 디렉터리를 훑어 실행 요약을 만든다), 파일시스템 PluginSource(종류 디렉터리를 훑어 매니페스트 목록을 만든다), MCP ToolSource(langchain-mcp-adapters), 시스템 Clock(UTC, uuid4). ChatAnthropic 인스턴스는 `adapters/anthropic.py`의 factory로 `main.py`가 만든다. 어댑터는 자기를 스스로 조립하지 않는다.
- 반환은 항상 새 객체다. 인자로 받은 객체를 제자리에서 바꿔 결과를 돌려주지 않는다.
- JSONL 목록은 단건 읽기를 재사용하지 않고 파일마다 헤더와 첫 줄과 마지막 줄만 파싱한다. 전부 파싱하면 목록 하나가 모든 실행의 모든 이벤트를 메모리에 올리고 `limit`은 그 뒤에 자르므로 도움이 되지 않는다. 그래서 가운데 줄이 깨진 파일은 목록에서 요약으로 나오고 단건에서 `PluginError`다. 매니페스트 목록은 반대로 단건 읽기를 그대로 부른다 — 파일 하나가 작고, 디렉터리와 `kind`·`name`이 맞는지 보는 검사가 거기 있다.
- 첫 어댑터는 디렉터리를 훑어 전부 만든 뒤 자른다. 필터와 커서를 포트가 이미 받으므로 색인을 붙일 때 어댑터만 바뀐다(ADR 0012).
