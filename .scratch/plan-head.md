# 전체 계획

규약(기능 하나에 디렉터리 하나, 프론티어, 계약 티켓, 상태 전이)은 `docs/agents/issue-tracker.md`의 전체 계획 절이 원천이다. 순서와 범위의 근거는 `docs/journal/`에 있고, 첫 슬라이스의 범위는 아래 목표 배치 뒤에 있다.

아래 기능 표와 프론티어는 도구가 기능 계획에서 만든다. 기능 계획 `.scratch/<slug>/plan.md`나 이 파일(`.scratch/plan-head.md`)을 고치고 `uv run python tools/plan_table.py`를 돈다. 기능의 상태는 손으로 적지 않고 기능 계획의 `끝` 줄과 티켓의 `Status:`에서 정해진다.

프론티어에 오른 기능이라도 그 기능 계획 본문의 첫 문장이 먼저 끝낼 하네스 일을 적었으면 그 일이 끝난 뒤에 시작한다. 하네스 일은 `**Blocked by:**`에 적을 수 없어 프론티어가 그것을 보이지 못한다. 지금은 release-image가 dev 전환(ADR 0043 Consequences "전환"의 harness 티켓)을 기다린다(ADR 0056 Consequences "dev 전환이 먼저다"). 전환 티켓이 닫힐 때 release-image를 든 이 문장을 걷는다. 전환 티켓은 닫을 때, 같은 전환을 문서 검색 서버 저장소(rag-engine)에 하라고 그 저장소의 세션에 줄 지시문도 사용자에게 낸다(사용자가 청했다, 일지 2026-11-11-1532 "사용자가 정했다"). 지시문에는 그 저장소가 agent-os의 규약 ADR을 따른다고 적고 다른 점만 적는 얇은 ADR 한 장을 두라는 요건을 싣고, 지시문을 낼 때 대기열 `rag-engine-port-by-hand`에 회차를 더한다. 전환 티켓이 닫힌 뒤의 하네스 일은 두 저장소의 공통 파일을 비교하는 점검 도구다(대기열 `rag-engine-harness-drift`. 같은 일지 "인계한 세션에서 사용자가 정했다"). 이 문장들은 그 지시문을 낸 뒤에 함께 걷는다.

## 목표 배치

슬라이스가 끝날 때마다 채워진다. 현재 트리는 `README.md`.

```
src/agent_os/
  main.py                  진입점. run → channel, serve → server. 어댑터를 조립해 넘긴다
  server.py                슬라이스 2. create_app() 하나가 FastAPI 앱을 조립한다. 전역 app은 없다(ADR 0010)
  sdk/  core/  adapters/
  channel/cli/             슬라이스 1
  http/                    슬라이스 2. HTTP 표면의 공용 배관(에러 봉투, 상태 코드 표, 미들웨어, 변환기). 채널과 관리가 쓴다(ADR 0016)
  channel/http/            슬라이스 2. POST /runs, POST /runs/{run_id}/approval. SSE(ADR 0014). 슬라이스 4가 최종 사용자 접두사의 시작, 결정, 구독을 더하고(ADR 0023) end-user-continuation이 이어 가기를 더한다(ADR 0022 이력)
  admin/http/              슬라이스 2. GET 넷과 /health. plugin-toggle 이 첫 쓰기 경로 PUT /plugins/{kind}/{name}/enabled 를 더한다. 승인은 여기가 아니라 채널이다
openapi.json               슬라이스 2. 커밋된 계약. tools/export_openapi.py 가 만들고 테스트가 최신성을 본다
web/                       슬라이스 3부터. pnpm 워크스페이스. 파이썬과 루트 분리
  apps/admin/              Next.js 관리 화면. 브라우저가 토큰을 들고 Next 는 rewrites 중계, 루프백만(ADR 0019)
  apps/widget/             슬라이스 4. 채팅 위젯. React 19 컴포넌트로 Next 16 iframe 페이지와 Vite element 번들을 낸다(ADR 0024)
  packages/api-client/     openapi.json에서 openapi-typescript 로 생성해 커밋한다(ADR 0021). 위젯 클라이언트가 는다
  packages/ui/             슬라이스 4. 디자인 시스템. 디자인 토큰과 atoms·molecules, Storybook. 두 앱이 소스를 import 한다(ADR 0026)
```

첫 슬라이스: `plugins/agents/`의 파이썬 에이전트 하나를 CLI로 실행하면, Anthropic 모델을 호출하고 MCP stdio 서버 하나의 도구를 써서 답을 내며, 실행 전체가 이벤트 스트림으로 나오고 JSONL 트레이스로 남는다. 첫 슬라이스가 끝나기 전에는 만들지 않는 것: 선언적 그래프 정의, 원격·WASM·FaaS 실행, 메모리·RAG, 멀티테넌시, UI, 스케줄러, HTTP 채널, 스킬 로더와 모델 로더(디렉터리와 `kind`만 예약).

## 기능 표
