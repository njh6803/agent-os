# 2026-11-09 (12:29) mcp-http 설계 인터뷰

세션 제목 `docs/mcp-http-design`. 브랜치 `docs/mcp-http-design`, 워크트리 `.claude/worktrees/mcp-http-design`. 모델 Fable 5.1 / xhigh. 주 체크아웃(main `24fdbe9a`)에서 시작해 `EnterWorktree`로 들어왔고, 도구가 만든 브랜치 `worktree-mcp-http-design`을 `git branch -m`으로 지시문의 이름으로 바꿨다. 바꾸는 파일이 모두 커밋 검사의 면제 모양(ADR, 일지, 기능 계획, `.scratch/plan.md`, `CONTEXT.md`, `docs/constitution/tech.md`)이라 티켓 없이 `docs/` 브랜치로 한다(`tools/check_ticket.py`의 면제 목록을 읽었다).

## 사용자 프롬프트

> 사용자: .claude/skills/grill-with-docs/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: mcp-http
>
> 다음 작업: 기능 mcp-http. 원격 MCP 서버에 주소로 접속해, 실행마다 MCP 서버를 새로 띄우는 시작 비용을 없앤다
> 다음 단계: 설계 인터뷰
> 어디서: 새 세션
> 시작 프롬프트: /grill-with-docs mcp-http
> 브랜치: docs/mcp-http-design
> 모델: Fable 5.1 / xhigh
> 읽을 것: .scratch/mcp-http/plan.md(설계 인터뷰가 먼저 볼 것과 수락). 프론티어의 pilot-portal도 공개 데모로 가는 행이라 이 기능과 함께 먼저 하고, local-model은 공개 데모 뒤다(.scratch/plan.md, ADR 0046의 2026-11-06 이력)
> 이어받을 상태: 없음
> 확인할 선행 조건: 없음
> 이번 요청 범위: PR과 병합까지

## 조사(첫 라운드 전)

기능 계획 `.scratch/mcp-http/plan.md`, ADR 0042의 "원격 MCP" 줄과 전제, ADR 0046의 결정과 Consequences, mcp-trust·diag-bundle·doc-qa-agent·public-demo·deploy-package의 기능 계획, `CONTEXT.md`의 원격 MCP 서버 항목을 읽었다. 코드와 라이브러리는 다음을 봤다.

- `sdk/manifest.py`의 `McpServer`는 `command`·`args`·`secret_args` 셋이다. `openapi.json`의 `McpServer` 스키마는 `command`를 필수로 들고, 생성한 TS 타입(`web/packages/api-client/src/generated/openapi.ts`)에 `command: string`이 있다. 관리 화면의 컴포넌트에는 `server.command`를 읽는 자리가 없다. 그러나 `web/apps/admin/components` 아래 테스트 픽스처와 스토리 넷이 `server` 값을 `command`·`args`·`secret_args`로 적는다(grep. 처음에는 없는 경로 `web/apps/admin/src`를 훑어 아무것도 보지 못한 채 "없다"고 적었고, 셀프 리뷰의 표준 축이 잡았다). 코드를 읽었다.
- mcp 2.3.0의 `streamable_http_client(url, *, http_client=None, terminate_on_close=True, max_sse_event_size=1MB)`에는 헤더 인자가 없다. `http_client`가 없으면 `create_mcp_http_client()`가 만든 `httpx2.AsyncClient`를 쓰고 그 기한은 접속·쓰기·풀 30초, 읽기 300초다(`mcp/client/streamable_http.py` 713~760줄, `mcp/shared/_httpx_utils.py` 32~64줄을 읽었다).
- 연결을 닫을 때의 세션 종료 요청(DELETE, `terminate_session`)은 `finally`에서 보내고 취소 보호(`CancelScope(shield=True)`)가 없다. 서버 쪽 세션은 `StreamableHTTPSessionManager`의 `session_idle_timeout` 기본 1800초 뒤 닫힌다(`mcp/client/streamable_http.py` 695~710줄과 790~800줄, `mcp/server/streamable_http_manager.py` 39~111줄을 읽었다).
- httpx2 2.13.0 `AsyncClient`의 `trust_env` 기본값은 True다(`httpx2/_client.py` 192·622줄을 읽었다). 프록시 환경 변수를 따른다는 뜻으로 읽었고(독스트링 "Enables or disables usage of environment variables"), 어느 변수를 어떻게 읽는지는 대 보지 않았다.
- `core/`와 `sdk/`에는 `os.environ`·`getenv`가 없다(grep). 실행 전체 기한의 기본은 600초다(`core/run.py`의 `DEFAULT_RUN_TIMEOUT_SECONDS`).
- mcp 2.3.0의 `MCPServer.run(transport="streamable-http", host, port, streamable_http_path="/mcp", json_response, stateless_http)`가 있어 시험용 서버를 HTTP로 띄울 수 있다(`mcp/server/mcpserver/server.py` 387~395줄과 1113~1134줄을 읽었다). 지금 테스트는 같은 클래스로 stdio 픽스처(`tests/adapters/mcp_fixture_server.py`)를 띄운다.
- 닫힌 포트(루프백에서 바인드했다 놓은 포트)에 `streamable_http_client`로 붙으니 이 PC(윈도우)에서 2.175초 뒤 `ConnectError: All connection attempts failed`(예외 그룹 안)로 끝났다. 세션 스크래치패드의 스크립트 `probe_refused.py`로 한 번 손으로 봤다. 리눅스에서는 재지 않았고, 저장소의 프로브로는 아직 옮기지 않았다.

