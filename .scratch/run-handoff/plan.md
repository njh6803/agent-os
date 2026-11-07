# run-handoff: 앞 에이전트가 끝나며 다음 에이전트를 지목하면 런타임이 이어서 곧바로 시작한다.
**슬라이스:** 13
**Blocked by:** otel-export

실행 경계 넘김(후보 4). 앞 에이전트가 `run_finished`에 `next_agent`·`handoff_note`를 내면 런타임이 같은 주체의 이어 가기로 다음 실행을 바로 시작하고, 채널의 한 스트림이 넘김 고리를 이어 보낸다. 검사 넷에 걸리면 둘째 실행이 `run_failed` 원인 `handoff`로 끝난다(ADR 0042 묶음 ④)
