# 2026-11-05 (06) approval-rules 설계 인터뷰

## 시작

next-session 지시문으로 연 세션이다. 브랜치 `docs/approval-rules-design`, 워크트리 `approval-rules-design`, 모델 Fable 5.1 / xhigh.

> 사용자: 다음 작업: 기능 approval-rules. 운영자의 승인 규칙 파일(후보 6)의 설계 인터뷰. 선행 조건인 skill-plugin의 티켓 다섯(PR 461~465)이 모두 병합됐고 .scratch/approval-rules/는 아직 없다 … 이어받을 상태: (1) plan.md의 skill-plugin 행이 in-progress로 남았으나 티켓 다섯이 모두 done이다. approval-rules의 선행 조건이 찼으므로 이 PR에서 그 행을 done으로 고칠지 인터뷰 때 판단한다. (2) PR 466(harness 042)의 claude-review가 두 회차 모두 짚은 Minor를 보류했다 … 이 인터뷰의 몫이 아니다 … 이번 요청 범위: PR과 병합까지

주 체크아웃 정리(`tidy-checkouts`)를 먼저 돌았다. 루트 main을 ea1453cd에서 b98b8dd5로 당겼고, 워크트리 `04-admin-skill-toggle-and-decision-preview`와 그 브랜치, 로컬 브랜치 `worktree-041-mutate-check-marker-quality`를 지웠다. 04를 쥔 쉬는 세션의 프로세스는 `end-holders`로 끝냈다. 남긴 것: `05-default-model-required-and-checked`는 다른 프로세스(agent-os.exe, python.exe 둘, node.exe, esbuild.exe 둘)가 모듈을 올려 이름 바꾸기가 막혔다(종료 1). 03·06은 바뀐 파일이 있다. 041·admin-style-spec·admin-style-to-spec·mcp-shutdown-spec·web-widget-spec은 병합된 PR이 없다. 042는 세션 셋의 claude.exe가 쥐고 있다. confident-wright·elegant-dijkstra는 앱의 표지가 있다. 휴지통에 04의 `web/node_modules` 조각이 esbuild.exe 때문에 남았고 `empty-trash`도 1로 끝났다. 다음 정리가 다시 본다.

plan.md의 skill-plugin 행은 티켓 다섯이 모두 병합됐는데 `in-progress`라, 상태 전이 규약(`docs/agents/issue-tracker.md` 전체 계획: 마지막 티켓이 병합될 때 done)에 따라 이 PR에서 `done`으로 고친다. 질문으로 올리지 않았다.

## 찾은 사실

1라운드를 올리기 전에 서브에이전트 셋(승인 흐름 코드, 운영자 파일 선례, 일지의 결정 원문)이 찾고 이 세션이 다시 대 본 것이다. 이 세션이 다시 대 보지 않은 것은 "서브에이전트가 …"로 표시했다. 표시는 코드를 읽었다 / 손으로 봤다 / 어림이다.

- 승인 게이트는 `core/run.py`의 `_Context._call` 한 자리다. 루프가 요청한 호출(`loop.py`의 `_execute`)과 에이전트의 직접 호출(`ctx.tool()`)이 같은 길을 지난다. 재생 기록이 있으면 게이트를 건너뛰고, 결정이 없고 `name in policy.approvals`이면 `_pause`로 멈춘다. 거부는 `_deny`가 도구를 부르지 않고 `tool_called(ok=false, content="승인자가 거부했다: {reason}")`로 남기며 루프는 계속되고 직접 부른 쪽은 `ToolError`를 받는다(코드를 읽었다, `run.py` 558~615).
- `requires_approval`이 가리키는 도구가 실재하는지 보는 검사는 준비 단계가 아니라 연결 직후다. `_Body._attend`가 `_reject_unknown_declarations(prepared.policy, connection.tools())`를 부르고(`run.py` 1036), 어긋나면 `LookupError`가 `run_failed(cause="tool_connection")`로 끝난다(코드를 읽었다, `run.py` 267·1542).
- 도구 이름은 MCP 서버가 준 원 이름 그대로이고 서버 접두가 없다. `adapters/mcp.py`의 `connect`가 `routes[route.tool.name] = route`로 모아 같은 이름이면 뒤 서버가 앞 서버를 조용히 덮는다(코드를 읽었다, 74~78). `ToolSpec`(`core/ports.py` 415)은 name·description·input_schema만 들고 서버가 없다. core의 타입이라 sdk 계약이 아니다. 모델에게는 `_Context.llm`이 `llm()` 호출마다 `tools()`를 읽어 `bind_tools`로 붙인다(서브에이전트가 코드를 읽었다, `run.py` 496, `loop.py` 57~83).
- `ToolCalled`의 칸은 run_id·ts·tool·ok·args·content, `RunPaused`는 run_id·ts·tool·args다(`sdk/events.py` 94·104). 트레이스는 형식 "3"으로 쓴다(`adapters/jsonl.py` 50 `TRACE_SCHEMA_VERSION`). 실패 원인은 아홉이다(코드를 읽었다).
- 결정 값은 `Approve`와 `Deny(reason)` 둘이고 채널 셋(CLI `resume --approve|--deny`, 운영자 채널 `POST /runs/{id}/approval`, 최종 사용자 `POST /end-user/runs/{id}/approval`)이 같은 둘을 받는다. 관리 API에는 결정 경로가 없다(서브에이전트가 코드를 읽었다).
- 꺼짐 파일 선례(`adapters/filesystem.py`): `schema_version="1"` 필수, 이름 배열 넷, 모르는 키는 손상(`extra=forbid`), 없으면 빈 집합, 깨지면 `PluginError("운영자 파일이 깨졌다: …")`로 500, 캐시 없음. `read_disabled`는 문법과 이름 패턴까지만 보고 이름이 실재하는지는 보지 않는다(코드를 읽었다, 103~109·228~234). 준비 `_prepare`(`run.py` 1235)가 `run`·`resume`에서 한 번 부르고(1267) 플러그인 목록(`list_manifests`)은 부르지 않는다(코드를 읽었다. `run.py`에 `list_manifests`가 없다). 저장소에 추적되는 `disabled.toml`은 없다(서브에이전트가 손으로 봤다, `git ls-files`).
- 관리 API의 플러그인 경로는 `GET /plugins`, `GET /plugins/{kind}/{name}`, `PUT /plugins/{kind}/{name}/enabled` 셋이고(그 밖에 `/health`와 트레이스 경로 둘이 있다, `admin/http.py`) 운영자 파일을 읽는 경로가 없다. 결정 칸의 꺼짐 미리 알림은 `web/apps/admin/components/organisms/RunDecision.tsx`의 `disabledFor`(80)다(코드를 읽었다).
- 예시 에이전트는 calc 하나(`mcp=["everything"]`, `requires_approval` 없음)이고 서버는 everything 하나다. 기본이 "묻는다"가 되면 멈추는 자리: 위젯 e2e의 `tools` 에이전트(`web/apps/widget/e2e/plugins.ts`의 `ctx.tool("add")` 둘), `tests/test_main.py`의 calc `-m llm`, `tests/channel/http/test_router.py`의 `ADDING`, `test_end_user.py`의 `looping`·`working`, `tests/core/test_run.py`의 도구를 부르는 사례 다수(서브에이전트가 코드를 읽었다. 다수는 어림이다).
- `CONTEXT.md`에는 운영자·운영자 파일·규칙 파일·서버 파일·사이트 파일·승인·결정·일시정지·도구·MCP 서버·신뢰 수준·최종 사용자·채널·주체가 있고, 저자·꺼짐 파일·승인 게이트·운영자 채널은 없다(서브에이전트가 읽었다). 규칙 파일의 정의: "운영자가 도구 호출을 막을지(deny), 물어볼지(ask), 묻지 않고 허락할지(allow)를 모든 에이전트에게 또는 에이전트마다 적은 운영자 파일. 적지 않은 호출은 묻고, 저자가 매니페스트에 적은 승인 요구를 풀지는 못한다."
- 묶음 ① 라운드의 원문(일지 2026-11-04-01)이 정한 것과 미룬 것: 파일 이름은 명세가 짓는다(148·258행). 읽는 때는 "부를 때마다 읽는 쪽이다(어림. 그 기능의 명세가 정한다)"(1367행). 맡기기의 deny·ask는 어림(1146·1273행). 사용자 원문 "일단 "도구 이름과 서버 와일드카드만"으로 하고 우리 프로젝트도 READ, WRITE 등 내장도구가 생긴다면 추가하자."(150~154행), "Claude Code의 평가 순서처럼 하자. 기본을 '물어본다'로 …"(156~157행). 일지 2026-11-03-04의 213행 "> 사용자: 못 풀게 하자."가 "운영자는 저자의 `requires_approval`을 풀지 못한다"의 원천이다.

