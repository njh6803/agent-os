# orphan-recovery: 서버가 죽거나 멈춰 결말 없이 남은 고아 실행을 임대 만료로 찾아내 worker가 실패로 닫는다.
**슬라이스:** 11
**Blocked by:** retention-worker

고아 실행 회수(후보 20). 트레이스 저장소의 임대(쥔 인스턴스와 만료 시각, 도는 동안 갱신)로 도는 실행을 가리고, 임대가 지난 결말 없는 실행에 worker가 `run_failed` 원인 `interrupted`를 쓴다. 임대 길이·갱신 주기·인스턴스 식별은 설계 인터뷰가 정한다(ADR 0042 묶음 ②)
