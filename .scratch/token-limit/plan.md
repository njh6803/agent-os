# token-limit: 한 실행이 쓸 수 있는 토큰 합에 상한을 두고, 넘으면 그 실행을 실패로 끝낸다.
**슬라이스:** 11
**Blocked by:** run-cost

토큰 합 상한(후보 8). core 기본값과 에이전트 매니페스트의 선택 칸이고 넘으면 `run_failed` 원인 `token_limit`이다. 비용 상한은 두지 않는다(ADR 0042 묶음 ②)
