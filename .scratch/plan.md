# 전체 계획

기능 하나가 `.scratch/<slug>/`(spec.md + issues/) 하나다. `Blocked by`가 비었거나 전부 done인 기능이 프론티어이고, 프론티어는 병렬로 돌린다. 계약(`sdk/`, `openapi.json`, 헌법)을 바꾸는 티켓은 각 기능의 첫 티켓이며 다른 티켓을 막는다. 순서와 범위의 근거는 헌법 "첫 슬라이스와 비목표"와 `docs/journal/`에 있다.

| 슬라이스 | 기능(slug) | 내용 | Blocked by | Status |
|---|---|---|---|---|
| 1 | first-slice | CLI로 에이전트 하나 실행. Anthropic 호출, MCP stdio 도구 하나, 이벤트 스트림, JSONL 트레이스. 원칙 I 기한 2026-09-22 | 없음 | todo |
| 2 | http-channel | `server.py`, `channel/http` `/runs`, 스트리밍 | first-slice | todo |
| 2 | admin-api | `admin/http` `/plugins`, `/traces`, 위젯 설정. `openapi.json` 내보내기. 씨앗: 일지 09-20 "슬라이스 2 씨앗"과 "슬라이스 2(백엔드)가 미리 갖춰야 할 것" | first-slice | todo |
| 2 | interrupts | 사람 승인 인터럽트, 체크포인터(`thread_id = run_id`), `RunPaused` 이벤트 | first-slice | todo |
| 3 | web-admin | `web/` 워크스페이스, `apps/admin`(Next.js, 아토믹 디자인), `packages/api-client`. 씨앗과 재검토 항목: 일지 09-20 "rules/frontend 14개 분석" | admin-api | todo |
| 4 | web-widget | `apps/widget` 채팅 위젯. 기술은 실측으로 결정 | http-channel, web-admin | todo |

프론티어: 지금은 first-slice 하나. 끝나면 http-channel, admin-api, interrupts 셋이 동시에 열린다.
