# 01: 계약 — mcp 매니페스트의 `[server]`가 `transport`로 stdio와 http를 가른다

**What to build:** 매니페스트 저자가 mcp 플러그인의 `[server]`에 `transport = "http"`와 `url`을 적고, 헤더가 필요하면 `[server.headers]`에 헤더 이름마다 환경 변수 이름을 적으면 그 매니페스트가 읽힌다. 운영자가 관리 API로 그 플러그인의 매니페스트를 읽으면 `transport`·`url`·`headers`(헤더 이름과 변수 이름)가 파일에 적은 글자 그대로 실린다. `transport`가 없는 지금의 매니페스트는 stdio로 읽혀 한 글자도 고치지 않고 그대로 돈다. 모양을 잘못 적으면(다른 모양의 칸, 모르는 `transport`, http·https가 아닌 주소, 사용자 정보가 든 주소, 패턴 밖의 헤더 이름이나 변수 이름, 대소문자만 다른 헤더 이름 둘, 라이브러리와 HTTP가 정하는 헤더 이름 아홉) 읽는 단계에서 어느 칸이 틀렸는지와 함께 거부된다. 관리 화면 개발자에게는 생성 TS 타입이 `transport`로 좁혀져, 좁히지 않고 `url`을 읽는 코드가 컴파일에서 걸린다. 아직 붙지는 않는다. http 모양의 서버를 쓰는 실행은 `MCP 서버 <이름>(<url>)에 붙지 못했다: NotImplementedError: http 전송은 아직 구현되지 않았다`로 원인 `tool_connection`의 `run_failed`가 된다.

이 기능의 계약 티켓이고 02를 막는다(03·04는 02를 거쳐 막힌다). 계약은 sdk의 두 모델과 합, `openapi.json`, 생성 TS 타입이다. 끌고 오는 것은 어댑터의 `transport` 갈래, 모델을 만드는 테스트 자리, 관리 화면의 픽스처와 스토리, `.claude/rules/sdk.md`의 `[server]` 문장이다. 리뷰의 질문은 "동작하나"가 아니라 이 모양과 이름으로 오래 살 수 있느냐다.

**병합 뒤에 틈이 있다(to-tickets에서 사용자가 네 장 분할을 골랐다).** 이 티켓만 병합된 main에서 http 모양의 mcp 플러그인을 쓰는 실행은 위 문구의 도구 연결 실패로 끝난다. stdio 모양은 바뀌지 않는다. 02가 이 갈래를 실제 접속으로 바꾼다. 이 티켓이 쓰는 문장(독스트링, 주석, rules)은 틈 동안에도 참이어야 한다. http 모양이 읽힌다는 것과 아직 붙지 않는다는 것을 함께 말하고, 접속·헤더 값·닫기의 동작은 02와 03이 쓴다.

근거는 `.scratch/mcp-http/spec.md`의 "매니페스트"와 그 2026-11-09 명세 검토 주석, "계약과 관리 화면"과 그 주석, "고칠 자리의 묶음"의 A 줄과 그 주석, Testing Decisions의 "sdk 매니페스트 시험의 사례"·"계약과 관리 화면"이다. 측정은 `.scratch/mcp-http/probes/manifest_shape.py`와 그 `README.md`이고 다시 돌리지 않는다. 앞선 결정은 ADR 0049의 결정 "매니페스트"·"주소"와 Consequences "계약 변경이 첫 티켓이다", ADR 0008의 2026-09-21 이력(`schema_version`), ADR 0010(직렬화 스키마에서 기본값 있는 칸도 required)이다.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

### sdk — 두 모델과 합

