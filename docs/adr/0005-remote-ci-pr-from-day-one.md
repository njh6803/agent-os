---
status: accepted
date: 2026-09-20
---

# 원격, CI, PR은 첫날부터다

헌법 1.x는 "원격 없음, 혼자면 PR 없음, ff 병합"이었다. 2026-09-20 헌법 2.1.0에서 "원격(GitHub), CI, PR은 첫날부터. 혼자여도 같은 리듬. 팀원이 생기면 리뷰 승인 필수와 CODEOWNERS를 더한다"로 바꿨다. 이유 셋. 선행 저장소 둘(`ai-agent-platform`, `agent-runtime-platform`)이 가드레일을 나중에 붙이다 LLM 호출 0줄에서 멈췄다. 사용자의 git-pr·git-pr-merge 스킬이 이미 PR 단위 흐름이라 맞추는 비용이 0이다. 훅은 각자 설치해야 하므로 CI가 최종 판정이어야 한다.

같은 날 실측한 제약이 이 결정의 모양을 정했다. 무료 플랜의 비공개 저장소는 보호 브랜치를 못 켜므로 병합 게이트를 GitHub가 아니라 병합 스킬에 두기로 했다. 규약과 되돌릴 조건은 `docs/constitution/operations.md`의 가드레일 절.

## Consequences

- 티켓마다 `feature/<NN>-<slug>` 브랜치, 혼자여도 PR, squash 병합, main 이력은 PR 단위. 규약은 `docs/constitution/operations.md`의 "브랜치와 병합"과 "가드레일".
- 원격 생성과 시크릿 등록은 사람이 한다. 에이전트는 토큰을 다루지 않고 `gh secret list`로 이름만 본다.
- 하네스 변경 하나가 PR 하나가 되어 첫날 PR 열 개가 나왔다. 그 비용은 회고 후보 5(결정 하나가 파일 열 개)로 관찰 중이다.
- Actions는 계정 결제 상태에 묶인다. 2026-09-20 PR #10에서 "recent account payments have failed or your spending limit needs to be increased"로 잡이 시작조차 안 됐다. CI가 최종 판정인 구조는 결제가 막히면 병합도 막힌다는 뜻이다. 런북 1단계의 플랜 확인에 결제 상태도 포함한다.
