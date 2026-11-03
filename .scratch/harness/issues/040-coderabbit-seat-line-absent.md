# 040: `coderabbit auth status`에 `Seat:` 줄이 없어도 CLI 리뷰가 돌면 CLI 축이다

**What to build:** `docs/constitution/operations.md` 리뷰 파이프라인 2는 유료 전환 전까지 PR 직전 CLI 축이 구조적으로 비어 있다고 적고 대체 둘(`/security-review`, `bug-perf-review`)이 그 자리를 맡는다고 했다. `.claude/agents/coderabbit-review.md` 1단계는 `auth status`의 `Seat:` 줄을 보고에 옮기고 `not assigned`면 종료하라고만 적어, 그 줄이 없는 출력에서는 어디로 가야 하는지가 없었다. 2026-11-03의 두 PR(harness 039, `docs/skill-plugin-design`)에서 CLI 0.7.5의 `auth status`는 `Plan`·`Seat` 줄 없이 `Review access`만 보였고 `coderabbit review`가 실제로 돌았다(앞은 `No findings`, 뒤는 findings 2. 손으로 봤다). 대기열 557이 다음 PR에서도 같으면 고친다고 둔 조건이 찼다. 두 문서를 실제 판정 길(PR마다 `auth status`를 보고 리뷰를 돌려 findings를 내면 CLI 축, 돌지 못하면 대체 둘)로 고친다. 정의의 고침은 이 세션의 실제 실행(서브에이전트가 `Seat:` 줄 없이 리뷰를 돌려 지적 둘을 냈고, 본 세션이 그 길을 브리프로 미리 일러 주어야 했다)으로 확인했고 다시 돌리지 않았다. 재실행은 시간당 3회의 한도를 하나 더 쓴다. 같은 커밋에 워크트리 가드가 새로 거부한 모양 둘을 `operations.md` 환경 규약 상세의 기록 줄에 더한다.

**대기열:** 557

**Status:** done

## 수용 기준

- [x] `operations.md` 리뷰 파이프라인 2가 CLI 축을 구조적으로 비어 있다고 하지 않고 PR마다의 실제 판정 길로 적으며, 같은 말을 옮긴 자리가 저장소의 살아 있는 문서에 없다(`구조적으로 비어`로 grep)
- [x] `coderabbit-review` 정의 1단계가 `Seat:` 줄이 없는 갈래를 들고, 그 갈래에서 종료하지 않고 리뷰로 간다
- [x] 회고 반영: 557의 고침, 일지 2026-11-03-02-skill-plugin-design.md
- [x] 카나리아 `.scratch/harness/probes/canary/coderabbit_review_seat_line_absent.toml`이 1단계의 새 갈래를 묻고 통과 4다(결과는 그 명세의 `# 최신 결과:` 줄)
- [x] 검증 명령이 모두 초록이다
