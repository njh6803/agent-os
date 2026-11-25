# worktree-lock-left-when-unlock-denied: 0326의 7회차. 인계하는 세션의 잠금 풀기(`git worktree unlock`)가 자동 모드 분류기에 거부되어, 인계로 연 새 세션의 `EnterWorktree(path)`가 다시 `belongs to another running Claude Code session`으로 거부했다

**상태:** 열림
**어디로:** `.claude/skills/next-session/directive.md`의 "어디서" 줄 규칙이나 지시문 훅(`tools/hook_prompt_directive.py`)이 새 세션에 넣는 "어디서" 안내: `EnterWorktree(path)`가 잠금으로 거부되고, 잠근 pid의 세션 제목이 그 브랜치에 `(인계함)`을 붙인 것이면, 새 세션이 워크트리에 들어가기 전의 주 체크아웃에서 `git worktree unlock <그 워크트리 절대 경로>`를 치고 다시 들어간다는 한 줄. `.claude/skills/next-session/handoff.md` "잠금 풀기"는 넘기는 쪽이 막히면 일지에 적고 열기로 간다고만 적어, 받는 쪽의 길이 대기열 326의 선례에만 있다. 넘기는 쪽의 거부를 허용 규칙으로 여는 길은 권한을 넓히는 것이라 넘김이다
**승인:** 자체 승인 2026-11-25, 0326의 7회차(0326이 6회차로 닫혔다), 일지 2026-11-24-2305-widget-admin-server-tickets.md. 8회차(2026-11-25), 일지 2026-11-25-1007-admin-login-tickets.md. ADR 불필요(ADR 0032·0033의 결정 안의 절차다)