질문에 처음 나오는 개념 셋(원격 MCP 서버와 streamable HTTP, 매니페스트의 `[server]` 표, 실패 원인 `tool_connection`)은 첫 라운드 호출 곁 본문에서 무엇인가·잡아 주는 것·치르는 값으로 풀었다.

## 라운드 1

첫 호출은 사실 확인 훅(`hook_choice_facts`)에 한 번 막혔다. "꺼진 서버는 연결 거부라 바로 끝나는 것이 보통(재지 않았다)"이라 적었던 설명을 위의 손으로 본 2.2초로 고쳐 다시 올렸다. 넷 모두 추천안을 골랐다.

> 사용자: (원격 MCP 서버의 주소(url)는 어디에 적을까요?) "매니페스트에 그대로 적는다 (Recommended)" — 설명: 플러그인의 plugin.toml에 `[server] url = "http://rag-engine:8000/mcp"`처럼 주소를 글자 그대로 적습니다. 플러그인 폴더는 배포의 몫이라(ADR 0042 전제 "플러그인 디렉터리와 운영자 파일은 배포의 몫") 배포마다 그 파일을 둡니다. compose에서는 서비스 이름이 곧 주소라 공개 데모와 참조 배포가 같은 주소를 씁니다. 주소는 비밀이 아닌 것으로 보아 관리 API의 매니페스트 응답과 실패 문구에 그대로 실리고, 그래서 `사용자:비밀번호@`가 든 주소는 매니페스트를 읽는 단계에서 거부합니다. 치르는 값: 로컬 개발처럼 주소가 다른 자리에서는 매니페스트를 고쳐야 합니다.

고르지 않은 선택지(라벨만): "환경 변수 이름을 적는다", "운영자의 서버 파일에 적는다".

> 사용자: (`[server]` 표에서 stdio 모양과 http 모양을 어떻게 가를까요?) "transport 칸으로 가른다 (Recommended)" — 설명: `transport = "http"`면 `url`·`headers`를, `"stdio"`이거나 칸이 없으면 지금처럼 `command`·`args`를 받습니다. 지금 있는 매니페스트는 고치지 않아도 됩니다. 계약(openapi.json)에는 두 모양이 따로 서고(oneOf) 생성한 TS 타입도 둘로 갈립니다. Claude Code의 `.mcp.json`도 `type` 칸으로 가릅니다(ADR 0042 "원격 MCP" 줄의 "type http 항목"). 엉뚱한 칸(http에 `command`)은 그 모양의 모르는 칸으로 거부됩니다. 치르는 값: 칸이 하나 늘어납니다.

고르지 않은 선택지(라벨만): "칸 유무로 가른다", "한 모양에 선택 칸을 더한다".

> 사용자: (원격 MCP 서버가 꺼져 있을 때, 그 서버를 쓰는 실행은 어떻게 끝날까요?) "지금처럼 바로 실패로 끝낸다 (Recommended)" — 설명: 실행이 `run_failed` 원인 `tool_connection`으로 끝나고 문구는 `MCP 서버 <이름>(<주소>)에 붙지 못했다: <원인>`입니다. 재시도는 하지 않습니다. 기한은 mcp의 기본값(접속 30초, 읽기 300초. `mcp/shared/_httpx_utils.py`를 읽었습니다)을 그대로 쓰고 실행 전체 기한(기본 600초, `core/run.py`)이 그 위에 있습니다. 꺼진 서버(닫힌 포트)에 붙으면 이 PC(윈도우)에서 2.2초 뒤 연결 거부로 끝났고(스크래치 스크립트로 한 번 쟀습니다. 리눅스에서는 재지 않았습니다), 패킷을 버리는 방화벽 뒤의 주소만 접속 기한 30초를 다 기다립니다(어림). 위젯에는 지금의 실패 항목이 그대로 보입니다.

고르지 않은 선택지(라벨만): "짧게 재시도한 뒤 실패한다", "접속 기한을 매니페스트 칸으로 둔다".

> 사용자: (서버가 꺼진 것을 실행 전에 미리 알 수 있는 길을 이 기능에서 줄까요?) "이 기능에서는 두지 않는다 (Recommended)" — 설명: 서버가 꺼진 것은 실행의 실패로만 드러납니다. 뒤의 diag-bundle이 접속 확인을 더할 때 어댑터의 서버 하나를 여는 함수를 다시 쓸 수 있도록 그 함수의 경계만 지킵니다. 이 기능의 범위가 늘지 않습니다.

고르지 않은 선택지(라벨만): "CLI 명령을 지금 더한다", "/health가 서버들을 함께 본다".

### 둘째 호출(같은 라운드의 나머지 넷)

첫 호출의 답에 기대지 않는 결정이라 같은 라운드다. 사실 확인 훅에 한 번 막혔고, 설명의 사실(1800초, 취소 보호 없음, 실행 전 거부의 500, ADR 0034의 닫기 보호)은 이미 대 본 것이라 같은 화면을 그대로 다시 올렸다. "취소와 닫기"만 추천과 다른 답이다.

> 사용자: (헤더 값을 담은 환경 변수가 serve의 환경에 없으면 어떻게 할까요?) "접속 단계의 실패로 끝낸다 (Recommended)" — 설명: 그 서버에 붙는 자리에서 어댑터가 환경을 읽고, 변수가 없으면 붙지 않고 `ConnectionError`로 끝내 실행은 `run_failed` 원인 `tool_connection`이 됩니다. 문구는 변수의 이름만 들고 값은 싣지 않습니다. 환경을 읽는 코드는 어댑터에만 둡니다(adapters 규칙: 바깥에 닿는 코드는 어댑터에만 산다. core와 sdk에는 환경을 읽는 코드가 없습니다, grep). 치르는 값: 실행 식별자가 생긴 뒤에 드러나 트레이스에 실패 하나가 남습니다.

