# claude-code-compat: Claude Code용 스킬과 서브에이전트와 MCP 설정을 올리면 우리 플러그인 형식으로 바꿔 설치한다.
**슬라이스:** 12
**Blocked by:** declarative-agent

Claude Code 호환(후보 3). 우리 형식의 마켓플레이스(git 저장소나 폴더)를 관리 화면에서 주소로 등록하고 코드 없는 넷을 골라 설치한다. Claude Code의 것 넷(스킬 zip, 서브에이전트 .md, `.mcp.json` 조각, 플러그인 zip)을 업로드하면 서버가 우리 `plugin.toml`로 바꿔 저장한다. `[server]`의 http 모양은 mcp-http가 먼저 들였다(ADR 0046). 원격 MCP의 나머지(`.mcp.json` 조각의 변환 등)는 이 행에 남는다(ADR 0042 묶음 ③). skill-plugin 명세가 범위 밖에 둔 셋(표준의 이름 규칙 가운데 플러그인 이름 패턴이 보지 않는 끝 하이픈·연속 하이픈, 표준이 허락하는 유니코드 소문자 이름, 설명의 1024자 상한)이 이 행의 업로드에 닿는다. 지금 규칙으로는 한글이나 전각 이름의 스킬 폴더가 들어오지 못한다
