# trace-postgres: 트레이스 저장소를 파일에서 PostgreSQL로 바꾸고, 같은 실행에 동시에 쓰는 일을 안전하게 막는다.
**슬라이스:** 11
**Blocked by:** usage-report, stale-warning

트레이스 저장소 교체(후보 18). PostgreSQL 어댑터 하나로 바꾸고 JSONL 어댑터와 그 테스트를 지운다. CLI run·테스트·개발도 DB를 쓴다. 포트의 `write`에 기대 자리를 더한 조건부 이어쓰기와 실행 식별자 키의 Redis 분산 잠금(재개와 주기 작업 앞)을 들인다. 테스트는 testcontainers로 PostgreSQL·Redis를 스스로 띄우고 없으면 실패한다. 이 행이 PostgreSQL과 Redis를 더하고 retention-worker가 worker를 더해, agent-os 배포의 프로세스가 넷(serve, worker, PostgreSQL, Redis)이 된다. 그 전의 판(기준선과 제품 1.0)은 `serve` 한 프로세스와 파일 트레이스다(PRD 전제, ADR 0042 묶음 ②와 그 2026-11-06 이력). ADR 0046과 ADR 0048이 넘긴 것: audit-export가 트레이스 저장소 포트의 읽기로 지은 조회가 이 어댑터에서도 돌아야 하고, agent-os의 데이터베이스는 연결 문자열 하나만 받으며 다른 서비스의 데이터베이스를 읽지 않는다. ops-backup-upgrade가 지은 백업에 이 데이터베이스를 더한다
