# run-checks-out-of-memory-with-parallel-sessions: 여러 세션의 검증이 겹치면 PC의 메모리가 모자라 pre-commit의 검사가 "out of memory"와 `MemoryError`로 죽고, 메모리가 돌아온 뒤 다시 치면 지나간다

**상태:** 열림
**어디로:** 하네스 chore: `tools/run_checks.py`가 검사를 띄우기 전에 남은 메모리(실제 메모리와 커밋 여유)를 재어, 모자라면 기다리거나 pytest의 일꾼 수를 줄인다. 문턱 값은 검증 한 바퀴가 쓰는 메모리를 먼저 재어 정한다(이 회차의 세션은 재지 않고 10GB 안팎으로 어림했다). 검사를 건너뛰는 길은 넣지 않는다(0309). 느린 한 바퀴를 재는 열린 `docs-only-commit-precommit-slow-again`과 한 chore로 묶을 수 있다
**승인:** 자체 승인 2026-11-21, 0530의 4회차, 일지 2026-11-20-1928-diag-bundle-design.md. 자체 승인 2026-11-21, 5회차(connection-check 브랜치 둘째 세션의 반영 커밋이 메모리 부족으로 죽었고 9분을 기다려도 풀리지 않았다. 메모리를 잡은 것은 이 저장소가 아니라 rag-engine 저장소의 세션 넷이 띄운 pytest 일꾼이었고, 하나는 세 시간 넘게 남아 있었다. 길은 검사 둘을 손으로 차례로 돌린 뒤 `SKIP=pytest,web-verify`로 커밋하는 것이었다), 일지 2026-11-21-0502-connection-check-spec.md. 자체 승인 2026-11-21, 6회차, 일지 2026-11-21-1935-e2e-standalone-token-rate-limit.md. 자체 승인 2026-11-25, 7회차(admin-login 티켓 01 세션의 커밋 시도 첫 둘이 윈도 오류 1455 "페이징 파일이 너무 작습니다", git "malloc failed", vitest 일꾼 종료 코드 `0xC0000409`로 죽었다. 같은 시각 다른 세션들의 pytest 일꾼이 64개였고 남은 메모리는 2GB였다(작업 관리자의 수치가 아니라 이 세션이 프로세스 목록과 메모리를 손으로 봤다). 메모리가 돌아온 뒤에도 시간 시험이 빨개 `SKIP=pytest` 한 번을 사용자가 허락했다), 일지 2026-11-25-1627-admin-login-ticket-01.md. ADR 불필요(고른 길이 러너의 구성을 바꾸면 그때 ADR 0035의 이력에 쌓는다)

만료된 0530(3회차)을 잇는다. 0530은 처방을 정하지 않고 회차를 지켜보다 만료됐다.

4회차는 connection-check의 설계 세션이다. 문서 열네 파일만 든 커밋의 pre-commit에서 `pyright-linux`와 `web-verify`의 `vitest run`이 `FATAL ERROR: Zone Allocation failed - process out of memory`로 죽었고, pytest는 xdist 일꾼 넷이 `MemoryError`와 "페이징 파일이 너무 작습니다"로 죽어 `8 failed, 7951 passed, 8 warnings, 1 error in 1461.34s`로 끝났다. 그때 전체 메모리 31.9GB에 남은 실제 메모리가 1.2GB, 커밋 한도 127.9GB에 남은 것이 9.7GB였고, 검증을 함께 돌린 다른 워크트리가 넷이었다(실패 알림 직후 `Get-CimInstance`로 손으로 봤다). 약 11분 뒤 남은 실제 메모리 5.1GB, 커밋 여유 20.8GB에서 다시 친 한 바퀴는 같은 검사 셋이 모두 지났다.

같은 날 앞 세션(pick-design-interview)도 pytest의 `MemoryError`와 Rolldown의 `out of memory`로 막혔고, 그 회고는 그 사건을 `docs-only-commit-precommit-slow-again`의 16회차에 적었다. 그 사건은 이 항목의 회차에 넣지 않았다. 처방을 고를 때는 그 사건도 함께 본다.

죽은 검증은 임시 폴더를 남긴다. 그 폴더가 스테이지에 섞인 일은 `git-add-all-staged-leftover-judge-tree`가 센다.
