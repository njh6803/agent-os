# 043: `plan.md`의 skill-plugin 행을 done으로 고치고 프론티어 문단에 닫힘을 적는다

**What to build:** skill-plugin의 티켓 다섯이 모두 병합됐다(01 PR #462, 02 PR #461, 03 PR #463, 05 PR #464, 04 PR #465. `.scratch/skill-plugin/issues/`의 `Status:` 줄이 다섯 모두 `done`). 그런데 `.scratch/plan.md`의 슬라이스 6 행은 상태 칸이 `in-progress`이고 설명이 "03이 이어 돈다"에서 멈췄으며, 프론티어 문단(44번 줄)의 끝도 "04와 05가 03을 기다린다"다. 다른 닫힌 기능(model-plugin 등)처럼 행의 상태 칸을 `done`으로 바꾸고 행의 설명 끝에 03·05·04의 병합과 닫힘을 적으며, 프론티어 문단 끝에 닫힘 문장을 더해 skill-plugin을 기다리던 approval-rules(슬라이스 7)가 풀렸음을 적는다. 슬라이스 7 행의 내용과 막는 칸은 그대로 둔다. 코드와 시험은 건드리지 않는다.

**대기열:** 없음

**Status:** done

## 수용 기준

- [x] `.scratch/plan.md`의 슬라이스 6(skill-plugin) 행의 상태 칸이 `done`이고, 행 설명의 끝이 03(PR #463)·05(PR #464)·04(PR #465)의 병합과 기능의 닫힘으로 끝난다(옛 "03이 이어 돈다"가 남지 않는다)
- [x] 프론티어 문단 끝이 skill-plugin의 닫힘(날짜, 티켓 01~05, PR #461 부터, 마지막 티켓 04, 일지 2026-11-05-03)과 approval-rules가 풀려 프론티어가 그 하나임을 적는다. 옛 "04와 05가 03을 기다린다"가 남지 않는다
- [x] 저장소의 살아 있는 문서에서 skill-plugin이 진행 중이라거나 03·04·05를 기다린다는 옛 표현이 0이다(grep. 이 티켓이 옛 문장을 인용한 곳과 일지·ADR 이력 같은 기록은 뺀다)
- [x] 검증 명령이 모두 초록이다(문서만 바꿨다. `plan.md`를 읽는 시험 172개, `check_md_tables.py`, `check_instructions.py`를 손으로 쳤고 나머지 손으로 치는 명령은 커밋의 pre-commit 결과로 갈음한다)
