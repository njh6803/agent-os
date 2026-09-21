---
paths:
  - "src/agent_os/sdk/**"
  - "plugins/**"
---

# sdk와 플러그인 규칙

원천은 `src/agent_os/sdk/`의 코드와 `tests/sdk/`다. 아래는 확정된 결정이다. 코드와 이 문서가 다르면 코드를 고치거나 ADR을 남긴다. 이 문서를 코드에 맞춰 조용히 고치지 않는다.

- sdk는 플러그인이 import하는 유일한 표면이다. `langgraph`, `langchain_core`, `langchain_anthropic`, `langchain_mcp_adapters`를 import하지 않는다. import-linter가 판정한다.
- 플러그인 종류는 넷이다. `agent`, `mcp`, `skill`, `model`. 매니페스트는 `plugin.toml` 하나이고 `schema_version`, `kind`, `name`, `version`을 가진다. `agent`만 `entrypoint = "모듈:속성"`과 쓸 MCP 서버 목록 `mcp = [...]`를 가진다. 비어 있으면 도구가 없다(ADR 0002). `mcp`만 `[server]` 표(`command`, `args`)를 가진다. 형식 버전과 주체의 근거는 ADR 0008. 디렉터리와 `kind`가 어긋나면 로더가 에러를 낸다.
- 에이전트는 개발자가 코드로 쓰는 플러그인이다. 그래프가 아니다.
- 모델은 이름을 가진 LLM 설정이다. 첫 슬라이스는 `kind`와 디렉터리만 예약한다.
- 스킬은 절차 지식이다. `SKILL.md`와 부속 파일의 폴더이고 에이전트의 컨텍스트에 주입된다. 함수가 아니다. 툴 경로는 MCP 하나이며 in-process 함수 툴 종류를 두지 않는다.
- 매니페스트와 이벤트 스키마는 디스크에 남는 형식이라 버전을 가진다. 모르는 버전은 거부하고, 모르는 이벤트 type은 읽는 쪽이 원문으로 보존한다. 바꾸면 ADR을 남긴다.
- 에이전트의 `run()`은 재실행 가능해야 한다. 파일, 시각, 난수, 네트워크 같은 부작용은 `ctx`를 통해서만 일으킨다. `ctx`에 `run_id`와 `now()`가 있다.
- `AgentContext`의 `llm()`과 `tool()`은 인자와 반환이 JSON으로 직렬화 가능해야 한다(`sdk.Json`). 파이썬 객체를 넘기지 않는다. `now()`의 `datetime`과 `run_id`는 런타임이 주는 값이라 예외다.
- 진실의 원천은 파일시스템이다(ADR 0003).
- `entrypoint`는 플러그인 디렉터리 기준 파일이며 고유 모듈명 `agent_os_plugins.<name>.<module>`로 로드한다. `sys.path`를 건드리지 않는다.
