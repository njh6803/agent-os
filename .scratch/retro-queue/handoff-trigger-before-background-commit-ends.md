# handoff-trigger-before-background-commit-ends: **`hook_handoff`의 인계 계기가 백그라운드로 띄운 커밋이 끝나기 전에 와서, 세션이 끝 알림 뒤에 절차로 돌아오는 길을 스스로 기억해야 한다**

**상태:** 열림
**어디로:** `tools/hook_handoff.py`와 `tools/hook_handoff_notice.py`: Bash의 `run_in_background`로 띄운 `git commit`에는 계기를 내지 않고 끝 알림 뒤에 낸다. 훅이 판정하기 어렵다면 `.claude/skills/next-session/handoff.md`에 백그라운드 커밋 직후의 계기는 끝 알림 뒤에 이어 간다는 한 줄을 적는다. 518은 같은 훅이 `인계 못함` 뒤에도 계기를 다시 넣는 일이고 이 항목은 계기를 내는 때가 다르다
**승인:** 자체 승인 2026-11-13, 1회차(이 브랜치의 세 세션에서 다섯 번: 앞 세션의 커밋 뒤 한 번, 인계받은 세션의 커밋 뒤 둘과 PR 연 뒤 하나, 셋째 세션의 커밋 뒤 한 번), 일지 2026-11-12-1937-portal-login-design.md. ADR 불필요

(백그라운드 명령은 띄운 때에 Bash 호출이 돌아오므로 훅은 커밋이 끝나기 전에 계기를 낸다. 앞 세션은 계기가 끝 알림 뒤에는 다시 오지 않아 끝 알림을 받은 뒤 절차로 돌아왔고, 인계받은 세션은 지시문이 `인계: 커밋 뒤`로 시작해 넘기지 않고 이었다. 손상은 없고 매번 `handoff.md`의 판정을 다시 따진 값이 든다)
