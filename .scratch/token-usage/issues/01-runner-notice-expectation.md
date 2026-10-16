# 01: 훅 러너가 사람에게만 보이는 알림을 기대 값으로 받는다

**What to build:** 커밋마다 pre-commit이 돌리는 훅 러너(`tools/run_hooks.py`)의 실제 입력 표(`tools/hook_payloads.toml`)에, 사람에게만 보이는 `systemMessage` 하나를 내는 사례를 기대 값 `notice`로 적을 수 있다. 러너는 그 사례를 다른 기대처럼 판정하고, 발동·침묵의 빈자리를 셀 때 `notice`를 발동으로 센다. 그래서 턴 끝에 사람에게 알리는 훅(05의 `hook_handoff_notice`)과 세션 시작에 요약을 보이는 훅(04의 `hook_session_usage`)이 표에 발동 사례를 둘 수 있다. 지금 러너의 기대는 deny·block·context·silent 넷이고, `notice`는 래퍼가 없는 훅을 지나갈 때의 판정으로만 쓰인다. 그래서 그런 훅을 등록하면 "발동 사례가 없다"는 빈자리로 모든 커밋이 막힌다.

새 훅 둘보다 앞선 사전 정비다. 이 티켓은 훅을 더하지 않는다.

근거는 `.scratch/token-usage/spec.md`의 "이음매"(훅 항목)와 Testing Decisions의 훅 항목이다. 명세 검토의 막는 지적(B1)에서 왔고, 사용자가 인계 훅을 둘로 나누기를 골랐다(일지 2026-10-16-34).

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] 표의 사례가 `expect = "notice"`를 받는다. 지금은 표를 읽는 단계(`Case`의 `Expectation`)에서 거절되므로, 시험은 판정 함수(`outcome_of`, 이미 `notice`를 낸다)만이 아니라 표를 읽고 대조하는 길로 돌린다. 가짜 훅과 `expect = "notice"` 사례 하나를 둔 표에서, 훅이 `systemMessage` 하나만 내면 맞고, `additionalContext`까지 내면 `context`, 아무것도 내지 않으면 `silent`로 어긋난다. 세 갈래를 `tests/tools/test_run_hooks.py`에 고정하고, 고치기 전에 첫 갈래가 빨간 것을 본다
- [ ] 빈자리 셈이 `notice`를 발동으로 센다. `notice` 사례와 `silent` 사례가 있는 훅은 빈자리가 아니고, `notice` 사례만 있는 훅은 "침묵 사례가 없다"다. 시험으로 고정한다
- [ ] `notice` 사례에도 `contains`(훅이 낸 문장에 들어야 하는 조각)를 둘 수 있고, 그 문장이 `systemMessage`에서 나온다. 침묵 사례에 `contains`를 둘 수 없다는 검사는 그대로다
- [ ] 래퍼가 없는 훅을 지나갈 때의 판정(`run_notices`, `NOTICE_ONLY_EVENTS`)은 바뀌지 않는다. 기존 시험이 초록이다
- [ ] 러너 독스트링의 "기대는 넷"과, `outcome_of` 독스트링이 `notice`를 "표의 훅은 내지 않는다"고 적은 문장, `notice_outcome` 독스트링의 "표의 훅은 `systemMessage` 를 내지 않으므로"를 고친다. 그 밖에 이 티켓이 거짓으로 만드는 문장을 러너와 그 시험에서 "notice"와 "systemMessage"로 grep해 본다
- [ ] `tools/mutate.py`로 새 판정을 바꾸면 새 시험이 빨개지는지 본다(`.claude/rules/tools.md`의 새 훅 넷 가운데 검사의 빨강). 변이 명세는 `.scratch/harness/probes/`에 커밋한다
- [ ] `CLAUDE.md`의 검증 명령이 모두 초록이다

### 받는 쪽

- [ ] 04와 05가 이 판정으로 `notice` 사례를 더한다. 두 티켓의 자리표시자(문턱을 넘는 트랜스크립트, 표지를 쓸 빈 임시 폴더, 가짜 홈과 출력 폴더)는 각 티켓이 더한다(명세 "러너의 자리표시자", "세션 시작 훅"의 자리). 이 티켓은 더하지 않는다

### 이 티켓이 정할 것

1. `notice`와 `context`가 함께 맞는 출력(`systemMessage`와 `additionalContext`를 함께 낸다)을 지금처럼 `context`로 볼지. 명세는 정하지 않았다. 정한 것과 까닭을 일지에 적는다
