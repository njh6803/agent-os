# probe-readme-result-cells: **프로브 README의 변이 표·탐침 행이 결과 서사를 한 칸에 쌓아 수천 자가 되어, 나란히 도는 PR 둘이 이웃한 행을 고치면 한 덩어리로 병합 충돌이 난다**

**상태:** 열림
**어디로:** `.scratch/harness/probes/README.md`의 변이 표·탐침 행 결과 칸을 각 변이 표 머리 주석(`# 최신 결과:`)과 탐침 독스트링으로 옮기고 행 길이를 막는 저장소 상태 시험을 더한다(0196과 같은 갈래이고 같은 파일이다)
**승인:** 자체 승인 2026-11-07, 0196의 4회차, 일지 2026-11-07-1047-journal-names-by-time.md. ADR 불필요

사건: retro-queue-per-item 티켓 04가 티켓 03(#484)을 합치는 자리에서 `.scratch/harness/probes/README.md`의 `sibling_overlap_mutations.toml`(이 브랜치만 고침), `journal_cite_scan.py`(이 브랜치만 고침), `review_workflow.py`(티켓 03만 고침) 세 행이 이웃해 한 덩어리로 충돌했다. 행마다 수천 자라 사람이 눈으로 풀 수 없었고, 기준 커밋과 줄 단위로 대는 스크래치 스크립트로 풀었다. 0196이 카나리아 행에서 같은 원인(결과 서사를 한 칸에 쌓음)을 고쳤으나 변이 표와 탐침 행에는 그 고침이 닿지 않았다.
