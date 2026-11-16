# queue-item-approval-line-conflicts: 나란히 도는 두 PR이 같은 대기열 항목에 회차를 더하면 승인 줄 한 줄에서 글자 충돌이 나고 회차 번호가 겹친다

**상태:** 열림
**어디로:** 하네스 chore: 항목 파일이 회차의 서술을 승인 줄 한 줄에 쌓지 않게 한다. 후보는 둘이다. 회차마다 한 줄로 본문에 적고 번호를 적지 않는 꼴(수는 `tools/queue_open_rows.py`가 센다), 또는 대기열 폴더에 양쪽이 더한 줄을 모두 받는 병합 방식을 거는 꼴이다. 어느 쪽이든 `.scratch/retro-queue/README.md`의 파일 모양과 `tools/queue_open_rows.py`의 읽기를 함께 고친다
**승인:** 자체 승인 2026-11-16, 0236의 2회차, 일지 2026-11-16-1705-portal-admin-spec.md. ADR 필요 여부는 그 chore가 정한다(항목 파일의 모양은 ADR 0045가 정했다)

`open-session-send-denied-despite-allow-rule`에 PR 594와 PR 595가 저마다 회차를 더해 승인 줄에서 충돌했다. PR 595는 그 충돌 하나 때문에 기준 브랜치를 한 번 더 합쳤고(pre-commit 한 바퀴와 봇 회차 한 번), 회차 번호를 두 번 다시 매겼다. 0236은 표 하나였던 대기열을 항목마다 파일로 나눠 닫혔고, 같은 꼴이 항목 안의 한 줄에 남았다. 줄 하나에 덧붙이다 충돌한 다른 사례는 닫힌 0532(`.scratch/plan.md`)다.
