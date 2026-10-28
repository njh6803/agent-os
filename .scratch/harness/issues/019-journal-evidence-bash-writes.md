# 019: Bash 명령이 일지를 쓸 때도 근거 계기를 넣는다

**What to build:** `tools/hook_journal_evidence.py` 는 Write·Edit 로 일지(`docs/journal/<이름>.md`)를 고칠 때만 근거의 종류를 밝히라는 계기를 넣는다. harness 018 둘째 세션이 일지를 Bash heredoc(`cat >>`)으로 덧붙여 그 계기가 닿지 않은 채, 잡 로그를 보지 않은 git 판을 본 것처럼 적었다(대기열 501, 훅 독스트링의 "못 보는 것" 첫 항목). 같은 훅이 Bash 호출의 `tool_input.command` 를 읽어, 그 명령이 일지 경로에 쓰는 꼴(리다이렉트 `>`·`>>`, `tee`, `sed -i`, 그 경로를 들고 쓰기를 하는 `python`)이면 같은 계기를 같은 표지로 세션·에이전트마다 한 번 넣는다. 일지를 읽기만 하는 명령(`cat`, `grep`, `git add`, 입력 리다이렉트 `<`)에는 알리지 않는다. 계기 훅이라 막지 않는다(`.claude/rules/tools.md` 의 계기·막는 훅 가름). 등록은 PostToolUse 의 새 `Bash` 묶음이다. PowerShell 로 쓴 일지는 이번에 넓히지 않고 못 보는 것에 적는다.

**대기열:** 501

**Status:** done

## 수용 기준

- [x] Bash 명령이 `>`·`>>`·`tee`·`sed -i`·쓰기를 하는 `python` 으로 일지 경로를 쓰면 계기가 나고, 일지를 읽기만 하는 명령과 일지 밖을 쓰는 명령에는 나지 않는다. 갈래마다 `tests/tools/` 시험이 있다
- [x] Write·Edit 와 Bash 가 표지 하나를 같이 써, 한 세션에서 어느 쪽으로든 한 번만 알린다
- [x] `.claude/settings.json` 의 PostToolUse 에 `Bash` 묶음으로 래퍼 모양 등록이 있고, `tools/hook_payloads.toml` 에 Bash 의 발동 하나와 침묵 하나가 있어 `tools/run_hooks.py` 가 통과한다
- [x] 독스트링의 "못 보는 것" 을 고친 항목마다 시험으로 고정한다(변수에 든 경로, PowerShell, `cp`·`mv` 등)
- [x] 이 계기를 Write·Edit 에만 적은 살아 있는 문서(`docs/agents/issue-tracker.md`, `.claude/rules/tools.md`)를 고친다
- [x] 검증 명령이 모두 초록이다