## 1라운드

호출 둘. 첫 호출의 셋은 아래이고, 둘째 호출(같은 이름의 도구, 관리 화면 범위)은 그 뒤에 적는다.

> 사용자: (도구 호출마다 어느 규칙이 판정했는지를 트레이스에 남길까요?) "선택 칸 하나로 남긴다 (Recommended)" — 설명: tool_called와 run_paused에 선택 칸 하나를 더해 판정의 근거(운영자 deny / 저자 requires_approval / 운영자 ask / 운영자 allow / 적힌 규칙 없음)를 적는다. 트레이스 형식은 지금 쓰는 3 그대로이고(adapters/jsonl.py의 TRACE_SCHEMA_VERSION, 코드를 읽었다) ADR 0042 묶음 ②가 밀리초 칸에 정한 "기본값 없는 선택 필드, 형식 번호 그대로"와 같은 모양이다. 옛 트레이스에는 칸이 없다. openapi.json과 생성 TS 타입이 바뀌어 첫 티켓이 계약 티켓이 된다. 운영자가 "왜 멈췄나, 왜 그냥 돌았나"를 트레이스에서 읽을 수 있어 ADR 0042의 "기록" 보장이 이 기능에서 선다.

> 사용자: (실행이 멈춘 사이 운영자가 그 도구를 deny로 바꿨는데 승인 결정이 오면?) "deny가 이긴다 (Recommended)" — 설명: 재개도 준비 단계(core/run.py의 _prepare)를 지나며 운영자 파일을 다시 읽으므로(꺼짐 파일을 그렇게 읽는다, 코드를 읽었다) 지금 디스크의 규칙을 집행한다. 결정이 승인이어도 그 도구를 부르지 않고 거부로 기록하며(지금의 거부와 같은 길) 실행은 계속된다. 지금 core의 "같은 호출이면 정책이 바뀌었어도 결정을 적용한다"(.claude/rules/core.md, ADR 0009 이력)는 저자의 requires_approval에만 남는다. 승인자가 최종 사용자일 수 있어, 운영자의 deny는 누구의 결정으로도 넘지 못한다.

> 사용자: (규칙 파일에 적은 에이전트·도구·서버 이름이 실제로 있는지 볼까요?) "모양만 본다 (Recommended)" — 설명: TOML과 칸의 모양(schema_version, 모르는 키 거부, 에이전트 이름의 패턴, 규칙 문자열의 두 꼴)만 판정하고 이름이 실재하는지는 보지 않는다. 꺼짐 파일이 그렇다(adapters/filesystem.py의 read_disabled는 문법과 이름 패턴까지만 보고 실재는 보지 않는다, 코드를 읽었다). 공통 표는 모든 에이전트에 걸려 어느 한 실행의 준비에서 다 대 볼 수 없다. 오타는 조용히 아무것도 하지 않는데, 기본이 "묻는다"라 오타의 결과는 "뜻밖에 묻는다"이고 뜻밖에 허락되는 일은 없다.

둘째 호출의 둘.

> 사용자: (한 에이전트가 고른 MCP 서버 둘이 같은 이름의 도구를 내면?) "연결 직후 실패한다 (Recommended)" — 설명: 연결된 도구 목록에 같은 이름이 둘 이상이면 requires_approval의 오타와 같은 자리(core/run.py의 _reject_unknown_declarations, 연결 직후, 코드를 읽었다)에서 run_failed(원인 tool_connection)로 끝낸다. 지금은 어댑터가 도구 이름으로 길을 모으므로 뒤 서버가 앞 서버를 조용히 덮는다(adapters/mcp.py 74~78의 routes[route.tool.name], 코드를 읽었다). 그 상태에서는 "도구 이름" 규칙이 어느 서버의 도구를 막는지 가를 수 없고 "서버:*" 규칙은 덮인 서버에 맞지 않는다. 이름이 같은 도구를 내는 서버 둘은 한 에이전트가 함께 고르지 못하게 된다.

> 사용자: (이 기능에서 관리 화면과 관리 API는 얼마나 바꿀까요?) "바꾸지 않는다 (Recommended)" — 설명: 규칙 파일은 꺼짐 파일처럼 git으로 고치고, 관리 API에 규칙 파일을 읽거나 쓰는 경로를 두지 않는다(지금 관리 API는 GET /plugins, GET /plugins/{kind}/{name}, PUT …/enabled 셋이고 운영자 파일을 읽는 경로가 없다, 코드를 읽었다). 운영자 파일의 화면 편집은 ADR 0042가 묶음 ⑤의 관리 화면 CRUD(후보 21)에 둔 일이다. 트레이스 상세는 앞 화면에서 더하기로 한 판정 칸을 보이는 데까지만 바뀐다(생성 타입과 화면의 필드 이름 표 갱신, 어림).

고르지 않은 선택지(라벨만): 기록의 "기록하지 않는다"·"새 이벤트 종류를 낸다", 재개의 "결정이 이긴다", 이름 검사의 "그 에이전트의 표만 연결 뒤 대 본다"·"에이전트 이름의 실재도 본다", 같은 이름의 "지금처럼 조용히 덮는다"·"mcp-trust(다음 기능)에 넘긴다", 관리 화면의 "결정 칸에 deny 미리 알림을 더한다"·"규칙 파일 원문 GET만 더한다".