고르지 않은 선택지(라벨만): "실행 전에 거부한다".

> 사용자: (실행이 취소되어(기한, serve 종료) 연결을 닫을 때, 서버 세션 종료 요청(DELETE)이 끝까지 가지 않아도 될까요?) "닫기를 취소에서 보호한다" — 설명: 어댑터가 닫기를 `CancelScope(shield=True)`와 짧은 기한(예: 2초)으로 감싸 DELETE까지 보냅니다. stdio 클라이언트가 서버 닫기를 보호하는 것(ADR 0034)과 같은 모양입니다. 치르는 값: 취소된 실행의 끝이 그만큼 늦고, 보호 코드와 그 테스트(취소된 실행에서 DELETE가 서버에 닿았는지)가 늘어납니다.

고르지 않은 선택지(추천이었다. 라벨과 설명): "받아들인다 (Recommended)" — 설명: mcp의 HTTP 클라이언트는 닫을 때 세션 종료 요청(DELETE)을 보내지만 취소 보호가 없어(`mcp/client/streamable_http.py`를 읽었습니다) 취소된 실행에서는 그 요청이 가지 않을 수 있습니다. 서버 쪽 세션은 mcp 서버 구현의 기본 유휴 기한 1800초 뒤 스스로 닫힙니다(`mcp/server/streamable_http_manager.py`를 읽었습니다). stdio와 달리 남는 것은 프로세스가 아니라 서버 안의 세션 하나입니다. 치르는 값: 취소가 잦으면 서버에 세션이 최대 30분 쌓입니다. 문서 검색 서버가 어떤 구현인지는 그 저장소가 정합니다.

> 사용자: (헤더 칸의 모양과 환경 변수 값의 뜻은 어떻게 할까요?) "헤더 이름→변수 이름 표, 값은 헤더 값 전체 (Recommended)" — 설명: `[server.headers]` 표에 `Authorization = "RAG_ENGINE_AUTH"`처럼 헤더 이름마다 환경 변수 이름을 적고, 환경 변수에는 `Bearer abc…`처럼 헤더에 그대로 실을 값 전부를 둡니다. 어댑터는 값을 바꾸지 않고 그대로 싣습니다. 토큰 헤더든 API 키 헤더든 같은 길입니다. 치르는 값: 운영자가 `Bearer ` 접두까지 환경 변수 값에 직접 적어야 합니다.

고르지 않은 선택지(라벨만): "bearer 토큰 전용 칸 하나", "표와 전용 칸 둘 다".

> 사용자: (serve의 프록시 환경 변수(HTTP_PROXY 등)를 원격 MCP 서버 접속에도 따를까요?) "따른다(httpx2 기본) (Recommended)" — 설명: httpx2 `AsyncClient`의 `trust_env` 기본값 True를 그대로 둡니다(`httpx2/_client.py`를 읽었습니다. 어느 변수를 어떻게 읽는지는 대 보지 않았습니다). 프록시 뒤의 배포에서 바깥 주소의 서버에 붙을 수 있고, 내부 주소(compose 서비스 이름)는 `NO_PROXY`에 적어야 합니다. 그 줄은 배포 안내(deploy-package)에 넘깁니다. 치르는 값: `NO_PROXY`를 빠뜨리면 내부 서버 요청이 프록시로 가서 접속 실패로 보입니다.

고르지 않은 선택지(라벨만): "따르지 않는다".

## 합의 요약(사용자가 확인했다)

두 라운드 뒤 남은 가지가 없었다. 답에서 따라오는 세부(기한 값, 주소 검증, 모델 이름, 문구, 시험 방법)는 요약에 적어 함께 확인받았다. 이 설계는 스킬·훅·브랜치 규약 같은 절차를 바꾸지 않아 절차의 중간 갈래를 밟을 것이 없다(grilling의 갈래 밟기 문단). 올린 요약은 다음 여덟이다.

