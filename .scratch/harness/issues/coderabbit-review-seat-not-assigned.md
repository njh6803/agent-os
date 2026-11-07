# coderabbit-review-seat-not-assigned: `Seat: not assigned`만 보고 리뷰를 돌리지 않고 끝내는 1단계를 고친다

**What to build:** `.claude/agents/coderabbit-review.md` 1단계는 `coderabbit auth status`에 `Seat: not assigned`가 보이면 CLI 축이 비어 있다고 보고하고 종료하라고 적는다. 그런데 같은 `Seat: not assigned`(`Plan: Free`, CLI 0.7.5)에서 `coderabbit review --agent --committed --base origin/main`을 직접 치면 종료 코드 0으로 끝나고 출력의 `complete` 줄이 `review_completed`·`findings: 0`·검토한 파일 19개였다(대기열 0578에 적힌 손으로 본 관찰). 다른 PR에서는 파일 616개가 한도 150을 넘어 `Too many files`로 거절됐고, `--dir tools`(파일 15개)로 좁히자 `findings: 0`으로 끝났다(일지 2026-11-07-02). 서브에이전트가 브리프로 "종료하지 말고 돌려서 판정하라"를 받고도 정의 1단계를 따라 리뷰를 돌리지 않고 끝낸 일이 여섯 번째로 되풀이됐다. 이 티켓은 두 가지를 고친다.

- 정의 1단계: `Seat: not assigned`여도 종료하지 않고 3단계로 가서, 리뷰가 실제로 findings를 내는지로 판정한다. 보고에는 `Seat:` 줄을 그대로 적는다. 3단계에는 파일이 150개를 넘어 `Too many files`로 거절될 때 `--dir`로 나눠 돌린다는 문장을 더한다.
- `docs/constitution/operations.md` 리뷰 파이프라인 2의 좌석 서술: `Seat: not assigned`를 CLI 축이 비었다는 증상으로 읽게 하는 문장을, 좌석 줄은 보고에 옮기는 값이고 판정은 `coderabbit review`의 실제 결과라는 문장으로 맞춘다. `Seat: not assigned`를 grep해 두 곳 이상을 함께 본다(대기열 0570의 "좌석 없이 비어 있다"는 이 서술을 옮긴 사건이다).

**대기열:** 578

**Status:** done

## 수용 기준

- [x] `coderabbit-review` 정의 1단계가 `Seat: not assigned`에서 종료하지 않고 3단계로 가며, 보고에 `Seat:` 줄을 그대로 적게 한다
- [x] 같은 정의의 3단계가 `Too many files` 거절에 `--dir`로 나눠 돌리는 길을 든다
- [x] `operations.md` 리뷰 파이프라인 2의 좌석 서술이 `Seat: not assigned`를 CLI 축이 빈 증거로 적지 않으며, 같은 서술을 옮긴 살아 있는 문서(PR 템플릿, `KICKOFF.md`, `kickoff/pitfalls.md`, `kickoff/facts.md`, `bug-perf-review` 정의, `tools/hook_security_review_journal.py` 독스트링)도 같이 맞췄다. 대기열 0570은 사람이 좌석을 배정하는 몫이라 열어 두고 본문에 새 사실을 덧붙였다
- [x] 카나리아 `.scratch/harness/probes/canary/coderabbit_review_seat_not_assigned.toml`이 1단계의 새 문장을 묻고 통과한다(결과는 그 명세의 `# 최신 결과:` 줄)
- [x] 회고 반영: 대기열 578의 고침, 일지 2026-11-07-02-retro-queue-one-file-per-item.md
- [x] 검증 명령이 모두 초록이다