## 찾은 사실 (2)

합의 요약을 올리기 전에 이 세션이 대 본 것이다.

- ADR 0009의 2026-09-22 이력 "결정은 정책이 아니라 멈춘 호출에 묶인다"(141~142행)가 "같은 호출이면 정책이 바뀌었어도 결정을 적용한다"를 든다(읽었다). 재개에서 운영자의 deny가 결정을 이기는 것은 이 문장의 범위를 저자의 `requires_approval`로 좁히므로 ADR 0009의 새 이력이다. 지난 이력 항목은 기록이라 포인터는 달지 않는다(`.claude/rules/adr.md`).
- 선택 칸을 더하며 트레이스 형식을 그대로 둔 선례는 ADR 0031(`RunFailed`의 원인)과 ADR 0009의 2026-09-22 이력(`LlmCalled.prompt`)이고, ADR 0040의 거부한 안이 그 선례와 치르는 값(`openapi.json`·생성 타입·관리 화면의 필드 이름 표)을 적어 두었다(읽었다). ADR 0008은 "버전을 올리는 것은 기존 필드의 뜻이나 필수 여부가 바뀔 때다"(27행).
- ADR 0012의 2026-11-04 이력이 ADR 0042의 기능 가운데 포트에 닿는 것으로 센 넷에 후보 6은 없다(읽었다). `PluginSource`의 규칙 파일 읽기와 `ToolSpec`의 서버 칸이 이 기능의 이력으로 선다.
- `docs/adr/README.md`의 마지막 행은 0043이다(`tail`로 손으로 봤다). `tools/sibling_overlap.py`가 낸 다음 빈 번호는 일지 2026-11-05-06, 대기열 573, 티켓 043이고 ADR 번호는 내지 않았다(이 브랜치에 새 번호가 없을 때라 커밋 전에 다시 친다). origin/main은 050bb13으로 이 워크트리의 기준(b98b8dd5)보다 앞섰다.

## 2라운드(합의 요약)

본문에 올린 합의 요약 열 가지는 아래 그대로다.

1. 자리와 읽는 때. 규칙 파일은 플러그인 루트의 운영자 파일이고 꺼짐 파일 옆에 둔다(이름은 명세가 짓는다). 실행을 준비할 때마다(시작과 재개 모두) 한 번 읽고 캐시하지 않으며, 그 실행의 호출마다 그 판을 집행한다. 도는 실행 중에 고친 파일은 다음 실행·재개부터 듣는다. 파일이 없으면 규칙 없음이라 모든 도구 호출이 묻는다. 깨지면 꺼짐 파일처럼 전부 거부한다(운영자 면 500, 최종 사용자 면 고정 문구 500). 준비 순서의 "운영자 파일의 손상" 자리에 든다.
2. 모양. `schema_version = "1"` 필수, 모르는 키는 손상. 공통 표 하나와 에이전트별 표(에이전트 이름이 키, 플러그인 이름 패턴)가 있고 표마다 `deny`·`ask`·`allow`의 문자열 배열이다(비어도 된다). 규칙 문자열은 두 꼴뿐이다. 도구 이름 그대로, 그리고 `<서버 플러그인 이름>:*`. 전역 `*`도 인자 패턴도 없다(내장 도구가 생길 때 더한다). 모양만 판정하고 이름이 실재하는지는 보지 않는다. 표와 키의 정확한 이름은 명세가 짓는다.
3. 판정. 공통 표와 그 에이전트의 표를 판정별로 합친다(두 표의 deny를 모두 모으고 ask·allow도 그렇게). 차례는 deny(운영자) → `requires_approval`(저자) → ask(운영자) → allow(운영자) → 어느 것에도 맞지 않으면 묻는다. 그래서 에이전트별 allow가 공통 deny·ask를 풀지 못하고, 공통 allow도 에이전트별 ask를 풀지 못한다(운영자 파일은 더하는 쪽으로만). deny는 모델에 붙이는 도구 목록에서 빼고, 직접 호출이나 모델이 이름으로 부른 호출은 도구를 부르지 않고 거부로 기록하며(`tool_called(ok=false)`, 문구는 명세) 루프는 계속되고 직접 부른 에이전트는 `ToolError`를 받는다. ask와 "묻는다"는 지금처럼 `run_paused`로 멈추고 그 실행의 채널이 결정한다. 둘은 행동이 같고 기록된 근거만 다르다. allow는 묻지 않고 부른다. `requires_approval`의 실재 검사는 deny로 빼기 전의 전체 목록에 대 본다.
4. 기록. `tool_called`와 `run_paused`에 선택 칸 하나(판정의 근거)가 는다. 값은 다섯이다. 운영자 deny, 저자 `requires_approval`, 운영자 ask, 운영자 allow, 적힌 규칙 없음. `run_paused`에는 멈추게 한 근거가, `tool_called`에는 그 호출을 판정한 근거가 든다(멈춘 뒤 결정을 받아 돈 호출이면 멈추게 한 근거 그대로). 재생 구간의 호출은 기록을 다시 쓰지 않는다. 트레이스 형식은 3 그대로다(선택 칸을 더하며 형식을 둔 선례는 ADR 0031과 ADR 0009의 2026-09-22 이력). `openapi.json`·생성 TS 타입·관리 화면의 필드 이름 표가 바뀌어 첫 티켓이 계약 티켓이다. 옛 트레이스에는 칸이 없다. 칸과 값의 이름은 명세가 짓는다.
5. 재개. 재개도 준비에서 규칙 파일을 다시 읽어 지금 디스크의 규칙을 집행한다. 멈춘 사이 그 도구가 deny가 됐으면 결정이 승인이어도 부르지 않고 거부로 기록하며 실행은 계속된다(근거는 운영자 deny). 그 밖의 변화(ask가 allow로 등)는 지금 규칙대로 결정을 그 호출에 적용한다. ADR 0009 이력의 "같은 호출이면 정책이 바뀌었어도 결정을 적용한다"는 저자의 `requires_approval`에만 남는다.
6. 같은 이름의 도구. 한 에이전트가 고른 서버들의 도구 목록에 같은 이름이 둘 이상이면 연결 직후 `run_failed`(원인 `tool_connection`)다. 이를 위해 어댑터가 도구마다 서버 플러그인 이름을 `ToolSpec`에 실어 넘긴다(core 타입, "서버:\*" 매칭의 근거이기도 하다). 검사가 어댑터에 서는지 core에 서는지는 명세가 정한다.
7. 층과 포트. 판정은 core의 게이트 한 자리(`_Context._call`)에 선다. 규칙 파일은 `PluginSource`에 동기 읽기 메서드 하나가 늘어 읽고 포트는 다섯 그대로다(ADR 0012의 이력). 형식은 어댑터가 소유하고 값은 core 타입이다(꺼짐 파일과 같은 자리). sdk는 이벤트의 선택 칸 말고는 바뀌지 않는다(매니페스트 그대로).
8. 범위 밖. 관리 API·관리 화면은 바꾸지 않는다(판정 칸을 그리는 데까지만). 사이트 축 없음. 인자 패턴 없음. 맡기기의 deny·ask는 묶음 ④에서. 서버 신뢰·도구 정의 해시는 다음 기능(mcp-trust). deny된 호출이 최종 사용자에게 보이는 모양은 지금의 거부 문구와 같은 길이다(위젯이 도구 결과를 그대로 보인다, 어림).
9. 치르는 값. 기본이 묻는다라 규칙 파일이 없는 배치에서는 모든 도구 호출이 멈춘다. 저장소의 calc와 e2e·테스트(위젯 e2e의 `tools` 에이전트, calc의 `-m llm`, 채널 테스트, `test_run.py`의 다수)가 allow 규칙 파일을 함께 둔다(구현 티켓). 같은 이름의 도구를 내는 서버 둘은 한 에이전트가 함께 쓸 수 없다. 오타는 소리 없이 "묻는다"가 된다.
10. 산출물. 새 ADR 하나(0044. 번호는 커밋 전에 다시 대조), ADR 0009·0012의 이력, `CONTEXT.md` 용어(domain-modeling 스킬), `plan.md`의 skill-plugin 행을 done으로, approval-rules 행에 ADR 참조, 이 일지. 명세(`.scratch/approval-rules/spec.md`)는 다음 단계(`/to-spec`, 사용자가 부른다)가 정한다. 파일·표·칸·값의 이름과 문구, 중복 검사의 자리, 테스트 자리가 거기 넘어간다.

