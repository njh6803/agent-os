# mcp-trust: MCP 서버마다 믿는 정도와 도구 정의 해시를 정해, 믿지 않는 서버의 결과를 바깥 글로 다룬다.
**슬라이스:** 10
**Blocked by:** approval-rules, pilot-release

MCP 서버의 신뢰 수준과 도구 정의 해시(후보 7). 운영자의 서버 파일이 서버마다 믿는다·확인한 해시·넘길 환경 변수 이름·주체 전파를 든다. 믿지 않는 서버의 결과는 루프가 바깥 글로 감싸고 `tool_called`에 수준을 적는다. 해시가 다르면 연결 직후 `run_failed` 원인 `tool_connection`. 연결 이벤트가 새 종류로 늘고 관리 API에 해시 승인과 믿기 토글의 PUT이 는다(ADR 0042 묶음 ①). approval-rules 명세(2026-11-05, `.scratch/approval-rules/spec.md`의 Out of Scope)가 넘긴 것: `tool_called`의 서버 칸은 신뢰 수준을 적을 때 함께 정하고, 운영자의 서버 파일의 이름(명세는 `servers.toml`이 자연스럽다고 적었다)은 이 기능이 정한다. ADR 0046이 넘긴 것: 이 행 전에는 런타임이 검색 결과를 바깥 글로 감싸지 않고, doc-qa의 프롬프트가 검색 결과를 데이터로 엮는 것에 기댄다. 신뢰 수준·해시·주체 전파는 stdio와 원격 MCP 서버 두 모양에 똑같이 건다(ADR 0042 "원격 MCP", ADR 0046)
