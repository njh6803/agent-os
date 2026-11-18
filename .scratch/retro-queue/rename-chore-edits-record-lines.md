# rename-chore-edits-record-lines: 이름을 바꾸는 chore가 카나리아 명세의 지난 결과 줄에 이어 적은 줄(그날 모델이 옮긴 글을 적은 기록)의 옛 이름까지 바꿨고, 셀프 리뷰 명세 축이 Major로 잡았다

**상태:** 열림
**어디로:** 검사 후보: 카나리아 명세의 결과 줄(`# 최신 결과:`, `# 그 전 결과:`)과 그 뒤에 이어 적은 줄이 기준 브랜치 판의 글을 앞에 그대로 두고 덧붙이기만 했는지 본다(머리를 `# 최신 결과:`에서 `# 그 전 결과:`로 바꾸는 것은 받는다). `tools/canary.py --shape`는 판 하나만 보므로 기준 판을 함께 보는 자리(예를 들어 `tools/sibling_overlap.py`)다. 검사로 가를 수 없다고 chore가 판정하면 `docs/agents/issue-tracker.md`의 이름 바꾸기 chore 티켓 서식에서 "바꾸지 않는 것"이 `docs/constitution/operations.md` 문서 위치 절을 가리키게 한다. 그 서식에 잔존 확인 한 줄을 더하는 `rename-residual-grep-misses-split-and-underscore-forms`는 덜 바꾼 것을, 이 항목은 더 바꾼 것을 다룬다. 새 검사라 같은 실수의 다섯 번째이거나 손상이 한 번 났을 때 더한다
**승인:** 자체 승인 2026-11-18, 1회차, 일지 2026-11-18-1559-rename-workflow-terms.md. ADR 불필요

(사건: 티켓의 "바꾸지 않는 것"이 카나리아 명세의 `# 최신 결과:` 줄만 들어, 그 뒤에 이어 적은 줄(`.scratch/harness/probes/canary/dev_base_implement.toml` 8행, 2026-11-12에 모델이 옮긴 구절)의 "루트 브랜치"를 바꿨다. `operations.md` 문서 위치 절은 그 줄도 기록으로 든다. 기준 커밋의 글자로 되돌리고, 티켓의 그 항목을 이어 적은 줄과 `# 그 전 결과:` 줄까지 넓혔다)
