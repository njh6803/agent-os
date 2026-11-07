# http-channel: 운영자가 HTTP로 실행을 시작하고 승인하며, 응답은 실시간 이벤트 스트림으로 받는다.
**슬라이스:** 2
**Blocked by:** first-slice
**끝:** 2026-09-26

`channel/http`의 `POST /runs`와 `POST /runs/{run_id}/approval`. 응답은 SSE 이벤트 스트림이고 실행은 연결에 묶이지 않는다(ADR 0014). 채널 전용 토큰, 주체는 `serve`의 OS 사용자(ADR 0015). 첫 티켓은 계약: 공유 층 `agent_os.http`로 배관 이동과 원칙 IV 개정(ADR 0016), core의 `PluginError` 하위 타입, 에러 어휘 다섯(ADR 0010 이력), fastapi 하한. 설계는 일지 2026-09-24-03
