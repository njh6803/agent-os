<!-- 이 파일은 도구가 만든다. 기능 계획(`.scratch/<slug>/plan.md`)이나 `.scratch/plan-head.md`를 고치고 `uv run python tools/plan_table.py`를 돌린다. -->
# 전체 계획

규약(기능 하나에 디렉터리 하나, 프론티어, 계약 티켓, 상태 전이)은 `docs/agents/issue-tracker.md`의 전체 계획 절이 원천이다. 순서와 범위의 근거는 `docs/journal/`에 있고, 첫 슬라이스의 범위는 아래 목표 배치 뒤에 있다.

아래 기능 표와 프론티어는 도구가 기능 계획에서 만든다. 기능 계획 `.scratch/<slug>/plan.md`나 이 파일(`.scratch/plan-head.md`)을 고치고 `uv run python tools/plan_table.py`를 돈다. 기능의 상태는 손으로 적지 않고 기능 계획의 `끝` 줄과 티켓의 `Status:`에서 정해진다.

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

| 슬라이스 | 기능 | 내용 | Blocked by | Status |
|---|---|---|---|---|
| 1 | [first-slice](first-slice/plan.md) | CLI로 에이전트 하나를 실행하면 모델을 부르고 도구를 써서 답하며, 실행 전체가 이벤트로 남는다. | 없음 | done |
| 2 | [admin-api](admin-api/plan.md) | 관리 서버가 서고, 플러그인 목록과 지난 실행의 기록(트레이스)을 읽기 전용으로 볼 수 있다. | first-slice | done |
| 2 | [http-channel](http-channel/plan.md) | 운영자가 HTTP로 실행을 시작하고 승인하며, 응답은 실시간 이벤트 스트림으로 받는다. | first-slice | done |
| 2 | [interrupts](interrupts/plan.md) | 위험한 도구를 쓰기 전에 실행이 멈추고, 사람이 승인하면 멈춘 자리에서 이어 간다. | first-slice | done |
| 2 | [plugin-toggle](plugin-toggle/plan.md) | 운영자가 플러그인을 켜고 끌 수 있고, 꺼진 플러그인을 부른 실행은 시작 전에 막힌다. | admin-api | done |
| 3 | [admin-style](admin-style/plan.md) | 관리 화면에 디자인 시스템을 들여 모든 화면을 새 스타일과 반응형으로 다시 그린다. | design-system, design-refresh, design-artifacts | done |
| 3 | [web-admin](web-admin/plan.md) | 웹 관리 화면의 뼈대를 세워, 플러그인 보기와 켜고 끄기, 실행 보기, 승인을 화면에서 할 수 있게 한다. | admin-api, http-channel, plugin-toggle | done |
| 4 | [conversation](conversation/plan.md) | 끝난 실행을 이어 가며 대화를 나눌 수 있고, 대화가 길어지면 런타임이 앞부분을 요약한다. | http-channel, web-admin | done |
| 4 | [design-artifacts](design-artifacts/plan.md) | 디자인 시스템과 화면을 곧 닫히는 Claude Design에서 Claude 아티팩트로 옮겨 둔다. | design-refresh | done |
| 4 | [design-card-build](design-card-build/plan.md) | 디자인 시스템 아티팩트의 컴포넌트 카드를 저장소의 짓기 명령으로 직접 만들게 한다. | design-reverse-sync | done |
| 4 | [design-refresh](design-refresh/plan.md) | 디자인 시스템의 색과 글꼴과 밀도를 관리 화면에 어울리도록 다시 탐색해 골라 코드에 옮긴다. | design-system | done |
| 4 | [design-reverse-sync](design-reverse-sync/plan.md) | 사람이 웹에서 고친 디자인 시스템을 검사를 거쳐 저장소의 코드로 다시 들이는 길을 만든다. | design-artifacts | done |
| 4 | [design-system](design-system/plan.md) | 위젯과 관리 화면이 함께 쓰는 디자인 토큰과 기본 컴포넌트, 화면 사진 비교 검사를 만든다. | web-admin | done |
| 4 | [end-user-channel](end-user-channel/plan.md) | 사이트가 서명한 토큰을 가진 최종 사용자가 실행을 시작하고 결과를 받는 별도 경로를 연다. | http-channel, web-admin | done |
| 4 | [end-user-continuation](end-user-continuation/plan.md) | 최종 사용자 경로에서도 앞 대화를 이어 가고, 긴 대화의 비용과 실패 원인을 다룬다. | conversation, end-user-channel | done |
| 4 | [mcp-shutdown](mcp-shutdown/plan.md) | 실행이 취소되거나 서버가 내려갈 때 MCP 서버 프로세스와 그 자식까지 함께 내려가게 한다. | end-user-channel | done |
| 4 | [web-widget](web-widget/plan.md) | 다른 사이트에 붙이는 채팅 위젯을 만들어, 질문하고 답과 도구 호출과 승인을 대화 안에서 본다. | conversation, end-user-channel, end-user-continuation, design-system, design-refresh, design-artifacts | done |
| 5 | [model-plugin](model-plugin/plan.md) | 모델을 플러그인으로 읽어, 에이전트가 고른 모델 설정을 서버를 다시 띄우지 않고 쓴다. | 없음 | done |
| 6 | [skill-plugin](skill-plugin/plan.md) | 스킬을 플러그인으로 읽어, 에이전트가 고른 스킬의 이름과 설명과 본문을 받아 쓴다. | 없음 | done |
| 7 | [approval-rules](approval-rules/plan.md) | 운영자가 승인 규칙 파일로 도구 호출을 거부하거나 승인을 요구하거나 허용하게 정한다. | skill-plugin | done |
| 7 | [local-model](local-model/plan.md) | 바깥 API를 쓸 수 없는 환경에서도 OpenAI 호환 모델 서버로 에이전트를 돌릴 수 있게 한다. | 없음 | todo |
| 7 | [mcp-http](mcp-http/plan.md) | 원격 MCP 서버에 주소로 접속해, 실행마다 서버를 새로 띄우는 시작 비용을 없앤다. | 없음 | done |
| 7 | [pilot-portal](pilot-portal/plan.md) | 위젯을 담는 질문 페이지가 로그인 없이 온 사람에게 사이트 토큰을 내, 위젯을 붙일 사이트가 없는 공개 데모와 배포 환경을 돕는다. | 없음 | in-progress |
| 8 | [answer-eval](answer-eval/plan.md) | 고정 질문으로 에이전트를 돌려 검색 적중과 출처 적중을 재고 평가 보고서를 낸다. | doc-qa-agent, rag-engine:release-image | todo |
| 8 | [doc-qa-agent](doc-qa-agent/plan.md) | 문서 검색 서버를 불러 근거를 찾고 출처를 달아 답하는 참조 질의응답 에이전트를 준다. | mcp-http, approval-rules | todo |
| 8 | [public-demo](public-demo/plan.md) | 공개 정부 문서를 넣은 클라우드 VM 한 대를 공개 주소에 열어, 누구나 로그인 없이 묻고 출처가 붙은 답을 받게 한다. | doc-qa-agent, release-image, answer-eval, rag-engine:release-image, rag-engine:search-eval | todo |
| 8 | [release-image](release-image/plan.md) | 판마다 서버와 관리 화면과 위젯과 질문 페이지의 컨테이너 이미지를 짓고 올리며 단독 배포 안내도 낸다. | pilot-portal | todo |
| 9 | [deploy-package](deploy-package/plan.md) | agent-os와 문서 검색 서버를 Docker Compose로 한 번에 띄우는 참조 배포를 준다. | local-model, portal-login, doc-qa-agent, release-image, ops-backup-upgrade, diag-bundle, mcp-http, rag-engine:release-image, rag-engine:admin, rag-engine:backup-upgrade, rag-engine:diag-bundle | todo |
| 9 | [diag-bundle](diag-bundle/plan.md) | 문제를 살필 때 판과 구성과 최근 실패 원인을 비밀 값 없이 파일 하나로 묶는 명령을 준다. | release-image, mcp-http | todo |
| 9 | [ops-backup-upgrade](ops-backup-upgrade/plan.md) | agent-os 데이터를 백업하고 새 서버에 복원하며, 판을 올린 뒤에도 옛 트레이스를 읽게 한다. | release-image | todo |
| 9 | [pilot-release](pilot-release/plan.md) | public-demo를 뺀 기준선의 기능이 모두 끝나면 제품 0.1 판을 내고 지원 범위와 고지를 문서로 남긴다. | answer-eval, deploy-package | todo |
| 9 | [portal-login](portal-login/plan.md) | 질문 페이지에 사내 로그인 모드를 더해, 배포 환경에서는 사내 사람만 질문하게 한다. | pilot-portal | todo |
| 10 | [audit-export](audit-export/plan.md) | 운영자가 트레이스를 주체와 기간과 에이전트와 도구별로 조회하고 파일로 내보낸다. | io-guardrail | todo |
| 10 | [io-guardrail](io-guardrail/plan.md) | 최종 사용자의 입력과 에이전트의 출력에서 주민등록번호 같은 패턴을 규칙으로 막거나 가린다. | value-masking | todo |
| 10 | [mcp-trust](mcp-trust/plan.md) | MCP 서버마다 믿는 정도와 도구 정의 해시를 정해, 믿지 않는 서버의 결과를 바깥 글로 다룬다. | approval-rules, pilot-release, mcp-http | todo |
| 10 | [portal-admin](portal-admin/plan.md) | 질문 페이지 설정을 화면에서 고치는 관리 화면을 질문 페이지 쪽에 두어, 운영자가 파일을 열지 않고 사이트마다의 위젯 설정을 바꾼다. | pilot-portal | todo |
| 10 | [principal-propagation](principal-propagation/plan.md) | 운영자가 켠 MCP 서버에만 실행의 주체를 넘겨, 사용자가 볼 수 있는 문서로만 답하게 한다. | mcp-trust | todo |
| 10 | [run-feedback](run-feedback/plan.md) | 최종 사용자가 틀린 답을 신고하고, 운영자가 신고된 실행을 관리 화면에서 볼 수 있게 한다. | pilot-release | todo |
| 10 | [stale-warning](stale-warning/plan.md) | 검색 결과의 근거 문서가 오래됐다고 표시돼 있으면 답에 경고를 붙여, 낡은 근거로 답했음을 알린다. | pilot-release, rag-engine:doc-freshness | todo |
| 10 | [usage-report](usage-report/plan.md) | 기간별 질문 수와 사용자 수와 오류 신고 비율을 이용 보고로 내보내 운영 상황을 한눈에 알게 한다. | audit-export, run-feedback | todo |
| 10 | [value-masking](value-masking/plan.md) | 런타임이 아는 비밀 값을 트레이스에 쓰기 직전에 모든 글 칸에서 찾아 가려, 기록에 새지 않게 한다. | principal-propagation | todo |
| 10 | [widget-appearance](widget-appearance/plan.md) | 레이아웃과 아이콘 같은 새 모양 칸을 위젯의 임베드 속성과 질문 페이지 설정에 더해, 사이트마다 위젯의 생김새를 더 넓게 고른다. | pilot-portal | todo |
| 11 | [orphan-recovery](orphan-recovery/plan.md) | 서버가 죽거나 멈춰 결말 없이 남은 고아 실행을 임대 만료로 찾아내 worker가 실패로 닫는다. | retention-worker | todo |
| 11 | [retention-worker](retention-worker/plan.md) | 별도 worker 명령이 승인 만료 닫기와 보존 기간이 지난 기록 지우기를 주기로 돌린다. | token-limit | todo |
| 11 | [run-cost](run-cost/plan.md) | 모델과 도구 호출에 걸린 시간을 남기고, 모델 단가로 실행 비용을 읽을 때 셈한다. | trace-postgres | todo |
| 11 | [token-limit](token-limit/plan.md) | 한 실행이 쓸 수 있는 토큰 합에 상한을 두고, 넘으면 그 실행을 실패로 끝낸다. | run-cost | todo |
| 11 | [trace-postgres](trace-postgres/plan.md) | 트레이스 저장소를 파일에서 PostgreSQL로 바꾸고, 같은 실행에 동시에 쓰는 일을 안전하게 막는다. | usage-report, stale-warning | todo |
| 12 | [claude-code-compat](claude-code-compat/plan.md) | Claude Code용 스킬과 서브에이전트와 MCP 설정을 올리면 우리 플러그인 형식으로 바꿔 설치한다. | declarative-agent | todo |
| 12 | [declarative-agent](declarative-agent/plan.md) | 코드 없이 설정 파일과 프롬프트 문서만으로 에이전트를 만들 수 있게 해, 운영자도 에이전트를 더하게 한다. | orphan-recovery | todo |
| 12 | [otel-export](otel-export/plan.md) | 실행의 트레이스를 OpenTelemetry 표준으로 내보내 Langfuse 같은 도구에서 볼 수 있게 한다. | claude-code-compat | todo |
| 13 | [delegation](delegation/plan.md) | 리드 에이전트가 다른 에이전트에게 일을 맡기고, 맡긴 기록이 리드의 트레이스에 남는다. | run-handoff | todo |
| 13 | [replay-evaluation](replay-evaluation/plan.md) | 지난 실행을 바뀐 에이전트나 모델로 다시 돌려 결과를 견주고 사람이 판정을 적는다. | delegation | todo |
| 13 | [run-handoff](run-handoff/plan.md) | 앞 에이전트가 끝나며 다음 에이전트를 지목하면 런타임이 이어서 곧바로 시작한다. | otel-export | todo |
| 14 | [admin-crud](admin-crud/plan.md) | 관리 화면에서 플러그인의 매니페스트와 본문 파일을 직접 만들고 고치고 지우며, 잘못된 내용은 거절한다. | replay-evaluation | todo |
| 14 | [multi-instance](multi-instance/plan.md) | 서버 인스턴스를 여럿 띄워도 동시 실행 상한과 실시간 구독이 하나의 서버처럼 동작하게 한다. | admin-crud | todo |

## 프론티어

done 이 아니고, Blocked by 가 비었거나 이 저장소의 막는 기능이 모두 done 인 기능이다. `local-model`, `pilot-portal`, `doc-qa-agent`

## 다른 저장소를 기다리는 기능

Blocked by 에 `rag-engine:<slug>` 가 들고 이 저장소의 막는 기능은 모두 done 인 기능이다. 그 기능이 끝났는지는 문서 검색 서버 저장소를 보고 확인한다(ADR 0048). (없음)
