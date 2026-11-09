# 2026-11-10 (01:52) mcp-http 계약

세션 제목 `01-contract-mcp-server-transport-stdio-or-http`. 브랜치 `feature/01-contract-mcp-server-transport-stdio-or-http`, 워크트리 `.claude/worktrees/01-contract-mcp-server-transport-stdio-or-http`(기준 `3cb40736`). 모델 Sonnet 5.5 / high(지시문).

## 사용자 프롬프트

> .claude/skills/implement/SKILL.md 를 읽어 그대로 따른다. 이 세션을 연 저장소는 `C:\project\agent`이고 작업 폴더가 그곳이 아니면 따르지 말고 알린다. 스킬의 인자는 이 줄의 '인자:' 뒤부터 메시지 끝까지다. 인자: .scratch/mcp-http/issues/01-contract-mcp-server-transport-stdio-or-http.md
>
> 다음 작업: `.scratch/mcp-http/issues/01-contract-mcp-server-transport-stdio-or-http.md`(mcp 매니페스트의 [server]가 transport로 stdio와 http를 가르는 계약(sdk 두 모델과 합, openapi.json, 생성 TS 타입)을 세운다)
> 이번 요청 범위: PR과 병합까지

## 한 일

티켓 01을 구현했다. 계약은 sdk의 두 모델(`StdioServer`, `HttpServer`)과 합 `McpServer`(호출 가능 판별자. `transport`가 없으면 stdio), `openapi.json`, 생성 TS 타입이다. 어댑터는 서버를 `transport`로 가르고 http 모양은 여는 단계에서 `NotImplementedError("http 전송은 아직 구현되지 않았다")`로 실패해 `MCP 서버 <이름>(<url>)에 붙지 못했다: …`인 `tool_connection`의 `run_failed`가 된다. `McpServer(` 생성 자리 열 곳과 `server.command` 읽는 자리(`test_filesystem.py`, `test_manifest.py`)를 고쳤고, 관리 화면 픽스처와 스토리 넷에 `transport: "stdio"`를 더했다. 스토리 14(관리 API 응답이 파일 그대로)와 15(생성 타입이 `transport`로 좁혀진다)의 시험을 더했다. `.claude/rules/sdk.md`의 `[server]` 문장을 두 모양으로, `adapters.md`의 연결 실패 문장에 http 모양의 현황을 고쳤다.

## 검증

- 러너 `uv run python tools/run_checks.py`: pytest 통과(694.9초), pyright 둘·lint-imports·지침 검사·타입 우회 검사·zizmor·훅 러너·커밋 검사 통과. 이 첫 러너의 web-verify는 `clients.test-d.ts`의 `@ts-expect-error` 줄에서 ESLint 오류 5건으로 빨갰고(타입 오류가 난 칸의 `any`가 안전하지 않은 사용으로 번졌다), 값을 `unknown`으로 받는 헬퍼로 고친 뒤 `pnpm -C web verify`를 다시 쳐 vitest 1606개 통과, tsc·ESLint·Prettier·tsconfig 검사가 초록이다.
- `uv run ruff check .`, `uv run ruff format --check .` 초록.
- 관리 화면 e2e `pnpm -C web/apps/admin exec playwright test` 9개 통과.
- 사진 비교 `pnpm -C web visual:admin`은 70개 통과, 2개 실패였다. 실패는 `organisms-plugindetail--disabled`의 너비 둘(320, 1280)이다. `PluginDetail`이 `formatJson(plugin.manifest)`로 매니페스트 전체를 JSON으로 그려, 픽스처에 더한 `"transport": "stdio"` 한 줄이 그림에 나타났다. 정답 네 장(너비 둘 × 모드 둘)을 `pnpm -C web visual:admin:update`로 갱신했고 다시 72개 통과다. 1280 라이트 사진을 열어 한 줄만 늘었음을 봤다.
- 위젯 e2e는 치지 않았다. 위젯은 `PluginManifest`와 `server` 칸을 읽지 않는다(`web/apps/widget`을 `PluginManifest|\.server\b`로 grep해 0건).
- 카나리아: `.claude/rules/adapters.md`와 `sdk.md`를 고쳤으므로 그 규칙을 원천으로 든 명세 다섯(`adapters_rule_rules_file_read`, `adapters_rule_new_optional_fields`, `adapters_rule_boundary_exceptions`, `sdk_rule_failure_cause`, `sdk_rule_shortcut_patterns`)을 `tools/canary.py`로 실제 돌렸다(claude 2.1.318, 커밋 `3cb40736` 위의 커밋하지 않은 작업 트리). 다섯 모두 통과 4(실험군 3, 대조군 1), "없음" 섞인 통과 0이다. 각 명세의 `# 최신 결과:` 줄을 이 결과로 바꾸고 지난 줄은 `# 앞선 결과:`로 내렸다. 이 PR에서 같은 PR 안의 통과가 없어 사전 확인 갈음 조건에 맞지 않아 실제로 돌렸다.

