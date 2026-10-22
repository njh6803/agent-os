# 005: 훅 보고가 사용자 프롬프트 훅의 알림을 그 훅의 알림으로 센다

**What to build:** `tools/hook_report.py`는 알림을 명령이 든 `hook_success` 첨부로만 센다. 그런데 UserPromptSubmit 훅(`hook_prompt_directive`)의 알림은 세션 기록에 명령 없는 `hook_additional_context` 첨부로만 남고 `hook_success`가 없어, 첫 턴마다 알린 그 훅을 "창 안에서 알리지도 막지도 않았다"며 뺄 후보로 냈다. 명령 없는 `hook_additional_context`를 막음의 `UNKNOWN` 판정처럼 등록 훅 파일의 문자열 조각과 견주어 그 훅의 알림으로 세고, 같은 첨부 꼴로 남는 다른 이벤트도 세션 기록에서 찾아 함께 본다. 독스트링의 판정과 못 보는 것을 고치고 그 입력을 시험으로 고정한다.

**대기열:** 404

**Status:** done

## 수용 기준

- [x] 명령 없는 `hook_additional_context` 첨부가 등록 훅 파일의 조각과 맞으면 그 훅의 알림으로 세고, 이 PC의 기록으로 돌린 보고에서 `hook_prompt_directive`가 뺄 후보에서 빠진다
- [x] 같은 알림이 `hook_success`와 `hook_additional_context`로 함께 남는 이벤트에서 한 번만 센다
- [x] 명령 없는 첨부 가운데 어느 훅인지 가르지 못한 것은 버리지 않고 따로 센다
- [x] 모듈 독스트링의 판정과 못 보는 것이 새 판정과 맞고, 새로 적은 항목마다 시험이 하나씩 있다. 시험을 먼저 써서 빨간 것을 본다
- [x] 검증 명령이 모두 초록이다

## Comments

- 셀프 리뷰가 짝 없는 첨부를 이벤트를 가리지 않고 모든 훅의 조각과 견주면 앱의 글이 훅의 알림으로 잡힌다고 짚어, 조각으로 가르는 것을 UserPromptSubmit 의 첨부와 그 이벤트에 등록된 훅으로 좁혔다. 같은 반영에서 ADR 0036 에 이력을 더했다(사용자 승인, 일지 2026-10-23-19).
