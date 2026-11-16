# mutation-table-checked-late: **변이 표를 지을 때 `expect_output`을 정하지 않고 지나가, 표지 없는 빨강 열일곱이 한 바퀴(약 20분)를 돈 커밋 시도의 끝에서야 `mutate.py --staged`에 막혔다**(`.claude/rules/probes.md` 첫 항목. 0350이 닫힌 뒤의 첫 사건이다. 검사는 제 몫을 했고 걸린 때가 늦었다)

**상태:** 열림
**어디로:** 대상 미정, 회차 감시. 검사(`tools/mutate.py --check`·`--staged`)가 이미 알리고, pre-commit이 훅을 하나씩 모두 돌아 `check-mutations`를 앞으로 옮겨도 한 바퀴는 줄지 않는다(`.pre-commit-config.yaml`에 `fail_fast`가 없다). 그래서 처방은 표를 짓는 때 `--check`를 먼저 돌리게 하는 지침 한 줄(`.claude/rules/probes.md`의 첫 항목 끝)이고, 더하는 것이라 5회차에 반영한다
**승인:** 자체 승인 2026-11-13, 1회차, 일지 2026-11-13-1423-llm-local-command-rents-model-servers.md. ADR 불필요

(0350은 표지 없는 새 변이를 알리는 검사를 들이며 닫혔다. 이 항목은 그 검사가 있는 채로 같은 실수가 다시 난 것을 센다. 표지 고르기의 질 문제(풀이 줄, 호출 한 토막)는 0579가 센다)