> 사용자: (위 합의 요약 열 가지가 정한 것과 같나요?) "맞다, 산출물로 간다 (Recommended)" — 설명: 요약 열 가지가 그대로 ADR 초안과 CONTEXT.md 용어와 plan.md에 옮겨지고, 이름·문구·검사 자리는 다음 단계의 명세가 짓는다.

고르지 않은 선택지(라벨만): "고칠 것이 있다".

## 용어(domain-modeling)

grill-with-docs의 둘째 호출로 domain-modeling 스킬을 불렀다. 용어집(`CONTEXT.md`)에 대 본 것과 고친 것이다.

- "판정"은 용어집에서 재생 평가의 사람 판정(Verdict, 좋음·나쁨)이고 결정(Decision)의 _Avoid_에도 든다(읽었다). 그래서 런타임이 호출마다 규칙을 대 보는 일은 ADR 0044에서 "판정"이 아니라 "집행"이라 쓴다. 인터뷰가 "판정의 근거"라고 부른 칸은 새 용어 **적용 규칙(Applied Rule)**이다. 값 다섯(운영자 deny, 저자 승인 요구, 운영자 ask, 운영자 allow, 적힌 규칙 없음)이 정의에 들어 있다.
- **저자(Author)**가 용어집에 없었다(서브에이전트가 읽었고 이 세션이 `**저자` 머리를 grep으로 다시 봤다). 더하고, 운영자·최종 사용자 정의의 "플러그인을 쓰는 개발자"를 저자로 바꿨다.
- **승인 요구(Approval Requirement)**를 더했다. 저자의 `requires_approval`을 가리키는 말이 규칙 파일 정의에는 "승인 요구"로, 하위 실행 정의에는 "승인 정책"으로 갈려 있었다. 하위 실행 정의를 승인 요구로 바꿨다. ADR 0042 본문(70행)의 "승인 정책"은 수락된 ADR의 글자라 두었다(`.claude/rules/adr.md`의 "본문의 다른 글자는 고치지 않는다").
- 규칙 파일·운영자 파일·승인·결정·재개의 정의는 합의 요약과 어긋나지 않아 그대로다.

## 산출물(셀프 리뷰 전)

- `docs/adr/0044-rules-file-is-enforced-per-call-and-operator-deny-beats-the-decision.md`(proposed). 합의 요약 열 가지를 절 여덟(자리와 읽는 때, 모양, 집행의 차례, 기록, 재개, 같은 이름의 도구, 층과 포트, 범위 밖)과 Considered Options·Consequences로 옮겼다.
- ADR 0009. 본문 8행 "승인이 필요한 도구는 에이전트 매니페스트의 `requires_approval`이 정하고 …"에 `(바뀜: ADR 0044)`를 달고 이력 2026-11-05를 쌓았다. ADR 0042가 규칙 파일을 정하면서 이 문장에 포인터를 달지 않았는데, 세부를 정한 이 ADR이 단다.
- ADR 0012. 이력 2026-11-05(`PluginSource`의 규칙 파일 읽기, `ToolSpec`의 서버 플러그인 이름).
- `docs/adr/README.md`에 0044 행.
- `.scratch/plan.md`. skill-plugin 행을 done으로(03·05·04의 PR 번호와 함께), approval-rules 행에 설계 일지·ADR 0044·사용자가 고른 다섯·다음 단계.
- `CONTEXT.md`. 위 용어 절.

## 인계(셀프 리뷰 직전)

code-review 스킬을 부른 직후 인계 계기(`hook_handoff`)가 왔다. 세션 컨텍스트 282,486 토큰(문턱 200,000), 경계 "셀프 리뷰 직전". `handoff.md`를 Read로 열어 따랐다. 인계하지 않는 때 다섯에 들지 않는다. 계기를 낸 명령은 실패하지 않았고, 요청 범위(PR과 병합까지)는 이 경계에서 끝나지 않으며, 이 세션의 지시문은 인계로 연 것이 아니고, `인계 못함` 줄이 없고, 곁 세션이 아니다(`get_session`의 `self`에 `parentSessionId`가 없다). 셀프 리뷰는 밟지 않고 새 세션이 한다.