## 셀프 리뷰(`/code-review`)

범위: 기준 `3cb40736`, 변경 파일 25개, 커밋 0개, 미추적 0개. 표준 축은 Sonnet(high), 명세 축은 본 세션의 모델로 돌렸다.

고친 것:

- `HttpServer`의 검증자 주석이 "문구는 적은 값을 되울리지 않는다"고 썼으나 헤더 이름은 문구에 실린다(`헤더 이름을 적을 수 없다: HOST`). 코드로 확인하고 "url의 글자와 환경 변수 이름을 되울리지 않는다. 헤더 이름은 비밀이 아니라 싣는다"로 좁혔다(표준 축 Minor).
- ADR 0049 본문의 "화면은 바뀌지 않는다"와 티켓 "관리 화면은 바뀌지 않는다"가 거짓이었다. ADR 0049에 이력 2026-11-10 "관리 화면의 매니페스트 JSON에 transport 줄이 늘어 사진 정답이 바뀐다"를 더하고 본문 문장 바로 뒤에 포인터를 달았다(`tools/check_adr_pointers.py` 통과). 티켓의 해당 항목에 결과를, 명세 88줄에 주석을 달았다(두 축이 모두 짚었다. 명세 축 Major).
- `manifest.py`의 "특수 기호 열둘"은 열다섯이다(`!#$%&'*+-.^_`|~`를 세어 확인). 고쳤다(명세 축 Minor).
- `adapters/mcp.py`의 `_opened` 독스트링에 "(http 모양이면 주소)"를 더해 `_connecting`과 맞췄다(명세 축 Minor).
- `admin/http.py`의 "command 와 args 도 나간다" 주석에 http 모양의 url과 헤더 이름을 더했다(명세 축 관찰).
- 인용 `ADR 0049 "주소"`를 말이 실제로 있는 Consequences 44행 "문구에 실리는 것과 실리지 않는 것"으로 바꿨다(표준 축 Nit). 검증자 이름 `_header_names_are_distinct_and_free`를 `…_and_not_reserved`로 바꿨다(Mysterious Name).

남긴 것과 이유:

- 모듈 독스트링의 "그 실행은 원인 `tool_connection`의 `run_failed`로 끝난다"를 http 갈래부터 core까지 이어 밟는 시험은 없다. 티켓이 core의 `tests/core/test_run.py` `BrokenTools` 시험(가짜 연결의 `ConnectionError`)을 근거로 정했고 02가 그 시험을 실제 접속의 시험으로 바꾼다.
- `isinstance(server, HttpServer)`가 `_where`와 `_session`에 두 번 나온다(Repeated Switches). 둘뿐이라 허용 범위이고 02가 갈래를 더할 때 공유 지점을 본다.
- `url`은 `http://h:abc/` 같은 잘못된 포트와 앞뒤 공백·개행이 든 주소를 받는다. 명세가 "그 밖은 판정하지 않는다"고 했다.
- `_transport_of`의 문자열 확인 반복(Duplicated Code)과 `secret_args`의 두 모델 중복(Data Clumps)은 판단 항목이고, 주석이 까닭(공통 접근)을 밝혀 두어 오탐에 가깝다.

다시 돌린 명령: `uv run ruff check src`, `uv run ruff format --check src`, `uv run pytest -q tests/sdk tests/adapters/test_mcp.py tests/test_server.py`(443개 통과), `uv run python tools/check_adr_pointers.py`. 나머지 손으로 치는 다섯은 커밋의 pre-commit 결과로 갈음한다.

## PR 직전 리뷰(`coderabbit-review`)

인계받은 세션이 푸시 전에 돌렸다. CLI(0.7.5)는 `review_completed`로 끝까지 돌아 findings 0건이었고(검토 파일 42개, `Seat: not assigned`, Plan Free), 서브에이전트가 비밀을 되울리는 길을 직접 읽고 `uv run python -c`로 재현해 넷을 보고했다.

고친 것(Major 유효 1):

- 매니페스트 `_parse`의 `from error`가 `ValidationError`를 `__cause__`에 남겨, 주소의 사용자 정보(`https://user:<비밀번호>@host/x`)나 환경 변수 이름 칸에 잘못 적은 토큰이 트레이스백 출력에 실린다. 서브에이전트가 재현했고 이 세션도 첫 사례를 `uv run python -c`로 `HttpServer.model_validate`에 쳐 `input_value='https://user:SECRETPW@host/x'` 줄을 봤다. `__cause__` 쪽은 고치기 전의 시험이 빨간 것으로 봤다. ADR 0041이 "매니페스트 `_parse`의 같은 사슬은 이 기능이 고치지 않는다"고 둔 것은 매니페스트에 비밀이 들 칸이 없다는 전제였고, 이 PR의 http 모양이 그 전제를 깼다. `_parse`가 `_parse_skill`처럼 `except`에서 이유 문구만 만들고 `PluginError`는 블록 밖에서 던지게 고쳤다. 시험(`tests/adapters/test_filesystem.py`의 `test_칸에_잘못_적은_비밀은_mcp_매니페스트의_문구에도_예외_사슬에도_남지_않는다`, 두 사례)은 고치기 전에 `__cause__` 단언에서 빨간 것을 봤고 고친 뒤 초록이다(`tests/adapters/test_filesystem.py`·`tests/sdk`·`tests/test_server.py` 541개 통과). `.claude/rules/adapters.md`가 매니페스트 `_parse`는 이 규칙을 따르지 않는다고 적은 문장이 거짓이 되어, 같은 모양으로 원인을 잇지 않는다고 고쳤다. ADR 0041의 문장은 그때의 기록이라 두었다.
- `adapters.md`를 다시 고쳤으나 카나리아는 다시 돌리지 않았다. 그 규칙을 원천으로 든 명세 셋 가운데 `adapters_rule_new_optional_fields`는 JSONL 항목의 문장이 `paths`에 맞는 파일을 Read할 때 실리는지를 보고, 이번에 고친 `read_skill` 항목은 어느 명세도 인용하지 않으며 실리는 장치(`paths`)도 바뀌지 않았다. 나머지 둘의 원천 문장도 다른 항목이다(어림. 둘의 원천 문장을 열어 대 보지는 않았다).

남긴 것과 이유(Minor와 보류):

- [Major 보류] `_where`가 `server.url` 전체(쿼리 문자열과 조각 포함)를 `run_failed` 문구에 싣는다. ADR 0049 Consequences "문구에 실리는 것과 실리지 않는 것"과 2026-11-09 이력 "실패 문구"가 정했고 쿼리를 떼는 안은 사용자가 거부했다. `?token=...`처럼 쿼리에 비밀을 적으면 트레이스에 남는다는 한계는 02의 시험이 고정한다.
- [Minor] `url`이 개행·제어 문자(`urlsplit`이 지워 통과한다)와 앞뒤 공백, 범위 밖 포트를 받는다. 명세가 "그 밖은 판정하지 않는다"고 정했다. 다만 개행이 든 주소가 `_where`를 거쳐 문구와 로그에 줄바꿈째 실리면 로그 위조가 되므로, 02가 주소를 문구에 쓰기 전에 거를지를 본다(아래 "다음").
- [Minor] `_RESERVED_HEADERS`에 `upgrade`·`te`·`trailer`·`keep-alive`·`proxy-authorization`·`cookie`가 없다. 어느 이름이 라이브러리가 정하는 것인지는 02가 접속을 만들며 재어 본다(받았다가 나중에 막으면 매니페스트가 깨지므로 그때 판단한다).
- [Minor] 모르는 `transport` 값이 `union_tag_invalid` 문구에 실린다. 값이 열거형 이름이라 비밀일 가능성은 낮다.

## 결정

사용자에게 물은 것은 없다. 티켓과 명세가 정한 대로 구현했다. 사진 정답 갱신은 티켓이 "바뀌면 까닭을 PR 본문에 적는다"고 정한 갈래다.

## 회고

후보 다섯, 승인 하나, 기각 넷이다. 넘긴 것은 없어 사용자에게 묻지 않았다.

승인(대기열 `canary-notice-spec-paths`, 1회차, 새 항목): `tools/sibling_overlap.py`의 카나리아 알림이 바뀐 규칙을 원천으로 든 명세의 파일 이름만 적고 경로와 돌리는 명령을 주지 않았다. 사건: 이 세션이 명세 다섯의 경로를 찾으려 Glob을 한 번 더 쳤고, 돌리는 법을 보려 `uv run python tools/canary.py --help`를 쳐 독스트링 전체를 읽었다(출력을 직접 보았다). 층: 도구 출력이라 린터·훅 층이고, 되돌림은 PR 하나다. 더하는 것이라 다섯 번째에 반영하고 그 전에는 회차를 센다. 같은 일을 다룬 열린 항목은 `tools/queue_open_rows.py --search` 두 번으로 찾았으나 보이지 않았다. 그 검색은 낱말을 `--search`마다 합쳐 읽는 것으로 보여 맞은 항목이 42개와 141개로 넓었고, 닫힌 항목 가운데 카나리아 `--help`의 크기를 다룬 것은 이 출력만으로 가르지 못했다(어림. 항목 원문을 열어 대 보지 않았다).

기각:

- 사진 비교가 `PluginDetail`의 그림 변화를 잡았다(ADR 0049 본문의 "화면은 바뀌지 않는다"가 거짓이었다). 이미 있는 검사(사진 비교)가 그 자리에서 잡았다.
- ESLint가 `clients.test-d.ts`의 `@ts-expect-error` 줄에서 `any` 전파 오류 5건을 잡았다. 이미 있는 검사가 잡았다.
- 셀프 리뷰가 거짓 주석 둘(검증자가 값을 되울리지 않는다는 문장, 특수 기호 열둘)을 잡았다. 두 축의 브리프가 든 주장 검증 기준을 어긴 것을 리뷰가 잡은 것이라 리뷰가 제 몫을 한 사건이고, 회차를 세지 않는다. 주장의 사실 여부는 검사로 옮길 수 없다.
- 이 회고에서 대기열을 찾는 `--search`를 낱말 여럿으로 넓게 줘 출력이 1만 자와 5.7만 자 넘게 나왔다. 스킬이 이미 전체 경로와 핵심어로 좁히라고 적었고 어긴 것은 이 세션이다.

만료: `tools/queue_open_rows.py`와 `--ref origin/main`(`git fetch origin` 뒤)이 같은 7개(215, 418, 472, 473, 474, 478, 479)를 만료할 항목으로 냈고, 상태 줄 하나씩을 `만료 2026-11-10 (ADR 0036)`으로 고쳤다.

## 다음

다음 단계는 티켓 02 `.scratch/mcp-http/issues/02-connect-to-remote-mcp-server-by-url.md`(주소로 원격 MCP 서버에 접속한다)이고 이 PR이 병합된 뒤에 돈다. 03(`03-session-close-request-from-cancelled-runs.md`)과 04(`04-real-model-calc-over-remote-mcp-server.md`)는 02 뒤에 나란히 돈다.

- 02는 이 PR이 둔 `NotImplementedError("http 전송은 아직 구현되지 않았다")` 갈래를 실제 접속으로 바꾼다. `tests/adapters/test_mcp.py`의 http 갈래 시험 둘과 `tests/core/test_run.py`의 `BrokenTools` 시험을 실제 접속의 시험으로 바꾼다.
- `.claude/rules/adapters.md`·`.claude/rules/core.md`의 stdio 전제 문장(ADR 0049 Consequences "구현 티켓이 함께 고칠 자리")은 02의 몫이다. 이 PR은 틈 동안 거짓이 되는 `[server]` 문장과 연결 실패 문장만 고쳤다.
- 02가 `_where`로 주소를 실패 문구에 싣는 자리를 만질 때 둘을 본다. 하나는 쿼리 문자열의 비밀이 `run_failed` 문구에 남는다는 한계(ADR 0049가 정한 것이니 시험으로 고정한다)이고, 다른 하나는 개행·제어 문자가 든 주소(이 PR의 읽는 단계는 받는다)가 문구에 줄바꿈째 실려 로그가 위조되는 길을 문구에 쓰기 전에 거를지다. 헤더 이름 금지 목록(`_RESERVED_HEADERS`)에 연결 계층 이름(`upgrade`, `te`, `trailer`, `keep-alive`, `proxy-authorization`, `cookie`)을 더할지도 02가 접속을 만들며 정한다. 셋 모두 코드래빗 CLI 뒤 서브에이전트의 수동 점검이 낸 것이다.
- `.scratch/end-user-channel/probes/run_timeout.py`와 `.scratch/mcp-shutdown/probes/`의 `McpServer(` 생성자는 기록이라 고치지 않았다(합이 호출 불가라 지금 실행하면 `TypeError`일 것이다. 명세 축 서브에이전트가 `McpServer(...)`를 불러 `TypeError`를 확인했고, 그 프로브 파일들을 직접 돌려 보지는 않았다).

## 인계

커밋 `cabdbbd4`(브랜치 `feature/01-contract-mcp-server-transport-stdio-or-http`) 뒤, 컨텍스트가 문턱을 넘어 인계한다. 이 세션의 제목은 `feature/01-contract-mcp-server-transport-stdio-or-http`였고 `(인계함)`을 붙여 넘긴다. 낸 지시문은 아래 그대로다.

```
다음 작업: .scratch/mcp-http/issues/01-contract-mcp-server-transport-stdio-or-http.md (mcp 매니페스트의 [server]가 transport로 stdio와 http를 가르는 계약을 세운다)
다음 단계: 구현
어디서: 새 세션. 주 체크아웃 미갱신이라 Skill 도구로 tidy-checkouts를 먼저 돌고(그 스킬이 사람에게 넘기는 것은 보고만 하고 답을 기다리지 않는다) 그 뒤 git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/mcp-http/issues/01-contract-mcp-server-transport-stdio-or-http.md
브랜치: feature/01-contract-mcp-server-transport-stdio-or-http
모델: Sonnet 5.5 / high. 2의 잇는 지시문
읽을 것: docs/journal/2026-11-10-0152-mcp-http-contract.md
이어받을 상태: 인계: 커밋 뒤. 구현, 게이트, 셀프 리뷰 반영, 커밋(cabdbbd4)까지 마쳤고 푸시하지 않았다. 티켓 파일은 이미 done이다. 남은 일은 푸시, /git-pr로 PR 열기, PR 연결(mcp__ccd_pr__get_status 뒤 필요하면 bind_pr), 봇 회차, 병합이고, 구현을 다시 하지 않는다. PR 본문에 적을 것 셋: (1) 사진 정답 네 장(organisms-plugindetail--disabled-{1280,320}-{light,dark}.png)이 바뀐 까닭은 PluginDetail이 매니페스트 전체를 JSON으로 그려 transport 줄이 더해져서이고 ADR 0049 이력 2026-11-10이 정정했다. (2) sync-design-system 확인은 스토리와 시험 픽스처만 바뀌어 건너뛰었다. (3) .scratch/end-user-channel/probes/run_timeout.py와 .scratch/mcp-shutdown/probes/는 McpServer( 생성자를 기록 그대로 둔다. 병합 뒤에는 next-session으로 티켓 02(.scratch/mcp-http/issues/02-connect-to-remote-mcp-server-by-url.md)의 지시문을 낸다. PR 504(pilot-portal-spec)가 먼저 병합됐으면 .scratch/plan.md를 uv run python tools/plan_table.py로 다시 만들어 싣는다
확인할 선행 조건: 주 체크아웃 미갱신: 루트는 main. 병합은 이 워크트리 사본의 next-session merge.md의 "워크트리에서 병합할 때"를 Read로 열어 따른다
이번 요청 범위: PR과 병합까지
```

open-session을 부른다 2026-11-09T17:08:42Z

## 인계 2

PR을 연 뒤(PR 505, 커밋 `6b49601c`까지 푸시), 컨텍스트가 문턱을 넘어 두 번째로 인계한다. 앞 인계의 세션이 푸시 전 `coderabbit-review`를 돌려 Major 하나(`_parse`의 예외 사슬)를 고친 커밋 둘을 더했고, PR 본문은 저장소 템플릿으로 채워 열었다. 이 세션의 제목은 `feature/01-contract-mcp-server-transport-stdio-or-http`였고 `(인계함)`을 붙여 넘긴다. 낸 지시문은 아래 그대로다. PR 505는 이미 이 세션에 연결되어 있고(`get_status`), 검사는 아직 시작 전이었다.

```
다음 작업: .scratch/mcp-http/issues/01-contract-mcp-server-transport-stdio-or-http.md (mcp 매니페스트의 [server]가 transport로 stdio와 http를 가르는 계약. PR 505를 반영하고 병합한다)
다음 단계: PR 반영·병합
어디서: 새 세션. git worktree list에서 그 브랜치가 체크아웃된 자리를 찾아 워크트리면 EnterWorktree(path)로 들어가고 주 체크아웃이면 거기서 잇는다
시작 프롬프트: /implement .scratch/mcp-http/issues/01-contract-mcp-server-transport-stdio-or-http.md
브랜치: feature/01-contract-mcp-server-transport-stdio-or-http
모델: Sonnet 5.5 / high. 2의 잇는 지시문
읽을 것: docs/journal/2026-11-10-0152-mcp-http-contract.md
이어받을 상태: 인계: PR 연 뒤. 일지는 docs/journal/2026-11-10-0152-mcp-http-contract.md 이고 "인계 2"가 이 인계다. PR 505(https://github.com/njh6803/agent-os/pull/505)가 열려 있고 커밋 셋(cabdbbd4, 11a464cc, 6b49601c)이 푸시됐다. 이 일지의 "인계 2" 구간은 커밋하지 않았다(앞 세션이 만든 변경). 남은 일은 merge.md 2(봇 회차)부터이고 구현을 다시 하지 않는다. 첫 @coderabbitai review 코멘트도 새 세션이 남긴다. 병합은 이 워크트리 사본의 next-session merge.md의 "워크트리에서 병합할 때"를 Read로 열어 따른다. PR 504(pilot-portal-spec)와 이 PR이 같은 대기열 항목 일곱(0215, 0418, 0472, 0473, 0474, 0478, 0479)을 만료로 고쳤다. 504가 먼저 병합되면 이 브랜치에 origin/main을 합쳐 글자 충돌을 풀고(같은 줄이면 같은 만료 줄 하나만 남긴다), 504가 .scratch/plan.md도 바꾸므로 합친 뒤 uv run python tools/plan_table.py로 다시 만들어 싣는다. 병합 뒤에는 next-session으로 티켓 02(.scratch/mcp-http/issues/02-connect-to-remote-mcp-server-by-url.md)의 지시문을 낸다. 코드래빗 첫 회차의 Minor·Nit은 지적마다 판단하고, 이 PR의 의도적 한계(쿼리 문자열의 비밀이 문구에 실림, 주소의 제어 문자, 헤더 이름 금지 목록)는 일지의 "PR 직전 리뷰"와 티켓 02의 "01이 넘긴 메모"에 이미 있다.
확인할 선행 조건: 없음
이번 요청 범위: PR과 병합까지
```
open-session을 부른다 2026-11-09T17:41:09Z

## 봇 회차 (인계 2를 받은 세션)

PR 505에 `@coderabbitai review` 코멘트를 남기고 `tools/wait_ci.py`로 기다렸다. 헤드 `6b49601c`의 검사는 전부 초록이었고 CodeRabbit은 `Review rate limited`(다음 리뷰는 4분 뒤)로 리뷰를 내지 않았다. claude-review는 통과였고 인라인 리뷰 코멘트는 없었다. 한도에 걸려 리뷰가 없던 푸시는 회차로 세지 않으므로 CodeRabbit의 첫 회차는 아직 오지 않았다. 이 PR의 보안·버그 축은 푸시 전에 돈 `coderabbit-review`(위 "PR 직전 리뷰")가 대신한다. 이 일지를 푸시하면 CodeRabbit이 다시 돌 수 있어 그 결과를 첫 회차로 받는다.

CodeRabbit의 첫 회차(헤드 `72666f50`)는 지적 여섯 건이었다(Major 셋, Minor 셋). 판정은 이렇다.

고친 것(Major 둘):

- `transport` 칸에 잘못 적은 값이 `union_tag_invalid` 문구(`Input tag '<값>' found using _transport_of() …`)로 관리 API 응답과 로그에 실린다. 앞 세션이 "값이 열거형 이름이라 비밀일 가능성이 낮다"며 보류했으나, 칸에 비밀을 잘못 적을 자리라는 점은 `url`·헤더와 같아 고쳤다. `filesystem._describe`가 이 종류에만 고정 문구(`transport 는 stdio 나 http 여야 한다`)를 쓴다.
- 주소의 대괄호 호스트(`https://[<값>]/x`)에서 `urlsplit`의 `ValueError`가 그 호스트를 문구에 싣는다. `uv run python -c`로 `HttpServer.model_validate`를 쳐 `'PLANTED_SECRET' does not appear to be an IPv4 or IPv6 address`가 문구에 나오는 것을 직접 봤다. 검증자가 예외를 블록 밖으로 잇지 않고 고정 문구(`url 이 주소 모양이 아니다`)로 바꾼다.
- 두 사례를 `tests/adapters/test_filesystem.py`의 비밀 시험에 더했고 고치기 전에 둘 다 빨간 것을 봤다(`transport` 칸은 문구에 값이 실려, 대괄호 호스트는 같은 단언에서). 고친 뒤 `tests/adapters/test_filesystem.py`·`tests/sdk`·`tests/test_server.py` 543개 통과.

보류한 것:

- [Major] `_where`가 `server.url` 전체를 `run_failed` 문구에 싣는다(서버 이름으로 바꾸라는 제안). ADR 0049 Consequences "문구에 실리는 것과 실리지 않는 것"과 이력 2026-11-09 "실패 문구"가 사용자의 결정으로 정한 것이라 이 PR이 바꾸지 않는다. 02가 시험으로 고정한다(위 "다음").
- [Minor] `.scratch/end-user-channel/probes/run_timeout.py`의 `McpServer(...)`를 `StdioServer(...)`로 바꾸라는 제안. 프로브는 그때 측정의 기록이라 고치지 않는다(PR 본문 (3)).
- [Minor] HTTP 매니페스트를 읽어 실제 `McpTools`로 실행하는 통합 시험. 이 PR의 http 갈래는 접속을 하지 않고 `NotImplementedError`로 실패하는 자리표시이고, 02가 그 시험을 실제 접속의 시험으로 바꾼다(티켓 02).
- [Minor] `headers` 스키마에 `additionalProperties: false`. 생성 스키마의 `patternProperties` 모양은 `skills` 칸이 이미 쓰는 것이고, 거부는 모델의 검증이 한다. 생성 스키마를 손으로 바꾸는 장치를 이 계약에 들이지 않는다.