1. **매니페스트.** `[server]`에 `transport` 칸이 생긴다. 칸이 없거나 `"stdio"`면 지금처럼 `command`·`args`를 받고, `"http"`면 `url`과 선택 표 `[server.headers]`(헤더 이름 → 환경 변수 이름)를 받는다. `url`은 `http`·`https`만 받고 `사용자:비밀번호@`가 들면 읽는 단계에서 거부한다. 환경 변수 이름은 글자·숫자·밑줄 꼴만 받는다. `secret_args`는 두 모양이 같이 쓴다. sdk에는 모양마다 모델이 하나씩 서고(`StdioServer`, `HttpServer`) `transport`로 가르는 합이 `McpServer`가 되어, `openapi.json`에는 oneOf로 실리고 TS 타입을 다시 생성한다. 지금 있는 매니페스트는 고치지 않는다. 계약 변경이라 첫 티켓이고 다른 티켓을 막는다.
2. **접속.** 실행마다 어댑터가 접속 직전에 헤더의 환경 변수를 읽어 `httpx2.AsyncClient`(기한은 mcp 기본값, 프록시 환경 변수 따름)를 만들고 mcp의 streamable HTTP 클라이언트로 붙어 세션을 열고 도구 목록을 읽는다. 그 뒤의 호출은 stdio와 같은 `McpConnection`이고, 도구마다 `ToolSpec.server`에 플러그인 이름이 실린다.
3. **실패.** 서버 꺼짐, 틀린 주소, 헤더 변수 없음, 인증 거부는 모두 여는 단계의 `ConnectionError`이고 실행은 `run_failed` 원인 `tool_connection`으로 끝난다. 문구는 `MCP 서버 <이름>(<주소>)에 붙지 못했다: <원인>`이고, 변수가 없을 때의 원인은 `헤더 <헤더 이름>의 환경 변수 <변수 이름>이 없다`다. 헤더 값은 어디에도 싣지 않는다. 재시도와 미리 확인은 없다.
4. **닫기.** 연결을 닫을 때 세션 종료 요청(DELETE)과 클라이언트 닫기를 `CancelScope(shield=True)`와 기한 2초(stdio 상류가 서버 종료를 기다리는 유예와 같은 값)로 감싸 취소된 실행에서도 보내고, 2초를 넘기면 그만둔다. 런처와 프로세스 정리는 http에 걸리지 않는다.
5. **의존.** `httpx2`를 런타임 직접 의존으로 선언하고 major 2로 묶는다(잠금의 2.13.0 그대로). `docs/constitution/tech.md`의 표에 적는다.
6. **시험.** 테스트 픽스처로 같은 `MCPServer`를 streamable HTTP로 루프백의 빈 포트에 띄운다. 사례는 도구 목록·호출·`ToolSpec.server`, 변수 없음, 꺼진 서버가 `tool_connection`으로 끝남(수락), 취소된 실행에서 DELETE가 서버에 닿음, calc 예시가 http 모양의 플러그인으로 도구를 써 트레이스가 남음(수락)이다. `plugins/mcp/`에 http 예시는 두지 않고 doc-qa-agent가 실제 플러그인을 가져온다.
7. **범위 밖.** 접속 미리 확인(diag-bundle), 운영자의 서버 파일과 신뢰 수준·해시(mcp-trust), SSE 전송, OAuth, 재시도, 접속 기한 칸.
8. **문서.** ADR 0049 초안(의존성 추가 포함), 용어는 `domain-modeling`이 정하고(`전송` 후보), 기능 계획에 `**설계:** ADR 0049`, `.scratch/plan.md` 재생성. ADR 0042의 "원격 MCP" 줄(url·헤더의 환경 변수 이름)은 그대로 참이라 포인터를 달지 않는다.

> 사용자: (위 합의 요약 여덟 항목대로 mcp-http의 설계를 확정해도 될까요?) "이대로 확정한다 (Recommended)" — 설명: 요약 여덟을 그대로 설계로 삼습니다. 다음으로 domain-modeling이 용어를 맞추고 ADR 0049 초안을 써서 셀프 리뷰 뒤에 승인을 묻습니다. 기능 계획의 설계 줄은 ADR이 승인된 뒤에 적습니다.

고르지 않은 선택지(라벨만): "고칠 것이 있다".

## domain-modeling

용어를 맞추고 ADR 초안을 썼다. 승인 전이라 상태는 proposed다.

- `CONTEXT.md`: **MCP 서버** 정의를 플러그인이 띄우는 프로세스만이 아니라 전송에 따라 플러그인이 띄운 프로세스이거나 주소로 붙는 원격 MCP 서버로 고쳤고, **전송(Transport)** 항목을 새로 넣었다(stdio와 streamable HTTP 둘, 매니페스트가 서버마다 하나를 고른다. 피할 말은 프로토콜·연결 방식·모드). **원격 MCP 서버** 항목은 그대로다.
- ADR 초안 `docs/adr/0049-mcp-server-has-a-transport-field-and-remote-servers-connect-per-run-by-manifest-url.md`. 제목은 결정 문장이고 본문은 합의 요약 여덟을 결정·Considered Options·Consequences로 옮겼다. 거부한 안 열하나에는 요약에 없던 근거를 적었고, 사용자가 추천과 다르게 고른 닫기 보호는 추천이었던 "받아들인다"를 거부한 안으로 적고 이 일지의 둘째 호출을 가리켰다. 2.2초는 저장소 프로브가 아니라 손으로 봤다로만 적었다.
- 초안을 쓰며 대 본 것. ADR이 이름으로 든 자리(import-linter의 금지 목록 둘, `pyproject.toml`의 `[dependency-groups]` 주석, `.claude/rules/core.md` 포트 표의 `ToolSource` 행과 실패 정책, `.claude/rules/adapters.md`의 MCP 항목 셋)는 적은 모양 그대로였다. 처음 적은 "`adapters.md`의 첫 항목"은 틀려(환경 이야기는 둘째 항목 "파일, DB, 외부 서비스, 시계에 닿는 코드는 여기에만 산다"다) 그 문장을 인용하는 것으로 고쳤다.
- 닫기 보호의 자리. mcp 2.3.0의 `streamable_http_client`는 종료 요청을 자기 문맥의 `finally`에서 보내고(789~791줄), 어댑터가 넘긴 클라이언트는 닫지 않으며(`client_provided`, 746~761줄), 세션 식별자를 yield하지 않는다(788줄. 코드를 읽었다). 그래서 어댑터의 보호는 라이브러리 바깥에서 그 문맥을 닫는 호출을 감싸는 모양이 되는데, ADR 0034가 stdio에서 같은 모양을 재 보고 거부했다(안쪽 task group이 취소를 삼켰다). http 클라이언트에도 걸리는지는 재지 않았고 ADR에 어림으로 적어 명세의 프로브가 먼저 재게 했다. 서지 않을 때의 길(`terminate_on_close=False`와 응답 헤더 `Mcp-Session-Id`로 어댑터가 직접 보내기)도 어림으로 적었다. 결정(취소된 실행에서도 2초 안에 종료 요청을 보낸다)은 바뀌지 않아 사용자에게 다시 묻지 않았다.
- 포인터(`.claude/rules/adr.md`). `stdio|\[server\]|McpServer|command|서버를 띄|프로세스를 띄`로 `docs/adr/`를 grep해 나온 본문을 봤다. ADR 0034의 두 문장(결정의 "닫기는 상류의 보호된 절차를 그대로 받아 …", Consequences의 "서버마다 `stdio_client`와 `ClientSession`을 열고 …")은 http 전송이 더해지면 stdio에만 참이라 `(바뀜: ADR 0049)`를 달았다. 달지 않은 것: ADR 0034가 거부한 안 "어댑터가 라이브러리 바깥에서 닫기를 보호한다"(거부한 안의 근거), ADR 0012의 "`ToolSource.connect`가 stdio 프로세스를 띄워야 나오는데"(결정의 그때 근거이고 결정은 같은 방향), ADR 0042의 "원격 MCP" 줄(글자 그대로 참)과 업로드 변환 줄(`headers`의 `${VAR}`를 서버 파일에 적는다. claude-code-compat 인터뷰의 접점), ADR 0046 18행(stdio 서버는 그때마다 새 프로세스로 뜬다. 여전히 참), ADR 0009의 2026-09-22 이력 문장(지난 이력의 기록), ADR 0007 20행(stdio 클라이언트가 anyio 태스크 그룹이라는 사실. 더해질 뿐이다).
- `docs/adr/README.md`에 색인 행(proposed, 2026-11-09)을 더했고, `docs/constitution/tech.md` 런타임 의존성 행의 `mcp` 문장 뒤에 `httpx2` 문장을 더했다. 선언은 mcp-http의 첫 티켓이 한다.

