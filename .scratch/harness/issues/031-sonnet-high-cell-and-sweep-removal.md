# 031: 구현·하네스 칸을 Sonnet 5.5 / high로 내리고 레벨 스윕을 걷는다

**What to build:** ADR 0029 이력 2026-10-31 "다시 풀기 1차는 결론 없음이고 레벨 스윕을 멈추며 사용자가 구현과 하네스 칸을 Sonnet 5.5 / high로 내려 막히면 한 단계씩 올린다"의 "함께 고치는 것"을 한다. `next-session` 결정표의 구현 두 줄과 하네스 티켓을 여는 줄(하네스 chore 배치 줄, "같은 주제가 남았다" 줄을 새 세션으로 열 때)의 "모델" 칸을 `Sonnet 5.5 / high`로 바꾼다. 막혔다고 넘기는 세션은 다음 세션의 모델을 사다리 `Sonnet 5.5 / high` → `Opus 5.5 / medium` → `Opus 5.5 / high` → `Opus 5.5 / xhigh`에서 한 단계 올리고, 컨텍스트가 차서 넘기는 보통의 인계와 끊기는 잇는 지시문의 규칙(다음 단계의 값, 구현이면 같은 모델)으로 잇는다. 그 규칙은 `directive.md` 2 한 곳에 두고 끊는 줄과 `handoff.md` 인계 줄이 가리킨다. 레벨 스윕을 걷는다. `tools/model_sweep.py`와 `tools/model_sweep_judge.py`와 그 시험, `next-session`이 그 도구를 부르는 자리와 스윕 갈래 표지, `directive.md` 2의 임시 다섯 문장, 아침 보고의 스윕 조각, 스윕만 확인하던 카나리아와 판정 변이 표, 결정표·`docs/model-selection.md`·`README.md`의 스윕 문장이다. `rerun_judge.py`가 가져다 쓰던 `percentile_ci`는 그 파일로 옮긴다. 스윕 프로브(`sweep.py`와 사전 등록 README)는 ADR이 인용하는 기록이라 남기고, 지운 도구를 import하므로 지우기 전 커밋 `f01ce1e9`에서 돈다고 적는다. PR #439의 봇이 보류한 지적(`sweep.py judge`의 조기 중단 표지, `directive.md` 2의 자기 참조 모양과 "다섯 문장" 수)은 그 도구와 문장째 지워 닫는다.

**대기열:** 없음

**Status:** done

## 수용 기준

- [x] 결정표의 구현 두 줄, 하네스 chore 배치 줄, "같은 주제가 남았다" 줄(새 세션)의 칸이 `Sonnet 5.5 / high`이고 `tests/tools/test_open_session.py`의 결정표 테스트가 초록이다
- [x] 막혔다고 넘길 때의 올리기 사다리와 보통의 인계·끊기가 같은 모델로 잇는 규칙이 `directive.md` 2에 있고, 끊는 줄과 `handoff.md` 인계 줄이 그것을 가리킨다
- [x] `tools/model_sweep.py`, `tools/model_sweep_judge.py`, 그 시험, 스윕 카나리아, 판정 변이 표가 없고, 스윕 프로브가 `f01ce1e9`에서 돈다고 적었으며, 아침 보고가 스윕 없이 돈다
- [x] 살아 있는 문서와 하네스에서 `model_sweep`·`레벨 스윕의 갈래`·`스윕 밖`을 grep한 줄이 모두 기록(일지, ADR, 닫힌 티켓과 명세, 프로브 기록, 대기열의 닫힌 행, 지난 지시문을 옮긴 시험 입력)이거나 지운 도구를 지웠다고 적는 문장이다
- [x] 바꾼 `next-session`을 새 세션(카나리아)에서 불러 확인했다
- [x] 검증 명령이 모두 초록이다
