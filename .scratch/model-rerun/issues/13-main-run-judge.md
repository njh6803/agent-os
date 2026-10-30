# 13: 본 측정 실행과 판정 — 병합된 main 에서 다시 풀기 본 측정을 끝까지 돌리고 판정해 기록한다

**What to build:** 티켓 12(`.scratch/model-rerun/issues/12-main-run.md`)가 시험을 고정해 병합한 main(06845c68)에서, 티켓 11 이 고정한 사전 등록대로 본 측정(과제 8개, 다섯 갈래, 상한 $1,600)을 돌고 `rerun_judge`로 판정한다. 결과는 회차 기록(`.scratch/model-rerun/probes/records/`), 일지, `docs/model-selection.md`에 적는다. 칸을 바꿀 판정이면 ADR 0029 이력 초안을 써서 사람의 승인을 받는다.

티켓 12 의 "본 측정" 항목을 잇는다. 그 항목은 PR 이 병합된 뒤에야 할 수 있어, PR 을 열 때 티켓이 done 이기를 요구하는 CI 커밋 검사(`tools/check_ticket.py`, ADR 0037)에 맞게 결과를 싣는 이 PR 의 티켓으로 넘겼다. 같은 디렉터리의 다음 번호다(`docs/agents/issue-tracker.md`).

**Blocked by:** 없음(12 는 done)

**Status:** done

### 본 측정

- [x] 선행 조건: 사람이 계정을 njh6803 으로 정했고 주간 한도가 넉넉하다고 답했다. 전용 설정 폴더 `C:\Users\User\.claude-rerun`의 로그인이 njh6803 이다(일지 `docs/journal/2026-10-29-10-main-run.md`). 사전 등록 절이 든 njh4803 과 다른 점은 그 일지에 벗어남으로 적었다
- [x] 병합된 main 의 판에서 러너를 백그라운드로 띄우고 끝 알림을 기다린다. 러너가 첫 회차 전에 사전 등록 절의 해시를 대 본다
- [x] 끝나면 판정(`rerun_judge`)을 돌려 결과를 일지와 `docs/model-selection.md`에 적는다. 결론 없음(S_A 2, T 7). 출력은 `.scratch/model-rerun/probes/judge-main.md`
- [x] ADR 0029 이력 초안을 써서 보이고 승인을 받는다. 이력 2026-10-20 이 칸을 두라고 해도 이력을 쌓으라고 정했다. 2026-10-31 승인. 사용자가 결과를 본 뒤 구현 칸을 Sonnet 5.5 / high로 내리고 막히면 한 단계씩 올리기로 정했다. 칸을 고치는 일은 chore/030 병합 뒤 별도 chore 티켓이 한다
