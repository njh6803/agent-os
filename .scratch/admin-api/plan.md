# admin-api: 관리 서버가 서고, 플러그인 목록과 지난 실행의 기록(트레이스)을 읽기 전용으로 볼 수 있다.
**슬라이스:** 2
**Blocked by:** first-slice
**끝:** 2026-09-24

`admin/http` 읽기 전용 GET 넷(`/plugins`, `/plugins/{kind}/{name}`, `/traces`, `/traces/{run_id}`)과 `/health`. `server.py`를 처음 만든다. `openapi.json` 내보내기. 멈춘 실행 목록이 여기로 왔다(interrupts spec의 Out of Scope). 설계는 ADR 0010·0011·0012, 씨앗: 일지 09-20 "슬라이스 2 씨앗"과 "슬라이스 2(백엔드)가 미리 갖춰야 할 것"