## 셀프 리뷰(code-review)

범위: 기준 `24fdbe9a`(origin/main과 같다), 커밋 0, 수정 넷(`CONTEXT.md`, ADR 0034, `docs/adr/README.md`, `docs/constitution/tech.md`), 미추적 둘(ADR 0049, 이 일지). 표준 축은 sonnet·high, 명세 축은 이 세션의 모델. 명세는 이 일지의 사용자 인용·합의 요약과 grill-with-docs·domain-modeling·`adr.md`의 절차를 요구로, 이 세션이 한 일을 참고로 가른 브리프다.

표준 축(Major 1, Minor 3, Nit 1). (1) Major: "관리 화면 코드는 `server.command`를 쓰는 자리가 없어 화면은 바뀌지 않고 생성물 최신성 검사만 요구"가 반례를 만난다. 생성 타입은 기본값 있는 칸(`args`)도 필수로 내므로 `transport`도 필수가 되고, `server` 값을 적은 테스트 픽스처와 스토리 넷이 바뀐다. (2) Minor: ADR 0008의 이력 날짜가 09-22가 아니라 09-21이다. (3) Minor: 일지의 grep 경로 `web/apps/admin/src`가 없다. (4) Minor: 닫기 항목이 ADR 0034의 실패 양상(호출자에게 취소가 전해지지 않음)을 적지 않았다. (5) Nit: 스택 표 열거에 `httpx2`가 없고, `pyproject.toml` `[project]` 주석과 `README.md` 111행도 고칠 자리에 없다. 대 보고 맞은 것: mcp·httpx2의 줄 번호와 동작 전부, 락, core·sdk의 환경 읽기 없음, 인용 전부, 어림 표시, 포인터 둘과 달지 않은 다섯, `check_adr_pointers.py` 0건, `CONTEXT.md` 잔존 없음.

명세 축(Minor 3, Nit 5, 범위 넘침 0). (a) 빠진 것: 둘째 호출 첫 질문의 치르는 값 "실행 식별자가 생긴 뒤에 드러나 트레이스에 실패 하나가 남습니다"(Minor), 첫 호출 셋째 질문의 "위젯에는 지금의 실패 항목이 그대로 보입니다"(Minor), 둘째 질문의 `.mcp.json` `type` 선례(Nit), `NO_PROXY` 동작의 근거 표시(Nit). (b) 범위 넘침 없음. 합의 요약 여덟의 조건 전부가 본문에 있고 ADR이 더한 것은 기존 기준에서 따라 나오는 결과·한계다. 절차도 맞다(설계 줄 없음, `.scratch/plan.md` 미변경, proposed). (c) 관리 앱 픽스처(표준 축 1과 같다, Minor), 리다이렉트 규칙의 "기본 포트일 때" 누락(Nit), "695~800줄"인데 파일은 794줄(Nit), 이 일지 둘째 호출의 괄호 "(라벨만, 추천이었다)"(Nit).

