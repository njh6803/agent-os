# 06: 모델이 스스로 내는 세션 카드를 훅이 막는다

**What to build:** 이 저장소의 세션이 스스로 세션 카드를 내려고(`start_session`에 `initiation: own_initiative`) 하면 카드가 화면에 뜨지 않고, 모델은 막힌 까닭의 글을 받는다. 그 글은 후속 일을 지금 일지의 "다음"이나 대기열 행(회고)으로 적으라고 하고, `initiation`을 `user_asked`나 `offer`로 바꿔 다시 부르지 말라고 한다. 사람이 "새 세션에서 해"라고 시킨 것(`user_asked`), 사람에게 묻는 것(`offer`), 이미 뜬 카드를 시작하는 것(`proposal_id`만 든 호출)은 그대로 지난다.

근거는 `.scratch/ticket-for-every-pr/spec.md`의 "카드 막는 훅"과 Testing Decisions의 "카드 훅", 사용자 스토리 10·11·31·38이다. 결정은 ADR 0037의 "세션 카드"다. 이 도구를 PreToolUse 훅으로 막을 수 있다는 측정은 `.scratch/ticket-for-every-pr/probes/card_block/`(결과 `2026-10-21-result.json`, 그 README)이다.

**Blocked by:** None (can start immediately)

**Status:** done

### 훅

- [x] **새 PreToolUse 훅 `tools/hook_session_card.py`.** 매처는 `mcp__ccd_session__start_session` 하나다(명세의 거부한 안: `__start_session`으로 끝나는 모든 도구로 넓히지 않는다). `tool_input.initiation`이 `own_initiative`이면 `permissionDecision: deny`와 까닭의 글을 낸다. 그 밖의 입력(`user_asked`, `offer`, `initiation` 없이 `proposal_id`만 든 시작, 풀 수 없는 입력)은 아무것도 내지 않는다
- [x] **까닭의 글**(명세 "까닭의 글" 그대로). 모델이 스스로 내는 세션 카드는 이 저장소에서 막는다는 것, 후속 일은 지금 일지의 "다음"이나 대기열 행(회고)으로 적는다는 것, `initiation`을 `user_asked`나 `offer`로 바꿔 다시 부르지 않는다는 것(그 값은 사용자가 말로 시켰거나 사용자에게 물을 때만 쓴다), 근거(ADR 0037)
- [x] **독스트링.** 무엇을 막고 무엇을 지나보내는지, 측정의 자리(위 프로브), 못 보는 것(`initiation`은 모델이 적는 값이라 스스로 낸 일을 `user_asked`로 적으면 막지 못한다, 앱이 도구 이름을 바꾸면 매처가 맞지 않아 조용히 지나간다, 사람이 카드를 눌러 시작한 것과 다른 세션 도구(`hand_off_to_session` 등)는 보지 않는다)
- [x] 표준 라이브러리만 쓴다(`.claude/rules/tools.md`)

### 새 훅의 넷(`.claude/rules/tools.md`)

- [x] **등록.** `.claude/settings.json`에 래퍼 모양(`tools/run_hooks.py`의 `REGISTRATION`)으로 등록한다. 훅 설정을 고치는 일이라 자동 모드의 분류기가 자기 수정으로 거부할 수 있으니, 등록하기 전에 사람의 허락을 받는다(프로브 README, 명세 일지 2026-10-21-05 "사건")
- [x] **순수 함수 시험**(`tests/tools/test_hook_session_card.py`). `own_initiative`(deny와 까닭 글의 낱말: 일지의 "다음", 대기열, `user_asked`, ADR 0037), `user_asked`, `offer`, `proposal_id`만 든 시작, 풀 수 없는 입력(JSON이 아니다, `tool_input`이 객체가 아니다)
- [x] **빨강을 먼저 본다.** 훅이 아무것도 내지 않는 첫 판으로 `own_initiative` 사례가 빨간 것을 본다
- [x] **실제 입력 표**(`tools/hook_payloads.toml`). 발동 사례는 탐침이 받은 실제 입력(`.scratch/ticket-for-every-pr/probes/card_block/2026-10-21-hook-log.jsonl`의 둘째 줄)으로, 침묵 사례는 `proposal_id` 입력과 `user_asked` 입력으로 둔다. `uv run python tools/run_hooks.py`로 돌려 본다

### 실제 세션의 확인

- [x] **사람이 그 워크트리 폴더에서 새 앱 세션을 한 번 연다**(명세가 정했다). 세션 도중에 더한 등록은 그 세션에 실리지 않았기 때문이다(프로브 README의 손으로 본 것). 그 세션에서 `own_initiative` 호출이 막히고 까닭의 글이 모델에게 가는 것과, 양성 대조로 `user_asked`나 없는 `proposal_id`의 호출이 훅에 막히지 않는 것을 본다. 이것이 탐침이 재지 않은 두 자리(래퍼, `settings.json`)를 닫는다. 결과를 프로브 README에 적고 일지에 옮긴다. 두 자리에서 막히지 않으면 등록의 모양을 고치고 다시 본다(결정은 바뀌지 않는다). 2026-10-22에는 사용자가 선택 화면에서 대신 열기를 골라, 이어받은 세션이 `start_session`(`user_asked`, `cwd`)으로 열었다

### 문서

- [x] `KICKOFF.md` 훅 목록에 `hook_session_card`를 더한다(이유는 독스트링, 막는 훅 무리, 앱의 세션 카드 도구를 쓰는 프로젝트에만)
- [x] `.claude/rules/tools.md`의 훅별 시간 문단에 이 훅이 붙는 도구와 시간을 적는다. 재지 않았으면 다른 훅과 같은 약 0.2초로 어림한다고 적는다
- [x] **카나리아.** `.claude/rules/tools.md`를 고쳤으므로 그 파일을 원천으로 든 카나리아 명세(`.scratch/harness/probes/canary/tools_rule*.toml`)를 고치거나 새로 두고 새 `claude -p` 세션에서 불러 본다(명세 "이음매"의 스킬과 문서, `CLAUDE.md` 작업 규약 3). 그러지 않으면 커밋 전 `tools/sibling_overlap.py`가 1로 끝난다. 결과를 일지의 검사 절에 적는다. 쓰기 전에 Skill 도구로 `writing-for-agents`를 부른다(`.claude/rules/agent-docs.md`)

### 검증

- [x] 첫 편집으로 이 티켓의 `Status:`를 `in-progress`로 바꿔 첫 커밋에 싣고, PR을 열기 전에 `done`으로 바꾼다
- [x] 원칙 III를 지킨다
- [x] 검증 명령이 모두 초록이다
