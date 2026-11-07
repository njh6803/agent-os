# declarative-agent: 코드 없이 설정 파일과 프롬프트 문서만으로 에이전트를 만들 수 있게 해, 운영자도 에이전트를 더하게 한다.
**슬라이스:** 12
**Blocked by:** orphan-recovery

선언형 에이전트(후보 1). `plugins/agents/<이름>/`에 entrypoint 없는 `plugin.toml`과 `AGENT.md`(YAML 머리말 + 프롬프트)를 두고, 몸통은 sdk의 공개 클래스이며 로더가 entrypoint 없는 에이전트에 그것을 쓴다. 매니페스트 판정과 로더가 바뀌는 sdk 계약 변경이다(ADR 0042 묶음 ③)