고친 것(새로 쓴 사실 문장은 PR 직전 리뷰의 밀 주장이다).
- ADR 0049 Consequences 첫 티켓: "관리 화면의 컴포넌트는 `server.command`를 읽지 않아(`web/apps/admin`을 grep했다) 화면은 바뀌지 않는다. 그러나 생성 타입은 기본값이 있는 칸도 필수로 내므로(`args`가 `@default []`인데 `args: string[]`이다. `sdk/manifest.py`의 매니페스트 공통 설정 `_MANIFEST_CONFIG`가 켠 `json_schema_serialization_defaults_required`, ADR 0010) `transport`도 필수가 되고, `server` 값을 생성 타입으로 적은 테스트 픽스처와 스토리 넷(`components/pages/HomePage.test.tsx`, `components/pages/RunPage.decision.test.tsx`, `components/organisms/RunDetail.stories.tsx`, `components/organisms/PluginDetail.stories.tsx`)이 `transport`를 더해야 한다(코드를 읽었다. `tsc`는 돌리지 않았다). `[server]`에 `command`가 없는 매니페스트의 거부 문구를 든 스토리(`components/organisms/PluginList.stories.tsx`)는 문구가 바뀌면 함께 고친다. e2e가 쓰는 stdio 매니페스트(`e2e/stack.ts`)는 `transport`가 없어도 stdio라 그대로다." 근거: `web/apps/admin`의 grep, `web/packages/api-client/src/generated/openapi.ts` 528~543행, `sdk/manifest.py` 45~49행.
- ADR 0049 매니페스트: ADR 0008 이력 날짜를 2026-09-21로 고쳤다. "Claude Code의 `.mcp.json`도 `type` 칸으로 전송을 가르는 선례다(ADR 0042 "원격 MCP" 줄의 `type http` 항목)."
- ADR 0049 닫기: "프로브는 종료 요청이 서버에 닿았는지만이 아니라 기한이 걸린 실행이 지금처럼 시간 초과의 `run_failed`로 끝나는지도 본다. ADR 0034에서 서지 않았던 양상은 가려진 취소를 안쪽 task group이 삼켜 호출자에게 취소가 전해지지 않은 것이고, 지금 core는 범위가 취소를 받았는지(`cancelled_caught`)로 기한을 보므로 그것이 거짓이 되면 결말이 바뀐다(`.claude/rules/core.md`의 실행 타임아웃 항목)." 근거: ADR 0034 14행, `core.md`의 실행 타임아웃 항목.
- ADR 0049 실패: "변수 없음은 실행 식별자가 생긴 뒤에 드러나 트레이스에 실패 하나가 남는다. 실행 전 거부를 두지 않은 대가다."
- ADR 0049 바꾸지 않는 것: "최종 사용자 경로와 위젯에는 지금의 실패 항목이 그대로 보인다."
- ADR 0049 배포 셋: "httpx2는 `trust_env`가 참이면 urllib의 `getproxies()`로 프록시 환경 변수를 읽고 `no_proxy`의 항목을 프록시를 거치지 않는 주소로 옮긴다. `httpx2/_utils.py` 30~76줄을 읽었다." 리다이렉트 문장에 "기본 포트를 쓰는"을 더했고, 머리의 줄 범위를 695~794로 고쳤다. 이 반영으로 위 조사 절의 "어느 변수를 어떻게 읽는지는 대 보지 않았다"는 닫혔다.
- ADR 0049 고칠 자리: `pyproject.toml`의 `[project]` 머리 주석을 더했고, tech.md 문장 뒤에 "(헌법 판 3.0.73, 스택 표의 문구 하나)"를 더했다.
- 이 일지: 조사 절의 경로 문장을 바로잡았고(원문은 `web/apps/admin/src`에 `command`가 없다였다), 둘째 호출의 괄호를 "(추천이었다. 라벨과 설명)"으로 고쳤다.

남긴 것과 이유. 스택 표 열거에 `httpx2`를 더하지 않는다(Nit. `pyjwt`·`anyio`처럼 열거 뒤의 문장으로 선언 사실을 적는 선례를 따른다). `README.md` 111행의 런처 문장은 stdio에만 걸리는 말이고 거짓이 아니라 그대로 둔다(Nit).

다시 돌린 명령. 문서만 바뀌어 린트·타입체크·경계·web은 바뀐 파일이 없다. 손으로 치는 다섯은 커밋의 pre-commit 결과로 갈음한다(결과는 커밋 뒤에 적는다). `uv run python tools/sibling_overlap.py`는 리뷰 중에 한 번 쳤다. ADR 0049는 번호 겹침이 없었고, `docs/constitution/tech.md`를 고쳤는데 헌법 판을 올리지 않았다는 1로 끝나 `docs/constitution/README.md`의 판을 3.0.72에서 3.0.73(스택 표의 문구 하나, patch. 선례는 3.0.66·3.0.10)으로 올리고 Last Amended를 2026-11-09로 했다. 함께 고친 파일 후보로 워크트리 `mcp-shutdown-spec`의 커밋하지 않은 ADR 0034 변경이 나왔다(종료 코드와 무관. 그 워크트리의 PR은 닫혔다).

## 승인

셀프 리뷰를 반영한 뒤 ADR 0049의 승인을 물었다.

> 사용자: (ADR 0049 초안을 이대로 승인할까요?) "승인한다 (Recommended)" — 설명: ADR 0049의 status와 색인 행을 accepted로 바꿉니다. 기능 계획 .scratch/mcp-http/plan.md에 설계 줄(**설계:** ADR 0049)을 적고 .scratch/plan.md를 재생성합니다. 그다음 커밋, PR 직전 리뷰, PR, 병합까지 묻지 않고 진행하고, 끝나면 다음 작업 지시문(명세 쓰기 /to-spec, 새 세션)을 내고 그 세션을 엽니다.

고르지 않은 선택지(라벨만): "고칠 것이 있다".

ADR 0049의 status와 색인 행을 accepted로 바꾸고, 기능 계획 `.scratch/mcp-http/plan.md`에 `**설계:** ADR 0049`를 `**Blocked by:**` 뒤에 적고 `uv run python tools/plan_table.py`로 `.scratch/plan.md`를 재생성했다.

## 인계