- 이 세션의 제목은 `docs/approval-rules-design`(이 세션이 첫 턴에 붙였다)이고 `docs/approval-rules-design (인계함)`으로 바꾼다.
- 커밋하지 않은 변경(`git status --porcelain`): 고친 것 `.scratch/plan.md`, `CONTEXT.md`, `docs/adr/0009-resume-by-replaying-the-trace.md`, `docs/adr/0012-ports-stay-five-lists-are-added.md`, `docs/adr/README.md`. 새 것 `docs/adr/0044-rules-file-is-enforced-per-call-and-operator-deny-beats-the-decision.md`, 이 일지. 내용은 위 "산출물(셀프 리뷰 전)" 절이다. 커밋도 푸시도 없고 PR도 없다.
- 이 세션이 번복하거나 고친 것: ADR 0044 "근거의 종류"의 "쟀다고 적은 수치가 없다"를 "수치 근거가 없다"로 바꿨다(측정 낱말 훅 알림. 낱말을 이름으로 든 것이었지만 걷어 냈다). 그 밖에 번복한 결정은 없다.
- 백그라운드 작업은 없다(`sibling_overlap.py`의 백그라운드 호출은 0으로 끝났다). 워크트리 잠금은 풀고 넘긴다.
- 주 체크아웃은 이 세션이 시작할 때 b98b8dd5로 당겼으나 그 뒤 origin/main이 050bb13으로 앞섰다(`git worktree list`와 `git rev-parse --short origin/main`으로 손으로 봤다). 새 세션의 지시문에 미갱신으로 적는다.
- 넘기는 단계(새 세션이 이 차례로 한다. "다음" 절은 단계를 닫는 세션이 쓴다): `/code-review`(기점 origin/main) 셀프 리뷰와 Critical·Major 반영 → ADR 0044 초안 승인을 AskUserQuestion으로 받고(작업 규약 5) 승인되면 ADR과 색인의 status를 accepted로 → 검증(문서만 바뀌어 손으로 치는 다섯은 pre-commit 결과로 갈음하되 마크다운 표·줄 구분 문자 검사는 pytest 저장소 상태 테스트가 본다) → origin/main을 이 브랜치에 합치고 `uv run python tools/sibling_overlap.py`로 ADR 0044·일지 06 번호를 다시 대조 → `git branch --show-current` 확인 뒤 커밋(메시지는 heredoc이나 파일) → `git-pr`로 PR(docs/ 면제 PR, 티켓 없음) → PR 직전 리뷰와 봇 회차 → 병합은 `next-session` `merge.md`의 "워크트리에서 병합할 때"를 Read로 열어 따른다 → next-session 지시문(다음은 `/to-spec approval-rules`, 사용자가 부른다) → retro.
- 이어받은 보류 하나는 그대로 넘긴다. PR 466(harness 042)의 claude-review가 두 회차 모두 짚은 Minor(카나리아 넷의 물음이 "훅마다 적은 문단"으로 남음)는 병합된 일지 2026-11-05-05의 "셀프 리뷰"에 적혀 있고 이 기능의 몫이 아니다.

지시문:

```
다음 작업: 기능 approval-rules. 운영자의 승인 규칙 파일(후보 6) 설계 인터뷰의 산출물(ADR 0044 초안, ADR 0009·0012 이력, CONTEXT.md 용어 셋, plan.md 두 행, 일지)을 셀프 리뷰부터 승인·커밋·PR·병합까지 마친다
다음 단계: 설계 인터뷰
어디서: 새 세션. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고(그 스킬이 사람에게 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /grill-with-docs approval-rules
브랜치: docs/approval-rules-design
모델: Fable 5.1 / xhigh. 2의 잇는 지시문
읽을 것: docs/journal/2026-11-05-06-approval-rules-design.md의 "인계(셀프 리뷰 직전)" 절(커밋하지 않은 변경과 넘기는 단계)과 "2라운드(합의 요약)" 절, docs/adr/0044-rules-file-is-enforced-per-call-and-operator-deny-beats-the-decision.md 초안, docs/adr/0042의 묶음 ① 절
이어받을 상태: 인계: 셀프 리뷰 직전. 커밋하지 않은 변경이 워크트리 approval-rules-design에 있고 셀프 리뷰(/code-review, 기점 origin/main)부터 한다. 일지 docs/journal/2026-11-05-06-approval-rules-design.md. 설계 인터뷰는 끝나 다시 묻지 않는다(라운드 둘, 합의 요약 확인됨). 산출물은 모두 쓰였고 셀프 리뷰·ADR 승인·검증·커밋·PR·병합이 남았다. ADR 0044와 색인의 status는 proposed이고 사용자 승인 뒤 accepted로 바꾼다. 일지의 "다음" 절은 아직 없다. PR 466의 Minor 보류는 이 기능의 몫이 아니다(일지 2026-11-05-05)
확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main(origin/main보다 뒤). 병합은 이 워크트리 사본의 next-session merge.md(없으면 SKILL.md)의 "워크트리에서 병합할 때"를 Read로 열어 따른다
이번 요청 범위: PR과 병합까지
```

제목을 `docs/approval-rules-design (인계함)`으로 바꿨고(앱이 묻지 않고 바꿨다), `git worktree unlock`으로 이 워크트리의 잠금을 풀었다(오류 없음). 같은 제목으로 도는 다른 세션은 없고 이 세션을 뺀 도는 세션은 0이다(`list_sessions` limit 50).

open-session을 부른다 2026-11-05T06:55Z

## 새 세션(셀프 리뷰부터)

인계 지시문으로 연 세션이다. 제목을 `docs/approval-rules-design`으로 바꾸고(앱이 묻지 않고 바꿨다) 주 체크아웃 정리(`tidy-checkouts`)를 먼저 돌았다. 루트 main을 b98b8dd5에서 050bb13b로 당겼다(`git merge --ff-only --no-overwrite-ignore origin/main`, 출력을 봤다). 휴지통의 04 `web/node_modules` 조각은 `empty-trash`가 지웠다. 남긴 것: 05는 `remove`가 종료 1이었다(agent-os.exe pid 7960, python.exe pid 26204·38052가 모듈을 올려 이름 바꾸기가 막혔다는 도구 출력). 042는 쉬는 세션 셋의 claude.exe를 `end-holders`로 끝냈는데 다시 친 `judge`에서 같은 세션 셋이 새 pid로 다시 쥐고 있어 그대로 두었다(앱이 다시 띄운 것으로 보이나 어림이다). 041은 한 시간 안에 활동한 세션(PR 467)이 쥐었다. 03·06은 바뀐 파일, admin-style-spec·admin-style-to-spec·approval-rules-design·mcp-shutdown-spec·web-widget-spec은 병합된 PR 없음, confident-wright·elegant-dijkstra는 앱 표지(모두 `judge` 출력). 그 뒤 `EnterWorktree`로 이 워크트리에 들어와 브랜치를 origin/main(050bb13b)으로 빨리 감기 했다. 커밋하지 않은 변경은 그대로다. `grill-with-docs`가 부르는 `grilling`·`domain-modeling`은 앞 세션이 마쳤으므로 다시 부르지 않았다.

`uv run python tools/sibling_overlap.py`: 번호 겹침 없음(이 브랜치의 새 번호는 일지 2026-11-05-06, ADR 0044). 워크트리 mcp-shutdown-spec이 `.scratch/plan.md`를 함께 고치고 있어 나중에 병합하는 쪽의 글자 충돌 후보다(도구 출력).

## 셀프 리뷰

`/code-review`, 기점 050bb13b(origin/main과 같다), 커밋 0, 고친 파일 5, 미추적 2. 표준 축(sonnet·high)과 명세 축(명세는 이 일지의 1라운드·2라운드 절과 시작 절의 지시문)이 나란히 돌았다.

### Standards(표준 축 보고)

Critical·Major 없음. 지적 11건(위반 3, 판단 5, 주장 3).

