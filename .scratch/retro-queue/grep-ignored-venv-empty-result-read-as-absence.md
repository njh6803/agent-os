# grep-ignored-venv-empty-result-read-as-absence: Grep 도구가 `.gitignore`대로 `.venv`를 넘어 FastAPI 소스의 `X-Accel-Buffering` 머리를 찾지 못했고, 세션이 그 빈 결과를 근거로 FastAPI가 그 머리를 싣지 않는다고 적었다가 Bash의 `grep -rli`로 찾아 바로잡았다

**상태:** 열림
**어디로:** Grep의 PostToolUse 훅(긴 일치 줄의 생략을 알리는 훅과 같은 자리): Grep의 `path`가 무시된 폴더(`.venv`, `node_modules`)이거나 그것을 품은 폴더이고 결과가 비었으면, 무시된 파일을 넘었을 수 있다고 알린다. `CLAUDE.md` 환경 함정의 Glob·Grep 항목이 이미 이 사실을 적었는데도 어겼으므로 지침이 아니라 훅이다. 다섯째 회차에 고른다
**승인:** 자체 승인 2026-11-24, 1회차, 일지 2026-11-24-1644-admin-login-spec.md. ADR 불필요