커밋 `02baaf75`의 pre-commit: ruff 둘은 `.py`가 없어 Skipped라 손으로 쳐 둘 다 초록이었고(`All checks passed!`, `1955 files already formatted`), 카나리아 명세 검사는 대상 없음 Skipped, 나머지는 전부 Passed(pytest 379.8초, web-verify 497.6초). 그 커밋 뒤에 인계 계기(`hook_handoff`, 컨텍스트 325,481 토큰, 경계 `커밋 뒤`)가 왔다. `handoff.md`의 인계하지 않는 때 다섯에 들지 않아 인계한다. 커밋은 성공했고, 범위는 PR과 병합까지라 이 경계에서 끝나지 않으며, 이어받은 인계가 아니고, 인계 못함 줄이 없고, `get_session self`에 `parentSessionId`가 없다. 이 브랜치에 열린 PR은 없다(`gh pr view`). 이 절부터는 커밋하지 않았고 새 세션이 이어 쓰고 커밋한다. 지시문은 다음이다.

```
다음 작업: 기능 mcp-http. 원격 MCP 서버에 주소로 접속해, 실행마다 MCP 서버를 새로 띄우는 시작 비용을 없앤다
다음 단계: 설계 인터뷰
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /grill-with-docs mcp-http
브랜치: docs/mcp-http-design
모델: Fable 5.1 / xhigh. 2의 잇는 지시문
읽을 것: docs/journal/2026-11-09-1229-mcp-http-design.md(인터뷰의 사용자 인용, 합의 요약, 셀프 리뷰 두 축의 보고와 반영, 승인, 이 지시문. "다음" 절은 아직 없다)
이어받을 상태: 인계: 커밋 뒤. docs/journal/2026-11-09-1229-mcp-http-design.md. 설계 인터뷰를 마치고 ADR 0049, CONTEXT.md의 전송 항목, tech.md의 httpx2 문장과 헌법 판 3.0.73, ADR 0034의 포인터 둘, 기능 계획의 설계 줄과 .scratch/plan.md 재생성, 일지를 한 커밋으로 이 브랜치에 두었다. 일지의 인계 절은 그 뒤에 적어 커밋하지 않았다. 남은 단계: PR 직전 리뷰(Skill 도구로 coderabbit-review, 안 되면 /security-review와 bug-perf-review. 밀 주장은 일지 셀프 리뷰 절의 "고친 것" 문장들), PR(/git-pr), 병합(이 워크트리 사본의 next-session merge.md "워크트리에서 병합할 때"를 Read로 열어 따른다), 그 뒤 next-session 지시문(설계 줄이 있고 spec.md가 없으니 결정표대로 /to-spec, 새 세션)과 open-session. 일지의 "다음" 절과 retro는 단계를 닫는 그 세션이 쓴다.
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```

세션 제목을 `docs/mcp-http-design (인계함)`으로 바꿨고, 멈출 백그라운드 작업은 없었으며, 워크트리 잠금을 풀었다. open-session을 부른다 2026-11-09T04:44:31Z

열기는 멈췄다. `tools/open_session.ps1 -Action send`의 출력은 `idle=0s`, `lock=13:48:00.945 waited=0s`, `start=.claude/skills/grill-with-docs/SKILL.md`, `stale=1`, `fired=13:48:02.840`이고, `page=` 없이 "30초 안에 프롬프트 첫 줄이 채워진 새 세션 화면을 찾지 못했다"로 끝났다(종료 코드 1). `fired=` 뒤의 멈춤이라 같은 파일로 다시 돌리지 않았다(세션이 둘 생긴다, open-session "막히면"). `deeplink_timeline.ps1`은 10-27 02:14 뒤의 딥링크를 보이지 않았고, `deeplink_overlap.py`는 이 계정의 열기 셋이 1분 40초 안에 있었다고 냈다. 13:46:57.230 다른 세션의 열기(입력창-없음), 13:48:02.840 이 열기(화면-없음), 13:48:37.353 다른 세션의 열기(보냄. 그 뒤 `list_sessions`에 `docs/pilot-portal-design`이 실행 중으로 새로 보였다). 셋 다 "자기 딥링크를 로그에서 찾지 못했다"라 앱 로그로는 겹침을 가르지 못했다(10-27 02:23 뒤의 열기가 모두 그렇다). `stale=1`은 앞 열기가 남긴 새 세션 화면의 첫 줄로 보인다(같은 스킬 grill-with-docs라 비교하는 앞 24자가 같다). 그 화면이 남은 채 온 이 딥링크가 새 화면으로 보이지 않았다고 어림한다. 잠금은 순서를 지켰다(다음 열기는 이 스크립트가 멈춘 뒤 약 4초에 쏘았다). 이 세션의 `get_window_layout`은 메인 창의 첫 패널이 세션이 아닌 `page`였다고 보였다. 그 화면에 이 지시문이 남아 있는지는 보지 못했다. 인계 못함 커밋 뒤. handoff.md 4의 열기 항목대로 제목을 `docs/mcp-http-design`으로 되돌렸고, 멈춘 대기는 없었으며, 이 세션에서 PR 직전 리뷰부터 잇는다.

## PR 직전 리뷰(coderabbit-review)

범위: 기준 `origin/main`(분기 뒤 움직이지 않았다), 커밋 하나(`02baaf75`)와 미커밋 일지. `coderabbit-review` 서브에이전트가 CLI 0.7.5로 `coderabbit review --agent --include-untracked`를 돌렸다. `auth status`는 `Seat: not assigned`(Plan: Free)였으나 리뷰는 `review_completed`, findings 4로 끝까지 돌아 CLI 축이다. 본 파일은 여덟(기능 계획, `CONTEXT.md`, ADR 0034·0049, ADR 색인, 헌법 README·tech.md, 일지)이고 생성 파일 `.scratch/plan.md`는 목록에 없었다.

