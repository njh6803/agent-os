# cross-repo-directive-before-merge: **다른 저장소(rag-engine)의 세션에 줄 지시문을 이 PR이 병합되기 전에 사용자에게 내면서 언제 주라는 말을 붙이지 않아, 사용자가 "rag-engine 저장소에 지금 지시해?"라고 되물었다**(지시문은 agent-os의 `origin/dev`에서 `tools/protection-dev.json` 등을 읽으라고 했는데, 그 파일은 이 PR이 병합되기 전의 `origin/dev`에 없었다)

**상태:** 열림
**어디로:** 대상 미정, 회차 감시. 5회차에 문장 하나를 더할 자리를 고른다(후보는 `rag-engine-port-by-hand` 본문의 "회차는 … 지시문을 사용자에게 낼 때 더한다" 곁과 `.scratch/release-image/plan.md`의 판 내기 지시문 대목이다. 더할 것은 지시문이 이 PR의 파일을 가리키면 병합 뒤에 주라고 함께 알린다는 문장이다)
**승인:** 자체 승인 2026-11-12, 1회차, 일지 2026-11-12-1148-dev-branch-create.md. ADR 불필요

`external-ref-moved-while-citing`과 방향이 반대다. 그것은 이 저장소가 다른 저장소의 병합 전 브랜치를 근거로 든 것이고, 이것은 다른 저장소에 이 저장소의 병합 전 파일을 읽으라고 한 것이다.
