# glob-slash-pattern-narrowed-path: Glob 도구에 `path` `.scratch`와 패턴 `*/probes/README.md`를 주자 "No files found"였고, 같은 `path`에 `**/probes/README.md`를 주자 서른 개를 찾았다

**상태:** 열림
**어디로:** `tools/`에 PreToolUse 계기 훅과 `.claude/settings.json` 등록: Glob의 `pattern`이나 Grep의 `glob`에 `/`가 들고 `**/`로 시작하지 않으면서 `path`를 좁혀 줬으면 `**/`로 열라고 알린다. 그 시험과 `tools/hook_payloads.toml`의 페이로드. 새 훅이라 문턱은 다섯 번째 반복이고 그 전에는 회차를 센다
**승인:** 자체 승인 2026-11-11, 0211의 2회차, 일지 2026-11-11-1110-release-image-design.md. ADR 불필요

`CLAUDE.md` 환경 함정의 Glob 줄("패턴에 `/`가 들면 `**/`로 연다", 대기열 211을 근거로 든다)이 이미 실린 세션에서 어겼다. 지침이 있는데도 어겼으므로 처방은 지침보다 높은 층인 계기 훅이다. 같은 함정의 Grep 쪽은 열린 `grep-glob-slash-pattern`이 세고, 그 항목의 처방에도 계기 훅이 들어 있어 훅 하나로 두 항목을 함께 닫을 수 있다.
