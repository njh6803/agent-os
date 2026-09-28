# 전체 계획

규약(기능 하나에 디렉터리 하나, 프론티어, 계약 티켓, 상태 전이)은 `docs/agents/issue-tracker.md`의 전체 계획 절이 원천이다. 순서와 범위의 근거는 `docs/journal/`에 있고, 첫 슬라이스의 범위는 이 파일 끝에 있다.

| 슬라이스 | 기능(slug) | 내용 | Blocked by | Status |
|---|---|---|---|---|
| 1 | first-slice | CLI로 에이전트 하나 실행. Anthropic 호출, MCP stdio 도구 하나, 이벤트 스트림, JSONL 트레이스. 원칙 I 기한 2026-09-22. 첫 티켓은 계약과 의존성: `pyproject.toml`을 tech.md에 맞추고(지금은 anthropic·mcp·pydantic) sdk에 `schema_version`·`principal`·`mcp`·`model`을 넣는다 | 없음 | done |
| 2 | http-channel | `channel/http`의 `POST /runs`와 `POST /runs/{run_id}/approval`. 응답은 SSE 이벤트 스트림이고 실행은 연결에 묶이지 않는다(ADR 0014). 채널 전용 토큰, 주체는 `serve`의 OS 사용자(ADR 0015). 첫 티켓은 계약: 공유 층 `agent_os.http`로 배관 이동과 원칙 IV 개정(ADR 0016), core의 `PluginError` 하위 타입, 에러 어휘 다섯(ADR 0010 이력), fastapi 하한. 설계는 일지 2026-09-24-03 | first-slice | done |
| 2 | admin-api | `admin/http` 읽기 전용 GET 넷(`/plugins`, `/plugins/{kind}/{name}`, `/traces`, `/traces/{run_id}`)과 `/health`. `server.py`를 처음 만든다. `openapi.json` 내보내기. 멈춘 실행 목록이 여기로 왔다(interrupts spec의 Out of Scope). 설계는 ADR 0010·0011·0012, 씨앗: 일지 09-20 "슬라이스 2 씨앗"과 "슬라이스 2(백엔드)가 미리 갖춰야 할 것" | first-slice | done |
| 2 | interrupts | 사람 승인 인터럽트. 승인 대상 도구를 에이전트 매니페스트에 선언하고, 멈춘 실행은 트레이스를 재생해 CLI로 재개한다(ADR 0009). 체크포인터라는 별도 부품은 두지 않는다. 첫 티켓은 계약: 이벤트 넷(`RunPaused`, `ApprovalGranted`, `ApprovalDenied`, `RunResumed`)과 두꺼워진 `LlmCalled`·`ToolCalled`, 트레이스 형식 2, 매니페스트 필드 둘 | first-slice | done |
| 2 | plugin-toggle | 플러그인을 켜고 끈다. PRD의 운영자가 "켜고 끄고" 싶다는 그것이다. 켜짐은 매니페스트가 아니라 플러그인 루트의 `disabled.toml`이 들고, 매니페스트와 sdk는 바뀌지 않는다(ADR 0017). 관리의 첫 쓰기 경로 `PUT /plugins/{kind}/{name}/enabled`(204)와, `/plugins`의 감싼 행 `{kind, name, enabled}` + `manifest`·`reason`(ADR 0010 이력). `PluginSource`에 메서드 둘(ADR 0012 이력). 꺼진 것을 부른 새 실행과 재개는 core의 `Disabled`이고 409다(ADR 0017). 재개 쪽과 하위 타입 기준의 개정은 ADR 0014 이력에 있다. 첫 티켓은 계약: `openapi.json`의 `/plugins` 응답과 새 경로, `POST /runs`의 409, 포트, `Disabled`. 설계는 일지 2026-09-26-06 | admin-api | done |
| 3 | web-admin | `web/` pnpm 워크스페이스, `apps/admin`(Next 16, 아토믹 디자인), `packages/api-client`(openapi-typescript로 `openapi.json`에서 생성해 커밋). 범위는 읽기, 켜고 끄기, 승인이다. 승인은 운영자가 채널 토큰을 넣었을 때만 보이고 마지막 티켓이다. 브라우저가 두 토큰을 sessionStorage에 들고, Next는 `rewrites`(`compress: false`) 중계이며 루프백에만 선다(ADR 0019, ADR 0011의 2026-09-28 이력). 파이썬 서버와 계약 파일은 바뀌지 않는다(ADR 0010의 2026-09-28 이력). 스택은 ADR 0021. 원칙 III을 TypeScript로 넓힌다(ADR 0020, 헌법 3.0.0). 첫 티켓은 헌법과 하네스다. 원칙 III 개정, `tech.md`의 웹·프론트 구성 행, `CLAUDE.md`의 검증 명령 다섯과 레이어, `.claude/rules/web-*.md`, pre-commit이 든다. 검증 명령을 "넷"으로 세는 살아 있는 문장도 함께 고친다. 2026-09-28 기준으로 `CLAUDE.md`의 게이트 줄과 작업 규약 3, `operations.md` 머리와 가드레일, `README.md` 원천 표, `code-review` 스킬 6단계, `tools/export_openapi.py`와 `tests/tools/test_export_openapi.py`의 독스트링이다. 티켓 때 `검사 넷`, `명령 넷`, `넷은 그중` 셋으로 다시 grep한다. 지난 사건을 적은 문장(`tools/check_type_escapes.py`, `tests/sdk/test_ids.py`)은 그대로 참이다. CI 워크플로 변경은 별도 PR로 먼저 병합한다(`operations.md`). 명세가 정할 열린 물음이 하나 있다. 결정을 멈춘 도구 호출에 묶을지(어긋나면 409)다. 묶으면 계약 변경이라 첫 티켓이 하고 ADR 0014의 이력에 쌓는다(ADR 0019). 설계는 일지 2026-09-28-06, 측정은 `.scratch/web-admin/probes/` | admin-api, http-channel, plugin-toggle | todo |
| 4 | web-widget | `apps/widget` 채팅 위젯. 기술은 실측으로 결정. 위젯 설정(어떤 에이전트를 붙이나 등)은 소비자가 여기 있으므로 여기서 정한다. http-channel이 넘긴 것: 최종 사용자 인증(공유 비밀이 아닌 것, 주체의 출처가 바뀐다), CORS, 끊긴 스트림 재접속(구독 경로와 SSE `id`), 원격 바인딩(ADR 0011·0014·0015). 에러 문구의 노출: 실행 전 실패의 500 봉투 `message`(`PluginError` 원문)와 `run_failed`의 `error`가 서버 경로와 예외 원문을 싣는다. 지금은 루프백과 채널 토큰 뒤라 그대로 두었다(PR #68 CodeRabbit CWE-209, 보류). 원격·브라우저 소비자 앞에 서기 전에 둘을 함께 다시 본다. plugin-toggle이 넘긴 것: 꺼진 에이전트를 부른 요청은 409 `conflict`이고 메시지가 그 이름을 든다. 최종 사용자 앞에서 존재를 숨길지(404)는 에러 노출과 함께 다시 본다(ADR 0017). web-admin이 넘긴 것은 다섯이다. (1) 관리 화면의 배치(브라우저가 운영자 토큰을 든다)는 위젯에 물려받지 않는다(ADR 0019). (2) Next는 인자 없이 띄우면 `0.0.0.0`과 `[::]`에 서고, `rewrites`는 기본 압축 때문에 SSE를 끝에 몰아 준다(ADR 0019). (3) 쿠키를 들이면 Next의 Server Actions CSRF 검사가 Host와 Origin이 같은 DNS rebinding 모양을 통과시킨다는 측정이 걸린다(`.scratch/web-admin/probes/next_measure.mjs`). (4) Storybook과 공유 atoms(`packages/ui`)는 여기서 다시 본다(ADR 0021). (5) SSE 항목의 타입은 생성되지 않으므로 손으로 파싱하고 판별자 술어로 좁힌다(ADR 0010의 2026-09-28 이력) | http-channel, web-admin | todo |

프론티어: first-slice 가 2026-09-21 에 닫혔다(PR #16~#23). interrupts 가 2026-09-22 에 닫혔다(PR #29~#37). admin-api 가 2026-09-24 에 닫혔다(티켓 01~06, PR #42 부터). http-channel 이 2026-09-26 에 닫혔다(티켓 01~05, PR #70 부터). plugin-toggle 이 2026-09-28 에 닫혔다(티켓 01~02, PR #85 부터). 지금 열린 것은 web-admin 하나다. web-admin 은 http-channel 이 닫히며 풀렸었다가(생성기를 고르는 측정이 채널 라우트가 붙은 계약 파일을 요구했다) 2026-09-26 plugin-toggle 설계에서 `/plugins` 의 응답 모양이 바뀌기로 해서 다시 막혔고, plugin-toggle 이 닫히며 다시 풀렸다. web-admin 의 설계 인터뷰는 2026-09-28 에 끝났다(일지 2026-09-28-06, ADR 0019~0021).

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
  admin/http/              슬라이스 2. GET 넷과 /health. plugin-toggle 이 첫 쓰기 경로 PUT /plugins/{kind}/{name}/enabled 를 더한다. 승인은 여기가 아니라 채널이다
openapi.json               슬라이스 2. 커밋된 계약. tools/export_openapi.py 가 만들고 테스트가 최신성을 본다
web/                       슬라이스 3부터. pnpm 워크스페이스. 파이썬과 루트 분리
  apps/admin/              Next.js 관리 화면. 브라우저가 토큰을 들고 Next 는 rewrites 중계, 루프백만(ADR 0019)
  apps/widget/             슬라이스 4. 채팅 위젯. 기술은 그때 결정
  packages/api-client/     openapi.json에서 openapi-typescript 로 생성해 커밋한다(ADR 0021)
```

첫 슬라이스: `plugins/agents/`의 파이썬 에이전트 하나를 CLI로 실행하면, Anthropic 모델을 호출하고 MCP stdio 서버 하나의 도구를 써서 답을 내며, 실행 전체가 이벤트 스트림으로 나오고 JSONL 트레이스로 남는다. 첫 슬라이스가 끝나기 전에는 만들지 않는 것: 선언적 그래프 정의, 원격·WASM·FaaS 실행, 메모리·RAG, 멀티테넌시, UI, 스케줄러, HTTP 채널, 스킬 로더와 모델 로더(디렉터리와 `kind`만 예약).