- Minor, `.scratch/plan.md` approval-rules 행: `docs/agents/issue-tracker.md`의 "계약의 모양은 ADR 번호로만 가리킨다"인데 선택 칸(다섯 값)·`ToolSpec` 서버 이름·원인 `tool_connection`을 풀어 적었다. 같은 행의 "판정한다"는 `CONTEXT.md`의 피할 말이다.
- Nit, `docs/adr/README.md` 0044 행 제목이 ADR H1("준비할 때마다 읽혀")과 어긋난다.
- Nit, `CONTEXT.md` 44행 "개발자가 코드로 쓰거나"가 저자의 _Avoid_ "개발자(단독)"에 걸린다.
- Minor(판단), ADR 0044 44행: "저자의 승인 요구에만 남는다"와 "승인 요구에서 빠짐 등은 결정을 적용한다"가 함께 서 모호하고, ask가 allow로 바뀌었는데 결정이 Deny일 때를 정하지 않는다.
- Minor(판단), ADR 0044 Consequences에 옛 코드가 새 칸이 든 줄을 손상으로 거부하는 대가가 없다(`.claude/rules/adapters.md`와 ADR 0031이 적은 대가).
- 판단 셋: ADR 0009의 `(바뀜: ADR 0044)`는 모양·자리가 맞되 0044가 proposed라 반려되면 매달린다. ADR 0042 70행 "승인 정책"은 기록으로 두는 쪽이 맞다. `.claude/rules/core.md` 재개 항목의 옛 문장은 구현 티켓이 고친다고 밝혀 허용 범위다.
- Minor(주장), ADR 0044 88행 "이 세션이 대 본 것": 일지가 몇 항목을 "서브에이전트가 코드를 읽었다"로만 적어 근거 종류가 부풀었다.
- Minor(주장), "관리 API 경로 셋"(ADR 0044 88행, 이 일지 23·42행): `admin/http.py`의 라우트는 여섯(`/health`, 플러그인 셋, 트레이스 둘)이다.
- Nit(주장), 이 일지 32행의 인용 "기본값 없는 선택 필드"는 원문(ADR 0042 52행) "기본값 없음의 선택 필드"와 다르다.
- 맞은 것: 인용 전부, 코드 참조 전부(형식 "3", 두 이벤트 칸, `ToolSpec` 세 칸, `routes[...]`, `read_disabled`, `_NOT_REPLAYED`, core.md 항목 넷), 닫힌 주장(원인 아홉, 결정 값 둘, 포트 다섯), 포인터·이력(ADR 0017 본문에 파일 수를 닫는 문장 없음, ADR 0012 2026-11-04 이력의 넷에 후보 6 없음, 선례 여섯), plan.md의 PR 번호와 상태 전이, 잔존 0(살아 있는 문서 기준).

### Spec(명세 축 보고)

누락·부분 없음, 범위 넘침 없음. 합의 요약 열 가지와 1라운드 답 다섯의 설명 조건이 ADR 0044에 모두 있고 지시문·용어·이력·ADR 0042 묶음 ①과의 대조도 충족. 지적 5건, 가장 심각한 것은 Minor.

- Minor, ADR 0044 14행 "`disabled.toml`처럼 그 실행을 전부 거부한다": 코드로는 `_prepare`의 `read_disabled`가 `PluginError`를 내 실행 식별자 전에 끝나고(트레이스 없음) 재개는 결정 이벤트 전이라 일시정지 그대로다(`run.py` 모듈 독스트링). 이 ADR의 "거부"는 호출 거부(`tool_called(ok=false)`)를 뜻해 "실행을 시작하지 않는다"로 써야 코드와 같다.
- Nit, ADR 0044 48행 "저자의 승인 요구의 오타와 같은 자리다"가 50행 "검사가 어댑터에 서는지 core에 서는지는 명세가 정한다"와 맞선다.
- Nit, ADR 0044 76행 "기본을 allow로 한다 … 라운드가 거부했다"의 근거를 못 찾았다. 일지 2026-11-04-01의 사용자 답은 선택지 밖의 "기본을 '물어본다'로"다.
- Nit(주장), 이 일지 32행 인용(표준 축과 같은 지적).
- 맞은 것: 따옴표 인용 9건, 이력 참조 7건, 코드 자리 20여 건. 깨짐 일곱은 스크래치패드 프로브로 `read_disabled`에 실제로 넣어 봤다(없음→빈 집합, 빈 파일·문법·모르는 키·형식 버전·이름 패턴·값 타입→"운영자 파일이 깨졌다", UTF-8→"운영자 파일을 읽을 수 없다". 열기 실패만 코드로 봤다. 프로브는 저장소에 두지 않았다).

### 반영

근거를 먼저 봤다. 관리 API 라우트 여섯은 `admin/http.py`의 `@router` 데코레이터 여섯으로 봤고(코드를 읽었다), plan.md 규약은 `docs/agents/issue-tracker.md` 32행, 옛 코드의 거부는 `.claude/rules/adapters.md` 11행과 ADR 0031 22행, 깨진 운영자 파일의 길은 `core/run.py` 32~39행 독스트링, 거부한 선택지는 일지 2026-11-04-01 156·161행과 2026-11-03-04 213행에서 읽었다. README 행과 ADR H1은 둘 다 "준비할 때 읽혀"로 같아(grep) 표준 축의 그 Nit은 틀렸다.

고친 것(새로 쓴 사실 문장은 PR 직전 리뷰의 밀 주장이다):

- ADR 0044 14행: "`disabled.toml`이 깨졌을 때와 같이 그 실행을 시작하지 않는다. 실행 식별자를 만들기 전에 `PluginError`로 끝나 트레이스가 없고, 재개는 결정 이벤트를 쓰기 전에 끝나 일시정지 그대로다(`core/run.py`의 모듈 독스트링. 코드를 읽었다)."
- ADR 0044 44행과 ADR 0009의 2026-11-05 이력: "(승인이면 부르고 거부면 거부로 기록한다)"를 더하고, "조건 없이 서는 것은 저자의 승인 요구뿐이고, 운영자의 규칙에서는 deny 하나가 결정을 이긴다"로 범위를 분명히 했다.
- ADR 0044 48행: "저자의 승인 요구의 오타가 실패하는 때(연결 직후)와 원인이 같다."
- ADR 0044 Considered Options: "기본을 allow로 한다"를 지우고, 거부한 안을 "운영자가 저자의 승인 요구를 푼다"(2026-11-03 라운드 밖 "못 풀게 하자")와 "allow를 두지 않는다(deny·ask 둘뿐), 좁은 allow가 넓은 ask를 이긴다"(2026-11-04 라운드가 고르지 않은 선택지. 사용자는 선택지 밖에서 "Claude Code의 평가 순서처럼 하자. 기본을 '물어본다'로")로 바로 적었다.
- ADR 0044 치르는 값: "이 기능 전의 코드가 새 칸이 든 `tool_called`·`run_paused` 줄을 읽으면 아는 종류의 모르는 필드라 그 트레이스를 손상(`PluginError`)으로 거부한다(`adapters/jsonl.py`의 `_read_event`, ADR 0031). `run_failed`의 원인 칸과 달리 두 이벤트는 재개의 입력이라, 옛 판은 새 판이 쓴 멈춘 실행을 재개하지 못한다. 같은 저장소를 옛 판과 새 판이 함께 읽지 않는 배치라 받아들인다."
- ADR 0044 88행과 이 일지 23행: "관리 API 경로 셋"을 "관리 API의 플러그인 경로 셋"으로(그 밖에 `/health`와 트레이스 경로 둘).
- 이 일지 15행: 서브에이전트만 읽은 항목은 그렇게 표시했다고 적었다.
- `.scratch/plan.md` approval-rules 행: 선택 칸·`ToolSpec`·원인의 모양을 ADR 번호로 가리키게 줄이고 "판정한다"를 "집행한다"로 바꿨다.
- `CONTEXT.md` 에이전트 정의: "개발자가 코드로 쓰거나"를 "저자가 코드로 쓰거나"로.