- [ ] **`[server]`는 모양마다 모델이 하나다.** `StdioServer`는 `transport`(닫힌 값 `"stdio"`, 기본값 `"stdio"`), `command`, `args`(기본 빈 튜플), `secret_args`(기본 빈 표)이고, `HttpServer`는 `transport`(닫힌 값 `"http"`, 필수), `url`, `headers`(기본 빈 표), `secret_args`다. 두 모델 모두 매니페스트 공통 설정(모르는 칸 거부, 불변, 직렬화 스키마에서 기본값 있는 칸도 required)을 쓴다. `McpServer`는 둘을 `transport`로 가르는 합이고 매니페스트의 `server` 칸은 그 합 또는 없음이다
- [ ] **판별자는 호출 가능 판별자다(pydantic의 `Discriminator`에 함수를 준다).** `transport`가 없으면 stdio로 읽는다. 보통 판별자(`Field(discriminator="transport")`)는 칸이 없는 입력을 `union_tag_not_found`로 거부해 지금 매니페스트가 모두 깨진다(쟀다, `manifest_shape.py`)
- [ ] **`url`은 문자열 그대로 보관한다.** 읽는 단계에서 `urllib.parse.urlsplit`으로 scheme이 `http`·`https`인지, netloc에 `@`(사용자 정보)가 없는지, 호스트가 비지 않았는지만 본다. 쿼리 문자열과 조각은 막지 않는다. `AnyHttpUrl`은 쓰지 않는다(빈 경로에 `/`를 붙이고 호스트를 소문자로 바꿔 "글자 그대로"와 어긋난다)
- [ ] **헤더 이름과 환경 변수 이름의 패턴은 타입의 제약(`StringConstraints(pattern=…)`)으로 건다.** 헤더 이름은 RFC 9110의 토큰 문자(``!#$%&'*+-.^_`|~``와 글자·숫자), 변수 이름은 `^[A-Za-z0-9_]+$`다. 그래야 `openapi.json`에 같은 규칙이 `patternProperties`로 실린다(명세 검토가 pydantic 2.13.5로 손으로 봤다). 대소문자만 다른 헤더 이름 둘의 거부는 스키마로 나타낼 수 없어 검사기에 둔다
- [ ] **헤더 이름 아홉을 대소문자를 가리지 않고 거부한다.** `Host`, `Content-Length`, `Transfer-Encoding`, `Connection`, `Accept`, `Content-Type`, `Mcp-Session-Id`, `Mcp-Protocol-Version`, `Last-Event-Id`다. mcp가 요청마다 싣는 헤더는 매니페스트의 값을 조용히 덮고, `Host`는 요청을 다른 호스트 이름으로 보낸다(명세 "매니페스트"의 주석)
- [ ] **거부의 위치는 명세가 잰 그대로다.** http에 `command`는 `server.http.command`, stdio에 `url`은 `server.stdio.url`(둘 다 모르는 칸), 모르는 `transport`는 `server`, stdio에 `command` 없음은 `server.stdio.command`(종류 `missing`)다. 운영자가 보는 글은 지금의 문구 규칙(종류, 위치, pydantic의 문구. 값은 되울리지 않는다) 그대로다
- [ ] **`[server]`가 없을 때의 문구를 두 모양을 드는 글로 바꾼다.** 지금 `sdk/manifest.py`의 `mcp 플러그인은 [server] 표가 필요하다 (command, args)`를 `mcp 플러그인은 [server] 표가 필요하다 (command, args 또는 transport = "http", url)`로 고친다
- [ ] **`schema_version`은 `"1"` 그대로다**(ADR 0008의 2026-09-21 이력 기준. `transport` 없음이 stdio라 옛 매니페스트의 뜻이 바뀌지 않는다)
- [ ] **sdk 매니페스트 시험의 사례.** `transport` 없음은 `StdioServer`로 읽힌다. http 모양이 `HttpServer`로 읽힌다. 위 거부 위치 넷. `ftp://`와 scheme 없는 주소, 사용자 정보가 든 주소는 거부된다. 토큰 문자가 아닌 헤더 이름과 패턴 밖의 변수 이름, 대소문자만 다른 헤더 이름 둘, 헤더 이름 아홉(대소문자를 바꾼 것 하나 포함)은 거부된다. 직렬화 스키마에서 `server`는 두 모양의 oneOf이고 두 모양 모두 `transport`가 required이며 `headers`는 `patternProperties`다. 실패를 기대하는 시험은 pydantic 오류의 `type`과 위치로 까닭을 단언한다(`CODING_STANDARDS.md`). 선례는 `tests/sdk/test_manifest.py`의 서버 표·직렬화 스키마 시험이다

### 어댑터와 모델을 만드는 자리

- [ ] **어댑터가 서버를 `transport`로 가른다.** `McpServer`가 합(호출할 수 없는 `Annotated` 별칭)이 되면 어댑터가 `server.command`·`server.args`를 읽는 자리가 pyright를 지나지 못한다. 한 서버를 여는 문맥과 여는 동안의 실패를 `ConnectionError`로 바꾸는 자리는 두 전송이 함께 쓰고, 그 아래 세션을 여는 자리만 갈라진다(명세 "세션을 여는 자리와 두 전송의 공통"). 실패 문구의 괄호는 stdio면 지금처럼 명령, http면 매니페스트의 `url` 그대로다. stdio 갈래의 동작은 바뀌지 않는다
- [ ] **http 갈래는 여는 단계 안에서 `NotImplementedError("http 전송은 아직 구현되지 않았다")`를 던진다.** 그래서 문구는 `MCP 서버 <이름>(<url>)에 붙지 못했다: NotImplementedError: http 전송은 아직 구현되지 않았다`이다. 어댑터 시험이 그 `ConnectionError`와 문구를 단언한다(선례 `tests/adapters/test_mcp.py`의 `test_서버_기동_실패는_서버_이름과_명령을_든_연결_오류다`). core가 여는 동안의 `ConnectionError`를 원인 `tool_connection`의 `run_failed`로 쓰는 것은 `tests/core/test_run.py`의 `BrokenTools` 시험이 이미 고정한다. 이 시험은 02가 실제 접속의 시험으로 바꾼다
- [ ] **`McpServer(`로 모델을 만드는 자리 열 곳을 고친다.** to-tickets 시점(main `5af643d7`)에 `grep -rn "McpServer(" tests src`에서 정의 줄을 빼면 `tests/adapters/test_mcp.py` 여덟, `tests/core/test_run.py` 하나, `tests/channel/cli/test_interrupt.py` 하나다. 그 가운데 `test_mcp.py`의 `_PARENT`와 `test_interrupt.py`의 `_MCP_CHILD`는 자식 스크립트 문자열 안이라 pyright가 보지 못하고 그 시험을 돌릴 때만 깨진다. 고친 뒤 다시 grep해 남은 것이 없는지 본다
- [ ] **`server.command`·`server.args`를 읽는 자리도 고친다.** 합에는 그 칸이 없어 모양을 좁히지 않고 읽는 줄은 pyright를 지나지 못한다. to-tickets 시점(main `5af643d7`)에 `grep -rn "server\.command\|server\.args" src tests`로 어댑터 밖에서 나오는 것은 `tests/adapters/test_filesystem.py`의 매니페스트 읽기 시험 하나와 `tests/sdk/test_manifest.py`의 서버 표 시험이다. `secret_args`는 두 모양이 함께 가져 좁히지 않고 읽힌다

### 계약 파일과 생성 타입

- [ ] **`openapi.json`을 `uv run python tools/export_openapi.py`로 다시 뽑는다.** 매니페스트 응답의 `server`는 `anyOf`에 `oneOf[StdioServer, HttpServer]`와 `null`이 서는 모양이다(쟀다, `manifest_shape.py`). 호출 가능 판별자라 `discriminator.mapping`은 없다. 최신성 시험과 생성 클라이언트의 `check:api-client`가 판정한다(`.claude/rules/http.md`)
- [ ] **생성 TS 타입을 다시 만들고, `server` 값을 생성 타입으로 적은 관리 화면의 픽스처와 스토리 넷에 `transport: "stdio"`를 더한다.** 넷은 `web/apps/admin/components/pages/HomePage.test.tsx`, `components/pages/RunPage.decision.test.tsx`, `components/organisms/RunDetail.stories.tsx`, `components/organisms/PluginDetail.stories.tsx`다(ADR 0049 Consequences). 타입 검사가 깨지는 것이 첫 빨강이다. `[server]`에 `command`가 없는 거부를 든 `components/organisms/PluginList.stories.tsx`의 글은 운영자 파일의 문구를 흉내 낸 임의의 글이라 그대로 둔다(명세가 정했다). e2e의 stdio 매니페스트(`e2e/stack.ts`)는 `transport`가 없어도 stdio라 그대로다
- [ ] **관리 화면은 바뀌지 않는다.** 컴포넌트는 `server`의 칸을 읽지 않는다(ADR 0049가 `web/apps/admin`을 grep했다). 사진 비교 `pnpm -C web visual:admin`으로 바뀐 사진이 없는 것을 본다. 바뀌면 그 까닭을 PR 본문에 적는다
- [ ] **스토리 14의 시험: 관리 API 응답이 파일 그대로다.** 선례는 `tests/test_server.py`의 `test_mcp_매니페스트의_command_와_args_도_가리지_않고_내보낸다`다. 저장소의 `plugins/`에는 http 모양의 예시를 두지 않으므로(ADR 0049) http 매니페스트는 시험이 만든 플러그인 루트에 두고, 관리 API의 매니페스트 응답에서 `transport`·`url`·`headers`(헤더 이름과 변수 이름)를 본다. `url`은 대문자가 든 호스트와 빈 경로(예: `http://Rag-Engine:8000`)로 적어 응답이 글자 그대로인지 단언한다(`AnyHttpUrl`을 거부한 결정을 고정한다)
- [ ] **스토리 15의 시험: 생성 타입이 `transport`로 좁혀진다.** `web/packages/api-client/src/clients.test-d.ts`의 선례대로 tsc가 판정하는 타입 시험을 둔다. `transport`로 좁힌 뒤 `url`을 읽는 코드가 지나고, 좁히지 않고 `url`을 읽는 줄에는 설명과 함께 `@ts-expect-error`를 단다(헌법 원칙 III, 타입 시험 파일에서만)

### 문서

- [ ] **`.claude/rules/sdk.md`의 "`mcp`만 `[server]` 표(`command`, `args`)를 가진다"를 두 모양으로 고친다.** `transport`로 가르는 두 모양, 판별자가 `transport` 없음을 stdio로 읽는 것, `url`과 헤더 이름·변수 이름의 검사, 헤더 값은 매니페스트에 없고 이름만 있다는 것이다. 고치기 전에 Skill 도구로 `writing-for-agents`를 부른다(`.claude/rules/agent-docs.md`)
- [ ] **옛 표현을 저장소 전체에서 grep해 살아 있는 문서에 잔존이 0인지 본다**(`CLAUDE.md` 작업 규약 4). `[server]`가 `command`·`args`만 든다고 읽히는 문장이다. ADR 0049가 고칠 자리로 넘긴 `.claude/rules/adapters.md`·`.claude/rules/core.md`의 MCP 문장은 접속을 들이는 02의 몫이고, 이 티켓에서는 틈 동안 거짓이 되는 문장만 고친다. 기록(일지, 대기열, ADR 이력)은 고치지 않는다

### 검증

- [ ] **빨강을 먼저 본다**(헌법 원칙 II). 첫 빨강은 sdk 매니페스트 시험, `openapi.json` 최신성 시험, 픽스처 넷의 타입 검사, 타입 시험, 어댑터의 http 갈래 시험이다
- [ ] **검증 명령이 모두 초록이다.** 손으로 치는 다섯에 더해 관리 화면 e2e(`pnpm -C web/apps/admin exec playwright test`. api-client가 바뀐다)와 사진 비교 `pnpm -C web visual:admin`을 친다. 생성 타입의 바뀐 몫이 위젯이 쓰는 api-client에 닿으면 위젯 e2e(`pnpm -C web/apps/widget exec playwright test`)도 친다. `-m llm`은 이 티켓이 닿지 않는다