보고(서브에이전트의 트리아지).
- 유효 [Minor] ADR 0049 결정의 매니페스트 항목(CLI는 Major, "https 강제, 로컬 개발만 http 예외"): http 주소로는 헤더 값이 평문으로 가는데 ADR이 그 사실도 https 강제를 거부한 근거도 적지 않았다. 서브에이전트는 CLI의 제안(루프백만 http 허용)을 그대로 받으면 compose 서비스 이름 주소로 붙는 이 기능의 첫 배포가 깨진다고 보고, 거부 안과 배포 경고를 더하자고 했다.
- 유효 [Minor] ADR 0049 Consequences(CLI는 Critical): mcp의 streamable HTTP 클라이언트가 DEBUG에서 보낸 메시지 전체를 로그에 싣고(`streamable_http.py` 635·191줄) 그 메시지에 `secret_args` 값이 든다. 이 저장소는 로깅을 설정하지 않아 기본에서는 나오지 않는 조건부 위험이라 Minor로 봤다.
- 오탐 ADR 0049 문구 항목(CLI Critical, 쿼리 문자열의 비밀이 `run_failed`와 관리 API에 노출): ADR이 알려진 한계로 이미 적었고, 주소를 비밀이 아닌 것으로 보는 결정은 인터뷰에서 확인했다(위 라운드 1의 주소 질문 인용). 최종 사용자 경로의 실패 항목은 고정 문구와 `cause`만 싣는다(`channel/http/items.py`, ADR 0023).
- 오탐 ADR 0034 10행(CLI Minor, 런처 도입 이유를 이력으로 옮기라): 이번 변경은 포인터 둘뿐이고 지적한 문장은 원래 있던 글이다(`.claude/rules/adr.md` "본문의 다른 글자는 고치지 않는다").
- CLI 밖 관찰(보류): ADR 0009의 2026-09-22 이력이 "다시 볼 때"의 둘째로 적은 날(매니페스트에 환경변수 필드가 생기는 날)이 ADR 0049인데, ADR 0009에 그 계기가 닿았다는 기록이 없다.

근거를 대 봤다. `streamable_http.py` 47줄 `logger = logging.getLogger(__name__)`, 172줄 `logger.info(f"Received session ID: …")`, 191줄 `logger.debug(f"SSE message: {message}")`, 635줄 `logger.debug(f"Sending client message: {message}")`, 756줄 접속 주소 로그를 Read로 봤고, `mcp/client/`를 `logger.`로 grep해 `stdio/`에는 로그 호출이 없음을 봤다. `src/agent_os`에 `logging.`·`getLogger`·`basicConfig`·`setLevel`이 없고(Grep), `secret_args`를 가리는 자리는 `core/run.py`의 이벤트뿐이다(Grep). `http://rag-engine:8000/mcp`는 이 일지 38행의 인용에만 있고 ADR 0046·0048에는 compose 참조 배포와 저장소 이름 rag-engine만 있어, 서브에이전트가 적은 출처(ADR 0046·0048)를 그대로 옮기지 않고 일지와 두 ADR의 몫을 갈라 적었다.

고친 것(새로 쓴 사실 문장은 PR 봇 회차의 밀 주장이다). 넷 다 결정을 바꾸지 않고 사실과 거부 안을 더한 것이라 승인을 다시 묻지 않았다.
- ADR 0049 Considered Options에 거부 안을 더했다: "**https를 강제한다(루프백 주소만 http 예외).** http 주소로는 헤더 값(토큰)이 평문으로 간다. 그러나 이 기능의 첫 쓰임이 참조 배포의 compose 네트워크 안에서 문서 검색 서버에 서비스 이름으로 붙는 주소(…)라 루프백만 예외로 두면 그 배포가 깨지고, 내부 네트워크마다 인증서를 두어야 한다. 거부했다."
- ADR 0049 Consequences "배포가 알아야 할 것 셋"을 넷으로 바꾸고 첫 항목을 더했다: "http 주소에서는 헤더 값(토큰)이 평문으로 가므로, http 주소는 신뢰하는 내부 네트워크(compose 네트워크의 서비스 이름 주소)에서만 쓰고 인터넷을 지나는 주소는 https로 적는다." 넘기는 곳도 "앞의 둘은 deploy-package의 배포 안내에"로 고쳤다.
- ADR 0049 Consequences에 "**로그.**" 항목을 더했다: 로거 이름 `mcp.client.streamable_http`와 세 줄(172·191·635), stdio 클라이언트에는 메시지를 찍는 로그가 없음, `secret_args`의 실제 값이 호출 본문에 실림, 저장소가 로깅을 설정하지 않아 기본 WARNING에서는 나오지 않음, 구현 티켓의 수락에 "`secret_args`가 있는 도구를 http 모양의 서버에 부르며 루트 로거를 DEBUG로 켠 테스트에서 그 값이 로그에 나타나지 않는다"를 넣음.
- ADR 0049 "다른 ADR의 본문"에 ADR 0009의 둘째 날 문장을 더하고, ADR 0009에 이력 "2026-11-09 매니페스트에 환경 변수 필드가 생겼고 그 자리는 이름만 담는다"를 더했다(그 ADR의 2026-10-03 이력이 첫째 날을 적은 선례). 포인터는 달지 않았다(지난 이력 항목은 기록이다).

남긴 것: 없음. 오탐 둘은 위 근거로 고치지 않았다.

다시 돌린 명령: `uv run python tools/check_adr_pointers.py`는 출력 없이 끝났다(종료 0). 나머지 손으로 치는 다섯은 다음 커밋의 pre-commit으로 갈음하고 결과는 커밋 뒤에 적는다.
