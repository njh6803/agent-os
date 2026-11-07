# retention-worker: 별도 worker 명령이 승인 만료 닫기와 보존 기간이 지난 기록 지우기를 주기로 돌린다.
**슬라이스:** 11
**Blocked by:** token-limit

보존 기간·승인 만료·worker(후보 12). 별도 명령 `agent-os worker`가 주기 작업(승인 만료 닫기, 보존 기간 지우기, 고아 실행 회수)을 돌린다. 승인 만료는 재개 시점 판정에 더해 worker가 `run_failed` 원인 `approval_expired`를 쓴다. 설정의 원천은 PostgreSQL의 운영 설정 표 하나이고 관리 API GET·PUT으로 바꾼다. ADR 0009의 만료 없음을 뒤집는다(ADR 0042 묶음 ②)