남긴 것과 이유:

- 이 일지 32행의 인용 어긋남(Nit): `> 사용자:` 인용은 그때 화면에 올린 선택지 설명을 글자 그대로 옮긴 기록이라 고치지 않는다. 원문은 ADR 0044 37행이 글자 그대로 들었다.
- README 행 제목(Nit): 지적이 틀렸다.
- ADR 0042 70행 "승인 정책", `.claude/rules/core.md` 재개 항목, proposed인 ADR에 단 포인터: 리뷰도 허용 범위로 봤다. 각각 기록, 구현 티켓의 몫, 승인 뒤 accepted로 바꾸는 이 PR의 절차다.
- ADR 0044 44행의 "ask가 allow로 바뀌었는데 결정이 Deny": 더한 괄호(거부면 거부로 기록한다)가 답한다.

다시 돌린 명령: `uv run pytest -q tests/tools/test_check_adr_pointers.py tests/tools/test_check_md_tables.py tests/tools/test_check_line_separators.py`가 85 passed(고치기 전에도 85 passed). `tools/check_adr_pointers.py`·`tools/check_md_tables.py`·`tools/check_line_separators.py`를 직접 쳐 출력 없이 끝났다. 손으로 치는 다섯은 커밋의 pre-commit으로 갈음하고 결과는 커밋 뒤에 적는다.

## ADR 0044 승인

셀프 리뷰를 반영한 뒤 AskUserQuestion으로 물었다(작업 규약 5). 질문에 올린 요약은 초안이 정한 여섯(자리와 읽는 때·없음과 깨짐, 집행의 차례와 allow의 한계, 적용 규칙 칸과 형식 3, 재개의 deny, 같은 이름의 도구, 관리 API·포트 그대로)과 치르는 값(규칙 파일 없는 배치의 멈춤, calc와 테스트의 allow 파일), 이름·문구는 명세가 짓는다는 것이다.

> 사용자: "승인한다 (Recommended)" — 설명: ADR 0044와 색인의 status를 accepted로 바꾸고, 커밋 → PR → PR 직전 리뷰와 봇 회차 → 병합까지 묻지 않고 진행합니다. 병합 뒤 다음 단계는 사용자가 부르는 /to-spec approval-rules입니다.

고르지 않은 선택지(라벨만): "고칠 것이 있다".

ADR 0044와 `docs/adr/README.md`의 status를 accepted로 바꿨다.

## 검증과 커밋

`git branch --show-current`는 `docs/approval-rules-design`이었고, `uv run python tools/sibling_overlap.py`는 번호 겹침 없음이었다(워크트리 041이 커밋하지 않은 일지 2026-11-05-07과 `.scratch/plan.md`를, mcp-shutdown-spec이 `.scratch/plan.md`를 함께 고치고 있다는 도구 출력). 커밋은 5dfd1b96 "docs: 운영자의 규칙 파일을 준비마다 읽어 호출마다 집행하는 설계를 ADR 0044로 정한다 (approval-rules)", 7 파일이다. pre-commit은 parallel-checks(pytest 나눠 돌기·타입체크·경계·web verify)가 581.88초에 Passed이고 나머지 검사도 Passed, Skipped는 셋이다. ruff check·ruff format(스테이지된 `.py` 없음), 카나리아 명세 모양(커밋에 `.scratch/**/probes/canary/*.toml` 없음), 헌법 버전(헌법 파일 없음). ruff 둘은 손으로 쳤다. `uv run ruff check .`는 All checks passed, `uv run ruff format --check .`는 1262 files already formatted. 카나리아 모양과 헌법 버전은 이 커밋에 대상 파일이 없어 칠 입력이 없다(`tools/canary.py --shape`는 명세 없이 치면 인자 오류 2로 끝난다).

pre-commit의 인용 검사(경고만)가 이 일지의 여섯 줄(26·44·140·152·153·154)을 원문과 다르다고 알렸다. 26행의 사용자 원문 둘은 일지 2026-11-04-01의 150행과 156행에서 앞머리를 grep으로 찾았다(원문이 줄을 걸쳐 있어 검사가 한 줄로 맞추지 못한 것으로 보인다. 어림). 44행의 "고르지 않은 선택지"는 화면에 올린 라벨이라 저장소에 원문이 없고, 140·152~154행은 리뷰 보고가 고치기 전의 ADR 문장을 인용한 것이라 고친 뒤의 ADR과 다르다. 여섯 모두 고치지 않는다.

## 인계(커밋 뒤)

커밋 직후 인계 계기(`hook_handoff`)가 왔다. 세션 컨텍스트 363,552 토큰(문턱 200,000), 경계 "커밋 뒤". 계기 직후 자동 압축이 와서, 압축 뒤에 `handoff.md`를 Read로 열어 따랐다. 인계하지 않는 때 다섯에 들지 않는다. 계기를 낸 커밋은 pre-commit을 지나 성공했고, 요청 범위(PR과 병합까지)는 이 경계에서 끝나지 않으며, 이 세션의 지시문의 "이어받을 상태"는 `인계: 셀프 리뷰 직전`이라 같은 경계가 아니고, `인계 못함` 줄이 없고, 곁 세션이 아니다(`get_session`의 `self`에 `parentSessionId`가 없다).

