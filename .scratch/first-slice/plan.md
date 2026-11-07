# first-slice: CLI로 에이전트 하나를 실행하면 모델을 부르고 도구를 써서 답하며, 실행 전체가 이벤트로 남는다.
**슬라이스:** 1
**Blocked by:** 없음
**끝:** 2026-09-21

CLI로 에이전트 하나 실행. Anthropic 호출, MCP stdio 도구 하나, 이벤트 스트림, JSONL 트레이스. 원칙 I 기한 2026-09-22. 첫 티켓은 계약과 의존성: `pyproject.toml`을 tech.md에 맞추고(지금은 anthropic·mcp·pydantic) sdk에 `schema_version`·`principal`·`mcp`·`model`을 넣는다
