# interrupts: 위험한 도구를 쓰기 전에 실행이 멈추고, 사람이 승인하면 멈춘 자리에서 이어 간다.
**슬라이스:** 2
**Blocked by:** first-slice
**끝:** 2026-09-22

사람 승인 인터럽트. 승인 대상 도구를 에이전트 매니페스트에 선언하고, 멈춘 실행은 트레이스를 재생해 CLI로 재개한다(ADR 0009). 체크포인터라는 별도 부품은 두지 않는다. 첫 티켓은 계약: 이벤트 넷(`RunPaused`, `ApprovalGranted`, `ApprovalDenied`, `RunResumed`)과 두꺼워진 `LlmCalled`·`ToolCalled`, 트레이스 형식 2, 매니페스트 필드 둘
