# 06: 큰 결과 알림 훅

**What to build:** 모델이 범위 없이 읽은 Read 결과가 2만 자를, Bash·PowerShell 결과가 1만 자를 넘으면, 새 훅 `hook_large_result`가 모델에게 결과의 크기와 문턱을 알린다. 그리고 일부만 필요했으면 다음에는 Grep으로 줄을 찾아 Read의 `offset`·`limit`로 읽거나 명령의 출력을 거르라고(`head`, `Select-Object`, `--stat`), 전체가 필요했으면 따르지 않아도 된다고 적는다. 막지 않는다. 서브에이전트의 호출에도 알린다.

근거는 `.scratch/token-usage/spec.md`의 "큰 결과 알림 훅"(문턱과 그 측정, 크기, 알림, 되풀이, 서브에이전트)과 Testing Decisions의 훅·계기 도달 항목이다. 막지 않는 것은 ADR 0033 본문이다.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

### 훅

- [ ] PostToolUse에 매처 `Read|Bash|PowerShell`로 래퍼 모양 등록을 더한다
- [ ] 문턱은 Read 2만 자, Bash·PowerShell 1만 자이고 바꾸지 않는다. Read에 `offset`이나 `limit`을 줬으면 알리지 않는다. 같은 대상이 넘을 때마다 알리고 표지를 두지 않는다
- [ ] 크기는 모델이 받는 결과의 글자 수다. PostToolUse의 `tool_response`는 도구의 구조화된 출력이라(명세 "크기", 공식 hooks 문서의 PostToolBatch 절), Read는 본문에 줄마다 줄 번호 접두의 글자 수를 더하고 Bash·PowerShell은 출력 칸들의 글자 수를 더한다. 글이 아닌 결과(그림, PDF)는 0자다
- [ ] 먼저 Read·Bash·PowerShell의 실제 PostToolUse 페이로드를 저장해, 구조화된 출력의 모양과 같은 호출의 기록 `tool_result` 본문 길이를 대 본다. 저장한 원본과 대조 스크립트는 `.scratch/token-usage/probes/`에 커밋하고 README에 줄을 둔다(`.claude/rules/probes.md`, 선례 `.scratch/harness/probes/webfetch_payload/`). 셈과 기록이 다르면 그 차이와 까닭을 일지에 적는다
- [ ] 독스트링에 못 보는 것을 적고 항목마다 시험으로 고정한다. 서브에이전트의 `additionalContext`가 그 서브에이전트의 모델에 닿는지(재지 않았다)를 든다

### 시험과 실행 확인

- [ ] 명세 Testing Decisions의 큰 결과 훅 항목을 시험으로 고정한다. 문턱의 앞뒤(Read와 셸 각각), 범위를 준 Read, 그림 결과, 저장한 실제 페이로드에서 셈한 글자 수가 그 기록의 `tool_result` 길이에 맞는 것이다
- [ ] `tools/hook_payloads.toml`에 발동(`context`) 하나와 침묵 하나(범위를 준 큰 Read, 또는 문턱 아래 결과)를 실제 입력으로 더한다
- [ ] `additionalContext`가 실제 세션의 모델에게 닿는지 모델이 그 문장을 옮기게 해서 본다(`.claude/rules/tools.md`의 새 훅이 함께 하는 넷)
- [ ] 문턱은 03의 장부(큰 도구 결과)와 같다. 03과 이 티켓 가운데 늦게 병합하는 쪽이 두 문턱이 같은지 보는 시험을 더한다
- [ ] `tools/mutate.py`로 문턱과 범위 판정을 바꾸면 시험이 빨개지는지 본다
- [ ] Read와 Bash 호출에서 훅이 쓰는 시간을 재서 `.claude/rules/tools.md`의 시간 목록에 더한다. 그 rules를 원천으로 든 카나리아 가운데 바뀐 문장에 닿는 것을 돌려 결과 줄을 고친다(`tools/sibling_overlap.py`가 본다)
- [ ] `KICKOFF.md` 7단계의 `.claude/settings.json` 항목에 이 등록은 새 프로젝트에 복사하지 않는다고 적고, 그 항목이 늘어놓은 PostToolUse 매처를 맞춘다(명세 Out of Scope)
- [ ] 레벨 스윕 README의 조건 변경 절에 큰 결과 알림 훅 줄을 이 PR 번호로 적는다. 절이 없으면 만들고 절 머리에 효과가 서는 때를 한 번 적는다(명세 "레벨 스윕 기록"). `sweep.py prereg`가 0으로 끝난다
- [ ] `CLAUDE.md`의 검증 명령이 모두 초록이다

### 이 티켓이 정할 것

1. 줄 번호 접두의 실제 모양과 Bash·PowerShell 출력 칸의 셈(저장한 페이로드로)
2. 알림의 문구