- 이 세션의 제목은 `docs/approval-rules-design`(이 세션이 첫 턴에 붙였다)이고 `docs/approval-rules-design (인계함)`으로 바꾼다.
- 커밋한 것: 5dfd1b96 하나(위 "검증과 커밋"). 푸시하지 않았고 PR은 없다(`gh pr view docs/approval-rules-design`이 없음). 커밋하지 않은 변경은 이 일지뿐이다(위 두 절과 이 절). 새 세션이 이 일지를 커밋한다.
- 이 세션이 번복하거나 고친 것: 셀프 리뷰 반영 아홉(위 "셀프 리뷰"의 "반영")과 ADR 0044·색인의 status를 accepted로. 결정을 번복한 것은 없다.
- 백그라운드 작업은 없다(커밋의 pre-commit은 끝났다). 워크트리 잠금은 풀고 넘긴다.
- 주 체크아웃: 루트는 main 050bb13b이고 origin/main도 050bb13b다(`git fetch origin` 뒤 `git worktree list`와 `git rev-parse --short origin/main`). 루트가 깨끗한지는 보지 못했다. 워크트리 세션의 가드가 `git -C <루트> status`를 거부했다.
- 나란히 도는 것: PR 468(`chore/043-plan-skill-plugin-done`, 열림)이 `.scratch/plan.md`의 skill-plugin 행을 done으로 고친다(`gh pr view 468 --json files`). 이 브랜치의 커밋도 같은 행을 done으로 고쳤다. 먼저 병합되는 쪽이 있으면 뒤쪽이 origin/main을 합칠 때 그 행에서 글자 충돌이 날 수 있다. 워크트리 mcp-shutdown-spec도 plan.md를 고치고 있다(`sibling_overlap.py` 출력).
- 넘기는 단계(새 세션이 이 차례로 한다. "다음" 절은 단계를 닫는 세션이 쓴다): 이 일지를 커밋 → PR 직전 리뷰(`coderabbit-review` 서브에이전트. 돌지 못하면 `/security-review`와 `bug-perf-review` 서브에이전트. 밀 주장은 위 "셀프 리뷰" "반영"의 고친 것 아홉 줄) → 지적 반영과 재검증 → `git-pr`로 PR(docs/ 면제 PR, 티켓 없음. 관련 티켓 칸은 면제의 종류 "기능의 설계") → `merge.md` 2의 봇 회차(`@coderabbitai review` 코멘트와 `uv run python tools/wait_ci.py <번호>` 백그라운드) → 병합은 `next-session` `merge.md`의 "워크트리에서 병합할 때"를 Read로 열어 따른다 → next-session 지시문(다음은 `/to-spec approval-rules`, 사용자가 부른다) → retro.
- 이어받은 보류 하나는 그대로 넘긴다. PR 466(harness 042)의 Minor는 이 기능의 몫이 아니다(일지 2026-11-05-05).

지시문:

```
다음 작업: 기능 approval-rules. 운영자의 승인 규칙 파일(후보 6) 설계 산출물(ADR 0044 accepted, ADR 0009·0012 이력, CONTEXT.md 용어 셋, plan.md 두 행, 일지)의 커밋을 PR 직전 리뷰·PR·봇 회차·병합까지 마친다
다음 단계: 설계 인터뷰
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /grill-with-docs approval-rules
브랜치: docs/approval-rules-design
모델: Fable 5.1 / xhigh. 2의 잇는 지시문
읽을 것: docs/journal/2026-11-05-06-approval-rules-design.md의 "인계(커밋 뒤)" 절(커밋한 것, 손으로 친 검사, 나란히 도는 PR 468, 넘기는 단계)과 "셀프 리뷰" 절의 "반영"(PR 직전 리뷰에 밀 주장), docs/adr/0044-rules-file-is-enforced-per-call-and-operator-deny-beats-the-decision.md(PR 본문의 원천)
이어받을 상태: 인계: 커밋 뒤. 설계 산출물 7 파일의 커밋 하나(셀프 리뷰 반영과 ADR 0044 승인·accepted 포함)까지 했고 푸시·PR은 없으며, 남은 단계는 일지 커밋 → PR 직전 리뷰 → git-pr → 봇 회차 → 병합 → next-session → retro다. 일지 docs/journal/2026-11-05-06-approval-rules-design.md. 설계 인터뷰는 끝나 다시 묻지 않는다(라운드 둘, 합의 요약 확인됨, ADR 0044 승인됨). 커밋하지 않은 변경은 그 일지뿐이다. 일지의 "다음" 절은 아직 없다. PR 466의 Minor 보류는 이 기능의 몫이 아니다(일지 2026-11-05-05)
확인할 선행 조건: 루트가 깨끗한지(워크트리 가드가 git -C <루트> status를 거부해 보지 못했다). PR 468(chore/043-plan-skill-plugin-done)이 .scratch/plan.md의 skill-plugin 행을 같은 뜻으로 고치고 있어, 먼저 병합되면 origin/main을 합칠 때 그 행의 충돌을 푼다
이번 요청 범위: PR과 병합까지
```

제목을 `docs/approval-rules-design (인계함)`으로 바꿨다(앱이 묻지 않고 바꿨다). `git worktree unlock`은 이미 풀려 있다는 오류(`is not locked`)로 끝나 넘어갔다. 같은 제목으로 도는 다른 세션은 없고 이 세션을 뺀 도는 세션은 0이다(`list_sessions` limit 50. PR 468의 세션 `chore/043-plan-skill-plugin-done`은 쉬고 있다).

open-session을 부른다 2026-11-05T07:57Z

## 새 세션(PR까지)

인계 지시문으로 연 세션이다. 제목을 `docs/approval-rules-design`으로 바꿨고(앱이 묻지 않고 바꿨다), `git worktree list`에서 이 브랜치가 워크트리 `approval-rules-design`에 체크아웃되어 있어 `EnterWorktree(path)`로 들어왔다. 지시문에 `tidy-checkouts`는 없다. `grill-with-docs`가 부르는 `grilling`·`domain-modeling`은 설계 인터뷰가 끝나 다시 부르지 않았다.

선행 조건 둘을 봤다. 루트는 이 세션이 시작될 때 앱이 찍은 git 상태에서 main 050bb13b이고 깨끗했다(워크트리 가드가 `git -C <루트> status`를 거부해 직접 치지는 않았다). `git fetch origin` 뒤 origin/main은 050bb13b로 이 브랜치의 기준(5dfd1b96의 부모)과 같아 합칠 것이 없다. PR 468(`chore/043-plan-skill-plugin-done`)은 열려 있고 병합되지 않았다(`gh pr view 468 --json state,mergedAt`). 고치는 파일은 harness 티켓 043, `.scratch/plan.md`, `.scratch/retro-queue.md`, 일지 2026-11-05-07의 넷이다. 이 PR보다 먼저 병합되면 origin/main을 합칠 때 plan.md의 skill-plugin 행에서 충돌을 푼다.

`coderabbit auth status`는 `Plan: Free`, `Seat: not assigned`였다. 2026-11-03의 두 PR에서는 `Seat` 줄이 없었는데(`operations.md` 리뷰 파이프라인 2) 오늘은 2026-09-23과 같은 모양이다. 서브에이전트 정의 1단계대로 CLI 축이 비어 있으므로 `coderabbit-review`는 부르지 않고 대체 둘(`/security-review`, `bug-perf-review` 서브에이전트)을 이 일지를 커밋한 뒤 나란히 돌린다(`operations.md` 리뷰 파이프라인 2). 밀 주장은 위 "셀프 리뷰"의 "반영"에 적은 고친 것 아홉 줄이다.
