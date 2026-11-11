# harness-work-invisible-in-plan: 하네스 일(ADR 0043의 dev 전환)이 전체 계획에 보이지 않아, 여는 계기 없이 2026-11-04부터 2026-11-11까지 남았고 그 일이 release-image를 막는 것도 프론티어에 드러나지 않았다

**상태:** 열림
**어디로:** `tools/plan_table.py`: 기능 계획의 `**Blocked by:**`가 하네스 티켓을 가리키는 꼴(`harness:<slug>`)을 받아, 그 티켓이 done이 아니면 그 기능을 프론티어에서 빼고 막는 일을 표에 보인다. `docs/agents/issue-tracker.md`의 전체 계획 절을 함께 고친다. 새 검사라 문턱은 다섯 번째 반복이고 그 전에는 회차를 센다
**승인:** 자체 승인 2026-11-11, 1회차, 일지 2026-11-11-1532-release-image-design-round3.md. ADR 불필요(반영하는 chore가 전체 계획의 표기를 넓히는 일이 ADR 0045의 이력에 닿는지 다시 본다)

사용자가 설계 인터뷰에서 "dev 브랜치는 왜 안만들었어?"라고 물었다. 전환은 ADR 0043이 harness 티켓에 넘겼고, 그 티켓을 여는 줄이 `next-session` 결정표에 없었다. 같은 인터뷰가 dev 전환을 release-image보다 먼저 하기로 정했는데, 도구가 `**Blocked by:**`의 기능이 아닌 항목을 거부해 조건을 본문 문장으로만 적었고 셀프 리뷰 두 축이 Major로 냈다. 이번에는 `.scratch/plan-head.md`의 문단과 기능 계획의 첫 문장으로 드러냈다.
