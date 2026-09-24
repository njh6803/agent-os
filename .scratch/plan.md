# 전체 계획

기능 하나가 `.scratch/<slug>/`(spec.md + issues/) 하나다. `Blocked by`가 비었거나 전부 done인 기능이 프론티어이고, 프론티어는 병렬로 돌린다. 계약(`sdk/`, `openapi.json`, 헌법)을 바꾸는 티켓은 각 기능의 첫 티켓이며 다른 티켓을 막는다. 순서와 범위의 근거는 헌법 "첫 슬라이스와 비목표"와 `docs/journal/`에 있다.

| 슬라이스 | 기능(slug) | 내용 | Blocked by | Status |
|---|---|---|---|---|
| 1 | first-slice | CLI로 에이전트 하나 실행. Anthropic 호출, MCP stdio 도구 하나, 이벤트 스트림, JSONL 트레이스. 원칙 I 기한 2026-09-22. 첫 티켓은 계약과 의존성: `pyproject.toml`을 tech.md에 맞추고(지금은 anthropic·mcp·pydantic) sdk에 `schema_version`·`principal`·`mcp`·`model`을 넣는다 | 없음 | done |
| 2 | http-channel | `channel/http`의 `POST /runs`와 `POST /runs/{run_id}/approval`. 응답은 SSE 이벤트 스트림이고 실행은 연결에 묶이지 않는다(ADR 0014). 채널 전용 토큰, 주체는 `serve`의 OS 사용자(ADR 0015). 첫 티켓은 계약: 공유 층 `agent_os.http`로 배관 이동과 원칙 IV 개정(ADR 0016), core의 `PluginError` 하위 타입, 에러 어휘 다섯(ADR 0010 이력), fastapi 하한. 설계는 일지 2026-09-24-03 | first-slice | todo |
| 2 | admin-api | `admin/http` 읽기 전용 GET 넷(`/plugins`, `/plugins/{kind}/{name}`, `/traces`, `/traces/{run_id}`)과 `/health`. `server.py`를 처음 만든다. `openapi.json` 내보내기. 멈춘 실행 목록이 여기로 왔다(interrupts spec의 Out of Scope). 설계는 ADR 0010·0011·0012, 씨앗: 일지 09-20 "슬라이스 2 씨앗"과 "슬라이스 2(백엔드)가 미리 갖춰야 할 것" | first-slice | done |
| 2 | interrupts | 사람 승인 인터럽트. 승인 대상 도구를 에이전트 매니페스트에 선언하고, 멈춘 실행은 트레이스를 재생해 CLI로 재개한다(ADR 0009). 체크포인터라는 별도 부품은 두지 않는다. 첫 티켓은 계약: 이벤트 넷(`RunPaused`, `ApprovalGranted`, `ApprovalDenied`, `RunResumed`)과 두꺼워진 `LlmCalled`·`ToolCalled`, 트레이스 형식 2, 매니페스트 필드 둘 | first-slice | done |
| 2 | plugin-toggle | 플러그인을 켜고 끈다. PRD의 운영자가 "켜고 끄고" 싶다는 그것. 매니페스트 계약 변경(ADR 0008 이력)과 런타임이 꺼진 플러그인을 거부하는 것까지 번지므로 admin-api에서 떼어 냈다 | admin-api | todo |
| 3 | web-admin | `web/` 워크스페이스, `apps/admin`(Next.js, 아토믹 디자인), `packages/api-client`. 씨앗과 재검토 항목: 일지 09-20 "rules/frontend 14개 분석". 승인 버튼을 둔다면 내용은 관리 API로 보고 결정은 채널의 `/runs/{run_id}/approval`로 내는 두 토큰 배치다. 읽기 전용 대시보드로 둘지는 운영자의 선택이다(ADR 0015) | admin-api | todo |
| 4 | web-widget | `apps/widget` 채팅 위젯. 기술은 실측으로 결정. 위젯 설정(어떤 에이전트를 붙이나 등)은 소비자가 여기 있으므로 여기서 정한다. http-channel이 넘긴 것: 최종 사용자 인증(공유 비밀이 아닌 것, 주체의 출처가 바뀐다), CORS, 끊긴 스트림 재접속(구독 경로와 SSE `id`), 원격 바인딩(ADR 0011·0014·0015) | http-channel, web-admin | todo |

프론티어: first-slice 가 2026-09-21 에 닫혔다(PR #16~#23). interrupts 가 2026-09-22 에 닫혔다(PR #29~#37). admin-api 가 2026-09-24 에 닫혔다(티켓 01~06, PR #42 부터). 지금은 http-channel, plugin-toggle, web-admin 셋이 열려 있다.

## 목표 배치

슬라이스가 끝날 때마다 채워진다. 현재 트리는 `README.md`.

```
src/agent_os/
  main.py                  진입점. run → channel, serve → server. 어댑터를 조립해 넘긴다
  server.py                슬라이스 2. create_app() 하나가 FastAPI 앱을 조립한다. 전역 app은 없다(ADR 0010)
  sdk/  core/  adapters/
  channel/cli/             슬라이스 1
  http/                    슬라이스 2. HTTP 표면의 공용 배관(에러 봉투, 상태 코드 표, 미들웨어, 변환기). 채널과 관리가 쓴다(ADR 0016)
  channel/http/            슬라이스 2. POST /runs, POST /runs/{run_id}/approval. SSE(ADR 0014)
  admin/http/              슬라이스 2. 읽기 전용 GET 넷과 /health. 승인은 여기가 아니라 채널이다
openapi.json               슬라이스 2. 커밋된 계약. tools/export_openapi.py 가 만들고 테스트가 최신성을 본다
web/                       슬라이스 3부터. pnpm 워크스페이스. 파이썬과 루트 분리
  apps/admin/              Next.js 관리 화면
  apps/widget/             슬라이스 4. 채팅 위젯. 기술은 그때 결정
  packages/api-client/     openapi.json에서 생성
```

첫 슬라이스: `plugins/agents/`의 파이썬 에이전트 하나를 CLI로 실행하면, Anthropic 모델을 호출하고 MCP stdio 서버 하나의 도구를 써서 답을 내며, 실행 전체가 이벤트 스트림으로 나오고 JSONL 트레이스로 남는다. 첫 슬라이스가 끝나기 전에는 만들지 않는 것: 선언적 그래프 정의, 원격·WASM·FaaS 실행, 메모리·RAG, 멀티테넌시, UI, 스케줄러, HTTP 채널, 스킬 로더와 모델 로더(디렉터리와 `kind`만 예약).
